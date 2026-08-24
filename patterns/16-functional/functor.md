---
name: Functor
slug: functor
family: 16-functional
category: Functional
aliases: [Mappable, Covariant Functor, Fmap]
first_described: "Eilenberg and Mac Lane 1945"
maturity: canonical
related: [applicative, monad, bifunctor, contravariant-functor, natural-transformation, iterator]
incompatible_with: [contravariant-functor-for-the-same-parameter, effectful-map]
verified: 2026-08-02
---

# Functor

## 1. Name, aliases, and lineage

The canonical name is Functor. In software, the name usually means a
parameterized container, context, or computation shape that can apply a pure
function to the value inside it while keeping the outer shape intact. Haskell's
`Data.Functor` documentation describes `Functor` as the class for types that can
be mapped over, with `fmap :: (a -> b) -> f a -> f b`, and states the identity
and composition laws for valid instances
(https://downloads.haskell.org/~ghc/9.6.1/docs/libraries/base-4.18.0.0/Data-Functor.html,
verified 2026-08-02). The Haskell 2010 Report also lists the `Functor` class in
section 6.3.5 and gives the same two laws
(https://www.haskell.org/onlinereport/haskell2010/, verified 2026-08-02).

The term comes from category theory. Samuel Eilenberg and Saunders Mac Lane
introduced the category-theoretic language around categories and functors in
"General Theory of Natural Equivalences", *Transactions of the American
Mathematical Society*, volume 58, 1945. Saunders Mac Lane, *Categories for the
Working Mathematician*, second edition, Springer, 1998, chapter I, section 3,
is the standard book citation for the mathematical definition and uses chapter
I to introduce categories, functors, and natural transformations. I am not
citing a page number because I did not verify the page image in this session.

Common software aliases are **mappable**, **covariant functor**, and **fmap**.
Scala Cats calls its `Functor` "covariant functor" and defines the operation as
`map[A, B](fa: F[A])(f: A => B): F[B]`
(https://typelevel.org/cats/api/cats/Functor.html, verified 2026-08-02).
fp-ts uses the same shape in TypeScript, with `map` lifting an `a -> b`
function to an `f a -> f b` function
(https://gcanti.github.io/fp-ts/modules/Functor.ts.html, verified 2026-08-02).

The word is overloaded in C++ and some older object-oriented texts, where
"functor" can mean "function object", an object that can be called like a
function. That is a different pattern. This entry is about the functional
Functor: a lawful mapping interface for a type constructor. The difference is
practical. A function object represents a callable operation. A software
Functor in this entry represents a context, such as optionality, a list, a
future result, a validation result, or an error-bearing result, and provides a
way to transform the successful or present value without unpacking the context.

## 2. Problem and context

A codebase has many values that are not plain values. A customer id may be
missing. A remote call may have failed. A parser may have produced either an
error or a result. A list may carry zero, one, or many values. A future may
carry a value later. A domain wrapper may carry metadata with the domain value.
In each case, the application wants to run an ordinary transformation, such as
`Customer -> EmailAddress` or `RawAmount -> Money`, while preserving the outer
context.

Without the pattern, each context grows its own manual unwrapping style. The
optional case checks for absence. The result case checks for failure. The list
case loops. The future case registers a callback. The domain wrapper case
copies metadata by hand. The business transformation gets tangled with the
mechanics of the context, and the same missing-value or error-propagation rules
are rewritten in many places.

Functor solves the narrow version of that problem. It says that if a context
has one covariant value position, the context can offer a mapping operation. The
mapping operation receives a pure function for the inside value. It returns the
same kind of context with the transformed inside value. It does not flatten
nested contexts, combine two independent contexts, or decide what to do with an
effectful function. Those are jobs for Monad, Applicative, Traverse, or an
effect system.

The useful mental model is simple. Keep the box. Change the content. For
`Option<A>`, `map` changes `Some<A>` to `Some<B>` and leaves `None` absent. For
`Result<A, E>`, `map` changes the success value and leaves the error side
untouched. For `List<A>`, `map` changes each element and keeps length and order.
For a lazy stream, `map` records a transformation in a pipeline. Java `Stream`
documents `map` as an intermediate operation that returns a stream of results
after applying the provided function to the elements
(https://docs.oracle.com/javase/8/docs/api/java/util/stream/Stream.html,
verified 2026-08-02).

The context is the boundary of applicability. A Functor is not a general escape
from control flow. It is a local abstraction for "I can transform the value
position and leave the context policy alone." That policy might be absence,
error retention, multiplicity, laziness, or metadata retention.

The pattern becomes valuable when that sentence appears in many places with
different data types. A claims system may parse a submitted amount, produce an
optional decimal, map it to a currency value, then map that to a display model.
An ingestion service may read many raw events, map each event to a normalized
record, and keep the stream boundary for batching. A validation layer may keep a
failed result unchanged while mapping the valid value to a richer domain type.
Those examples do not need the caller to know how optionality, streaming, or
failure is represented. The caller supplies the pure transform, and the context
owns the rest.

There is a second context that matters in real teams: refactoring context. Code
often starts with conditionals and loops because that is the clearest first
version. Functor earns its place when those local mechanics are repeated often
enough that they obscure the domain transform. In an optional pipeline, the
domain step should read as "parse amount, price amount, display amount", not
"check for missing value, call parser, check for missing value, call pricer,
check for missing value." In a collection pipeline, the business transform
should not be buried under allocation and index management unless those details
are the point of the code.

The laws are part of the problem statement, not academic ornament. They tell
maintainers which edits are valid. If `map(identity)` changes a value, then a
debugging edit that inserts an identity mapper has changed behavior. If
`map(f).map(g)` differs from `map(g after f)`, then an optimization that fuses
adjacent maps has changed behavior. The Haskell and fp-ts documentation publish
both laws for this reason
(https://downloads.haskell.org/~ghc/9.6.1/docs/libraries/base-4.18.0.0/Data-Functor.html,
verified 2026-08-02;
https://gcanti.github.io/fp-ts/modules/Functor.ts.html, verified
2026-08-02). The laws convert a nice method name into a refactoring contract.

## 3. Forces

This dimension is engineering judgement, except where a named API or law is
cited.

- **Coupling.** Favoured. Business transformations depend on plain functions
  and the `map` operation, not on the representation of absence, failure, or
  iteration.
- **Consistency.** Favoured. A lawful `map` centralizes the rule for preserving
  context. The identity law says mapping identity returns the original context,
  and the composition law says mapping two functions in sequence has the same
  result as mapping their composition. Haskell and fp-ts both publish these
  laws in their Functor documentation
  (https://downloads.haskell.org/~ghc/9.6.1/docs/libraries/base-4.18.0.0/Data-Functor.html,
  verified 2026-08-02;
  https://gcanti.github.io/fp-ts/modules/Functor.ts.html, verified
  2026-08-02).
- **Latency.** Mixed. Eager containers such as arrays and lists pay one
  function call per element and often allocate a same-size output structure.
  Lazy streams can defer that work, but long chains may hide when the work
  actually runs.
- **Allocation cost.** Mixed. Mapping immutable structures usually creates a
  new outer value. Mapping a lazy pipeline can allocate a pipeline node rather
  than the final values. Mapping `None`, `Err`, or an empty collection can be
  cheap because no inner transformation runs.
- **Operability.** Sacrificed unless teams add tracing around pipelines.
  Business names can disappear into chains of `map` calls, and a production
  trace may show only one request span unless the mapping boundary is named.
- **Team topology.** Favoured when platform teams own context types and product
  teams own pure transformations. Teams can share error or absence semantics
  without sharing every transformation.
- **Cognitive load.** Sacrificed for readers who do not know the laws or the
  difference between `map`, `flatMap`, and `traverse`. Favoured for readers who
  do know them, because many wrappers then behave under one rule.
- **Security and privacy.** Mixed. Central context preservation can avoid
  accidental unwrapping and logging of failure details, but careless mapping can
  copy sensitive values into longer-lived wrappers.

The pattern favours local reasoning and algebraic consistency. It sacrifices
some directness. A reader must know what context policy a given `map` preserves.

Another force is the distance between domain language and type-system language.
In Haskell, Cats, and fp-ts, the Functor name is visible and intentional. In
Java, Swift, and Rust, the pattern is often present as a concrete `map` method
without the word Functor in the API. Java `Optional.map`, Swift `Optional.map`,
and Rust `Option::map` all give practical examples of the same shape through
concrete standard-library types
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Optional.html,
verified 2026-08-02;
https://developer.apple.com/documentation/swift/optional/map%28_%3A%29,
verified 2026-08-02;
https://doc.rust-lang.org/stable/std/option/index.html, verified
2026-08-02). Engineering judgement: teams should prefer the vocabulary that
their language community already uses. Calling every `Optional.map` a Functor
in Java application code may distract readers, while using the Functor name in
a Cats module is normal and precise.

## 4. Applicability and non-applicability

Reach for Functor when these conditions hold.

- A type has exactly one value position that can vary from `A` to `B` while the
  outer type constructor stays the same.
- You want to transform the success, present, element, or payload side of a
  context while leaving absence, failure, ordering, timing, or metadata policy
  in the context type.
- Callers keep repeating manual unwrap, transform, and rewrap logic.
- You can state and test the identity and composition laws for the mapping
  operation.
- You want business functions to stay pure and context-free, then lift those
  functions into contextual code.
- The language or library already uses `map` for the context, such as Java
  `Optional.map`, Swift `Optional.map`, Rust `Option::map`, or Scala Cats
  `Functor.map` (https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Optional.html,
  verified 2026-08-02;
  https://developer.apple.com/documentation/swift/optional/map%28_%3A%29,
  verified 2026-08-02;
  https://doc.rust-lang.org/stable/std/option/enum.Option.html,
  verified 2026-08-02;
  https://typelevel.org/cats/api/cats/Functor.html, verified 2026-08-02).

Do not reach for Functor in these cases.

- **The function returns the same context.** Use Monad or `flatMap` when the
  transformation already returns `Option<B>`, `Result<B, E>`, `Future<B>`, or a
  similar wrapper. Java `Optional.flatMap` documents this distinction by saying
  that `flatMap` does not wrap an already optional result inside another
  optional (https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Optional.html,
  verified 2026-08-02).
- **You need to combine independent contexts.** Mapping one contextual value
  cannot combine `F<A>` and `F<B>` into `F<C>`. Use Applicative, product
  combinators, or explicit domain logic.
- **You need effects during traversal.** A mapper that logs, calls a network
  service, mutates state, or reads time is outside the pure Functor contract.
  The code may still compile, but the laws stop being a reliable design tool.
- **The type parameter is consumed, not produced.** A sink such as
  `Serializer<A>` or `Predicate<A>` is usually contravariant over `A`. Mapping
  forward with `A -> B` is the wrong direction for that parameter.
- **The context has two meaningful type parameters and both matter.** A pair,
  map entry, or result with transformable left and right sides may need
  Bifunctor, or it may need a project-specific method such as `mapError`.
- **The mapping function must change the shape.** Filtering elements, sorting a
  collection, retrying a future, or changing an error policy is shape work, not
  Functor work.
- **A plain function call is clearer.** If the value is already plain `A`, wrap
  and map adds ceremony. Use `f(a)`.
- **The context cannot obey the laws.** A `map` that drops elements, duplicates
  elements, changes timestamps, increments counters, or rewrites metadata based
  on the function identity is not a lawful Functor.
- **The language cannot express the abstraction cleanly.** Some languages lack
  higher-kinded types. A local `map` method on a concrete type may still be
  useful, but a generic Functor type class can become more complex than the
  code it replaces.

## 5. Structure

The participants are named by role.

- **Context type constructor.** A type-level shape such as `Option<_>`,
  `Result<_, E>`, `List<_>`, `Future<_>`, or `Box<_>`. It has a value position
  that can change from `A` to `B`.
- **Mapped value.** The `A` inside the context. There may be zero values, one
  value, many values, a delayed value, or a value paired with metadata.
- **Pure transformer.** A function `A -> B`. It knows nothing about absence,
  errors, retries, collection allocation, or wrapper internals.
- **Map operation.** The operation that lifts the transformer to work over the
  context. Its abstract shape is `(A -> B) -> F<A> -> F<B>`, or in method form,
  `F<A>.map(A -> B): F<B>`.
- **Context policy.** The hidden rule for preserving the outer structure. In an
  optional value, absence stays absent. In a list, length and order stay under
  the list rules. In a result, the error side passes through unchanged when the
  success side is mapped.
- **Functor laws.** The identity and composition equations. They make `map`
  more than a convenience method.

The structure is intentionally smaller than many object-oriented patterns. No
client-visible class hierarchy is required. A concrete type may expose `map` as
an instance method, as Java, Rust, and Swift do for optional values. A library
may expose `Functor` as a type class, as Haskell, Cats, and fp-ts do. In either
shape, the core relation is the same: plain transformation in, contextual
transformation out.

The participant that deserves the most care is the context policy. In a
well-designed Functor, that policy is boring and stable. `None` does not become
`Some`. An error does not become success. A list does not reorder itself. A
wrapper does not rewrite its trace id. This is why the pattern is useful for
business code: the mapper can focus on the domain value because context behavior
is already settled. If the context policy is still under debate, introducing
Functor too early can freeze a weak rule behind a familiar name.

There is also a useful negative participant: the client does not inspect the
inside representation. If callers can reach into the wrapper and mutate the
inner value, `map` becomes a convention rather than a boundary. Immutable values
make the contract easier to keep, but mutability does not make Functor
impossible. It means the implementation must be stricter about copying,
aliasing, and equality in tests.

## 6. ASCII structure diagram

```text
          type constructor F<_>
        +------------------------+
        |      context F<A>      |
        |------------------------|
        | policy: keep shape     |
        | value position: A      |
        +-----------+------------+
                    |
                    | map(transform)
                    v
        +------------------------+
        |      context F<B>      |
        |------------------------|
        | same outer policy      |
        | value position: B      |
        +------------------------+

        +------------------------+
        | transformer            |
        |------------------------|
        | A -> B                 |
        | no context knowledge   |
        +------------------------+

        Functor contract:
        map(id)              == id
        map(compose(g, f))   == compose(map(g), map(f))
```

## 7. Dynamics

At runtime, `map` asks the context whether it has values to expose to the
transformer. The transformer never decides how to handle absence, failure, or
iteration. The context decides that, then returns a new context of the same
kind.

```text
Client                 Context F<A>             Transformer A -> B
  |                         |                            |
  | map(transform)          |                            |
  |------------------------>|                            |
  |                         | inspect outer state        |
  |                         |------------------+         |
  |                         |                  |         |
  |                         | no value/error   |         |
  |                         | return F<B> with |         |
  |                         | same absence or  |         |
  |                         | failure policy   |         |
  |                         |<-----------------+         |
  |                         |                            |
  |                         | value present              |
  |                         |--------------------------->|
  |                         |        apply A -> B        |
  |                         |<---------------------------|
  |                         | wrap B in same context     |
  |<------------------------|                            |
  |                         |                            |

For a list, the value-present branch repeats for each element in order.
For a lazy stream, this flow may be recorded and run later.
```

The dynamics matter because many bugs come from putting the wrong concern in
the transformer. A transformer that handles `None`, retries a network call, or
logs the whole error object has taken over context policy from `map`. When that
happens, the code may still be readable in the small, but the value of a shared
Functor contract is gone.

## 8. Implementation variants

**Concrete method on a concrete context.** Java `Optional.map`, Rust
`Option::map`, Swift `Optional.map`, and Java `Stream.map` expose mapping as a
method on the concrete type
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Optional.html,
verified 2026-08-02;
https://doc.rust-lang.org/stable/std/option/enum.Option.html, verified
2026-08-02;
https://developer.apple.com/documentation/swift/optional/map%28_%3A%29,
verified 2026-08-02;
https://docs.oracle.com/javase/8/docs/api/java/util/stream/Stream.html,
verified 2026-08-02). This is easy to read and works well when code does not
need to abstract over many context types.

**Type class.** Haskell, Cats, and fp-ts expose Functor as an abstraction over
type constructors. This supports generic code such as "lift this pure function
into any `F` that has a Functor instance." The cost is type-system weight.
Scala Cats documents `Functor[F[_]]` and a `map` operation over `F[A]`
(https://typelevel.org/cats/api/cats/Functor.html, verified 2026-08-02). fp-ts
models multiple arities through interfaces such as `Functor`, `Functor1`, and
`Functor2` because TypeScript lacks native higher-kinded types
(https://gcanti.github.io/fp-ts/modules/Functor.ts.html, verified 2026-08-02).

**Module-level function.** Some libraries place `map` beside the type rather
than on the type. This can fit languages that prefer functions over methods.
The trade is discoverability. Readers must know where the module function lives.

**Right-biased mapping.** A two-parameter type such as `Result<E, A>` often maps
only the success side. Haskell's documentation notes that for type constructors
with more than one parameter, such as `Either`, `fmap` modifies only the last
type parameter, and `Bifunctor` can map two positions
(https://downloads.haskell.org/~ghc/9.6.1/docs/libraries/base-4.18.0.0/Data-Functor.html,
verified 2026-08-02). Rust exposes `Result::map` for the success side and
separate error mapping APIs in the standard library, but this entry cites only
`Option::map` for Rust because that was the page fetched live.

**Lazy mapping.** Streams and iterators often store the transform and perform
work later. Java `Stream.map` is documented as an intermediate operation
(https://docs.oracle.com/javase/8/docs/api/java/util/stream/Stream.html,
verified 2026-08-02). The benefit is pipeline fusion and early termination.
The cost is delayed failures and stack traces that point to consumption rather
than construction.

**Derived mapping.** In a Monad, `map` can often be defined through bind and a
pure constructor. The Haskell 2010 Report states a relation between `fmap` and
`>>=` for types that are both Monad and Functor
(https://www.haskell.org/onlinereport/haskell2010/, verified 2026-08-02).
The trade is conceptual: deriving `map` from Monad can be correct, but teaching
every mapping problem as Monad work makes simple transformations look heavier
than they are.

**Metadata-preserving domain wrapper.** Many application teams create wrappers
that carry a value plus metadata: source system, tenant, validation state,
classification, locale, or trace information. A lawful `map` for that wrapper
changes the value and leaves the metadata according to a clear rule. This
variant is less famous than `Option` or `List`, but it is common in domain
code. The implementation must decide whether metadata is copied exactly,
recomputed, or narrowed. Only exact preservation is the default Functor story.
Recomputed metadata may still be correct domain behavior, but then the method
may need a stronger name than `map`.

**Error-side mapping as a sibling operation.** Result-like types often have two
separate transforms: one for success and one for error. The success-side
operation is the Functor map for the value parameter. The error-side operation
is a different mapping over a different parameter. Mixing the two under one
method name is a source of incidents because a caller may think it is preserving
failure policy while changing it. Prefer names such as `mapError`,
`leftMap`, or `bimap` where the language or library convention supports them.

**Partial application over multi-parameter types.** A type such as
`Either<E, A>` becomes a Functor only after fixing one parameter. Haskell's
documentation describes `fmap` over multi-parameter constructors as modifying
the last parameter
(https://downloads.haskell.org/~ghc/9.6.1/docs/libraries/base-4.18.0.0/Data-Functor.html,
verified 2026-08-02). The software design lesson is concrete: be explicit
about which parameter your mapping changes. A result type that maps its error
side by default will surprise readers trained on right-biased result APIs.

## 9. Known production uses

- **GHC base, `Data.Functor`.** The Haskell `base` library documents the
  `Functor` class, `fmap`, operators such as `<$>`, and instances including
  `Maybe`, lists, and `IO`
  (https://downloads.haskell.org/~ghc/9.6.1/docs/libraries/base-4.18.0.0/Data-Functor.html,
  verified 2026-08-02). This is a named standard library use of the pattern as
  a first-class type class.
- **Scala Cats, `cats.Functor`.** Cats documents `Functor[F[_]]`, the `map`
  method, laws in `cats.laws.FunctorLaws`, and derived operations such as
  `lift`, `as`, and `fproduct`
  (https://typelevel.org/cats/api/cats/Functor.html, verified 2026-08-02).
  This is a named production library use for generic functional programming on
  the JVM.
- **fp-ts, `Functor.ts`.** fp-ts documents `Functor` interfaces for TypeScript
  and gives the identity and composition laws
  (https://gcanti.github.io/fp-ts/modules/Functor.ts.html, verified
  2026-08-02). This is a named production library use that adapts the type
  class idea to TypeScript.
- **Java standard library, `Optional.map` and `Stream.map`.** Oracle's Java 21
  `Optional` API documents `map` as applying a mapping function to a present
  value and returning empty when no value is present
  (https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Optional.html,
  verified 2026-08-02). Oracle's Java 8 `Stream` API documents `map` as an
  intermediate operation over stream elements
  (https://docs.oracle.com/javase/8/docs/api/java/util/stream/Stream.html,
  verified 2026-08-02).
- **Swift standard library, `Optional.map`.** Apple documents `Optional.map` as
  evaluating a closure when the optional is not `nil`, returning `nil` when it
  is `nil`
  (https://developer.apple.com/documentation/swift/optional/map%28_%3A%29,
  verified 2026-08-02).
- **Rust standard library, `Option::map`.** Rust documents optional values in
  `std::option` and describes `map` as transforming `Option<T>` to `Option<U>`
  by applying the function to `Some` and leaving `None` unchanged
  (https://doc.rust-lang.org/stable/std/option/index.html, verified
  2026-08-02).

These uses are not identical in surface design. Haskell, Cats, and fp-ts expose
Functor as a named abstraction. Java, Swift, and Rust expose the same design
through concrete methods on standard-library types. That spread is evidence of
the pattern's practical shape: the method-level idea is useful even where the
language does not make higher-kinded abstraction pleasant.

## 10. Consequences

This dimension is engineering judgement, with cited APIs supplying concrete
examples.

Positive consequences:

- Plain transformations become reusable. A function from `A` to `B` can serve
  optional, list, result, stream, and future-shaped code when each context has
  `map`.
- Context policy is centralized. Absence handling, error pass-through, element
  order, and metadata copying live in the context implementation rather than in
  each caller.
- Refactoring gets safer when laws hold. Identity and composition give a team a
  basis for merging adjacent maps or splitting a transformation for naming.
- Failure paths become quieter. Mapping over empty or failed contexts avoids
  repeated conditional code.
- Tests can target pure functions separately from context preservation.
- API vocabulary shrinks. A reader who knows `map` can recognize the same idea
  across Java `Optional`, Swift `Optional`, Rust `Option`, Java streams, Cats,
  fp-ts, and Haskell.

Negative consequences:

- Lawless instances are worse than no abstraction. A `map` that changes shape
  or triggers hidden effects invites refactors that alter behavior.
- Chains can hide operational boundaries. A long pipeline can make it hard to
  know which transform failed or which one allocated a large structure.
- Error handling can become too implicit. New team members may miss that an
  error or absence is being carried forward.
- Generic type class encodings can be hard in languages without higher-kinded
  types. fp-ts needs several interfaces for arity and encoding support
  (https://gcanti.github.io/fp-ts/modules/Functor.ts.html, verified
  2026-08-02).
- Debugging lazy maps can be surprising because the transformation is declared
  in one place and executed elsewhere.
- Overuse can turn clear domain steps into anonymous lambdas. Naming still
  matters.

## 11. Failure modes and misuse

This dimension is engineering judgement.

- **Symptom.** Mapping identity changes the object, metadata, order, counter,
  cache key, timestamp, or trace attribute.
  **Cause.** The `map` implementation changes the outer context, not only the
  mapped value.
  **Fix.** Move shape or metadata changes into a different operation. Add a
  property test for `map(identity) == identity`.

- **Symptom.** Replacing `x.map(f).map(g)` with `x.map(a => g(f(a)))` changes
  logs, counters, retry behavior, or exceptions.
  **Cause.** The mapping functions perform side effects, or `map` itself does.
  **Fix.** Keep mappers pure. Use an effect-aware abstraction for work that
  touches time, I/O, randomness, tracing, or mutation.

- **Symptom.** Code returns `Option<Option<T>>`, `Result<Result<T, E>, E>`, or
  `Future<Future<T>>` after a transformation.
  **Cause.** `map` was used with a function that already returns the context.
  **Fix.** Use `flatMap`, `andThen`, or the local monadic bind operation.

- **Symptom.** A list mapping step silently removes records or adds records.
  **Cause.** The operation is filter, expand, or bind, but was named `map`.
  **Fix.** Rename the operation to `filter`, `compactMap`, `flatMap`, or a
  domain-specific verb. Keep `map` shape-preserving.

- **Symptom.** Production traces show one long anonymous pipeline and no clue
  which transformation failed.
  **Cause.** Mapping chains were built only from inline lambdas.
  **Fix.** Name nontrivial transformations and add trace attributes around
  pipeline stages that cross service or data-boundary concerns.

- **Symptom.** Type inference errors mention higher-kinded types, arity, or
  missing instances far away from the business code.
  **Cause.** A generic Functor abstraction was introduced in a language where
  concrete methods would have carried the design with less type machinery.
  **Fix.** Pull the abstraction back to concrete context methods, or confine the
  type class to a small library layer.

- **Symptom.** Sensitive fields appear in logs after an otherwise harmless
  transformation.
  **Cause.** The mapper constructed debug strings or copied raw fields into a
  longer-lived context.
  **Fix.** Treat mapping functions as data-handling code. Redact before mapping
  into loggable structures.

## 12. Trade-off matrix

| Force | Functor `map` | Monad `flatMap` | Applicative `mapN` or product | Iterator loop | Visitor |
|---|---|---|---|---|---|
| Coupling | Low coupling to wrapper internals | Low, but function knows wrapper | Low for independent contexts | Often coupled to representation | Coupled to visited hierarchy |
| Consistency | High when laws hold | High for dependent context steps | High for independent combination | Depends on each loop | Depends on visitor discipline |
| Latency | One transform per value, lazy in streams | May add nested control flow | May evaluate several contexts | Direct and predictable | Dispatch cost per visit |
| Allocation | New context or pipeline node | New context after each bind | New combined context | Caller controls allocation | Visitor object may allocate |
| Cognitive load | Low after `map` vocabulary is known | Higher because nesting is flattened | Higher because arity and failure rules matter | Low locally, higher in repetition | Higher across class graph |
| Operability | Needs named stages in long chains | Needs named stages and error policy | Needs visibility into each input | Easy to place logs | Logs spread across visitor methods |
| Team topology | Good platform/product split | Good for effectful domain flows | Good for validation and assembly | Local team only | Good for closed hierarchies |
| Shape changes | Must not change shape | Can change and flatten shape | Combines fixed shapes | Any change possible | Depends on visitor result |
| Best fit | Transform inside one context | Dependent contextual steps | Combine independent contexts | One-off explicit control | Operations over a closed structure |

The important comparison is not "Functor versus no pattern." It is Functor
versus the named abstractions that handle neighboring work. Functor changes the
inside value. Monad sequences a function that returns the context. Applicative
combines independent contexts. Iterator loops make control explicit. Visitor
separates operations over a closed object structure.

## 13. Related and incompatible patterns

**Applicative.** Applicative extends the idea from one contextual value to
independent contextual values. If Functor lifts `A -> B`, Applicative can apply
contextual functions and combine contexts. Use Applicative when two inputs are
independent.

**Monad.** Monad handles dependent contextual steps. If the next step depends on
the unwrapped value and returns a new context, Functor produces nesting while
Monad flattens it. Many production APIs place `map` and `flatMap` side by side,
including Java `Optional` and Swift `Optional`
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Optional.html,
verified 2026-08-02;
https://developer.apple.com/documentation/swift/optional/map%28_%3A%29,
verified 2026-08-02).

**Bifunctor.** Bifunctor maps two type positions. It is related when a type has
two covariant positions, such as a pair or an either-like value. Haskell's
`Data.Functor` notes that `fmap` maps the last parameter for multi-parameter
constructors and points to `Bifunctor` for mapping two positions
(https://downloads.haskell.org/~ghc/9.6.1/docs/libraries/base-4.18.0.0/Data-Functor.html,
verified 2026-08-02).

**Contravariant Functor.** Contravariant mapping reverses the function direction
for input-consuming positions. It conflicts with covariant Functor for the same
type parameter unless the type is invariant or phantom. A predicate over `A`
cannot covariantly map with `A -> B`; it can contramap with `B -> A`.

**Natural Transformation.** A natural transformation changes the context while
leaving the value type alone, such as `Option<A> -> List<A>`. Functor changes
the value while leaving the context constructor alone. Together, they describe
two independent axes of change.

**Iterator.** Iterator exposes a traversal interface. Functor can be implemented
over iterable structures, but it promises a result in the same kind of context.
Iterator alone does not promise a shape-preserving map.

**Decorator.** Decorator wraps behavior around an object. A Functor context may
look like a wrapper, but its contract is about lawful value transformation, not
runtime behavior extension.

## 14. Refactoring path in and out

This dimension is engineering judgement.

Refactoring in:

1. Find repeated unwrap, transform, and rewrap code for the same context.
2. Name the context policy. Examples: absence stays absent, errors pass through,
   element order stays in list order, metadata is copied unchanged.
3. Add a `map` method or module function for one concrete type. Do not start
   with a generic type class unless callers already need it.
4. Move the repeated policy into `map`.
5. Replace one caller at a time with `context.map(transform)`.
6. Extract nontrivial lambdas into named pure functions.
7. Add identity and composition tests.
8. If several concrete contexts now expose the same shape and the language can
   support it cleanly, introduce a generic Functor interface.

Apply the refactoring in the smallest vertical slice that proves the policy.
For an optional domain value, start with one field or one parser result. For a
collection, start with one transformation that already preserves length and
order. For a result type, start with success-side mapping only. Do not migrate
every loop and conditional at once. The point is to prove that the new `map`
name carries a stable policy before many callers depend on it.

Review the call sites after the first slice. If the new code reads as a chain
of domain verbs, keep going. If it reads as a long stack of anonymous lambdas,
stop and name the transformations before widening the change. Functor should
make context handling fade into the background. It should not erase the business
language from the code.

Named refactorings from the refactoring family usually involved are Extract
Function for naming pure transformations, Replace Conditional with Polymorphism
when a context hierarchy currently switches on state, and Encapsulate Variable
or Encapsulate Collection when callers reach into wrapper internals. Use those
refactorings only where the existing code smell is present.

Refactoring out:

1. If there is one call site and the context policy is not shared, inline the
   map call into direct code.
2. If mapping functions return the same context, replace `map` chains with
   `flatMap` and remove nested wrappers.
3. If callers combine two or more independent contexts, move to Applicative or
   explicit combination functions.
4. If observability matters more than compactness, split a long map chain into
   named intermediate values with trace boundaries.
5. If the generic type class is causing type errors, retain concrete `map`
   methods and remove the generic interface first.
6. Delete law tests only after the operation is gone or renamed. If a method
   remains named `map`, it must keep the law tests.

Removal is often the right move in performance-sensitive code. A tight loop may
need manual allocation control, early exits, or vectorized operations that a
generic map interface hides. That does not make Functor wrong in the rest of the
system. It means this site has a force that beats the abstraction. Leave a
short local comment if the manual loop looks like code that future maintainers
may be tempted to "clean up" back into `map`.

## 15. Testing and verification

This dimension is engineering judgement.

The smallest useful tests are law tests. For a context `F`, test identity:
`fa.map(x => x)` equals `fa`. Test composition: `fa.map(f).map(g)` equals
`fa.map(x => g(f(x)))`. Use generated values where the language test framework
supports them, because hand-picked values tend to miss empty, failed, and
metadata-heavy cases.

Test context preservation separately from transformation correctness. For
`Option`, verify that absence remains absent and presence transforms once. For
`Result`, verify that errors pass through and success transforms once. For
lists, verify order and length. For lazy streams, verify that the mapper is not
run before consumption when laziness is part of the API contract. Java's
`Stream.map` is documented as an intermediate operation, so stream tests should
include a terminal operation before expecting the mapper to run
(https://docs.oracle.com/javase/8/docs/api/java/util/stream/Stream.html,
verified 2026-08-02).

Test doubles are usually unnecessary for the mapper itself because it should be
pure. If a mapper needs a mock, fake clock, fake service, or fake repository,
that is a signal that `map` may be carrying effectful work. Move that work to a
different layer or use an effect-aware abstraction.

Equality deserves attention. Law tests need an equality relation for `F<A>`.
For wrappers with metadata, define whether metadata participates in equality.
If production equality ignores trace ids but tests compare them, law tests will
fail for the wrong reason. If production equality includes timestamps updated by
`map`, the identity law should fail, and the design should be changed.

Test thrown exceptions according to language norms. Java `Optional.map`
documents null handling for the result of the mapper and throws
`NullPointerException` when the mapper itself is null
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Optional.html,
verified 2026-08-02). Swift `Optional.map` can work with throwing closures in
the current Apple documentation
(https://developer.apple.com/documentation/swift/optional/map%28_%3A%29,
verified 2026-08-02). Those are API facts, not general Functor laws. A project
wrapper should document its own exception or null policy and test it beside the
law tests.

Verification should include negative tests for mapper execution. For `None`,
`Err`, or an empty collection, the mapper should not run. Use a counting mapper
in tests to prove that absence and failure bypass the transform. For a list or
stream with three values, prove the mapper runs exactly three times when the
context is eager. For lazy contexts, prove the mapper runs at consumption time,
not construction time, if laziness is promised.

## 16. Observability signals

This dimension is engineering judgement.

Healthy Functor use is often invisible because the operation is local and pure.
That is fine for small contexts. Add observability only where mapping occurs in
a pipeline that affects latency, memory, or data policy.

Useful signals:

- Stage name for each nontrivial transformation in a long pipeline.
- Count of input and output elements for collection and stream maps.
- Count of skipped transformations for absent or failed contexts.
- Duration of expensive mapping stages.
- Allocation size or output size when mapping large collections.
- Error classification when a mapper can throw in a language that permits it.
- Redaction status when mapping sensitive records into display, log, or export
  models.

A healthy dashboard for mapped collection pipelines shows stable input-output
ratios, bounded stage duration, and no unexplained growth in output size. A
failing dashboard shows a sudden rise in mapper exceptions, a stage that
dominates request time, output cardinality changes where `map` was expected to
preserve shape, or sensitive-field redaction failures after a model transform.

Trace naming matters. A span called `map` is too vague. A span called
`priceQuote.toDisplayMoney` or `claim.parseSubmittedAmount` tells the operator
what business transform ran while still keeping the code functional.

## 17. Security and privacy implications

This dimension is engineering judgement.

Functor is silent on authorization, authentication, encryption, and retention.
It neither grants access nor proves data is safe. Its security value is local:
context preservation can keep absence, failure, or validation state from being
discarded by casual code. Its risk is also local: mapping makes it easy to copy
data into another shape, including shapes with different retention or logging
rules.

Security concerns to check:

- A mapper must not turn a failed authorization result into a success-shaped
  value by mapping the wrong side of a result.
- Mapping from internal models to log or audit models must redact before the
  value enters a long-lived context.
- Mapping over a collection of records should not accidentally include fields
  that the target audience may not see.
- Lazy maps can execute later under a different request or tenant context if
  the pipeline escapes its intended scope.
- Exceptions thrown inside mappers may carry raw input values in messages.
- Metrics around mapping stages must avoid high-cardinality labels that contain
  user data.

Privacy review should treat each mapping function as a data transformation. The
outer Functor law does not say the new `B` is safer than the old `A`. It only
says the context shape was preserved.

Access-control review should focus on which side is mapped. In a right-biased
result, success mapping should not alter the error or denial side. In an
authorization pipeline, that distinction is more than style. A mapper that
turns `Denied` into display text is fine if the result remains denied. A mapper
that converts a denied result into a success value has crossed from Functor into
policy rewriting.

Retention review should focus on lifetime changes. Mapping a short-lived
request record into a cached view model may keep fields alive longer than the
source object. Mapping a raw payment token into a display string may be safe if
the display string is masked, unsafe if it preserves the token. The Functor
interface will not warn about that. The mapper is where the data classification
change occurs.

## 18. References

- Samuel Eilenberg and Saunders Mac Lane, "General Theory of Natural
  Equivalences", *Transactions of the American Mathematical Society*, volume
  58, 1945.
- Saunders Mac Lane, *Categories for the Working Mathematician*, second
  edition, Springer, 1998, chapter I, section 3.
- Simon Marlow, editor, *Haskell 2010 Language Report*, section 6.3.5, Functor
  class, https://www.haskell.org/onlinereport/haskell2010/, verified
  2026-08-02.
- GHC `base-4.18.0.0`, `Data.Functor`, https://downloads.haskell.org/~ghc/9.6.1/docs/libraries/base-4.18.0.0/Data-Functor.html,
  verified 2026-08-02.
- Typelevel Cats API, `cats.Functor`,
  https://typelevel.org/cats/api/cats/Functor.html, verified 2026-08-02.
- fp-ts API, `Functor.ts`,
  https://gcanti.github.io/fp-ts/modules/Functor.ts.html, verified
  2026-08-02.
- Oracle, Java SE 21 API, `java.util.Optional`,
  https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Optional.html,
  verified 2026-08-02.
- Oracle, Java SE 8 API, `java.util.stream.Stream`,
  https://docs.oracle.com/javase/8/docs/api/java/util/stream/Stream.html,
  verified 2026-08-02.
- Apple Developer Documentation, Swift `Optional.map`,
  https://developer.apple.com/documentation/swift/optional/map%28_%3A%29,
  verified 2026-08-02.
- Rust standard library, `std::option`,
  https://doc.rust-lang.org/stable/std/option/index.html, verified
  2026-08-02.
- Rust standard library, `Option<T>` methods,
  https://doc.rust-lang.org/stable/std/option/enum.Option.html, verified
  2026-08-02.

## Code examples

The examples are intentionally small and concrete. They model `map` for a
domain wrapper, then exercise identity and composition.

```python
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")


@dataclass(frozen=True)
class Box(Generic[A]):
    value: A
    label: str

    def map(self, f: Callable[[A], B]) -> "Box[B]":
        return Box(f(self.value), self.label)


def compose(g: Callable[[B], C], f: Callable[[A], B]) -> Callable[[A], C]:
    return lambda a: g(f(a))


box = Box(20, "invoice")
assert box.map(lambda x: x) == box
assert box.map(lambda x: x + 1).map(str) == box.map(compose(str, lambda x: x + 1))
print(box.map(lambda cents: f"${cents / 100:.2f}"))
```

```swift
import Foundation

struct Box<Value: Equatable>: Equatable {
    let value: Value
    let label: String

    func map<Next: Equatable>(_ f: (Value) -> Next) -> Box<Next> {
        Box<Next>(value: f(value), label: label)
    }
}

func compose<A, B, C>(_ g: @escaping (B) -> C, _ f: @escaping (A) -> B) -> (A) -> C {
    { a in g(f(a)) }
}

let box = Box(value: 20, label: "invoice")
let inc: (Int) -> Int = { $0 + 1 }
let show: (Int) -> String = { String($0) }

precondition(box.map { $0 } == box)
precondition(box.map(inc).map(show) == box.map(compose(show, inc)))
print(box.map { cents in String(format: "$%.2f", Double(cents) / 100) })
```

```go
package main

import "fmt"

type Box[A any] struct {
	Value A
	Label string
}

func Map[A, B any](box Box[A], f func(A) B) Box[B] {
	return Box[B]{Value: f(box.Value), Label: box.Label}
}

func Compose[A, B, C any](g func(B) C, f func(A) B) func(A) C {
	return func(a A) C { return g(f(a)) }
}

func main() {
	box := Box[int]{Value: 20, Label: "invoice"}
	identity := func(x int) int { return x }
	inc := func(x int) int { return x + 1 }
	show := func(x int) string { return fmt.Sprint(x) }

	if Map(box, identity) != box {
		panic("identity law failed")
	}
	left := Map(Map(box, inc), show)
	right := Map(box, Compose(show, inc))
	if left != right {
		panic("composition law failed")
	}
	fmt.Println(Map(box, func(cents int) string {
		return fmt.Sprintf("$%.2f", float64(cents)/100)
	}))
}
```

```rust
#[derive(Debug, PartialEq, Eq)]
struct Boxed<T> {
    value: T,
    label: &'static str,
}

impl<T> Boxed<T> {
    fn map<U, F>(self, f: F) -> Boxed<U>
    where
        F: FnOnce(T) -> U,
    {
        Boxed {
            value: f(self.value),
            label: self.label,
        }
    }
}

fn main() {
    let box1 = Boxed {
        value: 20,
        label: "invoice",
    };
    assert_eq!(box1.map(|x| x), Boxed {
        value: 20,
        label: "invoice",
    });

    let left = Boxed {
        value: 20,
        label: "invoice",
    }
    .map(|x| x + 1)
    .map(|x| x.to_string());
    let right = Boxed {
        value: 20,
        label: "invoice",
    }
    .map(|x| (x + 1).to_string());
    assert_eq!(left, right);
    println!("{:?}", right);
}
```

I ran the Python, Swift, Go, and Rust samples locally with `python3`, `swiftc`,
`go run`, and `rustc`. Java citations are still used for production examples,
but the Java compiler was not usable in this sandbox because no Java runtime was
available.
