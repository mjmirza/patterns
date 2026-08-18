# Family 12. Data and Storage

Origin. Kleppmann

29 entries, 223,926 words. Every entry carries all 18
dimensions from [the entry contract](../../docs/ENTRY-TEMPLATE.md).

## Data Processing

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Lambda Architecture](lambda-architecture.md) | contested | 6,135 | A team needs to answer a query over an ever-growing data set, and the query must be both correct over the full history and current within seconds of the latest event, and no ... |

## Data Structure

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [B-Tree](b-tree.md) | canonical | 7,351 | A program needs to store an ordered collection of keys that is too large to fit in memory, and it needs to look up, insert, delete, and range-scan those keys with a small ... |
| [Merkle Tree](merkle-tree.md) | canonical | 9,547 | A system holds a large, changing collection of data, and two parties, or two replicas of the same system, need to agree that their copies of the collection are identical, or a ... |

## Data and Storage

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Bloom Filter](bloom-filter.md) | canonical | 8,876 | A system needs to answer one question over and over, at high volume, with low latency. |
| [CRDT](crdt.md) | established | 6,106 | A system replicates the same logical data across more than one node, and more than one node accepts writes without first coordinating with the others. |
| [Change Data Capture](change-data-capture.md) | established | 6,609 | A service owns a database that other services, warehouses, caches, and search indexes need to stay synchronized with. |
| [Consistent Hashing](consistent-hashing.md) | canonical | 7,705 | A system needs to map a large, high-churn set of keys, cache entries, shard identifiers, session identifiers, onto a smaller, changing set of nodes, caches, database shards, load ... |
| [Data Mesh](data-mesh.md) | established | 7,417 | A large organization with more than a handful of independent product or business domains eventually runs a central data team whose job is to ingest data from every domain's ... |
| [Data Vault](data-vault.md) | established | 8,114 | An enterprise data warehouse ingests data from many source systems, an ERP, a CRM, a billing platform, several SaaS tools connected through an API, and often at least one legacy ... |
| [ELT](elt.md) | established | 7,149 | A team needs data from several operational systems, a payments database, a support ticket system, a marketing platform's API, a stream of application events, made available for ... |
| [ETL](etl.md) | canonical | 7,257 | An organization has data that lives in one shape, in one place, produced for one purpose, and it needs that data in a different shape, in a different place, usable for a different ... |
| [Gossip Protocol](gossip-protocol.md) | canonical | 9,789 | A set of processes, potentially numbering in the hundreds or thousands, needs to keep a piece of shared state consistent, or needs to agree on who is currently alive, without a ... |
| [Kappa Architecture](kappa-architecture.md) | established | 6,510 | A team running analytics or derived views over an event stream commonly starts with a batch pipeline. |
| [LSM Tree](lsm-tree.md) | canonical | 9,064 | A key-value or wide-column store needs to sustain a high rate of writes, including writes that touch keys scattered across the entire key space, while still answering point ... |
| [Lamport Clock](lamport-clock.md) | canonical | 6,460 | A distributed system has no shared memory and no shared clock. |
| [Leaderless Replication](leaderless-replication.md) | canonical | 7,925 | A single-leader replicated database routes every write through one node. |
| [Medallion Architecture](medallion-architecture.md) | established | 7,094 | A data platform ingests information from many upstream systems. |
| [Multi-Leader Replication](multi-leader-replication.md) | established | 7,906 | A team runs a database that serves write traffic from more than one geographic region, or from more than one autonomous system that must keep working during a network partition ... |
| [Quorum](quorum.md) | canonical | 7,448 | A system replicates the same piece of data onto several nodes so that the loss of any one node, or the temporary unavailability of any one node, does not lose data or stop the ... |
| [Slowly Changing Dimensions](slowly-changing-dimensions.md) | canonical | 7,732 | A dimensional data warehouse separates numeric, frequently-recorded facts (an order line, a sensor reading, a page view) from the descriptive dimensions those facts are analyzed ... |
| [Snowflake Schema](snowflake-schema.md) | canonical | 7,419 | A team building a data warehouse or a semantic model for business intelligence needs to answer analytical questions fast, total revenue by region and month, units sold by product ... |
| [Star Schema](star-schema.md) | canonical | 7,771 | An organization accumulates a large volume of business events, orders, shipments, page views, sensor readings, trades. |
| [Three-Phase Commit](three-phase-commit.md) | established | 8,714 | A coordinator has already run the first two rounds of the classical Two-Phase Commit protocol. |
| [Vector Clock](vector-clock.md) | canonical | 8,622 | A distributed system has no single authoritative clock. |
| [Write-Ahead Log](write-ahead-log.md) | canonical | 8,777 | A database, or any system that mutates state on disk, has two competing needs that are difficult to satisfy with the same physical write. |

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
