---
name: Validation Applicative
slug: validation-applicative
family: 16-functional
category: Error Handling
aliases: [Accumulating Validation, Validated, Error-Accumulating Applicative]
first_described: "McBride and Paterson 2008"
maturity: canonical
related: [functor, applicative, monad, railway-oriented-programming, result-either]
incompatible_with: [monadic-validation-for-independent-checks]
verified: 2026-08-21
---

# Validation Applicative

## 1. Name, aliases, and lineage

The canonical name is Validation Applicative, often shortened to
Validation alone when the surrounding context is already about error
handling. The construction rests on the Applicative abstraction
introduced by Conor McBride and Ross Paterson in "Applicative
Programming with Effects", Journal of Functional Programming, volume
18, issue 1, 2008
(https://www.staff.city.ac.uk/~ross/papers/Applicative.pdf, verified
2026-08-21), which gave functional programming a general vocabulary for
combining independent effectful computations without requiring the
sequencing power of a full Monad. Validation is the specific
instantiation of that vocabulary where the effect is failure, and where
combining two failing computations accumulates both failures instead of
stopping at the first one.

The alias **Accumulating Validation** names the behaviour directly, the
defining property that separates this pattern from an ordinary Either
or Result type used monadically. **Validated** is the name Scala's Cats
library gives its own concrete type for the pattern.
**Error-Accumulating Applicative** is the generic, library-neutral name
used when describing the shape rather than any one library's spelling
of it.

## 2. Problem and context

A form, a configuration file, or an API request body carries several
independent fields, and each field has its own validation rule, a
required field, a numeric range, a format check, a cross-field
constraint. The obvious approach chains the checks with an ordinary
Either or Result type using monadic bind, so the first failing check
short-circuits the rest.

That approach produces a bad experience for the caller. A person filling
out a form with three invalid fields gets told about exactly one of
them, fixes it, resubmits, and is told about the second one, then the
third. The underlying checks are genuinely independent of each other,
none of them depends on the result of another, so there is no real
reason to stop at the first failure. What the caller actually wants is
every failure at once, so the whole problem can be fixed in a single
pass.

Validation Applicative solves exactly this. it runs every check, and
when more than one check fails, it combines all of the failures into
one accumulated error value, using the Applicative interface rather than
Monad, because Applicative composition does not need the result of one
computation to decide what the next computation is.

## 3. Forces

The pattern balances the following competing pressures.

- **Error completeness.** Favoured. Every independent check runs
  regardless of whether an earlier one failed, so the caller receives
  the full set of problems in one response instead of discovering them
  one at a time.
- **Sequencing power.** Sacrificed. Because Validation is Applicative
  rather than Monad, a later check cannot depend on the result of an
  earlier one. this is a genuine limitation, not an oversight, see
  dimension 4.
- **Error representation.** Favoured, at the cost of a small additional
  requirement. Accumulating more than one error needs a way to combine
  two error values into one, a Semigroup or an equivalent append
  operation, most often a list or a non-empty list of individual error
  messages.
- **Composability with existing Applicative combinators.** Favoured.
  Because Validation is an ordinary Applicative, it slots into any code
  already written generically against Applicative, map2, map3, sequence,
  and traverse all work on it unmodified.
- **Confusability with Either.** Sacrificed. Validation and Either are
  frequently represented with the identical two-constructor shape,
  Success or Failure, differing only in how their Applicative instance
  combines two failures, so a library that is not careful can expose a
  Validation whose Applicative instance behaves like Either's fail-fast
  one by accident.

## 4. Applicability and non-applicability

Reach for a Validation Applicative when the following hold.

- The checks being combined are genuinely independent, no later check's
  input or logic depends on an earlier check's result.
- The caller benefits from seeing every failure at once, most visibly a
  form, a configuration file, or an API request with several fields.
- There is a sensible way to combine two error values into one, a list
  append, a non-empty list append, or a monoid on the error type.
- The codebase already reaches for Applicative combinators such as map2
  or sequence elsewhere, so adopting a second Applicative-shaped type
  for errors fits an existing vocabulary rather than introducing a new
  one.

Do NOT reach for a Validation Applicative in these cases, and the reason
matters more than the rule.

- **A later check genuinely depends on an earlier one's result**,
  parsing a string into a number before checking the number is in
  range. that dependency needs Monad's sequencing, not Applicative's
  independence, and Validation's own Monad instance, where it exists at
  all, collapses back to fail-fast behaviour precisely because true
  dependency forces it to.
- **Only the first failure is ever shown to the caller**, or the caller
  has no use for more than one error at a time. plain Either or Result
  is simpler and needs no error-combining operation.
- **The error type has no sensible way to combine two values**, a
  single boolean failure flag, or an error type with no natural append.
  Inventing a combine operation purely to satisfy the interface produces
  an arbitrary and confusing result.
- **The checks are expensive**, and running every one regardless of
  earlier failures is not affordable, a check that hits a rate-limited
  external service for a field the user has plainly left empty should
  be skipped.

## 5. Structure

A Validation Applicative has two constructors, mirroring Either.

- **Success**, holding the value produced when every check passes.
- **Failure**, holding an accumulated error value, most often a
  non-empty list of individual error messages so a single failure and
  multiple failures share one representation.

The distinguishing operation is the Applicative apply, which combines
two Validation values holding a function and an argument.

- Success holding a function, applied to Success holding a value,
  produces Success holding the function applied to the value.
- Any other combination produces Failure. Success combined with
  Failure, or Failure combined with Success, produces that one Failure
  unchanged. Failure combined with Failure combines the two accumulated
  error values into one, using the error type's own combine operation.

This last case, Failure combined with Failure produces a combined
Failure rather than either input alone, is the entire difference between
Validation and a fail-fast Either.

## 6. ASCII structure diagram

```
Validation, two constructors

  Success v   holds a value v on the happy path
  Failure e   holds an accumulated error value e

Applicative apply, combining two Validation values

  Success f  x Success x  -> Success (f x)
  Success f  x Failure e2 -> Failure e2
  Failure e1 x Success x  -> Failure e1
  Failure e1 x Failure e2 -> Failure (e1 <> e2)
                             ^^ combine, both errors kept

Three independent field checks combined with map3

  checkName(input)
    -> Success "Ada" or Failure ["name required"]
  checkAge(input)
    -> Success 34 or Failure ["age must be positive"]
  checkEmail(input)
    -> Success "a@b.com" or Failure ["invalid email"]

  map3(checkName, checkAge, checkEmail, makeUser)
    all three Success -> Success (makeUser name age email)
    any Failures      -> Failure (every failing msg combined)
```

## 7. Dynamics

The runtime flow below shows three field checks running independently,
two of them failing, and their errors accumulating into one combined
Failure.

```
Caller                  map3(checkA, checkB, checkC, f)      Result

|-- checkName("") ---------------------------->|
|<-- Failure ["name required"] -----------------|

|-- checkAge(-5) -------------------------------->|
|<-- Failure ["age must be positive"] -------------|

|-- checkEmail("a@b.com") ------------------------>|
|<-- Success "a@b.com" -----------------------------|

|-- apply(checkName_result, checkAge_result) -------->|
|                                                      |-- Failure combined
|                                                      |   with Failure,
|                                                      |   errors appended
|<-- Failure ["name required", "age must be positive"]-|

|-- apply(that, checkEmail_result) --------------------->|
|                                                         |-- Failure applied
|                                                         |   to Success,
|                                                         |   Success ignored
|<-- Failure ["name required", "age must be positive"] ---|
```

## 8. Implementation variants

**Two-constructor sum type with a manually written Applicative
instance.** The most direct form, a Success and Failure constructor
exactly mirroring Either, with a hand-written apply function
implementing the four-case table in dimension 5. This is the shape
every library described in dimension 9 uses.

**Non-empty list as the accumulated error type.** Because the whole
point of the pattern is combining more than one error, the Failure
constructor almost always holds a non-empty list rather than a plain
list, so the type itself proves at compile time that a Failure always
carries at least one error, never an empty accumulation with nothing to
report.

**Semigroup or Monoid-parameterised error type.** Rather than fixing
the error type to a list, a more general implementation parameterises
over any type with a combine operation, a Semigroup in Haskell and
Scala terms, so a caller can accumulate errors as a set, a map keyed by
field name, or any other structure with a sensible append, not only a
list of strings.

**Validation built as a thin wrapper over Either with a swapped
Applicative instance.** Some libraries implement Validation as a
newtype around Either that reuses Either's own Functor instance, since
mapping over the success value behaves identically either way, but
supplies a completely different Applicative instance, the accumulating
one, so the two types share representation but diverge in behaviour
exactly at the apply operation.

**Deliberately no Monad instance, or a Monad instance that silently
degrades to fail-fast.** Because sequencing genuinely requires
depending on an earlier result, many Validation implementations expose
no Monad instance at all, forcing a caller who needs real dependency to
convert to Either first. Libraries that do supply a Monad instance for
convenience document plainly that it behaves like Either, one failure
at a time, and that only the Applicative instance accumulates.

## 9. Known production uses

**Haskell `validation`.** Chris Allen, Julie Moronuki, and contributors
publish the `validation` package on Hackage, providing a Validation type
whose Applicative instance accumulates errors through a Semigroup
constraint on the error type, deliberately separate from Either
specifically so the two behaviours cannot be confused at the type level.
Hackage package documentation, `validation`,
https://hackage.haskell.org/package/validation, verified 2026-08-21.

**Scala Cats `Validated`.** The Cats functional programming library for
Scala provides a `Validated` data type with exactly this accumulating
Applicative behaviour, documented as the type to reach for when
accumulating errors instead of short-circuiting during validation of
independent fields. Typelevel Cats documentation, `Validated`,
https://typelevel.org/cats/datatypes/validated.html, verified
2026-08-21.

**Haskell `Data.Either.Validation`.** The `either` package on Hackage
ships an alternative implementation, `Data.Either.Validation`, built
directly as a thin wrapper reusing Either's representation while
supplying its own accumulating Applicative instance, demonstrating the
wrapper implementation variant from dimension 8 in real, published code.
Hackage package documentation, `Data.Either.Validation`,
https://hackage.haskell.org/package/either/docs/Data-Either-Validation.html,
verified 2026-08-21.

## 10. Consequences

Positive.

- A caller sees every independent failure in one response instead of
  discovering problems one at a time across repeated resubmissions.
- The pattern reuses the ordinary Applicative interface, so existing
  generic combinators, map2, map3, sequence, traverse, work on it with
  no special casing.
- The two-constructor shape is familiar to anyone who already knows
  Either or Result, lowering the learning cost of adopting it.
- Because the error type is parameterised over a Semigroup, teams can
  accumulate errors as whatever shape suits them, a list of strings, a
  map keyed by field name, a structured error object with a combine
  rule.

Negative.

- Validation cannot express a check that genuinely depends on an
  earlier check's result. that case needs Monad, and Validation's own
  Monad instance, where it exists, reduces to fail-fast, which surprises
  a reader expecting accumulation everywhere.
- Validation and Either are close enough in shape that a codebase mixing
  both types, or converting carelessly between them, can silently lose
  the accumulating behaviour without any type error to flag the mistake.
- Accumulating errors needs a real combine operation on the error type,
  which is friction for an error type that was not designed with one in
  mind.
- Running every check regardless of earlier failures costs more, in
  wall-clock time and in resource use, than stopping at the first
  failure, which matters when a check is expensive.

## 11. Failure modes and misuse

**Reaching for the Monad instance and expecting accumulation anyway.**
Symptom. Two chained validations both fail, but only the first error
appears in the result, silently dropping the second. Cause. Using
Validation's Monad instance, bind or a do-block, rather than its
Applicative instance, map2 or applicative-style combination, when
Monad, wherever it is exposed at all, sequences and short-circuits
exactly like Either. Fix. Combine independent checks with the
Applicative operations, map2, map3, or a generic applicative sequence
over a list of checks, never with bind or a do-block.

**Choosing an error type with no sensible combine operation.**
Symptom. The accumulate step either fails to compile, or an ad hoc
combine function picks one error arbitrarily and discards the other,
defeating the whole purpose of the pattern. Cause. Reaching for
Validation before deciding what the accumulated error type actually is
and how two of them combine. Fix. Settle on a non-empty list, or
another type with a genuine Semigroup, as the error type before writing
any check.

**Running an expensive check regardless of earlier results.**
Symptom. A validation pass against a large batch of records runs
slower than expected, with profiling showing the same expensive
external call firing even for records that already failed a much
cheaper, earlier check. Cause. Validation deliberately runs every check
independently, so a check with real cost, a network call, a database
lookup, an expensive computation, pays that cost even when the input
has already failed an earlier, cheaper check. Fix. Order checks so a
cheap presence or format check runs first and skip the expensive check
when the cheap one has already failed, accepting the small accumulation
loss for that one field, or move the expensive check outside the
Validation composition entirely and run it only once the cheaper checks
have all passed.

**Converting between Validation and Either without noticing the
behaviour change.** Symptom. Code that worked correctly as a Validation
starts silently reporting only the first error after a refactor moved
it through an Either-typed function somewhere in the call chain. Cause.
The two types are close enough in shape, and conversions between them
common enough, that a refactor can swap accumulating behaviour for
fail-fast behaviour with no compiler error to catch it. Fix. Keep the
conversion boundary explicit and narrow, and add a test asserting
multiple accumulated errors survive the whole pipeline, not only the
Validation-typed portion of it.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Validation Applicative | Monadic Either or Result | Collecting errors by hand into a list | Throwing and catching multiple exceptions |
|---|---|---|---|---|
| Runs every independent check | Yes, always | No, stops at first failure | Yes, if written carefully | Rarely, first exception usually wins |
| Accumulates every failure | Yes, via the error Semigroup | No, only the first | Yes, but manually maintained | No, or only with substantial extra machinery |
| Reuses generic Applicative combinators | Yes | Yes, but they behave fail-fast | No, bespoke code | No |
| Expresses a genuine later-depends-on-earlier check | No | Yes | Yes, by hand | Yes |
| Learning cost for a team that knows Either | Low, same shape, different combine | Very low | Low, but reinvents what Validation gives for free | Low, familiar, but the wrong tool here |
| Requires a combine operation on the error type | Yes | No | Yes, implicit in the hand-written loop | No |

Reading of the table. Validation Applicative wins whenever the checks
are genuinely independent and the caller benefits from seeing every
failure, the common shape for form and request validation. Monadic
Either or Result wins whenever a later check depends on an earlier
result, or only the first failure matters. Hand-collecting errors into a
list reaches roughly the same outcome as Validation but reinvents its
combine logic ad hoc, with no reusable Applicative interface. Throwing
and catching multiple exceptions is rarely the right tool here, most
exception mechanisms are built around the first exception winning, not
around a deliberate collection of many.

## 13. Related and incompatible patterns

- **Applicative.** The interface Validation is built on. understanding
  Applicative composition, and why it does not need the result of one
  computation to determine the shape of the next, is the prerequisite
  for understanding why Validation can run every check independently.
- **Functor.** Validation's covariant mapping over the success value is
  an ordinary Functor instance, the simpler capability Applicative
  builds on top of.
- **Monad.** The sequencing power Validation deliberately does not
  have. a check that genuinely depends on an earlier result needs
  Monad, and reaching for Validation's Monad instance, where one
  exists, collapses back to the exact fail-fast behaviour Validation
  exists to avoid.
- **Railway-Oriented Programming.** The sibling pattern for the
  sequential, dependent case. where Validation accumulates independent
  failures, railway-oriented programming threads a single track of
  dependent steps, short-circuiting on the first failure, and the two
  are often used together in one system, Validation for the independent
  field checks, railway-oriented composition for the dependent steps
  after.
- **Result/Either.** The base two-constructor shape Validation reuses,
  and the type it is most easily confused with, since the two
  frequently share the identical representation and differ only in
  their Applicative instance.
- **Monadic validation for independent checks.** Conflicts directly.
  chaining genuinely independent checks with bind or a do-block silently
  reintroduces fail-fast behaviour and defeats the reason to reach for
  Validation in the first place, per the first failure mode in
  dimension 11.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered steps.

1. Identify a validation flow where the individual checks are genuinely
   independent, and confirm the current implementation stops at the
   first failure, either an explicit early return or a monadic Either
   chain.
2. Choose the accumulated error type and its combine operation, most
   often a non-empty list of error messages combined by concatenation.
3. Introduce the Validation type, Success and Failure, with an
   Applicative instance implementing the four-case combine table from
   dimension 5.
4. Rewrite each independent check to return a Validation instead of
   short-circuiting, and combine them with map2, map3, or a generic
   applicative sequence, never with bind.
5. Add a test asserting that two or more simultaneously failing checks
   produce a Failure containing every one of their messages, not only
   the first, since this is the property the whole refactor exists to
   establish.
6. Keep any genuinely dependent checks, where a later check needs an
   earlier result, outside the Validation composition, sequenced with
   ordinary Either or Result instead.

Removing the pattern when it stops earning its place. Signals that it
should go include a validation flow where every check has quietly become
dependent on an earlier one over time, or a caller that only ever reads
the first error out of an accumulated list.

1. Confirm whether the checks are still genuinely independent. if a
   later check now depends on an earlier result, Validation is no
   longer the right shape for that flow.
2. Confirm whether any caller actually consumes more than the first
   accumulated error. if none does, the accumulation is unearned
   complexity and a plain Either suffices.
3. Replace the Validation composition with a monadic Either chain, one
   call site at a time, keeping the existing tests green after each
   site, adding a test that only the first failure is expected where
   the old test asserted accumulation.
4. Delete the Validation type and its Applicative instance only after
   no call site references it.

## 15. Testing and verification

Easier because of the pattern.

- The accumulating property is a single, direct assertion. combining N
  failing checks produces a Failure whose accumulated error contains
  exactly the N expected messages, in the order the checks were
  combined, which is a straightforward table-driven or property test.
- Because Validation is Applicative and Applicative laws are well
  known, identity and composition, a single generic law-checking test
  written once against the Applicative interface is reusable unchanged
  across Validation and every other Applicative instance in the
  codebase.
- A test can construct arbitrary combinations of Success and Failure
  values directly, with no need for real input data or a real check
  function, since the four-case combine table in dimension 5 is pure
  and total.

Harder because of the pattern.

- A property test generating arbitrary combinations of Success and
  Failure needs the error type to have a real, testable Semigroup, and
  a badly chosen error type, one whose combine operation is not
  associative, can pass casual inspection while quietly violating the
  Semigroup law a correct accumulation depends on.
- Distinguishing accidental use of the Monad instance, per the first
  failure mode in dimension 11, from correct Applicative use is not
  visible from a passing single-failure test. the test must specifically
  exercise the multiple-simultaneous-failure case to catch the mistake.

Techniques that apply.

- **Accumulation property.** For an arbitrary set of N checks where a
  known, controlled subset fail, assert the resulting Failure's
  accumulated error contains exactly the messages from the failing
  subset, and Success is produced only when every check passes.
- **Semigroup law property, on the error type.** For arbitrary error
  values a, b, and c, assert combining them is associative, combining a
  with the combination of b and c equals combining the combination of a
  and b with c, the property the accumulation step silently depends on.
- **Applicative identity and composition laws.** Standard Applicative
  law tests, reused unchanged from any other Applicative instance in the
  codebase, applied to Validation.
- **Regression test for the Monad-instead-of-Applicative failure
  mode.** A direct test combining two known-failing checks with the
  Applicative operator and asserting both messages appear, guarding
  specifically against a future refactor that accidentally swaps in
  bind.

## 16. Observability signals

Validation itself is a pure, in-memory computation with no independent
runtime footprint, and inventing a dedicated production signal for the
type itself would be dishonest. Two signals at the boundary where
Validation results reach a person are worth naming.

What to record.

- A count, per validated request or form submission, of how many
  accumulated errors were returned, which is the direct measure of
  whether accumulation is actually earning its keep. a distribution
  clustered at exactly one error suggests the checks rarely fail
  together and a simpler fail-fast approach might serve equally well.
- A count of which specific checks fail most often, across accumulated
  submissions, which points product and design work at the field or
  rule that is confusing or too strict, information a fail-fast
  approach would have hidden behind whichever check happened to run
  first.

A healthy state. The accumulated-error-count distribution shows a
genuine tail past one error, confirming multiple simultaneous failures
are common enough that accumulation is worth its complexity, and the
per-check failure counts are stable and explainable.

A failing state. The accumulated-error-count distribution sits almost
entirely at one, suggesting the independence assumption behind reaching
for Validation was never really true for this flow, or one specific
check accounts for far more failures than the rest, which is a signal
to fix the check or its surrounding form guidance rather than to keep
accumulating around it indefinitely.

## 17. Security and privacy implications

Validation Applicative is close to neutral on security and privacy in
its own right, being a pure composition mechanism with no independent
storage or network surface, and inventing a specific attack surface
here would be dishonest. One practical implication is worth naming.

**Accumulated error messages can leak more than a single fail-fast
error would.** Because Validation deliberately runs and reports on
every check, including checks that touch sensitive fields, a caller who
submits a crafted, partially-invalid request receives more information
about the system's internal validation rules and the current state of
multiple fields at once than a fail-fast approach that would have
stopped after the first, less revealing, message. When any of the
checks being accumulated could reveal something sensitive, whether a
record already exists, whether a field matches an internal pattern,
review the combined error output for information disclosure the same
way a single error message would be reviewed, and consider stripping or
generalising individual messages before they reach an unauthenticated
caller.

## Code examples

Three languages where the pattern is genuinely idiomatic in different
ways. TypeScript defines a small discriminated union for Success and
Failure with a map2 combinator implementing the four-case table, the
shape a statically typed language with union types expresses directly.
Python shows the same construction with dataclasses and a small runtime
Semigroup convention, one attribute holding the accumulated errors,
closer to how the pattern reads without a dedicated typeclass system.
Swift shows an enum with associated values and a generic combine
function, using Swift's own enum-with-payload feature to express
Success and Failure directly. Java and Go are omitted, because
expressing a reusable, error-type-parameterised Applicative combinator
cleanly in either language needs more machinery than this entry has
room for without collapsing into a single hard-coded case that would
not add a genuinely distinct fourth shape. Rust is omitted for the same
reason as the language note elsewhere in this family, expressing a
general Applicative interface with a Semigroup-constrained error type
needs more trait machinery than fits the space here.

### TypeScript

```typescript
type Validation<E, A> =
  | { tag: "Success"; value: A }
  | { tag: "Failure"; errors: E[] };

function success<E, A>(value: A): Validation<E, A> {
  return { tag: "Success", value };
}

function failure<E, A>(errors: E[]): Validation<E, A> {
  return { tag: "Failure", errors };
}

function map2<E, A, B, C>(
  va: Validation<E, A>,
  vb: Validation<E, B>,
  f: (a: A, b: B) => C
): Validation<E, C> {
  if (va.tag === "Success" && vb.tag === "Success") {
    return success(f(va.value, vb.value));
  }
  const errors: E[] = [];
  if (va.tag === "Failure") errors.push(...va.errors);
  if (vb.tag === "Failure") errors.push(...vb.errors);
  return failure(errors);
}

function checkName(name: string): Validation<string, string> {
  return name.length > 0 ? success(name) : failure(["name required"]);
}

function checkAge(age: number): Validation<string, number> {
  return age > 0 ? success(age) : failure(["age must be positive"]);
}

const result = map2(checkName(""), checkAge(-5), (name, age) => ({ name, age }));

console.log(JSON.stringify(result));
```

### Python

```python
from dataclasses import dataclass, field
from typing import Generic, TypeVar, Callable, Union

E = TypeVar("E")
A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")


@dataclass(frozen=True)
class Success(Generic[A]):
    value: A


@dataclass(frozen=True)
class Failure(Generic[E]):
    errors: list = field(default_factory=list)


Validation = Union[Success, Failure]


def map2(va: Validation, vb: Validation, f: Callable[[A, B], C]) -> Validation:
    if isinstance(va, Success) and isinstance(vb, Success):
        return Success(f(va.value, vb.value))
    errors = []
    if isinstance(va, Failure):
        errors.extend(va.errors)
    if isinstance(vb, Failure):
        errors.extend(vb.errors)
    return Failure(errors)


def check_name(name: str) -> Validation:
    return Success(name) if name else Failure(["name required"])


def check_age(age: int) -> Validation:
    return Success(age) if age > 0 else Failure(["age must be positive"])


if __name__ == "__main__":
    result = map2(check_name(""), check_age(-5), lambda n, a: (n, a))
    print(result)
```

### Swift

```swift
enum Validation<A> {
    case success(A)
    case failure([String])
}

func map2<A, B, C>(
    _ va: Validation<A>,
    _ vb: Validation<B>,
    _ f: (A, B) -> C
) -> Validation<C> {
    switch (va, vb) {
    case let (.success(a), .success(b)):
        return .success(f(a, b))
    case let (.failure(e1), .failure(e2)):
        return .failure(e1 + e2)
    case let (.failure(e1), .success):
        return .failure(e1)
    case let (.success, .failure(e2)):
        return .failure(e2)
    }
}

func checkName(_ name: String) -> Validation<String> {
    name.isEmpty ? .failure(["name required"]) : .success(name)
}

func checkAge(_ age: Int) -> Validation<Int> {
    age > 0 ? .success(age) : .failure(["age must be positive"])
}

let result = map2(checkName(""), checkAge(-5)) { name, age in (name, age) }

print(result)
```

## 18. References

1. Conor McBride and Ross Paterson. "Applicative Programming with
   Effects". Journal of Functional Programming, volume 18, issue 1,
   2008.
   https://www.staff.city.ac.uk/~ross/papers/Applicative.pdf
   Verified 2026-08-21. Source of the Applicative abstraction Validation
   is an instance of.
2. Chris Allen, Julie Moronuki, and contributors. `validation` package
   documentation.
   https://hackage.haskell.org/package/validation
   Verified 2026-08-21. Source for the Haskell production use in
   dimension 9.
3. Typelevel Cats documentation. `Validated`.
   https://typelevel.org/cats/datatypes/validated.html
   Verified 2026-08-21. Source for the Scala production use in
   dimension 9.
4. `either` package documentation. `Data.Either.Validation`.
   https://hackage.haskell.org/package/either/docs/Data-Either-Validation.html
   Verified 2026-08-21. Source for the wrapper implementation variant in
   dimension 8 and the second Haskell production use in dimension 9.
