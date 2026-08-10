---
name: Leader-Follower Architecture
slug: leader-follower-architecture
family: 05-architectural
category: Architectural
aliases: [Leader-Based Coordination, Master-Election Architecture, Single-Writer Consensus Architecture]
first_described: "Leader and follower as formal, named roles in a production coordination protocol appear in Benjamin C. Reed and Flavio Paiva Junqueira, A Simple Totally Ordered Broadcast Protocol, LADIS 2008 (the Zab protocol behind Apache ZooKeeper), and were later formalized precisely by Diego Ongaro and John Ousterhout, In Search of an Understandable Consensus Algorithm, USENIX ATC 2014 (Raft)"
maturity: canonical
related: [primary-replica, saga, circuit-breaker, event-sourcing, sharding-partitioning]
incompatible_with: []
verified: 2026-08-02
---

# Leader-Follower Architecture

## 1. Name, aliases, and lineage

Leader-Follower Architecture names a whole-system arrangement in which a group
of cooperating nodes elects one of themselves, by protocol rather than by
static configuration, to hold exclusive authority over some class of
coordination decision, while the rest accept and replicate that leader's
decisions and stand ready to replace it if it disappears. The defining act is
the election. A cluster that always treats node A as primary because an
operator typed A into a config file is not running this pattern, it is running
a static primary-backup arrangement. A cluster where any surviving majority of
nodes can, without a human, agree on who leads next, is.

The words "leader" and "follower" as the formal names of the two roles in a
production consensus protocol first appear together in Benjamin C. Reed and
Flavio Paiva Junqueira, "A Simple Totally Ordered Broadcast Protocol",
Proceedings of the 2nd Workshop on Large-Scale Distributed Systems and
Middleware (LADIS '08), ACM, 2008, DOI 10.1145/1529974.1529978, describing the
Zab protocol used by Apache ZooKeeper. The paper states that Zab is a leader
based protocol and that Zab recovers histories and does special processing at
a leadership change to guarantee unique sequence numbers for values proposed
by a leader (Apache ZooKeeper wiki, "Zab1.0",
https://cwiki.apache.org/confluence/display/zookeeper/zab1.0, verified
2026-08-02). Six years later the terminology was formalized with a precise,
provable state machine in Diego Ongaro and John Ousterhout, "In Search of an
Understandable Consensus Algorithm", Proceedings of the 2014 USENIX Annual
Technical Conference, USENIX Association, 2014. Raft names three roles,
leader, follower, and candidate, gives each a monotonically increasing term
number, and proves that at most one leader can be elected per term. Raft did
not invent leader based replication, its own paper credits Paxos (Leslie
Lamport, "The Part-Time Parliament", ACM Transactions on Computer Systems,
16(2), 1998) and Viewstamped Replication (Brian M. Oki and Barbara Liskov,
"Viewstamped Replication, A New Primary Copy Method to Support
Highly-Available Distributed Systems", Proceedings of the 7th ACM Symposium
on Principles of Distributed Computing, 1988) as its intellectual ancestors,
both of which elect a single distinguished node, called a proposer in Paxos
and a primary in Viewstamped Replication, to order client operations. Raft's
achievement was not the idea, it was making the idea teachable and its safety
arguments checkable, which is why the vocabulary of leader, follower, and term
is what most production systems, and this entry, actually use today.

Two namesakes must be told apart, because both share the words "leader" and
"follower" and both live in this same catalog.

The first is Primary-Replica, catalogued separately in this family
(`primary-replica.md`). Primary-Replica is a data-replication pattern. Its
central concern is copying data from one authoritative store to one or more
read-only copies for scaling reads and surviving the loss of the primary. The
role assignment in a classic Primary-Replica deployment (MySQL, PostgreSQL
streaming replication in its simplest form) is frequently static, set by an
operator, and promotion of a replica to primary is frequently a manual or
externally-scripted operation rather than a self-running election among the
nodes. Leader-Follower Architecture, by contrast, is a coordination pattern
whose central concern is agreeing, safely, on who has authority to make an
ordering decision, and the election itself, including how a majority of
surviving nodes chooses a new leader without external help, is the pattern's
subject matter. Every Leader-Follower Architecture deployment also replicates
data from leader to followers, so a reader will correctly notice overlap, but
Primary-Replica can exist with no election protocol at all, and that
difference is why the two are catalogued as separate patterns rather than
aliases of each other.

The second namesake is Leader/Followers, the Pattern-Oriented Software
Architecture concurrency pattern by Douglas C. Schmidt, Carlos O'Ryan, Michael
Kircher, Irfan Pyarali, and Frank Buschmann (catalogued separately under
`09-concurrency/leader-followers.md` in this repository, and described in
Frank Buschmann, Kevlin Henney, Douglas C. Schmidt, "Pattern-Oriented Software
Architecture, Volume 2, Patterns for Concurrent and Networked Objects", Wiley,
2000). That pattern lives entirely inside a single operating-system process.
A pool of threads takes turns being "the leader", the one thread currently
blocked in an event demultiplexer such as `select`, while the rest queue as
followers waiting their turn. There is no network, no node failure to survive,
no consensus, and no majority vote, only a thread-pool synchronizer, typically
a mutex and a condition variable, coordinating role handoff between threads in
one address space. Leader-Follower Architecture as catalogued here operates
across machines, tolerates a machine dying mid-election, and requires a
quorum-based protocol precisely because there is no single memory space and no
single clock the nodes can trust. Reusing the same two English words for a
thread-scheduling trick and a distributed consensus architecture is an
unfortunate historical accident, not a sign that the two patterns are related,
and a reader who arrives here looking for a way to schedule worker threads in
one process should follow the `related` cross-reference to the concurrency
family entry instead.

## 2. Problem and context

A distributed system frequently needs some class of decision made exactly
once and in a single agreed order, even though the work of making that
decision is spread across several machines that can each fail independently,
and even though the network connecting them can partition, reorder messages,
or delay them arbitrarily. Examples of the decision that must be singular.
In what order do these writes to this key land. Which node currently owns
partition seven and is allowed to accept writes for it. Which of these three
identical controller replicas is the one actually allowed to reconcile
desired state against the cluster right now. Who assigns the next work item
so that two workers do not silently claim the same job.

If every node in the cluster were allowed to make that decision independently
and simultaneously, two nodes could order the same two writes differently, two
controllers could both believe they own reconciliation and stamp conflicting
changes onto the same objects, or two schedulers could both hand the same job
to different workers. The failure is not a crash, which would be loud and
visible, it is silent divergence, which is worse, because both halves of the
system continue running and each believes it is correct.

The naive fix, appoint one node as the decision-maker forever by writing its
address into a config file, solves the ordering problem on the happy path and
creates a worse one on the unhappy path. The moment that appointed node
crashes, or is partitioned from the rest of the cluster by a network failure,
the whole system stops making the decision it exists to make, because nothing
in the system is capable of noticing the appointed node is gone and choosing
a replacement without a human paging in at 3 AM to edit the config file again
and restart every dependent service. This is the exact failure Reed and
Junqueira's ZooKeeper paper names as its motivation, that a distributed
application needs to elect a leader dynamically and have the rest of the
system adjust when that leader changes, and it is the exact failure the Raft
paper's whole design is organized around solving with a provably correct,
software-driven election (Ongaro and Ousterhout, 2014, section 5).

Leader-Follower Architecture is the answer that keeps a single point of
ordering authority, because a single point of ordering authority is genuinely
the simplest way to guarantee a total order, while removing the single point
of failure that a statically-appointed leader creates. It does this by
replacing the human with a protocol. Nodes run an election among themselves,
a majority of the cluster must agree on the winner, the winner is given a
monotonically increasing identifier, called a term in Raft and an epoch in
Zab, so that a stale ex-leader who has not yet noticed it lost an election can
never be confused for the current one, and every follower that falls behind
or crashes and restarts can catch up its log to match the current leader's
before it is trusted to serve reads or to vote in the next election.

The context in which this pattern belongs, and not before, has three
properties together. There is a decision that genuinely needs a total order
or a single point of authority, not merely eventual agreement. The system has
three or more nodes so that a majority quorum is meaningful, a two-node
cluster cannot survive the loss of either node without losing quorum, which
this entry returns to in dimension 4. And the system is expected to run long
enough, and be operated by few enough humans, that automating leader
recovery is worth the real cost, in code complexity and in operational
subtlety, that this pattern imposes, a cost detailed in dimension 10.

## 3. Forces

This dimension states engineering judgement about which pressures dominate
and which the pattern trades away, not a sourced fact about any one system.

Consistency versus availability during a partition is the dominant force.
Leader-Follower Architecture makes the CAP-theorem choice explicit and
irreversible for the duration of the partition. A quorum-based election
requires a majority of nodes to be reachable from each other to elect or keep
a leader. When the network splits the cluster into two groups and neither
group contains a majority, the pattern deliberately refuses to let either
side elect a leader, which means the minority side, and if the split is
exactly even neither side, cannot make progress on the decisions this pattern
exists to serialize. This is a design choice, not a bug, because the
alternative, letting both halves of a split cluster each elect their own
leader and keep accepting writes, produces the silent divergence dimension 2
exists to prevent. The pattern trades availability during a partition for
correctness after the partition heals.

Latency of the critical decision path is a second force, and it works in two
opposite directions depending on which operation is being measured. Once a
leader is stable, decisions it makes alone, without waiting for a follower
round trip, are as fast as a single node, which is why per-partition leader
election in Apache Kafka lets any client read the latest committed data from
one broker with no coordination overhead per request (Confluent
documentation, "Kafka Replication",
https://docs.confluent.io/kafka/design/replication.html, verified
2026-08-02). But a write that must be durable, and therefore must be
acknowledged by a quorum of followers before the leader reports it committed,
pays the round trip latency to the slowest node inside that quorum, every
single time, forever. Adding more followers to increase fault tolerance
directly increases the number of nodes whose response time can sit on this
critical path.

Fault-tolerance budget is a third force, and it is quantized in an
uncomfortable, non-linear way that surprises engineers used to reasoning
about redundancy linearly. A cluster of three nodes tolerates the loss of one
node before it loses its ability to form a majority and therefore loses its
ability to elect a leader at all. A cluster of five tolerates the loss of
two. A cluster of four, despite costing one more machine than three, still
only tolerates the loss of one, because three of four is still the smallest
majority, so the fourth machine buys no additional fault tolerance over a
three-node cluster, only additional cost and additional quorum latency. This
is why production Raft and Zab deployments are conventionally sized at odd
numbers, three or five, and this convention is directly attributable to the
majority-quorum math, not to superstition.

Recovery time versus steady-state overhead is the fourth force. A short
election timeout detects a dead leader quickly and shortens the window during
which the system cannot make its coordinated decision, but a short timeout
also makes the cluster prone to spurious re-elections triggered by ordinary
transient network jitter, and every re-election, even a spurious one, costs a
brief availability gap while the new leader is confirmed and while it
re-establishes which entries followers have actually persisted. etcd's own
documentation states that with its default election timeout of one second,
clients can experience one to two seconds of write unavailability during a
leader election, and for that reason recommends running etcd across three or
more nodes precisely so that elections resolve quickly and so that planned
maintenance windows can be scheduled to avoid forcing an election at an
inconvenient moment (etcd FAQ, https://etcd.io/docs/v3.2/faq/, verified
2026-08-02).

Operational and cognitive complexity is the force the pattern most visibly
loses to its simpler alternatives. A team adopting this pattern by hand-rolling
its own leader election is choosing to reimplement one of the hardest,
best-studied problems in distributed systems, and the historical record of
attempts that got subtle edge cases wrong, split votes that never converge,
followers that ack an entry the leader itself later overwrites, a network
partition that produces two leaders because a term comparison was implemented
with a signed integer that wrapped, is long enough that the field's default
advice, echoed by both the Raft paper's stated motivation and this entry's
dimension 8, is to adopt a proven implementation such as etcd's Raft library
or ZooKeeper rather than write a bespoke one.

## 4. Applicability and non-applicability

Reach for Leader-Follower Architecture when the following hold together.

- A specific class of decision genuinely needs a single, agreed, total order,
  not merely eventual convergence, for example which node may currently write
  to a given shard, which controller replica is permitted to reconcile a
  resource, or in what order a replicated log's entries are committed.
- The cluster has, or can reasonably be sized to have, three or more voting
  members, so that a majority quorum is a meaningful, non-trivial concept.
- The system must survive the loss of individual nodes without a human
  manually reassigning the leader role, because it runs unattended, at a
  scale where paging a human for every leader failure is not viable, or
  because the required recovery time is shorter than a human can act in.
- The workload can tolerate the write latency of a quorum acknowledgement,
  because the correctness guarantee this pattern buys is paid for on the
  write path, not the read path.
- A mature, already-audited implementation of the election and replication
  protocol is available for the team's platform, for example etcd, Consul,
  ZooKeeper, or a Raft library, so the team is adopting a component rather
  than authoring a consensus algorithm from first principles.

Do NOT reach for it, and choose the alternative named in each line instead,
when any of the following hold.

- The system is a single, unpartitioned data store with no need to survive
  losing the machine it runs on. A quorum-election architecture has nothing
  to elect over, adopt a plain single-node database with periodic backups
  instead.
- The consistency requirement is "eventually the same everywhere" rather
  than "always one agreed order right now", for example a shopping cart
  merged across devices, or a set of counters that only need to converge.
  Adopt a conflict-free replicated data type or a gossip-based
  eventually-consistent store instead, where any node can accept a write at
  any time and the system resolves conflicts later, because that removes the
  entire cost of quorum writes and leader failover for a workload that never
  needed a single point of ordering authority.
- The team needs data replication for read scaling and disaster recovery,
  and role reassignment on failure can be a supervised, semi-manual runbook
  step rather than an automatic sub-second election. Adopt Primary-Replica
  as catalogued separately in this family, which is materially simpler to
  operate and reason about because it removes the election protocol
  entirely.
- The coordination need is local to threads inside one process, not spread
  across machines. Adopt the Leader/Followers concurrency pattern from
  `09-concurrency` instead, a thread pool synchronizer, not a network
  protocol.
- The cluster genuinely cannot be sized to three or more voting members, for
  example a two-node edge deployment with no room for a third witness node
  or arbiter. A two-node majority quorum requires both nodes, so losing
  either one halts the system exactly as a single unreplicated node would,
  which means the pattern is paying its full operational cost for zero
  fault-tolerance benefit. Either add a third, possibly lightweight, witness
  node, or drop the pattern and accept manual failover.
- The write path cannot tolerate the added round-trip latency of a quorum
  acknowledgement, for example a high-frequency trading matching engine
  where single-digit microseconds matter. Adopt a design that keeps a
  single authoritative process and treats replication as a separate,
  asynchronous, out-of-band concern instead of putting it on the commit
  path.

## 5. Structure

A leader-follower cluster is built from four participants and one protocol
tying them together.

A node is a process that can hold any of the roles below and that
persists whatever state the protocol requires it to remember across a
restart, at minimum the highest term or epoch it has observed and the vote it
cast in that term, so that it cannot be tricked into voting twice in the same
term after a crash and restart.

The leader is the single node currently holding authority for the
decision class this deployment coordinates. It is responsible for accepting
new client requests that require ordering, appending them to its own
replicated log, replicating each entry to followers, and declaring an entry
committed only once it has confirmation from a majority of the cluster,
including itself, that the entry is durably persisted. It is also responsible
for sending periodic heartbeats to followers, both to prove it is alive and
to prevent followers from starting an unnecessary election.

A follower is a node that accepts log entries and heartbeats from the
current leader, persists what it receives, and never originates a client
decision on its own. It participates in elections by voting when a candidate
asks, and it does not vote twice in the same term or epoch. If a follower
stops hearing from a leader within its election timeout, it transitions to
candidate.

A candidate is the transient role a follower enters when it believes the
leader has failed. It increments the term it last observed, votes for
itself, and requests votes from every other node. If it receives votes from a
majority of the cluster before the term times out again, it becomes leader.
If it does not, either because votes were split across multiple simultaneous
candidates or because a message from a higher term arrived, it reverts to
follower and the cluster tries again in a new, higher term.

The term or epoch is a monotonically increasing integer, owned by no
single node, that every message in the protocol carries. Any node that
observes a term higher than its own immediately adopts that term and steps
down to follower if it was leader or candidate. This single integer is what
makes it safe for a stale leader, one that has been partitioned away and does
not yet know an election happened without it, to be ignored the moment it
tries to rejoin, because every other node can compare its term against the
message and reject it on sight.

The quorum, a majority of the total voting membership, is not a
participant but a property the protocol enforces at two separate points, at
election, where a candidate needs a majority of votes to become leader, and
at commit, where the leader needs a majority of acknowledgements before it
may report a log entry as durably committed to whoever asked for it. Both
uses of quorum share one mathematical guarantee, that any two majorities of
the same set of nodes must overlap by at least one node, which is the fact
that prevents two disjoint groups from each electing a different leader in
the same term, or from each committing a conflicting entry.

## 6. ASCII structure diagram

```
                         term / epoch: N
                (a single monotonically increasing
                 counter every message carries)

         +----------------------------------------+
         |                LEADER                    |
         |  - accepts client writes                  |
         |  - appends to its own log                 |
         |  - replicates entries to followers        |
         |  - commits once quorum acks the entry     |
         |  - sends periodic heartbeats               |
         +----------------------------------------+
             |  AppendEntries / heartbeat   |
     +-------+                              +-------+
     v                                              v
+-----------+                                +-----------+
| FOLLOWER  |                                | FOLLOWER  |
| persists   |                                | persists   |
| entries    |                                | entries    |
| votes once |                                | votes once |
| per term   |                                | per term   |
+-----------+                                +-----------+
     |                                              |
     |          election timeout expires,           |
     |          no heartbeat arrived in time         |
     v                                              v
+-----------------------------------------------------+
|                     CANDIDATE                        |
|  - increments term, votes for itself                 |
|  - sends RequestVote to every other node              |
|  - becomes leader on a MAJORITY of votes for this term|
|  - reverts to follower on a higher term seen, or on   |
|    a split vote after its election timeout expires    |
+-----------------------------------------------------+

 quorum = floor(N / 2) + 1 of the cluster's voting nodes
 any two quorums of the same cluster must share at least
 one node, which is what prevents two leaders in one term
```

## 7. Dynamics

Two sequences matter, ordinary steady-state replication and leader failover.

Steady-state write replication, once a leader is established, proceeds as
follows. A client sends a write to the leader. The leader appends the entry
to its own local log at the next available index, still tagged with the
current term. The leader sends the entry to every follower in an
AppendEntries-style message that also carries the index and term of the
entry immediately before it, so that a follower can detect a gap in its own
log and refuse the entry until the gap is filled. Each follower that
successfully appends the entry, meaning its own preceding entry matched what
the leader claimed, persists it and replies with an acknowledgement. Once the
leader has received acknowledgements from a majority of the cluster,
including its own local append, it marks the entry committed, applies it to
its own state, and only then reports success back to the original client. On
the next heartbeat or the next entry, the leader informs followers of the new
commit index so they can apply the entry locally too. A follower's log entry
is therefore visible to the follower's own replicated state machine strictly
after it is known to be safe, never before, which is what lets a follower be
promoted to leader later without losing a committed write.

Leader failover proceeds as follows. A follower's election timeout, randomized
within a bounded range specifically so that not every follower times out at
the same instant and starts a simultaneous, self-defeating election, expires
without a heartbeat having arrived from the current leader. The follower
transitions to candidate, increments the term by one, votes for itself, and
sends RequestVote messages to every other node, including, in Raft, the
index and term of its own most recent log entry, so that a node whose log is
behind cannot win an election and subsequently overwrite entries a majority
already committed. Each other node grants its vote if, and only if, it has
not already voted in this term, and the candidate's log is at least as
up-to-date as its own. If the candidate collects votes from a majority
before its own election timeout expires again, it transitions to leader,
immediately sends a heartbeat to every other node to suppress further
elections, and begins accepting client writes in the new term. If two
candidates start elections in the same term and neither collects a majority,
because votes were split between them, both election timeouts expire again,
each node increments the term once more, and the randomized timeout,
statistically, breaks the tie within one or two additional rounds. Once a new
leader is established, any node still under the illusion that it holds an
earlier term, including a previous leader that was merely partitioned rather
than actually crashed, learns of the higher term the instant it exchanges a
single message with any current cluster member and immediately steps down,
which is the mechanism that guarantees the old leader can never again commit
a write the new leader and its followers disagree with.

```
Client       Leader(term N)    Follower A    Follower B     Follower C
  |  write ------->|                |             |              |
  |                | append local   |             |              |
  |                |--AppendEntries->|            |              |
  |                |--AppendEntries--------------->|             |
  |                |--AppendEntries-------------------------------->
  |                |<---- ack ------|             |              |
  |                |<---- ack ---------------------|              |
  |                |  quorum reached (2 of 3 replies + self)      |
  |<-- success ----|                |             |              |
  |                |  X leader crashes / partitioned              |
  |                                 |  election timeout expires   |
  |                                 |  becomes candidate, term N+1|
  |                                 |--RequestVote------------------>
  |                                 |<---- vote granted -------------
  |                                 |  quorum reached, becomes leader
  |                                 |--heartbeat(term N+1)---------->
  |  write ------------------------->|                              |
  |                                 |  (old leader, if it returns,   |
  |                                 |   sees term N+1 and steps down)|
```

## 8. Implementation variants

Term-based voting, exemplified by Raft. Every message carries a strictly
increasing integer term, a candidate wins by collecting votes strictly for
that term, and safety comes from the invariant that a node votes at most once
per term and a candidate must have an up-to-date log to be granted a vote.
This is the variant that dominates new systems today because Raft's paper
was written explicitly to be more understandable than Paxos, and its
correctness proof is checkable by an engineer without a distributed-systems
research background (Ongaro and Ousterhout, 2014, abstract and section 1).

Atomic-broadcast based election, exemplified by Zab, ZooKeeper's protocol.
Zab structures its work into two phases, leader election plus
synchronization, followed by atomic broadcast, and every proposal carries an
epoch number that changes at each leadership change, giving the same
stale-leader-rejection guarantee as a Raft term but arrived at through a
somewhat different formal structure, one built to also serve as a general
purpose broadcast primitive that ZooKeeper's own znode watches and sessions
are layered on top of, rather than being purpose-built only for a replicated
log (Apache ZooKeeper wiki, "Zab", https://cwiki.apache.org/confluence/display/ZOOKEEPER/Zab,
verified 2026-08-02).

Lease-based leadership, exemplified by Kubernetes control-plane leader
election. Rather than running a full voting protocol among the application's
own processes, the candidates instead compete to write their identity into a
single record, a Lease object backed by a strongly-consistent store, that
carries an expiry time. Whichever candidate successfully writes the lease
first holds it until the lease's time-to-live elapses without a successful
renewal, at which point any other candidate may claim it. The Kubernetes
documentation states plainly that Leases guarantee only one
instance of a component is running at any given time, and that this pattern
is what `kube-controller-manager` and `kube-scheduler` use for high
availability, with only one instance actively running while the rest stand by
(Kubernetes documentation, "Leases",
https://kubernetes.io/docs/concepts/architecture/leases/, verified
2026-08-02). This variant pushes the hard part of consensus, quorum voting
and log replication, into the already-consistent store the lease lives in,
which is why it is common in systems that already depend on etcd or a
similarly strongly-consistent key-value store for other reasons, at the cost
of that store becoming a dependency the leader-election path cannot function
without.

Per-partition leadership, exemplified by Apache Kafka. Rather than one leader
for the entire cluster, Kafka elects a leader independently for every
partition of every topic, each with its own set of in-sync replicas, so a
single broker can simultaneously be the leader for some partitions and a
follower for others. Followers pull new records from their partition's
leader over a single ordered socket connection and write them to their own
local log in the same order the leader wrote them, then acknowledge, and a
write is only considered committed once every in-sync replica has
acknowledged it (Confluent documentation, "Kafka Replication",
https://docs.confluent.io/kafka/design/replication.html, verified
2026-08-02). This variant trades a single global bottleneck for many small,
independently-electable bottlenecks, at the cost of needing a separate
mechanism, historically ZooKeeper and in newer Kafka deployments Kafka's own
built-in KRaft controller quorum, to track which broker leads which
partition and to run elections across potentially thousands of partitions
efficiently rather than one at a time.

Language-idiomatic shape. Because this pattern coordinates whole processes
across a network rather than objects inside one runtime, it rarely appears as
a hand-rolled class hierarchy the way a Gang of Four pattern does. In
practice a team either embeds a battle-tested library, Raft implementations
such as `etcd/raft` in Go or `raft-rs` in Rust, or delegates the entire
concern to an external coordination service, ZooKeeper, etcd, or a
Kubernetes Lease, reached over its client API. The idiomatic implementation
choice is therefore "adopt a library or a service" far more often than "write
the state machine yourself", which the code examples that close this entry
make explicit by simulating the protocol's decision logic in isolation rather
than building a network-facing implementation from first principles.

## 9. Known production uses

Apache Kafka. Every partition of every topic in a Kafka cluster is
assigned one leader replica and zero or more follower replicas. Producers and
consumers interact only with the partition's current leader, followers
continuously pull and persist the leader's log, and a write is acknowledged
back to the producer only once every replica in the in-sync replica set has
confirmed it, which Kafka's own documentation states directly, that a write
to a Kafka partition is not considered committed until all in-sync replicas
have received it (Confluent documentation, "Kafka Replication",
https://docs.confluent.io/kafka/design/replication.html, verified
2026-08-02; corroborated by the Apache Kafka project wiki, "Kafka
Replication", https://cwiki.apache.org/confluence/display/KAFKA/Kafka+Replication,
verified 2026-08-02).

Apache ZooKeeper, used directly by countless downstream systems including
historically Kafka and HBase for coordination. ZooKeeper's own ensemble
elects one server as leader using the Zab protocol, and every other server in
the ensemble runs as a follower, forwarding write requests to the leader and
acknowledging the leader's proposals. The originating paper describes Zab as
a leader-based protocol conceptually similar to Paxos, purpose-built to give
ZooKeeper the totally-ordered broadcast it needs for its own znode tree and
watch mechanism (Reed and Junqueira, LADIS 2008, DOI 10.1145/1529974.1529978,
verified via the paper's listing at
https://dl.acm.org/doi/10.1145/1529974.1529978, 2026-08-02).

etcd, the strongly-consistent key-value store Kubernetes itself uses as
its cluster's source of truth. etcd's server implements the Raft consensus
protocol directly for its own internal replication, with data flowing from a
single elected leader to followers, and a follower forwarding any proposal it
receives from a client on to the leader rather than accepting it locally
(etcd Go package documentation, "raft package",
https://pkg.go.dev/go.etcd.io/etcd/raft/v3, verified 2026-08-02). etcd's own
FAQ states that with the default one-second election timeout, a leader
election costs clients one to two seconds of write unavailability, and
recommends a minimum of three nodes specifically to keep that election fast
(etcd FAQ, https://etcd.io/docs/v3.2/faq/, verified 2026-08-02).

Kubernetes control plane high availability. In a highly available
Kubernetes cluster, multiple replicas of `kube-controller-manager` and
`kube-scheduler` run simultaneously, but only one replica of each is
permitted to act at any moment, coordinated through a Lease object in the
`coordination.k8s.io` API group that functions as the leader-election
mechanism, with the non-leading replicas on standby ready to take over the
moment the current lease holder fails to renew it in time (Kubernetes
documentation, "Leases",
https://kubernetes.io/docs/concepts/architecture/leases/, verified
2026-08-02).

## 10. Consequences

Positive consequences.

- A single, agreed order for the class of decision the leader owns, without
  requiring every node to run an expensive distributed transaction protocol
  for every individual operation, because ordering authority is established
  once per leadership term rather than negotiated on every write.
- Automatic recovery from the loss of any minority of the cluster's nodes,
  including the leader itself, with no human intervention required to
  restore the ability to make the coordinated decision, which is precisely
  the property a statically-configured primary lacks.
- Read scaling on data that does not require the strongest consistency
  guarantee, because followers hold a complete, only slightly lagging copy
  of the leader's committed state and can serve reads that tolerate that lag
  without touching the leader at all.
- A single, well-defined point in the system, the current leader, where
  invariants that depend on total ordering, such as "this counter increments
  exactly once per event" or "these two writes to the same key must be
  applied in the order they were issued", can be enforced with local logic
  rather than a distributed check on every write.

Negative consequences.

- Every write that must be durable pays the latency of a round trip to a
  majority of the cluster, not merely to the nearest node, which sets a hard
  floor on write latency that no amount of leader-side optimization can
  remove, because the guarantee lives in the quorum acknowledgement, not in
  the leader's local disk.
- The cluster's fault tolerance is quantized by quorum math rather than
  scaling smoothly with node count, so operators must understand that four
  nodes tolerate exactly one failure, the same as three, before spending the
  fourth machine's budget expecting otherwise.
- A leader election, even a healthy one triggered by a planned restart
  rather than a crash, is a brief but real availability gap on the write
  path, which etcd's own operators are told to expect and to plan
  maintenance windows around (etcd FAQ, verified 2026-08-02, cited above).
- Implementing the election and replication protocol correctly is genuinely
  hard, and a homegrown implementation is one of the more common places a
  distributed system silently loses data or briefly runs with two leaders,
  which is why the field's practical advice, echoed throughout this entry,
  is to adopt a proven implementation rather than write one.
- During a network partition where no side holds a majority, the pattern
  deliberately halts the decision it exists to coordinate rather than risk
  two disagreeing leaders, which is correct behavior but is frequently
  mistaken by an on-call engineer for an outage the cluster should be
  fighting harder to route around, when in fact the correct operator action
  is usually to restore connectivity, not to force an election.

## 11. Failure modes and misuse

This dimension draws on analytical judgement and practitioner experience
about how the pattern breaks in production, not on a single citable source
for each row.

| Symptom observed | Underlying cause | Fix |
|---|---|---|
| Writes intermittently time out and the cluster keeps electing a new leader every few seconds under normal load | Election timeout is set too close to typical heartbeat or network latency, so ordinary jitter is mistaken for a dead leader | Widen the election timeout relative to the measured heartbeat interval and network round-trip distribution, and confirm the timeout is randomized per node rather than identical, which is what prevents every follower from starting a candidacy in the same instant |
| Two processes both believe they are the current leader and both accept writes for a short window after a network blip | The application accepted a write from a leader without checking that the leader's term or lease is still the current one, most often because a stale in-process cache of "am I leader" was consulted instead of re-verifying against the coordination service on the write path | Attach the current term, epoch, or fencing token to every state-mutating operation the leader performs downstream, and require the downstream system to reject any operation carrying a token older than the highest token it has already seen, so a stale leader's writes are refused even if the leader itself has not yet noticed it lost the election |
| A newly elected leader appears to lose recently committed writes that clients were told succeeded | The election protocol was implemented without the log-completeness check, so a candidate whose log lags behind was allowed to win an election and then overwrote entries a prior majority had already committed | Verify the election implementation refuses to grant a vote to a candidate whose most recent log entry is older, by index and term, than the voter's own, which is precisely the safety property Raft's election restriction is built to guarantee, and prefer a maintained library over a bespoke implementation of this check |
| The cluster has five healthy nodes but cannot elect a leader, or elects one and loses it repeatedly | A network partition or a misconfigured load balancer is splitting the cluster into groups smaller than a majority, or is routing different candidates' vote requests to different, non-overlapping subsets of the cluster | Confirm every node can reach every other node directly on the election port, not only through a proxy that could itself be partitioning traffic, and confirm the configured voting membership on every node agrees, because a membership mismatch after a botched scale-up can make quorum arithmetic wrong on some nodes |
| A single client action, such as adding a fourth node to a three-node cluster, causes a temporary total outage | The membership change was applied non-atomically, so for a window some nodes believe the voting membership is three and others believe it is four, which can allow two disjoint groups to each believe they hold a majority | Use the coordination library's built-in membership-change protocol, such as Raft's joint-consensus reconfiguration, rather than restarting nodes with a new static peer list, because the joint-consensus step exists specifically to prevent two simultaneous, disjoint quorums during a membership change |
| Followers fall further and further behind the leader's log and never catch up, eventually failing every subsequent election because their log is too stale to win a vote | A follower is being throttled or starved of resources relative to the leader's write rate, or the leader is not enforcing a log-compaction or snapshotting policy, so the amount of history a rejoining follower must replay grows without bound | Implement periodic snapshotting so a lagging or rejoining follower can install a compact snapshot of current state rather than replaying every historical entry, and monitor per-follower replication lag as a first-class metric so a starving follower is caught before it becomes unable to ever win an election |

## 12. Trade-off matrix

Compared against the named alternatives introduced in dimension 4, across the
forces named in dimension 3.

| Force | Leader-Follower Architecture | Primary-Replica (static, manual failover) | Leaderless quorum (Dynamo-style, any node accepts writes) | Two-Phase Commit coordinator |
|---|---|---|---|---|
| Consistency guarantee on the coordinated decision | Total order under a single leader per term, provably safe across partitions | Total order while the primary is healthy, but a manual or scripted promotion can momentarily create ambiguity about who is primary | Eventual consistency by default, strong consistency only if the client explicitly reads and writes with overlapping quorums (R plus W greater than N) | Strong, atomic all-or-nothing consistency across participants for a single transaction |
| Failure recovery | Automatic, sub-second to low-single-digit-seconds, no human required | Manual or scripted, typically minutes, requires a human or a runbook to trigger promotion | No leader to lose, individual node failure has minimal impact on availability | The coordinator is itself a single point of failure, and its crash mid-commit can leave participants blocked indefinitely awaiting a decision |
| Write latency | One round trip to a quorum of nodes, fixed floor regardless of leader-side optimization | Comparable to a single node while healthy, since the primary need not wait for replica acknowledgement in the simplest configurations | Comparable to Leader-Follower Architecture when using quorum reads and writes, since it also waits for a quorum, but with no leader to route through first | Two full round trips, prepare then commit, to every participant, typically the highest latency of the four |
| Operational complexity | High, requires understanding term or epoch semantics, quorum sizing, and membership-change protocols | Low, a single authoritative node and asynchronous or synchronous copies, with promotion as a documented manual step | Moderate to high, requires reasoning about read-repair, vector clocks or version vectors, and conflict resolution | High, requires a durable coordinator log and careful handling of participant blocking on coordinator failure |
| Best fit | A decision that must have one agreed order and must recover automatically without a human | Read scaling and disaster recovery where a brief, human-mediated failover window is acceptable | Data with no inherent total order requirement, where availability under partition matters more than immediate consistency | A single, short-lived, multi-participant transaction that must be atomic, not a long-running coordination role |

## 13. Related and incompatible patterns

Primary-Replica, catalogued in this same family, composes tightly with this
pattern rather than competing with it in most real deployments, because the
leader in a Leader-Follower Architecture deployment is, from the data
replication perspective, exactly a primary, and its followers are exactly
replicas. The distinction this entry draws throughout, election versus static
assignment, is precisely the axis along which a team decides which of the two
entries to reach for, and a team that starts with Primary-Replica's manual
failover frequently migrates toward this pattern later specifically to
automate the promotion step, without changing anything about how data itself
is shipped from leader to followers.

Saga composes with this pattern at a different layer of the system. A saga
coordinates a multi-step business transaction across several independently
owned services, each of which may itself be built on a leader-follower
cluster internally for its own storage consistency. The saga does not need to
know or care that any one of its participating services runs an internal
election protocol, which is exactly the point, this pattern's job is to keep
one service's internal state consistent, not to coordinate across service
boundaries, which is the job Saga exists to do instead.

Event Sourcing pairs naturally with the replicated-log shape this pattern
produces, because a leader's committed log, the sequence of entries a
majority has acknowledged, is structurally the same thing as an event
sourcing system's append-only event log, and several production systems, most
directly Kafka, are used as the event store underneath an event-sourced
service specifically because Kafka's own per-partition leader-follower
replication is already providing the durability and ordering guarantee the
event log needs.

Sharding and Partitioning composes with this pattern at scale, because a
single leader-follower group has a practical ceiling on write throughput set
by the round trip to its slowest quorum member, and the standard way past
that ceiling is not a bigger single group but many smaller leader-follower
groups, each owning one shard, exactly as Kafka runs one leader election per
partition rather than one for the whole cluster, described in dimension 8.

Circuit Breaker is a defensive pattern a client of a leader-follower cluster
should compose alongside it, because a client that keeps retrying writes
against a cluster that has lost quorum and cannot elect a leader will, absent
a circuit breaker, keep generating load and log noise against a system that
cannot currently make progress, worsening the operational picture during
exactly the incident where clear signal matters most.

No pattern in this catalog is architecturally incompatible with
Leader-Follower Architecture in the sense of being unable to coexist in the
same system, though as dimension 1 states plainly, it should never be
conflated with, or treated as a substitute for, the same-named Leader
Followers thread-pool concurrency pattern, which solves an entirely different
problem at an entirely different scope.

## 14. Refactoring path in and out

Introducing this pattern into a system that currently has a single,
unreplicated authority for some decision, or a statically-assigned primary
with manual failover, proceeds in stages, each independently shippable and
each leaving the system in a working state.

First, identify the exact decision that needs a single agreed order, and
resist the temptation to put the entire application behind one leader
election, because the smallest scope that genuinely needs total ordering is
usually far smaller than "everything", the way Kafka elects a leader per
partition rather than per cluster.

Second, introduce a replicated log for that specific decision behind the
existing interface, so the rest of the system keeps calling the same method
or the same API it always did, while internally that call now appends to a
log rather than mutating state directly, and adopt an existing library or
coordination service, Raft library, ZooKeeper, or a Lease-backed store,
rather than authoring the election and replication logic from scratch, per
the guidance in dimension 8 and dimension 10.

Third, run the new leader-follower group in shadow mode alongside the
existing single authority, replicating the same decisions to both, and
compare outputs, before cutting reads or writes over, so any divergence
between the old system and the new group's committed log is caught while
the old system is still the source of truth and no user-visible harm can
result from a bug in the new path.

Fourth, cut writes over to the new group, keeping the old single authority
available briefly as a fallback with an explicit, monitored kill switch,
then remove the old authority once the new group has run correctly through
at least one real leader failover in production, because a leader-follower
group that has never actually lost its first leader has not yet exercised
the part of the pattern that justified adopting it.

Removing this pattern, when the decision it coordinates has shrunk to the
point that a single node with manual failover would now suffice, for example
because the workload moved almost entirely onto a downstream managed
database that already provides its own leader election, proceeds by first
confirming, over a real observation window, that leader elections in the
existing group are rare and that the operational cost of running the
election protocol, not merely its presence, has become the dominant
maintenance burden. Then replace automatic election with a single
designated node and a documented, tested manual promotion runbook, which is
precisely the direction dimension 13's cross-reference to Primary-Replica
describes, verify the runbook by actually executing a manual promotion in a
staging environment before relying on it, and only then decommission the
election and quorum machinery, never before the manual path has been proven
to work under the same conditions the automatic path was handling.

## 15. Testing and verification

This dimension is largely practitioner technique rather than a sourced
claim, because how a team actually tests a consensus-based architecture is
practice, not a fact any one paper asserts.

What becomes genuinely easy to test because of this pattern. The decision
logic that runs once a leader is established, accept a write, append it,
replicate it, is ordinary sequential code once the leader role is a given,
and can be unit tested with no network at all by constructing a leader
object and a set of in-memory follower stand-ins, exactly the shape the code
examples closing this entry use to demonstrate quorum commit and epoch
fencing without any real networking.

What becomes genuinely hard, and what a team must deliberately build test
infrastructure for rather than skip. The election protocol itself must be
tested under adversarial conditions no unit test naturally produces, message
loss, message reordering, message duplication, an artificially delayed
network partition that heals at an inconvenient moment, and a node crashing
mid-write before it has persisted the entry it just acknowledged. The
practical technique that has proven itself across the Raft, TiKV, and
CockroachDB ecosystems is deterministic simulation testing, running many
instances of the protocol inside a single test process with a simulated
clock and a simulated, intentionally hostile network layer that can be
instructed to drop, delay, duplicate, or partition messages on command, so
that a failing seed can be replayed exactly and the same bug reproduced
deterministically, rather than chasing a flaky failure that only appears
once in a thousand runs against a real network.

A second essential technique is Jepsen-style linearizability checking
against a real, running cluster, deliberately injecting network partitions
and process kills with a tool such as `iptables` rules or a proxy that can
sever connections on command, then recording every client-observed operation
and its result, and afterward running a linearizability checker against that
recorded history to confirm no client ever observed a result inconsistent
with a single, valid total order, which is the class of test that has
historically found the subtlest bugs in production consensus
implementations, because it tests the actual observable behavior of the
whole system rather than any one internal invariant in isolation.

Test doubles that apply directly. A fake, in-memory coordination service
that implements the same client interface as the real ZooKeeper or etcd
client but runs entirely inside the test process is the standard way to test
application code that merely consumes leader election, such as running a
reconciliation loop only while the process is the leader, without paying the
cost of standing up a real multi-node cluster for every test run, reserving
the real cluster, and the network-fault-injection techniques above,
specifically for tests of the election and replication protocol itself.

## 16. Observability signals

This dimension is practitioner judgement about what a healthy versus a
struggling deployment looks like, not a sourced claim.

A healthy deployment shows a stable current leader and current term or epoch
that changes rarely, on the order of once per planned maintenance event, not
several times an hour. It shows every follower's replication lag, measured
both in log entries and in wall-clock time behind the leader's latest
committed entry, staying close to zero and bounded, not growing without a
matching increase in write throughput to explain it. It shows the time from
election start to a new leader being confirmed staying within the
configured election timeout's expected range, not repeatedly hitting the
timeout and retrying. And it shows commit latency, the time from a client's
write request to the leader reporting it committed, tracking closely with
network round-trip time to the nearest surviving quorum, not spiking
independently of network conditions.

Log and trace what a struggling deployment reveals before it becomes an
outage. A rising count of leadership changes per hour is the earliest signal
that something, usually network instability or an undersized election
timeout relative to real jitter, is destabilizing the cluster, and should be
tracked as a first-class time series, not merely logged as an event, per
node and cluster-wide. Per-follower replication lag trending upward on a
subset of followers, rather than all of them, usually points at a
resource-starved or network-degraded specific machine rather than a
cluster-wide problem, and is exactly the metric the failure mode table in
dimension 11 names for catching a follower before it becomes too stale to
ever win an election. Vote-request rejection counts, broken down by reason,
already-voted-this-term versus candidate-log-too-stale, distinguish a benign
split vote resolving itself from a genuinely stuck node whose log has fallen
so far behind it can structurally never win, which needs an operator to
intervene rather than wait.

What a healthy dashboard looks like at a glance. A single, unambiguous
current leader identity and current term visible cluster-wide with no
disagreement between nodes about either value, replication lag hovering near
zero across every follower, and a leadership-change counter that is flat
for long stretches and only moves in expected, deliberate steps. A failing
one shows leadership flapping between two or more nodes in rapid succession,
replication lag on one or more followers climbing without bound, and, most
dangerously, two nodes simultaneously reporting they believe themselves to
be the current leader, which, if it is ever observed even momentarily, is a
correctness bug in the fencing logic described in dimension 11's second row,
not a transient condition to shrug off.

## 17. Security and privacy implications

The pattern's attack surface centers on the election and replication
channel itself, because whoever can inject or forge messages on that channel
can influence who the cluster believes is its leader, or can trick a
follower into applying entries that never went through a legitimate quorum.

Authentication and mutual TLS between cluster members on the election and
replication ports are the primary control, because an unauthenticated
election protocol lets any network participant that can reach the port send
forged RequestVote or AppendEntries-equivalent messages and either trigger
spurious elections as a denial-of-service, or, in the worst case, get a
malicious node admitted to the voting membership if membership changes are
themselves not authenticated and authorized. Production coordination
services, etcd and ZooKeeper among them, support peer-to-peer TLS
specifically to close this surface, and running the election port without it
on any network that is not fully trusted end to end is the single most
consequential security misconfiguration this pattern is exposed to.

Fencing tokens, introduced in dimension 8 and dimension 11 as a correctness
mechanism against a stale leader continuing to act, are also a security
control against a compromised or rogue node that continues issuing writes
after it has lost leadership, because a downstream system that enforces
monotonic fencing tokens on every state-mutating request rejects the stale
node's writes on structural grounds, not merely on the honesty of the stale
node itself, which matters in a threat model where a node might be
compromised rather than merely partitioned.

Data privacy implications are indirect but real. Because followers hold a
complete, only slightly-lagging copy of everything the leader has committed,
every follower in the cluster is, from a data-exposure standpoint, an
equally sensitive target, and access controls, encryption at rest, and
audit logging must be applied uniformly across every follower, not
concentrated on the leader alone, precisely because the pattern's whole
purpose is to make followers hold a faithful, near-real-time copy of
leader-authoritative state.

Where this pattern is silent, stated plainly rather than invented as a
concern. The election protocol itself says nothing about authorization of
which client requests a leader should accept, that is the responsibility of
whatever application layer sits above the replicated log, and the protocol
says nothing about encrypting the content of the replicated entries at rest,
which is a storage-layer concern each implementation and deployment must
address on its own.

## 18. References

1. Benjamin C. Reed and Flavio Paiva Junqueira, "A Simple Totally Ordered Broadcast Protocol", Proceedings of the 2nd Workshop on Large-Scale Distributed Systems and Middleware (LADIS '08), Association for Computing Machinery, 2008, article 2, DOI 10.1145/1529974.1529978, https://dl.acm.org/doi/10.1145/1529974.1529978, verified 2026-08-02.
2. Diego Ongaro and John Ousterhout, "In Search of an Understandable Consensus Algorithm", Proceedings of the 2014 USENIX Annual Technical Conference, USENIX Association, 2014, sections 1 and 5.
3. Leslie Lamport, "The Part-Time Parliament", ACM Transactions on Computer Systems, volume 16, issue 2, May 1998, pages 133 to 169.
4. Brian M. Oki and Barbara Liskov, "Viewstamped Replication, A New Primary Copy Method to Support Highly-Available Distributed Systems", Proceedings of the 7th ACM Symposium on Principles of Distributed Computing (PODC '88), Association for Computing Machinery, 1988, pages 8 to 17.
5. Frank Buschmann, Kevlin Henney, and Douglas C. Schmidt, "Pattern-Oriented Software Architecture, Volume 2, Patterns for Concurrent and Networked Objects", John Wiley and Sons, 2000, the Leader/Followers pattern chapter.
6. Douglas C. Schmidt, Carlos O'Ryan, Michael Kircher, Irfan Pyarali, and Frank Buschmann, "Leader/Followers", pattern paper, University of California at Irvine, Siemens AG, and Washington University in Saint Louis, 1998 to 2000, https://www.dre.vanderbilt.edu/~schmidt/PDF/lf.pdf, verified 2026-08-02, the Solution, Structure, Known Uses, and Consequences sections.
7. Apache ZooKeeper project wiki, "Zab1.0", https://cwiki.apache.org/confluence/display/zookeeper/zab1.0, verified 2026-08-02.
8. Apache ZooKeeper project wiki, "Zab", https://cwiki.apache.org/confluence/display/ZOOKEEPER/Zab, verified 2026-08-02.
9. Confluent documentation, "Kafka Replication", https://docs.confluent.io/kafka/design/replication.html, verified 2026-08-02.
10. Apache Kafka project wiki, "Kafka Replication", https://cwiki.apache.org/confluence/display/KAFKA/Kafka+Replication, verified 2026-08-02.
11. etcd documentation, "Frequently Asked Questions (FAQ)", https://etcd.io/docs/v3.2/faq/, verified 2026-08-02.
12. etcd Go package documentation, "raft package, go.etcd.io/etcd/raft/v3", https://pkg.go.dev/go.etcd.io/etcd/raft/v3, verified 2026-08-02.
13. Kubernetes documentation, "Leases", https://kubernetes.io/docs/concepts/architecture/leases/, verified 2026-08-02.

## Code examples

Three languages are used because the pattern's three dominant implementation
variants from dimension 8, term-based voting, lease-based leadership, and
quorum-acknowledged log replication with epoch fencing, are each clearest in
a different idiom. Every example simulates the decision logic in an isolated,
in-memory way, deliberately without real networking, because the pattern
itself is a network protocol and a faithful networked implementation is out
of scope for a minimal, runnable, three-language illustration, the same
reasoning dimension 15 gives for why unit tests of leader-side decision logic
use in-memory stand-ins rather than a live cluster.

### Go, term-based election (Raft-style)

Models dimension 7's failover sequence, a fixed cluster votes for
whichever candidate has the shortest election timeout, then re-elects with an
incremented term after the leader is removed from the cluster.

```go
package main

import "fmt"

type Node struct {
	ID       int
	Term     int
	VotedFor int
	Alive    bool
	Timeout  int
}

func requestVote(candidates []*Node, candidateID, term int) int {
	granted := 1
	for _, v := range candidates {
		if v.ID == candidateID {
			continue
		}
		if term > v.Term {
			v.Term = term
			v.VotedFor = candidateID
			granted++
		}
	}
	return granted
}

func elect(nodes []*Node, term int) *Node {
	var alive []*Node
	for _, n := range nodes {
		if n.Alive {
			alive = append(alive, n)
		}
	}
	best := alive[0]
	for _, c := range alive {
		if c.Timeout < best.Timeout {
			best = c
		}
	}
	quorum := len(nodes)/2 + 1
	votes := requestVote(alive, best.ID, term)
	if votes >= quorum {
		best.Term = term
		return best
	}
	return nil
}

func main() {
	nodes := []*Node{
		{ID: 1, Timeout: 150, Alive: true},
		{ID: 2, Timeout: 180, Alive: true},
		{ID: 3, Timeout: 120, Alive: true},
		{ID: 4, Timeout: 200, Alive: true},
		{ID: 5, Timeout: 170, Alive: true},
	}
	quorum := len(nodes)/2 + 1
	fmt.Printf("cluster size %d, quorum %d\n", len(nodes), quorum)

	leader := elect(nodes, 1)
	fmt.Printf("term 1: node %d elected leader (shortest election timeout)\n", leader.ID)
	fmt.Println("leader sends AppendEntries heartbeats, followers reset their timeouts")

	leader.Alive = false
	fmt.Printf("leader %d crashes, no heartbeat arrives before follower timeouts expire\n", leader.ID)

	newLeader := elect(nodes, 2)
	fmt.Printf("term 2: node %d elected leader (next shortest timeout among survivors)\n", newLeader.ID)
}
```

### TypeScript, lease-based leadership with a fencing token

Models dimension 8's lease-based variant, the Kubernetes and etcd style
election where whoever writes the record first holds it until it expires,
with the fencing token dimension 11's second row relies on to reject a stale
leader's late write.

```typescript
class LeaseStore {
  private holder: string | null = null;
  private fencingToken = 0;
  private expiresAtTick = -1;

  tryAcquire(candidateId: string, now: number, ttlTicks: number): number | null {
    const isFree = this.holder === null || now >= this.expiresAtTick;
    if (isFree) {
      this.holder = candidateId;
      this.fencingToken += 1;
      this.expiresAtTick = now + ttlTicks;
      return this.fencingToken;
    }
    if (this.holder === candidateId) {
      this.expiresAtTick = now + ttlTicks;
      return this.fencingToken;
    }
    return null;
  }

  currentFencingToken(): number {
    return this.fencingToken;
  }
}

function simulate(): void {
  const store = new LeaseStore();
  const ttl = 5;

  let token = store.tryAcquire("controller-a", 0, ttl);
  console.log(`tick 0, controller-a acquires the lease, fencing token ${token}`);

  token = store.tryAcquire("controller-b", 1, ttl);
  console.log(`tick 1, controller-b attempts, result ${token === null ? "rejected, lease still held" : token}`);

  token = store.tryAcquire("controller-a", 3, ttl);
  console.log(`tick 3, controller-a renews before expiry, fencing token ${token}`);

  token = store.tryAcquire("controller-b", 12, ttl);
  console.log(`tick 12, controller-a missed its renewal window, controller-b acquires, fencing token ${token}`);

  console.log(`a write arriving late from controller-a carrying fencing token 1 is rejected because the store now requires token ${store.currentFencingToken()}`);
}

simulate();
```

### Python, quorum-acknowledged replication with epoch fencing

Models dimension 7's steady-state commit path and dimension 11's stale-epoch
rejection, showing a majority-quorum write succeed, then showing a leader
still believing it holds an old epoch fail to reach quorum once most
followers have already moved on.

```python
from dataclasses import dataclass, field


@dataclass
class Follower:
    node_id: int
    epoch: int = 0
    log: list = field(default_factory=list)

    def append(self, epoch: int, entry: str) -> bool:
        if epoch < self.epoch:
            return False
        self.epoch = epoch
        self.log.append(entry)
        return True


class Leader:
    def __init__(self, node_id: int, epoch: int, followers: list):
        self.node_id = node_id
        self.epoch = epoch
        self.followers = followers
        self.log = []

    def replicate(self, entry: str) -> bool:
        self.log.append(entry)
        acks = 1
        for follower in self.followers:
            if follower.append(self.epoch, entry):
                acks += 1
        quorum = (len(self.followers) + 1) // 2 + 1
        return acks >= quorum


def main() -> None:
    followers = [Follower(2), Follower(3), Follower(4), Follower(5)]
    leader = Leader(1, epoch=1, followers=followers)

    committed = leader.replicate("SET x=1")
    quorum = (len(followers) + 1) // 2 + 1
    print(f"epoch {leader.epoch}, entry committed = {committed}, quorum required = {quorum}")

    for follower in followers[:3]:
        follower.epoch = 2

    partitioned_leader = Leader(1, epoch=1, followers=followers)
    rejected_write = partitioned_leader.replicate("SET x=2 from a partitioned leader")
    print("a leader still believing it holds epoch 1 tries to replicate after 3 of 4 followers moved to epoch 2")
    print(f"quorum reached = {rejected_write}, so its write correctly fails and it must step down and rejoin at a higher epoch")


if __name__ == "__main__":
    main()
```

Java, Rust, and Swift are omitted deliberately rather than by oversight. This
pattern's idiomatic shape, per dimension 8, is to adopt an existing library
or coordination service rather than author fresh election logic per project
in every language a team happens to use, so a third simulation of the same
underlying quorum arithmetic in a fourth or fifth language would repeat the
Go and Python examples' logic without illustrating a variant this entry has
not already covered in dimension 8.
