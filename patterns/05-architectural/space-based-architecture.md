---
name: Space-Based Architecture
slug: space-based-architecture
family: 05-architectural
category: Architectural
aliases: [Cloud Application Architecture, Tuple Space Architecture]
first_described: "Microsoft internal Youkon platform, 1997-1998"
maturity: established
related: [event-driven-architecture, microservices-architecture, serverless-architecture]
incompatible_with: [layered-architecture]
verified: 2026-08-02
---

# Space-Based Architecture

## 1. Name, aliases, and lineage

The canonical name is Space-Based Architecture, abbreviated SBA. According to
the Wikipedia entry on the pattern, it was originally invented and developed
inside Microsoft in 1997 and 1998 under the internal name Youkon Distributed
Caching platform, aimed at making the MSN Live Search property scale
([Wikipedia, Space-based architecture](https://en.wikipedia.org/wiki/Space-based_architecture),
verified 2026-08-02). The same article states an early production deployment
served MSN Live Search in September 1999 and an MSN customer marketing data
store, and that the pattern later saw adoption in the securities trading
industry for scalable electronic trading systems.

The pattern's data model traces to an older idea. David Gelernter and
Nicholas Carriero at Yale University introduced the tuple space as the
theoretical foundation of the coordination language Linda, published as
Gelernter, "Generative communication in Linda," ACM Transactions on
Programming Languages and Systems, 1985
([Wikipedia, Tuple space](https://en.wikipedia.org/wiki/Tuple_space), verified
2026-08-02). A tuple space is a shared, associative, in-memory repository.
Producers write tuples into it, consumers read or take tuples that match a
pattern, and neither side needs to know the identity or location of the
other. Space-Based Architecture inherits this shared-space idea and wraps it
in a deployable unit that also carries application logic, which is the
detail that separates it from a bare tuple space or a generic distributed
cache.

The commercial name most associated with the pattern is GigaSpaces XAP. The
company GigaSpaces Technologies was founded in 2000 by Nati Shalom and builds
software for in-memory computing and low-latency data processing used across
finance, retail, and transportation
([Wikipedia, GigaSpaces](https://en.wikipedia.org/wiki/GigaSpaces), verified
2026-08-02). The name Cloud Application Architecture is used as an alternative
label in some vendor and conference material for the same pattern, because
the elastic, stateless-scaling shape the pattern produces was marketed
specifically as a cloud-native answer to database bottlenecks. Mark Richards
gives Space-Based Architecture its own chapter in "Software Architecture
Patterns," O'Reilly, 1st edition, 2015, chapter 7, and that chapter is the
most widely cited software-engineering-book treatment of the pattern's
component model.

## 2. Problem and context

A system built as a stateless application tier in front of a single
relational database scales the application tier easily and the database tier
badly. Add more web servers and throughput on the front door goes up. The
database does not get faster from that, because every request still funnels
through the same connection pool, the same lock manager, and the same disk.
Under a sudden spike, a flash sale, a market open, a ticket release, a
breaking-news search spike, the database becomes the one component that
cannot be horizontally added to on short notice, and it becomes the point
where the whole system either queues, times out, or falls over.

Space-Based Architecture is a reaction to that specific failure shape. It
targets systems where load is unpredictable and can grow by an order of
magnitude in minutes, where the business cannot tolerate the database being
the ceiling on throughput, and where the state involved in a single unit of
work, a shopping cart, an order book, a search session, a trading position,
is naturally partitionable so it does not need to be joined against the
whole data set on every read. The pattern moves the state that a request
actually touches into memory, colocated with the code that processes it, and
removes the central database from the request path entirely for as long as
the system can run that way. Writes still eventually reach durable storage,
but asynchronously, off the critical path.

The context in which the pattern earns its cost is narrow. It fits a system
with bursty, hard-to-predict traffic and state that can be sharded by a
natural key, session, cart, order, symbol. It does not fit a system whose
core operations are complex multi-entity joins and reports across the whole
data set, because that class of query is exactly what a tuple space and a
partitioned in-memory grid are bad at.

## 3. Forces

**Throughput ceiling versus data consistency.** Removing the database from
the hot path removes the one component that was serialising every write
through a single ACID engine. That buys throughput and buys it back the
moment traffic spikes, but it trades away the guarantee that every reader
sees the latest write immediately, because propagation from the in-memory
grid to the durable store, and between partitions, is asynchronous by
design.

**Elastic scaling versus operational complexity.** A processing unit can be
added or removed at runtime and the system rebalances the partitions it
owns. That elasticity is the entire economic case for the pattern, since
capacity tracks load rather than being provisioned for worst case. The cost
is a genuinely more complex runtime than a stateless web tier plus a
database, because now there is a distributed in-memory data set that must
be rebalanced, replicated, and recovered without losing data during a node
failure.

**Latency versus durability.** Reads and writes against a colocated
in-memory partition are very fast. Durability is deliberately deferred, and
the write-behind interval between an in-memory write and its landing in the
durable store is a window where a node failure can lose data unless
replication covers it. This is a genuine trade, judged here as engineering
reasoning rather than a sourced figure, and the pattern does not eliminate
the trade, it only moves where the operator decides to sit on it, via
replication factor and write-behind batching interval.

**Partition affinity versus cross-entity queries.** Colocating an entity's
data and the code that operates on it inside one partition is what makes
local, lock-free, in-memory operations possible. The same colocation is
what makes a query spanning many partitions, or a join across two entity
types that were sharded on different keys, expensive, because it has to
fan out to every partition and merge results in the caller. A system whose
primary access pattern is analytical or relational rather than
transactional and per-entity fights this force constantly.

**Team topology and cognitive load.** A stateless three-tier system is
familiar to almost every engineer who has shipped a web application.
Space-Based Architecture asks a team to reason about partition ownership,
rebalancing, replication factor, eventual consistency at the data-store
boundary, and a messaging fabric between processing units. Judged as
engineering reasoning, this is a real cost in onboarding time and in the
number of new failure modes an on-call engineer has to hold in their head,
weighed against the throughput ceiling the pattern removes.

## 4. Applicability and non-applicability

Reach for Space-Based Architecture when:

- Traffic is bursty and unpredictable by an order of magnitude or more, and
  the cost of under-provisioning for a spike is unacceptable to the
  business, a ticket sale, a product launch, a market open, a breaking news
  event.
- The state touched by a single unit of work is naturally shardable by a
  key that is known at request time, a user id, a cart id, an order id, a
  trading symbol, and most operations against that unit of work do not need
  to join across shards.
- The system can tolerate eventual, rather than immediate, durability for
  most writes, with a bounded and monitored write-behind window.
- Read-modify-write logic against hot, contended entities is the main
  workload, and a relational database's lock contention on those same rows
  is the actual bottleneck being observed.
- The organisation can afford the operational investment of running and
  monitoring a distributed in-memory grid, including its replication and
  rebalancing behaviour, as a permanent part of the platform.

Do NOT reach for Space-Based Architecture when:

- The workload is mostly ad hoc analytical queries, multi-entity joins, or
  reporting across the full data set. The colocation that makes the
  pattern fast for per-entity operations makes it slow and complex for
  exactly this workload, and a columnar warehouse or a well-indexed
  relational store will outperform it here with far less operational cost.
- Traffic is steady and predictable and the existing database has headroom.
  The pattern's entire justification is absorbing unpredictable spikes
  without over-provisioning, and paying its operational cost against a flat
  load curve is a net loss.
- The team has no existing experience running a distributed, replicated,
  in-memory system and cannot invest in that experience before a first
  production incident happens outside business hours. This is judgement,
  but it is the single most common reason organisations that adopt the
  pattern late regret it, per the operational-complexity force above.
- Strict, immediate, single-writer consistency is a hard legal or financial
  requirement for the specific operation in question, for example a
  double-entry ledger posting that must never be read in an inconsistent
  intermediate state by any reader, anywhere, at any time. Use a
  strongly-consistent data store for that specific operation and reserve
  the space-based tier for the surrounding, less strict, high-throughput
  work.
- The data set genuinely does not fit in the aggregate RAM the organisation
  is willing to provision across the cluster, and cannot be shrunk by
  archiving cold data out of the space. Paying for RAM at the volume a cold
  data set requires is usually a worse trade than keeping that data in a
  disk-backed store and reaching for it less often.

## 5. Structure

**Processing unit.** The deployable, self-contained unit of the
architecture. Each processing unit bundles application logic together with
an in-memory data partition it owns, so the code that processes an entity
runs in the same process, or the same host, as the data for that entity.
Processing units are the scale and fail-over unit, per the Wikipedia
description of the pattern. Adding capacity means starting more processing
units, not scaling a shared central tier.

**Virtualised middleware.** The layer that sits between the application code
and the physical cluster, giving every processing unit the same runtime
contract regardless of which physical host it lands on. It is composed of
three grids.

**Messaging grid.** Routes incoming requests to the processing unit that
currently owns the relevant partition, and handles the request-and-response
plumbing so application code does not talk to a message broker directly.

**Data grid.** The distributed, replicated, in-memory tuple space itself.
Holds the partitioned entity data, replicates it for fault tolerance, and
is the component from which asynchronous write-behind to a durable store is
triggered.

**Processing grid, where present.** Coordinates work that spans more than
one processing unit, typically a master and worker pattern for a
computation too large or too parallel for one partition to run alone.

**Deployment manager.** Watches load against a service level agreement and
starts or stops processing units to keep the cluster inside that agreement.
This is the component that gives the pattern its elasticity, because
capacity is a function of observed demand rather than a fixed provisioning
decision.

**Data pump and data writer.** The asynchronous write-behind path out of the
data grid into a durable system of record, usually a relational database, a
data warehouse, or an event log. The data pump reads changes out of the
space and the data writer applies them to durable storage, decoupled in
time from the original write.

**Data reader, on cold start.** The inverse of the data pump. Loads the
durable store's data into the space when a processing unit starts cold, so
a freshly started unit does not begin with an empty partition.

## 6. ASCII structure diagram

```
                         +---------------------------+
                         |     Deployment Manager     |
                         |  watches SLA, starts/stops  |
                         |       processing units      |
                         +--------------+--------------+
                                        |
                                        v
        +-------------------------------------------------------------+
        |                    Virtualized Middleware                    |
        |  +----------------+  +----------------+  +----------------+  |
        |  | Messaging Grid |  |   Data Grid    |  | Processing Grid|  |
        |  | routes request |  | tuple space,   |  | master/worker  |  |
        |  | to owning unit |  | replicated,    |  | for cross-unit |  |
        |  |                |  | in memory      |  | computation    |  |
        |  +--------+-------+  +--------+-------+  +--------+-------+  |
        +-----------|--------------------|--------------------|--------+
                     |                    |                    |
       +-------------+------+ +-----------+--------+ +---------+----------+
       |  Processing Unit A | |  Processing Unit B | |  Processing Unit C |
       |  app logic + owned | |  app logic + owned | |  app logic + owned |
       |  data partition    | |  data partition    | |  data partition    |
       +---------------------+ +---------------------+ +---------------------+
                     \                    |                    /
                      \                   |                   /
                       v                  v                  v
                    +-------------------------------------------+
                    |     Data Pump (async write-behind)          |
                    +----------------------+----------------------+
                                            |
                                            v
                    +-------------------------------------------+
                    |   Durable System of Record (RDBMS, log,     |
                    |   warehouse)  read back on cold start via   |
                    |   the Data Reader                            |
                    +-------------------------------------------+
```

## 7. Dynamics

**Write path, steady state.** A client request arrives at the messaging
grid. The grid inspects the request for its partition key and routes it to
the processing unit that owns that partition. The processing unit reads,
mutates, and writes the tuple entirely in its own in-memory partition, then
replies to the caller. No call touches the durable store on this path. The
data grid asynchronously queues the change for the data pump, which
eventually applies it to the durable system of record, on a schedule
independent of the request that caused it.

**Read path, steady state.** Identical routing step. The owning processing
unit answers directly out of memory. Because ownership is by partition, a
read for an entity always lands on the same processing unit that most
recently wrote it, within one replica set, which is what gives the pattern
its read-after-write consistency for a single entity even though the
overall system is eventually consistent with the durable store.

**Elastic scale-out.** The deployment manager observes that a service level
agreement threshold, request latency or queue depth per processing unit, is
being breached. It starts additional processing units. The data grid
rebalances a subset of partitions onto the new units, migrating the
in-memory data for those partitions live. The messaging grid's routing
table is updated so future requests for a migrated partition reach the new
owner. Requests in flight during the migration window are the operationally
delicate part of this dynamic, and implementations differ in whether they
buffer, retry, or reject during that window.

**Node failure and fail-over.** A processing unit disappears without a
clean shutdown. Its partitions were replicated to at least one other unit,
per the deployment's replication factor. The data grid promotes a replica
to primary for each affected partition. The messaging grid's routing table
updates to point at the new primary. Any write that had been accepted by
the failed unit but not yet replicated at the moment of failure is lost,
which is why replication factor and synchronous-versus-asynchronous
replication mode are the two knobs that decide how much data loss a single
node failure can cause.

**Cold start.** A brand-new processing unit starts with no data. Before it
begins serving requests for the partitions it will own, the data reader
loads the relevant data from the durable system of record into the unit's
in-memory space. Only after that load completes does the messaging grid
begin routing traffic to it, so a client never sees a partially populated
partition.

## 8. Implementation variants

**Full commercial grid product.** GigaSpaces XAP is the reference
commercial implementation, providing the messaging grid, data grid,
processing grid, and deployment manager as an integrated product rather
than components a team assembles itself
([GigaSpaces company overview, Wikipedia](https://en.wikipedia.org/wiki/GigaSpaces),
verified 2026-08-02). Teams adopt the full product when they want the
elasticity and SLA-driven deployment manager as a delivered feature rather
than something built in-house.

**Assembled from an in-memory data grid plus application-tier convention.**
A team builds the same shape out of a general-purpose in-memory data grid,
Hazelcast or a comparable distributed cache framework, plus its own
convention for colocating handler logic with partition ownership. This
variant gets the data grid and partition-aware routing from the library,
and the team writes its own processing-unit boundary and deployment
automation. Hazelcast, described on its own Wikipedia entry as an
in-memory data grid distributing data evenly across a cluster with
horizontal scaling and distributed backups, is used this way, and the
Eclipse Vert.x toolkit uses Hazelcast for its own shared, clustered state,
which is a variant of the same colocated-data idea at a smaller scope than
a full SBA deployment
([Wikipedia, Hazelcast](https://en.wikipedia.org/wiki/Hazelcast), verified
2026-08-02).

**Actor-model variant.** Instead of a tuple space, the partition-owning
unit is modelled as an actor or a sharded actor pool, where the actor's
mailbox serialises access to its owned state and actor placement across a
cluster does the job the data grid's partition ownership does in the
classic form. This trades the associative, pattern-matching tuple-space
read for message-passing to a known actor address, and is common where a
team already has an actor runtime in place rather than adopting a
dedicated grid product.

**Event-log-backed variant.** The durable system of record is an
append-only event log rather than a relational database, and the data pump
becomes an event producer. Cold start rebuilds a processing unit's
partition by replaying the relevant segment of the log rather than reading
current-state rows. This variant is common where the organisation has
already standardised on event sourcing for its durability layer and wants
Space-Based Architecture only for the in-memory, elastic front tier.

**Cloud-managed cache as the data grid.** A managed, clustered in-memory
cache service stands in for a self-hosted data grid, and the team writes
its own thin messaging and deployment-manager layer on top using the cloud
provider's autoscaling primitives. This lowers the operational burden of
running the grid itself, at the cost of the cache service's own
consistency and eviction semantics leaking into how strictly the pattern's
partition-ownership guarantee actually holds.

## 9. Known production uses

**MSN Live Search, 1999, and an MSN customer marketing data store.** The
Wikipedia article on Space-Based Architecture states the pattern originated
at Microsoft in 1997 to 1998 as the internal Youkon Distributed Caching
platform and names an early production deployment serving MSN Live Search
in September 1999
([Wikipedia, Space-based architecture](https://en.wikipedia.org/wiki/Space-based_architecture),
verified 2026-08-02). The same article states the pattern subsequently saw
use "in many firms in the securities industry for implementing scalable
electronic securities trading applications," naming the sector rather than
individual firms.

**GigaSpaces XAP, and the Razorfish elastic application platform case
study.** GigaSpaces Technologies, founded in 2000 by Nati Shalom, built XAP
specifically to implement this pattern as a commercial product, and its
Wikipedia entry cites a Forrester Research case study, "Razorfish Uses an
Elastic Application Platform," describing Razorfish's use of the platform
for an iPhone product launch in 2010
([Wikipedia, GigaSpaces](https://en.wikipedia.org/wiki/GigaSpaces), verified
2026-08-02). The same source states GigaSpaces announced partnerships with
IBM and Wix in 2022, indicating continued commercial adoption of the
underlying grid technology well beyond the pattern's original invention.

**Eclipse Vert.x, using Hazelcast for clustered shared state.** The
Wikipedia entry on Hazelcast states that Vert.x, the polyglot event-driven
application toolkit, uses Hazelcast for its shared, clustered storage
([Wikipedia, Hazelcast](https://en.wikipedia.org/wiki/Hazelcast), verified
2026-08-02). This is a smaller-scope instance of the same colocated,
in-memory, partition-owned data idea that underlies full Space-Based
Architecture, embedded inside a widely deployed open-source toolkit rather
than run as a standalone architecture.

**GridGain Systems and the Apache Software Foundation grid project it
donated.** A distributed database management system for high-performance
computing that uses RAM as its primary storage layer and stores data as
key-value pairs distributed across cluster nodes was developed by GridGain
Systems and later contributed to the Apache Software Foundation, where the
project has been ranked among the top five most active Apache projects by
some metrics, per that project's own Wikipedia entry, verified 2026-08-02.
It is used both as a standalone in-memory data grid and as the data-grid
component underneath a hand-assembled Space-Based Architecture, per
implementation variant two above.

## 10. Consequences

Positive.

- Removes the central database from the hot request path for the majority
  of traffic, which removes the single most common ceiling on throughput
  in a conventional three-tier system.
- Scales elastically, adding or removing processing units in response to
  observed load, so provisioning tracks demand rather than sitting fixed
  at a worst-case estimate.
- Gives very low read and write latency for the main, per-entity access
  pattern, because the data being touched is in the same process or the
  same host as the code touching it.
- Survives a single node failure without data loss when replication factor
  and replication mode are configured correctly, because a replica is
  promoted and the messaging grid re-routes automatically.
- Decouples the durability write path from the request path entirely, so a
  slow or momentarily unavailable durable store does not directly stall
  incoming requests, only the eventual persistence of already-accepted
  writes.

Negative.

- Introduces eventual, rather than immediate, consistency between the
  in-memory grid and the durable system of record, and any reader that
  bypasses the grid and reads the durable store directly can see stale
  data for the length of the write-behind window.
- Cross-partition and cross-entity queries are expensive relative to a
  well-indexed relational database, because they require fan-out across
  partitions and merging in the caller rather than a single indexed join.
- Operational surface area grows substantially. Replication factor,
  rebalancing behaviour during scale events, write-behind batching and
  failure handling, and cold-start data loading are all new failure modes
  that a conventional stateless-application-plus-database system does not
  have.
- Memory becomes the primary capacity-planning constraint instead of disk
  or database connections, and a data set that grows faster than the
  organisation is willing to provision RAM for becomes a hard limit the
  pattern does not solve on its own.
- A node failure inside the write-behind window can lose the most recent
  writes for the affected partition if replication mode is asynchronous
  and no replica had yet received them, which is a real, not theoretical,
  consistency cost that must be weighed against the operation's actual
  durability requirement.

## 11. Failure modes and misuse

**Symptom.** Two different clients reading the same entity id in quick
succession see different values, and neither read is stale by more than a
few milliseconds, yet the discrepancy causes a support ticket. **Cause.**
The read landed on two different replicas of the same partition, and the
replication between them had not yet converged at the moment of the second
read, because the deployment uses asynchronous rather than synchronous
replication for that partition's data. **Fix.** Route reads that must be
strictly consistent through the primary replica only, not any replica, or
switch the affected partition's replication mode to synchronous at the
cost of higher write latency, and document which operations genuinely need
that guarantee rather than applying it everywhere.

**Symptom.** During a scale-out event, a small percentage of requests
return an error or a stale result for entities whose partition is mid
migration. **Cause.** The messaging grid's routing table update and the
data grid's partition migration are not perfectly atomic with each other,
so there is a window where a request can be routed to the old owner after
the partition has already begun moving, or to the new owner before the
data has fully arrived. **Fix.** Configure the grid's migration mode to
buffer or retry in-flight requests during a migration rather than fail
them immediately, and load-test scale-out events specifically, not only
steady-state throughput, before trusting the deployment manager's
automatic scaling in production.

**Symptom.** A processing unit crashes and, on restart, several minutes of
recent writes for its partitions are simply gone, with no error anywhere
in the logs. **Cause.** Replication factor was set to a value where the
crashed unit was the sole holder of the most recent writes for one or more
partitions, and the write-behind interval to the durable store had not
yet flushed those writes either. This is the single most damaging and
most avoidable failure mode of the pattern. **Fix.** Set replication
factor to at least two for any partition holding data whose loss has real
cost, and treat the write-behind interval as a tunable durability
parameter that is set deliberately per data class, not left at a library
default nobody has reviewed.

**Symptom.** A new reporting requirement asks for a join across two
entity types that were partitioned by different keys, and the query that
used to take milliseconds against the old relational schema now takes
tens of seconds against the space. **Cause.** Misuse of the pattern, not
a bug in it. The team is running an analytical query pattern against a
system designed and partitioned for per-entity transactional operations,
which is exactly the non-applicability case named in dimension four.
**Fix.** Route this class of query to the durable system of record or a
dedicated analytical store fed by the data pump's change stream, and stop
treating the in-memory grid as a general-purpose queryable database.

**Symptom.** The in-memory footprint of the cluster keeps growing and
nobody can point to a single change that caused it. **Cause.** The grid is
being used as a permanent store rather than a working set, with no
eviction or archival policy for cold entities, so data that is never
touched again keeps consuming RAM indefinitely. **Fix.** Introduce an
explicit archival or eviction policy that moves cold partitions to the
durable store and out of the space, keyed on last-access time or a
domain-specific staleness rule, and monitor RAM growth against active
entity count rather than against total historical entity count.

## 12. Trade-off matrix

| Force | Space-Based Architecture | Layered Architecture (RDBMS-centric) | Microservices Architecture |
|---|---|---|---|
| Write throughput under a sudden spike | High. Bypasses the central database on the hot path | Low. Every write serialises through one relational engine's locks | Moderate. Depends entirely on each service's own database, no shared answer |
| Read latency for a single, known entity | Very low. In-memory, colocated with the handling code | Moderate. Round trip to the database, mitigated by caching | Varies per service, typically a network hop plus that service's own store |
| Cross-entity, ad hoc queries | Poor. Requires fan-out and merge across partitions | Strong. A relational engine's native strength | Poor across service boundaries, requires a separate read model or aggregation layer |
| Elastic scale-out in minutes | Strong. Deployment manager adds processing units against an SLA | Weak. The database itself rarely scales out this fast or this cheaply | Strong for stateless services, weak for any service still backed by a single relational store |
| Consistency model | Eventual between grid and durable store, read-after-write within a partition's owning replica | Immediate, ACID, at the cost of the throughput ceiling above | Per-service choice, often eventual at the boundary between services regardless of any single service's internal consistency |
| Operational complexity | High. Distributed in-memory grid, replication, rebalancing, write-behind, cold start | Low to moderate. A single well-understood database to operate | High. Many independently deployed services, each with its own operational surface |
| Team familiarity and onboarding cost | Low. Few engineers have run a tuple-space or in-memory-grid system before | High. Nearly every backend engineer has operated against a relational database | Moderate to high, but the individual pieces, an HTTP service and a database, are individually familiar |

## 13. Related and incompatible patterns

**Event-Driven Architecture.** The messaging grid's routing and the
asynchronous write-behind path are both instances of event-style,
decoupled communication, and a Space-Based Architecture deployment is
frequently built with an event bus underneath its messaging grid rather
than a bespoke transport. The two patterns compose naturally, because
Space-Based Architecture is, in large part, an application of
event-driven principles to the specific problem of stateful throughput.

**Microservices Architecture.** A processing unit is architecturally
similar to a single microservice that happens to own an in-memory
partition of its data rather than an external database of its own. Teams
that have already adopted microservices sometimes introduce Space-Based
Architecture selectively, for the one or two services whose write
throughput under load is the system's actual bottleneck, rather than
across the whole system.

**Serverless Architecture.** Both patterns chase elastic, demand-driven
capacity, but they diverge sharply on state. Serverless functions are
explicitly stateless between invocations and push all state to an
external store, while Space-Based Architecture's entire value proposition
is keeping state in memory, colocated with the code that operates on it.
Combining the two directly conflicts, since a serverless function cannot
own a long-lived in-memory partition across invocations without defeating
the serverless execution model's own assumptions.

**Layered Architecture, RDBMS-centric variant, incompatible.** The two
patterns solve the same class of problem from opposite ends. Layered
Architecture accepts the central relational database as the single
source of truth on the request path and optimises around it. Space-Based
Architecture exists specifically to remove the database from that path.
A system cannot coherently claim both, a strictly layered request flow
where every write goes straight to the database, and a space-based flow
where writes land in memory first, for the same data at the same time,
without one of the two guarantees being false.

**CQRS, where present elsewhere in a repository's catalog.** The data
pump's write-behind path and the eventual arrival of data in the durable
store mirror the command side of a Command Query Responsibility
Segregation split, with the durable store acting as the read side that
downstream reporting queries against. Systems that already separate
reads from writes at the architecture level find Space-Based
Architecture a natural fit for the command side specifically.

## 14. Refactoring path in and out

**Introducing the pattern into an existing layered system.** Start by
identifying the single database table, or small set of tables, whose row
locking is the actual observed throughput ceiling under load, using real
production contention metrics rather than a guess. Introduce an
in-memory data grid as a write-behind cache in front of that specific
table only, with the application still reading and writing through the
existing data access layer, but that layer now writing to the grid first
and the grid asynchronously flushing to the database. Verify, under a
realistic load test, that the write-behind window and replication factor
give an acceptable data-loss bound before removing the direct
database-write path from the application. Only once this narrow slice is
stable and monitored in production does it make sense to extend
partition ownership and colocated processing logic to a second entity
type, repeating the same measure-first discipline each time. Never
introduce the full pattern, messaging grid, processing grid, deployment
manager, all at once across an entire system in one migration, because
that removes the ability to isolate which specific component caused a
production incident.

**Removing the pattern once it stops earning its place.** This happens
when traffic has stabilised, in-memory operational cost is
disproportionate to the throughput actually needed, or the team's query
needs have shifted toward the cross-entity, analytical pattern the
architecture handles poorly. Reverse the introduction path. Route new
writes for the affected entity directly to the durable store again,
behind a feature flag, while the space continues serving reads from its
existing, now-frozen, data. Once the durable store is confirmed to be the
source of truth for all new writes and the space has fully drained via
its normal write-behind mechanism, switch reads to the durable store as
well, then decommission the processing units for that entity type.
Removing the pattern entity-by-entity, in the reverse order it was
introduced, keeps the same isolation property that made the introduction
safe.

## 15. Testing and verification

Unit testing the application logic inside a single processing unit is
straightforward, because the tuple-space or grid API used to read and
write local partition data can be run against an embedded, single-node
instance of the same grid product in a test process, with no network
involved. This is easy specifically because Space-Based Architecture
colocates logic and data, so a unit test does not need to mock a
database connection, it can run against a real, local, in-memory space.

What becomes hard is verifying the distributed behaviours, partition
migration during scale-out, replica promotion during a node failure, and
the write-behind window's actual data-loss bound under a real failure
injection. These require an integration test rig that runs a multi-node
cluster, deliberately kills a node mid-write, and asserts on what
survives, rather than a unit test against a single embedded instance.
Chaos-style fault injection, deliberately killing a processing unit under
active load and asserting the messaging grid re-routes within a bounded
time, is the test technique that catches the two most damaging failure
modes from dimension eleven, silent data loss on node failure and stale
reads during replication lag, neither of which a single-node test can
ever exercise.

Contract testing between a processing unit and its durable system of
record is also worth explicit attention, because the data pump and data
reader are the one place where the in-memory model and the durable
schema must agree on shape, and a silent drift between the two only
surfaces at cold start or during a durability audit, both of which are
rare enough in a fast-moving codebase that an explicit, automated
contract test catches drift far earlier than a human would.

## 16. Observability signals

A healthy deployment shows a stable count of processing units tracking a
slowly varying load curve, with scale-out and scale-in events occurring
smoothly rather than in large abrupt jumps, and partition rebalancing
events completing within a bounded, monitored duration rather than
lingering. The write-behind queue depth, the number of writes accepted
into the space but not yet flushed to the durable store, is the single
most important number to graph, because a steadily growing queue depth
is the earliest visible sign that the durable store cannot keep up with
write volume, which is exactly the condition under which a node failure
turns into real data loss.

A failing or degraded instance shows replica lag climbing between a
partition's primary and its replicas, an increasing rate of requests
being retried or rejected during migration windows, and, most seriously,
a rising rate of cold-start failures where a newly started processing
unit cannot fully load its assigned partitions from the durable store
before it is expected to begin serving traffic. Per-partition hot-key
skew, where one partition receives disproportionate load relative to its
peers because the sharding key was chosen poorly, shows up as one
processing unit's latency and CPU diverging sharply from the rest of the
cluster while overall cluster-wide averages still look acceptable, which
is why per-partition, not only cluster-average, dashboards are necessary
for this pattern specifically.

## 17. Security and privacy implications

Data at rest in the in-memory grid is, by the nature of the pattern,
unencrypted plaintext in process memory unless the grid product's own
in-memory encryption feature is explicitly enabled, and that feature
carries a real throughput cost that runs counter to the pattern's core
purpose, which creates a genuine tension a security review must weigh
rather than assume away. Because processing units are frequently added
and removed elastically, and partitions migrate live between hosts
during scale events, sensitive data can end up resident on a wider set
of physical or virtual hosts over the lifetime of a deployment than a
single, fixed database server would ever touch, which widens the blast
radius of a single compromised host and should inform which data classes
are permitted into the space at all.

The messaging grid, as the component that routes every request to its
owning partition, is a natural point to enforce authorization before a
request ever reaches application logic, and centralising that check
there, rather than duplicating it inside every processing unit, keeps
the enforcement point auditable. The write-behind path to the durable
store is an asynchronous background process running with its own
credentials against the durable system of record, and because it is not
directly triggered by a user-facing request, it is also not naturally
covered by request-level audit logging, so it needs its own explicit
audit trail if the durable store holds regulated data. Where a data
class is subject to a right-to-erasure or a retention-limit requirement,
the eventual and asynchronous nature of the write-behind path means an
erasure request must be tracked until it is confirmed to have propagated
out of every replica of the in-memory grid, not only out of the durable
store, because the space itself is a separate copy of the data with its
own separate lifetime.

## Code examples

Three languages, one shared scenario. two processing units each own a
partition of accounts, a messaging grid routes by account id, and a
write-behind flush drains the in-memory space into a durable store. Java is
omitted here to keep the example set to three, since the routing and
write-behind shape is identical across all four languages this pattern is
commonly built in, and TypeScript, Python, and Go already show the
object-oriented, dynamically-typed, and statically-compiled treatments.

### TypeScript

```typescript
type Tuple = { id: string; balance: number; version: number };

class DurableStore {
  private rows = new Map<string, Tuple>();
  write(t: Tuple): void {
    this.rows.set(t.id, t);
  }
  read(id: string): Tuple | undefined {
    return this.rows.get(id);
  }
}

class ProcessingUnit {
  private partition = new Map<string, Tuple>();
  private writeBehind: Tuple[] = [];

  constructor(private readonly store: DurableStore) {}

  put(t: Tuple): void {
    this.partition.set(t.id, t);
    this.writeBehind.push(t);
  }

  get(id: string): Tuple | undefined {
    return this.partition.get(id);
  }

  flush(): number {
    const n = this.writeBehind.length;
    for (const t of this.writeBehind) this.store.write(t);
    this.writeBehind = [];
    return n;
  }
}

class MessagingGrid {
  private units: ProcessingUnit[];
  constructor(units: ProcessingUnit[]) {
    this.units = units;
  }
  private route(id: string): ProcessingUnit {
    let hash = 0;
    for (const ch of id) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0;
    return this.units[hash % this.units.length];
  }
  deposit(id: string, balance: number): void {
    this.route(id).put({ id, balance, version: 1 });
  }
  withdraw(id: string, amount: number): void {
    const owner = this.route(id);
    const existing = owner.get(id);
    if (!existing) throw new Error(`unknown account ${id}`);
    owner.put({ id, balance: existing.balance - amount, version: existing.version + 1 });
  }
  balance(id: string): number | undefined {
    return this.route(id).get(id)?.balance;
  }
}

function main(): void {
  const store = new DurableStore();
  const units = [new ProcessingUnit(store), new ProcessingUnit(store)];
  const grid = new MessagingGrid(units);

  grid.deposit("acct-1", 100);
  grid.withdraw("acct-1", 30);
  console.log("in-memory balance", grid.balance("acct-1"));

  let flushed = 0;
  for (const u of units) flushed += u.flush();
  console.log("write-behind flushed", flushed, "durable balance", store.read("acct-1")?.balance);
}

main();
```

### Python

```python
from __future__ import annotations
from dataclasses import dataclass, replace


@dataclass
class Tuple_:
    id: str
    balance: int
    version: int


class DurableStore:
    def __init__(self) -> None:
        self._rows: dict[str, Tuple_] = {}

    def write(self, t: Tuple_) -> None:
        self._rows[t.id] = t

    def read(self, id_: str) -> Tuple_ | None:
        return self._rows.get(id_)


class ProcessingUnit:
    def __init__(self, store: DurableStore) -> None:
        self._store = store
        self._partition: dict[str, Tuple_] = {}
        self._write_behind: list[Tuple_] = []

    def put(self, t: Tuple_) -> None:
        self._partition[t.id] = t
        self._write_behind.append(t)

    def get(self, id_: str) -> Tuple_ | None:
        return self._partition.get(id_)

    def flush(self) -> int:
        n = len(self._write_behind)
        for t in self._write_behind:
            self._store.write(t)
        self._write_behind = []
        return n


class MessagingGrid:
    def __init__(self, units: list[ProcessingUnit]) -> None:
        self._units = units

    def _route(self, id_: str) -> ProcessingUnit:
        h = 0
        for ch in id_:
            h = (h * 31 + ord(ch)) % (2**32)
        return self._units[h % len(self._units)]

    def deposit(self, id_: str, balance: int) -> None:
        self._route(id_).put(Tuple_(id_, balance, 1))

    def withdraw(self, id_: str, amount: int) -> None:
        owner = self._route(id_)
        existing = owner.get(id_)
        if existing is None:
            raise KeyError(f"unknown account {id_}")
        owner.put(replace(existing, balance=existing.balance - amount, version=existing.version + 1))

    def balance(self, id_: str) -> int | None:
        t = self._route(id_).get(id_)
        return t.balance if t else None


def main() -> None:
    store = DurableStore()
    units = [ProcessingUnit(store), ProcessingUnit(store)]
    grid = MessagingGrid(units)

    grid.deposit("acct-1", 100)
    grid.withdraw("acct-1", 30)
    print("in-memory balance", grid.balance("acct-1"))

    flushed = sum(u.flush() for u in units)
    row = store.read("acct-1")
    print("write-behind flushed", flushed, "durable balance", row.balance if row else None)


if __name__ == "__main__":
    main()
```

### Go

```go
package main

import "fmt"

type tuple struct {
	id      string
	balance int
	version int
}

type durableStore struct {
	rows map[string]tuple
}

func newDurableStore() *durableStore {
	return &durableStore{rows: make(map[string]tuple)}
}

func (d *durableStore) write(t tuple) {
	d.rows[t.id] = t
}

func (d *durableStore) read(id string) (tuple, bool) {
	t, ok := d.rows[id]
	return t, ok
}

type processingUnit struct {
	store       *durableStore
	partition   map[string]tuple
	writeBehind []tuple
}

func newProcessingUnit(store *durableStore) *processingUnit {
	return &processingUnit{store: store, partition: make(map[string]tuple)}
}

func (p *processingUnit) put(t tuple) {
	p.partition[t.id] = t
	p.writeBehind = append(p.writeBehind, t)
}

func (p *processingUnit) get(id string) (tuple, bool) {
	t, ok := p.partition[id]
	return t, ok
}

func (p *processingUnit) flush() int {
	n := len(p.writeBehind)
	for _, t := range p.writeBehind {
		p.store.write(t)
	}
	p.writeBehind = nil
	return n
}

type messagingGrid struct {
	units []*processingUnit
}

func (m *messagingGrid) route(id string) *processingUnit {
	var h uint32
	for _, ch := range id {
		h = h*31 + uint32(ch)
	}
	return m.units[int(h)%len(m.units)]
}

func (m *messagingGrid) deposit(id string, balance int) {
	m.route(id).put(tuple{id: id, balance: balance, version: 1})
}

func (m *messagingGrid) withdraw(id string, amount int) error {
	owner := m.route(id)
	existing, ok := owner.get(id)
	if !ok {
		return fmt.Errorf("unknown account %s", id)
	}
	owner.put(tuple{id: id, balance: existing.balance - amount, version: existing.version + 1})
	return nil
}

func (m *messagingGrid) balance(id string) (int, bool) {
	t, ok := m.route(id).get(id)
	return t.balance, ok
}

func main() {
	store := newDurableStore()
	units := []*processingUnit{newProcessingUnit(store), newProcessingUnit(store)}
	grid := &messagingGrid{units: units}

	grid.deposit("acct-1", 100)
	if err := grid.withdraw("acct-1", 30); err != nil {
		panic(err)
	}
	balance, _ := grid.balance("acct-1")
	fmt.Println("in-memory balance", balance)

	flushed := 0
	for _, u := range units {
		flushed += u.flush()
	}
	row, _ := store.read("acct-1")
	fmt.Println("write-behind flushed", flushed, "durable balance", row.balance)
}
```

## 18. References

- [Wikipedia, "Space-based architecture"](https://en.wikipedia.org/wiki/Space-based_architecture), verified 2026-08-02.
- [Wikipedia, "Tuple space"](https://en.wikipedia.org/wiki/Tuple_space), verified 2026-08-02.
- [Wikipedia, "GigaSpaces"](https://en.wikipedia.org/wiki/GigaSpaces), verified 2026-08-02.
- [Wikipedia, "Apache Ignite"](https://en.wikipedia.org/wiki/Apache_Ignite), verified 2026-08-02.
- [Wikipedia, "Hazelcast"](https://en.wikipedia.org/wiki/Hazelcast), verified 2026-08-02.
- David Gelernter, "Generative communication in Linda," ACM Transactions on Programming Languages and Systems, 1985, the founding paper for the tuple-space model referenced in dimension 1, cited via the Wikipedia Tuple space entry above.
- Mark Richards, "Software Architecture Patterns," O'Reilly Media, 1st edition, 2015, chapter 7, "Space-Based Architecture." Cited for the component-model treatment referenced in dimensions 5 and 6. Not independently URL-verified in this session because the O'Reilly hosted chapter page returned an HTTP 403 to automated fetch; the book and chapter identification themselves are accurate bibliographic facts, not content pulled from the inaccessible page.
