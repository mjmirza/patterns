---
name: Function Composition
slug: function-composition
family: 16-functional
category: Functional
aliases: [Composition, Compose, Pipeline, Function Pipeline, Unary Composition]
first_described: "Standard mathematical operation, established in functional programming practice"
maturity: canonical
related: [higher-order-function, partial-application, currying, pipeline, functor, monad, decorator, chain-of-responsibility]
incompatible_with: [hidden-side-effects, order-dependent-global-state, untyped-dynamic-pipeline]
verified: 2026-08-02
---

# Function Composition

## 1. Name, aliases, and lineage

The canonical name is Function Composition. In mathematics, composition connects
two functions when the output of one has the type required by the input of the
next. In programming notation, if `parse` has shape `Raw -> Parsed` and
`price` has shape `Parsed -> Money`, their composition has shape `Raw -> Money`.
The composed operation receives one raw value, applies `parse`, then applies
`price` to the parsed result.

Common aliases are **composition**, **compose**, **function pipeline**,
**pipeline**, and **unary composition**. The word pipeline is common when the
notation reads left to right. The word compose is common when the notation reads
right to left, as in Haskell's `(.)` operator. The Haskell tutorial gives the
type of `(.)` as `(b -> c) -> (a -> b) -> (a -> c)` and defines `f . g` as a
function that applies `g` first and then `f`
(https://www.haskell.org/tutorial/functions.html, verified 2026-08-02). Haskell
Prelude documentation also names `(.)` as function composition with the same
type shape
(https://www.haskell.org/hugs/pages/libraries/base/Prelude.html, verified
2026-08-02).

The lineage is older than software design pattern catalogs. Composition is a
basic operation on mathematical functions, and functional programming made that
operation available as an ordinary programming tool through first-class
functions. This entry treats Function Composition as a canonical functional
programming pattern rather than as a claim about one inventor. Where this entry
mentions a named programming API, it cites that API directly.

The name is overloaded in two common ways. First, "object composition" means
building an object from contained objects rather than from inheritance. That is
a different design idea. Second, "component composition" in UI frameworks can
mean nesting components, passing children, or combining render functions. Some
of that code also uses Function Composition, but the pattern here is narrower:
construct a new callable by connecting existing callables through matching input
and output types.

The smallest lawful equation is:

```text
compose(f, g)(x) == f(g(x))
```

That equation also explains why direction causes confusion. In mathematical and
Haskell-style notation, `f . g` reads left to right as names, but data flows
right to left. In pipeline notation, `pipe(g, f)` reads in data-flow order.
Both spell the same composition. The choice is notation, not a different
pattern.

## 2. Problem and context

A program has several small transformations that must run in a fixed order.
Each transformation is useful on its own, but the product behavior is the chain.
A request body is decoded, validated, normalized, priced, and converted into a
response model. A log event is redacted, enriched, serialized, and emitted. A
string is trimmed, lowercased, parsed, and mapped to a domain value. Without the
pattern, the chain appears as nested calls, temporary variables, or repeated
wrapper functions.

Nested calls hide the order from many readers:

```text
render(price(validate(decode(raw))))
```

Temporary variables make the order explicit, but they name intermediate values
whose only purpose is to connect one step to the next:

```text
decoded = decode(raw)
valid = validate(decoded)
priced = price(valid)
return render(priced)
```

Function Composition extracts the connection itself. The chain becomes a value:

```text
toResponse = compose(render, price, validate, decode)
return toResponse(raw)
```

The context matters. Function Composition is at its best when each step has one
primary input and one primary output, the order is stable, and the intermediate
values do not deserve names in the surrounding code. It works for pure
functions, but it also appears in disciplined effectful code, such as middleware
or stream operators, where the framework defines how effects are sequenced.
RxJS documents pipeable operators as functions from one Observable to another
Observable, and its `pipe` helper returns a unary function that feeds each
result into the next function
(https://rxjs.dev/api/index/function/pipe, verified 2026-08-02).

The pattern should not be confused with a larger workflow engine. Composition
does not choose a branch by business rule, retry failed steps, persist state,
schedule work, or compensate a completed action. Those behaviors can be placed
inside composed steps, but the composition itself is the small mechanism that
connects compatible callables.

The reason this pattern belongs in a pattern catalog is not syntax. Many
languages already have a compose operator, a pipe method, or a library helper.
The reusable idea is how to shape local code: build small functions with clear
input and output contracts, connect them explicitly, keep policy about order in
one place, and preserve the ability to test each step outside the chain.

A second problem appears during change. A sequence of calls often starts life in
one handler. Six months later the same sequence appears in an import job, a CLI
tool, and a test fixture. One copy trims before decoding, another decodes before
trimming, and a third silently skips normalization because the local author did
not know it was part of the business rule. Function Composition gives the
sequence a home. The team can ask whether `rawToCommand` is the approved path
from wire data to command data, instead of asking every call site to remember a
private set of steps.

The pattern also changes how failure policy is discussed. In direct code, a
reader may see `try`, `if`, and `return` mixed with the transformation steps. In
composed code, the failure policy must either be part of each step's return
type, part of the composition helper, or visible in a surrounding adapter. That
pressure is useful when the team wants consistency. It is harmful when the team
needs local escape hatches. A validation chain that returns `Result` can make
all failures look alike. That is good for a form parser and poor for an
incident response workflow where each failure needs its own escalation route.

## 3. Forces

Engineering judgement. This dimension weighs trade-offs seen in codebases that
use composition heavily. The named language and library facts in this entry are
cited where they appear.

- **Coupling.** Favoured when each step depends only on the previous step's
  output type and the next step's input type. Sacrificed when the chain hides a
  shared mutable dependency captured by closures.
- **Latency.** Usually neutral for ordinary application code. It can be
  negative in hot loops because each step may add a call frame, closure
  allocation, or missed inline opportunity. It can be positive when a runtime or
  library fuses adjacent transforms, but that is a library feature, not a
  universal property of the pattern.
- **Consistency.** Favoured because the chain is built once and reused. A
  payment normalization pipeline used in three handlers has one order of
  operations, not three hand-written sequences that can drift.
- **Operability.** Sacrificed if the composed function is anonymous and the
  chain has no step names. Favoured if the composition helper records step names,
  timing, and failures.
- **Cost.** Favoured for maintenance when small functions are reused. Sacrificed
  when every one-line expression becomes a named step because the team has turned
  composition into ceremony.
- **Team topology.** Favoured when platform code owns the composition contract
  and product teams contribute steps. Sacrificed when no team owns the type
  boundary between steps, because one changed step can break all downstream
  chains.
- **Cognitive load.** Favoured for readers comfortable with data-flow notation.
  Sacrificed for teams new to higher-order functions, especially when point-free
  code removes argument names that would explain intent.
- **Debuggability.** Favoured when steps are individually testable. Sacrificed
  when a stack trace names only `compose`, `pipe`, or anonymous lambdas.

The pattern chooses explicit connection over explicit intermediate names. That
is a good exchange only when the intermediate names add little meaning.

There is also a force around **type precision**. Composition rewards precise
types because the compiler or reviewer can see whether two steps fit. It
punishes vague types such as `object`, `any`, `dict`, or `map[string]any`
because every adjacent edge now depends on a convention that the type system
cannot check. In dynamic languages that cost can be acceptable for short chains
with strong tests. In long-lived domain code, vague step boundaries tend to
move errors from edit time to runtime.

Another force is **change locality**. Adding a step to a named chain is a local
edit, but changing a step's output type is not local. Every downstream step must
accept the new shape. In return, an upstream change cannot silently bypass a
downstream rule if all callers use the same composed function. The pattern
therefore favors teams that value one named path through a transformation more
than teams that want each caller to tune the sequence freely.

## 4. Applicability and non-applicability

Reach for Function Composition when the following conditions hold.

- A transformation can be expressed as a sequence of unary functions where each
  output type matches the next input type.
- Several call sites need the same ordered chain, and duplication would risk
  drift.
- Each step is worth testing or reusing outside the chain.
- The chain expresses a domain concept, such as `rawEventToMetric` or
  `requestToCommand`, rather than a pile of incidental calls.
- A framework models extension as composed functions, as with Redux store
  enhancers, RxJS pipeable operators, or Koa middleware.
- Error, absence, or asynchronous policy is already represented by the function
  type or the surrounding abstraction. Examples include `Result`, `Option`,
  `Promise`, `Observable`, and middleware `next`.

Explicit non-applicability list.

- **The steps require unrelated inputs.** Composition joins one output to one
  input. If step three also needs the original request, a clock, and a user
  record, use an explicit context object, Reader-style dependency passing, or an
  ordinary function with named parameters.
- **Intermediate values carry business meaning.** If `validatedClaim`,
  `pricedClaim`, and `authorizedClaim` are audit states, keep the names. A
  composed chain that hides legally meaningful states makes review harder.
- **The order changes by runtime policy.** Use Strategy, Chain of
  Responsibility, a rules engine, or a workflow graph when the next step depends
  on data rather than on fixed construction-time order.
- **A step mutates shared state relied on by later steps.** Composition can still
  run such code, but the apparent type contract lies. The real contract is
  hidden in global or captured state.
- **A debugger is the main maintenance tool for the team.** Long anonymous
  chains are awkward when the team depends on step-by-step debugging and stack
  frames do not name domain operations.
- **The language lacks type help and the chain crosses many shapes.** Dynamic
  composition can fail late. Add runtime validation, keep chains short, or use
  named intermediate variables.
- **The chain is a distributed transaction.** Function Composition does not
  provide retries, idempotency, deadlines, compensation, or durable state. Use a
  workflow pattern.
- **The code is clearer as direct calls.** A two-step transformation used once
  may read better as `normalize(parse(raw))` than as a named pipeline.
- **The chain is mostly exception handling.** If the main work is catching,
  mapping, retrying, and classifying exceptions, the code wants an error policy
  abstraction. Plain composition will hide the policy in helper internals.
- **The chain crosses trust boundaries.** Do not mix untrusted plugin code,
  privileged service calls, and private data in one anonymous chain. Use a
  sandboxed plugin protocol or a gateway object with explicit authority checks.
- **The team cannot agree on direction.** A codebase that mixes `compose(c, b,
  a)`, `pipe(a, b, c)`, method chaining, and nested calls for the same kind of
  work creates needless review cost. Pick one local spelling before widening
  use.

## 5. Structure

The structure has five participants.

- **Source value.** The value accepted by the composed function. It may be a
  request, event, string, domain object, or context object.
- **Step function.** A callable with one input and one output. The output must
  be acceptable to the next step. In typed languages the compiler can check this
  relationship. In dynamic languages the composition helper or tests must carry
  the burden.
- **Composition helper.** A function, operator, or method that connects step
  functions and returns a new callable. Examples include Haskell `(.)`, Java
  `Function.andThen`, Redux `compose`, and RxJS `pipe`.
- **Composed function.** The callable returned by the helper. It owns the
  ordered chain and gives the chain a name.
- **Terminal consumer.** The caller that supplies the source value and consumes
  the final output. The terminal consumer should not know the intermediate
  shapes unless those shapes are part of the public contract.

The dependencies point inward. A step knows its own local types and local
policy. The composition helper knows only how to connect callables. The terminal
consumer knows only the outer type of the composed function. That separation is
why the pattern is useful: the chain can be changed by rearranging or replacing
steps without rewriting every caller.

Two structural choices matter in practice. First, the chain may be **right to
left** (`compose(render, price, parse)`) or **left to right** (`pipe(parse,
price, render)`). Second, steps may be **plain** (`A -> B`) or **contextual**
(`Context<A> -> Context<B>`, `Request -> Promise<Response>`, `Observable<A> ->
Observable<B>`). The contextual form is still Function Composition when each
step returns the type expected by the next step.

In a well-factored structure, each participant has one reason to change. The
source value changes when the input contract changes. A step changes when its
local transformation rule changes. The composition helper changes when the
mechanics of connecting callables changes. The composed function changes when
the order or membership of the chain changes. The terminal consumer changes
when the public input or output changes. When those reasons collapse into one
large function, the pattern has not been applied. The code has a named helper
but no separation.

Naming matters because the composed function is the unit that other code sees.
Names such as `pipeline`, `process`, or `handler` are weak unless the surrounding
module supplies the missing context. Prefer names that include both boundary
types or business phases: `csvRowToInvoice`, `requestToCommand`,
`eventToMetric`, `claimToLedgerEntry`. A good name lets the reader ignore the
internal steps until they need detail.

## 6. ASCII structure diagram

```text
             build time

   +------------+     +------------+     +------------+
   | Step A     |     | Step B     |     | Step C     |
   | Raw -> Ok  |     | Ok -> View |     | View -> UI |
   +------------+     +------------+     +------------+
          \                |                 /
           \               |                /
            v              v               v
        +----------------------------------------+
        | Composition helper                     |
        | pipe(A, B, C) or compose(C, B, A)      |
        +----------------------------------------+
                         |
                         v
        +----------------------------------------+
        | Composed function                      |
        | Raw -> UI                              |
        +----------------------------------------+
                         |
                         v
        +----------------------------------------+
        | Terminal consumer                      |
        | calls composed(raw)                    |
        +----------------------------------------+

   Each adjacent edge must agree on type or runtime contract.
```

## 7. Dynamics

At runtime the terminal consumer calls one function. The composed function calls
the first step, passes that result to the next step, and repeats until a final
result is available. If a step throws, returns an error value, cancels, or
short-circuits, the surrounding language or abstraction decides whether later
steps run.

```text
Terminal       Composed fn       decode        validate       render
   |               |               |              |             |
   |-- raw ------->|               |              |             |
   |               |-- raw ------->|              |             |
   |               |<-- decoded ---|              |             |
   |               |-- decoded ------------------>|             |
   |               |<-- valid --------------------|             |
   |               |-- valid ---------------------------------->|
   |               |<-- response -------------------------------|
   |<-- response --|               |              |             |
   |               |               |              |             |

Failure path, one common policy:

Terminal       Composed fn       decode        validate       render
   |               |               |              |             |
   |-- raw ------->|               |              |             |
   |               |-- raw ------->|              |             |
   |               |<-- decoded ---|              |             |
   |               |-- decoded ------------------>|             |
   |               |<-- error --------------------|             |
   |<-- error -----|               |              |             |
   |               |        render is not called                 |
```

The diagram shows the plain synchronous case. In asynchronous composition, the
same shape appears with promises, callbacks, streams, or middleware `next`
calls. Koa middleware functions receive a context and a `next` function, and Koa
documents combining multiple middleware into a single middleware with
`koa-compose`
(https://github.com/koajs/koa/blob/master/docs/guide.md, verified
2026-08-02). That is contextual composition: the visible data is the HTTP
context, while the composed function also controls when downstream middleware
runs.

Order is the failure point. `render after validate after decode` is not the same
as `validate after render after decode`. Most composed functions are not
commutative. Treat order as part of the public behavior.

Lazy and streaming variants change the timing without changing the structure.
An eager chain computes each step before returning. A lazy chain may build a
description of work and run it later. A streaming chain may run the first step
for item one while item two has not arrived. RxJS operator chains fit that
streaming model. The design question is the same in each case: does the output
of this step become the input of the next step under a known sequencing rule?
If yes, Function Composition is present even when the result appears over time.

Cancellation and cleanup deserve explicit treatment in effectful chains. If a
step opens a file, starts a timer, or subscribes to a stream, the composition
contract must say who closes it. Plain synchronous examples do not show that
participant. Production chains should treat cleanup as part of the contextual
type, such as a stream subscription, request context, or resource scope.

## 8. Implementation variants

**Right-to-left compose.** This follows mathematical notation. `compose(c, b,
a)` means "run `a`, then `b`, then `c`." Haskell `(.)` and Redux `compose`
follow this direction. Redux documents `compose` as composing functions from
right to left and returning the final composed function
(https://redux.js.org/api/compose, verified 2026-08-02). The benefit is compact
alignment with mathematical convention. The cost is that many application
readers have to read the list from the end.

**Left-to-right pipe.** `pipe(a, b, c)` means "run `a`, then `b`, then `c`."
RxJS documents `pipe` as passing a value to the first unary function and then
passing each result to the next function
(https://rxjs.dev/api/index/function/pipe, verified 2026-08-02). The benefit is
reading in execution order. The cost is that `pipe` is often a library helper,
not a language operator, so error messages may point at helper overloads.

**Method chaining on function values.** Java's `Function<T,R>` interface
includes `compose`, `andThen`, `apply`, and `identity`; `andThen` returns a
function that applies the current function first and the following function
afterward
(https://docs.oracle.com/en/java/javase/22/docs/api/java.base/java/util/function/Function.html,
verified 2026-08-02). This form reads well for two or three steps. Longer chains
can become hard to format.

**Reducer-built composition.** A helper can fold a list of functions into one
function. Python's `functools.reduce` applies a two-argument function
cumulatively from left to right
(https://docs.python.org/3/library/functools.html, verified 2026-08-02). That
is a natural way to implement `pipe` or `compose` in languages where functions
are ordinary values. The benefit is small code. The cost is weaker type
checking in languages whose type systems do not express a heterogeneous list of
functions.

**Middleware composition.** Each step receives a context and a continuation.
The composed function arranges downstream and upstream flow. Koa documents
`koa-compose` for combining several middleware functions into one reusable
middleware
(https://github.com/koajs/koa/blob/master/docs/guide.md, verified
2026-08-02). The benefit is extension around a core request flow. The cost is
that control flow is no longer a simple left-to-right transform. A middleware
can stop the chain by not calling `next`.

**Typed domain pipeline.** Each step is a named domain function with explicit
input and output types. The composition may be manual because the language lacks
a convenient variadic helper. The benefit is excellent compiler feedback. The
cost is more named functions and more type declarations.

**Effect-aware composition.** A step returns `Result<B,E>`, `Option<B>`,
`Promise<B>`, or another context. Plain Function Composition is not enough when
the next step expects the unwrapped `B`. Use Monad, Applicative, or an
effect-specific `flatMap` pattern for that case. Engineering judgement: many
teams call this "composition" in conversation, but the implementation contract
has moved to the effect abstraction.

**Validation pipeline.** Each step checks or enriches data and returns either a
new value or a failure value. This variant is attractive because the happy path
reads as a clean chain. It becomes poor when the business wants to collect all
validation failures rather than stop at the first failure. Stop-first policy
points toward monadic composition. Accumulate-all policy points toward
Applicative validation.

**Instrumentation wrapper.** The composition helper can wrap every step with
timing and error capture. This variant keeps step code clean and gives operators
per-step data. The trade-off is that the helper becomes part of the production
platform. It must preserve step order, return values, thrown errors, and async
behavior, or it will introduce defects while observing them.

**Static composition by code generation.** Some teams generate direct calls from
a declarative step list. The generated function may be faster and easier for a
debugger than a generic helper. The cost is a build step and more moving parts.
This is worth considering only when chains are hot, numerous, or configured by
non-programmer tools.

## 9. Known production uses

**Redux store enhancers.** Redux exposes `compose(...functions)` as a helper
that composes functions from right to left. Its documentation says the helper is
included as a convenience and can be used to apply several store enhancers in a
row (https://redux.js.org/api/compose, verified 2026-08-02). Redux tutorials
also show `compose` combining multiple enhancers into one enhancer because
`createStore` accepts a single enhancer argument
(https://redux.js.org/tutorials/fundamentals/part-4-store, verified
2026-08-02). This is a production use because Redux store configuration relies
on function composition to turn separate store customizations into one store
customization function.

**RxJS pipeable operators.** RxJS documents pipeable operators as functions that
take an Observable and return another Observable, and documents `.pipe()` as the
preferred way to compose operators in readable order
(https://rxjs.dev/guide/operators, verified 2026-08-02). The standalone `pipe`
API also returns a unary function from a sequence of unary functions
(https://rxjs.dev/api/index/function/pipe, verified 2026-08-02). This is a
production use because RxJS applications build asynchronous event behavior by
composing Observable operators such as mapping, filtering, merging, and
debouncing.

**Koa middleware and koa-compose.** Koa middleware functions receive `(ctx,
next)`, and the Koa guide describes combining multiple middleware into one
middleware with `koa-compose`
(https://github.com/koajs/koa/blob/master/docs/guide.md, verified
2026-08-02). The `koa-compose` npm package describes its API as composing a
given middleware array and returning middleware
(https://www.npmjs.com/package/koa-compose, verified 2026-08-02). This is a
production use because Koa applications register middleware stacks, and reusable
middleware groups are built by composing those functions.

**Java standard library functions.** Java `Function<T,R>` is a standard library
functional interface with `compose`, `andThen`, and `identity` methods
(https://docs.oracle.com/en/java/javase/22/docs/api/java.base/java/util/function/Function.html,
verified 2026-08-02). This is not one application, but it is a production API
surface: Java code that accepts `Function` can receive composed behavior without
declaring a new class.

These examples show three different operational shapes. Redux composes store
customization functions at setup time. RxJS composes asynchronous stream
operators and runs them as values arrive. Koa composes middleware where each
step can run code before and after downstream work. The shared pattern is not
their runtime model. The shared pattern is that a larger callable is built by
connecting smaller callables through a defined continuation or input-output
contract.

## 10. Consequences

Positive consequences.

- The chain becomes a named value. That makes repeated behavior easier to reuse
  and review.
- Small functions stay small because orchestration is moved out of the step
  bodies.
- Tests can target individual steps and the whole chain separately.
- Order is centralized. Changing the order requires one edit at the composition
  site.
- Cross-cutting wrappers can be introduced around every step from the
  composition helper, such as timing, tracing, or input validation.
- A team can add new steps without editing the internals of existing steps when
  the type boundary stays stable.

Negative consequences.

- Long chains can hide meaningful intermediate states.
- Stack traces may contain helper functions and anonymous closures rather than
  domain names.
- Type errors can be harder to read when a variadic helper or overloaded method
  is involved.
- Debuggers may step through the helper rather than through the conceptual
  pipeline.
- Side effects become harder to reason about when a step captures mutable state.
- Runtime cost can rise in hot paths due to extra calls, allocations, and missed
  optimizations.
- Readers unfamiliar with composition may misread right-to-left order.

Neutral consequences that still matter.

- Composition does not make code pure. A composed function can still write a
  file, mutate state, or call a remote service.
- Composition does not make a chain lawful. Identity and associativity are
  properties to preserve through discipline and tests, not guarantees from a
  helper name.
- Composition does not remove the need for naming. It moves naming from
  intermediate values to steps and whole chains.
- Composition does not pick an error model. Exceptions, `Result`, `Option`,
  promises, streams, and middleware continuations all need different handling.

Engineering judgement: the pattern earns its place when it removes accidental
plumbing. It loses when it removes names that carried business meaning.

## 11. Failure modes and misuse

Engineering judgement. These are common failure shapes and the symptoms a
maintainer can observe.

- **Symptom.** A composed function returns a value with the right broad type but
  wrong domain state, such as a response rendered before authorization.
  **Cause.** Steps were reordered because the chain looked like a list of
  independent helpers. **Fix.** Rename steps with phase words, add a whole-chain
  test for required order, and keep order-sensitive states as distinct types
  where the language allows it.
- **Symptom.** A production trace says only `pipe` or `compose` failed.
  **Cause.** Anonymous functions were composed without step names or tracing.
  **Fix.** Name exported steps, wrap the composition helper to record step name,
  and attach the current step to error metadata.
- **Symptom.** A unit test passes for each step, but the composed chain fails at
  runtime with "property missing", `undefined`, `None`, `null`, or a type cast
  error. **Cause.** The boundary between two steps was assumed rather than
  checked. **Fix.** Add a contract test for every adjacent pair, use static
  types where available, or validate step output at chain construction.
- **Symptom.** A harmless-looking refactor changes behavior after combining two
  adjacent maps or removing an identity function. **Cause.** One step has a side
  effect or depends on evaluation count. **Fix.** Move side effects to named
  effectful boundaries, or document the chain as ordered imperative middleware
  rather than pure composition.
- **Symptom.** Performance profiles show many short-lived closures or deep
  stacks in a tight loop. **Cause.** The chain is rebuilt per item rather than
  built once, or the runtime cannot inline the helper. **Fix.** Build the chain
  once, use a loop in the hot path, or benchmark a specialized implementation.
- **Symptom.** A new optional or asynchronous step forces `Promise<Promise<T>>`,
  `Result<Result<T,E>,E>`, or nested callbacks. **Cause.** Plain composition was
  used where monadic binding was needed. **Fix.** Switch that portion to
  `flatMap`, `andThen` on `Result`, `await` at a clear boundary, or another
  effect-aware composition operator.
- **Symptom.** A chain gains flags such as `skipValidation`, `auditOnly`, and
  `retryMode`. **Cause.** Runtime policy has been squeezed into a fixed
  composition. **Fix.** Extract Strategy, a workflow graph, or a rules table and
  keep Function Composition for the fixed branches inside those choices.
- **Symptom.** A privacy review cannot tell whether redaction happens before
  export. **Cause.** The chain uses generic names such as `step1`, `step2`, and
  `process`. **Fix.** Rename security-sensitive steps, add an order test, and
  record step names in traces.
- **Symptom.** A new teammate repeatedly reverses `compose` argument order.
  **Cause.** The codebase mixes mathematical order and data-flow order without a
  convention. **Fix.** Standardize on `pipe` for application code or reserve
  `compose` for small local expressions where the team expects it.
- **Symptom.** A composed function works in tests but fails under concurrent
  load. **Cause.** One step closes over mutable state that is shared across
  calls. **Fix.** Make state request-scoped, pass it as input, or protect it
  with the same concurrency rules as any other shared state.

## 12. Trade-off matrix

| Force | Function Composition | Named temporary sequence | Chain of Responsibility | Decorator | Workflow graph |
|---|---|---|---|---|---|
| Coupling | Low between steps when types match | Local variables couple the caller to every intermediate shape | Sender is decoupled from receiver choice | Wrapped object interface couples all layers | Nodes couple through graph schema |
| Latency | Extra calls unless optimized | Direct calls, easy to inline | Handler traversal can add branching | One wrapper call per layer | Scheduler and persistence can dominate |
| Consistency | One named chain reused | Repeated sequences can drift | Order can vary by handler setup | Layer order fixed by wrapping | Graph version controls order |
| Operability | Needs step naming in helper | Intermediate variables are visible in logs if logged | Handler names can be logged | Wrapper names can be logged | Usually strongest tracing model |
| Cost | Low for local transforms | Lowest for one-off code | Higher due handler protocol | Higher due object wrappers | Highest due engine and state |
| Team topology | Good for step contributors | Good for one owning team | Good for extension teams | Good for platform wrapping | Good for operations-heavy teams |
| Cognitive load | Low after higher-order style is familiar | Low for most readers | Medium due dynamic dispatch | Medium due nested wrappers | High due graph semantics |
| Debuggability | Good with named steps, poor with anonymous chains | Strong with breakpoints | Depends on handler discovery | Depends on wrapper depth | Strong when engine exposes runs |

Named temporary sequences win for a single short transformation. Chain of
Responsibility wins when each handler decides whether to continue. Decorator
wins when each layer preserves the same object interface. A workflow graph wins
when the sequence is long-running, branching, retried, or durable.

The table is most useful when the alternatives are real options in the codebase.
For a command-line parser, named temporaries and Function Composition may be the
only serious choices. For an HTTP platform, middleware composition, Decorator,
and Chain of Responsibility may all be in play. For a claims workflow with
manual review, Function Composition may be fine inside each small phase, while
the phase ordering belongs in a workflow graph. Mixing these levels is a common
design mistake.

## 13. Related and incompatible patterns

**Higher-Order Function** is the parent idea. Function Composition exists
because functions can be passed to and returned from other functions.

**Partial Application** often prepares a multi-argument operation so it can fit
inside a unary chain. For example, `price(tax, amount)` can become
`priceWith(tax): Amount -> Money` and then compose with parsing and rendering.

**Currying** changes a multi-argument function into a chain of one-argument
functions. That makes composition easier in languages where unary functions are
the default shape.

**Pipeline** is the left-to-right presentation of the same idea when the stages
are functions. Some catalogs treat Pipeline as its own architectural pattern
when stages run concurrently, buffer data, or communicate through queues. That
larger architecture is outside this entry.

**Functor** composes with Function Composition through the functor composition
law. Mapping `f` and then mapping `g` should match mapping `g after f` for a
lawful functor. The Functor entry covers that law in detail.

**Monad** replaces plain composition when each step returns a wrapped value and
the next step needs the unwrapped value. In such code the composition operator
is often called `flatMap`, `bind`, `andThen`, or `then`.

**Decorator** resembles Function Composition because wrappers can be nested.
Decorator is object-shaped and preserves one interface. Function Composition is
callable-shaped and can change the type at each step.

**Chain of Responsibility** conflicts when the design requires each handler to
decide whether the next handler runs. Function Composition assumes a fixed
connection unless the composed function's context includes a continuation, as
middleware does.

**Hidden side effects** and **order-dependent global state** are incompatible
with treating a chain as ordinary composition. They can exist in composed code,
but then algebraic reasoning about rearranging, fusing, or testing steps becomes
false.

**Template Method** can call a composed function as one hook in a larger
algorithm. The two patterns sit at different levels. Template Method owns the
algorithm skeleton through inheritance. Function Composition owns a local
callable value through higher-order functions.

**Builder** can assemble a composed function step by step when the final chain
has many optional parts. This is useful for configuration-heavy systems, but it
should not hide the final order. A builder that accepts steps through several
mutating calls should expose the resulting chain for review or tracing.

## 14. Refactoring path in and out

Refactoring in.

1. Find a repeated sequence of transformations with the same order in two or
   more places.
2. Name the input and output type of each line. If an intermediate value carries
   domain meaning, keep it visible.
3. Extract each line that is only a transformation into a named function. This
   is the Extract Function refactoring from the refactoring family.
4. Make each extracted function unary. Use Partial Application or a context
   object for stable dependencies such as configuration, clock, logger, and
   tenant.
5. Add tests for each extracted function before changing call sites.
6. Introduce a small `pipe` or `compose` helper only if the language or local
   style lacks one.
7. Replace the repeated sequence with a named composed function.
8. Add a whole-chain test that proves the visible business behavior has not
   changed.
9. Add tracing or step names if the chain crosses an operational boundary.

During the refactor, keep one safety rule: do not change shape and order in the
same edit. First extract functions while preserving the old direct sequence.
Then introduce composition with the same order. Then consider renaming or
reordering if the tests expose a clearer domain path. Smaller edits make review
possible and keep blame useful when a behavior change appears.

Refactoring out.

1. Identify why the chain no longer pays rent: order changes by policy, steps
   need several unrelated inputs, stack traces are too opaque, or intermediate
   states now matter.
2. Inline the composed function at one call site while preserving tests.
3. Give intermediate values names where those names explain domain state.
4. Move branching into Strategy, Chain of Responsibility, or a workflow graph if
   runtime policy chooses the next step.
5. Delete the composition helper if it becomes unused. A helper kept for one
   call site is usually noise.

Refactoring out should be considered after the chain has absorbed too much
policy. A chain that began as `decode, validate, render` may become `decode,
validate, maybeLoadProfile, maybeDiscount, maybeEscalate, render`. If "maybe"
appears in several step names, the code is signalling that runtime choice has
entered the model. At that point, removing Function Composition from the outer
level can make the code more honest, while retaining composition inside each
fixed branch.

Engineering judgement: do not refactor into Function Composition because the
syntax looks more functional. Refactor when the sequence itself has become a
concept worth naming.

## 15. Testing and verification

Engineering judgement. Function Composition improves testing when the step
boundaries match domain boundaries.

Test each step with ordinary unit tests. A step such as `decode`, `validate`,
or `render` should have focused examples for valid input, invalid input, and
edge values. Those tests should not know about the rest of the chain.

Test adjacent contracts. For every pair `A -> B` and `B -> C`, include at least
one test where `B` is produced by the first step and consumed by the second.
This catches structural mismatch that isolated unit tests can miss, especially
in dynamic languages.

Test the whole chain with a small number of representative examples. Whole-chain
tests prove order and integration. They should not duplicate every step test.

Use spies sparingly to verify order when order itself is the behavior. A spy can
record that `decode`, `validate`, and `render` ran in that order. Prefer output
tests when observable output proves the same fact.

Use property tests for algebraic helpers. A generic `compose` helper should
satisfy identity and associativity for pure functions:

```text
compose(id, f)(x) == f(x)
compose(f, id)(x) == f(x)
compose(h, compose(g, f))(x) == compose(compose(h, g), f)(x)
```

Do not apply those laws blindly to effectful steps. A function that logs,
mutates, reads time, generates random numbers, or performs I/O may have the same
return value but different observable behavior.

For middleware composition, test short-circuit behavior. A Koa-style middleware
that does not call `next` should prevent downstream middleware from running.
That is not a violation. It is the middleware contract.

For observability wrappers, test that wrapping preserves behavior. A timing
wrapper should return the same value, throw the same error type, and preserve
async completion order. The wrapper is easy to treat as infrastructure and hard
to notice when it changes semantics.

For type-heavy chains, add compile-time examples where the repository supports
them. A TypeScript or Rust sample that fails to compile after a step type
changes can be more useful than a runtime test. For dynamic chains, add a small
contract test that feeds the actual output of each step into the next step.

For security-sensitive chains, test forbidden order as well as required output.
For example, a redaction chain can use a spy logger and prove that no raw secret
is observed before the redaction step. Output-only tests may miss that class of
leak because the final response can be correct while an earlier log is unsafe.

## 16. Observability signals

Engineering judgement. A composed chain should be observable as a chain, not
only as a single anonymous function.

Log or trace the chain name at entry and exit. Good names look like
`requestToCommand`, `eventToMetric`, or `storeEnhancerChain`. Avoid names such
as `pipeline1`.

Record step name, duration, input shape, output shape, and outcome. Do not log
full payloads by default. Shape can mean schema version, domain type, count, or
size in bytes.

Measure error rate per step. A healthy chain usually shows stable step duration
and low error concentration. A failing chain often has one step whose errors
rise sharply after a deploy or schema change.

Track short-circuit counts for contextual chains. Middleware and `Result` chains
often stop early by design. A sudden increase in early stops can mean a new
validator rejects too much traffic or an upstream parser changed shape.

Expose chain construction failures separately from chain execution failures.
Construction failures include incompatible step types, missing step
registration, or invalid configuration. Execution failures include invalid input
and downstream service errors.

For high-throughput chains, measure allocation rate and call depth. Composition
that rebuilds closures per item will show extra allocation pressure. Build the
chain once at startup or module load when the chain is static.

A dashboard for a healthy chain should answer five questions without reading
code. Which chain ran? Which version of the chain ran? Which step is currently
slowest? Which step fails most often? How many calls stopped before the final
step? If those answers are not available, the chain is operationally opaque even
if the code is elegant.

Version the chain when order is a business contract. A deployed service may run
old and new versions side by side during a rollout. Recording `chain.version`
with step timings helps distinguish a bad input spike from a bad chain edit.
The version can be a release id, config hash, or explicit chain name suffix.

## 17. Security and privacy implications

Engineering judgement. Function Composition is not a security control by
itself. It changes where controls are placed and how easy they are to audit.

Positive security effects appear when security-sensitive steps are named and
centralized. A request pipeline can make `authenticate`, `authorize`,
`validateInput`, and `redactOutput` visible in one ordered chain. That makes
review easier than finding those calls scattered across handlers.

Negative security effects appear when the chain hides order. If `redact` runs
after `log`, sensitive data may already have been written. If `authorize` runs
after `loadAccount`, the account lookup may leak existence information through
timing, metrics, or error messages. The fix is not "more composition." The fix
is an explicit security phase order with tests and traces.

Do not compose untrusted functions into privileged chains. Plugin systems,
tenant customization, and user-authored transforms need sandboxing, resource
limits, and an allowlist of accessible data. A composed function runs with the
authority of the process unless the host restricts it.

Be careful with closures. A step can capture credentials, request bodies,
tenant identifiers, or personal data. Long-lived composed functions should not
capture per-request secrets. Pass request-scoped data as input, and keep the
chain definition free of private payloads.

Logging composed steps can leak data if observability records full inputs and
outputs. Prefer step names, schemas, sizes, ids with approved handling, and
error categories. Redaction should happen before any logging step that sees
sensitive payloads.

Composition can also obscure authorization context. A step named `loadInvoice`
may look harmless in a billing chain, but the authorization decision may live in
an earlier step. If a later refactor reuses `loadInvoice` outside the chain, it
may run without the earlier guard. Treat security-bearing composition as a
public contract: either make guarded loaders require an authorized token type,
or keep unguarded loaders private to modules where the authorization order is
clear.

Privacy review should include closure capture. A top-level chain that captures
an analytics client is ordinary. A chain built inside a request handler that
captures the full request body can extend the lifetime of personal data beyond
the request. The privacy issue is not the compose helper. It is the hidden
reference held by the returned function.

## Code examples

The examples below use Python, Go, Rust, and TypeScript because each supports
first-class functions without framework setup. The samples were run or compiled
with `python3`, `go run`, `rustc`, and `tsc` in this repository session.

```python
from functools import reduce
from typing import Callable, TypeVar

A = TypeVar("A")


def pipe(*steps: Callable[[object], object]) -> Callable[[object], object]:
    def run(value: object) -> object:
        return reduce(lambda current, step: step(current), steps, value)

    return run


def strip(value: object) -> object:
    return str(value).strip()


def lower(value: object) -> object:
    return str(value).lower()


def tag(value: object) -> object:
    return f"user:{value}"


normalize_user = pipe(strip, lower, tag)

assert normalize_user("  ALICE ") == "user:alice"
print(normalize_user("  ALICE "))
```

```go
package main

import (
	"fmt"
	"strings"
)

type Step func(string) string

func Pipe(steps ...Step) Step {
	return func(value string) string {
		current := value
		for _, step := range steps {
			current = step(current)
		}
		return current
	}
}

func main() {
	normalize := Pipe(
		strings.TrimSpace,
		strings.ToLower,
		func(value string) string { return "user:" + value },
	)

	fmt.Println(normalize("  ALICE "))
}
```

```rust
fn trim(input: String) -> String {
    input.trim().to_string()
}

fn lower(input: String) -> String {
    input.to_lowercase()
}

fn tag(input: String) -> String {
    format!("user:{input}")
}

fn compose<A, B, C, F, G>(f: F, g: G) -> impl Fn(A) -> C
where
    F: Fn(B) -> C,
    G: Fn(A) -> B,
{
    move |value| f(g(value))
}

fn main() {
    let normalize = compose(tag, compose(lower, trim));
    println!("{}", normalize("  ALICE ".to_string()));
}
```

```typescript
type Unary<A, B> = (value: A) => B;

function pipe<A, B>(ab: Unary<A, B>): Unary<A, B>;
function pipe<A, B, C>(ab: Unary<A, B>, bc: Unary<B, C>): Unary<A, C>;
function pipe<A, B, C, D>(
  ab: Unary<A, B>,
  bc: Unary<B, C>,
  cd: Unary<C, D>
): Unary<A, D>;
function pipe(...steps: Array<Unary<unknown, unknown>>) {
  return (value: unknown) => steps.reduce((current, step) => step(current), value);
}

const normalize = pipe(
  (value: string) => value.trim(),
  (value: string) => value.toLowerCase(),
  (value: string) => `user:${value}`
);

console.log(normalize("  ALICE "));
```

## 18. References

- Haskell.org. "A Gentle Introduction to Haskell, Version 98. Functions."
  Function composition operator `(.)`.
  https://www.haskell.org/tutorial/functions.html, verified 2026-08-02.
- Haskell Hugs documentation. "Prelude." Entry for `(.)`, function
  composition. https://www.haskell.org/hugs/pages/libraries/base/Prelude.html,
  verified 2026-08-02.
- Oracle. "Interface Function<T,R>." Java SE 22 API documentation,
  `java.util.function.Function`.
  https://docs.oracle.com/en/java/javase/22/docs/api/java.base/java/util/function/Function.html,
  verified 2026-08-02.
- Python Software Foundation. "functools. Higher-order functions and operations
  on callable objects." `functools.reduce`.
  https://docs.python.org/3/library/functools.html, verified 2026-08-02.
- Redux documentation. "`compose(...functions)`."
  https://redux.js.org/api/compose, verified 2026-08-02.
- Redux documentation. "Redux Fundamentals, Part 4. Store." Store enhancers and
  `compose`. https://redux.js.org/tutorials/fundamentals/part-4-store,
  verified 2026-08-02.
- RxJS documentation. "RxJS Operators." Pipeable operators.
  https://rxjs.dev/guide/operators, verified 2026-08-02.
- RxJS documentation. "pipe." API entry.
  https://rxjs.dev/api/index/function/pipe, verified 2026-08-02.
- Koa documentation. "Guide." Combining multiple middleware with `koa-compose`.
  https://github.com/koajs/koa/blob/master/docs/guide.md, verified 2026-08-02.
- npm. "koa-compose." Package README and API summary.
  https://www.npmjs.com/package/koa-compose, verified 2026-08-02.
