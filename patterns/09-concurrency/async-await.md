---
name: Async Await
slug: async-await
family: 09-concurrency
category: Concurrency
aliases: [Coroutines with async/await, Async Functions, Task-Based Asynchronous Pattern]
first_described: "Selivanov 2015 (Python), Hejlsberg and Torgersen 2010 (C#), TC39 2017 (ECMAScript)"
maturity: canonical
related: [future-promise, reactor, proactor, half-sync-half-async, thread-pool, producer-consumer]
incompatible_with: []
verified: 2026-08-02
---

# Async Await

## 1. Name, aliases, and lineage

The canonical name in every mainstream language that ships it is async/await,
written as a pair because the two keywords only make sense together. `async`
marks a function as one that can suspend, `await` marks the point inside that
function where suspension happens. Some ecosystems use different keywords for
the same idea. Python calls the declaration `async def` and the suspension
point `await`. Kotlin calls the declaration `suspend fun` and does not require
an explicit keyword at the call site, because suspension is inferred from the
callee's signature. C# calls the declaration `async Task` or `async void` and
the operator `await`. JavaScript, Rust, Swift, and Dart all use the literal
words `async` and `await`.

The pattern is not a single invention with one paper behind it. It is
convergent design that several language teams arrived at independently after
watching the same failure mode play out in callback-heavy and promise-chained
code. The clearest documented origin is F# `async` workflows, described by Don
Syme's team at Microsoft Research starting around 2007, which used
computation expressions to let a function look sequential while compiling to a
continuation-passing state machine underneath. C# picked up the same idea for
its 5.0 release. Anders Hejlsberg and Mads Torgersen presented the design at
PDC 2010, and the feature shipped as the Task-based Asynchronous Pattern (TAP)
built on `async` and `await` keywords layered over `System.Threading.Tasks.Task`
([Microsoft Learn, Asynchronous programming in C#](https://learn.microsoft.com/en-us/dotnet/csharp/asynchronous-programming/),
verified 2026-08-02, which documents the TAP model and its supersession of the
older `IAsyncResult` and event-based asynchronous patterns).

Python's version arrived through PEP 492, written by Yury Selivanov, created
9 April 2015, accepted 5 May 2015, and shipped in Python 3.5. The PEP
introduced `async def`, `await`, `async with`, and `async for` as first-class
syntax distinct from the generator-based coroutines Python had been using since
PEP 342 and PEP 380, specifically to stop the confusion of a generator that is
sometimes an iterator and sometimes a coroutine depending on how it is driven
([PEP 492, Coroutines with async and await syntax](https://peps.python.org/pep-0492/),
verified 2026-08-02, author Yury Selivanov, target version Python 3.5, status
Final). JavaScript's proposal followed the same shape a few years later. The
TC39 proposal repository states plainly that async/await "represents a
dramatically improved language-level model for writing asynchronous code" and
that the design builds directly on both Promises and Generators as its foundation
([tc39/proposal-async-await](https://github.com/tc39/proposal-async-await),
verified 2026-08-02). The feature reached ECMAScript 2017 and lives today in
the async function definitions clause of the living ECMA-262 specification
maintained by TC39, the standard every conforming JavaScript engine must
implement ([ECMA-262, the ECMAScript Language Specification](https://tc39.es/ecma262/),
verified 2026-08-02 as the canonical governing document for this feature; the
async function grammar sits in the function and class definitions chapter).

Rust's version is the odd one out in this lineage because Rust designed
`async`/`await` as sugar over an explicit, allocation-free `Future` trait
rather than over a runtime-managed task object, and stabilized it comparatively
late, in Rust 1.39.0, released 7 November 2019 ([the Rust Blog, "Async-await on
stable Rust!"](https://blog.rust-lang.org/2019/11/07/Async-await-stable/),
verified 2026-08-02, which announces the stabilization date and version).
Swift's version, proposed as SE-0296 and authored by John McCall and Doug
Gregor with Ben Cohen as review manager, shipped in Swift 5.5 and explicitly
frames async functions as "ordinary functions" that gain "the special power to
give up their thread," a description chosen to distinguish the model from
green threads or fibers ([swift-evolution SE-0296, Async/await](https://github.com/apple/swift-evolution/blob/main/proposals/0296-async-await.md),
verified 2026-08-02).

Because the pattern recurs independently across ecosystems, this entry treats
async/await as one pattern with several concrete dialects rather than as a
single canonical implementation with ports. The forces, structure, and
failure modes described below are shared across every dialect. The differences
that matter for a working engineer are called out explicitly in the
implementation variants section.

## 2. Problem and context

A function that needs a result from somewhere slow, a network call, a disk
read, a timer, a lock, has two honest choices before async/await exists in a
language. It can block the calling thread until the slow thing finishes, which
is simple to write and simple to reason about but wastes a thread for the
entire wait, or it can register a callback and return immediately, which frees
the thread but scatters the logic of "what happens next" across a function
that is no longer readable top to bottom.

The callback style is where the real pain shows up. A sequence of three
dependent asynchronous steps, fetch a user, then fetch their orders, then
compute a total, turns into three nested callbacks, each one responsible for
error handling, each one capturing the outer scope's variables by closure,
each one indented one level deeper than the last. Developers who lived through
Node.js before promises named this shape "callback hell" or "the pyramid of
doom." The named GoF Command and Observer patterns describe pieces of this
world (a callback is a reified continuation, an event emitter is an observer),
but neither pattern addresses the readability collapse that happens when four
or five of these compose in sequence with error propagation threaded through
every layer.

Promises, `Future` objects, and `Task` objects (the subject of the sibling
Future/Promise entry in this repository) improve the situation by giving the
pending result a first-class value that can be returned, stored, and chained
with `.then()`, but chaining still reads back to front relative to how a
person thinks about the steps, and error handling through a promise chain
requires a `.catch()` at the end that has to reason about which of several
prior steps might have thrown. The context that makes async/await necessary is
exactly this gap. A team wants code that reads as a sequential list of steps,
because that is how a person plans a sequence of dependent I/O operations, but
they also need the actual execution to be non-blocking, because a thread
sitting idle on a network call is a thread that cannot serve another request.
Async/await closes that gap by asking the compiler, rather than the
programmer, to turn sequential-looking code into the state machine or
continuation chain that a promise-chained or callback-based version would have
required by hand.

The pattern applies specifically in single-threaded or thread-pooled runtimes
where cooperative suspension is available, an event loop (JavaScript, Python
asyncio), a work-stealing executor (Rust's Tokio, Kotlin coroutines), or a
thread-pool-backed task scheduler (C# `Task`, Swift's cooperative thread pool).
It does not apply, and actively misleads, in a context where the underlying
work is CPU-bound rather than I/O-bound, because suspending at an `await` only
helps when there is genuinely nothing for the current logical task to do while
it waits.

## 3. Forces

The strongest force async/await resolves is **readability versus non-blocking
execution**. Written as sequential code, a multi-step asynchronous operation
reads the way a person plans it, in order, with `try`/`catch` (or the
language's native error mechanism) wrapping the parts that can fail, exactly
as if the calls were synchronous. Underneath, none of that sequential
appearance is true. The runtime is free to run other work while any given
`await` is suspended. This entry's engineering judgement is that this force
outweighs every other design consideration in the pattern's history. Every
language team that added the feature did so after their community had already
built promise-based or Future-based idioms and found them functionally
sufficient but ergonomically expensive at scale.

A second force is **stack trace and debugging fidelity**. Callback code loses
the calling context the moment control returns to the event loop; a stack
trace inside a deeply nested callback often shows only the innermost frame and
the event loop's dispatch frame, with no path back to the code that scheduled
the work. Async/await state machines preserve enough compiler-generated
bookkeeping that modern debuggers and stack unwinders can reconstruct a
logical call stack across suspension points, which was explicitly one of the
design goals cited in the C# TAP documentation's comparison against
`ContinueWith` chains ([Microsoft Learn, Asynchronous programming in C#](https://learn.microsoft.com/en-us/dotnet/csharp/asynchronous-programming/),
verified 2026-08-02, "the compiler generates optimized state machine code" and
"the call stack and debugger experience is much better with async/await").

A third force, and the one that most distinguishes the dialects from each
other, is **cost of suspension**. In callback-based JavaScript, in
Promise-chained code, and in thread-pool-backed C#, suspension is comparatively
cheap because the runtime already owns a scheduler and a task representation.
In Rust, suspension had to be engineered to cost nothing at rest, because Rust
targets embedded and systems contexts where allocating a heap object per
pending operation is unacceptable. The `Future` trait Rust settled on is
poll-based rather than push-based specifically so that a suspended future
costs only the size of its state, stored inline, with no separate heap
allocation and no callback registration until something actually polls it
([the Rust Async Book, chapter on the Future trait](https://rust-lang.github.io/async-book/02_execution/02_future.html),
verified 2026-08-02, defining `trait Future { type Output; fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output>; }`).
This is a real trade-off, not free lunch. Rust's zero-cost suspension buys
efficiency at the price of Rust futures doing nothing at all unless something
polls them, which is the single most common source of confusion for engineers
new to the language, covered under failure modes below.

A fourth force is **concurrency versus parallelism**. Async/await, in every
dialect, is a concurrency primitive, not a parallelism primitive. Awaiting two
independent operations one after another is still sequential unless the caller
explicitly starts both before awaiting either, using `Promise.all`,
`asyncio.gather`, `Task.WhenAll`, `tokio::join!`, or a task group. This entry's
engineering judgement is that this is the single most common source of
performance bugs in async/await code, because the sequential-looking syntax
actively hides the difference between "these two things happen one after the
other" and "these two things happen at the same time," which is precisely the
opposite of what callback code made visible through its explicit nesting.

A fifth force is **error propagation**. The pattern deliberately reuses the
language's existing exception or error-handling construct (`try`/`catch` in
JavaScript, C#, Swift; Python's `try`/`except`; Rust's `?` operator over
`Result`) so that an error raised deep inside an awaited chain propagates the
same way a synchronous error would. This is a genuine improvement over manual
error-first callbacks and over promise chains where a missed `.catch()` at any
link silently swallows a rejection, but it also means async/await inherits
whatever weaknesses the host language's error model already has, most clearly
that a language without checked exceptions gives the reader no static signal
that an `await`ed call can fail at all.

## 4. Applicability and non-applicability

Reach for async/await when the work being coordinated is I/O-bound, meaning
the actual computation is small and the time is spent mostly waiting, network
requests, disk access, database queries, timers, or another process's
response, and when more than one such operation needs to be sequenced,
composed, or run concurrently inside a single logical unit of work such as a
request handler, a UI event handler, or a background job. It is also the right
tool when the alternative under consideration is a callback pyramid or a
deeply chained `.then()`/`.map()` sequence that has already become hard to
follow, and when the host language and its ecosystem give the pattern
first-class support, meaning a real runtime (an event loop, an executor, a
thread pool) exists to actually schedule the suspended work.

Do not reach for async/await in the following situations.

- **CPU-bound work with no I/O.** Marking a function `async` and `await`ing
  nothing but pure computation buys nothing. In a single-threaded event loop
  (JavaScript, Python's default asyncio loop) it can actively hurt, because a
  long CPU-bound `await`-free stretch inside an async function still blocks
  the event loop exactly as a synchronous call would, since there is no
  suspension point for the scheduler to interleave other work at. The correct
  tool is a worker thread, a process pool, or a dedicated CPU-bound executor,
  not async/await.
- **A single, unconditional, immediately-needed value with no concurrency
  opportunity.** If a function's entire body is one blocking call whose
  result is needed before anything else can happen, and nothing else in the
  program could usefully run during that wait, a plain synchronous call is
  simpler to read, simpler to test, and produces a simpler stack trace. Async
  infrastructure that never actually creates concurrency is pure overhead,
  what the Python core developers have described informally as "async for
  async's sake."
- **Tight, hot inner loops that need to run to completion without
  interruption.** A suspension point is a place where the scheduler can hand
  control to something else, and in some runtimes (Rust's cooperative
  executors, JavaScript's event loop) a poorly placed `await` inside a hot
  loop can introduce scheduling jitter that a synchronous loop would not have.
- **Contexts where the language or runtime has no real async support and the
  feature would only be simulated with threads underneath.** Faking
  async/await over a blocking implementation (an early, unofficial polyfill,
  or a library that spins up a thread per `await`) reintroduces the exact
  thread-per-operation cost the pattern exists to avoid, while presenting the
  same misleadingly cheap-looking syntax.
- **Code where deterministic, single-threaded execution order is a
  correctness requirement and any interleaving is unacceptable**, such as
  certain simulation kernels or protocol state machines that were verified
  under an assumption of strict sequential execution. Introducing `await`
  points, even cooperative ones, changes the set of states other code can
  observe mid-operation, and a system whose correctness proof assumed no such
  interleaving needs that proof redone, not a syntax change alone.
- **Fire-and-forget work where nobody will ever await the result and the
  failure mode of a silently dropped exception is unacceptable.** An
  `async` function called without `await` and without attaching an error
  handler produces, in nearly every dialect, a task whose failure vanishes
  unless the runtime has an unhandled-rejection or unobserved-task-exception
  hook wired up. This is covered in more detail under failure modes.

## 5. Structure

Async/await is a language-level transformation, not an object-oriented pattern
in the GoF sense, so its "participants" are the elements the compiler and
runtime cooperate to produce rather than classes a designer writes by hand.

**The async function** is the unit of suspendable work. Marking a function
`async` (or `async def`, or giving it a `suspend` modifier) changes its return
type at the type-system level, wrapping whatever the function's body returns
in a container the caller must unwrap, a `Promise<T>` in JavaScript, a
`Task<T>` in C#, a coroutine object in Python, an `impl Future<Output = T>` in
Rust, or an implicit async return in Swift and Kotlin. Calling an async
function does not run its body to completion. It produces (or, in Rust's
case, merely constructs, inert until polled) the wrapped future-like value and
returns control to the caller immediately.

**The `await` expression** marks a point inside an async function's body
where execution can suspend. When the awaited expression's underlying
operation is not yet complete, control returns to whatever scheduled the
current async function, and the function's local state, including everything
on its conceptual stack frame, is preserved so execution can resume from that
exact point later. This is the piece that requires either a heap-allocated
continuation (most garbage-collected languages) or a compiler-generated state
machine struct (Rust, and C# under the hood) to implement, because a normal
stack frame cannot be paused and resumed across an arbitrary amount of other
work happening in between.

**The scheduler or runtime** is the component that actually decides when a
suspended async function resumes. This is an event loop in JavaScript and in
Python's default asyncio implementation, a work-stealing multi-threaded
executor in Rust's Tokio or in Kotlin's default coroutine dispatcher, and a
thread-pool-backed task scheduler in the .NET runtime for C#. The scheduler is
never a syntactic part of async/await itself, which is why the same
`async`/`await` keywords in JavaScript and in Rust produce meaningfully
different runtime behavior, single-threaded cooperative multitasking in
JavaScript versus multi-threaded work-stealing that can run in Tokio.

**The awaitable itself**, the `Promise`, `Task`, coroutine, or `Future` that
`await` operates on, is the state-holding object that represents "this
operation, which may not have finished yet." It carries three possible states,
conventionally named pending, fulfilled or resolved, and rejected or failed,
and it is the object the sibling Future/Promise entry in this repository
describes in depth as its own pattern. Async/await is best understood as
syntax layered on top of the future/promise pattern. The future is the noun,
async/await is the sentence structure that makes working with the noun read
naturally.

**The caller's continuation** is the implicit remainder of the calling
function's work after an `await` returns. In callback-based code this is the
callback itself, written by hand. In async/await, the compiler generates it,
which is the entire value proposition of the pattern, it removes the need to
manually reify "what happens next" as a first-class closure.

## 6. ASCII structure diagram

```
+----------------------------------------------------------+
|                     Caller (sync code)                    |
|                                                            |
|   result = await someAsyncFunction(args)                  |
+---------------------+--------------------------------------+
                        | calls
                        v
+----------------------------------------------------------+
|                    Async Function                         |
|  (compiled to a state machine or heap continuation)        |
|                                                            |
|   state 0: run until first await ----+                    |
|   state 1: resume after await A, run until next await -+  |
|   state 2: resume after await B, run to return          |  |
|                                                            |
|   returns immediately with an Awaitable, NOT the result    |
+---------------------+--------------------------------------+
                        | produces
                        v
+----------------------------------------------------------+
|                Awaitable (Promise / Task / Future)         |
|                                                            |
|   state: Pending | Fulfilled(value) | Rejected(error)      |
|   registers continuation with the scheduler on suspend     |
+---------------------+--------------------------------------+
                        | scheduled by
                        v
+----------------------------------------------------------+
|             Scheduler / Runtime (event loop or             |
|                  executor / thread pool)                   |
|                                                            |
|  - polls or is notified when underlying I/O completes      |
|  - resumes the async function's state machine at the       |
|    saved suspension point                                  |
|  - may interleave other pending async functions while      |
|    the current one is suspended                            |
+----------------------------------------------------------+
```

## 7. Dynamics

The runtime sequence below traces a caller awaiting two independent async
operations, first sequentially, then concurrently, to make the concurrency
force from dimension 3 visible as a timeline rather than an abstract claim.

```
Sequential awaiting (each await blocks the next line from starting):

  caller           fnA()              fnB()            scheduler
    |                |                   |                  |
    | await fnA() -->|                   |                  |
    |                | suspend @ I/O --------------------->  | (register)
    |                |                   |                  | ... waiting ...
    |                | <---------------------------------- resume (A done)
    | <-- resultA ---|                   |                  |
    | await fnB() ------------------------->|               |
    |                |                   | suspend @ I/O -->| (register)
    |                |                   |                  | ... waiting ...
    |                |                   | <--------------- resume (B done)
    | <-- resultB ------------------------|                  |
    |                |                   |                  |
    total wall time ~= time(A) + time(B)


Concurrent awaiting (both started before either is awaited):

  caller           fnA()              fnB()            scheduler
    |                |                   |                  |
    | call fnA() --->| suspend @ I/O --------------------->  | (register A)
    | <-- taskA -----|                   |                  |
    | call fnB() -------------------------->| suspend @ I/O ->| (register B)
    | <-- taskB ----------------------------|                |
    | await taskA, taskB (e.g. Promise.all / gather / join!) |
    |                                                        | interleaves
    |                |                   |                  | both waits
    | <---------------------------------------------------- both resume
    | <-- resultA, resultB --------------------------------- |
    |                |                   |                  |
    total wall time ~= max(time(A), time(B))
```

The important detail the diagram makes explicit is that suspension is
observable from the outside as a return to the caller, not as a blocked
thread. Whatever called the async function gets its own control back the
instant an `await` inside that function first suspends, which is what lets
the scheduler interleave unrelated work, another HTTP request in a web
server, another UI event in a client application, during the wait.

## 8. Implementation variants

**Callback-desugaring (JavaScript, and any language whose async/await sits on
top of an existing promise or future type).** The compiler transforms an
`async function` into a state machine that, at each `await`, calls `.then()`
on the awaited promise and registers the remainder of the function body as the
`.then()` callback, then returns control. This is why JavaScript's async/await
is frequently and correctly described as "syntax sugar over promises," it
changes nothing about the underlying execution model, only how the source
reads.

**State-machine desugaring (C#, Rust).** The compiler generates a struct that
holds every local variable that needs to survive across an `await` point, plus
an integer or enum tag recording which suspension point execution is
currently at, and a `MoveNext()` (C#) or `poll()` (Rust) method that a
`switch`/`match` on that tag jumps into to resume execution. C# hides this
entirely from the programmer; Rust exposes the resulting type as
`impl Future<Output = T>` and requires an executor to actually drive it,
because a bare Rust future does nothing until polled, described directly in
the async book as the model where the executor "repeatedly poll[s] each
future in a queue, requiring a lot of unnecessary calls to poll" absent a
wake mechanism, which is exactly what `Waker` exists to avoid
([Rust Async Book, Future trait chapter](https://rust-lang.github.io/async-book/02_execution/02_future.html),
verified 2026-08-02).

**Generator-based coroutines (Python before PEP 492, still visible as the
underlying mechanism today).** Python's `async def` functions are, at the
bytecode level, a specialized flavor of generator, which is why the language
already had the suspension primitive it needed, `yield`, before it added
dedicated syntax. PEP 492 exists specifically to give coroutines their own
first-class type distinct from a generator being driven manually, closing the
ambiguity where the same object could be either ([PEP 492](https://peps.python.org/pep-0492/),
verified 2026-08-02).

**Structured concurrency task groups (Swift, Kotlin, and Python's
`asyncio.TaskGroup` since 3.11).** Rather than leaving concurrent awaiting to
ad hoc combinators, these dialects introduce a scoped construct,
`withThrowingTaskGroup` in Swift, `coroutineScope` in Kotlin, `TaskGroup` in
Python, that guarantees every child task started inside the scope either
completes or is cancelled before the scope exits, and that a failure in one
child cancels its siblings. This closes the "detached, unsupervised task"
failure mode described in dimension 11 by construction rather than by
convention. Swift's own proposal frames this directly as solving the problem
that unstructured `Task { ... }` blocks have no owner and no guaranteed
lifetime relationship to the code that spawned them.

**Cooperative single-threaded scheduling (JavaScript's event loop, Python's
default asyncio event loop).** Exactly one logical task runs at a time; an
`await` is the only point where the scheduler may switch to another task.
This makes shared mutable state between concurrently-running async functions
far safer than shared state between OS threads, because there is no
preemption mid-expression, but it also means a single `await`-free CPU-bound
stretch, however long, starves every other pending task in the process.

**Work-stealing multi-threaded scheduling (Rust's Tokio, most Kotlin
coroutine dispatchers, .NET's default `ThreadPool`-backed `Task` scheduler).**
Multiple OS threads pull ready work from a shared queue, so two async
functions genuinely can execute simultaneously on different cores between
suspension points. This reintroduces real data races on shared mutable state
across tasks, which is why Rust's `Send`/`Sync` traits and, in practice,
Kotlin's and C#'s conventions around `Mutex`/`lock` still matter inside
async/await code, the pattern removes the ergonomic pain of asynchrony, it
does not remove the need for synchronization when tasks genuinely share
mutable state across threads.

## 9. Known production uses

Node.js itself is the reference implementation of a production runtime built
around this exact suspension model, its documented event loop runs distinct
phases, timers, pending callbacks, poll, check, close callbacks, and treats
`process.nextTick` and Promise microtasks as running between phases rather
than as a phase of their own, which is precisely the scheduling substrate
every `await` in a Node.js program suspends onto and resumes from
([Node.js official guide, "The Node.js Event Loop, Timers, and process.nextTick()"](https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick),
verified 2026-08-02, documenting the six-phase loop and microtask ordering).

FastAPI, the Python web framework, is built directly around `async def` path
operation functions as its primary request-handling model, with its own
documentation explaining that request handlers declared `async def` run
directly on the event loop while ordinary `def` handlers are dispatched to an
external thread pool so a blocking call cannot stall the server, and
attributing the framework's throughput characteristics to "the same level of
performance you get with... NodeJS" and Go precisely because of this async
dispatch model ([FastAPI documentation, "Concurrency and async / await"](https://fastapi.tiangolo.com/async/),
verified 2026-08-02).

Tokio, the most widely used asynchronous runtime for Rust, exists specifically
to execute code written with Rust's `async`/`await` syntax at scale; its own
tutorial states plainly that it is "built on top of the async/await language
feature" and describes itself as the runtime whose usage "surpass[es] all
other runtimes combined" in the Rust ecosystem, which is the closest a
maintainer-authored source gets to a market-share claim without naming
individual adopters ([Tokio tutorial, "Overview"](https://tokio.rs/tokio/tutorial),
verified 2026-08-02).

ASP.NET Core, Microsoft's production web framework for .NET, adopts the
Task-based Asynchronous Pattern as its documented default for request
handling and I/O, the same TAP model Microsoft's own asynchronous programming
guide walks through end to end with the `async`/`await` keyword pair layered
over `System.Threading.Tasks.Task`, the identical mechanism this entry has
been describing throughout ([Microsoft Learn, "Asynchronous programming in C#"](https://learn.microsoft.com/en-us/dotnet/csharp/asynchronous-programming/),
verified 2026-08-02, describing TAP as the model that "provides a layer of
abstraction over typical asynchronous coding" for the whole of modern C#,
including ASP.NET Core request pipelines built on top of it).

Apple's own frameworks, most visibly `URLSession`, ship first-class
`async`/`await` overloads (`URLSession.shared.data(from:)` returning
`(Data, URLResponse)` via `await` rather than a completion handler) as the
recommended way to perform network requests on Apple platforms since Swift
5.5, which is the language-and-framework-level production adoption the
SE-0296 proposal itself was written to enable ([swift-evolution SE-0296](https://github.com/apple/swift-evolution/blob/main/proposals/0296-async-await.md),
verified 2026-08-02, describing async functions as the intended replacement
for completion-handler-based system APIs).

## 10. Consequences

**Positive.**

- Multi-step asynchronous logic reads top to bottom in the same order it
  executes conceptually, which is a direct, observed readability improvement
  over the equivalent callback or bare-promise-chain version, and is the
  reason every dialect's own design documentation leads with a
  before-and-after readability comparison.
- Error handling composes with the language's native mechanism
  (`try`/`catch`, `?`, `try`/`except`), so a single handler placed around a
  sequence of `await`s catches a failure from any of them, closing the
  "forgot a `.catch()` somewhere in the chain" failure mode that plain
  promise chains are prone to.
- Debuggers and stack unwinders can present a logical call stack that spans
  suspension points, restoring debugging ergonomics that were largely lost in
  deeply nested callback code.
- Because the awaited value is still a first-class `Promise`/`Task`/`Future`
  underneath, the pattern composes cleanly with every combinator that already
  exists for that underlying type (`Promise.all`, `Task.WhenAll`,
  `asyncio.gather`, `tokio::join!`), so concurrency is available on demand
  without abandoning the sequential-reading default.
- In event-loop-based runtimes, suspending at `await` frees the thread to do
  other work, which is the entire throughput argument for using it over
  blocking I/O in a server handling many concurrent connections.

**Negative.**

- Sequential-looking `await` calls hide the difference between "do these one
  after another" and "do these at the same time," making the most valuable
  performance property of asynchronous code, concurrency, opt-in and easy to
  forget rather than opt-out and hard to miss, the inverse of what explicit
  callback nesting made visible.
- The pattern is contagious through a codebase. A function that awaits
  anything must itself be declared `async`, and its callers must either
  `await` it or explicitly handle the resulting future/task/promise, which
  tends to propagate the `async` keyword outward until most of a call graph
  carries it, sometimes called "function coloring."
- In single-threaded cooperative runtimes, an `async` function with a long
  CPU-bound stretch and no `await` point starves every other pending task in
  the process for that entire stretch, a failure mode with no analogue in
  thread-per-request models.
- The compiler-generated state machine, or the heap-allocated continuation in
  garbage-collected runtimes, is real overhead per suspension point, small
  per call but non-trivial in extremely hot paths, which is one reason
  synchronous code is still preferred for tight inner loops even in languages
  that support async/await pervasively.
- In languages without a checked-exception-like signal on the type of an
  `await`ed call, nothing at the call site distinguishes an operation that
  cannot fail from one that can throw an arbitrary error, so failure handling
  discipline has to be maintained by convention rather than enforced by the
  type system.

## 11. Failure modes and misuse

**Fire-and-forget task swallowing an exception.** Symptom, an error that
should have surfaced never appears anywhere, and the operation it was part of
silently produces a wrong or incomplete result. Cause, an `async` function is
called without `await` and without the result being stored or otherwise
observed, so when it eventually rejects or throws, nothing is listening. In
JavaScript this becomes an unhandled promise rejection, in .NET an
unobserved task exception, in Python a warning about a coroutine that was
never awaited, and in Rust the future never even runs because nothing polled
it. Fix, either `await` the call, explicitly attach an error handler
(`.catch()`, a `try`/`catch` around an explicit await, `Task.Run` with proper
observation), or, where the intent genuinely is fire-and-forget, use the
runtime's blessed mechanism for that (`asyncio.create_task` plus tracking the
task in a set that is later awaited or cancelled on shutdown; Swift's
structured `Task { }` inside a scope that owns its lifetime) rather than
leaving a bare, unreferenced async call.

**Accidental serialization of independent work.** Symptom, an endpoint or
function that fetches from three independent sources takes roughly the sum of
their individual latencies instead of the maximum. Cause, each fetch is
awaited immediately after it is initiated (`await fetchA(); await fetchB();
await fetchC();`), so the second fetch does not even start until the first
one fully resolves, reproducing the sequential timeline from dimension 7
despite the operations having no actual dependency on each other. Fix, start
all the independent operations first, capturing their pending
promises/tasks/futures without awaiting, then await the whole set together
with the language's concurrent-await combinator, `Promise.all`,
`asyncio.gather`, `Task.WhenAll`, `tokio::join!`, or a structured task group.

**Blocking the event loop from inside an async function.** Symptom, an entire
Node.js process, or an entire Python asyncio event loop, becomes unresponsive
to every other pending task, including ones with no relation to the offending
code, for the duration of one call. Cause, an `async` function calls a
genuinely synchronous, blocking operation (a synchronous filesystem call, a
CPU-heavy computation, a blocking third-party library call) without ever
reaching an `await`, so the single thread driving the event loop has nothing
to interleave onto and the runtime cannot preempt mid-expression the way an
OS thread scheduler could. Fix, move the blocking work to a worker thread or
process pool and await the handoff (`asyncio.to_thread`, Node's
`worker_threads`, or, as FastAPI does automatically for plain `def` handlers,
dispatch to a thread pool), or break the computation into chunks with
explicit yield points if a true offload is not available.

**Awaiting a Rust future that is never polled.** Symptom, a future is
constructed and even assigned to a variable, but the operation it represents
never appears to happen, no side effect, no completion, silently. Cause,
Rust's futures are lazy and inert by design, `poll()` never gets called
unless something drives it, either an executor via `.await` inside an
`async fn` running on a runtime, or an explicit call to `block_on`. A future
built and then dropped without ever being awaited or spawned simply never
executes, which the language's own documentation calls out as a surprising
property of the model relative to eager futures in other languages. Fix,
always either `.await` the future inside a running async context or
`tokio::spawn` it explicitly onto the runtime; never construct a future
purely for its side effects and assume construction alone triggers them.

**Losing the original stack trace across an await boundary in older
tooling.** Symptom, an error thrown deep inside an awaited chain surfaces at
the top level with a stack trace that shows only the immediate throw site and
gives no indication of the calling chain that led there. Cause, this was a
real limitation of early async/await implementations and some transpilation
targets that did not preserve continuation metadata across suspension points;
it is largely solved in current JavaScript engines, current .NET, and current
Python, but reappears when async code is transpiled down to an older target
(older Babel configurations targeting pre-native-async engines, or CPS
transforms for embedded interpreters) that reconstructs control flow without
preserving the logical call chain. Fix, verify the actual runtime or
transpilation target genuinely supports native async/await stack
reconstruction before relying on stack traces for debugging asynchronous
failures; where it does not, add explicit contextual logging at each
suspension boundary as a substitute.

**Deadlock from mixing blocking `.Result`/`.Wait()` with async code on a
single-threaded synchronization context.** Symptom, a UI application or an
older ASP.NET (non-Core) request hangs indefinitely. Cause, calling
`.Result` or `.Wait()` synchronously on a `Task` from a context that has a
captured synchronization context (a UI thread, classic ASP.NET's request
context) blocks that context's single thread while it waits for the awaited
continuation, but the continuation was scheduled to resume on that exact same
now-blocked context, so it can never run. This is specific to environments
with a captured `SynchronizationContext`, absent by default in .NET Core's
default server contexts and in most other languages' dialects, but is one of
the most frequently reported production incidents in classic .NET WinForms
and WPF applications. Fix, await all the way up the call chain instead of
blocking on a task synchronously, or, when a synchronous boundary is truly
unavoidable, call `ConfigureAwait(false)` on the awaited task so its
continuation does not require the original captured context to resume on.

## 12. Trade-off matrix

| Force | Async/await | Raw callbacks | Bare Promise/Future chaining | OS thread-per-request (blocking I/O) |
|---|---|---|---|---|
| Readability of a multi-step sequence | High, reads top to bottom like synchronous code | Low, nesting depth grows with step count | Medium, chained but reads inside-out relative to execution order for nested cases | High for the sequence itself, but no concurrency without manual thread management |
| Error propagation | Native `try`/`catch` or equivalent, catches failures from any awaited step in the block | Manual, error-first argument convention must be honored at every callback | Requires a `.catch()` at the end of the chain, easy to omit on a branch | Native exceptions, but a blocked thread on failure still ties up the resource until timeout |
| Memory cost per pending operation | One state machine or heap continuation per suspended call, small and language-managed | One closure per callback, comparable cost, but scattered | One promise/future object plus its `.then()` registrations | One full OS thread stack, typically 512KB to 8MB, vastly higher per unit of concurrency |
| Concurrency is explicit or implicit | Implicit by default (sequential unless combined), explicit only when a combinator is used | Explicit by construction, nesting shows the dependency graph directly | Explicit at the chain level via `Promise.all` and similar | Explicit via number of threads spawned, but each thread runs truly in parallel on multi-core |
| Debuggability | High in modern runtimes, logical stack preserved across suspension | Low, stack context lost at each callback boundary | Medium, chain position visible but original call site often lost | High, a blocked thread has a completely normal, unbroken stack trace |
| Scales to tens of thousands of concurrent operations | Yes, this is the primary reason the pattern exists in server runtimes | Yes, same scalability as async/await since it is the same underlying model without the syntax | Yes, same underlying model | No, thread stack memory and OS scheduler overhead make this impractical past a few thousand threads |
| Requires a compatible runtime/scheduler | Yes, an event loop or executor must exist and drive the futures | No, works with any callback-capable API | No, works wherever the promise/future type is implemented | No, works with the OS thread scheduler that already exists |

## 13. Related and incompatible patterns

**Future/Promise** is the object async/await is built on top of in nearly
every dialect. The sibling entry in this repository describes the
future/promise pattern in its own right, as the value that represents a
not-yet-available result; async/await is best read as the sentence grammar
laid over that noun, syntax that lets code operate on a future/promise as
though it were an ordinary value while the underlying object still carries all
the same pending/fulfilled/rejected machinery.

**Reactor and Proactor** are the event-demultiplexing patterns that typically
sit underneath the scheduler an async/await runtime depends on. In Node.js
this is libuv's reactor-style event loop; the async functions a JavaScript
program writes are, at the platform boundary, callbacks the reactor invokes
when a registered file descriptor or timer becomes ready, wrapped by the
language runtime so they appear as resumed coroutines rather than raw
callbacks. Understanding async/await without understanding that a reactor or
proactor is doing the actual OS-level event waiting underneath it leaves a
gap in reasoning about why suspension is cheap in the first place.

**Half-Sync/Half-Async** describes the architectural split between a
synchronous layer that application code is written in and an asynchronous
layer that handles the actual I/O multiplexing, connected by a queue. A
typical async/await runtime is a specific, language-integrated instance of
this architecture, the "synchronous-looking" async function bodies are the
sync layer from the caller's point of view, while the event loop or executor
is the async layer, and the pending future/task/promise objects are the
queueing mechanism between them.

**Thread Pool** is both a complementary and a sometimes-competing pattern.
Complementary, because CPU-bound work that should not run on the event loop's
own thread is routinely offloaded to a thread pool and its completion awaited
(`asyncio.to_thread`, `Task.Run`, worker threads), making thread pools the
standard escape hatch from async/await's single-threaded-cooperative variant.
Competing, because thread-per-request architectures solve the exact same
"handle many concurrent operations without one blocking the rest" problem
using OS threads directly, at a much higher memory cost per unit of
concurrency but with a materially simpler mental model and no function
coloring.

**Producer-Consumer**, implemented with an async queue (`asyncio.Queue`,
JavaScript's async iterators feeding a channel, Rust's `tokio::sync::mpsc`),
is the standard way to connect an async/await-based consumer to work that
arrives over time rather than being requested on demand, and is frequently
composed with async/await in streaming and backpressure-sensitive systems.

**Structured concurrency task groups** (Swift's `TaskGroup`, Kotlin's
`coroutineScope`, Python's `asyncio.TaskGroup`) are not a separate pattern so
much as a disciplined variant of async/await's own concurrent-await
combinators, and this entry treats them as an implementation variant, see
dimension 8, rather than a related-but-distinct pattern, because they operate
entirely within the async/await model rather than alongside it.

No pattern in this family is flagged as directly incompatible with
async/await. The closest candidate, thread-per-request blocking I/O, is not
incompatible so much as a different point on the same trade-off curve
(dimension 12), and the two are frequently combined deliberately, an
async/await-based server offloading specific blocking calls onto a thread
pool rather than the two approaches genuinely conflicting.

## 14. Refactoring path in and out

**Introducing async/await into callback-based code.** Start at the leaves.
Wrap the lowest-level callback-taking function (a raw database driver call, a
raw HTTP client call) in a thin adapter that returns a promise/future/task
instead of accepting a callback, most language ecosystems ship a standard
helper for exactly this (Node's `util.promisify`, .NET's
`TaskCompletionSource`, Python's manual `asyncio.Future` bridging). Once the
leaf returns an awaitable, mark its immediate caller `async` and replace the
callback registration with `await`. Work outward one caller at a time,
re-running the existing test suite after each step, because a partially
converted call chain, some layers async, some still callback-based, still
functions correctly as long as each boundary is bridged with an adapter; there
is no requirement to convert an entire codebase in one pass. Where multiple
independent callback calls used to fire concurrently by construction (each
one registered separately, all pending at once), be deliberate about
preserving that concurrency when converting, using the language's
concurrent-await combinator rather than accidentally serializing them, this is
the single most common regression introduced during this refactor, see
dimension 11.

**Introducing async/await into promise/future-chained code.** This direction
is close to mechanical. A `.then(x => ...).then(y => ...).catch(err => ...)`
chain becomes a `try { const x = await stepOne(); const y = await
stepTwo(x); } catch (err) { ... }` block with the same steps in the same
order. The main judgement call is deciding whether steps that were chained
sequentially by habit rather than by real dependency should become concurrent
during the conversion, which is a good moment to audit for the accidental
serialization failure mode rather than simply transliterating the chain
one-to-one.

**Removing async/await where it no longer earns its place.** This happens
most often when a function that used to perform genuine I/O has been
refactored to be purely synchronous, for example a network call replaced by
an in-memory cache lookup, and the `async`/`await` keywords are the only
remaining trace of the old implementation. Confirm the function body no
longer contains any `await` expression, remove the `async` modifier, change
the return type from the wrapped type back to the bare type, and then walk
every caller, removing the corresponding `await` at each call site. This
removal has to be done carefully in the outward direction exactly like the
introduction does, because a caller that still awaits a now-synchronous
function will simply keep working (an already-resolved value awaits
trivially in every dialect), which means the propagation of the removal is
easy to defer indefinitely and easy to forget, leaving dead `async` markers
scattered through a codebase, a form of the code smell most catalogs call
speculative generality.

## 15. Testing and verification

Testing async/await code is, in the common case, easier than testing
callback-based code, because the test itself can simply `await` the function
under test and assert on its ordinary return value or thrown error, using the
exact same assertion machinery the test framework already uses for
synchronous code, `expect(await fn()).toBe(...)` in JavaScript,
`assert result == expected` after `await fn()` in Python with `pytest-asyncio`,
`#[tokio::test]` in Rust letting a test function itself be `async`. This is a
genuine testability improvement over manually wiring a callback, a done()
signal, and a timeout into a test rig, which was the standard shape of
asynchronous tests before the pattern existed.

What becomes harder is testing the concurrency behavior itself rather than
the correctness of any single awaited step. A test that wants to assert "these
two operations actually ran concurrently, not sequentially" cannot simply
check final return values, because both the sequential and the concurrent
version of the code under test produce the identical final result, only the
wall-clock timing differs. The standard technique is to inject a controllable
fake clock or a deterministic mock scheduler and assert on the relative order
and timing of internal events (using something like Python's
`unittest.mock` combined with a stub `asyncio.sleep`, or Rust Tokio's
`#[tokio::test(start_paused = true)]` with `tokio::time::advance`, which lets
a test manually step virtual time forward and assert exactly which pending
awaits resolve at each step, rather than relying on real wall-clock sleeps
that make tests slow and flaky).

Testing the failure modes in dimension 11 specifically requires deliberate
fault injection, an unhandled rejection is tested by asserting a global
rejection handler fires when a fire-and-forget async call is made without
attaching a handler; event-loop blocking is tested by asserting that a second,
unrelated async operation scheduled concurrently with the offending call
still completes within its expected time budget; the .NET deadlock failure
mode is tested by exercising the specific captured-`SynchronizationContext`
scenario in an integration test rather than a unit test, since the deadlock
depends on execution context that a pure unit test typically does not
recreate.

Test doubles for the awaited dependency itself are the same shape they would
be for a synchronous dependency, a stub that returns a fixed value, a mock
that records calls and asserts on them, a fake that implements a lightweight
real behavior, the only difference is that the double's method must itself be
`async` (or return an already-resolved promise/task/future) so that awaiting
it in the code under test behaves correctly without requiring the test to
change its own control flow.

## 16. Observability signals

A healthy async/await system, whether an event loop or a work-stealing
executor, shows a low and stable count of pending, unresolved
tasks/promises/futures relative to the throughput of new ones being created,
meaning work is being drained roughly as fast as it arrives. The single most
useful metric to expose is event-loop lag (Node.js) or scheduler tick latency
(most executors), the delay between when a timer or callback was scheduled to
run and when it actually got a chance to run; a rising trend in this metric
is the most direct, dialect-agnostic signal that something is blocking the
loop or the pool from keeping up, which is exactly the "blocking the event
loop" failure mode from dimension 11 made visible on a dashboard before it
becomes a full outage.

Per-task duration histograms, bucketed by the logical operation name rather
than by a generic "task" label, surface which specific awaited call is the
long pole; most production async runtimes support attaching a name or
context to a task (Node's `async_hooks` and the newer `AsyncLocalStorage` for
context propagation, .NET's `Activity` and distributed tracing integration,
Python's `contextvars` combined with structured logging, Rust's `tracing`
crate with `#[instrument]` on async functions) and this attribution is what
turns a raw latency number into an actionable one.

Counting unhandled rejections, unobserved task exceptions, and warnings about
coroutines that were never awaited is a direct observability signal for the
fire-and-forget failure mode; every mainstream runtime exposes a global hook
for exactly this (`process.on('unhandledRejection', ...)` in Node.js,
`TaskScheduler.UnobservedTaskException` in .NET, Python's
`asyncio.get_event_loop().set_exception_handler(...)` alongside its built-in
"coroutine was never awaited" `RuntimeWarning`), and a healthy system should
have this count at zero in steady state, with any non-zero rate treated as a
bug to fix rather than noise to filter.

For work-stealing multi-threaded runtimes specifically, thread pool
utilization and queue depth (Tokio's runtime metrics, .NET's `ThreadPool`
queue length counters) matter in addition to the single-threaded loop-lag
signal, because starvation in these runtimes can show up as high queue depth
with idle threads if a subset of tasks are unfairly hogging specific worker
threads, a distinct symptom from the pure event-loop-lag picture that a
single-threaded runtime produces.

## 17. Security and privacy implications

This entry's engineering judgement is that async/await itself, as a syntactic
and control-flow feature, is largely silent on security, it changes when code
runs relative to other code, not what data that code touches or how it
validates input, so the pattern does not by itself introduce a new class of
vulnerability the way, for example, a deserialization pattern or a template
pattern might. The implications that do exist are indirect, arising from the
concurrency the pattern makes easy to introduce.

Concurrent awaiting of independently-triggered async operations that share
mutable state, a session object, a cache entry, an in-memory rate limiter,
reintroduces classic time-of-check-to-time-of-use (TOCTOU) race conditions in
languages where a single-threaded event loop had previously made such races
easy to overlook, because two logically concurrent `await`ed operations can
interleave at any suspension point even on a single thread, not only across
OS threads. A rate limiter implemented as "read the current count, if under
the limit increment and proceed" is exploitable if the read and the increment
straddle an `await`, because a second concurrent request can read the same
pre-increment count before the first request's increment lands, silently
defeating the limit; the fix is the same as for any TOCTOU issue, make the
check-and-update atomic with respect to concurrent awaits (a single
non-suspending critical section, an actual mutex around the shared state, or
an atomic operation provided by the underlying store) rather than trusting
single-threaded execution to serialize it implicitly.

Error messages surfaced from a caught exception at an `await` boundary can
inadvertently leak internal detail, a stack trace, a database connection
string embedded in a driver's error message, an internal service hostname,
if the same generic top-level error handler that catches asynchronous
failures for logging purposes is also the one that formats a response sent
back to an external caller; this is a general error-handling hygiene issue
rather than something specific to async/await, but the pattern's tendency to
centralize error handling at a single `try`/`catch` wrapping several `await`s
makes it easy to accidentally route an internal-only error message down the
same path as a user-facing one.

There is no meaningful async/await-specific data-handling or storage
implication beyond the general point that a suspended async function's local
state, including any sensitive value held in a local variable across an
`await`, persists in whatever memory the compiler-generated state machine or
continuation object occupies for the entire duration of the suspension, which
in a garbage-collected language can be materially longer than the equivalent
value would have lived on a synchronous call stack, a consideration that
matters for the same reason any longer-lived copy of sensitive data in memory
matters, a larger window during which a memory dump or a debugging tool could
observe it, not a new mechanism of exposure.

## Code examples

Four dialects, chosen because each exercises a distinct scheduling model from
dimension 8, JavaScript's callback-desugared single-threaded event loop,
Python's generator-descended coroutine, Rust's poll-based work-stealing
runtime, and Swift's structured task group. All four fetch three independent
"orders" concurrently, sum their totals, and propagate a failure through the
language's native error mechanism. Every sample was compiled or run against
the toolchain versions on this machine and produces `total: 60`. Java and
Kotlin are omitted because no Java runtime was available on this machine to
verify a sample against, per the honesty requirement in the template rather
than any claim that the pattern does not apply to those languages.

```typescript
interface Order {
  id: number;
  total: number;
}

function delay<T>(value: T, ms: number): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

async function fetchOrder(id: number): Promise<Order> {
  if (id < 0) {
    throw new Error("invalid order id");
  }
  return delay({ id, total: id * 10 }, 20);
}

async function fetchOrderTotal(ids: number[]): Promise<number> {
  const orders = await Promise.all(ids.map((id) => fetchOrder(id)));
  return orders.reduce((sum, order) => sum + order.total, 0);
}

async function main(): Promise<void> {
  try {
    const total = await fetchOrderTotal([1, 2, 3]);
    console.log("total:", total);
  } catch (err) {
    console.error("failed:", (err as Error).message);
  }
}

main();
```

Compiled with `npx tsc --target es2020 --module commonjs` (TypeScript 7.0.2)
and run with `node`. Output is `total, 60`.

```python
import asyncio
from dataclasses import dataclass


@dataclass
class Order:
    id: int
    total: int


async def fetch_order(order_id: int) -> Order:
    if order_id < 0:
        raise ValueError("invalid order id")
    await asyncio.sleep(0.02)
    return Order(id=order_id, total=order_id * 10)


async def fetch_order_total(ids: list[int]) -> int:
    orders = await asyncio.gather(*(fetch_order(i) for i in ids))
    return sum(order.total for order in orders)


async def main() -> None:
    try:
        total = await fetch_order_total([1, 2, 3])
        print("total:", total)
    except ValueError as exc:
        print("failed:", exc)


if __name__ == "__main__":
    asyncio.run(main())
```

Run with `python3` (3.14.6). Output is `total, 60`.

```rust
use std::future::Future;
use std::pin::Pin;
use std::task::{Context, Poll, RawWaker, RawWakerVTable, Waker};

#[derive(Debug)]
struct Order {
    id: i64,
    total: i64,
}

struct DelayedOrder {
    id: i64,
    ticks_left: u32,
}

impl DelayedOrder {
    fn new(id: i64) -> Self {
        DelayedOrder { id, ticks_left: 2 }
    }
}

impl Future for DelayedOrder {
    type Output = Result<Order, String>;

    fn poll(mut self: Pin<&mut Self>, _cx: &mut Context<'_>) -> Poll<Self::Output> {
        if self.id < 0 {
            return Poll::Ready(Err("invalid order id".to_string()));
        }
        if self.ticks_left == 0 {
            Poll::Ready(Ok(Order {
                id: self.id,
                total: self.id * 10,
            }))
        } else {
            self.ticks_left -= 1;
            Poll::Pending
        }
    }
}

fn fetch_order(id: i64) -> DelayedOrder {
    DelayedOrder::new(id)
}

async fn fetch_order_total(ids: &[i64]) -> Result<i64, String> {
    let mut total = 0;
    for &id in ids {
        let order = fetch_order(id).await?;
        total += order.total;
    }
    Ok(total)
}

fn noop_raw_waker() -> RawWaker {
    fn no_op(_: *const ()) {}
    fn clone(_: *const ()) -> RawWaker {
        noop_raw_waker()
    }
    let vtable = &RawWakerVTable::new(clone, no_op, no_op, no_op);
    RawWaker::new(std::ptr::null(), vtable)
}

fn block_on<F: Future>(fut: F) -> F::Output {
    let waker = unsafe { Waker::from_raw(noop_raw_waker()) };
    let mut cx = Context::from_waker(&waker);
    let mut fut = Box::pin(fut);
    loop {
        match fut.as_mut().poll(&mut cx) {
            Poll::Ready(value) => return value,
            Poll::Pending => continue,
        }
    }
}

fn main() {
    match block_on(fetch_order_total(&[1, 2, 3])) {
        Ok(total) => println!("total: {}", total),
        Err(e) => println!("failed: {}", e),
    }
}
```

This sample is deliberately dependency-free, using only `std::future::Future`,
`std::task`, and a hand-written, busy-polling `block_on`, rather than pulling
in Tokio, so a reader can see the exact `poll`/`Poll`/`Waker` machinery from
dimension 6 driving real `async fn`/`.await` code with nothing hidden inside a
crate. Built and run with `rustc --edition 2021 -O` (rustc 1.97.1), no
`Cargo.toml` required. Output is `total, 60`. Because this minimal executor
polls one future to completion before moving to the next, it awaits the three
fetches sequentially, not concurrently. A production Rust program reaches the
concurrent-await timeline from dimension 7 by handing futures to a real
multi-task executor such as Tokio (`tokio::spawn` plus `tokio::join!`), which
this entry's dimension 8 and dimension 9 both cover separately with Tokio's
own documentation as the source.

```swift
import Foundation

struct Order {
    let id: Int
    let total: Int
}

enum OrderError: Error {
    case invalidId
}

func fetchOrder(id: Int) async throws -> Order {
    if id < 0 {
        throw OrderError.invalidId
    }
    try await Task.sleep(nanoseconds: 20_000_000)
    return Order(id: id, total: id * 10)
}

func fetchOrderTotal(ids: [Int]) async throws -> Int {
    try await withThrowingTaskGroup(of: Order.self) { group in
        for id in ids {
            group.addTask { try await fetchOrder(id: id) }
        }
        var total = 0
        for try await order in group {
            total += order.total
        }
        return total
    }
}

@main
struct Demo {
    static func main() async {
        do {
            let total = try await fetchOrderTotal(ids: [1, 2, 3])
            print("total: \(total)")
        } catch {
            print("failed: \(error)")
        }
    }
}
```

Compiled with `swiftc -O -parse-as-library` (Swift 6.3.2) and run directly.
Output is `total, 60`. This sample uses `withThrowingTaskGroup`, the
structured concurrency variant from dimension 8, so a failure in any one
fetch cancels the remaining siblings automatically rather than leaving them
detached.

## 18. References

- ECMA-262, the ECMAScript Language Specification, TC39. https://tc39.es/ecma262/ (verified 2026-08-02).
- TC39, `proposal-async-await`, the historical proposal repository for JavaScript async/await. https://github.com/tc39/proposal-async-await (verified 2026-08-02).
- Yury Selivanov, PEP 492, "Coroutines with async and await syntax," created 9 April 2015, accepted 5 May 2015, target Python 3.5. https://peps.python.org/pep-0492/ (verified 2026-08-02).
- Python Software Foundation, `asyncio` task documentation, `asyncio.gather`, `asyncio.create_task`, `asyncio.TaskGroup`. https://docs.python.org/3/library/asyncio-task.html (verified 2026-08-02).
- Microsoft, "Asynchronous programming in C#," Microsoft Learn, describing the Task-based Asynchronous Pattern (TAP) built on `async`/`await`, last updated 2025-03-10 per page metadata. https://learn.microsoft.com/en-us/dotnet/csharp/asynchronous-programming/ (verified 2026-08-02).
- The Rust Project, "Async-await on stable Rust!," the Rust Blog, announcing stabilization in Rust 1.39.0, 7 November 2019. https://blog.rust-lang.org/2019/11/07/Async-await-stable/ (verified 2026-08-02).
- The Rust Project, "Getting Started," Asynchronous Programming in Rust (the Async Book). https://rust-lang.github.io/async-book/01_getting_started/01_chapter.html (verified 2026-08-02).
- The Rust Project, "The Future Trait," Asynchronous Programming in Rust (the Async Book), defining `trait Future`, `Poll`, and `Waker`. https://rust-lang.github.io/async-book/02_execution/02_future.html (verified 2026-08-02).
- John McCall and Doug Gregor (review manager Ben Cohen), Swift Evolution proposal SE-0296, "Async/await," implemented Swift 5.5. https://github.com/apple/swift-evolution/blob/main/proposals/0296-async-await.md (verified 2026-08-02).
- Node.js Foundation, "The Node.js Event Loop, Timers, and process.nextTick()," Node.js official guides. https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick (verified 2026-08-02).
- Sebastian Ramirez et al., "Concurrency and async / await," FastAPI documentation. https://fastapi.tiangolo.com/async/ (verified 2026-08-02).
- The Tokio Project, "Overview," the Tokio tutorial, describing Tokio as the asynchronous runtime built on Rust's async/await. https://tokio.rs/tokio/tutorial (verified 2026-08-02).
