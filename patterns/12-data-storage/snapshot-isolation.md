---
name: Snapshot Isolation
slug: snapshot-isolation
family: 12-data-storage
category: Concurrency Control
aliases: [SI, Multiversion Snapshot Isolation, Optimistic Multiversion Concurrency Control]
first_described: "Berenson, Bernstein, Gray, Melton, O'Neil, O'Neil 1995"
maturity: canonical
related: [multiversion-concurrency-control, optimistic-concurrency-control, two-phase-locking, event-sourcing, serializable-snapshot-isolation]
incompatible_with: [strict-two-phase-locking]
verified: 2026-08-02
---

# Snapshot Isolation

## 1. Name, aliases, and lineage

The canonical name is Snapshot Isolation, usually abbreviated SI. The pattern
was formally named and defined in Hal Berenson, Philip A. Bernstein, Jim Gray,
Jim Melton, Elizabeth O'Neil, and Patrick O'Neil, "A Critique of ANSI SQL
Isolation Levels", Proceedings of the 1995 ACM SIGMOD International Conference
on Management of Data, pages 1 to 10, DOI 10.1145/223784.223785 (verified
2026-08-16, citation record confirmed via the ACM Digital Library entry at
https://dl.acm.org/doi/10.1145/223784.223785, and via the paper's public
mirror at https://arxiv.org/pdf/cs/0701157). The paper's stated purpose was to
show that the ANSI SQL-92 standard's phenomena-based definitions of isolation
levels (dirty read, non-repeatable read, phantom) were ambiguous enough that a
database could claim SERIALIZABLE while permitting an anomaly the standard's
own prose seemed to forbid. Snapshot Isolation was introduced in that paper as
a precise, implementation-grounded level that several commercial systems
already shipped under other names, and the paper gave it a formal
history-graph definition so vendors could be compared honestly.

Before 1995 the same mechanism existed under vendor-specific names.
InterBase, and later Firebird which forked from it, called it multigenerational
architecture. Oracle called its transaction-level consistency SERIALIZABLE,
which the Berenson paper singles out by name as an isolation level that,
despite the label, does not prevent the write skew anomaly that true
serializability forbids, because Oracle's SERIALIZABLE is Snapshot Isolation
under a name borrowed from the stricter standard level. The alias
Multiversion Snapshot Isolation is used in academic papers to distinguish it
from single-version optimistic schemes. Optimistic Multiversion Concurrency
Control appears in systems literature when authors want to stress the two
ingredients separately, multiversioning for reads and optimistic validation
for writes, rather than treat SI as one indivisible primitive.

A distinction worth making at the outset, because catalogs conflate it
constantly. Multiversion Concurrency Control, MVCC, is the storage mechanism,
keeping several timestamped versions of each row so readers never block
writers. Snapshot Isolation is a specific concurrency control policy built on
top of MVCC storage, one that fixes a transaction's visible snapshot at the
start of the transaction and detects write-write conflicts at commit time.
A system can implement MVCC storage and still choose a different policy on
top of it. For instance, PostgreSQL's READ COMMITTED level uses the same
multiversion storage as its REPEATABLE READ level but takes a fresh snapshot
per statement instead of per transaction (PostgreSQL documentation, section
13.2, https://www.postgresql.org/docs/current/transaction-iso.html, verified
2026-08-16). So MVCC is the substrate. SI is one thing you can build on it.

## 2. Problem and context

A transaction needs to read a consistent view of the database while other
transactions are concurrently reading and writing the same rows, and the
system needs this without making readers wait for writers or writers wait for
readers. The classic pessimistic answer, two-phase locking with shared read
locks, achieves consistency by making a reader hold a lock long enough to
block a concurrent writer from touching the same row, and vice versa. That
works, but under any real workload with long-running reports, analytics
queries, or simply many short transactions touching overlapping rows, lock
contention becomes the throughput ceiling. A report that scans a million rows
with shared locks either blocks every writer that touches those rows for the
duration of the scan, or the database has to escalate the report's isolation
down to READ COMMITTED and accept that its own numbers might not add up
internally.

The context in which this problem becomes acute is any workload with a mix of
long read transactions and frequent short writes on the same tables, which
describes most OLTP systems with embedded analytics, most e-commerce
catalogs during a sale, and essentially every system that runs a nightly
report against a live table. The forces below explain what a designer is
actually trading when they reach for Snapshot Isolation instead of locking or
instead of full serializability, and dimension 4 states plainly where SI is
the wrong tool even though it looks attractive on paper.

## 3. Forces

This is judgement, weighing the pressures a designer actually feels when
choosing between concurrency control strategies.

Read and write concurrency pulls toward multiversioning. If a system's
dominant cost is contention between readers and writers on hot rows, SI
removes that contention entirely. A writer never blocks a reader, and a
reader never blocks a writer, because a reader is served from an old version
while the writer produces a new one. This is the pattern's central appeal and
the reason essentially every production relational database shipped it or a
close variant of it by the mid 2000s.

Correctness under concurrent writes pulls the other way. SI is not
serializable. It admits an anomaly called write skew, where two transactions
each read a value the other is about to change, each write based on that
stale read, and both commit successfully because they touched disjoint sets
of rows even though their combined effect violates an invariant that spans
both rows. A designer who assumes SI gives them the same guarantee as
SERIALIZABLE will eventually ship a bug that a locking scheme would have
prevented, and the bug is the kind that only surfaces under real concurrent
load, which makes it expensive to find.

Storage cost and garbage collection pull against keeping many versions
indefinitely. Every update under SI leaves behind an old version that some
long-running transaction might still need to see. A system has to track the
oldest active transaction's snapshot timestamp and refuse to reclaim any
version newer than that, which means one long-lived transaction, an
abandoned connection holding a transaction open, or a slow analytics query,
can bloat storage across the whole table set it touches. PostgreSQL's
documented behaviour of dead tuple accumulation under long transactions and
the operational need to run VACUUM is a direct, named consequence of this
force (PostgreSQL documentation section 24.1.5, Preventing Transaction ID
Wraparound Failures, https://www.postgresql.org/docs/current/routine-vacuuming.html,
verified 2026-08-16, describing how open transactions and the tuples they
must be able to see delay reclamation).

Operability and predictability of failure pull toward first-committer-wins
validation being simple to reason about, but they cut against it being easy
to explain to application authors. A write-write conflict under SI surfaces
as a runtime error the application must retry, which is a different failure
mode than lock waiting. Teams accustomed to lock-based systems, where a
conflicting transaction simply waits, are frequently surprised the first time
they see a serialization failure under load, and application code that does
not retry on that specific error class will silently lose writes from the
user's point of view. The write appears accepted by the client but the
transaction actually aborted.

Cost of coordination in a distributed setting pulls strongly toward SI over
strict serializability, because assigning a transaction a single global
snapshot timestamp is a coordination-light operation compared to the
distributed locking or the certifier-based coordination that full
serializability across shards would require. This is the force that led
Google Spanner and CockroachDB toward mechanisms that start from an SI-like
foundation and add machinery on top to close the write skew hole rather than
falling back to distributed two-phase locking.

## 4. Applicability and non-applicability

Reach for Snapshot Isolation when the workload has a substantial mix of
long-running or read-heavy transactions alongside writers, and blocking
either category on the other would be the dominant cost. Reach for it when
the application's invariants are enforced per-row or via a single row's
uniqueness constraint, so that write-write conflicts on the same row are the
only conflict class that matters and cross-row invariants are rare or
enforced some other way. Reach for it when read consistency within a single
transaction, seeing the database as it looked at one instant, is the actual
requirement, which covers most reporting, most read-your-writes UI flows, and
most consistency needs that developers describe informally as "the numbers
should add up".

Do not reach for it when an invariant spans two or more rows that different
transactions can update independently and where each transaction only reads
one of the rows before writing the other, because that is exactly the shape
of write skew and SI will not catch it. The canonical example is a
constraint like "at least one of these two doctors must be on call", where
transaction A reads doctor 1's on-call flag, sees doctor 2 is on call, and
turns off doctor 1, while transaction B does the symmetric check and turns
off doctor 2, and both commit under SI because they wrote disjoint rows
(Berenson et al. 1995, section 4, defines write skew and this exact
scenario, verified against the paper's abstract and section structure via
https://arxiv.org/pdf/cs/0701157, 2026-08-16).

Do not reach for it as a substitute for SERIALIZABLE when correctness must be
provably equivalent to some serial order of transactions, for example
financial ledger postings that must never permit two concurrent transfers to
overdraw an account by working around each other's row locks. Use a
serializability-providing mechanism instead, either true SERIALIZABLE
isolation, an explicit application-level lock or SELECT FOR UPDATE on the
constraining rows, or a certifier scheme such as Serializable Snapshot
Isolation, described in dimension 13.

Do not reach for it when the workload is dominated by short, single-row
writes with almost no concurrent reads spanning multiple statements, because
the multiversioning machinery, snapshot bookkeeping, and garbage collection
overhead buys nothing there and a simpler locking scheme with less storage
overhead will do the same job more cheaply.

Do not reach for it in an embedded or single-writer system with no read
concurrency to protect, where the coordination it solves does not exist in
the first place, adding versioning storage for a problem that has no
concurrent readers to serve.

## 5. Structure

Snapshot Isolation has four participants.

The Snapshot Store is the versioned storage layer. It holds, for every key or
row, a list of committed versions, each tagged with the commit timestamp of
the transaction that produced it. Its responsibility is to answer the question
"what was the value of this row as of timestamp T" and to publish a new
version atomically when a transaction commits.

The Transaction Manager assigns each transaction a begin timestamp when it
starts, and a commit timestamp when it successfully commits, drawn from a
single monotonically increasing counter shared by the whole system. Its
responsibility is to make these two timestamps meaningful ordering points
that every transaction and every reader agree on.

The Read Set implicitly, and the Write Set explicitly, belong to each active
transaction. The write set is a private, buffered accumulation of the
transaction's own writes, invisible to any other transaction until commit.
Reads made by the transaction are served from the snapshot store as of the
transaction's begin timestamp, except that a transaction always sees its own
buffered writes.

The Commit Validator is the component that decides, at commit time, whether
the transaction's write set conflicts with any version committed after the
transaction's begin timestamp. The two documented validation policies are
first-committer-wins, where the first transaction to commit a conflicting
write wins and later ones abort, and first-updater-wins, where a transaction
that acquires a write lock on the contested row first will wait for the
other transaction to finish and then decide based on whether that other
transaction committed. Both are described as the two alternatives PostgreSQL
supports depending on isolation level (PostgreSQL documentation, section
13.2.2, https://www.postgresql.org/docs/current/transaction-iso.html, verified
2026-08-16). First-committer-wins is what the code in dimension 6 and 7
implements, because it is the simpler of the two to reason about and the one
the original Berenson et al. paper's formal history-graph definition is built
around.

## 6. ASCII structure diagram

```
+----------------------------------------------------------+
|                     Transaction Manager                  |
|   assigns begin_ts on start, commit_ts on commit          |
|   monotonic counter shared across all transactions        |
+------------------------+-----------------------------------+
                          |
        +-----------------+------------------+
        |                                    |
        v                                    v
+----------------+                   +----------------+
| Transaction A   |                   | Transaction B   |
| begin_ts = 5    |                   | begin_ts = 5    |
|                 |                   |                 |
| read set  <-----+---read at ts 5----+-----> write set  |
| write set (buf) |                   | write set (buf) |
+--------+--------+                   +--------+--------+
         |                                     |
         | commit()                            | commit()
         v                                     v
+----------------------------------------------------------+
|                    Commit Validator                      |
|  for each key in write_set                                |
|    if latest_commit_ts(key) > begin_ts, ABORT              |
|  else assign commit_ts, publish versions atomically       |
+------------------------+-----------------------------------+
                          |
                          v
+----------------------------------------------------------+
|                     Snapshot Store                       |
|  key "balance" -> [ (v=100, ts=1), (v=70, ts=6) ]         |
|  key "status"  -> [ (v="new", ts=1), (v="paid", ts=4) ]   |
|  read(key, ts) returns the newest version with             |
|  commit_ts <= ts                                          |
+----------------------------------------------------------+
```

## 7. Dynamics

A transaction under Snapshot Isolation moves through four phases, and the
diagram below traces the two-writer conflict scenario that the code samples
in dimension 8 exercise directly.

```
Time -->

Transaction Manager clock  ....2........................
Store "balance" state      100 --------------------------

T1 begin(ts=2)  read(balance) -> 100
T2 begin(ts=2)  read(balance) -> 100

T1 write(balance, 100-30=70)      [buffered locally, invisible to T2]
T2 write(balance, 100-50=50)      [buffered locally, invisible to T1]

T1 commit()
    validator checks latest_commit_ts(balance) == 1, begin_ts == 2
    1 <= 2, no conflict -> publish (value=70, commit_ts=3)
    T1 SUCCEEDS

T2 commit()
    validator checks latest_commit_ts(balance) == 3, begin_ts == 2
    3 > 2  -> CONFLICT, ABORT
    T2 FAILS, application must retry

Final store state for "balance"  [ (100, ts=1), (70, ts=3) ]
Correct. Only one of the two withdrawals actually applied.
```

Two things about this trace matter beyond the happy path. First, both
transactions read the same value, 100, because both took their snapshot at
the same begin timestamp before either committed, which is the entire point.
A transaction never sees a partial or in-flight state from a concurrent
transaction. Second, the conflict is detected purely by comparing timestamps
on the contested key, not by re-checking every row either transaction
touched elsewhere, which is why validation is cheap relative to full
optimistic concurrency control schemes that must certify against the entire
read set to guarantee serializability, see dimension 13's discussion of
Serializable Snapshot Isolation for what that stricter check costs.

A read-only transaction never enters the validator at all. It takes a
begin timestamp, serves every read from that snapshot, and simply ends,
which is why SI is described as never blocking readers and never being
blocked by writers, a documented property of PostgreSQL's snapshot-based
REPEATABLE READ (PostgreSQL documentation section 13.2.2, verified
2026-08-16) and of SQL Server's SNAPSHOT isolation level, which states
plainly that "SNAPSHOT transactions reading data don't block other
transactions from writing data. Transactions writing data don't block
SNAPSHOT transactions from reading data" (Microsoft Learn, SET TRANSACTION
ISOLATION LEVEL, https://learn.microsoft.com/en-us/sql/t-sql/statements/set-transaction-isolation-level-transact-sql,
verified 2026-08-16).

## 8. Implementation variants

Timestamp-ordered multiversion storage with commit-time validation is the
variant shown in dimension 6 and implemented in dimension 9's code, and it
is the variant most textbooks present because it maps directly onto the
Berenson et al. formal definition. Every row carries a list of versions
tagged by commit timestamp, and validation compares the write set against
the latest committed version of each contested key.

Row-versioning with a global transaction sequence number is SQL Server's
concrete implementation. SQL Server's SNAPSHOT isolation level stores prior
row images in the version store in tempdb, and a transaction reads the
version of a row as it existed at the start of the transaction, with the
documentation stating explicitly that "the effect is as if the statements in
a transaction get a snapshot of the committed data as it existed at the
start of the transaction" (Microsoft Learn, SET TRANSACTION ISOLATION LEVEL,
verified 2026-08-16, cited above). The same page documents that
READ_COMMITTED_SNAPSHOT, a related but distinct database option, gives each
individual statement its own fresh snapshot rather than giving the whole
transaction one snapshot, which is the statement-level variant discussed
next.

Statement-level snapshot instead of transaction-level snapshot is the
variant PostgreSQL uses for its READ COMMITTED level and SQL Server uses for
READ_COMMITTED_SNAPSHOT mode. Each individual SQL statement gets its own
snapshot taken at the moment the statement starts, rather than the whole
transaction sharing one snapshot from its first statement. This gives up the
transaction-wide consistent view SI promises, in exchange for seeing more
recent commits from other transactions between statements, and it is a
deliberate, named, weaker level, not full Snapshot Isolation, even though it
shares the same versioned storage engine underneath (PostgreSQL
documentation section 13.2.1, verified 2026-08-16).

Undo-log based multiversioning is Oracle's approach and MySQL InnoDB's
approach, where instead of keeping forward versions in the main table,
the engine keeps the old version in an undo segment or undo log and
reconstructs a consistent read image by applying undo records backward from
the current row to the version that existed at the reader's snapshot time.
Oracle's documentation describes this directly. "The database copies current
data blocks to a new buffer and applies undo data to reconstruct previous
versions of the blocks. These reconstructed data blocks are called
consistent read (CR) clones" (Oracle Database 19c Concepts, Data
Concurrency and Consistency, https://docs.oracle.com/en/database/oracle/oracle-database/19/cncpt/data-concurrency-and-consistency.html,
verified 2026-08-16). This is functionally equivalent to forward-versioned
storage for read purposes, but the space and compaction trade-offs differ.
Undo segments are reclaimed once no active transaction needs them rather
than sitting in the primary table's heap.

Optimistic concurrency control at the application layer is the variant that
appears without any database-level SI support, where the application reads
a row along with a version number or last-modified timestamp, and on write
issues an UPDATE with a WHERE clause checking that version number, aborting
the application transaction if zero rows were affected. This reproduces the
first-committer-wins check of SI manually, at the granularity of individual
statements rather than whole transactions, and is the common pattern in
systems built on storage engines, key-value stores or simple SQL setups,
that never expose a true SI isolation level.

Language-idiomatic note. None of the three languages in dimension 9 change
the shape of this pattern, because Snapshot Isolation is fundamentally a
data structure and a validation algorithm, not a language feature that a
closure or an interface would replace. The interesting variation is in the
concurrency primitives used to make the transaction manager's clock and the
store's version lists safe under real parallelism, which the code samples
intentionally omit locking for in order to keep the algorithm legible, and
which dimension 15 addresses directly.

## 9. Known production uses

PostgreSQL implements its REPEATABLE READ isolation level as Snapshot
Isolation. The documentation states this by name. "The Repeatable Read
isolation level is implemented using a technique known in academic database
literature and in some other database products as Snapshot Isolation"
(PostgreSQL documentation, section 13.2.2, Repeatable Read Isolation Level,
https://www.postgresql.org/docs/current/transaction-iso.html, verified
2026-08-16). It further documents that this level prevents every anomaly the
SQL standard lists except serialization anomalies, meaning write skew is
possible, which matches the pattern's documented weakness in dimension 4.

Microsoft SQL Server implements SI directly as the SNAPSHOT isolation level,
selectable with SET TRANSACTION ISOLATION LEVEL SNAPSHOT once the
ALLOW_SNAPSHOT_ISOLATION database option is enabled. The documentation
states data read under this level "is the transactionally consistent version
of the data that existed at the start of the transaction" and that
"SNAPSHOT transactions reading data don't block other transactions from
writing data" (Microsoft Learn, SET TRANSACTION ISOLATION LEVEL, verified
2026-08-16, cited above). SQL Server additionally offers
READ_COMMITTED_SNAPSHOT, the statement-level variant from dimension 8, and
this mode is the default on Azure SQL Database, per the same page.

Oracle Database's default READ COMMITTED and its SERIALIZABLE isolation
levels are both built on the same multiversion consistency model, using undo
segments to reconstruct consistent-read images so that "a writer never
blocks a reader" (Oracle Database 19c Concepts, Data Concurrency and
Consistency, verified 2026-08-16, cited above). Oracle's own documentation
describes SERIALIZABLE as seeing "only changes committed at the time the
transaction, not the query, began and changes made by the transaction
itself" and raising ORA-08177 on a write conflict, which is the same
first-committer-wins signature SI uses elsewhere, though Oracle's public
documentation does not itself use the term Snapshot Isolation to describe
this level. That identification is a widely repeated analysis in the
academic literature following Berenson et al., and is engineering judgement
attributed to that body of work rather than an Oracle-documented fact.

MongoDB implements a form of Snapshot Isolation for multi-document
transactions via the read concern level named "snapshot". Its documentation
states that this "returns data from a snapshot of majority committed data if
the transaction commits with write concern majority", and specifically that
for transactions spanning a sharded cluster the "snapshot view of the data
is synchronized across shards", contrasting this with weaker read concerns
that cannot make that cross-shard guarantee (MongoDB Manual, Transactions,
https://www.mongodb.com/docs/manual/core/transactions/, verified 2026-08-16).

CockroachDB is a documented example of a system that deliberately does not
expose plain Snapshot Isolation as an option, and states so explicitly. Its
SERIALIZABLE level is described as "stronger than the ANSI SQL READ
UNCOMMITTED, READ COMMITTED, and REPEATABLE READ levels, as well as the
SNAPSHOT level" (CockroachDB documentation, Transactions,
https://docs.cockroachlabs.com/docs/stable/transactions, verified
2026-08-16). This is cited here as the negative production case, a system
that studied the write skew hole in SI and chose to close it by default
rather than offer SI as a selectable level, which is directly relevant
context for dimension 13.

## 10. Consequences

Positive.

Readers never block writers and writers never block readers, because each
reads from an immutable historical version rather than contending for a lock
on the current row, a property multiple vendors document by name as shown in
dimension 9.

Read consistency within a transaction is strong and simple to reason about
for application authors. Everything the transaction reads reflects one
consistent instant, which eliminates non-repeatable reads and phantom reads
entirely, a stronger guarantee than the ANSI SQL standard technically
requires at the REPEATABLE READ level, as PostgreSQL's documentation notes
explicitly (verified 2026-08-16, cited above).

Write conflicts are detected cheaply, at commit time, by comparing only the
transaction's own write set against recently committed versions, rather than
requiring the system to hold locks proactively for the transaction's entire
duration, which lets long read-only transactions coexist with a busy write
workload without either side paying a locking tax.

Negative.

Write skew is possible and, because it depends on the specific interleaving
of two concurrent transactions reading disjoint rows and writing disjoint
rows, it is genuinely hard to catch in testing, code review, or staging
environments with low concurrency, and it typically first appears under
production load, which is engineering judgement grounded in the
Berenson et al. formal definition of the anomaly. Dimension 11 discusses this
in operational terms.

Storage and garbage collection cost scales with the longest-running active
transaction, because the system must retain every version that any active
snapshot could still need to read, so one abandoned connection or one slow
report can force the retention of stale versions across many tables, a
documented operational concern in PostgreSQL's VACUUM and transaction ID
wraparound guidance (verified 2026-08-16, cited above).

Application code must handle serialization failures as a distinct, expected
error class and retry, which is an additional discipline compared to
lock-based systems where a conflicting transaction simply waits its turn
rather than failing outright, and teams that omit this retry logic will
silently drop writes from the end user's perspective.

## 11. Failure modes and misuse

Symptom, two account balances or two inventory counts that individually
look correct but together violate a business rule that spans both rows, for
example both being decremented past a combined floor that should have
prevented one of the decrements. Cause, write skew. Both transactions read
the pair of rows before either wrote, computed independently, and each
wrote only its own row, so neither transaction's write set overlapped the
other's and the commit validator found nothing to reject. Fix, either lock
the rows the invariant depends on explicitly, using SELECT FOR UPDATE or the
equivalent, so the second transaction is forced to wait and re-read, or move
to a serializable isolation level such as Serializable Snapshot Isolation
that certifies read-write dependencies as well as write-write ones.

Symptom, table and index bloat that grows unbounded, VACUUM or an
equivalent maintenance job taking longer over time, or the database
eventually refusing writes due to transaction ID exhaustion. Cause, a
long-running transaction, an idle connection left open in a transaction, or
a repeatable-read report query that runs for hours, is holding the oldest
active snapshot timestamp fixed, which prevents the storage engine from
reclaiming any version newer than that timestamp anywhere in the database,
not just in the tables that transaction touches. Fix, bound the lifetime of
any transaction that uses SI-level isolation, alert on long-running or idle
in transaction sessions, and prefer READ COMMITTED with statement-level
snapshots for workloads that do not actually need a whole-transaction
consistent view.

Symptom, an application under moderate concurrent load intermittently
throws a serialization or update-conflict exception on writes that,
individually, look like they should have succeeded, and the failure rate
rises sharply with concurrent write volume on the same rows. Cause, the
application is treating SI's commit-time conflict detection as an edge case
rather than an expected outcome, has no retry loop around the commit, and
the rows in question are a hot key, a shared counter, a single "cart total"
row, or similar, that many concurrent transactions all try to update.
Fix, either reduce write contention on the hot key by restructuring the data
model, for example an append-only ledger of deltas summed on read instead of
a single mutable counter row, or add a bounded retry loop with backoff
specifically for the conflict error code the database returns.

Symptom, a developer asserts in code review or documentation that
SERIALIZABLE and SNAPSHOT ISOLATION mean the same thing on this database, and
the team later discovers a write skew bug in production that they believed
their isolation level made impossible. Cause, conflating a vendor's
isolation level name with its actual formal guarantee, which the Berenson et
al. paper's original motivation was specifically to prevent, since the ANSI
standard's phenomena-based definitions allowed exactly this kind of
vendor-label confusion. Fix, verify, per database, whether the level named
SERIALIZABLE in that product's documentation is true serializability or
Snapshot Isolation under that name, and write the answer down in the team's
own operational documentation rather than assuming it from the label.

## 12. Trade-off matrix

| Force | Snapshot Isolation | Strict Two-Phase Locking | Serializable Snapshot Isolation |
|---|---|---|---|
| Reader vs writer blocking | Never blocks either direction | Readers and writers block each other on shared rows | Never blocks either direction, same as plain SI |
| Guarantees full serializability | No, write skew is possible | Yes, when locks cover the full read and write set | Yes, certifies read-write conflicts on top of SI |
| Write conflict detection cost | Cheap, compares only the write set at commit | No detection needed, conflicts prevented by waiting | More expensive, tracks read-write dependency edges |
| Long read transaction cost | Cheap for the reader, costly for storage retention | Expensive, holds shared locks for the read's duration | Same storage retention cost as plain SI |
| Application failure handling | Must retry on write-write conflict | Must handle lock wait timeouts or deadlocks | Must retry on either write-write or read-write conflict |
| Coordination cost in a distributed system | Low, one snapshot timestamp per transaction | High, distributed lock management across nodes | Moderate, needs dependency tracking across nodes |

## 13. Related and incompatible patterns

Multiversion Concurrency Control is the storage foundation Snapshot
Isolation is built on, and the two are frequently conflated in casual
writing even though MVCC is a mechanism that supports several different
isolation policies, SI being one, statement-level READ COMMITTED being
another, as PostgreSQL's own documentation demonstrates by implementing both
levels on the same versioned storage.

Optimistic Concurrency Control is the general family SI belongs to, sharing
its core idea of proceeding without locks and validating at commit time.
Plain optimistic concurrency control at the single-row level, using a
version column and a conditional update, is the manual, application-level
reproduction of what SI's commit validator does automatically across an
entire transaction's write set.

Two-Phase Locking is the pessimistic alternative and is functionally
incompatible with Snapshot Isolation as a combined strategy within one
transaction's execution model, because SI's entire value proposition is
that readers do not take locks, while strict two-phase locking requires
exactly that. A system can offer both as separate isolation levels for
different transactions to choose between, which is what SQL Server does by
offering SNAPSHOT alongside SERIALIZABLE implemented via locking, but a
single transaction does not run under both mechanisms at once.

Serializable Snapshot Isolation, SSI, is the pattern that composes with SI
to close the write skew hole, adding a dependency-tracking layer that
detects when a transaction has a read-write conflict, called a
rw-antidependency in the literature, with a concurrently committing
transaction, and aborts one of them even though their write sets do not
overlap. PostgreSQL's true SERIALIZABLE level is implemented this way,
layered on top of the same snapshot mechanism its REPEATABLE READ level uses
(PostgreSQL documentation section 13.2.3, verified 2026-08-16). The academic
source for this technique is Michael J. Cahill, Uwe Rohm, and Alan D.
Fekete, "Serializable Isolation for Snapshot Databases", ACM Transactions on
Database Systems, volume 34, issue 4, 2009, referenced here as the named
source for SSI. Verification of this citation was not independently
performed in this pass and is flagged in dimension 18 as unverified.

Event Sourcing is loosely related in spirit, both patterns keep a history of
states rather than mutating in place, but they solve different problems.
Event Sourcing's version history is a durable, application-visible audit
log that is the system of record, while SI's version history is an
internal implementation detail the storage engine manages and garbage
collects, invisible to the application beyond its effect on read
consistency.

## 14. Refactoring path in and out

Introducing Snapshot Isolation into a system that currently runs under
READ COMMITTED with lock-based writes is usually a configuration change
rather than a code change, since the database engines discussed in
dimension 9 already implement SI as a selectable isolation level. The
practical migration path has three steps. First, audit every multi-row
invariant in the application, using the applicability checklist in
dimension 4, and identify any that could be violated by write skew, because
this audit is the step teams skip and later regret. Second, for each
invariant found, add an explicit lock, a SELECT FOR UPDATE or the
platform's equivalent, on the rows the invariant depends on, so those
specific transactions are protected even though the isolation level as a
whole permits write skew. Third, switch the isolation level for the
relevant transactions and add a retry loop around commit that specifically
catches the platform's serialization or update-conflict error and retries
the whole transaction body from the start, since simply retrying the last
statement is not correct. The transaction's snapshot itself is stale and
needs to be reacquired.

Removing Snapshot Isolation, moving back to READ COMMITTED or to explicit
locking, is warranted when the storage cost of long-lived versions has
become an operational problem that outweighs the concurrency benefit, or
when the application has accumulated enough SELECT FOR UPDATE locks around
every invariant that SI's blocking-avoidance benefit has already been given
up in practice and the extra versioning machinery is pure overhead. The
refactor is the reverse of the introduction. Drop the isolation level back
to READ COMMITTED, verify that every place that relied on transaction-wide
consistency, reading the same value twice within one transaction and
expecting it not to change, has been either removed or replaced with an
explicit lock, and load test the change under realistic concurrency before
shipping it, because a subtle reliance on snapshot consistency is easy to
miss in code review and will only surface as a bug once the guarantee is
gone.

## 15. Testing and verification

Testing code that runs under Snapshot Isolation is easier for the
single-transaction case and harder for the concurrent case, and both need
distinct test strategies. For the single-transaction case, standard unit
tests against a real database connection, or against an in-memory fake
implementing the same interface as the code samples in dimension 9,
verify that reads within one transaction see a consistent snapshot and that
the transaction's own writes are visible to its own subsequent reads,
which is the read-your-own-writes property every SI implementation
documents.

For the concurrent case, the technique that actually catches write skew and
other conflict bugs is a deliberately interleaved integration test. Start
two transactions, drive them through their reads before either writes,
drive the writes, and commit them in a controlled order the test dictates
rather than letting the database's own scheduler pick an order. Most
relational drivers support this via explicit BEGIN, a synchronization
barrier in the test code, then explicit COMMIT, so the test can force the exact race that
production concurrency would only produce occasionally. This kind of test
should assert on the final state of the shared invariant, not merely that
both commits returned without error, because the entire point of a write
skew test is that both transactions commit successfully while the combined
result is wrong.

Property-based and generative testing has a natural fit here. A property
test can generate random sequences of concurrent read and write operations
against a small set of shared keys, run them through the transaction
manager with randomized commit ordering, and assert an invariant that must
hold across every possible interleaving, for example that a counter's final
value equals the sum of all committed deltas regardless of race order. This
kind of test is far better at surfacing an unhandled write skew case than a
hand-written scenario test, because it explores interleavings a human
tester would not think to write.

Test doubles for the storage layer are useful for isolating the
transaction manager's logic from a real database's latency and setup cost.
The SnapshotStore implementations in dimension 9 are themselves examples of
such a double, small enough to run thousands of randomized interleaving
tests in milliseconds, which is the right layer to put the bulk of the
concurrency logic testing, reserving the smaller number of tests against
a real database for confirming the vendor's actual isolation level behaves
as documented.

## 16. Observability signals

The rate of serialization or update-conflict errors returned by commit,
per table or per hot key, is the single most important signal for a system
running under Snapshot Isolation, because it is the direct, measurable cost
of write contention that would otherwise be invisible until an application
team notices dropped writes. A healthy system shows this rate near zero for
low-contention tables and a stable, bounded rate for known hot keys that the
application already retries around, and a rising trend on a previously quiet
table is the first sign of a new source of write contention.

The age of the oldest active transaction, or equivalently the gap between
the current timestamp and the oldest still-referenced snapshot, is the
second critical signal, because it directly predicts storage bloat and
garbage collection pressure. PostgreSQL exposes this via the
pg_stat_activity view's transaction start time and via the xmin horizon
tracked internally for VACUUM (PostgreSQL documentation section 24.1.5,
verified 2026-08-16, cited above). The equivalent in any SI implementation
is worth alerting on when it exceeds a threshold the team sets based on
their actual write volume, since the storage cost of an old snapshot scales
with how much the database changed while it was open.

Dead or stale version counts, per table, measure the accumulated cost of
retained old versions that garbage collection has not yet reclaimed, and
should track roughly proportional to write volume times the age of the
oldest active snapshot. A count growing faster than that relationship
predicts indicates either garbage collection falling behind or something
holding a snapshot open longer than expected.

A healthy dashboard for an SI-backed system shows conflict rate flat near
zero except on named hot keys, oldest transaction age bounded and mostly
short, and version or dead tuple counts oscillating around a steady state
rather than climbing. A failing instance shows a climbing conflict rate on
a table that previously had none, an oldest transaction age that keeps
growing without bound, which usually traces to a connection leak or an
abandoned long transaction, or a version count climbing linearly with no
corresponding drop after garbage collection runs, which usually traces to
that same long-lived transaction preventing reclamation across the whole
instance rather than just the table it touches.

## 17. Security and privacy implications

Snapshot Isolation retains prior versions of every row that has been
updated, for as long as any active transaction's snapshot might still need
to read them, and this has a direct data retention implication that is easy
to overlook. If an application relies on a database-level DELETE or UPDATE
to remove sensitive data for a legal or contractual reason, for instance a
right-to-erasure request, the old version of that row may still exist in
the storage engine's version chain, undo log, or version store, readable by
any transaction whose snapshot predates the deletion, until garbage
collection actually reclaims it. Systems with strict data-erasure
requirements need to account for this window explicitly, either by bounding
the maximum transaction lifetime the system allows, so the retention window
has a known upper bound, or by using a mechanism that guarantees physical
overwrite rather than relying on the versioning engine's own garbage
collection timing.

A second, more subtle implication is that a long-lived transaction that
started before a sensitive value was updated will continue to see the old
value for its entire duration, which is the correct and intended behaviour
of the pattern but can be surprising in an audit or compliance context
where an operator expects every active session to reflect the latest state
immediately after a correction is applied. This is analytical judgement
rather than a documented vendor claim, informed by the mechanism described
in dimension 5 and 9.

Beyond retention, Snapshot Isolation does not itself introduce a new attack
surface for injection, authentication, or authorization, those concerns
belong to the layers above the isolation level and are unaffected by which
concurrency control policy a transaction runs under. The pattern is silent
on access control entirely, a transaction's snapshot respects the same
row-level and column-level permissions the database enforces regardless of
isolation level.

## Code examples

Three languages, all implementing the identical algorithm so the trade-offs
in dimension 8 are visible side by side rather than obscured by language
differences. TypeScript and Python show the shape most application
developers will actually write, an in-process optimistic multiversion store.
Go shows the same algorithm with explicit value types and no exceptions,
which is the closest a garbage-collected, non-object language gets to the
canonical form. Rust and Swift are omitted here because the pattern's
interesting content is the validation algorithm, not the language's memory
model, and three languages already show every variation the algorithm has,
adding two more would repeat the same twenty lines under a different syntax
rather than add insight, which is the omission rule the entry template asks
for.

Every sample below was compiled or run directly against the toolchain on
this machine and the transcript, showing the expected write-write conflict
being detected, is reproduced under each block.

### TypeScript

```typescript
type Version<V> = { value: V; commitTs: number };

class SnapshotStore<K, V> {
  private data = new Map<K, Version<V>[]>();
  private clock = 0;

  beginTxn(): SnapshotTxn<K, V> {
    return new SnapshotTxn(this, this.clock);
  }

  read(key: K, atTs: number): V | undefined {
    const versions = this.data.get(key);
    if (!versions) return undefined;
    let best: Version<V> | undefined;
    for (const v of versions) {
      if (v.commitTs <= atTs && (!best || v.commitTs > best.commitTs)) best = v;
    }
    return best?.value;
  }

  latestCommitTs(key: K): number {
    const versions = this.data.get(key);
    if (!versions || versions.length === 0) return -1;
    return Math.max(...versions.map((v) => v.commitTs));
  }

  tryCommit(writeSet: Map<K, V>, beginTs: number): number | null {
    for (const key of writeSet.keys()) {
      if (this.latestCommitTs(key) > beginTs) return null;
    }
    const commitTs = ++this.clock;
    for (const [key, value] of writeSet) {
      const arr = this.data.get(key) ?? [];
      arr.push({ value, commitTs });
      this.data.set(key, arr);
    }
    return commitTs;
  }
}

class SnapshotTxn<K, V> {
  private writeSet = new Map<K, V>();
  constructor(private store: SnapshotStore<K, V>, public beginTs: number) {}

  read(key: K): V | undefined {
    if (this.writeSet.has(key)) return this.writeSet.get(key);
    return this.store.read(key, this.beginTs);
  }

  write(key: K, value: V) {
    this.writeSet.set(key, value);
  }

  commit(): number | null {
    return this.store.tryCommit(this.writeSet, this.beginTs);
  }
}

const store = new SnapshotStore<string, number>();
const seed = store.beginTxn();
seed.write("balance", 100);
seed.commit();

const t1 = store.beginTxn();
const t2 = store.beginTxn();
t1.write("balance", (t1.read("balance") ?? 0) - 30);
t2.write("balance", (t2.read("balance") ?? 0) - 50);
const c1 = t1.commit();
const c2 = t2.commit();
console.log("t1 commit:", c1, "t2 commit:", c2);
```

Compiled with `npx tsc --target es2020 --module commonjs` and run with
`node`, this machine, verified 2026-08-16. Output.

```
t1 commit: 2 t2 commit: null
```

The second transaction returns null, its write set contained "balance" and a
version of "balance" was committed at timestamp 3, which is greater than its
own begin timestamp of 1, so the validator correctly rejects it.

### Python

```python
from dataclasses import dataclass
from typing import Dict, List, Optional, TypeVar, Generic

K = TypeVar("K")
V = TypeVar("V")


@dataclass
class Version(Generic[V]):
    value: V
    commit_ts: int


class SnapshotStore(Generic[K, V]):
    def __init__(self) -> None:
        self.data: Dict[K, List[Version[V]]] = {}
        self.clock = 0

    def begin_txn(self) -> "SnapshotTxn[K, V]":
        return SnapshotTxn(self, self.clock)

    def read(self, key: K, at_ts: int) -> Optional[V]:
        versions = self.data.get(key)
        if not versions:
            return None
        visible = [v for v in versions if v.commit_ts <= at_ts]
        if not visible:
            return None
        return max(visible, key=lambda v: v.commit_ts).value

    def latest_commit_ts(self, key: K) -> int:
        versions = self.data.get(key)
        if not versions:
            return -1
        return max(v.commit_ts for v in versions)

    def try_commit(self, write_set: Dict[K, V], begin_ts: int) -> Optional[int]:
        for key in write_set:
            if self.latest_commit_ts(key) > begin_ts:
                return None
        self.clock += 1
        commit_ts = self.clock
        for key, value in write_set.items():
            self.data.setdefault(key, []).append(Version(value, commit_ts))
        return commit_ts


class SnapshotTxn(Generic[K, V]):
    def __init__(self, store: SnapshotStore[K, V], begin_ts: int) -> None:
        self.store = store
        self.begin_ts = begin_ts
        self.write_set: Dict[K, V] = {}

    def read(self, key: K) -> Optional[V]:
        if key in self.write_set:
            return self.write_set[key]
        return self.store.read(key, self.begin_ts)

    def write(self, key: K, value: V) -> None:
        self.write_set[key] = value

    def commit(self) -> Optional[int]:
        return self.store.try_commit(self.write_set, self.begin_ts)


if __name__ == "__main__":
    store: SnapshotStore[str, int] = SnapshotStore()
    seed = store.begin_txn()
    seed.write("balance", 100)
    seed.commit()

    t1 = store.begin_txn()
    t2 = store.begin_txn()
    t1.write("balance", (t1.read("balance") or 0) - 30)
    t2.write("balance", (t2.read("balance") or 0) - 50)
    c1 = t1.commit()
    c2 = t2.commit()
    print("t1 commit:", c1, "t2 commit:", c2)
    assert c1 is not None and c2 is None
```

Run directly with `python3`, this machine, verified 2026-08-16. Output.

```
t1 commit: 2 t2 commit: None
```

The identical logic, the identical outcome, expressed with an isinstance
free write set dictionary and a max over a filtered list instead of an
optional-chained reduce, which is the natural Python shape for the same
validation rule.

### Go

```go
package main

import "fmt"

type version struct {
	value    int
	commitTs int
}

type snapshotStore struct {
	data  map[string][]version
	clock int
}

func newStore() *snapshotStore {
	return &snapshotStore{data: make(map[string][]version)}
}

func (s *snapshotStore) read(key string, atTs int) (int, bool) {
	versions, ok := s.data[key]
	if !ok {
		return 0, false
	}
	best, bestTs := -1, -1
	for _, v := range versions {
		if v.commitTs <= atTs && v.commitTs > bestTs {
			best, bestTs = v.value, v.commitTs
		}
	}
	if bestTs == -1 {
		return 0, false
	}
	return best, true
}

func (s *snapshotStore) latestCommitTs(key string) int {
	versions, ok := s.data[key]
	if !ok || len(versions) == 0 {
		return -1
	}
	max := -1
	for _, v := range versions {
		if v.commitTs > max {
			max = v.commitTs
		}
	}
	return max
}

func (s *snapshotStore) tryCommit(writeSet map[string]int, beginTs int) (int, bool) {
	for key := range writeSet {
		if s.latestCommitTs(key) > beginTs {
			return 0, false
		}
	}
	s.clock++
	commitTs := s.clock
	for key, value := range writeSet {
		s.data[key] = append(s.data[key], version{value: value, commitTs: commitTs})
	}
	return commitTs, true
}

type snapshotTxn struct {
	store    *snapshotStore
	beginTs  int
	writeSet map[string]int
}

func (s *snapshotStore) beginTxn() *snapshotTxn {
	return &snapshotTxn{store: s, beginTs: s.clock, writeSet: make(map[string]int)}
}

func (t *snapshotTxn) read(key string) (int, bool) {
	if v, ok := t.writeSet[key]; ok {
		return v, true
	}
	return t.store.read(key, t.beginTs)
}

func (t *snapshotTxn) write(key string, value int) {
	t.writeSet[key] = value
}

func (t *snapshotTxn) commit() (int, bool) {
	return t.store.tryCommit(t.writeSet, t.beginTs)
}

func main() {
	store := newStore()
	seed := store.beginTxn()
	seed.write("balance", 100)
	seed.commit()

	t1 := store.beginTxn()
	t2 := store.beginTxn()
	b1, _ := t1.read("balance")
	t1.write("balance", b1-30)
	b2, _ := t2.read("balance")
	t2.write("balance", b2-50)
	c1, ok1 := t1.commit()
	c2, ok2 := t2.commit()
	fmt.Println("t1 commit:", c1, ok1, "t2 commit:", c2, ok2)
}
```

Run directly with `go run`, this machine, verified 2026-08-16. Output.

```
t1 commit: 2 true t2 commit: 0 false
```

Go returns an explicit boolean rather than an optional or a null, which is
the idiomatic Go shape for "this operation may fail", and it is the same
first-committer-wins check running against the same data, producing the
same conflict on the second commit.

## 18. References

Hal Berenson, Philip A. Bernstein, Jim Gray, Jim Melton, Elizabeth O'Neil,
Patrick O'Neil, "A Critique of ANSI SQL Isolation Levels", Proceedings of the
1995 ACM SIGMOD International Conference on Management of Data, pages 1 to
10. DOI 10.1145/223784.223785. Public mirror https://arxiv.org/pdf/cs/0701157.
Verified 2026-08-16, both the DOI record on the ACM Digital Library and the
arXiv mirror's existence and authorship confirmed via search.

PostgreSQL Global Development Group, PostgreSQL Documentation, chapter 13,
Concurrency Control, section 13.2, Transaction Isolation.
https://www.postgresql.org/docs/current/transaction-iso.html. Verified
2026-08-16, sections 13.2.1 through 13.2.3 fetched and quoted directly.

PostgreSQL Global Development Group, PostgreSQL Documentation, chapter 24,
Routine Database Maintenance Tasks, section 24.1.5, Preventing Transaction
ID Wraparound Failures. https://www.postgresql.org/docs/current/routine-vacuuming.html.
Verified 2026-08-16 as the source for the transaction age and VACUUM
retention discussion in dimensions 11 and 16.

Microsoft Corporation, Microsoft Learn, "SET TRANSACTION ISOLATION LEVEL
(Transact-SQL)". https://learn.microsoft.com/en-us/sql/t-sql/statements/set-transaction-isolation-level-transact-sql.
Verified 2026-08-16, fetched in full, quoted directly for the SNAPSHOT and
READ_COMMITTED_SNAPSHOT sections.

Oracle Corporation, Oracle Database 19c Database Concepts, "Data
Concurrency and Consistency". https://docs.oracle.com/en/database/oracle/oracle-database/19/cncpt/data-concurrency-and-consistency.html.
Verified 2026-08-16, quoted directly for the multiversion consistency model,
consistent read clones, and the ORA-08177 serialization failure.

MongoDB, Inc., MongoDB Manual, "Transactions".
https://www.mongodb.com/docs/manual/core/transactions/. Verified
2026-08-16, quoted directly for the read concern "snapshot" behaviour.

Cockroach Labs, CockroachDB Documentation, "Transactions".
https://docs.cockroachlabs.com/docs/stable/transactions. Verified
2026-08-16, quoted directly for the statement that CockroachDB's
SERIALIZABLE level exceeds the SNAPSHOT level in strength and that
SNAPSHOT is not offered as a selectable isolation level.

Michael J. Cahill, Uwe Rohm, Alan D. Fekete, "Serializable Isolation for
Snapshot Databases", ACM Transactions on Database Systems, volume 34, issue
4, article 20, 2009, cited in dimension 13 as the source for Serializable
Snapshot Isolation. This citation was not independently verified against
the publisher during this authoring pass, unlike every other citation in
this entry, and should be confirmed before being relied on as a sourced
claim, it is flagged here rather than silently included as verified.
