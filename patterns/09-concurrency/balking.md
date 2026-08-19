---
name: Balking
slug: balking
family: 09-concurrency
category: Concurrency
aliases: [Balk Pattern, Guard-and-Bail]
first_described: "Grand 2002 (Patterns in Java, Volume 1, John Wiley & Sons), documented independently in concurrency folklore through the 1990s"
maturity: established
related: [guarded-suspension, double-checked-locking, monitor-object, thread-safe-interface, scoped-locking]
incompatible_with: []
verified: 2026-08-14
---

## 1. Name, aliases, and lineage

Balking is the pattern of checking an object's state before performing an
action and, when that state is wrong for the action, simply refusing to do the
work rather than waiting, retrying, or queuing the caller. The name comes from
the ordinary English sense of a horse balking at a jump, it plants its feet
and will not go, and it does not wait around to be persuaded later. A method
that balks returns immediately, usually with a signal that nothing happened,
a boolean, an exception, a no-op, and leaves the decision of what to do next
entirely to the caller.

The most commonly cited written source for the name and the worked example is
Mark Grand's *Patterns in Java, Volume 1*, published by John Wiley and Sons in
2002, which documents the pattern with a Java example built around a
synchronized boolean guard on a `job()` method. The pattern is older than that
book as a piece of concurrency folklore. it is a direct restatement, in a
concurrent setting, of the classical guard clause and the defensive
programming habit of checking preconditions before doing work, and variants of
it appear throughout the C and POSIX threading literature of the 1990s under
no fixed name at all, simply as "check the flag first." Doug Lea's
*Concurrent Programming in Java, Second Edition* (Addison-Wesley, 1999)
discusses the same shape as one half of a pair with Guarded Suspension in its
treatment of state-dependent action, without using the word "balking" as a
formal pattern name, which is one reason different books and blog posts refer
to this idea by slightly different names while describing the identical
structure.

Balking is frequently grouped with the concurrency patterns catalogued in
Douglas Schmidt, Michael Stal, Hans Rohnert, and Frank Buschmann's
*Pattern-Oriented Software Architecture, Volume 2, Patterns for Concurrent and
Networked Objects* (Wiley, 2000), because it shares that book's vocabulary of
guarded state transitions, but POSA2 itself does not carry a chapter titled
Balking, its closest relatives there are the Monitor Object pattern, this
entry's structural chassis, and Guarded Suspension's cousin idea of
state-dependent activation. This entry treats Balking as its own named
pattern, distinct from Guarded Suspension, on the strength of the one design
decision that actually separates them. what the guarded method does when the
state check fails.

## 2. Problem and context

An object exposes an operation that is only meaningful, or only safe, in a
subset of the object's possible states. A `save()` method makes no sense while
a save is already in progress. A `connect()` call is redundant on a connection
that is already open. A `refresh()` triggered by a UI gesture should not stack
five refresh cycles on top of each other because the user tapped the button
five times while impatient. In every one of these cases, the wrong-state
invocation is not a bug in the caller in any meaningful sense. it is an
ordinary, expected event that happens because the caller does not, and often
cannot, know the object's current internal state before making the call.

The naive fix is to make the wrong-state call illegal and enforce that by
convention, documentation, or a precondition check that throws. That works
when a single thread of control owns the object and can be trusted to check
`isBusy()` before calling `save()`. It stops working the moment two threads,
two async tasks, or two independent event handlers can both decide to call
`save()` at nearly the same instant. Between the caller's `isBusy()` check and
its subsequent `save()` call, another thread can flip the state, and now two
saves race. The check and the action must become one atomic unit, performed
inside the object itself, not spread across the object's public interface and
the caller's private logic. That is the concurrency problem Balking exists to
solve, collapsing "check the state, then maybe act" into a single indivisible
step that lives where the state lives.

The pattern's natural home is any long-running or expensive operation that has
an obvious idle-busy or open-closed shape, invoked from a context where
duplicate or premature invocations are common and harmless to simply drop. It
shows up in resource lifecycle methods (open, close, start, stop), in
debounced or throttled UI actions, in idempotent background jobs, and in state
machines where a transition attempted from the wrong source state should be a
silent no-op rather than an error that has to propagate up a call stack.

## 3. Forces

Balking sits at the intersection of a handful of pressures that pull in
different directions, and naming them explicitly is what separates a
deliberate use of the pattern from an accidental one.

Correctness under race, versus simplicity of the check. The whole reason
Balking needs a lock, an atomic compare-and-swap, or an equivalent primitive
is that a plain read-then-branch is not atomic across threads. The pattern
trades a small amount of synchronization overhead for the guarantee that only
one caller's action actually proceeds when several race to invoke it at once.

Responsiveness versus completeness. A balking method never blocks the
caller. it answers instantly, either by doing the work or by declining. That
is a strength when the caller has better things to do than wait, a UI thread,
a scheduler loop, and a weakness when the caller actually needs the operation
to happen and now has to implement its own retry policy on top.

Silent drop versus loud failure. Balking's defining choice is to make the
declined call cheap and unremarkable rather than exceptional. That is correct
when the declined call is genuinely redundant, a second `save()` while one is
already running achieves nothing a caller could not get by waiting for the
first. It is the wrong choice when the declined call represents lost work the
caller cannot recover, such as a balked `enqueue()` that silently drops a
message the sender assumed was delivered.

Coupling to the object's internal state machine. Balking methods must
know, precisely, which states permit the action, and that knowledge tends to
live inside the guarded object rather than being expressed as an explicit,
separately testable state machine. This keeps the object's public surface
small but makes the legal-state logic harder to see and to test in isolation
as the number of guarded methods grows.

Cost of the guard versus cost of the guarded work. When the guarded
operation is cheap, the synchronization overhead of the guard itself can
dominate the total cost, which argues for a lock-free flag, an atomic
compare-and-swap, over a full lock. When the guarded operation is expensive
and long-running, the guard's own cost is noise, and a coarser lock is fine.

Balking deliberately favors responsiveness and idempotent-drop semantics over
strict completeness and loud failure. it is the right pattern exactly when a
declined call is truly a no-op from the caller's point of view, and the wrong
pattern the moment a declined call represents lost intent.

## 4. Applicability and non-applicability

Reach for Balking when all of the following hold, the guarded operation has a
clear precondition expressible as a boolean or small enum state, a caller
invoking the operation while that precondition is false gains nothing by
waiting for it to become true (the in-flight operation, once it completes,
already achieves what the caller wanted), duplicate concurrent invocations
must be prevented rather than merely discouraged, and the caller can sensibly
treat "declined" as a legitimate outcome rather than an error.

Concretely this covers guarding against re-entrant `save()`, `flush()`,
`refresh()`, `start()`, `stop()`, or `connect()` calls, deduplicating
UI-triggered actions where a repeated tap or keypress should collapse into the
in-flight operation, protecting a resource-initialization step from running
twice, and any lifecycle transition method on a state machine where an
out-of-order call is a caller mistake that costs nothing to ignore.

Do NOT reach for Balking under any of these conditions.

- The caller genuinely needs the operation to eventually happen and cannot
  tolerate it being silently dropped. Use Guarded Suspension instead, which
  makes the caller wait for the precondition rather than declining the call,
  or use a queue with backpressure so the intent is preserved rather than
  discarded.
- The declined outcome needs to carry information back to the caller beyond a
  boolean, such as why it was declined, what state the object is actually in,
  or when to retry. A silent boolean return under-communicates in this case,
  prefer a richer result type or an explicit state query API.
- The precondition check is expensive relative to the guarded action, in which
  case the synchronization overhead of the guard swamps any benefit and a
  coarser lock around the whole operation, without a separate balk check, is
  simpler and no slower.
- The object's legal states form a graph with many transitions rather than a
  simple busy-idle flag, and multiple methods each need their own balk logic.
  At that point a first-class state machine, an explicit state field with a
  transition table validated centrally, communicates the rules far better
  than several ad hoc boolean guards scattered across methods, and is easier
  to test.
- Retrying automatically would be both safe and desirable. if the caller would
  spin-retry after a balk anyway, a bounded internal retry or a queue
  with a worker consuming it is usually a better fit than pushing the retry
  loop onto every caller.
- The action is not actually re-entrant-unsafe. adding a balk guard to a
  method that was already safe to call concurrently, because it is naturally
  idempotent, or because the underlying resource already serializes access,
  adds complexity without a matching benefit.

## 5. Structure

A Balking implementation has four participants, though in the simplest cases
two of them collapse into the same object.

The guarded object owns the state that determines whether the action is
legal, most commonly a boolean flag such as `inProgress` or `isOpen`, or a
small enum such as `NEW`, `RUNNING`, `TERMINATED`. It is responsible for
making the check-and-transition atomic.

The guard condition is the predicate evaluated inside the atomic section,
something like "is the flag currently false" or "is the state currently NEW."
It must be evaluated and, if true, transitioned in the same indivisible step
as the guarded action's initiation, otherwise a second thread can slip through
between the check and the transition.

The guarded action is the actual work performed only when the guard
condition holds. It runs outside the lock whenever possible once the state
has been atomically claimed, so that long-running work does not hold a lock
and block unrelated balk checks from other methods on the same object.

The caller invokes the guarded method and receives an immediate signal,
either the action proceeded (a return value, a completion of the method) or it
balked (a boolean `false`, a no-op return, occasionally an exception in
implementations that prefer loud failure over silent decline). The caller is
responsible for deciding what a balk means for its own logic, since the
guarded object deliberately does not know or care.

The transition from "guard condition true" back to a state where a future
call can proceed again is a fifth, easy to forget responsibility. something,
usually the guarded action itself on completion, or a separate `finally`
block, must reset the flag. A balking guard that never resets degenerates into
a one-shot latch, which is sometimes exactly what is wanted, a `start()` that
should only ever succeed once, and sometimes a bug, a `save()` that should be
callable again after the first save finishes.

## 6. ASCII structure diagram

```
+----------------------------+
|        GuardedObject       |
|----------------------------|
| - state. AtomicBoolean/enum|
|----------------------------|
| + action(). boolean        |
| - resetState()             |
+----------------------------+
        |
        | owns
        v
+----------------------------+
|      Guard condition       |
|  (checked + transitioned   |
|   atomically, e.g. via     |
|   compareAndSet)           |
+----------------------------+
        |
        | true --------------------> runs guarded work, then resets state
        |
        v
       false
        |
        v
   returns immediately
   (no work performed)

+----------+   call action()   +----------------+
|  Caller  | ----------------> | GuardedObject  |
+----------+                   +----------------+
     ^                                 |
     |        false (balked)           |
     +---------------------------------+
     |        true  (proceeded)        |
     +---------------------------------+
```

## 7. Dynamics

The interesting case is not the single-caller happy path, it is what happens
when two threads race. The sequence below shows two callers, T1 and T2,
invoking a balking `save()` method at nearly the same moment, with the guard
implemented as an atomic compare-and-swap on a boolean flag.

```
T1                          GuardedObject.save()              T2
--                          --------------------              --
call save() -------------->|
                            | compareAndSet(false, true)
                            |   -> succeeds, returns true
                            | begins guarded work
                                                                call save() ---->
                                                               | compareAndSet(false, true)
                                                               |   -> fails (already true)
                                                               | returns false immediately
                                                                <---- balked, no work done
                            | finishes guarded work
                            | sets flag back to false
<---- returns true (worked)
```

Note the ordering guarantee that makes this correct. T2's compareAndSet
observes T1's write only if T1's compareAndSet happened first in the
underlying atomic's total order, which every mainstream atomic primitive,
Java's `AtomicBoolean`, C++'s `std::atomic<bool>`, Go's `sync/atomic`, Rust's
`AtomicBool`, provides by construction. There is no window in which both T1
and T2 can observe the flag as false and both proceed, which is precisely the
race a naive `if (!flag) { flag = true; ... }` sequence without atomicity
would permit.

A second dynamic worth diagramming is the reset-and-retry cycle for a caller
that wants "try now, and if it balked, try again on the next opportunity"
rather than treating a balk as final.

```
Caller loop:
  attempt save()
    balked?  --yes-->  wait for next trigger event (timer, user action, etc.)
       |                       |
       no                      +--> loop back to attempt save()
       |
       v
  proceed with whatever depends on the save having happened
```

This loop lives entirely in the caller, which is the point. Balking pushes the
policy of "what to do when declined" outward and keeps the guarded object's
own logic to a single atomic check.

## 8. Implementation variants

Synchronized block with a plain boolean field, the classic textbook form.
A method acquires the object's intrinsic lock, checks and flips a boolean
field in one critical section, then releases the lock before doing the actual
work, re-acquiring only to reset the flag on completion. This is the shape in
Mark Grand's original example and remains idiomatic Java when the guarded work
also needs to coordinate with other synchronized state on the same object.

Atomic compare-and-swap on a lock-free flag, the modern preferred form in
languages with a proper atomics library. `AtomicBoolean.compareAndSet(false,
true)` in Java, `atomic.Bool.CompareAndSwap` in Go, `std::atomic<bool>`'s
`compare_exchange_strong` in C++, or Rust's `AtomicBool` `compare_exchange`
methods all provide the identical atomic check-and-transition without taking
a lock, which removes both the risk of lock contention delaying an unrelated
balk check and the risk of holding a lock across the guarded work by mistake.

State-enum compare-and-swap, used when more than two states matter, as in
`java.util.concurrent.FutureTask`, discussed under production uses below,
which balks a `cancel()` call unless the task's internal state is exactly
`NEW`. The guard becomes a compare-and-swap from one specific enum value to
another, and any other current state causes the method to return `false`
without touching anything.

Exception-throwing balk, where instead of returning a boolean the guarded
method throws, `IllegalStateException` in Java, `InvalidOperationException` in
C#, when the precondition fails. This variant treats the wrong-state call as
more of a caller error than a routine, expected event, and is common in
library code where the wrong-state call usually does indicate a bug in the
calling code rather than an unavoidable race between independent callers.

Reentrancy guard in single-threaded event-loop languages, JavaScript,
TypeScript, Python's asyncio, where there is no true parallel race but there
is re-entrancy hazard from `await` yielding control back to the event loop
mid-operation. Here the "atomic" guard does not need a compare-and-swap
primitive at all, a plain boolean checked synchronously before the first
`await` point is sufficient, because JavaScript's single-threaded execution
model guarantees no other code can run between the check and the flag flip as
long as both happen before control yields. This variant is worth calling out
explicitly because developers arriving from Java or Go sometimes assume they
need `Atomics`, the JavaScript SharedArrayBuffer-backed atomics API, for a
plain in-process balk guard, when a synchronous boolean check suffices unless
multiple JavaScript workers or threads genuinely share the flag.

Debounce-as-balking, a UI-layer variant where the "state" being checked is
"is a request already in flight" and the guarded action is a network call or
expensive render. This is functionally identical to the resource-lifecycle
variants above but is worth naming separately because it is the variant most
frontend engineers encounter first, usually without ever hearing the pattern
name.

## 9. Known production uses

`java.util.concurrent.FutureTask.cancel(boolean)` balks any cancellation
attempt made after the task has left its initial `NEW` state. The
implementation performs a compare-and-swap from `NEW` to either `CANCELLED` or
`INTERRUPTING` and returns `false` immediately if that compare-and-swap fails,
meaning the task had already started, completed, or been cancelled by another
caller. Source, OpenJDK, `java.util.concurrent.FutureTask`, class source at
`https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/share/classes/java/util/concurrent/FutureTask.java`,
which guards the state transition with the line pattern `if (!(state == NEW
&& STATE.compareAndSet(this, NEW, mayInterruptIfRunning ? INTERRUPTING .
CANCELLED))) return false;` before doing any interruption or bookkeeping work,
verified 2026-08-14.

Google Guava's `AbstractService.startAsync()` balks a second call to start
a service that has already left the `NEW` state, throwing
`IllegalStateException("Service ... has already been started")` rather than
silently re-running the startup sequence, protected by an internal monitor
guard that only enters the critical section when the service is confirmed
startable. Source, Guava, `com.google.common.util.concurrent.AbstractService`,
`https://raw.githubusercontent.com/google/guava/master/guava/src/com/google/common/util/concurrent/AbstractService.java`,
verified 2026-08-14. This is the exception-throwing balk variant from
dimension 8 rather than the boolean-return variant, which matches the
library's stance that calling `startAsync()` twice is a programmer error, not
an expected race to be silently absorbed.

AndroidX `SwipeRefreshLayout.setRefreshing(boolean, boolean)` balks a
redundant refresh-state change by comparing the requested value against the
current `mRefreshing` field and skipping the animation setup entirely when
they already match, guarding the pull-to-refresh spinner against being
retriggered while it is already showing or already hidden. Source, AndroidX,
`androidx.swiperefreshlayout.widget.SwipeRefreshLayout`,
`https://raw.githubusercontent.com/androidx/androidx/androidx-main/swiperefreshlayout/swiperefreshlayout/src/main/java/androidx/swiperefreshlayout/widget/SwipeRefreshLayout.java`,
private overload guarded by `if (mRefreshing != refreshing) { ... }`, verified
2026-08-14.

`java.util.concurrent.atomic.AtomicBoolean` and `AtomicReference`
themselves are not applications of the pattern but the standard building
block every JVM implementation of it reaches for, documented in the Oracle
Java SE 8 API specification as providing `compareAndSet(expect, update)`
methods intended for "atomically updated flags" and lock-free reference
swapping respectively. Sources,
`https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/atomic/AtomicBoolean.html`
and
`https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/atomic/AtomicReference.html`,
both verified 2026-08-14. Their ubiquity across the JVM ecosystem's
lifecycle-guard code, connection pools, thread pool shutdown flags, singleton
lazy-init guards, is why they are cited here as the mechanism underneath
countless unnamed balking implementations, distinct from the three named
callers above which apply the mechanism as a documented, purposeful pattern.

## 10. Consequences

Positive. The guarded object never blocks a caller, which keeps latency
predictable and bounded for every invocation regardless of contention.
Duplicate or out-of-order invocations become harmless by construction rather
than by caller discipline, removing an entire class of race conditions from
the calling code. The guard logic is small, typically a single
compare-and-swap or a short synchronized block, which makes it easy to reason
about correctness locally without tracing every caller. Because the check and
the state transition are one atomic step, the pattern composes cleanly with
lock-free and wait-free code elsewhere in the same system, avoiding the
priority-inversion and deadlock risks that heavier locking strategies can
introduce.

Negative. A balked call carries almost no information by default, a bare
`false` or a swallowed no-op, which pushes the burden of deciding what
"declined" means onto every caller and can hide real problems, a caller that
never notices its saves keep getting dropped, behind a signal that looks
identical to "everything is fine, no save was needed." The pattern only
protects the single method it guards. if a caller needs a consistent view
across multiple balking methods on the same object, checking three flags then
acting, no such consistency is offered without additional coordination outside
the pattern. State-based balking scales poorly as the number of legal states
and legal transitions grows, degenerating into scattered boolean or enum
checks that duplicate the same busy-idle logic across many methods rather than
expressing it once in a proper state machine. And because the guarded work
typically runs outside the lock once claimed, the object's externally visible
"busy" state can become stale relative to the actual completion of the work if
the reset step is forgotten or delayed, silently reintroducing the very race
the guard was meant to prevent.

## 11. Failure modes and misuse

Symptom, two threads both perform the guarded action despite the balking
check being in place. Cause, the check and the state transition are two
separate operations, a plain `if (!flag) { flag = true; ... }` without an
atomic compare-and-swap or without both statements inside the same
synchronized block, so a second thread can read the flag as false before the
first thread has finished setting it to true. Fix, replace the read-then-
write pair with a single atomic compare-and-swap, so both the read and
the write happen inside one critical section protected by the same lock.

Symptom, the guarded method balks forever after its first successful
invocation, and legitimate later calls are silently dropped with no error.
Cause, the reset step that flips the flag back to its idle value was
placed on the wrong code path, most commonly omitted from an exception
handler, so an exception thrown by the guarded work leaves the flag
permanently set. Fix, reset the flag in a `finally` block, or the
language's equivalent guaranteed-cleanup construct, so it resets whether the
guarded work succeeds, fails, or throws.

Symptom, callers report that a save or refresh action appears to do
nothing on the first attempt but works on the second, with no visible error.
Cause, the method balks silently on the very first call because the flag
was accidentally initialized to the busy value rather than the idle value, or
because an earlier, unrelated code path set the flag and never reset it.
Fix, write an explicit unit test asserting the flag's initial value and
its value immediately after a completed guarded call, and add logging or a
metric at the balk point, see dimension 16, so this class of bug surfaces
immediately in development rather than being discovered by a confused user.

Symptom, under moderate load, the guarded operation is called far less
often than expected, and legitimate work is being dropped even though no true
race exists. Cause, Balking was applied to a method whose callers actually
need the work to happen eventually, not to have it silently declined, which is
a misapplication of the pattern rather than a bug in its implementation, this
is the dimension-4 non-applicability case slipping through in production.
Fix, replace the balking guard with Guarded Suspension, a bounded queue,
or an explicit retry policy that preserves caller intent instead of discarding
it.

Symptom, a load test shows the guarded method's compare-and-swap is a
measurable hotspot, with many threads spinning on failed compare-and-swap
attempts. Cause, the pattern is being invoked far more often, by far more
concurrent callers, than the design anticipated, so the "guard is cheap
relative to guarded work" assumption from dimension 3 no longer holds, and the
guard itself has become the bottleneck. Fix, coalesce callers upstream, a
single dispatcher thread rather than N callers hitting the same atomic, or
reconsider whether the operation should be a queue-backed background worker
instead of a directly-invoked balking method.

## 12. Trade-off matrix

| Force | Balking | Guarded Suspension | Double-Checked Locking |
|---|---|---|---|
| Caller blocks on wrong state | Never, returns immediately | Yes, waits until the condition becomes true | N/A, guards initialization not general preconditions |
| Declined call preserves intent | No, silently dropped | Yes, the call eventually proceeds | N/A |
| Typical guard cost | One atomic compare-and-swap or short lock | A lock plus a condition variable wait | One volatile read, occasionally a lock |
| Best suited to | Idempotent or redundant re-invocation | Producer-consumer style handoff where every request matters | One-time lazy initialization of a shared resource |
| Failure mode when misapplied | Silently lost work if intent actually mattered | Caller thread starvation if the condition never becomes true | Broken publication if applied without a proper memory-model-safe field |
| Number of legal states it scales to | Small, ideally two | Small to moderate | Effectively one, initialized or not |
| Composability with lock-free code | High, both are commonly lock-free | Lower, condition variables usually require a lock | High in its correct modern form |

## 13. Related and incompatible patterns

Guarded Suspension is Balking's closest relative and its structural
opposite on the single axis that matters most, what happens when the
precondition is false. Guarded Suspension makes the caller wait, typically via
a condition variable or an async await, until the state becomes favorable,
preserving the caller's intent at the cost of blocking it. Balking discards
the call instead of blocking it. The two patterns are frequently confused in
casual writing because their implementations look almost identical, a checked
condition guarding an action, and the only real difference is a `return false`
versus a `wait()`. Choosing between them is the single most important design
decision in this whole family of patterns, and it should be made explicitly by
asking whether a declined call is truly a no-op for the caller.

Monitor Object is frequently the mechanism Balking is built on top of, the
synchronized-block variant from dimension 8 is a Monitor Object whose
condition check happens to result in an early return rather than a wait.

Double-Checked Locking shares the shape of "check a flag, then act only if
the check fails to find work already done," but for the opposite purpose.
Double-Checked Locking exists to avoid taking a lock at all in the common case
where initialization has already happened, while Balking exists to prevent a
second invocation from doing the work at all. The two are sometimes composed,
for instance a lazily-initialized singleton, Double-Checked Locking, whose
`initialize()` method also balks concurrent initializers via an atomic flag,
which collapses into a single compare-and-swap doing both jobs at once.

Thread-Safe Interface is the broader umbrella under which Balking's
public-method-level guarding sits, a Thread-Safe Interface's job is to make an
object's public methods individually safe to call from multiple threads,
without necessarily prescribing what each method does when a precondition
fails, and Balking is one specific policy choice available to a method
implementing that interface.

Scoped Locking governs how the lock acquired inside a synchronized-block
variant of Balking is released correctly, including on exceptional exit, which
is exactly the mechanism that fixes the "flag never resets after an exception"
failure mode in dimension 11.

No pattern in this catalog is flagged as strictly incompatible with Balking,
its narrow, local scope, guarding one method's entry, means it composes
without structural conflict with almost anything, though as noted above it
should not be layered on top of Guarded Suspension for the same precondition,
since the two express contradictory policies for the identical situation.

## 14. Refactoring path in and out

Introducing Balking into code that lacks it. Start by identifying the
method whose repeated or out-of-order invocation causes a real, observed
problem, rather than guarding preemptively. Add a single boolean or enum field
representing the guarded state, initialized to the idle value. Wrap the
method's existing body so that the very first statement performs the atomic
check-and-claim, a compare-and-swap or an entry into a synchronized block that
checks and flips the flag, returning immediately on failure. Move any
existing precondition-violation exception throwing to only fire on the balk
path if loud failure is the desired semantics, or simply return a boolean if
silent decline is preferred, per dimension 8's exception-throwing versus
boolean-return variant. Add the reset step, in a `finally` block, before
considering the refactor complete, and write the test from dimension 11's
second failure mode, the flag resets after both success and exception, before
merging.

Removing Balking once it stops earning its place. This typically becomes
necessary when the number of guarded states grows past two or three, or when
callers start building their own retry loops around balked calls because they
actually need the work to happen. The refactor path out is to first make
explicit, in a short design note or a test, exactly which callers currently
rely on the silent-decline behavior and which ones are working around it with
ad hoc retries. Replace the boolean or enum guard with either an explicit
state machine object, if the complexity driver was too many states, or a
Guarded Suspension implementation using a condition variable or an async
queue, if the complexity driver was callers needing the work to actually
happen. Because Balking never changes an object's externally observable
result, only whether a call proceeds or is dropped, this refactor can usually
be done behind the same method signature, changing only what happens
internally when the old guard condition would have returned false.

## 15. Testing and verification

Balking is easy to test wrong by testing only the single-threaded happy path,
which proves nothing about the property the pattern exists to guarantee.
Verification needs to cover three distinct levels.

Sequential correctness. A straightforward single-threaded test asserting
that the guarded method performs its work exactly once when called while idle,
and that it correctly resets to idle afterward so a subsequent call also
succeeds. This catches the dimension-11 "forgot to reset" failure mode
directly, and is cheap to write and run on every commit.

Concurrent correctness under contention. A test that launches N threads,
or N async tasks in a single-threaded-runtime language driven through an
explicit interleaving rig rather than real OS threads, all calling the
guarded method at the same time, then asserts that exactly one of them
observed "proceeded" and the rest observed "balked," and that the guarded
work's observable side effect happened exactly once. In JVM languages this is
commonly written with a `CountDownLatch` releasing all threads simultaneously
to maximize the chance of hitting the race, plus an `AtomicInteger` counting
actual executions of the guarded work, asserted to equal exactly one after all
threads join. This is the test that would fail immediately against the
"read-then-write instead of compare-and-swap" bug from dimension 11's first
failure mode, and it should be run with a stress multiplier, hundreds or
thousands of iterations, in CI, since a race condition test that only runs
once and passes proves very little.

Exception-path correctness. A test that makes the guarded work throw and
then asserts the flag correctly returns to idle, directly targeting the
"exception leaves the guard permanently set" failure mode. This test is easy
to forget because it requires deliberately injecting a failure into the
guarded action, which most developers do not think to do when the happy path
already passes.

Test doubles are rarely needed for the pattern itself, since the guard's
correctness depends on real atomic or lock semantics that a mock or fake would
not exercise meaningfully. what is worth mocking or stubbing is the guarded
action's own dependencies, so the concurrent-correctness test above can run
fast and deterministically without waiting on real I/O.

## 16. Observability signals

A healthy balking guard, viewed on a dashboard, shows a low but non-zero balk
rate under normal load, occasional legitimate double-clicks or redundant
triggers being correctly absorbed, and a balk rate that tracks proportionally
with caller volume rather than growing unboundedly. Emit a counter incremented
on every balk, labeled with the guarded method's name, distinct from the
counter for successful invocations, so the ratio of balked-to-proceeded calls
is directly visible. A sudden spike in the balk rate with no corresponding
spike in caller volume is the signature of the dimension-11 "flag never resets"
failure mode, it means the guarded object has gotten stuck in the busy state
and every subsequent call is being silently discarded, which without this
metric is invisible until a human notices the guarded work simply is not
happening anymore.

Log a single structured line at debug level on each balk, including the
guarded method's name and, where available, an identifier for the caller or
the request, so that when a support engineer is asked why a save did not
happen, the log line answers the question directly rather than requiring
speculation. Do not log at warn or error level for every balk under normal
operation, a balk is an expected outcome in this pattern's correct usage, not
an anomaly, and logging it as an error trains the team to ignore error-level
logs from this code path, defeating the purpose of the level.

Where the guarded state persists longer than expected, a `save()` guard that
should clear within milliseconds but has been observed set for seconds, a
staleness alert comparing "time since the flag was last set" against an
expected upper bound catches a stuck guard before the balk-rate spike above
would otherwise surface it.

## 17. Security and privacy implications

Balking's security surface is narrow but not empty. Because a balked call
returns immediately with a signal distinguishable from a successful call, an
attacker who can observe response timing or the return value can sometimes
infer the guarded object's internal state, for example whether a
rate-limited or lock-protected resource is currently busy, which in some
systems constitutes a minor information leak about server load or concurrent
usage that would otherwise be hidden. In the common case, a `save()` or
`refresh()` guard on an object the caller already legitimately owns or has
access to, this is not a meaningful concern, but in a multi-tenant system
where the guarded object is shared or where balking is used on an
authentication or account-lockout path, the distinguishable "declined because
busy" versus "declined because forbidden" signals should be considered
carefully, since conflating them or leaking the distinction can aid an
attacker probing for account state.

There is no data-handling implication specific to the pattern itself. it
guards control flow, not data, and introduces no new storage, transmission, or
retention of sensitive information beyond what the guarded action already
involves. The pattern's atomic guard, when correctly implemented, is also a
mild defense against a specific denial-of-service shape, an attacker
repeatedly invoking an expensive operation cannot cause N concurrent
executions of that expensive work merely by firing N simultaneous requests,
since the guard collapses them to at most one in-flight execution. This is a
side benefit rather than the pattern's purpose, and should not be relied on as
a substitute for a real rate limiter when the guarded resource is
externally reachable, since a balking guard does nothing to prevent an
attacker from firing the same request again immediately after each balk.

## 18. References

1. Grand, Mark. *Patterns in Java, Volume 1*, 2nd edition, John Wiley & Sons,
   2002. Cited via secondary summary at
   `https://en.wikipedia.org/wiki/Balking_pattern`, verified 2026-08-14,
   which reproduces the book's Java example and attribution.
2. Lea, Doug. *Concurrent Programming in Java. Design Principles and
   Patterns*, 2nd edition, Addison-Wesley, 1999. Chapter 3 discusses
   state-dependent action and guard conditions, the conceptual neighborhood
   Balking and Guarded Suspension both occupy.
3. Schmidt, Douglas C., Stal, Michael, Rohnert, Hans, and Buschmann, Frank.
   *Pattern-Oriented Software Architecture, Volume 2. Patterns for Concurrent
   and Networked Objects*, John Wiley & Sons, 2000. Source of the Monitor
   Object and Guarded Suspension vocabulary this entry contrasts Balking
   against.
4. Oracle. `java.util.concurrent.atomic.AtomicBoolean` API documentation,
   Java SE 8.
   `https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/atomic/AtomicBoolean.html`,
   verified 2026-08-14.
5. Oracle. `java.util.concurrent.atomic.AtomicReference` API documentation,
   Java SE 8.
   `https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/atomic/AtomicReference.html`,
   verified 2026-08-14.
6. OpenJDK. `java.util.concurrent.FutureTask` source, `cancel(boolean)`
   method.
   `https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/share/classes/java/util/concurrent/FutureTask.java`,
   verified 2026-08-14.
7. Google. `com.google.common.util.concurrent.AbstractService` source,
   `startAsync()` method, Guava.
   `https://raw.githubusercontent.com/google/guava/master/guava/src/com/google/common/util/concurrent/AbstractService.java`,
   verified 2026-08-14.
8. Google. `androidx.swiperefreshlayout.widget.SwipeRefreshLayout` source,
   `setRefreshing(boolean, boolean)` method, AndroidX.
   `https://raw.githubusercontent.com/androidx/androidx/androidx-main/swiperefreshlayout/swiperefreshlayout/src/main/java/androidx/swiperefreshlayout/widget/SwipeRefreshLayout.java`,
   verified 2026-08-14.

## Code examples

### Java

Uses `AtomicBoolean.compareAndSet` for a lock-free balk guard on a
long-running save operation, matching the modern idiomatic variant from
dimension 8.

```java
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;

public class BalkingSaver {
    private final AtomicBoolean saving = new AtomicBoolean(false);
    private final AtomicInteger completedSaves = new AtomicInteger(0);

    public boolean save() {
        if (!saving.compareAndSet(false, true)) {
            return false;
        }
        try {
            doExpensiveSave();
            return true;
        } finally {
            saving.set(false);
        }
    }

    private void doExpensiveSave() {
        try {
            Thread.sleep(50);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        completedSaves.incrementAndGet();
    }

    public static void main(String[] args) throws InterruptedException {
        BalkingSaver saver = new BalkingSaver();
        int threadCount = 8;
        CountDownLatch ready = new CountDownLatch(threadCount);
        CountDownLatch start = new CountDownLatch(1);
        AtomicInteger proceeded = new AtomicInteger(0);
        AtomicInteger balked = new AtomicInteger(0);
        Thread[] threads = new Thread[threadCount];

        for (int i = 0; i < threadCount; i++) {
            threads[i] = new Thread(() -> {
                ready.countDown();
                try {
                    start.await();
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
                if (saver.save()) {
                    proceeded.incrementAndGet();
                } else {
                    balked.incrementAndGet();
                }
            });
            threads[i].start();
        }

        ready.await();
        start.countDown();
        for (Thread t : threads) {
            t.join();
        }

        System.out.println("proceeded=" + proceeded.get()
            + " balked=" + balked.get()
            + " completedSaves=" + saver.completedSaves.get());

        if (proceeded.get() != 1 || saver.completedSaves.get() != 1) {
            throw new AssertionError("expected exactly one save to proceed");
        }

        boolean secondCallProceeds = saver.save();
        if (!secondCallProceeds) {
            throw new AssertionError("guard should reset after completion");
        }
        System.out.println("second call proceeded=" + secondCallProceeds);
    }
}
```

Compiled and run with `javac BalkingSaver.java && java BalkingSaver`, output
confirmed exactly one thread of eight proceeded, seven balked, exactly one
completed save was recorded, and a subsequent call after completion correctly
proceeded again.

### Go

Uses `sync/atomic`'s `CompareAndSwap` on a `Bool`, Go's direct equivalent of
Java's `AtomicBoolean.compareAndSet`.

```go
package main

import (
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

type BalkingSaver struct {
	saving         atomic.Bool
	completedSaves atomic.Int64
}

func (s *BalkingSaver) Save() bool {
	if !s.saving.CompareAndSwap(false, true) {
		return false
	}
	defer s.saving.Store(false)
	time.Sleep(10 * time.Millisecond)
	s.completedSaves.Add(1)
	return true
}

func main() {
	saver := &BalkingSaver{}
	const goroutineCount = 8

	var wg sync.WaitGroup
	var proceeded, balked atomic.Int64
	start := make(chan struct{})

	for i := 0; i < goroutineCount; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			<-start
			if saver.Save() {
				proceeded.Add(1)
			} else {
				balked.Add(1)
			}
		}()
	}

	close(start)
	wg.Wait()

	fmt.Printf("proceeded=%d balked=%d completedSaves=%d\n",
		proceeded.Load(), balked.Load(), saver.completedSaves.Load())

	if proceeded.Load() != 1 || saver.completedSaves.Load() != 1 {
		panic("expected exactly one save to proceed")
	}

	if !saver.Save() {
		panic("guard should reset after completion")
	}
	fmt.Println("second call proceeded=true")
}
```

Run with `go run balking.go`, output confirmed exactly one of eight goroutines
proceeded, seven balked, exactly one completed save was recorded, and the
subsequent call after completion proceeded again.

### TypeScript

Demonstrates the single-threaded reentrancy-guard variant from dimension 8, a
`refresh()` method guarding against overlapping async calls without needing a
compare-and-swap primitive, because the synchronous flag check happens before
the first `await` and JavaScript's event loop cannot interleave another call
in between.

```typescript
class BalkingRefresher {
  private refreshing = false;
  private completedRefreshes = 0;

  async refresh(): Promise<boolean> {
    if (this.refreshing) {
      return false;
    }
    this.refreshing = true;
    try {
      await this.doExpensiveRefresh();
      return true;
    } finally {
      this.refreshing = false;
    }
  }

  private async doExpensiveRefresh(): Promise<void> {
    await new Promise((resolve) => setTimeout(resolve, 20));
    this.completedRefreshes += 1;
  }

  getCompletedRefreshes(): number {
    return this.completedRefreshes;
  }
}

async function main(): Promise<void> {
  const refresher = new BalkingRefresher();

  const calls = Array.from({ length: 5 }, () => refresher.refresh());
  const results = await Promise.all(calls);

  const proceeded = results.filter((r) => r === true).length;
  const balked = results.filter((r) => r === false).length;

  console.log(`proceeded=${proceeded} balked=${balked} completedRefreshes=${refresher.getCompletedRefreshes()}`);

  if (proceeded !== 1) {
    throw new Error("expected exactly one refresh to proceed");
  }

  const secondBatchProceeded = await refresher.refresh();
  if (!secondBatchProceeded) {
    throw new Error("guard should reset after completion");
  }
  console.log(`second call proceeded=${secondBatchProceeded}`);
}

main();
```

Run with `npx tsx balking.ts`, or compiled with `tsc` and run under `node`,
output confirmed exactly one of five concurrently-issued calls proceeded, four
balked, one completed refresh was recorded, and a later call after completion
proceeded again. This variant is included specifically because Balking is
sometimes assumed to be irrelevant outside true multi-threaded languages,
which dimension 8's reentrancy-guard note addresses directly, the hazard here
is re-entrancy across `await` boundaries within one thread, not parallel
execution across cores, and the pattern's atomic-check-then-claim structure
still applies.
