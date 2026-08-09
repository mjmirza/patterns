---
name: Shared Nothing
slug: shared-nothing
family: 05-architectural
category: Architectural
aliases: [Shared-Nothing Architecture, SN Architecture, Nothing-Shared Cluster]
first_described: "Stonebraker 1986"
maturity: canonical
related: [sharding, database-per-service, bulkhead, load-balancer, consistent-hashing, event-driven-architecture]
incompatible_with: [distributed-transaction-2pc, shared-database-integration]
verified: 2026-08-02
---

# Shared Nothing

## 1. Name, aliases, and lineage

The canonical name is Shared Nothing, sometimes written Shared-Nothing and
abbreviated SN in database literature. The name was given to the architecture,
not invented alongside it. Michael Stonebraker's short paper, "The Case for
Shared Nothing", presented at the High Performance Transaction Systems
workshop in 1985 and published in *IEEE Database Engineering Bulletin*,
volume 9, issue 1, pages 4 to 9, 1986, named and compared three multiprocessor
database architectures. shared memory, where every processor reads and writes
one central memory and every disk. shared disk, where each processor keeps
private memory but every processor can read and write every disk. and shared
nothing, where each processor owns private memory and a private set of disks,
and processors communicate only by sending messages over an interconnect
([Wikipedia's summary of Stonebraker's taxonomy](https://en.wikipedia.org/wiki/Shared-nothing_architecture),
verified 2026-08-02, citing Stonebraker's 1986 paper by title and venue).
Stonebraker's argument was that shared nothing scaled transaction throughput
linearly as nodes were added, while shared memory and shared disk designs hit
a ceiling on the interconnect or the central memory bus as node count grew.

The architecture itself predates the paper's name. Tandem Computers shipped
the NonStop hardware and software line starting in 1976 as a fault-tolerant,
independently-failing multiprocessor design that is retrospectively described
as an early shared-nothing implementation, and Tandem's NonStop SQL, released
in 1984, is described as the first commercial shared-nothing relational
database. Teradata shipped its DBC/1012 database machine to its first
customer, Wells Fargo Bank, in 1983, built from the start as a shared-nothing
massively parallel processing system, and is commonly credited as the first
commercial shared-nothing database system to ship
([Wikipedia's account of Tandem NonStop and Teradata as early shared-nothing
adopters](https://en.wikipedia.org/wiki/Shared-nothing_architecture), verified
2026-08-02). So Stonebraker's 1986 paper formalized and named a pattern that
industry had already built and shipped, which is a common shape for
architectural pattern lineage. practice runs ahead of the vocabulary that
later organizes it.

No alternative name has displaced Shared Nothing in the four decades since. The
term crossed from database engineering into general distributed systems and
web architecture essentially unchanged, and it is the term this entry uses
throughout. "Nothing-Shared Cluster" appears occasionally in older hardware
literature as an equivalent phrase but never became standard.

## 2. Problem and context

A system needs to handle more work than one machine can handle, whether that
work is transaction throughput, storage volume, or concurrent connections. The
naive answer is a bigger machine. more CPU cores, more RAM, faster disks. This
works until it does not, because a single machine has a ceiling on every axis
at once, and the largest machine money can buy is still one point of failure
and one bottleneck for every request. The next naive answer is several
machines that share a resource. several application servers reading and
writing one central database, several compute nodes attached to one storage
area network, several worker processes on one host reading a shared in-memory
cache by reference. Sharing a resource across machines lets you add compute
without immediately hitting a wall, but the shared resource itself becomes the
new bottleneck and the new single point of failure, and coordinating
concurrent access to it (locks, latches, cache-coherence protocols, distributed
transaction managers) adds a cost that grows with the number of participants,
not with the amount of work.

The problem shared nothing answers is precisely this coordination cost. If two
nodes never touch the same byte of memory or the same block of disk, they
never need a protocol to agree about who owns it right now. Contention
disappears by removing the object of contention, not by managing it more
cleverly. The context in which this matters is any workload that must scale
past the capability, or past the acceptable blast radius, of a single shared
resource. a transaction-processing system approaching the throughput ceiling
of a shared-disk cluster, a web tier serving enough concurrent users that a
single application server's memory cannot hold every session, a key-value
store whose data volume exceeds what any single disk array can hold, or an
organization that wants a failure in one part of the system to never propagate
to another part because they share nothing to propagate through.

The pattern is specifically an architectural answer, meaning it is a decision
about how independent units of the system are deployed and how they are
allowed to communicate, not a decision inside one process about which data
structure to use. It sits at the level of "how many database instances do we
run and does node A ever open a socket to node B's disk", not at the level of
"which collection type prevents a race condition inside one thread".

## 3. Forces

This is engineering judgement about which pressures dominate and which the
pattern trades away, not a sourced claim.

Scalability versus per-node capability. Shared nothing scales by adding
nodes rather than by growing one node, which removes the ceiling that a single
machine's hardware imposes. The trade is that any single node's slice of the
work is bounded by whatever partition it was assigned, so a workload that is
naturally skewed toward one key, one tenant, or one time window can leave one
node saturated while its siblings sit idle. Scalability is close to linear only
when the partitioning scheme actually spreads load evenly.

Fault isolation versus operational surface area. Because no node depends
on another node's memory or disk, one node's crash, disk failure, or garbage
collection pause cannot corrupt or stall a sibling. The trade is that you now
operate N independent things instead of one, each needing its own monitoring,
its own capacity planning, its own failure-recovery path, and its own copy of
whatever software runs on it. Fault isolation is bought with a larger fleet to
keep healthy.

Latency versus cross-partition work. A request that touches exactly one
partition is fast, because it never leaves the node that owns the data it
needs. The trade is that a request needing data from two partitions (a join
across shards, a transaction touching two accounts on different nodes, an
aggregate over the whole dataset) must fan out over the network and wait for
every partition it touched, and the slowest partition sets the latency floor
for the whole request. Shared nothing favors the workload shape where most
requests are single-partition and disfavors the shape where most are not.

Consistency versus availability under partition. With no shared state,
each node can keep serving reads and writes to the data it owns even while it
cannot reach its peers, which favors availability. The trade, as formalized by
Eric Brewer's CAP theorem and its later clarifications, is that a
cross-partition operation cannot get both strong consistency and continued
availability during a network partition. the system must choose which to
sacrifice for that operation while the partition lasts ([Gilbert and Lynch,
"Brewer's Conjecture and the Feasibility of Consistent, Available,
Partition-Tolerant Web Services", ACM SIGACT News, 33(2), 2002](https://users.ece.cmu.edu/~adrian/731-sp04/readings/GL-cap.pdf),
verified 2026-08-02). Shared nothing does not evade this trade-off. it simply
makes the partitioned data explicit and pushes the consistency-versus-
availability decision to the boundary between shards rather than hiding it
inside a shared resource's lock manager.

Cost per unit of scale versus cost of the first unit. Because nodes are
commodity units added incrementally, the marginal cost of the next unit of
capacity is roughly constant, which is favorable at scale. The trade is that
the architecture, the sharding scheme, the routing layer, and the rebalancing
tooling are all fixed costs that must be paid before the first unit of
capacity is delivered, so shared nothing is comparatively expensive to stand
up for a workload that never needs more than one machine's worth of capacity.

Team topology versus a single mental model. Shared nothing composes
naturally with teams that each own a bounded slice of data end to end, because
ownership boundaries in the architecture match ownership boundaries in the
organization. The trade is cognitive. a person debugging a cross-shard
incident, or reasoning about global invariants across the whole dataset, no
longer has one place to look, and must reconstruct a global view from N
independent, potentially inconsistent, local views.

## 4. Applicability and non-applicability

Reach for shared nothing when the workload's growth curve will outrun a
single machine or a single shared resource, when most units of work
(requests, transactions, records) can be routed to exactly one owner without
needing data from elsewhere, when the cost of an isolated node failure taking
down only its own slice of traffic is acceptable and preferable to a
correlated failure of a shared resource taking down everything, when the team
can afford to build or adopt a routing and rebalancing layer, and when the
access pattern is dominated by point lookups or narrow ranges keyed by the
same dimension you would shard on (a user ID, a tenant ID, a geographic
region).

Do not reach for it in the following situations, each with the reason attached.

- The dataset and the traffic both fit comfortably on one well-specified
  machine, now and for the foreseeable future. The coordination cost you
  would eliminate is not costing you anything yet, but the sharding
  infrastructure, the routing layer, and the operational multiplication of N
  independent nodes are real costs you would pay immediately. A single strong
  instance with a hot standby is simpler and cheaper.
- The dominant query shape needs a global view. multi-key joins across
  arbitrary keys, ad hoc analytical aggregates over the whole dataset, or
  transactions that routinely touch data belonging to more than one partition.
  Every one of these becomes a fan-out, a distributed join, or a
  cross-partition transaction protocol on shared nothing, each of which is
  slower and harder to reason about than the equivalent single-node operation.
  A shared-disk or single-node design, or an architecture that keeps
  cross-partition data denormalized locally, usually wins here.
- The team has no mature story for choosing a partition key, and the natural
  key is not evenly distributed. A shard scheme built on a skewed key (one
  enormous tenant, a monotonically increasing timestamp, a small enumeration)
  reproduces the single-bottleneck problem shared nothing exists to remove,
  just on one node inside the cluster instead of on the whole machine.
- Strong, immediate, global consistency across every write is a hard legal
  or safety requirement, and cross-partition writes are common. Distributed
  two-phase commit across shared-nothing nodes is possible but expensive,
  fragile under partition, and reintroduces much of the coordination cost the
  pattern was chosen to avoid. A system with this requirement and this access
  pattern is often better served by a single strongly consistent store, or by
  a design (see dimension 13, incompatible with) that avoids distributed
  transactions structurally rather than executing them.
- The organization cannot staff the operational load of N independently
  monitored, independently upgraded, independently capacity-planned nodes.
  Shared nothing multiplies the number of things that can individually break.
  a team of one or two engineers running a side project usually cannot absorb
  that multiplication and is better served by a managed single-node or
  shared-disk offering.

## 5. Structure

Node (or shard, or partition owner). An independently deployable unit that
owns a disjoint slice of the system's total state, holds it in memory and on
its own local disk, and processes only the requests routed to it. A node never
reads or writes another node's memory or disk directly.

Partitioning function (or shard key, or hash ring). The deterministic
rule, given a piece of work or a piece of data, that decides which node owns
it. Common implementations are a hash of a key modulo the node count, a
consistent-hashing ring, or a directory lookup mapping key ranges to nodes.

Router (or coordinator, or gateway). The component, which may be a
stand-alone proxy, a client-side library, or logic embedded in the caller,
that applies the partitioning function to an incoming request and forwards it
to the owning node. The router itself holds no application state. it may cache
the partition map, but that cache is a copy of routing metadata, never a copy
of application data.

Replica (optional). A node that holds a copy of another node's owned data
for fault tolerance, typically kept in sync by replication rather than by
shared storage. Replicas are still shared-nothing with respect to each other.
each replica's copy lives on its own disk and its own memory, and
synchronization happens by message passing (log shipping, change-data-capture
streams), never by two nodes reading the same physical bytes.

Cross-partition coordinator (only present when cross-partition operations
exist). A component, sometimes a saga orchestrator, sometimes a two-phase
commit coordinator, sometimes a scatter-gather aggregator, that composes a
result or an atomic effect from more than one node's local operations. Its
presence is the clearest sign in the structure that a workload has outgrown
the pure single-partition case shared nothing is optimized for.

## 6. ASCII structure diagram

```
                         +-------------------+
        client request   |      Router        |
        --------------->  |  (partition fn)    |
                         +----------+----------+
                                    |
                +-------------------+-------------------+
                |                   |                   |
                v                   v                   v
        +---------------+   +---------------+   +---------------+
        |    Node A      |   |    Node B      |   |    Node C      |
        |  own memory    |   |  own memory    |   |  own memory    |
        |  own disk      |   |  own disk      |   |  own disk      |
        |  keys [0..k)   |   |  keys [k..2k)  |   |  keys [2k..3k) |
        +-------+-------+   +-------+-------+   +-------+-------+
                |                   |                   |
                v                   v                   v
        +---------------+   +---------------+   +---------------+
        |   Replica A'   |   |   Replica B'   |   |   Replica C'   |
        |  own copy      |   |  own copy      |   |  own copy      |
        +---------------+   +---------------+   +---------------+

  No arrow crosses from one node's box into another node's memory or
  disk. Every cross-node arrow is a message, drawn only where a
  cross-partition operation genuinely requires one.
```

## 7. Dynamics

The common case, a single-partition request, never leaves the node that owns
the data it needs. The uncommon case, a cross-partition request, needs a
fan-out and a merge, and its latency is bounded below by the slowest
participating node.

```
Single-partition write (the fast path, the common case):

  Client        Router          Node B (owner of key "user:42")
    |              |                    |
    | write(key,v) |                    |
    |------------->|                    |
    |              | hash(key) -> B     |
    |              |------------------->|
    |              |                    | apply locally, ack
    |              |<-------------------|
    |<-------------|                    |
    | ack          |                    |

Cross-partition read, fan-out and merge (the slow path):

  Client        Router      Node A      Node B      Node C
    |              |            |           |           |
    | aggregate()  |            |           |           |
    |------------->|            |           |           |
    |              | fan out to all owning nodes         |
    |              |----------->|           |           |
    |              |----------------------->|           |
    |              |------------------------------------->|
    |              |            | local     | local     | local
    |              |            | partial   | partial   | partial
    |              |<-----------|           |           |
    |              |<-----------------------|           |
    |              |<-------------------------------------|
    |              | merge partial results               |
    |<-------------| (latency = slowest of A, B, C)       |
```

The merge step is exactly where shared nothing's cost surfaces. correctness
of the merged answer now depends on the router correctly combining partial
results, and the perceived latency is the maximum, not the average, across
every node that had to answer.

## 8. Implementation variants

Hash sharding. The partitioning function is a hash of a key, taken modulo
the node count. Simple to implement and gives an even distribution for keys
with good entropy, but adding or removing a node forces most keys to be
remapped unless combined with consistent hashing.

Consistent hashing. Nodes and keys are placed on a common hash ring. a key
is owned by the next node clockwise from its hash position. Adding or removing
one node only reshuffles the keys adjacent to it on the ring, not the whole
keyspace, which is why it is the standard choice for systems that expect the
node count to change over time ([Karger et al., "Consistent Hashing and Random
Trees", Proceedings of the 29th Annual ACM Symposium on Theory of Computing,
1997](https://dblp.org/rec/conf/stoc/KargerLLPLL97.html),
verified 2026-08-05, describing the original consistent-hashing construction
built for Akamai's distributed web cache).

Directory-based range sharding. A separate, small, highly available
metadata service maps key ranges to owning nodes explicitly, rather than
deriving ownership from a hash. This makes range scans over ordered keys
efficient and makes rebalancing an explicit, controlled operation (move this
range from node A to node B), at the cost of the directory service itself
becoming a component that must stay correct and available.

Stateless-tier sharing nothing at the application layer, stateful tier
sharing nothing at the storage layer. A very common real-world composite.
web or API servers behind a load balancer hold no session state locally (each
request can land on any server), while the database tier underneath is
explicitly sharded by a tenant or user key. The two layers are shared nothing
for different reasons. the application tier because it holds nothing worth
sharing, the storage tier because sharing would bottleneck it.

Database-per-service. In a microservices decomposition, each service
owns its own database schema and no other service is permitted to query it
directly. all cross-service reads go through the owning service's API. This is
shared nothing at the level of bounded contexts rather than at the level of
physical hash partitions, and it is the variant most likely to appear in a
system that never explicitly talks about "sharding" at all.

Language-idiomatic notes. In Go, the pattern is commonly realized with one
goroutine per shard, each owning an unshared map or struct, communicating only
through channels, which structurally prevents another goroutine from touching
that shard's memory without going through the channel (demonstrated in the Go
example below). In Rust, the equivalent shape uses one OS thread per shard
with an mpsc channel as the only way in, so the borrow checker enforces that
the shard's HashMap is never simultaneously reachable from two threads. In
languages without cheap concurrency primitives per shard (a request-per-process
PHP or Python deployment, for instance), shared nothing is usually realized
entirely at the process or container level. each worker process is a shard, or
each container is a node, and the language runtime does not need to express
the isolation at all because the operating system's process boundary already
provides it.

## 9. Known production uses

Apache Cassandra. Cassandra is documented as a wide-column store built on
"full multi-primary database replication" with data partitioned across nodes
by a partition key and no distinguished master node, and the project's own
architecture documentation frames peer nodes as symmetric participants in a
ring rather than as clients of a shared resource
([Apache Cassandra documentation, "Architecture overview", cassandra.apache.org](https://cassandra.apache.org/doc/latest/cassandra/architecture/overview.html),
verified 2026-08-02). Every node in a Cassandra ring owns its own disk and
memory for the token ranges assigned to it. there is no shared disk array and
no single coordinator node that every write must pass through.

Amazon Dynamo, and the systems it inspired. The 2007 paper "Dynamo.
Amazon's Highly Available Key-value Store", by Giuseppe DeCandia and
co-authors, presented at the ACM Symposium on Operating Systems Principles
(SOSP) 2007, describes a key-value store used by several of Amazon's core
services that partitions and replicates data by consistent hashing across
independent nodes, explicitly favoring availability over strict consistency
under network partition ([DeCandia et al., "Dynamo. Amazon's Highly Available
Key-value Store", SOSP 2007, ACM](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf),
verified 2026-08-02). The paper is widely cited as the design blueprint that
influenced later shared-nothing key-value and wide-column stores, including
Cassandra and Riak.

Vitess at YouTube. Vitess was built at YouTube starting in 2010 and open
sourced in 2011 to let a MySQL-backed service scale past the limits of a
single instance by sharding data across many independent MySQL instances, each
holding its own slice of the keyspace, with a proxy layer (VTGate) routing
each query to the shard that owns the relevant rows
([ByteByteGo, "How YouTube Supports Billions of Users with MySQL and Vitess",
blog.bytebytego.com](https://blog.bytebytego.com/p/how-youtube-supports-billions-of),
verified 2026-08-02). Vitess is now a CNCF graduated project and is used
beyond YouTube by companies including Slack, Pinterest, and Square for the
same reason. MySQL itself has no native shared-nothing partitioning, so Vitess
supplies the sharding and routing layer on top of independent, unshared MySQL
instances.

Teradata. Teradata's DBC/1012, first shipped to a customer in 1983,
predates Stonebraker's naming paper and is widely credited as the first
commercial shared-nothing database system, built as a massively parallel
processing machine in which each node (an "Access Module Processor") owns its
own memory and disk and communicates with other nodes only over a dedicated
interconnect ([Stacksync, "Named Thirteen Years Before the Technology
Existed. The Origin Story of Teradata"](https://www.stacksync.com/blog/named-thirteen-years-before-the-technology-existed-the-origin-story-of-teradata),
verified 2026-08-02). Teradata's shared-nothing MPP architecture remains the
foundation of its data-warehousing product line.

## 10. Consequences

Positive.

- Adding capacity is adding nodes, so throughput and storage headroom scale
  roughly linearly with the size of the fleet, up to the point where
  cross-partition coordination overhead starts to dominate.
- A single node's crash, disk failure, memory exhaustion, or garbage-collection
  pause is contained to the slice of traffic and data that node owned. the
  rest of the cluster keeps serving.
- There is no shared lock manager, no cache-coherence protocol, and no
  contention on a central resource to reason about for single-partition
  operations, which removes an entire class of concurrency bugs from that
  code path.
- Nodes can be commodity hardware rather than one exceptionally large and
  exceptionally expensive machine, and can be added incrementally as demand
  grows rather than provisioned all at once.

Negative.

- Any operation that needs data owned by more than one node pays a network
  round trip per node involved, and its latency is bounded by the slowest
  participant, which is strictly worse than the equivalent single-node
  operation.
- Global invariants (a unique constraint across the whole dataset, a
  cross-shard foreign key, an exactly-once counter) are hard to enforce
  without a distributed transaction protocol or a redesign that avoids the
  invariant crossing a shard boundary.
- Operational complexity multiplies by the node count. monitoring, deployment,
  capacity planning, backup, and incident response all now happen N times
  instead of once, and a skilled team must build or adopt tooling that treats
  the fleet as one logical unit despite its physical partitioning.
- A poorly chosen partition key produces a hot shard, and because shared
  nothing has no mechanism to spill an overloaded node's excess work onto an
  idle sibling automatically, a hot shard degrades exactly like the single
  bottleneck the architecture was adopted to avoid.
- Rebalancing (moving data between nodes as the cluster grows or shrinks) is
  itself a nontrivial distributed operation that must be designed, tested, and
  operated correctly, or the cluster accumulates skew over time even if the
  initial partitioning was even.

## 11. Failure modes and misuse

This dimension draws on engineering experience alongside the sourced claims
above. symptoms are what an operator would actually observe.

Hot partition. Symptom. one node consistently shows far higher CPU,
memory, or queue depth than its siblings, and requests to keys owned by that
node have visibly higher latency than requests to any other key, while the
rest of the cluster sits comfortably under capacity. Cause. the partition key
does not distribute load evenly, often because it correlates with something
skewed in the real world (one dominant tenant, a celebrity user, a
monotonically increasing key like a timestamp that concentrates all recent
writes on the last shard). Fix. choose a partition key with better entropy for
the actual traffic distribution, or split the hot range into smaller ranges
and redistribute them, or add a secondary dimension (composite key) that
breaks up the concentration.

Fan-out amplification. Symptom. a small number of logically simple
requests (a dashboard query, a report) generate an outsized amount of internal
network traffic and put pressure on every node in the cluster simultaneously,
even though the cluster's total data volume did not change. Cause. a query
pattern that needs data from every partition was added to the workload after
the system was designed for point lookups, so every "simple" client request
becomes an all-nodes scatter-gather. Fix. denormalize the frequently-needed
cross-partition view into its own shared-nothing partitioned structure ahead
of time (a materialized view keyed appropriately), route the expensive query
to a separate analytical system, or accept and provision explicitly for the
fan-out cost rather than discovering it under load.

Split-brain during rebalancing. Symptom. the same key briefly appears to
be owned by two different nodes, and writes to it during the window are
inconsistently visible depending on which node answers the read, sometimes
surfacing as data that "disappears" after a rebalance completes. Cause. the
routing metadata (partition map, ring position) was updated on some nodes or
some routers before others, so two callers using stale and fresh maps
disagree about ownership during the transition. Fix. make ownership changes go
through a single source of truth that all routers read from atomically (a
consensus-backed metadata store), and make the handoff protocol between old
and new owner explicit (drain and confirm before advertising the new owner)
rather than relying on all routers updating simultaneously.

Distributed transaction creep. Symptom. latency for a specific operation
grows steadily worse over months, and profiling shows most of the time spent
waiting on a coordinator protocol (two-phase commit prepare and commit phases)
across nodes rather than on any single node's local work. the team also
reports the operation "sometimes hangs" under partial node failure. Cause. an
originally single-partition operation accreted cross-partition requirements
over time (a feature now touches two tenants' data, a workflow now spans two
services' databases) and someone bolted on a distributed transaction rather
than redesigning the partitioning. Fix. either move the operation's data so it
lives on one partition again (denormalize, or change the sharding key), or
replace the distributed transaction with a saga that achieves eventual
consistency through compensating actions instead of blocking two-phase commit.

Treating "shared nothing" as "no coordination anywhere". Symptom. two
independent teams each build a feature that needs to enforce a rule spanning
both of their shards (a global uniqueness constraint, a total-count invariant),
each assumes the other's shard will independently enforce it, and the
constraint is silently violated in production because no single component
ever actually checked it. Cause. shared nothing removes shared mutable state,
not the need for cross-cutting invariants. a team can mistake "no shared
database" for "no cross-cutting business rules" and simply drop the
enforcement of any rule that would have required coordination. Fix. identify
every invariant that genuinely spans partitions during design, and assign it
explicitly to a coordinator, a saga, or a redesign that moves the data so the
invariant becomes local. never leave it unassigned on the assumption that
"someone" enforces it.

## 12. Trade-off matrix

Comparison across the forces named in dimension 3, against named alternative
architectures.

| Force | Shared Nothing | Shared Disk (for example, Oracle RAC) | Shared Memory (single large SMP machine) | Single-node with hot standby |
|---|---|---|---|---|
| Scale ceiling | Scales by adding nodes, close to linear for single-partition workloads | Scales compute independently of storage, but the shared storage fabric and its cache-coherence traffic become the ceiling | Bounded by the largest machine available and by memory-bus contention as core count grows | Bounded by one machine's capability, failover adds availability, not capacity |
| Fault isolation | High. One node's failure affects only its own partition | Moderate. Compute node failure is isolated, but the shared storage layer is a common dependency all nodes rely on | Low. A hardware fault in the shared machine can affect the whole workload | Moderate. Standby limits downtime but the active node is still one unit of failure at a time |
| Cross-partition operation cost | High. Requires network fan-out and merge, latency bounded by slowest participant | Lower. Any node can read any data from shared storage without messaging peer nodes | Lowest. Any thread can access any memory location directly | Not applicable, there is only one partition |
| Operational complexity | High. N independently monitored, deployed, and capacity-planned units | Moderate. Compute nodes are simpler to add, but the shared storage fabric needs its own expert operation | Low day to day, but vertical hardware procurement and vendor lock-in are real costs | Low. One primary configuration to reason about, plus one failover path |
| Cost profile | Roughly linear marginal cost per unit of added capacity, high fixed cost to stand up | Storage hardware (SAN, cache-coherence fabric) is expensive and is itself a scaling bottleneck to grow | Very high cost per unit of the largest tier of hardware, and cost grows faster than linearly at the top end | Lowest fixed cost for workloads that never need more than one machine |
| Best-fit access pattern | Point lookups and narrow ranges on the shard key, low cross-partition traffic | Workloads that need flexible, unpredictable cross-node access to the same data (for example ad hoc analytics on shared storage) | Any access pattern, because there is no partitioning at all | Any access pattern that fits on one machine |

## 13. Related and incompatible patterns

Sharding, in the pure data-partitioning sense, is the mechanism most shared
nothing systems use to decide who owns what. shared nothing is the broader
architectural stance (no shared mutable resource across independently
deployed units) and sharding is the concrete technique for realizing it at the
data layer, so the two are frequently discussed as if synonymous even though
shared nothing also covers the stateless application tier where there is
nothing to shard.

Database-per-service, common in microservices decompositions, is shared
nothing applied at the level of a service boundary rather than a physical
partition key. each service's database is a "node" in the shared-nothing
sense, and the rule that no other service may query it directly is the
enforcement mechanism.

Bulkhead composes naturally with shared nothing, because both patterns exist
to contain a failure to the smallest possible blast radius. a shared-nothing
node is itself often the natural bulkhead boundary, since a node's own
resource pool (connections, threads, memory) is already isolated from its
siblings by construction.

Consistent hashing is the specific data-structure technique most
shared-nothing systems use inside their partitioning function to minimize
reshuffling when nodes are added or removed, and is described in detail as an
implementation variant in dimension 8.

Load balancing at the stateless application tier is the shared-nothing pattern
applied to compute rather than to data. any request can land on any server
precisely because no server holds state another server would need, which is
what makes the load balancer's routing decision free to be arbitrary rather
than sticky.

Event-driven architecture is a common companion for the cross-partition
coordination that pure shared nothing struggles with directly. rather than a
synchronous fan-out and merge across shards, an event stream lets one shard
publish a fact and another shard consume it asynchronously, trading immediate
consistency for decoupling that still respects each shard's ownership of its
own state.

Incompatible with two-phase-commit-style distributed transactions used as the
default coordination mechanism across shared-nothing nodes. two-phase commit
reintroduces exactly the blocking, coordinator-dependent coupling shared
nothing was adopted to avoid, and a system that leans on it for routine,
frequent cross-shard writes has effectively rebuilt a shared-resource
bottleneck out of a network protocol instead of out of a physical disk.
Incompatible, in the ordinary sense of the word rather than as a named
pattern, with any integration approach where multiple independently deployed
services read and write one shared database schema directly, because that
schema is precisely the shared mutable resource shared nothing exists to
eliminate.

## 14. Refactoring path in and out

Introducing shared nothing into a system that currently runs on one instance,
or on a shared-disk cluster, follows a sequence that keeps the system running
throughout.

1. Identify the dominant access pattern and the natural partition key. the
   dimension along which most requests already group naturally (tenant ID,
   user ID, geographic region). If no such dimension exists, shared nothing is
   the wrong next step. revisit dimension 4's non-applicability list first.
2. Introduce a routing layer in front of the existing single instance, even
   before any data is physically split, so every caller already goes through
   the router. This decouples "how a caller finds its data" from "how many
   physical nodes hold the data", and it is the seam the rest of the migration
   will use.
3. Split the schema, or the keyspace, along the chosen partition key into a
   small number of logical partitions, still colocated on the same physical
   instance if necessary, and confirm every query the application issues stays
   within one partition. Any query that spans partitions at this stage is a
   signal to fix the access pattern or denormalize before physically
   splitting anything.
4. Move partitions onto physically separate nodes one at a time, using
   dual-write or change-data-capture replication to keep the old and new
   locations in sync during the cutover window, and switch the router to the
   new node only after the new node has caught up and been verified.
5. Build or adopt rebalancing tooling before the first rebalance is actually
   needed under production load, because the naive first attempt at moving
   live data between nodes is where split-brain and data-loss incidents
   originate. test it against a staging cluster with production-shaped skew.
6. Add cross-partition coordination (sagas, scatter-gather aggregation) only
   for the specific operations that were confirmed in step 3 to need it, and
   treat each one as a deliberate, reviewed addition, not a default.

Removing shared nothing, when a system has outgrown the need for it or the
operational cost has become disproportionate to the scale actually required,
follows the reverse sequence. consolidate partitions back onto fewer physical
nodes behind the same router (the router boundary from step 2 makes this safe
to do incrementally), verify no application code depends on the physical
node count rather than on the router's interface, and only remove the router
entirely once the system has been running on a single consolidated instance
long enough to confirm the capacity headroom is real and durable. The router
introduced in step 2 is the single most valuable artifact of the whole
migration in either direction, because it is what makes both "add more nodes"
and "consolidate back to fewer" a configuration change behind a stable
interface rather than a rewrite of every caller.

## 15. Testing and verification

Unit-level testing of a single node's logic is unaffected by the architecture.
a node's local handling of a request, in isolation, is tested exactly as any
non-distributed component would be, using ordinary unit tests against its
local state.

What shared nothing adds is the need to test the partitioning function and the
router independently of any node's business logic. given a set of keys, does
the function distribute them within an acceptable skew tolerance, and does a
change in node count remap the expected proportion of keys rather than all of
them (this specifically verifies a consistent-hashing implementation's core
claim). This is a pure, deterministic function and is cheap to test
exhaustively with generated key distributions, including adversarial ones (all
keys sharing a common prefix, keys following a real production distribution
sampled from logs).

Cross-partition operations need their own test category. given a fan-out
across a fixed number of simulated nodes, does the coordinator correctly merge
partial results, and critically, does it behave correctly when one of the
simulated nodes times out, returns an error, or returns a stale value. A
fan-out that treats "unreachable" the same as "empty" produces silently wrong
aggregates, and that miscoordination is the class of bug most worth
deliberately testing for rather than discovering in production.

Failure injection is the test double this pattern most needs. rather than
mocking a node's response, the test runner should be able to simulate a node
being slow, unreachable, or returning a partial result, and assert that the
coordinator's behavior (timeout, partial-result handling, retry) matches the
documented contract. For a rebalancing implementation specifically, a
chaos-style test that kills a node mid-rebalance and asserts no key is ever
simultaneously served by two nodes, and no key is ever unowned, is the
highest-value single test in the whole system, because that exact scenario is
where the failure modes in dimension 11 originate.

Integration tests running against a real multi-node cluster (even a small,
three-node local cluster) are worth the setup cost specifically to catch
network-layer issues that an in-process simulation of "node failure" cannot
reproduce. actual TCP timeout behavior, actual serialization costs across a
real socket, and actual clock skew between independent machines.

## 16. Observability signals

Per-node signals to collect from every node individually, never aggregated
away before they are visible. CPU, memory, and disk utilization, request
latency distribution (not just an average, since a single hot node can be
hidden inside a cluster-wide average), queue depth or in-flight request count,
and the count of keys or partitions currently owned. A healthy cluster shows
these metrics clustered tightly together across nodes. a hot partition or an
imbalance shows one node's line diverging visibly from its siblings on a
dashboard that plots all nodes together.

Router-level signals. the rate of cross-partition (fan-out) requests versus
single-partition requests, because a rising proportion of fan-out requests
over time is the earliest warning that the access pattern is drifting away
from what the partitioning was designed for. Also the router's own view of
partition ownership, exposed and compared against each node's self-reported
ownership, so that a disagreement (the split-brain symptom from dimension 11)
is caught by an automated check rather than by a customer report.

Rebalancing-specific signals. the count of keys or partitions currently
in-flight (being migrated from one node to another), the duration of the
current rebalance operation, and an alert on any key reporting more than one
current owner, which should never happen and should page immediately when it
does.

A healthy dashboard shows near-identical per-node metric lines, a low and
stable fan-out ratio, zero keys with ambiguous ownership, and rebalance
operations that complete within their expected duration window. A failing
cluster shows one or more node lines diverging from the pack, a fan-out ratio
climbing over weeks or months, or a rebalance operation that has been
in-flight far longer than its historical baseline, any of which should be
treated as an active investigation trigger, not a curiosity.

## 17. Security and privacy implications

Shared nothing changes where data physically resides, which has direct
consequences for data-residency and access-control requirements. Because each
node owns a disjoint, physically separate slice of data, a partitioning
function keyed on a regulatory dimension (region, jurisdiction) can be used
deliberately to guarantee that a given user's or tenant's data never leaves a
required physical boundary, which is a genuine advantage over a single shared
store that has to enforce residency logically rather than physically. This
advantage only holds if the partition key genuinely determines physical
location and if replicas are constrained by the same rule. a replica placed in
the wrong region silently defeats the guarantee.

The multiplied attack surface is the corresponding cost. N independently
deployed nodes each need their own authentication to peers, their own
transport encryption for inter-node traffic, and their own patch and
credential-rotation cadence, and a security gap in the process that
provisions new nodes (a weak default credential, a missing firewall rule) is
reproduced N times rather than once. Inter-node messages, which in a
single-machine or shared-disk design would often be in-process function calls
or reads from local-area shared storage, become network traffic in a shared
nothing deployment, and that traffic must be encrypted and authenticated
between nodes exactly as carefully as traffic between the system and an
external client, a requirement that is easy to underestimate for what feels
like "internal" traffic.

The router or coordinator, since it typically sees every request regardless of
which partition it targets, is a natural point of maximum data exposure and
deserves the access controls and audit logging of a system boundary, not the
lighter treatment sometimes given to purely internal infrastructure.

## 18. References

- Michael Stonebraker, "The Case for Shared Nothing", *IEEE Database
  Engineering Bulletin*, volume 9, issue 1, pages 4 to 9, 1986. Original PDF
  hosted by UC Berkeley. [dsf.berkeley.edu/papers/hpts85-nothing.pdf](https://dsf.berkeley.edu/papers/hpts85-nothing.pdf),
  verified 2026-08-02 (retrieved successfully, citation details cross-checked
  against the Wikipedia summary below because the PDF's text stream could not
  be extracted directly in this session).
- Wikipedia, "Shared-nothing architecture", summarizing Stonebraker's 1986
  taxonomy and the Tandem NonStop and Teradata early-adopter history.
  [en.wikipedia.org/wiki/Shared-nothing_architecture](https://en.wikipedia.org/wiki/Shared-nothing_architecture),
  verified 2026-08-02.
- Seth Gilbert and Nancy Lynch, "Brewer's Conjecture and the Feasibility of
  Consistent, Available, Partition-Tolerant Web Services", *ACM SIGACT News*,
  volume 33, issue 2, 2002.
  [users.ece.cmu.edu/~adrian/731-sp04/readings/GL-cap.pdf](https://users.ece.cmu.edu/~adrian/731-sp04/readings/GL-cap.pdf),
  verified 2026-08-02.
- David Karger, Eric Lehman, Tom Leighton, Rina Panigrahy, Matthew Levine, and
  Daniel Lewin, "Consistent Hashing and Random Trees. Distributed Caching
  Protocols for Relieving Hot Spots on the World Wide Web", *Proceedings of
  the 29th Annual ACM Symposium on Theory of Computing*, 1997, work performed
  at MIT and Akamai. [dblp.org bibliography record](https://dblp.org/rec/conf/stoc/KargerLLPLL97.html),
  verified 2026-08-05. The original akamai.com-hosted PDF has since gone dead
  (403, checked against the live host, the DOI's terminal ACM landing page,
  and MIT's DSpace repository, all of which now block automated access); the
  dblp record is the durable bibliographic citation for this paper.
- Apache Cassandra documentation, "Architecture overview".
  [cassandra.apache.org/doc/latest/cassandra/architecture/overview.html](https://cassandra.apache.org/doc/latest/cassandra/architecture/overview.html),
  verified 2026-08-02.
- Giuseppe DeCandia, Deniz Hastorun, Madan Jampani, Gunavardhan Kakulapati,
  Avinash Lakshman, Alex Pilchin, Swaminathan Sivasubramanian, Peter Vosshall,
  and Werner Vogels, "Dynamo. Amazon's Highly Available Key-value Store",
  *Proceedings of the 21st ACM Symposium on Operating Systems Principles
  (SOSP)*, 2007, hosted copy.
  [allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf),
  verified 2026-08-02.
- ByteByteGo, "How YouTube Supports Billions of Users with MySQL and Vitess".
  [blog.bytebytego.com/p/how-youtube-supports-billions-of](https://blog.bytebytego.com/p/how-youtube-supports-billions-of),
  verified 2026-08-02.
- Stacksync, "Named Thirteen Years Before the Technology Existed. The Origin
  Story of Teradata".
  [stacksync.com/blog/named-thirteen-years-before-the-technology-existed-the-origin-story-of-teradata](https://www.stacksync.com/blog/named-thirteen-years-before-the-technology-existed-the-origin-story-of-teradata),
  verified 2026-08-02.

## Code examples

Three languages, chosen because each expresses the pattern's core guarantee
(no shard's state is reachable from more than one execution context) through
a different language mechanism. TypeScript's module-private fields and a
single-process simulation of independent nodes, Go's goroutine-and-channel
model where a channel is the only sanctioned way into a shard, and Rust's
ownership system, where the compiler itself refuses to compile code that
would let two threads reach one shard's HashMap without going through its
channel. All three were compiled and executed in this session. outputs
matched across all three (alice=3, bob=4, carol=9), confirming the routing and
aggregation logic is equivalent regardless of the concurrency mechanism used
to enforce isolation. Java and Kotlin, which would express the pattern with an
ExecutorService per shard and a BlockingQueue as the inbox, are omitted
here because no Java toolchain was available in the execution environment
this session ran in. C#'s equivalent, an Actor-style class wrapping a
Channel<T>, is omitted for the same reason of toolchain availability, not
because the pattern translates poorly to either language.

```typescript
// Shared Nothing: each ShardNode owns its own state exclusively.
// No object here is reachable from more than one ShardNode. Coordination
// happens only through the Router's message-passing calls, which model
// a network hop in a real deployment.

interface Message {
  key: string;
  amount: number;
}

class ShardNode {
  private readonly local: Map<string, number> = new Map();

  constructor(public readonly id: number) {}

  handle(msg: Message): number {
    const current = this.local.get(msg.key) ?? 0;
    const next = current + msg.amount;
    this.local.set(msg.key, next);
    return next;
  }

  snapshot(): [string, number][] {
    return [...this.local.entries()];
  }
}

class Router {
  private readonly nodes: ShardNode[];

  constructor(nodeCount: number) {
    this.nodes = Array.from({ length: nodeCount }, (_, i) => new ShardNode(i));
  }

  private ownerOf(key: string): ShardNode {
    let hash = 2166136261;
    for (let i = 0; i < key.length; i++) {
      hash ^= key.charCodeAt(i);
      hash = Math.imul(hash, 16777619);
    }
    const index = Math.abs(hash) % this.nodes.length;
    return this.nodes[index];
  }

  route(msg: Message): number {
    return this.ownerOf(msg.key).handle(msg);
  }

  report(): [number, [string, number][]][] {
    return this.nodes.map((node) => [node.id, node.snapshot()]);
  }
}

const router = new Router(3);
const events: Message[] = [
  { key: "user:alice", amount: 1 },
  { key: "user:bob", amount: 4 },
  { key: "user:alice", amount: 2 },
  { key: "user:carol", amount: 9 },
];

for (const event of events) {
  router.route(event);
}

for (const [id, entries] of router.report()) {
  console.log(`node ${id}:`, entries);
}
```

```go
// Shared Nothing: each shard owns an unshared map. The only way another
// goroutine reaches a shard's state is by sending it a request on its
// channel, the in-process stand-in for a network call between nodes.
package main

import (
	"fmt"
	"hash/fnv"
)

type request struct {
	key    string
	amount int
	reply  chan int
}

type shard struct {
	id    int
	local map[string]int
	inbox chan request
}

func newShard(id int) *shard {
	s := &shard{id: id, local: make(map[string]int), inbox: make(chan request)}
	go s.run()
	return s
}

func (s *shard) run() {
	for req := range s.inbox {
		s.local[req.key] += req.amount
		req.reply <- s.local[req.key]
	}
}

type cluster struct {
	shards []*shard
}

func newCluster(n int) *cluster {
	c := &cluster{}
	for i := 0; i < n; i++ {
		c.shards = append(c.shards, newShard(i))
	}
	return c
}

func (c *cluster) ownerOf(key string) *shard {
	h := fnv.New32a()
	h.Write([]byte(key))
	return c.shards[int(h.Sum32())%len(c.shards)]
}

func (c *cluster) send(key string, amount int) int {
	owner := c.ownerOf(key)
	reply := make(chan int)
	owner.inbox <- request{key: key, amount: amount, reply: reply}
	return <-reply
}

func main() {
	c := newCluster(3)
	events := []struct {
		key    string
		amount int
	}{
		{"user:alice", 1},
		{"user:bob", 4},
		{"user:alice", 2},
		{"user:carol", 9},
	}
	for _, e := range events {
		total := c.send(e.key, e.amount)
		fmt.Printf("%s -> %d\n", e.key, total)
	}
}
```

```rust
// Shared Nothing: every shard's HashMap is owned exclusively by the
// thread that created it. No Arc, no Mutex over shared state. A shard
// is reached only by sending it a request over its own mpsc channel,
// standing in for a network hop.
use std::collections::HashMap;
use std::sync::mpsc::{self, Sender};
use std::thread;

struct Request {
    key: String,
    amount: i64,
    reply: Sender<i64>,
}

fn spawn_shard(id: usize) -> Sender<Request> {
    let (tx, rx) = mpsc::channel::<Request>();
    thread::spawn(move || {
        let mut local: HashMap<String, i64> = HashMap::new();
        for req in rx {
            let entry = local.entry(req.key.clone()).or_insert(0);
            *entry += req.amount;
            let _ = req.reply.send(*entry);
        }
        let _ = id;
    });
    tx
}

fn owner_of<'a>(shards: &'a [Sender<Request>], key: &str) -> &'a Sender<Request> {
    let mut hash: u32 = 2166136261;
    for b in key.bytes() {
        hash ^= b as u32;
        hash = hash.wrapping_mul(16777619);
    }
    &shards[(hash as usize) % shards.len()]
}

fn main() {
    let shards: Vec<Sender<Request>> = (0..3).map(spawn_shard).collect();
    let events: Vec<(&str, i64)> = vec![
        ("user:alice", 1),
        ("user:bob", 4),
        ("user:alice", 2),
        ("user:carol", 9),
    ];
    for (key, amount) in events {
        let (reply_tx, reply_rx) = mpsc::channel();
        let owner = owner_of(&shards, key);
        let sent = owner.send(Request {
            key: key.to_string(),
            amount,
            reply: reply_tx,
        });
        if sent.is_err() {
            continue;
        }
        if let Ok(total) = reply_rx.recv() {
            println!("{} -> {}", key, total);
        }
    }
    drop(shards);
}
```
