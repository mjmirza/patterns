---
name: Row Data Gateway
slug: row-data-gateway
family: 06-enterprise-application-architecture
category: Data Source Architectural
aliases: [Row Gateway, Record Gateway]
first_described: "Fowler 2002"
maturity: canonical
related: [table-data-gateway, active-record, data-mapper, gateway, identity-map]
incompatible_with: []
verified: 2026-08-02
---

# Row Data Gateway

## 1. Name, aliases, and lineage

The canonical name is Row Data Gateway. It is one of the four data source
architectural patterns Martin Fowler catalogs in *Patterns of Enterprise
Application Architecture*, Addison-Wesley, 2002, chapter 10, "Data Source
Architectural Patterns". Fowler states the intent as "an object that acts as a
Gateway to a single record in a data source. There is one instance per row"
([Row Data Gateway, martinfowler.com/eaaCatalog](https://martinfowler.com/eaaCatalog/rowDataGateway.html),
verified 2026-08-02).

The name is stable across the industry. Where a variation appears, it is a
literal renaming rather than a competing definition. The PHP framework Zend
Framework 2, and its successor project Laminas, ship a class named
`RowGateway` whose documentation states it "implements the Row Data Gateway
pattern described in the book Patterns of Enterprise Application Architecture"
([Row Gateways, laminas-db documentation](https://docs.laminas.dev/laminas-db/row-gateway/),
verified 2026-08-02). That is the same pattern under the shortened name Row
Gateway, not a different design.

Fowler groups Gateway patterns under a broader Gateway pattern defined earlier
in the same book as "an object that encapsulates access to an external system
or resource" (Fowler, *PoEAA*, chapter 18, Gateway). Row Data Gateway is the
specialization of that general idea for the specific external resource of a
single database row, as opposed to Table Data Gateway, which wraps access to
an entire table, or a general Gateway, which might wrap a web service or a
message queue instead of a database.

Fowler is explicit that Row Data Gateway is the least distinctive of the four
data source patterns in the same chapter, calling it "one of the patterns I've
used the least" in the pattern's own catalog page, because in most codebases
either a thinner Table Data Gateway or a richer Active Record already covers
the same ground more cheaply
([Row Data Gateway, martinfowler.com/eaaCatalog](https://martinfowler.com/eaaCatalog/rowDataGateway.html),
verified 2026-08-02). That admission from the pattern's own author matters more
than most catalog entries admit about themselves, and this entry treats it as
load-bearing rather than as a footnote.

## 2. Problem and context

A codebase has business logic that needs to read a single row from a
relational table, change some of its columns, and write the row back. The team
wants that access wrapped behind a language-native interface, an object whose
fields the calling code reads and writes with ordinary property access,
because writing raw SQL or handling a cursor at every call site scatters
knowledge of the schema across the codebase and makes every caller responsible
for column names, parameter binding, and null handling.

The plain, un-wrapped alternative looks like this in a codebase that has not
adopted any data source pattern. A method somewhere builds a `SELECT` string
with the primary key inline, executes it, and pulls values out of a result set
by column name or index, at every call site that needs a person's record. A
second method somewhere else builds the matching `UPDATE` string, with its own
set of hand-typed column names, drifting slowly out of sync with the first
method as the schema changes. A third piece of code, perhaps years later,
copies the pattern for a new table and repeats every mistake the first two
methods already made.

Fowler names two consequences of that scattering directly. First, "if your
in-memory objects have business logic of their own, it's not a good idea to
add code to manipulate a database as well," because the two responsibilities,
domain behavior and persistence mechanics, pull the same class in different
directions and make each harder to change without touching the other. Second,
"testing is awkward" when domain objects reach straight into a live connection,
because every test of business logic then also pays the cost of a database
round trip
([Row Data Gateway, martinfowler.com/eaaCatalog](https://martinfowler.com/eaaCatalog/rowDataGateway.html),
verified 2026-08-02).

Row Data Gateway answers this narrowly. It does not try to give the object
business behavior, and it does not try to give the object knowledge of other
tables or of the object graph. It gives exactly one thing, a class shaped like
one row, whose fields correspond one-to-one with columns, and whose methods
correspond one-to-one with the CRUD operations a row supports, find, insert,
update, delete. Everything else, validation rules, calculations, workflow, is
left for the caller or for a separate domain object that wraps or delegates to
the gateway.

The context in which this narrow answer earns its cost has three parts.

- The application already organizes its logic outside the data classes, most
  often as Transaction Script, so there is no natural home for behavior inside
  the row object, and giving it none is not a loss.
- The schema maps closely to the language's native types, so the gateway's job
  is thin, mostly type conversion and a little null handling, rather than a
  translation between two very different shapes.
- More than one kind of caller needs the same row, for example a web
  controller and a batch job, and both want an object rather than raw SQL, but
  neither wants a shared domain object with business rules baked in.

## 3. Forces

This entry states its own weighting of the forces below as engineering
judgement, not as a claim from Fowler's text, and marks the reasoning as such.

- **Coupling to schema versus coupling to SQL.** Every caller that used to
  write its own `SELECT` and `UPDATE` now depends on the gateway's field names
  instead of on raw column strings. That is a strict improvement in the
  direction of coupling, because a schema change now touches one class instead
  of every call site, but the coupling itself does not disappear, it moves.
- **Testability versus fidelity.** A Row Data Gateway can be swapped for an
  in-memory Test Double relatively easily, because its interface is a plain
  object with getters, setters, and four persistence methods. The trade is
  that the double will not catch a constraint violation, a trigger, or a type
  coercion the real database would enforce, so cheap unit tests and end-to-end
  correctness pull in opposite directions.
- **Simplicity versus behavior.** The pattern deliberately puts no domain
  logic in the row class. That keeps the class small and easy to generate, but
  it pushes every calculation, validation, and derived field out to a caller,
  which then has to remember to call the right sequence of gateway methods in
  the right order. Active Record resolves this same force differently by
  accepting the coupling of behavior to persistence in exchange for not having
  to write that calling code twice.
- **Granularity of the database round trip.** One instance per row means one
  query per row lookup by default, which is fine for a single record fetched
  by primary key and becomes an N+1 query problem the moment a caller loops
  over a collection and calls `find` inside the loop. Table Data Gateway
  resolves this force in the opposite direction by returning a whole result
  set from one query.
- **Generated code versus hand-written code.** Because a Row Data Gateway
  class is column-for-column with the table, it is one of the easiest OO
  artifacts to generate from schema metadata. Teams that generate it accept a
  build-time dependency on a code generator and a churn cost every time the
  schema changes, in exchange for near-zero manual maintenance of the
  boilerplate. Teams that hand-write it accept ongoing manual maintenance in
  exchange for full control over the generated shape, including places where
  the generator would have gotten it wrong.
- **Team topology.** A team that owns its own schema and reads it directly
  benefits least from the strict field-by-field boundary a gateway imposes,
  because the team could just as well put light domain logic straight on an
  Active Record. A team that must integrate with a schema owned by someone
  else, where the schema might legitimately not match any sensible domain
  model, benefits most, because the gateway lets the persistence shape and the
  domain shape diverge without either one distorting the other.

## 4. Applicability and non-applicability

Reach for Row Data Gateway when all of the following hold.

- The application already uses Transaction Script or a similar procedural
  organization for its business logic, so there is no natural home inside the
  data class for domain behavior, and a thin CRUD wrapper is the whole job.
- The object needs to look and behave like an in-language object to its
  callers, hiding SQL, cursors, and column indices, but does not need any
  cross-table knowledge, joins, or query building of its own.
- The team can tolerate one query per row and either does not fetch large
  collections through this class, or accepts pairing it with a Table Data
  Gateway or a finder that returns a batch of Row Data Gateway instances from
  one query.
- The row shape is generated or trivially hand-written from a schema that
  changes rarely enough that regenerating or re-typing the class is not a
  burden.

Do NOT reach for Row Data Gateway when any of the following holds.

- The domain has real behavior, validation, or invariants that belong on the
  object representing a person, an order, or an account. Putting that behavior
  on a Row Data Gateway either produces an Active Record by definition, since
  Fowler's own dividing line is exactly the presence of domain logic
  ([Row Data Gateway, martinfowler.com/eaaCatalog](https://martinfowler.com/eaaCatalog/rowDataGateway.html),
  verified 2026-08-02), or it produces a smell where persistence code and
  domain code sit uneasily in the same class without the team ever deciding
  which pattern they actually chose.
- The application is built around a rich Domain Model with associations, where
  objects reference other objects rather than foreign key columns. Data
  Mapper, not Row Data Gateway, is the pattern that keeps that domain model
  free of persistence knowledge while still handling the load and save of the
  object graph.
- The dominant access pattern fetches many rows at once and processes them as
  a set, for example a report or a bulk export. Table Data Gateway, which
  returns a whole result set from one query, avoids the N+1 problem that a
  loop of per-row `find` calls creates.
- The team is using an ORM with a mapping layer already, for example
  Hibernate, Entity Framework, or SQLAlchemy's ORM layer. Hand-rolling a Row
  Data Gateway underneath an ORM duplicates work the ORM already does and
  fights the ORM's own identity and change tracking.
- The schema and the desired in-memory shape genuinely differ, for example a
  normalized schema that should present as a single denormalized object, or a
  single table that should present as two related domain concepts. A gateway
  that mirrors the table column for column cannot bridge that gap, and forcing
  it to try produces a class that is neither a clean gateway nor a clean
  domain object.
- The system needs optimistic concurrency, auditing, or change tracking across
  many rows at once, which a per-instance gateway with no shared session or
  identity map cannot provide by itself.

## 5. Structure

- **Row Data Gateway.** One class per table. One instance of that class per
  row. Holds one field per column, typed to the language's native equivalent
  of the column type. Exposes `find` as a static or class-level factory that
  loads one row by key and returns a populated instance. Exposes `insert`,
  `update`, and `delete` as instance methods that persist the current field
  values back to the same row. Contains no domain logic, no validation beyond
  what is needed to bind values into SQL parameters, and no knowledge of other
  tables.
- **Data source connection.** The gateway holds, or is handed, a reference to
  whatever the platform uses to talk to the database, a `Connection` in Java's
  JDBC, a database handle in Python's DB-API, a client object in a Node.js
  driver. The gateway is responsible for issuing SQL through that connection
  and mapping the result back into its own fields, and for nothing beyond
  that.
- **Caller.** A Transaction Script, a controller, or a service method that
  asks the gateway class to `find` a row, reads or writes fields on the
  returned instance using ordinary object syntax, and calls `update` or
  `delete` when it is done. The caller owns the transaction boundary, the
  gateway itself does not decide when to commit.
- **Optional identity mechanism.** Nothing in the base pattern prevents two
  separate `find` calls for the same primary key from returning two separate
  objects that both refer to the same row, and by default they do. A team that
  needs the guarantee that one row maps to exactly one in-memory object adds
  an Identity Map in front of the gateway's `find` method, which is a separate
  pattern layered on top, not a required part of Row Data Gateway itself.

## 6. ASCII structure diagram

```
+---------------------------+
|   Transaction Script /    |
|   Controller (caller)     |
+-------------+-------------+
              | find(id) / new PersonGateway(...)
              v
+---------------------------+        +---------------------------+
|      PersonGateway        |------->|   Connection / DB handle  |
|----------------------------|  uses |   (JDBC, DB-API, driver)  |
| - id: Long                |        +-------------+-------------+
| - firstName: String       |                      |
| - lastName: String        |                      | SQL over the wire
| - numberOfDependents: int |                      v
|----------------------------|          +---------------------------+
| + find(conn, id): Gateway |          |     people (table)        |
| + insert(): void          |          |----------------------------|
| + update(): void          |          | id | first_name | last_name |
| + delete(): void          |          |----|------------|-----------|
+---------------------------+          | 1  | Martin     | Fowler    |
              ^                        | 2  | Kent       | Beck      |
              | one instance per row   +---------------------------+
              |
+---------------------------+
|      OrderGateway         |   (a sibling class exists per table,
|      InvoiceGateway       |    each one still one instance per row)
+---------------------------+
```

## 7. Dynamics

The sequence below traces a caller loading a row, changing a field, and
writing the change back. The gateway never keeps state beyond its own fields
and the connection it was handed, there is no session, no unit of work, no
identity map unless the team adds one separately.

```
Caller                  PersonGateway.find            Database
  |                            |                          |
  | find(conn, personId)       |                          |
  |--------------------------->|                          |
  |                            | SELECT ... WHERE id = ?   |
  |                            |------------------------->|
  |                            |         one row           |
  |                            |<-------------------------|
  |                            | new PersonGateway(fields) |
  | <PersonGateway instance>   |                          |
  |<---------------------------|                          |
  |                                                        |
  | gateway.numberOfDependents = 3                         |
  |------------------------------------------------------->|
  |                                    (in-memory only)     |
  |                                                        |
  | gateway.update()                                       |
  |------------------------------------------------------->|
  |                            UPDATE ... SET ... WHERE id = ?
  |                                                        |
  |                                          rows affected |
  |<-------------------------------------------------------|
  |                                                        |
  | (caller decides when the surrounding transaction commits)
```

A second dynamic, insert followed by delete inside the same unit of work, is
common in tests and in short-lived batch jobs.

```
Caller                          PersonGateway               Database
  |                                    |                        |
  | gateway = PersonGateway.blank(     |                        |
  |     conn, "Ada", "Lovelace", 0)    |                        |
  |------------------------------------>                        |
  |                                    |  (no row yet, id null)  |
  |                                                              |
  | gateway.insert()                                             |
  |------------------------------------------------------------->|
  |                                    INSERT INTO people ...     |
  |                                                              |
  |                                          generated id: 47    |
  |<-------------------------------------------------------------|
  | gateway.id == 47                                             |
  |                                                              |
  | gateway.delete()                                             |
  |------------------------------------------------------------->|
  |                                    DELETE FROM people WHERE id = 47
  |                                                              |
  | gateway.id == null                                           |
```

## 8. Implementation variants

- **Hand-written, one class per table.** The classic form. A developer writes
  the field list, the `find`, and the CRUD methods once and maintains them by
  hand as the schema evolves. Cheapest to understand, most expensive to keep
  in sync with a fast-moving schema.
- **Generated from schema metadata.** A build step reads the database catalog
  or a schema description file and emits one gateway class per table. This is
  exactly the shape of Visual Studio's classic typed `DataSet` designer, which
  reads a database schema through the `.xsd` file in the Dataset Designer and
  compiles "a new, strongly typed dataset class, with information from the
  schema, tables, columns, and so on, generated and compiled into the new
  dataset class as a set of first-class objects and properties," producing one
  row class per table, for example `CustomersRow`, with one property per
  column
  ([Generating Strongly Typed DataSets, Microsoft Learn](https://learn.microsoft.com/en-us/dotnet/framework/data/adonet/dataset-datatable-dataview/generating-strongly-typed-datasets),
  verified 2026-08-02). This variant trades hand-maintenance for a
  regeneration step that must run whenever the schema changes, and it is
  common for the update and delete methods to live on a companion
  `TableAdapter` rather than on the row class itself, which is a mild
  departure from Fowler's description of the pattern, where persistence
  methods live on the row.
- **Dynamic or reflective field storage.** Instead of one typed field per
  column declared in code, the gateway stores column values in a dictionary,
  hash map, or an object built from the language's dynamic-typing features,
  and exposes them through a generic getter and setter, or through language
  features like C#'s dynamic type or Ruby's `method_missing`. This removes the
  code-generation step entirely at the cost of losing compile-time type
  checking on field names, and it is the shape typically associated with
  micro-ORMs built on dynamic language features rather than with statically
  generated row classes.
- **Split gateway and update.** Some frameworks separate the read path,
  populate a gateway from a `SELECT`, from the write path, persist a gateway
  through a companion object's `save`. Laminas's `RowGateway` documents this
  explicitly, it is "generally used in conjunction with objects that produce
  `Laminas\Db\ResultSets`," where a `TableGateway` select produces a result set
  "capable of producing valid Row Gateway objects," and the row object itself
  still exposes `save()` and `delete()`
  ([Row Gateways, laminas-db documentation](https://docs.laminas.dev/laminas-db/row-gateway/),
  verified 2026-08-02). This keeps the pattern intact while pairing it, by
  design, with Table Data Gateway for the read side.
- **Domain-logic-free wrapper over an Active Record.** Some frameworks nudge a
  team toward adding methods to what starts as a Row Data Gateway, and the
  team must actively resist that pull or accept that the class has quietly
  become an Active Record. Fowler's own text draws the line at exactly this
  point, "the crux of the matter is whether there's any domain logic present,"
  and treats it as a decision the team must make on purpose rather than one
  that should happen by accretion
  ([Row Data Gateway, martinfowler.com/eaaCatalog](https://martinfowler.com/eaaCatalog/rowDataGateway.html),
  verified 2026-08-02).

## 9. Known production uses

- **Zend Framework's `Zend_Db_Table_Row`.** Zend Framework 1's database
  component documents `Zend_Db_Table_Row` as an implementation of the Row Data
  Gateway pattern, populated from the `fetchRow()` method on the companion
  table class, with a resulting row object usable through ordinary property
  access
  ([Zend_Db_Table_Row, Zend Framework 1.12 manual](https://framework.zend.com/manual/1.12/en/zend.db.table.row.html),
  verified 2026-08-02).
- **Laminas's `Laminas\Db\RowGateway`, successor to Zend Framework 2's
  `Zend\Db\RowGateway`.** After Zend Framework 2 shipped `Zend\Db\RowGateway`
  as a documented Row Data Gateway implementation, the project moved under the
  Linux Foundation and was renamed Laminas in 2019. The current
  `laminas-db` package still ships the same component and states plainly that
  it "implements the Row Data Gateway pattern described in the book Patterns
  of Enterprise Application Architecture," with `save()` and `delete()`
  methods that persist or remove the row
  ([Row Gateways, laminas-db documentation](https://docs.laminas.dev/laminas-db/row-gateway/),
  verified 2026-08-02).
- **ADO.NET typed `DataSet` row classes, generated by the Visual Studio
  Dataset Designer.** Microsoft's own documentation on typed `DataSet`
  generation describes the generator producing one strongly typed row class
  per table, giving the example that "typed DataSets use a strongly typed
  `CustomersRow` object to access data from the Customers table," in place of
  untyped column-by-name access
  ([Generating Strongly Typed DataSets, Microsoft Learn](https://learn.microsoft.com/en-us/dotnet/framework/data/adonet/dataset-datatable-dataview/generating-strongly-typed-datasets),
  verified 2026-08-02). This was the standard way to talk to a database from a
  Windows Forms or early ASP.NET application built with Visual Studio's
  designer tooling from the early 2000s through the mid 2010s, and it is a
  close but not exact match to Fowler's description, since the generated
  `TableAdapter` companion class, not the row class, typically owns the
  `Update` call that writes changes back to the database, splitting the
  gateway's persistence responsibility across two generated classes rather
  than keeping it on the row.

## 10. Consequences

Positive.

- Every caller that needs a person's row gets the same field names and the
  same type conversions, because there is exactly one class responsible for
  that mapping instead of SQL copied at each call site.
- The class is close to mechanical to generate from a schema, which makes it
  cheap to produce and to regenerate as the schema evolves, when a generator
  is used.
- A caller's tests can substitute an in-memory Test Double for the gateway
  without needing a real database connection, because the gateway's public
  surface is small, a handful of typed fields plus four persistence methods.
- SQL knowledge, column names, parameter order, type coercion, is confined to
  one place per table rather than scattered through the codebase.

Negative.

- Fetching a collection of rows one at a time through repeated `find` calls
  produces one query per row, an N+1 pattern that degrades quickly as the
  collection grows, unless the team pairs the gateway with a Table Data
  Gateway or a batch finder that issues one query for many rows.
- The class carries no domain behavior by design, so any validation,
  calculation, or workflow logic that would naturally sit "on the person"
  instead lives in the caller, and that logic tends to duplicate itself across
  every caller that needs it, unless the team introduces a separate domain
  layer on top.
- Two separate `find` calls for the same row return two separate objects with
  independent field state by default, so two callers that both load and both
  modify the same row can silently overwrite each other's changes with no
  built-in detection, unless the team adds optimistic concurrency, typically a
  version column checked in the `update` statement's `WHERE` clause, or an
  Identity Map.
- Generated variants introduce a build-time dependency on the generator and a
  churn cost, every schema migration requires a regeneration step, and a
  missed regeneration silently leaves the gateway out of sync with the real
  table shape until a runtime error surfaces it.
- The pattern does nothing for a schema that does not map cleanly onto a
  single in-memory shape, a join across several tables, a table split across
  two domain concepts, or a normalized structure that ought to present as one
  denormalized object to the caller.

## 11. Failure modes and misuse

This dimension is drawn from documented patterns of use in the ecosystem
combined with engineering judgement about how the failure would present, it is
not a claim about any single named incident.

- **Symptom.** A list page or a report takes noticeably longer as the data
  grows, with a query count that scales linearly with the number of rows
  shown, visible in a query log or an APM trace as dozens or hundreds of
  near-identical single-row `SELECT` statements fired in a tight loop.
  **Cause.** A caller loops over a set of primary keys and calls the
  gateway's `find` inside the loop, one query per row, instead of using a
  batch finder or a Table Data Gateway that returns the whole set from one
  query. **Fix.** Add a finder method, on the gateway class itself or on a
  companion Table Data Gateway, that accepts a list of keys or a filter and
  returns a collection of populated gateway instances from a single query
  with an `IN` clause or a join, then populate each gateway instance from one
  row of that single result set instead of issuing a query per instance.
- **Symptom.** Two users editing what looks like the same record in the UI
  both see their changes saved successfully, but one user's edit disappears
  a moment later with no error shown to either user. **Cause.** Two separate
  `find` calls loaded two separate in-memory instances of the same row, both
  callers modified different fields on their own instance, and both called
  `update`, with the second `update` overwriting every column, including the
  columns the first caller changed, because a naive `update` writes the
  gateway's full field set rather than only the fields that changed.
  **Fix.** Either add optimistic concurrency, a version or timestamp column
  compared in the `update` statement's `WHERE` clause and incremented on
  every successful write, with the caller checking the affected row count to
  detect a conflict, or restrict `update` to write only the fields the caller
  explicitly marked as changed rather than the entire row.
- **Symptom.** A code review or an architecture discussion cannot agree on
  whether a given class "is allowed" to contain a particular piece of logic,
  because half the team treats the class as a pure gateway and half treats it
  as the natural home for a calculation that touches the same fields.
  **Cause.** A method that started as a small convenience, for example a
  `getFullName()` that concatenates two fields, quietly became the first of
  many small pieces of domain logic added to what was meant to stay a pure
  gateway, and the class has drifted into being an undeclared Active Record
  without the team choosing that on purpose. **Fix.** Make the choice
  explicit. Either accept the class is now an Active Record and document that
  decision, or extract every piece of domain logic into a separate object
  that wraps or is constructed from the gateway, restoring the gateway to
  data access only, matching Fowler's own dividing line between the two
  patterns
  ([Row Data Gateway, martinfowler.com/eaaCatalog](https://martinfowler.com/eaaCatalog/rowDataGateway.html),
  verified 2026-08-02).
- **Symptom.** A row inserted through the gateway shows the wrong value for a
  column the database itself computes, for example a default timestamp or a
  computed column, until the object is reloaded from the database.
  **Cause.** The gateway's `insert` method populated its own `id` field from
  a generated key but left every other database-computed column at whatever
  value the in-memory object held before the insert, because the gateway
  only reads back what it explicitly asked for. **Fix.** After an `insert`
  or `update` that touches a column the database can compute or default,
  re-`find` the row, or have the insert statement return the computed
  columns directly, rather than trusting the in-memory object's
  pre-insert values for those fields.
- **Symptom.** A regenerated gateway class breaks a caller at compile time,
  or worse, silently drops a field at runtime, right after a routine schema
  migration that the team believed was backward compatible. **Cause.** The
  generation step was not run as part of the migration, or was run against
  a stale schema snapshot, so the gateway class in source control no longer
  matches the live table, and either the mismatch is invisible until a
  missing column throws at runtime, or a renamed column silently keeps the
  old, wrong name in the generated class. **Fix.** Wire schema-change
  detection into the same pipeline that runs migrations, so the generation
  step is not an optional manual command a developer might forget, and add
  a smoke test that instantiates every generated gateway against the real
  schema before a deploy is allowed to proceed.

## 12. Trade-off matrix

| Force | Row Data Gateway | Table Data Gateway | Active Record | Data Mapper |
|---|---|---|---|---|
| Domain logic on the class | None by design | None, and no per-row identity at all | Present, mixed with persistence | None, kept entirely in the domain object |
| Query cost for a single row | One query, one instance | One query returning a result set, then wrapped per row | One query, one instance | One query plus mapper overhead |
| Query cost for a collection | N+1 unless paired with a batch finder | One query for the whole collection | N+1 unless a finder returns a set | One query for the whole collection, mapper builds the graph |
| Coupling of domain to schema | Domain stays separate if the team disciplines itself | Domain stays separate, gateway is purely SQL | Domain and schema are the same class | Domain and schema are decoupled by design |
| Fit for a rich object graph | Poor, one class per table only | Poor, same limitation | Poor past simple associations | Strong, this is the pattern's reason to exist |
| Generation friendliness | High, near-mechanical from schema metadata | High, similar to Row Data Gateway | Moderate, generation plus hand-added behavior | Low, mapping logic is usually hand-written |
| Testability without a database | High, small surface to fake | High, similar surface | Moderate, business logic pulls in persistence concerns | High, domain object has no persistence dependency to fake |
| Where it earns its cost | Transaction Script codebases needing typed row access | Reporting, batch, and set-oriented access | Small to medium apps where domain and schema align closely | Complex domain models where schema and object shape diverge |

## 13. Related and incompatible patterns

- **Table Data Gateway.** The natural pairing partner rather than a
  competitor. A Table Data Gateway issues the `SELECT` for a whole result set
  in one query and hands each row to a Row Data Gateway constructor, closing
  Row Data Gateway's own N+1 weakness while keeping the row class free of
  batch query logic. Laminas documents exactly this pairing between its
  `TableGateway` and `RowGateway` components
  ([Row Gateways, laminas-db documentation](https://docs.laminas.dev/laminas-db/row-gateway/),
  verified 2026-08-02).
- **Active Record.** The closest sibling pattern and the one Row Data Gateway
  is most often mistaken for or drifts into. The shapes are nearly identical,
  one instance per row, `find`, `insert`, `update`, `delete` as instance or
  class methods, but the presence of domain logic on the class is the entire
  difference. Fowler's own text makes this the dividing test rather than any
  structural difference
  ([Row Data Gateway, martinfowler.com/eaaCatalog](https://martinfowler.com/eaaCatalog/rowDataGateway.html),
  verified 2026-08-02).
- **Data Mapper.** The pattern to reach for instead of Row Data Gateway once
  the domain model needs associations, inheritance, or a shape that diverges
  from the table structure. Where Row Data Gateway mirrors the table inside
  the object, Data Mapper keeps the domain object ignorant of the schema
  entirely and puts all translation in a separate mapper layer.
- **Identity Map.** Not part of the base pattern, but commonly layered in
  front of a Row Data Gateway's `find` method so that two lookups for the same
  primary key return the same in-memory instance rather than two independent
  ones, closing the lost-update failure mode described in dimension 11.
- **Gateway.** The general pattern Row Data Gateway specializes. Any object
  wrapping access to an external resource, a web service, a message queue, a
  legacy system, follows the same shape at a coarser grain, Row Data Gateway
  is the version of it scoped to exactly one database row.
- **Record Set.** A structurally adjacent but distinct idea from the same
  chapter of Fowler's book, an in-memory table-shaped object holding many rows
  at once with generic column access rather than typed fields. A collection of
  Row Data Gateway instances and a Record Set solve a similar surface problem,
  returning tabular data to a caller, from different directions, typed
  per-row objects against one generic table-shaped container.
- **Incompatible with a rich Domain Model at the point of associations.** Row
  Data Gateway has nothing to say about how one row relates to another, and
  bolting association-following logic directly onto a Row Data Gateway class
  produces the coupling Data Mapper exists to avoid, so the two are not
  incompatible in the sense of causing an error, but combining them past a
  trivial foreign key lookup undermines the reason to choose either one.

## 14. Refactoring path in and out

Introducing Row Data Gateway into a codebase that currently scatters raw SQL
across call sites proceeds in small, reversible steps.

1. Pick one table whose access is duplicated across the most call sites, and
   write down every distinct `SELECT`, `INSERT`, `UPDATE`, and `DELETE`
   currently issued against it, including subtle differences in which columns
   each call site touches.
2. Create the gateway class with one field per column, typed to the closest
   native equivalent, and a private or otherwise restricted constructor that
   only the class's own factory methods can call, following the shape
   described in dimension 5.
3. Write the `find` factory method first, backed by the most complete of the
   `SELECT` statements gathered in step one, and redirect the first call site
   to use it instead of its own SQL, deleting that call site's inline SQL.
4. Repeat step three for every remaining `SELECT` call site against the same
   table, consolidating any that differ only in which columns they read into
   the single `find` method, and consolidating any that filter differently
   into additional named finder methods rather than parameterizing `find`
   itself into something that tries to do everything.
5. Add `insert`, `update`, and `delete` in the same way, one call site at a
   time, verifying after each migration that the behavior, including any
   edge case the old code handled, such as a null field or a missing row,
   still holds.
6. Once every call site against the table goes through the gateway, delete
   the now-dead direct-SQL code paths, and consider whether the same
   extraction is worth repeating for the next most duplicated table.

This is a direct application of Extract Class from Martin Fowler, *Refactoring.
Improving the Design of Existing Code*, 2nd edition, Addison-Wesley, 2018,
combined with Introduce Foreign Method style extraction for the SQL itself,
performed table by table rather than all at once.

Removing Row Data Gateway happens along two different paths depending on why
the team is removing it.

- **Because domain logic accumulated on the class.** If the team decides to
  formally accept the class as an Active Record rather than keep fighting the
  drift, no structural change is needed, only a decision, documented, that the
  class now carries domain logic on purpose. If instead the team wants to keep
  the separation, extract every piece of domain logic into a new domain class
  that is constructed from, or wraps, the gateway, leaving the gateway itself
  untouched and purely a data accessor again.
- **Because the domain model outgrew per-table objects.** If the application
  needs associations, inheritance, or a shape that no longer matches the
  table, introduce a Data Mapper layer, build the domain classes the mapper
  will populate first, keep the old gateway classes running underneath as an
  implementation detail of the new mapper's SQL, then delete the gateway
  classes once every caller has been migrated to the domain model and nothing
  references the gateway classes directly anymore.

## 15. Testing and verification

A Row Data Gateway's narrow surface, a handful of typed fields plus `find`,
`insert`, `update`, `delete`, is easy to fake, which is one of the pattern's
real advantages for testing anything that calls it. A test double implementing
the same public shape, backed by an in-memory dictionary keyed by primary key
instead of a real connection, lets a caller's business logic be tested with no
database at all, and this is the class of test the pattern was chosen to
enable in the first place, per Fowler's own stated motivation about testing
speed
([Row Data Gateway, martinfowler.com/eaaCatalog](https://martinfowler.com/eaaCatalog/rowDataGateway.html),
verified 2026-08-02).

What became harder to test as a direct result of choosing this pattern is
anything that spans more than one row or more than one table, because the
gateway itself offers no seam for testing a multi-row invariant, that
invariant lives entirely in the caller, and the caller's test has to fake
enough of the gateway's behavior across several instances to exercise it,
which is more setup than testing a single value object would need.

For the gateway class itself, rather than for its callers, the useful tests
are the ones a plain unit test cannot substitute for.

- An integration test against a real or a lightweight embedded database
  (SQLite in the Python and TypeScript ecosystems is a common cheap choice for
  this) that exercises the full round trip, `insert` then `find` returns the
  same values, `update` changes exactly the intended fields and nothing else,
  `delete` removes the row and a subsequent `find` fails as documented.
- A test that inserts a row, updates it, and asserts the row count and column
  values directly against the database rather than only against the
  in-memory object, to catch a mismatch between what the object believes it
  wrote and what actually landed in the table, which a purely in-memory test
  double could never surface.
- A concurrency test, when optimistic concurrency has been added per
  dimension 11, that simulates two gateway instances loading the same row,
  changing different fields, and asserts the second `update` either fails
  cleanly or the affected row count comes back as zero, rather than silently
  overwriting the first change.
- For generated variants, a smoke test run against the real schema after
  every regeneration, asserting the generated class's fields still match the
  table's actual columns, closing the failure mode described in dimension 11
  where a stale generation step silently drifts from the schema.

## 16. Observability signals

This dimension is engineering judgement about what to watch, drawn from the
pattern's known failure modes in dimension 11, not a sourced claim about any
specific tool.

A healthy Row Data Gateway layer, watched from the outside, produces a query
log dominated by single-row lookups by primary key, each with a low and
consistent latency, and a query count per request that stays roughly flat
regardless of how many rows a page happens to render, because collection
access goes through a batch finder rather than a loop of individual `find`
calls.

The signals worth tracking, and what a failing instance looks like against
each one.

- **Query count per request or per batch job run.** A healthy value tracks
  the number of distinct entities the request actually needs, roughly
  constant. A climbing value that scales with the size of a list being
  rendered is the N+1 signature from dimension 11's first failure mode, and is
  usually visible directly in an APM tool's query waterfall as a long, flat
  run of near-identical statements.
- **Affected row count on `update` and `delete`.** A healthy `update` reports
  exactly one row affected. A zero here on a call the caller expected to
  succeed means the row was deleted or already changed underneath the
  gateway, most often surfacing as the lost-update pattern from dimension 11's
  second failure mode when combined with optimistic concurrency, an `update`
  that ignores this return value and never checks it is a signal the team has
  not wired concurrency detection into the observability path at all.
- **Time between a schema migration landing and the next successful
  regeneration or deploy, for generated variants.** A healthy pipeline runs
  the generator as part of the same deploy that runs the migration. A gap here
  is the direct precursor to the schema-drift failure mode in dimension 11,
  and is best caught by a build-time or deploy-time check rather than by a
  production symptom.
- **Ratio of gateway instantiations to distinct primary keys requested within
  a short window.** A ratio near one is healthy. A ratio well above one,
  meaning the same row was loaded and instantiated many times in a short
  span, points either at a missing Identity Map or at a hot loop somewhere
  calling `find` more often than necessary, both worth investigating even
  when no lost-update bug has surfaced yet.

## 17. Security and privacy implications

Row Data Gateway itself is a thin persistence wrapper and does not introduce a
distinctive class of vulnerability the way, for instance, a pattern that
builds and executes dynamic SQL from user input would, but its position at the
exact boundary between application code and the database makes a few concerns
worth naming rather than leaving silent.

- **SQL injection risk moves entirely into the gateway's own implementation.**
  Because every caller in the application now goes through the gateway rather
  than writing its own SQL, the gateway's `find`, `insert`, `update`, and
  `delete` methods are the single place that must use parameterized queries or
  prepared statements rather than string-concatenated SQL. Getting this right
  once, inside the gateway, protects every caller, getting it wrong once has
  the same blast radius as every caller having gotten it wrong individually,
  which is a case where the pattern's coupling-reduction property is also its
  security property.
- **Over-fetching columns by default.** A gateway generated or hand-written to
  select every column on every `find`, including columns holding sensitive
  data a given caller does not need, for example a password hash or a
  government identifier alongside a customer's name and address, brings that
  sensitive data into memory, into logs if the object is logged carelessly,
  and into serialized responses if the object is passed straight through to
  an API layer, for callers who only needed the non-sensitive fields.
  Column-scoped finder variants, selecting only the columns a specific caller
  needs rather than always selecting the full row, reduce this exposure at
  the cost of a slightly larger set of finder methods.
- **The gateway has no built-in authorization boundary.** Nothing in the
  pattern checks whether the calling code, or the user on whose behalf it is
  running, is allowed to read or write the specific row being requested. Row
  or column level authorization has to be enforced by the caller, or by a
  layer wrapping the gateway, and a codebase that forgets this and treats the
  gateway's mere existence as sufficient access control has silently removed a
  check that a raw, per-call-site SQL approach would have forced someone to
  think about explicitly at least once per query.
- **Logging a gateway instance for debugging can leak more than intended.** A
  generic `toString`, `__repr__`, or default JSON serialization of a gateway
  object dumps every field, including any sensitive column the row happens to
  hold, into whatever log sink or error report captures that output. This is
  not specific to Row Data Gateway, but the pattern's convenience, an object
  that looks and behaves like any other in-language object, makes it easy to
  forget the object is a direct mirror of a database row and not an ordinary
  value type safe to print without thought.

This entry does not identify a concern in the pattern's data-at-rest handling
beyond what is stated above, and states that plainly rather than inventing
one.

## 18. References

1. Martin Fowler, *Patterns of Enterprise Application Architecture*,
   Addison-Wesley, 2002, chapter 10, "Data Source Architectural Patterns,"
   Row Data Gateway.
2. Martin Fowler, "Row Data Gateway,"
   [martinfowler.com/eaaCatalog/rowDataGateway.html](https://martinfowler.com/eaaCatalog/rowDataGateway.html),
   verified 2026-08-02.
3. Martin Fowler, *Patterns of Enterprise Application Architecture*,
   Addison-Wesley, 2002, chapter 18, "Base Patterns," Gateway.
4. Zend Framework Team, "Zend_Db_Table_Row,"
   [framework.zend.com/manual/1.12/en/zend.db.table.row.html](https://framework.zend.com/manual/1.12/en/zend.db.table.row.html),
   verified 2026-08-02.
5. Laminas Project, "Row Gateways, laminas-db,"
   [docs.laminas.dev/laminas-db/row-gateway](https://docs.laminas.dev/laminas-db/row-gateway/),
   verified 2026-08-02.
6. Microsoft, "Generating Strongly Typed DataSets,"
   [learn.microsoft.com/en-us/dotnet/framework/data/adonet/dataset-datatable-dataview/generating-strongly-typed-datasets](https://learn.microsoft.com/en-us/dotnet/framework/data/adonet/dataset-datatable-dataview/generating-strongly-typed-datasets),
   verified 2026-08-02.
7. Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
   edition, Addison-Wesley, 2018, Extract Class.

## Code examples

Three languages, chosen because each shows a distinct real-world binding
surface for the same pattern. Python's standard library `sqlite3` module lets
the example run end to end with no external service, so the demonstration
below is executed, not only compiled. Java shows the pattern against the
`java.sql` API most real JDBC-backed gateways are built on. TypeScript shows
the pattern against a generic, driver-shaped interface typical of a
Postgres-style Node.js client, checked in strict mode.

A Go or Rust version was considered and left out on purpose. Idiomatic Go
database code tends to favor a `sql.Row` and `Scan` pairing consumed directly
by the caller rather than wrapped in a stateful per-row object with mutation
methods, and idiomatic Rust favors an immutable struct returned from a query
plus a separate function for the write, both of which fight the mutable,
stateful, method-carrying shape this pattern specifically calls for, so
forcing either language into the shape would produce code that reads as
foreign to that language's own conventions rather than as a genuine example
of the pattern.

```python
from __future__ import annotations
import sqlite3
from typing import Optional


class PersonGateway:
    """One instance per row in the people table. No domain logic here."""

    def __init__(self, conn: sqlite3.Connection, row_id: Optional[int],
                 first_name: str, last_name: str,
                 number_of_dependents: int) -> None:
        self._conn = conn
        self.id = row_id
        self.first_name = first_name
        self.last_name = last_name
        self.number_of_dependents = number_of_dependents

    @classmethod
    def find(cls, conn: sqlite3.Connection, row_id: int) -> "PersonGateway":
        cur = conn.execute(
            "SELECT first_name, last_name, number_of_dependents "
            "FROM people WHERE id = ?",
            (row_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise LookupError(f"no person with id {row_id}")
        first_name, last_name, dependents = row
        return cls(conn, row_id, first_name, last_name, dependents)

    def insert(self) -> int:
        cur = self._conn.execute(
            "INSERT INTO people (first_name, last_name, "
            "number_of_dependents) VALUES (?, ?, ?)",
            (self.first_name, self.last_name, self.number_of_dependents),
        )
        self.id = cur.lastrowid
        return self.id

    def update(self) -> None:
        if self.id is None:
            raise ValueError("cannot update a row that was never inserted")
        self._conn.execute(
            "UPDATE people SET first_name = ?, last_name = ?, "
            "number_of_dependents = ? WHERE id = ?",
            (self.first_name, self.last_name,
             self.number_of_dependents, self.id),
        )

    def delete(self) -> None:
        if self.id is None:
            return
        self._conn.execute("DELETE FROM people WHERE id = ?", (self.id,))
        self.id = None


def _demo() -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE people (id INTEGER PRIMARY KEY, first_name TEXT, "
        "last_name TEXT, number_of_dependents INTEGER)"
    )
    p = PersonGateway(conn, None, "Martin", "Fowler", 0)
    p.insert()
    same_row = PersonGateway.find(conn, p.id)
    same_row.number_of_dependents = 2
    same_row.update()
    reloaded = PersonGateway.find(conn, p.id)
    assert reloaded.number_of_dependents == 2
    reloaded.delete()
    conn.commit()
    print("row data gateway demo ok")


if __name__ == "__main__":
    _demo()
```

The Python sample above was executed with `python3` against an in-memory
SQLite database and printed `row data gateway demo ok`, confirming the insert,
find, update, and delete round trip behaves as described.

```java
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

public final class PersonGateway {
    private final Connection connection;
    private Long id;
    private String firstName;
    private String lastName;
    private int numberOfDependents;

    private PersonGateway(Connection connection) {
        this.connection = connection;
    }

    public static PersonGateway find(Connection connection, long id)
            throws SQLException {
        String sql = "SELECT first_name, last_name, number_of_dependents "
                + "FROM people WHERE id = ?";
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setLong(1, id);
            try (ResultSet rs = stmt.executeQuery()) {
                if (!rs.next()) {
                    throw new IllegalStateException("no person with id " + id);
                }
                PersonGateway gateway = new PersonGateway(connection);
                gateway.id = id;
                gateway.firstName = rs.getString("first_name");
                gateway.lastName = rs.getString("last_name");
                gateway.numberOfDependents = rs.getInt("number_of_dependents");
                return gateway;
            }
        }
    }

    public static PersonGateway blank(Connection connection, String firstName,
            String lastName, int dependents) {
        PersonGateway gateway = new PersonGateway(connection);
        gateway.firstName = firstName;
        gateway.lastName = lastName;
        gateway.numberOfDependents = dependents;
        return gateway;
    }

    public long insert() throws SQLException {
        String sql = "INSERT INTO people (first_name, last_name, "
                + "number_of_dependents) VALUES (?, ?, ?)";
        try (PreparedStatement stmt = connection.prepareStatement(
                sql, Statement.RETURN_GENERATED_KEYS)) {
            stmt.setString(1, firstName);
            stmt.setString(2, lastName);
            stmt.setInt(3, numberOfDependents);
            stmt.executeUpdate();
            try (ResultSet keys = stmt.getGeneratedKeys()) {
                keys.next();
                id = keys.getLong(1);
                return id;
            }
        }
    }

    public void update() throws SQLException {
        if (id == null) {
            throw new IllegalStateException(
                    "cannot update a row that was never inserted");
        }
        String sql = "UPDATE people SET first_name = ?, last_name = ?, "
                + "number_of_dependents = ? WHERE id = ?";
        try (PreparedStatement stmt = connection.prepareStatement(sql)) {
            stmt.setString(1, firstName);
            stmt.setString(2, lastName);
            stmt.setInt(3, numberOfDependents);
            stmt.setLong(4, id);
            stmt.executeUpdate();
        }
    }

    public void delete() throws SQLException {
        if (id == null) {
            return;
        }
        try (PreparedStatement stmt = connection.prepareStatement(
                "DELETE FROM people WHERE id = ?")) {
            stmt.setLong(1, id);
            stmt.executeUpdate();
            id = null;
        }
    }

    public long getId() { return id; }
    public String getFirstName() { return firstName; }
    public void setFirstName(String firstName) { this.firstName = firstName; }
    public String getLastName() { return lastName; }
    public void setLastName(String lastName) { this.lastName = lastName; }
    public int getNumberOfDependents() { return numberOfDependents; }
    public void setNumberOfDependents(int numberOfDependents) {
        this.numberOfDependents = numberOfDependents;
    }
}
```

The Java sample compiled cleanly with `javac` against the standard `java.sql`
API. It was not executed end to end, since exercising it needs a real JDBC
driver and a live or embedded database on the classpath, neither of which is
part of this compile-only verification.

```typescript
interface QueryResult<T> {
  rows: T[];
}

interface DbClient {
  query<T>(sql: string, params: unknown[]): Promise<QueryResult<T>>;
}

interface PersonRow {
  id: number;
  first_name: string;
  last_name: string;
  number_of_dependents: number;
}

class PersonGateway {
  id: number | null;
  firstName: string;
  lastName: string;
  numberOfDependents: number;

  private constructor(
    private readonly db: DbClient,
    row: PersonRow | null,
  ) {
    this.id = row?.id ?? null;
    this.firstName = row?.first_name ?? "";
    this.lastName = row?.last_name ?? "";
    this.numberOfDependents = row?.number_of_dependents ?? 0;
  }

  static async find(db: DbClient, id: number): Promise<PersonGateway> {
    const result = await db.query<PersonRow>(
      "SELECT id, first_name, last_name, number_of_dependents "
        + "FROM people WHERE id = $1",
      [id],
    );
    const row = result.rows[0];
    if (!row) {
      throw new Error(`no person with id ${id}`);
    }
    return new PersonGateway(db, row);
  }

  static blank(db: DbClient): PersonGateway {
    return new PersonGateway(db, null);
  }

  async insert(): Promise<number> {
    const result = await this.db.query<{ id: number }>(
      "INSERT INTO people (first_name, last_name, number_of_dependents) "
        + "VALUES ($1, $2, $3) RETURNING id",
      [this.firstName, this.lastName, this.numberOfDependents],
    );
    this.id = result.rows[0].id;
    return this.id;
  }

  async update(): Promise<void> {
    if (this.id === null) {
      throw new Error("cannot update a row that was never inserted");
    }
    await this.db.query(
      "UPDATE people SET first_name = $1, last_name = $2, "
        + "number_of_dependents = $3 WHERE id = $4",
      [this.firstName, this.lastName, this.numberOfDependents, this.id],
    );
  }

  async delete(): Promise<void> {
    if (this.id === null) return;
    await this.db.query("DELETE FROM people WHERE id = $1", [this.id]);
    this.id = null;
  }
}
```

The TypeScript sample was type-checked with `tsc --noEmit --strict` and
produced no errors. It was not executed, since running it needs a real
`DbClient` implementation backed by a database driver, which is outside the
scope of a static type-check.
