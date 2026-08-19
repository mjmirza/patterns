---
name: Inbox
slug: inbox
family: 10-microservices
category: Reliability
aliases: [Transactional Inbox, Inbox Table, Message Deduplication Table, Idempotent Receiver Table]
first_described: "Dudycz, Outbox, Inbox patterns and delivery guarantees explained, event-driven.io, 2020, and Richardson, Microservices Patterns, Manning, 2018, chapter 3"
maturity: established
related: [idempotent-consumer, transactional-outbox, transaction-log-tailing, domain-event, database-per-service, saga]
incompatible_with: [shared-database]
verified: 2026-08-02
---

# Inbox

## 1. Name, aliases, and lineage

The pattern is called the Inbox pattern, and it is named for the mirror image
it forms with the Outbox pattern already catalogued in this family. Where the
Outbox pattern gives a service a durable place to stage messages it is about to
send, the Inbox pattern gives a service a durable place to record messages it
has already received, so that a message delivered twice by the network is
applied to business state exactly once.

The clearest early write-up under this exact name is Oskar Dudycz's article
"Outbox, Inbox patterns and delivery guarantees explained", published on his
site event-driven.io on 30 December 2020, which lays the two patterns side by
side and states plainly that the receiving side "stores incoming messages in a
database table before processing" and that duplicate delivery must still be
defended against through correct idempotency handling
(<https://event-driven.io/en/outbox_inbox_patterns_and_delivery_guarantees_explained/>,
verified 2026-08-02). The underlying mechanism, a durable record of processed
message identifiers consulted and updated in the same local transaction as the
business write, is older than the name. Chris Richardson describes the same
mechanism without the word inbox in *Microservices Patterns*, Manning, 2018,
chapter 3, where he discusses tracking a `PROCESSED_MESSAGES` table keyed by
message ID as the way to make a message consumer idempotent when the messaging
infrastructure only guarantees at least once delivery. Gregor Hohpe and Bobby
Woolf's *Enterprise Integration Patterns*, Addison-Wesley, 2003, describes the
closely related **Idempotent Receiver** as a design property a receiver can
have, without prescribing the storage-table mechanism as its own named
pattern. The Inbox pattern is best read as the concrete, transactionally safe
implementation technique that makes a receiver an idempotent receiver when the
receiver's own database is the only thing it can make transactional.

Two aliases circulate for the same idea. Milan Jovanović's engineering blog
calls it the **Inbox Pattern** and frames it as "Implementing the Inbox
Pattern for Reliable Message Consumption"
(<https://milanjovanovic.tech/blog/implementing-the-inbox-pattern-for-reliable-message-consumption>,
verified 2026-08-02). NServiceBus documentation, discussed under known
production uses below, folds the same mechanism into its **Outbox** feature
name, so a reader researching this pattern under vendor documentation should
expect to find it described as deduplication rather than as a separate
"inbox" noun. This entry treats Inbox as the pattern name and treats
deduplication, idempotent receiver table, and message ID tracking table as
synonyms for the same storage structure.

## 2. Problem and context

A service consumes messages from a broker, a queue, or an event stream, and it
must apply the side effect of each message to its own database exactly once,
even though the delivery mechanism can, and eventually will, deliver the same
message more than once.

This shows up in a codebase that looks correct at first read. A consumer
receives an order-placed event, debits inventory, and acknowledges the
message. The debit and the acknowledgement are two separate operations against
two separate systems, the service's own database and the broker. There is no
way to make both operations atomic across two different resources without a
distributed transaction coordinator, and this family already rules that
approach out for the reasons documented in
`distributed-transaction-coordinator-antipattern.md`. So one of two orderings
is chosen. If the debit commits and then the process crashes before the
acknowledgement reaches the broker, the broker redelivers the message on
timeout or on consumer restart, and the debit runs a second time. If the
acknowledgement is sent first and the process crashes before the debit
commits, the message is lost outright. Message brokers that promise anything
short of exactly-once end-to-end delivery, which in practice is every widely
deployed broker, force the operator to pick the redelivery side of that
trade-off, called at-least-once delivery, because losing a message silently is
almost always worse than processing one twice.

At-least-once delivery is not a defect in the broker, it is the honest
consequence of the trade-off between message loss and message duplication
under network partition and process failure. The problem the Inbox pattern
solves is entirely on the consumer's side of that boundary. Once duplicate
delivery is accepted as a fact the consumer will observe, the consumer needs a
way to recognise "I have already handled this exact message" and skip the
side effect the second time, without any cooperation from the broker and
without a second phase-commit-capable resource. The context that makes this
the right tool is a consumer whose side effect writes to a database it fully
controls, because the Inbox pattern's entire trick is piggy-backing the
deduplication check onto that same local transaction.

## 3. Forces

**Delivery guarantee versus application correctness.** The broker offers at
most at-least-once delivery in the common case. Application correctness
usually requires exactly-once effect. The Inbox pattern resolves the gap
entirely in application code, asking nothing extra of the broker.

**Latency and write amplification versus safety.** Every message now costs one
additional read-then-write against the inbox table inside the same
transaction as the business write. On a high-throughput consumer this
measurably adds write volume and, if the inbox table is not indexed and
pruned correctly, adds row contention. The pattern trades a small, bounded
per-message cost for the elimination of a class of duplicate-processing bugs
that are otherwise intermittent, hard to reproduce, and expensive to
investigate after the fact.

**Storage growth versus retention.** An inbox table that is never pruned grows
without bound and eventually degrades the very lookup it exists to make fast.
A retention window that is too short lets a legitimately delayed retry outlive
the window and be reprocessed as new. The pattern therefore always carries a
retention decision, and the retention decision is a real operational
parameter, not an afterthought.

**Ordering versus deduplication.** Deduplication alone answers "have I seen
this exact message before." It does not answer "have I seen every message
that should have arrived before this one." A consumer that needs ordered
processing per partition or per aggregate needs an additional sequence check
layered on top of the inbox lookup, discussed under dimension 8.

**Coupling to a single local database.** The pattern only works cleanly when
the business side effect and the inbox write share one transactional resource.
A consumer whose side effect is a call to a second remote service, rather than
a write to its own database, cannot make the inbox write and the side effect
atomic, and the pattern degrades back into the same two-writes problem it was
built to avoid. This is the sharpest force in the whole pattern and it drives
most of the applicability list below.

## 4. Applicability and non-applicability

Reach for the Inbox pattern when all of the following hold.

- The consumer's side effect is a write to a database the consumer itself
  owns and can enlist in a local ACID transaction.
- The message source delivers at-least-once, which includes essentially every
  production deployment of Kafka, RabbitMQ, Amazon SQS standard queues, Azure
  Service Bus with peer-lock retry, and Google Cloud Pub/Sub.
- Duplicate application of the side effect would be observably wrong, for
  example double-charging a card, double-decrementing stock, or sending a
  notification twice, rather than a duplicate that is naturally idempotent on
  its own, such as setting a field to the same fixed value.
- The consumer can identify a message uniquely and stably across redeliveries,
  either from a broker-supplied message ID or from a business-level identifier
  present in the payload.

Do not reach for the Inbox pattern in these situations.

- The side effect is already naturally idempotent, for example "set status to
  SHIPPED" applied twice leaves the same final state as applied once. Adding
  an inbox table here is unnecessary bookkeeping for a problem that does not
  exist. Confirm idempotence honestly, because "set status to SHIPPED and
  increment a shipment counter" is not naturally idempotent even though the
  first half of it looks like it is.
- The consumer's side effect is a call to an external, remote service rather
  than a local database write, for example forwarding the message on to a
  third-party API. The inbox write and the outbound call still cannot be made
  atomic, so the Inbox pattern alone does not close the gap; the correct
  combination is Idempotent Consumer at the remote service's own boundary,
  using an idempotency key the caller supplies, which is that remote service's
  problem to solve with its own inbox-shaped mechanism, not this consumer's.
- The broker itself already provides exactly-once processing semantics that
  the application can rely on end to end, as with Kafka Streams' exactly-once
  v2 semantics confined entirely within the Kafka cluster, per the Apache
  Kafka documentation on exactly-once semantics. Layering an application-level
  inbox table on top of a guarantee the platform already gives duplicates the
  work for no correctness gain.
- Message volume is so high, and the side effect so cheap and safely
  idempotent by construction, such as an upsert keyed by the message's own
  natural primary key, that the additional inbox row and index maintenance
  cost is pure overhead. An upsert on a stable business key is frequently a
  simpler and cheaper substitute for a separate inbox table.
- The consumer is a pure read-side projector inside an event-sourced system
  that already tracks a monotonic per-stream version number as part of its
  own projection state; the projection's own version check often already
  gives deduplication and ordering together without a second table.

## 5. Structure

**Message.** The unit of work arriving from the broker, carrying, at minimum,
a stable unique identifier the consumer can rely on across redeliveries. This
identifier is either the broker's own message ID, when the broker guarantees
it survives redelivery unchanged, or a business identifier the producer
embeds in the payload for exactly this purpose, such as an event ID generated
once at the point the event was first raised inside a Transactional Outbox.

**Inbox table.** A table local to the consumer's own database, holding one row
per message the consumer has processed or is currently processing. The row
carries at minimum the message identifier as a unique key, a processed
timestamp, and, in variants that also enforce ordering, a sequence or version
number scoped to the message's logical stream.

**Consumer transaction.** The unit of work that, in a single local database
transaction, first checks the inbox table for the incoming message's
identifier, applies the business side effect if the identifier is absent, and
inserts the identifier's row, committing all three as one atomic unit.

**Message handler.** The application code that performs the actual business
side effect, invoked from inside the consumer transaction only after the
duplicate check has passed.

**Acknowledgement step.** The step, outside the local transaction, that tells
the broker the message was consumed, run only after the local transaction has
committed. This ordering, commit locally first, then acknowledge, is what lets
redelivery of an unacknowledged message be handled safely by the inbox check
rather than by hoping the broker never redelivers.

**Retention sweeper.** A background process, or a scheduled job, that deletes
inbox rows older than the chosen retention window, keeping the table's size
and index bounded.

## 6. ASCII structure diagram

```
+------------------+        +--------------------------------------+
|   Message Broker  |        |             Consumer Service          |
|  (at-least-once)  |        |                                        |
+---------+---------+        |  +----------------------------------+  |
          |                  |  |         Message Handler          |  |
          | deliver(msg)     |  +----------------+-----------------+  |
          v                  |                   |                    |
   +--------------+          |                   v                    |
   |   Consumer   |--------->|  +----------------------------------+  |
   |   Endpoint   |          |  |     One Local DB Transaction     |  |
   +--------------+          |  |  1. SELECT inbox WHERE id = msg  |  |
                              |  |     .id   FOR UPDATE              |  |
                              |  |  2. if found: COMMIT, skip        |  |
                              |  |  3. else: apply side effect       |  |
                              |  |  4. INSERT INTO inbox(id, ts)     |  |
                              |  |  5. COMMIT                        |  |
                              |  +-----------------+------------------+  |
                              |                    |                     |
                              |                    v                     |
                              |         +----------------------+         |
                              |         |     Inbox Table       |         |
                              |         |  id UNIQUE PRIMARY    |         |
                              |         |  processed_at         |         |
                              |         |  (optional) seq_no    |         |
                              |         +----------------------+         |
                              |                    |                     |
                              |                    v                     |
                              |         +----------------------+         |
                              |         | Business tables the   |         |
                              |         | side effect wrote to  |         |
                              |         +----------------------+         |
                              +----------------------------------------+
                                          |
                                          v (after local commit)
                              +----------------------------------------+
                              |     ack(msg) sent back to broker        |
                              +----------------------------------------+
```

## 7. Dynamics

The sequence below shows the two paths a delivered message can take, first
delivery and redelivery, and why the second path is safe.

```
First delivery of message m (id = "m-42"):

Broker         Consumer Endpoint      Local DB Transaction         Broker
  | --deliver(m)--> |                        |                       |
  |                 | --BEGIN TX------------> |                       |
  |                 | --SELECT id FROM inbox  |                       |
  |                 |   WHERE id='m-42'-----> |                       |
  |                 | <--no row found-------- |                       |
  |                 | --apply side effect---> |                       |
  |                 |   (e.g. debit stock)    |                       |
  |                 | --INSERT id='m-42'----> |                       |
  |                 | --COMMIT--------------> |                       |
  |                 | <--commit ok----------- |                       |
  |                 | --------------------------------ack(m)--------> |
  | <---------------------------------------------------------------- |

Redelivery of the same message m (broker never saw the ack, or the ack
was lost, or a consumer restart replayed unacked messages from an offset):

Broker         Consumer Endpoint      Local DB Transaction         Broker
  | --deliver(m)--> |                        |                       |
  |                 | --BEGIN TX------------> |                       |
  |                 | --SELECT id FROM inbox  |                       |
  |                 |   WHERE id='m-42'-----> |                       |
  |                 | <--row found, skip----- |                       |
  |                 |   side effect NOT run   |                       |
  |                 | --COMMIT (no-op)------> |                       |
  |                 | --------------------------------ack(m)--------> |
  | <---------------------------------------------------------------- |
```

The critical property visible in both traces is that the SELECT, the side
effect, and the INSERT execute inside one local transaction, so a crash
between any two of those steps rolls the whole transaction back, and the
broker's own redelivery-on-timeout behaviour becomes the retry mechanism for
free. No separate retry logic is needed inside the consumer for this failure
mode.

## 8. Implementation variants

**Check-then-insert with a unique constraint.** The simplest and sturdiest
shape. A unique index on the message identifier column lets the consumer
attempt the INSERT with no prior SELECT at all, and treat a unique-constraint
violation as "already processed, skip." This variant needs no explicit
lookup and no row-level locking hint, because the database's own uniqueness
enforcement is the concurrency-safe check. It is the variant used in the
TypeScript and Go samples below.

**Explicit SELECT ... FOR UPDATE guard.** Some teams prefer a SELECT with a
row lock before deciding whether to proceed, particularly when the handler
needs to branch on more than presence or absence, for example when it must
also record a version or sequence number and reject an out-of-order message
rather than merely a duplicate one. This costs one extra round trip per
message compared to the unique-constraint variant but reads more explicitly.

**Sequence-checked inbox for ordering.** When messages within one logical
stream, for example all events for one order ID, must be applied in order,
the inbox row carries a sequence number, and the handler rejects, or defers
by re-queueing, any message whose sequence number is not exactly one greater
than the last recorded sequence number for that stream. This turns pure
deduplication into deduplication plus ordering, at the cost of one indexed
lookup per stream key rather than per message identifier alone. NServiceBus's
Outbox documentation and the Wolverine durability documentation both describe
message-store designs that support this stream-scoped variant.

**Time-windowed inbox with a retention sweeper.** Rather than keeping every
processed message identifier forever, the inbox row carries an expiry, and a
scheduled job or database TTL feature removes rows past the window. This
keeps the table bounded but reintroduces a real risk, a redelivery that
arrives after the window closes is treated as new and reprocessed, so the
window must be set comfortably longer than the broker's maximum realistic
redelivery delay, including consumer-down time during a deploy or an
incident.

**Framework-managed inbox.** Several messaging frameworks implement the
pattern as a first-class, configurable feature rather than leaving it to
application code, discussed by name under dimension 9. In this variant the
application only needs to enable the feature and choose retention; the
framework owns the SQL and the transaction boundary.

**Language-idiomatic notes.** In garbage-collected languages with ORM-managed
transactions, such as the TypeScript sample below using a raw SQL transaction
and the Python equivalent, the pattern is usually one small repository
function wrapping the check-then-insert. In Go, where transactions are
threaded explicitly through function calls rather than hidden behind a
framework's unit-of-work object, the pattern reads as an explicit `Tx`
parameter passed into the handler, which is the shape used in the Go sample.

## 9. Known production uses

**Wolverine, the .NET messaging and mediator framework published by JasperFx.**
Wolverine's own documentation describes "durable message persistence using
your application's database for reliable store and forward queueing," calling
the feature the transactional inbox and outbox together, and documents Marten
and Entity Framework Core, backed by PostgreSQL, SQL Server, or RavenDB, as
the supported message stores
(<https://wolverinefx.net/guide/durability/>, verified 2026-08-02). Enabling
the feature gives every configured listener endpoint an inbox table that
Wolverine itself checks and updates as part of the handler's own database
transaction, which is the check-then-insert variant described above,
implemented at the framework level rather than by application code.

**NServiceBus, the .NET service bus published by Particular Software.**
NServiceBus's Outbox feature documentation states that the system checks
outbox storage to see whether an incoming message has already been processed,
which it names deduplication, and that "NServiceBus uses the message identity
(MessageId) to deduplicate messages," retaining identification data for a
configurable retention period that must exceed the maximum possible retry
window
(<https://docs.particular.net/nservicebus/outbox/>, verified 2026-08-02).
Despite the feature's name being Outbox, the mechanism it documents for
incoming messages, a unique message ID checked and recorded inside the same
local transaction as the handler's business writes, is exactly the Inbox
pattern described in this entry, and NServiceBus's own documentation is
explicit that this deduplication step happens before the outgoing side of the
feature runs at all.

**Apache Camel's Idempotent Consumer EIP.** Camel's own documentation
describes the Idempotent Consumer as filtering out duplicates and states that
it "will add the message id eagerly to the repository to detect duplication,"
supporting pluggable, durable repository implementations including a
JDBC-backed `JdbcMessageIdRepository` alongside Redis, MongoDB, Kafka, and
Cassandra-backed repositories, and removing the ID from the repository if the
exchange subsequently fails so a genuine retry is not permanently blocked
(<https://camel.apache.org/components/next/eips/idempotentConsumer-eip.html>,
verified 2026-08-02). The JDBC-backed repository is a literal inbox table,
storing one row per processed message identifier, consulted before the route
runs its business logic.

## 10. Consequences

Positive.

- Converts at-least-once broker delivery into effectively-once application
  effect without requiring a distributed transaction coordinator or any
  cooperation from the broker beyond redelivering unacknowledged messages.
- Confines the correctness guarantee to a single local database transaction,
  which is a well-understood, cheaply testable unit compared to distributed
  consensus.
- Composes cleanly with the Transactional Outbox pattern on the sending side,
  so a chain of services can each independently guarantee exactly-once effect
  at its own boundary without any service needing global knowledge of the
  chain.
- Gives an explicit, queryable audit trail of every message the consumer has
  processed, which is frequently reused for debugging and for building a
  "was this event ever received" support tool.

Negative.

- Adds a write, and usually a read, to the hot path of every message,
  measurably increasing per-message latency and database write volume on
  high-throughput consumers.
- Requires a retention and pruning strategy from day one; skipping this is
  the single most common operational failure mode, discussed next.
- Only solves the problem when the side effect and the inbox write share one
  transactional resource; it gives false confidence if applied naively around
  a handler that also calls a remote service, because the remote call is not
  covered by the local transaction's atomicity.
- Introduces a new failure mode of its own if the deduplication key is chosen
  poorly, for example reusing a broker-assigned message ID that some brokers,
  including SQS standard queues under specific conditions, do not guarantee
  remains stable across a redelivery.

## 11. Failure modes and misuse

**Symptom.** A message that was legitimately retried after a long outage is
silently dropped instead of processed.
**Cause.** The inbox retention window was set shorter than the realistic
maximum time a message can sit undelivered or unacknowledged, for example
during a multi-hour deployment freeze, so the original inbox row was pruned
before the retry arrived, and the retry is then treated as new, but by that
point the retry's payload may reference state that has since changed,
producing a subtly wrong result rather than a clean reprocess.
**Fix.** Set the retention window based on the broker's actual maximum
redelivery or dead-letter timeout, with margin, and monitor the gap between a
message's original timestamp and its retry timestamp so a near-miss on the
window is visible before it becomes an actual miss.

**Symptom.** Duplicate side effects still occur under load, despite the inbox
table existing.
**Cause.** The check and the insert are two separate statements, run without a
transaction wrapping them, or the check uses a plain SELECT with no unique
constraint or row lock backing it, so two concurrent workers processing the
same redelivered message race each other, both see no existing row, and both
apply the side effect.
**Fix.** Enforce the deduplication guarantee at the database level with a
unique constraint on the message identifier column, and either use the
unique-constraint-violation-as-signal variant or wrap an explicit SELECT with
row-level locking inside the same transaction as the side effect, never as a
separate connection or a separate transaction.

**Symptom.** The consumer's throughput degrades over months in production
even though message volume is flat.
**Cause.** The inbox table has no retention sweeper, or the sweeper is
disabled or broken, so the table and its unique index grow without bound, and
every insert now pays for an ever-larger index maintenance cost.
**Fix.** Ship the retention sweeper as a required, monitored component of the
pattern from the start, not as an optional cleanup task, and alert on inbox
table row count growth relative to message volume.

**Symptom.** A handler applies a message's side effect twice even though the
inbox check reported no existing row both times.
**Cause.** The handler itself performs a remote call, for example charging a
payment provider, and the remote call is not covered by the local database
transaction, so a crash after the remote call succeeds but before the local
commit leaves the inbox row absent, and the redelivered message runs the
remote call again.
**Fix.** Recognise this as outside the applicability of the Inbox pattern
alone. The remote call needs its own idempotency key, generated once and
reused across retries, honoured by the remote service, which is the
Idempotent Consumer pattern applied at the second boundary, not solvable by
the first consumer's local inbox table.

**Symptom.** Two different messages are treated as duplicates of each other
and only one is ever processed.
**Cause.** The chosen message identifier is not actually unique per logical
message, for example the producer reused a correlation ID across multiple
distinct events, or a broker-level message ID was reused after a queue
redrive operation.
**Fix.** Generate the deduplication identifier at the point the event is
first created, ideally the same identifier the producer's own Transactional
Outbox row already carries, rather than relying on a broker-supplied ID whose
uniqueness guarantee the consumer has not independently verified.

## 12. Trade-off matrix

| Concern | Inbox pattern | Idempotent Consumer without a table | Broker-provided exactly-once (e.g. Kafka Streams EOS) |
|---|---|---|---|
| Works across heterogeneous brokers | Yes, broker-agnostic | Yes, broker-agnostic | No, confined to messages that never leave the guaranteeing platform |
| Requires a local transactional database | Yes, this is the core mechanism | Only if the naturally-idempotent operation is itself a DB write | Not from the application, the platform provides the guarantee |
| Handles side effects that are not naturally idempotent | Yes | No, relies entirely on the operation already being idempotent | Yes, within the platform's boundary |
| Operational overhead | Retention sweeper, index maintenance | None beyond normal schema design | Platform configuration and version alignment across the whole pipeline |
| Guarantees ordering | Only with the sequence-checked variant | No, unrelated concern | Yes, per partition, by construction of the platform |
| Protects a downstream remote call the handler makes | No, only protects the local write | No | No |

## 13. Related and incompatible patterns

**Transactional Outbox.** The producer-side mirror of this pattern, documented
in `transactional-outbox.md`. A message that originates from a service using
the Outbox pattern already carries a stable event ID generated once, at
write time, which is frequently the best possible deduplication key for the
downstream consumer's inbox table, closing the loop between the two patterns
across a service boundary.

**Idempotent Consumer.** Documented in `idempotent-consumer.md`, this is the
broader design goal, that a consumer produces the same result whether a
message is delivered once or many times. The Inbox pattern is one concrete,
storage-backed technique for achieving idempotent consumption when the side
effect is a local database write; it is not the only way to be an idempotent
consumer, since a naturally idempotent operation, such as a keyed upsert,
achieves the same goal without a separate table.

**Domain Event.** Documented in `domain-event.md`, the events an inbox table
deduplicates are frequently domain events published by an upstream service,
so the pair composes naturally in event-driven architectures where a chain of
services each consume, react to, and republish domain events.

**Saga.** A saga orchestrator or a saga participant that reacts to messages
benefits directly from an inbox table, because a saga step run twice due to
message redelivery is a common source of saga correctness bugs, particularly
when a saga step has a monetary or inventory side effect.

**Database per Service.** Documented in `database-per-service.md`, this
pattern is the precondition that makes the Inbox pattern's core promise, one
local transaction covering both the check and the side effect, actually
available. A service sharing a database with other services, the explicitly
Incompatible pattern noted in the frontmatter, may still technically place an
inbox table in the shared schema, but doing so reintroduces exactly the
cross-service coupling that Database per Service exists to avoid, and this
family treats that combination as an anti-pattern rather than a supported
variant.

## 14. Refactoring path in and out

**Introducing the pattern into a consumer that has none.** First, identify the
consumer's business side effect and confirm it writes to a database the
consumer controls; if it does not, stop here, because the pattern does not
apply as described in dimension 4. Second, add a migration creating the inbox
table with a unique constraint on the chosen message identifier column.
Third, wrap the existing handler body in an explicit local transaction if one
does not already exist, and insert the check-then-insert logic at the top of
that transaction, before the existing side-effect code runs. Fourth, move the
broker acknowledgement call to after the transaction commits, if it was
previously called before or during the handler; this reordering is itself
often the fix for a pre-existing duplicate-processing bug, independent of
adding the table. Fifth, add the retention sweeper as its own scheduled job
before enabling the feature in production, never after.

**Removing the pattern when it no longer earns its place.** This is rare in
practice, because the correctness property the pattern buys is difficult to
give up safely, but it does happen when a consumer's side effect is refactored
into a naturally idempotent upsert keyed by the same identifier that used to
live in the inbox table. In that case, first confirm the upsert is genuinely
idempotent under concurrent execution, not merely under a single-threaded
mental model, then migrate the deduplication key to be the primary key or a
unique constraint on the business table itself rather than a separate inbox
row, then remove the now-redundant inbox check and its table in a later
migration once the upsert has been running correctly in production for a full
retention window's worth of time, so any in-flight redeliveries from before
the change are still caught by the old mechanism during the transition.

## 15. Testing and verification

The pattern is easy to test because its entire correctness claim is a
property of one transaction, which is straightforward to exercise directly
against a real or an in-memory instance of the target database, rather than
against the broker.

Write a test that calls the handler twice with the identical message
identifier and asserts the side effect's observable state changed exactly
once, for example a balance decremented by one unit, not two, after both
calls. This single test is the core specification of the pattern and should
exist for every handler that uses an inbox table.

Write a concurrency test that fires the handler for the same message
identifier from two threads or two processes simultaneously, and assert that
exactly one of the two side effects was applied and that neither call
returned an error to its caller if the deduplication is meant to be silent.
This test is what actually exercises the unique-constraint-violation path
rather than the simpler sequential check-then-insert path, and it is the
test most teams skip and the one most likely to catch the race condition
described in dimension 11.

Write a retention test that inserts an inbox row with a timestamp older than
the retention window, runs the sweeper, and asserts the row is gone and that
a subsequent redelivery of that same identifier is now, correctly, treated as
new.

For the broker-facing integration itself, use a test double for the broker
that can simulate redelivery deterministically, redelivering the same message
a configurable number of times with a configurable delay, rather than relying
on a real broker's actual timeout behaviour, which is slow and flaky in a
test suite. Assert end to end that the business side effect's final state is
identical whether the test double delivers the message once or five times.

## 16. Observability signals

Track the ratio of inbox table inserts that hit the unique-constraint
duplicate path versus the ratio that insert cleanly; a healthy consumer shows
a small, roughly stable duplicate rate that tracks the broker's own known
redelivery rate, and a rising duplicate rate is usually a signal of an
upstream producer bug, a broker misconfiguration causing excessive
redelivery, or a consumer that is crashing before acknowledging more often
than expected.

Track inbox table row count and index size over time, alerting on growth that
outpaces message volume, which is the leading indicator that the retention
sweeper has stopped running.

Log, at minimum at debug level and at warn level for anything unusual, every
time a message is skipped as a duplicate, including its identifier and its
original processed timestamp, so an operator investigating "why didn't this
event do anything" has a direct answer rather than needing to reconstruct it
from broker-side redelivery counts.

Measure the age distribution of messages that arrive as duplicates, meaning
the time between a message's original processed timestamp and its duplicate
delivery's arrival time; a distribution with a long tail approaching the
retention window is the leading indicator that the window is too short before
any message is actually dropped.

## 17. Security and privacy implications

The inbox table itself typically stores only a message identifier and a
timestamp, which is low-sensitivity metadata, but the identifier chosen as
the deduplication key can leak information if it is derived from, or embeds,
personally identifiable data, for example a raw email address used as the key
rather than an opaque event UUID; prefer an opaque identifier generated by
the producer specifically for deduplication purposes.

Because the inbox table is an append-mostly audit trail of every message the
service has ever processed, it becomes, incidentally, a record of the
service's message-level activity, and it should be included in the same data
retention and right-to-erasure review as any other table that could indirectly
reconstruct a user's activity history, particularly under GDPR-style
regulation where "processed event IDs referencing this user" can itself be
considered personal data depending on jurisdiction and on how directly the
identifier ties back to the user; this is a judgement call for the service's
own data protection review, not a settled legal fact this entry asserts.

A consumer that trusts the message identifier supplied by an upstream
producer without validating that the identifier's format matches what the
producer is actually expected to send opens a narrow denial-of-service
surface, where a malicious or buggy upstream sender floods distinct,
never-before-seen identifiers, growing the inbox table without bound faster
than the retention sweeper can prune it; validating identifier shape and
rate-limiting per producer at the endpoint mitigates this.

## 18. References

- Oskar Dudycz, "Outbox, Inbox patterns and delivery guarantees explained",
  event-driven.io, 30 December 2020,
  <https://event-driven.io/en/outbox_inbox_patterns_and_delivery_guarantees_explained/>,
  verified 2026-08-02.
- Chris Richardson, *Microservices Patterns*, Manning, 2018, chapter 3,
  discussion of tracking processed message IDs to make a consumer idempotent
  under at-least-once delivery.
- Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns*,
  Addison-Wesley, 2003, Idempotent Receiver.
- Milan Jovanović, "Implementing the Inbox Pattern for Reliable Message
  Consumption",
  <https://milanjovanovic.tech/blog/implementing-the-inbox-pattern-for-reliable-message-consumption>,
  verified 2026-08-02.
- Wolverine documentation, "Durable Messaging",
  <https://wolverinefx.net/guide/durability/>, verified 2026-08-02.
- Particular Software, NServiceBus Outbox documentation,
  <https://docs.particular.net/nservicebus/outbox/>, verified 2026-08-02.
- Apache Camel documentation, "Idempotent Consumer EIP",
  <https://camel.apache.org/components/next/eips/idempotentConsumer-eip.html>,
  verified 2026-08-02.
- `patterns/10-microservices/transactional-outbox.md`, this repository, the
  producer-side counterpart pattern.
- `patterns/10-microservices/idempotent-consumer.md`, this repository, the
  broader design goal this pattern serves.
- `patterns/10-microservices/distributed-transaction-coordinator-antipattern.md`,
  this repository, the alternative this pattern replaces.

## Code examples

### TypeScript

```typescript
interface InboxRow {
  id: string;
  processedAt: Date;
}

interface DbClient {
  query(sql: string, params: unknown[]): Promise<{ rows: unknown[] }>;
  begin(): Promise<Transaction>;
}

interface Transaction {
  query(sql: string, params: unknown[]): Promise<{ rows: unknown[] }>;
  commit(): Promise<void>;
  rollback(): Promise<void>;
}

async function consumeOnce(
  db: DbClient,
  messageId: string,
  applySideEffect: (tx: Transaction) => Promise<void>
): Promise<"processed" | "duplicate"> {
  const tx = await db.begin();
  try {
    await tx.query(
      "INSERT INTO inbox (id, processed_at) VALUES ($1, now())",
      [messageId]
    );
    await applySideEffect(tx);
    await tx.commit();
    return "processed";
  } catch (err) {
    await tx.rollback();
    if (isUniqueViolation(err)) {
      return "duplicate";
    }
    throw err;
  }
}

function isUniqueViolation(err: unknown): boolean {
  return (
    typeof err === "object" &&
    err !== null &&
    "code" in err &&
    (err as { code: string }).code === "23505"
  );
}

class FakeTx implements Transaction {
  inbox = new Set<string>();
  applied = 0;
  async query(sql: string, params: unknown[]): Promise<{ rows: unknown[] }> {
    const id = params[0] as string;
    if (this.inbox.has(id)) {
      const e = new Error("duplicate key value violates unique constraint");
      (e as Error & { code: string }).code = "23505";
      throw e;
    }
    this.inbox.add(id);
    return { rows: [] };
  }
  async commit(): Promise<void> {}
  async rollback(): Promise<void> {}
}

async function main(): Promise<void> {
  const sharedTx = new FakeTx();
  const db: DbClient = {
    query: (sql, params) => sharedTx.query(sql, params),
    begin: async () => sharedTx,
  };

  const effect = async () => {
    sharedTx.applied += 1;
  };

  const first = await consumeOnce(db, "m-42", effect);
  const second = await consumeOnce(db, "m-42", effect);

  if (first !== "processed" || second !== "duplicate" || sharedTx.applied !== 1) {
    throw new Error("inbox pattern invariant violated");
  }
  console.log("first delivery:", first, "second delivery:", second, "applied:", sharedTx.applied);
}

main();
```

### Python

```python
import sqlite3


def consume_once(conn: sqlite3.Connection, message_id: str, apply_side_effect) -> str:
    cur = conn.cursor()
    try:
        cur.execute("BEGIN")
        cur.execute(
            "INSERT INTO inbox (id, processed_at) VALUES (?, datetime('now'))",
            (message_id,),
        )
        apply_side_effect(cur)
        conn.commit()
        return "processed"
    except sqlite3.IntegrityError:
        conn.rollback()
        return "duplicate"
    except Exception:
        conn.rollback()
        raise


def setup(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE inbox (id TEXT PRIMARY KEY, processed_at TEXT NOT NULL)"
    )
    conn.execute("CREATE TABLE ledger (balance INTEGER NOT NULL)")
    conn.execute("INSERT INTO ledger (balance) VALUES (0)")


def debit_one(cur: sqlite3.Cursor) -> None:
    cur.execute("UPDATE ledger SET balance = balance + 1")


def main() -> None:
    conn = sqlite3.connect(":memory:")
    setup(conn)

    first = consume_once(conn, "m-42", debit_one)
    second = consume_once(conn, "m-42", debit_one)

    balance = conn.execute("SELECT balance FROM ledger").fetchone()[0]

    assert first == "processed", first
    assert second == "duplicate", second
    assert balance == 1, balance

    print("first delivery:", first, "second delivery:", second, "balance:", balance)


if __name__ == "__main__":
    main()
```

### Go

```go
package main

import (
	"errors"
	"fmt"
	"sync"
)

var errDuplicate = errors.New("duplicate message")

type Inbox struct {
	mu   sync.Mutex
	seen map[string]bool
}

func NewInbox() *Inbox {
	return &Inbox{seen: make(map[string]bool)}
}

func (i *Inbox) ConsumeOnce(messageID string, applySideEffect func()) (string, error) {
	i.mu.Lock()
	defer i.mu.Unlock()

	if i.seen[messageID] {
		return "duplicate", nil
	}

	applySideEffect()
	i.seen[messageID] = true
	return "processed", nil
}

func main() {
	inbox := NewInbox()
	applied := 0

	debit := func() {
		applied++
	}

	first, err := inbox.ConsumeOnce("m-42", debit)
	if err != nil {
		panic(err)
	}
	second, err := inbox.ConsumeOnce("m-42", debit)
	if err != nil {
		panic(err)
	}

	if first != "processed" || second != "duplicate" || applied != 1 {
		panic(fmt.Sprintf("invariant violated: first=%s second=%s applied=%d", first, second, applied))
	}

	fmt.Printf("first delivery: %s, second delivery: %s, applied: %d\n", first, second, applied)
}
```

A Rust or Java sample is omitted from this entry. The pattern is a database
transaction shape rather than a language feature, and the three samples above
already show the idiom across a callback-based async style (TypeScript), a
synchronous DB-API style (Python), and an explicit-locking style without a
database driver in scope (Go), which covers the meaningfully distinct ways
this pattern is expressed. A Java or Rust reader applies the identical shape,
a unique constraint plus a check-then-insert inside one transaction, using
that language's own transaction API.
