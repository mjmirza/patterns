---
name: Read-Write Lock
slug: read-write-lock
family: 09-concurrency
category: Concurrency
aliases: [Reader-Writer Lock, Shared-Exclusive Lock, Multiple Readers Single Writer Lock, RWLock]
first_described: "Courtois, Heymans, Parnas 1971"
maturity: canonical
related: [mutex, monitor-object, double-checked-locking, optimistic-concurrency-control, actor-model]
incompatible_with: []
verified: 2026-08-02
---

# Read-Write Lock

## 1. Name, aliases, and lineage

The canonical name is Read-Write Lock, also written Reader-Writer Lock. The
underlying synchronization primitive predates the object-oriented pattern
catalogs. The original statement of the problem and a correct algorithm for it
appear in P. J. Courtois, F. Heymans, and D. L. Parnas, "Concurrent Control
with 'Readers' and 'Writers'", Communications of the ACM, Volume 14, Issue 10,
October 1971, pages 667 to 668. The paper is indexed at the ACM Digital
Library under DOI 10.1145/362759.362813; the digital library page returned an
HTTP 403 on direct fetch during verification, so the citation rests on the
paper's standard bibliographic record rather than a live-fetched abstract, and
that limit is stated here rather than hidden.

Courtois, Heymans, and Parnas posed the problem as two classes of processes
sharing one piece of data. readers, which only inspect it, and writers, which
update it. Their algorithm allows any number of readers to proceed
concurrently but requires a writer to have exclusive access, with no reader
and no other writer active at the same time. The paper also introduced the
now-standard vocabulary of the "readers-preference" and "writers-preference"
solutions, and showed that a naive readers-preference algorithm can starve
writers indefinitely under continuous read load, a result every production
implementation covered in this entry still has to answer for.

Alternative names in circulation. **Shared-Exclusive Lock** is the term used
in database internals literature, where the two lock modes are called shared
and exclusive rather than read and write, because a lock manager applies the
identical algorithm to row, page, and table-level access, not only to an
in-memory data structure. **Multiple Readers Single Writer Lock** appears in
older operating systems texts and spells out the invariant directly. **RWLock**
is the common abbreviated identifier used across POSIX threads
(`pthread_rwlock_t`), the Linux kernel (`rwlock_t`, `rw_semaphore`), and most
language standard libraries, and is used interchangeably with Read-Write Lock
throughout the rest of this entry.

The pattern is not attributed to the Gang of Four, and it does not appear in
*Design Patterns. Elements of Reusable Object-Oriented Software*. It is treated
as canonical here for the same reason Mutex and Monitor Object are, because it
is a load-bearing, independently named, universally implemented concurrency
primitive with a fixed and well understood shape, not because it traces to the
1994 catalog.

## 2. Problem and context

A single piece of shared, mutable state is accessed by multiple threads. Some
of those accesses only read the state. Some mutate it. A plain mutex forces
every access, read or write, through the same one-thread-at-a-time gate, which
is unnecessary and expensive when reads vastly outnumber writes and reads do
not conflict with each other, only with a concurrent write.

The concrete situation that creates the need looks like this in a codebase.
There is an in-memory cache, a configuration object, a routing table, a
connection pool's metadata, or an index structure. It is read on every request
that flows through the system, hundreds or thousands of times a second, and it
is written rarely, on a cache refresh, a config reload, or a topology change
that happens once every few seconds or minutes at most. Under a plain mutex,
every one of those frequent reads serializes against every other read, even
though two reads of an unchanging structure can never observe an inconsistent
result from each other. The system spends its concurrency budget forcing
non-conflicting operations to wait in line.

The context that makes a read-write lock the right answer has three parts, and
all three have to hold or the pattern is the wrong tool.

- Reads vastly outnumber writes, so the cost of coordinating readers against
  each other, which a plain mutex does for free by accident, is worth paying to
  remove.
- Reads take long enough, or happen at high enough concurrency, that
  serializing them against each other under a plain mutex is a measurable
  bottleneck. If a read is a single pointer dereference that takes nanoseconds,
  the coordination overhead of a read-write lock can exceed the serialization
  cost it was meant to avoid, a point covered in dimension 11.
- The data structure being protected can be read concurrently without
  corruption as long as no write is interleaved, meaning the protected
  operation genuinely partitions into a read-only class and a mutating class.
  A structure where "reading" involves incidental mutation, such as a
  self-balancing tree that rotates nodes during lookup or a cache that updates
  an LRU counter on read, does not fit this shape without further work,
  covered in dimension 4.

## 3. Forces

This is engineering judgement, weighing which pressure dominates in the shapes
of workload this pattern targets.

- **Throughput versus fairness.** The read-write lock exists to raise read
  throughput above what a mutex allows. The Java documentation for
  `ReentrantReadWriteLock` states plainly that its default, non-fair mode "will
  normally have higher throughput than a fair lock" ([Oracle, `ReentrantReadWriteLock` class documentation, JDK 21](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/locks/ReentrantReadWriteLock.html), verified 2026-08-02). Every implementation surveyed in this entry has to pick a point
  on this trade, and the choice is rarely free once made, because switching a
  production lock's fairness policy later changes its latency distribution
  under load in ways that are hard to predict without re-benchmarking.
- **Reader count versus writer starvation.** The more readers are allowed to
  interleave with each other, the longer a waiting writer can be made to wait,
  because a continuous stream of overlapping reads can, in the least fair
  implementations, keep the lock in read mode indefinitely. This is not a
  hypothetical. Rust's standard library documentation for `RwLock` states
  outright that "the priority policy of the lock is dependent on the
  underlying operating system's implementation, and this type does not
  guarantee that any particular policy will be used. In particular, a writer
  which is waiting to acquire the lock in write might or might not block
  concurrent calls to read" ([Rust standard library, `std::sync::RwLock`](https://doc.rust-lang.org/std/sync/struct.RwLock.html), verified 2026-08-02).
- **Coordination overhead versus contention avoidance.** A read-write lock
  needs an atomically updated reader count, and often a separate wait queue for
  writers, which is strictly more bookkeeping than a mutex's single bit of
  state. Under low contention that bookkeeping is pure overhead. Under high
  read contention it is the entire value proposition. The pattern favours
  systems that sit clearly on the high-read-contention side of that line.
- **Reentrancy versus deadlock avoidance.** Allowing a thread to acquire the
  same lock again while already holding it, in the same or a compatible mode,
  simplifies call graphs where a public API method that takes a read lock calls
  a private helper that also wants one. It also complicates the implementation
  and, if handled incorrectly, opens exactly the kind of deadlock the lock
  exists to prevent, discussed under dimension 11.
- **Simplicity of the mental model versus richness of the mode set.** A plain
  two-mode lock, read and write, is easy to reason about. Adding a third
  "upgradeable" mode, as .NET's `ReaderWriterLockSlim` does, buys a genuinely
  useful capability, letting a thread that starts in read mode transition to
  write mode without releasing and reacquiring, at the cost of a third state
  every caller now has to understand and a limit that only one thread may hold
  the upgradeable mode at a time.

## 4. Applicability and non-applicability

Reach for a read-write lock when all of these hold at once.

- The protected resource is read far more often than it is written, commonly
  cited as a ratio in the range of ten to one or higher in practice, though no
  fixed threshold is universal and the only reliable test is a benchmark of
  the actual workload.
- Concurrent reads of the resource, absent any interleaved write, can never
  produce an inconsistent or corrupted result, because the read path performs
  no mutation of the structure itself.
- The critical section, for either a read or a write, is long enough, or
  contended by enough concurrent threads, that avoiding serialization of reads
  against each other yields a measurable throughput gain.
- The resource is genuinely shared across independently scheduled threads or
  processes, so a language or runtime that has no true parallelism for the
  operations in question gets no benefit from the pattern.

Do NOT reach for a read-write lock when any of these hold.

- **Writes are frequent, or reads and writes are roughly balanced.** A
  read-write lock's bookkeeping overhead, the atomic reader count, the wait
  queue, the mode transition logic, is pure cost when there is no long run of
  concurrent reads to amortise it against. A plain mutex is simpler, has lower
  fixed overhead, and often performs as well or better in this regime.
- **The read operation itself is very cheap, on the order of a few
  instructions, and lock acquisition cost dominates the operation's cost.**
  Acquiring even an uncontended read-write lock typically costs more than
  acquiring an uncontended plain mutex, because it has to touch more shared
  state atomically. For very cheap, very hot reads, this overhead can erase the
  entire benefit, and a plain mutex, an immutable snapshot swap, or a
  lock-free structure is often faster in practice.
- **The runtime already provides a cheaper alternative for the exact
  read-mostly shape.** PostgreSQL's own documentation states that under its
  multiversion concurrency control model "locks acquired for querying
  (reading) data do not conflict with locks acquired for writing data, and so
  reading never blocks writing and writing never blocks reading" ([PostgreSQL 18 Documentation, Chapter 13, "Concurrency Control", section 13.2.1](https://www.postgresql.org/docs/current/mvcc-intro.html), verified 2026-08-02). Where a snapshot-based or copy-on-write scheme is available and fits the
  workload, it removes the reader-versus-writer coordination problem entirely
  rather than optimising it, and is frequently the better choice, covered
  further in dimension 12.
- **A single thread already owns the resource, or the language's execution
  model rules out true concurrent reads on it**, for example a plain
  JavaScript object accessed only from the Node.js event loop's single thread,
  where no lock of any kind is needed because there is no interleaving to
  guard against. The async read-write lock shown in dimension 8 exists for a
  different reason, ordering concurrent asynchronous operations, not for
  protecting against true parallel memory access.
- **The read path performs incidental mutation**, such as updating an access
  timestamp, promoting a cache entry, or rebalancing a structure during
  lookup. Such a "read" is a write in disguise and needs the exclusive lock, or
  a design change, such as moving the incidental update to a separate,
  independently synchronized counter, or accepting an approximate value for
  it, to keep the read path genuinely read-only.
- **The lock would be held across an I/O call or another unbounded blocking
  operation.** Holding a read-write lock, in either mode, across a network
  call or a disk read turns a data-structure lock into a de facto rate limiter
  on an entire unrelated subsystem, and a writer that is starved behind a slow
  reader compounds the problem badly, because it is now waiting on I/O it does
  not directly depend on.

## 5. Structure

- **Lock.** The shared coordination object. It tracks the current mode, free,
  shared by N readers, or held exclusively by one writer, the count of active
  readers, and, in fair or ordered implementations, a queue of waiting threads
  recording whether each is waiting to read or to write.
- **Read Lock, Shared Lock, handle.** The acquisition and release interface a
  reader uses. Acquiring it blocks while a writer holds or is waiting for the
  lock, under a writer-preferring or fair policy, and otherwise succeeds
  immediately alongside any other active readers. Releasing it decrements the
  active reader count and, if that count reaches zero, allows a waiting writer
  to proceed.
- **Write Lock, Exclusive Lock, handle.** The acquisition and release interface
  a writer uses. Acquiring it blocks until there are no active readers and no
  other active writer. Releasing it allows the lock to be granted to the next
  waiter, whether that is a batch of readers or a single writer, according to
  the lock's fairness policy.
- **Reader.** Any thread that only needs to observe the protected resource. It
  acquires the read lock, performs its read-only work, and releases the read
  lock. It never mutates the protected resource while holding only the read
  lock.
- **Writer.** Any thread that needs to mutate the protected resource. It
  acquires the write lock, performs the mutation, and releases the write lock.
  Exactly one writer, and no readers, may hold the lock at a time.
- **Upgradeable Reader, optional participant.** Present in richer
  implementations such as .NET's `ReaderWriterLockSlim`. A thread that enters
  this mode holds read access and may later transition to write mode without
  fully releasing and reacquiring, but at most one thread may be in this mode
  at a time, which is what makes the upgrade path deadlock-free.
- **Protected Resource.** The shared, mutable state the lock guards. It is
  conceptually external to the lock. the lock coordinates access, it does not
  contain or manage the data itself.

## 6. ASCII structure diagram

```
+-------------------------------------------------------------+
|                        ReadWriteLock                        |
|---------------------------------------------------------------|
| state: FREE | SHARED(n readers) | EXCLUSIVE(1 writer)         |
| waitQueue: [ (kind, waiterHandle), ... ]                      |
|---------------------------------------------------------------|
| + acquireRead()  / releaseRead()                              |
| + acquireWrite() / releaseWrite()                              |
+-------------------------------------------------------------+
        ^ blocks while EXCLUSIVE          ^ blocks while
        | or writer waiting (fair mode)   | SHARED(n>0) or
        |                                 | EXCLUSIVE
+---------------+                 +----------------+
|    Reader     |                 |     Writer     |
|---------------|                 |----------------|
| acquireRead()  |                 | acquireWrite()  |
| read(resource) |                 | write(resource) |
| releaseRead()  |                 | releaseWrite()  |
+---------------+                 +----------------+
        \                                 /
         \                               /
          v                             v
        +-----------------------------------+
        |          Protected Resource        |
        |  (cache, config, routing table...) |
        +-----------------------------------+

Optional: Upgradeable Reader
+-----------------------+
|   UpgradeableReader    |
|------------------------|
| acquireUpgradeable()    |
| read(resource)          |
| [condition] upgrade()   |----> becomes exclusive writer
| downgrade() / release() |
+-----------------------+
(at most one Upgradeable Reader may be active at any time)
```

## 7. Dynamics

The three interaction sequences below cover the cases that matter in
practice. concurrent readers, a writer arriving among active readers, and a
reader arriving while a writer waits, which is where fairness policy shows
up directly in behaviour.

```
Sequence: two readers overlap freely
--------------------------------------
Reader A          Lock                Reader B
   |-- acquireRead() -->|                  |
   |<-- granted (n=1) --|                  |
   |                    |<-- acquireRead() -|
   |                    |-- granted (n=2) ->|
   |  ... reading ...   |   ... reading ... |
   |-- releaseRead() -->|                  |
   |<-- ack (n=1) ------|                  |
   |                    |<-- releaseRead() -|
   |                    |-- ack (n=0) ----->|

Sequence: writer arrives while readers are active (writer-preferring policy)
------------------------------------------------------------------------------
Reader A          Lock                Writer W          Reader C
   |-- acquireRead -->|                    |                 |
   |<-- granted(n=1)--|                    |                 |
   |                  |<-- acquireWrite ---|                 |
   |                  |   (queued, blocks) |                 |
   |                  |                    |   (arrives)     |
   |                  |<---------------------- acquireRead --|
   |                  |   blocked: writer is waiting          |
   |  ... reading ... |                                       |
   |-- releaseRead -->|                                       |
   |<-- ack(n=0) ------|                                       |
   |                  |-- grant write ---->|                 |
   |                  |                    |  ... writing ... |
   |                  |<-- releaseWrite ---|                 |
   |                  |-- grant read ------------------------->|
   |                  |                                  ... reading ...

Sequence: upgrade path (upgradeable-mode implementations only)
----------------------------------------------------------------
Reader U (upgradeable)          Lock
   |-- acquireUpgradeable() -->|
   |<-- granted (read access) -|
   |  ... read, decide mutation is needed ...
   |-- enterWriteLock() ------>|
   |   (blocks until other active readers drain;
   |    no new readers admitted while an upgrade is pending)
   |<-- granted (write access)-|
   |  ... mutate resource ...  |
   |-- exitWriteLock() ------->|
   |<-- back to upgradeable ---|
   |-- exitUpgradeableReadLock()->|
   |<-- fully released --------|
```

## 8. Implementation variants

- **POSIX threads, `pthread_rwlock_t`, C, and any language binding to it.**
  The operating-system-level baseline. Attributes control the sharing scope
  between processes and, on glibc, a preference flag that can be set to favour
  writers, because the historical glibc default favoured readers strongly
  enough to starve writers under sustained read load, a well known operational
  trap on Linux systems built directly on this primitive.
- **JVM, `java.util.concurrent.locks.ReentrantReadWriteLock`, Java, Kotlin,
  Scala, and other JVM languages.** A class-based, explicit-lock
  implementation with two constructor-selected fairness modes and, distinctly,
  reentrancy plus a defined downgrade path. The JDK documentation states that
  "reentrancy also allows downgrading from the write lock to a read lock, by
  acquiring the write lock, then the read lock and then releasing the write
  lock. However, upgrading from a read lock to the write lock is not
  possible" ([Oracle, `ReentrantReadWriteLock` class documentation, JDK 21](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/locks/ReentrantReadWriteLock.html), verified 2026-08-02). This asymmetry, downgrade allowed, upgrade forbidden, is a
  deliberate deadlock-avoidance decision repeated in most implementations that
  do not offer a distinct upgradeable mode.
- **Go, `sync.RWMutex`.** A struct type with `RLock`/`RUnlock` and
  `Lock`/`Unlock` method pairs, embedded by value inside the type it protects
  by convention rather than wrapped around it, matching Go's general
  preference for composition over an explicit lock-handle object. It carries
  no reentrancy support at all. calling `Lock` twice from the same goroutine
  deadlocks, and this is treated as correct behaviour by the standard library
  rather than a defect.
- **Rust, `std::sync::RwLock<T>`.** Type-parameterized over the guarded data
  itself rather than wrapping an opaque resource, so the compiler enforces
  that the data can only be touched through a `RwLockReadGuard` or
  `RwLockWriteGuard`, making an unguarded access a compile error rather than a
  runtime bug. Rust's documentation is explicit that the lock "may only be
  poisoned if a panic occurs while it is locked exclusively (write mode). If a
  panic occurs in any reader, then the lock will not be poisoned" ([Rust standard library, `std::sync::RwLock`](https://doc.rust-lang.org/std/sync/struct.RwLock.html), verified 2026-08-02), an asymmetric poisoning policy that follows directly from the asymmetry
  of what a torn write versus a torn read can do to the data.
- **.NET, `ReaderWriterLockSlim`.** Adds a distinct upgradeable-read mode on
  top of the plain read and write modes, so a thread can hold read access and
  later become the writer without releasing its read hold to a competing
  writer in between. Microsoft's own documentation calls out the risk this
  mode is built to avoid, warning that "if two threads in read mode both try
  to enter write mode, they will deadlock. Upgradeable mode is designed to
  avoid such deadlocks" ([Microsoft Learn, `ReaderWriterLockSlim` class, .NET API reference](https://learn.microsoft.com/en-us/dotnet/api/system.threading.readerwriterlockslim), verified 2026-08-02), by allowing only one thread into upgradeable mode at a time. It also
  defaults to a non-recursive policy, and the documentation states this
  default "is recommended for all new development, because recursion
  introduces unnecessary complications and makes your code more prone to
  deadlocks" (same source, verified 2026-08-02).
- **Linux kernel, `rwlock_t` and `rw_semaphore`.** Two distinct in-kernel
  primitives at different layers, a spinning variant for short, non-sleeping
  critical sections and a sleeping-capable semaphore variant for longer ones.
  The kernel's own locking documentation notes that on realtime-preemption
  kernels the two are remapped onto a shared RT-mutex-based implementation and
  their fairness characteristics change, in particular that "a preempted
  low-priority reader will continue holding its lock, thus starving even
  high-priority writers" under that configuration ([The Linux Kernel documentation, "Lock types and their rules", locking/locktypes.rst](https://www.kernel.org/doc/html/latest/locking/locktypes.html), verified 2026-08-02), which is one of the clearest documented cases of a read-write lock's
  fairness policy shifting under a different runtime configuration of the same
  primitive.
- **Async, single-threaded event loops, JavaScript and TypeScript on Node.js,
  Python's `asyncio`.** There is no true parallel memory access to protect,
  so the pattern is reimplemented purely as an ordering discipline over
  `await` points, a queue of pending readers and writers gated so that a
  granted writer excludes all readers and other writers until it resolves, and
  granted readers run concurrently with each other but never alongside a
  writer. This variant protects invariants across `await` boundaries, such as
  "no reader observes a value mid-update while another async task is awaiting
  inside the writer", not against genuine hardware-level races. The
  TypeScript implementation in dimension 9 below is exactly this shape.

## 9. Known production uses

- **The Java Virtual Machine standard library**, `ReentrantReadWriteLock`,
  documented as part of `java.util.concurrent.locks` since J2SE 5.0 and still
  current in JDK 21. It is the standard building block for read-mostly caches
  and configuration holders across the JVM ecosystem, and its own
  documentation frames its purpose directly around "resources that are
  accessed frequently but modified less frequently" ([Oracle, `ReentrantReadWriteLock` class documentation, JDK 21](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/locks/ReentrantReadWriteLock.html), verified 2026-08-02).
- **The Linux kernel**, which uses `rwlock_t` and `rw_semaphore` as core
  synchronization primitives throughout subsystems that maintain long-lived,
  frequently read, rarely modified structures, for example routing and
  filesystem metadata tables, and documents both types and their fairness
  behaviour, including the realtime-kernel remapping, in its own kernel
  documentation tree ([The Linux Kernel documentation, "Lock types and their rules"](https://www.kernel.org/doc/html/latest/locking/locktypes.html), verified 2026-08-02).
- **The Rust standard library**, `std::sync::RwLock<T>`, shipped as a core
  concurrency primitive since Rust 1.0 and used across the ecosystem wherever
  a shared, read-mostly, thread-safe structure is needed and the async runtime
  is not already handling the coordination, with the library's own
  documentation stating its exact semantics and the platform-dependent writer
  fairness caveat in the same page ([Rust standard library, `std::sync::RwLock`](https://doc.rust-lang.org/std/sync/struct.RwLock.html), verified 2026-08-02).
- **.NET**, `ReaderWriterLockSlim`, part of `System.Threading` since .NET
  Framework 3.5 and recommended by Microsoft over the older, more
  deadlock-prone `ReaderWriterLock`. the current documentation states plainly
  that `ReaderWriterLockSlim` "is recommended for all new development" and
  cites both simplified recursion rules and materially better performance as
  the reasons ([Microsoft Learn, `ReaderWriterLockSlim` class, .NET API reference](https://learn.microsoft.com/en-us/dotnet/api/system.threading.readerwriterlockslim), verified 2026-08-02).

## 10. Consequences

Positive.

- Concurrent, non-conflicting reads proceed in parallel instead of serializing
  behind each other, which is the entire reason to reach for the pattern over
  a plain mutex in a read-heavy workload.
- The invariant enforced, at most one writer and never a reader alongside a
  writer, is simple to state and simple to verify by inspection of the lock
  usage at each call site, unlike more elaborate lock-free schemes.
- Several mature implementations, notably `ReentrantReadWriteLock` and
  `ReaderWriterLockSlim`, provide a safe downgrade path from write to read,
  letting a writer verify or immediately reuse the state it just wrote without
  releasing the lock and racing a second writer for it.
- The pattern composes cleanly with existing single-writer mental models.
  code that was already correct under a plain mutex, where only one thread
  touches the resource at a time, is usually correct under a read-write lock
  once reads are distinguished from writes, because the write-mode invariant
  is identical to the mutex's invariant.

Negative.

- Writer starvation is a live risk, not a theoretical one, under
  reader-preferring or unfair policies, and the severity depends entirely on
  the runtime's chosen policy, which several standard libraries explicitly
  decline to guarantee. Rust's documentation states outright that its policy
  "is dependent on the underlying operating system's implementation" with no
  guarantee attached ([Rust standard library, `std::sync::RwLock`](https://doc.rust-lang.org/std/sync/struct.RwLock.html), verified 2026-08-02).
- Acquiring and releasing a read-write lock costs strictly more than a plain
  mutex in the uncontended case, because the implementation has to maintain a
  reader count atomically rather than a single bit of ownership state. For a
  workload with a very cheap read body, this overhead can consume the entire
  benefit the pattern was meant to provide.
- The mode set grows the API surface a caller has to reason about correctly.
  every call site must classify itself as read-only or mutating, and a
  misclassification, treating a mutating operation as a read, is a silent
  data race that a type system without enforcement, such as Java's or Go's,
  will not catch, unlike Rust's borrow-checked `RwLockReadGuard`.
- Upgrade paths, where offered, add a distinct failure mode. a naive
  implementation that lets any reader attempt to become a writer produces a
  classic two-thread deadlock when two readers each wait for the other to
  release before upgrading, which is exactly why mature implementations
  either forbid the upgrade entirely or restrict it to a single, dedicated
  upgradeable mode.

## 11. Failure modes and misuse

**Reader-to-writer upgrade deadlock.** Symptom. Two or more threads, each
holding a plain read lock, each attempt to acquire the write lock, and the
process hangs permanently with no CPU usage on the affected threads. Cause. A
plain read lock grants no priority or exclusivity over other readers, so each
thread's write-lock acquisition waits for every other reader, including the
other thread also trying to upgrade, to release first, and none of them ever
will. Fix. Never attempt to acquire the write lock while holding only a plain
read lock. Release the read lock first and reacquire the write lock, accepting
that the state may have changed in between and re-validating it, or use an
implementation's dedicated upgradeable mode, which restricts at most one
thread to that mode specifically to make the upgrade deadlock-free, as .NET's
documentation states directly. "if two threads in read mode both try to enter
write mode, they will deadlock. Upgradeable mode is designed to avoid such
deadlocks" ([Microsoft Learn, `ReaderWriterLockSlim` class, .NET API reference](https://learn.microsoft.com/en-us/dotnet/api/system.threading.readerwriterlockslim), verified 2026-08-02).

**Writer starvation under sustained read load.** Symptom. A writer's
acquisition call blocks for an unexpectedly long, sometimes unbounded,
duration, and profiling shows a continuous stream of overlapping reader
acquisitions with no gap in which the writer is granted the lock. Cause. An
implementation or configuration that favours readers, or, per Rust's explicit
warning, an implementation with no defined fairness policy at all, letting
the operating system scheduler determine outcomes that happen to favour
readers under the observed load pattern. Fix. Switch to a writer-preferring or
fair-ordered implementation or constructor option where one is offered, such
as Java's fair-mode constructor flag, and, where no such option exists,
reduce read-critical-section duration so the window in which a new reader can
sneak in ahead of a waiting writer shrinks.

**Torn or inconsistent reads from a read path that silently mutates.**
Symptom. Intermittent corruption or an assertion failure observed only under
concurrent read load, never under a single-threaded reproduction. Cause. The
read operation performs an incidental write, such as updating an
access-order counter for an LRU policy or rebalancing a tree during lookup,
while other threads hold only the shared read lock and assume no mutation is
occurring. Fix. Separate the truly read-only operation from the
incidental-mutation operation. Either promote the mutating step to hold the
write lock, accepting the serialization cost, or move the incidental state,
such as an access counter, out from under the read-write lock entirely and
synchronize it independently, commonly with a lock-free counter that
tolerates approximate values.

**Held-lock deadlock across an unrelated resource.** Symptom. A full
application hang under load that clears the instant a slow downstream
dependency, such as a database or a remote service, becomes responsive
again, with thread dumps showing many threads blocked waiting for the same
read-write lock. Cause. A writer, or in some designs even a reader, performs
a blocking I/O call while holding the lock, so every other reader and the
next writer queue behind that one slow operation, and if the I/O call itself
depends, directly or transitively, on completing that same critical
section elsewhere in the system, the result is a full deadlock rather than
a temporary stall. Fix. Never perform network or disk I/O, or acquire a
second lock that could itself be held by code waiting on this one, while
holding either mode of a read-write lock. Copy the data needed for the I/O
call out of the critical section first, release the lock, then perform the
call.

**Non-reentrant acquisition on the same thread.** Symptom. An immediate,
reproducible deadlock or, in Go's case, a panic, the first time a code path
that already holds the lock calls into another function that also acquires
it. Cause. Assuming reentrancy is universal across read-write lock
implementations when it is not. Go's `sync.RWMutex` supports no reentrancy
at all, and a second `Lock` call from the same goroutine that already holds
the lock deadlocks by design, which the standard library documents as
expected behaviour rather than a bug to fix. Fix. Know the specific
implementation's reentrancy policy before writing call graphs that assume
it, and where reentrancy is not supported, restructure the code so the lock
is acquired exactly once per logical operation, with helper functions taking
the already-guarded data as a parameter rather than reacquiring the lock
themselves.

## 12. Trade-off matrix

| Force | Read-Write Lock | Plain Mutex | MVCC / Snapshot Isolation | Lock-Free (atomic CAS structure) | Actor Model (single-owner message passing) |
|---|---|---|---|---|---|
| Read throughput under high concurrency | High, concurrent readers do not block each other | Low, every read serializes | Very high, readers never block on writers at all | Very high, no blocking of any kind | Bounded by the single actor's message-processing rate, not parallel |
| Write throughput | Moderate, a writer must wait out all active readers | Moderate, same cost as any other operation | Moderate to high, depends on conflict detection and rollback cost | High for simple updates, degrades under contention retries | High per-actor, but globally serialized through the actor's mailbox |
| Implementation complexity | Moderate, well understood primitive with library support in nearly every language | Low, simplest possible primitive | High, requires versioning, garbage collection of old versions, and conflict resolution | High, correctness of lock-free algorithms is notoriously easy to get subtly wrong | Low to moderate, complexity moves into message design and actor supervision |
| Writer starvation risk | Real, and policy-dependent as shown in dimension 11 | Not applicable, no reader class exists to starve a writer | Not applicable, readers and writers never contend | Not applicable in the traditional sense, but retry storms can starve slow writers under heavy CAS contention | Not applicable, a single actor processes its mailbox in order |
| Fits incidental-mutation read paths (LRU, rebalancing trees) | Poorly, without separating the mutation out, per dimension 4 | Yes, trivially, since every access is already exclusive | Yes, naturally, since each transaction sees its own consistent view | Depends heavily on the specific lock-free structure chosen | Yes, naturally, since the actor serializes all access anyway |
| Best fit | Read-heavy, rarely-written shared state with a genuinely read-only read path | Balanced or write-heavy access, or very short critical sections | Multi-version data stores and databases where isolation semantics matter more than raw primitive simplicity | Extremely hot, simple counters or single-word state where every nanosecond of contention matters | Systems where correctness through isolation is worth more than raw shared-memory throughput |

## 13. Related and incompatible patterns

- **Mutex.** The read-write lock is a generalisation of the mutex for the
  specific case where operations partition cleanly into non-conflicting reads
  and conflicting writes. Every read-write lock's write mode behaves exactly
  like a mutex, and a read-write lock degrades to a plain mutex in
  correctness, though not in overhead, if every access is treated as a write.
- **Monitor Object.** A monitor typically wraps a single implicit lock around
  an entire object, giving every method, read or write, the same exclusive
  access. A read-write lock is frequently introduced as a refinement inside a
  monitor-style object once profiling shows that its read methods dominate
  call volume and do not need to exclude each other.
- **Double-Checked Locking.** Both patterns exist to avoid unnecessary
  synchronization cost on a hot read path, but they solve different shapes of
  problem. double-checked locking optimises the one-time lazy initialization
  of a value that is read far more often than it is ever written to, in the
  degenerate case exactly once, whereas a read-write lock optimises repeated
  concurrent reads of state that continues to be written to throughout the
  program's life. A lazily-initialized, never-again-mutated value is usually
  better served by double-checked locking or an atomic reference swap than by
  a read-write lock.
- **Optimistic Concurrency Control.** Where a read-write lock coordinates
  pessimistically, blocking a writer until readers finish, optimistic schemes
  let readers proceed without blocking at all and instead detect, after the
  fact, whether a conflicting write occurred during the read, retrying if so.
  The two patterns are direct alternatives for the same problem shape, and the
  choice between them usually comes down to how expensive a retry is versus
  how expensive blocking is for the specific workload.
- **Actor Model.** Actively incompatible as a co-located strategy for the
  same piece of state. once a resource's access is modeled as message passing
  through a single actor's mailbox, introducing a read-write lock around that
  same resource is redundant at best and a source of confusing dual-ownership
  bugs at worst. A team migrating a read-write-lock-protected structure into
  an actor should remove the lock entirely rather than layer the two.
- **MVCC / Snapshot Isolation.** Not incompatible in the sense of causing
  bugs if combined carelessly, but conceptually competing solutions to the
  same reader-versus-writer contention problem, covered in the trade-off
  matrix above. A system already built on MVCC, such as an application backed
  entirely by PostgreSQL for its shared state, has little reason to also
  introduce in-process read-write locks around the same data.

## 14. Refactoring path in and out

Introducing a read-write lock into code that currently uses a plain mutex,
step by step.

1. Profile first. Confirm, with real measurements under realistic
   concurrency, that lock contention on the mutex is a genuine bottleneck and
   that the workload is read-dominated. Introducing this pattern without that
   evidence is a common source of the negative consequences in dimension 10
   with none of the positive ones.
2. Audit every existing call site that acquires the mutex and classify each
   one as read-only or mutating. Pay particular attention to methods that look
   read-only on the surface but perform an incidental write, per the failure
   mode in dimension 11.
3. Replace the single mutex field with a read-write lock instance. In
   languages without compiler enforcement of guard usage, add a code
   convention or a lint rule requiring every acquisition to state its mode
   explicitly at the call site, rather than through an ambiguous shared
   helper.
4. Convert each read-only call site to acquire the read lock, and each
   mutating call site to acquire the write lock, one call site at a time,
   running the test suite after each change rather than converting the whole
   surface at once.
5. Re-benchmark under the same realistic concurrency used in step 1 and
   confirm the expected throughput improvement actually materialises. If it
   does not, revert. an unproven read-write lock is strictly worse than the
   mutex it replaced.
6. Add contention and wait-time monitoring, per dimension 16, before
   declaring the migration complete, so a future regression, such as writer
   starvation appearing under a load pattern not exercised in the benchmark,
   is caught in production rather than discovered as an outage.

Removing a read-write lock once it stops earning its place, step by step.

1. Confirm the removal reason. common triggers are a workload shift toward
   more frequent writes, a redesign onto MVCC or an actor model that already
   handles the coordination, or evidence from dimension 16's monitoring that
   contention has dropped low enough that the added complexity is no longer
   justified.
2. If migrating to a plain mutex, this is close to mechanical. replace every
   read-lock and write-lock acquisition with the single mutex's acquisition,
   since the write mode's invariant already matches a mutex exactly.
3. If migrating to MVCC, an actor, or a lock-free structure, this is not
   mechanical, and each call site needs to be redesigned around the new
   coordination model's actual API, not merely mapped one-to-one from the old
   lock calls.
4. Remove the now-unused upgradeable-mode logic, if any was present, since it
   is one of the more subtle pieces of code in the original implementation
   and is easy to leave behind as dead, confusing scaffolding.
5. Re-run the same benchmark used to justify the original introduction, to
   confirm the removal is also improving, or at minimum not regressing, the
   metric that mattered, rather than assuming the new approach is better
   purely on architectural grounds.

## 15. Testing and verification

This dimension is largely engineering judgement about practice, not a set of
sourced claims.

What becomes easier to test because of this pattern. the write path's
correctness can be verified in near-isolation, using a single writer thread
and asserting the resulting state, because the write mode's exclusivity
guarantee means no other thread can be mutating the resource concurrently
during that assertion.

What becomes harder to test. the interesting bugs in a read-write lock's usage
are almost entirely concurrency bugs, which by nature do not reproduce
reliably in a single-threaded or lightly-loaded test run. A test suite that
never runs more concurrent readers than the machine has cores, or never
interleaves a writer's arrival mid-stream of readers, will not exercise the
starvation and upgrade-deadlock failure modes in dimension 11 at all.

Techniques that apply.

- **Stress tests with an intentionally high reader-to-writer ratio and an
  intentionally long-running writer**, to force the starvation scenario to
  manifest within a bounded test timeout rather than only under
  production-scale load.
- **A watchdog timeout around every lock acquisition in the test runner
  itself**, so a genuine deadlock, such as the reader-to-writer upgrade
  deadlock in dimension 11, fails the test suite loudly with a clear timeout
  message rather than hanging the test runner indefinitely.
- **Race detectors where the language provides one**, such as Go's `-race`
  flag or Rust's reliance on the borrow checker plus tools like Miri for
  unsafe code, run against the code that uses the lock, to catch a
  misclassified read-only call site that actually mutates shared state
  without holding the write lock.
- **Property-based or model-based tests asserting the core invariant
  directly**, generating random interleavings of read and write acquisitions
  against a mock or instrumented lock and asserting that at no point in the
  generated history are a write-mode hold and any other hold, of either mode,
  simultaneously active.
- **Fault injection on the protected resource's write path**, deliberately
  throwing or panicking mid-write in a controlled test, to verify the lock's
  documented failure behaviour, for example that Rust's `RwLock` becomes
  poisoned "if a panic occurs while it is locked exclusively" ([Rust standard library, `std::sync::RwLock`](https://doc.rust-lang.org/std/sync/struct.RwLock.html), verified 2026-08-02), and that the rest of the system reacts to that poisoned state the way the
  design intends rather than assuming it cannot happen.

## 16. Observability signals

This dimension is largely engineering judgement about what practitioners
watch in production, not a set of independently sourced facts.

What to measure on a healthy instance.

- **Read lock hold duration**, as a distribution, not just an average. a
  healthy read-heavy system shows a tight, low-latency distribution for read
  acquisitions, with the vast majority resolving effectively immediately.
- **Write lock wait time**, tracked separately from write lock hold time.
  wait time is the signal that shows whether writers are being kept waiting by
  reader load, and hold time shows whether the write operation itself is slow.
- **Concurrent active reader count**, sampled periodically. a value that
  regularly approaches or matches the thread pool size under normal load is
  a sign the pattern is doing its job. a value that never rises above one or
  two even under load is a sign the pattern may not be earning its overhead.
- **Lock acquisition failure or timeout count**, for implementations that
  support timed acquisition attempts. a rising rate here, especially isolated
  to write-lock timeouts, is an early warning sign for the starvation failure
  mode in dimension 11, well before it becomes a full outage.

What a failing instance looks like.

- A write lock wait-time distribution with a long, heavy tail, or one that
  grows unboundedly over the life of a long-running process, points directly
  at writer starvation.
- A cluster of threads all blocked on the same write lock acquisition call,
  visible in a thread dump, combined with zero forward progress and zero CPU
  usage on those threads, points at the reader-to-writer upgrade deadlock.
- A read lock hold-time distribution with occasional extreme outliers
  correlated with downstream network or disk latency spikes points at the
  held-lock-across-I/O failure mode, and those outliers are exactly the
  moments other readers and any waiting writer are also stalled.
- Where the runtime exposes it, such as via .NET's `WaitingWriteCount` and
  `WaitingReadCount` properties on `ReaderWriterLockSlim`, a persistently
  non-zero waiting-writer count alongside a persistently non-zero active-reader
  count is a direct, structural signal of contention worth alerting on, not
  only inferring from latency.

## 17. Security and privacy implications

Where this pattern is silent, it is stated plainly rather than inventing a
concern that is not there. a read-write lock, by itself, has no cryptographic,
authentication, or data-classification behaviour, and does not alter what
data an attacker with code-execution capability inside the process could
already reach.

The implication that does apply is availability, not confidentiality or
integrity. because a write lock acquisition can be made to wait, sometimes
indefinitely under the starvation failure mode in dimension 11, a resource
protected by a read-write lock is a potential denial-of-service surface if an
attacker can influence the read-to-write ratio or the read hold duration. A
system that exposes an API where an external caller can trigger arbitrarily
many concurrent, long-held reads of a structure that internal code also needs
to write to, for example a public endpoint that reads a rate-limit table
directly locked by the same read-write lock an internal admin path writes to,
should treat that read path's request rate and duration as an availability
control, not merely a performance concern, and should bound both explicitly
rather than trusting the lock's fairness policy to protect the writer under
adversarial load.

A second, narrower implication concerns poisoning-on-panic semantics, where an
implementation offers them. Rust's asymmetric poisoning, where only a
panicking writer poisons the lock and a panicking reader does not, per
dimension 8, means an attacker who can reliably trigger a panic partway
through a write, for example by supplying input that a writer processes
without full validation before mutating shared state, can force the lock into
a poisoned state that denies subsequent access to every caller, reader and
writer alike, until the poison is explicitly cleared. Validating writer input
fully before acquiring the write lock, rather than inside the critical
section, narrows this surface.

## 18. References

- P. J. Courtois, F. Heymans, D. L. Parnas, "Concurrent Control with
  'Readers' and 'Writers'", Communications of the ACM, Volume 14, Issue 10,
  October 1971, pages 667 to 668. DOI 10.1145/362759.362813. The ACM Digital
  Library page returned HTTP 403 on direct fetch during verification on
  2026-08-02; the citation rests on the paper's standard bibliographic record
  rather than a live-fetched abstract, and that limit is stated here.
- Oracle, `ReentrantReadWriteLock` class documentation, JDK 21 API
  specification. https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/locks/ReentrantReadWriteLock.html
  verified 2026-08-02.
- Rust standard library, `std::sync::RwLock` struct documentation.
  https://doc.rust-lang.org/std/sync/struct.RwLock.html
  verified 2026-08-02.
- Microsoft Learn, `ReaderWriterLockSlim` class, .NET API reference.
  https://learn.microsoft.com/en-us/dotnet/api/system.threading.readerwriterlockslim
  verified 2026-08-02.
- The Linux Kernel documentation, "Lock types and their rules",
  locking/locktypes.rst.
  https://www.kernel.org/doc/html/latest/locking/locktypes.html
  verified 2026-08-02.
- PostgreSQL 18 Documentation, Chapter 13, "Concurrency Control", section
  13.2.1, "Introduction". https://www.postgresql.org/docs/current/mvcc-intro.html
  verified 2026-08-02.

## Code examples

Three languages, each running a working reader-writer scenario against a
small shared cache, chosen because each represents a materially different
implementation shape covered in dimension 8. Go's value-embedded, non-reentrant
`sync.RWMutex`, Rust's compiler-enforced guard-typed `RwLock<T>`, and an
async, single-threaded ordering-only lock in TypeScript for the Node.js event
loop shape. All three were run to completion during authoring; output is
noted per sample. Java, the fourth language with the richest standard-library
implementation covered in this entry, is omitted from the runnable set because
no JRE is installed in the authoring environment, which was verified with
`javac -version` before the omission rather than assumed.

### Go

```go
package main

import (
	"fmt"
	"sync"
)

type Cache struct {
	mu   sync.RWMutex
	data map[string]int
}

func NewCache() *Cache {
	return &Cache{data: make(map[string]int)}
}

func (c *Cache) Get(key string) (int, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	v, ok := c.data[key]
	return v, ok
}

func (c *Cache) Set(key string, value int) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.data[key] = value
}

func main() {
	cache := NewCache()
	var wg sync.WaitGroup

	for w := 0; w < 4; w++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for i := 0; i < 1000; i++ {
				cache.Set(fmt.Sprintf("k%d", id), i)
			}
		}(w)
	}

	for r := 0; r < 8; r++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for i := 0; i < 1000; i++ {
				cache.Get("k0")
			}
		}()
	}

	wg.Wait()
	v, ok := cache.Get("k0")
	fmt.Println("k0 final:", v, ok)
}
```

Run with `go run main.go` against Go 1.26.4. Output observed during
authoring is `k0 final: 999 true`, confirming the four writer goroutines and
eight reader goroutines completed without a data race and the last write won,
as expected for a race-free interleaving.

### Rust

```rust
use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use std::thread;

struct Cache {
    inner: RwLock<HashMap<String, i32>>,
}

impl Cache {
    fn new() -> Self {
        Cache { inner: RwLock::new(HashMap::new()) }
    }

    fn get(&self, key: &str) -> Option<i32> {
        let guard = self.inner.read().unwrap();
        guard.get(key).copied()
    }

    fn set(&self, key: String, value: i32) {
        let mut guard = self.inner.write().unwrap();
        guard.insert(key, value);
    }
}

fn main() {
    let cache = Arc::new(Cache::new());
    let mut handles = Vec::new();

    for w in 0..4 {
        let c = Arc::clone(&cache);
        handles.push(thread::spawn(move || {
            for i in 0..1000 {
                c.set(format!("k{}", w), i);
            }
        }));
    }

    for _ in 0..8 {
        let c = Arc::clone(&cache);
        handles.push(thread::spawn(move || {
            for _ in 0..1000 {
                let _ = c.get("k0");
            }
        }));
    }

    for h in handles {
        h.join().unwrap();
    }

    println!("k0 final: {:?}", cache.get("k0"));
}
```

Compiled with `rustc -O main.rs` against rustc 1.97.1. Output observed during
authoring is `k0 final: Some(999)`, confirming the same race-free interleaving
as the Go sample, with the guard types making it a compile error to touch
`inner`'s contents without holding the corresponding guard.

### TypeScript

```typescript
class AsyncRwLock {
  private activeReaders = 0;
  private writerActive = false;
  private waiters: Array<{ kind: "read" | "write"; resolve: () => void }> = [];

  private tryGrant(): void {
    while (this.waiters.length > 0) {
      const next = this.waiters[0];
      if (next.kind === "write") {
        if (this.activeReaders > 0 || this.writerActive) return;
        this.writerActive = true;
        this.waiters.shift();
        next.resolve();
        return;
      } else {
        if (this.writerActive) return;
        this.activeReaders++;
        this.waiters.shift();
        next.resolve();
      }
    }
  }

  async read<T>(fn: () => Promise<T> | T): Promise<T> {
    await new Promise<void>((resolve) => {
      this.waiters.push({ kind: "read", resolve });
      this.tryGrant();
    });
    try {
      return await fn();
    } finally {
      this.activeReaders--;
      this.tryGrant();
    }
  }

  async write<T>(fn: () => Promise<T> | T): Promise<T> {
    await new Promise<void>((resolve) => {
      this.waiters.push({ kind: "write", resolve });
      this.tryGrant();
    });
    try {
      return await fn();
    } finally {
      this.writerActive = false;
      this.tryGrant();
    }
  }
}

async function main() {
  const lock = new AsyncRwLock();
  let value = 0;
  const readLog: number[] = [];

  const writer = lock.write(async () => {
    await new Promise((r) => setTimeout(r, 5));
    value = 42;
  });

  const readers = [1, 2, 3].map(() =>
    lock.read(async () => {
      readLog.push(value);
    })
  );

  await Promise.all([writer, ...readers]);
  console.log("final value:", value);
  console.log("read log:", readLog);
}

main();
```

Compiled with `npx tsc --target es2020 --module commonjs rwlock.ts` and run
with `node rwlock.js`. Output observed during authoring is `final value: 42`
followed by `read log: [ 42, 42, 42 ]`, confirming the three concurrently
queued readers were all held back until the earlier-queued writer's promise
resolved, so none of them observed the pre-write value of zero, which is the
ordering guarantee this variant exists to provide on a single-threaded event
loop where no true parallel memory access is possible in the first place.
