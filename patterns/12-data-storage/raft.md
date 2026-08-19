---
name: Raft
slug: raft
family: 12-data-storage
category: Distributed Consensus
aliases: [Raft Consensus Algorithm, Understandable Consensus]
first_described: "Ongaro, Ousterhout 2014"
maturity: canonical
related: [leader-election, write-ahead-log, state-machine-replication, quorum-consensus, log-compaction, snapshotting]
incompatible_with: []
verified: 2026-08-02
---

# Raft

## 1. Name, aliases, and lineage

The canonical name is Raft, not an acronym in the usual sense but a play on
words chosen by the authors because a raft is what you build a log on. The
algorithm was introduced by Diego Ongaro and John Ousterhout of Stanford
University in the paper "In Search of an Understandable Consensus Algorithm
(Extended Version)", presented at the USENIX Annual Technical Conference in
2014 (https://raft.github.io/raft.pdf, verified 2026-08-02). The extended
version is the one practitioners cite because it contains the full proof
sketch and the membership change protocol that the conference paper trimmed
for space.

Ongaro's Stanford PhD dissertation, "Consensus, Bridging Theory and Practice"
(Stanford University, 2014), is the second primary source and is the one that
implementers reach for when the paper is ambiguous, because it contains the
complete formal TLA+ specification of the algorithm and a longer discussion of
the cluster membership change protocol, including the single-server change
approach that later implementations preferred over joint consensus
(https://github.com/ongardie/dissertation, verified 2026-08-02, PDF hosted at
that repository as stanford.pdf).

Raft is explicitly a response to Paxos, and the paper's stated goal is
understandability, not novel theoretical power. Ongaro and Ousterhout write
that Paxos, first described in Leslie Lamport's 1998 paper "The Part-Time
Parliament" (ACM Transactions on Computer Systems 16, 2, May 1998), is
notoriously hard to reason about and to implement correctly, and that the
industry response had been a proliferation of incompatible, informally
specified Paxos variants built to patch that gap. Raft decomposes the
consensus problem into three largely independent subproblems, leader
election, log replication, and safety, and adds a strong invariant, a leader
never overwrites or deletes entries in its own log, which the paper calls the
Leader Append-Only property. This single choice is what most separates Raft's
structure from Multi-Paxos, where any server can propose a value for any log
slot and reconciling divergent proposals is the hard part.

There is no meaningfully contested alternate name. Some early blog posts
called it "Raft consensus", used here as a descriptive phrase rather than a
distinct alias, because the paper itself only ever calls it Raft.

## 2. Problem and context

A distributed system that holds state a client cares about, a key-value
store, a lock service, a piece of cluster metadata, a leader pointer for
another system, needs that state to survive the failure of any single
machine, and it needs every client to see one consistent history of that
state even while machines are crashing, restarting, and losing network
connectivity to each other at unpredictable moments.

The concrete situation looks like this. You are building a small piece of
infrastructure, a configuration store, a lock manager, a job queue's
leader-election component, a metadata service in front of a sharded database.
You need three or five machines to agree on a sequence of state-changing
operations, in the same order, even when up to some number of them can crash,
restart with stale data, or be partitioned away from the rest by a flaky
network. A single machine holding the state is not fault tolerant. Simply
replicating writes to several machines and hoping they apply them in the same
order is not correct, because two machines can receive conflicting writes
concurrently, or a machine can miss a write while it was down and never
notice.

Raft's context is specifically the crash-recovery fault model, not Byzantine
faults. Every server is assumed to execute the algorithm faithfully. It may
crash, it may lose messages, it may run arbitrarily slowly, but it never lies,
never sends a malformed message on purpose, and never colludes with another
faulty server to violate the protocol. This assumption is what makes Raft,
like Paxos, unsuitable for adversarial environments such as public
blockchains, where Byzantine fault tolerant protocols such as PBFT or Tendermint
are the correct tool instead.

Raft further assumes a partially synchronous network. Messages can be
delayed, dropped, duplicated, and reordered arbitrarily, but the system is
only required to make progress during periods when message delivery delays
are bounded relative to the algorithm's timeout parameters. This is why every
production Raft deployment tunes election timeouts against the actual
round-trip time of its network, a theme that recurs throughout dimensions 11
and 16 below.

## 3. Forces

Judgement. The following weighs which pressure Raft favours and which it pays
for, based on the paper's own stated design goals and on operational
experience documented by implementers cited in dimension 9.

- **Understandability, favoured explicitly.** The paper's central and
  unusual claim is that understandability was treated as a first-class design
  goal alongside correctness, efficiency, and completeness, and that Raft
  trades away some of the freedom Paxos has, any server may propose a value
  for any log index, in exchange for a strong structural invariant, leader
  append-only logs, that makes the system's behaviour much easier for an
  implementer to reason about and to test. The authors ran a user study at
  two universities showing Raft was learned more accurately than Paxos by
  students given the same amount of time, cited as evidence, not proof.
- **Availability during leader failure, sacrificed briefly by design.**
  Raft has exactly one active writer, the leader, at any given term. When the
  leader crashes, the cluster cannot commit new entries until a new leader is
  elected, a gap the paper analyses as bounded by the election timeout, a few
  hundred milliseconds in the reference implementation's chosen parameters.
  Multi-Paxos with a stable leader has the same practical gap. A leaderless
  protocol like Egalitarian Paxos (EPaxos) avoids this pause but pays for it
  with far more complex conflict detection between concurrent proposals.
- **Throughput, sacrificed relative to leaderless designs.** All writes
  funnel through one leader's single log, so write throughput is bounded by
  that one machine's disk and network capacity, not by the cluster's
  aggregate capacity. This is why systems needing more write throughput than
  one Raft group can provide, TiKV and CockroachDB among them, run many
  independent Raft groups in parallel, see dimension 9.
- **Consistency, strongly favoured.** Raft provides linearizable
  reads and writes at the log level when correctly implemented, meaning every
  operation appears to take effect atomically at some point between its
  invocation and its response. This is the strongest consistency model
  commonly offered in a replicated log, stronger than the eventual
  consistency Dynamo-style systems offer, and it is not free, see the latency
  cost below.
- **Latency, sacrificed for correctness.** A write is not acknowledged to
  the client until a majority of the cluster has durably persisted it, which
  means every write pays at least one network round trip to the slowest
  server in the majority, plus a disk fsync on that majority. A single-node
  store or an asynchronously-replicated store can acknowledge faster but with
  weaker durability or consistency guarantees.
- **Cognitive load on the implementer, sacrificed compared to a
  single-node database, favoured compared to Paxos.** Raft is still a
  genuinely hard piece of software to build correctly. The paper's own
  formal TLA+ specification exists precisely because informal reasoning
  about distributed systems is unreliable, and production implementations
  have shipped subtle bugs, documented in dimension 11, even when the authors
  believed they had implemented the paper faithfully.
- **Operability, favoured relative to Paxos variants.** Because every
  server's log state can only diverge from the leader's in specific,
  provable ways (dimension 5's Log Matching Property), an operator debugging
  a stuck or diverging cluster has a much smaller space of possible causes
  to search than with a Paxos implementation where any server could have
  proposed any value for any slot.

## 4. Applicability and non-applicability

Reach for Raft when the following hold.

- You need a small number of machines, typically three or five, to agree on
  an ordered sequence of operations and to survive the crash of a minority of
  them without losing data or diverging.
- The workload's write throughput fits comfortably on one leader's disk and
  network, or you are willing to shard the state across many independent
  Raft groups, as every large-scale production user in dimension 9 does.
- You need strict linearizable consistency for the replicated state, not
  eventual consistency, and a brief unavailability window during a leader
  failure is acceptable.
- You are building a new piece of infrastructure, not integrating with an
  existing Paxos-based system, and you can choose your own replication
  protocol from scratch.
- You need the replicated data set to be small enough that periodic full-state
  snapshots, Raft's log compaction mechanism, are practical to produce and to
  transfer to a lagging follower.

Do NOT reach for Raft in these cases, and the reason matters more than the
rule.

- **The environment is adversarial or you cannot trust every participant
  to execute the protocol faithfully.** Raft assumes crash-stop or
  crash-recovery failures only. A malicious or compromised node running
  Raft's own code can violate every safety guarantee the algorithm claims,
  because nothing in the protocol authenticates that a server's stated log
  index or term is truthful beyond the RPC layer's own transport security.
  Use a Byzantine fault tolerant protocol such as PBFT, HotStuff, or
  Tendermint instead.
- **You need to scale write throughput across many machines and cannot
  shard the state.** A single Raft group has one leader and therefore one
  effective write bottleneck. If your data cannot be partitioned into
  independent groups, Raft alone will not give you horizontal write
  scalability, and you either need a sharding layer on top, as CockroachDB
  and TiKV both build, or a fundamentally different, leaderless protocol.
- **You only need eventual consistency and can tolerate reading stale or
  conflicting data.** A CRDT-based system or a Dynamo-style quorum store with
  last-writer-wins or vector clocks will give you far higher availability and
  throughput at the cost of consistency Raft is specifically built to avoid
  giving up. Forcing Raft onto a workload that would be happy with eventual
  consistency pays a latency and availability tax for no benefit.
- **The replicated state is very large and changes slowly, and you cannot
  afford full-state snapshotting.** Raft's log compaction mechanism
  (dimension 8) typically works by serialising the entire state machine into
  a snapshot. For a multi-terabyte state machine this can be an expensive,
  disruptive operation unless the implementation supports incremental or
  chunked snapshotting, which not every Raft library does.
- **You already operate a mature Paxos-based system and the migration cost
  outweighs the readability benefit.** Google's Chubby, Spanner, and
  Megastore are all Paxos-derived and stable in production for well over a
  decade, so rewriting a working Paxos deployment onto Raft purely because
  Raft is easier to reason about is rarely worth the risk, absent another
  driving need.
- **You need geographically distributed, wide-area consensus across
  continents with very high round-trip latency, and per-write latency is
  the dominant cost you are optimising.** Raft's majority-quorum,
  single-leader design means every write pays the round-trip time to the
  farthest-away member of the majority. Protocols and system designs built
  specifically for wide-area placement, such as Google Spanner's TrueTime-
  based commit-wait combined with Paxos, or flexible-quorum variants of Raft
  that let you weight quorums geographically, address this more directly than
  vanilla Raft's uniform majority quorum does.
- **You need only leader election or lock coordination and not a general
  replicated log.** A single-purpose leader election primitive built directly
  on a simpler mechanism, for example a lease held in an existing Raft-backed
  store such as etcd, is usually a better fit than implementing Raft
  yourself for that narrower purpose. This is in fact the common pattern,
  see dimension 9.

## 5. Structure

Raft names five participants and the roles they play.

- **Server.** Every participant in the cluster runs the same state machine
  with three mutually exclusive roles, follower, candidate, and leader, and
  transitions between them are driven entirely by timeouts and by receiving
  RPCs carrying a higher term number than the server's own.
- **Term.** A monotonically increasing logical clock, incremented every time
  an election starts. Exactly zero or one leader can exist for any given
  term, which the paper proves via the Election Safety property. A term acts
  as a version number for the entire cluster's leadership state, and every
  RPC carries the sender's current term so a server can detect it is talking
  to a stale leader or a stale candidate and reject the message.
- **Log.** An ordered, append-only sequence of entries kept independently by
  every server. Each entry holds the command to apply to the state machine,
  the term in which the leader that created it was in power, and its index
  position in the log. The Log Matching Property, proved in the paper, states
  that if two logs contain an entry with the same index and term, the logs
  are identical in every entry up to and including that index, and this
  single property is what lets Raft reason about log consistency using only
  a constant-size piece of information per AppendEntries RPC rather than
  comparing whole logs.
- **Leader.** The one server per term that accepts client commands, appends
  them to its own log, and replicates them to followers via AppendEntries
  RPCs. The leader also periodically sends empty AppendEntries RPCs as
  heartbeats to prevent followers from timing out and starting an election.
- **Candidate.** The transient role a follower enters when its election
  timeout elapses without hearing from a leader. It increments the term,
  votes for itself, and sends RequestVote RPCs to every other server, racing
  to collect votes from a majority before another candidate does or before
  its own election timeout elapses again.
- **RequestVote RPC.** Sent by a candidate. Carries the candidate's term, its
  server id, and the index and term of the last entry in its own log. A
  server grants its vote only if the requesting term is at least as high as
  its own, it has not already voted for a different candidate in that term,
  and the candidate's log is at least as up to date as the voter's own log,
  the mechanism the paper calls the Leader Completeness invariant's
  enforcement point.
- **AppendEntries RPC.** Sent by the leader, both to replicate new entries
  and as an empty heartbeat. Carries the leader's term, the index and term of
  the log entry immediately preceding the new entries (used for the
  consistency check below), the new entries themselves, and the leader's
  current commitIndex, so followers can advance their own commit position.
- **commitIndex.** The index of the highest log entry known to be committed,
  meaning replicated to a majority of the cluster. Once an entry is
  committed the leader is guaranteed by the Leader Completeness property
  never to lose it, even across subsequent leader elections, and it becomes
  safe to apply to the state machine.

## 6. ASCII structure diagram

```
                        election timeout elapses,
                        starts election (term += 1)
     +------------------------------------------------+
     |                                                 v
+----------+   receives majority       +-----------+   AppendEntries RPC
| Follower |<---------------------  wins vote    | Candidate |---------->
+----------+   of votes                 +-----------+  RequestVote RPC
     ^                                        |
     |  discovers current leader              |  discovers server
     |  or new term (via RPC)                 |  with higher term
     +-----------------------------------------+
                        |
                        v higher term seen
              +--------------------+
              |       Leader       |
              +--------------------+
                        |
                 steps down (higher term
                 discovered via RPC reply)
                        |
                        v
                    Follower

  One cluster, one term, at most one Leader (Election Safety property).

  +--------------------------- Cluster of 5 servers ------------------------+
  |                                                                          |
  |   +--------+     AppendEntries      +----------+     AppendEntries      |
  |   | Leader |------------------------>| Follower |----(no forwarding,    |
  |   | term 4 |------------------------>| Follower |     leader talks to   |
  |   +--------+------------------------>| Follower |     every follower    |
  |       |    ------------------------->| Follower |     directly)         |
  |       |                              +----------+                      |
  |    Client                                                               |
  |    command                                                              |
  +--------------------------------------------------------------------------+
```

## 7. Dynamics

Two runtime flows matter most, log replication under a stable leader, and
leader election after a failure.

```
Client        Leader (term 4)     Follower A        Follower B        Follower C
  |                 |                  |                  |                  |
  |-- SET x=1 ----->|                  |                  |                  |
  |                 |-- append to      |                  |                  |
  |                 |   own log[idx=9] |                  |                  |
  |                 |                  |                  |                  |
  |                 |-- AppendEntries -+                  |                  |
  |                 |   (term=4, prevLogIndex=8,           |                  |
  |                 |    prevLogTerm=4, entries=[x=1],     |                  |
  |                 |    leaderCommit=8) ---------------->|                  |
  |                 |------------------------------------+---------------->  |
  |                 |                  |                  |                  |
  |                 |<-- success=true -|                  |                  |
  |                 |<-------------------------------------- success=true -- |
  |                 |                  |                  |                  |
  |                 |-- majority (leader + 2 of 4          |                  |
  |                 |   followers) has entry -->           |                  |
  |                 |   advance commitIndex to 9           |                  |
  |                 |   apply x=1 to own state machine      |                  |
  |<-- ack ---------|                  |                  |                  |
  |                 |-- next heartbeat carries leaderCommit=9,                |
  |                 |   followers advance their commitIndex and apply too    |
```

```
Leader crashes (term 4).  Followers stop receiving heartbeats.

Follower A         Follower B          Follower C
    |                   |                   |
    | election timeout elapses first
    |-- becomes Candidate, term := 5
    |-- votes for self
    |-- RequestVote(term=5, lastLogIndex=9, lastLogTerm=4) --------->
    |------------------------------------------------------------->
    |                   |                   |
    |<-- voteGranted=true (log is at least as up to date) ---------|
    |<---------------------------------------------------------------|
    |
    | received votes from self + B + C = majority of 3 (of a 3-node
    | remainder cluster, or majority of 5 counting itself + 2 others)
    |
    |== becomes Leader, term 5 ==
    |-- sends AppendEntries heartbeats (term=5) to B and C -------->
    |------------------------------------------------------------->
    |  B and C recognize term 5 > their term, remain/become followers
```

The critical safety subtlety in the second diagram is the vote-granting
check on log recency. A voter grants its vote only if the candidate's
lastLogTerm is strictly greater than the voter's own, or equal and the
candidate's lastLogIndex is greater than or equal to the voter's own. This
single check is what the paper's Leader Completeness proof rests on. A
candidate cannot win an election unless its log contains every entry
committed in any earlier term, because committing an entry required a
majority to have it, and winning an election requires a majority of votes,
and any two majorities overlap in at least one server.

## 8. Implementation variants

**Reference-shape implementation, in-memory plus a write-ahead log.** The
canonical shape follows the paper closely. State (currentTerm, votedFor,
log entries) is persisted to stable storage before responding to any RPC,
because losing that state on a crash and restart can violate safety, most
seriously via the RequestVote vote-granting rule if votedFor is forgotten and
a duplicate vote is later granted to a different candidate in the same term.

**Pre-vote extension.** A widely adopted addition, not in the original
paper, where a server about to start an election first runs a non-binding
PreVote round to check whether it could plausibly win before actually
incrementing its term and disrupting the current leader. This is the fix
for the disruptive-server problem the paper itself names as an open issue in
section 9.6, a partitioned server whose election timeout repeatedly fires
increments its term over and over while partitioned, and when it rejoins the
cluster its inflated term forces the legitimate leader to step down even
though the partitioned server cannot win the resulting election. etcd's
raft library implements PreVote as an opt-in flag for exactly this reason
(https://pkg.go.dev/go.etcd.io/etcd/raft/v3, verified 2026-08-02, package
documents the CheckQuorum and PreVote fields on the Config struct).

**Leader lease and read-index optimisation.** The base protocol requires a
read to either go through the log, a no-op AppendEntries round trip, or rely
on a time-bounded lease from the leader's last confirmed heartbeat majority,
to guarantee linearizability without serving stale data from a partitioned
former leader that has not yet realized a new leader exists. The paper
discusses this in section 8, and most production implementations, including
etcd's, implement a variant called ReadIndex rather than a strict clock-based
lease, to avoid relying on synchronized clocks across servers.

**Joint consensus versus single-server membership changes.** The original
paper (section 6) specifies a two-phase joint consensus protocol for changing
cluster membership safely, where the cluster transitions through a
configuration that requires majorities from both the old and new member
sets simultaneously. Ongaro's dissertation instead recommends, and most
production libraries implement, a simpler single-server-change protocol,
adding or removing exactly one server at a time, which the dissertation
proves preserves safety without needing the joint configuration's two-phase
complexity, because a majority of the old configuration and a majority of a
configuration differing by one server always overlap.

**Multi-Raft and sharded Raft groups.** For workloads whose write throughput
exceeds what one Raft group's leader can sustain, or whose data set is too
large for one group's log, production systems run many independent Raft
groups, one per data shard or key range, on the same physical cluster. This
is not part of the original paper at all, it is a systems-engineering layer
built on top of Raft by its adopters, and it introduces its own
coordination problems, batching heartbeats across co-located groups, and
range-splitting a group when it grows too large. TiKV and CockroachDB both
document this design, see dimension 9.

**Language-idiomatic note.** Raft's structure, an explicit state machine
with three roles and RPC-driven transitions, translates naturally into any
language with sum types or explicit enums (Rust's enum, Go's iota-based
constants, TypeScript's discriminated unions) representing the Follower,
Candidate, Leader states, and the persistence requirement, term, votedFor,
and log must survive a crash before an RPC reply is sent, is the one detail
that differs least across languages, because it is a correctness requirement
of the algorithm, not an implementation convenience.

## 9. Known production uses

**etcd, the coordination store behind Kubernetes.** etcd implements Raft as
its replication layer and is itself the datastore Kubernetes uses to hold
all cluster state and to perform leader election for controllers. etcd's own
documentation on its learner feature states it builds on Raft section 4.2.1
for non-voting cluster members, and describes Raft's role in etcd as
providing leadership election to protect availability during topology
changes and log replication so all members receive consistent updates
(https://etcd.io/docs/v3.5/learning/design-learner/, verified 2026-08-02).

**HashiCorp Consul, Nomad, and Vault, via the hashicorp/raft Go library.**
HashiCorp maintains an open-source Raft implementation, described in its own
repository as a Go library that manages a replicated log and can be used
with a finite state machine to manage replicated state, for building
consistent, partition-tolerant systems
(https://github.com/hashicorp/raft, verified 2026-08-02). Consul used this
library for its own leader election and service catalog replication, as
documented in the same repository's history describing Consul's use of it
prior to version 0.7.0. HashiCorp's Nomad job scheduler and Vault secrets
manager both build their own high-availability and cluster-consistency
layers on the same underlying library.

**TiKV, the distributed key-value store underneath TiDB.** TiKV documentation
states plainly that TiKV uses Raft to perform data replication, and that each
data change is recorded as a Raft log, describing a Multi-Raft architecture
in which data is split into Regions, each Region's replicas across different
nodes forming an independent Raft Group kept consistent through the Raft
algorithm, with one replica per group serving as leader for reads and writes
(https://docs.pingcap.com/tidb/stable/tidb-storage, verified 2026-08-02).

**CockroachDB.** CockroachDB's architecture documentation states directly
that it uses the Raft consensus algorithm for replication, describing Raft
as the protocol that makes sure data is safely stored on multiple machines
and that those machines agree on the current state even if some of them are
temporarily disconnected, and organizes replicas into per-range Raft groups
each with its own leader and followers
(https://docs.cockroachlabs.com/docs/stable/architecture/replication-layer,
verified 2026-08-02). This is the same Multi-Raft, per-shard-group pattern
TiKV uses, independently arrived at by both systems' engineering teams.

## 10. Consequences

Positive.

- Every server in the cluster can independently verify, using only a
  constant-size piece of information per RPC, a term and an index, whether
  its log is consistent with the leader's, thanks to the Log Matching
  Property, avoiding the need to compare entire logs.
- The single-leader design collapses the write path into one linear
  sequence, which makes reasoning about ordering, and building the state
  machine that consumes the log, dramatically simpler than a design where any
  server can propose a value for any slot.
- The algorithm comes with a formal correctness proof and a full TLA+
  specification in Ongaro's dissertation, which several independent
  implementations, including etcd's and hashicorp/raft, have been checked
  against or model-tested with tools like TLC and Jepsen.
- Cluster membership can change while the cluster remains available,
  without a full stop-the-world reconfiguration, using either the
  paper's joint consensus or the dissertation's single-server-change
  protocol.
- Log compaction via snapshotting bounds the amount of log history a server
  must retain and replay, keeping restart and lagging-follower catch-up time
  proportional to the current state size rather than to the cluster's
  entire operational history.

Negative.

- Write throughput and write latency are both bounded by the single
  leader's capacity and by the round-trip time to a majority, a hard ceiling
  that forces large systems into the Multi-Raft sharding pattern documented
  in dimension 9, which introduces its own operational complexity.
- The cluster is briefly unavailable for new writes during a leader
  failure, bounded by the election timeout, typically a few hundred
  milliseconds to a few seconds depending on tuning, which is unacceptable
  for some latency-sensitive workloads without additional engineering, for
  example pre-vote and priority-based election ordering.
- Every write pays a durable-write cost on a majority of servers before it
  is acknowledged, which is strictly more expensive in latency and disk I/O
  than a single-node write or an asynchronously replicated write.
- Despite the paper's understandability goal, correctly implementing every
  edge case, particularly around persistence ordering, snapshot installation
  during an in-flight election, and membership change interaction with log
  compaction, has proven difficult in practice, and production
  implementations have shipped real safety bugs, see dimension 11.
- The protocol assumes a crash-recovery fault model and offers no protection
  at all against a malicious or compromised participant, so it cannot be
  used unmodified in any setting where that assumption does not hold.

## 11. Failure modes and misuse

**The disruptive partitioned server.** Symptom. A healthy, stable leader is
repeatedly deposed shortly after a previously partitioned node rejoins the
cluster, even though the rejoining node has no chance of winning the
resulting election, and cluster availability drops for a term or two with no
obvious external cause. Cause. The partitioned server's election timeout
kept firing while it was isolated, so its term counter climbed far above the
rest of the cluster's, and its first RequestVote RPC after rejoining
contains a higher term than the leader's, which forces the leader to step
down per the term-comparison rule, even though the disruptive candidate
cannot win a majority. This is discussed as an explicit open issue in
section 9.6 of the paper itself. Fix. Implement the PreVote extension
(dimension 8), so a server only actually increments its term and disrupts
the cluster after confirming in a non-binding round that it could plausibly
win.

**Missed persistence before RPC reply.** Symptom. After a crash and restart,
a server that had previously voted in an election votes again for a
different candidate in the same term, or a follower that acknowledged an
AppendEntries loses that entry on restart, and the cluster ends up with two
leaders believing they are both in charge, or an acknowledged write silently
disappears. Cause. The implementation replied to a RequestVote or
AppendEntries RPC before durably persisting the corresponding state,
votedFor, or the new log entries, to stable storage, so a crash between the
reply and the fsync loses the guarantee the RPC's success implied. Fix.
Persist to stable storage synchronously before sending any RPC reply that
depends on that state, exactly as the paper's Figure 2 RPC descriptions
specify. This is the single most common source of real Raft safety bugs
reported by implementers.

**Snapshot installation racing an election or a new leader.** Symptom. A
lagging follower that is mid-way through receiving an InstallSnapshot RPC
from the old leader ends up in a corrupt or inconsistent state when a new
leader is elected during the transfer, or the follower applies a snapshot
out of order relative to log entries it already has. Cause. Snapshot
installation and log replication are not naturally atomic with respect to a
concurrent term change, and an implementation that does not carefully check
the snapshot's lastIncludedIndex and lastIncludedTerm against the follower's
existing log before discarding entries can corrupt local state. Fix. Follow
the paper's InstallSnapshot RPC handling precisely, only discard log entries
covered by the snapshot, retain any entries the follower already has beyond
the snapshot's lastIncludedIndex, and reject the RPC's stale-term case the
same way AppendEntries does.

**Read staleness from a partitioned former leader.** Symptom. A client
reads a value from what it believes is the current leader, but the value is
stale, because that server was in fact partitioned away and a new leader has
already committed newer writes elsewhere in the cluster. Cause. Serving
reads directly from a leader's local state without either a lease check or
a ReadIndex round trip does not, by itself, guarantee linearizability,
because the server serving the read may no longer actually be the leader
by the time the read is served, even if it believes it still is. Fix.
Implement the ReadIndex protocol, confirm current leadership via a
heartbeat round to a majority before serving the read, or a strict,
clock-bounded leader lease, exactly as discussed in paper section 8.

**Misconfigured election timeout relative to network latency.** Symptom.
The cluster thrashes leadership constantly, electing a new leader every few
seconds under normal operating conditions, with no actual server failures or
partitions occurring. Cause. The election timeout is set too close to the
network's actual round-trip time and heartbeat interval, so ordinary
network jitter, not an actual leader failure, triggers repeated elections.
Fix. The paper's own guidance, restated by every production implementation's
documentation, is that the election timeout should be an order of magnitude
larger than the broadcast time, the time to send an RPC and receive a
response from every server, and that heartbeats should be sent well within
that timeout, often at roughly one tenth of the election timeout's lower
bound.

## 12. Trade-off matrix

Judgement, comparing Raft against its most commonly considered named
alternatives across the forces from dimension 3.

| Force | Raft | Multi-Paxos | ZAB (ZooKeeper Atomic Broadcast) | EPaxos (Egalitarian Paxos) |
|---|---|---|---|---|
| Understandability | Favoured, explicit design goal | Sacrificed, notoriously subtle | Moderate, closely tied to ZooKeeper's specific implementation | Sacrificed, conflict-graph reasoning is complex |
| Leaderless writes | No, single leader per term | No in the practical Multi-Paxos form | No, single leader | Yes, any replica can propose |
| Availability during leader failure | Brief pause during election | Brief pause during election | Brief pause during election | No pause for non-conflicting commands |
| Write throughput ceiling | One leader's capacity, or sharded via Multi-Raft | One leader's capacity | One leader's capacity | Higher, spreads load across replicas |
| Membership change safety | Explicit joint or single-server protocol | Not part of the original algorithm, added ad hoc by implementers | Handled by ZooKeeper's own dynamic reconfiguration extension | Less standardized across implementations |
| Formal specification available | Yes, TLA+ in Ongaro's dissertation | Informal in Lamport's original papers, formalized separately by others | Partially, described in a 2011 paper by Junqueira, Reed, Serafini | Yes, in the original SOSP 2013 paper |
| Maturity of production deployments | Very high (etcd, Consul, TiKV, CockroachDB) | Very high (Google Chubby, Spanner, Megastore) | Very high (ZooKeeper itself, and systems built on it) | Low relative to the others, mostly research and niche use |

## 13. Related and incompatible patterns

**State machine replication.** Raft is one specific protocol for
implementing the more general state machine replication pattern, where a
deterministic state machine is replicated so that every replica applies
the same sequence of commands in the same order. Raft supplies the ordering
and durability guarantee. The state machine itself, and how it is snapshot
and restored, is a separate concern the application must implement, often
following the same conventions as the write-ahead log pattern used in
single-node database engines.

**Write-ahead log.** Raft's own log is structurally a write-ahead log, and
Raft implementations frequently reuse single-node WAL techniques, batching
fsyncs, sequential append-only files, checksummed records, for the log's
on-disk representation. The two patterns compose directly. Raft answers in
what order and with what durability guarantee these entries become
committed across a cluster, and WAL techniques answer how a specific
server's copy of the log is persisted efficiently.

**Leader election.** Raft's leader election subprotocol is sometimes reused
in isolation, separate from log replication, as a general-purpose
distributed leader election primitive, though in practice most systems that
need only leader election build it on top of an existing Raft-backed store
such as etcd or ZooKeeper rather than implementing the RequestVote protocol
themselves, because the surrounding correctness machinery, persistence,
term handling, is most of the actual implementation effort.

**Quorum consensus, quorum reads and writes.** Raft's majority-quorum
requirement for both elections and commits is an instance of the general
quorum consensus pattern, any two quorums overlap, the same underlying idea
Dynamo-style systems use for their read and write quorums, though Dynamo
systems typically use quorums for availability and tunable consistency
rather than for total ordering, and do not have a leader.

**Log compaction and snapshotting.** Raft's own dimension 8 log compaction is
an application of the general snapshotting pattern used broadly in database
and messaging systems to bound replay time after a restart, and it composes
directly with Raft's InstallSnapshot RPC for bringing a far-behind follower
up to date without replaying its entire missed history.

**Incompatible with Byzantine fault tolerant protocols.** Raft cannot be
composed with or substituted into a system that genuinely requires Byzantine
fault tolerance, because Raft's safety proofs assume every server executes
the algorithm honestly. Attempting to run Raft hardened against malicious
participants without redesigning the protocol, for instance by adding
signatures to RPCs without also changing the quorum and voting logic to
tolerate a fraction of actively lying servers, does not produce a
Byzantine fault tolerant system.

## 14. Refactoring path in and out

**Introducing Raft into an existing single-node service.** Step one, isolate
the service's mutable state behind a narrow command interface, every
state-changing operation becomes a single serializable command object,
before touching replication at all. This is a pure refactor and is valuable
independent of Raft, because it is also the interface the eventual Raft log
will drive. Step two, stand up a Raft library, an existing implementation,
never a hand-rolled one for a first production deployment, see dimension 8's
caution about how subtle correctness bugs are, as a sidecar process or
embedded library, with the state machine's apply function wired to the
command interface from step one, and the existing service's writes routed
through the Raft leader's propose call instead of applied directly. Step
three, migrate reads to either go through the leader with the ReadIndex
protocol, or accept relaxed, possibly-stale reads from any replica if the
application can tolerate it, an explicit choice that must be documented, not
defaulted into silently. Step four, add the second and third replicas and
verify the cluster survives a killed leader in a staging environment before
trusting it in production, exercising the actual failure mode, not just the
happy path.

**Removing Raft when it stops earning its place.** This happens most often
when a system originally built as a small, standalone cluster gets absorbed
into a larger platform that already runs a shared, well-operated Raft-backed
coordination service, etcd being the common case inside a Kubernetes-adjacent
stack. Step one, confirm the shared service's consistency and availability
guarantees actually meet the absorbed system's original requirements, do not
assume they do. Step two, migrate the state machine's apply logic to consume
from the shared service's watch or subscription mechanism instead of from a
local Raft log. Step three, decommission the standalone cluster only after
running both in parallel long enough to confirm the migrated system observes
the same command ordering the old cluster would have produced, since a
silent ordering divergence during migration is the most dangerous possible
failure of this refactor.

## 15. Testing and verification

Testing correct Raft code well is unusually adversarial relative to typical
application testing, because the specification's guarantees are properties
of the whole distributed system under failure, not of any single function's
return value.

- **Deterministic simulation testing.** The most effective technique
  reported by implementers is running the entire cluster inside a single
  process with a simulated, controllable clock and network, so tests can
  deterministically inject message delays, drops, reorderings, partitions,
  and crash-restarts, and then replay a failing seed exactly to debug it.
  This is the approach the MIT 6.824 distributed systems course labs use for
  their Raft assignment, and it is the same technique FoundationDB's
  simulation testing framework is built around for its own consensus layer.
- **Linearizability checking.** After a test run that injects failures,
  a linearizability checker, the Jepsen project's Knossos checker is the
  most widely cited tool for this, replays the recorded client operation
  history against the expected state machine semantics and reports whether
  any observed sequence of reads and writes is inconsistent with some valid
  linear ordering, which is the property Raft claims to guarantee and the
  property most implementation bugs actually violate.
- **Property-based invariant checks, run continuously during simulation.**
  Rather than only checking the final state, a correct test setup asserts
  the paper's own safety properties, Election Safety, at most one leader per
  term, Leader Append-Only, Log Matching, Leader Completeness, and State
  Machine Safety, as invariants checked after every simulated step, so a
  violation is caught at the exact operation that caused it rather than
  discovered later as a symptom.
- **What becomes easier to test because of Raft.** The state machine itself
  becomes trivially testable in isolation, given a fixed sequence of
  commands it must produce a fixed resulting state deterministically, with
  no need to simulate any networking or timing at all, because Raft's job
  is precisely to guarantee that sequence is agreed upon before the state
  machine ever sees it.
- **What becomes harder.** Testing that a specific write took effect from
  a client's perspective now requires reasoning about commit and apply
  timing across a majority, not a single acknowledgement, and naive
  end-to-end tests that check state on only one replica immediately after a
  write can pass by accident even when the replication logic is broken,
  because they happened to read from the leader before a genuine consistency
  bug would have surfaced.

## 16. Observability signals

A healthy Raft cluster in steady state shows a stable, unchanging leader
over long periods, a term number that only rarely increments, and a
commitIndex that advances smoothly and roughly in step across every server.

- **Log this, per server.** Every state transition, Follower to Candidate,
  Candidate to Leader, Leader to Follower, with the old and new term and the
  reason, election timeout, higher term observed, vote received from
  majority. Every election started, with its outcome. Every
  AppendEntries rejection, with the reason, term mismatch, log
  inconsistency at a specific index, since a stream of rejections is the
  clearest signal of a follower falling meaningfully behind.
- **Trace this.** The end-to-end path of a single client command from
  propose on the leader, through replication to each follower, to commit,
  to apply on the state machine, tagged with the log index, so a slow write
  can be diagnosed to the specific follower or stage causing the delay.
- **Metric, leader stability.** Count of leadership changes per unit time,
  cluster-wide. A healthy cluster in steady operation has this near zero.
  A rising rate, even without any actual server crash, is the signature of
  the disruptive-server or misconfigured-timeout failure modes in
  dimension 11.
- **Metric, commitIndex lag per follower.** The gap between the leader's
  commitIndex and each follower's own matchIndex. A consistently large or
  growing gap on one follower indicates it cannot keep up, either from
  resource starvation or network degradation, and is the leading indicator
  that a snapshot transfer or a manual intervention will soon be needed.
- **Metric, election and heartbeat timing histograms.** The actual observed
  distribution of RPC round-trip times against the configured election
  timeout, which is the direct evidence needed to correctly tune the
  timeout parameters discussed in dimension 11's last failure mode, rather
  than guessing at a value.
- **A failing cluster on a dashboard shows.** A leadership-change counter
  climbing steadily rather than sitting near zero, one or more followers
  with a commitIndex lag that only grows, and a client-visible write
  latency distribution with a long tail corresponding to elections rather
  than a tight distribution around the network's steady-state round trip.

## 17. Security and privacy implications

Raft's own RPCs, RequestVote, AppendEntries, and InstallSnapshot, carry no
built-in authentication or encryption. The paper is silent on transport
security entirely, treating it as an orthogonal concern for the deployment
to handle. In practice, every production implementation cited in dimension
9 layers mutual TLS or an equivalent transport-level authentication and
encryption scheme underneath the Raft RPC layer, both to prevent an
unauthorized process from injecting itself as a cluster member, which,
given Raft's crash-recovery-only fault model, would be catastrophic, since
an unauthenticated node could win elections and corrupt committed state,
and to protect the confidentiality of whatever data flows through the log.

The replicated log itself is a durable, append-only record of every command
the cluster has ever processed, retained until log compaction discards the
covered portion. Any sensitive data embedded directly in log entries is
therefore persisted, in the clear unless the deployment encrypts data at
rest, on every server in the cluster, and remains recoverable from any
server's local disk, including a follower that was never the leader, until
that entry is covered by a snapshot and the underlying log segment is
actually deleted, not merely marked compacted. Systems handling sensitive
data through a Raft-backed log commonly avoid putting the sensitive payload
directly in the command, storing a reference and keeping the payload
encrypted in a separate store instead.

Because Raft assumes no participant is malicious, a compromised node that
is a legitimate cluster member has full read access to every entry the
leader replicates to it, by design, since replication to a majority
including that node is exactly what makes a write durable. There is no
concept in the base protocol of a partially-trusted replica that
participates in quorum without seeing plaintext content, a property that
would require a different design, for example combining Raft with
application-level encryption where only authorized clients hold the
decryption key.

## 18. References

1. Diego Ongaro and John Ousterhout, "In Search of an Understandable
   Consensus Algorithm (Extended Version)", USENIX Annual Technical
   Conference, 2014. https://raft.github.io/raft.pdf, verified 2026-08-02.
2. Diego Ongaro, "Consensus, Bridging Theory and Practice", PhD dissertation,
   Stanford University, 2014. Contains the full TLA+ specification and the
   single-server membership change protocol.
   https://github.com/ongardie/dissertation, verified 2026-08-02.
3. Leslie Lamport, "The Part-Time Parliament", ACM Transactions on Computer
   Systems, volume 16, issue 2, May 1998. The original Paxos paper Raft is
   positioned as a response to.
4. etcd documentation, "Design of Learner (Raft section 4.2.1)", describing
   etcd's use of Raft for leadership election and log replication.
   https://etcd.io/docs/v3.5/learning/design-learner/, verified 2026-08-02.
5. HashiCorp, hashicorp/raft repository README, describing the Go Raft
   library used historically by Consul.
   https://github.com/hashicorp/raft, verified 2026-08-02.
6. etcd Raft Go package documentation, describing the PreVote and
   CheckQuorum configuration options.
   https://pkg.go.dev/go.etcd.io/etcd/raft/v3, verified 2026-08-02.
7. PingCAP, TiDB storage architecture documentation, describing TiKV's
   Multi-Raft, per-Region replication design.
   https://docs.pingcap.com/tidb/stable/tidb-storage, verified 2026-08-02.
8. Cockroach Labs, "Replication Layer" architecture documentation,
   describing CockroachDB's use of Raft per data range.
   https://docs.cockroachlabs.com/docs/stable/architecture/replication-layer,
   verified 2026-08-02.
9. Kyle Kingsbury and the Jepsen project, distributed systems testing
   reports and the Knossos linearizability checker, commonly used to
   verify Raft-backed systems' consistency claims under injected failure.
10. MIT 6.824, Distributed Systems course, Raft lab assignments, a widely
    cited teaching implementation and deterministic-simulation test
    test rig for Raft.

## Code examples

Minimal, runnable illustrations of the leader-side commit rule (advance
commitIndex only once an entry is present on a majority of servers, and only
if that entry was appended during the leader's own current term, the
critical safety check from paper section 5.4.2) and the RequestVote
vote-granting check (paper section 5.4.1), the two rules most responsible for
Raft's safety guarantees. These are not full Raft implementations, they
isolate the two decision points that most implementations get wrong first.

### Go

```go
package raft

// logEntry mirrors the paper's log entry, an index, the term the
// leader was in when it appended the entry, and an opaque command.
type logEntry struct {
	Index   int
	Term    int
	Command string
}

// advanceCommitIndex implements the leader-side rule from section 5.4.2.
// An entry may be committed only once it is present on a majority of
// servers AND it was appended during the leader's current term. Committing
// an entry from an earlier term just because a majority now happens to
// hold it would violate the Leader Completeness property.
func advanceCommitIndex(matchIndex []int, currentTerm int, log []logEntry, currentCommit int) int {
	n := len(matchIndex)
	newCommit := currentCommit
	for idx := currentCommit + 1; idx <= len(log); idx++ {
		if log[idx-1].Term != currentTerm {
			continue
		}
		count := 1 // the leader itself always has the entry
		for _, m := range matchIndex {
			if m >= idx {
				count++
			}
		}
		if count*2 > n+1 {
			newCommit = idx
		}
	}
	return newCommit
}

// grantVote implements the RequestVote rule from section 5.4.1. A voter
// grants its vote only if the term is current or newer, it has not already
// voted this term for someone else, and the candidate's log is at least as
// up to date as the voter's own log.
func grantVote(voterTerm, candidateTerm int, votedFor string, candidateID string,
	voterLastLogTerm, candidateLastLogTerm, voterLastLogIndex, candidateLastLogIndex int) bool {
	if candidateTerm < voterTerm {
		return false
	}
	if votedFor != "" && votedFor != candidateID {
		return false
	}
	if candidateLastLogTerm != voterLastLogTerm {
		return candidateLastLogTerm > voterLastLogTerm
	}
	return candidateLastLogIndex >= voterLastLogIndex
}
```

### TypeScript

```typescript
interface LogEntry {
  index: number;
  term: number;
  command: string;
}

// Leader-side commit rule, paper section 5.4.2. Only an entry appended
// during the leader's current term may be committed by counting a
// majority, even once older entries also sit on a majority of servers.
function advanceCommitIndex(
  matchIndex: number[],
  currentTerm: number,
  log: LogEntry[],
  currentCommit: number
): number {
  const clusterSize = matchIndex.length + 1;
  let newCommit = currentCommit;
  for (let idx = currentCommit + 1; idx <= log.length; idx++) {
    if (log[idx - 1].term !== currentTerm) continue;
    let count = 1;
    for (const m of matchIndex) if (m >= idx) count++;
    if (count * 2 > clusterSize) newCommit = idx;
  }
  return newCommit;
}

// RequestVote vote-granting rule, paper section 5.4.1.
function grantVote(
  voterTerm: number,
  candidateTerm: number,
  votedFor: string | null,
  candidateId: string,
  voterLastLogTerm: number,
  candidateLastLogTerm: number,
  voterLastLogIndex: number,
  candidateLastLogIndex: number
): boolean {
  if (candidateTerm < voterTerm) return false;
  if (votedFor !== null && votedFor !== candidateId) return false;
  if (candidateLastLogTerm !== voterLastLogTerm) {
    return candidateLastLogTerm > voterLastLogTerm;
  }
  return candidateLastLogIndex >= voterLastLogIndex;
}

const matchIndex = [5, 5, 3, 3];
const log: LogEntry[] = Array.from({ length: 6 }, (_, i) => ({
  index: i + 1,
  term: i < 5 ? 2 : 3,
  command: `cmd${i + 1}`,
}));
console.log("committed up to:", advanceCommitIndex(matchIndex, 3, log, 0));
console.log(
  "vote granted:",
  grantVote(2, 3, null, "S2", 2, 2, 5, 6)
);
```

### Rust

```rust
struct LogEntry {
    index: u64,
    term: u64,
    command: String,
}

// Leader-side commit rule, paper section 5.4.2.
fn advance_commit_index(
    match_index: &[u64],
    current_term: u64,
    log: &[LogEntry],
    current_commit: u64,
) -> u64 {
    let cluster_size = match_index.len() as u64 + 1;
    let mut new_commit = current_commit;
    for idx in (current_commit + 1)..=(log.len() as u64) {
        let entry = &log[(idx - 1) as usize];
        if entry.term != current_term {
            continue;
        }
        let mut count = 1u64;
        for &m in match_index {
            if m >= idx {
                count += 1;
            }
        }
        if count * 2 > cluster_size {
            new_commit = idx;
        }
    }
    new_commit
}

// RequestVote vote-granting rule, paper section 5.4.1.
fn grant_vote(
    voter_term: u64,
    candidate_term: u64,
    voted_for: Option<&str>,
    candidate_id: &str,
    voter_last_log_term: u64,
    candidate_last_log_term: u64,
    voter_last_log_index: u64,
    candidate_last_log_index: u64,
) -> bool {
    if candidate_term < voter_term {
        return false;
    }
    if let Some(v) = voted_for {
        if v != candidate_id {
            return false;
        }
    }
    if candidate_last_log_term != voter_last_log_term {
        return candidate_last_log_term > voter_last_log_term;
    }
    candidate_last_log_index >= voter_last_log_index
}

fn main() {
    let log: Vec<LogEntry> = (1..=6)
        .map(|i| LogEntry {
            index: i,
            term: if i <= 5 { 2 } else { 3 },
            command: format!("cmd{i}"),
        })
        .collect();
    let match_index = [5u64, 5, 3, 3];
    let committed = advance_commit_index(&match_index, 3, &log, 0);
    println!("committed up to: {committed}");
    let granted = grant_vote(2, 3, None, "S2", 2, 2, 5, 6);
    println!("vote granted: {granted}");
}
```
