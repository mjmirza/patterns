---
name: Class Table Inheritance
slug: class-table-inheritance
family: 06-poeaa
category: Object-Relational Structural
aliases: [Table Per Subclass, Joined Table Inheritance, Table Per Type, Multi-Table Inheritance]
first_described: "Fowler 2002"
maturity: canonical
related: [single-table-inheritance, concrete-table-inheritance, identity-map, unit-of-work, embedded-value]
incompatible_with: [single-table-inheritance, concrete-table-inheritance]
verified: 2026-08-02
---

# Class Table Inheritance

## 1. Name, aliases, and lineage

The canonical name is Class Table Inheritance, and it comes from Martin
Fowler's *Patterns of Enterprise Application Architecture*, Addison-Wesley,
2002, chapter 12, part of the Object-Relational Structural Patterns section.
Fowler states the intent on its own catalog page as representing "an
inheritance hierarchy of classes with one table for each class"
(https://martinfowler.com/eaaCatalog/classTableInheritance.html, verified
2026-08-02). The book groups it with two siblings that solve the same
problem, mapping an inheritance hierarchy to relational tables, with two
different trade-offs, Single Table Inheritance and Concrete Table
Inheritance.

The most common alias in ORM tooling is Table Per Subclass, which is the
literal name of the JPA and Hibernate strategy constant
`InheritanceType.JOINED` uses to implement it, and the name Doctrine ORM's
documentation uses interchangeably with Class Table Inheritance
(https://www.doctrine-project.org/projects/doctrine-orm/en/3.6/reference/inheritance-mapping.html,
verified 2026-08-02). Ruby on Rails and its surrounding community tend to say
Multi-Table Inheritance, because Active Record's own built-in inheritance
support is Single Table Inheritance, and Class Table Inheritance is the thing
you reach for when STI's single wide table stops fitting. Django's official
documentation calls its own implementation Multi-Table Inheritance as well
(https://docs.djangoproject.com/en/5.0/topics/db/models/#multi-table-inheritance,
verified 2026-08-02). Joined Table Inheritance and Table Per Type are the
same idea under different vendor branding, Joined Table from the JPA
specification's `JOINED` strategy name, Table Per Type from the .NET Entity
Framework community, which mirrors the JPA terminology in its own docs under
the initialism TPT, set against Table Per Hierarchy (TPH, the STI
equivalent) and Table Per Concrete Type (TPC, the Concrete Table
equivalent).

This entry treats Class Table Inheritance strictly as Fowler defined it, an
object-relational mapping strategy for persisting a class hierarchy, and
distinguishes it explicitly from Class Table, an unrelated pattern
occasionally confused with it that describes storing metadata about classes
themselves, and from the OOP inheritance mechanism, which is a language
feature the pattern maps onto storage, not the pattern itself.

## 2. Problem and context

A domain model built with proper object-oriented inheritance, a `Player`
base class with `Pitcher` and `Fielder` subclasses each carrying fields the
other does not need, sits naturally in memory as a type hierarchy. A
relational database has no native concept of inheritance. It has tables,
rows, and foreign keys. The moment a team decides the domain model should
keep its inheritance structure, rather than being flattened into value
objects or a single generic entity, someone has to decide how that
hierarchy becomes tables.

The context in which Class Table Inheritance specifically becomes the right
answer, rather than one of its two siblings, is a hierarchy where the
subclasses genuinely differ in the fields and behavior they carry, where the
number of subclass-specific fields is large enough to matter, where the
schema is expected to change as the domain model changes, and where the team
values a schema that a database administrator can read and reason about
without consulting application code. It is the pattern reached for when a
wide, mostly-null Single Table Inheritance table becomes uncomfortable to
maintain, and the pattern avoided when Concrete Table Inheritance's
duplicated columns and painful cross-hierarchy queries become the bigger
problem instead. Fowler frames all three inheritance patterns as living on
one axis, how much of the object model's structure the schema is willing to
mirror, and Class Table Inheritance sits at the end of that axis that
mirrors the most.

## 3. Forces

Normalization versus join cost. Class Table Inheritance produces the
most normalized possible schema for an inheritance hierarchy, no column ever
sits null because it belongs to a sibling subclass, but reading a single
concrete object now means a join across every table from the leaf class up
to the root, one join per level of inheritance depth.

Schema clarity versus query complexity. A database administrator or a
report author looking at the schema directly, without the ORM's mapping
layer in front of them, sees a `players`, `pitchers`, and `fielders` table
and can reason about what each one holds. That same person, or that same
raw SQL query, now has to know which tables to join and in what order to
reconstruct one polymorphic entity, which Single Table Inheritance would
have handed them for free in one table.

Referential integrity versus insert and delete cost. Every foreign key
from a subclass table back to its parent is a real, enforceable database
constraint, so an orphaned subclass row is impossible at the storage layer.
The tradeoff is that creating one object now requires one insert per level
of the hierarchy inside a single transaction, and deleting one requires
deletes in the reverse order, or a cascade the schema must be told to
perform.

Consistency versus polymorphic query cost. Querying "all players" is
straightforward with Single Table Inheritance, a `SELECT * FROM players`.
With Class Table Inheritance it requires either an outer join across every
known subclass table, guessing at runtime which subclass a given root row
belongs to, or a discriminator column on the root table that names the
subclass, at which point the schema carries a small piece of Single Table
Inheritance's own mechanism riding along inside a Class Table Inheritance
design. Fowler treats a discriminator on the root table as the standard,
pragmatic way to make Class Table Inheritance's polymorphic reads workable.

Evolvability versus migration surface. Adding a field to a subclass is
a single, small, targeted `ALTER TABLE` against exactly the table that owns
that field, and it touches no unrelated data. This is a genuine advantage
over Single Table Inheritance, where every new subclass field widens the
one shared table for every row regardless of subclass, but it comes at the
cost of a wider, more numerous set of migration files as the hierarchy
grows deeper, one per table rather than one shared file for the whole
hierarchy.

The pattern favours correctness of representation, referential integrity,
and long-term schema clarity. It sacrifices read performance for
polymorphic queries and adds real cost to every write that touches more
than the leaf table.

## 4. Applicability and non-applicability

Reach for Class Table Inheritance when the hierarchy's subclasses carry a
meaningful number of fields that genuinely do not apply to their siblings,
when those fields are expected to keep growing independently per subclass
as the domain evolves, when the team wants the schema itself, independent
of ORM configuration, to be a legible statement of the domain model for
anyone who queries the database directly, when strict column-level
`NOT NULL` constraints per subclass matter to data quality, and when insert
and update volume on the hierarchy is moderate rather than extreme, so the
per-write join cost is not the dominant cost of the system.

Do not reach for it when the hierarchy is deep, four or more levels, and the
application performs frequent polymorphic reads across the whole hierarchy,
because each additional level adds another join to every such query, and
join cost compounds faster than most teams expect until they measure it. Do
not reach for it when the subclasses differ by only one or two fields,
because the join overhead is not repaid by any real normalization benefit,
and Single Table Inheritance's few extra nullable columns are cheaper in
every dimension that matters. Do not reach for it when the write path is
extremely high volume, a system ingesting many rows per second per
subclass, because the multi-table insert and delete cost becomes the
bottleneck. Concrete Table Inheritance or Single Table Inheritance both
avoid that specific cost. Do not reach for it when the hierarchy is
unstable, still being actively redesigned, because every reshuffling of the
class tree becomes a matching reshuffle of tables and foreign keys,
migration churn that Single Table Inheritance's one wide table absorbs far
more cheaply. Do not reach for it in an analytics or reporting-heavy
context where a BI tool needs to scan the whole hierarchy in one flat query
without ORM assistance, since a denormalized read model or a materialized
view will consistently outperform a live multi-way join.

## 5. Structure

Root table. The table backing the base class of the hierarchy. It holds
every field common to all subclasses, a primary key that is also the key
every subclass table foreign-keys against, and, in the common pragmatic
variant, a discriminator column naming the concrete subclass so a
polymorphic query knows which subclass tables to join.

Subclass table, one per class in the hierarchy, including intermediate
abstract classes that have their own fields. Holds only the columns
unique to that class. Its primary key is simultaneously the foreign key
back to the parent's table, most commonly the immediate parent's table
rather than always the root, and most implementations enforce that the
subclass row can exist only if the corresponding parent row exists via a
foreign key constraint, sometimes tightened further with `ON DELETE
CASCADE` so deleting the root row removes every dependent subclass row in
one statement.

Loader or mapper. The piece of code, hand-written or ORM-generated, that
knows how to reconstruct one in-memory object of the correct concrete type
by joining the root table to the relevant chain of subclass tables, reading
the discriminator, or otherwise inferring the type, and populating the
resulting object's fields from every table in the chain.

Discriminator, optional in Fowler's original description, near-universal
in practice. A column on the root table, an enum or string, naming the
concrete subclass a given root row belongs to. Without it, determining a
row's concrete type requires probing every subclass table's foreign key
column, an expensive habit every real implementation avoids.

## 6. ASCII structure diagram

```
+----------------------------+
|          players           |   root table
+----------------------------+
| id (PK)                    |
| name                       |
| player_type (discriminator)|
+--------------+-------------+
               |
     +---------+---------+
     |                   |
+----v-------------+ +---v----------------+
|    pitchers      | |     fielders       |
+------------------+ +---------------------+
| player_id (PK,FK)| | player_id (PK,FK)   |
| era               | | fielding_pct        |
| strikeouts        | | assists              |
+-------------------+ +---------------------+

Object model, for comparison, drives the mapping above

           Player
          /      \
    Pitcher      Fielder
```

## 7. Dynamics

```
Load. fetch a Pitcher by id
  Loader.find(Pitcher, 42)
    SELECT p.id, p.name, p.player_type, pi.era, pi.strikeouts
      FROM players p
      JOIN pitchers pi ON pi.player_id = p.id
     WHERE p.id = 42
    -> one row -> new Pitcher(id, name, era, strikeouts)

Load. fetch all Players polymorphically, discriminator-driven
  Loader.findAll(Player)
    SELECT p.id, p.name, p.player_type,
           pi.era, pi.strikeouts, fi.fielding_pct, fi.assists
      FROM players p
      LEFT JOIN pitchers pi ON pi.player_id = p.id
      LEFT JOIN fielders fi ON fi.player_id = p.id
    -> for each row, branch on player_type ->
       'PITCHER' -> new Pitcher(...)   using pi.* columns
       'FIELDER' -> new Fielder(...)   using fi.* columns

Save. insert a new Pitcher
  begin transaction
    INSERT INTO players (name, player_type) VALUES ('Kim', 'PITCHER')
      -> new id (or caller-assigned id, depending on key strategy)
    INSERT INTO pitchers (player_id, era, strikeouts) VALUES (id, 3.1, 210)
  commit
  -- root row must exist before the subclass row can reference it,
  -- so insert order runs root-to-leaf and delete order runs leaf-to-root
```

## 8. Implementation variants

Discriminator-column variant, the dominant one. A discriminator column
on the root table names the concrete subclass, avoiding the need to probe
every subclass table to determine an unknown row's type. Every major ORM
that implements this pattern, Hibernate's `JOINED` strategy, Doctrine's CTI
strategy, and Django's multi-table inheritance's implicit content-type
lookups, defaults to some form of this. Fowler describes it as the
practical way to make Class Table Inheritance's read path workable.

No-discriminator variant. The original, purer form Fowler first
describes, where a polymorphic query has to attempt a join against every
known subclass table and infer the type from which join actually matched a
row. This is rarely used in production because it costs an extra join per
candidate subclass on every polymorphic read, purely to determine type, but
it remains valid where the hierarchy has exactly one or two subclasses and
the extra join is cheap.

Shared primary key versus surrogate foreign key. The dominant variant
makes the subclass table's primary key identical to the parent's primary
key value, a one-to-one identifying relationship, so `pitchers.player_id`
is both the subclass table's primary key and its foreign key to
`players.id`. A less common variant gives the subclass table its own
independent surrogate key plus a non-key foreign key column back to the
parent, which loses the guarantee that at most one subclass row can exist
per root row, and is used mainly by teams whose ORM or migration tooling
makes composite or foreign-primary-keys awkward to express.

Root-to-leaf join versus parent-to-child join for deep hierarchies.
When a hierarchy is more than two levels deep, an implementation can either
join every subclass table directly to the root table, each subclass table's
foreign key points at the root, not its immediate parent, or chain the
joins parent-to-child down the hierarchy. The direct-to-root variant makes
every query a fixed number of joins regardless of which level a class sits
at. The chained variant more faithfully mirrors the inheritance tree but
means a leaf class four levels deep costs four joins to load.

Lazy leaf-only loading. Doctrine ORM's documentation notes a specific
runtime consequence of a variant where an association targets a non-leaf
class in a CTI hierarchy, in that case Doctrine cannot construct a lazy
proxy for the association and must eagerly load the full object graph
immediately, rather than deferring the load
(https://www.doctrine-project.org/projects/doctrine-orm/en/3.6/reference/inheritance-mapping.html,
verified 2026-08-02). Teams using Doctrine's implementation therefore treat
"target only leaf entities in associations" as a practical constraint on
how the pattern is used, not an optional detail.

Language-idiomatic shape. In statically typed, class-based languages
(Java, C#, Swift, Kotlin), the pattern maps directly onto the language's own
inheritance keyword, and the ORM's job is entirely the persistence mapping.
In languages that favour composition or structural typing over class
inheritance (Go, Rust), the pattern is rarely implemented with the
language's own type system standing in for the object hierarchy. Instead
teams typically model the same relational shape, a root table plus per-variant
tables, and reconstruct a tagged union or sum type in application code after
the join, because Go has no inheritance and Rust's `enum` is a closer match
to Single Table Inheritance's discriminator idea than to a class hierarchy.

## 9. Known production uses

Hibernate ORM, `InheritanceType.JOINED`. Hibernate's JPA-compliant
mapping annotations expose Class Table Inheritance as one of the three JPA
inheritance strategies, `JOINED`, alongside `SINGLE_TABLE` and
`TABLE_PER_CLASS`, and the Hibernate User Guide documents the strategy under
its "Joined table" section as one of the ORM's core inheritance mapping
approaches, present in the guide's table of contents at section 3.14.3
(https://docs.hibernate.org/orm/6.4/userguide/html_single/Hibernate_User_Guide.html,
verified 2026-08-02, table of contents entry confirmed live, full section
prose not independently reproduced here).

Doctrine ORM (PHP), Class Table Inheritance strategy. Doctrine's own
reference documentation names and implements this exact pattern under the
name Class Table Inheritance, describing it as mapping "each class in a
hierarchy... to several tables, its own table and the tables of all parent
classes," linked by a foreign key constraint from the child table's primary
key to the parent's
(https://www.doctrine-project.org/projects/doctrine-orm/en/3.6/reference/inheritance-mapping.html,
verified 2026-08-02).

Django ORM (Python), multi-table inheritance. Django's official model
documentation implements this exact pattern under the name multi-table
inheritance, stating that "each model in the hierarchy is a model all by
itself. Each model corresponds to its own database table," connected by an
automatically created `OneToOneField` from child to parent
(https://docs.djangoproject.com/en/5.0/topics/db/models/#multi-table-inheritance,
verified 2026-08-02). The framework's own worked example maps a `Place` base
model to a `Restaurant` subclass model exactly along the lines of this
entry's Player and Pitcher example.

.NET Entity Framework Core, Table Per Type (TPT). Microsoft's Entity
Framework Core documentation includes Table Per Type as one of its three
supported inheritance mapping strategies for object hierarchies, structurally
identical to Class Table Inheritance, a base table plus one table per
derived type joined on a shared primary key, documented under the "Table per
Type" (TPT) inheritance mapping strategy in the EF Core inheritance
documentation set.

## 10. Consequences

Positive.

- The schema fully normalizes the hierarchy, no column is ever null merely
  because it belongs to a sibling subclass, which keeps `NOT NULL`
  constraints meaningful at the column level rather than advisory.
- Referential integrity between a subclass and its parent is enforced by the
  database itself through a real foreign key, not by application discipline.
- The schema is legible to anyone reading it directly, a `pitchers` table
  visibly means pitcher-specific data, without needing to know an ORM's
  discriminator convention.
- Adding a field to one subclass is a small, isolated migration against
  exactly the table that needs it, and does not widen any row belonging to
  a sibling subclass.
- Storage is not wasted on unused columns the way a wide Single Table
  Inheritance table wastes it for every subclass that does not use a given
  field.

Negative.

- Reading one fully-formed object costs one join per level of inheritance
  depth, and this cost is paid on every single-entity fetch, not only on
  bulk polymorphic queries.
- Polymorphic queries across the whole hierarchy require either a
  discriminator-driven set of outer joins or a union-style query across
  every subclass table, both of which are more expensive and harder to
  optimize with indexes than a single-table scan.
- Writing one object costs one insert or update per level of the hierarchy
  inside a single transaction, and the insert order is not arbitrary, the
  root row must exist before any subclass row can reference it.
- Deleting one object requires deleting in leaf-to-root order, or relying on
  cascading foreign keys the schema must be explicitly configured to
  perform, and a missed cascade configuration produces orphaned or
  constraint-violating rows.
- The number of tables in the schema grows with the depth and breadth of the
  hierarchy, which increases the surface area a migration tool and a
  database administrator both have to track.

## 11. Failure modes and misuse

Symptom. A report author or a new engineer writes raw SQL against what
looks like a normal `players` table and gets back rows with no pitcher or
fielder detail at all. Cause. They queried only the root table, not
realizing the domain-relevant columns live in a joined subclass table they
did not know to join. Fix. Document the discriminator column and the
join path explicitly next to the schema, or provide a database view that
performs the join for ad hoc query authors, so the schema's shape is not a
trap for anyone who does not already know the ORM's mapping.

Symptom. A polymorphic "list all players" screen gets measurably slower
every time a new subclass is added to the hierarchy, even though the number
of rows returned has not grown. Cause. The polymorphic query is built as
a chain of outer joins across every subclass table, so query cost scales
with the number of distinct subclasses in the hierarchy, not with the row
count of any one of them. Fix. Either cap the acceptable hierarchy
breadth, denormalize a read-optimized projection for the polymorphic list
view specifically, or switch the list view's data source to a materialized
view refreshed asynchronously rather than joining live on every read.

Symptom. An insert into the leaf table throws a foreign key violation
intermittently, only under concurrent load. Cause. The root-row insert
and the subclass-row insert were issued as two separate, non-transactional
statements, and under load the subclass insert can race ahead of the root
insert's commit becoming visible, or a partial failure between the two
leaves an orphaned attempt. Fix. Wrap the whole multi-table write for
one logical object inside a single database transaction, which is the
standard remedy Fowler pairs with this pattern and with Unit of Work more
broadly.

Symptom. Deleting a root-level record silently fails with a foreign key
constraint error, or worse, silently succeeds and leaves orphaned subclass
rows behind depending on the database's default constraint behavior.
Cause. The cascade behavior on the parent-to-subclass foreign key was
never explicitly decided, so it defaults to whatever the database's default
happens to be, which is not guaranteed to be `CASCADE`. Fix. Make the
delete behavior an explicit, reviewed decision, either an explicit
`ON DELETE CASCADE` on every subclass foreign key, or an application-level
Unit of Work that performs the deletes in the correct leaf-to-root order
inside one transaction, and add a test that exercises the delete path
specifically.

Symptom. A non-leaf entity association behaves as if lazy loading were
turned off, and profiling shows the full object graph loading eagerly on
every access even where the code only asked for a reference. Cause.
Documented directly by Doctrine ORM, when the target of an association is a
non-leaf class inside a Class Table Inheritance hierarchy, the ORM cannot
construct a lazy proxy for it and must eagerly load the whole hierarchy of
tables to know the object's real concrete type
(https://www.doctrine-project.org/projects/doctrine-orm/en/3.6/reference/inheritance-mapping.html,
verified 2026-08-02). Fix. Target associations at leaf entities only
where lazy loading matters for performance, or accept and budget for the
eager load explicitly where a non-leaf target is unavoidable.

Symptom. The hierarchy has grown to five or six levels deep over time
as the domain model evolved, and even simple single-object reads have
become noticeably slow. Cause. Each additional inheritance level added
one more join to every load of a leaf-class object, and nobody set a limit
on how deep the hierarchy was allowed to grow. Fix. This is a modeling
misuse of the pattern more than an implementation bug. Fowler's own
non-applicability guidance is exactly this case. Flatten the deepest,
least-differentiated levels back into their parent, or reconsider whether
the domain genuinely needs that many levels of type-level differentiation
represented in the schema at all.

## 12. Trade-off matrix

| Force | Class Table Inheritance | Single Table Inheritance | Concrete Table Inheritance |
|---|---|---|---|
| Storage normalization | Fully normalized, no wasted columns | Wide table, unused columns null per subclass | Normalized per class, but shared columns duplicated across tables |
| Single-object read cost | One join per hierarchy level | One row, no join | One row, no join |
| Polymorphic query cost | Multi-table outer join or discriminator-driven join set | Single scan, cheapest of the three | Union across every concrete table, no shared identity key |
| Referential integrity to parent | Enforced by real foreign key | Not applicable, one table | Not applicable, no shared parent row exists |
| Schema legibility standalone | High, each table visibly matches a class | Low, one wide table hides which columns apply to which subclass | Medium, each table is legible but shared fields are duplicated everywhere |
| Adding a subclass field | Small, isolated migration on one table | Widens the single shared table for every row | Small migration but must be repeated if the field is later promoted to the parent |
| Cross-hierarchy identity, shared primary key space | Yes, one id space via the root table | Yes, one table, trivially | No, each concrete table has an independent key space unless engineered otherwise |
| Write cost per object | One insert or update per hierarchy level, in a transaction | One insert or update | One insert or update, but shared-field changes must be repeated per table if denormalized |

## 13. Related and incompatible patterns

Single Table Inheritance and Concrete Table Inheritance. These three
patterns are Fowler's own named alternatives for the same underlying
problem, mapping one class hierarchy to relational tables, and a hierarchy
is mapped using exactly one of the three at a time within a given ORM
mapping configuration. They are mutually incompatible as strategies applied
to the same hierarchy, though a large system with several independent
hierarchies is free to use a different one of the three for each hierarchy
based on that hierarchy's own shape and access pattern.

Identity Map. Because loading one object from Class Table Inheritance
requires reconstructing it from several joined rows, a caching layer that
guarantees a given logical row is loaded and materialized only once per
unit of work becomes considerably more valuable here than it is for a
single-table load, since it spreads the multi-table join cost across
repeated references to the same object within one request or transaction.

Unit of Work. The multi-table, ordered insert-and-delete requirement of
this pattern is precisely the coordination problem Unit of Work exists to
solve, tracking every object that changed during a business transaction and
committing the correctly ordered sequence of inserts, updates, and deletes
as one atomic operation.

Foreign Key Mapping and Embedded Value. Class Table Inheritance is
itself built from a specialized, one-to-one identifying use of Foreign Key
Mapping between each subclass table and its parent. Embedded Value is its
near opposite in intent, useful when a value type has no independent
identity of its own and should collapse into its owner's table rather than
gaining a table of its own the way every inheritance level does here.

Data Mapper. Class Table Inheritance is almost always implemented as a
mapping detail inside a Data Mapper layer, because the domain object
graph's shape, one polymorphic class, and its persisted shape, several
joined rows, diverge enough that a thin Active Record style save method on
the domain object itself becomes awkward to hand-write correctly across
every subclass.

## 14. Refactoring path in and out

Introducing it, from a flat table. Start from a single table that has
grown a discriminator-like column and a cluster of nullable, subclass-specific
columns, the shape Single Table Inheritance ends up in under its own growth
pressure. Identify the columns that are genuinely subclass-specific by
checking which ones are consistently null together, grouped by the existing
discriminator value. For each such group, create a new table carrying those
columns plus a primary key that doubles as a foreign key to the original
table's primary key. Migrate the data with a script that, for every existing
row, inserts a matching row into the new subclass table carrying only that
subclass's columns, then drop the now-redundant columns from the original
table, which becomes the root table. Do this one subclass at a time in
production, checking row counts and foreign key integrity after each
subclass's migration completes, rather than attempting the whole hierarchy
in one migration.

Introducing it, from Concrete Table Inheritance. Start from a set of
independent tables, each carrying its own copy of the shared fields with its
own independent primary key. Create a new root table carrying only the
shared fields plus a fresh shared primary key space. For each concrete
table, add a migration that assigns each existing row a new root-table row,
records the mapping from old key to new shared key, drops the
duplicated shared columns from the concrete table, and adds the foreign
key column pointing back to the new root table using the recorded mapping.
This migration is more involved than the Single Table Inheritance case
because it also has to unify what were previously several independent
primary key spaces into one.

Removing it, collapsing back toward Single Table Inheritance. Reverse
the introduction migration, for a hierarchy that turned out shallower or
less differentiated in practice than the schema assumed. Add the subclass
columns back onto the root table as nullable columns, run a migration that
copies each subclass table's data into the corresponding rows of the root
table, drop the subclass tables, and update the discriminator column, which
in the discriminator-column variant already exists on the root table, to be
the sole means of determining concrete type going forward.

## 15. Testing and verification

Testing code built on Class Table Inheritance is easier in one specific way
and harder in another. It is easier to write a strict unit test asserting a
particular field is genuinely required for one subclass and genuinely
absent from another, because the schema itself enforces that separation at
the column level, a test does not have to special-case "this column is
allowed to be null when the subclass is X" the way it would against a
Single Table Inheritance table.

It is harder to test the loading and saving path in isolation, because a
correct save of one object always exercises multiple tables and, in
production configurations, a transaction boundary spanning all of them.
Tests exercising the persistence layer for this pattern should assert, at
minimum, that saving a new subclass instance produces exactly one row in
each expected table with the correct linking key, that a failed insert into
any one of the subclass tables rolls back the root-table insert rather than
leaving an orphaned root row, that deleting a root object removes every
dependent subclass row, and that loading round-trips a saved object back to
an equal, not merely equivalent-looking, in-memory instance across the full
chain of joined tables. An in-memory or containerized real database, rather
than a mocked ORM session, is the appropriate test double here, because the
foreign key constraints, join semantics, and transaction rollback behavior
this pattern depends on are exactly the things a mock of the ORM cannot
faithfully reproduce. A lightweight real database such as SQLite for tests
that do not depend on vendor-specific join optimizer behavior, or a
containerized instance of the production database engine for tests that do,
are the two techniques teams commonly use.

## 16. Observability signals

A healthy instance of this pattern shows a stable, predictable number of
queries per logical object load, exactly one join query whose join count
matches the hierarchy depth of the concrete type being loaded, on every
single-object fetch, and this number should not silently rise over
time as the codebase changes. The clearest early warning sign of drift is
an N+1 query pattern specific to this mapping, a list of root objects
loaded with one query, followed by one additional per-row query issued to
fetch each object's subclass-specific data individually rather than as
part of a single joined statement. Most ORM query logs and APM tracing
tools will show this as a burst of near-identical queries immediately
following a single list query, and it is the single most common
performance regression this pattern introduces.

Log or trace the query plan's join count against the hierarchy depth for
any endpoint known to load leaf-class objects heavily, and treat an
observed join count higher than the hierarchy's actual depth as a signal
that either the mapping configuration has drifted from the schema or an
unnecessary intermediate table is being joined redundantly. On the write
path, the most useful signal is transaction duration and lock hold time on
multi-table inserts under concurrent load, since this pattern's write cost
is proportional to hierarchy depth and a growing hierarchy will show up
first as a slow, gradual rise in write latency under load rather than
as an outright failure.

## 17. Security and privacy implications

Splitting a hierarchy across multiple tables gives a data access layer a
genuine, column-level granularity for access control that a single wide
table does not offer as cleanly, a database role can be granted read access
to the `players` root table without any access to the `fielders` table's
sensitive columns, whereas a Single Table Inheritance table would require
column-level grants inside the one table to achieve the same separation.
This is a real, if secondary, benefit where regulatory or contractual
requirements demand that certain subclass-specific fields, medical data
attached to one subclass of a person hierarchy for instance, be readable
only by a narrower set of roles than the base entity's common fields.

The pattern introduces no new attack surface of its own beyond the
ordinary SQL injection and access control concerns any relational schema
carries, but it does raise the practical bar for anyone auditing data
access, since a full picture of what data one logical entity carries now
requires reading a join across several tables rather than one table's
column list, and an incomplete audit that checks only the root table's
grants can miss a subclass table's more sensitive columns entirely. Where
GDPR-style right-to-erasure obligations apply, the cascading, multi-table
delete this pattern requires needs to be verified as genuinely complete,
including any subclass table an auditor might not think to check, rather
than assumed complete because the root row was removed.

## 18. References

- Martin Fowler, *Patterns of Enterprise Application Architecture*,
  Addison-Wesley, 2002, chapter 12, Object-Relational Structural Patterns,
  Class Table Inheritance.
- Martin Fowler, Class Table Inheritance catalog page,
  https://martinfowler.com/eaaCatalog/classTableInheritance.html, intent
  quoted as "Represents an inheritance hierarchy of classes with one table
  for each class", verified 2026-08-02.
- Django Project, Models topic guide, Multi-table inheritance section,
  https://docs.djangoproject.com/en/5.0/topics/db/models/#multi-table-inheritance,
  verified 2026-08-02.
- Doctrine Project, Doctrine ORM Reference, Inheritance Mapping, Class Table
  Inheritance section,
  https://www.doctrine-project.org/projects/doctrine-orm/en/3.6/reference/inheritance-mapping.html,
  verified 2026-08-02.
- Hibernate ORM 6.4 User Guide, table of contents section 3.14.3, Joined
  table inheritance strategy,
  https://docs.hibernate.org/orm/6.4/userguide/html_single/Hibernate_User_Guide.html,
  section entry verified present 2026-08-02, full section prose not
  independently reproduced in this entry.
- Microsoft, Entity Framework Core documentation, Inheritance, Table per
  Type (TPT) mapping strategy, learn.microsoft.com, EF Core inheritance
  documentation set, cited from established public documentation of the
  TPT strategy name and shape, not independently re-fetched for this entry.

## Code examples

Three languages, each run to completion during authoring. Java was not used
because a working Java runtime was not available in this environment, only
the compiler stub was present, so a Java sample could not be verified to run
and is omitted rather than shipped unverified.

### Python (run with sqlite3, a real database, no ORM)

```python
"""Class Table Inheritance against sqlite3 directly, no ORM."""
import sqlite3
from dataclasses import dataclass


@dataclass
class Pitcher:
    id: int
    name: str
    era: float
    strikeouts: int


@dataclass
class Fielder:
    id: int
    name: str
    fielding_pct: float
    assists: int


CREATE_PLAYERS = (
    "CREATE TABLE players ("
    "id INTEGER PRIMARY KEY, name TEXT NOT NULL, player_type TEXT NOT NULL)"
)
CREATE_PITCHERS = (
    "CREATE TABLE pitchers ("
    "player_id INTEGER PRIMARY KEY REFERENCES players(id), "
    "era REAL NOT NULL, strikeouts INTEGER NOT NULL)"
)
CREATE_FIELDERS = (
    "CREATE TABLE fielders ("
    "player_id INTEGER PRIMARY KEY REFERENCES players(id), "
    "fielding_pct REAL NOT NULL, assists INTEGER NOT NULL)"
)


def setup(conn: sqlite3.Connection) -> None:
    conn.execute(CREATE_PLAYERS)
    conn.execute(CREATE_PITCHERS)
    conn.execute(CREATE_FIELDERS)


def save_pitcher(conn: sqlite3.Connection, name: str, era: float, k: int) -> int:
    with conn:
        cur = conn.execute(
            "INSERT INTO players (name, player_type) VALUES (?, 'PITCHER')",
            (name,),
        )
        player_id = cur.lastrowid
        conn.execute(
            "INSERT INTO pitchers (player_id, era, strikeouts) VALUES (?, ?, ?)",
            (player_id, era, k),
        )
    return player_id


def save_fielder(conn: sqlite3.Connection, name: str, pct: float, assists: int) -> int:
    with conn:
        cur = conn.execute(
            "INSERT INTO players (name, player_type) VALUES (?, 'FIELDER')",
            (name,),
        )
        player_id = cur.lastrowid
        conn.execute(
            "INSERT INTO fielders (player_id, fielding_pct, assists) VALUES (?, ?, ?)",
            (player_id, pct, assists),
        )
    return player_id


LOAD_PITCHER = (
    "SELECT p.id, p.name, pi.era, pi.strikeouts FROM players p "
    "JOIN pitchers pi ON pi.player_id = p.id WHERE p.id = ?"
)


def load_pitcher(conn: sqlite3.Connection, player_id: int) -> Pitcher:
    row = conn.execute(LOAD_PITCHER, (player_id,)).fetchone()
    return Pitcher(*row)


LOAD_ALL = (
    "SELECT p.id, p.name, p.player_type, pi.era, pi.strikeouts, "
    "fi.fielding_pct, fi.assists FROM players p "
    "LEFT JOIN pitchers pi ON pi.player_id = p.id "
    "LEFT JOIN fielders fi ON fi.player_id = p.id ORDER BY p.id"
)


def load_all_polymorphic(conn: sqlite3.Connection) -> list:
    rows = conn.execute(LOAD_ALL).fetchall()
    result = []
    for pid, name, kind, era, k, pct, assists in rows:
        if kind == "PITCHER":
            result.append(Pitcher(pid, name, era, k))
        elif kind == "FIELDER":
            result.append(Fielder(pid, name, pct, assists))
        else:
            raise ValueError(f"unknown player_type {kind}")
    return result


def main() -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    setup(conn)

    pitcher_id = save_pitcher(conn, "Kim", 3.10, 210)
    save_fielder(conn, "Diaz", 0.981, 312)

    loaded = load_pitcher(conn, pitcher_id)
    assert loaded == Pitcher(pitcher_id, "Kim", 3.10, 210)

    everyone = load_all_polymorphic(conn)
    assert len(everyone) == 2
    assert isinstance(everyone[0], Pitcher)
    assert isinstance(everyone[1], Fielder)

    print("class table inheritance sqlite demo passed")
    print(everyone)


if __name__ == "__main__":
    main()
```

Run with `python3 class_table_inheritance.py`, verified to print
`class table inheritance sqlite demo passed` during authoring, using the
real `sqlite3` foreign key constraint between `pitchers.player_id` and
`players.id` rather than a mocked join.

### TypeScript (in-memory tables plus a loader)

```typescript
type PlayerType = "PITCHER" | "FIELDER";

interface PlayerRow {
  id: number;
  name: string;
  playerType: PlayerType;
}

interface PitcherRow {
  playerId: number;
  era: number;
  strikeouts: number;
}

interface FielderRow {
  playerId: number;
  fieldingPct: number;
  assists: number;
}

abstract class Player {
  constructor(public readonly id: number, public readonly name: string) {}
}

class Pitcher extends Player {
  constructor(id: number, name: string, public era: number, public strikeouts: number) {
    super(id, name);
  }
}

class Fielder extends Player {
  constructor(id: number, name: string, public fieldingPct: number, public assists: number) {
    super(id, name);
  }
}

class PlayerTable {
  private rows = new Map<number, PlayerRow>();
  private nextId = 1;

  insert(name: string, playerType: PlayerType): number {
    const id = this.nextId++;
    this.rows.set(id, { id, name, playerType });
    return id;
  }

  get(id: number): PlayerRow {
    const row = this.rows.get(id);
    if (!row) throw new Error(`no players row for id ${id}`);
    return row;
  }

  all(): PlayerRow[] {
    return [...this.rows.values()];
  }
}

class PitcherTable {
  private rows = new Map<number, PitcherRow>();

  insert(row: PitcherRow): void {
    this.rows.set(row.playerId, row);
  }

  get(playerId: number): PitcherRow {
    const row = this.rows.get(playerId);
    if (!row) throw new Error(`no pitchers row for player_id ${playerId}`);
    return row;
  }
}

class FielderTable {
  private rows = new Map<number, FielderRow>();

  insert(row: FielderRow): void {
    this.rows.set(row.playerId, row);
  }

  get(playerId: number): FielderRow {
    const row = this.rows.get(playerId);
    if (!row) throw new Error(`no fielders row for player_id ${playerId}`);
    return row;
  }
}

class PlayerLoader {
  constructor(
    private players: PlayerTable,
    private pitchers: PitcherTable,
    private fielders: FielderTable
  ) {}

  savePitcher(name: string, era: number, strikeouts: number): Pitcher {
    const id = this.players.insert(name, "PITCHER");
    this.pitchers.insert({ playerId: id, era, strikeouts });
    return new Pitcher(id, name, era, strikeouts);
  }

  saveFielder(name: string, fieldingPct: number, assists: number): Fielder {
    const id = this.players.insert(name, "FIELDER");
    this.fielders.insert({ playerId: id, fieldingPct, assists });
    return new Fielder(id, name, fieldingPct, assists);
  }

  loadAll(): Player[] {
    return this.players.all().map((row) => {
      if (row.playerType === "PITCHER") {
        const pitcher = this.pitchers.get(row.id);
        return new Pitcher(row.id, row.name, pitcher.era, pitcher.strikeouts);
      }
      const fielder = this.fielders.get(row.id);
      return new Fielder(row.id, row.name, fielder.fieldingPct, fielder.assists);
    });
  }
}

function main(): void {
  const loader = new PlayerLoader(new PlayerTable(), new PitcherTable(), new FielderTable());
  loader.savePitcher("Kim", 3.1, 210);
  loader.saveFielder("Diaz", 0.981, 312);

  const all = loader.loadAll();
  if (all.length !== 2) throw new Error("expected 2 players");
  if (!(all[0] instanceof Pitcher)) throw new Error("expected first to be Pitcher");
  if (!(all[1] instanceof Fielder)) throw new Error("expected second to be Fielder");

  console.log("class table inheritance ts demo passed");
  console.log(all);
}

main();
```

Compiled with `npx tsc --strict --target es2020` and run with `node`,
verified to print `class table inheritance ts demo passed` during
authoring, using the real language `abstract class` hierarchy this pattern
maps onto storage, rather than a plain object shape.

### Go (a hierarchy modeled as a tagged struct, the idiomatic Go shape)

Go has no class inheritance, so this sample follows the language-idiomatic
shape from dimension 8, a root table plus per-variant tables, reconstructed
as a tagged struct after the join rather than a subclass instance.

```go
package main

import "fmt"

type PlayerType int

const (
	Pitcher PlayerType = iota
	Fielder
)

type PlayerRow struct {
	ID   int
	Name string
	Type PlayerType
}

type PitcherRow struct {
	ERA        float64
	Strikeouts int
}

type FielderRow struct {
	FieldingPct float64
	Assists     int
}

type Player struct {
	ID      int
	Name    string
	Type    PlayerType
	Pitcher *PitcherRow
	Fielder *FielderRow
}

type PlayerLoader struct {
	players  map[int]PlayerRow
	pitchers map[int]PitcherRow
	fielders map[int]FielderRow
	nextID   int
}

func NewPlayerLoader() *PlayerLoader {
	return &PlayerLoader{
		players:  make(map[int]PlayerRow),
		pitchers: make(map[int]PitcherRow),
		fielders: make(map[int]FielderRow),
		nextID:   1,
	}
}

func (l *PlayerLoader) SavePitcher(name string, era float64, k int) Player {
	id := l.nextID
	l.nextID++
	l.players[id] = PlayerRow{ID: id, Name: name, Type: Pitcher}
	l.pitchers[id] = PitcherRow{ERA: era, Strikeouts: k}
	row := l.pitchers[id]
	return Player{ID: id, Name: name, Type: Pitcher, Pitcher: &row}
}

func (l *PlayerLoader) SaveFielder(name string, pct float64, assists int) Player {
	id := l.nextID
	l.nextID++
	l.players[id] = PlayerRow{ID: id, Name: name, Type: Fielder}
	l.fielders[id] = FielderRow{FieldingPct: pct, Assists: assists}
	row := l.fielders[id]
	return Player{ID: id, Name: name, Type: Fielder, Fielder: &row}
}

func (l *PlayerLoader) LoadAll() []Player {
	out := make([]Player, 0, len(l.players))
	for id, row := range l.players {
		if row.Type == Pitcher {
			p := l.pitchers[id]
			out = append(out, Player{ID: id, Name: row.Name, Type: Pitcher, Pitcher: &p})
		} else {
			f := l.fielders[id]
			out = append(out, Player{ID: id, Name: row.Name, Type: Fielder, Fielder: &f})
		}
	}
	return out
}

func main() {
	loader := NewPlayerLoader()
	loader.SavePitcher("Kim", 3.1, 210)
	loader.SaveFielder("Diaz", 0.981, 312)

	all := loader.LoadAll()
	if len(all) != 2 {
		panic("expected 2 players")
	}

	pitcherCount, fielderCount := 0, 0
	for _, p := range all {
		if p.Pitcher != nil {
			pitcherCount++
		}
		if p.Fielder != nil {
			fielderCount++
		}
	}
	if pitcherCount != 1 || fielderCount != 1 {
		panic("expected exactly one pitcher and one fielder")
	}

	fmt.Println("class table inheritance go demo passed")
	for _, p := range all {
		fmt.Printf("%+v\n", p)
	}
}
```

Run with `go run class_table_inheritance.go`, verified to print
`class table inheritance go demo passed` during authoring.
