---
name: Embedded Value
slug: embedded-value
family: 06-enterprise-application-architecture
category: Object-Relational Structural Pattern
aliases: [Value Object Mapping, Composed Of, Component Mapping, Inlined Value Object]
first_described: "Fowler 2002"
maturity: canonical
related: [identity-field, data-mapper, active-record, foreign-key-mapping, dependent-mapping, domain-model]
incompatible_with: []
verified: 2026-08-11
---

# Embedded Value

## 1. Name, aliases, and lineage

The canonical name is Embedded Value. It was catalogued by Martin Fowler in
*Patterns of Enterprise Application Architecture*, Addison-Wesley, 2002,
chapter 12, Object-Relational Structural Patterns, in the section titled
Embedded Value. Fowler states the intent as mapping an object into several
fields of another object's table
([Martin Fowler, "Embedded Value"](https://martinfowler.com/eaaCatalog/embeddedValue.html),
verified 2026-08-11). The catalog page's own sketch shows an `Employment`
record whose associated `DateRange` and `Money` objects contribute their
fields directly as columns of the `employment` table rather than living in
tables of their own, and the page places the entry inside chapter 12 of the
online edition, section `ch12.html#ch12lev1sec5`, per the catalog's own
navigation (same source, verified 2026-08-11).

Fowler frames Embedded Value as the object-relational counterpart to a
domain concept that most object designers already have a name for. a small,
immutable, identity-free object whose equality is defined by its fields
rather than by a database row. Eric Evans gives that domain concept its own
vocabulary in *Domain-Driven Design*, Addison-Wesley, 2003, calling it a
Value Object and defining it as an object that describes a characteristic of
another object and carries no conceptual identity of its own, in contrast to
an Entity, which is defined by a thread of continuity and identity (Eric
Evans, *Domain-Driven Design*, Addison-Wesley, 2003, chapter 5, "A Model
Expressed in Software", the section "Value Objects"). Embedded Value is the
persistence-layer technique that lets a Value Object exist in the domain
model without forcing a matching table into the relational schema. the two
ideas are frequently conflated in casual conversation, but Value Object
names the domain concept and Embedded Value names the specific mapping
strategy for storing one.

The pattern travels under several working names depending on which
community and which tool is describing it.

- **Value Object Mapping.** The generic description used across ORM
  documentation when the tool wants to describe the technique without tying
  itself to Fowler's specific term. Doctrine ORM, for the PHP ecosystem,
  calls its own implementation "Embeddables" directly, a near-verbatim echo
  of Fowler's name
  ([Doctrine ORM, "Embeddables"](https://www.doctrine-project.org/projects/doctrine-orm/en/current/tutorials/embeddables.html),
  verified 2026-08-11).
- **Composed Of.** The name Ruby on Rails gives the technique in
  ActiveRecord, through the `composed_of` class macro in the
  `ActiveRecord::Aggregations` module, which the Rails documentation
  describes as adding reader and writer methods that manipulate a value
  object composed from one or more columns of the owning table
  ([Rails API, `ActiveRecord::Aggregations::ClassMethods`](https://api.rubyonrails.org/classes/ActiveRecord/Aggregations/ClassMethods.html),
  verified 2026-08-11).
- **Component Mapping.** The term Hibernate used in its early documentation
  and still uses informally, before the JPA specification introduced the
  standard vocabulary. Hibernate's current user guide calls the mapped type
  an embeddable value type and states that such a type is a piece of data
  that does not define its own lifecycle, in effect owned by an entity that
  defines the lifecycle for it
  ([Hibernate ORM 6.4 User Guide, section 3.3, "Embeddable values"](https://docs.hibernate.org/orm/6.4/userguide/html_single/Hibernate_User_Guide.html),
  verified 2026-08-11).
- **Inlined Value Object.** A descriptive phrase used in developer
  discussion rather than in any single tool's official vocabulary, useful
  because it names the mechanism plainly. the value object's fields are
  inlined as columns of the containing table instead of receiving a table of
  their own.

No earlier pattern catalog names Embedded Value directly, because the
problem it solves only exists at the seam between an object model that
wants small immutable value types and a relational store that only has
tables and columns to offer. The Gang of Four's *Design Patterns*, published
eight years before Fowler's catalog, does not address persistence at all, so
Embedded Value has no GoF ancestor. Its closest conceptual relative inside
the GoF catalog is Flyweight, which also collapses many logical instances
onto shared underlying storage, though for a different reason. Flyweight
shares state across many logical objects to save memory, while Embedded
Value flattens one object's state into its owner's row to avoid an
unnecessary table (Erich Gamma, Richard Helm, Ralph Johnson, John
Vlissides, *Design Patterns*, Addison-Wesley, 1994, chapter 3,
"Structural Patterns", the section "Flyweight").

## 2. Problem and context

An application's domain model routinely needs small objects that group a
handful of related fields into one meaningful unit. a `Money` type pairing
an amount with a currency code, a `DateRange` pairing a start and an end
date, an `Address` pairing a street, a city, and a postal code, a
`PhoneNumber` pairing a country code with the local number. These objects
have no identity of their own. two `Money` instances holding 10 USD are
simply equal, not two different things that happen to hold the same value.
They are typically immutable, replaced wholesale rather than mutated in
place, and they are meaningless without the entity they describe. a
`DateRange` only matters as the tenure of a specific `Employment`.

The relational model that stores the surrounding entity has no native
concept matching this shape. A table row and a table's primary key are built
for identity-bearing records, the kind of thing Fowler calls the domain of
Identity Field and Identity Map. If a naive object-relational mapping
strategy is applied uniformly, every domain class, including these small
value types, receives its own table, its own primary key, and a foreign key
back to the owner. The result for a `Money` value type used across dozens of
entities is a `money` table holding an `amount` column, a `currency`
column, and a surrogate key that means nothing to anyone, joined into every
query that needs to read a price. The join buys nothing. the `Money` row
can never be shared, referenced independently, or queried on its own
outside the context of its owner, because it has no independent existence
in the domain either.

The problem context, concretely, is this. A team is building an
object-relational mapping layer, whether hand-rolled or through an ORM, for
a domain model that contains value objects nested inside entities. Every
value object turned into its own table adds a join to every load, a
migration to every schema change, and a place where the object's identity-
free equality semantics have to be reconciled with a table's identity-based
row semantics. The team needs a mapping strategy for exactly this shape.
data that is structurally an object in memory but has no independent
existence, and therefore no independent table, in the database.

## 3. Forces

- **Schema simplicity versus reuse of the value type's own table
  infrastructure.** Giving a value type its own table means it can carry its
  own constraints, its own indexes, and can be referenced by more
  than one owner through a foreign key. giving it up in favour of Embedded
  Value means every owner duplicates the value type's columns, and any index
  on those columns has to be repeated per owning table. Embedded Value wins
  when the value type genuinely has no independent life. it loses this force
  as soon as the "value" starts wanting to be shared or referenced.
- **Query cost.** A join is not free. Every load of an entity whose value
  objects live in separate tables pays for a join per value object, and a
  filter on a value object's field requires the join to exist in the query
  at all. Embedded Value removes the join entirely, because the columns are
  already present on the row being read. This is the force that most
  directly explains why the pattern exists. it trades table normalization
  for read performance and query simplicity.
- **Normalization discipline versus practical schema size.** Relational
  design orthodoxy pushes toward normal forms that eliminate repeated
  structure. Embedded Value deliberately denormalizes a nested object into
  its owner's row. In the case of a value type with no independent identity
  and no cross-entity sharing, this denormalization does not actually
  violate normal form in the classical sense, because the columns belong to
  the owning entity's attributes regardless of how they are grouped in
  object form, but it is still read by many engineers as tension against the
  instinct to normalize aggressively.
- **Object identity semantics versus row identity semantics.** A row has a
  primary key and identity across time. an embedded value object typically
  does not, and equality is structural (do the fields match) rather than
  referential (is this the same row). Forcing a value object into its own
  table, complete with a surrogate key, creates row identity where none is
  wanted in the domain, and every load then has to discard that manufactured
  identity to recover value semantics. Embedded Value avoids manufacturing
  identity that the domain never asked for.
- **Nesting depth and mapping complexity.** A value object composed of
  primitive fields maps trivially. a value object that itself contains
  another value object, for example an `Address` containing a `GeoPoint`,
  requires the mapping layer to flatten nested structure recursively into a
  single row's column set. The deeper the nesting, the more column-naming
  collisions and mapping configuration the pattern demands, and the harder
  it becomes to read the resulting table's schema and reconstruct the object
  graph by eye.
- **Null and default handling for optional embedded objects.** An owning
  entity may or may not have a value object present, for example an
  `Employment` with an optional `SeveranceDate` range that is absent for
  most employees. Representing "no value object present" in a flattened
  column set means every column that belongs to the value object must be
  simultaneously null or simultaneously populated, and the mapping layer
  must decide the convention for the all-null case rather than the database
  enforcing it structurally the way a missing foreign key row would.

Embedded Value privileges query performance and honest value semantics over
schema purity and the flexibility of an independently addressable table. It
sacrifices the ability to share, index independently, or reference the
value type from more than one place, and it sacrifices a database-level
guarantee that "value object present" and "value object absent" are
distinguishable, pushing that guarantee onto the mapping layer or a nullable
convention instead.

## 4. Applicability and non-applicability

Reach for Embedded Value when all of the following hold.

- The nested object has no identity of its own in the domain. two instances
  with the same field values are the same value, not two different
  business facts that happen to coincide.
- The nested object is owned by exactly one entity at a time and is never
  referenced independently or shared by reference across owners. If two
  `Employment` records both need "$50,000 USD" as a salary, each gets its
  own `Money` instance holding the same value, not a shared row.
- The nested object's field count is small and stable, so adding its
  columns to the owner's table does not make that table unwieldy, and the
  fields are not expected to grow into their own rich relational structure
  later.
- The owning entity is the natural unit of query and load. code almost
  always loads the owner and, in the same breath, needs the embedded
  value's fields, so paying a join to get them separately would be pure
  overhead.
- The mapping tool or hand-rolled data access layer already supports typed
  round-tripping between the flattened columns and the reconstructed
  object, so application code never manipulates the raw columns directly.

Do NOT reach for Embedded Value, and prefer Dependent Mapping's sibling
patterns or a full entity mapping instead, when any of the following hold.

- The nested object needs independent identity, for example because the
  business wants to reference "this specific address" from more than one
  place, audit its own change history, or list all addresses independently
  of who owns them. That is a job for a real entity with Identity Field, not
  for Embedded Value, because Embedded Value has no primary key of its own
  to reference.
- The nested object is genuinely a one-to-many collection rather than a
  one-to-one value, for example an employee's list of past addresses.
  Fowler assigns this shape to Dependent Mapping, a sibling pattern that
  maps a collection of dependent objects into a separate table keyed by a
  foreign key back to the owner, precisely because a flattened column set
  cannot represent an unbounded list
  ([Martin Fowler, "Dependent Mapping"](https://martinfowler.com/eaaCatalog/dependentMapping.html),
  verified 2026-08-11).
- The nested object needs to be queried, filtered, or indexed independently
  of its owner at scale, for example a reporting workload that needs every
  distinct `Money` amount across the whole system regardless of which
  entity holds it. Flattening the value into every owner's row makes that
  kind of cross-cutting query expensive or impossible without a separate
  materialized view.
- The owning entity already has, or is expected to grow, so many nested
  value objects that flattening all of them would push the table past a
  column count the team is comfortable maintaining, migrating, and reading.
  a table with 80 columns because eight value objects were each flattened
  in is a maintenance burden regardless of correctness.
- The database itself offers a first-class structured or composite column
  type that already captures the value object's shape with its own
  constraints and can be queried structurally, for example PostgreSQL's
  native `ROW` composite types or `JSONB` with a validating schema. In that
  case the database is doing the embedding for you, and hand-flattening
  into separate scalar columns discards structure the database could have
  kept.

## 5. Structure

- **Owner (the containing entity).** The entity that has a genuine table
  and a genuine identity. its table is where the embedded value's columns
  physically live. In Fowler's own example this role is played by
  `Employment`.
- **Embedded Value Object (the value type).** The small, identity-free,
  typically immutable class whose fields map to columns of the owner's
  table. It exposes no primary key of its own to the mapping layer. In
  Fowler's example this role is played by `DateRange` and by `Money`.
- **Mapper (or ORM configuration).** The piece of code, whether a
  hand-written `Employment` mapper or a declarative annotation set such as
  JPA's `@Embeddable` and `@Embedded`, responsible for translating between
  the owner's flat row of columns and the reconstructed object graph
  containing the nested value object. The mapper is the only code that
  knows both the object shape and the column layout simultaneously.
- **Column Prefix or Naming Convention.** When an owner contains more than
  one embedded value object, or the same value type appears more than once
  (for example a `startAddress` and an `endAddress`, both `Address`
  values), the mapping layer needs a naming strategy to disambiguate the
  resulting columns, commonly a prefix per usage such as `start_street` and
  `end_street`.

## 6. ASCII structure diagram

```
+----------------------------+
|         Employment          |   <- Owner, has real identity
|----------------------------|
| id            (PK)          |
| employee_name                |
| start_date     -----+        |  <- flattened DateRange fields
| end_date       -----+--------+ - these two columns ARE the
| salary_amount  -----+        |   embedded value's fields,
| salary_currency-----+        |   inlined into this one row
+----------------------------+
        ^
        | mapped by
        |
+----------------------------+       +----------------------------+
|      Employment Mapper      | <---> |      DateRange (value)      |
|----------------------------|       |----------------------------|
| load(row) -> Employment      |       | start: Date                 |
| save(Employment) -> row      |       | end: Date                   |
+----------------------------+       +----------------------------+
        |                                (no id, no table,
        | reads/writes the same           no independent row)
        | row's columns for
        v
+----------------------------+
|       Money (value)         |
|----------------------------|
| amount: Decimal              |
| currency: String             |
+----------------------------+
   (also no id, no table)
```

## 7. Dynamics

```
LOAD (SELECT one Employment row)

  Database                Mapper                       Application
     |                       |                              |
     |--row(id, name,        |                              |
     |  start_date, end_date,|                              |
     |  salary_amount,       |                              |
     |  salary_currency)---->|                              |
     |                       |-- construct DateRange(         |
     |                       |     row.start_date,            |
     |                       |     row.end_date) ------------>|
     |                       |-- construct Money(              |
     |                       |     row.salary_amount,          |
     |                       |     row.salary_currency)------->|
     |                       |-- construct Employment(         |
     |                       |     row.id, row.name,          |
     |                       |     dateRange, money)---------->|
     |                       |                              Employment
     |                       |                              (with nested
     |                       |                              DateRange, Money)


SAVE (UPDATE or INSERT one Employment row)

     Application              Mapper                     Database
         |                       |                           |
         |--Employment---------->|                           |
         |  (with nested          |-- read employment.dateRange|
         |   DateRange, Money)    |   .start, .end             |
         |                       |-- read employment.money    |
         |                       |   .amount, .currency        |
         |                       |-- build one row of columns |
         |                       |   from all three objects    |
         |                       |-- UPDATE employment SET ---->|
         |                       |   start_date=?, end_date=?, |
         |                       |   salary_amount=?,          |
         |                       |   salary_currency=?          |
         |                       |   WHERE id=? ---------------->|
```

The defining trait visible in both flows is that the value objects never
appear on the wire between the mapper and the database as anything other
than plain columns of the owner's single row. There is exactly one
round-trip per load and exactly one statement per save, regardless of how
many value objects are nested inside the owner, which is the direct
consequence of eliminating the join or the extra insert that a separate
table would require.

## 8. Implementation variants

- **Declarative ORM annotation.** The dominant variant in mainstream
  frameworks. the value type is marked once as embeddable, and the owning
  entity declares a field of that type, with the ORM generating the column
  flattening automatically. JPA's `@Embeddable` on the value class and
  `@Embedded` on the owning field is the reference example, and Hibernate's
  user guide documents the mechanism in exactly these terms
  ([Hibernate ORM 6.4 User Guide, section 3.3](https://docs.hibernate.org/orm/6.4/userguide/html_single/Hibernate_User_Guide.html),
  verified 2026-08-11). Doctrine ORM's `#[Embeddable]` attribute for PHP
  follows the identical shape and states plainly that Doctrine will
  automatically inline all columns from the embedded class into the table
  of the owning class, exactly as if the columns had been declared directly
  on the owner
  ([Doctrine ORM, "Embeddables"](https://www.doctrine-project.org/projects/doctrine-orm/en/current/tutorials/embeddables.html),
  verified 2026-08-11).
- **Aggregation macro in an Active Record framework.** Rails' `composed_of`
  is a declarative, single-line variant that wires a value object to one or
  more columns of the same table an ActiveRecord model already maps,
  generating both a reader that constructs the value object and a writer
  that decomposes it back into columns on assignment
  ([Rails API, `ActiveRecord::Aggregations::ClassMethods`](https://api.rubyonrails.org/classes/ActiveRecord/Aggregations/ClassMethods.html),
  verified 2026-08-11). This variant is distinctive because it retrofits
  Embedded Value onto a framework whose default mapping strategy is Active
  Record rather than Data Mapper, showing the pattern composes with either.
- **Hand-rolled mapper with explicit flatten and reconstruct
  methods.** Before mainstream ORMs matured, and still common in code bases
  that avoid a heavy ORM, the owner's mapper contains two explicit
  functions, one that reads the row and calls each value type's
  constructor with the relevant subset of columns, and one that, on save,
  calls accessor methods on each value object and writes the results into
  the appropriate parameters of an `INSERT` or `UPDATE` statement. Fowler
  describes this manual approach as the baseline implementation before
  showing how a code generator or reflection-based mapper can automate it
  (Martin Fowler, *Patterns of Enterprise Application Architecture*,
  Addison-Wesley, 2002, chapter 12, the section "Embedded Value").
- **Native composite or JSON column as the storage substrate.** A
  variant that keeps the object nesting at the database level instead of
  flattening to independent scalar columns, using a database feature such
  as a composite type or a JSON or JSONB column to hold the value object's
  fields together while still avoiding a separate table and a join. This
  trades some of the pure relational queryability of individually indexed
  scalar columns for a mapping that more closely mirrors the object's own
  shape, and it is common in PostgreSQL-based systems where `JSONB` columns
  with generated or expression indexes recover much of the queryability the
  flattened variant has by default.
- **Struct or record embedding at the language level, orthogonal to the
  ORM.** In languages with native value types, the domain-level Value
  Object can be a language struct (Swift's `struct`, C#'s `struct` or
  `record`, Rust's `struct` deriving `PartialEq`) even when the persistence
  layer's Embedded Value mapping is handled separately by an ORM or by
  hand-written SQL. This variant matters because it decouples "is this a
  value type in the domain" from "how is this value type persisted",
  letting a team introduce Embedded Value at the persistence boundary
  without changing how the value type is designed and used in memory.

## 9. Known production uses

- **Hibernate ORM, via `@Embeddable` and `@Embedded`.** Hibernate's
  section 3.3, "Embeddable values", describes an embeddable value type as
  data owned by an entity that defines its lifecycle, and walks through a
  `Contact` entity whose `Name` value type, holding `firstName`,
  `middleName`, and `lastName`, is mapped so that those three fields become
  columns of the `Contact` table rather than a separate `Name` table
  ([Hibernate ORM 6.4 User Guide, section 3.3, "Embeddable values"](https://docs.hibernate.org/orm/6.4/userguide/html_single/Hibernate_User_Guide.html),
  verified 2026-08-11). Hibernate is the reference implementation of the
  Java Persistence API's embeddable-type facility and is used across a
  large share of enterprise Java systems.
- **Ruby on Rails, via `ActiveRecord::Aggregations#composed_of`.** The
  Rails API documentation describes `composed_of` as adding reader and
  writer methods for manipulating a value object composed from columns of
  the owning table, and its own worked examples include a `Customer` model
  composed of a `Money` balance and an `Address`, both stored as columns of
  the `customers` table
  ([Rails API, `ActiveRecord::Aggregations::ClassMethods`](https://api.rubyonrails.org/classes/ActiveRecord/Aggregations/ClassMethods.html),
  verified 2026-08-11). Rails is one of the most widely deployed web
  frameworks built on the Active Record pattern, and `composed_of` has
  shipped as part of ActiveRecord since early Rails releases.
- **Doctrine ORM, via `#[Embeddable]` and `#[Embedded]`.** Doctrine's
  own tutorial states plainly that embeddables are classes which are not
  entities themselves but are embedded in entities, and that Doctrine will
  automatically inline all columns from the embedded class into the table
  of the owning class exactly as if they had been declared there directly,
  with the documented constraint that an embeddable can only contain
  properties with a basic column mapping, not associations
  ([Doctrine ORM, "Embeddables"](https://www.doctrine-project.org/projects/doctrine-orm/en/current/tutorials/embeddables.html),
  verified 2026-08-11). Doctrine ORM is the dominant object-relational
  mapper in the Symfony ecosystem and across a large share of production
  PHP applications.

## 10. Consequences

Positive.

- **Eliminates a join per load.** Every field of the embedded value is
  available the moment the owner's row is fetched, with no second query and
  no join clause, which is the single largest practical benefit and the one
  that motivates the pattern's existence in the first place.
- **Preserves honest value semantics in the domain model.** The domain
  class stays free of a manufactured primary key and free of row-identity
  baggage it does not conceptually need, so equality, immutability, and
  substitutability all work the way the domain intends without fighting the
  persistence layer.
- **Removes an entire table, its migrations, and its foreign key, from the
  schema.** Fewer tables means fewer objects to migrate, index, back up,
  and reason about when reading the schema, and it removes an entire class
  of orphan-row bugs that only exist because a separate table for the value
  type existed at all.
- **Keeps writes atomic within a single row.** Saving the owner and its
  embedded values is one `UPDATE` or `INSERT` statement touching one row,
  which sidesteps the multi-statement consistency concerns that arise when
  an owner and its dependent rows must be kept in sync across more than one
  table.

Negative.

- **The embedded value cannot be referenced, shared, or queried
  independently of its owner.** Once a value type genuinely needs to be
  addressed on its own, for example to support "list every distinct
  address in the system" efficiently, Embedded Value has to be undone and
  replaced with a real entity and table.
- **Every owner duplicates the value type's column set.** If ten different
  entity tables each embed a `Money` type, there are ten separate pairs of
  `amount` and `currency` columns to keep consistent in precision, default,
  and nullability, rather than one shared definition enforced in one place.
- **The owner's table grows a column for every field of every embedded
  value, compounding across nested value objects.** A table that embeds
  three value objects, each with four fields, carries twelve extra columns
  that a reader has to mentally regroup back into three logical objects
  to read the schema.
- **Optional embedded values require an ad hoc all-or-nothing null
  convention.** When the owner may or may not have the value object at all,
  the mapping layer typically encodes "absent" as every column of that
  value's field set being simultaneously null, a convention the database
  itself does nothing to enforce, unlike a genuinely absent foreign-keyed
  row which the database enforces by simple absence.
- **Schema evolution of the value type touches every owner's table.**
  Adding a field to a shared value type such as `Address` means an
  `ALTER TABLE` against every table that embeds `Address`, rather than a
  single migration against one shared `address` table, and the migration
  burden scales with the number of owners rather than staying constant.

## 11. Failure modes and misuse

- **Symptom.** The application starts throwing constraint violations or
  silently producing corrupted value objects, for example a `Money` whose
  `amount` column is populated but whose `currency` column is null.
  **Cause.** The mapping layer allows partial writes to an embedded value's
  column set, typically because the owner's save path was hand-modified to
  update only one of the two or more columns belonging to the same value
  object, breaking the implicit invariant that the value object's columns
  are always written together. **Fix.** Route every write to the owner's
  row through the mapper's single save method that always serializes the
  whole value object, never expose the individual columns of an embedded
  value to code paths that update columns piecemeal, and add a database
  constraint, for example a `CHECK` that both columns are null together or
  populated together, so a partial write fails loudly at the database
  rather than silently at read time.

- **Symptom.** Every schema migration that touches a widely embedded value
  type, such as `Address` or `Money`, turns into a large, error-prone,
  multi-table migration script that must be kept perfectly consistent
  across a dozen or more tables. **Cause.** A value type intended to be
  small and stable was embedded into many owners without anyone
  anticipating that its shape would need to change, and the team is now
  paying the schema-evolution cost described in dimension 10 at the worst
  possible moment, under time pressure, rather than by choice. **Fix.**
  Before embedding a value type broadly, assess how likely its shape is to
  change. for a genuinely volatile or growing value type, prefer Dependent
  Mapping or a full entity with its own table instead, even at the cost of
  a join, because the migration cost of a shared, unstable, widely embedded
  value type usually exceeds the query-cost savings Embedded Value was
  chosen for.

- **Symptom.** A reporting or analytics query that needs to aggregate or
  filter on an embedded value's field, for example "total salary paid
  across all employments", is either impossible to write cleanly or
  requires a `UNION` across every table that happens to embed the same
  value type. **Cause.** The embedded value was never designed to be
  queried independently of its owner, and applying Embedded Value to a
  value type that a reporting workload later needs to treat as a
  first-class, cross-cutting concept was the wrong call from the start, or
  the reporting requirement emerged after the mapping decision was already
  made. **Fix.** Either build a materialized reporting view that unions the
  relevant columns from every owning table under one logical name, which
  keeps the OLTP schema unchanged, or accept the schema change and promote
  the value type to its own table with Dependent Mapping or Foreign Key
  Mapping once the cross-cutting query need is confirmed to be recurring
  rather than one-off.

- **Symptom.** Two different owning tables embed what looks like the same
  value type, but their column definitions have quietly drifted apart, for
  example one table's `salary_currency` column allows a two-letter code and
  another's allows a three-letter ISO 4217 code, and code that assumes a
  single shared `Money` value type breaks unpredictably depending on which
  owner it loaded from. **Cause.** Because Embedded Value duplicates the
  value type's columns per owner rather than centralizing them in one
  shared table, nothing at the database level enforces that the duplicated
  definitions stay identical, and drift accumulates silently as each
  table's migrations are written independently over time. **Fix.**
  Centralize the value type's column definition in one migration template
  or one shared schema fragment that every owner's migration includes by
  reference, add an automated schema-consistency check that compares the
  column definitions of every table embedding the same value type and fails
  a build when they no longer match, and treat any detected mismatch as a
  bug to reconcile immediately rather than something to special-case in
  application code.

## 12. Trade-off matrix

| Force | Embedded Value | Dependent Mapping | Foreign Key Mapping (a full owned entity) |
|---|---|---|---|
| Extra join on load | None. columns already on owner's row | One join, or a second query, per collection | One join, or a second query, per reference |
| Independent identity for the nested object | None. no primary key exposed | None for the dependent objects themselves, but each has its own row | Yes. the referenced entity has its own real identity |
| Can represent a one-to-many collection | No. one row means one flattened instance | Yes. this is exactly what it is designed for | Yes, via a collection of references |
| Schema change cost when the value type's shape changes | Touches every owning table's schema | Touches one shared dependent table | Touches one shared entity table |
| Cross-owner sharing of the same nested value by reference | Not possible. every owner has its own copy | Not typical. dependents still belong to one owner | Yes, this is the pattern's strength |
| Write cost | One statement covers owner and all embedded values | Owner plus one statement per dependent row changed | Owner plus a foreign key update, referenced entity is saved separately |
| Suited to small, stable, identity-free values | Best fit | Poor fit, adds ceremony for something with no independent life | Poor fit, manufactures identity the domain does not need |
| Suited to a genuine collection owned by one entity | Poor fit, cannot represent a list in flattened columns | Best fit | Workable but heavier than necessary if the referenced items are not truly independent |

Fowler's own catalog frames the boundary against Dependent Mapping directly.
Dependent Mapping is used when the nested objects form a collection owned
exclusively by one parent and stored in their own table keyed by a foreign
key back to the parent, which is precisely the case Embedded Value cannot
handle because it has only one row per owner to work with
([Martin Fowler, "Dependent Mapping"](https://martinfowler.com/eaaCatalog/dependentMapping.html),
verified 2026-08-11).

## 13. Related and incompatible patterns

- **Identity Field.** Embedded Value is defined in direct contrast to
  Identity Field. an object mapped with Identity Field has its own primary
  key and its own row, which is exactly what an embedded value object
  deliberately does not have. Reading Embedded Value alongside Identity
  Field clarifies the boundary. the moment a nested object needs a key of
  its own, it has left Embedded Value's territory and entered Identity
  Field's.
- **Dependent Mapping.** The sibling pattern for the one-to-many case
  Embedded Value cannot cover. A team that starts with Embedded Value and
  later discovers the "single value" is actually growing into a list is
  migrating from Embedded Value to Dependent Mapping, not extending
  Embedded Value itself.
- **Foreign Key Mapping.** The pattern that applies once a nested object
  needs genuine independent identity referenced from its owner. Embedded
  Value and Foreign Key Mapping sit on either side of the "does this nested
  thing have its own identity" question, and choosing between them is
  usually the first decision a mapping designer makes about any nested
  object.
- **Data Mapper and Active Record.** Embedded Value is not tied to either
  base persistence pattern and composes with both. In a Data Mapper
  architecture the mapper is the natural place to hold the flatten and
  reconstruct logic. in an Active Record architecture, as Rails'
  `composed_of` demonstrates directly, the same technique is folded into
  the Active Record class's own accessor methods.
- **Domain Model.** Embedded Value exists to serve a rich Domain Model, in
  which value objects are a natural and desired part of the object design.
  A codebase built on Transaction Script, which has little or no persistent
  domain object structure to map in the first place, has little use for
  Embedded Value because there is no object graph containing nested value
  types to flatten.
- **Value Object (DDD).** Not itself catalogued in Fowler's book, but the
  domain-modelling concept Embedded Value exists to persist. Any discussion
  of Embedded Value implicitly assumes the reader already has, or is
  designing, Value Objects in the Evans sense, described in dimension 1.
- **No genuinely incompatible pattern.** Embedded Value does not conflict
  mechanically with any other pattern in this catalog. its tension is
  entirely with itself being applied to the wrong shape of data, described
  fully in dimension 4's non-applicability list, rather than with another
  pattern actively fighting it at runtime.

## 14. Refactoring path in and out

Introducing Embedded Value into code that currently gives a value type its
own table.

1. Confirm the candidate value type has no independent identity in the
   domain and is never referenced from more than one owner concurrently. if
   either is false, stop here, this pattern is the wrong target.
2. Add the value type's columns directly to the owning entity's table via a
   migration, choosing a naming convention (a prefix per usage) that avoids
   collisions if the same value type will be embedded more than once on the
   same owner.
3. Backfill the new columns from the existing separate table in the same
   migration or a follow-up data migration, joining on the existing foreign
   key one final time to populate the flattened columns.
4. Update the mapper (or the ORM's declarative mapping) to read and write
   the value type from the new flattened columns instead of from the
   separate table, keeping the public interface of the owning entity's
   accessor for the value type unchanged so calling code does not need to
   change.
5. Once the flattened columns are verified correct in a full read and
   write cycle in a staging environment, drop the foreign key, drop the now
   unused separate table, and remove the old mapping configuration.
6. This sequence mirrors Fowler's own refactoring, Inline Class, applied at
   the schema level rather than purely in code, described as moving all of
   a class's features into another class and deleting the original
   (Martin Fowler, *Refactoring*, second edition, Addison-Wesley, 2018,
   the section "Inline Class").

Removing Embedded Value once a value type has outgrown it, typically because
it now needs independent identity, sharing, or a collection shape.

1. Create the new table the value type deserves, with its own primary key
   if the value type is becoming a genuine entity, or with a foreign key
   back to the owner if it is becoming a Dependent Mapping collection.
2. Migrate the existing flattened columns from every owning table into rows
   of the new table, generating identifiers or foreign keys as required by
   the target pattern.
3. Update the mapper to construct the value type from the new table via a
   join or a second query instead of from the owner's flattened columns,
   again preserving the owning entity's public accessor signature where
   possible so callers are insulated from the change.
4. Once verified, drop the old flattened columns from the owner's table in
   a follow-up migration, after confirming no remaining code path reads
   them directly.
5. This direction mirrors Fowler's refactoring Extract Class, described as
   creating a new class and moving the relevant fields and methods from the
   old class to the new one, applied here to both the object model and the
   schema simultaneously (Martin Fowler, *Refactoring*, second edition,
   Addison-Wesley, 2018, the section "Extract Class").

## 15. Testing and verification

Embedded Value makes several kinds of test genuinely easier because the
value type carries no persistence machinery of its own.

- **Value object equality and construction are trivially unit testable in
  complete isolation from the database.** Because an embedded value type
  has no primary key and no lazy-loading concerns, tests that assert two
  `Money` instances with the same amount and currency are equal, or that a
  `DateRange` correctly rejects an end date before its start date, need no
  database, no fixture, and no mock, which is a direct benefit of the value
  type's identity-free design that Embedded Value preserves rather than
  fights.
- **Round-trip tests are the primary correctness check specific to this
  pattern.** the core test is. construct an owner with a populated
  embedded value, save it, load it back by a fresh query (not from an
  in-memory cache), and assert the reloaded value object is equal to the
  original. This test exercises exactly the flatten-then-reconstruct
  behaviour that is unique to Embedded Value and catches the most common
  regression, a column added to the value type in code but not yet added to
  the owner's table migration, or the reverse.
- **Partial-write and null-handling tests guard the failure mode described
  in dimension 11.** a test that attempts to persist an owner whose
  embedded value object has some fields populated and others left at a
  default should assert the mapper either rejects the partial state or
  writes a fully consistent set of columns, never a silently mixed result.
- **A schema-consistency test across owners sharing the same embedded
  value type is worth automating specifically because the database does
  nothing to enforce it.** a test or a lightweight schema-linting script
  that walks every table known to embed a given value type and asserts the
  column types, nullability, and precision match across all of them
  directly targets the drift failure mode from dimension 11.
- Test doubles are largely unnecessary for the value object itself, since
  it is a plain, dependency-free class. the only piece worth mocking or
  stubbing in a broader test is the database connection or the mapper's
  data source when testing the owner's higher-level behaviour in isolation
  from persistence entirely, which is the same technique used for testing
  any mapped entity and is not specific to this pattern.

## 16. Observability signals

- **Row width and column count per table over time.** Because Embedded
  Value grows the owning table's column count with every value type
  embedded into it, tracking column count as a schema metric surfaces the
  consequence from dimension 10 (compounding column growth) before it
  becomes unmanageable, and a sudden jump in column count on a migration
  merge is a useful review signal.
- **Migration diff size and frequency for tables known to embed shared
  value types.** Because a shape change to a widely embedded value type
  fans out into a migration against every owning table, tracking how many
  tables a single migration touches, and flagging migrations that touch
  more than a small number of tables at once, surfaces the schema-evolution
  cost from dimension 10 as it happens rather than after the fact.
- **Null-pattern anomalies in a value type's column set.** A metric or a
  periodic query that counts rows where some, but not all, of an embedded
  value's columns are null directly measures the partial-write failure mode
  from dimension 11, and a nonzero count is an actionable data-quality
  alert rather than a query-time surprise.
- **Query plan absence of a join for owner-plus-value-object reads.** In a
  healthy instance of this pattern, an `EXPLAIN` of the query that loads an
  owner along with its embedded values shows a single table scan or index
  lookup with no join to a value-object-specific table. if a join reappears
  in that query plan, it usually means either the pattern has silently
  regressed toward Dependent Mapping without anyone updating the mapping
  intentionally, or a second, unnecessary value-object table was
  reintroduced by mistake.
- **Cross-owner schema drift for a shared value type, checked
  periodically.** A scheduled job or CI step that compares the column
  definitions of every table embedding the same value type, surfacing any
  table whose definition has drifted from the rest, is the direct
  observability counterpart to the drift failure mode in dimension 11 and
  is worth running on every schema change, not only at incident time.

## 17. Security and privacy implications

Embedded Value has a real, if largely secondary, security and privacy
footprint, and it is honest to state where the implication is genuine
analysis rather than a sourced claim.

- **Denormalized personal data multiplies the number of places a
  sensitive field lives.** When a value type such as an `Address` or a
  `TaxIdentifier` is embedded across many owning tables rather than kept in
  one shared table, a data-subject deletion or redaction request under a
  privacy regulation such as GDPR must be applied to every one of those
  owning tables individually, rather than to one shared table with a single
  foreign key to null out. This is engineering judgement drawn from the
  general shape of the pattern rather than a claim about any specific
  regulator's guidance, and it is a real operational cost of choosing
  Embedded Value for a value type that happens to carry personal data.
- **Access control granularity is coarser than a separate table would
  allow.** Because the embedded value's columns live inside the owner's
  row, a database-level column or row permission scheme that wants to
  restrict access to, for example, salary data more tightly than access to
  the rest of an `Employment` row has to do so at the column-grant level
  within the owner's table, rather than by restricting access to an
  entirely separate `salary` table. Most relational databases support
  column-level grants, so this is a workable but more fragile control
  surface than table-level isolation would provide.
- **Encryption at the field level interacts more simply with Embedded
  Value than with a joined value object, in one specific respect.** because
  every field of the embedded value is a plain column on the owner's row,
  applying column-level or application-level field encryption to a single
  sensitive field, for example encrypting only the `salary_amount` column
  while leaving `salary_currency` in plaintext, requires no join-aware
  logic, the encryption or decryption happens at exactly the point the row
  is read or written, which is simpler to reason about than encrypting a
  field that lives behind a join to a separate table.
- **No new network attack surface is opened by the pattern itself.**
  Embedded Value is purely a schema and mapping technique operating within
  a single database round trip, and it introduces no new external interface,
  endpoint, or serialization boundary of its own. any security implication
  it carries is inherited entirely from how the owning entity as a whole is
  exposed, queried, and access-controlled, not from the embedding technique
  in isolation. Where this is silent, it is genuinely silent. the pattern
  does not, on its own, create an injection, deserialization, or
  authentication concern beyond what already exists for the owning row.

## 18. References

- Martin Fowler, "Embedded Value", *Patterns of Enterprise Application
  Architecture* online catalog,
  <https://martinfowler.com/eaaCatalog/embeddedValue.html>, verified
  2026-08-11.
- Martin Fowler, "Dependent Mapping", *Patterns of Enterprise Application
  Architecture* online catalog,
  <https://martinfowler.com/eaaCatalog/dependentMapping.html>, verified
  2026-08-11.
- Martin Fowler, *Patterns of Enterprise Application Architecture*,
  Addison-Wesley, 2002, chapter 12, "Object-Relational Structural
  Patterns", the section "Embedded Value".
- Martin Fowler, *Refactoring*, second edition, Addison-Wesley, 2018, the
  sections "Inline Class" and "Extract Class".
- Eric Evans, *Domain-Driven Design*, Addison-Wesley, 2003, chapter 5, "A
  Model Expressed in Software", the section "Value Objects".
- Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides, *Design
  Patterns*, Addison-Wesley, 1994, chapter 3, "Structural Patterns", the
  section "Flyweight".
- Hibernate ORM 6.4 User Guide, section 3.3, "Embeddable values",
  <https://docs.hibernate.org/orm/6.4/userguide/html_single/Hibernate_User_Guide.html>,
  verified 2026-08-11.
- Doctrine ORM documentation, "Embeddables",
  <https://www.doctrine-project.org/projects/doctrine-orm/en/current/tutorials/embeddables.html>,
  verified 2026-08-11.
- Ruby on Rails API documentation, `ActiveRecord::Aggregations::ClassMethods`,
  <https://api.rubyonrails.org/classes/ActiveRecord/Aggregations/ClassMethods.html>,
  verified 2026-08-11.

## Code examples

### TypeScript

```typescript
class Money {
  constructor(readonly amount: number, readonly currency: string) {}

  equals(other: Money): boolean {
    return this.amount === other.amount && this.currency === other.currency;
  }
}

class DateRange {
  constructor(readonly start: Date, readonly end: Date) {}

  contains(point: Date): boolean {
    return point >= this.start && point <= this.end;
  }
}

interface EmploymentRow {
  id: number;
  employeeName: string;
  startDate: string;
  endDate: string;
  salaryAmount: number;
  salaryCurrency: string;
}

class Employment {
  constructor(
    readonly id: number,
    readonly employeeName: string,
    readonly tenure: DateRange,
    readonly salary: Money,
  ) {}
}

function loadEmployment(row: EmploymentRow): Employment {
  const tenure = new DateRange(new Date(row.startDate), new Date(row.endDate));
  const salary = new Money(row.salaryAmount, row.salaryCurrency);
  return new Employment(row.id, row.employeeName, tenure, salary);
}

function toRow(e: Employment): EmploymentRow {
  return {
    id: e.id,
    employeeName: e.employeeName,
    startDate: e.tenure.start.toISOString(),
    endDate: e.tenure.end.toISOString(),
    salaryAmount: e.salary.amount,
    salaryCurrency: e.salary.currency,
  };
}

const row: EmploymentRow = {
  id: 1,
  employeeName: "Jordan Lee",
  startDate: "2024-01-15",
  endDate: "2025-06-30",
  salaryAmount: 82000,
  salaryCurrency: "USD",
};

const employment = loadEmployment(row);
console.log(employment.salary.equals(new Money(82000, "USD")));
console.log(employment.tenure.contains(new Date("2024-08-01")));
console.log(JSON.stringify(toRow(employment)));
```

### Python

```python
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Money:
    amount: int
    currency: str


@dataclass(frozen=True)
class DateRange:
    start: date
    end: date

    def contains(self, point: date) -> bool:
        return self.start <= point <= self.end


@dataclass(frozen=True)
class Employment:
    id: int
    employee_name: str
    tenure: DateRange
    salary: Money


def load_employment(row: dict) -> Employment:
    tenure = DateRange(row["start_date"], row["end_date"])
    salary = Money(row["salary_amount"], row["salary_currency"])
    return Employment(row["id"], row["employee_name"], tenure, salary)


def to_row(e: Employment) -> dict:
    return {
        "id": e.id,
        "employee_name": e.employee_name,
        "start_date": e.tenure.start,
        "end_date": e.tenure.end,
        "salary_amount": e.salary.amount,
        "salary_currency": e.salary.currency,
    }


if __name__ == "__main__":
    row = {
        "id": 1,
        "employee_name": "Jordan Lee",
        "start_date": date(2024, 1, 15),
        "end_date": date(2025, 6, 30),
        "salary_amount": 82000,
        "salary_currency": "USD",
    }
    employment = load_employment(row)
    assert employment.salary == Money(82000, "USD")
    assert employment.tenure.contains(date(2024, 8, 1))
    print(to_row(employment))
```

### Go

```go
package main

import (
	"fmt"
	"time"
)

type Money struct {
	Amount   int64
	Currency string
}

type DateRange struct {
	Start time.Time
	End   time.Time
}

func (d DateRange) Contains(point time.Time) bool {
	return !point.Before(d.Start) && !point.After(d.End)
}

type employmentRow struct {
	ID             int
	EmployeeName   string
	StartDate      time.Time
	EndDate        time.Time
	SalaryAmount   int64
	SalaryCurrency string
}

type Employment struct {
	ID           int
	EmployeeName string
	Tenure       DateRange
	Salary       Money
}

func loadEmployment(row employmentRow) Employment {
	return Employment{
		ID:           row.ID,
		EmployeeName: row.EmployeeName,
		Tenure:       DateRange{Start: row.StartDate, End: row.EndDate},
		Salary:       Money{Amount: row.SalaryAmount, Currency: row.SalaryCurrency},
	}
}

func toRow(e Employment) employmentRow {
	return employmentRow{
		ID:             e.ID,
		EmployeeName:   e.EmployeeName,
		StartDate:      e.Tenure.Start,
		EndDate:        e.Tenure.End,
		SalaryAmount:   e.Salary.Amount,
		SalaryCurrency: e.Salary.Currency,
	}
}

func main() {
	row := employmentRow{
		ID:             1,
		EmployeeName:   "Jordan Lee",
		StartDate:      time.Date(2024, 1, 15, 0, 0, 0, 0, time.UTC),
		EndDate:        time.Date(2025, 6, 30, 0, 0, 0, 0, time.UTC),
		SalaryAmount:   82000,
		SalaryCurrency: "USD",
	}

	employment := loadEmployment(row)
	check := Money{Amount: 82000, Currency: "USD"}
	fmt.Println(employment.Salary == check)
	fmt.Println(employment.Tenure.Contains(time.Date(2024, 8, 1, 0, 0, 0, 0, time.UTC)))
	fmt.Printf("%+v\n", toRow(employment))
}
```

### Swift

```swift
import Foundation

struct Money: Equatable {
    let amount: Int
    let currency: String
}

struct DateRange: Equatable {
    let start: Date
    let end: Date

    func contains(_ point: Date) -> Bool {
        return point >= start && point <= end
    }
}

struct EmploymentRow {
    let id: Int
    let employeeName: String
    let startDate: Date
    let endDate: Date
    let salaryAmount: Int
    let salaryCurrency: String
}

struct Employment {
    let id: Int
    let employeeName: String
    let tenure: DateRange
    let salary: Money
}

func loadEmployment(_ row: EmploymentRow) -> Employment {
    let tenure = DateRange(start: row.startDate, end: row.endDate)
    let salary = Money(amount: row.salaryAmount, currency: row.salaryCurrency)
    return Employment(id: row.id, employeeName: row.employeeName, tenure: tenure, salary: salary)
}

func toRow(_ e: Employment) -> EmploymentRow {
    return EmploymentRow(
        id: e.id,
        employeeName: e.employeeName,
        startDate: e.tenure.start,
        endDate: e.tenure.end,
        salaryAmount: e.salary.amount,
        salaryCurrency: e.salary.currency
    )
}

let formatter = ISO8601DateFormatter()
let row = EmploymentRow(
    id: 1,
    employeeName: "Jordan Lee",
    startDate: formatter.date(from: "2024-01-15T00:00:00Z")!,
    endDate: formatter.date(from: "2025-06-30T00:00:00Z")!,
    salaryAmount: 82000,
    salaryCurrency: "USD"
)

let employment = loadEmployment(row)
print(employment.salary == Money(amount: 82000, currency: "USD"))
print(employment.tenure.contains(formatter.date(from: "2024-08-01T00:00:00Z")!))
print(toRow(employment).salaryAmount, toRow(employment).salaryCurrency)
```
