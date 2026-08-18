---
name: Three-Phase Commit
slug: three-phase-commit
family: 12-data-storage
category: Data and Storage
aliases: [3PC, Nonblocking Commit Protocol, Quorum-Based Commit Protocol]
first_described: "Skeen 1981, extended by Skeen and Stonebraker 1983"
maturity: established
related: [saga, outbox-pattern, event-sourcing, write-ahead-log, consistent-hashing]
incompatible_with: []
verified: 2026-08-02
---

# Three-Phase Commit

## 1. Name, aliases, and lineage

The canonical name is Three-Phase Commit, almost always abbreviated 3PC. The
protocol originates with Dale Skeen's paper "Nonblocking Commit Protocols,"
presented at the 1981 ACM SIGMOD International Conference on Management of
Data, pages 133 to 142 (https://dl.acm.org/doi/pdf/10.1145/582318.582339, verified
2026-08-02). That paper derives the necessary and sufficient condition for a
commit protocol to avoid blocking on a single site failure, and shows that
the standard Two-Phase Commit protocol cannot meet it because it has only one
uncertainty-free state to recover into. Skeen followed with a Cornell
University technical report describing a concrete quorum-based construction,
titled "A Quorum-Based Commit Protocol," February 1982, which is the version
most later texts summarize when they draw the three phases as CanCommit,
PreCommit, and DoCommit. The theoretical foundation was tightened the
following year in Dale Skeen and Michael Stonebraker, "A Formal Model of
Crash Recovery in a Distributed System," IEEE Transactions on Software
Engineering, volume SE-9, 1983, pages 219 to 228, DOI 10.1109/TSE.1983.236608
(verified 2026-08-02). That paper proves resilience results for site
failures on a network that does not partition, then separately for a network
that does partition, and it is the paper that shows the classical protocol
cannot be made resilient to a NETWORK PARTITION even though it can be made
resilient to independent site crashes.

The alias Nonblocking Commit Protocol is Skeen's own term from the 1981
title and is the name under which the idea is indexed in most distributed
systems bibliographies. Quorum-Based Commit Protocol is the alias tied to
the 1982 technical report specifically, because that version replaces a
single coordinator decision with a quorum vote so that a live majority can
terminate a transaction without waiting for a coordinator to recover. A
later refinement, Extended Three-Phase Commit or E3PC, closes a remaining
gap in the quorum-based version and is documented in Idit Keidar and Danny
Dolev, "Increasing the Resilience of Distributed and Replicated Database
Systems," Journal of Computer and System Sciences, volume 57, issue 3, 1998,
pages 309 to 324 (DOI 10.1006/jcss.1998.1566, https://doi.org/10.1006/jcss.1998.1566,
verified 2026-08-18, resolved via Crossref metadata confirming title, authors,
volume, issue, and page range). E3PC is described there as always allowing a
connected quorum to make progress, closing the case in ordinary 3PC where a
quorum can become connected again after a cascading failure and still
remain blocked because no surviving participant retained enough state to
decide safely.

A naming trap worth flagging up front, because it causes real confusion in
production incident reviews. Some engineering blogs and consensus write-ups
use the phrase "three phases" to describe the three message rounds of
Practical Byzantine Fault Tolerance, PRE-PREPARE, PREPARE, and COMMIT. PBFT
is a Byzantine-fault-tolerant STATE MACHINE REPLICATION protocol solving
ordered agreement across possibly malicious nodes, and it shares nothing
with Skeen's Three-Phase Commit beyond the coincidence of a three-round
message pattern and the word commit appearing in one of the round names. See
dimension 13 for how the two are related, which is barely at all.

## 2. Problem and context

A coordinator has already run the first two rounds of the classical
Two-Phase Commit protocol. Every participant has voted yes and is now
sitting in the PREPARED state, which means it holds locks, has written its
redo and undo records, and cannot unilaterally decide to commit or abort
without risking disagreement with the rest of the group. The coordinator has
collected every vote and is about to send the final COMMIT, when the
coordinator crashes.

Every prepared participant is now stuck. A participant cannot commit,
because the coordinator might have decided to abort based on a vote the
participant never saw. A participant cannot abort, because the coordinator
might already have told a DIFFERENT participant to commit before crashing,
and unilaterally aborting here would split the transaction's outcome across
the group. The only correct move for a participant in this exact situation
under 2PC is to wait, indefinitely if necessary, holding every lock it holds,
until the coordinator recovers and tells it what happened. This is the
blocking problem, and it is a genuine operational failure mode, not a
theoretical curiosity. A coordinator process crash, a coordinator host
reboot for patching, or a coordinator-side network partition all produce it,
and the blocked locks on every prepared participant can freeze unrelated
transactions that queue behind them.

Three-Phase Commit exists to answer one narrow question honestly. Can a
distributed commit protocol be built so that NO SINGLE SITE FAILURE ever
forces a surviving, correctly-functioning participant to block indefinitely,
waiting on a site that might never come back? Skeen's 1981 result is that
the answer is yes, but only by adding a state between PREPARED and COMMITTED
that carries enough information for the surviving participants to agree on
an outcome among themselves, without needing the crashed site's testimony.
The context in which this problem is worth solving is narrower than it
looks. It is a data center or cluster network where message delays and
process pauses are BOUNDED, so that a timeout reliably distinguishes "the
coordinator is dead" from "the coordinator's message is merely late." That
assumption is also the pattern's most consequential limitation, covered in
full in dimensions 3, 4, and 11.

## 3. Forces

- **Blocking avoidance versus message and round-trip cost.** Favoured toward
  avoidance. 3PC adds one full round trip and one additional persisted state
  compared with 2PC specifically to buy the property that a live majority can
  always decide without the coordinator. The Wikipedia summary of the
  protocol, itself citing the underlying literature, states the message count
  rises to 5(n-1) against 4(n-1) for 2PC, and that the protocol needs a
  minimum of three round trips to complete
  (https://en.wikipedia.org/wiki/Three-phase_commit_protocol, verified 2026-08-02).
  On a transaction path that already sits inside a request's latency budget,
  that extra round trip is the price paid for every single commit, whether or
  not a failure ever occurs.
- **Synchrony assumption versus real network behaviour.** Sacrificed, and
  this is the pattern's defining weakness. The protocol's correctness proof
  depends on a synchronous system model, bounded message delay and bounded
  process response time, so that a timeout is a reliable failure detector.
  Wikipedia states this plainly, that in most practical systems with
  unbounded network delay and process pauses, three-phase commit cannot
  guarantee atomicity (https://en.wikipedia.org/wiki/Three-phase_commit_protocol,
  verified 2026-08-02). A real wide-area network, and even a real data-center
  network under load, does not bound delay tightly enough for the assumption
  to hold without a large safety margin, and a large safety margin turns the
  "nonblocking" property into a slow one.
- **Partition tolerance versus consistency.** Sacrificed for the classical
  version, this is the second defining weakness. If the network partitions
  during the PreCommit phase, participants on one side of the partition can
  time out and independently decide to commit, while participants on the
  other side, having not yet received the PreCommit message, time out and
  independently decide to abort. Both decisions are individually "correct"
  given what each side observed, and the transaction ends in permanent,
  irreconcilable disagreement across the partition. This is the failure mode
  that keeps 3PC out of systems that must survive a genuine network split,
  and it is why the Extended Three-Phase Commit variant exists at all
  (Keidar and Dolev, Journal of Computer and System Sciences, volume 57,
  1998, pages 309 to 324, verified 2026-08-02).
- **Operational simplicity versus recovery correctness.** Sacrificed.
  Recovering a crashed coordinator or a crashed participant correctly under
  3PC requires an election protocol among the survivors and a termination
  rule that reads every survivor's last-known state before deciding, which
  is materially more code, more edge cases, and more testing surface than
  the comparatively simple 2PC recovery rule of reading the coordinator's log.
- **Latency versus availability of the decision.** The protocol favours
  eventual availability of a decision, in the bounded-delay model, over
  minimum latency. A system that can tolerate the coordinator being briefly
  unreachable, and that values every participant staying unblocked over that
  window, is trading latency for that guarantee on the happy path too,
  because the extra phase runs on every commit, not only on the ones that
  hit a failure.
- **Team and operational cost versus tolerating blocking as the
  alternative.** In practice most production teams judge, and the
  engineering record bears this out (see dimension 9), that a bounded
  blocking window under 2PC, combined with monitoring, timeouts, and a
  human or automated recovery procedure, costs less in engineering effort
  and incident surface than building, testing, and operating a protocol
  whose safety property quietly disappears the moment the network does
  something 2PC's designers never had to reason about.

## 4. Applicability and non-applicability

Reach for Three-Phase Commit, or more realistically for the design GOAL it
represents, when all of the following hold together.

- The system runs inside a single data center or a tightly bounded cluster
  network where message delay and process pause time genuinely have a known,
  enforceable upper bound, so the synchrony assumption is not fiction.
- The network is known, by design and by monitoring history, not to
  partition in ways that split a functioning quorum from another functioning
  quorum, or the system can tolerate the rare case where that happens by
  favouring one side and reconciling manually afterward.
- The number of participants is small, because the extra round trip and the
  quorum-recovery logic both scale in cost with the number of sites that must
  agree.
- A coordinator or participant outage that FREEZES OTHER, UNRELATED work
  waiting on the same locks is judged to be worse, for this specific system,
  than the extra latency and code complexity of the third phase.
- The team is building or already operating the commit layer itself, such as
  a distributed database engine, a replicated state machine, or middleware
  that other applications sit on top of, rather than building an application
  that could instead avoid distributed transactions altogether.

Do NOT reach for classical Three-Phase Commit in the following cases, and the
reason is the point, not the rule.

- **The system spans a wide-area network, multiple cloud regions, or the
  public internet.** Unbounded delay is the normal case there, not the
  exception, and the protocol's own correctness proof requires bounded
  delay. Reaching for 3PC here produces code that LOOKS like it handles
  failures correctly and does not, which is worse than code that admits it
  blocks.
- **The network can genuinely partition and both halves must keep making
  progress.** Classical 3PC resolves this by having each half independently
  decide, which produces divergent outcomes, exactly the correctness failure
  the protocol was built to avoid in the single-failure case. Reach for a
  consensus-based replicated log, Raft or Multi-Paxos, or for Extended
  Three-Phase Commit specifically, or restructure the problem so that
  quorum loss means unavailability rather than a wrong answer.
- **The transaction crosses an organizational or trust boundary.** 3PC
  assumes every participant is a correctly-functioning, non-adversarial
  process that simply might crash or pause. It has no defense against a
  participant that lies about its vote or its state, which is exactly the
  situation the unrelated PBFT family exists to handle (see dimension 13).
- **The workload is a long-running, multi-step business process spanning
  minutes, hours, or days, such as an order fulfillment flow touching
  inventory, payment, and shipping services owned by different teams.**
  Holding locks and votes open across that span, even briefly per hop, is
  the wrong shape. The Saga pattern, which commits each local step
  independently and defines a compensating action for rollback, is built for
  exactly this case and does not require every participant to block on
  anyone else. See dimension 13.
- **A consensus algorithm is already in the stack for a different reason.**
  If the system already runs Raft or Paxos for leader election or log
  replication, building 3PC on top adds an entirely separate failure model
  and recovery protocol to reason about, when the existing consensus layer
  can usually express the same commit decision as one more entry in the
  already-replicated log.
- **The team cannot commit to building and testing the recovery and election
  logic.** A 3PC implementation that only implements the happy path and the
  single-crash path, without the multi-failure quorum-recovery rule, is not
  3PC. It is 2PC with one extra network round trip and none of the
  nonblocking guarantee, which is strictly worse than 2PC on every axis.

## 5. Structure

- **Coordinator.** The process driving the transaction. Sends CanCommit,
  collects Yes and No votes, sends PreCommit once every vote is Yes,
  collects ACKs, then sends DoCommit. In the quorum-based version the
  coordinator's crash does not stop termination, because a backup
  coordinator, elected among the surviving participants, can take over
  using state the participants already hold.
- **Participant, also called cohort or resource manager.** Each site
  holding a piece of the transaction's work. Moves through the states
  INITIAL, then PREPARED on voting Yes, then PRECOMMITTED on receiving
  PreCommit and ACKing it, then COMMITTED on receiving DoCommit. A
  participant that votes No, or that times out waiting for PreCommit, moves
  to ABORTED instead.
- **The PreCommit message and the PRECOMMITTED state.** This is the
  structural addition over 2PC and the entire reason the protocol works. A
  participant reaching PRECOMMITTED has proof, in the form of that message,
  that EVERY participant voted Yes. That single fact is what lets a
  surviving quorum decide to commit on its own if the coordinator vanishes
  after this point, because no participant that never received PreCommit
  could possibly have committed either, so aborting on that side can never
  contradict a commit that already happened on the other.
- **Timeout and election subsystem.** Present in any real implementation
  though absent from the simplified textbook diagram. Each participant runs
  a timer at every wait state. On timeout, participants that can still reach
  each other run a leader-election round to pick a new coordinator, then that
  new coordinator queries every reachable participant's state and applies
  the termination rule from dimension 7 to decide commit or abort.
- **Persistent log.** Every participant, and the coordinator, force-write
  each state transition to durable storage before sending the corresponding
  message, exactly as in 2PC, so that a crash-and-restart recovers into the
  correct state rather than losing the vote or the PreCommit acknowledgment.

## 6. ASCII structure diagram

```
                       +---------------------+
                       |     Coordinator     |
                       |----------------------|
                       | log. decision state  |
                       | quorum size. Q        |
                       +-----------+----------+
                                   |
              CanCommit / PreCommit / DoCommit
                    (broadcast to all)
                                   |
        +--------------------------+--------------------------+
        |                          |                          |
        v                          v                          v
+---------------+          +---------------+          +---------------+
| Participant A |          | Participant B |          | Participant C |
|---------------|          |---------------|          |---------------|
| state.        |          | state.        |          | state.        |
|  INITIAL      |          |  INITIAL      |          |  INITIAL      |
|  -> PREPARED  |  Yes/No  |  -> PREPARED  |  Yes/No  |  -> PREPARED  |
|  -> PRECOMMIT |   ACK    |  -> PRECOMMIT |   ACK    |  -> PRECOMMIT |
|  -> COMMITTED |          |  -> COMMITTED |          |  -> COMMITTED |
+---------------+          +---------------+          +---------------+
        ^                          ^                          ^
        |                          |                          |
        +----------- election + state exchange ----------------+
             (runs only if the coordinator is unreachable
              past a participant's timeout at any wait state)
```

## 7. Dynamics

The happy path runs three rounds, each gated on every participant
responding before the coordinator advances.

```
Coordinator                Participant A         Participant B
    |                            |                     |
    |-- CanCommit? ------------->|-- CanCommit? ------>|
    |                            |                     |
    |<-- Yes (log. PREPARED) ----|<-- Yes (log. PREPARED)
    |                            |                     |
    |  (all votes Yes, so...)    |                     |
    |-- PreCommit -------------->|-- PreCommit -------->|
    |                            |                     |
    |<-- ACK (log. PRECOMMIT) ---|<-- ACK (log. PRECOMMIT)
    |                            |                     |
    |-- DoCommit ---------------->|-- DoCommit --------->|
    |                            |                     |
    |<-- ACK (log. COMMITTED) ---|<-- ACK (log. COMMITTED)
    |                            |                     |
```

The termination protocol is what runs when the coordinator disappears after
some participants reach PRECOMMITTED, and it is the part every simplified
explanation skips.

```
Coordinator crashes after PreCommit reaches A but before it reaches B.
A is PRECOMMITTED. B is still PREPARED and has timed out.

    Participant A               Participant B          (election, A wins)
         |                           |
         |-- elect new coordinator ->|
         |                           |
         |<---- state query ---------|
         |-- "I am PRECOMMITTED" --->|
         |                           |
   (rule. if ANY reachable participant is PRECOMMITTED,
    the new coordinator MUST decide commit, because that
    fact proves every participant voted Yes)
         |                           |
         |-- DoCommit --------------->|
         |<-- ACK (log. COMMITTED) --|

If instead every reachable participant were still only PREPARED,
and none had reached PRECOMMITTED, the rule flips. the new
coordinator decides ABORT, because a PreCommit could not yet
have been sent to anyone, prepared or otherwise.
```

The rule made explicit above, commit if any survivor is PRECOMMITTED,
otherwise abort, is the actual mechanism that avoids blocking. It also
exposes exactly why a network PARTITION breaks the guarantee. If the
partition splits the PRECOMMITTED participants from the merely-PREPARED
ones, each side applies the rule correctly against the information it can
see, and the two sides reach opposite, permanent decisions.

## 8. Implementation variants

**Centralized 3PC, Skeen 1981, the textbook version.** A single
coordinator drives all three phases; on coordinator failure, participants
run a simple timeout-and-elect step and the new coordinator applies the
termination rule from dimension 7 directly. Simplest to implement, weakest
under multiple concurrent failures, and the version most tutorials draw.

**Quorum-based 3PC, Skeen's 1982 Cornell technical report.** Decisions are
made and recorded by a QUORUM of participants rather than requiring every
site to agree, so the protocol can make progress and terminate correctly
even while some sites remain unreachable, as long as a quorum is reachable.
This is the version that scales to more realistic cluster sizes because it
does not require every single site to be alive to terminate.

**Extended Three-Phase Commit, E3PC, Keidar and Dolev 1998.** Adds eager
state propagation. participants proactively gossip their local state to
other reachable participants as soon as they learn it, rather than only on
demand during an election. This closes the specific gap where a quorum that
was lost during a cascading failure later reconnects but still cannot
recover a decision, because the reconnected participants now already hold
enough gossiped state to reconstruct the outcome without a fresh, more
expensive information round. Keidar and Dolev report that E3PC achieves this
without requiring more time or communication than ordinary 3PC in the
common case (Journal of Computer and System Sciences, volume 57, 1998,
pages 309 to 324, verified 2026-08-02).

**Presumed-commit and presumed-abort style optimizations.** Borrowed from
the 2PC optimization literature and applicable to 3PC's message counts too.
a participant that has not heard from the coordinator in a long time and
finds no log record can safely assume a specific default outcome, commit or
abort, chosen per deployment, without a round trip, trading a small risk of
an unnecessary compensating action for fewer messages on the common path.

**In-process simulation for teaching and testing.** Because a genuinely
distributed 3PC deployment needs several real, independently-crashable
processes to demonstrate its actual value, most codebases that reference the
pattern in tests or documentation implement a single-process simulation.
one coordinator object and several participant objects exchanging method
calls instead of network messages, with an injectable fault so a test can
force the coordinator to "crash" mid-protocol and assert the participants
still terminate correctly. This is the shape the code examples in this
entry use, and it is an honest simplification as long as it is labelled as
one, since a real network round trip is not a method call.

## 9. Known production uses

This dimension needs an honest correction before naming anything, because
the honest answer is unusual for a catalog entry. after a genuine search of
the primary literature, engineering blog record, and distributed-systems
textbook consensus, no widely-documented mainstream production database,
message broker, or distributed transaction coordinator implements the
CLASSICAL Skeen-style Three-Phase Commit protocol as its live commit path
today. This absence is itself a sourced, well-established fact, not an
unsupported claim.

- The English Wikipedia entry on the protocol states plainly that the
  protocol assumes a network with bounded delay and nodes with bounded
  response times, and that in most practical systems with unbounded network
  delay and process pauses, it cannot guarantee atomicity
  (https://en.wikipedia.org/wiki/Three-phase_commit_protocol, verified 2026-08-02).
  That is precisely the assumption real data-center and wide-area networks
  do not satisfy, and it is the reason engineering teams cite for not
  choosing it.
- Mainstream production distributed relational systems that DO need atomic
  commit across nodes overwhelmingly use Two-Phase Commit or a variant of
  it instead. PostgreSQL's Foreign Data Wrapper framework and MySQL's XA
  transaction support both implement two-phase commit, not three-phase
  commit, for exactly this reason, a fact independently corroborated across
  the survey material used for this entry's research, verified 2026-08-02
  against the live vendor documentation for each, the `postgres_fdw` and
  `dblink` two-phase commit documentation at https://www.postgresql.org and
  the XA Transactions manual page at https://dev.mysql.com.
- CockroachDB, a distributed SQL database built specifically to survive
  multi-region deployment and network partitions, documents choosing
  Two-Phase Commit as its baseline atomic-commit protocol and then
  optimizing it with a technique called Parallel Commits, which removes one
  of 2PC's two sequential consensus rounds rather than adding a third
  round. The engineering write-up explains the choice in terms of the
  latency cost of extra consensus rounds, the same cost 3PC pays by
  construction (https://cockroachlabs.com/blog/parallel-commits/, verified
  2026-08-02). The blog post does not name three-phase commit directly as a
  rejected alternative, so this entry cites it only for the documented fact
  that CockroachDB's chosen and shipped protocol is a 2PC derivative, not a
  3PC derivative, which is the closest sourced, checkable evidence available
  of how a modern distributed database actually decided this trade-off.

Where the classical protocol's descendants genuinely were built and
evaluated is in the research literature rather than in a shipped commercial
product. Skeen's own 1982 Cornell technical report describes and evaluates a
working quorum-based implementation as a research prototype, and Keidar and
Dolev's Extended Three-Phase Commit (Journal of Computer and System
Sciences, volume 57, 1998, pages 309 to 324, verified 2026-08-02) is
likewise presented and analyzed as an academic protocol with a formal
resilience proof, not as a component shipped inside a named commercial
system this author could independently verify. Presenting either of those
as a "production use" in the sense the rest of this catalog uses the phrase
would overstate what is actually documented, so this entry states the
absence directly instead of inventing a third example. A reader building a
system today who needs the property 3PC promises should read dimension 4's
non-applicability list and dimension 13's related patterns before assuming
3PC itself is the tool to reach for. in practice, the property is obtained
instead through a consensus-replicated commit log, Raft or Multi-Paxos,
layered under a 2PC-shaped commit, which several modern distributed
databases, including CockroachDB and Google Cloud Spanner as described in
their own public engineering literature, do use in production.

## 10. Consequences

Positive.

- No single site failure, coordinator or participant, forces a surviving,
  correctly-functioning site to block indefinitely, which is the entire
  reason the protocol exists and the specific guarantee 2PC lacks.
- The termination rule is DERIVED, not assumed. a surviving quorum can prove
  from the PRECOMMITTED state alone whether every participant voted Yes,
  without needing to contact the crashed coordinator, which is a genuinely
  clever use of an intermediate durable state to encode information that
  would otherwise only exist inside the coordinator's head.
- The protocol composes cleanly with existing 2PC infrastructure at the
  participant level. a participant implementing 3PC still needs the same
  redo, undo, and vote logging it would need for 2PC, plus one additional
  state and message pair.
- The formal analysis behind it, Skeen and Stonebraker 1983, is precise
  about exactly what failure classes it does and does not tolerate, which
  makes it a genuinely useful reference model for reasoning about ANY commit
  protocol's failure envelope, even when the protocol itself is not adopted.

Negative.

- The protocol's core correctness guarantee depends on a synchronous system
  model that most production networks do not satisfy, so a naive
  implementation can silently violate atomicity under exactly the conditions
  it was built to survive, network delay and process pauses.
- It does not tolerate a genuine network partition, and can produce
  divergent, unrecoverable commit decisions on the two sides of one, which
  is a worse failure than 2PC's blocking, because blocking is at least safe
  and merely slow.
- It costs one additional network round trip and one additional persisted
  state on every single transaction, whether or not a failure ever happens,
  which is a real latency and durability tax paid continuously for a
  guarantee that only matters during the rare failure case.
- The termination and election logic needed for a CORRECT implementation is
  substantially more complex than the happy-path diagram suggests, and an
  implementation that skips it is not actually 3PC, it is 2PC with extra
  latency.
- Because production teams have overwhelmingly chosen not to build or
  operate it, an engineer implementing it today has very little
  battle-tested open-source reference code to learn from, compared with the
  abundant, mature 2PC and consensus-log implementations available.

## 11. Failure modes and misuse

**The partitioned split-brain commit.** Symptom. Two disjoint sets of
participants each independently and confidently report a final, opposite
outcome for the same transaction, discovered only when the partition heals
and reconciliation runs, sometimes hours or days later. Cause. A network
partition split PRECOMMITTED participants from merely-PREPARED participants
during the window between PreCommit and DoCommit, and each side correctly
applied the termination rule to the state it could observe. Fix. Do not
deploy classical 3PC across a link that can partition while leaving both
sides able to reach a local quorum. Use Extended Three-Phase Commit, which
is specifically designed to avoid this case, or move to a consensus-log
based commit where a partitioned minority simply cannot make progress at all
instead of making a divergent one.

**The unbounded-timeout illusion.** Symptom. In load testing or during a
garbage-collection pause, a participant's timeout fires and it begins the
election protocol even though the coordinator was, in fact, still alive and
about to send DoCommit a moment later. Two coordinators now believe they are
authoritative for the same transaction. Cause. The synchrony assumption was
violated by a process pause, exactly the scenario Wikipedia's summary of the
protocol's bounded-delay requirement warns about
(https://en.wikipedia.org/wiki/Three-phase_commit_protocol, verified 2026-08-02).
Fix. Set timeouts with a wide, empirically measured safety margin above the
observed ninety-ninth percentile of coordinator response time including GC
pause and OS scheduling jitter, and treat any timeout-triggered election as
an event requiring a fencing mechanism, such as an epoch or term number, so
a late message from the old coordinator can never be mistaken for current.

**Three-phase commit that is actually two-phase commit with a redundant
phase.** Symptom. Code review finds a coordinator sending three message
rounds, but the recovery path on coordinator crash is identical to plain
2PC's. participants simply wait for the coordinator to come back. Cause.
The implementation added the PreCommit message and state without adding the
election and termination logic that gives the extra phase any meaning. Fix.
Either implement the election and quorum-decision logic from dimension 7 in
full, or drop the third phase entirely and accept 2PC's blocking, because
the half-built version pays 3PC's latency cost while delivering 2PC's
failure behaviour.

**Election storms under repeated partial failure.** Symptom. CPU and
network usage on the participant set spikes and stays high, transaction
latency degrades further, and logs show repeated coordinator-election
rounds firing in quick succession. Cause. A flapping network link or a
repeatedly restarting coordinator process causes participants to time out,
elect, partially terminate, and then have the coordinator come back before
the next transaction, over and over. Fix. Add a minimum backoff before a
participant is eligible to initiate election again, and alert on election
frequency as a first-class operational signal rather than only on
transaction failure rate.

**Quorum miscalculation after a topology change.** Symptom. A cluster that
recently added or removed nodes experiences a transaction that neither
commits nor aborts within any reasonable time, and manual inspection shows
no single quorum of the CURRENT membership was ever queried. Cause. The
quorum size used by the election and termination logic was computed against
a stale membership list, so "a majority of the group" no longer means what
the algorithm assumes it means. Fix. Tie quorum computation to the same
membership-change protocol the rest of the cluster uses, and require an
explicit reconfiguration step, itself agreed by the old quorum, before any
new quorum size takes effect.

## 12. Trade-off matrix

Compared against named alternatives that solve the same or an adjacent
problem, across the forces from dimension 3.

| Force | Three-Phase Commit | Two-Phase Commit | Paxos / Raft replicated commit log | Saga (compensating transactions) |
|---|---|---|---|---|
| Blocks on coordinator crash | No, if fully implemented with election | Yes, until coordinator recovers | No, a new leader is elected and continues | Not applicable, each step commits locally and independently |
| Tolerates a genuine network partition safely | No, classical version can split-brain | Degrades to blocking, but stays safe | Yes, minority side simply cannot make progress | Yes, each participant only needs its own availability |
| Message rounds on the happy path | Three | Two | One to two, depending on batching | One per step, no cross-service round trip required |
| Recovery complexity | High, needs election plus termination rule | Low, wait for coordinator | Moderate, but usually already built into the platform | Low per step, but requires designing every compensating action |
| All-or-nothing atomicity across participants | Yes, in the bounded-delay model | Yes | Yes, for entries the log actually orders | No, intermediate states are visible and must be tolerated |
| Suited to long-running, cross-team business processes | No, holds locks across the whole protocol | No | No, typically used for short log entries | Yes, this is its primary purpose |
| Production maturity and available implementations | Low, mostly academic and research code | High, decades of production databases | High, widely implemented and operated | High in application and workflow-engine code |

Reading of the table. 3PC and 2PC solve the same narrow problem, atomic
commit across a small, trusted, low-latency-network group of participants,
and 3PC only wins on the single axis of not blocking a live participant on a
coordinator crash, at the cost of every other axis in the table.
Paxos-and-Raft-based commit logs solve a broader version of the same problem
and, because they are built to survive partitions from the start rather than
assume them away, have displaced both 2PC and 3PC as the underlying
mechanism in most new distributed database designs. Saga solves a different
problem entirely, business processes that are too long-lived to hold
cross-service locks at all, and should not be read as a drop-in replacement
for 3PC so much as evidence that many systems reaching for a commit protocol
should first ask whether they need cross-service atomicity in the first
place.

## 13. Related and incompatible patterns

- **Two-Phase Commit.** The direct ancestor and the protocol 3PC extends by
  one phase. Every participant-side state 2PC needs, INITIAL, PREPARED,
  plus its logging discipline, is reused unchanged. 3PC only inserts
  PRECOMMITTED between PREPARED and COMMITTED. Understanding 2PC's blocking
  failure is the prerequisite for understanding why 3PC's extra phase exists
  at all.
- **Paxos and Raft.** Composes as the modern replacement rather than a
  sibling. A replicated commit log built on either algorithm can express
  the transaction commits as one more entry appended to an already-agreed,
  partition-aware log, which delivers the nonblocking property 3PC targets
  without inheriting 3PC's synchrony assumption. Most contemporary
  distributed databases that need atomic multi-node commit build it this
  way instead of implementing 3PC directly.
- **Saga.** A substitute for a different scope of problem. Where 3PC and 2PC
  hold every participant's locks open until a single atomic decision lands,
  Saga commits each local step immediately and defines a compensating action
  to undo it if a later step fails, trading strict atomicity for the ability
  to span long-running, cross-team processes without cross-service locking.
  A system choosing between them should ask whether the transaction genuinely
  needs all-or-nothing atomicity at a single point in time, which favours
  3PC or 2PC, or whether it can tolerate a temporarily visible intermediate
  state that gets compensated later, which favours Saga.
- **Write-Ahead Log.** A prerequisite, not an alternative. Every durable
  state transition in 3PC, PREPARED, PRECOMMITTED, COMMITTED, ABORTED, is
  only recoverable across a crash because it was force-written to a
  write-ahead log before the corresponding message was sent. 3PC's own
  correctness proof assumes this logging discipline exists.
- **Practical Byzantine Fault Tolerance, PBFT.** Frequently and wrongly
  conflated with 3PC because both are casually described as "three phase"
  protocols. PBFT's three message rounds, PRE-PREPARE, PREPARE, and COMMIT,
  solve ordered agreement among nodes that may behave arbitrarily or
  maliciously, a different problem, under a different fault model, with a
  different quorum size requirement, than Skeen's atomic commit protocol for
  crash-only failures. The shared word "commit" in one round name is the
  entire source of the confusion, and treating them as the same pattern is a
  category error.
- **Consistent Hashing.** Orthogonal. Consistent hashing decides WHICH nodes
  hold a given piece of data. 3PC decides how nodes that already hold
  related pieces of data agree on committing a change to them together. A
  system can use either without the other, and many systems that use
  consistent hashing for placement use a Saga or a 2PC derivative, not 3PC,
  for cross-node consistency when it is needed at all.

## 14. Refactoring path in and out

Introducing the design goal 3PC represents into a system currently running
plain 2PC and suffering from coordinator-crash blocking incidents. Ordered
steps.

1. Confirm the actual incident cause first. Measure how often a coordinator
   crash genuinely blocks live participants in production, and for how long.
   If the answer is rare and short, the fix may simply be faster coordinator
   restart and better monitoring, not a protocol change, given the real cost
   3PC adds on every transaction shown in dimensions 3 and 10.
2. If the blocking is a genuine, recurring operational problem, first
   evaluate whether the coordinator's role can be moved onto an already
   consensus-replicated log the platform runs for another reason, which
   usually delivers the nonblocking property more cheaply than building 3PC
   from scratch. This is the step most real systems stop at, per dimension 9.
3. Only if neither of those applies, and the deployment genuinely satisfies
   the bounded-delay, low-partition-risk context from dimension 4, add the
   PRECOMMITTED state and the PreCommit message pair to the existing 2PC
   participant state machine, reusing the same write-ahead log discipline
   already in place.
4. Implement the election protocol as a distinct, independently-testable
   component, because it is the part most likely to be skipped or built
   incorrectly, per the misuse case in dimension 11. Test it by injecting
   coordinator crashes at every possible point in the message sequence, not
   only the two or three obvious ones.
5. Implement the termination rule from dimension 7 exactly, verify it with a
   test that constructs the partition-split scenario deliberately and
   confirms the protocol's known limitation is at least detected and
   alerted on, since it cannot be eliminated in the classical version.
6. Roll out behind a feature flag that lets the old 2PC path run in parallel
   for a period, comparing decision outcomes, before removing the 2PC path.

Removing the pattern when the deployment context has changed, most often
because the system now spans multiple regions or a network the team no
longer controls tightly enough to trust the synchrony assumption.

1. Confirm the trigger. A move to multi-region deployment, an increase in
   participant count that makes election storms more likely, or a security
   or compliance requirement that the commit path must survive an actual
   network partition without risking a split decision, are the usual causes.
2. Introduce a consensus-replicated commit log alongside the existing 3PC
   path, and route new transactions through it while the 3PC path continues
   to drain in-flight work.
3. Once no transaction is mid-flight on the 3PC path, remove the
   PRECOMMITTED state, the PreCommit message, and the election and
   termination logic, collapsing the participant state machine back to
   whatever the new commit mechanism requires, which for a consensus log is
   usually simpler than either 2PC or 3PC's participant logic.
4. Delete the 3PC-specific tests and monitoring, but keep the partition
   incident postmortems that justified the change. they are the evidence a
   future engineer will need if someone proposes reintroducing 3PC later.

## 15. Testing and verification

Easier because of the pattern's explicit state machine.

- Every participant's behaviour is a pure function of its current state and
  the message it receives, so unit tests can drive the state machine
  directly with a table of state and message pairs mapped to a new state
  and outgoing message, without needing a real network at all.
- The termination rule from dimension 7 is a small, deterministic function
  of the states a newly-elected coordinator observes across the reachable
  participants, and it can be exhaustively tested against every combination
  of states a quorum could plausibly present.

Harder because of the pattern.

- The property the protocol exists to provide, that no live participant
  blocks forever, is a property about the ABSENCE of an outcome over
  unbounded time, which ordinary example-based tests cannot directly assert.
  it requires either a bounded-time liveness check with generous timeouts in
  a test rig, or a model-checking approach.
- The failure mode that actually matters most, the partition-split scenario
  from dimension 11, only manifests when TWO separate elections happen
  concurrently on two sides of an injected partition, which needs a test
  rig capable of genuinely partitioning simulated network links, not
  merely delaying or dropping individual messages.

Techniques that apply.

- **Deterministic simulation testing.** Run the entire protocol, coordinator
  and every participant, inside one process with a simulated clock and a
  simulated, controllable network, so a test can inject an exact crash at an
  exact message boundary and replay the same scenario deterministically when
  a bug is found. This is the standard technique the distributed systems
  community uses for exactly this class of protocol, because real
  multi-process, multi-machine test setups cannot reliably reproduce a
  specific interleaving.
- **Partition injection as a first-class test category, not an edge case.**
  Given dimension 11's split-brain failure mode is the protocol's known,
  accepted limitation rather than a bug to be fixed, the correct test is not
  an assertion that the protocol never split-brains, which would be
  asserting something false about the classical version. The correct test
  asserts that a partition scenario is DETECTED and surfaced to an operator
  or a reconciliation process, since eliminating it entirely requires the
  Extended Three-Phase Commit variant or a different protocol altogether.
- **Property-based state machine testing.** Generate random sequences of
  message deliveries, drops, and reorderings against the participant state
  machine and assert the invariant that no two participants ever reach
  COMMITTED and ABORTED for the same transaction unless a partition was
  present in the generated scenario, which turns dimension 11's known
  limitation into an explicit, checkable boundary condition instead of an
  implicit assumption.

## 16. Observability signals

Because the protocol's value is entirely about what happens during a
failure, and a healthy system spends almost all of its time never exercising
that path, observability has to specifically surface the RARE events, not
only the steady-state throughput.

What to record.

- A counter of transactions completing via the happy path, DoCommit received
  and acknowledged normally, labelled separately from transactions completing
  via the election and termination path.
- A counter and, ideally, a full trace of every ELECTION event, including
  which participant initiated it, the timeout that fired, and the states the
  new coordinator observed across the reachable quorum when it applied the
  termination rule.
- A gauge of participants currently sitting in the PREPARED or PRECOMMITTED
  state longer than the expected round-trip window, which is the direct
  signal that a block or a stuck coordinator is in progress.
- A dedicated alert-worthy event, not merely a log line, for any occurrence
  where the termination rule was applied against a quorum that did not
  represent every original participant, since this is the exact precondition
  under which the partition-split failure from dimension 11 becomes possible.
- Latency histograms for each phase separately, CanCommit-to-vote,
  PreCommit-to-ack, DoCommit-to-ack, so a regression in one specific phase
  localises to a specific message round rather than an undifferentiated
  commit-is-slow signal.

A healthy instance on a dashboard. The election counter is flat at or near
zero, transaction latency mostly reflects the three expected round trips
with a tight, predictable distribution, and the PREPARED and PRECOMMITTED
gauges never sit above the expected round-trip window.

A failing instance. The election counter climbs, which by itself is not
necessarily an atomicity violation but is always worth investigating, since
it means the synchrony assumption was violated at least once. A rising count
of terminations applied against a partial quorum is the leading indicator of
the partition-split failure mode before any application-level data
inconsistency is even discovered. A PREPARED or PRECOMMITTED gauge that
climbs and stays high on a specific participant, with no matching election
event, points at a participant that has stopped responding to the
coordinator without the coordinator's own timeout logic having noticed yet.

## 17. Security and privacy implications

The classical protocol assumes every participant is a correctly-functioning,
non-adversarial process within a single trust domain, and it has no defense
mechanism against a participant that lies about its vote, its state during
an election, or its identity. This is engineering judgement, not a sourced
claim from the original papers, which were written for single-organization
distributed database deployments where that assumption held by construction.
Three concrete implications follow from it.

**Trust boundary mismatch.** Deploying 3PC, or any variant of it, across a
trust boundary that includes a participant the operator does not fully
control is a direct security defect, because a compromised or malicious
participant can falsely claim to be PRECOMMITTED during an election,
forcing every surviving honest participant to commit a transaction that was
never actually agreed by the full original group. If a commit decision must
span organizations, the correct family of protocols is a Byzantine
fault-tolerant one, such as PBFT (see dimension 13), whose quorum sizes and
message rules are explicitly designed to tolerate a bounded number of lying
participants, not this pattern.

**Election-triggered denial of service.** Because a participant can
unilaterally initiate an election on a timeout, an attacker positioned to
delay or drop messages to a specific participant, without needing to
compromise any process outright, can repeatedly trigger the election storm
failure mode from dimension 11 as a denial-of-service technique against the
transaction throughput of the whole group. The mitigation named there,
backoff plus alerting on election frequency, is also the relevant security
control here, and should be paired with authenticating that election and
state-query messages genuinely originate from a legitimate member of the
current quorum.

**State disclosure during recovery.** The state-exchange step that runs
during election and termination necessarily reveals to every participating
site which OTHER sites had reached which state at the moment of failure,
which is metadata about the transaction's progress that would not otherwise
cross site boundaries on the happy path. Where the participants sit in
different regulatory or data-residency domains, this recovery-time metadata
exchange should be reviewed against the same data-handling rules that apply
to the transaction's actual payload, since it can leak, for example, that a
transaction touching a specific customer record was in flight at a specific
site at a specific time, even if the record's contents never cross that
boundary.

## Code examples

Three languages, each chosen for a different reason. Python shows the
protocol's state machine and termination rule in the clearest, least
ceremony-heavy form, and is the reference implementation the other two
match. TypeScript shows the same shape with explicit discriminated-union
states, which is a genuinely idiomatic way to represent a protocol state
machine in that language and catches an invalid transition at compile time.
Go shows the struct-and-method form, which is close to how a real
network-facing implementation in Go would actually be structured, using
plain function calls to stand in for the network. All three are in-process
simulations per the variant described in dimension 8, with an injectable
coordinator crash so each example can demonstrate the nonblocking
termination path, not only the happy path. Every sample was executed
locally. the transcript of each run is summarized in a trailing comment.

### Python

```python
from dataclasses import dataclass
from enum import Enum, auto


class State(Enum):
    INITIAL = auto()
    PREPARED = auto()
    PRECOMMIT = auto()
    COMMITTED = auto()
    ABORTED = auto()


@dataclass
class Participant:
    name: str
    vote_yes: bool = True
    state: State = State.INITIAL

    def on_can_commit(self) -> bool:
        self.state = State.PREPARED if self.vote_yes else State.ABORTED
        return self.vote_yes

    def on_pre_commit(self) -> None:
        self.state = State.PRECOMMIT

    def on_do_commit(self) -> None:
        self.state = State.COMMITTED

    def on_abort(self) -> None:
        self.state = State.ABORTED


def run_three_phase_commit(
    participants: list[Participant], coordinator_crashes_after: str | None = None
) -> str:
    votes = [p.on_can_commit() for p in participants]
    if not all(votes):
        for p in participants:
            if p.state != State.ABORTED:
                p.on_abort()
        return "ABORTED"

    for p in participants:
        p.on_pre_commit()
        if coordinator_crashes_after == p.name:
            # Coordinator dies right after telling this participant.
            return terminate_via_quorum(participants)

    for p in participants:
        p.on_do_commit()
    return "COMMITTED"


def terminate_via_quorum(participants: list[Participant]) -> str:
    # The termination rule from dimension 7. if any reachable participant
    # already reached PRECOMMIT, every vote was Yes, so the group commits.
    decision = (
        "COMMITTED"
        if any(p.state == State.PRECOMMIT for p in participants)
        else "ABORTED"
    )
    for p in participants:
        if decision == "COMMITTED":
            p.on_do_commit()
        else:
            p.on_abort()
    return decision


if __name__ == "__main__":
    happy = [Participant("A"), Participant("B"), Participant("C")]
    print("happy path", run_three_phase_commit(happy))

    crash = [Participant("A"), Participant("B"), Participant("C")]
    print(
        "coordinator crashes after A precommits",
        run_three_phase_commit(crash, coordinator_crashes_after="A"),
    )
    print("A state", crash[0].state, "B state", crash[1].state)
```

Run locally with `python3 three_phase_commit.py`. Output observed.

```
happy path COMMITTED
coordinator crashes after A precommits COMMITTED
A state State.COMMITTED B state State.COMMITTED
```

The second line shows the point of the pattern. B never received PreCommit
directly from the crashed coordinator, but B does not block forever either.
Because A already reached PRECOMMIT, the termination rule proves every vote
was Yes, so the surviving group resolves to COMMITTED and every reachable
participant, B included, is told to commit, all without ever hearing again
from the original coordinator.

### TypeScript

```typescript
type ParticipantState =
  | { kind: "initial" }
  | { kind: "prepared" }
  | { kind: "precommit" }
  | { kind: "committed" }
  | { kind: "aborted" };

class Participant {
  state: ParticipantState = { kind: "initial" };
  constructor(public name: string, private voteYes: boolean = true) {}

  onCanCommit(): boolean {
    this.state = this.voteYes ? { kind: "prepared" } : { kind: "aborted" };
    return this.voteYes;
  }

  onPreCommit(): void {
    this.state = { kind: "precommit" };
  }

  onDoCommit(): void {
    this.state = { kind: "committed" };
  }

  onAbort(): void {
    this.state = { kind: "aborted" };
  }
}

function terminateViaQuorum(participants: Participant[]): "COMMITTED" | "ABORTED" {
  const anyPreCommitted = participants.some((p) => p.state.kind === "precommit");
  const decision = anyPreCommitted ? "COMMITTED" : "ABORTED";
  for (const p of participants) {
    decision === "COMMITTED" ? p.onDoCommit() : p.onAbort();
  }
  return decision;
}

function runThreePhaseCommit(
  participants: Participant[],
  coordinatorCrashesAfter: string | null = null
): "COMMITTED" | "ABORTED" {
  const votes = participants.map((p) => p.onCanCommit());
  if (!votes.every(Boolean)) {
    for (const p of participants) {
      if (p.state.kind !== "aborted") p.onAbort();
    }
    return "ABORTED";
  }

  for (const p of participants) {
    p.onPreCommit();
    if (p.name === coordinatorCrashesAfter) {
      return terminateViaQuorum(participants);
    }
  }

  for (const p of participants) p.onDoCommit();
  return "COMMITTED";
}

const happy = [new Participant("A"), new Participant("B"), new Participant("C")];
console.log("happy path", runThreePhaseCommit(happy));

const crash = [new Participant("A"), new Participant("B"), new Participant("C")];
console.log(
  "coordinator crashes after A precommits",
  runThreePhaseCommit(crash, "A")
);
console.log("A state", crash[0].state.kind, "B state", crash[1].state.kind);
```

Compiled and run locally with `npx tsc --strict three_phase_commit.ts && node three_phase_commit.js`. Output observed.

```
happy path COMMITTED
coordinator crashes after A precommits COMMITTED
A state committed B state committed
```

Matches the Python run exactly, as it should, since both implement the same
termination rule.

### Go

```go
package main

import "fmt"

type State int

const (
	Initial State = iota
	Prepared
	PreCommit
	Committed
	Aborted
)

func (s State) String() string {
	return [...]string{"Initial", "Prepared", "PreCommit", "Committed", "Aborted"}[s]
}

type Participant struct {
	Name    string
	VoteYes bool
	State   State
}

func (p *Participant) OnCanCommit() bool {
	if p.VoteYes {
		p.State = Prepared
	} else {
		p.State = Aborted
	}
	return p.VoteYes
}

func (p *Participant) OnPreCommit() { p.State = PreCommit }
func (p *Participant) OnDoCommit()  { p.State = Committed }
func (p *Participant) OnAbort()     { p.State = Aborted }

func terminateViaQuorum(participants []*Participant) string {
	anyPreCommitted := false
	for _, p := range participants {
		if p.State == PreCommit {
			anyPreCommitted = true
			break
		}
	}
	decision := "ABORTED"
	if anyPreCommitted {
		decision = "COMMITTED"
	}
	for _, p := range participants {
		if decision == "COMMITTED" {
			p.OnDoCommit()
		} else {
			p.OnAbort()
		}
	}
	return decision
}

func runThreePhaseCommit(participants []*Participant, crashAfter string) string {
	allYes := true
	for _, p := range participants {
		if !p.OnCanCommit() {
			allYes = false
		}
	}
	if !allYes {
		for _, p := range participants {
			if p.State != Aborted {
				p.OnAbort()
			}
		}
		return "ABORTED"
	}

	for _, p := range participants {
		p.OnPreCommit()
		if p.Name == crashAfter {
			return terminateViaQuorum(participants)
		}
	}

	for _, p := range participants {
		p.OnDoCommit()
	}
	return "COMMITTED"
}

func main() {
	happy := []*Participant{{Name: "A", VoteYes: true}, {Name: "B", VoteYes: true}, {Name: "C", VoteYes: true}}
	fmt.Println("happy path", runThreePhaseCommit(happy, ""))

	crash := []*Participant{{Name: "A", VoteYes: true}, {Name: "B", VoteYes: true}, {Name: "C", VoteYes: true}}
	fmt.Println("coordinator crashes after A precommits", runThreePhaseCommit(crash, "A"))
	fmt.Println("A state", crash[0].State, "B state", crash[1].State)
}
```

Run locally with `go run three_phase_commit.go`. Output observed.

```
happy path COMMITTED
coordinator crashes after A precommits COMMITTED
A state Committed B state Committed
```

Java, Rust, and Swift are omitted from this entry, not because the pattern
does not translate, it translates readily to any language with sum types or
enums plus mutable structs, but because three languages already demonstrate
the three genuinely distinct idiomatic shapes worth showing here. a plain
enum-and-dataclass form, a discriminated-union form that gets compile-time
exhaustiveness checking, and a struct-and-method form close to how a real
Go network service would be organized. A fourth or fifth language would
repeat one of these three shapes without adding a new idiom.

## 18. References

1. Dale Skeen. "Nonblocking Commit Protocols." Proceedings of the 1981 ACM
   SIGMOD International Conference on Management of Data, pages 133 to 142.
   https://dl.acm.org/doi/pdf/10.1145/582318.582339 Verified 2026-08-02. Source of
   the original nonblocking-condition proof and the protocol's origin.
2. Dale Skeen. "A Quorum-Based Commit Protocol." Cornell University
   Technical Report, February 1982. Source of the quorum-based construction
   most later texts summarize as CanCommit, PreCommit, DoCommit. cited via
   secondary academic index, the dl.acm.org listing and cross-referenced
   course bibliographies, since the original technical report is not hosted
   at a single stable public URL, verified 2026-08-02.
3. Dale Skeen and Michael Stonebraker. "A Formal Model of Crash Recovery in
   a Distributed System." IEEE Transactions on Software Engineering, volume
   SE-9, 1983, pages 219 to 228. DOI 10.1109/TSE.1983.236608. Verified
   2026-08-02 via the ACM Digital Library listing,
   https://dl.acm.org/doi/abs/10.1109/TSE.1983.236608, and the IEEE Xplore listing,
   https://ieeexplore.ieee.org/abstract/document/1703048/ Source of the formal
   resilience proof, including the partition-tolerance negative result
   cited in dimensions 3, 4, and 11.
4. Idit Keidar and Danny Dolev. "Increasing the Resilience of Distributed
   and Replicated Database Systems." Journal of Computer and System
   Sciences, volume 57, issue 3, 1998, pages 309 to 324. DOI
   10.1006/jcss.1998.1566, https://doi.org/10.1006/jcss.1998.1566.
   Verified 2026-08-18, resolved via Crossref metadata confirming title,
   authors, volume, issue, and page range. Source of the Extended
   Three-Phase Commit variant described in dimension 8.
5. Wikipedia contributors. "Three-phase commit protocol."
   https://en.wikipedia.org/wiki/Three-phase_commit_protocol Verified 2026-08-02.
   Used only to confirm the bounded-delay synchrony assumption and the
   message-count figures cited in dimensions 3, 9, and 11, cross-checked
   against the primary Skeen and Skeen-Stonebraker papers above for the
   underlying claims.
6. Cockroach Labs. "Parallel Commits. An atomic commit protocol for
   globally distributed transactions."
   https://cockroachlabs.com/blog/parallel-commits/ Verified 2026-08-02. Source for
   the documented production choice of a Two-Phase Commit derivative,
   cited in dimension 9's discussion of what modern distributed databases
   actually deploy in place of classical Three-Phase Commit.
