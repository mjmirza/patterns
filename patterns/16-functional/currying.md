---
name: Currying
slug: currying
family: 16-functional
category: Functional
aliases: [Schönfinkelization, Curried Functions, Unary Function Encoding]
first_described: "Schönfinkel 1924, popularized by Curry"
maturity: canonical
related: [partial-application, higher-order-function, function-composition, pipeline, applicative]
incompatible_with: [long-parameter-list]
verified: 2026-08-02
---

# Currying

## 1. Name, aliases, and lineage

The canonical name is Currying. In programming, it means representing a
multi-argument operation as a chain of one-argument functions. A function that
would normally be read as `f(a, b, c)` is instead shaped as `f(a)(b)(c)`, where
each call captures one argument and returns the next function until the final
call produces the result.

The common name honors Haskell B. Curry, but the historical credit is messier
than the name implies. The Internet Encyclopedia of Philosophy records that
Curry objected to the naming because he took the idea from Moses Schönfinkel,
while the name had already stuck in later usage
(https://iep.utm.edu/haskell-brooks-curry/, verified 2026-08-02). Because of
that history, some mathematical writing uses **Schönfinkelization** for the
same transformation. The Haskell tutorial describes `Integer -> Integer ->
Integer` as equivalent to `Integer -> (Integer -> Integer)` and presents the
left-associated application model that makes `add 1 2` mean `(add 1) 2`
(https://www.haskell.org/tutorial/functions.html, verified 2026-08-02).

The phrase **curried function** is used in two slightly different ways. In
Haskell and F#, ordinary multi-argument source syntax is already a sequence of
unary function applications unless the programmer explicitly uses a tuple. In
JavaScript, TypeScript, Python, Go, Java, Rust, and Swift, a curried function is
usually an adapter or hand-written closure chain around a language that already
has ordinary multi-parameter calls. That difference matters because the pattern
is cheap and idiomatic in languages with curried application syntax, while it
can become ceremony in languages that print, debug, and type functions as
ordinary multi-argument callables.

Currying must be distinguished from **partial application**. Currying changes
the shape of a function so it can receive its arguments over several calls.
Partial application is the act of binding fewer arguments than the operation
needs. In practice they appear together: after a function is curried, supplying
the first argument yields a partially applied function. The Haskell tutorial
uses `inc = add 1` as an example of partial application of a curried function
(https://www.haskell.org/tutorial/functions.html, verified 2026-08-02).

## 2. Problem and context

A codebase has small operations that share some arguments across many calls but
vary another argument late in a pipeline. The repeated arguments may be a
tenant id, locale, currency, database handle, metric name, validation policy,
authorization context, date formatter, logger, or comparison rule. Passing all
arguments every time keeps the dependency visible, but it also scatters the
same prefix across many call sites and makes composition awkward.

The problem becomes visible when a programmer wants to turn an operation into a
specialized function without defining a new named wrapper for every case. For
example, `priceWith(taxRate, currency, amount)` is easy to call once. It is less
pleasant when a billing pipeline wants one reusable `priceForGermany` function
that already knows the tax rate and currency and only waits for an amount.
Currying makes that specialization the normal shape:
`priceWith(taxRate)(currency)(amount)`.

The context that makes Currying useful has four parts.

- The operation has stable arguments that should be bound before volatile
  arguments arrive.
- Functions are passed to other functions, such as `map`, `filter`, `fold`,
  route builders, event handlers, parser combinators, or middleware creators.
- The argument order is intentional. Parameters that are likely to be fixed
  earlier appear first, and data that flows through a pipeline appears last.
- The team is comfortable reading functions that return functions.

The pattern is a poor fit when the domain call reads as one indivisible action,
when named records carry more meaning than positional arguments, or when stack
traces and debugger displays are more valuable than point-free composition.

The hidden problem is often not the number of parameters by itself. A
five-parameter function can be clear when the call is rare and all arguments are
named through a record. The pain appears when the same early parameters are
repeated in many places and the final parameter is the value moving through a
chain. Currying changes that repeated prefix into a value. That value can then
be named, tested, passed to a collection transform, placed in a routing table,
or stored in a module-level constant.

This is why argument order is part of the problem, not a detail of the answer.
A function `contains(needle, haystack)` can become `contains("error")`, which
is useful as a predicate over many strings. A function `contains(haystack,
needle)` does not specialize as naturally for the same workload. Neither order
is universally right. The right order follows the common binding story in that
API. In functional libraries this commonly means policy first and data last.

Currying also addresses a boundary problem between configuration and execution.
Many systems have code that wants to say "from here down, use this locale" or
"from here down, use this authorization rule" without adding a global variable.
A curried function gives that code a local capability. The caller binds the
context and passes down a narrower callable. The callee does not need to know
where the context came from, yet the context is not global.

## 3. Forces

Engineering judgement. This dimension weighs trade-offs that vary by language,
runtime, and team habit.

- **Coupling.** Favoured when a caller can bind policy once and hand a narrower
  function to lower layers. Sacrificed if closures silently carry too much
  context and hide dependencies from the receiving function.
- **Latency.** Usually neutral for coarse business logic. Sacrificed in tight
  loops where each captured argument allocates or prevents inlining. In
  ahead-of-time and optimizing runtimes, simple closure chains may be collapsed,
  but that is an optimization, not a design contract.
- **Consistency.** Favoured when one prefix captures a policy set and all later
  calls share it. Sacrificed when different prefixes are created ad hoc and no
  one can tell which policy was bound.
- **Operability.** Sacrificed by anonymous closures. A log line that says
  `function` is rarely useful. Favoured if curried builders attach names,
  trace attributes, or wrapper labels at the point where context is bound.
- **Cost.** Favoured by avoiding small wrapper classes and repeated adapter
  functions. Sacrificed if the language needs heavy generic types, overloads,
  or helper libraries to express a simple call.
- **Team topology.** Favoured for library teams that publish general functions
  with policy-first, data-last order. Product teams can bind local policy
  without editing the library. Sacrificed when teams disagree on argument order
  and every service invents a local convention.
- **Cognitive load.** Favoured for readers fluent in functional pipelines.
  Sacrificed for readers who expect the final value at every call expression.
  Nested return types such as `A -> B -> C -> R` demand practice.
- **Type precision.** Favoured in languages where each stage has a concrete
  function type. Sacrificed in dynamically typed code where a missing final
  call produces another function instead of the domain value and no compiler
  complains.

The pattern favours composability, local specialization, and API uniformity. It
sacrifices directness, debugger clarity, and sometimes allocation behaviour.

There is a force between mathematical regularity and domain readability.
Currying makes every stage unary, which gives composition operators and type
inference a regular shape. Domain language often wants grouped concepts, such
as `Money`, `Address`, `Credentials`, or `SearchQuery`. Engineering judgement:
when the arguments are a single domain concept, regular unary shape is the
wrong win. Group the concept first, then consider Currying around the grouped
value if the API still needs staged binding.

There is also a force between open extension and local auditability. A curried
API lets a caller create many specialized functions without changing the
library. That is convenient for extension. It can be harder for audit because
the library owner may not know which policy values callers have captured. A
public platform API should give names and metrics to common specializations
instead of expecting operators to infer them from closure identities.

## 4. Applicability and non-applicability

Reach for Currying when the following hold.

- A function will often be specialized by its first one or two arguments, then
  passed to another function.
- The last argument is the flowing data value in a pipeline, collection
  transform, parser, validator, or request handler.
- You want to publish a small functional API where callers build new functions
  from old ones by omission of later arguments.
- A language or library already uses curried APIs. The Haskell tutorial, Ramda,
  FSharp.Core operators, and Scala `Function2.curried` all document this shape
  in their own contexts
  (https://www.haskell.org/tutorial/functions.html,
  https://ramdajs.com/docs/#curry,
  https://fsharp.github.io/fsharp-core-docs/reference/fsharp-core-operators.html,
  https://www.scala-lang.org/api/2.13.x/scala/Function2.html, each verified
  2026-08-02).
- You need to separate dependency binding from data processing without creating
  a class, container binding, or config object.
- A test should supply fake policy once and then reuse the specialized function
  across many examples.

Do NOT reach for Currying in these cases.

- **Arguments form a named domain concept.** If `street`, `city`, `postalCode`,
  and `country` form an address, use a record or value object. A chain of four
  positional calls loses names and invites swaps.
- **The operation is called in one place.** A curried wrapper adds an extra
  layer for no repeated specialization. A direct function is clearer.
- **The function has optional or default parameters.** JavaScript libraries
  warn about arity inference around defaults. Ramda documents that default
  parameters do not count toward function arity for its `curry`
  (https://ramdajs.com/docs/#curry, verified 2026-08-02).
- **The order of binding is not stable.** If callers sometimes bind tenant
  first, sometimes amount first, sometimes date first, a named options object or
  builder is easier to read.
- **The function relies on mutation across arguments.** Capturing a mutable
  object in the first call and using it in the final call can turn a short
  function into a time-dependent closure.
- **The team debugs mainly through stack traces.** Anonymous closure chains can
  produce frames with poor names. Use named adapters or direct calls.
- **The API must be consumed by reflection or metadata tools.** Some curry
  helpers do not preserve function arity. Lodash documents that `_.curry` does
  not set the `length` property of curried functions
  (https://lodash.com/docs/#curry, verified 2026-08-02).
- **The public API is for broad, mixed-skill usage.** Engineering judgement:
  curried APIs reward fluency, but a general SDK may benefit from named
  parameter objects and explicit methods.
- **The operation has more than three independent arguments.** A long chain of
  calls often hides meaning. If the stages do not have natural names, introduce
  a request object or split the operation into smaller functions.
- **The function crosses a process boundary.** Closures are local runtime
  values. They are poor messages for queues, RPC calls, database rows, and audit
  logs. Send data and an operation name instead.
- **The argument to bind is secret-bearing.** Capturing a secret in a closure
  can lengthen its lifetime. Prefer a short direct call or a small capability
  object with a defined disposal story.
- **Callers need independent validation of every field.** A curried chain can
  defer validation until the final call. A builder or typed record can validate
  earlier and report all field errors together.
- **The same name would describe every intermediate stage.** If `configure`,
  `configure`, and `configure` are the best names available, the staged API is
  probably not carrying enough domain information.

## 5. Structure

The pattern has six participants.

- **Original operation.** A function whose conceptual input has two or more
  arguments and whose result is the domain value.
- **Currying adapter.** A wrapper that accepts the original operation and
  returns the first unary stage. In languages with native currying, this role
  may be the compiler and syntax rather than a user-written function.
- **Argument stage.** A unary function that receives one argument, captures it,
  and returns the next stage.
- **Captured environment.** The closed-over values accumulated by prior stages.
  This is the hidden state of the pattern.
- **Final stage.** The unary function that receives the last argument and calls
  the original operation with the captured values plus that final argument.
- **Specialized function.** Any intermediate stage saved and reused under a
  domain name, such as `priceInEur`, `forTenant`, or `withAuditLogger`.

The structure is not inheritance-based. It is a chain of values. The first call
does not perform the whole operation. It creates a smaller function. Each later
call either creates another smaller function or returns the final result.

Argument order is part of the structure. A curried function that puts data last
works well in a pipeline because early calls bind policy and the pipeline feeds
the final data value. A curried function that puts data first often forces
callers to use placeholders, flip helpers, or small lambdas.

## 6. ASCII structure diagram

```text
   Original operation
   +---------------------------------------------------------+
   | priceWith(taxRate, currency, amount) -> MoneyString     |
   +---------------------------------------------------------+
                         |
                         | curry
                         v
   +---------------------+       +--------------------------+
   | Stage 1             |       | Captured environment     |
   | taxRate -> Stage 2  |------>| taxRate                  |
   +---------------------+       +--------------------------+
             |
             v
   +---------------------+       +--------------------------+
   | Stage 2             |       | Captured environment     |
   | currency -> Stage 3 |------>| taxRate, currency        |
   +---------------------+       +--------------------------+
             |
             v
   +---------------------+       +--------------------------+
   | Final stage         |       | Call original operation  |
   | amount -> result    |------>| with all three arguments |
   +---------------------+       +--------------------------+

   A saved Stage 2 or Stage 3 value is a specialized function.
```

## 7. Dynamics

At runtime, Currying separates binding time from execution time. The early calls
capture values. The final call computes the result. This is why Currying feels
like configuration when used well and like a missing function call when used
poorly.

```text
Caller              Stage 1             Stage 2             Final stage
  |                    |                   |                    |
  | priceWith(0.19)    |                   |                    |
  |------------------->|                   |                    |
  |                    | capture taxRate   |                    |
  |<-------------------| return Stage 2    |                    |
  |                    |                   |                    |
  | priceInEur("EUR")  |                   |                    |
  |--------------------------------------->|                    |
  |                    |                   | capture currency   |
  |<---------------------------------------| return final stage |
  |                    |                   |                    |
  | format(100)        |                   |                    |
  |----------------------------------------------------------->|
  |                    |                   |       call original|
  |<-----------------------------------------------------------|
  | "EUR 119.00"       |                   |                    |
```

The dynamic risk is stale capture. If a stage captures a mutable policy object,
later mutation changes behaviour without changing the function identity. A
healthy implementation either captures immutable values, copies the data it
needs, or names the closure so logs can identify the bound context.

## 8. Implementation variants

**Native curried language syntax.** Haskell and F# make curried calls ordinary.
The Haskell tutorial presents `add x y` as application of a function returned
by `add x`, with arrow types associating to the right
(https://www.haskell.org/tutorial/functions.html, verified 2026-08-02).
FSharp.Core documents operators such as forward piping and composition in a
style that depends on functions as first-class values
(https://fsharp.github.io/fsharp-core-docs/reference/fsharp-core-operators.html,
verified 2026-08-02). This variant has the lowest ceremony because the syntax,
type inference, and libraries share one calling convention.

This variant also changes how API authors think about binary operations. A
two-argument function is not second-class compared with a one-argument
function. It is a one-argument function returning another one-argument function.
That means the language can reuse ordinary function application for both full
and partial calls. The cost is that tupled interop needs conversion at
boundaries, and readers from multi-parameter languages must learn that arrows
associate to the right while calls associate to the left.

**Manual closure chain.** A programmer writes `a => b => c => result` in
TypeScript, nested `lambda` in Python, nested `func` in Go, or nested closures
in Swift and Rust. This variant is transparent and dependency-free. It is best
for functions with two or three arguments. After that, named records often read
better.

Manual chains are also the easiest place to attach names. Instead of exporting
`curry3(formatPrice)`, a library can export `withTaxRate`, whose return type is
`withCurrency`, whose return value is `formatAmount`. Those names may be
implemented as nested functions even in a language that prints them poorly in a
debugger. The code is longer than a generic helper, but the names document the
binding order.

**Generic curry helper.** Lodash exposes `_.curry`, and Ramda exposes `R.curry`
and `R.curryN` for JavaScript
(https://lodash.com/docs/#curry and https://ramdajs.com/docs/#curry, both
verified 2026-08-02). Helpers support mixed application such as supplying more
than one argument per call, but they usually rely on runtime arity and dynamic
argument lists. They fit JavaScript libraries better than strongly typed public
APIs.

Generic helpers are attractive during local refactoring because they let a team
try the call shape without changing the original function. The risk is that the
helper can become the public API before the argument order has been tested by
real call sites. Engineering judgement: keep generic helpers near the edge of a
module at first. Promote a named curried function only after several call sites
show that the binding order is stable.

**Placeholder curry.** Ramda and Lodash support placeholders so callers can
bind later positions before earlier ones
(https://ramdajs.com/docs/#curry and https://lodash.com/docs/#curry, both
verified 2026-08-02). This increases flexibility but weakens the main design
signal. If placeholders are common, the original argument order is probably
wrong for the workload.

Placeholders are a compromise between Currying and arbitrary partial
application. They are useful in JavaScript because the language has flexible
calls and large functional utility libraries. They are less attractive in typed
APIs because every hole complicates the function type the caller sees. A
placeholder also makes the reader simulate argument collection in their head.

**Curried higher-order component or builder.** React Redux documents
`connect(mapState, mapDispatch)` returning a wrapper function that is then
called with a component
(https://react-redux.js.org/api/connect, verified 2026-08-02). This is not
automatic currying of an arbitrary function. It is a hand-shaped two-stage API
that uses the same idea: bind store mapping first, bind component later.

**Tuple conversion.** Haskell Prelude exposes `curry` and `uncurry` to convert
between a function over a pair and a curried two-argument function
(https://downloads.haskell.org/~ghc/8.4-latest/docs/html/libraries/base-4.11.1.0/Prelude.html,
verified 2026-08-02). Scala `Function2.curried` creates a unary function that
returns another unary function
(https://www.scala-lang.org/api/2.13.x/scala/Function2.html, verified
2026-08-02). This variant is useful at boundaries where tupled and curried APIs
meet.

Tuple conversion is the cleanest migration path when an API has both tupled and
curried consumers. Tupled form is convenient for data structures, pattern
matching, and APIs that receive records from outside the process. Curried form
is convenient for specialization and composition. Treat conversion as a
boundary adapter rather than proof that one form should replace the other
everywhere.

## 9. Known production uses

- **Ramda.** Ramda documents `R.curry` and states that many call shapes of a
  ternary function are accepted by the curried result, including one argument
  at a time and grouped arguments. It also documents placeholder support and
  warns about default parameters and arity
  (https://ramdajs.com/docs/#curry, verified 2026-08-02). This is a named
  production JavaScript library built around data-last functional pipelines.
- **Lodash.** Lodash documents `_.curry(func, [arity=func.length])`, placeholder
  support, and the caveat that the returned function does not set `length`
  (https://lodash.com/docs/#curry, verified 2026-08-02). This is a named
  production utility library with currying as one function utility among many.
- **React Redux.** React Redux documents `connect()` as a first call that
  returns a wrapper function, and the returned function then accepts the
  component to wrap
  (https://react-redux.js.org/api/connect, verified 2026-08-02). This is a
  named production UI state library using a curried builder shape for higher
  order components.
- **GHC Haskell Prelude.** GHC base documentation includes `curry` and
  `uncurry`, with examples converting between pair-based and curried functions
  (https://downloads.haskell.org/~ghc/8.4-latest/docs/html/libraries/base-4.11.1.0/Prelude.html,
  verified 2026-08-02). This is a named production standard library for the
  Glasgow Haskell Compiler ecosystem.
- **Scala standard library.** Scala 2.13 documents `Function2.curried` as a
  method that returns a function `f` where `f(x1)(x2)` equals applying the
  original two-argument function
  (https://www.scala-lang.org/api/2.13.x/scala/Function2.html, verified
  2026-08-02). This is a named production language standard library feature.

## 10. Consequences

Positive consequences.

- Callers can name specialized functions at the point where policy is bound.
- Pipelines become easier when APIs put stable arguments first and data last.
- Small configuration adapters can replace small classes in functional code.
- Test setup can bind fake dependencies once and reuse the resulting function.
- Library APIs can encourage consistent argument order across many functions.
- A curried function exposes intermediate abstraction points that can be cached,
  memoized, decorated, or measured.

Negative consequences.

- A missing final call can pass a function where a value was expected in
  dynamically typed code.
- Positional arguments lose meaning when the chain is long.
- Stack traces may show nested anonymous functions instead of domain names.
- Generic helpers can obscure arity, especially with optional parameters,
  rest parameters, or default values.
- Captured mutable state can change between early binding and final execution.
- Overuse creates point-free code where the data path is no longer obvious.
- Runtime helpers may allocate intermediate closures and arrays of arguments.

Engineering judgement. Currying earns its place when it removes repeated
prefixes and clarifies composition. It does not earn its place when it is used
to make ordinary calls look more mathematical.

The most valuable positive consequence is local naming. A curried stage can
turn a general operation into a domain phrase without creating a new module.
`formatPrice(0.19)("EUR")` can become `priceInEur`, and the rest of the code
can talk in the language of the business rule. That name is also a test target,
an observability label, and a review point. This is where Currying is more than
syntax. It gives the team a way to name a decision after the decision is bound
but before data arrives.

The most expensive negative consequence is hidden lifetime. A direct call lives
for one expression. A specialized curried function can live for a request, a
session, a worker process, or the lifetime of a module. That may be exactly
what the design wants, but it should be visible. If a closure binds a stale
feature flag, old tenant policy, or old exchange rate, it can keep using that
value after the system has moved on. Teams using Currying in long-lived
services should decide whether specializations are rebuilt per request, per
config version, or per process.

Another consequence is API gravity. Once a library publishes data-last curried
functions, every new function is pressured to follow that order, even when a
particular operation reads better another way. Consistency has value, but it
can turn into awkward APIs. Engineering judgement: prefer consistency across a
small family of functions that compose together. Do not force every public
function in a broad SDK into a curried shape merely to satisfy a house style.

## 11. Failure modes and misuse

Engineering judgement. These are production failure patterns to look for during
review and incident analysis.

- **Symptom.** Logs show a function object, or a UI renders text like
  `[Function]`, instead of the expected domain value. **Cause.** A caller
  supplied one argument too few and passed an intermediate stage onward.
  **Fix.** Add type annotations at the boundary, name intermediate stages, and
  test the full application path.
- **Symptom.** A validator changes behaviour after a config reload even though
  no new validator was built. **Cause.** The first stage captured a mutable
  config object by reference. **Fix.** Capture immutable snapshots or rebuild
  the specialized function after config changes.
- **Symptom.** A generic `curry` helper works in tests but fails when a default
  parameter is introduced. **Cause.** Runtime arity no longer matches the
  intended number of required arguments. **Fix.** Use an explicit arity helper
  such as `curryN`, or write a manual closure chain.
- **Symptom.** Stack traces contain several frames named `lambda`, `anonymous`,
  or `func1` and the failing business rule is hard to identify. **Cause.**
  Curried stages were left unnamed. **Fix.** Save specialized functions under
  domain names and add trace attributes at binding time.
- **Symptom.** A code review cannot tell what `rule(a)(b)(c)(d)` means.
  **Cause.** Too many positional stages replaced a domain value object.
  **Fix.** Collapse related arguments into a named record and curry around that
  record if specialization is still useful.
- **Symptom.** A supposedly data-last API needs placeholders in most examples.
  **Cause.** Argument order was chosen for implementation convenience rather
  than caller binding order. **Fix.** Reorder arguments or publish named helper
  functions for common specializations.
- **Symptom.** Hot-path CPU profiles show closure allocation or adapter frames.
  **Cause.** A curried helper is rebuilt inside an inner loop. **Fix.** Move
  specialization outside the loop, cache it, or use a direct function in that
  path.
- **Symptom.** A feature-flag change appears in one handler but not another.
  **Cause.** One handler rebuilt its specialized function after the flag
  changed, while another kept an older closure. **Fix.** Bind a policy version,
  rebuild all specializations when that version changes, or read the flag at
  final execution time if freshness matters more than stable capture.
- **Symptom.** A queue worker cannot explain which user or tenant authorized an
  operation. **Cause.** The worker received a callback that already captured
  authority, rather than an explicit command with audit fields. **Fix.** Use a
  Command or data transfer object across the queue and recreate any curried
  function inside the worker from audited inputs.
- **Symptom.** A new contributor adds `flip`, placeholders, and local lambdas
  around nearly every call. **Cause.** The exported curried API has the wrong
  argument order for current callers. **Fix.** Add a caller-oriented wrapper or
  change the function declaration before the workaround becomes normal style.

## 12. Trade-off matrix

| Force | Currying | Partial application without currying | Options object | Builder pattern | Dependency injection |
|---|---|---|---|---|---|
| Coupling | Binds policy into a smaller function | Binds some args when the language supports it | Callers still know full shape | Hides staged setup behind methods | Moves binding to container or wiring code |
| Latency | May allocate per stage | Similar, often fewer stages | One allocation for the object | Usually allocates builder | Usually outside hot path |
| Consistency | Strong when argument order is stable | Varies by call-site syntax | Strong through named fields | Strong through validation in builder | Strong if container config is controlled |
| Operability | Needs names for closure stages | Same issue with fewer stages | Easy to log fields | Easy to log builder state | Easy to inspect wiring, harder at call site |
| Cost | Low in functional languages, higher in others | Low when built in | Low for broad APIs | Higher code count | Higher setup cost |
| Team topology | Good for library functions | Good for local call sites | Good for public SDKs | Good for complex construction | Good for platform-owned services |
| Cognitive load | Higher for non-functional teams | Medium | Low | Medium | Medium to high |
| Type precision | High in typed curried languages | Depends on feature support | High with typed records | High | High, but indirect |

## 13. Related and incompatible patterns

**Partial Application** composes directly with Currying. Currying creates a
chain that permits partial application at every stage. Partial application can
also exist without Currying in languages that bind arbitrary subsets of
arguments.

**Higher-Order Function** is the broader pattern. A curried function is a
higher-order function because most stages return another function. Collection
operators and parser combinators often become more expressive when their
callback APIs are designed for Currying.

**Function Composition** benefits from Currying when functions share a
single-input, single-output shape after specialization. The FSharp.Core
operators documentation lists composition operators among the standard
function operators
(https://fsharp.github.io/fsharp-core-docs/reference/fsharp-core-operators.html,
verified 2026-08-02).

**Pipeline** benefits from data-last curried APIs. A pipeline can feed the data
argument into a function that has already captured policy. Ramda describes its
API as arranged so the data operated on is generally supplied last
(https://ramdajs.com/, verified 2026-08-02).

**Decorator** can wrap any stage of a curried function, for example to trace
the moment a tenant id is bound separately from the moment a request is
processed.

**Builder** replaces Currying when staged construction needs named steps,
validation between steps, branching, or many optional values.

**Long Parameter List** is related but not automatically solved. Currying a
long parameter list can hide the smell rather than remove it. When arguments
belong together, introduce a parameter object or domain value.

**Command** can be a better fit when the final action must be queued,
serialized, retried, or authorized as a unit. A closure may capture data that
cannot be inspected or persisted safely.

**Reader or dependency-passing style** can replace Currying when many functions
need the same environment. Currying works well for one or two stable values.
When every function starts with `env -> ...`, a Reader-style abstraction or
plain dependency injection may express the shared environment more clearly.

**Memoization** composes with Currying at two levels. A stage can be memoized so
the same prefix returns the same specialized function, or the final result can
be memoized after all arguments are known. These are different caches. Prefix
memoization controls allocation and identity. Result memoization controls
domain work. Mixing them without names creates confusing cache metrics.

**Adapter** is often the boundary pattern. A tupled API, callback API, or
framework hook may demand one function shape while internal code uses another.
Small adapters keep the curried style local rather than forcing every boundary
consumer to adopt it.

## 14. Refactoring path in and out

To introduce Currying.

1. Find a function where call sites repeat the same prefix of arguments.
2. Confirm that the repeated prefix represents stable policy, not a domain
   object that deserves a name.
3. Reorder arguments so the most stable values come first and flowing data
   comes last. Do this as a separate refactoring if the function is public.
4. Add a curried wrapper beside the original function. Keep the original entry
   point during migration.
5. Name one or two common specializations in production code. Avoid anonymous
   chains in the first rollout.
6. Replace repeated call-site prefixes with the named specialization.
7. Add tests that prove the direct and curried forms produce the same result.
8. Remove the old form only after callers no longer rely on it, or keep both
   if the language community expects both tupled and curried APIs.

Named refactorings from Martin Fowler's catalog that often appear in this path
include **Introduce Parameter Object**, **Change Function Declaration**, and
**Extract Function**. Cite Fowler, *Refactoring*, 2nd edition, Addison-Wesley,
2018, chapters 6 and 11, for those refactoring names. No page claim is made
here because no page was verified during this entry.

To remove Currying.

1. Locate saved intermediate stages and list the bound values they represent.
2. Replace unclear positional stages with a named options object or value type.
3. Inline one-stage wrappers that are called in only one place.
4. Convert hot paths back to direct calls if profiling shows adapter overhead.
5. Preserve public compatibility through an adapter if external users consume
   the curried form.
6. Delete generic curry helpers if only one or two manual closure chains remain.

## 15. Testing and verification

Engineering judgement. Currying changes where defects appear. The domain
operation may be simple, while the binding order becomes the risky part.

Test the original operation and the curried adapter separately. For a pure
function, property tests are a good fit: for all inputs `a`, `b`, and `c`,
`curried(a)(b)(c)` should equal `plain(a, b, c)`. Table tests work well for
business functions because each row can show the bound prefix and final data.

For impure functions, test timing as well as result. The first stage should not
open a socket, write to a database, or send a metric unless the API is explicit
about doing setup at binding time. Many curried APIs are expected to be lazy
until the final data argument arrives. A test double can count when the side
effect occurs. The name of the test should say whether binding or final
execution is expected to trigger the effect.

Test named specializations, not only the generic helper. If production code
uses `priceInEur`, test that function directly. This catches argument-order
mistakes that a generic helper test would miss.

Mutation tests are useful for argument order. Swap two arguments in the
original operation or the wrapper and the specialization test should fail with
a domain-level assertion, not a low-level type error. This is valuable in
TypeScript and Python where two positions may both be strings.

Use fake dependencies at the first stage when Currying binds ports such as
clock, logger, repository, or client. The test should assert that the final
stage uses the fake and does not reach global state.

For concurrency, test that two specialized functions do not share mutable
capture by accident. Create two prefixes with different tenants or policies,
run their final stages interleaved, and assert that outputs stay separated. A
closure over module-level mutable state will often fail this test.

Add a negative test for missing final application in dynamically typed code.
For example, assert that a route handler returns a response object, not a
callable. In TypeScript, prefer explicit exported types for public curried
functions so the compiler catches a partially applied value at the boundary.

For runtime curry helpers, test arity-sensitive functions after adding default
or rest parameters. Lodash and Ramda both document arity-related behaviour for
their curry helpers
(https://lodash.com/docs/#curry and https://ramdajs.com/docs/#curry, both
verified 2026-08-02).

Performance verification belongs in microbenchmarks only if the curried
function is built or called inside a measured hot path. Otherwise, service-level
latency tests are more useful than timing the closure chain in isolation.

Snapshot tests are usually weak for this pattern. They can confirm a final
string, but they rarely prove that the binding structure is correct. Prefer
equivalence tests, stage-specific tests, and call-count assertions around
effects.

## 16. Observability signals

Engineering judgement. Currying is invisible unless the implementation names
what was bound.

Log or trace at the specialization point when the bound value changes runtime
behaviour. Good attributes include `function.name`, `bound.tenant`,
`bound.locale`, `bound.currency`, `bound.policy_version`, `bound.arity`, and
`stage`. Avoid logging secrets captured by closures.

A healthy dashboard shows a small, expected set of named specializations and
stable counts by specialization. For example, a billing service might show
`priceWith.taxProfile=de-standard` and `priceWith.currency=EUR` on formatting
spans. A validation service might show policy version and rule name at bind
time, then input counts at final execution time.

The act of binding can be an event worth tracing when the bound value changes
control flow. For example, a request router that builds a tenant-specific
handler can emit one span when the handler is built and a separate span when
the handler processes a request. This separates setup churn from request
volume. If setup spans rise with request count, the system may be rebuilding
specialized functions per request when it meant to reuse them.

A failing instance looks different. There may be high cardinality in bound
function labels, many anonymous closure names, repeated specialization inside a
hot loop, or a sudden rise in errors where the observed return type is
`function`. If the service has memory metrics, rising allocation rate during a
map or stream stage can point to rebuilding curried adapters per element.

Metrics that help include `curried_stage_created_total`,
`curried_stage_invoked_total`, `curried_final_invoked_total`,
`curried_stage_cache_hit_total`, and allocation rate around specialization
sites. These names are examples, not a standard. The point is to count both
stage creation and final use. A large gap between stage creation and final use
can reveal wasted binding or leaked closures.

Sampling logs should include stage names rather than source-code line numbers
alone. Line numbers move, and generic helpers often point every stage at the
same helper. A stage name such as `bindTenant`, `bindCurrency`, or
`bindPolicyVersion` gives operators a domain handle.

For JavaScript libraries, arity and function `length` should not be treated as
reliable telemetry for curried helper output. Lodash documents that its curry
method does not set `length` on the returned curried function
(https://lodash.com/docs/#curry, verified 2026-08-02).

## 17. Security and privacy implications

Engineering judgement. Currying is not a security control. Its security impact
comes from what closures capture and where specialized functions travel.

Positive security effects are possible. A top-level composition can bind an
authorization policy once and pass a narrower function downward, reducing the
number of lower-level functions that receive broad authority. A test can bind a
fake secret provider or fake clock without global mutation.

This is similar to capability-style programming. A function value can represent
permission to perform an action with some context already chosen. That is clean
inside one memory space and dangerous when function values are stored in broad
registries. Review who can call the specialized function, how long it lives,
and whether it can outlive the user or request that created it.

The risks are more common.

- A closure may capture a token, API key, user object, request body, or
  decrypted value and keep it alive longer than a direct call would.
- A partially applied function may cross a trust boundary, such as being stored
  in a queue or callback registry, with authority hidden inside it.
- A curried builder may bind tenant or user context early and then be reused
  after the request ends.
- Logging a closure's captured values for debugging can leak sensitive data.
- Equality and caching of closures can be misleading. Two functions with the
  same observable behaviour are not necessarily the same value, and one
  function value may carry private state.

Treat curried functions that capture authority as capabilities. Name them,
limit their lifetime, avoid serializing them, and prefer explicit data transfer
objects at process or network boundaries.

Privacy review should ask what a heap dump or closure inspector would reveal.
If a closure captures a full user record when it needs only a locale, bind the
locale. If it captures a request object when it needs only a tenant id, bind the
tenant id. Currying rewards small captures. Large captures turn a narrow helper
into a hidden data container.

## Code examples

The examples below are intentionally small and dependency-free. They show
manual Currying rather than a generic library helper, because the shape is the
pattern.

TypeScript.

```typescript
type Money = string;

type Curried3<A, B, C, R> = (a: A) => (b: B) => (c: C) => R;

function curry3<A, B, C, R>(fn: (a: A, b: B, c: C) => R): Curried3<A, B, C, R> {
  return (a: A) => (b: B) => (c: C) => fn(a, b, c);
}

const formatPrice = (taxRate: number, currency: string, amount: number): Money => {
  const total = amount * (1 + taxRate);
  return `${currency} ${total.toFixed(2)}`;
};

const priceWith = curry3(formatPrice);
const priceInEur = priceWith(0.19)("EUR");

console.log(priceInEur(100));
```

Python.

```python
from collections.abc import Callable

def curry2(fn: Callable[[str, str], str]) -> Callable[[str], Callable[[str], str]]:
    def with_prefix(prefix: str) -> Callable[[str], str]:
        def with_value(value: str) -> str:
            return fn(prefix, value)
        return with_value
    return with_prefix

def label(prefix: str, value: str) -> str:
    return f"{prefix}: {value}"

as_error = curry2(label)("error")

print(as_error("disk full"))
```

Go.

```go
package main

import "fmt"

type PriceFormatter func(float64) string

func FormatPrice(taxRate float64) func(string) PriceFormatter {
	return func(currency string) PriceFormatter {
		return func(amount float64) string {
			total := amount * (1 + taxRate)
			return fmt.Sprintf("%s %.2f", currency, total)
		}
	}
}

func main() {
	priceInEur := FormatPrice(0.19)("EUR")
	fmt.Println(priceInEur(100))
}
```

Rust.

```rust
fn format_price(tax_rate: f64) -> impl Fn(&'static str) -> Box<dyn Fn(f64) -> String> {
    move |currency| {
        Box::new(move |amount| {
            let total = amount * (1.0 + tax_rate);
            format!("{currency} {total:.2}")
        })
    }
}

fn main() {
    let price_in_eur = format_price(0.19)("EUR");
    println!("{}", price_in_eur(100.0));
}
```

## 18. References

- Haskell B. Curry and Robert Feys, *Combinatory Logic*, volume 1,
  North-Holland, 1958, chapter 1. Historical background only. No page claim
  made.
- Moses Schönfinkel, "Über die Bausteine der mathematischen Logik", 1924.
  Historical background only. No page claim made.
- Internet Encyclopedia of Philosophy, "Haskell Brooks Curry",
  https://iep.utm.edu/haskell-brooks-curry/, verified 2026-08-02.
- Haskell.org, "A Gentle Introduction to Haskell, Version 98, Functions",
  https://www.haskell.org/tutorial/functions.html, verified 2026-08-02.
- GHC base 4.11.1.0 documentation, "Prelude",
  https://downloads.haskell.org/~ghc/8.4-latest/docs/html/libraries/base-4.11.1.0/Prelude.html,
  verified 2026-08-02.
- Ramda documentation, "curry",
  https://ramdajs.com/docs/#curry, verified 2026-08-02.
- Ramda home page, "Why Ramda",
  https://ramdajs.com/, verified 2026-08-02.
- Lodash documentation, "_.curry",
  https://lodash.com/docs/#curry, verified 2026-08-02.
- React Redux documentation, "connect()",
  https://react-redux.js.org/api/connect, verified 2026-08-02.
- FSharp.Core API reference, "Operators",
  https://fsharp.github.io/fsharp-core-docs/reference/fsharp-core-operators.html,
  verified 2026-08-02.
- Scala Standard Library 2.13.18, "scala.Function2",
  https://www.scala-lang.org/api/2.13.x/scala/Function2.html, verified
  2026-08-02.
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapters 6 and 11. Refactoring names only. No
  page claim made.
