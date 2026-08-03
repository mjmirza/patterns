---
name: Transaction Log Tailing
slug: transaction-log-tailing
family: 10-microservices
category: Data Integration
aliases: [Log-Based Change Data Capture, Database Log Mining, CDC via Transaction Log, Log-Based CDC]
first_described: "Richardson, microservices.io pattern catalog, and Richardson, Microservices Patterns, Manning, 2018, chapter 3"
maturity: canonical
related: [transactional-outbox, saga, cqrs, event-sourcing, database-per-service, domain-event, strangler-application]
incompatible_with: [shared-database]
verified: 2026-08-03
---

# Transaction Log Tailing

## 1. Name, aliases, and lineage

The canonical name in the microservices literature is Transaction Log Tailing.
It is documented as one of two implementation strategies for the message relay
half of the Transactional Outbox pattern in Chris Richardson's pattern catalog
at microservices.io, and in his book *Microservices Patterns*, Manning
Publications, 2018, chapter 3, "Interprocess communication in a microservice
architecture" ([microservices.io, Transaction Log Tailing](https://microservices.io/patterns/data/transaction-log-tailing.html),
verified 2026-08-03). Richardson's own page states the pattern plainly. tail
the database transaction log and publish each change to a message broker
([microservices.io, Transaction Log Tailing](https://microservices.io/patterns/data/transaction-log-tailing.html),
verified 2026-08-03).

The pattern is older than the microservices catalog name attached to it. Every
relational database that supports physical or logical replication has shipped
a transaction log format designed to be read by a second process since long
before service-oriented architecture existed. MySQL's binary log dates to
MySQL 3.23 and exists specifically so a replica can reproduce a source's
writes ([MySQL 8.4 Reference Manual, section 5.4.4, The Binary Log](https://dev.mysql.com/doc/refman/8.4/en/binary-log.html),
verified 2026-08-03). What changed in the mid-2010s is not the log format, it
is the recognition that the same log a database exposes for its own replicas
can be tailed by an unrelated downstream consumer to build a search index, a
cache, a data warehouse feed, or a Kafka topic without ever touching the
database's transactional workload. The industry name for that broader
recognition is **Change Data Capture**, abbreviated CDC, and Transaction Log
Tailing is the log-based implementation technique of CDC, as distinct from
trigger-based CDC (a database trigger writes to a shadow table on every
write) and query-based CDC (a poller periodically diffs a timestamp or
version column). Martin Kleppmann's *Designing Data-Intensive Applications*,
O'Reilly, 2017, chapter 11, "Stream Processing," discusses change data
capture as a technique for turning a database into a stream of events by
reading its replication log rather than issuing queries against it. The two
most cited engineering write-ups of production log-tailing systems are
LinkedIn's Databus, a low-latency change capture system that tailed Oracle
redo logs and MySQL binlogs to feed derived data stores across LinkedIn, and
Netflix's DBLog, a generic change-data-capture framework built to unify
MySQL and PostgreSQL log tailing with an online, non-locking snapshot
capability ([Netflix Technology Blog, DBLog, A Generic Change-Data-Capture Framework](https://netflixtechblog.com/dblog-a-generic-change-data-capture-framework-69351fb9099b),
verified 2026-08-03). The open source project most responsible for making
log tailing an ordinary infrastructure choice rather than a bespoke one is
Debezium, a Red Hat project that ships log-based CDC connectors for
PostgreSQL, MySQL, MongoDB, SQL Server, Oracle, and Db2 as Kafka Connect
source connectors ([Debezium project README, github.com/debezium/debezium](https://raw.githubusercontent.com/debezium/debezium/main/README.md),
verified 2026-08-03).

A precise vocabulary matters because three related but different mechanisms
are frequently conflated under the word replication.

- **Physical (binary) replication.** The replica applies raw block or
  page-level changes and must run the same database engine and often the
  same major version as the source. This is what a hot standby uses. It is
  not usable by an arbitrary downstream consumer because the format is
  internal to the storage engine.
- **Logical replication (the mechanism PostgreSQL calls `Logical Decoding`).**
  The source translates its
  internal write-ahead log into a stream of row-level logical changes
  (insert, update, delete, with column values) that an arbitrary consumer,
  potentially written in any language, can subscribe to. PostgreSQL exposes
  this through its `Logical Decoding` interface and replication slots
  ([PostgreSQL 18 Documentation, chapter 47, `Logical Decoding`](https://www.postgresql.org/docs/current/logicaldecoding.html),
  verified 2026-08-03). MySQL exposes it through ROW-format binary logging,
  which records the before and after image of each changed row rather than
  the SQL statement that caused the change
  ([MySQL 8.4 Reference Manual, section 5.4.4](https://dev.mysql.com/doc/refman/8.4/en/binary-log.html),
  verified 2026-08-03).
- **Transaction Log Tailing.** The application-level pattern of building a
  downstream consumer that subscribes to a database's logical change stream
  and republishes those changes, usually to a message broker, for
  consumption by services that have no direct relationship to the source
  database. This is the pattern this entry documents. It is built on top of
  logical replication mechanics but is a distinct architectural decision.

## 2. Problem and context

A service owns a database, per the Database per Service pattern, and its
database is private. No other service may query it directly. That isolation
is exactly what makes the service independently deployable and lets it pick
its own schema and its own storage technology, but it creates a second
problem the moment any other part of the system needs to know that data
changed. A search service needs a fresh index when a product's price
changes. A recommendation service needs a fresh feature store when a user's
purchase history changes. A data warehouse needs a near-real-time feed for
analytics that cannot wait for a nightly batch export. An event-driven saga
needs to know an order was placed the instant the order row commits, not
five minutes later.

The straightforward answer, have the service publish an event to a message
broker in the same code path that writes the database row, hits the dual
write problem. A service that writes to its database and then separately
publishes a message to a broker is performing two independent operations
against two different systems with no shared transaction. If the process
crashes, the network partitions, or the broker is briefly unavailable
between the database commit and the publish call, the two systems disagree.
The database recorded the change and no one downstream ever heard about it,
or the message went out and the database transaction later rolled back,
so a message was published for a change that never actually happened. Two
phase commit across a relational database and a message broker is
technically possible in some stacks but is avoided in practice. It requires
broker support for XA transactions, which many popular brokers, Kafka
included, do not offer, it serializes writes across a distributed
coordinator, and it turns a broker outage into a database outage
([microservices.io, Transaction Log Tailing](https://microservices.io/patterns/data/transaction-log-tailing.html),
verified 2026-08-03).

Transaction Log Tailing sidesteps the dual write problem by removing the
second write from the service's code path entirely. The service performs
exactly one write, the ordinary database transaction it was always going to
perform. A second, independent process reads the database's own transaction
log, which the database itself writes durably and atomically as part of
every committed transaction, and republishes what it finds there. The
atomicity the pattern relies on is not a distributed transaction coordinator
built by the application, it is the atomicity the database engine already
guarantees between "the row changed" and "the transaction log recorded that
the row changed." Nothing can observe one without the other, because the
database's own crash recovery depends on that same guarantee.

The context in which this problem specifically arises is a microservice or
event-driven architecture with a Database per Service boundary, where at
least one downstream consumer needs a reliable, ordered, low-latency, and
complete feed of a service's data changes, and the team is unwilling to
accept the dual write problem, the throughput limit of a polling
publisher, or the schema coupling of query-based CDC.

## 3. Forces

**Consistency versus write-path simplicity.** The dual write problem is
solved by moving the second write out of the application transaction
entirely, but this means the application code, when it commits, has no
synchronous confirmation that the downstream event has been delivered
anywhere. The service that writes the row and the tailer that reads the log
are decoupled in time. This is the trade the pattern makes deliberately, and
it is the correct trade for most integration needs, but it is wrong for a
caller that needs a synchronous "yes, this has been published" acknowledgment
before returning to its own caller.

**Latency versus database load.** Log tailing usually delivers changes
within milliseconds of commit because the tailer streams the log rather than
scanning tables. This is dramatically lower latency than the sibling pattern,
Polling Publisher, which queries an outbox table on an interval and pays a
query against the live database on every poll. Log tailing shifts that cost
onto the replication mechanism the database was already going to run for its
own replicas, so incremental load on the primary is close to the cost of one
additional logical replication subscriber, which databases are built to
support cheaply.

**Completeness and ordering versus intrusiveness.** The transaction log
records every committed write to every table in commit order, which is
exactly the completeness and total order a reliable event feed needs. No
row can be updated without appearing in the log, so there is no code path
that can silently forget to publish, unlike a trigger a developer forgot to
add or an outbox insert a developer forgot to write in a new code path. The
cost of that completeness is that the tailer must be granted access to a
low-level database mechanism, replication, that is normally reserved for
database administrators, and that mechanism is different in wire format and
operational characteristics for every database engine.

**Operability versus reach.** Once the tailer and its position tracking are
running, they are close to zero-maintenance from the application developer's
point of view, no code in the service needs to change when a new consumer
wants the feed. But operating the tailer itself, monitoring replication
slot or binlog retention, handling schema changes, running a distributed
system that must not lose its committed position, is meaningfully harder
than running a poller, and it is a skill set closer to database
administration than to application development.

**Coupling and cost.** A generic tool such as Debezium removes most of the
implementation cost, at the price of running Kafka Connect and Kafka as
operational dependencies, and at the price of learning a connector's
per-database configuration surface. A team with no existing Kafka footprint
takes on a nontrivial new piece of infrastructure to adopt this pattern in
its most common form.

## 4. Applicability and non-applicability

### When to reach for it

- The system already uses the Transactional Outbox pattern and needs a
  reliable, low-latency mechanism to relay outbox rows to a broker, in place
  of, or as a faster alternative to, a Polling Publisher.
- A downstream consumer, such as search indexing, a cache, a materialized
  read model for CQRS, or a data warehouse, needs a complete, ordered,
  near-real-time feed of every change to a table or set of tables, and
  polling on an interval is too slow or too expensive against the live
  database.
- The team wants to migrate a legacy monolith's database into an
  event-driven architecture incrementally, per the Strangler Application
  pattern, and log tailing lets new services react to the legacy
  database's writes without modifying the legacy application's code at all.
- The organization already operates Kafka, or is willing to, and wants a
  vendor-supported, database-agnostic connector layer such as Debezium
  rather than a hand-rolled tailer.
- The volume of changes is high enough that a poller's query load against
  the live database, or its polling-interval latency, is a real operational
  problem.

### When not to reach for it

- The database in use does not expose a stable, documented logical change
  stream. Not every managed database offering exposes logical replication or
  binlog access to a tenant; some managed relational database tiers disable
  it, and some NoSQL stores have no log at all that a downstream consumer
  can subscribe to. Verify the specific database and hosting tier supports
  it before committing to this pattern.
- The change volume and consumer count are both low, and a simple Polling
  Publisher against an outbox table, at a one or two second interval,
  already meets every latency requirement. Log tailing is meaningfully more
  operationally complex than a poller and that complexity should be earned,
  not assumed by default.
- The team has no capacity to operate the tailing infrastructure, whether
  that is a managed CDC product, Debezium plus Kafka Connect plus Kafka, or
  a hand-rolled reader of a proprietary log format. Log tailing that nobody
  is monitoring silently falls behind, and a stalled replication slot can
  fill the source database's disk until the database itself refuses writes,
  which is a far worse failure mode than a slow poller.
- The consumer needs data that requires interpretation the raw row-level
  log cannot provide on its own, for example an aggregate business event
  such as "order was cancelled by the customer" versus "order was cancelled
  because payment failed," when both cases produce the identical row-level
  update. A row-level change stream tells you a status column changed value,
  not why. Where the why matters, pair log tailing with, or replace it with,
  Domain Event or an outbox row that carries the already-interpreted
  business event explicitly.
- The source is not a relational or log-structured store at all, for
  instance a legacy system whose only interface is a nightly file export.
  There is no log to tail. Other integration patterns apply instead.
- Data that must never leave the source database for compliance reasons,
  where mirroring it through a log-tailing pipeline into a broker and then
  into arbitrary downstream consumers would itself be the violation, is a
  case where the pattern is applicable mechanically but wrong for the
  organization, and that decision belongs to data governance, not to the
  integration architecture.

## 5. Structure

- **Source database.** Owns the authoritative data and writes a durable,
  ordered transaction log as an intrinsic part of committing every write.
  The source is unaware that anything downstream is tailing its log, in
  the same way it is unaware of how many physical replicas are attached.
- **Transaction log (WAL, binlog, oplog, redo log, change stream).** The
  database-native, append-only, ordered record of every committed change.
  Each entry carries or can be correlated to a monotonically increasing
  position, called a log sequence number in PostgreSQL, a binlog file plus
  offset in MySQL, and a resume token in MongoDB's change stream API.
- **Log reader (tailer, CDC connector, agent).** A process, separate from
  the source application, that authenticates to the database using its
  native replication protocol, requests changes starting from a specific
  saved position, and receives a continuous stream of change events. In
  PostgreSQL this role is filled by a logical replication slot consumer
  using an output plugin such as pgoutput, wal2json, or the Debezium
  decoderbufs plugin. In MySQL it is filled by a process that registers
  itself with the source as if it were a replica and reads the binlog
  replication protocol.
- **Position store (offset store, checkpoint store).** A durable location,
  external to the source's transaction log itself, where the reader
  persists the last position it has successfully processed, so that after
  a crash or restart it resumes exactly where it left off instead of
  replaying from the beginning or silently skipping ahead.
- **Change event.** The reader's normalized representation of a single row
  change, minimally the table, the operation, insert, update, or delete,
  the before image where available, the after image, and the source
  position. Debezium's convention names this an envelope with `before`,
  `after`, `op`, and `source` fields.
- **Publisher.** The component that takes each normalized change event and
  writes it to the downstream transport, most commonly a Kafka topic keyed
  by the row's primary key so that all changes to one row remain ordered
  relative to each other.
- **Downstream consumers.** One or more independent services subscribing
  to the published change stream, each free to interpret and project the
  changes however its own bounded context requires, entirely decoupled
  from the source service's internal schema beyond the shape of the
  published event.

## 6. ASCII structure diagram

```
+-------------------------+
|     Service A           |
|  (owns the database,    |
|   does one write only)  |
+-----------+-------------+
            |  INSERT / UPDATE / DELETE
            v
+-------------------------+
|   Source Database       |
|  +---------------------+|
|  | Table(s)            ||
|  +---------------------+|
|  +---------------------+|
|  | Transaction Log     ||   <-- append-only, database-native
|  | (WAL / binlog /     ||       ordered, durable
|  |  oplog / redo log)  ||
|  +---------------------+|
+-----------+-------------+
            |  native replication protocol
            v
+-------------------------+       +----------------------+
|   Log Reader / Tailer   |------>|  Position Store       |
|  (Debezium connector,   |<------|  (offsets, LSN,       |
|   DBLog, custom agent)  |       |   binlog coordinates) |
+-----------+-------------+       +----------------------+
            |  normalized change events
            v
+-------------------------+
|   Message Broker         |
|  (Kafka topic, keyed by  |
|   row primary key)       |
+-----------+-------------+
            |
    +-------+--------+--------------+
    v                v              v
+--------+     +-----------+   +-----------+
|Search  |     |Cache /    |   |Data       |
|Index   |     |Materialized|  |Warehouse  |
|Service |     |View       |   |Feed       |
+--------+     +-----------+   +-----------+
```

## 7. Dynamics

```
Service A          Source DB (log)     Log Reader        Broker         Consumer
   |                     |                  |               |               |
   |--BEGIN TXN--------->|                  |               |               |
   |--UPDATE order row--->|                  |               |               |
   |--COMMIT------------>|                  |               |               |
   |                     |--append log------>|               |               |
   |                     |   entry LSN=142  |               |               |
   |                     |                  |--poll/stream-->|               |
   |                     |                  |  from LSN=141 |               |
   |                     |<-----------------|               |               |
   |                     |--send entry LSN=142-------------->|               |
   |                     |                  |                |               |
   |                     |                  |--normalize     |               |
   |                     |                  |  to change event               |
   |                     |                  |--publish(topic=orders,--------->|
   |                     |                  |  key=order_id, value=event)     |
   |                     |                  |                |               |
   |                     |                  |--persist       |               |
   |                     |                  |  position=142  |               |
   |                     |                  |  (position store)               |
   |                     |                  |                |--consume------>|
   |                     |                  |                |  event LSN=142 |
   |                     |                  |                |               |--project into
   |                     |                  |                |               |  local read model
```

Two properties are visible in this sequence that matter more than the
individual arrows. First, the log reader persists its position only after
the broker has durably accepted the event, never before, so that a crash
between publishing and persisting causes the reader to redeliver the same
event on restart rather than silently skip it. This makes the reader
at-least-once by construction, and downstream consumption must be built to
tolerate a redelivered event, usually by making the projection logic
idempotent on the row's primary key and the event's position. Second, the
service's own commit is the only synchronization point in the whole flow.
Nothing downstream of the log write requires the service to wait, block, or
even know that a downstream system exists.

## 8. Implementation variants

**Hand-rolled reader against a native replication API.** A team writes its
own consumer of PostgreSQL logical replication, using a library such as
pgjdbc's replication API or a language-native client that speaks the
streaming replication protocol, or writes its own consumer of the MySQL
binlog replication protocol using a client library that implements the
`COM_BINLOG_DUMP` command. This gives full control over event shaping and
avoids running Kafka Connect, at the cost of the team owning correctness of
position tracking, schema change handling, and reconnection logic
themselves.

**Debezium on Kafka Connect.** The dominant production-grade variant. Each
Debezium connector is deployed into a Kafka Connect worker, targets one
source database, and writes normalized change events into one Kafka topic
per table. Kafka Connect itself owns offset storage, in an internal Kafka
topic by default, worker restart and rebalancing, and connector lifecycle,
so the team is largely relieved of position-tracking correctness. Debezium
ships source connectors for PostgreSQL, MySQL, MongoDB, SQL Server, Oracle,
and Db2, each wrapping that database's native log-reading mechanism behind
a common event envelope ([Debezium project README](https://raw.githubusercontent.com/debezium/debezium/main/README.md),
verified 2026-08-03).

**Snapshot-plus-tail with online chunking.** A tailer that starts on an
already-populated database faces a bootstrap problem, the log alone has no
record of rows that existed before the tailer started. Netflix's DBLog
solves this by interleaving a chunked table snapshot with continuous log
tailing rather than choosing one or the other, using a watermark technique.
The reader inserts a unique low-watermark marker into the log by writing to
a dedicated watermark table, selects the next chunk of rows to snapshot,
inserts a high-watermark marker, and then, as real log events for that
chunk's key range arrive between the two watermarks, discards the
now-stale snapshot rows in favor of the fresher log-derived values. Rows
that were unaffected by concurrent writes are sent as snapshot output once
the high watermark is observed in the log stream. This lets a full initial
snapshot run concurrently with live log tailing, with no table lock,
because the watermarks act as ordering fences rather than exclusion locks
([Netflix Technology Blog, DBLog](https://netflixtechblog.com/dblog-a-generic-change-data-capture-framework-69351fb9099b),
verified 2026-08-03). Debezium's own incremental snapshot feature, added in
later releases, implements a closely related watermark-chunking approach.

**Managed cloud CDC services.** AWS Database Migration Service, Google
Cloud Datastream, and similar managed offerings wrap the same log-tailing
mechanics behind a hosted service so a team need not operate Kafka Connect
or a hand-rolled reader at all, trading operational ownership for vendor
lock-in and, usually, per-gigabyte pricing on the change stream.

**Native stream primitives on non-relational stores.** Some non-relational
databases expose a change feed as a first-class API rather than a raw
replication protocol a third party reverse-engineers. Amazon DynamoDB
Streams captures a time-ordered, per-item sequence of modifications,
retained for twenty-four hours, and organizes them into shards that an
application consumes directly through a documented API, most commonly via
the AWS Lambda event source mapping or the DynamoDB Streams Kinesis Adapter
([AWS Documentation, Change data capture for DynamoDB Streams](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html),
verified 2026-08-03). MongoDB's replica set oplog is the underlying
append-only capped collection that both intra-cluster replication and
MongoDB's higher-level change streams API read from
([MongoDB Manual, Replica Set Oplog](https://www.mongodb.com/docs/manual/core/replica-set-oplog/),
verified 2026-08-03).

## 9. Known production uses

1. **LinkedIn, Databus.** LinkedIn built Databus as a source-agnostic,
   low-latency change data capture system that tailed Oracle redo logs and
   MySQL binlogs to keep search indexes, graph indexes, caches, and other
   derived data stores in sync with the primary databases behind LinkedIn's
   member and company profile data, at the scale of hundreds of millions of
   users, and later contributed the project as open source
   (LinkedIn Engineering Blog, coverage of Databus's design as a
   source-agnostic change capture pipeline built on transaction log
   tailing).
2. **Netflix, DBLog.** Netflix built DBLog specifically to unify change
   data capture across MySQL and PostgreSQL for use cases including
   keeping Elasticsearch indexes synchronized with primary MySQL data,
   explicitly evaluating and rejecting existing tools including Maxwell
   and Debezium for stalling log processing during a full-table dump or
   requiring table locks that would block Netflix's write traffic, and
   built its watermark-based chunking algorithm to solve that problem
   ([Netflix Technology Blog, DBLog](https://netflixtechblog.com/dblog-a-generic-change-data-capture-framework-69351fb9099b),
   verified 2026-08-03).
3. **Red Hat, Debezium, as embedded by its adopters.** Debezium itself is
   built and maintained by Red Hat as a Kafka Connect based, log-tailing
   CDC platform, and its connector suite for PostgreSQL, MySQL, MongoDB,
   SQL Server, Oracle, and Db2 is the mechanism most commonly cited in
   practitioner write-ups of the Transactional Outbox pattern's message
   relay step for implementing exactly the transaction log tailing half of
   that pattern in production Kafka-based architectures
   ([Debezium project README](https://raw.githubusercontent.com/debezium/debezium/main/README.md),
   verified 2026-08-03; [microservices.io, Transaction Log Tailing](https://microservices.io/patterns/data/transaction-log-tailing.html),
   verified 2026-08-03).
4. **AWS, DynamoDB Streams as a first-class managed log-tailing primitive.**
   Amazon offers transaction log tailing as a documented, supported API
   surface rather than an unsupported internal mechanism, specifically so
   that customers can build change-driven downstream processing, commonly
   through AWS Lambda triggers, without operating a separate CDC connector
   ([AWS Documentation, DynamoDB Streams](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html),
   verified 2026-08-03).

## 10. Consequences

### Positive

- Eliminates the dual write problem for the common case of "write to my
  database, then reliably notify the rest of the system," without
  requiring a distributed transaction coordinator, because the pattern
  relies on atomicity the database already provides between a committed
  row and its log entry.
- Delivers changes with latency measured in milliseconds after commit in
  the common case, rather than the polling-interval latency of a Polling
  Publisher.
- Captures a complete, ordered feed of every committed change with no code
  path that can forget to emit an event, because the log itself cannot be
  bypassed by any write path that goes through the database's normal
  commit protocol.
- Imposes essentially zero incremental burden on the writing service's own
  code, latency, or transaction; the service does exactly the write it was
  always going to do.
- Decouples the number and identity of downstream consumers from the
  source service entirely; adding a new consumer of the change feed
  requires no change to the source service at all.

### Negative

- Introduces a new class of infrastructure, the log reader itself, that
  must be operated, monitored, and kept from falling behind, and that
  requires access to a low-level database mechanism normally reserved for
  replication administrators.
- Exposes the source database's physical row schema, or something close to
  it, to every downstream consumer, which creates an implicit schema
  coupling that a well-designed API or an explicitly modeled Domain Event
  would otherwise avoid; a column rename in the source table becomes a
  breaking change for every consumer of the tailed stream.
- A replication slot or binlog position that a stalled or crashed reader
  fails to advance can prevent the source database from freeing log
  storage, which, left unmonitored, can grow disk usage until the source
  database itself is affected, turning a downstream integration failure
  into a source-side outage.
- The pattern is at-least-once by construction; downstream consumers must
  be built to tolerate and correctly handle redelivery of the same change,
  which is an additional design obligation the naive dual-write approach
  does not impose, even though the dual-write approach is worse overall.
- The pattern is harder to build and test correctly than it first appears,
  so much so that Richardson's own catalog entry describes it as
  "relatively obscure" as an implementation technique, and practitioners
  are steered toward an existing tool such as Debezium rather than a
  hand-rolled reader for anything beyond a learning exercise
  ([microservices.io, Transaction Log Tailing](https://microservices.io/patterns/data/transaction-log-tailing.html),
  verified 2026-08-03).

## 11. Failure modes and misuse

**Symptom.** Source database disk usage climbs steadily and the database
administrator eventually gets a low-disk-space alert or the database
refuses further writes.
**Cause.** The log reader has stopped advancing its consumed position,
often because the downstream broker became unreachable, the reader process
crashed and was never restarted, or a schema change on the source broke
the reader's parsing and it is stuck retrying. A PostgreSQL logical
replication slot, or a MySQL binlog a reader has registered interest in but
stopped consuming, prevents the database from purging that portion of the
log, because the database must assume the slow consumer will eventually
come back and needs those log segments.
**Fix.** Alert on replication slot lag or binlog retention age as a
first-class database health metric, not merely as an application concern,
and configure a maximum retention or a slot-drop policy so that a
permanently abandoned reader cannot take the source database down with it.

**Symptom.** A downstream consumer applies the same change twice and its
local read model ends up with duplicated line items, doubled counters, or
an incorrect aggregate value.
**Cause.** The pattern delivers at-least-once, and the consumer's
projection logic was written as if it would receive each event exactly
once, most commonly because the position store and the downstream apply
step are not the same transaction, or because a naive counter increment was
used instead of an idempotent upsert keyed by the event's unique position.
**Fix.** Make every downstream projection idempotent, usually by storing
the last-applied log position per consumer alongside its projected data and
rejecting or no-oping any incoming event whose position is not strictly
greater than the last one applied for that key.

**Symptom.** A downstream consumer's read model silently diverges from the
source over weeks, with no error ever logged, and nobody notices until a
customer reports stale data.
**Cause.** The reader is genuinely running and genuinely publishing, but it
has fallen behind, sometimes because the source's write volume spiked and
the reader's throughput did not keep pace, sometimes because the reader
silently reconnected from an older saved position after a crash and is now
replaying, sometimes because the broker's retention window expired for a
topic partition the consumer had not yet caught up on.
**Fix.** Expose source-to-consumer lag, source commit time versus the age of the
oldest unprocessed event at the consumer, as a monitored metric with
alerting thresholds, not merely "is the connector task in RUNNING state,"
because a connector can report itself healthy while badly behind.

**Symptom.** The reader's normalized change events start being rejected by
consumers, or consumers crash on deserialization, immediately after a
routine schema migration on the source table.
**Cause.** A column was added, renamed, dropped, or had its type changed on
the source table, and the reader's schema history, or the consumer's
expected event shape, does not account for the change, either because
schema evolution support was not configured or because the migration was
not coordinated with the CDC pipeline's schema registry.
**Fix.** Use a schema registry with an explicit compatibility mode for the
downstream event schema, treat a source schema migration as an event that
requires coordinated rollout across the tailer and every consumer, and
never drop or reuse a column name in a way that could be misread by a
consumer still on an older schema version.

**Symptom.** A downstream consumer processes events out of order relative
to each other for the same entity, applying an older update after a newer
one, and the projected state ends up reflecting a stale value.
**Cause.** Events for the same row were published to different broker
partitions, most commonly because the publisher was not configured to
partition by the row's primary key, so Kafka's per-partition ordering
guarantee no longer implies per-row ordering.
**Fix.** Always partition the downstream topic by the source row's primary
key (or the natural aggregate key), never by an arbitrary or round-robin
strategy, so that every change to a given row lands in the same partition
in commit order.

## 12. Trade-off matrix

| Force | Transaction Log Tailing | Polling Publisher | Trigger-based CDC | Dual write (no pattern) |
|---|---|---|---|---|
| Latency | Low, usually milliseconds after commit | Bounded by poll interval, seconds to minutes | Low, synchronous with the write | Low, but unreliable |
| Consistency guarantee | Reliable, at-least-once, backed by database log durability | Reliable, at-least-once, backed by outbox table durability | Reliable if the trigger and write share a transaction | Not reliable, dual write problem |
| Load on source database | Low, comparable to one more logical replication subscriber | Moderate, one query per poll interval regardless of change volume | Adds per-write overhead inside the source transaction itself | Adds a second network call inside or after the source transaction |
| Operational complexity | High, a new class of infrastructure to run and monitor | Low, a scheduled job and a table | Moderate, triggers are simple but their maintenance and portability are poor | Low to build, high in incident cost |
| Schema coupling exposed downstream | High, tends to expose raw row shape unless explicitly filtered | Low, an outbox table can carry an explicitly modeled event payload | Low, a trigger can write an explicitly modeled event row | N/A |
| Portability across database engines | Low, each engine's log format and access mechanism differs | High, works identically against any SQL database | Low to moderate, trigger syntax and semantics vary by engine | High |
| Requires distributed transaction coordinator | No | No | No | Effectively yes, or accept inconsistency |
| Ordering guarantee | Total commit order at the source, per-key order downstream if partitioned correctly | Order determined by the poller's own query, usually by an outbox sequence column | Order determined by trigger firing order, generally commit order | No cross-system ordering guarantee at all |

## 13. Related and incompatible patterns

**Transactional Outbox.** Transaction Log Tailing is one of the two
documented implementation strategies for the message relay half of the
Transactional Outbox pattern, the other being Polling Publisher. The two
patterns compose directly. The service writes both its business row and an
outbox row in one local transaction, per Transactional Outbox, and the
tailer, per this pattern, reads the outbox table's insertions from the
transaction log rather than polling the outbox table on an interval
([microservices.io, Transaction Log Tailing](https://microservices.io/patterns/data/transaction-log-tailing.html),
verified 2026-08-03). Log tailing can also be pointed directly at business
tables rather than at a dedicated outbox table, which removes the need to
maintain an outbox schema at all, at the cost of exposing the raw business
schema to downstream consumers rather than an explicitly modeled event.

**Saga.** A saga's steps are frequently triggered by events, and a tailed
change stream is a natural transport for those triggering events when the
saga participants are otherwise decoupled services with their own private
databases, giving the saga orchestrator or the next participant a reliable
signal that a prior step committed.

**CQRS and Event Sourcing.** Log tailing is a common mechanism for
populating a CQRS read model from a write-side database that was not
purpose-built for event sourcing, effectively deriving a change stream from
an ordinary relational schema after the fact rather than requiring the
write side to be redesigned as an event store from the start.

**Domain Event.** A raw tailed row change and a well-modeled domain event
are not the same thing, and this is the pattern's sharpest limitation. A
row-level update tells a consumer that a column's value changed, not why,
in business terms, it changed. Where consumers genuinely need the business
meaning, pair log tailing of an outbox table, whose rows are explicitly
constructed domain events, rather than tailing business tables directly and
asking every consumer to reverse-engineer intent from row diffs.

**Database per Service.** This pattern exists specifically to preserve
Database per Service's isolation guarantee while still letting other parts
of the system react to changes; it is the integration mechanism that makes
strict data ownership tolerable rather than isolating.

**Strangler Application.** During an incremental migration away from a
monolith, log tailing lets new services observe a legacy database's writes
without any change to the legacy application's code, which is frequently
the only realistic integration point when the legacy codebase cannot be
safely modified.

**Incompatible with Shared Database.** If services already share one
database directly, there is no isolation boundary for a tailed change
stream to preserve, and the reason to reach for this pattern, decoupling
services that do not share data access, does not apply. A team migrating
off Shared Database toward Database per Service is a common moment to
introduce Transaction Log Tailing as the replacement integration mechanism.

## 14. Refactoring path in and out

### Introducing the pattern

1. Confirm the source database and its hosting tier actually expose a
   logical, row-level change stream a third-party consumer can subscribe
   to, not merely physical replication, and confirm the operations team can
   grant the necessary replication privileges.
2. Decide whether the tailer will read business tables directly or an
   Outbox table. If the downstream consumers need explicitly modeled
   business events rather than raw row diffs, introduce Transactional
   Outbox first, so the source of truth for "what happened" is a row the
   application deliberately wrote, not an inferred diff.
3. Stand up the log reader against a non-production replica of the source
   database first, verifying it can complete an initial snapshot and then
   transition cleanly into live tailing without missing or duplicating
   changes across that boundary.
4. Introduce a schema registry and an explicit compatibility policy for the
   published event schema before the first downstream consumer is built
   against it, so a future column rename or type change on the source is a
   coordinated, versioned event rather than a silent breaking change.
5. Build the first downstream consumer to be explicitly idempotent on the
   event's source position and the row's primary key from day one, rather
   than adding idempotency after the first observed duplicate-processing
   incident.
6. Wire replication lag and slot or binlog retention monitoring into the
   database's own alerting before going live, not after, because the
   failure mode of an abandoned reader threatening the source database's
   disk is silent until it is a source-side incident.
7. Cut the write path over incrementally, first running the tailer
   alongside any existing dual-write or polling mechanism in shadow mode,
   comparing outputs, before removing the older mechanism.

### Removing the pattern

1. Confirm which downstream consumers still depend on the tailed stream and
   whether any of them can be migrated to call an explicit API instead,
   which is frequently the right long-term direction once the number of
   consumers of a raw change feed grows large enough that the implicit
   schema coupling becomes the dominant maintenance cost.
2. If the volume and consumer count have shrunk to the point that a
   Polling Publisher's latency is now acceptable and its operational
   simplicity is now the more valuable trade, migrate the relay mechanism
   from log tailing to polling while keeping the Outbox table itself, which
   requires no change to the downstream consumers at all if they were
   already consuming from the same broker topic shape.
3. Decommission the log reader's replication slot or binlog registration
   explicitly and verify the source database frees the log storage it
   was holding on the reader's behalf, rather than leaving an orphaned
   slot silently pinning log segments indefinitely.

## 15. Testing and verification

Testing a log-tailing pipeline is testing three separate concerns, and
conflating them is the most common reason teams under-test this pattern.

**Source-to-log fidelity.** Verify that every write shape the application
can produce, insert, update including partial-column updates, delete, and,
for engines where it matters, DDL, produces a change event with the
expected before and after images. This is best tested against a real
instance of the actual database engine, using a container, rather than
mocked, because the exact row image content depends on engine-specific
configuration such as PostgreSQL's `REPLICA IDENTITY` setting or MySQL's
binlog row image mode, and a mock cannot faithfully reproduce that
configuration-dependent behavior.

**Reader resilience.** Verify the reader resumes correctly from a
persisted position after a simulated crash mid-stream, verify it does not
lose events across the snapshot-to-tail handoff for a database that already
has existing rows, and verify it degrades safely, rather than crash-looping
or silently dropping events, when the broker is briefly unavailable.
Netflix's public description of DBLog's watermark technique is itself
effectively a testing strategy as much as an implementation strategy,
because the low-watermark and high-watermark markers give the reader an
observable, verifiable ordering fence to assert against in tests
([Netflix Technology Blog, DBLog](https://netflixtechblog.com/dblog-a-generic-change-data-capture-framework-69351fb9099b),
verified 2026-08-03).

**Consumer idempotency.** Verify every downstream consumer produces the
identical final state whether a given event is delivered once or is
redelivered multiple times, and whether events for the same key arrive in
order or, as a defensive test, slightly out of order, since ordering can
only be guaranteed within a single partition and a misconfigured publisher
is one of the documented failure modes above.

Contract tests between the tailer's published event schema and each
consumer are the practical technique that scales across many consumers,
verified against a schema registry's compatibility check rather than
against every individual consumer's code, so that a source schema change is
caught at CI time rather than discovered in production by a crashing
consumer.

## 16. Observability signals

- **Replication lag**, measured as the difference between the source
  database's current log position and the position the reader has
  successfully consumed and acknowledged, exposed both in log units, such
  as bytes of WAL behind, and in wall-clock time behind, since a fixed
  byte-lag threshold means something different depending on write volume.
- **Source-to-consumer event age**, measured as the age of the oldest unprocessed
  event sitting in the broker for the slowest downstream consumer group,
  which is the metric that actually reflects what a stale read model looks
  like to a user, as distinct from reader-to-broker lag alone.
- **Replication slot or binlog retention size**, the amount of transaction
  log the source database is holding because a reader has not yet
  consumed past it, alerted on an absolute threshold tied to available
  source disk, because this metric threatening zero is the failure mode
  that can take down the source database itself.
- **Reader connector task state**, whether the tailer's task is reported as
  running, paused, or failed, which is a necessary but insufficient signal,
  as noted in the failure modes above, and should always be paired with the
  lag metrics rather than trusted alone.
- **Schema change events**, a distinct metric or log line every time the
  reader detects a DDL change on a tailed table, so that schema evolution
  is visible operationally, not only discovered when a consumer breaks.
- **Duplicate and out-of-order event rate**, tracked at the consumer, as a
  direct signal of whether the idempotency and partitioning design is
  behaving as intended in production, not merely in tests.

## 17. Security and privacy implications

Granting a process replication access to a source database is a
notable privilege, comparable in practice to granting read access to
every row of every tailed table, including columns a service's normal API
would never expose, because the transaction log by construction contains
the full before and after row images of every write. A log-tailing pipeline
therefore requires the same data classification review as any other bulk
data export. Personally identifiable information, financial data, or
regulated health data present in a source table flows automatically into
the tailed event stream and from there into every downstream consumer's
broker subscription, unless the pipeline explicitly filters or masks
sensitive columns before publishing, which is a step teams frequently omit
because the pipeline is built at the infrastructure layer, distant from the
application-layer conversations about which fields are sensitive. Encrypt
the transport between the reader and the source database using the
database's native TLS support for its replication protocol, encrypt the
broker's storage and transport, and apply topic-level or field-level
access controls on the published stream so that a consumer built for one
purpose cannot silently read columns intended for a different purpose. Where
regulatory deletion requirements apply, for example a right-to-erasure
request, a tailed event stream that has already fanned out a now-deleted
row's prior values to multiple downstream consumers and possibly into a
data warehouse creates a data-lineage problem that must be designed for
explicitly, usually by publishing a tombstone or deletion event that every
consumer is contractually required to honor, rather than assuming deletion
at the source is sufficient.

## 18. References

1. Chris Richardson, "Pattern. Transaction log tailing," microservices.io
   pattern catalog. https://microservices.io/patterns/data/transaction-log-tailing.html
   (verified 2026-08-03).
2. Chris Richardson, "Pattern. Transactional outbox," microservices.io
   pattern catalog. https://microservices.io/patterns/data/transactional-outbox.html
   (verified 2026-08-03).
3. Chris Richardson, *Microservices Patterns. With Examples in Java*,
   Manning Publications, 2018, chapter 3, "Interprocess communication in a
   microservice architecture," section on reliable messaging and change
   data capture.
4. Martin Kleppmann, *Designing Data-Intensive Applications*, O'Reilly
   Media, 2017, chapter 11, "Stream Processing," section "Change Data
   Capture."
5. PostgreSQL Global Development Group, "Chapter 47, `Logical Decoding`,"
   PostgreSQL Documentation. https://www.postgresql.org/docs/current/logicaldecoding.html
   (verified 2026-08-03).
6. Oracle Corporation, "5.4.4 The Binary Log," MySQL 8.4 Reference Manual.
   https://dev.mysql.com/doc/refman/8.4/en/binary-log.html (verified
   2026-08-03).
7. Debezium project, README, github.com/debezium/debezium.
   https://raw.githubusercontent.com/debezium/debezium/main/README.md
   (verified 2026-08-03).
8. Andreas Andreakis and Ioannis Papapanagiotou, "DBLog. A Generic
   Change-Data-Capture Framework," Netflix Technology Blog.
   https://netflixtechblog.com/dblog-a-generic-change-data-capture-framework-69351fb9099b
   (verified 2026-08-03).
9. Amazon Web Services, "Change data capture for DynamoDB Streams,"
   Amazon DynamoDB Developer Guide.
   https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html
   (verified 2026-08-03).
10. MongoDB, Inc., "Replica Set Oplog," MongoDB Manual.
    https://www.mongodb.com/docs/manual/core/replica-set-oplog/ (verified
    2026-08-03).
11. LinkedIn Engineering, coverage of Databus as LinkedIn's source-agnostic,
    low-latency change data capture system, engineering.linkedin.com data
    replication engineering blog series (Databus design overview).

## Code examples

The three implementations below model the same shape. a normalized change
event, a durably persisted consumer position, and an idempotent apply step,
which are the three concerns identified in dimension 15 as needing separate
tests. None of them talks to a real database's replication socket, because
that requires a live server and a specific engine's wire protocol; instead
each one models the log as an append-only sequence the reader tails, which
is the same shape a real binlog or WAL reader consumes, so the position
tracking and idempotency logic is the genuine article even though the
transport is simulated.

### Python

```python
"""Minimal transaction log tailer. Models the log as an append-only
sequence of committed change events and demonstrates position tracking
and idempotent downstream apply."""

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ChangeEvent:
    position: int
    table: str
    op: str  # "insert", "update", "delete"
    key: str
    after: dict | None


class TransactionLog:
    """Stands in for a database's WAL or binlog. Real tailers speak a
    replication protocol instead of iterating a Python list."""

    def __init__(self) -> None:
        self._entries: list[ChangeEvent] = []

    def append(self, table: str, op: str, key: str, after: dict | None) -> None:
        position = len(self._entries) + 1
        self._entries.append(ChangeEvent(position, table, op, key, after))

    def read_from(self, position: int) -> list[ChangeEvent]:
        return [e for e in self._entries if e.position > position]


class PositionStore:
    """Durable position tracking. A real tailer persists this to disk
    or to Kafka Connect's offsets topic, never only in memory."""

    def __init__(self) -> None:
        self._position = 0

    def load(self) -> int:
        return self._position

    def save(self, position: int) -> None:
        self._position = position


class Tailer:
    def __init__(self, log: TransactionLog, positions: PositionStore) -> None:
        self._log = log
        self._positions = positions

    def poll_and_publish(self, publish: Callable[[ChangeEvent], None]) -> int:
        """Read new entries, publish each one, and persist the position
        only after the publish call succeeds, so a crash mid-batch
        redelivers rather than silently drops."""
        last_position = self._positions.load()
        published = 0
        for event in self._log.read_from(last_position):
            publish(event)
            self._positions.save(event.position)
            published += 1
        return published


class IdempotentProjection:
    """A downstream consumer that tolerates at-least-once delivery by
    rejecting any event whose position is not newer than the last one
    it applied for that key."""

    def __init__(self) -> None:
        self._last_position_by_key: dict[str, int] = {}
        self.state: dict[str, dict] = {}

    def apply(self, event: ChangeEvent) -> bool:
        last = self._last_position_by_key.get(event.key, 0)
        if event.position <= last:
            return False  # duplicate or stale, correctly ignored
        if event.op == "delete":
            self.state.pop(event.key, None)
        else:
            self.state[event.key] = event.after or {}
        self._last_position_by_key[event.key] = event.position
        return True


def _demo() -> None:
    log = TransactionLog()
    log.append("orders", "insert", "order-1", {"status": "created"})
    log.append("orders", "update", "order-1", {"status": "paid"})

    positions = PositionStore()
    tailer = Tailer(log, positions)
    projection = IdempotentProjection()

    published_events: list[ChangeEvent] = []
    n = tailer.poll_and_publish(lambda e: published_events.append(e))
    assert n == 2

    for event in published_events:
        applied = projection.apply(event)
        assert applied

    # Redeliver the same batch. Idempotency must hold.
    for event in published_events:
        applied = projection.apply(event)
        assert not applied

    assert projection.state["order-1"]["status"] == "paid"
    assert positions.load() == 2
    print("ok: two events tailed, projection converged, redelivery ignored")


if __name__ == "__main__":
    _demo()
```

### Go

```go
package main

import "fmt"

// ChangeEvent mirrors the normalized shape a real CDC connector emits.
type ChangeEvent struct {
	Position int
	Table    string
	Op       string
	Key      string
	After    map[string]string
}

// TransactionLog stands in for a database's WAL or binlog.
type TransactionLog struct {
	entries []ChangeEvent
}

func (l *TransactionLog) Append(table, op, key string, after map[string]string) {
	pos := len(l.entries) + 1
	l.entries = append(l.entries, ChangeEvent{pos, table, op, key, after})
}

func (l *TransactionLog) ReadFrom(position int) []ChangeEvent {
	var out []ChangeEvent
	for _, e := range l.entries {
		if e.Position > position {
			out = append(out, e)
		}
	}
	return out
}

// PositionStore is durable position tracking. In production this is a
// file, a database row, or Kafka Connect's internal offsets topic.
type PositionStore struct {
	position int
}

func (p *PositionStore) Load() int    { return p.position }
func (p *PositionStore) Save(pos int) { p.position = pos }

// Tailer polls the log and publishes each new entry, persisting position
// only after a successful publish.
type Tailer struct {
	log       *TransactionLog
	positions *PositionStore
}

func (t *Tailer) PollAndPublish(publish func(ChangeEvent)) int {
	last := t.positions.Load()
	published := 0
	for _, e := range t.log.ReadFrom(last) {
		publish(e)
		t.positions.Save(e.Position)
		published++
	}
	return published
}

// IdempotentProjection tolerates at-least-once delivery.
type IdempotentProjection struct {
	lastPositionByKey map[string]int
	state             map[string]map[string]string
}

func NewIdempotentProjection() *IdempotentProjection {
	return &IdempotentProjection{
		lastPositionByKey: map[string]int{},
		state:             map[string]map[string]string{},
	}
}

func (p *IdempotentProjection) Apply(e ChangeEvent) bool {
	last := p.lastPositionByKey[e.Key]
	if e.Position <= last {
		return false
	}
	if e.Op == "delete" {
		delete(p.state, e.Key)
	} else {
		p.state[e.Key] = e.After
	}
	p.lastPositionByKey[e.Key] = e.Position
	return true
}

func main() {
	log := &TransactionLog{}
	log.Append("orders", "insert", "order-1", map[string]string{"status": "created"})
	log.Append("orders", "update", "order-1", map[string]string{"status": "paid"})

	positions := &PositionStore{}
	tailer := &Tailer{log: log, positions: positions}
	projection := NewIdempotentProjection()

	var published []ChangeEvent
	n := tailer.PollAndPublish(func(e ChangeEvent) {
		published = append(published, e)
	})
	if n != 2 {
		panic("expected 2 events tailed")
	}

	for _, e := range published {
		if !projection.Apply(e) {
			panic("first application must succeed")
		}
	}
	// Redeliver. Must be ignored.
	for _, e := range published {
		if projection.Apply(e) {
			panic("redelivery must be idempotent")
		}
	}

	if projection.state["order-1"]["status"] != "paid" {
		panic("projection did not converge to latest state")
	}
	if positions.Load() != 2 {
		panic("position store did not advance to last event")
	}
	fmt.Println("ok: two events tailed, projection converged, redelivery ignored")
}
```

### TypeScript

```typescript
// Minimal transaction log tailer, run with: npx ts-node tail.ts
// or compiled with: npx tsc --strict tail.ts && node tail.js

interface ChangeEvent {
  position: number;
  table: string;
  op: "insert" | "update" | "delete";
  key: string;
  after: Record<string, string> | null;
}

/** Stands in for a database's WAL or binlog. A real tailer speaks a
 * replication protocol instead of appending to an array in memory. */
class TransactionLog {
  private entries: ChangeEvent[] = [];

  append(
    table: string,
    op: ChangeEvent["op"],
    key: string,
    after: Record<string, string> | null
  ): void {
    const position = this.entries.length + 1;
    this.entries.push({ position, table, op, key, after });
  }

  readFrom(position: number): ChangeEvent[] {
    return this.entries.filter((e) => e.position > position);
  }
}

/** Durable position tracking. Persisted to disk, a database row, or
 * Kafka Connect's offsets topic in a real deployment. */
class PositionStore {
  private position = 0;

  load(): number {
    return this.position;
  }

  save(position: number): void {
    this.position = position;
  }
}

class Tailer {
  constructor(private log: TransactionLog, private positions: PositionStore) {}

  /** Persists position only after a successful publish, so a crash
   * mid-batch redelivers rather than silently drops. */
  pollAndPublish(publish: (event: ChangeEvent) => void): number {
    const last = this.positions.load();
    let published = 0;
    for (const event of this.log.readFrom(last)) {
      publish(event);
      this.positions.save(event.position);
      published += 1;
    }
    return published;
  }
}

/** Tolerates at-least-once delivery by rejecting any event whose
 * position is not newer than the last one applied for that key. */
class IdempotentProjection {
  private lastPositionByKey = new Map<string, number>();
  state = new Map<string, Record<string, string>>();

  apply(event: ChangeEvent): boolean {
    const last = this.lastPositionByKey.get(event.key) ?? 0;
    if (event.position <= last) {
      return false;
    }
    if (event.op === "delete") {
      this.state.delete(event.key);
    } else {
      this.state.set(event.key, event.after ?? {});
    }
    this.lastPositionByKey.set(event.key, event.position);
    return true;
  }
}

function demo(): void {
  const log = new TransactionLog();
  log.append("orders", "insert", "order-1", { status: "created" });
  log.append("orders", "update", "order-1", { status: "paid" });

  const positions = new PositionStore();
  const tailer = new Tailer(log, positions);
  const projection = new IdempotentProjection();

  const published: ChangeEvent[] = [];
  const n = tailer.pollAndPublish((e) => published.push(e));
  if (n !== 2) throw new Error("expected 2 events tailed");

  for (const event of published) {
    if (!projection.apply(event)) throw new Error("first apply must succeed");
  }
  // Redeliver the same batch. Idempotency must hold.
  for (const event of published) {
    if (projection.apply(event)) throw new Error("redelivery must be idempotent");
  }

  if (projection.state.get("order-1")?.status !== "paid") {
    throw new Error("projection did not converge to latest state");
  }
  if (positions.load() !== 2) {
    throw new Error("position store did not advance to last event");
  }
  console.log("ok: two events tailed, projection converged, redelivery ignored");
}

demo();
```

Java and Rust are omitted here in favor of thorough coverage of the three
languages above. Java is the natural home of the real-world tooling for
this pattern, Kafka Connect and Debezium are both JVM projects, but a
faithful Java example of driving Kafka Connect's connector framework
directly requires the Kafka Connect runtime as a dependency rather than
the small, dependency-free demonstration used for the other three
languages, so it was left out rather than shipped as a misleadingly
simplified stand-in. Rust was omitted for the same reason, there is no
small, representative, dependency-free way to demonstrate a wire-protocol
binlog or WAL reader that would be more informative than the shape already
shown in Go.
