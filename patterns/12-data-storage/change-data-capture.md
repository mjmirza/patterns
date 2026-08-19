---
name: Change Data Capture
slug: change-data-capture
family: 12-data-storage
category: Data and Storage
aliases: [CDC, Log-Based Replication, Database Streaming]
first_described: "Practitioner term formalized through commercial ETL and replication tooling in the 1990s, later re-grounded in log-based streaming by Martin Kleppmann"
maturity: established
related: [event-sourcing, outbox-pattern, materialized-view, saga, cqrs]
incompatible_with: []
verified: 2026-08-02
---

# Change Data Capture

## 1. Name, aliases, and lineage

Change Data Capture, universally abbreviated CDC, names the practice of
identifying and streaming every row-level insert, update, and delete applied to
a database so that downstream systems can react to them without re-querying
the source. The term predates the modern log-based tooling that now defines
it. It surfaces in Oracle and IBM data-warehousing literature from the 1990s,
where CDC described any technique, trigger-based, timestamp-based, or
snapshot-diff, for feeding an incremental extract into a data warehouse rather
than re-running a full extract nightly. There is no single foundational paper
that coined the phrase the way Gang of Four coined Factory Method. The name is
a description of a problem class that acquired a standard name through
industry usage before any one implementation dominated.

The modern, log-based meaning of CDC was re-articulated for a streaming-first
audience by Martin Kleppmann, who devotes a full section of *Designing
Data-Intensive Applications*, O'Reilly, 1st edition, 2017, chapter 11 ("Stream
Processing"), to change data capture as a technique for treating a database's
replication log as a stream of change events that other systems can consume
(Kleppmann, chapter 11, "Change Data Capture" section). Kleppmann's framing,
that a database's internal write-ahead log or binary log is itself an
append-only event stream waiting to be exposed, is the intellectual bridge
between older batch-oriented CDC tools and the current generation of
log-based, Kafka-fronted CDC platforms such as Debezium.

Two aliases persist in casual use. **Log-Based Replication** is accurate for
the dominant modern implementation strategy but is narrower than CDC itself,
because CDC also covers trigger-based and query-based capture. **Database
Streaming** is a marketing-driven alias used by vendors (Fivetran, Airbyte,
Estuary) to describe CDC connectors as part of a broader ELT product, and it
sometimes gets stretched to include non-CDC batch extraction, which makes it
the least precise of the three names. This entry uses CDC to mean the general
problem, and calls out log-based CDC specifically wherever the distinction
between capture strategies matters, because the strategy chosen determines
almost every consequence discussed in dimensions 10 and 11.

## 2. Problem and context

A service owns a database that other services, warehouses, caches, and search
indexes need to stay synchronized with. The naive answer is polling, where a
downstream job runs a query such as `SELECT * FROM orders WHERE updated_at >
last_poll` every few minutes. Polling has three structural problems that do
not go away with a shorter interval. First, it cannot see a delete, because a
deleted row produces no row to select; systems work around this with soft
deletes, which then leak into every other query in the codebase. Second, it
cannot see intermediate states, because a row updated twice between polls is
observed only in its final state, which corrupts any downstream logic that
depends on the sequence of changes (a price that goes up then down within one
polling window looks like no change at all). Third, polling puts read load on
the source database proportional to the number of downstream consumers, and
that load competes with the application's own transactional traffic on the
exact table that traffic is heaviest on.

Trigger-based capture, where a database trigger writes each change into a
shadow "audit" table, solves the completeness problem, every insert, update,
and delete is guaranteed to produce a row, but it does so by doubling every
write inside the same transaction, and it does so inside the source database's
own write path, so the technique that is supposed to relieve pressure on the
source instead adds synchronous work to the source's transaction commit
latency.

CDC in its modern, log-based form arose to solve exactly this. Every
production relational database already maintains an internal, ordered,
durable, append-only log of every committed write, for its own crash-recovery
purposes. Postgres calls it the write-ahead log (WAL), MySQL calls it the
binary log (binlog), SQL Server calls it the transaction log, MongoDB calls it
the oplog. That log already contains, in commit order, every insert, update,
and delete the database has ever applied, including the old and new row values
in most configurations. Log-based CDC reads that log instead of the tables,
which means it observes every change including deletes, observes every
intermediate state, and does so by tailing a log the database is writing
anyway, at no additional cost to the source's own transactional throughput.
The context in which CDC belongs is any system where a source of truth needs
to feed one or more downstream consumers a complete, ordered, low-latency
record of its changes, and where the source's own write path must remain
untouched by the presence or absence of those consumers.

## 3. Forces

**Completeness versus intrusiveness.** Trigger-based capture is complete by
construction (a trigger fires on every write) but intrusive (it adds a
synchronous write inside the source's own transaction). Log-based capture is
non-intrusive to the write path but depends entirely on the database's log
retention and replication configuration being correct; a rotated-away log
segment produces silent gaps rather than a loud failure.

**Latency versus source load.** Query-based (polling) capture can be tuned to
arbitrary latency by shortening the interval, but every reduction in interval
increases source read load linearly, until at some interval the polling
traffic itself becomes the bottleneck it was meant to avoid.

**Ordering guarantee versus horizontal scalability.** A single source
database produces one true, globally-ordered log per shard. Fanning that log
out to N parallel consumers for throughput destroys the single global
ordering unless the fan-out preserves per-key ordering, which is exactly what
Kafka's per-partition ordering guarantee is used for downstream. A CDC
pipeline that scales out arbitrarily and a CDC pipeline that preserves strict
global ordering are, past a point, in direct tension.

**Schema coupling versus schema freedom.** CDC events mirror the source
table's schema by default, which means every downstream consumer is implicitly
coupled to the source team's column names and types. Loosening that coupling
(via an explicit event contract, discussed under the outbox pattern in
dimension 13) costs engineering effort the raw-CDC approach avoids.

**Exactly-once semantics versus operational simplicity.** Guaranteeing that a
downstream consumer applies every change exactly once, not zero times on
failure and not twice on retry, requires either idempotent consumers keyed on
a change's log sequence number, or a two-phase commit across the CDC pipeline
and the sink, both of which add real operational and code complexity that a
simpler at-least-once pipeline avoids at the cost of that duplicate-handling
burden falling onto every consumer.

This entry favors log-based CDC as the default recommendation for exactly the
first two forces, non-intrusive to source writes and complete including
deletes, while being explicit that it sacrifices operational simplicity
(dimension 10) and does not by itself solve the schema-coupling force, which
is why dimension 13 treats the outbox pattern as CDC's most important
companion rather than a competitor.

## 4. Applicability and non-applicability

Reach for CDC when the following conditions hold.

- Multiple downstream systems (a search index, a cache, a data warehouse, a
  materialized read model in another service) need to reflect every write to
  a source database, including deletes, without querying the source directly.
- Latency from write to downstream visibility needs to be sub-second to
  low-seconds, ruling out batch ETL windows.
- The source database's write throughput and latency must remain unaffected
  by the number or behavior of downstream consumers.
- A service-to-service integration needs to migrate off synchronous
  request-response calls or dual writes toward an asynchronous, replayable
  event stream, and the source of truth is (or can remain) a conventional
  relational database rather than an event-sourced aggregate.
- Zero-downtime database migration or replatforming is required, where CDC
  streams ongoing changes from the old database into the new one after an
  initial bulk snapshot, until cutover.

Do NOT reach for CDC under any of the following conditions.

- Only one downstream consumer needs the data and it can tolerate calling the
  source service's own API. Standing up a CDC pipeline (a connector, a broker,
  operational monitoring for log-position lag) to serve a single consumer that
  a synchronous API call would satisfy is disproportionate infrastructure for
  the problem.
- The source system's schema changes frequently and downstream consumers need
  a stable, versioned contract. Raw table-mirroring CDC propagates every
  column rename and type change straight to consumers; the outbox pattern
  (dimension 13) exists specifically to decouple this, and reaching for raw
  CDC in this situation is a known failure mode (dimension 11).
- The domain is naturally event-sourced already, meaning the write model
  already emits domain events as its primary artifact (see the Event Sourcing
  entry). CDC replicates a database's row states after the fact; an
  event-sourced system already has the event stream as its source of truth,
  and layering CDC on top of it is redundant capture of a derived artifact.
- Regulatory or contractual data-residency rules forbid streaming row-level
  changes, including deleted and superseded values, outside a certification
  boundary. Log-based CDC by design captures the full before-and-after of
  every row, including values a data-minimization policy intended to be
  ephemeral, and that visibility must be explicitly reasoned about, not
  assumed away.
- The source database does not expose a durable, retained replication log at
  all (some managed database tiers cap WAL or binlog retention aggressively,
  or disable logical replication entirely), and the operational cost of
  reconfiguring the database to support it is not acceptable for the team
  that owns it.

## 5. Structure

**Source database.** The system of record whose row-level changes are being
captured. Exposes a durable, ordered, append-only log of committed writes
(WAL, binlog, oplog, or equivalent), either natively or via an
administrator-enabled logical replication feature.

**Capture agent (connector).** The component that reads the source's
replication log (or, in the weaker strategies, polls tables or reads trigger
output), decodes the log's native binary or wire format into structured change
events, and performs an initial consistent snapshot of existing data before
tailing begins. Debezium's per-database connectors (for Postgres, MySQL,
MongoDB, SQL Server, Oracle, and others) are the canonical example of this
role.

**Change event.** The unit the capture agent emits, one per row-level change,
carrying at minimum the table and primary key identifying the row, the
operation type (create, update, delete, or read-during-snapshot), the row's
state before the change and after the change (before is often unavailable for
inserts and sometimes unavailable for updates depending on the source's log
configuration), and a source-native ordering token (a log sequence number, a
binlog position plus GTID, or an oplog timestamp) that establishes a total
order per source.

**Transport / event log.** The durable, ordered, replayable medium the change
events are published into, most commonly a partitioned log such as Apache
Kafka, which preserves per-key ordering, allows multiple independent
consumers to read at their own pace, and allows a new consumer to be added
later and replay history from its own chosen offset.

**Sink connector / consumer.** The component that reads change events from the
transport and applies them to a downstream target, materializing a search
index document, updating a cache entry, writing a row into a data warehouse
table, or triggering an application-level side effect. Consumers are
responsible for idempotency, because the transport guarantees at-least-once
delivery, not exactly-once application, in the general case.

**Schema registry (optional but common).** A component that stores the
serialization schema (commonly Avro or Protobuf via Confluent Schema
Registry, or JSON Schema) for each table's change events, so that a schema
change in the source is either propagated compatibly to consumers or flagged
as a breaking change before it reaches them.

## 6. ASCII structure diagram

```
+-------------------+
|  Source Database   |
|  (Postgres/MySQL)  |
|                     |
|  +---------------+  |
|  | Table  orders  |  |
|  +---------------+  |
|                     |
|  +---------------+  |
|  |  WAL / binlog |  |  <- append-only, database writes here anyway
|  +-------+-------+  |
+----------|----------+
           | logical replication slot / binlog stream
           v
+-------------------+
|   Capture Agent    |
|  (Debezium/Maxwell) |
|                     |
|  1. initial snapshot|
|  2. decode log      |
|  3. emit change event
+----------|----------+
           | (table, op, before, after, LSN)
           v
+-------------------------+
|  Transport (Kafka topic) |
|  partitioned by key       |
|  orders.public.orders     |
+----+---------+---------+--+
     |         |         |
     v         v         v
+--------+ +--------+ +--------+
| Sink   | | Sink   | | Sink   |
| Search | | Cache  | | Data   |
| Index  | | Redis  | | Warehouse
+--------+ +--------+ +--------+
```

## 7. Dynamics

The sequence below traces one update through a log-based CDC pipeline,
Debezium-style, from source commit to a downstream search index reflecting
the change.

```
1. Application commits UPDATE orders SET status='shipped' WHERE id=42
   -> source database writes the change to its WAL/binlog as part of
      the commit itself (this write happens regardless of CDC's existence)

2. Capture agent, already tailing the log via a replication slot,
   reads the new log entry
   -> decodes it into a change event
        table=orders op=u before(status=packed)
        after(status=shipped) lsn=0/16B3748

3. Capture agent publishes the change event to the transport
   -> Kafka topic orders.public.orders, partitioned by order id
      so all changes to order 42 land in the same partition in order

4. Search-index sink connector, subscribed to that topic,
   consumes the event
   -> checks whether it has already applied lsn 0/16B3748 for this
      key (idempotency check, because delivery is at-least-once)
   -> if not yet applied, upserts the order document in the index
      with status=shipped, records lsn 0/16B3748 as applied

5. A network partition or consumer restart between steps 3 and 4
   -> Kafka retains the event at its committed offset
   -> on recovery, the consumer resumes from its last committed
      offset and reprocesses; step 4's idempotency check absorbs
      the reprocessed duplicate without a double-apply

6. Capture agent itself restarts (process crash)
   -> resumes tailing from its last acknowledged log position,
      not from the beginning; the replication slot on the source
      database guarantees the log segment covering that position
      has not been discarded, because the slot's presence tells
      the source database to retain it
```

The two failure-recovery branches in steps 5 and 6 are the structurally
important part of the dynamics. The pattern's entire reliability story rests
on the source retaining log segments the capture agent has not yet
acknowledged, and on every downstream consumer treating delivery as
at-least-once rather than exactly-once.

## 8. Implementation variants

**Log-based CDC (the dominant modern variant).** Reads the database's native
replication log directly. Postgres exposes this via logical replication slots
and the `pgoutput` or `wal2json` output plugin; MySQL exposes it via binlog
row-based replication with GTIDs enabled; MongoDB exposes it via the oplog or,
in modern versions, change streams built on the oplog. Non-intrusive to
source writes, captures deletes and intermediate states, and is what Debezium,
Maxwell's Daemon, and AWS DMS's CDC mode all implement.

**Trigger-based CDC.** A database trigger on each table writes the changed
row (or a diff of it) into a shadow table or directly onto a message queue,
inside the same transaction as the original write. Complete by construction
and portable across database engines that lack a usable logical log, but adds
synchronous write amplification to every transaction and requires the trigger
logic to be maintained alongside every schema change. Used historically by
Oracle GoldenGate's trigger-based capture mode and by earlier-generation ETL
tools before log-based capture became standard.

**Query-based (timestamp or version-column) CDC.** Polls the source table on
an interval, filtering on an updated-at column or monotonically increasing
version column. Requires no special database privileges or replication
configuration and works against any queryable source including some managed
databases that disable logical replication, but cannot observe deletes
without a soft-delete convention, cannot observe intermediate states between
polls, and puts recurring read load on the source proportional to the
polling frequency and the number of consumers.

**Snapshot-diff CDC.** Periodically takes a full snapshot of a table and diffs
it against the previous snapshot to derive an implied changeset. The
heaviest-weight variant, generally reserved for sources with no other capture
mechanism available (legacy mainframe extracts, some SaaS export APIs), and
the least suited to low-latency use cases because a diff cycle is inherently
batch-shaped.

**Language-idiomatic framing.** CDC is infrastructure-level, not a
language-level construct, so there is no meaningful closure-versus-class
variant the way there is for, say, Strategy. The idiomatic variation across
languages appears entirely in the consumer, in a Go or Java Kafka consumer
implementing manual offset commits and an idempotency table lookup, versus a
higher-level framework (Kafka Streams, ksqlDB, Flink) that provides
exactly-once processing semantics across a topology as a first-class runtime
guarantee, removing the need to hand-write the idempotency check shown in
dynamics step 4.

## 9. Known production uses

**Debezium**, an open-source, Kafka Connect-based CDC platform originally
built at Red Hat, is the most widely deployed general-purpose CDC tool, with
connectors for Postgres, MySQL, MongoDB, SQL Server, Oracle, Db2, and
Cassandra. It operates as a set of source connectors that run inside Kafka
Connect and turn each database's native replication log into Kafka Connect
change event records (Debezium project, "Debezium Architecture" reference
documentation, https://debezium.io/documentation/reference/stable/architecture.html,
verified 2026-08-02). Debezium also ships the Outbox Event Router single
message transform specifically to support the outbox pattern described in
dimension 13 (Debezium project, "Outbox Event Router" reference documentation,
https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html,
verified 2026-08-02).

**Netflix DBLog** is a CDC framework built and run in production at Netflix
across tens of internal microservices. Its central engineering contribution
is a watermark-based algorithm that lets a full-table snapshot be taken
concurrently with ongoing log tailing, in interleaved chunks, without locking
the source table, and with the ability to pause and resume the snapshot at
will. The framework is described in Andreas Andreakis and Ioannis
Papapanagiotou, "DBLog. A Watermark Based Change-Data-Capture Framework,"
arXiv 2010.12597, https://arxiv.org/abs/2010.12597, verified 2026-08-02.

**LinkedIn Brooklin** (successor to LinkedIn's earlier Databus system) is
LinkedIn's production streaming platform, one of whose two primary declared
use cases is change data capture from LinkedIn's Espresso and Oracle data
stores, streaming low-latency change events so that dependent applications no
longer need to poll the source database for updates such as new job postings
or profile changes. LinkedIn Engineering, "Open sourcing Brooklin. Near
real-time data streaming at scale," https://engineering.linkedin.com/blog/2019/brooklin-open-source,
verified 2026-08-02.

**Confluent's Kafka Connect ecosystem**, the commercial platform built around
Apache Kafka, ships an Outbox Event Router single message transform for its
own connector ecosystem as a first-class, documented feature, indicating the
outbox-plus-CDC combination described in dimension 13 is treated as a
standard production pattern rather than a niche technique. Confluent
documentation, "Kafka Connect EventRouter SMT usage reference,"
https://docs.confluent.io/kafka-connectors/transforms/current/eventrouter.html,
verified 2026-08-02.

## 10. Consequences

**Positive.**

- Downstream systems receive a complete, ordered record of every change,
  including deletes and intermediate states, that polling structurally cannot
  provide.
- The source database's write-path latency and throughput are unaffected in
  the log-based variant, because the capture agent reads a log the database
  writes regardless of CDC's existence.
- Multiple independent consumers can be added over time without adding load
  to the source database, and a new consumer can replay history from the
  retained log rather than only seeing changes from the moment it started.
- Enables near-zero-downtime database migrations. An initial snapshot plus
  ongoing CDC tailing keeps a new datastore continuously synchronized with the
  old one until a brief cutover window, rather than requiring a long
  maintenance window for a full data copy.
- Decouples the timing of downstream processing from the timing of the
  original write; a slow or temporarily-down consumer does not block or slow
  the writing application, because the transport buffers events until the
  consumer catches up.

**Negative.**

- Operational surface area grows substantially. A capture agent process, a
  transport cluster (commonly Kafka), schema management, and per-consumer
  offset and idempotency tracking are all new systems that must be run,
  monitored, and kept available, none of which existed before CDC was
  introduced.
- Raw CDC events mirror the source table's physical schema, coupling every
  downstream consumer to the source team's internal column names, types, and
  migration history; a source-side column rename becomes a breaking change
  for every consumer simultaneously unless a schema-evolution and
  compatibility policy is enforced.
- Delivery is at-least-once in the general case, not exactly-once, which
  pushes the burden of idempotent application onto every single consumer.
- Log retention on the source database becomes a hard operational dependency.
  If the capture agent falls far enough behind, or is down long enough, that
  the source rotates away log segments the agent has not yet consumed, the
  gap is unrecoverable without a fresh full snapshot, and in the worst case
  this failure is silent rather than loud.
- Introduces meaningful replication lag as a first-class metric that did not
  exist before; a downstream consumer's view of the world is provably,
  measurably stale by some number of seconds, and application logic that
  assumes read-your-own-writes consistency against a CDC-derived read model
  will be wrong under load.

## 11. Failure modes and misuse

**Downstream data silently stops updating for a subset of rows, no error
anywhere.** Symptom, seen above. Cause, the source database rotated away a
WAL segment or binlog file the capture agent had not yet consumed, most
commonly because the capture agent was down or badly lagging for longer than
the source's log retention window, or because the replication slot itself
was dropped and recreated, losing its position. Fix, monitor replication
slot lag (bytes and time behind) as a first-class alert, not an afterthought;
set log retention generously relative to expected maximum capture-agent
downtime; treat a missing replication slot as a page-worthy event, and
recover via a fresh snapshot plus resumed tailing rather than assuming the
gap is small.

**Downstream consumers break every time the source team ships an unrelated
schema migration.** Symptom, seen above. Cause, raw table-level CDC was
adopted without an explicit, versioned event contract; consumers deserialize
change events directly against the source table's live schema, so a column
rename, type widening, or dropped column propagates as a breaking change to
every consumer at once. Fix, introduce the outbox pattern (dimension 13) so
the source team publishes an intentional, versioned domain event rather than
a raw row diff, or at minimum enforce backward-compatible schema evolution
through a schema registry with compatibility checking turned on before any
migration ships.

**A downstream read model shows a row applied out of order, an older update
overwriting a newer one.** Symptom, seen above. Cause, the sink connector is
not partitioned or keyed consistently with the source's per-row ordering, so
two changes to the same row land in different transport partitions and are
consumed by different consumer threads with no ordering guarantee between
them, or the consumer applies events by wall-clock arrival time rather than
by the source's log sequence number. Fix, partition the transport by the
row's primary key so all changes to one row are strictly ordered within one
partition, and have the consumer compare the incoming event's source LSN
against the LSN already applied for that key, discarding any event whose
LSN is not strictly greater, a last-write-wins guard keyed on source order,
not arrival order.

**The same change is applied twice downstream, producing duplicate side
effects (a duplicate notification sent, a counter incremented twice).**
Symptom, seen above. Cause, the consumer treats delivery as exactly-once
when the transport only guarantees at-least-once; a consumer crash after
applying a change but before committing its offset causes the same event to
be redelivered and reapplied on restart. Fix, make every downstream apply
idempotent, keyed on the change event's unique identifier (source LSN or an
explicit event id), by checking and recording the already-applied state
atomically with the apply itself, not as a separate step that can itself
fail independently.

**Initial backfill of a large table takes down the source database or
blocks writes for the duration of the snapshot.** Symptom, seen above.
Cause, a naive full-table snapshot uses a long-held table lock or a single
massive transaction to guarantee consistency, which is fine for small tables
but becomes a multi-hour lock or a huge replication-slot buildup on large,
actively-written tables. Fix, use an incremental, chunked, non-locking
snapshot algorithm, the watermark technique from Netflix's DBLog is the
reference approach, or Debezium's incremental snapshot feature built on the
same idea, that interleaves small chunked selects with ongoing log tailing
rather than locking the whole table for one large read.

## 12. Trade-off matrix

| Force | Log-based CDC | Trigger-based CDC | Query/polling CDC | Event Sourcing |
|---|---|---|---|---|
| Captures deletes | Yes, natively | Yes, natively | No, requires soft-delete convention | N/A, deletion is itself a domain event |
| Impact on source write latency | None | Adds synchronous write per transaction | None (writes untouched) | None; write path IS the event append |
| Impact on source read load | None | None | Grows with poll frequency times consumer count | None |
| Ordering guarantee | Total order per source, via log | Total order per source, via trigger sequence | No ordering between poll intervals | Total order by construction |
| Requires elevated source access | Yes, replication role | Yes, DDL to add triggers | No, standard read access | N/A, source is the event store |
| Retrofit onto existing legacy database | Straightforward if logical replication is available | Requires DDL changes to every captured table | Straightforward, works everywhere | Requires a rewrite of the write model |
| Schema coupling to consumers | Tight, mirrors physical schema | Tight, mirrors physical schema | Tight, mirrors physical schema | Loose, if events are modeled as domain concepts |
| Operational complexity added | High (agent, transport, offsets) | Medium (in-database, no new services) | Low (a scheduled job) | High (event store, projections) |

## 13. Related and incompatible patterns

**Outbox Pattern.** The single most important companion to CDC. Instead of
letting consumers subscribe to raw row-level changes across arbitrary tables,
the source service writes an explicit "outbox" row, an intentional,
versioned domain event, inside the same local transaction as its business
write, and CDC is then pointed at only that outbox table. This gives CDC's
transactional, no-dual-write reliability guarantee while giving consumers a
stable, source-team-controlled event contract instead of a raw schema mirror.
Debezium's Outbox Event Router transform exists specifically to reshape
captured outbox-table events into per-aggregate topics (Debezium
documentation, cited in dimension 9). Outbox and CDC are usually deployed
together, not as alternatives.

**Event Sourcing.** A related but distinct idea that is frequently confused
with CDC. Event Sourcing makes the append-only event log the primary source
of truth for the write model itself; CDC instead derives a secondary,
after-the-fact event stream from a conventional database's changes. A system
that is already event-sourced does not need CDC to expose its history,
because the events already exist as the write model; CDC is what you reach
for when the source of truth is, and will remain, a conventional relational
or document database.

**Materialized View.** A downstream CDC consumer that maintains a
denormalized, query-optimized copy of source data (a search index, a
read-model cache) is functionally implementing the materialized view
pattern, with CDC as its refresh mechanism instead of a periodic recompute.

**Saga.** In a distributed transaction spanning multiple services, CDC on an
outbox table is a common mechanism for reliably publishing the "step
completed" or "step failed" events that drive a saga's orchestration or
choreography, because it avoids the dual-write problem, writing to the local
database and separately publishing to a message broker with no atomicity
between the two, that a naive saga implementation would otherwise have.

**CQRS.** Command Query Responsibility Segregation frequently uses CDC as the
mechanism that keeps the query-side read model synchronized with the
command-side write model, when the two sides are backed by physically
separate stores.

No pattern in this catalog is structurally incompatible with CDC; the
closest to a conflict is Event Sourcing, where applying raw table-diff CDC on
top of an already event-sourced write model is redundant rather than
incompatible, capturing a derived state's changes when the authoritative
event stream already exists one layer down.

## 14. Refactoring path in and out

**Introducing CDC into a system without it.** Start narrow. Identify one
source table and one downstream consumer currently synchronized by polling
or by a batch nightly job, and prove out log-based capture on that single
pair first, including its snapshot, its lag monitoring, and its idempotent
consumer, before expanding to additional tables. Enable the source database's
logical replication feature (Postgres needs `wal_level = logical` plus a
replication slot; MySQL needs binlog in ROW format with GTIDs) as an
isolated, low-risk operational change, verified against a staging replica
before touching production. Stand up the capture agent pointed at that one
table, verify the initial snapshot completes and events start flowing, then
migrate the one downstream consumer from its polling loop to consuming from
the new event stream, running both in parallel and diffing their outputs
before retiring the polling loop. Only after this narrow slice is stable in
production should additional tables and consumers be added, and any table
whose consumers need a stable contract rather than a raw mirror should be
moved behind the outbox pattern (dimension 13) at that point rather than
retrofitted later, because retrofitting an event contract after consumers
already depend on the raw schema is itself the failure mode described in
dimension 11.

**Removing CDC once it stops earning its place.** CDC infrastructure is worth
decommissioning when the number of active downstream consumers on a pipeline
drops to one and that one consumer could be satisfied by a direct, synchronous
call to the source service instead, or when a table's change volume is low
enough and its consistency requirements loose enough that a scheduled batch
job (a nightly extract, a periodic reconciliation query) meets the actual
business need at a fraction of the operational cost. Removal proceeds in the
reverse order of introduction. Confirm no consumer still depends on the
stream by tracing consumer group membership on the transport, stop the sink
connectors first, then the capture agent, then, only once the source's
replication slot shows zero active consumers, drop the slot and disable
logical replication if no other table on that database still needs it.
Dropping the replication slot while a consumer is still attached is itself a
data-loss event for that consumer, so the ordering of this teardown matters
as much as the ordering of the introduction.

## 15. Testing and verification

CDC pipelines are tested at three separable layers, and conflating them is a
common source of false confidence.

**Capture agent configuration**, whether the connector is correctly capturing
the intended tables with the intended before/after payload, is verified with
an integration test that runs the actual database (via a container, using
something like Testcontainers' Postgres or MySQL module) plus the actual
capture agent, performs a scripted sequence of inserts, updates, and deletes,
and asserts on the exact shape of the emitted change events including
operation type and before/after values. This layer should never be mocked,
because the entire value of CDC rests on correctly decoding a specific
database's specific log format, which a mock cannot meaningfully stand in
for.

**Consumer idempotency and ordering** is verified independently of the real
capture agent, by feeding a consumer a synthetic stream of change events,
including deliberately duplicated events and deliberately out-of-order
events for the same key, and asserting the consumer's final applied state is
correct regardless. This is the layer where CDC's testing story becomes
easier than a naive polling consumer's. Because every event carries an
explicit source ordering token, the LSN, a consumer's ordering and
idempotency logic can be unit tested with plain in-memory event lists, no
database or broker required.

**End-to-end pipeline lag and correctness** is verified in a staging
environment that mirrors production's transport and connector topology,
where a synthetic write is made to the source and the test asserts the
change becomes visible at the sink within an expected latency bound, and
separately asserts, via a periodic reconciliation job comparing row counts or
checksums between source and sink, that no silent drift has accumulated over
time. This reconciliation check is the layer most teams skip and the layer
most responsible for catching the silent-gap failure mode described in
dimension 11, because unit and integration tests at the first two layers
cannot detect a replication slot that quietly stopped advancing in
production.

## 16. Observability signals

**Replication lag, in both bytes and time.** The distance between the
source's current log position and the capture agent's last-acknowledged
position, exposed by the source database itself (Postgres surfaces this
through pg_stat_replication.replay_lag and slot byte-lag via
pg_replication_slots; MySQL surfaces an equivalent seconds-behind metric on
the binlog consumer). A healthy pipeline shows this near zero and stable; a
failing one shows it monotonically growing.

**Capture agent connector state and restart count.** Whether the connector is
in a running, paused, or failed state, and how frequently it has restarted;
a connector cycling through restarts is very likely stuck on a poison
message or a schema it cannot decode, not transiently recovering.

**Consumer offset lag per consumer group.** How far behind the transport's
latest offset each downstream consumer is, tracked separately per consumer,
because one slow consumer falling behind should never be conflated with the
capture agent itself falling behind.

**Snapshot progress and duration**, during the initial-load phase of a new
table or a new consumer, tracked as rows processed versus estimated total, so
a stalled snapshot is visible as a flat progress line rather than silence.

**Dead-letter or error-topic volume.** Events a sink connector could not
apply (a malformed payload, a schema mismatch, a downstream write failure)
routed to an explicit dead-letter topic rather than dropped, with volume on
that topic as an alertable signal; a healthy pipeline's dead-letter topic is
empty.

A healthy dashboard shows near-zero replication lag on the source, near-zero
consumer offset lag on every consumer group, zero connector restarts in the
recent window, and zero dead-letter volume. The single most diagnostic
unhealthy pattern is source-side replication lag that is low while a
specific consumer's offset lag climbs, which isolates the problem to that
one consumer rather than to the capture pipeline as a whole.

## 17. Security and privacy implications

Log-based CDC captures the complete before-and-after state of every row a
table holds, including columns that application-level query access controls
might otherwise restrict, because the replication log operates below the
database's row-level or column-level security policies in most engines. A
CDC connector granted a broad replication role on a source database
effectively has read access to every column of every captured table,
regardless of what the application's own authorization layer would permit
for any given caller, so the capture agent's credentials and the transport's
downstream access controls become as security-sensitive as the source
database's own access controls, not a lesser concern. Sensitive columns
(payment details, government identifiers, health data) that flow through a
raw CDC pipeline are, by default, replicated in full to every topic and every
consumer with topic read access, which is a materially different exposure
surface than the source application's original, narrower query paths. Where
sensitive fields exist, they should either be excluded from capture at the
connector's column-filtering configuration, tokenized or masked by a
transform before reaching the transport, or isolated into an outbox event
whose payload the source team explicitly controls and can omit sensitive
fields from by design. CDC also captures deleted data on its way out, which
has a direct interaction with any right-to-erasure obligation such as
GDPR's Article 17. A row deleted from the source produces a delete change
event that itself contains the row's last known values, meaning erasure at
the source is not automatically erasure across every downstream system the
CDC pipeline has already fanned that row's history out to, and any
compliance process built around source-database deletion must separately
account for CDC-propagated copies at every sink and in the transport's own
retained log history.

## 18. References

1. Martin Kleppmann, *Designing Data-Intensive Applications*, O'Reilly Media,
   1st edition, 2017, chapter 11, "Change Data Capture" section.
2. Debezium project, "Debezium Architecture," Debezium reference
   documentation, https://debezium.io/documentation/reference/stable/architecture.html,
   verified 2026-08-02.
3. Debezium project, "Outbox Event Router," Debezium reference
   documentation, https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html,
   verified 2026-08-02.
4. Andreas Andreakis and Ioannis Papapanagiotou, "DBLog. A Watermark Based
   Change-Data-Capture Framework," arXiv 2010.12597, https://arxiv.org/abs/2010.12597,
   verified 2026-08-02.
5. LinkedIn Engineering, "Open sourcing Brooklin. Near real-time data
   streaming at scale," https://engineering.linkedin.com/blog/2019/brooklin-open-source,
   verified 2026-08-02.
6. Confluent, "Kafka Connect EventRouter SMT usage reference," Confluent
   documentation, https://docs.confluent.io/kafka-connectors/transforms/current/eventrouter.html,
   verified 2026-08-02.

## Code examples

The examples below show a minimal, idempotent CDC consumer applying a change
event to a downstream store, keyed on the source's log sequence number so
duplicate or replayed events are safely absorbed. They intentionally omit a
real Kafka client and a real database driver, standing those in with a small
in-memory stub, so each sample compiles or runs standalone and the
idempotency logic itself, the part CDC consumers actually get wrong in
production, is exercised directly.

### TypeScript

```typescript
type ChangeEvent = {
  table: string;
  op: "c" | "u" | "d";
  key: string;
  after: Record<string, unknown> | null;
  lsn: string;
};

class IdempotentSink {
  private appliedLsn = new Map<string, string>();
  private store = new Map<string, Record<string, unknown>>();

  apply(event: ChangeEvent): boolean {
    const lastLsn = this.appliedLsn.get(event.key);
    if (lastLsn !== undefined && lastLsn >= event.lsn) {
      return false;
    }
    if (event.op === "d") {
      this.store.delete(event.key);
    } else if (event.after) {
      this.store.set(event.key, event.after);
    }
    this.appliedLsn.set(event.key, event.lsn);
    return true;
  }

  get(key: string) {
    return this.store.get(key);
  }
}

const sink = new IdempotentSink();
const update: ChangeEvent = {
  table: "orders",
  op: "u",
  key: "42",
  after: { status: "shipped" },
  lsn: "0000000000000010",
};

console.log(sink.apply(update));
console.log(sink.apply(update));
console.log(sink.get("42"));
```

Run with `npx tsc --noEmit change-data-capture.ts` to type-check, or
transpile with `npx tsc change-data-capture.ts` followed by
`node change-data-capture.js`.

### Python

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class ChangeEvent:
    table: str
    op: str
    key: str
    after: Optional[dict]
    lsn: str


class IdempotentSink:
    def __init__(self) -> None:
        self._applied_lsn: dict[str, str] = {}
        self._store: dict[str, dict] = {}

    def apply(self, event: ChangeEvent) -> bool:
        last_lsn = self._applied_lsn.get(event.key)
        if last_lsn is not None and last_lsn >= event.lsn:
            return False
        if event.op == "d":
            self._store.pop(event.key, None)
        elif event.after is not None:
            self._store[event.key] = event.after
        self._applied_lsn[event.key] = event.lsn
        return True

    def get(self, key: str) -> Optional[dict]:
        return self._store.get(key)


if __name__ == "__main__":
    sink = IdempotentSink()
    update = ChangeEvent(
        table="orders", op="u", key="42",
        after={"status": "shipped"}, lsn="0000000000000010",
    )
    print(sink.apply(update))
    print(sink.apply(update))
    print(sink.get("42"))
```

Run with `python3 change-data-capture.py`.

### Go

```go
package main

import "fmt"

type ChangeEvent struct {
	Table string
	Op    string
	Key   string
	After map[string]any
	LSN   string
}

type IdempotentSink struct {
	appliedLSN map[string]string
	store      map[string]map[string]any
}

func NewIdempotentSink() *IdempotentSink {
	return &IdempotentSink{
		appliedLSN: make(map[string]string),
		store:      make(map[string]map[string]any),
	}
}

func (s *IdempotentSink) Apply(e ChangeEvent) bool {
	if last, ok := s.appliedLSN[e.Key]; ok && last >= e.LSN {
		return false
	}
	if e.Op == "d" {
		delete(s.store, e.Key)
	} else if e.After != nil {
		s.store[e.Key] = e.After
	}
	s.appliedLSN[e.Key] = e.LSN
	return true
}

func main() {
	sink := NewIdempotentSink()
	update := ChangeEvent{
		Table: "orders", Op: "u", Key: "42",
		After: map[string]any{"status": "shipped"},
		LSN:   "0000000000000010",
	}
	fmt.Println(sink.Apply(update))
	fmt.Println(sink.Apply(update))
	fmt.Println(sink.store["42"])
}
```

Run with `go run change-data-capture.go`.

Java and Rust are omitted for this entry. The pattern's essential logic, an
LSN-gated idempotent apply, is identical infrastructure-agnostic code in
every language capable of a map and a comparison, and the three languages
above already demonstrate the full technique; the parts of a real CDC
consumer that would meaningfully differ by language, such as a Kafka
client's specific API or a JDBC versus database/sql versus asyncpg driver,
are outside what this pattern entry is responsible for teaching.
