---
name: CAP Theorem
slug: cap-theorem
family: 04-principles-and-laws
category: Principle
aliases: [Brewer's Theorem, Brewer's Conjecture, CAP Trade-off]
first_described: "Brewer 2000 (conjecture), Gilbert and Lynch 2002 (proof)"
maturity: canonical
related: [pacelc, quorum-consensus, eventual-consistency, saga, circuit-breaker]
incompatible_with: []
verified: 2026-08-02
---

# CAP Theorem

## 1. Name, aliases, and lineage

The canonical name is the CAP theorem, sometimes written Brewer's theorem after
the person who first stated it. It began life as a conjecture, not a proof. Eric
Brewer, then a professor at UC Berkeley and the founder of Inktomi, presented it
as a keynote at the ACM Symposium on Principles of Distributed Computing (PODC)
2000, a talk whose recorded title concerned building resilient distributed
systems, arguing that a networked
shared-data system can hold at most two of three properties at once, strong
consistency, high availability, and tolerance to network partitions
([Brewer 2012, "CAP Twelve Years Later. How the 'Rules' Have Changed,"
IEEE Computer 45(2), pp. 23-29, DOI 10.1109/MC.2012.37](https://sites.cs.ucsb.edu/~rich/class/cs293b-cloud/papers/brewer-cap.pdf),
verified 2026-08-02, which recounts the substance of the 2000 keynote).

Two years later Seth Gilbert and Nancy Lynch of MIT gave the conjecture a formal
proof, in an asynchronous network model with an atomic read and write register,
and published it as Seth Gilbert and Nancy Lynch, "Brewer's Conjecture and the
Feasibility of Consistent, Available, Partition-Tolerant Web Services," ACM
SIGACT News, volume 33, issue 2, 2002, pages 51-59, DOI 10.1145/564585.564601
([ACM Digital Library record](https://dl.acm.org/doi/10.1145/564585.564601),
verified 2026-08-02). That is the paper that turned the conjecture into a
theorem with a citable proof, and it is the paper most engineers mean when they
say "the CAP paper," even though the idea predates it by two years and belongs
to Brewer.

The letters stand for Consistency, Availability, and Partition tolerance, and
each word carries a precise, narrower meaning inside the theorem than it carries
in ordinary engineering conversation, which is the single biggest source of
confusion around this pattern.

- **Consistency** in CAP means linearizability. Every read that completes after
  a write has completed must return that write's value or a later one, as if
  there were only one copy of the data and operations happened one at a time in
  real-time order. This is a much stronger guarantee than the C in ACID, which
  is about application-level integrity constraints (foreign keys, invariants),
  not about how fast replicas converge.
- **Availability** in CAP means every request to a non-failing node must
  eventually receive a non-error response, with no requirement on how fast. The
  formal proof does not put a time bound on this; a later result strengthens it
  by adding one, described in dimension 8.
- **Partition tolerance** means the system continues to operate despite an
  arbitrary number of messages being dropped or delayed between nodes by the
  network. It is not something a system chooses to have or not have. A network
  that spans more than one host, one process, or one availability zone will
  eventually drop or delay a message, so partition tolerance is a property of
  the physical world the system runs in, not a design decision.

Brewer revisited his own conjecture a decade later and pushed back on the
"pick two of three" framing that had become the popular shorthand, calling it
"misleading" because it "over-simplifies the tensions among properties," since
in practice partitions are rare, and outside of a partition a system can, and
usually does, offer both consistency and availability at once
(Brewer 2012, cited above, p. 23). The theorem only forces a choice while a
partition is actually happening. That correction matters enough that dimension
4 is built entirely around it.

## 2. Problem and context

A system holds one piece of mutable state that more than one machine can read
and write, and those machines are connected by a network that is not perfectly
reliable. The concrete situation looks like this in a real codebase, a
key-value store, a session table, a shopping cart, a leader-election flag, or a
counter is replicated across two or more nodes so the system survives the loss
of any one node and so reads do not all hit one machine. Then a network link
between two of those nodes drops packets, times out, or partitions the cluster
into two groups that can each still talk to their own clients but cannot talk to
each other.

At that moment the system that received a write on one side of the partition
faces an unavoidable choice about the read that arrives on the other side of the
partition, for the same key, while the partition is still up. It can refuse to
answer the read (or the write) until the partition heals, which preserves the
guarantee that every read reflects every prior write, at the cost of turning
away a live, healthy node's request. Or it can answer the read using whatever
value that side of the partition currently has, which keeps the system
answering requests, at the cost of possibly returning stale data or accepting a
write that conflicts with one accepted on the other side.

The context that makes this a genuine, unavoidable trade-off, rather than an
engineering problem with a clever fix, has three parts.

- The data is **replicated across nodes that can be separated by a network
  fault**, not held on a single machine, and not held on a single machine with
  a warm standby that is only ever read after a controlled failover.
- The system must **keep serving requests during the partition**, which is
  itself a real design goal, not a hypothetical. A payment gateway, a
  distributed lock, or an inventory counter each has a real cost to going
  silent.
- The workload includes **writes**, not only reads. A system that never
  accepts a write cannot violate consistency, so CAP tension is specifically
  about what a node does when a write or a conflicting read arrives during a
  partition.

Outside that context the "theorem" has nothing to say. A single-node database
with no replication is not choosing between C and A, because it has no P to
worry about; it is simply unavailable when its one node is down, and perfectly
consistent because there is only ever one copy. See dimension 4 for the full
non-applicability list.

## 3. Forces

- **Correctness under concurrency.** Favoured by the CP choice. When the system
  refuses requests it cannot safely answer, no client ever observes a stale or
  conflicting value, which is what most people mean by "the database told me
  the truth."
- **Request latency and uptime as observed by the caller.** Favoured by the AP
  choice. When the system always answers, callers never see an error or a
  timeout caused by internal replica disagreement, only by their own network
  path to the node they happened to reach.
- **Operability during a real incident.** In tension both ways. A CP system
  that goes read-only or fully unavailable during a partition is easy to reason
  about, nothing wrong happens, only nothing happens, but an operator staring
  at a 5xx storm still has to explain why. An AP system that keeps answering
  hides the incident from callers but pushes the hard part, reconciling
  divergent writes, into a later merge step that an operator (or application
  code) must eventually run.
- **Business semantics of the data.** This is the force that actually decides
  which side to pick, and it is the one CAP itself is silent about. Money moving
  between two accounts wants correctness over uptime. A social media like
  counter, a product view count, or a session cache wants uptime over exactness.
  The theorem gives you the axis; it never tells you where your workload sits
  on it.
- **Cost of reconciliation.** Sacrificed by the AP choice and largely avoided by
  the CP choice. Choosing availability during a partition defers a real cost,
  someone has to write, test, and operate a conflict-resolution strategy (last
  writer wins, vector clocks, CRDTs, application-level merge) for every value
  that can diverge. That machinery is not optional plumbing; it is the actual
  price of the A in CAP.
- **Read and write latency in the normal case, no partition present.** CAP is
  silent on this force entirely, which is precisely the gap Daniel Abadi's
  PACELC extension closes, covered in dimension 8. A system can be CP under CAP
  and still trade consistency for lower everyday latency when nothing is
  broken.

## 4. Applicability and non-applicability

### When CAP genuinely applies

- Designing or choosing a **distributed data store** that replicates writable
  state across more than one node connected by a network, a key-value store, a
  wide-column store, a document store, a distributed cache, a distributed lock
  service, a consensus-backed configuration store.
- Deciding **what a replica should do the instant it cannot reach a quorum or a
  peer**, answer locally and stale, or refuse and wait.
- Reasoning about **why a managed database advertises a specific consistency
  model** ("eventually consistent," "strongly consistent," "session
  consistent") and what that model costs during a real network fault.
- Evaluating a **multi-region deployment**, where cross-region links are the
  single most likely partition point in the whole system, far more likely than
  a same-rack partition.

### When CAP does not apply, and why

- **A single-node database.** There are no replicas to disagree, so there is
  nothing for consistency and availability to trade off against; the only
  question is whether the one node is up, which is a plain reliability
  question, not a CAP question.
- **A system with no writes**, a read-only cache or a static content store
  fronted by a CDN. Consistency in CAP's sense is a property of the ordering
  between writes and reads. With no writes after the initial load, every replica
  serves the same immutable value forever and there is no consistency to lose.
- **In-process or single-datacenter shared memory with no network between the
  writers**, for example two threads sharing a mutex-guarded map in one process.
  That is a concurrency problem (see Producer-Consumer, Readers-Writers), not a
  partition problem, because there is no network link that can drop a message.
- **The steady-state (no-partition) latency question**, "should this read hit
  the primary or a follower for speed." That is a real and important question,
  but it is not what the theorem is about; reach for PACELC (dimension 8)
  instead, which explicitly covers the latency-versus-consistency trade-off
  that exists even when the network is perfectly healthy.
- **ACID transaction isolation levels** inside a single database engine, for
  example choosing `READ COMMITTED` versus `SERIALIZABLE` in PostgreSQL. Those
  levels govern anomalies between concurrent transactions on one copy of the
  data; CAP's C is about agreement between multiple copies of the data across a
  network.
- **"We need CA."** A frequently repeated but incoherent request. Gilbert and
  Lynch's proof is specifically that no algorithm can guarantee both C and A
  once a partition is possible, and any networked system spanning more than one
  process eventually experiences one, so a system said to be "CA" is really
  either a single-node system (where CAP does not apply, see above) or a
  distributed system that has simply not yet had its unavailability-during-a-
  partition moment (Brewer 2012, cited above, states outright that "the 2-of-3
  formulation... was always misleading" for exactly this reason, and that
  three properties can be simultaneously offered outside of a partition,
  p. 23).

## 5. Structure

CAP is not a design pattern with instantiable participants like Factory Method;
it is a property of a system's behaviour under a specific fault. Its
"structure" is the arrangement of the actors whose interaction the theorem
constrains.

- **Node.** A single process holding a copy, or a partial copy via sharding, of
  the replicated state. In the formal proof, nodes are modelled as asynchronous
  state machines with unbounded local processing and no shared clock.
- **Network link.** The channel between any two nodes. The theorem's partition
  assumption is that any link, or any subset of links, can silently drop
  messages for an unbounded period, and neither side of the link can
  distinguish "the peer is slow" from "the peer is unreachable" from
  "the message was dropped," which is the fundamental limitation the FLP
  impossibility result (Fischer, Lynch, Paterson 1985) already establishes for
  asynchronous consensus and CAP inherits.
- **Client, or caller.** The party issuing a read or a write to some node and
  observing the response (or its absence) as the externally visible behaviour
  the C and A properties are defined over.
- **Coordinator (in quorum-based designs).** The node that receives a client
  request and fans it out to the other replicas, waiting for a configured
  number of acknowledgements (the read quorum R or the write quorum W) before
  answering the client. This is not part of the abstract theorem but is the
  concrete mechanism almost every production CP or tunable system uses to
  decide whether it can safely answer during degraded connectivity, and it is
  the mechanism the code in dimension 6 through 9 demonstrates directly.
- **Reconciler, or anti-entropy process (in AP designs).** The background process
  that detects and resolves divergent copies once a partition heals, a Merkle
  tree comparison, a read-repair pass, or a CRDT merge. It is not present at
  all in a CP design because a CP design never lets copies diverge in the first
  place.

## 6. ASCII structure diagram

```
                      +-------------------+
                      |      Client        |
                      +----------+---------+
                                 |
                          write(key, val)
                                 |
                                 v
+-----------------------------------------------------------------+
|                          Replica set                            |
|                                                                  |
|   +----------+        +----------+        +----------+          |
|   | Node A   | <----> | Node B   | <----> | Node C   |          |
|   | (coord.) |        |          |        |          |          |
|   +----+-----+        +----+-----+        +----+-----+          |
|        |                    |                   |                |
|        |   inter-node links (can drop or delay) |                |
|        +-------------X------+                   |                |
|              partition here divides A|B from C   |                |
+-----------------------------------------------------------------+

  Majority side (A, B). reaches quorum (2 of 3) -> can serve CP writes
  Minority side (C).    cannot reach quorum      -> CP node refuses;
                                                     AP node serves stale
```

## 7. Dynamics

The diagram below traces one write and one read arriving on opposite sides of a
partition, for both the CP and the AP response, using a three-node,
majority-quorum replica set as the concrete instance. This is the exact shape
the code in dimensions 8 and 9 implements and runs.

```
Before partition. A, B, C all hold value=100, version=1

Partition opens, isolating C from {A, B}.

  Client -> A. write(key, 200)
    A is the coordinator. A can reach B (majority. A+B = 2 of 3).
    CP mode. needs quorum (2). A + B ack. Write ACCEPTED. version=2.
    AP mode. needs 1. A acks locally regardless. Write ACCEPTED. version=2.
    Either way, A and B now hold value=200, version=2. C is unaware.

  Client -> C. read(key)
    C is isolated; it can only reach itself (1 of 3, no quorum).
    CP mode. C REFUSES the read (or the write), returns an error or a
             timeout, because it cannot prove its local value is current.
    AP mode. C ANSWERS from its own copy. value=100, version=1 (STALE).

Partition heals.

  CP system. nothing to reconcile. C never diverged because it refused
             to accept writes or answer reads without quorum.
  AP system. C now anti-entropies against A/B, discovers version=1 < 2,
             and adopts value=200 (last-writer-wins), or, if C ALSO
             accepted a local write at version 2 during the partition,
             the two version-2 values conflict and must be merged by a
             CRDT rule or surfaced to the application.
```

## 8. Implementation variants

- **Strict CP via synchronous majority quorum.** A write is only acknowledged
  after a strict majority (`N/2 + 1`) of replicas confirm it, and a read is
  only answered after confirming with a majority too, so read and write
  quorums always overlap by at least one node and a stale read is provably
  impossible. This is how etcd and Consul implement their key-value store, both
  built on the Raft consensus algorithm (Diego Ongaro and John Ousterhout, "In
  Search of an Understandable Consensus Algorithm," USENIX ATC 2014,
  [raft.github.io](https://raft.github.io/raft.pdf), verified 2026-08-02, which
  is a leader-based majority-quorum protocol whose write path etcd exposes
  directly).
- **Tunable per-request quorum.** Rather than fixing CP or AP for the whole
  system, the client chooses a consistency level per read and per write.
  Apache Cassandra's consistency levels (`ONE`, `QUORUM`, `LOCAL_QUORUM`,
  `EACH_QUORUM`, `ALL`) let one call ask for AP-style speed (`ONE`) and the
  next call, on the same cluster and the same table, ask for CP-style
  guarantees (`QUORUM` on both read and write, so `R + W > N`)
  ([DataStax, "How is the consistency level configured?"](https://docs.datastax.com/en/cassandra-oss/3.0/cassandra/dml/dmlConfigConsistency.html),
  verified 2026-08-02). This variant does not resolve the CAP trade-off, it
  moves the decision point from "which database do we buy" to "which call site
  needs which guarantee," which is usually a better place for it to live.
- **AP with eventual convergence via version vectors and read repair.** Every
  write is accepted locally regardless of what other replicas can currently be
  reached. Divergent versions of the same key are detected using vector clocks
  attached to each write, surfaced to the application (or to a
  last-writer-wins policy) at read time, and repaired opportunistically in the
  background. This is the design Amazon's Dynamo paper introduced for its
  internal key-value store and is the direct ancestor of Cassandra, Riak, and
  Voldemort's replication layer (Giuseppe DeCandia et al., "Dynamo. Amazon's
  Highly Available Key-value Store," SOSP 2007, pp. 205-220,
  [amazon.science](https://www.amazon.science/publications/dynamo-amazons-highly-available-key-value-store),
  verified 2026-08-02).
- **AP with automatic, order-independent merge via CRDTs.** Instead of
  detecting a conflict and asking the application (or a human) to pick a
  winner, the data type itself is designed so that any two divergent replicas
  merge deterministically into the same result no matter the order updates
  arrive in, for example a grow-only counter that merges by taking the maximum
  per-replica count, or a last-writer-wins register that merges by comparing
  timestamps. Redis's active-active geo-replication (CRDTs) and Riak's data
  types both build on this variant.
- **CP with an external fencing or consensus layer bolted onto an otherwise AP
  store.** Rather than rebuilding the whole storage engine as CP, a
  lightweight consensus service (etcd, ZooKeeper, or a leader-election API)
  is used only to elect a single writer or to fence stale writers out, while
  the bulk read and write path stays on a simpler, faster AP-style store. This
  is the shape most "leader election plus a fast data plane" architectures take.
- **Latency-aware CP, the PACELC refinement.** Daniel Abadi observed that the
  CP-versus-AP choice only describes what happens during an actual partition,
  and that most systems spend nearly all their time NOT partitioned, during
  which there is a second, separate trade-off between consistency and latency
  that CAP says nothing about. His PACELC formulation states it directly, "if
  there is a partition (P), how does the system trade off availability and
  consistency (A and C); else (E), when the system is running normally in the
  absence of partitions, how does the system trade off latency (L) and
  consistency (C)" (Daniel J. Abadi, "Consistency Tradeoffs in Modern
  Distributed Database System Design. CAP is Only Part of the Story," IEEE
  Computer 45(2), 2012, pp. 37-42, DOI 10.1109/MC.2012.33,
  [dl.acm.org](https://dl.acm.org/doi/10.1109/mc.2012.33), verified
  2026-08-02). Google Spanner is PC/EC, consistent under a partition (it
  refuses availability rather than serve stale data) and consistent in the
  normal case too (it pays a synchronous commit-wait latency, bounded by the
  TrueTime API's clock uncertainty, to guarantee external consistency; James
  C. Corbett et al., "Spanner. Google's Globally-Distributed Database," OSDI
  2012, [usenix.org](https://www.usenix.org/system/files/conference/osdi12/osdi12-final-16.pdf),
  verified 2026-08-02). Cassandra with `ONE` and `ONE` is PA/EL, available under
  a partition, low-latency normally, consistency sacrificed both times.

## 9. Known production uses

- **Amazon DynamoDB and the original Dynamo.** Designed explicitly as an AP
  system, "Dynamo targets applications that need an 'always writeable' data
  store where no updates are rejected due to failures or concurrent writes,"
  choosing availability over strict consistency by design, using vector clocks
  and read repair to reconcile divergent versions (DeCandia et al. 2007, cited
  above, section 2 and 4.4). This paper is also widely credited as the direct
  design ancestor of Cassandra, Riak, and Voldemort.
- **Google Spanner.** Designed as a CP system that additionally minimises the
  latency cost of that choice using the TrueTime API, a globally synchronised
  clock with a bounded uncertainty interval, so that externally consistent
  distributed transactions are possible across datacenters without sacrificing
  availability more than strictly necessary during a genuine partition
  (Corbett et al. 2012, cited above, abstract and section 1).
- **Apache Cassandra.** A tunable system, per replica-set consistency level, but
  ships with `ONE` reads and `ONE` writes as historically common defaults in
  many client configurations, which puts it firmly on the AP side of the
  spectrum unless the operator explicitly raises the consistency level to
  `QUORUM` on both reads and writes; the tunable model itself is documented as
  a per-operation trade-off between how many replicas need to respond and how
  available the operation stays if some of them cannot (DataStax
  documentation, cited above).
- **etcd.** Built directly on the Raft consensus algorithm and documented as
  providing linearizable reads and writes by requiring a leader with a
  majority quorum; it is the canonical example of a CP key-value store used as
  the coordination backbone for Kubernetes, where losing a minority of etcd
  nodes must never let the cluster observe two different "current" states of
  the same object (Ongaro and Ousterhout 2014, cited above, describing the
  majority-quorum leader-based replication Raft, and thus etcd, implements).
- **MongoDB.** Ships as a CP-leaning system by default, with the default write
  concern and read concern, a MongoDB replica set becomes unavailable for
  writes on the primary's side of a partition once it cannot see a majority of
  voting members, specifically to avoid serving stale or divergent data,
  matching its classification as a CP system in comparative surveys of NoSQL
  consistency models ([Wikipedia, "CAP theorem," section on system
  classification](https://en.wikipedia.org/wiki/CAP_theorem), verified
  2026-08-02, citing MongoDB alongside Redis as commonly classified CP
  systems).

## 10. Consequences

### Positive

- Gives engineers a **shared vocabulary and a hard boundary**, nobody has to
  independently rediscover, mid-incident, that "consistent and available during
  a network partition" is not on the table, which shortens the discussion from
  "can we have both" to "which one, and where."
- Forces the **partition-response decision to be made deliberately, in
  advance**, as a design choice with tests and documented behaviour, rather
  than being decided by accident by whatever the database driver's default
  timeout happens to do.
- Cleanly separates **two genuinely different engineering problems**, what to
  do the instant a partition is detected (CAP's question), and how to
  reconcile divergent state once it heals (a separate, equally real problem
  CAP does not answer, addressed by CRDTs, vector clocks, or application-level
  merge logic).
- Motivated an entire generation of purpose-built distributed data stores
  (Dynamo-family AP stores, Raft or Paxos-backed CP stores) that are explicit
  about their guarantees instead of inheriting an ambiguous "it's a database,
  it just works" posture from single-node relational systems.

### Negative

- **Frequently mis-stated as "pick two of three" as a permanent, static
  architectural label**, when the theorem's actual claim is about what happens
  during an active partition, which is rare; Brewer's own 2012 retraction of the
  crude version of his conjecture is largely ignored in casual engineering
  conversation, and teams still design around "we're a CP system" as an
  identity rather than "here is what our system does during a partition, and
  here is what it does the rest of the time."
- **Says nothing about the far more common trade-off**, latency versus
  consistency in the no-partition case, which is where most systems actually
  spend their engineering budget; a team that treats CAP as the whole picture
  will underinvest in the PACELC half of the problem (dimension 8).
- **Encourages a false binary at the whole-system level** when the real
  decision is almost always per-operation or per-data-type. a checkout flow's
  inventory count might need CP guarantees while the same application's
  "recently viewed items" list is perfectly fine as AP, and forcing one label
  onto the whole system either over-engineers the second case or
  under-engineers the first.
- **The AP choice defers real cost, it does not eliminate it.** Choosing
  availability during a partition means someone, later, has to reconcile
  divergent writes, and that reconciliation logic (merge functions, conflict
  UI, "we detected duplicate orders, refunding one") is genuine engineering
  work that is easy to skip in the initial design and expensive to retrofit
  once real conflicts start appearing in production.

## 11. Failure modes and misuse

- **Symptom.** A team ships a database labelled "CA" in an internal design
  doc, and the first real network blip between availability zones causes an
  outage nobody planned for.
  **Cause.** CA is not achievable for any system with more than one
  network-connected node, by the Gilbert-Lynch proof; the label was really
  describing a single-node deployment or a system that had simply never yet
  experienced a partition.
  **Fix.** Rename the design assumption to what it actually is (a single point
  of failure accepted for simplicity, or an untested assumption about network
  reliability), and explicitly decide, on paper, what the system does the
  first time that assumption breaks.

- **Symptom.** A "highly available" service returns wrong or conflicting data
  during an incident, and a post-mortem discovers stale reads were served from
  a replica that had silently fallen behind.
  **Cause.** The system was configured, or defaulted, to an AP-style read path
  (for example Cassandra `ONE` reads) without the team consciously choosing
  that trade-off, and without building the reconciliation logic that AP
  systems require to make the divergence safe.
  **Fix.** Make the consistency level an explicit, reviewed configuration per
  data type, matched to that data's actual tolerance for staleness, and treat
  "we chose AP" as a decision requiring a stated reconciliation strategy, not
  a default that was never examined.

- **Symptom.** A distributed lock or leader-election service occasionally
  allows two processes to believe they are both the leader at once (split
  brain), each doing work that assumes exclusivity.
  **Cause.** The lock service was built or configured for availability during a
  partition (each side of the partition keeps electing and re-electing a
  leader locally) rather than for consistency, which is exactly backwards for
  a use case whose entire value is the guarantee that only one leader exists.
  **Fix.** Use a consensus-backed CP store (etcd, ZooKeeper, a Raft-based lock
  service) for anything whose correctness depends on there being exactly one
  answer, and accept that the minority side of a partition must go silent
  rather than keep electing.

- **Symptom.** A team spends months debating "should we be CP or AP" for their
  entire platform and ships nothing, or ships one blanket choice that is wrong
  for half their data.
  **Cause.** Treating CAP as a single, system-wide, once-and-for-all
  architectural decision instead of a per-operation, per-data-type question.
  **Fix.** Classify data by its real tolerance for staleness and for
  unavailability (money and inventory lean CP, presence indicators and view
  counts lean AP) and let different parts of the system, or different calls to
  a tunable store, make different choices.

- **Symptom.** Engineers cite "CAP theorem" to justify a design decision that
  has nothing to do with a network partition, for example choosing a
  transaction isolation level inside a single Postgres instance.
  **Cause.** Confusing CAP's C (linearizability across network-connected
  replicas) with unrelated consistency concepts, ACID consistency (integrity
  constraints), or single-node isolation levels (concurrent-transaction
  anomalies). None of these involve a network partition and none are governed
  by CAP.
  **Fix.** Reserve CAP-theorem reasoning for genuinely networked, replicated
  systems, and use the correct vocabulary, ACID isolation levels, integrity
  constraints, for single-node concurrency questions.

## 12. Trade-off matrix

| Force | CP (favour Consistency) | AP (favour Availability) | Tunable per-op | PACELC-aware CP (e.g. Spanner) |
|---|---|---|---|---|
| Behaviour during a partition | Minority side refuses reads and writes | Every reachable node keeps answering | Chosen per call (`QUORUM` vs `ONE`) | Minority side refuses, like CP |
| Risk of stale or conflicting reads | None, by construction | Real, until anti-entropy runs | Depends on the level chosen per call | None, by construction |
| Uptime as observed by callers on the losing side of a partition | Zero, until partition heals or quorum recovers | Full, but data may be stale | Depends on quorum size chosen | Zero, same as CP |
| Reconciliation engineering required | None; divergence is prevented, not repaired | Real and ongoing (vector clocks, CRDTs, LWW) | Only for the ops that used a weak level | None |
| Steady-state (no partition) latency | Higher; every op needs quorum round trips | Lower; local ack is enough | Chosen per call | Higher still, bounded by clock-uncertainty commit-wait |
| Best fit | Money movement, inventory counts, distributed locks | Session data, view counts, shopping carts, presence | Mixed workloads on one cluster | Global financial ledgers needing both properties, at a latency cost |
| Representative system | etcd, ZooKeeper, MongoDB (default) | DynamoDB, original Dynamo, Cassandra at `ONE` | Cassandra (level chosen per query) | Google Spanner |

## 13. Related and incompatible patterns

- **PACELC.** The direct successor and correction to CAP, extending the same
  reasoning to cover the far more common no-partition case; any team applying
  CAP seriously should apply PACELC alongside it, because CAP alone only
  describes rare moments while PACELC describes what the system does the rest
  of the time.
- **Quorum consensus (Raft, Paxos, majority read and write quorums).** The
  concrete mechanism most CP implementations of CAP actually use to decide
  whether a node can safely answer during degraded connectivity; understanding
  quorum math (`R + W > N` guarantees a read sees the latest write) is the
  practical implementation of the CP choice.
- **Eventual consistency and CRDTs.** The concrete mechanisms most AP
  implementations of CAP use to make the "we might diverge" choice safe by
  guaranteeing divergent copies converge automatically, without requiring the
  application to hand-write conflict resolution for every field.
- **Saga pattern.** A complementary pattern for a different but adjacent
  problem, coordinating a multi-step business transaction across several
  services, each of which may itself be a CP or AP data store. Saga does not
  resolve CAP tension inside any one store; it accepts that distributed
  transactions across services are hard for the same underlying network
  reasons and compensates rather than locks.
- **Circuit Breaker.** Complementary at the client side, a circuit breaker
  decides when to stop calling a dependency that is behaving as if it were on
  the wrong side of a partition, which is a client-side mitigation for the
  same network unreliability CAP is reasoning about server-side.
- **Two-Phase Commit (2PC).** In tension with, and often confused for a
  solution to, CAP tension. 2PC tries to get atomicity across nodes by having a
  coordinator block all participants until every one of them votes to commit,
  which is a CP-flavoured strategy that becomes unavailable, not merely
  inconsistent, if the coordinator or any participant is unreachable during the
  vote; it does not sidestep CAP, it is one particular (and blocking) way of
  choosing C over A.

## 14. Refactoring path in and out

### Introducing an explicit CAP stance where one was implicit

1. Identify every place the system currently reads from or writes to a
   replicated store and ask, honestly, what happens today when that store's
   nodes cannot all reach each other. Most systems have never tested this and
   the honest answer is "we don't know," which is itself the finding to write
   down.
2. Classify each piece of state by its real tolerance for staleness (can a
   caller act on data that is a few seconds old) and its real tolerance for
   unavailability (can a caller wait, retry, or degrade gracefully if this
   specific call fails).
3. For state that cannot tolerate staleness (money, inventory, exclusive
   locks), move it onto, or configure it to use, a quorum-backed CP path,
   majority read and write quorums, or a dedicated consensus store like etcd
   for the exclusivity-sensitive subset.
4. For state that can tolerate staleness but not unavailability (session data,
   presence, counts), move it onto, or configure it to use, an AP path, and
   explicitly build the reconciliation step (a merge function, a
   last-writer-wins policy with a documented conflict window, or a CRDT type)
   rather than leaving it undefined.
5. Write and run an actual partition test (kill the network between two nodes
   in a staging cluster, or use a chaos-engineering tool) and verify the system
   behaves the way step 3 or 4 said it would, not the way the driver's default
   timeout happens to behave.

### Removing an over-engineered CP guarantee that is not earning its cost

1. Confirm, with real data (an incident log, a query pattern analysis), that
   the data in question genuinely tolerates the staleness window an AP
   approach would introduce; do not guess.
2. Lower the consistency level for that specific data type or table only
   (Cassandra's per-query consistency level is designed exactly for this,
   dimension 8), rather than re-architecting the whole store.
3. Add the reconciliation logic (dimension 10, negative consequence) before
   flipping the switch, not after; the whole cost of AP is this step, and
   skipping it is the misuse pattern in dimension 11.
4. Monitor conflict rate and staleness window in production after the change,
   and keep the CP fallback available for the specific operations (an admin
   override, a "force consistent read") that occasionally need it.

## 15. Testing and verification

Testing CAP behaviour is fundamentally a fault-injection problem, correctness
under normal conditions proves nothing, because the theorem only bites during a
partition. A test suite that never simulates a network partition has not tested
this pattern at all, it has only tested the happy path.

- **Chaos and partition injection.** Use a network fault-injection tool
  (`tc`/`netem` on Linux, Toxiproxy, or a chaos-engineering platform's
  network-partition action) to actually sever connectivity between a subset of
  nodes in a staging cluster, then assert the documented behaviour, does the
  minority side refuse, or does it answer stale, and does either match what
  the design said it would do.
- **Quorum-math unit tests.** For any quorum-based implementation, test the
  boundary conditions directly, at `N` replicas, a write with exactly
  `N/2` acks must fail (no majority) and a write with `N/2 + 1` acks must
  succeed, and that a read quorum plus a write quorum that together exceed `N`
  is guaranteed to overlap by at least one node (the mathematical basis for
  CP correctness in a quorum system).
- **Convergence tests for AP paths.** After deliberately creating a divergent
  write on each side of a simulated partition, heal the partition and assert
  that both sides converge to the same final value within the documented
  reconciliation window, using the same conflict-resolution rule the system
  actually ships (last-writer-wins timestamp comparison, vector-clock causality
  check, or CRDT merge function), never a hand-waved "eventually."
- **Jepsen-style linearizability checking.** For a system claiming CP
  guarantees, the strongest available verification is a Jepsen-style test,
  run a real client workload against a real cluster while injecting real
  network partitions, record every operation's real start and end time and its
  observed result, and run a linearizability checker (such as Knossos, the
  checker paired with the Jepsen test suite) against the recorded history to
  prove no anomaly occurred, rather than merely asserting the design intends
  one not to.

## 16. Observability signals

- **Quorum-availability rate.** For a CP or tunable system, the fraction of
  writes and reads that succeed on the first attempt without needing to retry
  against a different coordinator; a sustained drop signals either a real
  network partition or a replica that has silently fallen out of the quorum
  set.
- **Read-repair and anti-entropy rate.** For an AP system, the count of
  divergent versions detected and merged per unit time; a spike after any
  incident confirms a partition actually happened and quantifies how many keys
  diverged, which is the concrete cost the AP choice was paying for during that
  window.
- **Consistency-level distribution per query, for a tunable store.** Tracking
  what fraction of reads and writes actually ran at `ONE` versus `QUORUM`
  versus `ALL` surfaces silent drift, a table that was meant to be CP slowly
  accumulating call sites that use a weaker level than the design intended.
- **Staleness window, measured directly.** For any AP path, the actual observed
  time between a write being accepted on one replica and that value being
  visible on all replicas, sampled continuously rather than assumed; this
  number is the real SLA an AP choice is making, whether or not anyone wrote
  it down.
- **Partition and leader-election events.** For a Raft- or Paxos-backed CP
  store, every leader election and every period the cluster spent without a
  quorum is a direct, first-class signal that a partition occurred and that
  the system behaved (or failed to behave) as designed; these events should be
  alertable on their own, not only inferred from downstream error rates.

## 17. Security and privacy implications

CAP itself does not create a new attack surface, but the choice it forces has
two indirect security and privacy consequences worth naming plainly rather than
leaving silent.

- **An AP system's reconciliation window is a window where two different,
  simultaneously "valid" answers exist for the same piece of data.** For most
  data this is a minor staleness cost, but for authorization-relevant data (a
  revoked API key, a removed permission, a banned account flag) that same
  window means a request on the wrong side of a partition can be answered
  using a stale, not-yet-revoked value. Access-control and authentication state
  should default to the CP path specifically because the cost of a stale
  "allow" answer is categorically worse than the cost of a stale "counter"
  answer.
- **A CP system's availability sacrifice can itself be turned into a denial of
  service.** Because a CP system deliberately goes silent (rather than wrong)
  on the losing side of a partition, an attacker who can induce network
  partitions, or exploit a resource-exhaustion bug that mimics one from the
  cluster's point of view, can weaponise the system's own correctness
  guarantee to take it offline. This is a genuine, analytical trade-off rather
  than a documented CVE class, and it argues for rate limiting and resource
  isolation around the consensus layer itself, not only around the application
  layer above it.

## 18. References

1. Eric A. Brewer, "CAP Twelve Years Later. How the 'Rules' Have Changed,"
   IEEE Computer, vol. 45, no. 2, 2012, pp. 23-29, DOI 10.1109/MC.2012.37.
   [PDF mirror](https://sites.cs.ucsb.edu/~rich/class/cs293b-cloud/papers/brewer-cap.pdf),
   verified 2026-08-02.
2. Seth Gilbert and Nancy Lynch, "Brewer's Conjecture and the Feasibility of
   Consistent, Available, Partition-Tolerant Web Services," ACM SIGACT News,
   vol. 33, no. 2, 2002, pp. 51-59, DOI 10.1145/564585.564601.
   [ACM Digital Library](https://dl.acm.org/doi/10.1145/564585.564601),
   verified 2026-08-02.
3. Daniel J. Abadi, "Consistency Tradeoffs in Modern Distributed Database
   System Design. CAP is Only Part of the Story," IEEE Computer, vol. 45,
   no. 2, 2012, pp. 37-42, DOI 10.1109/MC.2012.33.
   [ACM Digital Library](https://dl.acm.org/doi/10.1109/mc.2012.33),
   verified 2026-08-02.
4. Giuseppe DeCandia, Deniz Hastorun, Madan Jampani, Gunavardhan Kakulapati,
   Avinash Lakshman, Alex Pilchin, Swaminathan Sivasubramanian, Peter Vosshall,
   Werner Vogels, "Dynamo. Amazon's Highly Available Key-value Store," SOSP
   2007, pp. 205-220.
   [amazon.science](https://www.amazon.science/publications/dynamo-amazons-highly-available-key-value-store),
   verified 2026-08-02.
5. James C. Corbett, Jeffrey Dean, Michael Epstein, et al., "Spanner.
   Google's Globally-Distributed Database," Proceedings of the 10th USENIX
   Symposium on Operating Systems Design and Implementation (OSDI 2012).
   [usenix.org PDF](https://www.usenix.org/system/files/conference/osdi12/osdi12-final-16.pdf),
   verified 2026-08-02.
6. Diego Ongaro and John Ousterhout, "In Search of an Understandable
   Consensus Algorithm," Proceedings of USENIX Annual Technical Conference
   (ATC) 2014.
   [raft.github.io](https://raft.github.io/raft.pdf), verified 2026-08-02.
7. DataStax, "How is the consistency level configured?," Apache Cassandra
   3.0 documentation.
   [docs.datastax.com](https://docs.datastax.com/en/cassandra-oss/3.0/cassandra/dml/dmlConfigConsistency.html),
   verified 2026-08-02.
8. "CAP theorem," Wikipedia, consulted for corroboration of the plain-language
   statement of the three properties and for the classification of MongoDB
   and Redis as commonly cited CP systems and CouchDB, Cassandra, and
   ScyllaDB as commonly cited AP systems.
   [en.wikipedia.org/wiki/CAP_theorem](https://en.wikipedia.org/wiki/CAP_theorem),
   verified 2026-08-02.

## Code examples

The pattern is demonstrated by a small, self-contained three-replica register
that can be operated in `"CP"` mode (a write or read on the minority side of a
partition is rejected because it cannot reach a majority quorum) or `"AP"`
mode (a write or read on the minority side is served locally regardless of
quorum, and may be stale). All three examples model the identical scenario
from dimension 7. three replicas start in sync, a partition isolates one
replica, and a client tries to write through the isolated replica.

### Python

```python
"""Minimal CP vs AP replica set to make the CAP trade-off concrete.

Three replicas hold one register. WRITE_QUORUM and READ_QUORUM decide
whether a write or read needs a majority of reachable replicas (CP) or
tolerates just one (AP). A partition is simulated by marking replicas
unreachable.
"""
from dataclasses import dataclass


@dataclass
class Replica:
    name: str
    value: int = 0
    version: int = 0
    reachable: bool = True


class ReplicaSet:
    def __init__(self, names, mode):
        self.replicas = [Replica(n) for n in names]
        self.mode = mode  # "CP" or "AP"
        self.quorum = len(self.replicas) // 2 + 1

    def partition(self, unreachable_names):
        for r in self.replicas:
            r.reachable = r.name not in unreachable_names

    def reachable_replicas(self):
        return [r for r in self.replicas if r.reachable]

    def write(self, coordinator_name, value):
        coordinator = next(r for r in self.replicas if r.name == coordinator_name)
        targets = self.reachable_replicas() if coordinator.reachable else []
        needed = self.quorum if self.mode == "CP" else 1
        if len(targets) < needed:
            return False, "REJECTED: quorum unavailable"
        version = coordinator.version + 1
        acked = 0
        for r in targets:
            r.value, r.version = value, version
            acked += 1
        return True, f"ACCEPTED: {acked}/{len(self.replicas)} replicas wrote v{version}"


def demo():
    for mode in ("CP", "AP"):
        rs = ReplicaSet(["r1", "r2", "r3"], mode)
        rs.partition(unreachable_names=set())
        rs.write("r1", 100)
        # simulate a network partition isolating r1 alone
        rs.partition(unreachable_names={"r2", "r3"})
        ok, msg = rs.write("r1", 200)
        print(f"{mode} write during partition (minority side): {ok} -> {msg}")


if __name__ == "__main__":
    demo()
```

Run and output, confirmed 2026-08-02 with `python3 cap.py`.

```
CP write during partition (minority side): False -> REJECTED: quorum unavailable
AP write during partition (minority side): True -> ACCEPTED: 1/3 replicas wrote v2
```

### Go

```go
// Minimal CP vs AP replica set to make the CAP trade-off concrete.
package main

import "fmt"

type Replica struct {
	Name      string
	Value     int
	Version   int
	Reachable bool
}

type ReplicaSet struct {
	Replicas []*Replica
	Mode     string // "CP" or "AP"
	Quorum   int
}

func NewReplicaSet(names []string, mode string) *ReplicaSet {
	reps := make([]*Replica, len(names))
	for i, n := range names {
		reps[i] = &Replica{Name: n, Reachable: true}
	}
	return &ReplicaSet{Replicas: reps, Mode: mode, Quorum: len(reps)/2 + 1}
}

func (rs *ReplicaSet) Partition(unreachable map[string]bool) {
	for _, r := range rs.Replicas {
		r.Reachable = !unreachable[r.Name]
	}
}

func (rs *ReplicaSet) reachable() []*Replica {
	out := []*Replica{}
	for _, r := range rs.Replicas {
		if r.Reachable {
			out = append(out, r)
		}
	}
	return out
}

func (rs *ReplicaSet) Write(coordinatorName string, value int) (bool, string) {
	var coordinator *Replica
	for _, r := range rs.Replicas {
		if r.Name == coordinatorName {
			coordinator = r
		}
	}
	targets := []*Replica{}
	if coordinator.Reachable {
		targets = rs.reachable()
	}
	needed := 1
	if rs.Mode == "CP" {
		needed = rs.Quorum
	}
	if len(targets) < needed {
		return false, "REJECTED: quorum unavailable"
	}
	version := coordinator.Version + 1
	acked := 0
	for _, r := range targets {
		r.Value, r.Version = value, version
		acked++
	}
	return true, fmt.Sprintf("ACCEPTED: %d/%d replicas wrote v%d", acked, len(rs.Replicas), version)
}

func main() {
	for _, mode := range []string{"CP", "AP"} {
		rs := NewReplicaSet([]string{"r1", "r2", "r3"}, mode)
		rs.Partition(map[string]bool{})
		rs.Write("r1", 100)
		rs.Partition(map[string]bool{"r2": true, "r3": true})
		ok, msg := rs.Write("r1", 200)
		fmt.Printf("%s write during partition (minority side): %v -> %s\n", mode, ok, msg)
	}
}
```

Run and output, confirmed 2026-08-02 with `go run cap.go` (go1.24).

```
CP write during partition (minority side): false -> REJECTED: quorum unavailable
AP write during partition (minority side): true -> ACCEPTED: 1/3 replicas wrote v2
```

### Rust

```rust
// Minimal CP vs AP replica set to make the CAP trade-off concrete.
use std::collections::HashSet;

struct Replica {
    name: &'static str,
    value: i32,
    version: u32,
    reachable: bool,
}

struct ReplicaSet {
    replicas: Vec<Replica>,
    mode: &'static str, // "CP" or "AP"
    quorum: usize,
}

impl ReplicaSet {
    fn new(names: &[&'static str], mode: &'static str) -> Self {
        let replicas = names
            .iter()
            .map(|&n| Replica { name: n, value: 0, version: 0, reachable: true })
            .collect::<Vec<_>>();
        let quorum = replicas.len() / 2 + 1;
        ReplicaSet { replicas, mode, quorum }
    }

    fn partition(&mut self, unreachable: &HashSet<&str>) {
        for r in self.replicas.iter_mut() {
            r.reachable = !unreachable.contains(r.name);
        }
    }

    fn write(&mut self, coordinator_name: &str, value: i32) -> (bool, String) {
        let coordinator_reachable = self
            .replicas
            .iter()
            .find(|r| r.name == coordinator_name)
            .map(|r| r.reachable)
            .unwrap_or(false);
        let needed = if self.mode == "CP" { self.quorum } else { 1 };
        let target_count = if coordinator_reachable {
            self.replicas.iter().filter(|r| r.reachable).count()
        } else {
            0
        };
        if target_count < needed {
            return (false, "REJECTED: quorum unavailable".to_string());
        }
        let version = self
            .replicas
            .iter()
            .find(|r| r.name == coordinator_name)
            .map(|r| r.version + 1)
            .unwrap_or(1);
        let mut acked = 0;
        let total = self.replicas.len();
        for r in self.replicas.iter_mut().filter(|r| r.reachable) {
            r.value = value;
            r.version = version;
            acked += 1;
        }
        (true, format!("ACCEPTED: {}/{} replicas wrote v{}", acked, total, version))
    }
}

fn main() {
    for mode in ["CP", "AP"] {
        let mut rs = ReplicaSet::new(&["r1", "r2", "r3"], mode);
        rs.partition(&HashSet::new());
        rs.write("r1", 100);
        let mut isolated: HashSet<&str> = HashSet::new();
        isolated.insert("r2");
        isolated.insert("r3");
        rs.partition(&isolated);
        let (ok, msg) = rs.write("r1", 200);
        println!("{} write during partition (minority side): {} -> {}", mode, ok, msg);
    }
}
```

Run and output, confirmed 2026-08-02 with `rustc -O cap.rs && ./cap`.

```
CP write during partition (minority side): false -> REJECTED: quorum unavailable
AP write during partition (minority side): true -> ACCEPTED: 1/3 replicas wrote v2
```

A Java or Swift port was not written for this entry because the pattern has no
language-specific idiom beyond ordinary object state and control flow. three
runnable, verified examples already demonstrate the behaviour identically
across an interpreted language, a compiled garbage-collected language, and a
compiled memory-safe-without-a-collector language, which spans the relevant
design space (dynamic scripting, managed compiled, and systems-level compiled)
that a fourth or fifth port would not meaningfully add to.
