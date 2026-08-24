---
name: Traversable
slug: traversable
family: 16-functional
category: Functional
aliases: [Traverse, Traversal, Sequence, ForEach]
first_described: "McBride and Paterson 2008"
maturity: canonical
related: [functor, foldable, applicative, monad, iterator, validation]
incompatible_with: [unordered-effects, shape-changing-transform, dependent-sequencing]
verified: 2026-08-02
---

# Traversable

## 1. Name, aliases, and lineage

The canonical software name is Traversable. In Haskell, `Data.Traversable`
defines `Traversable` as a class for data structures that can be traversed from
left to right while performing an action on each element. Its central operation
has the shape `traverse :: Applicative f => (a -> f b) -> t a -> f (t b)`,
with `sequenceA :: Applicative f => t (f a) -> f (t a)` as the close companion
(https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Data-Traversable.html,
verified 2026-08-02).

The pattern grew out of Conor McBride and Ross Paterson's work on applicative
programming. Their paper, "Applicative Programming with Effects", *Journal of
Functional Programming*, volume 18, issue 1, 2008, pages 1 to 13, introduced
applicative programming as a structure between Functor and Monad and is linked
from the Haskell `Control.Applicative` documentation
(https://hackage.haskell.org/package/base/docs/Control-Applicative.html,
verified 2026-08-02). The Haskell `Data.Traversable` module records copyright
for Conor McBride and Ross Paterson and connects Traversable with applicative
actions over data structures
(https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Data-Traversable.html,
verified 2026-08-02).

Jeremy Gibbons and Bruno C. d. S. Oliveira later made the pattern's design role
explicit in "The Essence of the Iterator Pattern", *Journal of Functional
Programming*, volume 19, issues 3 and 4, 2009, pages 377 to 402. The Oxford
publication page says the paper argues that applicative functors, and the
corresponding `traverse` operator in particular, capture the mapping and
accumulating aspects of iteration
(https://www.cs.ox.ac.uk/publications/publication1409-abstract.html, verified
2026-08-02).

Common aliases are **Traverse**, **traversal**, **sequence**, and **forEach**.
Scala Cats exposes the abstraction as `Traverse` and presents `traverse` plus
`sequence` as the core operations
(https://typelevel.org/cats/typeclasses/traverse.html, verified 2026-08-02).
fp-ts names the module `Traversable` and says `traverse` runs an action for
each element while accumulating effects, while `sequence` runs actions already
inside the structure
(https://gcanti.github.io/fp-ts/modules/Traversable.ts.html, verified
2026-08-02). ZIO Prelude uses the name `ForEach` for the same operational idea:
a parameterized type that contains zero or more values can run a function for
each value and collect the results back into the original collection type
(https://zio.github.io/zio-prelude/docs/functionalabstractions/parameterizedtypes/foreach,
verified 2026-08-02).

The name is easy to confuse with an object-oriented iterator or visitor. Those
patterns expose a way to visit elements. Traversable exposes a law-governed way
to visit elements with an Applicative effect and rebuild the same outer shape.
That "same shape" condition is the boundary. Iteration can consume a structure.
Traversal interprets each element and returns the interpreted structure inside
the effect.

## 2. Problem and context

A program has a structure of values and a function that validates, parses,
loads, checks, or annotates one value at a time. The function does not return a
plain value. It returns a context such as `Option<B>`, `Result<B, E>`,
`Promise<B>`, `Validation<Errors, B>`, or `IO<B>`. The program needs a result
for the whole structure, not a structure of small effects.

The shape of the problem is `t a` plus `a -> f b`. The desired result is
`f (t b)`. A list of raw user records and a function that validates one record
should become either a validated list of domain users or a validation failure.
A tree of file paths and a function that reads one file should become an effect
that returns the same tree shape with file contents. A form object containing
strings and a function that parses one field should become a parsed form inside
the error context. In each case, the structure is known before element effects
start, and every element can be treated through the same rule.

Without Traversable, code usually falls into one of four shapes. The first is a
manual loop that builds an output list and bails out or accumulates errors by
hand. The second is a nest of callbacks or `then` calls that turns a simple
collection operation into control-flow plumbing. The third is a `map` that
produces `List<Result<B, E>>` or `Tree<Promise<B>>`, followed by scattered code
that flips the layers. The fourth is a custom helper per data type and per
effect, such as `validateUsers`, `loadTree`, and `parseAddresses`, even though
the traversal policy is the same.

Traversable names the reusable middle. The data structure knows how to walk
itself and rebuild itself. The Applicative effect knows how to combine
independent effects. The element function knows the domain transformation. No
participant has to know the whole story. That separation is why the pattern is
more than a loop helper.

The context that makes Traversable the right pattern has three parts.

- The outer shape must be preserved. Mapping a list yields a list of the same
  length. Mapping a binary tree yields a binary tree with the same branches.
  Mapping `None` yields `None`. Traversable code may change element values, but
  it does not filter, sort, split, or append.
- The per-element effects are planned from the original structure. If the next
  element to visit or the next operation to run depends on a previous result,
  the code has moved into Monad territory.
- The effect has an Applicative way to combine independent work. That effect
  may short-circuit, collect errors, build a cross product, schedule work, or
  record state, but the combination policy belongs to the effect, not to the
  traversal loop.

The central move is often called flipping or turning a structure inside out.
`List<Option<A>>` becomes `Option<List<A>>`. `Tree<Result<A, E>>` becomes
`Result<Tree<A>, E>`. `List<Promise<A>>` becomes `Promise<List<A>>`. Cats shows
this with `sequence`, where a `List[Option[Int]]` becomes an `Option[List[Int]]`
(https://typelevel.org/cats/typeclasses/traverse.html, verified 2026-08-02).
fp-ts states the same compatibility between `traverse` and `sequence`
(https://gcanti.github.io/fp-ts/modules/Traversable.ts.html, verified
2026-08-02).

The laws matter because Traversable is used for refactoring and generic
programming. Haskell lists naturality, identity, and composition laws for
`traverse`, and parallel laws for `sequenceA`
(https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Data-Traversable.html,
verified 2026-08-02). In practice, those laws mean that a traversal cannot
secretly drop elements, duplicate elements, reorder effects outside the
documented order, or alter the shape based on the particular Applicative chosen.

Engineering judgement. In application code, the pattern earns its place when
the reader's real question is "what effect do we run for each element, and what
effect policy combines the answers?" If the reader's real question is "which
items survive?" or "which item comes next after this result?", Traversable is
the wrong name for the work.

## 3. Forces

This dimension is engineering judgement, except where a named API or law is
cited.

- **Coupling.** Favoured. The domain function works on one element. The
  structure owns walking and rebuilding. The effect owns failure, accumulation,
  scheduling, or nondeterminism.
- **Consistency.** Favoured. A lawful traversal gives one rule for `map`,
  `foldMap`, `traverse`, and `sequence`. fp-ts states compatibility between
  `traverse`, `sequence`, and the related `Foldable` behavior
  (https://gcanti.github.io/fp-ts/modules/Traversable.ts.html, verified
  2026-08-02).
- **Latency.** Mixed. Traversal exposes all element effects as a fixed shape,
  which can help an Applicative run independent effects in parallel. Other
  Applicatives still run left to right. Haskell `Data.Traversable` documents
  left-to-right evaluation for `traverse` and `sequenceA`
  (https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Data-Traversable.html,
  verified 2026-08-02).
- **Allocation cost.** Sacrificed for immutable structures. Rebuilding the same
  shape usually allocates a new outer value, even when the shape is unchanged.
  Empty or absent structures can be cheap.
- **Operability.** Sacrificed if the traversal is unnamed. A production trace
  may show a broad "parse request" span while hundreds of per-element effects
  fail inside it. Favoured when the traversal labels element count, effect
  count, and failure count.
- **Cost of change.** Favoured when a new effect is introduced. The same
  structure can be traversed with `Option`, `Result`, validation, async, state,
  or writer-like effects. Sacrificed when the structure's shape changes, since
  every traversal instance must preserve the new shape correctly.
- **Team topology.** Favoured when a platform team owns traversal instances for
  shared structures and product teams supply small element functions.
- **Cognitive load.** Sacrificed. The type `t a -> (a -> f b) -> f (t b)` is
  dense until a team has the Applicative and Functor vocabulary. Favoured after
  that vocabulary is shared, because many loops collapse into one known shape.
- **Security and privacy.** Mixed. Central traversal can keep error and
  redaction policy inside the effect. It can also aggregate every rejected
  value into one large error object if the effect was designed carelessly.

Traversable favours declarative, fixed-shape element processing. It sacrifices
the freedom to change shape, pick later work from earlier results, or hide
ordering details inside ad hoc loops.

Another force is API honesty. Many mainstream languages lack higher-kinded
types, so a direct, generic `Traversable<T>` abstraction can be awkward. The
pattern may still appear as concrete `sequence` or `traverse` helpers for
lists, arrays, trees, promises, options, and results. Engineering judgement:
use the abstraction level the language can express cleanly. A clear `traverse`
helper for `Array<Result<A, E>>` is better than a type-class simulation that
the team cannot debug.

## 4. Applicability and non-applicability

Reach for Traversable when these conditions hold.

- You have a structure of values and an effectful function for one value.
- You need the same structure of transformed values inside one combined effect.
- The traversal order is part of the data structure's contract, or the effect
  is insensitive to order.
- The per-element effects are independent enough to be planned before any
  result is inspected.
- You already have or can define a lawful Functor and Foldable view for the
  structure. Haskell makes `Functor` and `Foldable` superclasses of
  `Traversable`
  (https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Data-Traversable.html,
  verified 2026-08-02).
- You need one implementation to work with several effects, such as
  fail-fast result, error-accumulating validation, async task, state, or writer.
- You want `sequence` to turn `t (f a)` into `f (t a)` without writing a
  structure-specific flip by hand.

Do not reach for Traversable in these cases.

- **The transformation changes shape.** Filtering invalid rows, expanding one
  input into many outputs, deduplicating, grouping, or sorting violates the
  same-shape promise. Use Filter, Fold, flatMap, a collection pipeline, or a
  domain-specific transformation.
- **Later work depends on earlier results.** If the result of element one picks
  whether element two is visited, use Monad, explicit recursion, or a stateful
  interpreter.
- **The order is semantically unclear.** A hash map, graph, or concurrent bag
  may not have the stable order that the chosen effect needs. Define an order
  first, use a commutative effect, or avoid a Traversable instance.
- **The structure may be infinite.** Traversing an infinite stream into a single
  strict effect will not finish. Use streaming, pull-based iteration, or a
  bounded fold.
- **The element effect is non-idempotent and retry policy is hidden.** A
  traversal over payments, emails, or writes can duplicate side effects if the
  outer effect retries. Use an explicit workflow with idempotency keys.
- **You need early resource cleanup between elements.** A generic traversal may
  hold intermediate state until the combined effect finishes. Use streaming
  resource scopes when each element opens scarce resources.
- **The structure cannot be rebuilt from its elements.** A cursor, socket,
  database result set, or one-shot iterator can be folded, but it may not be a
  Traversable value because the original shape cannot be recreated.
- **The type has constrained or hidden element positions.** If a structure can
  only hold values that satisfy a runtime invariant not expressed by the type
  parameter, a lawful, total traversal may be impossible.
- **A plain loop is clearer.** Engineering judgement. If the code has one local
  list and one local effect, and no generic reuse, a loop with named variables
  may carry less cognitive load.

The non-applicability list is the guardrail. Traversable is not "loop, but
functional." It is "same-shape traversal with Applicative effects."

## 5. Structure

The pattern has five participants.

- **Traversable structure.** A parameterized structure `T<A>` that contains
  zero or more element positions and can rebuild `T<B>` from transformed
  positions while preserving shape.
- **Element function.** A function `A -> F<B>` that interprets one element in an
  Applicative effect. It may validate, parse, load, annotate, or compute.
- **Applicative effect.** A context `F` with `pure` and a way to combine
  independent effects. It decides whether effects short-circuit, accumulate,
  run later, form combinations, or collect logs.
- **Traversal operation.** The generic operation `traverse` that walks `T<A>`,
  calls the element function for each element, combines the resulting effects,
  and rebuilds `T<B>` inside `F`.
- **Sequencing operation.** The related operation `sequence` or `sequenceA`
  that flips `T<F<A>>` into `F<T<A>>`. It is `traverse` with the identity
  element function.

The relationships are precise. The Traversable structure depends on its own
shape and on Applicative operations. It does not know the meaning of `F`. The
Applicative effect does not know the shape of `T`; it only combines actions.
The element function does not know the whole structure. It sees one `A` and
returns one `F<B>`.

The same participant split applies in less abstract languages. A TypeScript
array helper can traverse `ReadonlyArray<A>` with a `Result<B, E>` returning
function. A Python tree method can traverse nodes with a validator returning a
small `Result`. A Rust tree can traverse with a function returning `Result`.
Those are not full higher-kinded type classes, but they preserve the same
roles.

## 6. ASCII structure diagram

```
  +--------------------------+       has element positions
  |   Traversable T<A>       |----------------------------------+
  |--------------------------|                                  |
  | shape: list, tree, form  |                                  v
  | traverse(f): F<T<B>>     |                         +----------------+
  +--------------------------+                         |  Element A     |
             |                                          +----------------+
             | calls
             v
  +--------------------------+       returns            +----------------+
  | Element function         |------------------------->|  Effect F<B>   |
  |--------------------------|                          +----------------+
  | f: A -> F<B>             |                                  |
  +--------------------------+                                  |
             |                                                   |
             | combined by                                       |
             v                                                   v
  +--------------------------+       rebuilds           +----------------+
  | Applicative F            |------------------------->|  F<T<B>>       |
  |--------------------------|                          +----------------+
  | pure, map, apply/product |
  +--------------------------+

  sequence is the special case where the input is T<F<A>>
  and the element function is identity.
```

## 7. Dynamics

The runtime flow is a walk, effect creation, Applicative combination, and
shape-preserving rebuild. The example below uses a three-element list and a
fail-fast `Result` effect.

```
Caller        Traversable List       f: A -> Result<B,E>    Result effect
  |                  |                         |                  |
  |-- traverse(xs,f)->                         |                  |
  |                  |-- f(a1) -------------->|                  |
  |                  |<--------- Ok(b1) -------|                  |
  |                  |-- combine Ok(b1) ------------------------>|
  |                  |<--------------------------- partial [b1] --|
  |                  |                         |                  |
  |                  |-- f(a2) -------------->|                  |
  |                  |<--------- Ok(b2) -------|                  |
  |                  |-- combine Ok(b2) ------------------------>|
  |                  |<----------------------- partial [b1,b2] --|
  |                  |                         |                  |
  |                  |-- f(a3) -------------->|                  |
  |                  |<--------- Err(e3) ------|                  |
  |                  |-- combine Err(e3) ----------------------->|
  |                  |<------------------------------- Err(e3) --|
  |<-- Err(e3) ------|                         |                  |

  With an error-accumulating Validation effect, the same list walk can
  continue and return all collected errors instead of the first error.
```

Two details matter in production code. First, traversal order belongs to the
Traversable instance. Haskell documents left-to-right evaluation for
`traverse`, `sequenceA`, `mapM`, and `sequence`
(https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Data-Traversable.html,
verified 2026-08-02). A custom structure should document its order with equal
care. Second, the same traversal can have different visible behavior under
different Applicatives. With `Result`, one error may stop the result. With
validation, many errors may be collected. With a list Applicative, choices can
combine into a cross product; Haskell's `Data.Traversable` overview shows
`sequenceA` over lists of lists producing combinations
(https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Data-Traversable.html,
verified 2026-08-02).

## 8. Implementation variants

**Type-class Traversable.** Haskell, Cats, and fp-ts expose the pattern as a
generic abstraction. The benefit is high reuse: one `traverse` consumer can
work over lists, options, maps, trees, and domain structures. The cost is
higher type-system demand and error messages that mention abstraction
machinery.

**Concrete collection traversal.** Many codebases define `traverseArray`,
`traverseList`, or `traverseTree` for a specific structure and a specific
effect family. This carries less abstraction and compiles in languages without
higher-kinded types. The cost is duplication across structures and effects.

**Fail-fast traversal.** The Applicative is `Option`, `Either`, or `Result`.
The first missing value or error can determine the whole result. This variant
fits parsing and lookups where one failure makes the result unusable. It is
poor for user-facing validation when people need all field errors at once.

**Error-accumulating traversal.** The Applicative is a validation type whose
error side has a Semigroup or Monoid. Every element is checked and all errors
are combined. Cats shows `Traverse` in the same ecosystem as `Validated`, which
is the common Scala data type for error accumulation
(https://typelevel.org/cats/typeclasses/traverse.html, verified 2026-08-02;
https://typelevel.org/cats/datatypes/validated.html, verified 2026-08-02).
The cost is possible extra work after the result is already known to be
invalid.

**Async traversal.** The Applicative is a promise, future, task, or effect.
Traversal describes a fixed set of requests and collects their results. The
cost is concurrency policy. Some implementations start work immediately, some
start later, some limit concurrency, and some run in order. The type alone does
not answer that operational question.

**Stateful traversal.** The Applicative carries state, producing operations
such as `mapAccumL` and `mapAccumR`. Haskell exposes `mapAccumL` and
`mapAccumR` in `Data.Traversable`
(https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Data-Traversable.html,
verified 2026-08-02). This variant fits indexing, numbering, and carrying a
small accumulator while preserving shape. The cost is a stronger ordering
dependency.

**Sequence-only helper.** Some APIs expose only `sequence`, because the element
effects already exist. This is common when application code first maps elements
to actions and later flips layers. The risk is repeated `map(...).sequence`
when a direct `traverse` would express both steps in one name.

**Streaming traversal.** A streaming library may offer a traversal-like
operation that emits outputs as they arrive rather than rebuilding the whole
structure in memory. This is often the right operational choice for large or
infinite inputs, but it is no longer the exact Traversable contract unless the
full same-shape result is returned.

## 9. Known production uses

**Haskell `base`, `Data.Traversable`.** The Haskell core library exposes
`Traversable`, `traverse`, `sequenceA`, `mapM`, `sequence`, `mapAccumL`,
`mapAccumR`, `fmapDefault`, and `foldMapDefault`. The Hackage page lists many
instances, including `Maybe`, lists, `NonEmpty`, `Map`, and `Tree`
(https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Data-Traversable.html,
verified 2026-08-02).

**Scala Cats, `Traverse`.** Cats documents `Traverse` as the abstraction behind
generic `traverse` and `sequence`, with examples for `List`, `Option`, and a
binary tree. It also explains that every `Traverse` is a lawful `Functor`
(https://typelevel.org/cats/typeclasses/traverse.html, verified 2026-08-02).

**fp-ts, `Traversable`.** fp-ts exposes `Traversable`, `Traversable1`,
`Traversable2`, and related interface variants for TypeScript. Its module
overview states that `Traversable` represents data structures traversed while
accumulating results and effects in an Applicative functor
(https://gcanti.github.io/fp-ts/modules/Traversable.ts.html, verified
2026-08-02).

**ZIO Prelude, `ForEach`.** ZIO Prelude uses `ForEach` for parameterized types
that contain zero or more values. The documentation shows `forEach` producing a
single `ZIO` that collects results in a `List`, explains instances for
collection types and zero-or-one types, and derives operators such as
`mapAccum`
(https://zio.github.io/zio-prelude/docs/functionalabstractions/parameterizedtypes/foreach,
verified 2026-08-02).

These are library uses rather than isolated examples. They matter because they
publish the pattern as a reusable API surface, with named operations and laws
that production users rely on.

## 10. Consequences

Positive.

- One traversal implementation works with many effects, so validation, parsing,
  async loading, state threading, and collection of logs can share structure
  walking code.
- Element transformations remain small and testable. They receive one element
  and return one effect.
- The data structure's shape policy is centralized. Rebuilding a tree, form,
  or list is no longer copied across call sites.
- `sequence` gives a standard name for flipping layers, which removes many
  custom `collectResults` helpers.
- Laws make refactoring safer. A lawful traversal permits replacing
  `map(f).sequence` with `traverse(f)` as fp-ts documents
  (https://gcanti.github.io/fp-ts/modules/Traversable.ts.html, verified
  2026-08-02).
- The same traversal can be interpreted for collection, validation, state, and
  async effects without changing the structure code.

Negative.

- The abstraction is hard to read before a team understands Functor,
  Applicative, and Foldable.
- A generic traversal can hide expensive effect creation behind a compact
  expression.
- Same-shape preservation can become a trap when the business operation really
  needs filtering, grouping, or expansion.
- Error-accumulating effects can retain rejected values longer than fail-fast
  code.
- Poorly documented traversal order can make side effects surprising.
- In languages without higher-kinded types, full generic Traversable encodings
  may produce more machinery than value.
- Traversing a large strict structure into a strict effect may allocate the
  whole result before downstream code consumes any element.

Engineering judgement. The best outcome is not the most abstract API. The best
outcome is a traversal boundary that makes element work, shape preservation,
and effect policy visible to the next maintainer.

## 11. Failure modes and misuse

**Shape-changing mapper.** Symptom. A traversal over ten inputs returns nine
outputs, or a tree returns with branches collapsed, while callers expected a
position-for-position result. Cause. Filtering or expansion was hidden inside a
method named `traverse`. Fix. Rename the operation to `filterMap`, `flatMap`,
or a domain name, and keep Traversable for same-shape transformations.

**Unstable map order.** Symptom. Logs, generated ids, or validation messages
appear in a different order across runs. Cause. A Traversable instance was
defined for a structure with no stable element order, or it delegated to a hash
iteration order. Fix. Define a stable order, use an ordered structure, or state
that only commutative effects are supported.

**Hidden parallel explosion.** Symptom. A request that once made ten backend
calls starts making thousands at once after a larger input arrives. Cause. An
async Applicative starts every element effect without a concurrency limit. Fix.
Use a bounded traversal variant, batch the input, or move to a streaming API
with explicit backpressure.

**Fail-fast where accumulation was required.** Symptom. A form response shows
one error at a time even though users submitted many invalid fields. Cause. The
traversal used `Result` or `Either` when the product requirement was error
accumulation. Fix. Use a validation Applicative with an error Semigroup, then
render all collected errors.

**Accumulation where fail-fast was required.** Symptom. A request continues
validating or loading data after an authorization or quota failure. Cause. The
traversal used an accumulating Applicative for work that should stop early.
Fix. Split the gate from the field traversal. Run authorization first, then
traverse only after the gate passes.

**One-shot iterator treated as Traversable.** Symptom. The first pass succeeds,
but a retry or second consumer sees no elements. Cause. A consumable cursor was
wrapped in a traversal-like API that promised a rebuildable structure. Fix.
Expose Foldable, Iterator, or Stream semantics instead of Traversable.

**Lawless instance.** Symptom. `traverse(pure)` changes metadata, increments a
counter, or rebalances a tree, and an optimization changes behavior. Cause. The
instance does work beyond element interpretation and same-shape rebuild. Fix.
Move metadata refresh, balancing, or metrics outside the Traversable instance
and add law tests.

**Nested effects left unflipped.** Symptom. Callers receive
`List<Result<User, Error>>` and each caller handles partial failure in a
different way. Cause. Code used `map` where it needed `traverse`. Fix. Replace
the mapping site with traversal so the effect policy is chosen once.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Traversable | Functor map | Foldable foldMap | Monad flatMap | Iterator | Visitor |
|---|---|---|---|---|---|---|
| Shape preservation | Strong. Returns `F<T<B>>` | Strong, but pure only | None. Produces a summary | Weak. Can change shape | None by default | Depends on visitor |
| Effect handling | Applicative effects | No effects unless hidden | Monoidal accumulation | Dependent effects | Manual | Manual |
| Dependent sequencing | Poor | Poor | Poor | Strong | Strong | Medium |
| Error accumulation | Strong with validation | Poor | Medium if errors form a monoid | Often fail-fast | Manual | Manual |
| Latency control | Depends on Applicative | Direct and predictable | Direct and predictable | Sequential by dependency | Explicit | Explicit |
| Cognitive load | High at first | Low | Medium | Medium | Low | Medium |
| Generic reuse | High | High for pure transforms | High for summaries | High for chains | Low to medium | Medium |
| Same code over many effects | Strong | Weak | Medium | Medium | Weak | Weak |
| Streaming large input | Weak unless lazy | Medium | Strong | Medium | Strong | Medium |
| Team fit | Good for FP-literate teams | Broad | Broad | Broad | Broad | OO-heavy teams |

Reading of the table. Functor wins for pure element changes. Foldable wins for
summaries. Monad wins when each step depends on the previous result. Iterator
wins when operational control and streaming matter more than rebuilding a
same-shaped result. Visitor wins when operations over an object structure need
double dispatch or object-oriented extension. Traversable wins when the work is
fixed-shape element interpretation under a reusable Applicative effect.

## 13. Related and incompatible patterns

- **Functor.** Traversable extends Functor in Haskell and can derive `map` by
  traversing with the identity effect. Haskell exposes `fmapDefault` for this
  relationship
  (https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Data-Traversable.html,
  verified 2026-08-02).
- **Foldable.** Traversable also extends Foldable in Haskell and can derive
  `foldMap` by traversing with a constant effect. Haskell exposes
  `foldMapDefault`
  (https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Data-Traversable.html,
  verified 2026-08-02).
- **Applicative.** Applicative is the effect side of the pattern. Traversable
  supplies the shape walk; Applicative supplies `pure` and combination.
- **Monad.** Monad replaces Traversable when later work depends on earlier
  results. Traversable can use monadic effects through `mapM`, but the
  structure of the traversal is still fixed. Haskell documents `mapM` as a
  monadic version of traversal
  (https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Data-Traversable.html,
  verified 2026-08-02).
- **Iterator.** Iterator is related historically and operationally. Gibbons and
  Oliveira argue that applicative traverse captures the mapping and
  accumulating aspects of Iterator
  (https://www.cs.ox.ac.uk/publications/publication1409-abstract.html,
  verified 2026-08-02). Iterator remains better for pull-based, one-element-at-a
  time consumption.
- **Visitor.** Visitor and Traversable both walk a structure, but Visitor
  dispatches operations over object types while Traversable interprets element
  values through an Applicative effect. Visitor can change behavior per node
  class; Traversable is constrained by same-shape rebuild.
- **Validation.** Validation is a common Applicative used with Traversable. It
  turns a structure of invalid or valid element checks into either all errors
  or the rebuilt valid structure.
- **Streaming.** Streaming libraries replace Traversable when the input is
  large, infinite, or resource-sensitive. They may offer traversal-like names,
  but the operational contract is backpressure and bounded memory rather than
  immediate same-shape rebuild.
- **Shape-changing transforms.** Filter, flatMap, groupBy, sort, and parser
  expansion conflict with Traversable when hidden under the same name. They can
  compose before or after traversal, but they are not traversal itself.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it.

1. Find a loop or recursive walk that applies an effectful function to each
   element and then rebuilds the same outer shape.
2. Name the three roles in the current code: the structure, the element
   function, and the effect policy.
3. Extract the element work into a function `A -> F<B>`. Keep it free of
   knowledge about indexes, tree branches, output buffers, and traversal state.
4. Extract the effect combination into a small Applicative-like API. For a
   narrow codebase this may be `ok`, `map2`, and `fail`; it need not be a full
   type class.
5. Replace the loop body with a local `traverse` helper for the exact
   structure. Run tests before making it generic.
6. Add a `sequence` helper only if callers already have `T<F<A>>` values.
7. Add law tests: traversing with a pure wrapper returns the original shape,
   and traversing with composed effects behaves the same as two traversals
   composed through the effect.
8. Generalize from list to tree, option, form, or domain structure only after a
   second real use appears.
9. Document traversal order for structures where side effects make order
   visible.

Removing the pattern when it stops earning its place.

1. Look for call sites that always use one structure and one effect.
2. Inline `traverse` into a named loop if the generic type vocabulary is now
   heavier than the code it replaces.
3. Split shape-changing work out of traversal. Rename the shape-changing
   operation before deleting traversal helpers.
4. If a traversal is used only to run effects and discard results, replace it
   with a `forEach`, `traverse_`, stream sink, or fold that states result
   discard plainly.
5. If dependent sequencing has crept in, convert the code to explicit recursion
   or monadic chaining. Keep the old traversal tests while migrating, then
   delete them after behavior is covered by workflow tests.
6. If memory pressure comes from rebuilding a large structure, replace strict
   traversal with streaming or batched processing and update telemetry to track
   chunk sizes.

The named refactoring family connections are Extract Function for the element
function, Extract Class or Extract Module for the effect policy, Replace Loop
with Pipeline where the host language supports it, and Inline Function when a
generic traversal helper no longer pays for itself.

## 15. Testing and verification

Testing splits into element tests, effect tests, structure tests, and laws.

- **Element tests.** Test the `A -> F<B>` function without a full structure.
  This keeps domain failures small and readable.
- **Effect tests.** Test the Applicative policy. For fail-fast result, assert
  the first error behavior. For validation, assert error accumulation and error
  order. For async, assert concurrency limits through a fake scheduler when the
  implementation exposes one.
- **Structure tests.** Test that traversal preserves shape. Lists keep length
  and order. Trees keep branch positions. Options keep absence. Domain forms
  keep field names.
- **Law tests.** For each Traversable instance, test identity and composition.
  Haskell lists naturality, identity, and composition laws for `traverse`
  (https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Data-Traversable.html,
  verified 2026-08-02). In languages without direct law tooling, sample a
  small set of structures and pure functions.
- **Sequence equivalence.** Test that `traverse(f)` matches `map(f)` followed by
  `sequence` for representative structures, matching the fp-ts compatibility
  statement
  (https://gcanti.github.io/fp-ts/modules/Traversable.ts.html, verified
  2026-08-02).
- **Order tests.** Use an effect that records visited elements. Assert the
  documented traversal order.
- **Resource tests.** For async or IO traversal, use fakes that count starts,
  completions, retries, and cancels.

What became easier. Element functions are small. The same structure traversal
can be tested with an identity-like effect, a recording effect, and a failure
effect. A bug in shape walking can be isolated from a bug in validation policy.

What became harder. The full behavior emerges from three participants, so a
single unit test may miss the interaction. Law tests can feel abstract in a
codebase that does not already test algebraic contracts. Async traversal needs
tests for scheduling, cancellation, and concurrency, none of which are visible
in the type `traverse`.

Engineering judgement. For application teams, the minimum useful test set is
one success traversal, one failure traversal, one order-recording traversal,
and one shape-preservation property. For library teams, law tests are not
optional.

## 16. Observability signals

This dimension is engineering judgement.

Record these signals when traversal runs in production.

- A traversal name, such as `validate_shipping_addresses` or
  `load_product_tree`, not only the generic word `traverse`.
- Input element count and output element count. For a lawful traversal they
  should match by position for fixed-size structures, with absence handled by
  the structure itself.
- Effect type or policy label, such as `result_fail_fast`, `validation_all`,
  `promise_bounded`, or `state_indexing`.
- Started, completed, failed, and skipped effect counts.
- Error count and error class distribution for validation and result effects.
- Traversal duration and per-element duration histograms.
- Concurrency gauge for async traversal.
- Memory or buffered result size for large strict traversals.
- Cancellation and retry counts when effects can be cancelled or retried.

A healthy dashboard shows stable input sizes, output shape counts matching
input shape counts, expected error rates, bounded concurrency, and duration
that grows roughly with input size. For validation, many element errors may be
healthy if the endpoint accepts bulk input and reports all invalid rows.

A failing dashboard shows one of these patterns. Input count grows while
duration grows faster than linearly. Output counts no longer match input
counts. Error order changes across versions. Concurrency spikes to input size
with no cap. Memory climbs with batch size. Fail-fast paths report only the
first error on endpoints that promised full feedback. Validation paths keep
running after an authorization gate should have stopped the workflow.

Log element values with care. Prefer indexes, field names, record ids, and
hashes over raw payloads. Traversal often touches every submitted value, so a
single careless log statement can leak an entire form or batch.

## 17. Security and privacy implications

Traversable is not a security pattern, but it changes where security decisions
sit.

**Validation surface.** Traversal is a natural fit for validating every element
of a structure. With an accumulating effect, it can report many errors at once.
The risk is that aggregated errors may include rejected secrets, tokens, raw
personal data, or internal rule names. The validation effect should carry safe
error codes and field paths, not raw rejected values by default.

**Authorization gates.** Traversal should not replace a gate that decides
whether work may proceed. If a user lacks permission for a batch operation,
running a traversal over every element may leak which element ids exist or may
perform work that should never have started. Gate first, traverse second.

**Side-effect duplication.** A traversal over non-idempotent effects such as
email sends, payment captures, or database writes can duplicate work when the
outer effect retries or when a caller repeats the whole traversal after a
timeout. Use idempotency keys and expose retry policy at the workflow level.

**Data retention.** An accumulating Applicative can retain every error and
sometimes every intermediate value until the final result is built. For bulk
inputs this may keep sensitive data alive longer than a streaming fail-fast
pipeline. Bound batch sizes and sanitize accumulated errors.

**Timing and enumeration.** Fail-fast traversal can reveal the position of the
first invalid or unauthorized element through timing or error shape. If that
position is sensitive, use constant-shape validation responses or normalize the
reported error.

**Untrusted callbacks.** Library traversal accepts a caller-provided element
function. If the library runs with elevated privileges, the callback must be
treated as untrusted code. Do not call it while holding locks, open
transactions, or privileged handles unless that contract is explicit.

The pattern is silent on encryption, authentication, and access control by
itself. Its security relevance comes from concentrating per-element work and
effect accumulation in one reusable path.

## 18. References

- Conor McBride and Ross Paterson, "Applicative Programming with Effects",
  *Journal of Functional Programming*, volume 18, issue 1, 2008, pages 1 to
  13. Linked from Haskell `Control.Applicative`,
  https://hackage.haskell.org/package/base/docs/Control-Applicative.html,
  verified 2026-08-02.
- Haskell `base` 4.22.0.0, `Data.Traversable`, Hackage documentation,
  https://hackage-content.haskell.org/package/base-4.22.0.0/docs/Data-Traversable.html,
  verified 2026-08-02.
- Jeremy Gibbons and Bruno C. d. S. Oliveira, "The Essence of the Iterator
  Pattern", *Journal of Functional Programming*, volume 19, issues 3 and 4,
  2009, pages 377 to 402. Oxford publication page,
  https://www.cs.ox.ac.uk/publications/publication1409-abstract.html,
  verified 2026-08-02.
- Typelevel Cats, "Traverse" type class documentation,
  https://typelevel.org/cats/typeclasses/traverse.html, verified 2026-08-02.
- Typelevel Cats, `Validated` data type documentation,
  https://typelevel.org/cats/datatypes/validated.html, verified 2026-08-02.
- fp-ts, `Traversable.ts` module documentation,
  https://gcanti.github.io/fp-ts/modules/Traversable.ts.html, verified
  2026-08-02.
- ZIO Prelude, "ForEach" parameterized type documentation,
  https://zio.github.io/zio-prelude/docs/functionalabstractions/parameterizedtypes/foreach,
  verified 2026-08-02.

## Code examples

The examples use TypeScript, Python, and Rust because those toolchains are
available in this repository environment and the pattern can be expressed
without framework scaffolding.

### TypeScript

```typescript
type Result<T> =
  | { tag: "ok"; value: T }
  | { tag: "err"; errors: string[] };

const ok = <T>(value: T): Result<T> => ({ tag: "ok", value });
const err = <T>(message: string): Result<T> => ({ tag: "err", errors: [message] });

function traverseResult<A, B>(
  values: readonly A[],
  f: (value: A, index: number) => Result<B>,
): Result<B[]> {
  const out: B[] = [];
  const errors: string[] = [];

  values.forEach((value, index) => {
    const next = f(value, index);
    if (next.tag === "ok") {
      out.push(next.value);
    } else {
      errors.push(...next.errors);
    }
  });

  return errors.length === 0 ? ok(out) : { tag: "err", errors };
}

const parsed = traverseResult(["1", "x", "3"], (text, index) => {
  const n = Number(text);
  return Number.isInteger(n) ? ok(n) : err(`field ${index} is not an integer`);
});

console.log(JSON.stringify(parsed));
```

### Python

```python
from dataclasses import dataclass
from typing import Callable, Generic, Iterable, TypeVar

A = TypeVar("A")
B = TypeVar("B")


@dataclass(frozen=True)
class Result(Generic[A]):
    value: A | None = None
    errors: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.errors


def success(value: A) -> Result[A]:
    return Result(value=value)


def failure(message: str) -> Result[A]:
    return Result(errors=(message,))


def traverse_result(values: Iterable[A], f: Callable[[A], Result[B]]) -> Result[list[B]]:
    out: list[B] = []
    errors: list[str] = []
    for value in values:
        item = f(value)
        if item.ok:
            out.append(item.value)  # type: ignore[arg-type]
        else:
            errors.extend(item.errors)
    return Result(value=out) if not errors else Result(errors=tuple(errors))


def parse_positive(text: str) -> Result[int]:
    try:
        number = int(text)
    except ValueError:
        return failure(f"{text} is not an integer")
    return success(number) if number > 0 else failure(f"{number} is not positive")


print(traverse_result(["4", "-1", "bad"], parse_positive))
```

### Rust

```rust
#[derive(Debug, PartialEq)]
enum Tree<T> {
    Empty,
    Leaf(T),
    Node(Box<Tree<T>>, T, Box<Tree<T>>),
}

impl<T> Tree<T> {
    fn traverse_result<U, E, F>(self, f: &mut F) -> Result<Tree<U>, E>
    where
        F: FnMut(T) -> Result<U, E>,
    {
        match self {
            Tree::Empty => Ok(Tree::Empty),
            Tree::Leaf(value) => f(value).map(Tree::Leaf),
            Tree::Node(left, value, right) => {
                let left_out = left.traverse_result(f)?;
                let value_out = f(value)?;
                let right_out = right.traverse_result(f)?;
                Ok(Tree::Node(Box::new(left_out), value_out, Box::new(right_out)))
            }
        }
    }
}

fn parse_positive(text: &str) -> Result<i32, String> {
    let number = text.parse::<i32>().map_err(|_| format!("{text} is not an int"))?;
    if number > 0 {
        Ok(number)
    } else {
        Err(format!("{number} is not positive"))
    }
}

fn main() {
    let tree = Tree::Node(
        Box::new(Tree::Leaf("2")),
        "5",
        Box::new(Tree::Leaf("8")),
    );
    let parsed = tree.traverse_result(&mut parse_positive).unwrap();
    println!("{parsed:?}");
}
```
