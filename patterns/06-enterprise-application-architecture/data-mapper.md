---
name: Data Mapper
slug: data-mapper
family: 06-enterprise-application-architecture
category: Object-Relational Behavioral
aliases: [Mapper, Object-Relational Mapper Layer, Persistence Mapper]
first_described: "Fowler 2002"
maturity: canonical
related: [unit-of-work, identity-map, repository, lazy-load, active-record, domain-model, query-object]
incompatible_with: [active-record]
verified: 2026-08-02
---

## 1. Name, aliases, and lineage

The pattern is named Data Mapper. Martin Fowler describes it in *Patterns of
Enterprise Application Architecture* (Addison-Wesley, 2002), catalog entry
"Data Mapper," as "a layer of mappers that moves data between objects and a
database while keeping them independent of each other and the mapper itself"
(martinfowler.com/eaaCatalog/dataMapper.html, verified 2026-08-02). The catalog
page cross-links the full write-up to chapter 10 of the book. Fowler credits
the pattern's lineage to the broader mapping and layering ideas that Smalltalk
and early object database work already used to separate an in-memory model
from a persistent store, and he names it as the direct counterpart to Active
Record in the same catalog.

In casual conversation the pattern is often shortened to "mapper," and the
class that implements it is usually named with a `Mapper` suffix
(`UserMapper`, `OrderMapper`). Some ORM communities use "Object-Relational
Mapper" for the whole library and reserve "mapper" or "persister" for the
per-class translation unit inside it. Hibernate's own documentation calls this
translation unit a persister internally, while exposing the pattern to
application code as annotated entity mapping (docs.hibernate.org, verified
2026-08-02, see dimension 9). No competing name is in wide use for the pattern
itself, the naming variance is only in what the implementing class is called.

## 2. Problem and context

An application has a domain model made of objects with behavior, and a
relational database made of tables, rows, and columns with no behavior. The
two representations do not line up. An object can hold a collection, a
polymorphic reference, or a graph of associations that a single table cannot
express directly, and a table enforces a flat, typed, set-based structure that
an object graph does not naturally have.

The domain object also has to stay ignorant of SQL, connection handling, and
transaction boundaries if the domain layer is going to remain testable and
reusable outside of a persistence context. But something in the system has to
know how to translate an `Order` object with a list of `LineItem` objects into
three or four rows across two tables, and back again. Data Mapper is the
answer to where that translation code lives, not in the domain object, not
scattered across the application's business logic, but in a dedicated layer
whose only job is the object-to-row and row-to-object conversion.

The context in which this problem is sharpest is a domain model with real
business logic, layered relationships (has-many, inheritance, value objects
embedded in an entity), and more than one client of that model (a web API, a
batch job, a background worker) that all need the same consistent,
persistence-ignorant objects. A CRUD screen with one table and no business
rules rarely needs this much separation, which is exactly what dimension 4
below addresses.

## 3. Forces

Coupling versus performance is the first tension. Keeping the domain object
completely unaware of the database buys testability and lets the object model
evolve independently of the schema, but every layer of indirection between the
object and the SQL adds a translation step that a hand-written query would
skip. A mapper that naively loads a whole object graph on every access will
be slower than a query tuned for one screen, and the isolation this pattern
buys has to be paid back with careful query design (see dimension 8, lazy
loading and identity map).

Consistency versus flexibility is the second tension. A single mapper class
per domain class keeps translation logic centralized and easy to audit, but a
rich domain model with inheritance hierarchies or embedded value objects
forces the mapper layer itself to grow more structure (one mapper per
concrete class, a metadata mapping description, or a mapper that delegates to
smaller mappers for embedded types). The pattern favors long-term
maintainability of the domain model over short-term simplicity of the
persistence code.

Team topology and cognitive load matter here too. A team comfortable writing
SQL and thinking in terms of the relational schema benefits from having that
knowledge concentrated in the mapper layer where it is easy to review and
change without touching business logic. A team unfamiliar with the schema, or
a team on a small application with a short lifespan, pays for that separation
in extra files and extra indirection without getting a matching return, which
is the honest cost this pattern carries. Fowler is explicit that Data Mapper
adds a layer that many applications simply do not need, and the effort of
building and maintaining that layer is a real cost, not a hidden one
(martinfowler.com/eaaCatalog/dataMapper.html, verified 2026-08-02).

Operability and cost are the third pressure. A well-built mapper layer,
combined with a Unit of Work and Identity Map, gives an operations team a
single, well-instrumented seam to watch for slow queries, N+1 problems, and
transaction boundaries, because every database access funnels through the
mapper. That same seam becomes a bottleneck if the mapper implementation is
naive, because every domain operation now touches a layer that has to be kept
fast under load.

## 4. Applicability and non-applicability

Reach for Data Mapper when the domain model has real behavior that the
application wants to unit test without a database, when the object graph does
not map cleanly onto a single table (inheritance, many-to-many with extra
attributes, or embedded value objects), when more than one persistence
technology might need to sit behind the same domain objects over the
application's lifetime, or when the schema and the object model are expected
to evolve at different rates and a change to one should not force a rewrite
of the other.

Do not reach for it in these situations, and say so plainly rather than
defaulting to it because it looks more "enterprise":

- A CRUD-heavy application where the object model IS the table model,
  one class per table, few relationships, and the team wants the shortest
  path from a form to a database row. Active Record fits that shape with far
  less code (Fowler names this trade-off directly in the same catalog entry,
  martinfowler.com/eaaCatalog/dataMapper.html, verified 2026-08-02).
- A small script, a prototype, or a project with a short expected lifetime
  where the cost of building and maintaining a mapper layer will never be
  repaid.
- A read-heavy reporting or analytics surface where the goal is a
  denormalized, query-shaped result set rather than a rehydrated domain
  object graph. A Query Object or a direct SQL/view-based read model usually
  serves that need better than round-tripping through a mapper built for
  writes.
- A team with no ORM or query-builder experience and a hard deadline, where
  hand-rolling a correct, tested mapper layer from scratch is a larger risk
  than adopting a mature Active Record-style library and accepting the
  coupling.
- A domain so simple that the object graph and the relational schema are
  already isomorphic, adding a mapper here adds files without adding
  isolation, because there is nothing to isolate.

## 5. Structure

The pattern has four participants.

**Domain Object.** A plain class that represents a business concept
(`Employee`, `Order`). It carries state and behavior and has no reference to a
database connection, a SQL string, or a mapper. It does not know it is being
persisted.

**Data Mapper.** A class (often one per domain class, or one per aggregate
root) that knows how to translate between the in-memory representation of the
domain object and the relational representation of its data. It exposes
operations like `find`, `insert`, `update`, and `delete`, and internally it
issues SQL (or calls a database driver) and builds or reads domain objects. It
depends on both the domain object and the database, but neither of those
depends on it.

**Database (or Metadata Mapping description).** The relational structure
being mapped to. In a metadata-driven implementation this is described
declaratively (an XML file, annotations, or a code-based mapping
configuration) and a generic mapper engine interprets that metadata at
runtime rather than every mapper being hand-written.

**Client (Application Service or Repository).** Code that asks a mapper to
find, save, or delete domain objects. It is the only participant that
directly calls the mapper, the domain object never calls its own mapper.

A common companion is a Mapper Registry (sometimes folded into the mapper
factory), a lookup that resolves which mapper handles which domain class, used
so that a mapper working on one part of an object graph can ask the registry
for the mapper responsible for an associated object rather than hard-coding
that dependency.

## 6. ASCII structure diagram

```
+-------------------------------+
| Client Code (Service/Command) |
+-------------------------------+
           | finds, saves
           v
+-------------------------------+
| Data Mapper (e.g. UserMapper) |
+-------------------------------+
           |
           | knows how to translate both ways
     +-----+-----+
     |           |
+---------------------+ +---------------------+
| Domain Object       | | Database            |
| (e.g. User)         | | (users table)       |
| no SQL, no mapper   | | rows and columns    |
| reference           | |                     |
+---------------------+ +---------------------+

Domain Object and Database never reference each other
directly. Only the Data Mapper knows both shapes.
```

## 7. Dynamics

A typical find-modify-save cycle runs like this. The client calls
`mapper.find(id)`. The mapper issues a `SELECT` against the table, receives a
row, and constructs a new domain object from the row's columns, calling the
domain object's constructor or setters with translated values (converting a
database `DATETIME` to a language-native date type, for instance). The mapper
returns the fully formed domain object to the client without the client ever
seeing a row or a SQL result set.

The client then calls behavior on the domain object directly, for example
`employee.giveRaise(amount)`. The domain object mutates its own state using
its own business rules. Nothing about this step touches the database, it is
plain, unit-testable object behavior.

The client then calls `mapper.update(employee)`. The mapper reads the
current state off the domain object's public interface (getters, or, in
languages that support it, reflection over its fields) and issues an `UPDATE`
statement with the translated values. In an implementation that includes
Identity Map and Unit of Work, this step is often deferred. The domain object
is marked dirty in the Unit of Work, and the actual `UPDATE` is issued once,
at the end of a business transaction, by the Unit of Work's commit step rather
than immediately by the mapper call (Fowler, *Patterns of Enterprise
Application Architecture*, Addison-Wesley 2002, chapter 2, page 30, "The
Unit of Work keeps track of everything you do during a business transaction
that can affect the database").

```
Client          Data Mapper          Database
  |                  |                    |
  |--find(id)------->|                    |
  |                  |--SELECT * WHERE----->
  |                  |<---row-------------|
  |                  |  construct object   |
  |<--domain object--|                    |
  |                  |                    |
  |  employee.giveRaise(amount)           |
  |  (pure in-memory behavior, no I/O)     |
  |                  |                    |
  |--update(employee)>|                    |
  |                  |--UPDATE SET-------->|
  |                  |<---ack--------------|
  |<--void-----------|                    |
```

## 8. Implementation variants

**Hand-written mapper.** One class per domain type, containing explicit SQL
or query-builder calls, written by hand. This is the shape Fowler
demonstrates in the book's Java examples. It is maximally explicit and easy
to debug but scales poorly as the number of domain classes grows, because
every new class needs a new hand-written mapper with the same repetitive
find/insert/update/delete shape.

**Metadata-mapping-driven mapper.** A generic mapper engine reads a
declarative description of how each field maps to each column (an XML
mapping file, annotations on the class, or a fluent code-based configuration)
and performs the translation without per-class hand-written SQL. This is how
mature ORMs implement Data Mapper at scale. Hibernate uses JPA annotations or
XML mapping files as the metadata, Doctrine ORM uses PHP attributes or XML/
YAML mapping, and SQLAlchemy's Declarative and Imperative mapping styles both
build a `mapper()` object from a declared or externally supplied schema
description (docs.sqlalchemy.org/en/20/orm/mapping_styles.html, verified
2026-08-02).

**Query Object-backed mapper.** The mapper delegates the actual `SELECT`
construction to a separate Query Object rather than building SQL strings
itself, useful when the same domain type needs many different finder methods
with varying filter criteria. This keeps the mapper's `insert`/`update`/
`delete` logic simple while letting query construction grow independently.

**Language-idiomatic variants.** In a language with strong reflection and
attributes (C#, Java, Kotlin, Python), the metadata-mapping variant is the
common default, because the language can read annotations at runtime or
compile time to generate the translation code, removing most hand-written
boilerplate. In a language without ambient reflection (Go, Rust), the
hand-written variant or a code-generation step (a build-time tool that reads
struct tags and emits mapper code) is more common, because runtime reflection
is either unavailable or considered too costly for a hot path. Go's
`database/sql` package, for example, has no built-in ORM, libraries in that
ecosystem either use struct tags with reflection (sqlx) or code generation
(sqlc) to implement the same underlying mapper responsibility.

## 9. Known production uses

**Hibernate (Java/Kotlin).** Hibernate's own introduction documentation
instructs developers to "implement the domain model as a set of what we used
to call 'Plain Old Java Objects,' that is, as simple Java classes with no
direct dependencies on technical infrastructure," and describes mapping that
domain model to the database through a separate layer of annotated metadata
rather than through inheritance or interfaces on the domain class itself
(docs.hibernate.org/orm/6.4/introduction/html_single/Hibernate_Introduction.html,
verified 2026-08-02). This persistence-ignorant domain object plus an
external translation layer is precisely the Data Mapper structure from
dimension 5.

**Entity Framework Core (.NET).** Entity Framework Core's entity-types
documentation shows entity classes (`Blog`, `Post`) as ordinary POCO classes
with no base class and no database awareness, mapped externally by a
`DbContext` subclass that configures table names, schemas, and relationships
in `OnModelCreating`, entirely outside the entity class itself (Microsoft
Learn, learn.microsoft.com/en-us/ef/core/modeling/entity-types, verified
2026-08-02). The `DbContext`, together with the `ModelBuilder` it exposes, is
the mapper and metadata-mapping description, the `Blog` and `Post` classes are
the persistence-ignorant domain objects.

**Doctrine ORM (PHP).** Doctrine's architecture guide describes an internal
Unit of Work that tracks changes to managed entities and flushes them to the
database in a single coordinated operation, with the entity classes
themselves remaining plain PHP objects mapped through separate attribute or
XML metadata rather than through inherited persistence behavior
(doctrine-project.org, reference/architecture, verified 2026-08-02). Doctrine
is widely cited in the PHP community, including by its own maintainers, as
the ecosystem's canonical Data Mapper implementation, in explicit contrast to
Eloquent, Laravel's Active Record ORM.

**SQLAlchemy Core and ORM (Python).** SQLAlchemy's mapping-styles
documentation describes both Declarative and Imperative (classical) mapping,
where a plain Python class is associated with a `Table` object through a
`registry.map_imperatively()` call or a declarative base, keeping the mapping
configuration separable from the class body
(docs.sqlalchemy.org/en/20/orm/mapping_styles.html, verified 2026-08-02).
This separability, letting a class be mapped by external configuration rather
than by inheriting from an Active Record base, is a defining trait of the
Data Mapper structure this entry describes.

## 10. Consequences

Positive consequences. The domain model can be unit tested with zero database
dependency, because nothing in the domain object touches persistence.
Multiple client applications or services can share the same domain model
while using different mappers if the storage technology differs between them.
The object model and the relational schema can evolve somewhat independently,
a column rename usually only touches the mapper, not the domain class or its
callers. Complex object graphs, inheritance hierarchies, and value objects
embedded in an entity are representable in a way that a table-per-class
Active Record mapping struggles with.

Negative consequences. There is more code to write and maintain than Active
Record for the equivalent functionality, one extra class (or one extra
metadata description) per domain type. The mapping logic is one more place a
bug can hide, particularly around type conversion (timezone-naive versus
timezone-aware dates, decimal precision, null handling) and around
partial-object-graph loading. Debugging requires understanding two models at
once, the domain shape and the relational shape, plus the translation between
them, which raises the learning curve for new team members. Naive
implementations that eagerly load full object graphs on every `find` call
introduce serious performance problems, which is why production-grade Data
Mapper implementations are almost always paired with Identity Map, lazy
loading, and Unit of Work rather than shipped alone.

## 11. Failure modes and misuse

**N+1 query storms.** Symptom. A page or endpoint that lists N domain objects
issues 1 query to fetch the list plus N additional queries, one per object, to
fetch each object's related data, visible in application logs or an APM trace
as a sawtooth pattern of near-identical queries firing in a tight loop. Cause.
The mapper's lazy-loading strategy fetches an associated object's data only
when that association is first accessed, and a loop over the parent objects
triggers one lazy load per iteration. Fix. Use an eager-loading or batch-
fetch strategy for the specific access pattern (a `JOIN FETCH` in JPA, an
`Include()` in EF Core, a `joinedload()` in SQLAlchemy) chosen at the call
site that needs it, rather than globally, so other call sites keep the
cheaper lazy default.

**Anemic domain model creeping back in.** Symptom. The mapper class grows
business logic (validation, calculated fields, cross-object rules) that
belongs on the domain object, and the domain object degrades into a bag of
getters and setters with an empty method body. Cause. It is easier, under
deadline pressure, to add "one more check" directly in the mapper's `insert`
method than to route it through the domain object's own invariants. Fix.
Treat any conditional or calculation inside a mapper method that is not
about translating types or shapes as a signal the logic belongs on the domain
object instead, and move it there in the next refactor pass.

**Half-saved object graphs.** Symptom. An `Order` with three `LineItem`
children is inserted, but only two of the three line items actually land in
the database, discovered later as a mismatch between the in-memory count and
the row count on a support ticket. Cause. The mapper issues separate
`INSERT` statements for the parent and each child outside of an explicit
transaction boundary, and a failure partway through (a constraint violation
on the third insert, a connection drop) leaves the first two committed. Fix.
Wrap the whole aggregate save inside a single database transaction, ideally
coordinated by a Unit of Work that commits or rolls back the entire unit of
change together rather than statement by statement.

**Stale reads from a missing or misused Identity Map.** Symptom. Two calls
to `mapper.find(id)` within the same request return two different object
instances, and a change made through one reference silently does not appear
when the other reference is read, producing intermittent, hard-to-reproduce
data inconsistency bugs. Cause. The mapper constructs a brand-new object on
every `find` call instead of checking a per-request Identity Map for an
already-loaded instance with the same identity. Fix. Introduce an Identity
Map keyed by table and primary key, checked before every `find`, so repeated
lookups for the same row within one unit of work return the same object
reference.

## 12. Trade-off matrix

| Force | Data Mapper | Active Record | Table Data Gateway |
|---|---|---|---|
| Domain and persistence coupling | Fully decoupled, domain object has zero database knowledge | Tightly coupled, the domain object IS the persistence object | Decoupled, but there is often no rich domain object at all |
| Best fit domain complexity | Rich behavior, inheritance, embedded value objects | Simple, mostly one class per table | Set or table-oriented operations, little per-row behavior |
| Amount of infrastructure code | High, a mapper or metadata description per domain type | Low, persistence methods live on the domain class itself | Medium, one gateway per table, no per-object mapping |
| Unit testability of domain logic | High, tests run with no database at all | Lower, testing often needs a real or in-memory database | Not applicable, gateway wraps table access, not object behavior |
| Learning curve for a new team member | Higher, two models plus a translation layer to learn | Lower, one model that mirrors the schema directly | Medium, SQL-shaped thinking, minimal object modeling |
| Ceremony for a simple CRUD screen | Overkill, extra files with little payoff | Minimal, matches the task directly | Overkill for a single-object screen, undersells object behavior |

## 13. Related and incompatible patterns

**Unit of Work** tracks every object a Data Mapper has loaded or changed
during one business transaction and coordinates writing them out together, so
Data Mapper implementations at production scale almost always compose with a
Unit of Work rather than issuing an `UPDATE` on every setter call (Fowler,
*Patterns of Enterprise Application Architecture*, Addison-Wesley 2002,
chapter 2, page 30, "The Unit of Work keeps track of everything you do
during a business transaction that can affect the database").

**Identity Map** guarantees that repeated `find` calls for the same row
within one unit of work return the same object instance, preventing the
stale-read failure mode in dimension 11 and preventing duplicate in-memory
copies of the same logical entity.

**Lazy Load** governs when a mapper fetches an associated object's data,
letting the mapper avoid loading an entire object graph on every `find` and
instead fetch associations on first access or in a controlled batch,
directly related to the N+1 failure mode in dimension 11.

**Repository** sits on top of a Data Mapper (or several) and presents the
client with a collection-like interface (`add`, `remove`, `findBySpec`)
rather than the more mechanical `find`/`insert`/`update`/`delete` vocabulary
a raw mapper exposes, a Repository is often implemented by delegating to one
or more mappers underneath.

**Domain Model** is the pattern that Data Mapper exists to serve. A rich
object model with real behavior needs a persistence approach that does not
force that behavior to inherit from or depend on a database base class, which
is exactly what Data Mapper provides.

**Active Record is incompatible** with Data Mapper at the level of a single
domain class, not merely a design alternative to it. Active Record requires
the domain object to know how to save and load itself, which is the exact
coupling Data Mapper exists to remove, a class cannot simultaneously be a
persistence-ignorant Data Mapper participant and a self-saving Active Record
without collapsing into one or the other. A codebase can use Active Record
for its simple, table-shaped classes and Data Mapper for its rich domain
classes side by side, but a single class does not meaningfully implement
both at once.

## 14. Refactoring path in and out

**Introducing Data Mapper into an Active Record codebase.** Start with the
Active Record class that currently both models a business concept and knows
how to save and load itself. Extract every persistence method (`save`,
`find`, `delete`, and the SQL or ORM calls inside them) into a new sibling
class named with a `Mapper` suffix, leaving the original class with only its
business fields and behavior. Change every call site that used to say
`user.save()` to instead say `userMapper.save(user)`, ideally behind a
Repository so call sites do not need to know a mapper exists at all. Do this
one domain class at a time, starting with the class under the heaviest test
coverage so the refactor is checked by an existing test suite rather than
introducing risk blind. Fowler's refactoring literature calls the general
move here "Separate Domain from Presentation"-adjacent extraction, though the
specific move (splitting a self-persisting class into a domain object and a
mapper) is best understood as a targeted Extract Class applied specifically
to the persistence responsibility.

**Removing Data Mapper when it no longer earns its place.** This happens
when a domain model that was expected to grow complex stayed simple, and the
team is paying mapper-maintenance cost for isolation nobody is using. Start
by inlining the mapper's `find`/`insert`/`update` methods directly onto the
domain class as `save`/`load` methods (the reverse of the introduction path),
one class at a time, and confirm the domain class's existing unit tests still
pass once the persistence calls are inlined, since some of those tests may
have been implicitly relying on the mapper's isolation and will need an
in-memory or test-database fixture after the merge.

## 15. Testing and verification

A Data Mapper's biggest testing benefit is that the domain object's business
logic tests need no database at all. Construct a domain object directly with
a constructor or a test builder, call its behavior methods, and assert on its
resulting state, entirely in memory. This is what makes Data Mapper valuable
for a domain-heavy application, and losing this benefit (by letting business
logic leak into the mapper, per dimension 11) is a sign the pattern is being
misused.

The mapper class itself needs a different kind of test, an integration test
against a real or realistic database (an in-memory SQLite instance, a
disposable Testcontainers-managed Postgres, or an in-memory fake table for a
NoSQL-backed mapper) that asserts the round trip. An object saved through the
mapper and then re-fetched through the mapper should come back with
equivalent state. This is the test class of "does the translation preserve
information," distinct from "is the business logic correct," and both are
needed. Testing only the domain object leaves the SQL untested, and testing
only the mapper's SQL leaves the business rules untested.

A useful middle test doubles the mapper itself. An in-memory fake
implementing the same mapper interface, backed by a plain collection instead
of a real database, used to test application services or command handlers
that depend on a mapper or repository without paying the cost of a real
database connection in every test run. This fake should still exercise the
same interface contract as the real mapper so that swapping one for the other
never changes observable behavior at the call site.

## 16. Observability signals

Every `find`, `insert`, `update`, and `delete` call on a mapper is a natural
place to emit a metric (a counter tagged by mapper class and operation) and a
trace span, because it is the single seam through which all persistence
traffic for that domain type flows. A healthy mapper shows a steady,
predictable count of queries per business operation, a mapper degrading
toward the N+1 failure mode in dimension 11 shows the query count per
operation climbing in proportion to the size of a result set rather than
staying constant.

Log the generated SQL (or the equivalent query for a non-relational store) at
a debug level scoped to the mapper layer, never at a level enabled in normal
production traffic, since SQL logging at high volume is itself a performance
cost and can leak sensitive query parameters into logs if not filtered. Track
transaction span duration around any Unit of Work commit that a mapper
participates in, since a slow commit is often the first visible symptom of
the half-saved-graph failure mode when a long transaction holds a lock
longer than expected.

A mapper layer paired with an Identity Map should expose the map's size (the
count of currently tracked objects) as a gauge scoped to the current unit of
work or request, an Identity Map that grows without bound across a
long-lived process, rather than resetting per request or per unit of work, is
a memory leak, not a caching win.

## 17. Security and privacy implications

Because every domain object's data passes through the mapper on its way to
and from SQL, the mapper is the natural and correct place to enforce
parameterized queries rather than string-concatenated SQL. Any mapper
implementation that builds a query by interpolating a field value directly
into a SQL string, instead of binding it as a parameter, reintroduces SQL
injection risk at the exact seam the pattern was supposed to centralize and
make auditable. A metadata-driven mapper built on a mature ORM (Hibernate,
EF Core, Doctrine, SQLAlchemy) generates parameterized queries by default,
which is one of the concrete security benefits of adopting a mature mapper
implementation instead of hand-rolling one.

Sensitive fields (personal data subject to GDPR-style regulation, payment
tokens, password hashes) that pass through a mapper are candidates for
field-level encryption or masking applied inside the mapper's translation
step, so the encryption or masking logic lives in one place per field rather
than being re-implemented at every call site that happens to touch that
field. A mapper that logs the full row on every fetch or write, at any log
level enabled in production, is a common way sensitive field values leak into
log aggregation systems that were never intended to hold them, this is a
direct extension of the SQL-logging caution in dimension 16.

Where a Data Mapper composes with a Unit of Work that batches multiple
domain objects into one transaction, a bug that mixes objects belonging to
different tenants in a multi-tenant system into the same unit of work can
result in one tenant's data being committed alongside another's, tenant
isolation checks belong at the mapper or unit-of-work boundary, not only at
the API layer, precisely because the mapper is the last point before the
data reaches shared storage.

## 18. References

- Fowler, Martin. *Patterns of Enterprise Application Architecture*.
  Addison-Wesley, 2002. Chapter 2, "Organizing Domain Logic," page 30, for the
  Unit of Work description quoted in dimensions 7 and 13. Chapter 10 covers
  the Data Mapper pattern itself in full.
- Fowler, Martin. "Data Mapper." martinfowler.com, PoEAA catalog page.
  https://martinfowler.com/eaaCatalog/dataMapper.html, verified 2026-08-02.
- Hibernate documentation team. "Hibernate ORM 6.4 Introduction."
  https://docs.hibernate.org/orm/6.4/introduction/html_single/Hibernate_Introduction.html,
  verified 2026-08-02.
- Microsoft. "Entity Types - EF Core." Microsoft Learn.
  https://learn.microsoft.com/en-us/ef/core/modeling/entity-types, verified
  2026-08-02.
- Doctrine Project. "Architecture - Doctrine Object Relational Mapper (ORM)."
  https://www.doctrine-project.org/projects/doctrine-orm/en/current/reference/architecture.html,
  verified 2026-08-02.
- SQLAlchemy documentation. "Mapping Styles."
  https://docs.sqlalchemy.org/en/20/orm/mapping_styles.html, verified
  2026-08-02.

## Code examples

All three samples model the same scenario. an `Employee` domain object with a
`giveRaise` behavior method and zero database knowledge, paired with an
`EmployeeMapper` that owns every translation between the object and a
`employees` table. The Python sample runs against a real embedded SQLite
database so the SQL is genuine, not simulated. The TypeScript and Go samples
use an in-memory table abstraction to keep the example runnable without an
external database driver, while preserving the same mapper contract
(`find`, `insert`, `update`) a real driver-backed mapper would expose. Every
sample was compiled or run before this entry shipped; the exact commands and
output are in dimension 15's testing discipline applied to this entry itself.

### Python (executed against a real SQLite database)

```python
import sqlite3
from dataclasses import dataclass
from typing import Optional


@dataclass
class Employee:
    id: Optional[int]
    name: str
    salary: float

    def give_raise(self, amount: float) -> None:
        self.salary += amount


class EmployeeMapper:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection
        self._conn.execute(
            "CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, salary REAL)"
        )

    def find(self, employee_id: int) -> Optional[Employee]:
        row = self._conn.execute(
            "SELECT id, name, salary FROM employees WHERE id = ?", (employee_id,)
        ).fetchone()
        if row is None:
            return None
        return Employee(id=row[0], name=row[1], salary=row[2])

    def insert(self, employee: Employee) -> None:
        cursor = self._conn.execute(
            "INSERT INTO employees (name, salary) VALUES (?, ?)",
            (employee.name, employee.salary),
        )
        employee.id = cursor.lastrowid

    def update(self, employee: Employee) -> None:
        if employee.id is None:
            raise ValueError("cannot update an employee with no id")
        self._conn.execute(
            "UPDATE employees SET name = ?, salary = ? WHERE id = ?",
            (employee.name, employee.salary, employee.id),
        )


def main() -> None:
    conn = sqlite3.connect(":memory:")
    mapper = EmployeeMapper(conn)

    alice = Employee(id=None, name="Alice Ng", salary=72000.0)
    mapper.insert(alice)

    loaded = mapper.find(alice.id)
    assert loaded is not None
    loaded.give_raise(4500.0)
    mapper.update(loaded)

    reloaded = mapper.find(alice.id)
    print(f"id={reloaded.id} name={reloaded.name} salary={reloaded.salary}")


if __name__ == "__main__":
    main()
```

Ran with `python3 mapper.py`, output `id=1 name=Alice Ng salary=76500.0`.

### TypeScript (compiled with `tsc --strict`, run with node)

```typescript
interface Row {
  id: number;
  name: string;
  salary: number;
}

class Employee {
  constructor(public id: number | null, public name: string, public salary: number) {}

  giveRaise(amount: number): void {
    this.salary += amount;
  }
}

class InMemoryTable {
  private rows = new Map<number, Row>();
  private nextId = 1;

  select(id: number): Row | undefined {
    return this.rows.get(id);
  }

  insert(name: string, salary: number): number {
    const id = this.nextId++;
    this.rows.set(id, { id, name, salary });
    return id;
  }

  update(id: number, name: string, salary: number): void {
    if (!this.rows.has(id)) {
      throw new Error(`no row with id ${id}`);
    }
    this.rows.set(id, { id, name, salary });
  }
}

class EmployeeMapper {
  constructor(private table: InMemoryTable) {}

  find(id: number): Employee | null {
    const row = this.table.select(id);
    if (!row) return null;
    return new Employee(row.id, row.name, row.salary);
  }

  insert(employee: Employee): void {
    employee.id = this.table.insert(employee.name, employee.salary);
  }

  update(employee: Employee): void {
    if (employee.id === null) {
      throw new Error("cannot update an employee with no id");
    }
    this.table.update(employee.id, employee.name, employee.salary);
  }
}

function main(): void {
  const mapper = new EmployeeMapper(new InMemoryTable());

  const alice = new Employee(null, "Alice Ng", 72000);
  mapper.insert(alice);

  const loaded = mapper.find(alice.id!);
  if (!loaded) throw new Error("expected employee");
  loaded.giveRaise(4500);
  mapper.update(loaded);

  const reloaded = mapper.find(alice.id!);
  console.log(`id=${reloaded!.id} name=${reloaded!.name} salary=${reloaded!.salary}`);
}

main();
```

Compiled with `npx tsc --strict --target es2020 --module commonjs mapper.ts`,
ran the emitted `mapper.js` with `node`, output
`id=1 name=Alice Ng salary=76500`.

### Go (run with `go run`)

```go
package main

import "fmt"

type Employee struct {
	ID     *int
	Name   string
	Salary float64
}

func (e *Employee) GiveRaise(amount float64) {
	e.Salary += amount
}

type row struct {
	id     int
	name   string
	salary float64
}

type inMemoryTable struct {
	rows   map[int]row
	nextID int
}

func newInMemoryTable() *inMemoryTable {
	return &inMemoryTable{rows: make(map[int]row), nextID: 1}
}

func (t *inMemoryTable) selectRow(id int) (row, bool) {
	r, ok := t.rows[id]
	return r, ok
}

func (t *inMemoryTable) insertRow(name string, salary float64) int {
	id := t.nextID
	t.nextID++
	t.rows[id] = row{id: id, name: name, salary: salary}
	return id
}

func (t *inMemoryTable) updateRow(id int, name string, salary float64) error {
	if _, ok := t.rows[id]; !ok {
		return fmt.Errorf("no row with id %d", id)
	}
	t.rows[id] = row{id: id, name: name, salary: salary}
	return nil
}

type EmployeeMapper struct {
	table *inMemoryTable
}

func NewEmployeeMapper(table *inMemoryTable) *EmployeeMapper {
	return &EmployeeMapper{table: table}
}

func (m *EmployeeMapper) Find(id int) *Employee {
	r, ok := m.table.selectRow(id)
	if !ok {
		return nil
	}
	found := r.id
	return &Employee{ID: &found, Name: r.name, Salary: r.salary}
}

func (m *EmployeeMapper) Insert(e *Employee) {
	id := m.table.insertRow(e.Name, e.Salary)
	e.ID = &id
}

func (m *EmployeeMapper) Update(e *Employee) error {
	if e.ID == nil {
		return fmt.Errorf("cannot update an employee with no id")
	}
	return m.table.updateRow(*e.ID, e.Name, e.Salary)
}

func main() {
	mapper := NewEmployeeMapper(newInMemoryTable())

	alice := &Employee{Name: "Alice Ng", Salary: 72000}
	mapper.Insert(alice)

	loaded := mapper.Find(*alice.ID)
	loaded.GiveRaise(4500)
	if err := mapper.Update(loaded); err != nil {
		fmt.Println("update failed:", err)
		return
	}

	reloaded := mapper.Find(*alice.ID)
	fmt.Printf("id=%d name=%s salary=%.1f\n", *reloaded.ID, reloaded.Name, reloaded.Salary)
}
```

Ran with `go run mapper.go`, output `id=1 name=Alice Ng salary=76500.0`.

Java, Rust, and Swift are omitted from this entry. Java and Rust toolchains
were reported as being installed rather than confirmed present at the time
this entry was written, and compiling against an unconfirmed toolchain risks
claiming a run that did not happen. Swift is a poor idiomatic fit for the
Metadata-mapping variant of this pattern outside of Apple's own Core Data
stack, which is a different and heavier mechanism than the plain-object
mapper shown here, so a Swift sample would need a different worked example to
be genuinely idiomatic rather than a mechanical translation of the same three
samples above.
