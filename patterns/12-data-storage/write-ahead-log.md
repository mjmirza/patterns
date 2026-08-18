---
name: Write-Ahead Log
slug: write-ahead-log
family: 12-data-storage
category: Data and Storage
aliases: [WAL, Redo Log, Commit Log, Transaction Log]
first_described: "Gray 1978, formalized by Mohan et al. 1992 (ARIES)"
maturity: canonical
related: [event-sourcing, leader-followers, leader-follower-architecture, change-data-capture]
incompatible_with: []
verified: 2026-08-02
---

# Write-Ahead Log

## 1. Name, aliases, and lineage

The canonical name is Write-Ahead Log, almost always shortened to WAL in code,
configuration files, and conversation. The rule the name describes is simple to
state and hard to violate by accident once it is built correctly. A change to
a data page is recorded in a log entry, and that log entry is durable on
persistent storage, before the change to the data page itself is allowed to
reach disk. The log is written ahead of the data, hence the name.

The earliest systematic description of the write-ahead rule as a named
principle for database recovery is Jim Gray's 1978 IBM research report on
transaction processing techniques, which stated the log-write rule as a
prerequisite for undo and redo recovery (Jim Gray, "Notes on Data Base
Operating Systems", IBM Research Report RJ2188, 1978, later republished as a
chapter in "Operating Systems, an Advanced Course", Springer-Verlag, 1978).
The idea itself predates the name. IBM's System R project in the mid-1970s
already used a log-based recovery scheme, but Gray's report is the first
widely cited formal statement of the write-ahead constraint as a rule a
recovery manager must obey, not an implementation detail added later.

The rule was made precise and given its most cited formal treatment in C.
Mohan, Don Haderle, Bruce Lindsay, Hamid Pirahesh, and Peter Schwarz, "ARIES,
a Transaction Recovery Method Supporting Fine-Granularity Locking and Partial
Rollbacks Using Write-Ahead Logging", ACM Transactions on Database Systems,
Vol. 17, No. 1, March 1992, pages 94 to 162
(https://dl.acm.org/doi/10.1145/128765.128770, verified 2026-08-02). ARIES is
not a synonym for write-ahead logging, it is a specific recovery algorithm
built on top of the write-ahead rule, adding log sequence numbers on every
page, a dirty page table, a transaction table, and a three-pass recovery
procedure, analysis, redo, undo. Most production relational databases that
claim ARIES-style recovery, including IBM Db2 and Microsoft SQL Server,
implement a variant of this algorithm rather than the write-ahead rule alone
(Wikipedia, "Algorithms for Recovery and Isolation Exploiting Semantics",
https://en.wikipedia.org/wiki/Algorithms_for_Recovery_and_Isolation_Exploiting_Semantics,
verified 2026-08-02).

**Redo Log** is Oracle's name for the same structure and appears throughout
Oracle documentation and DBA vocabulary. it names the recovery direction the
log is primarily used for in that product, rolling forward, or redoing,
committed changes after a crash. **Commit Log** is the name Kafka's own log
implementation and Cassandra both use, and in the distributed-systems and
message-broker world "commit log" and "write-ahead log" are used
interchangeably to describe an append-only, sequentially written, durability
structure, even though a message broker's commit log also serves as the
primary data store rather than a secondary durability record for a separate
data structure. **Transaction Log** is Microsoft SQL Server's name and also a
generic term used across the industry. All four names refer to the same
underlying mechanism. log first, mutate second, and never let the second step
outrun the first on stable storage.

## 2. Problem and context

A database, or any system that mutates state on disk, has two competing needs
that are difficult to satisfy with the same physical write. It must apply
changes to its actual data structures (B-tree pages, hash buckets, in-place
records) so that reads see current values, and it must survive a crash without
losing committed work or corrupting the on-disk structures that were mid-write
when the crash happened.

If a system writes changes directly into its data pages and the process or
the machine dies partway through a multi-page update, the data files are left
in an inconsistent state with no record of what the transaction intended.
Half of a B-tree split might be on disk, half not. A record might show a debit
with no corresponding credit. There is no way to tell, from the data files
alone, whether the crash happened before or after a given change was supposed
to complete, and no way to finish an interrupted operation or roll it back
cleanly.

Random in-place writes to data pages are also expensive relative to their
size. A single logical change, updating one row, can require writing a full 8
kilobyte page, an index page, and sometimes several index pages, at whatever
physical location those pages happen to live on disk, which on rotating media
means seeks, and even on flash media means a page-level write amplification
cost. Waiting for each of those scattered writes to be durable, on every
transaction commit, before telling the client the transaction succeeded, would
make commit latency proportional to random I/O rather than sequential I/O.

Write-ahead logging solves both problems with one structure. The log is a
strictly append-only sequence of entries, each entry describing a change that
either already happened to the in-memory representation of the data, or is
about to. Because the log is append-only, writing to it is always a sequential
write to the end of a file, which is dramatically cheaper than a scattered
random write on almost every storage medium, and syncing that one sequential
write to stable storage is the only I/O a transaction's commit has to wait
for. The actual data pages can be updated in memory and flushed to disk later,
in whatever order and whatever batching is efficient, because if the process
crashes before those pages reach disk, the log holds enough information to
redo, or undo, exactly what was supposed to happen.

## 3. Forces

**Durability versus commit latency.** The log must be fsynced, or the storage
equivalent, before a transaction is acknowledged as committed, or a
"committed" transaction can vanish on crash. That fsync is the largest cost
of a commit, and everything else, group commit, log batching, separate log
devices, exists to push that cost down without weakening the durability
guarantee.

**Sequential write throughput versus random write cost.** The log gets its
speed advantage specifically because it is append-only. Any design decision
that turns log writes into anything other than a strict sequential append,
log compaction done synchronously in the write path, multiple writers
contending for the same log file, seeking backward to patch an earlier
record, erodes the core performance property the pattern exists to provide.

**Recovery time versus steady-state write cost.** A system that never
checkpoints, never flushes dirty data pages and trims the log, has a fast
steady state but an unbounded log that grows forever and an unbounded
recovery time after a crash, because recovery has to replay everything since
the beginning of time. A system that checkpoints aggressively bounds recovery
time but pays extra I/O and CPU in steady state to do the checkpointing.

**Space and retention versus operational needs.** The log is also the raw
material for replication, point-in-time recovery, and change data capture in
many systems, per Dimension 9 below. Retaining more log than the minimum
needed for local crash recovery serves those needs but costs disk space and,
in some systems, makes the log itself a thing that needs its own retention
and cleanup policy, which is a second source of operational failure.

**Single-writer simplicity versus write concurrency.** A single append-only
log file naturally serializes writes, which is simple to reason about and easy
to make durable, but it is also a serialization point. Systems that need
higher write concurrency either shard the log (partitioned WALs, per-partition
commit logs as in Kafka), or accept the log as the intentional single point of
ordering for the guarantees they want, a single Raft log per replicated state
machine, deliberately, because the log's total order is the mechanism that
gives the replicas a consistent view.

## 4. Applicability and non-applicability

Reach for a write-ahead log when the following hold.

- The system must guarantee that an acknowledged write survives a crash of the
  process, and the underlying storage does not already provide that guarantee
  for the system's own data structures. The classic case is a database or
  key-value store implementing its own on-disk B-tree, hash table, or LSM
  tree.
- Commit latency matters and the workload includes many small transactions.
  Batching those transactions' durability requirement into sequential log
  writes, rather than scattered writes to the affected data pages, is the
  standard way to get both durability and throughput.
- The system needs crash recovery that restores exactly the set of committed
  transactions, no more and no less, including transactions that were
  in-flight, partially applied, at crash time.
- Replication, point-in-time recovery, or change data capture is a
  requirement, and the log's ordered, complete record of every change is a
  natural source to build those features on top of, rather than inventing a
  second mechanism to capture the same information.
- A distributed consensus protocol, Raft or Multi-Paxos, needs a durable,
  ordered record of proposed operations that every replica appends to before
  applying, so that a crashed and restarted node can recover to the state the
  cluster agreed on.

Do NOT reach for a write-ahead log under the following conditions.

- The data is genuinely disposable or fully reconstructible from another
  authoritative source on restart, a pure cache, a materialized view that can
  be rebuilt from its source table, most application-level in-memory caches.
  Adding a WAL here adds write latency and operational surface for a
  durability guarantee nothing needs.
- The underlying storage engine already gives you the durability guarantee at
  the layer you are writing to. Writing your own WAL on top of a database that
  already write-ahead-logs your inserts, for example hand-rolling a "recovery
  log" table inside PostgreSQL, duplicates the mechanism the database is
  already providing and doubles your durability-related I/O for no additional
  safety.
- The workload is read-heavy with rare, low-value writes where a stale or
  even briefly lost write is an acceptable business risk, and the operational
  cost of managing log files, checkpoints, and log-space alarms outweighs the
  benefit. A simple synchronous write plus periodic snapshot may be enough.
- A single-node embedded use case where the entire dataset comfortably fits
  a design that can be made crash-safe by simpler means, such as an
  atomic-rename-based snapshot write, write a new file, fsync, rename over the
  old one. This trades some write throughput for a much simpler recovery
  story and is a legitimate choice for small configuration stores, not a
  worse write-ahead log.
- Your storage medium already provides append-only, ordered, durable
  semantics as its primary abstraction, an existing commit-log-based message
  broker, an existing durable queue, and you are tempted to build a second WAL
  underneath it to be safe. That is redundant durability for the same
  failure mode, and it is a maintenance and consistency liability, not a
  safety net.

## 5. Structure

- **Log record.** The atomic unit written to the log. Minimally carries a log
  sequence number (LSN), a transaction identifier, an operation type (insert,
  update, delete, commit, abort, checkpoint), and enough payload to redo, and
  usually undo, the change. Either the full new value (physical logging), a
  description of the operation and its arguments (logical logging), or a
  combination (physiological logging, the ARIES approach, which logs
  page-level physical changes described logically enough to be idempotent).
- **Log Sequence Number (LSN).** A monotonically increasing identifier for
  every log record, used to order records, to record on each data page which
  LSN last modified it (so recovery knows whether a page already reflects a
  given log record), and to mark checkpoint and truncation boundaries.
- **Log buffer.** An in-memory area where log records accumulate before being
  flushed to stable storage. Batches multiple transactions' log records into
  fewer, larger sequential writes (group commit).
- **Log writer / flusher.** The component that appends the log buffer to the
  log file on disk and issues the fsync (or platform equivalent) that makes
  the write durable. This is the component whose latency directly gates
  transaction commit latency.
- **Buffer pool / page cache.** The in-memory copies of data pages that get
  mutated first, with the corresponding log record already durable. Dirty
  pages are flushed to the data files asynchronously, governed by the
  write-ahead rule. a dirty page may only be written to disk after its
  corresponding log record (identified by LSN) is durable in the log.
- **Checkpoint.** A periodic operation that records which log records have
  already been reflected in the on-disk data files, via a checkpoint record
  and a dirty-page table, so recovery does not need to replay the entire log
  from the beginning, only from the last checkpoint forward.
- **Recovery manager.** The component that runs on restart after a crash,
  reading the log from the last checkpoint (or the beginning, if no checkpoint
  exists), reapplying committed changes that had not yet reached the data
  files (redo), and reversing changes from transactions that never committed
  (undo), using the log's own undo information.
- **Log segment / rotation manager.** In systems that split the log into
  multiple files (segments), the component responsible for creating new
  segments, and reclaiming or archiving old ones once they are no longer
  needed for recovery or replication.

## 6. ASCII structure diagram

```
+---------------------------------------------------------------+
|                          Application                          |
+----------------------------+------------------------------+---+
                              | write(txn, change)
                              v
                    +-------------------+
                    |     Log Buffer    |  (in memory)
                    +---------+---------+
                              | flush + fsync, ahead of the
                              | corresponding data page write
                              v
              +-----------------------------+
              |     Write-Ahead Log file     |
              |  (append-only, sequential)   |
              |  LSN 100. BEGIN  txn 7       |
              |  LSN 101. UPDATE txn 7 ...   |
              |  LSN 102. COMMIT txn 7       |
              +---------------+---------------+
                              |
                              | recovery replays from here
                              v
       +----------------------------------------------------+
       |                  Recovery Manager                   |
       |  reads log, redoes committed, undoes uncommitted     |
       +----------------------------------------------------+

+-------------------+        (async, governed by the WAL rule.
|    Buffer Pool     |         a page may only reach disk after
|  (dirty data pages)| ----->  its highest-LSN change is durable
+---------+-----------+        in the log)
          |
          v
   +-------------+       +-------------------+
   | Data Files   |       |  Checkpoint file   |
   | (B-tree,     |       | (last durable LSN, |
   |  heap, etc.) |       |  dirty page table)|
   +-------------+       +-------------------+
```

## 7. Dynamics

The write path, for a single transaction that updates a data page.

```
1. Application issues UPDATE within transaction T.
2. Engine locates the affected page in the buffer pool
   (reads it from disk into memory if not already cached).
3. Engine constructs a log record describing the change,
   assigns it the next LSN, appends it to the in-memory log
   buffer, and stamps the data page's pageLSN with this LSN.
4. Engine applies the change to the in-memory copy of the
   page. The page is now "dirty" (differs from what is on
   disk) but the disk copy is untouched.
5. Application issues COMMIT for T.
6. Engine appends a COMMIT log record for T to the log buffer,
   then forces (fsyncs) the log buffer up to and including
   that COMMIT record to stable storage. THIS FSYNC IS THE
   POINT AT WHICH THE COMMIT BECOMES DURABLE.
7. Engine acknowledges the commit to the application. The
   dirty data page written in step 4 may still be sitting
   only in memory at this point, that is expected and safe.
8. Asynchronously, at some later time, the buffer pool's
   background writer flushes the dirty page to the data
   file. Before doing so it confirms the page's pageLSN is
   less than or equal to the log's durable LSN (the
   write-ahead rule enforced at flush time, not only at
   commit time).
```

The recovery path, on restart after an unclean shutdown.

```
1. Recovery manager locates the most recent checkpoint record
   in the log, which records a starting LSN and a dirty page
   table snapshot from the time of the checkpoint.
2. ANALYSIS PASS. Scan forward from the checkpoint to the end
   of the log, rebuilding the transaction table (which
   transactions were active) and the dirty page table (which
   pages might be out of date on disk).
3. REDO PASS. Scan forward again from the earliest LSN found
   necessary in the dirty page table, reapplying every logged
   change whose LSN is greater than the page's on-disk pageLSN,
   for EVERY transaction, committed or not. This restores the
   exact state the database was in at the moment of the crash,
   including the effects of transactions that were mid-flight.
4. UNDO PASS. For every transaction found active (not committed,
   not aborted) at crash time, walk backward through that
   transaction's log records using the log itself, reversing
   each change, and writing compensation log records (CLRs)
   describing the undo so that a second crash during undo does
   not repeat work already undone.
5. System is now in a consistent state and accepts new
   transactions.
```

This three-pass shape (analysis, redo, undo) is specific to the ARIES
algorithm cited in Dimension 1. simpler write-ahead logging implementations
(SQLite's WAL mode, for instance) use a different, simpler recovery procedure
because their engine does not support fine-grained concurrent transactions
sharing the same log the way a full RDBMS does, but every implementation
preserves the core ordering. log record durable before data page durable,
and replay the log to recover.

## 8. Implementation variants

**Physical logging.** The log record stores the literal before-and-after bytes
of the affected disk block or region. Simple to apply during redo (just copy
the bytes back), but records can be large, and logging every byte of a large
page for a one-field change wastes log space and I/O.

**Logical logging.** The log record stores the operation and its logical
arguments, for example "increment account 42 by 100", rather than the
physical bytes changed. Compact, but replaying it correctly during redo
requires the operation to be safely re-executable, which is difficult to
guarantee if the operation's effect depends on runtime state that might have
changed, an index structure whose exact physical layout after the operation
depends on concurrent activity.

**Physiological logging (ARIES's approach).** Physical at the page level,
each log record affects exactly one page, but logical within the page, the
record describes what changed on the page in a way that does not depend on
the page's exact byte layout beyond identifying the page. This is the
approach used by the systems in Dimension 9 that implement ARIES-style
recovery, and it is the standard choice for a production RDBMS because it
balances redo simplicity against log size.

**Separate WAL versus data-embedded log.** Most relational databases keep the
WAL in files entirely separate from the data files, PostgreSQL's `pg_wal`
directory, distinct from the tablespace files. SQLite's WAL mode instead
keeps changed pages in a separate `-wal` file next to the main database file,
and readers can read either the main file or the newer version in the WAL
file depending on a shared index, which is a design chosen specifically to
let readers and a single writer proceed concurrently without blocking each
other (D. Richard Hipp, "Write-Ahead Logging", SQLite documentation,
https://www.sqlite.org/wal.html, verified 2026-08-02).

**Log as the primary store versus log as a secondary durability record.** In
a classical RDBMS the WAL is a secondary structure, the data of record lives
in the B-tree pages, and the log exists only to make those pages' updates
crash-safe. In log-structured storage engines (LSM trees, and message brokers
like Kafka) the append-only log IS the primary durable store, and other
structures (memtables, SSTables, consumer offsets) are built on top of, or
read from, the log rather than the log being a redundant shadow of them. This
distinction matters because it changes the retention question entirely, a
classical WAL can be truncated once its changes are checkpointed to the data
files, while a log-as-primary-store system has to retain the log, or a
compacted form of it, indefinitely, because it is the data.

**Group commit.** Rather than fsyncing the log after every individual
transaction's commit record, the log writer batches the commit records of
several transactions that arrive close together in time and issues one fsync
covering all of them, then acknowledges all the batched transactions at once.
This trades a small amount of added latency for individual transactions
(waiting a few milliseconds for the batch window) for a large gain in overall
throughput, because fsync cost is roughly constant per call regardless of how
much data it flushes, so amortizing it across many transactions divides that
fixed cost by the batch size.

**Segmented, rotating logs.** Rather than one ever-growing file, the log is
split into fixed-size segment files. Old segments can be archived,
compressed, or deleted once no longer needed for recovery or replication,
without having to rewrite a single enormous file. Kafka's partition logs and
PostgreSQL's WAL segment files (16 MiB by default) both use this shape.

**Language-idiomatic notes.** Write-ahead logging is not usually something an
application author writes in isolation from a specific storage engine's
internals, it is almost always found either as a feature of a database you
are using, in which case there is no idiom to choose, you configure it, or
as a component you are implementing as part of building a storage engine or a
consensus module. In Go, etcd's `go.etcd.io/etcd/server/v3/storage/wal`
package is the most widely reused standalone WAL implementation, built for
Raft log persistence and reused by other Go projects that need a durable,
ordered append log (etcd project repository,
https://github.com/etcd-io/etcd/tree/main/server/storage/wal, verified
2026-08-02). In Rust, on-disk log crates typically favor an explicit,
type-checked record framing so that partial or torn writes at the tail of the
file are detectable and truncated during recovery, an approach that maps
naturally onto Rust's preference for making partial or invalid states
unrepresentable once parsed.

## 9. Known production uses

- **PostgreSQL.** Every transaction that modifies data is protected by
  PostgreSQL's write-ahead log, stored as segment files in the `pg_wal`
  directory. PostgreSQL's own documentation states the core rule directly,
  that changes to data files "must be written only after those changes have
  been logged, that is, after log records describing the changes have been
  flushed to permanent storage", and that this both provides crash recovery
  and, because "the WAL file is written sequentially... the cost of syncing
  the WAL is much less than the cost of flushing the data pages", explains
  why WAL reduces the number of disk writes required for durable commits
  (PostgreSQL 18 Documentation, Chapter 28, "Reliability and the Write-Ahead
  Log", https://www.postgresql.org/docs/current/wal-intro.html,
  verified 2026-08-02). PostgreSQL's streaming replication and point-in-time
  recovery features are both built directly on shipping and replaying this
  same log.
- **SQLite.** SQLite's WAL mode, enabled with `PRAGMA journal_mode=WAL`,
  appends changed pages to a separate `-wal` file instead of overwriting the
  main database file in place, allowing readers and a single writer to
  proceed concurrently because "readers read the original database file while
  writers append to the WAL file, so readers and writers do not block each
  other". The setting is persisted in the database file header so future
  connections automatically use WAL mode once set (SQLite documentation,
  "Write-Ahead Logging", https://www.sqlite.org/wal.html, verified
  2026-08-02).
- **Apache Kafka.** Kafka's own reference documentation describes each
  partition as "an ordered, immutable sequence of records that is
  continually appended to, a structured commit log", describing the
  append-only log as the persistence layer for messages, not a secondary
  structure protecting some other data store (Apache Kafka documentation,
  "4. Design", Log section, https://kafka.apache.org/documentation/#log,
  verified 2026-08-02). Kafka's own internal write path is itself described
  in the project and in independent analysis as write-ahead-log-based,
  replicas append records to their local log before a record is considered
  committed by the ISR (Wang et al., "Building a Replicated Logging System
  with Apache Kafka", Proceedings of the VLDB Endowment, Vol. 8, No. 12,
  2015, https://www.vldb.org/pvldb/vol8/p1654-wang.pdf, verified 2026-08-02).
- **etcd (and, through it, Kubernetes).** etcd persists every proposed Raft
  log entry to a write-ahead log on disk (the `wal` package) before it is
  considered part of the replicated log, so that a restarted etcd node can
  recover the exact sequence of entries it had accepted, which is what makes
  etcd usable as Kubernetes's cluster state store (etcd project repository,
  package `server/storage/wal`,
  https://github.com/etcd-io/etcd/tree/main/server/storage/wal, verified
  2026-08-02).
- **IBM Db2 and Microsoft SQL Server (ARIES lineage).** Both products
  implement recovery managers descended from, or directly implementing, the
  ARIES algorithm from Dimension 1, using a write-ahead transaction log as
  the durability and recovery backbone (Wikipedia, "Algorithms for Recovery
  and Isolation Exploiting Semantics",
  https://en.wikipedia.org/wiki/Algorithms_for_Recovery_and_Isolation_Exploiting_Semantics,
  verified 2026-08-02, summarizing the ARIES paper cited in Dimension 1 and
  its adoption).

## 10. Consequences

Positive.

- Converts the expensive part of durability, waiting for a write to be safe
  on stable storage, into a cheap, sequential, appendable operation, which is
  much faster than waiting for the corresponding random writes to the
  actual data structures.
- Gives a precise, mechanical recovery procedure. replay the log since the
  last checkpoint, and the system reaches exactly the state it should be in,
  no matter where in a multi-step operation the crash happened.
- Decouples "when a write is safe" from "when a write is reflected in the
  main data structures", which lets the system batch, reorder, and defer data
  page flushes for efficiency without weakening the durability guarantee
  clients observe.
- Provides, as a side effect, a complete, ordered, replayable history of
  every change, which is exactly the raw material replication, point-in-time
  recovery, and change data capture need, so those features can be built on
  the log that already exists rather than requiring their own separate
  change-tracking mechanism (see Dimension 13).

Negative.

- Every committed transaction now requires at least one durable write, the
  fsync of the log, which is a hard latency floor that cannot be optimized
  away, only amortized across transactions via group commit.
- Doubles the total bytes written to storage in the simplest implementations
  (once to the log, again eventually to the data files), which matters on
  cost-sensitive or write-endurance-limited media such as flash storage,
  where write amplification directly shortens device lifespan.
- Adds a whole new operational surface. log file growth, log rotation,
  checkpoint tuning, and log-space exhaustion are now failure modes that did
  not exist before, and getting checkpoint frequency wrong trades recovery
  time against steady-state write cost in ways that are easy to get wrong
  under real load.
- Recovery correctness is subtle and easy to get wrong in a hand-rolled
  implementation. Idempotent redo, correct handling of a crash during undo,
  and torn writes at the tail of the log (a partially written last record
  from the moment of the crash) all require careful, tested handling, which
  is why most engineers use an existing, battle-tested WAL implementation
  rather than writing one from scratch for a new project.

## 11. Failure modes and misuse

**Commit latency degrades under load with no CPU or lock contention visible.**
Symptom. Fsync-bound commits slow down and the slowdown does not correlate
with CPU usage, lock waits, or query complexity. Cause. The log device (or
filesystem) cannot sustain the fsync rate the workload demands, often because
the log shares a physical disk or volume with other heavy I/O, or the storage
backend batches or delays fsync in ways the application did not account for,
a common trap on some cloud network-attached-storage backends and on some
consumer SSDs whose firmware reports write completion before the data is
actually durable, to look faster on benchmarks. Fix. Isolate the log onto
dedicated, low-latency storage, verify the storage actually honors fsync as a
durability barrier rather than treating it as advisory, and use group commit
to amortize the fsync cost across concurrently committing transactions.

**Disk fills up unexpectedly, database goes read-only or crashes.** Symptom.
Log directory size grows without bound even though the write rate has not
changed. Cause. Log segments are not being reclaimed, most often because a
checkpoint is stalled or misconfigured, or because a replication consumer, a
streaming replica, a change-data-capture reader, has fallen far behind and
the system is correctly retaining old log segments that consumer still
needs, but nobody is monitoring replication lag as the actual root cause.
Fix. Alert directly on log directory size and on replication or consumer
lag, not only on disk free space, so the actual cause, a stalled checkpoint
or a lagging consumer, surfaces before the symptom, a full disk, does.

**Recovery after a crash takes far longer than expected, or the system
appears to hang on startup.** Symptom. Startup after a crash takes minutes
or longer instead of seconds. Cause. Checkpoints are too infrequent relative
to write volume, so recovery has to replay a very large amount of log since
the last checkpoint. This is a direct instance of the forces tradeoff in
Dimension 3, checkpoint frequency traded against steady-state cost, tuned
wrong for the actual write rate. Fix. Checkpoint on a schedule (time-based or
log-volume-based) tuned to bound worst-case recovery time to an acceptable
window for the operational requirements, and load-test the recovery path
deliberately, not only the happy path.

**Misuse. treating the WAL as a general-purpose message queue or audit log
for external consumers without understanding its retention model.** The log
in a classical database exists to serve crash recovery first. retaining it
long enough to also serve as an external audit trail or a message feed for
other systems, a legitimate and common pattern, see Dimension 13, change
data capture, requires deliberately reconfiguring retention and monitoring
consumer lag as a first-class operational concern, not assuming the log will
be there the way a purpose-built message log would be.

**Misuse. hand-rolling a WAL on top of a storage layer that already provides
one.** Building an application-level "audit log" table inside a relational
database, written synchronously as part of every transaction, to get a
change history, duplicates work the database's own WAL is already doing
internally and doubles the write cost for a need that, in most cases, is
better served by reading the database's actual write-ahead log via a
change-data-capture tool built for that purpose (see Dimension 13), rather
than reinventing logging inside the application.

## 12. Trade-off matrix

| Force | Write-Ahead Log | Shadow Paging / Copy-on-Write | Undo-Only Logging |
|---|---|---|---|
| Commit latency | One sequential fsync per commit, or per batch with group commit | No log fsync needed for the change itself, but committing a new root pointer still needs a durable write, and every change, however small, forces new page allocation | One log write per change, same fsync cost as WAL on commit |
| Recovery mechanism | Replay from last checkpoint, redo committed, undo in-flight | Roll back to the previous durable root, the new (incomplete) tree is simply discarded, no replay needed | Undo only, cannot redo committed-but-not-yet-flushed changes, so every change must be flushed before commit is acknowledged, which removes the sequential-write advantage |
| Write amplification | Doubles writes in the simplest case, log, then eventually data pages | Every modified page anywhere on the path from the changed leaf to the root must be rewritten, even for a one-byte change, typically higher amplification than WAL | Comparable to physical logging but without the deferred-flush efficiency benefit |
| Space reclamation | Bounded by checkpoint frequency, old segments reclaimed after checkpoint | Old (pre-commit) pages become garbage the moment the new root is committed and must be reclaimed, adding a garbage-collection concern | Log can be truncated once every logged change is confirmed flushed |
| Concurrency | Central log is a serialization point for writers, though reads of already-flushed pages are unaffected | Naturally supports snapshot-isolated readers on the previous durable version while a new version is being built, at the cost of the write amplification above | Same serialization concern as WAL, without WAL's throughput benefit |
| Best fit | High-throughput, small-transaction OLTP workloads where write latency and I/O efficiency matter most | Workloads where transactions are relatively rare or large, and simplicity of the discard-on-crash recovery story outweighs the per-write cost, or where copy-on-write is also wanted for other reasons, cheap snapshots, as in ZFS and Btrfs | Rarely chosen as a first design today, mostly of historical interest as the predecessor design WAL displaced once no-force buffer management became standard |

Shadow paging (also called copy-on-write paging) is the most commonly cited
named alternative to write-ahead logging for achieving crash-safe updates,
because instead of logging the intent to change a page, it never overwrites
a page in place at all. a modified page is written to a new location, its
parent is updated to point at the new location, which is itself a new page
written elsewhere, and this propagates up to a new root, which is installed
atomically as the very last, single durable write of the transaction. If the
system crashes at any point before that final root swap, the old root, and
therefore the entire old tree, is still intact and valid, and the
half-written new pages are simply garbage to be reclaimed later. LMDB is a
well known production key-value store built on copy-on-write B-trees rather
than write-ahead logging, and it explicitly documents this as its recovery
mechanism instead of a WAL (Symas Corporation, "LMDB, Lightning
Memory-Mapped Database Manager", project documentation,
https://www.symas.com/lmdb, verified 2026-08-02).

## 13. Related and incompatible patterns

- **Event Sourcing.** Event Sourcing generalizes the write-ahead log's core
  insight, an append-only, ordered record of what changed is authoritative,
  and moves it from being an internal implementation detail of a storage
  engine to being the primary source of truth for an entire application's
  state, with current state derived by replaying or folding the event log
  rather than being stored directly. See this repository's Event Sourcing
  entry for the full treatment. a write-ahead log is, in a sense, the
  storage-engine-internal ancestor of the application-level event log,
  sharing the append-first, replay-to-recover shape but operating at a
  different layer and typically with a much shorter retention horizon.
- **Change Data Capture.** CDC tools read a database's existing write-ahead
  log to produce a stream of change events for downstream consumers, reusing
  the log this pattern describes rather than requiring the application to
  maintain a separate change feed. This is the most direct compositional
  relationship in this list. CDC is built on top of an existing WAL, not an
  alternative to it.
- **Leader-Followers (replication).** Streaming or log-shipping replication,
  as implemented by PostgreSQL and by Raft-based systems such as etcd, works
  by shipping the leader's write-ahead log entries to follower replicas and
  having each follower replay them locally, which is exactly the recovery
  procedure in Dimension 7 applied continuously to keep a second copy of the
  system current rather than only on restart after a crash. See this
  repository's Leader-Followers and Leader-Follower Architecture entries.
- **Checkpointing.** A companion mechanism, not a separate architectural
  pattern with its own catalog entry in most treatments, but important
  enough to call out. checkpointing is what bounds the write-ahead log's
  growth and bounds recovery time, and no production WAL implementation
  ships without one, as covered in Dimension 3 and Dimension 11.
- **Shadow Paging (copy-on-write).** Covered as the primary named alternative
  in Dimension 12. The two patterns are not composable with each other for
  the same data structure, a page is either logged-and-updated-in-place or
  copied-on-write, not both, but a single system can legitimately use
  write-ahead logging for its primary transactional data and copy-on-write
  for a separate purpose, such as ZFS using copy-on-write for its filesystem
  block layer while still maintaining an intent log (the ZIL) for
  synchronous write latency, which is itself a write-ahead log used
  specifically to avoid waiting on the copy-on-write commit path for
  latency-sensitive synchronous writes.
- **Incompatible with.** Nothing at the conceptual level rules out combining
  WAL with other durability patterns, but WAL is redundant, not merely
  unnecessary, when layered directly underneath another mechanism already
  providing the identical guarantee for the identical data, as described in
  Dimension 4's non-applicability list, hand-rolling a WAL inside a database
  that already write-ahead-logs the same writes.

## 14. Refactoring path in and out

Introducing write-ahead logging into a system that currently mutates its data
files in place, step by step.

```
1. Define the log record format first. Decide what a record needs
   to contain to make redo (and, if needed, undo) possible, at
   minimum an LSN, an identifier for the affected data structure,
   and enough payload to reapply the change.
2. Add an append-only log file and a log writer that can append a
   record and force it durable (fsync or equivalent) on demand. Do
   this in isolation, with its own tests, before touching the commit
   path at all.
3. Change the commit path so that, before acknowledging a transaction
   as committed, the engine writes and fsyncs the transaction's log
   records, including a commit record. At this point the data pages
   are still being written in place as before, this step alone adds
   durability without yet gaining the performance benefit.
4. Change data page writes to happen against an in-memory buffer pool
   rather than directly to disk, and add a background flusher that
   writes dirty pages to disk asynchronously, enforcing the rule that
   a page's flush waits until its highest LSN is durable in the log.
   This is the step that actually delivers the sequential-write
   performance advantage, and it is also the step where most of the
   subtlety and risk lives, so it deserves the most testing.
5. Add a checkpoint mechanism, and add a recovery procedure that runs
   on startup, detects an unclean shutdown, and replays the log from
   the last checkpoint. Test recovery deliberately, by killing the
   process at many different points during writes and verifying the
   recovered state is always exactly the set of transactions that
   were actually committed.
6. Add log rotation and retention policy once the basic mechanism is
   proven, tuned to the actual checkpoint frequency and any
   replication or CDC consumers that depend on log retention.
```

Removing write-ahead logging (rare, and worth doing carefully because it is a
durability downgrade, not a neutral simplification).

```
1. Confirm the actual reason for removal, usually "we moved this
   data to a storage layer that already provides the guarantee", for
   example migrating a hand-rolled audit table to a managed database
   with its own WAL, or moving a workload onto a system where
   durability is provided by replication (multiple in-memory copies
   with quorum acknowledgment) rather than local logging.
2. Verify the replacement actually provides an equivalent guarantee
   under the same failure modes the WAL was protecting against
   (single-process crash, single-machine power loss), not only under
   the failure modes that are easy to test.
3. Remove the log write from the commit path only after the
   replacement guarantee is verified in production-like conditions,
   and keep the ability to detect and alert on any observed
   durability regression during the transition.
4. Decommission the log storage and its rotation and checkpoint
   machinery last, after the removal has been running safely for a
   deliberately chosen soak period.
```

## 15. Testing and verification

Because the entire value of a WAL is what happens across a crash, tests that
never simulate a crash test the least important part of the mechanism. The
standard, and largely irreplaceable, testing technique is fault injection
around process termination. run a workload against the system, kill the
process (SIGKILL, not a graceful shutdown, to simulate a real crash rather
than an orderly stop) at many different points in the write path, restart the
system, and verify that the recovered state contains exactly the transactions
that had actually been acknowledged as committed before the kill, no more and
no fewer. This needs to be automated and run repeatedly with randomized kill
points, because the interesting bugs live in narrow timing windows, a kill
between the log fsync and the data page flush, a kill mid-checkpoint, a kill
mid-write leaving a torn record at the tail of the log file, that manual
testing rarely hits by chance.

A second essential technique is torn-write simulation at the log file level
specifically. truncate or corrupt the last record of a log file to simulate a
write that was in progress at the moment of a power loss (as opposed to a
clean process kill, which usually still leaves complete records because the
OS page cache flush completes even if the process itself is gone), and verify
the recovery procedure detects the incomplete final record and safely ignores
it rather than treating garbage bytes as a valid log entry.

For the redo and undo logic itself, property-based testing is a strong fit.
generate random sequences of operations, apply them through the normal
commit path to reach some end state, then independently verify that replaying
only the log from a randomly chosen earlier point reconstructs the same state
that the actual data pages show. Any divergence is a concrete, minimal, and
reproducible bug report, which is exactly the failure mode manual test cases
tend to miss.

At the integration level, test the checkpoint and recovery time relationship
directly. measure recovery time as a function of the volume of log written
since the last checkpoint under realistic write rates, so that the
checkpoint-frequency tuning decision in Dimension 3 is based on a measured
number for the actual workload rather than a guess.

## 16. Observability signals

- **Log write (fsync) latency, p50/p99/p999.** The single most important
  metric for a WAL-backed system, because it is very close to the transaction
  commit latency floor. A healthy instance shows tight, low, stable latency
  matching the underlying storage's known fsync characteristics, a failing
  or degraded instance shows a widening tail, which is usually the earliest
  visible sign of a storage problem before anything else in the system
  notices.
- **Log directory (or partition) size and growth rate.** Should track a
  predictable relationship to checkpoint frequency and write rate. an
  unexpectedly growing log directory that does not shrink after checkpoints
  is the standard early warning sign for either a stalled checkpoint or a
  lagging replication/CDC consumer holding old segments open, per Dimension
  11.
- **Checkpoint duration and frequency.** How often checkpoints run and how
  long each one takes. a checkpoint that is taking longer relative to its
  configured interval, or that is being skipped or delayed, directly predicts
  both future disk usage growth and future recovery-time risk.
- **Replication or replay lag, measured in log position (LSN or offset), not
  wall-clock time alone.** Because retention and recovery are both
  fundamentally about how far behind is anyone who still needs old log
  entries, the most actionable form of this metric is the gap in log
  position between the current write position and the oldest position anyone
  (a replica, a CDC consumer, a checkpoint) still needs.
- **Recovery duration on the most recent restart.** Recorded and tracked over
  time as an operational metric in its own right, not only measured
  reactively during an incident, so that a slow trend in recovery time, a
  leading indicator of a checkpoint-tuning problem, is visible before an
  actual crash forces a slow recovery under pressure.
- **Torn-write and corruption detections during recovery, counted and
  alerted on even when recovery still succeeds.** A recovery that correctly
  detects and discards a torn tail record is working as designed, but a
  nonzero rate of these events over time is worth investigating as a possible
  symptom of an unreliable storage layer or an unclean shutdown pattern that
  should not be happening as often as it is.

## 17. Security and privacy implications

The write-ahead log contains, by construction, a complete and often
uncompressed record of every change made to the data it protects, including
changes that were later rolled back or that affected fields the application
never intended to expose directly, such as full previous values of updated
rows in physical or physiological logging schemes. This has direct data
protection implications that are easy to overlook because the log is an
internal implementation detail rather than a user-facing data store.

- **Retention and right-to-erasure conflicts.** If a data subject's personal
  data is deleted from the primary data files to satisfy an erasure request,
  copies of that data may still exist in retained WAL segments, in WAL
  archives kept for point-in-time recovery, and in any replication or backup
  streams derived from the log, until those segments age out or are
  themselves purged. A deletion policy that only accounts for the primary
  data files, and not the WAL retention window and any WAL-derived archives,
  is incomplete.
- **Access control on log files and archives.** Because the log can contain
  the same sensitive field values as the primary data, log files, archived
  WAL segments, and any replication stream carrying log data need the same
  access controls and encryption-at-rest treatment as the primary database,
  not a lighter standard on the assumption that it is just an internal log
  file.
- **Encryption in transit for shipped logs.** Streaming replication and log
  shipping to a standby or to a backup archive transmit the WAL's content,
  including sensitive field values, across the network, and that transport
  should be encrypted to the same standard as any other transmission of the
  underlying sensitive data.
- **CDC consumer trust boundary.** Because change-data-capture systems (see
  Dimension 13) read the WAL directly to produce downstream event streams,
  granting a system CDC access to a database's log is effectively granting it
  visibility into every change to every logged field, which may be broader
  than the specific tables or columns the consuming system was actually
  intended to see, and should be scoped and audited deliberately rather than
  granted as a blanket capability.
- **Log tampering as an attack vector.** In systems where the log is also
  used for audit purposes, see the misuse note in Dimension 11 about
  treating a hand-rolled audit table as a substitute for using the real WAL
  via CDC, the WAL's own integrity, whether an actor with write access to
  the log files can insert, remove, or reorder entries, becomes a security
  property worth reasoning about explicitly if the log is relied upon as
  evidence, in a way that is easy to overlook if the log's original purpose
  was recovery only rather than a trusted audit trail.

## 18. References

1. Jim Gray. "Notes on Data Base Operating Systems". IBM Research Report
   RJ2188, 1978. Republished in "Operating Systems, an Advanced Course",
   Lecture Notes in Computer Science Vol. 60, Springer-Verlag, 1978. Source of
   the earliest formal statement of the write-ahead rule cited in dimension 1.
2. C. Mohan, Don Haderle, Bruce Lindsay, Hamid Pirahesh, Peter Schwarz.
   "ARIES, a Transaction Recovery Method Supporting Fine-Granularity Locking
   and Partial Rollbacks Using Write-Ahead Logging". ACM Transactions on
   Database Systems, Vol. 17, No. 1, March 1992, pages 94 to 162.
   https://dl.acm.org/doi/10.1145/128765.128770
   Verified 2026-08-02. Source of the ARIES recovery algorithm in dimensions
   1, 7, and 9.
3. Wikipedia. "Algorithms for Recovery and Isolation Exploiting Semantics".
   https://en.wikipedia.org/wiki/Algorithms_for_Recovery_and_Isolation_Exploiting_Semantics
   Verified 2026-08-02. Source for the ARIES adoption summary in dimensions 1
   and 9.
4. PostgreSQL Global Development Group. "PostgreSQL 18 Documentation,
   Chapter 28, Reliability and the Write-Ahead Log".
   https://www.postgresql.org/docs/current/wal-intro.html
   Verified 2026-08-02. Source for the PostgreSQL production use in
   dimension 9.
5. D. Richard Hipp / SQLite project. "Write-Ahead Logging".
   https://www.sqlite.org/wal.html
   Verified 2026-08-02. Source for the SQLite WAL mode design in dimensions 8
   and 9.
6. Apache Kafka project. "Documentation, 4. Design, Log".
   https://kafka.apache.org/documentation/#log
   Verified 2026-08-02. Source for the Kafka commit log design in dimension
   9.
7. Guozhang Wang, Joel Koshy, Sriram Subramanian, Kartik Paramasivam, Mammad
   Zadeh, Neha Narkhede, Jun Rao, Jay Kreps, Joe Stein. "Building a
   Replicated Logging System with Apache Kafka". Proceedings of the VLDB
   Endowment, Vol. 8, No. 12, 2015.
   https://www.vldb.org/pvldb/vol8/p1654-wang.pdf
   Verified 2026-08-02. Source for the Kafka replicated write path in
   dimension 9.
8. etcd project. Package `server/storage/wal`.
   https://github.com/etcd-io/etcd/tree/main/server/storage/wal
   Verified 2026-08-02. Source for the etcd production use in dimensions 8
   and 9.
9. Symas Corporation. "LMDB, Lightning Memory-Mapped Database Manager".
   https://www.symas.com/lmdb
   Verified 2026-08-02. Source for the copy-on-write alternative in
   dimension 12.

## Code examples

The three implementations below are a minimal, single-writer write-ahead log
covering the core mechanism from Dimensions 6 and 7, append a record, force
it durable, replay it on recovery, applying the write-ahead rule (log record
durable before the corresponding "page", here a simple in-memory key-value
map, is considered committed). They are deliberately small enough to read in
full and are not a substitute for a production storage engine.

### TypeScript

```typescript
import { openSync, writeSync, fsyncSync, closeSync, readFileSync, existsSync } from "fs";

interface LogRecord {
  lsn: number;
  key: string;
  value: string | null;
}

class WriteAheadLog {
  private fd: number;
  private nextLsn = 1;

  constructor(path: string) {
    this.fd = openSync(path, existsSync(path) ? "a" : "w");
  }

  append(key: string, value: string | null): number {
    const lsn = this.nextLsn++;
    const record: LogRecord = { lsn, key, value };
    const line = JSON.stringify(record) + "\n";
    writeSync(this.fd, line);
    fsyncSync(this.fd);
    return lsn;
  }

  close(): void {
    closeSync(this.fd);
  }
}

class KeyValueStore {
  private data = new Map<string, string>();
  private log: WriteAheadLog;

  constructor(logPath: string) {
    this.recover(logPath);
    this.log = new WriteAheadLog(logPath);
  }

  private recover(logPath: string): void {
    if (!existsSync(logPath)) return;
    const contents = readFileSync(logPath, "utf8");
    for (const line of contents.split("\n")) {
      if (!line.trim()) continue;
      const record: LogRecord = JSON.parse(line);
      if (record.value === null) {
        this.data.delete(record.key);
      } else {
        this.data.set(record.key, record.value);
      }
    }
  }

  set(key: string, value: string): void {
    this.log.append(key, value);
    this.data.set(key, value);
  }

  delete(key: string): void {
    this.log.append(key, null);
    this.data.delete(key);
  }

  get(key: string): string | undefined {
    return this.data.get(key);
  }

  close(): void {
    this.log.close();
  }
}

const store = new KeyValueStore("/tmp/wal-example-ts.log");
store.set("account:42", "100");
store.set("account:43", "50");
store.delete("account:43");
console.log(store.get("account:42"));
console.log(store.get("account:43"));
store.close();
```

### Python

```python
import json
import os


class WriteAheadLog:
    def __init__(self, path):
        self.path = path
        self._fd = os.open(path, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o644)
        self._next_lsn = 1

    def append(self, key, value):
        lsn = self._next_lsn
        self._next_lsn += 1
        record = {"lsn": lsn, "key": key, "value": value}
        line = (json.dumps(record) + "\n").encode("utf-8")
        os.write(self._fd, line)
        os.fsync(self._fd)
        return lsn

    def close(self):
        os.close(self._fd)


class KeyValueStore:
    def __init__(self, log_path):
        self._data = {}
        self._recover(log_path)
        self._log = WriteAheadLog(log_path)

    def _recover(self, log_path):
        if not os.path.exists(log_path):
            return
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                if record["value"] is None:
                    self._data.pop(record["key"], None)
                else:
                    self._data[record["key"]] = record["value"]

    def set(self, key, value):
        self._log.append(key, value)
        self._data[key] = value

    def delete(self, key):
        self._log.append(key, None)
        self._data.pop(key, None)

    def get(self, key):
        return self._data.get(key)

    def close(self):
        self._log.close()


if __name__ == "__main__":
    path = "/tmp/wal-example-py.log"
    if os.path.exists(path):
        os.remove(path)
    store = KeyValueStore(path)
    store.set("account:42", "100")
    store.set("account:43", "50")
    store.delete("account:43")
    print(store.get("account:42"))
    print(store.get("account:43"))
    store.close()
```

### Go

```go
package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
)

type LogRecord struct {
	LSN   int     `json:"lsn"`
	Key   string  `json:"key"`
	Value *string `json:"value"`
}

type WriteAheadLog struct {
	file    *os.File
	nextLSN int
}

func OpenWAL(path string) (*WriteAheadLog, error) {
	f, err := os.OpenFile(path, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		return nil, err
	}
	return &WriteAheadLog{file: f, nextLSN: 1}, nil
}

func (w *WriteAheadLog) Append(key string, value *string) (int, error) {
	lsn := w.nextLSN
	w.nextLSN++
	record := LogRecord{LSN: lsn, Key: key, Value: value}
	line, err := json.Marshal(record)
	if err != nil {
		return 0, err
	}
	line = append(line, '\n')
	if _, err := w.file.Write(line); err != nil {
		return 0, err
	}
	if err := w.file.Sync(); err != nil {
		return 0, err
	}
	return lsn, nil
}

func (w *WriteAheadLog) Close() error {
	return w.file.Close()
}

type KeyValueStore struct {
	data map[string]string
	log  *WriteAheadLog
}

func OpenStore(path string) (*KeyValueStore, error) {
	store := &KeyValueStore{data: make(map[string]string)}
	if err := store.recover(path); err != nil {
		return nil, err
	}
	wal, err := OpenWAL(path)
	if err != nil {
		return nil, err
	}
	store.log = wal
	return store, nil
}

func (s *KeyValueStore) recover(path string) error {
	f, err := os.Open(path)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	defer f.Close()

	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := scanner.Bytes()
		if len(line) == 0 {
			continue
		}
		var record LogRecord
		if err := json.Unmarshal(line, &record); err != nil {
			return err
		}
		if record.Value == nil {
			delete(s.data, record.Key)
		} else {
			s.data[record.Key] = *record.Value
		}
	}
	return scanner.Err()
}

func (s *KeyValueStore) Set(key, value string) error {
	if _, err := s.log.Append(key, &value); err != nil {
		return err
	}
	s.data[key] = value
	return nil
}

func (s *KeyValueStore) Delete(key string) error {
	if _, err := s.log.Append(key, nil); err != nil {
		return err
	}
	delete(s.data, key)
	return nil
}

func (s *KeyValueStore) Get(key string) (string, bool) {
	v, ok := s.data[key]
	return v, ok
}

func (s *KeyValueStore) Close() error {
	return s.log.Close()
}

func main() {
	path := "/tmp/wal-example-go.log"
	os.Remove(path)

	store, err := OpenStore(path)
	if err != nil {
		panic(err)
	}

	store.Set("account:42", "100")
	store.Set("account:43", "50")
	store.Delete("account:43")

	if v, ok := store.Get("account:42"); ok {
		fmt.Println(v)
	}
	if _, ok := store.Get("account:43"); !ok {
		fmt.Println("deleted")
	}

	store.Close()
}
```

Java, Rust, and Swift are omitted from the compiled samples above. The pattern
translates directly into each, a file handle opened for append, a serialized
record write, an explicit fsync equivalent such as `FileChannel.force(true)`
in Java, `File::sync_all` in Rust, or a POSIX `fsync` call reached through
`FileHandle` in Swift, and a startup replay loop, but the mechanism itself is
identical across languages, so a fourth and fifth restatement of the same
25-line structure would not add anything the three above do not already show.
