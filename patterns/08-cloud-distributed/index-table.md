---
name: Index Table
slug: index-table
family: 08-cloud-distributed
category: Cloud Distributed
aliases: [Secondary Index Table, Lookup Table Pattern, Inverted Index Table]
first_described: "Microsoft Azure Architecture Center, Cloud Design Patterns catalog"
maturity: canonical
related: [sharding, materialized-view, cqrs, cache-aside, gateway-aggregation]
incompatible_with: []
verified: 2026-08-03
---

# Index Table

## 1. Name, aliases, and lineage

The canonical name is Index Table. Microsoft documents it as part of the Cloud
Design Patterns catalog on the Azure Architecture Center, under the storage and
data management category, with the description "create indexes over the fields
in data stores that are frequently referenced by queries" ([Microsoft, Index
Table pattern, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/index-table),
verified 2026-08-03). The catalog groups it beside Sharding, Materialized View,
and CQRS as one of the data management patterns that address a single root
problem, a primary data store that is organized by one key cannot efficiently
answer a query that filters or sorts by a different attribute.

The pattern predates the catalog entry by decades under other names. Relational
database vendors call the underlying mechanism a secondary index, and the SQL
standard has supported `CREATE INDEX` since the earliest commercial systems.
What the Index Table pattern names specifically is the DIY version of a
secondary index, built by the application rather than by the database engine,
for use against a data store that does not provide one natively, or provides
one with characteristics unsuitable for the query at hand.

Three aliases are in real use. **Secondary Index Table** is the term used when
contrasting the pattern with a primary key lookup, matching the relational
vocabulary directly. **Lookup Table Pattern** is used in message-driven and
event-sourced systems to describe a table whose only job is to translate one
identifier into another, which is the normalized variant of this pattern
described in section 8 below. **Inverted Index Table** is the term borrowed
from information retrieval, where a search engine's inverted index (a term
pointing to the set of document identifiers containing it) is a specialised
Index Table whose secondary key is a token rather than an attribute value.
Apache Lucene, the library underlying Elasticsearch and Apache Solr, is
described by its own project documentation as maintaining an inverted-index
structure on disk for this reason. That specific mention of Lucene here is a
cross-reference for the reader's mental model, not a claim independently
re-verified in this pass, and it should be treated as a pointer rather than a
sourced fact about Lucene internals.

The pattern is exclusively a cloud and NoSQL-era concern. In a relational
database the engine builds and maintains secondary indexes for you, and the
Index Table pattern collapses into "add an index," standard relational
database practice not independently attributed to a single source here. The
pattern earns its own name and its own catalog entry because key-value and
wide-column stores, the class of storage Azure Table Storage, Amazon DynamoDB,
Google Cloud Bigtable, and Apache Cassandra all belong to, organize data
strictly by a single primary or partition key and historically offered no
native secondary index, or offer one with sharp constraints on cost,
consistency, and cardinality that a relational secondary index does not carry.
When the native secondary index a store does offer (DynamoDB's Global Secondary
Index, Cassandra's built-in secondary index) turns out to have exactly this
shape internally, the pattern is not obsolete, it has simply moved from
something the application builds by hand into something the vendor builds for
you, using the same structure. Sections 8 and 9 make that continuity explicit.

## 2. Problem and context

A data store organizes its records by a primary key so that, given the key, it
can locate the record in close to constant time. Azure Table Storage does this
with a partition key and row key pair. DynamoDB does it with a partition key,
optionally combined with a sort key. Bigtable and Cassandra do it with a row
key. In every one of these systems a lookup that supplies the primary key is
cheap, because the storage layer physically clusters data by that key, and a
lookup that does not supply the primary key degenerates into a full scan of
every partition, because there is no other structure telling the engine where
to look.

The concrete situation that creates the need for this pattern, an application
stores customer records keyed by Customer ID, and Customer ID is exactly the
right key for the checkout flow, the account page, and every write path. Then
a support dashboard needs to show every customer in Redmond. There is no
Customer ID in that request. Absent an index, the only correct implementation
reads every customer record in the store and discards the ones that do not
match, which is a linear scan whose cost grows with the size of the whole
dataset rather than with the size of the answer, exactly the complaint the
Microsoft catalog entry opens with. "An application might not be able to use
the primary key if it needs to retrieve data based on some other field ... the
application might have to fetch and examine every customer record, which could
be a slow process" ([Microsoft, Index Table pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/index-table),
verified 2026-08-03).

This is not a rare edge case in a cloud system, it is close to the default
shape of an application's query surface. A single logical entity is almost
always queried along more than one dimension over its lifetime, by ID for a
transaction, by town for regional reporting, by signup date for a cohort
analysis, by loyalty tier for a marketing segment. A wide-column or key-value
store gives you exactly one of those dimensions for free. The Index Table
pattern is the general answer to having a store with one fast access path and
needing a second, third, or fourth one, and it applies equally whether the
underlying store is a managed cloud service, a self-hosted Cassandra ring, or
a hand-rolled sharded key-value layer.

The context in which the problem specifically arises has three necessary
conditions. First, the data volume is large enough that a full scan is
genuinely expensive, not merely inelegant. At a few hundred rows a scan is
fine and this pattern is premature engineering. Second, the store either lacks
a native secondary index entirely (early Azure Table Storage, most raw
key-value stores) or its native secondary index carries a cost or consistency
trade-off the application cannot accept as-is (DynamoDB GSIs bill separately
and propagate asynchronously, Cassandra's built-in secondary index performs
badly on high-cardinality or skewed columns, discussed in section 11). Third,
the query pattern is known in advance. This pattern, like every technique in
the NoSQL access-pattern-first school of modeling, requires the application to
name its queries before it names its tables, because the index tables it
builds are shaped by the query, not by the entity.

## 3. Forces

**Read latency against write cost.** Every index table added makes one class
of read fast at the cost of making every write slower, because a write must
now update the fact table and every index table that references the changed
field. This is the central trade of the pattern and it is symmetrical. An
index that is never queried is pure write overhead with zero benefit, and a
query that runs constantly against un-indexed data is pure read overhead with
zero mitigation. The Microsoft catalog states this directly as an issue to
consider, "the overhead of maintaining secondary indexes can be significant...
only create index tables when they're likely to be used regularly" ([Microsoft,
Index Table pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/index-table),
verified 2026-08-03).

**Storage cost against lookup hops.** A fully denormalized index table (the
whole record copied into every index) gives you a single lookup per query at
the price of duplicating the entire dataset once per index. A fully normalized
index table (pointers only, back to the fact table) minimizes storage at the
price of two round trips per query, one to the index and one to the fact
table. This is the same three-way tension every denormalization decision
makes, and the pattern's own solution section names it as a spectrum rather
than a binary choice, with a third, partially normalized strategy sitting
between the two extremes (section 5 and section 8 detail all three).

**Consistency against availability and cost.** The fact table and its index
tables are, in a distributed key-value store, separate physical structures
that cannot generally be updated in one atomic transaction across partitions.
DynamoDB's own documentation states this plainly for its native secondary
indexes. "Global secondary indexes on that table are updated asynchronously,
using an eventually consistent model. Applications never write directly to an
index" ([Amazon Web Services, Using Global Secondary Indexes in DynamoDB, AWS
Documentation](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html),
verified 2026-08-03). An application must therefore choose between accepting a
brief staleness window on index reads, or paying for a stronger, more
expensive coordination mechanism (a distributed transaction, or a queue-based
write path that funnels updates through a single ordered worker) to keep index
and fact table in lockstep. This forces the query surface to design for
eventual consistency as a default, not an exception.

**Query flexibility against operational simplicity.** A composite key index
table, where the index key concatenates two or more attributes, can answer a
compound query with a single lookup (customers in Redmond named Smith), but
every new compound query the application discovers it needs, after the system
is live, either requires a new index table or a fallback scan. This trades the
long-term flexibility a relational secondary index or an ad hoc query language
gives you for the up-front performance of a purpose-built structure, and it
means the pattern couples the schema to the query surface far more tightly
than a normalized relational schema does.

**Cognitive load and team topology.** A team operating a service that owns a
fact table and three hand-built index tables now owns four write paths that
must be kept synchronized, four sets of retry and idempotency logic, and four
places a schema migration must touch. This is a meaningful increase in the
surface area an on-call engineer must understand compared to a single table
with a database-managed index, and it is the primary reason engineering teams
prefer a managed secondary index (DynamoDB GSI, Cosmos DB's automatic
indexing) over hand-rolled index tables whenever the managed option's
consistency and cost model is acceptable, deferring to the DIY pattern only
when it is not.

## 4. Applicability and non-applicability

**Reach for the Index Table pattern when.**

- The primary data store does not provide a native secondary index at all, or
  the query needs to run against a store category (a blob store, a raw
  key-value cache, a hand-sharded key space) where a secondary index is not a
  concept the storage layer understands.
- The application's own store does offer a native secondary index, but its
  cost model (per-index provisioned or on-demand capacity), its consistency
  model (asynchronous propagation), or its cardinality constraints (poor
  behavior on low-cardinality or highly skewed columns) make it a poor fit for
  a specific, known, high-volume query.
- The query needs to run against a compound predicate (town and last name) or
  in a specific sort order that a single-attribute native index cannot serve
  in one lookup, and a composite-key index table can serve it in one.
- The underlying store shards or hashes its primary key, so the primary key
  itself carries no useful ordering, and the query needs results ordered or
  grouped by a human-meaningful attribute the hashed key destroys. This is
  exactly the sharded-data case the catalog describes. An index table "can
  organize data by the nonhashed value ... and provide the hashed shard key as
  the lookup data. This can save the application from repeatedly calculating
  hash keys" ([Microsoft, Index Table pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/index-table),
  verified 2026-08-03).
- The query pattern is known, stable, and executed frequently enough that the
  write overhead of maintaining the index is smaller than the aggregate cost
  of scanning for it on every read.

**Do NOT reach for this pattern when.**

- The data store already provides a general-purpose query engine over
  arbitrary fields with acceptable performance and cost, most obviously a
  relational database with `CREATE INDEX`, or a document store whose
  general-purpose index (MongoDB's B-tree indexes are the clearest example)
  already covers the field. Indexes there "are special data structures that
  store a small portion of the collection's data set in an easy-to-traverse
  form... ordered by the value of the field," and without one, "MongoDB must
  scan every document in a collection to return query results" ([MongoDB,
  Inc., Indexes, MongoDB Manual](https://www.mongodb.com/docs/manual/indexes/),
  verified 2026-08-03). Building a hand-rolled index table on top of a store
  that already indexes the field natively duplicates work the engine already
  does for free and introduces a second write path with no benefit.
- The field selected as the secondary key has low cardinality, meaning it
  takes only a small handful of distinct values across the whole dataset (the
  catalog's own example is gender). An index table over such a field groups
  most of the dataset into a tiny number of buckets, so a query against it
  still returns and must filter a large fraction of the data, and the
  maintenance overhead is rarely repaid.
- The value distribution for the secondary key is highly skewed, for example
  ninety percent of rows sharing one value, unless the queries that matter
  overwhelmingly target the remaining ten percent. The catalog names this
  exact condition as a reason the pattern "might not be useful" ([Microsoft,
  Index Table pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/index-table),
  verified 2026-08-03).
- The underlying data changes so frequently, relative to how often it is
  queried by the secondary key, that the index table would be perpetually
  stale or the write amplification from keeping it current would dwarf the
  read savings. The catalog states this as "an index table can become out of
  date very quickly, making it ineffective."
- The application needs strict, immediate rather than eventual consistency
  between a write and the very next read through the secondary key, and the
  team is not prepared to build the extra coordination (a transactional
  write, or a synchronous dual write inside one request) that consistency
  requires. If that coordination is out of scope, a normalized relational
  store with a native secondary index is very frequently the better default,
  because the engine gives you that consistency for free.
- The query is a one-off, ad hoc, or exploratory analytical query rather than
  a stable, repeated access pattern. A data warehouse or an OLAP layer
  (columnar storage, batch ETL into an analytics store) is the better tool for
  arbitrary slicing over a large dataset, and building a bespoke index table
  per analyst question does not scale.

## 5. Structure

- **Fact table.** The store of record. Organized by the primary or partition
  key the application's dominant write path and dominant read path both use.
  Every field the application ultimately needs to serve lives here, in full.
- **Index key.** The non-primary attribute, or the concatenation of several
  attributes, that a query needs to filter or sort by. This becomes the
  partition or lookup key of an index table.
- **Index table, denormalized variant.** A second physical table, keyed by the
  index key, holding a full copy of every field a query against that key
  might need. No dependency on the fact table at read time.
- **Index table, normalized variant.** A second physical table, keyed by the
  index key, holding only the primary key of the matching fact table row (a
  pointer). A query against this table is always a two-step lookup, find the
  primary key here, then fetch the full record from the fact table.
- **Index table, partially normalized variant.** A hybrid. The index table
  carries the primary key pointer plus the small set of fields most commonly
  needed alongside that lookup, and falls back to the fact table only for the
  remaining, less frequently accessed fields.
- **Write coordinator.** The component responsible for keeping the fact table
  and every index table consistent on every insert, update, and delete. In its
  simplest form this is application code performing sequential writes inside
  one request. Its sturdier form is a message queue or change-data-
  capture stream that fans a single logical write out to every dependent
  index asynchronously, trading immediate consistency for durability and
  decoupling.
- **Query router (implicit).** The part of the application, or the query
  planner of a managed index feature, that decides which physical table (fact
  or one of the index tables) a given incoming query should be directed at,
  based on which fields the query filters or sorts by.

## 6. ASCII structure diagram

```
                         WRITE PATH
                         ----------
        +-----------------------+
        |     Application       |
        |  (insert / update /   |
        |       delete)         |
        +-----------+-----------+
                    |
                    v
        +-----------------------+
        |   Write Coordinator    |
        |  (sequential writes    |
        |   or async fan-out)    |
        +---+-----------+-------+
            |           |
            v           v
  +-------------+   +-------------------+   +-------------------+
  |  Fact Table |   | Index Table  Town  |   | Index Table       |
  |  key=CustID |-->|  key = Town        |   | Town + LastName   |
  |  full record|   |  denormalized OR   |   |  composite key,   |
  +-------------+   |  normalized (id)   |   |  sorted           |
                    +-------------------+   +-------------------+

                         READ PATH
                         ----------
   Query, "by CustID"          Query, "by Town"       Query, "Town+LastName"
        |                            |                        |
        v                            v                        v
  +-------------+           +-------------------+     +-------------------+
  |  Fact Table |           | Index Table  Town  |     | Index Table       |
  | direct hit  |           | one lookup, or two |     | Town + LastName   |
  +-------------+           | if normalized      |     | one range lookup  |
                             +-------------------+     +-------------------+
```

## 7. Dynamics

```
sequence, WRITE, denormalized strategy, synchronous coordinator
-----------------------------------------------------------------
Client -> App:            insert Customer(id=c1, town=Redmond, ...)
App -> Coordinator:       persist(c1)
Coordinator -> FactTable: put(c1, full record)
FactTable -> Coordinator: ack
Coordinator -> IndexTable(Town): put(key=Redmond, value=full record copy)
IndexTable(Town) -> Coordinator: ack
Coordinator -> App:       success
App -> Client:            201 Created

  If the second put fails after the first succeeds, the fact table and
  the index table are now inconsistent, and the coordinator must retry
  or emit a repair signal, never report success to the client while an
  index write is still outstanding without a defined reconciliation plan.

sequence, WRITE, normalized strategy, async fan-out via queue
-----------------------------------------------------------------
Client -> App:            insert Customer(id=c1, town=Redmond, ...)
App -> FactTable:         put(c1, full record)     [synchronous, in request]
FactTable -> App:         ack
App -> Client:            201 Created              [request completes here]
App -> Queue:             publish IndexUpdate(c1, town=Redmond)
Queue -> IndexWorker:     deliver IndexUpdate
IndexWorker -> IndexTable(Town): put(key=Redmond, value=pointer c1)
IndexTable(Town) -> IndexWorker: ack

  The client's write is durable and fast. The index table becomes
  correct within a bounded but nonzero window, this is the eventual
  consistency this rule keeps calling out. A read against
  IndexTable(Town) issued in that window may miss c1.

sequence, READ, normalized strategy, two-hop lookup
-----------------------------------------------------
Client -> App:             query customers where town = Redmond
App -> IndexTable(Town):   query(key=Redmond)
IndexTable(Town) -> App:   [pointer c1, pointer c2]
App -> FactTable:          batchGet([c1, c2])
FactTable -> App:          [full record c1, full record c2]
App -> Client:              [c1, c2]
```

## 8. Implementation variants

**Fully denormalized index table.** The entire fact record, or every field a
query might need, is duplicated into the index table under the secondary key.
This is the first of the three strategies the Microsoft catalog names. "The
first strategy is to duplicate the data in each index table but organize it by
different keys (complete denormalization)... appropriate if the data is
relatively static compared to the number of times it's queried using each
key" ([Microsoft, Index Table pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/index-table),
verified 2026-08-03). Best fit for read-heavy, write-light data, and for
stores where a single lookup is materially cheaper than two (most wide-column
and key-value stores charge per request, so a single lookup halves the read
cost as well as the latency).

**Fully normalized index table, fact table plus pointer.** The index table
stores only the secondary key mapped to the primary key of the matching fact
row. The query issuer performs a second lookup against the fact table to
retrieve the full record. The catalog calls this the second strategy, and it
"saves space and reduces the overhead of maintaining duplicate data. The
disadvantage is that an application has to perform two lookup operations"
([Microsoft, Index Table pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/index-table),
verified 2026-08-03). Best fit when the fact records are large, storage cost
dominates, or writes are frequent enough that maintaining duplicate copies
across many index tables becomes the bottleneck.

**Partially normalized index table.** A hybrid that duplicates only the small
set of fields the query most commonly needs directly out of the index lookup
(display fields for a list view, for example), while falling back to the fact
table via the pointer for anything less common. The catalog names this the
third strategy and frames it as the practical default. "You can strike a
balance between the first two approaches. The data for common queries can be
retrieved quickly by using a single lookup, while the space and maintenance
overhead isn't as significant as duplicating the entire data set" ([Microsoft,
Index Table pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/index-table),
verified 2026-08-03).

**Composite-key index table.** The index key is a concatenation of two or more
attributes (town then last name), so a single lookup can serve a compound
predicate and the results arrive pre-sorted by the trailing attribute within
each leading-attribute group, exactly as the catalog's figure five describes.
The generalisation of this in a managed store is exposed directly by
DynamoDB's multi-attribute key feature for Global Secondary Indexes, which
lets a partition key be composed from up to four attributes and a sort key
from up to four more, so that "instead of creating composite strings like
TOURNAMENT#WINTER2024#REGION#NA-EAST, you can use the natural attributes from
your domain model directly" ([Amazon Web Services, Using Global Secondary
Indexes in DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html),
verified 2026-08-03), the managed-service equivalent of hand-encoding a
composite key string, saving the application the concatenation and parsing
logic.

**Index table over a sharded fact table.** When the fact table's primary key
is itself a hash (chosen to spread load evenly across shards, and therefore
useless for range queries or human-meaningful ordering), the index table
stores the human-meaningful attribute as its key and the hashed shard key as
its value, so "the application from repeatedly calculating hash keys (an
expensive operation)" is avoided ([Microsoft, Index Table pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/index-table),
verified 2026-08-03). This variant composes directly with the Sharding
pattern, the index table becomes the routing layer that tells a query which
shard to visit.

**Vendor-managed secondary index as the same pattern, automated.** DynamoDB's
Global Secondary Index is, structurally, exactly the normalized-plus-partial
index table variant, built and maintained by the database engine rather than
by application code. "A global secondary index contains a selection of
attributes from the base table, but they are organized by a primary key that
is different from that of the table... DynamoDB automatically synchronizes
each global secondary index with its base table... updated asynchronously,
using an eventually consistent model" ([Amazon Web Services, Using Global
Secondary Indexes in DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html),
verified 2026-08-03). Choosing this variant trades hand-rolled control (you
decide exactly what is duplicated and how writes are coordinated) for
operational simplicity, the vendor's write path handles the fan-out and the
consistency window for you, at the vendor's own pricing for the index's
provisioned or on-demand throughput. Apache Cassandra offers a comparable
built-in mechanism, but its native secondary index is a per-node local index
rather than a globally coordinated one, "stored locally on each node in a
hidden table and built in a background process," and it is explicitly not a
drop-in replacement for a hand-built index table on high-cardinality data,
because "querying for a particular value of a non-primary key column results
in scanning all partitions" unless the query also supplies the partition key
([DataStax, Cassandra 3.0, Indexing internals in Cassandra](https://docs.datastax.com/en/cassandra-oss/3.0/cassandra/dml/dmlIndexInternals.html),
verified 2026-08-03). This is precisely why Cassandra's own guidance,
according to the same source, favors building "a materialized view or
additional table" ordered by the query attribute over relying on the built-in
secondary index for anything beyond low-cardinality, partition-scoped lookups,
which is the query-first, hand-built Index Table strategy by another name.

## 9. Known production uses

**Amazon DynamoDB Global Secondary Indexes.** Every DynamoDB table that needs
to serve a query by an attribute other than its own partition key uses a GSI,
which is a vendor-implemented, eventually consistent index table maintained
automatically alongside the base table, documented in full in AWS's own
developer guide, including the explicit statement that GSIs support
"eventually consistent reads" only and that write capacity is billed and
throttled separately from the base table's ([Amazon Web Services, Using Global
Secondary Indexes in DynamoDB, AWS Documentation](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html),
verified 2026-08-03).

**Google Cloud Bigtable and Bigtable-derived systems at Google.** Bigtable's
own data model is a single, sorted index by row key with no secondary index
support at all, described as "a sparse, distributed multi-dimensional sorted
map" indexed by row key, column key, and timestamp ([Wikipedia, summarising
the original OSDI 2006 Bigtable paper by Chang et al., Bigtable article](https://en.wikipedia.org/wiki/Bigtable),
verified 2026-08-03). Because Bigtable itself offers only that one access
path, every Google product built on it that needs a second access path,
publicly documented users include Google Analytics, Google Maps, Gmail, Google
Earth, and web indexing, must maintain its own application-level index tables
or route through a layer that does, which is the textbook trigger condition
for this pattern at planetary scale ([Wikipedia, Bigtable article, listing
Bigtable's application base](https://en.wikipedia.org/wiki/Bigtable), verified
2026-08-03).

**Azure Storage, the pattern's own worked example.** Microsoft's catalog entry
documents Azure Table Storage's own limitation directly. Partitions are
optimized for a contiguous range of row keys within one partition key, and a
movies application that needs to query by genre and by starring actor from one
dataset must build a second Azure table, keyed by actor, acting purely as an
index table over the genre-partitioned fact table ([Microsoft, Index Table
pattern, Example section](https://learn.microsoft.com/en-us/azure/architecture/patterns/index-table),
verified 2026-08-03), a first-party, vendor-authored production illustration
of the pattern rather than a third-party inference about it.

**Apache Cassandra deployments using denormalized query tables.** Cassandra's
own documentation instructs operators to build a second, differently-keyed
table (functionally an index table) whenever a query needs to filter by a
non-partition-key column at scale, rather than lean on the built-in secondary
index, explicitly recommending "a materialized view or additional table that
is ordered by age" as the better solution to that exact class of query
([DataStax, Cassandra 3.0, Indexing internals in Cassandra](https://docs.datastax.com/en/cassandra-oss/3.0/cassandra/dml/dmlIndexInternals.html),
verified 2026-08-03). This is the query-first, denormalize-per-access-pattern
modeling discipline that underpins virtually every large Cassandra deployment,
and it is the Index Table pattern applied at the schema-design level rather
than as an afterthought.

## 10. Consequences

**Positive.**

- Converts a scan whose cost grows with the whole dataset into a lookup whose
  cost is close to constant against a purpose-built index table for the
  specific query the index was built for, independent of whether the
  underlying store has any native query planner at all.
- Works against stores with no query language and no native secondary index,
  which is otherwise a hard blocker for any query not keyed by the primary
  key.
- Lets an application serve a compound or ordered query in a single lookup by
  choosing a composite index key, avoiding an application-side join or
  multi-step filter.
- Decouples the shape of the write-optimized fact table from the shape of a
  read-optimized index, which composes naturally with CQRS. The fact table can
  stay a pure write model while one or more index tables serve as
  purpose-built read models.
- Scales horizontally in the same way the underlying store does. An index
  table is just another table in the same store, subject to the same
  partitioning and replication guarantees, so it inherits the store's own
  availability and throughput characteristics rather than introducing a
  separate scaling bottleneck.

**Negative.**

- Multiplies the number of writes per logical change by the number of index
  tables that reference the changed field, directly increasing write latency,
  write cost, and the number of places a partial failure can leave data
  inconsistent.
- Introduces an eventual consistency window between the fact table and every
  asynchronously updated index table, which is a correctness concern the
  application must design around explicitly (stale reads, and the possibility
  that an index entry outlives the fact row it once pointed to).
- Adds schema and code surface. Every index table needs its own write path,
  its own retry and idempotency handling, and its own migration story when the
  query pattern changes.
- Duplicated data in the denormalized variant multiplies storage cost roughly
  by the number of index tables, and every duplicate copy is another place a
  bug can leave the two views of the same fact disagreeing.
- A query the application did not anticipate when it designed its index tables
  has no fast path at all. The pattern trades general-purpose flexibility for
  purpose-built speed, and that trade is not reversible without a schema
  change and a backfill.

## 11. Failure modes and misuse

| Symptom | Cause | Fix |
|---|---|---|
| A dashboard or report intermittently returns a customer that was deleted seconds ago, or misses one that was just created | Index table updated asynchronously, and a read landed inside the eventual-consistency propagation window | Design the read path to tolerate staleness explicitly (label results as current as of a timestamp, or re-verify against the fact table for anything transactional), or move that specific write to a synchronous dual-write path if true immediate consistency is required |
| Write latency on the fact table climbs steadily as the team adds one more index table over time | Every write now fans out serially to N index tables inside the same request, and N kept growing | Move index maintenance off the request's critical path onto an asynchronous queue or change-data-capture stream, and audit whether every existing index table is still queried, retire unused ones |
| A query against an index table built over a low-cardinality field (status, gender, plan tier) is no faster than scanning the fact table directly | The index groups nearly the whole dataset into a handful of buckets, so a lookup still returns and filters a large fraction of the data | Do not index low-cardinality fields with this pattern. If the query is legitimate and frequent, add a compound key that narrows the bucket (status plus signup month, for example), or accept the scan |
| A production incident where an index table shows a stale value for a field that has since changed on the fact table, weeks after the change, with no error ever logged | The write coordinator's index-update step failed silently on one attempt (a transient timeout, a deploy mid-write) and no reconciliation job ever repaired it | Add an explicit reconciliation or repair job that periodically diffs fact table and index table and re-syncs drift, and alert on any index-write failure rather than swallowing it |
| A Cassandra-backed service queries its own built-in secondary index on a high-cardinality column and read latency spikes under load | The built-in local secondary index scans every node's partitions because the query did not also specify a partition key, exactly the condition Cassandra's own documentation warns against | Replace the built-in secondary index query with a hand-built, partition-keyed index table (or a materialized view) shaped for that specific query, per Cassandra's own guidance |
| Storage cost on the index tables alone exceeds the fact table's storage cost, and nobody notices until the monthly bill | The denormalized variant was chosen for every index without weighing storage cost, and the fact records are large | Reassess field duplication using the normalized or partially normalized variant for large records, projecting only the fields the query genuinely needs |
| A migration adds a new field to the fact table, and queries against an existing index table silently never see it | The index table's denormalized copy is a snapshot shape frozen at write time. Adding a fact-table field does not retroactively populate the index | Treat every fact-table schema change as a migration that also touches every index table it feeds, with an explicit backfill step, never assume propagation is automatic |

## 12. Trade-off matrix

| Concern | Index Table (this pattern) | Native RDBMS secondary index | Materialized View | CQRS with a dedicated read store |
|---|---|---|---|---|
| Consistency with source of truth | Application-defined, usually eventual | Strong, transactional, same engine | Usually eventual, refresh-driven | Usually eventual, event-driven |
| Query flexibility | Narrow, one query shape per index | Broad, arbitrary predicates via the query planner | Narrow, one shape per view definition | Broad within the read model's own schema |
| Who maintains it | Application code or a hand-built worker | The database engine, automatically | The database engine or a scheduled refresh job | A dedicated projection/consumer service |
| Write cost per change | One extra write per index table touched | Amortized into the engine's index maintenance, still nonzero but transactional | Deferred to refresh time, not per write | One event publish, fan-out is async and decoupled |
| Fit for key-value or wide-column stores with no native index | Purpose-built for exactly this gap | Not applicable, RDBMS-only | Sometimes available (Cassandra materialized views) | Yes, and often layered on top of an Index Table internally |
| Operational surface added | One new table plus a write-coordination path per index | None beyond the index definition itself | One view definition plus refresh scheduling | A full separate service or projection pipeline |
| Best used when | Store lacks a native index or the native one's cost/consistency model does not fit a specific hot query | The engine's own optimizer and transactional guarantees are sufficient | The read shape is a stable aggregate over the source data | The read and write workloads have fundamentally different scaling or modeling needs |

## 13. Related and incompatible patterns

**Sharding.** Sharding distributes the fact table itself across many physical
partitions by a shard key, and that shard key is very often a hash chosen for
even load distribution rather than for query utility. An Index Table is the
natural companion that restores a human-meaningful access path on top of a
sharded fact table, exactly the sharded-data example in section 8. The two
patterns compose rather than compete.

**Materialized View.** A materialized view is a stored, precomputed result of
a query, typically an aggregate or a join, refreshed on a schedule or on
change. An Index Table is a narrower, more mechanical special case. It does
not aggregate or transform the data, it only reorders and republishes it under
a different key. Where a materialized view answers "what is the total revenue
per region," an index table answers "which rows have region equal to X."
Some stores (Cassandra materialized views, for instance) blur this line by
implementing their native materialized view feature as, internally, an
index-table-shaped structure the engine maintains for you.

**CQRS.** CQRS separates the write model from the read model at the
architectural level, often via an event stream feeding one or more dedicated
read stores. An Index Table is frequently the concrete mechanism a CQRS read
side uses to serve a specific query shape. The pattern relationship is
compositional, an Index Table is a small, single-query instance of the
broader CQRS idea, not a substitute for it.

**Cache-Aside.** Cache-Aside caches the result of an expensive lookup and
invalidates or expires it. An Index Table is a durable, always-current
(subject to its own consistency window) structure that IS the lookup path,
not a cache of one. The two are complementary, an application can cache the
result of a query against an index table exactly as it would cache a query
against the fact table.

**Gateway Aggregation.** Where Gateway Aggregation composes results from
multiple backend calls at the API boundary, an Index Table composes results
from multiple physical tables (index plus fact, in the normalized variant)
inside a single logical query. They operate at different layers and do not
conflict, and a gateway can sit in front of a service that itself uses index
tables internally.

**Incompatible with.** A storage engine or access pattern that requires a
single, globally strongly consistent view across fact and index at all times
with no tolerance for propagation delay and no willingness to pay for
synchronous coordination. In that specific combination of requirements, an
Index Table built with asynchronous propagation is the wrong tool, and either
a synchronous dual-write (accepting the added latency and failure coupling) or
a genuinely transactional relational secondary index is the correct choice
instead.

## 14. Refactoring path in and out

**Introducing the pattern.**

1. Identify the specific, recurring query that currently forces a full scan
   or an unacceptably slow filter against the fact table. Do not build an
   index table speculatively, the catalog is explicit that speculative index
   tables cost more than they save.
2. Decide the index key. A single attribute for a simple filter, a composite
   key for a compound or ordered query, the hashed shard key as the value if
   the fact table is itself sharded.
3. Choose the denormalization strategy (full, normalized-pointer-only, or
   partial) based on record size, write frequency, and how much of the record
   the target query actually needs.
4. Build the write coordinator. Start with the simplest correct option, a
   synchronous sequential write inside the same request, and only move to an
   asynchronous queue-based fan-out once write latency or partial-failure
   handling actually demands it. Do not reach for asynchronous coordination
   before the synchronous version has shown a real problem.
5. Backfill the index table from the existing fact table data, ideally via a
   batch job that reuses the same write path the live coordinator uses, so
   there is only one code path to trust.
6. Route the target query to the new index table and verify, under
   production-representative load, that results match a full scan of the fact
   table for a sampled set of predicates before fully cutting over.
7. Monitor propagation lag if the coordinator is asynchronous, and alert on
   any index-write failure from day one, not after the first incident.

**Removing the pattern.**

1. Confirm the query the index table served is genuinely no longer executed,
   or has moved to a store or engine (a managed secondary index, a search
   index, an OLAP layer) that now serves it natively.
2. Stop the write coordinator from writing to the index table first, before
   deleting the table itself, and watch for any latent consumer still reading
   from it.
3. Archive or snapshot the index table's data before deletion if there is any
   chance an audit or a rollback needs it, consistent with a general
   no-silent-data-loss discipline during any schema removal.
4. Delete the index table and its write-coordination code only after a soak
   period confirms nothing still depends on it, and remove the corresponding
   capacity or index-specific billing configuration on the provider side (for
   a managed GSI, this also stops the separate throughput billing for that
   index).

## 15. Testing and verification

An Index Table's correctness has two independent things to test, that the
index returns the right rows for a given key, and that the index and the fact
table never drift apart in a way the application does not expect. Because the
pattern is purely mechanical (no business transformation happens inside it),
unit testing the write coordinator against a fake in-memory fact table and
in-memory index table (exactly the shape of the code examples in the code
section below) is inexpensive and catches most logic bugs before they reach a
real store. Verify that inserting a record produces the expected entry in
every index table, that updating the indexed field removes the old index
entry and adds the new one, and that deleting the fact row removes every index
entry that referenced it.

Consistency-window testing is the part teams skip and should not. Write an
integration test that performs a write, immediately issues a read against the
index table (not the fact table), and asserts on the store's actual, current
behavior. If the store is synchronous, the read must see the write every
time. If the store is eventually consistent (a native GSI, or a hand-built
asynchronous coordinator), the test should assert the eventual state is
correct within a bounded retry window rather than asserting immediate
visibility, and it should be paired with a second test that explicitly
demonstrates the staleness window exists, so a future refactor cannot silently
assume synchronous behavior it does not have.

Reconciliation testing verifies the repair path. Deliberately fail the
index-write half of a coordinated write (kill the process, drop the message,
simulate a timeout) and confirm the reconciliation job, or the next scheduled
repair pass, brings the index table back in line with the fact table without
manual intervention. A test suite that never exercises this path is testing
only the happy path of a pattern whose entire risk profile lives in the
unhappy path.

For a composite-key index table, add boundary tests around key construction.
Verify that a value containing the delimiter character used to build the
composite key (a literal hash mark in a field value, for the examples in this
entry) does not silently corrupt the key, and that range queries against the
composite key return results in the expected sort order, not merely the
expected set.

## 16. Observability signals

Track, per index table, write success rate and write latency for the
index-specific step of the coordinator, distinct from the fact table's own
write latency, so a regression in index maintenance is visible without being
masked by an otherwise-healthy fact table write path. Track propagation lag
directly for any asynchronous coordinator, the time between a fact table write
and the corresponding index table write becoming visible, and alert on lag
exceeding an agreed service-level objective rather than only on outright
failure.

Track query volume against each index table individually. An index table
whose query rate has dropped to zero over an observation window is a strong
signal it should be retired, following the pattern's own guidance to only
maintain indexes that are used regularly. This is the single most direct
metric for catching the built-it-speculatively-and-nobody-queries-it-anymore
failure mode named in section 4.

Track reconciliation job outcomes explicitly, how many drifted rows it found
and repaired per run, over time. A healthy system shows this metric at or near
zero. A rising trend is an early warning that the write coordinator is failing
silently somewhere upstream of the reconciliation job's visibility, and it is
a leading indicator that should fire well before a user-visible staleness
complaint does.

For a managed secondary index (a DynamoDB GSI, for instance), surface the
provider's own index-specific throughput and throttling metrics separately
from the base table's, because a GSI can be throttled by its own,
independently provisioned capacity even while the base table has capacity to
spare, and that throttling in turn throttles writes to the base table itself
when the index cannot keep up, exactly as AWS's own documentation warns.
"Write operations to the base table can be throttled if the GSI activity
resulting from writes to the base table exceeds the GSI's provisioned write
capacity" ([Amazon Web Services, Using Global Secondary Indexes in DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html),
verified 2026-08-03).

## 17. Security and privacy implications

An index table duplicates data, and every duplicate is a second place the
same sensitive field lives, with its own access control surface, its own
encryption-at-rest configuration, and its own retention lifecycle. A fact
table that correctly applies field-level access control or masking to a
sensitive attribute gains nothing from that control if a denormalized index
table copies the same attribute unmasked into a differently-secured table.
The access policy has to be reapplied, deliberately, per index table, and
this is a genuine and easy-to-miss attack surface expansion specific to the
denormalized variant of this pattern (engineering judgement, not a sourced
claim about any specific vendor).

Deletion and right-to-be-forgotten obligations are harder to satisfy correctly
once an index table exists, because a deletion request against the fact table
does not automatically imply the corresponding entries in every index table
are also removed unless the write coordinator explicitly handles delete
propagation with the same rigor it handles insert and update propagation. An
incomplete delete path is a real and recurring source of residual personal
data left in an index table long after the fact record itself was purged
(engineering judgement).

A composite-key index table built from personally identifiable fields
(surname plus town, in this entry's running example) can itself become a
sensitive artifact even when neither field is separately classified as
sensitive, because the combination narrows re-identification risk. Access
control and audit logging on an index table deserve the same review as on the
fact table it derives from, not an automatic pass for being merely an index
(engineering judgement).

The eventual consistency window an asynchronous index coordinator introduces
also has a security-adjacent implication, an authorization check that reads
from a stale index table (for example, checking whether a user is still a
member of a group, served from an index rather than the fact table) can grant
access based on data that has already changed on the source of truth. Any
authorization-relevant query should either read from the fact table directly,
or be served from an index table with an explicit, monitored bound on
staleness that the security review has accepted (engineering judgement).

## 18. References

1. Microsoft, "Index Table pattern," Azure Architecture Center, Cloud Design
   Patterns catalog. https://learn.microsoft.com/en-us/azure/architecture/patterns/index-table.
   Verified 2026-08-03.
2. Amazon Web Services, "Using Global Secondary Indexes in DynamoDB," Amazon
   DynamoDB Developer Guide. https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html.
   Verified 2026-08-03.
3. MongoDB, Inc., "Indexes," MongoDB Manual. https://www.mongodb.com/docs/manual/indexes/.
   Verified 2026-08-03.
4. DataStax, "Indexing internals in Cassandra," Cassandra 3.0 documentation.
   https://docs.datastax.com/en/cassandra-oss/3.0/cassandra/dml/dmlIndexInternals.html.
   Verified 2026-08-03.
5. Wikipedia contributors, "Bigtable," summarising Fay Chang et al., "Bigtable,
   A Distributed Storage System for Structured Data," OSDI 2006.
   https://en.wikipedia.org/wiki/Bigtable. Verified 2026-08-03.
6. Apache Lucene project, Lucene 9.11 core index file format overview,
   consulted only as a cross-reference for the "inverted index" alias and not
   independently re-verified in this pass.
   https://lucene.apache.org/core/9_11_0/core/org/apache/lucene/codecs/lucene99/package-summary.html.

## Code examples

Three variants are shown, one per denormalization strategy from section 8, in
three different languages, each compiled or run directly against the local
toolchain before inclusion here.

### TypeScript, fully denormalized index table

Compiled with `npx tsc --target es2020 --module commonjs` and run with `node`.
Both succeeded and printed `c1,c2` as expected.

```typescript
type Customer = { id: string; town: string; lastName: string };

class DenormalizedIndex {
  private byTown = new Map<string, Customer[]>();

  insert(c: Customer): void {
    const bucket = this.byTown.get(c.town) ?? [];
    bucket.push(c);
    this.byTown.set(c.town, bucket);
  }

  queryByTown(town: string): Customer[] {
    return this.byTown.get(town) ?? [];
  }
}

const idx = new DenormalizedIndex();
idx.insert({ id: "c1", town: "Redmond", lastName: "Smith" });
idx.insert({ id: "c2", town: "Redmond", lastName: "Nguyen" });
idx.insert({ id: "c3", town: "Cloppenburg", lastName: "Bauer" });

const result = idx.queryByTown("Redmond");
console.log(result.map((c) => c.id).join(","));
```

The full record is copied into the index bucket keyed by town, so a query
never touches the fact table at all. This is the strategy to reach for when
the record is small and the field is read far more often than it is written.

### Python, normalized index table with a fact table pointer

Run with `python3`. Printed `c1,c2` as expected.

```python
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Customer:
    id: str
    town: str
    last_name: str


class FactTable:
    def __init__(self) -> None:
        self._rows: Dict[str, Customer] = {}

    def put(self, c: Customer) -> None:
        self._rows[c.id] = c

    def get(self, customer_id: str) -> Customer:
        return self._rows[customer_id]


class NormalizedTownIndex:
    def __init__(self, fact_table: FactTable) -> None:
        self._fact_table = fact_table
        self._pointers: Dict[str, List[str]] = {}

    def index(self, c: Customer) -> None:
        self._pointers.setdefault(c.town, []).append(c.id)

    def query(self, town: str) -> List[Customer]:
        ids = self._pointers.get(town, [])
        return [self._fact_table.get(i) for i in ids]


fact = FactTable()
idx = NormalizedTownIndex(fact)
for c in [
    Customer("c1", "Redmond", "Smith"),
    Customer("c2", "Redmond", "Nguyen"),
    Customer("c3", "Cloppenburg", "Bauer"),
]:
    fact.put(c)
    idx.index(c)

print(",".join(c.id for c in idx.query("Redmond")))
```

The index table stores only primary key pointers, keeping its own footprint
small. Every query pays a second lookup against `FactTable.get`, which is the
cost the section 3 forces discussion names directly, storage against latency.

### Go, composite-key index table over a sharded fact table

Run with `go run main.go`. Printed `c1,c2` as expected.

```go
package main

import (
	"fmt"
	"sort"
	"strings"
)

type customer struct {
	id       string
	town     string
	lastName string
}

type compositeKeyIndex struct {
	entries map[string][]customer
}

func newCompositeKeyIndex() *compositeKeyIndex {
	return &compositeKeyIndex{entries: make(map[string][]customer)}
}

func (i *compositeKeyIndex) key(town, lastName string) string {
	return town + "#" + lastName
}

func (i *compositeKeyIndex) insert(c customer) {
	k := i.key(c.town, c.lastName)
	i.entries[k] = append(i.entries[k], c)
}

func (i *compositeKeyIndex) queryPrefix(town string) []customer {
	var out []customer
	prefix := town + "#"
	for k, v := range i.entries {
		if strings.HasPrefix(k, prefix) {
			out = append(out, v...)
		}
	}
	sort.Slice(out, func(a, b int) bool { return out[a].id < out[b].id })
	return out
}

func main() {
	idx := newCompositeKeyIndex()
	idx.insert(customer{"c1", "Redmond", "Smith"})
	idx.insert(customer{"c2", "Redmond", "Nguyen"})
	idx.insert(customer{"c3", "Cloppenburg", "Bauer"})

	ids := []string{}
	for _, c := range idx.queryPrefix("Redmond") {
		ids = append(ids, c.id)
	}
	fmt.Println(strings.Join(ids, ","))
}
```

The key concatenates town and last name with a delimiter, matching the
composite-key strategy from section 8. A production implementation must
choose a delimiter that cannot appear inside either field value, exactly the
boundary condition called out in section 15's testing guidance.

Java, Rust, C#, and Kotlin are omitted from this entry. The pattern is a data
modeling and access strategy rather than a language-idiomatic construct, so
the three examples above (a full copy, a pointer-only lookup, and a
composite-key lookup) already cover the structural variants section 8
describes. Adding the same logic again in four more languages would not
demonstrate anything the first three do not.
