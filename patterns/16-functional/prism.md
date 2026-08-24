---
name: Prism
slug: prism
family: 16-functional
category: Functional
aliases: [Prism Optic, Partial Iso, Sum Optic, Variant Optic]
first_described: "Optics folklore, formalized by Pickering, Gibbons, Wu 2017"
maturity: established
related: [lens, optional, traversal, iso, profunctor, sum-type]
incompatible_with: [total-lens-for-variant, many-focus-traversal, validation-as-optic]
verified: 2026-08-02
---

# Prism

## 1. Name, aliases, and lineage

The canonical software name is Prism. In the optics family, a prism is a
first-class accessor for one case of a sum type. Monocle describes `Prism[S, A]`
as an optic used to select one part of a sum type, with `S` standing for the sum
and `A` for the selected case
(https://www.optics.dev/Monocle/docs/optics/prism, verified 2026-08-02).
optics-ts gives the same practical shape by classifying `Prism` as a read and
write optic with zero or one focus
(https://akheron.github.io/optics-ts/reference-intro/, verified 2026-08-02).

The lineage is less clean than the GoF patterns because prisms grew inside the
functional optics community rather than through one catalog entry. The 2017
paper by Matthew Pickering, Jeremy Gibbons, and Nicolas Wu, "Profunctor Optics.
Modular Data Accessors", published in *The Art, Science, and Engineering of
Programming*, volume 1, issue 2, article 7, treats fields of records, variants
of unions, and elements of containers as data accessors under the shared name
optics. Its publication metadata records the article, DOI, and date, and the
abstract names variants of a union as one of the motivating accessor targets
(https://programming-journal.org/2017/1/7/, verified 2026-08-02). The same
article states the concrete prism representation in section 4.3 as a matcher
from a structure into either an unchanged fallback or a focus, paired with a
builder from the focus back to the structure. That source is the main formal
lineage for this entry.

Common aliases are **prism optic**, **sum optic**, **variant optic**, and
**partial iso**. The "partial iso" name is useful but incomplete. Haskell
`lens` says a prism can be thought of as an `Iso` that can be partial in one
direction, and also states that every `Prism` is a valid `Traversal`
(https://hackage.haskell.org/package/lens-3.7.0.1/docs/Control-Lens-Prism.html,
verified 2026-08-02). The phrase should not be stretched too far. A prism can
construct a whole value from a focus, but it may fail to extract that focus from
an arbitrary whole value.

The term is sometimes confused with Optional. In many libraries a prism and an
optional both represent zero or one focus. The difference is construction. A
prism has a reverse direction that can inject a focus into the larger type.
Monocle names that operation `reverseGet`, also usable as `apply`
(https://www.optics.dev/Monocle/docs/optics/prism, verified 2026-08-02).
monocle-ts exposes the same pair in its `Prism<S, A>` interface,
`getOption: (s: S) => Option<A>` and `reverseGet: (a: A) => S`
(https://gcanti.github.io/monocle-ts/modules/Prism.ts.html, verified
2026-08-02).

This entry uses Prism for the application programming pattern, not for the
category-theoretic proof object alone. The proof matters because it explains why
composition works. The engineering value is concrete: represent a branch of a
closed or disciplined union as a reusable value, then reuse that branch selector
for preview, modification, construction, testing, and composition.

## 2. Problem and context

A program models alternatives. A payment can be pending, authorized, captured,
or failed. A command can be local, remote, or scheduled. A parsed token can be a
number, string, keyword, or delimiter. The code often needs to work only with
one variant while leaving every other variant alone.

The first version is usually a direct pattern match. That is fine while the case
logic appears once. The problem appears when the same variant test spreads
across read paths, update paths, serialization, UI reducers, metrics filters,
and migration code. Each place repeats the same branch test. Some places read
the payload. Some places rebuild the variant. Some places modify the payload
only when the variant matches. Over time, the branch logic becomes a local
protocol with no name.

Prism gives that protocol a value. It packages two operations. The first is a
partial match from the whole sum to the payload. The second is an infallible
constructor from the payload back to the whole sum. Monocle documents the
constructor pair as `getOption` and `reverseGet`
(https://www.optics.dev/Monocle/docs/optics/prism, verified 2026-08-02). In
plain terms: "Can this whole value be viewed as this case?" and "Build this case
from its payload."

The context is value-oriented code. A prism is most useful when a branch can be
treated as data rather than as a one-off control statement. It fits algebraic
data types, discriminated unions, sealed traits, enum associated values, tagged
JSON shapes, result types, option types, state machines, compiler AST nodes,
domain events, protocol messages, and other sum-like structures. It is less
useful when an object hierarchy already uses virtual dispatch for each branch
and the operation naturally belongs on the object.

The pattern also addresses asymmetric construction. A lens can read a field from
every whole value and can rebuild every whole value with a new field. A prism
cannot read a focus from every whole value. It can, however, always build a
whole value from a focus. That asymmetry matches sum types. Every string token
contains a string payload, but not every token is a string token. Every failed
payment contains a failure reason, but not every payment is failed.

The practical payback arrives through composition. A prism for "this token is a
string" can compose with a lens for "the string token's text" and with another
optic for a nested payload. Monocle documents prism composition and shows a JSON
number prism composed with a `Double` to `Int` prism
(https://www.optics.dev/Monocle/docs/optics/prism, verified 2026-08-02).
optics-ts documents the composition rules for optics and says an `Iso` composed
with a `Prism` yields a `Prism`
(https://akheron.github.io/optics-ts/reference-intro/, verified 2026-08-02).

Engineering judgement. Prism earns its place when variant access is repeated,
composed, or exported. If the branch logic appears once, a match expression is
often clearer. If branch selection is being used to enforce business policy, a
domain method may be the better home. Prism should remove repeated structural
noise, not hide a decision that deserves a name in the domain language.

## 3. Forces

This dimension is engineering judgement, except where a cited source describes a
library or formal relationship.

- **Coupling.** Favoured. Callers depend on a named branch optic rather than on
  hand-written case analysis. If the branch representation moves but the prism
  remains lawful, callers keep their shape.
- **Consistency.** Favoured when laws are tested. Monocle states round-trip laws
  for `getOption` and `reverseGet`, and monocle-ts lists equivalent laws for
  `Prism` (https://www.optics.dev/Monocle/docs/optics/prism, verified
  2026-08-02; https://gcanti.github.io/monocle-ts/modules/Prism.ts.html,
  verified 2026-08-02).
- **Latency.** Mixed. A prism adds function calls around a branch test. The
  branch test already exists in manual code, but a deeply composed optic can add
  visible overhead in hot parsing, routing, or reducer loops.
- **Allocation cost.** Mixed. A successful modification rebuilds the matching
  branch. An unsuccessful modification commonly returns the original value. That
  no-match path is cheap if the implementation preserves identity, and less
  cheap if it copies defensively.
- **Operability.** Favoured if the prism has a domain name. A trace field such
  as `optic=failed_payment_reason` is easier to read than repeated anonymous
  match expressions. Sacrificed if composed optics are logged only as library
  combinators.
- **Team topology.** Favoured when platform or domain-model teams publish
  branch optics for shared event or command types. Feature teams can add focused
  logic without editing every consumer's matches.
- **Cognitive load.** Sacrificed. A reader must know why a prism can miss, why
  its reverse direction cannot miss, and how it differs from Lens, Optional, and
  Traversal.
- **Cost of change.** Favoured for representation changes behind a stable prism.
  Sacrificed when public prisms freeze a variant as a supported API before the
  domain model has settled.
- **Consistency of absence.** Favoured. Missing focus is part of the return
  shape, usually `Option`, `Maybe`, `undefined`, `Result`, or `None`, rather
  than an exception or sentinel.
- **Security and privacy.** Mixed. A named prism can centralize permitted
  access to sensitive variants. It can also make extracting those variants too
  convenient unless module boundaries are respected.

Prism favours branch reuse, composition, and explicit absence. It sacrifices
direct control-flow readability and adds a small abstraction cost.

## 4. Applicability and non-applicability

Reach for Prism when the following hold.

- A type is a sum, discriminated union, sealed hierarchy, enum with associated
  data, `Option`, `Either`, `Result`, or equivalent tagged shape.
- One branch is inspected, modified, or constructed in several places.
- The branch access needs to compose with lenses, optionals, traversals, or
  other prisms.
- A library boundary should expose branch access without exposing all
  constructors or representation details.
- The extraction can fail, but construction from the focus to the whole cannot
  fail.
- The team can state and test the round-trip laws for custom prisms.
- A no-match update should leave the whole value unchanged.
- The type system can carry the focus type without falling back to unchecked
  reflection or broad dynamic casts.

Do NOT reach for Prism in these cases.

- **The focus is always present.** Use Lens or Iso. A prism that never misses
  adds absence handling where no absence exists.
- **The focus may appear many times.** Use Traversal or Fold. A prism represents
  zero or one focus, not all matching children.
- **The update must create the missing branch during set.** Standard prism
  modification leaves non-matching values alone. If `set` on a missing focus
  should insert a value, the operation is a domain transformation or an upsert,
  not a prism update.
- **The branch test depends on external state.** A prism matcher should be a
  pure structural test. If it reads a database, calls a service, checks time, or
  consults permissions, use a function returning a domain result.
- **Construction can fail.** If a payload must be validated before it becomes a
  whole value, do not hide that failure behind `reverseGet`. Use a smart
  constructor or a validation type, then build a prism over the validated type.
- **The branch has side effects.** A prism is an accessor. It should not publish
  messages, increment counters, mutate caches, or perform I/O during preview or
  construction.
- **The operation is naturally behavior polymorphism.** If each branch owns a
  different algorithm, virtual dispatch, a visitor, or pattern matching may say
  more than an extracted payload.
- **The branch is private by design.** Exporting a prism exposes that the branch
  exists and makes it part of the compatibility contract.
- **The language cannot express the union safely.** A hand-built prism over
  untyped maps may be useful at a boundary, but inside core code it can become a
  typed-looking wrapper around unchecked string keys.
- **The code reads better as one local match.** A single branch in one function
  does not need an optic value.

The non-applicability rule of thumb is simple. Prism is for reusable structural
branch access. It is not a replacement for validation, authorization, effectful
lookup, object behavior, or business workflow.

## 5. Structure

Six participants define the pattern.

- **Whole sum.** The larger type that has several alternatives. In type
  notation this is often `S`.
- **Focused case.** The one alternative the prism targets. In type notation this
  is often `A`.
- **Matcher.** A pure function from whole sum to optional focus. Monocle calls
  this `getOption`; monocle-ts uses the same name
  (https://www.optics.dev/Monocle/docs/optics/prism, verified 2026-08-02;
  https://gcanti.github.io/monocle-ts/modules/Prism.ts.html, verified
  2026-08-02).
- **Builder.** A pure function from focus to whole sum. Monocle calls this
  `reverseGet`, and Haskell `lens` exposes the reverse direction through
  functions such as `review` and `remit`
  (https://www.optics.dev/Monocle/docs/optics/prism, verified 2026-08-02;
  https://hackage.haskell.org/package/lens-3.7.0.1/docs/Control-Lens-Prism.html,
  verified 2026-08-02).
- **Prism value.** The reusable package containing the matcher and builder, or a
  profunctor representation equivalent to that package.
- **Optic operations.** Generic operations such as preview, review, modify, set,
  compose, and convert to Optional or Traversal. monocle-ts documents `modify`,
  `modifyOption`, `set`, `asOptional`, `asTraversal`, and prism composition
  (https://gcanti.github.io/monocle-ts/modules/Prism.ts.html, verified
  2026-08-02).

The laws make the structure more than two convenient functions. The first law
says that if the prism matches a whole value and then rebuilds from that focus,
the result is the original whole value. The second says that if the prism builds
from a focus and then previews through the same prism, the result is that focus.
Monocle states both round-trip directions for matching values
(https://www.optics.dev/Monocle/docs/optics/prism, verified 2026-08-02).

For polymorphic prisms, the whole and focus can change type during update. The
Haskell `lens` constructor uses `(b -> t)` and `(s -> Either t a)`, which permits
different source, target, old focus, and new focus types
(https://hackage.haskell.org/package/lens-3.7.0.1/docs/Control-Lens-Prism.html,
verified 2026-08-02). Many application implementations use the simpler
monomorphic shape because it is easier to teach and easier to encode in
mainstream languages.

## 6. ASCII structure diagram

```text
             Whole sum S
   +================================+
   | Variant A(payload A)           |
   | Variant B(payload B)           |
   | Variant C                      |
   +================================+
                 |
                 | preview / getOption
                 v
          +================+
          |  Option[A]     |
          |  Some(payload) |
          |  None          |
          +================+

          +================+
          | payload A      |
          +================+
                 |
                 | review / reverseGet
                 v
   +================================+
   | Whole sum S as Variant A       |
   +================================+

   Prism[S, A] = matcher S -> Option[A]
               + builder A -> S
```

## 7. Dynamics

At runtime a prism has two directions. The read direction may fail. The build
direction does not fail. The modify direction combines both.

```text
Client             Prism[S,A]          Whole S              Focus A
  |                    |                  |                    |
  |.. preview(s) ....>.|                  |                    |
  |                    |.. match(s) ....>.|                    |
  |                    |<.. Some(a) ......|                    |
  |<.. Some(a) ........|                  |                    |
  |                    |                  |                    |
  |.. review(a) .....>.|                  |                    |
  |                    |.. build(a) ..........................>|
  |                    |<.. S as target case ..................|
  |<.. S ..............|                  |                    |
  |                    |                  |                    |
  |.. modify(f, s) ..>.|                  |                    |
  |                    |.. match(s) ....>.|                    |
  |                    |<.. Some(a) ......|                    |
  |                    |.. f(a) ..............................>|
  |                    |<.. b ................................|
  |                    |.. build(b) ..........................>|
  |<.. updated S ......|                  |                    |
  |                    |                  |                    |
  |.. modify(f, s2) .>.|                  |                    |
  |                    |.. match(s2) ...>.|                    |
  |                    |<.. None .........|                    |
  |<.. original s2 ....|                  |                    |
```

The key runtime property is no-match preservation. Monocle shows `replace` and
`modify` leaving a JSON number unchanged when the prism targets a JSON string
(https://www.optics.dev/Monocle/docs/optics/prism, verified 2026-08-02).
optics-ts describes the same behavior for `set` and `modify` through an
`optional` prism: if the prism does not match, the value is unchanged
(https://akheron.github.io/optics-ts/tutorial/, verified 2026-08-02).

Composition changes the result optic according to the weakest access guarantee.
A prism followed by a lens still has zero or one focus, so the result is
prism-like in many APIs. A lens followed by a prism cannot promise a focus, so
it is no longer a lens. The Monocle composition table records combinations among
Prism, Lens, Optional, Traversal, and other optics
(https://www.optics.dev/Monocle/docs/optics, verified 2026-08-02).

## 8. Implementation variants

**Pair of functions.** The direct implementation stores a matcher and a builder.
This is the form shown by Monocle and monocle-ts
(https://www.optics.dev/Monocle/docs/optics/prism, verified 2026-08-02;
https://gcanti.github.io/monocle-ts/modules/Prism.ts.html, verified
2026-08-02). It maps cleanly to TypeScript, Python, Go, Rust, Java, and Swift.
The cost is that composition helpers must be written by the application or
imported from a library.

**Pattern-match constructor.** Some libraries build prisms from a partial
function and a constructor. Monocle documents `Prism.partial`, which takes a
Scala `PartialFunction`, plus a constructor
(https://www.optics.dev/Monocle/docs/optics/prism, verified 2026-08-02). This
variant reads naturally in languages with pattern matching. The risk is hidden
partiality if the language does not make the failed match explicit.

**Generated prisms.** A macro, derive step, or code generator can emit one prism
per branch. Monocle documents `GenPrism` for subclasses
(https://www.optics.dev/Monocle/docs/optics/prism, verified 2026-08-02).
Generation reduces boilerplate and law mistakes for plain variants. It can also
export too much surface area if every internal case becomes public.

**Predicate prism.** A prism can narrow a type by predicate when construction is
identity. monocle-ts documents `fromPredicate`
(https://gcanti.github.io/monocle-ts/modules/Prism.ts.html, verified
2026-08-02). optics-ts documents `guard` as a way to create a prism from a type
guard (https://akheron.github.io/optics-ts/reference-standalone/, verified
2026-08-02). This works for type refinements, but it is only lawful when every
built value passes the predicate.

**Library optic hierarchy.** Some libraries place Prism among a family of optics
and provide conversions. monocle-ts exposes `asOptional` and `asTraversal`
(https://gcanti.github.io/monocle-ts/modules/Prism.ts.html, verified
2026-08-02). optics-ts lists Prism, RemovablePrism, Traversal, Getter, Fold,
and other optic kinds in a shared type table
(https://akheron.github.io/optics-ts/reference-intro/, verified 2026-08-02).
The benefit is interoperation. The cost is a larger vocabulary.

**Profunctor representation.** Pickering, Gibbons, and Wu present profunctor
optics so different accessor kinds can compose through a common representation,
and describe prisms as one of the concrete optics handled by that framework
(https://programming-journal.org/2017/1/7/, verified 2026-08-02). This variant
is powerful in Haskell, PureScript, Scala, and advanced TypeScript libraries.
The cost is a type signature that can be too abstract for teams that need only
one or two branch selectors.

**Error-carrying prism.** Effect's `Optic.makePrism` takes a fallible getter that
returns a `Result` and an infallible setter, and documents `fromChecks` for
schema checks
(https://github.com/Effect-TS/effect/blob/main/packages/effect/src/Optic.ts,
verified 2026-08-02). This variant gives better diagnostics than `Option` or
`undefined` when the mismatch reason matters. Engineering judgement: keep this
for validation boundaries or operator-facing diagnostics, not for every branch
test inside a small reducer.

## 9. Known production uses

- **Monocle.** Monocle is a Scala optics library whose documentation includes
  `Prism`, `Prism.partial`, `GenPrism`, prism composition, and prism laws
  (https://www.optics.dev/Monocle/docs/optics/prism, verified 2026-08-02).
  This is a named production library use of Prism for sum types such as sealed
  traits and enums.
- **Haskell lens.** The `lens` package exposes `Control.Lens.Prism`, defines the
  `Prism` type alias, gives constructors and consumers, and includes common
  prisms such as `_left`, `_right`, and `_just`
  (https://hackage.haskell.org/package/lens-3.7.0.1/docs/Control-Lens-Prism.html,
  verified 2026-08-02). This is a named production library use in the Haskell
  ecosystem.
- **monocle-ts.** monocle-ts documents `Prism.ts`, including the `Prism<S, A>`
  interface with `getOption` and `reverseGet`, constructors such as `prism` and
  `fromPredicate`, combinators, compositions, and conversions
  (https://gcanti.github.io/monocle-ts/modules/Prism.ts.html, verified
  2026-08-02). This is a named production library use in TypeScript.
- **optics-ts.** optics-ts documents Prism in its optic type table, `preview`,
  `collect`, `modify`, `set`, `optional`, `guard`, `at`, `atKey`, and
  RemovablePrism (https://akheron.github.io/optics-ts/reference-intro/,
  verified 2026-08-02; https://akheron.github.io/optics-ts/reference-standalone/,
  verified 2026-08-02). This is a named production library use for immutable
  TypeScript data access.
- **Effect Optic.** Effect's source defines a `Prism<S, A>` interface extending
  `Optional<S, A>` and provides `makePrism` and `fromChecks`
  (https://github.com/Effect-TS/effect/blob/main/packages/effect/src/Optic.ts,
  verified 2026-08-02). This is a named production library use inside the Effect
  TypeScript ecosystem.

## 10. Consequences

Positive consequences.

- Branch access becomes a named value that can be imported, tested, composed,
  and reviewed.
- The no-match case is explicit in preview and benign in modify.
- Construction of the target branch is centralized in one builder.
- Repeated pattern matching becomes smaller and more uniform.
- Prisms compose with lenses, traversals, optionals, and other prisms in optics
  libraries that support the family.
- Public APIs can expose focused branch access without exposing every detail of
  the whole representation.
- Law tests catch mismatches between matcher and builder.
- A branch optic can carry a domain name, which improves logs and review
  language.

Negative consequences.

- Readers must learn optic vocabulary before the code feels ordinary.
- A simple branch can become over-abstracted if the prism is used once.
- Public prisms can freeze internal variants into compatibility commitments.
- Composed optics can hide where a branch check occurs.
- No-match updates can mask bugs when the caller expected the branch to be
  present.
- Lawless prisms produce subtle data loss, especially when the builder normalizes
  or drops fields.
- Performance in hot code can suffer from allocation and higher-order function
  dispatch unless the compiler inlines well.
- Error detail is often lost when absence is represented only as `None` or
  `undefined`.

Engineering judgement. The largest cost is not runtime overhead. It is the gap
between a local match expression and an imported abstraction. Use a prism when
the branch is a reusable concept, not because every branch test deserves a
library object.

## 11. Failure modes and misuse

This dimension is engineering judgement, except where a cited law or API
behavior is named.

- **Symptom.** Preview after review returns `None`, `undefined`, or a different
  payload. **Cause.** The builder constructs a value that the matcher does not
  accept, or it changes the payload. **Fix.** Add a law test for
  `preview(review(a)) == Some(a)` and repair the builder or matcher. Monocle and
  monocle-ts both document this law
  (https://www.optics.dev/Monocle/docs/optics/prism, verified 2026-08-02;
  https://gcanti.github.io/monocle-ts/modules/Prism.ts.html, verified
  2026-08-02).
- **Symptom.** Modifying a matching value drops metadata from the original
  branch. **Cause.** The focus type is too small to rebuild the original branch
  faithfully, yet the prism claims a round trip. **Fix.** Focus the whole branch
  object, add a lens after the prism for the payload field, or use Optional when
  reverse construction cannot preserve the original.
- **Symptom.** A failed update looks like a successful no-op in production.
  **Cause.** The caller expected the branch to be present, but prism `modify`
  deliberately leaves non-matching values unchanged. **Fix.** Use
  `modifyOption`, `preview` plus explicit error handling, or an assertion at the
  boundary where branch presence is required.
- **Symptom.** A metrics filter undercounts events after a new variant ships.
  **Cause.** A prism was treated as an exhaustive match over the sum. **Fix.**
  Keep exhaustive handling in a compiler-checked match or visitor. Use prisms
  only for focused branch work.
- **Symptom.** Public clients start constructing internal states that should
  have been impossible. **Cause.** The builder side of a public prism exposed a
  variant constructor. **Fix.** Move the prism to an internal module, publish a
  read-only fold, or publish a smart constructor that enforces domain rules.
- **Symptom.** A composed optic has surprising type, for example Traversal
  instead of Prism. **Cause.** Composition crossed into many-focus access.
  **Fix.** Check the library's composition table and name the result according
  to its weakest guarantee. Monocle and optics-ts both publish composition
  guidance (https://www.optics.dev/Monocle/docs/optics, verified 2026-08-02;
  https://akheron.github.io/optics-ts/reference-intro/, verified 2026-08-02).
- **Symptom.** A type guard prism accepts values on preview but later set
  creates values that violate the guard. **Cause.** The refinement was not
  closed under the builder. **Fix.** Make construction identity over the refined
  type, or replace the prism with validation that can fail.
- **Symptom.** Profiling shows branch-heavy reducers spending time in optic
  combinators. **Cause.** Deep composition and allocation sit in a hot loop.
  **Fix.** Inline the hot path, precompose optics once, or keep the prism at the
  API boundary and use local matching inside the tight loop.

## 12. Trade-off matrix

<table>
<thead>
<tr>
<th>Force</th>
<th>Prism</th>
<th>Lens</th>
<th>Optional</th>
<th>Traversal</th>
<th>Visitor</th>
</tr>
</thead>
<tbody>
<tr>
<td>Focus count</td>
<td>Zero or one branch</td>
<td>Exactly one part</td>
<td>Zero or one part</td>
<td>Zero to many parts</td>
<td>All declared cases</td>
</tr>
<tr>
<td>Reverse construction</td>
<td>Yes, focus to whole</td>
<td>No separate variant injection</td>
<td>Usually no</td>
<td>No single whole from one focus</td>
<td>Usually no</td>
</tr>
<tr>
<td>Best target</td>
<td>Sum type case</td>
<td>Product field</td>
<td>Nullable or partial path</td>
<td>Repeated children</td>
<td>Branch-specific behavior</td>
</tr>
<tr>
<td>No-match behavior</td>
<td>Explicit absence or no-op modify</td>
<td>Not applicable</td>
<td>Explicit absence</td>
<td>Empty result</td>
<td>Compiler or runtime dispatch</td>
</tr>
<tr>
<td>Coupling</td>
<td>Low to branch representation</td>
<td>Low to field path</td>
<td>Low to optional path</td>
<td>Low to container shape</td>
<td>Low for adding operations, high for adding variants</td>
</tr>
<tr>
<td>Cognitive load</td>
<td>Medium to high</td>
<td>Medium</td>
<td>Medium</td>
<td>Medium to high</td>
<td>Medium</td>
</tr>
<tr>
<td>Latency</td>
<td>Small branch and call cost</td>
<td>Small field and call cost</td>
<td>Small branch and call cost</td>
<td>Can scale with collection size</td>
<td>Dispatch plus method body</td>
</tr>
<tr>
<td>Exhaustiveness</td>
<td>Not exhaustive</td>
<td>Not relevant</td>
<td>Not exhaustive</td>
<td>Not exhaustive</td>
<td>Strong when compiler checks cases</td>
</tr>
<tr>
<td>Law burden</td>
<td>Round-trip laws</td>
<td>Lens laws</td>
<td>Optional laws or conventions</td>
<td>Traversal laws</td>
<td>Object or visitor invariants</td>
</tr>
<tr>
<td>Public API risk</td>
<td>Can expose constructor</td>
<td>Can expose field</td>
<td>Can expose partial path</td>
<td>Can expose collection shape</td>
<td>Can expose operation set</td>
</tr>
</tbody>
</table>

Engineering judgement. Prism competes most directly with Optional and local
pattern matching. Choose Prism when reverse construction and composition matter.
Choose Optional when there is no lawful builder. Choose a match or Visitor when
the operation must account for every variant.

## 13. Related and incompatible patterns

**Lens.** Lens focuses an always-present part of a product-like value. Prism
focuses a possibly-present case of a sum-like value. Pickering, Gibbons, and Wu
frame record fields and union variants as related data accessors under optics
(https://programming-journal.org/2017/1/7/, verified 2026-08-02). They compose,
but the result must respect the weaker guarantee when the prism can miss.

**Optional.** Optional also has zero or one focus. It differs because it cannot
always build the whole from a focus. A prism can be viewed as an optional in
libraries such as monocle-ts through `asOptional`
(https://gcanti.github.io/monocle-ts/modules/Prism.ts.html, verified
2026-08-02). The reverse is not generally true.

**Traversal.** Haskell `lens` says every Prism is a valid Traversal
(https://hackage.haskell.org/package/lens-3.7.0.1/docs/Control-Lens-Prism.html,
verified 2026-08-02). Traversal is the replacement when the focus count can be
many. Prism is the narrower tool for a single branch.

**Iso.** An Iso can be read and built in both directions without failure. Haskell
`lens` says every Iso is a valid Prism
(https://hackage.haskell.org/package/lens-3.7.0.1/docs/Control-Lens-Prism.html,
verified 2026-08-02). Use Iso when neither direction is partial.

**Profunctor.** Profunctor optics provide one representation that can cover
lenses, prisms, traversals, and related accessors. The 2017 profunctor optics
paper is the formal source for that composition story
(https://programming-journal.org/2017/1/7/, verified 2026-08-02). Use the
profunctor form when a library needs a full optic algebra, not when an
application needs one branch helper.

**Visitor.** Visitor is useful when behavior varies by branch and the operation
set is stable. Prism is useful when a branch must be extracted or updated as
data. They can coexist, but using prisms to avoid all exhaustive handling is a
misuse.

**Smart Constructor.** Smart Constructor validates creation. Prism assumes
construction from focus to whole succeeds. If construction needs validation,
validate first, then review through the prism.

Incompatible patterns and uses are **total-lens-for-variant**, where a partial
branch is mislabeled as always present; **many-focus-traversal**, where a prism
is stretched across a collection; and **validation-as-optic**, where construction
failure is hidden behind a builder that has no failure channel.

## 14. Refactoring path in and out

To introduce Prism into existing code:

1. Find repeated pattern matches that target the same variant and either extract
   its payload or rebuild that variant.
2. Name the branch in domain terms, for example `authorizedAmount`,
   `failedReason`, `stringToken`, or `remoteCommand`.
3. Write the matcher first. It should return an explicit absence value when the
   whole is not the target branch.
4. Write the builder second. It should construct the target branch from the
   focus without consulting external state.
5. Add law tests for both round-trip directions. Use property tests where the
   focus has a meaningful generator.
6. Replace repeated preview logic with the prism's preview operation.
7. Replace repeated no-op-on-miss updates with modify through the prism.
8. Compose the prism with existing lenses only after the base branch prism is
   tested and named.
9. Keep exhaustive matches for workflows that must cover every variant.

Named refactorings from the refactoring family apply around the edges. Extract
Function names the matcher when it is still local. Replace Conditional with
Polymorphism may be better when the branch owns behavior rather than data.
Encapsulate Field is a warning when publishing a prism would expose internals.

To remove Prism when it stops paying:

1. Count call sites. If only one remains, inline the matcher and builder into a
   local match expression.
2. If no code uses reverse construction, replace the prism with Optional, Fold,
   or a named predicate plus extractor.
3. If every caller expects the branch to be present, replace prism preview with
   a total domain type that models the narrowed state.
4. If the prism is public, deprecate it before removing the branch constructor
   it exposed.
5. Delete law tests only after all uses of both matcher and builder are gone.

Engineering judgement. The out path matters because optics can become small
abstractions nobody wants to touch. A prism should survive because it names a
real branch used in more than one place, not because deleting it feels risky.

## 15. Testing and verification

Testing starts with the laws. For a prism `p`, generate focus values `a` and
whole values `s`.

- Review then preview. `preview(p, review(p, a))` returns `Some(a)`.
- Preview then review. If `preview(p, s)` returns `Some(a)`, then
  `review(p, a)` equals `s`.
- No-match modify. If `preview(p, s)` returns no focus, `modify(p, f, s)`
  equals `s`.
- Match modify. If `preview(p, s)` returns `Some(a)`, `preview(p, modify(p, f,
  s))` returns `Some(f(a))`, subject to equality rules for the branch.

Monocle documents law checking through `PrismTests` and states the two
round-trip properties
(https://www.optics.dev/Monocle/docs/optics/prism, verified 2026-08-02).
Haskell's `lens-properties` package documents an `isPrism` property for
QuickCheck testing
(https://hackage.haskell.org/package/lens-properties/docs/Control-Lens-Properties.html,
verified 2026-08-02).

Unit tests should include one value for each non-target branch so the no-match
path is not only implicit. For discriminated unions, include a test that fails
if a new branch is added without deciding whether the prism should match it.
The technique differs by language. In TypeScript, a `never` assertion in a
separate exhaustive match can catch forgotten variants. In Rust and Swift, the
compiler can check exhaustive matches. In Python, tests must compensate because
the runtime will not enforce a closed union.

Property tests are valuable when the branch has payloads with many edge cases.
For a string-token prism, generate empty strings, Unicode strings, and long
strings. For numeric refinements, generate boundaries. For protocol messages,
generate payloads with optional fields. The test oracle should be equality on
the domain value, not on serialized text unless serialization is the pattern
under test.

Test doubles are usually unnecessary because prisms should be pure. If a prism
needs a mock service, it is not a prism. For code that consumes a prism, use a
small fake prism only when the consumer is genuinely generic over optics. Most
application tests should use the real prism, since its lawfulness is part of the
behavior.

Verification also includes compile checks for typed languages. A prism should
preserve the focus type through preview and modification. If the implementation
uses unchecked casts, add negative type tests or runtime tests for wrong branch
payloads.

## 16. Observability signals

This dimension is engineering judgement.

Most prisms should not log by themselves. They are pure structural accessors and
may sit in hot code. Observability belongs at the operation that uses the prism.
When branch access affects production behavior, record these signals:

- `prism_name`. Stable domain name, such as `failed_payment_reason`.
- `match_result`. `matched` or `missed`, sampled if the path is hot.
- `whole_variant`. The source variant name when safe to record.
- `operation`. `preview`, `modify`, `review`, or a domain operation name.
- `no_match_action`. `ignored`, `returned_error`, `fallback`, or `escalated`.
- `law_test_failures`. Count from CI or pre-release property tests, not runtime.
- `unexpected_miss_count`. Count only at boundaries where a match is expected.
- `payload_redacted`. Boolean for sensitive branch payloads.

A healthy dashboard depends on context. In an event router, misses may dominate
because each prism targets one event among many. In a payment capture workflow,
an unexpected miss on `authorizedPayment` may indicate a race or invalid state
transition. The metric must be interpreted with the operation name.

Failing signals include a sudden rise in unexpected misses after a deployment,
payload redaction false on a sensitive prism, a new whole variant with zero
matching decision, and law-test failure in CI. Another useful trace pattern is
to annotate composed optics once at construction time rather than logging every
inner combinator. `payment.authorized.amount` is readable. A stack of anonymous
`compose`, `guard`, and `prop` calls is not.

Engineering judgement. Avoid logging raw focus payloads by default. Prisms often
target error details, credentials, tokens, personal data, or protocol payloads.
Log the branch and result, then add explicit redaction for payloads that
operators need.

## 17. Security and privacy implications

This dimension is engineering judgement, except where a cited API fact is named.

Prism is silent on authentication, authorization, encryption, and retention. It
is an access pattern. The security effect comes from what branch it exposes and
where the prism is exported.

Positive effects:

- A named prism can centralize approved access to a sensitive branch, such as a
  token-bearing event or a password-reset command.
- A read-only wrapper or non-exported builder can prevent callers from
  constructing sensitive states directly.
- A prism returning absence can avoid exceptions that leak internal shape in
  error messages.
- Law tests can catch accidental payload rewriting in security-sensitive
  protocol variants.

Risks:

- The builder side may expose a constructor that bypasses a smart constructor,
  permission check, signature check, or state transition rule.
- Generic logging around preview can leak payloads when a prism targets secrets
  or personal data.
- A predicate prism can be mistaken for validation. If construction accepts any
  value and validation happens only on preview, invalid values can still enter
  the system.
- Public branch optics can reveal internal state machine variants to plugin or
  client code.
- No-match no-op behavior can hide authorization bugs when a caller expected a
  protected branch to be present.

Practical controls:

- Keep sensitive builders internal. Export preview-only folds or domain
  functions when outside callers should not construct the branch.
- Prefer smart constructors before review for validated payloads.
- Redact focus payloads in logs and traces by default.
- Treat public prisms as API surface in threat modeling.
- Add tests proving that forbidden states cannot be constructed through exported
  optics.

Effect's `makePrism` documents a fallible getter and infallible setter, while
`fromChecks` builds a prism from schema checks
(https://github.com/Effect-TS/effect/blob/main/packages/effect/src/Optic.ts,
verified 2026-08-02). Engineering judgement: that shape is useful for typed
validation boundaries, but it does not replace a security review of the setter
side. A setter that can build a privileged variant is a capability.

## 18. References

- Matthew Pickering, Jeremy Gibbons, Nicolas Wu, "Profunctor Optics. Modular
  Data Accessors", *The Art, Science, and Engineering of Programming*, volume
  1, issue 2, article 7, 2017. DOI 10.22152/programming-journal.org/2017/1/7.
  https://programming-journal.org/2017/1/7/, verified 2026-08-02.
- Monocle documentation, "Prism", including `getOption`, `reverseGet`,
  `Prism.partial`, `GenPrism`, composition examples, and prism laws.
  https://www.optics.dev/Monocle/docs/optics/prism, verified 2026-08-02.
- Monocle documentation, "Optics", composition table for Fold, Getter, Setter,
  Traversal, Optional, Prism, Lens, and Iso.
  https://www.optics.dev/Monocle/docs/optics, verified 2026-08-02.
- Haskell `lens` package documentation, `Control.Lens.Prism`, including the
  `Prism` type, `_left`, `_right`, `_just`, `review`, `remit`, and the statement
  that every Prism is a Traversal and every Iso is a Prism.
  https://hackage.haskell.org/package/lens-3.7.0.1/docs/Control-Lens-Prism.html,
  verified 2026-08-02.
- Haskell `lens-properties` package documentation, `Control.Lens.Properties`,
  including `isPrism` for QuickCheck property testing.
  https://hackage.haskell.org/package/lens-properties/docs/Control-Lens-Properties.html,
  verified 2026-08-02.
- monocle-ts documentation, `Prism.ts`, including `Prism<S, A>`, `getOption`,
  `reverseGet`, laws, constructors, combinators, composition, `asOptional`, and
  `asTraversal`. https://gcanti.github.io/monocle-ts/modules/Prism.ts.html,
  verified 2026-08-02.
- optics-ts documentation, "Introduction", optic focus counts and composition
  rules. https://akheron.github.io/optics-ts/reference-intro/, verified
  2026-08-02.
- optics-ts documentation, "Standalone API", including `preview`, `collect`,
  `modify`, `set`, `optional`, `guard`, `at`, `atKey`, `find`, `when`, and
  RemovablePrism. https://akheron.github.io/optics-ts/reference-standalone/,
  verified 2026-08-02.
- optics-ts documentation, "Tutorial", Prism examples for optional fields,
  guards over union types, and no-match update behavior.
  https://akheron.github.io/optics-ts/tutorial/, verified 2026-08-02.
- Effect source, `packages/effect/src/Optic.ts`, including `Prism<S, A>`,
  `makePrism`, and `fromChecks`.
  https://github.com/Effect-TS/effect/blob/main/packages/effect/src/Optic.ts,
  verified 2026-08-02.

## Code examples

TypeScript is idiomatic for Prism when data is modeled as discriminated unions.
This example avoids library dependencies so it can compile as a small file.

```typescript
type Payment =
  | { tag: "Pending"; id: string }
  | { tag: "Authorized"; id: string; cents: number }
  | { tag: "Failed"; id: string; reason: string };

type Prism<S, A> = {
  preview: (source: S) => A | undefined;
  review: (focus: A) => S;
};

const authorizedCents: Prism<Payment, number> = {
  preview: (p) => (p.tag === "Authorized" ? p.cents : undefined),
  review: (cents) => ({ tag: "Authorized", id: "new", cents }),
};

function modify<S, A>(p: Prism<S, A>, f: (a: A) => A, source: S): S {
  const focus = p.preview(source);
  return focus === undefined ? source : p.review(f(focus));
}

const p1: Payment = { tag: "Authorized", id: "p1", cents: 500 };
const p2: Payment = { tag: "Pending", id: "p2" };

console.log(authorizedCents.preview(p1));
console.log(modify(authorizedCents, (n) => n + 100, p1));
console.log(modify(authorizedCents, (n) => n + 100, p2));
```

Python can express the same idea with dataclasses and union types. The type
checker helps less than in languages with sealed unions, so tests carry more
weight.

```python
from dataclasses import dataclass
from typing import Callable, Generic, Optional, TypeVar, Union

S = TypeVar("S")
A = TypeVar("A")


@dataclass(frozen=True)
class Pending:
    ident: str


@dataclass(frozen=True)
class Authorized:
    ident: str
    cents: int


@dataclass(frozen=True)
class Failed:
    ident: str
    reason: str


Payment = Union[Pending, Authorized, Failed]


@dataclass(frozen=True)
class Prism(Generic[S, A]):
    preview: Callable[[S], Optional[A]]
    review: Callable[[A], S]

    def modify(self, fn: Callable[[A], A], source: S) -> S:
        focus = self.preview(source)
        return source if focus is None else self.review(fn(focus))


authorized_cents: Prism[Payment, int] = Prism(
    lambda p: p.cents if isinstance(p, Authorized) else None,
    lambda cents: Authorized("new", cents),
)

print(authorized_cents.preview(Authorized("p1", 500)))
print(authorized_cents.modify(lambda n: n + 100, Authorized("p1", 500)))
print(authorized_cents.modify(lambda n: n + 100, Pending("p2")))
```

Rust is a natural host when variants are modeled as enums. This sample uses
function pointers for a small monomorphic prism.

```rust
#[derive(Clone, Debug, PartialEq)]
enum Payment {
    Pending { id: String },
    Authorized { id: String, cents: i32 },
    Failed { id: String, reason: String },
}

struct Prism<S, A> {
    preview: fn(&S) -> Option<A>,
    review: fn(A) -> S,
}

impl<S: Clone, A> Prism<S, A> {
    fn modify(&self, source: &S, f: fn(A) -> A) -> S {
        match (self.preview)(source) {
            Some(focus) => (self.review)(f(focus)),
            None => source.clone(),
        }
    }
}

fn preview_authorized(p: &Payment) -> Option<i32> {
    match p {
        Payment::Authorized { cents, .. } => Some(*cents),
        _ => None,
    }
}

fn review_authorized(cents: i32) -> Payment {
    Payment::Authorized {
        id: "new".to_string(),
        cents,
    }
}

fn add_fee(cents: i32) -> i32 {
    cents + 100
}

fn main() {
    let authorized = Prism {
        preview: preview_authorized,
        review: review_authorized,
    };
    let p1 = Payment::Authorized {
        id: "p1".to_string(),
        cents: 500,
    };
    let p2 = Payment::Pending {
        id: "p2".to_string(),
    };
    println!("{:?}", (authorized.preview)(&p1));
    println!("{:?}", authorized.modify(&p1, add_fee));
    println!("{:?}", authorized.modify(&p2, add_fee));
}
```

These samples use a reduced builder that assigns a fresh id. That means they are
not lawful for preserving the whole branch after preview. They demonstrate the
mechanics, and they also show why law tests matter. In production code, the
focus would include enough data to rebuild the original branch, or the prism
would focus the branch object and compose with a lens for `cents`.
