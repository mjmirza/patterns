---
name: Profunctor
slug: profunctor
family: 16-functional
category: Composition
aliases: [Distributor, Bimodule, Correspondence]
first_described: "Benabou 1973"
maturity: canonical
related: [function-composition, lens, functor, natural-transformation]
incompatible_with: [covariant-only-functor, contravariant-only-functor]
verified: 2026-08-21
---

# Profunctor

## 1. Name, aliases, and lineage

The canonical name in programming is Profunctor. The term originates in
category theory, where Jean Benabou introduced it in his 1973 Bourbaki
seminar notes as a way of relating two categories through a hom-set-valued
functor. Benabou himself later preferred the name **Distributor**, and the
nLab entry on the concept states plainly that "Jean Benabou, who invented
the term and originally used profunctor, later preferred distributor"
(https://ncatlab.org/nlab/show/profunctor, verified 2026-08-21). Category
theorists who came to the concept independently, or who emphasise the
module-theoretic reading, sometimes call the same construction a
**Bimodule** or a **Correspondence**, because a profunctor from category C
to category D behaves like a bimodule over the two categories treated as
rings, generalising the way a bimodule sits between two rings and can be
acted on from both sides.

The programming-language sense of the word is the same categorical idea
specialised to Haskell-style types and functions, where a profunctor is a
type constructor of two parameters that is contravariant in the first and
covariant in the second, packaged behind a single combinator called
`dimap`. This programming encoding reached wide practical use through Edward
Kmett's `profunctors` library for Haskell, and through its role as the
foundation of profunctor optics, formalised by Matthew Pickering, Jeremy
Gibbons, and Nicolas Wu in "Profunctor Optics, Modular Data Accessors"
(arXiv paper 1703.10857, verified 2026-08-21), which showed that lenses,
prisms, and traversals can all be represented uniformly as polymorphic
functions constrained by different subclasses of Profunctor.

## 2. Problem and context

A codebase accumulates two families of type constructors that look
unrelated on the surface but are secretly the same shape. One family maps
only outward, a `Functor`, used for a producer of values, a stream, a
parser's result, a computation's output. The other family maps only
inward, a `Contravariant` functor, used for a consumer of values, a
predicate, a comparator, a serialiser, a printer.

The situation that motivates a profunctor is when a single type needs
both directions at once, and needs them to compose cleanly. The plain
function type is the canonical case. a function from A to B is
contravariant in A (given a function C to A, you can precompose to get a
function C to B) and covariant in B (given a function B to D, you can
postcompose to get a function A to D). A parser combinator that both
consumes input and produces a value has the same two-directional shape.
An optic, a lens or a prism, that both reads a field out of a structure
and writes a new value back into it, has the same shape again. Without a
name for this shape, every one of these libraries reinvents its own pair
of "map over the input" and "map over the output" functions, under
different names, with no shared vocabulary and no shared laws to lean on.

Profunctor gives that shape one name and one operation, `dimap`, so any
code written against the Profunctor interface works uniformly across
functions, parsers, printers, and optics, and any library that defines
its type as an instance of Profunctor inherits a body of composition laws
and derived combinators for free.

## 3. Forces

The pattern balances the following competing pressures.

- **Uniform pre and post processing.** Favoured. `dimap` lets a caller
  adapt both the input and the output of a two-parameter type constructor
  in a single call, rather than writing two separate adapter functions
  and composing them by hand each time.
- **Variance correctness.** Favoured. The contravariant-in-first,
  covariant-in-second shape is exactly what a type checker needs to admit
  the function instance, the parser instance, and the optic instance
  under one interface, without unsound coercions.
- **Abstraction over concrete representation.** Favoured, at the cost of
  indirection. Code written polymorphically against Profunctor, most
  visibly profunctor optics, works over any concrete profunctor a caller
  supplies, so a single lens definition, for example, runs unmodified as
  a getter, a setter, and a traversal by choosing which profunctor
  instance interprets it.
- **Learning cost.** Sacrificed. The concept requires understanding two
  independent notions of variance at once, and the profunctor optics
  encoding in particular reads as unmotivated indirection to a reader
  who has not seen the derivation from the direct getter and setter
  representation.
- **Runtime overhead of the polymorphic encoding.** Sacrificed in some
  implementations. Profunctor optics as first-class polymorphic values
  route every use through a rank-2 polymorphic function application,
  which a compiler that does not specialise aggressively leaves as extra
  indirection compared to a direct getter-and-setter pair.
- **Subclass proliferation.** Sacrificed. Real use rarely stops at plain
  Profunctor. Optics on product types need `Strong`, optics on sum types
  need `Choice`, optics on traversable structures need `Traversing`, so a
  library ends up with a small hierarchy of profunctor subclasses rather
  than one flat interface.

## 4. Applicability and non-applicability

Reach for a Profunctor when the following hold.

- A type constructor of two parameters genuinely needs to be adapted on
  both sides, its input transformed one way and its output transformed
  another, and the two transformations should compose as a single
  operation with known laws.
- The codebase is building or consuming an optics library, where the
  profunctor encoding is what makes a lens, a prism, and a traversal all
  instances of one polymorphic function type, composable with plain
  function composition.
- A parser combinator, a codec, or a printer library wants to expose a
  uniform `dimap` so callers can adapt both what the combinator consumes
  and what it produces without reaching into the combinator's internals.
- The type already has separate, ad hoc "map the input" and "map the
  output" functions scattered through the codebase under different
  names, and unifying them under one law-abiding interface would remove
  duplication.

Do NOT reach for a Profunctor in these cases, and the reason matters more
than the rule.

- **The type constructor is covariant only.** A plain `Functor` (`map`
  alone) is the correct and simpler interface. Adding a contravariant
  parameter that is never varied independently is unearned complexity.
- **The type constructor is contravariant only.** A plain
  `Contravariant` functor (`contramap` alone) is correct. Predicates,
  comparators, and pure consumers rarely need a covariant side.
- **The language has no practical way to express two independent
  variance annotations, or no support for the higher-kinded
  polymorphism a general Profunctor interface needs.** Forcing the
  abstraction through generics that cannot express it produces brittle,
  unsafe casts rather than a real profunctor.
- **A direct getter-and-setter pair already reads clearly and the team
  has no plan to build composable optics on top of it.** The profunctor
  optics encoding earns its cost only when composition across many
  optics, or interpretation under many different profunctor instances,
  is the actual goal. A single one-off accessor does not need it.
- **The two directions are not actually independent.** If transforming
  the input always determines the output transformation in lockstep,
  the relationship is better modelled as one function, not two separate
  `dimap` arguments.

## 5. Structure

A Profunctor is a type constructor `p` of two type parameters, written
`p a b`, together with one combinator.

- **`dimap`.** Takes a function from `c` to `a` (adapting the input, run
  before the profunctor's own logic, hence contravariant) and a function
  from `b` to `d` (adapting the output, run after the profunctor's own
  logic, hence covariant), and produces a `p c d` from a `p a b`.

Two derived operations follow directly from `dimap` and are usually
provided as convenience methods.

- **`lmap`** (or `contramapFirst`), `dimap` with the output-adapting
  function fixed to the identity. Adapts only the input.
- **`rmap`** (or `map`), `dimap` with the input-adapting function fixed
  to the identity. Adapts only the output.

The base instance every profunctor library provides is the function
type itself. `p = (->)`, where `dimap f g h = g . h . f`, precompose with
`f`, run the original function `h`, then postcompose with `g`. Every
other profunctor instance, a parser, a printer, an optic, generalises
this same shape.

Two named subclasses extend a plain Profunctor to handle structured
data, and both matter for optics.

- **`Strong`.** Adds `first'` (or `strong-first`), lifting `p a b` into
  `p (a, c) (b, c)`, threading an untouched second component of a pair
  alongside. This is what makes a Profunctor able to focus on one field
  of a product type while leaving its sibling fields alone, the
  profunctor encoding of a Lens.
- **`Choice`.** Adds `left'`, lifting `p a b` into
  `p (Either a c) (Either b c)`, handling one branch of a sum type while
  passing the other branch through untouched. This is the profunctor
  encoding of a Prism.

## 6. ASCII structure diagram

```
Profunctor p, two type parameters, opposite variance

input side (contravariant)
  c --- f ---> a
output side (covariant)
  b --- g ---> d

  p a b  --- dimap f g --->  p c d

Base instance, functions:

  p a b  =  a -> b

  dimap f g h  =  g . h . f
    (precompose f, run h, postcompose g)

Subclass Strong (products):
  p a b  ---->  p (a, c) (b, c)
  (focus one field, pass the rest)

Subclass Choice (sums):
  p a b  ---->  p (Either a c) (Either b c)
  (focus one branch, pass the other through)
```

## 7. Dynamics

The runtime flow below shows `dimap` adapting a plain function
profunctor, then a Strong profunctor threading an untouched paired value
through a `first'` operation.

```
Caller                dimap(f, g, h)              Result

|-- dimap(toInt, toString, double) ---->|
|   where double = (n) => n * 2         |
|                                       |-- returns a new function
|                                       |   that runs toInt, then
|                                       |   double, then toString
|<-- composedFn ------------------------|

|-- composedFn("21") ------------------->|
|                                        |-- toInt("21") = 21
|                                        |-- double(21) = 42
|                                        |-- toString(42) = "42"
|<-- "42" -------------------------------|

|-- first'(getUserName) ---------------->|
|   getUserName : User -> String        |
|                                        |-- lifts to a function over
|                                        |   (User, RequestId) pairs
|<-- pairedFn ---------------------------|

|-- pairedFn((user, reqId)) ------------->|
|                                         |-- getUserName(user) = name
|                                         |-- reqId passed through
|<-- (name, reqId) -----------------------|
```

## 8. Implementation variants

**Function-based profunctor, the base case.** The plain function type is
itself the canonical Profunctor instance, `dimap f g h = g . h . f`.
Almost every practical profunctor library and every profunctor optics
encoding is built by generalising this one instance, so understanding it
first is the fastest path to understanding the rest.

**Typeclass or protocol encoding.** In Haskell and Scala the pattern is a
named interface, `Profunctor` in `profunctors` and in `cats.arrow`, with
`dimap` as the single required method and `lmap`/`rmap` derived from it
with default implementations. Any two-parameter type constructor becomes
a profunctor by writing one `dimap` instance, after which the whole body
of derived combinators and laws applies automatically.

**Profunctor optics.** Following Pickering, Gibbons, and Wu 2017, a Lens
is represented not as a getter-and-setter pair but as a single
polymorphic function of type `forall p. Strong p => p a b -> p s t`. The
same lens value, applied to different concrete profunctors, yields
different behaviour. applying it to the function profunctor recovers a
plain getter, applying it to a profunctor built from a monoid recovers a
fold, applying it to a profunctor built from an applicative functor
recovers a setter. A Prism is the same idea with `Choice` in place of
`Strong`, and a Traversal generalises further to a `Traversing`
constraint. This is the deepest and most productive implementation
variant, because composing two optics is then ordinary function
composition, with no bespoke composition operator needed.

**Star profunctor, wrapping an applicative or functor.** A common
building block, `Star f a b = a -> f b` for some functor `f`, is itself a
profunctor whenever `f` is a functor. `Star` is how profunctor optics
libraries reuse an existing `Functor` or `Applicative` instance (the
identity functor for a pure setter, a monoid-wrapping functor for a
fold) as the concrete profunctor a polymorphic optic gets applied to,
without writing a new profunctor instance for every behaviour.

**Forget profunctor, for pure extraction.** `Forget r a b = a -> r`,
ignoring the `b` parameter entirely. Applying a Lens built against
`Strong` to a `Forget` instance recovers exactly the getter, discarding
the setter capability, which is how a single polymorphic Lens value can
be used purely as a read without any separate accessor function.

**Ad hoc dimap without a named typeclass.** In languages with no
convenient way to express a two-parameter, opposite-variance interface,
teams often write the equivalent of `dimap` as a plain two-argument
method on a single concrete class, with no shared interface across
different profunctor-shaped types in the codebase. This captures the
combinator without the cross-type abstraction, and is a reasonable
fallback in a language whose type system cannot express the general
interface cleanly.

## 9. Known production uses

**Haskell `profunctors`.** Edward Kmett's `profunctors` package defines
the `Profunctor` class and the `Strong`, `Choice`, `Closed`, and
`Costrong` subclasses, along with the `Star` and `Costar` building
blocks, and is a direct dependency of the widely used `lens` library.
Hackage package documentation, `profunctors`,
https://hackage.haskell.org/package/profunctors, verified 2026-08-21.

**Haskell `lens`, polymorphic optics.** The `lens` library's `Iso`,
`Lens`, and `Prism` types are defined as profunctor-polymorphic
functions built directly on the `profunctors` package, so composing two
optics with plain function composition (`.`) works because both are
instances of the same profunctor-constrained function type. Hackage
package documentation, `lens`, module `Control.Lens.Iso`,
https://hackage.haskell.org/package/lens/docs/Control-Lens-Iso.html,
verified 2026-08-21.

**Scala Cats `cats.arrow.Profunctor`.** The Cats functional programming
library for Scala defines `Profunctor` in the `cats.arrow` package with
`dimap` as its core operation, contramapping on the first type parameter
and mapping on the second, with `Arrow`, `ArrowChoice`,
`CommutativeArrow`, and `Strong` as its named subclasses. Typelevel Cats
API documentation, `cats.arrow.Profunctor`,
https://typelevel.org/cats/api/cats/arrow/Profunctor.html, verified
2026-08-21.

## 10. Consequences

Positive.

- A single `dimap` call replaces two hand-written adapter functions
  composed by hand, and comes with algebraic laws a caller can rely on.
- Optics libraries built on the profunctor encoding compose lenses,
  prisms, and traversals with plain function composition, with no
  bespoke composition operator, because they are all the same
  polymorphic function type constrained by a different profunctor
  subclass.
- One profunctor definition for a type is reusable across every context
  that has already adopted the interface, a parser combinator library
  and a printer library that both implement Profunctor can share
  generic combinators written once against the interface.
- The `Star` and `Forget` building blocks let a library reuse an
  existing `Functor` or `Applicative` instance as a concrete profunctor,
  avoiding a new profunctor instance for every behaviour an optic needs
  to support.

Negative.

- The concept requires understanding two independent notions of
  variance simultaneously, which is a genuine learning cost for a reader
  who has not met contravariance before.
- The profunctor optics encoding in particular is close to unreadable
  without first seeing the direct getter-and-setter representation it
  generalises, so introducing it without that context confuses more
  than it clarifies.
- A rank-2 polymorphic optic value, applied through the profunctor
  encoding, adds indirection a compiler that does not specialise
  aggressively cannot always remove, compared to a direct
  getter-and-setter pair.
- Real optics work needs the `Strong` and `Choice` subclasses, and often
  `Traversing` as well, so a Profunctor-based library ends up with a
  small class hierarchy rather than one flat interface, adding surface
  area a plain getter-and-setter API does not have.

## 11. Failure modes and misuse

**Reaching for Profunctor when only one direction is needed.** Symptom.
A type is declared as an instance of Profunctor, but its `lmap` or
`rmap` is never called anywhere in the codebase, only the other
direction is ever used. Cause. Reaching for the general interface out of
habit rather than because the type genuinely varies in both directions.
Fix. Use a plain `Functor` or `Contravariant` instance, whichever
direction is actually needed, and drop the unused half of the interface.

**Violating the profunctor laws.** Symptom. Composing two `dimap` calls
produces a different result depending on whether the adapting functions
are combined first and applied once, or applied one at a time in
sequence, when the laws say the two must agree. Cause. A hand-written
`dimap` instance that does not actually precompose on the input and
postcompose on the output in the required order, often from mutating
shared state inside the profunctor's own logic. Fix. Verify the two
laws directly, `dimap id id = id` and
`dimap (f2 . f1) (g1 . g2) = dimap f1 g1 . dimap f2 g2`, with a property
test, and inspect the instance for any side effect that could break
them.

**Confusing the direction of contravariance.** Symptom. An adapting
function for the input side is written to run after the profunctor's own
logic instead of before it, so values flow through the composition in
the wrong order and a type that compiles produces the wrong runtime
result. Cause. Treating both `dimap` arguments as ordinary covariant
maps instead of remembering the input side is contravariant, precompose,
not postcompose. Fix. Trace one concrete example, the function instance,
`dimap f g h = g . h . f`, and confirm the new instance matches that
composition order exactly.

**Building a profunctor optics library without the Strong or Choice
subclass a use case needs.** Symptom. An attempt to define a Lens over a
product field, or a Prism over a sum branch, fails to type-check, or
compiles but silently loses the untouched sibling field or branch at
runtime. Cause. Implementing only plain Profunctor and skipping the
`Strong` or `Choice` extension that a structured optic actually needs to
thread the untouched part of the value through. Fix. Add the required
subclass instance before attempting to define any Lens (needs `Strong`)
or Prism (needs `Choice`) against the type.

**Introducing profunctor optics to a team with no prior exposure to the
direct getter-and-setter encoding.** Symptom. New team members cannot
read or extend the optics code, and productivity on anything touching it
drops. Cause. Skipping the pedagogical step of showing the direct
representation the profunctor encoding generalises, so the abstraction
arrives with no felt motivation. Fix. Introduce a direct
getter-and-setter Lens type first, demonstrate its composition
limitations, then show the profunctor encoding as the fix for exactly
those limitations.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Profunctor | Plain Functor (covariant only) | Plain Contravariant functor | Direct getter-and-setter pair | Ad hoc dimap, no shared interface |
|---|---|---|---|---|---|
| Handles both input and output adaptation | Yes, in one operation | No, output only | No, input only | Yes, via two separate functions | Yes, per type, no shared vocabulary |
| Composability across many instances | High, one law-abiding interface | High, for its one direction | High, for its one direction | Low, bespoke composition per pair | Low, no shared composition rule |
| Learning cost | High, two variances at once | Low | Low | Low | Low, but pays off later in duplication |
| Cross-library reuse of generic combinators | Yes, once the interface is adopted | Yes, for Functor-only code | Yes, for Contravariant-only code | No | No |
| Runtime overhead in a non-specialising compiler | Some, via the polymorphic encoding | Minimal | Minimal | Minimal | Minimal |
| Natural fit for optics (Lens, Prism) | Excellent, the standard modern encoding | Poor, wrong variance | Poor, wrong variance | Adequate for one-off use, poor for composition | Poor, no shared composition |

Reading of the table. Profunctor wins whenever a type genuinely needs
both directions of variance and composability across many concrete
instances matters, most visibly in optics libraries. A plain Functor or
Contravariant functor wins whenever only one direction is ever used, the
simpler interface is the honest one. A direct getter-and-setter pair
wins for a single, one-off accessor with no plan to compose it with
others. Ad hoc dimap wins only as a stopgap in a language that cannot
express the general interface, and it accrues the same duplication
Profunctor exists to remove.

## 13. Related and incompatible patterns

- **Function Composition.** The base case a Profunctor generalises. the
  plain function type's own `dimap` is exactly precompose-then-run-then-
  postcompose, and understanding ordinary function composition is the
  prerequisite for understanding any other profunctor instance.
- **Lens.** The profunctor optics encoding represents a Lens as a
  `Strong`-constrained polymorphic function, and composing two lenses is
  then plain function composition. Profunctor is the mechanism that
  makes this composition work without a bespoke operator.
- **Functor.** A Profunctor's covariant side, fixing the contravariant
  parameter, recovers an ordinary Functor. the two are directly related,
  not alternatives, a Profunctor is strictly the more general shape.
- **Natural Transformation.** A profunctor between two categories is
  itself sometimes presented via a hom-functor into Set, and the
  category-theoretic study of profunctors leans heavily on natural
  transformations between such hom-functors, so the two concepts are
  close cousins in the categorical framing even though they solve
  different everyday programming problems.
- **Covariant-only Functor as a substitute.** Conflicts with the
  applicability guidance directly. using a plain Functor where the input
  side genuinely also needs adaptation forces callers to write and
  compose separate input-adapting functions by hand, which is exactly
  the duplication Profunctor exists to remove.
- **Contravariant-only functor as a substitute.** The same conflict in
  the other direction. a type that also needs output adaptation, forced
  through a plain Contravariant interface, cannot express the output
  side at all.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered steps.

1. Identify a type constructor with separate, ad hoc "adapt the input"
   and "adapt the output" functions scattered under different names.
   Confirm both directions are genuinely used somewhere, otherwise a
   plain Functor or Contravariant functor is the right, simpler fix.
2. Write the single `dimap` operation for the type, checking it against
   the function instance's own definition, precompose on the input side,
   postcompose on the output side.
3. Derive `lmap` and `rmap` from `dimap` with the unused side fixed to
   identity, and replace every existing ad hoc adapter function with a
   call through one of the three.
4. Verify the two profunctor laws hold with a property test, identity
   preservation and composition distributing correctly over `dimap`.
5. If the type also needs to focus on one field of a product, or one
   branch of a sum, add the `Strong` or `Choice` instance rather than
   hand-rolling a separate accessor mechanism.
6. Only once the plain Profunctor instance is solid and tested, consider
   moving to the full profunctor optics encoding if composition across
   many optics is an actual, current need, not a speculative one.

Removing the pattern when it stops earning its place. Signals that it
should go include a type whose `lmap` or `rmap` is never called, or a
profunctor-optics-based accessor that the team consistently has to
explain from first principles before anyone can extend it.

1. Confirm which direction, if either, is genuinely still used across
   the codebase. If only one is, this is the strongest signal the
   general interface is unearned.
2. Replace the Profunctor instance with a plain Functor or Contravariant
   instance covering the direction that is actually used, or with a
   direct getter-and-setter pair if the type is a one-off accessor with
   no composition need.
3. Migrate call sites from `dimap`/`lmap`/`rmap` to the simpler
   replacement interface, one call site at a time, keeping tests green
   after each site.
4. Delete the Profunctor (and any `Strong`/`Choice`) instance only after
   no call site references it.

## 15. Testing and verification

Easier because of the pattern.

- The profunctor laws are two universally quantified equations,
  `dimap id id = id` and the composition law relating a single combined
  `dimap` call to two sequential ones, which are exactly the shape a
  property test framework is built to check across generated inputs and
  generated adapting functions.
- Because `dimap`, `lmap`, and `rmap` are pure, law-abiding operations
  with no hidden state, a test can construct a profunctor value, apply
  a sequence of adaptations, and assert on the final behaviour without
  any setup or teardown of shared mutable state.
- A single generic law-checking test, written once against the
  Profunctor interface, is reusable unchanged across every concrete
  instance a codebase defines, the function instance, a parser
  instance, a printer instance, cutting the marginal test-writing cost
  of a new instance to near zero.

Harder because of the pattern.

- Testing a profunctor-optics-encoded Lens or Prism through its
  polymorphic form requires instantiating it at a concrete profunctor,
  `Star`, `Forget`, or the plain function instance, so a test suite must
  understand at least those two or three concrete instances to exercise
  the getter and setter behaviour a polymorphic optic hides.
- A `Strong` or `Choice` instance that silently drops or duplicates the
  untouched paired value or branch is a subtle bug that a law-only test
  can miss unless the test specifically checks the untouched component
  survives unchanged.

Techniques that apply.

- **Identity law property.** For an arbitrary profunctor value, assert
  `dimap identity identity value` is indistinguishable from `value`
  under the profunctor's own equality or observation.
- **Composition law property.** For arbitrary adapting functions
  `f1, f2` on the input side and `g1, g2` on the output side, and an
  arbitrary profunctor value, assert that
  `dimap (compose f2 f1) (compose g1 g2) value` equals applying
  `dimap f1 g1` then `dimap f2 g2` in sequence.
- **Untouched-component property, for Strong and Choice.** For an
  arbitrary paired or either value, assert that the component the
  `Strong` or `Choice` lift did not focus on survives the round trip
  unchanged and in its original position.
- **Concrete-instantiation test, for profunctor optics.** For a
  polymorphic Lens or Prism value, instantiate it at the function
  profunctor to test the getter behaviour, and at a `Star`-wrapped
  identity or state-like functor to test the setter behaviour,
  confirming both agree with a hand-written direct accessor.

## 16. Observability signals

Profunctor is a compile-time and library-design abstraction with almost
no independent runtime footprint of its own, and inventing a dedicated
production signal for it here would be dishonest. Two indirect signals
are worth naming for a codebase that leans heavily on the pattern.

What to record.

- If a profunctor-optics library is used on a hot path, a latency or
  allocation signal at the call sites that apply a polymorphic optic,
  compared against an equivalent direct getter-and-setter path, is the
  honest way to catch the case where a non-specialising compiler leaves
  real indirection overhead in place.
- A code-review or static-analysis signal counting `Strong`/`Choice`
  instances added without a corresponding law-checking property test,
  since that gap is exactly where the untouched-component failure mode
  in dimension 11 hides.

A healthy state. Hot-path benchmarks comparing the profunctor-optics
path against a direct accessor show no measurable gap, meaning the
compiler is specialising the polymorphic calls away. Every `Strong` or
`Choice` instance in the codebase has a matching untouched-component
test.

A failing state. A hot-path benchmark shows a persistent gap between
the optics path and a direct accessor, pointing at a missed
specialisation opportunity worth addressing at the call site or in the
optics library's own inlining pragmas. Or a `Strong`/`Choice` instance
exists with no matching test, which is a standing risk the failure mode
in dimension 11 will eventually surface as a silently dropped field.

## 17. Security and privacy implications

The pattern is close to silent on security and privacy in its own
right, being a pure, compile-time compositional abstraction with no
independent storage, network, or logging surface, and inventing a
specific attack surface here would be dishonest. One practical
implication is worth naming.

**A profunctor-encoded optic can widen the blast radius of a field
access mistake.** Because a single polymorphic Lens or Prism value is
reusable as a getter, a setter, and a fold depending on which concrete
profunctor it is applied to, a Lens accidentally defined over a
sensitive field (a credential, a token, a piece of personal data) is
reusable in every one of those capacities everywhere the optic is
exported, which is more surface than a single, narrowly scoped getter
function would expose. When defining an optic over sensitive data,
scope its export deliberately, and prefer a `Forget`-instantiated,
read-only accessor at the boundary where only reading, never writing or
folding, should be possible.

On the underlying category-theoretic concept itself there is no security
or privacy dimension. it is a mathematical relationship between two
categories, and any security implication belongs entirely to what a
concrete profunctor instance is used to model.

## 18. References

1. nLab contributors. "Profunctor".
   https://ncatlab.org/nlab/show/profunctor
   Verified 2026-08-21. Source of the categorical lineage, the
   attribution to Jean Benabou, and the alternate name Distributor.
2. Matthew Pickering, Jeremy Gibbons, Nicolas Wu. "Profunctor Optics,
   Modular Data Accessors". arXiv paper 1703.10857.
   https://arxiv.org/abs/1703.10857
   Verified 2026-08-21. Source for the profunctor optics implementation
   variant in dimension 8, formalising Lens, Prism, and Traversal as
   profunctor-polymorphic functions.
3. Edward Kmett and contributors. `profunctors` package documentation.
   https://hackage.haskell.org/package/profunctors
   Verified 2026-08-21. Source for the Haskell production use in
   dimension 9 and the Strong, Choice, Star building blocks in
   dimension 8.
4. `lens` package documentation, module `Control.Lens.Iso`.
   https://hackage.haskell.org/package/lens/docs/Control-Lens-Iso.html
   Verified 2026-08-21. Source for the profunctor-polymorphic optics
   production use in dimension 9.
5. Typelevel Cats API documentation. `cats.arrow.Profunctor`.
   https://typelevel.org/cats/api/cats/arrow/Profunctor.html
   Verified 2026-08-21. Source for the Scala production use in
   dimension 9.

## Code examples

Three languages where the pattern is genuinely expressible in different
ways. TypeScript defines a small `Profunctor` interface and a concrete
instance for plain functions, the base case every other instance
generalises, then demonstrates `dimap` adapting both sides of a
function at once. Python shows the same construction as a dataclass
wrapping a callable, closer to how the pattern reads in a dynamically
typed language with duck-typed protocols rather than a named interface.
Swift shows a generic struct with `dimap` as a method, using Swift's own
generics to express the two independent type parameters, the shape the
pattern takes in a language with first-class protocols and strong static
typing but no built-in higher-kinded polymorphism. Java and Go are
omitted, because neither language's generics comfortably express a
reusable Profunctor interface across more than one concrete instance
within the length this entry has room for, and a single hard-coded
`dimap` method on one class would not add a genuinely distinct third
shape beyond what Python already shows. Rust is omitted for the same
reason as the language note on Rust throughout this family, ownership
makes a general higher-kinded Profunctor interface awkward to express
without substantial extra machinery.

### TypeScript

```typescript
interface ProfunctorFn<A, B> {
  readonly run: (a: A) => B;
}

function dimap<A, B, C, D>(
  pf: ProfunctorFn<A, B>,
  f: (c: C) => A,
  g: (b: B) => D
): ProfunctorFn<C, D> {
  return { run: (c: C) => g(pf.run(f(c))) };
}

function lmap<A, B, C>(pf: ProfunctorFn<A, B>, f: (c: C) => A): ProfunctorFn<C, B> {
  return dimap(pf, f, (b) => b);
}

function rmap<A, B, D>(pf: ProfunctorFn<A, B>, g: (b: B) => D): ProfunctorFn<A, D> {
  return dimap(pf, (a: A) => a, g);
}

const double: ProfunctorFn<number, number> = { run: (n) => n * 2 };

const composed = dimap(
  double,
  (s: string) => parseInt(s, 10),
  (n: number) => n.toString()
);

console.log(composed.run("21"));
```

### Python

```python
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")
D = TypeVar("D")


@dataclass(frozen=True)
class ProfunctorFn(Generic[A, B]):
    run: Callable[[A], B]

    def dimap(self, f: Callable[[C], A], g: Callable[[B], D]) -> "ProfunctorFn[C, D]":
        return ProfunctorFn(lambda c: g(self.run(f(c))))

    def lmap(self, f: Callable[[C], A]) -> "ProfunctorFn[C, B]":
        return self.dimap(f, lambda b: b)

    def rmap(self, g: Callable[[B], D]) -> "ProfunctorFn[A, D]":
        return self.dimap(lambda a: a, g)


double: ProfunctorFn[int, int] = ProfunctorFn(lambda n: n * 2)

composed = double.dimap(f=lambda s: int(s), g=lambda n: str(n))

if __name__ == "__main__":
    print(composed.run("21"))
```

### Swift

```swift
struct ProfunctorFn<A, B> {
    let run: (A) -> B

    func dimap<C, D>(f: @escaping (C) -> A, g: @escaping (B) -> D) -> ProfunctorFn<C, D> {
        ProfunctorFn<C, D> { c in g(self.run(f(c))) }
    }

    func lmap<C>(_ f: @escaping (C) -> A) -> ProfunctorFn<C, B> {
        dimap(f: f, g: { $0 })
    }

    func rmap<D>(_ g: @escaping (B) -> D) -> ProfunctorFn<A, D> {
        dimap(f: { $0 }, g: g)
    }
}

let double = ProfunctorFn<Int, Int> { $0 * 2 }

let composed = double.dimap(
    f: { (s: String) in Int(s) ?? 0 },
    g: { (n: Int) in String(n) }
)

print(composed.run("21"))
```
