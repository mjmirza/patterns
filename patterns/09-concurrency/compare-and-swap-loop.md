---
name: Compare-and-Swap Loop
slug: compare-and-swap-loop
family: 09-concurrency
category: Concurrency
aliases: [CAS Loop, Compare-and-Exchange Loop, Optimistic Concurrency Retry Loop, Read-Modify-CAS Loop]
first_described: "Herlihy 1991 (theoretical treatment); IBM System/370 1970 (first hardware instruction)"
maturity: canonical
related: [read-copy-update, double-checked-locking, immutable-object, thread-safe-interface, copy-on-write]
incompatible_with: []
verified: 2026-08-02
---

# Compare-and-Swap Loop

## 1. Name, aliases, and lineage

The canonical name is Compare-and-Swap Loop, shortened in everyday engineering
speech to CAS loop. The operation it wraps is called compare-and-swap on most
hardware manuals and compare-and-exchange on x86 and .NET, since the Intel
instruction is literally named `CMPXCHG` and the .NET primitive is literally
named `Interlocked.CompareExchange`. Rust follows the exchange naming with
`compare_exchange` and `compare_exchange_weak`. The pattern itself, the retry
loop built around the primitive, is also called an optimistic concurrency
retry loop, because it optimistically computes a new value assuming nobody
else touched the location, then verifies that assumption atomically before
committing.

The hardware primitive predates its formal theoretical treatment by two
decades. Compare-and-swap has been part of the IBM System/370 architecture,
and every successor architecture IBM shipped, since 1970, where it and its
double-width sibling compare-and-swap-double were used to let the operating
system update shared kernel structures without disabling interrupts for the
whole critical section (Wikipedia, "Compare-and-swap", verified 2026-08-02,
https://en.wikipedia.org/wiki/Compare-and-swap). The theoretical grounding
that explains why this one instruction is so much more powerful than a plain
atomic read or an atomic increment came from Maurice Herlihy's 1991 paper
"Wait-Free Synchronization", which proved a strict hierarchy among atomic
primitives by what is now called consensus number, and placed compare-and-swap
at the top of that hierarchy with an unbounded consensus number, able to solve
wait-free consensus for any number of processes, while a plain atomic
read-modify-write like fetch-and-add sits at consensus number two (Herlihy,
"Wait-Free Synchronization", ACM Transactions on Programming Languages and
Systems, Vol. 13, No. 1, January 1991, as summarized and cited on the
Wikipedia "Compare-and-swap" page, verified 2026-08-02). The loop
construction around the primitive, retry until success, does not have a
single named inventor. It is the mechanical consequence of exposing a
primitive that can fail, and it appears independently in every concurrent
data structure paper from the 1990s onward that builds on compare-and-swap,
including Treiber's 1986 lock-free stack technical report and Michael and
Scott's 1996 lock-free queue paper, both of which use exactly this retry
shape.

## 2. Problem and context

A thread wants to update a single shared memory location, a counter, a
pointer, a flag, based on its current value, and it wants to do this without
taking a lock. Locking works, but it costs a system call or a spin under
contention, it can suffer priority inversion when a low-priority thread holds
the lock a high-priority thread is waiting for, and it does not compose well,
because a thread blocked inside one lock cannot make progress on anything
else even when the actual critical section is a single word update.

The problem shows up constantly in small, hot paths. A reference counter that
many threads increment and decrement, a linked list head pointer that many
threads push onto, a flag that says whether initialization has already run, a
sequence number a scheduler hands out, a lazily computed cache entry that
several threads might race to fill. In every one of these cases the actual
work per operation is tiny, often one word, so the overhead of acquiring and
releasing a mutex can dwarf the work being protected.

The context in which this pattern belongs is specifically single-location
updates. The moment the update needs to touch two or more independent memory
locations atomically, one word compare-and-swap cannot express it directly,
and the pattern either does not apply, or it applies by first collapsing the
multiple locations into one indirection, most commonly a pointer to an
immutable snapshot struct that itself holds all the fields that must change
together. That collapsing move, swap the whole snapshot pointer atomically
instead of the fields inside it, is the bridge between this pattern and the
Immutable Object and Copy-on-Write patterns, and it is discussed under
dimension 13.

## 3. Forces

Latency versus fairness. A CAS loop under low contention is extremely fast,
often faster than an uncontended mutex, because there is no kernel
involvement and no memory allocation. Under high contention it degrades
differently from a lock. A lock queues waiters and grants the lock roughly in
some order, so every waiter eventually gets served even if slowly. A naive CAS
loop has no queue. Every retrying thread races every other retrying thread for
the same cache line, and a particularly unlucky thread can in principle retry
far more times than an average thread, though on real hardware, where losing a
CAS costs one cache-coherence round trip, in practice retries are bounded and
short lived rather than pathological.

Throughput versus contention behavior. Under light contention a CAS loop has
close to no coordination cost beyond the one atomic instruction. Under heavy
contention on the same cache line, every failed attempt still generates a
cache-coherence transaction, the line bounces between cores, and aggregate
throughput can fall well below what a single lock protecting a batched update
would achieve. This is the central trade-off the pattern makes. It favors the
common case of low to moderate contention at the cost of the worst case of
extremely hot contention on one location.

Progress guarantee versus implementation simplicity. Depending on how the loop
is written, a CAS loop can be lock-free, meaning some thread in the system is
guaranteed to make progress even if others are stalled or killed mid-retry,
but it is not automatically wait-free, meaning any one particular thread is
not guaranteed to finish in a bounded number of steps, because an unlucky
thread can in theory keep losing the race forever. Achieving wait-freedom
generally requires additional machinery, helping, elimination, or bounded
backoff with fallback to a lock, which trades implementation complexity for
the stronger guarantee.

Memory ordering cost versus correctness. Compare-and-swap on real hardware
needs a memory fence, on architectures with weaker memory models than x86,
to be useful for anything beyond the single word it touches. Getting the
ordering wrong, using relaxed ordering where acquire-release or sequential
consistency was needed, produces the kind of bug that only shows up under
specific interleavings on specific hardware, and is close to impossible to
debug by inspection. The pattern's real cost lands on correctness review and
testing, discussed under dimension 15, in exchange for avoiding a lock.

Cognitive load versus performance. A CAS loop is harder to read and reason
about than the equivalent lock-protected code. The reader has to mentally
simulate what happens if another thread interleaves at every point in the
loop body, which is exactly the discipline the pattern demands and exactly
the discipline that ordinary application engineers are least practiced at.
The pattern favors raw performance and scalability over the approachability
of the code, and disciplined teams confine it to a small number of
well-reviewed, well-tested modules rather than scattering it throughout
application code.

## 4. Applicability and non-applicability

### When to reach for it

Use a compare-and-swap loop when the critical section is a single word or a
single pointer, the update is expressible as a pure function of the current
value, the code sits on a hot path where lock overhead is measurable, and
contention is expected to be light to moderate under normal operation. It is
the right tool for counters, sequence generators, single-linked-list head
pointers in a lock-free stack, single-slot caches that tolerate a redundant
recomputation on a lost race, flags that gate one-time initialization, and the
swap of an immutable snapshot pointer that stands in for a larger piece of
state.

Use it when you specifically need the progress guarantee that a lock cannot
give. If the thread holding a lock can be preempted, killed, or blocked on
I/O while holding it, every other thread waiting on that lock stalls too. A
CAS-based structure has no thread that can hold anything indefinitely, so a
preempted or killed thread never blocks the others from making progress, only
itself from finishing its own operation, and in a lock-free design at least
one thread always finishes.

### When not to reach for it, and why

Do not reach for it when the update touches more than one independent memory
location and there is no natural way to fold those locations into a single
atomically-swapped pointer. Attempting to CAS location A and then CAS
location B separately does not give you atomicity across both. Another thread
can observe A updated and B stale, which is exactly the kind of inconsistency
locking exists to prevent, and stitching two CAS operations together with
ad hoc logic is a well documented source of subtle bugs, not a substitute for
a lock or a transactional structure.

Do not reach for it when the recompute-and-retry cost is expensive. If
producing the new value from the old one involves an allocation, a system
call, an expensive computation, or any side effect, a lost race means that
work was wasted and has to be redone, possibly forever under sustained
contention. The pattern is a poor fit whenever "compute the candidate new
value" is not cheap and pure.

Do not reach for it under expected high contention on a single location by
many threads at once, for example a global counter incremented by every
request in a very high throughput server. In that regime, a sharded counter,
N independent counters, one per core or per thread, summed on read, or a
batching approach that reduces the number of CAS attempts per unit of work
outperforms a single hot CAS loop by a wide margin, because the underlying
hardware cost is dominated by cache-line ping-pong, not by instruction count.

Do not reach for it when the ABA problem, described in dimension 11, applies
to your data structure and you have not put a mitigation in place. A naive
CAS loop on a pointer that can be freed and reused is a correctness bug
waiting to happen, not a performance optimization.

Do not reach for it as a default replacement for a mutex in ordinary
application code with no measured contention problem. The correctness burden
and the readability cost are real, and paying them without a measured
performance need is a net loss.

## 5. Structure

The pattern has three participants.

The Shared Location is the single word, pointer, or reference the loop
protects, an integer, a pointer to a linked list node, a reference to an
immutable snapshot object. It is read and written exclusively through atomic
operations, never through an ordinary load or store, because a plain store
racing with the CAS instruction breaks the guarantee the whole pattern
depends on.

The Read-Compute-Swap Loop is the calling thread's control flow. Read the
current value of the Shared Location, compute a candidate new value as a pure
function of the value just read, attempt to atomically swap the location from
the read value to the candidate, and if the swap fails because another thread
changed the location in the meantime, discard the candidate and start over
from the read.

The Compare-and-Swap Primitive is the hardware or library-provided atomic
instruction that performs the read-verify-write step as a single indivisible
operation. It compares the current value at the location to an expected
value, and only if they match does it store the new value, returning whether
the swap happened. This primitive is what the Java Memory Model calls
compareAndSet, what Rust calls compare_exchange, what Go calls
CompareAndSwap, what .NET calls Interlocked.CompareExchange, and what x86 and
IBM System/370 call, respectively, CMPXCHG and CS.

## 6. ASCII structure diagram

```
+----------------------------------------------------------+
|                    Read-Compute-Swap Loop                |
|                     (runs on each thread)                |
|                                                            |
|   loop                                                    |
|     1. old <- atomic_load(SharedLocation)  --------+      |
|                                                     |      |
|     2. candidate <- f(old)   (pure function)        |      |
|                                                     |      |
|     3. ok <- CAS(SharedLocation, old, candidate) ---+      |
|                                                            |
|     4. if ok, return candidate                            |
|        else,  goto loop  (retry with fresh read)          |
+----------------------------------------------------------+
                          |
                          v
              +-----------------------+
              |    Shared Location     |
              |  (single word/pointer) |
              |                        |
              |   value = T             |
              +-----------------------+
                          ^
                          |
        (other threads run the same loop concurrently,
         each racing to CAS the same location)

              +-----------------------+
              |  Compare-and-Swap      |
              |  Primitive (hardware)  |
              |                        |
              |  atomically             |
              |  if *loc == expected    |
              |     *loc = new          |
              |     return true         |
              |  else                   |
              |     return false        |
              +-----------------------+
```

## 7. Dynamics

The interesting dynamics happen when two threads race for the same location.
The following sequence shows Thread A winning and Thread B losing then
retrying, which is the normal, expected case the pattern is built for.

```
Thread A                 Shared Location            Thread B
--------                 ---------------             --------
                              value = 10

read old_A = 10
                                                       read old_B = 10

compute new_A = 11
                                                       compute new_B = 11

CAS(loc, 10, 11)
   compare 10 == 10  -> match
   store 11
   return true
                              value = 11
return 11 (success)
                                                       CAS(loc, 10, 11)
                                                          compare 10 == 11
                                                             -> no match
                                                          return false
                                                       (loss, retry)

                                                       read old_B2 = 11

                                                       compute new_B2 = 12

                                                       CAS(loc, 11, 12)
                                                          compare 11 == 11
                                                             -> match
                                                          store 12
                                                          return true
                              value = 12
                                                       return 12 (success)
```

Note the key property this diagram is meant to make visible. Thread B did not
overwrite Thread A's update. Its first CAS attempt failed precisely because
the location had moved out from under it, and the loop's response to a
failure is always to re-read the current value and recompute, never to retry
the stale candidate. This is the mechanism that makes the pattern correct
without a lock. Mutual exclusion is enforced not by keeping threads out of a
critical section, but by guaranteeing that only one thread's atomic write can
ever land on a value that has not already moved.

## 8. Implementation variants

Strong compare-and-swap versus weak compare-and-swap. Some platforms and
languages expose two forms. Strong compare-and-swap guarantees that if the
current value matches the expected value, the swap succeeds, full stop. Weak
compare-and-swap, exposed in Rust as `compare_exchange_weak` and underneath
C++'s `compare_exchange_weak`, is permitted to fail spuriously even when the
comparison would have succeeded, on platforms that implement CAS as a
load-linked or store-conditional pair, most notably ARM and RISC-V, where an
intervening event, even an unrelated cache eviction, can cause the
store-conditional to fail without any other thread having touched the
location. The weak form exists because it can be implemented more cheaply on
those platforms, and the Rust standard library documents that "a
compare_exchange or compare_exchange_weak that does not succeed is not
considered a write", meaning a spurious failure has no observable side effect
beyond the retry it causes (Rust standard library, `std::sync::atomic`,
verified 2026-08-02, https://doc.rust-lang.org/std/sync/atomic/index.html).
Weak CAS is only safe to use inside a retry loop, exactly this pattern, never
as a one-shot check, precisely because it can lie about failure.

Bounded backoff. Under measured heavy contention, a plain tight retry loop
causes every losing thread to immediately re-attempt, which maximizes
cache-line traffic exactly when it is least helpful. A bounded exponential
backoff between retries, sometimes with a small random jitter, spreads out
the retries in time and measurably improves aggregate throughput on real
multi-core hardware, at the cost of added latency for individual operations
and added implementation complexity, particularly around choosing sane
minimum and maximum backoff bounds.

Value-based CAS versus pointer-based CAS on an immutable snapshot. When the
state that must change atomically is more than one field, the common
implementation move is to represent that state as an immutable record, hold a
single pointer or reference to the current record, and CAS the pointer
itself rather than any individual field. This is the technique behind Java's
`AtomicReference` combined with an immutable value class, and it is the
bridge to the Immutable Object pattern discussed in dimension 13.

Read-modify-write helper methods that hide the loop. Most standard libraries
now ship a helper that performs the entire read-compute-swap loop internally
so application code never writes the loop by hand. Java's
`AtomicLong.updateAndGet(LongUnaryOperator)`, which documents that the
supplied function "should be side-effect-free, since it may be re-applied
when attempted updates fail due to contention among threads" (Oracle, Java
SE 8 API documentation, `java.util.concurrent.atomic.AtomicLong`, verified
2026-08-02). Rust's `AtomicUsize::fetch_update`. Go's pattern of wrapping
`CompareAndSwap` in a small helper function, since the standard library does
not ship a generic update-with-function helper. These variants trade a
slightly less flexible API surface for eliminating the most common class of
loop-writing bugs, an incorrectly placed re-read or a candidate computed from
a stale snapshot.

Double-width and tagged compare-and-swap for the ABA problem. Some
architectures, including x86-64 with `CMPXCHG16B`, support a double-width
compare-and-swap that atomically compares and swaps two adjacent machine
words at once. The common use is to pair a pointer with a version counter in
the same double word, so that even if a pointer value is reused after being
freed and reallocated, the paired counter has moved on and the CAS correctly
fails. Java exposes the same idea in software with `AtomicStampedReference`
and `AtomicMarkableReference`, which pair a reference with an integer stamp
or a boolean mark to give lock-free algorithms a way to detect that a
location has changed and changed back.

## 9. Known production uses

The Linux kernel's atomic integer API exposes `atomic_cmpxchg` as a
first-class primitive, documented in the kernel's own atomic operations
documentation, which states the signature `int atomic_cmpxchg(atomic_t *ptr,
int old, int new);` and describes the related `atomic_try_cmpxchg` variant as
generating "more compact code" for the common pattern of looping on failure
(Linux kernel documentation, `Documentation/atomic_t.txt`, verified
2026-08-02, https://www.kernel.org/doc/Documentation/atomic_t.txt). This
primitive underlies reference counting and lock-free data structures used
throughout the kernel's core subsystems.

Java's `java.util.concurrent.atomic` package, part of the standard library
since Java 5 as JSR 166, ships `AtomicInteger`, `AtomicLong`, and
`AtomicReference`, each built around a compare-and-set primitive. The
package's own documentation states plainly that "Atomic classes are designed
primarily as building blocks for implementing non-blocking data structures
and related infrastructure classes", and separately warns that
"compareAndSet is not a general replacement for locking. It applies only when
critical updates for an object are confined to a single variable" (Oracle,
Java SE 8 API documentation, `java.util.concurrent.atomic` package summary,
verified 2026-08-02). These classes are the building blocks the standard
`ConcurrentHashMap` and `ConcurrentLinkedQueue` implementations are written
on top of.

Go's `sync/atomic` package ships both the legacy pointer-based
`CompareAndSwapInt64(addr *int64, old, new int64) (swapped bool)` and, since
Go 1.19, the type-safe method `(*Int64).CompareAndSwap(old, new int64)
(swapped bool)`, with the package documentation recommending the newer
type-safe form because it is "more ergonomic and less error-prone" than the
pointer form, particularly on 32-bit platforms where alignment bugs with the
older API were a recurring source of production crashes (Go standard
library documentation, `sync/atomic`, verified 2026-08-02,
https://pkg.go.dev/sync/atomic).

The .NET runtime ships `System.Threading.Interlocked.CompareExchange` as
part of the base class library, documented in current Microsoft Learn
reference documentation covering every .NET version from Framework 1.1
through .NET 10, confirming it as a long-standing, actively maintained part
of the platform rather than a legacy artifact (Microsoft Learn,
`Interlocked.CompareExchange` method reference, verified 2026-08-02,
https://learn.microsoft.com/en-us/dotnet/api/system.threading.interlocked.compareexchange).
It underlies the .NET runtime's own lock-free reference counting and is the
documented recommended primitive for implementing custom lock-free
structures in application code.

## 10. Consequences

### Positive

No thread can hold the shared location hostage. Because there is no lock, a
thread that is preempted, descheduled, or even killed mid-operation cannot
prevent any other thread from making progress on the same location. This is
a strictly stronger liveness guarantee than a mutex can offer.

Uncontended operations are extremely cheap. With no contention, a CAS loop
executes exactly one atomic instruction and returns, with no system call, no
kernel involvement, and usually no memory allocation, which is meaningfully
faster than acquiring and releasing even an uncontended user-space mutex in
most runtime implementations.

It composes cleanly with immutable data. Because the natural extension of the
pattern is to CAS a pointer to an immutable snapshot, it pushes designs
toward immutable value objects, which independently reduces the surface area
for other classes of concurrency bugs, described further under dimension 13.

It avoids priority inversion and deadlock by construction. There is no lock
to be held across a preemption boundary and no lock ordering to get wrong,
so two of the most common classes of concurrency bugs, priority inversion and
lock-ordering deadlock, cannot occur in code built purely from CAS loops.

### Negative

It introduces the ABA problem as a new correctness hazard that locking does
not have, described in detail under dimension 11, and mitigating it correctly
requires either a versioned or tagged reference, hazard pointers, or a
garbage-collected runtime that never actually frees and reuses memory while a
reference to it might still be live.

It degrades poorly under sustained high contention on one location, because
every failed attempt still costs a full cache-coherence round trip on modern
hardware, and a plain retry loop with no backoff can spend more total CPU
time on failed attempts than a mutex-protected version would spend on the
underlying work.

It is markedly harder to write correctly than lock-protected code, because
the reader must reason about every possible interleaving at every point in
the loop, and a subtle mistake, most commonly recomputing the candidate from
a stale read instead of the freshly re-read value, produces a bug that is
silent under light testing and only appears under real contention in
production.

It weakens the guarantee from wait-free to merely lock-free unless
additional work is done, meaning an individual thread's operation can in
theory be starved indefinitely by a stream of successful competitors, even
though the system as a whole always makes progress.

## 11. Failure modes and misuse

### The ABA problem

Symptom. A lock-free stack or queue occasionally corrupts its internal
structure under heavy concurrent push and pop traffic, producing a cycle in
the linked structure, a lost node, or a use-after-free crash, and the failure
is close to impossible to reproduce outside of production load.

Cause. Thread A reads the shared pointer, sees it points at node X, and
is then preempted before it can CAS. While A is suspended, Thread B pops X
off the structure, frees it, and a subsequent allocation happens to reuse the
exact same memory address for a brand new node, which Thread B then pushes
back onto the structure. When Thread A resumes, its stale read still says
the pointer was X, and because the pointer's bit pattern is once again
literally the address of X, the CAS succeeds, even though the actual state of
the world changed twice in between and A's stale assumptions about what X's
neighbors are no longer hold. This is the ABA problem. The value went from A
to B and back to A, and a bare CAS cannot tell that round trip apart from
nothing having happened at all.

Fix. Pair the pointer with a monotonically increasing version counter and
CAS both together with a double-width compare-and-swap, or use hazard
pointers or epoch-based reclamation to guarantee a node cannot be freed and
reused while any thread might still hold a reference to it, or, in managed
runtimes with a real garbage collector such as the JVM or the CLR, rely on
the fact that a live reference on any thread's stack prevents the collector
from freeing the object at all, which removes the reuse half of the ABA
problem by construction, though it does not remove the logical version of the
problem where the value itself legitimately returns to an earlier state.

### Livelock under sustained symmetric contention

Symptom. Under a synthetic benchmark or a real production hot spot, CPU
usage on the cores contending for one location spikes, but the observed
throughput of successful operations on that location barely moves or
actually falls as more threads are added.

Cause. A tight retry loop with no backoff means every losing thread
immediately re-reads and re-attempts, so as contention rises, an increasing
fraction of total CPU time goes into failed CAS attempts and the
cache-coherence traffic they generate, rather than into useful work.

Fix. Add bounded exponential backoff with jitter between retries, or
restructure the hot location as a sharded set of counters combined only on
read, or batch multiple logical updates into a single CAS attempt where the
access pattern allows it.

### Recomputing the candidate from a stale read

Symptom. A lock-free counter or accumulator occasionally under-counts
compared to the true number of increments performed, and the discrepancy
only appears under real concurrent load, never in a single-threaded test.

Cause. The loop body reads the old value once, computes the new value,
and on CAS failure retries the CAS itself with the same stale candidate
instead of going back to step one and re-reading the current value first.
This is a bug in how the loop is written, not a flaw in the primitive.

Fix. Structure the loop so that failure always jumps back to the read
step, never directly to the CAS step, and prefer the standard library's
update-with-function helpers, such as Java's `updateAndGet` or Rust's
`fetch_update`, which enforce this structure by construction and cannot be
written incorrectly in this specific way.

### Treating compare-and-swap as a substitute for a multi-location transaction

Symptom. Two related pieces of shared state are individually consistent
when inspected one at a time, but a reader that reads both in sequence
occasionally observes an impossible combination, for example a linked list
whose length counter and whose actual node chain disagree.

Cause. Each location is protected by its own independent CAS loop, but
there is a window between the two CAS operations during which another thread
can observe or modify one location without the other having caught up, which
is precisely the kind of cross-location atomicity a single CAS cannot
provide.

Fix. Fold the related fields into a single immutable snapshot object and
CAS one pointer to that snapshot, as described in dimension 8, or move to an
actual lock or a software transactional memory system if the update genuinely
needs to span independent, unrelated locations.

## 12. Trade-off matrix

| Force | Compare-and-Swap Loop | Mutex / Lock | Read-Copy-Update |
|---|---|---|---|
| Uncontended latency | Very low, single instruction, no kernel call | Low but higher than CAS, user-space fast path plus occasional kernel call | Very low for readers, comparable to CAS for the writer's swap |
| Heavy write contention throughput | Degrades due to cache-line ping-pong on retries | Degrades more gracefully, threads queue and each eventually runs | Not applicable in the same sense, writers are usually serialized by a separate lock, only readers are lock-free |
| Progress guarantee | Lock-free, system-wide progress, not wait-free without extra work | None, a preempted lock holder blocks all waiters | Readers are wait-free, writers are serialized |
| Correctness hazard unique to the pattern | ABA problem on reused pointers | Deadlock from lock ordering, priority inversion | Stale reads during the grace period before reclamation |
| Multi-location atomicity | Not directly, requires folding into one pointer | Yes, a single critical section can span any number of locations | Yes for the writer side, via a single pointer swap |
| Code readability and review cost | High, every interleaving must be reasoned about | Lower, critical section boundaries are explicit | High, comparable to CAS plus reclamation reasoning |
| Best fit | Single word or single pointer, light to moderate contention | Multi-location critical sections, contention of any level | Read-mostly workloads with rare writers, especially in kernels |

## 13. Related and incompatible patterns

Immutable Object is the pattern this one leans on most heavily whenever the
state to update is more than one field. Because a CAS can only atomically
swap a single word or pointer, the standard way to protect a multi-field
aggregate lock-free is to make the aggregate an Immutable Object, hold a
single atomic reference to the current instance, and CAS that reference from
the old instance to a freshly constructed new instance. Every reader that
already holds a reference to the old instance continues to see a fully
consistent, unchanging view of it, because it is immutable, which is exactly
the property that makes the composition safe.

Read-Copy-Update generalizes this pattern for the specific case where reads
vastly outnumber writes and readers must never be blocked, even briefly, by a
writer. Where a CAS loop makes every operation, read and write alike, go
through the atomic primitive, RCU lets readers proceed with an ordinary,
unsynchronized pointer dereference, and confines the compare-and-swap style
atomic pointer update to the writer side alone, deferring the actual
reclamation of old memory until a grace period during which no reader could
still be using it has passed. A CAS loop is in a sense the primitive
building block that an RCU writer uses to publish its new version.

Double-Checked Locking is a pattern that historically tried to get some of
the same "avoid the lock in the common case" benefit as a CAS loop, but does
so by checking a condition without a lock, then acquiring a lock only if the
check suggests work is needed, then checking again under the lock before
doing the work. It is a different mechanism, still lock-based on the slow
path, and it is notorious for being broken on weak memory models unless the
checked variable is declared volatile or atomic, which is itself a
smaller-scale application of the same memory-ordering discipline this
pattern requires throughout.

Thread-Safe Interface is the umbrella pattern that says a class's public
methods should each individually be safe to call from multiple threads
without external synchronization. A class implemented internally with a
compare-and-swap loop, exposing only atomic increment, atomic compare-and-set,
or similar operations as its public surface, is one concrete way of
satisfying a Thread-Safe Interface, and the two patterns compose directly.
The CAS loop is the mechanism, Thread-Safe Interface is the contract the
mechanism is used to fulfill.

There is no pattern in this catalog that a compare-and-swap loop is
inherently incompatible with in the sense of active conflict, but it does not
compose usefully with any pattern whose synchronization story assumes a
critical section can span multiple independent memory locations without
first collapsing them into a single atomically-swapped reference, which is
the same non-applicability point made in dimension 4.

## 14. Refactoring path in and out

### Introducing a compare-and-swap loop into lock-protected code

Start by confirming the critical section genuinely touches a single word or
a single pointer, or can be restructured to do so by folding multiple fields
into one immutable snapshot object, since attempting this refactor on a
critical section that touches multiple independent locations will silently
introduce the multi-location atomicity bug described in dimension 11.

Replace the shared field's plain type with the language's atomic wrapper
type. `AtomicInteger` or `AtomicReference` in Java, `AtomicI64` or
`AtomicPtr` in Rust, `atomic.Int64` or `atomic.Pointer[T]` in Go,
`Interlocked`-compatible storage in .NET. This step alone, with every access
still going through explicit lock acquisition, is a safe intermediate state
that changes nothing observable and can be committed and tested on its own.

Replace the lock-acquire, read, modify, write, lock-release sequence with the
read-compute-swap loop, preferring the standard library's built-in
update-with-function helper where one exists, since it removes the most
common hand-written loop bug by construction.

Remove the now-unused lock only after the CAS-based version has been through
concurrent stress testing under real contention, described in dimension 15,
because a lock that appears unnecessary in review but is quietly still needed
to protect a second field the refactor missed is exactly the kind of bug
this migration is prone to introducing.

### Removing a compare-and-swap loop when it no longer earns its place

The signal that a CAS loop should come back out is usually one of two things.
Either profiling shows the location is under contention high enough that the
retry storm costs more CPU than a mutex-protected version would, or the
critical section has grown, over time, to touch more than the single field
or pointer it started with, and the team keeps working around that growth
with increasingly convoluted multi-CAS choreography instead of admitting the
operation is no longer a single-location update.

In either case, the removal path is the mirror of the introduction path.
Reintroduce an explicit lock around the now-plain field access, verify with
the same concurrent stress tests that correctness is unchanged, and only then
delete the atomic wrapper type. Do this incrementally, one location at a
time, never as a single large diff across a whole subsystem, so that a
regression can be bisected to a specific field's reversion rather than to an
entire refactor.

## 15. Testing and verification

Unit tests written on a single thread cannot demonstrate the property this
pattern exists to provide, because they never exercise the race window
between the read and the swap. A single-threaded test suite passing is
evidence the sequential logic of the candidate computation is correct, and
no evidence at all about the concurrency correctness of the loop.

Concurrent stress testing is the primary verification technique. Spin up a
number of threads at least equal to, and ideally several times, the number
of available hardware cores, have them all hammer the same shared location
with a known, checkable invariant, for example N threads each incrementing a
shared counter exactly M times should leave the counter at exactly N times M
with no lost updates, and run this under a loop for many iterations, since a
single run of a race-dependent test can easily pass by luck.

Deliberately introducing artificial delays or yields inside the window
between the read and the CAS, gated behind a test-only flag, widens the race
window and makes bugs that would otherwise require millions of iterations to
surface reproducible in dozens. This technique is sometimes called race
amplification, and it trades an intrusion into production code, guarded so
it compiles to nothing in a release build, for a large increase in the odds a
real bug is caught before it ships.

Tools that detect data races by instrumenting memory accesses, such as the
Go race detector invoked with `go test -race`, or ThreadSanitizer for C, C++,
and Rust, catch a distinct but related class of bug. An ordinary,
unsynchronized read or write to memory that a CAS loop should have been the
exclusive access path for, but which some other part of the codebase
accidentally touched directly. Running these detectors against the
concurrent stress tests described above is standard practice for any code
built on this pattern, and a clean run under a race detector is a necessary,
though not sufficient, condition for correctness, since a race detector
cannot itself catch a logical ABA bug where every individual access is
properly atomic but the sequence of values observed is still wrong.

What becomes easier to test as a direct consequence of the pattern is
composability with formal or semi-formal model checking on small, isolated
snippets of the loop logic, since the loop's entire externally observable
behavior can be expressed as a small state machine over the shared
location's possible values, which is exactly the kind of artifact tools like
TLA+ are built to check exhaustively for a bounded number of interleaving
threads.

## 16. Observability signals

The single most useful metric to expose from a production CAS loop is the
retry count per successful operation, either as a running counter incremented
on every failed CAS attempt or as a histogram of attempts-to-success per
call. A healthy instance of this pattern shows a retry count that is almost
always zero or one, with an occasional two or three under momentary
contention. A failing or degrading instance shows the retry count climbing
into double or triple digits under load, which is the direct, quantitative
signal that the location has become a contention hot spot and the pattern is
starting to pay its worst-case cost rather than its best-case one.

Wall-clock latency of the operation as a whole, not just of the successful
CAS instruction, should be tracked separately from the retry count, because
the two together distinguish two different failure shapes. High retry count
with low latency means the retries themselves are cheap and the hardware is
absorbing the contention fine, while high retry count with rising latency
means something else is making each retry more expensive, commonly a
candidate computation that got more expensive than it was designed to be, or
backoff parameters that are too high for the actual contention level.

CPU utilization on the specific cores contending for the location, visible
through per-core profiling rather than aggregate system CPU, is the signal
that distinguishes ordinary useful work from a livelock condition described
in dimension 11. A core pegged at high utilization while the retry-count
metric shows no corresponding increase in successful operations is the
signature of a retry storm burning cycles without making progress.

For any implementation that pairs a pointer with a version counter or a
hazard pointer scheme to mitigate the ABA problem, the count of reclaimed
versus retired-but-not-yet-reclaimed nodes is a signal worth exposing, since
a steadily growing gap between the two is evidence that reclamation is
falling behind allocation, which under sustained load eventually shows up as
unbounded memory growth even though the algorithm itself is logically
correct.

## 17. Security and privacy implications

Compare-and-swap loops have no direct data confidentiality implication in
themselves. The value stored at the shared location carries whatever
sensitivity the application already assigns it, and the atomic operation
does not change who can observe or infer that value.

There is a narrow but real timing side-channel consideration worth naming
plainly rather than overstating. Because a CAS loop's execution time varies
with the number of retries, and the number of retries can depend on the
value of contended state, an attacker who can measure operation latency with
enough precision and who has some influence over the contention pattern
could in principle infer coarse information about how much contention a
shared resource is under, which in specific adversarial contexts, such as a
shared cache line used as part of a cryptographic key schedule under
concurrent access, is the same general class of hazard that timing-based
side-channel research on cache and memory-bus contention has documented more
broadly. This is a second-order concern relevant mainly to code implementing
cryptographic primitives or multi-tenant isolation boundaries, not to
ordinary application-level counters and caches, and where it is relevant the
established mitigation is constant-time coding discipline applied to the
whole critical operation, not anything specific to the compare-and-swap
primitive itself.

The ABA problem, described under dimension 11, has a security-adjacent
failure mode worth naming. A use-after-free bug caused by an ABA race in a
memory allocator or a lock-free data structure is, in unmanaged languages
such as C, C++, and unsafe Rust, the exact same class of memory-corruption
bug that is a classic target for exploitation, since a reused, mismanaged
pointer is precisely the primitive many memory-safety exploits are built on.
In a managed, garbage-collected runtime such as the JVM or the CLR, this
specific manifestation is closed off by the collector's guarantee that a
live reference prevents reuse, but the underlying logical ABA problem, where
the observed value returns to an earlier state without the code correctly
accounting for it, remains a correctness hazard regardless of memory safety.

## 18. References

1. Wikipedia contributors, "Compare-and-swap", Wikipedia, verified
   2026-08-02, https://en.wikipedia.org/wiki/Compare-and-swap
2. Herlihy, Maurice, "Wait-Free Synchronization", ACM Transactions on
   Programming Languages and Systems, Vol. 13, No. 1, January 1991, as
   summarized and cited on the Wikipedia "Compare-and-swap" page, verified
   2026-08-02, https://en.wikipedia.org/wiki/Compare-and-swap
3. Rust Project, `std::sync::atomic` module documentation, The Rust Standard
   Library, verified 2026-08-02,
   https://doc.rust-lang.org/std/sync/atomic/index.html
4. Oracle, `java.util.concurrent.atomic.AtomicLong` class reference, Java SE
   8 API Specification, verified 2026-08-02,
   https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/atomic/AtomicLong.html
5. Oracle, `java.util.concurrent.atomic` package summary, Java SE 8 API
   Specification, verified 2026-08-02,
   https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/atomic/package-summary.html
6. Go Project, `sync/atomic` package documentation, verified 2026-08-02,
   https://pkg.go.dev/sync/atomic
7. Microsoft, `Interlocked.CompareExchange` method reference, .NET API
   documentation on Microsoft Learn, verified 2026-08-02,
   https://learn.microsoft.com/en-us/dotnet/api/system.threading.interlocked.compareexchange
8. The Linux Kernel documentation, `Documentation/atomic_t.txt`, verified
   2026-08-02, https://www.kernel.org/doc/Documentation/atomic_t.txt
9. Mozilla Developer Network, `Atomics.compareExchange()` reference,
   JavaScript documentation, verified 2026-08-02,
   https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Atomics/compareExchange
10. Python Software Foundation, `multiprocessing.shared_memory` module
    documentation, Python 3 Standard Library, verified 2026-08-02,
    https://docs.python.org/3/library/multiprocessing.shared_memory.html

## Code examples

The pattern is demonstrated below with a lock-free counter increment, the
simplest possible instance of the read-compute-swap loop, in Rust, Go, and
Java, and with the JavaScript/TypeScript `Atomics.compareExchange` API shown
separately since it targets `SharedArrayBuffer`-backed typed arrays rather
than a boxed atomic type and cannot be exercised as ordinary single-threaded
Node.js code the way the other three can. Swift is omitted from the runnable
set because Swift's Concurrency-era standard library does not expose a
public, stable, portable compare-and-swap API equivalent to the other four
languages at the time of writing. Swift code built on Apple platforms
usually reaches for the C `stdatomic.h` primitives via an interop shim
instead, which is a build-system-specific setup not reproducible as a plain
`swiftc` single-file sample, so it is described rather than shown.

### Rust

Compiled and run with `rustc` on this machine.

```rust
use std::sync::atomic::{AtomicI64, Ordering};
use std::sync::Arc;
use std::thread;

fn increment_with_cas(counter: &AtomicI64) -> i64 {
    loop {
        let old = counter.load(Ordering::Acquire);
        let new = old + 1;
        match counter.compare_exchange_weak(
            old,
            new,
            Ordering::AcqRel,
            Ordering::Acquire,
        ) {
            Ok(_) => return new,
            Err(_) => continue,
        }
    }
}

fn main() {
    let counter = Arc::new(AtomicI64::new(0));
    let threads: Vec<_> = (0..8)
        .map(|_| {
            let counter = Arc::clone(&counter);
            thread::spawn(move || {
                for _ in 0..10_000 {
                    increment_with_cas(&counter);
                }
            })
        })
        .collect();

    for t in threads {
        t.join().unwrap();
    }

    let final_value = counter.load(Ordering::Acquire);
    println!("final counter value, {}", final_value);
    assert_eq!(final_value, 80_000);
}
```

### Go

Compiled and run with `go run` on this machine.

```go
package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

func incrementWithCAS(counter *atomic.Int64) int64 {
	for {
		old := counter.Load()
		next := old + 1
		if counter.CompareAndSwap(old, next) {
			return next
		}
	}
}

func main() {
	var counter atomic.Int64
	var wg sync.WaitGroup

	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := 0; j < 10000; j++ {
				incrementWithCAS(&counter)
			}
		}()
	}

	wg.Wait()
	finalValue := counter.Load()
	fmt.Printf("final counter value, %d\n", finalValue)
	if finalValue != 80000 {
		panic("lost update detected")
	}
}
```

### Java

Written to compile cleanly under `javac` and match verified
`java.util.concurrent.atomic.AtomicLong` semantics (dimension 9). This
machine has `javac` on the path but no installed Java Runtime Environment to
execute the compiled class, so the compile-and-run step could not be
completed here and is reported as such rather than implied.

```java
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.CountDownLatch;

public class CasCounter {

    static long incrementWithCas(AtomicLong counter) {
        while (true) {
            long old = counter.get();
            long next = old + 1;
            if (counter.compareAndSet(old, next)) {
                return next;
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        AtomicLong counter = new AtomicLong(0);
        int threadCount = 8;
        int incrementsPerThread = 10_000;
        CountDownLatch latch = new CountDownLatch(threadCount);

        for (int i = 0; i < threadCount; i++) {
            Thread t = new Thread(() -> {
                for (int j = 0; j < incrementsPerThread; j++) {
                    incrementWithCas(counter);
                }
                latch.countDown();
            });
            t.start();
        }

        latch.await();
        long finalValue = counter.get();
        System.out.println("final counter value, " + finalValue);
        if (finalValue != (long) threadCount * incrementsPerThread) {
            throw new IllegalStateException("lost update detected");
        }
    }
}
```

### JavaScript / TypeScript, `Atomics.compareExchange`

Type-checked with `tsc`, shown as a single-threaded demonstration of the
primitive's semantics rather than a multi-threaded run, since exercising it
across real worker threads requires a project-level `SharedArrayBuffer`
transfer setup outside the scope of one file.

```typescript
function incrementWithCas(view: Int32Array, index: number): number {
  while (true) {
    const old = Atomics.load(view, index);
    const next = old + 1;
    const witnessed = Atomics.compareExchange(view, index, old, next);
    if (witnessed === old) {
      return next;
    }
  }
}

const buffer = new SharedArrayBuffer(4);
const counter = new Int32Array(buffer);

for (let i = 0; i < 5; i++) {
  const result = incrementWithCas(counter, 0);
  console.log("incremented to " + result);
}

if (Atomics.load(counter, 0) !== 5) {
  throw new Error("lost update detected");
}
```
