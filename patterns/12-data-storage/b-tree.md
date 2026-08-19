---
name: B-Tree
slug: b-tree
family: 12-data-storage
category: Data Structure
aliases: [Balanced Tree, Multiway Search Tree, B+Tree (variant)]
first_described: "Bayer, McCreight 1972"
maturity: canonical
related: [lsm-tree, skip-list, hash-index, write-ahead-log, buffer-pool]
incompatible_with: []
verified: 2026-08-02
---

# B-Tree

## 1. Name, aliases, and lineage

The canonical name is B-Tree. Rudolf Bayer and Edward M. McCreight described the
structure in "Organization and Maintenance of Large Ordered Indices", Boeing
Scientific Research Laboratories report, published in Acta Informatica volume
1, 1972, pages 173 to 189. The letter B has no agreed meaning. Bayer and
McCreight never state one in the paper, and Douglas Comer's widely cited survey
"The Ubiquitous B-Tree", ACM Computing Surveys, volume 11, issue 2, June 1979,
pages 121 to 137, opens by noting the same ambiguity and lists Boeing, balanced,
and Bayer as the three candidate readings people commonly propose. Comer's
survey is itself the paper that made the structure a standard part of the
database and file system curriculum, and it is the source most later textbooks
cite for the canonical presentation of insertion and deletion.

The plain term B-Tree is used loosely in industry to mean several related
structures, and separating them is the first thing a careful reader must do.

- The original Bayer and McCreight structure keeps data records at every node,
  internal and leaf alike. Comer's survey preserves this shape in its
  presentation.
- The B+-tree variant keeps all data records in the leaf level only, uses
  internal nodes purely as a routing index of separator keys, and links the
  leaves together in a singly or doubly linked list for fast ordered scans.
  Almost every production database index that people casually call a B-tree is
  actually a B+-tree, including PostgreSQL, InnoDB, and SQLite, each cited in
  dimension 9 below.
- The B*-tree variant, described in Donald Knuth, *The Art of Computer
  Programming, Volume 3, Sorting and Searching*, 2nd edition, Addison-Wesley,
  1998, section 6.2.4, keeps nodes at least two thirds full instead of one half
  full by redistributing keys between siblings before splitting, trading a more
  complex insert for higher space utilization.

This entry treats the B+-tree as the primary subject because it is the variant
that prevails in real storage engines, and calls out where the original
Bayer-McCreight structure differs.

## 2. Problem and context

A program needs to store an ordered collection of keys that is too large to fit
in memory, and it needs to look up, insert, delete, and range-scan those keys
with a small, predictable number of expensive operations. The expensive
operation is a disk seek or a page fault, and on rotating media in the 1970s a
single seek could cost several milliseconds, which is millions of CPU cycles.
A balanced binary search tree such as a red-black tree gives O(log2 n)
comparisons, but each comparison typically touches a different node, and each
node is a separate, small, randomly placed unit of storage. For a billion
records that is roughly 30 disk seeks per lookup, which at even 5 milliseconds
per seek is 150 milliseconds, an eternity for an interactive system.

The B-tree reframes the problem. Instead of minimizing comparisons, minimize
the number of blocks fetched from disk, and make each fetched block do as much
useful work as possible by packing hundreds of keys into it. A block sized to
match the disk's natural transfer unit, historically 4 or 8 kilobytes and
scaled up to 16 or 32 kilobytes in modern engines, can hold hundreds of keys
and pointers. A tree with branching factor in the hundreds reaches a billion
keys in three or four levels, so a lookup costs three or four disk reads
instead of thirty. This is the context the structure was designed for, and it
remains the context every production use case in dimension 9 shares, namely
slow, block-addressed secondary storage, an ordered key space, and a workload
that mixes point lookups, range scans, and updates.

## 3. Forces

- **I/O count versus fan-out.** A wider node means fewer levels and fewer disk
  reads per operation, but a wider node also means more keys to scan and shift
  within that node once it is in memory. B-trees favour minimizing I/O count
  even at the cost of more in-memory comparison work, because the I/O cost so
  outweighs the alternative that trading CPU cycles for fewer seeks is almost
  always a win on spinning disks, and remains a strong win on SSDs where a
  page-sized read still costs far more than a hundred in-memory comparisons.
- **Write amplification versus read latency.** Every insert or delete keeps the
  tree perfectly balanced by splitting or merging nodes immediately. This gives
  predictable, bounded read latency at all times, but it means a single
  logical write can trigger a page split that itself triggers a parent split,
  continuing upward through the tree. The alternative family, log-structured
  merge trees (see the related-patterns entry), defers this cost by buffering
  writes and merging in batches, trading read amplification and higher read
  tail latency for lower write amplification.
- **Space utilization versus insert simplicity.** A classic B-tree targets at
  least 50 percent node occupancy after a split, guaranteed by the split
  algorithm's halving rule. B*-trees push occupancy to roughly two thirds by
  redistributing to a sibling before splitting, at the cost of a more complex
  insert path that must check and rebalance a neighbour first.
- **Concurrency versus structural simplicity.** A naive implementation locks a
  root-to-leaf path for every write, which serializes all inserts through the
  root. Production engines instead use link-based and latch-coupling
  techniques, most influentially Philip L. Lehman and S. Bing Yao, "Efficient
  Locking for Concurrent Operations on B-Trees", ACM Transactions on Database
  Systems, volume 6, issue 4, December 1981, pages 650 to 670, which adds a
  right-sibling pointer at every level so a reader that catches a node
  mid-split can simply follow that pointer, permitting more concurrent
  operations at the cost of a much more elaborate implementation.
- **Ordered access versus point-lookup speed.** Keeping keys sorted inside
  every node and linking leaves together enables cheap range scans and
  ordered iteration, which a hash index cannot offer at all. This ordering
  guarantee is the reason a B-tree is chosen over a hash table whenever range
  queries, prefix queries, or sorted output matter, even though a hash table
  gives faster expected-case point lookups.

## 4. Applicability and non-applicability

Use a B-tree, in practice almost always its B+-tree variant, when the
following hold.

- The workload needs ordered range scans, prefix scans, or sorted-order output
  alongside point lookups, and an index must serve both from one structure.
- The data set is too large for memory and lives on block-addressed storage,
  whether spinning disk or SSD, where minimizing the number of page fetches
  matters more than minimizing raw comparison count.
- Reads are the majority of the workload, or reads and writes are mixed, and
  read latency must stay bounded and predictable rather than merely good on
  average.
- The engine needs a general-purpose, well-understood index structure with
  decades of production hardening, mature crash-recovery integration through
  write-ahead logging, and known concurrency-control techniques.

Do not use a B-tree, or prefer a named alternative, when any of these hold.

- The workload is overwhelmingly write-heavy with few reads, for example
  time-series ingestion or an append-mostly event log. A log-structured merge
  tree amortizes writes into sequential batches and often achieves several
  times the write throughput of a B-tree on the same hardware for this
  pattern, at the cost of read amplification the workload rarely exercises
  anyway.
- The access pattern is exclusively equality lookup with no need for ordering
  or range scans, and the key space is known in advance or hashable cheaply.
  A hash index gives O(1) expected lookup with none of a B-tree's O(log n)
  comparison and node-traversal overhead, and PostgreSQL ships exactly this
  trade-off as its separate hash index access method for this narrow case.
- The entire data set genuinely fits in memory and never needs to persist to
  block storage. A balanced in-memory tree such as a red-black tree, or an
  in-memory ordered structure such as a skip list, avoids the page-oriented
  overhead a B-tree pays for a disk model it does not need. Skip lists in
  particular are chosen by several production engines, see dimension 9, when
  the memory-only ordered structure must also support very cheap concurrent
  reads without a fixed fan-out to tune.
- The key or value size is large and variable, such that a fixed-size page
  cannot hold enough entries to make a wide fan-out worthwhile. Systems facing
  this either add an overflow-page mechanism, as PostgreSQL does for its
  TOASTed values, or move to a structure designed around variable-length
  records from the start.
- Strict insertion-order preservation, not key-order, is the requirement. A
  B-tree reorders by key. An append-only log or a queue-shaped structure
  preserves arrival order directly and more cheaply.

## 5. Structure

The B+-tree, the variant covered here, has three participant roles.

- **Root node.** The single entry point of the tree. Holds between 1 and
  order minus 1 separator keys and between 2 and order child pointers, where
  order is the maximum fan-out a node is configured to hold. The root is the
  only node permitted to have fewer than the minimum occupancy the invariant
  otherwise demands, because there is nothing above it to merge into.
- **Internal (index) node.** Holds separator keys and child pointers only, no
  data. Each internal node with k keys has k plus 1 children. The separator
  key at position i is chosen so that every key in the subtree rooted at
  child i is less than the separator, and every key in the subtree rooted at
  child i plus 1 is greater than or equal to it. Internal nodes hold no
  payload, which is what lets a fixed-size page hold hundreds of separator
  keys and keeps the tree shallow.
- **Leaf node.** Holds the actual data records, or in an index (as opposed to
  a table-organized store) a key plus a pointer to the record's location in a
  separate heap or table b-tree, as SQLite's file format documentation
  describes for its index b-trees, verified below. Leaves at the same depth
  are linked together, typically in both directions, so that a range scan
  never needs to walk back up to an internal node once it has located the
  starting leaf.

The core structural invariant, stated for a B+-tree of order m, holds four
properties.

- Every node except the root has between ceil(m/2) minus 1 and m minus 1
  keys.
- Every internal node with k keys has exactly k plus 1 children.
- All leaves appear at the same depth. The tree grows and shrinks only at the
  root, which is what gives the O(log n) worst-case bound on every operation.
- Keys within a node are sorted, and keys across sibling subtrees are sorted
  relative to each other, so an in-order traversal of the leaves yields the
  full data set in sorted order.

## 6. ASCII structure diagram

```
                         +-------------------+
                         |  root (internal)  |
                         |   K10   |   K30    |
                         +--+---+-----+---+---+
                            |         |    \
              +-------------+   +-----+     +-----------+
              |                 |                        |
      +-------v------+   +------v-------+        +-------v------+
      | internal      |   | internal     |        | internal      |
      | K3 | K6        |   | K15 | K22   |        | K40 | K55       |
      +--+---+----+----+   +--+---+---+--+        +--+---+----+----+
         |   |    |            |   |   |             |   |    |
      +--v+ +v-+ +v---+     +--v+ +v-+ +v---+     +--v+ +v-+  +v---+
      |leaf| |leaf| |leaf|  |leaf| |leaf| |leaf|  |leaf| |leaf|  |leaf|
      |1,2| |3,5| |6,9|<--->|10..| |15..| |22..|<->|30..| |40..|  |55..|
      +---+ +---+ +---+     +---+ +---+ +---+     +---+ +---+  +---+
        ^                                                          |
        +----------------------------------------------------------+
                    leaf level is a doubly linked list
```

Every leaf holds keys plus record pointers or inline data. Internal nodes hold
separator keys and child pointers only. The leaf linked list is what makes a
range scan for, say, keys between 6 and 40, cost one root-to-leaf descent plus
a linear walk across a handful of linked leaves, rather than a repeated
descent from the root for every value.

## 7. Dynamics

### Point lookup

```
search(node, key):
  if node is leaf:
    binary search node's keys for key
    return matching record pointer, or not-found
  else:
    i = position of the first separator key greater than key
      (or the last separator key <= key, exact convention
       varies by implementation)
    return search(node.children[i], key)
```

Cost is one page fetch per level. For a tree of height h and fan-out f holding
n keys, h is approximately log base f of n, so a fan-out of 200 reaches 40,000
keys in two levels and 8,000,000 keys in three.

### Insertion and node split

```
insert(key, value):
  leaf = find leaf where key belongs (descend as in search)
  insert key,value into leaf, keeping leaf sorted
  if leaf.count > max_keys:
    split leaf into left and right at the midpoint
    promote the first key of the right half (B+-tree)
      or the true median key (B-tree) up to the parent as a
      new separator, with a pointer to the new right sibling
    if parent.count > max_keys:
      recursively split parent
    if root itself split:
      create a new root with the two halves as its two children,
      tree height increases by exactly one
```

### Deletion and node merge or redistribution

```
delete(key):
  leaf = find leaf containing key (descend as in search)
  remove key from leaf
  if leaf.count < min_keys and leaf is not the root:
    if a sibling has more than min_keys, borrow one entry
      from the sibling through the parent (redistribution)
    else:
      merge leaf with a sibling, remove the separator
        key from the parent (merge)
      if parent.count < min_keys:
        recursively rebalance parent the same way
      if root now has zero keys and one child:
        make that child the new root, tree height decreases by one
```

Both operations are always local to a root-to-leaf path plus, in the worst
case, one sibling per level, which keeps every operation at O(log n) I/O and
O(log n) time, with the constant governed by fan-out and node size rather than
by the number of keys.

## 8. Implementation variants

- **B+-tree (data in leaves only).** The dominant production variant. Internal
  nodes are a pure routing index, so more separator keys fit per page than data
  records would, increasing fan-out and shrinking height. All three named
  production systems in dimension 9 use this shape.
- **B*-tree (two-thirds occupancy).** Knuth's variant, cited above, delays a
  split by first attempting to redistribute keys with a full sibling, raising
  minimum occupancy from roughly 50 percent to roughly 67 percent, which
  improves space efficiency at the cost of a more complex insert path that must
  check a neighbour before deciding to split.
- **Copy-on-write B-tree.** Instead of mutating a node in place, a write
  allocates a new copy of every node on the path from the modified leaf to the
  root, then atomically swaps the root pointer. This gives crash consistency
  and, in many implementations, cheap point-in-time snapshots without a
  separate write-ahead log, at the cost of write amplification proportional to
  tree height on every single write. This technique is used by other embedded
  and filesystem b-trees, and LMDB is a widely cited example of a
  copy-on-write B+-tree store.
- **Lehman-Yao link-based concurrent B-tree.** Adds a right-link pointer to
  every node so that a concurrent reader who lands on a node that has
  recently split can detect the situation from the link and step right to
  find the key it is looking for, instead of needing a lock held across the
  whole root-to-leaf path. PostgreSQL's own documentation for its B-tree
  access method points readers to its internal nbtree README for the
  detailed concurrency algorithm rather than stating the Lehman-Yao name
  directly in the user-facing manual page, confirmed live below. The
  technique is widely attributed to Lehman and Yao's 1981 paper in the
  database systems literature.
- **Prefix and suffix key compression.** Internal node separator keys are
  stored as the shortest prefix that still distinguishes two subtrees, rather
  than the full key value, increasing the effective fan-out per page. Widely
  used in file system and database B+-tree implementations to counteract long
  string keys reducing fan-out.
- **Bulk loading (bottom-up build).** When the full key set is known in
  advance and sorted, leaves are packed sequentially at target occupancy and
  internal levels are built bottom-up from the leaf boundaries, avoiding the
  split chain that inserting keys one at a time would trigger. Used by
  database CREATE INDEX code paths and by SQLite's internal btree balancing
  logic for large one-shot builds.

## 9. Known production uses

- **PostgreSQL's default index type.** The PostgreSQL documentation states
  PostgreSQL uses "the standard btree (multi-way balanced tree) index data
  structure" as its default CREATE INDEX method, describing a multi-level
  tree with a metapage, a doubly-linked leaf level holding more than 99
  percent of all pages, and internal pages holding downlinks. PostgreSQL 14
  and later add bottom-up index deletion to recover space from MVCC version
  churn without a page split, and per-index deduplication of equal keys into
  posting lists. Source, PostgreSQL documentation, "B-Tree Indexes",
  https://www.postgresql.org/docs/current/btree.html, verified 2026-08-02.
- **MySQL InnoDB's clustered and secondary indexes.** InnoDB stores every
  table as a B+-tree clustered index ordered by primary key, so the leaf pages
  of the clustered index are the actual row storage rather than a pointer to
  it elsewhere. Every secondary index is a separate B+-tree whose leaf entries
  store the primary key value and use it to look up the row through the
  clustered index. Source, MySQL 8.4 Reference Manual, "InnoDB and the ACID
  Model" and "Clustered and Secondary Indexes",
  https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html, verified
  2026-08-02.
- **SQLite's file format.** SQLite represents both tables and indexes as
  b-trees on disk. A table b-tree keys every entry by a 64-bit rowid and
  stores full row content only in leaf pages. An index b-tree stores no row
  data at all, only the indexed columns plus the row key, as arbitrary-length
  keys, and interior versus leaf pages are distinguished by an explicit page
  header flag (0x05 interior table, 0x0d leaf table, 0x02 interior index, 0x0a
  leaf index). Source, SQLite documentation, "Database File Format",
  https://www.sqlite.org/fileformat2.html, verified 2026-08-02.
- **File systems.** Ext4 uses an HTree, a variant of a B-tree specialized for
  directory entry lookup, described in the ext4 kernel documentation and
  Theodore Ts'o's original htree design notes. NTFS indexes directory entries
  and several metadata structures in B+-trees, documented in Microsoft's
  published NTFS technical documentation. APFS uses B-trees extensively for
  its object map and file system tree, described in Apple's own APFS
  Reference document. These are broadly and consistently cited across
  filesystem literature. This entry does not additionally re-verify each
  filesystem's primary source URL beyond the three storage-engine citations
  above, and a reader building on the filesystem claim should check the
  current vendor documentation directly.

## 10. Consequences

Positive outcomes.

- Worst-case O(log n) time and O(log n) disk I/O for search, insert, and
  delete, with the base of the logarithm equal to the fan-out, so in practice
  the height stays at 3 or 4 levels for data sets in the billions of rows.
- Native support for ordered range scans and sorted iteration, because a
  B+-tree's leaf level is itself a sorted, linked sequence.
- Guaranteed balance at all times. There is no pathological input that
  degrades a B-tree to linear behaviour the way an unbalanced binary search
  tree can degrade under sorted insertion order.
- Decades of production hardening around crash recovery, write-ahead logging
  integration, and concurrency control, so adopting a B-tree also means
  adopting a large, well-understood body of operational knowledge.

Negative costs.

- Every insert and delete does immediate, synchronous rebalancing work, which
  under a sustained heavy write load produces more total I/O than a structure
  that defers merging, such as an LSM tree, for the same logical write volume.
- Random-order insertion causes page splits scattered across the whole key
  space, which is disk-unfriendly on spinning media and, even on SSDs, causes
  write amplification at the storage layer because each split rewrites at
  least two pages plus a parent update.
- Minimum-occupancy guarantees, roughly 50 percent for a classic B-tree, mean
  a B-tree under adversarial or simply unlucky delete patterns can end up with
  substantial wasted space until a rebuild or vacuum recovers it.
- Concurrent access at correctness-preserving granularity, the Lehman-Yao
  style link-chasing scheme, is much more complex to implement and to reason
  about than a single global lock, and most of the genuinely hard bugs in
  production B-tree code live in this concurrency layer rather than in the
  basic split and merge logic.

## 11. Failure modes and misuse

- **Index bloat.** Symptom observed. the index file grows far larger than the
  data it indexes and query latency creeps up over weeks. Cause. a sustained
  update-heavy workload leaves many leaf pages below their target occupancy
  because deleted or superseded entries are marked dead but the page is never
  merged back, a known effect of MVCC-style storage engines where an update is
  physically a delete plus an insert. Fix. run the engine's dedicated
  space-recovery routine, for example VACUUM in PostgreSQL, or in newer
  PostgreSQL versions rely on bottom-up index deletion to reduce the problem
  at the source rather than only after the fact.
- **Unused range index.** Symptom observed. a range query that should be fast
  instead does a full table scan. Cause. the query planner determined the
  index is not selective enough for the predicate, or, more commonly, the
  leading column of a composite index does not match the predicate's leading
  column, so the index cannot be entered at the right point and the range
  cannot be walked contiguously. Fix. verify the composite index's column
  order matches the query's most selective equality predicates first, then
  the range predicate, and check the query plan explicitly rather than
  assuming the index is used because it exists.
- **Monotonic key hot spot.** Symptom observed. inserts that were fast at
  10,000 rows become dramatically slower at 10,000,000 rows, well beyond what
  a logarithmic curve predicts. Cause. monotonically increasing keys, for
  example an auto-increment primary key or a UUID that happens to sort in
  insertion order, concentrate every insert on the rightmost leaf, causing a
  hot page that must be split repeatedly and, in a clustered-index engine
  like InnoDB, causes constant page splits at the tail of the physical file.
  Fix. for genuinely sequential workloads this is often unavoidable and
  acceptable. For cases where key distribution is controllable, use a key
  that spreads writes across the key space, for example a randomized or
  hashed prefix, understanding this trades write distribution for loss of
  natural chronological ordering.
- **Concurrency contention.** Symptom observed. a long-running range scan
  blocks or is blocked by concurrent writers for far longer than expected.
  Cause. an implementation using coarse-grained locking, holding a lock
  across an entire root-to-leaf traversal instead of a link-based or
  latch-coupling scheme, serializes reads and writes far more than the
  workload should require. Fix. this is an engine-choice and
  engine-configuration problem, not something an application can patch
  around. Verify the storage engine's documented isolation and locking model
  matches the concurrency the workload actually needs before committing to
  it.
- **Oversized index entry.** Symptom observed. a key or value that should fit
  does not, and the insert fails with an obscure size error. Cause. a single
  index entry exceeds the fraction of a page the engine reserves for it.
  PostgreSQL for example documents that a B-tree index entry cannot exceed
  roughly one third of a page after TOAST compression. Fix. shorten the
  indexed value, index a hash or prefix of the value instead of the full
  value, or split it into a separate structure designed for large values.

## 12. Trade-off matrix

| Force | B-Tree / B+-Tree | LSM-Tree | Hash Index | Skip List |
|---|---|---|---|---|
| Point lookup latency | O(log n), few I/Os, predictable | O(log n) amortized, can hit multiple levels (bloom filters mitigate) | O(1) expected, unbeatable when applicable | O(log n) expected, in-memory only |
| Range scan support | Native, leaves are a sorted linked list | Requires merging multiple sorted runs at read time | None, no ordering guarantee | Native, in-memory only |
| Write throughput | Lower, immediate rebalancing on every write | Higher, writes batched and merged asynchronously | High for pure inserts, no rebalancing needed | High, in-memory, probabilistic balancing |
| Write amplification | Moderate, proportional to split cascade depth | Higher over the structure's lifetime due to repeated compaction merges | Low, single bucket write | Low, in-memory, no disk model |
| Space efficiency | 50 to 100 percent occupancy depending on variant and delete pattern | Can approach 100 percent post-compaction, transient overhead during merges | Depends on load factor and collision handling | Higher constant-factor overhead from multiple forward pointers per node |
| Implementation complexity | High, especially concurrent link-based variants | High, requires compaction scheduling and tombstone handling | Low to moderate | Low relative to a balanced tree, no rotation logic |
| Durable, on-disk fit | Purpose-built for block storage from the start | Purpose-built for block storage, favors write-optimized workloads | Common on disk (extendible or linear hashing) but loses ordering | Rare on disk, used almost only as an in-memory structure |

## 13. Related and incompatible patterns

- **Log-structured merge tree.** The primary alternative for write-heavy
  workloads. Where a B-tree pays its rebalancing cost synchronously on every
  write, an LSM tree defers it into background compaction, trading immediate
  write cost for later read and compaction cost. Many modern storage engines,
  for example RocksDB and Cassandra's storage layer, choose LSM specifically
  to avoid the write amplification pattern described in dimension 10.
- **Write-ahead log.** A B-tree almost never stands alone in a production
  engine. Because in-place page updates are not atomic with respect to a
  crash, engines pair the B-tree with a write-ahead log so that a page torn by
  a crash mid-write can be reconstructed from the log on recovery. PostgreSQL,
  InnoDB, and SQLite (via its rollback journal or WAL mode) all pair their
  B-tree with exactly this mechanism.
- **Buffer pool or page cache.** A B-tree's performance model assumes hot
  pages, especially the root and upper internal levels, stay resident in
  memory across operations. This is not automatic. It depends on a buffer
  pool or OS page cache sitting beneath the tree and is a co-designed
  component in every production engine cited in dimension 9, not an optional
  add-on.
- **Skip list.** Serves a similar role, ordered keys with logarithmic
  operations, but is designed for in-memory use and uses randomized level
  assignment instead of deterministic splitting and merging. Some engines use
  a skip list for an in-memory write buffer, sometimes called a memtable,
  that is later flushed into an on-disk B-tree or LSM structure, making the
  two patterns complementary rather than competing within a single
  component.
- **Hash index.** Not incompatible so much as orthogonal in purpose. Several
  engines, PostgreSQL among them, ship both a B-tree access method and a
  separate hash access method side by side, letting the schema author choose
  per index based on whether ordering is needed.
- **Bitmap index.** Complementary at the query planning layer. A planner may
  combine results from multiple B-tree scans using an in-memory bitmap, as
  PostgreSQL's bitmap index scan plan node does, rather than replacing the
  B-tree itself.

## 14. Refactoring path in and out

Introducing a B-tree into an existing system almost never means hand-rolling
one. It means adding an index backed by the database or storage engine's
existing B-tree access method, or, for an embedded or from-scratch storage
layer, adopting a well-tested library implementation rather than writing the
split and merge logic from scratch given how much of its cost lives in the
concurrency and crash-recovery correctness rather than the textbook algorithm.

1. Identify the access pattern that currently does a full scan or a linear
   search, for example an application-level filter over an unindexed column.
2. Confirm the pattern needs ordering or range access. If it is pure equality
   lookup, evaluate a hash index first per dimension 4.
3. Add the index, for example CREATE INDEX in a relational database or the
   equivalent secondary index declaration in the storage engine in use, and
   measure before and after query plans, not only wall-clock time, to confirm
   the B-tree is actually being chosen by the planner.
4. Watch write-path metrics after the change. An index is not free, every
   write to the indexed table now also writes to the index's B-tree, so
   insert and update throughput on that table will measurably drop, and that
   drop should be budgeted for rather than discovered in production.

Removing a B-tree, or more precisely retiring an index built on one, follows a
similar path.

1. Confirm through the engine's usage statistics, for example PostgreSQL's
   pg_stat_user_indexes view, that the index is genuinely unused by the
   current query workload, not merely unused by the queries the author
   happens to remember.
2. Drop the index and re-measure write throughput on the affected table,
   which should improve, and watch for any query that regresses to a full
   scan, which indicates the index was in fact load-bearing for a rarer but
   still real query path.
3. For a from-scratch storage layer being decommissioned in favour of an
   LSM-based engine, treat this as a data-migration project, not a refactor,
   and plan it with the write-amplification trade-off from dimension 3 as the
   explicit justification recorded for the change.

## 15. Testing and verification

B-tree correctness testing separates cleanly into structural invariant testing
and behavioural testing, because a bug can preserve one while violating the
other.

- **Invariant checking.** After every mutating operation in a test, walk the
  tree and assert that every leaf is at the same depth, every non-root node
  has between the minimum and maximum key count, every internal node's child
  count is exactly its key count plus one, every key in a subtree falls
  strictly within the bounds implied by its parent's separator keys, and an
  in-order traversal of leaves yields a fully sorted sequence with no
  duplicates unless duplicates are explicitly permitted by the design.
- **Property-based testing.** Generate random sequences of inserts and
  deletes, including adversarial monotonic sequences and sequences that
  repeatedly insert then delete the same key range to exercise merge and
  redistribution logic, and after each operation assert the invariants above
  plus that a subsequent lookup for every key still present succeeds and a
  lookup for every deleted key fails. This is a natural fit for a
  property-based testing library, since the invariants are exactly the kind
  of holds-after-any-sequence-of-operations property those libraries are
  built to check.
- **Concurrency testing.** For a link-based concurrent implementation,
  specifically test the split-in-flight case. a reader begins a descent, is
  paused, another thread splits the node the reader is about to enter, the
  reader resumes and must still find the correct result by following the
  right-link. This is the scenario the Lehman-Yao technique exists to handle
  and is the single most valuable concurrency test to write, because it is
  also the scenario most naive implementations get wrong first.
- **Crash-consistency testing.** For an on-disk implementation, simulate a
  crash mid-write, for example by truncating or corrupting the write-ahead
  log at varying offsets or by killing the process after a partial page write
  in a controlled test setup, and assert that recovery restores the tree to
  a state consistent with either the pre-write or the post-write state, never
  a torn intermediate state. This is the class of bug that a purely
  in-memory test suite, however thorough, cannot catch.
- **Test doubles.** A B-tree used purely as an in-memory ordered map in a
  test can usually be replaced with the language's built-in sorted map or
  tree structure for tests that only need the ordering contract and not the
  disk-page behaviour, which keeps unrelated tests fast and independent of
  storage-layer bugs.

## 16. Observability signals

- **Tree height or index depth.** Most database engines expose this directly
  or through page-count statistics. A height that grows past the expected 3
  to 4 levels for the data volume signals either unexpectedly low fan-out,
  from long keys or poor compression, or unexpected data growth that should
  be capacity-planned for.
- **Average leaf occupancy, the index bloat ratio.** The ratio of an index's
  on-disk size to the theoretical minimum size for its row count is the
  standard signal for the bloat failure mode in dimension 11. A healthy index
  typically sits in the 60 to 90 percent occupancy range depending on engine
  and workload. A ratio that has crept toward the minimum occupancy baseline,
  or below the engine's default fill factor, is the signal to run
  maintenance.
- **Page split rate.** A sudden or sustained spike in page splits per second,
  visible in most engines' internal statistics views, indicates either a hot
  insertion pattern, see the monotonic key failure mode, or a genuine
  workload growth event, and distinguishing the two is usually a matter of
  correlating the spike with the key distribution of recent inserts.
- **Buffer or cache hit ratio for index pages.** Because the B-tree's
  performance model assumes upper levels stay resident in memory, a falling
  hit ratio specifically for index pages, as opposed to table heap pages, is
  an early warning that the working set no longer fits the configured cache,
  well before overall query latency visibly degrades.
- **Index scan versus sequential scan counts per query.** A healthy state has
  the query planner choosing index scans for selective, indexed predicates. A
  rising share of sequential scans on a table that has the expected indexes
  is the primary signal for the query-planning failure mode in dimension 11,
  and is exactly what PostgreSQL's pg_stat_user_tables columns seq_scan
  versus idx_scan are designed to surface.

## 17. Security and privacy implications

A B-tree index is not itself an access-control boundary. It is a data
structure, and any security property must come from the layer that owns it,
not the tree. Two implications are worth naming plainly rather than left
silent.

- **Side-channel leakage through structural behaviour.** Because a B-tree's
  operation cost, its number of page splits, number of I/Os, or response
  latency, correlates with the value being inserted or looked up relative to
  existing keys, an attacker able to measure fine-grained timing of insert or
  lookup operations against a shared index can in principle infer information
  about the existing key distribution, for example whether a specific value
  is already present, purely from timing rather than from the returned
  result. This is the same general class of timing side channel that affects
  most data structures with data-dependent performance, and is a reason
  systems handling adversarial or untrusted query workloads against
  sensitive key spaces should not assume a B-tree's timing behaviour is
  neutral.
- **Data residue after logical delete.** As described in the bloat failure
  mode, a delete in most B-tree-backed engines does not immediately zero the
  physical bytes. It marks the entry dead, and the bytes can remain readable
  on disk, in a WAL segment, or in an unrecovered page, until vacuum,
  compaction, or page reuse overwrites them. Any system with a
  data-deletion or right-to-erasure obligation must verify its engine's
  actual physical deletion timeline, not assume a logical delete statement
  removes the bytes immediately, and should consult its engine's
  documentation on secure deletion, vacuum, and WAL retention specifically.
  This is engine-specific and this entry does not assert a single timeline
  across PostgreSQL, InnoDB, and SQLite. Verify against the engine actually
  in use.

## 18. References

1. Rudolf Bayer, Edward M. McCreight. "Organization and Maintenance of Large
   Ordered Indices." Acta Informatica, volume 1, 1972, pages 173 to 189.
   Original description of the B-tree, from Boeing Scientific Research
   Laboratories.
2. Douglas Comer. "The Ubiquitous B-Tree." ACM Computing Surveys, volume 11,
   issue 2, June 1979, pages 121 to 137. The canonical survey and the source
   most textbooks cite for the standard insertion and deletion presentation.
3. Donald E. Knuth. *The Art of Computer Programming, Volume 3, Sorting and
   Searching*, 2nd edition, Addison-Wesley, 1998, section 6.2.4, "Multiway
   Trees." Source for the B*-tree variant and its two-thirds occupancy
   rebalancing rule.
4. Philip L. Lehman, S. Bing Yao. "Efficient Locking for Concurrent
   Operations on B-Trees." ACM Transactions on Database Systems, volume 6,
   issue 4, December 1981, pages 650 to 670. Source for the link-based
   high-concurrency B-tree technique referenced in dimensions 3 and 8.
5. PostgreSQL documentation. "B-Tree Indexes."
   https://www.postgresql.org/docs/current/btree.html, verified 2026-08-02.
   Confirms PostgreSQL's default index method, multi-level structure,
   metapage, leaf linked list, bottom-up deletion, deduplication, and
   directs implementation-detail readers to its internal nbtree README.
6. MySQL 8.4 Reference Manual. "InnoDB and the ACID Model" and "Clustered and
   Secondary Indexes."
   https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html,
   verified 2026-08-02. Confirms InnoDB's clustered B+-tree row storage and
   secondary index lookup-through-primary-key design.
7. SQLite documentation. "Database File Format."
   https://www.sqlite.org/fileformat2.html, verified 2026-08-02. Confirms
   SQLite's dual use of table b-trees, rowid-keyed with data in leaves, and
   index b-trees, arbitrary-length keys with no stored data, and the
   page-type header flags distinguishing interior and leaf pages for each.
8. Wikipedia. "B-tree." https://en.wikipedia.org/wiki/B-tree, general
   cross-reference for terminology consistency, not used as a primary source
   for any specific factual claim above.

## Code examples

### TypeScript, an in-memory B+-tree with search, insert, and split

```typescript
class BPlusNode {
  keys: number[] = [];
  children: BPlusNode[] = [];
  values: number[] = [];
  isLeaf: boolean;
  next: BPlusNode | null = null;

  constructor(isLeaf: boolean) {
    this.isLeaf = isLeaf;
  }
}

class BPlusTree {
  private root: BPlusNode = new BPlusNode(true);
  private readonly order: number;

  constructor(order: number = 4) {
    this.order = order;
  }

  search(key: number): number | undefined {
    let node = this.root;
    while (!node.isLeaf) {
      let i = 0;
      while (i < node.keys.length && key >= node.keys[i]) i++;
      node = node.children[i];
    }
    const idx = node.keys.indexOf(key);
    return idx === -1 ? undefined : node.values[idx];
  }

  insert(key: number, value: number): void {
    const split = this.insertInto(this.root, key, value);
    if (split) {
      const newRoot = new BPlusNode(false);
      newRoot.keys = [split.promotedKey];
      newRoot.children = [this.root, split.right];
      this.root = newRoot;
    }
  }

  private insertInto(
    node: BPlusNode,
    key: number,
    value: number
  ): { promotedKey: number; right: BPlusNode } | null {
    if (node.isLeaf) {
      let i = 0;
      while (i < node.keys.length && node.keys[i] < key) i++;
      node.keys.splice(i, 0, key);
      node.values.splice(i, 0, value);
      if (node.keys.length < this.order) return null;
      return this.splitLeaf(node);
    }
    let i = 0;
    while (i < node.keys.length && key >= node.keys[i]) i++;
    const result = this.insertInto(node.children[i], key, value);
    if (!result) return null;
    node.keys.splice(i, 0, result.promotedKey);
    node.children.splice(i + 1, 0, result.right);
    if (node.keys.length < this.order) return null;
    return this.splitInternal(node);
  }

  private splitLeaf(node: BPlusNode) {
    const mid = Math.ceil(node.keys.length / 2);
    const right = new BPlusNode(true);
    right.keys = node.keys.splice(mid);
    right.values = node.values.splice(mid);
    right.next = node.next;
    node.next = right;
    return { promotedKey: right.keys[0], right };
  }

  private splitInternal(node: BPlusNode) {
    const mid = Math.floor(node.keys.length / 2);
    const promotedKey = node.keys[mid];
    const right = new BPlusNode(false);
    right.keys = node.keys.splice(mid + 1);
    right.children = node.children.splice(mid + 1);
    node.keys.pop();
    return { promotedKey, right };
  }
}

const tree = new BPlusTree(4);
[10, 20, 5, 6, 12, 30, 7, 17].forEach((k) => tree.insert(k, k * 10));
console.log(tree.search(12), tree.search(99));
```

Compiled with `npx tsc --noEmit` against TypeScript's default strict checks
and run under Node after transpilation. Output is `120 undefined`.

### Python, the same structure with an explicit range-scan method

```python
from bisect import bisect_left, insort
from dataclasses import dataclass, field


@dataclass
class BPlusNode:
    is_leaf: bool
    keys: list[int] = field(default_factory=list)
    children: list["BPlusNode"] = field(default_factory=list)
    values: list[int] = field(default_factory=list)
    next: "BPlusNode | None" = None


class BPlusTree:
    def __init__(self, order: int = 4) -> None:
        self.order = order
        self.root = BPlusNode(is_leaf=True)

    def search(self, key: int) -> int | None:
        node = self.root
        while not node.is_leaf:
            i = bisect_left(node.keys, key)
            if i < len(node.keys) and node.keys[i] == key:
                i += 1
            node = node.children[i]
        idx = bisect_left(node.keys, key)
        if idx < len(node.keys) and node.keys[idx] == key:
            return node.values[idx]
        return None

    def range_scan(self, low: int, high: int) -> list[tuple[int, int]]:
        node = self.root
        while not node.is_leaf:
            i = bisect_left(node.keys, low)
            node = node.children[i]
        out: list[tuple[int, int]] = []
        while node is not None:
            for k, v in zip(node.keys, node.values):
                if low <= k <= high:
                    out.append((k, v))
                elif k > high:
                    return out
            node = node.next
        return out

    def insert(self, key: int, value: int) -> None:
        promoted = self._insert(self.root, key, value)
        if promoted is not None:
            promoted_key, right = promoted
            new_root = BPlusNode(is_leaf=False, keys=[promoted_key])
            new_root.children = [self.root, right]
            self.root = new_root

    def _insert(self, node: BPlusNode, key: int, value: int):
        if node.is_leaf:
            idx = bisect_left(node.keys, key)
            node.keys.insert(idx, key)
            node.values.insert(idx, value)
            if len(node.keys) < self.order:
                return None
            return self._split_leaf(node)
        i = bisect_left(node.keys, key)
        if i < len(node.keys) and node.keys[i] == key:
            i += 1
        result = self._insert(node.children[i], key, value)
        if result is None:
            return None
        promoted_key, right = result
        node.keys.insert(i, promoted_key)
        node.children.insert(i + 1, right)
        if len(node.keys) < self.order:
            return None
        return self._split_internal(node)

    def _split_leaf(self, node: BPlusNode):
        mid = (len(node.keys) + 1) // 2
        right = BPlusNode(is_leaf=True, keys=node.keys[mid:], values=node.values[mid:])
        node.keys, node.values = node.keys[:mid], node.values[:mid]
        right.next, node.next = node.next, right
        return right.keys[0], right

    def _split_internal(self, node: BPlusNode):
        mid = len(node.keys) // 2
        promoted_key = node.keys[mid]
        right = BPlusNode(
            is_leaf=False,
            keys=node.keys[mid + 1 :],
            children=node.children[mid + 1 :],
        )
        node.keys = node.keys[:mid]
        node.children = node.children[: mid + 1]
        return promoted_key, right


if __name__ == "__main__":
    tree = BPlusTree(order=4)
    for k in (10, 20, 5, 6, 12, 30, 7, 17):
        tree.insert(k, k * 10)
    print(tree.search(12), tree.search(99))
    print(tree.range_scan(6, 20))
```

Run with `python3 btree.py`. Output is `120 None` followed by
`[(6, 60), (7, 70), (10, 100), (12, 120), (17, 170), (20, 200)]`, confirming
the leaf linked list produces a correctly ordered range scan.

### Go, a minimal generic-key B+-tree using integer keys

```go
package main

import (
	"fmt"
	"sort"
)

type node struct {
	isLeaf   bool
	keys     []int
	values   []int
	children []*node
	next     *node
}

type bplus struct {
	root  *node
	order int
}

func newTree(order int) *bplus {
	return &bplus{root: &node{isLeaf: true}, order: order}
}

func (t *bplus) search(key int) (int, bool) {
	n := t.root
	for !n.isLeaf {
		i := sort.SearchInts(n.keys, key)
		if i < len(n.keys) && n.keys[i] == key {
			i++
		}
		n = n.children[i]
	}
	i := sort.SearchInts(n.keys, key)
	if i < len(n.keys) && n.keys[i] == key {
		return n.values[i], true
	}
	return 0, false
}

func (t *bplus) insert(key, value int) {
	promoted, right := t.insertInto(t.root, key, value)
	if right != nil {
		newRoot := &node{keys: []int{promoted}, children: []*node{t.root, right}}
		t.root = newRoot
	}
}

func (t *bplus) insertInto(n *node, key, value int) (int, *node) {
	if n.isLeaf {
		i := sort.SearchInts(n.keys, key)
		n.keys = append(n.keys, 0)
		copy(n.keys[i+1:], n.keys[i:])
		n.keys[i] = key
		n.values = append(n.values, 0)
		copy(n.values[i+1:], n.values[i:])
		n.values[i] = value
		if len(n.keys) < t.order {
			return 0, nil
		}
		return t.splitLeaf(n)
	}
	i := sort.SearchInts(n.keys, key)
	if i < len(n.keys) && n.keys[i] == key {
		i++
	}
	promoted, right := t.insertInto(n.children[i], key, value)
	if right == nil {
		return 0, nil
	}
	n.keys = append(n.keys, 0)
	copy(n.keys[i+1:], n.keys[i:])
	n.keys[i] = promoted
	n.children = append(n.children, nil)
	copy(n.children[i+2:], n.children[i+1:])
	n.children[i+1] = right
	if len(n.keys) < t.order {
		return 0, nil
	}
	return t.splitInternal(n)
}

func (t *bplus) splitLeaf(n *node) (int, *node) {
	mid := (len(n.keys) + 1) / 2
	right := &node{isLeaf: true, keys: append([]int{}, n.keys[mid:]...), values: append([]int{}, n.values[mid:]...)}
	n.keys, n.values = n.keys[:mid], n.values[:mid]
	right.next, n.next = n.next, right
	return right.keys[0], right
}

func (t *bplus) splitInternal(n *node) (int, *node) {
	mid := len(n.keys) / 2
	promoted := n.keys[mid]
	right := &node{
		keys:     append([]int{}, n.keys[mid+1:]...),
		children: append([]*node{}, n.children[mid+1:]...),
	}
	n.keys = n.keys[:mid]
	n.children = n.children[: mid+1]
	return promoted, right
}

func main() {
	t := newTree(4)
	for _, k := range []int{10, 20, 5, 6, 12, 30, 7, 17} {
		t.insert(k, k*10)
	}
	v, ok := t.search(12)
	fmt.Println(v, ok)
	_, ok = t.search(99)
	fmt.Println(ok)
}
```

Run with `go run btree.go`. Output is `120 true` followed by `false`.

Rust and Swift are omitted from the compiled set for this entry. The pattern
translates directly to both. An owned-tree Rust version typically reaches for
`Box<Node>` child pointers or a slab-based pool to sidestep the
recursive-ownership and mutable-aliasing friction a naive `Rc<RefCell<Node>>`
tree runs into during split and merge, and a Swift version is a natural fit
for a class-based node with an `[Node]` children array. Both are common
teaching exercises for the structure but add no new structural insight beyond
the three languages compiled above, so this entry states the omission rather
than including an unrun sample.
