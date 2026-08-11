---
name: Entity
slug: entity
family: 11-domain-driven-design
category: Tactical Modeling
aliases: [Domain Entity, Identity Object, Reference Object]
first_described: "Evans 2003"
maturity: canonical
related: [value-object, aggregate, identity-field, repository, factory]
incompatible_with: []
verified: 2026-08-02
---

# Entity

## 1. Name, aliases, and lineage

The canonical name is Entity, and it comes from Eric Evans, *Domain-Driven
Design. Tackling Complexity in the Heart of Software*, Addison-Wesley, 2003.
Evans set out a classification of domain objects into three kinds, Entities,
Value Objects, and Services, and Entity is the first and most load-bearing of
the three. Wikipedia's summary of the book states the definition directly. an
Entity is "an object defined not by its attributes, but its identity," and
gives the example of an airline seat, where the seat number is what makes the
seat itself distinct across bookings, changes of passenger, and changes of
meal preference (Wikipedia, "Domain-driven design," verified 2026-08-02,
https://en.wikipedia.org/wiki/Domain-driven_design).

Martin Fowler's own summary of Evans's classification, published as a bliki
entry, restates the same three-way split and defines an Entity as "objects
that have a distinct identity that runs through time and different
representations," contrasting it against Value Objects, which "matter only as
the combination of their attributes," and Services, "a standalone operation
within the context of your domain" (Martin Fowler, "EvansClassification,"
verified 2026-08-02, https://martinfowler.com/bliki/EvansClassification.html).
Fowler's page is useful precisely because it is a secondary, independently
authored confirmation that the classification is not an idiosyncrasy of one
reading of the book, it is how the pattern-literate community actually
transmits the idea.

The alias Domain Entity distinguishes it in conversation from an ORM row class
or a database table row, both of which are sometimes loosely called "an
entity" in codebases that have never read Evans. Identity Object and Reference
Object appear in older, pre-DDD object modeling literature (the term
predates Evans, who borrowed and sharpened an existing intuition rather than
inventing the word from nothing), used to describe exactly the same idea, an
object you refer to across time rather than compare by value.

It is worth being precise about what this pattern entry is NOT. It is not the
JPA `@Entity` annotation, the Hibernate mapped class, or the Entity Framework
Core tracked type, even though all three borrow the word and all three
implement a version of the same identity concern at the persistence layer.
Those are covered here as implementation variants and known production uses,
because they are the most common place a working engineer meets this pattern,
but the DDD Entity is a modeling concept first. an object can be a DDD Entity
with no ORM anywhere near it, and an ORM-annotated class can violate every
DDD Entity discipline while still compiling and persisting correctly.

## 2. Problem and context

Every large domain contains two very different kinds of things, and
conflating them is one of the most common sources of subtle correctness bugs
in business software. Some things are described completely by their current
attributes, two objects with the same attributes are simply the same thing,
interchangeable, and can be freely replaced with each other or with a copy.
Other things persist a continuity across time and across every change to
their attributes, and two objects with identical attributes are still two
different things if their identity differs, while one object is still the
same thing after every attribute on it has changed.

A bank account is the second kind. An account holds a balance, a status, an
owner, and a set of recent transactions, and every one of those can change
over the account's life. what never changes, and what a banking system must
never confuse, is which account this is. The account you opened five years
ago with a starting balance of your first paycheck and the same account
today, holding a completely different balance, a different linked card, and
a different mailing address, is still, unambiguously, the same account. If
the system ever treats "an account with balance $500 and status active" as
interchangeable with any other account matching that description, because it
compared the two by value instead of by identity, money moves to the wrong
place.

The problem this pattern names and solves is exactly that confusion. a
codebase without a deliberate Entity versus Value Object distinction tends to
default every object into value-style equality (because that is what
language defaults, `==` on structs, `equals()` generated from all fields,
`==` on records, give you for free) or into ad hoc identity comparison
scattered wherever someone happened to need it, usually comparing a primary
key column by accident rather than by design. The context in which this
pattern becomes necessary is any domain where SOME concepts genuinely persist
identity across change and mutation (an order, a customer, a shipment, a
patient record, a hardware device) while other concepts in the SAME domain do
not (a street address on that order, a currency amount, a date range, a
color). A pattern applied everywhere, treating every object as an Entity, is
as wrong as applying it nowhere. the context is precisely the coexistence of
both kinds in one model, and the discipline is telling them apart honestly
for each concept rather than by convention or by ORM default.

## 3. Forces

**Identity continuity versus attribute equality.** The core tension the
pattern exists to resolve. business rules that reason about "this specific
account" need equality defined by a stable identifier, while every other
kind of comparison, deduplication, caching by value, and hashing wants
attribute-based equality. Choosing identity equality for an object that does
not need it makes ordinary comparisons (did the address change) awkward and
error-prone. choosing attribute equality for an object that does need
identity produces the exact bug class described in dimension 2.

**Mutability versus safety.** An Entity is typically mutable across its
lifetime, because the whole point is that its attributes legitimately change
while identity holds. Mutability is convenient for modeling real change but
is the classic source of aliasing bugs, shared references silently observing
each other's mutation, and makes the object unsafe to share across threads
without discipline. The pattern favors mutability in service of accurately
modeling change, and sacrifices the referential-transparency safety that an
immutable value gives for free.

**Cheap identity comparison versus a real generation strategy.** A stable
identifier has to come from somewhere, a database sequence, a UUID generator,
a natural key already present in the domain (an ISBN, a VIN, a national tax
ID), or a composite of several fields. Database-generated sequential keys
are cheap and dense but require a round trip before the identity exists,
which is awkward for an object created and used entirely in memory before
persistence. Client-generated UUIDs are available immediately but cost more
storage and index locality on the database side. Natural keys avoid a
manufactured identifier entirely but are fragile the moment the business
redefines what counts as unique (a VIN turns out not to be globally unique
across manufacturers in some edge cases, an ISBN is reused across printings).
The pattern does not resolve this force, it exposes it, and dimension 8 walks
the concrete trade-off.

**Encapsulated invariants versus anemic data holders.** Evans's stronger
claim, beyond "compare by identity," is that an Entity should hold enough
behavior to protect its own invariants (dimension 5 makes this explicit).
That trades simplicity, a plain data-carrying class is easier to serialize
and easier for a junior engineer to extend, for correctness, because a data
holder with public setters can be pushed into an invalid state by any caller
anywhere in the codebase, while a well-designed Entity refuses invalid state
transitions itself.

**Team topology and cognitive load.** In a codebase where the DDD Entity
versus Value Object split is explicit and enforced (base classes, linting,
naming conventions), a new engineer has to internalize one extra concept
before contributing. In a codebase without it, every engineer independently
reinvents an ad hoc, usually inconsistent, identity convention, and the cost
shows up later as bugs rather than up front as onboarding friction. The
pattern trades a small amount of up-front cognitive load for a large
reduction in a specific, expensive class of production defect.

## 4. Applicability and non-applicability

Reach for the Entity pattern when:

- The concept has a continuity across time that the business actually cares
  about. an order that moves through draft, placed, shipped, and delivered
  is still "the same order" the whole way, and code that treats a shipped
  order as a different thing from the draft that preceded it is wrong.
- Two instances with identical current attributes must still be treated as
  different things. two customers who happen to share a name and a mailing
  address are not the same customer.
- The object needs to protect invariants across a sequence of mutations, a
  bank balance that must never go negative, an inventory count that must
  never be decremented below zero, a state machine (draft to placed to
  shipped) where illegal transitions must be rejected.
- The object needs to be looked up, referenced, and reasoned about by a
  single stable handle across module boundaries, persistence, caching layers,
  and event streams. a stable identifier is what lets an event payload say
  "order 41f2..." rather than embedding a full snapshot every time.
- The object is the root, or an internal member, of an Aggregate (see
  dimension 13), where the Aggregate needs at least one Entity to serve as
  its addressable root.

Do NOT reach for it, and use a Value Object instead, when:

- The object is fully described by its current attributes and two instances
  with equal attributes are, for every purpose the domain cares about,
  interchangeable. a `Money` amount, a `DateRange`, a street `Address` as a
  descriptive attribute of something else, an `EmailAddress`, a `Color`. If
  you would happily replace one instance with a freshly constructed one
  carrying the same values and nothing in the system would notice or care,
  it is a Value Object, not an Entity.
- The concept has no continuity that the business cares about, it is
  created, used briefly, and discarded, with no later code path that needs
  to ask "is this the same one I saw before." a computed report row is a
  common example, generated fresh on every query, never referenced by
  identity afterward.
- You are tempted to give something an identity purely so you can put it in
  a `Set` or use it as a `Map` key, and the underlying reason is really
  deduplication by value. that is what a Value Object's structural equality
  is for. adding identity here is solving the wrong problem and introduces
  the exact bug class this pattern exists to prevent, elsewhere in the code.
- The performance or serialization cost of carrying a stable identifier
  through every layer (an extra column, extra index, extra field on every
  wire message) outweighs the benefit for a genuinely disposable, throwaway
  concept. this is rare inside a well-modeled domain but common at the edge,
  a DTO used purely to move data across one HTTP boundary rarely needs
  Entity-style identity of its own, separate from the identity of the
  domain object it represents.
- The object is a pure calculation or a stateless operation with no data of
  its own to hold. that is a Service in Evans's classification, not an
  Entity, and giving it an identity and a lifecycle is a category error.

## 5. Structure

An Entity participates in a domain model alongside these roles.

- **The Entity itself.** Holds a stable identifier (dimension 8 covers how
  that identifier is generated and typed), a set of mutable attributes, and
  the behavior needed to transition those attributes without violating its
  own invariants. It exposes methods that express business intent (
  `raiseCreditLimit`, `ship`, `cancel`) rather than bare property setters,
  which is what lets it refuse an illegal transition instead of silently
  accepting one.
- **The Identity (or Identifier).** A value, often itself modeled as a small
  Value Object rather than a bare primitive, that is stable for the whole
  life of the Entity and is the sole basis for the Entity's equality and
  hashing. This is frequently called out separately as its own tactical
  pattern, Identity Field, in Martin Fowler's *Patterns of Enterprise
  Application Architecture*, Addison-Wesley, 2003, which describes "saving a
  database ID field in an object to maintain identity between an in-memory
  object and a database row" (Martin Fowler, *Patterns of Enterprise
  Application Architecture*, catalog summary, verified 2026-08-02,
  https://martinfowler.com/eaaCatalog/identityField.html). Identity Field is
  the persistence-facing mechanism, Entity is the domain-modeling concept it
  serves.
- **Value Objects held by the Entity.** An Entity's non-identity attributes
  are frequently themselves Value Objects (an `EmailAddress`, a `Money`
  balance, an `Address`), because the Entity's own behavior is exactly what
  protects the composition of those values as a coherent whole. The
  Entity is the thing with identity and continuity, the Value Objects it
  holds are the thing that changes underneath that continuity.
- **The Aggregate boundary, when one exists.** An Entity is very often, but
  not always, part of a larger Aggregate (dimension 13), where exactly one
  Entity is designated the Aggregate root and every access to any other
  member, Entity or Value Object, of that Aggregate is required to go
  through the root. An Entity that is not an Aggregate root, sitting inside
  someone else's Aggregate, is still addressed internally by its own local
  identity but is never referenced directly from outside that Aggregate.
- **The Repository, when persistence is involved.** A Repository is
  typically keyed by an Entity's identity and is responsible for
  reconstituting the Entity, with its full state, from storage, and for
  persisting mutations back. The Entity's identity is exactly what makes
  this lookup by handle possible.
- **The Factory, when construction is complex.** When creating a valid
  Entity requires enforcing invariants across multiple fields at
  construction time, or requires generating the identity itself, a Factory
  is the conventional place to put that construction logic rather than
  scattering it across every call site.

## 6. ASCII structure diagram

```
+-----------------------------------------------------------+
|                        Aggregate                          |
|                                                             |
|   +---------------------------+                             |
|   |     Entity (root)         |                             |
|   |----------------------------|                             |
|   | - id : Identity  <stable>  |                             |
|   | - attribute1 : ValueObject |                             |
|   | - attribute2 : ValueObject |                             |
|   |----------------------------|                             |
|   | + doSomething()            |                             |
|   | + equals(other) -> by id   |                             |
|   +--------------+--------------+                             |
|                  | 1..*                                       |
|                  v                                            |
|   +---------------------------+                             |
|   |   Entity (internal)       |                             |
|   |----------------------------|                             |
|   | - id : Identity  <local>   |                             |
|   | - attribute : ValueObject  |                             |
|   +---------------------------+                             |
|                                                             |
+-----------------------------------------------------------+
                       ^
                       | looked up and reconstituted by id
                       |
              +-------------------+
              |    Repository      |
              |---------------------|
              | + findById(id)      |
              | + save(entity)      |
              +-------------------+
```

The internal Entity's identity is only guaranteed unique within the
Aggregate, not globally, which is why the diagram marks it `<local>`. Outside
the Aggregate, no code holds or dereferences that internal Entity's identity
directly, only the root's.

## 7. Dynamics

The runtime story of an Entity has two distinct phases, creation and
identity assignment, then a sequence of state transitions guarded by the
Entity's own methods.

```
Client              Factory / Constructor        Entity              Repository
  |                        |                        |                    |
  |-- create(rawInput) --->|                        |                    |
  |                        |-- validate invariants ->|                    |
  |                        |-- assign identity ----->|                    |
  |                        |<---- new Entity --------|                    |
  |<---- Entity instance --|                        |                    |
  |                        |                        |                    |
  |-- doAction(args) ------------------------------->|                    |
  |                        |          check invariant, mutate, or reject  |
  |<---------------- success or domain exception -----|                    |
  |                        |                        |                    |
  |-- save(entity) ---------------------------------------------------->  |
  |                        |                        |    persist by id    |
  |<--------------------------------------------------- ack --------------|
  |                        |                        |                    |
  |-- findById(id) -------------------------------------------------->    |
  |<---------------------------------- reconstituted Entity -------------|
  |                        |                        |                    |
  |-- entityA.equals(entityB) ---------------------->|                    |
  |                        |     compare ids only, ignore attributes      |
  |<--------------------------------- boolean -------|                    |
```

Two moments in this flow deserve emphasis. First, identity is assigned once,
either at construction (client-generated identifiers) or at the moment of
first persistence (database-generated identifiers), and never reassigned
afterward, dimension 8 covers exactly this fork. Second, every mutation is
routed through a method the Entity itself defines, never through a bare
setter reached from outside, because the Entity's whole reason for existing
as a distinct pattern rather than a struct is that it is the thing
responsible for keeping its own state valid across the sequence of changes
shown in the middle of the diagram.

## 8. Implementation variants

**Client-generated UUID identity, assigned at construction.** The Entity
generates or is given its identifier the moment it is constructed, before
persistence. This lets the identity be used immediately, in an event, in a
cross-aggregate reference, or in a UI, without waiting on a database round
trip. The trade-off is storage and index cost. a 128-bit random UUID as a
clustered primary key produces worse locality on write-heavy relational
tables than a dense sequential integer, a widely discussed operational
concern in database engineering circles and directly acknowledged in Entity
Framework Core's own documentation, which notes that non-composite numeric
and GUID primary keys get automatic value generation support, treating both
as distinct strategies with different generation behavior
(Microsoft Learn, "Keys - EF Core," verified 2026-08-02,
https://learn.microsoft.com/en-us/ef/core/modeling/keys).

**Database-generated sequential identity, assigned at first persistence.**
The identifier does not exist until the Entity is first saved, at which
point the database assigns the next value in a sequence or an auto-increment
column. This is dense and index-friendly but means the Entity is, briefly,
without an identity in memory, which forces either a nullable identity field
before save (awkward for equality, which needs SOME basis to compare unsaved
instances) or a temporary in-memory placeholder identity that gets replaced
on save. EF Core's documentation describes this explicitly, when a
database-generated key property is populated automatically, "EF will try to
generate a temporary value when the entity is added for tracking purposes,"
which is then "replaced by the value generated by the database" after
`SaveChanges` (Microsoft Learn, "Keys - EF Core," verified 2026-08-02,
https://learn.microsoft.com/en-us/ef/core/modeling/keys).

**Composite key identity.** The identity is not a single manufactured field
but a tuple of existing attributes that is jointly guaranteed unique, for
example a `(TenantId, OrderNumber)` pair in a multi-tenant system where
`OrderNumber` alone is only unique per tenant. EF Core supports this
directly through `HasKey` with multiple properties (Microsoft Learn, "Keys -
EF Core," verified 2026-08-02, https://learn.microsoft.com/en-us/ef/core/modeling/keys).
This variant avoids a manufactured surrogate key but couples identity
stability to the stability of the composite fields, if the business later
allows an order to move between tenants, the identity itself has to change,
which is a much more invasive migration than changing a mere attribute would
be.

**Natural key identity.** The identity is a value the business already
treats as unique, an ISBN, a national identification number, a VIN. This is
attractive because it needs no manufactured field at all, but it is fragile
the moment the "naturally unique" assumption turns out to be wrong in an
edge case the business had not anticipated, a book reissued with a
duplicated ISBN by a small publisher, a VIN collision across very old
vehicles. The general engineering guidance in this space, echoed across
enterprise data modeling practice, is to prefer a surrogate identity for
anything the domain did not itself define as a universal identifier, and to
treat natural keys as a searchable attribute rather than the record's
primary identity when there is any doubt about global uniqueness.

**Language-idiomatic identity encapsulation.** Rather than a bare `string`
or `int` identity field compared directly, many production codebases wrap
the identifier in its own small Value Object, `CustomerId`, `OrderId`, so
that the compiler prevents accidentally comparing a `CustomerId` to an
`OrderId` even when both happen to be backed by the same primitive type at
runtime. This is a widely used defensive pattern in strongly typed languages
and shows up as a recommended practice in domain modeling guides across
several language communities, though it adds a small amount of boilerplate
per identity type, a cost most teams accept once they have been bitten once
by an accidental cross-type comparison.

**ORM-managed identity, the most commonly encountered variant.** In JPA, the
`@Id` annotation on a field or property designates the primary key, and the
Java EE tutorial documentation states plainly that primary keys in entity
classes are covered as their own dedicated topic within the persistence
model, because the identity field is treated as structurally distinct from
every other persistent field on the class (Oracle, "The Java EE 7 Tutorial,
Introduction to Java Persistence API," verified 2026-08-02,
https://docs.oracle.com/javaee/7/tutorial/persistence-intro.htm). This is
the most common way working engineers first encounter an identity-bearing
domain object, and it is also the variant most prone to conflation with a
pure database row, the ORM's job is mapping, not enforcing business
invariants, so an `@Entity`-annotated class with public setters and no
behavior is a JPA entity but is not a DDD Entity in the sense this pattern
describes.

## 9. Known production uses

- **Jakarta Persistence (formerly JPA), the reference implementation of
  entity identity in the Java world.** The specification's `@Entity` and
  `@Id` annotations are the mechanism by which many production Java
  applications declare a class to have a stable, database-backed identity,
  distinct from its other persistent fields. The Java EE 7 Tutorial's
  chapter on introduction to the Java Persistence API documents this
  identity-first structure directly, with a dedicated subsection on primary
  keys in entity classes (Oracle, "The Java EE 7 Tutorial," verified
  2026-08-02, https://docs.oracle.com/javaee/7/tutorial/persistence-intro.htm).
- **Hibernate ORM**, the dominant JPA provider, implements this same
  identity discipline and publishes current user guides across every
  actively supported major version, from 6.x through the 8.0 line, each
  documenting entity identity mapping as a distinct first-class concern
  separate from ordinary attribute mapping (Hibernate.org, "Hibernate ORM
  Documentation," verified 2026-08-02, https://hibernate.org/orm/documentation/).
- **Entity Framework Core**, Microsoft's ORM for .NET, ships a dedicated
  "Keys" concept in its modeling documentation, describing how "a key serves
  as a unique identifier for each entity instance," with convention-based
  key detection, explicit `[Key]` and `HasKey` configuration, composite keys,
  and both database-generated and client-supplied value strategies
  (Microsoft Learn, "Keys - EF Core," verified 2026-08-02,
  https://learn.microsoft.com/en-us/ef/core/modeling/keys).
- **Axon Framework**, a CQRS and event-sourcing framework for the JVM built
  explicitly around DDD tactical patterns, implements Entity identity at the
  domain-modeling level rather than only at the persistence level. its
  Aggregate documentation describes `@AggregateIdentifier` for the root, and
  its multi-entity aggregate documentation describes `@EntityId` as
  "specifying the identifying field of an Entity," required "to be able to
  route a command (or event) message to the correct entity instance," with
  `@AggregateMember` marking the fields that hold child entities (AxonIQ,
  "Multi-Entity Aggregates," Axon Framework Reference 4.13, verified
  2026-08-02,
  https://docs.axoniq.io/axon-framework-reference/4.13/axon-framework-commands/modeling/multi-entity-aggregates/).
  This is a production framework used across event-sourced systems in
  finance and logistics, and it is notable as a case where Entity identity
  is enforced for message routing correctness, not merely for database
  row identification, a distinction dimension 16 returns to.

## 10. Consequences

Positive.

- **Correct equality for objects that continue across change.** Comparing
  by identity gets the "is this the same account" question right in every
  case, including the case that breaks value equality, an object whose
  every attribute has changed since you last saw it.
- **A natural home for invariant-protecting behavior.** Because the Entity
  owns the sequence of transitions across its own lifetime, it is the
  natural place to put the code that refuses an illegal transition, rather
  than scattering that validation across every caller.
- **Stable references across boundaries.** A stable identifier is exactly
  what an event, a cache key, a cross-service message, or a UI deep link
  needs to refer to "this one, specifically," independent of whatever its
  current attribute values happen to be.
- **Enables incremental persistence.** Because identity is stable and
  attributes are what changes, a persistence layer can diff and persist
  only the changed attributes, keyed by the unchanged identity, rather than
  replacing the whole record on every save.

Negative.

- **Mutability cost.** An Entity is usually mutable, which reintroduces
  every classic mutable-shared-state hazard, aliasing, unsynchronized
  concurrent mutation, action-at-a-distance bugs, that a Value Object's
  immutability avoids by construction.
- **Identity generation is a real design decision with real trade-offs.**
  Dimension 8's five variants are not equivalent, and picking one late,
  after the identity type is already threaded through a codebase, is an
  expensive migration.
- **Temptation to over-apply.** Once a team has the Entity vocabulary, there
  is a pull toward giving everything an identity "to be safe," which
  produces the opposite failure mode from the one the pattern fixes, Value
  Objects wrongly promoted to Entities lose their cheap, safe, by-value
  comparison and gain unnecessary lifecycle management overhead.
- **Equality that ignores attributes surprises naive code.** A developer
  unfamiliar with the convention who writes `if (customerA == customerB)`
  expecting an attribute comparison, and gets an identity comparison
  instead (or the reverse, expecting identity and getting Java's default
  reference equality because nobody overrode `equals`), produces a bug that
  is invisible until exactly the case dimension 2 describes.

## 11. Failure modes and misuse

**Symptom.** Two records that represent the same real-world thing get
created and both persisted, and the system silently treats them as
unrelated.
**Cause.** No stable identity was established before the first persistence,
or the identity generation strategy allowed two different code paths to
mint two different identifiers for what should have been one lookup-then-
update. A common concrete instance, an "upsert by natural key" endpoint that
does not actually check the natural key before creating a new row, so a
duplicate customer record gets created every time the same person submits
a form with the same email through a slightly different code path.
**Fix.** Enforce identity assignment or lookup in exactly one place, usually
a Factory or a Repository method dedicated to "find or create," and make it
the only construction path available to callers. Add a uniqueness
constraint at the persistence layer as a backstop, not as the primary
mechanism.

**Symptom.** Equality checks that used to work stop working after a
refactor, previously-equal-looking pairs of objects now compare unequal, or
vice versa, and nobody changed any comparison logic.
**Cause.** Someone regenerated or hand-wrote a language-default `equals`
and `hashCode` (or `==` in a language that supports operator overloading)
across all fields, unintentionally reverting an Entity from identity-based
equality back to attribute-based equality. This is especially common after
adopting a code generator, a record type, or an IDE "generate
equals/hashCode" action on a class that should have had a hand-written,
identity-only override.
**Fix.** Make the identity-only equality override explicit, tested, and
protected from regeneration, a small unit test asserting "two instances with
the same id but different attributes are equal" and "two instances with the
same attributes but different ids are not equal" catches this the moment it
regresses, and dimension 15 gives the concrete test shape.

**Symptom.** A collection deduplicates or a cache evicts entries that the
business considers distinct, or fails to deduplicate entries the business
considers the same.
**Cause.** The Entity's `hashCode` was implemented from all mutable fields
instead of only the immutable identity. If the Entity's attributes change
after it is placed into a hash-based collection, its hash bucket becomes
wrong and lookups silently fail to find it, or two Entities that share an
identity but currently differ in one attribute hash to different buckets
and both get retained where only one should be.
**Fix.** Hash on identity alone, and only ever hash on identity alone, for
exactly the same reason equality is identity-based, dimension 10's positive
consequence about stable references relies on this.

**Symptom.** An invalid state slips through into persisted data, an order
with a negative total, an account with a status that does not correspond to
any legal state in the business process.
**Cause.** The Entity exposed public setters or public mutable fields, so
some caller, often deep in an unrelated feature, mutated an attribute
directly rather than through a method the Entity itself defines, bypassing
whatever invariant that method would have checked.
**Fix.** Remove the setters. every state transition goes through a named
method (`ship()`, `applyDiscount(amount)`) that itself validates the
transition and raises a domain exception on an illegal one, per dimension 5.

**Symptom.** A single Entity's identity means two different things in two
different parts of the system, a customer's identity inside the billing
subsystem does not agree with the same customer's identity inside the
support ticketing subsystem, and reconciling them requires a lookup table
that itself drifts out of sync.
**Cause.** Identity was allowed to be minted independently in more than one
bounded context for what is conceptually the same real-world entity,
without ever establishing a translation or a single source of truth.
**Fix.** This is precisely the concern the Bounded Context and
Anti-Corruption Layer patterns exist to manage, see dimension 13, an
Entity's identity is only trustworthy for comparison within the bounded
context that owns it, and crossing a context boundary always requires an
explicit translation, never an assumption that "the same id number means
the same thing here too."

## 12. Trade-off matrix

| Concern | Entity | Value Object | Identity Field alone (persistence-only identity, no domain behavior) |
|---|---|---|---|
| Equality basis | Identity (id field) | All attributes | Identity, but with no behavior to protect invariants |
| Mutability | Usually mutable | Immutable by convention | Depends on the mapped class, often mutable with public setters |
| Safe to freely share and copy | No, aliasing matters | Yes, copies are interchangeable | No, but for the wrong reason, it is a data holder not a modeled concept |
| Encapsulates business invariants | Yes, via its own methods | Yes, at construction only | No, invariant enforcement lives elsewhere or nowhere |
| Natural cache/hash key | Yes, on identity | Yes, on full value | Yes, on identity, but the class carries no domain meaning beyond storage |
| Cost to introduce | One identity field plus identity-only equality override | None beyond the class itself | One id column plus ORM mapping, cheapest to add, easiest to misuse |
| Best fit | Order, Customer, Account, Shipment | Money, DateRange, Address (as an attribute), EmailAddress | A pure ORM-mapped row with no domain logic, an anti-pattern when mistaken for a real DDD Entity |

## 13. Related and incompatible patterns

**Value Object.** The direct complement. every Entity's non-identity
attributes are frequently modeled as Value Objects, and the whole
classification only works because the two are defined in opposition to each
other, identity equality versus value equality. A codebase that has Entities
but never introduces Value Objects usually ends up with primitive-typed
attributes (a bare `string` for an email, a bare `decimal` for money) that
lose the validation and behavior a Value Object would have given them for
free.

**Aggregate.** An Entity is very often, though not always, a member of an
Aggregate, and exactly one Entity within an Aggregate is designated its
root. The Aggregate is the transactional and referential consistency
boundary, external code holds a reference only to the root Entity's
identity, and reaches any internal Entity or Value Object only through the
root. Evans's classification and the Aggregate pattern were introduced
together in the same book, and treating Entity in isolation from Aggregate
is common in shallow summaries but is a genuine loss, the internal-Entity
identity scoping described in dimension 6's diagram only makes sense once
Aggregate is understood.

**Identity Field.** Martin Fowler's *Patterns of Enterprise Application
Architecture* pattern for the persistence mechanism, saving a database
identifier on an in-memory object to keep it correlated with its database
row (Martin Fowler, *Patterns of Enterprise Application Architecture*
catalog, verified 2026-08-02,
https://martinfowler.com/eaaCatalog/identityField.html). Identity Field is
the implementation mechanism an ORM typically uses to give an Entity its
persisted identity, it is a narrower, persistence-focused pattern that
Entity relies on but is not equivalent to, an Entity can exist and be
compared by identity before it has ever been persisted, and a plain
Identity-Field-bearing class with no protected invariants is not, by
itself, a well-modeled DDD Entity.

**Repository.** Provides the collection-like interface, typically keyed by
an Entity's identity, through which Entities are looked up and persisted,
abstracting away the specific storage mechanism. A Repository's method
signatures (`findById`, `save`) presuppose that the things it manages have
a stable identity, which is exactly the Entity's defining property.

**Factory.** Where constructing a valid Entity requires enforcing
invariants across several fields at once, or generating the identity
itself, a Factory centralizes that construction logic rather than letting
every call site duplicate it, closing the gap dimension 11's first failure
mode describes.

**Bounded Context and Anti-Corruption Layer.** These patterns govern what
happens when an Entity's identity needs to be referenced, or its concept
translated, across a boundary between two different models of the domain.
An Entity's identity is only stable and safe to compare within the bounded
context that owns it, dimension 11's last failure mode is exactly what
happens when this is forgotten.

**Incompatible with.** Nothing in this pattern family is structurally
incompatible with Entity in the sense of two patterns that cannot coexist.
the closest thing to a genuine tension is applying Entity to a concept that
is properly a Value Object (dimension 4's non-applicability list), which is
a misapplication rather than an incompatibility between two valid patterns.

## 14. Refactoring path in and out

**Introducing Entity into code that currently lacks it.** The starting
point is usually a data class or a bare struct with public mutable fields
and no identity discipline, compared, if at all, by whatever the language's
default equality happens to be. The path in, step by step.

1. Identify a stable identifier for the concept, or introduce one if none
   exists (dimension 8 covers the choice of strategy). Add it as a field
   that is set once, at construction or at first persistence, and never
   reassigned.
2. Override equality and hashing to be based on that identifier alone,
   comparing the runtime type as well as the identifier so that two
   different Entity types that happen to share an identifier value are
   never mistaken for each other.
3. Audit every public mutable field on the class. for each one, replace
   direct external mutation with a named method that expresses the
   business intent of the change (`raiseCreditLimit`, not `setCreditLimit`)
   and add the invariant check that method should have been enforcing all
   along. This step is the one most often skipped under time pressure, and
   skipping it leaves an object with correct equality but no actual
   protection of its invariants, which is only half the pattern.
4. Where the class held Value-Object-shaped data inline as primitives (a
   bare string used as an email, a bare decimal used as money), extract
   those into real Value Objects, this is the companion refactor described
   in the Value Object entry and the two refactors are usually done
   together, since Entity behavior methods (step 3) are much easier to
   write correctly once the data they operate on is already validated at
   its own boundary.
5. Add the equality regression test from dimension 15 before considering
   the refactor complete, so a future well-intentioned "generate equals"
   action cannot silently revert step 2.

**Removing Entity when it no longer earns its place.** This happens less
often in practice than introducing it, but it is a real refactor when a
concept that was originally modeled with identity turns out, after the
domain understanding matures, to genuinely be a Value Object, for example a
`ShippingOption` that was originally created once per order and referenced
by id, but is discovered to actually be fully described by its attributes
(carrier, speed, price) with no continuity across orders worth tracking.

1. Confirm that no code anywhere compares two instances by identity and
   expects a different answer than comparing by value would give, this is
   the safety check before removing identity-based equality.
2. Confirm no external reference, cache key, event payload, or persisted
   foreign key, depends on the object's identifier surviving independently
   of its attributes.
3. Remove the identifier field, or demote it to an ordinary attribute if
   the storage layer still needs one for its own reasons.
4. Replace identity-based equality and hashing with attribute-based
   equality and hashing, and make the class immutable if it is not already,
   completing the transition to a genuine Value Object.

## 15. Testing and verification

What becomes easy to test because of this pattern. behavior methods on an
Entity are ordinary methods with a before-state and an after-state, and
testing them is standard unit testing, construct an Entity in a known state,
invoke a behavior method, assert the resulting state, and assert that an
illegal invocation raises the expected domain exception rather than
silently succeeding or silently corrupting state. Because the invariant
checks live inside the Entity itself rather than scattered across callers,
one test suite against the Entity's own methods gives coverage that would
otherwise require testing every caller independently.

What becomes harder because of this pattern. testing equality correctly
requires deliberately constructing pairs of instances that isolate the two
directions of the property, same identity with different attributes must
compare equal, different identity with identical attributes must compare
unequal, and both directions must be asserted, because a suite that only
ever constructs Entities with both matching identity and matching
attributes never actually exercises the identity-based equality logic at
all and would pass even if `equals` had silently reverted to comparing by
attribute.

The concrete test doubles and techniques that apply. an in-memory fake
Repository, backed by a plain dictionary or map keyed by the Entity's
identity type, is the standard test double for anything that depends on
Repository lookups, and it is unusually cheap to build correctly precisely
because a Repository's contract is already keyed by identity. For an Entity
whose construction requires a Factory that generates identity, inject a
deterministic identity generator (a counter, or a fixed sequence of UUIDs)
in tests rather than a random one, so that assertions comparing expected
identities to actual ones are reproducible. For Entities inside an
Aggregate, test invariant enforcement at the Aggregate root's public
methods, never by reaching into an internal Entity directly and calling a
method on it in isolation, because that bypasses exactly the boundary the
Aggregate pattern exists to enforce, and a test that does so can pass while
the actual public API of the Aggregate still allows the same invariant
violation through a different path.

## 16. Observability signals

What to log or trace. every state-transition method invocation on an
Entity is a natural point for a domain event, or at minimum a structured
log line, carrying the Entity's stable identity, the transition attempted,
and whether it succeeded or was rejected for violating an invariant. This
is the same identity discipline dimension 9's Axon Framework example
depends on for message routing, `@EntityId` exists specifically so that an
incoming command or event can be routed to the correct entity instance by
identity (AxonIQ, "Multi-Entity Aggregates," verified 2026-08-02,
https://docs.axoniq.io/axon-framework-reference/4.13/axon-framework-commands/modeling/multi-entity-aggregates/),
which means the identity is not only a modeling concern, it is a concrete
runtime routing key that shows up directly in trace spans and message
headers in an event-sourced system.

What a healthy instance looks like on a dashboard. a low, steady rate of
rejected transitions relative to total transitions attempted, because a
healthy system mostly proposes legal transitions, and a healthy Entity's
invariant checks reject the rare illegal one cleanly rather than the
process crashing or the data silently corrupting. A count of distinct
identities created per unit time that matches the expected business rate
(new customers per day, new orders per hour) is a useful sanity signal,
because dimension 11's first failure mode, duplicate identity creation for
the same real-world thing, shows up as an unexplained spike in that count
relative to the actual number of distinct real-world events.

What a failing instance looks like. a rising rate of rejected transitions
that does not correspond to any known business change is a sign that
either a caller upstream is proposing illegal transitions in volume
(a bug in a calling service) or that the invariant logic itself has a
false-positive bug newly introduced by a recent deploy. A cache or
deduplication layer whose hit rate drops sharply after a deploy, with no
change in traffic pattern, is the operational symptom of dimension 11's
third failure mode, hashing on mutable attributes instead of stable
identity.

## 17. Security and privacy implications

An Entity's stable identifier is frequently the exact value used across
system boundaries, in URLs, in API payloads, in log lines, and it is worth
being deliberate about what kind of identifier that is. A dense, sequential,
database-generated identity (the earliest variant in dimension 8) leaks
information through its ordering, an attacker who observes their own
customer id can infer roughly how many customers exist and can enumerate
neighboring ids to probe for records that were not meant to be reachable by
guessing, a well-known class of vulnerability generally described as
insecure direct object reference. A client-generated UUID identity does not
have this enumeration property, because the identifier space is sparse and
effectively unguessable, which is a genuine security advantage of that
variant beyond its purely architectural trade-offs in dimension 8, though it
does not by itself replace proper authorization checks, an unguessable
identifier is not a substitute for verifying the requester is actually
allowed to access the specific Entity that identifier resolves to.

Because an Entity is typically mutable and long-lived, it is also typically
the object that accumulates personal data over its lifetime, an order
Entity accumulating shipping addresses, a customer Entity accumulating
contact history, and the stable identity is exactly what makes correlating
that accumulated data across separate systems both useful for legitimate
business purposes and risky if the identifier or the data it correlates
leaks. Where a domain model has to satisfy data protection obligations
(erasure requests, data minimization), the Entity's identity is what has to
be handled with particular care, an erasure request is a request to remove
or anonymize the attributes attached to a specific identity while, in some
regulatory regimes, still retaining the fact that the identity itself
existed for other legal or auditing reasons, which is a nuance that plain
value-object deletion does not carry.

## 18. References

1. Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*, Addison-Wesley, 2003. Original source for the Entity, Value
   Object, and Service classification.
2. Wikipedia, "Domain-driven design," verified 2026-08-02,
   https://en.wikipedia.org/wiki/Domain-driven_design. Secondary summary of
   Evans's Entity definition and the airline seat example.
3. Martin Fowler, "EvansClassification," verified 2026-08-02,
   https://martinfowler.com/bliki/EvansClassification.html. Independent
   restatement of Evans's three-way domain object classification.
4. Martin Fowler, *Patterns of Enterprise Application Architecture*,
   Addison-Wesley, 2003, catalog entry "Identity Field," verified
   2026-08-02, https://martinfowler.com/eaaCatalog/identityField.html.
   Source for the persistence-facing Identity Field pattern this entry
   distinguishes from the domain-modeling Entity concept.
5. Oracle, "The Java EE 7 Tutorial, Chapter 37, Introduction to the Java
   Persistence API," verified 2026-08-02,
   https://docs.oracle.com/javaee/7/tutorial/persistence-intro.htm. Source
   for JPA's `@Entity` and primary-key-focused identity model.
6. Hibernate.org, "Hibernate ORM Documentation," verified 2026-08-02,
   https://hibernate.org/orm/documentation/. Source confirming current,
   actively maintained user guides covering entity identity mapping across
   Hibernate's supported major versions.
7. Microsoft Learn, "Keys - EF Core," verified 2026-08-02,
   https://learn.microsoft.com/en-us/ef/core/modeling/keys. Source for
   Entity Framework Core's key configuration, composite keys, and both
   database-generated and client-supplied identity value strategies.
8. AxonIQ, "Multi-Entity Aggregates," Axon Framework Reference 4.13,
   verified 2026-08-02,
   https://docs.axoniq.io/axon-framework-reference/4.13/axon-framework-commands/modeling/multi-entity-aggregates/.
   Source for `@EntityId` and `@AggregateMember`, entity identity used
   directly for command and event message routing in a production
   event-sourcing framework.

## Code examples

Three languages, chosen because each is genuinely idiomatic for expressing
identity-based equality with a compiler that can enforce the contract, all
three compiled or ran without error.

### TypeScript

```typescript
abstract class Entity<Id> {
  protected constructor(private readonly _id: Id) {}

  get id(): Id {
    return this._id;
  }

  equals(other: Entity<Id> | null | undefined): boolean {
    if (other === null || other === undefined) return false;
    if (this === other) return true;
    if (this.constructor !== other.constructor) return false;
    return this._id === other._id;
  }
}

class EmailAddress {
  constructor(readonly address: string) {}

  equals(other: EmailAddress): boolean {
    return this.address === other.address;
  }
}

class Customer extends Entity<string> {
  private _email: EmailAddress;
  private _creditLimitCents: number;

  constructor(id: string, email: EmailAddress, creditLimitCents: number) {
    super(id);
    this._email = email;
    this._creditLimitCents = creditLimitCents;
  }

  get email(): EmailAddress {
    return this._email;
  }

  get creditLimitCents(): number {
    return this._creditLimitCents;
  }

  raiseCreditLimit(additionalCents: number): void {
    if (additionalCents < 0) {
      throw new Error("credit limit adjustment must be non negative");
    }
    this._creditLimitCents += additionalCents;
  }

  changeEmail(newEmail: EmailAddress): void {
    this._email = newEmail;
  }
}

const a = new Customer("cust-1", new EmailAddress("a@example.com"), 5000);
const b = new Customer("cust-1", new EmailAddress("different@example.com"), 99900);
const c = new Customer("cust-2", new EmailAddress("a@example.com"), 5000);

if (!a.equals(b)) throw new Error("same identity must be equal despite differing attributes");
if (a.equals(c)) throw new Error("different identity must not be equal despite matching attributes");
```

Compiled with `tsc --strict --target es2020` and run with `node`, both
assertions pass, `a` and `b` share an identity and are equal despite `b`
having a different email and credit limit, `a` and `c` share attribute
values but differ in identity and are not equal.

### Python

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


class Entity:
    def __init__(self, entity_id: str) -> None:
        self._id = entity_id

    @property
    def id(self) -> str:
        return self._id

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        if type(self) is not type(other):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        return hash((type(self), self._id))


@dataclass(frozen=True)
class EmailAddress:
    address: str


class Customer(Entity):
    def __init__(self, customer_id: str, email: EmailAddress, credit_limit_cents: int) -> None:
        super().__init__(customer_id)
        self.email = email
        self.credit_limit_cents = credit_limit_cents

    def raise_credit_limit(self, additional_cents: int) -> None:
        if additional_cents < 0:
            raise ValueError("credit limit adjustment must be non negative")
        self.credit_limit_cents += additional_cents


a = Customer("cust-1", EmailAddress("a@example.com"), 5000)
b = Customer("cust-1", EmailAddress("different@example.com"), 99900)
c = Customer("cust-2", EmailAddress("a@example.com"), 5000)

assert a == b, "same identity means equal, even though attributes differ"
assert a != c, "different identity means not equal, even with matching attributes"
```

Run with `python3`, both assertions pass. Note `__hash__` is derived from
type and identity only, never from `email` or `credit_limit_cents`, which is
what keeps a `Customer` placed in a `set` or used as a dict key locatable
after its mutable attributes change.

### Go

```go
package main

import "errors"

type EntityID string

type EmailAddress struct {
	Address string
}

func (e EmailAddress) Equals(other EmailAddress) bool {
	return e.Address == other.Address
}

type Customer struct {
	id              EntityID
	email           EmailAddress
	creditLimitCent int
}

func NewCustomer(id EntityID, email EmailAddress, creditLimitCent int) *Customer {
	return &Customer{id: id, email: email, creditLimitCent: creditLimitCent}
}

func (c *Customer) Equals(other *Customer) bool {
	if other == nil {
		return false
	}
	return c.id == other.id
}

func (c *Customer) RaiseCreditLimit(additionalCent int) error {
	if additionalCent < 0 {
		return errors.New("credit limit adjustment must be non negative")
	}
	c.creditLimitCent += additionalCent
	return nil
}

func main() {
	a := NewCustomer("cust-1", EmailAddress{"a@example.com"}, 5000)
	b := NewCustomer("cust-1", EmailAddress{"different@example.com"}, 99900)
	c := NewCustomer("cust-2", EmailAddress{"a@example.com"}, 5000)

	if !a.Equals(b) {
		panic("same identity must be equal despite differing attributes")
	}
	if a.Equals(c) {
		panic("different identity must not be equal despite matching attributes")
	}
}
```

Run with `go run`, both checks pass. Go has no operator overloading, so
`Equals` is a plain method rather than a language-level `==` override,
which is the idiomatic Go shape for this pattern, `==` on the pointer type
would compare pointer identity, not the domain identifier, and is
deliberately not used here to avoid exactly that confusion.

Java, Rust, and Swift are omitted from the running samples in this entry.
the pattern is equally idiomatic in all three, a Java class with a
hand-written `equals`/`hashCode` overriding Lombok or IDE generation, a
Rust struct implementing `PartialEq` by hand on the id field rather than
deriving it across all fields, and a Swift struct or class conforming to
`Equatable` with a hand-written `==` on the identifier, but three working,
verified samples across three genuinely different type system styles
(structural TypeScript classes, Python dunder methods, Go's method-based
equality with no operator overloading) already demonstrate the pattern's
core mechanism without repeating the same idea a fourth and fifth time.
