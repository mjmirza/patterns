---
name: Applicative
slug: applicative
family: 16-functional
category: Functional
aliases: [Applicative Functor, Idiom, Apply With Pure, Monoidal Functor]
first_described: "McBride and Paterson 2008"
maturity: canonical
related: [functor, monad, traverse, validation, parser-combinator, free-applicative]
incompatible_with: [dependent-sequencing, hidden-side-effects, unordered-error-reporting]
verified: 2026-08-02
---

# Applicative

## 1. Name, aliases, and lineage

The canonical software name is Applicative. Haskell exposes the pattern as the
`Applicative` type class in `Control.Applicative`, with `pure`, application
through `<*>`, and derived helpers such as `liftA2` and `liftA3`
(https://hackage.haskell.org/package/base/docs/Control-Applicative.html,
verified 2026-08-02). The Hackage page describes it as a structure between
Functor and Monad, and points readers to Conor McBride and Ross Paterson's
paper, "Applicative Programming with Effects", *Journal of Functional
Programming*, volume 18, issue 1, 2008, pages 1 to 13
(https://www.staff.city.ac.uk/~ross/papers/Applicative.html, verified
2026-08-02).

The main aliases are Applicative Functor and Idiom. McBride and Paterson used
"idiom" for a programming notation around the same abstraction, then the
Haskell ecosystem standardized on `Applicative`. The category-theory lineage is
usually described as strong lax monoidal functor, a phrase used in both the
Haskell `Control.Applicative` documentation and fp-ts `Apply` documentation
(https://hackage.haskell.org/package/base/docs/Control-Applicative.html,
verified 2026-08-02; https://gcanti.github.io/fp-ts/modules/Apply.ts.html,
verified 2026-08-02). That mathematical phrase matters because it points at
the shape of the operation: independent contextual values can be combined while
the outer context decides how effects, absence, failure, or multiplicity are
merged.

The TypeScript fp-ts library splits the idea into `Apply`, which has `ap`, and
`Applicative`, which adds `of` as the pure injection operation
(https://gcanti.github.io/fp-ts/modules/Apply.ts.html, verified 2026-08-02).
Scala Cats presents `Applicative` as an extension of `Functor` with `ap` and
`pure`, and also explains the equivalent `product` plus `map` formulation
(https://typelevel.org/cats/typeclasses/applicative.html, verified
2026-08-02). Elm does not usually expose a type class named Applicative, but
its `Json.Decode.map2`, `map3`, and related decoder combinators use the same
fixed-shape combination pattern for independent decoders
(https://guide.elm-lang.org/effects/json, verified 2026-08-02).

The name is sometimes confused with the word "application" in object-oriented
frameworks. This entry is not about application services, application layers,
or a program entry point. It is about lifting a multi-argument pure function
over independent values that already live in the same computational context.

## 2. Problem and context

A program often has several values that are not plain values. A configuration
field may be missing. A parsed form field may be invalid. A remote call may
complete later. A decoder may fail at a path inside a JSON object. A list may
represent many possible answers. The program still wants to call an ordinary
constructor or domain function with several arguments. The problem is how to
combine `F<A>`, `F<B>`, and `F<C>` into `F<D>` when the pure function has type
`A -> B -> C -> D`.

Functor handles one contextual value. It can turn `F<A>` into `F<B>` by mapping
`A -> B` over the value. Once the function needs two independent arguments,
Functor runs out of power. Mapping the first argument gives `F<B -> C -> D>`,
which is a contextual function, not a result. Applicative supplies the missing
operation. It can apply a contextual function to a contextual argument, or in
the equivalent product formulation, combine two contextual values and then map
over the pair.

The context that makes Applicative useful has a sharp boundary: the effects are
independent. The second validation does not need the successful result of the
first validation. The password decoder does not need the decoded username. The
three configuration reads can be described before any one of them succeeds. In
that setting, Applicative keeps the domain constructor visible while letting the
context decide how failures, scheduling, or multiplicity combine.

Without the pattern, the code usually grows one of three shapes. The first is a
deep nest of callbacks or conditionals, one unwrap per field. That form hides
the constructor call and makes error accumulation hard. The second is a custom
combiner per arity, such as `combineUserNameAndPasswordAndAge`, which repeats
the same context rules under domain names. The third is a monadic chain, which
is more power than the problem needs and often commits the code to fail-fast
sequencing. Cats documents this distinction with `Validated`: a
for-comprehension uses `flatMap`, while `Validated` is an Applicative used when
the goal is to collect all validation errors rather than stop at the first one
(https://typelevel.org/cats/datatypes/validated.html, verified 2026-08-02).

The pattern's promise is not that effects vanish. The promise is that their
shape is static. A reader can see which independent computations are required
before looking at their results. That makes Applicative especially useful for
form validation, command-line option parsing, JSON decoding, static analysis of
requests, batched reads, and traversals where the whole structure is known up
front.

A practical example is request construction. A checkout request may need a
customer id, a shipping address, a payment token, and a cart snapshot. Each
piece can be parsed or validated on its own. The domain constructor should not
care whether the data came from JSON, command-line flags, database columns, or a
test fixture. Applicative lets the field readers stay independent and then
apply the constructor once all required pieces have been interpreted by the
same context. If the context is validation, every missing or malformed field can
be reported together. If the context is a decoder, path information can be
retained for each failed branch. If the context is an async task, the same
shape can describe several independent reads before the result is assembled.

The same framing applies to feature flags, environment variables, and command
line options. Each reader can be described separately, and the final settings
record can be assembled by a plain constructor after the context has handled
missing values and parse errors.

Another useful case is static capability planning. A monadic program can choose
the next request after seeing the previous result, which is powerful but hard to
inspect ahead of time. An Applicative program has a fixed request tree. That
tree can be counted, authorized, batched, displayed, or interpreted in another
environment before execution. This is why Applicative appears in parser,
decoder, validation, traversal, and free Applicative designs. The fixed shape
is the feature. It is also the limit.

## 3. Forces

This dimension is engineering judgement, except where a named API or law is
cited.

- **Coupling.** Favoured. Domain constructors stay plain functions. They do not
  import optional, decoder, validation, or future APIs.
- **Consistency.** Favoured. A lawful instance gives one rule for combining
  contextual values. Haskell documents identity, composition, homomorphism, and
  interchange laws for `Applicative`
  (https://hackage.haskell.org/package/base/docs/Control-Applicative.html,
  verified 2026-08-02).
- **Latency.** Mixed. Applicative can expose independent effects that a runtime
  or library may run in parallel, but a given instance may still choose
  left-to-right sequencing. The abstraction does not by itself promise
  concurrency.
- **Operability.** Favoured when the static shape is named and traced. Sacrificed
  when a long `mapN` or `<*>` expression is logged as one opaque step.
- **Cost.** Favoured for repeated validation or parsing code because context
  handling moves into a reusable instance. Sacrificed when teams add a type
  class layer for one local constructor call.
- **Team topology.** Favoured when platform teams own common contexts, such as
  validation, decoding, async tasks, or configuration reads, while product teams
  own pure domain assembly functions.
- **Cognitive load.** Sacrificed for teams unfamiliar with `pure`, `ap`, and
  currying. Favoured once the vocabulary is shared, because many wrappers obey
  the same composition rule.
- **Security and privacy.** Mixed. Applicative validation can collect all input
  errors for a user-facing response, but careless accumulation can also retain
  sensitive rejected values longer than fail-fast code would.

Applicative favours static composition over dependent sequencing. The price is
that the next computation cannot choose its shape from the previous successful
value. If that dependency is real, Monad is the honest abstraction.

There is also a force around API surface. A library can expose `ap` and `pure`
only, which is small but can feel alien. It can expose `map2` through `map22`,
which reads well but creates a broad API. It can expose tuple syntax, which
keeps application code compact but may produce errors that mention tuple
machinery rather than domain names. Engineering judgement: application teams
should prefer the most boring spelling their language already accepts. Haskell
teams expect `<*>`. Scala Cats teams expect `mapN`. Elm teams expect decoder
`mapN` helpers. Python teams often do better with concrete `combine2` and
`combine3` functions unless the codebase already carries higher-kinded
vocabulary.

Another force is explainability in code review. Applicative code often looks
like a declarative list of ingredients. That is helpful when the ingredients
are peers, such as five fields of one form. It becomes misleading when one item
is a gate and the others are consequences of passing that gate. Engineering
judgement: the review question should be "could these branches be planned
together?" rather than "can I make the types line up?" The type signature can
permit an Applicative expression even when the business process is staged.

## 4. Applicability and non-applicability

Reach for Applicative when these conditions hold.

- You have two or more independent contextual values and a pure function that
  combines their inside values.
- The whole computation graph can be described before any branch result is
  inspected.
- You want to collect multiple validation errors, decode several fields, or
  combine several configuration reads under one context policy.
- You want reusable traversal logic. Cats shows `traverse` generalized from
  `Option` and `Either` by delegating construction of the empty result to
  `Applicative.pure` and combination to `map2`
  (https://typelevel.org/cats/typeclasses/applicative.html, verified
  2026-08-02).
- The library already has an Applicative vocabulary, such as Haskell
  `Control.Applicative`, Cats `Applicative`, fp-ts `Apply` and `Applicative`,
  ZIO Prelude `Validation.validateWith`, or Elm decoder `mapN` functions
  (https://hackage.haskell.org/package/base/docs/Control-Applicative.html,
  verified 2026-08-02; https://typelevel.org/cats/typeclasses/applicative.html,
  verified 2026-08-02; https://gcanti.github.io/fp-ts/modules/Apply.ts.html,
  verified 2026-08-02; https://zio.github.io/zio-prelude/docs/functionalabstractions/parameterizedtypes/foreach,
  verified 2026-08-02; https://guide.elm-lang.org/effects/json, verified
  2026-08-02).

Do not reach for Applicative in these cases.

- **Later steps depend on earlier values.** Use Monad, `flatMap`, `andThen`, or
  explicit branching when the second query needs an id returned by the first
  query.
- **You need early exit for resource control.** Error accumulation may keep
  validating fields after one field proves the request cannot proceed. Use
  fail-fast code when continued work is harmful or expensive.
- **The effects must run in a specific data-dependent order.** Applicative laws
  allow reassociation. An instance may still sequence, but clients should not
  encode business ordering by depending on that detail unless the API documents
  it.
- **The team does not have a shared vocabulary for the abstraction.** Engineering
  judgement: in a small non-functional codebase, a named `combine3` helper may
  be clearer than introducing `pure` and `ap`.
- **The arity is unbounded and heterogeneous.** Fixed `mapN` helpers work well
  up to a practical limit. Past that, a record builder, decoder DSL, or schema
  system usually reads better.
- **The context lacks a lawful pure value.** Cats documents `Apply` as the
  weaker abstraction for types such as `Map[K, *]`, where pairing existing keys
  is meaningful but inventing a key for `pure` is not
  (https://typelevel.org/cats/typeclasses/applicative.html, verified
  2026-08-02).
- **The mapper performs hidden side effects.** Applicative reasoning assumes the
  function being lifted can be treated as a value. Logging, mutation, time, and
  network calls inside the function make law-based refactoring unreliable.

## 5. Structure

Applicative has five participants.

- **Context type constructor.** A type shape such as `Option`, `Result<E, *>`,
  `Validation<E, *>`, `Decoder`, `Task`, `List`, or `ZipList`. It must also be
  a Functor.
- **Pure injector.** An operation often named `pure`, `of`, `succeed`, or
  `return` in older APIs. It embeds a plain value without adding failure,
  absence, or extra effects.
- **Applicative application.** An operation often named `ap` or `<*>`. It
  applies `F<A -> B>` to `F<A>` and returns `F<B>`.
- **Product or mapN helper.** A derived operation that combines `F<A>` and
  `F<B>` into `F<(A, B)>`, or applies a multi-argument function to several
  contextual values. Cats presents `product` plus `map` as an equivalent view
  of `Applicative` (https://typelevel.org/cats/typeclasses/applicative.html,
  verified 2026-08-02).
- **Pure combining function.** The domain function, constructor, or record
  builder that receives ordinary values after the context has supplied them.

The dependencies point in a useful direction. Domain code depends on ordinary
functions and records. Context-specific code owns absence, error, async,
collection, or decoding semantics. Applicative is the adapter between those two
parts.

## 6. ASCII structure diagram

```text
       pure value                  contextual values
          |                        F<A>        F<B>
          v                         |           |
   +---------------+                 |           |
   | pure/of       |                 |           |
   | A -> F<A>     |                 |           |
   +-------+-------+                 |           |
           |                         |           |
           v                         v           v
   +----------------------------------------------------+
   |              Applicative instance F                |
   |----------------------------------------------------|
   | ap:      F<A -> B> -> F<A> -> F<B>                 |
   | product: F<A> -> F<B> -> F<(A, B)>                 |
   | mapN:    (A -> B -> C) -> F<A> -> F<B> -> F<C>     |
   +---------------------------+------------------------+
                               |
                               v
                     +-------------------+
                     |   F<Result>       |
                     | same outer policy |
                     +-------------------+

   The combining function is plain. The instance owns context policy.
```

## 7. Dynamics

At runtime the client supplies contextual inputs and a pure function. The
Applicative instance decides how each input context contributes to the final
context.

```text
Client        F<A> branch       F<B> branch       Applicative       F<C>
  |                |                 |                  |             |
  |-- build fa --->|                 |                  |             |
  |-- build fb --------------------->|                  |             |
  |-- provide pure function f ------------------------->|             |
  |                |                 |                  |             |
  |-- mapN(f, fa, fb) --------------------------------->|             |
  |                |                 |-- inspect fb ---->|             |
  |                |-- inspect fa --------------------->|             |
  |                |                 |                  |             |
  |                |                 |                  |-- if both
  |                |                 |                  |   succeed,
  |                |                 |                  |   emit F<f(a,b)>
  |                |                 |                  |             |
  |                |                 |                  |-- if context
  |                |                 |                  |   reports absence,
  |                |                 |                  |   failure, or many
  |                |                 |                  |   results, combine
  |                |                 |                  |   by F's rules
  |<----------------------------------------------------|             |
```

The same diagram covers several policies. `Option` returns absence if any input
is absent. A fail-fast `Either` returns one error. An accumulating `Validation`
combines errors through a semigroup. A list Applicative may produce a Cartesian
product, while `ZipList` combines by position. Haskell documents separate
instances for list and `ZipList` in `Control.Applicative`
(https://hackage.haskell.org/package/base/docs/Control-Applicative.html,
verified 2026-08-02).

## 8. Implementation variants

**`pure` plus `ap`.** This is the canonical Haskell and Cats shape. Define
`pure : A -> F<A>` and `ap : F<A -> B> -> F<A> -> F<B>`. It is compact and
law-friendly, but reads strangely in languages without currying.

**`map` plus `product`.** This variant defines `product : F<A> -> F<B> ->
F<(A, B)>`, then maps a combining function over the pair. Cats documents this
as an equivalent formulation (https://typelevel.org/cats/typeclasses/applicative.html,
verified 2026-08-02). It reads well in strict object-oriented languages.

**Fixed arity `mapN`.** Many practical APIs expose `map2`, `map3`, or tuple
syntax. Elm JSON decoders use this style to combine field decoders into records
(https://guide.elm-lang.org/effects/json, verified 2026-08-02). It is easy to
read, but needs one helper per arity or a generated tuple syntax layer.

**Validation applicative.** Each field validation returns either a value or one
or more errors. The Applicative instance calls all independent validations and
combines failures. Cats `Validated` and ZIO Prelude `Validation` both document
this error-accumulating use
(https://typelevel.org/cats/datatypes/validated.html, verified 2026-08-02;
https://zio.github.io/zio-prelude/docs/functionalabstractions/parameterizedtypes/foreach,
verified 2026-08-02).

**Parser or decoder applicative.** A parser grammar or decoder schema is built
from small independent pieces. The Haskell `Control.Applicative` documentation
states that the interface is sufficient for context-free parsing and
`Traversable` (https://hackage.haskell.org/package/base/docs/Control-Applicative.html,
verified 2026-08-02). Engineering judgement: parser teams should switch to
Monad only where later grammar choices truly depend on earlier parsed values.

**Parallel applicative.** Some effect libraries provide an Applicative whose
combination can run independent effects at the same time. Cats documents
Parallel variants from its Applicative page
(https://typelevel.org/cats/typeclasses/applicative.html, verified
2026-08-02). The trade-off is that logs, timing, and cancellation become part of
the instance contract and must be documented.

**Free applicative.** A free Applicative represents a static request tree before
interpretation. This supports analysis, batching, permission checks, or
optimization before execution. McBride and Paterson's paper motivates the
static nature of Applicative by contrasting it with Monad's binding power
(https://www.staff.city.ac.uk/~ross/papers/Applicative.html, verified
2026-08-02). Engineering judgement: this form is valuable for DSLs, but too
heavy for ordinary validation code.

**Builder syntax over Applicative.** Some teams wrap Applicative in a builder
DSL so domain authors do not see `ap` directly. A validation builder might say
`field("email").required().email()` and later assemble a record from named
fields. The underlying implementation can still be Applicative, but the public
API carries domain labels, redaction flags, and error codes. The trade-off is
that the builder may hide the law-bearing core, so maintainers need tests at
both levels.

**Schema-derived applicative.** A schema library can derive field readers and
then use Applicative composition to build values. This is common in decoders and
form libraries. The benefit is consistency across many record types. The cost
is that schema metadata can become a second source of truth if the language's
type checker cannot keep it synchronized with the domain type.

**Accumulating writer applicative.** A context such as `Const` or a writer-like
pair can ignore the result value and accumulate annotations. Haskell lists a
`Const` Applicative instance when its stored type has a `Monoid`
(https://hackage.haskell.org/package/base/docs/Control-Applicative.html,
verified 2026-08-02). This variant is useful for collecting required fields,
declared permissions, or documentation from a static program. It is a poor fit
when later metadata depends on earlier runtime values.

## 9. Known production uses

- **Haskell `base`, `Control.Applicative`.** The Haskell base library ships the
  `Applicative` class, laws, standard instances such as `Maybe`, `Either`,
  `IO`, list, `ZipList`, and helpers including `liftA2` and `liftA3`
  (https://hackage.haskell.org/package/base/docs/Control-Applicative.html,
  verified 2026-08-02).
- **Scala Cats.** Cats exposes `Applicative[F[_]]`, documents `ap`, `pure`,
  `product`, `mapN`, `tupleN`, composition through `Nested`, and syntax under
  `cats.syntax.all._` (https://typelevel.org/cats/typeclasses/applicative.html,
  verified 2026-08-02).
- **Cats `Validated`.** Cats documents `Validated` as an Applicative Functor
  used when form validation should accumulate errors, with tuple `mapN` syntax
  building `RegistrationData` from independent field validations
  (https://typelevel.org/cats/datatypes/validated.html, verified 2026-08-02).
- **fp-ts.** fp-ts exposes `Apply` and `Applicative` modules in TypeScript. Its
  `Apply` documentation states that `ap` applies a function under a type
  constructor and that `Apply` can lift functions of two or more arguments over
  wrapped values (https://gcanti.github.io/fp-ts/modules/Apply.ts.html,
  verified 2026-08-02).
- **Elm JSON decoders.** The Elm guide shows `Json.Decode.map2` and `map4`
  combining independent field decoders into record constructors for `Person`
  and `Quote` values (https://guide.elm-lang.org/effects/json, verified
  2026-08-02).
- **ZIO Prelude `Validation`.** ZIO Prelude documents `Validation.validateWith`
  and `forEach` over `Validation` as a way to validate all values and return
  either fully validated data or a non-empty collection of errors
  (https://zio.github.io/zio-prelude/docs/functionalabstractions/parameterizedtypes/foreach,
  verified 2026-08-02).

These examples also show that production use does not require a language-level
type class. Haskell and Cats expose the abstraction directly. fp-ts simulates
higher-kinded types in TypeScript. Elm exposes fixed-arity combinators for
specific domains. ZIO Prelude exposes validation and traversal operations. The
common pattern is not a keyword. It is the reusable rule for lifting a pure
multi-argument function into a context that can combine independent inputs.

The examples also cover different failure policies. Haskell `Maybe` and many
`Either` instances are commonly used for absence or fail-fast errors. Cats
`Validated` and ZIO Prelude `Validation` are documented for accumulation of
multiple errors. Elm decoders combine field decoders while preserving decoder
semantics. fp-ts exposes the generic interface so application code can choose
which instance policy to import. This variety is why this entry treats
Applicative as a pattern rather than a single API shape.

## 10. Consequences

Positive consequences.

- Domain assembly stays direct. The constructor call remains visible instead of
  being spread across nested conditionals.
- Independent effects become explicit. Reviewers can tell that one field does
  not depend on another.
- Error accumulation becomes a library rule rather than a hand-written pattern
  in each form.
- The same traversal algorithm can target `Option`, `Either`, validation,
  async tasks, and decoders when each supplies an Applicative instance.
- Static descriptions can be inspected or optimized before interpretation in
  parser, decoder, and free Applicative designs.

Negative consequences.

- The abstraction is less familiar outside functional programming communities.
- Type errors can be hard to read when currying, higher-kinded types, or tuple
  syntax are involved.
- Applicative cannot express dependent sequencing. A later step cannot decide
  which contextual computation to build from an earlier successful value.
- Accumulating failures may perform work that fail-fast code would skip.
- Large `mapN` expressions can become wide, positional, and fragile when record
  fields are reordered.
- A generic Applicative interface can hide context-specific costs such as
  parallel scheduling, error retention, or Cartesian product growth.

The strongest long-term consequence is architectural. Once an Applicative layer
exists, teams tend to model more workflows as independent field graphs. That is
good for validation, decoding, and static request planning. It is bad when the
domain is a conversation with prior results. Engineering judgement: review
Applicative code by asking whether a business analyst could reorder the inputs
without changing the meaning. If yes, Applicative is probably earning its place.
If no, the code is smuggling dependency through an abstraction chosen for
independence.

## 11. Failure modes and misuse

This dimension is engineering judgement.

- **Symptom.** A validation endpoint reports several errors but also performs
  expensive external checks after the first local rejection. **Cause.** The team
  used an accumulating Applicative where early exit was part of the resource
  policy. **Fix.** Split cheap independent checks into Applicative validation
  and gate expensive dependent checks behind a fail-fast step.
- **Symptom.** Users see error messages in a confusing order, changing between
  releases. **Cause.** The Applicative instance accumulates errors through a
  collection with no stable order, or the code relies on unspecified parallel
  scheduling order. **Fix.** Accumulate into an ordered non-empty structure and
  sort display errors by field path.
- **Symptom.** A `mapN` call builds a record with swapped fields after a small
  refactor. **Cause.** Positional arguments grew past the point where review can
  track them. **Fix.** Use named-field builders, smaller nested records, or a
  decoder or validation DSL that labels each field.
- **Symptom.** A second query cannot use an id returned by the first query
  without awkward placeholders. **Cause.** Applicative was chosen for a
  dependent workflow. **Fix.** Use Monad or explicit branching for the dependent
  part, keeping Applicative only for independent subgroups.
- **Symptom.** A list combination unexpectedly returns many more rows than the
  inputs. **Cause.** The list Applicative is Cartesian product style, while the
  programmer expected zip-by-position behavior. **Fix.** Use a zip Applicative
  such as Haskell `ZipList`, or use an explicit zip operation when positional
  pairing is the rule.
- **Symptom.** Traces show one generic "validate" span with no field-level
  detail. **Cause.** The Applicative expression hid useful names inside a single
  combinator call. **Fix.** Add names to validation nodes or record field-path
  attributes as each branch is built.
- **Symptom.** Law tests fail after adding logging inside the combining
  function. **Cause.** The lifted function is no longer referentially
  transparent. **Fix.** Move effects into the context where the Applicative
  instance can define their order, or keep the combining function pure.

## 12. Trade-off matrix

| Force | Applicative | Functor | Monad | Arrow | Explicit conditionals |
|---|---|---|---|---|---|
| Independent multi-value composition | Strong | Weak | Strong but more power | Strong | Local only |
| Dependent sequencing | Weak | Weak | Strong | Medium | Strong |
| Error accumulation | Strong with validation instance | Weak | Usually fail-fast | Medium | Manual |
| Static analysis before execution | Strong | Medium | Weak | Strong | Weak |
| Cognitive load | Medium | Low | Medium to high | High | Low |
| Refactoring laws | Strong when lawful | Strong when lawful | Strong when lawful | Strong when known | Project-specific |
| Parallel opportunity | Strong when instance supports it | Low | Low to medium | Medium | Manual |
| Boilerplate | Low after library setup | Low | Low after library setup | Medium | High across many fields |
| Operational transparency | Medium | Medium | Medium | Medium | High in small code |

## 13. Related and incompatible patterns

Functor is the parent abstraction. Every Applicative is a Functor, and Haskell
states that `fmap f x` follows from `pure f <*> x`
(https://hackage.haskell.org/package/base/docs/Control-Applicative.html,
verified 2026-08-02). Use Functor when there is one contextual value and
Applicative when there are several independent contextual values.

Monad is the stronger sibling. Every lawful Monad can supply an Applicative
instance by using monadic application, and Haskell documents that a Monad
instance should satisfy `pure = return` and `<*> = ap`
(https://hackage.haskell.org/package/base/docs/Control-Applicative.html,
verified 2026-08-02). Use Monad when later computation depends on earlier
values.

Traverse is a consumer of Applicative. It turns a structure of contextual
results into a contextual structure of results. Cats presents traversal by
generalizing `Option` and `Either` implementations through `Applicative`
(https://typelevel.org/cats/typeclasses/applicative.html, verified
2026-08-02).

Parser Combinator often composes with Applicative. A static grammar fragment
that combines independent parsers is a good Applicative fit. A parser whose
next grammar depends on a parsed length or tag needs Monad or a dependent
parser API.

Validation is a common concrete pattern built with Applicative. Cats
`Validated` and ZIO Prelude `Validation` demonstrate the design where errors
combine while successes feed a pure constructor
(https://typelevel.org/cats/datatypes/validated.html, verified 2026-08-02;
https://zio.github.io/zio-prelude/docs/functionalabstractions/parameterizedtypes/foreach,
verified 2026-08-02).

Free Applicative composes with interpreter and command object designs. The
program is a data structure, then interpreters turn it into execution, docs,
batch requests, or permission checks. It conflicts with designs that require
runtime branching after each result.

Dependency Injection can replace Applicative when the problem is assembling
services, not combining contextual values. Engineering judgement: if the
values are long-lived collaborators, use DI. If the values are per-request
results under an effect or validation context, Applicative is the better fit.

## 14. Refactoring path in and out

To introduce Applicative, start with one repeated independent combination. Do
not begin with a global type class. Pick code that unwraps two or three values,
checks the same context policy, then calls a pure constructor.

1. Extract the constructor or combining expression into a pure function.
2. Name each contextual input before combining it. For validation, each field
   check should have its own value and field label.
3. Add a local `map2` or `map3` helper for the existing context. Keep the helper
   concrete until a second context needs the same shape.
4. Replace the manual unwrap sequence with `mapN` or `pure(function).ap(a).ap(b)`.
5. Add tests for all-success, one-failure, and multiple-failure cases.
6. If a second context repeats the same shape, extract an interface for
   `pure`, `map`, and `ap` or `product`.
7. Document the instance policy: fail-fast, accumulating, zip, Cartesian,
   sequential, or parallel.

The named refactoring is Extract Function for the pure combining logic, followed
by Replace Conditional with Polymorphism only if separate context instances
begin to multiply. In most TypeScript, Python, and Go code, a concrete helper
is the right first refactoring.

To remove Applicative, reverse the path.

1. Find `mapN`, `ap`, or tuple syntax calls with poor readability or real
   dependency between steps.
2. Inline the pure constructor call into explicit control flow.
3. Preserve the old instance policy in tests before changing behaviour.
4. Replace accumulating validation with fail-fast validation only after product
   requirements accept the response change.
5. Delete generic type class plumbing when only one concrete context remains.

## 15. Testing and verification

Testing has three layers.

First, test the pure combining function without the context. A record
constructor, request builder, or domain calculation should accept plain values
and return a plain result. These tests are small and catch field order mistakes
that Applicative syntax can hide.

Second, test the concrete instance policy. For `Option`, cover all present and
each absent input. For fail-fast `Result`, assert which error wins. For
accumulating validation, assert that multiple independent failures appear in a
stable order. For list or zip variants, test cardinality because Cartesian and
zip semantics differ sharply.

Third, test the laws for reusable instances. Haskell publishes the identity,
composition, homomorphism, and interchange laws for `Applicative`
(https://hackage.haskell.org/package/base/docs/Control-Applicative.html,
verified 2026-08-02). In property-based tests, generate small contextual values
and small functions, then compare both sides of each law. In languages where
function equality is not observable, test with a finite set of input values or
use the product formulation laws documented by Cats
(https://typelevel.org/cats/typeclasses/applicative.html, verified
2026-08-02).

Test doubles need care. A mock with ordered expectations may make Applicative
look sequential when the abstraction only promises independent combination. Use
fake contexts that record requested field names, or deterministic validation
values, rather than mocks that assert call order unless the instance documents
that order.

For application-level validation, build a golden set of bad inputs. Include
empty input, one invalid field, two invalid fields, wrong types, unknown fields,
and maliciously large fields. Assert both the machine-readable error codes and
their paths. Do not assert complete human message text unless message stability
is a product contract. This keeps the Applicative policy tested while leaving
copy edits cheap.

Field-order tests deserve their own mention. A positional `mapN` expression can
compile while passing `lastName` into the `firstName` slot if both fields have
the same type. Use test data where same-typed fields have visibly different
values. In strongly typed languages, introduce small domain wrappers for fields
that are often swapped. In dynamic languages, prefer named dictionaries or
dataclasses at the boundary before applying the final constructor.

For async Applicative code, test cancellation and timeout behavior. A parallel
instance should define what happens when one branch fails quickly and another
branch is still running. A sequential instance should define whether branch
order is left-to-right, right-to-left, or unspecified. The tests should match
the documented instance policy, not a reader's guess from the syntax.

For parser and decoder code, test minimal valid input, maximal valid input,
missing-field cases, type mismatch cases, and nested-path failure cases.
Applicative composition can preserve a rich error tree, but only if each branch
attaches labels before combination. A test that expects `payment.card.number`
instead of a generic `number` failure catches that regression early.

## 16. Observability signals

This dimension is engineering judgement.

Log the shape, not every raw value. Useful fields include validation name,
field path, decoder path, branch count, error count, accumulated error codes,
and whether the instance was sequential or parallel. Avoid logging rejected
payloads by default.

Trace independent branches as children of one combining span when branch cost
matters. A healthy validation dashboard shows stable branch count, low error
rate for normal traffic, predictable field-level error distribution, and no
large gap between first and last branch completion. A failing instance shows
error count spikes, high branch latency, field names with sudden missing-value
rates, or Cartesian result sizes growing faster than input sizes.

Metrics to collect:

- `applicative_branches_total`, tagged by context and operation.
- `applicative_errors_total`, tagged by field or error code.
- `applicative_accumulated_error_count`, histogram.
- `applicative_result_cardinality`, for list, parser, or query-planning uses.
- `applicative_branch_duration`, for async or external validation branches.

For decoders, keep path information. Elm's JSON guide frames decoders as small
building blocks snapped together, including field decoders for nested JSON
(https://guide.elm-lang.org/effects/json, verified 2026-08-02). In production,
that same composition should preserve path context so operators can see whether
failures cluster at `author.age`, `payment.currency`, or `lineItems[3].sku`.

For validation, dashboards should separate user-correctable errors from system
errors. `email.invalid` and `age.too_low` are product signals. A field validator
timing out or failing to load a reference table is an operational signal. If
both travel through the same Applicative context, tag them before accumulation.
Otherwise the response layer and the incident dashboard will disagree about
severity.

Sampling policy matters. Accumulating validation can produce many branch
failures for a single request, so one noisy client can dominate logs. Count all
errors in metrics, but sample detailed event logs by request id or tenant id.
For privacy-sensitive systems, keep a denylist of fields that may never appear
in structured logs, even as rejected values.

For static request DSLs, record plan size before execution. The number of
branches, maximum fan-out, and estimated remote calls are often more useful
than a single success metric. A sudden rise in plan size after a feature flag
rollout can explain latency before downstream service dashboards show clear
pressure.

## 17. Security and privacy implications

This dimension is engineering judgement.

Applicative can reduce some risk by centralizing context policy. A validation
instance can make sure rejected inputs stay in typed error structures rather
than leaking through thrown exceptions. A decoder can preserve field paths
without logging full payloads. A static request description can be inspected for
authorization needs before execution.

It can also increase exposure. Error accumulation may retain several invalid
values in memory until the response is built. A user-facing response with all
validation errors may reveal rules that a security-sensitive endpoint would
rather keep coarse. Parallel applicative branches may perform checks after an
authorization failure if authorization is modeled as one independent branch
among many. That is the wrong boundary. Authorization gates should usually run
before broad independent validation or data fetching.

Privacy review should ask four questions. Which branch can observe personal
data? Which errors are returned to the caller? Which errors are logged? Does the
context combine data from fields with different retention rules? If those
answers differ by field, the Applicative helper needs field labels and redaction
metadata, not a bare list of strings.

Applicative is silent on cryptography, authentication, and transport security.
It is a composition pattern. The security work is in the context instance and
in the data each branch is allowed to keep.

The riskiest misuse is treating authorization as another independent field
check. If the user is not allowed to perform the operation, independent branches
should not fetch related private data in parallel merely so the final
Applicative result can contain all errors. Put authorization before the
Applicative graph, or split the graph so public validation runs first and
private enrichment runs only after access has been granted.

When errors are accumulated, redact at the branch boundary. A validation error
should carry a field code and a safe reason, not the raw rejected value, unless
the product explicitly needs the value echoed back. For example, returning
`password.too_short` is safer than returning the supplied password with a
message attached. Applicative makes it easy to gather many failures, so it must
also make it easy to gather them without gathering secrets.

## Code examples

TypeScript, Python, and Rust are used here because they show three practical
forms: optional application, accumulating validation, and zip-style
combination. All three samples were run locally with `node`, `python3`, and
`rustc`.

```typescript
type Option<T> = { tag: "some"; value: T } | { tag: "none" };

const some = <T>(value: T): Option<T> => ({ tag: "some", value });
const none = <T>(): Option<T> => ({ tag: "none" });

const ap = <A, B>(ff: Option<(a: A) => B>, fa: Option<A>): Option<B> =>
  ff.tag === "some" && fa.tag === "some" ? some(ff.value(fa.value)) : none();

const pure = some;

type User = { name: string; age: number };

const makeUser = (name: string) => (age: number): User => ({ name, age });
const userName = some("Ada");
const age = some(36);
const user = ap(ap(pure(makeUser), userName), age);

console.log(user);
```

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Valid:
    value: object


@dataclass(frozen=True)
class Invalid:
    errors: tuple[str, ...]


def valid(value):
    return Valid(value)


def invalid(error):
    return Invalid((error,))


def ap(ff, fa):
    if isinstance(ff, Valid) and isinstance(fa, Valid):
        return Valid(ff.value(fa.value))
    errors = ()
    if isinstance(ff, Invalid):
        errors += ff.errors
    if isinstance(fa, Invalid):
        errors += fa.errors
    return Invalid(errors)


def validate_name(value):
    return valid(value) if value else invalid("name.empty")


def validate_age(value):
    return valid(value) if value >= 18 else invalid("age.too_low")


make_user = lambda name: lambda age: {"name": name, "age": age}
result = ap(ap(valid(make_user), validate_name("")), validate_age(15))
print(result)
```

```rust
fn zip_apply<A, B, F>(fs: Vec<F>, xs: Vec<A>) -> Vec<B>
where
    F: Fn(A) -> B,
{
    fs.into_iter().zip(xs).map(|(f, x)| f(x)).collect()
}

fn add_one(x: i32) -> i32 {
    x + 1
}

fn double(x: i32) -> i32 {
    x * 2
}

fn main() {
    let functions: Vec<fn(i32) -> i32> = vec![add_one, double];
    let values = vec![10, 20, 30];
    let result = zip_apply(functions, values);
    println!("{:?}", result);
}
```

## 18. References

- Conor McBride and Ross Paterson, "Applicative Programming with Effects",
  *Journal of Functional Programming*, volume 18, issue 1, 2008, pages 1 to
  13. https://www.staff.city.ac.uk/~ross/papers/Applicative.html, verified
  2026-08-02.
- Haskell `base` library, `Control.Applicative`, version shown by Hackage as
  base 4.22.0.0 at fetch time.
  https://hackage.haskell.org/package/base/docs/Control-Applicative.html,
  verified 2026-08-02.
- fp-ts documentation, `Apply.ts`.
  https://gcanti.github.io/fp-ts/modules/Apply.ts.html, verified 2026-08-02.
- Typelevel Cats documentation, `Applicative`.
  https://typelevel.org/cats/typeclasses/applicative.html, verified
  2026-08-02.
- Typelevel Cats documentation, `Validated`.
  https://typelevel.org/cats/datatypes/validated.html, verified 2026-08-02.
- Elm Guide, JSON decoders.
  https://guide.elm-lang.org/effects/json, verified 2026-08-02.
- ZIO Prelude documentation, `ForEach` and `Validation`.
  https://zio.github.io/zio-prelude/docs/functionalabstractions/parameterizedtypes/foreach,
  verified 2026-08-02.
