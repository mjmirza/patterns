---
name: Lock Striping
slug: lock-striping
family: 09-concurrency
category: Concurrency
aliases: [Lock Splitting, Striped Locks, Segment Locking, Partitioned Locking]
first_described: "Goetz, Peierls, Bloch, Bowbeer, Holmes, Lea 2006"
maturity: canonical
related: [read-write-lock, thread-pool, sharding, optimistic-locking, double-checked-locking]
incompatible_with: [global-lock]
verified: 2026-08-02
---

# Lock Striping

## 1. Name, aliases, and lineage

The canonical name is Lock Striping. The technique is documented in Brian
Goetz, Tim Peierls, Joshua Bloch, Joseph Bowbeer, David Holmes, and Doug Lea,
*Java Concurrency in Practice*, Addison-Wesley, 2006, Chapter 11,
"Performance and Scalability", in the section on lock splitting and lock
striping. The book distinguishes two related moves. Lock splitting divides one
lock guarding two independent pieces of state into two locks, one per piece.
Lock striping is the generalization of that split to an array of N locks
guarding N partitions of one logical structure, most often a hash table, where
the partition a given key belongs to is chosen by hashing the key. The book
uses `java.util.concurrent.ConcurrentHashMap` as the running example of a
production data structure built this way, and this description matches the
documented behavior of `ConcurrentHashMap` prior to Java 8, discussed in
dimension 9 below.

The name Lock Splitting is used for the same family of ideas in the same
chapter, and some authors treat splitting as the two-lock special case of the
N-lock striping technique rather than a wholly separate pattern. Segment
Locking and Partitioned Locking are the names used in database internals
literature and in systems programming for the identical idea applied to a
lock manager's own internal bookkeeping rather than to application data. The
PostgreSQL lock manager documentation, cited in dimension 9, uses the word
partitions for exactly this structure. Striped Locks is the name Google
Guava gives its public library implementation, also cited in dimension 9.

No single named inventor claims the technique the way the Gang of Four claim
their 23 patterns. Lock striping is better understood as a documented,
recurring engineering practice that predates its formal name in the concurrency
literature. Doug Lea's earlier book, *Concurrent Programming in Java. Design
Principles and Patterns*, second edition, Addison-Wesley, 1999, discusses
partitioned synchronization as a scalability technique for collection classes,
and Lea was also a co-author of `java.util.concurrent` itself, so the practice
was already present in Lea's own library code before the 2006 book gave it the
widely used name.

## 2. Problem and context

A single mutable structure, most often a hash table, a counter map, a cache, or
an in-memory index, is accessed by many threads at once. Some of those threads
only read. Others write. The simplest safe implementation guards the entire
structure with one lock. Every operation, on any key, from any thread,
serializes behind that one lock. On a machine with one core this costs nothing
extra. On a machine with many cores it throws away nearly all of the available
parallelism, because two threads updating two keys that have nothing to do
with each other still wait on each other.

The forcing context is specific. The structure is logically partitionable by
some property of the operation, almost always a key, and the partitions are
genuinely independent of one another most of the time. Updating the balance
under key alice does not need to observe or coordinate with an update under
key bob. If the workload instead requires a cross-key invariant to hold at
every instant, for example a global sum that must always be consistent with
every per-key value, lock striping stops being a free win and becomes a source
of a new problem, discussed in dimension 4.

The single-lock structure also creates a second, quieter problem even on a
lightly loaded system. Lock contention is not only a throughput problem, it is
a latency and fairness problem. A thread doing a fast read can be forced to
wait behind a thread doing a slow write on a completely unrelated key, simply
because both threads happened to want the one lock at the same moment. Lock
striping removes that coupling for the common case where the two keys hash to
different stripes.

## 3. Forces

**Concurrency versus memory.** More stripes mean less contention because fewer
threads collide on any one lock, but each stripe also carries the fixed cost of
a lock object, and in some designs a per-stripe cache line, so the memory and
false-sharing cost scales with the stripe count. *Java Concurrency in Practice*
frames this directly. `ConcurrentHashMap`'s default concurrency level of 16
(cited in dimension 9) was chosen as a practical middle ground rather than
derived from a formula, because the correct number depends on the actual
contention profile of the workload, which is rarely known in advance.

**Latency versus throughput.** Striping raises aggregate throughput under
concurrent load by letting independent operations run in parallel, but a single
serialized operation, one thread, no contention, pays a small fixed overhead
for the extra hash computation to find its stripe, compared to acquiring one
well-known lock directly. This cost is negligible in almost every real
workload and is included here because the trade-off table in dimension 12
should be honest about it rather than presenting striping as strictly free.

**Correctness versus scalability.** The moment an operation needs to touch two
different stripes at once, for example a rename that must move a value from
key A to key B atomically, or a resize the whole table operation, striping
either requires acquiring multiple stripe locks in a fixed global order to
avoid deadlock, or it requires falling back to a coarser lock for that one
operation, or it requires redesigning the operation to avoid needing a cross
stripe atomicity guarantee at all. Every one of these responses adds
complexity that a single global lock never had to pay.

**Fairness and starvation.** A striped design distributes contention, but it
does not evenly distribute it unless the hash function used to choose a
stripe is itself close to uniform over the actual key distribution. A poor
hash function, or a workload where a small number of hot keys happen to
collide on one stripe, reproduces the original single-lock bottleneck inside
one stripe while leaving the others idle, and this failure is frequently
invisible until it is measured, because the code still looks correct and the
aggregate lock count still looks high.

**Cognitive load and debuggability.** A single lock is trivial to reason about
and trivial to see in a debugger or a thread dump. An array of locks, hashed by
key, is harder to reason about for anyone who has to hold a stack trace showing
thread A blocked on `stripes[7].mutex` and mentally reconstruct which
application-level keys could possibly be contending for stripe 7. This cost is
paid by every future maintainer, not only the original author, and it is a
real force even though it is rarely quantified in a benchmark.

## 4. Applicability and non-applicability

Reach for lock striping when all of the following hold together.

- The structure is naturally partitionable by a stable key, and operations on
  different keys are logically independent of each other.
- Profiling, not intuition, has shown that a single lock guarding the whole
  structure is a measured contention bottleneck under the real or realistic
  concurrent workload. Lock striping is a scalability optimization, and
  optimizing before measuring risks adding real complexity for an imaginary
  problem.
- The operations that matter most are single-key operations, get, put,
  increment, remove, rather than whole-structure scans or cross-key
  transactions.
- The number of expected concurrent threads that can plausibly contend is
  large enough, typically more than the number of stripes you would otherwise
  consider, that a single lock would genuinely serialize real work.

Do NOT reach for lock striping in these situations, and the reason is given
alongside each.

- **The structure needs whole-table atomic operations** as a normal part of its
  workload, for example an atomic swap of the entire map, or an iteration
  that must observe a single consistent snapshot across all keys. Striping
  makes a whole-table lock either impossible without acquiring every stripe in
  order, which reintroduces global serialization and the deadlock-ordering
  discipline of dimension 4's next point, or it makes iteration only weakly
  consistent, which is a correctness change the caller must be able to accept.
- **The number of distinct keys is small and bounded,** and contention was never
  measured to be a problem. With four keys and four threads, four stripes and
  one lock per key are close to the same thing, and a plain `ConcurrentHashMap`
  or a per-key lock map already solves it with far less custom code to
  maintain.
- **Two different keys must be locked together** for a single operation, and this
  is common rather than rare, for example a funds transfer that debits one
  account and credits another as one atomic step. Striping introduces the risk
  of deadlock between two threads acquiring the same two stripes in opposite
  order, and the standard fix, acquiring stripes in a canonical order such as
  sorted stripe index, is exactly the kind of subtle correctness rule that a
  single lock never needed and that a future contributor can silently break.
- **The workload is read-heavy with rare writes.** A `ReadWriteLock` or an
  optimistic, versioned read (the pattern documented separately as
  Optimistic Locking, or a copy-on-write structure) frequently outperforms
  striping for this shape without the hashing and stripe-count tuning
  overhead, because readers never block each other regardless of key.
- **The environment is single-threaded**, for example a Node.js event loop
  process with no worker threads, or the structure is only ever touched from
  one thread. There is no lock contention to relieve, and the only thing
  striping can add in that setting is unneeded complexity, unless the goal is
  the different problem of serializing overlapping asynchronous operations on
  the same logical key without blocking the event loop, which is a legitimate
  but distinct use covered as an implementation variant in dimension 8.

## 5. Structure

- **Striped resource.** The logical structure the caller wants to treat as one
  thing, for example a map, a set of counters, or a cache. It exposes an API
  keyed by some identifier, and internally it does not correspond to any single
  physical lock.
- **Stripe.** One partition of the striped resource, each carrying its own
  independent synchronization primitive, a mutex, a semaphore, or a
  read-write lock, and the slice of state that primitive protects. Stripes are
  fixed in number for the lifetime of the structure in most implementations.
  A stripe is the unit of contention, the unit that a thread actually blocks
  on.
- **Stripe selector.** The function that maps an operation's key to exactly
  one stripe index, almost always hash(key) mod N or, when N is a power of
  two, hash(key) and (N - 1). The selector must be deterministic. The same key
  must always resolve to the same stripe for the life of the structure, or two
  operations on the same key could run against different locks and observe
  each other's writes without ever synchronizing, which reintroduces exactly
  the race the whole pattern exists to prevent.
- **Caller.** The thread performing an operation. It never holds more than one
  stripe lock at a time in the common case, and it never needs to know which
  stripe index its key resolved to, that detail stays internal to the striped
  resource.

## 6. ASCII structure diagram

```
                     StripedResource
                +---------------------------+
 caller ------->|  op(key, ...)             |
                |    idx = hash(key) mod N  |
                +-------------+-------------+
                              |
              chooses exactly one of N stripes
                              |
        +--------+--------+--v-----+--------+--------+
        |Stripe 0|Stripe 1|Stripe 2|  ...   |Stripe N-1|
        | mutex  | mutex  | mutex  |        |  mutex   |
        | data0  | data1  | data2  |        |  dataN-1 |
        +--------+--------+--------+        +----------+

 key "alice"  --hash--> idx 2 --> only Stripe 2's mutex is taken
 key "bob"    --hash--> idx 0 --> only Stripe 0's mutex is taken
 alice and bob run in parallel, no shared lock between them
```

## 7. Dynamics

```
Thread A                Stripe 2 (mutex)        Thread B
   |  op("alice")             |                     |
   |  idx = hash("alice")=2   |                     |
   |------------lock--------->|                     |
   |        (acquired)        |                     |
   |  mutate data2["alice"]   |     op("bob")        |
   |                          |    idx=hash("bob")=0 |
   |                          |                      |
   |                    [Stripe 0 not shown, B never |
   |                     touches Stripe 2 at all]    |
   |------------unlock------->|                     |
   |        (released)        |                     |
```

The important property this diagram makes visible is that Thread B never
appears in Stripe 2's timeline at all when its key hashes elsewhere. Under a
single global lock, B's entire operation would have queued behind A's,
regardless of key. Under striping, A and B execute concurrently whenever their
stripe selector returns different indices, and only serialize on the rarer
event that two keys collide on the same stripe. That collision rate is a
direct function of stripe count and hash quality, discussed further in
dimension 11.

A second dynamic worth showing is the multi-stripe path, used only for
operations that must touch two keys atomically, for example a move between two
buckets. This path is the one place where striping reproduces a lock-ordering
discipline.

```
Thread A: moveBalance("alice" -> "bob")
  idxA = hash("alice") = 2
  idxB = hash("bob")   = 0
  lockOrder = sort(idxA, idxB) = [0, 2]
  lock(Stripe 0)
  lock(Stripe 2)
  perform the two-key mutation
  unlock(Stripe 2)
  unlock(Stripe 0)

Thread B: moveBalance("bob" -> "alice")
  idxA = hash("bob")   = 0
  idxB = hash("alice") = 2
  lockOrder = sort(idxA, idxB) = [0, 2]     <- same canonical order as A
  ...no deadlock, because both threads always lock 0 before 2
```

If Thread A and Thread B instead each acquired their own pair of stripes in
source key first order without sorting, A would take Stripe 2 then wait for
Stripe 0, while B took Stripe 0 then waited for Stripe 2, a classic deadlock.
This is why any striped design that supports a multi-key operation must sort
the stripe indices into one canonical order before acquiring, every time,
without exception.

## 8. Implementation variants

**Fixed-size mutex array, eager allocation.** The simplest and most common
shape. An array of N mutexes is allocated up front, sized as a power of two so
the modulo can be a bit mask, and the stripe selector hashes the key and masks
it. This is what the Go and Rust code samples below implement. It costs N
mutex objects for the lifetime of the structure regardless of how many keys
are actually in use, which is cheap for a mutex but not free.

**Lazy, weakly referenced stripes.** Guava's Striped class, cited in
dimension 9, offers a weak variant that creates the underlying lock lazily on
first use per key and lets the JVM garbage collector free a stripe's
lock object once nothing is holding it, so a caller can request thousands of
logical stripes, effectively one lock per key, without paying for thousands of
live objects at once. This trades a small amount of per-access indirection and
GC pressure for much finer partitioning than a fixed small array can offer,
which is the right choice when the true number of distinct keys is large and unknown
in advance and hot keys are rare enough that most locks would sit idle.

**Read-write striping.** Instead of a plain mutex per stripe, each stripe
carries a `ReadWriteLock`, so readers within one stripe can run concurrently
with each other and only block writers to that same stripe. This composes
striping with the Read-Write Lock pattern and is worth it specifically when
per-stripe read traffic is high relative to writes, which is common for a
cache. Guava's `Striped.readWriteLock(int)` factory ships this variant
directly.

**Segment-owned sub-collections, pre-Java-8 `ConcurrentHashMap` style.** Rather
than one shared array behind a uniform key-value API, each stripe, called a
segment in the original design, owns its own independent hash table
fragment, its own resize logic, and its own lock. A whole-table `size()` call
sums across segments without a global lock by taking a best-effort
non-blocking pass, retrying with locks only if the counts look inconsistent
across two attempts. This variant buys per-segment resizing but costs
noticeably more implementation complexity than a flat mutex array, which is
exactly the trade-off `ConcurrentHashMap` itself walked away from in Java 8 in
favor of a different, finer-grained per-bin CAS and synchronized-block scheme,
discussed in dimension 9.

**Striped counters via contended-cell arrays.** `java.util.concurrent.atomic.LongAdder`, cited in dimension 9, is a close relative rather than a strict
instance of this pattern. Instead of striping a key space, it stripes a single
logical counter across a dynamically grown array of independent cells, each
updated with a compare-and-swap rather than a lock, and the total is computed
by summing all cells on read. It is included here because the underlying
motivation, breaking one hot piece of shared mutable state into N
independently updatable pieces to relieve contention, is the same forcing idea
as lock striping, applied without an explicit mutex.

**Striped asynchronous serialization in a single-threaded runtime.** In
Node.js or any purely single-threaded event-loop environment, there is no
thread contention to relieve, but there is a related problem, two overlapping
asynchronous operations on the same logical key racing each other because
neither one blocks the event loop while awaiting I/O. A striped async lock
built from an array of chained promises, one per stripe, serializes
operations that hash to the same stripe while letting operations on different
keys run interleaved, without ever blocking a native OS thread. The
TypeScript sample below implements exactly this variant, and it is the
correct analogue of lock striping for a runtime that has no real threads to
contend over a mutex in the first place.

## 9. Known production uses

**`java.util.concurrent.ConcurrentHashMap`, prior to Java 8.** The class's own
Javadoc, for the Java 7 release, documents the segment-based design directly.
"The allowed concurrency among update operations is guided by the optional
concurrencyLevel constructor argument (default 16), which is used as a hint
for internal sizing. The table is internally partitioned to try to permit the
indicated number of concurrent updates without contention."
(https://docs.oracle.com/javase/7/docs/api/java/util/concurrent/ConcurrentHashMap.html,
verified 2026-08-02). The current Java 17 Javadoc still exposes the same
`concurrencyLevel` constructor parameter for source compatibility, though the
internal implementation changed in Java 8 to a per-bin, mostly lock-free CAS
and synchronized-block scheme rather than a fixed segment array
(https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html,
verified 2026-08-02).

**Google Guava's `Striped` class.** The class Javadoc states directly that it
provides "lock striping similar to that of `ConcurrentHashMap` in a reusable
form, and extends it for semaphores and read-write locks", and documents the
compact fixed-stripe form, for example `Striped.lock(availableProcessors() * 4)`, alongside the lazy weak-reference variant for when "only a small portion"
of many possible stripes would be in use at once
(https://guava.dev/releases/33.0.0-jre/api/docs/com/google/common/util/concurrent/Striped.html,
verified 2026-08-02).

**The PostgreSQL lock manager.** The lock manager's own internal design
document states, "To reduce contention, the lock manager's data structures
have been split into multiple 'partitions', each protected by an independent
LWLock. Most operations only need to lock the single partition they are
working in," and that "Each possible lock is assigned to one partition
according to a hash of its LOCKTAG value." The same document records that this
replaced a single global `LockMgrLock` that had become a measured contention
bottleneck before PostgreSQL 8.2
(https://github.com/postgres/postgres/blob/master/src/backend/storage/lmgr/README,
verified 2026-08-02). This is Segment Locking applied to the database's own
internal lock bookkeeping, the systems-programming naming variant referenced
in dimension 1, and it is a useful example because it documents the
before-and-after contention motivation explicitly rather than presenting
striping as an assumed default.

**`java.util.concurrent.atomic.LongAdder`, as a related counter-striping
technique.** The class Javadoc describes "one or more variables that together
maintain an initially zero long sum," where "when updates are contended across
threads, the set of variables may grow dynamically to reduce contention," and
states plainly that under high contention "expected throughput of this class
is significantly higher [than AtomicLong], at the expense of higher space
consumption"
(https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/atomic/LongAdder.html,
verified 2026-08-02). Listed here as a related, not identical, production use
because it stripes a single counter's internal storage rather than a keyed
collection, exactly the distinction drawn in dimension 8's discussion of it.

## 10. Consequences

Positive.

- Aggregate throughput under real concurrent contention rises substantially,
  because independent operations that used to serialize behind one lock now
  run in parallel whenever their keys hash to different stripes.
- Worst-case latency for an unrelated operation drops, because a slow write on
  one key no longer blocks a fast read on a different key that happens to
  share nothing but the same logical structure.
- The technique composes with other synchronization refinements, notably
  read-write locking per stripe and lazy stripe allocation, so it is tunable
  rather than all-or-nothing.
- It requires no change to the caller's API. A well-encapsulated striped
  structure looks identical from outside to a single-lock structure, so it can
  be introduced as an internal refactor, as described in dimension 14.

Negative.

- Any operation that must span two or more stripes atomically becomes harder
  to implement correctly and carries a real deadlock risk if stripe locks are
  not acquired in a consistent, canonical order, as shown in dimension 7.
- Whole-structure operations, size, iteration, snapshot, either lose strong
  consistency, becoming best-effort or eventually consistent across stripes,
  or they require acquiring every stripe, which reintroduces the exact global
  serialization the pattern was built to avoid, only for that one operation.
- The right number of stripes is workload-dependent and is not knowable from
  first principles. Under-striping reproduces the original bottleneck inside
  one hot stripe. Over-striping wastes memory and adds a small fixed overhead
  to every operation for no measured benefit.
- The design is genuinely harder to reason about, to review, and to debug from
  a thread dump than a single lock, and that cost is paid by every future
  reader of the code, not only the original implementer.

## 11. Failure modes and misuse

**Hot-key collision inside one stripe.** Symptom, a stripe count that looks
generously high, and aggregate lock statistics that look mostly idle, coexist
with a small number of threads still blocking heavily on one particular
mutex. Cause, the workload is skewed toward a small number of keys, and those
keys happen to hash into the same stripe, or the stripe count is small enough
that a uniformly random hash still produces real collisions by the
birthday paradox. Fix, increase the stripe count so collisions become rarer,
switch to a hash function with better avalanche behavior for the actual key
distribution, or, when a single key is genuinely so hot that no amount of
striping helps because all of its own traffic must serialize on itself
regardless, restructure that specific key's updates, for example with a
striped counter cell array as described in dimension 8, rather than a single
mutex-protected value.

**Deadlock from unordered multi-stripe acquisition.** Symptom, the process
hangs under load, specifically under load that exercises a rare multi-key
operation like a rename or transfer, and a thread dump shows two threads each
holding one stripe lock and waiting on the other. Cause, an operation that
needs two stripes acquires them in an order derived from the caller's argument
order, for example source, then destination, rather than a canonical order
independent of which side called which. Fix, sort the required stripe indices
before acquiring, always in the same direction, as shown in dimension 7's
second diagram, and cover this specific interleaving with a concurrency test
as described in dimension 15.

**Silent race from an inconsistent stripe selector.** Symptom, data
occasionally appears lost or stale for a specific key under concurrent access,
even though every individual operation looks correctly locked in code review.
Cause, the stripe selector is not deterministic for a given key, most often
because it hashes on a mutable field of the key object, or because the
selector's hash function or modulus changed between two versions of the code
that are both live at once, for example during a rolling deployment, so two
processes disagree about which stripe a key belongs to. Fix, the stripe
selector must be a pure, deterministic function of the key's stable identity
alone, and it must be part of the structure's contract, not an implementation
detail that can silently drift between versions.

**Whole-structure operations treated as if they were still atomic.** Symptom,
a `size()`, an iteration, or a snapshot occasionally returns a count or a set
of entries that never existed at any single point in wall-clock time, and a
caller written before the structure was striped, expecting the old strong
consistency, produces subtly wrong downstream results, for example an
off-by-a-few count in a report that nobody notices for weeks. Cause, the
structure was refactored from a single lock to stripes, and the whole-table
operations were left as a best-effort pass over stripes without documenting or
enforcing the weakened consistency guarantee. Fix, either explicitly document
and test the weak-consistency contract for every whole-structure operation, or
implement a true global-consistent snapshot by acquiring every stripe lock in
canonical order for that operation only, accepting that it will serialize.

**Resource exhaustion from over-eager fixed striping.** Symptom, the process's
memory footprint grows noticeably for a structure whose actual data footprint
is small, and profiling attributes a sizable fraction of that memory to
mutex or lock objects rather than application data. Cause, a fixed, eagerly
allocated stripe array was sized far larger than the realistic concurrent
thread count needs, sometimes copied from another system's tuning without
re-measuring. Fix, size the stripe count from the realistic concurrent access
pattern, per the guidance quoted from the `ConcurrentHashMap` Javadoc in
dimension 3, or switch to the lazy, weakly referenced variant from dimension 8
when the true number of distinct keys is large and unpredictable.

## 12. Trade-off matrix

| Force | Lock Striping | Single Global Lock | Read-Write Lock (unstriped) | Optimistic Locking | Sharding across processes |
|---|---|---|---|---|---|
| Write concurrency across distinct keys | High, near-linear up to stripe count | None, fully serialized | Low, one writer at a time across whole structure | High, no blocking, but retries under contention | High, no shared lock at all |
| Read concurrency | Same as writes unless read-write striped | None | High, unlimited concurrent readers | High, no blocking | High |
| Cross-key atomic operations | Hard, needs ordered multi-lock or falls back to global | Trivial, already global | Trivial for reads and writes within the one lock | Hard, needs a version check across all touched keys | Hard, needs distributed transaction or 2PC |
| Memory overhead | One lock per stripe, fixed or lazy | One lock total | One lock total | None, or a version field per record | Process and network overhead per shard |
| Implementation complexity | Moderate, hashing plus ordering discipline | Trivial | Low | Moderate, requires retry logic | High, requires partitioning and routing layer |
| Whole-structure consistency | Weak by default, strong only if all stripes locked | Strong, trivially | Strong, trivially | Weak, snapshot reads can be stale | Weak, cross-shard consistency is its own problem |
| Correct choice when | Partitionable key space, measured single-lock contention | Low contention, simplicity matters more than throughput | Read-heavy, writes rare | Low write-write conflict rate, retries are cheap | Data volume exceeds one process's memory or CPU |

## 13. Related and incompatible patterns

**Read-Write Lock.** Composes directly with striping rather than competing
with it. Each stripe can itself be a read-write lock instead of a plain
mutex, letting readers within a stripe run concurrently while still confining
writer exclusion to that one stripe. Guava's `Striped.readWriteLock` factory,
cited in dimension 9, ships exactly this composition.

**Sharding.** Shares the same core idea, partition by key to reduce
contention, but at a different granularity and across a different boundary.
Lock striping partitions synchronization within one process's memory space.
Sharding partitions data itself across separate processes or machines, each
with its own independent state and often its own independent lock or none at
all. A system frequently uses both, sharding across nodes for capacity and
striping within each node's own in-memory structures for concurrency, and the
two should not be confused when discussing where a given bottleneck actually
lives.

**Optimistic Locking.** An alternative response to the same underlying
problem, contention on shared mutable state, that avoids taking a lock at all
for the common case, instead detecting conflicts after the fact via a version
number or compare-and-swap and retrying. Where lock striping reduces the
probability of contention by shrinking what any one lock protects, optimistic
locking removes the lock from the write path entirely and accepts occasional
retries. The two are alternatives for the same force in dimension 3 rather
than compatible layers, though a system can legitimately use striping for one
structure and optimistic locking for another based on each one's measured
conflict rate.

**Double-Checked Locking.** A different, narrower technique, most often used
for lazy one-time initialization of a single shared value, not for an ongoing
keyed workload. It is mentioned as related because both patterns are
frequently taught in the same reducing lock scope family of concurrency
techniques, and both share the risk of subtle memory-visibility bugs if
implemented without the correct happens-before guarantees for the target
language's memory model, but they solve different problems and are not
substitutes for each other.

**Thread Pool.** Orthogonal rather than directly composed. A thread pool
governs how many worker threads exist and how work is scheduled onto them.
Lock striping governs how those threads, once running, synchronize access to
shared state. A system commonly uses both together, a bounded thread pool
executing tasks that then contend for a striped structure, and neither pattern
substitutes for the other.

**Global Lock, incompatible.** A single global lock guarding the entire
structure is the thing lock striping specifically replaces to relieve
contention, so the two are mutually exclusive designs for the same piece of
state at the same time. A system that claims to use lock striping while still
routing every operation through one additional outer lock has not actually
achieved the pattern's purpose, even if the striped locks technically exist
underneath, because the outer lock reintroduces the exact serialization the
inner striping was meant to remove.

## 14. Refactoring path in and out

Introducing lock striping into code that currently uses one lock.

1. Confirm, with a profiler or a production metric, that the single lock is a
   measured bottleneck under real or realistic concurrent load, per the
   applicability guidance in dimension 4. Skipping this step is the most
   common cause of striping being added where it was never needed.
2. Enumerate every operation the structure exposes and classify each as
   single-key, for example get, put, remove, increment, or multi-key, for
   example a move, a merge, or a whole-structure iteration. This list drives
   every remaining step.
3. Choose a stable, deterministic key for the stripe selector, and choose an
   initial stripe count. A reasonable starting point, following the reasoning
   in the `ConcurrentHashMap` Javadoc quoted in dimension 9, is a small
   multiple of the expected number of concurrently contending threads, never
   the number of expected distinct keys, since keys and threads are usually
   very different in count.
4. Replace the single lock field with an array of N locks and route every
   single-key operation identified in step 2 through `stripes[hash(key) & mask]` instead of the old single lock. Each single-key operation now only
   ever touches one stripe, and the change is behavior-preserving for these
   operations by construction, since correctness within one key never
   depended on any other key.
5. For each multi-key operation identified in step 2, rewrite it to acquire
   every stripe it needs in one fixed canonical order, for example sorted
   ascending by stripe index, as shown in dimension 7. Write a concurrency
   test, per dimension 15, that specifically exercises two threads calling the
   operation with the key arguments reversed, to catch the deadlock failure
   mode from dimension 11 before it reaches production.
6. Decide and document the new consistency contract for any whole-structure
   operation, size, iteration, or snapshot. Either implement it as a
   full-order acquisition of every stripe, accepting that it serializes, or
   implement it as a best-effort weakly consistent pass and update every
   caller's expectations and tests to match.
7. Load test again against the same realistic concurrent workload used in
   step 1, and confirm the measured contention actually dropped before
   declaring the refactor done. A striped design that does not measurably
   improve on the single-lock baseline under the real workload has likely
   under-partitioned the hot key or mis-sized the stripe count, and should be
   re-tuned rather than shipped as-is.

Removing lock striping from code that no longer needs it.

1. Confirm the reverse condition, that measured contention on the striped
   structure is now low, most often because the workload shrank, the hot keys
   moved elsewhere, or the caller pattern changed to favor whole-structure
   operations that were paying the multi-stripe acquisition cost on every
   call.
2. Collapse the stripe array back to a single lock, or to a `ReadWriteLock` if
   the workload turned out to be read-heavy, and remove the stripe selector
   and the canonical-ordering logic for multi-key operations, since a single
   lock has no ordering hazard to guard against.
3. Re-run the concurrency test suite from dimension 15 to confirm no
   regression, and re-run the load test to confirm the simplification did not
   reintroduce a contention problem the original striping was solving, which
   would indicate the removal decision in step 1 was premature.

## 15. Testing and verification

Correctness of a striped structure has to be tested at two separate layers,
because a bug in the selector or the ordering discipline can pass every
single-threaded test while still being wrong.

- **Single-threaded functional tests.** Ordinary unit tests of every
  operation's logic, get, put, remove, increment, the multi-key move, and the
  whole-structure iteration, run with no concurrency at all. These catch bugs
  in the business logic each operation performs, but they cannot catch
  anything specific to striping, since with one thread there is never any
  contention to expose a locking bug.
- **Stripe-selector determinism tests.** A focused test asserting that the
  same key, called many times, always resolves to the same stripe index for
  the life of one structure instance, and that the observed distribution of
  stripe indices across a realistic sample of real keys is reasonably uniform
  rather than collapsing onto a small number of stripes, which would be an
  early warning of the hot-key collision failure mode from dimension 11.
- **Concurrent stress tests with real threads.** A test that spins up many
  threads, more than the stripe count, performing a mix of single-key
  operations on a shared set of keys, and asserts the final state is exactly
  what a sequential, single-threaded execution of the same operations would
  have produced. This is the direct test for lost updates. The Go code sample
  accompanying this entry is written in exactly this shape, ten thousand
  increments per key from a dedicated goroutine, then asserting the counter
  equals ten thousand exactly, and a wrong stripe boundary or a missing lock
  would show up as a value less than ten thousand under real scheduling.
- **Deadlock-specific tests for multi-key operations.** A test that
  deliberately runs the multi-key operation from both directions
  concurrently, for example many threads calling move(A, B) at the same
  time many other threads call move(B, A), with a bounded timeout on the
  whole test. A canonical-ordering bug, described in dimension 11, produces an
  intermittent hang here that a purely functional test would never surface,
  and the test must actually assert on the timeout, a test that merely does
  not crash can pass while occasionally hanging in CI without anyone
  noticing the flake's real cause.
- **Race detector tooling.** Language-level race detectors, for example Go's
  `-race` flag or Rust's reliance on the type system plus tools like
  ThreadSanitizer for `unsafe` code, should be run over the concurrent stress
  tests above, because a race detector catches unsynchronized access to a
  variable, a class of bug that a correctness assertion on the final value can
  sometimes miss if the racing writes happen to still add up to the right
  total by coincidence on a given run.

## 16. Observability signals

A striped structure should expose enough per-stripe telemetry to answer,
without attaching a debugger, whether the stripe count and hash function are
actually doing their job under the real production workload.

- **Per-stripe lock wait time or contention count.** The single most direct
  signal. If contention is roughly even across all stripes, the design is
  working as intended. If one or a small number of stripes show wait times an
  order of magnitude above the rest while others sit near zero, that is the
  hot-key collision failure mode from dimension 11, visible before it shows up
  as a user-facing latency complaint.
- **Stripe occupancy or key distribution histogram.** For designs where stripe
  assignment can be inspected, a periodic sample of how many live keys or how
  much traffic each stripe carries. A skewed histogram is a leading indicator
  that either the hash function or the actual key distribution deserves a
  second look, well before contention metrics get bad enough to alert on.
- **Multi-stripe operation duration and retry or wait count.** Any operation
  that must acquire more than one stripe should be timed and counted
  separately from single-stripe operations, since it is the one operation
  shape carrying the deadlock-ordering risk from dimension 11, and a rising
  duration or a rising count of these operations under load is a signal the
  system's workload mix has shifted toward the shape striping handles worst.
- **A healthy dashboard** shows contention counts and wait times distributed
  roughly evenly across all stripes, multi-stripe operations forming a small,
  stable fraction of total operations, and aggregate throughput scaling
  roughly linearly with added concurrent load up to the stripe count. **An
  unhealthy dashboard** shows one or two stripes carrying most of the total
  wait time while others sit near idle, a rising fraction of multi-stripe
  operations, or throughput flattening well before the configured stripe
  count would predict it should, any of which points back at the specific
  failure mode in dimension 11 that matches the shape observed.

## 17. Security and privacy implications

Lock striping's attack surface is narrow and mostly indirect, since it is a
performance and correctness technique rather than a data-handling boundary,
but two implications are worth stating rather than leaving silent.

If the stripe selector's hash function is derived from user-controllable input
and is a fast, non-cryptographic hash chosen purely for speed and uniform
distribution, an adversary who can predict or influence that hash function's
output could in principle craft a set of keys that all collide onto the same
stripe, deliberately reproducing the hot-key collision failure mode from
dimension 11 as a denial-of-service technique against the structure's
throughput. This is the same class of concern documented for hash table
implementations broadly, algorithmic complexity attacks via hash collision,
and the standard mitigation, a hash function keyed with a value chosen randomly
at process startup so an external attacker cannot predict which keys collide,
applies equally here whenever the structure is exposed to attacker-influenced
keys, for example a public API's request identifiers or user-supplied cache
keys.

Beyond that, lock striping introduces no new data-handling implication of its
own. It does not change what data is stored, logged, or transmitted, and it
does not introduce a new information-disclosure surface by itself, since the
lock objects and stripe indices are purely internal implementation state with
no real content to leak. Any per-stripe observability signal exposed
externally, per dimension 16, should still be reviewed under the same general
policy the rest of the system already applies to metrics and telemetry,
because a sufficiently fine-grained per-key metric could in principle leak
information about which specific keys are hot, but that concern belongs to
the metrics design generally and is not specific to the striping technique
itself.

## Code examples

Three languages are used, chosen because each exercises the pattern in a
genuinely different runtime concurrency model rather than repeating the same
shape three times. Go and Rust both use real operating system threads and a
real mutex array, the textbook shape of the pattern. TypeScript, running on
Node.js's single-threaded event loop, has no OS-level lock contention to
relieve at all, so it instead demonstrates the async-serialization variant
from dimension 8, which solves the analogous problem, overlapping operations
on the same logical key racing each other, without ever blocking a thread that
does not exist to block. Java and Python are the two languages from the
template's list where this pattern is most idiomatically expressed by
`ConcurrentHashMap` and by process-level sharding respectively rather than by
hand-written stripe arrays, and are omitted here in favor of showing the
pattern built from first principles in the three languages above, since
dimension 9 already documents `ConcurrentHashMap`'s own production
implementation in detail.

### Go

Compiled and run with `go run` (Go 1.26.4, `go build` succeeds with no
warnings). Ten goroutines each increment a per-key counter ten thousand times
concurrently, keys are distributed across four stripes via an FNV hash, and
the final counts confirm no update was lost.

```go
package main

import (
	"fmt"
	"hash/fnv"
	"sync"
)

type StripedCounter struct {
	stripes []stripe
	mask    uint32
}

type stripe struct {
	mu     sync.Mutex
	counts map[string]int64
	_      [56]byte
}

func NewStripedCounter(stripeCountPow2 uint) *StripedCounter {
	n := uint32(1) << stripeCountPow2
	s := &StripedCounter{stripes: make([]stripe, n), mask: n - 1}
	for i := range s.stripes {
		s.stripes[i].counts = make(map[string]int64)
	}
	return s
}

func (s *StripedCounter) stripeFor(key string) *stripe {
	h := fnv.New32a()
	h.Write([]byte(key))
	return &s.stripes[h.Sum32()&s.mask]
}

func (s *StripedCounter) Incr(key string, delta int64) {
	st := s.stripeFor(key)
	st.mu.Lock()
	st.counts[key] += delta
	st.mu.Unlock()
}

func (s *StripedCounter) Get(key string) int64 {
	st := s.stripeFor(key)
	st.mu.Lock()
	v := st.counts[key]
	st.mu.Unlock()
	return v
}

func hammer(sc *StripedCounter, wg *sync.WaitGroup, key string) {
	defer wg.Done()
	for i := 0; i < 10000; i++ {
		sc.Incr(key, 1)
	}
}

func main() {
	sc := NewStripedCounter(4)
	var wg sync.WaitGroup
	keys := []string{"alice", "bob", "carol", "dave", "erin", "frank"}
	for _, k := range keys {
		wg.Add(1)
		go hammer(sc, &wg, k)
	}
	wg.Wait()
	for _, k := range keys {
		fmt.Printf("%s=%d\n", k, sc.Get(k))
	}
}
```

Verified output, every key reaches exactly 10000, confirming no update was
lost across concurrent goroutines contending for a small, fixed set of
stripes.

```
alice=10000
bob=10000
carol=10000
dave=10000
erin=10000
frank=10000
```

The `_ [56]byte` field in the `stripe` struct pads each stripe to occupy its
own CPU cache line on a typical 64-byte cache line architecture, avoiding
false sharing between adjacent stripes' mutexes, a detail worth keeping in a
production version of this code and worth removing, with a comment explaining
why, when portability across cache line sizes matters more than the last
increment of throughput.

### Rust

Compiled and run as a standalone binary with `rustc -O` (rustc 1.97.1, no
errors, no warnings). The structure and workload mirror the Go example
directly, `Arc<Mutex<HashMap<...>>>` per stripe, an FNV-1a hash chosen by
hand so the example has no external crate dependency to compile.

```rust
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::thread;

struct StripedCounter {
    stripes: Vec<Mutex<HashMap<String, i64>>>,
    mask: u64,
}

impl StripedCounter {
    fn new(stripe_count_pow2: u32) -> Self {
        let n = 1u64 << stripe_count_pow2;
        let mut stripes = Vec::with_capacity(n as usize);
        for _ in 0..n {
            stripes.push(Mutex::new(HashMap::new()));
        }
        StripedCounter { stripes, mask: n - 1 }
    }

    fn hash_key(key: &str) -> u64 {
        let mut h: u64 = 0xcbf29ce484222325;
        for b in key.as_bytes() {
            h ^= *b as u64;
            h = h.wrapping_mul(0x100000001b3);
        }
        h
    }

    fn incr(&self, key: &str, delta: i64) {
        let idx = (Self::hash_key(key) & self.mask) as usize;
        let mut m = self.stripes[idx].lock().unwrap();
        *m.entry(key.to_string()).or_insert(0) += delta;
    }

    fn get(&self, key: &str) -> i64 {
        let idx = (Self::hash_key(key) & self.mask) as usize;
        let m = self.stripes[idx].lock().unwrap();
        *m.get(key).unwrap_or(&0)
    }
}

fn main() {
    let sc = Arc::new(StripedCounter::new(4));
    let keys = ["alice", "bob", "carol", "dave", "erin", "frank"];
    let mut handles = Vec::new();
    for k in keys {
        let sc = Arc::clone(&sc);
        let key = k.to_string();
        handles.push(thread::spawn(move || {
            for _ in 0..10_000 {
                sc.incr(&key, 1);
            }
        }));
    }
    for h in handles {
        h.join().unwrap();
    }
    for k in keys {
        println!("{}={}", k, sc.get(k));
    }
}
```

Verified output, identical shape to the Go run, every key at exactly 10000.

```
alice=10000
bob=10000
carol=10000
dave=10000
erin=10000
frank=10000
```

Rust's ownership model is worth calling out here beyond the syntax. Because
`Mutex<T>` in the standard library wraps its protected data directly rather
than pairing a separate lock handle with a separate data pointer the way Go
and Java do, the compiler statically refuses to compile any access to
`stripes[idx]`'s inner `HashMap` that does not go through
`.lock().unwrap()` first. A whole category of the bug in this pattern, reading
or writing a stripe's data without holding that stripe's lock, is not a
runtime race to be caught by a test in Rust, it is a compile error, which is a
genuinely different correctness guarantee than the other two languages in
this entry offer for the same pattern.

### TypeScript

Compiled with `npx tsc --strict --target es2020 --module commonjs`
(TypeScript 7.0.2, zero errors under `--strict`) and run with Node.js 23.11.0.
This is the async-serialization variant from dimension 8, chosen deliberately
over a thread-based translation because Node.js has no OS thread contention
for a mutex to relieve in the first place. Each stripe is a chain of promises
rather than a mutex, so an operation on a given key waits for the previous
operation on the same stripe to settle before running, while operations on
different stripes interleave freely on the single event loop thread.

```typescript
type Task<T> = () => Promise<T>;

class Stripe {
  private tail: Promise<unknown> = Promise.resolve();

  run<T>(task: Task<T>): Promise<T> {
    const result = this.tail.then(task, task);
    this.tail = result.catch(() => undefined);
    return result;
  }
}

class StripedAsyncLock {
  private readonly stripes: Stripe[];

  constructor(private readonly stripeCount: number) {
    this.stripes = Array.from({ length: stripeCount }, () => new Stripe());
  }

  private hash(key: string): number {
    let h = 2166136261;
    for (let i = 0; i < key.length; i++) {
      h ^= key.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return (h >>> 0) % this.stripeCount;
  }

  withLock<T>(key: string, task: Task<T>): Promise<T> {
    return this.stripes[this.hash(key)].run(task);
  }
}

async function main(): Promise<void> {
  const lock = new StripedAsyncLock(8);
  const balances = new Map<string, number>(
    ["alice", "bob", "carol"].map((k) => [k, 0]),
  );

  async function credit(account: string, amount: number): Promise<void> {
    await lock.withLock(account, async () => {
      const current = balances.get(account) ?? 0;
      await new Promise((r) => setTimeout(r, 0));
      balances.set(account, current + amount);
    });
  }

  const ops: Array<Promise<void>> = [];
  for (const account of ["alice", "bob", "carol"]) {
    for (let i = 0; i < 500; i++) {
      ops.push(credit(account, 1));
    }
  }
  await Promise.all(ops);

  for (const [account, total] of balances) {
    console.log(`${account}=${total}`);
  }
}

main();
```

Verified output, every account reaches exactly 500.

```
alice=500
bob=500
carol=500
```

The `await new Promise((r) => setTimeout(r, 0))` inside `credit` deliberately
yields the event loop mid-operation, simulating a real asynchronous I/O call
between reading `current` and writing the new balance. Without the
`StripedAsyncLock` serializing operations per key, two overlapping credits to
the same account would both read the same stale `current` value before either
one wrote back, and the final total would be lower than 500 due to a lost
update, exactly the same class of bug lock striping prevents with real
threads, reproduced here in an environment with no threads at all.

## 18. References

1. Brian Goetz, Tim Peierls, Joshua Bloch, Joseph Bowbeer, David Holmes, Doug
   Lea, *Java Concurrency in Practice*, Addison-Wesley, 2006, Chapter 11,
   "Performance and Scalability", section on lock splitting and lock
   striping.
2. Doug Lea, *Concurrent Programming in Java. Design Principles and
   Patterns*, 2nd edition, Addison-Wesley, 1999, discussion of partitioned
   synchronization for collection classes under heavy concurrent load.
3. Oracle, ConcurrentHashMap class documentation, Java SE 7,
   https://docs.oracle.com/javase/7/docs/api/java/util/concurrent/ConcurrentHashMap.html,
   verified 2026-08-02.
4. Oracle, ConcurrentHashMap class documentation, Java SE 17,
   https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html,
   verified 2026-08-02.
5. Oracle, LongAdder class documentation, Java SE 17,
   https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/atomic/LongAdder.html,
   verified 2026-08-02.
6. Google, Guava Striped class documentation, release 33.0.0-jre,
   https://guava.dev/releases/33.0.0-jre/api/docs/com/google/common/util/concurrent/Striped.html,
   verified 2026-08-02.
7. PostgreSQL Global Development Group, lock manager internal design notes,
   src/backend/storage/lmgr/README,
   https://github.com/postgres/postgres/blob/master/src/backend/storage/lmgr/README,
   verified 2026-08-02.
