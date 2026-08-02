---
name: Materialized View
slug: materialized-view
family: 08-cloud-distributed
category: Cloud and Distributed
aliases: [Precomputed View, Materialized Query Table, Denormalized Read Model]
first_described: "Blakeley, Larson, Tompa 1986 (incremental view maintenance algorithm); Microsoft patterns and practices, Cloud Design Patterns, 2014 (cloud architecture catalog name)"
maturity: canonical
related: [cache-aside, cqrs, event-sourcing, read-through-cache, write-through-cache]
incompatible_with: []
verified: 2026-08-02
---

# Materialized View

## 1. Name, aliases, and lineage

The canonical name is **Materialized View**. It names two related but distinct
things, and confusing them is the most common source of confusion when the
pattern is discussed.

The first is a relational database object, a query whose result set is
computed once and stored as data, rather than recomputed on every read the way
an ordinary view is. The foundational academic treatment of how to keep such a
stored result current as the underlying tables change is Jose A. Blakeley,
Per-Ake Larson, and Frank Wm. Tompa, "Efficiently Updating Materialized
Views", *ACM SIGMOD Record* 15, no. 2 (June 1986), pages 61 to 71
([ACM Digital Library, DOI 10.1145/16894.16861](https://dl.acm.org/doi/10.1145/16894.16861),
verified 2026-08-02). The paper introduces the idea of filtering out updates
that provably cannot affect the view, called irrelevant updates, and applying
a differential algorithm to re-evaluate only the affected part of the view
for the updates that remain. That differential idea is still the core of
every incremental refresh implementation in production today, thirty-nine
years later.

IBM's Db2 calls its implementation a **Materialized Query Table (MQT)**. The
vendor documentation states plainly, "materialized query tables are tables
whose definition is based on the result of a query", and adds the sentence
that draws the distinction that matters most for this dimension, "an MQT
actually stores the query results as data" so that a subsequent query against
the base tables can be automatically rewritten by the optimizer to read from
the MQT instead
([IBM Documentation, Materialized query tables](https://www.ibm.com/docs/en/db2/11.5.x?topic=tables-materialized-query),
verified 2026-08-02). PostgreSQL implements the same idea under the name
`MATERIALIZED VIEW` and states plainly that "the materialized view cannot
subsequently be directly updated and that the query used to create the
materialized view is stored in exactly the same way that a view's query is
stored, so that fresh data can be generated for the materialized view with"
an explicit `REFRESH MATERIALIZED VIEW` statement
([PostgreSQL Documentation, chapter 41.7](https://www.postgresql.org/docs/current/rules-materializedviews.html),
verified 2026-08-02). Oracle has shipped the feature since the 1990s under the
same SQL-standard name.

The second sense of the term, and the one this entry treats as primary, is
the cloud architecture pattern of the same name, generating a prepopulated,
query-shaped copy of data drawn from one or more source stores, of any kind,
not only a relational database with a native `MATERIALIZED VIEW` statement.
Microsoft's Azure Architecture Center catalogs it explicitly as one of its
cloud design patterns, describing it as generating views "in advance" in "a
format suited to the required results set" when "the data isn't ideally
formatted for required query operations"
([Microsoft Learn, Materialized View pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/materialized-view),
verified 2026-08-02). The Microsoft page adds a sentence that is the single
most important one in the whole pattern. "A key point is that a materialized
view and the data it contains is completely disposable because it can be
entirely rebuilt from the source data stores. A materialized view is never
updated directly by an application, and so it's a specialized cache." That
disposability, and the fact that the view is never the system of record, is
what separates the pattern from ordinary denormalization or replication.

In the CQRS and event sourcing literature the same construction is usually
called a **read model**. Microsoft's own CQRS pattern page uses "materialized
view" and "read model" interchangeably in the same paragraph, describing "a
durable, read-only cache that's optimized for fast and efficient queries"
([Microsoft Learn, CQRS pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs),
verified 2026-08-02). This entry treats Precomputed View, Denormalized Read
Model, and Materialized Query Table as the working aliases, because each
names a real, sourced usage of the same underlying construction rather than a
different mechanism.

## 2. Problem and context

An application reads data far more often than it writes it, and the shape a
write path needs is almost never the shape a read path wants. A normalized
relational schema is correct for enforcing integrity on write. It is
expensive to query, because answering "show me this customer's order total
for the current month, broken down by product category" against a normalized
schema means joining orders, order lines, products, and categories, then
aggregating, on every single request. An append-only event log is correct for
recording what happened, with a full audit trail and the ability to replay
history. It is close to useless for answering "what is this account's current
balance" without first replaying every event that ever touched the account.
A wide, denormalized document in a NoSQL store is correct for retrieving one
entity in a single read. It is a poor fit for "give me the total sales this
month across every customer", because that question spans many documents and
the store has no native aggregation across the collection at the speed a
dashboard needs.

The context in which the pattern belongs is precisely this mismatch, that the
storage format correct for writes, integrity, and history is the wrong format
for the specific, recurring read the application needs, and recomputing the
answer from the source shape on every request is either too slow, too
expensive in read capacity, or both. The pattern's context also includes
systems where the read is answerable in the source shape but only at a query
complexity or index cost the team is not willing to carry on the hot path,
and event-sourced systems, where a materialized view over the event stream is
frequently not an optimization but the only practical way to answer a query
at all, because there is no other queryable state representation of "what is
true right now."

## 3. Forces

**Read latency against write cost.** A materialized view moves computation
from read time to write time, or to a scheduled interval between the two. A
dashboard query that used to scan and aggregate at request time becomes a
single-row lookup. The cost that disappears from the read path reappears as
the cost of maintaining the view, extra writes on every relevant source
change, extra storage for the duplicated, transformed copy of the data, and,
in the incremental case, the operational cost of the pipeline that keeps the
view current.

**Consistency against availability and cost of freshness.** A materialized
view that updates synchronously in the same transaction as the source write
can stay strongly consistent, at the cost of coupling the write path to every
view derived from it and paying that latency on every write. A materialized
view that updates asynchronously decouples the write path completely, at the
cost of a staleness window the reader must tolerate or detect. This is the
same trade-off CQRS names directly. "When the read databases and write
databases are separated, the read data might not show the most recent
changes immediately. This delay results in stale data"
([Microsoft Learn, CQRS pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs),
verified 2026-08-02). The pattern does not remove this force, it makes the
team choose a point on it, deliberately, for each view.

**Storage cost against query flexibility.** Every materialized view is a bet
that a specific, recurring query shape is worth paying storage for. Microsoft
warns that "materialized views tend to be specifically tailored to one, or a
small number of queries. If many queries are used, materialized views can
result in unacceptable storage capacity requirements and storage cost"
([Microsoft Learn, Materialized View pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/materialized-view),
verified 2026-08-02). A generic, flexible schema needs no views. A schema that
answers every popular query fast needs one view per query shape, and the
number of views a team is willing to build and operate is finite.

**Coupling to the source shape against isolation from it.** A view derived
directly from the source schema is cheap to build but breaks whenever the
source schema changes shape. A view built to be schema-independent, driven
entirely by domain events rather than table structure, survives source
refactors better but costs more design effort up front, because the event
shape has to be deliberately designed to be replayable rather than
incidentally derived from whatever the source table happens to look like
today.

**Operational surface area against correctness guarantees.** A native
database `MATERIALIZED VIEW` gives up almost no operational surface, the
database engine owns the refresh, the locking, and the transactional
boundary. A hand-rolled, event-driven, cross-store materialized view gains
enormous flexibility, spanning multiple source systems and target stores of
different kinds, at the cost of the team now owning idempotency, ordering,
retry, and rebuild logic that the database engine would otherwise have
supplied for free.

Engineering judgement, offered here rather than sourced. On most teams the
deciding force in practice is storage and query flexibility rather than
consistency, because storage is cheap and staleness is usually tolerable for
the read in question, but the number of distinct view shapes a team is
willing to hand-build and operate grows slowly and is almost always the
actual ceiling on how far this pattern gets pushed.

## 4. Applicability and non-applicability

Reach for a materialized view when.

- The same expensive query, or a small family of them, runs frequently
  against data whose write rate is much lower than its read rate.
- The source data is spread across multiple stores, services, or bounded
  contexts, and the query needs a combined answer no single store can give
  without a runtime join across a network boundary.
- The system uses Event Sourcing, and a queryable, current-state view is
  needed because the event store alone cannot answer "what is true now"
  without replaying history on every request
  ([Microsoft Learn, Materialized View pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/materialized-view),
  verified 2026-08-02).
- The application must work in an occasionally-connected or offline mode,
  where a locally cached, prepopulated view lets the client answer queries
  without a live connection to the source
  ([Microsoft Learn, Materialized View pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/materialized-view),
  verified 2026-08-02).
- A subset of the source data needs to be exposed for security or privacy
  reasons without granting broader access to the underlying store.

Do NOT reach for a materialized view when.

- **The source data is simple and cheap to query directly.** Microsoft's own
  guidance states this pattern "isn't useful" when "the source data is simple
  and easy to query"
  ([Microsoft Learn, Materialized View pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/materialized-view),
  verified 2026-08-02). Building a view over a query that a single indexed
  lookup already answers in single-digit milliseconds adds a second thing to
  keep synchronized for no benefit.
- **The source data changes faster than the view can usefully stay ahead of
  it.** Very high write rates against a materialized view built for read
  efficiency can turn the view itself into the bottleneck, through write
  amplification, discussed in dimension 3 and dimension 11, and Microsoft
  warns directly against this. "The source data changes very quickly, or can
  be accessed without using a view. In these cases, you should avoid the
  processing overhead of creating views"
  ([Microsoft Learn, Materialized View pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/materialized-view),
  verified 2026-08-02).
- **The read genuinely needs the current, fully consistent value and cannot
  tolerate any staleness window**, for example a payment authorization check
  that must see the latest account balance. Microsoft's own considerations
  section names this directly, this pattern is not useful when "consistency
  is a high priority. The views might not always be fully consistent with the
  original data"
  ([Microsoft Learn, Materialized View pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/materialized-view),
  verified 2026-08-02).
- **The query shape is one-off or rarely repeated.** A materialized view is a
  standing investment against a recurring query. A query that runs once for
  an ad hoc report is cheaper to answer directly.
- **The team has no operational capacity to detect and repair drift.** A
  materialized view that silently falls behind its source and nobody notices
  is worse than no view at all, because the reader trusts a number that is
  quietly wrong. This is explored further in dimension 11.

## 5. Structure

The pattern has four participants, regardless of whether the implementation
is a single SQL statement or a distributed pipeline spanning services.

- **Source store (system of record).** The store, or stores, holding the
  authoritative data. It is written to directly by the application's normal
  write path and knows nothing about the view that depends on it.
- **Change signal.** The mechanism by which the view learns the source
  changed. This ranges from an in-database dependency the query planner
  tracks automatically, in a native `MATERIALIZED VIEW`, to a database
  changefeed such as a write-ahead-log stream or a change-data-capture
  connector, to an application-level domain event published on write, to a
  bare wall-clock timer that periodically re-derives the view whether or not
  anything changed.
- **View builder (maintenance process).** The code, database engine feature,
  or streaming job that consumes the change signal and produces or updates
  the materialized rows. Its two defining responsibilities are correctness of
  the transformation and idempotency against redelivery of the same signal.
- **Materialized store (the view itself).** The queryable copy the read path
  actually hits. It can live in the same store as the source, as with a
  native `MATERIALIZED VIEW`, or in a different store entirely chosen for its
  read characteristics, such as a search index or a wide-column store
  optimized for the exact access pattern the view exists to serve.

The defining structural property, stated by Microsoft as "a materialized view
and the data it contains is completely disposable because it can be entirely
rebuilt from the source data stores"
([Microsoft Learn, Materialized View pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/materialized-view),
verified 2026-08-02), is what makes the materialized store a specialized
cache rather than a second source of truth. If the materialized store cannot
be dropped and rebuilt from the source store without data loss, it is not a
materialized view, it is either a second system of record or a replica with
no cache-invalidation semantics, and the pattern name no longer fits.

## 6. ASCII structure diagram

```
   +------------------+          +--------------------+
   |   Write path     |--------->|  Source store       |
   | (application)     |         | (system of record)  |
   +------------------+          +----------+-----------+
                                             |
                                    change signal
                          (log stream / CDC / domain event / timer)
                                             |
                                             v
                                   +--------------------+
                                   |   View builder      |
                                   | (maintenance job)   |
                                   +----------+-----------+
                                             |
                                     writes derived rows
                                             |
                                             v
   +------------------+          +--------------------+
   |   Read path      |<---------|  Materialized store  |
   | (queries)         |         | (the view itself)   |
   +------------------+          +--------------------+

   The materialized store is disposable. It can be dropped and
   rebuilt from the source store by replaying the change signal
   from the start, or from the last durable checkpoint.
```

## 7. Dynamics

Two distinct runtime flows matter, the steady-state incremental update, and
the full rebuild that recovers from loss or a definition change.

```
Steady-state incremental refresh
---------------------------------

  application         source store        view builder        view store
       |                    |                    |                  |
       |--- write row  ---->|                    |                  |
       |                    |--- change signal -->|                  |
       |                    |   (row id + delta)  |                  |
       |                    |                    |--- has this      |
       |                    |                    |    change id     |
       |                    |                    |    been applied? |
       |                    |                    |------------------|
       |                    |                    |  no, apply delta,|
       |                    |                    |  record change id|
       |                    |                    |----- write ----->|
       |                    |                    |                  |
       |                    |                    |  yes, no-op      |
       |                    |                    |  (idempotent)    |
       |                    |                    |------------------|

Full rebuild
------------

  operator            view builder         source store         view store
     |                     |                     |                    |
     |-- trigger rebuild ->|                     |                    |
     |                     |--- drop / truncate ------------------->  |
     |                     |--- read full snapshot -->|                |
     |                     |<---------- rows ---------|                |
     |                     |--- transform + write ------------------->|
     |                     |--- resume from current change offset --->|
     |                     |    (so new writes during rebuild         |
     |                     |     are not lost)                        |
```

The steady-state flow is the common case and is dominated by one decision,
what happens when the same change signal is delivered twice. Every durable
message transport that offers at-least-once delivery, a Kafka topic, a
database changefeed after a crash and restart, a retried Lambda invocation,
will eventually redeliver. A view builder that is not idempotent against
redelivery will double-apply a delta, and this is one of the most common
production defects in this pattern, discussed further in dimension 11.

The rebuild flow matters because it is the operational proof of the pattern's
core property. A materialized view that cannot be safely rebuilt from its
source, without an operator having to reconcile the two by hand, has quietly
stopped being a cache and become a second source of truth that nobody
budgeted the operational discipline for.

## 8. Implementation variants

**Refresh strategy is the primary axis of variation**, and each has a
distinct latency and load profile.

- **On-demand (query-time rewrite).** The database engine transparently
  rewrites an incoming query against the base tables to instead read from an
  existing materialized structure, when the optimizer determines the view
  covers the query. IBM's Db2 documents this directly for its Materialized
  Query Tables. "If the optimizer determines that a query or part of a query
  could be resolved using an MQT, the query might be rewritten to take
  advantage of the MQT"
  ([IBM Documentation, Materialized query tables](https://www.ibm.com/docs/en/db2/11.5.x?topic=tables-materialized-query),
  verified 2026-08-02). The view still has to be refreshed by one of the
  strategies below, this variant only concerns how the reader reaches it.
  Load profile, zero extra load on the read path beyond the normal optimizer
  work. Latency profile, as fresh as the last refresh, not as fresh as the
  query itself.
- **Manual or explicit refresh.** The simplest variant. An operator or a
  scheduled job issues an explicit statement, `REFRESH MATERIALIZED VIEW` in
  PostgreSQL, that fully or incrementally recomputes the view on demand.
  PostgreSQL's own documentation is explicit that a materialized view "cannot
  subsequently be directly updated" by ordinary writes and needs this
  explicit call to pick up new data
  ([PostgreSQL Documentation, chapter 41.7](https://www.postgresql.org/docs/current/rules-materializedviews.html),
  verified 2026-08-02). Load profile, a single, predictable spike at refresh
  time. Latency profile, fresh only as of the last manual trigger, which can
  be minutes, hours, or days stale depending on who remembers to run it.
- **Scheduled refresh.** The same explicit refresh, run on a timer rather
  than by hand. Simple to reason about, cheap to implement, and the staleness
  window is a known, fixed quantity equal to the schedule interval plus the
  refresh duration. Load profile, a periodic spike, sized to however much of
  the source changed since the last run. Poor fit when the source changes
  fast enough that the spike itself becomes a load problem, or when the
  business needs fresher answers than the schedule interval allows.
- **Full recompute versus incremental recompute, within the on-demand and
  scheduled variants.** A full recompute discards the existing view and
  rebuilds it from the whole source, which is simple and self-healing but
  scales with the size of the source, not the size of the change. An
  incremental recompute applies only the delta since the last refresh, which
  is the approach Blakeley, Larson, and Tompa's original algorithm targets
  and is dramatically cheaper at scale, at the cost of needing a way to
  detect exactly what changed.
- **Event-driven, near-real-time incremental maintenance.** A change event is
  published the moment the source changes, a domain event, a database
  changefeed, a stream of write-ahead-log records, and a consumer applies the
  delta to the view within seconds. This is the variant used by AWS's own
  documented pattern for DynamoDB, where "the aggregation values are updated
  asynchronously through DynamoDB Streams and Lambda. There is typically a
  delay of a few seconds between a download being recorded and the
  aggregation being updated"
  ([AWS Documentation, Using GSIs for materialized aggregation queries](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-gsi-aggregation.html),
  verified 2026-08-02). Load profile, proportional to write volume,
  continuous rather than spiky. Latency profile, seconds of staleness rather
  than minutes or hours, at the cost of building and operating a streaming
  consumer that must handle out-of-order and duplicate delivery.
- **Continuous, dataflow-based incremental view maintenance.** The most
  aggressive variant, where the view is never "refreshed" in the batch sense
  at all, instead a dataflow engine maintains it continuously, applying each
  new input as an incremental update to the output the instant it arrives.
  Materialize documents this as its core mechanism. The product "maintains
  fresh results by persisting them in durable storage and incrementally
  updating them as new data arrives"
  ([Materialize Documentation, CREATE MATERIALIZED VIEW](https://materialize.com/docs/sql/create-materialized-view/),
  verified 2026-08-02), built on a differential dataflow engine that can
  "incrementally maintain views that other databases cannot, views with
  complex joins and aggregations, CTEs, and views on views"
  ([Materialize Documentation, CREATE MATERIALIZED VIEW](https://materialize.com/docs/sql/create-materialized-view/),
  verified 2026-08-02). Load profile, continuous, proportional to the delta
  of every input change, with no periodic spike at all. Latency profile, the
  lowest of any variant, typically sub-second.

## 9. Known production uses

**PostgreSQL, native `MATERIALIZED VIEW`.** PostgreSQL's own SQL statement is
the reference example of the database-engine variant. `CREATE MATERIALIZED
VIEW` stores query results as data, `REFRESH MATERIALIZED VIEW` recomputes
them, and `REFRESH MATERIALIZED VIEW CONCURRENTLY` recomputes without an
exclusive lock, but only "if there is at least one `UNIQUE` index on the
materialized view which uses only column names and includes all rows"
([PostgreSQL Documentation, REFRESH MATERIALIZED VIEW](https://www.postgresql.org/docs/current/sql-refreshmaterializedview.html),
verified 2026-08-02). See dimension 15 for the full detail on that
requirement.

**ksqlDB (Confluent), stream-derived materialized tables.** Confluent's
ksqlDB documentation defines a materialized view as what results "when a
table is derived from another collection", stating that "the benefit of a
materialized view is that it evaluates a query on the changes only (the
delta), instead of evaluating the query on the entire table"
([Confluent Documentation, Materialized Views in ksqlDB](https://docs.confluent.io/platform/current/ksqldb/concepts/materialized-views.html),
verified 2026-08-02). It stores current state locally in RocksDB while the
durable source of truth is the Kafka changelog topic, and pull queries answer
directly from the materialized local state rather than reprocessing the
stream.

**Materialize, incremental-view-maintenance database.** Materialize is built
around the pattern as its central primitive rather than a bolt-on feature.
`CREATE MATERIALIZED VIEW` "maintains fresh results by persisting them in
durable storage and incrementally updating them as new data arrives"
([Materialize Documentation, CREATE MATERIALIZED VIEW](https://materialize.com/docs/sql/create-materialized-view/),
verified 2026-08-02), separating the compute that maintains the view from the
clusters that query it, so the same continuously updated view can be read
from multiple clusters without recomputation.

**Apache Cassandra, native Materialized Views (documented failure).** Apache
Cassandra shipped `CREATE MATERIALIZED VIEW` starting in version 3.0, defined
as "a set of rows which corresponds to rows which are present in the
underlying, or base, table" where "a materialized view cannot be directly
updated, but updates to the base table will cause corresponding updates in
the view"
([Apache Cassandra Documentation 4.1, Materialized Views](https://cassandra.apache.org/doc/4.1/cassandra/cql/mvs.html),
verified 2026-08-02). This is a documented production usage and also a
documented cautionary tale, covered fully in dimension 11.

**Amazon DynamoDB, Streams-plus-Lambda materialized aggregation.** AWS's own
developer guide documents a hand-built version of the pattern, naming it
directly. "You can pre-compute aggregations as data changes and store the
results as regular items in your table. This pattern is called materialized
aggregation"
([AWS Documentation, Using GSIs for materialized aggregation queries in DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-gsi-aggregation.html),
verified 2026-08-02). A DynamoDB Stream captures each write, a Lambda
function applies the incremental delta with an atomic `ADD` update, and a
sparse global secondary index exposes the precomputed aggregate for
single-digit-millisecond reads, at the documented cost of eventual
consistency and, on retry, an approximate rather than exact count, see
dimension 11.

**CQRS read models built as materialized views.** Microsoft's CQRS pattern
guidance explicitly names this as a standard combination. "The read data
store can use its own data schema that's optimized for queries. For example,
it can store a materialized view of the data to avoid complex joins", and
when combined with Event Sourcing, "the read model generates materialized
views from these events, typically in a highly denormalized form"
([Microsoft Learn, CQRS pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs),
verified 2026-08-02).

## 10. Consequences

Positive.

- Read queries against the view are cheap and predictable, because the
  expensive join, aggregation, or cross-store fetch happened once, at write
  time or at refresh time, instead of on every read.
- The write path and the read path can be scaled, indexed, and even hosted on
  entirely different storage technologies independently of each other.
- The view is disposable, it can be dropped and rebuilt from the source data,
  which means a corrupted or wrongly shaped view is a recoverable operational
  incident rather than a data-loss incident, as long as the source retains
  what the rebuild needs.
- Multiple differently shaped views can be derived from the same source data,
  each tailored to a specific query, without changing the source schema or
  degrading the write path for a query that only some readers need.
- In event-sourced systems, the pattern is frequently the only practical way
  to expose current state for querying at all.

Negative.

- The view can lag the source, and every reader of the view must either
  tolerate that staleness or have a way to detect and act on it. Microsoft
  states this directly in the CQRS guidance. "Eventual consistency, because
  the write and read data stores are separate, updates to the read data
  store might lag behind event generation"
  ([Microsoft Learn, CQRS pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs),
  verified 2026-08-02).
- Every materialized view is an additional write, on every relevant source
  change, and a system with several views derived from one hot table can
  suffer real write amplification, covered fully in dimension 11.
- Storage cost grows with the number of views. A schema tailored to many
  distinct queries needs many distinct views, and Microsoft's own guidance
  warns this "can result in unacceptable storage capacity requirements and
  storage cost"
  ([Microsoft Learn, Materialized View pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/materialized-view),
  verified 2026-08-02).
- The team now owns a second thing that can be wrong, not just "is the data
  correct" but "is the view a correct, current derivation of the data",
  which is a genuinely different question and needs its own testing and
  observability, covered in dimensions 15 and 16.
- Every hand-built, event-driven view builder has to solve idempotency,
  ordering, and rebuild correctness itself. A native database
  `MATERIALIZED VIEW` gets this for free from the engine, a cross-store,
  application-level view does not.

## 11. Failure modes and misuse

| Symptom | Cause | Fix |
|---|---|---|
| The view shows a number that does not match the source, and nobody noticed for days or weeks. | No staleness monitoring exists. A materialized view has no built-in signal that tells anyone it stopped updating, it just keeps serving the last value it had, which looks identical to a correctly current value. | Emit a last-updated timestamp or change-offset with every read (see dimension 16), and alert when it exceeds the agreed staleness budget. Treat "view is stale" as a first-class production alert, not something discovered by a customer complaint. |
| A single write to a hot table causes several times the expected write load on the database or storage layer. | Several materialized views are derived from one frequently written source table, and each one applies its own delta on every source write. This is write amplification, roughly N views means roughly N extra writes per source write. | Consolidate views where the shapes overlap. Move view maintenance off the synchronous write path onto an asynchronous consumer so the extra writes do not add latency to the original write, even though the total write volume is unchanged. Batch deltas where staleness tolerance allows. |
| A count or sum in the view is slightly too high, and it only happens under load or after a retry. | The view builder is not idempotent against redelivery of the same change event. AWS documents this exact failure for its Streams-and-Lambda aggregation pattern. "If a Lambda execution fails after writing the updated aggregation value, the stream record may be retried. Because the ADD operation increments the count each time it runs, a retry would increment the count more than once for the same download, leaving you with an approximate value" ([AWS Documentation, Using GSIs for materialized aggregation queries](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-gsi-aggregation.html), verified 2026-08-02). | Key every applied change by a unique event or offset identifier and reject or no-op a delta whose identifier has already been applied, as shown in dimension 6's dynamics diagram. Where an exact count is required, add a condition expression or equivalent check that the specific event has not already been processed, rather than relying on a bare additive update. |
| The materialized view falls permanently out of sync with the base table, and the divergence gets worse over time rather than self-healing. | Apache Cassandra's own documentation for its native Materialized Views warns of exactly this class of bug. Deleting a column from the base table that is not selected in the view "may shadow missed updates to other columns received by hints or repair", and the project's own guidance is to advise "against doing deletions on base columns not selected in views" until the underlying issue is fixed ([Apache Cassandra Documentation 4.1, Materialized Views](https://cassandra.apache.org/doc/4.1/cassandra/cql/mvs.html), verified 2026-08-02). The broader lesson generalizes past Cassandra specifically, any implementation whose maintenance logic has an unproven edge case around deletes, out-of-order delivery, or partial failure can accumulate drift that repair mechanisms cannot detect or correct. | Prefer an implementation whose consistency properties are proven or at minimum widely production-tested, a native RDBMS `MATERIALIZED VIEW`, a well-understood streaming engine, over one flagged as experimental by its own maintainers. Where a home-grown maintenance path is unavoidable, build a periodic reconciliation job that compares a checksum or row count between the view and a fresh recompute from source, and alert on divergence rather than trusting the incremental path forever. |
| `REFRESH MATERIALIZED VIEW` blocks every reader of the view for the duration of the refresh, and dashboards time out during the refresh window. | The default, non-concurrent refresh in PostgreSQL takes a lock that blocks concurrent reads. "Without this option a refresh which affects a lot of rows will tend to use fewer resources and complete more quickly, but could block other connections which are trying to read from the materialized view" ([PostgreSQL Documentation, REFRESH MATERIALIZED VIEW](https://www.postgresql.org/docs/current/sql-refreshmaterializedview.html), verified 2026-08-02). | Use `REFRESH MATERIALIZED VIEW CONCURRENTLY`, after adding the required unique index (dimension 15), when the view must stay readable during refresh. Accept the non-concurrent path only for views where a brief unavailability window during refresh is genuinely acceptable, since the non-concurrent path is faster and lighter for large refreshes. |
| The view was built once, works, and then a schema change in the source silently breaks the transformation, producing wrong rather than missing data. | The view builder was written against the incidental shape of the source table rather than against a deliberately versioned contract, a domain event schema, a documented column contract. A source refactor changes meaning without changing the field the view reads, so the view keeps running and keeps producing output, just wrong output. | Derive views from an explicitly versioned event or contract rather than directly from incidental table shape wherever the source team plans to evolve the schema. Add a contract test that fails the source team's build if a change would alter the meaning of a field the view depends on. |

## 12. Trade-off matrix

Alternatives compared, Cache-Aside, native database Read Replica, and running
the expensive query directly (No View) as the baseline every alternative is
measured against.

| Force | Materialized View | Cache-Aside | Read Replica | No View (direct query) |
|---|---|---|---|---|
| Read latency for the target query | Lowest, the expensive work is already done | Low after warm-up, a cold miss pays full query cost | Moderate, still runs the full query, just against a second copy | Highest, pays the full join or aggregation cost every time |
| Write path impact | Extra write per relevant change, decoupled if async | None on the write path itself, only invalidation | Replication lag, but no extra application-level write logic | None |
| Data reshaping | Full, joins, aggregation, denormalization, cross-store combination | None, the cache stores the same shape as the source, just closer to the reader | None, the replica has the identical schema and shape as the primary | None, reads the source shape directly |
| Staleness model | Explicit and controllable per view (sync, scheduled, event-driven, continuous) | Governed by TTL and invalidation-on-write, per key | Replication-lag bound, usually seconds, shared across all data on the replica | None, always current, by definition |
| Query flexibility for readers | Low per view, each view answers one query shape well | High, the cache holds the same general-purpose shape as the source | Highest, a full copy of the source schema supports any query the primary does | Highest, unrestricted |
| Operational ownership | The team owns the view builder's correctness, idempotency, and rebuild path, unless using a native DB feature | The team owns invalidation correctness only | The database engine owns replication, the team owns lag monitoring | None, no additional component |
| Best fit | A small number of expensive, recurring, cross-store or aggregate queries | Point lookups by key, general-purpose acceleration | Read-scaling the exact same query shape the primary already answers | Cheap queries, or queries too rare to justify precomputation |

## 13. Related and incompatible patterns

**Cache-Aside.** The two are frequently confused because both sit between the
reader and the source and both can go stale. The distinguishing line is
shape, a Cache-Aside cache stores the *same-shaped* record the source holds,
keyed for fast lookup, and is populated lazily on a cache miss. A materialized
view stores a *transformed, reshaped* result, typically the output of a join
or aggregation the source cannot answer in one read, and is populated
proactively by a maintenance process rather than lazily on a miss. A system
can use both together, Cache-Aside in front of the materialized view itself,
to absorb read load on the view's own hot rows.

**CQRS.** Materialized View is the standard implementation technique for the
read side of a CQRS system once the read and write models are split into
separate stores. Microsoft's own guidance states this combination directly,
describing the read data store as able to "store a materialized view of the
data to avoid complex joins"
([Microsoft Learn, CQRS pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs),
verified 2026-08-02). CQRS is the architectural decision to split reads from
writes, Materialized View is one of the concrete techniques for building the
read side once that decision is made.

**Event Sourcing.** When the source of truth is an append-only event log
rather than current-state tables, a materialized view is very often not an
optional optimization but the only practical way to expose queryable current
state, because "materialized views are necessary" in an event-sourced system
where "prepopulating views by examining all events to determine the current
state might be the only way to obtain information from the event store"
([Microsoft Learn, Materialized View pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/materialized-view),
verified 2026-08-02). The two patterns compose so tightly in practice that
many teams treat "event sourcing plus materialized views" as a single
architecture rather than two independently chosen patterns.

**Read-Through Cache and Write-Through Cache.** Both are caching disciplines,
like Cache-Aside, that preserve the source's own shape. They differ from
Materialized View along the same dividing line as Cache-Aside, no
transformation, keyed lookup, and, for write-through, a synchronous update
tied to the write path rather than an asynchronous or scheduled maintenance
job.

**Saga and Retry.** Neither is incompatible with Materialized View, and both
are frequently needed alongside it. A view builder that consumes events
across service boundaries needs the same retry and idempotency discipline as
any other distributed consumer, and a maintenance pipeline spanning multiple
steps, extract, transform, write, benefits from being structured with the
same failure-isolation thinking a Saga applies to a multi-step business
transaction, even when no explicit compensating actions are involved.

**Incompatible with.** Nothing structurally excludes Materialized View, but
it actively fights against any requirement for strict, immediate read-after-
write consistency on the exact field the view holds. A design that promises
"the balance you see immediately after this write is guaranteed correct" is
incompatible with an asynchronously maintained materialized view of that
balance, and needs either a synchronous refresh, a read against the source
directly for that one field, or an explicit consistency-token mechanism
layered on top.

## 14. Refactoring path in and out

**Introducing the pattern.** Start by identifying the single most expensive,
most frequently run query against the current schema, using a slow-query log
or an equivalent profiling tool rather than a guess. Confirm the write rate
on the source data involved is low enough, relative to the read rate, that
precomputing pays off, see the forces in dimension 3. Choose the cheapest
refresh strategy that meets the actual staleness requirement the business
has, not the fastest one available, a scheduled nightly refresh that meets
the requirement is strictly better than an event-driven pipeline that also
meets it, because it is less to build and operate. Build and populate the
view alongside the existing direct-query code path, without removing it.
Compare the view's output against the direct query's output on production
data until confidence is established. Cut reads over to the view, keep the
direct-query path available as a fallback for a period, and only then retire
it. This mirrors the general Strangler pattern of introducing a new path
beside the old one and cutting over incrementally, applied specifically to a
read path.

**Removing the pattern.** A materialized view stops earning its place when
the query it exists to accelerate is no longer expensive, a new index, a
schema change, or a smaller data set changed the economics, when the query is
no longer run often enough to justify the maintenance cost, or when the
staleness the view introduces has become a genuine correctness problem the
business will not accept. Removal is close to the reverse of introduction,
confirm the direct query, run against current infrastructure, meets the
latency budget the view used to provide, cut reads back over to the direct
path, monitor for regressions, and only then drop the view and retire its
maintenance pipeline. Because the view is disposable by definition, dropping
it should never risk data loss, if dropping the view would lose data, it was
never actually a materialized view, it had quietly become a second system of
record and that discovery needs a different remediation than a simple drop.

## 15. Testing and verification

Testing a materialized view has two genuinely different halves that are easy
to conflate, testing that the transformation is correct, and testing that
the maintenance process keeps it correct over time under real operating
conditions.

**Transformation correctness** is the easier half and is ordinary unit
testing, given a known source state, does the view builder produce the
expected view rows. This is straightforward for both a SQL-defined view,
assert the query's output against fixture data, and an event-driven builder,
feed a fixed sequence of events, assert the resulting view state.

**Maintenance correctness under real conditions** is the half most teams
under-test, and it is exactly the half dimension 11's failure modes come
from. At minimum, verify the following.

- **Idempotency.** Apply the identical delta twice and assert the view state
  is unchanged after the second application, exactly as the dynamics diagram
  in dimension 6 assumes. This is the single highest-value test for any
  event-driven view builder, because redelivery is not a hypothetical edge
  case, it is a documented, expected occurrence in every at-least-once
  delivery system, as AWS's own guidance for its Streams-and-Lambda pattern
  confirms directly
  ([AWS Documentation, Using GSIs for materialized aggregation queries](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-gsi-aggregation.html),
  verified 2026-08-02).
- **Out-of-order delivery.** Apply deltas in a shuffled order and assert the
  final view state matches applying them in order, or, where true ordering
  cannot be guaranteed, assert the builder correctly detects and handles the
  out-of-order case rather than silently corrupting the view.
- **Rebuild fidelity.** Drop the materialized view entirely, rebuild it from
  a source snapshot, and assert the rebuilt view is row-for-row identical to
  the incrementally maintained one. This test directly proves the pattern's
  defining property from dimension 5, that the view is genuinely disposable
  and rebuildable, rather than an assumption nobody has ever checked.
- **The `REFRESH ... CONCURRENTLY` unique index requirement.** For a native
  PostgreSQL materialized view that needs concurrent refresh, verify in a
  test environment that the required unique index actually satisfies the
  constraint the database enforces. "This option is only allowed if there is
  at least one `UNIQUE` index on the materialized view which uses only
  column names and includes all rows, that is, it must not be an expression
  index or include a `WHERE` clause"
  ([PostgreSQL Documentation, REFRESH MATERIALIZED VIEW](https://www.postgresql.org/docs/current/sql-refreshmaterializedview.html),
  verified 2026-08-02). Discovering this constraint is unmet in production,
  the first time a concurrent refresh is attempted under load, is a common
  and entirely avoidable incident.
- **Staleness-budget behavior.** Confirm that whatever staleness-detection
  mechanism the view exposes (dimension 16) correctly reports a view as
  stale once its age exceeds the agreed budget, using a controlled clock in
  the test rather than a real wall-clock sleep, so the test is fast and
  deterministic.

## 16. Observability signals

A materialized view is invisible when it is working correctly, which is
exactly what makes silent staleness the most dangerous failure mode in
dimension 11. The signals to expose are the following.

- **View age, or lag behind source.** Expose the timestamp or change offset
  the view was last updated with, either as a queryable field on the view
  itself or as a metric emitted by the maintenance process, and alert when
  it exceeds the agreed staleness budget. AWS's own guidance quantifies this
  directly for its aggregation pattern, readers should expect "typically a
  delay of a few seconds between a download being recorded and the
  aggregation being updated"
  ([AWS Documentation, Using GSIs for materialized aggregation queries](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-gsi-aggregation.html),
  verified 2026-08-02), a system that documents its expected lag can alert
  meaningfully when the actual lag exceeds it.
- **Refresh duration and refresh throughput.** For scheduled or on-demand
  refresh strategies, track how long each refresh takes and how many rows it
  touched. A refresh duration trending upward against a fixed source growth
  rate is an early warning that the strategy needs to move from full to
  incremental, or from scheduled to event-driven, before it becomes an
  incident.
- **Change-signal consumer lag.** For an event-driven or streaming variant,
  the standard consumer-lag metric of the underlying transport, Kafka
  consumer group lag, a changefeed's replication slot lag, a queue's
  in-flight message age, is the direct measurement of how far behind the
  view builder has fallen.
- **Write amplification ratio.** Track writes to the materialized store as a
  ratio of writes to the source it is derived from. A ratio that creeps
  upward over time, without a corresponding increase in the number of active
  views, is a signal that a single view's maintenance logic has become more
  expensive per source write than it used to be.
- **Reconciliation drift.** Where a periodic reconciliation job exists, per
  dimension 11's recommended fix for the Cassandra-class drift failure,
  expose the size of the detected divergence as its own metric, not merely a
  pass or fail flag, so a slow accumulation of drift is visible before it
  crosses whatever threshold triggers an alert.

## 17. Security and privacy implications

A materialized view can be built to hold a deliberately narrower slice of
data than the source it is derived from, and Microsoft's own guidance names
this as a legitimate reason to build one. "Providing access to specific
subsets of the source data that, for security or privacy reasons, shouldn't
be generally accessible, open to modification, or fully exposed to users"
([Microsoft Learn, Materialized View pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/materialized-view),
verified 2026-08-02). Used this way, the pattern can reduce the exposed
attack surface for a given reader, by exposing only the derived, purpose-
built view rather than direct query access to the full source schema.

The same reshaping capability cuts the other way if it is not deliberately
governed. A view is a copy, and every copy of sensitive data is a second
place that data can leak from, a second place access control has to be
enforced correctly, and a second place a retention or deletion obligation
applies. A field excluded from the source table's normal read path, a column
masked by row-level security, for instance, can be silently reintroduced
into a materialized view if the view's own access control is configured
independently of the source's and nobody notices the gap. Because the view
is often built to be broadly and cheaply queryable, exactly the property
that makes it useful, a materialized view that accidentally includes a
sensitive field is frequently more exposed, not less, than the source it was
derived from.

This is engineering judgement rather than a sourced claim. Any team building
a materialized view over data subject to access control, data residency, or
a right-to-erasure obligation should treat the view's own access policy,
data classification, and deletion propagation as a first-class design
question, not an inherited property of the source. A source-side deletion, a
GDPR erasure request, for example, does not automatically imply the
materialized view is purged of that data on the same timeline, the deletion
has to propagate through whatever refresh or event-driven mechanism the view
uses, and the staleness window discussed throughout this entry applies to
deletions exactly as it applies to any other kind of change.

## 18. References

1. Jose A. Blakeley, Per-Ake Larson, and Frank Wm. Tompa, "Efficiently
   Updating Materialized Views", *ACM SIGMOD Record* 15, no. 2 (June 1986),
   61 to 71. [ACM Digital Library, DOI 10.1145/16894.16861](https://dl.acm.org/doi/10.1145/16894.16861),
   verified 2026-08-02.
2. Microsoft Learn, "Materialized View pattern", Azure Architecture Center.
   [https://learn.microsoft.com/en-us/azure/architecture/patterns/materialized-view](https://learn.microsoft.com/en-us/azure/architecture/patterns/materialized-view),
   verified 2026-08-02.
3. Microsoft Learn, "CQRS pattern", Azure Architecture Center.
   [https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs](https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs),
   verified 2026-08-02.
4. PostgreSQL Global Development Group, "41.7. Materialized Views",
   *PostgreSQL Documentation*.
   [https://www.postgresql.org/docs/current/rules-materializedviews.html](https://www.postgresql.org/docs/current/rules-materializedviews.html),
   verified 2026-08-02.
5. PostgreSQL Global Development Group, "REFRESH MATERIALIZED VIEW",
   *PostgreSQL Documentation*.
   [https://www.postgresql.org/docs/current/sql-refreshmaterializedview.html](https://www.postgresql.org/docs/current/sql-refreshmaterializedview.html),
   verified 2026-08-02.
6. IBM, "Materialized query tables", *IBM Db2 Documentation*, version 11.5.
   [https://www.ibm.com/docs/en/db2/11.5.x?topic=tables-materialized-query](https://www.ibm.com/docs/en/db2/11.5.x?topic=tables-materialized-query),
   verified 2026-08-02.
7. Confluent, "Materialized Views", *ksqlDB Concepts*, Confluent Platform
   Documentation.
   [https://docs.confluent.io/platform/current/ksqldb/concepts/materialized-views.html](https://docs.confluent.io/platform/current/ksqldb/concepts/materialized-views.html),
   verified 2026-08-02.
8. Materialize, Inc., "CREATE MATERIALIZED VIEW", *Materialize Documentation*.
   [https://materialize.com/docs/sql/create-materialized-view/](https://materialize.com/docs/sql/create-materialized-view/),
   verified 2026-08-02.
9. The Apache Software Foundation, "Materialized Views", *Apache Cassandra
   Documentation*, version 4.1.
   [https://cassandra.apache.org/doc/4.1/cassandra/cql/mvs.html](https://cassandra.apache.org/doc/4.1/cassandra/cql/mvs.html),
   verified 2026-08-02.
10. Amazon Web Services, "Using Global Secondary Indexes for materialized
    aggregation queries in DynamoDB", *Amazon DynamoDB Developer Guide*.
    [https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-gsi-aggregation.html](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-gsi-aggregation.html),
    verified 2026-08-02.

## Code examples

Three languages are shown because the pattern manifests differently in each
context that commonly implements it by hand rather than through a database
engine feature, a lightweight, in-process incremental aggregate typical of a
Node or browser-adjacent service (TypeScript), a batch or scheduled-refresh
job typical of an analytics or reporting pipeline (Python), and a streaming
consumer typical of the event-driven variant described in dimensions 8 and
9 (Go). All three were run against the toolchain versions installed on the
verification machine and their output is shown beneath each listing. Java,
Rust, and Swift are omitted here because the pattern's interesting
engineering content, incremental delta application and idempotent redelivery
handling, is identical in shape across languages and the three shown already
demonstrate the event-driven, scheduled, and streaming variants distinctly.

### TypeScript. Event-driven, idempotent incremental aggregate

```typescript
interface RatingEvent {
  productId: string;
  rating: number;
  eventId: string;
  occurredAt: number;
}

interface RatingSummary {
  productId: string;
  count: number;
  sum: number;
  average: number;
  lastEventId: string;
  updatedAt: number;
}

class RatingMaterializedView {
  private view = new Map<string, RatingSummary>();
  private processedEventIds = new Set<string>();

  apply(event: RatingEvent): void {
    if (this.processedEventIds.has(event.eventId)) {
      return;
    }
    this.processedEventIds.add(event.eventId);

    const existing = this.view.get(event.productId);
    const count = (existing?.count ?? 0) + 1;
    const sum = (existing?.sum ?? 0) + event.rating;

    this.view.set(event.productId, {
      productId: event.productId,
      count,
      sum,
      average: sum / count,
      lastEventId: event.eventId,
      updatedAt: event.occurredAt,
    });
  }

  read(productId: string): RatingSummary | undefined {
    return this.view.get(productId);
  }

  stalenessMs(now: number, productId: string): number | undefined {
    const row = this.view.get(productId);
    return row ? now - row.updatedAt : undefined;
  }
}

function demo(): void {
  const view = new RatingMaterializedView();
  const events: RatingEvent[] = [
    { productId: "sku-1", rating: 5, eventId: "e1", occurredAt: 1000 },
    { productId: "sku-1", rating: 3, eventId: "e2", occurredAt: 1500 },
    { productId: "sku-1", rating: 3, eventId: "e2", occurredAt: 1500 },
  ];
  for (const e of events) view.apply(e);

  console.log(view.read("sku-1"));
  console.log("staleness ms", view.stalenessMs(2000, "sku-1"));
}

demo();
```

Compiled with `npx tsc --target es2020 --module commonjs` and run with
`node`. Output.

```
{
  productId: 'sku-1',
  count: 2,
  sum: 8,
  average: 4,
  lastEventId: 'e2',
  updatedAt: 1500
}
staleness ms 500
```

The redelivered event `e2` is correctly ignored on its second application,
leaving `count` at 2 rather than 3, exactly the idempotency property
dimension 15 tests for.

### Python. Scheduled refresh with an explicit staleness budget

```python
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class OrderTotal:
    customer_id: str
    total_cents: int
    refreshed_at: float


class StaleViewError(RuntimeError):
    def __init__(self, key: str, age: float, budget: float) -> None:
        super().__init__(f"row {key} is {age:.1f}s old, budget is {budget:.1f}s")
        self.key = key
        self.age = age
        self.budget = budget


class OrderTotalsView:
    """A scheduled-refresh materialized view over a source orders table.
    The view is a specialized cache. It holds no data that is not
    reconstructible by re-running refresh() against the source."""

    def __init__(self, staleness_budget_seconds: float) -> None:
        self._rows: dict[str, OrderTotal] = {}
        self._staleness_budget = staleness_budget_seconds

    def refresh(self, source_rows: dict[str, int], now: float) -> None:
        for customer_id, total_cents in source_rows.items():
            self._rows[customer_id] = OrderTotal(customer_id, total_cents, now)

    def read(self, customer_id: str, now: float) -> OrderTotal:
        row = self._rows.get(customer_id)
        if row is None:
            raise KeyError(f"no materialized row for {customer_id}")
        age = now - row.refreshed_at
        if age > self._staleness_budget:
            raise StaleViewError(customer_id, age, self._staleness_budget)
        return row


def demo() -> None:
    view = OrderTotalsView(staleness_budget_seconds=5.0)
    view.refresh({"cust-1": 4200, "cust-2": 1500}, now=100.0)

    print(view.read("cust-1", now=103.0))

    try:
        view.read("cust-1", now=110.0)
    except StaleViewError as exc:
        print("rejected stale read", exc)


if __name__ == "__main__":
    demo()
```

Run with `python3`. Output.

```
OrderTotal(customer_id='cust-1', total_cents=4200, refreshed_at=100.0)
rejected stale read row cust-1 is 10.0s old, budget is 5.0s
```

The second read is refused because the row's age exceeds the staleness
budget, making the reader's exposure to stale data an explicit, testable
contract rather than an unstated assumption, directly addressing the
staleness-detection gap named in dimension 11.

### Go. Offset-checkpointed incremental consumer

```go
package main

import "fmt"

type Delta struct {
	Offset    int64
	ProductID string
	DeltaQty  int
}

type InventoryView struct {
	quantities map[string]int
	lastOffset int64
}

func NewInventoryView() *InventoryView {
	return &InventoryView{quantities: make(map[string]int), lastOffset: -1}
}

// Apply is idempotent against redelivery. An offset at or below the
// checkpoint is a no-op, so at-least-once delivery cannot double apply.
func (v *InventoryView) Apply(d Delta) {
	if d.Offset <= v.lastOffset {
		return
	}
	v.quantities[d.ProductID] += d.DeltaQty
	v.lastOffset = d.Offset
}

func (v *InventoryView) Read(productID string) int {
	return v.quantities[productID]
}

func main() {
	view := NewInventoryView()
	deltas := []Delta{
		{Offset: 0, ProductID: "sku-9", DeltaQty: 10},
		{Offset: 1, ProductID: "sku-9", DeltaQty: -3},
		{Offset: 1, ProductID: "sku-9", DeltaQty: -3},
		{Offset: 2, ProductID: "sku-9", DeltaQty: 5},
	}
	for _, d := range deltas {
		view.Apply(d)
	}
	fmt.Println("checkpoint offset", view.lastOffset)
	fmt.Println("sku-9 quantity", view.Read("sku-9"))
}
```

Run with `go run main.go`. Output.

```
checkpoint offset 2
sku-9 quantity 12
```

The redelivered offset 1 is skipped, so the final quantity is
10 - 3 + 5 = 12 rather than 10 - 3 - 3 + 5 = 9, again the same idempotent
delta-application shape as the TypeScript example, this time keyed by a
monotonic stream offset rather than an event identifier, which is the
common shape for a consumer built directly against a log-structured
change signal such as a Kafka topic or a DynamoDB Stream.
