---
name: Leaderless Replication
slug: leaderless-replication
family: 12-data-storage
category: Data and Storage
aliases: [Dynamo-style Replication, Quorum Replication, Multi-Master Without a Leader, N/R/W Replication]
first_described: "DeCandia, Hastorun, Jampani, Kakulapati, Lakshman, Pilchin, Sivasubramanian, Vosshall, Vogels 2007"
maturity: canonical
related: [quorum, multi-leader-replication, consistent-hashing, write-ahead-log, crdt, gossip-protocol]
incompatible_with: [single-leader-replication, two-phase-commit]
verified: 2026-08-02
---

# Leaderless Replication

## 1. Name, aliases, and lineage

The canonical name in the academic and practitioner literature is Leaderless
Replication. It is also called Dynamo-style replication, because the technique
was popularized, though not invented from nothing, by the paper "Dynamo,
Amazon's Highly Available Key-value Store," by Giuseppe DeCandia, Deniz
Hastorun, Madan Jampani, Gunavardhan Kakulapati, Avinash Lakshman, Alex
Pilchin, Swaminathan Sivasubramanian, Peter Vosshall, and Werner Vogels,
presented at the ACM Symposium on Operating Systems Principles (SOSP) in 2007
([Amazon Science publication page](https://www.amazon.science/publications/dynamo-amazons-highly-available-key-value-store),
verified 2026-08-02). Martin Kleppmann's textbook uses "leaderless replication"
as the section heading for this exact family of systems and treats Dynamo,
Riak, Cassandra, and Voldemort as its instances, Martin Kleppmann, *Designing
Data-Intensive Applications*, O'Reilly, first edition 2017, chapter 5,
"Replication," section "Leaderless Replication," pages 177 to 187.

Two further aliases are common. Quorum replication, because the defining
mechanic is a read quorum and a write quorum sized against a replication
factor. N/R/W replication, because the three tunable numbers, the replication
factor N, the number of nodes a read must contact R, and the number of nodes a
write must contact W, are how engineers actually talk about configuring one of
these systems day to day.

The idea did not start with the 2007 paper. The paper itself credits earlier
quorum-based replication research, and the general technique of write and read
quorums intersecting to guarantee overlap traces to Robert Thomas and to David
Gifford's 1979 dissertation on quorum consensus. What the Dynamo paper
contributed was not the quorum idea but the combination of quorums with
consistent hashing for partitioning, sloppy quorums with hinted handoff for
availability during failures, vector clocks for conflict tracking, Merkle
trees for anti-entropy, and gossip for membership, packaged as a single
production system running Amazon's shopping cart service. That combination is
what the rest of the industry copied, and it is why the pattern is
attributed to that paper rather than to the earlier quorum literature.

## 2. Problem and context

A single-leader replicated database routes every write through one node. That
node is a single point of coordination for writes, and, depending on the
failover mechanism, sometimes a single point of failure that a human or an
automated process must detect and route around before writes can resume. For a
storage system whose primary promise is availability, specifically the ability
to always accept a write and always answer a read even when part of the
cluster is unreachable, a leader is a liability. If the leader is partitioned
away from a client, or has crashed and not yet been replaced, that client
cannot write, no matter how many other healthy replicas exist.

Amazon's shopping cart is the context that produced this pattern in its most
cited form. The DeCandia et al. paper states the business requirement
plainly. The shopping cart service must accept an "add to cart" write even
during a network partition or a node failure, because a shopper who cannot
add an item is a shopper who leaves, and a lost or duplicated cart item is a
much smaller business cost than a shopper who sees an error page. The paper's
own framing is that "always writable" was a harder requirement than "always
correct," and the replication design follows directly from ranking
availability above consistency for this specific workload (Amazon Science
publication page, verified 2026-08-02).

The pattern belongs to systems where the following context holds together.
Writes and reads are addressed to a key, so the responsible replica set for
any given operation can be computed deterministically from the key without
asking a leader. The workload can tolerate, or the application layer is
willing to resolve, the possibility that two writes to the same key happen
concurrently on different replicas with no coordinator serializing them.
The deployment spans multiple failure domains, multiple racks, multiple data
centers, or multiple availability zones, where node and network failures are
not rare exceptional events but a constant background condition to be
designed for rather than escalated on.

## 3. Forces

**Availability versus consistency.** This is the dominant force and the one
the pattern is built to resolve in a specific direction. A leaderless system
accepts a write as long as enough replicas out of N respond, where "enough"
is a number smaller than N, so the system stays writable even when some
replicas are down or unreachable. The price is that different replicas can
temporarily hold different values for the same key, and the system does not
serialize concurrent writes the way a single leader naturally would.

**Latency versus durability guarantee.** A write or read quorum that touches
more nodes gives a stronger guarantee about what the client will observe, but
it also means the operation's latency is bounded by the slower of several
network round trips rather than one, and the operation fails outright if
fewer than the quorum size of replicas can be reached in time.

**Coordination cost versus conflict handling cost.** A single leader pays a
coordination cost up front, every write is ordered before it is applied.
Leaderless replication defers that cost, writes are applied optimistically
and out of order relative to each other, and the cost reappears later as
conflict detection and resolution, either automatically through a
last-writer-wins rule or a CRDT merge function, or explicitly by presenting
both versions to the application or the end user.

**Operability versus flexibility.** Leaderless systems remove one class of
operational drama, the leader-election dance during a failover, and replace
it with a different one, tuning N, R, and W correctly for the workload,
running and monitoring anti-entropy so replicas do not drift apart forever,
and reasoning about read-your-writes guarantees that are not automatic the
way they are when every write and every subsequent read go through the same
leader.

**Team topology and cognitive load.** A team adopting a leaderless store
takes on the cognitive burden of designing for eventual consistency at the
application layer, deciding what a conflict means for their specific data
model, and choosing a resolution strategy. A team using a single-leader store
gets a strongly consistent default for free and only has to think about
conflicts if they deliberately introduce multi-leader writes later. This
pattern trades a lower operational burden for a higher application-design
burden, and that trade is not free at either end.

The pattern favors availability, low tail latency under partial failure, and
operational simplicity in the failover sense. It sacrifices default strong
consistency, ordering guarantees between writes to the same key, and pushes
conflict resolution onto the application or a merge function the application
must choose.

## 4. Applicability and non-applicability

**Reach for leaderless replication when**:

- The dominant requirement is that writes must be accepted even during a
  partial network partition or the loss of a minority of replicas, and a
  short window of stale or divergent reads is an acceptable cost for that.
- The data model has a natural, mergeable structure for the specific fields
  that see concurrent writes, for example an append-only set, a counter that
  can be represented as a CRDT, or a shopping cart where taking the union of
  two conflicting versions is the correct business behavior.
- Reads and writes are addressed by a single key or a small partition key, so
  the responsible replica set is computable without a lookup through a
  leader or a metadata service, which is the property that lets any
  coordinator node in the cluster serve any request.
- The deployment spans multiple data centers or availability zones and the
  team wants to keep serving traffic in each region even if inter-region
  connectivity is degraded.
- The team can tolerate operating and monitoring an anti-entropy process
  (read repair, Merkle-tree comparison, or hinted-handoff replay) as an
  ongoing background job rather than a one-time setup step.

**Do NOT reach for leaderless replication when**:

- The application needs linearizable reads and writes, for example a bank
  account balance check that must never observe a stale value, or a
  distributed lock. Quorum reads and writes on a leaderless system are not
  linearizable in general, even when R plus W exceeds N, because there is no
  single point that orders concurrent writes; Kleppmann demonstrates a
  concrete non-linearizable execution with R equals W equals a majority in
  *Designing Data-Intensive Applications*, chapter 9, "Consistency and
  Consensus," section "Linearizability and quorums," pages 335 to 337.
- The data model has fields where "merge the two versions" has no sensible
  meaning, for example a unique username reservation or an inventory count
  that must never go negative; these need either a single-leader design or an
  explicit consensus protocol, not last-writer-wins or an ad hoc merge.
- The team has no plan for what the application does when it receives
  multiple sibling versions of a key back from a read. Shipping a leaderless
  store and always picking "the one with the newest timestamp" without
  understanding that this silently drops a concurrent write is a
  misapplication, not a simplification.
- Strict multi-record transactions across keys are required. Leaderless
  systems are built around single-key or single-partition operations; there
  is no built-in mechanism analogous to a leader's write-ahead log ordering
  a multi-key transaction.
- The workload is small enough, and the availability requirement modest
  enough, that a single-leader system with automated failover already meets
  the requirement with far less application-level complexity. Leaderless
  replication is not free complexity insurance; it is a deliberate trade
  that should be made because the availability requirement demands it.

## 5. Structure

- **Coordinator.** The node that receives a client's read or write request.
  In most implementations any node in the cluster can act as coordinator for
  any key; the coordinator does not have to be one of the replicas that
  stores the key. It computes the replica set from the key, forwards the
  request to those replicas in parallel, and waits for the required number
  of responses before answering the client.
- **Replica set.** The N nodes, determined by a partitioning scheme, usually
  consistent hashing, that are responsible for storing a given key. There is
  no designated primary among them for ordering purposes; every replica can
  independently accept a write for the key it is responsible for.
- **Replication factor N.** The configured number of replicas that should
  eventually hold a copy of any given key. Set at the keyspace or table
  level, not per request.
- **Write quorum W.** The number of replicas out of N that must acknowledge a
  write before the coordinator reports success to the client.
- **Read quorum R.** The number of replicas out of N that must respond to a
  read before the coordinator can assemble and return a result to the
  client.
- **Version metadata.** A mechanism attached to each stored value that lets
  the system tell whether two versions of a key are causally related (one
  happened strictly after the other and supersedes it) or concurrent (neither
  is aware of the other, and both must be surfaced or merged). Vector
  clocks, and, in later Riak versions, dotted version vectors, are the
  mechanism the Dynamo lineage uses for this.
- **Sloppy quorum and hinted handoff.** A fallback mechanism where, if one or
  more of the N home replicas for a key is unreachable, the coordinator
  writes to the next healthy node in the ring instead, tags that write with a
  hint identifying the intended home node, and later hands the data off to
  the home node once it recovers.
- **Read repair.** A background or inline step where, on a read, if the
  coordinator notices that some replicas returned a stale version, it writes
  the newer version back to those replicas.
- **Anti-entropy process.** A background job, often built on Merkle trees,
  that periodically compares the full contents of two replicas and
  synchronizes any divergence that read repair has not already caught, which
  matters for keys that are rarely or never read.

## 6. ASCII structure diagram

```
                          client
                            |
                            v
                     +--------------+
                     |  coordinator  |   (any node can play
                     |     node      |    this role per request)
                     +--------------+
                       /     |      \
              hash(key) determines the N-node
              preference list on the ring
                     /       |        \
                    v        v         v
             +---------+ +---------+ +---------+
             | replica | | replica | | replica |     N = 3
             |   A     | |   B     | |   C     |
             +---------+ +---------+ +---------+
                  |            |           |
             version+data  version+data  version+data
             (vector clock  (vector clock (vector clock
              per value)     per value)    per value)

   write   coordinator waits for W acks out of N   (e.g. W = 2)
   read    coordinator waits for R responses,       (e.g. R = 2)
           compares versions, returns newest
           and/or surfaces siblings on conflict

   background
     read repair    -> pushes newest version to stale replicas
     anti-entropy   -> Merkle-tree diff between replica pairs
     hinted handoff -> temp node holds data for an unreachable
                        home replica, replays it on recovery
```

## 7. Dynamics

```
WRITE, replication factor N=3, write quorum W=2

client -> coordinator : PUT key=cart:42 value=v1  vclock=[]

coordinator computes preference list = [A, B, C]
coordinator sends PUT(key, v1, new_vclock) to A, B, C in parallel

   A --ack--> coordinator     (t=5ms)
   B --ack--> coordinator     (t=7ms)
   C ......................   (network partition, no response)

coordinator has 2 acks (>= W=2) -> returns SUCCESS to client
                                    even though C never confirmed


CONCURRENT WRITE from a second client, same key, before either
client has seen the other's write

client-1 -> coordinator-1 : PUT key=cart:42 value="+shoes" vclock=[A:1,B:1]
client-2 -> coordinator-2 : PUT key=cart:42 value="+socks" vclock=[A:1,B:1]

both writes descend from the same vclock, so neither knows about
the other -> both are accepted as CONCURRENT, not one overwriting
the other. Replica A now holds two sibling versions for the key.


READ, read quorum R=2

client -> coordinator : GET key=cart:42

coordinator sends GET(key) to A, B, C in parallel
   A --> v("+shoes", vclock=[A:2,B:1]) , v("+socks", vclock=[A:1,B:2])
   B --> v("+shoes", vclock=[A:2,B:1])

coordinator has R=2 responses.
compares vector clocks, finds neither sibling dominates the other
-> coordinator returns BOTH siblings to the client
   (a Dynamo-style client must merge them, e.g. union the cart items)

read repair: coordinator also pushes the merged/known versions
             back to any replica that was behind
```

## 8. Implementation variants

**Sloppy quorum, Dynamo and Riak variant.** The write and read quorums are
satisfied by "the first N healthy nodes reachable on the ring," not
necessarily the N nodes that are permanently responsible for the key. This
maximizes write availability during a partition at the cost of a write
temporarily landing on a node that will later hand it off. Riak's
documentation on `n_val`, sloppy quorum behavior, and fallback vnodes
describes this variant directly
([Riak KV replication concepts](https://docs.riak.com/riak/kv/2.2.3/learn/concepts/replication/index.html),
verified 2026-08-02).

**Strict quorum, no hinted handoff.** Some Dynamo-derived systems, and Riak
itself when `notfound_ok` and PW/PR (durable primary write/read) settings are
tightened, restrict quorum membership to only the N nodes permanently
responsible for a key. A write or read simply fails if fewer than the quorum
size of the actual home replicas are reachable. This trades availability for
a stronger guarantee that an acknowledged write is on a home replica, not
merely somewhere temporary.

**Last-writer-wins.** Concurrent versions are resolved automatically by
comparing timestamps (physical or a logical counter) and discarding the
loser. Simple to implement and simple for application authors to reason
about, but it silently and permanently drops one of the two concurrent
writes, which is unacceptable for data like a shopping cart where the loser
might have been "add an item" and the winner "remove an item," producing a
result the user never intended. Cassandra defaults to this strategy per
column, resolved at write time by comparing the client-supplied or
server-assigned timestamp.

**Vector clocks with explicit sibling resolution.** The original Dynamo
design and early Riak versions attach a vector clock to every value. On a
conflicting read, both versions are returned to the client (or to a
Riak "pre-commit" or application-side resolver), which is responsible for
merging them into a single value on the next write. This variant does not
lose data silently but does push real design and implementation burden onto
every application that uses the store.

**Dotted version vectors.** A refinement over plain vector clocks, adopted by
Riak from version 2.0 onward, that avoids "sibling explosion," the growth of
an unbounded number of concurrent sibling versions when the same key is
written frequently and concurrently from many clients. It tracks per-write
provenance more precisely than a per-node counter can.

**CRDT-based automatic merge.** Instead of surfacing raw siblings to the
application, the store defines the value type as a conflict-free replicated
data type, a counter, a set, a map, or a register with a well-defined,
associative, commutative merge function, and merges concurrent versions
automatically and deterministically without application involvement. Riak KV
ships built-in CRDT data types (counters, sets, maps, flags) specifically to
remove the sibling-resolution burden for common cases
([Riak KV replication concepts](https://docs.riak.com/riak/kv/2.2.3/learn/concepts/replication/index.html),
verified 2026-08-02).

**Tunable per-operation consistency, Cassandra style.** Rather than fixing N,
R, and W for the whole keyspace, the client chooses a consistency level per
individual read or write, from `ONE` through `QUORUM` to `ALL`, letting a
single application trade latency for durability differently for a
low-stakes analytics write versus a high-stakes financial write, all against
the same underlying leaderless replica set (Apache Cassandra documentation,
"Dynamo," verified 2026-08-02).

## 9. Known production uses

**Amazon Dynamo**, the internal system described in the 2007 paper, served
Amazon's shopping cart and several other services with a stated requirement
of always accepting writes even during network partitions and node failures.
The paper reports the system was in production use backing "tens of
thousands of servers" worth of internal services at Amazon at the time of
publication (Amazon Science publication page, verified 2026-08-02). Note
that Amazon DynamoDB, the public AWS product, is a distinct system built
later that reimplements many of the same ideas as a managed service, not a
direct open-sourcing of the original internal Dynamo; DynamoDB's own
documentation describes its default eventually consistent reads alongside an
optional strongly consistent read mode, a direct descendant of the tunable
consistency idea
([Amazon DynamoDB read consistency documentation](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html),
verified 2026-08-02).

**Apache Cassandra** explicitly documents its architecture as derived from
Dynamo, combining Dynamo-style consistent hashing partitioning and tunable,
per-operation consistency levels with the Bigtable-style storage engine.
Cassandra's own documentation states it "relies on a number of techniques
from Amazon's Dynamo distributed storage key-value system," specifically
"dataset partitioning using consistent hashing" and "multi-master
replication using versioned data and tunable consistency," and describes
hinted handoff, read repair, and Merkle-tree anti-entropy repair as its
mechanisms for reconciling replicas
([Apache Cassandra documentation, "Dynamo"](https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html),
verified 2026-08-02). Cassandra is used in production at large scale by
Apple, Netflix, and Uber, per the same Apache Cassandra project
documentation and its published case studies pages, and it is the storage
engine originally open sourced by Facebook, described in Avinash Lakshman
and Prashant Malik, "Cassandra. A Decentralized Structured Storage System,"
ACM SIGOPS Operating Systems Review, volume 44, issue 2, April 2010.

**Riak KV**, originally built by Basho Technologies, is a direct, openly
Dynamo-derived key-value store exposing the N, R, and W tuning parameters to
the operator per bucket, along with sloppy quorum, hinted handoff, vector
clock or dotted-version-vector based conflict tracking, read repair, and
built-in CRDT data types for automatic conflict merging. Riak's own
documentation states plainly that data is "replicated to a number of nodes
in the cluster according to the N value" and that the tunable read and write
parameters are bound by that N value
([Riak KV replication concepts](https://docs.riak.com/riak/kv/2.2.3/learn/concepts/replication/index.html),
verified 2026-08-02).

**Project Voldemort**, built at LinkedIn starting in 2009 and explicitly
modeled on the Dynamo paper, was used in production at LinkedIn as a
distributed key-value store for highly scalable storage before the company
migrated to its successor, Project Venice, around 2018
([Wikipedia, "Voldemort (distributed data store)"](https://en.wikipedia.org/wiki/Voldemort_(distributed_data_store)),
verified 2026-08-02).

## 10. Consequences

**Positive.**

- The system remains writable and readable during a partial node or network
  failure, as long as W or R nodes out of N are still reachable, with no
  human or automated failover step required, because there is no leader to
  fail over.
- Write and read latency for a well-behaved cluster is bounded by the
  slowest of a small, fixed number of parallel round trips, not by a chain
  of replication hops through a leader and its followers.
- Adding or removing capacity does not require re-electing anything; it
  requires reassigning key ranges on the consistent-hashing ring, which is
  a data-movement problem, not a coordination problem.
- The N, R, and W parameters, or a per-operation consistency level in
  Cassandra's style, give the operator or the application a direct,
  quantitative lever to trade latency, durability, and consistency per
  workload rather than accepting one fixed trade-off for the whole system.
- There is no single node whose loss can, even temporarily, take writes for
  an entire keyspace offline, because responsibility for any given key is
  spread across N independent nodes with no ordering dependency between
  them.

**Negative.**

- The system does not guarantee linearizability by default, and quorum
  overlap (R plus W greater than N) is a durability guarantee, that a read
  quorum and a write quorum share at least one node, not a consistency
  guarantee about which value that shared node will report, since
  concurrent writes with no coordinator ordering them can still produce
  observably stale or out-of-order reads.
- Conflict handling becomes the application's problem, either through an
  explicit sibling-merge step the application must implement correctly, or
  through a last-writer-wins policy that silently discards one of two
  concurrent writes, a real data-loss mode that is easy to overlook during
  design.
- Anti-entropy, read repair, and hinted-handoff replay are ongoing
  operational processes that must be monitored, because a replica that
  never receives a repair pass can drift arbitrarily far from the rest of
  the cluster for keys that are written once and rarely or never read
  afterward.
- Multi-record transactions spanning more than one key are not naturally
  supported, since there is no single serialization point analogous to a
  leader's write-ahead log that could order writes to two different keys
  relative to each other.
- Debugging "why did the client see two different values for the same key"
  is a genuinely harder class of problem for an on-call engineer than
  debugging "why is the leader down," because the former requires reasoning
  about vector clocks, quorum membership at the moment of each operation,
  and the timing of a partition, rather than reading one leader's log.

## 11. Failure modes and misuse

**Symptom.** A quorum read intermittently returns stale data even though
R plus W is configured to exceed N, and the team believed this configuration
guaranteed strong consistency.
**Cause.** Overlapping read and write quorums guarantee that at least one
node in the read set also received the write, but they do not guarantee that
node's response is used, or that concurrent writes are ordered; a client can
still observe an older write after a newer one under normal Dynamo-style
quorum semantics, a scenario Kleppmann demonstrates concretely.
**Fix.** Do not treat R plus W greater than N as a linearizability
guarantee. If the workload genuinely needs linearizable reads for a subset
of keys, either move those keys to a single-leader or consensus-backed
store, or use the leaderless store's own strongly-consistent primitives if
it offers any (for example DynamoDB's optional strongly consistent read),
and document clearly which keys get which guarantee.

**Symptom.** The same logical record silently duplicates or loses an update,
for example a shopping cart that periodically drops an item a user added.
**Cause.** Last-writer-wins conflict resolution discarded one of two
concurrent writes because the application never checked for or merged
sibling versions, or because the timestamp source used to break ties was not
monotonic across nodes (clock skew).
**Fix.** Switch the value type to something with a well-defined merge
function, a CRDT set for cart items rather than a plain overwritten field, or
explicitly surface siblings to the application and merge them on write, and
never rely on wall-clock timestamps across nodes as a correctness mechanism
without bounding clock skew.

**Symptom.** A node that was down for an extended period rejoins the cluster
and the cluster's read latency or error rate spikes for keys it is
responsible for.
**Cause.** The rejoining node is missing a large backlog of writes that
neither hinted handoff nor read repair has caught up on yet, because hinted
handoff only covers writes that happened while a temporary substitute node
was reachable and holding hints, and anti-entropy runs on its own schedule
that may not have completed a full pass since the node returned.
**Fix.** Run and monitor the anti-entropy (Merkle-tree repair) process on an
explicit schedule rather than assuming read repair alone keeps replicas in
sync, and treat "time since last full anti-entropy pass" as a first-class
operational metric, not an afterthought.

**Symptom.** The number of sibling versions for a single key grows without
bound, degrading read latency and memory usage for that key specifically.
**Cause.** A high write rate to the same key from many independent clients,
combined with a version-tracking scheme (plain vector clocks keyed by
client ID rather than by node, for example) that cannot distinguish
"the same client writing again" from "a genuinely new concurrent writer,"
causing sibling count to grow with every write instead of converging.
**Fix.** Use a version-tracking scheme designed to bound sibling growth,
such as dotted version vectors, and, where the access pattern allows it,
route repeated writes to the same key from the same logical actor through a
single coordinator so the version history reflects true causality rather
than an artifact of routing.

**Symptom.** A minority of the cluster is unreachable and writes appear to
succeed, but data for those writes is nowhere to be found when the same
minority later recovers and is queried directly.
**Cause.** Sloppy quorum accepted the write on temporary fallback nodes, and
hinted handoff either never fired (the coordinator crashed before handing
off) or the temporary node itself was later decommissioned or had its hint
data expire before delivery.
**Fix.** Treat sloppy-quorum-accepted writes as durable only after hinted
handoff confirms delivery to a home replica, monitor hint queue depth and
age as an operational signal, and, for workloads that cannot tolerate this
class of loss, disable sloppy quorum in favor of a strict quorum against the
key's permanent home replicas, accepting the corresponding reduction in
write availability.

## 12. Trade-off matrix

| Force | Leaderless replication | Single-leader replication | Multi-leader replication |
|---|---|---|---|
| Write availability during partition | High. Any W of N reachable nodes suffice, including temporary fallback nodes under sloppy quorum | Low. Writes stop if the leader is unreachable, until failover completes | High within each leader's local scope, but each leader can independently accept writes |
| Read-after-write consistency by default | Not guaranteed by default; requires the client to track and forward version metadata or route repeat reads to the same nodes | Guaranteed for a client reading from the same connection that wrote, if reads go to the leader | Guaranteed locally at the leader that took the write, not across leaders |
| Conflict resolution | Required, explicit (siblings, last-writer-wins, or CRDT merge) at the application or store layer for every write path | Not needed. The leader serializes all writes to a key by construction | Required, explicit, same as leaderless, but scoped to conflicts between a smaller number of leaders |
| Coordination cost per write | Low and constant; a fixed fan-out to N replicas with no election or log-shipping chain | Low per write, but the leader is a serialization bottleneck and a failover coordination point exists | Low per leader, plus asynchronous cross-leader replication and conflict detection |
| Operational complexity of failure recovery | Moderate and continuous; anti-entropy and hinted handoff run as ongoing background processes | Concentrated at failover time; usually a well-defined, tooled event (leader election) | Moderate and continuous, similar to leaderless, but scoped per leader pair |
| Multi-key transaction support | Effectively none; designed around single-key operations | Natural, since the leader can order and apply a multi-key transaction against its own log | Natural within one leader's scope, not across leaders |
| Suitability for a strict correctness invariant (e.g., unique constraint) | Poor without an external coordination layer | Good, the leader is a natural single point to enforce it | Poor across leaders without an external coordination layer |

## 13. Related and incompatible patterns

**Quorum** is the mechanism this pattern is built on. Leaderless replication
is, structurally, "quorum reads and writes plus partitioning plus conflict
tracking plus anti-entropy," and understanding quorum sizing, why R plus W
greater than N guarantees overlap, and what that overlap does and does not
guarantee, is a prerequisite to understanding this pattern correctly.

**Multi-leader replication** shares the goal of accepting writes at more
than one place, but structures the cluster around a small, explicit set of
leaders, each locally strongly ordered, replicating asynchronously to each
other, rather than treating every replica as an equal peer for every write.
Multi-leader systems typically have far fewer nodes that can independently
accept a write for a given key than a leaderless system's replication
factor N, and conflict resolution in multi-leader systems is scoped between
those few leaders rather than between an arbitrary quorum.

**Consistent hashing** is almost always the partitioning scheme paired with
leaderless replication, because it is what lets a coordinator compute a
key's N-node replica set without consulting a leader or a metadata service,
and what lets the cluster reassign only a small fraction of keys when a node
joins or leaves. The Dynamo paper's replication design and its consistent
hashing design are presented together for exactly this reason.

**CRDT (conflict-free replicated data type)** composes directly with
leaderless replication as one specific answer to dimension 8's conflict
resolution question, replacing application-level sibling merging with a
mathematically well-defined, automatic merge function, at the cost of
restricting the value's data model to types that admit such a merge.

**Gossip protocol** is the usual mechanism leaderless clusters use to
propagate membership changes (a node joined, a node is suspected down)
without a leader, and it is what lets any coordinator node maintain a
current enough view of the ring to route requests correctly.

**Write-ahead log** is not incompatible with leaderless replication, each
individual replica typically still uses one locally for its own durability
and crash recovery, but the pattern this entry describes is orthogonal to
that local durability mechanism; the write-ahead log lives inside a single
replica, not across the replica set.

**Two-phase commit** is incompatible with the spirit of leaderless
replication in practice, though not logically impossible to bolt on. Two-
phase commit reintroduces a coordinator that blocks until every participant
acknowledges, which reintroduces exactly the availability-limiting
coordination dependency leaderless replication exists to avoid; a system
that needs two-phase commit semantics is signaling that it should use a
consensus-backed or single-leader design for that operation instead.

**Single-leader replication** is the pattern leaderless replication is most
directly an alternative to, and the two are incompatible as descriptions of
the same write path, a given key's writes are either always serialized
through one leader or they are not; a system can mix the two by using
single-leader replication for some data and leaderless for other data, but
a single write path cannot be both at once.

## 14. Refactoring path in and out

**Introducing leaderless replication into a single-leader system.**

1. Identify which parts of the data model actually need the availability
   guarantee. Do not migrate the whole database at once; leaderless
   replication is a targeted trade, not a general upgrade.
2. For each field or record type being migrated, design its conflict
   resolution strategy before writing any replication code. Decide, per
   field, whether last-writer-wins is acceptable, whether a CRDT type fits,
   or whether the application must merge siblings explicitly. This decision
   is the actual hard part of the migration; the quorum plumbing is
   comparatively mechanical.
3. Choose N, and choose initial R and W values that sum to more than N to
   get overlap, understanding from dimension 3 and dimension 11 that this
   overlap is a durability property, not a linearizability guarantee.
4. Stand up the replica set and dual-write from the existing single-leader
   system during a transition window, verifying that reads from the new
   leaderless path match expectations under normal operation before cutting
   reads over.
5. Explicitly test the failure path before relying on it. Kill a minority of
   replicas in a staging environment and confirm writes still succeed, then
   bring the node back and confirm hinted handoff and anti-entropy actually
   converge it, since this is the entire reason for the migration and it is
   the one thing that is easy to leave unverified.
6. Cut reads over, then cut the old single-leader path off, monitoring
   sibling counts and anti-entropy lag as the new operational signals that
   replace "is the leader healthy" as the primary health check.

**Removing leaderless replication in favor of a single leader.**

1. Confirm the actual reason for removal. The two common ones are
   application-level conflict-resolution bugs proving harder to get right
   than expected, or a requirement (a unique constraint, a linearizable
   balance check) emerging that leaderless replication cannot satisfy for
   this data.
2. Pick one existing node, or stand up a new dedicated node, to become the
   leader, and change the write path so every write for the affected keys
   routes through it rather than fanning out to N nodes directly.
3. Before the leader takes over authoritative writes, run a final
   anti-entropy pass and reconcile any outstanding sibling versions, because
   once the leader is authoritative there is no further mechanism in the old
   design that will surface or merge them.
4. Switch reads to go through the leader (or its synchronous or
   asynchronous followers, per whatever consistency the single-leader design
   requires) and retire the quorum-fan-out read path.
5. Decommission the sloppy-quorum, hinted-handoff, and anti-entropy
   machinery only after confirming, over a real operational period, that no
   writes are still arriving on the old write path from stale client
   configuration or cached routing tables.

## 15. Testing and verification

Testing code that uses leaderless replication is easier than testing a
leader-election-based system in exactly one respect and harder in most
others. It is easier because there is no leader-election state machine to
simulate; a test can freely kill any subset of fewer than N minus W nodes
and expect writes to keep succeeding, which is a simple, deterministic
property to assert. It is harder because the interesting bugs live in
concurrent-write conflict handling, which requires deliberately constructing
two writes with the same causal starting point (the same vector clock) and
confirming the system treats them as concurrent siblings rather than one
silently overwriting the other, and in partial-failure recovery, which
requires confirming hinted handoff and anti-entropy actually converge a node
that was offline, not merely that they run without error.

Useful techniques include a network-fault fixture that can pause and resume
connectivity between specific node pairs, so partition scenarios are
reproducible rather than relying on flaky timing; property-based tests that
generate random interleavings of concurrent writes to the same key and
assert the invariant "no acknowledged write is ever permanently lost,"
rather than asserting a specific resolved value, since the resolved value
depends on the conflict-resolution policy under test; and an explicit
convergence test that, after injecting a partition and letting both sides
write independently, heals the partition and asserts that all replicas
converge to the same value (or the same well-defined sibling set) within a
bounded time, which is the direct test of the anti-entropy and read-repair
machinery. Test doubles for the store itself are generally a poor
substitute here; because the pattern's entire value proposition is its
behavior under partial failure, an in-memory stand-in that cannot simulate
node unavailability tests very little of what actually matters.

## 16. Observability signals

A healthy leaderless cluster shows quorum operations succeeding at close to
100 percent with R or W nodes responding well within the configured timeout;
hint queue depth per node staying near zero, meaning hinted handoff is
draining as fast as it accumulates rather than backing up; anti-entropy
(Merkle-tree or equivalent) pass duration and recency staying within the
operator's chosen bound, so that a rarely-read key is still known to
converge within a predictable window even without read repair; sibling
count per key staying low, typically one or two, with any sustained rise
signaling either a hot key under heavy concurrent write pressure or a
version-tracking bug; and per-replica clock skew, where last-writer-wins
resolution is in use, staying within the bound the resolution policy
assumes.

An unhealthy cluster shows the mirror image. Quorum operations timing out
or falling back to a smaller effective quorum more often than the SLO
allows; a hint queue that grows monotonically on one or more nodes,
indicating a persistently unreachable or overloaded home replica that
sloppy quorum is silently papering over; anti-entropy passes that have not
completed in longer than the configured interval, meaning some subset of
keys have no freshness guarantee at all; a sibling count per key climbing
into double or triple digits, a direct signal of the sibling-explosion
failure mode from dimension 11; and read latency at the configured
consistency level rising specifically on the tail (p99, not the median),
which is the usual first symptom of a slow or degraded minority of replicas
before it becomes visible as an outright failure.

Cassandra and Riak both expose these signals natively through their metrics
systems (hinted handoff queue size, repair session status and duration,
sibling or tombstone counts), which is the practical reason to prefer using
the store's own built-in metrics over reimplementing equivalent
observability at the application layer.

## 17. Security and privacy implications

Leaderless replication widens the set of nodes that legitimately hold a
plaintext or at-rest-encrypted copy of any given record from one, the
leader plus its followers in a single-leader system's simplest form, which
is often still a single authoritative writer, to N independently writable
nodes. This correspondingly widens the attack surface for any single
compromised node to accept a forged or unauthorized write on that node's own
authority, since no leader validates or serializes the write before it is
considered locally accepted. Access control and write authorization
therefore need to be enforced consistently at every coordinator and every
replica, not centralized at a single leader's write path, and a
misconfigured or compromised node's writes can propagate to the rest of the
replica set through the ordinary conflict-resolution and anti-entropy
machinery exactly as if they were legitimate, since that machinery has no
concept of write provenance beyond the version metadata used for causality,
not authenticity.

Sibling versions surfaced to an application, and hinted-handoff data
temporarily held on a node other than a key's permanent home, both mean
that sensitive data can transiently exist on more physical nodes, and in
more places in the request path, than a simple "N replicas hold the data"
model suggests. This matters for data residency and data locality
requirements, for example a regulatory requirement that a record never
leave a specific region, because a coordinator or a fallback node
participating in sloppy quorum must itself be constrained to comply with
such a requirement, otherwise the pattern's normal operation, accepting a
write on whatever healthy node is reachable, can place data outside the
intended boundary during a failure. The Dynamo paper does not treat
security as a primary design goal, and this entry is not aware of a
specific documented vulnerability class unique to the replication pattern
itself beyond the general widened-write-surface and data-locality points
above; where a concrete threat model is required, it should be evaluated
against the specific store's own security documentation rather than
assumed from the pattern description.

## 18. References

- Giuseppe DeCandia, Deniz Hastorun, Madan Jampani, Gunavardhan Kakulapati,
  Avinash Lakshman, Alex Pilchin, Swaminathan Sivasubramanian, Peter
  Vosshall, Werner Vogels. "Dynamo. Amazon's Highly Available Key-value
  Store." ACM SOSP 2007. Amazon Science publication page,
  https://www.amazon.science/publications/dynamo-amazons-highly-available-key-value-store,
  verified 2026-08-02.
- Martin Kleppmann. *Designing Data-Intensive Applications*. O'Reilly, first
  edition, 2017. Chapter 5, "Replication," section "Leaderless Replication,"
  pages 177 to 187. Chapter 9, "Consistency and Consensus," section
  "Linearizability and quorums," pages 335 to 337.
- Apache Cassandra documentation, "Dynamo,"
  https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html,
  verified 2026-08-02.
- Avinash Lakshman, Prashant Malik. "Cassandra. A Decentralized Structured
  Storage System." ACM SIGOPS Operating Systems Review, volume 44, issue 2,
  April 2010.
- Riak KV documentation, "Replication,"
  https://docs.riak.com/riak/kv/2.2.3/learn/concepts/replication/index.html,
  verified 2026-08-02.
- Wikipedia, "Voldemort (distributed data store),"
  https://en.wikipedia.org/wiki/Voldemort_(distributed_data_store),
  verified 2026-08-02.
- Amazon Web Services, "Read consistency," Amazon DynamoDB Developer Guide,
  https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html,
  verified 2026-08-02.

## Code examples

The three examples below implement the same core mechanic. A client-side
coordinator fans a write out to N simulated replicas, waits for W
acknowledgements, and, on read, fans out to N replicas, waits for R
responses, and detects concurrent versions using a simple vector clock. This
is a minimal illustration of the pattern's mechanics, not a production
replication library; a real system also needs consistent-hashing
partitioning, network-level fault injection, hinted handoff, and anti-
entropy, none of which are in scope for a runnable teaching example.

### TypeScript

```typescript
type VClock = Record<string, number>;

interface Versioned<T> {
  value: T;
  clock: VClock;
}

function clockDominates(a: VClock, b: VClock): boolean {
  const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
  let strictlyGreater = false;
  for (const k of keys) {
    const av = a[k] ?? 0;
    const bv = b[k] ?? 0;
    if (av < bv) return false;
    if (av > bv) strictlyGreater = true;
  }
  return strictlyGreater;
}

class Replica<T> {
  private store = new Map<string, Versioned<T>[]>();
  constructor(public readonly id: string, public up = true) {}

  put(key: string, value: T, clock: VClock): void {
    if (!this.up) throw new Error(`${this.id} unreachable`);
    const existing = this.store.get(key) ?? [];
    const survivors = existing.filter((v) => !clockDominates(clock, v.clock));
    survivors.push({ value, clock });
    this.store.set(key, survivors);
  }

  get(key: string): Versioned<T>[] {
    if (!this.up) throw new Error(`${this.id} unreachable`);
    return this.store.get(key) ?? [];
  }
}

class Coordinator<T> {
  constructor(private replicas: Replica<T>[], private w: number, private r: number) {}

  write(key: string, value: T, actor: string): { acked: number } {
    let acked = 0;
    const clock: VClock = { [actor]: Date.now() };
    for (const replica of this.replicas) {
      try {
        replica.put(key, value, clock);
        acked++;
      } catch {
        /* unreachable, skip */
      }
    }
    if (acked < this.w) throw new Error(`only ${acked}/${this.w} replicas acked`);
    return { acked };
  }

  read(key: string): Versioned<T>[] {
    const responses: Versioned<T>[][] = [];
    for (const replica of this.replicas) {
      try {
        responses.push(replica.get(key));
      } catch {
        /* unreachable, skip */
      }
    }
    if (responses.length < this.r) {
      throw new Error(`only ${responses.length}/${this.r} replicas responded`);
    }
    const all = responses.flat();
    return all.filter((v) => !all.some((other) => other !== v && clockDominates(other.clock, v.clock)));
  }
}

const replicas = [new Replica<string>("A"), new Replica<string>("B"), new Replica<string>("C")];
const coordinator = new Coordinator(replicas, 2, 2);
coordinator.write("cart-42", "+shoes", "client-1");
replicas[2].up = false;
coordinator.write("cart-42", "+socks", "client-2");
console.log(coordinator.read("cart-42"));
```

### Python

```python
from dataclasses import dataclass
from time import time_ns


VClock = dict[str, int]


def clock_dominates(a: VClock, b: VClock) -> bool:
    keys = set(a) | set(b)
    strictly_greater = False
    for k in keys:
        av, bv = a.get(k, 0), b.get(k, 0)
        if av < bv:
            return False
        if av > bv:
            strictly_greater = True
    return strictly_greater


@dataclass
class Versioned:
    value: object
    clock: VClock


class Replica:
    def __init__(self, replica_id: str, up: bool = True) -> None:
        self.id = replica_id
        self.up = up
        self._store: dict[str, list[Versioned]] = {}

    def put(self, key: str, value: object, clock: VClock) -> None:
        if not self.up:
            raise RuntimeError(f"{self.id} unreachable")
        survivors = [v for v in self._store.get(key, []) if not clock_dominates(clock, v.clock)]
        survivors.append(Versioned(value, clock))
        self._store[key] = survivors

    def get(self, key: str) -> list[Versioned]:
        if not self.up:
            raise RuntimeError(f"{self.id} unreachable")
        return self._store.get(key, [])


class Coordinator:
    def __init__(self, replicas: list[Replica], w: int, r: int) -> None:
        self.replicas = replicas
        self.w = w
        self.r = r

    def write(self, key: str, value: object, actor: str) -> int:
        acked = 0
        clock: VClock = {actor: time_ns()}
        for replica in self.replicas:
            try:
                replica.put(key, value, clock)
                acked += 1
            except RuntimeError:
                pass
        if acked < self.w:
            raise RuntimeError(f"only {acked}/{self.w} replicas acked")
        return acked

    def read(self, key: str) -> list[Versioned]:
        responses: list[Versioned] = []
        seen = 0
        for replica in self.replicas:
            try:
                responses.extend(replica.get(key))
                seen += 1
            except RuntimeError:
                pass
        if seen < self.r:
            raise RuntimeError(f"only {seen}/{self.r} replicas responded")
        return [
            v
            for v in responses
            if not any(other is not v and clock_dominates(other.clock, v.clock) for other in responses)
        ]


if __name__ == "__main__":
    replicas = [Replica("A"), Replica("B"), Replica("C")]
    coordinator = Coordinator(replicas, w=2, r=2)
    coordinator.write("cart-42", "+shoes", "client-1")
    replicas[2].up = False
    coordinator.write("cart-42", "+socks", "client-2")
    for versioned in coordinator.read("cart-42"):
        print(versioned)
```

### Go

```go
package main

import (
	"fmt"
	"time"
)

type VClock map[string]int64

func dominates(a, b VClock) bool {
	strictlyGreater := false
	keys := map[string]struct{}{}
	for k := range a {
		keys[k] = struct{}{}
	}
	for k := range b {
		keys[k] = struct{}{}
	}
	for k := range keys {
		av, bv := a[k], b[k]
		if av < bv {
			return false
		}
		if av > bv {
			strictlyGreater = true
		}
	}
	return strictlyGreater
}

type Versioned struct {
	Value string
	Clock VClock
}

type Replica struct {
	ID    string
	Up    bool
	store map[string][]Versioned
}

func NewReplica(id string) *Replica {
	return &Replica{ID: id, Up: true, store: map[string][]Versioned{}}
}

func (r *Replica) Put(key, value string, clock VClock) error {
	if !r.Up {
		return fmt.Errorf("%s unreachable", r.ID)
	}
	existing := r.store[key]
	survivors := existing[:0]
	for _, v := range existing {
		if !dominates(clock, v.Clock) {
			survivors = append(survivors, v)
		}
	}
	survivors = append(survivors, Versioned{Value: value, Clock: clock})
	r.store[key] = survivors
	return nil
}

func (r *Replica) Get(key string) ([]Versioned, error) {
	if !r.Up {
		return nil, fmt.Errorf("%s unreachable", r.ID)
	}
	return r.store[key], nil
}

type Coordinator struct {
	Replicas []*Replica
	W, R     int
}

func (c *Coordinator) Write(key, value, actor string) (int, error) {
	acked := 0
	clock := VClock{actor: time.Now().UnixNano()}
	for _, r := range c.Replicas {
		if err := r.Put(key, value, clock); err == nil {
			acked++
		}
	}
	if acked < c.W {
		return acked, fmt.Errorf("only %d/%d replicas acked", acked, c.W)
	}
	return acked, nil
}

func (c *Coordinator) Read(key string) ([]Versioned, error) {
	var all []Versioned
	responded := 0
	for _, r := range c.Replicas {
		vs, err := r.Get(key)
		if err != nil {
			continue
		}
		responded++
		all = append(all, vs...)
	}
	if responded < c.R {
		return nil, fmt.Errorf("only %d/%d replicas responded", responded, c.R)
	}
	var live []Versioned
	for i, v := range all {
		dominated := false
		for j, other := range all {
			if i != j && dominates(other.Clock, v.Clock) {
				dominated = true
				break
			}
		}
		if !dominated {
			live = append(live, v)
		}
	}
	return live, nil
}

func main() {
	replicas := []*Replica{NewReplica("A"), NewReplica("B"), NewReplica("C")}
	coordinator := &Coordinator{Replicas: replicas, W: 2, R: 2}
	if _, err := coordinator.Write("cart-42", "+shoes", "client-1"); err != nil {
		panic(err)
	}
	replicas[2].Up = false
	if _, err := coordinator.Write("cart-42", "+socks", "client-2"); err != nil {
		panic(err)
	}
	versions, err := coordinator.Read("cart-42")
	if err != nil {
		panic(err)
	}
	fmt.Println(versions)
}
```

A Rust implementation is a natural fourth choice for this pattern, since
production Dynamo-derived systems are frequently written in Rust today, but
it is omitted here because the borrow-checker-correct way to share mutable
replica state across a coordinator without introducing `Arc<Mutex<_>>`
boilerplate that would obscure the pattern's actual logic needs more space
than this entry's code budget allows, so it was not compiled for this entry.
Swift, Java, and Kotlin are omitted for the same reason of not adding a
materially different illustration of the mechanic once three languages
already show it.
