---
name: Monoid
slug: monoid
family: 16-functional
category: Functional
aliases: [Identity-bearing Semigroup, Foldable Reducer, Combinable With Empty]
first_described: "Abstract algebra, named in software through Haskell type classes"
maturity: canonical
related: [semigroup, functor, applicative, monad, fold, reducer, algebraic-data-type]
incompatible_with: [non-associative-combine, missing-identity, order-sensitive-side-effects]
verified: 2026-08-02
---

# Monoid

## 1. Name, aliases, and lineage

The canonical software name is Monoid. In programming, a monoid is a type with
one closed binary operation and one identity value. Closed means combining two
values of the type returns another value of the same type. The operation must
be associative. The identity value must leave any other value unchanged when it
appears on either side of the operation. Haskell's `Data.Monoid` documentation
defines `Monoid` as a class for types with an associative binary operation and
an identity, with `mempty`, `mappend`, and `mconcat` as the class operations
(https://hackage.haskell.org/package/base/docs/Data-Monoid.html, verified
2026-08-02). The same documentation lists the right identity, left identity,
associativity, and `mconcat` laws for valid instances
(https://hackage.haskell.org/package/base/docs/Data-Monoid.html, verified
2026-08-02).

The mathematical lineage is abstract algebra. Saunders Mac Lane, *Categories
for the Working Mathematician*, second edition, Springer, 1998, chapter I,
section 1, presents monoids among the first algebraic examples used to explain
categories. I am citing the chapter and section, not a page number, because I
did not verify a page image in this session. Software practice adopted the same
word because the law is useful in programs, not because application developers
need category theory to add counters. The practical test is mechanical: can the
program combine two accumulated values in any grouping, and can it return a
valid value for an empty input?

Common software aliases include **identity-bearing semigroup**, **reducer with
empty**, and **combinable with empty**. Cats states the same shape by saying
that `Monoid` extends `Semigroup` with an `empty` value, and that `empty` must
be an identity for `combine` (https://typelevel.org/cats/typeclasses/monoid.html,
verified 2026-08-02). fp-ts exposes the same idea through an interface that
extends `Semigroup` and adds `empty`
(https://gcanti.github.io/fp-ts/modules/Monoid.ts.html, verified 2026-08-02).

The name is easy to overuse. Not every pair of methods named `combine` and
`empty` is a monoid. The operation must be associative. The identity must work
on both sides. If grouping changes the answer, the implementation is a reducer
with a preferred evaluation order, not a monoid. If an empty input cannot
produce a value of the same type without inventing a lie, the structure may be
a Semigroup instead. Cats uses `NonEmptyList` as an example of a type that can
form a semigroup through concatenation but has no matching identity element
(https://typelevel.org/cats/typeclasses/monoid.html, verified 2026-08-02).

The phrase "monoid pattern" in this entry means the software design pattern:
modeling an accumulation, merge, or composition rule as a named identity value
plus a lawful associative operation, then routing folds, parallel reductions,
configuration merges, metrics aggregation, and composable domain objects through
that rule.

## 2. Problem and context

A codebase has many places that reduce many values into one value. A service
adds counters. A reporting job merges per-partition summaries. A query builder
combines predicates. A logging layer merges metadata. A validation component
combines warnings. A streaming system combines partial aggregates from workers.
Each site has the same control-flow problem: the input may have zero values,
one value, or many values, and the implementation wants one result of the same
domain type.

Without the pattern, each call site decides what to do with the empty case and
how to group the work. One function starts a counter at zero. Another treats
the first row as a seed and crashes on an empty input. A third uses `null`. A
parallel version groups by partition and gives a different answer from the
single-threaded version because the operation was not associative. The domain
rule is no longer one rule. It is a set of local habits.

Monoid solves the narrow version of that problem. Put the empty value and the
combine rule next to each other. Give the pair a name. Test the laws. Then make
folding code depend on that pair rather than on ad hoc empty-case behavior.
Once that contract exists, a generic `combineAll` can reduce an empty list, a
single value, or many values with the same code. Cats documents this as the
reason `combineAll` can return `empty` for an empty list
(https://typelevel.org/cats/typeclasses/monoid.html, verified 2026-08-02).
fp-ts documents `concatAll` the same way: it combines a sequence and returns
the monoid empty value when the sequence is empty
(https://gcanti.github.io/fp-ts/modules/Monoid.ts.html, verified 2026-08-02).

The context matters. Monoid is not a prettier spelling of addition. It is a
contract for code that wants regrouping freedom. A single-threaded left fold
has one order. A parallel reduce has many possible groupings. Java Stream
`reduce` requires an identity value for the accumulator and requires the
accumulator to be associative, because stream implementations are not
constrained to execute sequentially
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Stream.html,
verified 2026-08-02). That requirement is the same pressure that makes monoids
useful in distributed systems.

The pattern also handles composition of richer values. A `ReportTotals` value
may have `orders`, `grossRevenue`, `refunds`, `warnings`, and `tags`. Each
field can have its own monoid. The whole report can then have a derived monoid
that combines fields pairwise and uses field identities for the whole identity.
fp-ts exposes this through `struct` and `tuple` constructors for monoids
(https://gcanti.github.io/fp-ts/modules/Monoid.ts.html, verified 2026-08-02).
Cats documentation gives map and set examples for `combineAll`
(https://typelevel.org/cats/typeclasses/monoid.html, verified 2026-08-02).

The pattern is most valuable when the operation is domain policy. A payment
system should not hide whether discounts add, multiply, take the maximum, or
compose in display order. A permissions system should not hide whether rules
combine by any-allow, all-allow, first-match, or last-match. Monoid gives the
policy a name and makes the empty case explicit. Engineering judgement: when a
team argues about the correct identity value, that argument is often the design
work the pattern is meant to expose.

A second common context is retry and recomputation. In batch systems, a worker
can fail after producing a partial result. In streaming systems, late data can
arrive after an earlier window result has already been emitted. In cache
warming, a partial cache entry may be rebuilt from several sources. If the
partial result has a monoid, the system can merge rebuilt pieces with the same
law used by the original path. If the partial result is a hidden mutable object
with local merge habits, retry behavior becomes a second implementation of the
business rule.

The empty value is also an API design decision. A search API returning an empty
result set for a successful query is usually clear. A balance API returning zero
for an account that could not be loaded is usually dangerous. Both values may
look like "nothing" to a programmer. Only one is the identity of a successful
domain operation. Monoid forces the distinction into the type. If the empty
case means "no members of this collection", a monoid may fit. If the empty case
means "the system does not know", use a result type, an optional type, or an
explicit error.

## 3. Forces

This dimension is engineering judgement, except where a named API or law is
cited.

- **Coupling.** Favoured. Folding, partition merging, and summary code depend
  on a small algebraic contract rather than on each domain type's internal
  fields.
- **Consistency.** Favoured when laws hold. Haskell publishes identity and
  associativity laws for `Monoid`, and Cats publishes the identity law for
  `empty` over `combine`
  (https://hackage.haskell.org/package/base/docs/Data-Monoid.html, verified
  2026-08-02;
  https://typelevel.org/cats/typeclasses/monoid.html, verified 2026-08-02).
- **Latency.** Favoured for parallel aggregation when the operation is truly
  associative. Independent chunks can be reduced separately and combined later.
  Sacrificed when the chosen operation allocates more intermediate values than
  a specialized mutable loop.
- **Consistency under concurrency.** Favoured for batch and stream systems that
  merge partial results, because grouping may vary by shard, retry, batch size,
  or worker count.
- **Operability.** Favoured when the monoid is named in telemetry. Sacrificed
  when a generic combine hides which domain fields dominated the final value.
- **Cost.** Mixed. The abstraction reduces repeated empty-case code, but law
  tests and named wrappers add maintenance cost.
- **Team topology.** Favoured when a platform team owns generic folding or
  streaming infrastructure and product teams supply domain aggregates.
- **Cognitive load.** Sacrificed for teams that do not know the difference
  between Semigroup, Monoid, and arbitrary reducer. Favoured after the team
  learns the law, because many aggregation rules become one review shape.
- **Privacy and security.** Mixed. A named combine can centralize redaction
  policy for metadata and audit fragments. A careless combine can also retain
  more data than an endpoint needs.

The pattern favours lawful regrouping and explicit empty cases. It sacrifices
some directness. A reader must know which monoid instance is in scope or which
wrapper selects the operation. Haskell's `Data.Monoid` documentation notes that
some types can have more than one monoid, such as addition and multiplication
for numbers, and uses `Sum` and `Product` wrappers for that reason
(https://hackage.haskell.org/package/base/docs/Data-Monoid.html, verified
2026-08-02).

## 4. Applicability and non-applicability

Reach for Monoid when these conditions hold.

- A domain value needs a valid empty value and a closed combine operation.
- Empty input should return a domain value rather than an error or an optional
  result.
- The operation can be regrouped without changing the answer.
- The same combine rule appears in multiple folds, merges, caches, retries, or
  distributed aggregation stages.
- A composite value can be built by combining fields independently.
- You want to expose the empty-case policy in code review, not hide it in the
  first line of a loop.
- The language or library already carries the vocabulary, such as Haskell
  `Data.Monoid`, Cats `Monoid`, fp-ts `Monoid`, or Algebird monoids
  (https://hackage.haskell.org/package/base/docs/Data-Monoid.html, verified
  2026-08-02;
  https://typelevel.org/cats/typeclasses/monoid.html, verified 2026-08-02;
  https://gcanti.github.io/fp-ts/modules/Monoid.ts.html, verified
  2026-08-02;
  https://twitter.github.io/algebird/, verified 2026-08-02).

Do not reach for Monoid in these cases.

- **There is no honest identity.** A non-empty list has concatenation, but an
  empty non-empty list is a contradiction. Use Semigroup and return `Option`,
  `Maybe`, or a domain error for empty input.
- **The operation is not associative.** Floating-point addition, string
  formatting with separators, and time-windowed rate calculations can change
  under regrouping. Use an ordered fold or a domain-specific accumulator.
- **Order carries domain meaning.** If "first rule wins" and "last rule wins"
  are different policies, the monoid must name that order through a wrapper such
  as `First`, `Last`, or `Dual`. If the order is accidental, do not present the
  operation as unordered.
- **The combine operation has side effects.** Writing logs, mutating an external
  cache, reading time, or making network calls inside `combine` breaks the
  rewrite assumptions. Use an effect type, a command, or explicit orchestration.
- **The empty value hides a missing-data error.** Returning zero revenue for a
  failed billing query is not the same as an empty set of paid invoices. Use a
  result type that preserves failure.
- **The operation is lossy and the loss is not intended.** Taking max, min, or
  last value is lawful for the right wrapper, but it discards information. Use
  it only when that loss is the product requirement.
- **A mutable builder is the real abstraction.** Some hot paths need mutation
  for allocation control. A monoid can still describe the final merge law, but
  the implementation may be a builder plus a separate immutable result.
- **The team cannot identify which instance is active.** If implicit or global
  instance lookup makes reviews ambiguous, prefer explicit wrapper types or a
  passed value named after the policy.

## 5. Structure

Four participants define the pattern.

- **Carrier type.** The type whose values are combined. Examples include
  `String`, `Sum<number>`, `Map<Key, Count>`, `ReportTotals`, a predicate, or an
  endomorphism.
- **Identity value.** The value that leaves any carrier value unchanged when
  combined on the left or right. Examples are `0` for numeric addition, `1` for
  multiplication, the empty string for string concatenation, an empty map for
  map union with value combination, and the identity function for function
  composition.
- **Associative combine operation.** A binary operation that takes two carrier
  values and returns a carrier value. It may be named `combine`, `concat`,
  `mappend`, `<>`, `merge`, or `append`, but the name is less important than the
  law.
- **Folder or reducer.** The client that reduces many values with the identity
  and combine operation. It may be a list fold, stream reduce, metrics rollup,
  distributed combiner, or configuration merge.

Relationships. The folder depends on the identity and combine pair, not on the
fields of the carrier. The carrier may expose the pair as methods, as a type
class instance, as a dictionary record, as a trait implementation, or as a value
passed to the reducer. Composite monoids depend on smaller monoids. A
`ReportTotals` monoid can depend on a `Sum` monoid for counts, a `Money` monoid
for amounts, and a set union monoid for tags.

The law is part of the structure. Without the law, the folder cannot safely
split work, reorder grouping, skip empty chunks, or reuse a generic
`combineAll`.

## 6. ASCII structure diagram

```text
   +-------------------+        provides        +-------------------+
   |    Monoid<M>      | ---------------------> |   Folder/Reducer  |
   |-------------------|                        |-------------------|
   | empty: M          |                        | fold(values, M)   |
   | combine(M, M): M  |                        +-------------------+
   +-------------------+                                  |
             ^                                            |
             | instance for                               | consumes many
             |                                            v
   +-------------------+        values          +-------------------+
   |   Carrier type M  | <--------------------- |   Iterable<M>     |
   |-------------------|                        |-------------------|
   | domain fields     |                        | zero or more M    |
   +-------------------+                        +-------------------+

   Law boundary:
   combine(empty, x) == x
   combine(x, empty) == x
   combine(x, combine(y, z)) == combine(combine(x, y), z)
```

## 7. Dynamics

At runtime, the reducer starts with the identity and combines each input. In a
parallel or distributed runtime, the same law permits each partition to reduce
locally, then merge partial results with the same operation. Java Stream
documents this pressure by requiring an identity and associative accumulator for
`reduce`, with execution not constrained to be sequential
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Stream.html,
verified 2026-08-02).

```text
Sequential fold

values:      [a, b, c]
identity:    e
combine:     <>

step 0:      acc0 = e
step 1:      acc1 = e <> a
step 2:      acc2 = acc1 <> b
step 3:      acc3 = acc2 <> c
result:      ((e <> a) <> b) <> c

Parallel fold with the same result when laws hold

partition 1: p1 = e <> a
partition 2: p2 = e <> b <> c
merge:       p1 <> p2
result:      (e <> a) <> ((e <> b) <> c)

The two groupings are interchangeable only because e is identity and <> is
associative.
```

The identity value handles empty partitions. A worker with no rows can return
`empty` and still participate in the merge. That is why a monoid is stronger
than a semigroup for infrastructure code. A semigroup can combine two present
values. A monoid can also represent the result of no values.

Dynamics become more subtle when many monoids exist for one carrier. For
numbers, addition and multiplication both qualify. For booleans, `and` with
`true` and `or` with `false` both qualify. For optional values, first-present
and last-present can both qualify. Haskell exposes wrappers such as `Sum`,
`Product`, `All`, `Any`, `First`, `Last`, `Dual`, and `Endo`
(https://hackage.haskell.org/package/base/docs/Data-Monoid.html, verified
2026-08-02). The wrapper chooses the runtime policy.

## 8. Implementation variants

**Type class instance.** Haskell, Cats, and fp-ts expose monoids as type class
style values. Generic code requests `Monoid<A>` and calls `empty` plus
`combine` or `concat`. This variant works well for libraries because the domain
type does not need to own every operation. Its cost is instance discovery. A
reader must know which imports or implicits select the instance.

**Interface or trait object.** Java, Go, TypeScript, and Rust can pass an object
or trait value with `empty` and `combine`. This is explicit and easy to test.
Its cost is ceremony at call sites.

**Static methods on the carrier.** A domain type can expose `empty()` and
`merge()`. This is discoverable, but it handles only one policy per carrier
unless wrappers are added. It is a poor fit for types with several valid
monoids.

**Wrapper types.** `Sum`, `Product`, `First`, `Last`, `All`, and `Any` give
separate names to separate policies over the same underlying carrier. Haskell's
`Data.Monoid` lists these wrappers
(https://hackage.haskell.org/package/base/docs/Data-Monoid.html, verified
2026-08-02). This variant is preferred when ambiguity would be dangerous.

**Derived product monoid.** A record, tuple, or struct combines field by field
using field monoids. fp-ts documents `struct` and `tuple` constructors for this
purpose (https://gcanti.github.io/fp-ts/modules/Monoid.ts.html, verified
2026-08-02). The cost is that every field's combine policy must be chosen.

**Endomorphism monoid.** Functions from `A` to `A` form a monoid under
composition with the identity function as empty. Haskell lists `Endo` in
`Data.Monoid` (https://hackage.haskell.org/package/base/docs/Data-Monoid.html,
verified 2026-08-02). This variant is useful for building pipelines, but it can
hide runtime order if the wrapper name is vague.

**Mutable accumulator with monoid result.** A hot aggregation path may mutate a
builder for speed, then expose a lawful immutable merge at partition boundaries.
Engineering judgement: this is often the best compromise in systems code. The
monoid describes the cross-boundary law, while the local loop stays allocation
aware.

**Configuration merge monoid.** Configuration layers often combine defaults,
environment overrides, tenant settings, and request settings. A monoid can
model fields that combine by union, append, max, min, or last writer. This
variant needs care because not every field shares one policy. A timeout may use
minimum to preserve a safety cap. A feature flag may use last writer with
source precedence. A redaction policy may use union. Engineering judgement:
configuration monoids should be built from small named field policies rather
than one broad "merge config" rule.

**Predicate monoid.** Predicates over the same input type form monoids under
conjunction with an always-true identity and under disjunction with an
always-false identity. This is useful for query filters, validation guards, and
feature gates. The variant is lawful, but the chosen identity has product
meaning. An empty list of filters under conjunction admits everything. An empty
list under disjunction admits nothing. Both can be right in different products.

**Map monoid.** Maps often combine by key union, with colliding values combined
by a value monoid. This is a frequent shape for counters, histograms, grouped
metrics, and tags. The cost is nested policy. The outer map policy is union.
The inner value policy decides what happens on key collision. A collision can
add counts, take the latest timestamp, merge a set, or reject conflict.

**Free monoid over a sequence.** Lists, arrays, strings, and byte buffers are
often treated as monoids under concatenation with the empty sequence as
identity. This variant is familiar and useful, but performance can be poor when
left-associated concatenation repeatedly copies data. A tree-shaped
concatenation, rope, builder, or chunked buffer may preserve the monoid law
while changing the runtime representation.

## 9. Known production uses

- **Haskell `base`, `Data.Monoid`.** The Haskell base library exposes the
  `Monoid` type class with `mempty`, `mappend`, and `mconcat`, plus many
  standard instances and wrappers such as `Sum`, `Product`, `All`, `Any`,
  `First`, `Last`, `Dual`, and `Endo`
  (https://hackage.haskell.org/package/base/docs/Data-Monoid.html, verified
  2026-08-02).
- **Typelevel Cats.** Cats documents `Monoid` as `Semigroup` plus `empty`,
  provides `combineAll`, and demonstrates use with integers, strings, maps, and
  sets (https://typelevel.org/cats/typeclasses/monoid.html, verified
  2026-08-02).
- **fp-ts.** fp-ts exposes a `Monoid<A>` interface extending `Semigroup<A>` with
  `empty`, plus `concatAll`, `reverse`, `struct`, and `tuple` helpers
  (https://gcanti.github.io/fp-ts/modules/Monoid.ts.html, verified
  2026-08-02).
- **Twitter Algebird.** Algebird describes itself as a Scala library for
  abstract algebra targeted at aggregation systems, including Scalding, Apache
  Storm, and Summingbird. Its documentation names monoids, groups, rings, and
  approximation algorithms such as Bloom filters, HyperLogLog, and
  CountMinSketch as part of the aggregation model
  (https://twitter.github.io/algebird/, verified 2026-08-02).
- **Java Stream reductions.** Java Stream `reduce` does not expose a `Monoid`
  type class, but the API contract requires the same identity and associativity
  properties for reduction over streams
  (https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Stream.html,
  verified 2026-08-02). This is a named production API use of the monoid law,
  not a claim that Java names the pattern `Monoid`.

These examples cover two styles of production use. Haskell, Cats, fp-ts, and
Algebird name the abstraction directly and make it part of the library
vocabulary. Java Stream reductions encode the same law in an API contract
without exposing a reusable `Monoid` interface. Engineering judgement: both
styles are valid. A codebase should copy the style its ecosystem expects. In a
Scala service already using Cats, spelling the law as `Monoid` is ordinary. In
a Java service using only the standard library, a small named reducer may be
clearer than importing abstract algebra vocabulary into every package.

## 10. Consequences

Positive consequences.

- Empty input has one domain answer, not one answer per call site.
- Generic folds, reducers, and partition combiners can be reused across domain
  types.
- Parallel and distributed aggregation can split and merge work when the law is
  valid.
- Composite values can be built from field monoids.
- Code review can ask direct questions: what is the identity, what is the
  combine policy, and do the laws hold?
- Ambiguous carriers can use wrapper types to name the policy.
- Law tests catch subtle changes before an optimization or parallelization
  changes behavior.
- Domain summaries become easier to cache because a cached partial result can
  be merged with later partial results through the same operation.
- APIs can document empty input behavior in one place instead of repeating it
  across endpoints and jobs.

Negative consequences.

- The abstraction can hide the selected policy when instance lookup is implicit.
- Not every useful reducer is associative. Forcing one into Monoid gives false
  confidence.
- Some lawful monoids are lossy. `Last` and `Max` can be correct while throwing
  away information.
- Floating-point operations can surprise teams because finite machine numbers
  do not always behave like algebra over exact numbers.
- Wrapper types add noise to simple code.
- A generic `combineAll` can obscure performance costs, especially allocation
  in immutable nested structures.
- The identity value can mask missing-data errors if the domain does not
  separate "no rows" from "query failed".
- Associativity can be hard to preserve after a product change adds ordering,
  timestamps, or source precedence to a value that used to be a plain summary.
- A lawful generic combine can still violate fairness or trust policy when the
  underlying sources are not equal.

Engineering judgement. The pattern earns its cost when regrouping freedom or
empty-case consistency matters. It does not earn its cost when a single local
loop is clearer and will never be split, reused, or made generic.

## 11. Failure modes and misuse

This dimension is engineering judgement.

- **Symptom.** Parallel results differ from single-threaded results.
  **Cause.** The combine operation is not associative, or it depends on mutable
  external state. **Fix.** Replace it with an ordered fold, redesign the
  aggregate as an associative summary, or keep the non-associative step at the
  final presentation boundary.
- **Symptom.** Empty input silently reports a valid-looking business value.
  **Cause.** The identity was chosen for programmer convenience, not domain
  truth. **Fix.** Return `Option`, `Result`, or a domain error for empty input,
  or split "empty successful query" from "failed query".
- **Symptom.** Reviewers cannot tell whether numbers are added, multiplied, or
  maximized. **Cause.** The carrier type has several monoids and the code uses a
  bare primitive. **Fix.** Introduce wrapper types such as `Sum`, `Product`, or
  `Max`, or pass a named monoid value.
- **Symptom.** Memory rises during large reductions. **Cause.** The combine
  creates large immutable intermediates, such as repeatedly copying maps or
  strings. **Fix.** Use a builder internally, combine chunks in a tree shape, or
  move to a data structure with cheaper concatenation.
- **Symptom.** Logs show duplicate audit entries after retries. **Cause.**
  `combine` performs effects or appends effect descriptions that are executed
  more than once. **Fix.** Make `combine` pure and move effects to a separate
  interpreter with idempotency keys.
- **Symptom.** A new field in an aggregate is always blank after merge.
  **Cause.** The derived product monoid forgot the field or used the wrong
  identity. **Fix.** Add field-level law tests and make construction fail until
  each field has an explicit monoid.
- **Symptom.** Results depend on import order or local implicits.
  **Cause.** Multiple instances for the same carrier are in scope. **Fix.** Use
  newtypes, wrappers, or explicit parameters at boundaries where policy matters.
- **Symptom.** A stream aggregate loses exactness at scale. **Cause.** The
  monoid is an approximate sketch or lossy summary and callers assumed exact
  data. **Fix.** Name the approximation in the type and expose error bounds in
  telemetry and docs.

## 12. Trade-off matrix

| Force | Monoid | Semigroup | Ordered fold | Mutable builder | Reducer with optional result |
|---|---|---|---|---|---|
| Empty input | Returns `empty` | Cannot answer alone | Caller decides | Builder decides | Returns none or error |
| Parallel merge | Strong when laws hold | Strong for non-empty chunks | Weak | Strong only with merge law | Strong after presence check |
| Law surface | Identity plus associativity | Associativity only | Order-specific | Often informal | Presence plus combine |
| Cognitive load | Medium | Medium | Low | Low to medium | Low |
| Policy naming | Strong with wrappers | Strong with wrappers | Often local | Often local | Medium |
| Allocation control | Mixed | Mixed | Good | Strong | Mixed |
| Missing-data safety | Risk if identity lies | Safer for empty input | Caller-specific | Caller-specific | Strong |
| Generic reuse | Strong | Medium | Low | Medium | Medium |

The named alternatives matter. Semigroup is the correct alternative when there
is no identity. Ordered fold is the correct alternative when grouping is part of
the meaning. Mutable builder is the correct alternative when allocation cost is
the dominant force. A reducer returning an optional result is the correct
alternative when empty input is not a value of the carrier.

Engineering judgement. The most common wrong comparison is "Monoid versus no
abstraction." That misses the real design choice. Production code already has
an abstraction once it has more than one reduction site. The choice is whether
the abstraction is named, tested, and reusable, or implicit in scattered seed
values and merge loops.

## 13. Related and incompatible patterns

**Semigroup** is the parent abstraction. It has the associative combine
operation but not the identity. Move from Semigroup to Monoid only when the
identity is honest.

**Fold** is the consumer of the monoid. A fold applies the identity and combine
rule to many values. Monoid supplies the algebra. Fold supplies traversal.

**Reducer** is the broader implementation shape used in JavaScript, Java
Streams, dataflow systems, and UI state management. A reducer becomes monoidal
only when it has identity and associativity.

**Applicative** composes independent contextual values. Monoids often appear
inside applicative validation to combine accumulated errors, warnings, or logs.

**Monad** sequences dependent computations. It can carry monoidal output, as in
writer-style designs, but dependency sequencing is separate from monoidal
combination.

**Composite** can use monoids for tree summaries. Each child returns a summary,
and the parent combines child summaries with the monoid.

**Strategy** can select a monoid at runtime. The selected strategy must still
obey the laws if infrastructure treats it as monoidal.

**Null Object** resembles the identity value but is not the same pattern. A null
object replaces absence with behavior. A monoid identity must participate in an
associative combine operation. A value can be a useful null object and still
fail as a monoid identity.

**Decorator** can attach metadata that later combines through a monoid, such as
trace attributes, warning lists, or validation notes. The danger is silent data
growth. A decorated value that accumulates metadata through many layers needs a
retention policy.

Incompatible patterns and practices are direct. A non-associative combine
conflicts with Monoid. Hidden side effects inside combine conflict with Monoid.
Using one global instance for a carrier that has several valid policies
conflicts with reviewable domain code. A null-object identity conflicts with
Monoid when the null object does not behave as a true identity.

## 14. Refactoring path in and out

To introduce Monoid:

1. Find repeated reductions over the same domain type.
2. Name the carrier and write the combine operation as a pure function.
3. Write three law checks: left identity, right identity, and associativity.
4. Decide whether the empty value is domain truth. If not, stop at Semigroup or
   return an optional result.
5. Place `empty` and `combine` together as a type class instance, trait value,
   static field, or wrapper type.
6. Replace local seed values and local merge code with `combineAll`.
7. For composite values, make every field's monoid explicit.
8. Add telemetry around aggregate size, empty inputs, and merge count before
   moving the reducer into a parallel path.

Named refactorings that apply include Extract Function for the local combine
operation, Introduce Parameter Object for a passed monoid dictionary, Replace
Primitive with Object for wrappers such as `Sum` and `Product`, and Replace
Conditional with Polymorphism when several named policies were selected by a
mode flag.

To remove Monoid:

1. Check whether generic reuse still exists. If one call site remains, inline
   the fold.
2. If the identity caused domain confusion, replace `combineAll` with a
   non-empty fold returning `Option` or `Result`.
3. If performance is the reason, keep the law tests and introduce a mutable
   builder with a documented partition merge.
4. If instance discovery is the reason, replace implicit instances with named
   wrapper types or explicit parameters before deleting the abstraction.
5. Delete wrappers that no longer name a real alternative policy.

Engineering judgement. Do not remove the law tests first. They are the best
description of what must remain true through the refactor.

## 15. Testing and verification

Testing has two layers.

First, test the laws. For a sample of values `x`, `y`, and `z`, verify
`combine(empty, x) == x`, `combine(x, empty) == x`, and
`combine(x, combine(y, z)) == combine(combine(x, y), z`. The test can be a
property test when generators exist, or a table test when the domain is small.
For floating-point values, decide whether approximate equality is allowed and
document that the operation may not be valid for parallel regrouping.

Second, test domain examples. Law tests can prove that a wrong business policy
is internally consistent. A `Last` monoid can be lawful and still wrong for
authorization. Example tests should cover empty input, one input, many inputs,
duplicate keys, conflicting fields, and partitioned reduction. Partition tests
are important: split the same data into several chunk shapes and verify the
same final value.

Useful test doubles are simple. Use an in-memory monoid value rather than a
mock. For telemetry, use a fake recorder and assert that merge count and empty
count are recorded. For failure cases, construct a deliberately unlawful
operation in tests and verify that law tests fail, so the test suite proves it
can catch the mistake.

Property testing fits this pattern well. Generate random values for the carrier,
then test the laws across many triples. For maps, generate overlapping and
non-overlapping keys. For records, generate each field independently. For
wrappers such as `First` and `Last`, generate absent and present values. For
predicate monoids, generate predicates from a small known set and test them
against generated inputs rather than trying to compare function values
directly.

Metamorphic testing is useful for reducers. Feed the same input through several
partition shapes: one chunk, one value per chunk, uneven chunks, and chunks with
empty partitions. The result should match. This catches implementations that
pass ordinary examples but fail under distributed grouping. It also catches
identity bugs because empty partitions become part of the test data.

What becomes easier: generic reducers need fewer example tests because the law
belongs to the supplied monoid. What becomes harder: instance lookup and wrapper
selection need review. In languages with implicit type class search, add tests
at module boundaries that call the exact exported function with realistic
imports.

## 16. Observability signals

This dimension is engineering judgement.

Log the monoid policy name at aggregation boundaries, not for every element.
Useful attributes include `aggregate.type`, `monoid.name`, `input.count`,
`partition.count`, `empty.partition.count`, `combine.count`, and
`result.size.bytes` when the result can grow. For sketch or approximate
monoids, record the configured precision and estimated error where the library
exposes it.

A healthy dashboard shows stable input counts, stable merge counts per job
shape, low empty partition count except for sparse workloads, bounded result
size, and no divergence between single-partition and multi-partition canaries.
A failing dashboard shows result size growth, high empty counts after upstream
filter changes, retry spikes that multiply non-idempotent outputs, or
disagreement between serial and partitioned reductions.

Canaries should compare grouping shapes, not only final job success. Run a small
known dataset through a single partition and a multi-partition path. Alert on
differences. For high-volume systems, sample a small key range or a synthetic
tenant with deterministic data. This is cheap insurance against accidental
changes to associativity after a new field is added.

Tracing should mark partition-local reduction separately from cross-partition
merge. That split helps diagnose whether latency is in element processing or in
combining large summaries. For configuration monoids, expose the source count
and the winning policy for conflict-prone fields. For `First` and `Last`
policies, record the source id of the selected value when privacy rules permit.

## 17. Security and privacy implications

This dimension is engineering judgement.

Monoid is mostly silent about security. It says how values combine, not whether
the values should be visible, retained, encrypted, or trusted. The risk comes
from the domain chosen for the carrier.

Positive security uses exist. A permission summary can combine deny reasons, a
redaction summary can combine required masks, and an audit summary can combine
structured fragments before final emission. In those cases the monoid should be
biased toward safety. For example, combining redaction policies by union is
usually safer than combining by last writer.

Risks:

- Empty identities can bypass controls. An empty allow-list is not the same as
  "no policy loaded" unless the product says so.
- Last-writer-wins merges can let a lower-trust source overwrite a higher-trust
  source.
- Log metadata monoids can accumulate sensitive values from several layers and
  then emit them together.
- Approximate aggregates can still leak sensitive distribution information.
- A combine rule for authorization may be lawful but wrong for the threat
  model. `Any` allow and `All` allow are both lawful boolean monoids, but they
  encode opposite policy instincts.

Mitigations are practical. Name security-sensitive monoids after policy, not
mechanics. Prefer wrapper types such as `DenyWins`, `MaskUnion`, or
`TrustedFirst`. Add domain tests for trust ordering and empty policy load.
Record which source won a conflict. Keep `combine` pure so retries and
regrouping cannot duplicate side effects such as audit writes.

Privacy review should pay attention to accumulation. A single request attribute
may be low risk alone, but a monoidal metadata value can collect attributes from
many middleware layers. The final combined value may cross a logging or
analytics boundary with more detail than any one layer intended to emit. A
privacy-aware monoid should drop, hash, count, or redact fields during combine
when retention is not required.

Security review should also test source precedence. Many merge policies are
lawful only after trust has been encoded into the carrier. For example, "take
the latest setting by timestamp" is a poor rule if an untrusted source can
produce a later timestamp. A safer carrier may include a trust tier, and the
combine rule may select by tier first and timestamp second. The monoid law can
still hold, but the carrier must include the data needed for the policy.

## Code examples

The examples below are intentionally small. Each one models the same pattern:
an identity value, an associative combine operation, and a generic fold.

TypeScript uses an explicit dictionary value. That keeps the selected monoid
visible at the call site.

```typescript
type Monoid<A> = {
  empty: A
  combine: (left: A, right: A) => A
}

type Totals = {
  orders: number
  cents: number
  tags: ReadonlySet<string>
}

const totalsMonoid: Monoid<Totals> = {
  empty: { orders: 0, cents: 0, tags: new Set<string>() },
  combine: (left, right) => ({
    orders: left.orders + right.orders,
    cents: left.cents + right.cents,
    tags: new Set([...left.tags, ...right.tags]),
  }),
}

function combineAll<A>(monoid: Monoid<A>, values: readonly A[]): A {
  return values.reduce(monoid.combine, monoid.empty)
}

const result = combineAll(totalsMonoid, [
  { orders: 2, cents: 5000, tags: new Set(["online"]) },
  { orders: 1, cents: 2500, tags: new Set(["priority"]) },
])

console.log(result.orders, result.cents, [...result.tags].sort().join(","))
```

Python uses a protocol-like class. The law tests are ordinary assertions so the
contract stays close to the implementation.

```python
from dataclasses import dataclass
from typing import Callable, Generic, Iterable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Monoid(Generic[T]):
    empty: T
    combine: Callable[[T, T], T]


def combine_all(monoid: Monoid[T], values: Iterable[T]) -> T:
    result = monoid.empty
    for value in values:
        result = monoid.combine(result, value)
    return result


sum_monoid = Monoid[int](0, lambda left, right: left + right)
values = [3, 4, 5]

assert combine_all(sum_monoid, values) == 12
assert sum_monoid.combine(sum_monoid.empty, 7) == 7
assert sum_monoid.combine(7, sum_monoid.empty) == 7

x, y, z = 2, 9, 11
left = sum_monoid.combine(x, sum_monoid.combine(y, z))
right = sum_monoid.combine(sum_monoid.combine(x, y), z)
assert left == right
print(combine_all(sum_monoid, []), combine_all(sum_monoid, values))
```

Go uses an interface. The `Summary` type demonstrates a product monoid: every
field has its own combine policy.

```go
package main

import "fmt"

type Monoid[T any] interface {
	Empty() T
	Combine(left T, right T) T
}

func CombineAll[T any](m Monoid[T], values []T) T {
	result := m.Empty()
	for _, value := range values {
		result = m.Combine(result, value)
	}
	return result
}

type Summary struct {
	Count int
	Tags  map[string]bool
}

type SummaryMonoid struct{}

func (SummaryMonoid) Empty() Summary {
	return Summary{Count: 0, Tags: map[string]bool{}}
}

func (SummaryMonoid) Combine(left Summary, right Summary) Summary {
	tags := map[string]bool{}
	for key := range left.Tags {
		tags[key] = true
	}
	for key := range right.Tags {
		tags[key] = true
	}
	return Summary{Count: left.Count + right.Count, Tags: tags}
}

func main() {
	values := []Summary{
		{Count: 2, Tags: map[string]bool{"api": true}},
		{Count: 3, Tags: map[string]bool{"batch": true}},
	}
	total := CombineAll[Summary](SummaryMonoid{}, values)
	fmt.Println(total.Count, total.Tags["api"], total.Tags["batch"])
}
```

These samples were compiled or run in this session with `npx tsc`, `python3`,
and `go run`.

## 18. References

- Haskell `base` documentation, `Data.Monoid`, version 4.22.0.0.
  https://hackage.haskell.org/package/base/docs/Data-Monoid.html, verified
  2026-08-02.
- Typelevel Cats documentation, `Monoid` type class.
  https://typelevel.org/cats/typeclasses/monoid.html, verified 2026-08-02.
- fp-ts documentation, `Monoid.ts`.
  https://gcanti.github.io/fp-ts/modules/Monoid.ts.html, verified 2026-08-02.
- Twitter Algebird documentation, abstract algebra for Scala aggregation.
  https://twitter.github.io/algebird/, verified 2026-08-02.
- Oracle, Java SE 21 API documentation, `java.util.stream.Stream`, `reduce`.
  https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Stream.html,
  verified 2026-08-02.
- Saunders Mac Lane, *Categories for the Working Mathematician*, second
  edition, Springer, 1998, chapter I, section 1. Page not cited because the
  page image was not verified in this session.
