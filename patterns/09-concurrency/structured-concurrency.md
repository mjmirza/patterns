---
name: Structured Concurrency
slug: structured-concurrency
family: 09-concurrency
category: Concurrency
aliases: [Nursery Pattern, Scoped Concurrency, Task Scope]
first_described: "Martin Sustrik, libdill design notes, 2016. Term popularized by Nathaniel J. Smith, Trio project, 2017"
maturity: established
related: [fork-join, future-promise, actor-model, thread-pool, barrier, countdown-latch, producer-consumer]
incompatible_with: [half-sync-half-async]
verified: 2026-08-02
---

# Structured Concurrency

## 1. Name, aliases, and lineage

The canonical name is Structured Concurrency. The term was coined by Martin
Sustrik while designing the C library libdill in 2016, arguing that
concurrent code should follow the same block-scoped discipline that structured
programming brought to control flow decades earlier. Sustrik's design notes
describe channels and coroutines whose lifetimes are bounded by the enclosing
block rather than left to float free in a global scheduler.

The idea reached a wider audience through Nathaniel J. Smith's essay "Notes on
structured concurrency, or. go statement considered harmful," written while
Smith built the Trio library for Python. Smith's central comparison is that a
bare `go` statement, or a bare spawned thread, is the concurrency equivalent
of `goto`. it lets execution jump into a background task with no caller
obliged to wait for it, no scope bounding its lifetime, and no single place an
exception from it is guaranteed to surface. Structured concurrency replaces
the unconditional spawn with a scoped construct, commonly called a nursery, in
which every child task must finish, be cancelled, or report its failure
before the scope that opened it can exit. Nathaniel J. Smith, "Notes on
structured concurrency, or. go statement considered harmful," vorpus.org,
2018,
https://vorpus.org/blog/notes-on-structured-concurrency-or-go-statement-considered-harmful/
verified 2026-08-02.

The **Nursery Pattern** alias comes directly from Trio's API name,
`trio.open_nursery()`. **Scoped Concurrency** and **Task Scope** are the names
used informally alongside Kotlin's `CoroutineScope` and Java's
`StructuredTaskScope` respectively, treated as synonyms for the same
discipline even though each library gives the concrete type its own name.
Roman Elizarov independently arrived at a materially identical design for
Kotlin coroutines around the same period, publishing the `CoroutineScope`
type and the `coroutineScope()` builder as the language's structured
concurrency primitive. JetBrains, Kotlin documentation, "Coroutines basics,"
section "Structured concurrency,"
https://kotlinlang.org/docs/coroutines-basics.html verified 2026-08-02.

Structured concurrency is not one specific API. it is a discipline that
several languages and libraries arrived at independently, and the concrete
shape of the guarantee differs enough between implementations to matter in
practice, which is why dimension 8 and dimension 9 treat each one separately
rather than as interchangeable.

## 2. Problem and context

A function spawns concurrent work, a network call, a background computation,
a fan-out to several services, and returns before that work is guaranteed to
be done. The caller of that function has no reliable way to know, from
reading the function's signature or its body, whether the work it kicked off
is still running somewhere. If the work fails, the exception may surface on a
thread nobody is watching, in a callback nobody registered a handler for, or
never at all. If the caller wants to cancel everything because the
surrounding request was aborted, there is no single handle that reaches every
task the function spawned, especially once that function itself called
another function that spawned more work.

This is the everyday shape of the problem in a request-handling server. A
handler fires off three downstream calls to gather the fields of a response.
One call hangs. The handler eventually times out and returns an error to its
own caller, but the two other downstream calls, and any goroutine, thread, or
task each of them spawned in turn, keep running in the background with no
supervisor and no cancellation signal. The process accumulates orphaned work
under load, and the eventual crash or memory exhaustion happens far from the
line of code that caused it.

The context in which the problem becomes acute has three properties. First,
concurrency is used for genuine parallel work inside a single logical
operation, a fan-out and fan-in, rather than for a long-lived independent
background service. Second, the language or runtime offers a primitive for
spawning concurrent work, a thread, a goroutine, a coroutine, or a task, that
by default detaches from its creator once spawned. Third, the code must
compose. a function that spawns work is itself called from other functions
that may also spawn work, and the caller at every level needs a predictable
answer to "is everything I started actually finished."

Outside that context, in particular for a genuinely independent long-running
background job with no caller waiting on it, structured concurrency is the
wrong tool, and dimension 4 says so directly.

## 3. Forces

- **Composability.** Favoured, and this is the pattern's reason to exist. A
  function that spawns concurrent work internally and joins it before
  returning is safe to call from anywhere, including from inside another
  structured scope, without the caller needing to know concurrency happened at
  all.
- **Error visibility.** Favoured. An exception raised by a child task is
  guaranteed to surface at the enclosing scope, either immediately by
  cancelling siblings or at the latest when the scope closes, rather than
  being swallowed by a detached thread or an unread future.
- **Latency.** Mixed. Waiting for every child to finish before the scope can
  exit adds latency equal to the slowest child, which is desirable when the
  result genuinely needs all children but a cost when one child's result is
  optional and the caller would rather not wait for it.
- **Resource lifetime clarity.** Favoured. A worker pool, a socket, or a lock
  acquired for the duration of the scoped work is guaranteed to outlive every
  task that uses it, because the scope cannot close and trigger cleanup until
  every child has stopped touching that resource.
- **Cancellation propagation.** Favoured. Cancelling the parent, whether from
  an explicit call, a timeout, or the parent's own scope being cancelled,
  propagates to every descendant automatically, without the caller needing to
  hold and thread through a cancellation token by hand at every layer.
- **Flexibility of lifetime shape.** Sacrificed. A task whose useful lifetime
  genuinely outlives the function that started it, a cache warmer, a
  connection keep-alive, a metrics flusher, does not fit the block-scoped
  shape and needs a deliberately unstructured escape hatch, discussed in
  dimension 4.
- **Debuggability.** Favoured. Because every task has exactly one place it was
  spawned and exactly one place it is joined, a stack trace or a task dump can
  reconstruct the full concurrency tree of a running program, which is
  materially harder when tasks are handed off between unrelated owners.
- **Migration cost.** Sacrificed, once. Retrofitting structured concurrency
  onto a codebase full of bare thread spawns or detached goroutines is not a
  local change. it requires threading a scope object, or its language
  equivalent, through every call site that currently fires and forgets.

## 4. Applicability and non-applicability

Reach for structured concurrency when the following hold.

- The concurrent work is a means to computing a single result or completing a
  single logical operation, a fan-out request, a parallel validation, a
  scatter-gather query, and the caller genuinely needs to wait for it.
- The function's caller should be able to treat the function as an ordinary,
  possibly slow, synchronous-looking call. anything it does concurrently
  internally is an implementation detail that must not leak past the return.
- A failure in any one piece of concurrent work should cancel the rest of that
  work and be reported to whoever is waiting, rather than being lost silently.
- The lifetime of a shared resource, a connection, a buffer, a lock, must be
  bounded by the concurrent work that uses it, so cleanup can run exactly once
  after every user has stopped.
- The code must be testable and composable. a test should be able to call the
  function, get a result or an exception, and know with certainty that no
  background work is still running afterward.

Do NOT reach for structured concurrency in these cases.

- **The task's lifetime genuinely exceeds its creator's.** A daemon that polls
  a queue for the life of the process, a background cache refresher, a
  long-running WebSocket connection handler, has no natural enclosing scope to
  join it against. Forcing it into a nursery either blocks the nursery forever
  or requires an artificial top-level scope that lives as long as the process,
  which is an unstructured spawn wearing extra ceremony with no payoff. Use a
  supervised, independently owned task, an actor, or a service-level
  lifecycle manager instead, see the Actor Model entry.
- **The concurrent work is fire-and-forget by explicit design and failure
  truly does not matter to the caller.** A best-effort analytics ping that the
  caller does not want to wait for or fail because of is not a structured
  child. it is deliberately unstructured, and that choice should be visible in
  the code, for example as a separate, clearly labelled unstructured spawn
  with its own error handling, rather than hidden inside a scope that
  pretends to wait for it.
- **The runtime has no cancellation-aware primitive to build on.** Structured
  concurrency's cancellation propagation depends on the underlying task or
  thread primitive being able to receive and check a cancellation signal
  cooperatively. In a runtime with only ungovernable OS threads and no
  cancellation API, a scope can join threads but cannot cancel them, which
  weakens the guarantee to "we will notice failure" without "we can stop
  wasted work," and that limitation should be stated rather than assumed away.
- **A single task is being spawned with no siblings and no need to wait.** One
  fire-and-forget task does not need a scope. adding one is ceremony without
  payoff. This mirrors the general warning against introducing structure
  before there is a second thing to structure, the same caution given in the
  Factory Method entry's non-applicability list.
- **The work is CPU-bound and the bottleneck is the number of cores, not
  coordination.** Structured concurrency governs lifetime and error
  propagation. it says nothing about scheduling CPU-bound work efficiently
  across cores, which is the concern of Fork-Join and work-stealing pools, see
  the Fork-Join entry. Structured concurrency composes with those, it does not
  replace them.
- **Extremely fine-grained parallelism where per-task bookkeeping overhead is
  the actual bottleneck.** A scope that tracks each child for join and
  cancellation adds a small but nonzero cost per child. Spawning millions of
  tiny tasks inside nurseries can turn that bookkeeping into the real cost
  centre, at which point a data-parallel construct that avoids per-item task
  objects, a vectorized loop or a bulk parallel-for, is the right tool.

## 5. Structure

- **Scope (Nursery, TaskGroup, StructuredTaskScope, CoroutineScope).** The
  block-scoped object opened by the parent. It is the single owner of every
  task spawned inside it, tracks each child's completion, and cannot exit
  until all children have finished, been cancelled and observed to stop, or
  reported an error according to the scope's policy.
- **Parent task (Owner).** The task, thread, or coroutine that opens the
  scope. It is the one entity permitted to spawn children into that scope and
  to observe the scope's outcome. Some implementations enforce single-owner
  access mechanically, discussed under Java in dimension 8.
- **Child task.** A unit of concurrent work spawned into the scope. Every
  child task's lifetime is a strict subset of the scope's lifetime. a child
  cannot outlive the block that spawned it.
- **Cancellation signal.** The mechanism, cooperative in every mainstream
  implementation, by which the scope tells a child to stop. A child observes
  cancellation at await points, blocking calls the runtime instruments, or
  explicit checks, and is expected to unwind promptly rather than being force
  killed.
- **Error aggregation policy.** The rule the scope applies when more than one
  child fails. The dominant modern shape, seen in Python's `TaskGroup` and
  Trio's nursery, is to collect every failure into a single exception group
  rather than surface only the first one and discard the rest.

The relationship that defines the pattern. the scope's lifetime strictly
contains every child's lifetime, and no reference to a child survives past the
scope's exit. This is a stronger guarantee than a thread pool or a plain
future gives, because a future can be handed to code far away from where it
was created and awaited, or never awaited at all, whereas a structured child
has exactly one place, the enclosing scope, that is responsible for it.

## 6. ASCII structure diagram

```
    Parent task
   +----------------------------------------------------+
   |   opens                                             |
   |   +----------------------------------------------+  |
   |   |                  Scope (nursery)              |  |
   |   |  tracks: child A, child B, child C            |  |
   |   |  policy: cancel siblings on first failure      |  |
   |   |                                                |  |
   |   |   spawn        spawn        spawn              |  |
   |   |    |             |             |               |  |
   |   |    v             v             v               |  |
   |   | +--------+   +--------+   +--------+           |  |
   |   | |Child A |   |Child B |   |Child C |           |  |
   |   | |(task)  |   |(task)  |   |(task)  |           |  |
   |   | +--------+   +--------+   +--------+           |  |
   |   |    |             |             |               |  |
   |   |    +-------------+-------------+               |  |
   |   |                  |                              |  |
   |   |            all joined or                        |  |
   |   |         cancelled and observed                  |  |
   |   +----------------------------------------------+  |
   |   scope exit blocks here until the above is true    |
   +----------------------------------------------------+
    control returns to code after the scope, with either
    a combined result, or a raised (possibly grouped) error

    No arrow ever leaves the scope box carrying a live
    child reference. A child's lifetime never crosses
    the scope's closing edge.
```

## 7. Dynamics

The defining dynamic is that the scope's exit is a synchronization barrier,
not a fire-and-return. The sequence below shows the happy path and the
failure path for a scope with two children.

```
Parent           Scope              Child A            Child B
  |                 |                   |                  |
  |-- open scope -->|                   |                  |
  |                 |                   |                  |
  |-- spawn(A) ---->|-- start -------->|                  |
  |-- spawn(B) ---->|-- start ------------------------>   |
  |                 |                   |                  |
  |-- (end of       |                   |                  |
  |    scope block)|                   |                  |
  |                 |<--- waiting ----- (running) -------- (running)
  |                 |                   |                  |
  |                 |                   |-- result A ----->|
  |                 |<------------------|                  |
  |                 |                   |                  |-- error B ---->|
  |                 |<-------------------------------------|                |
  |                 |                   |                                  |
  |                 |-- cancel A? -->|  (A already done, no-op)             |
  |                 |                   |                                  |
  |                 |-- combine results/errors --                          |
  |<-- raises grouped error, or returns combined result --|                |
  |                 |                   |                                  |
```

Two properties are worth naming because they are the source of the pattern's
real-world subtlety. First, cancellation of a sibling after one child fails is
a request, not an interrupt. a child that is deep inside a blocking,
non-cancellation-aware call, a synchronous file read on a thread with no
cancellation hook, will not stop until that call returns on its own, so
"cancel on first failure" bounds wasted work but does not guarantee instant
termination. Second, when two children fail close together in time, before
either cancellation has taken effect, both errors are live at the same
moment, which is exactly why the modern implementations, Python's `TaskGroup`
and Trio's nursery, raise an exception group holding every failure rather
than picking one and discarding the rest, a design choice covered with
citations in dimension 9.

## 8. Implementation variants

**Nursery with start_soon (Trio, Python).** The scope object exposes a
non-blocking spawn method, and the `async with` block itself is the join
point, blocking on exit until every child has exited. Failures from multiple
children are combined into a `BaseExceptionGroup`. Trio project, "Trio
reference," section on nurseries and `open_nursery`,
https://trio.readthedocs.io/en/stable/reference-core.html verified
2026-08-02.

**TaskGroup (Python asyncio, standard library).** Added to the standard
library's `asyncio` module in Python 3.11 directly modeled on Trio's nursery.
`asyncio.TaskGroup` is an async context manager. `create_task()` spawns a
child inside it, the context manager's `__aexit__` is the join point, the
first non-`CancelledError` failure cancels the remaining children, and every
failure that survives is combined into an `ExceptionGroup` or
`BaseExceptionGroup` and raised once the scope closes. Python Software
Foundation, "asyncio task groups," `asyncio.TaskGroup`,
https://docs.python.org/3/library/asyncio-task.html#task-groups verified
2026-08-02.

**TaskGroup and async let (Swift Concurrency).** Swift offers two related
shapes. `withTaskGroup(of:)` and `withThrowingTaskGroup(of:)` open a scope in
which `addTask` spawns homogeneous children, iterated with `for await` inside
the closure, and the closure itself is the join point. `async let` is the
fixed-arity sibling, binding a single child task to a local constant whose
value is awaited explicitly, with the compiler statically requiring the bound
task is awaited or implicitly cancelled before the enclosing scope exits.
Cancellation of the parent task propagates to every child in either form.
Apple, Swift Standard Library documentation, `TaskGroup`,
https://developer.apple.com/documentation/swift/taskgroup verified
2026-08-02.

**coroutineScope and structured launch (Kotlin Coroutines).** Kotlin's
`CoroutineScope` interface and the `coroutineScope { }` suspending builder
create a scope whose lifetime is tied to the calling coroutine. `launch` and
`async` spawn children bound to that scope, and `coroutineScope` suspends
until every child launched inside it, directly or via nested calls, has
completed, propagating cancellation and failure up the resulting coroutine
tree. JetBrains, Kotlin documentation, "Coroutines basics," section
"Structured concurrency," https://kotlinlang.org/docs/coroutines-basics.html
verified 2026-08-02.

**StructuredTaskScope (Java).** Finalized as a standard feature in JDK 25
under JEP 505, after several preview rounds. `StructuredTaskScope.open()`
returns a scope used in a try-with-resources block. `fork()` starts a subtask
on a new virtual thread, `join()` blocks the owner thread until the subtasks
complete according to a `Joiner` policy, for example
`awaitAllSuccessfulOrThrow` or `anySuccessfulResultOrThrow`, and only the
owner thread that opened the scope may fork, join, or close it, enforced at
runtime with a `WrongThreadException` on violation. Oracle, Java SE 25 API
Specification, `java.util.concurrent.StructuredTaskScope`,
https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/StructuredTaskScope.html
verified 2026-08-02.

**errgroup (Go, library convention rather than a language feature).** Go has
no built-in structured concurrency construct. goroutines are unstructured by
default, spawned with the bare `go` statement Smith's essay names directly.
`golang.org/x/sync/errgroup` is the community-standard approximation. a
`Group` whose `Go(f)` method starts a goroutine, `Wait()` blocks until every
started goroutine returns, and `WithContext` derives a `context.Context` that
is cancelled the moment any goroutine returns a non-nil error, giving
cooperating goroutines a signal to stop early. It is a library convention
layered on top of an unstructured primitive, not a compiler-enforced
guarantee, so nothing stops a goroutine from calling `go` directly instead of
`group.Go` and escaping the scope entirely. Go project,
`golang.org/x/sync/errgroup` package documentation,
https://pkg.go.dev/golang.org/x/sync/errgroup verified 2026-08-02.

**Scoped threads (Rust, `std::thread::scope`).** Rust's standard library
offers `thread::scope`, which takes a closure receiving a `Scope` handle.
`scope.spawn` starts an OS thread whose lifetime, and whose captured borrowed
references, cannot outlive the enclosing `scope` call, enforced at compile
time by the borrow checker rather than only at runtime. this is the one
mainstream implementation where structured concurrency's core guarantee, a
child cannot outlive its scope, is a static property rather than a runtime
one.

## 9. Known production uses

**Trio, the Python async library that originated the nursery API.** Trio is
used as the concurrency backbone of several production Python I/O libraries,
including the `httpcore`/`httpx` HTTP client stack's Trio backend and the
`anyio` compatibility layer that lets asyncio-based frameworks opt into
Trio-style structured primitives. Trio's own documentation states its design
goal directly as making it impossible to write a program with a task leak,
which is the structured concurrency guarantee described in dimension 3. Trio
project, "Trio reference," introduction section,
https://trio.readthedocs.io/en/stable/reference-core.html verified
2026-08-02.

**Python standard library, `asyncio.TaskGroup`.** Every Python 3.11 and later
standard library user gets `asyncio.TaskGroup` without a third-party
dependency, and it is the officially recommended replacement for the older,
unstructured `asyncio.gather` and bare `asyncio.create_task` patterns for new
code, precisely because it guarantees child cancellation on failure and
combined error reporting. Python Software Foundation, "asyncio task groups,"
https://docs.python.org/3/library/asyncio-task.html#task-groups verified
2026-08-02.

**Swift Concurrency, `TaskGroup` and `async let`, shipped across the Apple
platform SDK surface since Swift 5.5.** Apple's own frameworks, network
requests via `URLSession`'s async APIs, SwiftUI's `.task` modifier, and
concurrency-aware Core Data fetches, are documented to compose with
structured task groups so that cancelling a SwiftUI view's task cancels every
child spawned within it. Apple, Swift Standard Library documentation,
`TaskGroup`, https://developer.apple.com/documentation/swift/taskgroup
verified 2026-08-02.

**JetBrains Kotlin Coroutines, used across Android app development and
JetBrains' own IDE platform.** `viewModelScope` and `lifecycleScope`, the
structured scopes Android's Jetpack libraries expose to every Android
application, are `CoroutineScope` instances built directly on Kotlin's
structured concurrency primitives, so that a coroutine launched from a
destroyed Android `ViewModel` or `Activity` is cancelled automatically rather
than leaking. JetBrains, Kotlin documentation, "Coroutines basics," section
"Structured concurrency," https://kotlinlang.org/docs/coroutines-basics.html
verified 2026-08-02.

**OpenJDK, `java.util.concurrent.StructuredTaskScope`, finalized in JDK 25
under JEP 505.** The JEP process targets server request-handling code, where
a single incoming request commonly fans out to several downstream calls on
virtual threads, as the primary motivating use case for bringing the pattern
into the Java standard library rather than leaving it to third-party
frameworks. Oracle, Java SE 25 API Specification,
`java.util.concurrent.StructuredTaskScope`,
https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/StructuredTaskScope.html
verified 2026-08-02.

## 10. Consequences

Positive.

- A function that uses structured concurrency internally can be called from
  anywhere with a plain call-and-wait mental model. concurrency becomes an
  invisible implementation detail rather than a caller-visible contract.
- A failure anywhere in the concurrent tree is guaranteed to be observed at
  the enclosing scope, closing the class of bugs where an exception in a
  detached thread or an unread future disappears silently.
- Resource lifetimes become provably bounded. a connection or lock acquired
  for the scope's duration is guaranteed to be released once, at the point
  every child has stopped using it, without manual reference counting.
- Cancellation composes automatically through arbitrarily deep call chains.
  cancelling the outermost scope reaches every descendant without the
  programmer threading a cancellation token through every intermediate call.
- Debugging and tooling improve because the concurrency tree at any instant is
  a well-formed tree rooted at some still-open scope, which task inspectors
  and debuggers, such as Python's `asyncio` task introspection and Java's
  virtual thread dumps, can walk and render meaningfully.

Negative.

- Genuinely independent, long-lived background work does not fit the pattern
  and needs a separate, deliberately unstructured mechanism, which means most
  real systems end up with two concurrency disciplines side by side, and the
  boundary between them must be drawn and defended carefully.
- Waiting for the slowest child before the scope can exit can add latency
  that an unstructured fire-and-forget spawn would have avoided, when the
  caller genuinely did not need to wait for every child's result.
- Cancellation is cooperative in every mainstream implementation. a child
  blocked inside a call the runtime cannot interrupt keeps the scope open past
  the point cancellation was requested, so the guarantee is "we will
  eventually notice and stop asking," not "we can force-stop instantly."
- Migrating an existing codebase built on bare threads, detached goroutines,
  or unstructured futures onto a structured scope is a non-local change that
  touches every call site along the affected call chains, not a drop-in
  library swap.
- In languages where structured concurrency is a convention rather than a
  compiler-enforced guarantee, Go's `errgroup` being the clearest example,
  nothing stops a developer from bypassing the scope with a raw spawn, so the
  discipline depends on code review and convention rather than the type
  system.

## 11. Failure modes and misuse

**The false nursery.** Symptom. A scope object exists in the code, spawn calls
go through it, but the program still leaks tasks under load. Cause. Somewhere
in a called function, a task is spawned with the raw, unstructured primitive,
a bare goroutine, a detached thread, an `asyncio.create_task` outside any
`TaskGroup`, rather than through the scope. Fix. Audit every spawn site
reachable from the scoped code path and route each one through the scope, or
make the raw primitive itself unavailable inside scoped code via a lint rule
or a code-review checklist.

**Blocking cancellation-unaware calls inside a child.** Symptom. A scope hangs
well past the point its cancellation was triggered, sometimes indefinitely.
Cause. A child task performs a call that does not check the runtime's
cancellation signal, a synchronous file read, an uninstrumented native
library call, a blocking socket operation with no timeout, so cancellation
requests it but cannot make it stop. Fix. Wrap the blocking call with an
explicit timeout, move it to a boundary that can be interrupted at the OS
level, or document that this particular child cannot be cancelled and budget
for that in the scope's overall timeout.

**Swallowed sibling errors.** Symptom. Two children fail, but only one error
ever reaches the log or the caller, and the second failure's cause is
invisible during an incident. Cause. Using an older or hand-rolled join
mechanism that surfaces only the first exception it sees, rather than an
exception-group-aware implementation. Fix. Use a scope implementation that
aggregates every failure, `asyncio.TaskGroup`, Trio's nursery, or Java's
`StructuredTaskScope` with an appropriate `Joiner`, and log or handle the
full group rather than only its first member.

**Resource released too early because of a manual timeout wrapper.** Symptom.
A connection or buffer is closed while a child that was supposed to be scoped
to it is still using it, producing a use-after-close error under load. Cause.
A developer added a manual timeout wrapper around only part of the scoped
block, so the resource's cleanup code outside the scope runs before every
child that touches the resource has actually stopped. Fix. Put the timeout on
the scope itself, or on the individual child's spawn, rather than wrapping an
arbitrary subset of the scoped code with an external timeout that is not
scope-aware.

**Deadlock from spawning into a scope from a wrong thread or wrong task.**
Symptom. A hang with no progress, or in Java's `StructuredTaskScope`, an
explicit `WrongThreadException` at runtime. Cause. Code outside the scope's
owner, a callback fired on a different thread, another coroutine that was
handed the scope object, attempts to fork or join it, violating the
single-owner rule the pattern depends on for its correctness proof. Fix. Pass
data into the scope's owner rather than passing the scope object out, and in
runtimes that enforce ownership at runtime, treat the resulting exception as a
design signal rather than something to catch and ignore.

**Unbounded fan-out inside a scope.** Symptom. A scope that fans out one child
per element of an externally controlled, unbounded list, an
attacker-controlled request body or a paginated result set with no cap,
spawns thousands of children and exhausts memory or file descriptors before
any of them fail. Cause. The scope bounds lifetime and error propagation, not
concurrency width. nothing about structured concurrency itself limits how
many children a single spawn loop creates. Fix. Bound the fan-out explicitly
with a semaphore, a chunked batch size, or a concurrency-limited task-group
variant, treating this as a resource-exhaustion concern layered on top of the
pattern, discussed further in dimension 17.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Structured concurrency (nursery/scope) | Bare thread or goroutine spawn | Future/Promise handed off freely | Thread pool with submit-and-forget | Actor model |
|---|---|---|---|---|---|
| Caller composability | High. concurrency invisible outside the function | Low. caller has no handle on spawned work | Medium. caller has a handle, but nothing forces awaiting it | Low. submitted work has no return path unless the caller keeps the future | Medium. an actor's mailbox is a boundary, but actors are long-lived, not scope-bound |
| Error visibility | High. guaranteed surfaced at scope exit, often as a group | Low. an unhandled exception on a detached thread commonly crashes the process silently or is lost | Medium. surfaces only if someone awaits the future | Low. an exception inside a pooled task is usually swallowed unless explicitly logged | Medium. failure is visible to a supervisor, if one is wired up |
| Cancellation propagation | High. automatic through the whole child tree | None by default | None by default. must be built by hand with a cancellation token | None by default | Medium. requires an explicit supervision strategy |
| Resource lifetime clarity | High. bounded by the scope | Low. resource lifetime must be reasoned about manually | Low. depends on who ends up holding the future | Low. pool outlives any single submitted task | Medium. bounded by the actor's own lifecycle, not by any caller's scope |
| Fits long-lived background work | Poor. no natural top-level scope | Good. this is exactly what it is for | Good, if nobody is required to await it | Good. this is its primary purpose | Excellent. this is its primary purpose |
| Migration cost from existing unstructured code | High, non-local | None, it is the status quo | None, it is the status quo | None, it is the status quo | High. requires adopting a supervision hierarchy |
| Suits CPU-bound fan-out and fan-in | Good, and often paired with Fork-Join underneath | Poor without extra coordination code | Poor without extra coordination code | Good, that is the classical use case | Poor. actors coordinate via messages, not shared computation |

Reading of the table. structured concurrency wins decisively wherever the
concurrent work belongs to a single logical operation with a caller that
needs to wait for it. Bare spawns and thread pools win where the work is
genuinely independent of any caller. Actors win where the work is
independent and long-lived and needs its own failure-handling policy over
time. Structured concurrency is frequently implemented on top of a thread
pool, so the two are not always mutually exclusive, the scope decides
lifetime and error semantics while the pool decides how the underlying
threads are actually scheduled.

## 13. Related and incompatible patterns

- **Fork-Join.** A close relative and frequent implementation partner.
  Fork-Join specifies how CPU-bound divide-and-conquer work is split and
  recombined efficiently across cores. structured concurrency specifies the
  lifetime and error-propagation contract around any concurrent spawn,
  CPU-bound or not. A fork-join task pool is commonly the scheduler underneath
  a structured scope's children, see the Fork-Join entry.
- **Future/Promise.** Structured concurrency narrows what a future can be used
  for rather than replacing it. Inside a scope, the value returned by a
  spawned child is usually represented internally as a future, but the scope
  forbids the future from being handed to code outside the scope's lifetime,
  which is exactly the latitude a bare future normally grants and structured
  concurrency deliberately removes.
- **Actor Model.** A complementary alternative for a different lifetime
  shape. actors are designed for entities that live independently of any
  caller and communicate by message over time, which is precisely the shape
  dimension 4 says structured concurrency should not be forced into. A system
  commonly uses structured concurrency inside the handling of a single
  message an actor receives, while the actor itself sits outside any
  enclosing scope.
- **Thread Pool.** Composes underneath. a scope's children are frequently
  executed on threads borrowed from a pool, with the scope adding the
  lifetime and error-propagation discipline the pool alone does not provide.
- **Half-Sync-Half-Async.** Actively in tension. that pattern deliberately
  decouples an asynchronous, event-driven layer from a synchronous processing
  layer via a queue, which by design lets work outlive the request that
  queued it. that decoupling is exactly what structured concurrency's
  scope-bound lifetime forbids. combining the two requires a clear boundary,
  where structured concurrency governs one side of the queue and the queue
  itself is treated as the deliberate unstructured escape hatch.
- **Barrier and Countdown Latch.** Narrower cousins. both are also
  synchronization points that a set of concurrent participants must reach
  before proceeding, but neither one owns the lifetime or error propagation
  of the participants the way a structured scope does. a countdown latch
  tells you when N things happened. a structured scope also guarantees no
  live reference to any of those N things survives past the join.

## 14. Refactoring path in and out

Introducing structured concurrency into code that currently spawns
unstructured work.

1. Find every raw spawn, `go`, `Thread(target=...).start()`,
   `asyncio.create_task` outside a group, reachable from the function under
   refactor, and list what each one's result or failure is currently supposed
   to do.
2. Introduce the scope construct at the outermost point where the caller
   already intends to wait for the result, wrapping the existing spawns
   without changing their bodies yet.
3. Replace each raw spawn with the scope's spawn method, one at a time,
   running the existing tests after each replacement so a behavioural
   regression is caught against a single change rather than the whole batch.
4. Remove any manual counting-based join bookkeeping, a counter, a
   `WaitGroup`, a list of futures polled in a loop, once the scope's own join
   covers the same guarantee, since duplicating both is a source of drift.
5. Push the scope inward one call-frame at a time wherever a called function
   itself spawns further work, so the guarantee holds transitively rather than
   only at the top level, which is the step most refactors stop short of and
   the one that determines whether the false nursery failure mode in
   dimension 11 shows up later.
6. Add or update tests, per dimension 15, that assert no task outlives the
   scope, not merely that the happy path returns the right value.

Removing structured concurrency when it stops earning its place, most
commonly because a piece of work inside a scope turns out to need a lifetime
independent of its caller after all.

1. Identify precisely which child needs the independent lifetime. do not pull
   the whole scope apart for the sake of one child.
2. Extract that one child into its own explicitly unstructured mechanism, a
   supervised background task, a queue-fed worker, or an actor, with its own
   error handling and its own lifecycle owner, rather than letting it quietly
   escape the existing scope.
3. Leave the remaining children inside the original scope, since removing
   structure from work that still fits the pattern trades away the guarantees
   from dimension 3 for no benefit.
4. Document at the extraction boundary, in code, why this one piece of work is
   deliberately unstructured, so a future reader does not undo the extraction
   and reintroduce the problem it solved.

## 15. Testing and verification

Easier because of the pattern.

- A test can call the scoped function and assert, immediately after it
  returns or raises, that no background task from that call is still running,
  because the pattern's own guarantee makes that assertion true by
  construction rather than something the test has to poll for.
- Cancellation behaviour becomes directly testable. a test can cancel the
  parent scope partway through and assert every child observed cancellation,
  rather than needing to simulate a race against an unbounded background
  thread.
- Error-path tests are simpler to write because the failure surfaces at one
  known point, the scope's exit, instead of needing to hook into whichever
  detached mechanism the unstructured version used to report failure.

Harder because of the pattern.

- Testing genuine timing races between siblings, which one fails first when
  both fail close together, requires deterministic scheduling control, most
  runtimes provide a way to step or fake their event loop or scheduler for
  exactly this reason, and a test that relies on real wall-clock races will be
  flaky.
- Verifying the cooperative-cancellation limitation from dimension 10, that a
  child stuck in a non-cancellation-aware call does not actually stop, needs a
  deliberately slow or blocking fake in the test, not only a fast happy-path
  stub.

Techniques that apply.

- **Leak-detection setup.** Run the scoped function under a runtime's task
  or thread introspection, Python's `asyncio` debug mode listing pending
  tasks, Java's virtual thread dump, or a language-level fake clock, and
  assert the set of live tasks is empty after the call returns.
- **Fault injection at a chosen child.** Use a test double for one specific
  child that raises on demand, and assert that the siblings observed
  cancellation and that the resulting exception group contains exactly the
  expected failure, exercising the aggregation policy from dimension 5
  directly rather than only the happy path.
- **Fake clock for timeout and cancellation propagation.** Advance a
  controlled clock instead of sleeping in real time to assert a scope-level
  timeout actually reaches every child, keeping the test both fast and
  deterministic.
- **Ownership-violation test, where the runtime enforces it.** In Java, a test
  that deliberately calls `fork` or `join` from a thread other than the
  scope's owner and asserts `WrongThreadException` is thrown documents the
  single-owner invariant as an executable contract rather than only a
  paragraph in a doc comment.

## 16. Observability signals

What to record.

- A counter or gauge of currently-open scopes, and a separate gauge of
  currently-live children across all open scopes, so a leak, a scope that
  never closes, or a child count that only grows shows up on a dashboard
  before it becomes an outage.
- A histogram of scope duration, since the scope's own exit time is bounded
  by its slowest child, a growing tail on this histogram is a direct signal
  that one particular kind of child is degrading.
- A counter of scope exits by outcome, all children succeeded, at least one
  child failed and triggered a cancellation of siblings, and the scope itself
  was cancelled from outside, so the failure mode can be distinguished from
  the dashboard without reading logs.
- For runtimes that make it available, a periodic dump of the live task tree,
  which task spawned which, useful specifically for diagnosing the false
  nursery failure mode from dimension 11 in a running system rather than only
  in code review.
- A per-child duration metric labelled by the logical name of the work, a
  downstream service being called, a computation kind, so a slow one child
  among several can be identified without correlating raw task identifiers by
  hand.

A healthy instance on a dashboard. Live-child count tracks closely with
in-flight request count, rising and falling together with no persistent
baseline drift. Scope duration is flat, close to the expected slowest child
under normal load. The failed-and-cancelled outcome counter is low and
proportional to genuine downstream error rates.

A failing instance. The live-child gauge climbs and never returns to
baseline, which is the leak signature and points directly at an unstructured
spawn escaping a scope somewhere in the call graph, the false nursery failure
mode. Scope duration develops a long tail with no matching rise in any
individual child's own duration metric, which points at cancellation not
actually stopping a blocked child promptly, the cooperative-cancellation
limitation. A sudden spike in scopes exiting via cancellation with no
matching rise in a specific downstream's error rate suggests the trigger is
upstream of the scope itself, commonly a timeout set too aggressively.

## 17. Security and privacy implications

Structured concurrency is not primarily a security pattern, but it changes
two attack surfaces enough to be worth stating plainly, and it is silent on
everything else. inventing a broader security story here would not be
honest.

**Resource-exhaustion denial of service through unbounded fan-out.** As noted
in dimension 11, the pattern bounds lifetime and error propagation, it does
not bound the number of children a single spawn loop creates. Code that spawns
one child per element of an attacker-influenced list, one request field per
downstream call with no upper limit, one child per line of an uploaded file,
turns the scope into an amplifier. A caller who can make the list long can
make the process open thousands of sockets, threads, or connections in one
scope. The fix is to cap fan-out explicitly with a bounded concurrency
construct, a semaphore or a fixed-size worker pool feeding into the scope,
treating the cap as a required companion to the pattern whenever the fan-out
count is derived from untrusted input.

**Better failure containment reduces one class of information leakage.**
Because every failure inside a scope surfaces at a single, known point rather
than on a detached thread whose error handler may or may not exist, it
becomes easier to guarantee that a single, sanitized error response is
returned to a caller instead of accidentally leaking a raw stack trace or an
internal exception message from whichever unrelated code path happened to
have logging wired up. this is a byproduct of the pattern's error-aggregation
discipline rather than a feature designed for it, and it does not by itself
sanitize anything. the aggregated exception group must still be inspected and
translated deliberately before it reaches an external caller.

**Cancellation is not a security boundary.** Because cancellation in every
mainstream implementation is cooperative, a malicious or buggy child that
ignores cancellation checks, deliberately or through a blocking call the
runtime cannot interrupt, can continue consuming resources, holding a lock, or
completing a side effect after the scope has requested it stop. structured
concurrency should never be relied on as the sole mechanism to guarantee a
sensitive operation, a write, a charge, a privileged call, actually halts on
cancellation. that guarantee, where required, needs its own explicit
compensating check or timeout at the operation itself.

On privacy the pattern is neutral. it changes where and how an error surfaces,
not what data flows through the children. any data a child task handles
carries the same sensitivity it would under any other concurrency mechanism,
and the observability advice in dimension 16 to log per-child duration and
outcome should avoid including payload contents in those labels for the same
reason any other structured log field should.

## Code examples

Four languages, chosen because each represents a materially different shape
of the same guarantee. Python shows the standard-library `asyncio.TaskGroup`,
the closest thing to a canonical modern reference implementation. Swift shows
`withThrowingTaskGroup`, the compiler-integrated form. Go shows `errgroup`,
the library-convention form built on an otherwise unstructured primitive,
included specifically to contrast with the other three. Kotlin is described
in dimension 8 with a citation rather than run here, because a runnable
Kotlin sample needs the Kotlin compiler, `kotlinc`, which was not available in
this environment, and a snippet that was not actually compiled is not
presented as though it was.

### Python

```python
import asyncio


class DownstreamError(Exception):
    def __init__(self, name: str):
        super().__init__(f"downstream {name} failed")
        self.name = name


async def fetch(name: str, delay: float, fail: bool) -> str:
    await asyncio.sleep(delay)
    if fail:
        raise DownstreamError(name)
    return f"{name}:ok"


async def gather_profile() -> dict[str, str]:
    results: dict[str, str] = {}

    async def run(name: str, delay: float, fail: bool) -> None:
        results[name] = await fetch(name, delay, fail)

    async with asyncio.TaskGroup() as tg:
        tg.create_task(run("account", 0.01, False))
        tg.create_task(run("billing", 0.02, False))
        tg.create_task(run("preferences", 0.01, False))

    return results


async def gather_profile_with_failure() -> None:
    async def run(name: str, delay: float, fail: bool) -> None:
        await fetch(name, delay, fail)

    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(run("account", 0.05, False))
            tg.create_task(run("billing", 0.01, True))
    except* DownstreamError as eg:
        for exc in eg.exceptions:
            print("failed:", exc)


async def main() -> None:
    print(await gather_profile())
    await gather_profile_with_failure()


if __name__ == "__main__":
    asyncio.run(main())
```

### Swift

```swift
import Foundation

struct DownstreamError: Error {
    let name: String
}

func fetch(_ name: String, delaySeconds: Double, fail: Bool) async throws -> String {
    try await Task.sleep(nanoseconds: UInt64(delaySeconds * 1_000_000_000))
    if fail {
        throw DownstreamError(name: name)
    }
    return "\(name):ok"
}

func gatherProfile() async throws -> [String: String] {
    try await withThrowingTaskGroup(of: (String, String).self) { group in
        group.addTask { ("account", try await fetch("account", delaySeconds: 0.01, fail: false)) }
        group.addTask { ("billing", try await fetch("billing", delaySeconds: 0.02, fail: false)) }
        group.addTask { ("preferences", try await fetch("preferences", delaySeconds: 0.01, fail: false)) }

        var results: [String: String] = [:]
        for try await (name, value) in group {
            results[name] = value
        }
        return results
    }
}

func gatherProfileWithFailure() async {
    do {
        try await withThrowingTaskGroup(of: String.self) { group in
            group.addTask { try await fetch("account", delaySeconds: 0.05, fail: false) }
            group.addTask { try await fetch("billing", delaySeconds: 0.01, fail: true) }
            for try await value in group {
                print("got:", value)
            }
        }
    } catch {
        print("scope failed:", error)
    }
}

@main
struct Demo {
    static func main() async throws {
        let profile = try await gatherProfile()
        print(profile)
        await gatherProfileWithFailure()
    }
}
```

### Go

The sample below reproduces the `errgroup.Group` shape from dimension 8 with
standard-library-only code, `sync.WaitGroup`, a mutex, and `context`, rather
than importing `golang.org/x/sync/errgroup`, so it compiles as a single file
with `go vet` and needs no module resolution. Dimension 8 and dimension 9
describe the real, widely used `golang.org/x/sync/errgroup` package, this
sample only reimplements its narrow shape to keep the example self-contained.

```go
package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"
)

// group is a minimal, standard-library-only stand-in for errgroup.Group,
// built here only so the sample compiles without an external module.
type group struct {
	wg     sync.WaitGroup
	mu     sync.Mutex
	err    error
	cancel context.CancelFunc
}

func withGroup(ctx context.Context) (*group, context.Context) {
	gctx, cancel := context.WithCancel(ctx)
	return &group{cancel: cancel}, gctx
}

func (g *group) run(f func() error) {
	g.wg.Add(1)
	go func() {
		defer g.wg.Done()
		if err := f(); err != nil {
			g.mu.Lock()
			if g.err == nil {
				g.err = err
				g.cancel()
			}
			g.mu.Unlock()
		}
	}()
}

func (g *group) wait() error {
	g.wg.Wait()
	g.cancel()
	return g.err
}

func fetch(ctx context.Context, name string, delay time.Duration, fail bool) (string, error) {
	select {
	case <-time.After(delay):
	case <-ctx.Done():
		return "", ctx.Err()
	}
	if fail {
		return "", fmt.Errorf("downstream %s failed", name)
	}
	return name + ":ok", nil
}

func gatherProfile(ctx context.Context) (map[string]string, error) {
	g, gctx := withGroup(ctx)
	results := make(map[string]string)
	names := map[string]time.Duration{
		"account":     10 * time.Millisecond,
		"billing":     20 * time.Millisecond,
		"preferences": 10 * time.Millisecond,
	}

	type pair struct {
		name  string
		value string
	}
	out := make(chan pair, len(names))

	for name, delay := range names {
		name, delay := name, delay
		g.run(func() error {
			v, err := fetch(gctx, name, delay, false)
			if err != nil {
				return err
			}
			out <- pair{name, v}
			return nil
		})
	}

	if err := g.wait(); err != nil {
		return nil, err
	}
	close(out)
	for p := range out {
		results[p.name] = p.value
	}
	return results, nil
}

func gatherProfileWithFailure(ctx context.Context) error {
	g, gctx := withGroup(ctx)
	g.run(func() error {
		_, err := fetch(gctx, "account", 50*time.Millisecond, false)
		return err
	})
	g.run(func() error {
		_, err := fetch(gctx, "billing", 10*time.Millisecond, true)
		return err
	})
	return g.wait()
}

func main() {
	ctx := context.Background()
	profile, err := gatherProfile(ctx)
	if err != nil {
		fmt.Println("error:", err)
	} else {
		fmt.Println(profile)
	}

	if err := gatherProfileWithFailure(ctx); err != nil {
		fmt.Println("scope failed:", errors.Unwrap(err))
	}
}
```

The hand-rolled `group` type mirrors dimension 8's description of the real
`errgroup.Group`, cancellation-on-first-error and a single joined `wait()`,
but nothing in the type system stops a developer from writing a bare
`go func() { ... }()` inside the same function instead of `g.run(...)`, which
would compile cleanly and silently escape the group's guarantee. the real
`golang.org/x/sync/errgroup` package has the same property, cited with its
actual API in dimension 8 and dimension 9.

## 18. References

1. Nathaniel J. Smith. "Notes on structured concurrency, or. go statement
   considered harmful." vorpus.org, 2018.
   https://vorpus.org/blog/notes-on-structured-concurrency-or-go-statement-considered-harmful/
   Verified 2026-08-02. Source of the go-statement analogy and the nursery
   terminology's popularization in dimension 1 and dimension 2.
2. Trio project. "Trio reference," sections on nurseries, `open_nursery`, and
   `start_soon`. https://trio.readthedocs.io/en/stable/reference-core.html
   Verified 2026-08-02. Source for the nursery implementation variant in
   dimension 8 and the production-use citation in dimension 9.
3. Python Software Foundation. "asyncio task groups," `asyncio.TaskGroup`.
   https://docs.python.org/3/library/asyncio-task.html#task-groups
   Verified 2026-08-02. Source for the Python 3.11 `TaskGroup` behaviour,
   exception-group aggregation, and the cancellation-on-first-failure policy
   in dimension 8 and dimension 9.
4. Apple. Swift Standard Library documentation, `TaskGroup`.
   https://developer.apple.com/documentation/swift/taskgroup
   Verified 2026-08-02. Source for the Swift Concurrency implementation
   variant in dimension 8 and the production-use citation in dimension 9.
5. Oracle. Java SE 25 API Specification,
   `java.util.concurrent.StructuredTaskScope`.
   https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/StructuredTaskScope.html
   Verified 2026-08-02. Source for the JEP 505 `StructuredTaskScope` shape,
   the owner-thread enforcement, and the `Joiner` policies in dimension 8,
   dimension 9, and dimension 11.
6. Go project. `golang.org/x/sync/errgroup` package documentation.
   https://pkg.go.dev/golang.org/x/sync/errgroup
   Verified 2026-08-02. Source for the `errgroup.Group`, `WithContext`, `Go`,
   and `Wait` behaviour in dimension 8 and the Go code sample.
7. JetBrains. Kotlin documentation, "Coroutines basics," section "Structured
   concurrency." https://kotlinlang.org/docs/coroutines-basics.html
   Verified 2026-08-02. Source for the `coroutineScope` implementation
   variant in dimension 8, the attribution of the Kotlin design to Roman
   Elizarov in dimension 1, and the production-use citation in dimension 9.
8. Wikipedia contributors. "Structured concurrency."
   https://en.wikipedia.org/wiki/Structured_concurrency
   Verified 2026-08-02. Used only to corroborate the historical attribution
   of the term to Martin Sustrik's 2016 libdill design notes in dimension 1,
   not as a source of technical explanation.
