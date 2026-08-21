---
name: Reader Monad
slug: reader-monad
family: 16-functional
category: Functional
aliases: [Environment Monad, Reader, ReaderT, MonadReader]
first_described: "Jones 1995"
maturity: established
related: [monad, applicative, functor, tagless-final, dependency-injection]
incompatible_with: [global-mutable-state, service-locator]
verified: 2026-08-02
---

# Reader Monad

## 1. Name, aliases, and lineage

The canonical name is Reader Monad. In Haskell documentation it is also called
the Environment monad, and the `ReaderT` transformer is described as adding a
read-only environment to another monad. The GHC `mtl` documentation records the
core type as `type Reader r = ReaderT r Identity`, records `ReaderT r m a` as a
wrapper around a function from `r` to `m a`, and names the operations `ask`,
`reader`, and `local` on the `MonadReader` class
(https://downloads.haskell.org/~ghc/9.10.1/docs/libraries/mtl-2.3.1-aac9/Control-Monad-Reader.html,
verified 2026-08-02).

The lineage is best stated with care. Philip Wadler's chapter "Monads for
functional programming" popularized monads as a practical program structuring
device in functional programming, with case studies for evaluators, arrays, and
parsers. The bibliographic record places that chapter in *Advanced Functional
Programming*, Lecture Notes in Computer Science 925, pages 24 to 52, Springer,
1995 (https://www.research.ed.ac.uk/en/publications/monads-for-functional-programming/,
verified 2026-08-02). The GHC `mtl` documentation for `Control.Monad.Reader`
says the module is inspired by Mark P. Jones, "Functional Programming with
Overloading and Higher-Order Polymorphism", First International Spring School on
Advanced Functional Programming Techniques, Springer Lecture Notes in Computer
Science 925, 1995
(https://downloads.haskell.org/~ghc/9.10.1/docs/libraries/mtl-2.3.1-aac9/Control-Monad-Reader.html,
verified 2026-08-02). Springer's table of contents for that volume places
Jones's chapter on pages 97 to 136
(https://link.springer.com/book/10.1007/3-540-59451-5, verified 2026-08-02).

Three aliases need separation because teams use them differently.

- **Reader.** The pure form. A value of type `Reader Env A` is a computation
  that awaits an `Env` and produces an `A`.
- **Environment Monad.** The same idea named by its intent. It makes an
  immutable context available to a composed computation.
- **ReaderT.** The transformer form. A value of type `ReaderT Env M A` awaits
  an `Env` and produces `M A`, so it combines environment access with another
  effect such as I/O, errors, or async work.
- **MonadReader.** The type class interface used by Haskell libraries so code
  can ask for environment access without committing to one concrete stack. The
  GHC `mtl` documentation names `ask`, `local`, and `reader` as its core
  operations
  (https://downloads.haskell.org/~ghc/9.10.1/docs/libraries/mtl-2.3.1-aac9/Control-Monad-Reader.html,
  verified 2026-08-02).

Judgement. In application design conversations, "Reader" is often used for a
dependency passing style even when no library type called Reader is present.
That is acceptable when the same semantics hold. A read-only environment is
supplied once at the edge, and pure or effectful functions read from it without
mutating it.

## 2. Problem and context

A program has many functions that need the same read-only context. The context
may include configuration, a clock, a logger, feature flags, tenant metadata,
locale rules, or service handles. Passing that context as an explicit parameter
through every intermediate function is honest, but it spreads a plumbing detail
through code whose real concern is business logic. Hiding the same context in a
global variable removes the parameter noise but also removes locality, test
control, and the ability to run the same computation with two different
contexts in the same process.

Reader addresses the middle case. It keeps the context explicit at the program
boundary, but implicit within a composed computation. A Reader value is not the
result yet. It is a recipe that still needs an environment. Running the recipe
with one environment produces one result. Running the same recipe with another
environment produces another result. No shared cell is needed.

The pattern fits when functions form a pipeline or call graph where many nodes
need the same read-only dependency set, and the caller should decide which
environment to supply. It is not a general replacement for parameters. It earns
its place when ordinary parameter passing starts to obscure the main data flow,
when global access would damage tests, or when multiple interpretations of the
same program should run against different environments.

The Haskell `mtl` documentation states the computation type as computations
which read values from a shared environment, and describes the binding strategy
as applying both subcomputations to the inherited environment
(https://downloads.haskell.org/~ghc/9.10.1/docs/libraries/mtl-2.3.1-aac9/Control-Monad-Reader.html,
verified 2026-08-02). In TypeScript, `fp-ts` models `Reader<R, A>` as an
interface that is callable with `R` and returns `A`, and its module overview
describes `ask` and `asks` as accessors for the current context
(https://gcanti.github.io/fp-ts/modules/Reader.ts.html, verified 2026-08-02).

Judgement. The common application problem is dependency flow, not dependency
creation. Reader does not build the environment. It carries an already built
environment through a computation without handing that environment to every
intermediate function by name.

One useful way to recognize the context is to ask what would happen if the
environment were removed from every function signature and replaced by a
module-level variable. If that change would make the code shorter but make
tests less isolated, concurrent runs less trustworthy, or tenant-specific runs
harder to reason about, the code is in Reader territory. If that change would
make little difference because the value is read at one point and never passed
on, Reader is probably ceremony.

Another useful test is to look for "parameter tunneling". A function accepts
`config` only because a function three calls below needs `config`. The middle
function is not conceptually about configuration, yet its type says it is. Some
amount of tunneling is fine, because explicit data flow is valuable. Reader
becomes attractive when the tunneled value is read by many leaves and the
intermediate layers no longer communicate their own purpose clearly.

## 3. Forces

This dimension is engineering judgement unless a named source is cited.

- **Coupling.** Favoured between computation and concrete wiring. The program
  depends on an environment shape, not on a process-wide singleton. Sacrificed
  when the environment type becomes a large grab bag and every function can see
  more than it needs.
- **Latency.** Usually neutral. Reader adds function calls and closures. In
  most business code that cost is below I/O and allocation noise. In inner loops
  it can block inlining or allocate intermediate functions, so plain parameters
  can win.
- **Consistency.** Favoured for a single run. Every composed step sees the same
  environment unless `local` deliberately transforms it. Sacrificed if teams
  use `local` as hidden dynamic scoping and readers can no longer tell which
  value a step sees.
- **Operability.** Favoured when the environment is built at the edge and logged
  there. Sacrificed if a failure occurs deep inside a Reader chain and telemetry
  does not record which environment keys were present.
- **Cost.** Favoured by reducing repeated parameter lists and by making tests
  cheap to run with a small environment. Sacrificed through abstraction cost,
  library learning cost, and possible type error complexity.
- **Team topology.** Favoured when platform teams define narrow environment
  capabilities and product teams write computations that ask for them. Sacrificed
  if all teams share one central `AppEnv` type and every change creates a merge
  hotspot.
- **Cognitive load.** Favoured for people fluent in monadic composition.
  Sacrificed for readers unfamiliar with `ask`, `flatMap`, `local`, or
  transformer stacks. The value is a function in disguise, and that disguise
  must pay rent.
- **Test control.** Favoured. A test can run the same computation with a fake
  clock, logger, repository, or config value without patching globals.

A pattern that has no cost is being described as a slogan. Reader buys explicit
context at the boundary and compositional context inside. It pays in
indirection, type signatures, and the temptation to make the environment too
wide.

## 4. Applicability and non-applicability

Reach for Reader when the following conditions hold.

- Many functions need the same immutable context and the context is not the main
  business value being transformed.
- The caller at the edge should choose dependencies, configuration, or services,
  while inner code should remain ordinary computation.
- The same program should run with a live environment in production and a test
  environment in tests.
- A pipeline combines small computations that all require the same context, and
  the codebase already accepts functional composition.
- Local overrides are meaningful. For example, a subcomputation should run with
  a different timeout, locale, tenant, or log prefix while the outer environment
  remains unchanged.
- The language or library offers a Reader, Kleisli, ZIO environment, or typed
  effect context that the team already uses.

Do NOT reach for Reader in these cases.

- **The dependency is needed by one function only.** Pass it as a parameter.
  Reader would hide a simple fact behind a combinator vocabulary.
- **The context changes as the computation runs.** Use State, explicit return
  values, or an effect that models mutation. Reader promises shared input, not
  changing data.
- **The data is request input, not ambient context.** A payment amount, command
  payload, or parsed message should remain an explicit argument. Reader is for
  background context.
- **The environment is large and unfocused.** A single `AppEnv` with dozens of
  fields turns Reader into a typed global. Split the environment into small
  capabilities or use constructor injection.
- **The team does not use monadic composition elsewhere.** Reader can become an
  isolated local dialect. In that setting, constructor injection may be easier
  to maintain.
- **You need runtime discovery by string or key.** Reader's normal strength is a
  statically known environment shape. A plugin registry, map, or service
  container is a closer fit for dynamic lookup.
- **You need lifetime management.** Reader can carry a connection pool handle,
  but it does not acquire or release that pool. Use Resource, bracket, scope, or
  the host framework's lifecycle API for ownership.
- **You need cross-cutting interception.** Reader does not by itself add retry,
  metrics, authorization, or transactions. It can carry those capabilities, but
  the behavior must still be called or composed.
- **The call graph is shallow.** Two explicit parameters over two calls are
  clearer than a Reader stack.

## 5. Structure

The participants are named by role rather than by class.

- **Environment.** The immutable context supplied by the runner. It may be a
  record, interface, service map, tuple, or typed capability set. It should be
  as narrow as the computation permits.
- **Reader computation.** A value representing `Environment -> Result` in the
  pure form, or `Environment -> Effect<Result>` in the transformer form. The
  computation is inert until an environment is supplied.
- **Accessor.** A small operation that reads the whole environment or selects
  one field. In Haskell and `fp-ts`, these are named `ask` and `asks`
  (https://downloads.haskell.org/~ghc/9.10.1/docs/libraries/mtl-2.3.1-aac9/Control-Monad-Reader.html,
  verified 2026-08-02;
  https://gcanti.github.io/fp-ts/modules/Reader.ts.html, verified 2026-08-02).
- **Binder.** The operation that sequences two computations while passing the
  same environment to both. In many libraries this is `flatMap`, `chain`, or
  `>>=`.
- **Local transformer.** An operation that runs a subcomputation under a
  derived environment. Haskell names this operation `local`, and documents it as
  executing a computation in a modified environment
  (https://downloads.haskell.org/~ghc/9.10.1/docs/libraries/mtl-2.3.1-aac9/Control-Monad-Reader.html,
  verified 2026-08-02).
- **Runner.** The boundary function that supplies the environment. Examples are
  `runReader`, calling a `Reader<R, A>` as a function in `fp-ts`, or providing a
  ZIO environment to an effect.

The key relationship is simple. The runner supplies one environment. Accessors
read from it. The binder passes the same environment to each composed step.
`local` is the one sanctioned way to alter what a nested step sees, and it does
so by deriving a new environment rather than by mutating the existing one.

## 6. ASCII structure diagram

```
   +===================+       supplied once       +=====================+
   |      Runner       | ========================> |     Environment     |
   |===================|                           |=====================|
   | run(program, env) |                           | config, clock, log  |
   +===================+                           +=====================+
             |
             | calls with env
             v
   +===================+        ask / asks         +=====================+
   | Reader Program    | ========================> |     Accessor        |
   |===================|                           |=====================|
   | Env => Result     |                           | Env => selected val |
   +===================+                           +=====================+
             |
             | flatMap / chain passes same env
             v
   +===================+        local              +=====================+
   | Subcomputation    | <======================== | Env Transformer     |
   |===================|                           |=====================|
   | Env => Result2    |                           | Env2 => Env         |
   +===================+                           +=====================+

   No participant writes to Environment. A nested run can receive a derived
   Environment, but the outer Environment remains unchanged.
```

## 7. Dynamics

Reader's runtime behavior is easier to understand by expanding the wrapper. A
Reader value is a function waiting for an environment. Sequencing builds a new
function that, when called later, gives the same environment to the first step
and to the next step selected from the first result.

```
Client       Runner        Program            Step A          Step B
  |            |              |                  |               |
  |== env ====>|              |                  |               |
  |            |== call =====>|                  |               |
  |            |              |== env =========>|               |
  |            |              |<== a ===========|               |
  |            |              |== choose B(a) =================>|
  |            |              |== same env ====================>|
  |            |              |<== b ===========================|
  |            |<== result ===|                  |               |
  |<== result =|              |                  |               |
```

With `local`, only the nested segment changes what it sees.

```
Outer env: { region: "eu", logPrefix: "checkout" }

Program
  |
  | ask.region       -> "eu"
  |
  | local(addDebugPrefix)
  v
Nested program sees: { region: "eu", logPrefix: "debug.checkout" }
  |
  | ask.logPrefix    -> "debug.checkout"
  v
Outer program resumes with original env.
```

The same composed program can be run more than once.

```
program(testEnv) -> deterministic test result
program(liveEnv) -> production result
program(euEnv)   -> EU tenant result
program(usEnv)   -> US tenant result
```

Judgement. This repeatability is the design center. If running the same value
with two environments is not useful, Reader may be the wrong abstraction.

## 8. Implementation variants

**Pure Reader as a function.** The smallest form is `Env -> A`. Haskell's
`mtl` documentation says the partially applied function type `(->) r` is a
simple reader monad
(https://downloads.haskell.org/~ghc/9.10.1/docs/libraries/mtl-2.3.1-aac9/Control-Monad-Reader.html,
verified 2026-08-02). This form is easy to explain and works well in
TypeScript, Python, Go, and other languages with closures. It has no effect
channel, so failures and I/O must be represented in the result or handled
outside.

**Newtype or wrapper Reader.** Haskell wraps the function in `ReaderT r
Identity`, while `fp-ts` exposes `Reader<R, A>` as a callable interface
(https://downloads.haskell.org/~ghc/9.10.1/docs/libraries/mtl-2.3.1-aac9/Control-Monad-Reader.html,
verified 2026-08-02;
https://gcanti.github.io/fp-ts/modules/Reader.ts.html, verified 2026-08-02).
The wrapper gives names to operations, supports instances, and improves type
errors in some languages. It can feel ceremonial when ordinary functions would
do.

**ReaderT over an effect.** `ReaderT Env M A` is the common form when the
program both reads an environment and performs another effect. The `fp-ts`
`ReaderT` documentation says it adds a read-only environment to a given monad,
with `of` ignoring the environment and `chain` passing the inherited
environment to both subcomputations
(https://gcanti.github.io/fp-ts/modules/ReaderT.ts.html, verified
2026-08-02). This form is powerful but can produce deep stacks and dense types.

**Kleisli encoding.** Cats defines `Reader[A, B]` as `Kleisli[Id, A, B]`, and
its Kleisli documentation describes the shape as taking a read-only value and
producing a value with it
(https://typelevel.org/cats/datatypes/kleisli.html, verified 2026-08-02).
Kleisli generalizes Reader by allowing the output to live in an effect `F`.
The trade is that the name "Reader" becomes one view of a more general arrow.

**Typed effect environment.** ZIO models effects as `ZIO[-R, +E, +A]`, where
`R` is the environment required to run the effect
(https://zio.dev/1.0.18/reference/contextual/, verified 2026-08-02). The ZIO
reference describes `ZEnvironment` as a type-level map for maintaining the
environment of a ZIO effect and `ZLayer` as a recipe to build an environment
(https://zio.dev/reference/, verified 2026-08-02). This variant turns Reader
from a small pattern into the dependency axis of an effect system.

**Object constructor injection.** In object-oriented code, a class with
dependencies stored in final fields can be viewed as a manual Reader runner:
the constructor supplies the environment, and methods read from it. This is
not the Reader Monad unless the computations are first-class values that
compose as readers. It is often the clearer local substitute.

**Implicit context parameters.** Some languages support implicit or contextual
parameters. They remove call-site noise but can hide dependency flow. Reader is
more explicit because the environment type remains visible in the program type.

**Capability slices.** Instead of one environment record, a computation can
require a small interface such as `HasClock & HasLogger`. In TypeScript and
Scala effect libraries this can keep dependency requirements narrow. The cost
is more type machinery.

**Reader as module boundary.** A module can export Reader programs and keep the
environment type private except for a small constructor or runner. This lets the
module author change internal dependency layout without changing callers. The
trade is that callers may lose visibility into which service a program needs
unless the exported type or documentation names the capability.

**Reader over request context.** Web code sometimes treats request metadata as
the environment. That can work for trace identifiers, locale, tenant id, and
authorization claims after validation. It is a poor fit for mutable request
body parsing or streaming input. The request payload is business input and
should remain explicit. The request context is ambient information and can be
read through Reader.

**Manual closure bundle.** In languages without a popular Reader library, a
team can write functions that close over the environment at the boundary and
return smaller functions. This is a halfway form. It removes repeated
parameters but loses the shared `map`, `flatMap`, and `local` vocabulary. It is
often the right local choice when a full functional library would be too much
for the codebase.

## 9. Known production uses

**Haskell `mtl`, `Control.Monad.Reader`.** The GHC library documentation
includes `MonadReader`, `Reader`, `ReaderT`, `ask`, `local`, `reader`,
`runReader`, and `runReaderT`. It describes Reader computations as reading
values from a shared environment and records the simple function instance for
`(->) r`
(https://downloads.haskell.org/~ghc/9.10.1/docs/libraries/mtl-2.3.1-aac9/Control-Monad-Reader.html,
verified 2026-08-02).

**TypeScript `fp-ts`, `Reader` and `ReaderT`.** `fp-ts` documents `Reader<R,
A>` as an interface callable with `R` returning `A`, lists a `Monad` instance,
and provides `ask`, `asks`, `local`-style access through combinators, and
`ReaderT` for adding a read-only environment to another monad
(https://gcanti.github.io/fp-ts/modules/Reader.ts.html, verified
2026-08-02;
https://gcanti.github.io/fp-ts/modules/ReaderT.ts.html, verified 2026-08-02).

**Typelevel Cats, `Reader` as `Kleisli[Id, A, B]`.** Cats documents `Kleisli`
as representing `A => F[B]`, and its datatype guide states that Cats defines a
`Reader` alias as `Kleisli[Id, A, B]`
(https://github.com/typelevel/cats/blob/main/core/src/main/scala/cats/data/Kleisli.scala,
verified 2026-08-02;
https://typelevel.org/cats/datatypes/kleisli.html, verified 2026-08-02).

**ZIO environment.** ZIO documents `ZIO[-R, +E, +A]` as an effect that requires
an input type `R` as environment and may fail with `E` or succeed with `A`
(https://zio.dev/1.0.18/reference/contextual/, verified 2026-08-02). Its
reference also names `ZEnvironment` and `ZLayer` as contextual data types for
maintaining and building environments
(https://zio.dev/reference/, verified 2026-08-02).

**Effect for TypeScript, `Context`.** Effect's source documentation for
`Context` describes service keys as typed handles for storing, retrieving, and
requiring services in a `Context`, and describes the underlying structure as a
typed map from service identifiers to implementations
(https://github.com/Effect-TS/effect/blob/main/packages/effect/src/Context.ts,
verified 2026-08-02;
https://github.com/Effect-TS/effect/blob/main/migration/services.md, verified
2026-08-02). This is a typed environment mechanism in the same dependency
passing family as Reader, though Effect's full model is larger than plain
Reader.

## 10. Consequences

Positive.

- The environment is explicit at the edge. A runner must supply it, so tests and
  production wiring can differ without patching process globals.
- Intermediate functions no longer repeat parameters that are not their main
  data. This can make the main business flow easier to read.
- Composition preserves a single environment by construction. Every step in a
  chain receives the same context unless `local` says otherwise.
- It becomes cheap to run the same computation under several contexts, which is
  useful for tests, tenants, feature flag comparisons, and dry runs.
- Dependency requirements can be represented in types in languages and libraries
  that support typed environments.
- The pattern composes with error, async, and I/O effects through ReaderT,
  Kleisli, or a larger effect system.

Negative.

- Type signatures become heavier. `Env -> Result` is simple, but
  `ReaderT Env (Either Error) Result` or a large effect environment can slow
  reading and debugging.
- A broad environment turns into a typed global. The pattern does not stop a
  team from putting every service into one record.
- Control flow can be less obvious to people who do not read monadic chains
  fluently.
- `local` can become hidden dynamic scoping if used for behavior changes rather
  than small context adaptation.
- Stack traces may show combinators and closures instead of domain function
  names unless the implementation preserves useful frames.
- Performance can suffer in hot loops because composed readers create call
  layers. Measure before using Reader in tight numeric or parsing kernels.

## 11. Failure modes and misuse

This dimension is engineering judgement.

**Typed global environment.** Symptom. Tests build a huge fake environment with
many unrelated fields, and a small function can unexpectedly call a database,
clock, logger, and flag client. Cause. The project uses one broad `AppEnv`
instead of narrow environment slices. Fix. Split requirements into small
capabilities and make each Reader mention only the slice it reads.

**Reader where a parameter should be.** Symptom. A new contributor searches for
where a value enters the function and must jump through `ask` even though the
value is used once. Cause. Reader adopted for local code with a shallow call
graph. Fix. Inline the environment access into an explicit parameter.

**Hidden behavior through `local`.** Symptom. A nested function logs under a
different tenant, locale, or authorization scope than the outer request, and
the change is visible only in a combinator far above the call. Cause. `local`
used for policy changes rather than small adaptation. Fix. Restrict `local` to
mechanical environment projection or annotate policy-changing uses with tests
and telemetry.

**Effect ownership confusion.** Symptom. Connections, file handles, or spans
leak after tests, even though the Reader code is pure-looking. Cause. The
environment carries resources whose lifetime is not modeled by Reader. Fix. Use
Resource, bracket, scope, or framework lifecycle code to acquire and release
resources, then pass handles through Reader only while they are valid.

**Transformer stack opacity.** Symptom. A compiler error mentions several
stacked type constructors and the developer cannot tell whether the missing
piece is environment, error, async, or state. Cause. ReaderT stacked with other
effects without aliases or helper constructors. Fix. Introduce a named
application effect type, keep constructors near the boundary, and add small
helpers for common accessors.

**Environment drift between modules.** Symptom. Two modules define similar
environment records with slightly different field names, causing adapter code
to spread. Cause. No owned capability interfaces. Fix. Move stable capability
types to the module that owns the behavior and derive broader app environments
from those types.

**Accidental eager execution.** Symptom. A test constructs a Reader and observes
logging or network work before the environment is supplied. Cause. The code did
work while building the Reader rather than inside the returned function. Fix.
Move all environment-dependent behavior into the function body and keep
construction inert.

**Unlogged environment selection.** Symptom. Production failures differ by
tenant or region but traces do not show which environment ran the computation.
Cause. The runner supplies context silently. Fix. Log environment identity at
the boundary and attach non-sensitive labels to spans.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

<table>
  <thead>
    <tr>
      <th>Force</th>
      <th>Reader Monad</th>
      <th>Explicit Parameters</th>
      <th>Constructor Injection</th>
      <th>Service Locator</th>
      <th>State Monad</th>
      <th>Dependency Injection Container</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Coupling to wiring</td>
      <td>Low at inner call sites</td>
      <td>Low but verbose</td>
      <td>Medium. Class owns fields</td>
      <td>High. Global lookup</td>
      <td>Low for state, poor for dependencies</td>
      <td>Low in code, higher in config</td>
    </tr>
    <tr>
      <td>Readability for small code</td>
      <td>Medium to low</td>
      <td>High</td>
      <td>High</td>
      <td>Medium</td>
      <td>Low if no changing state exists</td>
      <td>Medium</td>
    </tr>
    <tr>
      <td>Readability for deep pipelines</td>
      <td>High for fluent teams</td>
      <td>Low due repeated context</td>
      <td>Medium</td>
      <td>Medium</td>
      <td>Medium</td>
      <td>Medium</td>
    </tr>
    <tr>
      <td>Context mutation</td>
      <td>Not supported</td>
      <td>Manual</td>
      <td>Manual</td>
      <td>Often hidden</td>
      <td>Designed for change</td>
      <td>Depends on container</td>
    </tr>
    <tr>
      <td>Test control</td>
      <td>High. Supply fake env</td>
      <td>High. Pass fake args</td>
      <td>High. Build fake object</td>
      <td>Low unless locator is replaceable</td>
      <td>High for state behavior</td>
      <td>Medium to high</td>
    </tr>
    <tr>
      <td>Latency</td>
      <td>Function layers</td>
      <td>Direct calls</td>
      <td>Method calls</td>
      <td>Lookup cost</td>
      <td>Function layers plus state</td>
      <td>Container cost mainly at wiring</td>
    </tr>
    <tr>
      <td>Operability</td>
      <td>Needs runner labels</td>
      <td>Values visible in call graph</td>
      <td>Object identity visible</td>
      <td>Lookup hidden</td>
      <td>Needs state snapshots</td>
      <td>Container graph can be inspected</td>
    </tr>
    <tr>
      <td>Team topology</td>
      <td>Good with small capabilities</td>
      <td>Good until parameter lists sprawl</td>
      <td>Good per service boundary</td>
      <td>Poor. Shared locator</td>
      <td>Good for stateful logic</td>
      <td>Good with platform ownership</td>
    </tr>
    <tr>
      <td>Cognitive load</td>
      <td>Higher</td>
      <td>Low</td>
      <td>Low</td>
      <td>Low at first, high later</td>
      <td>Higher</td>
      <td>Medium</td>
    </tr>
    <tr>
      <td>Resource lifetime</td>
      <td>Not modeled</td>
      <td>Not modeled</td>
      <td>Can be tied to object</td>
      <td>Often unclear</td>
      <td>Not modeled</td>
      <td>Often modeled by framework</td>
    </tr>
  </tbody>
</table>

Reading of the table. Reader wins when shared read-only context crosses many
small composed functions. Explicit parameters win for local code. Constructor
injection wins for object-oriented service code. A DI container wins when object
graphs and lifetimes are the main problem. State wins when the data changes.
Service Locator is listed because teams often reach for it to avoid parameter
noise, but it hides dependency flow and conflicts with Reader's explicit edge.

The table also shows why Reader and constructor injection can coexist. A
long-lived service object can receive stable collaborators through its
constructor, then expose methods that build Reader programs for per-run context.
For example, a report service may hold a parser and renderer as constructor
dependencies, while the Reader environment carries tenant policy, clock, and
locale for one report run. Judgement. Mixing the two styles is sound when
lifetimes differ. It is confusing when both mechanisms carry the same
dependency.

## 13. Related and incompatible patterns

- **Monad.** Reader is one concrete monad. It implements sequencing where the
  same environment is passed through each step. The general Monad entry covers
  the laws and shape.
- **Functor and Applicative.** Reader can map over its result, and independent
  readers can be applied under the same environment. Applicative style is often
  clearer when later steps do not depend on earlier results.
- **Kleisli.** Kleisli generalizes Reader from `Env -> A` to `Env -> F[A]`.
  Cats documents Reader as a Kleisli alias with `Id`
  (https://typelevel.org/cats/datatypes/kleisli.html, verified 2026-08-02).
- **ReaderT.** ReaderT composes environment access with another effect. It is
  the production form when reading config and doing I/O happen in one program.
- **Tagless Final.** Tagless final often passes capabilities through type class
  constraints, while Reader passes them through an environment value. They can
  compose, but using both heavily can make requirements hard to read.
- **Dependency Injection.** Constructor injection and Reader solve overlapping
  dependency passing problems. Constructor injection is usually clearer for
  long-lived objects. Reader is usually clearer for first-class computations.
- **State Monad.** State replaces Reader when the context must evolve and the
  new value must be returned with the result. Using Reader with mutable fields
  inside the environment is State without the type saying so.
- **Service Locator.** Incompatible in intent. Reader makes the environment
  supplied at the edge. Service Locator hides lookup behind global access.
- **Global Mutable State.** Incompatible with Reader's main value. If a Reader
  computation reads a global cell, running it with a different environment is no
  longer enough to control behavior.
- **Context Object.** Related but weaker. A context object passed explicitly is
  the raw material. Reader makes context passing compositional.

## 14. Refactoring path in and out

Introducing Reader into parameter-heavy code.

1. Identify a repeated parameter group that is read but not modified. Examples
   are `config`, `clock`, and `logger`.
2. Create a small environment type for that group. Avoid a project-wide
   catch-all environment.
3. Convert one leaf function from `(env, input) -> output` to
   `input -> Reader<env, output>`, or to `Reader<env, output>` if input is
   already captured.
4. Add `ask` or field access helpers for the values the leaf reads.
5. Convert its caller by composing the returned Reader rather than extracting
   the environment and passing it by hand.
6. Move upward one call at a time. Stop when the boundary is a natural runner,
   such as a request handler, CLI command, job entry, or test.
7. At the boundary, run the Reader with the environment built by existing
   wiring code.
8. Add a test that runs the same Reader with two environments. This proves the
   refactor preserved edge control.

Practical migration rule. Keep the first migration boring. Do not introduce
ReaderT, effect aliases, and capability splitting in the same commit unless the
code already uses those ideas. Start with a pure Reader around one repeated
read-only group. After that compiles and tests pass, decide whether the outer
effect belongs in the type. This protects reviewers from having to judge
dependency flow and effect modeling at the same time.

When introducing Reader into a team unfamiliar with it, keep the first helper
names plain. `askConfig`, `withTenant`, and `runWithEnv` are easier to review
than a full set of abstract type class operations. The monad laws still matter
for a custom wrapper, but the public surface can begin with domain names and
grow toward general combinators only when repeated patterns appear.

Removing Reader when it stops earning its place.

1. Find Readers that call `ask` once and have no composition value.
2. Inline the selected environment field as an explicit parameter.
3. For object-oriented modules, move stable dependencies into constructor
   fields and keep per-call data as method parameters.
4. Replace `local` with an explicit parameter transformation near the call if
   only one nested function needs the change.
5. Collapse the environment type after all Readers using a field are gone.
6. If the ReaderT stack is the problem but environment passing is still useful,
   introduce a named effect alias before deleting the pattern. The issue may be
   notation, not Reader itself.

Removal should preserve the boundary test from the introduction path. Before
deleting the Reader wrapper, keep a test that runs the old computation under
two environments. After replacing it with explicit parameters or constructor
fields, keep the same two cases. This catches accidental reintroduction of a
global value during cleanup.

Named refactorings that often apply are Introduce Parameter Object when forming
the environment, Replace Parameter with Method Call when a field can be derived
inside the environment, Inline Function when deleting thin readers, and Replace
Global Variable with Parameter when moving away from hidden state.

## 15. Testing and verification

This dimension is engineering judgement.

Reader improves tests by making the environment a plain value at the runner.
The main test double is not a mock object controlled by a framework. It is a
small environment value with fake services or deterministic functions.

Techniques.

- **Two-environment test.** Run the same computation with `testEnvA` and
  `testEnvB`. Assert that only environment-dependent outputs differ.
- **Narrow capability test.** Type or lint tests can guard that a function asks
  only for `ClockEnv` rather than all of `AppEnv`.
- **Fake service environment.** Supply a fake repository, clock, flag reader, or
  logger as fields in the environment.
- **Trace logger spy.** Use an environment logger that appends events to an
  array. After running the Reader, assert the events.
- **Local override test.** For any use of `local`, assert both the nested value
  and the outer value after the nested computation returns.
- **Law check for custom wrappers.** If the team writes its own Reader wrapper,
  test Functor identity and composition, Applicative identity and homomorphism,
  and Monad left identity, right identity, and associativity.

What became easier.

- Tests do not patch module globals.
- The same program value can be exercised under many contexts.
- Dependency fakes are ordinary data, so they can be built inline.

What became harder.

- A failing test may require expanding combinators to see which accessor read
  the wrong field.
- If the environment is too broad, tests can pass with accidental dependencies
  that production cannot satisfy.
- In transformer stacks, the test must supply both environment and the outer
  effect interpreter.

Verification checklist.

1. Constructing a Reader performs no I/O.
2. Running with the same immutable environment is repeatable, except for
   effects modeled in the outer monad.
3. Each accessor has a test or is trivial field selection.
4. `local` changes only the intended nested scope.
5. Production runners log a non-sensitive environment identity.

## 16. Observability signals

This dimension is engineering judgement.

Reader hides environment flow from ordinary call stacks, so the runner should
make that flow visible.

What to record.

- At the runner, record the program name, environment version, tenant or region
  label if non-sensitive, and dependency bundle name.
- On `local` uses that change policy, record the old and new policy label. Do
  not log secrets or full config records.
- Count executions by program name and environment label.
- Count environment construction failures separately from Reader execution
  failures. Reader often gets blamed for a missing dependency that was actually
  a wiring failure.
- For effect systems with typed environments, record missing service or missing
  layer errors with the service key name.
- Track duration of the whole Reader run, not every small accessor. Accessors
  should be cheap.

A healthy dashboard. Execution counts match expected traffic. Environment
labels match deploy configuration. Missing-service errors are zero. Duration
tracks business work rather than environment access. `local` policy changes are
rare and tied to known workflows.

A failing dashboard. One environment label disappears after deploy. A default
environment label appears in production. Missing-service errors spike for one
program. One tenant has a different `local` policy label from peer tenants.
Reader run duration grows while downstream I/O spans stay flat, which points to
CPU work inside pure composition or repeated environment derivation.

Operationally, the runner is the best place to draw the telemetry boundary.
Logging every `ask` call is usually noise and can expose sensitive field names.
Logging the runner gives one clear record of which environment was supplied to
which program. If a program has nested policy changes through `local`, record
those changes as span events with redacted labels. The goal is not to make the
entire environment visible. The goal is to make environment selection
auditable.

For incident response, keep enough information to replay a computation with a
matching non-production environment. That often means recording environment
version, feature flag snapshot id, tenant class, and region. It does not mean
recording secrets, tokens, or raw customer data. Reader makes replay feasible
because the environment is a value supplied at the edge. Telemetry should help
reconstruct a safe equivalent of that value.

## 17. Security and privacy implications

This dimension is engineering judgement.

Reader can improve security by removing globals and making the runner choose
the environment for a request, job, or test. That choice can make tenant,
region, clock, and authorization dependencies more reviewable. It can also
damage security if the environment is broad or if `local` is allowed to alter
policy invisibly.

Risks.

- **Authority creep.** A broad environment gives every computation access to
  services it does not need. A formatting function should not be able to read a
  payment repository because both live in `AppEnv`.
- **Tenant confusion.** If tenant identity sits in the environment, an incorrect
  runner or `local` transformation can run valid code under the wrong tenant.
- **Secret logging.** Environment records often include tokens, connection
  strings, or account identifiers. Observability should log stable labels, not
  full environment values.
- **Policy shadowing.** Nested `local` calls can change authorization, locale,
  or region policy for a subcomputation. That is powerful and should be rare.
- **Fake environment in production.** Test environments are easy to build. The
  deploy path must prevent a fake payment, mail, or auth service from reaching
  production.

Mitigations.

- Use narrow capability environments.
- Keep environment construction in a small number of reviewed runner modules.
- Make sensitive fields non-printable where the language allows it.
- Attach an environment fingerprint or version to traces without including
  secrets.
- Add tests that production runners use live service bindings and test runners
  use fake bindings.
- Treat policy-changing `local` calls as security-sensitive code.

Reader is silent on encryption, authentication protocols, and network trust. It
does not supply those controls. It only changes how dependency context reaches
code that may use those controls.

## Code examples

Three languages are shown. TypeScript shows the direct higher-order function
form that matches `fp-ts`' callable `Reader<R, A>` shape. Python shows a small
wrapper with `map`, `flat_map`, `ask`, and `local`. Go shows the same pattern
with named function types and explicit methods. Java, Rust, and Swift are
omitted because the three examples cover the central shape with less ceremony.

### TypeScript

```typescript
type Reader<Env, A> = (env: Env) => A;

const of = <Env, A>(value: A): Reader<Env, A> => () => value;

const ask = <Env>(): Reader<Env, Env> => (env) => env;

const map =
  <Env, A, B>(reader: Reader<Env, A>, f: (value: A) => B): Reader<Env, B> =>
  (env) =>
    f(reader(env));

const flatMap =
  <Env, A, B>(
    reader: Reader<Env, A>,
    f: (value: A) => Reader<Env, B>,
  ): Reader<Env, B> =>
  (env) =>
    f(reader(env))(env);

const local =
  <Outer, Inner, A>(
    reader: Reader<Inner, A>,
    f: (outer: Outer) => Inner,
  ): Reader<Outer, A> =>
  (outer) =>
    reader(f(outer));

type Env = {
  readonly taxRate: number;
  readonly currency: string;
};

const subtotal = of<Env, number>(100);
const total = flatMap(subtotal, (amount) =>
  map(ask<Env>(), (env) => `${env.currency} ${amount * (1 + env.taxRate)}`),
);

const euTotal = local(total, (env: Env) => ({
  ...env,
  currency: "EUR",
}));

console.log(total({ taxRate: 0.08, currency: "USD" }));
console.log(euTotal({ taxRate: 0.2, currency: "USD" }));
```

### Python

```python
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

Env = TypeVar("Env")
Inner = TypeVar("Inner")
A = TypeVar("A")
B = TypeVar("B")


@dataclass(frozen=True)
class Reader(Generic[Env, A]):
    run: Callable[[Env], A]

    def map(self, f: Callable[[A], B]) -> "Reader[Env, B]":
        return Reader(lambda env: f(self.run(env)))

    def flat_map(self, f: Callable[[A], "Reader[Env, B]"]) -> "Reader[Env, B]":
        return Reader(lambda env: f(self.run(env)).run(env))

    def local(self, f: Callable[[Inner], Env]) -> "Reader[Inner, A]":
        return Reader(lambda env: self.run(f(env)))


def ask() -> Reader[Env, Env]:
    return Reader(lambda env: env)


@dataclass(frozen=True)
class Config:
    tax_rate: float
    currency: str


total: Reader[Config, str] = Reader(lambda _env: 100.0).flat_map(
    lambda amount: ask().map(
        lambda env: f"{env.currency} {amount * (1 + env.tax_rate):.2f}"
    )
)

eu_total = total.local(lambda env: Config(env.tax_rate, "EUR"))

print(total.run(Config(0.08, "USD")))
print(eu_total.run(Config(0.2, "USD")))
```

### Go

```go
package main

import "fmt"

type Reader[E any, A any] func(E) A

func Of[E any, A any](value A) Reader[E, A] {
	return func(E) A { return value }
}

func Ask[E any]() Reader[E, E] {
	return func(env E) E { return env }
}

func Map[E any, A any, B any](reader Reader[E, A], f func(A) B) Reader[E, B] {
	return func(env E) B { return f(reader(env)) }
}

func FlatMap[E any, A any, B any](
	reader Reader[E, A],
	f func(A) Reader[E, B],
) Reader[E, B] {
	return func(env E) B { return f(reader(env))(env) }
}

func Local[Outer any, Inner any, A any](
	reader Reader[Inner, A],
	f func(Outer) Inner,
) Reader[Outer, A] {
	return func(outer Outer) A { return reader(f(outer)) }
}

type Config struct {
	TaxRate  float64
	Currency string
}

func main() {
	subtotal := Of[Config](100.0)
	total := FlatMap(subtotal, func(amount float64) Reader[Config, string] {
		return Map(Ask[Config](), func(env Config) string {
			return fmt.Sprintf("%s %.2f", env.Currency, amount*(1+env.TaxRate))
		})
	})

	euTotal := Local(total, func(env Config) Config {
		env.Currency = "EUR"
		return env
	})

	fmt.Println(total(Config{TaxRate: 0.08, Currency: "USD"}))
	fmt.Println(euTotal(Config{TaxRate: 0.2, Currency: "USD"}))
}
```

## 18. References

- Philip Wadler, "Monads for functional programming", in Johan Jeuring and Erik
  Meijer, editors, *Advanced Functional Programming*, Lecture Notes in Computer
  Science 925, Springer, 1995, pages 24 to 52.
  https://www.research.ed.ac.uk/en/publications/monads-for-functional-programming/,
  verified 2026-08-02.
- Mark P. Jones, "Functional Programming with Overloading and Higher-Order
  Polymorphism", in Johan Jeuring and Erik Meijer, editors, *Advanced
  Functional Programming*, Lecture Notes in Computer Science 925, Springer,
  1995, pages 97 to 136.
  https://web.cecs.pdx.edu/~mpj/pubs/springschool.html, verified 2026-08-02.
- Springer, *Advanced Functional Programming*, Lecture Notes in Computer Science
  925, table of contents and bibliographic information.
  https://link.springer.com/book/10.1007/3-540-59451-5, verified 2026-08-02.
- GHC libraries, `mtl-2.3.1`, `Control.Monad.Reader` documentation.
  https://downloads.haskell.org/~ghc/9.10.1/docs/libraries/mtl-2.3.1-aac9/Control-Monad-Reader.html,
  verified 2026-08-02.
- `fp-ts`, `Reader.ts` module documentation.
  https://gcanti.github.io/fp-ts/modules/Reader.ts.html, verified 2026-08-02.
- `fp-ts`, `ReaderT.ts` module documentation.
  https://gcanti.github.io/fp-ts/modules/ReaderT.ts.html, verified 2026-08-02.
- Typelevel Cats, Kleisli datatype documentation.
  https://typelevel.org/cats/datatypes/kleisli.html, verified 2026-08-02.
- Typelevel Cats, `cats.data.Kleisli` source documentation.
  https://github.com/typelevel/cats/blob/main/core/src/main/scala/cats/data/Kleisli.scala,
  verified 2026-08-02.
- ZIO, contextual effects introduction for `ZIO[-R, +E, +A]`.
  https://zio.dev/1.0.18/reference/contextual/, verified 2026-08-02.
- ZIO, reference page for contextual data types including `ZEnvironment` and
  `ZLayer`. https://zio.dev/reference/, verified 2026-08-02.
- Effect, `Context` source documentation.
  https://github.com/Effect-TS/effect/blob/main/packages/effect/src/Context.ts,
  verified 2026-08-02.
- Effect, service migration documentation describing `Context.Service` and the
  typed service map.
  https://github.com/Effect-TS/effect/blob/main/migration/services.md,
  verified 2026-08-02.
