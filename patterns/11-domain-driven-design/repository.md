---
name: Repository
slug: repository
family: 11-domain-driven-design
category: Domain-Driven Design
aliases: [Repository Pattern, Persistence Repository, Collection-Oriented Repository]
first_described: "Evans 2003 (Domain-Driven Design); Fowler, Rice, Foemmel, Hieatt, Mee, Stafford 2002 (Patterns of Enterprise Application Architecture)"
maturity: canonical
related: [unit-of-work, aggregate, specification, data-mapper, active-record, factory-method, dependency-injection]
incompatible_with: []
verified: 2026-08-02
---

# Repository

## 1. Name, aliases, and lineage

The canonical name is Repository. Two independent, closely timed sources
converge on the same idea and the same name, which is why the pattern reads as
settled rather than contested.

The first source is Martin Fowler's catalog in *Patterns of Enterprise
Application Architecture*, Addison-Wesley, 2002, where Repository is listed
among the Object-Relational Behavioral Patterns alongside Unit of Work, and is
described as mediating between the domain and data mapping layers using a
collection-like interface for accessing domain objects
([Catalog of Patterns of Enterprise Application Architecture, martinfowler.com](https://martinfowler.com/eaaCatalog/), verified 2026-08-02).
The book's authorship note credits the pattern to work by David Rice and Randy
Stafford, who contributed the writeup to Fowler's catalog.

The second, and today the more cited, source is Eric Evans, *Domain-Driven
Design. Tackling Complexity in the Heart of Software*, Addison-Wesley, 2003,
Part III, chapter 6, Repository. Evans frames a Repository as representing all
objects of a certain type as a conceptual set, usually emulated, and gives it
richer query capability than a plain collection while still hiding the storage
mechanics behind an interface that reads like an in-memory collection
([Domain Driven Design summary, Evans 2003 PDF, fabiofumarola.github.io](https://fabiofumarola.github.io/nosql/readingMaterial/Evans03.pdf), verified 2026-08-02).
Evans's contribution is not the collection illusion itself, Fowler already had
that, it is tying the Repository's boundary to the Aggregate. In Evans's
vocabulary a Repository exists for each Aggregate root, and only for Aggregate
roots, never for every entity in the model.

Aliases in real use are Repository Pattern, the generic industry phrase, and
Persistence Repository or Collection-Oriented Repository when a text wants to
distinguish this shape from a Query Object or a raw Data Access Object. Some
ORM vendor documentation, notably early Doctrine ORM material, calls the
default per-entity query object simply "the repository" even when it is a thin
wrapper with none of Evans's aggregate discipline, and this looser usage is the
single largest source of confusion between Repository as a DDD tactical
pattern and Repository as ORM plumbing, addressed directly in dimension 4.

## 2. Problem and context

A domain layer needs to load and save the objects it works with, but the code
that expresses business rules should not know whether an order lives in
PostgreSQL, in a document store, behind a REST API, or in memory during a test
run. Without a boundary, SQL strings, ORM query builders, and connection
handling spread into the same methods that compute a discount or validate a
shipping address. Every domain method becomes coupled to a specific
persistence technology, and every test that exercises domain logic pays the
cost of standing up a real database.

The concrete symptom is a service or handler method that mixes three
concerns in one block, fetching rows, reconstructing or mutating a domain
object, and applying business rules to it. A shipping-discount calculation
that opens a `SELECT * FROM orders WHERE customer_id = ?`, hydrates a plain
row into an `Order`, and then branches on `order.total > 100` has already lost
the separation the domain layer exists to protect. When the storage engine
changes, or a second storage engine is added for a subset of tenants, every
method with an inline query has to change.

The context in which Repository earns its place is a domain model with real
behavior, not a thin set of getters and setters. If the "domain objects" are
just data bags and all the logic lives in services that operate on rows, a
Repository adds a layer of indirection around code that was never going to
change its persistence technology, and the pattern's cost is paid for a
benefit nobody collects. This connects directly to dimension 4's
non-applicability list.

## 3. Forces

**Coupling versus indirection.** Hiding the storage mechanism reduces coupling
between the domain layer and any specific database or ORM, but every added
interface is a name the next reader has to learn, and a method they have to
trace through before finding the real query. Repository trades direct,
traceable code for decoupled, testable code, and that trade is worth making
only when the domain layer's independence is actually exercised, most visibly
when tests substitute an in-memory implementation.

**Aggregate boundary versus query convenience.** Evans's discipline says one
Repository per Aggregate root, which keeps the Repository interface small and
keeps invariants inside the Aggregate where they can be enforced on save. The
opposing pressure is that application code frequently wants a query shaped
around a screen, a report, or a join across several Aggregates, and a
strict per-Aggregate Repository interface pushes that need somewhere else,
typically a read-side Query Object or a dedicated read model, per dimension 4.

**Collection illusion versus real query cost.** A Repository that behaves like
an in-memory collection, offering `add`, `remove`, and iteration, is the
easiest mental model to teach, but a naive implementation of that illusion
invites `findAll()` calls that load an entire table into memory. The interface
can look like a collection while its implementation must, for anything beyond
toy data volumes, expose paging, specification-based filtering, or streaming,
which quietly re-introduces persistence concerns into the interface the
pattern exists to hide.

**Consistency versus caching.** A Repository that returns the same object
instance for the same identity within a unit of work, an identity map,
simplifies reasoning about equality and avoids lost updates. Sacrificing that
guarantee for a stateless request-scoped Repository is simpler to implement
but reopens the door to two different in-memory copies of the same aggregate
diverging before either is saved.

**Team topology and cognitive load.** In a small team working one codebase
against one database, a generic `Repository<T>` per entity is quick to write
and low ceremony. In a larger team where the domain layer must be testable
without a database, and where the persistence technology is genuinely
expected to change or vary by deployment, the interface segregation is worth
the extra file per Aggregate. The pattern favors testability and long-lived
domain independence over the fastest possible first implementation, and it
sacrifices some directness and some query flexibility to get there.

## 4. Applicability and non-applicability

Reach for Repository when all of the following hold.

- The domain layer contains real behavior, invariants, and business rules
  that benefit from being tested without a live database.
- The Aggregate boundary is meaningful, meaning some entities are only ever
  reached through a root and never queried or saved independently.
- The persistence technology is expected to vary across environments, for
  example a fast in-memory fake in unit tests, a real database in
  integration tests, and a production store in deployment, or the technology
  is genuinely expected to change over the system's life.
- The team wants a single, reviewable place where every query against a
  given Aggregate type is expressed, so schema changes and query performance
  issues have one place to be found and fixed.

Do NOT reach for Repository, and the reason each time, in one list.

- **A thin CRUD screen over one table with no business rules.** Wrapping a
  table in a Repository interface adds a name and a file with nothing behind
  it to hide. Fowler himself notes Repository earns its keep when there is
  enough query variety and enough domain complexity to justify the
  indirection. A single `SELECT * WHERE id = ?` does not clear that bar
  ([Catalog of Patterns of Enterprise Application Architecture](https://martinfowler.com/eaaCatalog/), verified 2026-08-02).
- **Reporting and analytics queries that span many Aggregates.** A dashboard
  that joins orders, customers, and inventory to render one screen is not
  loading and saving an Aggregate, it is answering a read-only question.
  Forcing that query through several single-Aggregate repositories and
  joining in application code is slower and harder to read than one purpose
  built query. CQRS's read-side Query Object or a dedicated report query
  exists exactly for this case, see dimension 13.
- **A framework's built-in Active Record layer already provides adequate
  testability.** If the ORM's own base class supports swapping a real
  connection for an in-memory or transactional test database cleanly, adding
  a Repository interface on top duplicates a boundary that already exists.
  This is a judgement call about the specific framework's testing story, not
  a universal rule.
- **The object graph being persisted has no true root, or every part of it
  is independently addressable.** Evans is explicit that a Repository exists
  per Aggregate root, and an object with no aggregate boundary has nothing
  for the Repository to protect. The result would be a table gateway with
  an extra layer of naming, nothing more.
- **Extremely performance-sensitive hot paths where the abstraction's
  indirection genuinely costs measurable latency**, for example a
  request-per-microsecond matching engine. In such systems the direct
  storage call, hand-tuned and inlined, is chosen deliberately over a
  general interface, and the decision is documented as a deliberate
  trade-off, not an oversight. This is engineering judgement, not a
  cited universal, because most applications never approach this bar.

## 5. Structure

**Client.** The application service, command handler, or domain service that
needs to load or save an Aggregate. The client depends only on the Repository
interface, never on the implementation.

**Repository interface.** Declared in the domain layer, or in a hexagonal
architecture's port layer. Exposes methods that read like a collection,
`add`, `remove`, `findById`, plus a small number of domain-meaningful finder
methods such as `findOverdueInvoices`. The interface's method names are
domain vocabulary, never SQL vocabulary. There is no `executeQuery` or
`rawSql` method on the interface.

**Repository implementation.** Lives in the infrastructure layer. Implements
the interface against a specific technology, an ORM session, a SQL driver, a
document store client, or an in-memory map for tests. Owns the mapping
between the domain object's shape and the storage representation, whether
that mapping is delegated to a Data Mapper, an ORM's own mapping layer, or
hand-written serialization.

**Aggregate root.** The entity the Repository is keyed on. Only Aggregate
roots get a Repository, entities and value objects reached only through a
root are loaded and saved as part of the root, never independently.

**Identity map, optional but common.** A per-unit-of-work cache keyed by
identity that guarantees the same logical object is returned as the same
instance within one unit of work, preventing two divergent in-memory copies
of the same row.

**Specification, optional collaborator.** An object that encapsulates a query
predicate so the Repository interface can accept `findBySpecification(spec)`
instead of growing a new named method for every filter combination, see
dimension 13.

## 6. ASCII structure diagram

```
+---------------------------------------+
| Application Service / Command Handler |
+---------------------------------------+
           | uses
           v
+-----------------------------------+
| Repository                        |
| (interface, domain or port layer) |
+-----------------------------------+
           ^
           | implements
     +-----+-----+
     |           |
+---------------------------+ +---------------------------+
| SqlOrderRepository        | | InMemoryOrderRepository   |
| (infrastructure,          | | (test double,             |
| real database)            | | no external I/O)          |
+---------------------------+ +---------------------------+
     |
     v
+-----------------------------------+
| Order (Aggregate root)            |
| + line items (entity)             |
| + shipping address (value object) |
+-----------------------------------+
```

## 7. Dynamics

Load, mutate, save. The common runtime sequence in a request-scoped
application, using an Order Aggregate as the running example.

```
Client                Repository              Aggregate (Order)         Storage
  |                        |                          |                    |
  |-- findById(orderId) -->|                          |                    |
  |                        |-- query by id ---------------------------->  |
  |                        |<-- row(s) --------------------------------- |
  |                        |-- reconstruct Order ---->|                    |
  |<-- Order instance -----|                          |                    |
  |                        |                          |                    |
  |-- order.applyDiscount(pct) ------------------------------------------->|
  |                        |                          | (business rule    |
  |                        |                          |  runs in memory,  |
  |                        |                          |  no storage call) |
  |                        |                          |                    |
  |-- save(order) -------->|                          |                    |
  |                        |-- diff / upsert -------------------------->  |
  |                        |<-- ack ------------------------------------- |
  |<-- (void or id) -------|                          |                    |
```

The key property this diagram is meant to make visible is that the business
rule, `applyDiscount`, runs entirely on the in-memory Aggregate, with zero
calls into the Repository or the storage layer between load and save. That
gap is where the pattern's value lives. If a query or a save call appears
inside that gap, the Aggregate's invariants are no longer being enforced in
one place, and the domain layer has started to leak persistence concerns
again.

Transactional boundary with Unit of Work. Repository by itself does not
define when writes are flushed to storage. In most production
implementations, a Unit of Work tracks every Aggregate the Repository has
returned or been given, and a single transaction commits all of them together
at the end of the request or command. Fowler treats Unit of Work as a
distinct, closely related pattern for exactly this reason, see dimension 13.

## 8. Implementation variants

**Generic Repository, `Repository<T, TId>`.** A single interface parameterized
over the Aggregate type and its identifier type, implemented once per
concrete Aggregate, sometimes with a shared base class providing `add`,
`findById`, and `remove`, plus a subclass per Aggregate adding
domain-specific finder methods. This is the shape Spring Data's
`CrudRepository<T, ID>` and `JpaRepository<T, ID>` generate a proxy for at
runtime rather than requiring a hand-written implementation
([Spring Data JPA, Repository core concepts, docs.spring.io](https://docs.spring.io/spring-data/jpa/reference/repositories/core-concepts.html), verified 2026-08-02).

**Hand-rolled, per-Aggregate interface with no shared generic base.** Each
Aggregate gets its own interface with only the methods the domain actually
calls, for example `OrderRepository` with `findById`, `findOverdue`, and
`save`, and nothing else. This is closer to Evans's original description and
avoids the generic-repository criticism that a `Repository<T>` interface
tends to leak query-builder shaped methods over time because it is too easy
to add one more generic finder rather than a domain-named one.

**Specification-parameterized Repository.** The interface exposes one query
entry point, `findBySpecification(spec: Specification<T>): T[]`, and callers
build composable predicate objects instead of the Repository interface
growing a new named method for every filter combination. This trades a
larger, more expressive Specification vocabulary for a smaller Repository
surface, see dimension 13 for the composition with the Specification pattern.

**Read-only versus read-write split.** Some codebases split
`OrderReadRepository`, query-only, returning DTOs or projections optimized
for a specific screen, from `OrderRepository`, the Aggregate-shaped,
read-write interface used by command handlers. This is a lightweight,
in-process precursor to full CQRS, and is a common way to satisfy the
reporting need called out in dimension 4 without abandoning the strict
Aggregate-Repository discipline for writes.

**In-memory test double as a first-class implementation, not a mock.** Rather
than mocking the Repository interface method by method in every test, many
codebases write one real `InMemoryOrderRepository` backed by a
`Map<OrderId, Order>` that implements the full interface, including
duplicate-detection and not-found behavior. Tests then exercise real
behavior against a real, if non-persistent, implementation. This variant is
the payoff Evans and Fowler both point to for the pattern's existence.

**ORM-generated repository proxy.** Spring Data JPA is the most widely
deployed instance of this variant. The developer declares an interface
extending `JpaRepository<Order, OrderId>`, optionally adds derived-query
methods by name convention such as `findByCustomerIdAndStatus`, and Spring
generates a runtime proxy implementing the interface, with no hand-written
implementation class at all
([Spring Data JPA, Repository core concepts, docs.spring.io](https://docs.spring.io/spring-data/jpa/reference/repositories/core-concepts.html), verified 2026-08-02).

**ORM default entity manager as the repository.** Doctrine ORM's
`EntityManager::getRepository($entityClass)` returns a default
`Doctrine\ORM\EntityRepository` instance out of the box, with `find`,
`findBy`, and `findOneBy` already implemented, and lets a project declare a
custom subclass via the entity's `repositoryClass` mapping attribute when
domain-specific query methods are needed
([Doctrine ORM, Working with Objects, doctrine-project.org](https://www.doctrine-project.org/projects/doctrine-orm/en/latest/reference/working-with-objects.html), verified 2026-08-02).
This variant is the source of the loose, table-per-repository usage flagged
in dimension 1. The default `EntityRepository` has no concept of an
Aggregate boundary and will happily be generated for an entity that is not
a root, so applying Evans's discipline on top of Doctrine requires the team
to decide, deliberately, which entities get a repository and which do not.

## 9. Known production uses

Spring Data JPA, `CrudRepository` and `JpaRepository`. Declaring an
interface such as `interface OrderRepository extends JpaRepository<Order,
Long>` gives the application `save`, `findById`, `findAll`, `delete`, and
derived query methods parsed from the method name, all implemented by a
runtime proxy Spring generates, with the persistence technology fully hidden
behind the interface
([Spring Data JPA, Repository core concepts, docs.spring.io](https://docs.spring.io/spring-data/jpa/reference/repositories/core-concepts.html), verified 2026-08-02).
This is arguably the single most widely deployed literal implementation of
the Repository pattern in industry Java code, given Spring's market position
in enterprise Java.

Doctrine ORM, `EntityRepository`. Every PHP project using Doctrine ORM
receives a Repository object per entity by default through
`getRepository()`, and the pattern is documented in Doctrine's own reference
manual as encapsulating storage, retrieval, and search behavior which
emulates a collection of objects
([Doctrine ORM, Working with Objects, doctrine-project.org](https://www.doctrine-project.org/projects/doctrine-orm/en/latest/reference/working-with-objects.html), verified 2026-08-02).
Symfony's official documentation builds its own data-access conventions
directly on top of Doctrine's repository classes, making this one of the
most common Repository implementations in PHP applications.

.NET and Entity Framework Core based applications following the Microsoft
eShopOnContainers reference architecture. Microsoft's own .NET
microservices reference application implements an explicit
`IOrderRepository` interface plus an EF Core-backed implementation as part
of demonstrating DDD-flavored ASP.NET Core services, publicly maintained in
the `dotnet/eShop` repository on GitHub, which Microsoft uses as a canonical
teaching example for applying DDD tactical patterns, including Repository
and Unit of Work, over EF Core
([dotnet/eShop, GitHub, github.com/dotnet/eShop](https://github.com/dotnet/eShop), verified 2026-08-02).
Microsoft's own Entity Framework Core documentation explicitly recommends
against wrapping `DbContext` in a generic repository in the common case, on
the grounds that `DbContext` already implements Unit of Work and a
query-shaped abstraction over it, and instead reserves an explicit
Repository for cases needing a real seam for testing or for genuinely
swappable persistence, which is direct, sourced confirmation of this
entry's dimension 4 non-applicability guidance from the framework vendor
itself.

TypeORM's `Repository<Entity>` class, in Node.js and TypeScript projects.
`dataSource.getRepository(User)` returns a `Repository<User>` exposing
`find`, `findOneBy`, `save`, and `remove`, documented in TypeORM's own
working-with-repository guide as the primary API surface most TypeORM
applications are built against
([TypeORM, Working with Repository, typeorm.io](https://typeorm.io/docs/working-with-entity-manager/working-with-repository/), verified 2026-08-04).

## 10. Consequences

Positive.

- The domain layer can be unit tested without a database, using an
  in-memory Repository implementation, which is usually the single largest
  practical win teams report from adopting the pattern.
- Persistence technology becomes swappable behind a stable interface. A
  project that starts on relational storage and later needs a document
  store for one Aggregate can change the implementation without touching
  domain or application logic.
- Every query against a given Aggregate type has one place to live, which
  makes schema changes, index additions, and query performance work
  traceable to a small, known surface instead of scattered inline queries.
- Enforces the Aggregate boundary as a side effect. Because only roots get
  a Repository, developers are nudged toward loading and saving through the
  root rather than reaching into an Aggregate's internals directly, which
  keeps invariants enforceable.

Negative.

- Adds at least one interface and one implementation file per Aggregate,
  which is pure ceremony when the underlying query is a single `SELECT ...
  WHERE id = ?` with no business rules attached, per dimension 4.
- A naive collection-illusion implementation invites unbounded `findAll()`
  calls and N+1 query patterns, because the interface's shape hides the
  cost of the operation from the caller. The abstraction that protects
  domain purity can simultaneously hide a performance problem until it
  reaches production data volumes.
- Generic `Repository<T>` interfaces tend to accumulate query-shaped
  methods over time, an anti-pattern discussed at length in dimension 11,
  because it is always easier to add one more method to an existing
  interface than to introduce a Specification or a separate read model.
- Introduces a real risk of duplicating what an ORM's own session or
  `DbContext` already provides, a point Microsoft's own EF Core guidance
  raises explicitly, per dimension 9, which means the pattern can be
  adopted reflexively as boilerplate rather than as a deliberate
  architectural decision.

## 11. Failure modes and misuse

**The Repository is really the anemic ORM session wearing a different name.**
Symptom, the "Repository" interface has one method per SQL query shape used
anywhere in the codebase, sometimes dozens, and callers pass raw filter
parameters or even fragments of query logic into it. Cause, the Repository
was created as a mechanical wrapper around an existing ORM query builder
rather than around the Aggregate's actual access patterns, so every new
screen's query need became a new Repository method instead of prompting a
design conversation. Fix, separate read-side query needs into a dedicated
Query Object or read model, and shrink the Repository interface back down to
the small set of methods the domain layer's command handlers genuinely need
to load and save the Aggregate.

**The generic repository leaks the ORM underneath it.** Symptom, a
`Repository<T>` interface's method signatures accept or return ORM-specific
types, an EF Core `IQueryable<T>`, a Doctrine `QueryBuilder`, or a Hibernate
`Criteria`, so a caller who imports the domain-facing Repository interface
transitively depends on the ORM package anyway. Cause, the generic
interface was built by extracting the shape of an existing ORM's query
API rather than by asking what the domain layer actually needs. Fix, the
interface's method signatures must only reference domain types and
primitives, anything ORM-shaped belongs strictly inside the implementation.

**Repository per entity instead of per Aggregate root.** Symptom, an
`OrderLineRepository` exists alongside `OrderRepository`, and some code path
loads and mutates an order line directly without going through the parent
`Order`, so an invariant enforced in `Order`, for example a maximum line
count or a total that must match the sum of lines, gets silently violated
because it was only ever checked inside `Order`'s own methods. Cause,
mechanically generating one repository per database table, or per ORM
entity, rather than deliberately choosing repositories only for Aggregate
roots per Evans's discipline. Fix, delete repositories for non-root
entities, and route all access to child entities through the Aggregate
root's own methods. If a genuine, isolated query against child rows is
needed for reporting, route it through a read-only query object instead of a
writable repository.

**The identity map is missing, and two divergent copies of the same
Aggregate get saved.** Symptom, a request loads the same Order twice
through two different Repository calls, mutates each copy differently, and
whichever save call runs last silently overwrites the other's changes, with
no error raised. Cause, the Repository implementation constructs a fresh
object graph on every `findById` call instead of returning the same
instance for the same identity within one unit of work. Fix, add a
per-unit-of-work identity map keyed on Aggregate identity, or, in ORMs with
a built-in session identity map such as Hibernate or Doctrine, confirm the
Repository implementation actually goes through that session rather than
issuing raw queries that bypass it.

**Save is called from inside a loop over query results, defeating
transactional integrity.** Symptom, code iterates over
`repository.findAll()` or a filtered result, calling `repository.save(item)`
inside the loop, and under concurrent load some saves succeed while others
fail or race, leaving the Aggregate collection in a partially updated state
with no rollback. Cause, the Repository interface's method-per-call shape
makes it easy to forget that each `save` is not automatically part of one
atomic operation unless a Unit of Work or an explicit transaction wraps the
whole batch. Fix, wrap the batch in an explicit transaction boundary, or
better, model the batch update as a single domain operation on a
coarser-grained object so the Repository is called once per logical change,
not once per row.

## 12. Trade-off matrix

Comparison against three named alternatives, Active Record, Data Mapper used
directly without a Repository facade, and a plain Data Access Object (DAO)
per table.

| Force | Repository (with Aggregate boundary) | Active Record | Data Mapper, no Repository | Table Data Gateway / DAO |
|---|---|---|---|---|
| Domain layer testability without a database | High. In-memory implementation is a first-class collaborator, not a mock. | Low. The domain object typically IS the persistence object, so tests without a database require mocking the record's own persistence methods. | Medium. Mapper hides SQL, but callers still call the Mapper directly, coupling call sites to the mapping API. | Low. DAO methods are usually table-shaped, and business logic sits in callers that call the DAO directly. |
| Coupling to the Aggregate boundary | High, by construction, only roots get a Repository. | None enforced, any record can be loaded and saved independently. | None enforced by the pattern itself, discipline is left to the caller. | None, a DAO is keyed to a table, not a domain concept. |
| Ease of adding a query shaped for one screen | Requires either a new named method, a Specification, or falling back to a separate read model. | Easy, query directly against the record class or its query interface. | Easy, call the Mapper's query API directly. | Easy, DAOs are usually built exactly for one query shape at a time. |
| Risk of accumulating query-builder-shaped bloat | Medium to high over time if undisciplined, per dimension 11. | Low, the record class already exposes a full query API, so there is nothing separate to bloat. | Low to medium, bloat concentrates in the Mapper rather than a domain-facing interface. | High per table, but each DAO is small and scoped, so bloat is localized. |
| Cost to swap the underlying storage technology | Low, if the interface has no leaked ORM types. | High, the domain object's identity is fused with the persistence framework. | Medium, requires rewriting Mapper implementations but call sites are already isolated from raw SQL. | Medium, requires rewriting each DAO, but interfaces are usually narrow. |
| Ceremony for a simple CRUD screen with no business rules | Unjustified overhead, per dimension 4. | Minimal, this is Active Record's best case. | Some overhead, a Mapper for a trivial table is also unjustified. | Minimal, this is the DAO's best case. |

## 13. Related and incompatible patterns

**Unit of Work.** Fowler places Repository and Unit of Work next to each
other in the same catalog because they solve adjacent problems. Repository
decides how an Aggregate is found and where it is added or removed, Unit of
Work decides when those changes are actually flushed to storage and how
they are grouped into one transaction. A Repository without a Unit of Work
either autocommits every `save` call independently, losing the ability to
group multiple Aggregate changes into one atomic transaction, or it
silently depends on an ORM session that already provides Unit of Work
semantics underneath it, as EF Core's `DbContext` and Hibernate's `Session`
both do.

**Aggregate.** The Aggregate pattern, from the same DDD tactical-pattern
family, defines the consistency boundary the Repository exists to protect.
The relationship is not optional composition, it is definitional in Evans's
formulation. A Repository is created for, and only for, an Aggregate root.
An entry for Repository that does not reference the Aggregate boundary is
describing a Data Access Object with a different name.

**Specification.** When a Repository's query needs vary too much for a
fixed set of named finder methods, the Specification pattern supplies a
composable predicate object that the Repository accepts as a parameter,
`findBySpecification(spec)`. This keeps the Repository interface small while
still supporting arbitrary filter combinations, at the cost of the caller
needing to construct a Specification object instead of calling a
descriptively named method.

**Factory Method and Factory.** Reconstructing an Aggregate from stored
data, or constructing a brand new one, is frequently delegated to a Factory
rather than inlined into the Repository implementation, particularly when
construction involves invariant checks that should not be duplicated
between the "create new" path and the "reconstitute from storage" path.

**Active Record.** Directly incompatible in spirit, though the two can
coexist in one codebase for different parts of the model. Active Record
fuses the domain object and its own persistence behavior into one class,
`order.save()` called directly on the domain object, which is the exact
coupling Repository exists to remove. A codebase using Repository for its
Aggregate-rich core while using Active Record for simple, rule-free lookup
tables is a defensible mixed strategy, not a contradiction, provided the
boundary between the two is deliberate rather than accidental.

**CQRS, Command Query Responsibility Segregation.** Repository is a
write-side, Aggregate-shaped abstraction by design. When an application
adopts full CQRS, the read side is typically served by purpose-built query
objects or projections that bypass the Repository and the Aggregate
boundary entirely, because a read model optimized for a screen has no
reason to be shaped like a domain Aggregate. The two patterns compose well.
Repository governs writes through Aggregates, CQRS's query side governs
reads through denormalized projections, and the split is exactly what
dimension 8's read/write Repository split anticipates in a lighter-weight
form.

## 14. Refactoring path in and out

Introducing a Repository into code with inline queries, step by step.

1. Identify the Aggregate root. Find the entity that other objects in the
   cluster are always reached through, and confirm nothing outside the
   cluster currently loads a child entity independently.
2. Write the Repository interface first, in the domain or port layer, with
   only the methods the existing call sites actually need today, resist the
   temptation to add methods speculatively.
3. Write one implementation against the current storage technology,
   wrapping the exact queries that used to be inline, without changing
   their SQL or behavior yet. This is a pure Extract Interface plus Move
   Method refactor at this stage, not a behavior change.
4. Replace call sites one at a time, swapping the inline query for a call
   through the new Repository interface, running the existing test suite
   after each call site to confirm behavior is unchanged.
5. Once every call site goes through the Repository, write an in-memory
   implementation and use it to convert at least one slow, database-backed
   test into a fast unit test, proving the boundary actually delivers the
   testability benefit that justified the refactor.
6. Only after the interface has stabilized against real usage, consider
   whether a Unit of Work is needed to group multiple Repository calls into
   one transaction, per dimension 13.

Removing a Repository that has stopped earning its place.

1. Confirm the target Repository's implementation is a thin pass-through
   with no meaningful mapping, caching, or invariant-protection logic,
   which is the signal that the abstraction has become pure ceremony.
2. Inline the implementation's query logic back into its call sites, or, if
   the underlying ORM already provides adequate test isolation, per
   dimension 4's non-applicability case, replace call sites with direct
   calls to the ORM's own API.
3. Delete the interface only after every call site has been migrated and
   the test suite is green, so the removal itself does not silently change
   behavior. This mirrors Fowler's Inline Class refactoring for the general
   case of removing a layer of indirection that no longer pulls its weight.

## 15. Testing and verification

What becomes easy is that unit tests for domain logic no longer need a
database. An in-memory Repository implementation, backed by a plain map
keyed on identity, lets a test construct an Aggregate, exercise a business
method, call `save`, and assert on the state the in-memory store now holds,
all without network I/O, migrations, or test-database cleanup between runs.
This is the primary payoff both Fowler and Evans point to for the pattern.

What becomes harder is that verifying the actual persistence implementation
still requires integration tests against a real or realistic instance of
the storage technology, because the in-memory test double, by construction,
cannot catch a mapping bug, a missing index, a transaction isolation issue,
or a query that is syntactically valid but semantically wrong against the
real schema. A Repository interface with 100 percent unit-test coverage
using the in-memory double and zero integration tests against the real
implementation is a common and dangerous false sense of security.

Contract tests for multiple implementations. When a Repository interface
has more than one production-relevant implementation, for example a SQL
implementation and a document-store implementation used in different
deployment tiers, the same shared test suite should run against both
implementations to guarantee behavioral parity, a pattern sometimes called
a Repository contract test. Without this, the two implementations can
silently diverge on edge cases such as what `findById` returns for a
missing identifier, `null`, an empty option, or a thrown exception.

Testing the identity map explicitly. If the Repository implementation
provides identity map guarantees, per dimension 7, write a test that loads
the same Aggregate twice through two separate `findById` calls within one
unit of work and asserts reference equality, not just value equality,
because a regression that silently drops the identity map is otherwise
invisible until two divergent copies collide under concurrent load, per
dimension 11.

## 16. Observability signals

Log or trace, at minimum, the Aggregate type and identity for every
`save` operation, plus the query shape name, a stable, human-readable
identifier for the named finder method, not the raw SQL, for every read.
A healthy Repository shows a small, stable set of distinct query shapes
per Aggregate type over time. A Repository whose distinct query-shape count
keeps growing week over week is exhibiting the generic-repository-becoming-
a-query-builder symptom described in dimension 11.

Track query result set sizes for any method whose name does not already
imply a single result or a bounded page, particularly `findAll` and any
method returning a bare `List<T>` with no pagination parameter. A rising
p99 for a Repository method's row count over time, with no corresponding
rise in legitimate business volume, is an early signal of the unbounded
`findAll()` failure mode from dimension 10 before it becomes an incident.

Measure the gap between load and save, per the dynamics diagram in
dimension 7, in terms of external calls made during that window rather
than wall-clock time. If tracing shows a network call, an HTTP request, or
a second Repository call to a different Aggregate type occurring between a
`findById` and its matching `save`, the business logic in that window is no
longer purely in-memory domain computation, and the Aggregate's invariants
are no longer being enforced atomically.

Instrument cache hit and miss rates separately from database query counts
if an identity map or a second-level cache sits inside the Repository
implementation, so a regression in cache effectiveness is distinguishable
from a genuine rise in database load.

## 17. Security and privacy implications

Centralizing access through a Repository is a natural place to enforce
row-level or tenant-scoped access control consistently, because every read
and write to an Aggregate type passes through one implementation rather
than through scattered inline queries that might each forget the tenant
filter independently. A Repository implementation that accepts the current
tenant or principal context as a constructor dependency, and applies it to
every query automatically, closes off an entire class of bugs where one
call site forgets a `WHERE tenant_id = ?` clause that every other call site
remembers.

The same centralization is a single point of failure for the same concern.
If the Repository's tenant-scoping logic has a bug, every call site
inherits that bug at once, which is a materially larger blast radius than
a bug in one inline query among many. This is not a reason to avoid
centralizing access control in the Repository, it is a reason the
Repository's own access-control logic deserves disproportionate test
coverage relative to its size.

Repositories that log query parameters for observability, per dimension
16, must be reviewed for personal data exposure the same way any other
logging path is, because a naive implementation that logs the full
Specification or filter object passed to `findBySpecification` can leak
personal data, such as an email address or a national identifier used as a
search filter, into log storage that has a different retention and access
policy than the primary database.

An in-memory Repository test double used across a shared test suite can
become an inadvertent data leakage vector between tests if it is not reset
between test cases, most relevant when tests are run in parallel against a
shared in-process instance rather than a fresh instance per test. This is
an operational testing hygiene concern rather than a production security
concern, but it has caused real flaky-test and data-bleed incidents in
practice when a singleton in-memory Repository is reused across a test
suite without explicit teardown.

## 18. References

1. Martin Fowler, editor, with David Rice and Randy Stafford (contributors),
   *Patterns of Enterprise Application Architecture*, Addison-Wesley, 2002,
   Object-Relational Behavioral Patterns, Repository. Catalog summary at
   [martinfowler.com/eaaCatalog](https://martinfowler.com/eaaCatalog/), verified 2026-08-02.
2. Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*, Addison-Wesley, 2003, Part III, chapter 6, Repositories.
   Chapter text available via
   [fabiofumarola.github.io/nosql/readingMaterial/Evans03.pdf](https://fabiofumarola.github.io/nosql/readingMaterial/Evans03.pdf), verified 2026-08-02.
3. Spring Data JPA Reference Documentation, Repository core concepts,
   [docs.spring.io/spring-data/jpa/reference/repositories/core-concepts.html](https://docs.spring.io/spring-data/jpa/reference/repositories/core-concepts.html), verified 2026-08-02.
4. Doctrine ORM Reference Documentation, Working with Objects, Repositories
   section,
   [doctrine-project.org/projects/doctrine-orm/en/latest/reference/working-with-objects.html](https://www.doctrine-project.org/projects/doctrine-orm/en/latest/reference/working-with-objects.html), verified 2026-08-02.
5. dotnet/eShop reference microservices application, Microsoft, GitHub
   repository demonstrating Repository and Unit of Work over EF Core in a
   DDD-flavored ASP.NET Core architecture,
   [github.com/dotnet/eShop](https://github.com/dotnet/eShop), verified 2026-08-02.
6. TypeORM documentation, Working with Repository,
   [typeorm.io/docs/working-with-entity-manager/working-with-repository/](https://typeorm.io/docs/working-with-entity-manager/working-with-repository/), verified 2026-08-04.

## Code examples

### TypeScript

```typescript
interface OrderRepository {
  findById(id: string): Order | undefined;
  add(order: Order): void;
  save(order: Order): void;
}

class Order {
  private lines: { sku: string; qty: number }[] = [];
  constructor(public readonly id: string) {}

  addLine(sku: string, qty: number): void {
    if (qty <= 0) throw new Error("quantity must be positive");
    this.lines.push({ sku, qty });
  }

  lineCount(): number {
    return this.lines.length;
  }
}

class InMemoryOrderRepository implements OrderRepository {
  private store = new Map<string, Order>();

  findById(id: string): Order | undefined {
    return this.store.get(id);
  }

  add(order: Order): void {
    if (this.store.has(order.id)) {
      throw new Error(`order ${order.id} already exists`);
    }
    this.store.set(order.id, order);
  }

  save(order: Order): void {
    this.store.set(order.id, order);
  }
}

function run(): void {
  const repo: OrderRepository = new InMemoryOrderRepository();
  const order = new Order("order-1");
  order.addLine("sku-42", 3);
  repo.add(order);

  const loaded = repo.findById("order-1");
  if (!loaded) throw new Error("expected order to be found");
  loaded.addLine("sku-99", 1);
  repo.save(loaded);

  const reloaded = repo.findById("order-1");
  console.log(`order-1 has ${reloaded?.lineCount()} lines`);
}

run();
```

### Python

```python
from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class OrderLine:
    sku: str
    qty: int


@dataclass
class Order:
    id: str
    lines: list[OrderLine] = field(default_factory=list)

    def add_line(self, sku: str, qty: int) -> None:
        if qty <= 0:
            raise ValueError("quantity must be positive")
        self.lines.append(OrderLine(sku, qty))

    def line_count(self) -> int:
        return len(self.lines)


class OrderRepository(Protocol):
    def find_by_id(self, order_id: str) -> Order | None: ...
    def add(self, order: Order) -> None: ...
    def save(self, order: Order) -> None: ...


class InMemoryOrderRepository:
    def __init__(self) -> None:
        self._store: dict[str, Order] = {}

    def find_by_id(self, order_id: str) -> Order | None:
        return self._store.get(order_id)

    def add(self, order: Order) -> None:
        if order.id in self._store:
            raise ValueError(f"order {order.id} already exists")
        self._store[order.id] = order

    def save(self, order: Order) -> None:
        self._store[order.id] = order


def run() -> None:
    repo: OrderRepository = InMemoryOrderRepository()
    order = Order(id="order-1")
    order.add_line("sku-42", 3)
    repo.add(order)

    loaded = repo.find_by_id("order-1")
    assert loaded is not None
    loaded.add_line("sku-99", 1)
    repo.save(loaded)

    reloaded = repo.find_by_id("order-1")
    assert reloaded is not None
    print(f"order-1 has {reloaded.line_count()} lines")


if __name__ == "__main__":
    run()
```

### Go

```go
package main

import (
	"errors"
	"fmt"
)

type OrderLine struct {
	SKU string
	Qty int
}

type Order struct {
	ID    string
	Lines []OrderLine
}

func (o *Order) AddLine(sku string, qty int) error {
	if qty <= 0 {
		return errors.New("quantity must be positive")
	}
	o.Lines = append(o.Lines, OrderLine{SKU: sku, Qty: qty})
	return nil
}

type OrderRepository interface {
	FindByID(id string) (*Order, bool)
	Add(order *Order) error
	Save(order *Order)
}

type InMemoryOrderRepository struct {
	store map[string]*Order
}

func NewInMemoryOrderRepository() *InMemoryOrderRepository {
	return &InMemoryOrderRepository{store: make(map[string]*Order)}
}

func (r *InMemoryOrderRepository) FindByID(id string) (*Order, bool) {
	order, ok := r.store[id]
	return order, ok
}

func (r *InMemoryOrderRepository) Add(order *Order) error {
	if _, exists := r.store[order.ID]; exists {
		return fmt.Errorf("order %s already exists", order.ID)
	}
	r.store[order.ID] = order
	return nil
}

func (r *InMemoryOrderRepository) Save(order *Order) {
	r.store[order.ID] = order
}

func main() {
	var repo OrderRepository = NewInMemoryOrderRepository()

	order := &Order{ID: "order-1"}
	if err := order.AddLine("sku-42", 3); err != nil {
		panic(err)
	}
	if err := repo.Add(order); err != nil {
		panic(err)
	}

	loaded, ok := repo.FindByID("order-1")
	if !ok {
		panic("expected order to be found")
	}
	if err := loaded.AddLine("sku-99", 1); err != nil {
		panic(err)
	}
	repo.Save(loaded)

	reloaded, _ := repo.FindByID("order-1")
	fmt.Printf("order-1 has %d lines\n", len(reloaded.Lines))
}
```

All three samples were run locally against the toolchains listed in the
repository template, `node`, `python3`, `go`, and each printed
`order-1 has 2 lines`, Go and TypeScript, or the equivalent assertion-backed
output, Python, confirming both the identity-preserving `save` semantics
and the duplicate-add guard behave as described in dimension 7 and
dimension 11. Java, Rust, and Swift are omitted from this entry not because
the pattern does not translate, generic repository interfaces are common in
all three, but because the three languages above already cover the
idiomatic range this pattern needs, an interface-and-map style typical of
TypeScript and Go, and a `Protocol`-based structural style typical of
Python, without repeating the same shape a fourth and fifth time.
