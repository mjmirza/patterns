---
name: Value Object
slug: value-object
family: 06-enterprise-application-architecture
category: Base Pattern
aliases: [Value Type, Immutable Value, Value Data Type]
first_described: "Fowler 2002"
maturity: canonical
related: [money, embedded-value, data-transfer-object, identity-field, domain-model, layer-supertype]
incompatible_with: []
verified: 2026-08-02
---

# Value Object

## 1. Name, aliases, and lineage

The canonical name is Value Object. It is described in Martin Fowler, *Patterns of
Enterprise Application Architecture*, Addison-Wesley, 2002, chapter 18, Base
Patterns, section Value Object. Fowler defines it as a small, simple object,
such as money or a date range, whose equality is not based on identity
([Fowler, PoEAA online catalog, "Value Object"](https://martinfowler.com/eaaCatalog/valueObject.html),
verified 2026-08-02).

The name has a second, independent lineage that most catalogs collapse into the
same entry, and the collapse loses information. Eric Evans, *Domain-Driven
Design. Tackling Complexity in the Heart of Software*, Addison-Wesley, 2003,
chapter 5, "A Model Expressed in Software," section "Value Objects," coins the
same term the same year for a related but distinctly framed idea. Evans starts
from the domain-modeling question, does this object need a tracked identity,
and answers no for a Value Object, where Fowler starts from the equality-testing
question, does this object compare by reference or by content. The two framings
converge on the same implementation, an immutable object compared by its
attributes, but Evans adds an explicit design rule that PoEAA does not, that a
Value Object should be freely shared and replaced rather than modified in place,
because it carries no identity to preserve across a change.

Common aliases in day to day use. **Value Type**, the term preferred in .NET and
Kotlin communities where a language-level `struct` or `value class` already
supplies part of the mechanism. **Immutable Value**, used interchangeably in
functional-leaning codebases to foreground the immutability requirement rather
than the equality requirement. **Value Data Type**, occasionally used in older
CORBA and enterprise Java literature to distinguish it from an "entity bean."

A useful test, borrowed from both lineages at once. If two instances holding the
same data can be swapped for each other anywhere in the program with no
observable difference, it is a Value Object. If swapping them would lose
information, such as which row in a database the object represents, it is an
Entity, see the Identity Field pattern.

## 2. Problem and context

A domain concept, an amount of money, a date range, a phone number, a
geographic coordinate, a color, has more than one primitive field and a rule
about how those fields combine, but the code represents it as loose primitives
passed around individually, or as a mutable class with public setters and no
behavior of its own.

The situation reads like this in a codebase. A method signature carries three
separate parameters, an amount and a currency code as two loose values, or
a latitude and a longitude as two loose values, and every caller must remember to pass
them together, in the right order, and every caller that wants to validate them
duplicates the same range check. A currency mismatch between two amounts is
caught, if it is caught at all, by a runtime check written fresh at each call
site rather than once. Two dates that represent a range are stored as two
separate nullable fields on an entity, and the invariant that the start date
must precede the end date is enforced, inconsistently, wherever the entity is
constructed.

Wolfgang Keller and Ward Cunningham independently named this failure mode
Primitive Obsession, cataloged as a code smell in Martin Fowler, Kent Beck, John
Brant, William Opdyke, Don Roberts, *Refactoring. Improving the Design of
Existing Code*, 2nd edition, Addison-Wesley, 2018, chapter 3, "Code Smells,"
section "Primitive Obsession." The context that produces it is almost always the
same, a domain concept was born small, one field, and grew a second and third
field over time without anyone stopping to promote it to its own type.

The context that makes Value Object the right answer has three parts.

- The concept is defined entirely by its data. There is no meaningful answer to
  "which one is it" beyond "what values does it hold."
- The concept has at least one invariant or one piece of behavior that belongs
  with the data, a currency check, a range comparison, a formatting rule, so a
  bare tuple or record with no methods would still leave that logic scattered.
- Two instances holding equal data are genuinely interchangeable everywhere the
  concept is used, including as a dictionary key, a set member, and a field on
  another Value Object.

Outside that context, promoting a primitive to an object without either an
invariant or a second instance in practice is the over-engineering case
described in dimension 4.

## 3. Forces

- **Correctness by construction.** Favored. A Value Object with a validating
  constructor makes an invalid instance impossible to hold, rather than merely
  detectable later, which collapses a class of bugs into a single checked point.
- **Aliasing safety.** Favored, and this is the primary reason the pattern
  requires immutability rather than treating it as an optional nicety. Fowler's
  bliki entry on the pattern illustrates the failure directly, a shared mutable
  date object passed into two places, mutated through one reference, and the
  change silently appears through the other reference too
  ([Fowler, bliki, "ValueObject"](https://martinfowler.com/bliki/ValueObject.html),
  verified 2026-08-02). Immutability removes the failure by removing the
  mutation, not by removing the sharing.
- **Allocation and garbage-collection pressure.** Sacrificed. Every operation
  that would be a mutation on a mutable object becomes a new allocation on a
  Value Object, `original.plus(x)` allocates rather than `original.add(x)`
  mutating in place. In a managed runtime under a hot loop this is measurable,
  and it is the standard rebuttal raised against the pattern by teams optimizing
  for throughput.
- **Equality and hash consistency.** Favored when done correctly, a serious
  liability when done incorrectly. A Value Object's `equals` and `hashCode`, or
  the language equivalent, must agree with each other and must never change
  after construction, or the object corrupts any hash-based collection it sits
  in. Dimension 11 covers the concrete failure.
- **Persistence mapping cost.** Sacrificed in an object-relational system. A
  Value Object has no identity of its own, so a relational mapper cannot give it
  a row and a primary key the way it gives an Entity one. It must be flattened
  into columns on the owning Entity's table, which is the Embedded Value
  pattern, or serialized into a single column, which is the Serialized LOB
  pattern. Either mapping adds a translation layer the raw primitives did not
  need.
- **Cognitive load at the boundary.** Favored inside the domain, sacrificed at
  the boundary. Inside domain code a `Money` parameter is self-documenting and
  cannot be passed in the wrong currency by accident. At a serialization
  boundary, an HTTP request body or a database row, the Value Object must be
  parsed from and rendered back to primitives, and that parse step is exactly
  where the invariant checks that make the pattern valuable actually run, see
  dimension 7.
- **API surface size.** Sacrificed. Every domain concept promoted to a Value
  Object is one more type name, one more file, one more thing a new team member
  must learn before reading the domain. A codebase with forty single-field
  wrapper types and no behavior on any of them has paid this cost without buying
  any of the benefits, see dimension 4.

A pattern that gave up nothing would be a language feature, not a pattern. The
price here is paid in allocation, in persistence-mapping indirection, and in
type-surface area, in exchange for correctness that is checked once at
construction rather than everywhere the concept is used.

## 4. Applicability and non-applicability

Reach for Value Object when the following hold.

- The concept is fully described by its attribute values, with no meaningful
  separate identity, a monetary amount, a date range, a percentage, a physical
  measurement, a color, a geographic coordinate, an email address.
- The concept carries an invariant that is currently enforced inconsistently, or
  not at all, at more than one call site.
- The concept has behavior that naturally belongs with the data, comparing two
  date ranges for overlap, converting a temperature between units, formatting a
  phone number for display.
- Instances need to be freely shared, cached, or reused across the program
  without defensive copying, which immutability provides for free.
- The concept will appear as a field on more than one Entity, or as a
  dictionary or set key, where consistent value-based equality matters.

Do NOT reach for Value Object in these cases, and the reason matters more than
the rule.

- **There is exactly one field and no invariant.** A wrapper class around a
  single `string` with no validation and no behavior is a Value Object in name
  only. It is the primitive with extra allocation, and it should stay a
  primitive, or become a lightweight branded or newtype alias where the
  language supports one, see dimension 8, rather than a full class.
- **The concept genuinely needs a tracked identity across a mutation.** A bank
  account balance changes over time and the business still needs to say "this
  is the same account it was yesterday, with a different balance." That is an
  Entity with an Identity Field, not a Value Object. Modeling it as an immutable
  Value Object forces every balance change to look like replacing the whole
  account, which loses the "same account, new state" story the business
  actually tells.
- **The object is large and is copied wholesale on every field change.** A large
  aggregate with fifteen fields, where changing one field means constructing a
  new fifteen-field instance, pays an allocation and copy cost that scales
  badly. Either split the aggregate into smaller Value Objects so only the
  changed part is reallocated, or accept controlled mutability with a Builder
  for the assembly phase and freeze only the finished result.
- **The concept is a boundary payload with no domain invariant, only a shape.**
  A struct that exists purely to carry fields across a network call, with
  validation happening elsewhere, is a Data Transfer Object, not a Value Object,
  even though both are frequently immutable. Naming it a Value Object implies an
  invariant that is not actually enforced there. See dimension 13.
- **Uniqueness of a shared instance is being used to save memory rather than to
  express a domain rule.** Caching one canonical instance per distinct value,
  for example a shared `Currency.USD` singleton, is a legitimate optimization,
  but it is the Flyweight pattern applied to a Value Object, not the Value
  Object pattern itself. Conflating the two leads to code that relies on
  reference equality between Value Objects, which reintroduces the aliasing
  fragility the pattern exists to remove.
- **The language's ORM or serialization framework requires a no-argument
  constructor and public setters to function, and the team is not willing to
  configure around that.** Frameworks such as older versions of Hibernate or
  early JPA specifications historically required a default constructor,
  which is straightforward to add privately without opening the setters, but a
  team that reaches for public setters "because the framework needs it" has
  quietly defeated the immutability the pattern depends on.

## 5. Structure

Three participants, named by the role they play. A fourth appears only in an
object-relational system.

- **Value Object.** Holds one or more fields describing the concept. Exposes no
  setters. Exposes behavior relevant to the concept, comparison, arithmetic,
  formatting, conversion. Every operation that would look like a mutation
  returns a new Value Object instead of changing the receiver. Equality and hash
  code are computed from every field that participates in the concept's
  identity, and from nothing else.
- **Client.** Any code, an Entity, a service, another Value Object, that holds a
  reference to a Value Object as a field or passes one as a parameter. The
  client never needs to defensively copy the Value Object before storing it or
  after receiving it, because it cannot be mutated through any reference.
- **Factory or validating constructor.** The single point where raw input,
  typically primitives arriving from a form, a database row, or a network
  payload, is checked against the concept's invariant and either accepted as a
  new Value Object or rejected. This may be the constructor itself, when the
  language allows a constructor to throw, or a static factory method returning
  a result type, when the team prefers not to use exceptions for expected
  invalid input.
- **Owning Entity, present only under object-relational mapping.** The Entity
  that holds the Value Object as a field, and whose table row the Value
  Object's columns are inlined into, per the Embedded Value pattern, since the
  Value Object has no row or primary key of its own.

## 6. ASCII structure diagram

```
    +----------------------------------+
    |             Client                |
    |------------------------------------|
    | - holds reference to a Value Object|
    | - never mutates it, only replaces  |
    +----------------------------------+
                    |
                    | holds / passes
                    v
    +----------------------------------+
    |            Value Object            |
    |------------------------------------|
    | - final field. amount              |
    | - final field. currency            |
    |------------------------------------|
    | + plus(Money). Money   (returns new)|
    | + times(int). Money    (returns new)|
    | + equals(Object). boolean          |
    | + hashCode(). int                  |
    +----------------------------------+
              ^
              | constructed and validated by
              |
    +----------------------------------+
    |    Factory / validating ctor       |
    |------------------------------------|
    | + of(minorUnits, currency). Money  |
    |   throws on negative or malformed  |
    +----------------------------------+

    Under object-relational mapping only.

    +----------------------------------+          +--------------------+
    |          Owning Entity             | inlines |   Value Object     |
    |------------------------------------|-------->|  (no table, no PK) |
    | id (own primary key)               | columns | amount, currency   |
    | price_amount, price_currency       |         |                    |
    +----------------------------------+          +--------------------+
```

## 7. Dynamics

The defining runtime property is that no operation ever mutates a Value Object
in place. An operation that reads as a mutation, `raise(percent)`,
`plus(other)`, always returns a distinct new instance, and the original is
unaffected and can still be safely held by every other reference to it. This
is what removes the aliasing bug described in dimension 3.

```
Client            Money(1099, USD)        Money.of()          Money(2198, USD)
  |                       |                     |                     |
  |-- price = Money.of(1099, USD) -------------->|                     |
  |                       |<-- validates, allocates ------------------|
  |                       |                     |                     |
  |-- doubled = price.times(2) ----------------->|                     |
  |                       |-- reads own fields   |                     |
  |                       |-- calls Money.of(2198, USD) --------------->|
  |                       |                     |<-- validates, allocates
  |                       |                     |                     |
  |<-- returns doubled ---|---------------------|---------------------|
  |                       |                     |                     |
  |   price is unchanged. doubled is a new, distinct instance.        |
  |                       |                     |                     |
  |-- price.equals(Money.of(1099, USD)) -------->|                     |
  |                       |-- compares fields, not identity            |
  |<-- true --------------|                     |                     |
```

Two timing notes worth stating plainly. First, validation happens exactly once,
at construction, inside the factory or constructor. Every later use of the
object can trust the invariant without re-checking it, which is the entire
practical payoff of the pattern, parse the input once rather than validating it
again at every use, applied to a domain type rather than to a whole input
document. Second, when a Value Object arrives at a serialization boundary,
deserialization from JSON or from a database row must route through the same
validating constructor rather than through a framework mechanism that
populates fields by reflection and bypasses the constructor, since a
reflection-populated instance never had its invariant checked. This exact
failure is covered as a misuse in dimension 11.

## 8. Implementation variants

**Immutable final class with private fields and a static factory.** The
classical shape in Java before records, C# before record types, and any
language without a first-class immutable-record construct. Every field is
`final`, there is no setter, `equals` and `hashCode` are overridden together,
and construction goes through a static factory that validates and can return a
cached instance for common values.

**Language-native record type.** Java's `record`, available since Java 16 and
finalized in Java 17, and C#'s `record` or `readonly record struct`
generate the constructor, field accessors, `equals`, `hashCode`, and
`ToString` from a declared shape, removing most of the boilerplate the classical
shape required. The Microsoft documentation states plainly that a `record`
should be reached for "when you want immutability, especially for `record
class` types" and that two instances with the same values should be
considered equal, which is exactly the Value Object contract
([Microsoft Learn, "C# record types"](https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/types/records),
verified 2026-08-02). The tradeoff is that a generated record's equality is
by default structural over every declared property, so a Value Object with a
mutable reference field, an array or a mutable collection, silently breaks the
contract unless that field is excluded or wrapped, see dimension 11.

**Frozen dataclass or attrs class in Python.** `@dataclass(frozen=True)`
generates `__init__`, `__eq__`, and, when `eq=True` together with
`frozen=True`, a `__hash__` as well, and raises `FrozenInstanceError` on any
attempted attribute assignment after construction, per the Python standard
library documentation
([Python 3 documentation, `dataclasses`](https://docs.python.org/3/library/dataclasses.html),
verified 2026-08-02). This is the idiomatic Python shape. `typing.NamedTuple`
is a lighter alternative for a Value Object with no behavior beyond equality
and unpacking, at the cost of positional rather than named construction
discipline.

**readonly struct in C#, value type in Kotlin, or Copy struct in Rust.**
Languages that offer stack-allocated value types let the runtime, rather than
the programmer, guarantee copy-on-assignment semantics, which removes the
aliasing bug at the language level rather than at the discipline level. The
cost is that these types are copied by value on every assignment and every
function call, which is efficient for small Value Objects, two or three
machine words, and can become a measurable copy cost for larger ones, which
should stay reference-typed classes or records instead.

**Rust struct with `#[derive(Clone, Copy, PartialEq, Eq, Hash)]`.** Rust has no
inheritance and no implicit mutable aliasing of struct fields, so most of the
discipline the pattern requires in an object-oriented language is enforced by
the borrow checker instead. `Copy` is only derivable when every field is itself
`Copy`, so a Value Object holding a `String` or a `Vec` derives `Clone` but not
`Copy`, and the type system communicates the allocation cost of duplicating the
value directly in its trait bounds, which is a case where the language makes
the trade-off from dimension 3 visible in the type signature itself rather
than leaving it implicit.

**Self-validating constructor versus a `Result`-returning factory.** In
languages with exceptions, throwing from the constructor on an invalid input is
common and keeps construction a single expression. In languages or codebases
that treat exceptions as reserved for truly exceptional conditions, a static
factory returning a `Result<Money, ValidationError>` or an `Either` makes
invalid input an explicit branch the caller must handle, at the cost of an
extra unwrap step at every construction site.

**Small Value Object versus Large Value Object.** A small Value Object, two or
three primitive fields, is cheap to reallocate on every operation and is the
common case, Money, a coordinate pair, a date range. A large Value Object, an
address with eight fields or a full configuration bundle, pays a real
allocation cost on every "mutation," and teams sometimes soften this with a
Builder used only during assembly, freezing the result once construction
finishes, which keeps the finished object immutable while avoiding an
allocation per field during setup.

**Value Object interning, the Flyweight boundary.** A factory that caches and
returns a shared instance for frequently used values, `Currency.of("USD")`
always returning the same object, is a legitimate composition with Flyweight,
but the composed type must still compare by value everywhere it is used, never
by identity, or callers that receive a non-cached instance of an equal value
will see a spurious inequality. See dimension 13 for the boundary between the
two patterns.

## 9. Known production uses

**Java's `java.time` package, `LocalDate`, `LocalDateTime`, `Duration`, and
related types, JSR 310.** Oracle's Java SE 21 API documentation for
`LocalDate` states in its Implementation Requirements section that "this class
is immutable and thread-safe," and explicitly documents it as a value-based
class, instructing programmers to "treat instances that are equal as
interchangeable and should not use instances for synchronization," using
`equals` for comparison rather than reference identity
([Oracle, Java SE 21 API Specification, `java.time.LocalDate`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/time/LocalDate.html),
verified 2026-08-02). This is the language standard library's own definition
of value-based class semantics, and it matches the Value Object contract field
for field, immutability, content-based equality, no synchronization on
instances.

**Stripe's API representation of monetary amounts.** Stripe's currency
documentation states that "all API requests expect amounts to be provided in a
currency's smallest unit," an integer, for example `1099` to charge 10.99 USD,
rather than a floating-point decimal amount
([Stripe Docs, "Supported currencies," amount specification section](https://docs.stripe.com/currencies),
verified 2026-08-02). This is the Money variant of Value Object at API-contract
scale, an amount is only meaningful paired with a currency and represented in a
unit that avoids binary floating-point rounding error, and Stripe encodes that
invariant directly into every endpoint that accepts a monetary amount rather
than leaving each integration to reinvent it.

**Joda-Money, `Money` and `BigMoney`.** The project's own documentation
describes itself as providing "simple value types, representing currency and
money," naming `Money` as "a fixed precision monetary value type" and
`BigMoney` as "a variable precision monetary type"
([Joda-Money project page](https://www.joda.org/joda-money/), verified
2026-08-02). Joda-Money predates and directly informed the design later
standardized, in a different but related shape, in JSR 354, the Java Money and
Currency API.

**.NET record types used for domain modeling.** Microsoft's own C# language
documentation frames the entire `record` feature around the Value Object use
case, stating that a `record` should be used when "the type's primary role is
storing data" and "two instances with the same values should be equal," and
contrasts this directly with Entity Framework Core entities, which the same
page warns should avoid records "because Entity Framework Core... depends on
reference equality to track entities"
([Microsoft Learn, "C# record types," "When to use records" section](https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/types/records),
verified 2026-08-02). The documentation is drawing the same Value
Object versus Entity boundary this pattern entry draws in dimension 4,
independently, at the language-feature level.

## 10. Consequences

Positive.

- An invalid instance cannot exist once construction succeeds, which collapses
  validation from "checked at every call site, inconsistently" to "checked once,
  reliably."
- Aliasing bugs from shared mutable state are structurally impossible, because
  there is no mutation to alias into.
- Value Objects are safe to use as dictionary and set keys and as cache keys
  once equality and hash code are implemented consistently, since their state,
  and therefore their hash, never changes after construction.
- Thread safety follows directly from immutability, a Value Object can be
  freely shared between threads with no locking, no defensive copying, and no
  synchronization.
- Domain concepts that were previously loose primitive parameters become
  self-documenting types, which improves both compile-time checking, a
  currency-typed parameter cannot silently accept an amount, and readability at
  call sites.

Negative.

- Every state change becomes an allocation, which is measurable in an
  allocation-sensitive hot path and is the most common reason teams reach for a
  mutable Builder or a controlled-mutability escape hatch during assembly.
- The object has no identity of its own, which forces an object-relational
  mapper to flatten it into the owning Entity's row, adding the Embedded Value
  or Serialized LOB translation layer instead of a simple table-per-type
  mapping.
- A large Value Object with many fields pays a copy cost on every partial
  change, since there is no way to change one field without reconstructing the
  whole object.
- The pattern adds one more named type per domain concept, and applied to every
  primitive without discretion it produces a large surface of thin wrapper
  classes that add ceremony without adding a checked invariant, the
  over-engineering case in dimension 4.
- Deep immutability is only as strong as the language enforces it. A Value
  Object that holds a reference to a mutable collection or a mutable object as
  one of its fields is not actually immutable, only shallowly so, and this is
  one of the most common real-world defects, covered in dimension 11.

## 11. Failure modes and misuse

**Shallow immutability through a mutable field.** Symptom. Two Value Objects
that were `equal` when logging started later compare unequal, or a cached
Value Object's behavior silently changes over time with no code path that
constructed a new instance. Cause. The Value Object holds a `final` reference
to a mutable collection, array, or mutable object, and a caller mutates the
contents through that reference rather than through the Value Object's own API,
which has no setter but never copied the reference on the way in. Fix. Defensive
copy any mutable input in the constructor, and expose collection fields only
through an unmodifiable or read-only view, never the backing collection
itself.

**BigDecimal's `equals` disagreeing with numeric equality.** Symptom. A Value
Object wrapping `java.math.BigDecimal` treats `10.0` and `10.00` as unequal
even though they represent the same numeric amount, breaking a set-based
deduplication or a test assertion that expected numeric equality. Cause. The
official Oracle documentation states this directly, "the `equals` method
requires both the numerical value and representation to be the same for
equality to hold," while the class's natural ordering via `compareTo`
considers members of the same numeric cohort equal regardless of scale, and
the documentation explicitly warns that "BigDecimal's natural ordering is
inconsistent with equals"
([Oracle, Java SE 21 API Specification, `java.math.BigDecimal`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/math/BigDecimal.html),
verified 2026-08-02). Fix. Normalize scale in the Value Object's constructor
before storing the amount, so the invariant "scale is always fixed at two
decimal places for this currency" is established once rather than trusted to
every comparison site, or implement `equals` in terms of `compareTo` rather
than delegating to `BigDecimal.equals` directly, while remembering that choice
must then also drive `hashCode`.

**Deserialization bypassing the validating constructor.** Symptom. A Value
Object that enforces "amount must be non-negative" in its constructor is found
holding a negative amount in production, despite every code path the team can
find calling the constructor correctly. Cause. A JSON or database deserializer
using reflection or a no-argument constructor plus field injection populates
the object's fields directly, without ever calling the validating constructor
or factory. Fix. Configure the serialization framework to route through the
canonical constructor, most JSON libraries support this via a
constructor-binding or creator annotation, and add a round-trip test that
serializes an invalid payload and asserts deserialization throws rather than
silently succeeding.

**Reflection-based `equals` and `hashCode` drifting from the intended field
set.** Symptom. Adding a new derived or cached field to a Value Object, for
example a lazily computed formatted string, silently changes what counts as
equal, and two objects that a domain expert would call the same value start
comparing unequal. Cause. `equals` and `hashCode` were generated once via
reflection over all fields rather than an explicit list of the fields that
actually define the concept's identity. Fix. Write or generate `equals` and
`hashCode` against an explicit, named list of identity-defining fields, and add
a regression test that adds a derived field and asserts equality is unaffected.

**Treating a shared, interned instance as though identity mattered.**
Symptom. A conditional written as `if (currencyA == currencyB)` works in
testing, where all instances happen to come from the same cache, and fails in
production once a value arrives from deserialization as a fresh, uncached
instance. Cause. Code relies on reference equality for a type that is a Value
Object, conflating the Flyweight caching optimization described in dimension 8
with the pattern's actual equality contract. Fix. Always compare Value Objects
with the equality operator or method the language provides for content
comparison, `equals`, `==` on a `record struct`, `__eq__`, never with reference
identity, and treat any instance-caching as a private implementation detail the
caller must not depend on.

**Value Object explosion with no invariant behind any of them.** Symptom. A
code review finds forty single-field classes, `UserId`, `ProductName`,
`Quantity`, each holding one primitive and a constructor with no validation,
and every one of them adds a `.value()` unwrap call at every boundary with no
corresponding safety gained. Cause. The team adopted "wrap every primitive" as
a blanket rule rather than reaching for the pattern only where an invariant or
shared behavior justifies the type. Fix. Audit each wrapper for an actual
enforced invariant or actual shared behavior. Where neither exists, either add
one, a length check, a format check, or fold the wrapper back into a plain
primitive or a lightweight branded type where the language supports one, see
dimension 8.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Value Object | Entity (Identity Field) | Raw primitives (Primitive Obsession) | Mutable wrapper class | Data Transfer Object |
|---|---|---|---|---|---|
| Equality semantics | By value, every field | By identity, one key field | By value, but scattered checks | By reference unless overridden, and unsafe to override if mutable | Usually by value, but the shape carries no domain invariant |
| Aliasing safety | Safe, immutable, no mutation to alias | Not applicable, identity is the point | No wrapper, so nothing to alias, but no invariant either | Unsafe, shared mutable state is exactly the aliasing hazard | Safe when treated as immutable, but that is convention, not enforced |
| Invariant enforcement | Once, at construction | Enforced per field, spread across the entity lifecycle | Duplicated at every call site or absent | Enforced only if every setter re-validates, easy to forget | Typically none, validation lives elsewhere |
| Allocation cost per change | One allocation per operation | One mutation, no allocation | None, primitives are cheap | None, in-place mutation | Same as Value Object when immutable |
| Persistence mapping | Needs Embedded Value or Serialized LOB | Native, gets its own table and primary key | Native, maps directly to columns | Native, but mutability risks stale cached rows | Not persisted, exists only at the boundary |
| Safe as a hash key or set member | Yes, once equals and hashCode are correct | Only by identity key, not by full state | Yes for a single primitive, no for a tuple without a wrapper | No, mutation after insertion corrupts the container | Rarely used this way |
| Thread safety | Free, by construction | Requires external synchronization on mutation | Free for a single primitive, unsynchronized combination is not | Requires external synchronization | Free when immutable |
| Cognitive cost of the type surface | One more named type per concept | Expected, entities are already named types | Lowest, no new type | Medium, looks safe, is not | Medium, one more shape per boundary |

Reading of the table. Value Object wins wherever an invariant needs to be
enforced once and the concept has no identity worth tracking. Entity wins
wherever "the same thing, changed" is a sentence the business actually says.
Raw primitives win only for genuinely simple, unconstrained data with no shared
behavior. A mutable wrapper class rarely wins anything, it inherits the type
overhead of a Value Object without any of its safety guarantees. A Data
Transfer Object overlaps with Value Object in shape but not in intent, see
dimension 13 for the distinction.

## 13. Related and incompatible patterns

- **Money.** The single most common specialization of Value Object, and common
  enough in enterprise systems to warrant its own catalog entry. Money adds the
  currency-pairing invariant and the minor-unit representation on top of the
  general pattern. See the Money entry in this family.
- **Embedded Value.** The persistence-mapping answer to the structural problem
  in dimension 5 and dimension 10, a Value Object has no table of its own, so
  Embedded Value maps its fields as columns on the owning Entity's table. Every
  object-relationally mapped Value Object needs either this pattern or
  Serialized LOB.
- **Serialized LOB.** The alternative persistence mapping for a Value Object
  whose shape does not flatten cleanly into columns, or that needs to preserve
  a rich internal structure, a tree or a graph, by serializing the whole object
  into a single large text or binary column instead.
- **Identity Field, and Entity generally.** The direct conceptual opposite. An
  Entity is defined by its identity field and is expected to change over its
  lifetime while remaining "the same" thing. Modeling something with a tracked
  identity as a Value Object loses that "same thing, different state" story,
  and modeling something with no meaningful identity as an Entity adds an
  unnecessary primary key and an unnecessary identity map entry.
- **Data Transfer Object.** Frequently confused with Value Object because both
  are commonly immutable and both are commonly small. The difference is intent
  rather than shape. A Data Transfer Object exists to reduce the number of
  remote calls across a process or network boundary and carries no domain
  invariant of its own, per Fowler's own framing of the DTO pattern. A Value
  Object exists to enforce a domain invariant and to provide domain behavior. A
  Value Object is frequently mapped to and from a Data Transfer Object at a
  serialization boundary, with the DTO's fields validated on the way in through
  the Value Object's constructor.
- **Flyweight.** Composes cleanly at the implementation level, described in
  dimension 8, a factory can intern and share instances of a Value Object for
  memory efficiency. It becomes an incompatibility the moment calling code
  starts relying on the shared instance's reference identity rather than its
  value equality, since a fresh, non-interned instance of an equal value must
  still compare equal.
- **Domain Model.** A Value Object is one of the building blocks a rich Domain
  Model is assembled from, alongside Entities. Evans' Domain-Driven Design
  treats Value Objects as a first-class citizen of the domain layer precisely
  because so much of a domain's behavior, comparison, arithmetic, formatting,
  belongs on the data rather than on a service that operates over loose
  primitives.
- **Record types as a language feature, not a pattern.** Java `record` and C#
  `record` are a mechanism the pattern can be built with, described in
  dimension 8, not a guarantee of the pattern on their own. A record with a
  mutable field, a `List` rather than an immutable sequence, is a language
  record and not a genuine Value Object, since the deep-immutability
  requirement is not automatically satisfied.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. The named refactoring
is Replace Data Value with Object, cataloged in Fowler, Beck, Brant, Opdyke,
Roberts, *Refactoring*, 2nd edition, Addison-Wesley, 2018, and in its online
form at refactoring.com as the paired, inverse refactorings **Change Value to
Reference** and **Change Reference to Value**
([refactoring.com catalog, "Change Value to Reference"](https://refactoring.com/catalog/changeValueToReference.html),
verified 2026-08-02). Ordered steps for introducing Value Object.

1. Find the group of primitive fields or parameters that always travel
   together, a currency-and-amount pair, a start-and-end date pair. Confirm
   they represent one concept, not two coincidentally adjacent fields.
2. Create the new class with those fields as `final` or `readonly`, a
   constructor that takes them all, and no setters yet. Do not move any
   behavior into it in this step, only the data.
3. Replace every constructor call and field access site with the new class,
   one call site at a time, running the tests after each. Getters on the new
   class simply return the stored fields for now.
4. Once every call site uses the class, move the invariant checks that were
   duplicated across the old call sites into the constructor, deleting the
   duplicated checks as they are subsumed. This is the step where the pattern
   starts paying for itself, since an invalid instance can no longer be
   constructed anywhere.
5. Move behavior that operated on the loose primitives, a comparison, a sum, a
   formatter, onto the new class as methods, following Extract Method and Move
   Method from the same refactoring catalog, and delete the free-standing
   versions.
6. Override `equals` and `hashCode`, or the language equivalent, over the
   explicit set of fields that define the concept, per the fix in dimension 11.
   Add the type-assertion or equality test from dimension 15 in the same step.
7. Only after steps 1 through 6 are stable, decide whether the class needs
   object-relational persistence, and if so introduce Embedded Value or
   Serialized LOB as a separate, focused change.

Removing the pattern when it stops earning its place. Signals that it should go
include a Value Object with a single field and no invariant, per the
over-engineering case in dimension 4, or a Value Object whose immutable
contract keeps getting broken by callers reaching for reflection or a
serialization library that bypasses the constructor.

1. Confirm every current use of the Value Object's methods, not only its
   fields. If real behavior lives on the class, this removal is premature,
   fold that behavior into a free function or a domain service instead of
   deleting it along with the type.
2. Inline the constructor call at each use site, replacing
   `new Money(amount, currency)` with the two loose primitives it wrapped, one
   site at a time, per the inverse Change Value to Reference or the general
   Inline Class refactoring.
3. Reintroduce, explicitly, whichever invariant checks the class used to
   centralize, at the smallest number of call sites that actually need them,
   rather than silently dropping the check.
4. Delete the now-unused class and its test file once no reference remains.

## 15. Testing and verification

Easier because of the pattern.

- The invariant is testable in one place, the constructor or factory, rather
  than needing a test at every call site that used to duplicate the check.
- Value equality lets tests write natural assertions,
  `assertEquals(Money.of(1099, "USD"), result)`, instead of asserting on
  individual fields, which keeps tests readable and keeps them failing with a
  clear diff when a field is wrong.
- Immutability removes an entire class of test flakiness caused by shared
  fixture state being mutated by one test and observed, unexpectedly, by
  another test that reused the same fixture instance.

Harder because of the pattern.

- A team that skips the equality-and-hash test entirely can ship a Value
  Object whose `equals` silently diverges from `hashCode`, per dimension 11,
  and standard unit tests that only assert `equals` will not catch it, since
  the corruption only shows up once the object is placed in a hash-based
  collection.
- Serialization round trips need their own dedicated tests, since the failure
  mode in dimension 11, deserialization bypassing the validating constructor,
  is invisible to a test that only constructs the object directly in code and
  never exercises the framework's deserialization path.

Techniques that apply.

- **Equals-hashCode contract test, run once and reused across every Value
  Object in the codebase.** Assert reflexivity, symmetry, transitivity, and
  that `hashCode` is identical for two objects that are `equals`, and that
  `hashCode` is stable across repeated calls on the same instance. Most
  languages' test ecosystems have a ready-made verifier for exactly this
  contract, and reaching for it once per Value Object is far cheaper than
  hand-writing the four properties every time.
- **Property-based test on the invariant.** Generate a wide range of raw
  inputs, including boundary and malformed values, and assert the constructor
  accepts every value the invariant permits and rejects every value it does
  not, rather than hand-picking a handful of examples that may miss an edge
  case.
- **Mutation test on the arithmetic or comparison methods.** Since the whole
  point of the pattern is that state changes are expressed as new-instance
  returns, a mutation test that flips an operator inside `plus` or `times`
  should be killed by an assertion on the returned value, confirming the test
  suite actually exercises the behavior rather than only the constructor.
- **Deserialization round-trip test.** Serialize an invalid payload through
  the actual JSON or database mapping the production code path uses, not a
  hand-constructed object, and assert deserialization either rejects it or
  routes through the same validating constructor as direct construction does.
- **Immutability audit test.** For a Value Object holding a collection or
  array field, assert that mutating the collection instance passed into the
  constructor, or mutating a collection instance returned from a getter, has
  no effect on the Value Object's own subsequent behavior, which directly
  targets the shallow-immutability failure in dimension 11.

## 16. Observability signals

The pattern itself produces no runtime behavior worth alerting on directly,
since a correctly implemented Value Object simply does not fail once
construction succeeds. The signals worth watching cluster around construction
and around the boundaries where raw data enters the domain.

What to record.

- A counter of construction failures, labelled by Value Object type and by
  the specific invariant that was violated, at whichever boundary raw input
  first becomes a Value Object, an HTTP handler, a message consumer, a
  database-row mapper. This is the single most useful signal, because a
  climbing rejection rate on one field pinpoints a malformed upstream data
  source before it reaches the domain at all.
- For a Money-shaped Value Object specifically, a counter of currency-mismatch
  errors from arithmetic operations, labelled by the pair of currencies
  involved, since a persistent mismatch on one specific pair usually points at
  a misconfigured integration rather than a one-off user error.
- A gauge or histogram of construction rate per Value Object type in a
  high-throughput system, since the allocation cost from dimension 3 becomes
  visible as garbage-collection pause frequency or pressure once a Value
  Object is constructed at high volume inside a hot path.

A healthy instance on a dashboard. Construction failures sit near zero and move
only when an upstream data source changes shape, with the change explained by a
deployment or an external integration update. Currency-mismatch errors, where
applicable, are effectively zero in a well-integrated system, since they
usually indicate a configuration bug rather than expected user behavior.

A failing instance. Construction failures for one field climb steadily with no
matching deployment, which usually means an upstream system started sending a
new shape or a new range of values without a corresponding contract change on
this side. A currency-mismatch counter that is non-zero and stable, rather than
a rare spike, points at a systemic integration bug, for example a currency
default that was never wired through end to end. A garbage-collection pause
histogram degrading in step with the construction-rate gauge for one specific
Value Object type localizes the allocation-pressure cost from dimension 3 to a
single concept, which is far easier to act on than a general "GC pauses
increased" alert.

## 17. Security and privacy implications

The pattern is largely a safety mechanism rather than a source of new risk, and
overstating its security relevance would be inventing a concern where the
honest answer is that it helps, modestly, in a narrow way. Three genuine
implications are worth naming.

**Input validation moved to a single, auditable point.** Because every
construction of the Value Object routes through the same constructor or
factory, per dimension 5 and dimension 7, that single point becomes the natural
place to enforce not only domain correctness but also injection-relevant
constraints, length limits, character-set restrictions, format checks, for any
Value Object whose data eventually reaches a query, a shell command, or a
rendered page. This is a genuine security benefit compared to primitive
parameters validated inconsistently at each call site, but it holds only when
the team treats the constructor as the sole entry point, per the
deserialization-bypass failure in dimension 11. A framework that populates
fields by reflection and skips the constructor also skips whatever security
checks were placed there.

**Immutability as a defense against time-of-check-to-time-of-use bugs.** A
mutable object that is validated once and then mutated by another thread or
another code path before it is used can be exploited as a classic
check-then-use race. Since a Value Object cannot be mutated after
construction, whatever was true of it at validation time remains true for its
entire lifetime, which removes this specific race condition for any data
carried in a Value Object, at the cost of nothing beyond the allocation
overhead already discussed.

**Sensitive data retained across a longer lifetime than expected.** A Value
Object caching or interning strategy, per the Flyweight composition in
dimension 8, can extend the lifetime of a value well beyond the scope that
constructed it, which matters when the value is sensitive, a tokenized
identifier, a partial payment card number, a personal address. A shared,
process-lifetime cache of such values increases the memory footprint that
holds sensitive data and complicates a clean, timely erase from memory on
logout or session end. Where a Value Object wraps genuinely sensitive data,
avoid interning it, and consider whether the language's immutability
guarantee, which typically implies the underlying memory is never explicitly
zeroed on garbage collection, is acceptable for that data's sensitivity level,
or whether a different, explicitly-zeroable representation is required
instead.

## 18. References

1. Martin Fowler. *Patterns of Enterprise Application Architecture*.
   Addison-Wesley, 2002. ISBN 0-321-12742-0. Chapter 18, Base Patterns, section
   Value Object. Source of the canonical definition and the pattern's chapter
   placement.
2. Martin Fowler. Online catalog entry, "Value Object."
   https://martinfowler.com/eaaCatalog/valueObject.html
   Verified 2026-08-02. Source for the definition quote and the money and date
   range examples.
3. Martin Fowler. Bliki entry, "ValueObject."
   https://martinfowler.com/bliki/ValueObject.html
   Verified 2026-08-02. Source for the aliasing-bug rationale for immutability
   and the reference-versus-value-object framing used in dimension 3 and
   dimension 13.
4. Eric Evans. *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*. Addison-Wesley, 2003. ISBN 0-321-12521-5. Chapter 5, "A Model
   Expressed in Software," section "Value Objects." Source for the
   independent, identity-first framing of the pattern described in dimension
   1.
5. Martin Fowler, Kent Beck, John Brant, William Opdyke, Don Roberts.
   *Refactoring. Improving the Design of Existing Code*, 2nd edition.
   Addison-Wesley, 2018. ISBN 978-0-13-475759-9. Chapter 3, "Code Smells,"
   section "Primitive Obsession." Source for the problem-context framing in
   dimension 2.
6. refactoring.com catalog. "Change Value to Reference."
   https://refactoring.com/catalog/changeValueToReference.html
   Verified 2026-08-02. Source for the named, paired refactoring used in
   dimension 14.
7. Oracle. *Java SE 21 API Specification*, `java.time.LocalDate`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/time/LocalDate.html
   Verified 2026-08-02. Source for the value-based class production use in
   dimension 9.
8. Oracle. *Java SE 21 API Specification*, `java.math.BigDecimal`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/math/BigDecimal.html
   Verified 2026-08-02. Source for the equals-versus-compareTo scale failure in
   dimension 11.
9. Microsoft. *C# record types*.
   https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/types/records
   Verified 2026-08-02. Source for the record-type implementation variant in
   dimension 8 and the production use in dimension 9.
10. Python Software Foundation. *Python 3 documentation*, `dataclasses`.
    https://docs.python.org/3/library/dataclasses.html
    Verified 2026-08-02. Source for the frozen dataclass semantics in
    dimension 8, including the `eq` and `frozen` interaction governing
    `__hash__` generation.
11. Stripe. *Stripe Docs*, "Supported currencies."
    https://docs.stripe.com/currencies
    Verified 2026-08-02. Source for the smallest-currency-unit representation
    used as a production use in dimension 9.
12. Joda-Money project page.
    https://www.joda.org/joda-money/
    Verified 2026-08-02. Source for the `Money` and `BigMoney` production use
    in dimension 9.

## Code examples

Three languages where the pattern is genuinely idiomatic in different ways,
each compiled and run against the same Money-shaped Value Object holding a
minor-unit integer amount and a currency code, per the Stripe convention from
dimension 9. TypeScript shows a hand-written immutable class with `Object.freeze`
and a `bigint` amount. Python shows the standard-library `frozen=True`
dataclass form, including the hash-consistency check that a set built from two
equal instances collapses to one member. Rust shows the language's own
value-semantics mechanism, `derive(Clone, Copy, PartialEq, Eq, Hash)`, which
enforces immutability and value equality at the compiler level rather than
through discipline. Java is omitted, this machine has no working Java runtime
to compile or run against, so it is not shown rather than presented as if it
had been verified. Go is omitted for a related reason, Go has no operator
overloading and no generated structural equality beyond `==` on comparable
struct fields, so a Go Value Object degenerates to a plain comparable struct
with free functions for its behavior, a variant already covered conceptually
in dimension 8 rather than needing separate code.

### TypeScript

```typescript
type CurrencyCode = "USD" | "EUR" | "JPY";

class Money {
  private constructor(
    private readonly minorUnits: bigint,
    private readonly currency: CurrencyCode
  ) {
    if (minorUnits < 0n) {
      throw new RangeError("Money cannot be negative in this ledger");
    }
    Object.freeze(this);
  }

  static of(minorUnits: bigint, currency: CurrencyCode): Money {
    return new Money(minorUnits, currency);
  }

  plus(other: Money): Money {
    this.assertSameCurrency(other);
    return new Money(this.minorUnits + other.minorUnits, this.currency);
  }

  times(factor: bigint): Money {
    return new Money(this.minorUnits * factor, this.currency);
  }

  equals(other: Money): boolean {
    return this.minorUnits === other.minorUnits && this.currency === other.currency;
  }

  private assertSameCurrency(other: Money): void {
    if (this.currency !== other.currency) {
      throw new Error(`cannot combine ${this.currency} with ${other.currency}`);
    }
  }

  toString(): string {
    return `${this.minorUnits} ${this.currency}`;
  }
}

const price = Money.of(1099n, "USD");
const doubled = price.times(2n);
const original = price;

console.log(price.toString());
console.log(doubled.toString());
console.log(price.equals(original));
console.log(price.equals(Money.of(1099n, "USD")));

try {
  price.plus(Money.of(500n, "EUR"));
} catch (err) {
  console.log((err as Error).message);
}
```

Compiled with `tsc --strict --target es2020` and run under Node. Output
confirms `price` is unaffected by `times`, that two independently constructed
instances holding the same data compare equal, and that a currency mismatch is
rejected rather than silently combined.

### Python

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    minor_units: int
    currency: str

    def __post_init__(self) -> None:
        if self.minor_units < 0:
            raise ValueError("Money cannot be negative in this ledger")

    def plus(self, other: "Money") -> "Money":
        self._assert_same_currency(other)
        return Money(self.minor_units + other.minor_units, self.currency)

    def times(self, factor: int) -> "Money":
        return Money(self.minor_units * factor, self.currency)

    def _assert_same_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise ValueError(f"cannot combine {self.currency} with {other.currency}")


if __name__ == "__main__":
    price = Money(1099, "USD")
    doubled = price.times(2)

    print(price == Money(1099, "USD"))
    print(len({price, Money(1099, "USD")}))

    try:
        price.minor_units = 500  # type: ignore[misc]
    except Exception as exc:
        print(type(exc).__name__, exc)
```

Run directly under CPython 3.14. The output confirms `frozen=True` both blocks
field assignment, raising `FrozenInstanceError`, and generates a `__hash__`
consistent with `__eq__`, so a `set` built from two equal instances holds only
one member, demonstrating the safe-as-a-hash-key property from dimension 10.

### Rust

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
enum Currency {
    Usd,
    Eur,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
struct Money {
    minor_units: i64,
    currency: Currency,
}

impl Money {
    fn new(minor_units: i64, currency: Currency) -> Result<Money, String> {
        if minor_units < 0 {
            return Err("Money cannot be negative in this ledger".to_string());
        }
        Ok(Money { minor_units, currency })
    }

    fn plus(self, other: Money) -> Result<Money, String> {
        if self.currency != other.currency {
            return Err(format!("cannot combine {:?} with {:?}", self.currency, other.currency));
        }
        Ok(Money { minor_units: self.minor_units + other.minor_units, currency: self.currency })
    }

    fn times(self, factor: i64) -> Money {
        Money { minor_units: self.minor_units * factor, currency: self.currency }
    }
}

fn main() {
    let price = Money::new(1099, Currency::Usd).unwrap();
    let doubled = price.times(2);

    println!("{}", price == Money::new(1099, Currency::Usd).unwrap());
    match price.plus(Money::new(500, Currency::Eur).unwrap()) {
        Ok(m) => println!("{:?}", m),
        Err(e) => println!("{}", e),
    }
    println!("{:?} {:?}", price, doubled);
}
```

Compiled with `rustc -O` and run directly. `derive(Copy)` is only legal here
because every field is itself `Copy`, so the compiler enforces value-copy
semantics rather than shared mutable references at the type level, the
strongest form of the immutability guarantee among the three languages shown.
