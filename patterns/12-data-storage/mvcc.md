---
name: Multiversion Concurrency Control
slug: mvcc
family: 12-data-storage
category: Data and Storage
aliases: [MVCC, Multiversion Concurrency, Snapshot Isolation Storage, Time-Travel Storage]
first_described: "Reed 1978 (MIT PhD thesis, Naming and Synchronization in a Decentralized Computer System); Bernstein and Goodman 1983 (ACM Computing Surveys survey paper)"
maturity: canonical
related: [optimistic-concurrency-control, event-sourcing, copy-on-write, snapshot-isolation, write-ahead-log, log-structured-merge-tree, saga]
incompatible_with: [two-phase-locking-as-sole-mechanism]
verified: 2026-08-02
---

# Multiversion Concurrency Control

## 1. Name, aliases, and lineage

Multiversion Concurrency Control, almost universally abbreviated MVCC, is a
concurrency control method in which a storage engine keeps more than one
physical version of each logical data item and hands a reader the version that
was current when that reader's transaction began, rather than the version that
is current right now. The pattern is also referred to informally as
multiversioning, and its effect on transaction semantics is called snapshot
isolation when the guarantee is stated in terms of what a transaction observes
rather than in terms of how the storage engine is built.

The academic origin traces to David P. Reed's 1978 MIT doctoral thesis, *Naming
and Synchronization in a Decentralized Computer System*, which proposed
timestamp-ordered multiversion storage as a way to let read-only transactions
proceed without ever blocking on a write lock. Philip A. Bernstein and Nathan
Goodman formalized and surveyed the technique for a broader database audience
in their 1983 ACM Computing Surveys paper, "Multiversion Concurrency Control,
Theory and Algorithms," which is the citation most textbooks point to when they
introduce the term MVCC by name. The thesis and the survey are the two
foundational references and are treated as authoritative lineage by every major
production database that documents its own MVCC implementation, including
PostgreSQL and Oracle, both cited below.

Two production lineages diverged from that shared theory in ways worth naming.
PostgreSQL stores full old row versions directly inside the table's heap pages
and relies on a background vacuum process to remove them, a design its own
documentation calls out explicitly as a design that trades write amplification
for read simplicity (PostgreSQL Documentation, "MVCC," accessed 2026-08-02,
see References). Oracle and InnoDB instead store the current row in place and
reconstruct older versions on demand from a separate undo log, which is the
lineage that gave rise to the term "undo-based MVCC" as distinct from
PostgreSQL's "append-only MVCC." Both are MVCC. They differ in where the old
bytes live and who pays the cost of keeping them.

## 2. Problem and context

A database serves many concurrent transactions. Some read, some write, and the
naive way to keep them from corrupting each other's view of the data is
locking. A reader takes a shared lock, a writer takes an exclusive lock, and
anyone who wants what is already locked waits. This is correct and it is also
the single biggest source of contention in a multi-user system, because a long
running report that reads a million rows under a shared lock can stall every
write to those rows for as long as the report runs, and a single writer holding
an exclusive lock stalls every reader who touches the same row.

The concrete situation that creates the need for MVCC is a workload with a mix
of long-running analytical reads and frequent short writes against the same
tables, the classic OLTP-plus-reporting shape found in nearly every production
system that has been alive for more than a year. A billing system generating a
month-end invoice report while new charges are being written every second is
the canonical example. Under pure locking, the report either blocks every new
charge for its duration, or the new charges block the report from ever seeing
a stable answer. Neither is acceptable, and the tension is not a corner case,
it is the default shape of production traffic once a system has more than a
handful of concurrent users.

MVCC exists to make that tension disappear by construction rather than by
tuning. If a reader is handed its own private, consistent view of the data as
of a fixed point in time, and a writer is never asked to wait for that reader
to finish looking at the old version, the report and the write can proceed at
the same time without either one seeing something broken. The pattern is
specifically a storage and concurrency-control pattern, not a data-modeling
pattern. It answers a "how does the engine let readers and writers coexist"
question, not a "how should I shape my schema" question.

## 3. Forces

The forces are read latency, write latency, storage cost, garbage collection
cost, and isolation strength, and MVCC resolves the tension between them by
deliberately paying storage and garbage collection cost to buy read and write
latency.

Read latency versus write latency is the primary force MVCC exists to resolve.
A pure locking scheme forces a choice. Either readers block writers, under
strict two-phase locking with shared locks, or writers overwrite in place and
readers risk seeing torn or uncommitted data. MVCC sidesteps the choice
entirely by giving the reader its own copy to look at, so neither side waits on
the other for the duration of a read. This is not free. It is bought by
keeping old versions around, which is the second force.

Storage cost versus garbage collection cost is the force every MVCC
implementation has to manage continuously. Every version that MVCC keeps alive
so that some in-flight reader can still see it is a version that occupies disk
or memory until nothing needs it anymore. A system that never removes old
versions grows without bound. A system that removes them too aggressively
risks invalidating a reader mid-transaction. PostgreSQL resolves this with a
background vacuum process and an oldest-active-transaction watermark; getting
that watermark wrong, by holding one transaction open for hours, is the single
most common operational failure mode of MVCC systems in practice, discussed in
dimension 11.

Isolation strength is the third force. MVCC by itself gives you snapshot
isolation, meaning a transaction sees a consistent point-in-time view, but
snapshot isolation is provably weaker than full serializability. Two
transactions can each read a value the other is about to change and both
commit, producing a result no serial execution of the two transactions could
have produced, the classic write skew anomaly. PostgreSQL's own documentation
states this directly and describes serializable snapshot isolation as an
additional layer built on top of ordinary MVCC snapshots specifically to close
that gap (PostgreSQL Documentation, "Serializable Isolation Level," accessed
2026-08-02, see References). MVCC favors concurrency over the strongest
possible correctness guarantee by default, and a system that needs full
serializability has to opt into a stronger, more expensive mode explicitly.

Cognitive load and operability form the fourth force. A DBA operating an MVCC
system has to reason about a moving population of live versions, vacuum or
purge schedules, and the interaction between long transactions and storage
growth, none of which exists under simple locking. The pattern trades a
simpler mental model for concurrency, and the price is paid in operational
footprint, a cost this entry does not minimize.

## 4. Applicability and non-applicability

Reach for MVCC, or choose a storage engine that implements it, when the
workload has a genuine mix of concurrent reads and writes against overlapping
data and read latency or read throughput matters. Reach for it when read-only
transactions must never be blocked by writers, which is a hard requirement in
most reporting, analytics, and dashboard workloads sitting on top of a live
OLTP database. Reach for it when the isolation level you need is snapshot
isolation or read committed, both of which MVCC provides naturally and
cheaply. Reach for it in any system where "readers never block writers and
writers never block readers" is a stated non-functional requirement, because
that is precisely the guarantee PostgreSQL's own documentation states as
MVCC's main advantage (PostgreSQL Documentation, "MVCC," accessed 2026-08-02,
see References).

Do not reach for MVCC, or do not assume you have solved your correctness
problem solely because the underlying engine uses it, in the following
situations.

First, when the application genuinely requires serializability and cannot
tolerate write skew, phantom reads across the transaction lifetime, or lost
updates between two concurrently modified but non-overlapping value sets. Plain
snapshot isolation, which is what most MVCC engines default to, does not
provide this. You need an explicit serializable mode, PostgreSQL's SSI or
CockroachDB's default serializable isolation, or an application-level check
such as a compare-and-swap on the version column, and treating "the database
uses MVCC" as equivalent to "the database is serializable" is a real and
recurring correctness bug.

Second, when the workload is write-heavy with very few long-lived readers and
storage or write amplification is the binding constraint. Every write under
MVCC either creates a new version, PostgreSQL's append-only model, which
bloats the table until vacuum runs, or writes an undo record in addition to
the in-place update, InnoDB's model, which doubles the write path for every
modified row. A pure write-through cache or a single-writer embedded key
store with no concurrent readers gains nothing from MVCC and pays its
overhead for no benefit.

Third, when transactions in the system are routinely long-lived, for example
an interactive session that opens a transaction and leaves it idle for
minutes while a human thinks. Under MVCC, an old transaction that is still
open pins every version newer readers might otherwise have discarded, and the
database cannot vacuum past that transaction's snapshot. This is not a
theoretical edge case, it is documented explicitly by PostgreSQL as a primary
cause of table bloat (PostgreSQL Documentation, "Routine Vacuuming," accessed
2026-08-02, see References) and is discussed further under dimension 11.

Fourth, for a small embedded system with a single writer and no concurrent
readers, such as a mobile app's local SQLite database used by one process at
a time, MVCC's version-management overhead buys nothing that a simple
rollback journal or write-ahead log does not already provide more cheaply.
SQLite itself defaults to a rollback journal rather than MVCC for exactly this
reason, and only offers WAL mode, which is closer to MVCC in spirit, as an
option for concurrent-reader workloads (SQLite Documentation, "Write-Ahead
Logging," accessed 2026-08-02, see References).

## 5. Structure

MVCC's participants are the same in every implementation, though the names
and the exact mechanics differ between an append-only engine like PostgreSQL
and an undo-log engine like InnoDB or Oracle.

Transaction identifier or timestamp. Every transaction is assigned a
monotonically increasing identifier or logical timestamp when it begins. This
identifier is stamped onto every version that transaction creates and is used
to compute visibility for every other transaction that reads later.

Version. A version is one physical copy of a row's data, tagged with the
identifier of the transaction that created it and, once it has been
superseded, the identifier of the transaction that superseded it. A single
logical row can have many versions alive at once. In PostgreSQL these are
called `xmin` and `xmax` and live directly in the row's header inside the
table's heap page. In InnoDB they are called `DB_TRX_ID` and `DB_ROLL_PTR`, a
transaction identifier plus a pointer into the undo log rather than a second
copy of the whole row (MySQL Reference Manual, "InnoDB Multi-Versioning,"
accessed 2026-08-02, see References).

Snapshot. A snapshot is the set of transaction identifiers that were
already committed, and the set that were still in progress, at the moment a
reading transaction began. Visibility of any given version to that reader is
computed purely from comparing the version's creating and superseding
transaction identifiers against this snapshot, with no locks consulted at all.

Garbage collector. A background process, called vacuum in PostgreSQL and
the purge thread in InnoDB, that walks the version chains and physically
removes versions no longer visible to any open snapshot. This participant is
not optional. An MVCC system with no garbage collector grows without bound.

Undo log or version chain. The mechanism that links a row's versions
together so the engine can walk backward from the current version to
reconstruct an older one on demand. Oracle and InnoDB store this explicitly as
a separate undo segment. PostgreSQL instead keeps all versions inline in the
table and relies on the row header pointers plus the visibility rules to find
the right one, with no separate reconstruction step needed because the old
bytes are already sitting in the page.

## 6. ASCII structure diagram

```
                    +---------------------------+
                    |     Transaction Manager    |
                    |  assigns monotonic txids   |
                    +--------------+--------------+
                                   |
                     issues txid   |   reads snapshot
                    (begin/commit) |   (xmin watermark)
                                   v
   +-------------------+   +------+-------+   +-------------------+
   | Writer Tx (id=42)  |   | Reader Tx     |   | Writer Tx (id=44)  |
   | writes new version |   | (id=43)       |   | writes new version |
   +----------+---------+   | snapshot={42} |   +----------+---------+
              |             +------+-------+              |
              v                    |                       v
   +-------------------------------+-------------------------------+
   |                   Logical Row "account_balance"                |
   |                                                                 |
   |  +--------------+   +--------------+   +--------------+        |
   |  | version v1    |   | version v2    |   | version v3    |      |
   |  | xmin=10       |-->| xmin=42       |-->| xmin=44       |      |
   |  | xmax=42       |   | xmax=44       |   | xmax=(open)   |      |
   |  | value=100     |   | value=150     |   | value=200     |      |
   |  +--------------+   +--------------+   +--------------+        |
   |          ^                  ^                                  |
   |          |                  |                                  |
   |   too old for tx43   VISIBLE to tx43 (created before,           |
   |   (superseded by v2)  superseded after tx43's snapshot)         |
   +-----------------------------------------------------------------+
                                   |
                                   v
                    +---------------------------+
                    | Garbage Collector (vacuum, |
                    | purge thread)              |
                    | removes v1 once no open    |
                    | snapshot can see it        |
                    +---------------------------+
```

## 7. Dynamics

The runtime interaction has four phases, transaction begin, write, read, and
garbage collection, and they proceed concurrently rather than in any fixed
order across different transactions.

```
Time -->

Writer A (txid=42)  |--BEGIN--write row(v2)---------COMMIT--|
Reader R (txid=43)         |--BEGIN--snapshot={<42}--read row--COMMIT--|
Writer B (txid=44)                     |--BEGIN--write row(v3)---COMMIT--|
Vacuum/Purge                                                     |--remove v1--|

Step 1. Writer A begins, gets txid 42, writes a new version v2 of the row.
        v1's xmax is set to 42, superseded by A. v2's xmin is 42, xmax open.
Step 2. Reader R begins, gets txid 43. Its snapshot records that txid 42 was
        already committed before R started, so v2 is visible to R.
Step 3. R reads the row. The engine walks the version chain, finds v2, checks
        v2.xmin (42) is committed and at or before R's snapshot watermark, and
        v2.xmax is either open or a txid not yet committed at R's start, so v2
        is the answer returned. No lock was taken by R and none was taken by
        A on R's behalf.
Step 4. Writer B begins, gets txid 44, independently writes v3. v2's xmax is
        set to 44. v3 is invisible to R because R's snapshot was fixed at
        step 2 and does not include txid 44 as committed.
Step 5. R commits, still having seen only v2, a single consistent snapshot,
        regardless of B's concurrent write.
Step 6. Once no open transaction's snapshot could possibly still need v1, the
        oldest active snapshot watermark has advanced past it, and the
        garbage collector removes v1's storage.
```

The critical property this dynamic demonstrates is that visibility is
computed purely by comparing transaction identifiers, with zero locks
acquired for the read path. Writer A and Writer B never block each other's
commit, assuming they touch different rows or the engine's write-write
conflict detection allows it, and neither ever blocks Reader R.

## 8. Implementation variants

Append-only MVCC, PostgreSQL's model. Every update creates an entirely
new row version inside the table's own heap storage, and the old version is
left in place, marked dead once no snapshot needs it, and physically removed
later by vacuum. Reads never need a separate reconstruction step because the
version they need is already a full row sitting in the table. The trade-off is
table bloat. An update-heavy table can grow several times its logical size
between vacuum runs, which is precisely why PostgreSQL exposes `autovacuum`
tuning as a first-class operational concern rather than an internal detail
(PostgreSQL Documentation, "Routine Vacuuming," accessed 2026-08-02, see
References).

Undo-log MVCC, InnoDB and Oracle's model. The current version of a row
is always the one stored in place in the primary data structure. Older
versions are not stored as full rows at all. Instead, an undo log entry
records the delta needed to reconstruct the previous value, and a reader that
needs an older version follows a roll pointer into the undo segment and
replays the delta. This keeps the primary table compact at the cost of a
reconstruction step on every read that needs a non-current version, and a
separate purge thread that removes undo segments once no transaction can
still need them (MySQL Reference Manual, "InnoDB Multi-Versioning," accessed
2026-08-02; Oracle Database Concepts, "Data Concurrency and Consistency,"
accessed 2026-08-02, see References).

Distributed timestamp-based MVCC, CockroachDB and Spanner's model. Rather
than a purely local monotonic transaction counter, the version tag is a
hybrid logical clock timestamp that is comparable across machines without a
central sequencer. CockroachDB documents this explicitly. It relies on MVCC
at the storage layer and uses hybrid logical clock timestamps to create
distinct versions and to decide when a value becomes eligible for garbage
collection (CockroachDB Docs, "Storage Layer," accessed 2026-08-02, see
References). Google's Spanner takes this further with TrueTime, using
hardware-synchronized clock uncertainty bounds to assign globally comparable
timestamps to transactions across data centers, which is the mechanism that
lets Spanner offer external consistency across a geographically distributed
MVCC store.

Copy-on-write snapshot MVCC, ZFS, Btrfs, and similar filesystems. The
same underlying insight, that keeping the old version reachable while a new
one is written is valuable, appears one layer down the stack in copy-on-write
filesystems, which never overwrite a block in place but instead write a new
block and update a pointer, leaving the old block reachable from a previous
snapshot until it is removed. This is architecturally the same
version-chain-plus-garbage-collector shape as database MVCC, applied to disk
blocks instead of rows, and is worth naming because engineers who have tuned
ZFS snapshot retention have already built the mental model MVCC needs.

Language-idiomatic note. MVCC is primarily a storage-engine and
data-structure pattern rather than an object-oriented design pattern, so
there is no meaningfully different idiomatic shape per programming language
the way there is for, say, Strategy or Observer. The three code samples below
each implement the same version-chain-and-snapshot mechanism because that
mechanism, not language idiom, is the substance of the pattern. The
differences between the samples are differences of concurrency primitive,
`sync.Mutex` in Go, a `threading.Lock` in Python, `std::sync::Mutex` in
Rust, not of design shape.

## 9. Known production uses

PostgreSQL, every supported version, implements MVCC as its core
concurrency control mechanism for all table access, storing `xmin` and `xmax`
transaction identifiers directly in each row's header and relying on
`autovacuum` for removing old versions. This is documented as the foundational
mechanism of the entire engine, not an optional feature (PostgreSQL
Documentation, "Chapter 13. Concurrency Control," accessed 2026-08-02, see
References).

MySQL's InnoDB storage engine, the default engine since MySQL 5.5,
implements undo-log-based MVCC to support REPEATABLE READ as its default
isolation level, storing `DB_TRX_ID` and `DB_ROLL_PTR` on every row and
maintaining rollback segments for consistent nonlocking reads (MySQL
Reference Manual 8.4, "InnoDB Multi-Versioning," accessed 2026-08-02, see
References).

Oracle Database, across all editions, uses undo-segment-based
multiversion read consistency as the mechanism behind its stated guarantee
that a writer never blocks a reader and a reader never blocks a writer,
reconstructing consistent-read block clones from undo data keyed by System
Change Number (Oracle Database 19c Concepts, "Data Concurrency and
Consistency," accessed 2026-08-02, see References).

CockroachDB, a distributed SQL database, states plainly that it relies
heavily on multi-version concurrency control to process concurrent requests
and guarantee consistency, using hybrid logical clock timestamps to version
keys in its Pebble storage engine (CockroachDB Docs, "Storage Layer,"
accessed 2026-08-02, see References).

Microsoft SQL Server, in its Read Committed Snapshot Isolation and
Snapshot Isolation modes, both optional and off by default, implements a
version-store-based MVCC that copies pre-update row images into a version
store in `tempdb`, an architecture SQL Server's documentation describes
directly as row versioning, distinguishing it from the engine's default
lock-based Read Committed mode (Microsoft SQL Server Documentation,
"Snapshot Isolation in SQL Server," accessed 2026-08-02, see References).

Git, as an object store, exhibits the same structural pattern one layer
removed from a database engine. Every commit is an immutable new version of
the tree, old commits remain reachable until garbage collection prunes
unreferenced objects, and a checkout is exactly a snapshot read against a
fixed point in that version history. This is named here as a structural
analogue, not as a database claim, and readers should treat it as
illustrative rather than as evidence that Git's authors intended it as an
MVCC implementation.

## 10. Consequences

Positive. Readers never block writers and writers never block readers,
which is the single most valuable property MVCC provides and is stated as
the primary design goal by both PostgreSQL and Oracle's own documentation,
cited in dimension 9. Long-running analytical queries get a stable,
consistent snapshot without freezing the write path, which is what makes
MVCC engines viable as the backing store for a live OLTP system with a
reporting workload running concurrently. Read scalability improves because
reads never contend on locks with each other or with writers, only with the
cost of walking a version chain. Point-in-time recovery and time-travel
queries fall out of the mechanism almost for free in systems that expose
historical snapshots deliberately, since the machinery to reconstruct an
older version already exists for ordinary transaction isolation.

Negative. Storage grows to hold old versions, and that growth is
proportional to write rate and to how long the oldest open snapshot stays
open, which means a single forgotten long-running transaction can bloat a
table dramatically. This is not a rare failure, it is the single most common
MVCC operational incident and is documented explicitly by PostgreSQL as a
reason to monitor transaction age and long-running transactions (PostgreSQL
Documentation, "Preventing Transaction ID Wraparound Failures," accessed
2026-08-02, see References). Garbage collection is a permanent operational
cost, not a one-time setup cost, and under-provisioning it, or running it too
infrequently, degrades read performance over time as version chains grow long
and the engine has to walk further to find a visible version. Snapshot
isolation, which is what most MVCC engines provide by default, is strictly
weaker than full serializability, and application code that assumes
serializable behavior because "the database uses MVCC" is a recurring, real
source of subtle correctness bugs, particularly the write skew anomaly where
two transactions each read a value the other is about to change and both
commit successfully, together producing a result that could not have occurred
under any serial ordering. Write amplification is real. Every logical update
either duplicates the row, the append-only model, or writes both the
in-place update and an undo record, the undo-log model, which is strictly
more I/O than a naive in-place overwrite with no versioning at all.

## 11. Failure modes and misuse

Symptom. Table size grows continuously and never shrinks, disk usage
climbs steadily even though the logical row count is stable, and query
latency degrades over weeks without a code change.
Cause. A long-running or idle-in-transaction connection is holding a
snapshot open, which pins the vacuum watermark and prevents the garbage
collector from removing any version newer than that snapshot, so every
subsequent update piles up dead versions the vacuum process is not permitted
to remove.
Fix. Set a statement timeout and an idle-in-transaction session timeout
at the connection-pool or database level, and alert on any transaction open
longer than a small threshold, minutes not hours, in a system with a high
write rate. PostgreSQL's own operational guidance names this
exact scenario as the primary cause of table bloat (PostgreSQL
Documentation, "Routine Vacuuming," accessed 2026-08-02, see References).

Symptom. A read-modify-write sequence under snapshot isolation
occasionally produces a result that is impossible under any serial ordering
of the two transactions, most commonly two account balances that should sum
to a constant drifting apart after two concurrent transfers.
Cause. Snapshot isolation permits write skew. Each transaction reads a
value the other is about to overwrite, and neither transaction's write
conflicts with the other's write set because they write different rows, so
the engine's default MVCC conflict check never fires even though the
combined outcome is inconsistent.
Fix. Either use an explicit serializable isolation level that adds
conflict detection beyond plain snapshot isolation, PostgreSQL's SSI or
CockroachDB's default `SERIALIZABLE`, or add an explicit application-level
constraint such as a `SELECT ... FOR UPDATE` to force a write-write conflict,
or a check constraint enforced at commit time.

Symptom. A transaction identifier counter approaches its maximum value
in a long-lived, high-write-rate database, and the engine either refuses new
writes or, worse, wraps around and makes old committed data appear to be from
the future, which can make it invisible to every reader.
Cause. Transaction identifiers are a finite counter, 32-bit in classic
PostgreSQL, and a database that runs for years at high write volume without
the wraparound-prevention vacuum ever completing can genuinely exhaust the
identifier space.
Fix. Monitor transaction ID age proactively rather than reactively, and
keep autovacuum's wraparound-prevention runs from ever being disabled or
starved of I/O bandwidth. PostgreSQL documents this as a standing operational
requirement, not an edge case (PostgreSQL Documentation, "Preventing
Transaction ID Wraparound Failures," accessed 2026-08-02, see References).

Symptom. An application built against an MVCC database experiences lost
updates under load. Two concurrent transactions each read the same row,
compute an update from the value they read, and the second commit
silently discards the first's change.
Cause. Under snapshot isolation, two transactions that read the same row
and independently update it using their read may both succeed, with
whichever commits last winning outright, unless the engine's first-committer-
wins conflict detection is engaged for that specific write, which it is not
guaranteed to be for logically related but structurally distinct writes.
Fix. Use optimistic concurrency control at the application layer, a
version column checked and incremented on every write, see the related
Optimistic Concurrency Control pattern, so the second writer's `UPDATE ...
WHERE version = expected` affects zero rows and the application can detect
and retry, rather than relying on MVCC's storage-layer guarantees to catch a
logically related but structurally independent conflict.

## 12. Trade-off matrix

| Force | MVCC (snapshot-based) | Strict Two-Phase Locking | Optimistic Concurrency Control (no versions kept) |
|---|---|---|---|
| Read blocks write | Never | Blocks on shared lock held | Never, no locks at read time |
| Write blocks read | Never | Blocks readers holding shared locks | Never at read time |
| Storage overhead | High, must retain old versions | Low, single copy in place | Low, single copy plus a version counter |
| Default isolation achievable | Snapshot isolation, not automatically serializable | True serializability achievable directly | Snapshot-like at read, but conflict caught only at commit |
| Write-write conflict handling | First-committer-wins or engine-specific | Prevented up front via lock waits | Detected at commit via version check, requires retry logic |
| Garbage collection burden | Continuous, dedicated background process required | None | Minimal, only the version counter |
| Long transaction impact | Blocks garbage collection, can bloat storage | Blocks other transactions directly, visible stalls | No blocking, but stale reads increase conflict rate at commit |
| Best fit | Mixed read-heavy plus write workloads, reporting alongside OLTP | Workloads needing strict serializability with moderate concurrency | Low-contention writes with client-driven retry tolerance |

## 13. Related and incompatible patterns

Optimistic Concurrency Control composes naturally with MVCC and is
frequently confused with it. MVCC solves how the storage engine hands
different transactions different views of the same data at the storage
layer. Optimistic Concurrency Control solves how an application detects that
two transactions tried to modify the same logical entity, typically via a
version column checked at write time. An MVCC database still needs
application-level optimistic concurrency control if the application requires
stronger conflict detection than the engine's default isolation level
provides, as discussed in dimension 11's lost-update failure mode.

Event Sourcing shares MVCC's core insight, that keeping history rather
than overwriting in place is valuable, but applies it at the application
model layer rather than the storage engine layer. An event-sourced system
retains every state transition as a permanent, queryable fact. An MVCC
engine retains only enough old versions to satisfy currently open snapshots
and discards the rest. A system can use both, MVCC as the storage engine
underneath an event store, and event sourcing as the application-level model
built on top of it.

Copy-on-Write is the structural mechanism MVCC's append-only variant is
built from. Any data structure that never mutates in place, instead writing
a new version and repointing a reference, is doing copy-on-write, and
PostgreSQL's row-version creation on every update is a direct instance of
this at the row level.

Write-Ahead Log is a complementary, not competing, pattern. A
write-ahead log guarantees durability and crash recovery by recording every
change before it is applied. MVCC governs which version of the data
different concurrent transactions are permitted to see. Nearly every
production MVCC database also implements a write-ahead log, and the two are
frequently implemented together but solve different problems.

Log-Structured Merge Tree shares MVCC's tolerance for multiple physical
copies of logically overlapping data, an LSM tree's overlapping SSTables
across levels, but for a different reason. LSM trees trade read
amplification for write throughput on the storage medium, while MVCC trades
storage for concurrent-access latency. A storage engine can combine both, as
CockroachDB does by layering MVCC versioning on top of the Pebble LSM-tree
engine.

Incompatible with treating Two-Phase Locking as the sole concurrency
mechanism. A system cannot coherently claim both that readers never block
on writer locks, MVCC's core promise, and that every access is mediated by a
strict two-phase lock, 2PL's core mechanism, as its primary concurrency
strategy at once. A hybrid system can layer explicit row locks on top of an
MVCC engine for specific operations, as `SELECT ... FOR UPDATE` does, but
that is locking used selectively within an MVCC engine, not 2PL as the
system's sole mechanism.

## 14. Refactoring path in and out

Introducing MVCC into a system that currently relies on explicit locking.
The realistic path for most teams is not implementing MVCC from scratch, it
is migrating to a storage engine that already provides it, since MVCC is
primarily a storage-engine property rather than something layered onto
an existing schema. Concretely, first, audit every place the application
takes an explicit read lock, `SELECT ... FOR SHARE` or table-level locking
hints, purely to prevent a concurrent write from being observed mid-flight,
because most of those locks become unnecessary once the underlying engine's
default isolation level already provides a consistent snapshot. Second,
change the transaction isolation level to Read Committed or Repeatable Read,
rather than Serializable unless serializability is a genuine requirement, so
the engine's MVCC path is actually engaged rather than bypassed by a
stricter mode that falls back toward locking. Third, remove the now-redundant
explicit locks one at a time, verifying under load that the removal does not
reintroduce a correctness bug that the lock was silently covering for, since
some of those locks may have been compensating for an application-level
optimistic concurrency gap rather than a pure storage-visibility problem, in
which case the fix is to add explicit version-column checking, dimension 13,
rather than simply deleting the lock.

Migrating away from MVCC toward pure locking or a single-writer model.
This is rare in practice, since almost no team voluntarily gives up
non-blocking reads, but it happens when a workload becomes so write-heavy and
so latency-sensitive on writes that the version-retention overhead
identified in dimension 10 becomes the dominant cost. The path, first,
identify the specific hot tables or key ranges where write amplification is
the measured bottleneck, not a guess. Second, consider whether a narrower
fix, such as reducing the isolation level's version-retention window,
tightening the garbage-collection interval, or partitioning the hot table so
vacuum or purge work is smaller per pass, resolves the problem without
abandoning MVCC entirely, since a full migration off an MVCC engine is a
much larger undertaking than tuning it. Third, if migration is genuinely
warranted, move the specific hot path to a single-writer, lock-free append
structure, a log, a queue, a dedicated write-optimized store, rather than
attempting to retrofit strict two-phase locking onto the existing schema,
since 2PL retrofitted onto an application built assuming non-blocking reads
is a substantially larger correctness risk than the write-amplification
problem it is meant to solve.

## 15. Testing and verification

MVCC's core guarantee, that a reader sees a consistent snapshot regardless of
concurrent writes, is straightforward to verify with a deterministic test.
In the entry's own reference implementations, `readAsOf` in Go, `read_as_of`
in Python, and `read_as_of` in Rust are all pure functions of the version
chain and a snapshot identifier, with no wall-clock or thread-scheduling
dependency in the visibility logic itself, so a unit test can assert exact
behavior by constructing a fixed sequence of writes and snapshot points
without any sleeps or timing-dependent assertions, which is the single most
valuable property to preserve when testing MVCC logic. Never assert timing,
always assert against explicit transaction identifiers.

What becomes easier to test because of MVCC. Read-path correctness under
concurrent writes, because a test can start a reader snapshot, apply
writes from other simulated transactions, and assert the reader still sees
its original snapshot deterministically, with no need to introduce artificial
delays or mocks to simulate isolation, since the isolation is structural
rather than timing-based.

What becomes harder to test because of MVCC. Garbage collection correctness,
because verifying that a version is removed only after it becomes
genuinely unreachable by any open snapshot requires modeling the full set of
concurrently open transactions, not only the two transactions directly
involved in a single test case, and a test that only checks single-reader,
single-writer behavior will miss a garbage-collection bug that only
manifests with three or more overlapping open snapshots. Write skew and
other snapshot-isolation anomalies, dimension 11, are also genuinely hard to
test deterministically against a real production database, because
reproducing the exact interleaving that triggers the anomaly typically
requires either a database-specific fault-injection setup or a formal
model checker such as TLA+ rather than an ordinary integration test, and
teams that rely on MVCC for correctness-critical invariants should model the
transaction interleaving explicitly rather than relying on flaky
integration-test timing to reveal an anomaly.

## 16. Observability signals

A healthy MVCC system shows a bounded, roughly stable relationship between
logical row count and physical storage size for a given table, a garbage
collection or vacuum process that completes regularly and keeps pace with
the write rate, and no transaction held open for longer than the
application's expected request duration. The specific indicators to log,
trace, or alert on are the transaction age of the oldest currently open
transaction, PostgreSQL exposes this via `pg_stat_activity.xact_start`,
alert when it exceeds a small threshold, minutes rather than hours, in any
high write-rate system; table or database bloat ratio, the difference between
logical and physical size, tracked over time rather than as a single
point-in-time measurement, since a slow upward trend is the actual indicator,
not any single reading; vacuum or purge lag, meaning how far behind the
garbage collector is running relative to the write rate, since a garbage
collector that never catches up is functionally equivalent to having no
garbage collection at all; and the count of currently held version chains
per row, or an equivalent proxy, since an unexpectedly long chain on a
specific hot row is the earliest visible symptom of a stuck removal
process on that row specifically, before it shows up in aggregate
table-level bloat metrics.

A failing instance shows steadily climbing table or index size unaccompanied
by a matching increase in logical row count, an oldest-open-transaction age
that grows without bound rather than oscillating around a small steady
value, query latency on the affected tables that degrades gradually over
days or weeks rather than failing suddenly, and, in the most severe case, a
database that begins refusing new transactions because it is approaching a
transaction identifier wraparound limit, which PostgreSQL reports as an
explicit, alertable warning well before the hard failure point (PostgreSQL
Documentation, "Preventing Transaction ID Wraparound Failures," accessed
2026-08-02, see References).

## 17. Security and privacy implications

MVCC's version retention has a direct and easily overlooked privacy
implication. Data a user believes has been deleted or overwritten may still
be physically present on disk, readable by any process with sufficient
storage access, for as long as some open transaction's snapshot could still
reference it, and in some engines for longer still if the garbage collector
has fallen behind. A delete operation under MVCC does not zero the bytes, it
marks the version as superseded and leaves the physical data recoverable
until the background process actually runs, which matters directly for any
system with a regulatory requirement to guarantee data is unrecoverable
after deletion, such as GDPR's right to erasure or a contractual data
destruction clause. A naive `DELETE` statement against an MVCC-backed table
does not, by itself, satisfy such a requirement, and teams building erasure
compliance on top of an MVCC database need to verify both that the
transaction deleting the row has committed and that the storage engine has
actually removed the old version, not merely marked it dead, or pursue a
more explicit approach such as encrypting the sensitive field with a
per-record key and destroying that encryption key on erasure instead of
relying on physical deletion timing.

A second, narrower implication concerns transaction identifiers and
timestamps themselves, which, in a system that exposes them at the
application layer, for example a `xmin`/`xmax`-based optimistic locking
scheme, or an API that shows a row's last-modified version, can leak a
coarse-grained indicator of write ordering and write frequency across the
whole database, not only the row in question, since transaction identifiers
are typically allocated from a single global counter shared by every table.
This is a narrow, low-severity concern relative to the erasure issue above,
but worth naming. An API response that includes a raw internal transaction
identifier is exposing more than the value of the row.

## 18. References

1. Reed, D. P. "Naming and Synchronization in a Decentralized Computer
   System." PhD thesis, MIT, 1978. Foundational proposal of timestamp-ordered
   multiversion storage.
2. Bernstein, P. A. and Goodman, N. "Multiversion Concurrency Control,
   Theory and Algorithms." ACM Computing Surveys, Vol. 15, No. 4, December
   1983. The formalizing survey most texts cite for the MVCC name and
   correctness proofs.
3. PostgreSQL Global Development Group. "Chapter 13. Concurrency Control,"
   PostgreSQL Documentation, current version.
   https://www.postgresql.org/docs/current/mvcc-intro.html
   Verified 2026-08-02.
4. PostgreSQL Global Development Group. "Serializable Isolation Level,"
   PostgreSQL Documentation, current version.
   https://www.postgresql.org/docs/current/transaction-iso.html#XACT-SERIALIZABLE
   Verified 2026-08-02.
5. PostgreSQL Global Development Group. "Routine Vacuuming," PostgreSQL
   Documentation, current version.
   https://www.postgresql.org/docs/current/routine-vacuuming.html
   Verified 2026-08-02.
6. PostgreSQL Global Development Group. "Preventing Transaction ID Wraparound
   Failures," PostgreSQL Documentation, current version.
   https://www.postgresql.org/docs/current/routine-vacuuming.html#VACUUM-FOR-WRAPAROUND
   Verified 2026-08-02.
7. Oracle Corporation. "Data Concurrency and Consistency," Oracle Database
   19c Database Concepts.
   https://docs.oracle.com/en/database/oracle/oracle-database/19/cncpt/data-concurrency-and-consistency.html
   Verified 2026-08-02.
8. Oracle Corporation. MySQL 8.4 Reference Manual, "InnoDB Multi-Versioning."
   https://dev.mysql.com/doc/refman/8.4/en/innodb-multi-versioning.html
   Verified 2026-08-02.
9. Cockroach Labs. "Storage Layer," CockroachDB Docs, stable release.
   https://docs.cockroachlabs.com/docs/stable/architecture/storage-layer
   Verified 2026-08-02.
10. Microsoft. "Snapshot Isolation in SQL Server," SQL Server Documentation.
    https://learn.microsoft.com/en-us/dotnet/framework/data/adonet/sql/snapshot-isolation-in-sql-server
    Judgement note. Title and general content confirmed against Microsoft
    Learn's SQL Server isolation-level documentation family. Not re-fetched
    live in this session, treat the specific quoted phrasing as
    representative rather than an exact quote.
11. SQLite Consortium. "Write-Ahead Logging," SQLite Documentation.
    https://sqlite.org/wal.html
    Judgement note. Cited for the general claim that SQLite's default
    rollback-journal mode is not MVCC and WAL mode is the closer analogue.
    Not re-fetched live in this session.

## Code examples

Three languages, each compiled or run against the exact source shown. Go and
Rust use a `sync.Mutex` / `std::sync::Mutex` to guard the version chain, which
is the plain, unavoidable technical term for the mutual-exclusion primitive
guarding the in-memory structure, not a figurative usage. Python uses
`threading.Lock` for the same purpose. All three implement the identical
version-chain-and-snapshot mechanism traced in dimensions 6 and 7. an ever
growing list of versions per row, a monotonically increasing transaction
counter, and a read that walks the list backward from the newest version to
find the first one whose begin and end range contains the reader's snapshot.
Java is omitted here because the mechanism is language-neutral (dimension 8's
language-idiomatic note) and three languages already show every concurrency
primitive this pattern needs; nothing about Java's syntax would change the
shape.

### Go

```go
package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

type version struct {
	txID  int64
	value int
	begin int64
	end   int64
}

type MVCCRow struct {
	mu       sync.Mutex
	versions []*version
}

type TxManager struct {
	nextTxID int64
}

func (tm *TxManager) begin() int64 {
	return atomic.AddInt64(&tm.nextTxID, 1)
}

func (row *MVCCRow) write(txID int64, value int) {
	row.mu.Lock()
	defer row.mu.Unlock()
	if len(row.versions) > 0 {
		row.versions[len(row.versions)-1].end = txID
	}
	row.versions = append(row.versions, &version{txID: txID, value: value, begin: txID, end: 1 << 62})
}

func (row *MVCCRow) readAsOf(snapshotTxID int64) (int, bool) {
	row.mu.Lock()
	defer row.mu.Unlock()
	for i := len(row.versions) - 1; i >= 0; i-- {
		v := row.versions[i]
		if v.begin <= snapshotTxID && snapshotTxID < v.end {
			return v.value, true
		}
	}
	return 0, false
}

func main() {
	tm := &TxManager{}
	row := &MVCCRow{}
	writer := tm.begin()
	row.write(writer, 100)
	reader := tm.begin()
	writer2 := tm.begin()
	row.write(writer2, 200)
	val, ok := row.readAsOf(reader)
	fmt.Println(val, ok)
}
```

Compiled and run with `go run mvcc.go` on Go's standard toolchain. Output.
`100 true`. The reader's snapshot was taken between `writer` and `writer2`, so
it sees the value written by `writer` (100) and never observes `writer2`'s
value (200), matching the visibility rule proven in dimension 7's dynamics
walk-through.

### Python

```python
from dataclasses import dataclass
from itertools import count
from threading import Lock

_tx_ids = count(1)


@dataclass
class Version:
    tx_id: int
    value: object
    begin: int
    end: float


class MVCCRow:
    def __init__(self):
        self._lock = Lock()
        self._versions: list[Version] = []

    def write(self, tx_id: int, value: object) -> None:
        with self._lock:
            if self._versions:
                self._versions[-1].end = tx_id
            self._versions.append(Version(tx_id, value, tx_id, float("inf")))

    def read_as_of(self, snapshot_tx_id: int):
        with self._lock:
            for v in reversed(self._versions):
                if v.begin <= snapshot_tx_id < v.end:
                    return v.value
            return None


if __name__ == "__main__":
    row = MVCCRow()
    writer = next(_tx_ids)
    row.write(writer, 100)
    reader = next(_tx_ids)
    writer2 = next(_tx_ids)
    row.write(writer2, 200)
    print(row.read_as_of(reader))
```

Run with `python3 mvcc.py`. Output. `100`. Same visibility outcome as the Go
version, confirming the mechanism is identical across languages, only the
concurrency primitive differs.

### Rust

```rust
use std::sync::atomic::{AtomicI64, Ordering};
use std::sync::Mutex;

struct Version {
    begin: i64,
    end: i64,
    value: i64,
}

struct MvccRow {
    versions: Mutex<Vec<Version>>,
}

impl MvccRow {
    fn new() -> Self {
        MvccRow { versions: Mutex::new(Vec::new()) }
    }

    fn write(&self, tx_id: i64, value: i64) {
        let mut versions = self.versions.lock().unwrap();
        if let Some(last) = versions.last_mut() {
            last.end = tx_id;
        }
        versions.push(Version { begin: tx_id, end: i64::MAX, value });
    }

    fn read_as_of(&self, snapshot_tx_id: i64) -> Option<i64> {
        let versions = self.versions.lock().unwrap();
        versions
            .iter()
            .rev()
            .find(|v| v.begin <= snapshot_tx_id && snapshot_tx_id < v.end)
            .map(|v| v.value)
    }
}

static NEXT_TX_ID: AtomicI64 = AtomicI64::new(1);

fn begin_tx() -> i64 {
    NEXT_TX_ID.fetch_add(1, Ordering::SeqCst)
}

fn main() {
    let row = MvccRow::new();
    let writer = begin_tx();
    row.write(writer, 100);
    let reader = begin_tx();
    let writer2 = begin_tx();
    row.write(writer2, 200);
    println!("{:?}", row.read_as_of(reader));
}
```

Compiled with `rustc -O mvcc.rs -o mvcc_rs` and run as `./mvcc_rs`. Output.
`Some(100)`. All three implementations were compiled or run against these
exact sources during authoring of this entry, not hand-verified only.
