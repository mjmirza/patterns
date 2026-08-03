---
name: Polling Publisher
slug: polling-publisher
family: 10-microservices
category: Data
aliases: [Outbox Polling, Message Relay Polling, Cursor-Based Relay]
first_described: "Richardson, microservices.io pattern catalog"
maturity: canonical
related: [transactional-outbox, transaction-log-tailing, domain-event, saga, database-per-service]
incompatible_with: [shared-database]
verified: 2026-08-02
---

# Polling Publisher

## 1. Name, aliases, and lineage

The canonical name is Polling Publisher. It comes from Chris Richardson's
microservices.io pattern catalog, the same catalog that names Transactional
Outbox, Transaction Log Tailing, and Saga. Richardson states the pattern's
problem plainly as how to publish messages that were inserted into the
database's outbox table to the message broker, and states the solution as
publish messages by polling the database's outbox table
([microservices.io, "Polling publisher"](https://microservices.io/patterns/data/polling-publisher.html),
verified 2026-08-02). The page names one advantage explicitly, that it works
with any SQL database, and two drawbacks, that maintaining publication order
is hard and that some NoSQL databases are a poor fit for the query the pattern
needs
(same page, verified 2026-08-02).

Two names circulate for the same idea outside Richardson's own vocabulary.
Outbox Polling shows up in engineering blog posts that treat Polling
Publisher as the default, unglamorous implementation strategy for the wider
Transactional Outbox idea, as opposed to the log-tailing strategy. Message
Relay Polling appears in some .NET and Java shops as a name for the
background worker itself, the process whose only job is to read rows and
push them onward. This entry adds a third alias, Cursor-Based Relay, because
the mechanism this pattern names, a query that asks for everything past a
remembered position and then advances that position, is identical whether
the table being polled is a purpose-built outbox or a general-purpose event
log. That identity is not incidental. it is why the pattern also underwrites
tools nobody thinks of as outbox tools, among them Kafka Connect's JDBC
Source Connector and Airbyte's cursor-based incremental sync, both discussed
in dimension 9 below.

The pattern's own catalog page names one direct alternative, Transaction Log
Tailing, and one direct prerequisite, Transactional Outbox, and the sibling
Transaction Log Tailing page returns the favor, calling Polling Publisher an
alternative solution in one line and leaving the comparison at that
([microservices.io, "Transaction log tailing"](https://microservices.io/patterns/data/transaction-log-tailing.html),
verified 2026-08-02). This entry expands that one line into dimension 12,
the trade-off matrix, because the two patterns solve the exact same problem
with opposite engineering trade-offs, and a reader choosing between them
needs the comparison spelled out, not implied.

## 2. Problem and context

The context is the second half of the Transactional Outbox story, and it is
worth stating precisely because Polling Publisher is frequently confused
with the outbox pattern itself. Transactional Outbox solves the write side.
a service commits its business change and a row describing an event to
publish in one local database transaction, so the two either both happen or
neither does. That solves atomicity. It does not move a single byte onto a
message broker. The moment the transaction commits, there is a row sitting
in a table, and a completely separate problem now exists, how does that row
ever leave the database and become a message a consumer can react to.

That is the problem Polling Publisher answers, and it answers it in the
simplest way available to anyone who already has a relational database and a
message broker and nothing else. run a query on a schedule. The concrete
context is a service that owns its own database, publishes domain events so
other services can react to state changes without a synchronous call back
into the owning service, and either cannot or does not want to depend on a
change-data-capture pipeline sitting between its database and its
consumers. That last clause matters. teams pick Polling Publisher not
because it is the best available mechanism in the abstract, but because it
needs nothing beyond what a normal application already has, a database
connection and a scheduler, whereas its main rival needs a CDC connector, a
place to run it, and, in most real deployments, Kafka Connect or Debezium
sitting in the infrastructure as a new operational dependency.

The problem sharpens further inside the microservices context specifically,
where the pattern almost always lives. In a monolith, publishing an event
after a commit can be a call inside the same process, subject to its own
failure modes but at least local. Once a service is one of many, each with
its own datastore per the Database per Service pattern, the publishing step
crosses a process boundary, a network, and usually an authentication
boundary too, and every one of those can fail independently of the database
commit that already succeeded. Polling Publisher exists because someone has
to own the retry loop for that crossing, and putting that someone inside the
request path, publishing synchronously right after the commit, reintroduces
exactly the dual-write problem the outbox table was built to avoid. the
request thread can crash, time out, or lose its connection to the broker
after the database has already committed, and the event is gone forever
unless something else, running independently of the original request, comes
back and finds it.

## 3. Forces

Simplicity against timeliness sits at the center. A polling loop that wakes
up, runs `SELECT ... WHERE id > :last_seen ORDER BY id LIMIT :batch`, and goes
back to sleep needs no new infrastructure, but the minimum possible latency
it can offer is the sleep interval, and there is a real ceiling on how short
that interval can go before the polling itself becomes the database's
dominant workload. A five second interval is invisible to most operators and
most consumers. A one hundred millisecond interval against a busy table
under a naive polling query is a self-inflicted denial of service.

Coupling to the specific database engine is real but shallow. Every SQL
database Richardson's catalog page names as compatible speaks the same
`SELECT ... WHERE > ORDER BY LIMIT` dialect closely enough that the query
barely changes between Postgres, MySQL, and SQL Server. Contrast that with
Transaction Log Tailing, whose forces run the other way, near-real-time
delivery bought at the cost of learning a genuinely different mechanism per
engine, MySQL's binlog, Postgres's write-ahead log through logical
replication slots, SQL Server's CDC feature, DynamoDB's table streams, four
different technologies wearing one conceptual label
(microservices.io, "Transaction log tailing", verified 2026-08-02).

Ordering is a force the pattern loses to outright, and it is worth stating
why rather than only that it happens. A poll that runs `LIMIT 100` against a
table receiving concurrent inserts from multiple connections can observe
rows out of the order their transactions actually committed, because a
lower-numbered auto-increment id can commit after a higher-numbered one under
concurrent writers, a phenomenon sometimes called a commit gap or a
non-monotonic sequence. Any consumer that assumes event order equals
insertion order will occasionally be wrong, and the failure is silent, not a
crash, just a wrong ordering nobody notices until two events land in the
opposite sequence a downstream state machine required.

Operability pulls toward Polling Publisher and away from log tailing for a
team without dedicated platform capacity. A polling worker is an ordinary
process a normal application team already knows how to run, monitor, and
restart. A CDC pipeline is infrastructure with its own failure modes, its own
need for a schema registry in many setups, and its own on-call rotation in
organizations large enough to have one. Cost follows the same line, the
polling query's cost is visible on the service's own database, while a CDC
connector's cost is spread across a message broker cluster, a Kafka Connect
worker fleet, and the engineering time to run both.

## 4. Applicability and non-applicability

Reach for Polling Publisher when the message broker's per-event delivery
latency need not beat a small number of seconds, when the team operates the
publishing service's own database and can add a status column or a separate
outbox table to it, when the organization has no existing CDC platform and
adding one purely to relay one service's events is disproportionate to the
problem, when event volume per service is low enough that a periodic batch
query stays cheap, and when the audience for the events is internal
consumers who accept eventual consistency rather than a latency-sensitive
external integration.

Do not reach for it, and this is the non-applicability list the catalog
omits and this entry does not.

- When sub-second delivery latency is a real requirement, for example
  synchronizing a read-model cache that a user-facing page depends on within
  the same request-response cycle. no polling interval can honestly promise
  that without becoming a near-continuous query.
- When event volume per publishing service is high, tens of thousands of
  rows per minute or more, because every poll that returns a full batch
  immediately schedules another poll, and the loop degenerates into
  continuous scanning, which is the operational cost profile the pattern was
  chosen specifically to avoid.
- When the database in question is a document or key-value store with no
  efficient range query on a monotonic key, which is exactly the NoSQL
  incompatibility Richardson's own page flags
  (microservices.io, "Polling publisher", verified 2026-08-02).
- When strict per-partition or global ordering is a hard downstream
  requirement, because a naive polling query over a table with concurrent
  writers cannot guarantee it, as covered in dimension 3.
- When the team already operates a CDC platform for other services, in which
  case adding one more table to the existing Debezium or DynamoDB Streams
  pipeline costs less in total ownership than standing up a second,
  different relay mechanism.
- When the outbox table is expected to hold a large unbounded backlog, for
  example because the downstream broker is frequently unavailable for
  extended periods, since an unindexed or badly indexed poll against a
  multi-million-row backlog turns from a cheap query into a full scan.

## 5. Structure

Four participants make up the pattern, and every real implementation names
some variant of each.

The Outbox Table is the shared surface the whole pattern turns on, a
relational table in the publishing service's own database, written to inside
the same local transaction as the business change it announces, per
Transactional Outbox. Its columns carry at minimum an id suitable for
ordering or cursoring, a payload, an event type, a created timestamp, and
some notion of publication state, either a boolean or timestamp flag column
updated in place, or the row's continued presence, if the implementation
deletes published rows outright.

The Poller is the active participant, a background process, thread, or
scheduled job that owns exactly one responsibility, run the select query on
an interval, hand the resulting rows to the publisher, and record how far it
got. The Poller is where the pattern's forces from dimension 3 actually get
decided in code, the interval, the batch size, the query shape, and the
cursor or flag strategy all live here.

The Message Broker is the destination, any system able to accept a publish
call, Kafka, RabbitMQ, SQS, or an in-process event bus in a smaller
deployment. The pattern is broker-agnostic by design, which is part of why
Richardson calls the SQL-database compatibility the pattern's chief
advantage rather than any property of the broker
(microservices.io, "Polling publisher", verified 2026-08-02).

The Cursor Store is the participant that keeps the pattern's progress
durable across restarts, sometimes a column on the outbox table itself,
updated in the same transaction as the mark-published step, sometimes a
separate small table, sometimes an external store the poller checkpoints
into. Its job is narrow and load-bearing, if the poller crashes and
restarts, the Cursor Store is the only thing standing between a clean resume
and either replaying already-published events or silently skipping
unpublished ones.

## 6. ASCII structure diagram

```text
+-----------------------------+          +--------------------------+
|      Publishing Service     |          |       Message Broker     |
|                              |          |  (Kafka, RabbitMQ, SQS)  |
|  +------------------------+  |          +--------------------------+
|  |  Business transaction  |  |                       ^
|  |  writes domain rows    |  |                       |
|  |  and one outbox row,   |  |                       | publish()
|  |  in ONE local commit   |  |                       |
|  +-----------+------------+  |                       |
|              |                |                       |
|              v                |                       |
|  +------------------------+  |    poll interval  +----+-----+
|  |     Outbox Table       |<-|--------------------|  Poller  |
|  |  id | payload | state  |  |    SELECT ... >    | (thread, |
|  +------------------------+  |    cursor LIMIT n   | worker,  |
|              ^                |                       | cron)    |
|              |                |                       +----+-----+
|              | UPDATE state,  |                            |
|              | advance cursor |                            |
|              +----------------|----------------------------+
|                                |
|  +------------------------+  |
|  |      Cursor Store       |<-- checkpoint after each
|  |  (column or side table) |    successful batch publish
|  +------------------------+  |
+-----------------------------+
```

## 7. Dynamics

Every cycle of the poller follows the same six steps, and naming them
explicitly is what separates a working implementation from a subtly broken
one, because the ordering of steps four and five below is where most real
bugs in this pattern live.

```text
1. Timer fires (interval or fixed-delay schedule)
2. Poller reads last cursor position from Cursor Store
3. Poller runs SELECT rows WHERE cursor_column > last_cursor
                          ORDER BY cursor_column ASC
                          LIMIT batch_size
4. For each row, in order: publish(row) to the message broker
     - on publish failure: stop the batch, do NOT advance the cursor
     - on publish success: proceed to the next row in the batch
5. After the batch publishes successfully, in one transaction:
     UPDATE outbox SET state = 'published' WHERE id IN (batch ids)
     (or advance the Cursor Store's checkpoint value)
6. Sleep until the next timer tick, return to step 1
```

The order of step 4 versus step 5 is the pattern's single most important
runtime detail. Publishing must complete, and the caller must receive
confirmation the broker accepted the message, before the cursor advances or
the row is marked published. Reversing that order, marking a row published
and then attempting the broker call, produces silent message loss on any
crash between the two operations, because a restart resumes past a row the
broker never actually received. Publishing first and confirming before
advancing the cursor instead produces at-least-once delivery, the pattern's
actual guarantee, a duplicate on rare crash-during-confirm scenarios, never
a silent gap. Dimension 15 covers how to test exactly this ordering.

## 8. Implementation variants

Timestamp-column polling is the simplest variant and the one most tutorials
show first, a `SELECT ... WHERE created_at > :last_seen_ts` query. Its known
weakness is that a timestamp with insufficient precision, or two rows
committed within the same millisecond by concurrent transactions, can tie,
and a naive implementation using strict greater-than on the timestamp alone
can then silently skip one of the tied rows on the next poll. Kafka Connect's
JDBC Source Connector addresses this specific weakness by supporting a
combined timestamp-plus-incrementing mode built to break ties deterministically
([Confluent, "JDBC Source Connector Configuration Options"](https://docs.confluent.io/kafka-connectors/jdbc/current/source-connector/source_config_options.html),
verified 2026-08-02).

Incrementing-id polling avoids the tie problem outright by cursoring on a
strictly increasing primary key rather than a timestamp, at the cost of not
detecting updates to already-inserted rows, only new inserts, a trade-off the
same Confluent documentation states directly for its incrementing mode (same
source, verified 2026-08-02). For an outbox table specifically, where rows
are append-only by design and never updated in place, this trade-off costs
nothing, which is why incrementing-id polling is the variant most
purpose-built outbox implementations converge on.

Delete-on-publish is a variant that treats a published row as done and
removes it rather than flagging it, trading away an audit trail for a
permanently small table that never needs pruning. Flag-and-retain keeps
every row, marking a `published_at` timestamp instead of deleting, and pairs
naturally with a separate, slower archival job, at the cost of needing an
index on the state column and a periodic cleanup process of its own or the
table grows without bound, one of the failure modes covered in dimension 11.

Fixed-delay versus fixed-rate scheduling is a smaller but real variant.
fixed-delay waits a constant interval after the previous poll finishes,
which naturally backs off under sustained load since a slow batch pushes the
next poll later. fixed-rate fires on a strict wall-clock schedule regardless
of how long the previous poll took, which can queue overlapping polls under
sustained load unless the implementation explicitly guards against
re-entrancy, typically with a lightweight lock row or an advisory lock the
database itself provides.

## 9. Known production uses

Chris Richardson's own microservices.io catalog names Eventuate Tram, his
open-source microservices platform, as the practical example of this exact
pattern, describing it as a polling-based approach to publishing outbox
messages to a message broker
([microservices.io, "Polling publisher"](https://microservices.io/patterns/data/polling-publisher.html),
verified 2026-08-02). Eventuate Tram's newer default configuration favors a
separate change-data-capture reader process rather than in-application
polling, per its current getting-started documentation
([Eventuate, "Getting Started with Eventuate Tram"](https://eventuate.io/docs/manual/eventuate-tram/latest/getting-started-eventuate-tram.html),
verified 2026-08-02), which is worth stating plainly rather than glossing
over. it shows the pattern's own home platform treats Polling Publisher and
Transaction Log Tailing as two configurable strategies for the identical
outbox-delivery problem, exactly the choice dimension 12 below formalizes.

Confluent's Kafka Connect JDBC Source Connector is the second production
use, and it is the one most engineers touch without ever hearing the name
Polling Publisher. its documentation states the connector's mechanism in
those terms directly, a configurable poll interval, five thousand
milliseconds by default, and a choice of incrementing, timestamp, or
combined timestamp-plus-incrementing query modes to detect new or modified
rows since the last poll
([Confluent, "JDBC Source Connector Configuration Options"](https://docs.confluent.io/kafka-connectors/jdbc/current/source-connector/source_config_options.html),
verified 2026-08-02). Any team pointing this connector at an outbox table
rather than a general business table is running Polling Publisher inside
managed Kafka Connect infrastructure rather than a hand-rolled worker, and
this is a genuinely common way teams already running Kafka Connect implement
the pattern without building a custom poller.

The third use sits one layer up the stack, in data-integration tooling
rather than service-to-service messaging, and it demonstrates the mechanism
generalizes past the outbox use case specifically. Airbyte's incremental
sync mode moves rows out of a source table by running a cursor-bounded
query of the shape select rows where the cursor column is greater than or
equal to the last synced cursor value, then advancing that cursor after a
successful sync
([Airbyte, "Incremental Sync, Append"](https://docs.airbyte.com/using-airbyte/core-concepts/sync-modes/incremental-append),
verified 2026-08-02). The query shape, the checkpoint-after-success
ordering, and the reliance on a monotonic cursor column are identical to
dimension 7's dynamics, applied to bulk data replication rather than
event-driven messaging, and it is named here specifically because it shows
this is not a niche microservices trick but a general, load-bearing
mechanism for moving rows out of a database reliably, one production
data-integration platform depends on at scale.

## 10. Consequences

The pattern buys operational simplicity. no new infrastructure component,
no schema registry decision forced by a CDC tool's requirements, no new
category of on-call incident beyond ordinary application-process failures.
It buys database portability, the same query shape works across every SQL
engine that supports comparison operators and LIMIT, which none of the
engine-specific log formats Transaction Log Tailing depends on can claim
(microservices.io, "Transaction log tailing", verified 2026-08-02). It buys
an easy-to-reason-about failure model, at-least-once delivery with a clearly
defined resume point, the cursor, which is straightforward to inspect,
alert on, and manually intervene against when something goes wrong.

The pattern costs delivery latency, bounded below by the poll interval and
never able to approach the sub-second latency log tailing achieves by
reading committed transactions as they land in the write-ahead log. It costs
database load proportional to poll frequency, every poll is a real query the
database must plan and execute even when it returns zero rows, and that cost
scales with the number of services independently polling their own outbox
tables. It costs strict ordering guarantees under concurrent writers, as
covered in dimension 3. It costs table growth management, whichever
retention variant from dimension 8 is chosen, someone must own either the
delete-on-publish path or a separate archival job, and neither happens
without deliberate effort.

## 11. Failure modes and misuse

**Symptom.** Consumers occasionally receive an event twice for the same
business action. **Cause.** The poller published successfully, the broker
accepted the message, but the process crashed or the database connection
dropped before the cursor-advance update committed, so on restart the same
row is re-read and re-published. **Fix.** Treat this as expected under
at-least-once delivery rather than a bug, and make every consumer's event
handler idempotent, typically by deduplicating on the event's own id, which
is the standard mitigation the pattern's at-least-once guarantee requires
rather than an optional extra.

**Symptom.** An event that was clearly written to the outbox table never
reaches consumers, and the row sits forever with a null published-at column.
**Cause.** The publish call throws, and the poller's error handling swallows
the exception and advances the cursor or marks the row published anyway,
usually because the code was written to keep the batch loop moving rather
than to stop and retry the specific failing row. **Fix.** The cursor or the
published flag must only advance after a confirmed successful publish, per
dimension 7. any exception during publish should abort the current batch
before the mark-published step runs, leaving the row to be retried on the
next poll.

**Symptom.** The polling query, which used to run in milliseconds, now takes
seconds and the poller starts missing its interval, sometimes overlapping
with itself. **Cause.** Rows accumulate faster than they are marked
published or deleted, and the WHERE clause on an unindexed or poorly
indexed state column forces a growing table scan on every poll. **Fix.** Add
a composite index covering the state or cursor column used in the WHERE
clause plus the ORDER BY column, and set a bound, either a hard LIMIT on
batch size that the poller enforces every cycle or a separate archival job
that keeps the live, unpublished portion of the table small regardless of
total historical row count.

**Symptom.** Two events published moments apart from the same service
arrive at a downstream consumer in the opposite order they were written.
**Cause.** Concurrent transactions inserted rows whose auto-increment ids or
timestamps do not perfectly reflect commit order, exactly the ordering force
named in dimension 3, and a downstream consumer assumed insertion order
without accounting for it. **Fix.** Either accept unordered delivery and
design consumers to be order-independent, which is the cheaper and more
common answer, or move to a pattern with a stronger ordering guarantee, most
directly Transaction Log Tailing, which reads the database's own commit-
ordered log rather than reconstructing order from an id or timestamp column.

**Symptom.** During a deploy, two instances of the poller run briefly at
once, and consumers see duplicate publishes in a tight burst rather than the
occasional at-least-once duplicate the team had already accounted for.
**Cause.** No mutual exclusion protects the poll-and-publish cycle, so both
instances read the same unpublished rows before either one advances the
cursor. **Fix.** Serialize the poller with a database-level lock scoped to
the poll cycle, a `SELECT ... FOR UPDATE SKIP LOCKED` on the batch in
Postgres-family engines, or an advisory lock held for the duration of one
poll cycle, so only one instance can be mid-cycle at any moment.

## 12. Trade-off matrix

| Force | Polling Publisher | Transaction Log Tailing | Synchronous publish in request path |
|---|---|---|---|
| Delivery latency | Seconds, bounded by poll interval | Near real time, reads the commit log directly | Fastest when it works, but not durable |
| New infrastructure required | None beyond the poller process | CDC connector, often a schema registry | None |
| Database portability | High, same query shape on any SQL engine | Low, one mechanism per engine | Not applicable, database-agnostic |
| Ordering guarantee | Weak under concurrent writers | Strong, reflects true commit order | Strong per-request, no cross-request guarantee |
| Atomicity with business write | Guaranteed by the local outbox transaction | Guaranteed by the local outbox transaction | Not guaranteed, classic dual-write hazard |
| Operational burden | Low, an ordinary background job | Moderate to high, a new pipeline component | Lowest, until failures start losing events |
| Load on source database | Proportional to poll frequency | Low, reads a log the engine already writes | None extra |

## 13. Related and incompatible patterns

Transactional Outbox is the prerequisite this pattern always sits on top of.
Polling Publisher answers only how rows already safely in the outbox table
leave it. it says nothing about how they got there, and without the outbox
pattern's local-transaction guarantee, Polling Publisher would simply be
reading an ordinary table with no atomicity story at all.

Transaction Log Tailing is the direct sibling and the pattern most often
weighed against this one, as both catalog pages state explicitly
(microservices.io, "Polling publisher" and "Transaction log tailing",
verified 2026-08-02). The two are mutually exclusive as delivery mechanisms
for a single outbox table, a team picks one, though a large organization can
reasonably run Polling Publisher for a low-volume service and Log Tailing
for a high-volume one.

Domain Event is the payload shape carried through the outbox row and the
publish call, describing the fact of a business state change rather than a
command. Saga frequently depends on Polling Publisher, or its log-tailing
sibling, as the delivery mechanism that moves a saga's own domain events
between the participating services, since a saga is, structurally, a chain
of services reacting to one another's published events.

Database per Service is a structural prerequisite in the sense that the
pattern presumes the publishing service owns the outbox table inside its
own datastore. against a Shared Database, the entire premise collapses,
because there is no longer a single local transaction whose boundary the
outbox row and the business row both sit inside, which is why this entry's
frontmatter lists Shared Database as incompatible.

NServiceBus's own Outbox feature is worth naming as a related but distinct
design, not a Polling Publisher implementation. its documentation states
dispatch is triggered synchronously by the message-processing flow itself,
immediately after the local transaction commits and before the incoming
message is acknowledged, with no polling loop involved
([Particular Software, "NServiceBus Outbox"](https://docs.particular.net/nservicebus/outbox/),
verified 2026-08-02). It solves a related but narrower problem, safe
message deduplication for a message-driven handler, and it is named here
precisely as a contrast that sharpens what Polling Publisher actually is,
an independent, out-of-band delivery worker, not an in-line dispatch step.

## 14. Refactoring path in and out

Introducing Polling Publisher into a service that currently publishes
synchronously inside the request path starts with introducing Transactional
Outbox first, since Polling Publisher has nothing to poll until that exists.
add the outbox table, change the business transaction to insert one outbox
row alongside its domain writes, and stop publishing directly from the
request handler, replacing that direct call with nothing, for now the event
simply sits in the table. Next, write the poller as an entirely separate
process or scheduled job, starting with a conservative interval, ten seconds
is a reasonable default to begin measuring from, and a small batch size.
Confirm end-to-end delivery in a staging environment before removing any
remaining synchronous publish path, and only then decommission it. Finally,
add the index from dimension 11's third failure mode before the table sees
production write volume, not after the first slow-query alert.

Removing the pattern, migrating from Polling Publisher to Transaction Log
Tailing, is the more common exit path in practice, usually triggered by a
latency requirement the polling interval can no longer satisfy. The outbox
table itself does not change, both patterns read from the same table, only
the delivery mechanism changes. Stand up the CDC connector pointed at the
same outbox table, run it in parallel with the existing poller against a
non-production copy of the table to confirm event content and ordering
match, then cut consumers over to the CDC-sourced topic, and only then
retire the poller. Running both mechanisms briefly in parallel against
production, publishing the same events twice from two independent
mechanisms, is the one step worth calling out as a trap. every consumer must
already be idempotent, per dimension 11's first failure mode, before that
parallel period, or the cutover itself becomes an incident.

## 15. Testing and verification

The single most valuable test is the crash-ordering test named in dimension
7, and it deserves to be written explicitly rather than assumed correct by
inspection. insert a row, invoke the poller's publish step with a broker
client stubbed to throw on the first call, and assert the row's state is
still unpublished and the cursor has not advanced afterward. Then run the
same poller a second time with the stub now succeeding, and assert the same
row publishes exactly once and the cursor advances past it. Together these
two tests pin down the ordering that separates safe at-least-once delivery
from silent message loss, and either one failing after a refactor is the
signal that step 4 and step 5 from dimension 7 have been accidentally
reordered.

Consumer idempotency is easy to test in isolation, given the pattern's
guarantee is at-least-once rather than exactly-once. call the same consumer
handler twice with an identical event payload and assert the observable
side effect, a row written, a downstream call made, happened once, not
twice. This test belongs to every consumer of every event this pattern
publishes, not to the publisher itself, and it is the cheapest available
defense against the duplicate-delivery failure mode in dimension 11.

Concurrency safety deserves a focused integration test given the fourth
failure mode above, running two poller instances against one database
concurrently and asserting no event is ever published by both, which
exercises the locking mechanism from dimension 11 directly rather than
trusting it works by reading the code. Ordering, by contrast, is not
something to test for a strict guarantee this pattern does not offer.
instead, test that the system as a whole tolerates the disorder dimension 3
describes, by feeding a consumer two related events in the wrong order and
confirming it still reaches the correct final state, which is the honest
target given the pattern's actual guarantees.

## 16. Observability signals

The cursor's distance from the outbox table's newest row is the pattern's
single most important gauge, typically exposed as a lag metric, the count
of unpublished rows or the age in seconds of the oldest unpublished row. A
healthy poller keeps this near zero, rising briefly between poll cycles and
falling back after each one. A steadily climbing lag is the earliest and
clearest indicator that publishing is falling behind ingestion, whether
from a broker outage, a slow query, or the poller itself having stopped.

Poll cycle duration, tracked as a histogram, reveals the query-degradation
failure mode from dimension 11 well before it becomes a user-visible
outage, a duration that creeps upward over days as the table grows is the
mark of a missing or ineffective index. Publish success and failure counts
per cycle, tagged by whether a batch completed cleanly or aborted partway
through, distinguish ordinary at-least-once retries from a broker that is
genuinely unreachable, which look identical from the lag metric alone but
demand different responses.

A gauge or counter for concurrent poller instances actively holding the
lock from dimension 11's fifth failure mode catches the deploy-overlap
scenario directly, rather than waiting for downstream duplicate-event
reports to reveal it indirectly. Finally, the raw row count of the outbox
table itself, independent of publication state, deserves its own alert
threshold, since unbounded growth from a missing retention job is a slow
failure that a lag metric alone will not reveal until the table is already
large enough to be painful to fix.

## 17. Security and privacy implications

The outbox table inherits whatever sensitivity the domain events themselves
carry, and because those rows persist, sometimes for a retention period
measured in days per dimension 8's flag-and-retain variant, they extend the
window during which personal or otherwise sensitive data sits at rest
beyond the lifetime of the original business transaction that created it.
Any data-retention or right-to-erasure obligation that applies to the
underlying business record applies equally to its corresponding outbox row,
and a delete-on-publish retention strategy, purely as a side effect of
minimizing how long sensitive data lingers, is the stronger default from a
privacy standpoint whenever an audit trail is not independently required.

Access to the outbox table is effectively access to the service's outbound
event stream before it reaches the broker's own access controls, so
database-level permissions on that table deserve the same scrutiny as
broker-level topic permissions, an application role with unnecessary
write access to the outbox table can forge events the rest of the system
will treat as authentic. The poller's own credentials, since it typically
needs both database read access and broker publish access, are a
concentration of privilege worth scoping narrowly, read-only on the outbox
table plus write access limited to the specific topics or queues it
publishes to, rather than credentials broadly reused from the owning
service's general database role.

## 18. References

- Chris Richardson, ["Polling publisher"](https://microservices.io/patterns/data/polling-publisher.html), microservices.io pattern catalog, verified 2026-08-02.
- Chris Richardson, ["Transaction log tailing"](https://microservices.io/patterns/data/transaction-log-tailing.html), microservices.io pattern catalog, verified 2026-08-02.
- Eventuate, ["Getting Started with Eventuate Tram"](https://eventuate.io/docs/manual/eventuate-tram/latest/getting-started-eventuate-tram.html), Eventuate documentation, verified 2026-08-02.
- Confluent, ["JDBC Source Connector Configuration Options"](https://docs.confluent.io/kafka-connectors/jdbc/current/source-connector/source_config_options.html), Confluent documentation, verified 2026-08-02.
- Airbyte, ["Incremental Sync, Append"](https://docs.airbyte.com/using-airbyte/core-concepts/sync-modes/incremental-append), Airbyte documentation, verified 2026-08-02.
- Particular Software, ["NServiceBus Outbox"](https://docs.particular.net/nservicebus/outbox/), Particular Software documentation, verified 2026-08-02.
- Chris Richardson, *Microservices Patterns*, Manning, 2019, chapter 3, the outbox and message-relay problem this pattern completes.

## Code

The three implementations below share one shape, a poll function that
reads unpublished rows past a cursor, publishes each in order, and only then
advances the cursor, matching dimension 7's dynamics exactly. Each uses an
in-memory stand-in for the database and broker so the sample compiles and
runs without external infrastructure, while keeping the query and the
commit-after-publish ordering the part a real implementation must preserve.

```typescript
interface OutboxRow {
  id: number;
  payload: string;
  published: boolean;
}

interface Broker {
  publish(payload: string): Promise<void>;
}

class PollingPublisher {
  private cursor = 0;

  constructor(
    private readonly rows: OutboxRow[],
    private readonly broker: Broker,
    private readonly batchSize: number
  ) {}

  async pollOnce(): Promise<number> {
    const batch = this.rows
      .filter((r) => r.id > this.cursor && !r.published)
      .sort((a, b) => a.id - b.id)
      .slice(0, this.batchSize);

    for (const row of batch) {
      await this.broker.publish(row.payload);
      row.published = true;
      this.cursor = row.id;
    }
    return batch.length;
  }
}

async function main(): Promise<void> {
  const rows: OutboxRow[] = [
    { id: 1, payload: "order.created:1", published: false },
    { id: 2, payload: "order.created:2", published: false },
  ];
  const broker: Broker = {
    async publish(payload: string) {
      console.log("published", payload);
    },
  };
  const publisher = new PollingPublisher(rows, broker, 10);
  const count = await publisher.pollOnce();
  console.log("batch size", count);
}

main();
```

```python
from dataclasses import dataclass
from typing import Callable, List


@dataclass
class OutboxRow:
    id: int
    payload: str
    published: bool = False


class PollingPublisher:
    def __init__(self, rows: List[OutboxRow], publish: Callable[[str], None], batch_size: int):
        self.rows = rows
        self.publish = publish
        self.batch_size = batch_size
        self.cursor = 0

    def poll_once(self) -> int:
        pending = [r for r in self.rows if r.id > self.cursor and not r.published]
        pending.sort(key=lambda r: r.id)
        batch = pending[: self.batch_size]
        for row in batch:
            self.publish(row.payload)
            row.published = True
            self.cursor = row.id
        return len(batch)


def main() -> None:
    rows = [
        OutboxRow(id=1, payload="order.created:1"),
        OutboxRow(id=2, payload="order.created:2"),
    ]
    publisher = PollingPublisher(rows, lambda p: print("published", p), batch_size=10)
    count = publisher.poll_once()
    print("batch size", count)


if __name__ == "__main__":
    main()
```

```go
package main

import "fmt"

type OutboxRow struct {
	ID        int
	Payload   string
	Published bool
}

type Broker interface {
	Publish(payload string) error
}

type consoleBroker struct{}

func (consoleBroker) Publish(payload string) error {
	fmt.Println("published", payload)
	return nil
}

type PollingPublisher struct {
	rows      []*OutboxRow
	broker    Broker
	batchSize int
	cursor    int
}

func (p *PollingPublisher) PollOnce() (int, error) {
	var batch []*OutboxRow
	for _, r := range p.rows {
		if r.ID > p.cursor && !r.Published {
			batch = append(batch, r)
		}
		if len(batch) >= p.batchSize {
			break
		}
	}
	for _, row := range batch {
		if err := p.broker.Publish(row.Payload); err != nil {
			return len(batch), err
		}
		row.Published = true
		p.cursor = row.ID
	}
	return len(batch), nil
}

func main() {
	rows := []*OutboxRow{
		{ID: 1, Payload: "order.created:1"},
		{ID: 2, Payload: "order.created:2"},
	}
	publisher := &PollingPublisher{rows: rows, broker: consoleBroker{}, batchSize: 10}
	count, err := publisher.PollOnce()
	if err != nil {
		fmt.Println("poll failed", err)
		return
	}
	fmt.Println("batch size", count)
}
```
