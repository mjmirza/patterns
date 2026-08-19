---
name: Two-Phase Commit
slug: two-phase-commit
family: 12-data-storage
category: Distributed Transactions
aliases: [2PC, Two-Phase Commit Protocol]
first_described: "Gray 1978"
maturity: canonical
related: [saga, write-ahead-log, quorum, event-sourcing, outbox]
incompatible_with: []
verified: 2026-08-02
---

# Two-Phase Commit

## 1. Name, aliases, and lineage

The canonical name is Two-Phase Commit, almost universally shortened to 2PC. It
is the atomic commitment protocol that lets a set of independent resources
agree, all together or not at all, on whether a distributed transaction
succeeded.

The protocol traces to Jim Gray, "Notes on Data Base Operating Systems," in
*Operating Systems, An Advanced Course*, Lecture Notes in Computer Science
volume 60, Springer Verlag, 1978, also circulated as IBM Research Report
RJ2188. A web search of academic citation records lists this paper as the
first public description of the two phase commit protocol, and it is the
paper cited by the standard textbook treatment, Philip A. Bernstein, Vassos
Hadzilacos, and Nathan Goodman, *Concurrency Control and Recovery in Database
Systems*, Addison Wesley, 1987, chapter 7, which formalises the protocol and
its correctness proof (verified 2026-08-02 against search results returned by
a live query for "Jim Gray 1978 Notes on Data Base Operating Systems two
phase commit first described").

The name describes its shape exactly. Phase one asks every participant to
vote. Phase two tells every participant the outcome. Nothing about the name
is metaphorical, which is unusual for a pattern in this catalog and is part
of why it reads as an algorithm rather than a design pattern in the
object-oriented sense. It belongs in a pattern catalog anyway because it is a
recurring, named structural solution to a recurring problem, participants,
coordinator, and a fixed message protocol between them, exactly the shape
dimension 5 below describes.

Two-Phase Commit is standardised, not only described. The X/Open group
published *Distributed Transaction Processing, The XA Specification* in
1991, defining the XA interface between a transaction manager and a resource
manager that most relational databases still implement today. MySQL's own
reference manual states plainly that its XA support is "based on the X/Open
CAE document Distributed Transaction Processing, The XA Specification"
(https://dev.mysql.com/doc/refman/8.4/en/xa.html, verified 2026-08-02). PREPARE
and COMMIT PREPARED in PostgreSQL implement the same two phases under
different verb names (https://www.postgresql.org/docs/current/sql-prepare-transaction.html,
verified 2026-08-02).

A related but distinct algorithm, Three-Phase Commit, was proposed later to
remove the blocking failure mode described in dimension 11. It is not covered
here as production databases essentially never use it, for reasons given in
dimension 8.

## 2. Problem and context

A single database transaction is easy to make atomic because one process
holds the log and one process decides. The problem starts the moment a
transaction has to touch two separate systems that each have their own
independent failure domain, their own log, and their own idea of what
committed. An order service writes a row in its own database and, in the
same business operation, tells a payment service to charge a card, which
writes into a completely different database. If the order commit succeeds
and the payment call fails, or the payment succeeds and the order write is
rolled back, the two systems now disagree about reality and nobody can find
out except by comparing state after the fact.

The concrete situation this pattern targets is a single logical transaction
that must be applied against multiple independent resource managers,
classically multiple database instances, sometimes a database plus a message
queue, sometimes multiple shards of the same distributed database, where each
resource manager can independently and durably decide to commit or abort its
own local piece of the work. Nobody outside the transaction should ever be
able to observe a state where some resources applied the change and others
did not. That is the atomicity guarantee a single-node database gives for
free through its own write-ahead log, and Two-Phase Commit exists to extend
that same guarantee across a network boundary where no single node has
authority over the others.

The context that makes this the right tool, rather than a workaround, has
three properties together. First, all the participants are known and
reachable at transaction start, this is not a fire and forget message to an
unknown set of subscribers. Second, each participant can hold locks and defer
its final decision for an unbounded but hopefully short window, meaning the
resource managers are willing to sacrifice some availability for correctness.
Third, correctness in the strict sense, no partial application ever visible,
matters more than latency or availability during the commit window. When any
of those three does not hold, later dimensions in this entry, especially 4
and 12, point toward Saga or event-sourced compensation instead.

## 3. Forces

**Consistency versus availability.** Two-Phase Commit is a strict pick of
consistency. Every participant that has voted yes must hold its locks and
wait for the coordinator's decision, which means the protocol trades
availability of that data for the guarantee that the outcome is identical
everywhere. This is the same trade the CAP framing makes explicit, and 2PC
sits firmly on the consistency side of it for the duration of a transaction.

**Latency versus atomicity.** The protocol requires at minimum two network
round trips, prepare and commit, before any participant can safely release
its locks, so end to end latency for a distributed write is bounded below by
the slowest participant's round trip time, twice. A transaction that could
be a single local write becomes a multi hop conversation.

**Coupling and blast radius.** The coordinator becomes a single point that
every participant depends on for its final answer. A slow or crashed
coordinator, discussed in dimension 11, stalls every participant that voted
yes, so the protocol trades operational simplicity, one place decides, for a
new class of failure, one place can freeze everyone.

**Cost of holding resources.** Locks held between prepare and commit are not
free. A participant that prepared and is waiting on a coordinator that never
responds is holding row locks, page locks, or worse, an entire connection
slot, for as long as the coordinator is unreachable. This is the force that
makes operations teams nervous about long-lived prepared transactions, and it
is why PostgreSQL's own documentation recommends disabling the feature
entirely when it is not actively used by a transaction manager
(https://www.postgresql.org/docs/current/sql-prepare-transaction.html,
verified 2026-08-02).

**Cognitive load and operability.** A team that adopts 2PC has to reason
about a new failure mode, the in-doubt transaction, that has no analogue in
single-node transactions. Operability tooling, monitoring for stuck prepared
transactions, alerting on coordinator unavailability, and a runbook for
manual resolution, is not optional overhead here, it is part of the pattern.

The pattern is honest about what it sacrifices. It buys strict atomicity
across independent failure domains and pays for that with availability
during the commit window, added latency, a new single point of coordination,
and an operational surface that a purely local transaction never has.

## 4. Applicability and non-applicability

Reach for Two-Phase Commit when all of the following hold together.

- The transaction spans a small, known, bounded set of participants that are
  all reachable and willing to accept the protocol, typically two to five
  resource managers, not dozens.
- Every participant can durably persist a prepared state and hold resources,
  usually locks, until told the outcome, and the resource manager exposes an
  interface for this, such as XA or a native PREPARE TRANSACTION verb.
- The business requirement genuinely needs all-or-nothing atomicity across
  those participants, not eventual consistency with a compensating action.
- The participants are within the same administrative and network trust
  boundary, or connected by a link reliable enough that coordinator outages
  are rare and short, because every outage directly costs availability.
- The transaction is short-lived, on the order of milliseconds to low single
  digit seconds, so the lock-holding window during phase one stays small.

Do not reach for Two-Phase Commit in these situations, and the reason is
specific to each.

- **The transaction spans organisational boundaries, for example calling a
  third party payment provider you do not operate.** You cannot force an
  external service to implement XA prepare semantics, and you have no
  authority to hold their resources locked while you decide. Use Saga with
  compensating actions instead, see dimension 13.
- **The transaction is long-running, human-in-the-loop, or waits on an
  external event that can take minutes or hours.** Holding locks for that
  duration turns a brief availability dip into a sustained outage for every
  row those locks touch. Use an orchestrated Saga or a state machine with
  compensations.
- **The participant count is large or unbounded, for example fanning a
  write out to every shard in a large horizontally sharded cluster.** The
  probability that at least one participant is slow or unreachable rises
  with participant count, and so does the probability of a stalled
  transaction, making the protocol progressively less reliable exactly where
  it is used most aggressively.
- **The system needs to stay available for writes during a network
  partition, even at the cost of temporary inconsistency that will be
  reconciled later.** 2PC is the wrong tool by construction, because it
  chooses to block rather than let a partitioned participant decide alone.
- **You are inside a single database engine that already gives you ACID
  transactions.** Reaching for XA across two schemas in the same physical
  database instance adds coordination overhead the local transaction manager
  already provides for free.
- **The workload is naturally idempotent and can tolerate eventual
  consistency with retries, for example most event-driven integration
  between services.** The outbox pattern, publishing an event as part of the
  local transaction and letting a relay deliver it at-least-once, achieves
  the same end-to-end correctness without a blocking protocol.

## 5. Structure

- **Coordinator (also called Transaction Manager, TM).** The single process
  that owns the decision. It assigns the transaction identifier, sends the
  prepare request to every participant, collects votes, decides commit only
  if every vote is yes, and then sends the final decision to every
  participant. The coordinator is the only participant whose durable log
  entry is authoritative for the outcome of the whole transaction.
- **Participant (also called Resource Manager, RM, or Cohort).** Each
  independent system taking part, typically a database instance. On receipt
  of prepare, a participant does all the work needed to guarantee it CAN
  commit, applies the change to a durable but not yet visible log record,
  acquires and holds any locks required, and replies yes or no. It never
  unilaterally commits on a yes vote, it waits for the coordinator's second
  message.
- **Transaction log (coordinator side).** A durable, force-written record on
  the coordinator that survives a coordinator crash and lets it recover the
  outcome of any in-flight transaction after restart, this is what
  distinguishes the protocol from an unreliable broadcast.
- **Prepared state (participant side).** The durable, in-doubt state each
  participant enters after voting yes and before receiving the final
  decision. PostgreSQL literally names this state PREPARED TRANSACTION.
- **Transaction identifier (XID).** A globally unique token that ties every
  message in both phases to one logical transaction, so a participant that
  restarts can ask what the fate of a given XID is and get a consistent
  answer.

## 6. ASCII structure diagram

```text
                       +----------------------+
                       |     Coordinator      |
                       |  (Transaction Log)    |
                       +-----------+----------+
                                   |
             prepare(xid) --------+-------- prepare(xid)
                    |             |             |
                    v             v             v
           +--------+---+  +-----+------+  +---+--------+
           |Participant A|  |Participant B|  |Participant C|
           |  (Resource  |  |  (Resource  |  |  (Resource  |
           |   Manager)  |  |   Manager)  |  |   Manager)  |
           +-------------+  +-------------+  +-------------+
             ^  yes/no  ^      ^  yes/no  ^      ^  yes/no  ^
             |          |      |          |      |          |
             +----------+------+----------+------+----------+
                                   |
                       commit(xid) or abort(xid)
                                   |
                                   v
                       (each participant applies
                        or discards, then acks)
```

## 7. Dynamics

```text
Coordinator                Participant A          Participant B
    |                            |                      |
    |------ PREPARE(xid) ------->|                      |
    |------ PREPARE(xid) ---------------------------- ->|
    |                            |                      |
    |                       [write undo/redo log,       |
    |                        acquire locks]              |
    |                            |                      |
    |<------ VOTE-YES -----------|                      |
    |<---------------------------------- VOTE-YES ------|
    |                            |                      |
    [force-write COMMIT record to coordinator log]
    |                            |                      |
    |------ COMMIT(xid) -------->|                      |
    |------ COMMIT(xid) ------------------------------ ->|
    |                            |                      |
    |                       [apply change, release      |
    |                        locks, discard undo log]    |
    |                            |                      |
    |<------ ACK -----------------|                      |
    |<---------------------------------- ACK ------------|
    |                            |                      |
    [discard coordinator log entry, transaction complete]

Abort path, any single VOTE-NO or a timeout on prepare replaces
COMMIT(xid) with ABORT(xid). Participants that already voted yes
must roll back on receiving ABORT, releasing their locks.

Coordinator crash mid-protocol, after force-writing COMMIT but
before all participants ack, recovery replays the coordinator log
and re-sends COMMIT to any participant that has not acknowledged.
Participant crash after voting yes but before receiving the final
message leaves that participant IN-DOUBT until it can reach the
coordinator, or a recovery participant, again.
```

The two force-writes are load-bearing. The participant's write in phase one,
the undo and redo information needed to either apply or discard the change,
must hit stable storage before the yes vote is sent, or a participant crash
after voting yes could lose the ability to honour that vote. The
coordinator's write in phase two, the commit decision itself, must hit stable
storage before any commit message is sent, because that single log record is
the only thing that lets the coordinator recover the correct, already-decided
outcome after its own crash rather than having to ask participants what they
remember, which they might disagree about.

## 8. Implementation variants

- **XA over relational databases (the industry-standard variant).** Defined
  by the X/Open XA specification and implemented by MySQL InnoDB
  (https://dev.mysql.com/doc/refman/8.4/en/xa.html, verified 2026-08-02) and
  PostgreSQL's PREPARE TRANSACTION and COMMIT PREPARED
  (https://www.postgresql.org/docs/current/sql-prepare-transaction.html,
  verified 2026-08-02). A client-side or middleware transaction manager plays
  the coordinator role and issues `XA START`, `XA END`, `XA PREPARE`, `XA
  COMMIT` against each database. This is the variant most engineers mean
  when they say two-phase commit against a database.
- **Presumed abort.** An optimisation where the coordinator does not force-
  write a durable log record for transactions that end up aborting. If a
  participant asks about a transaction ID the coordinator has no record of,
  the coordinator presumes it was aborted and answers accordingly. This
  halves the number of forced writes on the common path where the coordinator
  never needs to answer what happened, described in Bernstein, Hadzilacos,
  and Goodman, *Concurrency Control and Recovery in Database Systems*,
  Addison Wesley, 1987, chapter 7.
- **Presumed commit.** The mirror optimisation for workloads that mostly
  commit, at the cost of a slightly more complex protocol, trading the
  optimisation to the more common outcome for that workload.
- **Two-Phase Commit inside a single distributed database's own replica
  groups, rather than across independent products.** Google's Spanner uses
  Two-Phase Commit for transactions that touch data owned by more than one
  Paxos group, layering the protocol over an already-replicated, already-
  consistent storage layer so the blocking window is short and the
  coordinator itself is a replicated, highly available group rather than a
  single fragile process. This is described in the Spanner paper's public
  abstract and citation record, James C. Corbett et al., "Spanner, Google's
  Globally Distributed Database," ACM Transactions on Computer Systems, 2013
  (https://research.google/pubs/spanner-googles-globally-distributed-database/,
  verified 2026-08-02, abstract and publication record confirmed live, full
  protocol detail drawn from the paper's well documented public description
  of cross-group transactions using two-phase commit, not independently
  re-derived here).
- **Three-Phase Commit, a non-blocking variant, largely unused in
  production.** Adds a pre-commit phase so a coordinator failure does not
  leave participants blocked indefinitely under the assumption of no network
  partitions. It is covered in academic treatments as the theoretical
  answer to 2PC's blocking problem, but it assumes a synchronous network with
  bounded delay, an assumption production systems cannot rely on, and every
  major relational database ships 2PC, none ship 3PC as their transaction
  protocol, which is itself the strongest evidence of its practical fate.
- **Two-Phase Commit as an internal step inside a Saga orchestrator, scoped
  to a small sub-transaction.** Some systems use 2PC locally for the two or
  three resources that genuinely need atomicity, and Saga for the larger
  cross-service flow around it, rather than treating the two patterns as
  mutually exclusive choices.

## 9. Known production uses

- **PostgreSQL**, via `PREPARE TRANSACTION` and `COMMIT PREPARED`, exists
  specifically so that an external transaction manager can coordinate
  PostgreSQL as one participant in a distributed transaction
  (https://www.postgresql.org/docs/current/sql-prepare-transaction.html,
  verified 2026-08-02).
- **MySQL, InnoDB storage engine**, via XA transactions implementing the
  X/Open XA specification, used for cases such as coordinating a MySQL write
  with another MySQL instance, another XA-compliant database such as Oracle,
  or a messaging system in the same global transaction
  (https://dev.mysql.com/doc/refman/8.4/en/xa.html, verified 2026-08-02).
- **Java Transaction API (JTA) and Jakarta EE application servers**, which
  standardise the coordinator role as `UserTransaction` and
  `TransactionManager` and drive XA-compliant resource managers, the
  reference application-server-level implementation of the coordinator
  described in dimension 5.
- **Google Spanner**, which uses two-phase commit for transactions whose
  reads and writes span multiple Paxos-replicated groups, described in James
  C. Corbett et al., "Spanner, Google's Globally Distributed Database," ACM
  Transactions on Computer Systems, 2013
  (https://research.google/pubs/spanner-googles-globally-distributed-database/,
  verified 2026-08-02).
- **Microsoft Distributed Transaction Coordinator (MSDTC)**, the coordinator
  service shipped with Windows Server that lets SQL Server and other
  MSDTC-aware resource managers participate in cross-database or
  cross-machine two-phase commit transactions, a widely deployed example of
  the coordinator role implemented as a standalone operating system service.

## 10. Consequences

**Positive.**

- Strict atomicity across independently failing systems, no external
  observer can ever see a partially applied distributed transaction.
- A well-understood, standardised interface, XA, that many databases
  implement out of the box, so the participant side of the protocol rarely
  needs to be hand-written.
- Deterministic recovery. A coordinator that crashes and restarts can, given
  its own durable log, always resolve every in-flight transaction correctly,
  it does not need to guess.
- Composability with existing local transaction managers, since each
  participant still uses its own native transaction under the hood, prepare
  is layered on top rather than replacing it.

**Negative.**

- The protocol blocks. A participant that has voted yes and is waiting on a
  coordinator that has crashed or is partitioned away holds its locks with
  no way to resolve them on its own, this is the central and unavoidable
  weakness the algorithm accepts, discussed further in dimension 11.
- Added latency on every distributed transaction, two full network round
  trips at minimum, bounded by the slowest participant, before locks can be
  released.
- The coordinator becomes critical infrastructure. Its uptime and its log's
  durability directly gate the availability of every transaction that uses
  it, which pushes teams toward replicating the coordinator itself, adding
  more moving parts to solve the single point of failure the base protocol
  introduces.
- Poor fit for large fan-out. As participant count grows, so does the
  probability that at least one participant is slow, unreachable, or votes
  no, which drives up abort rates and increases the odds of the blocking
  scenario occurring somewhere in the fleet at any given moment.
- Operational burden. In-doubt or abandoned prepared transactions silently
  hold locks and, in PostgreSQL's case, actively interfere with vacuum and
  can force a forced shutdown to prevent transaction ID wraparound if left
  unresolved, which is why PostgreSQL's own documentation recommends setting
  `max_prepared_transactions` to zero unless a transaction manager is
  actively driving prepared transactions
  (https://www.postgresql.org/docs/current/sql-prepare-transaction.html,
  verified 2026-08-02).

## 11. Failure modes and misuse

- **Symptom.** A participant reports rows locked with no apparent owning
  session, and the lock does not clear on its own. **Cause.** The
  coordinator crashed, was network-partitioned away, or its process was
  killed after the participant voted yes but before it received the final
  commit or abort message, leaving the participant in the in-doubt, blocked
  state that dimension 10 names as the protocol's central weakness. **Fix.**
  Restore or repair the coordinator so it can replay its durable log and
  resend the decision, or, if the coordinator's log is genuinely and
  permanently lost, have an operator manually decide the outcome for each
  in-doubt transaction using external knowledge of what should have
  happened, then issue `COMMIT PREPARED` or `ROLLBACK PREPARED` by hand.
  This manual heuristic decision procedure is exactly the scenario the
  protocol's forced logging exists to make rare, never to make impossible.
- **Symptom.** A slow but not crashed participant causes every other
  participant in the same transaction to hold locks far longer than
  expected, and overall system throughput drops even though nothing has
  technically failed. **Cause.** Two-Phase Commit has no notion of a
  partial or best-effort outcome, the whole transaction runs at the speed of
  its slowest participant, and there is no way for a fast participant to
  proceed alone. **Fix.** Bound prepare-phase timeouts aggressively and
  treat a timeout as a no vote, an abort, never as an ambiguous state to
  wait out indefinitely, and keep the participant set small so one slow
  member has a small blast radius.
- **Symptom.** Prepared transactions accumulate over days or weeks and a
  database refuses new connections or forces an emergency vacuum shutdown.
  **Cause.** A misconfigured or crashed transaction manager left prepared
  transactions unresolved, and nobody was monitoring for them because the
  default assumption was that prepare and commit always happen close
  together. **Fix.** Actively monitor `pg_prepared_xacts` in PostgreSQL, or
  the equivalent XA recovery view in MySQL, and alert on any prepared
  transaction older than a small, workload-appropriate threshold, typically
  seconds to low minutes, not hours.
- **Symptom.** Two-Phase Commit is used to coordinate a write to an internal
  database and a call to a third-party payment API, and occasionally a
  charge succeeds on the provider's side while the internal transaction
  rolls back, or vice versa. **Cause.** This is a misuse of the pattern.
  Two-Phase Commit requires the participant to expose prepare semantics and
  to be willing to hold state pending an external decision, a third-party
  HTTP API almost never offers this, so wrapping it as if it were an XA
  resource manager only creates the illusion of atomicity while the real
  behaviour is closer to an unsynchronised best-effort call. **Fix.** Use
  Saga with an explicit compensating action, for example a refund call,
  rather than pretending an external, uncontrolled system can participate
  in phase one.
- **Symptom.** Adding a fourth or fifth participant to an existing
  two-participant transaction causes a visible jump in abort rate and
  timeout-related incidents that did not exist before. **Cause.** Abort
  probability compounds across participants, if each independent
  participant has even a small chance of a transient failure or slow
  response, the chance that at least one participant in the set fails rises
  quickly with participant count, which is the applicability boundary
  named in dimension 4. **Fix.** Keep the participant set small and
  bounded, and if the workload genuinely needs to touch many resources,
  restructure it as a Saga with independently committing local steps rather
  than one large 2PC transaction.

## 12. Trade-off matrix

| Force | Two-Phase Commit | Saga | Outbox plus eventual consistency |
|---|---|---|---|
| Atomicity guarantee | Strict, all-or-nothing, always | Eventual, via compensation, a window of partial state exists | Eventual, at-least-once delivery, no cross-service atomicity |
| Availability during commit | Reduced, participants block | High, each local step commits independently | High, local write always succeeds first |
| Latency per transaction | Two round trips minimum, bounded by slowest participant | Sum of local step latencies, can run in parallel branches | One local commit plus asynchronous relay |
| Coordinator single point of failure | Yes, unless replicated | Orchestrator can be stateless and restarted, compensations are idempotent | No central coordinator required |
| Works across organisational boundaries | No, requires prepare support from every participant | Yes, compensations are ordinary API calls | Yes, a consumer processes the event independently |
| Operational burden | Monitoring in-doubt transactions, lock timeouts | Designing and testing compensating actions for every step | Building and monitoring a reliable relay process |
| Best participant count | Small, roughly two to five | Larger, since steps commit independently | Effectively unbounded, fan-out via a message bus |

## 13. Related and incompatible patterns

**Composes with Write-Ahead Log.** Two-Phase Commit is only durable because
every participant and the coordinator each maintain their own write-ahead
log, the force-writes in dimension 7 are literally WAL entries. The pattern
is, structurally, an agreement protocol layered on top of per-node WAL
durability that already exists for local crash recovery.

**Replaced by Saga in cross-service and cross-organisation settings.** Saga
solves the same top-level problem, a business operation that spans multiple
systems needs to end in a consistent state, by giving up strict, simultaneous
atomicity in exchange for availability and the ability to include
participants that cannot support a prepare phase. Where 2PC blocks and waits,
Saga commits each local step immediately and compensates afterward if a
later step fails. The choice between them is dimension 4's applicability
test, not a maturity ranking, both are canonical for their respective
context.

**Complements Outbox.** A service that wants to write to its own database
and reliably publish an event without a distributed transaction across the
database and the message broker typically uses the Outbox pattern, writing
the event as a row in the same local transaction and relaying it
asynchronously, which sidesteps the need for 2PC between a database and a
broker entirely.

**Related to Quorum consensus, but solving a different problem.** Quorum-
based protocols such as Paxos and Raft answer which value the group agreed
on, typically for replicating a single piece of state across identical
replicas. Two-Phase Commit answers whether every heterogeneous participant
applied the change, across independently owned resources. Google Spanner
combines both, using Paxos to replicate each shard and Two-Phase Commit to
coordinate a transaction that spans shards, which is exactly the production
use cited in dimension 9.

**Incompatible with, or at minimum a poor fit for, long-running or
human-in-the-loop workflows.** Any pattern that assumes a step can pause for
minutes or hours, an approval step, a scheduled batch job, a wait for a
callback from a slow external system, is structurally incompatible with
holding 2PC locks open for that duration, and should be modelled as a Saga
or a state machine instead.

## 14. Refactoring path in and out

**Introducing Two-Phase Commit into code that currently makes two
uncoordinated local commits.** Start by identifying the exact set of
resource managers involved and confirm each one exposes prepare semantics,
this alone eliminates most candidate systems, such as third-party APIs, from
consideration and often ends the refactor before it starts. For the
remaining internal resources, introduce a coordinator, either a
purpose-built transaction manager library such as a JTA implementation, or a
hand-rolled coordinator that persists its own decision log before sending
commit or abort. Change the calling code so that instead of two independent
`COMMIT` statements, it issues `XA END` plus `XA PREPARE` against each
resource, waits for both votes, force-writes its own decision, then issues
`XA COMMIT` against each resource. Add monitoring for prepared transactions
before shipping this to production, per the operability point in dimension
3, this step is not optional, it is what turns an in-doubt transaction from
a silent time bomb into an alerted incident.

**Removing Two-Phase Commit once it stops earning its place.** The usual
trigger is that the participant set grew, the latency became unacceptable,
or a participant that cannot support prepare semantics, typically a
third-party service, needs to join the flow. The refactor path is to
introduce an explicit compensating action for each step, converting the
transaction into a Saga, then remove the shared coordinator and let each
step commit locally and immediately. This is a behaviour change, not a pure
refactor, because the system now has a window, however brief, where partial
state is genuinely visible to the outside world, so it needs an explicit
decision from whoever owns the business requirement that eventual
consistency is acceptable there, and it needs the compensating actions to be
designed and tested with the same care as the original forward steps, per
dimension 15.

## 15. Testing and verification

Two-Phase Commit makes certain properties easy to test and others
significantly harder.

Easy to test, because the protocol is explicit and deterministic. Unit tests
of the coordinator's decision logic, given a fixed set of votes, always all
yes, always at least one no, a mix, assert the coordinator always chooses
the same, correct outcome. This is straightforward because the decision
function is pure, no network involved.

Harder to test, and requiring deliberate fault injection, is the in-doubt
state after a coordinator crash. Verification here means actually killing
the coordinator process between the force-write of its decision and the
sending of the final message, then asserting that on restart it correctly
replays its log and resolves every participant to the same outcome it had
already decided. A test that only ever runs the happy path, prepare, all
yes, commit, all ack, without ever injecting a crash between those steps,
has not tested the property that makes this pattern worth using at all,
since the whole point of the coordinator log is crash recovery.

Participant-side recovery deserves the same treatment. Kill a participant
after it votes yes but before it receives the coordinator's decision,
restart it, and assert it correctly re-asks the coordinator and resolves to
the right outcome rather than either committing or aborting unilaterally.

A fake coordinator that can be programmed to crash at named points in the
protocol, one per participant message boundary, is a standard testing tool
for this pattern. Property-based testing is a good fit for the
coordinator's core decision function, generate a random set of votes and
assert the invariant that the outcome is commit if and only if every vote
was yes. What this pattern makes harder to test is anything involving real
network partitions rather than process kills, since a partition that heals
mid-test behaves differently from a clean crash and restart, and most local
test environments cannot cheaply and deterministically simulate a
partition the way they can a process kill.

## 16. Observability signals

**What to log.** Every prepare request and its vote, tagged with the
transaction ID and participant identity, every coordinator decision the
instant it is force-written, and every final commit or abort message sent
to each participant with its acknowledgment or timeout. The transaction ID
must appear on every one of these log lines so an operator can reconstruct
the full timeline of a single transaction across every participant's
independent logs.

**What to trace.** The prepare phase and the commit phase as two distinct
spans within one distributed trace, since their latency characteristics and
failure modes differ, and slow prepare responses from a specific participant
should stand out clearly rather than being averaged into a single overall
commit-time number that hides which participant was slow.

**What to measure.** The count and age distribution of currently in-doubt or
prepared transactions is the single most important gauge, since it is a
direct measure of the blocking risk described in dimension 11. Abort rate,
broken down by which participant voted no, second. Coordinator decision
latency, the time from the last participant's vote to the coordinator's
force-write. Time from force-write to every participant acknowledging, which
measures how long the decided-but-not-yet-fully-propagated window actually
stays open in production.

**What a healthy instance looks like on a dashboard.** Zero or very few
prepared transactions older than a few seconds, an abort rate consistent
with expected transient failures rather than a rising trend, and commit
latency governed mainly by network round trip time rather than by
participants sitting in the prepared state waiting on the coordinator.

**What a failing instance looks like.** A growing count of prepared
transactions with increasing maximum age, which is the leading indicator of
the blocking scenario in dimension 11 well before it becomes a lock
contention incident visible to end users. A sudden spike in abort rate
concentrated on one participant usually points at that participant being
overloaded or its own local resources, such as connection pool slots, being
exhausted.

## 17. Security and privacy implications

The prepare phase durably persists the full content of a pending write on
every participant, including any sensitive data in that write, before the
transaction is known to have committed. This means sensitive data sits in a
durable, at-rest log entry for the duration of the in-doubt window, and that
log entry, unlike the eventual committed row, may not be covered by the same
row-level access controls or encryption-at-rest policy review that the
application's normal data model receives, since prepared-transaction storage
is often a database-internal mechanism rather than an application table.
Teams handling regulated data, personal data subject to a right-to-erasure
requirement, or payment card data, should confirm that their prepared
transaction storage is covered by the same encryption and retention policy
as the rest of the database, and should keep the in-doubt window as short as
possible precisely because that window is an exposure window, not only a
performance concern.

The coordinator itself is an attack surface worth naming explicitly. A
coordinator with the authority to instruct a participant to commit or abort
is, functionally, a privileged component with write authority over every
participant's data. Access to the coordinator, its decision log, and the
network path between coordinator and participants should be treated with
the same care as access to a production database, since compromising the
coordinator, or replaying or forging a commit message, could force a
participant to apply a change it never independently validated on its own.
This entry does not go further than naming the surface, the specific
mitigations, mutual TLS between coordinator and participants, signed
transaction identifiers, are ordinary distributed systems security practice
rather than something specific to this pattern.

No further privacy-specific concern beyond the two named above was
identified for this pattern. It does not itself introduce a new category of
personal data collection, only a new place existing data can transiently
rest.

## 18. References

- Jim Gray, "Notes on Data Base Operating Systems," in *Operating Systems, An
  Advanced Course*, Lecture Notes in Computer Science volume 60, Springer
  Verlag, 1978, also circulated as IBM Research Report RJ2188, cited as the
  first public description of two-phase commit in academic citation records
  returned by a live search query, verified 2026-08-02.
- Philip A. Bernstein, Vassos Hadzilacos, and Nathan Goodman, *Concurrency
  Control and Recovery in Database Systems*, Addison Wesley, 1987, chapter 7,
  the standard textbook formalisation of the protocol including presumed
  abort and presumed commit optimisations.
- X/Open Company Ltd., *Distributed Transaction Processing, The XA
  Specification*, 1991, the standard interface between a transaction manager
  and a resource manager implemented by the databases named in dimension 9.
- PostgreSQL Global Development Group, "PREPARE TRANSACTION," PostgreSQL
  documentation, current version, https://www.postgresql.org/docs/current/sql-prepare-transaction.html,
  verified 2026-08-02.
- Oracle Corporation, "13.3.7 XA Transactions," MySQL 8.4 Reference Manual,
  https://dev.mysql.com/doc/refman/8.4/en/xa.html, verified 2026-08-02.
- James C. Corbett, Jeffrey Dean, Michael Epstein, et al., "Spanner, Google's
  Globally Distributed Database," ACM Transactions on Computer Systems, 2013,
  https://research.google/pubs/spanner-googles-globally-distributed-database/,
  verified 2026-08-02.
- Wikipedia contributors, "Two-Phase Commit Protocol," Wikipedia, consulted
  for the plain statement of the blocking disadvantage, cross-checked
  against the Bernstein, Hadzilacos, and Goodman textbook treatment above,
  https://en.wikipedia.org/wiki/Two-phase_commit_protocol, verified
  2026-08-02.

## Code examples

Working code in three languages follows, TypeScript, Python, and Go. Each
implements the coordinator's core decision and message-sequencing logic with
in-memory participants standing in for real resource managers, since a real
XA driver requires a live database connection this sandbox does not have.
The runnable focus is the protocol state machine itself, prepare, collect
votes, decide, notify, which is the part of the pattern most valuable to see
executed rather than merely described. Swift, Java, and Rust were considered
and are omitted here in favour of depth on three, per the template's
guidance to choose the languages where the pattern is genuinely idiomatic
and state plainly why a language is left out, the coordinator logic below
does not meaningfully change shape across Java, Swift, Kotlin, or Rust, it
is the same finite state machine in every C-family or ML-family language.

### TypeScript

```typescript
type Vote = "yes" | "no";

interface Participant {
  name: string;
  prepare(): Promise<Vote>;
  commit(): Promise<void>;
  abort(): Promise<void>;
}

class Coordinator {
  private log: string[] = [];

  async run(participants: Participant[]): Promise<"committed" | "aborted"> {
    const votes = await Promise.all(participants.map((p) => p.prepare()));
    const allYes = votes.every((v) => v === "yes");

    this.log.push(allYes ? "COMMIT" : "ABORT");

    if (allYes) {
      await Promise.all(participants.map((p) => p.commit()));
      return "committed";
    }

    await Promise.all(participants.map((p) => p.abort()));
    return "aborted";
  }
}

class FakeParticipant implements Participant {
  constructor(public name: string, private willVoteYes: boolean) {}

  async prepare(): Promise<Vote> {
    return this.willVoteYes ? "yes" : "no";
  }

  async commit(): Promise<void> {
    console.log(this.name + " committed");
  }

  async abort(): Promise<void> {
    console.log(this.name + " aborted");
  }
}

async function main() {
  const coordinator = new Coordinator();

  const outcomeAllYes = await coordinator.run([
    new FakeParticipant("orders-db", true),
    new FakeParticipant("payments-db", true),
  ]);
  console.log("all yes outcome", outcomeAllYes);

  const outcomeOneNo = await coordinator.run([
    new FakeParticipant("orders-db", true),
    new FakeParticipant("payments-db", false),
  ]);
  console.log("one no outcome", outcomeOneNo);
}

main();
```

### Python

```python
from dataclasses import dataclass
from typing import Literal

Vote = Literal["yes", "no"]


@dataclass
class Participant:
    name: str
    will_vote_yes: bool

    def prepare(self) -> Vote:
        return "yes" if self.will_vote_yes else "no"

    def commit(self) -> None:
        print(f"{self.name} committed")

    def abort(self) -> None:
        print(f"{self.name} aborted")


class Coordinator:
    def __init__(self) -> None:
        self.log: list[str] = []

    def run(self, participants: list[Participant]) -> str:
        votes = [p.prepare() for p in participants]
        all_yes = all(v == "yes" for v in votes)

        self.log.append("COMMIT" if all_yes else "ABORT")

        if all_yes:
            for p in participants:
                p.commit()
            return "committed"

        for p in participants:
            p.abort()
        return "aborted"


def main() -> None:
    coordinator = Coordinator()

    outcome_all_yes = coordinator.run(
        [Participant("orders-db", True), Participant("payments-db", True)]
    )
    print("all yes outcome", outcome_all_yes)

    outcome_one_no = coordinator.run(
        [Participant("orders-db", True), Participant("payments-db", False)]
    )
    print("one no outcome", outcome_one_no)


if __name__ == "__main__":
    main()
```

### Go

```go
package main

import "fmt"

type Vote string

const (
	VoteYes Vote = "yes"
	VoteNo  Vote = "no"
)

type Participant struct {
	Name        string
	WillVoteYes bool
}

func (p Participant) Prepare() Vote {
	if p.WillVoteYes {
		return VoteYes
	}
	return VoteNo
}

func (p Participant) Commit() {
	fmt.Println(p.Name + " committed")
}

func (p Participant) Abort() {
	fmt.Println(p.Name + " aborted")
}

type Coordinator struct {
	log []string
}

func (c *Coordinator) Run(participants []Participant) string {
	allYes := true
	for _, p := range participants {
		if p.Prepare() == VoteNo {
			allYes = false
		}
	}

	if allYes {
		c.log = append(c.log, "COMMIT")
		for _, p := range participants {
			p.Commit()
		}
		return "committed"
	}

	c.log = append(c.log, "ABORT")
	for _, p := range participants {
		p.Abort()
	}
	return "aborted"
}

func main() {
	coordinator := &Coordinator{}

	outcomeAllYes := coordinator.Run([]Participant{
		{Name: "orders-db", WillVoteYes: true},
		{Name: "payments-db", WillVoteYes: true},
	})
	fmt.Println("all yes outcome", outcomeAllYes)

	outcomeOneNo := coordinator.Run([]Participant{
		{Name: "orders-db", WillVoteYes: true},
		{Name: "payments-db", WillVoteYes: false},
	})
	fmt.Println("one no outcome", outcomeOneNo)
}
```
