---
name: Stream-Table Duality
slug: stream-table-duality
family: 24-stream-processing
category: Stream Processing
aliases: [Stream/Table Duality, Duality of Streams and Tables]
first_described: "Apache Kafka Streams documentation, current, exact original coinage and date unconfirmed; conceptual predecessor, Martin Kleppmann, Turning the Database Inside Out with Apache Samza, Strange Loop 2014, published on the Confluent blog, 2015"
maturity: established
related: [event-sourcing, cqrs, materialized-view, change-data-capture, watermark, event-time-processing]
incompatible_with: []
verified: 2026-08-23
---

## 1. Name, aliases, and lineage

Apache Kafka's own Kafka Streams documentation names the concept directly and
calls it "the so-called stream-table duality." "Now, an interesting
observation is that there is actually a close relationship between streams
and tables, the so-called stream-table duality. And Kafka exploits this
duality in many ways... Essentially, this duality means that a stream can be
viewed as a table, and a table can be viewed as a stream. Kafka's log
compaction feature, for example, exploits this duality." The same page closes
the section by stating the idea is load-bearing, not incidental to the
library's own design. "The stream-table duality is such an important concept
that Kafka Streams models it explicitly via the KStream, KTable, and
GlobalKTable interfaces." Source. Apache Kafka documentation, "Core
Concepts," Kafka Streams, verified 2026-08-23,
https://kafka.apache.org/43/streams/core-concepts/.

ksqlDB's own documentation carries an independently worded framing of the
identical idea, "stream/table duality" with a slash rather than a hyphen,
built around a different worked example. "Streams and tables are closely
related. A stream is a sequence of events that you can derive a table from...
This is a profound realization, and much has been written on this
stream/table duality." Source. Confluent documentation, "Materialized Views,"
ksqlDB, verified 2026-08-23,
https://docs.confluent.io/platform/current/ksqldb/concepts/materialized-views.html.

The clearest conceptual predecessor this entry can honestly point to is
Martin Kleppmann's 2014 talk, published on the Confluent blog in 2015, which
frames a materialized view, a secondary index, and a cache as three instances
of the same underlying idea, derived data continuously transformed from a log
of changes. "The solution is to build materialized views from the writes in
the transaction log. The materialized views are just like the secondary
indexes we talked about earlier, data structures that are derived from the
data in the log, and optimized for fast reading." The talk names Kafka's own
compaction directly as the same technique a database already uses
internally. "Kafka supports compaction, which is a kind of garbage collection
process that runs in the background. It's very similar to the log compaction
that databases do internally." The literal phrase stream-table duality does
not appear anywhere in the primary text of this talk, a fact this entry
states plainly rather than overclaiming a coinage, so it is presented here as
a conceptual ancestor, not as the origin of the name. Source. Martin
Kleppmann, "Turning the Database Inside Out with Apache Samza," Confluent
blog, verified 2026-08-23,
https://www.confluent.io/blog/turning-the-database-inside-out-with-apache-samza/.

## 2. Problem and context

Kafka's own documentation frames the problem as a first-class support gap a
stream-processing technology must close, not a hypothetical. "When
implementing stream processing use cases in practice, you typically need
both streams and also databases. An example use case that is very common in
practice is an e-commerce application that enriches an incoming stream of
customer transactions with the latest customer information from a database
table... Any stream processing technology must therefore provide first-class
support for streams and tables." The Streams DSL developer guide restates
the same gap through a different worked example, a continuously-updated
customer view built from many input event streams. "What your application
will be doing is transforming many input streams of customer-related events
into an output table that contains a continuously updated 360-degree view of
your customers." Source. Apache Kafka documentation, "DSL API," Kafka
Streams, verified 2026-08-23,
https://kafka.apache.org/43/streams/developer-guide/dsl-api/.

The concrete difficulty a naive, hand-rolled answer runs into is named
directly by Kleppmann's own talk, describing the standard application-level
cache pattern this duality replaces. cache invalidation is "tricky," the
architecture is "very prone to race conditions" because writers can update
the database and the cache in a different order concurrently, and a rebuilt
cache has a cold-start problem starting from empty. ksqlDB's own
materialized-views documentation supplies the mechanical answer this entry's
duality gives instead, incremental maintenance rather than full
recomputation. "The benefit of a materialized view is that it evaluates a
query on the changes only, the delta, instead of evaluating the query on the
entire table... In this way, a view is never fully recomputed when new
events arrive. Instead, the view adjusts incrementally."

## 3. Forces

Log-compaction safety versus semantic correctness is the sharpest, most
concretely-stated force in the whole pattern, and Kafka's own DSL
documentation states it as a direct, load-bearing consequence of the
stream-versus-table distinction. "If you were to store a KTable into a Kafka
topic, you'd probably want to enable Kafka's log compaction feature...
However, it would not be safe to enable log compaction in the case of a
KStream because, as soon as log compaction would begin purging older data
records of the same key, it would break the semantics of the data... Hence
log compaction is perfectly safe for a KTable, changelog stream, but it is a
mistake for a KStream, record stream." The same physical storage
optimization is a correctness bug on one side of the duality and a
correctness-preserving space saving on the other, decided purely by which
side of the duality the topic is playing.

Storage and network cost versus join convenience, the KTable-versus-
GlobalKTable trade named directly by the same documentation. "Benefits of
global tables. More convenient and or efficient joins... they support
foreign-key lookups... Downsides of global tables. Increased local storage
consumption compared to the partitioned KTable because the entire topic is
tracked. Increased network and Kafka broker load compared to the partitioned
KTable because the entire topic is read." A GlobalKTable also "has no notion
of time in contrast to a KTable," a correctness and expressiveness trade
named in the same breath as the storage one.

Eager, precomputed correctness versus continuous maintenance load, the cost
side of the general materialized-view idea, named directly by Kleppmann's
own talk. "Maintaining the materialized view puts additional load on the
database, while actually the whole point of a cache is to reduce load on the
database." Correctness by construction, never stale, no cache-miss state, is
bought with continuous background write and compute cost on every upstream
change.

Aggregation-input flexibility versus an always-materialized output, a force
Kafka's own core concepts documentation names as a deliberate design choice.
"In the Kafka Streams DSL, an input stream of an aggregation can be a
KStream or a KTable, but the output stream will always be a KTable. This
allows Kafka Streams to update an aggregate value upon the out-of-order
arrival of further records after the value was produced and emitted...
Because the output is a KTable, the new value is considered to overwrite the
old value with the same key in subsequent processing steps." The trade is
simplicity of a single output type against the fact that a value emitted
from a KStream-of-aggregates is never truly final, a downstream consumer
must know a later record with the same key is a correction, not a new fact.

## 4. Applicability and non-applicability

Reach for stream-table duality thinking when enriching or joining a
real-time event stream against the latest known state of some other entity,
Kafka's own worked example, customer transactions joined against latest
customer information, is exactly this. Reach for it when computing a
rolling aggregate, a count, a sum, a running total, from an unbounded event
stream, the DSL makes this structural since a grouped stream's own aggregate
operation is typed to always produce a table. Reach for it when replicating
a database's current row state to downstream consumers with a natural bound
on storage, precisely the domain log compaction exists for, per Kafka's own
design documentation. "Database change subscription. Each change to the
database will need to be reflected in the cache, the search cluster, and
eventually in Hadoop." Source. Apache Kafka documentation, "Design," Log
Compaction, verified 2026-08-23,
https://kafka.apache.org/43/design/design/#log-compaction.

Do not reach for it when the data is genuinely event-only and must never
collapse to latest-state-per-key. Kafka's own documentation names the exact
failure mode directly, applying compaction, the table-side optimization, to
a stream of discrete facts "would break the semantics of the data," a
credit-card-transaction log or a page-view log is named specifically because
summing or replaying every record matters, not just the last one. Do not
reach for it when every intermediate value in history is needed rather than
only the current value, a compacted KTable by definition only retains the
last update for each key once compaction runs. Do not reach for a
GlobalKTable when the join volume is large and every partition on every
instance is not genuinely required, its own documented downside is
"increased local storage consumption... increased network and Kafka broker
load... because the entire topic is read" on every single instance. Do not
reach for a GlobalKTable when the join site needs a real notion of
event-time correctness, the documentation states plainly that "a GlobalKTable
has no notion of time in contrast to a KTable."

## 5. Structure

KStream, "an abstraction of a record stream, where each data record
represents a self-contained datum in the unbounded data set... data records
in a record stream are always interpreted as an INSERT, think, adding more
entries to an append-only ledger, because no record replaces an existing row
with the same key."

KTable, "an abstraction of a changelog stream, where each data record
represents an update. More precisely, the value in a data record is
interpreted as an UPDATE of the last value for the same record key... a data
record in a changelog stream is interpreted as an UPSERT aka INSERT or
UPDATE because any existing row with the same key is overwritten. Also, null
values are interpreted in a special way, a record with a null value
represents a DELETE or tombstone for the record's key."

GlobalKTable, "like a KTable, a GlobalKTable is an abstraction of a
changelog stream, where each data record represents an update. A GlobalKTable
differs from a KTable in the data that they are being populated with... the
local GlobalKTable instance of each application instance will be populated
with data from all partitions of the topic," versus a KTable where each
instance only sees data from a single partition.

Changelog topic, the durable, log-compacted Kafka topic backing every state
update to a local state store, replayed on recovery. "For each state store,
it maintains a replicated changelog Kafka topic in which it tracks any state
updates... Log compaction is enabled on the changelog topics so that old
data can be purged safely to prevent the topics from growing indefinitely."
Source. Apache Kafka documentation, "Architecture," Kafka Streams, verified
2026-08-23, https://kafka.apache.org/43/streams/architecture/.

State store, a local, queryable store, "a persistent key-value store, an
in-memory hashmap, or another convenient data structure," per the same
architecture page, with ksqlDB's own documentation naming the concrete local
technology it uses. "The current state of a table is stored locally and
ephemerally on a specific server by using RocksDB."

The toStream and toTable operators, the literal, callable API expression of
the duality's two directions. "Table to Stream. KTable to KStream. Get the
changelog stream of this table." and "Stream to Table. KStream to KTable.
Convert an event stream into a table, or say a changelog stream." All from
the DSL API documentation cited above.

## 6. ASCII structure diagram

```
DIRECTION 1: STREAM TO TABLE (aggregation, materialization)

  KStream of raw events
  (alice pageview) (bob pageview) (alice pageview) ...
        |
        |  groupByKey()  ->  KGroupedStream
        v
  .aggregate(initializer, adder)
        |
        v
  KTable  (one current row per key, upserted on every input record)
  key=alice -> count=2
  key=bob   -> count=1
        |
        |  backed by, on restore replayed from:
        v
  state store (local, e.g. RocksDB)  <--- restore ---  changelog topic
                                                          (log-compacted,
                                                           last value wins
                                                           per key)

DIRECTION 2: TABLE TO STREAM (changelog, table.toStream())

  KTable (current state)
  key=alice -> count=2  --(update: 2 to 3)-->  key=alice -> count=3
        |
        |  every UPSERT to the table is itself emitted as a record
        v
  KStream  (the changelog of the table)
  (alice, 2)  (bob, 1)  (alice, 3)  ...
        |
        |  a null value on a key means tombstone, DELETE for that key
        v
  replayed from the start, this stream reconstructs the table exactly,
  the same mechanism log compaction, CDC, and state-store recovery rely on
```

## 7. Dynamics

Materialization, KStream to KTable via aggregate, including incremental
maintenance. Re-aggregating an already-existing table, not a raw stream,
needs a subtractor in addition to the initializer and adder used for stream
aggregation. "When aggregating a grouped stream, you must provide an
initializer, for example aggValue = 0, and an adder aggregator, for example
aggValue + curValue. When aggregating a grouped table, you must additionally
provide a subtractor aggregator, think, aggValue minus oldValue." A
table-of-tables aggregation is maintained by retracting the old contribution
of a changed row and adding its new contribution rather than rescanning
everything, the same incremental-view-maintenance shape ksqlDB describes in
prose.

Changelog and fault tolerance, at runtime. "In addition, Kafka Streams makes
sure that the local state stores are [immune] to failures, too. For each
state store, it maintains a replicated changelog Kafka topic in which it
tracks any state updates... If tasks run on a machine that fails and are
restarted on another machine, Kafka Streams guarantees to restore their
associated state stores to the content before the failure by replaying the
corresponding changelog topics prior to resuming the processing on the newly
started tasks."

Log compaction internals, the mechanism the whole table-as-compacted-stream
side runs on. "Log compaction is handled by the log cleaner, a pool of
background threads that recopy log segment files, removing records whose key
appears in the head of the log. Each compactor thread works as follows. It
chooses the log that has the highest ratio of log head to log tail. It
creates a succinct summary of the last offset for each key in the head of
the log. It recopies the log from beginning to end removing keys which have
a later occurrence in the log." The tombstone mechanism, the DELETE
primitive the duality relies on. "A message with a key and a null payload
will be treated as a delete from the log... This delete marker will cause
any prior message with that key to be removed... but delete markers are
special in that they will themselves be cleaned out of the log after a
period of time to free up space." The same page gives the guarantee that
makes safe reconstruction possible. "Any consumer progressing from the start
of the log will see at least the final state of all records in the order
they were written. Additionally, all delete markers for deleted records
will be seen, provided the consumer reaches the head of the log in a time
period less than the topic's delete.retention.ms setting."

The toStream and toTable operators confirm both directions execute, not
merely define, at runtime. calling table.toStream() is a live, first-class
stream emitting the table's running changelog, and calling stream.toTable()
is a live, first-class table upserting on each incoming stream record.

## 8. Implementation variants

Kafka Streams, the primary, most precisely documented variant, exposing the
duality explicitly through KStream, KTable, and GlobalKTable, with toStream
and toTable as the literal, callable conversion operators between the two
sides.

ksqlDB, a SQL layer over Kafka Streams, expressing the same duality through
CREATE STREAM and CREATE TABLE syntax. A stream is "a partitioned, immutable,
append-only collection that represents a series of historical facts," a
table is "a mutable, partitioned collection that models change over time,"
where "a table represents what is true as of now." The syntax makes the
duality's asymmetry concrete, CREATE TABLE mandates a declared primary key,
"you must declare a PRIMARY KEY when you create a table on a Kafka topic,"
with the same UPSERT and tombstone semantics as a KTable, "a NULL message
value is treated as a tombstone, any existing row with a matching key is
deleted." Source. Confluent documentation, "Streams" and "Tables," ksqlDB,
verified 2026-08-23, https://docs.confluent.io/en/latest/concepts/streams/
and https://docs.confluent.io/en/latest/concepts/tables/.

Materialize, a streaming SQL database, a genuine third variant expressed
through a different vocabulary rather than a KStream and KTable pair.
Sources ingest external changing data, including native Postgres and MySQL
CDC connectors and Kafka topics, into read-only collections, and
materialized views are "incrementally updated" as new data arrives rather
than recomputed. "A materialized view is a view whose underlying query is
executed during view creation. The view results are persisted in durable
storage, and, as new data arrives, incrementally updated." Materialize is
built on differential dataflow, where every collection is internally a
stream of change triples, so the stream side of the duality is an
implementation detail here rather than a first-class, user-facing type the
way KStream is, a genuine difference in framing worth stating honestly
rather than smoothing over. Source. Materialize documentation, "Sources" and
"Views," verified 2026-08-23, https://materialize.com/docs/concepts/sources/
and https://materialize.com/docs/concepts/views/.

## 9. Known production uses

The New York Times' publishing pipeline. Confluent's own blog documents the
system directly by name, quoting NYT's engineers. "All published content is
appended to a Kafka topic in chronological order... The Monolog contains
every asset published since 1851," and, "The Denormalizer is a Java
application that uses Kafka's Streams API. It consumes the Monolog, and
maintains a local store of the latest version of every asset," described in
the same piece as "its own materialized view, representing only the data it
needs." this is a KTable-shaped local state store materialized from an
append-only stream, one of the most widely cited real-world Kafka Streams
stream-table-duality use cases. Source. Confluent blog, "How The New York
Times Publishes Content Using Apache Kafka," verified 2026-08-23,
https://www.confluent.io/blog/publishing-apache-kafka-new-york-times/.

Pinterest's predictive ad-spend budgeting. Pinterest's own engineering blog,
"Spend aggregator, tails input topic and aggregates spends based on adgroup
using Kafka Streams," maintaining "a 10 second window store of inflight
spend per adgroup," a stream aggregated into stateful, table-like windowed
state. worth stating honestly, this piece names window store and aggregation
directly rather than the KTable vocabulary by name, so it demonstrates the
duality's mechanism rather than the library's own terms. Source. Pinterest
Engineering blog, "Using KafkaStreams for Predictive Budgeting," verified
2026-08-23,
https://medium.com/pinterest-engineering/using-kafkastreams-for-predictive-budgeting-9f58d206c996.

## 10. Consequences

A single, unified API surface for both continuous event-history subscription
and point-in-time state lookup is the primary gain, and ksqlDB names the two
query types explicitly over the same underlying duality. a push query
"subscribes to a result as it changes in real-time" while a pull query
"retrieves a result as of now, like a query against a traditional RDBMS,"
fetching "the current state of a materialized view." Kafka Streams' own
equivalent is Interactive Queries, allowing "direct read-only queries of the
state stores by methods, threads, processes or applications external to the
stream processing application," per the architecture page cited above. Fault
tolerance for the same duality is reused as a recovery strategy rather than
invented separately, restoring a failed task's state is literally replaying
its changelog stream, the identical mechanism the duality itself describes.

The cost is storage duplication, a KTable's changelog topic is a second,
durable copy of state on top of the local store, by design. changelog topic
overhead is mitigated but not eliminated by log compaction, and compaction
is a background process, not an instant guarantee, covered further in
Failure modes below. Composing operations across the table side trades
strict consistency for eventual consistency, Kafka's own documentation
states this plainly for table-table joins without versioned stores, "the
join result is a changelog stream and hence will be eventually consistent."
GlobalKTable trades convenience for a real, named storage and network cost,
already quoted in Forces above.

## 11. Failure modes and misuse

Using a GlobalKTable when a partitioned KTable would suffice. a directly
documented downside, not an inferred anti-pattern, "increased local storage
consumption... because the entire topic is tracked," and "increased network
and Kafka broker load... because the entire topic is read," versus a KTable
where each instance is populated "from only one partition of the topic."
The observable production symptom is every application instance replicating
the entire topic locally instead of only its assigned shard, a full,
instance-count-scaled fan-out of storage and broker read load.

Log compaction not keeping up, causing changelog topic bloat. Kafka's own
design documentation states the compaction deadline these thresholds imply
is not a hard guarantee. "Note that this compaction deadline is not a hard
guarantee since it is still subjected to the availability of log cleaner
threads and the actual compaction time. You will want to monitor the
uncleanable-partitions-count, max-clean-time-secs and
max-compaction-delay-secs metrics." A changelog or GlobalKTable-backing
topic can grow unboundedly on disk despite compaction being enabled, if the
cleaner thread pool is starved or a low-throughput topic never crosses its
dirty ratio threshold, directly extending state-restore time on the next
recovery, since restore replays that same bloated topic.

Treating a table-table join as if it carried strict cross-partition
ordering. "For Table-Table joins, if not using versioned stores, then
out-of-order records are not handled... the join result is a changelog
stream and hence will be eventually consistent." A KTable's per-partition
ordering guarantee does not extend across partitions or across topics, the
misuse is assuming a joined or aggregated KTable reflects a globally
consistent snapshot at any instant, when the framework only guarantees
eventual, per-key convergence.

## 12. Trade-off matrix

Against the two other real Kafka Streams abstractions, never a strawman
naive approach.

| Force | KStream | KTable | GlobalKTable |
|---|---|---|---|
| Semantic model | record stream, INSERT, every record a distinct fact | changelog stream, UPSERT, a record overwrites the prior value for that key, null is DELETE | Same UPSERT and changelog semantics as KTable |
| Data locality per instance | not partition-scoped, stateless by default | one partition per application instance, when scaled | all partitions replicated to every instance |
| Storage cost | no durable per-key state by default | one partition's worth of state per instance | full topic replicated on every instance |
| Network and broker load | standard produce and consume | standard, partition-scoped | increased, the entire topic is read by every instance |
| Co-partitioning for joins | required for stream-stream joins | required for stream-table and table-table joins | not required, the whole table is present locally |
| Notion of time | event-time bearing | event-time bearing, used for windowed and versioned semantics | no notion of time |
| Log compaction | unsafe, breaks the semantics of a record stream | safe and expected | safe, backed by the same changelog mechanism as KTable |

## 13. Related and incompatible patterns

Change Data Capture, directly composable, and the natural production-side
technique that most often feeds a KTable. CDC produces exactly the kind of
changelog stream a KTable materializes, and Kafka's own documentation states
the same mechanism serves both purposes. "The same mechanism is used, for
example, to replicate databases via change data capture, CDC... within Kafka
Streams, to replicate its so-called state stores."

Event Sourcing, related but distinct. Event Sourcing is a system-of-record
design decision, the append-only event log IS the durable truth and current
state is always derived, while Stream-Table Duality is a processing-model
framing, a table is one materialized view of a stream and either can be
recovered from the other. A KTable built via KStream.toTable() is a live,
continuously-maintained projection of exactly the kind an event-sourced
system's read model would build.

CQRS, related at the architecture level. CQRS separates the write model,
commands, producing the stream side, from the read model, queries, consuming
the table side. A KStream carrying events and a downstream KTable serving
queries is a natural, concrete implementation shape for CQRS's read and
write split, though CQRS itself is a broader application-architecture
pattern, not tied to Kafka specifically.

Materialized View, the tightest relationship of the four. a KTable is a
materialized view in the general sense, specialized to Kafka's log and
changelog substrate. Materialize's own vocabulary, "materialized view...
incrementally updated," is the identical concept Kafka Streams calls a
KTable, under a different name.

Watermark and Event-Time Processing, published siblings in this same
family, related but orthogonal, not overlapping. both siblings govern when a
stream-time-based computation is considered complete, while Stream-Table
Duality governs what shape the output of that computation takes, a
continuously-updated table. Kafka Streams itself does not use watermark
terminology at all, the sibling Watermark entry documents this directly.
"Kafka Streams uses a non-conformant watermark, referred to as a grace
period." A KTable built by Kafka Streams' windowed aggregation composes
with event-time and grace-period handling, through a differently-named
mechanism than Flink or Beam's watermark.

Incompatible or non-applicable. a purely stateless, non-aggregating stream
pipeline, map, filter, or flatMap only, has no table side at all. Kafka's
own documentation states plainly that "for stateless operations, out-of-order
data will not impact processing logic since only one record is considered
at a time," and there is nothing for such a pipeline to materialize.

## 14. Refactoring path in and out

The naive starting point this pattern replaces is polling, already named
directly by the sibling Change Data Capture entry in this repository. "The
naive answer is polling, where a downstream job runs a query such as SELECT
star FROM orders WHERE updated_at greater than last_poll every few
minutes... it cannot see a delete, because a deleted row produces no row to
select." The refactoring path from there. replace polling with log-based
CDC, Debezium being the standard tool the CDC entry names, writing change
events into Kafka topics. Those topics are now a changelog stream in
Kafka's own sense, the exact mechanism its documentation cites for CDC
replication. Consume that topic as a KTable, StreamsBuilder.table() or
stream.toTable(), or as CREATE TABLE in ksqlDB, giving the application a
continuously materialized, queryable copy of the source table's current
state without polling the source database again. Where the raw event
stream itself is also needed downstream, the same topic can be consumed as
a KStream or CREATE STREAM simultaneously, one topic, two consumption
shapes, chosen per consumer, is the duality's practical payoff.

The path out, away from this pattern. if the data is genuinely stateless
and never aggregated, per the incompatibility named above, introducing
KTable machinery buys nothing but the storage and changelog-topic costs
from Consequences. if strict, immediate cross-partition consistency is
required, per the table-table-join eventual-consistency caveat in Failure
modes, a stream-table-duality-based materialized view is the wrong tool,
and a system with stronger consistency guarantees should be preferred
instead. where a GlobalKTable's full-replication cost is being paid only to
avoid co-partitioning, re-partitioning the source data by the join key,
enabling a plain KTable, is the right descope.

## 15. Testing and verification

Kafka Streams' own TopologyTestDriver "makes it possible to test topologies
without a real Kafka broker, so the tests execute very quickly with very
little overhead," letting a developer "test simple topologies that have a
single processor, or very complex topologies that have multiple sources,
processors, sinks, or sub-topologies." The class exposes getKeyValueStore,
"often useful in test cases to pre-populate the store before the test case
instructs the topology to process an input message, and or to check the
store afterward," which is the direct verification hook for the duality
itself. a test can feed a KStream of input records through the topology,
then assert on the resulting KTable's own state store contents through this
method, proving the materialization direction end to end without ever
starting a broker. Source. Apache Kafka Javadoc, TopologyTestDriver,
verified 2026-08-23,
https://kafka.apache.org/43/javadoc/org/apache/kafka/streams/TopologyTestDriver.html.

## 16. Observability signals

The changelog topic underlying a KTable is an ordinary, replicated Kafka
topic, so its consumer lag during state restoration is observable through
Kafka's own standard consumer-group lag tooling, the same signal used for
any consumer falling behind its source, applied here to the restore
consumer racing to replay a task's changelog before that task can resume
normal processing. this is this entry's own reasoning connecting the
already-sourced fact that state restoration replays the changelog topic
directly to the standard, already-well-established Kafka observability
surface, rather than a specific Kafka-Streams-only metric name this entry
independently verified live, and it is flagged as such. The compaction
health metrics named directly in Failure modes above,
uncleanable-partitions-count, max-clean-time-secs, and
max-compaction-delay-secs, are the second, directly-sourced observability
signal, since a changelog or GlobalKTable-backing topic that silently fails
to compact is exactly the failure this pattern's own restore-time cost
depends on catching early.

## 17. Security and privacy implications

A KTable materializes a durable, potentially long-retained snapshot of the
latest value per key, which changes the privacy posture of a stream
carrying personal data in a way plain event retention does not. a raw
KStream's records age out under the topic's own retention policy, but a
compacted changelog topic keeps the latest value for a key indefinitely
unless an explicit tombstone, a null-valued record for that key, is
produced, meaning a person's most recent state can persist far longer than
the source topic's nominal retention window would suggest. this is this
entry's own reasoning from the documented tombstone and compaction
mechanics in Dynamics above, not a directly quoted warning, since none of
the sources fetched for this entry frame it as a security concern in these
terms. GlobalKTable widens this same concern's blast radius directly, since
its own documented behavior replicates the entire topic, and therefore
every key's latest value, to every application instance, rather than
scoping exposure to the single partition a KTable would confine it to.

## 18. References

Apache Kafka documentation. "Core Concepts." Kafka Streams. Verified
2026-08-23. https://kafka.apache.org/43/streams/core-concepts/.

Apache Kafka documentation. "DSL API." Kafka Streams. Verified 2026-08-23.
https://kafka.apache.org/43/streams/developer-guide/dsl-api/.

Apache Kafka documentation. "Architecture." Kafka Streams. Verified
2026-08-23. https://kafka.apache.org/43/streams/architecture/.

Apache Kafka documentation. "Design." Log Compaction. Verified 2026-08-23.
https://kafka.apache.org/43/design/design/#log-compaction.

Apache Kafka Javadoc. TopologyTestDriver. Verified 2026-08-23.
https://kafka.apache.org/43/javadoc/org/apache/kafka/streams/TopologyTestDriver.html.

Confluent documentation. "Materialized Views." ksqlDB. Verified 2026-08-23.
https://docs.confluent.io/platform/current/ksqldb/concepts/materialized-views.html.

Confluent documentation. "Streams." ksqlDB. Verified 2026-08-23.
https://docs.confluent.io/en/latest/concepts/streams/.

Confluent documentation. "Tables." ksqlDB. Verified 2026-08-23.
https://docs.confluent.io/en/latest/concepts/tables/.

Martin Kleppmann. "Turning the Database Inside Out with Apache Samza."
Confluent blog. Verified 2026-08-23.
https://www.confluent.io/blog/turning-the-database-inside-out-with-apache-samza/.

Materialize documentation. "Sources." Verified 2026-08-23.
https://materialize.com/docs/concepts/sources/.

Materialize documentation. "Views." Verified 2026-08-23.
https://materialize.com/docs/concepts/views/.

Confluent blog. "How The New York Times Publishes Content Using Apache
Kafka." Verified 2026-08-23.
https://www.confluent.io/blog/publishing-apache-kafka-new-york-times/.

Pinterest Engineering blog. "Using KafkaStreams for Predictive Budgeting."
Verified 2026-08-23.
https://medium.com/pinterest-engineering/using-kafkastreams-for-predictive-budgeting-9f58d206c996.

**Evidence grade.** medium-high.

Most solid findings. the KStream, KTable, and GlobalKTable definitions, the
log-compaction safety distinction, and the changelog and fault-tolerance
mechanism are each sourced to a direct, live-fetched quote from Apache
Kafka's own current documentation and Javadoc, verified 2026-08-23.

Unverified or unclear. the exact original coinage and date of the phrase
stream-table duality is not confirmed, Kleppmann's talk is presented as a
conceptual predecessor rather than the source of the term, since the phrase
does not appear in it. dimension 16's changelog-lag reasoning and dimension
17's retention-and-privacy framing are this entry's own inference connecting
already-sourced mechanics, not directly quoted warnings. WebSearch was
unavailable for the session this entry was researched in, so source
discovery relied on direct WebFetch against known or reconstructed canonical
URLs rather than a search-assisted pass, and a small number of guessed URLs,
a Materialize arrangements page and an alternate Kleppmann mirror, did not
resolve before the correct sources were located.

## Code examples

Minimal, illustrative simulations of the two directions of the duality, a
stream folding into a table via a group-and-aggregate step, and a table
emitting its own changelog stream on every update, including tombstone
deletes. These are teaching illustrations of the duality's shape, not a
reimplementation of Kafka Streams' own engine.

### TypeScript

```typescript
type ChangeEvent<V> = { key: string; value: V | null };

class Table<V> {
  private readonly state = new Map<string, V>();
  private readonly changelog: ChangeEvent<V>[] = [];

  upsert(key: string, value: V | null): void {
    if (value === null) {
      this.state.delete(key);
    } else {
      this.state.set(key, value);
    }
    this.changelog.push({ key, value });
  }

  get(key: string): V | undefined {
    return this.state.get(key);
  }

  toStream(): ChangeEvent<V>[] {
    return [...this.changelog];
  }
}

function streamToTable(events: { key: string }[]): Table<number> {
  const table = new Table<number>();
  for (const event of events) {
    const current = table.get(event.key) ?? 0;
    table.upsert(event.key, current + 1);
  }
  return table;
}

function reconstructFromChangelog(changelog: ChangeEvent<number>[]): Map<string, number> {
  const rebuilt = new Map<string, number>();
  for (const change of changelog) {
    if (change.value === null) {
      rebuilt.delete(change.key);
    } else {
      rebuilt.set(change.key, change.value);
    }
  }
  return rebuilt;
}
```

### Python

```python
from dataclasses import dataclass


@dataclass
class ChangeEvent:
    key: str
    value: int | None


class Table:
    def __init__(self) -> None:
        self.state: dict[str, int] = {}
        self.changelog: list[ChangeEvent] = []

    def upsert(self, key: str, value: int | None) -> None:
        if value is None:
            self.state.pop(key, None)
        else:
            self.state[key] = value
        self.changelog.append(ChangeEvent(key=key, value=value))

    def get(self, key: str) -> int | None:
        return self.state.get(key)

    def to_stream(self) -> list[ChangeEvent]:
        return list(self.changelog)


def stream_to_table(events: list[str]) -> Table:
    table = Table()
    for key in events:
        current = table.get(key) or 0
        table.upsert(key, current + 1)
    return table


def reconstruct_from_changelog(changelog: list[ChangeEvent]) -> dict[str, int]:
    rebuilt: dict[str, int] = {}
    for change in changelog:
        if change.value is None:
            rebuilt.pop(change.key, None)
        else:
            rebuilt[change.key] = change.value
    return rebuilt
```

### Go

```go
package streamtableduality

type ChangeEvent struct {
	Key   string
	Value *int
}

type Table struct {
	state     map[string]int
	changelog []ChangeEvent
}

func NewTable() *Table {
	return &Table{state: make(map[string]int)}
}

func (t *Table) Upsert(key string, value *int) {
	if value == nil {
		delete(t.state, key)
	} else {
		t.state[key] = *value
	}
	t.changelog = append(t.changelog, ChangeEvent{Key: key, Value: value})
}

func (t *Table) Get(key string) (int, bool) {
	v, ok := t.state[key]
	return v, ok
}

func (t *Table) ToStream() []ChangeEvent {
	out := make([]ChangeEvent, len(t.changelog))
	copy(out, t.changelog)
	return out
}

func StreamToTable(events []string) *Table {
	table := NewTable()
	for _, key := range events {
		current, ok := table.Get(key)
		if !ok {
			current = 0
		}
		next := current + 1
		table.Upsert(key, &next)
	}
	return table
}

func ReconstructFromChangelog(changelog []ChangeEvent) map[string]int {
	rebuilt := make(map[string]int)
	for _, change := range changelog {
		if change.Value == nil {
			delete(rebuilt, change.Key)
		} else {
			rebuilt[change.Key] = *change.Value
		}
	}
	return rebuilt
}
```
