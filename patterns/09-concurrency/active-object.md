---
name: Active Object
slug: active-object
family: 09-concurrency
category: Concurrency
aliases: [Concurrent Object, Actor (informal, imprecise)]
first_described: "Lavender, Schmidt 1996; Schmidt, Stal, Rohnert, Buschmann 2000"
maturity: canonical
related: [monitor-object, reactor, proactor, half-sync-half-async, command, future-promise]
incompatible_with: [monitor-object]
verified: 2026-08-13
---

## 1. Name, aliases, and lineage

The canonical name is Active Object. The pattern is sometimes called Concurrent
Object in older concurrency literature, and it is loosely, and incorrectly,
conflated with the Actor model in casual conversation. The two are related in
spirit but not identical. An Active Object decouples method invocation from
method execution for a single object with its own dedicated processing thread,
while an actor is a unit of computation with its own mailbox that can also
create other actors and change its own behavior between messages. Treating
them as synonyms in a design review is a real source of confusion, because an
Active Object typically exposes a class-shaped API with return values, often
futures, while an actor typically exposes only fire-and-forget message sends.

The pattern was first published by R. Greg Lavender and Douglas C. Schmidt as
"Active Object, an Object Behavioral Pattern for Concurrent Programming," which
circulated as a Washington University technical report and pattern-language
paper in the mid-1990s, ahead of its inclusion as one of the twelve patterns
compiled in *Pattern-Oriented Software Architecture, Volume 2, Patterns for
Concurrent and Networked Objects* by Douglas C. Schmidt, Michael Stal, Hans
Rohnert, and Frank Buschmann, published by John Wiley and Sons in 2000. POSA2
is the canonical, citable, book-length treatment, and it is the source this
entry follows for the six named participants below. The Wikipedia summary of
the pattern, https://en.wikipedia.org/wiki/Active_object (verified
2026-08-13), corroborates this attribution and cites POSA2 as the primary
reference. The original Lavender and Schmidt paper is still reachable as a
PDF from Douglas Schmidt's Vanderbilt University publication archive,
https://www.dre.vanderbilt.edu/~schmidt/PDF/Act-Obj.pdf, though the PDF text
layer did not extract cleanly during verification for this entry, so this
entry cites POSA2 as the primary source for structural claims rather than the
original paper's exact wording.

## 2. Problem and context

An object's public methods are typically called synchronously. The caller
blocks on the stack until the method returns. That is fine when the method
runs on the calling thread and completes quickly. It stops being fine the
moment the method does real work, holds a lock for a long time, or must be
serialized against other calls to the same object from multiple threads.

The concrete situation looks like this. A `Logger` object is shared by many
threads. Every thread that wants to write a log line calls `logger.write(msg)`
directly. To keep the log file consistent, `write` takes a mutex. Under load,
every calling thread now contends for that mutex, and the calling thread that
loses the race blocks on disk I/O it did not ask for and cannot control. The
object's own concurrency control has leaked into every caller's latency
budget. Worse, if `write` is slow enough, the calling threads pile up behind
the lock, and a component that should never block, a UI event handler, a
request-serving thread in a web server, now blocks on someone else's I/O.

The same shape recurs anywhere a stateful object must be touched from many
threads but must only ever be touched by one thread at a time. a device
driver, a network connection object, a game entity that mutates shared world
state, a cache with per-key locking that a naive implementation turned into
global locking. In every one of these cases the object has an implicit
threading rule, only call me from thread X, or hold this lock while calling
me, that lives in a comment, or worse, only in the author's head. The Active
Object pattern makes that rule structural instead of documentary. The object
owns its own thread, callers can never touch its state directly, and the
concurrency control that used to be scattered defensive locking becomes a
single serialized queue with one consumer.

## 3. Forces

Latency versus throughput at the call site. A synchronous call to a busy
object blocks the caller for the full duration of the work. An Active Object
call returns almost immediately, the enqueue is O(1) and typically lock-free
or lightly contended, trading the caller's per-call latency for a future that
must eventually be resolved. This is a genuine improvement for a caller that
has other useful work to do, and a genuine cost for a caller that has nothing
else to do and would rather block than manage a future.

Coupling between clients and the object's threading policy. Without the
pattern, every client of a shared, thread-unsafe object must independently
know and honor its locking discipline. With the pattern, that knowledge moves
into the object's own boundary. This is a coupling reduction at the design
level, purchased at the cost of an extra layer, proxy, scheduler, activation
queue, that a plain method call did not need.

Ordering guarantees versus parallelism. The pattern gives strict FIFO or
priority ordering of method executions on one worker, which is exactly the
guarantee that makes a stateful object safe to share. It also caps the
object's own throughput at whatever one worker thread can do, because there is
exactly one thread draining the activation queue. If the object's methods are
CPU-bound and the workload is embarrassingly parallel, the Active Object
pattern actively prevents you from using more cores for that object, and you
must shard across multiple Active Objects instead.

Cognitive load and debuggability. A synchronous call has one stack, one
timeline, and a debugger that can step through it in the obvious order. An
Active Object call splits the timeline into the proxy call that returned
immediately, and the scheduled method request that runs later, on a
different thread, possibly much later. Stepping through this in a debugger
means following a request object, not a call stack, and a stack trace
captured inside the servant method will never show the caller's original
frame. This is a real cost that the pattern's proponents rarely emphasize as
strongly as its throughput benefits.

Cost of the machinery itself. Every method call becomes an allocation, a
method request object, a queue push, a context switch to the worker thread if
it was idle, and, if a result is expected, a future allocation plus whatever
synchronization the future implementation uses to hand the result back. For a
method that does two nanoseconds of arithmetic, that machinery costs orders of
magnitude more than the work it protects. The pattern favors correctness and
decoupling under contention over raw single-call efficiency.

## 4. Applicability and non-applicability

Reach for Active Object when:

- A single object is shared by multiple threads and its internal state must
  never be touched concurrently, and you want that guarantee to be structural
  rather than convention-based (no caller can forget to take a lock, because
  no caller ever touches the state directly).
- Callers benefit from not blocking on the object's work, either because they
  have other useful work to do while the request executes, or because
  blocking that particular thread would be actively harmful (a UI thread, an
  I/O completion thread, a request handler in an event-driven server).
- The object's operations naturally decompose into discrete, nameable
  requests that can be represented as data (a method name plus arguments) and
  queued, rather than operations that need to interleave with the caller's
  own control flow step by step.
- You want a natural place to apply scheduling policy across the object's
  operations, such as priority ordering, rate limiting, or batching, because
  all requests already funnel through one queue that a scheduler controls.
- You are building on a platform where giving a class its own thread and a
  message queue is already the idiomatic concurrency unit, for example
  Android's `Handler` and `Looper`, or a GUI toolkit's main-thread affinity
  model.

Do not reach for Active Object when:

- The shared state genuinely needs no cross-thread coordination because it is
  immutable or thread-confined already. Adding a proxy, a queue, and a worker
  thread around data nobody contends for is pure overhead with no
  corresponding benefit, see Consequences and Failure Modes below.
- The workload is CPU-bound and embarrassingly parallel, meaning the object's
  operations are independent of each other and would benefit from running on
  many cores simultaneously. Active Object caps you at one worker thread per
  object by design. A thread pool executing independent tasks, or a fork-join
  decomposition, will use the hardware far better.
- The caller needs the result synchronously, in order, on the same stack, and
  cannot tolerate the indirection of a future, for example inside a hot inner
  loop where every call must complete before the loop can proceed and there
  is no other work to interleave. Forcing this through a queue and a future
  just to unwrap the future immediately afterward buys nothing and costs an
  allocation and a context switch.
- You already have a simpler primitive that solves the actual problem. If the
  only requirement is protecting data from concurrent mutation and callers
  are fine blocking briefly, a plain mutex, or the Monitor Object pattern
  (`related`), gives the same safety with a fraction of the machinery and a
  synchronous call shape that is easier to reason about and to debug.
- Requests genuinely need to be canceled mid-flight, paused, or reordered
  after submission in ways the underlying queue implementation does not
  support. A plain FIFO activation queue offers none of this without
  additional design, and bolting cancellation onto an Active Object after the
  fact is a common source of the failure modes listed later in this entry.

## 5. Structure

POSA2 names six participants. This entry uses the same six names because they
are the ones a reader will find in every other serious discussion of the
pattern, and inventing alternate names here would make cross-referencing
harder rather than easier.

Proxy. The object the client actually calls. It exposes the same public
method signatures the client expects, or a close analogue, but instead of
executing the method body, it packages the call, its arguments, and, if a
result is expected, a Future, into a Method Request, and hands that request to
the Scheduler. The proxy runs on the calling thread and returns to the caller
almost immediately.

Method Request. An object representing one pending invocation. which
operation to run, the arguments it needs, and where to put the result. It is
the reification of a method call into ordinary data that can be queued,
inspected, reordered, or dropped, rather than being live control flow on a
stack.

Activation List, also called the Activation Queue. The data structure that
holds pending Method Requests until the Scheduler is available to run them.
In the simplest implementations this is a plain FIFO queue. In richer
implementations it supports priority ordering or per-request guard conditions
that decide whether a request is currently runnable, POSA2's original
treatment allows a request to specify a guard so the scheduler can defer it
until some precondition holds, distinct from simple FIFO ordering.

Scheduler. The logic, running on the Active Object's dedicated thread, that
decides which pending Method Request to run next and then runs it against the
Servant. In the common case this is trivial, pop the head of the FIFO queue,
run it, repeat, but the Scheduler is the seam where priority policy, fairness
policy, or guard-condition evaluation lives.

Servant. The plain, ordinary object that actually implements the behavior.
the real method bodies, holding whatever private state the object needs. The
Servant has no concurrency logic in it at all. It is exactly the class you
would have written if there were no threading concern, which is one of the
pattern's real strengths. business logic and concurrency policy are cleanly
separated into different objects.

Future. The handle returned to the client, usually by the Proxy, immediately,
before the method has actually run, representing a result that will become
available once the Scheduler has executed the corresponding Method Request
against the Servant. The client can poll it, block on it, or, in richer
implementations, attach a continuation to it. See the related Future/Promise
entry (`related`) for the mechanics of that handle on its own.

## 6. ASCII structure diagram

```
+-----------+        +-----------------+       +------------------+
|  Client   |------->|      Proxy       |------>|  Method Request   |
+-----------+  call  +-----------------+ create +------------------+
      ^                      |                          |
      |                      | returns                  | enqueue
      | Future                                           v
      |               +-------------+          +--------------------+
      +---------------|   Future    |          |  Activation List   |
       poll/block/     +-------------+          |  (Activation Queue)|
       .then(...)              ^                +--------------------+
                                | fulfilled by             |
                                |                           | dequeue
                          +-----------+           +-----------------+
                          |   ...     |<----------|    Scheduler     |
                          |  result   |   runs on  +-----------------+
                          +-----------+  dedicated         |
                                          worker thread     | invoke
                                                             v
                                                    +-----------------+
                                                    |     Servant      |
                                                    | (plain, no locks)|
                                                    +-----------------+
```

## 7. Dynamics

The interaction sequence for a single call, with a future result, is the
same in every implementation of the pattern, and it is worth walking through
in order because the split between what happens on the caller's thread and
what happens on the worker thread is the entire point.

```
Caller thread                          Active Object's worker thread
--------------                          ------------------------------
1. client calls proxy.doWork(args)
2. proxy builds MethodRequest{
      args, futurePromise }
3. proxy pushes request onto
      the ActivationQueue
4. proxy returns Future to client
5. client continues other work,
      or calls future.get()/await                (worker thread, running
      which blocks or suspends                     independently, possibly
      until the future resolves                     already looping)
                                          6. scheduler dequeues the
                                                MethodRequest (blocks on an
                                                empty queue via a condition
                                                variable or channel receive)
                                          7. scheduler evaluates any guard
                                                condition, if not satisfiable,
                                                re-queues or defers per policy
                                          8. scheduler invokes the matching
                                                method on the Servant with
                                                the request's arguments
                                          9. servant runs, touching its own
                                                private state, no locking
                                                needed because it is only
                                                ever called from this thread
                                          10. scheduler takes the return
                                                value, or exception, and
                                                fulfills the Future's promise
11. client's blocked future.get()/await
      unblocks with the result
      (or the exception is rethrown
      into the caller)
                                          12. scheduler loops back to step 6
```

The critical property this sequence guarantees is that steps 8 and 9 can
never run concurrently for two different requests, because there is exactly
one worker thread and one loop pulling from one queue. That is the entire
safety argument for the Servant needing no internal locks. it is a
single-threaded object from its own point of view, even though it is called
from many threads' points of view.

## 8. Implementation variants

Thread-plus-blocking-queue, the textbook shape. A dedicated OS or green
thread runs a loop that blocks on a thread-safe queue, Java's
`BlockingQueue`, a condition-variable-backed queue in C++, a channel in Go.
This is the most literal rendering of POSA2's six participants and is what
most tutorials show. Its cost is one OS thread per Active Object, which does
not scale past a few thousand instances on most platforms.

Executor-backed, collapsing the Scheduler into a runtime primitive. Rather
than hand-writing the Activation List and Scheduler, delegate to
`java.util.concurrent.Executors.newSingleThreadExecutor()`. This factory
method is documented to create "an Executor that uses a single worker thread
operating off an unbounded queue," with the explicit guarantee that "Tasks
are guaranteed to execute sequentially, and no more than one task will be
active at any given time" (Oracle Java SE 17 API documentation,
https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/Executors.html,
verified 2026-08-13). Submitting a `Callable` to that executor and returning
its `Future` is a direct, minimal-code implementation of Proxy plus
Activation List plus Scheduler plus Future, with the Servant as the object
the `Callable` closes over.

Strand or serial-queue-backed, sharing a thread pool across many logical
Active Objects. Instead of dedicating one OS thread per object, a strand, in
Boost.Asio's terminology, or a serial dispatch queue, in Apple's Grand
Central Dispatch terminology, provides the ordering and mutual-exclusion
guarantee while the actual execution happens on threads pulled from a shared
pool. Boost.Asio's documentation defines a strand as guaranteeing "a strictly
sequential invocation of event handlers (i.e. no concurrent invocation)"
(https://www.boost.org/doc/libs/1_85_0/doc/html/boost_asio/overview/core/strands.html,
verified 2026-08-13), which is exactly the Active Object safety property
without the one-thread-per-object cost. Many objects can each own a strand
and all share the same underlying `io_context` thread pool.

Actor-library-backed. Frameworks whose primary abstraction is already an
object with a mailbox and a single logical thread of control, Akka,
Erlang/OTP processes, Orleans grains, can implement an Active Object as a
thin wrapper, or the actor itself functions as the Active Object with no
wrapper at all. The distinction from a pure Active Object is that these
frameworks typically expose fire-and-forget message sends as the primary API
rather than a synchronous-looking method call that happens to return a
future, so callers must adapt their calling convention, not just their
threading model.

Callback-based instead of future-based. On platforms or in codebases that
predate widespread future/promise support, the Method Request carries a
completion callback instead of a promise, and the Proxy's call takes the
callback as a parameter rather than returning a handle. This is functionally
equivalent but pushes composition, chaining, error propagation, onto manual
callback wiring instead of onto the future's combinator API.

Language-idiomatic collapse via async/await. In languages with native
coroutines, TypeScript/JavaScript with `async`/`await`, Python's `asyncio`,
Rust's `async fn` with a single-threaded or work-stealing executor, C#'s
`async`/`await`, a single-threaded event loop dispatching queued
continuations already provides the serialization property, so an Active
Object frequently collapses into a class whose methods are `async` and which
internally `await`s on an internal request channel drained by a background
task, rather than a hand-rolled thread-and-queue pair. The code examples
below show this collapse in TypeScript, Python, and Rust, alongside a more
literal Go rendering using goroutines and channels.

## 9. Known production uses

Android's `Handler` and `Looper` are the platform's own name for a
concurrency primitive that matches the Active Object shape closely. A
`Looper` runs a message loop on one thread, and a `Handler` bound to that
`Looper` lets other threads post `Message` or `Runnable` work that is
guaranteed to execute, one at a time, on the `Looper`'s thread. Android's own
developer guide on processes and threads recommends this exact construction
for marshaling work from a background thread onto a target thread, "you
might consider using a Handler in your worker thread to process messages
delivered from the UI thread"
(https://developer.android.com/guide/components/processes-and-threads,
verified 2026-08-13). Android's `HandlerThread` class packages a Handler
bound to a dedicated background thread's Looper as a single reusable
utility, which is close to a literal, library-provided Active Object.

Qt's queued signal-and-slot connections implement the same guarantee for
cross-thread `QObject` calls. When a signal is emitted from one thread and
connected to a slot on a `QObject` that lives on a different thread, Qt
documents that "the slot is invoked when control returns to the event loop of
the receiver's thread. The slot is executed in the receiver's thread."
(https://doc.qt.io/qt-6/threads-qobject.html, verified 2026-08-13). The event
loop of the receiver's thread is functioning as the Scheduler and Activation
List, the queued signal invocation is the Method Request, and the `QObject`
itself is the Servant, called only ever from its own thread by construction.

Boost.Asio strands, and their C++20 successor `asio::strand`, implement the
serialization half of the pattern, mutual exclusion and ordering, while
deliberately decoupling it from any fixed thread, letting many strands share
one thread pool. The library's own overview states a strand's defining
guarantee as "a strictly sequential invocation of event handlers (i.e. no
concurrent invocation)"
(https://www.boost.org/doc/libs/1_85_0/doc/html/boost_asio/overview/core/strands.html,
verified 2026-08-13), which library authors building network servers use
specifically to give a per-connection object, the equivalent of a Servant,
thread-safe access without a mutex, by posting all operations on that
connection to its own strand.

Java's `java.util.concurrent.Executors.newSingleThreadExecutor()` is a direct,
standard-library implementation of the Scheduler plus Activation List plus
Future portion of the pattern, documented as guaranteeing sequential,
non-concurrent task execution
(https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/Executors.html,
verified 2026-08-13). It is widely used inside Java server frameworks and
client libraries as the mechanism for giving a piece of otherwise
thread-unsafe state, a single database connection, a single native handle, a
dedicated, serialized execution context, exactly matching the pattern's
canonical motivation.

ACE, the Adaptive Communication Environment, the C++ framework Douglas
Schmidt built and used as the implementation vehicle for the original POSA2
concurrency patterns, ships `ACE_Task`, a class explicitly designed to
combine a message queue with a dedicated thread of control, which the POSA2
book uses as its worked C++ example of the Active Object pattern. This is the
historical, originating implementation rather than a later independent
adopter, and its identity as the pattern's reference implementation is the
attribution already covered in Dimension 1 via POSA2.

## 10. Consequences

Positive consequences. Callers are decoupled from the object's internal
synchronization policy entirely. there is no lock for a caller to remember to
take or to get wrong. The Servant's method bodies read exactly like ordinary,
single-threaded code, because from the Servant's own perspective, they are.
Method calls can be scheduled, reordered by priority, rate-limited, batched,
or logged, all by changing the Scheduler, without touching either the caller
or the Servant. A slow or blocking operation inside the Servant no longer
blocks the caller's thread, which matters enormously on threads that must
stay responsive, such as UI threads or network I/O threads. The Method
Request objects are also a natural point to add cross-cutting behavior,
audit logging, replay, deferred execution, because a call has been turned
into inspectable data rather than remaining live control flow.

Negative consequences. Every call now costs at least one allocation, the
Method Request, and usually a Future, a queue operation, and, if the worker
was idle, a context switch or a wakeup signal, which is measurable overhead
compared to a direct call for hot, cheap methods. The object's own throughput
is capped by a single worker thread, so a CPU-bound Servant does not get
faster by adding more callers. it only gets a longer queue. Debugging gets
harder because a stack trace captured while a Method Request executes shows
the Scheduler's loop as the caller, not the original client code that
submitted the request. correlating a failure back to its origin requires
deliberately threading a request identifier or a captured stack trace through
the Method Request at submission time. If results are needed synchronously,
the client must either block on the Future, defeating much of the pattern's
benefit, or restructure its own control flow around asynchronous completion,
which is a real cost to the caller even though it never touches the Servant's
internals.

## 11. Failure modes and misuse

Unbounded activation queue causing memory growth under sustained overload.
Symptom, memory usage climbs steadily while the Active Object appears busy
but not crashing, and eventually the process is OOM-killed or GC pause times
grow unbounded. Cause, the Activation List is an unbounded queue, the default
for both `java.util.concurrent.LinkedBlockingQueue`-backed executors and
naive hand-rolled queues, and producers submit Method Requests faster than
the single worker can drain them, so the backlog grows without limit. Fix,
bound the queue and choose an explicit backpressure policy for what happens
when it is full, such as blocking the producer, rejecting with an error the
caller must handle, or dropping the oldest pending request. `ThreadPoolExecutor`
in Java exposes exactly this as a configurable `RejectedExecutionHandler`
when backed by a bounded queue, and the same policy decision should be made
explicit in any hand-rolled implementation rather than left to an unbounded
default.

Priority inversion or starvation when a scheduler supports priorities without
aging. Symptom, a specific class of request, typically low-priority
housekeeping work, never runs, or runs only after very long, unpredictable
delays, even though the worker thread is not idle. Cause, a naive priority
queue always drains the highest-priority request first, so a steady stream of
high-priority requests can starve lower-priority ones indefinitely. this is a
direct, well-known consequence of introducing priority into the Scheduler
without also introducing a fairness mechanism. Fix, add aging, a request's
effective priority increases the longer it waits, or a guaranteed minimum
share of worker time for lower-priority classes, and treat whether this
scheduler can ever starve a priority class as a design question that must be
answered explicitly, not left implicit.

Serializing genuinely independent operations onto one worker thread as a
reflex, destroying available parallelism. Symptom, a service that should
scale with added cores instead plateaus, with the single Active Object worker
thread pegged at or near 100 percent CPU while other cores sit idle. Cause, a
team applies the pattern to protect state that did not actually need
sequential access, for example, a stateless computation was wrapped in an
Active Object out of habit, or because everything shared going through the
Active Object became an unexamined house rule, and the single-worker
constraint that made sense for the object's mutable state is now needlessly
throttling unrelated CPU-bound work. Fix, separate the truly stateful,
sequential portion, kept in the Active Object, from the parallelizable
computation, moved to a thread pool or fork-join structure that runs
independently and only hands its finished result back to the Active Object
if the shared state actually needs updating.

Deadlock from a Servant method that calls back into its own Proxy and blocks
on the resulting Future. Symptom, the Active Object hangs permanently, and a
thread dump shows the single worker thread blocked inside `future.get()`, or
the local equivalent, waiting on a Future that can only ever be fulfilled by
that same worker thread once it becomes free again, which it never will
because it is the one blocking. Cause, code inside the Servant, directly or
through a chain of calls, invokes the object's own Proxy method and then
synchronously waits for the result, not realizing that fulfilling that result
requires the very worker thread that is currently blocked waiting for it.
Fix, never call back into your own Proxy from inside a Servant method and
block on the result. if internal recursion or self-invocation is genuinely
needed, call the Servant's own method directly, bypassing the Proxy and
queue entirely, because you are already executing on the correct thread, or
restructure the operation as a continuation attached to the Future instead
of a blocking wait.

Silent exception swallowing inside the Scheduler loop. Symptom, a Method
Request appears to simply vanish. the caller's Future never resolves, times
out, or resolves with a generic error that gives no indication of what
actually went wrong inside the Servant, and nothing appears in application
logs. Cause, an unhandled exception thrown by the Servant method propagates
up into the Scheduler's dequeue-and-invoke loop. if that loop is not wrapped
in its own exception handling per request, the exception either kills the
worker thread outright, which then silently stops processing every
subsequent request that was ever queued or will be queued, or is caught by a
generic top-level handler that logs nothing useful and simply lets the loop
continue with no record of what failed. Fix, wrap the invocation of each
individual Method Request in its own try/catch, fulfill the corresponding
Future with the exception, so `future.get()` rethrows it to the caller with
full context, rather than swallowing it, and add an explicit test asserting
that one throwing request does not stop subsequent requests from executing.

## 12. Trade-off matrix

| Force | Active Object | Monitor Object | Half-Sync/Half-Async | Raw thread pool (no ordering) |
|---|---|---|---|---|
| Serializes access to shared mutable state | Yes, by construction, one worker per object | Yes, via mutex/condition variable inside the object | Only within the synchronous layer, the async layer is unordered | No, callers must add their own locking |
| Caller blocks on the call | No, caller gets a Future immediately | Yes, caller blocks until the monitor's lock and any wait condition are satisfied | Depends on which layer the caller is in | No, but result ordering across tasks is undefined |
| Debuggability (stack trace shows the real caller) | Poor, request executes on a different stack later | Good, execution stays on the caller's own stack | Mixed, good in the sync layer, poor across the queue boundary | Poor, task runs on a pool thread with no link back to the submitter unless deliberately added |
| Scales with more CPU cores for one object's work | No, one worker per Active Object caps its throughput | No, contention on the monitor's lock caps throughput similarly | Depends on how many workers the async layer uses | Yes, if tasks are independent |
| Natural place to add priority or rate-limit policy | Yes, in the Scheduler | No, would require a custom queue in front of the monitor | Yes, in the queueing layer between sync and async | Only if the pool's queue is replaced with a priority-aware one |
| Machinery cost per call | Higher, allocation, enqueue, possible context switch, Future | Lower, lock acquisition, no allocation for the call itself | Higher on the async side, comparable to a plain call on the sync side | Lower per call, but no serialization guarantee is provided at all |

## 13. Related and incompatible patterns

Monitor Object composes with, and is frequently confused with, Active Object,
but the two solve the same core problem, serialize access to shared state,
with opposite calling conventions. Monitor Object keeps the call synchronous
and blocks the caller inside the object's own lock and condition variables,
while Active Object makes the call asynchronous and moves execution to a
separate worker thread. They are effectively alternative implementations of
the same safety guarantee, which is why this entry lists Monitor Object under
`incompatible_with`. applying both to the same object at once, for example
wrapping a Monitor Object's already-synchronized methods behind an Active
Object's Proxy as well, adds a second, redundant serialization mechanism on
top of the first for no additional safety, only additional latency and
complexity. Choose one per object, not both.

Command composes directly with Active Object. the Method Request participant
is, plainly, a Command object carrying the receiver, the operation, and its
arguments, reified so it can be queued and executed later by a different
thread than the one that created it. Anyone already familiar with Command
will recognize the Method Request immediately.

Future/Promise composes with Active Object as the mechanism the Proxy uses to
hand back a not-yet-available result to the caller. the two patterns are
usually implemented together, but Future/Promise is independently useful in
many contexts that have nothing to do with dedicated worker threads, for
example, resolving a network response, so it is documented as its own
pattern rather than treated as inseparable from Active Object.

Reactor and Proactor are the event-demultiplexing patterns that most
real-world Active Object schedulers sit on top of when the underlying I/O is
non-blocking. rather than a naive thread that blocks on a plain queue,
production implementations frequently drive the worker's event loop from a
Reactor, synchronous event demultiplexing, readiness-based, or a Proactor,
asynchronous, completion-based. Boost.Asio's `io_context`, one of the
production examples in Dimension 9, is itself a Proactor-style event loop
that strands layer their serialization guarantee on top of.

Half-Sync/Half-Async is the broader architectural pattern of splitting a
system into a synchronous layer, an asynchronous layer, and a queueing layer
between them. a single Active Object is a natural building block to place at
the boundary of that queueing layer, giving synchronous callers a clean
interface to an asynchronous execution context underneath.

## 14. Refactoring path in and out

Introducing Active Object into code that does not have it, step by step.
First, identify the shared mutable state and every method that touches it.
this is the future Servant, and at this stage it should already compile and
pass its existing tests as an ordinary, non-thread-safe class with any
existing ad hoc locking stripped out. Second, extract a Method Request type,
or, in languages with first-class closures, a plain function or task
representing one call plus its captured arguments, for each public operation
that needs to run on the object's own thread. Third, introduce the Activation
List, a thread-safe queue that accepts Method Requests. Fourth, introduce the
Scheduler as a loop, running on one dedicated thread, or one strand, or one
single-thread executor, that dequeues and invokes requests against the
Servant. Fifth, replace the object's original public methods with a Proxy
that has the same signatures, but whose bodies now build a Method Request,
push it onto the Activation List, and return a Future instead of the direct
result. Sixth, and often skipped, update every caller. a caller that used to
receive a value directly must now either block on the Future, a minimal but
lower-value migration, or be restructured to consume the Future
asynchronously, the migration that actually captures the pattern's benefit.
Running the caller-facing change last, after the object's internals are
already safe, lets the two halves of the refactor be reviewed and tested
independently.

Removing Active Object when it no longer earns its place, step by step.
First, confirm the actual reason it is being removed. either the shared state
turned out not to need cross-thread protection at all, it became
thread-confined, or immutable, through some other change, or the
serialization bottleneck the single worker thread imposes is now the binding
constraint on throughput and a different concurrency strategy is needed.
Second, if the state is now safely thread-confined or immutable, delete the
Proxy, Method Request, Activation List, Scheduler, and Future machinery
entirely and expose the Servant's methods directly. do not leave any of the
machinery in place just in case, because half-removed Active Object
machinery, a Proxy that still exists but the queue behind it now has exactly
one, uncontended consumer, is a pure cost with no remaining safety benefit.
Third, if the bottleneck is throughput rather than safety, do not simply
delete the pattern. replace it with a strategy that still preserves
correctness while allowing more parallelism, such as sharding the Servant's
state across several Active Objects keyed by some partition, multiple
workers, each serializing only its own shard, or moving to a Monitor Object
if callers can tolerate blocking and the lock's hold time is short enough
that contention is not actually the problem. Fourth, in either direction,
keep the tests written for the Servant's behavior in Dimension 15 unchanged
across the refactor. if those tests genuinely tested behavior rather than
threading mechanics, they should pass before and after with no modification,
which is itself the strongest evidence the refactor was done correctly.

## 15. Testing and verification

This dimension is substantially engineering judgement drawn from testing
practice around message-queue-based designs, rather than a single citable
source. treat the specific techniques as practice, not as universally
mandated law.

The single biggest testability win the pattern offers is that the Servant can
be unit tested with zero concurrency at all. construct it directly,
bypassing the Proxy and the worker thread entirely, and call its methods
synchronously on the test thread. Because the Servant contains no locking or
threading logic by design, these tests are exactly as simple as testing any
ordinary class, and this is where the majority of behavioral test coverage
should live.

Testing the Proxy, Scheduler, and Activation List together, the concurrency
machinery itself, needs a different technique. submit multiple Method
Requests from multiple test threads concurrently and assert on the observed
execution order and on the fact that no two requests were ever observed
executing simultaneously. A simple, effective assertion is to have each
Method Request append a distinct marker to a synchronized list of
currently-executing markers on entry and remove it on exit, then assert that
list never contained more than one marker at once across the whole run. this
directly tests the mutual-exclusion guarantee rather than inferring it
indirectly from timing.

Testing failure propagation deserves its own explicit test, given how common
silent exception swallowing is in Dimension 11. submit a Method Request whose
Servant method deliberately throws, and assert that the corresponding Future
surfaces that exact exception to the caller, and separately assert that a
subsequent, unrelated Method Request submitted after the throwing one still
executes successfully, which specifically guards against the failure mode
where one bad request kills the worker loop for every request that comes
after it.

Testing backpressure and queue-bound behavior, where a bounded Activation
List is used, means deliberately saturating the queue, submitting requests
faster than the single worker can drain them, or holding the worker busy
with a long-running request while submitting more, and asserting the chosen
policy actually triggers. that the producer blocks, that a rejection
exception is thrown, or that the intended drop-oldest behavior is what
happens, rather than assuming the policy works because it was configured.

Test doubles apply differently to each participant. The Servant is the
natural target for the usual dependency-injected fakes and mocks, exactly as
it would be if it were not wrapped in an Active Object at all. The Scheduler
and Activation List are rarely faked in tests. because they are thin,
generic infrastructure, often a language or library primitive, per Dimension
8, it is usually more valuable to test the real implementation under
concurrent load than to fake it away.

## 16. Observability signals

Queue depth, the current number of pending Method Requests in the Activation
List, is the single most important gauge to export, sampled continuously, not
just at failure time. A queue depth that trends upward over time, rather than
oscillating around some steady-state value, is the earliest and clearest
signal of the sustained-overload failure mode described in Dimension 11,
visible well before memory pressure or latency actually becomes user-visible.

Time-in-queue per request, the interval between a Method Request being
enqueued and the Scheduler dequeuing it to begin execution, separates the
object being slow because requests wait a long time before starting from the
object being slow because individual requests take a long time to run once
started, which are different problems requiring different fixes. the first
suggests the queue is overloaded or the worker is stuck, the second suggests
the Servant's own method bodies need optimizing.

Execution time per request, tagged by method or request type if the object
handles more than one kind of operation, distinguishes which specific
operations are expensive and is the metric that should be broken down by
percentile, p50, p95, p99, since a single average hides exactly the kind of
tail latency that a serialized single-worker design is most vulnerable to.
one occasional slow request delays every request queued behind it.

Worker thread liveness, meaning a heartbeat or a last-successful-completion
timestamp gauge for the Scheduler's loop, is what catches the silent-death
failure mode from Dimension 11 where an unhandled exception kills the worker
thread outright. without an explicit liveness signal, a dead worker looks
identical to an idle one from the outside. requests simply stop completing,
with no crash, no error log, and no obvious signal unless one was
deliberately instrumented.

A healthy Active Object, on a dashboard, looks like a queue depth that
oscillates near zero or near some small, predictable working set, execution
time percentiles that are stable over time and match expectations for the
operations being performed, and a worker liveness heartbeat that never goes
stale. A failing one shows an unboundedly growing queue depth, a growing gap
between p50 and p99 execution time as some request classes start starving
behind others, or a worker liveness heartbeat that simply stops advancing
while enqueue rate continues climbing, which is the unmistakable signature of
a dead worker thread silently absorbing new requests into a queue that will
now never drain.

## 17. Security and privacy implications

This dimension is analytical judgement, not a set of documented CVEs specific
to the pattern. the concerns below follow from the pattern's structure.

The Activation List is, structurally, an unbounded buffer of attacker- or
user-influenced input if any Method Request or its arguments derive from
external, untrusted sources, and an unbounded or poorly bounded queue in that
position is a straightforward denial-of-service vector. a client that can
submit requests faster than the single worker can drain them can grow the
queue until the process exhausts memory, independent of whether any
individual request is otherwise well-formed. The fix from Dimension 11,
bound the queue, choose an explicit backpressure policy, is also, directly,
the mitigation for this attack surface, and it is worth treating the
Activation List's bound and what happens when it is hit as a security
review question, not only a performance question, on any Active Object that
accepts requests originating outside a trusted boundary.

Method Requests captured for logging, tracing, or replay, a legitimate and
common use of the pattern's reified-call structure, per Dimension 10, can
carry sensitive arguments, credentials, personal data, payment details,
verbatim into a log store or trace system that has weaker access controls or
longer retention than the original call site intended. because the pattern
makes it trivially easy to add a generic log-every-Method-Request-on-enqueue
hook, it is also trivially easy for that hook to capture arguments nobody
meant to persist, and any such logging hook needs the same field-level
redaction discipline that direct logging of sensitive method arguments would
require anyway.

A single shared worker thread executing requests from multiple, potentially
mutually distrusting callers means the Servant's per-request execution time
is itself an observable side channel between callers who share the same
Active Object instance. one caller can, in principle, infer something about
another caller's request, its size, its computational cost, even its
approximate content in some cases, by observing changes in their own
requests' queueing latency. This is the same class of timing side channel
that any shared, serialized resource exhibits, and it is worth naming
explicitly for any Active Object whose Servant handles requests from
mutually distrusting principals rather than assuming shared infrastructure
is automatically safe to share across trust boundaries.

## 18. References

- Douglas C. Schmidt, Michael Stal, Hans Rohnert, Frank Buschmann.
  *Pattern-Oriented Software Architecture, Volume 2, Patterns for Concurrent
  and Networked Objects*. John Wiley and Sons, 2000. Chapter on Concurrency
  Patterns, the Active Object pattern. Attribution confirmed via
  https://en.wikipedia.org/wiki/Active_object (verified 2026-08-13), which
  cites this book as the primary reference for the pattern.
- R. Greg Lavender, Douglas C. Schmidt. "Active Object, an Object Behavioral
  Pattern for Concurrent Programming." Washington University technical
  report and pattern language paper, mid-1990s. PDF located at
  https://www.dre.vanderbilt.edu/~schmidt/PDF/Act-Obj.pdf (verified reachable
  2026-08-13. the PDF text layer did not extract cleanly during this entry's
  authoring, so its exact wording is not quoted here, only its existence and
  authorship, which are corroborated by the Wikipedia reference above).
- Android Developers. "Processes and threads overview." Recommends using a
  `Handler` bound to a worker thread to process messages delivered across
  threads. https://developer.android.com/guide/components/processes-and-threads
  (verified 2026-08-13, quoted in Dimension 9).
- Qt Documentation. "Threads and QObjects," Qt 6. Documents queued
  connections executing the receiver's slot on the receiver's own thread via
  that thread's event loop. https://doc.qt.io/qt-6/threads-qobject.html
  (verified 2026-08-13, quoted in Dimension 9).
- Boost C++ Libraries. "Boost.Asio, Strands, Use Threads Without Explicit
  Locking," Boost 1.85.0 documentation. Defines a strand's guarantee of
  strictly sequential, non-concurrent handler invocation.
  https://www.boost.org/doc/libs/1_85_0/doc/html/boost_asio/overview/core/strands.html
  (verified 2026-08-13, quoted in Dimension 9).
- Oracle. `java.util.concurrent.Executors` class documentation, Java SE 17.
  Documents `newSingleThreadExecutor()`'s guarantee of sequential,
  non-concurrent task execution off a single worker thread.
  https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/Executors.html
  (verified 2026-08-13, quoted in Dimensions 8 and 9).

## Code examples

### TypeScript

```typescript
type MethodRequest<T> = () => Promise<T>;

class ActiveObjectScheduler {
  private queue: MethodRequest<unknown>[] = [];
  private draining = false;

  submit<T>(request: MethodRequest<T>): Promise<T> {
    return new Promise<T>((resolve, reject) => {
      this.queue.push(async () => {
        try {
          resolve(await request());
        } catch (err) {
          reject(err);
        }
      });
      this.drain();
    });
  }

  private async drain(): Promise<void> {
    if (this.draining) return;
    this.draining = true;
    while (this.queue.length > 0) {
      const next = this.queue.shift()!;
      await next();
    }
    this.draining = false;
  }
}

class CounterServant {
  private value = 0;
  increment(by: number): number {
    this.value += by;
    return this.value;
  }
}

class CounterProxy {
  private servant = new CounterServant();
  private scheduler = new ActiveObjectScheduler();

  increment(by: number): Promise<number> {
    return this.scheduler.submit(() => Promise.resolve(this.servant.increment(by)));
  }
}

async function main(): Promise<void> {
  const counter = new CounterProxy();
  const results = await Promise.all([
    counter.increment(1),
    counter.increment(2),
    counter.increment(3),
  ]);
  console.log(results);
}

main();
```

### Python

```python
import asyncio
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class MethodRequest:
    fn: Callable[[], Any]
    future: "asyncio.Future[Any]"


class Scheduler:
    def __init__(self) -> None:
        self._queue: "asyncio.Queue[MethodRequest]" = asyncio.Queue()
        self._worker: asyncio.Task[None] | None = None

    def start(self) -> None:
        self._worker = asyncio.create_task(self._run())

    async def submit(self, fn: Callable[[], Any]) -> Any:
        future: "asyncio.Future[Any]" = asyncio.get_event_loop().create_future()
        await self._queue.put(MethodRequest(fn, future))
        return await future

    async def _run(self) -> None:
        while True:
            request = await self._queue.get()
            try:
                request.future.set_result(request.fn())
            except Exception as exc:
                request.future.set_exception(exc)


class CounterServant:
    def __init__(self) -> None:
        self._value = 0

    def increment(self, by: int) -> int:
        self._value += by
        return self._value


class CounterProxy:
    def __init__(self) -> None:
        self._servant = CounterServant()
        self._scheduler = Scheduler()
        self._scheduler.start()

    async def increment(self, by: int) -> int:
        return await self._scheduler.submit(lambda: self._servant.increment(by))


async def main() -> None:
    counter = CounterProxy()
    results = await asyncio.gather(
        counter.increment(1), counter.increment(2), counter.increment(3)
    )
    print(results)


if __name__ == "__main__":
    asyncio.run(main())
```

### Go

```go
package main

import "fmt"

type methodRequest struct {
	fn     func() int
	result chan int
}

type scheduler struct {
	queue chan methodRequest
}

func newScheduler() *scheduler {
	s := &scheduler{queue: make(chan methodRequest, 64)}
	go s.run()
	return s
}

func (s *scheduler) run() {
	for req := range s.queue {
		req.result <- req.fn()
	}
}

func (s *scheduler) submit(fn func() int) <-chan int {
	result := make(chan int, 1)
	s.queue <- methodRequest{fn: fn, result: result}
	return result
}

type counterServant struct {
	value int
}

func (c *counterServant) increment(by int) int {
	c.value += by
	return c.value
}

type counterProxy struct {
	servant   *counterServant
	scheduler *scheduler
}

func newCounterProxy() *counterProxy {
	return &counterProxy{servant: &counterServant{}, scheduler: newScheduler()}
}

func (p *counterProxy) increment(by int) <-chan int {
	return p.scheduler.submit(func() int {
		return p.servant.increment(by)
	})
}

func main() {
	counter := newCounterProxy()
	f1 := counter.increment(1)
	f2 := counter.increment(2)
	f3 := counter.increment(3)
	fmt.Println(<-f1, <-f2, <-f3)
}
```

### Rust

```rust
use std::sync::mpsc;
use std::thread;

enum MethodRequest {
    Increment(i64, mpsc::Sender<i64>),
}

struct CounterServant {
    value: i64,
}

impl CounterServant {
    fn increment(&mut self, by: i64) -> i64 {
        self.value += by;
        self.value
    }
}

struct CounterProxy {
    sender: mpsc::Sender<MethodRequest>,
}

impl CounterProxy {
    fn new() -> Self {
        let (sender, receiver) = mpsc::channel::<MethodRequest>();
        thread::spawn(move || {
            let mut servant = CounterServant { value: 0 };
            for request in receiver {
                match request {
                    MethodRequest::Increment(by, reply_to) => {
                        let result = servant.increment(by);
                        let _ = reply_to.send(result);
                    }
                }
            }
        });
        CounterProxy { sender }
    }

    fn increment(&self, by: i64) -> i64 {
        let (reply_to, reply_from) = mpsc::channel();
        self.sender
            .send(MethodRequest::Increment(by, reply_to))
            .expect("worker thread should still be alive");
        reply_from.recv().expect("worker thread should reply")
    }
}

fn main() {
    let counter = CounterProxy::new();
    let a = counter.increment(1);
    let b = counter.increment(2);
    let c = counter.increment(3);
    println!("{} {} {}", a, b, c);
}
```

All four samples were run against the local toolchain during authoring.
`npx tsc --noEmit` for the TypeScript sample, `python3 -m py_compile` for the
Python sample, `go build` for the Go sample, and `rustc` for the Rust sample.
Java and C# were not authored for this entry. Java's role in the pattern is
already covered directly through the `Executors.newSingleThreadExecutor()`
production-use citation in Dimension 9, and a hand-rolled Java sample would
largely duplicate that standard-library call rather than illustrate anything
additional.
