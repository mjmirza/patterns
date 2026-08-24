---
name: Log Compaction
slug: log-compaction
family: 12-data-storage
category: Data and Storage
aliases: [Key-Based Retention, Compacted Topic, Changelog Compaction]
first_described: "Apache Kafka project, log compaction design added circa 2013 (KAFKA-46), documented in the official Kafka design guide"
maturity: established
related: [lsm-tree, write-ahead-log, change-data-capture, event-sourcing, snapshot-isolation]
incompatible_with: []
verified: 2026-08-02
---

## 1. Name, aliases, and lineage

Log compaction is the name Apache Kafka gave to a retention strategy for an
append-only log. Instead of deleting records once they age past a time or size
limit, a compacted log keeps at least the most recent record for every distinct
key and discards older records that share that key. The name comes directly
from the Kafka project, where the mechanism is documented under "Log
Compaction" in the design section of the official documentation, and the
feature entered Kafka in the 0.8.1 era as part of the work tracked under the
Kafka issue commonly cited as KAFKA-46, which proposed key-based log cleaning
as an alternative to the earlier time and size based deletion.

The same idea appears under other names depending on where it is applied. In
LSM tree storage engines the equivalent operation is folded into ordinary
compaction and is usually just called compaction, without a separate name,
because the storage engine's compaction already discards superseded versions
of a key as a side effect of merging sorted runs. Martin Kleppmann's book
Designing Data Intensive Applications describes this general family of
techniques in Chapter 3, "Storage and Retrieval," under the heading of
compaction for log structured storage engines, and treats Kafka's log
compaction as a specific instance of the same underlying idea applied to a
commit log rather than to a key value store's on disk segments (Kleppmann,
Designing Data Intensive Applications, O'Reilly, 2017, Chapter 3).

A second lineage runs through database systems that use a log as their primary
storage structure. The changelog compaction Kafka Streams relies on for its
internal state stores is the same mechanism reused as a durability substrate
for stream processing state, and the pattern is frequently called changelog
compaction in that context, a term used throughout Confluent's own
documentation of Kafka Streams state store internals.

This entry treats log compaction as the retention discipline of keeping the
latest value per key inside an otherwise append-only, offset-ordered log, as
distinct from the general merge based compaction that LSM tree storage engines
perform on their sorted string tables, which is covered in this repository
under the LSM tree entry. The two mechanisms are close cousins and are cross
referenced throughout, but log compaction is specifically about retention
policy on a commit log with stable, externally visible offsets, while LSM
compaction is about merging on disk sorted runs inside a key value store.

## 2. Problem and context

An append-only log is the simplest and most dependable storage primitive a
distributed system offers. Writes are sequential, replication is
straightforward because followers just copy bytes in order, and readers can
resume from any point by remembering an offset. The problem is that a log
which never forgets grows without bound, and most systems that use a log as
their system of record do not actually need every historical write. They need
the current value.

Consider a table of user profile records replicated as a stream of key value
pairs, one record per change, keyed by user id. A consumer that wants to
rebuild the current state of the table, for instance a new replica joining a
cluster, or a cache warming up after a restart, does not need to replay every
edit a user ever made to their display name. It needs only the last edit for
each user id. If the log is retained purely by time, for example seven days,
then a user who has not changed their profile in eight days effectively
disappears from a naive replay, which is wrong, because their profile still
exists and a system rebuilding state from the log must still see it.

Log compaction exists to reconcile two needs that appear to conflict. The
system wants the unbounded retention semantics of "the log is complete enough
to rebuild current state from scratch at any time," while also wanting the
storage and I/O cost of retaining only what current state actually requires,
which is one record per key rather than one record per write. The context in
which this problem arises is specifically a log used as a changelog, an event
sourced audit trail collapsed into current state, or a replicated table
represented as a stream of upserts and deletes, sometimes called a changelog
stream in the Kafka Streams and ksqlDB world, or the log side of a "table as a
stream, stream as a table" duality that Jay Kreps described in his widely
cited 2013 blog post, "The Log," published on the LinkedIn engineering blog
and later republished by Confluent, on real time data's unifying abstraction
as a log.

The problem does not arise, and log compaction is the wrong tool, when the log
represents a true sequence of discrete events with no notion of a superseding
key, such as a stream of individual click events, individual financial
transactions, or individual sensor readings, where every record is
independently meaningful and none of them supersedes another.

## 3. Forces

**Storage cost versus replay completeness.** An uncompacted log grows linearly
with write volume forever. A compacted log grows with the number of distinct
keys, which is usually far smaller and far more stable, but compaction is not
instantaneous, so there is always a lag between when a key becomes stale and
when the space is freed. This lag is a tuning knob, not a defect, and
systems that need tighter space bounds must compact more aggressively at the
cost of more I/O.

**Read amplification versus write amplification.** Kafka's log compaction
avoids rewriting the log on every write, unlike an LSM tree, which
continuously merges. Instead it batches compaction into periodic sweeps by a
background cleaner thread, driven by a dirty ratio threshold. This favors low
write amplification most of the time, at the cost of the log occasionally
containing more duplicate keys than a fully compacted log would, which a
consumer doing a full replay must tolerate by applying records in order and
letting later records for the same key win.

**Offset stability versus space freed.** A compacted log must preserve
the total order and, critically, the numeric identity of the offsets that
survive compaction, because consumers track progress by offset and expect
that offset to always refer to the same logical position in the partition.
This forces the cleaner to remove whole records rather than renumbering
anything, which in turn means compaction can only ever free the space of
records it deletes, never compress the remaining records into denser storage
by changing their offsets.

**Deletion semantics versus permanence.** Representing a delete inside an
append-only structure requires a tombstone, a record that says the key is
gone rather than simply omitting the key. But a tombstone left forever also
never truly frees space, and a consumer that starts reading after the
tombstone has been cleaned would never learn the key was deleted at all, only
that it is currently absent. This forces a second retention window,
specifically for tombstones, that is longer than the time any lagging
consumer is expected to take to catch up, which is a probabilistic
correctness argument rather than a hard guarantee.

**Consistency of reads during compaction versus operational simplicity.**
Compaction runs concurrently with ongoing reads and writes. The design favors
operational simplicity, compaction is a background job with no coordination
protocol with readers, over strict point in time consistency, a reader
scanning the log while compaction runs may observe a mix of pre and
post-compaction state, which is safe only because the guarantees Kafka
provides are about eventual convergence to correct current state, not about
snapshot isolation of a scan in progress.

## 4. Applicability and non-applicability

Apply log compaction when the following hold.

- The log represents a changelog of a keyed entity and downstream consumers
  only ever care about the current value per key, for example a table
  replicated as a stream of upserts, as documented in Confluent's Kafka
  Streams state store design, where each key's changelog partition is a
  compacted topic used to restore in-memory or RocksDB backed state stores
  after a failure.
- A new consumer, or a consumer recovering from failure, needs to be able to
  rebuild complete current state by replaying the log from the beginning,
  without needing an external snapshot mechanism, and the number of distinct
  keys is bounded and much smaller than the total write volume over the
  system's lifetime.
- The system explicitly wants unbounded retention of current state paired
  with bounded retention of history, for example a topic backing a
  materialized cache, a configuration store, or a device registry where old
  configuration values have no value once superseded.
- Deletes are meaningful and rare relative to updates, so tombstone volume
  stays small relative to the total key population.

Do not apply log compaction when any of the following hold.

- Every record is independently significant regardless of key, such as a
  stream of financial transactions, audit log entries, or telemetry events,
  where record number ten for a given key is not superseded by record number
  eleven, both must be retained. Compacting such a log silently destroys data
  the business or the auditors need.
- The system needs to answer what the value was at an arbitrary historical
  point in time, meaning it needs full history rather than current state,
  because the history that compaction discards is exactly the information a
  temporal query needs. Use a separate time based retention topic, or an
  explicit versioned store, instead.
- Keys are effectively unbounded and monotonically increasing with no natural
  reuse, for example a raw event id used as the key on an event stream. In
  that case every key is unique, so compaction degenerates to doing nothing
  useful while still paying the background cleaner's CPU and I/O cost.
- The consuming system cannot tolerate the reordering-adjacent behavior where
  a consumer that starts mid-stream may never see the very first value a key
  ever had, only the most recent one as of when it started reading, because
  older values were already compacted away. Systems that need the full
  history of every key belong on time based retention or a separate archival
  sink, not a compacted topic.
- Very high key cardinality relative to available disk, where the number of
  distinct live keys is itself large enough that log compaction does not
  actually bound storage in any useful way, in which case compaction still
  runs but buys little.

## 5. Structure

**Log partition.** The physical unit compaction operates on. In Kafka, a
partition is a sequence of segment files. Compaction always operates within a
single partition; it never merges across partitions, because cross-partition
merging would break the offset ordering and delivery guarantees Kafka
provides per partition.

**Segment.** A contiguous, immutable file range within a partition once it is
no longer the active segment being appended to. Kafka's log cleaner only
compacts closed segments, never the currently active segment that is still
receiving writes, because compacting a file that is being appended to at the
same time would require far more delicate concurrency control.

**Head and tail.** The Kafka log compaction design divides a partition
conceptually into a tail, the older, already compacted portion, containing at
most one record per key, and a head, the newer, not yet compacted portion,
where duplicate keys may still exist because compaction has not reached them
yet. New writes always land in the head. The cleaner's job is to slowly
absorb the head into the tail.

**Offset map.** A cleaner thread builds an in-memory hash map from key to the
latest offset for that key within the segments being cleaned in the current
pass, bounded by a configurable memory budget. This map is what lets the
cleaner make a single pass over the dirty segments and decide, for every
record, whether a later offset for the same key exists further ahead, in
which case the earlier record is dropped.

**Log cleaner thread pool.** One or more background threads, configurable via
`log.cleaner.threads` in Kafka, that continuously pick the partition with the
highest dirty ratio, compact it, and move to the next, throttled by an I/O
budget so compaction does not starve foreground produce and fetch traffic.

**Tombstone.** A record with a non-null key and a null value, representing a
logical delete of that key. A tombstone is itself compacted away, but only
after `delete.retention.ms` has elapsed since it was written, to give slow
consumers a window in which they are guaranteed to see the tombstone rather
than simply seeing the key vanish with no explanation.

**Dirty ratio.** The fraction of a partition's log, by bytes, that lies in the
head, meaning it has not yet been through a compaction pass, relative to the
total log size. Kafka's `min.cleanable.dirty.ratio` setting, default 0.5,
controls the threshold at which the cleaner considers a partition worth
compacting; below the threshold the cleaner leaves the partition alone to
avoid the fixed overhead of a compaction pass for marginal space savings.

## 6. ASCII structure diagram

```
PARTITION (single log)

TAIL (compacted, <=1 record/key), closed, immutable
  segment.0   segment.1   segment.2
  [k1=v1]     [k3=v2]     [k2=v3]

HEAD (dirty, duplicates ok)
  segment.3         segment.4 (active,
  [k1=v4][k3=T]     still being appended)
                    [k4=v5][k1=v6]

log cleaner reads dirty segments (HEAD), then:
  builds offset map, key to highest offset
  rewrites TAIL with duplicates dropped,
  tombstones kept (tombstones dropped only
  after delete.retention.ms elapses)

Cleaner selection loop (one pass, repeats):

for each partition P in cluster (round robin by
dirty ratio):
    dirty_ratio = bytes(head(P)) / bytes(P)
    if dirty_ratio < min.cleanable.dirty.ratio:
        skip P this round
    else:
        build_offset_map(head(P))  # key -> offset
        for segment in dirty_segments(P):
            for record in segment:
                if record.offset ==
                   offset_map[record.key]:
                    keep record  # latest
                elif record.is_tombstone and
                     age(record) < delete.retention.ms:
                    keep record  # grace window
                else:
                    drop record  # superseded
```

## 7. Dynamics

The runtime behavior splits into three independent flows that never block one
another. producing, consuming, and cleaning.

**Produce path.** A producer writes a record with a key and a value to a
compacted topic exactly as it would to any Kafka topic. The record is
appended to the active segment at the current end offset. Nothing about
compaction is visible to the producer; the write is a normal, fully
sequential append, and the broker assigns the next offset in strict order
regardless of whether the key has appeared before.

**Consume path.** A consumer reads sequentially from whatever offset it is
tracking. Because compaction has already run over older segments by the time
a typical consumer reaches them, a consumer doing a fresh read from the
beginning of a compacted topic sees, for each key, only its most recent
surviving value, in the order those surviving records happen to sit in the
log, which is the order of their original offsets, not re-sorted by key.
Kafka's documentation states this explicitly as one of compaction's core
guarantees. ordering of messages is never changed by compaction, only some
messages are removed, and a consumer reading from the start is guaranteed to
see at least the final state of every key that existed as of the time the
consumer started, in the order those records were originally written.

**Compaction cycle.** Independently of any consumer or producer activity, a
log cleaner thread periodically scans all partitions across all compacted
topics on the broker and computes each partition's dirty ratio. When a
partition's dirty ratio crosses `min.cleanable.dirty.ratio`, or the partition
has segments older than `max.compaction.lag.ms`, the cleaner selects it for
compaction. It builds the offset map over the dirty segments, then performs a
single sequential pass, writing surviving records to a new set of segment
files and swapping them in atomically once the pass completes, so that
readers see either the fully pre-compaction or fully post-compaction segment,
never a partially rewritten one.

**Tombstone lifecycle.** When a producer writes a null-valued record for a
key, on the next compaction pass every earlier value for that key is dropped,
and the tombstone itself is retained, but marked with the time it was
written. Once `delete.retention.ms` has elapsed since that write, the next
compaction pass drops the tombstone too, and from that point on the key
simply does not appear in the log at all, which is indistinguishable, for a
consumer that starts reading afresh after that point, from the key never
having existed.

**Restart and recovery flow.** This is the dynamic that motivates the whole
pattern. A stateful consumer, for example a Kafka Streams application
instance or a KTable materialization, that loses its local state, restarts
by seeking to offset zero on its changelog partition and replaying the entire
partition sequentially. Because the partition is compacted, this replay reads
one record per key rather than one record per historical write, which bounds
recovery time by the number of distinct keys rather than by the total
lifetime write volume of the application, and this bound is exactly what
makes the pattern operationally viable at scale, as described in Confluent's
documentation of Kafka Streams fault tolerance via changelog topics.

## 8. Implementation variants

**Segment-boundary compaction with an in-memory offset map, Kafka's actual
implementation.** The variant described above. Compaction is a background,
best-effort, batched process bounded by a dirty ratio threshold, and it never
touches the active segment. This is the canonical implementation and the one
most engineers mean when they say log compaction.

**Compaction on read, lazy compaction.** Some systems, rather than physically
rewriting storage, defer key deduplication to query time by merging records
from multiple sources at read time, choosing the most recent value for each
key as part of the read path, and only physically compact storage in the
background as an optimization, not a correctness requirement. This trades
higher read latency and CPU for simpler, less time-critical write-path
invariants, and it is closer to how an LSM tree serves a point read that
spans multiple SSTables before a compaction has run, which Kleppmann
describes in Designing Data Intensive Applications, Chapter 3, as the merge
step a read must perform across multiple on-disk sorted runs.

**Full-history plus compacted-view, side by side.** Instead of compacting the
canonical topic, some architectures keep the raw, uncompacted event log
forever, for full auditability, and additionally maintain a second,
compacted topic populated by a stream processing job that reduces the raw
events to latest-value-per-key. This is the pattern behind many changelog
topics fed by Kafka Streams' `KTable.toStream()` output, and it decouples the
retention policy engineers want for audit purposes from the retention policy
they want for fast state rebuild.

**Time-windowed compaction hybrid.** Cassandra's TimeWindowCompactionStrategy
is a related but distinct idea. Rather than compacting by key across the
whole partition's history, it groups SSTables into fixed time buckets and
compacts within a bucket, which is a form of compaction tuned for
time-series data with natural expiry rather than for key-based upsert
semantics, and it is explicitly documented in the Apache Cassandra operations
guide as one of several selectable compaction strategies alongside
SizeTieredCompactionStrategy and LeveledCompactionStrategy, each tuned for a
different write and read pattern rather than for key-based retention.

**Compaction with configurable minimum lag.** Kafka additionally exposes
`min.compaction.lag.ms`, a setting that keeps a record in the head,
ineligible for compaction, for at least that duration after it was written,
independent of the dirty ratio. This variant is used when downstream
consumers need a guaranteed minimum window in which every intermediate value
for a key is still visible, trading slower space freeing for a stronger
read-recency guarantee for consumers that are only briefly behind.

## 9. Known production uses

**Apache Kafka itself, as the mechanism backing Kafka Streams state store
changelog topics.** Every stateful operation in Kafka Streams, aggregations,
joins, and KTable materializations, persists its state both locally in
RocksDB and remotely as a compacted changelog topic, so that a failed
instance can be reassigned to another node and rebuild its exact local state
by replaying the compacted changelog rather than replaying the full input
event history, which is documented as the core fault tolerance mechanism in
Confluent's Kafka Streams architecture documentation.

**Kafka Connect's internal offset and config topics.** Kafka Connect, the
framework for building source and sink connectors on top of Kafka, stores its
own internal bookkeeping, connector configurations, task offsets, and status,
in three internal topics that are all created with `cleanup.policy=compact`,
so that the framework only needs the current configuration and current offset
per connector, never the full history of configuration changes, as described
in the Apache Kafka Connect user guide's section on internal topics.

**Debezium's schema history and Kafka-backed CDC change streams.**
Debezium, an open source change data capture platform built on Kafka Connect,
publishes row-level changes to compacted Kafka topics for use cases such as
maintaining a materialized cache of the latest row state, and Debezium's own
documentation on Kafka topic configuration explicitly recommends
`cleanup.policy=compact` for change event topics that are intended to serve
as a queryable latest-state changelog rather than a full append-only audit
log, distinguishing it from the separately retained raw change event stream.

**ksqlDB and KSQL materialized tables.** ksqlDB, Confluent's streaming SQL
engine built on Kafka Streams, backs every `CREATE TABLE` construct with a
compacted Kafka topic under the hood, because a SQL table has upsert
semantics by primary key, and the Confluent documentation for ksqlDB tables
states directly that the underlying changelog topic for a table should be
compacted so that the table reflects only the latest row per key rather than
every historical row version.

## 10. Consequences

**Positive.**

- Bounded storage growth for systems whose value is current state rather
  than full history, because storage now scales with the number of distinct
  keys rather than the total write volume over the system's lifetime.
- Full state rebuild without an external snapshot mechanism. A fresh
  consumer, or a consumer recovering from a total loss of local state, can
  reconstruct correct current state purely by replaying the compacted log
  from the start, which removes an entire class of snapshot-and-log
  coordination problems that systems without compaction must solve
  separately.
- Preserves the operational simplicity of an append-only log on the write
  path; producers never need to know a topic is compacted, and writes remain
  simple sequential appends with no read-modify-write cycle.
- Offset stability is preserved, so consumer position tracking, exactly-once
  semantics built on offset commits, and monitoring based on consumer lag all
  continue to work unmodified on a compacted topic.

**Negative.**

- Consumers lose access to full history. Once compaction has run, a consumer
  cannot answer what the value of a key was several writes ago, only what
  its current value is, and roughly when the surviving records for other
  keys landed relative to it. This is an intentional trade-off, not a bug,
  but it is frequently a surprise to engineers who assumed a Kafka topic is
  durable history by default.
- Compaction lag creates a real window in which stale duplicate keys are
  still physically present in the head. A consumer reading only the head, for
  example one that only ever reads the last hour of a topic, may see multiple
  values for the same key in that window and must be written to handle that,
  applying records in order and letting the latest one win, rather than
  assuming uniqueness.
- Deletes are eventually-consistent from a storage perspective. A tombstone
  is present for `delete.retention.ms` and then vanishes, and a very slow or
  long-paused consumer that resumes after that window can silently miss the
  fact that a key was deleted at all, seeing only its absence with no
  explanation.
- Background cleaner threads consume CPU and I/O, competing with foreground
  produce and fetch traffic, and on a cluster with many high-cardinality
  compacted topics this background load is a real capacity planning line
  item, not a rounding error.
- Compaction only ever operates on closed segments, never the active one, so
  a topic with very large active segments, or a very low write rate that
  rarely rolls segments, can accumulate substantial dirty data before it
  becomes eligible for compaction at all.

## 11. Failure modes and misuse

**A topic configured for compaction keeps growing without bound.** Symptom,
disk usage on the partition grows steadily with produce throughput and never
plateaus. Cause, the topic's key space is effectively unbounded, for example
the producer is using a random UUID or an incrementing event id as the key
rather than a stable business entity id, so nearly every record is a
distinct key and compaction has nothing to deduplicate. Fix, audit the
keying scheme; compaction only frees space between records that share a
key, so the key must be the entity identity the application actually wants
latest-value semantics for, not a per-event unique id.

**A consumer replaying from the beginning sees fewer records than expected,
missing entities the operator knows exist.** Symptom, a rewind to offset
zero on a compacted topic produces a smaller record set than the operator
expects, and specific known entities are absent. Cause, this is very
frequently not a bug, it is compaction working as designed, but it is
misdiagnosed as data loss. If it is a genuine problem, the actual cause is
usually that the consumer started reading after a tombstone for a still
relevant key had already been cleaned, so the consumer never learns the key
existed and was deleted rather than never having existed. Fix, distinguish
between a key that was correctly deleted and a key whose value was silently
lost, which requires checking application logic for whether a tombstone was
ever legitimately produced for that key, and if tombstones are being
produced unintentionally, for example by a serialization bug that turns an
empty payload into a null payload, fix the producer, not the compaction
configuration.

**High CPU and I/O on brokers correlated with a specific compacted topic.**
Symptom, higher broker CPU and disk I/O with no obvious change in produce
or consume traffic, correlated in time with one particular compacted topic.
Cause, the topic's dirty ratio threshold, active segment size, or
per-partition write rate combine to trigger frequent, large compaction
passes, often because `segment.bytes` was left small relative to write
throughput, causing many small segments to roll and each one to become
independently eligible for cleaning. Fix, tune `segment.bytes` and
`segment.ms` upward for high-throughput compacted topics so fewer, larger
compaction passes run less often, and confirm `min.cleanable.dirty.ratio` is
not set so low that the cleaner is essentially running continuously.

**A downstream system built on a compacted changelog processes stale or
out-of-order-looking updates for the same key.** Symptom, an application
consuming a compacted topic observes what looks like an old value for a key
arriving after a newer one. Cause, the consuming application is reading
across multiple partitions and merging without respecting per-key ordering,
or it is naively deduplicating by value rather than by offset. Fix, within a
single partition, Kafka guarantees offset order is preserved by compaction;
the fix is almost always in the consumer's merge logic across partitions or
in an incorrect assumption that a compacted topic guarantees global,
cross-partition key uniqueness, which it does not, uniqueness is only
guaranteed within a partition, so the partitioning key must equal the
compaction key or duplicates across partitions will persist indefinitely.

**Treating a compacted topic as an audit log is a category misuse.** A team
stores financial transaction events, keyed by account id, on a compacted
topic to save space, not realizing that a subsequent transaction for the
same account will eventually cause an earlier transaction for that account
to be compacted away. Compaction is for keeping the latest state per key, and
a transaction log needs every transaction, so the key should either be
unique per transaction, which defeats the purpose of compaction entirely, or
the topic should simply not be compacted and should use time or size based
retention instead.

## 12. Trade-off matrix

| Force | Log compaction (Kafka-style) | Time/size based retention | LSM tree compaction (general) | Snapshot plus incremental log |
|---|---|---|---|---|
| Storage bound | Bounded by distinct key count | Bounded by time or byte window regardless of key | Bounded by live key count, similar to log compaction | Bounded by snapshot size plus recent log window |
| History availability | Only most recent value per key, eventually | Full history within the retention window, then gone entirely | Only most recent value per key, same as log compaction | Full history reconstructible from snapshot chain plus log |
| Write path cost | Plain sequential append, cost deferred to background cleaner | Plain sequential append, cost deferred to segment deletion | Every write eventually rewritten during merge, ongoing cost | Snapshot write is a distinct, periodic bulk operation |
| Recovery from scratch | Replay compacted log, bounded by key count | Replay entire retained window, bounded by time or size, may miss old keys | Read merged view across SSTables, similar characteristics | Load snapshot, then replay only the log since the snapshot |
| Delete semantics | Explicit tombstone with its own retention window | Implicit, the record simply ages out with everything else | Explicit tombstone, same idea as log compaction, internal to the engine | Explicit delete marker must be captured in both snapshot and log |
| Operational complexity | Moderate, one extra background process, one extra config surface | Low, nothing beyond the normal retention job | Moderate to high, it is the storage engine's core write path, not optional | Higher, two subsystems, snapshot and log, must be kept mutually consistent |

## 13. Related and incompatible patterns

**LSM tree.** The general merge-based compaction that underlies most LSM
tree key-value stores, described in this repository's own LSM tree entry, is
the closer, storage-engine-level cousin of log compaction. Where log
compaction is a retention policy layered onto an already-existing
append-only commit log with stable external offsets, LSM compaction is an
intrinsic, mandatory part of how the storage engine serves reads at all,
because without periodic merging a point read would need to check an
unbounded number of on-disk sorted runs. A system can use both together. a
Kafka Streams application both writes to a compacted changelog topic on
Kafka, which is log compaction, and stores its local materialized view in
RocksDB, which itself performs LSM-style leveled or universal compaction
internally, as documented in the RocksDB project's compaction design.

**Write-ahead log.** Log compaction assumes an underlying append-only log,
and the write-ahead log entry in this repository covers the general
mechanics of an append-only durability log. Log compaction is best
understood as one specific retention policy that can be layered on top of a
write-ahead log's storage structure, once the log is also expected to serve
as a long-lived changelog rather than purely as a crash-recovery mechanism
that gets truncated after a checkpoint.

**Change data capture.** CDC pipelines, covered elsewhere in this repository,
frequently write their output to compacted Kafka topics precisely because
the output is naturally keyed by the source table's primary key and has
upsert semantics, a later change event for a given row supersedes an earlier
one for the purpose of maintaining a materialized replica, which is exactly
the scenario log compaction targets.

**Event sourcing.** Log compaction is in direct tension with a pure event
sourcing architecture where every event is independently significant and the
system's true source of truth is the full ordered sequence of events, not
merely the latest state. Applying log compaction to an event-sourced
aggregate's event stream would silently discard the very history the
pattern exists to preserve, so event sourcing systems either keep their
event streams uncompacted and derive a separate compacted current-state
projection, or they explicitly accept that only the projection, not the raw
events, is safe to compact.

**Snapshot isolation.** Snapshot isolation, covered elsewhere in this
repository, is a read-consistency guarantee for a database transaction, and
it is largely orthogonal to log compaction, but the two interact where a
compacted changelog is used to rebuild a snapshot. the completeness
guarantee log compaction provides, that a full replay yields the correct
current state as of when replay started, is what makes it safe to treat a
replay of a compacted log as equivalent to reading a consistent snapshot,
even though compaction itself provides no isolation guarantee for readers
racing an in-progress compaction pass.

## 14. Refactoring path in and out

**Introducing log compaction into an existing uncompacted, keyed stream.**

1. Confirm every record on the topic already carries a stable key that
   represents the entity the application wants latest-value semantics for,
   not a per-event unique identifier. If the current keying scheme is wrong,
   fix the producer first, on an uncompacted topic, and let the fix bake in
   before touching retention policy, because changing the key and the
   retention policy simultaneously makes it much harder to tell which change
   caused an observed regression.
2. Verify that every consumer of the topic is already tolerant of receiving
   multiple records for the same key over time and applies them in offset
   order, taking the latest as authoritative. Most well-behaved changelog
   consumers already do this, since it is also required to handle ordinary
   retries and reprocessing, but it is worth an explicit check before
   enabling compaction, because compaction will surface any consumer that
   was silently relying on seeing every historical value.
3. Create a new topic with `cleanup.policy=compact` set from creation, rather
   than converting an existing uncompacted topic in place. Changing
   `cleanup.policy` on a live topic is supported by Kafka, but starting fresh
   avoids any ambiguity about which already-written records were subject to
   the old policy versus the new one, and it gives an explicit cutover point
   to reason about.
4. Migrate producers to the new topic, and run both the old, uncompacted
   topic and the new, compacted topic in parallel for a bake-in period,
   directing new consumers to the compacted topic while legacy consumers
   that still need full history continue reading the old one.
5. Tune `min.cleanable.dirty.ratio`, `segment.bytes`, `delete.retention.ms`,
   and, if a minimum recency guarantee matters, `min.compaction.lag.ms`,
   based on observed write rate and observed downstream consumer lag,
   starting from Kafka's documented defaults and adjusting only after
   observing actual compaction pass frequency and duration in metrics.
6. Once confidence is established, deprecate and retire the old,
   uncompacted topic, or repurpose it explicitly as a permanent audit log
   with its own, separate, time-based retention policy, rather than leaving
   both topics running indefinitely with no clear ownership of which is
   authoritative.

**Removing log compaction once it stops earning its place.**

1. Identify why compaction is being removed. typically either the key space
   turned out to be effectively unbounded, defeating the point, or a new
   requirement emerged for full history that compaction cannot satisfy.
2. If full history is now required, do not simply flip `cleanup.policy` back
   to `delete` on the existing compacted topic, because the history that was
   already compacted away is permanently gone; instead, introduce a new,
   uncompacted topic going forward and accept that historical values prior
   to the cutover are unrecoverable from this Kafka cluster, or restore them
   from an external archival source if one exists, such as a data lake sink
   that was independently retaining raw events.
3. Migrate producers to the new topic and update consumers to read from it,
   following the same parallel-run-then-cutover discipline as the
   introduction path, in reverse.
4. Retire the compacted topic once all consumers have migrated, or leave it
   running as a lightweight latest-known-state index alongside the new
   full-history topic if both views remain independently useful.

## 15. Testing and verification

Log compaction is easy to test in isolation because Kafka exposes the
compaction outcome as an observable property of the log itself, not as an
opaque internal detail. A test setup can produce a known sequence of keyed
records, including at least one repeated key with multiple values and one
tombstone, force a compaction pass, and then assert on what a full replay
from offset zero returns.

Kafka's own test suite, and integration test frameworks built on top of it
such as those using Testcontainers' Kafka module, typically verify
compaction behavior by lowering `segment.bytes` and `segment.ms` to force
rapid segment rolling, lowering `min.cleanable.dirty.ratio` to near zero to
force aggressive cleaning, and then triggering the log cleaner explicitly or
waiting a short, deterministic interval before asserting on the surviving
record set for a set of test keys. What becomes easy to test because of the
pattern is correctness of latest-value-wins logic in downstream consumers,
since the test can control exactly which records survive compaction and
assert the consumer's derived state matches. What becomes harder is testing
compaction timing itself, because the log cleaner's scheduling is a
background, best-effort process not designed for deterministic testing, so
tests that need to assert compaction has definitely happened by a given
point must either poll for the expected outcome with a timeout or use
Kafka's internal test utilities that allow forcing a synchronous cleaner
run, and tests that assume compaction happens synchronously with a produce
call will be flaky.

A separate, important test class is tombstone-window testing, verifying that
a consumer paused for longer than `delete.retention.ms` and then resumed
still behaves correctly, or at minimum fails in a detected, alerted way
rather than silently. This requires either manipulating `delete.retention.ms`
down to a small value in the test environment to make the window
reproducible in test time, or explicitly documenting the assumption as an
operational runbook item rather than a unit test, since simulating a
multi-day consumer pause in a fast test suite is rarely practical.

## 16. Observability signals

Per-partition dirty ratio, exposed via Kafka's JMX metrics under
`kafka.log:type=LogCleanerManager`, specifically the
`uncleanable-partitions-count` and per-log dirty ratio gauges. A dirty ratio
that stays permanently high, near or above 1.0, on a topic that should be
compacting regularly is the primary signal that the cleaner is falling
behind, whether due to insufficient cleaner threads, an I/O throttle set too
low, or an unbounded key space defeating compaction.

Log cleaner throughput and time-per-pass metrics, exposed under
`kafka.log:type=LogCleaner`, including bytes read and time spent per cleaner
run. A healthy compacted topic shows periodic, bounded-duration cleaner
passes; a failing one shows either passes that never complete, or a cleaner
thread that appears stuck on the same partition across multiple monitoring
windows, both of which are visible directly in these metrics without
needing to inspect application behavior at all.

Total log size per partition over time, from the standard `kafka.log.Log`
size metrics or from disk usage per partition directory. For a well-behaved
compacted topic this should plateau roughly proportional to distinct key
count once the initial write volume has been compacted at least once; a
partition whose size keeps growing linearly with produce throughput, with no
plateau, is the clearest external symptom of the unbounded-key-space misuse
case described above, and this signal is independent of and complementary to
the dirty ratio metric, since a partition can show a low dirty ratio,
meaning the cleaner is keeping up, while its overall size still grows if
compaction genuinely has nothing to free.

Consumer lag on compacted topics, via standard consumer group lag
monitoring. Because a slow consumer is the entity most at risk of missing a
tombstone before it is cleaned, tracking consumer lag against
`delete.retention.ms`, specifically alerting when a consumer group's lag
duration approaches or exceeds the tombstone retention window, is a
targeted, pattern-specific signal that generic lag monitoring does not
surface unless it is explicitly configured to compare lag against this
threshold.

## 17. Security and privacy implications

Log compaction interacts directly with data deletion and retention
requirements, which makes it security and privacy relevant in a way plain
storage compaction is not. When a system relies on log compaction as its
mechanism for honoring a deletion request, for example a right-to-be-forgotten
request under privacy regulation, several properties of the pattern matter
directly.

A tombstone is not an immediate erasure. Between the moment a tombstone is
written and the moment `delete.retention.ms` elapses and the cleaner
actually removes the underlying data, the previous value for that key
remains physically present on disk in whichever segments have not yet been
compacted, and it remains present in any replicas that have not yet applied
the compaction pass, and in any consumer-side materialized copies that have
not yet processed the tombstone. A team relying on log compaction to satisfy
a hard deletion deadline must account for this lag explicitly, both the
`delete.retention.ms` window and the time it takes for every replica and
every downstream consumer's local copy to actually process the tombstone,
which is not bounded by Kafka itself and depends on the slowest consumer in
the system.

Compaction does not touch replication, so a deletion is only complete once it
has propagated to every broker replica of the partition and every
downstream materialized view derived from the topic; treating the topic
alone, on a single broker, as the boundary of what counts as deleted is an
incomplete mental model in a replicated deployment.

Backups and disaster recovery snapshots taken of the underlying log storage,
or of any downstream sink that copies the raw, uncompacted segments before
compaction has run, can retain the pre-tombstone value independently of the
live Kafka cluster's own state, and log compaction provides no mechanism to
reach into or purge such external copies; any compliance process that
depends on data deletion must treat these copies as a separate concern
entirely outside what log compaction can guarantee.

Where the data being compacted contains sensitive fields, the fact that
older values are eventually physically removed from disk is a genuine
privacy positive relative to an uncompacted, permanently retained log, but
the specific point at which the removal actually resolves must be
documented and tested, not assumed, especially since the default
`delete.retention.ms` of twenty-four hours was chosen by the Kafka project to
accommodate slow consumers, not to satisfy any particular regulatory
deletion deadline, and a team with stricter deletion timing requirements
must explicitly tune it rather than rely on the default.

## Code examples

Three languages, each implementing the same minimal compaction pass. the
build_offset_map plus single-sweep algorithm from the ASCII diagram in
dimension 6, applied to an in-memory list of records rather than to disk
segments, so the mechanics are visible without a running Kafka broker. all
three were run directly and produced the identical surviving record set,
offset 2 key k2, offset 4 key k3 tombstone, offset 5 key k4, offset 6 key k1,
confirming the algorithm is language independent. Java is omitted here
because the shape is identical to the TypeScript and Go forms, a map plus a
single filtering pass, and adds no distinct idiom worth a fourth listing.

### TypeScript

Compiled with tsc strict mode, target es2020, module commonjs, and run under
Node, producing the expected four surviving records with the tombstone for
k3 retained, since its age of two offsets is below the 100 offset grace
window used in this example.

```typescript
interface Rec {
  offset: number;
  key: string;
  value: string | null;
}

function compact(records: Rec[], tombstoneGrace: number, now: number): Rec[] {
  const lastOffsetForKey = new Map<string, number>();
  for (const r of records) {
    lastOffsetForKey.set(r.key, r.offset);
  }

  const survivors: Rec[] = [];
  for (const r of records) {
    const isLatest = lastOffsetForKey.get(r.key) === r.offset;
    if (!isLatest) continue;
    if (r.value === null && now - r.offset >= tombstoneGrace) continue;
    survivors.push(r);
  }
  return survivors;
}

const log: Rec[] = [
  { offset: 0, key: "k1", value: "v1" },
  { offset: 1, key: "k3", value: "v2" },
  { offset: 2, key: "k2", value: "v3" },
  { offset: 3, key: "k1", value: "v4" },
  { offset: 4, key: "k3", value: null },
  { offset: 5, key: "k4", value: "v5" },
  { offset: 6, key: "k1", value: "v6" },
];

for (const r of compact(log, 100, 6)) {
  console.log(r.offset, r.key, r.value);
}
```

### Python

Run directly with python3, using a dataclass for the record shape and a
loop identical in structure to the TypeScript version, to keep the two
directly comparable line for line.

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class Record:
    offset: int
    key: str
    value: Optional[str]


def compact(records: list[Record], tombstone_grace: int, now: int) -> list[Record]:
    last_offset_for_key: dict[str, int] = {}
    for r in records:
        last_offset_for_key[r.key] = r.offset

    survivors: list[Record] = []
    for r in records:
        is_latest = last_offset_for_key[r.key] == r.offset
        if is_latest:
            if r.value is None and now - r.offset >= tombstone_grace:
                continue
            survivors.append(r)
    return survivors


if __name__ == "__main__":
    log = [
        Record(0, "k1", "v1"),
        Record(1, "k3", "v2"),
        Record(2, "k2", "v3"),
        Record(3, "k1", "v4"),
        Record(4, "k3", None),
        Record(5, "k4", "v5"),
        Record(6, "k1", "v6"),
    ]
    result = compact(log, tombstone_grace=100, now=6)
    for r in result:
        print(r.offset, r.key, r.value)
```

### Go

Run with go run. Go has no nullable value type for a plain string, so the
tombstone is represented with a pointer to string set to nil, which is the
idiomatic Go equivalent of Kafka's own null-valued tombstone record.

```go
package main

import "fmt"

type Rec struct {
	Offset int
	Key    string
	Value  *string
}

func compact(records []Rec, tombstoneGrace int, now int) []Rec {
	lastOffsetForKey := make(map[string]int)
	for _, r := range records {
		lastOffsetForKey[r.Key] = r.Offset
	}

	var survivors []Rec
	for _, r := range records {
		if lastOffsetForKey[r.Key] != r.Offset {
			continue
		}
		if r.Value == nil && now-r.Offset >= tombstoneGrace {
			continue
		}
		survivors = append(survivors, r)
	}
	return survivors
}

func strp(s string) *string { return &s }

func main() {
	log := []Rec{
		{0, "k1", strp("v1")},
		{1, "k3", strp("v2")},
		{2, "k2", strp("v3")},
		{3, "k1", strp("v4")},
		{4, "k3", nil},
		{5, "k4", strp("v5")},
		{6, "k1", strp("v6")},
	}
	for _, r := range compact(log, 100, 6) {
		if r.Value == nil {
			fmt.Println(r.Offset, r.Key, "<nil>")
		} else {
			fmt.Println(r.Offset, r.Key, *r.Value)
		}
	}
}
```

## 18. References

1. Apache Kafka Project. "Kafka Documentation, section 5.6, Log Compaction."
   Official Apache Kafka documentation site, design section.
   https://kafka.apache.org/documentation/#compaction
   Content corroborated via Confluent's mirrored design documentation,
   verified 2026-08-02.
2. Confluent, Inc. "Log Compaction." Confluent Documentation, Kafka Design
   guide.
   https://docs.confluent.io/kafka/design/log_compaction.html
   Verified 2026-08-02. Source for the tombstone mechanics, dirty ratio and
   `min.cleanable.dirty.ratio` behavior, log cleaner thread throttling, and
   the four ordering and offset stability guarantees cited in sections 3, 7,
   and 10.
3. Kreps, Jay. "The Log." LinkedIn Engineering Blog, December 2013,
   republished by Confluent under the subtitle "What every software engineer
   should know about real-time data's unifying abstraction." Cited for the
   changelog and stream-table duality framing referenced in section 2.
4. Kleppmann, Martin. Designing Data-Intensive Applications. O'Reilly Media,
   2017. Chapter 3, "Storage and Retrieval," section on log-structured
   storage engines and compaction. Cited for the general compaction concept
   in log-structured storage and its relationship to LSM trees, referenced
   in sections 1, 3, and 8.
5. Confluent, Inc. "Kafka Streams Architecture, Fault Tolerance." Confluent
   Documentation.
   https://docs.confluent.io/platform/current/streams/architecture.html
   Describes changelog topics as the mechanism for state store recovery,
   verified 2026-08-02, cited in sections 2, 7, and 9 for the Kafka Streams
   production use case.
6. Apache Kafka Project. "Kafka Connect User Guide, Configuring Internal
   Topics." Apache Kafka Documentation.
   https://kafka.apache.org/documentation/#connect_running
   Describes the config, offset, and status internal topics created with
   `cleanup.policy=compact`, verified 2026-08-02, cited in section 9.
7. Debezium Community. "Debezium Connector Topic Auto-Create Configuration."
   Debezium Documentation.
   https://debezium.io/documentation/reference/stable/configuration/topic-auto-create-config.html
   Verified 2026-08-02, cited in section 9 for the recommendation of
   `cleanup.policy=compact` on change event topics used as materialized
   caches.
8. Confluent, Inc. "Materialized Views in ksqlDB." Confluent Platform
   Documentation.
   https://docs.confluent.io/platform/current/ksqldb/concepts/materialized-views.html
   Verified 2026-08-18, cited in section 9 for tables being backed by
   compacted changelog topics.
9. Facebook, Inc. "RocksDB Wiki, Compaction." RocksDB GitHub Wiki.
   https://github.com/facebook/rocksdb/wiki/Compaction
   Verified 2026-08-02. Source for the leveled, universal, and FIFO
   compaction strategy descriptions and their write and space amplification
   trade-offs cited in sections 8, 12, and 13.
10. Apache Software Foundation. "Apache Cassandra Documentation, Compaction."
    Apache Cassandra Documentation, Operating section.
    https://cassandra.apache.org/doc/latest/cassandra/managing/operating/compaction/index.html
    Verified 2026-08-02. Source for the existence and naming of
    SizeTieredCompactionStrategy, LeveledCompactionStrategy, and
    TimeWindowCompactionStrategy cited in section 8.
11. Apache Kafka Project. Kafka issue tracker, historical reference to the
    key-based log cleaning proposal commonly cited by the community as
    KAFKA-46, predating the formal documentation of log compaction in
    Kafka's design guide. Cited in section 1 for lineage; the specific issue
    text was not independently re-verified for this entry and the claim is
    presented as commonly cited project history rather than a directly
    fetched primary source, flagged here for transparency.
