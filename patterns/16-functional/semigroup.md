---
name: Semigroup
slug: semigroup
family: 16-functional
category: Functional
aliases: [Associative Combine, Non-empty Reducer, Appendable]
first_described: "Abstract algebra, adopted in software through functional type classes"
maturity: canonical
related: [monoid, magma, fold, reducer, functor, applicative, monad]
incompatible_with: [non-associative-combine, hidden-empty-case, effectful-combine]
verified: 2026-08-02
---

# Semigroup

## 1. Name, aliases, and lineage

The canonical software name is Semigroup. In programming, a semigroup is a type
with one closed binary operation that is associative. Closed means combining two
values of the type returns another value of the same type. Associative means
grouping does not change the result: combining `a` with the result of combining
`b` and `c` gives the same value as combining the result of `a` and `b` with
`c`. Haskell's `Data.Semigroup` documentation describes `Semigroup` as the
class of types with an associative binary operation, names `(<>)` as that
operation, and states the associativity law
(https://hackage.haskell.org/package/base/docs/Data-Semigroup.html, verified
2026-08-02).

The mathematical lineage is abstract algebra. P. B. Bhattacharya, S. K. Jain,
and S. R. Nagpaul, *Basic Abstract Algebra*, Cambridge University Press, 1994,
chapter 4, define a semigroup as a nonempty set with an associative binary
operation. Cambridge Core lists chapter 4 as "Groups", pages 61 to 90, and its
online summary includes the semigroup definition
(https://www.cambridge.org/core/books/abs/basic-abstract-algebra/groups/B094AF8C8F6569FADB7BA8AF290AD852,
verified 2026-08-02). Saunders Mac Lane, *Categories for the Working
Mathematician*, second edition, Springer, 1998, chapter VI section 4, discusses
free semigroups in the categorical setting. I am citing the chapter and section,
not a page number, because I did not verify a page image in this session.

Common software aliases include **associative combine**, **non-empty reducer**,
and **appendable**. The aliases are useful because many languages expose the
pattern without the word Semigroup. Scala Cats defines `Semigroup[A]` with
`combine(x, y): A` and states that the operation must be associative
(https://typelevel.org/cats/typeclasses/semigroup.html, verified 2026-08-02).
fp-ts defines `Semigroup<A>` with `concat(x, y): A` and publishes the same
associativity law for TypeScript users
(https://gcanti.github.io/fp-ts/modules/Semigroup.ts.html, verified
2026-08-02). Haskell uses the operator `(<>)` and can reduce a `NonEmpty` list
with `sconcat`, because a semigroup does not promise a result for an empty
input (https://hackage.haskell.org/package/base/docs/Data-Semigroup.html,
verified 2026-08-02).

The name is often confused with Monoid. A Monoid is a Semigroup plus an identity
value. Haskell's `Data.Semigroup` documentation describes Semigroup as a
generalization of Monoid and says Monoid adds a neutral element, while some
types, such as non-empty lists, do not have that neutral element
(https://hackage.haskell.org/package/base/docs/Data-Semigroup.html, verified
2026-08-02). In software design, this difference matters. Semigroup represents
the case where two valid values can always be merged, but there is no honest
value for zero inputs.

The phrase "Semigroup pattern" in this entry means the software design pattern:
model a merge, append, summary, precedence, or conflict-resolution rule as a
named associative binary operation, then use that rule where code combines two
or more values. It is not a claim that every codebase must import a functional
programming library. It is a claim that once code depends on regrouping, retry,
parallel reduction, or tree-shaped aggregation, associativity becomes part of
the design contract.

## 2. Problem and context

A codebase needs to combine values that are already present. A pipeline merges
two non-empty batches. A validation layer combines two error reports. A pricing
engine combines two non-empty discount traces. A distributed job combines
partition summaries. A UI renderer combines two patches. A permission system
combines two decisions. The operation has a domain name, but the code often
starts as local syntax: `a + b`, `a.merge(b)`, `append(left, right)`, or a
lambda passed to a reducer.

The hidden problem appears when the same operation is used in more than one
shape. A single-threaded path groups values from the left. A parallel path
combines per-worker chunks and then combines the chunk results. A retry path
replays one shard and merges its result with a cached partial value. A batch
path combines daily summaries into weekly summaries and then monthly summaries.
If grouping changes the answer, the system has two meanings for the same
business rule.

Semigroup solves the narrow version of that problem. It puts a closed
associative combine operation behind a name, then makes code that combines
non-empty inputs depend on that name. The pattern does not answer the empty
case. That omission is a feature, not a gap. If the caller has zero inputs, it
must choose a different return type, such as `Option`, `Maybe`, `Result`, or a
domain error, or move to Monoid if an identity value exists.

The context that makes Semigroup valuable has three parts. First, the values are
same-type values. Combining a `LineItem` and a `TaxRate` into a `Receipt` is a
calculation, not a semigroup. Combining two `ReceiptSummary` values into one
`ReceiptSummary` can be a semigroup. Second, the operation is intended to be
associative. It may be order-sensitive, but it must not be grouping-sensitive.
`First`, `Last`, list append, string append, max, min, set union, and map merge
can be semigroups. Subtraction and division are not semigroups under normal
numeric meaning. Third, the code combines at least two values. If one value is
being transformed, use Functor or a plain function. If many values may be empty,
use Monoid or a fold that returns an optional result.

The pattern is common in libraries that expose generic aggregation. Cats shows a
`Map[String, Int]` semigroup that combines maps by combining values for matching
keys (https://typelevel.org/cats/typeclasses/semigroup.html, verified
2026-08-02). fp-ts exposes constructors such as `min`, `max`, `first`, `last`,
`reverse`, `struct`, and `tuple`, letting a TypeScript program select the
specific semigroup it means
(https://gcanti.github.io/fp-ts/modules/Semigroup.ts.html, verified
2026-08-02). Haskell's `Data.Semigroup` lists wrappers such as `Min`, `Max`,
`First`, `Last`, `Dual`, `Sum`, and `Product`
(https://hackage.haskell.org/package/base/docs/Data-Semigroup.html, verified
2026-08-02). These wrappers exist because a raw type can have several lawful
combine policies.

The same pressure exists outside named Semigroup APIs. Java Stream's
`reduce(BinaryOperator<T>)` requires an associative accumulator and returns an
`Optional<T>` because the stream may be empty
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Stream.html,
verified 2026-08-02). That is the Semigroup shape under Java's vocabulary:
combine two values of the same type, require associativity, and do not invent an
identity for empty streams.

Engineering judgement: the pattern earns its place when a reviewer must ask,
"Can this merge happen in another grouping?" If the answer matters, the combine
rule deserves a name and law tests. If the code is a single local append with no
parallelism, no retry, no reuse, and no generic fold, a named Semigroup may be
ceremony.

Another useful context is conflict handling. Many systems receive two valid
facts about the same domain object. A profile service may receive two name
updates. A feature-flag service may receive two rule fragments. A document
editor may receive two patches. The decision is not "merge somehow." It is a
specific policy: keep the earliest value, keep the latest value, append both
values, take the highest priority, retain a conflict, or reject the pair.
Several of those policies can be lawful semigroups. The point of the pattern is
not to make every policy commutative or lossless. The point is to name the exact
policy and prove that regrouping will not change it. Algebird documents `First`
and `Last` as non-commutative semigroups, which is a useful reminder that order
may matter while grouping still must not
(https://twitter.github.io/algebird/datatypes/first_and_last.html, verified
2026-08-02).

## 3. Forces

This dimension is engineering judgement, except where a cited API or law is
named.

- **Coupling.** Favoured. Callers that reduce non-empty values depend on a
  compact algebraic contract, not on each domain type's fields.
- **Consistency.** Favoured when the law holds. Haskell, Cats, and fp-ts all
  publish associativity as the required Semigroup law
  (https://hackage.haskell.org/package/base/docs/Data-Semigroup.html, verified
  2026-08-02; https://typelevel.org/cats/typeclasses/semigroup.html, verified
  2026-08-02; https://gcanti.github.io/fp-ts/modules/Semigroup.ts.html,
  verified 2026-08-02).
- **Latency.** Favoured when the system can combine partitions independently.
  Sacrificed when a generic immutable combine allocates more intermediate
  values than a tuned mutable accumulator.
- **Operability.** Favoured if each semigroup instance has a domain name in
  logs and traces. Sacrificed if generic `combine` calls hide whether the
  policy was max, first, last, append, or union.
- **Cost.** Mixed. The operation is small, but law tests and wrapper types cost
  code review time. That cost buys confidence in regrouping.
- **Team topology.** Favoured when platform teams own generic reducers and
  domain teams own the combine rule for their data.
- **Cognitive load.** Sacrificed for teams unfamiliar with algebraic
  vocabulary. Favoured after adoption, because many merge rules fit one review
  checklist.
- **Security and privacy.** Mixed. A central combine can preserve redaction
  policy. A careless combine can retain data from both inputs when the endpoint
  only needed one side.

The pattern favours lawful regrouping. It sacrifices the comfort of reading a
single local branch. A reader must identify which semigroup instance is in
scope. This is not a small concern. Haskell exposes wrappers such as `Sum` and
`Product` because numbers have more than one lawful semigroup under common
operations (https://hackage.haskell.org/package/base/docs/Data-Semigroup.html,
verified 2026-08-02). fp-ts exposes `first` and `last` as separate instances
because "keep one side" is lawful but policy-bearing
(https://gcanti.github.io/fp-ts/modules/Semigroup.ts.html, verified
2026-08-02).

Semigroup also balances honesty against convenience. Monoid is easier for many
folds because it can return a value for empty input. Semigroup is more honest
when no identity exists. Engineering judgement: returning `None` for an empty
non-empty reduction is often a better API than inventing a fake empty domain
value to satisfy a fold helper.

There is also a force around auditability. A semigroup can make data loss more
visible when the operation is called `KeepFirstDecision` or `MaxRiskScore`. The
same pattern can make data loss harder to see when the operation is an imported
`combine` with no domain name. The law says nothing about whether a discard is
acceptable. Review must still ask which facts survive, which facts are
discarded, and whether the discarded facts should be counted or retained as
evidence.

## 4. Applicability and non-applicability

Reach for Semigroup when these conditions hold.

- Two valid values of the same type can always be combined into another valid
  value of that type.
- The combine operation is associative, so the system may regroup work without
  changing the result.
- The input is known to be non-empty, or the API can return an optional result
  for empty input.
- The domain has no honest identity value, but it has a useful non-empty merge.
- The same operation appears in partition merging, batch summary merging, retry
  recovery, cache merge, conflict resolution, or validation accumulation.
- The raw type has more than one possible combine policy and wrappers can name
  the choice, such as first, last, max, min, sum, product, append, or union.
- A generic reducer, aggregator, or folding abstraction needs a law it can test.

Do not reach for Semigroup in these cases.

- **The operation is not associative.** Observable symptom: results differ
  between a local fold and a partitioned fold. Reason: the grouping affects the
  value. Use an ordered fold or a stateful domain accumulator.
- **The empty case needs a normal value.** Observable symptom: every caller adds
  a pre-check for zero inputs. Reason: Semigroup has no identity. Use Monoid
  when an identity exists, or return an optional result.
- **The empty case is an error.** Observable symptom: a helper returns a default
  that hides missing source data. Reason: Semigroup only handles combining
  present values. Use `Result`, `Either`, an exception boundary, or a domain
  error.
- **The combine has side effects.** Observable symptom: retrying a reduction
  sends duplicate emails, writes duplicate audit rows, or mutates a shared
  cache twice. Reason: associativity only speaks about values, not effects. Use
  Command, Saga, or an explicit effect pipeline.
- **The operation combines different types.** Observable symptom: the operation
  is named `combine` but the input and output types differ. Reason: this is a
  transform or builder, not a closed binary operation. Use Builder, Adapter, or
  a plain function.
- **Order must be globally stable and part of the result.** Observable symptom:
  the same elements give different rendered text after distributed grouping.
  Reason: associativity does not imply commutativity. Use an ordered collection
  plus an ordered fold, or a semigroup that carries enough ordering metadata.
- **The operation is lossy without a named policy.** Observable symptom: one
  side's details disappear and nobody can say whether first, last, max, or min
  was intended. Reason: loss may be valid, but it must be named. Use a wrapper
  such as `First`, `Last`, `Min`, or `Max`.
- **The abstraction hides a simple local rule.** Observable symptom: a reader
  jumps through a type class or interface to find a one-line append used once.
  Reason: the indirection is not buying reuse or regrouping freedom. Keep the
  operation local.

## 5. Structure

The pattern has four participants.

- **Value type.** The domain type being combined. It may be primitive, a record,
  a collection, an error report, a patch, a summary, or a wrapper around another
  type.
- **Combine operation.** A pure closed binary operation from `(A, A)` to `A`.
  It is the law-bearing part of the pattern.
- **Semigroup instance.** The named binding between the value type and the
  combine operation. In type-class languages this may be an instance. In OO
  languages it may be an interface implementation. In dynamic languages it may
  be a small object with a `combine` function.
- **Non-empty consumer.** Code that combines two or more values by depending on
  the Semigroup instance. Examples include `sconcat`, `reduceOption`, a shard
  merger, a validation error accumulator, or a cache entry merge.

Relationships. The non-empty consumer does not know the fields of the value
type. It only asks the Semigroup instance to combine values. The instance may be
selected implicitly by the compiler, passed as an argument, carried on the value
type, or selected by an explicit wrapper. The value type can have more than one
lawful instance when each instance is named. Numbers under addition and numbers
under multiplication are different policies. Records can combine by field. Maps
can combine keys by using the value semigroup. fp-ts documents `struct` and
`tuple` constructors for deriving semigroups from field or element semigroups
(https://gcanti.github.io/fp-ts/modules/Semigroup.ts.html, verified
2026-08-02).

The structure has no identity participant. That absence is deliberate. If an
identity value is present, the structure has become Monoid. Haskell's
`sconcat` takes a `NonEmpty` list for this reason
(https://hackage.haskell.org/package/base/docs/Data-Semigroup.html, verified
2026-08-02).

One structural warning follows from that absence. Do not hide a default inside
the non-empty consumer. A helper named `reduceSemigroup` that returns a
zero-like value for empty input is no longer communicating the contract. It is
either a Monoid fold with an unnamed identity, or it is an error-masking
adapter. The type or function name should tell the reader which one is true.

## 6. ASCII structure diagram

```text
   +---------------------+        uses        +---------------------+
   |  Non-empty consumer | -----------------> |  Semigroup<A>       |
   |---------------------|                    |---------------------|
   | reduce(values)      |                    | combine(A, A): A    |
   +---------------------+                    +----------+----------+
              |                                           |
              | supplies at least two A values            | delegates
              v                                           v
   +---------------------+                    +---------------------+
   | NonEmpty<A>         |                    | Combine operation   |
   |---------------------|                    |---------------------|
   | head: A             |                    | pure, closed,       |
   | tail: List<A>       |                    | associative         |
   +----------+----------+                    +----------+----------+
              |                                           |
              | contains                                  | returns
              v                                           v
   +---------------------------------------------------------------+
   | Value type A                                                   |
   | Same input type on both sides. Same output type after combine. |
   +---------------------------------------------------------------+

   No identity value appears in the structure. Empty input is outside the
   Semigroup contract.
```

## 7. Dynamics

At runtime the consumer reduces a non-empty collection by taking the first
value as the seed and applying the combine operation to each later value. A
tree-shaped or parallel consumer may combine pairs first, then combine the pair
results. Both flows are valid only when associativity holds.

```text
Left fold:

  values:        a          b          c          d
                 |          |          |          |
  start -------- a          |          |          |
                 |          |          |          |
  combine(a,b) --+--------> ab         |          |
                            |          |          |
  combine(ab,c) ------------+--------> abc        |
                                       |          |
  combine(abc,d) ---------------------+--------> abcd


Tree reduction:

  values:        a          b          c          d
                 |          |          |          |
                 +----+-----+          +----+-----+
                      |                     |
                combine(a,b)          combine(c,d)
                      |                     |
                      ab                    cd
                      |                     |
                      +----------+----------+
                                 |
                           combine(ab,cd)
                                 |
                                abcd

  Associativity is the promise that both flows return the same value.
```

The consumer may also be incremental. A cache can store a partial summary and
combine it with a later summary. A stream window can combine worker-local
summaries at the end of a window. A validation routine can combine two error
reports after validating two independent fields. In each case, the consumer
does not need an empty value. It already has at least one value, or it returns
an optional result when it has none. Java Stream's `reduce(BinaryOperator<T>)`
uses that optional-result shape and requires the accumulator to be associative
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Stream.html,
verified 2026-08-02).

## 8. Implementation variants

**Type class instance.** Haskell, Cats, and fp-ts use a type-class style shape.
The consumer asks for a `Semigroup<A>`, and the instance supplies `(<>)`,
`combine`, or `concat` (https://hackage.haskell.org/package/base/docs/Data-Semigroup.html,
verified 2026-08-02; https://typelevel.org/cats/typeclasses/semigroup.html,
verified 2026-08-02; https://gcanti.github.io/fp-ts/modules/Semigroup.ts.html,
verified 2026-08-02). This variant works well when a library owns generic
aggregation and application code supplies domain instances. The trade-off is
instance discovery. Readers must know where instances come from.

**Explicit strategy object.** TypeScript, Java, Go, Python, and Swift can pass a
small object or value that contains the combine function. This is more verbose
than a type class, but the dependency is visible at the call site. It fits
service code where implicit instance selection would surprise readers.

**Method on the value type.** A domain value can expose `merge(other): Self`.
This is direct and easy to discover. The drawback is that a type can only have
one obvious method with that name. If the same value type needs first, last,
max, min, append, and union policies, wrapper types or strategy objects read
better.

**Newtype or wrapper selection.** Haskell's `Data.Semigroup` lists wrappers
including `Min`, `Max`, `First`, `Last`, `Dual`, `Sum`, and `Product`
(https://hackage.haskell.org/package/base/docs/Data-Semigroup.html, verified
2026-08-02). fp-ts exposes constructors for `first`, `last`, `reverse`, `min`,
and `max` (https://gcanti.github.io/fp-ts/modules/Semigroup.ts.html, verified
2026-08-02). The wrapper names the policy and prevents an accidental mix between
policies.

**Derived record and tuple semigroups.** A record can combine field by field
when each field has a semigroup. fp-ts documents `struct` and `tuple`
constructors for that style
(https://gcanti.github.io/fp-ts/modules/Semigroup.ts.html, verified
2026-08-02). The trade-off is policy density. A single derived instance may
hide many field-level choices. A domain type with sensitive fields may need a
hand-written combine to name retention rules.

**Free semigroup.** A free semigroup stores the tree of non-empty values and
postpones interpretation. Algebird documents `Batched` as a free semigroup that
represents a lazy associative combination of values and can recover a value when
a `Semigroup[T]` is available
(https://twitter.github.io/algebird/datatypes/summer/batched.html, verified
2026-08-02). This variant trades memory for control over when combination work
runs.

**Non-empty collection reducer.** Haskell's `sconcat` reduces a `NonEmpty`
collection because a semigroup cannot reduce zero values
(https://hackage.haskell.org/package/base/docs/Data-Semigroup.html, verified
2026-08-02). Java Stream's `reduce(BinaryOperator<T>)` returns `Optional<T>`
because the stream may be empty
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Stream.html,
verified 2026-08-02). Both variants keep the empty case explicit.

**Conflict-preserving semigroup.** A merge can return a value that keeps both
sides when they disagree. For example, a field can be `One(value)` or
`Conflict(non_empty_values)`, and combining two different `One` values can
produce a conflict. This keeps the operation closed while preserving evidence.
The trade-off is larger output and a need for callers to present conflicts to
users or operators.

**Idempotent semigroup.** Some semigroups satisfy `combine(x, x) = x`, such as
set union, max, and min. Haskell's `Data.Semigroup` documents specialized
`stimes` helpers for idempotent semigroups and monoids
(https://hackage.haskell.org/package/base/docs/Data-Semigroup.html, verified
2026-08-02). Idempotence is not required for Semigroup, but it is useful when
retries may send the same partial result more than once.

## 9. Known production uses

- **Haskell `base`, `Data.Semigroup`.** The Haskell `base` library exposes
  `Data.Semigroup`, the `Semigroup` class, the `(<>)` operation, `sconcat`, and
  wrappers such as `Min`, `Max`, `First`, `Last`, `Dual`, `Sum`, and `Product`.
  The documentation says the class has existed since `base-4.9.0.0`
  (https://hackage.haskell.org/package/base/docs/Data-Semigroup.html, verified
  2026-08-02).
- **Cats, `cats.Semigroup`.** Cats documents `Semigroup[A]` with
  `combine(x, y): A`, the associativity law, integer addition, and map merging
  examples (https://typelevel.org/cats/typeclasses/semigroup.html, verified
  2026-08-02).
- **fp-ts, `Semigroup.ts`.** fp-ts documents a TypeScript `Semigroup<A>` with
  `concat(x, y): A`, its associativity law, and constructors and instances such
  as `first`, `last`, `reverse`, `min`, `max`, `struct`, and `tuple`
  (https://gcanti.github.io/fp-ts/modules/Semigroup.ts.html, verified
  2026-08-02).
- **Twitter Algebird.** Algebird describes itself as abstract algebra for Scala
  and says it targets aggregation systems through Scalding, Apache Storm, and
  Summingbird, with broader use at Twitter after its origin in Scalding's Matrix
  API (https://twitter.github.io/algebird/, verified 2026-08-02). Its data type
  docs include semigroup-backed `Min`, `Max`, `First`, `Last`, and `Batched`
  structures (https://twitter.github.io/algebird/datatypes/min_and_max.html,
  verified 2026-08-02;
  https://twitter.github.io/algebird/datatypes/first_and_last.html, verified
  2026-08-02;
  https://twitter.github.io/algebird/datatypes/summer/batched.html, verified
  2026-08-02).
- **Java Stream reduction.** Java does not name the API Semigroup, but
  `Stream.reduce(BinaryOperator<T>)` is a same-type non-empty reduction shape
  with an associative accumulator and optional empty result
  (https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Stream.html,
  verified 2026-08-02). Cite it as a semigroup-shaped standard API, not as a
  library that exposes the Semigroup name.

## 10. Consequences

This dimension is engineering judgement, with cited APIs used where named.

Positive consequences.

- Non-empty reduction gets a clear contract: closed combine plus associativity.
- Parallel and tree reductions have a law to rely on.
- Empty input stays explicit. Haskell uses `NonEmpty` for `sconcat`, and Java
  returns `Optional` for `Stream.reduce(BinaryOperator<T>)`
  (https://hackage.haskell.org/package/base/docs/Data-Semigroup.html, verified
  2026-08-02;
  https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Stream.html,
  verified 2026-08-02).
- Domain policies get names. `First`, `Last`, `Min`, `Max`, `Sum`, `Product`,
  and `Dual` communicate which lawful merge is being used.
- Generic consumers become small. The consumer can reduce any non-empty value
  type with a supplied semigroup.
- Law tests catch refactors that break distributed grouping.

Negative consequences.

- The abstraction can hide the concrete policy if the instance is imported far
  from the call site.
- A type can have many lawful semigroups, so instance selection becomes a design
  question.
- Associativity is easy to claim and easy to violate with timestamps, floating
  point rounding, mutation, or lossy merge.
- Semigroup does not solve empty input. Callers still need `Option`, `Maybe`,
  `Result`, a non-empty type, or Monoid.
- Generic immutable combine can allocate more than a local mutable loop.
- Teams unfamiliar with algebraic laws may treat Semigroup as naming style
  rather than a testable contract.

## 11. Failure modes and misuse

This dimension is engineering judgement.

- **Symptom:** a nightly batch result differs from a streaming result for the
  same records. **Cause:** the combine operation is not associative, often due
  to rounding, sorting, or order-dependent cleanup. **Fix:** write an
  associativity law test, then replace the operation with a lawful summary
  representation or keep the algorithm as an ordered fold.
- **Symptom:** a parallel job changes output when worker count changes.
  **Cause:** the reducer groups partitions differently, and the alleged
  semigroup depends on grouping. **Fix:** test the operation against random
  groupings and make the partition combiner use the tested semigroup.
- **Symptom:** an empty input returns a fake domain value that later reaches a
  customer or ledger. **Cause:** a Semigroup was stretched into a Monoid without
  an honest identity. **Fix:** return an optional result for empty input or
  define a real Monoid only when the domain has an identity.
- **Symptom:** audit logs duplicate after retry. **Cause:** `combine` performs
  side effects while merging values. **Fix:** make `combine` pure and return an
  audit fragment value, then write fragments once at the orchestration boundary.
- **Symptom:** sensitive metadata survives after merging a redacted and an
  unredacted value. **Cause:** field-by-field derived combine kept both sides
  without a privacy policy. **Fix:** hand-write the semigroup for that domain
  type and name the redaction rule.
- **Symptom:** a map merge drops conflicts silently. **Cause:** the value
  semigroup for duplicate keys keeps first or last without a visible wrapper.
  **Fix:** use a conflict type, a non-empty list of values, or a named wrapper
  such as `First` or `Last`.
- **Symptom:** code review debates whether `+` means addition, append, max, or
  last-write-wins. **Cause:** the raw operator hides multiple lawful policies.
  **Fix:** introduce policy wrappers or pass an explicit semigroup object.
- **Symptom:** performance worsens after replacing a tuned loop with generic
  combine. **Cause:** immutable intermediate values allocate at each step.
  **Fix:** keep the semigroup as the correctness contract, then add a batched or
  builder-backed implementation with the same final law.

## 12. Trade-off matrix

| Force | Semigroup | Monoid | Ordered Fold | Strategy |
|---|---|---|---|---|
| Empty input | Refuses or returns optional | Returns identity | Caller decides | Caller decides |
| Associativity | Required | Required | Not required | Depends on strategy |
| Parallel reduction | Good when law holds | Good when law holds | Poor unless ordered | Depends on strategy |
| Domain honesty | High when no identity exists | High only with real identity | High but local | High if named |
| Cognitive load | Medium, law vocabulary | Medium, law plus identity | Low locally | Low to medium |
| Instance ambiguity | Medium to high | Medium to high | Low | Low when explicit |
| Runtime cost | Low abstraction cost, possible allocation | Same plus identity | Lowest for local loop | Varies |
| Empty-case safety | High if optional or non-empty | High with true identity | Varies by caller | Varies by caller |
| Best fit | Non-empty merge | Empty-capable aggregation | Order-sensitive logic | Runtime policy choice |

Monoid is the nearest related pattern. Use it when a real identity value exists.
Ordered Fold is the honest alternative when grouping affects the answer.
Strategy is the broader behavioral pattern when the choice among algorithms is
more important than the associativity law.

## 13. Related and incompatible patterns

**Monoid** extends Semigroup with an identity value. If the empty case can
return a real value of the same type, Monoid can replace Semigroup. If no such
value exists, forcing Monoid creates bad defaults.

**Magma** is weaker than Semigroup. It has a closed binary operation but no
associativity requirement. Use the Magma vocabulary only when regrouping is not
allowed.

**Fold** consumes a sequence. A Semigroup can power a fold over a non-empty
sequence. A Monoid can power a fold over a possibly empty sequence. An ordered
fold can handle operations that are not associative.

**Reducer** is the implementation role that applies the operation across a
collection. Semigroup is the law for one kind of reducer.

**Strategy** composes with Semigroup when callers choose among several lawful
combine policies at runtime. The Strategy object may be the Semigroup instance.

**Composite** can use Semigroup when combining child results into a parent
result. It conflicts only if tree shape affects the result, because Composite
often changes grouping.

**Command** is a better fit for side effects. If the combine operation writes to
an external system, it is not a Semigroup combine. Combine command descriptions
as values, then execute later.

**Applicative** and **Monad** compose with Semigroup in validation and effect
systems. For example, error accumulation often uses a Semigroup for errors
while the outer effect type controls success and failure. This entry does not
claim any one validation API, because the exact shape differs by library.

Incompatible patterns include hidden empty-case defaults, effectful combines,
and non-associative reducers presented as parallel-safe operations.

## 14. Refactoring path in and out

To introduce Semigroup into existing code:

1. Find two or more call sites that combine same-type values with the same
   domain rule.
2. Write the operation as a pure `(A, A) -> A` function.
3. Add three tiny examples that prove closure, left grouping, and right
   grouping for representative values.
4. Add a property test for associativity where the domain can generate random
   values.
5. Name the policy. Prefer names such as `ReportSummaryAppend`,
   `ValidationErrorsAppend`, `LatestTimestamp`, or `MaxPriority` over a vague
   `DefaultSemigroup`.
6. Change one non-empty reducer to depend on the named operation.
7. Keep empty input outside the helper. Use a non-empty type or return an
   optional value.
8. Convert the remaining call sites after the law test protects the behavior.

Named refactorings from the refactoring catalog often appear around this move.
Use Extract Function when the combine logic is buried in a loop. Use Extract
Class or Introduce Parameter Object when a merge policy needs a named object.
Use Replace Conditional with Polymorphism or Strategy when a switch chooses
among several combine policies. Use Replace Temp with Query when intermediate
merge state hides the actual operation.

To remove Semigroup when it stops earning its place:

1. Count call sites. If only one remains, inline the operation unless the law is
   still part of a public API.
2. Check whether an identity value has become honest. If yes, migrate to Monoid.
3. Check whether grouping is no longer free. If order now matters, replace the
   semigroup consumer with an ordered fold.
4. Inline wrapper types whose only role was to pick a policy no caller can
   confuse now.
5. Keep the associativity tests until the replacement tests cover the same
   production risk.

Engineering judgement: the safest migration is not "functionalize everything."
It is to name one repeated merge policy, test the law, and let that proof decide
whether the abstraction belongs.

## 15. Testing and verification

This dimension is engineering judgement, with API citations where named.

The main test is associativity. For representative values `a`, `b`, and `c`,
check that `combine(combine(a, b), c)` equals `combine(a, combine(b, c))`.
Haskell, Cats, and fp-ts publish that law as the Semigroup requirement
(https://hackage.haskell.org/package/base/docs/Data-Semigroup.html, verified
2026-08-02; https://typelevel.org/cats/typeclasses/semigroup.html, verified
2026-08-02; https://gcanti.github.io/fp-ts/modules/Semigroup.ts.html, verified
2026-08-02).

Use example tests for named policies. `First(a, b)` should keep `a`. `Last(a,
b)` should keep `b`. `Max` should keep the larger ordered value. `Min` should
keep the smaller ordered value. List append should preserve left-to-right
order. Map merge should explain duplicate-key behavior. The example is not only
a test. It is policy documentation.

Use property tests when values can be generated safely. Generate three values
and compare left-grouped and right-grouped results. If values carry timestamps,
IDs, redaction state, or floating-point numbers, bias generators toward equal
timestamps, missing fields, redacted fields, `NaN`, infinity, and boundary
values. The odd cases are where false semigroups tend to break.

Test non-empty and empty consumers separately. A `NonEmpty` reducer should not
accept empty input. A possibly empty reducer should return an optional result,
or it should move to Monoid. Java Stream's same-type `reduce` without identity
returns `Optional<T>` for this reason
(https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Stream.html,
verified 2026-08-02).

Test regrouping directly for distributed code. Feed the same values through a
left fold, a right fold, a balanced tree fold, and random partition folds. The
result should match. If it does not, either the operation is not a Semigroup or
the equality relation is wrong for the domain.

Use mutation and side-effect checks for critical code. Run combine twice with
the same inputs and compare outputs. Verify that inputs are not mutated unless
mutation is part of a private builder path hidden behind a pure result. Verify
that no external write occurs in combine. A semigroup operation should be a
value operation.

For lossy policies, test the loss. A `First` policy should prove that the right
value is discarded. A `Last` policy should prove that the left value is
discarded. A max policy should test equal priorities. A map-merge policy should
test duplicate keys. These tests make policy loss visible, which is more useful
than only testing a happy path where no conflict occurs.

For records, test fields independently and together. Field tests catch the
wrong primitive semigroup. Whole-record tests catch copy-paste errors, missing
fields, and unsafe derivation. If a new field is added to the record, the test
should fail until the field's combine policy is chosen.

## 16. Observability signals

This dimension is engineering judgement.

Log the semigroup policy name at boundaries where grouping can vary. Useful
fields include `combine.policy`, `combine.input_count`, `combine.grouping`,
`combine.partition_count`, `combine.conflict_count`, and
`combine.output_size`. Do not log raw values unless the domain permits it. For
privacy-sensitive values, log counts and policy names, not payloads.

Trace partitioned reductions with the same policy name on every worker and on
the final merge. A healthy trace shows stable policy names, expected partition
counts, and bounded output growth. A failing trace often shows high conflict
counts, output size growing faster than input size, or a fallback path that
uses a different policy.

Metrics should answer four questions. How many values were combined? How many
combine calls ran? How many conflicts or duplicate keys were seen? How large is
the resulting value? For append-like semigroups, watch output size. For map
merge, watch duplicate-key count. For first and last policies, watch the number
of discarded alternatives. For validation accumulation, watch error count and
field count.

Dashboards should compare groupings when the system has both streaming and
batch paths. A batch total and a streaming total that diverge on the same input
window are a strong signal that a law, equality relation, or data selection
rule has changed. This is not proof that Semigroup is wrong. It is a pointer to
the place where associativity was assumed.

Add a counter for empty input at the adapter boundary. Semigroup does not handle
empty input, so a spike in empty reductions may reveal a caller that should use
Monoid, optional result, or a domain error. Treat "empty coerced to default" as
an incident in financial, billing, permission, and medical systems.

Record regrouping mode where it can change between deployments. Values such as
`left_fold`, `balanced_tree`, `worker_partitioned`, and `cache_merge` help an
operator compare two paths that should be equivalent. When a new optimization
changes grouping, the dashboard should make that visible on the first run, not
after a customer reports a mismatch.

## 17. Security and privacy implications

This dimension is engineering judgement.

Semigroup is silent about security by itself. Its risk comes from centralizing a
merge policy that may retain, drop, or expose data. That centralization can help
when the policy is reviewed, named, and tested. It can hurt when a generic
field-by-field combine retains data the endpoint should have discarded.

For privacy-sensitive records, do not derive the semigroup blindly. Decide each
field. Some fields should append, some should take max confidence, some should
prefer redacted over unredacted, some should keep only a count, and some should
fail on conflict. A derived `struct` semigroup is convenient, but it should not
be the default for secrets, health data, financial details, access tokens, or
audit records.

For authorization decisions, name the policy. `AnyAllow`, `AllAllow`,
`DenyOverrides`, and `LastDecision` have different security meanings. Some are
lawful semigroups, but lawfulness does not mean the policy is safe. A lawful
"last decision wins" merge can still be a security bug when evaluation order is
attacker-influenced.

For audit and legal records, avoid lossy combine unless the loss is the product
requirement. `First` and `Last` are useful policies, and Algebird documents
`First` and `Last` as non-commutative semigroups
(https://twitter.github.io/algebird/datatypes/first_and_last.html, verified
2026-08-02). Losing the other side may be unacceptable for audit evidence. Use
a non-empty list of alternatives or a conflict record when both sides must
remain inspectable.

For distributed systems, a semigroup combine should be deterministic. If it
reads wall-clock time, random numbers, mutable process state, or network data,
then two legal groupings may return different values. That breaks correctness
and can create security gaps when retries or shard counts are attacker-visible.

## Code examples

The examples are intentionally small. They model validation error accumulation,
report summary merging, and non-empty reduction. They were run locally with
`node`, `python3`, and `go`.

TypeScript.

```typescript
type Semigroup<A> = {
  combine: (left: A, right: A) => A;
};

type ValidationErrors = {
  fields: Record<string, string[]>;
};

const errorsSemigroup: Semigroup<ValidationErrors> = {
  combine(left, right) {
    const fields: Record<string, string[]> = { ...left.fields };
    for (const [field, messages] of Object.entries(right.fields)) {
      fields[field] = [...(fields[field] ?? []), ...messages];
    }
    return { fields };
  },
};

function reduceNonEmpty<A>(values: [A, ...A[]], sg: Semigroup<A>): A {
  return values.slice(1).reduce((acc, value) => sg.combine(acc, value), values[0]);
}

const a = { fields: { email: ["missing"] } };
const b = { fields: { email: ["invalid"], name: ["blank"] } };
const c = { fields: { name: ["too short"] } };

const left = errorsSemigroup.combine(errorsSemigroup.combine(a, b), c);
const right = errorsSemigroup.combine(a, errorsSemigroup.combine(b, c));

console.log(JSON.stringify(left) === JSON.stringify(right));
console.log(reduceNonEmpty([a, b, c], errorsSemigroup).fields.email.length);
```

Python.

```python
from dataclasses import dataclass
from typing import Callable, Generic, Iterable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Semigroup(Generic[T]):
    combine: Callable[[T, T], T]


@dataclass(frozen=True)
class ReportSummary:
    orders: int
    revenue_cents: int
    warnings: tuple[str, ...]


summary_semigroup = Semigroup(
    lambda left, right: ReportSummary(
        orders=left.orders + right.orders,
        revenue_cents=left.revenue_cents + right.revenue_cents,
        warnings=left.warnings + right.warnings,
    )
)


def reduce_non_empty(first: T, rest: Iterable[T], sg: Semigroup[T]) -> T:
    result = first
    for value in rest:
        result = sg.combine(result, value)
    return result


a = ReportSummary(orders=2, revenue_cents=4500, warnings=("late",))
b = ReportSummary(orders=3, revenue_cents=1200, warnings=())
c = ReportSummary(orders=1, revenue_cents=900, warnings=("manual",))

left = summary_semigroup.combine(summary_semigroup.combine(a, b), c)
right = summary_semigroup.combine(a, summary_semigroup.combine(b, c))

print(left == right)
print(reduce_non_empty(a, [b, c], summary_semigroup))
```

Go.

```go
package main

import "fmt"

type Semigroup[T any] struct {
	Combine func(T, T) T
}

type Patch struct {
	Ops []string
}

func ReduceNonEmpty[T any](first T, rest []T, sg Semigroup[T]) T {
	result := first
	for _, value := range rest {
		result = sg.Combine(result, value)
	}
	return result
}

func main() {
	patches := Semigroup[Patch]{
		Combine: func(left Patch, right Patch) Patch {
			ops := append([]string{}, left.Ops...)
			ops = append(ops, right.Ops...)
			return Patch{Ops: ops}
		},
	}

	a := Patch{Ops: []string{"title"}}
	b := Patch{Ops: []string{"body"}}
	c := Patch{Ops: []string{"footer"}}

	left := patches.Combine(patches.Combine(a, b), c)
	right := patches.Combine(a, patches.Combine(b, c))

	fmt.Println(fmt.Sprint(left.Ops) == fmt.Sprint(right.Ops))
	fmt.Println(ReduceNonEmpty(a, []Patch{b, c}, patches).Ops)
}
```

## 18. References

- P. B. Bhattacharya, S. K. Jain, and S. R. Nagpaul. *Basic Abstract Algebra*.
  Cambridge University Press, 1994. Chapter 4, "Groups", pages 61 to 90 as
  listed by Cambridge Core. URL verified 2026-08-02:
  https://www.cambridge.org/core/books/abs/basic-abstract-algebra/groups/B094AF8C8F6569FADB7BA8AF290AD852
- Saunders Mac Lane. *Categories for the Working Mathematician*. Second
  edition. Springer, 1998. Chapter VI section 4, "Words and Free Semigroups";
  chapter VII section 3, "Monoids". Cited by chapter and section only.
- Haskell `base` documentation. `Data.Semigroup`, `base-4.22.0.0`. URL
  verified 2026-08-02:
  https://hackage.haskell.org/package/base/docs/Data-Semigroup.html
- Typelevel Cats documentation. `Semigroup`. URL verified 2026-08-02:
  https://typelevel.org/cats/typeclasses/semigroup.html
- fp-ts documentation. `Semigroup.ts`. URL verified 2026-08-02:
  https://gcanti.github.io/fp-ts/modules/Semigroup.ts.html
- Twitter Algebird documentation. Home page. URL verified 2026-08-02:
  https://twitter.github.io/algebird/
- Twitter Algebird documentation. `Min and Max`. URL verified 2026-08-02:
  https://twitter.github.io/algebird/datatypes/min_and_max.html
- Twitter Algebird documentation. `First and Last`. URL verified 2026-08-02:
  https://twitter.github.io/algebird/datatypes/first_and_last.html
- Twitter Algebird documentation. `Batched`. URL verified 2026-08-02:
  https://twitter.github.io/algebird/datatypes/summer/batched.html
- Oracle Java SE 21 API documentation. `java.util.stream.Stream`. URL verified
  2026-08-02:
  https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Stream.html
