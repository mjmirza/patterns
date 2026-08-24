---
name: Query Object
slug: query-object
family: 06-enterprise-application-architecture
category: Data Source Architectural
aliases: [Criteria Object, Fluent Query Builder]
first_described: "Fowler 2002"
maturity: canonical
related: [repository, data-mapper, table-data-gateway, specification, interpreter, lazy-load]
incompatible_with: []
verified: 2026-08-11
---

# Query Object

## 1. Name, aliases, and lineage

The canonical name is Query Object. Martin Fowler catalogued it in *Patterns of
Enterprise Application Architecture*, Addison-Wesley, 2002, in the Data Source
Architectural Patterns chapter, and states the intent as "an object that
represents a database query" (Martin Fowler, "Query Object",
https://martinfowler.com/eaaCatalog/queryObject.html, verified 2026-08-11).
The page is dated 05 March 2003 and points readers to chapter 13 of the same
book for the full write-up, which sits alongside Repository, Data Mapper, and
Table Data Gateway as one of the data-access patterns.

Fowler frames Query Object as a specific application of a much older idea, an
object structure that plays the role of an interpreter for a small domain
specific language, in this case a language whose vocabulary is classes and
fields rather than tables and columns. He is explicit about the mechanism, not
just the intent. A Query Object "functions as an interpreter", built from a
composite of smaller objects, each representing one clause or one comparison,
that together assemble into an executable SQL statement or an equivalent query
representation (Martin Fowler, "Query Object",
https://martinfowler.com/eaaCatalog/queryObject.html, verified 2026-08-11).
This is not an accident of prose. Query Object is architecturally a domain
specific Interpreter (Gamma, Helm, Johnson, Vlissides, *Design Patterns*,
Addison-Wesley, 1994, chapter 5, Interpreter) applied to the narrow grammar of
query construction, and most of Query Object's real-world descendants read
that way once you know to look for it, a tree of predicate and expression
nodes with an `accept`, `toSql`, or `evaluate` operation.

Two names are used for the same shape depending on the community. Object
Relational Mapping literature and Java, .NET, and PHP frameworks that expose a
tree of typed restriction objects (equal-to, greater-than, and, or, in, and
their composites) generally call it a Criteria Object or a Criteria API,
following the historical Hibernate `Criteria` interface that predates
JPA. Frameworks that instead expose a chainable, fluent builder whose methods
each return a new or mutated version of the query, `.where(...).order_by(...)`,
are usually described as a Fluent Query Builder or simply a query builder.
Both are Query Object in Fowler's sense. What varies is only the concrete
implementation variant, covered in dimension 8, not the pattern's structural
role of standing between calling code and a data source as an executable,
composable representation of a query.

The pattern predates its formal name by a wide margin. Smalltalk's `Query` and
`Cursor` classes and early object-database query interfaces from the 1990s
already built up query state as first-class objects rather than strings, and
Fowler credits the general shape to that lineage rather than claiming
originality for the idea itself, only for naming and cataloguing it (Martin
Fowler, *Patterns of Enterprise Application Architecture*, Addison-Wesley,
2002, chapter 13, "Query Object", p. 316 in the print edition's Data Source
Architectural Patterns catalogue entry list).

## 2. Problem and context

An application needs to ask its data source for a set of objects that satisfy
some condition, and the condition is not known ahead of time. It might come
from a search form with optional fields, a report with a user-selected date
range, an admin screen letting an operator combine two or three filters, or
business logic that composes a base query with additional restrictions
depending on the caller's role.

Two design responses precede Query Object, and both break down under this
exact pressure.

The first response is a menu of named finder methods on a Repository or a
Table Data Gateway. `findByLastName`, `findByLastNameAndCity`,
`findActiveCustomersInRegion`. This works while the combinations stay small and
finite. It stops working the moment a caller needs a combination nobody wrote a
method for. The maintainer is now stuck choosing between an explosion of finder
methods, one per combination the business has ever asked for, or a single
finder method with a dozen nullable parameters and an if-ladder inside that
decides which WHERE clauses to add. Both outcomes rot. The method explosion
duplicates SQL fragments across dozens of near-identical methods, so a schema
change, a renamed column, a new join needed for a filter, means editing every
method that touches that column. The parameter-ladder finder is marginally
better on duplication but is now doing runtime branching that the caller
cannot see, is untestable in isolation from the rest of the finder, and grows a
new parameter, and a new branch, every time the business asks for one more
filter.

The second response, reached for once the first stops scaling, is building the
SQL as a string directly in application code, often with `StringBuilder`
concatenation and a growing pile of `if (hasCity) sb.append(" AND city = ?")`.
This solves the combinatorial-explosion problem the finder-method approach
had, at the cost of everything a string buys you nothing on. There is no
compile-time or IDE checking of column names against the schema, so a typo in
a column name is a runtime SQL error, sometimes only under the specific
combination of filters that reaches that code path. There is no reuse of
partial query state. A base filter cannot be handed to two different callers,
one of whom adds a date restriction and one of whom adds a status restriction,
without either duplicating the string-building code or threading extra
boolean flags through it. And the query logic is now spread across the layer
that should own business rules, coupling that layer directly to SQL syntax
and, usually, to a specific database's SQL dialect.

Query Object exists for exactly this context, an application whose query
requirements are combinatorial and change over time, built by developers who
would rather express "customers in this region who have ordered in the last
year" as a composition of small, reusable, type-checked objects than as either
a combinatorial menu of methods or a hand-assembled string. Fowler's own
framing names the underlying motivation as reducing how much SQL and schema
knowledge the calling developer needs, and as localizing the effect of a
schema change to one place, the Query Object's own translation logic, instead
of every caller who wrote a raw query against that table (Martin Fowler,
"Query Object", https://martinfowler.com/eaaCatalog/queryObject.html, verified
2026-08-11).

## 3. Forces

**Expressiveness against safety.** A raw SQL string can express anything the
database's SQL dialect supports. A Query Object can only express what its
vocabulary of predicate and expression classes was built to express. Every
Query Object design trades some of SQL's raw expressiveness for compile-time
or at-minimum-construction-time checking that the query is even well formed.
The pattern favours safety, deliberately, and accepts that an escape hatch, a
raw expression node, a native-query fallback, is usually still needed for the
SQL that genuinely does not fit the vocabulary.

**Composability against performance transparency.** The entire value of the
pattern rests on being able to build a base query and hand it to two different
callers who each add different restrictions, or to build a query incrementally
across several methods. That composability is in direct tension with knowing,
by reading any single site, what SQL will finally execute. A developer reading
`orders().unshipped().forRegion(r)` cannot see the generated SQL at that call
site the way they could reading a literal string. The pattern sacrifices local
readability of the final query for global reuse of query fragments.

**Coupling to the domain model against coupling to the schema.** Fowler's
stated goal is that a Query Object refers to classes and fields, not tables
and columns, so the calling code is coupled to the domain model rather than to
the schema (Martin Fowler, "Query Object",
https://martinfowler.com/eaaCatalog/queryObject.html, verified 2026-08-11).
This is a genuine win when the schema changes independently of the domain
model, which is common under an ORM, because only the mapping layer inside the
Query Object's translation logic needs to change. It has a real cost too, the
Query Object implementation itself now needs a metadata layer, a mapping from
class and field names to table and column names, which is extra machinery that
a raw-SQL approach never needed.

**Immutability against ergonomics.** A Query Object can be designed so every
restriction-adding method returns a new, independent object (favoured by
Django's QuerySet and by most modern fluent builders) or so restriction-adding
methods mutate the receiver and return it for chaining (favoured by many
Criteria-style APIs and by hand-rolled query builders written before
immutable-by-default became the norm). Immutable designs are safe to share and
cache a base query across callers with no risk that one caller's added filter
leaks into another's, at the cost of an allocation per step and a slightly
less obvious mental model for anyone used to mutation-based builders. Mutable,
chain-returning designs are cheaper and match the syntax most developers
expect from a fluent API, at the cost of surprising aliasing bugs when a base
query is stored in a variable and reused, because two callers who each add a
filter to the "same" stored query are actually mutating one shared object.

**Team cognitive load against long-term maintainability.** A Query Object
vocabulary, however well designed, is one more thing a new team member has to
learn on top of SQL, which they already know from every other job. The payoff
is amortized over the life of the codebase. The pattern earns its cost back
only if the combinatorial-query problem it solves would otherwise recur many
times across the application's lifetime. A single admin screen with three
fixed filters rarely earns Query Object's learning cost. A reporting engine
whose filters are user-composed rarely survives without something in this
family.

## 4. Applicability and non-applicability

### Reach for Query Object when

- Callers need to combine an open-ended, changing set of filter conditions,
  and a fixed menu of named finder methods has already started to explode or
  is visibly about to.
- The application already talks to the data source through domain objects
  (via Data Mapper, Repository, or an Active Record layer) and raw SQL strings
  scattered through business logic would break that separation.
- The same base query, or the same restriction, needs to be reused across
  multiple call sites, and duplicating a SQL fragment in each of them has
  already caused a schema-change bug once.
- The application must support ad hoc, dynamically composed queries driven by
  a user interface (an advanced search form, a report builder, an admin filter
  panel) where the exact combination of filters cannot be enumerated in
  advance.
- The team wants query construction to be unit-testable independently of a
  live database, by asserting on the structure of the built query (its clause
  list, its parameter values) rather than only on the SQL string or the
  eventual result set.

### Do not reach for Query Object when

- The application has a small, fixed, enumerable set of queries. A handful of
  named finder methods on a Repository or a Table Data Gateway is simpler,
  more directly readable, and does not require anyone to learn a query
  vocabulary. Fowler himself frames Query Object as the answer once finder
  methods "become awkward", not as a default starting point (Martin Fowler,
  "Query Object", https://martinfowler.com/eaaCatalog/queryObject.html,
  verified 2026-08-11).
- The team already has a mature ORM whose own query builder covers the need.
  Building a second, hand-rolled Query Object layer on top of Doctrine's
  QueryBuilder, Django's QuerySet, or JPA's Criteria API duplicates machinery
  the framework already provides at production quality, and adds an
  indirection layer with no independent value.
- The query in question is genuinely a one-off report or migration script.
  The reuse and testability payoff of a Query Object never arrives for code
  that runs once.
- Extreme, hand-tuned SQL performance is the actual requirement, for example a
  query that must use a specific index hint, a specific join order, or a
  database-specific optimizer directive. Most Query Object abstractions
  either cannot express these at all or express them so awkwardly that a raw,
  reviewed SQL string with a comment explaining the hint is the more honest
  and more maintainable choice.
- The data source is not relational and does not have the kind of composable
  filter semantics the pattern assumes. A key-value store lookup by a single
  known key, or a full-text search against an external index with its own
  dedicated query language, is usually better served by that store's own
  native client than by forcing it through a Query Object designed around
  SQL's WHERE-clause shape.
- The codebase deliberately embraces raw SQL as its primary data-access style,
  for instance a project standardized on hand-written, reviewed SQL files
  managed as versioned assets. Introducing Query Object there fights the
  team's chosen architecture rather than serving it.

## 5. Structure

**Query** (or `QueryObject`, `Criteria`). The root object a caller constructs
and holds. Owns a collection of restriction nodes and, usually, ordering and
paging state. Exposes methods to add restrictions (commonly returning `self`
or a new `Query` for chaining) and an execute-style operation that hands the
built structure to the data source and returns a result.

**Criterion / Restriction / Predicate.** One node representing a single
comparison or logical grouping, equality, range, membership, pattern match,
and their boolean combinations (`And`, `Or`, `Not`). Each node knows how to
render itself, whether that means appending SQL fragments and bind parameters,
or contributing to an intermediate expression tree that a later stage
compiles to SQL.

**Field / Property reference.** A typed handle onto a domain-model field or
property, used inside a criterion instead of a raw column name. This is the
element that carries Fowler's stated goal of expressing the query in terms of
classes and fields rather than tables and columns.

**Metadata Mapping** (or an equivalent schema map). A lookup, usually shared
with the Data Mapper or ORM the application already has, that translates a
class-and-field reference into a table-and-column reference at query-build
time. This is the seam that lets a schema rename ripple through automatically
instead of requiring every call site to be found and edited.

**Query Translator / SQL generator.** The component, sometimes folded directly
into `Query`, that walks the criterion tree and produces an executable
statement, a SQL string with positional or named bind parameters, or an
in-memory expression tree handed to a driver that compiles it further, as
Entity Framework's `IQueryable` provider does, and as Doctrine's
`QueryBuilder` does when it emits DQL that its own parser later turns into
SQL.

**Data source / Gateway.** Whatever actually executes the built query, a JDBC
`Connection`, an ADO.NET `Command`, a raw database driver call, or a Table
Data Gateway or Data Mapper that the Query Object hands its finished statement
to.

**Result mapper.** Turns the raw rows the data source returns back into domain
objects, usually delegating to the same Data Mapper the application already
uses for single-object loads.

## 6. ASCII structure diagram

```
+-----------------+
| Client (caller) |
+-----------------+
           | holds 0..*
           v
+-------------------+
| Query             |
| where(Criterion)  |
| orderBy(Field)    |
| execute(): Result |
+-------------------+
           | 0..*
           v
+----------------------+
| Criterion (abstract) |
| toSql(Mapping)       |
+----------------------+
           ^
           | extended by
     +-----+-----+-----+
     |           |     |
+---------------+ +---------------+ +---------------+
| Comparison    | | And / Or      | | Field         |
| (=, <, IN)    | | (composite,   | | reference     |
+---------------+ | holds more    | +---------------+
                | Criterion)    |                
                +---------------+                
                             |
                             v
+-----------------------------+
| Metadata Mapping            |
| class.field -> table.column |
+-----------------------------+
           |
           v
+------------------------------------+
| Query Translator                   |
| criterion tree -> SQL + parameters |
+------------------------------------+
```

## 7. Dynamics

The typical sequence for a caller building and running a composed query.

```
Client              Query                  Criterion tree        Metadata Mapping    Translator      Data source
  |                   |                          |                     |                |               |
  |--new()----------->|                          |                     |                |               |
  |                   |--(empty root)             |                     |                |               |
  |                   |                          |                     |                |               |
  |--where(A)-------->|--append(A)-------------->|                     |                |               |
  |                   |                          | root: A             |                |               |
  |<--self------------|                          |                     |                |               |
  |                   |                          |                     |                |               |
  |--and(B)---------->|--append(B, AND)--------->|                     |                |               |
  |                   |                          | root: A AND B       |                |               |
  |<--self------------|                          |                     |                |               |
  |                   |                          |                     |                |               |
  |--orderBy(field)--->|--set ordering            |                     |                |               |
  |                   |                          |                     |                |               |
  |--execute()------->|--translate(tree)-------------------------------->|--resolve()--->|               |
  |                   |                          |                     |<--table.col----|               |
  |                   |                          |                     |                |--emit SQL+---->|
  |                   |                          |                     |                |  params        |
  |                   |                          |                     |                |               |
  |                   |                          |                     |                |<--rows---------|
  |                   |<--rows-------------------------------------------------------------------------|
  |                   |--map(rows)--------------->|                     |                |               |
  |<--domain objects---|                          |                     |                |               |
```

Two variations on this sequence show up constantly in production systems and
are worth naming explicitly, because they change what "the query" even means
at each step.

**Deferred, lazy execution.** In immutable, chainable designs (Django's
`QuerySet`, Rails' `ActiveRecord::Relation`), no `translate` or `execute` step
runs at any of the `where` or `orderBy` calls. Each call instead returns a new
Query Object wrapping an updated criterion tree, and the translate-and-execute
step is deferred until the caller does something that actually needs rows, an
iteration, a `count()`, an explicit `.all()` or `.to_a`. This is Lazy Load
(dimension 13 covers the relationship) applied at the level of the whole
query rather than a single association.

**Reuse of a shared base.** A base `Query` built once, held in a variable or
returned from a factory method, is handed to two different callers who each
add their own restriction and independently execute. In an immutable design
this is safe, each caller's `.where(...)` call returns its own new tree,
leaving the shared base untouched. In a mutating, chain-returning design this
is a well-documented hazard. Both callers are mutating the same underlying
object, so the second caller's filter silently applies to the first caller's
query too if the base was stored and reused rather than freshly obtained. This
exact failure mode is covered as a named failure mode in dimension 11.

## 8. Implementation variants

**String-assembling Query Object.** The simplest variant. Each `where`-style
method appends a fragment to an internal string builder and records a bound
parameter in a parallel list. `execute()` hands the finished string and
parameter array to a plain database driver call. This is close to what
hand-rolled query builders looked like before ORMs standardized the pattern,
and it is still common in lightweight, no-ORM codebases that want composable
query construction without adopting a full mapping framework.

**Tree-of-objects Interpreter variant.** Each restriction is its own small
object (`Equals`, `GreaterThan`, `And`, `Or`) implementing a shared interface
with a render or evaluate operation. `execute()` walks the tree once at the
end. This is the variant that most literally matches Fowler's description of
the pattern as an interpreter, and it is the variant that composes best. Two
subtrees can be combined with `And` or `Or` without either subtree knowing
anything about how it will eventually be combined. JPA's `CriteriaBuilder`
produces exactly this shape, `Predicate` objects composed via
`criteriaBuilder.and(...)` and `criteriaBuilder.or(...)`, that a
`CriteriaQuery` later compiles.

**Fluent, chain-returning builder.** Every method on `Query` mutates internal
state and returns `this` (or `self`), so calls read as a single fluent
expression, `query.where("status", "active").orderBy("createdAt").limit(20)`.
Internally this can be implemented as either of the two variants above; the
"fluent" label describes only the calling convention, not the internal
representation. Most SQL query builder libraries (Knex.js in the Node
ecosystem, Doctrine's `QueryBuilder` in PHP) present this calling convention
regardless of internal implementation.

**Immutable, copy-on-write builder.** Structurally identical to the fluent
variant, except every `where`, `orderBy`, or `limit` call returns a brand new
`Query` instance wrapping an updated, structurally-shared tree, and the
receiver is left unchanged. Django's `QuerySet` is the canonical example. Each
refinement method documents that it "does not actually modify the original
QuerySet object" and "instead returns a new QuerySet" (see the production-use
citation in dimension 9). This variant costs an allocation per refinement step
and buys safe sharing of a base query across independent callers.

**Expression-tree-to-provider variant.** Instead of translating directly to
SQL text, the Query Object builds a language-native expression tree (an
Abstract Syntax Tree of the host language's own expression nodes) that a
pluggable provider later compiles, potentially into SQL, into an in-memory
LINQ-to-Objects filter, or into a different backend entirely. .NET's
`IQueryable<T>` and LINQ expression trees are the best known example of this
variant. The same query syntax compiles differently depending on which
`IQueryProvider` receives the tree (Entity Framework's SQL provider versus an
in-memory "LINQ to Objects" provider).

**Specification-composed Query Object.** The criterion tree is built not
directly through `where` calls on the Query Object itself but by composing
independent Specification objects (dimension 13 covers this relationship in
detail), each encapsulating one named business rule as a predicate, which the
Query Object then accepts and translates. This variant separates "what counts
as an active, high-value customer" (a Specification, owned by the domain
layer) from "how do I run a query for that" (the Query Object, owned by the
data-access layer).

**Named, closure-based variant** (language-idiomatic). In languages with
first-class functions and lightweight lambda syntax, a lighter alternative to
a full object-per-criterion tree is a `Query` object whose `where` method
simply accepts a closure or predicate function and stores it in a list, to be
combined and applied at execute time. This trades away some of the
introspectability a full object tree gives (a caller cannot examine the
structure of a stored closure the way they can walk an object tree) for
substantially less boilerplate, and shows up in smaller Python and JavaScript
query-builder implementations that do not need to compile down to SQL text.

## 9. Known production uses

- **Doctrine ORM's `QueryBuilder`** (PHP). Doctrine's documentation describes
  it as "a tool to dynamically build" DQL queries through a programmatic,
  fluent, object-oriented interface rather than raw query strings, letting
  developers build queries conditionally across several steps and compose
  expressions through helper methods (Doctrine Project, "The QueryBuilder",
  Doctrine ORM current documentation,
  https://www.doctrine-project.org/projects/doctrine-orm/en/current/reference/query-builder.html,
  verified 2026-08-11). This is a direct, textbook instance of the
  chain-returning implementation variant, backed by an internal expression
  tree that Doctrine's own `Expr` classes assemble.

- **Django's `QuerySet`** (Python). Django's own documentation states that a
  `QuerySet` "represents a collection of objects from your database", that it
  "can have zero, one or many filters", that in SQL terms it "equates to a
  `SELECT` statement, and a filter is a limiting clause such as `WHERE` or
  `LIMIT`", and that `QuerySet` objects "are lazy" so that "creating a
  `QuerySet` doesn't involve any database activity" until the `QuerySet` is
  evaluated (Django Software Foundation, "Making queries", Django 5.2
  documentation,
  https://docs.djangoproject.com/en/5.2/topics/db/queries/, verified
  2026-08-11). This is the canonical immutable, copy-on-write, lazily
  evaluated variant. Chaining `.filter(...).exclude(...).filter(...)`
  produces a new `QuerySet` at each step, none of which touch the database
  until iterated or otherwise forced.

- **Ruby on Rails' `ActiveRecord::Relation`.** The Rails guides document that
  methods can be chained "when the previous method called returns an
  `ActiveRecord::Relation`, like `all`, `where`, and `joins`", and that "when
  an Active Record method is called, the query is not immediately generated
  and sent to the database", only "when the data is actually needed" (Rails
  Core Team, "Active Record Query Interface", Ruby on Rails Guides,
  https://guides.rubyonrails.org/active_record_querying.html, verified
  2026-08-11). This is the same lazy, chain-returning shape as Django's
  `QuerySet`, applied to Rails' own Active Record data layer, and it is
  itself the pattern's most cited real-world example of the boundary between
  Query Object and the Active Record pattern that consumes its output.

- **Jakarta Persistence's Criteria API** (Java, formerly a Hibernate-specific
  feature and now a standard part of the JPA specification). The Jakarta
  Persistence 3.2 specification devotes chapter 6 to the Criteria API,
  describing it as a programmatic alternative to string-based JPQL query
  construction in which query elements are represented as Java objects,
  offering compile-time, type-safe construction of queries via
  `CriteriaBuilder` and `CriteriaQuery`, in contrast to writing JPQL strings
  (Eclipse Foundation, "Jakarta Persistence Specification, Version 3.2",
  chapter 6, "Criteria API",
  https://jakarta.ee/specifications/persistence/3.2/jakarta-persistence-spec-3.2.html,
  verified 2026-08-11). This is the tree-of-objects Interpreter variant in
  its most literal, standardized form. `Predicate` objects composed through
  `criteriaBuilder.and(...)`, `criteriaBuilder.equal(...)`, and similar
  factory methods, walked by the persistence provider at query time.

## 10. Consequences

Positive.

- Query construction becomes reusable and composable. The same base query, or
  the same restriction, can be shared across multiple call sites, and adding
  or removing a filter is a matter of adding or removing one criterion object
  rather than editing a SQL string embedded in business logic.
- Query construction becomes independently testable. A test can assert on the
  structure of a built `Query` object, or on the SQL and parameters it would
  produce, without touching a real database, something a raw SQL string
  embedded in a method body cannot offer.
- A single point of schema knowledge. When the Query Object is paired with a
  Metadata Mapping, a schema rename touches one mapping definition instead of
  every scattered SQL string that referenced the old column.
- Calling code reads closer to the domain than to the database. Queries are
  expressed in terms of classes, fields, and business predicates, which is
  more legible to a developer who knows the domain model but has never
  memorized the schema.
- Dynamic, ad hoc queries stop being special cases. A search form with
  optional fields builds its query by conditionally calling `.where(...)`
  for each present field, with no branching logic duplicated across finder
  methods.

Negative.

- The Query Object's own vocabulary is a second thing to learn, on top of
  SQL every developer on the team already knows from prior jobs. A team new
  to the codebase pays a real ramp-up cost before they can read or write a
  query confidently.
- Debugging is one layer removed from the executed SQL. When a query is
  slow or wrong, the developer must first mentally translate the criterion
  tree back into the SQL it produces, or turn on query logging to see the
  generated statement, before they can reason about it the way they would
  reason about a literal string.
- Full SQL expressiveness is rarely available. Vendor-specific hints, window
  functions, complex subqueries, and recursive CTEs frequently fall outside
  what the Query Object's vocabulary was built to express, forcing either an
  awkward extension of the vocabulary or a fallback to raw SQL anyway,
  undermining the abstraction's promised uniformity.
- Mutable, chain-returning implementations introduce a real aliasing hazard.
  A shared base query, stored and reused by two callers who each expect an
  independent starting point, can leak one caller's added filter into the
  other's results. This is common enough in production systems to be
  documented as its own failure mode in dimension 11.
- Building and maintaining the Query Object machinery itself, the criterion
  classes, the metadata mapping, the translator, is a real engineering
  investment. For a small, static set of queries this investment never pays
  back, which is exactly why dimension 4 lists a small fixed query set as a
  reason not to use the pattern.

## 11. Failure modes and misuse

Shared mutable base query leaks filters between callers.

Symptom. Two unrelated features start returning results that are subtly
scoped by each other's filters, with no obvious code path connecting them,
and the bug only reproduces when both features run in the same process in a
particular order.

Cause. A `Query` (or equivalent builder) built once, stored in a shared
variable, field, or cache, and handed to two callers, each of whom calls a
mutating, chain-returning method (`where`, `andWhere`) that mutates the shared
receiver instead of returning an independent copy.

Fix. Either switch the Query Object implementation to the immutable,
copy-on-write variant (dimension 8), which most modern frameworks default to
for exactly this reason, or, if the mutable variant must be kept, document and
enforce that a stored base query is always explicitly cloned before any
caller adds a restriction to it.

N+1 query generation hidden behind a fluent chain.

Symptom. A page or endpoint that looks like it issues one query, reading the
code top to bottom, actually issues one query per row of an earlier result,
and this only shows up as a production performance problem under real data
volume, never in a development database with ten rows.

Cause. The Query Object's laziness (dimension 7) defers execution until data
is actually accessed, and a loop that iterates a lazily-built collection and
accesses a related property inside the loop body triggers one fresh Query
Object execution per iteration, because nothing in the fluent syntax signals
that the access inside the loop is itself a database round trip. This is the
same underlying issue Lazy Load documents, surfacing here because Query
Object's own laziness compounds it.

Fix. Eagerly load or explicitly join the related data before the loop, most
frameworks that ship Query Object also ship an eager-loading escape hatch,
such as Django's `select_related` and `prefetch_related`, or Doctrine's
explicit `join` calls, and add a query-count assertion in tests that
exercise the loop, so a regression back to N+1 fails a test instead of only a
production dashboard.

Leaky abstraction forces a raw-SQL fallback that bypasses the mapping.

Symptom. One specific report or query, written as an escape-hatch raw SQL
string inside an otherwise Query-Object-based codebase, silently breaks after
an unrelated schema rename, because it referenced the old column name
directly and the mapping layer that would have caught the rename was
bypassed.

Cause. The Query Object's vocabulary genuinely could not express the query
(a vendor-specific hint, a recursive CTE, an aggregate with an unusual
grouping), so a developer reached for a raw-SQL escape hatch, and the schema
change that broke it landed months later with nobody remembering the raw
query existed.

Fix. Track every raw-SQL escape hatch in one place (a naming convention, a
lint rule, or a small registry file) so a schema migration checklist includes
grepping for them, and prefer extending the Query Object's vocabulary with a
new criterion type over an ad hoc raw fragment whenever the same escape is
needed more than once.

Unbounded, unindexed dynamic queries from an unconstrained search form.

Symptom. A search feature that works fine in every manual test suddenly times
out or locks a table when a real user submits a search with an unusual
combination of filters, or with a text field containing a wildcard pattern
that forces a full table scan.

Cause. The Query Object made composing filters so easy that no one imposed a
limit on which fields can be combined, or validated that a filter's shape
(a leading-wildcard `LIKE` pattern, for example) is actually indexable,
because the pattern's whole selling point is decoupling the caller from
needing to know that.

Fix. Put an explicit allowlist of combinable, indexed fields in front of the
Query Object layer for any user-facing search feature, reject or rewrite
filter shapes known to defeat an index (a leading wildcard, a
function-wrapped column with no matching functional index) before they reach
the Query Object, and load-test the search feature with realistic filter
combinations, not only the combinations a manual tester happened to try.

Query Object used as a substitute for domain validation.

Symptom. Business rules ("only active customers", "only orders placed within
the return window") are duplicated as ad hoc criterion combinations scattered
across many call sites, and a rule change requires finding and editing every
one of them.

Cause. Nothing stops a caller from building the same three-criterion
combination inline at ten different call sites instead of naming it once.
Query Object solves the mechanical problem of composing filters, but it does
not by itself solve the separate problem of naming and reusing a business
rule.

Fix. Extract the repeated combination into a named Specification (dimension
13) or a named factory method on the Query Object's own type, so the rule is
defined once and every call site references the name, not the raw
combination.

## 12. Trade-off matrix

| Force | Query Object | Table Data Gateway | Named finder methods on Repository | Raw SQL / string concatenation |
|---|---|---|---|---|
| Expressiveness for arbitrary combinations of filters | High. Any composition of the vocabulary's criteria | Low. One method per table, not per filter combination | Low, degrades to method explosion or a parameter ladder as combinations grow | Highest, limited only by the database's own SQL dialect |
| Compile-time or construction-time safety | High in typed-tree variants, moderate in string-assembling variants | High, but only for the fixed methods that already exist | High for existing methods, none for ad hoc combinations | None, errors surface only at execution |
| Reuse of query fragments across call sites | High, a base query or criterion can be shared | Low, each method is a self-contained unit | Low, shared logic must be pulled into a helper or duplicated | Low, fragments duplicated by copy-paste |
| Local readability at the call site | Moderate, the fluent chain is readable but hides generated SQL | High, the method name states the query directly | High, the method name states the query directly | High for a single literal query, low once concatenation logic appears |
| Testability without a live database | High, structure can be asserted independent of execution | Moderate, method behaviour still runs against a real or fake table | Moderate, same as Table Data Gateway | Low, a string cannot be meaningfully asserted without executing it |
| Cost to add support for one more ad hoc filter combination | Low, add or compose one more criterion | High, usually a new method | High, a new method or a widened parameter list | Low at the call site, but grows the concatenation logic's complexity |
| Learning curve for a developer new to the codebase | Moderate to high, the vocabulary must be learned | Low, plain methods with SQL knowledge already known | Low, plain methods with SQL knowledge already known | Lowest, ordinary SQL |
| Access to database-specific features (hints, CTEs, window functions) | Low to moderate, usually requires an escape hatch | Moderate, the method's SQL body can use anything | Moderate, same as Table Data Gateway | Highest |

## 13. Related and incompatible patterns

**Repository.** Repository presents a collection-like interface over a set of
domain objects and is frequently the object a caller actually holds; Query
Object is very often the mechanism a Repository implementation uses
internally, or exposes directly, to let a caller ask for something more
specific than a named finder method covers. In many real codebases the line
between "a Repository with a rich query interface" and "a Query Object with a
collection-like execute method" is blurry by design, and that blurriness is
not a mistake, the two patterns are meant to compose.

**Data Mapper.** Query Object depends on the same class-to-table and
field-to-column mapping metadata that a Data Mapper already needs to load and
save individual domain objects. In practice the two nearly always ship
together. The Data Mapper's metadata is exactly the Metadata Mapping
dimension 5 describes the Query Translator depending on, so a codebase rarely
has one without the other.

**Table Data Gateway.** Table Data Gateway is the pattern Query Object most
directly displaces once a fixed set of gateway methods stops covering the
combinations callers need. The two are not mutually exclusive within one
codebase. A simple, low-churn table can stay on Table Data Gateway while a
table with genuinely dynamic query needs gets a Query Object built on top of
it or in front of it.

**Specification.** Specification names and encapsulates one business
predicate ("is an active customer", "is within the return window") as a
first-class, independently testable, composable object, deliberately kept
separate from any data-access concern. A Query Object can accept
Specification objects and translate them into its own criterion tree,
letting the domain layer own the business rule while the data-access layer
owns the SQL translation. Where Query Object is data-access machinery,
Specification is domain-layer vocabulary, and the Specification-composed
Query Object implementation variant in dimension 8 is exactly this pairing.

**Interpreter (GoF).** As dimension 1 covers, Query Object's tree-of-objects
implementation variant is architecturally an Interpreter applied to a query
grammar. The relationship is not incidental. Anyone who has implemented
Interpreter already has most of the conceptual vocabulary needed to implement
this variant of Query Object, and the failure modes both patterns share, a
grammar that grows unwieldy as it tries to cover every case, apply here too.

**Lazy Load.** The deferred-execution behaviour most production Query Object
implementations exhibit (dimension 7) is a direct application of Lazy Load at
the level of an entire query rather than a single object reference or
collection. The N+1 failure mode in dimension 11 is the same failure mode
Lazy Load documents for object references, recurring here because Query
Object inherits the same laziness.

**Unit of Work.** Query Object and Unit of Work solve different problems,
reading versus tracking pending writes, and are not in tension, but they
frequently need to cooperate. A query executed mid-transaction against
objects that Unit of Work has already modified in memory but not yet flushed
can return stale results unless the Unit of Work flushes pending changes
before the Query Object's translator sends its statement to the database.
Frameworks that ship both patterns together (Doctrine, Hibernate) generally
handle this flush-before-query coordination automatically; a hand-rolled
combination of the two patterns has to handle it deliberately.

No pattern in this catalog is actively incompatible with Query Object in the
sense of the two being unable to coexist in one codebase; the tensions above
are all about overlap and division of responsibility rather than conflict.

## 14. Refactoring path in and out

Introducing Query Object into code that currently uses named finder methods
or string concatenation.

1. Identify the finder methods, or the string-concatenation call sites, whose
   combinations are actually growing over time, not every finder in the
   codebase. Query Object earns its cost only where the combinatorial
   pressure is real.
2. Design the minimum criterion vocabulary that covers today's actual
   combinations, not a speculative superset. Start with equality, a small set
   of comparisons, and `And`, and extend the vocabulary only when a real
   caller needs a shape it does not yet support.
3. Introduce the `Query` type and its criterion classes without removing any
   existing finder method yet. Let the two approaches coexist.
4. Migrate call sites one at a time from the old finder method to the new
   Query Object, verifying with a test at each site that the generated query
   and its result set match the old finder method's behaviour before deleting
   the old method.
5. Once every caller of a given finder method has migrated, delete that
   finder method. Repeat for the next finder method rather than migrating the
   whole surface at once.
6. If a Metadata Mapping does not already exist because the codebase was not
   using an ORM, build the minimum mapping needed for the fields actually
   referenced by the migrated queries, not a full schema mapping up front.

Removing Query Object once it stops earning its place.

1. Confirm the removal is warranted. Either the combinatorial pressure that
   justified the pattern has genuinely gone away (the query set has settled
   into a small, stable list), or the team is migrating to a mature ORM whose
   own query builder should replace the hand-rolled one rather than living
   alongside it.
2. Inventory every distinct query shape currently built through the Query
   Object across the codebase. This inventory becomes the list of finder
   methods, or the list of calls into the new ORM's builder, that replace it.
3. Replace each Query Object call site with the corresponding named finder
   method or the replacement builder's equivalent call, verifying result
   parity with a test at each site before deleting the old call.
4. Delete the criterion classes, the Query type, and the hand-rolled Query
   Translator only after every call site has migrated and no code references
   them, following the same trailing-deletion order used when introducing
   the pattern, so the codebase never sits mid-refactor with two competing
   query mechanisms and no clear owner for either.

## 15. Testing and verification

Query Object's central testability win is that query construction and query
execution can be tested separately, and most of the value comes from
exercising construction without a database at all.

**Structural assertions on the built query.** Where the implementation
exposes its criterion tree (the tree-of-objects Interpreter variant, dimension
8), a test can build a `Query` and assert directly on the shape of the
resulting tree, which criteria are present, how they are composed, whether an
expected `And` node wraps the expected two children. This catches
composition bugs (a filter silently dropped, an `Or` used where an `And` was
intended) with no database involved and no network round trip.

**SQL and parameter assertions without execution.** Where the criterion tree
is not directly inspectable, or where the team specifically wants to guard
against a generated-SQL regression, a test can call the translator directly
and assert on the produced SQL string and its bound parameter list, without
sending either to a real database. This is the natural place to catch a
SQL-injection regression too. Asserting that a value ends up as a bound
parameter and never gets string-interpolated into the SQL text directly, in
every code path, is a cheap and durable test.

**Integration tests against a real or containerized database.** Structural
and SQL-level tests catch construction bugs but cannot catch a query that is
syntactically valid, correctly generated, and still wrong against the actual
schema, or a query that is correct but catastrophically slow. A smaller,
separate suite that runs a representative sample of built queries against a
real (or containerized, ephemeral) database instance, asserting on the actual
result rows returned, closes that gap. This suite is deliberately kept
smaller than the structural suite, because it is slower and because most
construction bugs are already caught earlier and more cheaply.

**Query-count assertions to guard against N+1 regressions.** Given the N+1
failure mode in dimension 11, a test that exercises a loop over a
lazily-loaded Query Object result should assert on the total number of
queries issued, not only on the correctness of the final data, so a future
change that reintroduces an access-inside-a-loop pattern fails a fast unit or
integration test instead of only showing up as a slow production dashboard.

**Property-based testing of the criterion composer.** For a Query Object with
a rich composition vocabulary (nested `And`/`Or`, negation), a property-based
test that generates random valid combinations of criteria and asserts an
invariant, for example that translating `And(A, B)` and separately
intersecting the result sets of `A` and `B` produce identical row sets, is a
strong, low-effort way to catch composition bugs the hand-written example
tests never think to try.

## 16. Observability signals

**Generated SQL and its bound parameters, logged at the point of execution.**
The single most valuable observability signal for a Query Object layer is a
log line, at debug or trace level in production and at a higher level in
development, showing the exact SQL text and parameter values a given
execution produced. Without this, debugging "why did this query return the
wrong rows" degrades into re-deriving the SQL by reading the criterion
composition by hand.

**Query count per logical request or transaction.** Because Query Object's
laziness makes N+1 generation invisible at the call site (dimension 11), a
per-request or per-transaction query counter, surfaced in development
tooling and sampled in production, is the primary early-warning signal for
that failure mode. A healthy request touching a Query Object layer shows a
small, stable number of queries regardless of how many result rows it
processes; an unhealthy one shows a query count that scales linearly with
result size.

**Query execution latency, broken down by generated query shape rather than
by call site.** Because many different call sites can produce structurally
similar generated SQL through different criterion compositions, grouping
latency metrics by the normalized shape of the generated query (with literal
parameter values stripped, as most APM tooling for SQL already does) surfaces
a slow query pattern even when it originates from several different Query
Object call sites in application code.

**Escape-hatch usage counter.** A codebase with a raw-SQL escape hatch
(dimension 8, and the failure mode in dimension 11) benefits from an explicit
counter, or even just a grep-friendly marker convention, tracking how many
call sites use it and where. A rising count over time is a direct signal that
the Query Object's vocabulary is falling behind what the application actually
needs, and is the concrete trigger for extending the vocabulary rather than
letting the escape hatch spread.

**Cache hit rate, if built queries or their results are cached.** Where a
Query Object's built SQL, or the result of executing it, is cached (common
for expensive, frequently-repeated report queries), a cache hit rate metric
distinguishes a cache that is earning its complexity from one that is not,
and a sudden drop in hit rate is a strong signal that either the query
vocabulary changed in a way that broke cache-key stability, or that the
underlying data started changing faster than the cache's invalidation
strategy accounts for.

## 17. Security and privacy implications

**Parameterized construction closes the classic SQL injection surface, but
only when every code path actually uses it.** A Query Object built correctly,
where every value contributed by a criterion becomes a bound parameter rather
than an interpolated string, structurally prevents SQL injection through the
Query Object's normal path, because there is no code path where user input
ever becomes part of the SQL text itself. This protection is only as good as
the least-careful escape hatch in the codebase; the moment a raw-SQL fallback
(dimension 8, and the failure mode in dimension 11) exists and is used with
directly interpolated user input, the vulnerability is back, indistinguishable
from any hand-rolled string-concatenation bug, and often harder to find
precisely because the surrounding codebase's normal path looks safe.

**Field-name and sort-direction inputs need the same discipline as value
inputs, and are easy to overlook.** Bound parameters solve the value-injection
problem, but a Query Object whose column-to-sort-by, or filter-field-to-apply,
is itself taken from user input (an API accepting a raw field name string for
sorting, for example) opens a distinct injection surface if that field name
is ever concatenated directly into an `ORDER BY` clause instead of being
validated against an allowlist of known Field references first. The Metadata
Mapping layer (dimension 5) is the natural place to enforce this. Any field
name that does not resolve through the mapping should be rejected before it
reaches the translator, never passed through as-is.

**Query Object's expressiveness is itself an authorization surface that must
be constrained deliberately.** Because the pattern's entire purpose is to let
callers compose arbitrarily rich filter combinations, an authorization check
that only gates whether a caller may call a given method (as it naturally
would for a fixed set of named finder methods) does not automatically gate
what that caller may filter by or see once a Query Object exposes broad
composability. A multi-tenant application, in particular, must apply the
tenant-scoping restriction at a layer the caller cannot remove or
bypass by composing an unexpected combination of criteria, typically by
injecting the tenant restriction automatically inside the Query Object's own
construction rather than trusting every caller to remember to add it.

**Denial-of-service risk from unconstrained, dynamically composed queries.**
As the failure mode in dimension 11 describes, a Query Object's flexibility
can let a caller (malicious or merely careless) compose a filter combination
that forces an expensive full scan, an unbounded result set, or a
pathologically slow join, with no code-level signal that anything unusual
happened until the database itself is under load. Any Query Object surface
reachable from untrusted or lightly trusted input (a public search endpoint,
an API accepting arbitrary filter parameters) needs its own explicit
constraints, an allowlist of combinable fields, a hard result-size cap, and a
query timeout enforced at the data-source layer, independent of whatever
validation the application code performs, because the database is the last
line of defense once a costly query has already been built and sent.

**Sensitive fields must be excluded from the queryable vocabulary, not merely
from the response serialization.** A common mistake is restricting which
fields a result object serializes to the caller while leaving those same
fields fully queryable, letting an attacker infer a sensitive value's content
through timing or boolean-style oracle queries, does a customer whose
password-reset-token starts with a given prefix exist, even though the field
itself never appears in any response body. Fields that must not be exposed to
a given caller need to be excluded at the Metadata Mapping or criterion-class
level for that caller's context, not only filtered out of the eventual JSON
response.

## 18. References

1. Martin Fowler, "Query Object", martinfowler.com,
   https://martinfowler.com/eaaCatalog/queryObject.html, page dated 05 March
   2003, verified 2026-08-11.
2. Martin Fowler, *Patterns of Enterprise Application Architecture*,
   Addison-Wesley, 2002, chapter 13, "Query Object", and the surrounding Data
   Source Architectural Patterns catalogue.
3. Gamma, Helm, Johnson, Vlissides, *Design Patterns. Elements of Reusable
   Object-Oriented Software*, Addison-Wesley, 1994, chapter 5, "Interpreter".
4. Doctrine Project, "The QueryBuilder", Doctrine ORM current documentation,
   https://www.doctrine-project.org/projects/doctrine-orm/en/current/reference/query-builder.html,
   verified 2026-08-11.
5. Django Software Foundation, "Making queries", Django 5.2 documentation,
   https://docs.djangoproject.com/en/5.2/topics/db/queries/, verified
   2026-08-11.
6. Rails Core Team, "Active Record Query Interface", Ruby on Rails Guides,
   https://guides.rubyonrails.org/active_record_querying.html, verified
   2026-08-11.
7. Eclipse Foundation, "Jakarta Persistence Specification, Version 3.2",
   chapter 6, "Criteria API",
   https://jakarta.ee/specifications/persistence/3.2/jakarta-persistence-spec-3.2.html,
   verified 2026-08-11.
8. Martin Fowler, "Repository", martinfowler.com,
   https://martinfowler.com/eaaCatalog/repository.html, verified 2026-08-11.

## Code examples

Working, minimal, original examples in three languages, each compiled or run
locally before inclusion. All three build a small, in-memory customer search
against a fixed dataset, avoiding a live database dependency so the example
is self-contained and runnable as shown.

### TypeScript. Immutable, chain-returning Query Object

```typescript
interface Customer {
  id: number;
  name: string;
  city: string;
  active: boolean;
  orders: number;
}

type Criterion = (c: Customer) => boolean;

class CustomerQuery {
  private constructor(private readonly criteria: ReadonlyArray<Criterion>) {}

  static all(): CustomerQuery {
    return new CustomerQuery([]);
  }

  whereCity(city: string): CustomerQuery {
    return new CustomerQuery([...this.criteria, (c) => c.city === city]);
  }

  whereActive(active: boolean): CustomerQuery {
    return new CustomerQuery([...this.criteria, (c) => c.active === active]);
  }

  whereMinOrders(min: number): CustomerQuery {
    return new CustomerQuery([...this.criteria, (c) => c.orders >= min]);
  }

  execute(dataSource: ReadonlyArray<Customer>): Customer[] {
    return dataSource.filter((row) =>
      this.criteria.every((criterion) => criterion(row)),
    );
  }
}

const dataSource: Customer[] = [
  { id: 1, name: "Reyes", city: "Munich", active: true, orders: 12 },
  { id: 2, name: "Klein", city: "Munich", active: false, orders: 3 },
  { id: 3, name: "Ortiz", city: "Berlin", active: true, orders: 7 },
  { id: 4, name: "Vogel", city: "Munich", active: true, orders: 1 },
];

const base = CustomerQuery.all().whereCity("Munich").whereActive(true);
const bigSpenders = base.whereMinOrders(5);
const anyMunichActive = base;

console.log(
  "big spenders",
  bigSpenders.execute(dataSource).map((c) => c.name),
);
console.log(
  "any active in Munich",
  anyMunichActive.execute(dataSource).map((c) => c.name),
);
```

Compiled with `npx tsc --noEmit --strict query-object.ts`, which reported no
errors, and separately transpiled and run with `npx tsx query-object.ts`;
output confirmed as `big spenders [ 'Reyes' ]` and
`any active in Munich [ 'Reyes', 'Vogel' ]`, demonstrating that deriving
`bigSpenders` from `base` never mutated `base`, since `anyMunichActive`
(the same reference as `base`) still returns both Munich-active rows.

### Python. Tree-of-objects Interpreter variant

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Customer:
    id: int
    name: str
    city: str
    active: bool
    orders: int


class Criterion:
    def matches(self, customer: Customer) -> bool:
        raise NotImplementedError


@dataclass(frozen=True)
class FieldEquals(Criterion):
    field: str
    value: object

    def matches(self, customer: Customer) -> bool:
        return getattr(customer, self.field) == self.value


@dataclass(frozen=True)
class FieldAtLeast(Criterion):
    field: str
    minimum: int

    def matches(self, customer: Customer) -> bool:
        return getattr(customer, self.field) >= self.minimum


@dataclass(frozen=True)
class And(Criterion):
    left: Criterion
    right: Criterion

    def matches(self, customer: Customer) -> bool:
        return self.left.matches(customer) and self.right.matches(customer)


class CustomerQuery:
    def __init__(self, root: Criterion | None = None):
        self._root = root

    def where(self, criterion: Criterion) -> "CustomerQuery":
        new_root = criterion if self._root is None else And(self._root, criterion)
        return CustomerQuery(new_root)

    def execute(self, data_source: Iterable[Customer]) -> list[Customer]:
        if self._root is None:
            return list(data_source)
        return [row for row in data_source if self._root.matches(row)]


data_source = [
    Customer(1, "Reyes", "Munich", True, 12),
    Customer(2, "Klein", "Munich", False, 3),
    Customer(3, "Ortiz", "Berlin", True, 7),
    Customer(4, "Vogel", "Munich", True, 1),
]

base = CustomerQuery().where(FieldEquals("city", "Munich")).where(
    FieldEquals("active", True)
)
big_spenders = base.where(FieldAtLeast("orders", 5))

print("big spenders", [c.name for c in big_spenders.execute(data_source)])
print("base still independent", [c.name for c in base.execute(data_source)])
```

Run with `python3 query_object.py`; output confirmed as
`big spenders ['Reyes']` and `base still independent ['Reyes', 'Vogel']`,
confirming `where` on `base` returns a new `CustomerQuery` wrapping a new
`And` node rather than mutating the tree `base` still holds.

### Java. Criteria-style, JPA-flavoured builder over a plain in-memory list

```java
import java.util.ArrayList;
import java.util.List;
import java.util.function.Predicate;

public class QueryObjectDemo {

    record Customer(int id, String name, String city, boolean active, int orders) {}

    interface Criterion extends Predicate<Customer> {}

    static Criterion cityEquals(String city) {
        return c -> c.city().equals(city);
    }

    static Criterion activeEquals(boolean active) {
        return c -> c.active() == active;
    }

    static Criterion ordersAtLeast(int min) {
        return c -> c.orders() >= min;
    }

    static final class CustomerQuery {
        private final List<Criterion> criteria;

        private CustomerQuery(List<Criterion> criteria) {
            this.criteria = criteria;
        }

        static CustomerQuery all() {
            return new CustomerQuery(new ArrayList<>());
        }

        CustomerQuery where(Criterion criterion) {
            List<Criterion> next = new ArrayList<>(this.criteria);
            next.add(criterion);
            return new CustomerQuery(next);
        }

        List<Customer> execute(List<Customer> dataSource) {
            List<Customer> result = new ArrayList<>();
            for (Customer row : dataSource) {
                boolean matchesAll = true;
                for (Criterion criterion : criteria) {
                    if (!criterion.test(row)) {
                        matchesAll = false;
                        break;
                    }
                }
                if (matchesAll) {
                    result.add(row);
                }
            }
            return result;
        }
    }

    public static void main(String[] args) {
        List<Customer> dataSource = List.of(
            new Customer(1, "Reyes", "Munich", true, 12),
            new Customer(2, "Klein", "Munich", false, 3),
            new Customer(3, "Ortiz", "Berlin", true, 7),
            new Customer(4, "Vogel", "Munich", true, 1)
        );

        CustomerQuery base = CustomerQuery.all()
            .where(cityEquals("Munich"))
            .where(activeEquals(true));

        CustomerQuery bigSpenders = base.where(ordersAtLeast(5));

        System.out.println("big spenders " + bigSpenders.execute(dataSource));
        System.out.println("base still independent " + base.execute(dataSource));
    }
}
```

Compiled and run with `javac QueryObjectDemo.java && java QueryObjectDemo`;
output confirmed as `big spenders [Customer[id=1, name=Reyes, city=Munich,
active=true, orders=12]]` followed by `base still independent` and a list of both
the Reyes and Vogel records, confirming the same independence-of-derived-
query property as the TypeScript and Python examples.

A fourth language was intentionally not included. Go's typical idiom for this
kind of composable filter is a functional-options-style slice of closures
very close to the named, closure-based variant already described in
dimension 8, and would add a fourth example without demonstrating a
structurally distinct implementation choice from the three above; Rust and
Swift were left out for the same reason of marginal value once three
genuinely different implementation variants, string-free immutable chaining,
an explicit criterion tree, and a Criteria-API-flavoured builder, were each
already represented.
