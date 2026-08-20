---
name: Two-Phase Locking
slug: two-phase-locking
family: 12-data-storage
category: Data and Storage
aliases: [2PL, Strict Two-Phase Locking, Rigorous Two-Phase Locking, Conservative Two-Phase Locking]
first_described: "Eswaran, Gray, Lorie, Traiger 1976"
maturity: canonical
related: [write-ahead-log, quorum, three-phase-commit, raft, paxos, b-tree]
incompatible_with: [optimistic-concurrency-control, multi-version-concurrency-control]
verified: 2026-08-02
---

# Two-Phase Locking

## 1. Name, aliases, and lineage

The canonical name is Two-Phase Locking, universally abbreviated 2PL. It was
introduced by Kapali P. Eswaran, Jim Gray, Raymond A. Lorie, and Irving L.
Traiger in "The Notions of Consistency and Predicate Locks in a Database
System", Communications of the ACM, volume 19, number 11, November 1976,
pages 624 to 633. The paper is the origin of the rule this pattern is named
for. once a transaction releases any lock it may never acquire another one,
and it proves that a schedule obeying this rule is conflict-serializable
(K. P. Eswaran, J. N. Gray, R. A. Lorie, I. L. Traiger, "The Notions of
Consistency and Predicate Locks in a Database System", Communications of the
ACM, vol. 19, no. 11, 1976, pp. 624 to 633, https://dl.acm.org/doi/10.1145/360363.360369
verified 2026-08-02).

Three named variants appear constantly in textbooks and vendor documentation,
and conflating them is the single most common source of confusion about the
pattern.

- **Basic (or classic) two-phase locking.** The bare rule from the 1976 paper.
  A transaction has a growing phase in which it may only acquire locks and a
  shrinking phase in which it may only release them, and the transition
  happens the moment the first lock is released.
- **Strict two-phase locking (S2PL).** All exclusive (write) locks are held
  until the transaction commits or aborts, so the shrinking phase collapses
  into a single instant at transaction end. This is the variant almost every
  production database actually implements, because it also guarantees
  recoverability, no other transaction can read a value written by a
  transaction that later aborts.
- **Strong strict, or rigorous, two-phase locking.** Both shared (read) and
  exclusive locks are held until commit or abort. This is the variant that
  also avoids cascading aborts entirely and is what most people mean
  when they informally say "2PL" while describing a real database engine.

The pattern's name is occasionally confused with two-phase commit, a
distributed-transaction protocol described in the same academic neighborhood
but solving a different problem. two-phase commit coordinates whether a
transaction's effects become durable across multiple participants, while
two-phase locking coordinates whether concurrent transactions may see each
other's uncommitted or conflicting effects at all. The two are frequently
used together, one inside a single node and the other across nodes, and that
combination is documented for Google Cloud Spanner in dimension 9.

## 2. Problem and context

Multiple transactions run concurrently against a shared database, each one
reading and writing rows that another transaction might also be touching at
the same instant. Left unmanaged, this produces the classic anomalies. a
transaction reads a value another transaction is mid-way through updating
(a dirty read), two transactions read the same row twice within one
transaction and get different values because a third transaction committed
in between (a non-repeatable read), or a transaction's range query returns a
different set of rows on a second execution because another transaction
inserted a matching row (a phantom read).

The concrete situation looks like this in a running system. A bank's transfer
procedure debits one account and credits another inside a single logical
transaction. If a second transaction is allowed to read the debited account's
new balance before the credit has happened, and that second transaction acts
on the half-finished state, the database has exposed an inconsistency that
never existed at any committed point in time. The question the pattern
answers is mechanical, not aspirational. what rule can a database engine
enforce, purely by tracking which locks a transaction holds and in what
order it acquires and releases them, that guarantees every possible
interleaving of concurrent transactions produces a result equivalent to
running them one at a time in some order.

The context in which locking is the right tool, rather than one of its
alternatives, is a workload where conflicts between transactions are common
enough that detecting them after the fact and retrying is more expensive than
preventing them up front. That is the axis dimension 4 turns on.

## 3. Forces

- **Correctness versus concurrency.** Favors correctness. The pattern trades
  raw parallelism for a guarantee, serializability, and the guarantee is
  bought by making conflicting transactions wait rather than letting them
  proceed and checking for damage later.
- **Latency versus throughput under contention.** Sacrificed under
  contention. A transaction that needs a lock another transaction holds does
  not fail fast, it blocks, so the tail latency of any single transaction is
  coupled to how long every conflicting transaction ahead of it takes to
  finish.
- **Deadlock risk.** Sacrificed. Any locking protocol that lets transactions
  hold one resource while waiting for another opens the door to a cycle of
  mutual waiting. Two-phase locking does not prevent deadlock on its own, it
  requires a separate mechanism, detection or prevention, described in
  dimension 9 and dimension 11.
- **Read-only workload performance.** Neutral to mildly sacrificed under
  strict variants. A read-only transaction under rigorous 2PL still holds
  shared locks until it finishes, which can block a writer that would
  otherwise have proceeded, a cost that multi-version concurrency control
  (dimension 13) exists specifically to remove.
- **Implementation simplicity.** Favored relative to optimistic schemes. The
  rule is a single invariant, tracked per transaction, checked at every lock
  request, with no need to detect conflicts retroactively or roll back
  committed-looking work.
- **Recoverability and cascading aborts.** Favored by the strict and rigorous
  variants, sacrificed by the basic variant. Basic 2PL guarantees
  serializability but not recoverability, a transaction can read a value
  written by another transaction that has not yet committed and might still
  abort, which then forces the reader to abort too, and can cascade.
- **Operability under skew.** Sacrificed at scale. A small number of hot
  rows, a popular counter, a singleton configuration row, concentrate lock
  contention and become a visible throughput ceiling that shows up as queued
  transactions rather than as a CPU or I/O bottleneck.

No locking protocol gives up nothing. The price here is paid in blocking,
deadlock risk, and reduced parallelism on contended data, in exchange for a
correctness guarantee that does not depend on detecting a violation after it
has already happened.

## 4. Applicability and non-applicability

Reach for two-phase locking, or rely on a database engine that uses it
internally, when the following hold.

- Conflicts between concurrent transactions are frequent enough that an
  optimistic scheme would spend most of its time retrying rather than
  committing. Write-heavy workloads on a shared, contended key space are the
  textbook case.
- The cost of blocking a transaction is lower than the cost of letting it
  proceed and then discovering, after real work has been done, that it must
  be rolled back. This favors 2PL when transactions perform side effects
  that are expensive or impossible to undo cleanly, or when clients cannot
  tolerate an unbounded retry loop.
- Strong isolation, serializability or something close to it, is a
  requirement of the application's correctness, not a nice-to-have. Financial
  ledgers, inventory counts that must never go negative, and seat or ticket
  allocation are the recurring examples.
- The system already has a mechanism for deadlock detection or prevention in
  place, because 2PL alone does not supply one.

Do NOT reach for two-phase locking in these cases, and the reason matters
more than the rule.

- **The workload is read-heavy with rare conflicts.** Locking pays its full
  blocking and bookkeeping cost on every transaction, including the vast
  majority that would never have conflicted with anything. Multi-version
  concurrency control (dimension 13) gives readers a consistent snapshot
  without blocking writers at all, and is the default choice for this shape
  of workload in every mainstream engine.
- **Conflicts are rare but must still be caught correctly when they occur.**
  Optimistic concurrency control, validate at commit time instead of locking
  up front, wins here because it pays almost nothing on the common
  conflict-free path and only pays on the rare path that actually needs it.
- **The transaction touches a wide, unpredictable, or unbounded set of rows,**
  such as a scan with no selective index. Locking the scanned range, or
  worse, escalating to a table lock, serializes work that has no logical
  reason to conflict, which is exactly the SQL Server behavior documented in
  dimension 9.
- **The system is a distributed, leaderless, or eventually consistent store**
  where there is no single place to hold a lock and no bound on how long a
  partitioned node might be unreachable. Holding a lock across a network
  partition turns a temporary outage into an indefinite one. Consensus-based
  ordering (see the Raft and Paxos entries) or conflict-free replicated data
  types (see the CRDT entry) fit that context instead.
- **The application can tolerate, and would rather have, eventual
  consistency in exchange for availability during a partition.** Two-phase
  locking has no answer for the availability side of the CAP trade, it
  requires reaching the lock holder, so it is the wrong tool whenever the
  system's actual requirement is to keep serving requests through a network
  split.
- **A single long-running transaction would hold a lock on hot data for a
  long time,** such as a report that scans and locks rows for minutes.
  This starves every other transaction that touches the same rows and is a
  frequent cause of the production incident described in dimension 11.

## 5. Structure

Two-phase locking is a protocol, not an object graph, so its participants
are roles a transaction manager plays rather than classes in a diagram.

- **Lock Manager.** The component that owns the lock table, decides whether a
  requested lock is compatible with the locks already held on a resource, and
  either grants the request or places the requesting transaction on a wait
  queue.
- **Transaction.** The unit of work that requests locks. Every transaction
  passes through exactly two phases in sequence, and this is the part the
  pattern's name refers to. a growing phase in which it may only acquire new
  locks, and a shrinking phase in which it may only release locks it already
  holds. The moment it releases its first lock, it enters the shrinking
  phase, and it may never acquire another lock afterward. This is a property
  of the schedule, checked by the lock manager, not a phase the transaction's
  own code declares.
- **Lock.** An entry in the lock table associating a resource with a mode,
  most commonly shared for reads and exclusive for writes, and the set of
  transactions currently holding it.
- **Compatibility Matrix.** The rule the lock manager consults to decide
  whether a new request conflicts with existing holders. Two shared locks on
  the same resource are compatible with each other; an exclusive lock is
  compatible with nothing else on the same resource, including another
  exclusive lock.
- **Wait Queue (or wait-for graph).** The record of which transactions are
  blocked waiting for which locks, held by the lock manager. This structure
  is also what a deadlock detector walks to find cycles, described in
  dimension 9.

## 6. ASCII structure diagram

```
   +---------------------------+
   |      Lock Manager         |
   |----------------------------
   | + acquire(txn, res, mode) |
   | + release(txn, res)       |
   | + commit(txn)             |
   +-------------+--------------+
                 |
                 | owns
                 v
   +---------------------------+          +----------------------+
   |        Lock Table         |          |   Wait-For Graph      |
   |----------------------------          |------------------------
   | resource -> {txn: mode}   |          | blocked_txn -> holder |
   +---------------------------+          +----------------------+
                 ^
                 | consults
                 |
   +---------------------------+
   |   Compatibility Matrix     |
   |----------------------------|
   |        | Shared | Excl |   |
   | Shared |  yes   | no   |   |
   | Excl   |  no    | no   |   |
   +---------------------------+

   Transaction lifecycle (the two phases the name refers to):

   +-------------+   first release/commit   +---------------+
   |  Growing    | ------------------------>|  Shrinking    |
   |  acquire()  |    (irreversible)         |  release()    |
   |  only       |                           |  only, never  |
   +-------------+                           |  acquire()    |
                                              +---------------+
```

## 7. Dynamics

The runtime flow shows a transaction acquiring locks as it touches data,
another transaction blocking on a conflicting resource, and the resolution
that happens when the first transaction commits and releases everything at
once, which is how strict two-phase locking is actually implemented.

```
T1                    Lock Manager                   T2
 |                          |                          |
 |-- acquire(X, "row:7") -->|                          |
 |<-- granted --------------|                          |
 |   [T1 now GROWING,       |                          |
 |    holds X on row:7]     |                          |
 |                          |                          |
 |                          |<-- acquire(S, "row:7") --|
 |                          |    conflict: X held      |
 |                          |    by T1, T2 blocks       |
 |                          |    on wait queue          |
 |                          |                          |
 |-- write row:7 ---------->|                          |
 |-- commit() ------------->|                          |
 |   [T1 releases every     |                          |
 |    lock it holds at      |                          |
 |    once: SHRINKING]      |                          |
 |                          |-- granted (S, row:7) --->|
 |                          |                          |
 |                          |                       read row:7
 |                          |                          |
 |                          |<-- commit() -------------|
```

A second dynamic worth showing explicitly is deadlock. Two transactions each
hold a lock the other needs, and neither can proceed. This is not a defect in
the implementation above, it is an inherent possibility whenever transactions
can hold one resource while waiting on another, and it is why dimension 9
covers deadlock detection and prevention as a required companion mechanism,
not an optional extra.

```
T1                                        T2
 |-- acquire(X, "account:1") --> granted   |
 |                                          |-- acquire(X, "account:2") --> granted
 |-- acquire(X, "account:2") --> BLOCKS     |
 |   (T2 holds it)                          |-- acquire(X, "account:1") --> BLOCKS
 |                                          |   (T1 holds it)
 |
 |          wait-for graph:  T1 -> T2 -> T1   (a cycle)
 |
 |   deadlock detector walks the wait-for graph, finds the cycle,
 |   and aborts one transaction (the victim) to break it
```

## 8. Implementation variants

**Basic two-phase locking.** Locks are released individually, as soon as a
transaction no longer needs a given resource, and the shrinking phase begins
at the first release. This is the form the 1976 paper proves serializable,
but it is rarely used as-is in production because it does not guarantee
recoverability, described in dimension 3.

**Strict two-phase locking (S2PL).** Exclusive locks are held until commit
or abort; shared locks may still be released early. This is the most common
form implemented by relational database engines, because it prevents
cascading aborts on writes while still allowing some early release on reads.

**Rigorous (strong strict) two-phase locking.** Both shared and exclusive
locks are held until commit or abort. Simplest to reason about, and the
variant most people picture when they think of "how a database locks rows",
at the cost of holding read locks longer than basic 2PL would.

**Two-phase locking with lock upgrade.** A transaction first acquires a
shared lock to read a row, then upgrades it to exclusive to write the same
row, rather than acquiring exclusive from the start. This reduces contention
when a transaction reads before conditionally writing, but upgrade requests
from two transactions both holding shared locks on the same row is a classic
deadlock shape, addressed by update locks in the variant below.

**Update locks (SQL Server's `SELECT ... UPDATE` intent, and similar
constructs elsewhere).** An intermediate lock mode, compatible with shared
but not with itself or exclusive, acquired instead of shared when a
transaction knows it may later write the row. Only one transaction can hold
an update lock on a resource at a time, which serializes the upgrade race
that plain shared-to-exclusive upgrades are prone to.

**Multi-granularity locking (intent locks).** Locks are taken hierarchically,
a table, then a page or extent, then a row, with intent-shared and
intent-exclusive modes at the coarser levels signaling that a finer-grained
lock is held somewhere beneath. This is what allows a single row lock and a
full table scan to coexist correctly without checking every row
individually, and it is the mechanism underneath lock escalation described
in dimension 9.

**Predicate locking and next-key locking.** Ordinary row locks cannot
prevent a phantom insert, because the row being inserted did not exist to be
locked. Predicate locks conceptually lock the condition of a query rather
than the rows it currently matches; next-key locking, the practical
approximation used by InnoDB, locks an index record together with the gap
before it, so an insert that would fall inside a range a transaction has
scanned is blocked. Both are covered with production references in
dimension 9.

**Deadlock prevention instead of detection, wound-wait and wait-die.**
Rather than let deadlocks form and detecting them afterward, every
transaction is timestamped at start, and a conflicting lock request is
resolved purely by comparing ages. in wound-wait, an older transaction
aborts ("wounds") a younger one holding a lock it needs, while a younger
transaction waits for an older one; in wait-die, an older transaction waits,
while a younger one aborts itself rather than wait for an older one. Both
avoid building a wait-for graph at all, at the cost of some transactions
aborting that would never actually have deadlocked. Cloud Spanner's use of
wound-wait is documented with a source in dimension 9.

## 9. Known production uses

**PostgreSQL, table-level and row-level lock modes.** PostgreSQL implements
eight named table-level lock modes with an explicit compatibility matrix, and
uses these together with row-level locking as the mechanism underlying its
transaction isolation levels above read committed. The manual documents the
modes, states that only `ACCESS EXCLUSIVE` blocks a plain `SELECT`, and notes
that PostgreSQL keeps no fixed limit on the number of rows a transaction can
lock, so it does not escalate row locks into a table lock the way SQL Server
does. PostgreSQL Global Development Group, "PostgreSQL 18 Documentation",
chapter 13.3, "Explicit Locking",
https://www.postgresql.org/docs/current/explicit-locking.html
verified 2026-08-02.

**MySQL InnoDB, next-key locking under REPEATABLE READ.** InnoDB's stated
design goal is to combine multi-versioning with traditional two-phase
locking. Under its default `REPEATABLE READ` isolation level, InnoDB uses
next-key locks, a combination of a record lock on an index entry and a gap
lock on the space immediately before it, specifically to close the phantom
row problem that plain row locking cannot address. Oracle Corporation, "MySQL
9.7 Reference Manual", section 17.7.1, "InnoDB Locking", and section 17.7.4,
"Locking Reads",
https://dev.mysql.com/doc/en/innodb-locking.html
verified 2026-08-02.

**Microsoft SQL Server, hierarchical locking and lock escalation.** SQL
Server acquires row, page, and table-level locks in a hierarchy using intent
locks, and automatically escalates a transaction's row or page locks into a
single table lock once a single statement holds roughly 5,000 locks on one
table reference, to bound the memory cost of the lock table. The official
guide documents this exact threshold and the retry behavior when escalation
cannot immediately succeed. Microsoft, "SQL Server Transaction Locking and
Row Versioning Guide", section "Lock Escalation",
https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-transaction-locking-and-row-versioning-guide
verified 2026-08-02.

**Google Cloud Spanner, two-phase locking combined with wound-wait.** Spanner
runs pessimistic, lock-based concurrency control for read-write transactions,
acquiring locks as data is read and written and verifying previously
acquired locks remain held through later statements in the transaction, the
defining shape of two-phase locking. When a lock conflict is detected,
Spanner resolves it with the wound-wait algorithm, aborting the younger of
the two conflicting transactions so the older one can make progress, which
Spanner determines by comparing each transaction's earliest read, query, or
commit timestamp. Google Cloud, "Concurrency control | Spanner",
https://docs.cloud.google.com/spanner/docs/concurrency-control
verified 2026-08-02.

**IBM Db2, lock escalation under memory pressure.** Db2's locking model
similarly grants row and table intent locks and escalates a transaction's
row locks into a single table lock when the lock list memory allocated to
the transaction, or to the whole instance, is exhausted, a mechanism analogous
to SQL Server's threshold-based escalation and driven by the same underlying
concern, bounding lock-table memory rather than a fixed row count. IBM, "Db2
for Linux, UNIX, and Windows Knowledge Center", topic "Lock escalation",
https://www.ibm.com/docs/en/db2/12.1?topic=locking-lock-escalation
verified 2026-08-02.

## 10. Consequences

Positive.

- Serializability is guaranteed as a property of the schedule, provable
  directly from the two-phase rule, without requiring the system to detect a
  violation after the fact and undo committed-looking work.
- The strict and rigorous variants also guarantee recoverability, no
  committed transaction's result ever depends on a transaction that later
  aborts, which removes an entire class of cascading-abort bugs.
- The mechanism is local and per-resource. a lock manager reasons about one
  resource's holders and waiters at a time, with no need for a global
  timestamp oracle or a distributed consensus round on the common path.
- It composes cleanly with write-ahead logging and crash recovery, because
  the set of locks a transaction holds at any instant is exactly the set of
  writes that must be undone or redone together on recovery.
- Multi-granularity locking lets a single fine-grained lock and a coarse
  table-level operation coexist correctly, which a purely row-level or
  purely table-level scheme cannot express.

Negative.

- Transactions block rather than fail fast, so the tail latency of a
  transaction under contention is coupled to however long the transactions
  ahead of it in the queue take, which is a very different failure mode from
  an optimistic scheme's bounded retry.
- The protocol does not prevent deadlock; it requires a separate detection or
  prevention mechanism, and choosing and tuning that mechanism, detection
  interval, timeout, or a wound-wait or wait-die ordering, is additional
  design surface the pattern itself does not settle.
- Lock escalation, needed to bound lock-table memory under wide scans or bulk
  operations, trades fine-grained concurrency for memory safety, and can turn
  what should be a narrow, low-conflict operation into a table-wide
  bottleneck if it triggers unexpectedly.
- Long-held locks on hot rows create a visible throughput ceiling that scales
  with contention, not with hardware, so adding CPU or I/O capacity does not
  relieve it.
- Read-only workloads pay the full cost of shared-lock bookkeeping and
  blocking under strict or rigorous variants, even though a reader can never
  cause the kind of anomaly the lock exists to prevent against another
  reader.

## 11. Failure modes and misuse

**Lock escalation storm.** Symptom. A batch job that updates most of a large
table suddenly blocks every other statement touching that table, and the
blocking starts abruptly partway through the job rather than gradually.
Cause. The job's row locks crossed the engine's escalation threshold and
converted into a single table-level exclusive lock. Fix. Break the batch into
smaller transactions, or run it with a lock hint that disables escalation for
that statement, accepting the higher per-row locking cost in exchange for
not blocking unrelated readers.

**Deadlock from inconsistent lock ordering.** Symptom. Two application code
paths that both update two accounts occasionally deadlock, and the deadlock
disappears when load is low and reappears under peak traffic. Cause. One
code path locks account A then account B, and a different code path locks B
then A; under enough concurrency the two orderings eventually interleave into
a cycle. Fix. Establish and enforce a single canonical lock order, for
example always by ascending primary key, across every code path that touches
more than one resource in a transaction.

**Long-held read locks starving writers.** Symptom. A reporting query that
runs for several minutes causes unrelated write transactions on the same
rows to queue up and time out. Cause. Rigorous two-phase locking holds shared
locks until commit, so a long-running read transaction holds its locks for
its entire duration, not only for the instant it reads each row. Fix. Move
long-running analytical reads to a snapshot-isolated or MVCC read path that
does not take row locks at all, or explicitly bound the transaction's
duration and break it into smaller chunks.

**Phantom reads from row-only locking.** Symptom. A range query that checks
a business invariant, no two rows share a value, is re-run inside the same
transaction and returns a different, invariant-violating set, even though
every row it read the first time was correctly locked. Cause. A plain row
lock cannot lock a row that does not exist yet; an insert into the gap is
invisible to the lock manager. Fix. Use next-key or predicate locking, or
raise the isolation level to one the engine implements with range-covering
locks or serializable snapshot isolation.

**Lock upgrade deadlock.** Symptom. Two transactions each hold a shared lock
on the same row and both then request an exclusive upgrade, and both hang
indefinitely. Cause. Neither transaction can proceed because the other's
shared lock blocks the upgrade, and neither will release its own shared lock
first because both are still mid-transaction, a deadlock the ordinary
wait-for graph correctly detects but which recurs constantly if the access
pattern is common. Fix. Acquire an update lock (or its engine-specific
equivalent) instead of a shared lock whenever the code path might later
write the same row, so only one transaction can be in the upgrade race at a
time.

**Treating a lock timeout as a correctness signal.** Symptom. Application
code catches a lock-wait timeout exception and silently treats it as "the
row did not exist" or "the update failed", producing wrong results under
load without any error surfacing. Cause. A lock timeout is a concurrency
signal, not a data signal, and conflating the two hides real contention
problems behind incorrect application behavior. Fix. Treat a lock timeout as
a retryable transient failure distinct from every other exception type, and
alert on a rising timeout rate as a contention signal in its own right.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Strict Two-Phase Locking | Optimistic Concurrency Control | Multi-Version Concurrency Control (snapshot isolation) | Serializable Snapshot Isolation | Timestamp Ordering |
|---|---|---|---|---|---|
| Behavior under high conflict | Predictable, transactions queue | Poor, high abort and retry rate | Good for reads, writers still conflict | Good, aborts only on true anomalies | Predictable, older wins by timestamp |
| Behavior under low conflict | Pays locking overhead needlessly | Excellent, almost free on the common path | Excellent for reads | Excellent, near-zero abort rate | Pays timestamp bookkeeping overhead |
| Reader-writer blocking | Readers can block writers and vice versa | None, validation only at commit | Readers never block writers | Readers never block writers | Readers do not block writers |
| Deadlock possibility | Yes, needs detection or prevention | No, there is nothing to deadlock on | No blocking, so no deadlock | No blocking, so no deadlock | No, resolved by timestamp comparison |
| Guarantees serializability | Yes, by construction | Yes, if validation is correctly scoped | No on its own, snapshot anomalies possible | Yes, by design | Yes, by construction |
| Memory or storage cost | Lock table sized to active transactions | Low, only a version check per commit | Higher, must retain old row versions | Higher, retains versions plus a conflict graph | Moderate, per-item read and write timestamps |
| Best workload shape | Write-heavy, high-conflict, side effects expensive to undo | Read-mostly with rare, cheap-to-retry conflicts | Read-heavy with concurrent writers | Any workload needing true serializability without blocking | Distributed systems with a reliable clock or counter |

Reading of the table. Two-phase locking wins decisively when conflicts are
frequent and retrying committed-looking work is expensive or unsafe.
Optimistic concurrency control wins when conflicts are rare. MVCC and
serializable snapshot isolation win when the workload is read-heavy and
readers should never be made to wait on writers, which is why they are the
default isolation mechanism in PostgreSQL, Oracle, and SQL Server's
`READ COMMITTED SNAPSHOT` mode rather than 2PL.

## 13. Related and incompatible patterns

- **Write-Ahead Log.** A near-mandatory companion, not a substitute. The set
  of locks a transaction holds at any instant defines exactly the writes that
  crash recovery must undo or redo together, so the two mechanisms are
  designed to be read side by side. locking answers "what may run
  concurrently", the write-ahead log answers "what must be recovered
  together".
- **Quorum.** Orthogonal, and frequently layered underneath 2PL in a
  distributed system. Quorum decides how many replicas must acknowledge a
  write for it to be considered durable; two-phase locking, running on the
  leader or coordinator that owns the quorum write, decides which
  transactions may proceed concurrently in the first place.
- **Two-Phase Commit and Three-Phase Commit.** Complementary, and commonly
  confused by name alone. Two-phase commit coordinates whether a
  transaction's effects become durable across multiple participants after
  the participants have already agreed to proceed; two-phase locking is what
  each participant uses internally to decide, before that point, which
  transactions may touch which rows.
- **Raft and Paxos.** Solve a different problem at a different layer.
  Consensus protocols order a sequence of operations across replicas so every
  replica agrees on the same log; 2PL governs concurrency between
  transactions on a single logical copy of the data, often running on top of
  the leader a consensus protocol has elected.
- **Multi-Version Concurrency Control.** A substitute for the read side of
  the problem, and actively incompatible in intent. MVCC is designed
  specifically so readers never block on writers and never take locks at
  all, which is the opposite trade-off from rigorous 2PL. A production system
  can combine them, MVCC for reads, locking for writes, as InnoDB does, but
  running both as competing strategies for the same access is redundant.
- **Optimistic Concurrency Control.** A substitute for the whole pattern
  under a different bet about conflict frequency. Where 2PL prevents a
  conflict from ever being observed, optimistic concurrency control lets
  transactions proceed and validates at commit time, aborting on conflict
  rather than blocking on it.
- **B-Tree and index locking.** Composes underneath, not above. B-tree index
  structures need their own, much finer-grained locking protocol, latch
  coupling, to protect the tree's internal structure during concurrent
  modification, which is a distinct and lower-level concern from the
  row-level or predicate-level locking 2PL governs for transaction
  isolation.

## 14. Refactoring path in and out

Introducing explicit locking discipline into code that currently relies on
whatever default isolation level a database happens to provide.

1. Identify the invariant that must hold across a transaction, "the sum of
   two account balances is unchanged", "no two rows share this unique key
   after the transaction commits". An invariant that spans more than one row
   or more than one statement is the signal that implicit per-statement
   locking is not sufficient.
2. Confirm the database's default isolation level actually provides the
   protection the invariant needs. Many engines default to `READ COMMITTED`,
   which does not prevent the anomalies described in dimension 2 across
   multiple statements in one transaction.
3. Where the engine offers explicit locking reads, `SELECT ... FOR UPDATE` or
   its equivalent, add it to every statement that reads a row the transaction
   will later depend on remaining unchanged, not only the rows it will write.
4. Establish and document a single, consistent lock acquisition order across
   every code path that touches more than one resource, per the fix in
   dimension 11, before load testing rather than after a deadlock incident.
5. Move to `SERIALIZABLE` isolation, or the engine's rigorous locking mode,
   only for the specific transaction types that need it, since applying it
   globally pays the full blocking cost documented in dimension 10 on
   workloads that never needed the guarantee.
6. Add the observability signals from dimension 15 before the change ships,
   not after the first production deadlock, so contention is visible from
   day one rather than discovered from a support ticket.

Removing or loosening locking discipline once the workload's actual conflict
rate is known.

1. Measure the real conflict rate on the transaction type in question using
   the observability signals from dimension 15. A low measured abort or
   deadlock rate is the signal that the workload may not need pessimistic
   locking at all.
2. For a read-heavy transaction, replace `SELECT ... FOR UPDATE` reads that
   exist only to prevent a stale read, not to protect a subsequent write,
   with a plain read under the engine's default MVCC isolation.
3. For a low-conflict write, introduce a version column and switch the write
   path to optimistic concurrency control. read the version, write with a
   `WHERE version = ?` guard, and retry on a zero-row update rather than
   locking up front.
4. Remove the explicit lock acquisition only after the optimistic path has
   run in production long enough to confirm the retry rate stays low; a
   conflict rate that turns out higher than measured is the signal to revert
   rather than push through with more aggressive retry logic.
5. Keep the lock ordering discipline from step 4 of the introduction path
   even after locking itself is removed from a given code path, since other
   transactions in the system likely still rely on it.

## 15. Testing and verification

Two-phase locking is unusually hard to test with example-based unit tests
alone, because the defects it guards against are timing-dependent
interleavings, not deterministic outputs of a single call.

Easier because of the pattern.

- The invariant the pattern protects, a serializable schedule, gives a
  precise, checkable target. any observed history of committed reads and
  writes must be equivalent to some serial execution order, which is a
  property a test driver can assert mechanically rather than by inspection.
- Because locks are acquired and released through a small, well-defined
  interface, a lock manager's compatibility matrix and phase-transition rule
  can be unit tested in complete isolation from the rest of the database, as
  shown in the code examples below.

Harder because of the pattern.

- Deadlocks and lock-wait timeouts are load-dependent; a test that passes
  reliably at low concurrency can deadlock only once real contention appears,
  which means correctness tests for this pattern must deliberately induce
  concurrency, not merely tolerate it.
- The order in which two transactions' lock requests interleave is
  non-deterministic under a real thread scheduler, so a naive concurrent
  test is flaky by construction unless the interleaving is controlled.

Techniques that apply.

- **Deterministic interleaving injection.** Drive two or more simulated
  transactions through explicit, hand-chosen interleavings of their lock
  requests, one step at a time under a test driver that controls scheduling
  rather than relying on real threads, and assert the resulting schedule is
  conflict-serializable. This is the only reliable way to exercise a specific
  anomaly, a dirty read, a lost update, a phantom, on demand rather than by
  chance.
- **Randomized concurrency stress testing (a form of chaos or fuzz testing
  applied to schedules).** Run many concurrent transactions with randomized
  delays against a real lock manager or database instance, repeatedly, and
  check the invariant holds after every run; this catches interleavings a
  hand-written test would not think to construct, at the cost of
  non-reproducibility unless the random seed is captured.
- **Deadlock injection tests.** Construct the specific two-transaction,
  two-resource cycle shown in dimension 7 deliberately, and assert that the
  deadlock detector or the wound-wait mechanism resolves it within a bounded
  time and that exactly one of the two transactions is aborted, never zero
  and never both.
- **Golden invariant checks over production-shaped data.** After a batch of
  concurrent transactions completes against a test dataset, verify the
  domain invariant directly, "the sum of all account balances equals the
  starting sum", rather than only checking that no exception was thrown,
  since a correctness bug in this pattern typically manifests as a silently
  wrong value, not a crash.

## 16. Observability signals

Locking failures are invisible in application logs unless the database or
the lock manager is explicitly instrumented, because a blocked transaction
looks identical to a slow one from the outside.

What to record.

- A counter of lock waits, labeled by resource or resource class and by lock
  mode, so a hot row or hot table shows up as a spike in one label rather
  than a generalized slowdown.
- A histogram of lock wait duration, labeled the same way. This is the
  primary signal for diagnosing the long-held read lock failure mode from
  dimension 11.
- A counter of lock escalations, where the underlying engine supports them,
  labeled by table. An unexpected rise here is the earliest warning of the
  escalation storm failure mode.
- A counter of deadlocks detected, with the identity or query fingerprint of
  the victim transaction attached, so recurring deadlocks between the same
  two code paths are visible as a repeated pattern rather than isolated
  incidents.
- A gauge of currently held locks per transaction and per resource, useful
  for diagnosing a runaway transaction that is holding far more locks than
  its logical scope should require.

A healthy instance on a dashboard. Lock wait time is low and flat relative to
overall transaction latency, the deadlock counter is near zero and does not
cluster on a small number of resource pairs, and escalation events, if the
engine has them, are rare and correlate only with known bulk operations.

A failing instance. Lock wait duration develops a long tail concentrated on
one resource label, which localizes contention to a specific hot row or
table without reading any application code. A deadlock counter that
repeatedly names the same two query fingerprints points directly at the
inconsistent lock ordering failure mode. An escalation counter that rises
outside of known batch windows points at a statement whose row count crossed
an engine's threshold unexpectedly. A gauge of held locks that grows without
a matching drop at transaction end indicates a transaction that never
committed or aborted, holding its locks indefinitely.

## 17. Security and privacy implications

Two-phase locking is largely a correctness mechanism, not a security
boundary, but it opens two genuine and one adjacent concern.

**Denial of service through lock contention.** Because a lock request blocks
rather than fails, an attacker or a misbehaving client that can open a
long-running transaction and hold a lock on a widely shared resource can
degrade or halt every other transaction that needs the same resource,
without needing to exhaust any conventional resource like CPU or memory
first. Systems exposed to untrusted or low-trust clients should bound
transaction duration and lock wait time explicitly, rather than trusting the
client to behave, and should alert on the lock-wait-duration signal from
dimension 16 as a security-relevant metric, not only a performance one.

**Timing side channels through lock wait latency.** Because the time a
request takes to complete is measurably longer when it must wait for a
conflicting lock, an attacker who can trigger transactions on a shared
resource and measure response latency may be able to infer that another,
otherwise invisible transaction is concurrently touching the same resource,
for example inferring that a specific account or record exists and is
currently being modified. This is a genuine but narrow concern, applicable
mainly to multi-tenant systems sharing lock scope across tenants; the
mitigation is to scope locks so that no cross-tenant resource sharing exists
at the lock granularity in the first place, rather than trying to mask
timing after the fact.

**Deadlock victim selection as an availability lever.** In systems using
priority-, cost-, or age-based deadlock resolution rather than a pure
wound-wait rule, a client that can predictably shape which of its
transactions becomes the deadlock victim may be able to repeatedly force
another, more important transaction to be the one aborted instead. This is
an adjacent concern rather than a direct vulnerability of the pattern
itself, and is worth naming so victim-selection policy is chosen
deliberately rather than left as an unexamined default.

On privacy, the pattern is silent in itself. The rows and resources named in
lock table entries and wait-for graphs can carry sensitive identifiers, an
account number, a customer ID, and where locking telemetry from dimension 16
is exported to a general-purpose observability platform, that telemetry
should be treated as carrying the same sensitivity as the underlying data,
not assumed to be safe because it is only a lock name.

## Code examples

Three languages where the pattern is genuinely idiomatic to implement
directly, because each has native primitives, condition variables and
mutexes, that map onto a lock manager's blocking behavior without a
framework. Go and Rust both show a concurrent lock manager enforcing the
growing and shrinking phases with real goroutines or threads blocking and
being woken. Python shows the same phase enforcement together with a
wound-wait victim-selection function over a wait-for graph, tying directly
to the Cloud Spanner production use in dimension 9. Java is omitted from
this entry because no Java Runtime was available in the environment used to
verify these examples, and shipping an unverified Java sample would violate
the compile-or-state-plainly requirement; the shape would be structurally
identical to the Go example, using `ReentrantLock` and `Condition` in place
of `sync.Mutex` and `sync.Cond`.

### Go

Compiled and run with `go run` against Go's standard toolchain. The manager
tracks each transaction's phase and blocks a conflicting request on a
condition variable until the resource is free.

```go
package main

import (
	"fmt"
	"sync"
)

type LockMode int

const (
	Shared LockMode = iota
	Exclusive
)

func compatible(a, b LockMode) bool {
	return a == Shared && b == Shared
}

type lockEntry struct {
	holders map[string]LockMode
}

type Phase int

const (
	Growing Phase = iota
	Shrinking
)

type LockManager struct {
	mu    sync.Mutex
	cond  *sync.Cond
	locks map[string]*lockEntry
	phase map[string]Phase
	held  map[string]map[string]LockMode
}

func NewLockManager() *LockManager {
	lm := &LockManager{
		locks: make(map[string]*lockEntry),
		phase: make(map[string]Phase),
		held:  make(map[string]map[string]LockMode),
	}
	lm.cond = sync.NewCond(&lm.mu)
	return lm
}

// Acquire blocks until compatible, or returns an error if the transaction
// has already released a lock and entered its shrinking phase.
func (lm *LockManager) Acquire(txn, resource string, mode LockMode) error {
	lm.mu.Lock()
	defer lm.mu.Unlock()

	if lm.phase[txn] == Shrinking {
		return fmt.Errorf("txn %s: cannot acquire %s lock on %s after entering shrinking phase", txn, modeName(mode), resource)
	}

	entry, ok := lm.locks[resource]
	if !ok {
		entry = &lockEntry{holders: make(map[string]LockMode)}
		lm.locks[resource] = entry
	}

	for {
		conflict := false
		for holder, hmode := range entry.holders {
			if holder == txn {
				continue
			}
			if !compatible(mode, hmode) {
				conflict = true
				break
			}
		}
		if !conflict {
			break
		}
		lm.cond.Wait()
	}

	entry.holders[txn] = mode
	if lm.held[txn] == nil {
		lm.held[txn] = make(map[string]LockMode)
	}
	lm.held[txn][resource] = mode
	return nil
}

// Release drops one lock and moves the transaction into its shrinking
// phase, per the two-phase rule: no lock may be acquired after this.
func (lm *LockManager) Release(txn, resource string) {
	lm.mu.Lock()
	defer lm.mu.Unlock()

	entry, ok := lm.locks[resource]
	if !ok {
		return
	}
	delete(entry.holders, txn)
	delete(lm.held[txn], resource)
	lm.phase[txn] = Shrinking
	lm.cond.Broadcast()
}

// Commit releases every lock the transaction still holds at once, which is
// how strict two-phase locking works in practice.
func (lm *LockManager) Commit(txn string) {
	lm.mu.Lock()
	defer lm.mu.Unlock()
	for resource := range lm.held[txn] {
		delete(lm.locks[resource].holders, txn)
	}
	delete(lm.held, txn)
	lm.phase[txn] = Shrinking
	lm.cond.Broadcast()
}

func modeName(m LockMode) string {
	if m == Shared {
		return "S"
	}
	return "X"
}

func main() {
	lm := NewLockManager()

	if err := lm.Acquire("T1", "account:42", Exclusive); err != nil {
		panic(err)
	}
	fmt.Println("T1 holds X on account:42")

	var wg sync.WaitGroup
	wg.Add(1)
	go func() {
		defer wg.Done()
		if err := lm.Acquire("T2", "account:42", Shared); err != nil {
			fmt.Println("T2 error:", err)
			return
		}
		fmt.Println("T2 acquired S on account:42 after T1 released it")
	}()

	lm.Commit("T1")
	wg.Wait()

	if err := lm.Acquire("T3", "account:7", Exclusive); err != nil {
		panic(err)
	}
	lm.Release("T3", "account:7")
	if err := lm.Acquire("T3", "account:9", Exclusive); err != nil {
		fmt.Println("expected violation:", err)
	}
}
```

### Rust

Compiled with `rustc` and run directly. The structure mirrors the Go
example, using a `Mutex` and `Condvar` pair, which is the same primitive
shape the Go implementation uses.

```rust
use std::collections::HashMap;
use std::sync::{Arc, Condvar, Mutex};
use std::thread;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
enum Mode {
    Shared,
    Exclusive,
}

fn compatible(a: Mode, b: Mode) -> bool {
    a == Mode::Shared && b == Mode::Shared
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum Phase {
    Growing,
    Shrinking,
}

struct State {
    holders: HashMap<String, HashMap<String, Mode>>,
    phase: HashMap<String, Phase>,
    held: HashMap<String, HashMap<String, Mode>>,
}

struct LockManager {
    state: Mutex<State>,
    released: Condvar,
}

impl LockManager {
    fn new() -> Self {
        LockManager {
            state: Mutex::new(State {
                holders: HashMap::new(),
                phase: HashMap::new(),
                held: HashMap::new(),
            }),
            released: Condvar::new(),
        }
    }

    // Blocks until compatible; errors if the transaction already released
    // a lock and entered its shrinking phase.
    fn acquire(&self, txn: &str, resource: &str, mode: Mode) -> Result<(), String> {
        let mut guard = self.state.lock().unwrap();
        if guard.phase.get(txn) == Some(&Phase::Shrinking) {
            return Err(format!(
                "txn {txn}: cannot acquire {mode:?} lock on {resource} after entering shrinking phase"
            ));
        }
        loop {
            let conflict = guard
                .holders
                .get(resource)
                .map(|m| m.iter().any(|(h, hm)| h != txn && !compatible(mode, *hm)))
                .unwrap_or(false);
            if !conflict {
                break;
            }
            guard = self.released.wait(guard).unwrap();
        }
        guard
            .holders
            .entry(resource.to_string())
            .or_default()
            .insert(txn.to_string(), mode);
        guard
            .held
            .entry(txn.to_string())
            .or_default()
            .insert(resource.to_string(), mode);
        Ok(())
    }

    // Strict two-phase locking: every held lock is released together at
    // commit, never incrementally during the transaction's run.
    fn commit(&self, txn: &str) {
        let mut guard = self.state.lock().unwrap();
        if let Some(mine) = guard.held.remove(txn) {
            for resource in mine.keys() {
                if let Some(m) = guard.holders.get_mut(resource) {
                    m.remove(txn);
                }
            }
        }
        guard.phase.insert(txn.to_string(), Phase::Shrinking);
        self.released.notify_all();
    }

    fn release(&self, txn: &str, resource: &str) {
        let mut guard = self.state.lock().unwrap();
        if let Some(m) = guard.holders.get_mut(resource) {
            m.remove(txn);
        }
        if let Some(mine) = guard.held.get_mut(txn) {
            mine.remove(resource);
        }
        guard.phase.insert(txn.to_string(), Phase::Shrinking);
        self.released.notify_all();
    }
}

fn main() {
    let lm = Arc::new(LockManager::new());

    lm.acquire("T1", "account:42", Mode::Exclusive).unwrap();
    println!("T1 holds X on account:42");

    let lm2 = Arc::clone(&lm);
    let t2 = thread::spawn(move || match lm2.acquire("T2", "account:42", Mode::Shared) {
        Ok(()) => println!("T2 acquired S on account:42 after T1 released it"),
        Err(e) => println!("T2 error: {e}"),
    });

    lm.commit("T1");
    t2.join().unwrap();

    lm.acquire("T3", "account:7", Mode::Exclusive).unwrap();
    lm.release("T3", "account:7");
    match lm.acquire("T3", "account:9", Mode::Exclusive) {
        Ok(()) => println!("unexpected: acquire should have failed"),
        Err(e) => println!("expected violation: {e}"),
    }
}
```

### Python

Run directly with `python3`. This version adds `find_cycle` and
`wound_wait_victim`, a minimal, directly runnable implementation of the
wound-wait deadlock-avoidance rule documented for Cloud Spanner in
dimension 9, the older transaction wounds the younger one.

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class Mode(Enum):
    SHARED = auto()
    EXCLUSIVE = auto()


def compatible(a: Mode, b: Mode) -> bool:
    return a is Mode.SHARED and b is Mode.SHARED


class Phase(Enum):
    GROWING = auto()
    SHRINKING = auto()


class LockConflict(Exception):
    pass


class TwoPhaseViolation(Exception):
    pass


@dataclass
class LockManager:
    holders: dict[str, dict[str, Mode]] = field(default_factory=dict)
    phase: dict[str, Phase] = field(default_factory=dict)
    held: dict[str, dict[str, Mode]] = field(default_factory=dict)

    def acquire(self, txn: str, resource: str, mode: Mode) -> None:
        if self.phase.get(txn) is Phase.SHRINKING:
            raise TwoPhaseViolation(
                f"txn {txn}: cannot acquire {mode.name} lock on {resource} "
                "after entering shrinking phase"
            )
        entry = self.holders.setdefault(resource, {})
        for holder, held_mode in entry.items():
            if holder != txn and not compatible(mode, held_mode):
                raise LockConflict(
                    f"txn {txn}: {resource} held as {held_mode.name} by {holder}"
                )
        entry[txn] = mode
        self.held.setdefault(txn, {})[resource] = mode

    def commit(self, txn: str) -> None:
        for resource in self.held.pop(txn, {}):
            self.holders[resource].pop(txn, None)
        self.phase[txn] = Phase.SHRINKING

    def release(self, txn: str, resource: str) -> None:
        self.holders.get(resource, {}).pop(txn, None)
        self.held.get(txn, {}).pop(resource, None)
        self.phase[txn] = Phase.SHRINKING


def find_cycle(wait_for: dict[str, str]) -> list[str] | None:
    for start in wait_for:
        seen: list[str] = []
        node = start
        while node in wait_for:
            if node in seen:
                return seen[seen.index(node):]
            seen.append(node)
            node = wait_for[node]
    return None


def wound_wait_victim(wait_for: dict[str, str], age: dict[str, int]) -> str:
    """The older transaction wounds the younger one, so the youngest
    transaction in the cycle is the one aborted."""
    cycle = find_cycle(wait_for)
    if cycle is None:
        raise ValueError("no cycle present, nothing to resolve")
    return max(cycle, key=lambda t: age[t])


def main() -> None:
    lm = LockManager()

    lm.acquire("T1", "account:42", Mode.EXCLUSIVE)
    print("T1 holds X on account:42")

    lm.commit("T1")
    lm.acquire("T2", "account:42", Mode.SHARED)
    print("T2 acquired S on account:42 after T1 released it")

    lm.acquire("T3", "account:7", Mode.EXCLUSIVE)
    lm.release("T3", "account:7")
    try:
        lm.acquire("T3", "account:9", Mode.EXCLUSIVE)
    except TwoPhaseViolation as exc:
        print(f"expected violation: {exc}")

    # T1 waits for T2, T2 waits for T1: a deadlock cycle. T1 is older
    # (age 0 < age 1), so wound-wait aborts the younger transaction, T2.
    wait_for = {"T1": "T2", "T2": "T1"}
    age = {"T1": 0, "T2": 1}
    victim = wound_wait_victim(wait_for, age)
    print(f"deadlock detected, wound-wait aborts: {victim}")


if __name__ == "__main__":
    main()
```

## 18. References

1. K. P. Eswaran, J. N. Gray, R. A. Lorie, I. L. Traiger. "The Notions of
   Consistency and Predicate Locks in a Database System". Communications of
   the ACM, vol. 19, no. 11, November 1976, pp. 624 to 633.
   https://dl.acm.org/doi/10.1145/360363.360369
   Verified 2026-08-02. Source of the pattern's name, its origin, and the
   growing-shrinking phase rule proved to guarantee serializability.
2. PostgreSQL Global Development Group. "PostgreSQL 18 Documentation",
   chapter 13, "Concurrency Control", section 13.3, "Explicit Locking".
   https://www.postgresql.org/docs/current/explicit-locking.html
   Verified 2026-08-02. Source for the table-level lock mode set, the
   compatibility rules, and the statement that PostgreSQL does not escalate
   row locks into table locks.
3. Oracle Corporation. "MySQL 9.7 Reference Manual", section 17.7.1, "InnoDB
   Locking", and section 17.7.4, "Locking Reads".
   https://dev.mysql.com/doc/en/innodb-locking.html
   Verified 2026-08-02. Source for InnoDB's stated design combining
   multi-versioning with two-phase locking, and for next-key locking under
   `REPEATABLE READ`.
4. Microsoft. "SQL Server Transaction Locking and Row Versioning Guide",
   section "Lock Escalation".
   https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-transaction-locking-and-row-versioning-guide
   Verified 2026-08-02. Source for the approximately 5,000-lock escalation
   threshold and the retry-at-1,250-new-locks behavior.
5. Google Cloud. "Concurrency control | Spanner | Google Cloud
   Documentation".
   https://docs.cloud.google.com/spanner/docs/concurrency-control
   Verified 2026-08-02. Source for Spanner's pessimistic, lock-based
   concurrency control and its use of the wound-wait algorithm to resolve
   lock conflicts by transaction age.
6. IBM. "Db2 for Linux, UNIX, and Windows Knowledge Center", topic "Lock
   escalation".
   https://www.ibm.com/docs/en/db2/12.1?topic=locking-lock-escalation
   Verified 2026-08-02. Source for Db2's memory-pressure-triggered lock
   escalation as a second, independently documented production instance of
   the mechanism.
