---
name: Paxos
slug: paxos
family: 12-data-storage
category: Distributed Consensus
aliases: [Synod Protocol, Single-Decree Paxos, Multi-Paxos]
first_described: "Lamport 1998 (written), Lamport 2001 (Paxos Made Simple, published)"
maturity: canonical
related: [raft, two-phase-commit, three-phase-commit, leader-election, quorum, replicated-state-machine]
incompatible_with: []
verified: 2026-08-02
---

# Paxos

## 1. Name, aliases, and lineage

The canonical name is Paxos. Leslie Lamport wrote the algorithm down as "The
Part-Time Parliament," a paper framed as an anthropological account of a
fictional Greek island legislature. The paper sat unpublished for years,
reportedly because reviewers found the narrative frame more distracting than
illuminating, and eventually appeared in ACM Transactions on Computer Systems,
volume 16, issue 2, May 1998, pages 133 to 169. Because the original paper was
hard for readers to get through, Lamport wrote a second, plainer explanation
titled "Paxos Made Simple," published in ACM SIGACT News, volume 32, issue 4
(whole number 121), December 2001, pages 51 to 58
([Microsoft Research publication page](https://www.microsoft.com/en-us/research/publication/paxos-made-simple/),
verified 2026-08-02). Lamport has said in talks that he "got tired of everyone
saying how difficult it was to understand the Paxos algorithm" and that people
got hung up on the pseudo-Greek names even though the algorithm itself is
simple, which is why the second paper drops the parliament framing entirely
([search summary of the SIGACT News introduction](https://lamport.azurewebsites.net/pubs/paxos-simple.pdf),
verified 2026-08-02).

The name Paxos is the fictional island in the parliament story, and it stuck to
the algorithm even after later papers dropped the narrative. Two aliases are in
wide practical use and mean two different things, which is worth separating
cleanly because most confusion about "using Paxos" traces back to conflating
them.

- **Synod Protocol.** The name Lamport gives, inside "The Part-Time
  Parliament," to the sub-protocol that gets a single group of participants to
  agree on a single value. This is what the rest of this entry calls
  single-decree Paxos, and it is the mathematical core that every variant
  below builds on.
- **Multi-Paxos.** Not a name Lamport used in the original papers as a
  formal term, but the name the systems community settled on for the standard
  engineering technique of chaining many single-decree Paxos instances, one
  per slot in a replicated log, with a stable leader that skips the Prepare
  phase for consecutive slots once it holds it. "Paxos Made Simple" itself
  describes exactly this construction in its closing sections without naming
  it, and later systems papers such as Google's "Paxos Made Live" name the
  optimization explicitly (Tushar Chandra, Robert Griesemer, Joshua Redstone,
  "Paxos Made Live. An Engineering Perspective," PODC 2007, section 3,
  [paper PDF](https://www.cs.utexas.edu/~lorenzo/corsi/cs380d/papers/paper2-1.pdf),
  verified 2026-08-02).

A related and frequently cited teaching paper is Robbert van Renesse and Deniz
Altinbuken, "Paxos Made Moderately Complex," ACM Computing Surveys, volume 47,
issue 3, February 2015, which works through the full engineering detail (state
machine replication, leader election, log compaction) that "Paxos Made Simple"
leaves as an exercise
([paper PDF](https://www.cs.cornell.edu/home/rvr/Paxos/paxos.pdf), verified
2026-08-02). This entry treats Paxos as the family described across these four
papers, the original 1998 proof, the 2001 simplification, the 2007 production
report, and the 2015 engineering completion, rather than as a single fixed
text.

## 2. Problem and context

A group of machines needs to agree on one value, and any one of them can crash
or become unreachable at any moment, including in the middle of trying to get
everyone to agree. The group cannot wait for every machine to be reachable,
because a network partition or a single dead disk would then stop the whole
system forever. The group also cannot let a minority of machines decide on
their own, because a partition could then produce two different, contradictory
decisions on each side of the split.

The concrete shape this takes in a real system is this. Several replicas hold
copies of a log or a piece of state, and something happens (a write request
arrives, a leader needs electing, a lock needs granting) that requires the
replicas to settle on exactly one next entry, with no way to undo the decision
once made. A design that just picks the fastest replica's answer is not safe,
because two replicas can each believe they were fastest during a network
glitch. A design that requires unanimous agreement is not live, because one
dead machine then freezes the whole system.

Paxos exists for the specific context where the participants are willing to
tolerate a minority being down, unreachable, or slow, in exchange for the
guarantee that whatever gets agreed on is agreed on for good, never silently
overwritten later even if the network does something adversarial. This is the
asynchronous crash-fault model. Messages can be arbitrarily delayed, duplicated
or dropped, and processes can crash and later recover with their persistent
state intact, but no process ever sends a message that lies about the
protocol's own rules (Paxos does not defend against Byzantine, actively
malicious participants, which is a separate, harder problem with its own
literature).

## 3. Forces

Judgement. Which force dominates in a given deployment is a design call, not a
provable fact, so this section states reasoning rather than citing a source
for every sentence.

- **Safety versus liveness.** Paxos is designed to never sacrifice safety
  (only one value is ever chosen, and nobody learns a wrong value) even when
  that means giving up liveness temporarily (no value gets chosen at all,
  for a while, if proposers keep interrupting each other). This is a
  deliberate asymmetry. An unavailable system can always be restarted, a
  system that returns two different answers for one decision cannot be
  un-corrupted.
- **Latency versus fault tolerance.** Each additional acceptor added to
  tolerate one more simultaneous failure adds one more vote that has to be
  collected before a decision commits, which raises tail latency, because a
  message round trip is bounded by the slowest replica in the quorum, not the
  average.
- **Message complexity versus round trips.** Single-decree Paxos needs two
  full round trips (Prepare/Promise, then Accept/Accepted) to commit any
  value from a cold start. Multi-Paxos amortizes the first round trip across
  many decisions once a leader is stable, trading a small window of
  unavailability during leader changes for near-optimal steady-state latency.
- **Coupling to a specific leader versus symmetry.** The original algorithm
  has no leader at all, any proposer can propose at any time, which is
  elegant and censorship-resistant but pathologically prone to dueling
  proposers that never let each other finish (the livelock this entry covers
  in dimension 11). Every production system reintroduces a leader, which
  restores throughput at the cost of a moment of unavailability whenever the
  leader is suspected dead and a new one has to be elected.
- **Understandability versus what got built.** The protocol as specified is
  short, but production Paxos needs a huge amount of surrounding machinery
  (log compaction, group membership changes, leader leases) that is not part
  of the base algorithm and is where most of the engineering effort and most
  of the historical bugs actually live. Diego Ongaro and John Ousterhout make
  exactly this point in motivating Raft. "Paxos is notoriously difficult to
  understand... Its architecture is a poor one for building practical
  systems, requiring complex changes to create an efficient and complete
  solution" (Diego Ongaro, John Ousterhout, "In Search of an Understandable
  Consensus Algorithm," USENIX ATC 2014, section 1, page 1,
  [paper PDF](https://raft.github.io/raft.pdf), verified 2026-08-02).

## 4. Applicability and non-applicability

Reach for Paxos when the following hold.

- A set of replicas must agree on a totally ordered sequence of values (a
  replicated log, a sequence of configuration changes) and must keep working
  when a minority of replicas are down or slow.
- The system must survive the crash of any single coordinating process
  without losing or duplicating a committed decision, and restarting a
  crashed process with its disk intact is an acceptable recovery path.
- You are building the lowest layer that everything else in a distributed
  system is bootstrapped from, a lock service, a metadata store, a
  configuration authority. Chubby is the canonical example of this role
  (Mike Burrows, "The Chubby Lock Service for Loosely-Coupled Distributed
  Systems," OSDI 2006, section 1,
  [paper PDF](https://static.googleusercontent.com/media/research.google.com/en//archive/chubby-osdi06.pdf),
  verified 2026-08-02).
- You specifically need single-round-trip conditional writes (compare and
  set) at the individual row or key level rather than log replication, which
  is what Cassandra's lightweight transactions use Paxos for.

Do not reach for Paxos when any of the following hold.

- The team implementing and operating the system has no prior distributed
  systems background and will be debugging it in production. Ongaro and
  Ousterhout's central argument is that this exact gap between "the algorithm
  is provably correct" and "engineers can build and reason about it" is
  Paxos's biggest practical cost, and it is the reason Raft exists as an
  alternative with the same guarantees ([paper](https://raft.github.io/raft.pdf),
  section 1, verified 2026-08-02). Use Raft in a new system where either
  algorithm would satisfy the requirement.
- The workload does not actually need linearizable, ordered agreement. A
  cache invalidation, a metrics counter, or an eventually-consistent
  replicated set does not need consensus, and paying its latency and
  operational cost for these is waste. Use a CRDT or gossip-based
  anti-entropy instead.
- You need Byzantine fault tolerance, meaning some participants may lie or
  behave arbitrarily, not merely crash. Paxos assumes crash-stop or
  crash-recover failures and provides no protection against a node that
  sends contradictory messages on purpose. Use PBFT or a blockchain-style
  protocol.
- The group of participants is a single machine, or all participants fail
  together (same rack, same power supply, same availability zone), because
  Paxos's guarantees are about surviving independent failures, and it adds
  real complexity and latency for a fault model that does not hold.
- You need a decision made even when a majority is down. Paxos is
  CP in the sense of the CAP theorem. During a partition that leaves no
  majority reachable, it deliberately refuses to make progress rather than
  risk two different answers. If your requirement is "always answer, even a
  stale answer," Paxos is the wrong tool.

## 5. Structure

Single-decree Paxos has three roles. A single physical process commonly plays
more than one role at once, the roles are logical, not deployment units.

- **Proposer.** Initiates a proposal identified by a proposal number, drives
  it through the two phases, and is responsible for choosing which value to
  propose, subject to the constraint in dimension 7 that it must adopt any
  value it learns a quorum may already have accepted.
- **Acceptor.** The stateful role. Holds two pieces of durable state per
  decision, the highest proposal number it has promised to honor, and, if
  any, the value and number of the highest proposal it has actually accepted.
  A group of acceptors is where the fault tolerance lives, the protocol only
  requires a majority quorum of them to be reachable and durable at any given
  moment.
- **Learner.** Finds out what value was chosen. In the simplest form every
  acceptor tells every learner directly when it accepts a value and a learner
  infers a chosen value once a majority of acceptors report the same one, in
  practice systems designate a distinguished learner (often the leader) to
  avoid an all-to-all message pattern.

Multi-Paxos adds a fourth, non-formal role that the base papers describe
without naming distinctly.

- **Leader (Distinguished Proposer).** A single proposer that other
  proposers defer to for as long as it appears alive, so that phase 1
  (Prepare/Promise) needs to run only once for a whole run of consecutive log
  slots instead of once per slot, and steady-state commits collapse to a
  single round trip (phase 2 only).

## 6. ASCII structure diagram

```
                     +----------------------------+
                     |          Proposer          |
                     |  chooses proposal number n |
                     |  chooses / adopts value v  |
                     +--------------+-------------+
                                    |
                       Prepare(n)  /  \  Accept(n, v)
                                  /    \
        +----------------------+      +----------------------+
        |      Acceptor A       |      |      Acceptor B       |
        | promised: n           |      | promised: n           |
        | accepted: (id, val)   |      | accepted: (id, val)   |
        +-----------+------------+      +-----------+------------+
                    |                              |
                    +--------------+---------------+
                                   |
                     majority of {A, B, C, D, E}
                                   |
                     +-------------v-------------+
                     |          Learner           |
                     |  value is CHOSEN once a    |
                     |  majority accepted the     |
                     |  same (id, value) pair     |
                     +----------------------------+

  Any 2 out of any 5 acceptors can be unreachable and the group still
  reaches a decision, because any two majorities of 5 always overlap in
  at least one acceptor (this overlap is the whole safety argument).
```

## 7. Dynamics

Single-decree Paxos runs in two phases, each with a request and a response
half. Every message carries a proposal number that is unique to the proposer
that generated it (commonly `round * total_proposers + proposer_id`, so no two
proposers ever generate the same number) and every acceptor tracks proposal
numbers monotonically, never going backward.

```
Proposer                    Acceptor (any one of N)
   |                              |
   |--- Prepare(n) -------------->|
   |                              | if n > promised:
   |                              |    promised = n
   |                              |    reply Promise(n, accepted_id,
   |                              |                    accepted_val)
   |                              | else:
   |                              |    reply Reject
   |<---- Promise / Reject -------|
   |                              |
   |  (proposer waits for a majority of Promise replies)
   |
   |  choose v = value of the highest-numbered accepted proposal
   |            among the Promise replies, or the proposer's own
   |            value if no acceptor had accepted anything yet
   |
   |--- Accept(n, v) ------------>|
   |                              | if n >= promised:
   |                              |    promised = n
   |                              |    accepted_id = n
   |                              |    accepted_val = v
   |                              |    reply Accepted(n)
   |                              | else:
   |                              |    reply Reject
   |<---- Accepted / Reject ------|
   |
   |  (proposer waits for a majority of Accepted replies)
   |  value v is now CHOSEN, forever, regardless of future crashes
```

Two invariants make this safe, stated informally here and precisely in the
source cited below. P1 says an acceptor must accept the first proposal it
ever receives. P2 says once a value has been chosen, every higher-numbered
proposal that any acceptor subsequently accepts must have that same value.
Lamport's paper derives P2 through the successive refinements P2a and P2b down
to the actual rule an acceptor can check locally, P2c. an acceptor may accept
proposal `(n, v)` only if no acceptor has accepted any proposal numbered less
than `n` with a value other than `v`, among the acceptors that have responded
to a Prepare for `n` or higher (Lamport, "Paxos Made Simple," 2001, sections
2.3 and 2.4, [paper PDF](https://lamport.azurewebsites.net/pubs/paxos-simple.pdf),
verified 2026-08-02). The Prepare/Promise phase exists precisely so a proposer
can discover, before proposing, whether any acceptor already accepted a value
under a lower number, and if so it must adopt that value rather than its own.
This is the single mechanism that prevents two different values from both
being chosen, and it is demonstrated concretely in the working code below.

In Multi-Paxos, a leader that already holds an unrevoked promise for the
highest proposal number across a whole log skips Prepare for every subsequent
slot and goes straight to Accept, which is why steady-state Multi-Paxos costs
one round trip per committed entry rather than two.

## 8. Implementation variants

- **Single-decree, ad hoc leaderless.** The base algorithm exactly as
  specified in "Paxos Made Simple." Any proposer can propose at any time.
  Correct but prone to livelock under contention (dimension 11), and rarely
  deployed as-is outside of teaching and formal-verification exercises.
- **Multi-Paxos with a stable leader.** The production shape. A leader
  elected (often via a separate Paxos round, or a lease mechanism, or a
  simpler heuristic like lowest process ID) runs Prepare once, then Accept
  repeatedly for consecutive log slots. Chandra, Griesemer, and Redstone's
  "Paxos Made Live" describes exactly this construction as run inside Google
  Chubby, along with the group-membership and disk-corruption handling the
  base papers omit (PODC 2007, section 3, verified 2026-08-02).
- **Cheap Paxos.** A variant that runs the normal quorum during healthy
  operation but only requires `f + 1` of `2f + 1` acceptors to be online, with
  the remaining `f` "auxiliary" acceptors activated only after a failure, to
  reduce steady-state hardware cost. Leslie Lamport and Mike Massa, "Cheap
  Paxos," DSN 2004, abstract,
  [paper PDF](https://lamport.azurewebsites.net/pubs/web-dsn-submission.pdf),
  verified 2026-08-02.
- **Fast Paxos.** Lets a proposer send Accept messages directly to acceptors
  in some rounds without going through a distinguished leader first, reducing
  latency to one round trip under low contention at the cost of needing a
  larger quorum (`ceil(3/4)` rather than a simple majority) to resolve
  collisions safely. Leslie Lamport, "Fast Paxos," Distributed Computing,
  2006,
  [publication page](https://www.microsoft.com/en-us/research/publication/fast-paxos/),
  verified 2026-08-18.
- **Egalitarian Paxos (EPaxos).** Removes the single stable leader entirely
  and lets any replica commit a command in one round trip in the common case,
  by tracking interference between concurrent commands rather than a total
  order up front. Iulian Moraru, David G. Andersen, Michael Kaminsky,
  "There Is More Consensus in Egalitarian Parliaments," SOSP 2013, abstract,
  [paper PDF](https://www.cs.cmu.edu/~dga/papers/epaxos-sosp2013.pdf),
  verified 2026-08-02.
- **Compare-and-set on a single key (Cassandra's Paxos).** Runs a full
  Prepare/Propose/Accept/Commit cycle per row, scoped to that row's replica
  set, to implement `INSERT ... IF NOT EXISTS` and `UPDATE ... IF` without
  a separate log or leader. This is a different deployment shape from log
  replication even though it uses the same core algorithm, as documented in
  DataStax's lightweight transactions documentation and the AxonOps
  engineering writeup of the newer "Paxos v2" optimization
  ([DataStax docs](https://docs.datastax.com/en/cassandra-oss/3.0/cassandra/dml/dmlLtwtTransactions.html),
  verified 2026-08-02;
  [AxonOps blog](https://axonops.com/blog/paxos-v2-and-lightweight-transactions/),
  verified 2026-08-02).

Language-idiomatic note. The working code below is deliberately not
"idiomatic" in a language-specific sense, because Paxos has no natural
mapping onto any single language feature (no closure, no iterator, no
generic replaces it). What differs across languages is how the durable
acceptor state and the network transport are typically wired. Go tends to
express the acceptor as a goroutine owning a channel, Java systems (Chubby's
descendants) tend to express it as a durable log-backed actor, and Rust
implementations lean on the type system to make an illegal state (accepting
without a live promise) unrepresentable at compile time.

## 9. Known production uses

- **Google Chubby**, the internal lock and small-file coordination service
  that Google's own infrastructure (GFS, Bigtable, and others in 2006) used
  to elect a master and hold configuration data, is built directly on Paxos
  for its replication, as described by its own designer. Mike Burrows,
  "The Chubby Lock Service for Loosely-Coupled Distributed Systems," OSDI
  2006, section 3, [paper PDF](https://static.googleusercontent.com/media/research.google.com/en//archive/chubby-osdi06.pdf),
  verified 2026-08-02.
- **Google's production Paxos implementation** underlying Chubby, plus the
  gap between the textbook algorithm and what shipping it actually required
  (disk corruption handling, group membership changes, an epoch-based leader
  election on top of the base algorithm), is documented first-hand by the
  Google engineers who built it. Tushar Chandra, Robert Griesemer, Joshua
  Redstone, "Paxos Made Live. An Engineering Perspective," PODC 2007,
  [paper PDF](https://www.cs.utexas.edu/~lorenzo/corsi/cs380d/papers/paper2-1.pdf),
  verified 2026-08-02.
- **Apache Cassandra** uses Paxos to implement its lightweight transactions
  (linearizable compare-and-set operations, `IF NOT EXISTS` and conditional
  `UPDATE`), scoped per partition, and its documentation explicitly names the
  Prepare, Propose, Accept, and Commit phases as Paxos phases. DataStax,
  "How do I accomplish lightweight transactions with linearizable
  consistency?", Apache Cassandra 3.0 documentation,
  [docs page](https://docs.datastax.com/en/cassandra-oss/3.0/cassandra/dml/dmlLtwtTransactions.html),
  verified 2026-08-02.

Judgement, not independently re-verified for this entry with a primary
source at the time of writing. Google's Spanner and Megastore systems, and
Microsoft's early Windows Azure Storage stamp coordination, are widely
described in the systems literature as using Paxos-family protocols for
metadata and replica-set agreement. Readers relying on that claim for a
citation-grade purpose should verify against the Spanner OSDI 2012 paper and
the Windows Azure Storage SOSP 2011 paper directly rather than this summary.

## 10. Consequences

Positive.

- Tolerates the crash or unreachability of any minority of acceptors without
  losing safety, and resumes making progress automatically once a majority
  is reachable again, with no manual intervention or data reconciliation
  step required.
- Provides a mathematically proven safety guarantee (Lamport's 1998 paper
  includes a full correctness proof) rather than an empirically-tested one,
  which matters for a component everything else in a system is built on top
  of.
- Degrades gracefully under partial failure. A minority partition simply
  stalls rather than diverging, so there is never a split-brain scenario to
  detect and repair after the fact.
- Composable into a replicated state machine. Once single-decree Paxos
  agrees on one log entry, the well-understood technique of chaining
  instances (Multi-Paxos) gives you an arbitrarily long, totally-ordered,
  fault-tolerant log for free.

Negative.

- Genuinely hard to get right in production. "Paxos Made Live" spends most
  of its length on problems the base algorithm does not address at all
  (disk corruption producing a torn write of the promised/accepted state,
  changing the acceptor set without a window of unsafety, master leases),
  and states plainly that "there are significant gaps between the description
  of the Paxos algorithm and the needs of a real-world system," requiring
  "not just understanding individual algorithms but also creatively
  combining them" (Chandra, Griesemer, Redstone, PODC 2007, abstract and
  section 2, verified 2026-08-02).
- Costs at least two message round trips to commit a value from a cold
  start (Prepare/Promise, then Accept/Accepted), and every acceptor's
  response has to be durable on disk before it replies, so latency is bound
  by disk fsync time plus the slowest reachable majority member's network
  round trip.
- Requires `2f + 1` acceptors to tolerate `f` simultaneous failures, so
  fault tolerance is directly paid for in hardware and cross-machine
  bandwidth. There is no way to get 3-failure tolerance for the price of a
  2-failure deployment.
- The base algorithm alone provides no throughput past what a single
  leader's fsync rate allows. Scaling reads and writes further requires
  sharding into many independent Paxos groups, which is its own significant
  system-design problem (this is essentially what Spanner's architecture is
  built around).

## 11. Failure modes and misuse

Judgement. The symptoms below are drawn from the cited engineering papers and
from widely reproduced descriptions of Paxos operational behavior, and are
labeled as observed behavior, not formally proven properties.

| Symptom | Cause | Fix |
|---|---|---|
| Commits stall completely under moderate write concurrency, CPU and network utilization stay low, but nothing ever gets chosen | Dueling proposers, two or more proposers keep issuing higher-numbered Prepare requests that abort each other's in-flight Accept phase before it completes, an infinite livelock the base algorithm does not prevent on its own | Elect a single distinguished leader (Multi-Paxos) and route all proposals through it; give the leader a randomized backoff before retrying after a Prepare rejection |
| Two different values appear to have been "chosen" for the same log slot after a crash and restart | An acceptor's promised or accepted proposal number was not durably written to stable storage before the process crashed, so it forgot a promise it had already made and later voted inconsistently | Never acknowledge a Promise or an Accepted message until the corresponding state change is fsynced to durable storage; treat this as a hard invariant, not a performance knob |
| A replica that was offline for an extended window rejoins and its log falls further and further behind, eventually causing operator intervention | Multi-Paxos as specified has no built-in mechanism for catching up a replica whose gap exceeds what the leader retains; the base papers explicitly leave log compaction and state transfer as an implementation exercise | Implement a separate snapshot-and-install-snapshot path (the same shape Raft standardizes) so a far-behind replica can be brought current by copying state rather than replaying every missing decision |
| A membership change (adding or removing an acceptor) is followed by a brief window where two disjoint majorities can both believe they hold quorum | Naively swapping the acceptor set atomically breaks the majority-overlap guarantee that makes Paxos safe, because the old majority and the new majority may not intersect | Use a joint-consensus or single-server-change-at-a-time protocol so that every majority under the old configuration overlaps every majority under the new one at all times during the transition |
| Application-level correctness bugs appear only under specific network delay patterns in staging, never in unit tests | Paxos's state space (proposal numbers, interleaved Prepare/Accept phases from multiple proposers, crash-and-recover at arbitrary points) is too large to cover by hand-written test cases | Use model checking (TLA+, the same specification language Lamport used to originally verify Paxos) or deterministic simulation testing that can inject specific message reorderings and crash points |
| A single slow or partitioned acceptor causes every write's tail latency to spike, even though the acceptor is a minority member | The naive implementation waits for replies from all acceptors rather than stopping at the first majority to reply, so one straggler still holds up the observed latency of the group even though it cannot block correctness | Complete the phase as soon as a majority of replies (not all replies) has arrived, and treat late replies from the remaining minority as informational only |

## 12. Trade-off matrix

| Force | Paxos (Multi-Paxos) | Raft | Two-Phase Commit | Three-Phase Commit |
|---|---|---|---|---|
| Tolerates coordinator crash without blocking | Yes, any minority of acceptors including the leader can crash | Yes, same fault model as Paxos | No, a crashed coordinator after prepare leaves participants blocked indefinitely | Partially, adds a pre-commit phase to bound blocking, but still assumes synchronous timeouts to avoid a split decision |
| Understandability for the team implementing it | Low; Ongaro and Ousterhout built Raft specifically because Paxos scored poorly here in their own teaching study ([paper](https://raft.github.io/raft.pdf), section 1) | High by design; the same paper reports substantially better comprehension test results for Raft over Paxos among students taught both | Moderate; the two-phase idea itself is simple, the failure handling around it is where the difficulty hides | Moderate to low; adds a phase specifically to fix 2PC's blocking problem, which itself requires careful timeout tuning |
| Steady-state commit latency | One round trip once a stable leader holds an unexpired promise | One round trip, same shape as Multi-Paxos in steady state | One round trip for the happy path, but the protocol offers no fault tolerance for it | Two round trips, the extra phase is the direct cost of bounding blocking |
| Requires a distinguished coordinator to make progress | No in the base algorithm, yes in every practical Multi-Paxos deployment | Yes, always; a leader is part of the formal specification, not an optimization layered on top | Yes, and the coordinator is a single point of blocking on crash | Yes, same role as 2PC's coordinator |
| Survives loss of a minority of participants and keeps deciding | Yes | Yes | No | Partially, only under a synchrony assumption that bounds message delay |
| Formal specification and proof available from the original source | Yes, Lamport's 1998 TOCS paper includes a full proof | Yes, the Raft paper and Ongaro's dissertation include a proof, built to be an easier one to follow | No standard formal proof in the original literature; it is a simple protocol whose blocking failure mode is well understood empirically | Partial, the protocol was designed to address a known gap in 2PC's fault tolerance under a synchrony assumption |

## 13. Related and incompatible patterns

- **Raft.** Solves the identical problem (crash-fault-tolerant replicated
  log consensus) with the same formal guarantees as Multi-Paxos, but is
  specified from the start around a single elected leader and a
  restrict-yourself-to-the-most-up-to-date-candidate election rule, which
  the Raft authors argue makes the whole protocol substantially easier for
  engineers to implement correctly and reason about (Ongaro, Ousterhout,
  USENIX ATC 2014, verified 2026-08-02). Choosing between them today is
  largely a question of which one the team can implement and operate
  correctly. Raft is not more powerful than Paxos, it targets the same
  consistency guarantee.
- **Two-Phase Commit and Three-Phase Commit.** Solve a related but distinct
  problem, atomic commitment of a single transaction across multiple
  independent resource managers, rather than ongoing replication of a log
  among peers that all hold the same kind of state. 2PC has no fault
  tolerance for a coordinator crash between phases. Paxos is sometimes used
  underneath a transaction coordinator specifically to make the coordinator
  itself fault tolerant, which is a composition, not a substitution.
- **Leader Election.** Multi-Paxos requires a leader-election mechanism as a
  precondition for its steady-state optimization, and that election is
  itself frequently implemented as a single-decree Paxos round over "who is
  the current leader," making leader election both a consumer of Paxos and,
  circularly, a building block Multi-Paxos depends on.
- **Quorum (the general pattern).** Paxos is a specific, safety-proven
  instance of the broader idea of requiring overlapping majority
  acknowledgment before treating an operation as durable. Systems that use
  ad hoc read/write quorums without Paxos's proposal-numbering discipline
  (classic Dynamo-style `R + W > N` quorums) get availability and
  eventual consistency but not linearizability, and are not a safe
  substitute wherever Paxos's stronger guarantee is actually required.
- **Replicated State Machine.** The umbrella pattern that Paxos (and Raft)
  implement one layer of. A replicated state machine applies the same
  deterministic sequence of commands to every replica. Paxos is the
  mechanism that guarantees every replica agrees on that sequence, one entry
  at a time.
- **Incompatible with naive dynamic membership.** Swapping the acceptor set
  without a joint-consensus-style transition (dimension 11) actively breaks
  Paxos's core safety proof, because the proof depends on every quorum under
  the old and new configurations overlapping. This is not a performance
  trade-off, it is a correctness bug if done carelessly.

## 14. Refactoring path in and out

Introducing Paxos into a system that currently has no consensus layer.

1. Identify the single piece of state whose agreement actually needs to be
   linearizable across replicas (a leader identity, a log offset, a lock
   holder). Resist the urge to route everything through consensus, because
   every decision that goes through it pays the full round-trip cost.
2. Stand up an odd-sized acceptor group (3 or 5 is standard) with durable,
   fsync-backed storage for the promised and accepted proposal state per
   decision slot. Get this storage layer correct and tested before writing
   any proposer logic, since a durability bug here is the single most common
   source of the split-brain failure in dimension 11.
3. Implement single-decree Paxos first, with one hardcoded decision, and
   write a test rig that can inject arbitrary message delays, drops, and
   crash-and-restart at arbitrary points in the protocol, because ad hoc
   manual testing will not surface the interleavings that break it.
4. Extend to Multi-Paxos by chaining slot numbers and adding a leader
   election mechanism (itself often built as a Paxos round or a
   lease-based heuristic). Add log compaction and a snapshot-transfer path
   before deploying, since a replica that falls behind with no way to catch
   up will eventually force manual operator intervention.
5. Add group membership change support last, using joint consensus or a
   single-change-at-a-time discipline, only once the fixed-membership case
   is fully proven in production.

Removing Paxos, or replacing it, once it stops earning its place.

1. Confirm the actual consistency requirement first. If downstream
   consumers only ever need eventual consistency or can tolerate a brief
   stale read, the replacement is a much larger design change than swapping
   one consensus library for another, and should be evaluated as such.
2. If the requirement is unchanged but the team is struggling to operate the
   existing Paxos implementation correctly, migrating to Raft while keeping
   the exact same guarantee is usually the lower-risk path, because the
   external contract (a linearizable replicated log) does not change, only
   the internal protocol producing it.
3. If the requirement was overprovisioned (Paxos deployed for a piece of
   state that never actually needed cross-replica linearizability), replace
   it with a simpler mechanism scoped to the real requirement, a
   single-writer with a lease, or a CRDT if the operations are
   commutative, and delete the consensus group entirely rather than leaving
   it running unused.

## 15. Testing and verification

Judgement. This dimension is written from established practice in the systems
literature, not from a single citable checklist.

- **Formal specification checking.** Lamport's own toolchain for verifying
  Paxos-family protocols is TLA+, and writing the protocol as a TLA+
  specification and model-checking it with TLC is the standard way to
  exhaustively search small configurations (3 to 5 acceptors, a handful of
  proposal rounds) for safety violations before writing any implementation
  code. This catches the class of bug where two values both appear chosen
  under a specific interleaving no human reviewer thought to check by hand.
- **Deterministic simulation testing.** Because the interesting bugs live in
  message reordering, duplication, and mid-protocol crash-and-restart, an
  implementation-level test rig that runs the whole acceptor and
  proposer logic inside a single deterministic event loop, with a
  test-controlled clock and network, and that can replay a failing seed
  exactly, finds the bugs that pure unit tests of individual functions
  cannot, because the bug is in the interaction, not in any single function.
- **Fault injection.** Explicitly test an acceptor crashing between
  receiving a Prepare and replying to it, an acceptor crashing between
  updating its promised state and fsyncing it, a proposer crashing after a
  majority of Accept replies but before informing any learner, and a
  network partition that isolates exactly a minority versus exactly a
  majority. Each of these corresponds to a specific step in the correctness
  proof, and each should have a dedicated test.
- **What Paxos itself makes easy to test.** Because the algorithm's safety
  property is stated as a pure invariant over acceptor state (no acceptor
  ever accepts a value contradicting an already-chosen one), it is
  straightforward to write a property-based test that runs many random
  schedules of the same fixed set of operations and asserts the invariant
  holds after every step, rather than hand-writing individual scenarios.
- **What becomes harder.** End-to-end integration tests that depend on wall
  clock timing (leader election timeouts, lease expiry) are inherently
  flaky unless the clock itself is injected and controlled by the test, and
  teams that skip this step tend to end up with a test suite that is
  intermittently red for reasons unrelated to the change under test.

## 16. Observability signals

Judgement. Derived from what production Paxos operators actually need to
watch, not from a single normative source.

- **Time to chosen value, per decision slot.** The elapsed time from a
  proposer issuing its first Prepare to a value being learned as chosen.
  A healthy leader-stable system should show this dominated by a single
  fsync-plus-round-trip. A rising or bimodal distribution usually means
  either leader instability or a slow minority acceptor being waited on
  unnecessarily.
- **Prepare rejection rate.** How often a Prepare request is rejected
  because the acceptor already promised a higher number. Near zero in a
  healthy, single-leader Multi-Paxos deployment. A sustained non-zero rate
  is the direct signal of the dueling-proposer livelock in dimension 11 and
  should trigger investigation of leader stability, not a latency-only
  alert.
- **Leader churn rate.** How many times per hour a new leader is elected.
  Frequent churn (seconds to minutes between elections) means the group is
  spending most of its time in the unavailable window between leaders
  rather than making progress, and is the single strongest signal that
  something upstream (network flapping, an overloaded leader process, an
  overly aggressive election timeout) needs fixing.
- **Acceptor quorum health.** Which acceptors are currently reachable and
  up to date, exposed per-acceptor so an operator can distinguish "the group
  is at full strength" from "the group is limping along on the bare minimum
  majority," since the latter means the very next failure takes the whole
  group down.
- **Log lag per replica.** How far behind the leader's committed index each
  replica's applied index sits, which is the direct signal for whether a
  replica needs a snapshot transfer rather than continuing to replay the
  log entry by entry.

## 17. Security and privacy implications

The base Paxos protocol assumes a crash-fault, non-Byzantine environment and
provides no cryptographic authentication of messages, no confidentiality, and
no defense against a participant that deliberately sends contradictory or
malformed messages. A single compromised acceptor that lies about its
promised or accepted state can violate the safety guarantee that makes the
protocol worth using in the first place. This is stated explicitly as the
model boundary in the foundational description of the fault model these
protocols assume (an asynchronous system with crash failures, as opposed to
arbitrary or Byzantine failures), and it is why Paxos is deployed inside a
trust boundary (a single organization's data center or private network)
rather than across mutually distrusting parties.

Judgement, analytical rather than sourced. In practice this means the
network between acceptors should be authenticated and, where it crosses a
boundary an attacker could reach, encrypted, since Paxos messages carry no
protection of their own. The acceptor's durable storage is also a sensitive
asset, since an attacker who can corrupt or roll back an acceptor's disk can
potentially cause it to violate a promise it already made. Because Paxos is
frequently the substrate under a lock service or metadata store, a
successful attack on the consensus layer can cascade into every system built
on top of it, which is exactly the blast radius Chubby's design accepts in
exchange for the simplicity of having one trusted coordination point. For
cross-organization or adversarial settings where a participant might lie on
purpose, Paxos is the wrong protocol family entirely and a Byzantine fault
tolerant consensus protocol should be used instead.

## 18. References

1. Leslie Lamport, "The Part-Time Parliament," ACM Transactions on Computer
   Systems, volume 16, issue 2, May 1998, pages 133 to 169. Original proof of
   the algorithm, published under the fictional-parliament framing.
2. Leslie Lamport, "Paxos Made Simple," ACM SIGACT News, volume 32, issue 4
   (whole number 121), December 2001, pages 51 to 58,
   [https://lamport.azurewebsites.net/pubs/paxos-simple.pdf](https://lamport.azurewebsites.net/pubs/paxos-simple.pdf),
   verified 2026-08-02. Also indexed at
   [https://www.microsoft.com/en-us/research/publication/paxos-made-simple/](https://www.microsoft.com/en-us/research/publication/paxos-made-simple/),
   verified 2026-08-02.
3. Tushar Chandra, Robert Griesemer, Joshua Redstone, "Paxos Made Live. An
   Engineering Perspective," Proceedings of the 26th Annual ACM Symposium on
   Principles of Distributed Computing (PODC 2007),
   [https://www.cs.utexas.edu/~lorenzo/corsi/cs380d/papers/paper2-1.pdf](https://www.cs.utexas.edu/~lorenzo/corsi/cs380d/papers/paper2-1.pdf),
   verified 2026-08-02.
4. Robbert van Renesse, Deniz Altinbuken, "Paxos Made Moderately Complex,"
   ACM Computing Surveys, volume 47, issue 3, article 42, February 2015,
   [https://www.cs.cornell.edu/home/rvr/Paxos/paxos.pdf](https://www.cs.cornell.edu/home/rvr/Paxos/paxos.pdf),
   verified 2026-08-02.
5. Mike Burrows, "The Chubby Lock Service for Loosely-Coupled Distributed
   Systems," Proceedings of the 7th USENIX Symposium on Operating Systems
   Design and Implementation (OSDI 2006),
   [https://static.googleusercontent.com/media/research.google.com/en//archive/chubby-osdi06.pdf](https://static.googleusercontent.com/media/research.google.com/en//archive/chubby-osdi06.pdf),
   verified 2026-08-02.
6. Diego Ongaro, John Ousterhout, "In Search of an Understandable Consensus
   Algorithm," Proceedings of the 2014 USENIX Annual Technical Conference
   (USENIX ATC 2014),
   [https://raft.github.io/raft.pdf](https://raft.github.io/raft.pdf),
   verified 2026-08-02.
7. Leslie Lamport, Mike Massa, "Cheap Paxos," Proceedings of the 2004
   International Conference on Dependable Systems and Networks (DSN 2004),
   [https://lamport.azurewebsites.net/pubs/web-dsn-submission.pdf](https://lamport.azurewebsites.net/pubs/web-dsn-submission.pdf),
   verified 2026-08-02.
8. Leslie Lamport, "Fast Paxos," Distributed Computing, 2006,
   [https://www.microsoft.com/en-us/research/publication/fast-paxos/](https://www.microsoft.com/en-us/research/publication/fast-paxos/),
   verified 2026-08-18.
9. Iulian Moraru, David G. Andersen, Michael Kaminsky, "There Is More
   Consensus in Egalitarian Parliaments," Proceedings of the 24th ACM
   Symposium on Operating Systems Principles (SOSP 2013),
   [https://www.cs.cmu.edu/~dga/papers/epaxos-sosp2013.pdf](https://www.cs.cmu.edu/~dga/papers/epaxos-sosp2013.pdf),
   verified 2026-08-02.
10. DataStax, "How do I accomplish lightweight transactions with
    linearizable consistency?", Apache Cassandra 3.0 documentation,
    [https://docs.datastax.com/en/cassandra-oss/3.0/cassandra/dml/dmlLtwtTransactions.html](https://docs.datastax.com/en/cassandra-oss/3.0/cassandra/dml/dmlLtwtTransactions.html),
    verified 2026-08-02.
11. AxonOps, "Paxos v2 and Beyond. Lightweight Transactions (LWTs) in Apache
    Cassandra,"
    [https://axonops.com/blog/paxos-v2-and-lightweight-transactions/](https://axonops.com/blog/paxos-v2-and-lightweight-transactions/),
    verified 2026-08-02.

## Code

Each example implements single-decree Paxos in-process. A fixed group of five
acceptors, and two sequential proposal rounds run against the same group. The
first round (proposer 1, value "blue") completes both phases and gets a value
chosen. The second round (proposer 2, a strictly higher proposal number,
value "green") demonstrates the adoption rule from dimension 7. Because a
majority already accepted "blue" under a lower number, proposer 2's Prepare
phase discovers that accepted value and is required to re-propose "blue"
rather than its own "green," even though no acceptor has any special-cased
knowledge of round 1. This is Paxos's safety guarantee made visible. Two
different proposers, two different rounds, one value.

### TypeScript

```typescript
type ProposalID = { round: number; proposerId: number };

const ZERO: ProposalID = { round: 0, proposerId: 0 };

function isZero(p: ProposalID): boolean {
  return p.round === 0 && p.proposerId === 0;
}

function less(a: ProposalID, b: ProposalID): boolean {
  if (a.round !== b.round) return a.round < b.round;
  return a.proposerId < b.proposerId;
}

interface PrepareReply {
  ok: boolean;
  acceptedId: ProposalID;
  acceptedValue: string | null;
}

class Acceptor {
  promised: ProposalID = ZERO;
  acceptedId: ProposalID = ZERO;
  acceptedValue: string | null = null;

  constructor(public id: number) {}

  prepare(pid: ProposalID): PrepareReply {
    if (!isZero(this.promised) && less(pid, this.promised)) {
      return { ok: false, acceptedId: ZERO, acceptedValue: null };
    }
    this.promised = pid;
    return { ok: true, acceptedId: this.acceptedId, acceptedValue: this.acceptedValue };
  }

  accept(pid: ProposalID, value: string): boolean {
    if (!isZero(this.promised) && less(pid, this.promised)) {
      return false;
    }
    this.promised = pid;
    this.acceptedId = pid;
    this.acceptedValue = value;
    return true;
  }
}

function runSingleDecree(
  acceptors: Acceptor[],
  pid: ProposalID,
  proposedValue: string
): [string | null, boolean] {
  const quorum = Math.floor(acceptors.length / 2) + 1;

  const promises: PrepareReply[] = [];
  for (const a of acceptors) {
    const r = a.prepare(pid);
    if (r.ok) promises.push(r);
  }
  if (promises.length < quorum) return [null, false];

  // Adopt the highest already-accepted value in the quorum, per P2c.
  let value = proposedValue;
  let best: ProposalID = ZERO;
  for (const r of promises) {
    if (r.acceptedValue !== null && less(best, r.acceptedId)) {
      best = r.acceptedId;
      value = r.acceptedValue;
    }
  }

  let accepted = 0;
  for (const a of acceptors) {
    if (a.accept(pid, value)) accepted++;
  }
  if (accepted < quorum) return [null, false];
  return [value, true];
}

function main() {
  const acceptors = [1, 2, 3, 4, 5].map((id) => new Acceptor(id));

  const [v1, ok1] = runSingleDecree(acceptors, { round: 1, proposerId: 1 }, "blue");
  console.log(`round 1 chosen=${ok1} value=${JSON.stringify(v1)}`);

  const [v2, ok2] = runSingleDecree(acceptors, { round: 2, proposerId: 2 }, "green");
  console.log(`round 2 chosen=${ok2} value=${JSON.stringify(v2)}`);

  if (v1 !== v2) {
    throw new Error("safety violated. two different values chosen");
  }
  console.log("safety held, single value across both rounds:", v2);
}

main();
```

Verified by compiling with `npx tsc paxos.ts --target es2020 --module commonjs
--strict` (TypeScript 7.0.2) and running the resulting `paxos.js` under Node.
Output.

```
round 1 chosen=true value="blue"
round 2 chosen=true value="blue"
safety held, single value across both rounds: blue
```

### Python

```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass(order=True, frozen=True)
class ProposalID:
    round: int
    proposer_id: int

    def is_zero(self) -> bool:
        return self.round == 0 and self.proposer_id == 0


ZERO = ProposalID(0, 0)


@dataclass
class Acceptor:
    id: int
    promised: ProposalID = field(default_factory=lambda: ZERO)
    accepted_id: ProposalID = field(default_factory=lambda: ZERO)
    accepted_value: Optional[str] = None

    def prepare(self, pid: ProposalID):
        if not self.promised.is_zero() and pid < self.promised:
            return None
        self.promised = pid
        return (self.accepted_id, self.accepted_value)

    def accept(self, pid: ProposalID, value: str) -> bool:
        if not self.promised.is_zero() and pid < self.promised:
            return False
        self.promised = pid
        self.accepted_id = pid
        self.accepted_value = value
        return True


def run_single_decree(acceptors, pid: ProposalID, proposed_value: str):
    quorum = len(acceptors) // 2 + 1

    promises = []
    for a in acceptors:
        r = a.prepare(pid)
        if r is not None:
            promises.append(r)
    if len(promises) < quorum:
        return None, False

    # Adopt the highest already-accepted value in the quorum, per P2c.
    value = proposed_value
    best = ZERO
    for accepted_id, accepted_value in promises:
        if accepted_value is not None and best < accepted_id:
            best = accepted_id
            value = accepted_value

    accepted = sum(1 for a in acceptors if a.accept(pid, value))
    if accepted < quorum:
        return None, False
    return value, True


def main():
    acceptors = [Acceptor(id=i) for i in range(1, 6)]

    v1, ok1 = run_single_decree(acceptors, ProposalID(1, 1), "blue")
    print(f"round 1 chosen={ok1} value={v1!r}")

    v2, ok2 = run_single_decree(acceptors, ProposalID(2, 2), "green")
    print(f"round 2 chosen={ok2} value={v2!r}")

    assert v1 == v2, "safety violated. two different values chosen"
    print("safety held, single value across both rounds:", v2)


if __name__ == "__main__":
    main()
```

Verified with `python3 paxos.py` (Python 3.14.6). Output.

```
round 1 chosen=True value='blue'
round 2 chosen=True value='blue'
safety held, single value across both rounds: blue
```

### Go

```go
package main

import "fmt"

// ProposalID orders proposals. Round is bumped on every retry, ProposerID
// breaks ties so no two proposers ever produce the same ID.
type ProposalID struct {
	Round      int
	ProposerID int
}

func (a ProposalID) Less(b ProposalID) bool {
	if a.Round != b.Round {
		return a.Round < b.Round
	}
	return a.ProposerID < b.ProposerID
}

func (a ProposalID) Zero() bool { return a.Round == 0 && a.ProposerID == 0 }

// Acceptor holds the two durable fields Paxos requires. the highest
// proposal it has promised not to ignore, and the highest proposal it has
// actually accepted, if any.
type Acceptor struct {
	ID            int
	Promised      ProposalID
	AcceptedID    ProposalID
	AcceptedValue string
	hasAccepted   bool
}

type PrepareReply struct {
	OK            bool
	AcceptedID    ProposalID
	AcceptedValue string
	HasAccepted   bool
}

// Prepare implements Paxos phase 1b. It never inspects the proposed value,
// only the proposal number, and it never forgets a promise once made.
func (a *Acceptor) Prepare(id ProposalID) PrepareReply {
	if !a.Promised.Zero() && id.Less(a.Promised) {
		return PrepareReply{OK: false}
	}
	a.Promised = id
	return PrepareReply{OK: true, AcceptedID: a.AcceptedID, AcceptedValue: a.AcceptedValue, HasAccepted: a.hasAccepted}
}

// Accept implements Paxos phase 2b. An acceptor accepts a value only if no
// higher-numbered proposal has since claimed the same slot.
func (a *Acceptor) Accept(id ProposalID, value string) bool {
	if !a.Promised.Zero() && id.Less(a.Promised) {
		return false
	}
	a.Promised = id
	a.AcceptedID = id
	a.AcceptedValue = value
	a.hasAccepted = true
	return true
}

// RunSingleDecree drives one proposer through phase 1 and phase 2 against a
// fixed acceptor set, returning the value that was actually chosen (which
// may differ from proposedValue if a prior round already picked one).
func RunSingleDecree(acceptors []*Acceptor, id ProposalID, proposedValue string) (string, bool) {
	quorum := len(acceptors)/2 + 1
	replies := []PrepareReply{}
	for _, a := range acceptors {
		r := a.Prepare(id)
		if r.OK {
			replies = append(replies, r)
		}
	}
	if len(replies) < quorum {
		return "", false
	}

	// Adopt the highest already-accepted value in the quorum, per P2c.
	value := proposedValue
	best := ProposalID{}
	for _, r := range replies {
		if r.HasAccepted && best.Less(r.AcceptedID) {
			best = r.AcceptedID
			value = r.AcceptedValue
		}
	}

	accepted := 0
	for _, a := range acceptors {
		if a.Accept(id, value) {
			accepted++
		}
	}
	if accepted < quorum {
		return "", false
	}
	return value, true
}

func main() {
	acceptors := []*Acceptor{{ID: 1}, {ID: 2}, {ID: 3}, {ID: 4}, {ID: 5}}

	v1, ok1 := RunSingleDecree(acceptors, ProposalID{Round: 1, ProposerID: 1}, "blue")
	fmt.Printf("round 1 chosen=%v value=%q\n", ok1, v1)

	v2, ok2 := RunSingleDecree(acceptors, ProposalID{Round: 2, ProposerID: 2}, "green")
	fmt.Printf("round 2 chosen=%v value=%q\n", ok2, v2)

	if v1 != v2 {
		panic("safety violated. two different values chosen")
	}
	fmt.Println("safety held, single value across both rounds:", v2)
}
```

Verified with `go run paxos.go` (go1.26.4 darwin/arm64). Output.

```
round 1 chosen=true value="blue"
round 2 chosen=true value="blue"
safety held, single value across both rounds: blue
```

Java, Rust, and Swift are omitted from this entry, not because Paxos does not
translate to them (it translates cleanly, the state machine is language
agnostic), but because three languages already demonstrate the pattern's
structure and the marginal value of a fourth near-identical acceptor/proposer
implementation is low relative to its length cost in this entry.
