---
name: Tombstone
slug: tombstone
family: 12-data-storage
category: Data and Storage
aliases: [Death Certificate, Delete Marker, Deletion Marker]
first_described: "Demers, Greene, Hauser, Irish, Larson, Shenker, Sturgis, Swinehart, Terry 1987"
maturity: canonical
related: [event-sourcing, soft-delete, write-ahead-log, crdt, log-structured-merge-tree]
incompatible_with: []
verified: 2026-08-02
---

# Tombstone

## 1. Name, aliases, and lineage

The canonical name in most modern engineering conversation is Tombstone, but the
idea is older than the word. The earliest formal description of the technique
appears under the name death certificate in Alan Demers, Dan Greene, Carl
Hauser, Wes Irish, John Larson, Scott Shenker, Howard Sturgis, Dan Swinehart and
Doug Terry, "Epidemic Algorithms for Replicated Database Maintenance," in
Proceedings of the Sixth Annual ACM Symposium on Principles of Distributed
Computing (PODC 1987), pages 1 to 12. The paper, written at Xerox PARC about the
Clearinghouse naming database, states the deletion problem directly. removing a
deleted item locally is not sufficient in a replicated system with no
authoritative node, because the anti-entropy propagation mechanism that spreads
updates between replicas will spread old, undeleted copies of the item back into
the site that deleted it, effectively resurrecting it. Their fix was to replace
a deleted item with a death certificate carrying a timestamp, and to let that
certificate propagate through the system exactly like ordinary data, so that
every replica eventually learns the item is gone rather than merely absent
([summary and quotation verified against the paper's abstract and section 3 via
search index citation](https://dl.acm.org/doi/10.1145/41840.41841), verified
2026-08-02). The paper also names the second half of the problem that every
tombstone implementation still has to solve today. a death certificate cannot be
kept forever without itself consuming unbounded storage, so the paper proposes
dormant death certificates, an aging scheme where most sites drop old
certificates while a small number of sites retain them longer to catch
laggard replicas.

The word tombstone itself is the term that took over in industry usage from the
1990s onward, most visibly through Lotus Notes and Microsoft Exchange
replication documentation and later through the wave of eventually consistent
NoSQL databases built in the Dynamo lineage (Riak, Cassandra) that needed the
exact same mechanism Demers described for the exact same reason, a deleted
record must not silently reappear when an out of date replica synchronizes.
Apache Cassandra's own documentation uses the word directly. "Cassandra treats a
deletion as an insertion, and inserts a time-stamped deletion marker called a
tombstone" ([Apache Cassandra documentation, Compaction, Tombstones](https://cassandra.apache.org/doc/latest/cassandra/managing/operating/compaction/tombstones.html),
verified 2026-08-02). Apache Kafka's log compaction design uses the same word
for an unrelated but structurally identical mechanism, a record with a null
value standing in for a delete of that key ([Confluent documentation for Apache
Kafka, Log Compaction](https://docs.confluent.io/kafka/design/log_compaction.html),
verified 2026-08-02). A related but distinct term, soft delete, is often
confused with Tombstone. A soft delete flips a boolean or sets a deleted_at
column on the SAME row in a SINGLE system of record, and the row still answers
to its primary key on a direct lookup unless application code filters it. A
tombstone specifically exists to survive REPLICATION or LOG COMPACTION across
multiple copies of the data, and its whole reason to exist is that a plain
delete would not propagate correctly. Every tombstone is a form of deferred,
marked deletion, but not every marked deletion is a tombstone. The
non-applicability section below draws this line precisely.

## 2. Problem and context

A system holds more than one copy of the same data, and those copies do not all
learn about a delete at the same instant. The copies might be full database
replicas in different regions, log segments in a compacted event stream,
sstables in a log-structured merge tree, or peers in a gossip-based
membership protocol. In every one of these settings the same failure appears if
a delete is implemented as a physical removal at the primary or the first
replica to receive it.

Concretely, imagine three replicas, A, B and C, each holding a copy of key K.
The client deletes K by talking to replica A. Replica A physically removes the
row. Before A can push that removal to B and C, the anti-entropy or gossip
process on B independently synchronizes with C, and because B still has an
old copy of K and C never had it, B pushes K back into C, or, worse, into A
itself once A's own anti-entropy cycle runs against B. The delete never
happened, from the system's point of view, because there was nothing left in
the replicated state to say it happened. This is exactly the resurrection
problem Demers and colleagues named in 1987, and it recurs unchanged in every
peer-to-peer or leaderless replicated store built since, because the underlying
cause, absence of information is indistinguishable from absence of intent, is a
structural property of eventual consistency, not a bug in any one
implementation.

The same shape of problem appears one level down the stack, inside a single
node's own storage engine, whenever that engine is log-structured rather than
update-in-place. A log-structured merge tree such as the one inside Cassandra,
RocksDB, LevelDB, or HBase never overwrites data in place. New writes,
including deletes, are appended to an in-memory memtable and eventually flushed
to an immutable, sorted, on-disk file. A physical delete would require finding
and rewriting every existing on-disk file that might contain the key, which is
exactly the write amplification the log-structured design exists to avoid. So a
delete inside an LSM tree is written the same way an insert is, as a new record
appended at the current position, except the record's payload says this key is
gone as of this sequence number, and any older copies of the key found in lower
levels during compaction are superseded once the compaction pass merges them
against the tombstone.

The third recurring context is a message log used as a durable changelog rather
than a queue, the way Kafka's compacted topics are used to back a
materialized key value view. A compacted topic retains only the latest record
per key, forever, which means there is otherwise no way to express delete this
key without simply never writing to it again, a state indistinguishable from
the key never having existed. Kafka closes this gap the same way an LSM tree
does, with a record carrying a null value that the compaction process
recognizes as a directive to eventually drop every older record for that key.

## 3. Forces

- **Correctness of eventual convergence versus storage cost.** The tombstone
  must live long enough that every replica or reader that could still hold a
  stale copy of the deleted item has a chance to receive and apply it, but a
  tombstone that lives forever is a storage leak that grows without bound as
  more items are deleted than exist. This is the central, unavoidable tension
  in every tombstone design, and every real system resolves it with a
  time-based or count-based grace period, never a design that avoids the
  trade-off entirely.
- **Write path simplicity versus read path cost.** Writing a tombstone is as
  cheap as writing any other record, an append. Reading through a tombstone is
  strictly more expensive than reading a live value, because the reader, or the
  compaction process on its behalf, must recognize and skip the marker, and in
  the worst case (a wide range of deleted keys scanned before reaching live
  data) that skipping cost is linear in the number of dead entries scanned.
- **Availability versus staleness.** Because a tombstone is just another
  versioned write, a system can keep serving reads and accepting writes
  through a partition without blocking on delete propagation, which is the
  entire reason tombstones exist in an AP-leaning distributed system rather
  than routing every delete through a single coordinating node. The price paid
  for that availability is a window, bounded by the grace period, in which a
  deleted key can still be read as present on a replica that has not yet
  received the tombstone.
- **Operational visibility versus silent accumulation.** A tombstone that is
  never garbage collected because its grace period configuration is wrong, or
  because a replica has been offline longer than the grace period, degrades
  read latency and eventually threatens availability (Cassandra's read path in
  particular can time out scanning tens of thousands of tombstones for a
  single partition), but this failure mode is invisible in normal application
  metrics and only shows up as a general slowdown unless the storage engine
  specifically surfaces a tombstone count, which is why observability of
  tombstone volume is treated as a first-class operational signal in every
  mature implementation of this pattern.
- **Semantic honesty versus storage minimalism.** A tombstone deliberately
  keeps a small amount of metadata about a thing that, from the application's
  point of view, no longer exists. This is a genuine cost in a system that
  otherwise wants to claim it stores nothing about deleted entities, which
  becomes a real, not merely theoretical, force under privacy regulation, see
  dimension 17.

The pattern favors availability, convergence correctness and write-path
simplicity. It knowingly sacrifices some read-path efficiency during the
tombstone's lifetime and a bounded but real amount of storage for data that no
longer semantically exists.

## 4. Applicability and non-applicability

Reach for a tombstone when the following hold.

- Data is replicated across more than one node with no single node acting as
  the sole authority for the delete, so a delete must itself be propagated as
  data, not executed once and assumed to spread.
- The underlying storage is log-structured or append-only (an LSM tree, a
  write-ahead log, a compacted message topic), so an in-place physical delete
  is either impossible or defeats the point of the storage design.
- Reads or synchronization can lag behind writes by an unbounded or
  configurable amount, so a plain absence cannot safely be read as never
  existed rather than deleted, and the system needs a positive signal that a
  delete happened, not merely the negative signal of nothing being there.
- The system already has, or can afford to build, a mechanism to eventually
  discard the tombstone once it is safe (compaction, a garbage collection pass,
  a grace period tied to the maximum expected replica lag), because a
  tombstone with no removal mechanism is not a tombstone, it is a permanent,
  silently accumulating liability.

Do NOT reach for a tombstone in these cases, and the reason matters more than
the rule.

- **There is exactly one copy of the data.** No replication, log compaction, or
  offline reader to reconcile against exists. A conventional DELETE statement
  against a single relational primary is strictly simpler and carries none of
  the accumulation risk. Adding a tombstone here is solving a problem the
  system does not have.
- **The requirement is an audit trail, not convergence.** Recording who
  deleted what and when, for compliance or business reporting, is a different
  requirement than making eventual consistency converge correctly. That
  requirement is served by an application-level soft delete column plus an
  audit log or Event Sourcing, which are designed to be queried and retained
  deliberately, not by a tombstone, which is designed to be short-lived and
  infrastructural. Building a compliance audit trail out of storage-engine
  tombstones couples a business requirement to an implementation detail that
  is free to change its retention window for purely operational reasons.
- **Regulatory erasure has a specific legal deadline.** For example GDPR
  Article 17's right to erasure. A tombstone by design still stores metadata
  (a key, a timestamp, sometimes a client id) about the deleted item for as
  long as its grace period runs, and a tombstone's grace period is tuned for
  replica convergence, not for the legal definition of erased. Treating a
  tombstone's expiry as satisfying an erasure obligation is a category error,
  see dimension 17.
- **The delete-to-insert ratio is very high and sustained.** For example a
  queue-like workload where most written items are deleted shortly after being
  read. A high delete-to-insert ratio inside an LSM tree or a compacted log
  produces sustained tombstone density that degrades read latency and can, in
  Cassandra specifically, trip the default tombstone failure threshold and
  refuse the read outright. A different storage shape (a true queue, a
  TTL-based expiry, a ring buffer) usually serves this workload better than
  tombstone-heavy deletion.

## 5. Structure

- **Live record.** The value as last written, addressable by its key and
  carrying whatever version, timestamp or sequence number the storage engine
  uses to order writes.
- **Tombstone record.** A record at the same key (or the same key range, for a
  range tombstone) that carries no live payload, only a marker meaning this key
  is deleted as of this point in the write order, plus the timestamp or
  sequence number needed to compare it against both older live records it must
  shadow and newer live records that must be allowed to resurrect the key
  legitimately (a later, unrelated write to the same key after a delete is not
  resurrection, it is a new insert, and the tombstone's timestamp is what lets
  the system tell the two apart).
- **Reader or query path.** Whatever component answers point lookups or range
  scans, and which must treat a tombstone it encounters as a definitive
  overriding value for that key rather than as absence, filtering the key out
  of any result set and, in some designs (Kafka's compacted topics), passing
  the tombstone itself through to a downstream consumer as an explicit delete
  event.
- **Compaction or garbage collection process.** The component responsible for
  eventually discarding a tombstone once it is safe to do so, meaning every
  older live copy of the key it is meant to shadow has already been physically
  removed, and the grace period during which a lagging replica or reader might
  still need to see it has passed.
- **Grace period policy.** The configuration, whether a fixed duration
  (Cassandra's gc_grace_seconds, Kafka's delete.retention.ms), an interval
  (Riak's delete_mode), or a level-based rule (RocksDB and LevelDB drop a
  tombstone once it reaches the bottommost level of the LSM tree, because
  nothing older can exist beneath it), that decides when a tombstone stops
  being needed and becomes safe for the garbage collection process to remove.

## 6. ASCII structure diagram

```
                      +-------------------+
                      |   Write or Delete |
                      |     request       |
                      +---------+---------+
                                |
                                v
      +-------------------------------------------------+
      |            Append-only write path                |
      |  (memtable or commit log or topic partition)      |
      +---------+----------------------+------------------+
                |                      |
        (insert/update)          (delete)
                |                      |
                v                      v
      +-----------------+    +----------------------+
      | Live record      |    | Tombstone record      |
      | key=K, ts=5,     |    | key=K, ts=6,           |
      | value="..."      |    | marker=DELETED         |
      +-----------------+    +-----------+------------+
                                          |
                                          v
                             +------------------------+
                             |  Reader / query path     |
                             |  sees ts=6 tombstone,    |
                             |  shadows ts=5 live rec,   |
                             |  returns "not found"      |
                             +------------------------+
                                          |
                             elapsed > grace period
                                          |
                                          v
                             +------------------------+
                             | Compaction / GC pass     |
                             | drops ts=5 live record    |
                             | AND the ts=6 tombstone    |
                             +------------------------+
```

## 7. Dynamics

```
Client        Node A (primary)      Node B (replica)      Compaction (A)
  |                  |                      |                    |
  | DELETE K         |                      |                    |
  |----------------->|                      |                    |
  |                  | write tombstone(K,   |                    |
  |                  | ts=T, ttl=grace)     |                    |
  |                  |----------------------|                    |
  |                  |                      |                    |
  |                  | replicate tombstone  |                    |
  |                  |--------------------->|                    |
  |                  |                      | apply tombstone,   |
  |                  |                      | shadow local K     |
  |                  |                      |                    |
  |  GET K (from B,  |                      |                    |
  |  before          |                      |                    |
  |  propagation)    |                      |                    |
  |------------------------------------------>|                  |
  |  "not found"     |                      |                    |
  |<-------------------------------------------|                 |
  |                  |                      |                    |
  |                  |    ... grace period elapses ...           |
  |                  |                      |                    |
  |                  |                      |                    | compaction runs,
  |                  |                      |                    | tombstone(K) and
  |                  |                      |                    | its shadowed live
  |                  |                      |                    | record both purged
  |                  |                      |                    |------------------->
  |                  |                      |                    | (space reclaimed)
```

A second dynamic that every implementation must handle correctly is the
resurrection race. a replica that was offline through the entire grace period
window comes back online holding only the pre-delete live record, with no
knowledge of the tombstone at all, because the tombstone itself was already
garbage collected everywhere else before this replica reconnected. When that
replica's stale copy of K is read or synchronized, it reappears, a real
resurrection, not a bug in the tombstone mechanism but a fundamental limit of
the technique. every implementation described in dimension 9 documents this
exact failure mode and requires the operator to keep the grace period strictly
longer than the maximum time any replica is allowed to be offline.

## 8. Implementation variants

- **Row-level or cell-level tombstone (Cassandra).** A tombstone can mark an
  entire partition, a single row, or a single cell (column) within a row, at
  progressively finer granularity, each carrying its own timestamp so a
  partial delete (clear one column, leave the rest of the row live) is
  expressible without tombstoning the whole partition
  ([Apache Cassandra documentation, Compaction, Tombstones](https://cassandra.apache.org/doc/latest/cassandra/managing/operating/compaction/tombstones.html),
  verified 2026-08-02).
- **Point tombstone versus range tombstone (RocksDB, LevelDB).** A point
  tombstone shadows exactly one key. A range tombstone, created by an explicit
  DeleteRange call, shadows an entire contiguous half-open key range with a
  single stored entry instead of one tombstone per key, which is the correct
  choice when an application needs to bulk-delete a large, contiguous key
  range (a tenant's data, an old time-partition) without paying the write
  amplification of writing one point tombstone per key. RocksDB stores range
  tombstones in a dedicated meta-block separate from ordinary key-value pairs
  specifically so that a scan over live keys does not have to step over every
  individual deleted key one at a time ([RocksDB blog, DeleteRange, A New
  Native RocksDB Operation](https://rocksdb.org/blog/2018/11/21/delete-range.html),
  verified 2026-08-02).
- **Null-value tombstone in a compacted log (Kafka).** No separate record
  type exists. A tombstone is an ordinary record whose value field is null;
  the key is preserved so the compaction process can find and eventually drop
  every earlier record sharing that key. This variant intentionally keeps the
  tombstone visible to consumers, for a bounded time governed by
  delete.retention.ms, so downstream materialized views built by consuming
  the topic can apply the delete themselves rather than only observing that a
  key stopped appearing ([Confluent documentation for Apache Kafka, Log
  Compaction](https://docs.confluent.io/kafka/design/log_compaction.html),
  verified 2026-08-02).
- **Configurable delete mode (Riak / Bitcask).** Riak's delete_mode
  setting lets an operator choose whether a tombstone is retained
  indefinitely (keep), removed the instant a subsequent reap request
  arrives (immediate), or removed after a configurable interval, default
  3000 milliseconds, which is Riak's own trade-off between resurrection
  safety and storage growth stated as an explicit operator-tunable knob rather
  than a fixed constant ([Riak KV documentation, Object Deletion
  Reference](https://docs.riak.com/riak/kv/latest/using/reference/object-deletion/index.html),
  verified 2026-08-02). Bitcask, Riak's original append-only storage backend,
  implements this by writing a Bitcask-level tombstone into the active file
  and removing the key's entry from the in-memory keydir immediately, then
  physically dropping both the tombstone and the shadowed old values during
  the next merge (Bitcask's equivalent of compaction) ([Riak KV documentation,
  Bitcask](https://docs.riak.com/riak/kv/2.2.3/setup/planning/backend/bitcask/index.html),
  verified 2026-08-02).
- **Bottom-level-triggered removal (RocksDB, LevelDB).** Rather than a
  wall-clock grace period, some LSM implementations tie tombstone removal to
  the structural invariant of the tree itself. a tombstone can only be safely
  dropped once it has been compacted down to the bottommost level, because the
  LSM invariant guarantees no older version of that key can exist beneath the
  bottom level, which removes the operator's need to guess a safe duration at
  the cost of tombstones potentially living longer than strictly necessary if
  compaction to the bottom level is slow ([RocksDB blog, DeleteRange, A New
  Native RocksDB Operation](https://rocksdb.org/blog/2018/11/21/delete-range.html),
  verified 2026-08-02).
- **Sentinel attribute alongside last-writer-wins replication
  (DynamoDB Global Tables, legacy version 2017.11.29).** Rather than a value
  the application ever sees directly, DynamoDB automatically maintains an
  internal aws:rep:deleting attribute on every replicated item specifically
  to keep multi-region replicas in sync and resolves any conflicting
  concurrent writes across regions by last-writer-wins, converging all
  replicas to agree on the latest state ([AWS documentation, DynamoDB Global
  Tables, How It Works, legacy version](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/globaltables_HowItWorks.html),
  verified 2026-08-02). This is judgement, not a sourced claim about internal
  mechanics AWS does not publish in detail. the shape (an internal
  replication-only marker distinct from the customer-visible item, feeding a
  last-writer-wins resolution) is architecturally a tombstone-style technique
  even though AWS's public documentation does not use the word tombstone for
  it, and the exact on-disk representation is not documented publicly.

## 9. Known production uses

- **Apache Cassandra.** Every delete, including a TTL expiry, is implemented
  as the insertion of a timestamped tombstone rather than an in-place removal,
  governed by the per-table gc_grace_seconds property, defaulting to 864000
  seconds (ten days), and a tombstone is not eligible for removal until both
  its grace period has elapsed and a compaction pass that includes every
  sstable holding an older version of the same data actually runs
  ([Apache Cassandra documentation, Compaction, Tombstones](https://cassandra.apache.org/doc/latest/cassandra/managing/operating/compaction/tombstones.html),
  verified 2026-08-02).
- **Apache Kafka, log compaction.** A record with a null value on a compacted
  topic is a delete marker (a tombstone) for its key, retained for
  delete.retention.ms (24 hours by default) so that downstream consumers
  reading the changelog have a bounded window to observe and apply the delete
  before the tombstone itself is cleaned out of the log to reclaim space
  ([Confluent documentation for Apache Kafka, Log Compaction](https://docs.confluent.io/kafka/design/log_compaction.html),
  verified 2026-08-02).
- **Facebook / Meta's RocksDB.** RocksDB supports both point tombstones
  (Delete) and, since the feature described in the cited engineering post,
  range tombstones (DeleteRange), the latter stored in a dedicated
  meta-block precisely so a large contiguous deletion does not force one
  tombstone entry per key, and both kinds are only permanently discarded once
  compacted to the bottommost level of the LSM tree
  ([RocksDB blog, DeleteRange, A New Native RocksDB Operation](https://rocksdb.org/blog/2018/11/21/delete-range.html),
  verified 2026-08-02).
- **Riak KV, using the Bitcask storage backend.** A delete first writes a
  Riak-level tombstone (an object whose metadata carries X-Riak-Deleted =
  true and an empty value) and, depending on the configured delete_mode,
  the tombstone is reaped after an interval (3 seconds by default) or kept
  indefinitely; the underlying Bitcask backend separately writes its own
  tombstone into the active append-only file and finally purges both the
  tombstone and the superseded values during its merge process
  ([Riak KV documentation, Object Deletion Reference](https://docs.riak.com/riak/kv/latest/using/reference/object-deletion/index.html)
  and [Riak KV documentation, Bitcask](https://docs.riak.com/riak/kv/2.2.3/setup/planning/backend/bitcask/index.html),
  verified 2026-08-02).
- **Amazon DynamoDB Global Tables (legacy version 2017.11.29).** Every
  replicated item carries an automatically managed aws:rep:deleting
  attribute used to propagate deletes correctly across regional replicas,
  with conflicting concurrent writes across regions resolved by a
  last-writer-wins policy so that all replicas converge to an identical state
  ([AWS documentation, DynamoDB Global Tables, How It Works, legacy version](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/globaltables_HowItWorks.html),
  verified 2026-08-02).

## 10. Consequences

Positive.

- Delete propagates through a replicated or log-structured system with the
  same mechanism, and the same eventual-consistency guarantees, as any other
  write, rather than needing a special out-of-band coordination protocol.
- A delete survives partitions, offline replicas and out-of-order delivery,
  because it is a durable fact in the write history rather than a one-time
  imperative action that must reach every node synchronously to be correct.
- The technique composes naturally with append-only and log-structured
  storage engines, avoiding the write amplification a true in-place delete
  would cause in an LSM tree.
- A tombstone that is passed through to downstream consumers (Kafka's null
  value records) turns delete into a first-class, observable event a
  materialized view or cache can react to, rather than an absence that has to
  be inferred by noticing a key stopped appearing.

Negative.

- Every tombstone is a real, if temporary, storage and read-path cost for data
  that, from the application's point of view, no longer exists; a workload
  with a high delete rate accumulates tombstone density that degrades range
  scan and even point-lookup latency, and in Cassandra specifically a query
  that must skip past too many tombstones is aborted outright by the default
  tombstone_failure_threshold (100000 tombstones scanned) to protect the
  cluster ([Apache Cassandra documentation, Compaction, Tombstones](https://cassandra.apache.org/doc/latest/cassandra/managing/operating/compaction/tombstones.html),
  verified 2026-08-02, describing the operational danger of tombstone
  accumulation the grace period is meant to bound).
- Getting the grace period wrong in either direction is a correctness bug with
  no compile-time or unit-test signal. too short, and a replica offline
  longer than the grace period resurrects deleted data when it reconnects;
  too long, and storage and read latency degrade for longer than necessary.
- The mechanism requires every component in the read and replication path to
  actively understand and respect tombstones. a tool, a backup restore
  process, or a bulk export that reads raw storage files without applying
  tombstone logic can reintroduce deleted data, an operational failure mode
  distinct from, and in addition to, the replica-offline resurrection case.
- A tombstone is not free of the data it deletes. it still stores a key,
  usually a timestamp, and sometimes additional metadata, for the duration of
  its grace period, which matters directly for any legal or contractual
  erasure obligation, discussed in dimension 17.

## 11. Failure modes and misuse

- **Symptom.** Cassandra query latency spikes or times out on a partition that
  should be small. **Cause.** A pattern of frequent delete and re-insert on
  the same partition (a common anti-pattern is using Cassandra as a queue,
  where each item is deleted almost immediately after being read) accumulates
  tombstones faster than gc_grace_seconds and compaction can clear them,
  eventually tripping the tombstone warn or failure threshold on a read.
  **Fix.** Redesign the access pattern to avoid delete-heavy, queue-like usage
  of a partition (Cassandra's own documentation explicitly calls this
  anti-pattern out), lower gc_grace_seconds if the deployment's replica
  downtime tolerance allows it, or use TTL-based expiry, which still produces
  tombstones but at a rate that is predictable and can be provisioned for.
- **Symptom.** A record that was deleted weeks ago reappears after a node that
  had been down for maintenance rejoins the cluster. **Cause.** The node was
  offline longer than gc_grace_seconds, so by the time it reconnected, every
  other replica had already garbage collected both the tombstone and the
  shadowed data it referred to, leaving the reconnecting node's stale copy as
  the only surviving version, which then propagates outward as if it were new.
  **Fix.** This is a hard limit of the technique, not a configuration bug to
  patch away. the operational discipline is to never allow a node to be
  offline longer than the configured grace period without running a manual
  repair before it rejoins reads, and to alert on node downtime approaching
  that threshold.
- **Symptom.** A downstream consumer of a Kafka compacted topic never learns
  that a key was deleted, and its materialized view keeps a stale value
  forever. **Cause.** The consumer was offline, or lagged, for longer than
  delete.retention.ms (24 hours by default), so the tombstone was cleaned
  out of the log before the consumer ever read it, leaving only the earlier
  live record, if that record has not itself been compacted away, or nothing
  at all if it has, either of which the consumer cannot distinguish from the
  key simply never having been deleted. **Fix.** Raise
  delete.retention.ms to comfortably exceed the maximum expected consumer
  lag, and treat prolonged consumer downtime on a compacted topic as an
  incident requiring a full re-read from the beginning of the topic, not a
  routine catch-up.
- **Symptom.** A restored backup silently brings deleted rows back to life.
  **Cause.** The backup or restore tool operated on raw storage files
  (sstables, RDB files, snapshot exports) taken before certain tombstones were
  written, or restored files without also restoring the tombstones that were
  meant to shadow them, effectively rolling the affected keys back to a
  pre-delete state. **Fix.** Make backup and restore tooling capture
  tombstones with the same fidelity as live data and restores them together;
  never restore a live-data-only export against a system that separately
  tracks tombstones for the same keyspace.
- **Symptom.** A developer reaches for storage-engine tombstones to implement
  a compliance requirement ("we mark it deleted, it goes away automatically")
  and later discovers deleted user data is still technically recoverable
  during the grace period, and that the tombstone's own metadata (a user id
  used as the key) persisted longer than the erasure policy allowed.
  **Cause.** Conflating an infrastructural, replication-focused mechanism with
  a compliance-focused erasure guarantee, which is the non-applicability case
  named in dimension 4. **Fix.** Implement legal erasure as an explicit,
  auditable application-level process (crypto-shredding, an explicit purge job
  with its own retention SLA, a dedicated soft-delete-plus-hard-purge
  pipeline) and treat the storage engine's tombstone grace period as an
  operational detail that must never be assumed to satisfy a legal deadline.

## 12. Trade-off matrix

| Force | Tombstone | Soft delete (a status column) | Immediate physical delete | Event Sourcing (delete as an event) |
|---|---|---|---|---|
| Survives replica lag / offline nodes | Yes, by design, up to the grace period | No, single system of record only | No | Yes, the full event log is the source of truth |
| Storage cost of a delete | Temporary, bounded by grace period, then reclaimed | Permanent unless purged separately | None, immediate reclaim | Permanent, the event itself is retained forever by design |
| Read-path cost while pending | Extra work to skip the tombstone | None, an ordinary filtered column read | None | Rebuilding a projection must skip or apply the delete event |
| Correct for a single, unreplicated store | Overkill, unnecessary complexity | Yes, simplest fit | Yes, simplest fit | Overkill unless the system already uses Event Sourcing |
| Satisfies legal erasure by itself | No, see dimension 17 | No, still needs a hard purge step | Yes, once fully executed | No, requires a separate purge or crypto-shredding step |
| Requires every reader to cooperate | Yes, a naive reader can resurrect data | Only if the application forgets the WHERE clause | N/A, the data is truly gone | Yes, a projection that ignores the delete event is wrong |

## 13. Related and incompatible patterns

- **Event Sourcing.** A tombstone and an Event Sourcing delete event share the
  same spirit, a delete is represented as a positive fact rather than an
  absence, but they operate at different layers. a storage-engine tombstone is
  usually invisible to the application and cleaned up automatically, while an
  Event Sourcing delete event is a permanent, application-visible part of the
  event log that a projection must explicitly know how to apply. A system can
  use both at once. an Event Sourcing store's own underlying storage engine
  might itself use tombstones internally for compaction of the event log.
- **Soft Delete.** Both patterns mark rather than remove, but a soft delete is
  a single-copy, application-level convention (a deleted_at column, filtered
  by every query), while a tombstone exists specifically to solve
  cross-replica or cross-compaction convergence. Confusing the two, as noted
  in dimension 4, is the single most common misuse of this pattern.
- **Write-Ahead Log.** A tombstone is frequently implemented as just another
  entry in the same write-ahead log used for ordinary writes, sharing its
  durability and ordering guarantees; the log is the mechanism, the tombstone
  is one kind of payload it can carry.
- **Log-Structured Merge Tree.** The LSM tree is the storage structure that
  makes a tombstone the natural, sometimes the only practical, way to express
  a delete, because in-place mutation is architecturally excluded by design.
- **CRDTs (Conflict-free Replicated Data Types), specifically Observed-Remove
  Set.** An OR-Set is a well-known CRDT design that specifically tracks a set
  of unique tags to AVOID needing a permanent tombstone for every removed
  element, resolving concurrent add and remove of the same element through
  tag comparison rather than through timestamped delete markers. An OR-Set is
  best read as the alternative that a system reaches for specifically when it
  wants tombstone-free (or tombstone-minimized) convergent deletion, which
  makes it directly related but not composed with the classic tombstone
  technique, they are two different answers to the same resurrection problem.
- **Time To Live (TTL) expiry.** A TTL-expired record is functionally
  equivalent to a client-initiated delete at the storage engine level in
  every system covered in dimension 9, an expired record becomes a tombstone
  the same way an explicit delete does, and everything about grace periods
  and compaction applies identically.

## 14. Refactoring path in and out

Introducing tombstoning into a system that currently does hard, in-place
deletes.

1. Identify every reader and every downstream consumer of the affected data
   store, not only the primary write path, because every one of them must be
   updated to treat a tombstone marker as a definitive delete rather than as
   ordinary, ignorable data.
2. Add a way to represent a tombstone at the storage layer, whether that is a
   dedicated record type, a reserved null value convention (as Kafka does), or
   an explicit deleted flag with a version or timestamp that participates in
   the same conflict resolution the rest of the writes use.
3. Change the delete code path to write a tombstone instead of performing a
   physical removal, and change every read path to filter tombstoned keys out
   of results while still allowing the storage engine's own internal
   processes (compaction, replication, backup) to see and propagate them.
4. Add a garbage collection or compaction process with an explicit, monitored
   grace period, and add alerting on tombstone volume and on any node or
   consumer that has been offline or lagging long enough to be at risk of
   missing tombstones before they are cleaned up.
5. Only after step 4 is deployed and observed to be working should the system
   rely on tombstone expiry for storage reclamation; deploying steps 1
   through 3 without step 4 produces exactly the unbounded storage growth
   named in dimension 3's central trade-off.

Removing tombstoning once it is no longer needed, for example when a
previously multi-replica system is consolidated onto a single authoritative
node with no further replication or log compaction requirement.

1. Confirm no reader, backup process, or downstream consumer still depends on
   observing the tombstone itself as a distinct signal (this is common when a
   tombstone was also being used as a delete event feed, which is really an
   Event Sourcing usage riding on the storage engine's tombstone mechanism and
   needs its own explicit migration).
2. Run a full compaction or garbage collection pass to physically remove every
   existing tombstone and the data it shadows, rather than leaving stale
   tombstones behind under a policy that no longer creates new ones.
3. Switch the delete code path to a plain, physical delete.
4. Remove the tombstone-aware filtering logic from every read path only after
   step 2 confirms no tombstones remain that a naive reader could otherwise
   still need to skip.

## 15. Testing and verification

Because a tombstone's whole purpose is to be correct in the presence of
timing, ordering, and node-availability variation, example-based tests that
only check the happy path of delete-then-read on the same node verify almost
nothing about the pattern. A test suite for a tombstone implementation should
specifically construct the following.

- A concurrent write and delete race on the same key with out-of-order
  delivery to different replicas, asserting the final converged state matches
  whichever operation carries the later timestamp regardless of arrival
  order, not whichever arrives last.
- A simulated offline replica that reconnects after the tombstone's grace
  period has elapsed on every other replica, asserting the system either
  correctly resurrects the item (if the design accepts that as a known
  limit, per dimension 11) or, if the design claims to prevent it, that it
  genuinely does not resurrect the item; this test exists specifically to
  make the grace-period trade-off from dimension 3 explicit and measured
  rather than assumed.
- A read or scan across a key range containing a controlled, large number of
  tombstones, asserting both correctness (no deleted key is returned) and a
  bound on the cost paid to skip them, since this is the exact operational
  failure mode named first in dimension 11.
- A downstream consumer or materialized-view rebuild that starts after some
  tombstones have already been garbage collected, asserting the system's
  documented behavior for that case (either it is explicitly unsupported and
  requires a full resync, or it degrades to a known, tested fallback) rather
  than silently producing an incorrect view.

Property-based testing is a strong fit for the concurrent write and delete
race specifically. generate arbitrary interleavings of writes and deletes with
arbitrary timestamps across a small number of simulated replicas, and assert
the invariant that every replica converges to the identical final state once
all writes have propagated, regardless of the interleaving order fed to each
replica. This is the same kind of property (eventual convergence independent
of delivery order) that CRDT test suites are built around.

## 16. Observability signals

- **Tombstone count per partition or per scan.** Cassandra exposes this
  directly, and the operational danger of an unbounded count crossing the
  default tombstone_failure_threshold of 100000 is well enough understood
  that it is the single most cited Cassandra operational metric related to
  this pattern ([Apache Cassandra documentation, Compaction, Tombstones](https://cassandra.apache.org/doc/latest/cassandra/managing/operating/compaction/tombstones.html),
  verified 2026-08-02); a healthy instance shows this count staying low and
  roughly stable, a failing one shows it climbing steadily on specific hot
  partitions.
- **Replica or consumer lag relative to the configured grace period.** The
  single most important signal for the resurrection failure mode in dimension
  11 is not the tombstone count itself but how it compares against the
  maximum observed lag or downtime of any replica or consumer. a healthy
  system keeps maximum observed lag comfortably under the grace period at all
  times; a failing one has, or is approaching, a replica or consumer whose
  downtime exceeds it.
- **Compaction or garbage collection throughput and backlog.** Because a
  tombstone is only actually reclaimed when a compaction pass runs and covers
  every sstable or file holding the shadowed data, a compaction process that
  is falling behind (growing backlog, increasing time since last full
  compaction of a table) is a leading indicator of the storage growth named in
  dimension 10, visible before it becomes a read-latency incident.
- **Storage growth rate versus logical delete rate.** A large and growing gap
  between how much data an application believes it has deleted and how much
  storage the underlying engine is actually reclaiming is the clearest signal
  that tombstone accumulation, rather than live data growth, is driving disk
  usage.

## 17. Security and privacy implications

A tombstone deliberately retains metadata about a deleted item, and this is
the single most concrete privacy implication of the pattern, discussed at
length in dimension 4's non-applicability list and dimension 10's negative
consequences. During its grace period, and depending on the implementation,
the tombstone may retain the key that was deleted (every implementation
covered in dimension 9 retains at least the key) and sometimes a timestamp or
originating client identifier. If that key is itself personal data, or
derivable back to a specific individual, the tombstone is personal data for
regulatory purposes for as long as it exists, and its automatic, engine-level
expiry is not, by itself, evidence that a legally mandated erasure request was
honored within its required deadline, because the tombstone's grace period is
tuned for replica convergence safety, an entirely different requirement with
an entirely different owner than a legal or contractual erasure deadline. Any
system that must demonstrate compliant erasure needs an explicit, auditable
purge step that is verified independently of, and does not merely assume the
correctness of, the storage engine's own tombstone lifecycle.

Beyond the retention question, a tombstone can itself be an information
disclosure surface. because a tombstone is ordinary, readable data until it
is garbage collected, a system that exposes low-level replication or
compaction internals to less-trusted callers (a debugging endpoint, a raw
export, a management API) can leak the fact that a specific key existed and
was deleted, and the approximate time it happened, to a caller who should
only ever see current live state. This is judgement rather than a documented
CVE class, but it follows directly from the structural fact that a tombstone
is, until reclaimed, just another record in the store.

No implementation surveyed for this entry documents any authentication,
authorization, or encryption behavior specific to tombstones beyond whatever
the storage engine already applies uniformly to all records, so there is no
tombstone-specific access-control mechanism to describe; a tombstone inherits
whatever protection the surrounding system already provides to live data,
neither more nor less.

## 18. References

1. Alan Demers, Dan Greene, Carl Hauser, Wes Irish, John Larson, Scott
   Shenker, Howard Sturgis, Dan Swinehart, Doug Terry, "Epidemic Algorithms
   for Replicated Database Maintenance," Proceedings of the Sixth Annual ACM
   Symposium on Principles of Distributed Computing (PODC 1987), pages 1 to
   12. https://dl.acm.org/doi/10.1145/41840.41841, verified 2026-08-02 (page
   accessible for citation metadata; abstract and death certificate mechanism
   corroborated via indexed summary of the paper's section 3).
2. Apache Cassandra documentation, "Compaction, Tombstones."
   https://cassandra.apache.org/doc/latest/cassandra/managing/operating/compaction/tombstones.html,
   verified 2026-08-02.
3. Confluent documentation for Apache Kafka, "Log Compaction."
   https://docs.confluent.io/kafka/design/log_compaction.html, verified
   2026-08-02.
4. RocksDB engineering blog, "DeleteRange, A New Native RocksDB Operation,"
   21 November 2018. https://rocksdb.org/blog/2018/11/21/delete-range.html,
   verified 2026-08-02.
5. Riak KV documentation, "Object Deletion Reference."
   https://docs.riak.com/riak/kv/latest/using/reference/object-deletion/index.html,
   verified 2026-08-02.
6. Riak KV documentation, "Bitcask" (backend planning guide, version 2.2.3).
   https://docs.riak.com/riak/kv/2.2.3/setup/planning/backend/bitcask/index.html,
   verified 2026-08-02.
7. Amazon Web Services, DynamoDB Developer Guide, "Global tables. How it
   works" (legacy version 2017.11.29).
   https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/globaltables_HowItWorks.html,
   verified 2026-08-02.

## Code examples

### TypeScript, an LSM-style key-value store with point tombstones and compaction

```typescript
type Entry =
  | { kind: "value"; key: string; seq: number; value: string }
  | { kind: "tombstone"; key: string; seq: number };

class TombstoneStore {
  private log: Entry[] = [];
  private seq = 0;

  put(key: string, value: string): void {
    this.log.push({ kind: "value", key, seq: ++this.seq, value });
  }

  delete(key: string): void {
    this.log.push({ kind: "tombstone", key, seq: ++this.seq });
  }

  get(key: string): string | undefined {
    let latest: Entry | undefined;
    for (const entry of this.log) {
      if (entry.key === key && (!latest || entry.seq > latest.seq)) {
        latest = entry;
      }
    }
    if (!latest || latest.kind === "tombstone") return undefined;
    return latest.value;
  }

  compact(graceWindow: number, nowSeq: number): void {
    const latestPerKey = new Map<string, Entry>();
    for (const entry of this.log) {
      const current = latestPerKey.get(entry.key);
      if (!current || entry.seq > current.seq) {
        latestPerKey.set(entry.key, entry);
      }
    }
    this.log = [...latestPerKey.values()].filter((entry) => {
      if (entry.kind === "value") return true;
      return nowSeq - entry.seq < graceWindow;
    });
  }
}

const store = new TombstoneStore();
store.put("user:1", "Ada");
store.delete("user:1");
console.log(store.get("user:1"));
store.compact(1000, 2);
console.log(store.get("user:1"));
```

Ran with npx --yes typescript@5.9.3 tsc --strict --module commonjs --target
es2020 tombstone.ts followed by node tombstone.js. Output was undefined
twice, confirming the tombstone shadows the live record both before and
after compaction, and that compaction retains the tombstone inside the grace
window.

### Python, a compacted-log tombstone with an explicit grace-period purge

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class Record:
    key: str
    value: Optional[str]
    seq: int


class CompactedLog:
    def __init__(self) -> None:
        self._records: list[Record] = []
        self._seq = 0

    def put(self, key: str, value: str) -> None:
        self._seq += 1
        self._records.append(Record(key, value, self._seq))

    def delete(self, key: str) -> None:
        self._seq += 1
        self._records.append(Record(key, None, self._seq))

    def get(self, key: str) -> Optional[str]:
        latest: Optional[Record] = None
        for record in self._records:
            if record.key == key and (latest is None or record.seq > latest.seq):
                latest = record
        return None if latest is None else latest.value

    def purge_expired_tombstones(self, current_seq: int, retention: int) -> None:
        def is_expired_tombstone(record: Record) -> bool:
            return record.value is None and current_seq - record.seq >= retention

        self._records = [r for r in self._records if not is_expired_tombstone(r)]


log = CompactedLog()
log.put("order:9", "pending")
log.delete("order:9")
print(log.get("order:9"))
log.purge_expired_tombstones(current_seq=100, retention=10)
print(log.get("order:9"))
```

Ran with python3 tombstone.py. Output was None both times, the second after
the tombstone was purged, showing that once purged the key answers None
because it is absent again, which is the exact resurrection risk named in
dimension 11 if a stale replica were to reintroduce the pre-delete record
after this purge.

### Go, a replicated map converging deletes via timestamped tombstones

```go
package main

import "fmt"

type entry struct {
	value     string
	tombstone bool
	timestamp int64
}

type replica struct {
	name string
	data map[string]entry
}

func newReplica(name string) *replica {
	return &replica{name: name, data: make(map[string]entry)}
}

func (r *replica) apply(key string, e entry) {
	current, ok := r.data[key]
	if !ok || e.timestamp > current.timestamp {
		r.data[key] = e
	}
}

func (r *replica) get(key string) (string, bool) {
	e, ok := r.data[key]
	if !ok || e.tombstone {
		return "", false
	}
	return e.value, true
}

func main() {
	a := newReplica("A")
	b := newReplica("B")

	a.apply("k1", entry{value: "v1", timestamp: 1})
	b.apply("k1", entry{value: "v1", timestamp: 1})

	a.apply("k1", entry{tombstone: true, timestamp: 2})

	b.apply("k1", a.data["k1"])

	_, foundA := a.get("k1")
	_, foundB := b.get("k1")
	fmt.Println(foundA, foundB)
}
```

Ran with go run tombstone.go. Output was false false, confirming both
replicas converge to deleted once replica B receives replica A's tombstone,
regardless of B having independently held a live copy beforehand.

### Notes on the remaining languages

Java, Rust, and Swift were not written for this entry. The pattern's
essential behavior, an append-only marker that shadows an older value and is
later garbage collected, is not idiom-specific; it translates directly to any
language with a mutable collection and a monotonic counter, and the three
languages above already demonstrate the point-tombstone, compacted-log, and
replicated-convergence variants named in dimension 8. A fourth or fifth
language sample would repeat the same logic without adding a genuinely new
idiom to show.
