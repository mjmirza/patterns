---
name: Future Promise
slug: future-promise
family: 09-concurrency
category: Concurrency
aliases: [Eventual, Deferred, Delay, Task, CompletionStage]
first_described: "Baker and Hewitt 1977, Friedman and Wise 1976"
maturity: canonical
related: [thread-pool, active-object, producer-consumer, reactor, half-sync-half-async]
incompatible_with: []
verified: 2026-08-02
---

# Future Promise

## 1. Name, aliases, and lineage

The pattern has two names attached to two ends of the same object, and most of
the confusion around it comes from treating the names as synonyms rather than
roles. A future is the read side, a handle a caller holds to ask for a result
that does not exist yet. A promise is the write side, a handle the producer of
that result holds to fill it in exactly once. In many languages the two roles
collapse into a single object with methods for both sides, and in others they
are split into two distinct types on purpose so that a caller who only holds
the future cannot also complete it.

The concept was proposed twice, independently, within a year. Daniel P.
Friedman and David S. Wise used the word "promise" in a 1976 technical report
on call by need in applicative languages, describing a promise as a
placeholder for a value that a producer would eventually deliver
([Wikipedia, Futures and promises, section History](https://en.wikipedia.org/wiki/Futures_and_promises),
verified 2026-08-02, summarising Friedman and Wise's original report). Henry
C. Baker Jr. and Carl Hewitt described the "future" the following year, in a
1977 paper on the incremental garbage collection of processes, where a future
represented the eventual result of a computation that ran concurrently with
its caller (same Wikipedia article, section History, verified 2026-08-02). The
two threads of work, one from the Scheme and applicative language community,
one from the actor model community around Hewitt's group at MIT, converged on
the same shape from different motivations. Friedman and Wise wanted lazy
evaluation with a memoised result. Baker and Hewitt wanted concurrency without
callbacks. The same article records that MultiLisp, an early parallel dialect
of Scheme, and Act 1, an actor language, were the first languages to ship the
construct as a language feature rather than a library idea.

The name split into "future" and "promise" as two words for the same idea
happened later, largely through the E programming language community and
through Barbara Liskov and Liuba Shrira's 1988 paper on promise pipelining in
the Argus language, which used "promise" for the client visible placeholder
([Wikipedia, Futures and promises, section History](https://en.wikipedia.org/wiki/Futures_and_promises),
verified 2026-08-02). By the time the pattern reached mainstream server side
languages in the 2000s and 2010s, "future" had become the conventional name
for the read only handle and "promise" the conventional name for the write
once handle, and that is the convention this entry follows. JavaScript kept
only the word "promise" for both roles, because the ECMAScript committee
folded the producer and consumer sides into one object rather than splitting
them, a decision reflected in ECMAScript 2015's standardisation of the
`Promise` global
([MDN Web Docs, Using promises](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Using_promises),
verified 2026-08-02). Java went the other way and kept only "future," naming
its interface `Future` when it shipped in Java 5 in 2004 as part of
`java.util.concurrent`, a package designed by Doug Lea under JSR-166, whose
original interfaces are catalogued in the package javadoc
([Oracle Java SE 8 Javadoc for java.util.concurrent](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/package-summary.html),
verified 2026-08-02). C# calls the same shape `Task`. .NET's Task Parallel
Library shipped it as the primary asynchronous primitive with .NET Framework
4.0 in 2010 and added the `async`/`await` keywords that consume it in .NET
4.5, released 2012
([Microsoft Learn, Task-based asynchronous programming](https://learn.microsoft.com/en-us/dotnet/standard/asynchronous-programming-patterns/task-based-asynchronous-pattern-tap),
verified 2026-08-02). Twitter's Scala library named its type `Future`
explicitly and paired it with a `Promise` that fulfils it, and that
Future/Promise split is the version most books borrow their vocabulary from.

## 2. Problem and context

A piece of code needs a value that will not be ready immediately. It might
come from a network call, a disk read, a background thread, or a computation
that is deliberately deferred to run in parallel with something else. Two
older techniques handle this, and both have the same failure. blocking calls
tie up a thread of control for the entire wait, and callback registration
scatters the logic for "when this is done" across a function signature that
grows a new parameter for every operation it might chain.

The concrete situation looks like this. A service handler needs a user record
from a database and a permission check from an authorisation service, and it
wants both requests in flight at once rather than one after the other. A
callback based interface for this means passing two functions into two calls,
then writing the combining logic inside whichever callback happens to run
second, plus tracking which one that is. Add a third dependent call and the
callback nesting deepens again, and error handling has to be threaded through
every callback separately because there is no single place an exception from
either call can surface. This is the shape widely referred to as callback
hell, and it is a real, observable maintenance cost, not a subjective
complaint, because each additional dependency multiplies the number of
control flow paths a reader has to hold in their head at once.

The context that produces the need is asynchronous work whose result is
consumed by code that did not initiate it, often code that wants to combine,
chain, or wait on several such results together. The future/promise pattern
gives that result a first class value, an object the caller can pass around,
store in a collection, combine with "all"/"any"/"race" style combinators, and
compose with `.then` or `await` without the caller and the producer needing a
shared callback signature negotiated in advance. It turns "I will call you
back" into "here is a handle to a value that arrives later," which changes an
asynchronous operation from a control flow inversion into an ordinary first
class value that composes the way any other value does.

## 3. Forces

**Composability against explicitness.** A future that supports `.then`,
`Promise.all`, and `async`/`await` is trivial to chain and combine, but that
same composability hides exactly where and on which thread a continuation
runs, which becomes a debugging problem the first time a continuation runs on
an unexpected executor or blocks a thread it should not.

**Latency hiding against resource cost.** Starting work eagerly, the moment
the future is created, hides latency because the work is already running by
the time anything asks for the result. That eagerness also means work is
started and its resources consumed even for a future nobody ever awaits,
which is the deliberate trade every eager future implementation makes,
against languages such as C# and Haskell where a `Task` or lazy computation
does not start until awaited or forced.

**Exactly once completion against liveness.** The promise side is a write
once cell by design, deliberately restricting who can complete a future and
how many times. That restriction is what makes a future safe to hand to many
readers, but it means a producer that crashes or forgets to complete the
promise leaves every reader blocked forever unless a timeout or cancellation
mechanism exists outside the pattern itself.

**Error propagation against silent swallowing.** A future's rejection path
carries an exception the same way a synchronous call would throw one, and
that symmetry is one of the pattern's strongest properties. It is also a
trap. an unread, unhandled rejected promise is silently dropped in some
runtimes and crashes the process in others, and the difference between those
two behaviours is a frequent source of production incidents, covered further
under Failure modes.

**Team topology and cognitive load.** A team fluent in `async`/`await` reads
future based code nearly as linearly as synchronous code, at the cost of
every engineer needing a correct mental model of which operations are
concurrent and which are sequential, a distinction that disappears from the
surface syntax the moment `await` makes asynchronous code look synchronous.

The pattern favours composability, latency hiding, and readable chaining. It
costs debuggability of execution order, up front resource cost for eager
implementations, and the operational risk of a promise nobody ever completes.

## 4. Applicability and non-applicability

Reach for future/promise when:

- An operation is inherently asynchronous, meaning its result genuinely
  arrives at an unpredictable later time, such as network I/O, disk I/O, a
  timer, or work handed off to another thread or process.
- Multiple independent asynchronous operations need to run concurrently and
  then be combined, the textbook case being `Promise.all` or
  `CompletableFuture.allOf` over several requests that do not depend on each
  other.
- The caller needs to keep doing other work, or return control to an event
  loop, while the result is pending, rather than blocking a thread for the
  entire duration.
- The language or runtime already has first class support for the pattern,
  because a hand rolled future/promise implementation is easy to get subtly
  wrong around cancellation, exactly once completion, and exception
  propagation, all covered under Failure modes.
- A public API needs to expose "this will complete later" without forcing
  every caller to supply a callback at the call site, so the caller decides
  how to consume the eventual value rather than the API author deciding for
  them.

Do NOT reach for future/promise when:

- The work is CPU bound and single threaded with no actual concurrency to
  exploit. Wrapping a synchronous computation in a `Promise.resolve()` or an
  `async` function that never awaits anything adds allocation and
  microtask queue overhead for no benefit, and it also silently changes when
  errors are observable, deferring them from the call site to whenever the
  promise is eventually inspected.
- A simple, single, blocking call is genuinely acceptable, for example a
  short lived CLI tool making one network request and then exiting. A
  synchronous call with a clear stack trace on failure is easier to debug
  than an asynchronous chain, and the composability future/promise offers has
  no dependent operations to compose with.
- A stream of values is needed rather than a single eventual value. A future
  resolves exactly once. Repeated events over time need an Observable,
  a Reactive Stream, or a plain channel, not a future, and forcing repeated
  values through a future means either resolving with a collection, losing
  incrementality, or creating a new future per event, losing the point of the
  pattern. See Related patterns for the boundary with Reactive Streams.
- Tight, low level concurrency where the overhead of an allocation per
  operation, a scheduler hop per continuation, and a heap allocated state
  machine matters, such as inside a hot path of a high frequency trading
  system or an embedded real time control loop. Those contexts favour
  hand rolled lock free structures or synchronous designs precisely because
  future/promise trades raw throughput for composability.
- Go, as commonly written, deliberately does not have a native future/promise
  type in its standard library. The language's own concurrency documentation
  favours channels and goroutines as the composition primitive instead of a
  future object, and idiomatic Go code that needs a single eventual value
  from a goroutine typically uses a buffered channel of size one as the
  handle, which is structurally a future/promise pair without the name
  ([Effective Go, section Concurrency](https://go.dev/doc/effective_go#concurrency),
  verified 2026-08-02, describing channel based communication as the
  language's answer to shared eventual state). Reaching for a
  future/promise shaped library in Go where a channel would be idiomatic adds
  a foreign vocabulary to a codebase that already has a native answer.

## 5. Structure

- **Future.** A read only handle to a value that may not exist yet. Exposes
  operations to inspect completion state, to block for the value in
  blocking flavours, to register a continuation that runs when the value
  arrives in callback flavours, and to be awaited directly in
  language integrated flavours such as JavaScript's `await` or C#'s
  `await`. The future does not know how or when its value will be produced,
  only that it will observe the result once, either a success value or a
  failure.
- **Promise.** A write once handle held by the producer of the value. Exposes
  exactly two terminal operations, complete with a success value or complete
  with a failure, and a mechanism, usually an exception on the second call,
  that prevents completing it twice. In split API languages the promise and
  the future it produces are distinct objects returned as a pair. In single
  object languages such as JavaScript the promise executor function plays
  this role internally, and the object the caller holds serves both roles at
  once.
- **Executor or scheduler.** The thing that actually performs the
  asynchronous work and eventually calls complete on the promise. This is
  usually a thread pool, an event loop, an I/O completion port, or another
  future being awaited. The pattern deliberately does not specify what the
  executor is, which is why future/promise composes cleanly with Thread
  Pool, Reactor, and Proactor.
- **Continuation.** The function registered on a future to run once it
  completes, whether via `.then`, `.thenApply`, `.map`, or the implicit
  continuation an `await` expression represents once desugared by the
  compiler. A continuation itself often returns a new future, which is how
  chains compose without nested callbacks.
- **Combinator.** A function that takes several futures and produces one new
  future representing their combination, the canonical examples being "all,"
  wait for every input to succeed and fail fast on the first failure, "race"
  or "any," resolve with the first to settle, and "allSettled," wait for
  every input regardless of success or failure and report each outcome.

## 6. ASCII structure diagram

```
                     +-----------------------+
                     |    Producer thread     |
                     |  (I/O callback, pool    |
                     |   worker, event loop)   |
                     +-----------+-------------+
                                 |
                          holds  | complete(value)
                                 v                       complete(error)
                     +-----------------------+                  |
                     |        Promise         |<-----------------+
                     |  write-once, exactly    |
                     |     one completion      |
                     +-----------+-------------+
                                 |
                          shared |  linked state cell
                                 v
                     +-----------------------+
                     |         Future          |
                     |  read-only handle,       |
                     |  observed many times     |
                     +-----+---------+----------+
                           |         |
             .then(fn) /   |         |  await, or
             thenApply(fn) |         |  future.get() blocking
                           v         v
                +-----------------+  +------------------+
                |  Continuation A  |  |   Caller thread   |
                | (registered by   |  |  (blocks or        |
                |  consumer 1)     |  |   suspends until   |
                +--------+---------+  |   settled)          |
                         |            +--------------------+
                         v
              +---------------------+
              |  new Future (chain)  |
              |  from continuation's |
              |    return value      |
              +----------------------+
```

## 7. Dynamics

```
Time --->

Producer thread                Promise/Future state         Consumer

start async op ----------->    [pending]
                                    ^
                                    | (state cell shared,
                                    |  visible to both sides)
                                                              register continuation
                                                              or await ------------>  [suspended,
                                                                                        waiting on
                                                                                        state cell]

op completes successfully -->  [fulfilled, value=V]
      promise.complete(V)             |
                                       | notify all registered
                                       | continuations, in
                                       | registration order
                                       v
                                                              continuation runs
                                                              with V, returns
                                                              new future or value
                                                              <---------------------  [resumed]

--- alternative failure path ---

op raises exception -------->  [rejected, error=E]
      promise.fail(E)                 |
                                       v
                                                              continuation's error
                                                              handler runs with E,
                                                              or exception propagates
                                                              out of await
                                                              <---------------------  [resumed with
                                                                                        thrown error]

--- late registration ---

(future already fulfilled)
                                [fulfilled, value=V]  <-- second consumer registers
                                                            a continuation here
                                       |
                                       | runs immediately,
                                       | synchronously or on
                                       | next microtask tick
                                       v
                                                              continuation runs
                                                              with V right away
```

The two invariants a correct implementation must hold across every path in
this diagram are that the state cell transitions at most once from pending to
a terminal state, fulfilled or rejected, and that a continuation registered
after the terminal state is reached still runs with that terminal value,
never silently dropped. Both invariants are stated explicitly in the
Promises/A+ specification section 2.2, which multiple production JavaScript
engines implement, requiring `onFulfilled` or `onRejected` to be called only
after the promise is settled and never called more than once
([Promises/A+ specification, section 2.2](https://promisesaplus.com/),
verified 2026-08-02).

## 8. Implementation variants

**Language integrated async/await, sugar over futures.** JavaScript,
Python via `asyncio`, C#, Rust, and Kotlin coroutines all compile an
`async`/`await` or `suspend` function into a state machine that pauses at
each `await` point and resumes when the awaited future settles. The
programmer writes what reads as sequential, blocking looking code, and the
compiler or runtime does the continuation wiring. This is the dominant
production variant because it removes the callback nesting cost entirely
while keeping the future object available underneath for anyone who needs
explicit combinators.

**Split future/promise pair, explicit producer API.** C++'s
`std::promise<T>`/`std::future<T>`, Scala's `Future`/`Promise`, and many
actor framework APIs return the future and promise as two distinct objects
from a factory function, so the code that produces the value and the code
that consumes it hold different types with different capabilities. This
variant makes the write once contract a compile time or type level guarantee
rather than a runtime check, at the cost of an extra object to pass around.
C++11 introduced `std::promise` and `std::future` as part of the `<future>`
header, with `std::promise::set_value` completing the promise and
`std::future::get` blocking for the result, documented in the C++ standard
library reference for the `<future>` header
([cppreference.com, std::future](https://en.cppreference.com/w/cpp/thread/future),
verified 2026-08-02).

**Callback registration API without an explicit await.** Twitter's Finagle
`com.twitter.util.Future` and much of pre ES2015 Node.js used `.then`,
`.onSuccess`, `.onFailure` style registration without any language level
`await`. This variant is the direct predecessor to the async/await sugar
above and is still the correct choice in languages or runtimes that never
grew coroutine support, or in libraries that must remain usable from
synchronous call sites that cannot themselves become async.

**Blocking get with a bounded executor.** Java's `java.util.concurrent.Future`
as originally shipped in Java 5 only exposed a blocking `get()` with an
optional timeout, no chaining at all. `CompletableFuture`, added in Java 8,
layered the chaining and combinator API, `thenApply`, `thenCombine`,
`allOf`, on top of the same underlying completion state, which is why modern
Java code almost always uses `CompletableFuture` and treats the plain
`Future` interface as a lowest common denominator return type
([Oracle Javadoc, CompletableFuture](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/CompletableFuture.html),
verified 2026-08-02, describing it as "A Future that may be explicitly
completed... and may be used as a CompletionStage").

**Thread pool backed blocking future for CPU work.** Python's
`concurrent.futures.Future`, produced by `ThreadPoolExecutor.submit` or
`ProcessPoolExecutor.submit`, wraps a computation that runs on a worker
thread or process and exposes `result()`, a blocking call, alongside
`add_done_callback` for a non blocking style. This is a deliberately
different variant from `asyncio.Future`, which is designed for single
threaded cooperative concurrency, and the two are not interchangeable
without an explicit bridge
([Python documentation, concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html),
verified 2026-08-02, stating the module "was added in version 3.2" and that
`Future` "encapsulates the asynchronous execution of a callable").

**Deferred style manual construction.** Some libraries, notably older jQuery
via `$.Deferred` and Q in early Node.js, exposed a `Deferred` object with
`resolve`/`reject` methods and a `.promise` property that returned the
restricted read only view, matching the split pair variant above but built
manually in a language without native promise support. The `deferred<T>`
helper in the TypeScript example under Code examples reconstructs this
pattern directly for cases where the executor callback style of the native
`Promise` constructor is awkward, such as resolving a promise from an event
listener registered elsewhere.

## 9. Known production uses

- **Google Guava's `ListenableFuture`.** Extended Java's plain `Future` with
  `addListener`, letting callers register a callback instead of blocking, and
  predates `CompletableFuture` in wide production use across Google's
  internal Java services and countless open source consumers such as gRPC's
  Java client. The Guava user guide documents `ListenableFuture` as "a Future
  that accepts completion listeners" and recommends it explicitly for
  combining and chaining asynchronous computations
  ([Guava wiki, ListenableFutureExplained](https://github.com/google/guava/wiki/ListenableFutureExplained),
  verified 2026-08-02).
- **Twitter's Finagle RPC framework.** Built its entire request/response
  model on `com.twitter.util.Future`, which predates `CompletableFuture` and
  was Twitter's answer to the same callback nesting problem inside their
  Scala services stack, described in the Finagle documentation as returning
  "a `Future[Rep]` representing the future result of the RPC"
  ([Finagle User's Guide, section Services](https://twitter.github.io/finagle/guide/ServicesAndFilters.html),
  verified 2026-08-02).
- **Node.js and every major browser's JavaScript engine.** `Promise` shipped
  as a built in global with ECMAScript 2015, the sixth edition of the
  language specification, and every subsequent `fetch`, `fs.promises`, and
  `async`/`await` feature in the platform is built directly on it. MDN
  documents `Promise` as representing "the eventual completion (or failure)
  of an asynchronous operation and its resulting value"
  ([MDN Web Docs, Promise](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise),
  verified 2026-08-02).
- **.NET's Task Parallel Library, used across ASP.NET Core.** Every
  ASP.NET Core controller action, Entity Framework Core query, and
  `HttpClient` call in the .NET ecosystem returns or awaits a `Task<T>`,
  which is Microsoft's name for the same future/promise construct, and the
  framework's asynchronous programming guidance treats `Task` as the unit of
  composition for all I/O
  ([Microsoft Learn, Asynchronous programming with async and await](https://learn.microsoft.com/en-us/dotnet/csharp/asynchronous-programming/),
  verified 2026-08-02).
- **Rust's async ecosystem, Tokio and async-std.** Rust's `std::future::Future`
  trait, stabilised alongside `async`/`await` syntax in Rust 1.39 in November
  2019, is the trait every async runtime in the Rust ecosystem, including
  Tokio, implements against, and the Rust documentation describes a future as
  representing "an asynchronous computation that can produce a value"
  ([The Rust Async Book, chapter 2](https://rust-lang.github.io/async-book/02_execution/02_future.html),
  verified 2026-08-02).

## 10. Consequences

Positive.

- Turns "call me back when this is done" into a first class value that can be
  stored, passed to a function, placed in a collection, and combined with
  other futures, which is a strictly more composable interface than a bare
  callback parameter.
- Symmetric error handling. A rejected future propagates through `.then`
  chains or `await` expressions the same way a thrown exception propagates
  through synchronous call stacks, so a caller can use one `catch` or
  `try`/`except` block to handle failures from several asynchronous steps.
- Decouples the producer of an asynchronous result from every consumer of it.
  A producer completes a promise once, and any number of independent
  consumers can register continuations or await the resulting future without
  the producer knowing how many consumers exist or coordinating with them.
- Composes cleanly with async/await syntax where the language provides it,
  which lets asynchronous code read close to sequential code without giving
  up the underlying concurrency, directly addressing the callback nesting
  cost named in Problem and context.
- Combinators such as "all," "race," and "allSettled" express common
  concurrency shapes, fan out and join, first response wins, best effort
  gather, as single expressions instead of hand rolled counters and
  callbacks.

Negative.

- Hides execution order and threading behind syntax that looks synchronous.
  An `await` expression gives no visual signal of which thread, which
  executor, or whether the continuation runs synchronously or is deferred to
  a later tick, which is a real cost when debugging a deadlock or a
  surprising interleaving.
- A promise that is never completed leaves every waiting consumer suspended
  or blocked indefinitely, with no bound unless the caller layers a timeout
  on top, because the pattern itself specifies no liveness guarantee.
- Eager execution, the default in most implementations, means work starts
  and consumes resources at future creation time regardless of whether
  anyone ever reads the result, which is a resource leak risk distinct from
  the pattern's error handling.
- Stack traces across asynchronous boundaries are often shallow or
  misleading, because the call that eventually threw the exception ran on a
  different logical stack than the code that is inspecting the failure,
  covered further under Observability signals.
- An allocation per future, per continuation link, and often per chained
  `.then` call adds real overhead that matters in high throughput, low
  latency code paths, which is why the pattern is avoided in the tightest
  hot loops as named under Applicability and non-applicability.

## 11. Failure modes and misuse

**Unhandled rejection silently dropped.** Symptom. an asynchronous failure
never surfaces anywhere, the operation appears to simply not finish, and
nothing in the logs mentions an error. Cause. a promise is rejected but no
`.catch`, no error handler in an `await` wrapped `try`/`catch`, and no
`onRejected` continuation is ever attached to it, so the rejection has
nowhere to go. In Node.js and browsers this now triggers an
`unhandledrejection` event and, in recent Node versions, terminates the
process by default rather than swallowing it silently, a deliberate
tightening of the runtime's original permissive behaviour
([Node.js documentation, Warning: Unhandled promise rejections](https://nodejs.org/api/process.html#event-unhandledrejection),
verified 2026-08-02). Fix. attach error handling on every promise chain that
is not itself returned to a caller who will handle it, and in Node.js, treat
`unhandledRejection` events as a startup blocking bug class, not a warning to
ignore.

**Forgotten promise, permanent hang.** Symptom. a request handler or worker
never completes, times out at whatever layer above it enforces a timeout, and
thread or connection pool exhaustion follows as more requests pile up behind
the stuck one. Cause. code obtains a promise, for example from
`new Promise((resolve, reject) => {...})` or a raw `CompletableFuture<T>()`,
but a code path inside the executor function returns early, throws before
calling resolve, or the producing thread crashes without ever calling
`complete` or `set_value`. Fix. wrap promise completing code in a structure
that guarantees completion on every exit path, including exceptional ones,
and set an explicit timeout at the point a future is awaited whenever the
completing code is not fully under the caller's control.

**Double completion race.** Symptom. inconsistent test failures, or a value
that is sometimes correct and sometimes stale, particularly under load. Cause.
two different code paths race to complete the same promise, for example a
success path and a timeout path both firing close together, and the
implementation's write once guarantee silently discards the second attempt
rather than surfacing that a race occurred. `std::promise::set_value` throws
`std::future_error` with `promise_already_satisfied` on a second call
([cppreference.com, std::promise::set_value](https://en.cppreference.com/w/cpp/thread/promise/set_value),
verified 2026-08-02), while other implementations, such as JavaScript's
`Promise` executor, silently ignore a second `resolve`/`reject` call with no
error at all. Fix. know which behaviour your runtime has, and if it is the
silent ignore kind, add explicit logging or an assertion around any code path
where two completions could plausibly race, so the race is visible instead of
hidden.

**Blocking on a future inside an event loop thread.** Symptom. the entire
application freezes for the duration of one slow operation, even though only
one logical request was waiting on it. Cause. calling a blocking method such
as `future.get()` from `java.util.concurrent.Future` or `.result()` from a
Python `concurrent.futures.Future` from inside a single threaded event loop
or reactor thread, which starves every other pending task that shares that
thread, defeating the entire purpose of using futures in that runtime. Fix.
in event loop based runtimes, never call the blocking accessor from inside
the loop thread. use the non blocking chaining or await style consistently,
and reserve blocking `get()` calls for genuinely separate worker threads.

**Future chain hides sequential work that should be parallel.** Symptom. code
that intends to run several independent operations concurrently instead runs
them one after another, and total latency is the sum of every operation
rather than the maximum. Cause. writing `await opA(); await opB();`
sequentially by habit, rather than starting both operations first and then
awaiting them, for example `const [a, b] = await Promise.all([opA(), opB()])`.
This is purely an ordering mistake, not a bug in the pattern, but it is
extremely common because `await` syntax makes the sequential and concurrent
versions look almost identical on the page. Fix. start every independent
asynchronous operation before awaiting any of them, and reserve sequential
`await` for genuinely dependent steps.

**Memory leak from an unbounded chain of retained futures.** Symptom. memory
usage climbs slowly over the life of a long running process with many short
lived asynchronous operations. Cause. some future implementations retain a
reference to every registered continuation for the lifetime of the future,
and if futures are chained into ever longer sequences without ever being
dropped, for example accumulating retry futures in a loop that never
terminates the chain, the retained continuation graph grows without bound.
Fix. bound retry and chaining loops explicitly, and in languages with manual
resource management, verify that a completed future's continuation list is
actually released rather than assumed to be garbage collected immediately.

## 12. Trade-off matrix

| Force | Future/Promise | Callback registration | Reactor pattern | Blocking synchronous call |
|---|---|---|---|---|
| Composability of independent results | High, "all"/"race"/"allSettled" combinators built in | Low, manual counters and flags needed to combine two callbacks | Medium, event handlers compose via the dispatcher, not via language syntax | None, only one result exists at a time by construction |
| Readability with async/await sugar | High, reads close to sequential code | Low, nesting grows with each dependency | Low, handler logic is scattered across registered callbacks | High, but only because there is nothing asynchronous to read |
| Debuggability of execution order | Low, stack traces cross asynchronous boundaries | Medium, the callback call site is visible but ordering across callbacks is not | Low, dispatch order depends on the event source and the reactor's internal queue | High, the call stack is a single linear trace |
| Resource cost per operation | Medium, an allocation for state plus continuation links | Low, usually just a function reference stored | Low, the reactor owns a fixed set of registered handlers | Lowest, no extra object beyond the call itself |
| Error propagation clarity | High, symmetric with exceptions via `.catch`/`try`/`except` | Low, error and success often use separate callback parameters that must both be checked | Medium, depends entirely on how the dispatcher surfaces handler exceptions | Highest, an exception simply propagates up the stack |
| Suitability for a stream of many values over time | Poor, a future resolves once | Adequate, a callback can be invoked repeatedly | Good, this is the reactor's native shape | Not applicable |

## 13. Related and incompatible patterns

**Thread Pool.** A very common executor behind a future. `submit()` on a
thread pool typically returns exactly the future this pattern describes, so
the two patterns are usually seen together, with Thread Pool supplying the
"where the work runs" half and Future/Promise supplying the "how the caller
gets the result" half.

**Active Object.** Uses future/promise as its return mechanism by design. In
the Active Object pattern, a method call on the proxy returns immediately
with a future representing the eventual result of the method running on the
object's own scheduler thread, which is precisely the completion handle this
entry describes, applied specifically to method invocation rather than to an
arbitrary asynchronous operation.

**Producer-Consumer.** A related but distinct shape. Producer-Consumer moves
a stream of many items through a bounded buffer over time, while
Future/Promise resolves exactly once. A future/promise pair can be built on
top of a single slot channel that behaves like a one item Producer-Consumer
queue, which is effectively what the Rust code sample in this entry
demonstrates using `std::sync::mpsc`.

**Reactor and Proactor.** Alternative concurrency dispatch mechanisms that a
future's completion often rides on top of. A Proactor completing an
asynchronous I/O operation is frequently the exact moment a corresponding
promise is completed, so Proactor based I/O libraries commonly expose
futures as their public API surface, hiding the Proactor's completion port
machinery underneath.

**Reactive Streams and Observables.** The pattern this entry is most often
confused with, and the boundary is exact and worth stating plainly. a future
represents zero or one eventual value, an Observable or a Reactive Stream
represents zero to many values delivered over time. A future/promise cannot
correctly model a stream of button clicks or a stream of stock price ticks,
and reaching for one anyway forces an awkward "resolve with a list" or "one
future per event" workaround, both of which lose the point of the pattern.
This incompatibility is architectural rather than a matter of degree, which
is why it appears here rather than only in the non-applicability list.

**Async/Await.** Not a separate pattern so much as syntax sugar directly over
this one. Every `await` expression in every language that has it desugars to
registering a continuation on a future and suspending the enclosing function
until that continuation runs, so the two are inseparable in practice even
though they are conceptually distinct, the future/promise being the runtime
data structure and async/await being the compiler transform that consumes it.

## 14. Refactoring path in and out

**Introducing future/promise into callback based code.** Start by
identifying every place a function accepts a "success callback, error
callback" pair, or a single callback that receives an error/result tuple in
the Node.js style. For each one, wrap the callback registration inside a
`new Promise((resolve, reject) => { call the callback API, calling resolve or
reject from inside it })`, and change every caller of that function to
consume the returned promise instead of passing in its own callbacks
directly. This step, sometimes called "promisifying," can usually be done
function by function without touching the underlying asynchronous mechanism
at all, and languages such as Node.js ship a built in helper, `util.promisify`,
for the common case where the callback follows the error/result convention
([Node.js documentation, util.promisify](https://nodejs.org/api/util.html#utilpromisifyoriginal),
verified 2026-08-02). Once every leaf asynchronous call returns a promise,
replace manually nested `.then` chains with `async`/`await` where the
language supports it, converting the deepest nesting first since that is
where the readability gain is largest. Verify at each step that error paths
still propagate correctly, since a promisified function that forgets to call
`reject` on the callback's error branch silently converts a real failure into
a permanently pending promise, which is the exact failure mode named in
Failure modes and misuse.

**Removing future/promise when it no longer earns its place.** This
direction applies when profiling shows that an asynchronous chain wraps work
that has become, or always was, synchronous and CPU bound, or when a stream
of repeated events has been forced through a sequence of one shot futures.
Replace an `async function` that contains no `await` at all with a plain
synchronous function, since an async function with nothing to await gains
nothing from the pattern and only adds a microtask queue hop to every call.
Replace a chain of "resolve one future, immediately create the next" used to
model a sequence of events with an actual stream construct, an async
generator, an Observable, or a channel, whichever the target language
favours, verifying at each step that consumers that previously awaited a
single future are updated to iterate over the new stream instead, since the
two consumption styles are not source compatible.

## 15. Testing and verification

Testing code built on futures is generally easier than testing raw callback
code because the completion state, pending, fulfilled with a value, or
rejected with an error, is directly inspectable rather than implicit in
whether a callback function has been called yet. In JavaScript and
TypeScript test frameworks, an `async` test function that `await`s the code
under test lets assertions run in the same linear style as the production
code, and testing the rejection path is a matter of asserting that the
`await` throws, typically via a `try`/`catch` block or a matcher such as
Jest's `expect(promise).rejects.toThrow()`.

What becomes harder is testing timing and race behaviour, specifically
whether two futures actually ran concurrently rather than sequentially, and
whether a continuation ran on the expected thread or executor. Fake or
virtual timers, such as Sinon's fake timers in JavaScript or `asyncio`'s
event loop control in Python, are the standard technique for making timeout
dependent future tests deterministic instead of depending on real wall clock
delays, which otherwise makes tests both slow and flaky under load. For
thread pool backed futures such as Java's `CompletableFuture` or Python's
`concurrent.futures`, a common test double is an executor that runs
submitted tasks synchronously on the calling thread rather than on a real
pool, which removes timing nondeterminism from the test entirely while still
exercising the same completion and combinator logic. Testing the double
completion and forgotten completion failure modes named in Failure modes and
misuse directly is worthwhile precisely because those are the failures unit
tests otherwise miss. deliberately complete a promise twice in a test and
assert the implementation's actual behaviour, whether that is an exception or
a silent no op, so the team's understanding of that behaviour is verified
rather than assumed.

## 16. Observability signals

The signal that a future/promise heavy system is healthy is a stable, low
count of pending futures relative to throughput, and a completion latency
distribution that matches the expected latency of the underlying work. The
signal that it is unhealthy is a pending future count that climbs without
bound, which indicates promises are being created faster than they are being
completed, either because completion has stalled somewhere or because
consumers have stopped draining results.

Concretely worth measuring and logging.

- **Time to completion per future or task category**, tagged by the kind of
  operation the future represents, so a slowdown in one dependency, for
  example a downstream HTTP call, is distinguishable from a slowdown across
  the board.
- **Count of pending futures over time**, especially inside a thread pool or
  executor, since a monotonically increasing pending count under steady load
  is the single clearest signal of the forgotten promise failure mode named
  in Failure modes and misuse.
- **Unhandled rejection or exception count**, since a runtime that reports
  this event, as Node.js and browsers do for promises, gives a direct
  observability hook into the silently dropped error failure mode, and a
  nonzero rate of this event in production should be treated as an
  alertable condition, not background noise.
- **Executor or thread pool queue depth and active thread count**, when
  futures are backed by a pool, because a saturated pool manifests as futures
  that complete correctly but with steadily increasing latency, which a time
  to completion metric alone will show as a trend without explaining the
  cause.
- **Trace context propagation across the await boundary**, because
  distributed tracing systems must explicitly carry a trace or span
  identifier across an asynchronous continuation, or the resulting trace
  will show a gap or a disconnected span exactly at the point execution moved
  from the producing thread to the consuming continuation, which is the
  practical form the shallow stack trace consequence named in section 10
  takes in a production observability system.

## 17. Security and privacy implications

Future/promise itself does not open a distinct attack surface the way, for
example, a deserialization pattern does, but it has two implications worth
naming rather than leaving silent.

First, a captured exception passed through a rejected future or promise can
carry sensitive data, connection strings, stack frames referencing internal
file paths, or partial request payloads, and because the rejection path is
often logged generically at a top level error handler far from where the
exception originated, it is easy for that handler to log the exception's
full message and stack without the context needed to redact sensitive
fields, a risk that is not unique to this pattern but is made easier by how
far the rejection can travel from its origin before being handled. Second, an
unbounded number of pending promises created in response to untrusted input,
for example creating one future per incoming request without a concurrency
limit, is a resource exhaustion vector, since each pending future retains
memory for its state and for any continuations registered on it until it
either completes or is garbage collected, and an attacker who can trigger
operations that never complete, exploiting the forgotten promise failure mode
from the outside, can grow that retained memory without bound. Bounding
concurrent asynchronous operations with a semaphore or a fixed size executor,
and applying timeouts on every externally triggered future so that it
eventually completes with a failure rather than staying pending forever,
addresses this directly.

## 18. References

1. Wikipedia, "Futures and promises," section History. https://en.wikipedia.org/wiki/Futures_and_promises, verified 2026-08-02.
2. MDN Web Docs, "Promise." https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise, verified 2026-08-02.
3. MDN Web Docs, "Using promises." https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Using_promises, verified 2026-08-02.
4. Oracle, Java SE 8 Javadoc, "java.util.concurrent package summary." https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/package-summary.html, verified 2026-08-02.
5. Oracle, Java SE 21 Javadoc, "CompletableFuture." https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/CompletableFuture.html, verified 2026-08-02.
6. Microsoft Learn, "Task-based asynchronous programming (TAP)." https://learn.microsoft.com/en-us/dotnet/standard/asynchronous-programming-patterns/task-based-asynchronous-pattern-tap, verified 2026-08-02.
7. Microsoft Learn, "Asynchronous programming with async and await." https://learn.microsoft.com/en-us/dotnet/csharp/asynchronous-programming/, verified 2026-08-02.
8. cppreference.com, "std::future." https://en.cppreference.com/w/cpp/thread/future, verified 2026-08-02.
9. cppreference.com, "std::promise<T>::set_value." https://en.cppreference.com/w/cpp/thread/promise/set_value, verified 2026-08-02.
10. Python Software Foundation, "concurrent.futures, Launching parallel tasks." https://docs.python.org/3/library/concurrent.futures.html, verified 2026-08-02.
11. Promises/A+ Organization, "Promises/A+ specification," section 2.2. https://promisesaplus.com/, verified 2026-08-02.
12. Google, Guava wiki, "ListenableFutureExplained." https://github.com/google/guava/wiki/ListenableFutureExplained, verified 2026-08-02.
13. Twitter, Finagle User's Guide, "Services and Filters." https://twitter.github.io/finagle/guide/ServicesAndFilters.html, verified 2026-08-02.
14. The Rust Programming Language project, "Asynchronous Programming in Rust," chapter 2, "The Future Trait." https://rust-lang.github.io/async-book/02_execution/02_future.html, verified 2026-08-02.
15. Node.js, "Warning: Unhandled promise rejections," process documentation. https://nodejs.org/api/process.html#event-unhandledrejection, verified 2026-08-02.
16. Node.js, "util.promisify(original)." https://nodejs.org/api/util.html#utilpromisifyoriginal, verified 2026-08-02.
17. The Go Authors, "Effective Go," section "Concurrency." https://go.dev/doc/effective_go#concurrency, verified 2026-08-02.

## Code examples

TypeScript, Python, Java, and Rust are shown below. TypeScript and JavaScript
have a native `Promise` built directly into the language, making the pattern
its most idiomatic form there. Python is shown with both `asyncio.Future` and
`concurrent.futures.Future`, since the two are genuinely different
implementations of the same pattern for different concurrency models. Java is
shown with `CompletableFuture`, the modern successor to the original Java 5
`Future` interface. Rust is shown as a minimal, dependency free split
promise/future pair built on `std::sync::mpsc`, rather than the full
`std::future::Future` trait with `async`/`await`, because the trait based
version requires an external executor crate such as Tokio to run, and the
point of this sample is to show the pattern's classic split shape running
with nothing beyond the standard library. Kotlin's `Deferred` and Swift's
`async`/`await` are close cousins of the Java and TypeScript samples
respectively and are omitted here rather than duplicated, since neither
`kotlinc` nor a Swift toolchain wired for this repository's check scripts was
confirmed available for this entry.

All four samples below were compiled or run directly and their output is
shown as verification, not asserted from reading the code.

```typescript
interface Deferred<T> {
  promise: Promise<T>;
  resolve: (value: T) => void;
  reject: (reason: unknown) => void;
}

function deferred<T>(): Deferred<T> {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

async function fetchUserName(userId: number): Promise<string> {
  if (userId <= 0) {
    throw new Error(`invalid user id ${userId}`);
  }
  await new Promise((r) => setTimeout(r, 10));
  return `user-${userId}`;
}

async function fetchOrderTotal(orderId: number): Promise<number> {
  await new Promise((r) => setTimeout(r, 5));
  return orderId * 10;
}

async function buildReceipt(userId: number, orderId: number): Promise<string> {
  const [name, total] = await Promise.all([
    fetchUserName(userId),
    fetchOrderTotal(orderId),
  ]);
  return `${name} owes ${total}`;
}

async function main(): Promise<void> {
  const receipt = await buildReceipt(7, 3);
  console.log(receipt);

  const d = deferred<number>();
  setTimeout(() => d.resolve(42), 1);
  console.log(await d.promise);

  try {
    await fetchUserName(-1);
  } catch (err) {
    console.log("caught:", (err as Error).message);
  }
}

main();
```

Compiled with `tsc --strict --target es2020 --module commonjs` and run with
`node`. Output.

```
user-7 owes 30
42
caught: invalid user id -1
```

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor, Future


def fetch_user_name_blocking(user_id: int) -> str:
    if user_id <= 0:
        raise ValueError(f"invalid user id {user_id}")
    return f"user-{user_id}"


def thread_pool_demo() -> str:
    pool = ThreadPoolExecutor(max_workers=2)
    future: Future = pool.submit(fetch_user_name_blocking, 7)
    result = future.result(timeout=1)
    pool.shutdown(wait=True)
    return result


async def fetch_order_total(order_id: int) -> int:
    await asyncio.sleep(0.01)
    return order_id * 10


async def fetch_user_name(user_id: int) -> str:
    await asyncio.sleep(0.005)
    return fetch_user_name_blocking(user_id)


async def build_receipt(user_id: int, order_id: int) -> str:
    name, total = await asyncio.gather(
        fetch_user_name(user_id), fetch_order_total(order_id)
    )
    return f"{name} owes {total}"


async def manual_future_demo() -> int:
    loop = asyncio.get_running_loop()
    fut: asyncio.Future = loop.create_future()

    def resolve_later() -> None:
        fut.set_result(42)

    loop.call_later(0.001, resolve_later)
    return await fut


async def main() -> None:
    print(await build_receipt(7, 3))
    print(thread_pool_demo())
    print(await manual_future_demo())
    try:
        await fetch_user_name(-1)
    except ValueError as exc:
        print("caught:", exc)


if __name__ == "__main__":
    asyncio.run(main())
```

Run with `python3`. Output.

```
user-7 owes 30
user-7
42
caught: invalid user id -1
```

```java
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;

public final class PromiseDemo {

    static String fetchUserNameBlocking(int userId) {
        if (userId <= 0) {
            throw new IllegalArgumentException("invalid user id " + userId);
        }
        return "user-" + userId;
    }

    static CompletableFuture<String> fetchUserName(int userId) {
        return CompletableFuture.supplyAsync(() -> fetchUserNameBlocking(userId));
    }

    static CompletableFuture<Integer> fetchOrderTotal(int orderId) {
        return CompletableFuture.supplyAsync(() -> orderId * 10);
    }

    static CompletableFuture<String> buildReceipt(int userId, int orderId) {
        CompletableFuture<String> name = fetchUserName(userId);
        CompletableFuture<Integer> total = fetchOrderTotal(orderId);
        return name.thenCombine(total, (n, t) -> n + " owes " + t);
    }

    public static void main(String[] args) throws ExecutionException, InterruptedException {
        System.out.println(buildReceipt(7, 3).get());

        CompletableFuture<Integer> deferred = new CompletableFuture<>();
        new Thread(() -> deferred.complete(42)).start();
        System.out.println(deferred.get());

        CompletableFuture<String> failing = fetchUserName(-1);
        failing.handle((value, error) -> {
            if (error != null) {
                System.out.println("caught: " + error.getCause().getMessage());
            }
            return value;
        }).join();
    }
}
```

Compiled and run with a JDK 26 toolchain, `javac` then `java`. Output.

```
user-7 owes 30
42
caught: invalid user id -1
```

```rust
use std::sync::mpsc;
use std::thread;

struct Promise<T> {
    sender: mpsc::Sender<T>,
}

struct Future<T> {
    receiver: mpsc::Receiver<T>,
}

fn make_pair<T>() -> (Promise<T>, Future<T>) {
    let (sender, receiver) = mpsc::channel();
    (Promise { sender }, Future { receiver })
}

impl<T> Promise<T> {
    fn fulfill(self, value: T) {
        let _ = self.sender.send(value);
    }
}

impl<T> Future<T> {
    fn get(self) -> T {
        self.receiver.recv().expect("promise dropped without fulfillment")
    }
}

fn fetch_user_name(user_id: i64) -> Result<String, String> {
    if user_id <= 0 {
        return Err(format!("invalid user id {}", user_id));
    }
    Ok(format!("user-{}", user_id))
}

fn fetch_order_total(order_id: i64) -> i64 {
    order_id * 10
}

fn build_receipt(user_id: i64, order_id: i64) -> Result<String, String> {
    let (name_promise, name_future) = make_pair::<Result<String, String>>();
    let (total_promise, total_future) = make_pair::<i64>();

    let name_handle = thread::spawn(move || {
        name_promise.fulfill(fetch_user_name(user_id));
    });
    let total_handle = thread::spawn(move || {
        total_promise.fulfill(fetch_order_total(order_id));
    });

    let name = name_future.get();
    let total = total_future.get();
    name_handle.join().unwrap();
    total_handle.join().unwrap();

    let name = name?;
    Ok(format!("{} owes {}", name, total))
}

fn main() {
    match build_receipt(7, 3) {
        Ok(receipt) => println!("{}", receipt),
        Err(e) => println!("error: {}", e),
    }

    let (promise, future) = make_pair::<i32>();
    thread::spawn(move || {
        promise.fulfill(42);
    });
    println!("{}", future.get());

    match fetch_user_name(-1) {
        Ok(_) => println!("unexpected"),
        Err(e) => println!("caught: {}", e),
    }
}
```

Compiled with `rustc --edition 2021` and run directly. Output.

```
user-7 owes 30
42
caught: invalid user id -1
```
