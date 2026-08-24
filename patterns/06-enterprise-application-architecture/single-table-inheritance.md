---
name: Single Table Inheritance
slug: single-table-inheritance
family: 06-enterprise-application-architecture
category: Object-Relational Structural Patterns
aliases: [STI, Discriminator Column Inheritance, Type Column Inheritance]
first_described: "Fowler 2002"
maturity: canonical
related: [class-table-inheritance, concrete-table-inheritance, active-record, foreign-key-mapping, layer-supertype, identity-field]
incompatible_with: [concrete-table-inheritance, class-table-inheritance]
verified: 2026-08-02
---

# Single Table Inheritance

## 1. Name, aliases, and lineage

The canonical name is Single Table Inheritance, catalogued as one of the three
inheritance mapping patterns in Martin Fowler's *Patterns of Enterprise
Application Architecture*, Addison-Wesley, 2002, ISBN 0-321-12742-0, in the
Object-Relational Structural Patterns group, catalog entry "Single Table
Inheritance". The book states the intent as representing an inheritance
hierarchy of classes as a single table that has columns for all the fields of
the various classes (Fowler, *Patterns of Enterprise Application Architecture*,
online catalog page, https://martinfowler.com/eaaCatalog/singleTableInheritance.html
verified 2026-08-02). The catalog page groups it alongside its two siblings,
Class Table Inheritance and Concrete Table Inheritance, as three distinct
answers to the same problem, mapping an object hierarchy onto tables that have
no native concept of inheritance.

The most common alias in day-to-day engineering conversation is the acronym
**STI**, used pervasively in the Ruby on Rails community because Rails
implements the pattern as a first-class ActiveRecord feature under exactly that
name. **Discriminator Column Inheritance** and **Type Column Inheritance** are
descriptive aliases used in the Java persistence world, where the JPA
specification names the same technique `InheritanceType.SINGLE_TABLE` and
identifies rows by a discriminator column, most often called `DTYPE` by
convention (Baeldung, "Hibernate Inheritance Mapping",
https://www.baeldung.com/hibernate-inheritance verified 2026-08-02).

Two things get conflated with this pattern often enough that a reader should
learn to separate them on sight.

- **Single Table Inheritance is not the same thing as a wide, denormalised
  table that was never meant to model a hierarchy.** A table becomes an
  instance of this pattern only when the columns beyond a shared core are
  genuinely partitioned by an object-oriented subtype relationship, and a
  discriminator column exists to say which subtype a given row belongs to. A
  table that merely accumulated unrelated optional columns over years of ad
  hoc feature work is not STI, it is schema decay, even though the two can
  look identical in `DESCRIBE TABLE` output.
- **STI is not Table Per Hierarchy in every ORM's exact terminology, but it is
  the same concept.** Entity Framework calls it Table-Per-Hierarchy (TPH).
  Hibernate and the wider JPA ecosystem call it the single table strategy.
  Rails calls it Single Table Inheritance. All three names point at the same
  mapping decision, one table, one discriminator column, nullable
  subtype-specific columns.

## 2. Problem and context

An object model has a natural inheritance hierarchy. A base type carries
shared fields and shared behaviour, and several subtypes each add a small
number of fields or override a small number of methods. The relational
database that will store these objects has no concept of inheritance at all,
only tables, columns, and rows.

The concrete situation looks like this in a real codebase. A `Vehicle` base
class exists with `make`, `model`, and `year`. A `Car` subclass adds
`door_count`. A `Motorcycle` subclass adds `has_sidecar`. A `Truck` subclass
adds `cargo_capacity_kg`. All three subclasses are queried together often, for
example a fleet-listing screen that shows every vehicle regardless of kind,
and each is also queried alone, for example a report that only cares about
trucks and their cargo capacity. The application already has working
polymorphic behaviour in memory, a `Vehicle.describe()` method that each
subclass overrides, and the persistence layer needs to preserve that
polymorphism across a save and a reload.

Three relational mapping answers exist for this exact situation, and Fowler's
catalog treats them as a family precisely because no single one of the three
is correct in every case. Single Table Inheritance answers it by making one
table wide enough to hold every column any subtype needs, with a discriminator
column recording which subtype a row actually is, and by leaving a row's
subtype-irrelevant columns null. Class Table Inheritance answers it with one
table per class in the hierarchy, joined by a shared identifier. Concrete
Table Inheritance answers it with one table per concrete leaf class,
duplicating the shared columns into each. This entry covers the first of the
three, and treats the choice between them as dimension 12's job.

The context that makes Single Table Inheritance specifically the right member
of that family to reach for has a few recognisable shapes.

- The hierarchy is queried across subtypes far more often than it is queried
  within one subtype alone, so a query spanning the whole hierarchy must not
  pay a join for every level.
- The number of subtype-specific columns is small relative to the shared
  columns, so the table does not become mostly empty cells.
- The hierarchy is shallow, typically one or two levels, and reasonably
  stable, so the column count is not expected to keep growing indefinitely.
- The team values the operational simplicity of one table, one set of
  indexes, and one migration history over the normalisation purity of a
  table per class.

Outside that context the pattern turns into a liability, covered in dimension
4.

## 3. Forces

This is judgement, weighing which pressure matters more, rather than reporting
a citable ranking.

- **Read performance for cross-subtype queries.** Strongly favoured. A query
  that must return every vehicle regardless of kind touches one table and
  needs no join, which is the pattern's whole reason to exist.
- **Read performance for single-subtype queries.** Mildly favoured, though
  less than the whole-hierarchy case. A query scoped to trucks alone still
  reads one table with a `WHERE vehicle_type = 'truck'` predicate, and an
  index on the discriminator column keeps that fast, but the table itself may
  now be wider than a dedicated `trucks` table would have been, so each page
  read pulls in columns the query never touches.
- **Write and schema evolution cost.** Sacrificed as the hierarchy grows. Every
  new subclass field is a new column on a table shared by every other
  subclass, and every column addition is a schema migration that touches rows
  that will never use the new column. A hierarchy that keeps growing new
  leaf-specific fields turns this into a running cost that compounds.
- **Data integrity at the column level.** Sacrificed. A relational column
  cannot be `NOT NULL` for one subtype and irrelevant for another in the same
  physical column, so subtype-specific columns are necessarily nullable even
  when a given subtype's business rule says the field is mandatory for that
  subtype. The database can no longer enforce that mandatory-ness; the
  application must.
- **Storage.** Sacrificed, though usually by a smaller margin than intuition
  suggests. Modern row-oriented engines store `NULL` cheaply, often as a bit
  in a null bitmap rather than a full-width empty value, so the wasted-space
  argument against STI is weaker in practice than it was when the pattern was
  first documented against 1990s and early-2000s database engines. Column
  count against a page-size limit is the more durable cost, not raw byte
  waste. See dimension 11.
- **Operability and schema readability.** Sacrificed for a large hierarchy. A
  table with sixty columns where any given row uses fifteen of them is hard
  for a new engineer, or a DBA without ORM context, to read directly. The
  meaning of a column is conditional on another column's value, which is not
  something a `\d tablename` in `psql` communicates.
- **Consistency of shared behaviour.** Favoured. Because every subtype's data
  lives in rows of the same table, a constraint, trigger, or shared index that
  applies to the whole hierarchy is defined exactly once.
- **Polymorphic association simplicity.** Favoured. A foreign key from another
  table pointing at "any vehicle" points at one table and one primary key
  space, with no need for a polymorphic association scheme that must also
  carry a type tag to know which of several tables to join against.

A pattern that sacrificed nothing would not be a design decision, it would be
a database feature. The price paid here is schema width, nullable columns
that carry conditional meaning, and a growing migration burden as the
hierarchy grows, purchased in exchange for join-free polymorphic reads and a
single, simple identity space.

## 4. Applicability and non-applicability

Reach for Single Table Inheritance when the following hold together, not in
isolation.

- The hierarchy is shallow and the set of subclasses is closed or changes
  rarely, so the column count is not on a growth trajectory.
- Subtype-specific fields are few relative to shared fields, so the table
  does not become mostly nullable columns.
- Cross-subtype queries outnumber single-subtype queries, and paying a join
  for every such query would be a measured cost, not a theoretical one.
- The team is comfortable enforcing subtype-conditional validation in the
  application or the ORM rather than in database constraints.
- A single, uniform primary key space across the whole hierarchy simplifies
  other parts of the system, most often polymorphic foreign keys from
  unrelated tables.

Do NOT reach for Single Table Inheritance in these cases, and the reason
matters more than the rule.

- **The hierarchy is wide and still growing.** A base type with a dozen
  subclasses, each contributing several unique fields, produces a table with
  a very large column count, most of it null for any given row. Beyond a
  point that varies by engine, this stops being a modelling inconvenience
  and starts being an operational one, see dimension 11 for the concrete
  limits. Class Table Inheritance scales the column count per class instead
  of per hierarchy, and is the honest answer here.
- **Subtypes need column-level `NOT NULL`, `CHECK`, or foreign key
  constraints that only apply to that subtype.** The relational engine cannot
  express "this column is mandatory only when `vehicle_type = 'truck'`" as a
  plain column constraint in most engines. A workaround exists in engines
  that support partial or filtered constraints, covered in dimension 8, but
  where that support is absent the integrity guarantee genuinely weakens, and
  Class Table Inheritance restores it by giving each subtype its own table
  with its own honest constraints.
- **Concrete leaf tables are queried far more often than the shared
  hierarchy, and never together.** If nothing in the application ever asks
  "give me every vehicle" and every query is scoped to one concrete subtype,
  the join-avoidance benefit that motivates STI never materialises, while the
  wide-table cost still applies. Concrete Table Inheritance, one table per
  leaf class with no shared table at all, fits this access pattern better.
- **Different subtypes belong to genuinely different bounded contexts or
  services.** Forcing unrelated domains to share a physical table because
  they both happen to specialise a common abstract idea couples their schema
  migrations and their locking behaviour for no domain reason. Separate
  aggregates, or separate services, are the honest boundary here, not a
  shared table.
- **The team needs strict, engine-enforced data integrity over the operational
  simplicity of one table**, for example a financial ledger where a wrong or
  missing constraint has direct monetary consequences. The nullable,
  application-enforced validation this pattern trades for its simplicity is
  the wrong trade in that context.
- **Regulatory or access-control requirements demand physically separate
  storage per subtype**, for example one subtype carrying data subject to a
  stricter retention or residency rule than its siblings. A shared table
  makes per-subtype storage policy, encryption at rest scoped to a column
  set, or per-subtype access grants awkward to express, because the database
  grant system operates at the table level, not the conditional-row level, in
  most engines.
- **The object model already has, or is trending toward, a composition
  relationship rather than an inheritance one.** If "a truck has cargo
  capacity" is more honestly modelled as "a vehicle has an optional cargo
  profile" than as "a truck is a kind of vehicle", a separate related table
  joined optionally is the better shape, and it is not this pattern at all,
  it is ordinary normalisation.

## 5. Structure

Four participants, named by the role each plays.

- **Root table.** The single physical table backing the whole hierarchy. Its
  columns are the union of every field declared anywhere in the hierarchy,
  the shared fields declared on the base type plus every field declared on
  every subtype.
- **Discriminator column.** One column in the root table whose value records
  which concrete subtype a given row represents. It is typically a short
  string or a small integer code, and it is the one piece of relational data
  that carries the object model's type information across the
  object-relational boundary.
- **Base type.** The in-memory class or interface that declares the shared
  fields and behaviour. It maps to the root table as a whole, minus the
  columns that belong only to specific subtypes.
- **Concrete subtype.** An in-memory class that extends the base type and
  declares its own additional fields. Each concrete subtype maps to the same
  root table, reading and writing only the columns relevant to it, plus the
  shared columns, and is selected on load by matching the discriminator
  column's value.

The defining structural fact is that there is exactly one table and exactly
one primary key space for the entire hierarchy, no matter how many concrete
subtypes exist. A row's "identity" as a particular subtype is recoverable
purely from the discriminator column's value, and the mapping layer, whether
hand-written or an ORM, is responsible for routing a loaded row to the correct
in-memory class and for leaving every column that subtype does not use null
on write.

## 6. ASCII structure diagram

```
   +----------------------------------------------------------+
   |                       vehicles (table)                   |
   |------------------------------------------------------------
   | id             INTEGER  PRIMARY KEY                       |
   | vehicle_type   TEXT     NOT NULL   <- discriminator column|
   | make           TEXT     NOT NULL   <- shared, base type   |
   | model          TEXT     NOT NULL   <- shared, base type   |
   | year           INTEGER  NOT NULL   <- shared, base type   |
   | door_count     INTEGER  NULL       <- Car only            |
   | has_sidecar    INTEGER  NULL       <- Motorcycle only     |
   | cargo_capacity_kg INTEGER NULL     <- Truck only          |
   +----------------------------------------------------------+
                              ^
                              | maps every row to one of three
                              | in-memory classes, chosen by
                              | reading vehicle_type
                              |
        +---------------------+---------------------+
        |                     |                     |
   +-----------+        +------------+        +-----------+
   |  Vehicle  |<-------|    Car     |        | Motorcycle|
   | (base)    | extends| door_count |        |has_sidecar|
   +-----------+        +------------+        +-----------+
        ^
        | extends
        |
   +------------+
   |   Truck    |
   | cargo_kg   |
   +------------+

   Every row lives in one table. A Car row has NULL in
   has_sidecar and cargo_capacity_kg. A Truck row has NULL
   in door_count and has_sidecar. The discriminator column
   is the only column read before deciding which class to
   instantiate.
```

## 7. Dynamics

The runtime flow that matters most is the read path, because it is where the
discriminator column drives a decision the schema itself cannot make. The
write path is simpler and is shown second.

```
Application code       Mapping layer            vehicles table
     |                       |                          |
     |-- findAll() -------->|                            |
     |                       |-- SELECT * FROM vehicles ->|
     |                       |<-- rows[] -----------------|
     |                       |                            |
     |                       |  for each row:             |
     |                       |    read vehicle_type       |
     |                       |    switch on its value     |
     |                       |    build Car, Motorcycle,  |
     |                       |    or Truck instance,      |
     |                       |    reading only that       |
     |                       |    subtype's columns       |
     |                       |                            |
     |<-- Vehicle[] ---------|                            |
     |   (mixed concrete     |                            |
     |    subtypes, all      |                            |
     |    satisfying the     |                            |
     |    base interface)    |                            |
     |                       |                            |
     |-- save(aTruck) ------>|                            |
     |                       |-- INSERT INTO vehicles     |
     |                       |   (vehicle_type, make,     |
     |                       |    model, year,            |
     |                       |    cargo_capacity_kg)      |
     |                       |   VALUES                   |
     |                       |   ('truck', ..., ..., ..., |
     |                       |    aTruck.cargoCapacityKg) |
     |                       |   -- door_count and        |
     |                       |   -- has_sidecar are left  |
     |                       |   -- out of the column     |
     |                       |   -- list, defaulting NULL |
     |                       |------------------------->  |
     |<-- ack ---------------|                            |
```

Two timing and correctness notes worth stating plainly. First, the
discriminator column must be read before any other column is interpreted,
because every other column's meaning depends on it, a `door_count` of `4`
means nothing on a row whose `vehicle_type` is `motorcycle`, it simply should
not be read. Second, an `INSERT` should write only the columns the concrete
subtype owns plus the shared columns, leaving the rest to the column
default, almost always `NULL`, rather than writing an explicit `NULL` for
every irrelevant column. Explicitly writing every column on every insert
works too, but it makes future column additions to sibling subtypes require
touching every other subtype's insert statement, which quietly reintroduces
some of the coupling the pattern was meant to avoid.

## 8. Implementation variants

**Hand-written mapping, no ORM.** The mapping layer is a small amount of code
that switches on the discriminator column after a `SELECT *` and constructs
the matching class. This is the clearest way to see the pattern with nothing
hidden, and is the shape used in dimension "Code examples" below. It costs
more boilerplate per subtype than an ORM, and it is the right choice when a
project deliberately avoids an ORM's mapping layer.

**ORM-managed single table strategy.** Hibernate and the wider JPA ecosystem
implement this as `@Inheritance(strategy = InheritanceType.SINGLE_TABLE)` with
an optional `@DiscriminatorColumn` and a per-subclass `@DiscriminatorValue`
(Baeldung, "Hibernate Inheritance Mapping",
https://www.baeldung.com/hibernate-inheritance verified 2026-08-02). Entity
Framework in the .NET ecosystem calls the identical mapping Table-Per-Hierarchy
(TPH) and infers a discriminator column named `Discriminator` by convention
unless configured otherwise. The ORM generates the conditional `SELECT`
column lists and the discriminator-driven object construction automatically,
which removes the hand-written mapping's boilerplate at the cost of the ORM's
own configuration surface and its own set of gotchas, several of which are
covered in dimension 11.

**Rails ActiveRecord's convention-based STI.** Rails triggers the pattern
automatically the moment a table has a column literally named `type`, no
explicit configuration required. A model class extending another
ActiveRecord model that maps to a table with a `type` column is treated as an
STI subclass, and Rails writes the class name into that column on create and
filters by it on every query issued through the subclass (Ruby on Rails API
documentation, `ActiveRecord::Inheritance`,
https://api.rubyonrails.org/classes/ActiveRecord/Inheritance.html verified
2026-08-02; Ruby on Rails Guides, "Active Record Associations",
https://guides.rubyonrails.org/association_basics.html verified 2026-08-02).
The column name storing the discriminator can be changed by overriding
`Base.inheritance_column`, and the absence of a `type` column simply turns
STI off for that table with no error, which is a convention worth knowing
because a typo in a migration, `typ` instead of `type`, silently produces a
plain, non-polymorphic table rather than a loud failure.

**Discriminator as an integer code rather than a string.** Storing a small
integer, mapped to subtype names in application code, saves bytes per row and
avoids a string comparison in the query planner's filter, at the cost of
needing a lookup table or an enum definition kept in sync between the schema
and the code. This trade matters more at very large row counts than at
moderate ones, and is a genuine micro-optimisation rather than a structural
choice.

**Partial or filtered constraints to recover per-subtype `NOT NULL`.**
PostgreSQL's partial indexes and check constraints, and SQL Server's filtered
indexes, can express "this column must be non-null when the discriminator
equals this value" as `CHECK (vehicle_type <> 'truck' OR cargo_capacity_kg IS
NOT NULL)` or an equivalent partial unique index. This recovers some of the
integrity that dimension 3 lists as sacrificed, at the cost of a
constraint whose intent is not obvious from the column definition alone and
that must be updated whenever a new subtype is added.

**Hybrid single table with a JSON or JSONB overflow column.** Rather than
adding a physical column for every rare subtype-specific field, some
implementations keep a small set of common subtype fields as real columns and
push a long tail of rarely-queried, subtype-specific attributes into one
`attributes JSONB` column. This bounds the physical column count growth that
dimension 11 flags as the pattern's sharpest failure mode, at the cost of
losing native column typing, indexing, and constraint support for whatever
moves into the JSON column. This is a genuine and increasingly common
variant in PostgreSQL-based systems, but it is a deliberate hybrid, not the
textbook form of the pattern, and should be named as such in code review
rather than presented as plain STI.

## 9. Known production uses

**Ruby on Rails ActiveRecord.** Rails treats any table carrying a column named
`type` as an STI hierarchy by convention, writing the subclass name into that
column on `create` and automatically scoping subsequent queries issued
through a subclass to matching rows. The framework's own documentation states
that Active Record allows inheritance by storing the class name in a column
that defaults to `type`, and that the column name can be changed by
overriding `Base.inheritance_column`. Ruby on Rails API documentation,
`ActiveRecord::Inheritance`,
https://api.rubyonrails.org/classes/ActiveRecord/Inheritance.html verified
2026-08-02. Supporting detail on query scoping and the discriminator column's
role in associations, Ruby on Rails Guides, "Active Record Associations",
section on Single Table Inheritance, https://guides.rubyonrails.org/association_basics.html
verified 2026-08-02.

**WordPress core, the `wp_posts` table.** Every post, page, media attachment,
navigation menu item, and revision in a WordPress site is stored as a row in
the single `wp_posts` table, differentiated by the `post_type` column. A blog
post and a static page share every core column, title, content, author,
timestamps, and status, and are distinguished purely by the value of
`post_type`, which is the discriminator-column shape this pattern describes,
applied to content types rather than to an object-oriented class hierarchy in
the traditional sense. Description of the `post_type` column's role across
posts, pages, and attachments verified via live web search of WordPress
developer documentation and hosting-provider database guides, 2026-08-02.

**Hibernate and the Jakarta Persistence single table strategy.** Hibernate
implements `InheritanceType.SINGLE_TABLE` as the default inheritance mapping
strategy when none is specified, mapping every entity in a class hierarchy to
one physical table and using a discriminator column, `DTYPE` by default, to
determine which entity class a given row instantiates as. The strategy is
configured with `@Inheritance(strategy = InheritanceType.SINGLE_TABLE)` on the
root entity and `@DiscriminatorColumn` plus a per-subclass
`@DiscriminatorValue` for customisation. Baeldung, "Hibernate Inheritance
Mapping", https://www.baeldung.com/hibernate-inheritance verified 2026-08-02.

## 10. Consequences

Positive.

- Querying across the entire hierarchy, or any subset of it, needs no join,
  because every row lives in one table regardless of concrete subtype.
- Polymorphic foreign keys from unrelated tables point at one primary key
  space and one table, rather than needing a type tag plus a
  conditionally-joined table.
- Adding a new subtype whose fields already fit within the existing column
  set costs nothing structurally, no new table, no new migration to add a
  join.
- The whole hierarchy shares one set of indexes, one set of table-level
  statistics for the query planner, and one place to look when diagnosing a
  slow query against the hierarchy.
- Moving a row from one subtype to another, a car that gets reclassified,
  is a single `UPDATE` changing the discriminator and the relevant columns,
  rather than a delete-and-insert across two tables.

Negative.

- The physical column count grows with the union of every subtype's fields,
  not with any one subtype's fields, so a wide, growing hierarchy produces a
  wide, growing table regardless of how narrow any individual subtype is.
- Every subtype-specific column is necessarily nullable, and a database's
  native `NOT NULL` constraint cannot express "mandatory for this subtype
  only" without a conditional check constraint, so integrity for
  subtype-specific fields moves into application or ORM validation code.
- A row carries dead cells for every column its concrete subtype does not
  use, which grows the average row width and, past a threshold that varies
  by engine, can push rows toward or across a page-size boundary.
- The table's schema is not self-describing to a reader without the
  discriminator column's semantics in mind, a column can be simultaneously
  present, non-null in principle, and irrelevant for a given row.
- Access-control and data-residency policy that should differ by subtype is
  awkward to express, because grants and column-level policy in most engines
  operate on the whole table, not on rows filtered by a discriminator value.

## 11. Failure modes and misuse

**Column count creep.** Symptom. A migration history that adds two or three
new nullable columns every quarter, and a `SELECT *` against the table that
now returns eighty or more columns, most `NULL` for any given row. Cause.
Every new subtype, or every new field on an existing subtype, was added as a
physical column with no upper bound considered. Fix. Set an explicit column
count or row-width budget for the table at design time, and route rarely-used
or long-tail subtype fields into the JSON overflow variant from dimension 8,
or migrate the whole hierarchy to Class Table Inheritance once the budget is
exceeded.

**Silent integrity loss on a mandatory subtype field.** Symptom. A production
incident where a `Truck` row was saved with a null `cargo_capacity_kg`, a
field the business considers mandatory for trucks, and nothing in the
database rejected the write. Cause. The column is necessarily nullable at
the physical level because other subtypes never populate it, so a plain
`NOT NULL` constraint cannot be applied, and the application-level validation
that was meant to enforce mandatory-ness was skipped on one code path, most
often a bulk import or an administrative script that bypassed the normal
model layer. Fix. Add a conditional check constraint where the engine
supports one, per dimension 8, so the database itself refuses the invalid
row regardless of which code path wrote it, and treat any write path that
bypasses the model layer, including bulk loaders, as a path that must also
go through validation.

**Discriminator value drift between code and data.** Symptom. A subtype's
rows silently stop being returned by queries scoped to that subtype after a
class rename, or a report shows an "unknown vehicle type" bucket that grows
over time. Cause. The in-memory class name or the configured discriminator
value was changed, most often during a rename refactor, without a
corresponding data migration updating existing rows' discriminator column
values. Fix. Treat a discriminator value as a stable, versioned identifier
independent of the class name that happens to use it today, never derive it
implicitly from `getClass().getName()` or an equivalent reflection call in a
context where the class might be renamed, and write an explicit migration
whenever a discriminator value must change.

**Polymorphic count and aggregate queries returning wrong totals.** Symptom.
A dashboard metric such as "total vehicles" or "average cargo capacity" that
mysteriously includes or excludes rows it should not. Cause. An aggregate
query, most often `AVG()` or `SUM()` over a subtype-specific nullable
column, was run without a `WHERE` clause scoping it to the relevant
discriminator value, so the aggregate silently treats every other subtype's
`NULL` in that column as excluded from the average's denominator by SQL's
null-handling rules, which produces a number that is correct in isolation but
misleading about what population it describes. Fix. Every aggregate over a
subtype-specific column must carry an explicit discriminator filter, and
that filter should be asserted by a test, not left to the query author's
memory.

**ORM `SELECT *` cost on a very wide table.** Symptom. A hierarchy that
started narrow and grew wide over years now produces a noticeably slower
"list all" query than it did at launch, even though row count grew only
modestly. Cause. Most ORMs implementing the single table strategy issue a
`SELECT` covering every mapped column across every subtype on a
whole-hierarchy query, regardless of which concrete subtypes are actually
present in the result set, so query cost scales with total column count, not
with the columns any individual row actually uses. Fix. Where the ORM
supports it, scope the query to the specific columns needed by the calling
code, or split the query per subtype when a whole-hierarchy listing view
genuinely only needs the shared base columns.

**Table lock contention from schema migrations on a hot table.** Symptom. A
routine "add a column for the new subtype" migration causes a production
incident, either a lock timeout or a visible latency spike, on a table
otherwise unrelated to the new subtype's rollout. Cause. Because every
subtype in the hierarchy shares one physical table, a schema change for any
one subtype is a schema change against the whole table, including rows and
traffic belonging to every other subtype, and on engines or table sizes
where an `ALTER TABLE ADD COLUMN` is not a fast metadata-only operation, that
change can hold a lock affecting unrelated read and write traffic. Fix.
Confirm the target engine and table size support the fast-path column
addition before deploying, prefer default-null column additions which are
metadata-only on most modern engines, and rehearse migrations against a
production-sized copy before running them against the live table.

## 12. Trade-off matrix

Compared against the two other members of Fowler's own inheritance-mapping
family, plus one structurally different alternative.

| Force | Single Table Inheritance | Class Table Inheritance | Concrete Table Inheritance | Composition instead of inheritance |
|---|---|---|---|---|
| Cross-subtype query cost | No join, one table | Join per level in the hierarchy | No join, but requires a UNION across leaf tables | Depends on the composed relation, usually one join |
| Single-subtype query cost | One table, discriminator filter | One join to the shared base table | One table, no filter needed | One table plus a conditional join |
| Column count growth | Grows with the whole hierarchy's union | Grows per class, spread across tables | Grows per leaf class, duplicated shared columns | Grows per composed relation, not per subtype |
| Native NOT NULL per subtype field | Not expressible without a conditional check | Fully expressible, each table owns its columns | Fully expressible, each table owns its columns | Fully expressible |
| Polymorphic foreign keys from elsewhere | One key space, trivial to reference | Base table's key is the stable reference point | No single key space, needs a lookup or a shared ID generator | Depends on the design, often needs its own scheme |
| Schema migration blast radius | Whole table, every subtype affected | Scoped to one class's table | Scoped to one leaf class's table | Scoped to the composed relation |
| Storage efficiency per row | Nullable columns for unused fields | No wasted columns per row | No wasted columns per row | No wasted columns, but extra join overhead |
| Identity when a row changes subtype | One UPDATE | Requires moving rows between tables | Requires delete-and-reinsert across tables | Depends on the design |
| Reader comprehension of the schema alone | Requires knowing discriminator semantics | Self-describing per table | Self-describing per table, duplication visible | Self-describing, relationship-based |

Reading of the table. Single Table Inheritance is the strongest choice when
cross-subtype reads outnumber single-subtype reads and the hierarchy stays
narrow and shallow. Class Table Inheritance is the strongest choice when
per-subtype integrity constraints and a narrower per-class schema matter more
than join-free reads. Concrete Table Inheritance is the strongest choice when
subtypes are queried almost exclusively in isolation and the hierarchy will
never need a genuine "give me everything" query. Composition is the strongest
choice when the relationship between the shared concept and the specialised
data is better described as "has a" than "is a" in the first place, which is
a modelling question that precedes any of the three mapping patterns.

## 13. Related and incompatible patterns

- **Class Table Inheritance.** A direct sibling in the same catalog family,
  solving the identical problem with the opposite trade, one table per class
  joined by a shared key instead of one wide table. The two are mutually
  exclusive mapping choices for the same hierarchy, a team picks one, not
  both, though a large system with many independent hierarchies can
  reasonably use Single Table Inheritance for a narrow, stable hierarchy and
  Class Table Inheritance for a wide, evolving one elsewhere in the same
  schema.
- **Concrete Table Inheritance.** The third sibling in the family, and the
  pattern to reach for when subtypes are almost never queried together. It
  is incompatible with Single Table Inheritance in the same sense as Class
  Table Inheritance, they are alternative answers to one mapping decision.
- **Active Record.** Frequently paired with Single Table Inheritance in
  practice, most visibly in Ruby on Rails, because an Active Record object
  already carries its own persistence logic, and STI's discriminator-driven
  construction slots naturally into an Active Record subclass's constructor
  or class-level factory behaviour. Fowler's own catalog entry cross
  references Active Record as a typical partner. Active Record is not
  required to use STI, and STI does not require Active Record, but the two
  are commonly implemented together because both favour convention over
  configuration.
- **Identity Field.** A prerequisite. Every row in the shared table needs a
  stable identifier independent of its subtype, and Identity Field is the
  pattern describing how that identifier is generated and mapped, whether an
  auto-incrementing integer, a UUID, or a sequence.
- **Foreign Key Mapping.** Composes cleanly on top. An association from the
  hierarchy to another table, or from another table into the hierarchy,
  benefits directly from STI's single key space, because the foreign key
  needs no accompanying discriminator to know which table to join against,
  unlike a polymorphic association over Class or Concrete Table Inheritance.
- **Layer Supertype.** Often the base class in an STI hierarchy is itself
  built on top of a Layer Supertype providing common persistence
  infrastructure, timestamps, soft-delete flags, and the like, shared across
  every hierarchy in the application, not only this one.
- **Single Responsibility Principle, in tension.** The discriminator-driven
  construction logic in the mapping layer accumulates one branch per
  subtype, and as the hierarchy grows that switch or match statement becomes
  a place where unrelated subtype construction logic is packed into one
  method. This is a genuine tension rather than an incompatibility, and the
  usual resolution is a registry-based dispatch keyed by the discriminator
  value rather than a single growing conditional, which mirrors the
  registry-backed variant described in the Factory Method entry's dimension
  8.
- **Discriminated Union or Sum Type, at the language level.** In languages
  with algebraic data types, Rust enums, Swift enums with associated values,
  Kotlin sealed classes, the in-memory side of an STI hierarchy is
  frequently modelled as a discriminated union rather than a class
  hierarchy, and the persistence-layer discriminator column maps directly
  onto the union's tag. The relational pattern and the language-level
  construct are a strong conceptual match even when the object-oriented
  inheritance vocabulary this pattern was named in does not apply literally.

## 14. Refactoring path in and out

Introducing the pattern into a schema that does not have it, most often
because separate, poorly related tables have organically converged toward a
shared shape. Ordered steps.

1. Confirm the candidate tables genuinely represent subtypes of one concept,
   not merely tables that happen to share some column names by coincidence.
   A shared column name is not evidence of a shared concept.
2. Design the discriminator column and its value set before writing any
   migration. Decide the column's name, type, and whether values are strings
   or small integers, and write down the mapping between discriminator value
   and concrete class, because this mapping becomes a contract the whole
   codebase depends on.
3. Create the new, wider root table with the union of every source table's
   columns plus the discriminator column, without dropping the source
   tables yet.
4. Migrate data with an explicit `INSERT ... SELECT` per source table,
   populating the discriminator column with that source table's assigned
   value and leaving every column that source table does not own as
   `NULL`. Verify row counts before and after per source table match
   exactly.
5. Update the mapping layer to read and write the new table, gated behind a
   feature flag if the migration is happening against a live system, so
   reads and writes can be switched over independently and rolled back if
   the migration reveals a data problem.
6. Once the new table is verified correct and the application is reading
   from it exclusively, drop the old source tables in a separate,
   reversible migration, keeping a backup or an archived copy per the
   project's data retention policy rather than deleting outright.

Removing the pattern when it stops earning its place, typically because
dimension 11's column-count creep symptom has appeared. This is the reverse
of the introduction path, and is best framed as a migration toward Class
Table Inheritance rather than a full removal of the shared concept.

1. Identify the natural split points in the current wide table, usually the
   discriminator values that carry the most subtype-specific columns.
2. Create a shared base table carrying only the columns every subtype
   actually uses, plus the identity field and the discriminator, and one
   table per subtype carrying that subtype's specific columns, keyed by the
   same identifier as the base table's row.
3. Migrate data with an `INSERT ... SELECT` splitting each row into its base
   table row and its subtype table row, filtering the subtype table insert
   by the discriminator value.
4. Update the mapping layer to join the base table to the relevant subtype
   table on load, and to write both rows on save, again gated behind a flag
   if this is a live migration.
5. Verify with a row-count and column-value audit that the split preserved
   every field's value exactly, then drop the wide table once reads and
   writes are fully cut over.

## 15. Testing and verification

This is judgement drawn from how object-relational mapping bugs actually
surface in practice, not from a single authoritative source.

Easier because of the pattern.

- A test asserting polymorphic behaviour across the whole hierarchy needs to
  set up only one table, with no join fixtures to coordinate across
  multiple tables.
- Round-trip tests, save an object, reload it, assert equality, are simple
  to write because there is exactly one table and one row per object,
  rather than a base row plus a subtype row that must be assembled
  correctly to compare.

Harder because of the pattern.

- A test cannot rely on the database to catch a missing mandatory field for
  one subtype, because the column is nullable at the physical level, so the
  application-level or ORM-level validation for that field needs its own
  explicit test, per subtype, asserting the save is rejected.
- A schema-level test verifying "this column is only ever populated for this
  discriminator value" is not something the database enforces by default, so
  a data-integrity test suite for a mature STI table needs an explicit
  assertion per subtype-specific column confirming it is null everywhere the
  discriminator does not match, catching the class of bug where a bulk
  update or a raw SQL migration wrote into the wrong subtype's column by
  mistake.

Techniques that apply.

- **Per-discriminator round-trip test.** One test per concrete subtype,
  constructing an instance, saving it, reloading it by primary key, and
  asserting both the object's fields and the raw row's discriminator value
  match expectations. This catches the discriminator-drift failure mode from
  dimension 11 directly, because a renamed class whose discriminator value
  was not migrated will fail this test on reload rather than silently
  vanishing from subtype-scoped queries in production.
- **Cross-subtype column isolation test.** For each subtype-specific column,
  a query asserting that column is null for every row whose discriminator
  does not match that column's owning subtype. Run this as a data-integrity
  check, not only against test fixtures, so it can also run periodically
  against production data to catch drift introduced outside the normal
  application code path.
- **Mandatory-field-per-subtype test.** For every field the business
  considers mandatory for a specific subtype, an explicit test attempting to
  save an instance of that subtype with the field unset, and asserting the
  save is rejected. This is the direct test for the "silent integrity loss"
  failure mode, and it should run against every code path capable of
  writing a row, including any bulk import or administrative script, not
  only the primary model layer.
- **Aggregate query correctness test.** For any reporting query that
  aggregates a subtype-specific column, a test asserting the aggregate's
  result is unaffected by the presence of other subtypes' rows in the table,
  populating the test fixture with rows from every subtype and confirming
  the aggregate scoped to one subtype ignores the others entirely.

## 16. Observability signals

The pattern's central risk, an ever-widening table that grows less legible
over time, is one that surfaces slowly, so the most useful observability
signals are trend-based rather than point-in-time alerts.

What to record.

- Column count on the root table, tracked over time as part of schema
  documentation or a periodic schema-audit job, so a slow creep toward the
  budget set in dimension 11's fix is visible before it becomes a crisis
  rather than after.
- Row-level null density per subtype-specific column, the proportion of rows
  where that column is populated versus null. A column whose populated
  proportion keeps shrinking as new, unrelated subtypes are added is a
  concrete signal that the table is trending toward the wide, mostly-empty
  shape dimension 11 warns against.
- Query latency for the whole-hierarchy `SELECT`, tracked separately from
  latency for discriminator-filtered queries, because the two should diverge
  as the table widens, whole-hierarchy queries paying the full column-width
  cost on every row while filtered queries pay it only for matching rows.
- Discriminator value distribution, a count of rows per discriminator value,
  refreshed periodically. An unexpected discriminator value appearing in
  this distribution, one not present in the application's known subtype set,
  is the direct signal for the discriminator-drift failure mode from
  dimension 11.
- Schema migration duration and lock wait time for `ALTER TABLE` operations
  against the root table, because this table is shared infrastructure for
  every subtype and a slow migration against it has a wider blast radius
  than a migration against a table owned by one feature alone.

A healthy instance on a dashboard. Column count grows slowly, in step with
the pace of genuinely new subtypes rather than
individual features bolting on ad hoc fields. Null density per column stays
roughly stable over time for a given subtype's share of total rows.
Whole-hierarchy query latency stays flat relative to total row count, not
relative to column count. The discriminator value distribution contains only
known, expected values.

A failing instance. Column count grows every migration cycle with no
corresponding growth in distinct subtypes, which points at fields that
should have been normalised elsewhere being added directly to the shared
table instead. An unfamiliar discriminator value appears in the
distribution, pointing at either a data-entry bug, a partially-completed
migration, or an application deploy that introduced a new subtype without
updating every downstream consumer of the discriminator value set. A
schema migration against this table starts taking measurably longer or
starts holding locks longer than it used to, at a table size that has not
grown proportionally, which points toward the table approaching a row-width
or page-size boundary relevant to the specific database engine in use.

## 17. Security and privacy implications

This is judgement. The pattern is largely neutral on security in the
classical sense, no new network surface or authentication concern, but it has
two concrete implications once real data governance requirements meet a
shared table, and inventing more than these would overstate the pattern's
actual attack surface.

**Coarse-grained access control across subtypes.** Because every subtype's
data lives in one physical table, database-level access control, `GRANT`
statements, row-level security policies, and column-level encryption
configuration, applies most naturally at the table granularity, not at the
per-subtype granularity a business requirement might actually need. A
hierarchy where one subtype's rows carry more sensitive data than its
siblings, for example a `Vehicle` hierarchy where a hypothetical
`PersonalVehicle` subtype carries an owner's home address while a
`FleetVehicle` subtype does not, needs deliberate handling, either a
row-level security policy keyed by the discriminator column where the engine
supports one, PostgreSQL's row security policies being the clearest example,
or a decision to split that specific subtype into its own table precisely
because its data sensitivity genuinely differs from its siblings. Treating
"they are all vehicles" as reason enough to keep sensitive and non-sensitive
subtypes in one table without an access-control plan is the failure mode to
design against.

**Bulk data export and deletion complexity.** Right-to-erasure and
data-portability requirements under privacy regulation typically operate at
the level of a specific subject's records across a domain concept, and a
shared table's discriminator-conditional column semantics make a generic
"export everything for this row" or "delete everything for this row"
operation somewhat less obvious to implement correctly than it would be
against a narrower, single-purpose table, because the export or deletion
logic must still understand which columns apply to the row's specific
discriminator value rather than exporting or nulling every column uniformly.
This is a usability concern for whoever writes the erasure tooling, not a
structural vulnerability, and it is fully solvable with a discriminator-aware
export function, but it is a genuine extra step compared to a schema where
each subtype already has its own table.

On the pattern's own attack surface beyond these two points, there is
nothing further to add honestly. Single Table Inheritance introduces no new
injection surface, no new authentication concern, and no new network
exposure of its own; those risks, where present, come from how queries
against the table are constructed and parameterised, which is a general SQL
hygiene concern applying equally to any table, not one specific to this
pattern.

## 18. References

1. Martin Fowler. *Patterns of Enterprise Application Architecture*.
   Addison-Wesley, 2002. ISBN 0-321-12742-0. Object-Relational Structural
   Patterns, catalog entry "Single Table Inheritance",
   https://martinfowler.com/eaaCatalog/singleTableInheritance.html
   Verified 2026-08-02. Source of the pattern's name, intent, and its place
   alongside Class Table Inheritance and Concrete Table Inheritance.
2. Ruby on Rails project. *Ruby on Rails API documentation*,
   `ActiveRecord::Inheritance`.
   https://api.rubyonrails.org/classes/ActiveRecord/Inheritance.html
   Verified 2026-08-02. Source for the `type` column convention, the
   `Base.inheritance_column` override, and the class-name-to-column-value
   mapping described in dimensions 8 and 9.
3. Ruby on Rails project. *Ruby on Rails Guides*, "Active Record
   Associations", section on Single Table Inheritance.
   https://guides.rubyonrails.org/association_basics.html
   Verified 2026-08-02. Source for the query-scoping behaviour and the
   association-handling caveats referenced in dimension 9.
4. Baeldung. "Hibernate Inheritance Mapping".
   https://www.baeldung.com/hibernate-inheritance
   Verified 2026-08-02. Source for the `InheritanceType.SINGLE_TABLE`
   default strategy, the `DTYPE` discriminator column convention, and the
   `@DiscriminatorColumn` and `@DiscriminatorValue` annotations described in
   dimensions 8 and 9.
5. WordPress developer and hosting documentation on the `wp_posts` table and
   the `post_type` discriminator column, confirmed via live search of
   WordPress core database structure references, verified 2026-08-02.
   Source for the WordPress production use in dimension 9. This claim is
   corroborated across multiple independent WordPress documentation and
   hosting-provider sources rather than a single canonical page, because
   WordPress core does not publish one authoritative schema reference page
   for `wp_posts`.
6. PostgreSQL Global Development Group. *PostgreSQL Documentation*, chapter
   on partial indexes and `CHECK` constraints. Cited as engineering
   judgement in dimension 8 for the conditional-constraint variant that
   recovers per-subtype `NOT NULL` semantics; readers should consult the
   current PostgreSQL documentation for their deployed version's exact
   syntax rather than relying on this entry for syntax specifics.

## Code examples

Three languages, each showing the pattern's defining behaviour, a single
table, one discriminator column, and polymorphic construction on read. Python
runs against a real, in-process SQLite database, which is the closest of the
three to how the pattern behaves against an actual relational engine. Java and
TypeScript simulate the table as an in-memory list of row records to keep the
examples runnable without an external database dependency, while preserving
the exact same discriminator-driven mapping logic a real ORM or hand-written
data access layer would use against a live table. Go is omitted because the
pattern is a mapping decision between an object hierarchy and a relational
schema, and Go's preference for composition over inheritance makes the
classical subclass hierarchy this pattern maps from awkward to express
idiomatically, the more natural Go shape being a single struct with an
embedded interface for the subtype-specific behaviour, which sits closer to
the Strategy pattern than to this one.

### Python

```python
import sqlite3
from dataclasses import dataclass


@dataclass
class Vehicle:
    id: int
    make: str
    model: str
    year: int


@dataclass
class Car(Vehicle):
    door_count: int


@dataclass
class Motorcycle(Vehicle):
    has_sidecar: bool


@dataclass
class Truck(Vehicle):
    cargo_capacity_kg: int


SCHEMA = """
CREATE TABLE vehicles (
    id INTEGER PRIMARY KEY,
    vehicle_type TEXT NOT NULL,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    year INTEGER NOT NULL,
    door_count INTEGER,
    has_sidecar INTEGER,
    cargo_capacity_kg INTEGER
)
"""


def insert_car(conn: sqlite3.Connection, car: Car) -> None:
    conn.execute(
        "INSERT INTO vehicles (id, vehicle_type, make, model, year, door_count) "
        "VALUES (?, 'car', ?, ?, ?, ?)",
        (car.id, car.make, car.model, car.year, car.door_count),
    )


def insert_motorcycle(conn: sqlite3.Connection, m: Motorcycle) -> None:
    conn.execute(
        "INSERT INTO vehicles (id, vehicle_type, make, model, year, has_sidecar) "
        "VALUES (?, 'motorcycle', ?, ?, ?, ?)",
        (m.id, m.make, m.model, m.year, int(m.has_sidecar)),
    )


def insert_truck(conn: sqlite3.Connection, t: Truck) -> None:
    conn.execute(
        "INSERT INTO vehicles (id, vehicle_type, make, model, year, cargo_capacity_kg) "
        "VALUES (?, 'truck', ?, ?, ?, ?)",
        (t.id, t.make, t.model, t.year, t.cargo_capacity_kg),
    )


def load_all(conn: sqlite3.Connection) -> list[Vehicle]:
    rows = conn.execute(
        "SELECT id, vehicle_type, make, model, year, door_count, "
        "has_sidecar, cargo_capacity_kg FROM vehicles"
    ).fetchall()
    result: list[Vehicle] = []
    for (vid, vtype, make, model, year, doors, sidecar, cargo) in rows:
        if vtype == "car":
            result.append(Car(vid, make, model, year, doors))
        elif vtype == "motorcycle":
            result.append(Motorcycle(vid, make, model, year, bool(sidecar)))
        elif vtype == "truck":
            result.append(Truck(vid, make, model, year, cargo))
        else:
            raise ValueError(f"unknown discriminator value: {vtype}")
    return result


def total_cargo_capacity(conn: sqlite3.Connection) -> int:
    # Aggregate filtered by the discriminator, per dimension 11's warning.
    row = conn.execute(
        "SELECT COALESCE(SUM(cargo_capacity_kg), 0) FROM vehicles "
        "WHERE vehicle_type = 'truck'"
    ).fetchone()
    return row[0]


if __name__ == "__main__":
    conn = sqlite3.connect(":memory:")
    conn.execute(SCHEMA)
    insert_car(conn, Car(1, "Honda", "Civic", 2023, 4))
    insert_motorcycle(conn, Motorcycle(2, "Ducati", "Monster", 2024, False))
    insert_truck(conn, Truck(3, "Volvo", "FH16", 2022, 12000))
    conn.commit()

    for vehicle in load_all(conn):
        print(vehicle)

    print("total cargo capacity:", total_cargo_capacity(conn), "kg")
    conn.close()
```

### Java

```java
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

abstract class Vehicle {
    final int id;
    final String make;
    final String model;
    final int year;

    Vehicle(int id, String make, String model, int year) {
        this.id = id;
        this.make = make;
        this.model = model;
        this.year = year;
    }

    abstract String discriminator();
}

final class Car extends Vehicle {
    final int doorCount;

    Car(int id, String make, String model, int year, int doorCount) {
        super(id, make, model, year);
        this.doorCount = doorCount;
    }

    String discriminator() {
        return "car";
    }

    public String toString() {
        return "Car{" + make + " " + model + ", doors=" + doorCount + "}";
    }
}

final class Motorcycle extends Vehicle {
    final boolean hasSidecar;

    Motorcycle(int id, String make, String model, int year, boolean hasSidecar) {
        super(id, make, model, year);
        this.hasSidecar = hasSidecar;
    }

    String discriminator() {
        return "motorcycle";
    }

    public String toString() {
        return "Motorcycle{" + make + " " + model + ", sidecar=" + hasSidecar + "}";
    }
}

final class Truck extends Vehicle {
    final int cargoCapacityKg;

    Truck(int id, String make, String model, int year, int cargoCapacityKg) {
        super(id, make, model, year);
        this.cargoCapacityKg = cargoCapacityKg;
    }

    String discriminator() {
        return "truck";
    }

    public String toString() {
        return "Truck{" + make + " " + model + ", cargoKg=" + cargoCapacityKg + "}";
    }
}

// Each map represents one row in the shared "vehicles" table.
// Every row carries every column key, with null for columns the
// row's discriminator does not own, matching how a real single
// table strategy stores data.
final class VehicleTable {
    private final List<Map<String, Object>> rows = new ArrayList<>();

    void insertCar(Car car) {
        Map<String, Object> row = new HashMap<>();
        row.put("id", car.id);
        row.put("vehicle_type", car.discriminator());
        row.put("make", car.make);
        row.put("model", car.model);
        row.put("year", car.year);
        row.put("door_count", car.doorCount);
        row.put("has_sidecar", null);
        row.put("cargo_capacity_kg", null);
        rows.add(row);
    }

    void insertMotorcycle(Motorcycle m) {
        Map<String, Object> row = new HashMap<>();
        row.put("id", m.id);
        row.put("vehicle_type", m.discriminator());
        row.put("make", m.make);
        row.put("model", m.model);
        row.put("year", m.year);
        row.put("door_count", null);
        row.put("has_sidecar", m.hasSidecar);
        row.put("cargo_capacity_kg", null);
        rows.add(row);
    }

    void insertTruck(Truck t) {
        Map<String, Object> row = new HashMap<>();
        row.put("id", t.id);
        row.put("vehicle_type", t.discriminator());
        row.put("make", t.make);
        row.put("model", t.model);
        row.put("year", t.year);
        row.put("door_count", null);
        row.put("has_sidecar", null);
        row.put("cargo_capacity_kg", t.cargoCapacityKg);
        rows.add(row);
    }

    List<Vehicle> loadAll() {
        List<Vehicle> result = new ArrayList<>();
        for (Map<String, Object> row : rows) {
            String type = (String) row.get("vehicle_type");
            int id = (int) row.get("id");
            String make = (String) row.get("make");
            String model = (String) row.get("model");
            int year = (int) row.get("year");
            switch (type) {
                case "car":
                    result.add(new Car(id, make, model, year, (int) row.get("door_count")));
                    break;
                case "motorcycle":
                    result.add(new Motorcycle(id, make, model, year, (boolean) row.get("has_sidecar")));
                    break;
                case "truck":
                    result.add(new Truck(id, make, model, year, (int) row.get("cargo_capacity_kg")));
                    break;
                default:
                    throw new IllegalStateException("unknown discriminator value: " + type);
            }
        }
        return result;
    }
}

public final class SingleTableInheritanceDemo {
    public static void main(String[] args) {
        VehicleTable table = new VehicleTable();
        table.insertCar(new Car(1, "Honda", "Civic", 2023, 4));
        table.insertMotorcycle(new Motorcycle(2, "Ducati", "Monster", 2024, false));
        table.insertTruck(new Truck(3, "Volvo", "FH16", 2022, 12000));

        for (Vehicle v : table.loadAll()) {
            System.out.println(v);
        }
    }
}
```

### TypeScript

```typescript
type VehicleRow = {
  id: number;
  vehicleType: "car" | "motorcycle" | "truck";
  make: string;
  model: string;
  year: number;
  doorCount: number | null;
  hasSidecar: boolean | null;
  cargoCapacityKg: number | null;
};

interface Vehicle {
  id: number;
  make: string;
  model: string;
  year: number;
  describe(): string;
}

class Car implements Vehicle {
  constructor(
    public id: number,
    public make: string,
    public model: string,
    public year: number,
    public doorCount: number
  ) {}

  describe(): string {
    return `${this.make} ${this.model} car with ${this.doorCount} doors`;
  }
}

class Motorcycle implements Vehicle {
  constructor(
    public id: number,
    public make: string,
    public model: string,
    public year: number,
    public hasSidecar: boolean
  ) {}

  describe(): string {
    return `${this.make} ${this.model} motorcycle, sidecar=${this.hasSidecar}`;
  }
}

class Truck implements Vehicle {
  constructor(
    public id: number,
    public make: string,
    public model: string,
    public year: number,
    public cargoCapacityKg: number
  ) {}

  describe(): string {
    return `${this.make} ${this.model} truck, cargo=${this.cargoCapacityKg}kg`;
  }
}

// Simulated "vehicles" table, one array standing in for one physical
// table. Every row carries every column, null where the row's
// discriminator does not own that column.
const vehiclesTable: VehicleRow[] = [];

function insertCar(car: Car): void {
  vehiclesTable.push({
    id: car.id,
    vehicleType: "car",
    make: car.make,
    model: car.model,
    year: car.year,
    doorCount: car.doorCount,
    hasSidecar: null,
    cargoCapacityKg: null,
  });
}

function insertMotorcycle(m: Motorcycle): void {
  vehiclesTable.push({
    id: m.id,
    vehicleType: "motorcycle",
    make: m.make,
    model: m.model,
    year: m.year,
    doorCount: null,
    hasSidecar: m.hasSidecar,
    cargoCapacityKg: null,
  });
}

function insertTruck(t: Truck): void {
  vehiclesTable.push({
    id: t.id,
    vehicleType: "truck",
    make: t.make,
    model: t.model,
    year: t.year,
    doorCount: null,
    hasSidecar: null,
    cargoCapacityKg: t.cargoCapacityKg,
  });
}

function loadAll(): Vehicle[] {
  return vehiclesTable.map((row) => {
    switch (row.vehicleType) {
      case "car":
        return new Car(row.id, row.make, row.model, row.year, row.doorCount as number);
      case "motorcycle":
        return new Motorcycle(row.id, row.make, row.model, row.year, row.hasSidecar as boolean);
      case "truck":
        return new Truck(row.id, row.make, row.model, row.year, row.cargoCapacityKg as number);
      default: {
        const exhaustive: never = row.vehicleType;
        throw new Error(`unknown discriminator value: ${exhaustive}`);
      }
    }
  });
}

insertCar(new Car(1, "Honda", "Civic", 2023, 4));
insertMotorcycle(new Motorcycle(2, "Ducati", "Monster", 2024, false));
insertTruck(new Truck(3, "Volvo", "FH16", 2022, 12000));

for (const vehicle of loadAll()) {
  console.log(vehicle.describe());
}
```
