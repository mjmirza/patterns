---
name: Serialized LOB
slug: serialized-lob
family: 06-poeaa
category: Object-Relational Structural
aliases: [Serialized Large Object, Blob Serialization, Object Graph Serialization]
first_described: "Fowler 2002"
maturity: established
related: [memento, single-table-inheritance, class-table-inheritance, lazy-load, embedded-value]
incompatible_with: [class-table-inheritance, query-object]
verified: 2026-08-02
---

# Serialized LOB

## 1. Name, aliases, and lineage

The canonical name is Serialized LOB, where LOB stands for Large Object, the
generic database term for a column that can hold a large binary or character
payload, most commonly a BLOB (Binary Large Object) or CLOB (Character Large
Object). Martin Fowler first described it in *Patterns of Enterprise
Application Architecture* (Addison-Wesley, 2002), in the chapter on
Object-Relational Structural Patterns, as one of a family of patterns that
answer the question of how an in-memory object graph gets mapped onto a
relational schema. The pattern is also referred to informally as Blob
Serialization or Object Graph Serialization in practitioner writing, though
those are descriptive labels rather than names with their own independent
lineage. Fowler's own catalog page states the definition plainly, saying it
"saves a graph of objects by serializing them into a single large object
(LOB), which it stores in a database field" (Martin Fowler, "Serialized
LOB", https://martinfowler.com/eaaCatalog/serializedLOB.html, verified
2026-08-02). The pattern has a close conceptual sibling from the Gang of Four
catalog, Memento, and Fowler explicitly draws that comparison. Serialized LOB
behaves like a database-backed Memento for an entire object subgraph,
capturing and restoring the internal state of a set of related objects
without those objects needing to expose that state to any other
collaborator.

## 2. Problem and context

Object models are good at representing composite structures. A department
has child departments, an employee reports to a manager who reports to
another manager, a document has sections that have paragraphs that have runs
of formatted text. In memory this is naturally a tree or a graph, and code
that walks it is straightforward recursive traversal. The relational model
has no native concept of a composite structure. A tree becomes a table with
a self-referencing foreign key, or a set of tables joined by foreign keys at
every level, and reading the whole tree back out requires either a recursive
common table expression, a fixed number of joins bounded by the maximum
depth, or N+1 individual queries walking down one level at a time.

For a shallow structure with a handful of rows this cost is invisible. For a
genuinely deep or wide hierarchy, and especially for one that is read and
written as a single unit rather than queried piece by piece, the join cost
becomes the dominant expense of the operation, and the object-relational
mapping code needed to reconstruct the tree from flattened rows becomes a
disproportionate share of the persistence layer. The problem Serialized LOB
answers is narrower than the general question of how to map a hierarchy to a
database. It answers the more specific question of how to map a hierarchy
that is always read and written whole, and never queried by its internal
structure, without paying join cost on every access. The context that makes
the pattern make sense is a structure whose contents are opaque to SQL.
Nobody writes a query that asks for every employee two levels below a
department, in the department that has this Serialized LOB department
subtree, because if they did the pattern would immediately become the wrong
choice.

## 3. Forces

Four forces pull against each other here, and a reader should notice that the
pattern makes a deliberate, sometimes uncomfortable trade among them rather
than resolving all four cleanly.

**Read and write cost versus query cost.** Serializing the whole graph into
one field turns an N-join read into a single-row read, and turns an N-row
transactional write into a single-row write. Every join eliminated is a
respectable amount of round-trip latency and lock contention saved,
particularly over a network-attached database. The cost lands on query cost.
Nothing inside the serialized blob is visible to SQL. A `WHERE` clause cannot
filter on a field two levels deep in the graph, an index cannot be built on
it, and an aggregate cannot sum across it, unless the database offers a
native document type with query support layered on top of a large-object
column, which is a different and more capable animal than a plain BLOB or
CLOB.

**Coupling to a serialization format versus schema flexibility.** The blob is
opaque to the schema, which means adding a field inside the graph never
requires a migration on the relational side. That flexibility is bought by
tightly coupling every reader of that column to one serialization format and,
in binary formats, one serializer version. A schema change inside the object
graph is now a data migration problem hidden inside application code instead
of a visible `ALTER TABLE`, and it is invisible to anyone inspecting the
database with a SQL client.

**Consistency granularity versus concurrent access.** Because the whole graph
lives in one row, one row-level lock protects the whole tree during a write,
which gives natural all-or-nothing consistency for the subgraph. The cost is
that granularity is now coarse. Two processes that each want to modify a
different branch of the same tree must serialize against each other at the
row level, where a normalized schema would have let them lock two different
child rows independently.

**Operability and inspectability versus storage compactness.** A serialized
blob, particularly a binary one, is opaque to `SELECT *`, to ad hoc reporting
tools, to database backup diffing, and to a DBA doing incident triage at 3 AM
without the application's own reconstruction code at hand. A normalized
schema is self-describing by comparison. The pattern trades that operational
transparency for a compact single-field representation and, often, a smaller
storage footprint than the equivalent set of normalized rows with their
foreign keys and per-row overhead.

## 4. Applicability and non-applicability

Reach for Serialized LOB when the following hold.

- The object graph is a private structure that is always loaded and saved as
  a single unit, never partially. A department tree that is only ever read to
  render an org chart and only ever written back as a whole edited tree is a
  fit.
- Nothing outside the owning object ever needs to query into the internals of
  the graph with SQL. If reporting, analytics, or a second application need
  to filter on a field two levels deep, the pattern is fighting the
  requirement.
- The graph shape is variable or extensible in ways that would otherwise
  cause frequent schema migrations, for example a plugin system where
  different installations attach different optional sub-objects to a parent
  record.
- The relational alternative genuinely would be expensive to query, meaning a
  tree that is deep, or wide, or accessed with high frequency relative to the
  cost of assembling it from joins.
- The consuming application controls both the writer and the reader of the
  field, so the serialization format's evolution can be governed centrally.

Avoid Serialized LOB when the following hold.

- Any part of the graph needs to participate in a relational query, a report,
  a foreign key constraint, or a join from another table. Once one field two
  levels in needs a `WHERE` clause, the blob has to be loaded whole and
  rebuilt only to reach it, defeating the reason it existed.
- The graph is shared or edited concurrently by independent processes at a
  sub-object granularity. Two services that each edit a different child of
  the same tree will serialize against each other unnecessarily and are
  better served by normalized rows with their own locks.
- Long-term data longevity across format or schema changes to the objects is
  a requirement, and there is no plan for versioning the serialized format. A
  binary serializer tied to one language runtime's class layout is a known
  trap here, discussed in dimension 11.
- The database itself now offers a native structured large-object type with
  indexing and query support over its contents, such as a JSON or JSONB
  column with expression indexes. In that case the applicable pattern is
  closer to Embedded Value or a document-store-backed representation than a
  plain Serialized LOB, because the database can see inside the field.
- Auditability by a human with a plain SQL client is a hard requirement, for
  example for compliance review of individual data points, and there is no
  companion audit or reporting path that already handles that need outside
  the blob.

## 5. Structure

The pattern has three participants.

The Owner is the persistent object or aggregate root whose table carries the
LOB column. It is the thing that has an identity in the relational schema, is
looked up by primary key, and is the unit that a `SELECT` or `UPDATE`
naturally targets.

The Object Graph is the in-memory structure being persisted, a tree or a
general graph of plain domain objects related to each other by ordinary
object references. It has no independent existence in the relational schema.
It exists only as the reconstructed form of the LOB column's content, and it
is never assigned relational identity of its own.

The Serializer is the piece of logic, sometimes a library, sometimes hand
written, that converts the Object Graph to a byte or character stream on
write and rebuilds it on read. It owns the format decision, whether that
is a binary serialization protocol, XML, JSON, or a custom encoding, and it
owns the versioning strategy that lets old serialized data remain readable
after the object graph's shape changes.

The relationship is that the Owner holds a reference to the root of the
Object Graph in memory, and the Owner's persistence code calls the Serializer
to convert that graph to and from the single LOB column value that the
Owner's row carries.

## 6. ASCII structure diagram

```
+-------------------+          +----------------------+
|   Owner (row)      |          |   Object Graph        |
|-------------------|          |----------------------|
| id (PK)           |          | root node             |
| name              |          |  |-- child node        |
| lob_data  <-------|----------|--  |-- grandchild node  |
| (BLOB/CLOB column)|  read/   |  |-- child node         |
+-------------------+  build   |     |-- grandchild node |
         ^             |       +----------------------+
         |             v
         |     +----------------+
         +---- |   Serializer    |
   read/write  |----------------|
               | serialize(root)|
               | rebuild(bytes) |
               +----------------+
```

## 7. Dynamics

On write, the Owner's persistence code asks the Serializer to convert the
current in-memory Object Graph, starting from its root, into a stream. The
Serializer walks the graph, following object references, and produces one
contiguous representation. That representation is assigned to the Owner's LOB
column as an ordinary field value, and the Owner's row is written with one
`INSERT` or `UPDATE` statement, exactly as if the LOB field were a plain
string or byte array column, because to the SQL layer it is. No additional
statements are issued for the internal nodes of the graph.

```
Application       Owner            Serializer         Database
    |               |                   |                  |
    | save(owner)   |                   |                  |
    |-------------->|                   |                  |
    |               | serialize(graph)  |                  |
    |               |------------------>|                  |
    |               |   byte stream      |                 |
    |               |<------------------|                  |
    |               |         UPDATE owners SET lob=? ...   |
    |               |--------------------------------------->
    |               |                   |          OK        |
    |               |<---------------------------------------|
    | ack           |                   |                  |
    |<--------------|                   |                  |
```

On read, the Owner's row is fetched with a single `SELECT` by primary key,
returning the LOB column value alongside the Owner's other scalar fields. The
Serializer then rebuilds that value back into the full Object Graph in
memory, in one pass, before the Owner is considered fully loaded and handed
back to the caller. The graph exists nowhere in the database as separate rows
during this round trip. It exists only inside the Owner's LOB field, in its
serialized form, and inside application memory, as a live graph.

```
Application       Owner            Serializer         Database
    |               |                   |                  |
    | find(id)      |                   |                  |
    |-------------->|                   |                  |
    |               |          SELECT * FROM owners WHERE id=? |
    |               |--------------------------------------->
    |               |            row incl. lob bytes           |
    |               |<---------------------------------------|
    |               | rebuild(bytes)    |                  |
    |               |------------------>|                  |
    |               |   full graph       |                 |
    |               |<------------------|                  |
    | owner+graph   |                   |                  |
    |<--------------|                   |                  |
```

## 8. Implementation variants

**Native binary serialization.** The host language's built-in object
serialization mechanism, for example Java's `Serializable` interface and
`ObjectOutputStream`, or Python's `pickle`, writes the graph's exact runtime
class layout to bytes. This is the least code to write and the fastest to
implement, but it is the most fragile. The byte format is tied to the class
version and, in several ecosystems, to the exact language runtime, so a class
field rename or reorder can make previously stored data unreadable. It is
generally the weakest choice for anything that must outlive a single
deployment of the code that wrote it.

**Text-based structured serialization.** XML or JSON representations of the
graph, written by a general-purpose or hand-rolled writer, trade some size
and a small amount of parse cost for human readability and, importantly,
forward and backward compatibility that is much easier to reason about,
because a text format can tolerate an unrecognized field far more gracefully
than a binary layout can. Fowler's own worked example in the book is exactly
this. It serializes a department hierarchy as XML into a Java string column.
This is the variant most commonly reached for today, because JSON in
particular is well supported by every mainstream language's standard library
or a near-ubiquitous third-party library, and it degrades gracefully as the
graph's shape evolves, so long as the reader is written defensively.

**Custom compact binary format.** A hand-written or schema-driven binary
protocol, such as Protocol Buffers, Avro, or a bespoke format, gives full
control over both size and forward and backward compatibility through
explicit field numbering or a companion schema file, at the cost of a build
step and a codegen or schema-management dependency. This variant is chosen
when the graph is large enough, or written frequently enough, that JSON's
overhead is measurable, and when the team is willing to own schema evolution
discipline in return.

**Database-native semi-structured column.** Where the underlying database
offers a native JSON, JSONB, or XML column type with indexing and query
operators over its contents, such as PostgreSQL's `jsonb` or SQL Server's
`xml` type, the pattern shades toward Embedded Value territory. The column
still holds a serialized graph, but the database can now see inside it for
indexing and querying purposes. This variant weakens the opaque-to-SQL force
from dimension 3 and is worth calling out explicitly, because a team reaching
for Serialized LOB on a modern database frequently ends up here by default
rather than with a genuinely opaque BLOB, and that changes several of the
trade-offs discussed later in this entry.

**Language-idiomatic wrapper.** In languages with strong built-in
serialization support at the ORM boundary, such as Ruby on Rails'
`ActiveRecord::AttributeMethods::Serialization`, the pattern is implemented
declaratively. A single class-level call names the attribute and the coder,
and the framework performs the read and write transparently on every load
and save. This is functionally identical to the manual variant but removes
almost all of the boilerplate, at the cost of making the serialization
decision less visible in the code that actually reads or writes the field.

## 9. Known production uses

**Apache Tomcat's `JDBCStore`**, part of the `PersistentManager` session
persistence mechanism, serializes an entire HTTP session object, including
every attribute a servlet has placed into it, into a single BLOB column of a
configurable session table, so that session state survives a server restart
or can be shared in a cluster without decomposing the session's contents
into individual rows (Apache Tomcat, `org.apache.catalina.session.JDBCStore`
API documentation,
https://tomcat.apache.org/tomcat-8.5-doc/api/org/apache/catalina/session/JDBCStore.html,
verified 2026-08-02).

**ASP.NET's SQL Server session state provider** stores the entire session
dictionary for a request, serialized to a binary form, in the
`SessionItemShort` or `SessionItemLong` `varbinary` columns of the
`ASPStateTempSessions` table, choosing between the two columns purely by
payload size so that small sessions stay in-row for a performance advantage,
while the session's individual key-value entries never become separate rows
(Microsoft Learn, "Session State Providers",
https://learn.microsoft.com/en-us/previous-versions/dotnet/articles/aa478952(v=msdn.10),
verified 2026-08-02).

**Ruby on Rails' `ActiveRecord::AttributeMethods::Serialization`** offers the
`serialize` class method, which marks a model attribute for automatic
write-on-save and rebuild-on-load using a pluggable coder, most commonly YAML
or JSON, so that an arbitrary Ruby object graph attached to a model can be
stored in one text column without a normalized schema for its internals
(Ruby on Rails API documentation,
`ActiveRecord::AttributeMethods::Serialization::ClassMethods`,
https://api.rubyonrails.org/classes/ActiveRecord/AttributeMethods/Serialization/ClassMethods.html,
verified 2026-08-02).

**Hibernate ORM's `@Lob` annotation** marks a persistent Java attribute, such
as a `byte[]` or a `String`, to be mapped to a database BLOB or CLOB column
respectively, giving JPA and Hibernate applications a direct, declarative way
to attach a large serialized payload, commonly an entire serialized object
graph, to an entity row without decomposing that payload into further tables
(Hibernate ORM User Guide, section on basic type mappings for `@Lob`,
https://docs.hibernate.org/orm/6.4/userguide/html_single/Hibernate_User_Guide.html,
verified 2026-08-02).

**Martin Fowler's own worked example**, which is the canonical demonstration
rather than an independently discovered production case, serializes a
department hierarchy to XML and stores it in a single Java `String` column,
illustrating the pattern's shape for a self-referencing tree that would
otherwise require a recursive join to reassemble (Martin Fowler, "Serialized
LOB", https://martinfowler.com/eaaCatalog/serializedLOB.html, verified
2026-08-02, and Martin Fowler, *Patterns of Enterprise Application
Architecture*, Addison-Wesley, 2002, Object-Relational Structural Patterns
chapter).

## 10. Consequences

Positive consequences. Reading or writing the entire graph costs exactly one
row's worth of I/O regardless of the graph's internal size or depth, which
removes join cost and N+1 query risk entirely for that subgraph. The
relational schema stays stable as the internal shape of the graph evolves,
because nothing about a field added deep in the graph requires a migration.
The persistence code for the graph collapses to a write-out step and a
rebuild-on-read step, which is far less object-relational mapping machinery
than a fully normalized hierarchy would need. Consistency for the whole
subgraph is automatic and free. A single row write is atomic, so the graph
can never be observed in a half-written state by another transaction the way
a multi-table write theoretically could without careful transaction
boundaries.

Negative consequences. The graph's contents are invisible to SQL, so no
report, no ad hoc query, no foreign key constraint, and no database-level
index can reach into it, which pushes any future requirement to query by an
internal field into an expensive rewrite. Concurrent modification is
serialized at the whole-row level even when two writers are touching
logically unrelated branches of the tree, which can create contention that a
normalized schema would not have. The application is now coupled to a
serialization format and, in binary variants, a serializer version, so
evolving the object graph's shape requires either a format that tolerates
unknown or missing fields gracefully, or an explicit migration pass over
every stored row, neither of which is free. Operational visibility drops.
Nobody can read the field's meaning from the database schema alone, and
tooling built around row-level diffs, such as many change-data-capture and
audit systems, sees the whole blob change on any edit rather than a
visible field-level delta.

## 11. Failure modes and misuse

**Symptom.** A new report or analytics query is requested against a field
that lives inside the serialized graph, and there is no way to write it in
SQL. **Cause.** The pattern was applied to a structure that looked private at
design time but later gained a genuine cross-cutting query requirement, which
is exactly the scenario dimension 4 warns against. **Fix.** Either extract
the specific field that needs to be queried into a real column alongside the
LOB, duplicating it for query purposes while the LOB remains the source of
truth for the rest of the graph, or migrate the whole structure to a
normalized or document-database representation that a query engine can see
into.

**Symptom.** After a routine deployment, previously stored rows fail to
rebuild, throwing a class-not-found or an incompatible-version error at read
time, in production, for records that were written by an older build.
**Cause.** A binary serialization format, most often a language's native
object serializer, was used without a versioning strategy, and a class field
was renamed, reordered, or removed in a later release, breaking backward
compatibility of the byte layout. **Fix.** Migrate to a text-based or
schema-versioned format that tolerates unknown or missing fields by design,
write an explicit migration script to re-serialize every stored row under
the new class shape before the deployment that changes it, or maintain an
explicit format version tag inside the serialized payload and branch the
read logic on that tag.

**Symptom.** Two services or two background jobs each update a different
branch of the same stored tree and the second writer silently clobbers the
first writer's change, or the application throws a stale-object exception on
every other write under moderate concurrency. **Cause.** The whole graph
shares one row-level lock or one optimistic-concurrency version number, so
edits to logically independent parts of the tree are treated as conflicting
writes to the same resource. **Fix.** Either restructure so that
independently-edited subgraphs get their own LOB rows, or move the
frequently and independently edited portion of the structure out of the blob
into normalized rows that can be locked individually, keeping only the
infrequently-touched remainder inside the Serialized LOB.

**Symptom.** A database backup, a change-data-capture stream, or a DBA
running a diff between two snapshots reports that a row changed on every
edit, with no indication of what actually changed inside it. **Cause.** The
whole graph is stored as one opaque field value, so any change to any part of
the graph, no matter how small, produces a completely different serialized
byte sequence with no field-level granularity visible to tooling operating at
the row or column level. **Fix.** Accept this as an inherent cost of the
pattern and build any needed change-auditing at the application layer, where
the graph's structure is actually visible, rather than expecting row-level
or column-level database tooling to surface it.

## 12. Trade-off matrix

Judgement. The weightings below reflect typical relative costs observed
across the sources cited in this entry and general practitioner experience.
They are not independently benchmarked figures.

| Force | Serialized LOB | Class Table Inheritance | Single Table Inheritance | Embedded Value (structured, e.g. JSONB) |
|---|---|---|---|---|
| Read cost for the whole graph | Lowest, one row | High, one join per level or subtype | Low, one table, no join | Low, one row, native parse |
| Query into internal fields | None, opaque | Full SQL access to every level | Full SQL access | Partial to full, depends on database's expression index support |
| Schema stability as graph shape evolves | High, no migration needed | Low, new subtype needs a new table | Medium, new subtype needs new nullable columns | High to medium, depends on validation strictness |
| Write consistency for the whole subgraph | Atomic by construction | Requires explicit transaction across tables | Atomic, single row | Atomic by construction |
| Concurrent edits to independent sub-parts | Poor, whole-row contention | Good, independent row locks per level | Poor, single row | Poor to fair, depends on database's partial-update support |
| Operational inspectability with plain SQL | Low, opaque blob | High, self-describing schema | Medium, wide table with many nulls | Medium to high, native JSON tooling in most modern databases |

## 13. Related and incompatible patterns

**Memento (Gang of Four).** Serialized LOB is, in Fowler's own framing, a
database-persisted instance of the Memento idea. It captures and later
restores an object's internal state without that object exposing its
internals to unrelated code, except that the memento here is durable and
lives in a database field rather than in memory for the lifetime of an undo
stack.

**Class Table Inheritance and Single Table Inheritance.** Both are
alternative answers to mapping a structured object model onto relational
tables, and both are the patterns most directly displaced when a team
chooses Serialized LOB instead, because all three compete to answer how this
hierarchy lives in the database. A hierarchy that starts life normalized
under Class Table or Single Table Inheritance and later proves to be always
read and written whole, and never queried by its internals, is a reasonable
candidate for refactoring into a Serialized LOB, and the reverse refactoring
is equally reasonable when a query requirement appears against previously
opaque internals, discussed in dimension 14.

**Embedded Value.** Where the target database offers a native, queryable
semi-structured column type, a Serialized LOB implementation naturally drifts
toward Embedded Value, because the field stops being opaque to the database
and starts being a value the database itself can inspect and index parts of.
The two patterns are not identical but sit close enough together that a team
choosing between them should decide explicitly whether they want the
database to see inside the field or not.

**Lazy Load.** A Serialized LOB column is frequently large relative to the
rest of the Owner's row, and Owner objects are frequently loaded in lists
where the graph itself is not needed for every row, for example rendering a
table of department names without their full org-chart contents. Lazy Load
is the natural companion pattern that defers the rebuild step, or even
fetching, of the LOB column until the graph is actually accessed, avoiding
paying that cost for rows where it is wasted.

**Incompatible with Class Table Inheritance and with Query Object.** Once a
structure is committed to a Serialized LOB, it cannot simultaneously be
represented as Class Table Inheritance for the same data, because the two
patterns describe mutually exclusive physical layouts for the same logical
structure. One decomposes into per-level tables, the other collapses into
one opaque field. Similarly, Query Object presumes the ability to build a
SQL query that reaches into the structure being queried. A Serialized LOB's
internals are by definition invisible to that mechanism, so any part of a
structure that needs Query Object support cannot simultaneously live inside
a Serialized LOB.

## 14. Refactoring path in and out

**Introducing the pattern.** Start from a normalized representation that is
paying an unwanted join cost on every read or write of a whole subgraph.
First, confirm the non-applicability list in dimension 4 truly does not
apply, in particular that nothing outside the owning object queries into the
structure's internals with SQL today, and that nothing is realistically
expected to in the near term. Second, choose a serialization format,
generally a text-based one such as JSON unless there is a measured
performance reason to choose otherwise, and write the write-out and
rebuild-on-read functions, keeping them isolated behind the Owner's
persistence boundary so the rest of the application never sees the
serialized form. Third, add the new LOB column to the Owner's table and
write a one-time migration that reads every existing row's normalized child
rows, assembles the in-memory graph exactly as application code already does
when loading it, serializes that graph, and writes it into the new column.
Fourth, switch the Owner's load and save code paths over to the LOB column
and verify against the old normalized tables in parallel for a deployment
cycle before dropping them, so that a mismatch between the two
representations is caught before the old data is gone. Fifth, drop the
now-redundant normalized tables once confidence is established.

**Removing the pattern.** The trigger is almost always a new requirement to
query, join, or index into something that lives inside the blob. First,
determine whether only a small number of fields need to become queryable, in
which case the cheaper move is to duplicate only those fields into real
columns on the Owner's row, written alongside the LOB on every save, leaving
the LOB as the authoritative full representation and the duplicated columns
as a query-only projection. Second, if a genuinely normalized representation
is needed, design the target schema, most often Class Table Inheritance or
Single Table Inheritance depending on how much the subtypes within the graph
diverge, and write a migration that rebuilds every stored LOB value and
inserts the resulting objects as normalized rows. Third, run both
representations in parallel behind a feature flag, writing to both and
reading from the normalized tables once they are verified complete and
correct, before removing the LOB column and its serialization code entirely.

## 15. Testing and verification

What becomes genuinely easy to test is the Serializer's round trip, a pure
function from an in-memory graph to bytes and back, so it can be
unit-tested exhaustively with constructed object graphs, including edge
cases such as an empty graph, a single node with no children, deeply nested
structures near any recursion or size limit the format imposes, and graphs
containing values the format handles awkwardly, such as characters that need
escaping in a text format or floating-point values near a serializer's
precision boundary. Because the Owner's persistence code only ever touches
one field, integration tests against a real or in-memory database reduce to
a single write-then-read assertion per Owner rather than needing to assert
across several joined tables.

What becomes harder to test is any assertion that depends on a specific
internal field of the graph being queryable at the database layer, which
cannot be written as a SQL-level test at all, and must instead load the
whole Owner, rebuild the graph, and assert against the in-memory object,
which is slower and couples the test to the application's object model
rather than to the schema. Backward-compatibility testing becomes an
explicit responsibility rather than something that falls out of ordinary
schema testing. A regression suite for this pattern should keep a small
corpus of previously serialized payloads from earlier versions of the
graph's shape, generated before any field rename or removal, and assert that
the current reader still reads them correctly, because nothing else will
catch a silent backward-compatibility break of the kind described in
dimension 11. Test doubles for the Serializer, a fake that returns a fixed
byte sequence for a given graph and vice versa, are useful for isolating the
Owner's persistence logic from the actual write and rebuild cost during fast
unit tests, with a small number of slower tests exercising the real
Serializer end to end.

## 16. Observability signals

The size in bytes of the serialized value is worth tracking per write,
because unbounded growth of a particular Owner's graph over time, for
example a department tree that only ever gains children and never prunes
them, is invisible in row count metrics but shows up immediately as a
climbing average or maximum LOB size, and is an early warning that the
subgraph is drifting toward a size where the pattern's read and write cost
advantage starts to erode. Failures rebuilding a stored value should be
logged with enough context, such as the Owner's identifier and the
serializer version tag if one exists, to distinguish a genuine data
corruption event from a backward-compatibility break of the kind described
in dimension 11, because the two require very different remediation. The
time spent rebuilding a graph from its stored bytes, measured separately
from the database round trip that fetches the row, is a useful signal for
catching the moment a binary or text format's read cost starts to matter,
particularly after the graph size has been growing for a while, and it is a
metric that a query-cost dashboard focused purely on database time will not
surface on its own. Write contention on the Owner's row, visible as lock
wait time or optimistic-concurrency retry counts, is the signal to watch for
the concurrent-edit failure mode in dimension 11. A healthy instance of this
pattern shows near-zero contention because the graph genuinely is edited as
a unit by one actor at a time, and rising contention is the leading
indicator that the pattern's coarse locking assumption has stopped holding.

## 17. Security and privacy implications

Judgement. These implications follow from the pattern's shape rather than
from a specific documented vulnerability report.

Storing an entire object graph as one opaque field concentrates every piece
of data inside that graph, including any sensitive fields nested deep within
it, behind a single access-control boundary. Whoever can read the Owner's row
can read everything inside the graph, because there is no column-level or
row-level granularity to restrict access to only the sensitive parts. Where a
normalized schema could apply field-level or table-level access controls, or
a database-level column encryption feature, to only the sensitive columns, a
Serialized LOB generally requires encrypting or redacting at the application
layer before serialization if partial protection is needed, because the
database has no visibility into which bytes inside the blob correspond to
which logical field. A binary or text serialization format that includes
type or class name information as part of its format, most notably several
languages' native object serializers, is a well documented attack surface
for rebuilding untrusted input, because reconstructing untrusted bytes with
such a format can be made to instantiate arbitrary classes or execute
unintended code paths. This risk does not apply when the only writer of the
field is the same trusted application that reads it, but it becomes a real
concern the moment a Serialized LOB column is populated from, or shared
with, an external or less-trusted system. Right-to-erasure and
data-subject-access requests under privacy regulation are harder to satisfy
precisely against a Serialized LOB, because deleting or redacting one
person's data that happens to be nested inside a larger stored graph
requires reading, editing, and re-serializing the whole structure, rather
than a targeted `UPDATE` or `DELETE` against a normalized row that held only
that person's data.

## 18. References

1. Martin Fowler, *Patterns of Enterprise Application Architecture*,
   Addison-Wesley, 2002, Object-Relational Structural Patterns chapter,
   Serialized LOB section.
2. Martin Fowler, "Serialized LOB", eaaCatalog,
   https://martinfowler.com/eaaCatalog/serializedLOB.html, verified
   2026-08-02.
3. Apache Tomcat, `JDBCStore` API documentation, Apache Tomcat 8.5,
   https://tomcat.apache.org/tomcat-8.5-doc/api/org/apache/catalina/session/JDBCStore.html,
   verified 2026-08-02.
4. Microsoft Learn, "Session State Providers",
   https://learn.microsoft.com/en-us/previous-versions/dotnet/articles/aa478952(v=msdn.10),
   verified 2026-08-02.
5. Ruby on Rails API documentation,
   `ActiveRecord::AttributeMethods::Serialization::ClassMethods`,
   https://api.rubyonrails.org/classes/ActiveRecord/AttributeMethods/Serialization/ClassMethods.html,
   verified 2026-08-02.
6. Hibernate ORM User Guide, section on basic type mapping for `@Lob`,
   https://docs.hibernate.org/orm/6.4/userguide/html_single/Hibernate_User_Guide.html,
   verified 2026-08-02.

## Code examples

The three samples below serialize a small self-referencing department
hierarchy, the exact structure from Fowler's own worked example, to a JSON
string that stands in for a database LOB column, then rebuild it back into a
live object graph and print a value from a nested node to prove the round
trip worked.

### TypeScript

```typescript
interface Department {
  name: string;
  children: Department[];
}

function serialize(root: Department): string {
  return JSON.stringify(root);
}

function rebuild(data: string): Department {
  return JSON.parse(data) as Department;
}

const engineering: Department = {
  name: "Engineering",
  children: [
    { name: "Platform", children: [] },
    { name: "Mobile", children: [{ name: "iOS", children: [] }] },
  ],
};

const lobColumn: string = serialize(engineering);
const restored: Department = rebuild(lobColumn);

console.log(restored.children[1].children[0].name);
```

### Python

```python
import json
from dataclasses import dataclass, field, asdict


@dataclass
class Department:
    name: str
    children: list["Department"] = field(default_factory=list)


def serialize(root: Department) -> str:
    return json.dumps(asdict(root))


def rebuild(data: str) -> Department:
    def build(node: dict) -> Department:
        return Department(
            name=node["name"],
            children=[build(child) for child in node["children"]],
        )

    return build(json.loads(data))


engineering = Department(
    name="Engineering",
    children=[
        Department(name="Platform"),
        Department(name="Mobile", children=[Department(name="iOS")]),
    ],
)

lob_column = serialize(engineering)
restored = rebuild(lob_column)

print(restored.children[1].children[0].name)
```

### Go

```go
package main

import (
	"encoding/json"
	"fmt"
)

type Department struct {
	Name     string       `json:"name"`
	Children []Department `json:"children"`
}

func serialize(root Department) (string, error) {
	bytes, err := json.Marshal(root)
	if err != nil {
		return "", err
	}
	return string(bytes), nil
}

func rebuild(data string) (Department, error) {
	var root Department
	err := json.Unmarshal([]byte(data), &root)
	return root, err
}

func main() {
	engineering := Department{
		Name: "Engineering",
		Children: []Department{
			{Name: "Platform"},
			{Name: "Mobile", Children: []Department{{Name: "iOS"}}},
		},
	}

	lobColumn, err := serialize(engineering)
	if err != nil {
		panic(err)
	}

	restored, err := rebuild(lobColumn)
	if err != nil {
		panic(err)
	}

	fmt.Println(restored.Children[1].Children[0].Name)
}
```

Java and Rust are omitted here in favor of the three above because the
pattern's shape, one write function and one rebuild function bridging an
object graph to a single field value, is identical in every language this
repository targets, and TypeScript, Python, and Go were chosen because their
standard libraries handle JSON encoding of a self-referencing struct with the
least ceremony, keeping the sample focused on the pattern rather than on
annotation or builder boilerplate that a Java or Rust equivalent would add
without illustrating anything new about Serialized LOB itself.
