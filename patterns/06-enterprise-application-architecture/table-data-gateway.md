---
name: Table Data Gateway
slug: table-data-gateway
family: 06-enterprise-application-architecture
category: Data Source Architectural
aliases: [Table Gateway]
first_described: "Fowler 2002"
maturity: canonical
related: [row-data-gateway, active-record, data-mapper, repository, unit-of-work]
incompatible_with: [row-data-gateway]
verified: 2026-08-11
---

# Table Data Gateway

## 1. Name, aliases, and lineage

The canonical name is Table Data Gateway. Martin Fowler catalogued it in
*Patterns of Enterprise Application Architecture*, Addison-Wesley, 2002, in the
Data Source Architectural Patterns chapter, and states the intent as "an object
that acts as a gateway to a database table. One instance handles all the rows
in the table" (Martin Fowler, "Table Data Gateway",
https://martinfowler.com/eaaCatalog/tableDataGateway.html, verified
2026-08-11). The shortened form Table Gateway is common in framework
documentation and in later writing, including Fowler's own later references to
the pattern, and the two names refer to the identical structure.

The pattern sits in a family Fowler groups under Data Source Architectural
Patterns, three patterns that answer the same question, how does application
code talk to a database, with a different unit of granularity each time.

- **Table Data Gateway.** One object per table. It knows every column and every
  SQL statement for that table, and it hands back or accepts generic records,
  typically an in-memory row structure such as a `RecordSet`, a `DataTable`, or
  a plain map, not a domain object.
- **Row Data Gateway (Fowler 2002).** One object per row. It wraps a single
  record and exposes get and set accessors for its columns, with no domain
  behaviour attached (Martin Fowler, "Row Data Gateway",
  https://martinfowler.com/eaaCatalog/rowDataGateway.html, verified
  2026-08-11). See the dedicated entry for the full contrast.
- **Data Mapper (Fowler 2002).** A layer that moves data between objects and a
  database while keeping them independent of each other and of the mapper
  itself. Data Mapper is not covered further here except where it clarifies
  a boundary, it has its own entry.

Table Data Gateway is easy to mistake for Active Record because both wrap a
table, and it is easy to mistake for Repository because both centralise
queries. Section 13 draws each line precisely. The short version, stated once
here because it recurs through every dimension below, is this. Table Data
Gateway returns raw data and carries no domain logic. Active Record returns
objects that carry both data and behaviour and know how to persist themselves.
Repository returns domain objects reconstituted by a mapper and hides the
existence of a table entirely, including cases where several tables back one
aggregate.

## 2. Problem and context

An application needs to read and write rows in a table, and the two paths that
seem obvious both go wrong at scale.

The first obvious path is inlining SQL at every call site. A `SELECT` for the
list screen, an `INSERT` in the signup handler, an `UPDATE` in three different
places that each touch the `users` table slightly differently. This works for
a screen or two. Past that point the same table's schema is guessed at from
memory in a dozen files, a column rename becomes a grep-and-pray exercise, and
a developer who is confident in the domain language but shaky on SQL now has
to write and debug SQL to ship a feature. Fowler frames this directly, the
scattered SQL is hard for a domain expert to read, hard for a DBA to review or
tune in one place, and hard to keep consistent when the schema shifts (Fowler,
*Patterns of Enterprise Application Architecture*, "Table Data Gateway", 2002).

The second obvious path is reaching straight for a full object-relational
mapper or a rich domain model before either is needed. That is a real cost, a
mapping layer, a change-tracking mechanism, a learning curve for the team,
paid up front for a system that is, at this point, five screens over one
schema with almost no business rules attached to the data. The mismatch is not
that ORMs are wrong, it is that the investment does not match the problem yet.

The context in which Table Data Gateway is the right answer has a specific
shape. The application is organised around Transaction Script or a thin
service layer rather than a rich domain model, the data itself has little or
no behaviour beyond validation, the team is more comfortable calling named
methods than composing SQL, and the persistence technology is a relational
database reached through a driver that speaks in generic result sets, an
ADO.NET `DataTable`, a PHP array of rows, a JDBC `ResultSet`, rather than typed
domain objects. It is also the shape a legacy codebase takes on the way toward
something richer, because it is the smallest step that gets SQL out of
scattered call sites without committing to a domain model the team has not yet
designed.

## 3. Forces

The forces below are engineering judgement, weighing what the pattern trades,
not a sourced claim about a specific implementation.

- **Encapsulation of SQL versus flexibility of ad hoc queries.** A gateway
  method for every access pattern the application needs is a finite,
  auditable surface. An application that later needs a query shape the
  gateway never anticipated either grows the gateway's method count without
  bound or falls back to exposing a raw query escape hatch, which erodes the
  encapsulation the pattern exists to provide.
- **Simplicity versus richness of domain behaviour.** A gateway returns data,
  not objects with behaviour. That keeps the class simple and the mental model
  small, and it means any business rule that touches this data lives
  somewhere else, in a service layer or a Transaction Script, which is a
  deliberate choice, not an oversight, but it is a real absence some readers
  expect a "model" class to fill.
- **Table-per-class versus query-per-need.** One gateway per table maps
  cleanly onto a relational schema and is trivial to explain to a newcomer.
  It maps poorly onto a query that spans several tables in a way that does
  not correspond to any single table's shape, a report, a join-heavy search.
  Those queries either live awkwardly inside one gateway, duplicate logic
  across two gateways, or need a separate query object entirely.
- **Testability versus realism.** Table Data Gateway isolates SQL behind an
  interface that can, in principle, be faked. In practice the interface
  usually still returns a generic row structure shaped by the database, so a
  fake gateway has to fake that shape too, which is less clean than faking a
  method that returns a genuine domain object.
- **Team skill and organisational fit.** The pattern favours teams where SQL
  competence is uneven and where a DBA wants a small, stable surface of
  queries to review. It costs little to a team that is equally comfortable
  writing SQL and writing an ORM query, where the extra indirection buys
  little.

## 4. Applicability and non-applicability

### When to reach for it

- The application has thin domain logic and is organised around Transaction
  Script, page controllers, or a service layer that talks directly to the
  database, and SQL statements for one table are currently duplicated or
  scattered across the codebase.
- The team wants every SQL statement for a table reviewable and tunable in one
  file, so a DBA or a senior engineer can audit and optimise it without
  chasing call sites.
- The runtime's native data access idiom already returns generic in-memory
  tabular structures, an ADO.NET `DataTable`, a PHP associative array, a
  Go `[]map[string]any`, so wrapping that access in a table-shaped object adds
  structure without fighting the platform.
- The codebase is migrating away from inline SQL incrementally and Table Data
  Gateway is a deliberately small first step, one that can later be replaced
  by Data Mapper or wrapped by a Repository without touching call sites, per
  dimension 14.
- Language platforms with strong built-in dataset abstractions, most visibly
  .NET's `DataAdapter` and Visual Studio's generated `TableAdapter` classes
  (see dimension 9), where the pattern is close to the idiomatic default for
  simple CRUD screens.

### When NOT to reach for it, and why

- **The domain has real behaviour attached to the data.** Order totals that
  must recompute on line-item change, an account balance that must never go
  negative, an approval workflow with state transitions. That behaviour needs
  a home, and a gateway that returns bare rows has nowhere to put it. Active
  Record or a Domain Model with Data Mapper is the better fit, because the
  behaviour and the data belong together (see dimension 13).
- **The persistence model must stay independent of the domain model.** Any
  system with a rich domain model deliberately shaped by business rules,
  independent of the schema, should reach for Data Mapper or Repository
  instead. Coupling the domain to one row-per-table shape defeats the
  independence those patterns exist to provide.
- **The query needs span more than one table in a way no single table owns.**
  A search that joins five tables and returns a flattened projection does not
  belong inside any one table's gateway. A dedicated query object, a
  read-model, or a view-backed gateway fits better than stretching one
  table's gateway to answer a cross-table question.
- **The team already uses an ORM with a mature unit of work and identity map.**
  Introducing a hand-rolled Table Data Gateway alongside an existing ORM for
  the same tables creates two conflicting sources of truth for how a row is
  read and written, and the two will drift.
- **Concurrent writers must coordinate change tracking across an entire
  transaction.** Table Data Gateway has no notion of a Unit of Work, every
  call executes its own statement. A workflow that needs to batch several
  changes to several tables into one atomic, dirty-tracked commit needs a
  Unit of Work layered on top, or a richer pattern that already includes one.
- **The row identity matters more than the table does.** Passing a single row
  around a call stack, mutating it, and saving it back is Row Data Gateway's
  job, not Table Data Gateway's, see dimension 13 for the precise line.

## 5. Structure

- **Table Data Gateway.** One class per database table or view. It exposes
  finder methods that return a generic in-memory record set, and mutator
  methods, insert, update, delete, that accept either individual column values
  or a generic record. It holds no reference to any specific row, a single
  instance serves every row in the table, and in most implementations the
  gateway is stateless enough to be a singleton or created fresh per call with
  no observable difference in behaviour.
- **Record Set, DataTable, or row structure.** The generic, un-typed carrier of
  data that the gateway returns and accepts. This is not part of the pattern's
  own vocabulary in the strict sense, but every real implementation needs
  something to hold a row, whether that is an ADO.NET `DataTable`, a PHP
  associative array, a `sql.Rows` cursor mapped to a struct, or a simple
  key-value map. The gateway owns the mapping between this generic structure
  and the SQL that produces or consumes it.
- **Client.** A Transaction Script, a service method, or a controller that
  calls the gateway to fetch or persist data and then does whatever it needs
  with the returned rows, including handing them to a view or wrapping them
  in a short-lived value object of its own choosing.
- **Connection or DataSource.** The database connection or connection pool the
  gateway uses to execute its statements. In simple implementations this is
  injected once at construction, in ambient-transaction implementations it is
  resolved per call from a scoped context.

## 6. ASCII structure diagram

```
+---------------------------+
|          Client           |
|  (Transaction Script,     |
|   service, controller)    |
+-------------+-------------+
              |
              | calls finder / mutator methods
              v
+---------------------------+        +---------------------------+
|   UserTableGateway        |------->|   Connection / DataSource  |
|---------------------------|        |   (owns the SQL driver)    |
| + findById(id)            |        +---------------------------+
| + findByEmail(email)      |
| + findActive()            |
| + insert(fields)          |
| + update(id, fields)      |
| + delete(id)              |
+-------------+-------------+
              |
              | returns / accepts
              v
+---------------------------+
|  generic row structure    |
|  (DataTable, map, dict,   |
|   struct slice)           |
+---------------------------+

One UserTableGateway instance serves every row of the "users" table.
A second table gets a second gateway class, e.g. OrderTableGateway,
with its own finder and mutator methods for the "orders" table.
```

## 7. Dynamics

```
Client                    UserTableGateway              Database
  |                              |                          |
  | findByEmail("a@x.com")       |                          |
  |----------------------------->|                          |
  |                              | SELECT * FROM users      |
  |                              | WHERE email = ?          |
  |                              |------------------------->|
  |                              |                          |
  |                              |<-------------------------|
  |                              | rows (0 or more)         |
  |<-----------------------------|                          |
  | generic record set           |                          |
  |                              |                          |
  | -- client reads/uses rows, may mutate a local copy --   |
  |                              |                          |
  | update(id, {status: "active"})                          |
  |----------------------------->|                          |
  |                              | UPDATE users SET         |
  |                              | status = ? WHERE id = ?  |
  |                              |------------------------->|
  |                              |<-------------------------|
  |                              | rows affected             |
  |<-----------------------------|                          |
  | boolean / affected count     |                          |
```

Each call to the gateway is a single, self-contained round trip. There is no
session, no change tracking, and no deferred flush. If the client needs
several statements to succeed or fail together, the transaction boundary is
the client's responsibility, opened before the first call and committed or
rolled back after the last, using whatever transaction primitive the platform
gives the connection. The gateway itself is transaction-agnostic by design, it
executes whatever statement is asked of it against whatever connection or
transaction context it is handed.

## 8. Implementation variants

- **Concrete gateway per table, hand-written.** The default shape. One class,
  named after the table, containing every finder and mutator the application
  needs for that table, each method a thin wrapper around one parameterised
  SQL statement. This is the variant shown in the code samples below.
- **Generic gateway, table name as configuration.** A single reusable class
  parameterised by table name and column list at construction time, used for
  many simple tables that share no special query logic beyond CRUD. This
  trades a small amount of type safety and IDE discoverability for less
  boilerplate, and is common in dynamically typed languages where reflection
  or metaprogramming can build the SQL from a schema description at runtime.
  Laminas's `AbstractTableGateway` (dimension 9) supports both a subclassed
  and a generic-instance usage.
- **Dataset-backed gateway (.NET style).** The gateway wraps an ADO.NET
  `DataAdapter`, exposing `Fill` to populate a `DataTable` and `Update` to push
  changed rows back, with `SelectCommand`, `InsertCommand`, `UpdateCommand`,
  and `DeleteCommand` properties holding the four parameterised statements
  (Microsoft, "DbDataAdapter Class",
  https://learn.microsoft.com/en-us/dotnet/api/system.data.common.dbdataadapter,
  verified 2026-08-11). Visual Studio's TableAdapter designer generates this
  variant automatically from a typed DataSet, one generated class per table
  (Microsoft, "Fill datasets by using TableAdapters",
  https://learn.microsoft.com/en-us/visualstudio/data-tools/fill-datasets-by-using-tableadapters,
  verified 2026-08-11).
- **Query-object-composed gateway.** Rather than hard-coding each SQL string,
  the gateway builds statements through a query builder or SQL DSL internal
  to the method body, which helps when the same table needs many optional
  filter combinations, at some cost to readability of the generated SQL by a
  reviewer who wants to see the literal statement.
- **View-backed gateway.** The gateway targets a database view rather than a
  base table, useful when a read-heavy access pattern needs a denormalised
  shape but the team still wants the encapsulation and naming discipline of
  a table-shaped gateway rather than a fully separate query object.
- **Stored-procedure-backed gateway.** Every method delegates to a stored
  procedure rather than inline SQL, common in environments where the DBA team
  owns and versions all data access logic separately from the application
  deploy cycle.

## 9. Known production uses

- **ADO.NET `DataAdapter` and `DbDataAdapter`.** The `DbDataAdapter` base
  class defines `SelectCommand`, `InsertCommand`, `UpdateCommand`, and
  `DeleteCommand` properties, each holding a parameterised statement for one
  table, and exposes `Fill` to populate a `DataTable` from the select
  statement and `Update` to push row changes back through the other three
  (Microsoft, "DbDataAdapter Class",
  https://learn.microsoft.com/en-us/dotnet/api/system.data.common.dbdataadapter,
  verified 2026-08-11). This is Table Data Gateway as a first-class .NET
  Framework abstraction, present since .NET Framework 1.1 and still in the
  current documentation set at the time of verification.
- **Visual Studio TableAdapter code generation.** The TableAdapter designer
  generates one class per database table, named after the table, for example
  `OrdersTableAdapter`, exposing `Fill` and `GetData` methods that run the
  adapter's select statement and `Update`, `Insert`, `Delete` helper methods
  wired to the adapter's other three commands (Microsoft, "Fill datasets by
  using TableAdapters in .NET Framework applications",
  https://learn.microsoft.com/en-us/visualstudio/data-tools/fill-datasets-by-using-tableadapters,
  verified 2026-08-11). This is a code generator whose entire output is Table
  Data Gateway instances, one per table, wired into the typed DataSet design
  surface of Visual Studio.
- **Laminas (formerly Zend Framework) `Zend\Db\TableGateway`.** The component
  documentation describes it as "an object-oriented representation of a
  database table, its methods mirror the most common table operations", with
  each `TableGateway` instance corresponding to one table and exposing
  `select()`, `insert()`, `update()`, and `delete()` methods for that table
  (Laminas/Zend Framework documentation, "Zend\\Db\\TableGateway Overview",
  https://docs.zendframework.com/zend-db/table-gateway/, verified
  2026-08-11). The class is literally named `TableGateway`, and its
  predecessor in Zend Framework 1, `Zend_Db_Table_Abstract`, shipped the same
  one-instance-per-table shape for over a decade of PHP enterprise
  applications built on that framework.

## 10. Consequences

### Positive

- Every SQL statement that touches a table lives in one file, so a schema
  change, a column rename, an index-friendly rewrite, is a one-place edit
  instead of a codebase-wide search, matching Fowler's stated intent for the
  pattern.
- A DBA or a senior reviewer can audit and tune the entire SQL surface for a
  table in a single review, without reading every call site that touches that
  table.
- The pattern is small and mechanical enough that a developer who is not
  strong in SQL can call named methods, `findByEmail`, `insertOrder`, without
  writing SQL themselves.
- It maps cleanly onto platforms that already speak in generic tabular
  structures, ADO.NET DataTables, PHP associative arrays, requiring no
  additional mapping infrastructure beyond the gateway itself.
- It is a low-cost, incremental step out of scattered inline SQL, and a
  natural stepping stone toward Data Mapper or Repository later, because the
  SQL is already isolated behind a stable interface (see dimension 14).

### Negative

- The gateway carries no domain behaviour, so any business rule attached to
  the data needs a home elsewhere, and that home is easy to skip under
  deadline pressure, which pushes logic back into callers and recreates the
  scattering problem one level up.
- Returning generic, untyped rows sacrifices compile-time safety in statically
  typed languages, a column rename in the database silently breaks every
  caller that reads the old column name from the returned structure, and the
  break only surfaces at runtime.
- The pattern has no built-in transaction or unit-of-work concept, so
  coordinating several gateway calls into one atomic operation is entirely
  the client's responsibility, and a client that forgets this can commit a
  half-finished multi-table change.
- The one-gateway-per-table shape does not extend gracefully to queries that
  genuinely need several tables, which either bloats a single gateway with
  cross-table methods that do not belong to it, duplicates logic across two
  gateways, or forces an escape hatch that undermines the encapsulation the
  pattern exists to provide.
- At larger scale, the number of gateway classes grows one-for-one with the
  number of tables, and a schema with many tables produces a correspondingly
  large, flat set of gateway classes with no higher-level organisation beyond
  the schema itself.

## 11. Failure modes and misuse

- **Symptom.** A gateway method named `update` silently overwrites columns the
  caller never intended to touch, and a concurrent edit from another request
  is lost.
  **Cause.** The `update` method accepts a full record and issues a blanket
  `UPDATE table SET col1=?, col2=?, ... WHERE id=?` regardless of which
  columns actually changed, and does not check the row's current state before
  writing, so two callers reading the same stale copy overwrite each other's
  changes with the classic lost-update race.
  **Fix.** Accept a partial field set rather than a full record for updates
  where partial updates are common, and add optimistic concurrency, a version
  column or a timestamp checked in the `WHERE` clause, when concurrent writers
  are realistic.

- **Symptom.** A finder method's SQL grows an unreadable pile of optional
  `AND` clauses, each guarded by a null check, and every new filter the
  product asks for adds another branch.
  **Cause.** The team kept adding filter parameters to one general-purpose
  `find` method instead of introducing a small query-builder internal to the
  gateway or splitting into named, specific finder methods.
  **Fix.** Split into intention-revealing finder methods for the common
  cases, `findActiveByRegion`, `findExpiredTrials`, and reserve a
  parameterised general finder, built with a query builder rather than string
  concatenation, only for the genuinely dynamic case.

- **Symptom.** Business logic that clearly belongs to the domain, discount
  eligibility, order-total recomputation, is scattered across three different
  service classes that all call the same table gateway and each reimplement
  a slightly different version of the same rule.
  **Cause.** The gateway returns bare data with nowhere to attach behaviour,
  and the team never introduced a service layer or domain object to hold that
  behaviour, so each caller reinvented it.
  **Fix.** Introduce a thin domain object or a dedicated service method that
  wraps the gateway call and owns the rule in one place. If this keeps
  recurring, that is the signal the application has outgrown Table Data
  Gateway and should move toward Active Record or Data Mapper (dimension 14).

- **Symptom.** A multi-table operation, transferring an order from one
  customer to another, leaves the database in an inconsistent state after a
  crash partway through.
  **Cause.** The client called two gateways, `OrderTableGateway.update` and
  `CustomerTableGateway.update`, as two separate implicit transactions rather
  than wrapping both calls in one explicit transaction, because the gateway
  offers no transaction concept of its own and the client forgot to add one.
  **Fix.** Open an explicit transaction on the shared connection before the
  first gateway call and commit or roll back after the last, and make the
  transaction boundary visible at the call site rather than buried inside any
  one gateway.

- **Symptom.** SQL injection through a finder method that looked safe in
  review.
  **Cause.** A method built its `WHERE` clause by string-concatenating a
  caller-supplied value directly into the SQL text instead of using a
  parameterised statement, often introduced later by a developer adding a new
  filter to an existing method under time pressure and copying the wrong
  nearby pattern.
  **Fix.** Enforce parameterised statements as the only way any gateway
  method builds SQL, and add a lint or code-review checklist item that
  rejects any string concatenation of caller-supplied values into a SQL
  literal.

## 12. Trade-off matrix

Judgement, weighed against the same three named alternatives across the forces
from dimension 3.

| Force | Table Data Gateway | Row Data Gateway | Active Record | Data Mapper |
|---|---|---|---|---|
| Domain behaviour location | None, lives entirely in the caller | None, lives entirely in the caller | On the row object itself | On separate domain objects, mapper stays ignorant of them |
| Unit returned per call | Whole result set, generic rows | One wrapped row per instance | One domain-and-data object per row | One domain object per row, independent of table shape |
| SQL encapsulation | Full, per table, in one class | Full, per row type, in one class | Full, but mixed with domain logic in the same class | Full, isolated from the domain entirely |
| Cost to introduce | Low, a thin wrapper over existing SQL | Low to moderate, needs identity per row | Moderate, needs a base class and a persistence contract per domain type | High, needs a mapping layer and often a unit of work |
| Fit for rich domain rules | Poor, no home for rules | Poor, no home for rules | Good for simple to moderate rules | Best, domain fully independent of schema |
| Fit for cross-table queries | Poor, one class per table | Poor, one row type at a time | Poor unless modelled as its own aggregate | Good, mapper can compose across tables per aggregate |
| Testability without a database | Moderate, fake the gateway interface | Moderate, fake the row interface | Harder, persistence and domain logic are entangled | Best, domain objects test with no persistence at all |

## 13. Related and incompatible patterns

- **Row Data Gateway (closely related, mutually exclusive for the same table).**
  Both patterns encapsulate SQL for a table and return no domain behaviour,
  the difference is granularity. Table Data Gateway is one instance for the
  whole table and returns generic multi-row result sets. Row Data Gateway is
  one instance per row and exposes typed accessors for that row's columns
  (Fowler, "Row Data Gateway",
  https://martinfowler.com/eaaCatalog/rowDataGateway.html, verified
  2026-08-11). Applying both patterns to the same table at once is
  contradictory, because they disagree on what one instance represents, so a
  codebase picks one per table, though different tables in the same
  application can legitimately use different choices.
- **Active Record (composes poorly, usually a replacement, not an addition).**
  Active Record is Table Data Gateway's data-plus-behaviour cousin, an object
  that wraps a row, encapsulates its own database access, and adds domain
  logic on top (Fowler, "Active Record",
  https://martinfowler.com/eaaCatalog/activeRecord.html, verified
  2026-08-11). A codebase evolving from Table Data Gateway toward richer
  domain behaviour typically migrates by merging the gateway's per-row
  concerns into an Active Record class rather than running both side by side
  for the same table.
- **Data Mapper (complementary at a distance, replacement at a table).** Data
  Mapper keeps the domain model wholly ignorant of the database, moving data
  between the two through a separate layer. A Table Data Gateway can be the
  thing a Data Mapper calls internally to execute its SQL, which is a
  reasonable composition, gateway as the low-level data-access primitive,
  mapper as the layer that reconstitutes domain objects from what the
  gateway returns.
- **Repository (usually built on top, never confused with).** A Repository
  presents a collection-like interface over domain objects and mediates
  between the domain and the mapping layer (Fowler, "Repository",
  https://martinfowler.com/eaaCatalog/repository.html, verified 2026-08-11).
  A Repository implementation frequently delegates its actual row access to
  one or more Table Data Gateways internally, while the Repository's own
  interface never leaks that a table, or several tables, sit underneath it.
  This is the most common healthy composition of the two patterns.
- **Unit of Work (composes on top, not included).** Table Data Gateway has no
  transaction or change-tracking concept of its own. A Unit of Work layered
  above several gateway calls is how an application gets coordinated,
  all-or-nothing multi-table commits without adding that responsibility to
  the gateway itself.
- **Query Object (composes when finder logic grows complex).** When a
  gateway's finder methods need genuinely dynamic filter composition, a Query
  Object internal to or alongside the gateway keeps the SQL construction
  readable without polluting the gateway's public method surface with dozens
  of near-duplicate finders.

## 14. Refactoring path in and out

### Introducing Table Data Gateway into code with scattered inline SQL

1. Pick one table whose SQL is duplicated across the most call sites, that is
   the highest-value first extraction.
2. Create a new class named after the table, `UsersTableGateway`, with a
   private connection reference.
3. For each distinct SQL statement touching that table found across the
   codebase, create one method on the gateway with a name that describes the
   query's intent, not its SQL shape, `findActiveByRegion` rather than
   `queryWithTwoFilters`, and move the exact parameterised statement into that
   method.
4. Replace each call site's inline SQL with a call to the new gateway method,
   one call site at a time, verifying behaviour is unchanged after each
   replacement. This mirrors the "Extract Method" and "Move Method" spirit of
   Fowler's refactoring catalogue applied at the data-access boundary.
5. Once every call site for that table goes through the gateway, delete any
   now-dead direct-connection code paths for that table and repeat for the
   next table.
6. Add a construction-time or DI-container wiring point for the gateway so
   call sites depend on an interface or an injected instance rather than a
   concrete class with a hard-coded connection, which pays off immediately in
   dimension 15's testing story.

### Removing Table Data Gateway once behaviour accretes around it

1. Recognise the exit signal from dimension 11's third failure mode, domain
   logic repeatedly reimplemented around the same gateway calls in multiple
   callers.
2. Introduce a thin domain class per row concept that currently has
   duplicated logic, and move that logic onto the new class as methods.
3. Have the new domain class hold a reference to the existing table gateway
   internally for its persistence calls, so the gateway is not thrown away,
   it becomes an implementation detail of the new domain class. This is the
   Table Data Gateway to Active Record transition.
4. Once every caller talks to the domain class rather than the gateway
   directly, the gateway's public surface can shrink to exactly what the
   domain class needs, and any remaining direct callers are the signal that
   the domain class's interface is still incomplete.
5. If the eventual target is Data Mapper or Repository instead of Active
   Record, keep the domain objects free of any reference to the gateway. Put
   the gateway calls inside a separate mapper class that reconstitutes and
   flushes domain objects using the gateway as its low-level data-access
   primitive.

## 15. Testing and verification

Table Data Gateway makes one thing easy to test and one thing hard to test,
and the split falls exactly where the pattern draws its boundary.

What becomes easy is testing any code that calls the gateway. A Transaction
Script or a service method can be tested against a fake or in-memory
implementation of the gateway's interface, because the interface is small and
mechanical, returning plain data structures rather than framework-specific
database handles. A test double that returns a hard-coded record set for
`findByEmail` and records the arguments passed to `update` is enough to test
every caller's logic without touching a real database, provided the gateway
is defined behind an interface or a duck-typed contract in the language rather
than depended on as a concrete class, which is why step 6 of the introduction
refactor above matters for testability, and not only for wiring convenience.

What stays hard is verifying the gateway class itself, because its entire
reason for existing is correct SQL, and that needs a real database or a
close-enough substitute. A unit test that mocks the connection object and
asserts the exact SQL string was called is brittle, it breaks on any
harmless rewording of a query that produces the identical result, and it does
not catch a SQL statement that is syntactically valid but semantically wrong.
The reliable technique is an integration test against a real instance of the
target database engine, run against a disposable schema per test or per test
run, populated with known fixture rows, asserting on the returned data rather
than on the SQL text. Test doubles for the connection are appropriate only for
testing error-handling paths, a dropped connection, a constraint violation
surfaced as an exception, where reproducing the real failure reliably against
a live database is itself the harder problem.

A useful discipline is keeping the gateway's own test suite small and focused
on exactly the statements the class contains, one test per finder and one per
mutator, while every other test in the codebase that would have needed a real
database instead depends on the fake gateway interface. This keeps the slow,
database-backed test suite proportional to the number of tables rather than
to the number of callers.

## 16. Observability signals

Judgement, drawn from operating this shape of data access layer in practice.

- **Per-method call counts and latency, tagged by gateway class and method
  name.** Because every method name already describes an intention-revealing
  query, this gives a query-shaped latency breakdown for free, without
  needing to parse or normalise raw SQL text for grouping. A healthy gateway
  shows stable, low p99 latency per method. A spike isolated to one method
  points at a specific missing index or a query that changed shape under a
  new filter combination.
- **Row counts returned per finder call.** A finder that historically returns
  tens of rows and starts returning tens of thousands is either a genuine
  data growth event worth capacity planning for, or a missing filter that
  slipped past review, and this is visible only if the count is measured at
  the gateway boundary rather than inferred from downstream symptoms.
- **Affected-row counts on mutators, compared against expected values.** An
  `update` that is supposed to touch exactly one row by primary key but
  reports zero or more than one affected rows is a strong, cheap signal of a
  bad `WHERE` clause, a stale primary key, or an unexpectedly duplicated row,
  and is worth asserting on in code, not only observing in a dashboard.
- **Connection pool saturation attributable to a specific gateway's call
  pattern.** Because every gateway call is a single round trip with no
  session state, an unhealthy pattern usually shows up as one gateway issuing
  far more round trips per logical operation than its callers expect, an N+1
  pattern where a loop over a result set calls a second finder once per row
  instead of once per batch.
- **Slow query log correlation by statement fingerprint.** Because the
  gateway centralises every statement for a table into one file, mapping a
  database's slow query log back to the exact method and call site is a
  direct, one-hop lookup rather than a codebase-wide search, which is one of
  the pattern's clearest operational payoffs over scattered inline SQL.

## 17. Security and privacy implications

The pattern's centralisation of SQL is itself a security control, not merely
an organisational convenience. Every statement for a table sits in one place,
which makes a security review of that table's data access surface a bounded,
single-file exercise rather than a codebase-wide search for every place a
table name appears in a string.

The primary risk the pattern introduces is the reverse of that benefit if
discipline slips. Because every method in the gateway builds SQL, a single
method that falls back to string concatenation of a caller-supplied value
reintroduces SQL injection risk for that one table's entire application
surface, since every caller trusts the gateway's methods as safe by
construction. Parameterised statements, never string-built SQL from external
input, must be a non-negotiable, enforced convention within the gateway class,
because the gateway is precisely the trust boundary every caller relies on.

Because the gateway typically returns generic, untyped rows rather than
domain objects with field-level access control, it does not itself enforce
column-level authorisation. A gateway's `findById` will happily return a
sensitive column, a password hash, a national identifier, to any caller that
asks for a row, with no built-in concept of which caller is allowed to see
which column. Any column-level access restriction has to be enforced by the
caller, by a narrower finder method that explicitly excludes sensitive
columns from its `SELECT` list, or by a layer above the gateway. It is not
something the pattern provides for free, and assuming otherwise is a real
data-exposure risk in codebases that treat "it went through the gateway" as
synonymous with "it was checked."

Auditing and data-retention concerns benefit from the same centralisation
that helps security review. A requirement to log every write to a regulated
table, or to purge rows past a retention window, has exactly one file per
table to instrument, rather than needing to find and modify every scattered
`INSERT` or `DELETE` statement across the codebase.

## 18. References

- Martin Fowler, "Table Data Gateway",
  https://martinfowler.com/eaaCatalog/tableDataGateway.html, verified
  2026-08-11.
- Martin Fowler, "Row Data Gateway",
  https://martinfowler.com/eaaCatalog/rowDataGateway.html, verified
  2026-08-11.
- Martin Fowler, "Active Record",
  https://martinfowler.com/eaaCatalog/activeRecord.html, verified
  2026-08-11.
- Martin Fowler, "Repository",
  https://martinfowler.com/eaaCatalog/repository.html, verified 2026-08-11.
- Martin Fowler, *Patterns of Enterprise Application Architecture*,
  Addison-Wesley, 2002, Data Source Architectural Patterns chapter, "Table
  Data Gateway".
- Microsoft, "DbDataAdapter Class (System.Data.Common)",
  https://learn.microsoft.com/en-us/dotnet/api/system.data.common.dbdataadapter,
  verified 2026-08-11.
- Microsoft, "Fill datasets by using TableAdapters in .NET Framework
  applications",
  https://learn.microsoft.com/en-us/visualstudio/data-tools/fill-datasets-by-using-tableadapters,
  verified 2026-08-11.
- Laminas Project (formerly Zend Framework) documentation, "Zend\\Db\\TableGateway
  Overview", https://docs.zendframework.com/zend-db/table-gateway/, verified
  2026-08-11.

## Code examples

Three languages, TypeScript, Python, and Go. Java was unavailable on the
authoring machine, `javac` reported no JRE located, and was skipped rather
than shipped unverified.

### TypeScript

```typescript
// users_gateway.ts
// Table Data Gateway for a "users" table. One instance serves every row.

interface UserRow {
  id: number;
  email: string;
  status: string;
}

interface SqlConnection {
  query(sql: string, params: unknown[]): UserRow[];
  execute(sql: string, params: unknown[]): number; // returns affected rows
}

class UsersTableGateway {
  constructor(private readonly conn: SqlConnection) {}

  findById(id: number): UserRow | undefined {
    const rows = this.conn.query(
      "SELECT id, email, status FROM users WHERE id = ?",
      [id]
    );
    return rows[0];
  }

  findByEmail(email: string): UserRow | undefined {
    const rows = this.conn.query(
      "SELECT id, email, status FROM users WHERE email = ?",
      [email]
    );
    return rows[0];
  }

  findActive(): UserRow[] {
    return this.conn.query(
      "SELECT id, email, status FROM users WHERE status = ?",
      ["active"]
    );
  }

  insert(email: string, status: string): number {
    this.conn.execute(
      "INSERT INTO users (email, status) VALUES (?, ?)",
      [email, status]
    );
    return 1;
  }

  updateStatus(id: number, status: string): number {
    return this.conn.execute(
      "UPDATE users SET status = ? WHERE id = ?",
      [status, id]
    );
  }

  delete(id: number): number {
    return this.conn.execute("DELETE FROM users WHERE id = ?", [id]);
  }
}

// A fake connection, standing in for a real driver, to keep the sample
// runnable with no external database.
class InMemoryConnection implements SqlConnection {
  private rows: UserRow[] = [
    { id: 1, email: "a@x.com", status: "active" },
    { id: 2, email: "b@x.com", status: "pending" },
  ];

  query(sql: string, params: unknown[]): UserRow[] {
    if (sql.includes("WHERE id = ?")) {
      return this.rows.filter((r) => r.id === params[0]);
    }
    if (sql.includes("WHERE email = ?")) {
      return this.rows.filter((r) => r.email === params[0]);
    }
    if (sql.includes("WHERE status = ?")) {
      return this.rows.filter((r) => r.status === params[0]);
    }
    return this.rows;
  }

  execute(sql: string, params: unknown[]): number {
    if (sql.startsWith("UPDATE")) {
      const [status, id] = params as [string, number];
      const row = this.rows.find((r) => r.id === id);
      if (row) {
        row.status = status;
        return 1;
      }
      return 0;
    }
    if (sql.startsWith("DELETE")) {
      const [id] = params as [number];
      const before = this.rows.length;
      this.rows = this.rows.filter((r) => r.id !== id);
      return before - this.rows.length;
    }
    if (sql.startsWith("INSERT")) {
      const [email, status] = params as [string, string];
      const nextId = this.rows.length + 1;
      this.rows.push({ id: nextId, email, status });
      return 1;
    }
    return 0;
  }
}

function main(): void {
  const gateway = new UsersTableGateway(new InMemoryConnection());

  const active = gateway.findActive();
  console.log("active users", active.length);

  const affected = gateway.updateStatus(2, "active");
  console.log("rows updated", affected);

  const found = gateway.findById(2);
  console.log("user 2 status", found ? found.status : undefined);
}

main();
```

Run with `npx tsc --strict --target es2020 --module commonjs users_gateway.ts
&& node users_gateway.js`.

### Python

```python
# users_gateway.py
# Table Data Gateway for a "users" table. One instance serves every row.

from dataclasses import dataclass
from typing import Optional


@dataclass
class UserRow:
    id: int
    email: str
    status: str


class UsersTableGateway:
    """One instance handles every row of the users table."""

    def __init__(self, connection: "InMemoryConnection") -> None:
        self._conn = connection

    def find_by_id(self, user_id: int) -> Optional[UserRow]:
        rows = self._conn.query(
            "SELECT id, email, status FROM users WHERE id = ?", (user_id,)
        )
        return rows[0] if rows else None

    def find_by_email(self, email: str) -> Optional[UserRow]:
        rows = self._conn.query(
            "SELECT id, email, status FROM users WHERE email = ?", (email,)
        )
        return rows[0] if rows else None

    def find_active(self) -> list[UserRow]:
        return self._conn.query(
            "SELECT id, email, status FROM users WHERE status = ?", ("active",)
        )

    def insert(self, email: str, status: str) -> int:
        return self._conn.execute(
            "INSERT INTO users (email, status) VALUES (?, ?)", (email, status)
        )

    def update_status(self, user_id: int, status: str) -> int:
        return self._conn.execute(
            "UPDATE users SET status = ? WHERE id = ?", (status, user_id)
        )

    def delete(self, user_id: int) -> int:
        return self._conn.execute("DELETE FROM users WHERE id = ?", (user_id,))


class InMemoryConnection:
    """Stands in for a real DB-API connection so the sample runs standalone."""

    def __init__(self) -> None:
        self._rows: list[UserRow] = [
            UserRow(1, "a@x.com", "active"),
            UserRow(2, "b@x.com", "pending"),
        ]

    def query(self, sql: str, params: tuple) -> list[UserRow]:
        if "WHERE id = ?" in sql:
            return [r for r in self._rows if r.id == params[0]]
        if "WHERE email = ?" in sql:
            return [r for r in self._rows if r.email == params[0]]
        if "WHERE status = ?" in sql:
            return [r for r in self._rows if r.status == params[0]]
        return list(self._rows)

    def execute(self, sql: str, params: tuple) -> int:
        if sql.startswith("UPDATE"):
            status, user_id = params
            for r in self._rows:
                if r.id == user_id:
                    r.status = status
                    return 1
            return 0
        if sql.startswith("DELETE"):
            (user_id,) = params
            before = len(self._rows)
            self._rows = [r for r in self._rows if r.id != user_id]
            return before - len(self._rows)
        if sql.startswith("INSERT"):
            email, status = params
            next_id = len(self._rows) + 1
            self._rows.append(UserRow(next_id, email, status))
            return 1
        return 0


def main() -> None:
    gateway = UsersTableGateway(InMemoryConnection())

    active = gateway.find_active()
    print("active users", len(active))

    affected = gateway.update_status(2, "active")
    print("rows updated", affected)

    found = gateway.find_by_id(2)
    print("user 2 status", found.status if found else None)


if __name__ == "__main__":
    main()
```

Run with `python3 users_gateway.py`.

### Go

```go
// users_gateway.go
// Table Data Gateway for a "users" table. One instance serves every row.
package main

import "fmt"

type UserRow struct {
	ID     int
	Email  string
	Status string
}

// Conn is the narrow interface the gateway depends on, so a test can
// substitute a fake without touching a real database driver.
type Conn interface {
	Query(sql string, args ...any) []UserRow
	Exec(sql string, args ...any) int
}

type UsersTableGateway struct {
	conn Conn
}

func NewUsersTableGateway(conn Conn) *UsersTableGateway {
	return &UsersTableGateway{conn: conn}
}

func (g *UsersTableGateway) FindByID(id int) (UserRow, bool) {
	rows := g.conn.Query("SELECT id, email, status FROM users WHERE id = ?", id)
	if len(rows) == 0 {
		return UserRow{}, false
	}
	return rows[0], true
}

func (g *UsersTableGateway) FindActive() []UserRow {
	return g.conn.Query("SELECT id, email, status FROM users WHERE status = ?", "active")
}

func (g *UsersTableGateway) Insert(email, status string) int {
	return g.conn.Exec("INSERT INTO users (email, status) VALUES (?, ?)", email, status)
}

func (g *UsersTableGateway) UpdateStatus(id int, status string) int {
	return g.conn.Exec("UPDATE users SET status = ? WHERE id = ?", status, id)
}

func (g *UsersTableGateway) Delete(id int) int {
	return g.conn.Exec("DELETE FROM users WHERE id = ?", id)
}

// inMemoryConn stands in for a real sql.DB so the sample runs standalone.
type inMemoryConn struct {
	rows []UserRow
}

func newInMemoryConn() *inMemoryConn {
	return &inMemoryConn{
		rows: []UserRow{
			{ID: 1, Email: "a@x.com", Status: "active"},
			{ID: 2, Email: "b@x.com", Status: "pending"},
		},
	}
}

func (c *inMemoryConn) Query(sql string, args ...any) []UserRow {
	switch {
	case contains(sql, "WHERE id = ?"):
		id := args[0].(int)
		var out []UserRow
		for _, r := range c.rows {
			if r.ID == id {
				out = append(out, r)
			}
		}
		return out
	case contains(sql, "WHERE status = ?"):
		status := args[0].(string)
		var out []UserRow
		for _, r := range c.rows {
			if r.Status == status {
				out = append(out, r)
			}
		}
		return out
	default:
		return c.rows
	}
}

func (c *inMemoryConn) Exec(sql string, args ...any) int {
	switch {
	case hasPrefix(sql, "UPDATE"):
		status := args[0].(string)
		id := args[1].(int)
		for i := range c.rows {
			if c.rows[i].ID == id {
				c.rows[i].Status = status
				return 1
			}
		}
		return 0
	case hasPrefix(sql, "DELETE"):
		id := args[0].(int)
		before := len(c.rows)
		var kept []UserRow
		for _, r := range c.rows {
			if r.ID != id {
				kept = append(kept, r)
			}
		}
		c.rows = kept
		return before - len(kept)
	case hasPrefix(sql, "INSERT"):
		email := args[0].(string)
		status := args[1].(string)
		nextID := len(c.rows) + 1
		c.rows = append(c.rows, UserRow{ID: nextID, Email: email, Status: status})
		return 1
	default:
		return 0
	}
}

func contains(s, sub string) bool {
	return len(s) >= len(sub) && indexOf(s, sub) >= 0
}

func hasPrefix(s, prefix string) bool {
	return len(s) >= len(prefix) && s[:len(prefix)] == prefix
}

func indexOf(s, sub string) int {
	for i := 0; i+len(sub) <= len(s); i++ {
		if s[i:i+len(sub)] == sub {
			return i
		}
	}
	return -1
}

func main() {
	gateway := NewUsersTableGateway(newInMemoryConn())

	active := gateway.FindActive()
	fmt.Println("active users", len(active))

	affected := gateway.UpdateStatus(2, "active")
	fmt.Println("rows updated", affected)

	found, ok := gateway.FindByID(2)
	if ok {
		fmt.Println("user 2 status", found.Status)
	}
}
```

Run with `go run users_gateway.go`.
