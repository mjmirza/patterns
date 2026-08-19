---
name: Monitor Object
slug: monitor-object
family: 09-concurrency
category: Concurrency
aliases: [Monitor, Synchronized Object, Serialized Object]
first_described: "Hoare 1974 (concept); Schmidt, Stal, Rohnert, Buschmann 2000 (pattern form)"
maturity: canonical
related: [active-object, half-sync-half-async, guarded-suspension, thread-safe-interface, producer-consumer]
incompatible_with: [active-object]
verified: 2026-08-13
---

## 1. Name, aliases, and lineage

The canonical name is Monitor Object. It is also called simply a Monitor, and
in some codebases a Synchronized Object or a Serialized Object, because every
method call on the object is serialized with respect to every other method
call on the same object. The idea predates the pattern-catalog name by two
decades. C.A.R. Hoare published "Monitors, an Operating System Structuring
Concept" in Communications of the ACM, volume 17, issue 10, October 1974,
pages 549 to 557, which formalized the monitor as a language construct that
bundles shared state, the procedures that operate on it, and the
synchronization that protects it into a single module, with condition
variables as the mechanism for a thread to wait for state it cannot yet act
on. The ACM Digital Library entry for the paper, at
https://dl.acm.org/doi/10.1145/355620.361161, verified 2026-08-13, confirms
the title, author, venue, and pagination. Hoare credits Per Brinch Hansen's
earlier work on the Concurrent Pascal language and Edsger Dijkstra's earlier
proposal of the "secretary" concept as the roots of the idea, a lineage that
Hoare states explicitly in the paper's introduction.

The pattern-catalog form used in this entry, with the six named participants
and the explicit distinction between a monitor lock and monitor condition
variables, is documented as one of the twelve patterns in
*Pattern-Oriented Software Architecture, Volume 2, Patterns for Concurrent and
Networked Objects* by Douglas C. Schmidt, Michael Stal, Hans Rohnert, and
Frank Buschmann, published by John Wiley and Sons in 2000, chapter 5. POSA2 is
also the source cited by this same pattern family's Active Object entry, and
the two entries are deliberately paired, because POSA2 presents Monitor Object
as the pattern Active Object is built from. Java's own language designers cite
Hoare's monitor concept directly as the model for the `synchronized` keyword
and the `wait`, `notify`, and `notifyAll` methods on `java.lang.Object`, this
is documented in the Java Language Specification, section 17.1, "Synchro-
nization," reachable at
https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html, verified
2026-08-13, which states that "every object in Java is associated with a
monitor" and describes the lock-acquire, lock-release, and wait-set semantics
in monitor terms.

## 2. Problem and context

An object holds mutable state that more than one thread will call methods on
concurrently. Unlike Active Object, the calling thread here is not trying to
avoid blocking, it genuinely wants a synchronous answer before it continues.
The problem is narrower than Active Object's problem, and that narrowness is
the whole point. how do you make an object's methods individually atomic with
respect to each other, and let a thread that calls a method it cannot proceed
with yet wait, efficiently, without spinning, until some other thread changes
the state enough to let it proceed, then wake it up.

The concrete situation is a bounded queue shared by producer and consumer
threads. `enqueue(item)` must not run at the same instant as `dequeue()`,
because both mutate the same backing array and the same size counter, and an
interleaved read-modify-write on the counter corrupts it. That much is solved
by a plain mutex. The harder half is what `dequeue()` does when the queue is
empty. It cannot return garbage, and it cannot busy-loop calling `dequeue()`
again immediately, because that burns a full CPU core polling a lock that
another thread is not currently trying to release. It needs to sleep until an
`enqueue` happens, and it needs to sleep while holding no lock, so that the
producer thread which is about to call `enqueue` is not blocked behind a
sleeping consumer that is still holding the queue's own mutex. The Monitor
Object pattern is the answer to exactly that. state, guard, and
condition-based wait bundled into one object, so that every caller sees a
synchronous, atomic method, and every caller that must wait does so on a
condition variable that releases the guard while asleep and reacquires it on
wake.

The context this pattern belongs in is single-process, shared-memory
concurrency where the calling thread wants synchronous results, not
fire-and-forget dispatch. That distinguishes it from Active Object, which
targets exactly the same shared-state problem but for callers that want to
continue without blocking. Both patterns solve concurrent access to a
stateful object. They differ on what the caller's thread does while the
object's invariant is protected.

## 3. Forces

Correctness under interleaving versus throughput. A monitor holds one lock for
the whole object, so two calls to different methods on the same instance from
two different threads still serialize against each other even when they touch
disjoint fields. This is the simplest possible correctness argument, and it
is also the pattern's biggest throughput tax under contention, because a
monitor with several logically independent operations turns them into one
serialized stream the moment more than one thread calls in.

Waiting efficiently versus waiting correctly. A condition variable lets a
thread sleep without holding the CPU, but only if the wait, the wake, and the
re-check of the condition are done in the exact sequence the monitor
discipline requires, reacquire the lock atomically with waking up, and
re-check the predicate in a loop rather than an if, because a woken thread has
no guarantee it is the only one that was woken, and no guarantee the state is
still what the waking thread thought it was at signal time. Getting this
sequence slightly wrong produces a program that is correct in testing and
wrong under load, which is the pattern's sharpest edge for someone new to it.

Caller latency versus object simplicity. Because every method call blocks the
caller until the monitor's lock is free, and can block further if the method
itself waits on a condition, a monitor pushes all latency onto the calling
thread's stack. That is a deliberate trade against Active Object, which moves
the same latency into a queue and gives the caller a future instead. Monitor
Object accepts caller-side blocking in exchange for a simpler mental model,
no scheduler, no queue, no separate worker thread, just a lock and some
condition variables sitting inside the object itself.

Language support versus portability. Java and C# bake the monitor concept
directly into every object, via `synchronized` and `Monitor.Enter` respect-
ively, which makes the pattern nearly invisible as a pattern in those
languages. Languages without built-in per-object monitors, such as Go, Rust,
and C, require the pattern to be assembled explicitly from a mutex and one or
more condition variables, which makes the structure visible but also makes it
possible to get the assembly wrong.

## 4. Applicability and non-applicability

Reach for a Monitor Object when a single object holds mutable state accessed
by multiple threads, the calling threads want synchronous return values or
side effects before they continue, at least one operation on the object needs
to wait for a state change that another operation produces, for example
bounded-buffer producer and consumer, a connection pool checkout that waits
for a free connection, or a barrier that releases all waiters once a count is
reached, and the object's invariant can be expressed and checked cheaply
inside the lock, so that holding the lock across the check does not become
the bottleneck.

Do not reach for a Monitor Object when the caller must not block, in which
case Active Object or a lock-free queue handing work to a dedicated thread is
the correct shape, the protected section does real I/O or another
unbounded-duration operation while holding the lock, because every other
caller now waits for that I/O, which converts a synchronization primitive
into an accidental rate limiter. Move the I/O outside the lock and only guard
the state transition. The state is naturally partitionable across many
independent locks, one coarse monitor lock over the whole object then
serializes operations that never needed to serialize against each other, and
sharding into finer-grained locks, or a lock-free structure, gives real
throughput back. The platform has no native thread-blocking primitive at all,
for example a single-threaded JavaScript event loop or a Rust `async`
executor without OS threads, where `wait`/`notify`-style blocking either does
not exist or blocks the wrong thing, an `async` task's cooperative scheduler
rather than an OS thread, and the async-native equivalent, a notify channel
or an async condition variable, is the correct tool. Two or more monitors
must be locked together for a single operation, where a fixed global lock
ordering must be imposed by hand across the whole codebase or the monitors
will eventually deadlock. This is a real cost of using more than one monitor
object in a system and is often the reason a design collapses several
monitors into one.

## 5. Structure

**Synchronized object.** The object whose public interface is the monitor. It
holds the mutable state under protection and exposes the operations callers
invoke. In Java and C#, any ordinary object can play this role because the
language gives every object an intrinsic lock. In Go and Rust the role is
played by a struct that explicitly embeds a mutex.

**Monitor lock.** A single mutual-exclusion lock, owned by the synchronized
object, that every synchronized method acquires on entry and releases on
exit, or, in the explicit-assembly languages, that the object's methods
acquire around every access to the protected state. Exactly one thread holds
the monitor lock at a time.

**Monitor condition (condition variable).** A queue of waiting threads
associated with a specific predicate over the monitor's state, for example
"the queue is not empty" or "the pool has an idle connection." A thread calls
wait on the condition to atomically release the monitor lock and go to sleep.
Another thread calls signal or broadcast on the same condition, after
changing the state that makes the predicate true, to wake one or all waiters,
which then reacquire the monitor lock before returning from wait.

**Synchronized method.** A method on the synchronized object that acquires
the monitor lock for its entire body, so its execution never interleaves with
any other synchronized method's execution on the same object. Some
synchronized methods additionally wait on a monitor condition partway
through, when the state they need is not yet present.

**Client.** The calling thread. It invokes a synchronized method exactly as
it would invoke any ordinary method, with no visible queueing, futures, or
callback registration. It blocks for as long as the monitor lock is held by
another thread, plus however long any condition wait inside the method takes.

**Recursive lock (optional).** Some monitor implementations, including
Java's intrinsic lock and .NET's `Monitor` class, allow the thread that
already holds the monitor lock to reacquire it, incrementing a hold count,
so that one synchronized method can call another synchronized method on the
same object from the same thread without deadlocking against itself. This is
convenient and also a known source of accidental reentrancy bugs, covered in
Dimension 11.

## 6. ASCII structure diagram

```
+-----------------------------------------------------------+
|                    Synchronized Object                    |
|                                                             |
|   +---------------+     guards      +------------------+  |
|   |  Monitor Lock  |<--------------->|  Protected State |  |
|   +---------------+                 +------------------+  |
|          ^                                    ^            |
|          | acquire/release                    | read/write |
|          |                                     |            |
|   +------+-------------------------------------+--------+  |
|   |              Synchronized Method (e.g. enqueue)      |  |
|   |    lock.acquire()                                    |  |
|   |    mutate state                                       |  |
|   |    condition.signal()                                 |  |
|   |    lock.release()                                     |  |
|   +--------------------------------------------------------+  |
|                                                             |
|   +--------------------------------------------------------+  |
|   |              Synchronized Method (e.g. dequeue)       |  |
|   |    lock.acquire()                                     |  |
|   |    while (state not ready): condition.wait(lock)  ----+--+--> Wait Set
|   |    mutate state                                        |  |   (parked
|   |    lock.release()                                      |  |    threads)
|   +---------------------------------------------------------+  |
+-----------------------------------------------------------+
        ^                                              ^
        | synchronous call, blocks until returned       |
        |                                                |
   +---------+                                     +---------+
   | Client A|  (producer thread)                  | Client B|  (consumer
   +---------+                                     +---------+   thread)
```

## 7. Dynamics

The bounded-queue example makes the interleaving concrete. Two threads, a
producer P and a consumer C, share one Monitor Object queue with capacity 1
and it starts empty.

```
Time  Thread   Action
----  ------   ------
t0    C        calls dequeue(); acquires monitor lock
t1    C        checks predicate: queue is empty; true
t2    C        calls wait(monitorLock); lock is released atomically
                as C is added to the wait set; C is now parked, holding
                no lock, consuming no CPU
t3    P        calls enqueue(x); acquires monitor lock (free, since C
                released it in t2)
t4    P        writes x into the queue; queue is no longer empty
t5    P        calls signal(); C is moved from the wait set to the
                lock's contention queue, but C does not run yet,
                because P still holds the lock
t6    P        returns from enqueue(); releases monitor lock
t7    C        wakes, reacquires monitor lock (now free)
t8    C        re-checks predicate: queue is empty; false; exits the
                wait loop
t9    C        reads x, mutates the queue to empty, releases monitor
                lock, returns x to the client of dequeue()
```

The re-check at t8, rather than trusting the wake as proof the predicate now
holds, is the detail every monitor implementation must get right. Between t5
and t7 a third thread could, in a real system with more than one consumer,
have raced C to the lock and drained the item first. Without the re-check, C
would return a stale or corrupted value. This is why the pattern's canonical
form is `while (!predicate) condition.wait(lock);` and never
`if (!predicate) condition.wait(lock);`. POSA2 states this loop-not-if rule
explicitly as part of the Monitor Object implementation guidance, and Java's
own `Object.wait` documentation, at
https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Object.html#wait(),
verified 2026-08-13, states plainly that "a thread can also wake up without
being notified, interrupted, or timing out... it is recommended that
applications programmers... use the wait method only in a loop."

## 8. Implementation variants

**Language-intrinsic monitor.** Java's `synchronized` keyword on a method or
block, paired with `Object.wait`, `notify`, and `notifyAll`, and C#'s
`lock` statement paired with `Monitor.Wait` and `Monitor.Pulse` or
`PulseAll`, both give every object a built-in monitor lock and a single
built-in condition. This is the lowest-ceremony variant, and its main
limitation is exactly that every object has only one condition. A monitor
that needs to distinguish "not full" from "not empty" as two separate wait
predicates cannot do so with the intrinsic lock alone in either language and
must fall back to an explicit `java.util.concurrent.locks.ReentrantLock`
with multiple `Condition` objects, or C#'s explicit multi-condition support
via `System.Threading.Monitor` combined with manual predicate tracking.

**Explicit mutex plus condition variable.** POSIX `pthread_mutex_t` with
`pthread_cond_t`, Rust's `std::sync::{Mutex, Condvar}`, and Go's
`sync.Mutex` with `sync.Cond` all require the author to assemble the monitor
by hand. acquire the mutex, loop on the predicate calling `cond.wait(mutex)`,
mutate state, call `cond.notify`, release the mutex either explicitly or via
a scope guard. This variant is the most portable, the most explicit about
what is happening, and the easiest to get subtly wrong, because there is no
language enforcement that every access to the protected field goes through
the mutex.

**Monitor-with-timeout.** Nearly every real implementation offers a bounded
wait, `wait(long timeoutMillis)` in Java, `Condvar::wait_timeout` in Rust,
`pthread_cond_timedwait` in POSIX, so a caller can give up on a wait after a
deadline rather than block forever if the expected signal never arrives, for
example a connection-pool checkout that should fail fast under sustained
exhaustion rather than hang the caller indefinitely.

**Multiple named conditions on one lock.** `java.util.concurrent.locks
.ReentrantLock` paired with several `Condition` objects created via
`lock.newCondition()`, and POSIX's pattern of one `pthread_mutex_t` guarding
several `pthread_cond_t` instances, both let a monitor separate "readers
should wake" from "writers should wake" without waking every waiter on every
signal, which the single-condition intrinsic-monitor variant cannot express
without extra predicate checks inside every waiter.

**Channel-mediated monitor (Go idiom).** Rather than a `sync.Cond`, an
idiomatic Go monitor is often built from a `sync.Mutex` guarding state plus a
buffered channel of capacity one used purely as a signal, sent to on state
change, received from (non-blockingly, in a `select` with `default`) by a
waiter. This is functionally a monitor condition implemented on top of a
channel rather than `sync.Cond`, and the Go standard library documentation
for `sync.Cond`, at https://pkg.go.dev/sync#Cond, verified 2026-08-13, itself
notes that "for many simple use cases, users will be better off using
channels," which is a direct, sourced steer toward this variant in Go
specifically.

## 9. Known production uses

Every `synchronized` method or block in the Java Class Library is a direct
instance of this pattern, because the JLS defines every Java object as
carrying an intrinsic monitor, cited above at JLS section 17.1. A concrete
library example is the pre-`java.util.concurrent` `java.util.Vector` and
`java.util.Hashtable`, whose methods are `synchronized` and which internally
use `wait`/`notifyAll` in blocking variants such as the historical producer
and consumer idioms documented in Oracle's own Java Tutorials, "Guarded
Blocks," at
https://docs.oracle.com/javase/tutorial/essential/concurrency/guardmeth.html,
verified 2026-08-13, which walks through exactly the wait-loop-then-notify
structure described in Dimension 7 as the canonical fix for a naive
`Drop` class.

The POSIX threads specification's condition variable API, `pthread_cond_wait`
and `pthread_cond_signal`, described in IEEE Std 1003.1-2017 (POSIX.1-2017),
section on Threads, reachable via The Open Group's public specification at
https://pubs.opengroup.org/onlinepubs/9699919799/functions/pthread_cond_wait.html,
verified 2026-08-13, is the direct, standardized building block that every
C, C++, and Rust monitor implementation on a POSIX system is built from,
and the specification's own reference implementation guidance describes the
mandatory predicate re-check loop in the same terms as Dimension 7.

.NET's `System.Threading.Monitor` class, documented at
https://learn.microsoft.com/en-us/dotnet/api/system.threading.monitor,
verified 2026-08-13, implements Hoare's monitor concept directly as a
first-class API, `Monitor.Enter`, `Monitor.Exit`, `Monitor.Wait`, and
`Monitor.Pulse`/`PulseAll`, underneath the `lock` keyword's syntactic sugar,
and the same page states explicitly that "the Wait, Pulse, and PulseAll
methods... implement the classic monitor pattern for synchronizing access to
an object," which is a direct, named, sourced statement that this pattern is
what the API implements.

Rust's `std::sync::Condvar`, documented at
https://doc.rust-lang.org/std/sync/struct.Condvar.html, verified 2026-08-13,
requires the caller to pass a `MutexGuard` into `wait` and returns a new
`MutexGuard`, an API shape whose documentation states plainly that "condition
variables are typically associated with a boolean predicate... and a mutex,"
and that "waiting on a condition variable... [is] typically done in a loop,"
which encodes the loop-not-if discipline from Dimension 7 into the type
signature itself, since `Condvar::wait` takes and returns the guard, making
it structurally awkward to call outside a loop that re-checks the guarded
value.

## 10. Consequences

Positive. Every method on the object is individually atomic, so a caller
never observes a torn or partially updated state, which removes an entire
class of data races by construction. Waiting is efficient, a parked thread on
a condition variable consumes no CPU and is woken by the scheduler exactly
when the signaling thread calls notify, in contrast to a spin-wait loop.
The synchronization is localized to the object itself rather than scattered
across every call site that touches the object's fields, so a reader who
wants to know whether some state is protected only has to read one class
rather than audit every caller. In languages with intrinsic monitors, the
syntax overhead is nearly zero, a single keyword, which keeps the pattern
from imposing the structural weight that Active Object's queue-and-future
machinery does.

Negative. Coarse-grained locking is the default outcome, because the
simplest correct implementation guards the whole object with one lock, and
splitting that into finer-grained locks to recover throughput is extra work
that is easy to defer indefinitely. Calling threads block, so a monitor is
the wrong tool wherever a caller cannot tolerate blocking, which is precisely
the case Active Object exists to handle. Getting the wait discipline wrong,
using `if` instead of `while`, forgetting to hold the lock across the
predicate check, or calling `notify` instead of `notifyAll` when more than
one waiter could be woken correctly, produces bugs that pass functional
tests and fail only under real concurrent load, which is the pattern's
sharpest correctness trap. Recursive-lock reentrancy, described in Dimension
5, can mask a design smell where one synchronized method calling another on
the same object hides an implicit ordering dependency that would be visible
as a compile error in a non-reentrant lock discipline.

## 11. Failure modes and misuse

**Lost wakeup.** Symptom, a consumer thread blocks forever even though a
producer has enqueued items, and the queue's size counter shows a
nonzero value while a thread sits parked. Cause, the producer mutated the
state and called `notify` before the consumer had actually entered its
`wait`, for example because the check-then-wait was not done atomically
under the same lock, so the signal was sent to an empty wait set and simply
vanished. Fix, the state check and the call to `wait` must happen while
holding the same lock the signaling side also holds while mutating state and
signaling, so that the two operations cannot interleave in the lost order.
This is exactly what a proper monitor's atomic lock-release-and-park inside
`wait` guarantees, and any hand-rolled variant that checks the condition
outside the lock, or releases the lock before calling wait, reintroduces the
race.

**Spurious wakeup treated as a real signal.** Symptom, a consumer processes a
value that is not actually there yet, or crashes on a null or default value,
intermittently, under load, but never in a single-threaded test. Cause, the
platform's condition variable, POSIX included, is explicitly permitted to
wake a waiter without any corresponding `notify` call, documented in both the
POSIX specification and the JLS cited above, and code that used `if` instead
of `while` around the wait proceeds as though the predicate is now true
without re-checking it. Fix, always wrap `wait` in a loop that re-checks the
predicate on every wake, exit-through, or return from wait, never on a bare
`if`.

**Deadlock from inconsistent lock ordering across two monitors.** Symptom, a
program that ran correctly for weeks freezes entirely under a specific
timing window, and a thread dump shows two threads each holding one monitor
and blocked waiting for the other's monitor. Cause, two separate Monitor
Objects are locked in opposite orders by two different call paths, for
example a `transfer(accountA, accountB)` method that locks A then B, and a
`transfer(accountB, accountA)` call from elsewhere that locks B then A, the
classic dining-philosophers shape. Fix, impose and document a single total
ordering for acquiring more than one monitor lock at a time, for example
always lock by ascending object identity hash or a stable numeric id, or
avoid holding two monitor locks simultaneously altogether by copying the data
needed out of one monitor before entering the second.

**Holding the monitor lock across a slow or blocking operation.** Symptom,
throughput collapses under load even though the workload is not CPU bound,
and profiling shows most threads parked waiting for the same lock rather than
doing work. Cause, a synchronized method performs network I/O, disk I/O, or
calls into another subsystem's monitor while still holding this monitor's
lock, so every other caller of this object queues up behind that one slow
operation. Fix, do the slow work outside the lock, entering the monitor only
to read the minimal state needed to start the operation and again only to
record its result, which is the standard "compute outside, mutate inside"
discipline for monitor bodies.

**Signaling before mutating, or forgetting to signal at all.** Symptom, a
correct-looking `enqueue` never wakes a waiting `dequeue`, and the consumer
times out or hangs. Cause, `notify` was called before the state mutation that
makes the predicate true actually happened, so a waiter that wakes, re-checks
under the loop discipline, finds the predicate still false, and goes back to
sleep before the mutation lands, or the signal call was simply omitted
because the author assumed the JVM or runtime would somehow wake waiters
automatically on any state change, which no monitor implementation does.
Fix, always perform the state mutation first, then call signal or broadcast,
both while still holding the lock, and never assume any implicit wake
happens on plain field assignment.

## 12. Trade-off matrix

| Force | Monitor Object | Active Object | Guarded Suspension (manual) | Lock-free structure |
|---|---|---|---|---|
| Caller blocking | Blocks caller for the call's duration | Caller does not block, gets a future | Blocks caller, same as Monitor Object | Never blocks the caller |
| Structural guarantee against races | Strong, enforced by the object's own lock | Strong, enforced by single-consumer queue | Weak, depends on every call site doing the guard correctly by hand | Strong for the specific operations the structure supports, weak for anything composite |
| Fine-grained parallelism | Poor by default, whole-object lock unless split by hand | Poor, single worker thread serializes all requests | Depends entirely on the author's discipline | Excellent, independent operations proceed concurrently |
| Handles waiting for state cleanly | Yes, via condition variables, the pattern's core purpose | Indirect, achieved via queued messages and futures, not condition waits | Yes, if the author implements the wait loop correctly every time | No, lock-free structures generally cannot express blocking waits without an added mechanism |
| Ceremony in languages with intrinsic monitors | Very low, one keyword | High, requires a queue, a worker thread, and future plumbing | Low, but repeated by hand at every call site | High, requires careful atomic-operation reasoning |
| Deadlock risk | Present when two or more monitors are held together | Low, a single active object rarely deadlocks against itself, but a future chain across active objects can | Present, same as Monitor Object | Absent by construction, no locks to order |

## 13. Related and incompatible patterns

Active Object is Monitor Object's closest relative and its usual replacement
when the caller-blocking cost becomes unacceptable. Active Object is
frequently built directly on top of a Monitor Object internally, the
activation queue itself is commonly a small Monitor Object guarding a list
with `enqueue` and `dequeue` methods exactly like the running example in this
entry, even though the two patterns are marked incompatible with each other
at the outer, caller-facing level. A single object should not simultaneously
promise synchronous monitor-style calls and asynchronous active-object-style
calls on the same public interface, because that mixes two different
threading contracts a client would have to remember per method.

Guarded Suspension is the more primitive, unnamed-as-a-pattern-in-code
technique that Monitor Object formalizes. The check-loop-then-proceed shape
described in Dimension 7 is Guarded Suspension's essence, and Monitor Object
is what you get when Guarded Suspension is consistently applied to every
method of one object with one shared lock and named condition variables
rather than reimplemented ad hoc at each call site.

Half-Sync/Half-Async frequently uses a Monitor Object as the queue that
bridges the synchronous layer and the asynchronous layer, the same role
Active Object's activation list plays, which is why all three patterns in
this family cross-reference each other's queue implementation as a shared
building block rather than three unrelated designs.

Producer-Consumer, in its classic textbook form, is simply the running
example of this entry, a bounded buffer implemented as a Monitor Object with
two conditions, "not full" for producers and "not empty" for consumers. Many
introductions to concurrency teach Producer-Consumer as the motivating
problem and Monitor Object as its solution without separating the two as
distinct named patterns, which this entry treats as a related-but-distinct
pairing, the problem and its canonical solution.

## 14. Refactoring path in and out

**Introducing a Monitor Object into code that lacks one.** Start from a class
whose fields are read and written from more than one thread with no lock at
all, or with locking scattered across call sites rather than inside the
class. First, identify the invariant the class must maintain across its
public methods, for example "size never exceeds capacity" for a bounded
queue. Second, add one lock, or in an intrinsic-monitor language mark the
methods `synchronized`, and move any external locking that callers were
doing into the class itself, so the class becomes solely responsible for its
own consistency. Third, for any method that currently returns early or throws
when the state is not ready, for example a `dequeue` that returns null on an
empty queue, replace the early return with a condition-variable wait loop
that blocks until the state is ready instead of pushing the retry logic onto
every caller. Fourth, add explicit condition variables, or reuse the
intrinsic single condition if only one predicate is needed, and place
`signal` or `notifyAll` calls at every point that changes the state a waiter
might be blocked on. Verify by writing a test that starts one thread blocked
in the waiting method and a second thread that performs the state change,
and asserting the first thread unblocks within a bounded time.

**Removing a Monitor Object once it stops earning its place.** The signal
that a Monitor Object should be dismantled is contention, one lock now
serializes operations that provably never touch overlapping state, or
callers that cannot tolerate the blocking the pattern imposes. First, if the
problem is coarse locking over disjoint state, split the single monitor into
several smaller ones, one per independently-accessed region of state, or
migrate to a concurrent collection type the platform already provides, such
as `java.util.concurrent.ConcurrentLinkedQueue` or `java.util.concurrent
.locks.ReadWriteLock`, which is frequently a straight drop-in replacement for
a hand-rolled Monitor Object once the platform matured past the point where
the hand-rolled version was necessary. Second, if the problem is caller-side
blocking, refactor toward Active Object, keeping the Monitor Object as the
internal activation-queue implementation detail rather than discarding it
entirely, per Dimension 13. Third, run the full concurrent test suite before
and after, because removing a monitor is exactly the kind of change that
silently reintroduces the races the monitor existed to prevent.

## 15. Testing and verification

Testing a Monitor Object is easier than testing raw manual locking for one
structural reason. the invariant lives in one place, so a single test class
can drive the object from N threads and assert the invariant after every
call rather than reasoning about every call site independently. A minimal
but effective test starts several threads each calling a mutating
synchronized method a fixed number of times, joins all threads, and asserts
the final state matches the arithmetic sum expected if every call executed
atomically, for example a shared counter incremented 10,000 times from 10
threads should read exactly 100,000, and any lower number is direct proof of
a missed or broken lock.

Testing the wait-and-signal half specifically requires deliberately
constructing the interleaving from Dimension 7 rather than hoping a random
test run hits it. start a consumer thread, use a synchronization barrier or
a short sleep with a loop-based poll on the implementation's internal state
to confirm the consumer thread has actually entered its wait, before then
starting the producer thread and asserting the consumer unblocks within a
bounded timeout. A monitor bug of the lost-wakeup class described in
Dimension 11 will make exactly this test hang or time out, while a naive
test that starts producer and consumer simultaneously and merely checks the
final queue state can pass even with a lost-wakeup bug present, because the
race window it depends on may simply not occur on that run.

Java's `java.util.concurrent` package ships `CountDownLatch` and
`CyclicBarrier`, both useful as test scaffolding to force the deterministic
ordering described above, consumer definitely waiting before producer
signals, rather than as production replacements for the monitor under test.
Stress testing with a high thread count and a long duration, run repeatedly
in CI rather than once locally, is the practical mitigation for the fact
that most monitor bugs are timing-dependent and will not reproduce on every
run. A monitor test suite that passes once is weaker evidence than the same
suite passing one thousand consecutive times under load.

## 16. Observability signals

Lock hold time and lock wait time are the two numbers that most directly
diagnose a Monitor Object's health. Hold time, how long a thread keeps the
lock once acquired, reveals whether the pattern's rule against doing slow
work inside the lock, Dimension 11, is being honored. Wait time, how long
callers queue for the lock before acquiring it, reveals contention. Java
Flight Recorder and `jstack` thread dumps both surface which threads are
`BLOCKED` waiting to enter a monitor versus `WAITING` inside a `wait` call,
a distinction that matters diagnostically. `BLOCKED` means lock contention
from too many concurrent callers, `WAITING` means a thread is legitimately
parked on a condition and the question becomes whether the expected signal
is arriving. The JDK's own monitoring documentation for thread state,
part of the `java.lang.Thread.State` enum javadoc at
https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Thread.State.html,
verified 2026-08-13, defines exactly this `BLOCKED` versus `WAITING`
distinction as two of the six thread states, which is the primary
observability signal built into the platform itself.

A healthy monitor under load shows a `WAITING` thread count that oscillates
and drains, waiters appear when the guarded predicate is false and disappear
promptly after a signal, and a `BLOCKED` count that stays low relative to
total request rate. A failing instance shows a `WAITING` count that grows
monotonically and never drains, the lost-wakeup or missing-signal failure
mode from Dimension 11, or a `BLOCKED` count that dominates thread dumps
taken seconds apart with the same thread stuck at the front each time, which
points at a thread holding the lock across a slow operation rather than at
contention volume alone. Logging the queue depth or the number of parked
waiters at signal time, one line per signal, gives a cheap, low-overhead
trend line that a dashboard can chart without full profiling overhead.

## 17. Security and privacy implications

Monitor Object has no direct data-handling implication beyond the general
rule that whatever state it protects should already be classified and
handled per the sensitivity of that state. The pattern itself neither adds
nor removes exposure of the underlying data. The implication that is
specific to this pattern is availability rather than confidentiality. a
monitor guarding a resource that untrusted or unbounded external input can
drive, for example a per-connection object whose queue depth is unbounded and
whose `enqueue` a remote client controls, is a straightforward denial-of-
service vector, because a slow or malicious client can hold the monitor's
capacity, or the calling threads that block on it, indefinitely if the
`wait` calls used are unbounded rather than timed. The standard mitigation is
to always use a bounded wait, per the monitor-with-timeout variant in
Dimension 8, on any monitor whose signaling condition is influenced, directly
or indirectly, by input from outside the trust boundary, so a caller that
would otherwise block forever instead fails after a deadline the surrounding
system can handle.

## 18. References

1. C.A.R. Hoare, "Monitors, an Operating System Structuring Concept,"
   Communications of the ACM, volume 17, issue 10, October 1974, pages 549
   to 557. https://dl.acm.org/doi/10.1145/355620.361161, verified
   2026-08-13.
2. Douglas C. Schmidt, Michael Stal, Hans Rohnert, and Frank Buschmann,
   *Pattern-Oriented Software Architecture, Volume 2, Patterns for
   Concurrent and Networked Objects*, John Wiley and Sons, 2000, chapter 5,
   Monitor Object pattern.
3. Java Language Specification, Java SE 21 Edition, section 17.1,
   "Synchronization." https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html,
   verified 2026-08-13.
4. `java.lang.Object` javadoc, `wait()` method documentation, Java SE 21.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Object.html#wait(),
   verified 2026-08-13.
5. Oracle Java Tutorials, "Guarded Blocks."
   https://docs.oracle.com/javase/tutorial/essential/concurrency/guardmeth.html,
   verified 2026-08-13.
6. The Open Group Base Specifications Issue 7, IEEE Std 1003.1-2017,
   `pthread_cond_wait` and `pthread_cond_timedwait`.
   https://pubs.opengroup.org/onlinepubs/9699919799/functions/pthread_cond_wait.html,
   verified 2026-08-13.
7. Microsoft Learn, `System.Threading.Monitor` class documentation.
   https://learn.microsoft.com/en-us/dotnet/api/system.threading.monitor,
   verified 2026-08-13.
8. Rust standard library documentation, `std::sync::Condvar`.
   https://doc.rust-lang.org/std/sync/struct.Condvar.html, verified
   2026-08-13.
9. Go standard library documentation, `sync.Cond`.
   https://pkg.go.dev/sync#Cond, verified 2026-08-13.
10. `java.lang.Thread.State` javadoc, Java SE 21.
    https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Thread.State.html,
    verified 2026-08-13.

## Code examples

### Java, the intrinsic-monitor idiom

Java gives every object a built-in monitor lock and a single condition,
which makes this the most direct expression of the pattern in any mainstream
language. The bounded queue below uses `synchronized` methods and the
`while`-loop wait discipline from Dimension 7.

```java
import java.util.LinkedList;
import java.util.Queue;

public final class BoundedQueue<T> {
    private final Queue<T> items = new LinkedList<>();
    private final int capacity;

    public BoundedQueue(int capacity) {
        this.capacity = capacity;
    }

    public synchronized void enqueue(T item) throws InterruptedException {
        while (items.size() == capacity) {
            wait();
        }
        items.add(item);
        notifyAll();
    }

    public synchronized T dequeue() throws InterruptedException {
        while (items.isEmpty()) {
            wait();
        }
        T item = items.remove();
        notifyAll();
        return item;
    }

    public synchronized int size() {
        return items.size();
    }
}
```

### Go, the mutex-plus-Cond idiom

Go has no intrinsic per-object monitor, so the pattern is assembled by hand
from `sync.Mutex` and `sync.Cond`. The `sync.Cond` documentation itself
recommends channels for many cases, cited in Dimension 8, but the `Cond`
form below is the closer, more literal translation of the classic monitor
shape and is shown for that reason.

```go
package main

import "sync"

type BoundedQueue struct {
	mu       sync.Mutex
	notFull  *sync.Cond
	notEmpty *sync.Cond
	items    []int
	capacity int
}

func NewBoundedQueue(capacity int) *BoundedQueue {
	q := &BoundedQueue{capacity: capacity}
	q.notFull = sync.NewCond(&q.mu)
	q.notEmpty = sync.NewCond(&q.mu)
	return q
}

func (q *BoundedQueue) Enqueue(item int) {
	q.mu.Lock()
	defer q.mu.Unlock()
	for len(q.items) == q.capacity {
		q.notFull.Wait()
	}
	q.items = append(q.items, item)
	q.notEmpty.Signal()
}

func (q *BoundedQueue) Dequeue() int {
	q.mu.Lock()
	defer q.mu.Unlock()
	for len(q.items) == 0 {
		q.notEmpty.Wait()
	}
	item := q.items[0]
	q.items = q.items[1:]
	q.notFull.Signal()
	return item
}
```

### Rust, the Mutex-plus-Condvar idiom

Rust's `Condvar::wait` takes ownership of a `MutexGuard` and returns a new
one, an API shape that structurally discourages the `if`-instead-of-`while`
mistake described in Dimension 11, since the returned guard is only valid to
act on after the loop's predicate re-check.

```rust
use std::collections::VecDeque;
use std::sync::{Arc, Condvar, Mutex};

struct BoundedQueue {
    state: Mutex<VecDeque<i32>>,
    not_empty: Condvar,
    not_full: Condvar,
    capacity: usize,
}

impl BoundedQueue {
    fn new(capacity: usize) -> Arc<Self> {
        Arc::new(BoundedQueue {
            state: Mutex::new(VecDeque::new()),
            not_empty: Condvar::new(),
            not_full: Condvar::new(),
            capacity,
        })
    }

    fn enqueue(&self, item: i32) {
        let mut guard = self.state.lock().unwrap();
        while guard.len() == self.capacity {
            guard = self.not_full.wait(guard).unwrap();
        }
        guard.push_back(item);
        self.not_empty.notify_one();
    }

    fn dequeue(&self) -> i32 {
        let mut guard = self.state.lock().unwrap();
        while guard.is_empty() {
            guard = self.not_empty.wait(guard).unwrap();
        }
        let item = guard.pop_front().unwrap();
        self.not_full.notify_one();
        item
    }
}

fn main() {
    let q = BoundedQueue::new(2);
    q.enqueue(1);
    q.enqueue(2);
    let a = q.dequeue();
    let b = q.dequeue();
    assert_eq!((a, b), (1, 2));
}
```

C#, TypeScript, Python, and Kotlin are omitted from the code examples. C#'s
`System.Threading.Monitor` and `lock` keyword would repeat the Java example
nearly line for line, since both languages inherit the same intrinsic-monitor
design directly from Hoare's original formulation, and the entry already
demonstrates that idiom in Java. Python's global interpreter lock removes
most of the pattern's motivating problem for pure-Python objects, and
`threading.Condition` is a near-literal copy of the Java API shown above, so
it would not add a genuinely distinct idiom to this entry. TypeScript and
JavaScript's single-threaded event loop has no OS-level blocking wait at
all, so a literal Monitor Object translation would misrepresent the pattern.
The async-native equivalent belongs to a different entry on async
coordination primitives rather than this one. Kotlin's `synchronized`
function and `Object.wait`/`notify` interop are a thin wrapper over the same
JVM intrinsic monitor already shown in the Java example.
