---
name: Consistent Hashing
slug: consistent-hashing
family: 12-data-storage
category: Data and Storage
aliases: [Ring Hashing, Karger Hashing, Hash Ring Partitioning]
first_described: "Karger, Lehman, Leighton, Panigrahy, Levine, Lewin 1997"
maturity: canonical
related: [sharding, load-balancer, cache-aside, leader-election, bloom-filter]
incompatible_with: []
verified: 2026-08-02
---

# Consistent Hashing

## 1. Name, aliases, and lineage

The canonical name is Consistent Hashing. It was introduced in David Karger,
Eric Lehman, F. Thomson Leighton, Rajmohan Panigrahy, Matthew Levine, and
Daniel Lewin, "Consistent Hashing and Random Trees. Distributed Caching
Protocols for Relieving Hot Spots on the World Wide Web," presented at the
29th Annual ACM Symposium on Theory of Computing (STOC), 1997 (confirmed via
Wikipedia's summary of the paper's title, authors, and venue,
https://en.wikipedia.org/wiki/Consistent_hashing, verified 2026-08-02). The
paper set out to solve request distribution across a changing population of
web caches without every client agreeing on the exact same server list at the
exact same moment, the problem later called cache coherence under churn.

Two of the original authors, Daniel Lewin and F. Thomson Leighton, went on to
found Akamai Technologies in 1998 and built the company's content-delivery
request-routing layer on the same idea (Wikipedia, same source, verified
2026-08-02). That lineage matters because it is the reason the pattern reads
as a caching and CDN idea in older material and as a database sharding idea in
newer material. It is the same construction serving two different resource
types, caches and shards, and the difference is only in what a bucket answers
for.

**Ring Hashing** is the informal name used in load-balancer and infrastructure
writing, describing the mental model directly, points placed on a circle. It
refers to the same technique. **Karger Hashing** appears in academic citation
chains as a shorthand for the original construction, crediting the first
author. Neither is a competing pattern, both are the same pattern named after
its shape or its inventor.

A separate, later technique with an overlapping goal is worth naming here so
it is never confused with this entry. Rendezvous hashing, also called highest
random weight hashing, achieves the same low-disruption property through a
completely different mechanism, and it is covered as a named alternative in
dimension 12 rather than as an alias, because the internal structure, a ring
versus a per-key scoring function over all nodes, is genuinely different.

## 2. Problem and context

A system needs to map a large, high-churn set of keys, cache entries, shard
identifiers, session identifiers, onto a smaller, changing set of nodes,
caches, database shards, load balancer backends, and it needs that mapping to
stay stable when the node set changes.

The naive approach is `node = hash(key) mod N`, where `N` is the current
number of nodes. This is cheap, uniform, and looks correct until `N` changes.
Adding or removing one node from a five-node pool changes the modulus from 5
to 6, and because the modulus operation depends on the exact value of `N`, the
node assignment for nearly every key flips, not just the keys that belonged to
the added or removed node. In a cache this means a near-total cache wipe at
the exact moment the system is under stress, typically because the node count
just changed due to a failure or a scale event, which is the worst possible
time for every request to become a cache miss. In a sharded database it means
a near-total data migration triggered by a single node joining or leaving.

The context that creates the need is precisely a fleet that changes size
routinely, through autoscaling, through failure and replacement, or through
deliberate rebalancing, combined with a mapping that is expensive to
invalidate wholesale, a cold cache, a resharding job, a reconnect storm
against session-affinious backends. Where the node set is fixed for the
lifetime of the system, modulo hashing is simpler and consistent hashing buys
nothing, see dimension 4.

A second, related context is client-side routing without a coordinator. Many
consistent hashing deployments, memcached client pools in particular, have no
central router at all. Every client independently computes which node a key
belongs to. For that to work, every client must reach the same answer from
the same, small amount of shared state, the node list, without communicating
with the others on every request. Consistent hashing gives that property
because the ring construction is a pure function of the node list and the
key, so any two clients holding the same node list compute the same node for
the same key with no coordination protocol at all.

## 3. Forces

- **Movement on membership change.** Favoured, and this is the entire reason
  the pattern exists. With `K` keys and `N` nodes, expected reassignment on
  adding or removing one node is close to `K / N` keys, not `K` keys. Modulo
  hashing sacrifices this completely.
- **Load balance across nodes.** Sacrificed in the naive, single-point-per-node
  form. A small number of ring points per node produces visibly uneven load,
  because the arc lengths between random points on a circle are not equal, and
  the largest gaps can be several times the average. Virtual nodes trade extra
  memory and lookup cost to recover this, see dimension 8.
- **Lookup cost.** Mildly sacrificed relative to modulo hashing. A binary
  search over a sorted ring of `O(N * v)` points, where `v` is virtual nodes
  per physical node, costs `O(log(N * v))` per lookup instead of `O(1)`.
  Negligible in absolute terms for realistic fleet sizes, and it is the
  largest per-request cost only in extremely latency-sensitive routing paths.
- **Coordination requirement.** Favoured. Because the mapping is a pure
  function of the node list and the key, no central coordinator is required
  for a client to compute the correct target, only agreement on the node list
  itself, which can be propagated far more cheaply than propagating a
  live routing decision per key.
- **Client skew tolerance.** Sacrificed relative to a fully coordinated router.
  If two clients hold different node lists, even briefly during a rollout,
  they compute different targets for the same key. For a cache this is a
  temporary miss. For a system that requires a single writer per key, this is
  a correctness hazard, see dimension 11.
- **Operational simplicity.** Mixed. Adding a node is simple, place its points
  and done. Handling permanent versus transient removal, replication, and
  hinted handoff on top of the base ring is where real systems, Dynamo and
  Cassandra among them, add substantial machinery that the base pattern alone
  does not provide.
- **Memory and metadata cost.** Sacrificed. The ring itself, plus virtual node
  bookkeeping, is metadata every client or router must hold and keep current,
  which is more state than a single integer modulus.

The honest summary is that consistent hashing trades a small, controllable
increase in lookup cost and metadata for a large, otherwise unavoidable
reduction in data movement on membership change, and it requires an explicit
extra construction, virtual nodes, to recover the load balance that modulo
hashing gets for free when the node set never changes.

## 4. Applicability and non-applicability

Reach for consistent hashing when the following hold.

- The set of nodes, caches, shards, or backends changes at runtime, through
  autoscaling, failure and replacement, or deliberate rebalancing, and it
  changes often enough that a full remap on every change is unacceptable.
- Clients or routers need to compute the target node independently, without a
  round trip to a central coordinator, and can tolerate briefly stale node
  lists during a rollout.
- Keys are numerous and the cost of a cache miss or a shard migration per key
  is real, so minimizing the fraction of keys that move on a topology change
  has direct, measurable payoff.
- The workload benefits from bounded, mechanical placement of replicas, the
  ring gives a natural definition of "the next N distinct nodes clockwise" for
  replica placement, which several production systems, Dynamo among them,
  build directly on top of the base ring.

Do NOT reach for consistent hashing in these cases, and the reason matters
more than the rule.

- **The node set is fixed for the system's operational lifetime.** A
  three-shard database that will never gain a fourth shard, or a fixed pool of
  worker processes sized once at deploy time, has no membership-change problem
  to solve. Modulo hashing is simpler, has perfectly even load with no virtual
  node tuning, and the entire mechanism this pattern adds is unearned
  complexity.
- **Perfectly even load matters more than movement minimization, and the node
  count is small.** With very few nodes, single-digit counts, even a
  well-tuned virtual node scheme shows visible variance, and a coordinator
  that tracks exact load per node and assigns explicitly will balance better.
  Consistent hashing approaches even load only in the limit of many virtual
  nodes and many keys.
- **A single, central router already exists and is not a bottleneck.** If
  every request already passes through one component that can hold an exact,
  up-to-date node list and consult it, plain modulo hashing behind that router
  works, and the router can migrate keys explicitly and gradually rather than
  by letting a hash function decide. The client-side, coordinator-free
  property that motivates consistent hashing is not being used.
- **Range queries are the primary access pattern.** Hashing, consistent or
  not, destroys key ordering. A workload that needs "give me all keys between
  A and M" needs range partitioning, not hash partitioning, and consistent
  hashing does not help that case at all, see dimension 12 for the
  range-partitioning alternative.
- **Strict, single-writer correctness is required across a membership
  change with no coordination window.** As dimension 3 states, two nodes with
  different views of the ring compute different owners for the same key. A
  system that cannot tolerate a brief period of divergent ownership during a
  topology change needs an explicit consensus-backed membership protocol on
  top of, or instead of, the base ring, see dimension 11.
- **The problem is actually load balancing traffic across a fixed backend
  pool for a single request type**, not partitioning data ownership. Weighted
  round robin or least-connections routing is the simpler, better-suited tool
  when there is no data affinity requirement to preserve.

## 5. Structure

Four participants, named by the role they play in the construction, not by a
generic class name.

- **HashSpace.** The fixed, ordered value space the ring is built over,
  conventionally the output range of the hash function treated as a circle,
  for example the unsigned 32-bit or 64-bit integers with the largest value
  wrapping back to zero.
- **Node.** A physical resource, a cache server, a database shard, a load
  balancer backend, that owns one or more points on the ring. A Node is
  identified by a stable label, a hostname, a shard id, an IP and port, whose
  hash determines where its point or points land.
- **VirtualNode (replica point).** One of several points placed on the ring
  for a single Node, computed by hashing the Node's label concatenated with a
  distinguishing suffix, `node-1#0`, `node-1#1`, and so on. Multiple
  VirtualNodes per Node are what recovers even load distribution, see
  dimension 8. A deployment with exactly one VirtualNode per Node is the
  degenerate, unevenly loaded case.
- **Key.** The item being placed, a cache key, a record's partition key, a
  session id. A Key's owner is found by hashing the Key into the same
  HashSpace and walking clockwise to the first VirtualNode encountered.

The relationship is a lookup, not an ownership hierarchy in the
object-oriented sense. The ring itself is normally represented as a sorted
map or sorted array from hash value to Node label, held identically by every
client or router that needs to answer "who owns this key."

## 6. ASCII structure diagram

```
                    HashSpace, a circle of values 0 .. 2^32-1

                              0 / 2^32
                                |
                    +-----------------------+
                    |                       |
              [B#2] o                       o [A#1]
                    |                       |
                    |     the ring          |
              [A#2] o                       o [C#1]
                    |                       |
                    |                       |
              [C#2] o                       o [B#1]
                    |                       |
                    +-----------------------+

  Legend
    [A#1], [A#2]   VirtualNodes for physical Node A (two replica points)
    [B#1], [B#2]   VirtualNodes for physical Node B
    [C#1], [C#2]   VirtualNodes for physical Node C

  A Key K hashes to a point on the circle. Its owner is the first
  VirtualNode found walking CLOCKWISE from K's position. Every position
  on the circle between two consecutive VirtualNodes belongs to the
  VirtualNode that follows it clockwise, so each physical Node owns the
  union of the arcs that precede each of its VirtualNodes.
```

## 7. Dynamics

The two operations that matter are a lookup and a membership change. Both are
pure functions of the current ring state, there is no message exchange
required to answer either question once the ring is held locally.

```
Lookup: which Node owns Key K

  Client                          Ring (sorted map: hash -> Node)
    |                                        |
    |-- hash(K) = h ----------------------->|
    |                                        |-- binary search for the
    |                                        |   smallest entry >= h
    |                                        |   (wrap to the first entry
    |                                        |    if h is past the last one)
    |<-- owning VirtualNode's Node label ----|
    |                                        |

Membership change: Node D joins

  Operator / autoscaler         Ring (shared, held by every client)
    |                                        |
    |-- insert VirtualNodes for D ---------->|
    |   (v points: hash(D#0) .. hash(D#v-1)) |
    |                                        |
    |         only the keys that now fall between D's new points
    |         and the point immediately clockwise of each move to D.
    |         every other key's owner is unchanged.
    |                                        |
    |-- (for a cache) D starts cold for -----|
    |    its newly owned keys, everyone      |
    |    else's cache stays warm             |
```

The property visible in the second diagram is the entire payoff of the
pattern. A join or a leave touches only the arcs adjacent to the changed
VirtualNodes, in expectation `K / N` keys out of `K`, not all of them. The
ring itself does not decide anything about data migration, replication, or
consistency, it only answers ownership. Real systems build a separate
protocol on top of the ring to actually move data to its new owner, see
dimension 9 for how Dynamo and Cassandra do this with hinted handoff and
anti-entropy repair rather than a synchronous migration on join.

## 8. Implementation variants

**Single point per node, the textbook minimum.** One VirtualNode per physical
Node. Simplest to reason about, and visibly unbalanced in practice, because
random points on a circle do not divide it into equal arcs. A useful
back-of-envelope fact, with `N` nodes the largest arc is expected to be
roughly `ln(N) / N` times the circle rather than `1 / N`, so load skew grows
with the log of the node count rather than shrinking. Almost never used
unmodified in production for that reason.

**Virtual nodes (replica points), the standard production form.** Each
physical Node is hashed into `v` points, commonly in the low hundreds. The
number of points determines the smoothing, more points means a load
distribution closer to uniform at the cost of more ring memory and a larger
sorted structure to search. Amazon's Dynamo paper describes exactly this
technique and explicitly frames the virtual node count as the tuning knob for
heterogeneity, letting a more capable physical machine hold proportionally
more virtual nodes than a smaller one, so capacity-aware placement falls out
of the same mechanism used for load smoothing.

**Bounded-load consistent hashing.** A variant that caps how far above the
average any single Node's load may go by skipping over an owner that is
already at its cap and continuing clockwise to the next candidate. Solves the
residual skew that even a large virtual node count cannot fully remove,
because virtual node counts smooth the expectation but not the worst case,
at the cost of extra bookkeeping of live load per Node and a more complex
lookup that may probe several candidates instead of one.

**Jump consistent hash.** A closed-form, table-free variant that computes a
bucket index directly from the key and the node count using a small
pseudorandom recurrence, with no ring, no virtual nodes, and effectively no
memory overhead. It gives the same minimal-movement property for the specific
case where nodes are numbered `0` to `N-1` and removal always happens from
the highest index, which fits a shard array far better than a general,
arbitrarily-named node pool, and it cannot directly express "remove node 3 of
7 while keeping 4 through 7." Chosen when the deployment already treats nodes
as a dense, numbered array rather than named machines.

**Multi-probe consistent hashing.** Instead of storing many virtual node
points per physical node, a small, fixed number of hash functions are applied
to the key itself at lookup time, and the closest resulting owner across
those probes is chosen. This trades ring memory for a few extra hash
computations per lookup, useful when the node count is large enough that even
a modest virtual-node ring becomes a meaningful memory cost per client.

**Language and library note.** Most production use of this pattern is through
a library rather than a hand-rolled ring, because the correctness of the
"first clockwise" search and the wraparound at the end of the space are easy
to get subtly wrong. `libketama` for memcached clients, and the partitioner
implementations inside Cassandra, DynamoDB-style systems, and Vitess are the
common reference implementations rather than something reimplemented per
project.

## 9. Known production uses

**Apache Cassandra, data partitioning.** Cassandra's own architecture
documentation states that "consistent hashing allows distribution of data
across a cluster to minimize reorganization when nodes are added or removed,"
and describes assigning partition-key hash values, computed with Murmur3, to
token ranges owned by nodes on the ring. DataStax, "Data Distribution and
Replication," Cassandra 3.0 documentation,
https://docs.datastax.com/en/cassandra-oss/3.0/cassandra/architecture/archDataDistributeHashing.html
verified 2026-08-02.

**Amazon Dynamo, partitioning with virtual nodes.** The Dynamo paper describes
using a variant of consistent hashing in which each physical node is assigned
to multiple points on the ring, virtual nodes, both to balance load across
heterogeneous hardware and to smooth the distribution of data across the
cluster on membership change. Giuseppe DeCandia, Deniz Hastorun, Madan
Jampani, Gunavardhan Kakulapati, Avinash Lakshman, Alex Pilchin, Swaminathan
Sivasubramanian, Peter Vosshall, Werner Vogels, "Dynamo. Amazon's Highly
Available Key-value Store," Proceedings of the 21st ACM Symposium on
Operating Systems Principles (SOSP), 2007, section 4.2, "Partitioning
Algorithm," https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf
verified 2026-08-02.

**Google Maglev, network load balancing.** Google's software network load
balancer, serving Google's production traffic including Search and Gmail
since 2008, uses consistent hashing so that connection-to-backend assignment
survives backend pool changes without breaking already-established
connections. Daniel E. Eisenbud, Cheng Yi, Carlo Contavalli, Cody Smith,
Roman Kononov, Eric Mann-Hielscher, Ardas Cilingiroglu, Bin Cheyney, Wentao
Shang, Jinnah Dylan Hosein, "Maglev. A Fast and Reliable Software Network
Load Balancer," 13th USENIX Symposium on Networked Systems Design and
Implementation (NSDI), 2016,
https://www.usenix.org/conference/nsdi16/technical-sessions/presentation/eisenbud
verified 2026-08-02.

**Memcached client pools, ketama.** Last.fm engineer Richard Jones, with
Christian Muehlhaeuser, wrote and open-sourced libketama in April 2007 to
replace naive modulo hashing across a memcached pool, because adding or
removing a memcached server previously remapped nearly every key and
effectively wiped the cache. Ketama hashes each server to 100 to 200 points on
a 32-bit ring, and it became the reference algorithm bundled into most
memcached client libraries afterward. Richard Jones, "libketama, a consistent
hashing algo for memcache clients," memcached mailing list announcement, 10
April 2007, https://lists.danga.com/pipermail/memcached/2007-April/003853.html
verified 2026-08-02.

**Akamai, content delivery request routing.** Akamai Technologies was founded
in 1998 by Daniel Lewin and F. Thomson Leighton, two of the authors of the
original 1997 consistent hashing paper, and the company's edge-server request
routing descends from the same construction the paper introduced to relieve
hot spots on the early web. Wikipedia contributors, "Consistent hashing,"
https://en.wikipedia.org/wiki/Consistent_hashing verified 2026-08-02, cited
here only for the founding and lineage fact, not as a source of technical
explanation.

## 10. Consequences

Positive.

- Membership changes move a small, bounded fraction of keys in expectation,
  `K / N` rather than nearly all `K` keys, which is the property that makes
  autoscaling and failure recovery survivable for a cache or a sharded store.
- Ownership lookups require no coordinator and no network round trip beyond
  holding the current node list, so many independent clients reach the same
  answer for the same key without a consensus protocol on the hot path.
- The ring gives a natural, mechanical definition of replica placement, "the
  next N distinct physical nodes walking clockwise," which several systems
  build directly on for replication without a separate placement algorithm.
- Heterogeneous node capacity is expressible for free, by assigning more
  virtual node points to a more capable physical machine, with no change to
  the lookup algorithm.
- The construction is a pure function of the node list and the key, which
  makes it straightforward to unit test and to reason about independently of
  the rest of the system.

Negative.

- Single-point-per-node placement is visibly unbalanced, and the fix, virtual
  nodes, adds memory proportional to node count times virtual nodes per node,
  and a lookup cost of `O(log(N * v))` instead of `O(1)`.
- Hashing destroys key ordering entirely, so consistent hashing offers no path
  to efficient range queries, and adding one later usually means adding a
  second, separate index rather than adapting the ring.
- The ring's correctness depends on every consumer agreeing on the same node
  list. Two clients with a stale versus a current view of the ring compute
  different owners for the same key, and closing that gap requires a
  membership propagation mechanism the base pattern does not itself provide.
- Even with virtual nodes, load imbalance is asymptotic, not exact. Real
  deployments still see meaningful skew unless bounded-load variants or a
  large virtual node count are used, and both cost something.
- The pattern solves ownership assignment, not data movement, replication, or
  consistency during a topology change. Systems that need those properties
  build substantial additional machinery on top of the ring, which is easy to
  underestimate when the ring itself looks simple.

## 11. Failure modes and misuse

**The single-point ring in production.** Symptom. One or two nodes in a small
fleet consistently receive two to three times the traffic or storage of the
others, and the imbalance does not go away as the fleet grows. Cause. One
VirtualNode per physical Node, so the arc-length variance inherent to random
points on a circle is never smoothed. Fix. Add virtual nodes, in the low
hundreds per physical node is a reasonable starting point, and measure the
resulting skew rather than assuming a fixed count is enough for every fleet
size.

**Divergent rings during a rollout.** Symptom. A brief window after a node
join or leave where some requests for the same key are served by the old
owner and some by the new owner, sometimes surfacing as duplicate cache
writes or, in a write path, as two different nodes believing they own a key
at once. Cause. Node list changes are propagated to clients or routers
asynchronously, and different processes update at different times. Fix.
Version the ring, and where correctness (not just cache freshness) depends on
a single owner, gate the transition through a coordination mechanism, a
membership service, a versioned configuration push with a barrier, rather
than letting each process pick up the new list on its own schedule.

**Silent load skew hidden by aggregate metrics.** Symptom. Fleet-wide CPU or
memory utilization looks healthy, but one node runs hot, drops connections, or
evicts more aggressively than the rest, and the aggregate dashboard never
shows it because it is averaged away. Cause. Consistent hashing's balance
guarantee is a statistical expectation over many keys, not a per-node
guarantee, and a workload with a small number of very hot keys can land
several of them on the same physical node by chance regardless of virtual
node count. Fix. Instrument per-node load, not only fleet-wide aggregates
(see dimension 16), and apply bounded-load consistent hashing or explicit hot
key splitting when a small number of keys account for most requests.

**Ring rebuilt from scratch instead of updated incrementally.** Symptom. A
routine node replacement, one node down, one node up, causes a much larger
data movement or cache invalidation than expected, closer to the naive
modulo-hashing case than the consistent-hashing case. Cause. Some
implementations regenerate the entire ring, and in doing so change hash seeds,
rehash all node labels with a different scheme, or otherwise produce a ring
that does not share most of its points with the previous one, defeating the
whole point of the pattern even though "consistent hashing" is technically in
use. Fix. Confirm the implementation updates the existing sorted structure by
inserting or removing only the changed node's points, and add a regression
test asserting that a single node join or leave moves close to `K / N` keys,
not close to `K` keys.

**Confusing consistent hashing with sticky sessions.** Symptom. A load
balancer is described as doing "consistent hashing for session affinity," but
a backend restart during a deploy still logs every user out at once. Cause.
The ring correctly minimizes remapping on a node count change, but a rolling
restart that replaces every node's identity (a new pod name or IP per
instance) is, from the ring's perspective, removing every old node and adding
every new one, the worst case rather than the best case. Fix. Give backends
stable identities across restarts where session affinity matters, or accept
that a full fleet identity change is outside what the pattern smooths, and
plan session draining separately.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Consistent hashing (ring, with virtual nodes) | Modulo hashing (`hash(key) mod N`) | Rendezvous / highest random weight hashing | Range partitioning | Static, coordinator-assigned sharding |
|---|---|---|---|---|---|
| Movement on membership change | Near-minimal, about `K / N` keys move | Worst case, nearly all keys move | Near-minimal, comparable to ring, no ring structure needed | Depends on where the split falls, can be minimal or large | Zero automatic movement, an operator or a rebalancer decides explicitly |
| Load balance across nodes | Good with sufficient virtual nodes, exact only asymptotically | Perfect, as long as `N` never changes | Good, and does not degrade with a small `N` the way a single-point ring does | Depends entirely on key distribution, can be very skewed | As good as the assignment algorithm makes it |
| Lookup cost | `O(log(N * v))`, a sorted-structure search | `O(1)`, a single modulus | `O(N)` per lookup, score every node | `O(log N)` over sorted range boundaries | `O(1)` to `O(log N)`, a table lookup |
| Coordination requirement | None beyond a shared node list | None beyond a shared `N` | None beyond a shared node list | Requires shared range boundaries | Requires a central assigner or metadata store |
| Range query support | None, hashing destroys order | None | None | Native, the whole point of the scheme | Depends on the assignment key, not inherent |
| Memory per client or router | Proportional to `N * v` points | Effectively none | Proportional to `N`, node list only | Proportional to number of range boundaries | Proportional to shard map size |
| Behaviour under a full fleet identity change (rolling restart with new identities) | Worst case, equivalent to a full remap | Worst case, equivalent to a full remap | Worst case, equivalent to a full remap | Not directly affected, boundaries are independent of node identity | Not directly affected, reassignment is explicit |
| Natural fit for replica placement | Strong, "next N distinct nodes clockwise" | None built in | None built in | Explicit range-owner replication, separate mechanism | Explicit, whatever the assigner encodes |

Reading of the table. Consistent hashing and rendezvous hashing solve the
same problem, minimal movement without coordination, through different
internal structures, and the choice between them is largely about lookup cost
at scale, a large sorted ring versus scoring every node on every lookup, not
about the guarantee itself. Range partitioning is the right tool the moment
range queries matter, at the direct cost of the even-distribution guarantee
this pattern provides. Static, coordinator-assigned sharding gives up the
coordinator-free property entirely in exchange for exact control over
placement, which is worth it when placement decisions are rare and each one
matters, migrations, compliance-driven data residency, and the like.

## 13. Related and incompatible patterns

- **Sharding.** The umbrella pattern this entry is one implementation
  strategy for. Consistent hashing answers the specific question "which shard
  owns this key, and how do I minimize movement when the shard count
  changes," while sharding as a pattern also covers range-based and
  directory-based assignment, which this entry treats as named alternatives
  rather than variants.
- **Load balancer.** Consistent hashing is one routing algorithm a load
  balancer can implement, chosen specifically when backend affinity for a
  given client or key matters and the backend pool changes over time.
  Maglev's use, see dimension 9, is exactly this composition.
- **Cache-aside.** Consistent hashing determines which cache node a key
  belongs to. Cache-aside determines what the application does on a hit or a
  miss against that node. The two compose directly, and the load-survival
  property this entry provides is specifically about not turning a topology
  change into a mass cache-aside miss storm.
- **Leader election.** A genuinely different problem, deciding which single
  process acts as leader for a resource, that is sometimes solved with the
  same ring construction, "the leader for key K is the first live node
  clockwise from K." This works for lightweight, best-effort leadership, but
  it is not a substitute for a consensus-backed leader election protocol
  where split-brain during ring divergence, see dimension 11, would be
  unacceptable.
- **Rendezvous hashing.** A substitute rather than a composition partner.
  Chosen instead of a ring when the node count is small enough that its
  `O(N)` lookup is cheap, and when avoiding the ring's memory overhead and
  wraparound-edge-case implementation risk matters more than raw lookup
  speed at very large `N`.
- **Vector clocks and read repair (as used by Dynamo-style stores).**
  Actively depends on this pattern rather than replacing it. Once consistent
  hashing has assigned N replica owners for a key, the replication and
  conflict-resolution machinery, hinted handoff, read repair, vector clocks,
  operates on top of that assignment. This pattern does not provide
  replication correctness on its own, only the placement the replication
  layer then uses.
- **Two-phase commit or distributed transactions across shards.** In tension
  with this pattern in practice, not incompatible in principle. A ring that
  rebalances keys on every membership change makes it harder to reason about
  which shards a multi-key transaction spans, because that answer can itself
  change mid-migration. Systems that need strict cross-shard transactions
  typically pin shard assignment far more rigidly than a live-rebalancing
  ring, closer to static, coordinator-assigned sharding from dimension 12.

## 14. Refactoring path in and out

Introducing the pattern into a system that currently uses modulo hashing or a
fixed node array.

1. Confirm the actual problem is membership churn, not just "we want
   sharding." If the node count genuinely never changes, stop here, this
   pattern is not earning its place, see dimension 4.
2. Pick a hash function with good avalanche behaviour and 32-bit or 64-bit
   output, Murmur3 and xxHash are common production choices, and confirm it
   is available consistently in every language or runtime that will compute
   ring positions, a mismatch here silently breaks the "every client agrees"
   property.
3. Build the ring as a sorted structure, hash value to node label, behind a
   single lookup function, `owner_of(key) -> node`, and route all existing
   `hash(key) mod N` call sites through it. At this point with one virtual
   node per physical node, correctness should already be verifiable, movement
   on a simulated node addition should already be close to `K / N`.
4. Add virtual nodes and re-measure the load distribution across a
   representative key sample. Tune the count for the target skew tolerance,
   there is no universally correct number, it depends on `N` and how uneven a
   distribution the workload can tolerate.
5. Add a node-list propagation mechanism if one does not already exist,
   because dimension 11's divergent-ring failure mode is inevitable without
   one. This can be as simple as a versioned configuration file pushed to
   every consumer, or as involved as a dedicated membership service.
6. If the pattern is being used for data ownership rather than only a cache,
   add the data movement step explicitly, do not assume the ring moves data,
   it only decides where data should be. Plan the migration or replication
   protocol as a separate piece of work.
7. Add the regression test from dimension 11, asserting expected movement on
   a simulated join or leave, so a future refactor that accidentally rebuilds
   the ring from scratch is caught immediately rather than discovered in
   production.

Removing the pattern when it stops earning its place. Signals include a node
count that has been stable for a long time with no roadmap to change it, or a
migration to a coordinator-driven architecture that already tracks exact
placement for other reasons.

1. Confirm nothing depends on the ring's replica-placement convenience,
   "next N nodes clockwise," dimension 13. If something does, that dependency
   needs its own explicit replacement first.
2. Freeze the current ring's assignment as a static map from key range or key
   hash bucket to node, snapshotting the existing placement rather than
   recomputing it, so the removal does not itself trigger a mass migration.
3. Replace the `owner_of(key)` lookup with a lookup into the static map.
4. Delete the virtual node generation and ring-maintenance code once nothing
   references it.
5. If the underlying reason for removal is a move to coordinator-assigned
   sharding, this is essentially "Replace Algorithm" from the refactoring
   family, swapping the ring's O(log N) computed lookup for an explicit
   table maintained by whatever service now owns placement decisions.

## 15. Testing and verification

Easier because of the pattern.

- The core lookup, `owner_of(key) -> node`, is a pure function of the ring
  state and the key, so it can be unit tested exhaustively with synthetic
  keys and a small, fixed node set, with no network or timing involved.
- Membership change behaviour is directly assertable. Build a ring, snapshot
  every key's owner, add or remove a node, recompute, and assert the fraction
  of keys that changed owner is close to `1 / N`. This is the single most
  valuable test for this pattern and it is cheap to write.
- Load distribution is directly measurable offline. Generate a large
  synthetic key sample, compute owner counts, and assert the standard
  deviation across nodes is within a chosen bound for a given virtual node
  count, which turns dimension 8's tuning decision into a repeatable,
  numeric check rather than a guess.

Harder because of the pattern.

- Divergent-ring behaviour, dimension 11's most serious failure mode, is a
  distributed-systems timing problem and does not show up in a single-process
  unit test. It needs a test setup that can simulate two or more processes
  holding different ring versions simultaneously.
- Hot-key skew, where a small number of keys concentrate on one node by
  chance rather than by systematic imbalance, is a statistical property that
  needs a realistic key distribution to surface, a uniform synthetic key
  sample will not reveal it.
- Correctness of the wraparound at the top of the hash space, the case where
  a key's hash is greater than every VirtualNode's position and ownership
  must wrap to the first entry, is a classic off-by-one source and needs an
  explicit boundary test rather than relying on random sampling to hit it.

Techniques that apply.

- **Property-based testing on the movement guarantee.** Generate random node
  sets and random join or leave events, and assert the moved-key fraction
  stays within a statistical bound of `1 / N` across many random trials, which
  is stronger evidence than a handful of hand-picked scenarios.
- **Golden-ring fixture.** A fixed hash function, a fixed node list, and a
  fixed expected owner for a set of representative keys, checked into the test
  suite, catches an accidental hash function change or seed change that would
  otherwise silently move every key without any test noticing, since each
  test in isolation might still pass "a plausible node" for its key.
- **Chaos test for the divergent-ring window.** Deliberately hold two ring
  versions in two test processes and assert the system's actual behaviour,
  a temporary cache miss for a cache, or an explicit conflict-resolution path
  for a data store, matches the documented tolerance rather than silently
  corrupting state.

## 16. Observability signals

The pattern hides load distribution behind a hash function, so the actual
per-node outcome has to be measured directly or an imbalance is invisible
until a node falls over.

What to record.

- A per-node counter or gauge of keys owned, or bytes stored, or requests
  routed, labelled by physical node, refreshed on every ring change. This is
  the primary signal, aggregate fleet metrics hide exactly the skew this
  pattern is supposed to bound.
- A counter of ring versions or node-list changes over time, so an
  unexpectedly frequent churn rate, which directly drives cache miss rate and
  data movement, is visible as its own trend rather than only inferred from
  downstream symptoms.
- A histogram or gauge of "fraction of keys that changed owner" on each
  membership change, computed from before and after snapshots where
  feasible, which turns the pattern's central guarantee into a monitored
  number rather than an assumption.
- For deployments where virtual node count is tuned, a periodic measurement
  of the coefficient of variation across node load, so a drift toward
  imbalance as the fleet grows past the size the virtual node count was tuned
  for is caught before it becomes an incident.
- For any deployment where different consumers might hold different ring
  versions, a way to detect version skew, a version number attached to
  routing decisions, logged and compared, is far cheaper than debugging a
  live divergence after the fact.

A healthy instance on a dashboard. Per-node load counters track each other
within a small, expected band, and that band does not widen as the fleet
scales. Ring version changes correlate one-to-one with known deploys, scale
events, or failures, never appearing unexplained. The moved-key fraction on
each change stays close to `1 / N` and does not creep toward the full
remapping value characteristic of the naive modulo approach.

A failing instance. One node's load counter climbs steadily away from the
rest with no corresponding change in the ring, which points at a hot key or
a small set of hot keys landing on that node rather than at a ring bug, see
dimension 11. Or the moved-key fraction on a routine node replacement
approaches 100 percent instead of `1 / N`, which is the ring-rebuilt-from-
scratch failure mode from dimension 11 and should be treated as a regression,
not tuned around. Or ring version skew is detected across consumers for an
extended window rather than briefly during a rollout, which points at a
broken or stalled node-list propagation mechanism rather than an ordinary,
short-lived divergence.

## 17. Security and privacy implications

The base pattern is close to silent on security, and the genuine implications
appear specifically at the boundary where the node list, and therefore the
ring, is influenced by something outside the operator's direct control.

**Node list poisoning.** If the mechanism that adds nodes to the ring, service
discovery, an autoscaler, a plugin registration path, can be influenced by an
attacker, an attacker-controlled node can be inserted into the ring and will
then legitimately receive a share of traffic or data proportional to its
virtual node count, exactly as any other node would. This is not a flaw
specific to consistent hashing, but the pattern's design means a poisoned
node is not a marginal anomaly, it is treated as a fully legitimate owner for
whatever keys hash into its arcs. Fix by authenticating node registration and
by treating the node-list source as a trust boundary, the same way any
service discovery mechanism should be treated.

**Key targeting through hash prediction.** If the hash function or the node
labeling scheme is predictable and the key space is at least partly
attacker-chosen, for example a user-controlled cache key or a user-supplied
partition key, an attacker can choose inputs that concentrate load onto a
specific node, a targeted, low-volume denial of service against one shard
rather than the whole fleet, which is harder to detect than a broad-spectrum
flood because aggregate traffic and load metrics can look entirely normal.
Fix by keying the hash with a server-side secret or salt when the key space
includes attacker-influenced input, so an outside party cannot predict which
physical node a chosen key will land on, and by applying the per-node load
monitoring from dimension 16, which is the direct detection mechanism for
this specific attack shape.

**Data residency and locality leakage.** Because ring placement is a
deterministic function of a key's hash, and because operational tooling
commonly logs which physical node served a given key for debugging, the
node-to-key mapping can incidentally reveal information correlated with the
key itself, a customer identifier or tenant identifier that happens to be
part of the partition key, if node placement correlates with a geography or a
compliance boundary. Where data residency requirements exist, this needs an
explicit constraint on top of the base pattern, pinning certain key ranges or
certain tenants to specific, compliant physical nodes, rather than trusting
the hash function to respect a boundary it has no knowledge of.

The pattern has no privacy implication of its own beyond these composition
effects, it does not itself store, transmit, or expose key contents, only the
routing decision for where a key's data lives or where a request for it
should go.

## 18. References

1. David Karger, Eric Lehman, F. Thomson Leighton, Rajmohan Panigrahy, Matthew
   Levine, Daniel Lewin. "Consistent Hashing and Random Trees. Distributed
   Caching Protocols for Relieving Hot Spots on the World Wide Web,"
   Proceedings of the 29th Annual ACM Symposium on Theory of Computing (STOC),
   1997. Cited via Wikipedia contributors, "Consistent hashing," summary of
   title, authors, and venue, https://en.wikipedia.org/wiki/Consistent_hashing
   verified 2026-08-02. Source for dimension 1's origin claim and dimension 9's
   Akamai founding lineage.
2. DataStax. "Data Distribution and Replication," Apache Cassandra 3.0
   documentation,
   https://docs.datastax.com/en/cassandra-oss/3.0/cassandra/architecture/archDataDistributeHashing.html
   Verified 2026-08-02. Source for the Cassandra production use in dimension
   9, quoted directly.
3. Giuseppe DeCandia, Deniz Hastorun, Madan Jampani, Gunavardhan Kakulapati,
   Avinash Lakshman, Alex Pilchin, Swaminathan Sivasubramanian, Peter Vosshall,
   Werner Vogels. "Dynamo. Amazon's Highly Available Key-value Store,"
   Proceedings of the 21st ACM Symposium on Operating Systems Principles
   (SOSP), 2007, section 4.2, "Partitioning Algorithm."
   https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf
   Verified 2026-08-02, existence and hosting confirmed live. Source for the
   virtual node and heterogeneity claims in dimensions 8 and 9.
4. Daniel E. Eisenbud, Cheng Yi, Carlo Contavalli, Cody Smith, Roman Kononov,
   Eric Mann-Hielscher, Ardas Cilingiroglu, Bin Cheyney, Wentao Shang, Jinnah
   Dylan Hosein. "Maglev. A Fast and Reliable Software Network Load
   Balancer," 13th USENIX Symposium on Networked Systems Design and
   Implementation (NSDI), 2016.
   https://www.usenix.org/conference/nsdi16/technical-sessions/presentation/eisenbud
   Verified 2026-08-02. Source for the Maglev production use in dimension 9.
5. Richard Jones. "libketama, a consistent hashing algo for memcache
   clients," memcached mailing list announcement, 10 April 2007.
   https://lists.danga.com/pipermail/memcached/2007-April/003853.html
   Verified 2026-08-02. Source for the ketama production use in dimension 9
   and the 100 to 200 points per server figure in dimension 8.
6. Wikipedia contributors. "Rendezvous hashing."
   https://en.wikipedia.org/wiki/Rendezvous_hashing Verified 2026-08-02. Used
   only to confirm rendezvous hashing as a distinct named technique for
   dimensions 1 and 12, not as a source of technical explanation.

## Code examples

Three languages chosen for genuinely different idiomatic shapes. Go shows the
sorted-slice-plus-binary-search form most production ring libraries use
internally. Python shows the same construction with the standard library's
`bisect` module doing the search, close to how a quick internal tool would be
written. Rust shows an ordered `BTreeMap`, which gives the sorted-structure
lookup for free from the standard library rather than hand-rolling a binary
search. Java and TypeScript are omitted from the runnable examples because
the construction is identical in shape to the Go and Python versions, a
hashed sorted structure plus a "first entry at or after this value, wrapping"
lookup, and a third near-identical restatement would not add a genuinely
different idiom.

### Go

```go
package main

import (
	"crypto/sha1"
	"fmt"
	"sort"
)

type Ring struct {
	points []uint32
	owners map[uint32]string
}

func hash32(s string) uint32 {
	h := sha1.Sum([]byte(s))
	return uint32(h[0])<<24 | uint32(h[1])<<16 | uint32(h[2])<<8 | uint32(h[3])
}

func NewRing(nodes []string, virtualPerNode int) *Ring {
	r := &Ring{owners: make(map[uint32]string)}
	for _, node := range nodes {
		for i := 0; i < virtualPerNode; i++ {
			p := hash32(fmt.Sprintf("%s#%d", node, i))
			r.points = append(r.points, p)
			r.owners[p] = node
		}
	}
	sort.Slice(r.points, func(i, j int) bool { return r.points[i] < r.points[j] })
	return r
}

func (r *Ring) OwnerOf(key string) string {
	if len(r.points) == 0 {
		return ""
	}
	h := hash32(key)
	i := sort.Search(len(r.points), func(i int) bool { return r.points[i] >= h })
	if i == len(r.points) {
		i = 0
	}
	return r.owners[r.points[i]]
}

func main() {
	ring := NewRing([]string{"A", "B", "C"}, 100)
	for _, k := range []string{"user:1", "user:2", "session:abc"} {
		fmt.Println(k, "->", ring.OwnerOf(k))
	}
}
```

### Python

```python
import bisect
import hashlib


def hash32(value: str) -> int:
    digest = hashlib.sha1(value.encode()).digest()
    return int.from_bytes(digest[:4], "big")


class Ring:
    def __init__(self, nodes: list[str], virtual_per_node: int = 100):
        self._owners: dict[int, str] = {}
        for node in nodes:
            for i in range(virtual_per_node):
                point = hash32(f"{node}#{i}")
                self._owners[point] = node
        self._points = sorted(self._owners)

    def owner_of(self, key: str) -> str:
        if not self._points:
            raise ValueError("ring has no nodes")
        h = hash32(key)
        idx = bisect.bisect_left(self._points, h)
        if idx == len(self._points):
            idx = 0
        return self._owners[self._points[idx]]


if __name__ == "__main__":
    ring = Ring(["A", "B", "C"], virtual_per_node=100)
    for key in ["user:1", "user:2", "session:abc"]:
        print(key, "->", ring.owner_of(key))
```

### Rust

```rust
use std::collections::hash_map::DefaultHasher;
use std::collections::BTreeMap;
use std::hash::{Hash, Hasher};

fn hash32(value: &str) -> u32 {
    let mut hasher = DefaultHasher::new();
    value.hash(&mut hasher);
    (hasher.finish() & 0xFFFF_FFFF) as u32
}

struct Ring {
    points: BTreeMap<u32, String>,
}

impl Ring {
    fn new(nodes: &[&str], virtual_per_node: u32) -> Self {
        let mut points = BTreeMap::new();
        for node in nodes {
            for i in 0..virtual_per_node {
                let key = format!("{node}#{i}");
                points.insert(hash32(&key), node.to_string());
            }
        }
        Ring { points }
    }

    fn owner_of(&self, key: &str) -> Option<&str> {
        let h = hash32(key);
        self.points
            .range(h..)
            .next()
            .or_else(|| self.points.iter().next())
            .map(|(_, node)| node.as_str())
    }
}

fn main() {
    let ring = Ring::new(&["A", "B", "C"], 100);
    for key in ["user:1", "user:2", "session:abc"] {
        println!("{key} -> {:?}", ring.owner_of(key));
    }
}
```
