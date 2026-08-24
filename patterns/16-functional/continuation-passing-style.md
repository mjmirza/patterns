---
name: Continuation-Passing Style
slug: continuation-passing-style
family: 16-functional
category: Functional
aliases: [CPS, Explicit Continuation, CPS Transform, Success Continuation, Failure Continuation]
first_described: "Reynolds 1972"
maturity: canonical
related: [continuation, tail-call-optimization, trampolining, monad, async-await, future-promise, chain-of-responsibility]
incompatible_with: [implicit-return-contracts, double-callback, ambient-mutable-state, unbounded-continuation-retention]
verified: 2026-08-02
---

# Continuation-Passing Style

## 1. Name, aliases, and lineage

The canonical name is Continuation-Passing Style. The usual short form is
**CPS**. In CPS, a function does not deliver its answer by returning to the
native caller in direct style. It receives a continuation, usually a function
named `k`, and gives its result to that continuation. A stricter CPS program
also calls every continuation in tail position, so no work remains in the
current function after the continuation call.

The main aliases are **explicit continuation**, **CPS transform**, **success
continuation**, and **failure continuation**. The first names the programming
shape. The second names the compiler rewrite that converts direct style to CPS.
The last two name a common application variant where normal completion and
error completion are separate futures.

The lineage starts in programming language semantics and compiler work rather
than in object design catalogs. John C. Reynolds, "Definitional Interpreters
for Higher-Order Programming Languages", ACM Annual Conference 1972, pages
717-740, is the usual citation point for interpreters that make continuations
explicit. DBLP records Reynolds as author, the 1972 ACM venue, the page range,
and DOI 10.1145/800194.805852
(https://dblp.dagstuhl.de/rec/conf/acm/Reynolds72.html, verified 2026-08-02).
Andrew W. Appel then made CPS a named compiler representation in *Compiling
with Continuations*, Cambridge University Press, 1992. Cambridge University
Press describes the book as using CPS as the main intermediate form for
optimization and program transformation in a compiler for Standard ML
(https://www.cambridge.org/core/books/compiling-with-continuations/7CA9C36DCE78AD82218E745F43A4E740,
verified 2026-08-02).

Scheme and related languages made continuations part of the programmer-visible
control vocabulary. R6RS specifies `call-with-current-continuation`, also known
as `call/cc`, as a procedure that packages the current continuation and passes
it to a caller-supplied procedure
(https://r6rs.org/final/html/r6rs/r6rs-Z-H-14.html, verified 2026-08-02).
That is not identical to manual CPS, because `call/cc` captures an existing
future while CPS passes the future as an ordinary argument, but both designs
turn control flow into a value.

Modern production languages hide CPS behind coroutine and async syntax. The
Kotlin language specification states that each suspendable function is
transformed to continuation-passing style by receiving an extra parameter of
type `kotlin.coroutines.Continuation<T>` and returning `Any?`
(https://kotlinlang.org/spec/asynchronous-programming-with-coroutines.html,
verified 2026-08-02). The Kotlin standard library API defines
`Continuation<T>` as the interface representing the continuation after a
suspension point
(https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.coroutines/-continuation/,
verified 2026-08-02).

Engineering judgement. This entry treats CPS as the program representation
where the next step is an explicit parameter. It treats captured continuations,
delimited continuations, promises, and coroutines as related mechanisms, not as
the same pattern. That boundary matters because CPS can be written in any
language with functions, while captured continuations need runtime support.

## 2. Problem and context

A computation has a next step that matters as much as the value being computed.
The code has to choose that next step, store it, delay it, run it on another
execution context, replace it with an error path, or expose it as a framework
handoff point. A normal return value hides all of that behind the machine stack.

The problem appears in many forms. A compiler wants an intermediate program
where returns, jumps, tail calls, and exception exits can be optimized as
ordinary terms. An interpreter wants to describe evaluation order without
leaning on the host language's call stack. A parser wants success and failure
branches to be first-class values. A search procedure wants to leave many
recursive layers without building exception logic into every layer. A web
middleware wants each handler to decide whether the request stops here or moves
to the next handler. An asynchronous runtime wants a suspended computation to
resume later without keeping an operating system stack parked.

Direct style answers a narrower question: what value should the current
function return to its caller? CPS answers a broader question: what should
happen next after this value, failure, or partial result is known? The
difference is not syntax decoration. It changes ownership of control. In direct
style the caller owns the return address. In CPS the callee receives a value
that represents the return address and may call it, skip it, store it, wrap it,
or call another continuation instead.

The context that makes CPS useful has three conditions. First, control transfer
is part of the design, not an incidental detail. Second, the future can be
named with a small contract, for example `User -> Response` or
`ParseState -> Result`. Third, the codebase can pay the readability cost of
reading execution in terms of calls to continuations instead of returns.

The boundary is often the most important design choice. A full codebase written
in manual CPS is rare outside compilers, interpreters, and research languages.
A smaller boundary is common: one parser subsystem, one middleware runner, one
runtime adapter, one request suspension mechanism, or one compiler pass. That
boundary lets the rest of the program stay in direct style while the part that
needs explicit control uses CPS internally. A clean adapter at the edge should
translate `k(value)` into a return value, a promise settlement, a coroutine
resume, or an HTTP response.

There is also a difference between teaching CPS and shipping CPS. Teaching
examples often convert `add(x, y)` into `addCps(x, y, k)`. That shows the
mechanics but not the reason to pay for the mechanics. Production CPS earns its
place when the continuation can be delayed, selected, observed, or protected.
If none of those verbs apply, the continuation parameter is ceremony.

Outside that context, CPS becomes a tax. A direct function that computes a
value once and returns it to one caller is clearer in direct style. A business
rule that has no scheduling, retry, early exit, parser backtracking, compiler
rewrite, or middleware handoff should return a value and stop there.

## 3. Forces

Engineering judgement. The forces below describe the trade in application
code, runtime code, and compiler code.

- **Control explicitness.** Favoured. The next step has a name, a type, and a
  call site. Early exit and alternate completion paths are no longer hidden in
  the language runtime.
- **Local readability.** Sacrificed. Direct style reads from top to bottom.
  CPS often reads as nested futures, with later work written before the call
  that produces the value.
- **Latency.** Mixed. CPS can remove stack growth and let a runtime schedule
  work cooperatively. It can also allocate closures and add dispatch hops.
- **Coupling.** Favoured when the callee knows only a continuation type.
  Sacrificed when the continuation closes over a large owner object, scheduler,
  request, or mutable context.
- **Consistency.** Mixed. A single continuation can centralize completion.
  Calling it twice, calling it after cancellation, or forgetting to call it
  breaks consistency in ways a normal return cannot express.
- **Operability.** Sacrificed unless the code records continuation creation,
  resume, cancellation, and age. Native stack traces no longer show the whole
  logical call chain.
- **Cost.** Favoured for compilers and runtimes because a uniform control
  representation simplifies later passes. Sacrificed in hand-written
  application code because every function signature carries control plumbing.
- **Team topology.** Favoured at framework boundaries. A platform team can own
  the runner while product teams supply handlers that receive a continuation.
  Sacrificed inside product code where many teams must read and maintain nested
  callbacks.
- **Cognitive load.** High. A reader must track who owns the continuation,
  whether it is single-use, whether it may run synchronously, and which
  variables it retains.

CPS favours code where control flow is itself the subject. It sacrifices
ordinary sequential reading. That is a reasonable price in compiler IRs,
middleware runners, async runtime internals, and parser combinators. It is a
poor price for plain transformations over local data.

## 4. Applicability and non-applicability

Reach for Continuation-Passing Style when the following hold.

- A computation needs to choose among several futures: success, failure,
  retry, abort, backtrack, or next handler.
- A recursive algorithm needs tail-position calls but cannot be made into a
  simple accumulator loop without losing the shape of the algorithm.
- A compiler or interpreter needs an intermediate form where evaluation order
  and control targets are explicit.
- A framework needs to own the runner while giving user code a precise handoff
  point, such as a `next` middleware function.
- An async or coroutine runtime has to suspend and resume logical execution
  without blocking an operating system thread.
- A parser, evaluator, or search routine needs backtracking where the next
  choice is a value.
- The continuation can be small, typed, and documented as single-use or
  multi-use.

Do NOT reach for Continuation-Passing Style in these cases.

- **The function has one ordinary result and one ordinary caller.** Return the
  value. CPS adds a second protocol without removing a real problem.
- **The language already has good `async` and `await` for the caller surface.**
  Use direct-looking async syntax at the boundary and keep CPS inside the
  adapter or runtime.
- **The continuation would capture a large mutable object graph.** The heap
  will retain everything reachable from the closure. Pass a small value record
  instead.
- **The codebase lacks a firm exactly-once convention.** A continuation that
  may be called twice creates duplicate writes, duplicate responses, and
  repeated cleanup.
- **The main issue is validation or error reporting.** Use typed results,
  exceptions, or a validation applicative. CPS can model errors, but it is too
  broad when the only difference is success versus failure.
- **The call chain must remain visible in native stack traces for support.**
  Manual CPS cuts the logical call chain into many closure frames and runner
  frames.
- **The continuation crosses a trust boundary without a wrapper.** A plugin
  that receives the raw continuation controls the rest of the framework's
  computation.
- **The scheduler ownership is unclear.** Calling a continuation on the wrong
  thread, event loop, actor, or executor can break affinity rules.
- **The team is using CPS to avoid a small local refactor.** A guard clause,
  loop, strategy, visitor, or promise chain may express the same idea with less
  control machinery.

## 5. Structure

The participants are named by role rather than by class.

- **Current computation.** The function that would return a value in direct
  style. In CPS it receives one or more continuations and calls one in tail
  position.
- **Success continuation.** A function that accepts the normal result and
  represents the next step of the computation.
- **Failure continuation.** An optional function that accepts an error,
  rejection, missing parse, or abort reason. It keeps error control explicit
  without throwing.
- **Continuation owner.** The caller, runner, compiler pass, middleware engine,
  parser driver, or runtime that creates the continuation and decides its
  contract.
- **Captured environment.** The values retained by the continuation closure.
  This is the main lifetime cost of CPS.
- **Final continuation.** The outer bridge that converts CPS back to a direct
  result, process exit code, HTTP response, promise completion, or test
  assertion.
- **Scheduler or driver.** Optional. A loop, executor, event queue, trampoline,
  or coroutine runtime that stores and resumes continuations.

The core relationship is simple. The owner calls the current computation and
passes a continuation. The current computation does its local work and calls a
continuation instead of returning to the owner with an ordinary value. In a
strict CPS program, both recursive calls and continuation calls are tail calls.
When the language lacks tail call optimization, the scheduler or trampoline may
store the next step as data and run it in a loop.

## 6. ASCII structure diagram

```
 +--------------------+        calls         +----------------------+
 | Continuation Owner | -------------------> | Current Computation  |
 |--------------------|                      |----------------------|
 | creates k          |                      | input                |
 | creates errK       |                      | success k            |
 | sets policy        |                      | failure errK         |
 +---------+----------+                      +----------+-----------+
           |                                            |
           | owns                                       | tail-calls
           v                                            v
 +--------------------+                      +----------------------+
 | Success            | <------------------- | local result         |
 | Continuation k     |     value            +----------------------+
 |--------------------|
 | accepts result     |                      +----------------------+
 | runs next step     | <------------------- | error or abort       |
 +--------------------+     reason           +----------------------+
           ^
           |
           | closes over
           v
 +--------------------+        optional      +----------------------+
 | Captured           | <------------------- | Scheduler or Driver  |
 | Environment        |                      |----------------------|
 +--------------------+                      | stores continuations |
                                             | resumes later        |
                                             +----------------------+
```

## 7. Dynamics

The runtime flow changes the direction of result delivery. The current
computation calls the continuation. It does not return a domain result to its
native caller. A final continuation converts the CPS world back to the outside
world.

```
Client       CPS Function        Nested CPS Function      Continuation k
  |               |                       |                     |
  |-- call f(x,k)->                       |                     |
  |               |-- call g(y,k2) ------>|                     |
  |               |                       |                     |
  |               |       compute value   |                     |
  |               |<----- k2(value) ------|                     |
  |               |                       |                     |
  |               | transform value       |                     |
  |               |-- k(result) ------------------------------->|
  |               |                       |                     |
  |               |  no more local work   |                     |
  |               |                       |                     |
```

A success and failure variant makes the branch visible.

```
Parser Owner       parseTerm CPS       Success k        Failure errK
    |                   |                  |                 |
    |-- parse(input,k,errK)--------------->|                 |
    |                   |                  |                 |
    |                   |-- token ok ----->|                 |
    |                   |                  |                 |
    |                   |-- k(ast, rest) ------------------->|
    |                   |                  |                 |
    |                   |-- token bad ---------------------->|
    |                   |                  |   errK(reason)  |
```

The call to `k` is the return path. In strict CPS, there is no statement after
that call. If work appears after the continuation call, the code is a callback
API, not full CPS. That distinction matters because tail-position continuations
are what make stack removal, trampolining, and compiler control-flow rewrites
straightforward.

## 8. Implementation variants

**Manual single-continuation CPS.** A function receives one continuation and
passes its normal result to it. This is the smallest form and the easiest to
teach. It fits transformations, tree walks, and small interpreters. The cost is
poor error shape unless errors are encoded in the result.

**Success and failure continuations.** The function receives `ok` and `fail`.
Parsers, validators, and callback APIs often use this shape. It avoids throwing
through unknown frames and can express backtracking. The cost is protocol
discipline. Exactly one of the two should run for a single-use operation.

**Node or middleware CPS.** The continuation is named `next` and means "run the
next handler". Express documents middleware as receiving request, response, and
`next`, and says calling `next()` invokes the next middleware function in the
application
(https://expressjs.com/en/guide/writing-middleware/, verified 2026-08-02).
This is CPS specialized to pipelines. It permits short-circuiting by not
calling the continuation.

**Compiler CPS transform.** A compiler rewrites direct-style source into a form
where all intermediate results and control targets have names. Appel's
*Compiling with Continuations* is the classic book-length treatment of this
approach for Standard ML
(https://www.cambridge.org/core/books/compiling-with-continuations/7CA9C36DCE78AD82218E745F43A4E740,
verified 2026-08-02). In this variant, CPS is not an API exposed to users. It
is a machine-facing representation that lets compiler passes treat return
points, branches, calls, and exceptional exits under one control vocabulary.

**Generated coroutine CPS.** Source remains direct-looking, while the compiler
adds continuation parameters and builds a state machine. Kotlin documents this
directly for suspendable functions
(https://kotlinlang.org/spec/asynchronous-programming-with-coroutines.html,
verified 2026-08-02). This variant is usually preferable at public application
boundaries because it gives operators and maintainers source-level sequencing.

**Defunctionalized CPS.** Instead of storing a closure, the program stores a
tagged data value such as `AfterRead`, `AfterParse`, or `AfterValidate`. A
driver interprets those tags. This costs more boilerplate but gives better
serialization, inspection, and test control.

**Trampolined CPS.** Each CPS step returns a small value describing the next
call. A loop runs those steps. This avoids stack growth in languages without
tail call optimization. The cost is allocation and a runner protocol.

**Continuation monad.** A type such as `Cont r a` represents a computation that
will give an `a` to a continuation and end in result type `r`. This variant
packages CPS composition behind `map` and `flatMap` or `bind`. It fits
functional libraries, but it can hide control flow from teams that do not
already read monadic code.

**Delimited or captured continuation bridge.** A runtime captures the current
continuation and exposes it as a value. Racket's reference documents
`call-with-current-continuation` and related prompt operations
(https://docs.racket-lang.org/reference/cont.html, verified 2026-08-02). This
is more powerful than manual CPS and needs stronger lifetime and barrier rules.

**Object continuation.** Some public APIs use an object with methods such as
`resume`, `resumeWith`, `fail`, or `cancel` rather than a raw function. Kotlin's
standard library uses an interface for this role
(https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.coroutines/-continuation/,
verified 2026-08-02). The object form costs more surface area, but it gives the
runtime a place to carry context, interception, and failure delivery.

**Linear continuation.** A linear continuation is meant to be called at most
once. Few mainstream languages can express that type rule directly, so library
code simulates it with wrappers. This variant is the right default for request
completion, promise settlement, payment flow steps, and middleware forwarding.

**Multi-shot continuation.** A multi-shot continuation can be called more than
once. Parser backtracking and nondeterministic search can benefit from this
power. The cost is much higher because every captured value may need to remain
valid across repeated resumes. In ordinary service code, multi-shot behavior is
more often a bug than a feature.

## 9. Known production uses

**Kotlin coroutines.** Kotlin suspend functions are specified as a CPS
transformation with an added `Continuation<T>` parameter. The language
specification says a suspendable function is transformed from normal invocation
to CPS and receives an additional continuation parameter
(https://kotlinlang.org/spec/asynchronous-programming-with-coroutines.html,
verified 2026-08-02). The standard library exposes the continuation interface
used at this boundary
(https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.coroutines/-continuation/,
verified 2026-08-02).

**Racket web server stateful servlets.** Racket's web-server documentation
shows `send/suspend` creating a URL and says a later browser request is
returned from `send/suspend` to the continuation of that call. It also describes
`send/suspend/dispatch` as supporting multiple logical continuations of a page
(https://docs.racket-lang.org/web-server/servlet.html, verified 2026-08-02).
This is a production web framework using continuations as web interaction
state.

**Express middleware.** Express middleware receives `req`, `res`, and `next`.
The Express guide states that calling `next()` invokes the next middleware
function in the app
(https://expressjs.com/en/guide/writing-middleware/, verified 2026-08-02).
This is not a whole-program CPS transform, but it is a production API whose
pipeline handoff is continuation-passing.

**Standard ML of New Jersey compiler lineage.** Appel's *Compiling with
Continuations* documents CPS as the compiler representation used for Standard
ML compiler work, and Cambridge University Press describes the book as applying
CPS to optimization and transformation in a compiler for Standard ML
(https://www.cambridge.org/core/books/compiling-with-continuations/7CA9C36DCE78AD82218E745F43A4E740,
verified 2026-08-02). This source is cited for the compiler lineage and use,
not for a page-specific claim.

## 10. Consequences

Positive.

- Control transfer becomes explicit and programmable.
- Tail-position calls become easier to see, which helps trampolines and
  compiler rewrites.
- Early exit, failure, retry, parser backtracking, and middleware
  short-circuiting can be represented without special return sentinels.
- A framework can give user code a narrow handoff point while keeping the
  runner under framework ownership.
- Async runtimes can represent suspended work on the heap rather than keeping a
  native stack blocked.
- Tests can pass continuations that record result delivery, double calls, and
  missed calls.

Negative.

- Sequential reading becomes harder. The code no longer follows direct source
  order.
- Closure allocation and retained environments can raise memory use.
- Native stack traces often show runner frames and callbacks rather than the
  logical call chain.
- Exactly-once behavior is a convention unless the continuation wrapper
  enforces it.
- A continuation can run synchronously or later unless the API states one
  timing rule.
- Cancellation and timeout handling move into continuation wrappers and drivers.
- Public CPS APIs are harder to evolve because every caller now participates in
  the control protocol.

## 11. Failure modes and misuse

Engineering judgement. These failure modes are written as observable symptoms,
causes, and fixes because abstract warnings do not help during an incident.

**Double continuation call.** Symptom. A request sends two responses, a promise
settles once and logs a later ignored completion, or a database write happens
twice for one input. Cause. Both the success and failure path call their
continuation, or a timeout path races a later success path. Fix. Wrap the
continuation in an exactly-once guard and make the second call a logged error.

**Dropped continuation.** Symptom. A request hangs, a parser never reports
failure, a test waits until timeout, or a coroutine remains suspended. Cause. A
branch returns without calling success, failure, abort, or cancellation. Fix.
Use exhaustive branch tests and a watchdog metric for pending continuation age.

**Continuation called after cancellation.** Symptom. A cancelled request still
writes to a socket, a closed UI view receives an update, or a task logs success
after its owner timed out. Cause. The stored continuation did not check the
current cancellation token at resume time. Fix. Put the cancellation check in
the wrapper around the continuation, not only at the original call site.

**Captured environment leak.** Symptom. Heap snapshots show request objects,
buffers, or user records retained by closures long after the request should be
gone. Cause. The continuation closes over the whole frame. Fix. Copy only the
small immutable values the next step needs, and clear pending entries on
timeout.

**Hidden synchronous resume.** Symptom. A caller observes state changed before
the CPS function returns, even though the API was assumed to be async. Cause.
The implementation calls the continuation immediately for a cache hit or fast
validation path. Fix. Document synchronous versus deferred behavior, or force
all continuation calls through the scheduler.

**Scheduler affinity breach.** Symptom. A UI update runs on a worker thread, an
actor receives state mutation outside its mailbox, or a request context is lost
after an event-loop hop. Cause. The continuation was resumed on the wrong
executor. Fix. Store scheduler identity with the continuation and resume only
through that scheduler.

**Callback pyramid.** Symptom. A function becomes a deep nest of anonymous
continuations and repeats error handling at every level. Cause. Manual CPS was
used where promises, async functions, parser combinators, or a named state
machine would be clearer. Fix. Collapse the public surface to direct-looking
async code or extract named continuation steps.

**Exception crossing CPS boundary.** Symptom. A thrown exception bypasses the
failure continuation and appears as an unhandled process error. Cause. The CPS
function mixes throw-based failure with explicit failure continuations. Fix.
Catch at the boundary and translate into the failure continuation, or remove
the failure continuation and use exceptions consistently.

**Continuation exposed to untrusted code.** Symptom. A plugin skips billing,
audit, validation, or cleanup by calling the continuation early or not calling
it at all. Cause. The framework passed the raw continuation to untrusted
extension code. Fix. Pass a narrowed wrapper that enforces ordering, policy,
quota, and exactly-once behavior.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Continuation-Passing Style | Direct Return | Exception | Promise or Future | Async/Await | Trampolining |
|---|---|---|---|---|---|---|
| Control explicitness | High. Next step is a value | Low. Return target is implicit | Medium. Error path is implicit | Medium. Continuations attach to result | Medium. Compiler hides CPS | Medium. Next step is data |
| Local readability | Low for hand-written code | High | High on normal path | Medium | High | Medium |
| Stack use | Low with tail calls or runner | Native stack grows | Native stack grows until throw | Low after async boundary | Low after suspend | Low |
| Error modeling | Strong with failure continuation | Needs result type or throw | Strong for exceptional paths | Strong for async errors | Strong for async errors | Needs extra step type |
| Cancellation | Explicit but manual | External | External | Often built into runtime type | Often runtime-supported | Manual |
| Operability | Needs logical trace fields | Native stack helps | Native stack helps until async | Needs promise tracing | Runtime often helps | Driver can report steps |
| Heap pressure | Closure per continuation | Low | Low on normal path | State plus callbacks | State machine or heap frame | Step objects |
| Team fit | Good for framework internals | Good for business logic | Good for exceptional failures | Good for async APIs | Good for app surfaces | Good for stack safety |
| Data-driven branching | Strong | Branch in caller | Poor | Medium | Medium | Medium |
| Trust boundary safety | Risky without wrapper | Safer | Safer | Safer if API controls settle | Safer if runtime controls resume | Safer if driver owns steps |

Reading of the table. CPS wins where the program must manipulate the future.
Direct return wins where there is one ordinary future. Exceptions win for rare
failure exits when native stack semantics are acceptable. Promises and
async/await win for user-facing asynchronous application APIs. Trampolining
wins when the core issue is stack depth rather than control abstraction.

Engineering judgement. A useful migration rule is to expose the highest-level
alternative that fits the caller. For public asynchronous APIs, that is usually
`async` and `await`, a task, or a promise. For a middleware runner, it may be a
`next` continuation because the handler truly chooses whether the chain
continues. For compiler internals, CPS may be the clearest form because the
consumer is another compiler pass rather than a person reading business code.
The same control idea can therefore be excellent in one layer and noisy in the
next layer above it.

## 13. Related and incompatible patterns

- **Continuation.** CPS passes a continuation explicitly. Captured
  continuations reify the current future at runtime. CPS is easier to port
  across languages. Captured continuations are more powerful and more dangerous.
- **Tail Call Optimization.** Strict CPS puts calls in tail position. A runtime
  with tail call optimization can run that shape without growing the stack.
- **Trampolining.** A trampoline is the usual companion when the language lacks
  tail call optimization. CPS produces the next step. The trampoline runs it.
- **Monad.** The continuation monad packages CPS behind a compositional type.
  It works well in functional libraries but can hide control flow from readers.
- **Future or Promise.** A promise stores continuations and runs them after a
  result appears. It is a structured, runtime-owned cousin of CPS.
- **Async/Await.** Async syntax is often compiled to a state machine that
  carries a continuation. It replaces manual CPS at application boundaries.
- **Chain of Responsibility.** Middleware `next` is a continuation specialized
  to a chain. CPS is the implementation shape behind many middleware chains.
- **Strategy.** Strategy selects an algorithm. CPS selects, stores, or calls
  the rest of the computation. They compose when the continuation chooses among
  strategies.
- **Ambient mutable state.** This conflicts with stored continuations. A
  continuation may resume after ambient state has changed or been cleared.
- **Service Locator.** This conflicts when a continuation reaches into global
  state to recover dependencies that should have been captured explicitly.

## 14. Refactoring path in and out

Introducing CPS into direct-style code.

1. Identify the point where direct return hides a real control decision, such
   as early exit, retry, parser failure, async completion, or next middleware.
2. Extract the code that currently runs after the direct call into a named
   function. Its parameter is the result that direct style would have returned.
3. Change the original function to accept that function as a continuation.
   Call the continuation with the result instead of returning the result.
4. Move any remaining work after the continuation call into the continuation
   body. The CPS function should have no local work after calling `k`.
5. Add a failure continuation only when the caller needs a separate failure
   future. Do not add it by habit.
6. Add an exactly-once wrapper if the operation is single-use.
7. Add telemetry for continuation creation, resume, error, cancellation, and
   age before storing continuations across requests or event-loop turns.
8. Convert callers one boundary at a time. Keep a direct-style adapter at the
   outer edge so the rest of the program is not forced into CPS at once.

Refactoring out to `async` or promises.

1. Wrap the CPS function in a promise, future, task, or coroutine adapter.
2. Translate the success continuation into completion of the result.
3. Translate the failure continuation into rejection or a typed error result.
4. Move cancellation into the runtime's cancellation token if one exists.
5. Migrate callers to `await`, `then`, or direct task composition.
6. Keep the low-level CPS boundary only where a legacy callback or middleware
   API still requires it.

Refactoring out to direct return.

1. Find CPS functions whose continuation is always called once,
   synchronously, and with no alternate branch.
2. Inline the continuation body after the call site.
3. Change the CPS function to return the value it currently passes to `k`.
4. Replace the call with a direct assignment or return.
5. Delete once-only wrappers and pending-continuation metrics that no longer
   have a continuation to observe.

## 15. Testing and verification

Engineering judgement. CPS makes result delivery testable, but it also creates
new contracts around timing and cardinality.

Easier because of the pattern.

- Tests can pass a recording continuation and assert the exact value delivered.
- Tests can pass a failure continuation and assert that parse failure, timeout,
  or validation failure takes the intended branch.
- Stack-safety tests can run a deep recursive input and check that the driver
  finishes without stack overflow when a trampoline or tail calls are present.
- Middleware tests can pass a `next` function that increments a counter, then
  assert whether a handler forwarded or short-circuited.

Harder because of the pattern.

- A passing value assertion is not enough. The test must also assert that the
  continuation ran exactly once when that is the contract.
- Timing must be tested when the API promises deferred resume. Fast paths often
  resume synchronously by accident.
- Native stack traces do not show the logical chain, so tests need named steps
  or trace identifiers for failure messages.
- Cancellation and timeout races need controlled schedulers or fake clocks.

Techniques that apply.

- **Recording continuation.** Capture all values passed to `k` in a test list.
  Assert the list has length one and the expected value.
- **Fail-fast continuation.** In a success-only test, pass a failure
  continuation that raises a test error if called.
- **Exactly-once wrapper test.** Call the wrapped continuation twice and assert
  the second call reports a contract breach without repeating the effect.
- **Scheduler test.** Use a fake executor that records which queue received the
  continuation, then drain the queue under test control.
- **Leak test.** Store a weak reference to a large object captured by a
  continuation, clear the pending continuation, force collection where the
  runtime permits, and assert the object can be reclaimed.

## 16. Observability signals

Engineering judgement. CPS hides the native call path, so telemetry must record
the logical path.

Record these fields.

- Continuation id. Generate it at creation and carry it through resume,
  cancellation, and failure.
- Continuation kind. Example values: success, failure, retry, abort, next,
  parser-choice, coroutine-resume.
- Owner name. The function, middleware, parser, compiler pass, or runtime
  component that created the continuation.
- Resume count. Single-use continuations should show zero or one. Anything
  above one is a contract breach.
- Pending age. Measure time from creation to resume, cancellation, timeout, or
  cleanup.
- Scheduler name. Record the queue, executor, event loop, actor, or thread
  pool that resumed the continuation.
- Captured payload size where measurable. At minimum, record count of pending
  continuations by owner.
- Outcome. Values should include resumed, failed, cancelled, timed_out,
  dropped, and rejected_double_call.

A healthy dashboard shows stable pending counts, low pending age, no double
call events, and a continuation kind mix that matches expected traffic. A
middleware pipeline shows most requests either forwarding through the expected
number of handlers or short-circuiting at known authentication, routing, or
error handlers.

A failing dashboard shows pending age climbing, a flatline in resume counts
after a deploy, double-call events from one owner, or scheduler labels that
change unexpectedly. Heap growth paired with rising pending continuation count
points at retained environments. High `dropped` counts point at branches that
return without calling any continuation.

## 17. Security and privacy implications

Engineering judgement. CPS is a control-flow pattern, so its main security risk
is handing control to code that should not own it.

**Continuation as authority.** A continuation can mean "finish this request",
"run the next handler", "commit the result", or "resume privileged work".
Treat that function as an authority-bearing value. Do not pass raw
continuations to plugins when a narrower wrapper can enforce order, quota,
authorization, and exactly-once behavior.

**Bypassed checks.** Middleware CPS lets a handler call `next` early, late, or
not at all. If authentication, audit, rate limits, and input validation are
separate continuation steps, the runner should own their order rather than
trusting plugins to call them.

**Replay.** A stored continuation can be invoked more than once unless the
wrapper forbids it. In a web flow, replay can duplicate writes. In a payment or
approval flow, replay can repeat an action after the user believes the flow is
over. Bind continuations to a nonce, expiry, tenant, user, and generation where
they cross a request boundary.

**Data retention.** Continuations retain captured variables. A closure that
captures a request may retain headers, tokens, form data, and personal data
until the continuation is resumed or cleared. Keep captured state small and set
retention rules for pending-continuation stores.

**Confused scheduler.** Resuming a continuation under the wrong security
context can attach one user's result to another user's trace, request, or
tenant. Carry security context explicitly or use a continuation-local context
mechanism supplied by the runtime.

**Exception escape.** If a CPS API promises that errors go to a failure
continuation, a thrown exception can bypass redaction, audit, or cleanup. Catch
at the boundary and translate into the failure path, or document that thrown
exceptions are outside the CPS contract.

**Privacy in observability.** Continuation ids and owner names can become
linkable data when they include tenant, user, region, or workflow identifiers.
Use opaque ids for logs and keep raw domain identifiers in protected fields with
retention rules. Pending-continuation stores should be treated like session
stores because they can retain user input and authorization context.

**Liveness as a security property.** A dropped continuation can become denial
of service when pending work occupies a slot, actor mailbox, socket, timer, or
workflow record. Put hard age limits on stored continuations and make expiry a
normal outcome, not an unobserved cleanup thread.

## 18. References

1. John C. Reynolds. "Definitional Interpreters for Higher-Order Programming
   Languages." ACM Annual Conference, 1972, pages 717-740. DOI
   10.1145/800194.805852. DBLP record:
   https://dblp.dagstuhl.de/rec/conf/acm/Reynolds72.html
   Verified 2026-08-02. Source for the lineage citation.
2. Andrew W. Appel. *Compiling with Continuations*. Cambridge University Press,
   1992. Cambridge University Press record:
   https://www.cambridge.org/core/books/compiling-with-continuations/7CA9C36DCE78AD82218E745F43A4E740
   Verified 2026-08-02. Source for compiler CPS lineage and the Standard ML
   compiler representation claim.
3. Kotlin project. *Kotlin Language Specification*, "Asynchronous programming
   with coroutines", section "Continuation Passing Style".
   https://kotlinlang.org/spec/asynchronous-programming-with-coroutines.html
   Verified 2026-08-02. Source for the generated continuation parameter in
   suspendable functions.
4. Kotlin project. *Kotlin Standard Library API*, `kotlin.coroutines.Continuation`.
   https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.coroutines/-continuation/
   Verified 2026-08-02. Source for the public `Continuation<T>` interface.
5. R6RS editors. *Revised^6 Report on the Algorithmic Language Scheme*,
   section on control features and `call-with-current-continuation`.
   https://r6rs.org/final/html/r6rs/r6rs-Z-H-14.html
   Verified 2026-08-02. Source for Scheme continuation terminology.
6. Racket project. *The Racket Reference*, section 10.4, "Continuations".
   https://docs.racket-lang.org/reference/cont.html
   Verified 2026-08-02. Source for captured and delimited continuation
   operations.
7. Racket project. *Racket Web Server*, "Stateful Servlets".
   https://docs.racket-lang.org/web-server/servlet.html
   Verified 2026-08-02. Source for `send/suspend` and web continuations.
8. Express project. *Writing middleware for use in Express apps*.
   https://expressjs.com/en/guide/writing-middleware/
   Verified 2026-08-02. Source for the `next` continuation in middleware.

## Code examples

Three languages are shown. TypeScript shows the common web and middleware
shape. Python shows success and failure continuations for parsing. Go shows a
typed CPS pipeline with an exactly-once guard. The samples are small enough to
run without framework scaffolding.

### TypeScript

```typescript
type Done<T> = (value: T) => void;

function readUser(id: number, k: Done<string>): void {
  const users = new Map<number, string>([
    [1, "Ada"],
    [2, "Grace"],
  ]);
  const name = users.get(id) ?? "Unknown";
  k(name);
}

function greetUser(id: number, k: Done<string>): void {
  readUser(id, (name) => {
    k(`hello ${name}`);
  });
}

greetUser(1, (message) => {
  console.log(message);
});
```

### Python

```python
from collections.abc import Callable

Ok = Callable[[int, str], str]
Fail = Callable[[str], str]


def parse_int(text: str, ok: Ok, fail: Fail) -> str:
    stripped = text.strip()
    if not stripped:
        return fail("empty")
    if not stripped.isdecimal():
        return fail("not a number")
    return ok(int(stripped), stripped)


def describe(text: str) -> str:
    return parse_int(
        text,
        lambda value, raw: f"{raw} squared is {value * value}",
        lambda reason: f"invalid input: {reason}",
    )


if __name__ == "__main__":
    print(describe("7"))
    print(describe(" nope "))
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
			fmt.Println("double call rejected")
			return
		}
		called = true
		k(value)
	}
}

func Lookup(id int, k Continuation) {
	names := map[int]string{1: "Ada", 2: "Grace"}
	name, ok := names[id]
	if !ok {
		k("Unknown")
		return
	}
	k(name)
}

func main() {
	done := Once(func(value string) {
		fmt.Println("hello " + value)
	})
	Lookup(2, done)
	done("late")
}
```
