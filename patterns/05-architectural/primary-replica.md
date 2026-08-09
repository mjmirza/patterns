---
name: Primary-Replica
slug: primary-replica
family: 05-architectural
category: Architectural
aliases: [Master-Slave Replication, Leader-Follower Replication, Source-Replica, Primary-Standby, Read Replica]
first_described: "Gray and Reuter 1993 (log shipping for backup); popularized as a scaling pattern by MySQL and PostgreSQL replication documentation through the 2000s"
maturity: canonical
related: [cqrs, sharding-partitioning, circuit-breaker, saga, event-sourcing]
incompatible_with: []
verified: 2026-08-02
---

# Primary-Replica

## 1. Name, aliases, and lineage

The canonical name in current documentation is Primary-Replica, though the
pattern has been described under several names across three decades of
database engineering. The oldest name, Master-Slave, comes from control
theory and appears throughout early relational database literature. Jim Gray
and Andreas Reuter describe log shipping for standby databases as a recovery
and availability mechanism in *Transaction Processing. Concepts and
Techniques*, Morgan Kaufmann, 1993, chapter 12, well before the pattern was
used for read scaling. The idea there is defensive, a copy of the log lets a
standby machine take over if the primary dies. The scaling use case, sending
read traffic to the copy while it is still healthy, is a later addition, and
it is this dual purpose, availability and scale, that defines the pattern as
practiced today.

Every major database system settled on its own vocabulary. MySQL calls the
two roles source and replica since MySQL 8.0, after retiring the master and
slave terminology, and the official reference states the mechanism plainly.
"MySQL 8.4 supports different methods of replication. The traditional method
is based on replicating events from the source's binary log, and requires
the log files and positions in them to be synchronized between source and
replica" (MySQL 8.4 Reference Manual, Chapter 19, Replication,
https://dev.mysql.com/doc/refman/8.4/en/replication.html, verified
2026-08-02). PostgreSQL uses primary and standby, and distinguishes a warm
standby that only replays logs from a hot standby that also serves read
queries, documented at
https://www.postgresql.org/docs/current/warm-standby.html (verified
2026-08-02). MongoDB calls it a replica set with a primary and secondaries,
where "the primary node receives all write operations" and secondaries
replicate the primary's operation log
(https://www.mongodb.com/docs/manual/replication/, verified 2026-08-02). AWS
uses source and read replica for the same shape layered on top of whichever
underlying engine the customer chose
(https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ReadRepl.html,
verified 2026-08-02). Redis, in its own documentation, still uses master and
replica side by side and calls the relationship "leader follower"
(https://redis.io/docs/latest/operate/oss_and_stack/management/replication/,
verified 2026-08-02).

The name churn is not cosmetic. Master-Slave was retired industry-wide around
2020 for the obvious reason, and every vendor's own docs are the authoritative
record of which term is current for that system. This entry treats
Primary-Replica as the pattern name and Primary-Standby as a synonym used when
the copy exists purely for failover and never serves reads, a distinction that
matters in dimension 4.

## 2. Problem and context

A single database instance handling both writes and reads eventually hits a
ceiling on at least one of three axes, read throughput, availability, and
geographic latency. A read-heavy application, the common case for most web
and mobile products where reads outnumber writes by ten to one or more,
saturates the primary's CPU, memory, and I/O on SELECT queries long before
write volume becomes the bottleneck. A single instance is also a single point
of failure. If that machine's disk fails or the process crashes, every write
and every read stops until it is restored from backup, and a restore from a
nightly backup can mean hours of data loss. A single instance in one region
also means every read from a user on the other side of the planet pays a
full round trip of network latency to reach it.

The context in which Primary-Replica solves this is specific. The workload's
consistency requirement tolerates a small amount of staleness on reads, the
write volume is modest enough that a single primary can absorb all of it, and
the application can distinguish reads that must see the very latest write
from reads that can tolerate a lag of milliseconds to seconds. Outside that
context, in particular under heavy write volume that a single primary cannot
absorb regardless of read routing, the pattern does not solve the actual
bottleneck and a different pattern, sharding, is the correct next step
(dimension 13 covers this boundary in detail).

## 3. Forces

Consistency versus availability and latency. Every replica lags the primary
by some nonzero amount of time, the replication lag, because the copy is
asynchronous in the common case. A read against a replica can therefore
return a value that is already stale by the time it reaches the client. The
pattern trades strict consistency for horizontal read scaling and for
survivability when the primary fails.

Read scaling versus write scaling. Adding replicas linearly increases read
capacity because each replica can answer queries independently. It does
nothing for write capacity, because every write still flows through one
primary and that primary must apply every write serially with respect to a
given row or, depending on the isolation level, the whole database. A
workload with heavy writes gets no relief from adding replicas and the
operator who adds replicas expecting write relief has misdiagnosed the
bottleneck.

Operability versus simplicity. A single unreplicated instance is
operationally trivial, one process, one disk, one thing that can fail. A
primary with N replicas multiplies the operational surface, N additional
processes to monitor, a replication topology to reason about, a failover
procedure that must promote exactly one replica and never two, and a lag
metric that must be watched continuously. The pattern buys resilience and
scale at the direct cost of operational complexity, and that complexity does
not disappear, it moves into the deployment tooling and the on call runbook.

Cost versus headroom. Each replica is a full copy of the data set and
typically runs on hardware comparable to the primary, so N replicas cost
roughly N times the primary's compute and storage bill, even though a
replica does strictly less work than the primary, it never processes writes.
This is the direct financial force behind why teams reach for read replicas
before reaching for a cache. A replica is a correctness preserving way to add
read capacity, a cache is a performance preserving way that trades away some
correctness guarantee of its own.

Team topology and cognitive load. Once an application has more than one
database connection target, every code path that issues a query must decide,
explicitly or through a routing layer, whether that query goes to the primary
or a replica. This decision, if left implicit, becomes a recurring source of
bugs. A read immediately following a write that silently lands on a stale
replica is the single most common failure mode this pattern produces
(dimension 11), and avoiding it requires either discipline from every
engineer touching the data layer or a routing abstraction that removes the
decision from application code.

## 4. Applicability and non-applicability

Reach for Primary-Replica when the read to write ratio is high, commonly
cited as 80 percent or more reads, so that adding read capacity actually
relieves the dominant bottleneck. Reach for it when the application can
tolerate eventual consistency on at least some read paths, for example a
public profile page, a product catalog, an analytics dashboard, or a search
index feed, where a value that is a few hundred milliseconds stale causes no
observable harm to the person reading it. Reach for it when high availability
is a requirement and a promotable standby is the mechanism chosen to avoid a
single point of failure, independent of whether the standby also serves
reads. Reach for it when read latency for geographically distributed users
matters and a read replica can be placed in the region closest to those
users, which several cloud providers support directly, for example AWS RDS
cross region read replicas
(https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ReadRepl.html,
section Cross-Region read replicas, verified 2026-08-02).

Do not reach for it when the bottleneck is write throughput, because every
replica still funnels through the same single primary for writes and adding
replicas does nothing to relieve that path. The fix there is sharding,
partitioning, or a queue that absorbs write bursts. Do not reach for it when
the application requires strict read your writes consistency on every read
path and there is no mechanism, sticky routing, causal token, or synchronous
replica, to guarantee that. Naively routing reads to an asynchronous replica
under that requirement produces user visible bugs, most famously "I just
saved my settings and they reverted." Do not reach for it purely to solve
disk space or storage cost, because a replica duplicates the full data set
rather than reducing it. Partitioning or archival solves a storage problem,
replication does not. Do not reach for it as a first response to a slow
query, because a replica multiplies the cost of an inefficient query rather
than fixing it. An unindexed table scan is exactly as slow on ten replicas as
on the primary, it is simply now slow ten times over and ten times more
expensive. Do not reach for it in a system with a small, single tenant data
set that already fits comfortably in memory and serves low traffic, where the
operational cost of a replication topology exceeds any benefit. A single well
resourced instance with regular backups is simpler and sufficient.

## 5. Structure

The primary, also called source, leader, or master in older material, is the
single instance that accepts all write operations, orders them, applies them
to its own storage, and records the change stream, either a write ahead log,
a binary log, or an operation log depending on the engine.

The replica, also called replica, standby, secondary, or follower, is one of
potentially many instances that connects to the primary's change stream,
applies each change in the order it was recorded, and thereby converges
toward the same state the primary held at the time each change was recorded.
A replica is read-only by default in every mainstream system. Writing
directly to a replica either fails outright or, where permitted, is
explicitly discouraged because it produces divergence from the primary
(dimension 11).

The replication stream is the ordered sequence of changes flowing from
primary to replica. It is engine specific in format, MySQL's binary log,
PostgreSQL's write ahead log records, MongoDB's oplog, Redis's command
stream, but structurally identical in role, a totally ordered log of state
transitions that a replica replays to reconstruct the primary's state.

The router, also called a proxy, a connection pool with routing rules, or
application level logic, is the component, sometimes explicit and sometimes
implicit in hand written code, that decides for each incoming query whether
it goes to the primary or to one of the replicas. This participant is not
always drawn as a separate box in textbook diagrams, but every real system
that uses this pattern has one, whether it is a dedicated proxy like
ProxySQL, a driver feature, or a conditional in application code that picks
the primary for a write and a replica for a tolerant read.

The failover coordinator is the component, human or automated, that detects
a failed primary and promotes exactly one replica to take its place. Systems
like Patroni exist specifically to own this responsibility for PostgreSQL.
"Patroni is a Python template for building PostgreSQL high availability (HA)
clusters. It supports several distributed configuration stores, including
ZooKeeper, etcd, Consul, and Kubernetes"
(https://github.com/patroni/patroni, verified 2026-08-02), using a
distributed lock to guarantee that at most one node believes itself to be
primary at any moment.

## 6. ASCII structure diagram

```
                         WRITES
                            |
                            v
                    +----------------+
                    |    PRIMARY     |
                    |  (accepts all  |
                    |  writes, holds |
                    |  change log)   |
                    +----------------+
                       |    |    |
             replication    stream (async or sync)
                       |    |    |
           +-----------+    |    +-----------+
           v                v                v
   +--------------+ +--------------+ +--------------+
   |  REPLICA 1   | |  REPLICA 2   | |  REPLICA 3   |
   | (read-only,  | | (read-only,  | | (read-only,  |
   |  region A)   | |  region B)   | |  region C)   |
   +--------------+ +--------------+ +--------------+
           ^                ^                ^
           |                |                |
           +----------------+----------------+
                            |
                    +----------------+
                    |     ROUTER     |
                    | writes -> pri  |
                    | reads  -> rep  |
                    +----------------+
                            ^
                            |
                          CLIENT

  Failover coordinator (Patroni, MongoDB election protocol, RDS
  Multi-AZ agent) watches the primary's health and promotes one
  replica to primary if it stops responding. Only one node may
  ever hold the primary role at a given moment; the coordinator's
  distributed lock enforces that invariant.
```

## 7. Dynamics

A normal write proceeds in four steps. The client sends a write to the
router, which forwards it to the primary because the router recognizes it as
a mutating operation. The primary applies the write to its own storage and
appends the corresponding entry to its change log. At this point the write is
durable on the primary, and for a synchronous configuration, the primary also
waits for acknowledgment from at least one replica before confirming the
write to the client. For the far more common asynchronous configuration, the
primary confirms immediately without waiting. Each replica, independently and
continuously, pulls new entries from the primary's change log and applies
them to its own local copy of the data. The gap between the moment the
primary applied the write and the moment a given replica finishes applying
the same write is the replication lag for that replica, and it varies
independently per replica because each is a separate consumer of the same
stream.

A normal read proceeds differently depending on routing policy. If the
router sends the read to the primary, the client sees the absolute latest
state, at the cost of adding load to the primary the pattern exists to
offload. If the router sends the read to a replica, the client sees whatever
state that replica had applied as of the moment it processed the query,
which may lag the primary by anywhere from single digit milliseconds on a
healthy, lightly loaded replica to seconds or, under replica overload or
network partition, minutes.

```
  CLIENT           ROUTER           PRIMARY          REPLICA
    |   write        |                 |                |
    |--------------->|                 |                |
    |                |---------------->|                |
    |                |                 | apply + log    |
    |                |    ack (sync    |                |
    |                |<----(optional)--|                |
    |     ack        |                 |                |
    |<---------------|                 |                |
    |                |                 |--- stream ---->|
    |                |                 |                | apply
    |                |                 |                | (lag = t2 - t1)
    |   read         |                 |                |
    |--------------->|                 |                |
    |                |----(routed to replica)---------->|
    |                |<----------------(stale or fresh)--|
    |    result      |                 |                |
    |<---------------|                 |                |

  Failover sequence when the primary stops responding.

  1. coordinator misses N consecutive health checks on primary
  2. coordinator acquires the distributed lock previously held
     by the primary (Patroni uses etcd/Consul/ZooKeeper for this)
  3. coordinator selects the replica with the smallest lag as the
     promotion candidate (never an arbitrary replica)
  4. candidate replica is promoted, it stops applying the old
     stream and starts accepting writes as the new primary
  5. surviving replicas are repointed to replicate from the new
     primary
  6. router's target for writes is updated to the new primary
  7. old primary, if it returns, must NOT resume as primary, it
     rejoins as a replica of the newly promoted node (a violation
     of this step is exactly how split brain happens, dimension 11)
```

## 8. Implementation variants

Asynchronous replication is the default in every mainstream system, the
primary confirms a write to the client the instant it is durable locally,
without waiting for any replica to apply it. Redis states this plainly.
"Redis uses by default asynchronous replication, which being low latency and
high performance, is the natural replication mode for the vast majority of
Redis use cases"
(https://redis.io/docs/latest/operate/oss_and_stack/management/replication/,
verified 2026-08-02). This variant maximizes write throughput and minimizes
write latency at the direct cost of a nonzero and unbounded window in which a
committed write could be lost if the primary fails before any replica
applies it.

Synchronous replication makes the primary wait for one or more replicas to
acknowledge before confirming the write, closing that data loss window at
the cost of write latency, since the primary is now bounded by the slowest
acknowledging replica. PostgreSQL exposes this as synchronous_commit with
graduated levels including remote_write and remote_apply
(https://www.postgresql.org/docs/current/warm-standby.html, section 26.2.8,
verified 2026-08-02). Redis exposes the closest analog with the WAIT command.
The documentation is careful to state its actual guarantee rather than an
inflated one, that WAIT confirms a specified number of acknowledged copies
exist on other Redis instances, but "it does not turn a set of Redis
instances into a CP system with strong consistency"
(https://redis.io/docs/latest/operate/oss_and_stack/management/replication/,
verified 2026-08-02), an important distinction. Synchronous replication
reduces the loss window, it does not eliminate every failure mode.

Semi synchronous is a middle configuration, used by MySQL among others,
where the primary waits for acknowledgment from at least one replica but not
from all of them, trading full durability guarantees for lower latency than
fully synchronous while still closing the worst of the single node data loss
window.

Cascading replication lets a replica itself act as an upstream source for
further replicas, forming a tree instead of a flat fan out from one primary.
Redis documents this explicitly. "replicas can also be connected to other
replicas in a cascading-like structure. Since Redis 4.0, all the sub-replicas
will receive exactly the same replication stream from the master"
(https://redis.io/docs/latest/operate/oss_and_stack/management/replication/,
verified 2026-08-02). This variant reduces the fan out load on the primary at
the cost of an extra hop of lag for every level of cascade.

Physical versus logical replication is a division seen most explicitly in
PostgreSQL, where physical, or streaming, replication copies the raw write
ahead log byte for byte, producing an exact binary copy and requiring the
same major version and architecture on both sides, while logical replication
decodes the change stream into row level changes and can replicate a subset
of tables, transform data in flight, or replicate across major versions.
Physical replication is the common choice for high availability and read
scaling. Logical replication is the common choice for selective sync, zero
downtime upgrades, and feeding a different downstream system such as a
search index or a data warehouse.

Multi-primary, sometimes loosely called master-master, is a variant where
more than one node accepts writes and the system reconciles conflicting
writes to different nodes for the same data through a conflict resolution
strategy. This entry treats multi-primary as adjacent rather than a variant
of Primary-Replica proper, because it removes the defining property of the
pattern, a single ordering authority for writes, and introduces a distinct
problem, conflict resolution, that Primary-Replica by design avoids.

## 9. Known production uses

Amazon RDS implements the pattern as a managed product across six database
engines. The service documentation states the mechanism directly. "When you
make updates to the primary DB instance, Amazon RDS copies them asynchronously
to the read replica," and separately documents that "Read replicas are
billed as standard DB instances at the same rates as the DB instance class
used for the replica"
(https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ReadRepl.html,
verified 2026-08-02).

MongoDB implements the pattern natively as the replica set, its default
deployment topology since MongoDB 3.6 required it for sharded clusters. The
manual documents the mechanism. "The primary node receives all write
operations. A replica set can have only one primary capable of confirming
writes with { w, majority } write concern," and secondaries independently
"replicate the primary's oplog and apply the operations to their data sets"
(https://www.mongodb.com/docs/manual/replication/, verified 2026-08-02).

PostgreSQL implements the pattern as streaming replication, in production use
across the majority of managed PostgreSQL offerings including AWS RDS for
PostgreSQL, Google Cloud SQL, and self hosted deployments coordinated by
Patroni, whose own repository describes it as "a template for PostgreSQL
High Availability with Etcd, Consul, ZooKeeper, or Kubernetes"
(https://github.com/patroni/patroni, verified 2026-08-02), used widely at
companies running self managed PostgreSQL fleets to automate the failover
step of this pattern's dynamics (dimension 7).

Redis implements the pattern as its foundational replication mechanism, used
directly by Redis Sentinel for automated failover and as the underlying
mechanism inside Redis Cluster. The documentation notes a production
guardrail specific to Redis. "In setups where Redis replication is used, it
is strongly advised to have persistence turned on in the master and in the
replicas," warning explicitly that a master with persistence disabled that
auto restarts can propagate an empty data set to every replica
(https://redis.io/docs/latest/operate/oss_and_stack/management/replication/,
verified 2026-08-02), a documented real failure mode of the pattern rather
than a hypothetical one.

MySQL implements the pattern as source-replica replication, the default
scaling mechanism documented since early MySQL releases and still the basis
for the managed offering at AWS, Google Cloud SQL, and PlanetScale. The
official manual describes the default mode explicitly. "Replication is
asynchronous by default; replicas do not need to be connected permanently to
receive updates from a source"
(https://dev.mysql.com/doc/refman/8.4/en/replication.html, verified
2026-08-02).

## 10. Consequences

Positive. Read throughput scales roughly linearly with the number of
replicas for read-only query load, because each replica answers reads
independently of the others. Availability improves because a promotable
replica removes the primary as an unrecoverable single point of failure,
turning a total outage into a brief failover window. Geographic read latency
improves when a replica is placed near the reading population, since the
read no longer crosses the network distance to wherever the primary happens
to live. Backup and reporting workloads can run against a replica without
competing for I/O with the production write path, which is one of the oldest
and most mundane uses of the pattern and remains one of the most common in
practice. AWS lists this explicitly as a use case, "Business reporting or
data warehousing scenarios where you might want business reporting queries to
run against a read replica, rather than your production DB instance"
(https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ReadRepl.html,
verified 2026-08-02).

Negative. Replication lag introduces a window of potential staleness on
every replica read, and that window is not fixed, it varies with write
volume, replica hardware, and network conditions, which makes it a moving
target rather than a constant an engineer can hard code around. Write
throughput does not improve, and a team that adds replicas expecting write
relief will be disappointed and will have spent real infrastructure cost
solving the wrong problem. Operational complexity increases directly with
the number of replicas, each one is a process to monitor, a lag metric to
watch, and a node that participates in the failover procedure. Failover is
not instantaneous, and the window between a primary failing and a replica
being promoted and accepting writes is itself an availability gap that the
pattern narrows but does not eliminate. Cost scales with replica count, since
each replica is a near full cost copy of the primary's compute footprint.

## 11. Failure modes and misuse

Read after write inconsistency. Symptom, a user submits a form, is redirected
to a page that reads the value back, and sees the old value, or no value at
all, immediately after saving. Cause, the write landed on the primary and the
very next read was routed to a replica that had not yet applied that write,
because the router's default policy sends all reads to replicas without
regard to whether the same session just wrote the data it is about to read.
Fix, route reads that immediately follow a write from the same session to the
primary for a bounded window, or route them to a replica only once that
replica's applied offset is confirmed to be at or past the offset of the
write, a technique sometimes called a causality token or a sticky session.

Split brain. Symptom, two nodes in the cluster each believe themselves to be
the primary and each accepts writes, producing two diverging histories of the
same data set that cannot be automatically reconciled. Cause, a network
partition separates the primary from the failover coordinator and the
replicas, the coordinator promotes a replica because it cannot reach the
primary, and the original primary, still healthy on its own side of the
partition, continues accepting writes because nothing told it to stop. Fix, a
correctly implemented failover coordinator uses a distributed lock with a
lease or fencing token, so that only the node currently holding the lease may
serve writes, and the old primary is fenced, its writes are physically
rejected by storage or network, not merely asked politely to stop, the moment
a new primary is promoted. This is precisely the job a tool like Patroni,
backed by etcd, Consul, or ZooKeeper, exists to do reliably.

Cascading load collapse. Symptom, one replica falls behind, then falls
further behind, and the lag keeps growing instead of recovering even after
write volume returns to normal. Cause, a replica applying changes is itself
doing write I/O to its own storage, and if that replica's disk or CPU is
undersized relative to the write volume it must replay, it cannot keep pace.
Once behind, it may also be serving a growing backlog of read queries against
increasingly stale, and on some engines increasingly large in memory diff,
state, compounding the problem. Fix, size replicas for the sustained write
rate, not merely for read query volume, and alert on lag trend rather than a
single lag threshold, so a replica that is falling behind faster than it is
catching up is caught before it becomes unusable.

Replica used as a load bearing dependency for correctness sensitive reads.
Symptom, a financial balance, an inventory count, or a permission check reads
stale data from a replica and the application acts on it as if it were
current, producing a double spend, an oversold item, or a stale permission
grant. Cause, the routing policy treats all reads as interchangeable and does
not distinguish reads where staleness is harmless from reads where staleness
is a correctness bug. Fix, classify read paths explicitly, the router
participant from dimension 5 should encode this classification, and force
correctness critical reads to the primary regardless of the general routing
policy, even though this sacrifices some of the scaling benefit for that
specific path.

Writable replica drift. Symptom, data present on a replica is absent, or
different, on the primary, and the divergence grows over time. Cause, an
engine that technically permits writes to a replica, Redis explicitly still
allows this for legacy reasons, is written to directly, and those writes are
local to the replica and never propagated upstream. The Redis documentation
itself warns "Using writable replicas can result in inconsistency between
the master and the replica, so it is not recommended to use writable
replicas"
(https://redis.io/docs/latest/operate/oss_and_stack/management/replication/,
verified 2026-08-02). Fix, enforce read-only at the replica configuration
level wherever the engine supports it, Redis's replica-read-only, on by
default since Redis 2.6, and treat any code path that manages to write to a
replica as a bug, not a feature.

## 12. Trade-off matrix

| Force | Primary-Replica | Sharding / Partitioning | Cache-aside (in front of a single DB) |
|---|---|---|---|
| Read scaling | Linear with replica count, strongly consistent for a primary read, stale for a replica read | Linear with shard count, but only for reads scoped to one shard's key range | Very high for cache hits, but introduces a second source of truth to invalidate |
| Write scaling | None, all writes still serialize through one primary | Linear with shard count, because each shard has its own independent write path | None, writes still go through the single database |
| Consistency model | Eventually consistent on replica reads, strongly consistent on primary reads | Strongly consistent within a shard, no built-in cross-shard consistency | Explicitly stale until invalidated or expired, staleness window is a design choice not a side effect |
| Operational cost | Moderate, N extra full-size nodes plus a failover coordinator | High, requires a shard key strategy, resharding tooling, and cross-shard query handling | Low to moderate, one more system, the cache, to run and invalidate correctly |
| Failure isolation | A failed replica loses no data, the primary is authoritative. A failed primary is a real incident until failover completes | A failed shard is a partial outage scoped to the keys on that shard | A failed cache degrades to database load, not data loss |
| Best fit | Read-heavy workload, moderate write volume, tolerance for milliseconds to seconds of staleness on non-critical reads | Write volume or data volume exceeds what any single primary can hold or absorb | Read pattern is highly skewed toward a small hot set of keys and staleness can be bounded by a short TTL |

## 13. Related and incompatible patterns

Sharding and Partitioning is the pattern reached for when the bottleneck is
write throughput or total data volume rather than read throughput, and the
two compose directly in large systems. Each shard is itself commonly
implemented as its own primary with its own set of replicas, so a large scale
system frequently runs both patterns simultaneously, sharding for write and
storage scale, replication within each shard for read scale and
availability.

CQRS, Command Query Responsibility Segregation, generalizes the same
underlying idea, separate the write path from the read path, but does so at
the model and schema level rather than at the infrastructure level. A CQRS
system's read model is very often backed by a Primary-Replica setup, or by an
entirely different storage engine optimized for reads, making CQRS a
superset use case that Primary-Replica frequently serves as the physical
implementation of.

Event Sourcing produces exactly the kind of ordered, replayable change log
that a replica consumes, and a system built around event sourcing can use its
own event stream as the replication mechanism between a write optimized
store and one or more read optimized projections, making the boundary
between an event sourced read model and a database replica more a matter of
framing than of mechanism.

Circuit Breaker composes defensively on top of Primary-Replica. A router that
has detected a replica returning errors, or lagging past an acceptable
threshold, should trip a circuit for that specific replica and route around
it rather than continuing to send traffic to a node that cannot reliably
answer, which prevents one degraded replica from degrading the whole read
path.

Saga is largely orthogonal, since it addresses distributed transactions
across independently owned services rather than replication within one data
store, but a saga step that reads from a service backed by a lagging replica
can itself become a source of the read after write bug described in
dimension 11, so the two patterns interact at the boundary even though
neither depends on the other.

Multi-primary replication is worth naming as the pattern this one is most
often confused with and is functionally incompatible with the single
ordering guarantee that defines Primary-Replica. A system that needs writes
accepted at more than one node concurrently has left this pattern's problem
space and entered conflict resolution and eventual consistency territory
that Primary-Replica, by design, sidesteps.

## 14. Refactoring path in and out

Introducing the pattern into a system that currently runs a single database
instance proceeds in stages, and skipping stages is the most common source of
production incidents during this migration. First, provision a replica and
let it catch up fully before sending it any traffic. Every mainstream engine
exposes a lag metric, seconds behind source in MySQL, replication lag in
PostgreSQL's pg_stat_replication, MongoDB's replication lag in
rs.printSecondaryReplicationInfo, and the migration should not proceed until
that metric has been stably near zero, not merely observed once. Second,
route a single, low risk, tolerant read path to the replica, for example a
public listing page rather than an authenticated account page, and monitor
it in production before expanding further. Third, build or adopt the routing
layer explicitly rather than scattering the primary versus replica decision
through hand written conditionals across the codebase. A centralized router
is what makes the next stages tractable and what makes dimension 11's
failure modes fixable in one place instead of many. Fourth, classify every
remaining read path by its tolerance for staleness and move each one
deliberately, correctness critical paths staying on the primary
indefinitely, tolerant paths moving to replicas. Fifth, and only once
routing is stable and observed in production, set up and rehearse the
failover procedure, because an untested failover procedure is worse than no
failover procedure. It creates false confidence that evaporates during the
one moment it is actually needed.

Removing the pattern, which happens less often but does happen, typically
follows a system outgrowing read replication as the right lever, most
commonly because the write volume has grown to the point where sharding is
now the binding constraint, and the operational cost of maintaining replicas
for a read scaling benefit that the new architecture no longer needs, because
sharding itself distributes read load across shards, outweighs their value.
The path out is the reverse of the path in. First shrink the classified read
paths back toward the primary or toward the new architecture's own read
path, then decommission replicas one at a time while watching the primary's
load to confirm capacity is not actually still needed, then remove the
failover coordinator only once whatever replaced it, for example a managed
multi node cluster in a sharded architecture, has taken over that
responsibility.

## 15. Testing and verification

Unit tests for application code that uses this pattern should treat the
router as an injectable dependency, so the read and write routing decision
can be asserted directly without standing up real replicated infrastructure.
A test asserts that a write call is routed to the primary connection and
that a tagged tolerant read is routed to a replica connection, using two
distinct fake or mock connection objects.

Integration tests should run against a real, minimal replication topology,
one primary and one replica, either in a container based test environment or
against a local install of the actual database engine, and should
deliberately exercise the lag window rather than assuming it away. Write a
value, immediately read it from the replica connection before that specific
replica has had time to apply the change, and assert the application's
behavior in that gap is the intended behavior, either it correctly reads
stale data on a tolerant path, or it correctly redirected to the primary on
a critical path. A test suite that only ever writes and reads with an
artificial delay in between never exercises the actual bug this pattern is
prone to.

Failover should be tested with a chaos style exercise, not merely reviewed
on paper. In a staging environment, kill the primary process outright and
measure, with real timestamps, how long the system took to detect the
failure, promote a replica, and resume accepting writes, then compare that
measured number against the availability target the pattern was adopted to
meet. A failover runbook that has never been executed against a real failure
is a hypothesis, not a verified capability.

Consistency assertions belong in the test suite for any read path explicitly
classified as correctness critical (dimension 11). A test should assert that
reading that specific path always returns data from the primary connection,
never a replica connection, which functions as a regression test against a
future refactor accidentally loosening the routing rule for that path.

## 16. Observability signals

Replication lag, measured per replica and reported both as an instantaneous
value and as a trend over a rolling window, is the single most important
signal this pattern produces and the one every mainstream engine exposes
natively, MySQL's Seconds_Behind_Source, PostgreSQL's
pg_stat_replication.replay_lag, MongoDB's oplog window. A healthy replica
shows lag in the low single digit milliseconds under normal load and a lag
value that returns to near zero shortly after any write burst. A failing
replica shows lag that is trending upward over time rather than merely
spiking and recovering, which is the leading indicator of the cascading load
collapse failure mode from dimension 11, and this trend should be alerted on
before the absolute lag value crosses a hard threshold.

Read and write split ratio per route, tracked as a metric on the router
itself, shows what fraction of traffic on each logical read path is actually
landing on the primary versus a replica. An unexpected shift, for example a
previously replica served path suddenly showing all traffic on the primary,
is a strong signal that either a replica has been circuit broken out or the
routing configuration has regressed.

Failover events, each one logged as a discrete, timestamped, alertable
occurrence with the identity of the demoted node and the identity of the
promoted node, are what make a postmortem possible after an incident. A
system that cannot answer which node was primary at a given time cannot
reliably investigate a data inconsistency reported by a customer around that
time.

Per replica error rate and query latency, tracked separately per replica
rather than aggregated across the fleet, surfaces a single degraded node
before it degrades the aggregate metric enough to trigger a fleet wide
alert. This is the signal a circuit breaker sitting in front of the replica
pool should consume directly.

A healthy dashboard for this pattern shows, at a glance, every replica's lag
near zero and flat, the read and write split matching the configured
routing policy, zero unplanned failover events, and per replica error rates
within normal variance of each other. A dashboard in trouble shows one
replica's lag climbing while its siblings stay flat, a read path's traffic
shifting toward the primary without a corresponding deploy, or any failover
event outside a planned maintenance window.

## 17. Security and privacy implications

Replication traffic between primary and replica carries the full data set in
transit and must be encrypted. An unencrypted replication link is a
plaintext copy of every row in the database moving across the network on
every write, and any engine's default configuration should be checked rather
than assumed, since some defaults, particularly in self hosted, non managed
deployments, do not enable transport encryption out of the box. A replica
that is geographically distributed, which is one of this pattern's named
benefits (dimension 4), can also move regulated data across a jurisdictional
boundary as an unintended side effect of a routing decision made purely for
latency, which is a data residency and compliance concern that a purely
performance driven replica placement decision can silently violate. Placing
a replica in a new region is a decision that should involve whoever owns
data residency compliance, not only whoever owns database performance.

A replica that serves reads is a second copy of the entire access surface.
An authentication or authorization bug that is fixed on the primary's query
path but not mirrored in the replica's query path, for example a row level
security policy applied at the application layer rather than the database
layer, and applied inconsistently between the two code paths, leaves the
replica as an unprotected side door to the same data the primary correctly
guards. Redis's own documentation flags a specific instance of this concern
for its read-only replicas. "Read-only replicas will reject all write
commands... This does not mean that the feature is intended to expose a
replica instance to the internet or more generally to a network where
untrusted clients exist, because administrative commands like DEBUG or
CONFIG are still enabled"
(https://redis.io/docs/latest/operate/oss_and_stack/management/replication/,
verified 2026-08-02). Read-only at the data level is not the same guarantee
as safe to expose, and a replica needs the same network isolation and access
controls as the primary, not a lesser set on the theory that it merely serves
reads.

A promoted replica inherits every credential, certificate, and access grant
the failover procedure assigns to the primary role, and a failover process
that is not carefully specified can accidentally promote a node that was
provisioned with weaker access controls than the original primary, silently
downgrading the security posture of the write path at the exact moment the
system is already in a degraded, higher risk state.

## 18. References

1. Gray, Jim and Reuter, Andreas. *Transaction Processing. Concepts and
   Techniques*, Morgan Kaufmann, 1993, chapter 12.

2. MySQL 8.4 Reference Manual, Chapter 19, Replication.
   https://dev.mysql.com/doc/refman/8.4/en/replication.html, verified
   2026-08-02.

3. PostgreSQL 18 Documentation, Chapter 26.2, Log-Shipping Standby Servers,
   including section 26.2.5 Streaming Replication and section 26.2.8.
   https://www.postgresql.org/docs/current/warm-standby.html, verified
   2026-08-02.

4. MongoDB Manual, Replication.
   https://www.mongodb.com/docs/manual/replication/, verified 2026-08-02.

5. Amazon Web Services, Amazon RDS User Guide, Working with DB instance read
   replicas.
   https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ReadRepl.html,
   verified 2026-08-02.

6. Redis Documentation, Redis replication.
   https://redis.io/docs/latest/operate/oss_and_stack/management/replication/,
   verified 2026-08-02.

7. Patroni GitHub repository, project description and README.
   https://github.com/patroni/patroni, verified 2026-08-02.

## Code examples

Every sample implements the same shape. A router that inspects whether an
operation is a write or a tolerant read, and directs it to the primary or to
one of a pool of replicas, tracking a simple lag based health check so a
replica that has fallen too far behind is excluded from the pool. This
mirrors dimension 14's advice to centralize the routing decision rather than
scatter it. Each sample is a standalone, dependency-free simulation, not a
driver for a real database, since the pattern itself is the routing and
consistency logic, not any one engine's wire protocol.

### Python

```python
import random
from dataclasses import dataclass, field


@dataclass
class Node:
    name: str
    is_primary: bool
    data: dict = field(default_factory=dict)
    last_applied_offset: int = 0


class PrimaryReplicaRouter:
    def __init__(self, primary: Node, replicas: list[Node], max_lag_offset: int = 5):
        self.primary = primary
        self.replicas = replicas
        self.max_lag_offset = max_lag_offset
        self.write_offset = 0

    def write(self, key: str, value: str) -> int:
        self.write_offset += 1
        self.primary.data[key] = value
        self.primary.last_applied_offset = self.write_offset
        return self.write_offset

    def replicate(self, replica: Node, up_to_offset: int) -> None:
        if replica.last_applied_offset < up_to_offset:
            replica.data.update(self.primary.data)
            replica.last_applied_offset = up_to_offset

    def healthy_replicas(self) -> list[Node]:
        lag = [self.write_offset - r.last_applied_offset for r in self.replicas]
        return [r for r, l in zip(self.replicas, lag) if l <= self.max_lag_offset]

    def read(self, key: str, *, must_be_fresh: bool = False) -> str | None:
        if must_be_fresh:
            return self.primary.data.get(key)
        candidates = self.healthy_replicas()
        if not candidates:
            return self.primary.data.get(key)
        return random.choice(candidates).data.get(key)


def demo() -> None:
    primary = Node(name="primary", is_primary=True)
    replicas = [Node(name="replica-a", is_primary=False),
                Node(name="replica-b", is_primary=False)]
    router = PrimaryReplicaRouter(primary, replicas)

    offset = router.write("balance:user-1", "100")
    assert router.read("balance:user-1", must_be_fresh=True) == "100"

    router.replicate(replicas[0], offset)
    assert router.read("balance:user-1") is not None

    router.write("balance:user-1", "150")
    stale = replicas[0].data.get("balance:user-1")
    assert stale == "100", "replica has not yet caught up, this is the lag window"

    router.replicate(replicas[0], router.write_offset)
    router.replicate(replicas[1], router.write_offset)
    assert router.read("balance:user-1", must_be_fresh=True) == "150"


if __name__ == "__main__":
    demo()
    print("primary-replica python demo: all assertions passed")
```

### TypeScript

```typescript
interface Node {
  name: string;
  isPrimary: boolean;
  data: Map<string, string>;
  lastAppliedOffset: number;
}

function makeNode(name: string, isPrimary: boolean): Node {
  return { name, isPrimary, data: new Map(), lastAppliedOffset: 0 };
}

class PrimaryReplicaRouter {
  private writeOffset = 0;

  constructor(
    private primary: Node,
    private replicas: Node[],
    private maxLagOffset: number = 5
  ) {}

  write(key: string, value: string): number {
    this.writeOffset += 1;
    this.primary.data.set(key, value);
    this.primary.lastAppliedOffset = this.writeOffset;
    return this.writeOffset;
  }

  replicate(replica: Node, upToOffset: number): void {
    if (replica.lastAppliedOffset < upToOffset) {
      for (const [k, v] of this.primary.data) {
        replica.data.set(k, v);
      }
      replica.lastAppliedOffset = upToOffset;
    }
  }

  healthyReplicas(): Node[] {
    return this.replicas.filter(
      (r) => this.writeOffset - r.lastAppliedOffset <= this.maxLagOffset
    );
  }

  read(key: string, mustBeFresh = false): string | undefined {
    if (mustBeFresh) {
      return this.primary.data.get(key);
    }
    const candidates = this.healthyReplicas();
    if (candidates.length === 0) {
      return this.primary.data.get(key);
    }
    const pick = candidates[Math.floor(Math.random() * candidates.length)];
    return pick.data.get(key);
  }

  currentWriteOffset(): number {
    return this.writeOffset;
  }
}

function assertEqual<T>(actual: T, expected: T, message: string): void {
  if (actual !== expected) {
    throw new Error(`${message}, expected ${expected}, got ${actual}`);
  }
}

function demo(): void {
  const primary = makeNode("primary", true);
  const replicaA = makeNode("replica-a", false);
  const replicaB = makeNode("replica-b", false);
  const router = new PrimaryReplicaRouter(primary, [replicaA, replicaB]);

  const offset1 = router.write("balance:user-1", "100");
  assertEqual(router.read("balance:user-1", true), "100", "primary read must be fresh");

  router.replicate(replicaA, offset1);
  assertEqual(router.read("balance:user-1"), "100", "replica should have caught up");

  router.write("balance:user-1", "150");
  assertEqual(
    replicaA.data.get("balance:user-1"),
    "100",
    "replica has not yet applied the second write, this is the lag window"
  );

  router.replicate(replicaA, router.currentWriteOffset());
  router.replicate(replicaB, router.currentWriteOffset());
  assertEqual(router.read("balance:user-1", true), "150", "primary must show latest write");

  console.log("primary-replica typescript demo: all assertions passed");
}

demo();
```

### Go

```go
package main

import (
	"fmt"
	"math/rand"
)

type Node struct {
	Name              string
	IsPrimary         bool
	Data              map[string]string
	LastAppliedOffset int
}

func NewNode(name string, isPrimary bool) *Node {
	return &Node{Name: name, IsPrimary: isPrimary, Data: make(map[string]string)}
}

type Router struct {
	Primary     *Node
	Replicas    []*Node
	MaxLag      int
	WriteOffset int
}

func NewRouter(primary *Node, replicas []*Node) *Router {
	return &Router{Primary: primary, Replicas: replicas, MaxLag: 5}
}

func (r *Router) Write(key, value string) int {
	r.WriteOffset++
	r.Primary.Data[key] = value
	r.Primary.LastAppliedOffset = r.WriteOffset
	return r.WriteOffset
}

func (r *Router) Replicate(replica *Node, upToOffset int) {
	if replica.LastAppliedOffset < upToOffset {
		for k, v := range r.Primary.Data {
			replica.Data[k] = v
		}
		replica.LastAppliedOffset = upToOffset
	}
}

func (r *Router) HealthyReplicas() []*Node {
	var healthy []*Node
	for _, rep := range r.Replicas {
		if r.WriteOffset-rep.LastAppliedOffset <= r.MaxLag {
			healthy = append(healthy, rep)
		}
	}
	return healthy
}

func (r *Router) Read(key string, mustBeFresh bool) (string, bool) {
	if mustBeFresh {
		v, ok := r.Primary.Data[key]
		return v, ok
	}
	candidates := r.HealthyReplicas()
	if len(candidates) == 0 {
		v, ok := r.Primary.Data[key]
		return v, ok
	}
	pick := candidates[rand.Intn(len(candidates))]
	v, ok := pick.Data[key]
	return v, ok
}

func must(cond bool, msg string) {
	if !cond {
		panic(msg)
	}
}

func main() {
	primary := NewNode("primary", true)
	replicaA := NewNode("replica-a", false)
	replicaB := NewNode("replica-b", false)
	router := NewRouter(primary, []*Node{replicaA, replicaB})

	offset := router.Write("balance:user-1", "100")
	v, _ := router.Read("balance:user-1", true)
	must(v == "100", "primary read must be fresh")

	router.Replicate(replicaA, offset)
	v, ok := router.Read("balance:user-1", false)
	must(ok && v == "100", "replica should have caught up")

	router.Write("balance:user-1", "150")
	must(replicaA.Data["balance:user-1"] == "100",
		"replica has not yet applied the second write, this is the lag window")

	router.Replicate(replicaA, router.WriteOffset)
	router.Replicate(replicaB, router.WriteOffset)
	v, _ = router.Read("balance:user-1", true)
	must(v == "150", "primary must show latest write")

	fmt.Println("primary-replica go demo: all assertions passed")
}
```

Java, Rust, and Swift are omitted from the runnable set for this entry
because the routing logic above is not language idiomatic in a way that
differs meaningfully across those three and the three already shown. The
pattern's substance lives in the offset tracking and health check logic,
which translates mechanically. Python, TypeScript, and Go were chosen because
they represent three distinct concurrency and typing models, dynamic
scripting, structurally typed with async support, and statically typed
compiled, which is where a router implementation's real differences show up
in production code.
