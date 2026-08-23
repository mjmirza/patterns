# Family 12. Data and Storage

Origin. Kleppmann

45 entries, 319,824 words. Every entry carries all 18
dimensions from [the entry contract](../../docs/ENTRY-TEMPLATE.md).

## Concurrency Control

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Snapshot Isolation](snapshot-isolation.md) | canonical | 7,871 | A transaction needs to read a consistent view of the database while other transactions are concurrently reading and writing the same rows, and the system needs this without making ... |

## Data Processing

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Lambda Architecture](lambda-architecture.md) | contested | 6,135 | A team needs to answer a query over an ever-growing data set, and the query must be both correct over the full history and current within seconds of the latest event, and no ... |

## Data Structure

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Anti-Entropy](anti-entropy.md) | canonical | 7,728 | A system that replicates data across multiple nodes for availability and durability accepts, sooner or later, that its replicas will not always agree. |
| [B-Tree](b-tree.md) | canonical | 7,351 | A program needs to store an ordered collection of keys that is too large to fit in memory, and it needs to look up, insert, delete, and range-scan those keys with a small ... |
| [Merkle Tree](merkle-tree.md) | canonical | 9,547 | A system holds a large, changing collection of data, and two parties, or two replicas of the same system, need to agree that their copies of the collection are identical, or a ... |

## Data and Storage

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Bloom Filter](bloom-filter.md) | canonical | 8,876 | A system needs to answer one question over and over, at high volume, with low latency. |
| [Byzantine Fault Tolerance](byzantine-fault-tolerance.md) | canonical | 1,762 | A distributed system that assumes a failed node simply stops responding, a crash fault, is defenseless against a node that instead keeps responding but lies, sending one answer to ... |
| [CRDT](crdt.md) | established | 6,106 | A system replicates the same logical data across more than one node, and more than one node accepts writes without first coordinating with the others. |
| [Change Data Capture](change-data-capture.md) | established | 6,609 | A service owns a database that other services, warehouses, caches, and search indexes need to stay synchronized with. |
| [Columnar Storage](columnar-storage.md) | canonical | 7,452 | A database has to put bytes on disk or in memory in some fixed physical order, and that order is a one-time decision with permanent consequences for every query that runs ... |
| [Consistent Hashing](consistent-hashing.md) | canonical | 7,705 | A system needs to map a large, high-churn set of keys, cache entries, shard identifiers, session identifiers, onto a smaller, changing set of nodes, caches, database shards, load ... |
| [Data Mesh](data-mesh.md) | established | 7,417 | A large organization with more than a handful of independent product or business domains eventually runs a central data team whose job is to ingest data from every domain's ... |
| [Data Vault](data-vault.md) | established | 8,114 | An enterprise data warehouse ingests data from many source systems, an ERP, a CRM, a billing platform, several SaaS tools connected through an API, and often at least one legacy ... |
| [Database Federation](database-federation.md) | established | 1,721 | Data that a person or an application needs often lives in more than one system, a transactional database here, an analytical warehouse there, a data lake elsewhere, and copying ... |
| [Denormalization](denormalization.md) | canonical | 1,923 | The normalization article states directly why a fully normalized schema exists in the first place, and denormalization is the deliberate trade against exactly this protection. |
| [Distributed Hash Table](distributed-hash-table.md) | canonical | 1,561 | A centralized lookup directory is a single point of failure and a single scaling bottleneck, every lookup depends on that one directory staying up and staying fast as the number ... |
| [ELT](elt.md) | established | 7,149 | A team needs data from several operational systems, a payments database, a support ticket system, a marketing platform's API, a stream of application events, made available for ... |
| [ETL](etl.md) | canonical | 7,204 | An organization has data that lives in one shape, in one place, produced for one purpose, and it needs that data in a different shape, in a different place, usable for a different ... |
| [Gossip Protocol](gossip-protocol.md) | canonical | 9,783 | A set of processes, potentially numbering in the hundreds or thousands, needs to keep a piece of shared state consistent, or needs to agree on who is currently alive, without a ... |
| [Hinted Handoff](hinted-handoff.md) | canonical | 5,677 | A leaderless, replicated key-value store assigns each key to a fixed set of N nodes, typically the next N nodes clockwise on a consistent-hashing ring. |
| [Kappa Architecture](kappa-architecture.md) | established | 6,510 | A team running analytics or derived views over an event stream commonly starts with a batch pipeline. |
| [LSM Tree](lsm-tree.md) | canonical | 9,064 | A key-value or wide-column store needs to sustain a high rate of writes, including writes that touch keys scattered across the entire key space, while still answering point ... |
| [Lamport Clock](lamport-clock.md) | canonical | 6,460 | A distributed system has no shared memory and no shared clock. |
| [Leaderless Replication](leaderless-replication.md) | canonical | 7,925 | A single-leader replicated database routes every write through one node. |
| [Log Compaction](log-compaction.md) | established | 8,043 | An append-only log is the simplest and most dependable storage primitive a distributed system offers. |
| [Medallion Architecture](medallion-architecture.md) | established | 7,094 | A data platform ingests information from many upstream systems. |
| [Multi-Leader Replication](multi-leader-replication.md) | established | 7,906 | A team runs a database that serves write traffic from more than one geographic region, or from more than one autonomous system that must keep working during a network partition ... |
| [Multiversion Concurrency Control](mvcc.md) | canonical | 7,230 | A database serves many concurrent transactions. |
| [Quorum](quorum.md) | canonical | 7,448 | A system replicates the same piece of data onto several nodes so that the loss of any one node, or the temporary unavailability of any one node, does not lose data or stop the ... |
| [Read Repair](read-repair.md) | canonical | 6,416 | A system with leaderless, quorum-based replication accepts writes on any of several replicas for a key, and a temporarily unreachable replica, a dropped message, or a slow node ... |
| [Read-Through Cache](read-through-cache.md) | canonical | 7,970 | An application reads the same piece of data far more often than the data changes. |
| [Slowly Changing Dimensions](slowly-changing-dimensions.md) | canonical | 7,737 | A dimensional data warehouse separates numeric, frequently-recorded facts (an order line, a sensor reading, a page view) from the descriptive dimensions those facts are analyzed ... |
| [Snowflake Schema](snowflake-schema.md) | canonical | 7,439 | A team building a data warehouse or a semantic model for business intelligence needs to answer analytical questions fast, total revenue by region and month, units sold by product ... |
| [Star Schema](star-schema.md) | canonical | 7,771 | An organization accumulates a large volume of business events, orders, shipments, page views, sensor readings, trades. |
| [Three-Phase Commit](three-phase-commit.md) | established | 8,714 | A coordinator has already run the first two rounds of the classical Two-Phase Commit protocol. |
| [Tombstone](tombstone.md) | canonical | 7,488 | A system holds more than one copy of the same data, and those copies do not all learn about a delete at the same instant. |
| [Two-Phase Locking](two-phase-locking.md) | canonical | 8,153 | Multiple transactions run concurrently against a shared database, each one reading and writing rows that another transaction might also be touching at the same instant. |
| [Vector Clock](vector-clock.md) | canonical | 8,622 | A distributed system has no single authoritative clock. |
| [Write-Ahead Log](write-ahead-log.md) | canonical | 8,777 | A database, or any system that mutates state on disk, has two competing needs that are difficult to satisfy with the same physical write. |
| [Write-Behind Cache](write-behind-cache.md) | canonical | 6,973 | A service holds hot, frequently mutated state in a fast in-memory or in-cluster cache, and every mutation must eventually reach a durable backing store, typically a relational ... |
| [Write-Through Cache](write-through-cache.md) | canonical | 7,964 | A service reads the same records far more often than it writes them, and the backing store, whether a relational database, a document store, or a remote API, is the slowest part ... |

## Distributed Consensus

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Paxos](paxos.md) | canonical | 7,747 | A group of machines needs to agree on one value, and any one of them can crash or become unreachable at any moment, including in the middle of trying to get everyone to agree. |
| [Raft](raft.md) | canonical | 8,114 | A distributed system that holds state a client cares about, a key-value store, a lock service, a piece of cluster metadata, a leader pointer for another system, needs that state ... |

## Distributed Transactions

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Two-Phase Commit](two-phase-commit.md) | canonical | 6,404 | A single database transaction is easy to make atomic because one process holds the log and one process decides. |

## Probabilistic data structure

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [HyperLogLog](hyperloglog.md) | canonical | 8,164 | A system needs to answer "how many distinct X happened" where X might be visitors to a page, IP addresses hitting an API, users who played a song, distinct search queries in a ... |

## Reading order

Entries are independent. Each one names the patterns it composes with and
the patterns it conflicts with in dimension 13, so following those links
gives a better path than reading top to bottom.

Generated by `tools/gen-indexes.py`. Do not edit by hand.
