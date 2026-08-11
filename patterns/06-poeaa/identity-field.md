---
name: Identity Field
slug: identity-field
family: 06-poeaa
category: Object-Relational Structural Pattern
aliases: [Surrogate Key Field, Primary Key Property, ID Field]
first_described: "Fowler 2002"
maturity: canonical
related: [identity-map, unit-of-work, foreign-key-mapping, metadata-mapping, repository, lazy-load]
incompatible_with: []
verified: 2026-08-11
---

# Identity Field

## 1. Name, aliases, and lineage

The canonical name is Identity Field. It was catalogued by Martin Fowler in
*Patterns of Enterprise Application Architecture*, Addison-Wesley, 2002,
chapter 12, Object-Relational Structural Patterns, in the section titled
Identity Field. Fowler states the intent as saving a database ID field in an
object to maintain identity between an in-memory object and a database row
([Martin Fowler, "Identity Field"](https://martinfowler.com/eaaCatalog/identityField.html),
verified 2026-08-11).

The pattern has no earlier named ancestor in the Gang of Four catalog because
it addresses a problem that only exists at the boundary between an
object-oriented in-memory model and a relational store, a boundary the GoF
book does not cover. Fowler's own framing places it beside Identity Map and
Foreign Key Mapping as one of the object-relational patterns needed once an
application persists domain objects into tables.

In day-to-day practice the pattern goes by several names depending on which
community is talking about it.

- **Surrogate Key Field.** The database-design term for the same field, used
  when discussing the column itself rather than the object property that
  mirrors it. A surrogate key has no business meaning, contrasted with a
  natural key drawn from the domain (an ISBN, a national ID number, an email
  address).
- **Primary Key Property.** The ORM-framework term. Hibernate calls the
  Java property annotated `@Id` the identifier property, and its user guide
  devotes a full section to identifier configuration ([Hibernate ORM 6.5 User
  Guide, section 3.7, "Identifiers"](https://docs.hibernate.org/orm/6.5/userguide/html_single/Hibernate_User_Guide.html),
  verified 2026-08-11).
- **ID Field.** The plain-English shorthand used across most web-framework
  tutorials, and this is the name most working engineers reach for first.

All three names describe the identical structural fact, that an object
carries a field whose sole job is to hold the value that uniquely identifies
its row in a relational table, so the object can be found, updated, and
reconciled against that row on every later interaction with the database.

## 2. Problem and context

An in-memory object system and a relational database use two different, and
incompatible, notions of identity.

In an object system, identity is usually reference identity. Two variables
point at literally the same object in memory, or they do not, and a language
runtime settles the question for free (`===` in JavaScript on object
references, `is` in Python, reference equality in Java before `equals` is
overridden). Once that object is written to disk and read back later in a new
process, reference identity is gone. The new object read from the row is a
different allocation, at a different address, in a possibly different
process on a possibly different machine.

A relational table settles identity a completely different way. Every row has
a primary key, a column or set of columns whose value is guaranteed unique
within the table by a database-enforced constraint. Two rows are the same row
if and only if their primary key values match. The database has no concept of
object identity at all, it only ever compares column values.

The problem Identity Field solves sits exactly at this seam. When an
application loads a row into an object, updates the object over time, and
must eventually write the changes back to the correct row, or must load the
same row a second time and recognise it is the same logical entity it already
has in memory, the application needs some value it can carry inside the
object that maps unambiguously back to the primary key of the row. Without
that value, an update has nothing to target in its `WHERE` clause beyond
guessing from business fields, which is fragile the moment two rows share the
same business-field values, and impossible the moment those values change
between load and save.

The context in which this problem arises is any application with a mapping
layer between domain objects and a relational schema, whether that mapping is
hand-written data access code, a full ORM such as Hibernate or Entity
Framework, or a lighter data mapper. The pattern is irrelevant to
applications that never persist objects to rows (a pure in-memory
simulation, a stateless transformation pipeline) and irrelevant to
applications that talk to a document store or key-value store where the
store's own native key already plays this role without any translation.

## 3. Forces

The pattern balances a small set of forces, and the balance it strikes is
close to non-negotiable once you accept it is needed at all.

**Correctness of identity resolution against convenience of a natural key.**
Using a business field (an email address, a product SKU) as the identity
value avoids adding a field that has no domain meaning, but business fields
change. A person's email address gets edited, a SKU gets renumbered during a
catalog migration. A stable value generated once and never touched again
removes that fragility at the cost of one column that means nothing to a
domain expert reading the schema.

**Simplicity of implementation against fidelity to encapsulation.** The
straightforward implementation exposes the ID field as a plain public
property on the domain object, which is the shape every mainstream ORM
assumes and generates. That directly punches a hole in encapsulation,
because now every object in the domain model advertises a database-shaped
concept. Fowler is explicit that this is an accepted trade rather than an
oversight, treating the identity field as one of the visible places
persistence technology leaks into the domain layer
([Fowler, PoEAA, "Identity Field"](https://martinfowler.com/eaaCatalog/identityField.html),
verified 2026-08-11).

**Local uniqueness against global uniqueness.** A per-table auto-increment
integer is cheap, small, and index-friendly, but it is only unique within its
own table, so a value of `42` says nothing across tables and cannot double as
a globally addressable reference. A generated UUID is unique everywhere at
the cost of a wider, less index-friendly value and, for random (v4) UUIDs, a
real cost in B-tree index fragmentation under high insert volume, a cost
documented at length in the PostgreSQL and MySQL communities and one of the
reasons time-ordered UUID variants (UUIDv7) exist.

**Assignment timing against object usability before persistence.** A
database-assigned identity value (an `IDENTITY` column, a sequence-backed
auto-increment) is not known until the row is actually inserted, which means
a freshly-constructed, not-yet-saved object has no identity value yet. Code
that reasons about the object's identity, equality, or hashing before it is
saved must either tolerate a null or sentinel identity, or the pattern must
be paired with client-side generation (a UUID minted in the constructor)
which sacrifices some of the compactness and ordering of a database sequence
in exchange for having a stable identity from the moment of construction.

## 4. Applicability and non-applicability

Reach for Identity Field when the situation matches any of these.

- The application maps domain objects to relational rows and needs to save
  changes back to the exact row an object was loaded from.
- The application needs to detect that two separately loaded objects
  represent the same underlying row, the precondition that Identity Map
  relies on to avoid loading duplicate in-memory copies of one row.
- The mapping layer needs a stable, cheap value to use in foreign keys when
  writing associated rows.
- The team is using, or building, an ORM or data mapper, where the pattern
  is effectively assumed by the tooling. Hibernate requires every managed
  entity to declare an identifier property before it will map the class at
  all ([Hibernate ORM 6.5 User Guide, section 3.7](https://docs.hibernate.org/orm/6.5/userguide/html_single/Hibernate_User_Guide.html),
  verified 2026-08-11).

Do NOT reach for Identity Field, or reach for a variant of it, in these
situations.

- The persistence target has no relational primary-key concept at all, such
  as an append-only event log where identity is derived from position or a
  content hash rather than an assigned key. Forcing a surrogate ID field
  onto an event record adds a column nobody needs and invites someone to
  mutate by ID later, which contradicts the append-only design.
- The object is a genuine Value Object, per Fowler's own distinction in the
  same chapter (PoEAA, chapter 12, the discussion around Embedded Value). A
  value object, an amount of money, a date range, an address, is defined
  entirely by the equality of its constituent fields and has no independent
  lifecycle. Giving it an Identity Field turns it into an Entity by
  definition, and now two value objects with identical fields can be
  treated as different, which breaks the substitutability a value object is
  supposed to guarantee.
- The domain already has a stable, immutable, genuinely unique natural key
  and the team has deliberately decided to use it as the primary key (an
  ISO country code table, a currency code table). This is a legitimate,
  narrower alternative called a Natural Key strategy, and mixing it with a
  surrogate Identity Field on the same table without a reason adds a column
  nobody queries by.
- The object is transient by design and never crosses a save boundary, a
  DTO built purely to shuttle data across a network call, a builder object
  used only during construction, a pure calculation result. Adding an
  identity field to these forces every consumer to reason about an ID that
  is never actually populated with a value anyone reads.
- The system is single-table-per-tenant multi-tenant SaaS with tenant
  isolation enforced at the row level and the team wants IDs that are
  globally unique across tenants for cache-key or URL-safety reasons. A
  bare auto-increment Identity Field is the wrong choice there, not because
  the pattern itself is wrong, but because the naive local-uniqueness
  implementation of it is. The fix is still Identity Field, backed instead
  by a UUID or a Snowflake-style generator rather than a sequence.

## 5. Structure

Identity Field has three participants.

- **Domain Object (or Entity).** The in-memory class that represents a
  business concept, a `Customer`, an `Order`, a `Product`. It carries the
  Identity Field as one of its properties, conventionally named `id`,
  `identifier`, or a suffixed form such as `customerId` when the object is
  embedded inside a larger aggregate and the plain name would be ambiguous.
- **Identity Field.** The property itself. It holds a value drawn from a
  small, well-understood set of types, an integer or long, a string-encoded
  UUID, or occasionally a compound key represented as a small value object
  when the underlying table has a composite primary key. It is set exactly
  once per logical row, either by the database at insert time or by the
  application before insert, and after that it is treated as effectively
  immutable for the life of the object.
- **Database Row and Primary Key column.** The relational counterpart. One
  or more columns constrained `PRIMARY KEY`, enforced unique and non-null by
  the database engine, and typically backed by a clustered or unique index
  so lookups by that value are fast.

A fourth, optional participant appears whenever the ID is database-assigned
rather than client-assigned.

- **Key Generator.** The mechanism that produces the next value, a sequence
  object in PostgreSQL, an `IDENTITY` column in SQL Server, an
  `AUTO_INCREMENT` column in MySQL, or a client-side generator such as a
  UUID library or a Snowflake-style distributed ID service.

## 6. ASCII structure diagram

```
+-----------------------+          maps to           +----------------------+
|     Domain Object     |  <----------------------->  |    Database Table    |
|  (e.g. Customer)      |                             |   (e.g. customers)   |
+-----------------------+                             +----------------------+
| - id: Long            |  <== Identity Field ==>     | id     BIGINT   PK   |
| - name: String        |                             | name   VARCHAR       |
| - email: String       |                             | email  VARCHAR       |
+-----------------------+                             +----------------------+
        ^                                                       ^
        |  assigned by                                          |  enforced by
        |                                                       |
+-----------------------+                             +----------------------+
|    Key Generator       |  --- produces next value -> |  PRIMARY KEY and     |
|  (sequence, UUID gen,  |                             |  UNIQUE constraint   |
|   IDENTITY column)     |                             +----------------------+
+-----------------------+
```

## 7. Dynamics

The two dynamics that matter are the assignment of an identity on first
save, and the use of that identity on every subsequent load or update.

Assignment on first insert, database-generated case.

```
Application          Domain Object          Mapper              Database
    |                      |                    |                    |
    | new Customer()       |                    |                    |
    |--------------------->|                    |                    |
    |   id = null          |                    |                    |
    |                      |                    |                    |
    | save(customer)       |                    |                    |
    |----------------------------------------->  |                    |
    |                      |                    | INSERT ... RETURNING id
    |                      |                    |------------------->|
    |                      |                    |   id = 42          |
    |                      |                    |<-------------------|
    |                      |   customer.id = 42 |                    |
    |                      |<-------------------|                    |
    |  customer.id == 42   |                    |                    |
    |<-----------------------------------------------------------------
```

Reload and update, using the identity to target the correct row.

```
Application          Mapper                Database
    |                    |                      |
    | load(id=42)        |                      |
    |------------------->|                      |
    |                    | SELECT * WHERE id=42 |
    |                    |--------------------->|
    |                    |   row               |
    |                    |<---------------------|
    |  customer(id=42)   |                      |
    |<--------------------|                     |
    |                    |                      |
    | customer.name = "New Name"                |
    | save(customer)     |                      |
    |------------------->|                      |
    |                    | UPDATE ... WHERE id=42
    |                    |--------------------->|
```

The critical property both flows depend on is that `id` never changes for the
lifetime of the domain object once it is assigned, so the second flow's
`WHERE id=42` always targets the correct, single row.

## 8. Implementation variants

**Database-assigned surrogate integer.** The most common shape in practice.
The column is declared `AUTO_INCREMENT` (MySQL), `IDENTITY` (SQL Server), or
backed by a `SERIAL` or explicit sequence (PostgreSQL). The object's field
starts unset (`null`, `nil`, `Optional.empty()`, or a sentinel such as `0`
depending on the language's typing conventions) and is populated by the
mapper immediately after the insert returns the generated value. This is the
Rails ActiveRecord and Django default, both of which auto-create an
integer-typed `id` primary key column unless the developer overrides it
([Ruby on Rails Guides, "Active Record Basics"](https://guides.rubyonrails.org/active_record_basics.html),
verified 2026-08-11; [Django documentation, "Automatic primary key fields"](https://docs.djangoproject.com/en/5.2/topics/db/models/#automatic-primary-key-fields),
verified 2026-08-11).

**Client-generated UUID.** The identifier is minted in application code, in
the constructor or in a factory, before the object ever touches the
database. This removes the "identity is unknown until insert" force
entirely, at the cost of a wider column, generally worse index locality for
the fully random UUIDv4 variant, and a value that carries no ordering
information. The time-ordered UUIDv7 variant, standardized in RFC 9562
(Internet Engineering Task Force, RFC 9562, "Universally Unique
IDentifiers, UUIDs", May 2024), narrows this gap by embedding a millisecond
timestamp in the high bits so values sort close to insertion order while
remaining globally unique.

**Compound or composite key wrapped as a small value object.** When the
underlying table's primary key is genuinely multi-column (an `order_id`
plus a `line_number` for order-line rows), the idiomatic shape is a small,
immutable value type that bundles the columns and implements structural
equality, rather than exposing two loose fields on the entity. Java
persistence frameworks formalize this with `@EmbeddedId` or `@IdClass`
([Hibernate ORM 6.5 User Guide, section 3.7.2, "Composite identifiers"](https://docs.hibernate.org/orm/6.5/userguide/html_single/Hibernate_User_Guide.html),
verified 2026-08-11).

**Externally-assigned natural-looking identifier.** Some systems use a
non-sequential, externally recognisable identifier as the field's value, a
Stripe-style `cus_1MqXxxxxxxxx` prefixed opaque string, or a Snowflake ID
in distributed systems descended from Twitter's original design. These are
still surrogate keys in the Identity Field sense, they carry no business
meaning a user is meant to reason about, they are simply formatted to be
recognisable, sortable, or namespaced by entity type at a glance.

**Framework-generated, developer-invisible field.** Modern ORMs
increasingly default this pattern into existence without the developer
writing it. .NET's Entity Framework Core applies key discovery by
convention, treating a property literally named `Id` or `<TypeName>Id` as
the primary key unless told otherwise ([Microsoft Learn, "Keys, Entity
Framework Core"](https://learn.microsoft.com/en-us/ef/core/modeling/keys)).
The developer writes a plain class, the framework infers the Identity
Field structurally.

## 9. Known production uses

- **Ruby on Rails ActiveRecord.** Every model backed by a migration-created
  table gets an integer `id` primary key by default, described directly in
  the framework's own guide as the standard Active Record convention
  ([Ruby on Rails Guides, "Active Record Basics", section "Convention over
  Configuration in Active Record"](https://guides.rubyonrails.org/active_record_basics.html),
  verified 2026-08-11).
- **Django ORM.** Every model without an explicit `primary_key=True` field
  is given a `BigAutoField` named `id`, and the documentation states
  plainly that exactly one field must have `primary_key=True`, whether that
  is the automatic one or a developer-declared one
  ([Django documentation, "Automatic primary key fields"](https://docs.djangoproject.com/en/5.2/topics/db/models/#automatic-primary-key-fields),
  verified 2026-08-11).
- **Hibernate ORM.** No entity can be mapped without declaring an
  identifier property, either `@Id` on a simple field or
  `@EmbeddedId`/`@IdClass` for a composite one, and Hibernate's own user
  guide devotes an entire section, 3.7, to the identifier configurations
  it supports ([Hibernate ORM 6.5 User Guide](https://docs.hibernate.org/orm/6.5/userguide/html_single/Hibernate_User_Guide.html),
  verified 2026-08-11).
- **Microsoft Entity Framework Core.** Ships an explicit key-by-convention
  algorithm that looks for a property named `Id` or `<EntityName>Id` and
  designates it the primary key automatically, with documented rules for
  what happens when no such property exists
  ([Microsoft Learn, "Keys, Entity Framework Core"](https://learn.microsoft.com/en-us/ef/core/modeling/keys)).
- **Stripe API objects.** Every resource returned by the Stripe API
  carries an `id` field, a prefixed opaque string (`cus_...` for
  customers, `ch_...` for charges), which the Stripe API reference
  documents as the unique identifier used in all subsequent lookups and
  mutations of that object ([Stripe API Reference](https://stripe.com/docs/api),
  the `id` field description present on every resource schema).

## 10. Consequences

Positive consequences of the pattern.

- Gives the mapping layer a single, unambiguous value to target for update
  and delete statements, eliminating the fragility of matching rows by
  business-field content.
- Enables Identity Map, because two loads of the same row can be
  recognised as the same logical entity by comparing Identity Field
  values, which is the precondition Fowler states for that pattern
  (PoEAA, chapter 11, Object-Relational Behavioral Patterns, Identity Map).
- Provides a stable, compact value to use in foreign keys, keeping
  associated-row references small and index-friendly compared to
  embedding a full natural key in every child row.
- Decouples identity from mutable business data, so renaming a customer or
  correcting an email address never invalidates a reference already held
  elsewhere in the system.

Negative consequences of the pattern.

- Leaks a persistence concept into the domain model. Every entity now
  visibly carries a field whose only purpose is database plumbing, which
  weakens the argument that the domain model is persistence-ignorant.
- Introduces a null-or-unset window for newly constructed, not-yet-saved
  objects when the ID is database-assigned, forcing every piece of code
  that compares or hashes entities to handle that state correctly.
- A poorly chosen generation strategy, random UUIDv4 as a clustered or
  primary index key on a high-write table, actively degrades write and
  range-scan performance due to index fragmentation, a widely documented
  cost in PostgreSQL and MySQL B-tree index literature.
- Values carry no meaning to a human reading raw data, which slows down
  manual debugging against production data unless the team also maintains
  readable natural-key indexes.

## 11. Failure modes and misuse

**Symptom.** Two objects that represent the same logical entity are
treated as different, duplicate rows appear after what looked like an
update. **Cause.** The Identity Field is compared by value equality using
the language's default `equals` or `==` before it has actually been
assigned (both sides still hold the unset or null sentinel), so two
distinct in-memory objects both report as equal, or both report as not
equal to anything, depending on the sentinel chosen. **Fix.** Base entity
equality on identity comparison only after confirming both sides have a
real, non-null ID, and fall back to reference equality for two unsaved
objects being compared to each other.

**Symptom.** An `UPDATE` silently updates zero rows, or updates the wrong
row, after a batch import or a cache-restore path. **Cause.** The Identity
Field was populated from a stale or externally-controlled source (a CSV
import, a cache deserialization) rather than from the actual insert, and
the value collided with, or diverged from, the database's own generator
state, a classic symptom when a sequence is manually reset lower than the
highest existing ID after a data migration. **Fix.** Never hand-assign a
database-generated Identity Field outside the mapper, and after any bulk
load that inserts explicit ID values, explicitly advance the underlying
sequence or `IDENTITY` starting value to the new maximum.

**Symptom.** The primary key column is used as if it carries business
meaning, sort order shown to a customer as a queue position, or the ID
embedded directly in a public URL treated as evidence of how many rows
exist. **Cause.** The team confused the surrogate Identity Field, which is
supposed to carry no business meaning, with a natural key or a business
sequence number, and code elsewhere started depending on its numeric
magnitude or its gaps. **Fix.** Add an explicit, separately maintained
business field (an order number, a display sequence) for anything the
domain or the user is meant to reason about, and treat the Identity Field
strictly as an opaque lookup token.

**Symptom.** Enumerable, incrementing integer IDs exposed directly in a
public API let an attacker walk `/orders/1`, `/orders/2`, `/orders/3` and
enumerate other customers' data. **Cause.** The Identity Field's internal
generation strategy, a simple sequential integer, was exposed unchanged as
the external API identifier, conflating cheap-for-the-database-to-index
with safe-to-hand-to-an-untrusted-client. **Fix.** Either use a
non-sequential value (a UUID or a Stripe-style opaque prefixed string) as
the externally-visible identifier, or keep the internal sequential ID
private and expose a separately generated public token, paired with
proper authorization checks so guessing a valid ID is not itself
sufficient to read the row.

**Symptom.** Object equality tests pass in unit tests but the same
entities compare unequal once loaded through the ORM in an integration
test. **Cause.** Two entity subclasses, or an entity and its dynamically
generated proxy (a common Hibernate lazy-loading artefact), override
`equals` using `getClass() == other.getClass()` rather than `instanceof`,
so a proxy wrapping the exact same row compares unequal to the plain
loaded instance. **Fix.** Base entity equality on the Identity Field
value plus an `instanceof` check against the unproxied entity type, not
on exact class identity, which is the documented fix pattern recommended
for Hibernate-managed entities.

## 12. Trade-off matrix

Compared against the two named alternatives, using no stored identity at
all (matching by natural key on every operation) and using a Natural Key
as the declared primary key.

| Force | Identity Field (surrogate) | Match by Natural Key (no stored ID) | Natural Key as declared PK |
|---|---|---|---|
| Stability across business-data edits | Immune, never depends on mutable fields | Breaks the moment the matched field changes | Requires a migration if the key value must ever change |
| Cost to implement | One extra column, well supported by every ORM | No extra column, but every update needs a full old-value match | No extra column, and the value already carries business meaning |
| Foreign key size and index locality | Small, index-friendly (int/long) or moderate (UUID) | Typically not used for FK targets | Can be large or variable-width, hurting FK index size |
| Human readability of raw data | Unreadable without a join | Immediately readable | Immediately readable |
| Enables Identity Map or object caching by key | Directly, this is the precondition | Only if the natural key is itself stable, which is rare | Directly, same as Identity Field |
| Risk of key enumeration if exposed publicly | High for sequential integers, low for UUID or opaque tokens | Not applicable | Depends, often already public (an email, an ISBN) |
| Coupling to a single correct business identifier existing | None, works even when no natural key is unique or stable | Requires a genuinely unique, stable field to already exist | Requires the same, plus willingness to expose it as the PK |

## 13. Related and incompatible patterns

**Identity Map** depends directly on Identity Field. Identity Map's entire
mechanism, keeping one canonical in-memory instance per logical row within
a session, is only possible because the Identity Field value gives it a
reliable lookup key. Without a stable Identity Field, Identity Map has
nothing to key its cache on (Fowler, PoEAA, chapter 11, Identity Map).

**Unit of Work** composes with Identity Field. Unit of Work tracks which
objects are new, dirty, or removed, and when it flushes those changes it
uses each object's Identity Field to decide between issuing an `INSERT`
(field unset) and an `UPDATE` (field already populated), and to target the
`UPDATE`'s `WHERE` clause.

**Foreign Key Mapping** consumes Identity Field values as the payload of a
relationship. A child row's foreign-key column stores the parent's
Identity Field value, and the mapping layer resolves that value back into
a loaded parent object, or a lazily-resolved proxy of one, on read.

**Metadata Mapping** and Data Mapper frameworks generally declare, in
their metadata, which property plays the role of the Identity Field for a
given class, which is exactly what Hibernate's `@Id` annotation and Entity
Framework's key-by-convention detection both do.

**Repository** typically exposes a `findById(id)` method whose parameter
type is precisely the type of the aggregate root's Identity Field, making
the pattern visible at the boundary of the persistence-oriented API even
when the rest of the domain model tries to hide persistence concerns.

**Value Object** is the pattern Identity Field is explicitly incompatible
with at the conceptual level. Giving a Value Object an Identity Field
converts it into an Entity by definition, because identity-based equality
now overrides the structural equality a value object is meant to provide.
The two patterns are not used on the same class.

## 14. Refactoring path in and out

Introducing Identity Field into code that lacks it. Start from a domain
model whose objects are matched by ad-hoc combinations of business fields.

1. Add a nullable identifier field to the class, typed to match the
   intended primary key column, and leave every existing call site
   untouched for now.
2. Alter the underlying table to add the primary key column if it is not
   already there, backfilling existing rows with a one-off generation pass
   (a sequence starting above the current row count, or freshly generated
   UUIDs) rather than leaving historical rows without a value.
3. Update the insert path in the mapper to populate the new field from the
   database's generated value, or to generate it client-side before
   insert if that strategy was chosen, immediately after the row is
   written.
4. Update the update and delete paths to target `WHERE id = ?` instead of
   the previous ad-hoc match, one code path at a time, keeping the old
   match as a defensive assertion during the transition so a mismatch is
   loud rather than silent.
5. Once every read and write path goes through the Identity Field, remove
   the old ad-hoc matching logic and any now-redundant unique constraints
   that existed purely to support it.

This sequence mirrors the general shape of Fowler's *Refactoring, Improving
the Design of Existing Code*, 2nd edition, Addison-Wesley, 2018, chapter 6,
"A First Set of Refactorings", in that each step keeps the system working
end to end rather than pausing behaviour mid-change.

Removing Identity Field is rare, and is really the refactoring of
converting an Entity into a Value Object, because removing the Identity
Field only makes sense once every consumer has been shown the type no
longer needs independent identity across saves. Confirm no foreign key
anywhere still references the field, confirm no cache or session-scoped
Identity Map keys on it, replace equality and hashing with a full
structural comparison of the remaining fields, and only then drop the
column, in a migration that is reversible until the team is confident
nothing external still depends on the old identifiers.

## 15. Testing and verification

Identity Field makes one class of test trivially easy and hides one class
of bug that is easy to miss without a deliberate test for it.

What becomes easy is a round-trip test. Save an object, reload it by the
ID the mapper returned, and assert the reloaded object's business fields
match the original. This is the most reliable integration test for a
mapping layer, because it exercises the Identity Field's entire reason for
existing in one assertion.

What is easy to miss is equality and hashing correctness before an ID is
assigned. A dedicated unit test should construct two fresh, unsaved
instances with identical business-field values and assert they are NOT
considered equal, because neither has a real identity yet, then save one,
reload it into a second in-memory reference, and assert those two ARE
considered equal, purely because their Identity Field values now match
even though the object references differ. A test suite that only checks
equality after both sides are saved will not catch the far more common
production bug, comparing two not-yet-saved instances and getting a false
positive because both hold the same null or zero sentinel.

A separate integration-level test worth writing explicitly checks
concurrent insert of two rows and asserts their generated Identity Field
values are distinct, which catches sequence misconfiguration (a manually
reset sequence colliding with existing rows, discussed under failure
modes above) before it reaches production. In-memory or embedded
databases used for fast unit tests (SQLite in-memory, H2) are a
reasonable stand-in for this as long as the ID generation strategy under
test (sequence vs UUID) behaves the same way in the lightweight database
as it will in production, which is not always true for
`AUTO_INCREMENT` semantics across database engines and should be
verified once against the real target database rather than assumed.

## 16. Observability signals

The health of an Identity Field strategy is largely invisible until it
fails, so the useful signals are indirect.

- **Insert-to-ID-availability latency.** For database-generated strategies
  relying on `RETURNING` or a round trip to fetch `LAST_INSERT_ID()`, this
  is effectively part of insert latency. A spike here often means
  contention on the sequence or identity-generation lock under high
  concurrent insert load, worth its own dashboard panel on write-heavy
  tables.
- **Duplicate key constraint violation rate.** A nonzero, rising count of
  primary-key violation errors on insert is close to a direct signal that
  something outside the mapper is manually assigning ID values, or that a
  sequence has drifted below the current maximum row value after a data
  migration or restore.
- **Index size and fragmentation for the primary key index**, specifically
  on tables using random (UUIDv4-style) values under sustained high write
  volume. B-tree bloat on a clustered random-key index is a leading
  indicator of the exact cost predicted under the forces in dimension 3,
  and it shows up first as a slow, gradual increase in average insert
  latency and index storage size rather than a sudden failure.
- **Object-cache or Identity-Map hit rate keyed on ID**, in systems
  layering a cache over the mapper. A falling hit rate despite stable
  traffic patterns can indicate ID values are not stable across requests,
  which points back to a bug in how or when the Identity Field is being
  assigned.

## 17. Security and privacy implications

A sequential, database-generated Identity Field exposed as an external API
or URL identifier is an enumeration and information-disclosure risk. An
attacker who can access `/api/orders/1001` can trivially guess
`/api/orders/1000` and `/api/orders/1002` exist and attempt to access
them, turning a single authorization bug on that endpoint into
full-dataset exposure, and even with correct authorization, the sequential
value itself leaks business intelligence, roughly how many customers,
orders, or accounts exist and how fast the count is growing. The standard
mitigations are to expose a non-sequential, per-object token or a UUID as
the external identifier while keeping the internal sequential Identity
Field private to the mapping layer, and, independently and always, to
enforce authorization checks on every ID-keyed lookup rather than relying
on the ID's unguessability as a security boundary by itself, since
unguessability alone is not authorization.

Beyond enumeration, the Identity Field itself is rarely sensitive data in
the way the fields it accompanies can be, but it does become a durable,
stable correlation key. If the same value for a person's record is reused
across multiple systems, tables, or exported datasets without review, it
becomes a de facto cross-system tracking identifier even when no single
field within any one system looks sensitive on its own, which is worth
flagging in a data-mapping review for any system subject to data
protection regulation. Where a strict separation between systems is
required, generating a distinct, purpose-specific identifier per external
system rather than propagating one internal Identity Field everywhere is
the safer default.

## 18. References

- Martin Fowler, *Patterns of Enterprise Application Architecture*,
  Addison-Wesley, 2002, chapter 12, Object-Relational Structural Patterns,
  "Identity Field".
- [Martin Fowler, "Identity Field"](https://martinfowler.com/eaaCatalog/identityField.html), verified 2026-08-11.
- Martin Fowler, *Refactoring, Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 6, "A First Set of Refactorings".
- [Hibernate ORM 6.5 User Guide, section 3.7, "Identifiers", and section 3.7.2, "Composite identifiers"](https://docs.hibernate.org/orm/6.5/userguide/html_single/Hibernate_User_Guide.html), verified 2026-08-11.
- [Ruby on Rails Guides, "Active Record Basics"](https://guides.rubyonrails.org/active_record_basics.html), verified 2026-08-11.
- [Django documentation, "Models topic guide, Automatic primary key fields"](https://docs.djangoproject.com/en/5.2/topics/db/models/#automatic-primary-key-fields), verified 2026-08-11.
- [Microsoft Learn, "Keys, Entity Framework Core"](https://learn.microsoft.com/en-us/ef/core/modeling/keys).
- Internet Engineering Task Force, RFC 9562, "Universally Unique
  IDentifiers, UUIDs", May 2024.
- [Stripe API Reference](https://stripe.com/docs/api), object identifier
  field description.

## Code

### TypeScript

```typescript
class Customer {
  private _id: number | null = null;
  name: string;
  email: string;

  constructor(name: string, email: string) {
    this.name = name;
    this.email = email;
  }

  get id(): number | null {
    return this._id;
  }

  assignIdentity(id: number): void {
    if (this._id !== null) {
      throw new Error("identity already assigned");
    }
    this._id = id;
  }

  equals(other: Customer): boolean {
    if (this._id === null || other._id === null) {
      return this === other;
    }
    return this._id === other._id;
  }
}

class InMemoryCustomerTable {
  private rows = new Map<number, { name: string; email: string }>();
  private nextId = 1;

  insert(customer: Customer): void {
    const id = this.nextId++;
    this.rows.set(id, { name: customer.name, email: customer.email });
    customer.assignIdentity(id);
  }

  findById(id: number): Customer | null {
    const row = this.rows.get(id);
    if (!row) return null;
    const loaded = new Customer(row.name, row.email);
    loaded.assignIdentity(id);
    return loaded;
  }
}

const table = new InMemoryCustomerTable();
const a = new Customer("Ada Lovelace", "ada@example.com");
table.insert(a);

const b = table.findById(a.id as number);
console.log(a.equals(b as Customer));
console.log((b as Customer).id === a.id);
```

### Python

```python
class Customer:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email
        self._id: int | None = None

    @property
    def id(self) -> int | None:
        return self._id

    def assign_identity(self, identity: int) -> None:
        if self._id is not None:
            raise ValueError("identity already assigned")
        self._id = identity

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Customer):
            return NotImplemented
        if self._id is None or other._id is None:
            return self is other
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id) if self._id is not None else id(self)


class InMemoryCustomerTable:
    def __init__(self) -> None:
        self._rows: dict[int, dict] = {}
        self._next_id = 1

    def insert(self, customer: Customer) -> None:
        identity = self._next_id
        self._next_id += 1
        self._rows[identity] = {"name": customer.name, "email": customer.email}
        customer.assign_identity(identity)

    def find_by_id(self, identity: int) -> Customer | None:
        row = self._rows.get(identity)
        if row is None:
            return None
        loaded = Customer(row["name"], row["email"])
        loaded.assign_identity(identity)
        return loaded


if __name__ == "__main__":
    table = InMemoryCustomerTable()
    a = Customer("Ada Lovelace", "ada@example.com")
    table.insert(a)

    b = table.find_by_id(a.id)
    assert a == b
    assert b.id == a.id
    print("ok", a.id, b.id)
```

### Java

```java
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

class Customer {
    private Long id;
    private final String name;
    private final String email;

    Customer(String name, String email) {
        this.name = name;
        this.email = email;
    }

    Long getId() {
        return id;
    }

    void assignIdentity(long identity) {
        if (this.id != null) {
            throw new IllegalStateException("identity already assigned");
        }
        this.id = identity;
    }

    String getName() {
        return name;
    }

    String getEmail() {
        return email;
    }

    @Override
    public boolean equals(Object other) {
        if (this == other) return true;
        if (!(other instanceof Customer)) return false;
        Customer that = (Customer) other;
        if (this.id == null || that.id == null) {
            return false;
        }
        return this.id.equals(that.id);
    }

    @Override
    public int hashCode() {
        return id != null ? Objects.hash(id) : System.identityHashCode(this);
    }
}

class InMemoryCustomerTable {
    private final Map<Long, String[]> rows = new HashMap<>();
    private long nextId = 1;

    void insert(Customer customer) {
        long identity = nextId++;
        rows.put(identity, new String[]{customer.getName(), customer.getEmail()});
        customer.assignIdentity(identity);
    }

    Customer findById(long identity) {
        String[] row = rows.get(identity);
        if (row == null) return null;
        Customer loaded = new Customer(row[0], row[1]);
        loaded.assignIdentity(identity);
        return loaded;
    }
}

public class IdentityFieldDemo {
    public static void main(String[] args) {
        InMemoryCustomerTable table = new InMemoryCustomerTable();
        Customer a = new Customer("Ada Lovelace", "ada@example.com");
        table.insert(a);

        Customer b = table.findById(a.getId());
        System.out.println(a.equals(b));
        System.out.println(b.getId().equals(a.getId()));
    }
}
```
