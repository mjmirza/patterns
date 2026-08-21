---
name: Continuation
slug: continuation
family: 16-functional
category: Functional
aliases: [CPS, Callback Continuation, Escape Continuation, Delimited Continuation]
first_described: "Reynolds 1972"
maturity: canonical
related: [tail-call-optimization, trampolining, monad, callback, coroutine, chain-of-responsibility]
incompatible_with: [hidden-control-flow, double-callback, unbounded-continuation-retention, ambient-mutable-state]
verified: 2026-08-02
---

# Continuation

## 1. Name, aliases, and lineage

The canonical name is Continuation. In programming language work, a
continuation is the rest of a computation represented as a value. In ordinary
direct style, a function returns to its caller. In continuation style, the
function receives a representation of what should happen after its result exists
and calls that representation instead of returning in the normal way.

The main aliases are **continuation-passing style**, **CPS**, **callback
continuation**, **escape continuation**, and **delimited continuation**.
Continuation-passing style is the transformed program shape where every
function receives its future as an explicit function argument. Callback
continuation is the common application-level form in JavaScript, Go, Python, and
web middleware. Escape continuation is the Scheme form that abandons the current
future and resumes an earlier one. Delimited continuation is the bounded form
that captures only part of the future, rather than the whole remainder of the
program.

The usual software lineage point is John C. Reynolds, "Definitional
Interpreters for Higher-Order Programming Languages", ACM Annual Conference
1972, pages 717-740, DOI 10.1145/800194.805852. DBLP records the paper title,
author, venue, year, page range, and DOI
(https://dblp.dagstuhl.de/rec/conf/acm/Reynolds72.html, verified
2026-08-02). Reynolds' paper is a lineage source for interpreters that make the
control continuation explicit. Andrew W. Appel later made CPS a compiler
engineering topic in *Compiling with Continuations*, Cambridge University Press,
1992. Cambridge University Press describes the book as showing CPS as an
intermediate representation for optimization and program transformation in a
compiler for Standard ML
(https://www.cambridge.org/core/books/compiling-with-continuations/7CA9C36DCE78AD82218E745F43A4E740,
verified 2026-08-02).

Scheme made continuations visible to programmers. R6RS specifies
`call-with-current-continuation`, also called `call/cc`, as a procedure that
packages the current continuation as an escape procedure and passes it to a
procedure supplied by the caller
(https://r6rs.org/final/html/r6rs/r6rs-Z-H-14.html, verified 2026-08-02).
R7RS records that `call-with-current-continuation` can reenter a dynamic extent
after the original procedure call has returned
(https://standards.scheme.org/corrected-r7rs/r7rs-Z-H-6.html, verified
2026-08-02).

Kotlin exposes the same idea through coroutines. The Kotlin language
specification states that every suspending function is associated with a
generated `Continuation` subtype and that the function is adapted to accept an
extra continuation parameter to support continuation-passing style
(https://kotlinlang.org/spec/asynchronous-programming-with-coroutines.html,
verified 2026-08-02). The Kotlin standard library API defines
`kotlin.coroutines.Continuation<T>` as an interface representing a continuation
after a suspension point that returns a value of type `T`
(https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.coroutines/-continuation/,
verified 2026-08-02).

Engineering judgement. This catalog treats Continuation as broader than a
callback. A callback is any function passed to be called later. A continuation is
a callback that represents the next step of a computation and controls whether,
when, and with what value that computation proceeds.

## 2. Problem and context

A computation cannot finish by returning to its immediate caller, because the
rest of the work must be selected, stored, resumed, aborted, retried, scheduled,
or exposed as a programmable step.

This shows up in ordinary code in several forms. A request pipeline needs each
stage to either end the response or pass control to the next stage. An async API
starts I/O and later needs to resume the suspended caller. A parser wants a clean
way to say what happens after a token is recognized. A search wants to escape
from deep recursion the moment it finds a result. A compiler wants an
intermediate form where control flow, return addresses, exception paths, and
tail calls are explicit values. A web framework wants to suspend an interaction,
send a page to a browser, and later continue from the point where the page was
sent.

Without the pattern, the program uses scattered flags, special return values,
exceptions, shared mutable state, or duplicated branch logic. The code says
"return a value" when the design problem is "what should run next". The
result is brittle around early exit, backtracking, timeout, cancellation,
middleware handoff, and async completion. The continuation pattern moves that
future into a named parameter, object, closure, or generated state machine.

The context matters. Continuations are not a better syntax for every function
call. They earn their place when control transfer itself is the thing under
design. In direct business logic, returning a value is clearer. In control
orchestration, making the future explicit can remove hidden branches and expose
the exact point where execution may proceed, stop, or be resumed.

## 3. Forces

Engineering judgement. The forces below are design pressures observed when
continuations are used in libraries, compilers, middleware, and async runtimes.

- **Control clarity.** Favoured when the code truly needs to manipulate the
  next step. The future is a value with a name and a contract.
- **Local readability.** Sacrificed. Direct style reads in source order.
  Continuation style often reads inside out, with the "after" path declared
  before the work that leads to it.
- **Latency.** Mixed. A continuation can avoid stack growth and support
  cooperative scheduling. It can also add closure allocation, dispatch hops, and
  scheduler overhead.
- **Coupling.** Favoured at the call boundary because the callee no longer knows
  its caller. Sacrificed when the continuation closes over large caller state or
  assumes one scheduler.
- **Consistency.** Mixed. A single continuation path can centralize cleanup and
  completion. A continuation called twice can produce duplicate effects.
- **Operability.** Sacrificed unless telemetry records the continuation id,
  state, and resume path. Stack traces are less direct after transformation.
- **Cost.** Favoured when the pattern replaces duplicated branch logic or stack
  frames. Sacrificed when it makes routine code harder for a team to maintain.
- **Team topology.** Favoured for framework teams that publish an extension
  point such as `next`, `doFilter`, or `resumeWith`. Sacrificed if product teams
  must reason about scheduler internals to write simple handlers.
- **Cognitive load.** High. A reader must track who owns the continuation, when
  it may be called, whether it may be called more than once, and what state it
  retains.

The pattern favours explicit control transfer over direct local reading. That is
the trade. If control transfer is not the hard part, the pattern is usually too
heavy.

Another practical force is **ownership of time**. Direct return gives time back
to the caller immediately. A stored continuation lets another owner decide when
the computation may proceed. That owner may be an event loop, browser request,
message broker, scheduler, test driver, or plugin. This is useful when progress
depends on the outside world. It is expensive when the original caller assumed
that all state would be gone after the call returned. A continuation carries a
piece of time with it, and the owner of that piece must be named in the API.

There is also a force around **semantic distance**. In a compiler or
interpreter, CPS can reduce semantic distance because return addresses,
exception exits, and join points become ordinary values in the intermediate
language. In product code, the same transformation can increase semantic
distance because a reader must reconstruct the source-level story from nested
functions. The same pattern can therefore clarify one layer and confuse another.
That is why continuations work best at boundaries: runtime internals, framework
handoff points, parser drivers, and async adapters. Inside domain code, a
smaller abstraction often reads better.

## 4. Applicability and non-applicability

Reach for Continuation when the following hold.

- A callee must decide whether to continue, abort, retry, branch, or suspend the
  caller's future.
- The next step must be stored and resumed later, such as after I/O, a timer, a
  user action, or cooperative scheduling.
- A framework must let application code run before or after the rest of a
  pipeline while the framework keeps ownership of the chain.
- A compiler, interpreter, parser, or evaluator benefits from representing
  control flow as data.
- Deep recursion needs early exit or backtracking without unwinding through
  every frame by hand.
- An API needs a testable boundary for success, failure, cancellation, and
  timeout paths.
- Tail calls or trampolines are being used to run a recursive process without
  growing the native stack.

Do NOT reach for Continuation in these cases, and the reason matters.

- **The function has one normal next step.** Return a value. A continuation
  parameter hides a simple call path.
- **The team is already struggling with callback nesting.** Add `async` and
  `await`, promises, futures, tasks, or a structured effect type. More callbacks
  will deepen the problem.
- **The continuation closes over large mutable state.** A stored continuation
  can retain the whole object graph reachable from that state.
- **The caller expects exactly-once completion but the API cannot enforce it.**
  A plain callback can be called zero, one, or many times unless wrapped.
- **The control transfer crosses trust boundaries.** Passing the next step to
  untrusted plugin code gives that code the power to skip, repeat, or delay the
  rest of the operation.
- **The goal is ordinary error handling.** Use `Result`, `Either`, exceptions,
  or a typed error channel. Continuations can model errors, but they are too
  broad for a routine failure result.
- **The runtime has no stable suspension model.** Capturing stackful
  continuations in an environment that was not built for them can conflict with
  resource lifetime, stack inspection, debuggers, and native frames.
- **The continuation would be invoked across thread or event-loop ownership
  without a documented handoff rule.** The bug will appear as races or blocked
  event loops, not as a type error.

## 5. Structure

The participants are named by role.

- **Current computation.** The code that reaches a point where the rest of the
  work must be made explicit. In CPS this is a function body. In middleware this
  is the current handler. In a coroutine this is generated state-machine code.
- **Continuation value.** A function, object, or generated frame representing
  the rest of the computation. It accepts the result needed by the next step, or
  an error channel when the API has one.
- **Continuation invoker.** The code that calls the continuation. It may be the
  current computation, an event loop, a scheduler, a parser driver, or a web
  container.
- **Captured environment.** The variables retained by the continuation. This is
  where the pattern gains power and where memory leaks start.
- **Final continuation.** The outer boundary that converts continuation style
  back to a visible result, response, log event, process exit, or resolved task.
- **Abort or escape path.** An optional continuation that bypasses the normal
  next step. Scheme `call/cc`, Haskell `callCC`, and many validation pipelines
  expose this form.

Relationships. The current computation receives the continuation value instead
of assuming the native return address. It may call that continuation now, store
it, wrap it, replace it, or call a different one. The captured environment lives
as long as the continuation is reachable. The final continuation is the point
where ordinary code can observe the result.

## 6. ASCII structure diagram

```text
        +----------------------+      calls or stores
        | Current Computation  |-------------------------------+
        |----------------------|                               |
        | input values         |                               v
        | continuation: K      |                    +----------------------+
        +----------------------+                    | Continuation Value   |
                  |                                |----------------------|
                  | closes over                    | function or object   |
                  v                                | next(result)         |
        +----------------------+                    +----------------------+
        | Captured Environment |                               |
        |----------------------|                               | resumes
        | locals, request,     |                               v
        | parser state, frame  |                    +----------------------+
        +----------------------+                    | Next Computation     |
                                                     |----------------------|
                                                     | normal or escape     |
                                                     +----------------------+
                                                               |
                                                               v
                                                     +----------------------+
                                                     | Final Continuation   |
                                                     |----------------------|
                                                     | response, result,    |
                                                     | effect, or exit      |
                                                     +----------------------+
```

## 7. Dynamics

The main runtime move is inversion of return. The callee does not hand a value
back through the native stack. It hands the value to a continuation selected by
the caller, the framework, or a compiler transformation.

```text
Client        Current Computation       Continuation K       Final Boundary
  |                    |                       |                    |
  |-- start(input, K)->|                       |                    |
  |                    |                       |                    |
  |                    |-- compute partial --->|                    |
  |                    |                       |                    |
  |                    |-- K(value) ---------->|                    |
  |                    |                       |-- next step ------>|
  |                    |                       |                    |
  |                    |                       |<-- result/effect --|
  |                    |<-- optional return ---|                    |
  |<-- boundary result-|                       |                    |
  |                    |                       |                    |
```

An escape path changes the flow.

```text
Search frame 1     Search frame 2     Search frame 3     Escape K
     |                  |                  |                 |
     |-- descend ------>|                  |                 |
     |                  |-- descend ------>|                 |
     |                  |                  |-- found ------->|
     |                  |                  |                 |
     |<---------------- abort all remaining recursive work --|
     |                  |                  |                 |
```

When the continuation is stored, the return point outlives the call that created
it. That is the form used by many coroutine and web interaction systems. Kotlin
documents that suspend functions are transformed to accept a continuation
parameter, and Racket's web server documents that `send/suspend` captures the
current continuation, binds it to a URL, and later invokes it when the URL is
requested
(https://kotlinlang.org/spec/asynchronous-programming-with-coroutines.html,
verified 2026-08-02;
https://download.racket-lang.org/docs/5.0.2/html/web-server/servlet.html,
verified 2026-08-02).

## 8. Implementation variants

**Manual continuation-passing style.** Each function takes a continuation
argument and calls it with its result. This is precise and portable. The cost is
inside-out code and more closures.

**Callback continuation.** The continuation is a callback such as `done`,
`next`, `resume`, or `reply`. This is common in web frameworks and event loops.
It is easy to adopt and easy to misuse because the type often cannot express
exactly-once invocation.

**Generated coroutine continuation.** The source code stays in direct style, but
the compiler rewrites suspend points into a continuation object or state machine.
Kotlin specifies this shape for suspending functions
(https://kotlinlang.org/spec/asynchronous-programming-with-coroutines.html,
verified 2026-08-02). The cost moves to tooling, debugging, and scheduler rules.

**Escape continuation.** The continuation is captured and later invoked to
abandon the current path. R6RS describes `call/cc` as packaging the current
continuation as an escape procedure
(https://r6rs.org/final/html/r6rs/r6rs-Z-H-14.html, verified 2026-08-02).
This is powerful for early exit and backtracking. It is dangerous around locks,
transactions, and cleanup unless dynamic extent rules are clear.

**Delimited continuation.** Only a bounded section of the future is captured.
This avoids some of the scale and lifetime risk of whole-program continuations.
It is harder to explain and usually appears in language runtimes or advanced
effect systems rather than application code.

**Continuation monad.** The continuation is represented as a type such as
`Cont r a`, commonly read as a CPS computation that will produce an `a` inside a
larger result `r`. Hackage's `mtl` documentation for `Control.Monad.Cont`
describes `Cont` and `ContT` as the continuation monad and monad transformer
(https://hackage.haskell.org/package/mtl/docs/Control-Monad-Cont.html,
verified 2026-08-02). This form composes with monadic code but can become hard
to read.

**Trampoline continuation.** A function returns the next continuation step as
data rather than calling it on the native stack. A loop repeatedly runs the next
step. This is the functional route to stack safety in runtimes without proper
tail calls.

**Middleware continuation.** A framework passes a `next` object or function to
each handler. The handler may stop or pass control onward. Express documents
`next` as the next middleware function in the request-response cycle, and
Jakarta Servlet documents `FilterChain.doFilter` as invoking the next filter or
the resource at the end of the chain
(https://expressjs.com/en/guide/using-middleware/, verified 2026-08-02;
https://jakarta.ee/specifications/servlet/6.2/apidocs/jakarta.servlet/jakarta/servlet/filterchain,
verified 2026-08-02).

**Success and failure continuations.** The callee receives two futures, one for
normal completion and one for failure. This is sometimes called double-barrelled
CPS in compiler literature, but in application code it appears as `resolve` and
`reject`, `ok` and `err`, or `success` and `failure`. The appeal is explicit
control over both exits. The cost is contract drift. If one branch calls the
normal continuation and later discovers an error, the failure continuation may
still be reachable unless the pair is wrapped as one stateful completion object.

**Continuation object.** Instead of passing a raw function, the API passes an
object with methods such as `resume`, `fail`, `cancel`, and `context`. Kotlin's
`Continuation<T>` is this kind of public surface
(https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.coroutines/-continuation/,
verified 2026-08-02). An object can carry scheduler context, trace ids, and
guards. It is heavier than a function but often safer for public APIs because
future versions can add methods or wrap behavior.

**Defunctionalized continuation.** The continuation is represented as a tagged
data structure plus an interpreter loop rather than as a closure. Compilers and
interpreters use this when they want to inspect, serialize, optimize, or switch
over control states. The gain is visibility. The cost is that adding a new state
means editing the dispatcher, so the style trades function extensibility for
data inspection.

## 9. Known production uses

**Kotlin coroutines, `kotlin.coroutines.Continuation`.** Kotlin's standard
library defines the `Continuation<T>` interface with `context` and `resumeWith`.
The language specification says every suspending function is associated with a
generated continuation subtype and is adapted to accept an extra continuation
parameter for CPS
(https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.coroutines/-continuation/,
verified 2026-08-02;
https://kotlinlang.org/spec/asynchronous-programming-with-coroutines.html,
verified 2026-08-02).

**Express middleware, `next`.** Express describes an application as a series of
middleware function calls during the request-response cycle. Middleware receives
`req`, `res`, and the next middleware function, commonly named `next`; if a
middleware function does not end the cycle, it must call `next()` or the request
is left hanging
(https://expressjs.com/en/guide/using-middleware/, verified 2026-08-02).

**Jakarta Servlet filters, `FilterChain.doFilter`.** The Servlet API defines
`FilterChain` as the object a container provides so a filter can invoke the next
filter in the chain, or the target resource when the filter is last
(https://jakarta.ee/specifications/servlet/6.2/apidocs/jakarta.servlet/jakarta/servlet/filterchain,
verified 2026-08-02).

**Racket web server, `send/suspend` and `send/suspend/dispatch`.** Racket's web
server documentation says `send/suspend` captures the current continuation,
stores it with an expiration handler, binds it to a URL, and later invokes it
when that URL is used. The Racket tutorial for web applications explains
`send/suspend/dispatch` as creating special URLs that restart an application
from an associated handler rather than from `start`
(https://download.racket-lang.org/docs/5.0.2/html/web-server/servlet.html,
verified 2026-08-02;
https://docs.racket-lang.org/continue/, verified 2026-08-02).

**Standard ML of New Jersey compiler.** Appel's *Compiling with Continuations*
uses a compiler for Standard ML as the worked implementation context. Cambridge
University Press describes the book as applying CPS as an intermediate
representation for optimization and transformation in a compiler for Standard ML
(https://www.cambridge.org/core/books/compiling-with-continuations/7CA9C36DCE78AD82218E745F43A4E740,
verified 2026-08-02).

These uses are intentionally varied. Kotlin hides most continuation machinery
behind source-level suspend functions. Express makes the continuation a small
callback that application authors call by hand. Jakarta Servlet wraps the next
step as a chain object. Racket exposes captured web continuations as interaction
state. SML/NJ uses CPS below the source language as compiler representation.
Together they show that the pattern is not one syntax. It is the design move of
reifying the future, then deciding who owns it.

## 10. Consequences

Engineering judgement. The lists below describe design effects, not universal
facts.

Positive.

- The next step becomes an explicit parameter, object, or generated frame.
- Early exit, retry, backtracking, and suspension can be represented without
  scattering flags through every call.
- A framework can give user code a precise handoff point while retaining
  ownership of the outer algorithm.
- Stack-safe recursion becomes possible when continuations are paired with a
  trampoline or a runtime with proper tail calls.
- Async completion and cancellation can be made visible in one contract rather
  than hidden behind shared state.
- Compilers and interpreters gain an intermediate form where control flow is
  easier to rewrite, analyze, and schedule.

Negative.

- Source order no longer matches runtime order as plainly as direct style.
- A continuation can be called zero times, one time, or many times unless the API
  guards that contract.
- Captured environments can retain requests, buffers, transactions, or security
  principals longer than expected.
- Stack traces and logs can lose the original direct call path.
- Ordinary cleanup mechanisms can be bypassed by escape or reentry paths unless
  the runtime defines dynamic extent rules.
- Exposing the continuation to plugins gives those plugins control over the rest
  of the operation.

## 11. Failure modes and misuse

Engineering judgement. Each item is written as Symptom, Cause, Fix because this
is how the bug appears in production work.

**Double completion.** Symptom. A request sends two responses, a promise settles
once but logs a second completion error, or a payment callback runs twice.
Cause. The continuation is called from both success and error paths, or called
again after a timeout path already fired. Fix. Wrap the continuation in an
exactly-once guard and test both race orders.

**Dropped continuation.** Symptom. A request hangs, a coroutine never resumes, or
a test times out with no error. Cause. A branch returns without calling,
storing, or failing the continuation. Fix. Require every branch to call one of
success, failure, or cancellation; add a watchdog metric for aged pending
continuations.

**Retained environment leak.** Symptom. Heap grows with request count, and heap
snapshots show old requests retained by closures or coroutine frames. Cause. A
stored continuation captures large state. Fix. Capture small immutable values
instead of whole objects, clear references after resume, and expire stored
continuations.

**Out-of-order resume.** Symptom. A UI shows stale data, a pipeline step runs
after a newer request finished, or a coroutine resumes on the wrong event loop.
Cause. The continuation does not carry a generation, cancellation token, or
scheduler rule. Fix. Attach a version and cancellation check to resume, then
dispatch resume onto the owning scheduler.

**Lost cleanup around escape.** Symptom. A lock remains held, a transaction stays
open, or a span never closes after early exit. Cause. An escape continuation
bypasses the direct-style cleanup path. Fix. Put cleanup in a dynamic extent
facility, `defer`, `finally`, or framework-managed scope that runs on both exit
and reentry.

**Callback pyramid.** Symptom. A file contains nested continuation callbacks
where error handling is repeated at every level. Cause. Manual CPS was used for
ordinary sequencing rather than a structured async or effect abstraction. Fix.
Move to `async` and `await`, futures, a monad, or a small pipeline combinator.

**Continuation exposed across trust boundary.** Symptom. A plugin skips audit
middleware, calls the next step twice, or delays completion until resources are
exhausted. Cause. The framework handed raw control over the continuation to
untrusted code. Fix. Pass a constrained wrapper with once-only semantics,
deadline checks, and authorization around the actions that may proceed.

**Wrong final boundary.** Symptom. A low-level helper prints, sends a response,
or exits the process from inside a continuation path, making the same helper
unusable in tests or batch jobs. Cause. The final continuation was placed too
deep in the call graph. Fix. Move printing, response creation, or process exit
to the outer boundary and keep inner continuations typed around values.

**Hidden synchronous call.** Symptom. A caller assumes the continuation will run
later, but it runs before the current function returns and observes half-updated
state. Cause. The API does not say whether resume is synchronous or scheduled.
Fix. Document the timing rule, pick one behavior, and in tests assert whether
the continuation has run before the call returns.

**Continuation after cancellation.** Symptom. A cancelled request still writes to
a response object, or a cancelled operation mutates state after the user has
moved on. Cause. The continuation was stored without checking cancellation at
resume time. Fix. Put the cancellation check inside the continuation wrapper so
every resume path shares the same gate.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Continuation | Direct return | Exception | Promise or Future | Coroutine or async function | Chain of Responsibility |
|---|---|---|---|---|---|---|
| Control clarity | Strong when next step varies | Strong for one path | Strong for failure escape | Strong for async result | Strong in source form | Strong for ordered handlers |
| Local readability | Low to medium | High | Medium | Medium | High | Medium |
| Latency | Closure or scheduler cost | Lowest | Unwind cost on failure | Scheduler cost | Runtime state-machine cost | Handler dispatch cost |
| Coupling | Low at callee boundary | Caller and callee tied by return | Hidden nonlocal edge | Tied to task runtime | Tied to coroutine runtime | Tied to chain contract |
| Consistency | Needs exactly-once rule | Native call discipline | Runtime unwinds once | Usually one settlement | Runtime controls resume | Each handler may stop or pass |
| Operability | Needs ids and resume logs | Native stack is clear | Stack trace on throw | Task tracing needed | Coroutine tracing needed | Middleware tracing needed |
| Cost | High for simple code | Low | Low for rare failure | Medium | Medium | Medium |
| Team topology | Good for framework seams | Good inside one module | Good for language-wide errors | Good for service APIs | Good when platform standard | Good for web platform teams |
| Cognitive load | High | Low | Medium | Medium | Medium | Medium |

Reading of the table. Continuation wins when the next step itself is the design
object. Direct return wins for ordinary functions. Exceptions win for rare
failure escape. Promises and coroutines win when the desired surface is
structured async. Chain of Responsibility wins when the continuation is only
"call the next handler" and no capture or replay is needed.

## 13. Related and incompatible patterns

- **Tail Call Optimization.** Continuation style often turns returns into tail
  calls. A runtime with proper tail calls can execute those paths without native
  stack growth.
- **Trampolining.** A trampoline runs continuation steps in a loop. It is the
  usual escape hatch when the runtime lacks proper tail calls.
- **Monad.** The continuation monad packages CPS as a composable type. It fits
  functional code that already uses bind, but it can obscure control flow for
  teams not fluent in monadic style.
- **Coroutine.** A coroutine is often the user-facing form of a continuation
  state machine. Kotlin documents continuations as the basis of coroutine
  machinery
  (https://kotlinlang.org/spec/asynchronous-programming-with-coroutines.html,
  verified 2026-08-02).
- **Chain of Responsibility.** Middleware `next` is a continuation specialized
  to ordered handlers. If the only operation is "pass to the next handler", the
  chain pattern may be the clearer name.
- **Command.** A continuation can be stored like a command, but command models a
  requested action while continuation models the rest of a computation.
- **Strategy.** Strategy selects an algorithm. Continuation selects or stores
  what happens after the current step.
- **Ambient Mutable State.** This conflicts in practice. Reentering or delaying
  a continuation that depends on ambient state can resume under a different
  user, locale, transaction, or request context.
- **Service Locator.** This conflicts when a continuation reaches into global
  state to decide where to resume. The resume path becomes hidden and hard to
  test.

## 14. Refactoring path in and out

Introducing the pattern into direct-style code.

1. Find the point where a function returns a value that immediately determines
   the next step.
2. Extract that next step into a named function that accepts the returned value.
3. Change the original function to accept that function as a continuation and
   call it instead of returning.
4. Add an error, cancellation, or escape continuation only if the code has a real
   second control path.
5. Wrap the continuation with an exactly-once guard if the API contract requires
   one completion.
6. Add telemetry for continuation creation, resume, cancellation, and age before
   storing continuations across turns.
7. If many functions need the same shape, introduce a small type alias or
   interface. Do not spread raw `(value) -> void` signatures everywhere.

Moving from callbacks to structured async.

1. Wrap the continuation API in a promise, future, task, or coroutine bridge.
2. Preserve cancellation and timeout semantics explicitly.
3. Replace nested callbacks one level at a time with direct-style async calls.
4. Keep the lower-level continuation boundary only at the adapter to the legacy
   API or framework.

Removing the pattern when it stops earning its place.

1. Find continuations that are always called once, synchronously, and with no
   branching.
2. Inline the continuation body after the call site.
3. Change the callee to return the value directly.
4. Delete once-only wrappers and pending-continuation metrics that no longer
   observe any stored state.
5. Run tests that cover success, failure, cancellation, and timeout paths because
   those paths are where semantic drift hides.

Cross reference. Replace Temp with Query, Substitute Algorithm, Extract
Function, Inline Function, and Replace Control Flag with Break or Return are the
refactoring-family moves most often involved before or after this pattern.

Worked path from nested callbacks to a smaller continuation surface. Start with
one nested callback chain and name the domain steps in direct order on paper.
Convert only the lowest async boundary into a promise, future, or callback
adapter. Leave the rest of the domain flow in direct style. If a middle step
needs to branch to an alternate future, name that branch as a continuation and
keep it local to the step. Repeat until the remaining continuations correspond
to real control boundaries rather than incidental library shapes. This avoids
the common failure where a team replaces one callback style with another but
keeps the same tangled control graph.

Worked path from direct recursion to an escape continuation. First write the
recursive function with a normal return and a test that captures the intended
early-exit result. Next add an internal helper that accepts `found` and
`missing` continuations, while the public function still returns a direct value.
Use the `found` continuation only at the point where the search result is known.
Keep cleanup outside the helper until the tests pass. Then add cleanup inside a
scope that runs no matter which continuation fires. This order keeps the public
contract stable while the internal control path changes.

## 15. Testing and verification

Engineering judgement. Continuation code is tested by controlling the future
explicitly.

Easier because of the pattern.

- A test can pass a recording continuation and assert the value, error, and call
  count.
- Early exit can be tested without building the whole caller stack.
- Middleware can be tested by passing a fake `next` that records whether control
  continued.
- Coroutine bridges can be tested by manually resuming a stored continuation.

Harder because of the pattern.

- Native stack traces may not show the logical caller.
- Time matters. A continuation may be called later, from a different scheduler,
  or after cancellation.
- Exactly-once behavior needs race tests, not only single-threaded examples.
- Memory retention needs heap or allocation checks because unit tests rarely
  fail on retained closures.

Techniques that apply.

- **Recording continuation.** A tiny function or object records all calls. Assert
  call count, values, and order.
- **Once wrapper test.** Call success, error, and timeout paths in every order.
  Assert only the first reaches the real continuation.
- **Fake scheduler.** Run delayed resume through a deterministic queue so tests
  control time.
- **Pending continuation audit.** At test teardown, assert no continuation
  remains stored unless the test explicitly owns it.
- **Middleware fallthrough test.** For `next`-style APIs, test stop, pass, skip,
  and error paths separately.
- **Property test for parser CPS.** Generate input where the continuation should
  be called at most once per accepted parse branch, then assert no branch leaks.

Verification should also include negative timing tests. For a stored
continuation, create it, cancel the owner, then try to resume it. The expected
result should be a recorded rejection, not a late side effect. For middleware,
call a handler that ends the response and assert the fake `next` was not called.
Then call a handler that should pass control and assert `next` was called once.
For a trampoline, run an input large enough to overflow direct recursion in the
same runtime and assert the loop completes without native stack growth.

When continuations capture local variables, add a retention test if the runtime
and test tools make it practical. The test creates many short-lived owners,
stores and expires their continuations, forces collection where the platform
allows it, and checks that retained owner count falls. This kind of test is more
fragile than ordinary unit tests, but it catches the expensive class of leak
where every closure carries an old request graph.

## 16. Observability signals

Engineering judgement. Continuations need telemetry because the normal stack no
longer tells the full story.

What to record.

- A continuation id, parent id, logical operation name, and creation time.
- Resume count labelled by continuation type, success, failure, cancellation,
  timeout, and duplicate-resume rejection.
- Age of pending continuations, with histograms and a gauge for the count still
  stored.
- Scheduler or thread where the continuation was created and resumed.
- Size class of captured state when the runtime can expose it, or an application
  proxy such as request body size.
- Middleware `next` latency and a counter for handlers that ended the chain.
- Cleanup events around escape paths, including transaction close, lock release,
  span end, and resource disposal.

A healthy instance. Pending continuation count rises and falls with traffic.
Age stays below configured timeouts. Duplicate-resume rejections are rare and
investigated. Resume happens on the expected scheduler. Middleware chains show a
stable distribution of pass, stop, and error paths.

A failing instance. Pending count climbs after traffic drops, which points to a
dropped continuation or retained environment leak. Duplicate-resume rejection
spikes after a deploy, which points to a race. Resume appears on an unexpected
thread, which points to a scheduler handoff bug. Chain latency grows in one
middleware label, which localizes a stuck `next` or slow handler.

## 17. Security and privacy implications

Engineering judgement. Continuation is a control-transfer pattern, so the main
security question is who may control the future.

**Authorization bypass.** A raw continuation can let plugin or middleware code
skip later checks, repeat a protected step, or call a path after the user's
authorization context changed. Pass a constrained continuation wrapper that
checks authorization at resume time, not only at capture time.

**Replay.** A stored continuation bound to a URL, token, or callback id can be
reused unless it is one-shot or bound to a session. Racket's web server
documentation explicitly discusses storing captured continuations behind URLs
(https://download.racket-lang.org/docs/5.0.2/html/web-server/servlet.html,
verified 2026-08-02). In application code, expire such URLs, bind them to a
principal, and reject second use when the operation is one-shot.

**Retention of private data.** A continuation can capture request bodies,
headers, credentials, tenant ids, or local variables that were meant to die at
return. Treat stored continuations as data-bearing objects. Apply retention
limits, redact telemetry, and clear captured references after resume.

**Denial of service.** A caller that can create continuations faster than they
expire can consume heap or scheduler capacity. Bound pending continuations per
user, tenant, request, and process.

**Confused deputy.** A continuation resumed under a different ambient context
can run with the wrong tenant, locale, transaction, or security principal.
Capture the minimal context needed, validate it at resume, and avoid global
lookup during resume.

Where the pattern is silent. A local CPS helper that never stores the
continuation and never crosses a trust boundary has little security surface
beyond ordinary function calls. The concern appears when the continuation is
stored, replayable, remotely addressable, or exposed to untrusted code.

## Code examples

Three languages are used because each shows a different production shape.
TypeScript shows middleware-style `next`. Python shows escape continuation for
early exit from traversal. Go shows a once-guarded continuation wrapper. Java,
Rust, and Swift are omitted because the core lesson here is clearer with
first-class functions and small examples; those languages can express the same
contracts with interfaces, closures, and result callbacks.

### TypeScript

```typescript
type AppRequest = { path: string; user?: string };
type AppResponse = { status: number; body: string };
type Next = () => AppResponse;
type Middleware = (req: AppRequest, next: Next) => AppResponse;

function compose(stack: Middleware[], terminal: Next): (req: AppRequest) => AppResponse {
  return (req: AppRequest) => {
    const run = (index: number): AppResponse => {
      const current = stack[index];
      if (!current) return terminal();
      return current(req, () => run(index + 1));
    };
    return run(0);
  };
}

const requireUser: Middleware = (req, next) => {
  if (!req.user) return { status: 401, body: "login required" };
  return next();
};

const addTrace: Middleware = (req, next) => {
  const response = next();
  return { ...response, body: `${req.path}: ${response.body}` };
};

const app = compose([requireUser, addTrace], () => ({
  status: 200,
  body: "ok",
}));

console.log(app({ path: "/orders" }).status);
console.log(app({ path: "/orders", user: "mia" }).body);
```

### Python

```python
from collections.abc import Callable

Tree = tuple[str, list["Tree"]]
Escape = Callable[[str], str]


def walk(node: Tree, found: Escape, missing: Callable[[], str]) -> str:
    name, children = node
    if name.startswith("target"):
        return found(name)
    for child in children:
        result = walk(child, found, lambda: "")
        if result:
            return result
    return missing()


tree: Tree = (
    "root",
    [
        ("docs", []),
        ("src", [("target-continuation", [])]),
    ],
)

print(walk(tree, lambda value: f"found {value}", lambda: "not found"))
```

### Go

```go
package main

import "fmt"

type Continuation func(string)

func Once(k Continuation) Continuation {
	called := false
	return func(value string) {
		if called {
			fmt.Println("duplicate ignored")
			return
		}
		called = true
		k(value)
	}
}

func fetch(name string, resume Continuation) {
	if name == "" {
		resume("missing")
		return
	}
	resume("hello " + name)
	resume("late duplicate")
}

func main() {
	done := Once(func(value string) {
		fmt.Println(value)
	})
	fetch("continuation", done)
}
```

## 18. References

1. John C. Reynolds. "Definitional Interpreters for Higher-Order Programming
   Languages". ACM Annual Conference, 1972, pages 717-740. DOI
   10.1145/800194.805852. DBLP record:
   https://dblp.dagstuhl.de/rec/conf/acm/Reynolds72.html
   Verified 2026-08-02. Source for the lineage citation.
2. Andrew W. Appel. *Compiling with Continuations*. Cambridge University Press,
   1992. ISBN 978-0-521-03311-4. Cambridge Core record:
   https://www.cambridge.org/core/books/compiling-with-continuations/7CA9C36DCE78AD82218E745F43A4E740
   Verified 2026-08-02. Source for compiler CPS context and SML compiler use.
3. R6RS editors. *Revised^6 Report on the Algorithmic Language Scheme*,
   chapter 11, section 11.15, Control features.
   https://r6rs.org/final/html/r6rs/r6rs-Z-H-14.html
   Verified 2026-08-02. Source for `call-with-current-continuation`.
4. R7RS editors. *Revised^7 Report on the Algorithmic Language Scheme*,
   corrected HTML, section 4.2.6, Dynamic bindings.
   https://standards.scheme.org/corrected-r7rs/r7rs-Z-H-6.html
   Verified 2026-08-02. Source for dynamic extent and continuation reentry.
5. JetBrains. *Kotlin Language Specification*, section "Asynchronous programming
   with coroutines".
   https://kotlinlang.org/spec/asynchronous-programming-with-coroutines.html
   Verified 2026-08-02. Source for Kotlin CPS transformation and generated
   continuations.
6. JetBrains. *Kotlin Standard Library API*, `kotlin.coroutines.Continuation`.
   https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.coroutines/-continuation/
   Verified 2026-08-02. Source for the Kotlin `Continuation` production use.
7. Express project. *Using middleware*.
   https://expressjs.com/en/guide/using-middleware/
   Verified 2026-08-02. Source for Express `next` middleware production use.
8. Eclipse Foundation. *Jakarta Servlet 6.2.0-M1 API*,
   `jakarta.servlet.FilterChain`.
   https://jakarta.ee/specifications/servlet/6.2/apidocs/jakarta.servlet/jakarta/servlet/filterchain
   Verified 2026-08-02. Source for Servlet `FilterChain.doFilter`.
9. Racket project. *Racket Web Server documentation*, Stateful Servlets,
   `send/suspend`.
   https://download.racket-lang.org/docs/5.0.2/html/web-server/servlet.html
   Verified 2026-08-02. Source for captured web continuations bound to URLs.
10. Racket project. *Continue: Web Applications in Racket*.
   https://docs.racket-lang.org/continue/
   Verified 2026-08-02. Source for `send/suspend/dispatch`.
11. Haskell `mtl` maintainers. *Control.Monad.Cont* documentation.
   https://hackage.haskell.org/package/mtl/docs/Control-Monad-Cont.html
   Verified 2026-08-02. Source for `Cont` and `ContT` terminology.
