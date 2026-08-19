---
name: LSM Tree
slug: lsm-tree
family: 12-data-storage
category: Data and Storage
aliases: [Log-Structured Merge-Tree, Log-Structured Merge Tree]
first_described: "O'Neil, Cheng, Gawlick, O'Neil 1996"
maturity: canonical
related: [write-ahead-log, bloom-filter, sharding, event-sourcing, cqrs]
incompatible_with: []
verified: 2026-08-02
---

# LSM Tree

## 1. Name, aliases, and lineage

The canonical name is the Log-Structured Merge-Tree, almost always abbreviated
LSM tree or LSM-tree in running text. It was first described in Patrick E.
O'Neil, Edward Cheng, Dieter Gawlick, and Elizabeth J. O'Neil, "The
Log-Structured Merge-Tree (LSM-Tree)," Acta Informatica 33(4), 1996, pages
351 to 385 (cross-referenced via [dblp](https://dblp.org/rec/journals/acta/ONeilCGO96.html),
verified 2026-08-02). The paper's central move was to combine two older ideas,
the append-only log-structured file system work of Rosenblum and Ousterhout
and the merge step of an external merge sort, into a single indexing structure
built for a storage medium where random writes are expensive relative to
sequential ones. That medium was spinning disk in 1996. Flash and cloud object
storage inherited the same asymmetry for different physical reasons, which is
why the paper's argument outlived the hardware it was written against.

The full name is used almost everywhere the pattern is discussed formally,
and no meaningfully different alias has taken hold. What varies across
systems is not the name of the tree but the name of its parts. RocksDB and
LevelDB call the on-disk sorted files SSTables, a term inherited from
Bigtable; Cassandra also calls them SSTables; some academic papers use "runs"
or "sorted runs" for the same concept, particularly in the tiering and
leveling literature that formalized LSM cost models after the original paper,
for example Dayan, Athanassoulis, and Idreos, "Monkey. Optimal Navigable
Key-Value Store," SIGMOD 2017. This entry uses SSTable throughout because it
is the term the most widely deployed real systems (LevelDB, RocksDB,
Cassandra) actually use in their own source and documentation.

## 2. Problem and context

A key-value or wide-column store needs to sustain a high rate of writes,
including writes that touch keys scattered across the entire key space, while
still answering point lookups and range scans without unbounded latency
growth. A classic in-place structure, a B-tree being the reference case,
answers a write by locating the leaf page that owns the key and mutating it
on disk. When writes are randomly distributed across a key space larger than
memory, that means a random disk seek, or a random flash page write and
erase, for nearly every write. Spinning disk seeks cost single-digit
milliseconds; SSD random writes are fast but suffer write amplification at
the flash translation layer, and cause fragmentation that degrades garbage
collection over the device's life. Either way, in-place random-write
throughput on a key-value workload tops out far below what sequential
throughput on the same device can sustain, often by one to two orders of
magnitude for spinning disk and a smaller but still real factor for flash.

The situation that creates the need for an LSM tree, concretely, looks like
this. A service ingests events, metrics, or user actions at high volume, the
keys involved (a user id, a sensor id, a UUID) are effectively random with
respect to any on-disk ordering, and the write path is on the critical path
of the service, so every millisecond of write latency is felt by a caller.
Simultaneously the service still needs to serve reads, often of recent data
(a hot working set that benefits from caching) or of a bounded key range (a
time-series query, a user's recent orders). A structure tuned purely for
sequential write throughput and indifferent to reads, a plain append-only
log, would solve the write half of the problem and make every read a full
scan. The LSM tree exists in the gap between those two extremes, accepting
writes as fast as an append-only log can, then periodically reorganizing
that log into a form that reads can navigate in logarithmic time, paying for
the reorganization in a background process rather than on the write's
critical path.

The context that makes LSM the right answer, rather than a B-tree or a hash
index, has three parts. First, the write volume is genuinely high and the key
distribution is not friendly to locality, so in-place random writes would
dominate the I/O budget. Second, the storage medium has an asymmetry between
sequential and random write cost that the application can exploit, true of
spinning disk, true to a lesser but still real degree of flash SSDs and cloud
block and object storage. Third, the workload can tolerate reads that are
somewhat more expensive than a B-tree's single-page-per-level lookup, in
exchange for that write throughput, and can tolerate space and CPU spent on a
background compaction process.

## 3. Forces

The LSM tree is a deliberate trade of read cost and background CPU and I/O
for write cost, and every real-world tuning knob on an LSM implementation is
an attempt to move that trade along a continuous curve rather than escape it.

Write latency versus write amplification. A write that only appends to an
in-memory structure and a log is nearly free, microseconds, not
milliseconds. But every byte written eventually gets rewritten by compaction,
sometimes many times, as it moves from the newest, smallest level to older,
larger levels. The RocksDB tuning guide states this precisely, writing 10
MB/s to the database while observing 30 MB/s of disk write traffic is a write
amplification of 3, and it explains that under level compaction "every byte
gets written to Level 0, then compacted into Level 1... and repeatedly
compacted into higher levels where each byte merges with many existing
bytes" ([RocksDB Tuning Guide](https://github.com/facebook/rocksdb/wiki/RocksDB-Tuning-Guide),
verified 2026-08-02). Cheap writes on the front end are bought with
extra, deferred writes on the back end; the pattern never eliminates the
work, it moves it off the caller's latency path and amortizes it.

Read amplification versus write amplification. A point read in the worst
case must check the memtable, then potentially every SSTable at every level,
because a key can live in any of them and the newest write for that key
wins. Bloom filters and per-level key range metadata cut this down sharply in
practice, but a pattern that compacts aggressively to keep read amplification
low (fewer, larger, more overlapping-free SSTables) does so by increasing
write amplification, and a pattern that compacts lazily to keep write
amplification low does so by leaving more SSTables for a read to consult.
This is the single force every compaction strategy exists to arbitrate, and
it cannot be eliminated, only shifted, which the trade-off matrix in
dimension 12 makes explicit per strategy.

Space amplification versus both of the above. An LSM tree does not overwrite
data in place; an update or delete is itself a new entry with the same key
and a newer sequence number or a tombstone marker, and the old value is not
reclaimed until compaction physically merges the levels that contain both
versions and discards the shadowed one. Between compactions, a database can
hold multiple versions of the same logical row, multiplying its on-disk
footprint relative to the live data set. Deferring compaction to reduce write
amplification directly increases space amplification, and in the worst
observed case, workloads with heavy overwrite or delete traffic and an
under-tuned compaction schedule, space amplification factors of two to four
times the live data size are common in production RocksDB deployments before
retuning, per Facebook's own account of RocksDB's evolution (Dong, Kryczka,
Jin, and Stumm, "Evolution of Development Priorities in Key-value Stores
Serving Large-scale Applications. The RocksDB Experience," 19th USENIX
Conference on File and Storage Technologies, FAST 21, 2021, pages 33 to 49,
cross-referenced via [WebSearch summary of the paper](https://www.usenix.org/conference/fast21/presentation/dong),
verified 2026-08-02).

Compaction cost versus foreground responsiveness. Background compaction
competes with foreground reads and writes for the same disk bandwidth and CPU
cores. A compaction scheduler that runs too aggressively starves user-facing
traffic of I/O; one that runs too lazily lets Level 0 SSTables pile up, which
degrades both read amplification (more files to check) and, in systems that
stall writes when Level 0 is too large, write latency itself, turning the
system's own safety valve into a foreground stall. This coupling between a
background maintenance process and foreground latency is the operational
force that dominates real LSM tuning conversations, more than the asymptotic
trade-offs that dominate academic ones.

Durability versus write latency. The memtable is volatile; durability across
a crash is provided by a write-ahead log that is appended, and often
fsynced, before or alongside the memtable write. A system that fsyncs every
write is durable against process crashes and OS crashes at the cost of
disk-flush latency on every write; a system that batches or defers the fsync
trades a bounded window of possible data loss (typically milliseconds to a
few seconds) for materially higher throughput. This is a standard
write-ahead-log trade discussed at length in its own entry in this catalog
and is not unique to LSM trees, but LSM trees make the trade unusually
visible because the memtable itself contributes nothing to durability.

## 4. Applicability and non-applicability

Reach for an LSM tree when the workload is write-heavy or write-bursty, when
keys are not naturally clustered by insertion order (so an append-only file
sorted by insertion time would not also be sorted by key), when point and
short-range reads on recent or hot data need to stay fast while cold data
does not, when the storage medium rewards sequential I/O over random I/O
(spinning disk, most flash, most cloud block storage), and when the
operational team can run and monitor a background compaction process, either
directly (self-hosted RocksDB, Cassandra) or through a managed service that
does it for them (DynamoDB, Bigtable, most modern time-series databases).

Do not reach for an LSM tree in these situations, with the reason for each.

- The workload is read-dominated with infrequent writes and the read
  latency tail matters more than write throughput. A B-tree gives a single,
  predictable number of page accesses per read (its height, typically three
  to four for a large table); an LSM tree's read cost depends on how many
  SSTables have accumulated since the last compaction, which varies over
  time and under load, making tail latency less predictable unless
  compaction is tuned aggressively, which reintroduces the write-cost the
  pattern was meant to avoid.
- The data fits comfortably in memory and durability can be handled by a
  simpler snapshot-plus-log scheme. An in-memory hash table or sorted
  structure with periodic snapshots (Redis's RDB, for example) avoids the
  entire compaction machinery and its operational surface area.
- Strong, low-latency range-scan performance across the full key space is
  the primary requirement and writes are comparatively rare. A B+-tree keeps
  leaf pages physically or logically ordered with no merge step needed; an
  LSM tree's data is scattered across levels and a full-range scan must
  merge-read every level, which costs more CPU and I/O than a B+-tree's
  single ordered traversal even though both are asymptotically the same
  complexity class.
- The team cannot operate or does not want to operate background compaction.
  Compaction has real failure modes (dimension 11) that require monitoring,
  alerting, and occasional manual intervention (forcing a major compaction,
  adjusting compaction priority, or reprovisioning I/O bandwidth); a team
  without the operational maturity to watch these signals will eventually be
  paged by a compaction backlog they do not understand.
- Data is write-once and never updated or deleted, and the natural insertion
  order already matches a useful read order (an append-only time-series log
  read back in time order, for example). In that specific case a simpler
  segment-file log without a merge-sorted, multi-level read path may serve
  the workload with less machinery, though many time-series databases still
  choose an LSM-derived structure for other reasons, notably efficient
  compression of sorted-by-time segments.
- Transactional, multi-row ACID semantics with serializable isolation are
  the primary requirement and the storage engine itself must provide them.
  LSM trees are commonly used as the storage layer under a transactional
  engine (RocksDB under CockroachDB and TiDB, for instance), but the LSM
  tree itself provides no cross-key transaction semantics; that is a layer
  built on top, and choosing LSM does not by itself solve the transaction
  problem.

## 5. Structure

An LSM tree has two structural halves, one in memory and one on disk, plus a
supporting durability mechanism.

- **Memtable.** An in-memory, sorted structure, typically a skip list or a
  balanced tree, that receives every write first. Reads consult it before
  anything on disk, because it holds the newest data. It has a configured
  size threshold (commonly tens to a few hundred megabytes) that triggers a
  flush when exceeded.
- **Write-ahead log (WAL).** An append-only on-disk log that records every
  mutation before or alongside its application to the memtable, so the
  memtable's contents can be reconstructed after a crash without waiting for
  a flush. See the write-ahead-log entry in this catalog for the general
  pattern; the LSM tree is one of its most common consumers.
- **Immutable memtable.** When the active memtable fills, it is frozen
  (renamed immutable) and a new, empty memtable takes over writes. The
  immutable memtable is still served for reads while a background thread
  flushes it to disk.
- **SSTable (sorted string table).** An immutable, on-disk file holding
  sorted key-value pairs, produced by flushing a memtable or by compacting
  older SSTables. Once written, an SSTable is never modified, only read or
  eventually deleted by a later compaction. Each SSTable typically carries
  an internal index (a sparse or dense key index) and, in most production
  implementations, a Bloom filter summarizing the keys it contains so a
  point lookup can skip the file entirely with high probability if the key
  is absent.
- **Levels (or sorted runs).** SSTables are organized into levels, commonly
  numbered from 0 upward. Level 0 holds freshly flushed SSTables and may
  contain overlapping key ranges across its files, because each flush
  starts a new file independently. Levels 1 and above are compacted so that
  files within a level have non-overlapping key ranges, letting a lookup at
  those levels binary-search to a single candidate file rather than check
  every file in the level. Each level is typically an order of magnitude
  larger than the one above it; the LevelDB implementation documentation
  states level-1 is sized around 10 MB and level-2 around 100 MB, growing
  by roughly a factor of ten per level
  ([LevelDB implementation notes](https://github.com/google/leveldb/blob/main/doc/impl.md),
  verified 2026-08-02).
- **Manifest (or version metadata).** A separate persistent record of which
  SSTables exist at which level and what key ranges each covers, so the
  database can reconstruct its current view of the data on restart without
  re-scanning every file. LevelDB's own documentation describes the
  MANIFEST file as listing "the set of sorted tables that make up each
  level, the corresponding key ranges, and other important metadata"
  ([LevelDB implementation notes](https://github.com/google/leveldb/blob/main/doc/impl.md),
  verified 2026-08-02).
- **Compaction process.** A background procedure, or family of procedures
  depending on the compaction strategy chosen, that reads a set of SSTables,
  merge-sorts their contents, discards shadowed or tombstoned entries once
  they are no longer needed for correctness, and writes the result as new
  SSTables at a lower (denser) level, then deletes the input files.

## 6. ASCII structure diagram

```text
                     WRITE PATH                          READ PATH
                        |                                    |
                        v                                    v
              +-------------------+                +-------------------+
              |   Write-Ahead Log |                |   query key K      |
              |   (append only)   |                +-------------------+
              +-------------------+                          |
                        |                                     v
                        v                          +---------------------+
              +-------------------+                | 1. check memtable   |
              |     Memtable      |<---------------+ 2. check immutable  |
              |  (sorted, RAM)    |                |    memtable if any  |
              +-------------------+                +---------------------+
                        |                                     |
                flush when full                    if not found, descend
                        v                                     v
              +-------------------+                +---------------------+
              |     Level 0       |  overlapping    | 3. check L0 files   |
              |  SSTable SSTable  |  key ranges,     |    (may overlap,   |
              |  SSTable ...      |  checked in      |    check newest    |
              +-------------------+  newest-first    |    first, Bloom    |
                        |            order           |    filter first)  |
                compaction merges                    +---------------------+
                        v                                     |
              +-------------------+                +---------------------+
              |     Level 1       |  non-overlapping| 4. binary search    |
              |  SSTable SSTable  |  key ranges,     |    within level    |
              |  SSTable ...      |  ~10x L0 size    |    (Bloom filter   |
              +-------------------+                  |    per file first)|
                        |                             +---------------------+
                compaction merges                                |
                        v                                     ...continue
              +-------------------+                        down levels
              |     Level 2       |  ~10x L1 size          until found
              |  (larger, colder) |                        or exhausted
              +-------------------+
                        |
                       ...
                        v
              +-------------------+
              |     Level N        |  coldest, largest,
              |  (oldest data)      |  fewest writes touch it
              +-------------------+
```

## 7. Dynamics

The write path and the read path move through the structure differently, and
compaction runs asynchronously to both.

```text
WRITE(key, value)
  1. Append (key, value, seq_no) to the write-ahead log.
     If the WAL append is synchronous (fsync before ack), durability is
     guaranteed for this write at this point.
  2. Insert (key, value, seq_no) into the active memtable.
  3. Acknowledge the write to the caller.
  --- asynchronous, does not block the caller ---
  4. If active memtable size >= threshold.
       a. Freeze it as an immutable memtable; start a new active memtable.
       b. Schedule a flush. sort-order-write the immutable memtable to a
          new Level 0 SSTable, with a Bloom filter and index built inline.
       c. On successful flush, drop the immutable memtable from memory and
          truncate the corresponding portion of the WAL.

READ(key)
  1. Check the active memtable. If key found (including a tombstone),
     return the associated value or "not found" and stop.
  2. Check the immutable memtable, if one exists, same rule.
  3. For each Level 0 SSTable, newest first.
       consult its Bloom filter; if it says "definitely absent," skip.
       otherwise, check its index/binary search; if key found, return
       the value (or tombstone) and stop, because Level 0 order defines
       newest-wins among overlapping files.
  4. For Level 1 through N, in order.
       identify the single SSTable in that level whose key range could
       contain the key (levels are non-overlapping, so at most one file
       per level), consult its Bloom filter, then binary search if the
       filter does not rule it out.
       if key found, return the value (or tombstone) and stop.
  5. If no level yields the key, return "not found."

RANGE SCAN(start, end)
  1. Open an iterator over the memtable restricted to [start, end).
  2. Open an iterator over each relevant SSTable at every level whose key
     range intersects [start, end).
  3. Merge all iterators in key order (a k-way merge), preferring the
     newest source (memtable, then Level 0 newest-first, then higher
     levels) whenever the same key appears in more than one source.
  4. Skip tombstoned or superseded entries as they are encountered.
  5. Yield the merged, deduplicated stream to the caller.

COMPACTION (background, style-dependent, level-style shown)
  1. Trigger. Level L exceeds its size or file-count threshold, or a
     manual/scheduled compaction is requested.
  2. Select. choose one (or a few) SSTables from Level L, and every
     SSTable in Level L+1 whose key range overlaps them.
  3. Merge. k-way merge-sort the selected SSTables by key; for each key,
     keep only the entry with the highest sequence number; drop
     tombstones once no lower level (further from memory) could still
     hold a shadowed value they need to suppress, subject to the
     engine's tombstone-retention window for read-repair correctness.
  4. Write. emit the merged result as one or more new SSTables sized for
     Level L+1.
  5. Install. atomically update the manifest to reference the new
     SSTables and remove the old ones; the old files are then deleted
     (or scheduled for deletion once no reader still references them).
  6. Loop. if the resulting Level L+1 now exceeds its own threshold,
     schedule a further compaction from L+1 into L+2, and so on.
```

The correctness-critical detail in this dynamic is step 3 of the read path
and step 3 of compaction. because newer writes are always found before older
ones (memtable before Level 0, Level 0 newest-file-first, and lower-numbered
levels before higher-numbered ones), a key's most recent write, or its most
recent tombstone, always wins a lookup, even though older, shadowed versions
of the same key may still physically exist on disk until a later compaction
reclaims the space they occupy.

## 8. Implementation variants

**Level compaction (leveled).** Each level above Level 0 has non-overlapping
key ranges and a size roughly ten times the level above it; compaction
repeatedly folds a subset of one level into the next. This bounds space
amplification tightly, typically to roughly 1.1x the live data size once
steady state is reached, at the cost of higher write amplification, because
a single byte can be rewritten once per level it passes through. RocksDB's
own tuning guide names level compaction as its default, describing it as
balancing read and write amplification "reasonably well for typical
workloads"
([RocksDB Tuning Guide](https://github.com/facebook/rocksdb/wiki/RocksDB-Tuning-Guide),
verified 2026-08-02).

**Size-tiered compaction (tiering).** SSTables of roughly similar size are
grouped and merged together into a new, larger SSTable once enough of them
accumulate at a given size tier, rather than being folded into a
strictly-larger next level. Cassandra's and ScyllaDB's Size-Tiered
Compaction Strategy (STCS) is the reference implementation of this variant;
ScyllaDB's documentation states its premise is to "merge SSTables of
approximately the same size," yielding "a low and logarithmic... number of
SSTables" while copying "the same data... a fairly low number of times"
during compaction
([ScyllaDB compaction strategies, via WebSearch summary](https://docs.scylladb.com/manual/stable/architecture/compaction/compaction-strategies.html),
verified 2026-08-02). Tiering generally lowers write amplification relative
to leveling but raises both read amplification (more overlapping files to
check per read) and, transiently, space amplification (up to roughly 2x
during a large tier merge, since old and new copies coexist until the merge
completes).

**Time-window compaction (TWCS).** A tiering variant specialized for
time-series data with a natural expiry, most notably in Cassandra and
ScyllaDB. Data is grouped into fixed time windows; SSTables within an
active window are compacted using size-tiered logic, and once a window
closes, all of its SSTables are merged into a single, final SSTable for that
window, which is never touched again except for whole-window deletion when
the retention period (a TTL) expires. This variant trades general-purpose
read efficiency for extremely cheap, whole-file expiry, avoiding the need to
compact-and-rewrite expired data at all.

**Universal compaction.** A tiering-family strategy in RocksDB explicitly
designed, per the project's own tuning guide, to "decrease write
amplification" for write-heavy workloads at the cost of increased read and
space amplification relative to level compaction
([RocksDB Tuning Guide](https://github.com/facebook/rocksdb/wiki/RocksDB-Tuning-Guide),
verified 2026-08-02). It is the recommended choice when write throughput is
the dominant constraint and the working set fits comfortably enough in
memory or fast storage that the extra read cost is tolerable.

**FIFO compaction.** The narrowest variant. no key-based merging at all.
SSTables are dropped wholesale, oldest first, once the total data size
exceeds a configured cap, or once a per-file age exceeds a TTL. This is used
for pure caching or short-retention-window workloads (an event buffer, a
metrics ring buffer) where the data has no long-term value and the cost of
any real compaction is pure waste. RocksDB documents this as an available
compaction style for exactly this class of workload
([RocksDB Tuning Guide](https://github.com/facebook/rocksdb/wiki/RocksDB-Tuning-Guide),
verified 2026-08-02).

**Key-value separation (WiscKey-style).** A structural variant, not a
compaction-strategy variant, in which large values are stored in a separate,
append-only value log, and the LSM tree itself indexes only keys plus a
pointer into that log. This shrinks the amount of data compaction has to
rewrite (since values are never physically moved by an LSM-level compaction)
at the cost of an extra indirection on read and a separate garbage
collection process for the value log. RocksDB's BlobDB and the standalone
WiscKey research design are the reference implementations of this idea.

**Language-idiomatic notes.** The pattern itself is not language-specific;
it is a storage-engine architecture, most often consumed through a library
(RocksDB, LevelDB) rather than reimplemented per project. Where a language
changes the shape is mainly in how the memtable's sorted structure and the
compaction scheduler are expressed. a garbage-collected language (Java, Go)
typically leans on a concurrent skip list from its standard or common
library for the memtable, and a background goroutine or thread pool for
compaction; a systems language (Rust, C++) more often hand-rolls a
lock-free or fine-grained-locked skip list to avoid GC pause interaction
with the hot write path, which is precisely why RocksDB, itself written in
C++, is embedded into so many other-language systems rather than
reimplemented natively.

## 9. Known production uses

- **RocksDB** (Facebook/Meta, forked from LevelDB), an embeddable
  persistent key-value store built as an LSM tree, is used as the storage
  engine inside MySQL (MyRocks), CockroachDB, TiDB, Kafka Streams'
  state stores, and Facebook's own internal services; Facebook's FAST 2021
  paper documents its production deployment and the priorities that shaped
  its compaction and tuning work over roughly a decade of operation (Dong,
  Kryczka, Jin, and Stumm, "Evolution of Development Priorities in
  Key-value Stores Serving Large-scale Applications. The RocksDB
  Experience," FAST 21, 2021, pages 33 to 49, cross-referenced via
  [WebSearch summary](https://www.usenix.org/conference/fast21/presentation/dong),
  verified 2026-08-02).
- **LevelDB** (Google), the original open-source implementation that
  established the SSTable-plus-manifest-plus-level structure most later
  systems copied, documented in the project's own implementation notes
  describing its level sizing (roughly 10 MB for level 1, growing by a
  factor of ten per level) and its MANIFEST-based metadata design
  ([LevelDB implementation notes](https://github.com/google/leveldb/blob/main/doc/impl.md),
  verified 2026-08-02).
- **Apache Cassandra**, whose storage engine writes to a memtable and an
  append-only commit log, flushes to immutable SSTables, and compacts them
  under a choice of Size-Tiered, Leveled, Time-Window, or Unified
  Compaction Strategy, documented in the project's own operations manual
  listing these four strategies as first-class, user-selectable options
  ([Apache Cassandra compaction documentation](https://cassandra.apache.org/doc/latest/cassandra/managing/operating/compaction/index.html),
  verified 2026-08-02).
- **ScyllaDB**, a Cassandra-API-compatible database reimplemented in C++,
  which documents the same LSM two-region design (an in-memory MemTable
  flushed to immutable, persistent, ordered SSTable files, merged by a
  background compaction process) and offers Size-Tiered, Leveled,
  Time-Window, and Incremental Compaction Strategy as configurable options,
  per its own architecture documentation
  ([ScyllaDB compaction strategies, via WebSearch summary](https://docs.scylladb.com/manual/stable/architecture/compaction/compaction-strategies.html),
  verified 2026-08-02).

## 10. Consequences

Positive.

- Write throughput scales close to the sequential I/O limit of the
  underlying storage device, because every write is an append to an
  in-memory structure and a log, never a random-access mutation of an
  on-disk page, regardless of how randomly the key space is touched.
- Space efficiency on disk is generally good relative to in-place
  structures with fragmentation, because SSTables are written once, fully
  packed, and can apply compression per block during compaction with no
  need to leave slack space for future in-place growth the way a B-tree
  page often must.
- The immutability of SSTables makes several operational tasks simpler than
  they would be against a mutable structure. point-in-time backups can be
  hard-linked file copies rather than a consistent snapshot mechanism,
  replication can ship whole immutable files rather than diff mutable
  pages, and concurrent readers never need to coordinate with an in-place
  writer over the same on-disk bytes.
- Compaction is a natural place to apply compression, garbage-collect
  tombstones, and reclaim space from deleted or superseded data, all as a
  background process that does not compete with foreground write latency
  the way in-place page compaction in a B-tree can.

Negative.

- Read amplification is inherently higher than a comparably sized B-tree in
  the worst case, because a lookup may need to consult several SSTables
  across several levels before finding, or definitively failing to find, a
  key, even with Bloom filters reducing most of that cost in practice.
- Write amplification is real and, if left untuned, can be severe. the same
  logical write is physically rewritten by every compaction pass it is
  swept up in as it descends through the levels, and the RocksDB tuning
  guide's own worked example shows a 3x amplification factor as a
  representative, not extreme, figure
  ([RocksDB Tuning Guide](https://github.com/facebook/rocksdb/wiki/RocksDB-Tuning-Guide),
  verified 2026-08-02).
- Space amplification between compactions can transiently exceed the live
  data size by a significant multiple, particularly under size-tiered
  strategies during a large tier merge, or under any strategy when deletes
  and overwrites are frequent and compaction has not yet caught up.
- Compaction consumes CPU and I/O bandwidth that competes directly with
  foreground traffic, and an under-provisioned or misconfigured compaction
  schedule is the single most common root cause of both latency spikes and
  eventual write stalls in production LSM deployments (dimension 11
  develops this in detail).
- Range scans and full-key-space traversals are more expensive than on a
  B+-tree with physically ordered leaves, because the scan must merge
  iterators across every level rather than walk one ordered structure.
- Tombstones (delete markers) are themselves writes, occupy space, and must
  survive in the tree until compaction can prove no shadowed value remains
  beneath them; a delete-heavy or a write-then-immediately-overwrite-heavy
  workload can accumulate tombstones faster than compaction reclaims them,
  degrading both read latency and space usage, a well-documented Cassandra
  operational failure mode.

## 11. Failure modes and misuse

Symptom, cause, fix, presented as observable triples.

**Symptom.** Write latency, previously sub-millisecond, suddenly spikes to
hundreds of milliseconds or seconds, and the database logs mention "stall"
or "stopping writes."
**Cause.** Level 0 has accumulated more SSTable files than the engine's
configured safety threshold (RocksDB's `level0_slowdown_writes_trigger` and
`level0_stop_writes_trigger` are the canonical knobs), typically because
compaction throughput fell behind write throughput, either from an I/O
bandwidth shortage, a compaction thread-pool that is too small, or a burst
of writes that outran the compaction scheduler's steady-state assumptions.
**Fix.** Provision more compaction I/O and CPU headroom ahead of peak load
rather than at the average; raise the Level 0 file-count thresholds only as
a temporary release valve, since raising them permanently just relocates
the read-amplification cost the thresholds exist to bound; and, for
recurring bursts, consider a compaction style (universal, size-tiered) that
prioritizes write throughput over the read and space costs level
compaction optimizes for.

**Symptom.** Disk usage grows well beyond the size of the logically live
data, sometimes two to four times over, even though the application deletes
or overwrites records regularly.
**Cause.** Compaction has not caught up with the rate of overwrites and
deletes, so multiple superseded versions of the same keys, and unreclaimed
tombstones, coexist on disk; this is especially common under size-tiered
strategies, which defer merging longer than leveled strategies by design,
and under any strategy when compaction has been throttled to protect
foreground latency.
**Fix.** Trigger a manual major (full) compaction if the engine supports one
and the resulting I/O spike is tolerable during a low-traffic window;
increase steady-state compaction priority or bandwidth so the backlog
does not recur; and, for delete-heavy workloads, consider a TTL-based or
time-windowed compaction strategy that can drop entire expired SSTables
without a key-by-key merge.

**Symptom.** Point-lookup latency degrades gradually over weeks or months
even though write volume and data size are roughly stable.
**Cause.** SSTable count at one or more levels has crept upward because
compaction thresholds were tuned for an earlier, smaller data volume, or
because a Bloom filter's false-positive rate has risen (commonly from an
under-sized filter relative to the actual key count), causing more SSTables
to be opened and checked per lookup than the filter should allow.
**Fix.** Re-tune level size multipliers and Bloom filter bits-per-key for
the current data volume rather than the volume the system was originally
sized for; monitor and alert on read amplification (files touched per
lookup) as a first-class metric, not only on raw latency, so the underlying
cause is visible before latency crosses a user-facing threshold.

**Symptom.** A single very large or very hot key range causes uneven
compaction load, with one compaction thread or shard perpetually behind
while others are idle.
**Cause.** Key distribution is not actually uniform across the range each
level or shard owns, so range-based level partitioning concentrates
compaction work unevenly; this is a form of hot-partition skew, the same
underlying problem the Sharding pattern in this catalog addresses at the
cluster level, surfacing instead inside a single node's compaction
scheduler.
**Fix.** Re-partition or re-shard the key space so ranges are more evenly
sized in write volume, not just in key-count; some engines support
sub-range or dynamic-level splitting to rebalance without a full
re-shard, which should be preferred when available since it avoids an
application-level migration.

**Symptom.** After a crash, the database either loses recent writes it had
already acknowledged, or takes an unexpectedly long time to recover.
**Cause.** The write-ahead log was not fsynced on acknowledgment (a
throughput-over-durability configuration choice) so writes acknowledged
just before the crash never reached stable storage; or, on the recovery
side, an unusually large volume of unflushed WAL accumulated because the
memtable flush interval was tuned too loosely, so recovery must replay a
large log before the database can serve traffic.
**Fix.** Align the WAL fsync policy with the durability guarantee the
application actually promises callers, group-commit if per-write fsync
cost is the concern rather than silently disabling fsync; and bound
memtable size and flush frequency so WAL replay time after a crash stays
within an acceptable recovery-time objective.

**Misuse.** Treating an LSM-backed store as if it had B-tree read
characteristics and building a schema or access pattern that depends on
many small, random point reads across a cold, rarely-compacted key range
(a common mistake when migrating from a relational database without
re-profiling read latency), which produces read amplification the original
schema's designer never priced in because the mental model carried over
from the prior storage engine did not transfer.

## 12. Trade-off matrix

Compared against named alternatives across the forces from dimension 3.

| Force | LSM tree (level compaction) | B-tree / B+-tree | Hash index (in-memory or on-disk) | LSM tree (size-tiered) |
|---|---|---|---|---|
| Random write throughput | High, near sequential-I/O limit | Low to moderate, one random page write per key | Very high for in-memory, moderate on-disk | High, generally higher than level compaction |
| Point read latency | Moderate, several potential SSTable checks, mitigated by Bloom filters | Low and predictable, fixed by tree height | Very low, O(1) average | Higher than level compaction, more SSTables per level typically |
| Range scan performance | Moderate, multi-level merge iterator required | High, single ordered traversal | Poor to none, no natural ordering | Lower than level compaction, more files to merge |
| Write amplification | Moderate to high, bytes rewritten at each level traversed | Low per write, but random-write cost dominates instead | Low | Lower than level compaction by design |
| Space amplification | Low in steady state, roughly 1.1x live data | Low, minus page fragmentation slack | Low for on-disk, higher for chained/open-addressed variants under load | Higher, transient spikes toward 2x during large tier merges |
| Delete/tombstone handling | Deferred to compaction, bounded by level descent | Immediate, in-place removal | Immediate for most implementations | Deferred, can lag further than level compaction |
| Operational complexity | Higher, requires compaction monitoring and tuning | Lower, no background rewrite process to manage | Lower for the index itself, but on-disk variants add their own concerns | Similar to level compaction, different tuning knobs |
| Best-suited workload | Write-heavy with tolerant read latency requirements | Read-heavy or balanced with strong range-scan needs | Point-lookup-only, no range queries needed | Write-throughput-critical, read latency less critical |

## 13. Related and incompatible patterns

**Write-Ahead Log.** The LSM tree's durability guarantee is provided
entirely by its write-ahead log; the memtable itself is volatile and
reconstructed from the WAL after a crash. Any tuning of WAL fsync behavior
directly changes the LSM tree's durability-versus-latency trade-off
described in dimension 3, and the general pattern, its failure modes, and
its own trade-offs are covered in the write-ahead-log entry in this
catalog rather than repeated here.

**Bloom Filter.** Nearly every production LSM implementation attaches a
Bloom filter to each SSTable so that a point lookup can skip files that
provably do not contain the key, without which read amplification would be
far worse than the figures cited in dimension 10. The Bloom filter's own
false-positive-rate-versus-memory trade-off compounds with the LSM tree's
own read-amplification-versus-write-amplification trade-off, so tuning one
in isolation from the other under-serves the workload.

**Sharding.** LSM trees solve the single-node write-throughput problem;
they do not by themselves solve the problem of a workload that exceeds any
single node's total I/O or storage capacity. Distributed systems built on
LSM storage engines (Cassandra, ScyllaDB, CockroachDB on RocksDB) combine
the LSM tree per node with sharding across nodes, and the hot-key-range
compaction imbalance described in dimension 11 is frequently a symptom of
sharding decisions made without accounting for how they interact with
per-node compaction load.

**Event Sourcing and CQRS.** Both patterns favor an append-heavy write
model with derived, queryable read structures built asynchronously from
that append log, which is structurally analogous to how an LSM tree
separates its append-oriented write path (memtable, WAL) from its
compaction-derived, queryable read structure (leveled SSTables). Systems
that already lean on event sourcing at the application layer often find an
LSM-backed store a natural fit underneath it, though the two are
independent choices at different layers and neither requires the other.

**Incompatible or in tension with.** In-place update assumptions found in
some replication or backup tooling that expects to diff a mutable file
byte-range rather than ship whole immutable files; and any consistency
model that assumes a read strictly reflects the most recently completed
write with no possibility of a compaction-in-progress view, which most LSM
implementations do provide correctly via manifest versioning, but which
custom tooling built against the raw on-disk files, bypassing the engine's
own read path, can violate if it is not careful about which manifest
version it reads against.

## 14. Refactoring path in and out

Introducing an LSM tree into a system that currently uses a B-tree-backed
store, step by step.

1. Profile the current write path to confirm the bottleneck is genuinely
   random-write I/O rather than something upstream (lock contention,
   application-level serialization cost, network); introducing an LSM tree
   does not help a bottleneck that is not actually about storage I/O
   pattern.
2. Choose an embeddable LSM engine appropriate to the language and
   deployment (RocksDB has bindings for most major languages; native
   options exist per ecosystem) rather than hand-rolling one, for the same
   reason this catalog generally favors adopting a proven implementation
   of any nontrivial pattern over reimplementing it.
3. Introduce the LSM-backed store behind the existing data-access
   interface, running it alongside the B-tree store in shadow mode first
   (dual-write, read from the old store, compare against the new store) to
   validate correctness under real traffic before it serves any live
   reads.
4. Migrate the read path over incrementally, monitoring point-read and
   range-scan latency against the previous baseline, since read
   characteristics are the dimension most likely to regress.
5. Tune compaction strategy and level sizing against the real production
   workload's write-to-read ratio and key distribution, not against
   default settings tuned for a generic benchmark; defaults are a starting
   point, not a destination.
6. Retire the old B-tree store's write path once the new store has run at
   full read and write traffic for long enough to observe at least one
   full compaction cycle at every level under real load.

Removing an LSM tree once it no longer earns its place, for example
when write volume has fallen enough that a simpler structure would serve
the workload with less operational overhead.

1. Confirm the write-to-read ratio and key-distribution assumptions that
   originally motivated the LSM tree no longer hold, rather than assuming
   they do not; a temporary lull in write traffic is not the same as a
   permanent shift in the workload.
2. Evaluate whether the operational cost being avoided (compaction
   monitoring, the failure modes in dimension 11) genuinely outweighs the
   write-throughput headroom being given up, since headroom often matters
   again at the next growth spike even if the current traffic does not
   need it.
3. If removal is warranted, migrate to the simpler structure the same way
   as the introduction path in reverse. shadow-write to the new store,
   validate, cut reads over incrementally, then retire the LSM-backed
   write path only after the new store has proven itself under full
   production load.

## 15. Testing and verification

What becomes easier to test because of this pattern. SSTables are
immutable, so any test that reads a specific SSTable file can rely on its
contents never changing underneath the test, which makes fixture-based unit
tests of the read path (given these specific SSTable files, does a lookup
for key K return the right value) straightforward and deterministic, with
no need to guard against concurrent mutation of the file under test.
Compaction logic itself is a pure function of its inputs (a set of SSTables
in, a merged set of SSTables out) and can be tested in isolation from the
rest of the engine by constructing synthetic SSTables with known,
overlapping key ranges and verifying the merged output has the correct
newest-wins semantics and correctly drops eligible tombstones.

What becomes harder. End-to-end correctness under concurrent compaction and
foreground traffic is genuinely difficult to test deterministically,
because the interleaving of a flush, a compaction, and a concurrent read or
write is exactly the kind of race that unit tests structurally cannot
exercise well; this calls for property-based or randomized concurrency
testing (fuzzing the interleaving of operations against a reference model
that tracks the expected key-value state) rather than example-based tests
alone, and several production LSM implementations, including RocksDB, ship
internal stress-test harnesses for exactly this reason. Crash-consistency
testing, verifying the database recovers correctly after a simulated crash
at an arbitrary point during a WAL append, a memtable flush, or a
compaction's manifest update, similarly needs dedicated fault-injection
tooling (killing the process or truncating files at controlled points)
rather than conventional unit tests, since the property under test is
specifically about behavior across an ungraceful termination.

Test doubles that apply. An in-memory-only LSM implementation (skipping the
WAL and using a plain in-memory sorted map with no compaction) is a useful
test double for exercising application logic that sits above the storage
engine, when the test's purpose is to validate application behavior rather
than storage-engine behavior itself; it should never be used to validate
anything about durability, compaction correctness, or read/write
amplification, since it has none of those properties.

## 16. Observability signals

A healthy LSM-backed store, on a dashboard, shows write latency stable and
low with no stall events; Level 0 file count oscillating within its
configured bounds rather than trending upward over time; compaction
throughput (bytes compacted per second) tracking write throughput closely
enough that a backlog is not accumulating; read amplification (average
number of SSTables or blocks touched per point lookup) stable rather than
climbing; and space amplification (on-disk size divided by estimated live
data size) holding near its steady-state expectation for the chosen
compaction strategy, roughly 1.1x for level compaction, higher and more
variable for size-tiered.

Signals that indicate an unhealthy instance include Level 0 file count
climbing without bound, the leading indicator of a compaction backlog well
before write stalls actually trigger; a growing gap between the rate of
bytes written by the application and the rate of bytes written to disk by
compaction, which quantifies write amplification directly and flags when
it has drifted from its expected steady-state value; pending-compaction
bytes (the total size of data queued for compaction but not yet processed)
trending upward across multiple measurement windows rather than
oscillating around a stable value; a rising Bloom filter false-positive
rate, which shows up as more SSTables being opened per lookup than the
filter should allow and is often the first symptom of the filter being
under-sized for the current key cardinality; and WAL replay time after a
restart trending upward, which signals memtable flush intervals have
drifted too loose for the current write volume and directly threatens
recovery-time objectives. Production implementations of RocksDB expose
most of these as first-class statistics (level file counts, compaction
bytes read and written, Bloom filter hit and miss counters) specifically
because the tuning guide's own worked examples depend on being able to
observe write and read amplification directly rather than infer them
([RocksDB Tuning Guide](https://github.com/facebook/rocksdb/wiki/RocksDB-Tuning-Guide),
verified 2026-08-02).

## 17. Security and privacy implications

An LSM tree's immutability and deferred-compaction design has a direct
privacy consequence that is easy to overlook. A deleted or overwritten
value is not physically erased from disk at the moment the application
issues the delete or the overwrite. It persists in one or more older
SSTables, marked shadowed or tombstoned but not yet reclaimed, until a
compaction pass physically merges past it and discards it. For a system
under a data-deletion obligation (a right-to-erasure request under GDPR,
for example, or a contractual data-retention limit), "the application
issued a delete" is not equivalent to "the data no longer exists on any
disk the operator controls" until the relevant compaction has actually
completed, which can be minutes, hours, or in a lazily-compacted or
size-tiered system, potentially much longer, after the logical delete.
Systems with a hard deletion-timing requirement need either an explicit,
monitored process that confirms compaction has physically reclaimed the
target data (not merely that the delete or tombstone was written), or a
compaction strategy and forced-compaction schedule tuned specifically to
bound how long shadowed data can persist, rather than relying on the
default steady-state compaction cadence a throughput-tuned system would
otherwise use.

A second, related implication concerns backup and snapshot mechanisms that
exploit SSTable immutability by hard-linking or directly copying on-disk
files. A backup taken this way can capture SSTables containing data that
was logically deleted from the live database before the backup was taken
but had not yet been physically reclaimed by compaction, meaning the
backup itself becomes a copy of data the operator believed was gone. Backup
retention and access-control policy needs to account for this, treating
LSM-backed backups as potentially containing pre-deletion data for as long
as the backup itself is retained, independent of what the live database
currently reports.

Beyond deletion timing, an LSM tree introduces no meaningfully new attack
surface of its own relative to any other on-disk key-value storage engine.
Standard concerns, encryption at rest for the SSTable and WAL files,
access control on the files and on the database's network interface, and
secure handling of any encryption keys used for those files, apply
identically to LSM-backed storage as to any other persistent storage
mechanism, and this entry does not identify any LSM-specific concern beyond
the deletion-timing issue above.

## Code examples

Each sample below builds a minimal LSM tree with an in-memory memtable, a
size-based flush into an immutable sorted SSTable, and a leveled-compaction
step triggered once a level holds more SSTables than its configured fanout
allows. Deletes are represented with a tombstone (`None` in Python, an
`Option<String>` of `None` in Rust, a boolean flag in Go) rather than a
physical removal, matching the real semantics described in dimensions 6, 7,
and 10. Every sample was compiled or run directly against the toolchain
listed in the repository's available-toolchains table before this entry was
submitted.

```python
"""Minimal LSM tree. memtable, flush to sorted SSTable, leveled compaction."""
from bisect import bisect_left
from dataclasses import dataclass, field

TOMBSTONE = object()


@dataclass
class SSTable:
    entries: list  # sorted list of (key, value_or_tombstone)

    def get(self, key):
        keys = [k for k, _ in self.entries]
        i = bisect_left(keys, key)
        if i < len(keys) and keys[i] == key:
            return self.entries[i][1]
        return None


@dataclass
class LSMTree:
    memtable_limit: int = 4
    level_fanout: int = 2
    memtable: dict = field(default_factory=dict)
    levels: list = field(default_factory=list)  # levels[0] newest-first

    def put(self, key: str, value: str) -> None:
        self.memtable[key] = value
        if len(self.memtable) >= self.memtable_limit:
            self._flush()

    def delete(self, key: str) -> None:
        self.memtable[key] = TOMBSTONE
        if len(self.memtable) >= self.memtable_limit:
            self._flush()

    def _flush(self) -> None:
        entries = sorted(self.memtable.items())
        table = SSTable(entries=entries)
        if not self.levels:
            self.levels.append([])
        self.levels[0].insert(0, table)  # newest first within level 0
        self.memtable = {}
        self._maybe_compact(0)

    def _maybe_compact(self, level: int) -> None:
        if level >= len(self.levels):
            return
        capacity = self.level_fanout ** (level + 1)
        if len(self.levels[level]) <= capacity:
            return
        merged: dict = {}
        for table in reversed(self.levels[level]):
            for k, v in table.entries:
                merged[k] = v
        self.levels[level] = []
        if level + 1 >= len(self.levels):
            self.levels.append([])
        self.levels[level + 1].append(SSTable(entries=sorted(merged.items())))
        self._maybe_compact(level + 1)

    def get(self, key: str):
        if key in self.memtable:
            v = self.memtable[key]
            return None if v is TOMBSTONE else v
        for level in self.levels:
            for table in level:
                v = table.get(key)
                if v is not None:
                    return None if v is TOMBSTONE else v
        return None


def main() -> None:
    tree = LSMTree(memtable_limit=4, level_fanout=2)
    for i in range(12):
        tree.put(f"key{i}", f"value{i}")
    tree.put("key3", "value3-updated")
    tree.delete("key5")

    assert tree.get("key3") == "value3-updated"
    assert tree.get("key5") is None
    assert tree.get("key0") == "value0"
    assert tree.get("missing") is None
    print("lsm tree ok, levels:", [len(l) for l in tree.levels])


if __name__ == "__main__":
    main()
```

```go
package main

import (
	"fmt"
	"sort"
)

type entry struct {
	key       string
	value     string
	tombstone bool
}

type sstable struct {
	entries []entry
}

func (s *sstable) get(key string) (entry, bool) {
	i := sort.Search(len(s.entries), func(i int) bool { return s.entries[i].key >= key })
	if i < len(s.entries) && s.entries[i].key == key {
		return s.entries[i], true
	}
	return entry{}, false
}

type lsmTree struct {
	memtableLimit int
	levelFanout   int
	memtable      map[string]entry
	levels        [][]*sstable
}

func newLSMTree(memtableLimit, levelFanout int) *lsmTree {
	return &lsmTree{
		memtableLimit: memtableLimit,
		levelFanout:   levelFanout,
		memtable:      make(map[string]entry),
	}
}

func (t *lsmTree) put(key, value string) {
	t.memtable[key] = entry{key: key, value: value}
	if len(t.memtable) >= t.memtableLimit {
		t.flush()
	}
}

func (t *lsmTree) delete(key string) {
	t.memtable[key] = entry{key: key, tombstone: true}
	if len(t.memtable) >= t.memtableLimit {
		t.flush()
	}
}

func (t *lsmTree) flush() {
	entries := make([]entry, 0, len(t.memtable))
	for _, e := range t.memtable {
		entries = append(entries, e)
	}
	sort.Slice(entries, func(i, j int) bool { return entries[i].key < entries[j].key })
	table := &sstable{entries: entries}
	if len(t.levels) == 0 {
		t.levels = append(t.levels, nil)
	}
	t.levels[0] = append([]*sstable{table}, t.levels[0]...)
	t.memtable = make(map[string]entry)
	t.maybeCompact(0)
}

func (t *lsmTree) maybeCompact(level int) {
	if level >= len(t.levels) {
		return
	}
	capacity := 1
	for i := 0; i <= level; i++ {
		capacity *= t.levelFanout
	}
	if len(t.levels[level]) <= capacity {
		return
	}
	merged := make(map[string]entry)
	for i := len(t.levels[level]) - 1; i >= 0; i-- {
		for _, e := range t.levels[level][i].entries {
			merged[e.key] = e
		}
	}
	t.levels[level] = nil
	if level+1 >= len(t.levels) {
		t.levels = append(t.levels, nil)
	}
	out := make([]entry, 0, len(merged))
	for _, e := range merged {
		out = append(out, e)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].key < out[j].key })
	t.levels[level+1] = append(t.levels[level+1], &sstable{entries: out})
	t.maybeCompact(level + 1)
}

func (t *lsmTree) get(key string) (string, bool) {
	if e, ok := t.memtable[key]; ok {
		if e.tombstone {
			return "", false
		}
		return e.value, true
	}
	for _, level := range t.levels {
		for _, table := range level {
			if e, ok := table.get(key); ok {
				if e.tombstone {
					return "", false
				}
				return e.value, true
			}
		}
	}
	return "", false
}

func main() {
	tree := newLSMTree(4, 2)
	for i := 0; i < 12; i++ {
		tree.put(fmt.Sprintf("key%d", i), fmt.Sprintf("value%d", i))
	}
	tree.put("key3", "value3-updated")
	tree.delete("key5")

	if v, ok := tree.get("key3"); !ok || v != "value3-updated" {
		panic("key3 mismatch")
	}
	if _, ok := tree.get("key5"); ok {
		panic("key5 should be deleted")
	}
	if v, ok := tree.get("key0"); !ok || v != "value0" {
		panic("key0 mismatch")
	}
	if _, ok := tree.get("missing"); ok {
		panic("missing should not be found")
	}
	fmt.Println("lsm tree ok, levels:", len(tree.levels))
}
```

```rust
use std::collections::HashMap;

#[derive(Clone)]
struct Entry {
    key: String,
    value: Option<String>, // None means tombstone
}

struct SSTable {
    entries: Vec<Entry>, // sorted by key
}

impl SSTable {
    fn get(&self, key: &str) -> Option<&Entry> {
        match self.entries.binary_search_by(|e| e.key.as_str().cmp(key)) {
            Ok(i) => Some(&self.entries[i]),
            Err(_) => None,
        }
    }
}

struct LsmTree {
    memtable_limit: usize,
    level_fanout: usize,
    memtable: HashMap<String, Entry>,
    levels: Vec<Vec<SSTable>>,
}

impl LsmTree {
    fn new(memtable_limit: usize, level_fanout: usize) -> Self {
        LsmTree {
            memtable_limit,
            level_fanout,
            memtable: HashMap::new(),
            levels: Vec::new(),
        }
    }

    fn put(&mut self, key: &str, value: &str) {
        self.memtable.insert(
            key.to_string(),
            Entry { key: key.to_string(), value: Some(value.to_string()) },
        );
        if self.memtable.len() >= self.memtable_limit {
            self.flush();
        }
    }

    fn delete(&mut self, key: &str) {
        self.memtable.insert(
            key.to_string(),
            Entry { key: key.to_string(), value: None },
        );
        if self.memtable.len() >= self.memtable_limit {
            self.flush();
        }
    }

    fn flush(&mut self) {
        let mut entries: Vec<Entry> = self.memtable.values().cloned().collect();
        entries.sort_by(|a, b| a.key.cmp(&b.key));
        let table = SSTable { entries };
        if self.levels.is_empty() {
            self.levels.push(Vec::new());
        }
        self.levels[0].insert(0, table);
        self.memtable.clear();
        self.maybe_compact(0);
    }

    fn maybe_compact(&mut self, level: usize) {
        if level >= self.levels.len() {
            return;
        }
        let capacity = self.level_fanout.pow((level + 1) as u32);
        if self.levels[level].len() <= capacity {
            return;
        }
        let mut merged: HashMap<String, Entry> = HashMap::new();
        for table in self.levels[level].iter().rev() {
            for e in &table.entries {
                merged.insert(e.key.clone(), e.clone());
            }
        }
        self.levels[level].clear();
        if level + 1 >= self.levels.len() {
            self.levels.push(Vec::new());
        }
        let mut out: Vec<Entry> = merged.into_values().collect();
        out.sort_by(|a, b| a.key.cmp(&b.key));
        self.levels[level + 1].push(SSTable { entries: out });
        self.maybe_compact(level + 1);
    }

    fn get(&self, key: &str) -> Option<String> {
        if let Some(e) = self.memtable.get(key) {
            return e.value.clone();
        }
        for level in &self.levels {
            for table in level {
                if let Some(e) = table.get(key) {
                    return e.value.clone();
                }
            }
        }
        None
    }
}

fn main() {
    let mut tree = LsmTree::new(4, 2);
    for i in 0..12 {
        tree.put(&format!("key{}", i), &format!("value{}", i));
    }
    tree.put("key3", "value3-updated");
    tree.delete("key5");

    assert_eq!(tree.get("key3"), Some("value3-updated".to_string()));
    assert_eq!(tree.get("key5"), None);
    assert_eq!(tree.get("key0"), Some("value0".to_string()));
    assert_eq!(tree.get("missing"), None);
    println!("lsm tree ok, levels: {}", tree.levels.len());
}
```

Java, C#, and Kotlin are omitted deliberately rather than silently. The
pattern's essential shape, an in-memory sorted structure flushed to an
immutable file with a background merge step, is fully captured by the three
samples above, and a fourth or fifth translation would add length without
adding a new idea; real production LSM engines in the JVM ecosystem
(Cassandra, HBase) are themselves large, long-lived C++ or Java codebases
consumed as a dependency rather than reimplemented per project, which is the
same point made in dimension 8's language-idiomatic notes.

## 18. References

- Patrick E. O'Neil, Edward Cheng, Dieter Gawlick, and Elizabeth J. O'Neil,
  "The Log-Structured Merge-Tree (LSM-Tree)," Acta Informatica, volume 33,
  issue 4, 1996, pages 351 to 385, cross-referenced via
  https://dblp.org/rec/journals/acta/ONeilCGO96.html, verified 2026-08-02.
- Siying Dong, Andrew Kryczka, Yanqin Jin, and Michael Stumm, "Evolution of
  Development Priorities in Key-value Stores Serving Large-scale
  Applications. The RocksDB Experience," 19th USENIX Conference on File
  and Storage Technologies (FAST 21), 2021, pages 33 to 49, cross-referenced
  via https://www.usenix.org/conference/fast21/presentation/dong, verified
  2026-08-02.
- RocksDB project, "RocksDB Tuning Guide," GitHub wiki,
  https://github.com/facebook/rocksdb/wiki/RocksDB-Tuning-Guide, verified
  2026-08-02.
- LevelDB project, "LevelDB Implementation Notes,"
  https://github.com/google/leveldb/blob/main/doc/impl.md, verified
  2026-08-02.
- Apache Cassandra project, "Compaction," Cassandra documentation,
  https://cassandra.apache.org/doc/latest/cassandra/managing/operating/compaction/index.html,
  verified 2026-08-02.
- ScyllaDB project, "Choose a Compaction Strategy," ScyllaDB documentation,
  https://docs.scylladb.com/manual/stable/architecture/compaction/compaction-strategies.html,
  verified 2026-08-02.
- Niv Dayan, Manos Athanassoulis, and Stratos Idreos, "Monkey. Optimal
  Navigable Key-Value Store," Proceedings of the 2017 ACM International
  Conference on Management of Data (SIGMOD 2017), engineering-judgement
  cross-reference only, cited for the formal tiering-versus-leveling cost
  model discussed in the literature; not independently re-verified for
  this entry beyond confirming the paper's existence and venue via
  standard bibliographic search, 2026-08-02.
