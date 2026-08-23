---
name: Primitive Obsession
slug: primitive-obsession
family: 02-code-smells
category: Code Smell
aliases: [Primitive Type Obsession, Stringly Typed Code]
first_described: "Fowler, Beck 1999"
maturity: canonical
related: [replace-primitive-with-object, value-object, whole-value, type-code, introduce-parameter-object]
incompatible_with: []
verified: 2026-08-02
---

# Primitive Obsession

## 1. Name, aliases, and lineage

The canonical name is Primitive Obsession. It is catalogued as a code smell in
Martin Fowler's *Refactoring. Improving the Design of Existing Code*, with the
"Bad Smells in Code" chapter credited to Kent Beck, Addison-Wesley, first
edition 1999, second edition 2018 (confirmed against the Wikipedia entry for
the book, which cites the same title and author, verified 2026-08-02,
https://en.wikipedia.org/wiki/Code_smell). The refactoring that treats it,
named in the book's catalog, has gone through a rename across editions. It
appears on Fowler's own maintained catalog site as **Replace Primitive with
Object**, with the older names **Replace Data Value with Object** and
**Replace Type Code with Class** listed as aliases of that same entry
(confirmed live, https://refactoring.com/catalog/replacePrimitiveWithObject.html,
verified 2026-08-02). Readers coming from the first edition of the book, or
from older blog posts, will know the fix by the older names even though the
smell's name has stayed constant across both editions.

**Stringly Typed Code** is a colloquial alias that circulated widely in
programming forums and later blog posts for the specific case where the
primitive in question is a string standing in for a value that should have its
own type. It is not Fowler's or Beck's own term. It names the same underlying
problem from the angle of everything being a string, which is the single most
common manifestation of primitive obsession in dynamically typed and loosely
typed codebases.

The related concept of a small, focused type that wraps a primitive and
carries its own identity and behaviour is called a **Value Object**. Fowler
defines a value object as an object whose equality is determined by the value
of its properties rather than by reference identity, and states plainly that
value objects should be immutable (confirmed live,
https://martinfowler.com/bliki/ValueObject.html, verified 2026-08-02). Eric
Evans gives the same concept a central place in domain modelling, describing
the value object as an object with no conceptual identity, distinguished by
its attributes rather than by a persistent identifier (Eric Evans,
*Domain-Driven Design. Tackling Complexity in the Heart of Software*,
Addison-Wesley, 2003). The name **Whole Value** is used in the same spirit by
part of the pattern community to describe replacing a scattered set of related
primitives, for example the four separate ints that make up a date, with a
single object that treats the whole concept as one unit. Whole Value is not
a Fowler coinage and its authorship is contested across pattern-community
sources, so it is recorded here as a community term rather than attributed to
a specific publication.

## 2. Problem and context

A codebase represents a concept from its domain, a monetary amount, a
telephone number, a temperature, an email address, a percentage, a date range,
a currency code, using the language's built-in scalar types instead of a type
of its own. The concept exists in the design, everyone on the team can name it
and would recognise it in a whiteboard sketch, but nowhere in the source code
does a type carry that name. Instead the concept is represented as an `int`, a
`double`, or a `String`, and every place that needs to validate, format,
compare, or operate on the concept repeats its own copy of the rules for doing
so.

The smell is not that primitives exist. Every language has them and every
program uses them. The smell is that a primitive is standing in for a *domain
concept with its own rules*, and the type system has been told nothing about
those rules. The compiler or interpreter will happily accept an `int`
representing a user's age where an `int` representing a shopping cart's item
count was expected, because to the type checker they are both just `int`. The
concept the human intended has been erased at the type level, and the
program's correctness now depends entirely on programmers remembering, every
time, which particular `int` means what, and re-deriving the same validation
and formatting logic by hand at every call site.

The context in which this becomes a genuine problem, rather than an
academic nitpick, has three ingredients working together. First, the concept
has rules beyond its raw storage. A percentage must stay between zero and one,
or zero and a hundred, and the two conventions must never be mixed silently. A
monetary amount is tied to a currency and cannot be added to an amount in a
different currency without an explicit conversion. Second, the concept
recurs across the codebase, so the same validation, the same formatting, or
the same comparison logic is written more than once, in more than one place,
by more than one person, drifting slowly out of agreement with itself.
Third, the primitive representation is ambiguous at the call site. A function
signature that reads `createUser(String, String, String)` tells the reader
nothing about which string is the name, which is the email, and which is the
password, and the compiler will not stop a reader from passing them in the
wrong order.

## 3. Forces

**Familiarity against expressiveness.** A primitive is universally understood
and requires zero onboarding. A domain type requires the reader to go learn
what `EmailAddress` guarantees before they can trust it, but once learned it
communicates far more than `String` ever could at the call site.

**Speed of a first cut against long-run correctness.** Reaching for `int` or
`string` is the fastest way to get a feature compiling today. Introducing a
wrapper type is slower on day one and pays for itself starting on day two,
the first time the validation rule is needed a second place, or the first
time a bug is caused by two `int` parameters being swapped.

**Serialization simplicity against domain fidelity.** Primitives cross a
JSON boundary, a database column, or a wire protocol with zero friction.
Domain types typically need explicit (de)serialization code, a mapping layer,
or annotations, which is real engineering cost that a raw primitive avoids.

**Language ergonomics.** In a language with rich operator overloading,
implicit conversions between named types, and cheap value types (Swift's
`struct`, Kotlin's `value class`, C#'s `readonly struct`, Rust's newtype
`struct Wrapper(T);`), the cost of wrapping a primitive is close to zero at
both compile time and runtime. In a language that treats every object as a
heap allocation with no operator overloading and clumsy equality semantics,
the same wrapping carries a real allocation and boilerplate cost, and the
force tilts further toward tolerating primitives longer.

**Team size and churn against local convenience.** A single author working
alone can hold every implicit rule about what a bare `int` means in their
head. As the team grows, or as time passes and the original author moves on,
the tribal knowledge that used to compensate for the missing type erodes, and
the smell's cost rises even though the code has not changed.

Primitive obsession, when it is a real problem rather than a false positive,
favours long-run correctness, domain fidelity, and safety against accidental
misuse, at the direct cost of upfront implementation speed and, in some
languages, runtime and memory overhead from extra allocations.

## 4. Applicability and non-applicability

Reach for a domain type in place of a primitive when the following hold.

- The value has validation rules that would otherwise be duplicated at every
  point of use, for example a valid range, a required format, or a set of
  legal values.
- The value has behaviour attached to it that is currently implemented as free
  functions taking the primitive as a parameter, for example formatting a
  phone number for display, or computing whether one date range overlaps
  another.
- Two values of the same primitive type are not interchangeable in the domain,
  for example a user ID and a product ID both stored as a plain integer, where
  passing one where the other is expected compiles cleanly and produces a
  silent bug.
- The value is passed as a parameter alongside several other primitives of the
  same type, so the parameter list has become an ordered sequence of
  same-typed values that only convention, not the compiler, keeps in the
  right order.
- The concept recurs in three or more places in the codebase in slightly
  different representations, for example a currency amount sometimes stored
  as a float in dollars and sometimes as an integer in cents.

Do not reach for a domain type when any of the following hold.

- The value genuinely is a bare number or string with no domain rules beyond
  what the primitive already enforces, for example a loop counter, an array
  index, or a temporary accumulator inside a single function. Wrapping these
  produces ceremony with no corresponding safety gain, and is itself a form
  of over-engineering some practitioners call primitive avoidance.
- The performance budget is tight enough that the extra indirection or
  allocation from a wrapper type is measured and shown to matter, for example
  in a hot inner loop over millions of elements in a language without
  zero-cost value types. Stripe's public API represents every monetary amount
  as a plain integer in the smallest unit of the currency rather than as a
  dedicated money object, explicitly to avoid floating-point precision loss
  and to keep the wire format simple and language-agnostic (confirmed live,
  Stripe API reference for the Charge object's `amount` field, verified
  2026-08-02, https://docs.stripe.com/api/charges/object). This is a
  deliberate boundary decision. Client libraries built on top of that wire
  format frequently do wrap the integer in a domain type internally, so the
  smell can be genuinely absent at a system boundary while still being
  present, and worth fixing, one layer in.
- The value crosses a serialization boundary where the ecosystem convention
  is a bare primitive, and introducing a wrapper type would only move the
  primitive obsession into a translation layer without eliminating it, unless
  that translation layer is itself the one place the concept should live.
- The code is a short-lived script, a one-off migration, or a prototype whose
  entire lifetime is measured in hours, where the amortised cost of the extra
  type will never be recovered.
- Wrapping every single primitive in the codebase indiscriminately, without
  regard to whether it carries domain rules. This produces what practitioners
  sometimes call primitive obsession about primitive obsession, where
  `Count` wraps an `int` that is genuinely just a count with no invariant
  beyond non-negativity, adding a layer of indirection that a comment would
  have communicated just as well.

## 5. Structure

Primitive obsession, unlike a design pattern, has no participant structure of
its own to diagram, because it is the *absence* of structure. It is
identifiable by what is missing rather than what is present. The structural
description below is of its treatment, the Replace Primitive with Object
refactoring, since that is what gives the smell a shape to compare against.

- **Domain concept.** The idea being represented, for example an email
  address, a money amount, or a percentage. It exists in the requirements and
  in conversation, whether or not the code has a type for it.
- **Primitive stand-in.** The built-in scalar type, typically a string,
  integer, or floating-point number, currently used to hold the domain
  concept's raw value, with no type-level distinction from any other use of
  the same primitive.
- **Scattered validation and formatting logic.** The functions, methods, or
  inline checks, duplicated across the codebase, that enforce the domain
  concept's rules on the primitive at each point of use.
- **Value object, the fix.** A small, typically immutable type that wraps
  the primitive's raw storage, validates it once at construction, exposes the
  domain's operations as methods, and gives the compiler or type checker a
  name it can use to reject a value of the wrong domain concept even though
  the underlying storage type is identical.
- **Equality and comparison contract.** The value object overrides or defines
  equality, hashing, and ordering based on its wrapped value rather than on
  object identity, because two value objects with the same underlying data
  must be treated as the same value throughout the program.

## 6. ASCII structure diagram

```
BEFORE (primitive obsession)

  +--------------------------+
  | OrderService.placeOrder( |
  |   customerId: int,       |
  |   productId: int,        |
  |   email: String,         |
  |   quantity: int)         |
  +--------------------------+
            | raw String, three separate call sites
            v
  +---------------------------------+
  | validateEmail(str)              |
  | formatEmail(str)                |
  | sendConfirmation(str)           |
  | each re-validates independently |
  +---------------------------------+

  customerId and productId are both plain int, so nothing
  stops placeOrder(productId, customerId, ...) from
  compiling and silently swapping the two arguments.


AFTER (Replace Primitive with Object)

  +---------------------------+
  | OrderService.placeOrder(  |
  |   customerId: CustomerId, |
  |   productId: ProductId,   |
  |   email: EmailAddress,    |
  |   quantity: Quantity)     |
  +---------------------------+
            | EmailAddress
            v
  +----------------------+
  | EmailAddress         |
  | - value: String      |
  | - validate() private |
  | + format(): String   |
  | + equals(other)      |
  +----------------------+

  CustomerId and ProductId are now distinct types.
  placeOrder(productId, customerId, ...) is a compile-time
  type error, not a silent runtime bug.
```

## 7. Dynamics

The dynamics of the smell itself are a decay pattern over time, not a runtime
interaction. The dynamics of the refactoring, Replace Primitive with Object,
are a fixed sequence of steps, and Fowler's own catalog page states the
mechanics as a self-encapsulate-then-wrap sequence (confirmed live,
https://refactoring.com/catalog/replacePrimitiveWithObject.html, verified
2026-08-02). The flow below shows both, side by side, as the smell is
introduced and then remediated.

```
TIME  ---------------------------------------------------------------->

DECAY (how the smell accumulates)

  t0: field discountPercent added to Order as a raw double, value 0.0..1.0

  t1: a second class, Invoice, needs the same concept, developer copies
      the raw double and re-derives the 0.0..1.0 convention from memory

  t2: a third developer, unaware of the convention, stores 15 instead of
      0.15 in a new ReportRow class, no error, silent data corruption

  t3: bug ticket filed, "discount showing as 1500%", root cause traced
      back through three different in-memory conventions for the "same"
      concept

REMEDIATION (Replace Primitive with Object, applied at one call site)

  1. Use Encapsulate Variable so every read and write of the primitive
     goes through an accessor, if it does not already.
  2. Create the new value type (e.g. Percentage) wrapping the primitive.
  3. Add a validating constructor or factory to the new type, enforcing
     the invariant (here, 0.0 <= value <= 1.0) in exactly one place.
  4. Change the accessor's return type and the field's declared type to
     the new value type, one call site at a time, letting the compiler
     or type checker point at every place that still expects the raw
     primitive.
  5. Move the scattered formatting and comparison logic that used to live
     at each call site into methods on the new type.
  6. Delete the now-redundant validation duplicated elsewhere, since the
     constructor is the only place the invariant can be violated.
```

## 8. Implementation variants

The core idea, one named type instead of a bare primitive, is implemented
differently depending on what the host language offers for cheap, safe
wrapping.

**Class-based value object (Java, TypeScript, C#, older idiomatic style).**
A small class with a single private field holding the primitive, a
constructor or static factory that validates and normalises, and overridden
equality and hashing based on that field. This is the classic form Fowler and
Evans both describe. Its cost in a language without operator overloading is
that arithmetic and comparison have to be spelled out as methods
(`amount.add(other)` instead of `amount + other`), which is more verbose than
the primitive it replaces but removes an entire class of accidental
type-confusion bugs.

**Newtype wrapper (Rust, Haskell-influenced style).** A tuple struct with a
single field, `struct UserId(u64);`, that the compiler treats as a distinct
type from `u64` and from any other single-field tuple struct, at zero runtime
cost. Rust's own type system makes this variant essentially free, and the
`#[derive(...)]` mechanism lets the wrapper opt back into equality, ordering,
hashing, and Debug formatting with one line rather than hand-written
boilerplate.

**Branded or nominal type (TypeScript, Flow-era JavaScript).** TypeScript's
structural type system means two `type UserId = number` and `type ProductId =
number` aliases are interchangeable at compile time, defeating the whole
purpose. The community workaround, a branded type using an intersection with a
unique symbol or a phantom `__brand` property, recovers nominal typing purely
at the type level with zero runtime representation change, at the cost of a
small amount of boilerplate and a construction function that must be called
instead of a bare literal.

**Value class or inline class (Kotlin's `value class`, planned Java Valhalla
inline classes, C#'s `readonly record struct`).** Newer JVM and CLR-family
languages offer a wrapper type that the compiler is permitted to erase at
runtime in many contexts, giving class-based clarity at close to the runtime
cost of the bare primitive. This variant directly targets the wrapping is
too expensive objection from dimension 3.

**Domain-specific whole value with rich behaviour (Money, Percentage,
DateRange).** The variant Evans and the Whole Value community emphasise, where
the wrapper is not a thin validation shell but carries genuine domain
operations, `money.convertTo(currency, rate)`, `range.overlaps(other)`,
`percentage.of(quantity)`. This is the variant that most fully cashes in the
benefit of the refactoring, because it is where the scattered logic dimension
6 describes actually gets consolidated, rather than merely relocated behind a
getter.

**Enum or sealed type replacing a type code (Replace Type Code with Class,
the pre-2018 name for part of this same catalog entry).** When the primitive
in question is a small closed set of integer or string constants standing in
for a category, `orderStatus: int` with the values 0, 1, 2 meaning pending,
shipped, and cancelled, the fix is a language-native enum or sealed hierarchy
rather than a general-purpose wrapper class, because the compiler can then
enforce exhaustiveness at every switch or match over the value.

## 9. Known production uses

**java.time (JSR 310), replacing java.util.Date and java.util.Calendar.**
The JSR 310 specification, led by Stephen Colebourne, Michael Nascimento
Santos, and Roger Riggs, was created specifically because Java's date and time
handling had no classes for modelling other concepts, non-time-zone dates or
times, durations, periods and intervals having no class representation in
Java SE, and because the mutable `Date` and `Calendar` types forced every
consumer to reason about thread safety and cloning by hand (confirmed live,
JSR 310 specification page, https://jcp.org/en/jsr/detail?id=310, verified
2026-08-02). Before java.time, a date was frequently represented internally as
a `long` millisecond timestamp, an `int` combination of year, month, and day
fields, or a formatted `String`, all three of which are textbook primitive
obsession over the single concept of a point in time or a calendar date.
java.time introduces distinct, immutable types, `LocalDate`, `LocalTime`,
`Instant`, `Duration`, `Period`, each with its own validated construction and
its own arithmetic methods, directly replacing the scattered primitive
representations that predated it.

**NodaTime, the .NET analogue built by Jon Skeet.** NodaTime's own
documentation frames the library around a deliberate multiplication of small,
precise types, `LocalDate`, `Instant`, `Duration`, `LocalTime`,
`LocalDateTime`, `OffsetDateTime`, and `ZonedDateTime`, each documented on its
own page, explicitly so that developers choose the semantically correct type
for a given concept rather than reaching for the single general-purpose
built-in `DateTime` for every temporal value regardless of whether it
represents a timezone-free calendar date or a globally unambiguous instant
(confirmed live, NodaTime user guide index, https://nodatime.org/3.2.x/userguide/,
verified 2026-08-02). This is a direct, named, still-maintained production
counterexample to representing every temporal concept as the platform's one
built-in `DateTime` primitive.

**RFC 4122 UUID as a distinct 128-bit type, not a string.** RFC 4122 defines a
UUID as 128 bits long with an internal representation composed of specific
named fields (`time_low`, `time_mid`, `time_hi_and_version`,
`clock_seq_hi_and_reserved`, `clock_seq_low`, and `node`), and treats the
familiar hyphenated hexadecimal string as a separate textual representation
produced only when the binary value needs to be encoded, for example as a URN
(confirmed live, RFC 4122, https://www.rfc-editor.org/rfc/rfc4122, verified
2026-08-02). Every language's standard or de facto UUID library, Java's
`java.util.UUID`, Python's `uuid.UUID`, Go's `github.com/google/uuid`, follows
this by exposing UUID as a dedicated type with its own equality and parsing,
rather than leaving callers to compare UUIDs as raw strings, which would
silently treat two differently-cased hexadecimal representations of the same
UUID as different values despite RFC 4122 UUIDs being case-insensitive in
their canonical textual form.

## 10. Consequences

Positive consequences of fixing the smell.

- Invalid states become unrepresentable, or at minimum unrepresentable past
  construction, because validation happens once in the wrapper type's
  constructor instead of being re-derived at every call site.
- Function and method signatures become self-documenting. A parameter typed
  `EmailAddress` tells the reader what it is without a name, a comment, or a
  trip to the implementation.
- The compiler or type checker can catch a whole class of argument-order and
  argument-substitution bugs at build time that were previously only
  discoverable at runtime, or not discoverable at all.
- Domain behaviour that used to live as scattered free functions taking the
  primitive as a parameter gets a single home, reducing duplication and the
  drift between duplicated copies described in dimension 2.
- Refactoring the internal representation of the concept later, for example
  changing a money amount's internal storage from a float to an integer count
  of minor units, becomes a change confined to one type instead of a
  find-and-replace across the whole codebase.

Negative consequences of fixing the smell.

- Extra ceremony at every construction site. A bare `int` literal becomes
  `new Percentage(15)` or `Percentage.of(15)`, which is more to type and more
  to read for the simplest cases.
- In languages without cheap value types, each wrapper is a heap allocation,
  which is a real and sometimes measurable cost in hot paths, and can create
  additional garbage-collector pressure at scale.
- Serialization and persistence layers need explicit mapping code, an
  (de)serializer, a custom JSON converter, an ORM column type, that a bare
  primitive would not have required, shifting complexity rather than removing
  it in aggregate, even as it removes complexity from the domain layer
  specifically.
- Over-application produces a wrapper type for every trivial scalar in the
  system, adding indirection with no corresponding safety benefit and slowing
  down onboarding for exactly the wrong reason, the opposite failure mode from
  the smell itself, discussed further in dimension 11.
- Equality, hashing, and comparison must be implemented correctly on every new
  wrapper type, and a wrapper type with reference-identity equality by
  accident, the default in many object-oriented languages unless explicitly
  overridden, is worse than the primitive it replaced, because it looks like
  a value type while behaving like a reference type.

## 11. Failure modes and misuse

Symptom, cause, and fix are given as explicit triples below, because the
abstract description of the smell rarely matches how a reader will actually
encounter it in a real codebase or a real code review.

**Symptom.** Two same-typed parameters in a function signature keep getting
swapped in practice, and code review keeps catching it, or worse, does not.
**Cause.** Two or more distinct domain concepts, for example a source account
ID and a destination account ID in a funds transfer, are both represented as
the identical primitive type, `int` or `long`, so nothing but argument order
and parameter naming distinguishes them, and both of those are advisory
rather than enforced. **Fix.** Wrap each in its own distinct type,
`SourceAccountId` and `DestinationAccountId`, or at minimum two
differently-named newtypes over the same primitive, so the compiler rejects
the swapped call at build time instead of a human catching it, sometimes, in
review.

**Symptom.** The same regex, the same range check, or the same formatting
function shows up in a code search across five or more files, each copy
subtly different from the others. **Cause.** A domain concept with real
validation rules, an email address, a postal code, a percentage, is stored as
a bare string or number everywhere it is used, so every author who needed to
validate or format it wrote their own copy rather than discovering an
existing one, because there was no type to search for and no natural home for
the logic. **Fix.** Introduce the value type once, move every one of the
duplicated implementations' logic into it, and delete the duplicates,
verifying via the compiler or a full test suite that no call site's
behaviour has silently changed in the consolidation.

**Symptom.** A bug ticket describes data that is off by a factor of one
hundred, a discount showing as 1500 percent, a temperature off by a scaling
factor, a currency amount that is a hundred times too large or too small.
**Cause.** Different parts of the system independently chose different
conventions for the same underlying primitive, for example percentage stored
as 0.0 to 1.0 in one class and 0 to 100 in another, with nothing enforcing
which convention a given raw number follows at any point in the flow.
**Fix.** The value type's constructor fixes the convention in exactly one
place and normalises every input to it, so the ambiguity that caused the bug
cannot exist once the migration to the wrapper type is complete.

**Symptom, over-application, the mirror-image misuse.** A code review is
dominated by arguments about whether `Count` should wrap `int`, or whether a
loop index needs a `LoopIndex` type, and the team velocity visibly drops
while adding no corresponding defect reduction. **Cause.** Primitive
obsession has been misread as never use a bare primitive rather than do not
use a bare primitive for a domain concept with rules attached to it, and
every scalar in the system, including ones with no invariant beyond their own
storage type, is being wrapped indiscriminately. **Fix.** Apply the
applicability test from dimension 4. Does this value have a validation rule,
a piece of behaviour, or a risk of type confusion with another same-typed
value, and stop wrapping values that answer no to all three.

**Symptom.** A "fixed" value object still lets invalid data through, because
the invalid data was constructed via a public setter or a public mutable
field after the object was created, bypassing the validating constructor.
**Cause.** The refactoring introduced a class with the right name but did not
make the class immutable, so validation at construction time is not actually
sufficient, an object can be mutated into an invalid state after the fact.
**Fix.** Make the wrapper genuinely immutable, no public setters, no public
mutable fields, any change operation returns a new instance rather than
mutating the existing one, consistent with Fowler's stated rule that value
objects should be immutable (confirmed live,
https://martinfowler.com/bliki/ValueObject.html, verified 2026-08-02).

## 12. Trade-off matrix

The comparison is framed as three concrete design choices for representing a
recurring domain concept, since Primitive Obsession itself is a smell rather
than a competing pattern, and the honest comparison is against the named
alternatives a team would actually be choosing between.

| Force | Bare primitive (the smell) | Class-based value object | Newtype / branded type |
|---|---|---|---|
| Compile-time misuse protection | None, any same-typed primitive is interchangeable | Full, distinct type per concept | Full, distinct type per concept, at or near zero cost |
| Onboarding cost for a new type | Zero, everyone already knows int and string | Moderate, reader must learn the wrapper's contract | Moderate, same as class-based |
| Runtime and memory overhead | None | Allocation per instance in most OO languages | Near zero in Rust and similar, erased at runtime in JVM/CLR inline value types |
| Where validation lives | Duplicated at every call site, or nowhere | Centralised in one constructor | Centralised in one constructor or smart constructor function |
| Serialization boundary friction | None, primitives cross boundaries natively | Explicit mapping code usually required | Usually needs an explicit unwrap/construct at the boundary, similar cost to class-based |
| Refactoring cost to change internal representation later | High, every call site touches the raw type directly | Low, confined to the wrapper's internals | Low, confined to the wrapper's internals |
| Best fit | Loop counters, indices, values with no domain rule | Languages with heap objects and rich behaviour needs, e.g. Java, TypeScript, older C# | Languages with cheap zero-cost wrapping, e.g. Rust, Kotlin value classes, TypeScript branded types |

## 13. Related and incompatible patterns

**Value Object** is the structural shape the fix takes. Fowler's own
definition of a value object, equality determined by attribute values rather
than by identity, immutability as a stated rule, is exactly the contract a
Primitive Obsession fix must satisfy to actually solve the problem rather than
merely relocate it, as dimension 11's immutability failure mode demonstrates
(confirmed live, https://martinfowler.com/bliki/ValueObject.html, verified
2026-08-02).

**Replace Primitive with Object, also known as Replace Data Value with Object
and Replace Type Code with Class,** is the named refactoring in Fowler's
catalog that performs the fix mechanically, described in dimension 7's
dynamics (confirmed live,
https://refactoring.com/catalog/replacePrimitiveWithObject.html, verified
2026-08-02).

**Introduce Parameter Object**, a sibling refactoring in the same catalog,
composes naturally with this fix when several related primitives are always
passed together as a group of parameters, for example `startDate` and
`endDate`, rather than each individually representing a single concept.
Introduce Parameter Object groups them into one parameter object first;
Primitive Obsession's fix is then applied within that new object if its
individual fields also have their own domain rules, for example replacing a
raw pair of ints with a `DateRange` object that itself validates that the
start is before the end.

**Type Code (as an anti-pattern name in its own right)** is a narrower,
specific instance of Primitive Obsession, where the primitive in question is
specifically a small set of integer or string constants standing in for a
category or state. It is treated distinctly enough in Fowler's earlier
catalog editions, under the name Replace Type Code with Class or Replace Type
Code with Subclasses, to be worth naming separately even though it is a
special case of the same underlying smell.

**Data Class**, a separate code smell in the same catalog, is a related but
distinct problem, a class with fields and accessors but no behaviour. A value
object produced by fixing Primitive Obsession can regress into a Data Class
if the team stops after adding the wrapper type but never migrates the
scattered behaviour, described in dimension 2, into the new type's methods.
The two smells are frequently confused because both involve a small object
holding a value, but Data Class is about a class that has no business logic
at all, while Primitive Obsession is about the complete absence of a
domain-specific type in the first place.

**Strategy pattern** and **enum-based state machines** are the typical
follow-on once a Type Code has been replaced with a class hierarchy or an
enum, because a validated, closed set of states is the natural substrate for
a state machine or a per-state strategy object.

There are no patterns that are structurally incompatible with fixing
Primitive Obsession. It is a foundational hygiene concern, closer to a
prerequisite for other patterns than a competitor to any of them, since a
misrepresented domain concept undermines the reliability of anything built on
top of it.

## 14. Refactoring path in and out

Introducing the fix, step by step, following Fowler's stated mechanics for
Replace Primitive with Object (confirmed live,
https://refactoring.com/catalog/replacePrimitiveWithObject.html, verified
2026-08-02).

1. If the primitive value is stored in a field accessed directly rather than
   through an accessor, apply Encapsulate Variable first, so every read and
   write already goes through a single choke point.
2. Create the new value class, with a single field holding the primitive.
3. Add a constructor, or a static factory function in languages that favour
   that idiom, that validates the incoming primitive and throws or returns an
   explicit error on invalid input, so the invariant is enforced at exactly
   one place.
4. Change the field's declared type from the primitive to the new value
   class, and change the accessor to construct and return an instance of the
   new type.
5. Let the compiler or type checker enumerate every call site that still
   expects the old primitive type, and update each one, typically by calling
   a `.value` accessor or equivalent at the boundary where the primitive is
   genuinely still needed, for example a database driver call or a wire
   serialization point.
6. Migrate the scattered validation, formatting, and comparison logic found
   during dimension 2's audit into methods on the new type, and delete the
   original duplicated copies once every call site has been switched over and
   verified.
7. Where the primitive was a small closed set of values, a Type Code,
   consider a further step, Replace Conditional with Polymorphism or a
   language-native enum, once the values are represented by the new type
   rather than the raw primitive.

Removing the fix, when the wrapper has stopped earning its place, is the rarer
direction. A value object should be removed, folding its single field back
into a bare primitive, when every one of the applicability criteria from
dimension 4 has stopped holding, there is no validation rule left worth
centralising, no behaviour left attached to the type, and no risk of type
confusion with another same-typed value, typically because the surrounding
code that used to need those guarantees has itself been deleted or radically
simplified. This direction is rare in practice. Most Value Object removals
observed in real codebases are actually the opposite mistake, a class that
was already a thin Data Class being flattened prematurely while genuine
domain rules still live in scattered call-site code, which is a regression
back into the smell rather than a legitimate simplification.

## 15. Testing and verification

Testing a codebase before the fix is applied is testing against a moving,
implicit contract, because the validation rule lives at each call site rather
than in one place, and a test written against one call site's copy of the
rule says nothing about whether a different call site's copy agrees with it.
This is itself a diagnostic signal. When adding a new test for a primitive's
validation rule requires deciding which of several existing, slightly
different implementations to test against, that is direct evidence the smell
is present.

After the fix, testing becomes substantially easier in one specific way. The
value object's constructor becomes the single place invalid input can be
rejected, so a table-driven or parametrised test covering the boundary
conditions of the domain rule, the empty string, the maximum length, the
minimum and maximum numeric bounds, needs to exist exactly once, against the
constructor, rather than once per call site. Any code that merely accepts an
already-constructed instance of the value object no longer needs its own
copy of that validation test, because a value of the type is a proof, by
construction, that the invariant already holds. This is the core testing
benefit of the make illegal states unrepresentable framing common in the
value-object and domain-modelling literature.

What becomes harder to test is the boundary itself, the point where a raw
primitive from an external source, an HTTP request body, a database row, a
third-party API response, is first converted into the domain type. That
conversion path needs explicit negative tests, malformed input, missing
fields, out-of-range values, that a bare-primitive representation, which
silently accepted anything of the right built-in type, would not have needed
in the same way, because there was previously no single place where the
conversion happened at all. Mutation testing is a useful technique here
specifically, deleting or weakening the constructor's validation logic and
confirming a test actually fails, because a validating constructor with a
subtly incomplete check is worse than no validation at all if it gives the
rest of the codebase false confidence that every instance in play is
guaranteed valid.

## 16. Observability signals

A value object introduced to fix Primitive Obsession is, by construction,
mostly invisible in production observability, and that invisibility is itself
the signal of health, because a value that reaches every downstream consumer
already validated produces no downstream validation-failure log lines. The
signals worth watching are concentrated at the boundary where raw primitives
still enter the system and get converted.

Construction failure rate at the boundary is the most direct signal. A metric
counting how often the value type's validating constructor rejects an
incoming primitive, tagged by the upstream source, a specific API client, a
specific batch import job, a specific user-facing form, points at either
degraded upstream data quality or a validation rule that itself needs
revisiting. A sudden spike traceable to one upstream source points at a
change in that source's behaviour. A broad, sustained baseline of rejections
across many sources suggests the rule is too strict for real-world data and
needs review rather than the data needing to change.

Equality and hashing correctness in caches and deduplication is the second
signal. Because value objects are compared by value rather than identity, a
cache keyed by a value object with an incorrectly implemented equals and
hashCode pair, one that falls back to default reference equality, will
silently produce cache misses that look like a cache with too small a
capacity or too aggressive an eviction policy. A healthy value-typed cache
key shows a hit rate consistent with the actual repetition rate of the
underlying data. A value-typed cache key with a broken equality contract
shows a hit rate close to zero regardless of capacity, which is the
diagnostic tell.

Serialization round-trip drift is the third signal, where the value object
crosses a persistence or wire boundary. A round-trip test or a canary check
that writes a value, reads it back, and compares for equality, run
continuously against a sample of production traffic or a synthetic canary
record, catches the case where a schema migration or a library upgrade has
silently changed how the type serializes, for example a currency amount's
minor-unit convention flipping between two deployments.

## 17. Security and privacy implications

Primitive Obsession has a genuine, if indirect, security surface. When a
value with security-relevant rules, a session token, a password hash, an
authorization scope string, is represented as a bare `String`, nothing at the
type level distinguishes it from any other string in the program, which makes
it structurally possible to pass a session token where a display name was
expected, to log a password hash into a general-purpose logging call that was
only intended for user-facing strings, or to concatenate an unsanitised raw
string directly into a SQL query or shell command because the type system
gave no signal that the value needed special handling. Wrapping such values
in a dedicated type does not, on its own, prevent misuse, but it creates a
single, auditable point where the correct handling, redaction in logs,
constant-time comparison for secrets, parameterisation before use in a query,
can be enforced by the type's own methods rather than relying on every future
caller remembering to do so correctly by hand.

A specific, well-known instance of this is representing a secret, an API key,
a password, a token, as a plain string that a language's default logging,
debug-printing, or error-message formatting will happily include verbatim in
a log line or a stack trace. A dedicated wrapper type can override its own
string conversion or debug representation to redact the value, a placeholder
such as `REDACTED` instead of the real secret, which a bare primitive has no
mechanism to do, because every string in the program shares the exact same
default formatting behaviour.

There is a countervailing concern worth stating plainly, rather than treating
wrapping as an unconditional security improvement. A wrapper type that
exposes an unrestricted string conversion, an equality check that leaks
timing information about a secret's value through a non-constant-time
comparison, or a public accessor that hands back the raw underlying primitive
with no further control, reproduces the exact same exposure as the bare
primitive while giving reviewers false confidence that it is wrapped, so it
is safe. The security benefit of fixing Primitive Obsession is realised only
when the wrapper's own contract, its equality semantics, its string
conversion, and its accessors, are deliberately designed for the
security-sensitive concept it represents, not merely present as a class with
the right name.

## 18. References

- Martin Fowler and Kent Beck, *Refactoring. Improving the Design of Existing
  Code*, Addison-Wesley, first edition 1999, second edition 2018, chapter
  "Bad Smells in Code," credited to Kent Beck. Bibliographic details
  cross-checked against the Wikipedia article "Code smell," which cites the
  same title, https://en.wikipedia.org/wiki/Code_smell, verified 2026-08-02.
- Martin Fowler, "Replace Primitive with Object," aliases Replace Data Value
  with Object and Replace Type Code with Class, Refactoring Catalog,
  https://refactoring.com/catalog/replacePrimitiveWithObject.html, verified
  2026-08-02.
- Martin Fowler, "ValueObject," bliki, https://martinfowler.com/bliki/ValueObject.html,
  verified 2026-08-02.
- Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
  Software*, Addison-Wesley, 2003.
- P. Leach, M. Mealling, R. Salz, "A Universally Unique IDentifier (UUID) URN
  Namespace," RFC 4122, Internet Engineering Task Force, 2005,
  https://www.rfc-editor.org/rfc/rfc4122, verified 2026-08-02.
- Java Community Process, "JSR 310. Date and Time API," specification led by
  Stephen Colebourne, Michael Nascimento Santos, and Roger Riggs,
  https://jcp.org/en/jsr/detail?id=310, verified 2026-08-02.
- Jon Skeet et al., NodaTime User Guide, https://nodatime.org/3.2.x/userguide/,
  verified 2026-08-02.
- Stripe, API Reference, "The Charge object," field amount,
  https://docs.stripe.com/api/charges/object, verified 2026-08-02.

## Code examples

### TypeScript

Demonstrates the branded-type variant from dimension 8. `UserId` and
`ProductId` are both structurally `string` at runtime, but TypeScript's
structural type system is defeated by an unexported brand symbol, so the two
are not interchangeable at compile time, and a validating constructor
function is the only way to produce one.

```typescript
declare const brand: unique symbol;
type Brand<T, B extends string> = T & { readonly [brand]: B };

type UserId = Brand<string, "UserId">;
type ProductId = Brand<string, "ProductId">;

function makeUserId(raw: string): UserId {
  if (!/^u_[a-z0-9]{8}$/.test(raw)) {
    throw new Error(`invalid UserId ${raw}`);
  }
  return raw as UserId;
}

function makeProductId(raw: string): ProductId {
  if (!/^p_[a-z0-9]{8}$/.test(raw)) {
    throw new Error(`invalid ProductId ${raw}`);
  }
  return raw as ProductId;
}

function placeOrder(userId: UserId, productId: ProductId): string {
  return `order placed for user ${userId} on product ${productId}`;
}

const uid = makeUserId("u_ab12cd34");
const pid = makeProductId("p_zz99yy88");
console.log(placeOrder(uid, pid));

// The following line is a COMPILE-TIME error, not a runtime bug,
// because ProductId and UserId are not assignable to one another
// even though both are branded strings.
//
// placeOrder(pid, uid);
```

### Python

Demonstrates the class-based value object variant, a `Percentage` type
enforcing the 0.0 to 1.0 invariant exactly once, in its constructor, with
value-based equality via a frozen dataclass.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Percentage:
    value: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.value <= 1.0):
            raise ValueError(
                f"Percentage must be between 0.0 and 1.0, got {self.value}"
            )

    def of(self, amount: float) -> float:
        return amount * self.value

    def as_display_string(self) -> str:
        return f"{self.value * 100:.1f}%"


def apply_discount(price: float, discount: Percentage) -> float:
    return price - discount.of(price)


discount = Percentage(0.15)
after = apply_discount(100, discount)
print(f"{discount.as_display_string()} off $100.00 is ${after:.2f}")

try:
    Percentage(1.5)
except ValueError as exc:
    print(f"rejected at construction, {exc}")
```

### Go

Demonstrates the newtype-adjacent variant available in a language without
generics-based branding tricks, a named type with a validating constructor
function, distinct from a bare `string` at the type-checker level for
function signatures, even though the compiler still permits an explicit
conversion.

```go
package main

import (
	"errors"
	"fmt"
	"regexp"
)

type EmailAddress string

var emailPattern = regexp.MustCompile(`^[^@\s]+@[^@\s]+\.[^@\s]+$`)

func NewEmailAddress(raw string) (EmailAddress, error) {
	if !emailPattern.MatchString(raw) {
		return "", fmt.Errorf("invalid email address %q", raw)
	}
	return EmailAddress(raw), nil
}

func (e EmailAddress) Domain() (string, error) {
	for i, r := range e {
		if r == '@' {
			return string(e[i+1:]), nil
		}
	}
	return "", errors.New("no @ found, invariant violated")
}

func sendWelcome(to EmailAddress) string {
	return fmt.Sprintf("welcome email queued for %s", to)
}

func main() {
	addr, err := NewEmailAddress("mirza@example.com")
	if err != nil {
		panic(err)
	}
	fmt.Println(sendWelcome(addr))

	domain, err := addr.Domain()
	if err != nil {
		panic(err)
	}
	fmt.Println("domain", domain)

	_, err = NewEmailAddress("not-an-email")
	fmt.Println("rejected", err)
}
```

A fourth language, Rust, is the most idiomatic host for this pattern via the
zero-cost newtype (`struct UserId(u64);` with `#[derive(PartialEq, Eq, Hash)]`)
but is omitted from the runnable examples above to keep the entry to three
verified, compiled or executed samples. The mechanism is directly analogous to
the Go example, with the added benefit that Rust's orphan and privacy rules
prevent an outside module from constructing an invalid instance at all once
the inner field is kept private to the defining module.
