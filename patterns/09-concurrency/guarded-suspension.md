---
name: Guarded Suspension
slug: guarded-suspension
family: 09-concurrency
category: Concurrency
aliases: [Guarded Wait, Wait Until Ready, Condition-Guarded Blocking]
first_described: "Lea 2000; Schmidt, Stal, Rohnert, Buschmann 2000"
maturity: canonical
related: [balking, monitor-object, producer-consumer, thread-safe-interface, read-write-lock, active-object]
incompatible_with: []
verified: 2026-08-02
---

# Guarded Suspension

## 1. Name, aliases, and lineage

The canonical name is Guarded Suspension. The Wikipedia summary of the pattern
attributes it to Doug Lea's *Concurrent Programming in Java, Second Edition*,
Addison-Wesley, 2000, and describes it as "a software design pattern for
managing operations that require both a lock to be acquired and a
precondition to be satisfied before the operation can be executed"
([Wikipedia, "Guarded suspension"](https://en.wikipedia.org/wiki/Guarded_suspension),
verified 2026-08-02). The same shape, under the same name, appears
independently in the concurrency pattern catalog of Douglas C. Schmidt,
Michael Stal, Hans Rohnert and Frank Buschmann, *Pattern-Oriented Software
Architecture, Volume 2. Patterns for Concurrent and Networked Objects*, Wiley,
2000, whose contents list is summarized on Wikipedia's concurrency pattern
overview page alongside Balking, Monitor Object and Active Object as sibling
entries in the same catalog
([Wikipedia, "Concurrency pattern"](https://en.wikipedia.org/wiki/Concurrency_pattern),
verified 2026-08-02). Both books were written by people working on the same
problem in the same period, Lea publishing the Java-specific treatment and the
POSA2 authors publishing the language-neutral catalog entry, and the two
converge on the same name and the same mechanism, which is why this entry
lists both as the origin rather than picking one.

The alias Guarded Wait is used interchangeably in code comments and in some
secondary literature, and it is the more literal description of what the
calling thread does. Wait Until Ready appears in framework documentation for
initialization barriers that use the same mechanism to hold a caller until a
resource finishes constructing. Condition-Guarded Blocking is a phrase this
entry uses to distinguish the pattern from Guarded Command Language, a
distinct formalism from Edsger Dijkstra's 1975 paper on nondeterministic
choice among enabled statements in sequential program derivation, which
shares the word "guard" but describes a notation for program derivation, not
a concurrency synchronization technique. The Wikipedia entry on Guarded
Suspension lists Guarded Command Language as a related but distinct concept
for exactly this reason, and a reader who searches for "guarded" in a
concurrency context should not conflate the two.

The pattern is also frequently rediscovered without a name. A method that
opens with `while (!condition) { wait(); }` before doing its real work is
Guarded Suspension whether or not the author has ever read Lea or POSA2. This
entry treats the named pattern and its many unnamed instances as the same
thing, because the mechanism, not the label, carries the correctness
guarantee.

## 2. Problem and context

A thread calls a method on a shared object, and the method cannot proceed
safely or sensibly until some condition involving that object's state becomes
true. A queue's `take` cannot return an element from an empty queue. A
connection pool's `acquire` cannot hand out a connection when every connection
is checked out. A barrier's `await` cannot release a thread until every other
participant has also arrived. A task future's `get` cannot return a result
before the task completes.

Three answers exist to what the calling thread should do while the condition
does not hold, and the choice between them is the entire subject of this
pattern family.

The naive answer is to loop, checking the condition repeatedly with no pause,
which burns a CPU core purely to poll a flag and starves other work on that
core. A slightly better naive answer adds a short sleep between checks, which
trades CPU burn for added latency that is either too short, so the loop still
spins wastefully, or too long, so the thread notices the change late. Neither
scales to many waiters, because every waiter is independently polling shared
state, and the polling itself becomes contention.

The Guarded Suspension answer is different in kind, not degree. The calling
thread parks itself, releasing the CPU entirely, and is only ever rescheduled
by the operating system or runtime scheduler when a producer thread that
changed the guarded state explicitly wakes it. No polling, no wasted cycles, no
sleep interval to tune. The context in which this matters is any shared,
mutable object accessed by more than one thread where some operations are only
valid in a subset of the object's states, and where the number of threads that
might be waiting, and the length of time they might wait, are both unbounded
at compile time. A single-consumer, always-full queue has no need of the
pattern. A queue read from many threads under bursty load, sometimes empty for
milliseconds and sometimes for minutes, is exactly the situation the pattern
was built for.

## 3. Forces

The pattern balances the following competing pressures.

- **Correctness under concurrent mutation.** Favoured, and this is the
  pattern's whole purpose. The guard is re-checked after every wakeup rather
  than trusted once, which is what survives a second thread racing in and
  consuming the resource between the wakeup signal and the waiter actually
  running.
- **CPU efficiency while waiting.** Strongly favoured over any polling
  approach. A parked thread consumes no CPU time, and a runtime with many
  waiters, a connection pool serving thousands of blocked callers under load,
  pays nothing for the ones that are asleep.
- **Latency to notice a state change.** Favoured relative to polling with a
  sleep interval, because notification is immediate rather than bounded by a
  poll period, but not free. The waiter still pays the cost of being rescheduled
  by the operating system, which is typically low microseconds to low
  milliseconds depending on system load, and it pays the cost of re-acquiring
  the lock the notifying thread may still be holding.
- **Simplicity of the caller's mental model.** Sacrificed somewhat. A method
  that can suspend the calling thread for an unbounded time is a different
  contract from one that always returns promptly, and callers must reason about
  timeouts, interruption and deadlock in a way a synchronous, always-ready
  method does not require.
- **Composability across multiple guards.** Sacrificed as guard count grows.
  A single condition variable per guard scales cleanly to two or three guarded
  states, as the classic bounded buffer's `notFull` and `notEmpty` demonstrate,
  but an object with many independent preconditions either grows a matching
  number of condition variables or falls back to one shared condition and a
  spurious-wakeup storm on every signal, since every waiter on a single
  condition wakes for every notification and must re-check its own guard.
- **Fairness among waiting threads.** Mixed, and language-dependent. Some
  runtimes offer no ordering guarantee among woken threads, so a thread that
  arrived first can be the last to acquire the resource; other runtimes and
  higher-level constructs, notably `java.util.concurrent.locks.ReentrantLock`
  with the fair flag set, provide first-in-first-out ordering at a measurable
  throughput cost.
- **Susceptibility to deadlock and lost wakeup.** Sacrificed by hand-rolled
  implementations that get the lock-then-wait ordering wrong. This is the
  dimension the pattern's precise recipe exists to close, see dimension 5 and
  dimension 11.

A pattern that traded nothing away would not need a name. The price paid here
is a harder contract for the caller and a correctness discipline the
implementer must follow exactly, in exchange for a wait that costs no CPU and
resolves as soon as the awaited state actually arrives.

## 4. Applicability and non-applicability

Reach for Guarded Suspension when the following hold together.

- An operation on a shared object is only valid, or only sensible, in a
  subset of that object's possible states, and the operation must not proceed
  outside that subset.
- More than one thread can change the object's state such that the guard
  transitions from false to true, so the waiting thread genuinely cannot
  compute the answer itself and must be told.
- The expected wait, in the common case, is long enough that spinning would
  waste meaningful CPU. A guard that is almost always already true when checked
  does not need this machinery, see the non-applicability list below.
- The caller is willing to accept a method whose duration is unbounded, or
  is willing to supply a timeout and handle the case where the guard never
  becomes true in time.
- The number of possible waiters is not known and fixed at one, in which
  case a simpler single-slot handoff, such as a one-shot `Future`, may be
  enough and the general-purpose condition machinery is more than the problem
  needs.

Do NOT reach for Guarded Suspension in these cases, and the reason for each
matters more than the rule itself.

- **The guard is almost always already satisfied, and failing fast is
  acceptable when it is not.** This is the Balking pattern's territory, not
  Guarded Suspension's. A cache refresh that should simply be skipped if one is
  already in progress does not need a caller who blocks and waits for the
  in-progress refresh to finish; it needs a caller who checks once and returns
  immediately if the guard fails. Applying Guarded Suspension here forces every
  caller to pay a potentially long wait for work they did not actually need
  completed on their behalf.
- **The wait has a hard, short, known upper bound and busy-waiting is
  genuinely cheaper than a context switch.** On a lock held for a handful of
  machine instructions inside a low-level allocator or a lock-free data
  structure's fallback path, a short spin loop that never involves the
  operating system scheduler at all can outperform parking a thread, because
  the cost of two context switches, one to sleep and one to wake, exceeds the
  cost of the spin. This is a narrow, measured, low-level exception, not a
  license to spin on ordinary application-level guards.
- **The condition and the resource creation are the same event, and only one
  waiter will ever exist for that resource.** A single, one-time result that
  many threads want to read once, such as a lazily-initialized singleton or the
  result of exactly one asynchronous computation, is better modelled with
  Future/Promise, which exposes a get-once contract and typically caches the
  result, rather than a general condition variable that every caller must
  re-check.
- **The producer and consumer never share memory and communicate only by
  message passing across a process or network boundary.** Guarded Suspension
  is an in-process, shared-memory pattern built on a lock and a condition
  variable, or their equivalent. A distributed queue behind a network call
  needs backpressure, timeouts and retries at the protocol level, and dressing
  that up as an in-process condition variable is a category error.
  Communicating Sequential Processes and channel-based concurrency solve the
  cross-boundary version of this problem with different primitives; see the
  Communicating Sequential Processes entry.
- **The language or runtime already supplies a purpose-built, well-tested
  bounded collection that implements the pattern internally.** `BlockingQueue`
  in Java, `queue.Queue` in Python and `BlockingCollection<T>` in .NET already
  are Guarded Suspension, correctly implemented, tested at scale and hardened
  against the failure modes in dimension 11. Reimplementing the bounded buffer
  by hand with a raw lock and condition variable when the standard library
  already ships one is needless risk for no benefit; reach for the pattern by
  hand only when the guard is something the standard library does not model,
  such as an application-specific readiness condition.
- **The condition depends on real time rather than on another thread's
  action.** Waiting until a wall-clock deadline is a sleep or a scheduled
  timer, not a guard on shared state that another thread mutates and signals.

## 5. Structure

Four participants, named by the role each plays.

- **GuardedObject.** The shared object whose state the guard examines. It
  owns the mutable fields the condition is computed from, and it owns the
  synchronization primitives, the lock and the condition variable or their
  equivalent, that protect those fields.
- **Guard.** The boolean predicate over the GuardedObject's state that must
  hold before a GuardedMethod may proceed. The guard is not a separate object
  in most implementations; it is a condition expression evaluated inside the
  lock. It is named as its own participant here because it is the thing that
  must be recomputed, never assumed, at every wakeup.
- **GuardedMethod.** The operation a Caller invokes that has a precondition
  expressed by the Guard. It acquires the lock, loops on the Guard, calls
  `wait` (or the equivalent parking primitive) inside that loop while the Guard
  is false, and once the Guard is true, performs its real work and releases the
  lock.
- **Notifier.** Any method on the same GuardedObject, invoked from a different
  thread, that changes state such that the Guard could newly be true, and that
  calls `notify` or `notifyAll` (or the equivalent) after making that change,
  while still holding the same lock the GuardedMethod uses.

The critical structural fact, responsible for most of the correctness
subtlety in dimension 11, is that all four participants share exactly one
lock. The Guard is read under that lock. The condition variable the
GuardedMethod parks on is associated with that same lock, so that parking
atomically releases the lock and suspends the thread, and waking re-acquires
the lock before the GuardedMethod resumes. The Notifier holds that same lock
while it mutates the state the Guard depends on and while it signals. If any
of these three uses a different lock, or if the state mutation happens outside
the lock the Guard is checked under, the pattern is broken in a way that
usually does not show up in testing and does show up in production under load.

## 6. ASCII structure diagram

```
   +----------------------------------------------------+
   |                  GuardedObject                     |
   |------------------------------------------------------|
   | - lock, a Lock                                       |
   | - condition, a Condition bound to the lock            |
   | - state, the fields the guard reads                  |
   |------------------------------------------------------|
   | + guardedMethod()                                    |
   | + notifierMethod()                                    |
   +----------------------------------------------------+
             |                              ^
             | uses                         | uses
             v                              |
   +-----------------+            +-----------------+
   |      Lock       |<---------->|    Condition    |
   |-----------------|  bound to  |-----------------|
   | + lock()        |            | + await()       |
   | + unlock()      |            | + signal()      |
   +-----------------+            | + signalAll()   |
                                   +-----------------+

   guardedMethod() body, expressed as pseudocode.

     lock.lock()
     while (!guardHolds(state)) {
         condition.await()   -- atomically unlocks, suspends, re-locks on wake
     }
     -- guard is now true, and the lock is held --
     do real work, mutate state if needed
     lock.unlock()

   notifierMethod() body, expressed as pseudocode.

     lock.lock()
     mutate state such that guardHolds(state) may now be true
     condition.signal()  -- or signalAll()
     lock.unlock()
```

## 7. Dynamics

The runtime flow below shows two callers of `take` racing an empty queue
against one `put`, using the loop-around-`await` shape rather than a
single `if`, which is the detail that keeps the pattern correct when more
than one thread is woken by the same signal.

```
CallerA (take)     CallerB (take)     Lock/Condition        Producer (put)
    |                    |                    |                    |
    |-- lock() --------->|                    |                    |
    |   guard false      |                    |                    |
    |-- await() -------->|-- unlocks,        |                    |
    |   (parked)         |   parks A -------->|                    |
    |                    |-- lock() ------------------------------>|
    |                    |   guard false                            |
    |                    |-- await() ------->|-- unlocks,           |
    |                    |   (parked)         |   parks B --------->|
    |                    |                    |                     |
    |                    |                    |<-- lock() ----------|
    |                    |                    |    put item          |
    |                    |                    |<-- signal() ----------
    |                    |                    |   wakes ONE waiter    |
    |                    |                    |<-- unlock() ----------|
    |<-- re-lock A ----------------------------|                     |
    |   guard TRUE now                        |                     |
    |   take item, unlock() ------------------>|                     |
    |                    |                    |                     |
    |                    |<-- re-lock B -------|  (only if signalAll,|
    |                    |   guard now FALSE   |   or A's re-check)  |
    |                    |   again -> await()  |                     |
```

The two facts this diagram makes visible are the ones a description in prose
tends to gloss over. First, `signal()` wakes at most one waiter and does not
guarantee it wakes CallerA rather than CallerB; the choice of which parked
thread is woken is a scheduling decision the runtime makes, not the
Notifier. Second, a woken thread does not resume with the lock free to act on
stale knowledge; it resumes holding the lock, re-checks the Guard because
`await` returning is not itself proof the Guard holds, and only proceeds when
the re-check succeeds. If CallerB was woken instead of CallerA, and only one
item was put, CallerB's re-check finds the guard true, takes the item, and
CallerA's later reschedule finds the guard false again and parks once more.
Nothing is lost, nothing double-consumes, and the sequence is correct
regardless of which waiter the scheduler happens to wake, precisely because
the guard is re-verified rather than assumed.

## 8. Implementation variants

**The `while` loop around `wait`, single condition variable.** The baseline
form, one lock, one condition, one guard, checked in a `while` not an `if`.
Correct against spurious wakeups, a wakeup with no corresponding notify, which
POSIX condition variables and the Java memory model both explicitly permit,
and correct against the lost-race scenario in dimension 7. This is the form
the `BoundedBuffer` example in the `java.util.concurrent.locks.Condition`
Javadoc uses, and it is the form to default to.

**Two condition variables on one lock, for opposite guards.** When a bounded
resource has a full guard and an empty guard, as a bounded buffer does,
splitting into `notFull` and `notEmpty` conditions on the same lock lets a
`signal()` on one wake only threads that could possibly benefit, rather than
waking every waiter on a single shared condition and making them all re-check
a guard that, for half of them, cannot have become true. The Java
`Condition` Javadoc's own bounded-buffer example uses exactly this split and
states the rationale plainly, wanting to "keep waiting put threads and take
threads in separate wait-sets" ([Java SE 21 API documentation,
`java.util.concurrent.locks.Condition`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/locks/Condition.html),
verified 2026-08-02).

**Semaphore-backed guard.** For the specific and common guard where at least
N resources are available, a counting semaphore already implements Guarded
Suspension internally, exposing `acquire`/`release` rather than a raw
condition variable. This trades generality, a semaphore can only express a
single non-negative counter, for a smaller and harder-to-misuse surface.

**Timed guard, `awaitNanos` or `wait(timeout)`.** The Guard loop is bounded by
a deadline, and the method returns a failure or throws a timeout exception
rather than waiting forever. This is close to mandatory in production code,
since an unbounded wait on a Notifier that never arrives, because of a bug, a
crash, or a permanently-closed resource, otherwise hangs the caller forever.

**Signal-with-handoff via a queue or channel, no explicit condition
variable.** Languages and runtimes with first-class channels, Go's channels
and CSP-style languages generally, express the same guard-and-wait shape as a
blocking receive on a channel that the producer sends into, with the runtime
scheduler doing the parking and waking that a hand-rolled condition variable
would otherwise do explicitly. `sync.Cond` still exists in Go's standard
library for the cases a channel does not fit, and its own documentation
prescribes the identical loop-around-Wait shape as the Java form ([Go
standard library documentation, `sync.Cond`](https://pkg.go.dev/sync#Cond),
verified 2026-08-02).

**Coroutine or `async`/`await` suspension.** In an actor or coroutine
runtime, the guarded method suspends the coroutine rather than blocking an
operating-system thread, and the scheduler resumes it when the awaited event
fires. The correctness discipline is identical, re-check the guard on resume,
because the coroutine can be resumed for reasons other than the specific
event it was waiting for, but the cost model changes since parking a
coroutine costs far less than parking a thread, which is why this variant
scales to far larger waiter counts.

**Monitor-object variant, guard baked into the object's own methods.** When
every method of an object implicitly acquires the same lock, as a language's
built-in monitor construct does, the Guarded Suspension logic becomes the
first few lines of the relevant method bodies rather than an explicit,
separately named lock and condition. The Monitor Object pattern is the
umbrella this sits inside; see dimension 13.

## 9. Known production uses

**`java.util.concurrent.BlockingQueue` and its implementations
(`ArrayBlockingQueue`, `LinkedBlockingQueue`).** The interface documentation
states that `put(E e)` is defined to "insert the specified element into this
queue, waiting if necessary for space to become available", and `take()` is
defined to "retrieve and remove the head of this queue, waiting if necessary
until an element becomes available", explicitly built for the producer and
multiple-consumer scenario ([Java SE 21 API documentation,
`java.util.concurrent.BlockingQueue`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/BlockingQueue.html),
verified 2026-08-02). This interface underlies `ThreadPoolExecutor`'s work
queue, so every standard Java thread pool depends on Guarded Suspension at
its core.

**Python's `queue.Queue`.** The standard library documentation describes
`put(item, block=True, timeout=None)` as blocking "if necessary until a free
slot is available" and `get(block=True, timeout=None)` as blocking "if
necessary until an item is available", and notes that the module's three
queue types "use locks to temporarily block competing threads" internally
([Python 3 documentation, `queue`](https://docs.python.org/3/library/queue.html),
verified 2026-08-02). `queue.Queue` is the standard bridge between producer
and consumer threads in CPython multithreaded programs, including the pattern
used to hand work from a main thread to a `ThreadPoolExecutor`-backed pool.

**Go's `sync.Cond`.** The standard library documentation describes `Cond` as
implementing "a condition variable, a rendezvous point for goroutines waiting
for or announcing the occurrence of an event", requires the associated
`Locker` to be held while changing the condition and while calling `Wait`, and
prescribes checking the condition in a loop because Wait "cannot return unless
awoken by Broadcast or Signal" yet the caller "typically cannot assume that
the condition is true when Wait returns" ([Go standard library documentation,
`sync.Cond`](https://pkg.go.dev/sync#Cond), verified 2026-08-02).

**.NET's `System.Collections.Concurrent.BlockingCollection<T>`.** The class
documentation states that when the collection reaches its specified maximum
capacity, "the producing threads will block until an item is removed", and
when the collection is empty, "the consuming threads will block until a
producer adds an item", through its `Add` and `Take` methods ([Microsoft .NET
API documentation, `BlockingCollection<T>`](https://learn.microsoft.com/en-us/dotnet/api/system.collections.concurrent.blockingcollection-1),
verified 2026-08-02). `BlockingCollection<T>` is the standard building block
for producer-consumer pipelines in .NET server applications and is used
internally by several .NET dataflow and pipeline libraries as the bounded
handoff between stages.

## 10. Consequences

Positive.

- A waiting thread consumes no CPU while its precondition is unmet, which is
  the pattern's entire reason to exist and the property that lets a system
  hold thousands of idle waiters cheaply.
- The wakeup latency after the guard becomes true is bounded by scheduler
  responsiveness rather than by a polling interval, which is both faster and
  more predictable than any sleep-and-recheck loop.
- The correctness discipline, one lock, guard checked in a loop, state
  mutated and signalled under that same lock, is a small, learnable, and
  mechanically checkable recipe once understood, unlike ad hoc flag-and-sleep
  schemes that each invent their own subtly different race conditions.
- The pattern composes cleanly with bounded resources to provide automatic
  backpressure. A producer that outruns a consumer simply blocks in its own
  guarded `put`, without any separate rate-limiting mechanism.
- Once implemented inside a well-tested collection, such as `BlockingQueue`
  or `queue.Queue`, the correctness burden is paid once by the library authors
  and application code gets the guarantee for free.

Negative.

- Hand-rolled implementations are easy to get subtly wrong, and the specific
  ways they go wrong, lost wakeup, spurious-wakeup vulnerability, notify
  outside the lock, are each individually rare enough in testing to survive
  code review and only appear under production load, see dimension 11.
- A caller of a guarded method accepts an operation whose duration is, absent
  an explicit timeout, unbounded. This changes the caller's own reasoning
  about liveness and must be documented, not left implicit.
- Multiple guards on one object either multiply the number of condition
  variables, adding bookkeeping, or share one condition variable, adding
  spurious wakeups where every waiter re-checks a guard that could not
  possibly have changed for it.
- Debugging a stuck system that depends on Guarded Suspension requires
  reading thread dumps and correlating which threads are parked on which
  condition, which is materially harder than debugging a synchronous call
  stack, and requires the observability discipline in dimension 16 to be in
  place before the incident, not during it.
- The pattern is entirely intra-process. It offers no answer for coordinating
  across processes or machines, and a team that has internalised it as the
  way to make a caller wait can be tempted to misapply it, or a homegrown
  imitation of it, across a network boundary where it does not belong.

## 11. Failure modes and misuse

**Lost wakeup.** Symptom. A thread blocks in `take()` or the equivalent
forever, even though a matching `put()` clearly ran, visible in logs or
metrics, and the process must be restarted to unstick it. Cause. The Notifier
mutated the state and called `notify` outside the lock, or the GuardedMethod
checked the guard and called `wait` as two separate steps with a window
between them where another thread could run, so the Notifier's signal arrives
in the gap between the check and the wait and is never seen by the waiter.
Fix. Guarantee, as an invariant, that the state mutation and the `notify`
call happen while holding the exact same lock the waiter holds while checking
the guard and calling `wait`, so the two are never interleaved with a gap.

**Spurious wakeup treated as a real signal.** Symptom. A guarded method
occasionally proceeds when its precondition is not actually true, an
intermittent bug that reproduces only under specific timing and looks like
data corruption rather than a concurrency bug. Cause. The guard is checked
with a single `if (!guardHolds()) wait();` instead of a `while` loop around
the same call. Both POSIX condition variables and the Java `Object.wait`
contract explicitly permit a thread to wake without any corresponding
`notify` call, and every mainstream implementation's own documentation says
so; treating a return from `wait` as proof the guard holds is a documented,
not a hypothetical, bug. Fix. Always loop on the guard, never branch on it
once, regardless of language or platform.

**Notify one when the waiters are heterogeneous.** Symptom. A system with a
`notFull` and a `notEmpty` guard sharing a single condition variable
occasionally stalls one class of waiter while the other class proceeds
repeatedly, an unfairness that grows worse under load and looks like starvation
rather than a design defect. Cause. `signal()` wakes an arbitrary one of the
waiters on the shared condition, and if the woken thread's specific guard is
not the one that just became true, it re-checks, finds its own guard still
false, and parks again, effectively wasting the wakeup. Fix. Split into
separate condition variables per guard, as dimension 8 describes, or use
`signalAll()`/`Broadcast()` at the cost of waking every waiter on every state
change, which is correct but less efficient.

**Deadlock through nested guarded calls.** Symptom. Two threads each hold one
lock and block waiting on a guard whose satisfaction requires the other
thread's lock, and the system freezes entirely, discoverable in a thread dump
as a cycle. Cause. A guarded method calls, while still holding its own lock,
into another object's guarded method that in turn needs a lock the first
thread holds, forming the classic lock-ordering cycle, except here manifested
through condition-variable parking rather than a simple mutual `lock()` call.
Fix. Never call into another guarded object while still holding the current
object's lock; release first, or restructure so the two objects share one
lock, or establish and document a strict lock acquisition order across the
whole system and verify it, ideally with a static lock-order checker.

**Missed timeout, unbounded wait on a Notifier that will never arrive.**
Symptom. A thread pool's worker threads accumulate, each parked forever on a
`take()` that has no matching `put()` because the upstream producer crashed
or was shut down without draining its consumers, and the process cannot exit
cleanly. Cause. Production code used the unbounded `wait()`/`await()` form
rather than a timed variant, on the assumption that the Notifier is always
eventually going to arrive. Fix. Default to a timed wait with an explicit,
observable timeout and a defined fallback, retry, fail the request, or alert,
and reserve the unbounded form for cases with an independent liveness
guarantee, such as a supervised, restart-on-crash producer.

**Signalling the wrong condition, or forgetting to signal at all.** Symptom.
A `put` succeeds, the queue's size genuinely increased, but no waiting
`take()` ever wakes, an intermittent stall that is easy to miss in a quick
manual test because a subsequent unrelated event, a timeout elsewhere or a
new arrival, eventually shakes the system loose and masks the bug. Cause. The
Notifier method changed the state but the call to `signal()` or `notify()`
was omitted, a copy-paste error added it to the wrong method, or it targeted
the wrong condition object in a multi-condition design. Fix. Treat every
state mutation that can make a guard true as being paired with a signal on
the condition that guard belongs to, as a compile-time-checkable invariant
where the language allows it, and as a code-review checklist item and a unit
test assertion where it does not; see dimension 15.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Guarded Suspension | Balking | Busy-wait / spin loop | Future/Promise | Semaphore | Actor mailbox |
|---|---|---|---|---|---|---|
| CPU cost while unmet | None, thread parked | None, caller returns immediately | High, spins the core | None, thread parked | None, thread parked | None, mailbox delivery is scheduler-driven |
| Correctness discipline required | High, lock plus loop plus paired signal | Low, single check-and-return | Low, but easy to spin forever by mistake | Low, library-managed | Medium, still lock-adjacent | Low, actor runtime owns it |
| Multiple, independent waiters | Well suited | Not the point, caller does not wait | Poor, contention on the flag | Poor beyond one-shot results | Well suited for counting resources | Well suited |
| Repeated preconditions (many put/take pairs) | Well suited, this is its home ground | Not suited, one-shot check | Technically works, wastes CPU | Not suited, one-shot by design | Well suited for counted resources | Well suited |
| Cross-process applicability | None, in-process only | None, in-process only | None, in-process only | Depends on implementation, often remote-capable | None, in-process only | Yes, in distributed actor systems |
| Failure surface | Lost wakeup, spurious wakeup, deadlock via nesting | Race on the boolean check itself if not atomic | Livelock, priority inversion | Broken promise, unhandled rejection | Permit leak on missing release | Mailbox unbounded growth, backpressure design needed |
| Backpressure for producers | Automatic, `put` blocks | None, producer never waits | None, no queue | None, not a queue construct | Automatic for counted resources | Requires explicit bounded mailbox |
| Fits "N is available" counting problems | Adequate but general-purpose | Poor fit | Poor fit | Poor fit | Best fit, purpose-built | Poor fit |

Reading of the table. Guarded Suspension is the general, repeated-use answer
for a shared object with a real precondition and real, possibly numerous,
waiters. Balking answers a different question, what should happen when the
precondition is not met right now and the caller does not want to wait at
all. Busy-waiting is a narrow, low-level optimisation, not a substitute.
Future/Promise is the right shape for a one-time result rather than a
recurring state transition. Semaphore is Guarded Suspension specialised to
counting, and is the better choice whenever the guard reduces to at least N
available. Actor mailboxes solve the same coordination problem at a
different, distributed granularity, and generally still need a bounded-queue
design underneath that is, itself, Guarded Suspension.

## 13. Related and incompatible patterns

- **Balking.** The closest sibling and the one most often confused with this
  pattern. Both patterns start from the same observation, a method has a
  precondition it must check before proceeding. Balking's answer is to check
  once and return immediately, typically throwing or reporting failure, if the
  condition does not hold. Guarded Suspension's answer is to wait for the
  condition to become true. Choosing between them means choosing between a
  caller who does not want to wait and a caller who is willing to wait for the
  work to happen once the state allows it.
- **Monitor Object.** The umbrella structure Guarded Suspension usually lives
  inside. A Monitor Object serializes all access to an object behind one lock
  and exposes synchronized methods; Guarded Suspension is what happens inside
  one of those methods when the method also has a precondition beyond mere
  mutual exclusion. Many languages, Java's `synchronized` plus `Object.wait`,
  give both patterns together as a single built-in feature.
- **Producer-Consumer.** The most common application of Guarded Suspension.
  A producer-consumer pipeline needs a bounded buffer whose `put` blocks when
  full and whose `take` blocks when empty, and that buffer's `put` and `take`
  are, structurally, two Guarded Suspension methods sharing one lock with
  opposite guards. `BlockingQueue`, `queue.Queue` and `BlockingCollection<T>`
  in dimension 9 are all Producer-Consumer implementations built on Guarded
  Suspension.
- **Thread-Safe Interface.** A broader design discipline that Guarded
  Suspension composes with rather than competes against. A Thread-Safe
  Interface separates the externally-visible, lock-acquiring methods from
  internal, lock-free helper methods that assume the lock is already held.
  A well-structured guarded method is usually the public half of a
  Thread-Safe Interface, calling private helpers once its guard is satisfied.
- **Read-Write Lock.** Solves a related but distinct problem, letting many
  readers proceed concurrently while writers get exclusive access. It is not
  a substitute for Guarded Suspension, because a read-write lock has no
  concept of a precondition beyond whether a writer is active; a reader that
  must wait for a specific piece of data to exist, not merely for a writer to
  finish, still needs a guard and a condition variable layered on top of, or
  instead of, the read-write lock.
- **Active Object.** Compatible and complementary at a different layer. An
  Active Object decouples method invocation from method execution by queuing
  requests and running them on a dedicated thread; the request queue inside an
  Active Object implementation is, itself, frequently a Guarded Suspension
  bounded buffer.
- **Double-Checked Locking.** Superficially similar, both check a condition,
  acquire a lock, and check again, but the intent differs. Double-Checked
  Locking exists to avoid paying the lock's cost on the common path where
  initialization has already happened; Guarded Suspension exists to make a
  thread wait for a state that has not yet arrived. Applying Double-Checked
  Locking's single re-check, rather than a `while` loop, to a Guarded
  Suspension problem is exactly the spurious-wakeup bug in dimension 11.
- **Busy-wait / spinlock.** Actively in tension with Guarded Suspension's
  goal. Where a hot, low-level path deliberately chooses to spin rather than
  park because the expected wait is a handful of instructions, it is
  explicitly rejecting the pattern for the narrow reason given in dimension 4,
  not composing with it.

## 14. Refactoring path in and out

Introducing the pattern into code that currently polls a flag or sleeps in a
loop.

1. Identify every place that reads the shared state the polling loop is
   watching, and every place that writes it. Confirm all of them already run
   under one shared lock; if they do not, this step, making them do so, must
   happen first and independently, since Guarded Suspension cannot repair a
   data race that already exists.
2. Introduce one condition variable bound to that same lock if the language
   requires an explicit one, or confirm the built-in monitor construct
   supplies one implicitly.
3. Replace the polling loop's sleep with a call to `wait`/`await` on the
   condition, still inside the same `while (!guardHolds())` shape the polling
   loop already had, only the body of the loop changes from sleeping a fixed
   interval to parking until signalled.
4. At every site identified in step 1 that writes the guarded state such that
   the guard could newly become true, add a call to `notify`/`signal` (or
   `signalAll`/`Broadcast` if more than one guard shares the condition or the
   change could satisfy more than one waiter's guard), placed while still
   holding the shared lock.
5. Add or extend tests per dimension 15 that assert the transition actually
   wakes a waiting thread within a bounded time, not merely that the state
   changed, since the polling version's tests likely only checked the latter.
6. Add a timeout to the wait if the original polling loop had an implicit
   maximum retry count, translating that bound into an explicit timed wait
   rather than dropping the bound silently.
7. Remove the sleep interval constant and any tuning comments about polling
   frequency; they no longer apply and their presence in the diff is a signal
   the refactor genuinely changed the mechanism, not merely renamed it.

Removing the pattern when a guard that used to require waiting no longer
does, typically because the underlying resource became effectively unbounded
or because the system moved to a design where the precondition is always
true by construction.

1. Confirm, with evidence rather than assumption, that the guard is now
   always true at every call site, for example because the bounded resource
   was replaced by an unbounded one, or because a prior pipeline stage now
   guarantees ordering that made the wait necessary.
2. Replace the `while (!guardHolds()) wait();` loop with a single assertion
   that the guard holds, changed from a loop condition to a defensive check
   that fails loudly, an assertion or an exception, if it is ever wrong, so a
   violated assumption is caught rather than silently reintroducing the bug
   this refactor removes.
3. Remove the `notify`/`signal` calls at the state-mutation sites, since
   nothing is parked to wake.
4. Delete the condition variable if nothing else in the object uses it.
5. Keep the shared lock if the object still has other reasons for mutual
   exclusion; only remove locking entirely if the object's access pattern has
   independently become single-threaded, which is a separate, larger claim
   that needs its own verification.

## 15. Testing and verification

Testing Guarded Suspension is harder than testing an ordinary synchronous
method, because the property under test, does the waiting thread actually
resume when and only when the guard is satisfied, is inherently about the
interaction of two threads over time, not about a single call's return value.

Easier because of the pattern.

- The precondition is centralised in one guard expression rather than
  scattered across every call site as ad hoc checks, so a single unit test on
  the guard's boolean logic covers every caller.
- Because the state mutation and the signal are required to happen under the
  same lock, a test can reliably drive the object into a specific state and
  assert the resulting wakeup, without needing to guess at timing, as long as
  the test itself also holds the discipline described below.

Harder because of the pattern.

- A test that merely calls the guarded method and asserts the returned value
  proves nothing about the waiting behaviour if the guard happened to already
  be true when the test called it; the interesting case is a caller that
  genuinely blocks first.
- A hand-rolled implementation that has a lost-wakeup or spurious-wakeup bug
  can pass every test that does not specifically provoke the race, because
  the failure is timing-dependent and single-threaded or lightly-loaded test
  runs rarely trigger it.

Techniques that apply.

- **Two-thread rendezvous test.** Start a thread that calls the guarded
  method while the guard is false, using a synchronization primitive
  independent of the pattern under test, a `CountDownLatch` or equivalent, to
  confirm the thread has actually entered the wait before the test proceeds.
  Then, from the main test thread, drive the state to satisfy the guard and
  signal, and assert the waiting thread completes within a bounded time. This
  is the single most important test for the pattern and the one most often
  skipped.
- **Multiple-waiter fairness or correctness test.** Start several threads
  blocked on the same guard, satisfy it once, and assert exactly the expected
  number of them proceed, no more, no fewer, which specifically catches the
  wrong-notify-target bug from dimension 11.
- **Timeout-path test.** Call the guarded method with a short timeout and a
  guard that will never become true within the test, and assert the method
  returns the documented timeout failure rather than hanging the test suite
  itself, which both verifies the timeout path and prevents a broken
  implementation from silently hanging CI.
- **Stress or fuzz test under a race detector.** Run many producer and
  consumer threads concurrently for a sustained period under a tool that
  detects data races on the shared state, since a lost-wakeup bug often only
  manifests statistically, not deterministically, and a single passing run
  proves nothing.
- **Deadlock-detection sanity test.** For designs where a guarded method
  might call into another guarded object, a test that intentionally exercises
  the two objects from opposite thread orderings, combined with a bounded test
  timeout that fails loudly rather than hanging, catches the nested-lock
  deadlock from dimension 11 before it reaches production.

## 16. Observability signals

Because a parked thread is, by definition, doing nothing observable through
its own return value, this pattern is one where the absence of application
logs is not evidence of health, and dedicated instrumentation is required to
tell a healthy wait from a stuck one.

What to record.

- A gauge of the current number of threads currently parked on each named
  guard, incremented when a thread enters `wait`/`await` and decremented when
  it resumes, labelled by which guarded object and which guard.
- A histogram of actual wait duration per guard, measured from the moment a
  thread enters the wait to the moment it resumes with a satisfied guard,
  which distinguishes waits that are normally near-instant from waits that
  are routinely long, a distinction a raw parked-thread count alone cannot
  make.
- A counter of timeouts, per guard, when the timed variant is used, since a
  rising timeout rate is the earliest external signal that a producer or
  Notifier has stopped signalling.
- A counter of signals sent, per guard, so it can be cross-checked against the
  parked-thread gauge; a system where signals are being sent but the parked
  count never drops is exhibiting the lost-wakeup or wrong-target-notify
  failure from dimension 11 in real time.
- For a bounded-buffer instantiation specifically, the current fill level as
  its own gauge, since fill level trending toward full or toward empty for a
  sustained period is the leading indicator of a producer-consumer imbalance
  well before any thread actually times out.

A healthy instance on a dashboard. The parked-thread gauge for each guard
tracks load, rising and falling with traffic, but returns to a low baseline
between bursts. Wait-duration histograms are tightly clustered near zero,
with a long tail only during known load spikes. The signal-sent and
parked-thread-decrement counters move together, roughly one decrement per
signal, allowing for `signalAll` fan-out where documented. Timeout counters
sit at or near zero.

A failing instance. The parked-thread gauge climbs and never returns to
baseline, which is either a genuine, sustained producer-consumer imbalance
that capacity planning must address, or a lost-wakeup bug; the signal-sent
counter tells them apart, since a lost wakeup shows signals still arriving
while the parked count refuses to drop. A wait-duration histogram that
develops a permanent long tail on one guard while others stay tight localises
the imbalance to a specific resource. A timeout counter that steps up sharply
at a specific deployment marks a regression introduced by that release and is
the single fastest way to correlate a production incident with a code change
in a system built on this pattern.

## 17. Security and privacy implications

Judgement. The specific implications below are analytical, drawn from how the
pattern is typically deployed, rather than sourced claims about a named
incident, and are stated as reasoning rather than fact for that reason.

**Denial of service via unbounded waiter accumulation.** A guarded method
with no timeout, called from a request path an external, potentially
malicious actor can trigger, lets that actor accumulate an unbounded number
of parked threads by issuing requests faster than the guard can be satisfied.
Because each parked thread typically holds a stack and a scheduler slot, this
is a resource-exhaustion vector distinct from, and in addition to, whatever
rate limiting protects the guarded resource itself. The mitigation is the
same one dimension 11 already gives for the missed-timeout failure mode, a
mandatory, bounded timeout on any guarded wait reachable from untrusted input,
combined with an explicit cap on the number of concurrent waiters the system
will admit before rejecting new requests outright.

**Timing side channel through wait duration.** A caller who can measure how
long a guarded call took to return learns something about the internal state
of the shared resource at the moment the call was made, for example, roughly
how full a queue was or how contended a resource pool was. In most
applications this is an operational curiosity rather than a security
boundary, but in a system where the guarded resource's fill level is itself
sensitive, a multi-tenant queue where knowing another tenant's queue depth
would leak business information, the wait duration is an observable side
channel that the design should account for, typically by not exposing timing
to the caller with any more precision than necessary.

**Notifier confusion as a trust boundary issue.** In a design where the code
that satisfies a guard and the code that consumes the guarded resource belong
to different trust domains, a plugin system where third-party code can act as
a Notifier on a core object's condition variable, that third-party code can
signal falsely or refuse to signal at all, either causing a legitimate waiter
to proceed against a state that a well-behaved Notifier would not yet have
declared ready, or causing a legitimate waiter to hang. Where the Notifier
role is exposed across a trust boundary, the Guard should be re-validated
independently by the guarded method itself rather than trusted purely because
a signal arrived, since the signal is only ever a hint to re-check, never
itself proof.

On broader data privacy the pattern is silent in itself. The one practical
note is the same one dimension 16 raises for observability generally. If the
guard's identifying label or the resource's name in logs and metrics can
encode a customer, tenant or user identifier, that field should be treated as
attributable data under the application's existing retention and access
rules, not as an exempt piece of internal plumbing.

## Code examples

Three languages where the pattern is genuinely idiomatic in materially
different forms. TypeScript, running under Node.js's single-threaded event
loop, shows the async/await coroutine-suspension variant, since Node.js has
no shared-memory threads for the classical lock-and-condition form to apply
to. Python shows the standard `threading.Condition` form, the direct
descendant of the Java form Doug Lea's book describes. Go shows `sync.Cond`,
matching the standard library documentation quoted in dimension 8 and
dimension 9. Java is covered at length by the `BlockingQueue`/`Condition`
citations in dimensions 8 and 9 rather than repeated here as a fourth code
sample, since the shape has already been shown verbatim from its own
documentation.

### TypeScript (Node.js, coroutine suspension)

```typescript
class GuardedBox<T> {
  private value: T | undefined;
  private hasValue = false;
  private waiters: Array<() => void> = [];

  async take(): Promise<T> {
    while (!this.hasValue) {
      await new Promise<void>((resolve) => this.waiters.push(resolve));
    }
    const result = this.value as T;
    this.hasValue = false;
    this.value = undefined;
    return result;
  }

  put(item: T): void {
    this.value = item;
    this.hasValue = true;
    const woken = this.waiters;
    this.waiters = [];
    for (const resolve of woken) resolve();
  }
}

async function demo() {
  const box = new GuardedBox<string>();
  const consumer = box.take().then((v) => console.log("took", v));
  setTimeout(() => box.put("payload"), 10);
  await consumer;
}

demo();
```

### Python (`threading.Condition`)

```python
import threading
import time


class BoundedBuffer:
    def __init__(self, capacity: int):
        self._capacity = capacity
        self._items: list[object] = []
        self._lock = threading.Condition()

    def put(self, item: object) -> None:
        with self._lock:
            while len(self._items) == self._capacity:
                self._lock.wait()
            self._items.append(item)
            self._lock.notify()

    def take(self) -> object:
        with self._lock:
            while not self._items:
                self._lock.wait()
            item = self._items.pop(0)
            self._lock.notify()
            return item


def demo() -> None:
    buf = BoundedBuffer(capacity=2)

    def consumer() -> None:
        print("took", buf.take())

    t = threading.Thread(target=consumer)
    t.start()
    time.sleep(0.05)
    buf.put("payload")
    t.join()


if __name__ == "__main__":
    demo()
```

### Go (`sync.Cond`)

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

type BoundedBuffer struct {
	mu       sync.Mutex
	cond     *sync.Cond
	capacity int
	items    []string
}

func NewBoundedBuffer(capacity int) *BoundedBuffer {
	b := &BoundedBuffer{capacity: capacity}
	b.cond = sync.NewCond(&b.mu)
	return b
}

func (b *BoundedBuffer) Put(item string) {
	b.mu.Lock()
	defer b.mu.Unlock()
	for len(b.items) == b.capacity {
		b.cond.Wait()
	}
	b.items = append(b.items, item)
	b.cond.Signal()
}

func (b *BoundedBuffer) Take() string {
	b.mu.Lock()
	defer b.mu.Unlock()
	for len(b.items) == 0 {
		b.cond.Wait()
	}
	item := b.items[0]
	b.items = b.items[1:]
	b.cond.Signal()
	return item
}

func main() {
	buf := NewBoundedBuffer(2)
	done := make(chan struct{})
	go func() {
		fmt.Println("took", buf.Take())
		close(done)
	}()
	time.Sleep(50 * time.Millisecond)
	buf.Put("payload")
	<-done
}
```

## 18. References

1. Wikipedia contributors. "Guarded suspension".
   https://en.wikipedia.org/wiki/Guarded_suspension
   Verified 2026-08-02. Source for the pattern name, its definition, the
   attribution to Doug Lea, *Concurrent Programming in Java, Second Edition*
   (Addison-Wesley, 2000), and the related Balking and Guarded Command
   Language references in dimension 1.
2. Wikipedia contributors. "Concurrency pattern".
   https://en.wikipedia.org/wiki/Concurrency_pattern
   Verified 2026-08-02. Source for Guarded Suspension's place alongside
   Balking, Monitor Object and Active Object in the Schmidt, Stal, Rohnert,
   Buschmann concurrency pattern catalog, *Pattern-Oriented Software
   Architecture, Volume 2* (Wiley, 2000), used in dimension 1.
3. Oracle. *Java SE 21 API Specification*,
   `java.util.concurrent.locks.Condition`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/locks/Condition.html
   Verified 2026-08-02. Source for the `BoundedBuffer` example, the
   two-condition-variable variant in dimension 8, and the `await`/`signal`
   contract description used throughout.
4. Oracle. *Java SE 21 API Specification*,
   `java.util.concurrent.BlockingQueue`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/BlockingQueue.html
   Verified 2026-08-02. Source for the `put`/`take` blocking contract and the
   producer-consumer production use in dimension 9.
5. Python Software Foundation. *Python 3 documentation*, `queue`.
   https://docs.python.org/3/library/queue.html
   Verified 2026-08-02. Source for `queue.Queue`'s blocking `put`/`get`
   contract used as a production use in dimension 9.
6. The Go Authors. *Go standard library documentation*, `sync.Cond`.
   https://pkg.go.dev/sync#Cond
   Verified 2026-08-02. Source for the `Wait`/`Signal`/`Broadcast` contract,
   the mandatory loop-around-`Wait` guidance, and the production use in
   dimension 9.
7. Microsoft. *.NET API documentation*,
   `System.Collections.Concurrent.BlockingCollection<T>`.
   https://learn.microsoft.com/en-us/dotnet/api/system.collections.concurrent.blockingcollection-1
   Verified 2026-08-02. Source for the bounded-capacity blocking `Add`/`Take`
   contract used as a production use in dimension 9.
