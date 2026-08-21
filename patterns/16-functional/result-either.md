---
name: Result Either
slug: result-either
family: 16-functional
category: Functional
aliases: [Either, Result, Typed Result, Two-case Result, Left Right]
first_described: "standard functional sum-type idiom"
maturity: established
related: [railway-oriented-programming, monad, applicative, validation, option]
incompatible_with: [exception-only-flow, unchecked-null-flow, panic-flow]
verified: 2026-08-02
---

# Result Either

## 1. Name, aliases, and lineage

The canonical name in this catalog is Result Either. The name joins two common
spellings of the same pattern shape. Haskell and Scala use `Either`, with
`Left` and `Right` as the two cases. Rust, Swift, FSharp.Core, and many domain
libraries use `Result`, with success and failure named as `Ok` and `Err`,
`success` and `failure`, or `Ok` and `Error`. Haskell `base` documents
`Either a b` as a type with `Left a` and `Right b`, and states the convention
that `Left` carries the error while `Right` carries the correct value
(https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Data-Either.html,
verified 2026-08-02). Rust documents `Result<T, E>` as an enum with `Ok(T)`
and `Err(E)` where the type represents success or failure
(https://doc.rust-lang.org/std/result/enum.Result.html, verified 2026-08-02).
Swift documents `Result<Success, Failure>` as an enum whose cases carry a
success value or a failure value
(https://developer.apple.com/documentation/Swift/Result, verified 2026-08-02).

The pattern has several aliases in ordinary engineering speech. **Either** is
the older functional name and stays neutral about which side is good. **Result**
is the error-handling name and says the two cases are success and failure.
**Typed result** highlights the core benefit, the error path is part of the
function signature. **Two-track result** is common when this pattern is paired
with Railway-Oriented Programming. **Left Right** is an informal name used when
people discuss the constructors rather than the type.

This entry treats `Either` and `Result` as one software pattern because the
design duty is the same. A function returns one value that is exactly one of two
cases. The success case carries the value needed by later work. The error case
carries the reason that later success work must not run. Combinators such as
`map`, `mapError`, `flatMap`, `bind`, and `and_then` transform those cases
without losing the distinction. Scala 2.13 documents `Either` as right-biased,
so `map` and `flatMap` operate on `Right` and leave `Left` unchanged
(https://www.scala-lang.org/api/2.13.16/scala/util/Either.html, verified
2026-08-02). Rust documents `map` and `map_err` on `Result` as transforming
the success case or the error case while leaving the other case alone
(https://doc.rust-lang.org/std/result/enum.Result.html, verified 2026-08-02).

Engineering judgement. The lineage is better understood as a stable family of
sum-type practice than as a single named pattern invented by one author. The
catalog name therefore describes the reusable design shape, not a claim that
one publication coined both names.

## 2. Problem and context

A program has operations that can fail in expected, meaningful ways. The caller
must distinguish those failures from success, and often must choose a different
business action for each failure. The failure is not a process crash. It is a
known outcome such as invalid input, missing account, rejected payment, empty
search result where emptiness is a domain event, expired token, unsupported
file format, or version conflict.

Without Result Either, teams tend to encode that outcome in weaker forms.
Exceptions hide expected outcomes from ordinary function signatures. Nullable
returns discard the reason for failure. Boolean status values separate success
from the data needed on success. Sentinel values such as empty strings,
negative IDs, or magic numbers make illegal values part of the data model.
Out-parameters split one logical answer across several variables. A caller can
forget to inspect the side channel and proceed as if the operation succeeded.

Result Either puts the two alternatives into a single value. The value is
closed over two cases, so a caller cannot read a success value until it has
dealt with the case distinction. In languages with algebraic data types or
sealed unions, the compiler checks the cases. In languages without those
features, a local discriminated union can still concentrate the convention in a
small API. The type says, at the boundary, that success and expected failure are
both part of the contract.

The context is narrow. This pattern is for recoverable, expected outcomes where
the caller has useful work to do after either case. It is not a replacement for
every exception, not a logging system, not a transaction manager, not a retry
policy, and not an observability plan. A disk corruption error during startup
may need to abort the process. A domain validation failure in a signup request
should usually be returned as a typed error. The difference is whether the
caller can make a normal decision from the error value.

Result Either is most valuable at module boundaries and workflow steps. A
parser can return either a parsed command or a parse error. A repository can
return either an aggregate or a domain-level not-found value. A policy check can
return either proof that the action is allowed or the reason it is refused. A
job step can return either the new checkpoint or a retryable failure. The type
keeps that decision local and testable.

Engineering judgement. The pattern pays best when the error type is designed
with the same care as the success type. A result of `Result<User, String>` is
better than throwing a plain exception in many codebases, but it still makes
callers parse prose if they need behavior. A result of
`Result<User, LoginError>` gives the rest of the program a stable vocabulary.

## 3. Forces

Engineering judgement. This section weighs trade-offs from production design
practice. Named API facts are cited where they describe a specific language or
library.

- **Coupling.** Favoured. The caller depends on a small result contract rather
  than on exception subclasses, global state, or a second mutable output slot.
  The producer and consumer agree on the success type and error type.
- **Consistency.** Favoured for expected failures. The success and failure
  channels travel together, so a caller cannot receive data from one channel
  while forgetting the other channel exists.
- **Latency.** Mixed. A native enum such as Rust `Result` is compiled into
  ordinary control flow, and Rust's `?` operator is designed to propagate
  errors from functions that return compatible result-like types
  (https://doc.rust-lang.org/std/result/, verified 2026-08-02). A boxed or
  object-heavy result in another runtime can allocate more than a thrown
  exception on the success path if exceptions are rare.
- **Operability.** Favoured when error cases are named and counted. Sacrificed
  when teams wrap every error in a generic left value and erase diagnostic
  fields.
- **Cost of change.** Favoured when adding a new caller, because the failure
  contract is explicit. Sacrificed when changing an error algebra, because each
  exhaustive match may need an edit.
- **Team topology.** Favoured across service and library boundaries. A platform
  team can publish a typed result API. Feature teams then map the error cases
  into product behavior rather than reverse-engineering thrown values.
- **Cognitive load.** Mixed. Readers see the failure contract in the type, but
  they must learn the small vocabulary of `map`, `bind`, `flatMap`, `map_err`,
  `fold`, and pattern matching.
- **Composition.** Favoured for fail-fast flows. `bind` or `flatMap` connects a
  function returning a result to the next function returning a result.
  FSharp.Core documents `Result.bind` as passing an `Ok` value to the binder
  and returning an existing `Error` unchanged
  (https://fsharp.github.io/fsharp-core-docs/reference/fsharp-core-resultmodule.html,
  verified 2026-08-02).
- **Error accumulation.** Sacrificed by the monadic form. The usual `bind`
  behavior stops at the first error. Validation that needs many errors at once
  usually wants an applicative validation type, not fail-fast Result Either.

The pattern therefore favours explicit contracts, local reasoning, and
composable expected failure. It sacrifices some brevity, some compatibility
with exception-centric APIs, and the ability to gather independent errors by
default.

## 4. Applicability and non-applicability

Reach for Result Either when the following hold.

- A function has a normal success value and one or more expected failure values.
- The caller can make a meaningful decision from the failure case.
- The success path and failure path should be visible in the type signature.
- Several fallible steps must compose in order, with later steps skipped after
  the first failure.
- The error vocabulary is part of the domain model, public API, or test
  contract.
- You need to convert between exception APIs and typed domain flow at a clear
  boundary.
- You want tests to assert error cases as values rather than catch thrown
  control flow.

Do NOT reach for Result Either in these cases.

- **The error is unrecoverable in the current process.** A corrupt binary,
  failed invariant, or impossible state should not be disguised as a value that
  the caller might ignore. Crash, abort startup, or raise an exception at the
  boundary where that is the runtime contract.
- **The caller cannot act on the failure.** Returning a typed error that every
  caller maps to the same generic failure adds ceremony without buying a
  decision point.
- **You need many independent validation errors in one response.** The ordinary
  monadic result short-circuits. Use Validation, an accumulated error list, or
  an applicative style when every field should be checked.
- **The language ecosystem is exception-first at the boundary.** A Java
  framework method that is required to throw a checked exception should do so
  at the framework boundary. Use Result Either inside the domain layer, then
  translate once.
- **The operation is absence without a reason.** If the only failure is "no
  value" and no caller needs more detail, Option or Optional is smaller.
- **The error value would be an untyped string bag.** A result with arbitrary
  prose errors moves string parsing into callers. Design a small error type, or
  keep the error local.
- **The result would cross an untyped serialization boundary unchanged.** JSON
  clients may not understand `Left` and `Right`. Publish a response schema with
  stable fields, then map to Result Either inside the service.
- **The function has side effects that must always run after failure.** A
  result value does not manage cleanup by itself. Use language resource
  constructs such as `defer`, `finally`, context managers, or bracket-style
  APIs.
- **The codebase lacks pattern matching or union discipline and the type would
  be faked badly.** A pair of nullable fields named `value` and `error` can hold
  both or neither. Use constructors that make invalid states unrepresentable, or
  choose a language-native error mechanism.

Non-applicability list summary. Avoid this pattern where the failure is not
recoverable, where no caller branches on it, where many errors must be gathered,
where interop demands exceptions, or where the implementation cannot prevent
invalid result states.

## 5. Structure

The core participants are small.

- **Result Either type.** The closed two-case carrier. It has one type
  parameter for the success value and one for the error value. In `Either<E, A>`
  notation, `E` is usually the left side and `A` is the right side. In
  `Result<A, E>` notation, `A` is usually success and `E` is error.
- **Success case.** The branch that holds the value later work needs. It is
  called `Right`, `Ok`, or `success` depending on the language or library.
- **Failure case.** The branch that holds the reason the requested operation did
  not produce success. It is called `Left`, `Err`, `Error`, or `failure`.
- **Producer.** A function, method, parser, repository, policy, or workflow
  step that returns a result instead of throwing, returning null, or mutating an
  output parameter.
- **Consumer.** Code that pattern matches, folds, maps, binds, or translates the
  result into an outer protocol such as HTTP, a CLI exit code, a job retry, or a
  user-visible message.
- **Combinators.** Operations that preserve the two-case shape. `map` changes
  success. `mapError` or `map_err` changes failure. `bind`, `flatMap`, `chain`,
  or `and_then` runs the next fallible step only for success. `fold` collapses
  both cases to one common output type.
- **Error algebra.** The set of failure values the producer may return. It can
  be an enum, sealed hierarchy, tagged union, record union, or a small class
  tree. Its design controls how useful the pattern becomes.

The main relationship is a type-level promise. The producer returns exactly one
case. The consumer must account for both cases before it obtains an ordinary
value. Combinators allow the consumer to defer the final match while still
building larger operations.

## 6. ASCII structure diagram

```text
                 +-----------------------------------+
                 |        ResultEither<E, A>         |
                 |-----------------------------------|
                 | one value, exactly one case       |
                 +-----------------+-----------------+
                                   |
                     +-------------+-------------+
                     |                           |
        +------------v------------+   +----------v-----------+
        |       Failure case       |   |     Success case     |
        |--------------------------|   |----------------------|
        | Left(E), Err(E), Error(E)|   | Right(A), Ok(A)      |
        | carries reason           |   | carries value        |
        +------------+-------------+   +----------+-----------+
                     |                            |
                     | mapError                   | map
                     v                            v
        +-------------------------+    +----------------------+
        | ResultEither<F, A>      |    | ResultEither<E, B>   |
        +-------------------------+    +----------------------+
                     \                            /
                      \                          /
                       v                        v
                 +-----------------------------------+
                 | bind: A -> ResultEither<E, B>     |
                 | runs only from the success case    |
                 +-----------------------------------+
```

## 7. Dynamics

At runtime, a producer constructs one of the two cases. A consumer then chooses
one of three common paths. It can match immediately. It can map or bind more
work while keeping the value wrapped. Or it can translate the result at the
boundary into an exception, response, message, retry decision, or exit code.

```text
Client          parse input        validate domain       save change       Boundary
  |                  |                    |                    |              |
  |-- request ------>|                    |                    |              |
  |                  |-- Ok(command) ---->|                    |              |
  |                  |                    |-- Ok(approved) --->|              |
  |                  |                    |                    |-- Err(db) -->|
  |                  |                    |                    |              |
  |                  |                    |       later success steps skipped  |
  |                  |                    |                    |              |
  |<------------------------------- failure response -------------------------|

Alternate flow:

Client          parse input        validate domain       save change       Boundary
  |                  |                    |                    |              |
  |-- request ------>|                    |                    |              |
  |                  |-- Err(parse) ----->|                    |              |
  |                  |  no validate call  |                    |              |
  |                  |  no save call      |                    |              |
  |<------------------------------- validation response ----------------------|
```

The dynamics are strict about sequencing in the monadic form. The next fallible
function is not called when the current value is a failure. That is the feature
that makes a Result Either pipeline readable, and the reason it is wrong for
accumulating all validation errors.

## 8. Implementation variants

**Native enum or algebraic data type.** Rust `Result`, Swift `Result`, Haskell
`Either`, and F# `Result` have native or standard-library forms. This is the
best variant when available because construction and matching are part of the
language or core library. Rust's enum definition exposes the two variants as
`Ok(T)` and `Err(E)` in standard documentation
(https://doc.rust-lang.org/std/result/enum.Result.html, verified 2026-08-02).

**Right-biased Either.** In Haskell, Scala, Arrow, fp-ts, and many functional
libraries, `Right` is the success side by convention. Bias means operations
such as `map` and `flatMap` target the right side by default. Scala 2.13
documents this behavior for `Either`
(https://www.scala-lang.org/api/2.13.16/scala/util/Either.html, verified
2026-08-02). This variant is compact for pipelines, but the name `Right` is
less domain-specific than `Ok` or `success`.

**Result with named success and failure.** Swift and Rust use names that make
the error-handling intent clear. Swift's documentation names the cases
`success(Success)` and `failure(Failure)`
(https://developer.apple.com/documentation/Swift/Result, verified 2026-08-02).
This variant reads well for application code and for teams less familiar with
`Left` and `Right`.

**Library-provided Either in a host language.** Java, Kotlin, and TypeScript
often use library types because the language core does not carry an exact
standard Result Either type for all contexts. Arrow documents Kotlin `Either`
for typed errors and gives examples using `Either.Right`, `Either.Left`,
`flatMap`, and `map`
(https://apidocs.arrow-kt.io/arrow-core/arrow.core/-either/index.html,
verified 2026-08-02). Vavr documents Java `Either<L, R>` as either `Left` or
`Right` and notes the success-by-right convention
(https://javadoc.io/doc/io.vavr/vavr/1.0.1/io/vavr/control/Either.html,
verified 2026-08-02). fp-ts documents TypeScript `Either` as a disjoint union
with right-side mapping
(https://fp-ts.github.io/core/modules/Either.ts.html, verified 2026-08-02).

**Local discriminated union.** TypeScript, Python, and Go codebases often define
a small local result type. This is reasonable when adding a dependency would be
heavier than the type itself. It needs private or disciplined constructors so
callers cannot create an invalid value with both success and error fields.

**Exception bridge.** A boundary function catches exceptions and turns known
ones into typed errors, or calls `get`, `unwrap`, or an equivalent at the edge
to convert a result back into the host mechanism. Apple documents `Result.get()`
as returning the success value as a throwing expression, throwing the failure
value when the instance represents failure
(https://developer.apple.com/documentation/swift/result/get%28%29, verified
2026-08-02). This variant is often the right interop move.

**Async result.** Some APIs return a result through a callback, future, task, or
stream event. Apple documents `Result` for failable asynchronous APIs where an
API cannot throw synchronously
(https://developer.apple.com/documentation/swift/writing-failable-asynchronous-apis,
verified 2026-08-02). In modern async code, prefer one clear layer, such as
`Task<Result<A, E>>` for typed domain errors or `Result<Task<A>, E>` only when
task creation itself can fail before async work starts.

## 9. Known production uses

**Rust standard library, `std::result::Result`.** Rust's standard library
defines `Result<T, E>` with `Ok(T)` and `Err(E)`, and the module documentation
describes it as the type used for returning and propagating errors. The enum and
methods such as `map`, `map_err`, and `and_then` are documented in the standard
library API (https://doc.rust-lang.org/std/result/enum.Result.html, verified
2026-08-02; https://doc.rust-lang.org/std/result/, verified 2026-08-02).

**Swift standard library, `Result<Success, Failure>`.** Swift's standard
library defines `Result` as an enumeration with success and failure cases, and
documents `map`, `mapError`, `flatMap`, `flatMapError`, and `get`. Apple also
documents `Result` in guidance for failable asynchronous APIs
(https://developer.apple.com/documentation/Swift/Result, verified 2026-08-02;
https://developer.apple.com/documentation/swift/writing-failable-asynchronous-apis,
verified 2026-08-02).

**Haskell `base`, `Data.Either`.** The `base` package documents `Either` with
`Left` and `Right`, along with functions such as `either`, `lefts`, `rights`,
`isLeft`, `isRight`, and `partitionEithers`
(https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Data-Either.html,
verified 2026-08-02).

**FSharp.Core, `Result` module.** FSharp.Core documents `Result<'T,'TError>`
with `Ok` and `Error` cases and module functions including `bind`, `map`,
`mapError`, `isOk`, `isError`, and conversion functions
(https://fsharp.github.io/fsharp-core-docs/reference/fsharp-core-resultmodule.html,
verified 2026-08-02).

**Arrow Core, `Either`.** Arrow Core documents Kotlin `Either` as a typed error
wrapper and shows fail-fast composition with `flatMap` and `map`
(https://apidocs.arrow-kt.io/arrow-core/arrow.core/-either/index.html,
verified 2026-08-02). Its typed-errors guide also names wrapper types,
including `Either`, `Option`, and `Result`, as one supported approach
(https://arrow-kt.io/learn/typed-errors/, verified 2026-08-02).

## 10. Consequences

Positive.

- Expected failure becomes part of the function contract.
- Callers can branch on typed error values without string parsing.
- Success and failure remain one logical return value.
- Fallible steps compose with `bind`, `flatMap`, `and_then`, or the host
  language's propagation syntax.
- Tests can assert exact failure values.
- Domain code can avoid throwing for normal business refusal.
- Boundary translation becomes explicit. A controller, worker, or CLI handler
  can convert one typed result into HTTP status, retry, or exit status.

Negative.

- Function signatures get wider because both success and error types are named.
- Callers must handle the result or deliberately discard it.
- Error type changes can touch many matches.
- Fail-fast composition returns the first error, not all errors.
- Exception-based libraries need adapter code.
- In languages without native sum types, teams must maintain a local encoding
  and guard against invalid states.
- Poorly designed error values can become a dumping ground for strings,
  stack traces, and private data.

Engineering judgement. Result Either is a clarity trade. It spends syntax and
type vocabulary to make ordinary failure visible. When the failure vocabulary
is valuable, the cost is easy to defend. When all failures collapse to the same
message, the syntax is often noise.

## 11. Failure modes and misuse

Engineering judgement. The triples below describe common production symptoms,
their usual causes, and the repair that changes the design rather than hiding
the symptom.

**Stringly left values.** Symptom. Callers compare error text such as
`"not found"` or `"timeout"` to choose behavior, and localization or copy edits
break tests. Cause. The error side was typed as `String` even though callers
needed structured decisions. Fix. Replace the string with an enum or tagged
record and keep prose generation at the boundary.

**Nested result stacks.** Symptom. Signatures contain shapes like
`Result<Result<A, E1>, E2>`, and callers unwrap twice. Cause. Code used `map`
where it needed `bind` or mixed two failure layers without a boundary decision.
Fix. Use `bind`, flatten the result, or translate the inner error into the
outer error algebra.

**Ignored failure values.** Symptom. Logs show an error result was returned, but
the user sees a success response or a default value. Cause. A caller converted
the result to an option, boolean, or default too early. Fix. Match on the error
case at the boundary and make discard operations rare, named, and reviewed.

**Exception tunnel inside result code.** Symptom. A function returning
`Result<A, E>` still throws for common domain cases, so callers need both match
logic and catch logic. Cause. The implementation wrapped only some failures and
allowed others to escape. Fix. Define which failures belong in `E`, catch and
map those inside the producer, and reserve thrown exceptions for defects or
environment failures.

**Over-wide error algebra.** Symptom. Every function returns
`Result<A, AppError>`, matches have long default branches, and a small parser
appears able to fail with database errors. Cause. The team used one global
error type for all layers. Fix. Give each module a narrow error type and map
outward at module boundaries.

**Lost diagnostics.** Symptom. Operators see `Err(InvalidInput)` but cannot
find which field or request caused it. Cause. The error value is typed but too
small, or diagnostic context was dropped during `mapError`. Fix. Keep stable
machine fields on the error and attach request context in telemetry rather than
in user-facing prose.

**Result everywhere.** Symptom. Pure calculations, constructors, and invariant
checks all return result values, and application code becomes a chain of
wrappers. Cause. The pattern was applied as a style rule instead of a contract
decision. Fix. Return plain values for total functions, use assertions for
impossible states, and use Result Either for expected recovery decisions.

**Invalid local encoding.** Symptom. A Go or TypeScript value has both `value`
and `err` populated, or neither populated, and different callers interpret it
differently. Cause. The local type exposed its fields or lacked a discriminator.
Fix. Add a tag, private fields, constructors, and one match or fold function.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Result Either | Exceptions | Option Optional | Validation | Error code return | Panic Abort |
|---|---|---|---|---|---|---|
| Expected failure visibility | High. In the return type | Medium. Often absent from the type | Medium. Absence visible, reason absent | High. Error set visible | Low to medium | None |
| Success value coupling | Low. Success type is direct | Low on success path | Low | Low | Often split from status | None |
| Failure detail | High when error algebra is typed | High when caught with type and context | None | High, often many errors | Low unless paired with lookup | Process stops |
| Fail-fast composition | Strong with bind or propagation | Strong with throw | Weak | Weak by design | Manual branches | Not applicable |
| Error accumulation | Weak | Weak | None | Strong | Manual | None |
| Interop with exception APIs | Needs bridge | Native | Needs bridge | Needs bridge | Native in C-style APIs | Native for defects |
| Cognitive load | Medium | Low at first, higher across boundaries | Low | Medium | Low at first, higher with tables | Low |
| Operability | Strong with named cases and metrics | Strong if caught and logged well | Weak | Strong for form-like input | Weak without mapping | Strong crash signal, no recovery |
| Privacy control | Good if error fields are designed | Mixed, stack traces can leak | Good | Good | Mixed | Mixed |
| Best fit | Recoverable domain failure | Exceptional runtime failure and host APIs | Missing value with no reason | Many independent errors | Low-level ABI boundaries | Broken invariant |

Reading of the table. Result Either is the best fit when the caller can
recover or choose product behavior from a typed failure. Exceptions remain a
good fit for APIs whose host contract is exception-based, for defects, and for
failures that cannot be handled locally. Option is smaller when absence has no
reason. Validation wins when all field errors should be returned together.
Panic or abort belongs to invariant failure, not normal refusal.

## 13. Related and incompatible patterns

- **Railway-Oriented Programming.** Composes directly. Result Either is the
  value shape. Railway-Oriented Programming is the workflow style that connects
  many result-returning steps.
- **Monad.** Result Either has the monadic shape when the error side is fixed
  and `bind` connects success to the next fallible computation. That relation
  explains fail-fast composition.
- **Applicative and Validation.** Related but different. Applicative validation
  can gather independent errors. Result Either with `bind` stops at the first
  error.
- **Option Optional.** A smaller cousin. Option says value or no value. Result
  Either says value or reason. Use Option when the reason has no behavior.
- **Null Object.** Sometimes replaces Result Either when the caller can proceed
  with a behavior-preserving object. It conflicts when the failure reason is a
  product decision.
- **Exception Translation.** Composes at boundaries. Catch host exceptions,
  translate known ones into typed errors, and translate the final typed error
  into the host protocol.
- **Circuit Breaker and Retry.** Compose outside the result. The error side can
  say whether an operation is retryable, but the retry policy itself should not
  be hidden inside `map` chains.
- **Panic Flow.** Incompatible for expected failure. A panic says the program
  reached a state it should not recover from locally. A result says the caller
  has a normal branch to choose.
- **Unchecked Null Flow.** Incompatible. Null erases the reason and often moves
  the failure far from the source.

## 14. Refactoring path in and out

Introducing Result Either into existing code.

1. Pick one boundary where expected failure already exists. Good first targets
   are parsers, validators, command handlers, and repository methods with
   not-found behavior.
2. List the decisions callers make today. If every caller treats failure the
   same way, do not introduce a wide error type.
3. Create a small error algebra with stable names. Prefer cases such as
   `InvalidEmail`, `AccountClosed`, or `VersionConflict` over prose strings.
4. Change the producer to return `Result<Success, Error>` or
   `Either<Error, Success>`.
5. Convert known local exceptions, nulls, booleans, or sentinel values into the
   new failure cases.
6. Update the nearest caller to match both cases and translate once into the
   outer protocol.
7. Add tests for each error case and one success case.
8. Move outward one call at a time. Do not convert the whole application in one
   pass.
9. Add combinators only when repeated matching appears. Start with `map`,
   `mapError`, `bind`, and `fold`.

Removing Result Either when it stops earning its place.

1. Find result-returning functions whose error side has one case and no caller
   branches on it.
2. If the only failure is absence, replace the result with Option or Optional
   and move the old reason into logs if needed.
3. If the failure is unrecoverable, replace the result with an exception,
   assertion, panic, or startup failure according to the host language.
4. If every caller translates the result into the same exception immediately,
   move the translation into the producer and delete the intermediate result.
5. If many independent validation failures are needed, replace bind chains with
   a validation accumulator and return a non-empty error collection.
6. Delete unused combinators after call sites are simplified. A tiny result API
   is easier to review than a copied functional library.

Cross reference the refactoring family entries for Replace Error Code with
Exception, Replace Exception with Result, Introduce Parameter Object when error
details need structure, and Replace Conditional with Polymorphism when error
handling dispatch has become behavior-heavy.

## 15. Testing and verification

Engineering judgement. Result Either makes error testing direct because the
failure is a value. It also creates new contract tests because callers now rely
on exact error cases.

What becomes easier.

- Unit tests can assert `Err(InvalidEmail)` or `Left(ParseError)` without
  catching control flow.
- Property tests can generate invalid inputs and check that each invalid class
  maps to the promised error case.
- Workflow tests can assert short-circuit behavior by using a later step that
  records whether it was called.
- Boundary tests can assert translation from domain error to HTTP status,
  message, retry, or exit code.
- Contract tests can run the same success and failure suite against every
  implementation of a fallible interface.

What becomes harder.

- Exhaustive matching needs maintenance when a public error algebra changes.
- Snapshot tests of error values can become brittle if error types carry raw
  messages or stack details.
- Testing interop needs both sides. A boundary adapter should be tested for
  exception-to-result and result-to-exception conversion where both are used.

Useful verification checks.

- For every error case in the algebra, have at least one producer test and one
  boundary translation test.
- For every use of `map`, verify the error case passes through unchanged.
- For every use of `bind`, verify the next function is not called on failure.
- For every `mapError`, verify diagnostic fields survive unless the boundary
  intentionally redacts them.
- For local encodings in TypeScript, Python, or Go, test that constructors
  cannot create both cases at once.

The code examples in this entry were run with `python3`, `go run`, `rustc`, and
`npx tsc` followed by `node` in this workspace.

## 16. Observability signals

Engineering judgement. The pattern improves observability only when the error
side has stable, non-secret labels. A typed error that is never counted is a
private implementation detail.

Record these signals at the boundary where a result leaves a module.

- A counter of results by operation, case, and error kind. Keep labels bounded.
- A duration histogram for the operation, tagged with success or error kind at
  completion.
- A trace event when a failure case is created, with operation name, stable
  error kind, and correlation identifier.
- A conversion counter for exception-to-result adapters, grouped by exception
  class and mapped error kind.
- A discard counter for calls that intentionally convert a result to Option,
  default value, or boolean.
- A short-circuit counter for workflows where skipped steps matter to product
  behavior.

Healthy dashboards show an expected mix. Validation failures may rise after a
new client release. Not-found results may follow traffic. Retryable dependency
failures may appear during an upstream incident and then fall. The key is that
the result label is stable enough to compare across releases.

Failing dashboards show drift. A new error kind appears without a matching
release note. A generic `Unknown` case grows while specific cases fall. A
success counter stays flat while validation errors spike. A discard counter
climbs after a refactor, implying callers may be hiding useful failure
information. A boundary adapter starts converting many exceptions into a single
typed error, which usually means the translation layer is too coarse.

Avoid logging full error values by default. Error values often contain field
names, user input, tokens, file paths, or upstream messages. Put stable error
kinds in metrics. Put detailed diagnostics behind normal redaction rules.

## 17. Security and privacy implications

Engineering judgement. Result Either does not authenticate users, authorize
actions, encrypt data, or sanitize input by itself. Its security value is in
making expected refusal explicit and auditable.

Positive implications.

- Authorization and validation failures can be represented as named cases, so
  the boundary can map them consistently to product responses.
- A typed error algebra can separate user-safe messages from internal causes.
- Short-circuiting can stop later steps after a failed validation or policy
  check, reducing accidental side effects after refusal.
- Tests can assert that sensitive failures map to redacted output.

Risks.

- Error values can leak secrets if they carry raw exception messages, SQL text,
  tokens, file paths, request bodies, or stack traces.
- Over-specific public errors can aid enumeration. For example, separating
  `EmailNotFound` from `WrongPassword` in a login response may disclose account
  existence.
- A generic catch-all adapter can launder defects into normal domain errors,
  causing monitoring to miss a security bug.
- A caller that unwraps, panics, or defaults on error can turn a typed refusal
  into denial of service or unauthorized success behavior.

Practical rules.

- Keep internal diagnostic fields separate from public presentation fields.
- Redact before crossing process, tenant, or trust boundaries.
- Treat `Unknown` as an alert-worthy case, not as a place to hide defects.
- For authentication flows, map multiple internal errors to the same external
  message when distinct messages would disclose sensitive facts.
- Do not use Result Either as a substitute for access checks. A result can
  carry the result of a check, but something still has to perform the check.

## Code examples

### TypeScript

```typescript
type Result<T, E> =
  | { tag: "ok"; value: T }
  | { tag: "err"; error: E };

const ok = <T, E>(value: T): Result<T, E> => ({ tag: "ok", value });
const err = <T, E>(error: E): Result<T, E> => ({ tag: "err", error });

function bind<T, U, E>(
  result: Result<T, E>,
  next: (value: T) => Result<U, E>,
): Result<U, E> {
  return result.tag === "ok" ? next(result.value) : result;
}

function parseAmount(text: string): Result<number, string> {
  const value = Number(text);
  return Number.isFinite(value) ? ok(value) : err("amount is not numeric");
}

function positive(value: number): Result<number, string> {
  return value > 0 ? ok(value) : err("amount must be positive");
}

function priceLabel(text: string): Result<string, string> {
  return bind(bind(parseAmount(text), positive), (value) =>
    ok(`USD ${value.toFixed(2)}`),
  );
}

console.log(priceLabel("12.5"));
console.log(priceLabel("-1"));
```

### Python

```python
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E")


@dataclass(frozen=True)
class Ok(Generic[T, E]):
    value: T

    def bind(self, fn: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        return fn(self.value)


@dataclass(frozen=True)
class Err(Generic[T, E]):
    error: E

    def bind(self, fn: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        return Err(self.error)


Result = Ok[T, E] | Err[T, E]


def parse_int(text: str) -> Result[int, str]:
    try:
        return Ok(int(text))
    except ValueError:
        return Err("not an integer")


def reciprocal(n: int) -> Result[float, str]:
    if n == 0:
        return Err("zero has no reciprocal")
    return Ok(1 / n)


def program(text: str) -> Result[float, str]:
    return parse_int(text).bind(reciprocal)


assert program("4") == Ok(0.25)
assert program("0") == Err("zero has no reciprocal")
assert program("x") == Err("not an integer")
print(program("4"))
```

### Go

```go
package main

import "fmt"

type Result[T any, E any] struct {
	value T
	err   E
	ok    bool
}

func Ok[T any, E any](value T) Result[T, E] {
	return Result[T, E]{value: value, ok: true}
}

func Err[T any, E any](err E) Result[T, E] {
	return Result[T, E]{err: err}
}

func Bind[T any, U any, E any](
	result Result[T, E],
	next func(T) Result[U, E],
) Result[U, E] {
	if !result.ok {
		return Err[U](result.err)
	}
	return next(result.value)
}

func parsePort(text string) Result[int, string] {
	var port int
	_, scanErr := fmt.Sscanf(text, "%d", &port)
	if scanErr != nil {
		return Err[int]("port is not numeric")
	}
	if port < 1 || port > 65535 {
		return Err[int]("port out of range")
	}
	return Ok[int, string](port)
}

func endpoint(port int) Result[string, string] {
	return Ok[string, string](fmt.Sprintf("127.0.0.1:%d", port))
}

func configure(text string) Result[string, string] {
	return Bind(parsePort(text), endpoint)
}

func main() {
	fmt.Println(configure("8080"))
	fmt.Println(configure("0"))
}
```

### Rust

```rust
#[derive(Debug, PartialEq)]
enum LoginError {
    BadName,
    WeakPassword,
}

fn normalize_name(raw: &str) -> Result<String, LoginError> {
    let trimmed = raw.trim();
    if trimmed.is_empty() {
        Err(LoginError::BadName)
    } else {
        Ok(trimmed.to_lowercase())
    }
}

fn check_password(raw: &str) -> Result<&str, LoginError> {
    if raw.len() < 8 {
        Err(LoginError::WeakPassword)
    } else {
        Ok(raw)
    }
}

fn create_login(name: &str, password: &str) -> Result<String, LoginError> {
    let name = normalize_name(name)?;
    check_password(password)?;
    Ok(format!("{name}:ready"))
}

fn main() {
    assert_eq!(create_login(" Ada ", "long-pass"), Ok("ada:ready".to_string()));
    assert_eq!(create_login("", "long-pass"), Err(LoginError::BadName));
    assert_eq!(create_login("Ada", "short"), Err(LoginError::WeakPassword));
    println!("{:?}", create_login(" Ada ", "long-pass"));
}
```

## 18. References

- Haskell `base` documentation, `Data.Either`, `Either`, `Left`, `Right`,
  `either`, `isLeft`, `isRight`, and `partitionEithers`,
  https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Data-Either.html,
  verified 2026-08-02.
- Rust standard library documentation, `std::result::Result`, enum variants
  `Ok(T)` and `Err(E)`, methods including `map`, `map_err`, and `and_then`,
  https://doc.rust-lang.org/std/result/enum.Result.html, verified 2026-08-02.
- Rust standard library documentation, `std::result` module, returning and
  propagating errors, https://doc.rust-lang.org/std/result/, verified
  2026-08-02.
- Swift standard library documentation, `Result<Success, Failure>`, cases
  `success` and `failure`, methods `map`, `mapError`, `flatMap`,
  `flatMapError`, and `get`, https://developer.apple.com/documentation/Swift/Result,
  verified 2026-08-02.
- Apple Developer Documentation, `Result.get()`,
  https://developer.apple.com/documentation/swift/result/get%28%29, verified
  2026-08-02.
- Apple Developer Documentation, "Writing Failable Asynchronous APIs",
  https://developer.apple.com/documentation/swift/writing-failable-asynchronous-apis,
  verified 2026-08-02.
- Scala standard library documentation, `scala.util.Either`, right-biased
  `map` and `flatMap`, https://www.scala-lang.org/api/2.13.16/scala/util/Either.html,
  verified 2026-08-02.
- FSharp.Core documentation, `Result` module, `Result<'T,'TError>`, `bind`,
  `map`, `mapError`, `isOk`, and `isError`,
  https://fsharp.github.io/fsharp-core-docs/reference/fsharp-core-resultmodule.html,
  verified 2026-08-02.
- Arrow Core API documentation, `Either`, examples using `Either.Left`,
  `Either.Right`, `flatMap`, and `map`,
  https://apidocs.arrow-kt.io/arrow-core/arrow.core/-either/index.html,
  verified 2026-08-02.
- Arrow documentation, "Typed errors", wrapper types including `Either`,
  `Option`, and `Result`, https://arrow-kt.io/learn/typed-errors/, verified
  2026-08-02.
- Vavr API documentation, `io.vavr.control.Either`,
  https://javadoc.io/doc/io.vavr/vavr/1.0.1/io/vavr/control/Either.html,
  verified 2026-08-02.
- fp-ts core documentation, `Either.ts`, `map`, `mapLeft`, and disjoint-union
  API, https://fp-ts.github.io/core/modules/Either.ts.html, verified
  2026-08-02.
