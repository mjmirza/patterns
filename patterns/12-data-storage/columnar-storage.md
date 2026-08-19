---
name: Columnar Storage
slug: columnar-storage
family: 12-data-storage
category: Data and Storage
aliases: [Column-Oriented Storage, Column Store, Vertical Partitioning of Storage]
first_described: "Copeland, Khoshafian 1985"
maturity: canonical
related: [write-ahead-log, lsm-tree, materialized-view, bloom-filter, cqrs]
incompatible_with: [row-oriented-storage]
verified: 2026-08-02
---

# Columnar Storage

## 1. Name, aliases, and lineage

The canonical name is Columnar Storage, also called Column-Oriented Storage or,
informally, a Column Store. The earliest widely cited academic description is
George P. Copeland and Setrag N. Khoshafian, "A Decomposition Storage Model,"
in *Proceedings of the 1985 ACM SIGMOD International Conference on Management
of Data*, pages 268 to 279 (ACM Digital Library,
https://dl.acm.org/doi/10.1145/318898.318923, verified 2026-08-02). Copeland
and Khoshafian called their scheme the Decomposition Storage Model, and it is
the paper the later commercial and research literature on column stores
consistently traces back to, including the MonetDB and C-Store research lines
that turned the idea into working database engines two decades later.

The name "Decomposition Storage Model" is the academic ancestor. The name
"column store" or "column-oriented DBMS" became the working industry term once
Sybase IQ (1995, the first commercial columnar database) and later MonetDB,
C-Store, Vertica, and Google's Bigtable made the technique a normal choice
rather than a research curiosity. Mike Stonebraker and a group of coauthors
published "C-Store. A Column-oriented DBMS" at the 2005 Very Large Data Bases
conference, and that paper is the one most frequently cited as the modern
articulation of the pattern for OLAP workloads
(https://www.vldb.org/conf/2005/papers/p553-stonebraker.pdf, verified
2026-08-02). Fay Chang et al., "Bigtable. A Distributed Storage System for
Structured Data," OSDI 2006
(https://www.usenix.org/legacy/event/osdi06/tech/chang/chang.pdf, verified
2026-08-02), independently arrived at a column-family layout for a different
reason, wide sparse tables at planet scale, and that lineage produced HBase and
Cassandra's storage engine rather than an analytical query engine, which is why
this entry treats "column-family store" as a cousin, not a synonym, of the
analytical column store described below.

There is no real name dispute in the literature. Every source uses "columnar"
or "column-oriented" interchangeably with "column store." The one distinction
worth being precise about, because practitioners conflate it constantly, is
between a column-oriented physical layout (this pattern, the subject of
this entry) and a column-family data model (Bigtable, HBase, Cassandra),
which groups related columns into named families but still often stores each
row's column family together on disk rather than storing one physical file per
column across all rows. Dimension 8 returns to this distinction in detail
because it changes what performance claims are actually true.

## 2. Problem and context

A database has to put bytes on disk or in memory in some fixed physical order,
and that order is a one-time decision with permanent consequences for every
query that runs afterward. The traditional choice, inherited from System R and
every mainstream OLTP engine since, is to store a table row by row. All the
columns of a single record sit contiguously, so writing or reading one whole
record is one contiguous I/O.

That layout is correct for the workload it was designed for, transaction
processing, where a request reads or writes a small number of complete rows,
for example "fetch this customer's full profile" or "insert this order." It is
wrong for a different, increasingly common workload, analytical queries that
touch a small number of columns but a very large number of rows, for example
"sum the revenue column across four hundred million rows for the last quarter"
or "compute the average latency for every request tagged with a particular
region." In the row-oriented layout, satisfying that query means reading every
byte of every column in every row, including the eighty percent of the row
that the query never asked for, because the storage engine cannot separate
"give me this one column" from "give me this whole row" when they live on the
same disk page.

The problem columnar storage solves is precisely this mismatch, it reorganizes
physical storage so that all values belonging to one column, across every row
in the table, sit contiguously, and it accepts the corresponding cost that
reconstructing one full row now requires stitching values back together from
many separate places. The context in which this trade is worth making is
specific and important, it is a good trade when a workload reads a narrow
slice of columns over a wide swath of rows, when the data is written in bulk or
append-mostly rather than updated field by field, and when the values within a
column repeat or vary smoothly enough that a compressor can exploit that
locality. Ralph Kimball's data warehouse toolkit literature had already
described the analytical access pattern that motivates this before column
stores existed as a physical technique, which is part of why the pattern found
its first large audience in data warehousing and later in big-data and
observability systems rather than in transactional application databases.

## 3. Forces

The tension this pattern resolves, and the ones it deliberately does not
resolve, are best stated as competing forces rather than a simple list of pros
and cons.

Column locality versus row locality. A physical layout can make one of
these two access patterns fast, and doing so makes the other slow, because
both cannot be the contiguous unit of storage at once. Columnar storage chooses
column locality. This is the central force and every other consequence in this
entry follows from it.

Compression ratio versus write latency. A column of repeated or
monotonically increasing values (a status enum, a timestamp column, a country
code) compresses extremely well because the compressor's dictionary or delta
encoder only has to model one domain of values at a time, not an interleaved
mixture of a customer ID, a free-text comment, and a floating-point price. That
compression is cheapest to compute in large batches, which pushes the pattern
toward bulk writes and away from single-row, low-latency inserts. Building a
compressed column segment for one new row at a time is either wasteful (a
segment of size one gets no compression benefit) or requires buffering writes
somewhere else first, which is exactly why columnar engines are almost always
paired with a write-optimized buffering layer.

Query throughput versus point-lookup latency. Vectorized scans over
contiguous column arrays are extremely fast for aggregate queries because
modern CPUs process the array with SIMD instructions and predictable memory
access patterns. The identical layout is comparatively slow for "fetch this
one row by primary key," because that operation now has to seek into N
different column files or column segments and reassemble them, an operation
row stores do in a single seek.

Read amplification for narrow queries versus read amplification for wide
queries. Columnar storage reduces I/O for a query that reads few columns
across many rows, and it can increase I/O and CPU overhead (reassembly cost,
scattered seeks) for a query that reads most or all columns of a small number
of rows. The pattern is not universally faster, it changes which queries are
fast.

Schema flexibility versus encoding efficiency. Encoding a column tightly
(dictionary encoding, run-length encoding, bit-packing) generally assumes the
column's type and cardinality are known and comparatively stable. Frequent
schema evolution, especially adding wide, sparsely populated columns, degrades
the efficiency columnar storage exists to provide, because the whole benefit
of the layout depends on a column being a dense, homogeneous, predictable run
of values.

## 4. Applicability and non-applicability

Reach for columnar storage when the situation matches one or more of these.

- The workload is dominated by analytical queries that aggregate, filter, or
  scan a small subset of columns across a large number of rows, the canonical
  OLAP pattern.
- Data arrives in large, append-mostly or immutable batches, such as event
  logs, metrics, clickstream data, or periodic ETL loads, rather than as a
  stream of small single-row updates.
- Storage cost matters at scale and the data has real compressibility, for
  example low-cardinality categorical columns, monotonic timestamps, or
  sparse numeric columns with many repeated or default values.
- The system needs to scan and aggregate over data sets far larger than
  memory, where reducing bytes read from disk or from a network-attached
  object store is the dominant cost, as in cloud data lake query engines
  reading Parquet from S3.
- Reporting, dashboards, business intelligence, or ad hoc analytical queries
  are a first-class access pattern, not an occasional afterthought bolted
  onto a transactional schema.

Do NOT reach for columnar storage when any of these apply instead.

- The workload is dominated by single-row reads and writes by primary key,
  the classic OLTP pattern of an order-processing or user-account system.
  Reassembling a full row from many separate column segments on every request
  adds latency and complexity a row store does not pay.
- Rows are frequently updated field by field with low latency requirements.
  Updating one value inside a compressed, immutable column segment typically
  means rewriting the whole segment, or routing the write through a separate
  mutable buffer and merging later, both of which add operational complexity
  that a row store's in-place update avoids.
- The table is narrow, for example three or four columns, where the benefit
  of skipping unread columns is small relative to the fixed overhead of
  managing separate column files, indexes, and metadata per column.
- Strong, low-latency transactional consistency across many columns of one
  row is required, because most columnar engines historically traded
  transactional guarantees for scan throughput, though modern hybrid engines
  are narrowing this gap, discussed in dimension 8.
- The data set is small enough to fit comfortably in memory and be scanned in
  full regardless of layout, where the columnar advantage of skipping unread
  bytes has little to act on.

## 5. Structure

The participants in a columnar storage system, using the roles the C-Store and
Parquet literature actually names them by.

- Column segment (or column chunk). The physical unit of storage holding
  a contiguous run of values for one column. This is the structural heart of
  the pattern, everything else exists to produce, encode, compress, index,
  and later reassemble these segments.
- Row group (Parquet's term) or fragment (C-Store's term). A horizontal
  slice of the table, typically tens of thousands to a few million rows,
  within which each column is stored as its own contiguous segment. Splitting
  the table into row groups bounds the amount of data that must be
  decompressed to answer a query touching only part of the table, and gives
  the query engine a unit at which to apply skipping via zone maps.
- Encoder. The component that transforms raw column values into a
  compact representation before or alongside general-purpose compression.
  Dictionary encoding, run-length encoding (RLE), delta encoding, and
  bit-packing are the four encodings that appear in essentially every
  production columnar format.
- Zone map (min/max index, also called a small materialized aggregate or a
  segment statistic). Per-column, per-row-group metadata recording the
  minimum and maximum value, and often a null count, so the query planner can
  skip an entire row group without decompressing it when the predicate
  cannot match anything in that group's range.
- Column footer or metadata block. The catalog describing where each
  column's segments live, their encoding, their compression codec, and their
  zone-map statistics, so a reader can plan a scan without touching the data
  itself.
- Vectorized execution engine. The query engine component that operates
  on whole batches of column values at once (a "vector" or "chunk" of
  typically 1,024 to 65,536 values) rather than one row or one value at a
  time, which is what lets the CPU exploit SIMD instructions and cache
  locality that a row-at-a-time interpreter cannot.
- Delete vector or tombstone bitmap (in mutable columnar formats such as
  Apache Iceberg and Delta Lake). A side structure recording which
  logically-deleted or updated rows should be skipped when reading an
  otherwise-immutable column segment, which is how modern table formats add
  update and delete support on top of immutable columnar files without
  rewriting them on every mutation.

## 6. ASCII structure diagram

```
Row-oriented table (conceptual)                Columnar table (conceptual)

  Row 1: [id][name][age][city]                 Row Group 0
  Row 2: [id][name][age][city]                   Column "id"    segment
  Row 3: [id][name][age][city]                     [1][2][3][4] (delta enc.)
  Row 4: [id][name][age][city]                   Column "name"  segment
                                                   ["A"]["B"]["C"]["D"]
  A full-row read touches                          (dictionary enc.)
  one contiguous block.                          Column "age"   segment
  A single-column scan                             [30][41][29][52]
  still reads every row.                           (plain / bit-packed)
                                                  Column "city"  segment
                                                    [NYC][NYC][SF][NYC]
                                                    (RLE. NYC*2, SF*1, NYC*1)

                                                Row Group 1
                                                  ... same four column
                                                      segments, next batch
                                                      of rows ...

  +------------------+          +--------------------------------------+
  |  Column Footer    | ------> | zone map. id [1,4] name n/a           |
  |  (metadata block)  |         | age [29,52]  city n/a nulls=0        |
  +------------------+          +--------------------------------------+
  A query filtering city = 'SF' reads only the "city" column segment,
  and can skip a whole row group instantly if its zone map shows the
  predicate cannot match inside that group.
```

## 7. Dynamics

The runtime flow for a typical read query, following the sequence a columnar
query engine such as DuckDB, ClickHouse, or a Parquet-reading engine like
Trino actually executes.

```
Client            Query Planner        Metadata / Footer      Storage (segments)
  |  SELECT city,       |                     |                     |
  |  SUM(age)           |                     |                     |
  |  WHERE city='SF'    |                     |                     |
  |--------------------->|                     |                     |
  |                      | 1. Parse query,     |                     |
  |                      |    determine needed |                     |
  |                      |    columns. city,age|                     |
  |                      |-------------------->|                     |
  |                      |                     | 2. Read footer,     |
  |                      |                     |    get zone maps    |
  |                      |                     |    per row group    |
  |                      |<--------------------|                     |
  |                      | 3. Prune row groups |                     |
  |                      |    whose city zone  |                     |
  |                      |    map excludes 'SF'|                     |
  |                      |---------------------------------------->  |
  |                      |                     | 4. For surviving    |
  |                      |                     |    groups, fetch    |
  |                      |                     |    ONLY city+age    |
  |                      |                     |    segments, skip   |
  |                      |                     |    id, name entirely|
  |                      |<----------------------------------------  |
  |                      | 5. Decode segments  |                     |
  |                      |    (dict-decode,    |                     |
  |                      |    RLE-expand),     |                     |
  |                      |    filter city='SF' |                     |
  |                      |    vectorized       |                     |
  |                      | 6. Aggregate age    |                     |
  |                      |    per surviving    |                     |
  |                      |    row batch        |                     |
  |<---------------------|                     |                     |
  |  result. SUM(age)   |                     |                     |
```

The write path is structurally different and worth drawing separately, because
it is where the pattern's write-latency cost shows up most clearly.

```
Ingest buffer (row- or memory-oriented, mutable)
        |
        | rows accumulate until a size or time threshold
        v
Sort / partition rows (optional, by a chosen key for later pruning)
        |
        v
For each column. transpose row values into a column array
        |
        v
Encode each column array (dictionary, RLE, delta, bit-pack, as fits)
        |
        v
Compress each encoded column segment (general codec, e.g. Zstd, Snappy)
        |
        v
Compute per-segment zone map (min, max, null count)
        |
        v
Write immutable column segments + footer metadata to durable storage
```

The write path shows the structural reason columnar formats are almost always
paired with a separate write-optimized buffer, an in-memory row batch, a
log-structured merge tree, or a streaming ingest layer, rather than accepting
writes directly into compressed columnar segments. The transpose-then-encode
step is only worth its fixed cost when there is enough buffered data to
amortize it.

## 8. Implementation variants

Pure analytical file format (Apache Parquet, Apache ORC). The data itself
never lives in a running database process between writes, it lives as
immutable files, typically in a data lake or object store, organized into row
groups (Parquet) or stripes (ORC), each internally column-oriented, described
in the Apache Parquet format specification
(https://parquet.apache.org/docs/file-format/, verified 2026-08-02) and the
Apache ORC specification (https://orc.apache.org/specification/, verified
2026-08-02). Any engine (Spark, Trino, DuckDB, Snowflake external tables) can
read the same files because the format, not the engine, defines the layout.
This variant maximizes portability and minimizes lock-in, at the cost of no
built-in mutability, which table formats (Iceberg, Delta Lake, Apache Hudi)
layer on top by tracking which files and which rows within files are logically
current.

In-process analytical engine (DuckDB, ClickHouse local, Apache Arrow plus
Polars). The columnar layout lives inside a single process's memory or local
disk, typically using the Apache Arrow columnar memory format
(https://arrow.apache.org/docs/format/Columnar.html, verified 2026-08-02) as
the in-memory representation so that multiple tools (Polars, DuckDB, pandas
via PyArrow) can share the exact same memory layout with zero copy between
them. This variant optimizes for single-machine analytical throughput and for
interoperability between analytical libraries.

Distributed analytical database (ClickHouse in cluster mode, Snowflake,
Google BigQuery, Amazon Redshift, Vertica). Columnar storage is combined
with horizontal partitioning across many machines, distributed query
execution, and a purpose-built storage engine rather than a portable file
format. ClickHouse's MergeTree engine family, described in the ClickHouse
documentation (https://clickhouse.com/docs/engines/table-engines/mergetree-family/mergetree,
verified 2026-08-02), is the clearest open-source example of this variant, it
combines LSM-tree-style background merging (see the related pattern
lsm-tree) with a columnar on-disk part layout, which is a deliberate hybrid
that solves the write-latency force from dimension 3 by absorbing writes into
small parts and periodically merging and re-encoding them into larger,
better-compressed parts.

Wide-column store, the Bigtable and Cassandra lineage. This variant is the
one most often confused with the pattern proper, and the confusion deserves
direct correction. Bigtable and its descendants (HBase, Cassandra) organize
data into named column families and, within a column family, store data
sorted by row key with columns grouped together, which is genuinely
column-family-oriented at the data-model level but is not the same physical
technique as a Parquet row group. Cassandra's SSTable storage engine, as
described in the Apache Cassandra documentation
(https://cassandra.apache.org/doc/4.0/cassandra/architecture/storage_engine.html,
verified 2026-08-18), is fundamentally a log-structured merge tree of sorted
row-key-to-column-value pairs, and while later Cassandra versions added
genuinely columnar internal encodings for wide partitions, the wide-column
store's original design goal was sparse, wide, semi-structured rows at
planet scale, not analytical scan throughput over dense numeric columns. An
entry author who cites Cassandra or HBase as proof that columnar storage
speeds up analytics is making the exact category error this dimension exists
to prevent, Cassandra is cited correctly in dimension 9 for a different,
narrower reason.

Hybrid transactional analytical processing, HTAP (SAP HANA, MemSQL and
SingleStore, TiDB's TiFlash). These systems maintain both a row-oriented
representation for transactional workloads and a columnar representation for
analytical workloads, either simultaneously (a row store plus an
automatically synchronized columnar replica, as TiFlash does for TiDB,
documented at https://docs.pingcap.com/tidb/stable/tiflash-overview/, verified
2026-08-02) or by choosing per-table which layout to use. This variant is a
direct, engineered response to the applicability boundary in dimension 4, it
tries to get both forces from dimension 3 rather than accepting the trade.

## 9. Known production uses

ClickHouse, an open-source columnar OLAP database whose MergeTree table
engine family stores each column in a separate compressed file per data
part, used in production for real-time analytics at scale by companies
including Cloudflare for its HTTP analytics pipeline, documented in
Cloudflare's own engineering blog, "How Cloudflare analyzes 1M DNS queries
per second" (https://blog.cloudflare.com/how-cloudflare-analyzes-1m-dns-queries-per-second/,
verified 2026-08-02), which describes storing and querying request logs in
ClickHouse specifically because of its columnar scan performance over wide
log tables.

Apache Parquet, used as the default columnar file format for Apache
Spark's DataFrame and SQL engine, documented in the Apache Spark SQL Data
Sources Guide (https://spark.apache.org/docs/latest/sql-data-sources-parquet.html,
verified 2026-08-02), which states that Parquet is the default format for
Spark SQL and that Spark automatically preserves the schema and applies
predicate pushdown against Parquet's column statistics.

Google BigQuery, whose underlying storage format, Capacitor, is a
proprietary columnar storage format described in Google's own BigQuery
documentation on storage internals
(https://cloud.google.com/bigquery/docs/storage_overview, verified
2026-08-02), which explains that BigQuery stores data in a columnar format
and that this is the mechanism by which a query scanning few columns of a
wide table is billed for, and executes over, only the bytes in those
columns.

Apache Cassandra's internal storage engine, cited here specifically for
its SSTable format, which the Apache Cassandra Storage Engine documentation
(https://cassandra.apache.org/doc/4.0/cassandra/architecture/storage_engine.html,
verified 2026-08-18) describes as organizing a partition's columns for
efficient retrieval and, since the Storage Attached Indexes and newer
Trie-based SSTable formats, using increasingly columnar internal layouts
for wide partitions, cited as the wide-column-store variant from dimension
8, not as an OLAP engine.

Snowflake, whose architecture documentation
(https://docs.snowflake.com/en/user-guide/intro-key-concepts, verified
2026-08-02) states that Snowflake stores table data in an optimized,
compressed, columnar format, and separates storage from compute so that
many virtual warehouses can query the same columnar micro-partitions
concurrently.

## 10. Consequences

Positive consequences of adopting this pattern.

- Dramatically lower I/O for queries that read few columns across many rows,
  because unread columns are never fetched from disk or network storage at
  all, not merely decompressed and discarded.
- Substantially better compression ratios than row-oriented storage for most
  real-world tabular data, because each column's encoder only has to model
  one data domain rather than an interleaved mixture of types and
  distributions.
- Vectorized execution over contiguous column arrays lets modern CPUs use
  SIMD instructions and predictable memory access patterns, which is a large
  part of why columnar OLAP engines can be an order of magnitude faster than
  row-oriented engines on aggregate queries over the same data.
- Zone maps and other per-segment statistics let a query engine skip whole
  row groups without decompressing them, which compounds with the column
  pruning benefit above.
- Immutable, append-only column segments are simple to replicate, cache, and
  serve from cheap object storage, which is the technical foundation of the
  modern data lakehouse architecture.

Negative consequences that come with the same choice.

- Single-row reads and writes become slower and more complex, because a full
  row must be assembled from, or scattered across, many separate column
  segments rather than read or written as one contiguous block.
- Updating or deleting an individual value inside an already-written,
  compressed column segment typically requires either rewriting the whole
  segment or layering a separate mutable structure (a delete vector, a merge
  tree of small parts) on top, adding real operational and consistency
  complexity that a row store's in-place update avoids.
- Small writes are inefficient, because the compression and encoding
  techniques that make the pattern valuable only pay off over a batch large
  enough to amortize their fixed overhead, which forces most columnar systems
  to buffer writes elsewhere first.
- The number of separate physical objects (files, segments, metadata blocks)
  per table grows with the number of columns and the number of row groups,
  which increases metadata management overhead and, in cloud object storage,
  can increase the number of small network requests if not batched carefully.
- Reasoning about performance requires understanding encoding, compression,
  and row-group sizing choices that a row-store user never has to think
  about, which raises the operational skill floor for the team running the
  system.

## 11. Failure modes and misuse

Symptom. A query that filters and returns most of a table's columns is
significantly slower on the columnar system than an equivalent row store
was.
Cause. The workload was assumed to be analytical (narrow-column, wide-
row) but is actually closer to fetching the whole record, which is the
access pattern columnar storage is worst at, because reconstructing a wide
row means reassembling nearly every column segment for that row.
Fix. Reassess the workload's real column-selectivity. If most queries
need most columns, revert to a row-oriented store, or adopt a hybrid HTAP
system from dimension 8 that keeps a row-oriented path for that access
pattern.

Symptom. Small, frequent write operations (single-row inserts) are slow,
or the storage layer accumulates an unmanageable number of tiny files or
row groups.
Cause. Writes are being flushed to immutable columnar segments too
eagerly, without a buffering or merge layer, so every small write pays the
full fixed cost of encoding and compressing a segment for almost no data.
Fix. Insert a write-optimized buffer in front of the columnar layer, a
memtable, an LSM-tree ingest path, or a streaming batching layer, and only
flush to compressed columnar segments once enough rows have accumulated, as
ClickHouse's MergeTree and Iceberg-based streaming ingest pipelines both
do.

Symptom. A row group's zone map shows a very wide min/max range, and
predicate pushdown almost never prunes that row group even for selective
queries.
Cause. Rows were written in arrival order rather than sorted or
clustered by the column the queries actually filter on, so every row
group's value range for that column spans nearly the whole domain and the
zone map provides no useful pruning signal.
Fix. Sort or cluster incoming data by the predicate column, or a
correlated column, before or during the write path (Parquet's row-group
boundaries, ClickHouse's ORDER BY key, or Iceberg's sort-order metadata
all exist for exactly this reason), so zone maps become tight and useful.

Symptom. Storage costs and compressed file sizes are much higher than
expected for a table that should compress well.
Cause. A high-cardinality column (a UUID, a free-text field, a
floating-point measurement with many unique digits) was encoded with the
same dictionary or run-length approach that works well for low-cardinality
columns, producing a dictionary nearly as large as the column itself, or a
run-length encoding with almost no runs.
Fix. Choose the encoding per column based on its actual value
distribution and cardinality, delta encoding for monotonic or slowly
varying numeric columns, plain or bit-packed encoding for high-entropy
numeric columns, dictionary encoding only for genuinely low-cardinality
categorical columns, which is exactly what Parquet's and ORC's
encoding-selection heuristics attempt to automate.

Symptom. A query engine reports it read far more bytes than the query's
filter should have required, even though zone maps exist.
Cause. The predicate is on an expression over the column (a function
call, a cast, a date-truncation) rather than the raw column value, and the
zone map, which was computed on raw stored values, cannot be used to prune
against a transformed predicate, so the engine falls back to scanning every
row group.
Fix. Rewrite the predicate to reference the raw column directly where
possible, or precompute and store a derived column that carries its own
zone map, so that predicate pushdown has a matching statistic to check
against.

## 12. Trade-off matrix

Compared against the two most relevant named alternatives, row-oriented
storage (the standard OLTP layout, related entry write-ahead-log covers
its durability mechanism) and log-structured merge trees used as a general
storage engine (lsm-tree), across the forces named in dimension 3.

| Force | Row-oriented storage | LSM-tree (as general engine) | Columnar storage |
|---|---|---|---|
| Full-row point read latency | Low, single contiguous read | Low to moderate, may check multiple levels | High, requires reassembly across segments |
| Narrow-column, wide-row scan throughput | Low, reads unrequested columns | Low to moderate, same row-oriented cost inside each level | High, unrequested columns never touched |
| Compression ratio on typical tabular data | Moderate, mixed-type rows compress worse | Depends on the value encoding used within the engine | High, homogeneous per-column encoding |
| Write latency for small, frequent writes | Low, in-place or append-log update | Low, designed for this exact pattern | High unless buffered by another layer first |
| In-place update or delete of one field | Simple, direct | Simple via tombstone plus later compaction | Complex, delete vectors or full segment rewrite |
| Predicate pushdown via min/max pruning | Rare, page-level statistics at best | Possible per SSTable, coarser than per-column | Native and central to the pattern's design |
| Operational skill floor | Lower, well understood defaults | Moderate, tuning compaction matters | Higher, encoding and row-group sizing matter |

## 13. Related and incompatible patterns

Write-Ahead Log (write-ahead-log). Composes with columnar storage as
the durability mechanism for the mutable write buffer that sits in front of
immutable columnar segments, discussed in dimension 7's write path. The two
patterns solve different problems, durability of an in-flight write versus
physical layout of settled data, and nearly every real columnar system
needs both.

LSM-Tree (lsm-tree). Composes closely, and in systems such as
ClickHouse's MergeTree the two patterns are fused, an LSM-tree's background
merge process is reused to periodically re-encode and re-compress small,
recently-written columnar parts into larger, better-compressed ones, which
is how those systems resolve the write-latency force from dimension 3
without abandoning columnar storage for reads.

Materialized View (materialized-view). Frequently paired at a higher
level, a row-oriented transactional system feeds a materialized, columnar
copy of the same data optimized for analytical queries, which is the
architecture behind change-data-capture pipelines that replicate an OLTP
database into a columnar warehouse.

Bloom Filter (bloom-filter). Composes as a complementary pruning
mechanism alongside zone maps, particularly useful for high-cardinality
columns and equality predicates where a min/max range provides little
pruning power but a per-segment bloom filter can cheaply rule out a segment
that cannot contain a specific value.

CQRS (cqrs). A common architectural motivation for adopting columnar
storage at all, the query side of a CQRS split is frequently backed by a
columnar store precisely because it is optimized for the read and
aggregation patterns CQRS deliberately separates from the write side's
transactional row-oriented model.

Incompatible with. Row-Oriented Storage. Strictly speaking these are
alternative physical layouts for the same logical table, not patterns that
can be composed for the same physical bytes. A single physical table is
either laid out row by row or column by column at rest (hybrid systems from
dimension 8 resolve the conflict by maintaining two separate physical
copies, not by making one layout be both at once).

## 14. Refactoring path in and out

Introducing columnar storage into a system that does not have it.

1. Identify the specific analytical queries that motivate the change,
   including which columns they read and which predicates they filter on,
   because the pruning and encoding benefits described in dimensions 3 and 6
   depend on those specifics, not on analytics as an abstract label.
2. Stand up the columnar path alongside, not instead of, the existing
   row-oriented system, a change-data-capture pipeline or a periodic batch
   export into Parquet or a columnar warehouse is the lowest-risk starting
   point, matching the materialized-view pattern from dimension 13.
3. Choose a row-group or partitioning key that matches the predicates
   identified in step 1, so zone maps and pruning are effective from day one
   rather than being tuned reactively after a slow-query incident.
4. Redirect only the analytical read traffic to the new columnar path,
   leaving the transactional read and write traffic on the original
   row-oriented system, verifying the failure modes from dimension 11 do not
   appear (tiny-file accumulation, wide zone-map ranges) before widening
   adoption.
5. Once the columnar path is proven, evaluate whether the source system can
   be retired, replaced with the HTAP hybrid variant from dimension 8, or
   kept permanently as the transactional source of truth feeding the
   columnar analytical copy, which is the steady-state architecture most
   production systems land on.

Removing columnar storage once it no longer earns its place.

1. Confirm the workload has genuinely shifted away from wide-row, narrow-
   column analytical access, not merely that a specific slow query was fixed
   by other means such as an index or a cache.
2. Check whether the actual driver is a mismatch identified in dimension 11
   (the workload wants whole rows, or writes are too small and frequent)
   rather than a fundamental mistake in choosing the pattern at all, because
   the fix for those symptoms is often tuning, not removal.
3. If removal is genuinely warranted, migrate to a row-oriented store using a
   bulk export of the columnar data, reconstructing full rows in batches
   rather than row by row, since that reconstruction is exactly the operation
   columnar storage is worst at, per dimension 10.
4. Decommission the columnar path's write and compaction infrastructure last,
   after read traffic has fully moved, to avoid a period where writes still
   flow into a store nothing reads from anymore.

## 15. Testing and verification

Testing code that reads and writes columnar storage has to verify two
distinct things a row-oriented equivalent does not separately need to prove,
correctness of the column encoding round-trip, and correctness of predicate
pushdown pruning, because a bug in either one produces wrong query results
silently rather than a visible crash.

Encoding round-trip tests. For every encoder used (dictionary,
run-length, delta, bit-packing), a property-based test asserting that
decode(encode(column_values)) equals column_values for a wide range of
generated inputs, including edge cases each encoding is uniquely fragile
to, an empty column, a column of all-identical values (worst case for
dictionary encoding's dictionary size, best case for run-length), a column
with the maximum representable delta between consecutive values, and a
column containing nulls if the format supports them.

Zone map correctness tests. Verify that a computed zone map's minimum
and maximum genuinely bound every value in the segment it describes,
including after any transformation the encoder applies, since a zone map
computed on encoded rather than raw values is a common and dangerous class
of bug that silently causes a query to skip a row group that actually
contained a matching row.

Predicate pushdown tests. For each supported predicate pushdown
scenario, write a test that constructs data known to be prunable and data
known not to be prunable, execute the query through the actual planner and
storage layer end to end, and assert both the correctness of the result
and, separately, that the number of bytes or row groups actually read
matches the expected pruned amount, so a regression that silently disables
pruning (a common failure when a predicate is rewritten into a form the
planner no longer recognizes) is caught even when the query's returned
rows are still correct.

Schema evolution tests. Because columnar formats commonly support
adding columns over time (a new column simply has no segments in old row
groups), test that reading old data after a schema change returns the
documented default or null for the new column rather than an error or
misaligned values, and that a reader on the old schema version can still
read data written after the schema changed, if the format claims
backward compatibility.

What became easier because of the pattern. Column-level unit testing
in isolation, since a single column's encoder, compressor, and zone-map
computation can be tested completely independently of every other column,
which a row-oriented format's interleaved layout does not allow as
cleanly.

What became harder. End-to-end row-identity tests, verifying that a
specific logical row's values across all its columns are still correctly
associated with each other after a full write-then-read cycle, because
the correctness of that association now depends on every column segment
and every row group's ordering staying consistent, a property that is
trivially true in a row store and must be explicitly tested here.

## 16. Observability signals

A columnar storage system's health and efficiency are visible in a
characteristic set of metrics that a row-oriented system either does not
have or does not need to watch as closely.

Bytes read versus bytes scanned by the query's logical row count. The
single most informative signal for whether the pattern is delivering its
promised benefit, a large gap between the logical rows a query touches and
the physical bytes it reads indicates column pruning and predicate
pushdown are working, a shrinking gap over time, for a query whose
selectivity has not changed, indicates a regression, most commonly the
wide-zone-map failure mode from dimension 11.

Row group or file count and average file size. A healthy system shows
a stable or slowly growing count of reasonably-sized files or row groups.
A rapidly growing count of very small files, sometimes called the small
files problem in data lake operations, is the clearest observable symptom
of the buffering failure mode from dimension 11 and directly predicts
degrading query latency as the metadata catalog and open-file overhead
grow.

Compression ratio per column, tracked over time. A sudden drop in a
specific column's compression ratio, with no change to the underlying
data's actual distribution, usually indicates an encoding was misselected
or a schema change introduced higher-cardinality or higher-entropy values
into a column that used to compress well.

Zone map pruning rate, the fraction of row groups skipped versus
scanned per query. A dashboard tracking this over the query workload
reveals whether the physical data layout, in particular the sort or
cluster key chosen in the ingestion path, still matches the predicates
the workload is actually issuing, which drifts as query patterns evolve
even when the storage layer itself has not changed.

Write buffer or memtable flush latency and frequency, in systems with a
buffering layer. A healthy system flushes on a predictable cadence sized
to produce well-compressed segments. Increasingly frequent, small flushes
signal the write-amplification failure mode described in dimension 11 and
will manifest downstream as the small-files signal above.

A failing instance, concretely, looks like this. Query latency for a
previously-fast narrow analytical query increases steadily, the bytes-read-
to-logical-rows ratio climbs toward one (meaning pruning has effectively
stopped), file count grows faster than data volume, compaction or merge
background processes fall behind their input rate, visible as a growing
backlog of unmerged small parts.

## 17. Security and privacy implications

Columnar storage changes the shape of several security and privacy
considerations relative to row-oriented storage, some for the better and
some for the worse. This dimension is largely engineering judgement drawn
from how these systems are actually operated, since the format
specifications themselves are mostly silent on security.

Column-level access control becomes structurally easier to enforce
correctly, because a column is already a distinct physical object rather
than a slice of an interleaved row. Systems built on columnar storage, such
as BigQuery's column-level security and Snowflake's column masking policies,
can restrict or mask a specific column without needing to intercept and
rewrite every row read, which is a genuine security benefit of the physical
layout, not merely a policy feature bolted on top.

The same physical separation has a corresponding privacy risk, because a
sensitive column is stored as its own contiguous, often less-encrypted-in-
practice unit, a misconfigured access grant on that one column segment can
expose the sensitive data for an entire table's worth of rows in one file,
whereas a row-oriented leak of one file typically exposes a comparably-sized
slice of both sensitive and non-sensitive columns together, diluting the
blast radius somewhat differently.

Right-to-erasure and other deletion requirements, for example under GDPR,
are meaningfully harder to satisfy correctly against immutable columnar
segments than against a row store's in-place delete. A naive implementation
that only marks a row as deleted in a tombstone or delete vector, per
dimension 5, leaves the actual value physically present in the underlying
compressed segment on disk until a background compaction rewrites that
segment, which means the data is deleted logically but not physically for
an operationally significant window of time, a gap that a compliance review
must account for explicitly rather than assume away.

Compression itself introduces a narrow, well-documented side-channel
category. Compression-oracle attacks such as CRIME and BREACH, described in
Juliano Rizzo and Thai Duong's original CRIME presentation
(https://breachattack.com/, verified
2026-08-18), exploit the fact that compressed output size can leak
information about compressed plaintext content when an attacker can inject
adjacent chosen plaintext and observe the resulting compressed size. This is
a known, real risk in any system compressing attacker-influenced and secret
data together, most famously demonstrated against HTTP response
compression. A columnar store compressing per-column, per-tenant, or
per-user data alongside data an adversary can influence should be evaluated
against this class of attack specifically, rather than assuming
general-purpose compression is a privacy-neutral implementation detail.

## 18. References

1. George P. Copeland and Setrag N. Khoshafian, "A Decomposition Storage
   Model," Proceedings of the 1985 ACM SIGMOD International Conference on
   Management of Data, pages 268-279.
   https://dl.acm.org/doi/10.1145/318898.318923 (verified 2026-08-02).
2. Mike Stonebraker et al., "C-Store. A Column-oriented DBMS," Proceedings
   of the 31st VLDB Conference, 2005.
   https://www.vldb.org/conf/2005/papers/p553-stonebraker.pdf (verified
   2026-08-02).
3. Fay Chang et al., "Bigtable. A Distributed Storage System for Structured
   Data," OSDI 2006.
   https://www.usenix.org/legacy/event/osdi06/tech/chang/chang.pdf (verified
   2026-08-02).
4. Apache Parquet Project, "Parquet File Format."
   https://parquet.apache.org/docs/file-format/ (verified 2026-08-02).
5. Apache ORC Project, "ORC Specification v1."
   https://orc.apache.org/specification/ (verified 2026-08-02).
6. Apache Arrow Project, "Arrow Columnar Format."
   https://arrow.apache.org/docs/format/Columnar.html (verified 2026-08-02).
7. ClickHouse, Inc., "MergeTree Table Engine," ClickHouse Documentation.
   https://clickhouse.com/docs/engines/table-engines/mergetree-family/mergetree
   (verified 2026-08-02).
8. Apache Cassandra Project, "Storage Engine," Cassandra Documentation.
   https://cassandra.apache.org/doc/4.0/cassandra/architecture/storage_engine.html
   (verified 2026-08-18).
9. PingCAP, "TiFlash Overview," TiDB Documentation.
   https://docs.pingcap.com/tidb/stable/tiflash-overview/ (verified
   2026-08-02).
10. Cloudflare, Inc., "How Cloudflare Analyzes 1M DNS Queries per Second,"
    Cloudflare Blog. https://blog.cloudflare.com/how-cloudflare-analyzes-1m-dns-queries-per-second/
    (verified 2026-08-02).
11. Apache Software Foundation, "Parquet," Apache Spark SQL Data Sources
    Guide. https://spark.apache.org/docs/latest/sql-data-sources-parquet.html
    (verified 2026-08-02).
12. Google Cloud, "Storage Internals," BigQuery Documentation.
    https://cloud.google.com/bigquery/docs/storage_overview (verified
    2026-08-02).
13. Snowflake Inc., "Key Concepts and Architecture," Snowflake
    Documentation. https://docs.snowflake.com/en/user-guide/intro-key-concepts
    (verified 2026-08-02).
14. Juliano Rizzo and Thai Duong, "The CRIME Attack," ekoparty 2012,
    documented at breachattack.com. https://breachattack.com/
    (verified 2026-08-18).

## Code examples

The three examples below implement the same small piece of the pattern from
different angles that are each genuinely idiomatic in their language, a
column encoder in TypeScript exercising dictionary and run-length encoding,
a zone-map predicate-pruning scan in Python exercising the read-path pruning
logic from dimension 7, and a row-to-column transpose with delta encoding in
Go exercising the write-path transform from dimension 7. C#, Kotlin, Swift,
and Rust are omitted here because the pattern is a storage-layer physical
technique rather than a language-idiom concern, the three languages chosen
are the ones where columnar engines make the pattern's mechanics most
directly visible, DuckDB embeds an engine callable from Python, Arrow's
canonical JS bindings are TypeScript, and Go is the implementation language
of several real column-store internals such as InfluxDB's TSM engine.

### TypeScript. dictionary and run-length column encoder

```typescript
interface DictionaryEncoded {
  kind: "dictionary";
  dict: string[];
  codes: number[];
}

interface RleEncoded {
  kind: "rle";
  runs: Array<[string, number]>;
}

type Encoded = DictionaryEncoded | RleEncoded;

function dictionaryEncode(column: string[]): DictionaryEncoded {
  const dict: string[] = [];
  const index = new Map<string, number>();
  const codes: number[] = [];
  for (const value of column) {
    let code = index.get(value);
    if (code === undefined) {
      code = dict.length;
      dict.push(value);
      index.set(value, code);
    }
    codes.push(code);
  }
  return { kind: "dictionary", dict, codes };
}

function runLengthEncode(column: string[]): RleEncoded {
  const runs: Array<[string, number]> = [];
  for (const value of column) {
    const last = runs[runs.length - 1];
    if (last && last[0] === value) {
      last[1]++;
    } else {
      runs.push([value, 1]);
    }
  }
  return { kind: "rle", runs };
}

function decode(encoded: Encoded): string[] {
  if (encoded.kind === "dictionary") {
    return encoded.codes.map((code) => encoded.dict[code]);
  }
  const out: string[] = [];
  for (const [value, count] of encoded.runs) {
    for (let i = 0; i < count; i++) out.push(value);
  }
  return out;
}

function bestEncoding(column: string[]): Encoded {
  const rle: RleEncoded = runLengthEncode(column);
  const dict: DictionaryEncoded = dictionaryEncode(column);
  const rleSize = rle.runs.length * 2;
  const dictSize = dict.dict.length + dict.codes.length;
  const chosen: Encoded = rleSize <= dictSize ? rle : dict;
  return chosen;
}

const city = ["NYC", "NYC", "SF", "SF", "SF", "NYC", "LA"];
const chosen = bestEncoding(city);
const roundTrip = decode(chosen);
console.log(chosen.kind, JSON.stringify(chosen));
console.log("round trip matches", JSON.stringify(roundTrip) === JSON.stringify(city));
```

### Python. zone-map predicate pruning over row groups

```python
from dataclasses import dataclass, field


@dataclass
class RowGroup:
    values: list[int]

    @property
    def zone_map(self) -> tuple[int, int]:
        return (min(self.values), max(self.values))


@dataclass
class ColumnarTable:
    row_groups: list[RowGroup] = field(default_factory=list)
    bytes_read: int = 0
    row_groups_scanned: int = 0


def scan_greater_than(table: ColumnarTable, threshold: int) -> list[int]:
    matches: list[int] = []
    table.bytes_read = 0
    table.row_groups_scanned = 0
    for group in table.row_groups:
        low, high = group.zone_map
        if high <= threshold:
            continue
        table.row_groups_scanned += 1
        table.bytes_read += len(group.values) * 8
        matches.extend(value for value in group.values if value > threshold)
    return matches


def build_table(rows: list[int], group_size: int) -> ColumnarTable:
    groups = [
        RowGroup(rows[i : i + group_size])
        for i in range(0, len(rows), group_size)
    ]
    return ColumnarTable(row_groups=groups)


if __name__ == "__main__":
    data = list(range(0, 100)) + list(range(500, 600))
    table = build_table(data, group_size=20)
    result = scan_greater_than(table, threshold=550)
    print(f"matches: {len(result)}")
    print(f"row groups scanned: {table.row_groups_scanned} of {len(table.row_groups)}")
    print(f"bytes read: {table.bytes_read} (vs {len(data) * 8} unpruned)")
    assert result == [v for v in data if v > 550]
    assert table.row_groups_scanned < len(table.row_groups)
    print("pruning verified")
```

### Go. row-to-column transpose with delta encoding

```go
package main

import "fmt"

type Row struct {
	ID        int64
	Timestamp int64
}

func transpose(rows []Row) (ids []int64, timestamps []int64) {
	ids = make([]int64, len(rows))
	timestamps = make([]int64, len(rows))
	for i, r := range rows {
		ids[i] = r.ID
		timestamps[i] = r.Timestamp
	}
	return ids, timestamps
}

func deltaEncode(column []int64) []int64 {
	if len(column) == 0 {
		return nil
	}
	encoded := make([]int64, len(column))
	encoded[0] = column[0]
	for i := 1; i < len(column); i++ {
		encoded[i] = column[i] - column[i-1]
	}
	return encoded
}

func deltaDecode(encoded []int64) []int64 {
	if len(encoded) == 0 {
		return nil
	}
	decoded := make([]int64, len(encoded))
	decoded[0] = encoded[0]
	for i := 1; i < len(encoded); i++ {
		decoded[i] = decoded[i-1] + encoded[i]
	}
	return decoded
}

func main() {
	rows := []Row{
		{ID: 1, Timestamp: 1000},
		{ID: 2, Timestamp: 1010},
		{ID: 3, Timestamp: 1025},
		{ID: 4, Timestamp: 1026},
	}

	_, timestamps := transpose(rows)
	encoded := deltaEncode(timestamps)
	decoded := deltaDecode(encoded)

	fmt.Println("raw column:    ", timestamps)
	fmt.Println("delta encoded: ", encoded)
	fmt.Println("decoded again: ", decoded)

	for i := range timestamps {
		if timestamps[i] != decoded[i] {
			panic("round trip mismatch")
		}
	}
	fmt.Println("round trip verified")
}
```
