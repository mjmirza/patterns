---
name: Record Set
slug: record-set
family: 06-enterprise-application-architecture
category: Data Source Architectural Patterns
aliases: [Disconnected Recordset, DataSet, CachedRowSet, ADO Recordset]
first_described: "Fowler 2002"
maturity: established
related: [table-data-gateway, row-data-gateway, data-transfer-object, data-mapper, gateway]
incompatible_with: [domain-model]
verified: 2026-08-02
---

# Record Set

## 1. Name, aliases, and lineage

The canonical name is Record Set, catalogued by Martin Fowler in *Patterns of
Enterprise Application Architecture*, Addison-Wesley, 2002, as one of the Data
Source Architectural Patterns, chapter 18. Fowler states the intent as "an
in-memory representation of tabular data" that bridges the gap between a
data-aware UI framework and a domain layer that needs to run business logic
against results shaped like a database query (Martin Fowler, "Record Set",
martinfowler.com, https://martinfowler.com/eaaCatalog/recordSet.html, verified
2026-08-02).

The pattern predates Fowler's naming of it. The concept goes back to ODBC and
OLE DB cursor-based recordsets in the 1990s, and Fowler's own catalog entry
credits Microsoft's ActiveX Data Objects Recordset as the concrete example he
had in mind when writing the pattern up (the same martinfowler.com entry cites
the ADO Recordset explicitly as the pattern's most recognisable
implementation).

Three names are used interchangeably in practice for the same underlying
shape, and a reader moving between platforms needs to know they line up.

- **Record Set (Fowler's pattern name).** The catalog term for the general
  idea, in-memory tabular data that can be passed around, bound to a UI, and
  updated independently of the connection that produced it.
- **DataSet (ADO.NET).** Microsoft's concrete class, `System.Data.DataSet`,
  which holds a collection of `DataTable` objects plus `DataRelation` objects
  between them, and which is explicitly disconnected from the database once
  populated (Microsoft, ".NET API browser, DataSet Class",
  https://learn.microsoft.com/en-us/dotnet/api/system.data.dataset, verified
  2026-08-02).
- **CachedRowSet (Java, JSR 114).** The javax.sql.rowset interface whose own
  javadoc calls it "a disconnected rowset, which means that it makes use of a
  connection to its data source only briefly" and states it "caches its rows
  in memory, which makes it possible to operate without always being
  connected to its data source" (Oracle, "CachedRowSet",
  https://docs.oracle.com/en/java/javase/21/docs/api/java.sql.rowset/javax/sql/rowset/CachedRowSet.html,
  verified 2026-08-02).

The unifying property across all three names, and the one that separates
Record Set from a plain query result, is disconnection. A Record Set outlives
the connection or the cursor that produced it. It can be handed to a UI
control, serialized, mutated locally, and later reconciled against the
database, all without the original `ResultSet` or cursor still being open.

## 2. Problem and context

A team is building a screen, or a report, or a batch step, that needs to work
with data shaped exactly like a SQL query result. Rows, columns, column
names, column types. The consuming code does not want a domain object graph
with navigation and behaviour, it wants a table it can bind a grid to, sort,
filter, and sometimes edit and write back.

The two obvious choices both cost something. Keep a live `ResultSet` cursor
open and iterate it, which ties up a database connection and a server-side
cursor for as long as the UI is open, and which cannot be handed across a
process boundary because a `ResultSet` is not serializable in most drivers.
Or build a full Domain Model with mapped objects, which is the right answer
when there is real business logic to run, but is expensive to build and to
learn when the actual need is show this query result in a grid and let the
user edit a few cells.

Record Set is the pattern for exactly that middle case. Fetch the result
once, materialise it into an in-memory table structure that knows its own
column names and types, close the connection, and hand the table to whatever
needs it. The table tracks which rows were added, changed, or deleted while
disconnected, so a later step can generate the SQL to reconcile those changes
back to the source without the caller writing that SQL by hand.

The context in which this problem shows up is almost always data-aware UI. A
spreadsheet-like grid, a reporting tool, a rapid-development forms
application, or a batch ETL step that needs to hold a chunk of rows in memory
between a read phase and a write phase. It is a pattern born from tools that
generate UI bindings automatically from a tabular shape, not from
hand-written business objects.

## 3. Forces

- **Development speed versus expressiveness.** Favoured toward speed. A grid
  control can bind directly to a Record Set's columns with no mapping code,
  which is why Visual Basic, classic ASP, and early ADO.NET tooling built
  entire generations of line-of-business software around it. The cost is that
  the table has no vocabulary for the domain, only rows and columns.
- **Connection lifetime versus memory.** Favoured toward short connections. A
  Record Set is filled once and disconnected, so the database connection is
  held only for the fetch and the eventual write-back, not for the whole
  interaction. The trade is that every row in the result now lives in process
  memory for the life of the object, which does not scale to result sets of
  unbounded size.
- **Encapsulation versus transparency.** Sacrificed. A Record Set exposes its
  columns as public, generically typed values. Nothing stops calling code
  from reading or writing any column, and there is no place to put a
  validation rule that fires whenever a specific field changes, short of
  event handlers wired onto the table itself.
- **Update simplicity versus correctness under concurrency.** The pattern
  favours simplicity for the common case, one row changed by one user, and
  is honest about its limits under concurrent edits, see dimension 11 on
  optimistic concurrency failures.
- **Coupling to database shape.** Sacrificed. The table's columns are the
  query's columns. Renaming a column in the query, or changing a join, breaks
  every piece of code that read that column by name or ordinal, because there
  is no interface between the data shape and the consumer the way a Data
  Transfer Object or a domain object would provide.
- **Serializability and cross-process transport.** Favoured. Unlike a live
  cursor, a Record Set is designed to serialize, which is why it was the
  vehicle of choice for passing query results across a COM boundary in
  classic ADO, or across a remoting boundary in early .NET Remoting, before
  REST and JSON largely replaced that need.

## 4. Applicability and non-applicability

Reach for Record Set when the following hold.

- The consuming code genuinely wants tabular data, not domain objects, and
  the UI or reporting tool it feeds is itself tabular, a grid, a pivot, a
  spreadsheet export.
- The application has little or no business logic to apply to the data
  beyond simple validation, and what logic exists can live in event handlers
  attached to the table rather than in a rich object model.
- The interaction pattern is fetch, disconnect, let the user edit for a
  while, then reconcile a small number of changed rows back to the database
  in one batch. Long user-think-time between fetch and write-back is exactly
  where disconnection earns its keep.
- The platform or toolkit already ships strong Record Set support that the
  team would otherwise reinvent, notably ADO.NET DataSet with Windows Forms
  or WPF data binding, or a reporting engine that consumes a tabular data
  source directly.
- The result set is small to moderate, bounded by what is reasonable to hold
  entirely in memory on the client or mid-tier process. Fowler's own
  discussion of the pattern treats it as suited to interactive, human-scale
  data volumes, not batch-scale ones.

Do NOT reach for Record Set in these cases, and the reason matters more than
the rule.

- **There is real business logic to enforce.** A Record Set has no natural
  home for a rule spanning several columns or several rows, such as a
  discount above a threshold needing manager approval. That logic ends up
  either duplicated at every call site that touches the table, or wedged
  into fragile event handlers attached to the table's change notifications.
  This is the case for a Domain Model instead, and it is the single most
  common reason a Record Set-based application becomes unmaintainable as it
  grows. Fowler's own catalog is explicit that Record Set is a Data Source
  pattern, meant to sit at the boundary with the database, not to carry
  domain behaviour (Fowler, *Patterns of Enterprise Application
  Architecture*, Addison-Wesley, 2002, chapter 2, "In the Plane of the
  Architect", and chapter 18 introduction, distinguishing Data Source
  patterns from Domain Logic patterns).
- **The result set is large or unbounded.** Materialising millions of rows
  into an in-memory table defeats the point of streaming a `ResultSet` or
  paging a query, and it produces the out-of-memory failures described in
  dimension 11. A streaming cursor, or paging with `Row Data Gateway`
  fetched in batches, is the honest shape here.
- **The API is meant to be consumed outside the process, over HTTP, by a
  client that does not share the platform's Record Set representation.** A
  `DataSet` serializes to a large, platform-specific XML shape that a
  non-.NET client cannot easily consume. A Data Transfer Object mapped to
  JSON is the interoperable choice for a public or cross-platform API.
- **The team is building on a platform with no strong Record Set primitive,
  or is explicitly avoiding vendor lock-in to one.** Reimplementing ADO.NET's
  change-tracking and reconciliation machinery by hand is a large,
  error-prone undertaking that the platforms which do it well have already
  spent years hardening. Doing it badly on a platform without native support
  is worse than not doing it.
- **The team already has, or is building, a Domain Model or a Table Data
  Gateway layer that maps rows to typed domain objects.** Mixing a Record
  Set into a codebase that otherwise talks in domain objects creates two
  competing vocabularies for the same data, and every consumer has to know
  which one a given method returns.
- **Column names or types genuinely need to be enforced at compile time.** A
  Record Set's columns are accessed by string name or ordinal index and
  resolved at runtime, so a typo in a column name is a runtime failure, not a
  compile error, in every language shown in the code examples.

## 5. Structure

- **Table (or DataTable, ResultSet-like structure).** Holds a collection of
  named, typed columns and a collection of rows. It knows its own schema,
  including primary key columns where declared, and it is the unit that gets
  serialized and passed around.
- **Row.** One entry in the table. It carries the current values for each
  column, and in the mutable form of the pattern it also carries the
  original values fetched from the database plus a row state (unchanged,
  added, modified, deleted), so that later code can compute exactly what
  changed.
- **Column definition (schema).** Metadata describing each column's name,
  data type, nullability, and sometimes constraints such as maximum length
  or whether it is part of the primary key. This is what lets a UI grid
  build itself automatically from the Record Set with no hand-written
  binding code.
- **DataSet or RowSet container (optional, multi-table form).** In ADO.NET
  and in the general shape Fowler describes, several related tables can be
  held together in one container, with relations between them, so a single
  disconnected object can represent an order and its line items as two
  related tables. Not every platform's Record Set implementation offers
  this, single-table variants such as a plain `CachedRowSet` do not.
- **Reconciler (change-application logic).** The component, sometimes a
  method on the table itself, sometimes a separate adapter, that walks the
  rows marked added, modified, or deleted and issues the corresponding
  INSERT, UPDATE, or DELETE statements against the database. ADO.NET calls
  this a `DataAdapter`, and `CachedRowSet` implements the same idea through
  `acceptChanges()`.

## 6. ASCII structure diagram

```
   +-------------------------------------+
   |          Table (DataTable)          |
   |---------------------------------------
   | + Columns: [ColumnDef, ColumnDef,..] |
   | + Rows:    [Row, Row, Row, ...]      |
   | + NewRow(): Row                      |
   | + AcceptChanges()                    |
   | + GetChanges(): Table                |
   +-------------------------------------+
             |  contains many
             v
   +-------------------------------------+
   |                Row                  |
   |---------------------------------------
   | + Values:  {col -> current value}    |
   | + Original: {col -> fetched value}   |
   | + RowState: Unchanged | Added |      |
   |             Modified | Deleted       |
   +-------------------------------------+

   +-------------------------------------+
   |             ColumnDef               |
   |---------------------------------------
   | + Name: string                       |
   | + Type: DataType                     |
   | + IsPrimaryKey: bool                 |
   | + Nullable: bool                     |
   +-------------------------------------+

   +----------------+     fills / reads    +---------------------+
   |    Database     |<-------------------->|  Reconciler /       |
   |  (Connection)   |     writes changes    |  DataAdapter        |
   +----------------+                       |  (short-lived use)   |
                                             +---------------------+
                                                       ^
                                                       | operates on
                                                       |
                                             +---------------------+
                                             |   Table (above)      |
                                             |   while disconnected |
                                             +---------------------+

   The connection is open only during Fill and during AcceptChanges.
   For the rest of the Table's life it holds no connection at all.
```

## 7. Dynamics

The defining trait of the pattern's runtime behaviour is that the connection
to the database is opened twice, briefly, with a long disconnected period in
between where the caller can do anything it wants to the table, including
handing it to a UI thread, serializing it, or passing it to another process.

```
Caller          Reconciler/Adapter        Connection          Table
  |                    |                       |                 |
  |-- Fill(query) ---->|                       |                 |
  |                    |-- open ------------->|                 |
  |                    |-- execute query ---->|                 |
  |                    |<-- rows -------------|                 |
  |                    |-- close ------------>|                 |
  |                    |-- populate Table ------------------->|
  |<-- Table (filled) -|                       |                 |
  |                                                              |
  |  ... connection is CLOSED here. Caller may serialize,        |
  |      bind to a grid, hand to another thread or process ...   |
  |                                                              |
  |-- Rows[3]["price"] = 19.99 ----------------------------------->|
  |                                                (RowState = Modified)
  |-- AddRow({...}) ----------------------------------------------->|
  |                                                (RowState = Added)
  |                                                              |
  |-- Reconcile(Table) ------->|                       |         |
  |                    |-- open ------------->|                 |
  |                    |-- GetChanges() ------------------------->|
  |                    |<-- changed rows only --------------------|
  |                    |-- UPDATE / INSERT / DELETE per row ->|   |
  |                    |<-- rows affected --------------------|  |
  |                    |-- close ------------>|                 |
  |                    |-- AcceptChanges() -------------------->|
  |<-- reconciled ------|                       |    (RowState reset
  |                                                    to Unchanged)
```

Two timing details matter in practice. First, the second connection is opened
only for the rows that actually changed, not the whole table, which is why
`GetChanges()` (ADO.NET) and the analogous filtered walk in `CachedRowSet`
exist as a distinct step from `AcceptChanges()`. Second, nothing in the
pattern re-checks the current database state before writing back, unless the
implementation is explicitly configured to compare original values against
the current database row first. That comparison, when present, is how
optimistic concurrency is detected, and its absence is the most common
production failure mode, covered in dimension 11.

## 8. Implementation variants

**Read-only, forward-only Record Set.** No row-state tracking, no
reconciliation. Used purely to move a query result into memory once, for
reporting or export. Cheapest to build and to reason about, and the shape
most hand-rolled implementations should default to unless write-back is a
genuine requirement.

**Mutable, change-tracked Record Set (the classical form).** Every row
carries both its current and original values and a row state. This is what
ADO.NET `DataTable` and JDBC `CachedRowSet` both implement, and it is the
shape Fowler describes as the pattern proper.

**Multi-table Record Set with relations.** Several related tables held in one
container with parent-child relations declared between them, so that
disconnected data spanning a one-to-many relationship, an order and its line
items, can be handled as one unit. ADO.NET's `DataSet` is the canonical
example, holding a `DataRelationCollection` between its `DataTable` objects
(Microsoft, ".NET API browser, DataRelationCollection Class",
https://learn.microsoft.com/en-us/dotnet/api/system.data.datarelationcollection,
verified 2026-08-02). Single-table variants such as `CachedRowSet` do not
offer this without an additional layer.

**Language-native flat array or dict-of-dicts (the dynamic-language
variant).** Python, Ruby, PHP, and JavaScript rarely build a dedicated
Record Set type. Instead the database driver returns an array or list of
associative arrays or dictionaries directly, and the language's native
collection stands in for the Table and Row structures. PHP's
`PDOStatement::fetchAll(PDO::FETCH_ASSOC)` is the clearest instance, returning
"all remaining rows from a result set" as a plain array of associative
arrays with no separate schema object (PHP Documentation Group,
`PDOStatement::fetchAll`, https://www.php.net/manual/en/pdostatement.fetchall.php,
verified 2026-08-02). This variant gives up change tracking and reconciliation
entirely, trading it for language-native simplicity, and it is the correct
choice when the caller only needs to read.

**Web-tier tabular payload.** A JSON array of objects, or a columnar JSON
shape (parallel arrays of column values), passed from a server API to a
JavaScript grid component such as ag-Grid or Handsontable. This is Record
Set's spiritual descendant on the web, minus the platform-native change
tracking, minus the disconnected-database-connection concept since HTTP is
already stateless and disconnected by construction. Reconciliation, where it
exists, is reimplemented as an explicit PATCH or bulk-update endpoint rather
than inherited from the pattern's own machinery.

**Cached, updatable RowSet over JDBC (Java).** `javax.sql.rowset.CachedRowSet`
implements `RowSet`, `Joinable`, and the change-tracking contract directly in
the standard library, including `acceptChanges(Connection)` to write back and
an optimistic-concurrency check against the row's original values (Oracle,
"CachedRowSet Interface",
https://docs.oracle.com/en/java/javase/21/docs/api/java.sql.rowset/javax/sql/rowset/CachedRowSet.html,
verified 2026-08-02).

## 9. Known production uses

**ADO.NET `System.Data.DataSet` and `DataTable`.** Microsoft's own
documentation describes `DataSet` as representing "an in-memory cache of
data" composed of `DataTable` and `DataRelation` objects, explicitly designed
to be used disconnected from the originating database connection, and it
remains a shipping class in current .NET (Microsoft, ".NET API browser,
DataSet Class", https://learn.microsoft.com/en-us/dotnet/api/system.data.dataset,
verified 2026-08-02, showing support current through .NET 10 and .NET
Framework 1.1 onward). Decades of Windows Forms and classic ASP.NET
line-of-business applications were built with `DataSet` bound directly to
grid controls.

**JDBC `CachedRowSet` (JSR 114, part of `java.sql.rowset`).** Ships as a
standard interface in the Java SE platform's `java.sql.rowset` module, with
its own javadoc stating it is "a container for rows of data that caches its
rows in memory, which makes it possible to operate without always being
connected to its data source" (Oracle, "CachedRowSet Interface, Java SE 21",
https://docs.oracle.com/en/java/javase/21/docs/api/java.sql.rowset/javax/sql/rowset/CachedRowSet.html,
verified 2026-08-02).

**Microsoft ActiveX Data Objects (ADO) `Recordset` object.** The original
disconnected-recordset implementation, used extensively in classic ASP and
Visual Basic 6 applications, and cited directly in Fowler's own pattern entry
as the example he had in mind when documenting Record Set (Martin Fowler,
"Record Set", https://martinfowler.com/eaaCatalog/recordSet.html, verified
2026-08-02).

**PHP PDO's array-based result materialisation.** `PDOStatement::fetchAll()`
is the read-only, un-typed variant of the pattern shipped in PHP's standard
database extension since PHP 5.1, still current in PHP 8, returning the
entire result set as an in-memory array in one call rather than requiring the
caller to keep the statement cursor open (PHP Documentation Group,
`PDOStatement::fetchAll`, https://www.php.net/manual/en/pdostatement.fetchall.php,
verified 2026-08-02).

## 10. Consequences

Positive.

- A UI grid, a spreadsheet-like editor, or a reporting tool can bind directly
  to the table's columns with no hand-written mapping code, which is the
  pattern's largest single productivity win for data-entry-heavy
  applications.
- The database connection is held only briefly, at fetch and at write-back,
  rather than for the whole span of a user's editing session, which is
  friendlier to connection pool exhaustion than a long-lived open cursor.
- Change tracking at the row level means only the rows that actually changed
  are sent back to the database, without the caller having to compute a diff
  by hand.
- The disconnected shape is naturally serializable, which made it a
  reasonable payload across process and machine boundaries before REST and
  JSON became the default choice for that job.
- Little to no mapping code is needed between the query and the in-memory
  representation, because the table's schema is derived directly from the
  query's result metadata.

Negative.

- The whole result set lives in memory for as long as the table is held,
  which does not scale past a size that is reasonable for one process to
  hold, and gives no natural mechanism for paging a very large query.
- There is no home for domain logic. Validation and business rules end up
  either duplicated at every call site or wired as fragile event handlers on
  the table, and the pattern actively discourages building a richer object
  model on top, because doing so defeats the reason the pattern was chosen.
- Column access by string name or numeric ordinal defers all schema errors
  to runtime, in every language shown in the code examples, unlike a typed
  Data Transfer Object where the compiler catches a renamed field.
- Reconciliation logic, where it exists, typically assumes single-table,
  single-row-key updates, and needs real engineering effort to handle
  multi-table transactional writes correctly.
- The pattern couples calling code directly to the shape of the SQL query
  that produced the table. A join added or removed, or a column renamed in
  the query, silently breaks every consumer that reads that column by name,
  with no compiler warning.

## 11. Failure modes and misuse

**Lost update under optimistic concurrency.** Symptom. Two users open the
same row, one saves, the second save silently overwrites the first user's
change with stale data, or throws a `DBConcurrencyException` (ADO.NET) that
the application swallows and retries blindly. Cause. The reconciler compares
the row's original values against the database's current values before
writing, and when a caller either disables that check or does not implement
it in a hand-rolled Record Set, the second write proceeds without detecting
the conflict. Fix. Enable and handle the built-in concurrency check (ADO.NET
`DataAdapter.Update` compares `RowState` original values by default when the
generated UPDATE includes all original column values in its WHERE clause),
or add a version or timestamp column and check it explicitly in a hand-rolled
implementation.

**Out-of-memory from an unbounded query.** Symptom. The process hosting the
Record Set crashes or is OOM-killed under production data volumes that never
appeared in a test environment seeded with a few hundred rows. Cause. The
whole result set materialises into memory in one `Fill` call, with no paging.
Fix. Page the query with explicit LIMIT and OFFSET (or the platform's
equivalent), and fetch successive pages into fresh, smaller Record Sets
rather than one unbounded one.

**Business logic smeared across event handlers.** Symptom. A validation rule
that should apply in exactly one place is duplicated, inconsistently, in a
grid's cell-changed handler, in a save-button click handler, and again on the
server after write-back, and the three copies drift out of sync over time.
Cause. The Record Set has no natural place to put domain behaviour, so each
consumer re-implements the rule locally. Fix. Extract the rule into a single
shared validator called from every entry point, or, if the amount of logic
has grown past what event handlers can reasonably carry, migrate the layer
holding that logic to a Domain Model and keep Record Set only at the true
data-source boundary.

**Silent truncation or type coercion on write-back.** Symptom. A save
succeeds with no error, but the value that lands in the database differs
from what the user typed, for example a decimal silently rounded, or a
string silently truncated to a column's maximum length. Cause. The Record
Set's column typing is looser than the database column's actual constraint,
and the reconciler does not validate against the destination schema before
issuing the write. Fix. Populate column metadata (type, length, precision)
from the database schema at fetch time, and validate new or modified values
against that metadata before allowing `AcceptChanges` or the equivalent to
proceed.

**Column-name typo caught only in production.** Symptom. `table.Rows[i]["Custmer_ID"]`
throws or silently returns null at runtime, weeks after the code shipped,
because a column was renamed or a query was edited and one call site was
missed. Cause. Column access is by string, resolved at runtime, in every one
of the implementations in dimension 9. Fix. Wrap column access behind a
strongly-typed accessor generated from the schema (ADO.NET's typed
`DataSet` designer generates exactly this), or add a startup-time schema
assertion that checks every column name the application expects actually
exists in the fetched table.

**Reconciler regenerates SQL for unchanged rows.** Symptom. A save operation
that should touch three rows instead issues an UPDATE for every row in the
table, and audit logs or triggers on the table fire far more often than the
actual edit count. Cause. The reconciler is called against the full table
rather than the filtered set of changed rows, either because `GetChanges()`
or its equivalent was skipped, or because a hand-rolled implementation never
tracked row state correctly. Fix. Always reconcile from the filtered changed
set, and add a test asserting that saving an untouched table issues zero
writes.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Record Set | Row Data Gateway | Table Data Gateway | Data Transfer Object over a Domain Model | Streaming ResultSet / cursor |
|---|---|---|---|---|---|
| Setup cost for a simple grid-bound screen | Very low, native binding | Medium, need a row object per query shape | Medium, need a gateway per table | High, need a domain model plus a mapper plus a DTO | Low, but no binding support |
| Home for business logic | None, logic lives outside the table | Weak, one row object per record but usually thin | None, gateway is data access only | Strong, the domain model is exactly this home | None |
| Memory footprint for large results | High, whole result held in memory | Proportional to rows fetched, but caller controls fetch size | Proportional to rows fetched | Proportional to rows mapped | Low, one row in flight at a time |
| Change tracking for write-back | Built in, per-row state | Manual, caller tracks what changed | Manual, caller writes explicit SQL | Manual or via a Unit of Work | Not applicable, cursor is typically read-only in this use |
| Serializable across process boundary | Yes, by design | Depends on the row object | Not applicable, gateway holds no data | Yes, that is the DTO's job | No, a live cursor cannot cross a boundary |
| Compile-time schema safety | None, string or ordinal column access | Strong, the row object's fields are typed | Strong, gateway methods are typed | Strong, the DTO's fields are typed | Depends on the driver's typed row mapping |
| Connection lifetime | Short, open only at fetch and write-back | Short, one fetch per row or batch | Short, one call per operation | Short, mapping happens after the fetch closes | Long, held open for the duration of iteration |
| Fit for a UI data-binding toolkit | Excellent, purpose-built for this | Poor, needs adapter code | Poor, needs adapter code | Fair, needs a view-model layer in between | Poor, no in-memory structure to bind to |

Reading of the table. Record Set wins decisively when the consumer is a
data-binding UI toolkit and the data has little business logic. Row Data
Gateway and Table Data Gateway win when the team wants typed, testable data
access without committing to a full Record Set container. A Domain Model
plus Data Transfer Object wins once real business rules exist. A streaming
cursor wins when the result set is too large to hold in memory at all.

## 13. Related and incompatible patterns

- **Table Data Gateway and Row Data Gateway.** Sibling Data Source
  Architectural Patterns from the same chapter of Fowler's catalog. Where a
  Record Set is a generic, schema-derived container that any query can fill,
  a Table Data Gateway or Row Data Gateway is a hand-written class specific
  to one table, offering typed access and a natural place for
  table-specific query methods. A codebase sometimes uses a Table Data
  Gateway's `findAll` method to run the query and returns the result as a
  Record Set, combining the two.
- **Data Transfer Object.** A frequent substitute rather than a companion. A
  DTO is a typed, purpose-built shape carrying exactly the fields a specific
  call needs, with compile-time safety Record Set cannot offer. Many
  systems that outgrow a Record Set migrate to mapping query results into
  DTOs as the first step away from the pattern, see dimension 14.
- **Data Mapper and Domain Model.** The pattern this one is chosen instead
  of, whenever the application needs real business logic against the data.
  A Domain Model is Fowler's own answer to the case where Record Set's lack
  of a home for behaviour becomes a liability, and migrating from one to the
  other is the most common refactoring path away from Record Set in a
  growing application.
- **Unit of Work.** Where Record Set's built-in row-state tracking handles
  change tracking for one table or one connected set of tables, a Unit of
  Work generalises the same idea, tracking changes across an entire object
  graph spanning many tables and coordinating a single transactional commit.
  A large system sometimes uses a Unit of Work at the domain layer and a
  Record Set only at the thin data-access boundary feeding it.
- **Optimistic Offline Lock.** Composes directly with Record Set's
  reconciliation step. The row-state comparison against original values that
  a well-built reconciler performs before writing back is a concrete
  instance of Optimistic Offline Lock, and the lost-update failure in
  dimension 11 is exactly what happens when that lock is missing or
  disabled.
- **Domain Model, as an incompatible pairing rather than a related one.**
  Mixing a Record Set-based data-access layer directly into a codebase that
  otherwise expresses business rules through a rich Domain Model produces
  two competing representations of the same data, and forces every new
  developer to learn which layer's vocabulary a given method uses. The two
  patterns are not composable at the same layer of a single feature, one is
  chosen instead of the other for that feature.

## 14. Refactoring path in and out

Introducing the pattern into code that currently iterates a live cursor.

1. Identify the query whose result is currently consumed by iterating an
   open `ResultSet` or cursor directly, and confirm the consumer needs the
   whole result available for editing or binding, not a one-pass read.
2. Introduce a table structure that owns column metadata derived from the
   query's result metadata, and a fill step that reads every row from the
   cursor into that structure, then closes the cursor.
3. Change the consumer to read from the new table structure instead of the
   live cursor. Run the tests. The connection lifetime should now be
   measured in milliseconds rather than the span of the UI interaction.
4. Add row-state tracking (added, modified, deleted) if the consumer needs
   to write changes back, starting with the smallest surface, a single
   table, a single primary key column.
5. Add a reconciler that walks only the changed rows and issues the
   corresponding writes, guarded by an optimistic-concurrency check against
   original values.
6. Where the platform ships a native Record Set implementation, for example
   ADO.NET's `DataAdapter.Fill` and `Update`, prefer it over the hand-rolled
   version from steps 2 through 5, since it has already hardened the
   concurrency and type-coercion edge cases described in dimension 11.

Removing the pattern when it stops earning its place. The signal is usually
that business logic has accumulated around the table faster than the team
is comfortable with, or that a public API needs to expose the data in a
platform-neutral shape.

1. Confirm what actual behaviour, beyond simple field validation, has
   accumulated in event handlers or call sites around the Record Set. List
   it. This list becomes the seed of the domain object's methods.
2. Introduce a typed object, or a Data Transfer Object if the destination is
   a Domain Model layer that already exists, with one field per column the
   consumer actually reads.
3. Add a mapping step immediately after the fill, converting each row into
   an instance of the new typed object, and change the consumer to work
   against the typed objects rather than the table's rows.
4. Move the behaviour identified in step 1 onto the new typed object, one
   piece at a time, deleting the duplicate copies at each old call site as
   its logic moves.
5. Once every consumer reads the typed objects, delete the Record Set fill
   step and have the mapping happen directly from the query result, closing
   the pattern out entirely. Cross-reference Replace Data Value with Object,
   in the refactoring family, for the mechanics of step 2 and 3.

## 15. Testing and verification

Easier because of the pattern.

- A test can construct a table in memory, with no database connection at
  all, populate it with rows by hand, and pass it to whatever code consumes
  it, exercising UI-binding or business logic against a fully controlled
  in-memory fixture.
- Change tracking can be asserted directly. Set a value, assert the row's
  state flipped to modified, call `AcceptChanges`, assert it flipped back to
  unchanged, all without touching a real database.
- Reconciliation logic can be tested against a table pre-populated with a
  known mix of added, modified, deleted, and unchanged rows, asserting the
  exact set of INSERT, UPDATE, and DELETE statements generated, without a
  live connection.

Harder because of the pattern.

- Because column access is by string or ordinal, a test that misspells a
  column name passes at compile time and fails only when the assertion runs,
  which weakens the safety net a typed object would otherwise give the test
  suite itself.
- Testing that the reconciler correctly detects an optimistic-concurrency
  conflict requires simulating a second writer between fetch and write-back,
  which needs either two real connections against a shared row or careful
  mocking of the underlying database call, since the Record Set itself
  carries no notion of a second party.
- Schema drift between the query and the code under test is invisible until
  a real database is involved, since a hand-built in-memory fixture will
  happily carry a column that the real query no longer produces.

Techniques that apply.

- **Schema-assertion test.** On application startup or in a dedicated
  integration test, fetch the real query once and assert that every column
  name the code expects to read is present in the returned schema. This
  catches the column-typo failure from dimension 11 well before production.
- **Fixture-builder helper.** A small test helper that builds a populated
  table from a plain list of dictionaries or tuples, so that individual
  tests do not repeat the column-definition boilerplate. This is the
  in-memory analogue of an Object Mother for domain objects.
- **Round-trip reconciliation test against a real or containerised
  database.** Fill a table from a real fixture, mutate rows in every state
  (add, modify, delete), reconcile, then re-fill from the database and
  assert the final state matches what was intended. This is the one part of
  the pattern that genuinely benefits from an integration test rather than a
  pure unit test, because the SQL generation and the concurrency check are
  the riskiest part of the pattern.

## 16. Observability signals

Judgement. The following is drawn from operating data-binding applications
in production, not from a single cited source, and is stated as reasoning
rather than fact.

What to record.

- The row count fetched per query, and the elapsed time of the fill step,
  labelled by the query or screen that triggered it. This is the earliest
  signal of the unbounded-query failure mode from dimension 11, since row
  count creeping upward over weeks or months is visible long before it
  causes an outage.
- The count of rows in each state (added, modified, deleted) at the moment
  a reconcile is attempted, and the count of rows actually affected by the
  generated writes. A mismatch between the two, more rows attempted than
  affected, is the direct symptom of a lost-update or a concurrency conflict
  that the application swallowed.
- The rate of optimistic-concurrency exceptions or conflict responses from
  the reconciler, labelled by table or screen. A healthy system sees this
  near zero. A rising rate points either at a genuinely contended row
  (several users editing the same record) or at a UI flow that lets a user
  hold a Record Set open far longer than intended.
- Memory used by any long-lived Record Set instances held in a session or
  cache, since these are the instances most likely to grow unbounded over a
  session's lifetime.

A healthy instance on a dashboard. Fill duration and row count are flat and
proportional to the screen's expected data volume. The reconciliation
attempted-versus-affected counts match almost exactly. Concurrency conflicts
are rare and correlate with genuinely shared records, not with a single
user's normal workflow.

A failing instance. Row counts per fill trend upward with no corresponding
change in the underlying business volume, which is the unbounded-query
failure developing quietly. Reconciliation attempted counts consistently
exceed affected counts, which means writes are silently failing to match
rows, most often because the original values used in the WHERE clause no
longer match the database, itself a symptom of either the lost-update
failure or a schema drift the fill step did not pick up. A sudden spike in
memory tied to session count, rather than to request rate, points at
Record Sets being held in session state far longer than the user's actual
editing window.

## 17. Security and privacy implications

**Whole-row exposure by default.** A Record Set typically fetches and holds
every column the underlying query selects, and a UI grid bound to it will
happily render every one of those columns unless explicitly configured
otherwise. A query written for one purpose that happens to select a
sensitive column, a salary, a national identifier, a raw password hash left
over from a migration, exposes that column to whatever the Record Set is
eventually bound or serialized to, with no per-field access control built
into the pattern. Select only the columns the consumer is actually meant to
see, and treat the query itself as the access-control boundary, since the
Record Set enforces none.

**Serialization as a data-exfiltration surface.** Because Record Set
implementations are designed to serialize (ADO.NET `DataSet` to XML,
`CachedRowSet` to Java serialization), a Record Set that is accidentally
logged, cached, or written to a diagnostic dump captures the full contents
of the query result, including any sensitive columns, in a durable form that
outlives the original request. Exclude Record Set objects from generic
exception-logging or diagnostic-dump mechanisms, or scrub sensitive columns
before the object is allowed to serialize.

**SQL injection risk shifts, it does not disappear.** The pattern itself
says nothing about how the originating query is built. A Record Set filled
from a query that concatenates untrusted input is exactly as vulnerable to
SQL injection as any other data-access approach, and the disconnected,
tabular nature of the result gives a reviewer no visual cue that the
underlying query might be unsafe. Build the query with parameterisation
regardless of what consumes its result.

**Reconciliation as a write-side injection surface.** A hand-rolled
reconciler that builds UPDATE or DELETE statements by concatenating column
names or values taken from the Record Set's own schema or row data,
particularly in a dynamically typed implementation where column names come
from user-controlled configuration, reopens the same injection risk on the
write path. Platform-native reconcilers (ADO.NET `DataAdapter`, JDBC
`CachedRowSet.acceptChanges`) parameterise generated statements correctly by
default, but a custom reconciler must be held to the same standard.

## 18. References

1. Martin Fowler. *Patterns of Enterprise Application Architecture*.
   Addison-Wesley, 2002. ISBN 0-321-12742-0. Chapter 18, "Data Source
   Architectural Patterns", section "Record Set". Source of the pattern name,
   the intent, and the identification of ADO Recordset as the motivating
   example.
2. Martin Fowler. "Record Set". martinfowler.com.
   https://martinfowler.com/eaaCatalog/recordSet.html
   Verified 2026-08-02. Source of the pattern's intent statement and the
   ADO Recordset attribution.
3. Microsoft. ".NET API browser, DataSet Class".
   https://learn.microsoft.com/en-us/dotnet/api/system.data.dataset
   Verified 2026-08-02. Source for the ADO.NET DataSet production use and
   its disconnected, in-memory-cache description.
4. Microsoft. ".NET API browser, DataRelationCollection Class".
   https://learn.microsoft.com/en-us/dotnet/api/system.data.datarelationcollection
   Verified 2026-08-02. Source for the multi-table, related-tables variant
   in dimension 8.
5. Oracle. "CachedRowSet Interface", Java SE 21 & JDK 21 java.sql.rowset
   module documentation.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.sql.rowset/javax/sql/rowset/CachedRowSet.html
   Verified 2026-08-02. Source for the CachedRowSet production use, and the
   direct quotation describing it as a disconnected rowset that caches its
   rows in memory.
6. PHP Documentation Group. `PDOStatement::fetchAll`.
   https://www.php.net/manual/en/pdostatement.fetchall.php
   Verified 2026-08-02. Source for the PHP PDO read-only, array-based
   production use in dimensions 8 and 9.

## Code examples

Three platforms where the pattern is genuinely native, shown in three
different languages so the shape of the idea, not one API's syntax, is
visible. C# shows ADO.NET's `DataTable`, the most complete built-in
implementation. Python shows a minimal hand-rolled version with row-state
tracking, since Python has no standard Record Set type and this is closer to
how the pattern actually gets built there. Go is included as a
reconciliation-focused example built on `database/sql`, since Go also has no
standard Record Set type and the idiomatic shape is a small struct plus
explicit change tracking rather than a generic container.

### C#

```csharp
using System;
using System.Data;

class RecordSetDemo
{
    static void Main()
    {
        var table = new DataTable("Product");
        table.Columns.Add("Id", typeof(int));
        table.Columns.Add("Name", typeof(string));
        table.Columns.Add("Price", typeof(decimal));
        table.PrimaryKey = new[] { table.Columns["Id"] };

        // Simulate a fill from a query result, connection is closed after this.
        table.Rows.Add(1, "Widget", 9.99m);
        table.Rows.Add(2, "Gadget", 19.99m);
        table.AcceptChanges();

        // Disconnected editing. No connection is open here.
        table.Rows.Find(1)["Price"] = 12.49m;
        var newRow = table.NewRow();
        newRow["Id"] = 3;
        newRow["Name"] = "Gizmo";
        newRow["Price"] = 5.49m;
        table.Rows.Add(newRow);

        DataTable changes = table.GetChanges();
        Console.WriteLine($"Rows to reconcile: {changes?.Rows.Count ?? 0}");
        foreach (DataRow row in changes.Rows)
        {
            Console.WriteLine($"  {row.RowState}: {row["Id"]} {row["Name"]} {row["Price"]}");
        }

        table.AcceptChanges();
        Console.WriteLine($"Rows to reconcile after accept: {table.GetChanges()?.Rows.Count ?? 0}");
    }
}
```

### Python

```python
from dataclasses import dataclass, field
from enum import Enum, auto


class RowState(Enum):
    UNCHANGED = auto()
    ADDED = auto()
    MODIFIED = auto()
    DELETED = auto()


@dataclass
class Row:
    values: dict
    original: dict = None
    state: RowState = RowState.UNCHANGED

    def __post_init__(self):
        if self.original is None:
            self.original = dict(self.values)

    def set(self, column: str, value):
        self.values[column] = value
        if self.state == RowState.UNCHANGED:
            self.state = RowState.MODIFIED


class Table:
    def __init__(self, columns: list[str]):
        self.columns = columns
        self.rows: list[Row] = []

    def add_from_source(self, **values) -> Row:
        row = Row(values=dict(values))
        self.rows.append(row)
        return row

    def new_row(self, **values) -> Row:
        row = Row(values=dict(values), original={}, state=RowState.ADDED)
        self.rows.append(row)
        return row

    def mark_deleted(self, row: Row):
        row.state = RowState.DELETED

    def changes(self) -> list[Row]:
        return [r for r in self.rows if r.state != RowState.UNCHANGED]

    def accept_changes(self):
        self.rows = [r for r in self.rows if r.state != RowState.DELETED]
        for r in self.rows:
            r.original = dict(r.values)
            r.state = RowState.UNCHANGED


if __name__ == "__main__":
    table = Table(columns=["id", "name", "price"])
    r1 = table.add_from_source(id=1, name="Widget", price=9.99)
    table.add_from_source(id=2, name="Gadget", price=19.99)
    table.accept_changes()

    r1.set("price", 12.49)
    table.new_row(id=3, name="Gizmo", price=5.49)

    for row in table.changes():
        print(row.state, row.values)

    table.accept_changes()
    print("changes after accept:", len(table.changes()))
```

### Go

```go
package main

import "fmt"

type RowState int

const (
	Unchanged RowState = iota
	Added
	Modified
	Deleted
)

type Row struct {
	Values   map[string]any
	Original map[string]any
	State    RowState
}

func NewSourceRow(values map[string]any) *Row {
	orig := make(map[string]any, len(values))
	for k, v := range values {
		orig[k] = v
	}
	return &Row{Values: values, Original: orig, State: Unchanged}
}

func (r *Row) Set(column string, value any) {
	r.Values[column] = value
	if r.State == Unchanged {
		r.State = Modified
	}
}

type Table struct {
	Columns []string
	Rows    []*Row
}

func (t *Table) NewRow(values map[string]any) *Row {
	r := &Row{Values: values, Original: map[string]any{}, State: Added}
	t.Rows = append(t.Rows, r)
	return r
}

func (t *Table) Changes() []*Row {
	var out []*Row
	for _, r := range t.Rows {
		if r.State != Unchanged {
			out = append(out, r)
		}
	}
	return out
}

func (t *Table) AcceptChanges() {
	kept := t.Rows[:0]
	for _, r := range t.Rows {
		if r.State == Deleted {
			continue
		}
		r.Original = map[string]any{}
		for k, v := range r.Values {
			r.Original[k] = v
		}
		r.State = Unchanged
		kept = append(kept, r)
	}
	t.Rows = kept
}

func main() {
	table := &Table{Columns: []string{"id", "name", "price"}}
	r1 := NewSourceRow(map[string]any{"id": 1, "name": "Widget", "price": 9.99})
	r2 := NewSourceRow(map[string]any{"id": 2, "name": "Gadget", "price": 19.99})
	table.Rows = append(table.Rows, r1, r2)
	table.AcceptChanges()

	r1.Set("price", 12.49)
	table.NewRow(map[string]any{"id": 3, "name": "Gizmo", "price": 5.49})

	for _, row := range table.Changes() {
		fmt.Println(row.State, row.Values)
	}

	table.AcceptChanges()
	fmt.Println("changes after accept:", len(table.Changes()))
}
```
