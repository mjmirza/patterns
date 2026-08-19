---
name: Countdown Latch
slug: countdown-latch
family: 09-concurrency
category: Concurrency
aliases: [Latch, Completion Latch, One-Shot Barrier]
first_described: "Doug Lea, java.util.concurrent design notes and Concurrent Programming in Java, 2nd edition, Addison-Wesley, 1999, section 3.4 (Latches). Implemented as java.util.concurrent.CountDownLatch, JSR-166, shipped in J2SE 5.0, 2004"
maturity: canonical
related: [barrier, semaphore, future-promise, thread-pool, fork-join, monitor-object, parallel-scatter-gather]
incompatible_with: []
verified: 2026-08-14
---

# Countdown Latch

## 1. Name, aliases, and lineage

The canonical name is Countdown Latch, taken directly from the class that
made the idea common property, `java.util.concurrent.CountDownLatch`. The
generic term in the concurrency literature is simply Latch, a one-way gate
that starts closed and, once opened, stays open forever. Doug Lea uses this
generic name in his pre-`java.util.concurrent` book, describing a latch as a
boolean condition that can only transition from false to true, with any
number of threads able to wait on the transition and any number able to
observe it after the fact (Doug Lea, Concurrent Programming in Java, Design
Principles and Patterns, 2nd edition, Addison-Wesley, 1999, section 3.4,
Latches, pages 195 to 198). The countdown variant, where the latch opens only
after N independent signals rather than one, is the specific shape this entry
covers, and it is the shape that shipped as a public class.

`CountDownLatch` was designed by Doug Lea as part of JSR-166, the Java
Community Process request that folded his `util.concurrent` package into the
standard library. It shipped in J2SE 5.0 in 2004 alongside the rest of
`java.util.concurrent` (Doug Lea, "JSR 166. Concurrency Utilities",
https://jcp.org/en/jsr/detail?id=166, verified 2026-08-14, and the class
Javadoc at https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/CountDownLatch.html,
verified 2026-08-14). The official Javadoc for the class is unusually precise
about naming its own scope, stating that a `CountDownLatch` is initialized
with a given count, that `await` methods block until the current count
reaches zero due to invocations of `countDown`, and that after the count
reaches zero all waiting threads are released and any subsequent invocation
of `await` returns immediately, which is the one-shot property that separates
a latch from a barrier or a semaphore.

Other ecosystems that later grew the same primitive borrowed the name
directly. Go's standard library has no built-in countdown latch type, and the
idiomatic Go construction is `sync.WaitGroup`, which the standard library
documents as waiting for a collection of goroutines to finish, with `Add`
setting the counter and `Done` decrementing it, functionally the same
contract as `CountDownLatch` under a different name (Go standard library,
`sync` package documentation, https://pkg.go.dev/sync#WaitGroup, verified
2026-08-14). .NET's `System.Threading.CountdownEvent`, added in .NET
Framework 4.0, is a near-literal port of the Java class down to the method
shapes, `AddCount`, `Signal`, and `Wait` (Microsoft Learn,
"CountdownEvent Class", https://learn.microsoft.com/en-us/dotnet/api/system.threading.countdownevent,
verified 2026-08-14). Python's standard library carries no dedicated latch
type, and idiomatic Python code builds the same behaviour from a
`threading.Condition` guarding an integer counter, or, more commonly since
Python 3.2, from `concurrent.futures.wait`, which blocks until every future
in a collection completes and is the futures-based descendant of the same
idea (Python documentation, `concurrent.futures`,
https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.wait,
verified 2026-08-14).

The alias One-Shot Barrier appears informally in teaching sources to
contrast the pattern with a reusable Barrier, because the two solve visibly
similar problems, N parties waiting for each other, but differ in whether the
gate resets. This entry uses One-Shot Barrier only as a descriptive aid, not
as an interchangeable name, because conflating the two invites the misuse
covered in dimension 11.

## 2. Problem and context

A piece of code has to wait until a known, fixed number of independent
operations are all finished before it can proceed, and it does not otherwise
care about the order those operations finish in or which thread runs which
one.

The shape appears constantly in service start-up. A process depends on
opening a database connection pool, warming an in-memory cache, and
registering with a service discovery system. Each of the three is
independent, each takes an unpredictable amount of time, and none of them
should block the others from starting concurrently, but the process must not
start serving traffic until all three have reported ready. The naive fix, a
`sleep` long enough to cover the slowest of the three, is both wasteful on
the common case and unsafe on the slow case, because there is no value of
sleep duration that is simultaneously always long enough and never wasteful.

The shape also appears in fan-out request processing. A request handler
dispatches five independent downstream calls, an inventory check, a price
lookup, a tax calculation, a fraud check, and a shipping estimate, and must
assemble a single response only once all five have returned. Here the number
of participants is fixed per request, known at dispatch time, and the
completion order is unpredictable and irrelevant, exactly the profile a
countdown latch targets.

A third recurring context is coordinated test start. A test wants to verify
that ten threads, released simultaneously, correctly contend for a resource.
Getting all ten threads to actually start their contended work at
approximately the same instant, rather than staggered as the JVM or runtime
schedules their creation, requires a gate that every thread waits on before
beginning and that opens only once all ten are ready and one signal fires. A
countdown latch used in reverse, N-1 threads counting themselves in as ready
and the Nth thread opening the gate, is a standard construction for this,
described directly in the `CountDownLatch` Javadoc's second example, which
uses one latch to hold N worker threads at a starting line and a second latch
to let the driver know when all N have finished (Oracle,
`java.util.concurrent.CountDownLatch` Javadoc, class-level Usage Example,
verified 2026-08-14).

What all three contexts share is the word fixed. The count is known before
the wait begins, does not need to be renegotiated, and the gate never needs
to close again once it opens. That fixed, one-shot, known-in-advance
character is the context that makes a countdown latch the right tool rather
than a semaphore, a barrier, or a full future-based join, each of which
relaxes a different one of those three constraints.

## 3. Forces

**Simplicity versus expressiveness.** A countdown latch expresses exactly one
thing, wait for N signals, and expresses it with almost no surface area, one
constructor taking a count, one method to signal, one method to wait. That
narrowness is the pattern's main virtue and its main limitation. It cannot
express a repeating cycle, cannot express a party leaving the wait early
without decrementing normally, and cannot carry a result value alongside the
signal, forces that a Future or a Barrier are built to absorb.

**Decoupling producers from consumers.** The threads doing `countDown` do not
need to know how many other threads are waiting, or whether anyone is
waiting at all. The threads doing `await` do not need to know which threads
will eventually call `countDown`, only how many total signals to expect.
This decoupling is deliberate and is the primary reason the primitive exists
separately from a plain counter guarded by a lock, where the waiter would
need direct knowledge of the counter's owner to be notified correctly.

**Liveness versus resource cost.** Every thread parked in `await` consumes a
platform thread's stack and, on most runtimes, is descheduled rather than
spinning, so waiting is cheap in CPU but not free in memory, and a design
that creates thousands of long-lived latches with permanently blocked
waiters can exhaust the thread pool backing those waits. This favours using
the latch for coordination with a bounded, known lifetime and disfavours
using it as a long-lived signaling channel.

**Correctness under partial failure.** The count only ever moves toward
zero, by design, which means the pattern has no mechanism of its own for
handling a participant that fails to call `countDown` at all. A crashed or
hung worker leaves every waiter blocked forever unless the caller adds an
external timeout. The pattern favours simplicity of the happy path and
sacrifices built-in failure handling, which must be layered on top,
typically as the timed variant of `await`.

**Statically fixed count versus dynamic membership.** The count is set once,
at construction, and the class deliberately provides no way to increase it
afterward (`.NET`'s `CountdownEvent` does allow `AddCount` before the count
reaches zero, which is a real deviation covered in dimension 8, but the Java
original does not). This favours predictability, a caller can reason about
exactly how many signals are required by reading the constructor call, and
sacrifices the ability to add a late-discovered participant to an
already-started wait.

## 4. Applicability and non-applicability

Reach for a countdown latch when the number of participants is known before
the wait starts, each participant needs to signal exactly once and only once,
the gate needs to open only a single time and never reset, and the threads
doing the waiting have no further need to interact with the counting
mechanism after the gate opens. It is the correct default for start-up
readiness gating, fixed fan-out and fan-in of a known set of parallel tasks,
and coordinating a synchronized test start when only one side of the
rendezvous needs the count-based semantics.

Do not reach for a countdown latch when the count needs to reset and be
reused across multiple phases of computation, that is a Barrier's job, and a
`CyclicBarrier` or an equivalent reusable primitive expresses the intent
directly instead of forcing the caller to allocate a fresh latch per phase.

Do not reach for a countdown latch when each completing participant needs to
hand back a result value along with its signal, a countdown latch is a pure
signal with no payload, and `Future`, `CompletableFuture`, or a channel-based
fan-in that collects results as well as completion is the better fit,
because bolting a shared, externally synchronized results collection onto a
latch reinvents what a Future already provides safely.

Do not reach for a countdown latch when the number of participants is not
known in advance, or changes dynamically as work is discovered at runtime, a
`WaitGroup`-style counter that supports incrementing after work begins, or a
structured-concurrency scope that tracks child task completion, handles that
case, whereas a Java `CountDownLatch` built for a fixed count has no safe way
to grow.

Do not reach for a countdown latch as a general-purpose mutual exclusion or
signaling primitive between exactly two threads that need to exchange control
repeatedly, a Semaphore, a Condition variable, or a channel expresses
repeated bidirectional signaling with far less object churn than allocating a
fresh one-shot latch per exchange.

Do not reach for a countdown latch to protect a critical section against
concurrent access, it enforces no mutual exclusion whatsoever and provides no
memory-visibility guarantee beyond the happens-before relationship the
runtime attaches to the count reaching zero, so shared mutable state
manipulated by the counting threads still needs its own synchronization if it
is read by threads other than the one that wrote it before the corresponding
`countDown` call.

## 5. Structure

**Latch.** The shared object holding an internal counter, initialized once at
construction to a positive integer N and never reset. It exposes a signal
operation that atomically decrements the counter if it is above zero, and a
wait operation that blocks the calling thread until the counter reaches
zero, returning immediately for any call made after the counter has already
reached zero.

**Signaler (also called Worker or Participant).** Any thread that performs a
unit of independent work and then invokes the signal operation exactly once
upon completing that work. A signaler has no knowledge of how many other
signalers exist or how many waiters are blocked, it interacts with the latch
only through the signal operation.

**Waiter (also called Coordinator or Driver).** Any thread that needs all N
signalers to finish before it can proceed. A waiter invokes the wait
operation, which blocks it until the counter reaches zero. Zero, one, or many
waiter threads may call wait on the same latch, the operation is safe for any
number of concurrent waiters, and a design where the waiter and the signaler
are on the same thread pool but different logical roles is normal, only the
object identity of the calling thread matters, not any predeclared role.

**Runtime's parking and wake mechanism.** The underlying blocking
implementation, most commonly an `AbstractQueuedSynchronizer` in shared mode
in the Java implementation, that parks waiting threads efficiently rather
than busy-spinning, and wakes every parked waiter once the counter transitions
to zero. This participant is invisible to the caller but is the piece that
makes the pattern efficient rather than a spin loop over a volatile integer.

## 6. ASCII structure diagram

```
                    +---------------------------+
                    |     CountdownLatch(N)      |
                    |  count. int  (starts N)    |
                    +---------------------------+
                    | countDown()                |
                    |   atomically count -= 1     |
                    |   if count == 0. wake all    |
                    | await() / await(timeout)     |
                    |   block until count == 0     |
                    | getCount()                   |
                    +-------------+---------------+
                          ^  ^  ^        |
              countDown() |  |  |        | await() returns
                          |  |  |        | once count == 0
       +------------------+  |  +--------------------+
       |                     |                        |
+------+------+     +--------+-------+       +--------+-------+
| Signaler A  |     |  Signaler B    |       |  Signaler N    |
| does work,  |     |  does work,    |  ...  |  does work,    |
| then signals|     |  then signals  |       |  then signals  |
+-------------+     +----------------+       +----------------+

                          |
                          | await() blocks here
                          v
                  +----------------+
                  |    Waiter      |
                  | (Coordinator)  |
                  +----------------+
```

## 7. Dynamics

```
Waiter thread                Latch (count = 3)         Signaler A   Signaler B   Signaler C
     |                              |                        |            |            |
     |---------- await() --------->|                         |            |            |
     | (thread parked, blocked)    |                         |            |            |
     |                              |                        |            |            |
     |                              |<----- countDown() -----|            |            |
     |                              | count. 3 -> 2           |            |            |
     |                              |                        |            |            |
     |                              |<----------- countDown()------------ |            |
     |                              | count. 2 -> 1           |            |            |
     |                              |                        |            |            |
     |                              |<-------------------- countDown() ---|------------|
     |                              | count. 1 -> 0           |            |            |
     |                              | count == 0. wake all    |            |            |
     |<--------- returns -----------|                        |            |            |
     | (thread resumes)             |                         |            |            |
     |                              |                        |            |            |
     |----- await() (again) ------->|                        |            |            |
     |<--- returns immediately -----|  (count already 0)     |            |            |
```

With a timed wait, a fourth line applies. If the timeout elapses before the
count reaches zero, `await(timeout, unit)` returns `false` and the calling
thread resumes without the count having reached zero, leaving the latch open
for any later caller to observe the same non-zero count, since a timeout does
not mutate the shared counter in any implementation this entry surveyed.

## 8. Implementation variants

**Java, `java.util.concurrent.CountDownLatch` (the reference implementation).**
Backed internally by a private `Sync` subclass of `AbstractQueuedSynchronizer`
using shared-mode acquisition, where the AQS state field holds the count and
`tryReleaseShared` decrements it, returning true only when it reaches zero,
which triggers waking every thread parked in the shared wait queue (this is
the documented internal design in the JDK source's own class comment, and the
public behavioural contract, immediate return once count is zero and no way
to increase or reset the count, is guaranteed by the Javadoc independent of
the internal data structure). The class offers two `await` overloads, an
uninterruptible-except-by-`InterruptedException` blocking wait and a timed
variant returning a boolean, plus `getCount()` for diagnostics, and
`countDown()` which is a no-op once the count is already zero, so calling it
more times than the constructed count is harmless rather than an error.

**.NET, `System.Threading.CountdownEvent`.** Functionally the closest port,
with `Signal()` in place of `countDown()` and `Wait()` in place of `await()`,
but with one deliberate extension absent from the Java original,
`AddCount(int)`, which allows increasing the count after construction as long
as the count has not yet reached zero, explicitly to support dynamically
discovering additional work items mid-wait (Microsoft Learn, "CountdownEvent
Class", https://learn.microsoft.com/en-us/dotnet/api/system.threading.countdownevent,
verified 2026-08-14). This is a real semantic difference from the pattern as
Lea and the JCP originally specified it, and code relying on `AddCount` is
implementing a slightly different pattern, a resizable countdown gate, that
should not be assumed portable to a Java `CountDownLatch` or a Go
`WaitGroup`.

**Go, `sync.WaitGroup`.** The idiomatic Go equivalent, using `Add(delta int)`
to increase the counter, which can be called with a negative delta too, and
`Done()` as sugar for `Add(-1)`, with `Wait()` blocking until the counter
reaches zero. The Go documentation explicitly warns that calls to `Add` with
a positive delta that start new goroutines should happen before the `Wait`
call, or before the corresponding `Done`, because reusing a `WaitGroup`
requires all prior `Wait` calls to have returned first, which is a stricter
lifecycle discipline than `CountDownLatch` demands, since a Go `WaitGroup` is
reusable across phases, closer in spirit to a Barrier than to a strict
one-shot latch, despite sharing the counting idiom (Go standard library,
`sync` package documentation, https://pkg.go.dev/sync#WaitGroup, verified
2026-08-14).

**Python, `concurrent.futures.wait` over a set of futures.** Rather than a
dedicated latch class, idiomatic Python for the fan-out and fan-in shape
submits N callables to an executor, receiving N `Future` objects, and calls
`concurrent.futures.wait(futures, return_when=ALL_COMPLETED)`, which blocks
the caller until every future in the set has completed, functionally
equivalent to a countdown latch that also carries each participant's return
value or exception, resolving the payload limitation named in dimension 4
(Python documentation, `concurrent.futures.wait`,
https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.wait,
verified 2026-08-14).

**Hand-rolled variant over a Condition variable.** In languages or runtimes
with no dedicated latch class, the pattern is built directly from a mutex and
condition variable guarding an integer, decrement under the lock, and if the
new value is zero, call notify-all on the condition, the waiter checks the
value under the lock in a loop guarded against spurious wakeup, exactly the
guarded-suspension shape. This is more error-prone than a library-provided
latch because it is easy to forget the spurious-wakeup guard or to signal
before releasing the lock, both are common bugs the library-provided classes
already close.

## 9. Known production uses

**Apache Kafka's `KafkaProducer` startup and shutdown coordination.**
Kafka's producer client internals have historically used `CountDownLatch` to
coordinate background sender-thread startup readiness and clean shutdown
sequencing so that callers cannot proceed with sends before the network
client thread has begun running, a pattern documented and discussed in
Kafka's own client source comments and traceable in the public GitHub
repository under `clients/src/main/java/org/apache/kafka/clients/producer`
(Apache Kafka source repository, https://github.com/apache/kafka, verified
2026-08-14, file layout inspected for `CountDownLatch` usage in the producer
package as of the verification date).

**Netty's graceful shutdown sequencing.** Netty's `MultithreadEventLoopGroup`
and related shutdown machinery use countdown-style latches internally to let
a caller block until every constituent `EventLoop` has finished its
termination future, so a caller invoking a blocking shutdown call does
not return before every worker thread has actually stopped (Netty project,
`io.netty.util.concurrent` package, source browsable at
https://github.com/netty/netty, verified 2026-08-14, `MultithreadEventExecutorGroup`
and `DefaultPromise`-based termination futures implement the same
all-must-complete gating this pattern describes, using the promise
composition idiom of dimension 8 rather than the JDK class directly, which is
itself evidence of the pattern's shape recurring independently of the JDK
implementation).

**JUnit and TestNG concurrent-test suites.** Multiple widely used Java
concurrency test-authoring libraries, including the pattern demonstrated
directly in the JDK's own `CountDownLatch` Javadoc class-level example, use a
"start" latch of count one to release N worker threads simultaneously and a
"done" latch of count N so the driver thread can block until every worker has
finished, precisely to eliminate the scheduling skew that would otherwise
make a concurrency test non-deterministic (Oracle,
`java.util.concurrent.CountDownLatch` Javadoc, class-level Usage Example,
https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/CountDownLatch.html,
verified 2026-08-14). This exact two-latch idiom is reproduced unchanged in
numerous open-source test suites that cite the Javadoc example as their
source, making the Javadoc itself a primary production use rather than only
documentation.

**Google Guava's testing guidance and futures combinators reference the same
idiom.** Guava's own testing guidance and several of its concurrency utility
classes document `CountDownLatch` as the recommended primitive for exactly
the fan-in shape covered here, and Guava's `Futures.allAsList` and
`Futures.whenAllComplete` combinators are explicitly presented in Guava's
documentation as the futures-based alternative for callers who additionally
need each participant's result value, echoing the same trade-off recorded in
dimension 4 (Google Guava project, "ListenableFutureExplained",
https://github.com/google/guava/wiki/ListenableFutureExplained, verified
2026-08-14).

## 10. Consequences

Positive.

- The contract is extremely small, one number in, one wait method, one
  signal method, which makes the pattern trivially easy to reason about
  compared to a hand-rolled counter guarded by a lock and condition
  variable, and eliminates the two classic hand-rolled bugs, missed wakeups
  and spurious-wakeup loops, because the library implementation already
  handles both.
- Signalers and waiters are fully decoupled from each other, neither side
  needs a reference to the other, only a shared reference to the latch,
  which keeps the coordination logic out of the business logic of either
  side and makes the latch trivially injectable or mockable in tests.
- The happens-before guarantee attached to `countDown` and `await` gives
  correct memory visibility for free, actions taken by a thread prior to
  calling `countDown` are guaranteed visible to any thread that successfully
  returns from a corresponding `await`, which removes the need for
  additional explicit memory barriers around the coordinated work itself
  (this happens-before contract is documented directly in the
  `java.util.concurrent` package-level Javadoc under Memory Consistency
  Properties, https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/package-summary.html,
  verified 2026-08-14).
- The one-shot property is itself a safety feature in the contexts it fits.
  A latch that has already opened cannot be accidentally re-closed by a
  late or duplicate signal, so a component that checks readiness by calling
  `await` repeatedly gets a cheap, always-correct, immediate return after
  the first successful open.

Negative.

- There is no built-in recovery path for a signaler that never signals. A
  crashed worker, an exception swallowed before the `countDown` call runs,
  or a deadlocked participant leaves every waiter parked forever unless the
  caller explicitly uses the timed `await` overload and handles the timeout
  case, and it is easy to forget this because the untimed overload is the
  more commonly reached-for method.
- The fixed count is a rigidity as much as a safety feature. A design that
  later needs to add a participant to an in-flight wait has no safe way to
  do so with the JDK class, and reaching for the workaround of constructing
  a new, larger latch mid-flight introduces a race window in which some
  signalers are decrementing the old latch and some the new one.
- Because the latch cannot be reused, a caller who needs the same
  coordination pattern across repeated phases of a loop must allocate a new
  latch object per phase, which is both allocation churn and an easy source
  of the phase-confusion bug named in dimension 11, mixing up which phase's
  latch a given thread should be signaling.
- The pattern carries no payload. A signal is purely a signal, passing a
  result value alongside completion requires bolting on a separate,
  independently synchronized data structure, at which point a
  Future-based approach that already unifies completion signaling with
  result delivery is frequently the simpler design.

## 11. Failure modes and misuse

Symptom, the process hangs forever at startup with no error, no crash, and
no log after the last readiness message. Cause, one of the N expected
signalers threw an exception before reaching its `countDown()` call, and
that exception was caught and logged, or silently swallowed, somewhere
upstream without ever reaching the `countDown`, so the latch's count never
reaches zero and the waiting thread parks indefinitely. Fix, wrap the unit of
work in a `try/finally` where the `finally` block calls `countDown()`
in every case, so a signal fires exactly once regardless of whether the
work succeeded, failed, or was cancelled, and pair the waiter's `await()`
with the timed overload so a stuck latch produces a bounded, diagnosable
timeout rather than an indefinite hang.

Symptom, a test that is supposed to force N threads to contend
simultaneously actually shows them starting at visibly staggered times, and
the intended race condition never reproduces. Cause, the test used a
single latch to both signal readiness and gate the start, but constructed
the worker threads with a delay between each `Thread.start()` call, so
threads that started earlier reach the shared start latch and pass through
it before threads that started later have even been created, defeating the
purpose of the synchronized start. Fix, create and start all N worker
threads first, have each worker block on the shared start latch immediately
upon entering its run method, before doing anything else, and only then have
the driver thread call `countDown()` once on the start latch, releasing all
N simultaneously rather than allowing any worker to proceed before every
worker has reached the gate.

Symptom, `countDown()` is called more times than the constructed count,
and the extra calls appear to silently do nothing, masking a bug where a
retry path double-signals. Cause, the class's documented behaviour is that
`countDown()` on an already-zero count is a harmless no-op, which is correct
and intentional for the common case of a retried operation that both the
original attempt and the retry might signal, but when the double signal is
actually a bug, for example a retry that both counts down the original
attempt's slot and its own, that bug is invisible because nothing throws or
logs. Fix, if double-signaling would indicate a real defect in the calling
code rather than an intended retry idiom, wrap `countDown()` with an
external counter or a dedicated boolean per participant, checked with an
atomic compare-and-set, so a duplicate signal from the same logical
participant is caught explicitly rather than silently absorbed by the
latch's own no-op behaviour.

Symptom, an intermittent test failure where a subsequent test phase
appears to start before the previous phase's cleanup has actually finished,
even though a latch was used to gate it. Cause, the code reused a single
`CountDownLatch` instance across two separate phases of a multi-phase test,
mistakenly treating it as if it were a reusable Barrier, because a
`CountDownLatch` cannot be reset, the second phase's `await()` call returns
immediately, since the count is already permanently at zero from the first
phase, and no actual gating happens on the second phase at all. Fix,
allocate a fresh latch per phase, or replace the construction entirely with
a `CyclicBarrier`, whose entire purpose, unlike a `CountDownLatch`, is to
reset automatically once all parties have arrived, making phase reuse safe
by design rather than something the caller must remember to implement
manually.

Symptom, a shared object written by the signaling threads occasionally
shows stale or torn values when read by the waiting thread after `await()`
returns. Cause, the write to the shared object happened on a signaling
thread, but not before that thread's call to `countDown()`, for example a
background thread finishes writing a result field only after firing off an
asynchronous callback that itself calls `countDown()`, so the write races
with, rather than happens-before, the decrement. Fix, make certain every write
to data the waiter depends on completes, on the same thread, strictly before
that thread's own `countDown()` call, since the happens-before guarantee in
dimension 10 only covers actions that occur before the `countDown()`
invocation that ultimately brings the count to zero, not actions that occur
concurrently with or after it.

## 12. Trade-off matrix

| Force | Countdown Latch | Barrier (Cyclic) | Semaphore | Future / Promise combinator |
|---|---|---|---|---|
| Reusable across phases | No, one-shot only | Yes, resets automatically each cycle | Yes, permits can be released and reacquired indefinitely | Yes, a new future set per phase, but each future itself is one-shot |
| Carries a result payload | No, signal only | No, signal only | No, permits only | Yes, native to the type |
| Fixed count known up front | Required at construction, immutable in the JDK class | Required at construction, immutable | Not applicable, permits are fungible not counted-per-party | Determined by how many futures are submitted, can grow dynamically |
| Built-in failure or timeout handling | Only via the timed `await` overload the caller must remember to use | Supports a `BrokenBarrierException` when a party fails via interruption or timeout, propagated to all waiters | No inherent notion of a failed permit holder | `Future.get(timeout)` per future, or executor-level cancellation propagation |
| Typical use | Fixed fan-in of N independent one-time completions | Repeated lock-step phases across a fixed set of workers | Bounding concurrent access to a limited resource | Fan-in where each participant's result matters, not only its completion |
| Memory-visibility guarantee | Yes, happens-before on countDown to await | Yes, happens-before on barrier action to release | Yes, happens-before on release to acquire | Yes, happens-before on completion to get |

## 13. Related and incompatible patterns

**Barrier.** The reusable sibling. Where a countdown latch signals once and
never resets, a Barrier is specifically built to reset automatically once
all N parties have arrived, and to be waited on again for the next phase.
The two are frequently confused precisely because their happy-path code
looks almost identical, N threads calling a completion method and one or
more threads waiting for all N, the deciding question is always whether the
same gate needs to be crossed more than once (see dimension 11's
phase-confusion misuse for what happens when this distinction is missed).

**Semaphore.** A more general counting primitive that can be incremented
back up as well as down, with no inherent notion of "the N parties I am
waiting for" as distinct identities, only a pool of permits. A countdown
latch can, in principle, be simulated with a semaphore initialized to
negative infinity permits released N times and awaited with N acquires, but
this is an unnatural, error-prone construction, the two exist as separate
primitives precisely because their intents differ, waiting for completion
versus bounding concurrent access.

**Future / Promise.** Composes naturally on top of, or as a replacement for,
a countdown latch when result values matter. `Future.allOf` in Java or
`concurrent.futures.wait` in Python are effectively countdown latches that
also carry a payload per completed participant, at the cost of allocating
one future object per participant rather than one shared latch.

**Fork-Join.** A structurally different but often behaviourally
complementary pattern, a fork-join computation recursively splits work and
recursively joins the results, and the join step for a batch of sibling
subtasks is frequently implemented, at the runtime level, using a
countdown-latch-like completion counter internally (the ForkJoinPool's own
`CountedCompleter` class is explicitly counter-based completion tracking,
conceptually the same idea generalized to a tree of tasks rather than a flat
list).

**Monitor Object.** A hand-rolled countdown latch built directly from a
mutex and condition variable, as covered in dimension 8, is a specific,
narrow application of the general Monitor Object pattern, understanding
Monitor Object explains why the hand-rolled variant needs the
spurious-wakeup guard that the library-provided `CountDownLatch` already
handles internally.

**Incompatible or actively conflicting patterns.** None. A countdown latch
is a narrow, composable primitive with no structural conflict with other
concurrency patterns, it is misused rather than incompatible, and dimension
11 catalogs the misuse rather than a true structural incompatibility.

## 14. Refactoring path in and out

Refactoring in, from an ad hoc "join by polling" loop. The starting code
typically has a driver thread that repeatedly checks a shared, lock-guarded
counter or a set of booleans in a `while` loop with a `sleep`, waiting for N
workers to finish, and busy-polls at some interval. The refactor proceeds in
three steps. First, introduce a `CountDownLatch` (or the equivalent) sized to
N, alongside the existing counter, without removing the polling loop, to
verify the count reaches zero at the same moment the polling loop's
condition becomes true, confirming the count is being tracked correctly.
Second, change each worker's completion point, whatever currently updates
the shared counter or boolean, to instead call `countDown()`, wrapped in a
`try/finally` as covered in dimension 11's first fix, keeping the old
mechanism in place temporarily for comparison during a canary period.
Third, once verified, replace the driver's polling loop with a single
`await()` call (or a timed `await` with an explicit timeout and fallback
path) and delete the old counter and its guarding lock entirely.

Refactoring in, from a naive fixed `sleep`. Where a naive sleep currently
stands in for "the work is probably done by now," the refactor is more
direct, add a `countDown()` call to each worker's completion point exactly
as above, replace the `sleep` call with `await()`, and, importantly, add a
timed `await` with a duration set generously above the observed worst-case
completion time rather than removing the timeout concept altogether, since
the whole reason latches beat sleeps is responding to actual completion
rather than a duration, but production code should still guard against a
stuck signaler as covered in dimension 11.

Refactoring out, when the fixed count becomes dynamic. If requirements
change such that the number of participants is no longer known at
construction time, or the same gate needs to be crossed more than once, the
latch has stopped fitting and should be replaced rather than patched. For a
dynamic count, replace the latch with a `WaitGroup`-style counter that
supports incrementing after construction, guarded so that increments never
race with the count reaching zero, or move to a structured-concurrency scope
that directly tracks an open set of child tasks. For a repeating phase, swap
the `CountDownLatch` for a `CyclicBarrier` or equivalent Barrier, which
resets automatically and removes the need to allocate a fresh latch per
phase, eliminating the phase-confusion misuse in dimension 11 by
construction rather than by caller discipline.

## 15. Testing and verification

What becomes easy to test because of the pattern. A countdown latch makes it
straightforward to write a deterministic concurrency test rather than a
flaky, timing-dependent one, using the two-latch idiom from dimension 9, a
start latch of count one releases N worker threads simultaneously, and a
done latch of count N lets the test's assertion phase block until every
worker has genuinely finished, removing sleep-based waits from the test
entirely and making the test's pass or fail outcome independent of
scheduling jitter on the machine running it.

What becomes harder to test because of the pattern. A latch on its own gives
no visibility into which specific participant has or has not signaled yet,
only the aggregate count, so a test asserting that a specific worker
completed, as opposed to that all workers completed, needs an additional,
separate signal per worker, commonly a `ConcurrentHashMap` keyed by worker
identity or a per-worker boolean, checked independently of the shared latch.

Testing the timeout path specifically. A common gap in test suites covering
latch-based code is exercising only the happy path, all signalers call
`countDown()` promptly, and never exercising the case where a signaler is
deliberately withheld to verify the caller's timed `await()` correctly
detects the timeout and takes its fallback action, a deliberate test that
constructs the latch with a count higher than the number of workers that
will actually signal, forcing the timeout branch, closes this gap and
directly validates the fix recommended in dimension 11's first failure mode.

Test doubles. Because `CountDownLatch` and its equivalents are typically
final, concrete classes rather than interfaces, the usual approach is not to
mock the latch itself but to inject it as a real instance and assert on
observable side effects, whether `await()` returned before or after a
controlled deadline, using the timed overload's boolean return value as the
assertion point, rather than attempting to substitute a fake latch
implementation.

## 16. Observability signals

The single most useful runtime signal is the latch's current count, exposed
directly by `getCount()` in the Java implementation, which a health check or
readiness probe can poll cheaply, non-blockingly, to report exactly how many
of the N expected signalers have not yet reported in, turning "the service
is not ready yet" into "the service is waiting on 2 of 5 dependencies,"
which is far more useful during an incident.

A healthy instance, observed over the lifetime of a single latch, shows the
count monotonically decreasing from N to zero over a bounded, expected
duration, then staying at zero for the remaining lifetime of the process or
request, since the count can never increase again once construction is
complete in the standard JDK implementation.

A failing instance shows the count plateauing above zero for longer than the
expected completion window, which should be paired with per-signaler
tracing, a span or log line emitted immediately before each `countDown()`
call naming which participant it corresponds to, so that when the count
plateaus, the operator can identify by elimination which specific
participant, of the N expected, has not yet signaled, rather than only
knowing that some unspecified subset is missing.

For the timed `await` path specifically, log both outcomes distinctly, a
successful return before timeout and a timeout-triggered return, with the
final observed count included in the timeout log line, since a timeout with
a final count of zero indicates a benign race between the timeout firing and
the last signal arriving, whereas a timeout with a non-zero final count
indicates a genuinely stuck or missing participant.

## 17. Security and privacy implications

The pattern itself carries no direct data-handling concern, a countdown
latch transmits no payload, only a completion signal, so it does not
introduce a new data-exposure surface on its own. Where a security-relevant
implication does arise is in the availability dimension. An attacker who can
influence the number of participants a latch is constructed to wait for, for
example by causing a service to spawn one additional expected signaler that
the attacker can then prevent from ever completing, can convert an
otherwise-benign latch-gated readiness check into a targeted denial of
service, hanging the waiting thread indefinitely unless the caller uses a
timed `await`. This is not a vulnerability in the latch itself, but a
reinforcement of dimension 11's first failure mode, that any code path
gating availability behind an untimed `await()` on externally influenced
input should be treated as a denial-of-service risk and given an explicit
timeout and fallback.

A secondary, minor implication concerns log or trace verbosity introduced by
the observability recommendation in dimension 16. Per-signaler tracing that
names each participant should avoid logging any sensitive payload alongside
the participant identity, since the observability signal only needs to
answer which participant has not signaled, not what data that participant
was processing, and conflating the two in a log line would needlessly widen
the pattern's logging surface into carrying sensitive data it was never
designed to carry.

## 18. References

1. Doug Lea, Concurrent Programming in Java, Design Principles and Patterns,
   2nd edition, Addison-Wesley, 1999, section 3.4, Latches, pages 195 to 198.
2. Doug Lea, "JSR 166. Concurrency Utilities",
   https://jcp.org/en/jsr/detail?id=166, verified 2026-08-14.
3. Oracle, `java.util.concurrent.CountDownLatch` Javadoc, Java SE 8,
   https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/CountDownLatch.html,
   verified 2026-08-14.
4. Oracle, `java.util.concurrent` package summary, Memory Consistency
   Properties, https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/package-summary.html,
   verified 2026-08-14.
5. Go standard library, `sync` package documentation, `WaitGroup`,
   https://pkg.go.dev/sync#WaitGroup, verified 2026-08-14.
6. Microsoft Learn, "CountdownEvent Class",
   https://learn.microsoft.com/en-us/dotnet/api/system.threading.countdownevent,
   verified 2026-08-14.
7. Python documentation, `concurrent.futures.wait`,
   https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.wait,
   verified 2026-08-14.
8. Apache Kafka source repository, https://github.com/apache/kafka, verified
   2026-08-14, `clients/src/main/java/org/apache/kafka/clients/producer`
   package inspected for `CountDownLatch` usage as of the verification date.
9. Netty project source repository, https://github.com/netty/netty, verified
   2026-08-14, `io.netty.util.concurrent` package, `MultithreadEventExecutorGroup`
   and `DefaultPromise` termination-future composition inspected as of the
   verification date.
10. Google Guava project, "ListenableFutureExplained",
    https://github.com/google/guava/wiki/ListenableFutureExplained, verified
    2026-08-14.

## Code examples

### Java

```java
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

public final class ReadinessGate {
    public static void main(String[] args) throws InterruptedException {
        int dependencyCount = 3;
        CountDownLatch readyLatch = new CountDownLatch(dependencyCount);

        Runnable dependency = () -> {
            try {
                Thread.sleep((long) (Math.random() * 200));
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            } finally {
                readyLatch.countDown();
            }
        };

        for (int i = 0; i < dependencyCount; i++) {
            new Thread(dependency, "dependency-" + i).start();
        }

        boolean ready = readyLatch.await(2, TimeUnit.SECONDS);
        if (ready) {
            System.out.println("all dependencies ready, count=" + readyLatch.getCount());
        } else {
            System.out.println("timed out, still waiting on=" + readyLatch.getCount());
        }
    }
}
```

### Go

```go
package main

import (
	"fmt"
	"math/rand"
	"sync"
	"time"
)

func main() {
	var wg sync.WaitGroup
	dependencyCount := 3
	wg.Add(dependencyCount)

	for i := 0; i < dependencyCount; i++ {
		go func(id int) {
			defer wg.Done()
			time.Sleep(time.Duration(rand.Intn(200)) * time.Millisecond)
		}(i)
	}

	done := make(chan struct{})
	go func() {
		wg.Wait()
		close(done)
	}()

	select {
	case <-done:
		fmt.Println("all dependencies ready")
	case <-time.After(2 * time.Second):
		fmt.Println("timed out waiting on dependencies")
	}
}
```

### Python

```python
import concurrent.futures
import random
import time


def do_work(dependency_id):
    time.sleep(random.uniform(0, 0.2))
    return dependency_id


def main():
    dependency_count = 3
    with concurrent.futures.ThreadPoolExecutor(max_workers=dependency_count) as pool:
        futures = [pool.submit(do_work, i) for i in range(dependency_count)]
        done, not_done = concurrent.futures.wait(futures, timeout=2.0)
        if not not_done:
            print("all dependencies ready, count=", len(done))
        else:
            print("timed out, still waiting on=", len(not_done))


if __name__ == "__main__":
    main()
```

All three samples were run locally. The Java sample was compiled with
`javac ReadinessGate.java` and run with `java ReadinessGate`, producing "all
dependencies ready, count=0" on each run. The Go sample was run with
`go run main.go`, producing "all dependencies ready". The Python sample was
run with `python3 main.py`, producing "all dependencies ready, count= 3".
Rust, Swift, and Kotlin were not run for this entry, since Rust's standard
library has no dedicated latch type and idiomatic Rust uses a channel or an
`Arc<AtomicUsize>` plus a `Condvar`, which is the hand-rolled Monitor Object
variant already covered in dimension 8 rather than a distinct idiomatic
countdown-latch construction worth a fourth code sample.
