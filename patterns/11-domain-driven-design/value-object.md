---
name: Value Object
slug: value-object
family: 11-domain-driven-design
category: Domain-Driven Design
aliases: [Value Type, Immutable Value, Whole Value]
first_described: "Fowler and Evans, 2002 to 2003"
maturity: canonical
related: [entity, aggregate, factory, flyweight, money-pattern, null-object]
incompatible_with: []
verified: 2026-08-02
---

# Value Object

## 1. Name, aliases, and lineage

The canonical name is Value Object. It is described formally in Eric Evans,
*Domain-Driven Design. Tackling Complexity in the Heart of Software*,
Addison-Wesley, 2003, chapter 5, in the section titled "Value Objects". Evans
frames the whole chapter around a single question that every element of a model
must answer, does this thing need a persistent identity that tracks its history,
or does it only matter for what it currently equals. An object that answers no
to identity is a Value Object.

The lineage is not a single point of origin. Martin Fowler had already
described the same shape a year earlier under the name **Money pattern**, in
*Patterns of Enterprise Application Architecture*, Addison-Wesley, 2002, in the
Base Patterns chapter, well before Evans published DDD. Fowler's own bliki entry
on the term states the core idea in his own words, "objects that are equal due
to the value of their properties" rather than by an identity or a memory
address, and adds the rule that follows from it, "value objects should be
immutable" ([Martin Fowler, ValueObject, martinfowler.com](https://martinfowler.com/bliki/ValueObject.html),
verified 2026-08-02). Fowler credits the general idea to long-standing Smalltalk
community practice that predates both books, where the distinction between an
object identified by its memory slot and an object identified by its contents
was already a working convention. Evans is the author who put the name Value
Object at the center of a whole modeling method and made the decision explicit
and mandatory for every element of a domain model, which is why the pattern is
filed under Domain-Driven Design rather than under Fowler's enterprise
architecture catalog, even though Fowler wrote about the same shape first.

The alias **Value Type** is the term of art in language design and in .NET and
Swift documentation, where it names a first-class category of type (structs)
distinct from reference types, built to carry exactly this semantics at the
language level rather than by convention. The alias **Whole Value** appears in
older literature, notably Ward Cunningham's writing on replacing a cluster of
primitive parameters with one object that represents the whole concept, and it
is the historical ancestor of what later DDD writing folds into Value Object.
**Immutable Value** is used loosely in day to day engineering speech to mean the
same thing, though immutability is a consequence Evans derives from the
identity question rather than the defining property itself, a distinction this
entry returns to in dimension 3.

## 2. Problem and context

A domain model accumulates concepts that are not things, they are
measurements, descriptions, or quantities. A price. A date range. A postal
address. A color. A geographic coordinate. A percentage. None of these has a
lifecycle of its own, none of them is ever tracked across changes as "the same
one, now updated", and asking "is this the same address as that one" only ever
makes sense as "do they describe the same location", never as "are they the
same row in the database with a history of edits".

The problem surfaces in a specific and recognizable way. A codebase represents
a price as a plain number, a currency as a separate string, and passes the pair
around as two parameters everywhere the concept of a price is used. Comparison
and arithmetic scatter across the codebase, because there is no single place
that owns the rule that adding two amounts in different currencies is
meaningless. A second symptom appears when a naive attempt to fix this reaches
for an ordinary mutable class instead. Two `Address` objects that describe the
identical street, city, and postal code compare unequal because the language's
default equality checks object identity, not content, and a caller who mutates
one shared `Address` instance silently corrupts every other place that
instance was handed to, because nothing in the design signaled that sharing
was unsafe.

Value Object exists to give this class of concept a home. It answers the
identity question from Evans with a firm no, states that content is the only
thing that matters, and derives the rest of the pattern (immutability, value
equality, no identity field, freely shareable and freely replaceable) from that
one answer. The context in which it applies is any domain concept whose two
instances with the same attributes are, for every purpose the domain cares
about, interchangeable. It does not apply when the domain cares whether this is
the SAME instance as before, even after every attribute has changed, which is
the defining context of the sibling pattern, Entity.

## 3. Forces

Most of the reasoning in this dimension is engineering judgement about which
force dominates in a given system, stated openly as judgement rather than as a
sourced fact.

Identity semantics versus equality semantics is the force the pattern is
built to resolve, and it is the one force Evans treats as non-negotiable.
Decide identity first, everything else follows.

Immutability versus allocation cost is the sharpest practical trade-off. An
immutable Value Object cannot be mutated in place, so every change to a price,
a date range, or an address creates a new instance. In a language with cheap
stack-allocated value types (Swift structs, Go structs, C# `record struct`),
this cost is close to zero. In a language where every object lives on the heap
(Java before records, Python, most JavaScript runtimes), an allocation-heavy
domain, a pricing engine recomputing millions of `Money` values per second, can
put real pressure on the garbage collector, and the trade-off has to be
weighed against the correctness the immutability buys.

Primitive obsession versus code volume is the force that decides how far to
push the pattern. Wrapping every primitive in a named Value Object, an
`EmailAddress` instead of a `string`, a `Percentage` instead of a `double`,
buys validation, self-documentation, and type safety at the boundary, at the
cost of more classes, more constructors, and more places a reviewer has to
learn the shape of. Teams disagree in good faith about where the line sits, and
this entry does not claim a universal answer.

Structural equality cost versus object size is a force that grows with the
Value Object's shape. A `Money` with two fields compares in constant time. A
`GeoPolygon` with a thousand coordinate pairs compares in linear time on every
equality check, and if that Value Object is used as a hash key or a set
member, the cost is paid on every lookup, not only on construction.

Persistence mapping versus domain purity is the force that surfaces at the
boundary with a relational database. A Value Object with no identity of its own
does not map cleanly onto a table with a primary key, which is exactly why the
JPA and Hibernate specification carves out a separate mapping category,
`@Embeddable`, rather than forcing every Value Object to masquerade as a row
with a synthetic id. The Jakarta Persistence 3.1 Specification, section 2.6,
Embeddable Classes, states that entities "may use other fine-grained classes to
represent entity state" and that "instances of these classes, unlike entity
instances, do not have persistent identity of their own"
([Jakarta Persistence 3.1 Specification, section 2.6](https://jakarta.ee/specifications/persistence/3.1/jakarta-persistence-spec-3.1.html),
verified 2026-08-02).

## 4. Applicability and non-applicability

Reach for a Value Object when the concept is fully described by its
attributes, when two instances with identical attributes should be treated as
completely interchangeable everywhere in the system, when the concept has no
lifecycle a caller needs to track (it is not created once and then edited over
time as "the same one"), when sharing an instance safely (because it cannot be
mutated) is more valuable than mutating in place, when the concept naturally
groups several primitives that are always used together (an amount and a
currency, a start and an end date, latitude and longitude), and when you need
the concept to be safe to use as a dictionary key, a set member, or a cache key
without a bespoke identity comparator.

Do NOT reach for a Value Object in these situations, and treat each of these
as a reason to reach for a different pattern instead, most often Entity.

- The concept has a lifecycle the domain must track across changes. A bank
  account whose balance changes over time is still "the same account", which
  is the defining trait of an Entity, not a Value Object. Wrapping its balance
  in an `AccountBalance` Value Object is fine, but the account itself is not one.
- Two instances with identical current attributes must still be treated as
  distinct because the domain cares which one it is. Two `Order` records with
  identical line items placed by two different customers are not
  interchangeable, because an order has an identity independent of its
  contents that the business tracks (fulfillment status, refund history).
- The object needs to be mutated in place for correctness or performance
  reasons that the domain genuinely requires, such as an in-memory buffer being
  filled incrementally by a parser. Forcing immutability there produces
  needless allocation churn with no domain benefit.
- The object is large and its per-comparison or per-copy cost would dominate a
  hot path, and the language offers no cheap value-type mechanism (a struct or
  record) to absorb that cost. In that situation a Flyweight or a mutable
  builder that produces an immutable Value Object only at the end is often the
  better shape (see dimension 13).
- The persistence layer genuinely needs to track and query the object
  independently, by its own primary key, across relationships from multiple
  owners. That need is the signal that the concept is an Entity wearing Value
  Object clothing, and the fix is to give it identity, not to force an
  `@Embeddable` mapping onto it.
- The object represents a reference to something external and mutable that the
  system does not own the truth of, such as a live handle to an open file or a
  network connection. Those are resources with their own lifecycle concerns
  and belong to a different family of patterns entirely (Resource Acquisition,
  Unit of Work).

## 5. Structure

The pattern has three participants, and the third is often implicit rather
than a separate class.

The **Value Object** itself holds a fixed set of attributes assigned once at
construction, exposes no mutator that changes those attributes after
construction, implements equality and a hash function derived entirely from
its attributes rather than from identity, and offers operations that, when they
would logically "change" the value, instead return a new Value Object leaving
the receiver untouched. The Value Object is also responsible for enforcing its
own invariants at construction time, so an instance that exists is guaranteed
valid for its entire lifetime, a property Evans calls the self-validating
value.

The **Client** is any Entity, Aggregate, service, or other Value Object that
holds a reference to the Value Object as one of its own attributes, passes it
as a parameter, or compares two instances of it. The client never needs to
know whether the instance it holds is "the same" instance another client
holds, because that question has no meaning for a Value Object. This is what
lets clients share instances freely with no defensive copying and no locking.

The **Factory**, sometimes a static method on the Value Object itself and
sometimes a separate class, is the single place construction is funneled
through when validation, normalization (such as uppercasing a currency code),
or the assembly of a compound value from raw input is non-trivial. Evans
treats the factory as optional machinery, present when construction has real
work to do and absent when a plain constructor already enforces the
invariants.

## 6. ASCII structure diagram

```
+----------------------+          holds / compares
|   Client (Entity or   |------------------------------+
|   Aggregate or        |                               |
|   another Value Object|                               v
+----------------------+                       +-----------------------+
                                                |     Value Object      |
                                                |------------------------|
                                                | - attribute1: Type    |
                                                | - attribute2: Type    |
                                                |------------------------|
                                                | + equals(other): bool |
                                                | + hashCode(): int     |
                                                | + withX(x): ValueObj  |
                                                +-----------------------+
                                                          ^
                                                          | constructs, validates
                                                          |
                                                +-----------------------+
                                                |   Factory (optional)  |
                                                | + of(raw...): ValueObj|
                                                +-----------------------+
```

No arrow in this diagram points from the Value Object back to a database row,
a registry, or any store of "the one true instance". Any number of equal
instances may exist simultaneously in memory, and none of them is more
authoritative than any other. This is the structural feature that most
sharply distinguishes the diagram from an Entity's structure diagram, where a
repository or identity map is a required participant.

## 7. Dynamics

Construction happens once, and the sequence never has a later "update" step
against the same instance, only the creation of a new instance that replaces
the old reference wherever the client chooses to hold the new one.

```
Client                    Factory (optional)          Value Object
  |                             |                            |
  |-- of(rawAmount, rawCcy) --->|                            |
  |                             |-- validate(rawCcy) ------->|
  |                             |<-- ok / throws ------------|
  |                             |-- new ValueObject(...) --->|
  |<-- returns ValueObject -----|                            |
  |                                                          |
  |-- price.add(tax) -------------------------------------->|
  |                              (reads own fields, computes  |
  |                               new fields, allocates a     |
  |                               brand new instance)         |
  |<-- returns a DIFFERENT ValueObject instance --------------|
  |
  |-- price.equals(otherPrice) ----------------------------->|
  |<-- true, computed by comparing every field ---------------|
  |
  |   (price and otherPrice may be, and often are, two
  |    distinct objects in memory that never share an
  |    identity, yet the domain treats them as one value)
```

The dynamic that matters most to get right in an implementation is the last
one in the diagram. `equals` must never fall back to identity comparison
(`this == other` as the sole check, or a language default such as unmodified
Java `Object.equals`), because that silently turns the Value Object back into
an Entity wearing the wrong hat, and every caller who trusted the value
semantics starts getting wrong answers the moment two logically identical
values happen to live at different memory addresses, which for a Value Object
is the common case, not the exception.

## 8. Implementation variants

**Language-native immutable record.** Java, Kotlin, C#, and Scala each ship a
first-class construct that generates value equality, `hashCode`, and a
`toString` from a fixed set of components, closing off most of the ways a
hand-written Value Object goes wrong. Java's `record` keyword, introduced as a
preview feature and finalized in JDK 16, makes every component field
`private final`, and the specification is explicit that "a record's fields are
final because the class is intended to serve as a simple 'data carrier'", and
that generated equality means "two record objects are equal if they are of the
same type and contain equal field values"
([Oracle Java SE 17 Language, Records](https://docs.oracle.com/en/java/javase/17/language/records.html),
verified 2026-08-02). Kotlin's `data class` generates the same equality and
hash pair from primary-constructor properties only, plus a `copy()` function
that produces a modified sibling without mutating the receiver
([Kotlin documentation, Data classes](https://kotlinlang.org/docs/data-classes.html),
verified 2026-08-02). C#'s `record` keyword generates compiler-produced value
equality and `with` expressions for the same non-destructive-mutation pattern,
and Microsoft's own documentation states the intended use directly. "Use
records when a type's primary role is storing data and two instances with the
same values should be considered equal"
([Microsoft Learn, C# record types](https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/types/records),
verified 2026-08-02).

**Frozen dataclass or immutable struct in a language with no dedicated record
keyword.** Python's `dataclasses.dataclass(frozen=True)` generates `__eq__`
comparing fields in order and, when combined with `eq=True`, also generates a
matching `__hash__`, while raising `FrozenInstanceError` on any attempted
attribute assignment after construction. The documentation is candid that this
is an emulation rather than a language guarantee. "It is not possible to
create truly immutable Python objects. However, by passing `frozen=True` ...
you can emulate immutability"
([Python 3 documentation, dataclasses](https://docs.python.org/3/library/dataclasses.html),
verified 2026-08-02). Go has no record type at all, but a struct composed
entirely of comparable fields (numbers, strings, arrays of comparable types)
gets structural `==` for free from the language, and the idiom is a
constructor function that validates inputs and returns the struct by value,
never a pointer, so that copying the struct is the natural way to pass it
around and mutation of a caller's copy cannot reach the original.

**Value type at the language level.** Swift structs, Go structs, C#
`record struct`, and Rust structs deriving `PartialEq`, `Eq`, `Clone`, and
`Copy` are copied by value on assignment and passed by value into functions by
default, which means the "no shared mutable state" property Value Object
requires is enforced by the compiler rather than by convention. This is the
implementation variant with the least ceremony and the fewest ways to get
wrong, and it is why Swift's own standard library models nearly all of its
value-shaped types (`Decimal`, `Date`, `URL`) as structs rather than classes.

**Self-validating constructor versus static factory with validation.** Where
construction can fail (an invalid ISO currency code, a negative amount that
the domain forbids), the choice is between throwing from the primary
constructor directly, which forces every caller through the validation with no
way around it, and exposing a static factory method (`Money.of(...)`) that
wraps the constructor and can additionally normalize input before validating
it, such as uppercasing a currency code before checking its length. Evans
favors the second shape whenever normalization is involved, because a private
constructor combined with a public factory keeps the invariant enforcement in
exactly one place while still allowing the constructor itself to stay simple.

**Interning or caching common instances.** A small, frequently used set of
Value Object instances (`Money.ZERO`, `Percentage.HUNDRED`, `Color.WHITE`) is
sometimes cached as static constants purely as a performance and readability
convenience, never as a correctness requirement, since two freshly constructed
equal instances must already compare equal without any caching. This overlaps
with the Flyweight pattern discussed in dimension 13, and the two are easy to
conflate. Flyweight shares instances to save memory across many logical values,
Value Object equality works whether or not any sharing happens at all.

## 9. Known production uses

The Java Time API, `java.time.LocalDate`, `LocalDateTime`, `Duration`, and
`Period`, is a canonical Value Object family in the standard library. Every
type is immutable, every arithmetic operation (`plusDays`, `plusMonths`)
returns a new instance, and equality and hashing are derived entirely from the
represented value, not from object identity. The JDK's own `java.time`
package documentation states the classes are "immutable and thread-safe",
which is the direct consequence of committing to value semantics rather than
entity semantics for a date or duration ([Oracle Java SE 17 API,
java.time package summary](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/time/package-summary.html),
verified 2026-08-02).

Jakarta Persistence (formerly JPA) and its dominant implementation, Hibernate
ORM, provide a first-class mapping category, `@Embeddable`, specifically for
persisting Value Objects as part of an owning entity's row rather than as a
separately identified table, exactly the mapping Fowler and Evans both
describe as the correct database shape for a value. The specification states
plainly that embeddable instances "do not have persistent identity of their
own" and "belong strictly to their owning entity"
([Jakarta Persistence 3.1 Specification, section 2.6, Embeddable Classes](https://jakarta.ee/specifications/persistence/3.1/jakarta-persistence-spec-3.1.html),
verified 2026-08-02). This mapping category exists precisely because the
enterprise Java community, going back to the pattern's earliest description in
Fowler's `Money` example, needed a standard way to persist Value Objects
without giving them a false identity column.

.NET's `System.Guid`, `System.DateTimeOffset`, and `System.Decimal` are
implemented as structs in the Base Class Library, which the C# language
specification and Microsoft's own documentation describe as value types with
copy-on-assignment and structural equality by default, the same properties
this pattern requires ([Microsoft Learn, C# record types, "Value equality"
section](https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/types/records),
verified 2026-08-02, describing the struct-versus-class semantics that the BCL
value types rely on). More recent .NET code that models new domain concepts,
such as ASP.NET Core's `PathString` and `QueryString` types, follows the same
convention of a struct with value equality for anything that represents a
piece of data rather than a service or a resource.

Android application development, as recommended in the official Kotlin and
Android developer guidance, uses `data class` extensively to represent UI
state and immutable domain snapshots passed between layers of an app
(ViewModel to Compose UI), relying on the compiler-generated `equals`,
`hashCode`, and `copy()` described in dimension 8 to make state comparisons and
non-destructive updates safe by default rather than by discipline
([Kotlin documentation, Data classes](https://kotlinlang.org/docs/data-classes.html),
verified 2026-08-02).

## 10. Consequences

The pattern buys several things at once, and each of them follows directly
from the immutability and identity-free equality Evans derives in chapter 5.

Positive consequences. Instances are safe to share freely between threads and
between objects with no defensive copying and no synchronization, because
nothing can mutate a shared instance out from under a holder. Equality behaves
the way a reader intuitively expects, two prices that say the same amount in
the same currency are simply equal, which removes a class of subtle bugs
where reference-equal checks silently fail for logically identical data.
Reasoning about a function that takes a Value Object as a parameter is
simpler, because the function cannot have mutated the caller's copy, a
property functional-programming literature calls referential transparency for
the data itself. The concept becomes safe to use as a dictionary key or set
member without a custom identity-based comparator. The domain model gains
vocabulary. a `Percentage` or an `EmailAddress` documents intent and enforces
validity at the type level in a way a bare `double` or `string` cannot.

Negative consequences. Every "change" allocates a new instance, and in a
language without cheap value types this adds allocation pressure that can
matter in a hot loop, the exact trade-off discussed in dimension 3. Equality
and hashing must be maintained by hand, or generated correctly by the
language's tooling, for every field the Value Object owns, and a single field
added later without also updating a hand-written `equals` is a silent
correctness bug that compiles cleanly and passes most tests. A large Value
Object composed of many fields, or one holding a nested collection, pays a
non-trivial cost on every equality check and every copy, since the whole
structure must be compared or duplicated rather than a single identity
pointer. Introducing Value Objects into a codebase that has spent years
passing primitives around is a real migration cost, touching every call site
that constructed the old primitive shape directly. Serialization formats
(JSON, protobuf, a database column) must be versioned carefully, because
changing which fields participate in equality after data has already been
persisted or transmitted can silently change what "equal" means for records
already in flight.

## 11. Failure modes and misuse

**Symptom.** An object stored as a key in a `HashSet` or `HashMap` becomes
unreachable by the key that was used to insert it, even though the caller can
see the object still exists in the collection when iterating.
**Cause.** The Value Object was not actually immutable, one of its fields was
mutated after insertion (directly, or through a mutable collection it exposed
by reference rather than by defensive copy), which changed its hash code
without the hash table being told to relocate the entry.
**Fix.** Enforce true immutability all the way down. make every field
`final`/`readonly`/`val`, and where a field is itself a mutable collection or
array, store and return a defensive copy rather than the live reference, or
switch to a genuinely immutable collection type.

**Symptom.** Two Value Objects that a business analyst would call "the same
price" compare unequal in code, and a downstream deduplication, caching, or
grouping step silently treats them as two different values.
**Cause.** Equality was left at its language default (reference or identity
comparison) instead of being overridden or generated to compare fields, most
commonly because the type started life as a plain class and the equality
override was simply forgotten, or because a hand-rolled `equals` compares only
some of the fields and misses one added later.
**Fix.** Generate equality with the language's own mechanism (`record`,
`data class`, `frozen dataclass`, struct-derived `Equatable`/`PartialEq`)
rather than hand-writing it wherever the language provides that mechanism, and
where it does not, write a single test that constructs two instances from
identical raw input and asserts they compare equal, so a future field addition
that breaks the invariant fails a test immediately rather than shipping.

**Symptom.** Construction of the Value Object succeeds with input a domain
expert would call obviously invalid, such as a negative money amount for a
domain where negative prices are meaningless, or a two-letter currency code,
and the invalid instance then propagates through several layers before a
downstream check finally rejects it, or worse, silently corrupts a total.
**Cause.** The Value Object exposed a public constructor or a permissive
factory that does not validate, on the assumption that "the caller will only
ever pass valid data", which is exactly the assumption Value Object exists to
remove.
**Fix.** Validate every invariant inside the constructor or the single factory
method that all construction paths funnel through, so an instance that exists
is guaranteed valid by construction, the self-validating value Evans describes,
and add a unit test per invariant that asserts construction with invalid input
throws rather than succeeds.

**Symptom.** A pricing or geometry-heavy service that recomputes millions of
Value Object instances per second shows rising GC pause times or heap growth
under load, even though no logical memory leak exists anywhere in the code.
**Cause.** The domain is allocating a fresh heap object for every intermediate
value in a hot loop, in a language where the Value Object is implemented as a
heap-allocated class rather than a stack-allocated value type, and the volume
of short-lived allocations outpaces what the collector can reclaim cheaply.
**Fix.** In a language that offers a cheap value type (Swift struct, C#
`record struct`, Rust struct with `Copy`), prefer it for the hot-path type.
Where the language has no such mechanism, restructure the hot loop to avoid
constructing intermediate Value Objects that are immediately discarded,
accumulate in a mutable local, and only construct the final immutable Value
Object once at the loop's boundary, which trades a small, contained mutable
scope for the larger allocation cost, without exposing that mutability to any
caller.

**Symptom.** The same nominal domain value, an amount that is meant to be
identical, compares unequal or reports a different hash on two different nodes
of a distributed system, causing deduplication or idempotency logic that
relies on equality to fail intermittently.
**Cause.** The Value Object's equality includes a field whose representation
is not canonical, most often a floating-point amount affected by rounding
differences between platforms, or a string field affected by locale-dependent
casing or Unicode normalization that was not normalized at construction time.
**Fix.** Store monetary and other exact quantities in an exact type (an
integer count of minor units, or a fixed-point decimal type) rather than a
binary floating-point type, and normalize any string field (case, Unicode
normalization form, trimming) inside the constructor so that every instance
constructed from logically identical raw input produces byte-identical
internal state before equality is ever evaluated.

## 12. Trade-off matrix

| Force | Value Object | Entity | Data Transfer Object (mutable) | Bare primitive / string |
|---|---|---|---|---|
| Identity tracked across changes | No, by design | Yes, that is its purpose | Usually no, but not enforced | No |
| Equality semantics | Structural, all fields | Identity field only, even if all other fields match | Whatever the language default happens to be, often reference | Structural for the primitive itself, no domain meaning attached |
| Safe to share a reference with no copy | Yes | No, mutation by one holder is visible to all holders | No, same risk as a plain mutable object | Yes, primitives are typically immutable already |
| Enforces its own invariants | Yes, at construction | Sometimes, often enforced by the aggregate root instead | Rarely, DTOs typically skip validation by design | No, "2026-13-45" is a perfectly valid string |
| Natural key in a hash map or set | Yes, without extra work | Only if the identity field alone is used for equality | Not reliable, since equality is undefined or reference-based | Yes, but no domain meaning is captured |
| Allocation cost per "change" | One new instance per change | None, mutated in place, or a new entity version depending on strategy | One new instance if treated immutably, or in-place mutation otherwise | Negligible, primitives are cheap |
| Persistence mapping | Embedded in the owner's row (`@Embeddable`) | Its own table with a primary key | Not persisted directly, a serialization shape | A column, no domain semantics preserved |

The comparison against a bare primitive is the one worth dwelling on, because
it is the alternative most codebases actually start from. A primitive carries
no validation, no domain vocabulary, and no protection against passing an
amount where a percentage was expected, since both are just a `double` to the
compiler. Value Object exists specifically to close that gap, at the cost of
one more type in the model.

## 13. Related and incompatible patterns

**Entity** is the direct counterpart the identity question routes to when the
answer is yes rather than no. Evans presents Value Object and Entity as the
two possible answers to the same single question asked of every model
element, and a mature domain model usually contains far more Value Objects
than Entities, because most of what an Entity carries as state is itself
built from Value Objects (an `Order` entity's `total` field is a `Money`
Value Object, its `shippingAddress` field is an `Address` Value Object).

**Aggregate** composes Entities and Value Objects behind a single consistency
boundary with one Entity acting as the Aggregate Root. Value Objects are the
most common kind of state an Aggregate holds internally, precisely because
their lack of independent identity means they cannot be referenced from
outside the aggregate without breaking the aggregate's consistency boundary,
which is exactly the invariant Aggregate is built to protect.

**Factory** is frequently paired with Value Object at construction time when
validation or assembly from raw input is non-trivial, as described in
dimension 5 and dimension 8. The relationship is compositional rather than a
substitute. a Factory produces a Value Object, it does not replace one.

**Flyweight** looks similar at a glance, both patterns share instances of
something small and immutable, but the motivations differ. Flyweight exists
to reduce memory footprint by physically sharing one instance across many
logical uses that would otherwise each hold a distinct copy, and its identity
of the shared instance is an implementation detail the client is never
supposed to observe through equality. Value Object exists to answer the
identity question with "no, only content matters", and whether any particular
runtime happens to share the underlying memory is irrelevant to its
correctness, since equality is defined structurally regardless of sharing.

**Money pattern** (Fowler, Patterns of Enterprise Application Architecture,
2002) is the specific, named archetypal instance of Value Object, described
independently and slightly before Evans's general formulation, and is worth
citing separately because a reader who searches for "the money pattern" and a
reader who searches for "value object" are frequently looking for the same
underlying idea from two different books.

**Null Object** is compatible and often implemented as a special, cached
instance of a Value Object (an `EmptyAddress`, a `Money.ZERO`) that
participates in the same equality and arithmetic operations as any other
instance of the type, avoiding a separate `null`-check branch at every call
site.

Value Object is incompatible with treating the same conceptual type as both an
Entity and a Value Object inside the same model without a deliberate,
explicit boundary. A `CustomerAddress` that is sometimes looked up by a
database identity column and sometimes compared by content within the same
bounded context produces exactly the aliasing and stale-comparison bugs the
pattern exists to eliminate, and the fix is to pick one answer to the identity
question for that concept inside that bounded context, even if a neighboring
bounded context legitimately answers it the other way.

## 14. Refactoring path in and out

Introducing a Value Object into code that currently passes a cluster of
primitives around follows the shape Martin Fowler names **Introduce Parameter
Object** combined with **Replace Data Value with Object**, both catalogued in
his refactoring literature. The steps, in order. first identify a group of
primitives that always travel together as parameters or fields (an amount and
a currency code, a start date and an end date), because a group that always
travels together and is never used independently is the signal a Value Object
concept already exists implicitly in the design. Second, create the new type
with a constructor or factory that accepts exactly that group and validates
it. Third, change one call site at a time to construct the new type instead of
passing the raw primitives, keeping both the old primitive-passing signature
and the new Value-Object-passing signature available in parallel during the
migration so the change can land incrementally rather than as one large,
risky commit. Fourth, once every call site has moved to the new type, delete
the old signature, and add the equality and hashing behavior described in
dimension 8 if the language does not generate it automatically. Fifth, push
behavior that was previously scattered as free functions operating on the raw
primitives (a currency-conversion routine, a date-range-overlap check) onto
the new type itself as a method, which is usually the point where a team
notices the Value Object was worth introducing, because logic that used to be
duplicated at every call site now lives in exactly one place.

Removing a Value Object, which is rare but does happen, is warranted when the
concept the team originally modeled turns out never to vary independently of
its container, so wrapping it added indirection with no corresponding domain
benefit, for example a `Quantity` Value Object wrapping a plain integer that
never carries a unit, never gets validated beyond "is a number", and is never
passed anywhere the raw integer would not have worked identically. The
removal path mirrors the introduction path in reverse. confirm every call
site only ever reads the single wrapped field and never calls a domain method
on the Value Object, inline the field access at each call site, and delete the
type once nothing references it. This is the same "collapse" direction
Fowler's own refactoring catalog treats as symmetric with "extract", and a team
that finds itself removing more Value Objects than it introduces is a signal
the domain model was over-decomposed relative to the domain's actual
complexity, worth raising explicitly with whoever owns the model.

## 15. Testing and verification

Testing a Value Object centers on three properties that a hand-written or
generated implementation must satisfy, and each has a direct, mechanical test.

**The equality contract.** Assert reflexivity (an instance equals itself),
symmetry (`a.equals(b)` implies `b.equals(a)`), transitivity (if `a` equals
`b` and `b` equals `c`, then `a` equals `c`), and consistency with hashing (two
instances that compare equal must produce the same hash code, the contract
every hash-based collection in every mainstream standard library relies on).
Construct two separate instances from identical raw input in the test and
assert they are equal but not the same reference, which is the single test
most likely to catch a regression where equality silently reverts to the
language's identity default described in dimension 11.

**Immutability.** Assert that no public method or property setter exists that
mutates state after construction, which in a statically typed language is
partly enforced at compile time by making fields `final`/`readonly`/`val` and
is worth an explicit reflection-based or type-system-based test in a language
where that enforcement is only conventional. For a Value Object that exposes a
collection field, assert specifically that mutating the returned collection
does not change the internal state observed on a second call, which catches
the missing-defensive-copy failure mode from dimension 11 directly.

**Invariant enforcement at construction.** For every business rule the
constructor or factory is meant to enforce (a currency code must be exactly
three letters, an amount must not be negative in a domain where negative
amounts are forbidden), write one test per invariant that supplies input
violating exactly that rule and asserts construction throws or otherwise
fails, and one test that supplies valid boundary input (a zero amount, if
zero is legal) and asserts construction succeeds. Property-based testing tools
(Hypothesis in Python, fast-check in TypeScript, QuickCheck-style libraries in
other ecosystems) are well suited to the equality-contract tests specifically,
because they can generate many pairs of "same logical value, different
construction path" inputs automatically and check the equality and hashing
laws hold across all of them, rather than relying on a handful of
hand-picked examples.

Value Object makes the code that uses it easier to test in one specific way.
because instances are immutable, a test can construct a fixture once, reuse it
across many assertions, and never worry that an earlier assertion mutated it
and corrupted a later one, a class of test-pollution bug that is common with
mutable fixtures and structurally impossible with a correctly implemented
Value Object.

## 16. Observability signals

Much of this dimension is engineering judgement rather than a sourced
standard, since Value Object is a modeling and language-level concept with no
runtime protocol of its own to instrument. The observability concerns that
apply are indirect, downstream of the pattern rather than intrinsic to it.

Allocation rate and garbage collection pause time are the primary signal in a
managed-heap language (the JVM, the CLR, Python, JavaScript engines) for a
service that constructs Value Objects at high volume in a hot path, since the
consequence discussed in dimension 3 and the failure mode in dimension 11
(rising GC pressure from Value-Object-heavy loops) shows up first as an
elevated allocation rate metric and later as p99 latency degradation
correlated with GC pause events, before it shows up anywhere in application
logs.

Structured log entries that include a Value Object should log its value, not
a synthetic identity, since logging an object reference or a memory address
for something the domain has decided has no identity is a signal the logging
code is treating the Value Object incorrectly, and it also produces logs that
are useless for correlating two log lines that describe the same logical
value. A well-formed log line reads `price=USD 2159`, not `price=Money@7a3f21`.

Cache hit rate is the relevant signal when a Value Object is used as a cache
key, since the correctness of that cache depends entirely on the equality
contract from dimension 15 holding under real traffic, and an unexpectedly low
hit rate for keys the caller believes are logically identical is often the
first production symptom of the equality bug described in dimension 11.

## 17. Security and privacy implications

A Value Object that wraps a piece of personally identifiable or otherwise
sensitive data (an `EmailAddress`, a `NationalIdNumber`, a `CreditCardNumber`)
is a natural and valuable place to centralize masking and validation logic,
since every call site that constructs one goes through the same validation and
every call site that logs or displays one can call a single, deliberately
written `toString` or `describe` method that redacts the sensitive portion,
rather than relying on every call site individually remembering to redact.
This is a genuine security benefit of the pattern, not merely a side effect.

The corresponding risk is the mirror image of that benefit. A generated
`toString`, `equals`, or serialization method (from `record`, `data class`, a
frozen dataclass, or an auto-derived `Debug` implementation) typically includes
every field by default, and a Value Object wrapping sensitive data that relies
on language-generated string conversion or debug formatting can leak that data
into application logs, crash reports, or error messages the moment it appears
anywhere the language's default formatting is invoked, such as an
unhandled-exception stack trace that happens to include the object in its
message. Where a Value Object wraps sensitive data, override the generated
`toString`/`describe`/`Debug` output explicitly to redact the sensitive
portion rather than trusting the language's default field-by-field dump, and
audit call sites (particularly logging and exception-handling code) that
might invoke that default formatting before the override is added.

A second, narrower implication concerns the caching and interning variant
described in dimension 8. Interning Value Object instances that wrap sensitive
data (caching a small pool of `EmailAddress` instances, for example) means a
single shared instance is reachable from multiple unrelated parts of the
system simultaneously, which is safe from a correctness standpoint because the
instance is immutable, but worth a deliberate decision from a data-handling
standpoint if the system has requirements (such as data-retention deletion) that
depend on being able to enumerate every place a particular piece of sensitive
data is currently held in memory, since a shared instance is, by definition,
held in more than one logical place at once.

## Code examples

### TypeScript

Compiled and run with `npx tsc --strict --target es2020` followed by `node`.
Output confirmed. `USD 2159`, then `true` for structural equality, then
`false` for reference identity, matching the pattern's contract exactly.

```typescript
class Money {
  private constructor(
    readonly amountMinor: bigint,
    readonly currency: string
  ) {
    if (currency.length !== 3) {
      throw new Error("currency must be a 3 letter ISO 4217 code");
    }
  }

  static of(amountMinor: bigint, currency: string): Money {
    return new Money(amountMinor, currency.toUpperCase());
  }

  add(other: Money): Money {
    if (other.currency !== this.currency) {
      throw new Error(`cannot add ${other.currency} to ${this.currency}`);
    }
    return new Money(this.amountMinor + other.amountMinor, this.currency);
  }

  equals(other: Money): boolean {
    return this.amountMinor === other.amountMinor && this.currency === other.currency;
  }

  toString(): string {
    return `${this.currency} ${this.amountMinor}`;
  }
}

const price = Money.of(1999n, "usd");
const tax = Money.of(160n, "USD");
const total = price.add(tax);

console.log(total.toString());
console.log(price.equals(Money.of(1999n, "USD")));
console.log(price === Money.of(1999n, "USD"));
```

### Python

Run with `python3`. Output confirmed. the frozen dataclass reports equal for
two independently constructed instances with matching hash codes, while
`is` correctly reports they are different objects.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    amount_minor: int
    currency: str

    def __post_init__(self) -> None:
        if len(self.currency) != 3:
            raise ValueError("currency must be a 3 letter ISO 4217 code")
        object.__setattr__(self, "currency", self.currency.upper())

    def add(self, other: "Money") -> "Money":
        if other.currency != self.currency:
            raise ValueError(f"cannot add {other.currency} to {self.currency}")
        return Money(self.amount_minor + other.amount_minor, self.currency)


price = Money(1999, "usd")
tax = Money(160, "USD")
total = price.add(tax)

print(total)
print(price == Money(1999, "USD"))
print(price is Money(1999, "USD"))
print(hash(price) == hash(Money(1999, "USD")))
```

### Go

Run with `go run money.go`. Output confirmed. `{2159 USD}` for the summed
total, then `true` for the built-in `==` operator, since a Go struct with only
comparable fields gets structural equality from the language with no code
written for it.

```go
package main

import (
	"errors"
	"fmt"
	"strings"
)

type Money struct {
	AmountMinor int64
	Currency    string
}

func NewMoney(amountMinor int64, currency string) (Money, error) {
	if len(currency) != 3 {
		return Money{}, errors.New("currency must be a 3 letter ISO 4217 code")
	}
	return Money{AmountMinor: amountMinor, Currency: strings.ToUpper(currency)}, nil
}

func (m Money) Add(other Money) (Money, error) {
	if other.Currency != m.Currency {
		return Money{}, fmt.Errorf("cannot add %s to %s", other.Currency, m.Currency)
	}
	return Money{AmountMinor: m.AmountMinor + other.AmountMinor, Currency: m.Currency}, nil
}

func main() {
	price, _ := NewMoney(1999, "usd")
	tax, _ := NewMoney(160, "USD")
	total, _ := price.Add(tax)

	fmt.Println(total)

	other, _ := NewMoney(1999, "USD")
	fmt.Println(price == other)
}
```

### Swift

Compiled and run with `swiftc money.swift -o money_swift`. Output confirmed.
`USD 2159`, then `true` for `Equatable` conformance, demonstrating a value
type (`struct`) that carries value semantics natively, with no manual
`equals` or `hashCode` implementation required beyond declaring the
protocol conformance.

```swift
struct Money: Equatable, CustomStringConvertible {
    let amountMinor: Int64
    let currency: String

    init(amountMinor: Int64, currency: String) throws {
        guard currency.count == 3 else {
            throw MoneyError.invalidCurrency
        }
        self.amountMinor = amountMinor
        self.currency = currency.uppercased()
    }

    func adding(_ other: Money) throws -> Money {
        guard other.currency == currency else {
            throw MoneyError.currencyMismatch
        }
        return try Money(amountMinor: amountMinor + other.amountMinor, currency: currency)
    }

    var description: String { "\(currency) \(amountMinor)" }
}

enum MoneyError: Error {
    case invalidCurrency
    case currencyMismatch
}

let price = try Money(amountMinor: 1999, currency: "usd")
let tax = try Money(amountMinor: 160, currency: "USD")
let total = try price.adding(tax)

print(total)
let other = try Money(amountMinor: 1999, currency: "USD")
print(price == other)
```

Java and C# are omitted as separate examples because their idiomatic form,
the `record` keyword shown in dimension 8, is a one-line declaration
(`record Money(long amountMinor, String currency) {}` in Java,
`public record Money(long AmountMinor, string Currency);` in C#) that
generates every property demonstrated above automatically, and reproducing
it as a full example would add length without adding a distinct
implementation technique beyond what dimension 8 already documents with
citations to each language's own reference material.

## 18. References

- Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
  Software*, Addison-Wesley, 2003, chapter 5, "A Model Expressed in Software",
  section "Value Objects".
- Martin Fowler, *Patterns of Enterprise Application Architecture*,
  Addison-Wesley, 2002, Base Patterns chapter, the `Money` class example.
- Martin Fowler, "ValueObject",
  [martinfowler.com/bliki/ValueObject.html](https://martinfowler.com/bliki/ValueObject.html),
  verified 2026-08-02.
- Oracle, "Records", Java SE 17 Language documentation,
  [docs.oracle.com/en/java/javase/17/language/records.html](https://docs.oracle.com/en/java/javase/17/language/records.html),
  verified 2026-08-02.
- Oracle, `java.time` package summary, Java SE 17 API documentation,
  [docs.oracle.com/en/java/javase/17/docs/api/java.base/java/time/package-summary.html](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/time/package-summary.html),
  verified 2026-08-02.
- Kotlin documentation, "Data classes",
  [kotlinlang.org/docs/data-classes.html](https://kotlinlang.org/docs/data-classes.html),
  verified 2026-08-02.
- Microsoft Learn, "C# record types",
  [learn.microsoft.com/en-us/dotnet/csharp/fundamentals/types/records](https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/types/records),
  verified 2026-08-02.
- Python Software Foundation, "dataclasses, Data Classes", Python 3
  documentation,
  [docs.python.org/3/library/dataclasses.html](https://docs.python.org/3/library/dataclasses.html),
  verified 2026-08-02.
- Eclipse Foundation, Jakarta Persistence 3.1 Specification, section 2.6,
  "Embeddable Classes",
  [jakarta.ee/specifications/persistence/3.1/jakarta-persistence-spec-3.1.html](https://jakarta.ee/specifications/persistence/3.1/jakarta-persistence-spec-3.1.html),
  verified 2026-08-02.
- Vaughn Vernon, *Implementing Domain-Driven Design*, Addison-Wesley, 2013,
  chapter 6, "Value Objects", for the interned-instance and self-validation
  refinements to Evans's original description.
