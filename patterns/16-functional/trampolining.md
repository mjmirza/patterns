---
name: Trampolining
slug: trampolining
family: 16-functional
category: Functional
aliases: [Trampoline, Trampolined Style, Stackless Recursion, Bounce Loop]
first_described: "Established implementation technique in functional programming and compiler literature"
maturity: established
related: [continuation-passing-style, tail-recursion, free-monad, monad, interpreter, iterator]
incompatible_with: [native-tail-call-required, synchronous-unbounded-work-on-request-thread, stack-sensitive-security-checks]
verified: 2026-08-02
---

# Trampolining

## 1. Name, aliases, and lineage

The canonical name in this entry is Trampolining. The concrete value that a
program returns to the driver is often called a **trampoline**, a **bounce**, a
**thunk**, a **step**, a **tail call token**, or a **stackless computation**.
The broader programming style is called **trampolined style**. In Clojure, the
standard function is named `trampoline`. In Scala, the standard library exposes
`scala.util.control.TailCalls`, whose API documentation says its methods
implement tail calls through trampolining
(https://scala-lang.org/api/3.x/scala/util/control.html, verified 2026-08-02).

The idea is older than the term's current library packaging. Scheme reports
made proper tail recursion part of the language contract. R5RS says a Scheme
implementation is properly tail-recursive when it supports an unbounded number
of active tail calls, and its rationale explains why a tail call can reuse the
same continuation rather than allocate another one
(https://groups.csail.mit.edu/mac/ftpdir/scheme-reports/r5rs-html.old/r5rs_22.html,
verified 2026-08-02). Trampolining is the library-level answer used when the
host runtime does not give that guarantee for the calls the program needs.

The named research lineage includes Steven D. Ganz, Daniel P. Friedman and
Mitchell Wand, "Trampolined Style", ICFP 1999, pages 18 to 22. Yasuhiko
Minamide's "Selective Tail Call Elimination", SAS 2003, section 2, describes
tail call elimination with trampolines for runtimes without direct tail-call
support. Runar Oli Bjarnason's "Stackless Scala With Free Monads", Scala
Workshop 2012, sections 3 and 4, gives the Scala formulation used by many
functional programmers on the JVM
(https://blog.higher-order.com/assets/trampolines.pdf, verified 2026-08-02).

The name is easy to misread. Trampolining is not a faster call instruction. It
is an explicit protocol. A recursive function stops calling the next recursive
function directly. It returns either a final value or a delayed next step. A
single loop receives those values, calls delayed steps one at a time, and stops
when it sees the final value. The call stack stays flat because the recursive
chain has moved into heap values controlled by the loop.

Engineering judgement. Treat Trampolining as an implementation pattern, not as
a domain abstraction. The domain does not care whether a parser, workflow, or
tree walk bounces. The codebase cares because it must run on a runtime whose
call stack has a fixed budget.

## 2. Problem and context

A program expresses repetition, descent, or mutual recursion through function
calls. The call depth can be larger than the runtime stack. The logic may be
tail-recursive, but the language, compiler, runtime, or specific call shape does
not remove the stack frame. The failure appears only at scale. A unit test over
ten nodes passes. A production document with one hundred thousand nested nodes
crashes. A state machine that alternates between two functions works for short
inputs, then fails after enough transitions.

The simplest case is direct tail recursion:

```text
sum(n, acc):
  if n == 0: return acc
  return sum(n - 1, acc + n)
```

If the runtime converts that final call into a jump, the stack remains flat. If
it does not, each call keeps a frame until the final answer returns. Many
production runtimes optimize narrower cases than programmers expect. Bjarnason
shows that Scala can optimize self-recursive methods in tail position, but not
mutual recursion across `even` and `odd`, and not general monadic composition on
the JVM
(https://blog.higher-order.com/assets/trampolines.pdf, verified 2026-08-02).

The second case is mutual recursion. A parser alternates between `parseValue`,
`parseArray`, and `parseObject`. A protocol handler alternates between
`readHeader`, `readBody`, and `readTrailer`. A validator alternates between
`checkNode` and `checkChildren`. Each call may be in tail position, but no
single function calls only itself. Many compilers can rewrite self recursion to
a loop, but cannot rewrite a graph of calls without changing the calling
convention.

The third case is composition. A library builds a long chain of `flatMap`,
`map`, continuation, visitor, or interpreter steps. No source line looks deeply
recursive, but the runtime evaluation of the composed value nests calls. Cats
documents `Eval` as a data type for controlling synchronous evaluation whose
implementation is designed for stack safety through trampolining
(https://typelevel.org/cats/datatypes/eval.html, verified 2026-08-02). Its API
documentation states that `map` and `flatMap` use an internal trampoline to
avoid stack overflows
(https://typelevel.org/cats/api/cats/Eval.html, verified 2026-08-02).

Trampolining fits when the program can represent "what to do next" as a value.
The next value is usually a zero-argument function, a small enum, a sealed
class, or a closure plus arguments. The driver loop repeatedly examines that
value. If it is a final result, the loop returns. If it is a delayed step, the
loop calls it and repeats. The program has not reduced the amount of work. It
has changed where pending work lives.

The context also includes ownership. Trampolining is rarely a leaf-function
choice made in isolation. It works best at a boundary where one module owns the
recursion contract. Examples include a parser package, a small expression
evaluator, a validation engine, a recursive descent over user-supplied data, or
a functional data type that exposes `map` and `flatMap`. If each application
call site builds its own trampoline wrapper, the codebase ends up with many
small drivers, many step encodings, and no shared budget policy. A single
driver per recursive subsystem gives a better place for naming, limits,
metrics, and tests.

There is a practical timing issue as well. Many teams first meet this problem
after a crash, because small examples do not reveal stack pressure. The right
response is not to wrap every recursive function in a trampoline. First classify
the call graph. A structurally recursive tree walk with bounded depth may need
an input limit. A single accumulator recursion may need a loop. A mutually
recursive state machine over untrusted or large input is a stronger candidate.
The pattern is a repair for a specific resource mismatch: the logical depth of
the program can be much larger than the host stack budget.

## 3. Forces

Engineering judgement. These forces are trade-offs observed when a recursive
algorithm is moved from the call stack into heap-allocated steps.

- **Stack safety.** Favoured. The pattern caps stack depth at the driver loop
  plus one step. The recursive depth moves out of native frames.
- **Latency.** Sacrificed in many hot paths. Each bounce introduces a branch,
  an allocation or closure capture in common implementations, and often weaker
  optimizer visibility than a local loop.
- **Heap pressure.** Sacrificed. Every delayed step may allocate a thunk, enum
  value, boxed continuation, or captured environment.
- **Coupling.** Mixed. Recursive functions become coupled to the trampoline
  protocol, but callers can become decoupled from stack limits.
- **Consistency.** Favoured when all participants return the same `Step<T>`
  shape. It becomes hard for one branch to accidentally recurse directly if
  the compiler requires the step type.
- **Operability.** Mixed. Stack traces become shallower and less informative,
  while explicit counters in the driver can expose depth, bounce count, and
  final state.
- **Cost.** Sacrificed in code size and runtime work. A plain recursive
  function becomes a small interpreter.
- **Team topology.** Favoured for shared libraries that serve many application
  teams. The library can promise stack safety without asking each caller to
  audit recursion depth.
- **Cognitive load.** Sacrificed at the implementation boundary. New readers
  must learn the step protocol, the driver, and the rule that recursive
  branches return the next step rather than calling it.

The pattern pays for stack safety by trading native call frames for explicit
heap values. That exchange is sound when unbounded depth is a real input
property. It is wasteful when the depth is naturally small or when the runtime
already performs the needed tail-call elimination.

Two forces deserve extra attention in shared libraries. The first is API
stability. Once a public function returns `Step<T>` or `Eval<T>`, callers may
begin composing that value rather than running it at once. That can be a good
library design, but it is harder to undo than an internal loop. The second is
failure containment. A driver can add a max-step limit and convert runaway
recursion into a typed error, but that choice changes the function contract.
For pure library code, a step limit may be wrong because it turns a total
computation over large data into a partial one. For request-facing code, the
same limit may be the right defense against resource exhaustion.

Debugging pressure moves in both directions. Removing deep native frames makes
one class of crash disappear. It also removes a familiar view of "how did I get
here". Mature trampoline code compensates with logical frame names, step
counts, and bounded breadcrumbs. Without those, the pattern can feel like it
made failures less visible even while it made them less frequent.

## 4. Applicability and non-applicability

Reach for Trampolining when these conditions hold.

- A recursive or mutually recursive computation can run deeper than the native
  stack on real inputs.
- The next action can be represented as data or as a zero-argument function.
- The result is synchronous and deterministic enough for a local driver loop.
- The runtime lacks proper tail calls for the specific call graph.
- You need a stack-safe `flatMap`, visitor, parser, fold, evaluator, or free
  monad interpreter.
- You need to preserve a recursive model for clarity, but deploy on a runtime
  that charges stack frames for each call.
- You can place all recursive exits behind one return type such as `Done<T>` or
  `Call<T>`.

Do NOT reach for Trampolining in these cases.

- **A plain loop is clearer.** If the state is a small tuple and the control
  graph is one self-recursive function, rewrite it as `while`, `for`, or a
  local loop. The trampoline adds allocation and protocol noise with no new
  behavior.
- **The language promises proper tail recursion for the call shape.** Scheme
  implementations are required by R5RS to support an unbounded number of active
  tail calls
  (https://groups.csail.mit.edu/mac/ftpdir/scheme-reports/r5rs-html.old/r5rs_22.html,
  verified 2026-08-02). In that setting a source-level trampoline often repeats
  what the language already supplies.
- **The computation is naturally asynchronous.** If each step waits on I/O,
  timers, or remote services, an async runtime, stream, actor, or scheduler is
  the better control mechanism.
- **You depend on full native stack traces for auditing.** The trampoline
  collapses recursive frames into a driver loop. That can break diagnostic
  workflows that inspect stack depth or stack frame identity.
- **Stack-sensitive security checks are part of the platform contract.**
  Bjarnason notes that the JVM exposes stacks for inspection and permission
  checks, among other reasons general tail calls are difficult there
  (https://blog.higher-order.com/assets/trampolines.pdf, verified 2026-08-02).
  Moving control to heap values can change what a stack-based checker sees.
- **You need preemptive fairness.** A synchronous trampoline can monopolize a
  thread until it finishes. Use a scheduler with yield points when fairness
  across tasks matters.
- **You are hiding an algorithmic problem.** A trampoline prevents stack
  overflow. It does not make an exponential recursion linear, and it does not
  remove duplicate work.
- **Final values may be callables and the protocol cannot distinguish them.**
  Clojure's `trampoline` calls any returned function until a non-function
  appears, so a function that is meant to be the final result must be wrapped
  (https://clojure.github.io/clojure/clojure.core-api.html, verified
  2026-08-02).

## 5. Structure

The core participants are small.

- **Recursive step producer.** A function that formerly called itself or a peer
  function. It now returns a step value. A base case returns `Done(result)`. A
  recursive case returns `Call(() => next(...))`, or an equivalent token.
- **Step value.** The protocol value. It has at least two variants: final value
  and delayed next action. Richer versions add `FlatMap`, `Suspend`, `Raise`,
  or `Yield`.
- **Thunk.** A zero-argument delayed computation used by a `Call` step. It
  captures the arguments for the next recursive function without running it.
- **Trampoline driver.** A loop that owns the native stack. It repeatedly
  unwraps steps until it reaches `Done`.
- **Continuation, optional.** A function from one completed value to the next
  step. Monadic trampolines store continuations so that `flatMap` chains remain
  stack-safe.
- **Instrumentation, optional.** Counters and callbacks attached to the driver
  for bounce count, max steps, cancellation, and tracing.

The dependency direction is deliberate. Recursive functions depend on the step
protocol. The driver depends on the step protocol. Callers depend only on the
driver's final result. The driver never needs domain knowledge, and the domain
functions do not own the loop.

## 6. ASCII structure diagram

```text
        Caller
          |
          v
   +----------------+
   | run(step0)     |
   | Trampoline     |
   | driver loop    |
   +--------+-------+
            |
            | inspect Step<T>
            v
   +----------------+       thunk       +----------------------+
   | Step<T>        | ----------------> | Recursive producer   |
   | Done(value)    |                   | even, odd, parse...  |
   | Call(thunk)    | <---------------- | returns Step<T>      |
   +----------------+      next Step    +----------------------+
            |
            | Done
            v
       final value

   Native stack depth belongs to run(). Logical recursion depth belongs
   to Step values and thunks on the heap.
```

## 7. Dynamics

At runtime, Trampolining is a small interpreter loop. The producer builds the
first step. The driver inspects that step. If it is complete, the driver returns
the value. If it is delayed, the driver invokes the thunk. The thunk computes
one logical transition and returns the next step. The driver repeats.

```text
Caller                 Driver                  Producer
  |                      |                         |
  | step0 = even(4)      |                         |
  |----------------------------------------------->|
  |                      |<----- Call(() => odd(3))|
  | run(step0)           |                         |
  |--------------------->|                         |
  |                      | invoke thunk            |
  |                      |------------------------>|
  |                      |<----- Call(() => even(2))
  |                      | invoke thunk            |
  |                      |------------------------>|
  |                      |<----- Call(() => odd(1))
  |                      | invoke thunk            |
  |                      |------------------------>|
  |                      |<----- Call(() => even(0))
  |                      | invoke thunk            |
  |                      |------------------------>|
  |                      |<----- Done(true)        |
  |<---------------------| true                    |

  Each logical call returns before the next logical call begins.
  The native stack does not grow with the parity chain.
```

A monadic trampoline changes the dynamic picture by storing continuations
instead of asking the host stack to remember them. Bjarnason's paper shows why
a naive `flatMap` can still overflow, then introduces an internal `FlatMap`
case and right-association to keep evaluation productive without a growing call
stack
(https://blog.higher-order.com/assets/trampolines.pdf, verified 2026-08-02).

## 8. Implementation variants

**Thunk-returning function.** The smallest variant returns either a final value
or a zero-argument function. Clojure's `trampoline` follows this shape: it calls
the initial function, calls returned functions with no arguments while functions
keep appearing, then returns the first non-function value
(https://clojure.github.io/clojure/clojure.core-api.html, verified
2026-08-02). This form is compact in dynamic languages. Its main risk is
ambiguity when a function is a valid final result.

**Tagged step type.** Statically typed code usually defines `Done<T>` and
`Call<T>`. This avoids ambiguity, gives exhaustiveness checks in languages with
sealed types, and makes the final result type explicit. TypeScript, Rust, Go,
and Swift examples in this entry use this style.

**Continuation trampoline.** A richer step type adds `FlatMap` or an explicit
continuation stack. This is the form needed for stack-safe monadic composition,
where many binds can be chained before evaluation. Cats `Eval` exposes
stack-safe `map` and `flatMap` through an internal trampoline
(https://typelevel.org/cats/api/cats/Eval.html, verified 2026-08-02).

**Free monad trampoline.** A trampoline can be represented as a free monad over
zero-argument functions. Bjarnason generalizes from a trampoline to free monads
and uses that path to model stackless Scala programs
(https://blog.higher-order.com/assets/trampolines.pdf, verified 2026-08-02).
This form is valuable when the program is also an interpreter or embedded DSL.
It is heavier than a tagged `Done` or `Call`.

**Scheduler trampoline.** The driver can interleave several computations rather
than run one to completion. Ganz, Friedman and Wand's "Trampolined Style"
frames the scheduler as the central point that runs discrete pieces of work.
That variant begins to overlap with cooperative multitasking. It needs fairness
rules, cancellation, and queue bounds.

**Compiler or transformation pass.** A source-to-source compiler can introduce
trampolines mechanically. Minamide's "Selective Tail Call Elimination" studies
where trampolines are needed and where ordinary calls can remain. That variant
belongs in compilers and code generators rather than hand-written application
code.

Engineering judgement. Pick the smallest variant that closes the stack-safety
risk. Most application code needs a tagged `Done` and `Call`. Library authors
writing `flatMap` need the continuation form. Compiler authors need effect or
control-flow analysis.

**Loop plus explicit state machine.** Some code that first appears to need a
trampoline can be rewritten as an enum state and a loop. For example, `even`
and `odd` can become `state = Even` or `state = Odd` inside `while n > 0`.
This is the fastest form, and it is often best when the state machine has few
states. It becomes harder to maintain when each state carries distinct local
data, because all local data must be merged into one state record.

**Explicit work list.** Tree, graph, and directory traversals often need a
stack-safe walk rather than a stack-safe call graph. An explicit vector or
deque of pending nodes can be clearer than thunks. It gives direct control over
order, memory, and cycle checks. Use Trampolining when the pending operation is
better represented as "resume this function with these arguments" than as
"visit this node later".

**Hybrid threshold.** A performance-sensitive library can recurse directly for
small depths and switch to a trampoline after a threshold. This avoids overhead
on common shallow inputs while preserving stack safety for large ones. The cost
is complexity. The boundary must be tested, and both paths must produce the
same result. Engineering judgement: do this only when measurements show the
trampoline overhead matters on real workloads.

**Defunctionalized trampoline.** Instead of storing closures, represent each
next action as a data constructor with fields. The driver switches on the
constructor and executes the matching transition. This can reduce accidental
capture of large environments and can make tracing easier, because each case
has a name. It is more verbose than thunks and less open to extension.

## 9. Known production uses

**Clojure core `trampoline`.** Clojure ships `clojure.core/trampoline` in the
core namespace. The official API describes it as a function that converts
algorithms requiring mutual recursion without stack consumption, by repeatedly
calling returned functions until a non-function value appears. The same page
records that it was added in Clojure 1.0
(https://clojure.github.io/clojure/clojure.core-api.html, verified
2026-08-02).

**Scala standard library `TailCalls`.** Scala ships
`scala.util.control.TailCalls`. The Scala 3 API documentation says that methods
exported by this object implement tail calls through trampolining, and that
tail-calling methods return either `done` or `tailcall`, producing a `TailRec`
whose result is obtained through `result`
(https://scala-lang.org/api/3.x/scala/util/control.html, verified
2026-08-02).

**Typelevel Cats `Eval`.** Cats ships `cats.Eval`. The Typelevel guide says
`Eval` is designed for stack safety at all times using trampolining, and the
API page says `map` and `flatMap` use an internal trampoline to avoid stack
overflows
(https://typelevel.org/cats/datatypes/eval.html, verified 2026-08-02;
https://typelevel.org/cats/api/cats/Eval.html, verified 2026-08-02).

**Scheme implementations by language contract.** Scheme is not a production use
of a library trampoline, but it is the production language family that explains
the target behavior. R5RS requires proper tail recursion and defines it as
support for an unbounded number of active tail calls
(https://groups.csail.mit.edu/mac/ftpdir/scheme-reports/r5rs-html.old/r5rs_22.html,
verified 2026-08-02). A trampoline exists mainly to approximate that property
in runtimes where the property is not supplied by the language.

## 10. Consequences

Positive consequences.

- Deep recursion can complete without consuming native stack frames for every
  logical step.
- Mutual recursion becomes portable across runtimes that optimize only direct
  self recursion or no recursion at all.
- The driver loop creates a single location for step limits, cancellation,
  tracing, and bounce counters.
- A library can give stack-safety guarantees for composed values such as
  `flatMap` chains, folds, interpreters, and visitors.
- Recursive code can keep a direct domain shape. The `even` function can still
  name `odd`; the parser can still name the next grammar state.

Negative consequences.

- The program allocates step values or closures that a plain loop may avoid.
- Debugging by stack trace becomes less direct because the call stack mostly
  shows the driver.
- The protocol infects return types. Functions that used to return `T` now
  return `Step<T>` or a library equivalent.
- Latency can rise in tight loops due to dispatch, allocation, and lost inlining
  opportunities.
- A synchronous driver can monopolize a thread unless it has a step budget,
  yield policy, or caller-controlled cancellation.
- Exceptions thrown inside thunks may point at the driver unless the program
  attaches logical trace context.
- It can hide algorithmic blowups. A stack-safe exponential recursion is still
  exponential.

Engineering judgement. The main consequence is not performance alone. It is the
change in control ownership. The stack no longer owns pending calls. The driver
does. That gives you measurement and limits, but it also makes you responsible
for them.

## 11. Failure modes and misuse

Engineering judgement. These are common operational failures in hand-written
and library trampolines.

- **Symptom.** The program still throws `RecursionError`, `StackOverflowError`,
  or a native stack overflow on large input.
  **Cause.** One recursive branch calls the next function directly instead of
  returning `Call(() => next(...))`.
  **Fix.** Make the recursive functions return a single step type and let the
  compiler reject direct `T` returns. Add a depth test that exceeds the native
  stack by a wide margin.

- **Symptom.** Memory grows with input depth until the process pauses or dies.
  **Cause.** Each thunk captures a large object graph, or the driver stores all
  visited steps for logging.
  **Fix.** Capture small scalar state, pass indexes instead of slices, and log
  aggregate counters rather than retaining every step.

- **Symptom.** CPU time is much worse than the loop version for shallow inputs.
  **Cause.** The algorithm did not need stack protection, but now pays closure
  allocation and dispatch per step.
  **Fix.** Keep a plain loop for bounded hot paths. Use Trampolining only on
  paths where depth is input-controlled.

- **Symptom.** A function meant to return a callback never returns because the
  trampoline keeps calling the callback.
  **Cause.** The protocol treats any callable result as another bounce, as in
  the Clojure-style dynamic variant.
  **Fix.** Use tagged `Done(callback)` and `Call(thunk)`, or wrap callable
  final values in a non-callable container.

- **Symptom.** A `flatMap` chain overflows even though every branch returns a
  trampoline.
  **Cause.** The monadic implementation runs the left side by recursive calls
  or builds left-associated continuation towers.
  **Fix.** Store continuations as data, right-associate binds, and test a long
  left-associated chain. Bjarnason's section 4.3 covers this exact pitfall
  (https://blog.higher-order.com/assets/trampolines.pdf, verified
  2026-08-02).

- **Symptom.** Logs show one request thread running for seconds with no async
  handoff, while other work waits.
  **Cause.** A synchronous trampoline drains unbounded work in one turn.
  **Fix.** Add a max-step budget, cooperative yield, cancellation check, or move
  the workload to a background executor.

- **Symptom.** Operators cannot tell which logical recursion path failed.
  **Cause.** Native stack traces point at the driver and the thunk wrapper, not
  at every logical call.
  **Fix.** Add logical frame names to the step value or trace span, and record
  the last few state transitions in a bounded ring buffer.

## 12. Trade-off matrix

```text
Alternative                 Stack       Heap        Latency     Clarity
Plain while loop            flat        lowest      lowest      high for simple state
Native proper tail calls    flat        lowest      lowest      high if language has it
Trampolining                flat        higher      higher      medium, protocol visible
Continuation-passing style  depends     higher      higher      low without helpers
Explicit work stack         flat        medium      medium      high for tree traversal
Async event loop            flat        higher      higher      high for I/O workflows

Alternative                 Mutual recursion       Composition       Diagnostics
Plain while loop            weak                   weak              simple stack
Native proper tail calls    strong                 runtime-specific runtime stack
Trampolining                strong                 strong           needs logical trace
Continuation-passing style  strong                 strong           hard stack shape
Explicit work stack         medium                 weak              visible state
Async event loop            strong for async       strong for async  task traces
```

The alternatives are not ranked universally. A plain loop is better for a
single numeric accumulator. An explicit work stack is better for many tree and
graph traversals because it names the pending nodes directly. Native proper
tail calls are better when the language gives them for the call graph. A
trampoline is the portable middle ground when recursive structure matters and
the runtime stack is the constraint.

## 13. Related and incompatible patterns

**Tail Recursion** is the closest relative. Trampolining is often used to
simulate the space behavior of tail recursion when the host does not optimize
the needed calls. Tail Recursion replaces the current call with the next call.
Trampolining returns the next call as data to a loop.

**Continuation-Passing Style** composes with Trampolining. CPS makes the
remainder of the computation explicit as a continuation. A trampoline can store
that continuation on the heap and run it later. The combination is powerful but
harder to read than direct style.

**Free Monad** generalizes the continuation trampoline. Bjarnason shows the
connection between trampolines and free monads in "Stackless Scala With Free
Monads"
(https://blog.higher-order.com/assets/trampolines.pdf, verified 2026-08-02).
Use the free monad form when the steps are also an interpretable program.

**Interpreter** composes with Trampolining. The driver is an interpreter for the
step language. A parser, workflow, or DSL can return instructions to the driver
rather than call through host recursion.

**Iterator** is a cousin for pull-based traversal. An iterator also externalizes
progress state. It is often better when the consumer wants one element at a
time. A trampoline is better when the consumer wants one final value from a deep
call graph.

**Explicit Work Stack** can replace Trampolining. A depth-first tree walk can
often use a vector of pending nodes. That form gives clearer memory accounting
than a chain of thunks.

**Native Tail Calls Required** conflicts with Trampolining as a portability
plan. If a module's contract depends on host-language tail-call semantics for
performance or stack inspection, a heap trampoline changes the execution model.

**Stack-Sensitive Security Checks** can conflict. When a platform reads the
native stack for permission or auditing, turning logical calls into heap data
can hide frames from that mechanism. Treat that as a platform review item, not
as an automatic ban.

## 14. Refactoring path in and out

To introduce Trampolining:

1. Find the failing recursive path with a depth test that reproduces the stack
   failure.
2. Identify the recursive exits. Mark each branch that calls the same function
   or a peer function.
3. Define a step type with `Done<T>` and `Call<T>`. In dynamic code, prefer a
   tagged shape when callable final values are possible.
4. Change the recursive function's return type from `T` to `Step<T>`.
5. Wrap base cases in `Done(value)`.
6. Wrap recursive calls in `Call(() => recursiveCall(nextState))`.
7. Add a driver loop that repeatedly invokes `Call` thunks until it sees
   `Done`.
8. Replace external calls to the recursive function with `run(function(...))`.
9. Add a test with depth far above the native stack limit.
10. Add bounce count and max-step metrics if the computation can be triggered
    by external input.

During migration, keep the old direct recursive function private for a short
period only if it helps with equivalence tests. Do not expose both public paths
unless callers need an explicit speed-versus-depth choice. Dual public APIs
invite drift: one branch receives bug fixes, the other keeps the old behavior.

For mutually recursive functions, convert the whole strongly connected group in
one change. A half-converted pair is a common source of false confidence:
`even` returns `Call`, but one branch inside `odd` still calls `even` directly.
Types can catch this in statically typed languages when every branch must
return `Step<T>`. In dynamic languages, the deep-depth test is the backstop.

For code review, ask three concrete questions. Does every recursive edge return
a delayed step rather than call the next function? Does the thunk capture only
the state needed for the next step? Does the driver have the right policy for
limits, cancellation, and tracing at this boundary? Those questions find most
of the real defects without arguing about the pattern name.

To remove Trampolining:

1. Prove the depth is bounded by data validation, schema limits, or a stronger
   algorithmic invariant.
2. Measure the trampoline overhead in the hot path.
3. Replace `Step<T>` returns with direct returns in one function at a time.
4. Convert self-recursive accumulator loops to `while` or `for`.
5. Convert tree traversals to explicit work stacks when pending nodes are the
   real state.
6. Keep the deep-depth regression test and change its expected behavior to the
   new limit policy if unbounded depth is no longer accepted.

Related named refactorings include Replace Recursion with Iteration, Substitute
Algorithm, Extract Function, and Introduce Parameter Object. In this repo, the
closest family neighbors are Tail Recursion, Function Composition, Monad, and
Interpreter.

Removal should also consider caller habits. If callers have learned to compose
the step value, removing it is an API break. If the trampoline is internal and
callers see only `T`, removal is a local performance refactor. That is another
reason to hide the step protocol unless callers truly need to build or combine
steps themselves.

## 15. Testing and verification

Engineering judgement. A trampoline deserves tests for behavior and for the
resource property it claims.

Start with equivalence tests. Run a small input through the original recursive
version and the trampolined version, then compare the final value. Property
tests work well for arithmetic folds, parser acceptors, and tree traversals.

Add stack-depth tests. Pick an input depth that fails with ordinary recursion
on at least one developer machine, then run the trampolined version at that
depth. The exact native stack limit varies by runtime and flags, so the test
should assert completion of the trampolined path rather than assert failure of
the direct recursive path in CI.

Add branch coverage for every step variant. `Done` with a final value, `Call`
with one next step, long `Call` chains, thrown exceptions inside a thunk, and
callable final values if the language permits them.

For monadic trampolines, add associativity-shape tests. Build a large
left-associated chain and a large right-associated chain. Both should produce
the same result without stack overflow. This catches the failure mode described
in Bjarnason's section 4.3
(https://blog.higher-order.com/assets/trampolines.pdf, verified 2026-08-02).

For production entry points, test budgets. A malicious or broken input can
produce an infinite bounce chain. The driver should be testable with a max-step
limit or cancellation token. The test should prove that the limit returns a
controlled error rather than hanging.

Test doubles are simple. A fake step producer can return `Done`, one `Call`, a
chain of `Call` values, or a never-ending `Call`. A trace sink can record the
last N logical frames. A clock is rarely needed unless the driver yields or
enforces time budgets.

Performance tests should separate three cases. The first is shallow input,
where a direct loop may be faster. The second is near-stack-limit input, where
the direct recursive version may still pass but has little safety margin. The
third is far-beyond-stack input, where the trampoline's value is not speed but
completion. Reporting all three prevents a benchmark from hiding the reason the
pattern exists.

Fuzzing can be valuable for parsers and evaluators. Generate nested input with
varied depth, width, and invalid branches. Assert that invalid input returns a
controlled parse or validation error rather than an uncontrolled stack or
memory failure. Pair fuzzing with a step budget so the fuzzer can discover
runaway cases without hanging the test process.

## 16. Observability signals

Engineering judgement. Native stack depth stops being the main signal once a
trampoline is in place. Expose logical progress instead.

Record `trampoline.steps` as a counter per run. A healthy value should match
input size or another predictable bound. A failing value rises without
finishing, or reaches a configured max-step limit.

Record `trampoline.max_logical_depth` when the driver knows depth, or record
the highest state index processed. For mutual recursion, record logical state
names such as `parse_array`, `parse_value`, or `odd`.

Record `trampoline.duration_ms` and, if possible, separate step execution time
from driver overhead. A sudden rise in driver overhead points at too many tiny
steps or allocation pressure.

Record `trampoline.allocations` or heap usage when the runtime exposes it. A
healthy run should allocate roughly one small step per bounce in a simple
implementation. A failing run captures large objects or retains step history.

Trace the first logical state, the last logical state, the final outcome, and a
bounded ring buffer of recent states on error. Do not log every bounce by
default. A request with one million steps would produce one million log lines.

Dashboards should show bounce count distribution, max-step limit hits, duration
percentiles, cancellation count, and error count by logical state. Alert on
limit hits and on sharp changes in steps per input unit.

For developer diagnostics, expose a debug mode that records a bounded logical
trace. A useful record is the first state, the last state, the current depth or
index, and the last 20 state names. Avoid a full trace by default. Full traces
can be larger than the original input and can retain data that should have been
released.

For capacity planning, track the ratio between input size and bounce count. A
parser that normally takes one to three bounces per token but suddenly takes
hundreds per token has likely entered a pathological grammar branch. A tree
walk whose bounce count exceeds node count by a wide factor may be revisiting
nodes. These ratios are more stable than raw duration because hardware and
process load change over time.

## 17. Security and privacy implications

Engineering judgement. Trampolining is mainly a control-flow pattern, but it
changes denial-of-service exposure and diagnostic data handling.

The main security risk is unbounded synchronous work. A hostile input can drive
millions of steps without growing the stack, which means the process may no
longer fail fast with stack overflow. That is a feature for valid deep input
and a risk for adversarial input. Add max-step limits, input depth limits,
timeouts, and cancellation for externally supplied data.

Heap pressure is the second risk. If thunks capture request bodies, credentials,
tenant data, or large AST nodes, the trampoline can retain sensitive data longer
than a direct loop would. Capture indexes, identifiers, or immutable small state
where possible. Clear references in long-lived drivers after completion.

Stack-based auditing can change. When a platform checks permissions or records
call stacks, a trampoline collapses logical calls into a loop. Bjarnason notes
that JVM stack inspection and security model details are part of why general
tail calls are difficult on that platform
(https://blog.higher-order.com/assets/trampolines.pdf, verified 2026-08-02).
If your security model depends on stack frames, review the trampoline with the
platform owner.

Error reporting can leak logical state. A ring buffer of recent parser states
or workflow states may contain user input. Redact values before attaching them
to traces. Prefer state names and sizes over full payloads.

The pattern is silent on authentication, authorization, encryption, and network
boundaries. It does not grant or remove access by itself. Its security relevance
comes from how long work can run, what closures retain, and what diagnostics
emit.

Review cancellation semantics carefully. If the driver checks cancellation only
between bounces, a single thunk can still run for a long time. Keep each thunk
small, or make long thunks check cancellation internally. A trampoline is only
as interruptible as its largest step.

Review tenant isolation when a driver is shared. A global queue or shared
scheduler variant can let one tenant's deep computation delay another tenant's
work. A per-request synchronous driver avoids cross-tenant queues but can still
consume the request thread. The right design depends on the service boundary,
but the risk should be visible in design review.

Finally, review exception wrapping. If the driver catches exceptions to attach
logical trace context, it must not swallow security exceptions or convert them
into ordinary validation failures. Preserve the original exception type where
callers rely on it, and redact logical context before reporting it.

## Code examples

The following samples use Python, TypeScript, Go, and Rust because those
toolchains were available locally. Java was omitted because `javac` was not
available in this environment. Each sample computes parity through mutual
recursion without growing the native stack.

Python:

```python
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar, Union

T = TypeVar("T")

@dataclass(frozen=True)
class Done(Generic[T]):
    value: T

@dataclass(frozen=True)
class Call(Generic[T]):
    thunk: Callable[[], "Step[T]"]

Step = Union[Done[T], Call[T]]

def run(step: Step[T]) -> T:
    while isinstance(step, Call):
        step = step.thunk()
    return step.value

def even(n: int) -> Step[bool]:
    if n == 0:
        return Done(True)
    return Call(lambda: odd(n - 1))

def odd(n: int) -> Step[bool]:
    if n == 0:
        return Done(False)
    return Call(lambda: even(n - 1))

print(run(even(100000)))
```

TypeScript:

```typescript
type Step<T> = Done<T> | Call<T>;

type Done<T> = {
  tag: "done";
  value: T;
};

type Call<T> = {
  tag: "call";
  thunk: () => Step<T>;
};

function done<T>(value: T): Step<T> {
  return { tag: "done", value };
}

function call<T>(thunk: () => Step<T>): Step<T> {
  return { tag: "call", thunk };
}

function run<T>(step: Step<T>): T {
  while (step.tag === "call") {
    step = step.thunk();
  }
  return step.value;
}

function even(n: number): Step<boolean> {
  return n === 0 ? done(true) : call(() => odd(n - 1));
}

function odd(n: number): Step<boolean> {
  return n === 0 ? done(false) : call(() => even(n - 1));
}

console.log(run(even(100000)));
```

Go:

```go
package main

import "fmt"

type Step[T any] interface {
	isStep()
}

type Done[T any] struct {
	Value T
}

func (Done[T]) isStep() {}

type Call[T any] struct {
	Thunk func() Step[T]
}

func (Call[T]) isStep() {}

func Run[T any](step Step[T]) T {
	for {
		switch s := step.(type) {
		case Done[T]:
			return s.Value
		case Call[T]:
			step = s.Thunk()
		}
	}
}

func Even(n int) Step[bool] {
	if n == 0 {
		return Done[bool]{Value: true}
	}
	return Call[bool]{Thunk: func() Step[bool] { return Odd(n - 1) }}
}

func Odd(n int) Step[bool] {
	if n == 0 {
		return Done[bool]{Value: false}
	}
	return Call[bool]{Thunk: func() Step[bool] { return Even(n - 1) }}
}

func main() {
	fmt.Println(Run[bool](Even(100000)))
}
```

Rust:

```rust
enum Step<T> {
    Done(T),
    Call(Box<dyn FnOnce() -> Step<T>>),
}

fn run<T>(mut step: Step<T>) -> T {
    loop {
        match step {
            Step::Done(value) => return value,
            Step::Call(thunk) => step = thunk(),
        }
    }
}

fn even(n: u32) -> Step<bool> {
    if n == 0 {
        Step::Done(true)
    } else {
        Step::Call(Box::new(move || odd(n - 1)))
    }
}

fn odd(n: u32) -> Step<bool> {
    if n == 0 {
        Step::Done(false)
    } else {
        Step::Call(Box::new(move || even(n - 1)))
    }
}

fn main() {
    println!("{}", run(even(100000)));
}
```

## 18. References

- Richard Kelsey, William Clinger and Jonathan Rees, editors. *Revised(5)
  Report on the Algorithmic Language Scheme*, section 3.5, "Proper tail
  recursion". https://groups.csail.mit.edu/mac/ftpdir/scheme-reports/r5rs-html.old/r5rs_22.html,
  verified 2026-08-02.
- Steven D. Ganz, Daniel P. Friedman and Mitchell Wand. "Trampolined Style".
  *Proceedings of the Fourth ACM SIGPLAN International Conference on Functional
  Programming*, 1999, pages 18 to 22.
- Yasuhiko Minamide. "Selective Tail Call Elimination". *Static Analysis,
  10th International Symposium*, 2003, section 2.
- Runar Oli Bjarnason. "Stackless Scala With Free Monads". Scala Workshop
  2012, sections 3 and 4.
  https://blog.higher-order.com/assets/trampolines.pdf, verified 2026-08-02.
- Scala standard library API. `scala.util.control.TailCalls`, Scala 3 API.
  https://scala-lang.org/api/3.x/scala/util/control.html, verified
  2026-08-02.
- Clojure API documentation. `clojure.core/trampoline`, Clojure v1.12.4 API.
  https://clojure.github.io/clojure/clojure.core-api.html, verified
  2026-08-02.
- Typelevel Cats documentation. "Eval".
  https://typelevel.org/cats/datatypes/eval.html, verified 2026-08-02.
- Typelevel Cats API documentation. `cats.Eval`.
  https://typelevel.org/cats/api/cats/Eval.html, verified 2026-08-02.
