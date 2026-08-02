---
name: Sharding
slug: sharding
family: 08-cloud-distributed
category: Data Distribution
aliases: [Horizontal Partitioning, Data Partitioning, Database Sharding]
first_described: "Google 2006 (Bigtable), popularized as a web-scale term by MySQL and Flickr operators mid-2000s"
maturity: canonical
related: [consistent-hashing, leader-election, cqrs, event-sourcing, saga]
incompatible_with: [two-phase-commit-as-primary-consistency-model]
verified: 2026-08-02
---

# Sharding

## 1. Name, aliases, and lineage

The canonical name in this catalog is Sharding. The term is also called
Horizontal Partitioning, most often in relational database vendor
documentation, and Data Partitioning, in distributed systems literature that
wants to keep the word neutral between horizontal and vertical splits. This
entry uses Sharding for the specific technique of splitting one logical
dataset into many independently stored pieces, keyed by some function of the
data, and routed to different physical nodes.

The word shard predates its database usage by decades in ordinary English, a
fragment of something broken. Its application to databases is usually traced
to the MMO games industry, where a game world was split into parallel copies
called shards running on separate server clusters so tens of thousands of
players did not collide on one machine, and separately to Google's internal
infrastructure for Bigtable, where the paper describes splitting a table into
tablets, the mechanism that later databases would generalize into what the
industry now calls a shard (Fay Chang et al., "Bigtable. A Distributed Storage
System for Structured Data", OSDI 2006, section 2,
[static.googleusercontent.com PDF](https://static.googleusercontent.com/media/research.google.com/en//archive/bigtable-osdi06.pdf),
verified 2026-08-02). The paper itself never uses the word shard, it uses
tablet, but the concept, a contiguous key range served by exactly one node at
a time and automatically split when it grows too large, is the same idea the
rest of the industry converged on and later named shard.

The web-scale usage of the word shard as a verb and a noun for relational
database partitioning is generally attributed to engineers at companies
running MySQL past its single-server limits in the mid-2000s, notably Flickr's
public writeups on horizontally partitioning photo metadata across many MySQL
instances (Cal Henderson, O'Reilly Media, 2006, the chapter on architecture
for large sites, discusses splitting a large table across many federated
database servers using an explicit shard identifier embedded in the primary
key). This
entry treats the pattern as canonical rather than merely established because
it now appears as a first class, named feature in essentially every
horizontally scaling data store shipped since 2010, both relational (Vitess,
Citus, CockroachDB, Spanner) and non relational (MongoDB, Cassandra,
DynamoDB, Elasticsearch).

## 2. Problem and context

A single database server has a hard limit on what it can do. It has a fixed number of CPU cores, a
fixed amount of RAM for its buffer pool or page cache, a fixed number of disk
IOPS, and a fixed amount of network bandwidth on its host. Vertical scaling,
buying a bigger machine, pushes that limit up but never removes it, and past
a certain point the price of the next tier of hardware grows faster than the
capacity it delivers. A write-heavy table that has grown past what one
machine's disk can serve, or a read-heavy table whose working set no longer
fits in RAM so every query pays a disk seek, both hit the same wall. The team
needs more capacity than one machine, of any size that can be bought or
rented, can provide.

Replication alone does not solve this for writes. A read replica adds read
capacity by copying the whole dataset to more machines, but every write still
has to land on the one primary, so a write-bound table gets no relief from
adding replicas. The context in which sharding becomes the right tool is
specifically a write-bound or storage-bound dataset, or a read-bound dataset
whose working set is bigger than any single machine's cache, where the data
itself, and not only the read traffic, needs to be split across independent
machines so that each machine is responsible for a fraction of the whole.

Sharding is the answer to a dataset that is now bigger than a fair machine
can hold or serve, and it is a different problem from traffic to a small
dataset being bigger than one machine can serve, which is closer to the
load-balancing and caching family of patterns.

## 3. Forces

Sharding is one of the more expensive patterns in this catalog to introduce,
because unlike adding a cache in front of a service, it changes what queries
are legal. The forces below are the reasons the industry still reaches for it
despite that cost.

**Write throughput versus operational simplicity.** A single primary has one
write path and therefore one place to reason about consistency, backups, and
schema migrations. Splitting into N shards multiplies write throughput
roughly N times in the ideal case, but multiplies the operational surface by
the same factor, N schemas to migrate in lockstep, N backup jobs, N failure
domains to monitor.

**Query flexibility versus routing cost.** An unsharded database lets any
query touch any row with a join, an aggregate, or a full scan. Once data is
sharded, a query that needs rows from more than one shard has to be executed
as a scatter-gather across shards and merged by the application or a query
router, which is slower and harder to reason about than a single-node join.
The pattern favors queries that are naturally scoped to one shard key, for
example "all orders for this customer", and disfavors global aggregates, for
example "total revenue across all customers this hour", unless a separate
denormalized or analytical path is built for that.

**Even distribution versus data locality.** The shard key determines both how
evenly load spreads across shards and whether related rows end up on the same
shard so a query can be answered without a cross-shard join. These two goals
are frequently in tension. A key that distributes perfectly evenly, like a
random UUID, destroys locality, every range query becomes a full scatter.
A key that preserves locality, like a customer id used unchanged, can create
severe skew if a handful of customers account for most of the workload. This
tension is the single most consequential design decision in the whole
pattern and is covered in depth in dimension 11.

**Rebalancing cost versus growth headroom.** Every sharding scheme has to
answer what happens when the number of shards changes, whether up because the
dataset grew, or down because it shrank. A poorly chosen scheme makes adding
a shard mean physically moving a large fraction of the existing data, an
expensive, risky, and slow operation performed while the system is live. A
well chosen scheme, generally consistent hashing or a directory that can be
edited in place, bounds the fraction of data that has to move.

**Cost per node versus latency.** More, smaller shards mean each individual
shard holds less data and can respond faster to a query that touches only
that shard, and gives finer-grained failure isolation, one shard's outage
affects a smaller fraction of users. But more shards means more per-node fixed
overhead, connection pools, monitoring agents, replication lag to track, and
a higher chance that a broad query touches many shards at once, paying the
scatter-gather cost on every request instead of only the rare cross-shard
query.

## 4. Applicability and non-applicability

Reach for sharding when the following hold.

- The dataset's total size, or its write rate, has already exceeded what the
  best single machine you are willing to operate or pay for can sustain, not
  merely might exceed it someday. Sharding pays for itself only once the
  limit is real.
- The vast majority of queries are naturally scoped to a single identifiable
  key, for example a tenant id, a user id, or a device id, so that scoping a
  query to one shard is the normal case rather than the exception.
- The team can tolerate, or has already built, denormalized or asynchronous
  paths for the minority of queries that genuinely need to aggregate across
  the whole dataset, rather than requiring every query to remain a live,
  synchronous cross-shard join.
- Read replicas and vertical scaling of the single primary have already been
  tried, or have been ruled out for a documented reason, a write-bound
  workload, or a dataset larger than any affordable single-node disk, so
  sharding is not being reached for as the first option tried.

Do NOT reach for sharding in these cases, and the reason matters more than
the rule.

- The actual bottleneck is read traffic against a working set that fits
  comfortably in RAM. A read replica, a cache, or a materialized view solves
  this at a fraction of the operational cost, and none of them change what
  queries are legal.
- The dataset's growth is speculative rather than measured. Sharding
  irreversibly complicates every query, every migration, and every backup
  from day one, and undoing a sharding decision, unsharding, is close to a
  full data migration in its own right. Premature sharding is a recognized
  and expensive mistake.
- Strong, cross-entity transactional consistency is a hard requirement and
  the team has neither the budget nor the appetite to build or adopt a
  distributed transaction layer, a two-phase commit coordinator, a saga, or a
  vendor-provided distributed SQL engine. A single well-tuned primary with
  ACID transactions is dramatically simpler and, up to its capacity limit,
  strictly more capable for this use case.
- The team cannot yet answer, in one sentence, what the shard key is and why
  more than 80 percent of production queries will be scoped to it. Sharding
  without a settled shard key produces a system where every query becomes a
  scatter-gather, which is frequently slower than the unsharded system it
  replaced.
- A managed, auto-scaling, serverless data store already provides the needed
  throughput with automatic partitioning hidden behind its API, for example a
  document database's own internal partitioning, or an object store.
  Building an application-level sharding layer on top of a store that already
  shards internally is usually redundant effort solving a problem the vendor
  already solved.

## 5. Structure

- **Shard.** One independently stored subset of the overall dataset, holding
  a disjoint slice of the key space. A shard is usually itself a fully
  functioning, independently backed up database instance, not merely a table
  partition on shared hardware, though the two are sometimes conflated in
  casual usage.
- **Shard key**, also called partition key or distribution key. The
  attribute, or function of one or more attributes, of each row or document
  that determines which shard it belongs to. The single most consequential
  design choice in the pattern.
- **Sharding function or scheme.** The deterministic mapping from a shard key
  value to a shard identifier. The three schemes in production use are
  covered in depth in dimension 8, hash-based, range-based, and
  directory-based, also called lookup-based.
- **Router**, also called proxy or query coordinator. The component, whether
  a standalone process, a client-side library, or logic embedded in the
  application, that consults the sharding function or a directory service to
  determine which shard or shards a given query must be sent to, and that
  merges results when a query has to touch more than one shard.
- **Shard map or directory service.** In directory-based and many
  hash-based-with-rebalancing schemes, an authoritative, small, and
  frequently cached record of which shard currently owns which key range or
  hash bucket. This is itself a piece of state that needs its own
  availability and consistency story, because if the shard map is wrong,
  every query is misrouted.
- **Rebalancer**, also called resharding job. The offline or online process
  that moves data between shards when the number of shards changes, updating
  the shard map as it goes, and that must do so without losing writes that
  land during the move.

## 6. ASCII structure diagram

```
                         +-------------------+
        client query --> |      Router        |
                         |  (consults shard   |
                         |   map / hash fn)    |
                         +---------+----------+
                                   |
                +------------------+------------------+
                |                  |                   |
                v                  v                   v
        +---------------+  +---------------+  +---------------+
        |    Shard 0    |  |    Shard 1    |  |    Shard 2    |
        | keys [A - H]  |  | keys [I - P]  |  | keys [Q - Z]  |
        |  (own disk,   |  |  (own disk,   |  |  (own disk,   |
        |  own replicas)|  |  own replicas)|  |  own replicas)|
        +---------------+  +---------------+  +---------------+

                         +-------------------+
                         |    Shard Map /    |
                         | Directory Service |
                         |  0 -> host-a:5432 |
                         |  1 -> host-b:5432 |
                         |  2 -> host-c:5432 |
                         +-------------------+
                          (router reads this
                           to resolve shard id
                           to a physical host)
```

## 7. Dynamics

```
Single-shard query, the common case, must make up most of the traffic

  Client        Router            Shard Map          Shard 1
    |  query      |                   |                 |
    | key=42 ---> |                   |                 |
    |             | resolve(42) ----> |                 |
    |             | <-- shard=1 ------|                 |
    |             |------------------------------------>|
    |             |                   query executed here
    |             |<------------------------------------|
    | <-- result -|                   |                 |


Cross-shard scatter-gather, the expensive, minority case

  Client        Router          Shard 0   Shard 1   Shard 2
    | aggregate    |               |         |         |
    | query -----> |               |         |         |
    |              |-- partial --->|         |         |
    |              |-- partial -------------->|         |
    |              |-- partial ----------------------->|
    |              |<-- rows ------|         |         |
    |              |<-- rows -----------------|         |
    |              |<-- rows ----------------------------|
    |              | merge/aggregate locally  |         |
    | <-- result --|               |         |         |


Resharding, moving a range from Shard 0 to a new Shard 3, hash scheme

  Rebalancer          Shard 0            Shard 3 (new)      Shard Map
      |  start copy      |                    |                |
      |----------------->| stream matching    |                |
      |                  | rows ------------->|                |
      |                  |                    |                |
      |  dual-write window, writes to the moving range land on
      |  BOTH Shard 0 and Shard 3 until the map cuts over
      |                  |                    |                |
      |  verify counts match, catch up lag    |                |
      |----------------------------------------------------->  |
      |  atomically flip map entry, range now points to Shard 3 |
      |------------------------------------------------------->|
      |  stop dual-write, delete range from Shard 0, delayed    |
```

## 8. Implementation variants

**Hash-based sharding.** The shard identifier is computed by hashing the
shard key with a deterministic hash function and mapping the hash output to
one of N shards, commonly `hash(key) mod N` in the naive form or, far more
commonly in production, consistent hashing or a hash ring, where the hash
space is divided into a large fixed number of virtual buckets that are then
assigned to physical shards, and rebalancing only moves the buckets that
change owner rather than rehashing every key. MongoDB implements this as
hashed sharding, where the shard key value is passed through an MD5-derived
hash before being placed into a chunk range, explicitly to spread
monotonically increasing keys, timestamps and auto-increment ids, evenly
across shards rather than concentrating all new inserts on one shard
(MongoDB Manual, "Shard Keys", the Hashed Shard Keys section of the Sharding
reference, [www.mongodb.com/docs/manual/core/sharding-shard-key](https://www.mongodb.com/docs/manual/core/sharding-shard-key/),
verified 2026-08-02). The resharding cost of naive `mod N` hashing is severe,
changing N from say 4 to 5 shards invalidates the mapping for nearly every
key, forcing almost the entire dataset to move. Consistent hashing bounds
this to roughly `1/N` of the data moving per shard added or removed, which is
the reason production hash-sharded systems use a hash ring or an equivalent
virtual-bucket indirection rather than raw modulo arithmetic.

**Range-based sharding.** The shard key space is divided into contiguous
ranges, and each shard owns one range, for example customer ids 1 through
1,000,000 on shard 0, and 1,000,001 through 2,000,000 on shard 1. MongoDB's
ranged sharding is the direct implementation of this idea, and its
documentation is explicit that this scheme keeps documents with nearby shard
key values physically close, which makes range queries fast, but that if
many documents share the same or very close shard key values, the resulting
chunk becomes a jumbo chunk that MongoDB cannot split further, concentrating
load on one shard (MongoDB Manual, "Shard Keys", the Ranged Shard Keys and
Jumbo Chunks sections of the Sharding reference, same URL as above, verified
2026-08-02). The resharding cost of range-based sharding is comparatively
gentle for growth, adding a shard usually means splitting one existing range
into two and moving only the split-off portion, but it is uniquely
vulnerable to sequential write hotspotting, described in dimension 11,
because a monotonically increasing key like a timestamp or an
auto-increment integer sends every new write to whichever shard currently
owns the tail of the key space.

**Directory-based sharding**, also called lookup-based sharding. An explicit
table, the shard map or directory, records which shard owns which key, or
which range or hash bucket owns which key, and every routing decision is a
lookup against that table rather than a pure computation. This is close to
the scheme widely reported for Instagram's move away from a single Postgres
primary, generating ids that embed a logical shard number, where many
logical shards are then mapped, many-to-one, onto a smaller number of
physical Postgres servers via a lookup table, so that rebalancing means
moving logical shards between physical servers and updating the lookup
table, never touching the ids or the application-visible sharding scheme
itself. This entry marks the Instagram detail as widely reported rather than
independently verified here, because the original engineering post could not
be reached during this verification pass. Vitess formalizes the generalized
approach with its Vindex abstraction, where the Primary Vindex a table
declares determines how its keyspace id, and therefore its physical shard,
is computed, and the choice of Vindex is what determines whether the
effective scheme behaves as hash-based or range-based underneath, while
resharding is handled by a dedicated workflow that keeps existing shards
serving live read and write traffic throughout the migration, with only a
few seconds of read-only downtime during the final cutover (Vitess project
documentation, Sharding reference page, [vitess.io/docs/22.0/reference/features/sharding](https://vitess.io/docs/22.0/reference/features/sharding/),
verified 2026-08-02). The cost of directory-based sharding is the directory
itself, it is now a piece of critical shared state that must be highly
available and low-latency to consult on every single query, and it is
usually cached aggressively at the router with a short TTL or an
invalidation channel to avoid becoming the new bottleneck.

**Composite and derived-key schemes.** Many production systems use a shard
key that is not a raw column but a composite or derived value chosen
specifically to balance locality against skew, for example Discord's
partitioning of chat messages by a channel id and a time bucket in
Cassandra and later ScyllaDB, which keeps all of one channel's recent
messages together for fast reads of the most recent messages in that
channel, while the time bucket component prevents an old, still-active
channel's partition from growing without bound (Discord Engineering, "How
Discord Stores Trillions of Messages", [discord.com/blog/how-discord-stores-trillions-of-messages](https://discord.com/blog/how-discord-stores-trillions-of-messages),
verified 2026-08-02).

**Postgres-native declarative partitioning combined with foreign data
wrappers or Citus.** PostgreSQL's own built-in hash and range partitioning
implement these two schemes at the single-node table level, and Citus, a
PostgreSQL extension, applies the same hash-based philosophy across a
distributed cluster of physical nodes rather than partitions on one disk.
Citus requires the application to nominate one column per table as the
distribution column, and a row is stored in a shard if the hash of the value
in the distribution column falls within the shard's hash range, with shards
sharing the same hash range always co-located on the same physical node so
that rows related by that column can still be joined without a network hop,
even after a rebalance operation moves shards between nodes (Citus Data
documentation, "How Citus Shards Data", [docs.citusdata.com/en/stable/sharding/data_modeling.html](https://docs.citusdata.com/en/stable/sharding/data_modeling.html),
verified 2026-08-02).

## 9. Known production uses

1. **Vitess**, the horizontal scaling layer for MySQL originally built at
   YouTube and now a CNCF graduated project, implements sharding as a first
   class, named feature with a pluggable Vindex system for choosing the
   sharding scheme per table and a live resharding workflow, documented in
   Vitess's own Sharding reference page
   ([vitess.io/docs/22.0/reference/features/sharding](https://vitess.io/docs/22.0/reference/features/sharding/),
   verified 2026-08-02).
2. **MongoDB**, which builds hashed and ranged sharding into the database
   engine itself as a core, documented configuration option on the shard
   collection command, choosing between the two shapes described in
   dimension 8, along with the platform's own guidance on avoiding jumbo
   chunks and hot shards (MongoDB Manual, "Shard Keys", [www.mongodb.com/docs/manual/core/sharding-shard-key](https://www.mongodb.com/docs/manual/core/sharding-shard-key/),
   verified 2026-08-02).
3. **Citus**, an open source PostgreSQL extension owned by Microsoft and the
   engine behind Azure Cosmos DB for PostgreSQL, implements hash-based
   sharding of standard PostgreSQL tables across a cluster of physical
   nodes, with a distribution column chosen per table (Citus Data
   documentation, "How Citus Shards Data", [docs.citusdata.com/en/stable/sharding/data_modeling.html](https://docs.citusdata.com/en/stable/sharding/data_modeling.html),
   verified 2026-08-02).
4. **Discord** shards its message-storage tier in Cassandra and later
   ScyllaDB by a composite channel-id-plus-time-bucket key, and its own
   engineering blog documents this scheme by name along with the hot
   partition failure mode it produces under celebrity-scale traffic and the
   request-coalescing and consistent-hash-routing mitigations built to
   compensate for it ([discord.com/blog/how-discord-stores-trillions-of-messages](https://discord.com/blog/how-discord-stores-trillions-of-messages),
   verified 2026-08-02).

## 10. Consequences

**Positive.**

- Write throughput and total storage capacity scale roughly linearly with
  the number of shards, for workloads whose queries are well scoped to the
  shard key, removing the single-machine limit entirely rather than merely
  pushing it back.
- Failure is isolated to a fraction of the dataset. One shard going down, or
  one shard's disk filling up, affects only the rows that live on that
  shard, rather than the entire dataset, which materially improves both
  blast radius and mean time to recover for the unaffected majority of
  traffic.
- Each shard is small enough that its indexes, its working set, and its
  vacuum or compaction cycles fit comfortably within the resources of one
  affordable machine, which keeps per-shard operational behavior, backup
  time, restore time, query planning, predictable even as the overall system
  grows arbitrarily large.

**Negative.**

- Every query that cannot be scoped to a single shard key becomes a
  scatter-gather across some or all shards, which is slower, harder to
  reason about, and loses the atomicity guarantees a single-node query had
  for free. A join, a global unique constraint, or a global count that was
  trivial before sharding becomes an application-level engineering problem
  after it.
- Rebalancing is a live, risky, data-moving operation that the team now
  owns permanently, for the life of the system, every time capacity needs
  change. The cost and risk of this operation is directly determined by the
  sharding scheme chosen, as detailed in dimension 8.
- Schema migrations, backups, and any cross-cutting operational task now
  have to be run, and reasoned about, N times instead of once, and a
  migration that succeeds on 39 of 40 shards and fails on the 40th leaves
  the dataset in a partially migrated state that did not exist before
  sharding.
- The shard key becomes effectively permanent. Changing it later requires
  re-deriving it for every existing row and, in most schemes, physically
  moving most of the data, which is close in cost and risk to standing the
  system up from scratch. A wrong shard key chosen early is one of the most
  expensive mistakes to correct in this catalog.

## 11. Failure modes and misuse

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 1 | One shard's CPU, IOPS, or connection count is consistently and dramatically higher than its siblings, while the others sit idle | Hot-shard skew. The shard key has low distinct-value count relative to load, or a small number of key values, a viral post, a large enterprise tenant, a celebrity account, account for most of the traffic, so hash or range placement puts all of that traffic on one physical node | Split the hot key's data further with a composite key that adds a secondary dimension, Discord's channel-plus-time-bucket approach is the canonical example, or special-case the outlier key onto its own dedicated shard, or add a caching or request-coalescing layer in front of the shard so repeated reads for the same hot key do not all hit the database |
| 2 | Insert latency climbs steadily and only the newest, highest-numbered shard is under load while older shards are nearly idle | Sequential-key hotspotting under a range-based scheme. A monotonically increasing shard key, an auto-increment id, a timestamp, always sorts to the tail of the key space, so every new write lands on whichever shard currently owns the top of the range | Switch to a hash-based or hashed-prefix scheme for the shard key so new writes distribute uniformly, or explicitly reverse or shuffle a component of the key before using it as the range key, a common technique is prefixing with a hash of the id |
| 3 | A single logical row or chunk in the sharded store refuses to split further and keeps absorbing an increasing share of a shard's storage and load | Jumbo chunk, MongoDB's own term, or an unsplittable range, caused by many documents or rows sharing an identical or near-identical shard key value, so range-based splitting has nowhere left to cut | Choose a higher-distinct-value count shard key, or add a secondary component to the key that discriminates within the offending value, a suffix hash, a sub-bucket id, before the chunk grows large enough to become unsplittable |
| 4 | Application code has queries with a join, a global count, or a cross-tenant report that used to run in milliseconds and now times out, hangs, or is disabled entirely after a sharding migration | The query was never scoped to the shard key and the team sharded a table without first auditing every existing query pattern against the proposed shard key, so a query that should have driven the shard key selection now cannot be efficiently answered at all | Add a purpose-built asynchronous aggregation path, a nightly batch job, a change-data-capture pipeline into a data warehouse, a materialized view maintained by an event stream, for the specific cross-shard queries that remain, rather than trying to force the OLTP router to serve them synchronously |
| 5 | A rebalancing or resharding job appears to complete, but some writes made during the migration window are missing on the destination shard, or exist on both source and destination with conflicting values | The dual-write or copy-then-cutover window was implemented without correctly ordering the start-dual-write, backfill-existing-data, and cut-over-reads steps, so writes that land in the gap between backfill completion and read cutover are lost or duplicated | Use a proven resharding tool that guarantees this ordering, Vitess's Reshard workflow with VDiff verification, or an equivalent vendor tool, rather than hand-rolling the copy-and-cutover sequence, and always run a row-count and checksum diff between source and destination before deleting the source data |
| 6 | The shard map or directory service becomes unavailable, and every query in the system fails simultaneously, even though every individual data shard is healthy | The directory-based scheme's shard map was built as a single point of failure, either an unreplicated database or a service with no local caching at the router, so it inherited none of the fault isolation the sharding scheme was meant to provide | Cache the shard map aggressively at every router with a bounded staleness window and a fallback behavior for a stale entry, retry against the last-known shard, then invalidate, and run the shard map itself as a small, separately and highly replicated store, never as a single unsharded database that the whole system depends on |

## 12. Trade-off matrix

| Concern | Sharding | Read replication only | Vertical scaling, bigger machine | A managed serverless data store with built-in partitioning |
|---|---|---|---|---|
| Write throughput limit | Scales roughly linearly with shard count | No improvement, all writes still hit one primary | Improves, bounded by the largest machine the vendor sells | Scales automatically, but throughput is throttled per the vendor's provisioned or on-demand capacity model |
| Cross-entity transactions | Hard, needs a distributed transaction pattern, Saga or two-phase commit, or application-level compensation | Fully available on the primary, unaffected | Fully available, this is the whole appeal of staying on one node | Usually limited to a single partition or a vendor-specific transaction scope, similar constraint to sharding |
| Operational surface | Highest, N databases to patch, back up, and monitor | Low, one primary plus read-only followers | Lowest, one machine to operate | Lowest for the team, but hands control of failure modes to the vendor |
| Rebalancing cost when capacity needs change | Real and ongoing, magnitude depends entirely on scheme choice, dimension 8 | Not applicable, replicas can be added or removed independently of data placement | Requires a maintenance window to migrate to bigger hardware, a one-time event | Handled by the vendor, invisible to the operator, but also outside the operator's control if it misbehaves |
| Global query and reporting simplicity | Requires a separate async or analytical path for anything not scoped to the shard key | Simple, one node has the whole dataset | Simple, one node has the whole dataset | Varies by vendor, frequently as constrained as sharding |

## 13. Related and incompatible patterns

Sharding composes tightly with **Consistent Hashing**, which is the standard
technique used to implement the hash-based scheme from dimension 8 in a way
that bounds rebalancing cost, and the two are frequently conflated in
casual conversation even though consistent hashing is the general-purpose
mechanism and sharding is the specific application of it to data placement.

Sharding is a natural companion to **CQRS** and **Event Sourcing**, because
the cross-shard query problem described in dimension 10 is most cleanly
solved by maintaining a separate, denormalized read model built from an
event stream that already crosses shard boundaries, rather than trying to
force the sharded write-side store to answer aggregate queries directly.

Sharding frequently needs the **Saga** pattern, or an equivalent
compensating-transaction mechanism, the moment a business operation needs to
touch rows on two different shards atomically, because the pattern
deliberately gives up the ability to run a single ACID transaction across
shard boundaries in exchange for horizontal scale.

Sharding is directly downstream of a good **Leader Election** implementation
inside each individual shard, since most production sharded systems still
run each shard as a small replicated cluster with one leader for writes, so
the sharding layer sits on top of, not instead of, per-shard high
availability.

Sharding is largely incompatible as a primary consistency model with an
architecture whose correctness depends on synchronous, cluster-wide
two-phase commit for every write, because the coordination overhead of
two-phase commit across an ever-growing number of shards tends to erode
most of the throughput gain sharding was introduced to capture, which is why
production systems that need both horizontal scale and strong cross-shard
transactions, Spanner, CockroachDB, invest heavily in specialized consensus
and clock infrastructure rather than layering naive two-phase commit on top
of an otherwise ordinary sharded relational database.

## 14. Refactoring path in and out

**Introducing sharding into an unsharded system.**

1. Instrument the existing single-node database to find the true bottleneck.
   Confirm with real metrics that the binding limit is write throughput or total
   storage, not read traffic or cache misses, before doing anything
   irreversible, see dimension 4's non-applicability list.
2. Audit the production query log for the actual shape of queries in use,
   and propose a shard key candidate that the audit shows the large majority
   of queries are already scoped to.
3. Introduce the shard key as an explicit, indexed column on the existing
   single-node schema first, and rewrite the application's data access layer
   to always include it in queries, while the data still lives on one node.
   This step alone frequently surfaces every place a query was not scoped to
   the intended key, before any data has moved, which is far cheaper to fix
   than discovering it mid-migration.
4. Stand up the target shard topology and perform an online backfill copy
   using change-data-capture or a vendor resharding tool, keeping the
   original single node as the source of truth throughout.
5. Dual-write the newly identified shard key's writes to both the old
   single-node system and the new sharded topology, verify row counts and
   checksums match, then flip reads over shard by shard, keeping the old
   system as a rollback path until confidence is high.
6. Decommission the old single-node primary only after a full production
   cycle, including batch jobs, backups, and reporting, has run cleanly
   against the sharded topology.

**Removing sharding, unsharding, when the dataset has shrunk or the
operational cost has exceeded the benefit.**

1. Confirm the aggregate dataset now comfortably fits, with headroom, on a
   single machine of a size the team is willing to operate, including its
   growth projection for the next planning period, not only its current
   size.
2. Reverse the dual-write pattern from step 5 above, writing every shard's
   changes into a single consolidated target database while all shards
   remain the read source of truth.
3. Verify the consolidated target against every shard with a full checksum
   pass, then cut reads over to the single consolidated database.
4. Decommission the shards and the router or shard map only after the
   consolidated database has served production traffic cleanly through a
   full operational cycle.

## 15. Testing and verification

Unit and integration tests for the sharding function itself are
straightforward and cheap. Given a fixed set of shard key inputs and a fixed
shard count, assert the mapping is deterministic, the same key always
resolves to the same shard, and, for hash-based schemes, assert the
distribution is close to uniform across a large, representative sample of
real or realistic key values, which is exactly the property the code example
in dimension 8's TypeScript sample below verifies directly.

What becomes genuinely harder to test is the router's cross-shard behavior
under partial failure. A scatter-gather query where one of three shards is
slow or unavailable needs an explicit test that asserts the router's timeout
and partial-result behavior, rather than assuming happy-path behavior
generalizes.

Resharding logic deserves its own dedicated test suite that specifically
exercises the failure modes in dimension 11's row 5. A fake clock and a
fault-injecting test double for the destination shard should be used to
simulate a write landing exactly during the backfill-to-cutover gap, and the
test should assert that write is neither lost nor duplicated once the
migration completes, since this exact window is where real production
resharding bugs concentrate.

Load testing before a shard key goes live in production is close to
mandatory. Replaying a realistic, tenant-weighted sample of production
traffic against a proposed shard key and shard count, and measuring the
resulting per-shard request rate, is the only reliable way to catch the
skew failure modes in dimension 11 before they reach production, because
synthetic uniform-random test data systematically hides exactly the skew
that real-world data, celebrity accounts, large enterprise tenants,
sequential ids, exhibits.

## 16. Observability signals

A healthy sharded system shows near-uniform per-shard metrics for CPU,
connection count, query latency percentiles, and storage growth rate, with
the spread between the busiest and quietest shard staying within a small,
stable band over time. The single most important dashboard for a sharded
system is a per-shard breakdown of these metrics side by side, not only an
aggregate across all shards, because an aggregate can look perfectly healthy
while one shard is quietly saturated and its siblings are nearly idle,
exactly the hot-shard failure mode in dimension 11's first row.

Track the rate and latency of scatter-gather, cross-shard, queries
separately from single-shard queries, and alert if the proportion of
scatter-gather traffic climbs unexpectedly, since that is frequently a
leading indicator that application code has started issuing queries the
shard key was not designed to serve.

During any active rebalancing or resharding operation, track replication or
copy lag between source and destination for the range being moved, and treat
that lag crossing a threshold as a signal to pause cutover, never to
proceed on schedule regardless of lag, since proceeding with significant lag
is precisely the condition under which dimension 11's row 5 data-loss
failure mode occurs.

Track the age and error rate of shard-map lookups at the router if using a
directory-based scheme, since a stale or failing shard map produces
misrouted queries that are otherwise invisible until a customer reports
missing or duplicated data.

## 17. Security and privacy implications

Sharding by a tenant or customer identifier, the most common shard key in
multi-tenant SaaS systems, is frequently adopted specifically because it
gives strong physical data isolation as a side effect. One tenant's rows
never share a physical shard, connection pool, or backup file with another
tenant's rows if each tenant is pinned to exactly one shard, which can
materially simplify satisfying a data-residency or single-tenant compliance
requirement compared with a single shared database relying entirely on
row-level access control.

The shard map or directory service itself becomes a sensitive piece of
infrastructure once tenant-to-shard assignment is used this way, because it
now encodes which physical machine, and potentially which geographic region,
each tenant's data lives in, which is itself business-sensitive metadata
that deserves its own access controls separate from the data shards.

Cross-shard scatter-gather queries widen the blast radius of a single
compromised router or query coordinator, since that one component now has
legitimate query access to every shard rather than only one, which is a
consideration that did not exist in the unsharded system and should factor
into the router's own authentication, network segmentation, and audit
logging design.

Backups and access logs multiply by the shard count, and a security or
compliance audit that assumed the database as a singular auditable unit
before sharding now has to explicitly account for every shard, or risk
silently missing coverage on a subset of the data.

## 18. References

1. Fay Chang, Jeffrey Dean, Sanjay Ghemawat, Wilson C. Hsieh, Deborah A.
   Wallach, Mike Burrows, Tushar Chandra, Andrew Fikes, Robert E. Gruber,
   "Bigtable. A Distributed Storage System for Structured Data", OSDI 2006,
   [static.googleusercontent.com/media/research.google.com/en//archive/bigtable-osdi06.pdf](https://static.googleusercontent.com/media/research.google.com/en//archive/bigtable-osdi06.pdf),
   verified 2026-08-02.
2. Cal Henderson, O'Reilly Media, 2006, the chapter on architecture for
   large sites, discusses federating a large MySQL table across many
   database servers using an explicit partition identifier embedded in the
   key, consulted for the origin of web-scale shard terminology. The book
   title itself is omitted from this reference because it contains a word
   this repository's house style bans in prose.
3. MongoDB, Inc., "Shard Keys", the Sharding section of the MongoDB Manual,
   covering ranged, hashed, jumbo chunks, and hot shard guidance,
   [www.mongodb.com/docs/manual/core/sharding-shard-key](https://www.mongodb.com/docs/manual/core/sharding-shard-key/),
   verified 2026-08-02.
4. Vitess project, CNCF, Sharding reference documentation, describing
   Vindexes, hash and range based schemes, and the live resharding
   workflow, [vitess.io/docs/22.0/reference/features/sharding](https://vitess.io/docs/22.0/reference/features/sharding/),
   verified 2026-08-02.
5. Citus Data, Microsoft, "How Citus Shards Data", describing the
   distribution column, hash-based shard assignment, and shard co-location
   across rebalances,
   [docs.citusdata.com/en/stable/sharding/data_modeling.html](https://docs.citusdata.com/en/stable/sharding/data_modeling.html),
   verified 2026-08-02.
6. Discord, "How Discord Stores Trillions of Messages", Discord Engineering
   Blog, describing the channel-id-plus-time-bucket composite shard key,
   hot partitions under celebrity-scale traffic, and the request-coalescing
   and consistent-hash-routing mitigations,
   [discord.com/blog/how-discord-stores-trillions-of-messages](https://discord.com/blog/how-discord-stores-trillions-of-messages),
   verified 2026-08-02.

## Code examples

### TypeScript, consistent-hash-ring router, hash-based scheme

```typescript
import { createHash } from "node:crypto";

function ringHash(input: string): number {
  const digest = createHash("md5").update(input).digest();
  return digest.readUInt32BE(0);
}

class ConsistentHashRing {
  private ring: Array<{ point: number; shard: string }> = [];

  constructor(shards: string[], virtualNodesPerShard = 100) {
    for (const shard of shards) this.addShard(shard, virtualNodesPerShard);
  }

  addShard(shard: string, virtualNodes = 100): void {
    for (let i = 0; i < virtualNodes; i++) {
      this.ring.push({ point: ringHash(`${shard}#${i}`), shard });
    }
    this.ring.sort((a, b) => a.point - b.point);
  }

  removeShard(shard: string): void {
    this.ring = this.ring.filter((entry) => entry.shard !== shard);
  }

  route(key: string): string {
    const point = ringHash(key);
    for (const entry of this.ring) {
      if (entry.point >= point) return entry.shard;
    }
    return this.ring[0].shard;
  }
}

function main(): void {
  const ring = new ConsistentHashRing(["shard-0", "shard-1", "shard-2"]);
  const counts = new Map<string, number>();
  for (let i = 0; i < 10000; i++) {
    const shard = ring.route(`customer-${i}`);
    counts.set(shard, (counts.get(shard) ?? 0) + 1);
  }
  console.log("distribution before adding shard-3:", Object.fromEntries(counts));

  const before = new Map<string, string>();
  for (let i = 0; i < 10000; i++) before.set(`customer-${i}`, ring.route(`customer-${i}`));

  ring.addShard("shard-3");
  let moved = 0;
  for (let i = 0; i < 10000; i++) {
    if (ring.route(`customer-${i}`) !== before.get(`customer-${i}`)) moved++;
  }
  console.log(`keys remapped after adding a 4th shard, ${moved} of 10000, ${(moved / 100).toFixed(1)}%`);
}

main();
```

### Python, range-based shard router with a split-driven reshard

```python
from bisect import bisect_right
from dataclasses import dataclass, field


@dataclass
class RangeShardRouter:
    boundaries: list[int] = field(default_factory=lambda: [1_000_000, 2_000_000])
    shard_names: list[str] = field(
        default_factory=lambda: ["shard-0", "shard-1", "shard-2"]
    )

    def route(self, customer_id: int) -> str:
        index = bisect_right(self.boundaries, customer_id)
        return self.shard_names[index]

    def split(self, shard_to_split: str, split_point: int, new_shard: str) -> None:
        index = self.shard_names.index(shard_to_split)
        self.boundaries.insert(index, split_point)
        self.shard_names.insert(index + 1, new_shard)


def main() -> None:
    router = RangeShardRouter()
    sample_ids = [500_000, 1_500_000, 2_500_000, 999_999, 1_000_001]
    before = {cid: router.route(cid) for cid in sample_ids}
    print("routes before split", before)

    router.split("shard-1", 1_500_000, "shard-3")

    after = {cid: router.route(cid) for cid in sample_ids}
    print("routes after splitting shard-1 at 1,500,000", after)

    moved = [cid for cid in sample_ids if before[cid] != after[cid]]
    print(f"keys that moved, {moved}, only rows above the split point relocate")


if __name__ == "__main__":
    main()
```

### Go, directory-based shard map with hot-key detection

```go
package main

import "fmt"

type ShardMap struct {
	lookup map[string]string
	hits   map[string]int
}

func NewShardMap() *ShardMap {
	return &ShardMap{
		lookup: map[string]string{
			"tenant-acme":    "shard-0",
			"tenant-globex":  "shard-1",
			"tenant-initech": "shard-2",
		},
		hits: map[string]int{},
	}
}

func (m *ShardMap) Route(key string) (string, bool) {
	shard, ok := m.lookup[key]
	if ok {
		m.hits[key]++
	}
	return shard, ok
}

func (m *ShardMap) Reassign(key, newShard string) {
	m.lookup[key] = newShard
}

// HotKeys returns any key whose share of total traffic exceeds thresholdPct.
func (m *ShardMap) HotKeys(thresholdPct float64) []string {
	total := 0
	for _, c := range m.hits {
		total += c
	}
	var hot []string
	for key, c := range m.hits {
		if total > 0 && float64(c)/float64(total)*100 > thresholdPct {
			hot = append(hot, key)
		}
	}
	return hot
}

func main() {
	sm := NewShardMap()
	for i := 0; i < 900; i++ {
		if _, ok := sm.Route("tenant-acme"); !ok {
			panic("expected tenant-acme to resolve")
		}
	}
	for i := 0; i < 60; i++ {
		sm.Route("tenant-globex")
	}
	for i := 0; i < 40; i++ {
		sm.Route("tenant-initech")
	}

	fmt.Println("hot keys above 50 percent of traffic", sm.HotKeys(50))

	sm.Reassign("tenant-acme", "shard-dedicated-acme")
	newShard, _ := sm.Route("tenant-acme")
	fmt.Println("tenant-acme moved to its own dedicated shard", newShard)
}
```

Rust, Java, and Swift are omitted for this entry. The pattern is a data
placement and routing decision, not a language-idiom-shaped construct, and
the three languages above already demonstrate its three implementation
variants, hash-ring, range-boundary, and directory-lookup, without a fourth
language adding a materially different idiom to show.
