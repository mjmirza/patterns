---
name: ACID
slug: acid
family: 04-principles-and-laws
category: Principle
aliases: [ACID Properties, ACID Transactions, Transactional Guarantees]
first_described: "Haerder and Reuter 1983 (acronym), Gray 1981 (concept)"
maturity: canonical
related: [cap-theorem, single-source-of-truth, fail-fast, saga, circuit-breaker]
incompatible_with: []
verified: 2026-08-02
---

# ACID

## 1. Name, aliases, and lineage

ACID is the acronym for Atomicity, Consistency, Isolation, and Durability, the
four properties a database transaction is expected to hold. The acronym itself
was coined by Theo Haerder and Andreas Reuter in "Principles of
Transaction-Oriented Database Recovery," ACM Computing Surveys, volume 15,
issue 4, 1983, pages 287 to 317, DOI 10.1145/289.291
([ACM Digital Library record](https://dl.acm.org/doi/10.1145/289.291),
verified 2026-08-02). The paper set out to give transaction recovery a
consistent vocabulary, and the four-letter word for the properties a recovery
scheme has to preserve stuck.

The underlying concept predates the acronym by two years. Jim Gray, then at
Tandem Computers, described the transaction as the unit that groups operations
into an all-or-nothing outcome in "The Transaction Concept. Virtues and
Limitations," an invited paper at the Very Large Data Bases conference, VLDB
'81, Proceedings of the Seventh International Conference on Very Large Data
Bases, volume 7, pages 144 to 154, also issued as Tandem Technical Report TR
81.3 ([Tandem TR 81.3, hosted by the author's personal
site](https://jimgray.azurewebsites.net/papers/thetransactionconcept.pdf),
verified 2026-08-02). Gray's paper names atomicity, consistency, and durability
explicitly, and discusses isolation under the heading of concurrency control
without yet giving it the fourth letter of a tidy acronym. Two years later
Haerder and Reuter supplied that letter, and the industry has used ACID as a
single word ever since.

There is no serious contest over the name or the attribution. Every
transaction-processing textbook and every relational database manual repeats
the same two citations, and the SQL standard, ISO/IEC 9075, defines
transaction isolation levels that operationalize the third letter without
disputing the acronym's origin.

## 2. Problem and context

A database serves many concurrent operations against shared, durable state. An
application groups several reads and writes into one logical unit of work, a
transaction, because the operations only make sense together. A bank transfer
debits one account and credits another. An order-placement writes a new row to
an orders table and decrements a row in an inventory table. If the transfer
debits the source account and then the process crashes before it credits the
destination, the money has vanished. If two transfers run at the same time
against the same account and each reads the balance before the other writes
its update, one transfer's effect is silently lost, a classic lost update. If
the database loses a committed transaction's effect when the machine reboots
after a power failure, every promise made to the caller before the crash was a
lie.

ACID is the contract a database engine offers so that application code does
not have to solve any of those problems itself. The context in which this
contract matters is any system where more than one writer can touch the same
data at overlapping times, and where the cost of a torn write, a lost update,
or a vanished commit is unacceptable. It applies most directly inside a single
database instance, and by extension, with real cost, to a group of operations
that must be treated as one unit across more than one database or more than
one network node.

## 3. Forces

**Correctness against concurrency and failure.** Every property in the acronym
exists to close a specific failure window. Atomicity closes the window between
a partial write and a crash. Consistency closes the window between a
constraint and a caller who does not check it. Isolation closes the window
between two transactions racing on the same rows. Durability closes the window
between a commit acknowledgement and a power loss. Reasoning about each
property separately is the only tractable way to reason about the whole.

**Throughput against isolation strength.** The strongest isolation level,
serializable, is also the one that most restricts how many transactions can
run at once without conflicting, because it has to behave as if transactions
ran one after another. Weaker levels let more work proceed concurrently at the
cost of admitting specific classes of anomaly. This is judgement, not a
sourced fact, and it is the single most consequential trade-off a team makes
when it picks a default isolation level for a service.

**Latency against durability guarantee.** A commit is only durable once its
effect survives the failure model the system promises to tolerate, most often
an `fsync` to a local disk or a quorum acknowledgement from replicated
storage. Waiting for that acknowledgement adds latency to every commit. A
system that returns success before the write is actually durable trades a
faster response for a data-loss window on crash, and that trade is sometimes
made deliberately, and sometimes made by accident through a misconfigured
write-back cache.

**Scope against feasibility, single node versus distributed.** ACID was
designed for a single database engine that owns its own log and its own lock
table. Extending the same four guarantees across independent nodes connected
by an unreliable network is a materially harder problem, governed by a
different set of constraints described in dimension 4 and connected to the
CAP theorem (`cap-theorem`) in dimension 13. A team that assumes distributed
ACID is free because single-node ACID is free is making the most common
mistake this entry documents.

**Operability against implementation complexity.** Write-ahead logging,
multiversion storage, deadlock detection, and two-phase commit are all
mechanisms invented to deliver ACID properties, and each one adds moving parts
an operator has to understand when something goes wrong at 3 a.m. A
database's ACID guarantee is a promise made on the operator's behalf by the
engine's authors, and the operator inherits the debugging surface of whatever
mechanism the engine chose.

## 4. Applicability and non-applicability

Reach for a fully ACID transactional store when the following hold.

- Correctness of the aggregate state matters more than raw write throughput,
  for example financial ledgers, inventory counts, seat reservations, or
  anything where "the total must always reconcile" is a business requirement,
  not a nice-to-have.
- Multiple operations must succeed or fail together and there is no
  acceptable intermediate state a reader could observe, for example writing
  an order row and decrementing stock in the same unit of work.
- The data and the transaction fit comfortably inside a single database
  instance or a single well-bounded cluster, so the cost described in
  dimension 3's scope trade-off stays contained.
- Readers need a guarantee about what they see relative to concurrent
  writers, and "eventually correct" is not good enough for the use case, for
  example displaying an account balance that must never show a transient
  negative value a concurrent transfer would have prevented.
- Regulatory or audit requirements demand a durable, ordered, recoverable
  record of every committed change, which is exactly what the write-ahead log
  behind atomicity and durability already produces as a side effect.

Do not reach for full ACID transactions, or accept the throughput and latency
cost of the strongest isolation level, when the following hold.

- The workload is made up mostly of independent, high-volume writes that
  never need to be read back together as one unit, for example raw event
  ingestion, telemetry, or click logs, where an append-only or
  eventually-consistent store removes the coordination cost entirely.
- The system already spans multiple independently owned services or
  databases and a distributed transaction would couple their availability
  together; a saga (`saga`) or an outbox pattern that trades
  immediate atomicity for eventual consistency is usually the better fit,
  because it does not make every participating service's uptime a dependency
  of every other's.
- The data model is a cache or a derived read-view rebuilt from an
  authoritative source, so losing or corrupting it costs nothing beyond a
  rebuild, and the cost of transactional guarantees would be paid for no
  benefit.
- The team cannot tolerate the latency of the isolation level correctness
  actually requires, and is tempted to weaken isolation silently instead of
  redesigning the workload; this trades a known, reasoned cost for an unknown
  and undocumented one, which is strictly worse, and is the misuse pattern
  described in dimension 11.
- The scale requirement genuinely exceeds what a single ACID-compliant
  cluster can serve and the team has not yet reached for a system, such as
  Google Spanner, that pays the distributed-transaction cost explicitly and
  deliberately (dimension 9), rather than reaching for ad hoc, partial
  consistency that nobody signed off on.

## 5. Structure

ACID is not a design pattern with classes and collaborators in the
Gang-of-Four sense. It is a contract implemented by a small number of
cooperating engine components, and naming those components is the honest
equivalent of dimension 5 for a principle.

- **The transaction manager** is the component that opens a transaction,
  tracks its identifier, and decides whether it ultimately commits or aborts.
  It is the participant that owns atomicity, because it is the only component
  with the authority to make the all-or-nothing decision.
- **The write-ahead log (WAL)** is an append-only, durable record of every
  change a transaction makes, written and flushed to stable storage before
  the corresponding data page is modified in place. It is the mechanism
  behind both atomicity, because an incomplete transaction can be undone by
  replaying its log entries backward, and durability, because a committed
  transaction can be redone from the log even if the data pages themselves
  were never flushed before a crash.
- **The concurrency control component**, most often either a lock manager
  implementing two-phase locking or a multiversion concurrency control
  (MVCC) subsystem that keeps multiple historical versions of each row, is
  the participant responsible for isolation. It decides which concurrent
  transactions may see which versions of which rows, and it detects or
  prevents the anomalies named in dimension 8.
- **The constraint checker** enforces the schema's integrity rules, foreign
  keys, unique indexes, check constraints, and triggers, at commit time. It
  is the participant responsible for consistency in the narrow database sense
  used inside this acronym, meaning the database moves only between states
  that satisfy its own declared rules, not the broader meaning of
  "eventually consistent" used in distributed systems.
- **The recovery manager** runs on restart after a crash. It reads the log,
  undoes the effects of transactions that never committed, and redoes the
  effects of transactions that committed but whose data pages had not yet
  been flushed to disk. It is the component that makes durability true in
  practice rather than true only on paper.
- **The client or application transaction**, the caller that issues `BEGIN`,
  a sequence of reads and writes, and either `COMMIT` or `ROLLBACK`, is the
  participant whose intent the other five exist to serve honestly.

## 6. ASCII structure diagram

```
                       +-----------------------+
   client / caller --> |   Transaction Manager  |
   BEGIN / COMMIT       |  owns atomicity, tracks|
   / ROLLBACK           |  txn id and outcome    |
                       +----+---------+----------+
                            |         |
              writes go     |         | reads/writes routed
              through log   |         | through concurrency
              before pages  v         v control first
                       +--------+  +-------------------+
                       |  WAL   |  | Concurrency Control|
                       | append |  | locks or MVCC      |
                       | only   |  | owns isolation      |
                       +---+----+  +---------+----------+
                           |                  |
                           v                  v
                     +-----------+     +-------------+
                     |  Data     | <-> | Constraint   |
                     |  Pages    |     | Checker      |
                     | (on disk) |     | owns "C"     |
                     +-----+-----+     +-------------+
                           |
                     crash / restart
                           v
                     +-----------+
                     | Recovery  |
                     | Manager   |
                     | undo/redo |
                     | owns "D"  |
                     +-----------+
```

## 7. Dynamics

```
Happy path, single transaction, committed.

client        txn mgr        WAL          data pages     constraint chk
  | BEGIN        |             |               |                |
  |-------------->|             |               |                |
  |  UPDATE       |             |               |                |
  |-------------->| log(before, after) -------> |                |
  |               |             | flush()       |                |
  |               |             |-------------->|                |
  |               |             |               | apply in place |
  |  COMMIT       |             |               |                |
  |-------------->| check constraints ------------------------->|
  |               |             |               |     OK        |
  |               |<-------------------------------------------|
  |               | log(COMMIT) |               |                |
  |               |------------>|               |                |
  |               |  fsync()    |               |                |
  |               |------------>|               |                |
  | ack, committed|             |               |                |
  |<--------------|             |               |                |

Crash recovery on restart, after a mid-flight crash.

recovery mgr scans WAL from last checkpoint forward.
   for each txn found without a COMMIT record, UNDO its writes.
   for each txn found WITH a COMMIT record but pages not yet
   flushed at crash time, REDO its writes.
   database is now identical to the moment of the last
   durable commit, no partial transaction is visible.
```

## 8. Implementation variants

**Two-phase locking (2PL) for isolation.** Each transaction acquires locks
before touching a row and releases none of them until it commits or aborts,
which is what makes the schedule serializable. Strict 2PL, the variant nearly
every production engine uses, additionally holds write locks until commit
specifically, which also avoids chained aborts across other waiting transactions. The cost is blocking and,
without a deadlock detector, indefinite waits; most engines pair 2PL with a
wait-for graph and abort the younger transaction on a detected cycle.

**Multiversion concurrency control (MVCC) for isolation.** Rather than
blocking readers behind writer locks, the engine keeps multiple timestamped
versions of each row and gives every transaction a consistent snapshot to
read from, taken at the transaction's start (or, for serializable snapshot
isolation, extended with conflict detection at commit time). PostgreSQL,
Oracle, and MySQL's InnoDB engine all use MVCC as their primary concurrency
control mechanism, and PostgreSQL's own documentation states the choice
directly, that Read Uncommitted is mapped to Read Committed because that "is
the only sensible way to map the standard isolation levels to PostgreSQL's
multiversion concurrency control architecture"
([PostgreSQL 17 Documentation, Chapter 13, Concurrency
Control](https://www.postgresql.org/docs/current/transaction-iso.html),
verified 2026-08-02).

**Write-ahead logging for atomicity and durability.** The mechanism described
in dimension 5, near-universal across relational engines. SQLite implements
an alternate rollback-journal variant by default, where the journal holds the
original page content and the atomic commit point is the deletion of the
journal file itself, a fact the SQLite documentation states plainly, that
"deleting a file is not really an atomic operation, but it appears to be from
the point of view of a user process," and that after a crash SQLite checks
whether the journal still exists to decide whether to roll a transaction back
([SQLite, Atomic Commit In
SQLite](https://www.sqlite.org/atomiccommit.html), verified 2026-08-02).
SQLite also supports write-ahead logging as an alternative journal mode, using
a different mechanism to reach the same atomic-commit guarantee, as the same
page notes explicitly.

**Two-phase commit (2PC) for atomicity across nodes.** When a transaction
spans more than one resource manager, a coordinator asks every participant to
prepare, vote to commit or abort, in phase one, and only tells them to
actually commit in phase two once every participant has voted yes. This is
the mechanism behind the X/Open XA standard that many application servers and
message brokers implement for distributed transactions. Its well-known
weakness is that it blocks if the coordinator crashes between the two phases,
a limitation Jim Gray and Leslie Lamport addressed by showing that classic
two-phase commit is a degenerate, single-point-of-failure case of a
Paxos-based commit protocol, in "Consensus on Transaction Commit," ACM
Transactions on Database Systems, volume 31, issue 1, March 2006, pages 133
to 160, DOI 10.1145/1132863.1132867
([ACM Digital Library record](https://dl.acm.org/doi/10.1145/1132863.1132867),
verified 2026-08-02).

**Optimistic concurrency control.** Instead of locking on read, the
transaction proceeds without locks and validates at commit time that no
conflicting write occurred since it started, aborting and retrying if a
conflict is found. This variant favours low-contention workloads where
locking overhead would otherwise outweigh any benefit, at the cost of wasted
work on abort under high contention.

**Distributed ACID via synchronized clocks.** Google Spanner extends ACID
transactional guarantees, specifically external consistency, a form of
strict serializability across the whole distributed system, by exposing
clock uncertainty directly through a TrueTime API backed by GPS and atomic
clocks, so that commit timestamps can be ordered correctly even across
data centers. The original paper states that Spanner's serialization order
satisfies external consistency, meaning "if a transaction T1 commits before
another transaction T2 starts, then T1's commit timestamp is smaller than
T2's," and that Spanner is the first system to provide this at global scale
([J.C. Corbett et al., "Spanner. Google's Globally-Distributed Database,"
Proceedings of OSDI '12](https://research.google.com/archive/spanner-osdi2012.pdf),
verified 2026-08-02).

## 9. Known production uses

- **PostgreSQL** implements full ACID transactions with a choice of four
  standard SQL isolation levels (Read Uncommitted mapped to Read Committed,
  Read Committed, Repeatable Read, Serializable), the last two built on
  MVCC-based snapshot isolation with additional predicate-lock-based conflict
  detection for true serializability
  ([PostgreSQL 17 Documentation, Chapter 13, Transaction
  Isolation](https://www.postgresql.org/docs/current/transaction-iso.html),
  verified 2026-08-02).
- **MySQL's InnoDB storage engine** is ACID-compliant by default and supports
  the same four SQL-standard isolation levels through an MVCC implementation,
  with Repeatable Read as its own default, a stronger default than most
  other engines choose, documented in the MySQL Reference Manual chapter on
  the InnoDB transaction model
  ([MySQL 8.4 Reference Manual, Section 17.7.2.1, Transaction
  Isolation Levels](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html),
  verified 2026-08-02).
- **SQLite** guarantees full ACID transactions even though it is an
  embedded, file-based engine with no server process, using either the
  rollback-journal mechanism or write-ahead logging described in dimension 8,
  and its own documentation is explicit that the file-deletion atomicity
  trick is the mechanism that makes single-file commits atomic
  ([SQLite, Atomic Commit In
  SQLite](https://www.sqlite.org/atomiccommit.html), verified 2026-08-02).
- **Google Spanner** extends ACID guarantees, including external
  consistency, across a globally distributed, multi-datacenter deployment
  using the TrueTime API, and the OSDI 2012 paper describing it is one of the
  most cited systems papers of the decade
  ([J.C. Corbett et al., "Spanner. Google's Globally-Distributed
  Database," OSDI '12](https://research.google.com/archive/spanner-osdi2012.pdf),
  verified 2026-08-02).
- **Oracle Database** has offered full ACID transactions with MVCC-based
  read consistency (Oracle calls its default level "Read Committed" and also
  offers "Serializable") since long before the term MVCC was common industry
  vocabulary, documented across every edition of the Oracle Database Concepts
  and Oracle Database Development Guide manuals under the heading of data
  concurrency and consistency.
- **The X/Open XA specification**, implemented by application servers such as
  Java EE's Java Transaction API (JTA) and message brokers, formalizes the
  two-phase commit protocol from dimension 8 as an industry-standard
  interface for coordinating ACID transactions across independent resource
  managers, an interface still shipped in current Jakarta EE application
  servers.

## 10. Consequences

Positive.

- Application code is freed from reasoning about partial failure, torn
  writes, and interleaved reads by hand; the database absorbs that
  complexity once, correctly, on behalf of every caller.
- Financial and inventory-style invariants (an account balance never goes
  negative, a seat is never double-booked) can be expressed as constraints
  and isolation guarantees instead of as ad hoc application-level locking,
  which is easy to get subtly wrong.
- A durable, ordered log of every committed change is a natural byproduct of
  the atomicity and durability mechanism, and that log is directly reusable
  for audit trails, point-in-time recovery, and change-data-capture
  pipelines, at almost no extra engineering cost.
- Serializable isolation, when chosen, gives the strongest possible
  correctness guarantee available to concurrent transactions. the observable
  outcome is always equivalent to some serial execution, which removes an
  entire category of race-condition bugs from the application's
  responsibility.

Negative.

- The strongest isolation levels reduce achievable concurrency, because
  transactions that would conflict under serializable semantics must wait,
  abort and retry, or be reordered, and that cost grows with contention on
  hot rows.
- Durability requires a synchronous flush or a synchronous replication
  acknowledgement before a commit can be reported to the caller, and that
  round trip is latency the caller pays on every write, not a one-time cost.
- Distributed ACID, via two-phase commit or a system like Spanner, couples
  the availability of every participant together; if one participant is
  unreachable during the prepare phase, the whole transaction cannot
  proceed, which trades local availability for global correctness, a trade
  that is not free and is not always wanted (see dimension 13 and the CAP
  theorem entry).
- The vocabulary itself is a source of confusion, because the "C" in ACID
  (application-level constraint satisfaction) and the "C" in CAP
  (linearizable single-copy semantics) name genuinely different properties
  despite sharing a letter, and engineers who conflate them make
  architecture decisions on a false equivalence.

## 11. Failure modes and misuse

Judgement, drawn from operational experience with transactional systems
rather than from a single citable source.

| Symptom | Cause | Fix |
|---|---|---|
| Intermittent lost updates under load, a counter or balance occasionally reflects only one of two concurrent writes | The application reads a value, computes a new value in its own process, then writes it back, without the read and write happening inside one transaction at an isolation level strong enough to detect the conflict, most often Read Committed used where Repeatable Read or Serializable was needed | Wrap the read-modify-write in a single transaction at Repeatable Read or Serializable, or use an atomic `UPDATE ... SET x = x + 1` that never leaves the database round trip, or use explicit row-level locking (`SELECT ... FOR UPDATE`) around the read |
| Deadlock errors returned to the application under moderate concurrent load, transactions failing with a database-reported deadlock code | Two or more transactions acquire the same set of locks in a different order, so each waits on a lock the other holds; the database's deadlock detector picks a victim and aborts it | Standardize a consistent lock acquisition order across all code paths that touch the same tables, keep transactions short so lock hold time is minimal, and have the application retry on the specific deadlock error code rather than surfacing it to the end user |
| A long-running report or batch job appears to block or slow down unrelated, short online transactions | The batch job holds a transaction open for minutes while reading, and under Repeatable Read or Serializable the engine either has to hold locks that block writers, or, under MVCC, has to retain old row versions for the duration, bloating storage and slowing vacuum or garbage collection | Run long reads at Read Committed if strict repeatability is not actually required, break the batch into smaller committed chunks, or run it against a replica so it never competes for the primary's lock table or version-retention budget |
| A distributed transaction across two services occasionally hangs indefinitely, or one service is unavailable and an unrelated service's writes are blocked | Two-phase commit was used to couple the availability of independently owned services, and the coordinator crashed between the prepare and commit phases, or a participant is down during prepare, which is the documented blocking limitation of classic 2PC | Replace the distributed ACID transaction with a saga (`saga`) that performs each step with its own local transaction and a compensating action on failure, so no single service's downtime blocks another's writes |
| "Serializable" is enabled and throughput collapses under contention that used to run fine at Read Committed | Serializable isolation, whether lock-based or snapshot-based with predicate locking, is designed to abort transactions that would violate a serial ordering, and high write contention on the same rows produces frequent aborts that the application must retry | Confirm the workload genuinely needs serializable guarantees before defaulting to it; for many workloads Repeatable Read plus a small number of explicit locks on the specific invariant that matters delivers correctness at a fraction of the abort rate |
| An "eventually consistent" system is described in its own documentation as ACID, and downstream teams build correctness-critical logic on that claim | A team conflates the durability and ordering promises of an event log or a message queue with the transactional guarantees of a database, because both use the word "durable" or "atomic" in their own, narrower sense | Read the specific consistency model documented for the actual technology in use rather than inferring it from the word "durable" or "atomic" appearing in its marketing copy; ask specifically what isolation level, if any, the system provides for concurrent readers and writers |

## 12. Trade-off matrix

Compared against the named alternatives for building correctness into a
system with concurrent writers.

| Approach | Correctness guarantee | Availability under partition or node failure | Latency per write | Operational complexity |
|---|---|---|---|---|
| ACID transaction, single node | Strongest, up to full serializability | Fails closed if the node is down, no availability during that outage | One round trip plus the durability flush, no cross-node coordination | Moderate, engine owns WAL, locking, recovery |
| ACID via two-phase commit, multiple nodes | Strong, but degrades to blocking on coordinator failure (dimension 8, Gray and Lamport 2006) | Low, any unreachable participant blocks the whole transaction | Multiple round trips, at least two phases across every participant | High, requires a coordinator, participant recovery logic, and XA-style resource managers |
| Saga (compensating transactions) | Weaker, eventual consistency with explicit compensation on failure, no cross-service isolation guarantee | High, each step is a local transaction against a single, available service | Comparable to a single ACID write per step, no cross-service round trip | High in a different dimension, the team must design and test every compensating action |
| CAP-theorem-favoring AP system (`cap-theorem`) | Weakest by design, stale or conflicting reads possible during a partition, resolved by convergence rules | Highest, every reachable node keeps serving during a partition | Lowest, no cross-replica coordination required per write | Low per node, but pushes conflict-resolution complexity into the application |
| Spanner-style distributed ACID with TrueTime | Strongest available at global scale, external consistency across data centers | Moderate, tolerates node failure within a Paxos group but pays commit-wait latency for clock uncertainty | Higher than a single node, bounded by TrueTime's uncertainty interval | Very high, requires specialized clock infrastructure most teams do not operate themselves |

## 13. Related and incompatible patterns

- **CAP theorem** (`cap-theorem`) governs the same territory ACID does but at
  a different scope, distributed systems under network partition rather than
  a single engine's concurrency control. The two are frequently confused
  because both reuse the letter "C" for a different property; ACID's
  consistency is about application-defined integrity constraints, CAP's
  consistency is about linearizable single-copy semantics across replicas.
  A system can be fully ACID internally on each node and still make an
  availability-versus-consistency trade under CAP when a partition occurs
  between nodes.
- **Saga** composes with ACID rather than replacing it. each individual step
  of a saga is usually its own local ACID transaction against one service's
  database, and the saga pattern exists specifically to avoid needing a
  single ACID transaction that spans every step.
- **Circuit breaker** is complementary at the failure-handling layer. When a
  distributed ACID coordinator or a remote participant becomes unreachable, a
  circuit breaker around the call to that participant prevents one failure from spreading to callers
  while the underlying transaction protocol resolves or times out.
- **Single Source of Truth** (`single-source-of-truth`) is the design
  principle ACID's consistency and isolation guarantees exist to protect. if
  a system has one authoritative record for a piece of state, ACID is the
  mechanism that keeps concurrent writers from corrupting that single
  record.
- **Fail fast** (`fail-fast`) shares ACID's philosophy at a different layer.
  Both prefer an explicit, immediate rejection, an aborted transaction, a
  raised exception, over allowing a system to proceed in a state it cannot
  guarantee is correct.
- No pattern in this repository is directly incompatible with ACID in the
  sense of being unable to coexist in the same system. The genuine tension is
  with architectural styles, principally eventual-consistency-first,
  AP-leaning distributed designs, that deliberately trade away ACID's
  guarantees for availability or latency, described fully in dimensions 3, 4,
  and 12.

## 14. Refactoring path in and out

Introducing transactional integrity into code that lacks it.

1. Identify every place in the codebase where more than one write against
   the same data store must succeed or fail together, by tracing the
   business invariant backward from its statement, for example "an order
   always has matching inventory decremented," to the code paths that could
   violate it.
2. Wrap those write sequences in an explicit transaction boundary
   (`BEGIN`/`COMMIT`/`ROLLBACK`, or the equivalent transaction API for the
   language and ORM in use), and confirm the underlying store actually
   defaults to a connection-per-request model that does not silently
   auto-commit between statements.
3. Choose the weakest isolation level that still prevents the specific
   anomaly the invariant depends on, rather than defaulting to serializable
   everywhere; identify the anomaly by name (dirty read, non-repeatable
   read, phantom read, lost update, write skew) and select the isolation
   level documented to prevent it.
4. Add integration tests that actually exercise concurrency, spawning two or
   more transactions against the same rows and asserting the invariant holds
   under the chosen isolation level, because a single-threaded test suite
   cannot expose an isolation bug (see dimension 15).
5. For any write sequence that spans more than one independently deployed
   service or database, do not reach for a distributed ACID transaction by
   default; evaluate the saga alternative in dimension 12 first, and only
   fall back to two-phase commit when the coupling cost it imposes on
   availability is genuinely acceptable to every participating team.

Removing or weakening transactional scope once it has proven too costly.

1. Confirm, with a real production metric, which specific symptom from
   dimension 11's trade-off (lock contention, abort rate, or cross-service
   coupling) is the actual cost being paid, rather than weakening isolation
   on suspicion.
2. If the cost is abort rate under serializable isolation, narrow the
   transaction's scope first, shortening the window it holds locks or a
   snapshot open, before lowering the isolation level; a narrower
   serializable transaction often outperforms a wider Repeatable Read one.
3. If the cost is genuinely isolation-level throughput, step down exactly
   one level at a time (Serializable to Repeatable Read, or Repeatable Read
   to Read Committed) and re-verify, with the concurrency test from step 4
   above, that no depended-upon anomaly reappears.
4. If the cost is cross-service coupling from a distributed transaction,
   migrate the flow to a saga one step at a time, starting with the
   least-critical step, and write the compensating action and its own test
   before removing the corresponding branch of the two-phase commit.
5. Never remove a transaction boundary or lower an isolation level as a
   quick fix for a timeout or a deadlock error without first identifying
   which anomaly the original boundary was preventing; a suppressed error is
   not evidence the invariant it protected no longer matters.

## 15. Testing and verification

Judgement, drawn from database testing practice.

ACID's atomicity and durability are the easiest of the four properties to
test directly. kill the process (or the container, or the VM) mid-transaction
in an integration test, restart the database, and assert that either every
write from the killed transaction is visible or none of them are. A test
setup that can inject a crash between the log flush and the data-page flush
is the strongest possible test of durability, and most engines' own test
suites include exactly this kind of fault injection, which is why the SQLite
project documents its own crash-simulation test setup in the atomic-commit
page cited in dimension 8.

Consistency, in the narrow database sense of constraint satisfaction, is
tested the same way any invariant is tested. write a test that attempts to
violate the constraint directly, a duplicate unique key, an orphaned foreign
key, a check constraint violation, and assert the write is rejected and no
partial state is left behind.

Isolation is the hardest property to test, because a bug only manifests under
genuine concurrency and most application test suites run single-threaded.
The reliable technique is to spawn two or more transactions from separate
connections, deliberately interleave their statements using explicit
synchronization points (a second connection does not proceed past its own
read until the first connection's write has committed, or is held open in a
still-uncommitted state), and assert the outcome matches what the chosen
isolation level promises rather than what a naive single-threaded mental
model would predict. This is precisely the technique used by jepsen-style
testing tools and by database vendors' own isolation conformance suites, and
it is the only reliable way to catch a lost-update or write-skew bug before
it reaches production, because the bug is invisible under low concurrency and
appears only under real contention.

Distributed ACID protocols additionally need fault injection at the network
level, dropping or delaying messages between the coordinator and a
participant during the prepare phase specifically, to verify the system
either blocks as documented (classic 2PC) or makes progress despite the
fault (a Paxos-based commit protocol), rather than silently committing on one
side and aborting on the other.

## 16. Observability signals

Judgement, drawn from operating transactional databases in production.

A healthy transactional workload shows a low and stable transaction abort
rate, low average lock wait time, a write-ahead log flush latency that tracks
the underlying storage's fsync latency and does not grow over time, and a
replication lag, where replicas exist, that stays within the bounds the
application's read-your-writes or durability requirements demand.

Signals that indicate ACID mechanics are under strain rather than functioning
normally include a rising rate of deadlock errors or serialization-failure
errors surfaced to the application, indicating either genuine contention
growth or a lock-ordering bug introduced by a recent change; a growing gap
between the write-ahead log's current position and the point the recovery
manager would have to replay from on a restart, which lengthens
crash-recovery time and is itself worth alerting on directly; unbounded
growth in a database's version or undo storage, which under MVCC indicates a
long-running transaction is preventing old row versions from being freed;
and, for any system that uses two-phase commit, a growing count of
transactions stuck in the prepared but not yet committed or aborted state,
which is the direct, measurable symptom of the coordinator-crash blocking
failure mode named in dimension 8 and dimension 11.

## 17. Security and privacy implications

The write-ahead log or rollback journal that makes atomicity and durability
possible is, by construction, a record of every value written to the
database, including values from transactions that were later rolled back and
never became visible to any reader. That log therefore has to be protected
with at least the same access controls and encryption-at-rest posture as the
database files themselves, because an attacker who can read the log can
recover data the application logic believes was never committed or was
deleted, a distinction the application layer cannot enforce once the bytes
exist on disk in log form.

Isolation levels have a data-visibility dimension beyond correctness. A
transaction running under Read Uncommitted, where an engine permits it, can
observe another transaction's uncommitted, in-flight write, which means an
attacker or a buggy internal service running at that isolation level could
observe sensitive data mid-write that the writer intended to roll back and
never expose; this is a reason, independent of correctness, to avoid Read
Uncommitted for any workload touching regulated or sensitive data.

Distributed ACID protocols widen the network attack surface relative to a
single-node transaction, because the prepare and commit messages exchanged
between a coordinator and its participants carry transaction content across
the network and must themselves be authenticated and encrypted in transit;
a compromised or spoofed participant in a two-phase commit could otherwise
vote to commit or abort a transaction it was never authorized to see.

Backups and point-in-time recovery, both natural byproducts of the durability
mechanism, are themselves a data-exfiltration surface if not access-controlled
as strictly as the live database, since a restored backup grants an attacker
read access to every row that was ever committed within the retention window,
independent of whatever row-level access controls the live application
enforces.

## 18. References

- T. Haerder and A. Reuter, "Principles of Transaction-Oriented Database
  Recovery," ACM Computing Surveys, volume 15, issue 4, 1983, pages 287 to
  317, DOI 10.1145/289.291.
  [https://dl.acm.org/doi/10.1145/289.291](https://dl.acm.org/doi/10.1145/289.291),
  verified 2026-08-02.
- J. Gray, "The Transaction Concept. Virtues and Limitations," Proceedings of
  the Seventh International Conference on Very Large Data Bases (VLDB '81),
  volume 7, pages 144 to 154, also issued as Tandem Technical Report TR 81.3.
  [https://jimgray.azurewebsites.net/papers/thetransactionconcept.pdf](https://jimgray.azurewebsites.net/papers/thetransactionconcept.pdf),
  verified 2026-08-02.
- J. Gray and L. Lamport, "Consensus on Transaction Commit," ACM Transactions
  on Database Systems, volume 31, issue 1, March 2006, pages 133 to 160, DOI
  10.1145/1132863.1132867.
  [https://dl.acm.org/doi/10.1145/1132863.1132867](https://dl.acm.org/doi/10.1145/1132863.1132867),
  verified 2026-08-02.
- J.C. Corbett et al., "Spanner. Google's Globally-Distributed Database,"
  Proceedings of the 10th USENIX Symposium on Operating Systems Design and
  Implementation (OSDI '12), 2012.
  [https://research.google.com/archive/spanner-osdi2012.pdf](https://research.google.com/archive/spanner-osdi2012.pdf),
  verified 2026-08-02.
- PostgreSQL Global Development Group, "PostgreSQL 17 Documentation, Chapter
  13, Concurrency Control."
  [https://www.postgresql.org/docs/current/transaction-iso.html](https://www.postgresql.org/docs/current/transaction-iso.html),
  verified 2026-08-02.
- Oracle Corporation, "MySQL 8.4 Reference Manual, Section 17.7.2.1,
  Transaction Isolation Levels."
  [https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html),
  verified 2026-08-02.
- SQLite Consortium, "Atomic Commit In SQLite."
  [https://www.sqlite.org/atomiccommit.html](https://www.sqlite.org/atomiccommit.html),
  verified 2026-08-02.

## Code examples

Three languages, three different properties made concrete. TypeScript for
atomicity and durability via a write-ahead log and crash replay, Python for
consistency via a checked, all-or-nothing transaction, Go for isolation via
a lost-update race with and without a lock. Java, C#, and Kotlin are omitted
here in the interest of budget, not because the pattern does not translate;
any language with a mutex or a transactional client library expresses the
same three mechanisms.

### TypeScript, durability via write-ahead log and crash replay

```typescript
// Durability via a write-ahead log, replayed after a simulated crash.
//
// The store applies a write to its in-memory page only after the log
// entry has been appended. On restart, replayLog walks the log and
// reapplies every committed entry, so a value survives even though the
// in-memory page that received it before the crash is gone.

type LogEntry = { txnId: number; key: string; value: number; committed: boolean };

class WalStore {
  private log: LogEntry[] = [];
  private pages: Map<string, number> = new Map();

  write(txnId: number, key: string, value: number): void {
    this.log.push({ txnId, key, value, committed: false });
  }

  commit(txnId: number): void {
    for (const entry of this.log) {
      if (entry.txnId === txnId) {
        entry.committed = true;
        this.pages.set(entry.key, entry.value);
      }
    }
  }

  crash(): WalStore {
    const survivingLog = this.log.slice();
    const fresh = new WalStore();
    fresh.log = survivingLog;
    fresh.pages = new Map();
    return fresh;
  }

  recover(): void {
    for (const entry of this.log) {
      if (entry.committed) {
        this.pages.set(entry.key, entry.value);
      }
    }
  }

  read(key: string): number | undefined {
    return this.pages.get(key);
  }
}

function demo(): void {
  let store = new WalStore();

  store.write(1, "balance:alice", 70);
  store.commit(1);

  store.write(2, "balance:bob", 999);

  console.log(`before crash, alice=${store.read("balance:alice")} bob=${store.read("balance:bob")}`);

  store = store.crash();
  console.log(`immediately after crash, alice=${store.read("balance:alice")} bob=${store.read("balance:bob")}`);

  store.recover();
  console.log(`after recovery, alice=${store.read("balance:alice")} bob=${store.read("balance:bob")}`);
}

demo();
```

Run and output, confirmed with `npx tsc --strict --target es2020 --module commonjs acid.ts && node acid.js`.

```
before crash, alice=70 bob=undefined
immediately after crash, alice=undefined bob=undefined
after recovery, alice=70 bob=undefined
```

Bob's write was staged in the log but never committed before the crash, so
recovery correctly does not restore it, and Alice's committed write survives
the crash even though the in-memory page holding it was destroyed.

### Python, consistency via a checked, all-or-nothing transaction

```python
"""Atomicity and consistency for a bank transfer, no partial commit.

A transaction context manager stages every write. It only applies the
staged writes to the real store if a declared invariant still holds,
otherwise it discards the whole batch, so the caller never observes a
half-applied transfer.
"""
from contextlib import contextmanager


class Account:
    def __init__(self, name, balance):
        self.name = name
        self.balance = balance


class Ledger:
    def __init__(self):
        self.accounts = {}

    def open_account(self, name, balance):
        self.accounts[name] = Account(name, balance)

    @contextmanager
    def transaction(self, invariant):
        staged = {name: acct.balance for name, acct in self.accounts.items()}

        class Handle:
            def set_balance(_, name, value):
                staged[name] = value

        handle = Handle()
        yield handle
        if not invariant(staged):
            raise ValueError("invariant violated, transaction rolled back")
        for name, value in staged.items():
            self.accounts[name].balance = value

    def transfer(self, src, dst, amount):
        total_before = sum(a.balance for a in self.accounts.values())

        def invariant(staged):
            no_negative = all(v >= 0 for v in staged.values())
            total_conserved = sum(staged.values()) == total_before
            return no_negative and total_conserved

        with self.transaction(invariant) as txn:
            txn.set_balance(src, self.accounts[src].balance - amount)
            txn.set_balance(dst, self.accounts[dst].balance + amount)


def demo():
    ledger = Ledger()
    ledger.open_account("alice", 100)
    ledger.open_account("bob", 20)

    ledger.transfer("alice", "bob", 30)
    print(f"after valid transfer alice={ledger.accounts['alice'].balance} "
          f"bob={ledger.accounts['bob'].balance}")

    try:
        ledger.transfer("alice", "bob", 1000)
    except ValueError as exc:
        print(f"rejected: {exc}")

    print(f"after rejected transfer alice={ledger.accounts['alice'].balance} "
          f"bob={ledger.accounts['bob'].balance}")


if __name__ == "__main__":
    demo()
```

Run and output, confirmed with `python3 acid_py.py`.

```
after valid transfer alice=70 bob=50
rejected: invariant violated, transaction rolled back
after rejected transfer alice=70 bob=50
```

The second transfer would have taken Alice's balance negative, so the
invariant check inside the transaction context manager rejects the whole
staged batch before any account balance is touched, which is what
consistency in the ACID sense guarantees, the database never moves into a
state that violates its own declared rules.

### Go, isolation via a lost-update race with and without a lock

```go
// Isolation preventing a lost update, two writers racing on one balance.
//
// unsafeIncrement has no locking, so concurrent read-modify-write cycles
// interleave and lose updates. safeIncrement holds a mutex across the
// whole read-modify-write, matching what a database's row lock or MVCC
// conflict check achieves for one row.
package main

import (
	"fmt"
	"sync"
)

type Account struct {
	mu      sync.Mutex
	balance int
}

func unsafeIncrement(a *Account, amount int) {
	current := a.balance
	current = current + amount
	a.balance = current
}

func safeIncrement(a *Account, amount int) {
	a.mu.Lock()
	defer a.mu.Unlock()
	current := a.balance
	current = current + amount
	a.balance = current
}

func run(increment func(*Account, int), writers int, perWriter int) int {
	acct := &Account{balance: 0}
	var wg sync.WaitGroup
	wg.Add(writers)
	for i := 0; i < writers; i++ {
		go func() {
			defer wg.Done()
			for j := 0; j < perWriter; j++ {
				increment(acct, 1)
			}
		}()
	}
	wg.Wait()
	return acct.balance
}

func main() {
	writers, perWriter := 50, 200
	expected := writers * perWriter

	unsafeResult := run(unsafeIncrement, writers, perWriter)
	fmt.Printf("unsafe (no isolation)  expected=%d got=%d lostUpdates=%v\n",
		expected, unsafeResult, unsafeResult != expected)

	safeResult := run(safeIncrement, writers, perWriter)
	fmt.Printf("safe (mutex isolation) expected=%d got=%d lostUpdates=%v\n",
		expected, safeResult, safeResult != expected)
}
```

Run and output, confirmed with `go run main.go`.

```
unsafe (no isolation)  expected=10000 got=8053 lostUpdates=true
safe (mutex isolation) expected=10000 got=10000 lostUpdates=false
```

Fifty goroutines each increment a shared balance two hundred times.
Without isolation the read-modify-write cycles interleave and thousands
of increments are silently lost, exactly the anomaly a database's row
lock, or an MVCC engine's write-write conflict detection, exists to
prevent; the mutex-protected version reproduces what that isolation
guarantee delivers.
