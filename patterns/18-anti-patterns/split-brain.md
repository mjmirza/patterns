---
name: Split Brain
slug: split-brain
family: 18-anti-patterns
category: Distributed Systems Anti-Pattern
aliases: [Dual Primary, Divergent Cluster, Partition Amnesia]
first_described: "Coined in the clustering and high-availability literature of the 1980s and 1990s (VAXcluster, IBM HACMP), popularized in distributed-systems writing through the 2000s"
maturity: canonical
related: [saga, event-sourcing, cqrs, circuit-breaker, bulkhead]
incompatible_with: []
verified: 2026-08-02
---

# Split Brain

## 1. Name, aliases, and lineage

The canonical name is Split Brain. The term is borrowed directly from clinical
neuroscience, where severing the corpus callosum leaves two hemispheres of a
brain operating independently, each unaware of what the other is doing. In
distributed systems the metaphor is exact. a network partition severs the
communication link between two halves of a cluster, and each half, unaware the
other still exists and is still serving traffic, keeps acting as if it alone is
in charge.

The term entered computing through commercial high-availability clustering
products of the 1980s and 1990s, most visibly IBM's HACMP (High Availability
Cluster Multi-Processing, later PowerHA) and DEC's VAXcluster software, both of
which shipped explicit split-brain avoidance mechanisms (quorum disks, tie
breakers) because the failure mode was already well known to their engineering
teams before the term appears in academic literature. The pattern is not
attributed to a single paper or author the way many of the patterns in this
catalog are. it is a name that consolidated around a recurring, independently
rediscovered failure across the shared-storage clustering industry, and later
carried unchanged into the different but structurally identical problem of
leader election in replicated databases and consensus systems.

Aliases in circulation. **Dual Primary** is the term used inside MySQL and
PostgreSQL replication communities for the specific case of two nodes each
believing they hold write authority ([MySQL 8.0 Reference Manual, Group
Replication chapter, discussion of "multi-primary" versus accidental dual
writers](https://dev.mysql.com/doc/refman/8.0/en/group-replication.html),
verified 2026-08-02). **Divergent Cluster** appears in some Kubernetes and etcd
operational writing to describe the state after the fact, once two subsets of a
cluster have accumulated incompatible history. **Partition Amnesia** is a less
common term for the moment right after a partition heals, when neither side
remembers, or trusts, what happened on the other side while it was gone. This
catalog treats all four as the same underlying anti-pattern, differing only in
which stage of the failure they name (the cause, the symptom during the outage,
or the symptom after recovery).

This entry distinguishes Split Brain, the anti-pattern, from the
legitimate distributed-systems techniques that manage the same underlying risk.
Split Brain is not "what happens when you run a distributed system", it is what
happens when a system is built, or configured, without the fencing, quorum, or
lease mechanisms that the rest of this catalog's related patterns provide.
Every named production incident in dimension 9 below is a case where a real
engineering team either omitted a known safeguard, misconfigured it, or hit a
scenario a safeguard did not anticipate.

## 2. Problem and context

A system replicates state, or elects a leader, across more than one node so
that it survives the failure of any single node. The mechanism that decides
"who is currently in charge" or "which copy of the data is authoritative"
depends on the nodes being able to talk to each other. A network partition, a
switch failure, a misconfigured firewall rule, a slow or overloaded link that
times out heartbeats, or even a botched maintenance window, removes that
communication path without removing the nodes themselves. Every node keeps
running. None of them crashed. From the outside, and from each node's own
point of view, everything still looks healthy.

The problem is what each side of the partition does next. If the system's
design assumes that "I cannot reach my peer" means "my peer is dead", each side
independently concludes it is now the sole survivor and the sole rightful
leader, and each side keeps accepting writes. Two authoritative copies of the
same data set now exist, diverging from the moment the partition begins. When
the network heals, the system has two histories that cannot both be true. rows
that exist on one side and not the other, the same primary key written to
different values on each side, a counter incremented independently on both
sides so the merged total is simply wrong. There is no operation that
reconciles this automatically without a policy decision, because the two
histories are not "out of sync" in the way a lagging replica is out of sync.
they are two different, self-consistent, mutually incompatible realities.

The context in which this becomes a live risk has three necessary conditions,
all present together.

- **More than one node can independently accept writes**, or independently
  decide it is the leader, without first confirming that decision with the
  rest of the system. A single-writer system with no failover has no split
  brain risk because there is only ever one candidate for authority.
- **The nodes communicate over a network that can partition**, as opposed to
  sharing memory or a single disk that physically cannot be split. Any system
  spanning more than one process, one machine, one rack, one availability
  zone, or one region carries this risk in proportion to how independently
  its parts can fail.
- **The failure-detection mechanism cannot distinguish "peer is dead" from
  "peer is alive but unreachable".** This is the crux of the problem, and it
  is provably undecidable in the general case. no timeout value tells a node
  whether the silence means the peer died or the link died. Martin Kleppmann
  frames this directly. "In fact, a node cannot even be sure whether it is in
  a minority or majority partition... Worse still, that state might not even
  be true anymore by the time a decision based on it is acted upon" (Martin
  Kleppmann, *Designing Data-Intensive Applications*, O'Reilly, 2017, chapter
  8, "The Truth Is Defined by the Majority", on the impossibility of reliable
  failure detection over an asynchronous network).

Split Brain is therefore not a bug in one specific implementation. it is the
predictable consequence of building multi-node coordination on top of a
network that can lie by omission, without building in a mechanism that treats
"I cannot reach the majority" as "I must stop acting as leader" rather than "I
must assume I am still the leader".

## 3. Forces

**Availability versus safety.** This is the primary force at work and it is a
direct instance of the CAP theorem's practical consequence. a majority-quorum
system that correctly avoids split brain does so by refusing to serve writes,
and often reads, from the minority partition. That is not a bug in the
safeguard. it is the deliberate trade the safeguard makes, choosing
consistency and availability-within-the-quorum over availability everywhere.
A system that instead chooses to keep accepting writes on both sides of a
partition is choosing availability over safety, and Split Brain is the name
for what that choice costs when the partition heals.

**Failure-detection latency versus failure-detection accuracy.** A short
heartbeat timeout detects a genuinely dead node quickly, which is good for
recovery time, but also triggers on a merely slow or congested link, which is
bad because it starts a failover that later has to be reconciled with a node
that was never actually down. A long timeout reduces false failovers but
extends the window during which a real outage goes unhandled. There is no
timeout value that is simultaneously fast and safe, only a chosen point on
that curve.

**Automatic recovery versus operator judgement.** Automated failover reduces
mean time to recovery for the common case (a node genuinely died) at the cost
of removing a human's opportunity to notice an ambiguous case (a network blip,
not a node death) before an action is taken that cannot be cleanly undone.
GitHub's own postmortem of the incident discussed in dimension 9 states this
trade explicitly as a lesson learned, describing a move toward requiring a
human to confirm the intended state of the system before automation is
allowed to take a wide-scale action on its own (GitHub, "October 21
post-incident analysis", GitHub Blog, 2018, verified 2026-08-02).

**Operational simplicity versus coordination overhead.** A quorum-based system
needs an odd number of voting members, or an external arbiter, and needs every
client and every node to agree on the current cluster membership. Getting this
wrong, for example running an even number of voters, or letting the voter
count drift without updating the quorum threshold, silently reopens the split
brain risk the system believed it had closed. The coordination machinery
itself becomes a thing that must be operated correctly.

**Data loss avoidance versus write availability.** A system that limits how
long a lagging or isolated node may keep accepting writes, as Redis Sentinel's
`min-replicas-to-write` setting does, trades some write availability during a
partition for a hard bound on how much data can be lost or corrupted if that
node turns out to be on the wrong side of a split. The alternative, unbounded
write availability during a partition, means an unbounded window of data loss
once the partition is discovered and one side's writes must be discarded.

## 4. Applicability and non-applicability

Split Brain is not something a system designer chooses to apply. it is a
failure mode a system is vulnerable to, or is protected against, based on how
its coordination layer is built. This dimension therefore reframes the
question as when the RISK is present versus when it genuinely is not.

**When the risk is present, and safeguards belong in the design from day one.**

- Any system with more than one node capable of accepting writes to the same
  logical data set, including active-passive setups where the passive node
  can be promoted, because promotion is exactly the moment split brain can
  occur.
- Any leader-election or consensus-based cluster (etcd, ZooKeeper, Consul,
  Kubernetes control planes, database replica sets) where a network partition
  could isolate a subset of voting members from the rest.
- Any storage system offering synchronous or semi-synchronous replication
  with automatic failover, including managed database services where the
  failover logic is provided by the vendor rather than the application team,
  because the risk still exists even though the mitigation is someone else's
  code.
- Any active-active geo-replicated deployment across regions or data centers,
  where the inter-region link is the single most likely component to fail
  independently of the machines on either end, exactly as it did in the
  GitHub incident in dimension 9.
- Any caching or session layer treated as a source of truth for something
  that must not diverge, for example a distributed lock service, a rate
  limiter's counter, or an inventory reservation count. these are the cases
  where teams most often forget the risk exists because "it's only a cache".

**When the risk is genuinely absent, and building split-brain machinery is
wasted complexity.**

- A single-node system with no failover target. there is nothing for the
  brain to split into.
- A stateless service with no locally authoritative data, where every replica
  reads from and writes to one already-safe backing store. the coordination
  problem has been pushed down to that store, and duplicating the safeguard
  at this layer adds nothing.
- An eventually-consistent system that was explicitly designed for
  merge-friendly divergence, using CRDTs, vector clocks, or a
  last-writer-wins policy the business has consciously accepted, where
  concurrent independent writes are not an incident, they are the expected
  and reconciled steady state. This is a legitimate design choice, not split
  brain, provided the merge semantics are actually defined and actually
  correct for the data. an unmergeable field (a bank balance, a unique
  username) hidden inside an otherwise CRDT-friendly system is where this
  non-applicability claim quietly turns back into the anti-pattern.
- A read replica that is explicitly documented and enforced as read-only at
  the client and infrastructure level, with no promotion path that a client
  could ever reach mid-partition. If nothing can ever write to it, it cannot
  diverge in a way that matters for correctness, only in staleness, which is
  a different and better-understood problem.
- Batch or offline processing pipelines with no concurrent writers to shared
  mutable state, where each run is idempotent and reprocessing a partition
  from a checkpoint is the correct recovery path rather than reconciling two
  divergent live states.

## 5. Structure

Split Brain names an absence, so its "structure" is the shape of the missing
safeguard alongside the components that, without it, produce the failure.

- **Coordinator or leader role.** The logical position of authority in the
  system, whether that is a database primary, a distributed lock holder, or a
  cluster leader in a consensus protocol. In a correctly built system exactly
  one node holds this role at any instant. Split Brain is precisely the
  violation of that invariant.
- **Follower or replica nodes.** Nodes that accept the coordinator's writes,
  or defer to its decisions, under normal operation, and that are each a
  candidate to become the coordinator on failover.
- **Failure detector.** The heartbeat, lease, or timeout mechanism each node
  uses to decide whether the current coordinator, or its peers, are still
  alive. This is the component whose fundamental unreliability, distinguishing
  "dead" from "merely unreachable", is the root cause of the anti-pattern.
- **Quorum or fencing mechanism, when present.** The component that requires
  a majority, a witness, or an external arbiter to agree before a new
  coordinator is recognized, and that invalidates the authority of a stale
  coordinator once it does. This is the piece whose absence, or
  misconfiguration, turns an ordinary network partition into a split-brain
  incident. Dimension 8 catalogs the real implementations of this piece.
- **Divergent write log.** The two (or more) independent histories of
  accepted writes that accumulate on each side of a partition once more than
  one node believes itself to be the coordinator. This is the artifact that
  makes the incident hard to recover from, because reconciling it requires
  either discarding one side's writes or building an application-specific
  merge, and both options are decided after the fact under pressure rather
  than designed in advance.

## 6. ASCII structure diagram

```
  BEFORE PARTITION (healthy, single coordinator)

       +-------------------+
       |   Coordinator N1  |  <-- accepts all writes
       +-------------------+
          |       |       |
     heartbeat  heartbeat  heartbeat
          |       |       |
     +--------+ +--------+ +--------+
     |  N2    | |  N3    | |  N4    |   followers, defer to N1
     +--------+ +--------+ +--------+


  DURING PARTITION, WITHOUT QUORUM SAFEGUARD  (the anti-pattern)

     partition boundary
             ||
    +--------++--------------------------+
    | N1     ||   N2         N3      N4  |
    | "peers ||   "N1 is unreachable,    |
    |  gone, ||    elect a new leader"   |
    |  I'm   ||                          |
    |  still ||   +--------------+       |
    |  the   ||   | Coordinator  |       |
    |  lead" ||   |     N3       |       |
    +--------++   +--------------+       |
     writes A        writes B            |
     accepted        accepted            |
             ||
             ||   TWO COORDINATORS, TWO DIVERGENT WRITE LOGS


  DURING PARTITION, WITH QUORUM SAFEGUARD  (protected)

     partition boundary
             ||
    +--------++--------------------------+
    | N1     ||   N2         N3      N4  |
    | 1 vote ||   3 votes reachable,     |
    | < 3    ||   3 >= majority(3 of 5)  |
    | steps  ||                          |
    | down,  ||   +--------------+       |
    | reads  ||   | Coordinator  |       |
    | only   ||   |     N3       |       |
    +--------++   +--------------+       |
     no writes        writes accepted    |
             ||
             ||   ONE COORDINATOR, ONE WRITE LOG, N1 REFUSES TO LEAD
```

## 7. Dynamics

The sequence below traces the anti-pattern end to end, in the shape it takes
without a quorum or fencing safeguard, and names the exact point where the
safeguard would intervene if one existed.

```
t0   Cluster healthy. N1 is coordinator. N2, N3, N4 are followers.
     Clients write through N1. All four nodes agree on cluster state.

t1   Network partition occurs. N1 is isolated from N2, N3, N4.
     N1 cannot tell whether N2/N3/N4 crashed or are merely unreachable.
     N2/N3/N4 cannot tell whether N1 crashed or is merely unreachable.

t2   [WITHOUT SAFEGUARD]
     N1's heartbeat to followers times out. N1 assumes IT is the survivor
     and continues accepting writes as coordinator. No check is made
     against how many peers N1 can actually still reach.

     [WITH SAFEGUARD]
     N1 computes votes it can currently confirm (itself only, 1 vote) and
     compares against the majority threshold (3 of 5). 1 < 3, so N1 steps
     down to a non-authoritative, read-only state and REFUSES new writes,
     even though nothing has proven N1 is at fault.

t3   [WITHOUT SAFEGUARD]
     N2/N3/N4's heartbeat to N1 times out. They hold an election among
     themselves. N3 wins, becomes coordinator. N3 also has no way to
     confirm N1 has stopped acting as coordinator, and proceeds anyway.
     TWO COORDINATORS NOW EXIST SIMULTANEOUSLY.

     [WITH SAFEGUARD]
     N2/N3/N4 hold an election. N3 wins with 3 of 5 possible votes
     (itself, N2, N4), which meets the majority(3) threshold. N3 becomes
     the sole coordinator. Because N1 already stepped down at t2, there
     is only ever one coordinator active at any given instant.

t4   [WITHOUT SAFEGUARD]
     Clients still connected to N1 write value X to key K.
     Clients now connected to N3 write value Y to key K.
     Both writes succeed locally. Both nodes report success to their
     respective clients. Two incompatible values for K now exist.

     [WITH SAFEGUARD]
     Clients connected to N1 receive a rejection or redirect, because N1
     is no longer accepting writes. Clients that reconnect to the
     majority partition (N2, N3, N4) write successfully through N3.
     Only one value for K is ever accepted anywhere in the cluster.

t5   Network partition heals. N1 can reach N2/N3/N4 again.

     [WITHOUT SAFEGUARD]
     N1 and N3 both present themselves as coordinator. The system, or an
     operator, must now choose which write log is authoritative and
     discard or attempt to merge the other. Data written to the losing
     side during t3 to t5 is lost or requires manual reconciliation.

     [WITH SAFEGUARD]
     N1 detects a coordinator with a higher term or epoch already exists
     (N3) and rejoins as a follower, resyncing from N3's log. No
     reconciliation decision is needed because only one log ever existed.
```

## 8. Implementation variants

Every real implementation of a split-brain safeguard is a variation on one
underlying idea. require a decision to be confirmed by more nodes, or by an
authority, than any single partition can produce on its own.

**Majority (odd-node) quorum.** The most common variant. cluster membership
size is kept odd, and any leadership or write decision requires votes or
acknowledgments from strictly more than half the voting members. Because two
disjoint subsets of a group can never both contain a strict majority of that
group, at most one partition can ever reach quorum. This is the mechanism
behind Raft-based systems (etcd, Consul), Elasticsearch's cluster coordination
below and at 7.x, and MongoDB's replica set elections, all discussed with
citations in dimension 9. The trade-off is availability. an N-node cluster
with a majority quorum can tolerate the loss of up to (N-1)/2 nodes and keep
functioning, but a partition that leaves no side with a majority (for example
an even split, or several small isolated partitions) makes the entire cluster
unavailable for writes until it heals, which is the deliberate, safety-first
choice CAP theorem forces.

**Witness node or tie-breaker.** For clusters that cannot economically run a
third full voting replica (commonly two-node database or storage clusters
where a third full copy is expensive), a lightweight witness or arbiter node,
sometimes running only a quorum-vote service and holding no data, is added
specifically to break ties and give an odd number of votes without the cost
of a third full replica. MongoDB explicitly supports this pattern as an
"arbiter" member of a replica set that votes in elections but holds no data
([MongoDB Manual, "Replica Set Arbiter"](https://www.mongodb.com/docs/manual/core/replica-set-arbiter/),
verified 2026-08-02).

**Quorum disk or shared-storage fencing.** In classic shared-storage
clustering (SAN-attached databases, some VAXcluster and HACMP configurations),
a dedicated small disk region is used as a tie-breaker that nodes race to
lock. whichever node acquires the lock on the quorum disk is authorized to
proceed as the active node, and a node that cannot reach the quorum disk must
assume it may be partitioned and refuse to act as primary. This variant trades
network-only coordination for a dependency on shared storage remaining
reachable from every node that might need to claim it.

**Fencing tokens (generation numbers, epochs, terms).** Rather than, or in
addition to, preventing a second leader from being elected, this variant
is built so that even if a stale leader keeps issuing writes, those writes are
provably rejected downstream. Every time leadership changes, a monotonically
increasing number (a term, an epoch, a generation) increases. Every write
carries the writer's current number, and any storage layer or downstream
system rejects a write whose number is lower than the highest it has already
seen. Kleppmann calls this the fencing token pattern and states it plainly.
"the storage service in question must actively refuse writes tagged with an
old fencing token" (Martin Kleppmann, *Designing Data-Intensive Applications*,
O'Reilly, 2017, chapter 8, "Fencing Tokens"). This variant works well because
it protects the system even when the election mechanism itself has a bug or a
gap, since it is the last line of defense at the point of write, not at the
point of leader selection. The Python example in this entry demonstrates
exactly this variant.

**Lease-based leadership with expiry.** A node is granted leadership for a
bounded time window (a lease), renewed periodically by successfully
re-confirming quorum, rather than holding leadership indefinitely once
elected. If a leader is partitioned away, its lease simply expires without
requiring any explicit "step down" message to reach it, and it is architected
to stop acting as leader locally once its own lease clock runs out, whether or
not it can reach anyone to confirm this. Chubby, Google's lock service, and
systems built on it use lease-based leadership for exactly this reason
(discussed generally, without a specific citation here since this entry does
not independently verify the Chubby paper's exact wording, flagged per the
judgement-versus-sourced-claim guidance in this repository's template).

**Bounded stale-write windows.** Rather than fully preventing a minority-side
node from accepting any writes, some systems allow a bounded grace period
during which the minority side may still serve writes, capped by a maximum
acceptable staleness or lag, after which it must stop. Redis Sentinel's
`min-replicas-to-write N` combined with `min-replicas-max-lag T` is exactly
this variant, examined with a direct quote from the Redis documentation in
dimension 9. it does not prevent a brief window of writes to an isolated
master, but it bounds how long that window can last, trading a small,
quantified risk window for continued availability during most transient
network hiccups.

## 9. Known production uses

**GitHub, October 2018, MySQL cluster split-brain during a network
partition.** During scheduled maintenance work, a 43-second network
connectivity loss occurred between GitHub's US East Coast primary data center
and its US West Coast facility. GitHub's Orchestrator tool, which manages MySQL
topology using Raft consensus, interpreted the loss of connectivity as a
signal that the East Coast primaries had failed and promoted new primaries in
the West Coast facility. When connectivity was restored 43 seconds later, the
system was left with two sets of primaries that had each accepted writes
independently. GitHub's own postmortem states plainly that "the database
servers in the US East Coast data center contained a brief period of writes
that had not been replicated to the US West Coast facility", roughly 954
writes on the East Coast side, while the West Coast side had accumulated over
thirty minutes of writes from the application tier by the time the incident
was fully understood and resolved. GitHub chose to preserve the West Coast
data (fail forward) rather than discard it, which required restoring multiple
terabytes of data from backups and manually rebuilding replication topology,
and the overall service degradation lasted 24 hours and 11 minutes. The
postmortem's own summary of the root cause. "Orchestrator's actions behaved as
configured, despite our application tier being unable to support this
topology change" ([GitHub, "October 21 post-incident
analysis"](https://github.blog/news-insights/company-news/oct21-post-incident-analysis/),
GitHub Blog, verified 2026-08-02). This is the clearest publicly documented
case of a real production split brain in the pattern's fullest form. two
authoritative databases, each accepting real application writes, for a period
long enough to require a lossy manual reconciliation.

**MongoDB replica sets, majority-based election as the designed safeguard.**
MongoDB's replication documentation describes the exact mechanism this entry's
dimension 8 calls majority quorum, applied specifically to prevent split
brain. "A network partition may segregate a primary into a partition with a
minority of nodes. When the primary detects that it can only see a minority of
voting nodes in the replica set, the primary steps down and becomes a
secondary. Independently, a member in the partition that can communicate with
a majority of the voting nodes (including itself) holds an election to become
the new primary" ([MongoDB Manual, "Replica Set
Elections"](https://www.mongodb.com/docs/manual/core/replica-set-elections/),
verified 2026-08-02). The documentation is explicit that this mechanism
depends on a majority of voting members, capped at seven voting members per
replica set, and that writes accepted by a primary that later turns out to
have been on the minority side of a partition are subject to rollback once the
partition heals and the node rejoins as a secondary, which MongoDB documents
separately under replica set rollbacks. This is a system whose entire
election and consistency model is designed around avoiding split brain, and
whose documentation is unusually direct about naming the failure mode it
avoids.

**Redis Sentinel, documented split-brain scenario and the bounded mitigation
it recommends.** Unlike MongoDB and Elasticsearch, the Redis documentation
walks through a concrete worked example of a partition isolating an old
master M1 from Sentinels and a new master, and states the consequence without
euphemism. clients still connected to the isolated master "may continue to
write data to the old master. This data will be lost forever since when the
partition heals, the Sentinel configuration will converge to the new [master],
and the data on the old master will be discarded" ([Redis documentation,
"High availability with Redis
Sentinel"](https://redis.io/docs/latest/operate/oss_and_stack/management/sentinel/),
section on consistency under partitions, verified 2026-08-02). The
documentation goes on to name the mitigation directly. "in order to prevent a
permanent split brain condition", it recommends configuring
`min-replicas-to-write 1` and `min-replicas-max-lag 10` on the Redis instance
itself, so that a master which cannot see at least one replica within a ten
second lag bound stops accepting writes altogether, bounding the size of the
lost-data window to that ten seconds rather than leaving it open for the full
duration of an undetected partition. This is a notable production case because
the vendor's own documentation acknowledges the anti-pattern will occur under
partition and ships a tunable to bound its blast radius rather than a
mechanism that claims to eliminate it entirely, an honest and instructive
contrast to the majority-quorum systems above.

**Elasticsearch, pre-7.0 `minimum_master_nodes` split brain and the later
quorum-based redesign.** Elasticsearch's own current documentation states the
design goal directly. cluster quorum thresholds are "carefully chosen so the
cluster does not have a 'split brain' scenario where it's partitioned into two
pieces such that each piece may make decisions that are inconsistent with
those of the other piece", and a cluster decision is made "only after more
than half of the nodes in the voting configuration have responded" ([Elastic,
"Quorum-based decision
making"](https://www.elastic.co/guide/en/elasticsearch/reference/current/modules-discovery-quorums.html),
verified 2026-08-02). This is worth including as a production case because
Elasticsearch's history with this exact anti-pattern is well known in the
distributed-systems community. versions before 7.0 relied on operators
manually setting `discovery.zen.minimum_master_nodes` to (master-eligible
nodes / 2) + 1, and a cluster where an operator left this at its old default,
or miscalculated it after adding nodes, could and did elect two independent
masters during a network partition, each accepting index writes independently.
Elasticsearch's 7.0 redesign moved this calculation inside the cluster
coordination layer itself specifically so operators could no longer
misconfigure it, which this entry treats as a documented, vendor-acknowledged
example of an anti-pattern being closed off at the design level after
repeated real-world misconfiguration, rather than a claim about any single
customer's outage.

## 10. Consequences

**Negative, and this list is the longer of the two.**

- Silent, undetected data divergence during the partition window, which is
  often worse than an outright outage because the system appears to be
  working correctly on both sides while it is actually corrupting shared
  state.
- Data loss is frequently unavoidable once the divergence is discovered,
  because reconciling two self-consistent but incompatible histories usually
  requires discarding one side's writes, as GitHub's postmortem describes.
- Manual, high-pressure, error-prone recovery. reconciliation almost always
  happens during an active incident, under time pressure, which is exactly
  the condition under which further mistakes are most likely.
- Erosion of trust in the system's own guarantees. once operators have seen a
  system exhibit split brain once, they reasonably distrust its automated
  failover thereafter, which pushes teams toward manual failover procedures
  that are slower but psychologically safer, undermining the original reason
  for building automatic failover.
- Downstream cascading corruption. any system that consumed writes from
  either side of the split (a cache, a search index, a message queue
  consumer, an analytics pipeline) now also holds corrupted or inconsistent
  state and must itself be repaired, extending the blast radius well beyond
  the original cluster.

**Positive, in the narrow sense of what studying and naming this anti-pattern
provides.** There are no positive consequences of split brain occurring.
There are real positive consequences of understanding the pattern well enough
to design against it. teams that internalize this anti-pattern build quorum,
fencing, or lease mechanisms into new distributed components from the start
rather than retrofitting them after a first incident, and they design their
recovery runbooks (which side wins, what gets discarded, how consumers are
notified) before an incident rather than during one.

## 11. Failure modes and misuse

**Symptom, cause, fix, presented as explicit triples.**

- Symptom. Two application servers, or two database instances, both log
  "elected as leader" or "promoted to primary" within the same short time
  window, and monitoring shows write throughput or write success continuing
  on both. Cause. the election or promotion path has no majority-quorum
  check, so each side independently concludes it has the right to lead once
  its heartbeat to the other times out. Fix. add a majority-vote requirement
  before any promotion is finalized, sized against the total voting
  membership, as demonstrated in the Go example in this entry.

- Symptom. After a network incident, the same record has two different
  values on two nodes that are supposed to be replicas of each other, and
  neither node's write log shows any conflict or rejection at write time.
  Cause. writes were accepted locally on both sides during the partition
  with no fencing token or generation check at the point of write, so
  neither node had any way to know its peer was also accepting writes. Fix.
  attach a monotonically increasing epoch or term to every write and reject
  any write whose epoch is lower than the highest already recorded, as
  demonstrated in the Python example in this entry.

- Symptom. A cluster with an even number of voting nodes (commonly
  introduced by someone adding a fourth node to what was a healthy
  three-node cluster, believing more nodes is safer without checking the
  arithmetic) becomes fully unavailable, or worse, split, during a partition
  that would not have affected an odd-sized cluster. Cause. an even number
  of voters allows a partition to split the cluster into two equal halves,
  neither of which can reach strict majority, or in a misconfigured system,
  both of which are incorrectly treated as reaching majority. Fix. keep the
  voting membership count odd, or explicitly designate a subset of nodes as
  non-voting observers so the effective voter count stays odd, as MongoDB's
  arbiter mechanism does.

- Symptom. Automated failover fires repeatedly during a period of network
  flakiness that never actually takes any node fully offline, and each
  failover event itself briefly widens the risk window for an actual split
  brain to occur, because leadership is changing hands exactly while the
  network is least reliable. Cause. failure-detection timeouts are tuned too
  aggressively relative to the network's real jitter, so transient latency
  spikes are indistinguishable, from the detector's point of view, from a
  genuine node failure. Fix. widen the timeout to reflect observed network
  jitter with margin, and prefer requiring sustained unreachability over
  multiple consecutive probes rather than a single missed heartbeat, before
  triggering an election.

- Symptom. A team believes their system is protected because "we use a
  managed database with automatic failover", and is later surprised to find
  the vendor's failover mechanism itself has a documented split-brain
  scenario, as Redis Sentinel does with its bounded-not-eliminated
  mitigation. Cause. misuse through false confidence. delegating the
  coordination problem to a vendor is reasonable, but assuming delegation
  means the risk has been eliminated rather than bounded is a category
  error. Fix. read the vendor's own documentation of its worst-case
  consistency guarantees under partition, not only its marketing claims of
  high availability, and size the acceptable data-loss window
  (`min-replicas-max-lag` or its equivalent) to the business's actual
  tolerance, not the vendor's default.

- Symptom. An application-level "distributed lock" built on a single Redis
  instance, or a single database row with no fencing token, appears to work
  correctly in every test and staging environment, then two workers both
  hold the "same lock" simultaneously in production during a brief network
  or garbage-collection pause. Cause. the lock's expiry and the holder's
  belief that it still holds the lock can drift apart under real-world
  pauses (a long GC pause, a slow disk write, the same asynchronous-network
  uncertainty discussed in dimension 2), which is functionally identical to
  a split brain between "the lock service's view" and "the lock holder's
  view" of who holds the lock. Fix. use a fencing token issued by the lock
  service and enforced by whatever resource the lock protects, exactly the
  mechanism Kleppmann describes and this entry's Python example
  demonstrates, rather than trusting the lock holder's local belief that its
  lease has not expired.

## 12. Trade-off matrix

| Force | Majority quorum | Fencing tokens | Bounded stale-write window (Sentinel style) | No safeguard (the anti-pattern) |
|---|---|---|---|---|
| Prevents dual leadership | Yes, provably, given odd voter count | No, allows dual leadership but neutralizes its effect at the write point | No, briefly allows it, bounded by the lag setting | No |
| Prevents any data loss | Not by itself, still needs application-level reconciliation for the discarded side | Yes for the specific writes it rejects, at the cost of rejecting some legitimate late writes too | No, bounded but nonzero loss window is explicit and documented | No, unbounded loss |
| Availability during partition | Minority side becomes fully unavailable for writes | Both sides may accept writes; only downstream storage enforces the outcome | Isolated side keeps writing until its lag bound is hit, then stops | Both sides fully available, which is the illusion that makes this dangerous |
| Operational complexity | Requires odd voter count and correct quorum math | Requires every write path and every storage layer to check and enforce the token | Low, a documented configuration knob | Lowest, which is exactly why it is easy to end up here by default |
| Where it lives in the stack | Coordination or consensus layer | Storage or resource-access layer, deliberately independent of the election layer | Replication layer | Nowhere, by omission |
| Best paired with | Fencing tokens, as defense in depth for the moment right around an election | Any leader-election mechanism, including majority quorum, as a second independent layer | An explicit, documented data-loss budget approved by the business | Nothing, this column exists to be avoided |

## 13. Related and incompatible patterns

**Saga.** A Saga is one of the practical answers to what to do once a system
has accepted that a single distributed transaction across services is not
always achievable, using a sequence of local transactions with compensating
actions instead. It composes with split-brain avoidance in a specific way. a
Saga's compensating actions assume each local transaction was itself correctly
isolated and not silently duplicated by a split-brain condition in the service
that executed it. A Saga step running against a split-brained service can
itself record two divergent local outcomes, which then poisons the Saga's own
compensation logic. Fencing tokens at each service's write boundary keep a
Saga's assumptions valid even if that service's leadership layer is
momentarily ambiguous.

**Event Sourcing.** Event sourcing can make split-brain recovery more
tractable, because the append-only event log gives a natural, auditable
substrate for detecting where two histories diverged and for replaying a
corrected history, rather than trying to reconcile two opaque, already-mutated
final states. It does not prevent split brain. two divergent append streams
are still two divergent histories, and the event store itself needs the same
majority or fencing protections as any other write path, but it changes
dimension 10's "manual, error-prone recovery" consequence into something more
mechanical, because the divergence point is visible in the log rather than
inferred from a diff of final states.

**CQRS (Command Query Responsibility Segregation).** CQRS is largely
orthogonal to split brain, but it interacts with it at the command side. the
write model in a CQRS system is exactly the component that needs the
protections this entry describes, because it is the place where authoritative
writes are accepted. The read side, being derived and typically eventually
consistent by design, is far less exposed to the acute correctness failure of
split brain and more exposed to ordinary staleness, which is a different,
better-tolerated problem.

**Circuit Breaker.** A Circuit Breaker and a split-brain safeguard solve
adjacent but different problems. a Circuit Breaker protects a caller from a
struggling downstream dependency by failing fast, while a split-brain
safeguard protects the coordination layer itself from making an unsafe
decision under uncertainty. They compose well. a node that has stepped down
because it lost quorum, per dimension 8's majority variant, is in a state a
well-designed client-side Circuit Breaker should treat exactly like an
unhealthy dependency, failing over its own calls to whichever node the
coordination layer currently reports as leader.

**Bulkhead.** A Bulkhead isolates failure domains so that a problem in one
does not exhaust shared resources and take down another. It is complementary
in a specific, narrow way. isolating the resources used by cross-region
replication traffic from the resources used by local, same-region traffic
means a struggling cross-region link, the most common trigger for the
partitions that cause split brain in geo-replicated systems, is less likely
to also starve the local heartbeat and quorum traffic that is trying to detect
and safely resolve that very partition.

**Incompatible or actively opposed patterns.** Split Brain itself is not a
pattern to compose with anything, it is the failure this entire dimension's
neighbors exist to prevent, so there is no pattern in this catalog that is
"incompatible" with it in the sense the template intends for a legitimate
pattern. The closest useful statement is that any design relying on
last-writer-wins semantics for data that genuinely cannot tolerate silent
overwrite, an account balance, a unique identifier allocation, a physical
inventory count, is actively incompatible with tolerating split brain, even
briefly, and needs one of the safeguards in dimension 8 rather than an
eventually-consistent merge strategy.

## 14. Refactoring path in and out

This anti-pattern is unusual among the entries in this family in that there is
no "refactoring into it" path worth documenting, since nobody deliberately
adds split brain to a working system. The refactoring path that matters is
strictly the path out, moving a vulnerable system toward one of the
safeguards in dimension 8.

1. **Establish the current voting or coordination model first.** Before
   changing anything, write down, explicitly, how many nodes can currently
   accept writes or claim leadership, and what mechanism, if any, currently
   decides who is allowed to. Many teams discover at this step that the
   answer is "there is no mechanism, it's whichever node's health check
   passes first", which is itself the finding that justifies the rest of the
   work.
2. **Add fencing tokens at the storage boundary before touching the election
   logic.** This is the highest-impact first step because it is the
   cheapest to add, does not require redesigning how leaders are chosen, and
   provides real protection immediately. every write already carries, or can
   be made to carry, the writer's current term or epoch, and every write
   target checks it against the highest epoch it has already accepted,
   rejecting anything lower. This closes the "two coordinators both actually
   corrupt shared state" failure even before the election mechanism itself
   is fixed.
3. **Make the voter count odd, or add an explicit arbiter or witness, if it
   is currently even or ambiguous.** Confirm the majority threshold is
   computed as (voters / 2) + 1 and that this computation lives in exactly
   one place, ideally inside the coordination library itself rather than in
   application configuration that a future operator could get wrong, echoing
   Elasticsearch's own 7.0 redesign discussed in dimension 9.
4. **Require quorum confirmation before any promotion is finalized**, so
   that a node about to become leader first confirms it can reach a majority
   of voting peers, not merely that it cannot reach the previous leader. This
   is the step that actually prevents dual leadership rather than merely
   neutralizing its effects, and it is deliberately sequenced after step 2
   because fencing tokens provide a safety net while this larger, riskier
   change is designed, tested, and rolled out.
5. **Move automated failover behind a human confirmation gate for
   high-blast-radius topology changes**, at least until the system has
   demonstrated correct behavior under real partition testing (see dimension
   15), taking GitHub's own stated lesson from dimension 3 as the model.
6. **Write and rehearse the reconciliation runbook before the next
   incident**, not during it. decide in advance which side's writes win in
   an unresolvable conflict, how affected customers or downstream systems
   are identified and notified, and who has the authority to make that call
   at 3 a.m., so that the decision described in dimension 10's "manual,
   high-pressure recovery" consequence is at least a rehearsed decision
   rather than an improvised one.

## 15. Testing and verification

Split brain is specifically the kind of failure that unit tests, and even most
integration tests, cannot exercise, because it depends on the network
misbehaving in a way that a normal test environment's network never does.
Verification has to target this directly.

- **Fault injection at the network layer**, deliberately partitioning a
  cluster under test using tools that drop or delay packets between specific
  nodes (Linux `tc`/`netem`, iptables rules that drop traffic between two
  sets of hosts, or dedicated chaos-engineering tooling), then asserting on
  the cluster's observable behavior during the partition, not merely after it
  heals. the assertion that matters most is "at most one node accepted writes
  at any instant during the partition", which requires timestamped, per-node
  write logs collected independently of the cluster's own self-reported
  state, since a split-brained cluster cannot be trusted to accurately report
  on itself.
- **Property-based and deterministic simulation testing** of the election and
  fencing logic in isolation from real networking, generating random
  partition schedules (which nodes can reach which others, and when) and
  asserting the invariant "the set of nodes believing themselves to be leader
  has size at most one at every simulated instant" holds across all generated
  schedules, not only the specific partition shape a hand-written test
  happened to choose. This is a natural fit for testing the quorum-decision
  code shown in this entry's Go example, since that function is pure and
  deterministic given its inputs.
- **Fencing token enforcement tests** that specifically attempt an
  out-of-order write, a write bearing an older epoch arriving after a write
  bearing a newer one, has already been accepted, and assert the older write
  is rejected rather than silently applied, exactly as the Python example in
  this entry demonstrates as an executable test.
- **Chaos-engineering exercises in a staging or pre-production environment**
  that combine network partition injection with realistic write load,
  because the anti-pattern's real damage comes from concurrent writes during
  the partition, and a partition test run against an idle cluster proves far
  less than one run under load.
- **Recovery-path testing**, explicitly triggering a partition, letting it
  resolve, and verifying the system's documented reconciliation behavior (an
  automatic rollback of the minority side's writes, as MongoDB documents, or
  a controlled manual reconciliation step) actually executes correctly,
  since an untested recovery path is exactly as likely to be wrong as an
  untested detection path, and is discovered far more expensively if it is
  wrong only during a real incident.

## 16. Observability signals

- **A gauge or count of "current believed leader" reported independently by
  every node**, scraped centrally and alerted on whenever more than one
  distinct node reports itself as leader at the same observed timestamp.
  this is the single most direct signal for split brain and should be
  treated as a page-worthy alert, not a dashboard curiosity, because by the
  time it fires the system may already be accumulating divergent writes.
- **Per-node write acceptance rate, correlated against the leader-belief
  gauge above.** a node that believes it is not the leader but is still
  showing nonzero accepted writes indicates either a bug in the fencing
  enforcement or a gap in what the coordination layer's status reporting
  actually covers.
- **Cluster membership and reachability matrix**, tracking which nodes each
  node currently believes it can reach, refreshed at least as often as the
  heartbeat interval, so that a partition is visible as a graph change (an
  edge disappearing between two specific nodes) well before it manifests as
  a leadership anomaly.
- **Election or promotion event rate.** a healthy cluster promotes a new
  leader rarely, ideally only on genuine node failure or planned
  maintenance. A rising rate of elections, especially elections that
  complete and then are followed by another election within seconds, is a
  strong leading indicator of network flakiness that is approaching, or has
  already crossed into, split-brain territory, and should be investigated
  before it produces an actual dual-leader incident.
- **Fencing token or epoch rejection counter.** if this entry's fencing-token
  safeguard from dimension 8 is in place, a nonzero and especially a rising
  rejection rate is itself a valuable signal, it means the safeguard is
  actively catching a stale-leader write attempt that would otherwise have
  silently corrupted state, and every occurrence deserves investigation into
  why a stale leader was still issuing writes at all.
- **Replication lag distribution across replicas**, since a replica whose
  lag is approaching a configured bound like Redis Sentinel's
  `min-replicas-max-lag` is a replica approaching the edge of the bounded
  risk window discussed in dimension 8, and should be visible before it
  crosses that threshold, not only in the log line generated at the moment
  it does.

## 17. Security and privacy implications

Split brain's most direct security-adjacent implication is data integrity
rather than confidentiality. a system that has silently accepted conflicting
writes on two partitions has, by definition, lost the ability to state with
certainty which value is currently authoritative for any record written
during the partition window, and any downstream authorization, auditing, or
compliance decision made against that data during or shortly after the
incident is made against potentially incorrect state. For systems subject to
audit requirements (financial ledgers, access-control records, consent
records under privacy regulation), a split-brain incident is not merely an
availability or correctness bug, it can constitute a genuine compliance
failure, because the system's own record of "what happened and in what order"
becomes provably unreliable for the duration of the incident.

There is a narrower, more direct security implication in the fencing-token
variant from dimension 8. a fencing token or epoch is only a safeguard if it
cannot be forged or replayed by a party that should not be able to act as
leader. a fencing mechanism that relies on a value the client can simply
choose (rather than one issued and verified by the coordination service
itself) provides no real protection and gives a false sense of safety, which
is arguably worse than no fencing mechanism at all, because it is more likely
to be trusted. any implementation of this pattern should verify the token is
issued by, and independently verifiable against, the authoritative
coordination layer, not merely a value the writing node asserts about itself.

There is no direct confidentiality implication specific to this anti-pattern.
split brain concerns who is allowed to write and what value is authoritative,
not who is allowed to read, and this entry found no basis to claim otherwise.

## 18. References

1. Martin Kleppmann, *Designing Data-Intensive Applications*, O'Reilly Media,
   2017. Chapter 8, "The Trouble with Distributed Systems", sections "The Truth
   Is Defined by the Majority" and "Fencing Tokens".
2. GitHub, "October 21 post-incident analysis", GitHub Blog,
   https://github.blog/news-insights/company-news/oct21-post-incident-analysis/,
   verified 2026-08-02.
3. MongoDB, "Replica Set Elections", MongoDB Manual,
   https://www.mongodb.com/docs/manual/core/replica-set-elections/,
   verified 2026-08-02.
4. MongoDB, "Replica Set Arbiter", MongoDB Manual,
   https://www.mongodb.com/docs/manual/core/replica-set-arbiter/,
   verified 2026-08-02.
5. Redis, "High availability with Redis Sentinel", Redis documentation,
   https://redis.io/docs/latest/operate/oss_and_stack/management/sentinel/,
   sections "Consistency under partitions" and the `min-replicas-to-write`
   worked example, verified 2026-08-02.
6. Elastic, "Quorum-based decision making", Elasticsearch Reference,
   https://www.elastic.co/guide/en/elasticsearch/reference/current/modules-discovery-quorums.html,
   verified 2026-08-02.
7. MySQL, "Chapter 20, Group Replication", MySQL 8.0 Reference Manual,
   https://dev.mysql.com/doc/refman/8.0/en/group-replication.html, verified
   2026-08-02, cited for the "multi-primary" versus unintended dual-writer
   terminology distinction.

## Code examples

### Go: majority-quorum leader election check

```go
package main

import "fmt"

// canBecomeLeader reports whether a node holding one self-vote plus
// reachablePeers additional votes meets strict majority of totalNodes.
func canBecomeLeader(reachablePeers, totalNodes int) bool {
	votes := 1 + reachablePeers
	majority := totalNodes/2 + 1
	return votes >= majority
}

func main() {
	total := 5
	partitionA := 3
	partitionB := total - partitionA

	leaderA := canBecomeLeader(partitionA-1, total)
	leaderB := canBecomeLeader(partitionB-1, total)

	fmt.Printf("partition A size=%d can_elect_leader=%v\n", partitionA, leaderA)
	fmt.Printf("partition B size=%d can_elect_leader=%v\n", partitionB, leaderB)

	if leaderA && leaderB {
		fmt.Println("SPLIT BRAIN: two leaders elected")
	} else {
		fmt.Println("SAFE: at most one partition reaches quorum")
	}
}
```

Run with `go run quorum.go`. Verified output on this machine (go1.x,
2026-08-02).

```
partition A size=3 can_elect_leader=true
partition B size=2 can_elect_leader=false
SAFE: at most one partition reaches quorum
```

### Python: fencing tokens rejecting a stale leader's write

```python
class StorageNode:
    def __init__(self):
        self.data = {}
        self.highest_epoch_seen = 0

    def write(self, key, value, leader_epoch):
        if leader_epoch < self.highest_epoch_seen:
            raise PermissionError(
                f"rejected write from stale leader epoch={leader_epoch}, "
                f"current epoch={self.highest_epoch_seen}"
            )
        self.highest_epoch_seen = leader_epoch
        self.data[key] = value
        return True


def simulate_split_brain_without_fencing():
    store = {}
    store["config"] = "written-by-old-leader"
    store["config"] = "written-by-new-leader"
    store["config"] = "written-by-old-leader-again"
    return store["config"]


def simulate_split_brain_with_fencing():
    node = StorageNode()
    node.write("config", "written-by-old-leader", leader_epoch=5)
    node.write("config", "written-by-new-leader", leader_epoch=6)
    try:
        node.write("config", "written-by-old-leader-again", leader_epoch=5)
    except PermissionError as exc:
        return node.data["config"], str(exc)
    return node.data["config"], "no rejection, this is the bug"


if __name__ == "__main__":
    unsafe_result = simulate_split_brain_without_fencing()
    print(f"without fencing tokens, final value: {unsafe_result!r} (silently corrupted)")

    safe_value, rejection = simulate_split_brain_with_fencing()
    print(f"with fencing tokens, final value: {safe_value!r}")
    print(f"stale write rejected: {rejection}")
    assert safe_value == "written-by-new-leader"
```

Run with `python3 fencing.py`. Verified output on this machine (Python 3,
2026-08-02).

```
without fencing tokens, final value: 'written-by-old-leader-again' (silently corrupted)
with fencing tokens, final value: 'written-by-new-leader'
stale write rejected: rejected write from stale leader epoch=5, current epoch=6
```

### Rust: rejecting an unsafe write-and-read quorum configuration

```rust
struct ReplicaSet {
    total_nodes: usize,
    write_quorum: usize,
    read_quorum: usize,
}

impl ReplicaSet {
    fn new(total_nodes: usize, write_quorum: usize, read_quorum: usize) -> Result<Self, String> {
        if write_quorum + read_quorum <= total_nodes {
            return Err(format!(
                "unsafe config: W({}) + R({}) <= N({}), stale reads possible",
                write_quorum, read_quorum, total_nodes
            ));
        }
        Ok(ReplicaSet { total_nodes, write_quorum, read_quorum })
    }

    fn allows_dual_write_quorum(&self, partition_a: usize, partition_b: usize) -> bool {
        partition_a >= self.write_quorum && partition_b >= self.write_quorum
    }
}

fn main() {
    let strict_majority = ReplicaSet::new(5, 3, 3).expect("valid quorum config");
    let (a, b) = (3usize, 2usize);
    let split = strict_majority.allows_dual_write_quorum(a, b);
    println!("N=5 W=3 R=3, partitions ({}, {}), dual write quorum possible: {}", a, b, split);
    assert!(!split, "majority write quorum must never be reachable on both sides");

    match ReplicaSet::new(5, 2, 2) {
        Ok(_) => println!("this should not happen"),
        Err(reason) => println!("rejected unsafe config: {}", reason),
    }
}
```

Compiled with `rustc -O quorum.rs -o quorum_rs` and run as `./quorum_rs`.
Verified output on this machine (rustc, 2026-08-02, one benign dead-code
warning about unused struct fields kept for clarity, no functional issue).

```
N=5 W=3 R=3, partitions (3, 2), dual write quorum possible: false
rejected unsafe config: unsafe config: W(2) + R(2) <= N(5), stale reads possible
```

Java, Kotlin, C#, and Swift were not exercised for this entry. The quorum and
fencing-token logic shown above is small, backend-coordination code with no
platform-specific idiom that changes its shape in those languages, so a fourth
or fifth translation would repeat the same three constructs (an integer
majority check, a rejection on a stale counter, a validated constructor)
without adding new information, and this entry follows the template's
guidance that omission is acceptable when stated plainly rather than
silently implied.
