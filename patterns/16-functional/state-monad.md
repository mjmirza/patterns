---
name: State Monad
slug: state-monad
family: 16-functional
category: Functional
aliases: [State, StateT, MonadState, Stateful, State-passing Monad]
first_described: "Wadler 1992 and 1995"
maturity: established
related: [monad, reader-monad, writer-monad, result-either, lens, traversable]
incompatible_with: [shared-mutable-state, hidden-global-state, unbounded-state-threading]
verified: 2026-08-02
---

# State Monad

## 1. Name, aliases, and lineage

The canonical name is State Monad. In Haskell libraries the common names are
`State`, `StateT`, and `MonadState`. The `transformers` package documents
`Control.Monad.Trans.State.Strict` as strict state monads that pass an updatable
state through a computation, with the concrete operations `runState`,
`evalState`, `execState`, `get`, `put`, `modify`, and `gets`
(https://hackage.haskell.org/package/transformers-0.4.1.0/docs/src/Control-Monad-Trans-State-Strict.html,
verified 2026-08-02). In Scala, Typelevel Cats exposes `State` and `StateT`.
Its State page describes `State[S, A]` as a functional structure for application
state, shaped like a function from `S` to an updated `S` plus an `A`
(https://typelevel.org/cats/datatypes/state.html, verified 2026-08-02).
Its StateT page describes `StateT[F[_], S, A]` as the transformer form that
adds state handling to another effect `F`
(https://typelevel.org/cats/datatypes/statet.html, verified 2026-08-02).
In TypeScript, fp-ts exposes a `State<S, A>` interface represented as a function
from `S` to `[A, S]`, with `flatMap`, `evaluate`, and `execute`
(https://gcanti.github.io/fp-ts/modules/State.ts.html, verified 2026-08-02).

The software lineage comes through the monadic treatment of computational
effects. Philip Wadler's "Monads for functional programming" presents monads as
a way to structure functional programs with effects such as global state,
exception handling, output, and nondeterminism. The paper also has a named
section on state and models stateful computation as a function from an initial
state to a computed value and a final state. Wadler's note says an earlier
version appeared in the 1992 Marktoberdorf summer school proceedings and the
version cited here appeared in the 1995 Advanced Functional Programming volume,
sections 1 and 2.3
(https://homepages.inf.ed.ac.uk/wadler/papers/marktoberdorf/baastad.pdf,
verified 2026-08-02).

The pattern has several aliases. **State** is the common library type. **StateT**
is the monad transformer that wraps another effect. **MonadState** is the
Haskell type class interface for code that can read and write state without
naming the concrete stack. **Stateful** is the Cats MTL capability with `get`
and `set`; the Cats MTL page says `Stateful[F, S]` describes the ability to
read and write state values of type `S` in an `F[_]` context
(https://typelevel.org/cats-mtl/mtl-classes/stateful.html, verified
2026-08-02). **State-passing monad** is a descriptive name used when the focus
is the representation rather than the library type.

Engineering judgement. This catalog treats State Monad as a software pattern
when the state is local to a computation, passed from step to step by the bind
operation, and exposed only when the runner supplies an initial state. It is not
the same pattern as process-wide mutable state, database state, actor state, or
object fields, even when those mechanisms also change over time.

## 2. Problem and context

A computation needs a current value that changes after each step, and later
steps depend on the changed value. The value might be a parser cursor, a random
number seed, a symbol supply, a compiler environment under construction, a
cache, a simulation model, a game board, a validation context, or a small
domain state machine. The code should remain readable as a sequence of domain
steps, yet every step has to receive the current state and return the next
state.

Without this pattern, teams tend to write one of four shapes. They pass a state
parameter by hand through every function. They mutate an object, record, map, or
global variable that many functions can see. They split the algorithm into a
class whose fields act as scratch space. Or they hide the state in callbacks and
closures. Each shape can work, but each loses a different property. Manual state
passing makes the domain flow hard to see. Shared mutation makes call order and
aliasing part of correctness. Scratch fields make one run of the algorithm hard
to isolate from another run. Callback state often gives poor error messages and
awkward tests.

State Monad captures the mechanical part. A computation of type `State<S, A>`
can be viewed as a function that accepts an `S` and returns a pair containing an
`A` and the next `S`. `pure` returns a value without changing the state. `bind`
runs the first computation, takes the value it produced, asks the caller's
function for the next computation, and supplies that next computation with the
state produced by the first one. `get` returns the current state as the value.
`put` replaces the state. `modify` changes the state with a function. `gets`
reads a projection from the state.

The context matters. The state belongs to one logical run. It is not a public
store. The runner owns the initial state and decides what to do with the final
state. Inside the chain, domain steps can read and alter state without spelling
out the plumbing on every line. Outside the chain, the caller still sees a
plain input and a plain output.

State Monad fits especially well when the state is small enough to pass as a
value, when every update has a clear next-state meaning, and when tests benefit
from running the same computation with different initial states. It is weak
when changes must be visible to other threads during the run, when updates must
be durable before the final result is returned, or when the state becomes a bag
of unrelated data. The pattern makes state local and explicit at the boundary.
It does not make arbitrary mutation simple, cheap, or good.

## 3. Forces

This section is engineering judgement unless a cited source names a concrete
API.

- **Coupling.** Favoured between domain steps and state transport. A step can
  ask for `get`, `put`, or `modify` without importing a mutable holder, a
  database client, a lock, or a framework context.
- **Consistency.** Favoured inside one run. Bind feeds the final state of one
  step to the next step. The Haskell `transformers` source states that bind
  uses the final state of the first computation as the initial state of the
  second
  (https://hackage.haskell.org/package/transformers-0.4.1.0/docs/src/Control-Monad-Trans-State-Strict.html,
  verified 2026-08-02).
- **Latency.** Mixed. The pure State form adds function calls and pair
  allocation in languages without optimizer support. It can remove lock and
  alias costs caused by shared mutation. In tight loops, an explicit local
  mutable variable may be cheaper.
- **Memory cost.** Mixed. A compact immutable state value is cheap. A large
  state copied on every update is costly unless it uses structural sharing or
  a local mutable representation hidden behind the runner.
- **Operability.** Sacrificed unless the runner records initial state, final
  state, step counts, and failures. The state transitions are values inside the
  computation, not automatic logs.
- **Cost of change.** Favoured when adding one more stateful step to an
  existing chain. Sacrificed when the state type changes, because every reader
  and writer of that state may need an edit.
- **Team topology.** Favoured when a library team defines a small state
  capability and feature teams author steps against it. Sacrificed if one team
  turns the shared state record into a cross-team dumping ground.
- **Cognitive load.** Mixed. Readers fluent in `map`, `flatMap`, `get`, and
  `modify` see a direct sequence. Readers new to the pattern may miss where the
  state value enters and exits because no state parameter appears on each line.
- **Concurrency.** Favoured for isolated runs because no state is shared by
  default. Sacrificed if developers assume State Monad coordinates concurrent
  access. It does not.
- **Failure semantics.** Mixed. With `StateT` plus an error effect, transformer
  ordering decides whether state changes survive failure. GHC's mtl
  documentation discusses state and error as non-commuting effects, where one
  ordering can preserve state after an error while another can lose both state
  and result
  (https://downloads.haskell.org/ghc/latest/docs/libraries/mtl-2.3.1-77f5/src/Control.Monad.Accum.html,
  verified 2026-08-02).

State Monad favours local reasoning, deterministic tests, and linear state
flow. It sacrifices directness, some performance transparency, and live
operational visibility unless the surrounding code addresses those costs.

## 4. Applicability and non-applicability

Reach for State Monad when these conditions hold.

- A sequence of pure or locally controlled steps must thread one logical state.
- Later steps depend on values produced by earlier steps and on the updated
  state.
- The caller should choose the initial state and inspect the result or final
  state at the boundary.
- The state is bounded enough to carry through one run.
- The state has a clear domain meaning, such as parser cursor, symbol supply,
  seed, stack, cache, worklist, or finite machine state.
- You need deterministic tests that can run the same computation with several
  starting states.
- You need to compose many small stateful operations without exposing a mutable
  object to every helper.
- You are already in a library ecosystem with State support, such as Haskell
  `transformers`, Cats, Cats MTL, or fp-ts
  (https://hackage.haskell.org/package/transformers-0.4.1.0/docs/src/Control-Monad-Trans-State-Strict.html,
  verified 2026-08-02;
  https://typelevel.org/cats/datatypes/state.html, verified 2026-08-02;
  https://typelevel.org/cats-mtl/mtl-classes/stateful.html, verified
  2026-08-02;
  https://gcanti.github.io/fp-ts/modules/State.ts.html, verified 2026-08-02).

Do NOT reach for State Monad in these cases.

- **The state must be shared across threads or requests.** Use a database,
  transactional memory, an actor, a lock-protected object, or a service store.
  State Monad describes one local run.
- **Updates must be durable during the run.** Use a transaction, append-only
  log, message queue, or outbox. A final state returned from a pure computation
  is not a durable write.
- **The state is a mixed application context.** Split it. A record containing
  user, clock, logger, config, cache, metrics, and request body is a hidden
  service locator.
- **The operation is read-only.** Use Reader Monad or a plain parameter.
  `get` without `put` is often Reader in disguise.
- **The operation only accumulates output and never reads it.** Use Writer Monad
  or a fold. Haskell `transformers` explicitly points readers from State to
  Reader for read-only state and to Writer for accumulation without later reads
  (https://hackage.haskell.org/package/transformers-0.4.1.0/docs/src/Control-Monad-Trans-State-Strict.html,
  verified 2026-08-02).
- **The state changes independently in parallel branches.** Use explicit merge
  logic, CRDTs, STM, actors, or a dataflow model. State Monad's default story is
  linear.
- **The state is very large and updates copy most of it.** Use persistent data
  structures, an indexed store, or a local mutable builder that returns an
  immutable result.
- **The team cannot agree on failure semantics.** Pick an explicit return type
  first. With StateT and errors, effect ordering changes what survives failure.
- **The language already has a shorter local loop.** A ten-line Go loop with a
  local variable may be clearer than a hand-rolled State type.
- **The state contains secrets or regulated personal data.** Avoid carrying it
  through many closures unless retention, redaction, and crash reporting are
  controlled.
- **The goal is user interface state.** React, SwiftUI, Elm-style update
  functions, actors, or framework stores may be the right surface. State Monad
  can model an update, but it is rarely the full UI state architecture.
- **The code needs breakpoints on every write.** Mutable local code can be
  easier to step through in a debugger than chained functions returning pairs.

Non-applicability list summary. Avoid State Monad when the state must be
shared, durable, live, huge, unrelated, secret, parallel by default, read-only,
or simpler as a local variable.

## 5. Structure

The participants are named by the role they play.

- **State value.** The `S` carried through the computation. It should have a
  narrow domain role. Examples are `ParserState`, `Seed`, `Supply`, `VmStack`,
  or `ReservationBook`.
- **State computation.** A value representing a function from current state to a
  result plus next state. In fp-ts this is literally the interface
  `State<S, A>`, a function from `S` to `[A, S]`
  (https://gcanti.github.io/fp-ts/modules/State.ts.html, verified
  2026-08-02). In Cats, `State[S, A]` is described as `S => (S, A)`
  (https://typelevel.org/cats/datatypes/state.html, verified 2026-08-02).
- **Runner.** The boundary operation that supplies the initial state. Haskell
  names include `runState`, `evalState`, and `execState`; fp-ts names include
  `evaluate` and `execute`
  (https://hackage.haskell.org/package/transformers-0.4.1.0/docs/src/Control-Monad-Trans-State-Strict.html,
  verified 2026-08-02;
  https://gcanti.github.io/fp-ts/modules/State.ts.html, verified 2026-08-02).
- **Primitive operations.** `get` reads the current state, `put` replaces it,
  `modify` derives a new state from the current one, and `gets` reads a
  projection. The Haskell `transformers` module exports these operations
  (https://hackage.haskell.org/package/transformers-0.4.1.0/docs/src/Control-Monad-Trans-State-Strict.html,
  verified 2026-08-02).
- **Bind operation.** The sequencing rule that passes the updated state forward
  while letting the previous result choose the next computation.
- **State transformer.** The optional `StateT` layer that combines local state
  with another effect, such as errors, async, IO, or logging. Cats describes
  `StateT[F[_], S, A]` as adding state manipulation to an existing computation
  in `F`
  (https://typelevel.org/cats/datatypes/statet.html, verified 2026-08-02).

Relationships. The runner calls the state computation with an initial state.
Each primitive returns another state computation. Bind composes computations,
unpacks the pair produced by the left computation, and feeds the next state to
the right computation. The client never mutates the state directly unless the
state value itself contains mutable references, which is a separate design
choice and should be visible in the state type name.

## 6. ASCII structure diagram

```text
  +------------------+        run(initial)        +------------------+
  |      Runner      | -------------------------> | State computation|
  |------------------|                            |------------------|
  | runState         |                            | S -> (A, S)      |
  | evalState        |                            +---------+--------+
  | execState        |                                      |
  +------------------+                                      |
                                                            |
                                                            v
                         +----------------------+   +-------+--------+
                         | Primitive operations |   | Bind / flatMap |
                         |----------------------|   |----------------|
                         | get  : S -> (S, S)   |   | left then next |
                         | put  : S -> ((), S)  |   | passes next S  |
                         | mod  : S -> ((), S)  |   +-------+--------+
                         | gets : S -> (A, S)   |           |
                         +----------------------+           |
                                                            v
  +------------------+       supplied and returned  +-------+--------+
  |   State value S  | <--------------------------> | Domain result A|
  |------------------|                              |----------------|
  | parser cursor    |                              | parsed token   |
  | random seed      |                              | generated id   |
  | symbol supply    |                              | compiled term  |
  | cache snapshot   |                              | service result |
  +------------------+                              +----------------+
```

## 7. Dynamics

A State chain is a series of pure state transitions viewed as one computation.
The important runtime fact is that the state value produced by step one is the
state value consumed by step two. The caller sees that chain only when it runs
the computation.

```text
Client        Runner        stepA: State<S,A>     stepB: A -> State<S,B>
  |             |                    |                       |
  | run prog s0 |                    |                       |
  |-----------> |                    |                       |
  |             | run stepA s0       |                       |
  |             |------------------->|                       |
  |             |<-------------------| returns (a, s1)       |
  |             |                    |                       |
  |             | choose stepB(a)                            |
  |             |------------------------------------------->|
  |             |                    |        returns State<S,B>
  |             | run that state computation with s1         |
  |             |------------------------------------------->|
  |             |<-------------------------------------------|
  |             |                    |        returns (b, s2) |
  |<------------| returns (b, s2)    |                       |
  |             |                    |                       |

  Invariant: each step receives the exact state produced by the prior step.
```

When `get` appears, it returns the current state as the value and leaves the
state unchanged. When `put(newState)` appears, it returns unit and replaces the
state. When `modify(f)` appears, it computes `f(currentState)` and stores that
result. When `gets(f)` appears, it returns `f(currentState)` while leaving state
unchanged. The chain can be interpreted as a domain-specific script, but its
meaning is still a plain function from initial state to result and final state.

StateT changes the dynamics by placing another effect around the pair. The
shape becomes `S -> F<(S, A)>` in Cats terminology
(https://typelevel.org/cats/datatypes/statet.html, verified 2026-08-02). That
means the second step may not run if the surrounding effect fails, cancels, or
suspends. The effect order must be chosen deliberately when failure and state
must interact.

## 8. Implementation variants

**Pure State type.** The type is a wrapper around `S -> (A, S)` or the language's
equivalent tuple. This is the teaching form, and in TypeScript or Python it can
be the actual production form for small interpreters, parsers, and test data
generators. Its cost is visible allocation and a style that some teams find
foreign.

**StateT transformer.** The type is `S -> F<(S, A)>` or `S -> F<(A, S)>`,
depending on library convention. It combines local state with another effect.
Cats documents StateT as the generalization of State to an effect `F`, and says
State is a StateT with `Eval` as the effect
(https://typelevel.org/cats/datatypes/statet.html, verified 2026-08-02). The
trade-off is ordering. State outside error differs from error outside state.
Tests must pin the chosen semantics.

**Capability interface.** Code asks for `MonadState` or `Stateful` instead of a
concrete State type. This keeps business logic independent of the final stack.
Cats MTL defines `Stateful[F, S]` through `get` and `set` and provides instances
for stacks where StateT appears
(https://typelevel.org/cats-mtl/mtl-classes/stateful.html, verified
2026-08-02). The trade-off is type class machinery and harder onboarding.

**Manual state-passing functions.** Each function explicitly accepts state and
returns state. This is not a different meaning, but a different spelling. It is
often best in Go, Java, and Python when there are only two or three steps. It is
also the migration path before introducing a State abstraction.

**Indexed State.** The start state and end state types can differ. Cats exposes
`IndexedStateT` under the State documentation and shows a door example where
valid open and close sequences are checked by types
(https://typelevel.org/cats/datatypes/state.html, verified 2026-08-02). This
variant is valuable for protocols, parsers, and finite machines where the
transition changes the type-level state. Its cost is more type complexity.

**Lens-backed state updates.** In Haskell and Scala ecosystems, lenses can focus
updates on a field inside a larger state. This reduces record rewrite noise.
The danger is that a large record plus lenses can hide that unrelated concerns
have been packed into one state value.

**Local mutable builder behind a pure runner.** The public API remains
`initial -> (result, final)`, while the implementation uses mutable arrays,
maps, or builders internally. This is common in performance-sensitive code. It
keeps external reasoning clean, but the internal code needs its own tests for
aliasing and rollback.

**Effect system encoding.** Modern functional effect systems may encode state
as an algebra or capability rather than as `StateT`. This can improve
interpreter flexibility, but it moves the pattern from a small datatype into a
larger effect runtime.

## 9. Known production uses

- **GHC library internals.** GHC publishes `GHC.Utils.Monad.State.Strict`, a
  strict State monad module in the GHC library documentation. The page names
  `State`, `runState`, `evalState`, `execState`, `get`, `put`, and `modify`,
  and describes the module as a state monad strict in its state
  (https://ghc.gitlab.haskell.org/ghc/doc/libraries/ghc-9.15-inplace/GHC-Utils-Monad-State-Strict.html,
  verified 2026-08-02). GHC also publishes a register allocator state module
  that imports this strict State module
  (https://ghc.gitlab.haskell.org/ghc/doc/libraries/ghc-9.15-inplace/src/GHC.CmmToAsm.Reg.Linear.State.html,
  verified 2026-08-02). This is a named compiler codebase exposing and using
  its own State implementation.
- **Typelevel Cats.** Cats ships `cats.data.State` and `cats.data.StateT`.
  Its State page describes `State[S, A]` as a functional approach to
  application state and provides examples using random generation and typed
  door states. Its StateT page describes the transformer form and effectful
  examples
  (https://typelevel.org/cats/datatypes/state.html, verified 2026-08-02;
  https://typelevel.org/cats/datatypes/statet.html, verified 2026-08-02).
- **fp-ts.** fp-ts ships a `State.ts` module added in version 2.0.0. The module
  documents the `State<S, A>` interface as a function from `S` to `[A, S]` and
  exposes `Functor`, `Applicative`, `Chain`, `Monad`, `flatMap`, `evaluate`,
  and `execute`
  (https://gcanti.github.io/fp-ts/modules/State.ts.html, verified
  2026-08-02).
- **Haskell transformers.** The `transformers` package ships
  `Control.Monad.Trans.State.Strict` with `State`, `StateT`, run helpers, and
  state operations. It also documents when Reader or Writer may be a smaller
  fit than State
  (https://hackage.haskell.org/package/transformers-0.4.1.0/docs/src/Control-Monad-Trans-State-Strict.html,
  verified 2026-08-02).
- **Cats MTL.** Cats MTL ships the `Stateful` type class for state capability.
  Its documentation shows cache read, write, invalidation, and running through
  `State[Cache, *]`
  (https://typelevel.org/cats-mtl/mtl-classes/stateful.html, verified
  2026-08-02).

Engineering judgement. The named uses above are library and compiler uses, not
claims about a private company's application code. They are still production
uses for this catalog because they are released software surfaces that users
compile against.

## 10. Consequences

Positive consequences.

- The state transition becomes an explicit value-level contract at the runner
  boundary.
- Domain steps can be small and composable without manual state plumbing.
- Tests can supply initial state and assert result plus final state.
- Refactors inside a chain are safer than with shared mutation because state
  flow is linear.
- A pure State computation can be replayed with the same initial state.
- The state type documents what the computation is allowed to change.
- The same operations can run under a transformer stack when error, IO, or async
  effects are needed.
- A capability interface can decouple domain code from a concrete monad stack.

Negative consequences.

- Readers must understand bind, `get`, `put`, and the runner convention.
- Debugging can be harder in languages whose debuggers are built around
  imperative local variables.
- The state record can grow into an implicit context if code review does not
  resist unrelated fields.
- Large immutable state updates can allocate heavily.
- StateT with failure effects has ordering semantics that are easy to choose
  accidentally.
- Production telemetry is absent unless the runner records state summaries and
  step outcomes.
- The pattern can hide a simple loop behind abstraction.
- In languages without higher-kinded types, reusable State interfaces require
  more boilerplate or less type safety.

Engineering judgement. The strongest payoff is not "purity" as a slogan. The
payoff is being able to test, replay, and compose a stateful algorithm without
giving every helper a mutable object.

## 11. Failure modes and misuse

This section is engineering judgement.

- **Symptom.** A small change to one feature forces edits across many unrelated
  stateful functions. **Cause.** The state type has become a mixed application
  context. **Fix.** Split the state by workflow, then pass read-only data
  through Reader or parameters and write-only data through Writer or events.
- **Symptom.** Memory rises linearly with input size during a parser or
  compiler pass. **Cause.** Each update copies a large state value or retains
  old states through closures. **Fix.** Use structural sharing, narrower state,
  strict updates where the language needs them, or a local mutable builder
  hidden behind a pure runner.
- **Symptom.** A failed operation sometimes keeps state changes and sometimes
  discards them. **Cause.** StateT and error effects are stacked differently in
  different modules. **Fix.** Define one stack order for the boundary, add tests
  for failure survival, and name the policy in the type alias.
- **Symptom.** Logs show final success but operators cannot tell which state
  path the request followed. **Cause.** State transitions stayed inside the pure
  chain with no summary emitted. **Fix.** Add runner-level trace attributes,
  transition counts, and redacted before or after summaries.
- **Symptom.** Unit tests assert a final state with many incidental fields.
  **Cause.** Tests know too much about a large state record. **Fix.** Assert the
  result and the fields the behavior owns, or expose domain queries over final
  state.
- **Symptom.** Two branches both update state and the later one overwrites the
  earlier one. **Cause.** The code treated a linear State computation as if it
  supported concurrent merges. **Fix.** Use explicit merge functions or a
  concurrency abstraction built for that problem.
- **Symptom.** A function that only reads state is difficult to reuse outside
  the State stack. **Cause.** Reader-style dependencies were placed inside
  State. **Fix.** Move read-only data to Reader or a parameter.
- **Symptom.** A developer adds `get` at the top of every function and passes
  slices by hand afterward. **Cause.** The state record is too broad or helper
  APIs are not shaped around domain operations. **Fix.** Add focused helper
  operations such as `freshName`, `advanceCursor`, or `rememberReservation`.
- **Symptom.** A small imperative loop becomes a page of generic State helpers.
  **Cause.** The pattern was applied for style, not for composition. **Fix.**
  Inline the loop or keep manual state passing until repeated composition earns
  the abstraction.
- **Symptom.** Sensitive request data appears in crash dumps or debug prints of
  closures. **Cause.** The state value carried raw secrets through a long chain.
  **Fix.** Store opaque ids, redacted summaries, or short-lived handles, and
  keep secret material in the approved secret-handling path.

## 12. Trade-off matrix

| Force | State Monad | Reader Monad | Writer Monad | Explicit state parameter | Local mutable variable | Actor state |
|---|---|---|---|---|---|---|
| Coupling | Low coupling to transport, medium coupling to state type | Low for read-only context | Low for append-only output | Every signature names state | Low outside one function | Coupled to actor protocol |
| Consistency | Linear next-state flow | No updates | Append order only | Depends on discipline | Depends on scope | Serialized by mailbox |
| Latency | Function and pair overhead unless optimized | Low overhead | Append overhead | Low overhead | Lowest in tight loops | Mailbox and scheduling cost |
| Memory | Good with small state, risky with large copies | Small | Risky for large logs | Visible to caller | Usually small | Held across messages |
| Operability | Needs runner instrumentation | Context can be logged at boundary | Output visible if emitted | Easy to inspect in debugger | Easy inside one frame | Observable through actor metrics |
| Team topology | Good with narrow capabilities | Good for shared config | Good for diagnostics teams | Poor across many APIs | Good for owned functions | Good for service ownership |
| Cognitive load | Medium to high for new readers | Low to medium | Medium | Low concept, high noise | Low | Medium |
| Failure semantics | Must choose StateT ordering | Usually unaffected | Output survival depends on stack | Explicit in return type | Manual cleanup | Supervision policy |
| Concurrency | Isolated by default, no sharing | Safe for shared reads | Safe if output is local | Caller decides | Unsafe if escaped | Designed for concurrent callers |
| Best fit | Local evolving state in a composable chain | Immutable environment | Accumulated output | Short pipelines | Tight local algorithm | Long-lived shared state |

## 13. Related and incompatible patterns

- **Monad.** State is a concrete monad whose bind operation threads state. The
  general Monad entry covers laws and dependent sequencing.
- **Reader Monad.** Reader is the read-only cousin. Use Reader when the context
  is supplied once and never replaced.
- **Writer Monad.** Writer accumulates output. Use Writer when later steps do
  not need to inspect the accumulated value. Use State when later steps must
  read and update it.
- **Result or Either.** State often composes with failure. The order of StateT
  and Either controls whether state changes survive failure.
- **Lens.** Lenses can make focused state updates readable. They can also make
  an oversized state record feel acceptable, so review the record shape first.
- **Traversable.** Traversing a collection with State is a common way to label
  nodes, allocate ids, or thread a cursor through each element.
- **Free Monad and tagless final.** These patterns can describe state
  operations as an algebra and interpret them later. State Monad is smaller when
  the only effect is local state.
- **Persistent data structures.** Persistent maps, vectors, and trees reduce
  copy cost when State carries immutable structures.
- **Shared mutable state.** This conflicts with State Monad's local-run model.
  If many actors can mutate the same value at the same time, use concurrency
  tools.
- **Hidden global state.** This actively conflicts with the pattern. State
  Monad moves state to an explicit boundary; hidden globals move it away from
  the boundary.
- **Actor model.** Actor state replaces State Monad when the state must live
  across messages and be shared safely with concurrent callers.
- **Unit of Work.** Unit of Work owns durable changes to external resources.
  State Monad can prepare changes, but it is not a commit protocol.

## 14. Refactoring path in and out

To introduce State Monad into code that passes state by hand:

1. Pick one workflow with a single logical state. Do not start with a whole
   application context.
2. Name the state type after the domain role, such as `ParserState` or
   `NameSupply`.
3. Convert the smallest helper from `S -> (A, S)` into a State computation.
4. Add `pure`, `map`, and `flatMap` or use the library's existing type.
5. Convert read helpers to `get` or `gets`.
6. Convert write helpers to `put` or `modify`.
7. Replace manual unpack and repack sites with bind or language syntax.
8. Keep the runner at the old boundary so callers still pass an initial state
   and receive the result they expect.
9. Add tests for result and final state after each migration step.
10. Only after the pure shape is stable, introduce StateT if another effect is
    actually needed.

Named refactorings that often apply are Extract Function, Introduce Parameter
Object, Replace Temp with Query, and Split Phase. The pattern-specific step is
turning the parameter object into the state carried by the computation.

To remove State Monad when it no longer earns its place:

1. Find the runner and list every operation used inside the chain.
2. If operations only read, replace the state with Reader or explicit
   parameters.
3. If operations only append output, replace the state with Writer or a fold.
4. If there are fewer than four stateful steps, inline the state parameter and
   compare readability.
5. If the state must be shared, move it behind an actor, repository,
   transaction, or service boundary.
6. Replace `get` and `modify` helpers with named domain functions before
   deleting the State type, so behavior remains easy to test.
7. Keep golden tests around result and final state while changing the shape.
8. Delete the abstraction after the tests pass with the simpler form.

Engineering judgement. Refactoring in is safest from explicit state passing,
not from hidden mutation. Refactoring out is safest toward explicit state
passing, not toward global state.

## 15. Testing and verification

This section is engineering judgement unless a cited source names a concrete
API.

Test a State Monad implementation at three levels.

First, test primitive laws. `pure(a).flatMap(f)` should behave like `f(a)`.
`m.flatMap(pure)` should behave like `m`. Regrouping nested binds should not
change the final result or final state. The general monad law source belongs in
the Monad entry; here the special check is that final state equality is included
in every law assertion.

Second, test domain transitions. A parser cursor should advance by the parsed
width. A symbol supply should allocate unique names. A cache should record a
miss after the service call and hit on the second lookup. These tests should run
the computation with a known initial state and assert both result and final
state.

Third, test boundaries. `runState` style helpers should return result and final
state. `evalState` style helpers should discard final state only in APIs where
that loss is intended. `execState` style helpers should discard result only for
commands whose result is unit or uninteresting. The Haskell `transformers`
module documents the distinction among these runner helpers
(https://hackage.haskell.org/package/transformers-0.4.1.0/docs/src/Control-Monad-Trans-State-Strict.html,
verified 2026-08-02).

Useful test doubles and techniques:

- **Initial-state fixtures.** Small named states that describe the scenario.
- **Final-state assertions.** Assertions over domain fields rather than whole
  incidental records.
- **Transition table tests.** For finite machines, table each start state,
  command, expected result, and end state.
- **Property tests.** Generate operation sequences and assert invariants such as
  monotonic counters, no duplicate ids, cursor never moves backward, or cache
  size remains under a limit.
- **Golden traces.** If the runner emits transition summaries, compare a stable
  redacted trace for a representative flow.
- **Failure-order tests.** For StateT plus errors, assert whether state changes
  survive failure. Do not leave that as an inference from type aliases.

What becomes easier. Pure State code has no mock database, no global reset, and
no race-prone shared fixture. The same computation can be replayed with many
initial states.

What becomes harder. Single-step debugging and line coverage can be less
obvious. In languages without monad syntax, lambdas can obscure domain names.
StateT stacks may need helper constructors to keep tests readable.

## 16. Observability signals

This section is engineering judgement.

State Monad is invisible to production tooling unless the runner emits signals.
Instrument the boundary, not every helper by default.

Log or trace these fields where they are safe:

- computation name
- initial state version or redacted summary
- final state version or redacted summary
- number of state transitions
- number of reads and writes if the implementation can count them cheaply
- failed transition name
- failure policy, such as state kept or state discarded
- state size or item count for caches and worklists
- elapsed time for the whole run

A healthy dashboard shows stable transition counts for the same workload,
bounded state size, low failure rate, and predictable run time. A failing
dashboard shows growing state size, repeated rollback, transition counts far
above input size, or a spike in failures after one transition name.

Recommended trace shape:

```text
state.run name=parseHeader status=ok transitions=7
  initial=cursor:0,len:128
  final=cursor:42,len:128
  elapsed_ms=3

state.run name=allocateSymbols status=error transitions=19
  initial=supply:120
  final_policy=discarded
  failed_step=freshName
  error=duplicate-prefix
```

Avoid logging full state by default. State often contains input fragments,
tokens, user ids, cache values, or intermediate compiler terms. Prefer counts,
versions, hashes where approved, or domain summaries. If a debug build records
full transitions, place it behind an explicit flag with retention limits.

For local development, expose a runner that returns a trace value next to the
result. That keeps tests deterministic and avoids coupling the pure chain to
the production logger.

## 17. Security and privacy implications

This section is engineering judgement.

State Monad narrows some risks and opens others. It narrows risks from hidden
global mutation because state enters at the runner boundary and leaves as a
value. It also narrows cross-request leakage when each request gets a fresh
initial state. A pure State computation cannot be read by another thread unless
the state value itself contains shared references.

The main risk is retention. State is carried through closures and returned at
the end. If it contains tokens, passwords, session cookies, personal data,
source text, or payment fragments, those values may live longer than expected
and may appear in debug output, crash dumps, trace attributes, or failed test
snapshots. The fix is not a special monad trick. Keep sensitive material out of
the state when possible. Store opaque handles or redacted summaries. Clear
short-lived data before returning final state. Review derived `show`, `debug`,
`repr`, and JSON encoders for the state type.

Another risk is authorization drift. If authorization context is placed inside
mutable state and later steps can replace it, a bug can run a step under the
wrong user or tenant. Treat identity and authorization facts as read-only
Reader data unless a state transition is part of the security model and is
tested as such.

StateT with errors also has a security angle. If a failed operation returns a
state that contains partially prepared changes, the caller might accidentally
use that state after failure. If a failed operation discards state that contains
audit evidence, the system might lose information. Pick the failure policy at
the boundary and test it.

State Monad is silent about durability, access control, encryption, and
concurrent isolation. Those properties come from the surrounding storage,
runtime, and protocol design.

## Code examples

The examples use TypeScript, Python, and Go because the repository toolchain can
run them directly with `node`, `python3`, and `go`. They implement the same
small pattern: a stateful name supply that allocates fresh ids while returning
domain values.

```typescript
type State<S, A> = (state: S) => [A, S];

const pure = <S, A>(value: A): State<S, A> => state => [value, state];

const flatMap =
  <S, A, B>(step: State<S, A>, next: (value: A) => State<S, B>): State<S, B> =>
  state => {
    const [value, state1] = step(state);
    return next(value)(state1);
  };

const get = <S>(): State<S, S> => state => [state, state];

const put = <S>(nextState: S): State<S, void> => _state => [undefined, nextState];

type Supply = { nextId: number; prefix: string };

const freshName: State<Supply, string> = flatMap(get<Supply>(), supply =>
  flatMap(put<Supply>({ ...supply, nextId: supply.nextId + 1 }), () =>
    pure(`${supply.prefix}${supply.nextId}`),
  ),
);

const pair: State<Supply, [string, string]> = flatMap(freshName, first =>
  flatMap(freshName, second => pure([first, second])),
);

const [names, finalSupply] = pair({ nextId: 7, prefix: "tmp" });
console.log(names.join(","));
console.log(`${finalSupply.prefix}:${finalSupply.nextId}`);
```

```python
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable, Generic, TypeVar

S = TypeVar("S")
A = TypeVar("A")
B = TypeVar("B")


class State(Generic[S, A]):
    def __init__(self, run: Callable[[S], tuple[A, S]]) -> None:
        self.run = run

    @staticmethod
    def pure(value: A) -> "State[S, A]":
        return State(lambda state: (value, state))

    def flat_map(self, next_step: Callable[[A], "State[S, B]"]) -> "State[S, B]":
        def run(state: S) -> tuple[B, S]:
            value, state1 = self.run(state)
            return next_step(value).run(state1)

        return State(run)


def get() -> State[S, S]:
    return State(lambda state: (state, state))


def put(next_state: S) -> State[S, None]:
    return State(lambda _state: (None, next_state))


@dataclass(frozen=True)
class Supply:
    next_id: int
    prefix: str


def fresh_name() -> State[Supply, str]:
    return get().flat_map(
        lambda supply: put(replace(supply, next_id=supply.next_id + 1)).flat_map(
            lambda _none: State.pure(f"{supply.prefix}{supply.next_id}")
        )
    )


program = fresh_name().flat_map(
    lambda first: fresh_name().flat_map(lambda second: State.pure((first, second)))
)

names, final_supply = program.run(Supply(next_id=3, prefix="sym"))
print(",".join(names))
print(f"{final_supply.prefix}:{final_supply.next_id}")
```

```go
package main

import "fmt"

type Pair[A any, S any] struct {
	Value A
	State S
}

type State[S any, A any] func(S) Pair[A, S]

func Pure[S any, A any](value A) State[S, A] {
	return func(state S) Pair[A, S] {
		return Pair[A, S]{Value: value, State: state}
	}
}

func FlatMap[S any, A any, B any](
	step State[S, A],
	next func(A) State[S, B],
) State[S, B] {
	return func(state S) Pair[B, S] {
		first := step(state)
		return next(first.Value)(first.State)
	}
}

func Get[S any]() State[S, S] {
	return func(state S) Pair[S, S] {
		return Pair[S, S]{Value: state, State: state}
	}
}

func Put[S any](nextState S) State[S, struct{}] {
	return func(_ S) Pair[struct{}, S] {
		return Pair[struct{}, S]{Value: struct{}{}, State: nextState}
	}
}

type Supply struct {
	NextID int
	Prefix string
}

func FreshName() State[Supply, string] {
	return FlatMap(Get[Supply](), func(supply Supply) State[Supply, string] {
		updated := Supply{NextID: supply.NextID + 1, Prefix: supply.Prefix}
		return FlatMap(Put(updated), func(_ struct{}) State[Supply, string] {
			return Pure[Supply](fmt.Sprintf("%s%d", supply.Prefix, supply.NextID))
		})
	})
}

func main() {
	program := FlatMap(FreshName(), func(first string) State[Supply, string] {
		return FlatMap(FreshName(), func(second string) State[Supply, string] {
			return Pure[Supply](first + "," + second)
		})
	})

	result := program(Supply{NextID: 10, Prefix: "n"})
	fmt.Println(result.Value)
	fmt.Printf("%s:%d\n", result.State.Prefix, result.State.NextID)
}
```

## 18. References

- Philip Wadler, "Monads for functional programming", in Johan Jeuring and Erik
  Meijer, editors, *Advanced Functional Programming*, Springer Lecture Notes in
  Computer Science 925, 1995, sections 1 through 2.5. Earlier version in the
  1992 Marktoberdorf summer school proceedings. URL:
  https://homepages.inf.ed.ac.uk/wadler/papers/marktoberdorf/baastad.pdf,
  verified 2026-08-02.
- Haskell `transformers`, `Control.Monad.Trans.State.Strict` source
  documentation, version 0.4.1.0. URL:
  https://hackage.haskell.org/package/transformers-0.4.1.0/docs/src/Control-Monad-Trans-State-Strict.html,
  verified 2026-08-02.
- GHC libraries, `GHC.Utils.Monad.State.Strict`, GHC 9.15 in-place
  documentation. URL:
  https://ghc.gitlab.haskell.org/ghc/doc/libraries/ghc-9.15-inplace/GHC-Utils-Monad-State-Strict.html,
  verified 2026-08-02.
- GHC libraries, `GHC.CmmToAsm.Reg.Linear.State` source documentation. URL:
  https://ghc.gitlab.haskell.org/ghc/doc/libraries/ghc-9.15-inplace/src/GHC.CmmToAsm.Reg.Linear.State.html,
  verified 2026-08-02.
- Typelevel Cats, `State` data type documentation. URL:
  https://typelevel.org/cats/datatypes/state.html, verified 2026-08-02.
- Typelevel Cats, `StateT` data type documentation. URL:
  https://typelevel.org/cats/datatypes/statet.html, verified 2026-08-02.
- Typelevel Cats MTL, `Stateful` type class documentation. URL:
  https://typelevel.org/cats-mtl/mtl-classes/stateful.html, verified
  2026-08-02.
- fp-ts, `State.ts` module documentation. URL:
  https://gcanti.github.io/fp-ts/modules/State.ts.html, verified 2026-08-02.
- GHC `mtl`, `Control.Monad.Accum` source documentation discussing
  non-commuting state and error effects. URL:
  https://downloads.haskell.org/ghc/latest/docs/libraries/mtl-2.3.1-77f5/src/Control.Monad.Accum.html,
  verified 2026-08-02.
