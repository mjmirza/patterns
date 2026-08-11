---
name: Pessimistic Offline Lock
slug: pessimistic-offline-lock
family: 06-enterprise-application-architecture
category: Concurrency
aliases: [Exclusive Checkout, Lock Manager Pattern, Editing Lock]
first_described: "Fowler 2002"
maturity: canonical
related: [optimistic-offline-lock, unit-of-work, coarse-grained-lock, identity-map]
incompatible_with: [optimistic-offline-lock]
verified: 2026-08-02
---

# Pessimistic Offline Lock

## 1. Name, aliases, and lineage

The canonical name is Pessimistic Offline Lock. Martin Fowler catalogued it in
*Patterns of Enterprise Application Architecture*, Addison-Wesley, 2002, in the
Concurrency chapter, paired directly against Optimistic Offline Lock as the two
answers to the same problem, business transactions that span more than one
system-level request (Martin Fowler, "Pessimistic Offline Lock",
https://martinfowler.com/eaaCatalog/pessimisticOfflineLock.html, verified
2026-08-02). The word offline in the name does not mean disconnected from a
network. It means the lock protects a business transaction that spans multiple
requests and multiple system transactions, as opposed to a database lock that
lives entirely inside one system transaction and is released when that
transaction commits or rolls back. Fowler is explicit about this distinction
in the same catalog entry, contrasting an offline business transaction, which
might run for minutes while a person edits a form, against a system
transaction, which runs for milliseconds inside a database.

Two older names describe the same mechanism from different angles. Exclusive
Checkout is the name used in configuration management and document management
systems that predate Fowler's catalog by decades, RCS (Revision Control
System) and CVS both implement lock-modify-release as their default concurrency
model, where `rcs -l` or `cvs edit -c` places an exclusive lock on a file
before it can be modified (Walter F. Tichy, "RCS. A System for Version
Control", Software. Practice and Experience, Volume 15, Issue 7, 1985, pages
637 to 654, describing the lock command as the mechanism that serialises
concurrent edits). Lock Manager Pattern is the name used inside the pattern
itself for the component that owns the lock table, and several practitioner
write-ups use it as the entry's informal name because the pattern is, in
practice, mostly about designing that one component. Editing Lock is the name
users see in the product, Confluence calls it a page lock, SharePoint and
Documentum call it a checkout, and neither surfaces the word pessimistic
anywhere in the interface, because the term is an implementation detail of how
the concurrency control is achieved, not a concept a business user needs.

The pattern is older than its Fowler citation in practice, RCS shipped in 1982
and CVS in 1986, both built on an exclusive lock model, twenty years before the
catalog entry gave the approach a name inside enterprise application
architecture and set it against its optimistic counterpart as a named trade-off
rather than as the only available option.

## 2. Problem and context

A business transaction in an enterprise application routinely spans more than
one system-level request. A person opens a purchase order for editing, looks
at the current line items, steps away for a phone call, comes back, changes the
quantity on line three, and clicks save. Between the open and the save there
might be one request or there might be forty, and there might be five minutes
or five hours. During that whole window, no database transaction is open. The
system transaction that fetched the order to display it committed the instant
the read finished. The system transaction that will apply the save has not
started yet. The application-level business transaction, the person's single
continuous act of editing this one order, has no database mechanism protecting
it at all, because a database transaction that stayed open for the whole
editing session would hold row locks or MVCC snapshot resources for an
unbounded and unpredictable length of time, which no production database
tolerates well under real concurrent load.

Without any protection, two people can open the same order, both see the
original state, both make different edits, and whichever one saves second
silently overwrites the first person's change with no error and no warning.
This is the lost update problem, and it is exactly the failure mode both
Pessimistic Offline Lock and Optimistic Offline Lock exist to prevent. The two
patterns differ only in when they detect the conflict. Optimistic Offline Lock
lets both people edit freely and detects the conflict at save time, by
comparing a version stamp captured at read time against the current version
stamp in storage, failing the second save with a conflict error. Pessimistic
Offline Lock detects the conflict at edit-start time instead, by having the
first person's open-for-edit action acquire an exclusive lock that the second
person's open-for-edit action then fails to acquire, so the second person is
told at the moment they try to start editing, not after they have done work
that then has to be discarded.

The context in which this matters is not every concurrent-editing situation.
It matters specifically where the cost of discovering a conflict late is high,
where the edit itself is expensive to redo, where the business process cannot
tolerate a merge, and where the population of concurrent editors on the same
record is small enough that contention for the lock itself is rare. A single
shared configuration file that three administrators occasionally edit is a
good fit. A social media post that ten thousand people might comment on
simultaneously is not, because there the writes do not actually collide with
each other in a way a single record-level lock could sensibly serialise.

## 3. Forces

Latency is the force this pattern sacrifices most visibly. The moment a lock
manager sits between a person and the record they want to edit, every
edit-start operation now costs a round trip to acquire the lock and check it
against the lock table, and every abandoned edit session, a closed browser tab,
a crashed client, a network partition, either leaves the record locked forever
or requires a timeout mechanism whose own latency cost is the risk of an
expired lock releasing while the original editor is still legitimately mid-edit.

Coupling rises because every code path that can mutate the protected resource
now has to check in with the lock manager, including paths that are not the
one you designed the locking for, a batch import job, an administrative bulk
edit tool, a data migration script. Every one of these either has to acquire
the lock through the same manager or the lock provides no real guarantee,
because a system-transaction-scoped lock only protects the code that remembers
to ask for it.

Consistency is what the pattern buys, and it buys a strong, simple kind. As
long as every mutator goes through the lock manager, exactly one business
transaction can be mid-edit on a given resource at a time, and that guarantee
holds even across process restarts if the lock table is persistent, which
Optimistic Offline Lock cannot promise at edit-start time because it detects
the conflict only at commit time.

Operability is a real cost most catalog treatments underweight. A pessimistic
lock that outlives its owner, because the owning process crashed, because a
network partition dropped the release message, because a person walked away
from their desk on a Friday afternoon, becomes an operational incident that
someone has to notice and manually break. The lock manager needs its own
monitoring, its own break-glass procedure, and usually a lock-owner audit trail,
none of which the pattern's short catalog description mentions but all of
which real deployments end up building.

Cost and team topology interact through the lock manager's own availability.
If the lock manager is a single database table guarded by row locks, every
edit-start and edit-end across the whole application now depends on that
table's availability, and it becomes a shared point of contention across teams
whose services otherwise have nothing to do with each other, which is exactly
the coupling a service-oriented or microservice topology tries to avoid.

Cognitive load falls on whoever reads the code later. Pessimistic Offline Lock
is, by contrast with Optimistic Offline Lock, easy to reason about locally,
one lock, one owner, one clear failure mode of lock denied. The harder
cognitive burden shows up at the edges, at timeout tuning, at what happens when
two different lock managers in a distributed system disagree about who holds a
lock, and at how a person explains to another person why their five minute old
edit lock just silently expired while they were still typing.

## 4. Applicability and non-applicability

Reach for Pessimistic Offline Lock when the resource being edited is coarse
enough that whole-record locking is the natural unit, when concurrent editors
of the same specific record are rare enough that lock contention itself will
not become the bottleneck, when the cost of a lost update is high relative to
the cost of a person occasionally being told the record is locked, when the
editing session is long enough or the merge is hard enough that Optimistic
Offline Lock's late failure would waste real work, and when the application
already has, or can afford to build, a reliable mechanism for releasing locks
whose owning session has died.

Do not reach for it in the following situations, and each reason is the
specific mechanism, not a restatement of the applicability list.

- **High-concurrency reads and writes on the same hot record.** A shopping
  cart, an inventory counter under flash-sale load, a leaderboard score. Here
  the lock itself becomes the bottleneck, every writer serialises behind the
  lock manager regardless of whether their edits would actually have
  conflicted, and throughput collapses to one writer at a time for that record.
  A counter-style resource is better served by an atomic increment operation
  or Optimistic Offline Lock's narrower conflict window.
- **Distributed systems where the lock owner and the lock manager can partition
  from each other.** A network partition that isolates the lock manager from
  the process holding the lock creates the split-brain question of whether the
  lock is still valid, and a naive implementation either blocks every other
  writer indefinitely, waiting for a partition that may never heal, or expires
  the lock while the original holder is still legitimately working and has no
  way to know its lock was revoked out from under it.
- **Offline-first or eventually-consistent clients.** A mobile app that must
  function without a live connection to the lock manager cannot acquire a
  pessimistic lock before editing, because acquiring a lock is itself an online
  operation. Fowler notes this explicitly, disconnected clients cannot use
  Pessimistic Offline Lock at all and must fall back to Optimistic Offline Lock
  or a conflict-free replicated data type.
- **Collaborative real-time editing of the same document by design.** Google
  Docs and Figma's live multiplayer editing are built on operational
  transformation or conflict-free replicated data types precisely because
  the product goal is simultaneous editing, which a mutual-exclusion lock
  actively prevents rather than enables.
- **Short, cheap, idempotent operations.** If reapplying the operation on
  conflict is free, for example toggling a boolean flag or incrementing a
  view counter, the overhead of acquiring and releasing a lock exceeds the
  cost of simply detecting and retrying a conflict, which is what Optimistic
  Offline Lock or a database-level compare-and-swap already does more cheaply.
- **Very large numbers of independently-editable sub-resources inside one
  aggregate.** Locking the whole aggregate to protect one field starves every
  editor of every other field. This is the specific failure this pattern's own
  catalog entry calls out as a reason to consider a finer locking granularity,
  which trades simplicity for the added complexity of partial locks.

## 5. Structure

The pattern names three participants and one supporting concept.

- **Lock Manager.** The single component that owns the lock table and answers
  three questions authoritatively, can this session acquire a lock on this
  resource, does this session currently hold this lock, and release this
  session's lock on this resource. Every other participant talks to the
  resource only through the Lock Manager. The Lock Manager is the only
  component allowed to write the lock table.
- **Resource.** The domain object, record, or aggregate being protected. The
  Resource itself carries no locking logic. It is identified by a stable key
  that the Lock Manager uses as the lock table's primary key.
- **Session (or Owner).** The unit of work on whose behalf a lock is held, a
  logged-in user's HTTP session, a background job's run identifier, a
  long-running business process instance. The Session is what the lock is
  granted to, not the physical connection or thread that happens to be making
  the request at any given moment, because a person's editing session
  routinely spans many separate HTTP requests over separate connections.
- **Lock table.** The persistent record of who holds what. It must survive
  application restarts if the lock is meant to survive them, which for a
  business transaction spanning minutes or hours it usually must, so the lock
  table is almost always a database table, not an in-memory structure, unless
  the pattern is being implemented for a much shorter-lived, single-process
  scope.

Fowler's catalog entry also names three lock strategies as implementation
variants of the same structural roles, exclusive write lock, which is the
default described above and only blocks other writers, read lock, which also
blocks readers from seeing data that is mid-edit, and exclusive lock, which
blocks readers and writers both. These are strategy choices inside the Lock
Manager's grant logic, not separate structural participants.

## 6. ASCII structure diagram

```
+-------------------+          +--------------------+
|      Session       |          |    Lock Manager     |
|  (owns a token or   |--------->|  acquire(res, sess)  |
|   session id)       |          |  release(res, sess)  |
+-------------------+          |  isLocked(res)      |
          |                     +----------+-----------+
          |                                |
          | reads/writes via                | reads/writes
          | the domain layer                |
          v                                v
   +----------------+              +------------------+
   |    Resource     |              |   Lock Table      |
   | (order, doc,     |              | resource_id       |
   |  record, ...)    |              | owner_session_id  |
   +----------------+              | acquired_at        |
                                    | expires_at         |
                                    +------------------+
```

## 7. Dynamics

```
Session A                Lock Manager             Resource / Lock Table
   |                           |                          |
   | open-for-edit(order#42)   |                          |
   |-------------------------->|                          |
   |                           | check lock table for #42  |
   |                           |------------------------->|
   |                           |   no row found            |
   |                           |<-------------------------|
   |                           | insert lock row           |
   |                           |   (owner=A, acquired=now) |
   |                           |------------------------->|
   |   lock granted             |                          |
   |<--------------------------|                          |
   |                           |                          |
   |                    Session B                          |
   |                        |                              |
   |                        | open-for-edit(order#42)      |
   |                        |------------------------------|
   |                        |    lock table has owner=A     |
   |                        |<------------------------------|
   |                        |   lock DENIED, owner=A         |
   |                        |    (with a way to contact A)   |
   |                        v                              |
   |                                                        |
   | ... A edits across several requests, minutes pass ...  |
   |                                                        |
   | save(order#42, changes)   |                          |
   |-------------------------->|                          |
   |                           | verify A still owns lock  |
   |                           |------------------------->|
   |                           |    yes, owner=A            |
   |                           |<-------------------------|
   |                           | apply changes, delete lock |
   |                           |------------------------->|
   |   save confirmed           |                          |
   |<--------------------------|                          |
```

A second, essential dynamic is lock expiry, because the flow above assumes A
behaves well and eventually saves or explicitly cancels. In practice A closes
the laptop lid mid-edit far more often than the diagram suggests.

```
Session A                 Lock Manager              Background Reaper
   |                            |                            |
   | acquires lock, expires_at   |                            |
   |    = now + 30 minutes       |                            |
   |----------------------------->|                          |
   |  A's browser crashes         |                            |
   |  (no release ever sent)      |                            |
   |                              |     every N minutes:       |
   |                              |     scan for expires_at    |
   |                              |     older than now         |
   |                              |<----------------------------|
   |                              |     delete expired rows     |
   |                              |----------------------------->|
   |                              |  (Session B can now acquire) |
```

## 8. Implementation variants

The most common shape in database-backed applications is a **dedicated lock
table**, a single relational table keyed by resource identifier, holding the
owning session identifier, an acquisition timestamp, and either an expiry
timestamp or a heartbeat timestamp the owning session refreshes periodically
while it is still legitimately editing. Acquisition is a single
`INSERT ... ON CONFLICT DO NOTHING` or the equivalent, made atomic by the
database's own row uniqueness constraint on the resource identifier column,
so the database itself serialises concurrent acquisition attempts and the
application never has to implement its own mutual exclusion logic on top.

A second variant piggybacks on **native database row locks**, `SELECT ... FOR
UPDATE` in PostgreSQL and MySQL InnoDB, or `SELECT ... FOR UPDATE NOWAIT` to
fail fast instead of blocking. This is a genuinely different mechanism from
the dedicated lock table variant, because a native row lock is scoped to the
database transaction that took it and is released automatically when that
transaction commits, rolls back, or the holding connection dies, which solves
the crashed-client-leaves-a-stale-lock problem for free at the cost of
requiring the business transaction to be expressed as one long-held database
transaction, which is precisely the resource-holding cost Fowler's offline
terminology exists to warn against for anything longer than a few seconds.
This variant is therefore mostly seen for short pessimistic locks inside a
single request, an inventory reservation held for the few hundred milliseconds
of a checkout flow, not for a person's multi-minute editing session.

A third variant is the **explicit checkout model** used by version control and
document management systems, where acquiring the lock also checks out a
working copy of the resource to the requesting session, and the lock is a side
effect of the checkout rather than a separate call. RCS and CVS implement
concurrency this way by default, `rcs -l` locks a file and marks it writable
locally, and the corresponding release action, `rcs -u` or a checkin, both releases
the lock and publishes the new revision in the same operation (Walter F.
Tichy, "RCS. A System for Version Control", Software. Practice and Experience,
Volume 15, Issue 7, 1985, pages 637 to 654).

A fourth variant, common in distributed systems rather than single-database
applications, uses a **distributed lock service** such as Apache ZooKeeper's
ephemeral znodes or a Redis-based algorithm, where the lock's liveness is tied
to a session heartbeat with the lock service rather than to a fixed expiry
timestamp, so the lock survives exactly as long as the owning process keeps
proving it is alive, and is released automatically, without a separate reaper
process, the moment that heartbeat stops (Flavio P. Junqueira and Benjamin
Reed, *ZooKeeper. Distributed Process Coordination*, O'Reilly Media, 2013,
chapter 2, "Getting Started with ZooKeeper", describing ephemeral znodes and
their session-tied lifetime as the primitive locking recipes are built on).
This variant trades the simplicity of a single database table for the
operational cost of running and reasoning about a separate coordination
service, and it introduces the split-brain question named in dimension 4,
what a lock means during a network partition between the lock service and its
own quorum, which the ZooKeeper documentation itself discusses at length under
session and watch semantics.

## 9. Known production uses

**Git LFS file locking.** Git LFS (Large File Storage) implements an explicit
pessimistic lock as a first-class feature, `git lfs lock <path>`, specifically
because binary assets, art files, video, compiled objects, cannot be
three-way merged, so Git's normal optimistic copy-modify-merge model produces
unusable results on conflict. The lock is server-side, tied to the requesting
user, and `git lfs locks` lists current holders so a team can see who is
editing which binary file before starting their own edit (GitHub Docs,
"Configuring Git Large File Storage",
https://docs.github.com/en/repositories/working-with-files/managing-large-files/configuring-git-large-file-storage,
section on file locking, verified 2026-08-02).

**PostgreSQL and MySQL row-level `SELECT ... FOR UPDATE`.** Both databases
implement pessimistic row locking as a core primitive that application-level
lock managers are frequently built on top of. The PostgreSQL documentation
describes `FOR UPDATE` as causing rows retrieved by a `SELECT` to be locked as
though for an update, so that no other transaction can lock, modify, or delete
them until the current transaction ends (PostgreSQL 17 Documentation, "13.3.2.
Row-level Locks", https://www.postgresql.org/docs/current/explicit-locking.html,
verified 2026-08-02). Django's ORM exposes this directly as
`QuerySet.select_for_update()`, and its own documentation states the method
returns a queryset that will lock rows until the end of the transaction,
implementing the pessimistic locking behaviour of `SELECT ... FOR UPDATE` (
Django Project, "Database transactions, select_for_update()",
https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update,
verified 2026-08-02).

**RCS and CVS lock-modify-release.** Both version control systems, and the
lock-modify-release model they popularised, are the historical origin cited by
Fowler's own catalog entry for the concept, and the model remains the default
in centralised systems that predate distributed version control, described in
the original RCS paper's discussion of the `-l` lock and `-u` release commands
as the mechanism preventing two authors from checking in conflicting revisions
of the same file (Walter F. Tichy, "RCS. A System for Version Control",
Software. Practice and Experience, Volume 15, Issue 7, 1985, pages 637 to 654).

**Apache ZooKeeper distributed lock recipe.** ZooKeeper's own documentation
publishes an explicit recipe for building a pessimistic distributed lock on
top of ephemeral sequential znodes, where a client creates an ephemeral node
under a lock path, is granted the lock if its node has the lowest sequence
number among siblings, and otherwise watches the next-lowest sibling, so the
lock is automatically released if the holding session dies because the
ephemeral node is removed by ZooKeeper itself (Apache ZooKeeper Project,
"ZooKeeper Recipes and Solutions, Locks",
https://zookeeper.apache.org/doc/current/recipes.html, verified 2026-08-02).

## 10. Consequences

Positive consequences follow from detecting the conflict at the earliest
possible point. The second editor is told immediately, at the moment they try
to start work, rather than after investing time in an edit that will then be
discarded, which is a materially better experience whenever the edit itself is
expensive to redo. The guarantee the pattern provides is also simple to reason
about, exactly one business transaction can be actively editing a given
resource at a time, with no window in which two conflicting versions of the
truth can simultaneously exist in application memory, which makes the
concurrency story easy to explain to a person who is not a distributed systems
specialist. Because the lock check happens up front, the code paths that apply
the actual mutation do not need to carry conflict-detection or merge logic at
all, that complexity concentrates entirely in the Lock Manager, which is a
real separation-of-concerns win over Optimistic Offline Lock, where every
writer has to handle a possible version-conflict exception.

Negative consequences begin with the availability trade the pattern makes.
Wherever a lock is held, every other session is blocked from that specific
edit, full stop, and this holds even when the second session's intended edit
would not actually have conflicted with the first session's edit, for example
two people editing different fields of the same coarse-grained record. A
pessimistic lock whose owning session dies without releasing it becomes a
resource nobody can edit until either a timeout fires or an operator
intervenes, and both of those remedies carry their own risk, a timeout that
fires too early can silently revoke a lock while its original owner is still
legitimately mid-edit, producing exactly the lost-update bug the pattern was
built to prevent, just relocated to a different failure path. The pattern also
does not compose with disconnected or offline clients, because acquiring a
lock is itself an online operation that a client with no connectivity cannot
perform, a limitation Fowler's own catalog entry states directly. Finally, the
Lock Manager itself becomes a single, shared point of coupling across the
whole application, every code path capable of mutating a locked resource type
must go through it, and any code path that forgets to, a batch job, an
administrative tool, a data migration, silently bypasses the guarantee the
pattern exists to provide.

## 11. Failure modes and misuse

**Symptom.** Users report that a record is permanently stuck as locked by a
colleague who insists they closed the editor hours ago and are not touching it.
**Cause.** The lock's release is tied to an explicit action, closing the tab
gracefully, calling a save or cancel endpoint, rather than to a mechanism that
detects the absence of the owner, and the owning browser tab, process, or
connection terminated abnormally, a crash, a lost network connection, a forced
logout, without ever sending the release call.
**Fix.** Give every lock a bounded lifetime, either a hard expiry timestamp
refreshed by a periodic heartbeat from the still-active editing session, or a
liveness mechanism tied to the underlying connection itself, such as a
ZooKeeper ephemeral node or a database session-scoped advisory lock, so the
lock's continued existence is provable rather than merely assumed, and pair it
with an explicit and clearly labelled "force release" administrative action for
the cases the automatic mechanism cannot cover.

**Symptom.** A migration script or a nightly batch job silently overwrites
changes a user made through the normal editing UI just minutes earlier, with
no error anywhere in either code path.
**Cause.** The batch job writes directly to the resource's storage, bypassing
the Lock Manager entirely, either because it was written before the locking
scheme existed and nobody revisited it, or because the developer reasoned,
correctly on its own terms but incorrectly for the system as a whole, that a
batch job running at 2 AM would never actually collide with a live user.
**Fix.** Make every write path to a lockable resource, without exception, go
through the same Lock Manager, including batch and administrative tooling,
and enforce this at the data access layer rather than trusting each caller to
remember, for example by having the resource's repository or DAO refuse a
write on a locked resource unless the caller presents a valid lock token for
the current holder.

**Symptom.** Under moderate concurrent load, most edit-start requests for a
popular resource fail with lock denied, even though the actual edit windows
are short, and users describe the application as feeling like it is
constantly fighting them.
**Cause.** The lock granularity is too coarse for the actual contention
pattern, a single lock on an entire large aggregate, an order with forty line
items, a document with sixty sections, when the real edits are almost always
scoped to one small part of it, so unrelated concurrent edits collide on the
lock even though they would never have collided on the actual data.
**Fix.** Narrow the lock granularity to the smallest unit that is
independently meaningful to edit, a line item rather than the whole order, a
section rather than the whole document, accepting the added bookkeeping
complexity of tracking multiple simultaneous locks per aggregate, or, if the
contention pattern suggests true simultaneous multi-user editing is the actual
product requirement rather than an edge case, reconsider whether pessimistic
locking is the right pattern at all against a merge-based or operational
transformation approach.

**Symptom.** The application deadlocks intermittently under load, two
different user sessions both stuck waiting, neither making progress, and the
only remedy operators have found is restarting the affected processes.
**Cause.** A single business transaction acquires more than one lock, on two
different resources, in an order that is not consistent across all code
paths, so session A acquires lock 1 then waits for lock 2 while session B has
already acquired lock 2 and is waiting for lock 1, the classic lock-ordering
deadlock, made worse here because the locks are long-held offline locks rather
than short-held database transaction locks, so the deadlock can persist for
the full length of a human editing session rather than resolving in
milliseconds via a database's own deadlock detector.
**Fix.** Establish and enforce a single, global, consistent ordering for
acquiring locks on multiple resources within one business transaction, for
example always by ascending resource identifier, so a cycle of the kind above
becomes structurally impossible, and add an explicit deadlock-detection
timeout as a defence-in-depth backstop rather than relying on lock ordering
discipline alone to hold across every future code path.

## 12. Trade-off matrix

| Force | Pessimistic Offline Lock | Optimistic Offline Lock | Coarse-Grained Lock alone |
|---|---|---|---|
| When conflict is detected | At edit-start, before any work is done | At save-time, after the edit is complete | Depends on which underlying pattern it wraps |
| Read/write throughput under high contention | Degrades sharply, one editor at a time per lock | Stays high, conflicts are rare in practice for most workloads | Same as whichever concurrency pattern it is applied to |
| Behaviour for disconnected or offline clients | Cannot be used, acquiring a lock requires connectivity | Works naturally, the client just risks a conflict at sync time | Same limitation as the wrapped pattern |
| Operational burden | Real, needs lock expiry, a reaper, and a break-glass release procedure | Low, a version column and a comparison, no separate lock lifecycle | Adds its own aggregate-boundary bookkeeping |
| User experience on conflict | Told immediately, before wasting effort | Told after finishing the edit, may need to redo work or merge | Depends on the underlying pattern |
| Code complexity at the mutation site | Low, the Lock Manager already guaranteed exclusivity | Higher, every writer must handle a possible version conflict | Adds coordination logic across the aggregate's members |
| Fit for coarse aggregates with many independent sub-parts | Poor unless lock granularity is narrowed below the aggregate | Good, conflicts are detected per field or per version, not per lock | This is the pattern's own specialty, defines the aggregate's lock scope |

## 13. Related and incompatible patterns

Pessimistic Offline Lock and **Optimistic Offline Lock** are catalogued by
Fowler side by side as the two competing solutions to the same lost-update
problem, and they are structurally incompatible to apply to the same resource
at the same time, because Optimistic Offline Lock's premise is that
concurrent editing is allowed and detected afterward, while Pessimistic
Offline Lock's premise is that concurrent editing is prevented up front. A
system can legitimately use one pattern for one resource type and the other
for a different resource type, choosing per resource based on the forces in
dimension 3, but applying both to the same resource simultaneously produces
no coherent conflict-resolution story.

**Coarse-Grained Lock**, also catalogued by Fowler in the same Concurrency
chapter, is a companion rather than a competitor, it answers the separate
question of what unit an offline lock should be scoped to when a business
transaction touches a graph of related objects, for example locking an entire
order aggregate with one lock rather than acquiring forty separate locks for
forty line items, and it composes directly with Pessimistic Offline Lock as
the mechanism deciding the lock's granularity.

**Unit of Work** is the pattern that typically triggers the need for
Pessimistic Offline Lock in the first place, because a Unit of Work tracks
changes across a business transaction and commits them together at the end,
and the gap between when the Unit of Work starts tracking a change and when
it commits is precisely the window Pessimistic Offline Lock is protecting.

**Identity Map**, in the same chapter's neighbourhood, solves a related but
distinct problem, so that within a single process, a given database row
is represented by exactly one in-memory object, which matters for
Pessimistic Offline Lock because a naive lock check that queries the lock
table fresh on every access can be made more efficient once an Identity Map
guarantees there is only one in-memory representative of the locked resource
to check against.

## 14. Refactoring path in and out

Introducing Pessimistic Offline Lock into a codebase that has none typically
starts from an observed lost-update incident, a support ticket describing two
users' edits colliding, rather than from a speculative design decision, because
the pattern's cost is real and should be justified by a demonstrated need.

The first step is adding a lock table and a Lock Manager component with two
operations, acquire and release, and wiring the resource's existing edit-start
action, whatever currently loads the record into an edit form, to call acquire
first and to surface a clear denial message when it fails. This step alone,
even before touching the save path, already prevents a second user from
opening the edit form while the first is mid-edit, which stops the most
visible symptom immediately.

The second step is wiring the save action to verify the calling session still
holds the lock before applying the write, and to release the lock as part of
a successful save, because without this verification a lock that expired
mid-edit due to a timeout would silently let a stale session's save through
anyway, defeating the point of the check.

The third step is adding the expiry and heartbeat mechanism from dimension 11,
because a Pessimistic Offline Lock without a liveness story reliably
degrades into an operational incident generator within the first few weeks of
real usage, and retrofitting this after the fact, once users have already
learned to distrust the "record locked" message because it is so often stale,
is harder than building it in from the start.

Removing the pattern, when a resource's contention pattern turns out to be
low enough or its edits turn out to be mergeable enough that the operational
cost is no longer justified, follows the reverse order and is genuinely
simpler than introducing it. Replace the acquire call at edit-start with
nothing, or with a read of the current version stamp if migrating to
Optimistic Offline Lock, replace the save-time lock-ownership check with a
version-stamp comparison, and delete the lock table and its reaper process
last, once monitoring confirms no code path still reads it. Migrating from
Pessimistic to Optimistic Offline Lock on the same resource is a common
enough refactor that it is worth treating as its own named step rather than
as a special case of pure removal, because it requires adding a version
column to the resource before the lock table can be safely dropped.

## 15. Testing and verification

Unit tests around the Lock Manager itself are straightforward and should
cover the state machine directly, without any real database or network
involved, an in-memory or fake implementation of the lock table is entirely
sufficient. Verify that acquire succeeds when the resource is unlocked, fails
when it is already locked by a different session, succeeds again for the same
session that already holds the lock, which is idempotent re-acquisition,
release only succeeds for the session that actually holds the lock, and an
expired lock is treated as absent by acquire even before the reaper has run,
so expiry checking is not solely dependent on the background sweep timing.

Testing the concurrency guarantee itself, that two genuinely simultaneous
acquire attempts against the same resource never both succeed, is the part
naive test suites get wrong, because a sequential test that calls acquire,
asserts success, then calls acquire again and asserts failure, never actually
exercises the race. This needs a true concurrency test, spawning multiple
threads or processes that call acquire at the same time against a shared lock
manager instance and asserting that across many repeated runs exactly one
ever succeeds, which is what actually proves the atomicity of the acquisition
operation rather than merely proving the happy-path logic reads correctly in
isolation.

What becomes easier to test as a direct consequence of this pattern is the
resource's mutation logic itself, because by the time a mutation is applied
the Lock Manager has already guaranteed exclusive access, so the mutation
code and its tests never need to consider a concurrent-write scenario at all,
which is real complexity Optimistic Offline Lock's writers do have to carry
in their own tests, exercising the version-conflict exception path.

What becomes harder to test is the full lifecycle under realistic failure
conditions, a client that acquires a lock and then genuinely disappears mid
test, simulating a crash rather than a graceful release, verifying the reaper
correctly frees the lock after the configured timeout and not before, and
verifying that a second legitimate acquisition attempt made a moment before
expiry correctly fails while one made a moment after correctly succeeds,
which are timing-sensitive tests that benefit from an injectable or fakeable
clock rather than relying on real wall-clock sleeps in the test suite.

## 16. Observability signals

A healthy Lock Manager, watched on a dashboard, shows a lock table whose row
count tracks closely with the number of users actively editing something
right now, rising and falling with daily traffic, and a lock hold duration
distribution whose vast majority of entries fall well under the configured
expiry window, most edits finishing and releasing their lock in seconds to a
few minutes.

The signals worth alerting on are the ones that indicate the operational
failure modes from dimension 11 directly. A rising count of locks reaped due
to expiry rather than released via an explicit save or cancel action is the
leading indicator of the stale-lock problem, and a sudden spike in it usually
correlates with a client-side deployment that introduced a crash or a
connectivity regression. A rising rate of lock-denied responses on the
edit-start operation, tracked as its own metric distinct from generic error
rates, signals either genuine growth in concurrent editing of the same
resources, worth investigating whether the lock granularity needs narrowing
per dimension 11, or a bug where a code path is failing to release locks it
successfully acquired. Average and maximum lock hold duration, tracked per
resource type rather than as one global number, surfaces the case where one
particular resource type's editing workflow has grown unexpectedly long, for
example because a form gained new fields that make editing take longer, which
is exactly the kind of drift that quietly turns a previously reasonable
expiry timeout into one that is now too short.

Every acquire, release, and expiry-reap event is worth logging with the
resource identifier, the owning session identifier, and a timestamp, because
this audit trail is the tool an operator actually reaches for when a user
reports a stuck lock, tracing back through the log to see exactly when it was
acquired, by whom, and whether it was ever legitimately released, is
materially faster than trying to reconstruct the same story from application
error reports alone.

## 17. Security and privacy implications

The lock table itself is a small but real disclosure surface. Its owner field
necessarily identifies which user or session currently holds a lock on a
given resource, and an endpoint that exposes lock status, showing users "this
record is being edited by X" so they know who to contact, is by design
revealing which specific person is currently looking at a specific record.
For most business records this is an acceptable and even useful disclosure,
but for a resource whose very existence or whose editors' identities are
themselves sensitive, a case file, a personnel record under active
investigation, exposing the current editor's identity to any user who
attempts to open the same record for editing may itself be an information
leak worth explicit review, and the lock status endpoint should generally
respect the same authorization checks as the resource it is reporting on
rather than being treated as a lower-sensitivity, purely operational
endpoint.

A more actionable concern is denial of service through lock hoarding. Because
acquiring a lock is a cheap operation and holding one blocks every other
legitimate editor, an authenticated but malicious or simply careless client
that repeatedly acquires locks on many resources and never releases them,
whether by design or by a buggy automated script hammering the edit-start
endpoint, can degrade the application for every other user far out of
proportion to the attacker's own resource consumption, which is a classic
amplification pattern worth defending against with per-session or per-user
rate limits on lock acquisition, independent of whatever general API rate
limiting the application already applies, plus a maximum lock hold duration
that is enforced regardless of any client-supplied heartbeat, so a
misbehaving client cannot simply refresh a lock forever by repeatedly
extending it.

## 18. References

1. Martin Fowler, "Pessimistic Offline Lock", Patterns of Enterprise
   Application Architecture catalog,
   https://martinfowler.com/eaaCatalog/pessimisticOfflineLock.html, verified
   2026-08-02.
2. Martin Fowler, *Patterns of Enterprise Application Architecture*,
   Addison-Wesley, 2002, Concurrency chapter, pages covering Pessimistic
   Offline Lock and Optimistic Offline Lock.
3. Walter F. Tichy, "RCS. A System for Version Control", Software. Practice
   and Experience, Volume 15, Issue 7, 1985, pages 637 to 654.
4. GitHub Docs, "Configuring Git Large File Storage", file locking section,
   https://docs.github.com/en/repositories/working-with-files/managing-large-files/configuring-git-large-file-storage,
   verified 2026-08-02.
5. PostgreSQL Global Development Group, "PostgreSQL 17 Documentation, 13.3.2.
   Row-level Locks", https://www.postgresql.org/docs/current/explicit-locking.html,
   verified 2026-08-02.
6. Django Software Foundation, "QuerySet API reference, select_for_update()",
   https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update,
   verified 2026-08-02.
7. Apache ZooKeeper Project, "ZooKeeper Recipes and Solutions, Locks",
   https://zookeeper.apache.org/doc/current/recipes.html, verified 2026-08-02.
8. Flavio P. Junqueira and Benjamin Reed, *ZooKeeper. Distributed Process
   Coordination*, O'Reilly Media, 2013, chapter 2, "Getting Started with
   ZooKeeper".

## Code examples

The three implementations below share one shape, an in-memory Lock Manager
backed by a map from resource identifier to a lock record holding the owner
session identifier and an expiry timestamp, with acquire, release, and a
background-callable reap operation. This is deliberately the simplest correct
version of the pattern from dimension 8's first variant, a dedicated lock
table, expressed without a real database so each sample compiles and runs on
its own with no external service.

### TypeScript

```typescript
type LockRecord = { owner: string; expiresAt: number };

class LockManager {
  private locks = new Map<string, LockRecord>();

  constructor(private ttlMs: number) {}

  acquire(resourceId: string, sessionId: string, now: number): boolean {
    this.reap(now);
    const existing = this.locks.get(resourceId);
    if (existing && existing.owner !== sessionId) {
      return false;
    }
    this.locks.set(resourceId, { owner: sessionId, expiresAt: now + this.ttlMs });
    return true;
  }

  release(resourceId: string, sessionId: string): boolean {
    const existing = this.locks.get(resourceId);
    if (!existing || existing.owner !== sessionId) {
      return false;
    }
    this.locks.delete(resourceId);
    return true;
  }

  isLockedBy(resourceId: string, sessionId: string, now: number): boolean {
    this.reap(now);
    const existing = this.locks.get(resourceId);
    return existing !== undefined && existing.owner === sessionId;
  }

  private reap(now: number): void {
    for (const [resourceId, record] of this.locks) {
      if (record.expiresAt <= now) {
        this.locks.delete(resourceId);
      }
    }
  }
}

function main(): void {
  const manager = new LockManager(30 * 60 * 1000);
  const t0 = 1000;

  const grantedToA = manager.acquire("order#42", "sessionA", t0);
  const deniedToB = manager.acquire("order#42", "sessionB", t0 + 1);
  const stillOwnedByA = manager.isLockedBy("order#42", "sessionA", t0 + 2);

  console.log("A acquired:", grantedToA);
  console.log("B denied while A holds it:", deniedToB === false);
  console.log("A still owns it:", stillOwnedByA);

  const released = manager.release("order#42", "sessionA");
  const nowGrantedToB = manager.acquire("order#42", "sessionB", t0 + 3);

  console.log("A released:", released);
  console.log("B can now acquire:", nowGrantedToB);

  const expiredThenGranted = manager.acquire(
    "order#43",
    "sessionC",
    t0
  );
  const stillLockedJustBeforeExpiry = manager.acquire(
    "order#43",
    "sessionD",
    t0 + 30 * 60 * 1000 - 1
  );
  const grantedAfterExpiry = manager.acquire(
    "order#43",
    "sessionD",
    t0 + 30 * 60 * 1000 + 1
  );

  console.log("C acquired order#43:", expiredThenGranted);
  console.log("D denied just before expiry:", stillLockedJustBeforeExpiry === false);
  console.log("D granted after expiry:", grantedAfterExpiry);
}

main();
```

### Python

```python
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class LockRecord:
    owner: str
    expires_at: float


class LockManager:
    def __init__(self, ttl_seconds: float) -> None:
        self._ttl_seconds = ttl_seconds
        self._locks: Dict[str, LockRecord] = {}

    def acquire(self, resource_id: str, session_id: str, now: float) -> bool:
        self._reap(now)
        existing = self._locks.get(resource_id)
        if existing is not None and existing.owner != session_id:
            return False
        self._locks[resource_id] = LockRecord(
            owner=session_id, expires_at=now + self._ttl_seconds
        )
        return True

    def release(self, resource_id: str, session_id: str) -> bool:
        existing = self._locks.get(resource_id)
        if existing is None or existing.owner != session_id:
            return False
        del self._locks[resource_id]
        return True

    def is_locked_by(self, resource_id: str, session_id: str, now: float) -> bool:
        self._reap(now)
        existing: Optional[LockRecord] = self._locks.get(resource_id)
        return existing is not None and existing.owner == session_id

    def _reap(self, now: float) -> None:
        expired = [rid for rid, rec in self._locks.items() if rec.expires_at <= now]
        for rid in expired:
            del self._locks[rid]


def main() -> None:
    manager = LockManager(ttl_seconds=1800)
    t0 = 1000.0

    granted_to_a = manager.acquire("order#42", "sessionA", t0)
    denied_to_b = manager.acquire("order#42", "sessionB", t0 + 1)
    still_owned_by_a = manager.is_locked_by("order#42", "sessionA", t0 + 2)

    print("A acquired:", granted_to_a)
    print("B denied while A holds it:", denied_to_b is False)
    print("A still owns it:", still_owned_by_a)

    released = manager.release("order#42", "sessionA")
    now_granted_to_b = manager.acquire("order#42", "sessionB", t0 + 3)

    print("A released:", released)
    print("B can now acquire:", now_granted_to_b)

    expired_then_granted = manager.acquire("order#43", "sessionC", t0)
    still_locked_just_before_expiry = manager.acquire(
        "order#43", "sessionD", t0 + 1800 - 1
    )
    granted_after_expiry = manager.acquire(
        "order#43", "sessionD", t0 + 1800 + 1
    )

    print("C acquired order#43:", expired_then_granted)
    print("D denied just before expiry:", still_locked_just_before_expiry is False)
    print("D granted after expiry:", granted_after_expiry)


if __name__ == "__main__":
    main()
```

### Go

```go
package main

import "fmt"

type lockRecord struct {
	owner     string
	expiresAt int64
}

type LockManager struct {
	ttl   int64
	locks map[string]lockRecord
}

func NewLockManager(ttlSeconds int64) *LockManager {
	return &LockManager{ttl: ttlSeconds, locks: make(map[string]lockRecord)}
}

func (m *LockManager) reap(now int64) {
	for resourceID, rec := range m.locks {
		if rec.expiresAt <= now {
			delete(m.locks, resourceID)
		}
	}
}

func (m *LockManager) Acquire(resourceID, sessionID string, now int64) bool {
	m.reap(now)
	if existing, ok := m.locks[resourceID]; ok && existing.owner != sessionID {
		return false
	}
	m.locks[resourceID] = lockRecord{owner: sessionID, expiresAt: now + m.ttl}
	return true
}

func (m *LockManager) Release(resourceID, sessionID string) bool {
	existing, ok := m.locks[resourceID]
	if !ok || existing.owner != sessionID {
		return false
	}
	delete(m.locks, resourceID)
	return true
}

func (m *LockManager) IsLockedBy(resourceID, sessionID string, now int64) bool {
	m.reap(now)
	existing, ok := m.locks[resourceID]
	return ok && existing.owner == sessionID
}

func main() {
	manager := NewLockManager(1800)
	var t0 int64 = 1000

	grantedToA := manager.Acquire("order#42", "sessionA", t0)
	deniedToB := manager.Acquire("order#42", "sessionB", t0+1)
	stillOwnedByA := manager.IsLockedBy("order#42", "sessionA", t0+2)

	fmt.Println("A acquired:", grantedToA)
	fmt.Println("B denied while A holds it:", deniedToB == false)
	fmt.Println("A still owns it:", stillOwnedByA)

	released := manager.Release("order#42", "sessionA")
	nowGrantedToB := manager.Acquire("order#42", "sessionB", t0+3)

	fmt.Println("A released:", released)
	fmt.Println("B can now acquire:", nowGrantedToB)

	expiredThenGranted := manager.Acquire("order#43", "sessionC", t0)
	stillLockedJustBeforeExpiry := manager.Acquire("order#43", "sessionD", t0+1800-1)
	grantedAfterExpiry := manager.Acquire("order#43", "sessionD", t0+1800+1)

	fmt.Println("C acquired order#43:", expiredThenGranted)
	fmt.Println("D denied just before expiry:", stillLockedJustBeforeExpiry == false)
	fmt.Println("D granted after expiry:", grantedAfterExpiry)
}
```

Java was not run for this entry. No Java Runtime is currently installed on
this machine, `javac -version` fails with "Unable to locate a Java Runtime",
so a Java sample was not attempted rather than left unverified. Rust and
Kotlin are omitted, the pattern's implementation shape is identical to the
three languages above and adds no idiomatic variant a fourth or fifth
language would meaningfully illustrate.
