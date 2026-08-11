---
name: Active Record
slug: active-record
family: 06-poeaa
category: Object-Relational Metadata Mapping Pattern
aliases: [ActiveRecord, Model as Row]
first_described: "Fowler 2002"
maturity: canonical
related: [table-data-gateway, row-data-gateway, domain-model, transaction-script, unit-of-work, identity-map]
incompatible_with: [table-data-gateway]
verified: 2026-08-02
---

# Active Record

## 1. Name, aliases, and lineage

The canonical name is Active Record. It is one of the object-relational
patterns catalogued in Martin Fowler, *Patterns of Enterprise Application
Architecture*, Addison-Wesley, 2002, chapter 11 (Object-Relational Behavioral
Patterns), section "Active Record," pages 160 to 165. Fowler's own definition
opens the pattern entry with the sentence, "An object that wraps a row in a
database table or view, encapsulates the database access, and adds domain
logic on that data" (Fowler, *PoEAA*, page 160). The pattern's public catalog
page carries the same intent statement and a UML sketch matching the book
(https://martinfowler.com/eaaCatalog/activeRecord.html, verified 2026-08-02).

The pattern predates the book as a folk practice. Fowler himself credits it as
already common before he wrote it down, and the accompanying "Sidebar" in the
PoEAA text, co-written with the contributor David Rice, frames it as a
description of existing practice rather than an invention. The name has since
been captured by a specific implementation. Ruby on Rails ships an ORM library
literally named `ActiveRecord`, first released with Rails 1.0 in December
2005, whose README states plainly that it "implements the Active Record
pattern and is an ORM framework" (https://github.com/rails/rails/blob/main/activerecord/README.rdoc,
verified 2026-08-02). Because Rails' `ActiveRecord` gem is one of the most
widely used pieces of Ruby software ever shipped, the term "Active Record" is
now used loosely, by many working programmers, to mean "an ORM whose model
objects also know how to save and load themselves," even when the underlying
implementation departs from Fowler's diagram. This entry treats the GoF-style
"Fowler pattern" as the precise definition and calls out where the Rails-style
usage diverges from it, because conflating the pattern with any one library's
implementation is the single most common source of confusion when discussing
this pattern in an interview or an architecture review.

No other alias is in wide use. "Model as Row" is a description occasionally
used in teaching material to distinguish it from Domain Model, not a name
found in a primary source, and this entry marks it as informal rather than
citing a source for it.

## 2. Problem and context

An application needs to load rows from a relational table, let a caller read
and mutate the fields as ordinary object properties, validate the values, and
persist changes back, and it needs this for many different tables. The
context in which Active Record is chosen, rather than one of its siblings, is
narrow and specific. The domain logic attached to each row is genuinely
simple, close to a direct field-by-field mapping between the object's
properties and the table's columns, and there is close to a one-to-one
correspondence between a table and a class. Fowler frames the choice this way
directly, writing that "Active Record is a good choice for domain logic that
isn't too complex, such as create, read, update, and delete... Domain logic
that involves validation, calculations, and derivations is a good fit"
(Fowler, *PoEAA*, page 161).

The pattern exists because two earlier, more mechanically separated patterns
in the same catalog, Row Data Gateway and Table Data Gateway, keep the "row as
object" idea and the "domain behavior" idea in two different objects, one
holding data, the other holding the queries and the mapping. That separation
buys flexibility at the cost of an extra layer a programmer has to navigate
for every simple CRUD-shaped table. Active Record collapses the gateway and
the domain object into one class. The row object itself carries `find`,
`save`, `delete`, and instance-level validation, alongside whatever plain
business rules apply to that row, such as a total, a status transition, or a
formatted label. The problem the pattern solves is specifically the
productivity cost of that extra indirection when the mapping really is
straightforward, at the cost, discussed under Consequences, of tying domain
logic to the shape of a single table.

## 3. Forces

The forces Active Record balances, in order of how strongly the pattern
favors each side.

Developer velocity against architectural separation. Active Record wins
heavily on velocity for CRUD-shaped screens, one class per table, generate
the mapping, done. It loses on separation, because the object mixing
persistence and behavior means a unit test of business logic that happens to
touch a persisted field is also, implicitly, a test that depends on a schema
and usually a live or in-memory database connection.

Learning cost against long-run flexibility. A newcomer to a codebase can read
one Active Record class and understand both what the row looks like and what
it can do, without chasing a Repository interface, a mapper, and a domain
object separately. That legibility is a real force in the pattern's favor for
small teams and early-stage products. It is bought against flexibility. When
the domain model needs to diverge from the table shape, such as a computed
field sourced from three tables, an aggregate spanning several rows, or a
value object shared across several entities, Active Record has no natural
home for the divergence, because the object is the table row.

Consistency of persistence timing against control over persistence timing.
Because save and load are instance methods on the domain object, and many
Active Record implementations, Rails' `ActiveRecord` and Laravel's Eloquent
among them, persist eagerly on a `save` call or on association assignment,
the pattern favors an obvious, synchronous "what you see is what got
written" mental model over the batched, deferred write coordination that a
Unit of Work provides. This is a real trade, not a defect. It removes a whole
class of bugs around forgetting to flush a session, at the cost of losing the
ability to batch writes for performance or to defer constraint checks until a
larger transaction commits.

Team topology and cognitive load. A single, small team maintaining a modest
number of tables can hold "the row objects are the domain objects" in their
head without friction. As the team, the table count, and the divergence
between the relational shape and the business shape all grow, the same
collapsed structure raises cognitive load, because every screen touching that
table now also has to reason about persistence concerns baked into the same
class.

## 4. Applicability and non-applicability

Reach for Active Record when the following hold, together, not individually.

- The domain logic per table is genuinely simple, mostly create, read,
  update, delete, plus straightforward validation and derived fields computed
  from that row's own columns.
- There is a close, largely one-to-one correspondence between a database
  table and a conceptual entity in the domain.
- The team values being able to open one file and see both the shape of the
  data and the behavior that touches it, over strict separation of concerns.
- The application is early-stage, a script, an admin tool, or a
  CRUD-dominated product where the relational schema and the mental model of
  the business genuinely agree.
- The persistence technology is a single relational, or relational-like,
  store the object maps onto directly, not a mix of stores or an
  event-sourced write model.

Do not reach for Active Record, and prefer Domain Model, Data Mapper, or a
Repository plus a plain object instead, when any of these hold.

- The domain logic is complex, meaning multiple objects collaborating,
  business invariants spanning more than one row or more than one table,
  state machines with several transitions, or calculations that do not
  reduce to a formula over the row's own fields. Fowler is explicit that
  Active Record works "as long as the logic isn't too complicated" and that
  once it grows, "you'll soon want to use your object-oriented programming
  skills to organize the logic better, and for that you need Domain Model"
  (Fowler, *PoEAA*, page 161).
- The object needs to be unit-tested in isolation, at speed, without a
  database, and the team wants that as a hard requirement rather than an
  aspiration. Active Record's persistence methods being instance methods on
  the same object makes true isolation from the database awkward without
  extra scaffolding, such as an in-memory adapter, dependency injection of
  the connection, or accepting integration-style tests as the norm.
- The relational schema and the domain concept genuinely diverge, for example
  an aggregate assembled from several tables, a value object reused across
  several entities, or a read model shaped very differently from the write
  model, which is a case where CQRS is a better fit than any single ORM
  pattern.
- Multiple, independently evolving persistence targets exist for the same
  logical entity, such as a relational primary store plus a search index
  plus a cache representation, because Active Record has no natural seam for
  a second persistence mechanism without duplicating the class or bolting on
  ad hoc hooks.
- The team is large enough, or the codebase old enough, that many people are
  touching the same table's Active Record class for unrelated reasons, and
  the class is becoming what practitioners call a "god object" mixing
  unrelated concerns. This is the most commonly reported real-world failure
  mode, discussed in section 11.
- The write path needs coordinated, deferred persistence across many objects
  in one transaction, which is what Unit of Work exists to provide, and which
  is awkward to retrofit onto per-instance eager saves.

## 5. Structure

Fowler's diagram for the pattern names four collaborating responsibilities,
usually folded into fewer physical classes depending on the implementation.

- Active Record instance. One object per row. Holds the row's column values
  as properties, holds instance methods that implement the row's own
  business rules, such as validation, derived values, and small
  calculations, and holds the instance-level persistence operations, most
  commonly `save`, `update`, and `delete`, that act on this one row.
- Finder, class-level or static, methods. Class or static methods that
  perform queries and return one or more instances, for example
  `find(id)`, `findAll()`, or a `where(...)` style query builder. Fowler
  places these on the class rather than the instance because, in his
  words, "before you have a domain object you need some way to find it,"
  so the responsibility of locating a row is necessarily static (Fowler,
  *PoEAA*, page 162).
- Mapping metadata. The knowledge of which table, which columns, and which
  types correspond to the object's properties. In hand-rolled
  implementations this is explicit mapping code. In framework
  implementations, Rails, Eloquent, and Django when used in Active-Record
  style among them, this metadata is inferred by convention from the
  table's schema at runtime, which is why these frameworks avoid a separate
  mapping file for the common case.
- Database gateway, implicit. The actual SQL execution and connection
  handling. Fowler's book keeps this conceptually distinct from the
  domain-and-persistence behavior on the Active Record object even though,
  in most real implementations, the Active Record class itself calls
  straight through to this layer rather than delegating to a separate
  gateway object, which is the key structural difference from Row Data
  Gateway.

The load-bearing structural fact, repeated because it is the source of most
misapplication, is that there is exactly one class per table or view, and
that one class carries both the data and the behavior. There is no separate
"domain object" and "persistence object" for the same row. If a codebase has
both, it has moved to Data Mapper or Repository, not Active Record.

## 6. ASCII structure diagram

```
+----------------------------------+
|          Active Record           |
|  (one class per table/view)      |
+----------------------------------+
| - id                             |
| - column1, column2, ...          |     +-------------------+
| + save()                         |---->|   Database         |
| + update()                       |     |   (table/view)      |
| + delete()                       |<----|                     |
| + validate()                     |     +-------------------+
| + <business logic on this row>() |
+----------------------------------+
| class/static:                    |
| + find(id) : ActiveRecord        |
| + findAll(criteria) : list       |
| + tableName() : string           |
+----------------------------------+
              ^
              | instantiates / populates
              |
+----------------------------------+
|            Client                |
|  (controller, service, script)   |
+----------------------------------+
```

Contrast with Row Data Gateway, where the same shape is split in two.

```
+------------------+        +---------------------+
|   Row Data Obj    |<------>|   Row Data Gateway    |
|  (plain fields)   |  used  |  (find/insert/update)  |
+------------------+  by     +---------------------+
        no behavior here            no domain logic here
```

Active Record fuses these two boxes into one.

## 7. Dynamics

A typical Active Record read-modify-write cycle, drawn as a sequence flow.

```
Client                ActiveRecord.Class      ActiveRecord instance      Database
  |                          |                        |                     |
  |--find(id)-------------->|                        |                     |
  |                          |--SELECT * WHERE id=?-------------------->   |
  |                          |<---------------------- row -----------------|
  |                          |--new(row)------------->|                     |
  |<----instance-------------|                        |                     |
  |                          |                        |                     |
  |--setStatus("paid")----------------------------->  |                     |
  |                          |                        |--validate()         |
  |                          |                        |   (fails? raise)    |
  |--save()------------------------------------------>|                     |
  |                          |                        |--UPDATE ...----->  |
  |                          |                        |<----ack------------|
  |<----success---------------------------------------|                     |
```

The two moments practitioners get wrong are both visible in this diagram.
First, `validate()` runs on the client's thread, inline, as part of `save()`,
so a validation failure is discovered synchronously at save time, not at the
moment the field was set, unless the implementation also validates on
assignment. Second, there is no coordinating object between the client and
the instance managing when the write actually happens. If the client calls
`save()` on five related instances in a loop, each call is its own round
trip, and absent an explicit transaction wrapped around the loop by the
client, each is its own implicit transaction. This is the direct consequence
of Active Record not providing a Unit of Work, discussed further in section
10 and section 11.

A secondary, commonly seen dynamic is lazy loading of an association,
present in Rails' `ActiveRecord` and Laravel's Eloquent. Accessing
`order.customer` on an already-loaded `Order` instance triggers a second
query at the moment of first access, rather than being loaded eagerly with
the original `find`. This is convenient in the common case and is also the
direct mechanical cause of the N+1 query problem discussed in section 11,
where a loop over many `Order` instances each independently triggers a
`customer` query.

## 8. Implementation variants

Judgement, stated plainly. the boundary between these variants is a matter of
practitioner convention rather than something the original source formally
enumerates as sub-patterns, so this section states it as engineering
judgement drawn from observing the listed frameworks, not as a sourced
taxonomy from Fowler.

- Convention-based, schema-inferred. The class declares no mapping at all.
  The framework introspects the table's columns at boot or at class-load
  time and generates accessor properties dynamically. This is Ruby on
  Rails' `ActiveRecord::Base` default behavior and is also how PHP's
  Laravel `Eloquent` model works for its declared `$table` or the
  pluralized class name by convention
  (https://laravel.com/docs/12.x/eloquent, verified 2026-08-02). The
  upside is near-zero boilerplate for a table that already matches the
  class name. The cost is that the mapping is implicit and only
  discoverable by inspecting the live schema or the framework's generated
  documentation.
- Explicit, declared mapping. The class states its columns and types
  directly, either through attributes or decorators or through a small
  configuration block, still keeping persistence methods on the instance.
  Python's Django ORM, when used in its default "fat model" style, is
  closer to this variant. `models.Model` subclasses declare each field
  explicitly as a class attribute, `CharField`, `ForeignKey`, and so on,
  and the resulting objects carry both the data and, when the team chooses
  to put it there, instance methods for behavior, plus a `.save()` and
  `.delete()` method inherited from `Model`
  (https://docs.djangoproject.com/en/5.2/topics/db/models/, verified
  2026-08-02). Django's own documentation is candid that this is a
  deliberate simplification and describes the design as "loosely based on"
  the Active Record pattern rather than a strict implementation, because
  `QuerySet` acts as a query builder layered in front of the model rather
  than every finder living as a static method directly on the model class
  in the Fowler sense.
- Language-idiomatic, macro or annotation driven. Java's early object
  persistence tooling, such as Hibernate's `@Entity` annotations used
  without a separate DAO layer, or lighter frameworks such as jOOQ's
  code-generated record classes, approximate the same idea using
  compile-time code generation or annotations rather than runtime
  reflection, trading some dynamism for compile-time type safety and IDE
  support.
- Hand-rolled, no framework. A team writes the class by hand. Fields, a
  `find` static method executing a hand-written `SELECT`, a `save` method
  executing a hand-written `UPDATE` or `INSERT`. This is the closest
  implementation to Fowler's own book, which shows exactly this shape in
  Java, and it remains common in small services, CLI tools, and any
  context where pulling in a full ORM is judged not worth the dependency
  weight.
- Value-object-returning variant. Some modern statically typed
  implementations, idiomatic Rust and Go database code, and Kotlin
  exposed's `IntEntity` style among them, keep the "load and save this
  row" responsibility on a dedicated type but favor immutable value
  construction over mutable in-place field assignment, calling `.save()` a
  method that persists the currently held immutable snapshot rather than
  mutating fields directly before a call. This keeps the Active Record
  shape, the object still knows how to load and save itself, while
  adapting it to a language culture that disfavors uncontrolled
  mutability.

## 9. Known production uses

At least two required by the template, four are named here, each
independently verifiable.

1. Ruby on Rails, `ActiveRecord` gem. The reference implementation for the
   term as most working programmers encounter it. Ships as part of every
   default Rails application since Rails 1.0, December 2005, and its own
   README states it "implements the Active Record pattern"
   (https://github.com/rails/rails/blob/main/activerecord/README.rdoc,
   verified 2026-08-02). It is the library that made the pattern's name a
   household term in web development.
2. Laravel, `Eloquent` ORM. PHP's most widely used web framework ships
   `Eloquent` as its default ORM, and its own documentation states plainly,
   "Each database table has a corresponding \"Model\" which is used to
   interact with that table. Models allow you to query for data in your
   tables, as well as insert new records into the table"
   (https://laravel.com/docs/12.x/eloquent, verified 2026-08-02), which is
   the Active Record shape described in Fowler's catalog entry applied to
   PHP.
3. Django, `django.db.models.Model`. Python's dominant full-stack web
   framework gives every model class its own `.save()` and `.delete()`
   instance methods, plus a query interface reachable from the class
   through `Model.objects`, documented at
   https://docs.djangoproject.com/en/5.2/topics/db/models/, verified
   2026-08-02. Django's own documentation describes the design as inspired
   by the Active Record pattern while layering a separate `QuerySet` query
   builder in front of it, making it a partial rather than textbook
   implementation, which is exactly the kind of nuance this entry's
   "known production uses" section exists to record honestly rather than
   flatten into a blanket claim.
4. Yii Framework, PHP, `yii\db\ActiveRecord`. A long-running PHP framework
   whose ORM class is literally named `ActiveRecord` and whose guide
   documents it as implementing the pattern directly. "Active Record
   provides an object-oriented interface for accessing and manipulating
   data stored in databases," and the class is `yii\db\ActiveRecord`
   (https://www.yiiframework.com/doc/guide/2.0/en/db-active-record,
   verified 2026-08-02).

Each of these four is a widely deployed, independently maintained piece of
software still in active use as of the verification date above, satisfying
the template's requirement for a real, named, sourced production use rather
than a generic claim.

## 10. Consequences

Positive consequences.

- Rapid development for CRUD-dominated screens, because there is one place
  to look for both the shape of a row and its simple behavior, with no
  separate mapping layer to keep in sync by hand for the common case.
- Low ceremony for newcomers. Reading one class answers "what does this
  entity look like" and "what can I do with it" simultaneously.
- Framework tooling, migrations, scaffolding, admin generators, can be
  built cheaply against the pattern because the schema and the object
  shape are, by construction, tightly coupled, which is exactly what a
  scaffolding tool wants to introspect.
- Explicit, synchronous persistence calls, `save()` and `delete()` among
  them, give an obvious, easy-to-trace mental model of when a write
  actually happens, compared to patterns that batch or defer writes.

Negative consequences.

- Domain logic is coupled to the database schema. A column rename, a table
  split, or a normalization change forces a change to the object that
  business logic also depends on, so a purely structural database change
  can ripple into behavior-carrying code.
- Testing business logic in isolation from a real or in-memory database is
  awkward by default, because persistence and behavior share one object.
  Fowler notes this tension directly when discussing when to prefer Domain
  Model instead (Fowler, *PoEAA*, page 161).
- The pattern scales poorly with growing behavioral complexity. As more
  business rules accumulate on the same table's class, from many
  contributors touching unrelated features, the class tends to grow into
  what the Rails and wider Ruby community commonly calls a "fat model," a
  form of the God Object anti-pattern where one class accumulates
  responsibilities that belong to several collaborators.
- No natural home for cross-table invariants or aggregates, because each
  Active Record instance is scoped to one row of one table by definition.
- No coordinated write ordering or deferred flush across several instances
  without the client wrapping calls in an explicit transaction itself,
  because the pattern provides no Unit of Work.

## 11. Failure modes and misuse

Judgement, stated plainly. the symptoms below are drawn from widely reported
practitioner experience with Rails, Laravel, and Django applications rather
than from a single citable source for each. The underlying mechanism for
each, the N+1 query pattern, and the mapping between schema coupling and fat
models, is established computer science, not a novel claim.

| Symptom (what you would actually observe) | Cause | Fix |
|---|---|---|
| A single page load issues dozens or hundreds of near-identical SQL queries, visible in a query log or APM trace, each fetching one related row | A loop iterates over N Active Record instances and accesses a lazily loaded association inside the loop, so each access triggers its own query. This is the N+1 query problem | Eager-load the association before the loop, using `includes` in Rails, `with` in Eloquent, `select_related` or `prefetch_related` in Django, or batch-fetch the related rows separately and join them in memory |
| A model class grows to hundreds or thousands of lines, with methods spanning unrelated concerns, billing, notifications, formatting, authorization, all living on the same table's class | Every new business rule that mentions this entity gets added as an instance method because that is the path of least resistance in an Active Record codebase, over months or years, with no natural pressure pushing unrelated concerns into separate collaborators | Extract cohesive groups of methods into plain service objects, value objects, or concerns and modules that the Active Record instance delegates to, keeping persistence on the record and moving multi-step business processes elsewhere |
| Saving one object silently leaves a related object in an inconsistent state after a partial failure, discovered later as orphaned or mismatched rows | Multiple `save()` calls on related instances are each their own implicit transaction. A failure partway through a multi-object operation commits the earlier saves and rolls back nothing | Wrap the whole multi-object operation in an explicit database transaction supplied by the client code, `ActiveRecord::Base.transaction`, Eloquent's `DB::transaction`, Django's `atomic()`, or move the coordination into an explicit Unit of Work if this recurs often |
| Unit tests for a piece of business logic are slow, and fail in CI due to missing database connectivity, even though the logic being tested does not obviously need a database | The business method lives directly on the Active Record class, so exercising it in a test instantiates and often persists a real, or in-memory, database-backed object | Extract the pure calculation into a plain function or value object taking primitive inputs, and keep only the persistence-adjacent glue on the Active Record class, or accept integration-style testing as the deliberate trade-off of choosing this pattern |
| A validation that should have caught bad data did not fire, and a row with invalid state exists in the database | Validation was bypassed by a raw SQL update, a bulk-update helper that skips instance callbacks, Rails' `update_all`, Eloquent's mass `update()` on a query builder, or an external process writing to the table directly | Restrict direct SQL and bulk-update helpers on validated tables to reviewed, deliberate cases, and prefer instance-level saves for anything that must honor validations, or move the invariant into a database constraint as a second line of defense |
| Reworking the schema, a normalization, a column split, forces edits across many unrelated feature files that use the affected model | Domain logic that only conceptually cares about business meaning ended up depending on column names and shapes directly, because Active Record gives no seam between how the row is shaped and what the row means | Introduce accessor methods or computed properties on the record as the one seam that changes, or migrate the affected concern to a Domain Model object once the coupling becomes a recurring maintenance cost |

## 12. Trade-off matrix

Comparison against named alternatives from the same catalog family, across the
forces named in section 3.

| Force | Active Record | Table Data Gateway | Row Data Gateway | Domain Model |
|---|---|---|---|---|
| Velocity for simple CRUD | Highest, one class, generated mapping, save/find on the instance | High, but callers manipulate raw data plus a separate gateway, two objects to touch | Medium, still two objects, data holder plus gateway, per table | Lowest for pure CRUD, the extra separation is overhead when there is little behavior to separate |
| Separation of persistence from behavior | Low, persistence and domain logic share one class | High for pure CRUD tables, because there is no per-row domain object at all, only a table-wide gateway | Medium, the row holder is typically free of domain logic, closer to a struct | Highest, persistence lives in a separate mapper, domain object is pure |
| Testability of business logic without a database | Low by default, needs deliberate extraction to test in isolation | N/A in the same sense, there is usually little standalone domain logic to test since the gateway does not carry it | Low, same coupling concern as Active Record if behavior is added to the row object | High, the domain object has no persistence dependency to fake or connect to |
| Fit for complex, multi-object business rules | Poor, no natural home for cross-row or cross-table invariants | Poor, gateway is data-access only, not a home for domain rules at all | Poor, for the same reason as Active Record if behavior creeps in | Strong, this is the pattern's stated purpose |
| Coordinated, deferred writes across many objects | Weak, no Unit of Work, client must wrap explicit transactions itself | Weak, same reason | Weak, same reason | Strong when paired with an explicit Unit of Work, which Domain Model is commonly combined with |
| Onboarding legibility for a new contributor | High, one file explains both shape and behavior | Medium, behavior for a table lives centrally but data shape is separate from any per-row object | Medium, similar split as Table Data Gateway but per-row | Lower initially, requires understanding the mapper plus the domain object plus how they connect |

## 13. Related and incompatible patterns

Row Data Gateway. The closest sibling and the pattern from which Active
Record is most easily confused. Row Data Gateway keeps one object per row,
the same granularity as Active Record, but that object holds no domain logic
at all, only the data and the raw find, insert, update, delete operations.
Any business rule lives elsewhere. Active Record is what you get when you
fold a Row Data Gateway's persistence methods and a plain data-holder's
fields into one class and then also add domain behavior to that same class.
A codebase migrating away from Active Record toward more separation often
passes through Row Data Gateway as an intermediate step, by pulling the
domain-behavior methods off the record class first while leaving persistence
in place.

Table Data Gateway. Structurally incompatible with Active Record for the
same table, because Table Data Gateway centralizes all SQL for a table into
one gateway object shared across many plain data holders, whereas Active
Record puts the SQL access directly on each row's own class. A codebase
would not normally use both patterns on the same table simultaneously.
Doing so duplicates the SQL access path and invites the two mechanisms to
drift out of sync, which is why this entry's frontmatter lists Table Data
Gateway under `incompatible_with`.

Domain Model. The pattern most teams graduate to when Active Record's
domain logic outgrows what a single table-shaped class can cleanly hold.
Domain Model composes naturally with Data Mapper, a separate pattern in the
same PoEAA family not covered in this entry, rather than with Active
Record's built-in persistence methods, because Domain Model's whole point
is keeping the domain object free of persistence concerns. Migrating from
Active Record to Domain Model is a substantial refactor, discussed in
section 14, not a drop-in swap.

Unit of Work. Frequently paired with Domain Model and Data Mapper to
coordinate deferred, batched writes across many objects in one transaction.
Active Record implementations sometimes bolt on a partial Unit of Work,
Rails' `ActiveRecord::Base.transaction` block or Django's `atomic()`
context manager among them, to get transactional safety around a group of
otherwise-independent per-instance saves, but this is a workaround layered
on top of Active Record's eager-save default, not the same coordinated,
deferred-flush behavior a true Unit of Work provides.

Identity Map. Commonly combined with Active Record implementations to
avoid loading two different in-memory objects representing the same
database row within one request, preventing the two objects' in-memory
state from silently diverging. Rails' `ActiveRecord` does not implement a
strict Identity Map by default within a single request in the way some
Java ORMs enforce it, which is a frequently misunderstood detail worth
flagging. Assuming Identity Map guarantees hold, when the specific
implementation does not provide them, is a real source of subtle bugs
where two "different" objects for the same row diverge after independent
mutation.

Transaction Script. An alternative organizing principle for the whole
business logic layer, not specifically for the persistence layer, and the
two patterns solve different problems. Transaction Script organizes logic
procedurally by use case, Active Record organizes logic and persistence
around a table. They are frequently seen together in small applications,
where a Transaction Script method loads and saves several Active Record
instances as steps in one procedure.

## 14. Refactoring path in and out

Introducing Active Record into code that does not have it, when a
Transaction Script or raw SQL-scattered codebase has accumulated enough
repeated per-table CRUD logic to justify consolidation.

1. Identify a table whose access is scattered across several procedures as
   ad hoc SQL, and confirm its domain logic is genuinely simple, the
   applicability check in section 4.
2. Create one class named for the singular business concept the table
   represents, with fields matching the table's columns.
3. Move the table's `SELECT` logic into static or class-level finder
   methods on the new class, replacing call sites one at a time so each
   replacement is independently verifiable.
4. Move the table's `INSERT` and `UPDATE` logic into an instance `save()`
   method, again replacing call sites incrementally.
5. Move any validation or small business rule that reads the row's own
   fields into instance methods on the class, verifying each moved rule
   still fires at the same point in the flow it used to.
6. Only after the mechanical CRUD is centralized should genuinely
   table-scoped business behavior be added directly to the class. Anything
   that spans more than this one table's own fields is a signal to stop
   and reconsider Domain Model instead of continuing to grow this class.

Removing Active Record from code where it has outgrown its fit, moving
toward Domain Model plus Data Mapper.

1. Identify the subset of methods on the Active Record class that are
   genuinely persistence concerns, finders, `save`, `delete`, raw column
   access, versus the subset that are business rules.
2. Extract the business-rule methods into a new, persistence-free domain
   class, initially delegating to the still-existing Active Record
   instance for any data it needs, so the extraction is
   behavior-preserving at each step. This mirrors Extract Class from
   Martin Fowler's refactoring catalog, *Refactoring, Improving the
   Design of Existing Code*, 2nd edition, 2018, and can be verified
   against the wider refactoring family entry in this repository for the
   general technique.
3. Introduce a mapper responsible for translating between the row shape
   and the new domain object's shape, initially thin, essentially a
   pass-through, so it can be swapped in without changing behavior.
4. Redirect callers to construct and query through the domain object plus
   mapper, retiring direct calls to the old Active Record class's finder
   and save methods one call site at a time.
5. Once no caller depends on the old class directly, delete it, or narrow
   it down to a pure Row Data Gateway if some code still benefits from raw
   row access alongside the new Domain Model layer.
6. Introduce a Unit of Work once more than one domain object commonly
   needs to be saved together as one transactional operation, rather than
   before it is needed.

## 15. Testing and verification

Judgement, stated plainly. this section is drawn from common testing
practice around the named production implementations rather than a single
source, since testing strategy is practice, not a fact a source can be
wrong about.

What becomes easy. End-to-end and integration-style tests are natural,
because the object that represents the business concept is the same object
that talks to the database, so a test can create a record, exercise a
method, and assert on the persisted state, all through one API. Frameworks
built around Active Record, Rails' `ActiveSupport::TestCase` with fixtures
or factories, Laravel's model factories, Django's `TestCase` with its
transaction-wrapped test isolation, invest heavily in making this specific
kind of test fast and convenient, because it is the kind of test the
pattern naturally produces.

What becomes hard. Isolating a single business rule from the database
becomes awkward without deliberate extraction, because calling any method
on the object implicitly drags in whatever persistence machinery the base
class provides, even for logic that does not conceptually need a database
at all. Three practical techniques mitigate this without abandoning the
pattern.

- Use an in-memory or SQLite-backed test database rather than a full
  production-equivalent database, trading perfect fidelity for test speed.
  This is the default in Rails, Laravel, and Django test suites.
- Extract pure calculation logic, anything computable from the object's
  already-loaded fields with no further query, into plain functions or
  value objects that the Active Record method delegates to, and unit test
  the extracted function directly with no database at all.
- Use the framework's factory or fixture tooling, Laravel model factories,
  FactoryBot for Rails, Django's `factory_boy` convention among them, to
  construct valid instances quickly in tests, keeping test setup from
  becoming its own maintenance burden as the schema evolves.

Test doubles are of limited use for the Active Record instance itself,
because mocking the class's own static finder methods tends to produce
brittle tests that assert on implementation details, which query ran,
rather than behavior. The more durable technique is to test against a
real, disposable test database and assert on outcomes.

## 16. Observability signals

Judgement, stated plainly. these signals reflect common operational
practice around relational-backed Active Record systems, not a formal
specification.

What to log or trace. Every query the Active Record class issues, ideally
tagged with the calling method and, where the framework supports it, the
originating request or job, so that a query log or APM trace can attribute
each query back to the code path that triggered it. Rails' query log and
Laravel's query log listener are both designed around exactly this
attribution.

What to measure. Query count per request or per background job,
specifically watched for growth over time or for spikes correlated with a
specific endpoint, because an unbounded or rapidly growing query count per
request is the primary operational symptom of the N+1 problem described in
section 11. Slow query logs at the database level, correlated against the
ORM's own generated SQL, surface cases where the convenience of automatic
query generation produced an inefficient query shape, a missing index, an
unnecessarily wide `SELECT *`, a Cartesian-product join from a poorly
specified eager load.

What a healthy instance of this pattern looks like on a dashboard. A
roughly constant, low query count per request regardless of the size of
the result set being displayed, indicating eager loading is used
correctly, and transaction duration histograms with a tight distribution,
indicating writes are not routinely left open across slow, unrelated work
inside the same transaction block. A failing instance looks like query
count per request scaling linearly, or worse, with the number of records
displayed, or transaction duration growing over months as more business
logic gets stuffed into the same save-time callback chain without anyone
noticing the cumulative cost.

## 17. Security and privacy implications

The pattern's main attack-surface implication is indirect, through the SQL
generation convenience that framework implementations provide. When query
building is exposed as a mostly automatic, string-composition-based
mechanism, developers occasionally drop down to raw SQL fragments for a
query the ORM cannot express cleanly, and that fragment, if it concatenates
untrusted input directly, reopens classic SQL injection risk that the ORM's
parameterized query builder would otherwise have closed. This is not a flaw
specific to Active Record as a pattern, and applies to any ORM's raw-query
escape hatch. It is worth naming here because Active Record implementations
in particular, Rails' `where("raw sql #{param}")` anti-pattern, Laravel's
`DB::raw()`, Django's `.raw()` or `.extra()` among them, are commonly
reached for precisely because the pattern's convention-based model makes
anything outside the conventional shape feel like friction, which is
exactly the moment a developer is tempted to write a raw string.

Mass-assignment is the second named concern specific to how several Active
Record implementations historically worked. A convenience feature that
lets a caller populate many fields on the object at once from an untrusted
hash or form payload, Rails' pre-4.0 `attr_accessible` and
`attr_protected` history, Laravel's `$fillable` and `$guarded` model
properties among them, can, if misconfigured, let an attacker set fields
the application never intended to expose through that form, such as an
`is_admin` flag riding along on an otherwise legitimate profile-update
request. This is a well documented historical vulnerability class in Rails
specifically. CVE-2012-2660, CVE-2012-2661, and CVE-2012-2695 are three of
several Rails mass-assignment CVEs from that era
(https://groups.google.com/g/rubyonrails-security/, referenced by the
Rails security advisories archive, verified 2026-08-02 for the existence
of the advisory thread, not for reproducing exploit detail here). Both
Rails and Laravel now default to an explicit allowlist, `permit` with
strong parameters in Rails, `$fillable` in Laravel, specifically in
response to this history.

On the data-handling side, Active Record's convenience in exposing an
object's full set of columns as readable properties means it is easy to
accidentally serialize a sensitive column, a password hash, an internal
note field, into an API response or a log line, simply because the object
makes every column equally easy to reach without a deliberate projection
step. This is a design-discipline concern rather than a defect in the
pattern itself, and the mitigation, an explicit serialization allowlist or
a dedicated view or DTO layer between the Active Record instance and any
external-facing payload, is the same discipline any object-relational
pattern needs, stated here because Active Record's low-friction property
access makes skipping that discipline unusually easy.

## 18. References

1. Martin Fowler, *Patterns of Enterprise Application Architecture*,
   Addison-Wesley, 2002, chapter 11, "Active Record," pages 160 to 165.
2. Martin Fowler, "Active Record" catalog page,
   https://martinfowler.com/eaaCatalog/activeRecord.html, verified
   2026-08-02.
3. Martin Fowler, *Refactoring, Improving the Design of Existing Code*,
   2nd edition, Addison-Wesley, 2018, referenced for the general Extract
   Class refactoring technique used in section 14.
4. Ruby on Rails, `activerecord` README,
   https://github.com/rails/rails/blob/main/activerecord/README.rdoc,
   verified 2026-08-02.
5. Laravel documentation, "Eloquent, Getting Started,"
   https://laravel.com/docs/12.x/eloquent, verified 2026-08-02.
6. Django documentation, "Models,"
   https://docs.djangoproject.com/en/5.2/topics/db/models/, verified
   2026-08-02.
7. Yii Framework guide, "Active Record,"
   https://www.yiiframework.com/doc/guide/2.0/en/db-active-record, verified
   2026-08-02.
8. Rails security advisories archive, referenced for the existence of the
   2012 mass-assignment CVE cluster discussed in section 17, Ruby on Rails
   Security mailing list, https://groups.google.com/g/rubyonrails-security/,
   verified 2026-08-02.
9. Wikipedia, "Factory method pattern," cited only for cross-checking the
   Gamma, Helm, Johnson, Vlissides attribution style used across this
   repository's other entries, consistent with section 1's citation of the
   sibling entry, https://en.wikipedia.org/wiki/Factory_method_pattern,
   verified 2026-08-02.

## Code examples

### TypeScript

```typescript
interface Row {
  id: number;
  title: string;
  price_cents: number;
  status: string;
}

class Product {
  id: number;
  title: string;
  priceCents: number;
  status: string;

  private static rows: Map<number, Row> = new Map();
  private static nextId = 1;

  constructor(row: Row) {
    this.id = row.id;
    this.title = row.title;
    this.priceCents = row.price_cents;
    this.status = row.status;
  }

  static find(id: number): Product {
    const row = Product.rows.get(id);
    if (!row) {
      throw new Error(`Product ${id} not found`);
    }
    return new Product(row);
  }

  static create(title: string, priceCents: number): Product {
    const row: Row = {
      id: Product.nextId++,
      title,
      price_cents: priceCents,
      status: "draft",
    };
    Product.rows.set(row.id, row);
    return new Product(row);
  }

  publish(): void {
    if (this.priceCents <= 0) {
      throw new Error("cannot publish a product with no price");
    }
    this.status = "published";
    this.save();
  }

  save(): void {
    Product.rows.set(this.id, {
      id: this.id,
      title: this.title,
      price_cents: this.priceCents,
      status: this.status,
    });
  }
}

const p = Product.create("Widget", 1999);
p.publish();
const reloaded = Product.find(p.id);
console.log(reloaded.status, reloaded.priceCents);
```

### Python

```python
from typing import Dict


class Product:
    _table: Dict[int, dict] = {}
    _next_id = 1

    def __init__(self, id: int, title: str, price_cents: int, status: str):
        self.id = id
        self.title = title
        self.price_cents = price_cents
        self.status = status

    @classmethod
    def find(cls, id: int) -> "Product":
        row = cls._table.get(id)
        if row is None:
            raise ValueError(f"Product {id} not found")
        return cls(**row)

    @classmethod
    def create(cls, title: str, price_cents: int) -> "Product":
        id = cls._next_id
        cls._next_id += 1
        row = {"id": id, "title": title, "price_cents": price_cents, "status": "draft"}
        cls._table[id] = row
        return cls(**row)

    def publish(self) -> None:
        if self.price_cents <= 0:
            raise ValueError("cannot publish a product with no price")
        self.status = "published"
        self.save()

    def save(self) -> None:
        Product._table[self.id] = {
            "id": self.id,
            "title": self.title,
            "price_cents": self.price_cents,
            "status": self.status,
        }


if __name__ == "__main__":
    p = Product.create("Widget", 1999)
    p.publish()
    reloaded = Product.find(p.id)
    print(reloaded.status, reloaded.price_cents)
```

### Go

```go
package main

import (
	"errors"
	"fmt"
)

type row struct {
	id         int
	title      string
	priceCents int
	status     string
}

var table = map[int]row{}
var nextID = 1

type Product struct {
	ID         int
	Title      string
	PriceCents int
	Status     string
}

func FindProduct(id int) (*Product, error) {
	r, ok := table[id]
	if !ok {
		return nil, errors.New("product not found")
	}
	return &Product{r.id, r.title, r.priceCents, r.status}, nil
}

func CreateProduct(title string, priceCents int) *Product {
	id := nextID
	nextID++
	r := row{id, title, priceCents, "draft"}
	table[id] = r
	return &Product{r.id, r.title, r.priceCents, r.status}
}

func (p *Product) Save() {
	table[p.ID] = row{p.ID, p.Title, p.PriceCents, p.Status}
}

func (p *Product) Publish() error {
	if p.PriceCents <= 0 {
		return errors.New("cannot publish a product with no price")
	}
	p.Status = "published"
	p.Save()
	return nil
}

func main() {
	p := CreateProduct("Widget", 1999)
	if err := p.Publish(); err != nil {
		panic(err)
	}
	reloaded, err := FindProduct(p.ID)
	if err != nil {
		panic(err)
	}
	fmt.Println(reloaded.Status, reloaded.PriceCents)
}
```

Java and Rust are omitted from the runnable set for this entry. Judgement,
stated plainly. the pattern is not less idiomatic in either language, but a
fourth and fifth runnable example add limited additional understanding once
three languages across two different typing disciplines, structural
TypeScript, dynamic Python, static Go, already show the finder-plus-instance-
save shape. The Structure and Dynamics sections above are language-neutral
and apply identically to a Java or Rust rendition of the same class shape.
