---
name: Unit of Work
slug: unit-of-work
family: 06-enterprise-application-architecture
category: Object-Relational Behavioral
aliases: [Change Tracker, Transaction Manager Object, Session]
first_described: "Fowler 2003"
maturity: canonical
related: [identity-map, data-mapper, repository, optimistic-offline-lock, transaction-script, domain-model]
incompatible_with: [table-data-gateway]
verified: 2026-08-02
---

# Unit of Work

## 1. Name, aliases, and lineage

The canonical name is Unit of Work. It is one of the object-relational behavioral
patterns catalogued by Martin Fowler in *Patterns of Enterprise Application
Architecture*, Addison-Wesley, 2002, and republished in the online catalog. The
stated intent is to maintain a list of objects affected by a business
transaction and to coordinate the writing out of changes and the resolution of
concurrency problems (Martin Fowler, "Unit of Work",
https://martinfowler.com/eaaCatalog/unitOfWork.html, verified 2026-08-02, and
*Patterns of Enterprise Application Architecture*, chapter 11).

Fowler credits the underlying idea to conversations within the patterns
community rather than to a single earlier publication, and the pattern reads
as a codification of what every serious object-relational mapper already had
to build in some form. The book frames it as the answer to a concrete
question that Data Mapper leaves open. once several mapped objects have been
loaded, changed, and created inside one business operation, something has to
remember which of them need writing back, and in what order, when the
operation finishes.

The most common alias in practice is Change Tracker, used by ORM authors
to describe the internal component that watches property assignments. The
term Session is the name most persistence frameworks give to the concrete
object that plays this role, most visibly Hibernate's Session and NHibernate's
ISession, which is why a working engineer who has never opened the GoF-style
catalog will still recognize the pattern the moment its structure is named. A
smaller number of writers use Transaction Manager Object, which is
technically imprecise because Unit of Work coordinates object state, not the
database transaction boundary itself, though the two are frequently
implemented by the same class.

Two distinct implementation strategies share the one name, and conflating
them is the most common source of confusion when reading code.

- Registered Unit of Work. Domain objects, or the code that mutates them,
  explicitly call back into the unit of work to register themselves as new,
  dirty, or removed. The unit of work never inspects an object on its own; it
  only knows what it has been told.
- Automatic (change-tracking) Unit of Work. The unit of work snapshots
  object state when an object enters its scope, usually at load time, and
  computes dirtiness itself by comparing the current state against that
  snapshot when asked to commit. The caller never calls markDirty.

Fowler describes both variants in the same catalog entry and treats them as
two ways of answering the same question, not as separate patterns (Fowler,
Patterns of Enterprise Application Architecture, chapter 11, "Unit of Work",
the "Registering Objects with Unit of Work" and "Object-Based Identity"
discussion). The distinction matters throughout this entry because the two
variants trade off differently against every force in dimension 3.

## 2. Problem and context

An operation touches several objects that came from, or are destined for, a
database. Somewhere in the middle of a request handler, a domain service
loads a customer, adjusts two of its addresses, creates a new order, and
marks an old invoice as paid. Each of those four objects is a separate
persistent thing. The naive approach saves each one the moment it changes,
issuing an UPDATE right after the address mutation, an INSERT right after
the order is built, and another UPDATE when the invoice status flips.

That naive approach has three concrete costs that show up quickly in a real
codebase. First, each write is its own round trip to the database, so an
operation that logically belongs together as one business transaction turns
into several independent statements, each vulnerable to a partial failure
between them. Second, the code that decides an object needs saving is
scattered across every place that mutates it, which means a developer adding
a fifth mutation three months later has to remember to add a fifth save call,
and nothing enforces that they will. Third, and more subtly, saving eagerly
forces a decision about transaction boundaries at the wrong level. the
low-level code that sets a property on an address object should not be the
code that decides when a database transaction commits, because that decision
belongs to whoever is orchestrating the whole business operation.

The context in which Unit of Work becomes the right tool has a specific
shape. There is a business transaction, meaning a unit of work in the plain
English sense as well as in the pattern sense, that spans multiple domain
object mutations and must either fully apply or fully not apply. The objects
involved are mapped to a relational store by something in the spirit of Data
Mapper, so there already exists a layer that knows how to translate an
in-memory object into SQL. And the number of objects touched per operation is
small enough, usually single or low double digits, that holding them all in
memory for the duration of the operation is cheap.

Outside that context, most obviously in a system where each request touches
exactly one row through one query, Unit of Work adds machinery to solve a
problem that does not exist yet, see dimension 4.

## 3. Forces

- Round trips versus staleness window. Favoured toward fewer round trips.
  Batching every pending change into one flush, ideally inside one
  transaction, cuts the number of statements the database sees and lets the
  database order and batch them itself. The cost is a widened window during
  which in-memory objects have diverged from the database and nothing outside
  the process can see the pending change, which matters for anything that
  reads the database directly, such as a reporting job or a second process.
- Consistency versus coupling to transaction boundary. Favoured toward
  consistency. Because all writes happen at one commit point, the pattern
  makes it natural to wrap that commit in a single database transaction, so a
  partial failure rolls back everything. The coupling cost is that the
  business-logic code which creates and mutates objects now has an implicit
  dependency on when the unit of work decides to flush, which can surprise a
  developer who assumes a mutation is durable the moment it happens.
- Developer ergonomics versus hidden cost. Favoured toward ergonomics in
  the automatic variant. A developer who forgets nothing, because the unit of
  work tracks state on their behalf, writes less code and makes fewer
  save-call omissions. The hidden cost is that dirty checking by comparison
  is not free. every commit walks every tracked object and compares it
  against its loaded snapshot, which is CPU and, in naive implementations,
  memory for the snapshot itself.
- Explicitness versus magic. Sacrificed for the automatic variant, favoured
  for the registered variant. Explicit registration means a reader can grep
  for registerDirty and see exactly which code paths cause a write.
  Automatic tracking means the write happens because some property assignment
  somewhere flipped a flag the reader cannot see without instrumentation or a
  debugger.
- Memory versus object graph size. Sacrificed as the graph grows. Holding
  every loaded and every new object for the life of the unit of work is
  proportional to how much the operation touches. A batch job that processes
  one hundred thousand rows inside a single unit of work will exhaust memory
  unless the unit of work is deliberately flushed and cleared in chunks, a
  gotcha specific enough to be its own failure mode in dimension 11.
- Cognitive load versus lifecycle discipline. The pattern demands a clear
  answer to when a unit of work begins and when it ends, per request, per
  thread, per aggregate, per test. Getting that lifecycle wrong produces bugs
  that are hard to reproduce because they depend on which unit of work an
  object happened to be attached to at a given moment, see dimension 11.
- Operability. Slightly sacrificed. Because writes are deferred, a stack
  trace captured at the moment an object was mutated does not tell an operator
  when, or whether, that mutation actually reached the database. The commit
  point needs its own observability, covered in dimension 16.

## 4. Applicability and non-applicability

Reach for Unit of Work when the following hold.

- A single business operation creates, modifies, and deletes several mapped
  objects and those changes must be written together, atomically, or not at
  all.
- The system already has, or is willing to build, a Data Mapper or an ORM
  layer capable of translating tracked object state into SQL, since Unit of
  Work has nothing to coordinate without that translation layer underneath
  it.
- The cost of an extra round trip per mutation is measurable, either because
  the database is remote and every round trip carries real latency, or
  because the volume of mutating operations is high enough that batching
  cuts database load by a measurable amount.
- Developers repeatedly forget to call save after a mutation, which is a
  concrete, observed symptom that the manual save-per-object approach has
  stopped scaling with the size of the team or the codebase.
- Optimistic concurrency control is needed across a set of related objects,
  because a unit of work is a natural place to carry the version checks that
  Optimistic Offline Lock requires at commit time.

Do NOT reach for Unit of Work in these cases.

- A single row is read and a single row is written, with nothing else
  touched in between. A direct UPDATE statement or a single mapped save
  call is the honest shape. A unit of work wrapped around one object adds a
  tracking layer, a snapshot, and a flush step to replace one line of SQL,
  which is unearned indirection.
- The system is built around Table Data Gateway or Row Data Gateway with no
  Data Mapper underneath. Those patterns save eagerly, one call per row, by
  design, and grafting a unit of work on top means either duplicating the
  gateway's own save logic inside the tracker or fighting the gateway's
  eagerness. This is the reason table-data-gateway is marked incompatible
  in the frontmatter, not because the two can never coexist in one codebase,
  but because they should not both own the same object's persistence
  decision.
- The operation is a bulk update or bulk delete affecting many rows by a
  predicate, for example "set every subscription older than a year to
  expired". Loading every affected row into memory, marking it dirty, and
  flushing is orders of magnitude more expensive than a single UPDATE ...
  WHERE statement, and the unit of work's own memory limit makes this
  actively dangerous as row counts grow.
- The persistence model is not relational and the underlying store already
  gives atomic, single-document writes, as with many document databases
  used in single-aggregate-per-document style. The store's own atomicity
  already solves the problem Unit of Work exists to solve, and adding an
  in-memory tracker on top duplicates that guarantee without adding anything.
- Objects cross process boundaries between mutation and commit, for
  example a mutation applied in a web request and a commit intended to happen
  in a background job picking up the same object later. A unit of work is
  scoped to one in-memory session and does not survive serialization in any
  of the mainstream implementations, so this shape needs an explicit event or
  outbox pattern instead, not a stretched unit of work.
- The team cannot commit to a clear lifecycle rule for when a unit of work
  starts and ends. A unit of work with an ambiguous lifetime, commonly one
  held as a long-lived field on a singleton service rather than scoped per
  request, produces the cross-request state leakage described in dimension
  11, and the fix is organizational discipline, not more pattern.

## 5. Structure

Four participants, named by the role they play, following Fowler's own naming
in the catalog entry.

- Client (business transaction code). The application or domain-service
  code that loads objects, creates new ones, mutates existing ones, and marks
  some for deletion, then asks the unit of work to commit when the business
  operation is complete. In the registered variant the client, or the
  domain objects acting on the client's behalf, explicitly calls
  registerNew, registerDirty, or registerRemoved.
- Unit of Work. Holds three lists (new, dirty, removed) or, in the
  automatic variant, holds a map from identity to a loaded snapshot plus the
  live object. Exposes commit(), which computes the necessary inserts,
  updates, and deletes, and coordinates them with the Data Mapper layer,
  usually inside one database transaction.
- Data Mapper (or an equivalent persistence layer). Knows how to turn one
  domain object into the SQL needed to insert, update, or delete its row. The
  unit of work calls into the mapper for each object it decides needs
  writing, but does not itself know SQL. This separation is what lets Unit of
  Work stay a coordination pattern rather than an object-relational mapper in
  its own right.
- Domain Object. The object under change. In the registered variant it
  holds a reference to, or is given, the current unit of work so it can
  register itself on mutation. In the automatic variant it holds no such
  reference and is entirely unaware that it is being tracked, which the
  automatic variant treats as a feature.

A fifth, often implicit, participant deserves naming because most production
implementations depend on it. Identity Map, which guarantees that loading the
same database row twice inside one unit of work returns the same in-memory
object rather than two separate copies. Without an identity map, the unit of
work cannot reliably know that a dirty object it is about to write is the
same row a second query already loaded, and duplicate or conflicting writes
follow. Fowler treats Identity Map as its own pattern and notes the two are
almost always implemented together (Fowler, Patterns of Enterprise
Application Architecture, chapter 11, "Unit of Work", the "Identity Map"
discussion cross-reference).

## 6. ASCII structure diagram

```
+--------------------------------------------+
| Business Transaction (client / domain svc) |
+--------------------------------------------+
     | uses
     v
+------------------------+
| Unit of Work           |
| - newObjects: []       |
| - dirtyObjects: []     |
| - removedObjects: []   |
| + registerNew(obj)     |
| + registerDirty(obj)   |
| + registerRemoved(obj) |
| + commit()             |
+------------------------+
     | holds
     v
+----------------------------+
| Identity Map, id -> object |
+----------------------------+

Unit of Work also uses:

+---------------+
| Data Mapper   |
| + insert(obj) |
| + update(obj) |
| + delete(obj) |
+---------------+
     | issues SQL inside one transaction
     v
+----------+
| Database |
+----------+

Data Mapper maps a Domain Object:

+-----------------------------------+
| Domain Object                     |
| + markDirty() calls back into UoW |
+-----------------------------------+

In the registered variant only, a dashed line runs from
Domain Object back to Unit of Work, tracking a
reference. In the automatic variant that arrow does not
exist. Dirtiness is computed by the Unit of Work
comparing the live object against a snapshot it took at
load time, so Domain Object has no reference to, and no
knowledge of, the Unit of Work tracking it.
```

## 7. Dynamics

The sequence below shows the registered variant, since it makes every
callback explicit. The automatic variant collapses the registerDirty calls
into a single dirty-checking pass inside commit().

```
Client            UnitOfWork          Order (new)      Invoice (dirty)     DataMapper       DB
  |                    |                    |                  |                |            |
  |-- new UnitOfWork()->|                    |                  |                |            |
  |                    |                    |                  |                |            |
  |-- order = new Order() -------------------->|                  |                |            |
  |-- uow.registerNew(order) ---------------->|                  |                |            |
  |                    |-- add to newObjects |                  |                |            |
  |                    |                    |                  |                |            |
  |-- invoice.markPaid() ---------------------------------------->|                |            |
  |                    |<-- invoice.uow.registerDirty(invoice) --|                |            |
  |                    |-- add to dirtyObjects (dedup by id)      |                |            |
  |                    |                    |                  |                |            |
  |-- uow.commit() -->|                    |                  |                |            |
  |                    |-- begin transaction ------------------------------------------------>|
  |                    |-- for each new: mapper.insert(order) ---------------->|-- INSERT -->|
  |                    |-- for each dirty: mapper.update(invoice) ------------>|-- UPDATE -->|
  |                    |-- for each removed: mapper.delete(x)     |                |            |
  |                    |-- commit transaction ---------------------------------------------->|
  |<-- returns --------|                    |                  |                |            |
  |                    |                    |                  |                |            |
```

Two ordering rules matter and both are stated explicitly in Fowler's catalog
description. Inserts happen before updates and deletes so that a newly
created object's generated identifier is available if a dirty object
references it, and deletes are usually issued last, or at minimum after any
constraint that would be violated by deleting a row still referenced
elsewhere in the same batch (Fowler, Patterns of Enterprise Application
Architecture, chapter 11, "Unit of Work", "Sequencing the Interaction"
discussion). A production implementation resolves within-batch foreign key
ordering either by a topological sort over the pending objects or by
deferring constraint checks to the end of the database transaction, which
PostgreSQL and a small number of other engines support directly.

## 8. Implementation variants

Registered, explicit lists. Three collections, new, dirty, removed, each
appended to by an explicit call. This is the shape most closely matching
Fowler's own sample code. It is the easiest to unit test in isolation because
the three lists are directly inspectable, and it forces every mutation site
to state its intent, which some teams treat as a documentation benefit rather
than a cost.

Automatic, snapshot comparison. The unit of work takes a shallow or deep
copy of each object's state at load time and diffs the live object against
that copy when asked to commit. This is what Hibernate's persistence context
and SQLAlchemy's Session both do, and it is the variant most engineers
encounter first because it ships inside an ORM rather than being
hand-written. The cost, beyond the CPU of the comparison itself, is memory
proportional to twice the tracked object graph for the lifetime of the unit
of work, since both the live object and its snapshot are retained.

Per-request, framework-scoped. The unit of work's lifetime is bound to one
web request by the framework, created at the start of the request and
committed, or rolled back, at the end. This is the default shape in ASP.NET
Core with Entity Framework's DbContext registered as scoped, and in most
Spring Boot applications using JPA with @Transactional at the service-method
boundary. The convenience is real. a developer working inside a request
handler almost never thinks about the unit of work explicitly. The risk,
covered in dimension 11, is the convenience itself becoming a trap when code
assumes request-scoping in a context, such as a background job, that has no
request.

Explicit session object passed by the caller. Rather than framework
magic, the unit of work is an ordinary object the caller creates, passes
through the call stack or a context object, and commits or discards
explicitly. SQLAlchemy's Session, used outside of a web framework's
integration layer, is written this way, and so is a hand-rolled unit of work
in a language such as Go, which has no ambient framework scoping to lean on.
This variant trades convenience for a lifecycle a reader can trace by
following a value rather than by knowing a framework's conventions.

Unit of Work per aggregate versus per request. Domain-Driven Design
literature narrows the pattern's usual scope from "everything touched in this
request" to "everything touched inside this one aggregate's consistency
boundary", treating cross-aggregate consistency as eventual rather than
transactional. Eric Evans, Domain-Driven Design. Tackling Complexity in the
Heart of Software, Addison-Wesley, 2003, the aggregate and repository
discussion in part 3, argues that a transaction, and by extension a unit of
work commit, should not span more than one aggregate root at a time. This is
a narrower and stricter reading than Fowler's original, business-transaction-
scoped version, and the two are frequently in tension inside the same
codebase, see dimension 11.

Functional, immutable variant. In languages that favour immutability, the
"registration" step is replaced by building up an explicit list of pending
commands or events rather than mutating shared objects in place, and the
commit step interprets that list. This sidesteps dirty checking entirely at
the cost of the caller having to construct the change list itself rather than
mutating a live object graph. This is the shape most idiomatic in Rust,
where shared mutable state tracked implicitly by a framework runs directly
into the borrow checker, and it is close in spirit to Command, see dimension
13.

Language note on Go. Go has no ambient framework-level dependency
injection scoping in the way ASP.NET Core or Spring does, and no ORM as
dominant as Hibernate or Entity Framework among its surrounding libraries. A Go
implementation is almost always the explicit, hand-passed session object
variant, commonly a struct wrapping a *sql.Tx with small helper methods, and
the registration lists tend to be simpler because Go idiom favours explicit
error returns over deferred, batched failure reporting.

## 9. Known production uses

Hibernate ORM, the Session as persistence context. Every Session
maintains its own persistence context, described by the project's own
introduction as functioning as a first-level cache that tracks the entities
read or created within the current transaction, and flushes pending changes
to the database at defined synchronization points. Red Hat, Hibernate ORM
Introduction Guide, current release,
https://docs.hibernate.org/orm/current/introduction/html_single/Hibernate_Introduction.html
verified 2026-08-02.

Jakarta Persistence (JPA), EntityManager and its persistence context.
The specification defines an EntityManager instance as associated with a
persistence context, "a set of entity instances in which for any persistent
entity identity there is a unique entity instance," within which "the entity
instances and their lifecycle are managed," and states that changes made to
managed entities are written to the database on flush() or transaction
commit. Oracle, Java EE 7 API Specification, javax.persistence.EntityManager,
https://docs.oracle.com/javaee/7/api/javax/persistence/EntityManager.html
verified 2026-08-02.

SQLAlchemy, the Session object. SQLAlchemy's own documentation names the
pattern directly. "Whenever the database is about to be queried, or when the
transaction is about to be committed, the Session first flushes all pending
changes stored in memory to the database. This is known as the unit of work
pattern." The same page describes the identity map that backs it, stating
that ORM objects are maintained "inside a structure called the identity map,
a data structure that maintains unique copies of each object, where 'unique'
means 'only one object with a particular primary key.'" SQLAlchemy project,
SQLAlchemy 2.0 Documentation, "Session Basics",
https://docs.sqlalchemy.org/en/20/orm/session_basics.html verified 2026-08-02.

Entity Framework Core, DbContext and SaveChanges. Microsoft's own
documentation describes the pattern's behaviour without naming it explicitly.
"EF automatically detects changes made to an existing entity that is tracked
by the context," and multiple pending Add, Update, and Remove operations are
combined "into a single call to SaveChanges," which is documented as
transactional for most database providers, meaning "all the operations either
succeed or fail and the operations are never left partially applied."
Microsoft, Entity Framework Core documentation, "Basic Save Changes",
https://learn.microsoft.com/en-us/ef/core/saving/basic verified 2026-08-02.

## 10. Consequences

Positive.

- Multiple related writes are collapsed into one flush, and usually one
  database transaction, reducing round trips and giving a natural atomicity
  boundary for a business operation that touches several objects.
- Business logic that mutates objects is decoupled from the decision of when
  to write, which lets the same domain code run inside different transaction
  scopes without modification.
- The automatic variant removes an entire class of bug, the forgotten save
  call, because the framework rather than the developer decides what needs
  writing.
- Deletion ordering, insertion ordering, and dependency resolution across a
  batch of changes become the unit of work's problem rather than something
  every call site has to reimplement.
- Provides a natural place to attach optimistic concurrency checks, audit
  timestamps, and change notifications, since every write that will happen
  passes through one coordination point before it reaches the database.

Negative.

- Introduces a lifecycle the whole team must understand correctly. when a
  unit of work starts, when it ends, and what object is attached to which
  instance, and getting this wrong produces some of the hardest bugs to
  reproduce in an ORM-based codebase, catalogued in dimension 11.
- Deferred writes mean an in-memory object can diverge from the database for
  the life of the unit of work, which is invisible to any other process, and
  in some implementations invisible even to a fresh query issued from the
  same unit of work before a flush.
- Automatic dirty checking has a real, measurable CPU and memory cost that
  scales with the size of the tracked object graph, and this cost is
  frequently invisible to the developer writing the business logic, because
  it happens entirely inside the framework at commit time.
- The pattern assumes the operation's working set fits comfortably in memory
  for its duration, which makes it actively wrong for bulk operations, see
  dimension 4.
- Debugging why a change was not persisted requires understanding the unit
  of work's internal state at the time of the mutation, which is a level of
  indirection a plain UPDATE statement never had.

## 11. Failure modes and misuse

The N+1 flush, sometimes called excessive auto-flushing. Symptom. A
request that logically issues five writes generates dozens of round trips,
visible in a slow query log as many small statements interleaved with reads.
Cause. The ORM's auto-flush behaviour triggers a flush before every query,
including read-only queries, to keep query results consistent with pending
writes, and the code issues a query inside a loop that also mutates objects.
Fix. Batch the mutating and querying phases separately, or, where the ORM
supports it, switch auto-flush off for the duration of the loop and flush
explicitly once at the end.

Detached entity, lazy-load-after-close. Symptom. An exception such as
Hibernate's LazyInitializationException, or a silent stale read, when code
outside the original request handler tries to access a relation on an object
that was loaded inside a now-closed unit of work. Cause. The unit of work was
scoped to a request, the object escaped that scope by being returned from a
service method or cached, and the code touching it later runs with no active
persistence context. Fix. Fully load, or explicitly project, everything the
caller needs before the unit of work closes, and never return live-tracked
entities from a boundary where the unit of work's lifetime ends.

Cross-request unit of work leakage. Symptom. One user's uncommitted
change appears in a different user's response, or an object mutated by
request A is silently written to the database by request B's commit. Cause.
The unit of work was stored somewhere with a lifetime broader than one
request, most often a singleton service or a static field, rather than
request-scoped as the framework's dependency injection container assumes.
Fix. Verify the container's registration lifetime for the unit of work or
DbContext matches the intended scope, and add a test that asserts two
concurrent requests never share the same instance.

Silent partial commit inside a loop. Symptom. Half of a batch operation
lands in the database and the other half does not, with no exception raised
that the caller notices. Cause. The code calls commit() inside a loop over
many items rather than once at the end, so an item that fails midway leaves
earlier items already committed and later items never attempted. Fix. Commit
once per logical business transaction, and if a batch is genuinely too large
for one unit of work, chunk it deliberately, with each chunk's success or
failure tracked and reported, rather than committing incidentally inside a
loop.

Unbounded persistence context in a long-running process. Symptom. Memory
grows steadily during a batch job or a worker process that never restarts,
eventually triggering an out-of-memory error or degraded garbage collection
pauses. Cause. Every object read during the job's lifetime stays attached to
the same unit of work, because the job never calls clear() or opens a fresh
session per chunk. Fix. Periodically detach or clear the persistence context,
commonly every few hundred or few thousand processed items, and confirm the
ORM actually releases the memory rather than only marking objects as no
longer tracked.

Aggregate-boundary violation. Symptom. A single commit silently writes
changes to two unrelated aggregate roots, and a later concurrency conflict on
one of them rolls back a change to the other that had nothing to do with the
conflicting update. Cause. The unit of work's scope was drawn around "this
request" rather than around "this aggregate's consistency boundary", per the
Domain-Driven Design reading in dimension 8, and two independently
consistent aggregates ended up sharing one transaction by accident of code
organization rather than by design. Fix. Draw the unit of work boundary at
the aggregate root explicitly, and use a separate mechanism, an event, a
message, an eventual-consistency job, for changes that must propagate to a
second aggregate.

Optimistic lock exception surfacing at the wrong layer. Symptom. A user
sees a raw database or ORM exception, naming a table and a version column,
instead of a clear "someone else changed this while you were editing it"
message. Cause. The unit of work's commit, and the version check that
Optimistic Offline Lock performs inside it, throws a low-level exception type
that propagates unhandled to the outermost layer. Fix. Catch the
concurrency-specific exception at the unit of work's caller and translate it
into a clear domain error before it reaches the presentation layer.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Unit of Work (automatic) | Unit of Work (registered) | Table Data Gateway (eager save) | Transaction Script with explicit SQL | Data Mapper with no coordinator |
|---|---|---|---|---|---|
| Round trips for a multi-object change | Low. One flush per commit | Low. One flush per commit | High. One call per mutated row | Variable, developer-controlled | High. Each save is independent |
| Risk of a forgotten write | Low. Tracked automatically | Medium. Depends on every mutation site calling register | Low. Save is explicit and immediate at the call site | Low, but only because the developer writes every statement by hand | High. Nothing coordinates who calls save |
| Explicitness of what will be written | Low. Requires inspecting tracked state | High. Explicit list, greppable | High. The save call is right where the mutation happened | High. The SQL is literally in the code | Medium. Depends on caller discipline |
| Memory cost per operation | Medium to high. Snapshot plus live object | Medium. Three lists of live objects | Low. Nothing retained between calls | Low | Low. Nothing retained between calls |
| Suitability for bulk operations | Poor. Memory scales with rows touched | Poor. Same reason | Good, if paginated. Still one call per row | Good. A single set-based statement is natural | Good, same as gateway |
| Atomicity across several objects | Strong, when wrapped in one transaction | Strong, same | Weak, unless the caller wraps every call in a transaction manually | Strong, if the developer writes it that way | Weak. Each mapper call is its own concern |
| Fit with Data Mapper | Native. Assumes a mapper underneath | Native, same | Poor fit. Gateway usually replaces the mapper role | Not applicable, no mapping layer | Partial. Has the mapper but no batching |
| Testability of the coordination logic | Harder. Tracking is internal to the framework | Easier. Lists are directly inspectable | Easy, because there is no coordination to test | Easy, statements are inline and mockable | Hard, coordination is implicit in call order |

Reading of the table. Automatic Unit of Work wins where developer convenience
and low forgotten-write risk matter more than explicit traceability, which is
most line-of-business CRUD work. Registered Unit of Work wins where a team
values an explicit, testable list of pending changes over the convenience of
not writing registration calls. Table Data Gateway wins where each row's
persistence genuinely is independent and a coordination layer would add
nothing. Transaction Script wins where the operation is naturally a single
set-based statement rather than an object graph. Data Mapper alone, with no
coordinator, is the shape to avoid once an operation touches more than one
object, because it has all of Unit of Work's dependency on a mapping layer
and none of its atomicity or batching benefit.

## 13. Related and incompatible patterns

- Identity Map. The near-constant companion. A unit of work needs to know
  that two references to the same database row are the same in-memory
  object, or it risks tracking one row as both dirty and, through a second
  copy, unmodified at the same time. Fowler's own catalog entry treats the
  two as usually implemented together, with Identity Map solving the
  "is this the same object" question that Unit of Work depends on but does
  not itself answer.
- Data Mapper. The layer underneath. Unit of Work coordinates when
  writes happen, and Data Mapper knows how to perform each individual write.
  Neither is complete without the other in a typical implementation, and a
  Unit of Work with no Data Mapper has nothing to call at commit time beyond
  hand-written SQL, which collapses the pattern back into a manually written
  batching layer.
- Repository. Composes above it, at a slightly different altitude.
  Repository presents a collection-like interface over an aggregate's
  persistence, and a Repository's add() or remove() call frequently
  delegates straight into a Unit of Work's registerNew() or
  registerRemoved() rather than writing immediately. See the DDD
  repository entry, repository, for the collection-oriented framing that
  usually sits on top of a Unit of Work in a Domain-Driven Design codebase.
- Optimistic Offline Lock. Frequently implemented inside the unit of
  work's commit step, because the commit is the one place that knows every
  object about to be written and can check each one's version column before
  issuing the update. A unit of work with no concurrency check is exposed to
  lost updates the moment two units of work overlap on the same row.
- Transaction Script. A substitute, not a complement, for a given
  operation. Where Unit of Work coordinates changes across an object graph,
  Transaction Script writes the SQL for one procedural operation directly,
  with no object tracking layer at all. A codebase can use both, choosing
  per operation, but a single operation should commit to one shape rather
  than mixing a tracked object graph with hand-written SQL that bypasses the
  tracker, which reintroduces the ordering and staleness problems Unit of
  Work exists to solve.
- Table Data Gateway, marked incompatible. Table Data Gateway's whole
  design is to save the moment a row changes, with no deferred, batched
  commit step. Layering a Unit of Work on top means either the gateway keeps
  saving eagerly, defeating the batching the unit of work exists to provide,
  or the gateway's own save method has to be disabled and reimplemented
  inside the tracker, at which point the gateway has stopped being a
  gateway. The two patterns solve the same coordination question with
  opposite answers, eager versus deferred, and a codebase should pick one
  per persistence layer rather than mix them for the same object type.
- Command. The functional variant from dimension 8 is close in shape to a
  list of Command objects executed at commit time rather than a mutated
  object graph diffed at commit time. The two converge when a team chooses
  explicit intent capture over implicit dirty checking, which is the same
  trade-off as registered versus automatic Unit of Work, expressed as a
  different pattern name.

## 14. Refactoring path in and out

Introducing the pattern into code that saves eagerly today.

1. Identify one business operation that currently issues more than one save
   call across more than one object, and confirm those saves logically
   belong to a single business transaction, meaning a partial application of
   them would leave the system in a state nobody wants.
2. Introduce a Unit of Work class with the three registration methods and an
   empty commit() that, for now, simply calls the existing eager save
   methods in the order they are registered. This step changes nothing about
   when writes happen, only where the decision to write is expressed. Run
   the tests.
3. Change every eager save call in the target operation to a registration
   call instead. At the end of this step no write has moved, but every write
   decision now flows through the unit of work's lists. Run the tests.
4. Change commit() to perform the actual inserts, updates, and deletes in
   dependency order, wrapped in a single database transaction, rather than
   delegating to each object's individual save method. This is the step
   where the round-trip reduction and atomicity actually take effect. Run the
   tests, paying particular attention to any test that asserted an
   intermediate write happened before the operation finished, since those
   assertions are now testing an implementation detail that no longer holds.
5. Add the identity map from dimension 5 if it does not already exist,
   before extending the pattern to a second business operation, because a
   second operation loading the same row a first operation already tracks is
   exactly the scenario identity map exists to guard.
6. Extend the pattern to further operations one at a time, verifying at
   each step that the unit of work's lifetime scoping, request, thread, or
   explicit session object, is deliberate rather than accidental, since this
   is where the leakage failure mode in dimension 11 originates.

Removing the pattern when it stops earning its place. Signals include an
operation that now touches exactly one object, a bulk job that was
retrofitted onto a per-object unit of work and is running out of memory, or a
persistence layer migrating toward a document store with its own atomic
per-document write.

1. Confirm the operation genuinely touches one object, or that the
   remaining multi-object writes can tolerate the eager, per-object save
   semantics of the target replacement, most commonly Table Data Gateway or a
   direct mapper call.
2. Replace the registration call at each mutation site with a direct,
   synchronous save call to the underlying Data Mapper or gateway. Run the
   tests after each site, since removing deferred batching can surface tests
   that relied on the earlier, batched write ordering.
3. Remove the unit of work's lifecycle wiring, its scoping in the dependency
   injection container or its explicit construction at the top of the
   operation, once no code path still registers with it.
4. Delete the unit of work class and its identity map once no reference to
   either remains, and confirm through the test suite in dimension 15 that
   no test still depends on batching behaviour the removal deleted.

## 15. Testing and verification

Easier because of the pattern.

- Business logic can be tested against an in-memory or fake unit of work
  that records registration calls without touching a real database, which
  turns a test that would otherwise need a live connection into a fast,
  isolated unit test.
- The three registration lists, in the explicit variant, are directly
  assertable. a test can check that exactly one new object, zero dirty
  objects, and one removed object were registered by a given operation,
  without needing to inspect generated SQL.
- Concurrency and ordering bugs, such as an insert issued after a dependent
  update, become reproducible in a single-threaded test against a fake
  commit implementation that records call order, rather than requiring a
  live race condition against a real database.

Harder because of the pattern.

- A test that asserts a write happened must decide whether it is testing the
  registration (did the operation register the right intent) or the commit
  (did the intent actually reach the database), and conflating the two
  produces tests that pass against a fake unit of work while the real commit
  path is broken.
- Integration tests against a real database now need to reason about flush
  timing, since a query issued mid-test before an explicit flush may or may
  not see a pending, unflushed change, depending on the ORM's auto-flush
  configuration.
- Tests that share a unit of work across multiple test cases, commonly
  through a poorly scoped test fixture, leak state between tests in exactly
  the way described in the cross-request leakage failure mode, producing
  order-dependent test failures.

Techniques that apply.

- Fake Unit of Work. A hand-written implementation of the same interface
  that records registrations into simple lists and exposes them for
  assertion, with no database behind it. This is the primary tool for
  keeping domain-logic tests fast and independent of infrastructure.
- In-memory or SQLite-backed integration test for the commit path
  specifically. A smaller, separate test suite that exercises the real
  commit logic, insert-before-update ordering, transaction rollback on
  failure, against a real, disposable database, kept deliberately apart
  from the domain-logic tests so the two do not blur.
- Explicit flush-and-clear assertions. In frameworks with auto-flush
  behaviour, a test that deliberately triggers a flush and re-queries can
  assert that a change is actually visible to a fresh query, catching bugs
  where a change was registered but never reached the commit step due to a
  scoping error.
- Concurrency conflict test using two units of work. Open two units of
  work against the same row inside a single test, commit the first,
  attempt to commit the second, and assert the expected optimistic-lock
  failure, which directly exercises the interaction between Unit of Work and
  Optimistic Offline Lock described in dimension 13.

## 16. Observability signals

Because writes are deferred, the moment a mutation happens in the source code
is not the moment it becomes durable, which makes the commit point the
correct place to attach most of the useful telemetry.

What to record.

- A counter of commits, labelled by outcome, success or rollback, and by
  the logical operation name where the framework can supply one, so a
  dashboard can show which business operations are failing to commit and how
  often.
- A histogram of commit duration, since a slow commit usually means either
  too many objects were registered in one unit of work or a lock contention
  issue on the database side, and the two have different fixes.
- A gauge, or a per-request log field, of how many objects were registered
  as new, dirty, and removed at commit time. A sudden jump in this number for
  an operation that used to register a handful of objects is a strong signal
  of the unbounded persistence context failure mode from dimension 11.
- On rollback, the exception type and, where the framework distinguishes it,
  whether the failure was a constraint violation, an optimistic concurrency
  conflict, or an infrastructure error such as a connection drop, since these
  three require entirely different operator responses.
- For frameworks that expose it, the flush count per unit of work lifetime,
  distinct from the commit count, since a high flush-to-commit ratio points
  directly at the N+1 flush failure mode.

A healthy instance on a dashboard. Commit duration is flat and small relative
to the surrounding request latency. The registered-object-count gauge stays
within a narrow, expected band for a given operation type, because the shape
of a well-understood business operation does not change day to day. Rollback
rate is near zero and, when nonzero, made up mostly of optimistic concurrency
conflicts rather than infrastructure errors, which is the expected background
rate for a system with real concurrent writers.

A failing instance. Commit duration develops a long tail that correlates with
a specific operation, which usually means that operation's registered-object
count has grown unbounded, either because a loop is registering every row in
a large result set or because a unit of work meant to be short-lived is being
reused across many logical operations. A rising rollback rate made up mostly
of infrastructure errors rather than concurrency conflicts points at a
database or network problem upstream of the pattern entirely. A flush count
that climbs relative to commit count on a chart that used to track it one to
one indicates a code change introduced a query inside what used to be a pure
mutation loop, triggering the auto-flush failure mode.

## 17. Security and privacy implications

The pattern itself performs no authentication or authorization, and treating
it as a security boundary would be a mistake. Three implications are genuine
and worth stating.

Deferred writes widen the window of an inconsistent read. Because
changes are batched and written together at commit, any code path that reads
the database directly, rather than through the same unit of work, during
that window sees a state that has already been superseded in memory but not
yet in storage. Where that direct-read path is an authorization check, for
example a permission lookup performed by a second service against the raw
database rather than through the same session, the check can act on stale
data. The fix is architectural. authorization decisions that must be
consistent with a pending change belong inside the same unit of work's scope,
not outside it.

Registration and identity-map state is per-session and must not cross
tenants. In a multi-tenant system, a unit of work or its identity map that
outlives its intended scope, the cross-request leakage failure mode from
dimension 11, is not only a correctness bug but a data-isolation bug. an
object belonging to tenant A, still attached to a unit of work that a
subsequent request from tenant B reuses, can be read or, worse, silently
written by the wrong tenant's request. Scoping discipline is therefore a
security control here, not only a performance or correctness one, and the
test in dimension 15 that asserts two concurrent requests never share a unit
of work instance is doing security-relevant work.

Large, silently deferred batches are a denial-of-service surface. An
attacker-influenced input that causes a loop to register far more objects
than the operation was designed for, for example a bulk import endpoint with
no upper bound on row count, turns a single request into an
unboundedly-large in-memory graph and an unboundedly-large single database
transaction. Because nothing is written until commit, the cost is invisible
to naive request-rate monitoring until the commit itself either times out or
exhausts memory. Bound the number of objects a single unit of work may
register, and reject or paginate an operation that would exceed that bound,
rather than trusting the pattern's batching to absorb an unbounded input.

On plain data privacy the pattern is silent beyond what any persistence layer
already implies. sensitive field values held in a tracked, in-memory object
for the duration of the unit of work are subject to the same memory-handling
and logging discipline as any other in-process data, and the observability
advice in dimension 16 to log registered-object counts should not extend to
logging the objects' field values themselves.

## Code examples

Three languages chosen for genuinely different idiomatic shapes. Java shows
the registered, explicit-list variant closest to Fowler's own description.
TypeScript shows the same registered shape with a lighter, interface-based
Data Mapper, plus how the pattern looks against an async, promise-based
database driver. Python shows the automatic, snapshot-comparison variant,
which is closer to how SQLAlchemy's own Session behaves internally, and is
the idiomatic Python shape because the language makes attribute-level
interception straightforward. Go is omitted from the code samples because,
per the language note in dimension 8, an idiomatic Go implementation differs
from the other three only in syntax, not in shape. it is the same explicit,
hand-passed session object as the TypeScript example with Go's usual
explicit-error-return style layered on top, and including it would repeat
the pattern rather than show a genuinely different one. Rust and Swift are
omitted for the same reason, plus the added friction that automatic dirty
checking over shared mutable state runs directly against both languages'
ownership models, which is exactly the argument in dimension 8 for the
functional, command-list variant rather than a snapshot-comparison Unit of
Work in either language.

### Java

```java
import java.util.*;

interface Mapper<T> {
    void insert(T obj);
    void update(T obj);
    void delete(T obj);
}

final class Invoice {
    final long id;
    boolean paid;
    Invoice(long id, boolean paid) {
        this.id = id;
        this.paid = paid;
    }
}

final class Order {
    long id;
    String customerRef;
    Order(String customerRef) {
        this.customerRef = customerRef;
    }
}

final class UnitOfWork {
    private final List<Object> newObjects = new ArrayList<>();
    private final Map<Object, Boolean> dirtyObjects = new LinkedHashMap<>();
    private final List<Object> removedObjects = new ArrayList<>();
    private final Mapper<Order> orderMapper;
    private final Mapper<Invoice> invoiceMapper;

    UnitOfWork(Mapper<Order> orderMapper, Mapper<Invoice> invoiceMapper) {
        this.orderMapper = orderMapper;
        this.invoiceMapper = invoiceMapper;
    }

    void registerNew(Object obj) {
        newObjects.add(obj);
    }

    void registerDirty(Object obj) {
        if (!newObjects.contains(obj)) {
            dirtyObjects.put(obj, true);
        }
    }

    void registerRemoved(Object obj) {
        newObjects.remove(obj);
        dirtyObjects.remove(obj);
        removedObjects.add(obj);
    }

    @SuppressWarnings("unchecked")
    void commit() {
        for (Object obj : newObjects) {
            if (obj instanceof Order) {
                orderMapper.insert((Order) obj);
            }
        }
        for (Object obj : dirtyObjects.keySet()) {
            if (obj instanceof Invoice) {
                invoiceMapper.update((Invoice) obj);
            }
        }
        for (Object obj : removedObjects) {
            if (obj instanceof Invoice) {
                invoiceMapper.delete((Invoice) obj);
            }
        }
        newObjects.clear();
        dirtyObjects.clear();
        removedObjects.clear();
    }
}

public final class Demo {
    public static void main(String[] args) {
        Mapper<Order> orderMapper = new Mapper<Order>() {
            public void insert(Order o) { System.out.println("INSERT order " + o.customerRef); }
            public void update(Order o) { }
            public void delete(Order o) { }
        };
        Mapper<Invoice> invoiceMapper = new Mapper<Invoice>() {
            public void insert(Invoice i) { }
            public void update(Invoice i) { System.out.println("UPDATE invoice " + i.id + " paid=" + i.paid); }
            public void delete(Invoice i) { }
        };

        UnitOfWork uow = new UnitOfWork(orderMapper, invoiceMapper);

        Order order = new Order("cust-42");
        uow.registerNew(order);

        Invoice invoice = new Invoice(7, false);
        invoice.paid = true;
        uow.registerDirty(invoice);

        uow.commit();
    }
}
```

### TypeScript

```typescript
interface Mapper<T> {
  insert(obj: T): Promise<void>;
  update(obj: T): Promise<void>;
  remove(obj: T): Promise<void>;
}

class Order {
  constructor(public customerRef: string) {}
}

class Invoice {
  constructor(public id: number, public paid: boolean) {}
}

class UnitOfWork {
  private newOrders: Order[] = [];
  private dirtyInvoices: Set<Invoice> = new Set();
  private removedInvoices: Invoice[] = [];

  constructor(
    private orderMapper: Mapper<Order>,
    private invoiceMapper: Mapper<Invoice>
  ) {}

  registerNew(order: Order): void {
    this.newOrders.push(order);
  }

  registerDirty(invoice: Invoice): void {
    this.dirtyInvoices.add(invoice);
  }

  registerRemoved(invoice: Invoice): void {
    this.dirtyInvoices.delete(invoice);
    this.removedInvoices.push(invoice);
  }

  async commit(): Promise<void> {
    for (const order of this.newOrders) {
      await this.orderMapper.insert(order);
    }
    for (const invoice of this.dirtyInvoices) {
      await this.invoiceMapper.update(invoice);
    }
    for (const invoice of this.removedInvoices) {
      await this.invoiceMapper.remove(invoice);
    }
    this.newOrders = [];
    this.dirtyInvoices.clear();
    this.removedInvoices = [];
  }
}

async function main() {
  const orderMapper: Mapper<Order> = {
    async insert(o) { console.log("INSERT order", o.customerRef); },
    async update(_o) {},
    async remove(_o) {},
  };
  const invoiceMapper: Mapper<Invoice> = {
    async insert(_i) {},
    async update(i) { console.log("UPDATE invoice", i.id, "paid=", i.paid); },
    async remove(_i) {},
  };

  const uow = new UnitOfWork(orderMapper, invoiceMapper);

  const order = new Order("cust-42");
  uow.registerNew(order);

  const invoice = new Invoice(7, false);
  invoice.paid = true;
  uow.registerDirty(invoice);

  await uow.commit();
}

main();
```

### Python

The automatic, snapshot-comparison variant. No explicit registration call.
dirtiness is computed at commit time by comparing tracked state against a
snapshot taken when each object entered the unit of work.

```python
import copy


class Order:
    def __init__(self, customer_ref):
        self.customer_ref = customer_ref


class Invoice:
    def __init__(self, id, paid):
        self.id = id
        self.paid = paid


class UnitOfWork:
    def __init__(self):
        self._new = []
        self._tracked = {}   # id(obj) -> (obj, snapshot)
        self._removed = []

    def register_new(self, obj):
        self._new.append(obj)

    def track(self, obj):
        # Called once, usually right after loading an object from storage.
        self._tracked[id(obj)] = (obj, copy.deepcopy(vars(obj)))

    def register_removed(self, obj):
        self._tracked.pop(id(obj), None)
        self._removed.append(obj)

    def _dirty_objects(self):
        dirty = []
        for obj, snapshot in self._tracked.values():
            if vars(obj) != snapshot:
                dirty.append(obj)
        return dirty

    def commit(self, order_mapper, invoice_mapper):
        for order in self._new:
            order_mapper.insert(order)
        for invoice in self._dirty_objects():
            invoice_mapper.update(invoice)
        for invoice in self._removed:
            invoice_mapper.delete(invoice)
        self._new.clear()
        self._tracked.clear()
        self._removed.clear()


class OrderMapper:
    def insert(self, order):
        print(f"INSERT order {order.customer_ref}")


class InvoiceMapper:
    def update(self, invoice):
        print(f"UPDATE invoice {invoice.id} paid={invoice.paid}")

    def delete(self, invoice):
        print(f"DELETE invoice {invoice.id}")


if __name__ == "__main__":
    uow = UnitOfWork()

    order = Order("cust-42")
    uow.register_new(order)

    invoice = Invoice(id=7, paid=False)
    uow.track(invoice)     # snapshot taken here, as if just loaded
    invoice.paid = True    # no call back into uow, dirtiness is inferred

    uow.commit(OrderMapper(), InvoiceMapper())
```

## 18. References

1. Martin Fowler. Patterns of Enterprise Application Architecture.
   Addison-Wesley, 2002. ISBN 0-321-12742-0. Chapter 11, object-relational
   behavioral patterns, "Unit of Work". Source of the intent, the four
   participants, the registered and automatic variants, and the insert
   before update and delete ordering rule.
2. Martin Fowler. "Unit of Work", online catalog entry.
   https://martinfowler.com/eaaCatalog/unitOfWork.html verified 2026-08-02.
   Source of the exact intent wording quoted in dimension 1.
3. Red Hat / Hibernate ORM project. Hibernate ORM Introduction Guide,
   current release, "Persistence Context".
   https://docs.hibernate.org/orm/current/introduction/html_single/Hibernate_Introduction.html
   verified 2026-08-02. Source for the Hibernate Session production use in
   dimension 9.
4. Oracle. Java EE 7 API Specification, javax.persistence.EntityManager.
   https://docs.oracle.com/javaee/7/api/javax/persistence/EntityManager.html
   verified 2026-08-02. Source for the JPA persistence context production
   use and the flush() semantics in dimension 9.
5. SQLAlchemy project. SQLAlchemy 2.0 Documentation, "Session Basics".
   https://docs.sqlalchemy.org/en/20/orm/session_basics.html verified
   2026-08-02. Source for the explicit "unit of work pattern" naming and the
   identity map description quoted in dimension 9.
6. Microsoft. Entity Framework Core documentation, "Basic Save Changes".
   https://learn.microsoft.com/en-us/ef/core/saving/basic verified
   2026-08-02. Source for the DbContext change tracking and transactional
   SaveChanges production use in dimension 9.
7. Eric Evans. Domain-Driven Design. Tackling Complexity in the Heart of
   Software. Addison-Wesley, 2003. ISBN 0-321-12521-5. Part 3, the
   aggregate and repository discussion. Source of the aggregate-scoped
   transaction boundary reading in dimension 8 and the aggregate-boundary
   violation failure mode in dimension 11.
