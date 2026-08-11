---
name: Identity Map
slug: identity-map
family: 06-enterprise-application-architecture
category: Object-Relational Behavioral
aliases: [Object Cache, Session Cache, First-Level Cache, Persistence Context Uniqueness]
first_described: "Fowler 2002"
maturity: canonical
related: [unit-of-work, lazy-load, data-mapper, repository]
incompatible_with: []
verified: 2026-08-02
---

# Identity Map

## 1. Name, aliases, and lineage

The canonical name is Identity Map. Martin Fowler catalogued it in *Patterns of
Enterprise Application Architecture*, Addison-Wesley, 2002, in the Object-Relational
Behavioral Patterns chapter, and describes the intent as loading each object at
most once by keeping every loaded object in a map, then looking objects up
through that map on every later reference instead of loading them again
(Martin Fowler, "Identity Map",
[martinfowler.com/eaaCatalog/identityMap.html](https://martinfowler.com/eaaCatalog/identityMap.html),
verified 2026-08-02).

Fowler credits the idea as folklore rather than his own invention, noting in the
same catalog entry that the pattern predates his write-up and circulated in the
Smalltalk object-database community before he named and formalized it for the
book. The pattern is old enough, and common enough, that most people meet it
under one of its implementation names rather than its catalog name.

Three names appear most often in practice and they name the same structural
idea at different scopes.

- **Identity Map**, the catalog name from Fowler, used when discussing the
  pattern in the abstract or when a codebase builds its own explicit map data
  structure by hand, independent of any ORM.
- **First-level cache** or **session cache**, the name Hibernate and the Java
  Persistence API community use for the identity-map behavior that lives
  inside an `EntityManager` or `Session`. The Java EE Tutorial and the JPA
  specification describe the persistence context's uniqueness requirement,
  that "a persistence context is a set of entities such that for any
  persistent identity there is a unique entity instance" (Oracle, "Persistence
  Context", section 7.3,
  [docs.oracle.com/cd/E24001_01/apirefs.1111/e13946/ejb3_overview_emfactory_perscontext.html](https://docs.oracle.com/cd/E24001_01/apirefs.1111/e13946/ejb3_overview_emfactory_perscontext.html),
  verified 2026-08-02). This is Identity Map by another name, scoped to the
  lifetime of a persistence context.
- **Object identity table** or, informally, just "the session's identity map",
  the phrasing used by Doctrine's own documentation, which states plainly that
  "Doctrine uses the Identity Map pattern to track objects" inside its
  `UnitOfWork`, keyed on a two-level array of root entity name and id (Doctrine
  Project, "Working with Objects" and "Doctrine Internals explained",
  [doctrine-project.org/projects/doctrine-orm/en/3.6/reference/unitofwork.html](https://www.doctrine-project.org/projects/doctrine-orm/en/3.6/reference/unitofwork.html),
  verified 2026-08-02).

The names diverge by community, not by mechanism. A Java engineer who has never
heard "Identity Map" and a Ruby engineer who has never heard "first-level cache"
are both describing the same table when they explain why calling `find(id)`
twice on the same session returns the identical object reference rather than
two equal-but-distinct copies.

## 2. Problem and context

An object-relational mapping layer loads rows from a database and turns them
into in-memory objects. The moment more than one code path in the same unit of
work can trigger a load of the same row, two failure modes appear together, and
neither one announces itself with an obvious stack trace.

The first is a correctness failure. Say an order-processing service loads
`Customer#42` to check a credit limit, and separately, deeper in the call
graph, a shipping calculation also loads `Customer#42` to read the shipping
address. Without a map remembering that row 42 is already in memory, the mapper
constructs two distinct `Customer` objects, each independently reflecting the
state of row 42 at the moment it was read. If the credit-limit code then
mutates its copy, setting a flag or decrementing a balance, that mutation is
invisible to the shipping code's copy. Two objects claiming to represent the
same real-world entity have silently diverged, and whichever one is saved last
wins, overwriting the other's change with no error and no warning. Fowler
states this directly, that identity maps address "the same object mapped to
different objects, or an inconsistency in one being missed" (Fowler,
*Patterns of Enterprise Application Architecture*, 2002, Object-Relational
Behavioral Patterns chapter).

The second is a performance failure. Even when the two loads never mutate
anything, each load is a round trip to the database, and in a request handler
that walks a graph of related objects (an order, its line items, and each line
item's product) it is common for the same row to be requested many times over
the course of one transaction. A map that remembers what has already been
loaded turns every repeat load into a dictionary lookup instead of a query, and
in a chatty domain model this routinely removes the majority of the redundant
queries in a single request.

The pattern belongs specifically in the object-relational mapping layer of a
system built around a domain model of long-lived, mutable, identity-bearing
objects (an Active Record or Data Mapper architecture), scoped to a single
unit of work such as a request, a transaction, or a batch job. It does not
belong in a stateless functional pipeline that treats every fetched row as an
immutable value, because there identical rows loaded twice are not a
correctness hazard, they are simply two equal values.

## 3. Forces

**Correctness of identity versus memory cost.** Every entry kept in the map is
a live reference the garbage collector cannot collect until the map itself is
released. A map that is never cleared, or that is scoped too broadly, becomes
an unbounded cache and a memory leak in a long-running process.

**Consistency versus staleness.** The map guarantees that within its scope,
every reference to a given identity resolves to the same in-memory object, and
therefore to the same state. That same guarantee is what makes the map's
contents stale the instant another process, or another connection outside the
map's scope, commits a change to the underlying row. The map trades
freshness-per-read for consistency-within-scope.

**Simplicity of call sites versus map bookkeeping complexity.** Once the map
exists, every code path that constructs a domain object from a row must be
routed through it, or the guarantee silently breaks for that one path. This
concentrates bookkeeping into the mapper layer so the rest of the codebase can
stay ignorant of identity management entirely, which is the pattern's whole
point, but it means the mapper's construction logic cannot be bypassed without
consequence.

**Coupling to a scope boundary.** The pattern only works if something owns a
clear beginning and end for the map's lifetime. A request, a transaction, a
`Session`, a `UnitOfWork`. Without an explicit scope the map has no natural
moment to be discarded, and correctness silently degrades into a growing,
increasingly stale global cache shared across unrelated operations.

**Concurrency and thread affinity.** A map scoped to one unit of work is
usually not built to be shared or synchronized across threads, because sharing
it defeats the isolation the scope boundary was meant to provide. This pushes
most implementations toward one map instance per request or per thread rather
than one process-wide map, which the pattern favors over a single global
structure that would need internal locking on every read and write.

The pattern favors correctness and locality of a bounded scope over
process-wide freshness or process-wide memory economy, and it deliberately
sacrifices any promise about what happens outside its scope boundary.

## 4. Applicability and non-applicability

Reach for an Identity Map when all of the following hold together.

- The domain model represents entities as mutable, identity-bearing objects
  (an `Order`, a `Customer`) rather than immutable value objects, and code in
  more than one place can independently trigger a load of the same row.
- A single unit of work (a request, a transaction, a batch job iteration) is
  the natural, well-defined scope in which "the same object" must mean
  literally the same reference, and that scope has a clear start and end you
  can hook a map's lifecycle to.
- The mapper or repository layer already funnels every row-to-object
  construction through one code path (or can be made to), so the map can be
  consulted before construction and populated after it, with no way for a
  caller to bypass it.
- Lazy loading, a Unit of Work, or both are already in play, because those
  patterns depend on being able to find "the object for this row" reliably,
  and an Identity Map is what makes that lookup possible and cheap.

Do NOT reach for it when any of these hold.

- The data being fetched is read as immutable values rather than mutable
  entities (a reporting query, a DTO projection, a search-result list meant to
  be displayed once and discarded). Wrapping read-only value objects in an
  identity map adds bookkeeping cost for a correctness guarantee nothing needs,
  because there is no mutation to protect against divergence.
  Fowler states this directly, contrasting Identity Map's applicability to a
  mutable domain model against a simpler read path for reporting (Fowler,
  *Patterns of Enterprise Application Architecture*, 2002, Object-Relational
  Behavioral Patterns chapter, Identity Map).
- The application is stateless per request with no shared mutable domain
  objects at all, for example a thin CRUD layer that maps each row directly to
  a response DTO and never holds an object across two operations. There is no
  identity to protect because nothing ever asks "is this the same object I
  already have."
- The unit of work you would scope the map to is unbounded or ill-defined, for
  example a long-lived singleton service, a background worker with no
  per-task boundary, or a shared cache meant to live across many unrelated
  requests. An Identity Map scoped that broadly stops being a correctness tool
  and becomes an unmanaged, ever-growing, increasingly stale cache, which is a
  different problem with different solutions (an actual cache with eviction,
  TTLs, and invalidation, not an identity map).
- Multiple processes, or multiple database connections outside the map's own
  transaction, can concurrently modify the same row. The map has no mechanism
  to detect that its cached object is now stale relative to the database, and
  presenting it as authoritative in that situation is actively misleading. A
  Unit of Work with optimistic locking, or explicit re-fetching, addresses that
  concern, the Identity Map alone does not.
- The mapper cannot guarantee every construction path goes through the map. A
  partial identity map, one that some code paths honor and others silently
  bypass by constructing objects directly, is worse than no identity map,
  because it gives the illusion of the guarantee while regularly breaking it.

## 5. Structure

- **Client.** The application or domain code that asks for an object by its
  identity, typically through a repository or mapper method, and is unaware
  that a map exists behind that call.
- **Finder / Mapper (the map's owner).** The object-relational mapping code
  that owns the lookup-then-construct-then-register sequence. Before issuing a
  database query it consults the map. If the map has an entry for the
  requested identity, it returns that object and skips the query entirely. If
  not, it queries, constructs the domain object from the row, registers the new
  object in the map keyed by its identity, then returns it.
- **Identity Map.** The registry itself, structurally a dictionary or hash
  table from a key (the object's identity) to the in-memory object that
  represents it. In a system with several distinct entity types, the
  implementation is almost always one map per type (a `Customer` map, an
  `Order` map), because two different entity types can share a numeric primary
  key value without being the same identity, and per-type maps avoid that
  collision without needing a compound key everywhere.
- **Identity Key.** The value, or composite of values, that uniquely identifies
  one row, most often the primary key. Doctrine's own identity map is keyed on
  exactly this shape, "root entity name" and a serialized form of the primary
  key, precisely to disambiguate identical numeric ids across different entity
  types (Doctrine Project, "Doctrine Internals explained",
  [doctrine-project.org/projects/doctrine-orm/en/3.6/reference/unitofwork.html](https://www.doctrine-project.org/projects/doctrine-orm/en/3.6/reference/unitofwork.html),
  verified 2026-08-02).
- **Scope owner.** Whatever construct opens and closes the map's lifetime, a
  `Session`, a `UnitOfWork`, a request-scoped container, or in a hand-rolled
  implementation, a simple object created at the top of a transaction and
  discarded at its end. The scope owner is what turns "an object cache" into
  "an Identity Map", because without a defined end to its lifetime the
  structure is not scoped to a unit of work at all, it is just a cache.

## 6. ASCII structure diagram

```
+-------------------+        find(id)        +------------------------+
|      Client        | ----------------------> |  Finder / Mapper        |
| (domain / service   |                        |  (owns the lookup      |
|  code)              | <----------------------|   sequence)             |
+-------------------+     domain object       +------------------------+
                                                  |            ^
                                     1. lookup(id)|            | 3. register(id, obj)
                                                  v            |
                                          +----------------------------+
                                          |       Identity Map          |
                                          |  Map<IdentityKey, Object>   |
                                          |  scoped to a Unit of Work   |
                                          +----------------------------+
                                                  |
                                     2. miss: query, then build
                                                  v
                                          +----------------------------+
                                          |         Database            |
                                          |  (row identified by key)    |
                                          +----------------------------+

  Per-entity-type maps, held by one scope owner:

  UnitOfWork
    +-- CustomerMap : Map<CustomerId, Customer>
    +-- OrderMap    : Map<OrderId, Order>
    +-- ProductMap  : Map<ProductId, Product>
```

## 7. Dynamics

Two runs of the same lookup within one scope produce different paths, a miss
followed later by a hit, and the difference is the entire point of the
pattern.

```
Sequence, first request for Customer#42 (a miss):

Client            Mapper                 IdentityMap[Customer]     Database
  |  find(42)       |                          |                     |
  |----------------->|                          |                     |
  |                  |  lookup(42)              |                     |
  |                  |------------------------->|                     |
  |                  |  <not found>              |                     |
  |                  |<-------------------------|                     |
  |                  |  SELECT * FROM customer WHERE id = 42           |
  |                  |------------------------------------------------>|
  |                  |  <row>                                          |
  |                  |<------------------------------------------------|
  |                  |  new Customer(row)                              |
  |                  |  register(42, customerObj)                      |
  |                  |------------------------->|                     |
  |  customerObj      |                          |                     |
  |<-----------------|                          |                     |

Sequence, second request for Customer#42 in the SAME scope (a hit):

Client            Mapper                 IdentityMap[Customer]     Database
  |  find(42)       |                          |                     |
  |----------------->|                          |                     |
  |                  |  lookup(42)              |                     |
  |                  |------------------------->|                     |
  |                  |  customerObj (same ref)  |                     |
  |                  |<-------------------------|                     |
  |  customerObj      |                          |    (no query fired)|
  |<-----------------|                          |                     |

Scope boundary:

  BEGIN unit of work  --->  map is created empty
  ... any number of find() calls, hits and misses ...
  COMMIT / END unit of work  --->  map is discarded, references released
```

The critical property visible in the second sequence is that the two calls to
`find(42)` return the identical object reference, not two objects that merely
compare equal. That is what makes a mutation made through one reference visible
through the other, because there is, structurally, only one object.

## 8. Implementation variants

**Hand-rolled per-mapper map.** The simplest and most direct form, a private
dictionary field on the mapper or repository class itself, scoped to the
lifetime of that mapper instance. This is the shape shown in the code samples
below and the shape Fowler demonstrates in the book's Java examples.

**ORM-embedded first-level cache.** The map lives inside the ORM's session or
entity-manager object rather than in application code at all, and the
application never interacts with it directly, only through `find`,
`get`, or the query API. Hibernate's `Session` and JPA's `EntityManager` are
the canonical example, where the persistence context transparently guarantees
that "for any persistent identity there is a unique entity instance" for the
lifetime of that context (Oracle, "Persistence Context", section 7.3,
[docs.oracle.com/cd/E24001_01/apirefs.1111/e13946/ejb3_overview_emfactory_perscontext.html](https://docs.oracle.com/cd/E24001_01/apirefs.1111/e13946/ejb3_overview_emfactory_perscontext.html),
verified 2026-08-02).

**Composite key variant.** Where a natural key is compound (a `(tenant_id,
order_id)` pair in a multi-tenant system, for example), the map key is a
serialized or tuple form of the compound key rather than a single scalar,
exactly as Doctrine's internal identity map does, keying two levels deep on
entity type and a "sorted, serialized version of all the key columns"
(Doctrine Project, "Working with Objects",
[doctrine-project.org/projects/doctrine-orm/en/3.6/reference/working-with-objects.html](https://www.doctrine-project.org/projects/doctrine-orm/en/3.6/reference/working-with-objects.html),
verified 2026-08-02).

**Weak-reference map.** In languages with weak references available (Java's
`WeakHashMap`, or a manual weak-reference wrapper), the map can hold weak
references to its entries so that an object with no other live references can
still be garbage-collected even while the map technically still "knows" about
it. This trades a small amount of correctness (a rare re-fetch after a GC
sweep clears an entry nothing else was holding) for a lower risk of the map
becoming an unbounded retention root in a very long-lived scope. It is
uncommon in request-scoped implementations, where the whole map is discarded
at request end regardless, and more relevant in long-lived batch-processing
scopes.

**Read-through versus explicit registration.** Some implementations fold the
map lookup and the query into one method (`find(id)`, shown in the dynamics
diagram above), so a caller never sees the miss path directly. Others expose a
lower-level `register(object)` the mapper calls explicitly after any
construction, including construction that happens as a side effect of another
query (for example, loading an order also loads and registers its customer).
The second style is necessary whenever more than one code path can produce a
newly constructed object for the same identity, because a read-through
`find(id)` alone does not cover objects that arrive via a join or an eager
load rather than a direct lookup.

## 9. Known production uses

- **Hibernate ORM**, where the `Session`'s persistence context acts as a
  first-level cache implementing exactly this guarantee, that within one
  session at most one Java object represents a given database row. Hibernate's
  own reference documentation describes the `Session` as maintaining "a
  generally repeatable read persistence context (first level cache) of the
  application domain model" (Hibernate, *Hibernate User Guide*, version 6.4,
  Architecture Overview,
  [docs.hibernate.org/orm/6.4/userguide/html_single/Hibernate_User_Guide.html](https://docs.hibernate.org/orm/6.4/userguide/html_single/Hibernate_User_Guide.html),
  verified 2026-08-02).
- **The Java Persistence API**, standardized across every JPA-compliant
  provider (Hibernate, EclipseLink, OpenJPA), where the `EntityManager`'s
  persistence context enforces the uniqueness requirement, "a persistence
  context is a set of entities such that for any persistent identity there is
  a unique entity instance" (Oracle, "Persistence Context", section 7.3,
  [docs.oracle.com/cd/E24001_01/apirefs.1111/e13946/ejb3_overview_emfactory_perscontext.html](https://docs.oracle.com/cd/E24001_01/apirefs.1111/e13946/ejb3_overview_emfactory_perscontext.html),
  verified 2026-08-02).
- **Doctrine ORM** (PHP), which states outright in its own reference
  documentation that "Doctrine uses the Identity Map pattern to track
  objects", implemented inside `UnitOfWork` as an identity map keyed on entity
  type and a serialized composite of the primary key columns (Doctrine
  Project, "Working with Objects" and "Doctrine Internals explained",
  [doctrine-project.org/projects/doctrine-orm/en/3.6/reference/unitofwork.html](https://www.doctrine-project.org/projects/doctrine-orm/en/3.6/reference/unitofwork.html),
  verified 2026-08-02).
- **SQLAlchemy** (Python), whose `Session` exposes `session.identity_map`
  directly, documented as a "dictionary of all persistent objects, keyed on
  their identity key". Within a session, calling the same query twice for the
  same primary key returns the same Python object (SQLAlchemy, "Session State
  Management",
  [docs.sqlalchemy.org/en/20/orm/session_state_management.html](https://docs.sqlalchemy.org/en/20/orm/session_state_management.html),
  verified 2026-08-02).

## 10. Consequences

Positive.

- Removes a whole class of divergent-state bugs where two in-memory
  representations of the same row silently drift apart because a mutation
  made through one is invisible to the other.
- Removes redundant round trips to the database for rows already loaded within
  the current scope, which is often the single largest reduction available to
  a chatty domain model without changing its query shape at all.
- Concentrates the identity-management concern into the mapper layer, so
  application and domain code can treat "the object for this id" as simply
  true without ever reasoning about caching or duplicate loads themselves.
- Makes reference equality (`==` in most languages) a valid and reliable test
  for "is this the same entity" within the map's scope, which simplifies
  in-memory graph traversal, deduplication, and change tracking.

Negative.

- Every entry is a live reference the garbage collector cannot collect while
  the map exists, so an unbounded or long-lived map's scope directly becomes a
  memory-retention risk.
- The guarantee is only as strong as the discipline of the construction path.
  Any code that builds a domain object without registering it in the map
  breaks the guarantee silently, producing exactly the divergent-object bug
  the pattern exists to prevent, but now hidden behind an apparent guarantee
  that no longer actually holds.
- The cached object can be stale relative to the database the instant another
  connection commits a change to the same row, and the map has no built-in
  mechanism to detect or signal that. Fowler explicitly frames this as the
  reason Identity Map matters most within a bounded unit of work and does not
  promise anything across separate transactions.
- Thread-unsafe by default in most hand-rolled and per-session implementations.
  Sharing a single map instance across concurrent requests without explicit
  synchronization reintroduces the exact race conditions the pattern is meant
  to close.

## 11. Failure modes and misuse

**Symptom.** Two objects that are supposed to represent the same row compare
unequal by reference, and a change made to one silently vanishes when the
other is saved. **Cause.** A construction path bypassed the map, most commonly
a raw SQL query, a bulk-load routine, or a second mapper method that
constructs objects directly instead of delegating to the map-aware finder.
**Fix.** Audit every place that constructs the entity type in question and
route all of them through the single register-on-construct path, or, in an
ORM, confirm the bypass is a native query or bulk update that is documented as
intentionally outside the persistence context, and handle staleness there
explicitly (a manual refresh or clear).

**Symptom.** Memory usage in a long-running worker process climbs steadily
over hours and is never released, correlating with the number of distinct
rows processed rather than with concurrent load. **Cause.** The identity map
was scoped to the process or to a long-lived service object rather than to a
bounded unit of work, so it accumulates one entry per distinct row ever
touched and never releases any of them. **Fix.** Scope the map explicitly to a
transaction, request, or batch, and discard it (or call the ORM's `clear()` or
equivalent) at that scope's natural end, rather than reusing one map across
unrelated units of work.

**Symptom.** A read that should reflect a very recent external change (a row
updated by a different process moments ago) instead returns visibly outdated
data, even though the query clearly should have hit the database. **Cause.**
The identity map served a cached object from an earlier point in the same
scope instead of re-querying, because from the map's perspective nothing asked
it to refresh, it simply answered a lookup as designed. **Fix.** Where
freshness matters mid-transaction, explicitly refresh or evict the specific
entry (most ORMs expose a `refresh()` or `evict()` call) rather than relying on
implicit re-querying, and treat "the map might be stale relative to concurrent
writers" as an accepted, named trade-off rather than a surprise.

**Symptom.** Two entities of genuinely different types (a `Customer` with id
7 and an `Order` with id 7) intermittently resolve to the wrong object, or a
lookup for one type unexpectedly returns an object of the other type.
**Cause.** A single shared map was keyed on the raw numeric id alone across
multiple entity types instead of on a composite key of type plus id, so two
unrelated rows with the same numeric primary key collide in the same
dictionary slot. **Fix.** Key the map on entity type plus identity, either
with one map instance per type (the common approach) or with an explicit
composite key that includes the type, matching the two-level keying Doctrine
documents for its own identity map (Doctrine Project, "Doctrine Internals
explained",
[doctrine-project.org/projects/doctrine-orm/en/3.6/reference/unitofwork.html](https://www.doctrine-project.org/projects/doctrine-orm/en/3.6/reference/unitofwork.html),
verified 2026-08-02).

**Symptom.** Under concurrent load, objects returned to different threads
occasionally show interleaved or corrupted field values that neither thread
wrote. **Cause.** A single identity map instance, meant to be scoped
per-request or per-thread, was inadvertently shared and mutated concurrently
without synchronization. **Fix.** Confirm the scope owner (session, unit of
work, request context) truly creates one map per unit of work rather than
reusing a shared instance, which is the standard, thread-safe-by-construction
approach every named production use above follows.

## 12. Trade-off matrix

| Force | Identity Map | No caching, always requery | Global process-wide cache with TTL | Unit of Work alone (no map) |
|---|---|---|---|---|
| Correctness of in-memory identity within a unit of work | Guaranteed, one object per identity | Not guaranteed, duplicate objects can diverge | Not guaranteed for identity, only for value freshness | Tracks changes but does not prevent duplicate object construction |
| Redundant query elimination | Strong, within scope | None | Strong, but across unrelated requests too | None on its own |
| Staleness risk versus concurrent writers | Present, bounded to scope lifetime | None, always current | Present, bounded by TTL, spans unrelated requests | None on its own, no caching happens |
| Memory retention risk | Bounded by scope, real if scope is too broad | None | High, unbounded unless evicted actively | None |
| Implementation cost | Low to moderate, one map plus discipline at construction sites | None | Moderate to high, needs eviction and invalidation policy | Moderate, needs explicit dirty tracking |
| Thread-safety model | Simple, one map per scope, no sharing needed | Trivially safe, nothing shared | Requires explicit synchronization or a concurrent map | Depends on the Unit of Work's own scoping |

Identity Map and Unit of Work are usually adopted together rather than as
alternatives. the comparison to "Unit of Work alone" above isolates what an
Identity Map specifically adds (duplicate-object prevention) on top of what a
Unit of Work alone provides (change tracking and commit orchestration).

## 13. Related and incompatible patterns

**Unit of Work.** The two patterns are near-inseparable in practice. Unit of
Work tracks which objects were read, created, changed, or deleted so it can
commit the right set of database operations at the end of a transaction, and
it needs to know, for any given identity, whether an object already exists in
its scope before deciding whether a load is a fresh read or a cache hit. Most
production implementations (Hibernate's `Session`, SQLAlchemy's `Session`,
Doctrine's `EntityManager`) fold the Identity Map directly into the Unit of
Work's own data structures rather than keeping them as two separate objects,
because they share the same scope boundary by necessity.

**Lazy Load.** Lazy loading defers fetching an associated object until it is
actually accessed, and when that deferred fetch finally happens, it must
consult the identity map first, exactly like any other load, or the same
association traversed from two different starting objects could produce two
different in-memory copies of the target. The two patterns compose cleanly.
Lazy Load decides when to fetch, Identity Map decides whether the fetch is
actually necessary or can be satisfied from the map.

**Data Mapper.** A Data Mapper is the natural owner of an Identity Map,
because the mapper is already the single funnel through which every row
becomes an object, which is exactly the discipline the map depends on. An
Active Record architecture can still use an Identity Map, but has to enforce
the same discipline across every place a row is loaded, since Active Record
does not naturally centralize construction the way a Data Mapper does.

**Repository.** A repository built on top of Data Mapper typically exposes
`find(id)` as its primary read method, and that method is the natural
read-through entry point into the identity map, matching the dynamics
described in section 7.

**Value Object.** Value objects are the pattern's natural exclusion, not an
incompatibility so much as a deliberate non-application. A value object has no
identity to protect, two value objects with the same field values are simply
equal, not "the same object", so wrapping value object construction in an
identity map adds cost for a guarantee that has nothing to protect.

## 14. Refactoring path in and out

**Introducing an Identity Map into code that lacks one.** Start by locating
every place the codebase currently constructs the entity type in question from
a database row. This is usually more places than expected, direct repository
methods, eager-load code for associations, and any bulk-fetch or search
method. Introduce a single map, scoped to whatever object already represents
the current unit of work (a request context, a transaction wrapper, or a new
purpose-built scope object if none exists yet). Change each construction site
to first check the map by identity key, and to register the newly constructed
object in the map immediately after construction and before returning it,
never before, since another concurrent path within the same scope could
otherwise register a competing object for the same key. Verify with a
targeted test, load the same id twice within one scope and assert the two
results are reference-identical, not merely equal, the specific property the
map exists to guarantee.

**Removing an Identity Map that no longer earns its place.** This is rare and
usually only correct when a codebase has already migrated away from a mutable
domain model toward read-only value objects or DTOs for the affected entity
type, at which point the map's correctness guarantee has nothing left to
protect. Confirm no code path currently depends on reference equality for the
entity type (grep for `===`, `is`, or reference-comparison idioms against
instances of that type), remove the map and its registration calls, and
replace any reference-equality checks with value-equality checks on the
identity key instead. If the removal is really about reducing memory
footprint rather than about the domain model changing shape, prefer narrowing
the map's scope first (a request-scoped map instead of a longer-lived one)
before removing it outright, since scope narrowing usually solves the memory
concern without giving up the correctness guarantee.

## 15. Testing and verification

An Identity Map makes one specific property directly and cheaply testable,
reference identity, which is exactly what makes tests for it clear and
worthwhile.

- **Same-scope, same-id test.** Request the same entity by id twice within one
  unit of work and assert the two returned references are identical (`is` in
  Python, `==` on reference types in Java or C#, `===` in TypeScript for
  object references), not merely field-by-field equal. This is the single most
  direct test of the pattern's core guarantee and should exist for every
  entity type the map covers.
- **Cross-scope test.** Request the same entity by id in two separate,
  sequential units of work (two separate sessions or transactions) and assert
  the two returned objects are NOT the same reference, confirming the map's
  scope boundary is actually respected and it is not accidentally behaving as
  a process-wide singleton.
- **Mutation-propagation test.** Load an entity, mutate a field on the
  returned reference, then request the same id again within the same scope and
  assert the mutation is visible on the second reference too, proving the two
  calls really did return one shared object rather than two objects that
  happen to be equal at construction time.
- **Bypass-detection test.** Where the codebase has any construction path that
  does not go through the map (a bulk import, a raw query used for a report),
  write an explicit test asserting that objects from that path are excluded
  from, or explicitly reconciled with, the map, so a future refactor cannot
  silently reintroduce a duplicate-object bug through that path without a
  test failing.
- Test doubles rarely help here directly, because the map's behavior is
  precisely what is under test, replacing it with a mock removes the thing
  being verified. Prefer exercising the real map (or a minimal in-memory
  implementation identical in behavior) rather than mocking it away.

## 16. Observability signals

This is engineering judgement drawn from operating ORM-backed services, not a
sourced claim about any specific product's dashboards.

- **Map size at scope end.** Logging or metering the number of distinct
  entries registered in the map by the time a unit of work commits gives an
  early signal of an N+1-shaped access pattern, a request that touches an
  unexpectedly large number of distinct rows of one type is often loading a
  collection one row at a time instead of in a batch.
- **Hit versus miss ratio.** Where the ORM or hand-rolled mapper exposes it
  (Hibernate statistics, SQLAlchemy's own instrumentation hooks), tracking the
  ratio of map hits to misses within a scope surfaces whether the map is doing
  useful work at all, a ratio near zero across most requests suggests the
  domain model rarely revisits the same row and the map's performance benefit
  is marginal there, even though its correctness benefit may still matter.
- **Scope lifetime versus map growth.** Correlating how long a unit of work
  stays open against how large its map grows over that lifetime is the
  earliest warning sign of the "map scoped too broadly" failure mode from
  section 11, an unusually long-lived scope combined with steadily climbing
  map size points at a scope boundary that was never meant to be that long.
- A healthy instance looks like a map whose size stays proportional to the
  actual distinct entities a request or transaction touches, and that is
  reliably empty again immediately after the scope ends. A failing instance
  looks like map size climbing without bound across many sequential units of
  work sharing one process, which points at a scope leak rather than at the
  map itself being wrong.

## 17. Security and privacy implications

This dimension is analytical judgement, not a sourced finding about a specific
incident.

The map holds fully materialized domain objects in memory for the duration of
its scope, which means any personal or sensitive data present on those objects
persists in process memory for that whole window, not just for the instant a
query result is read and discarded. In a long-lived or broadly scoped map
(the same failure mode named in section 11), this extends how long sensitive
field values remain resident in memory, which matters for systems with memory
dump or crash report exposure surfaces, since a memory dump taken mid-request
could capture more sensitive objects than a purely stateless read path would
have held at that instant.

The pattern is otherwise silent on authorization. it caches whatever object
the mapper constructed, and if the mapper's underlying query already enforces
row-level access control (a tenant filter, an ownership check), the map
preserves that correctly scoped result. If the underlying query does not
enforce access control, the map does not add or remove any protection either
way, it simply caches whatever was returned. Any access-control concern here
belongs to the query and mapper construction logic, not to the identity map
itself.

## 18. References

- Martin Fowler, *Patterns of Enterprise Application Architecture*, Addison-Wesley,
  2002, Object-Relational Behavioral Patterns chapter, Identity Map.
- Martin Fowler, "Identity Map",
  [martinfowler.com/eaaCatalog/identityMap.html](https://martinfowler.com/eaaCatalog/identityMap.html),
  verified 2026-08-02.
- Oracle, "Persistence Context", section 7.3, Java EE 6 Tutorial,
  [docs.oracle.com/cd/E24001_01/apirefs.1111/e13946/ejb3_overview_emfactory_perscontext.html](https://docs.oracle.com/cd/E24001_01/apirefs.1111/e13946/ejb3_overview_emfactory_perscontext.html),
  verified 2026-08-02.
- Hibernate, *Hibernate User Guide*, version 6.4, Architecture Overview,
  [docs.hibernate.org/orm/6.4/userguide/html_single/Hibernate_User_Guide.html](https://docs.hibernate.org/orm/6.4/userguide/html_single/Hibernate_User_Guide.html),
  verified 2026-08-02.
- Doctrine Project, "Working with Objects", Doctrine ORM 3.6 reference,
  [doctrine-project.org/projects/doctrine-orm/en/3.6/reference/working-with-objects.html](https://www.doctrine-project.org/projects/doctrine-orm/en/3.6/reference/working-with-objects.html),
  verified 2026-08-02.
- Doctrine Project, "Doctrine Internals explained", Doctrine ORM 3.6 reference,
  [doctrine-project.org/projects/doctrine-orm/en/3.6/reference/unitofwork.html](https://www.doctrine-project.org/projects/doctrine-orm/en/3.6/reference/unitofwork.html),
  verified 2026-08-02.
- SQLAlchemy, "Session State Management", SQLAlchemy 2.0 ORM documentation,
  [docs.sqlalchemy.org/en/20/orm/session_state_management.html](https://docs.sqlalchemy.org/en/20/orm/session_state_management.html),
  verified 2026-08-02.

## Code examples

### TypeScript

```typescript
interface CustomerRow {
  id: number;
  name: string;
  creditLimit: number;
}

class Customer {
  constructor(public readonly id: number, public name: string, public creditLimit: number) {}
}

class Database {
  private rows = new Map<number, CustomerRow>([
    [42, { id: 42, name: "Ada Lovelace", creditLimit: 1000 }],
  ]);
  private queryCount = 0;

  fetchRow(id: number): CustomerRow {
    this.queryCount += 1;
    const row = this.rows.get(id);
    if (!row) throw new Error(`no row for id ${id}`);
    return row;
  }

  get queriesIssued(): number {
    return this.queryCount;
  }
}

class CustomerMapper {
  private identityMap = new Map<number, Customer>();

  constructor(private db: Database) {}

  find(id: number): Customer {
    const cached = this.identityMap.get(id);
    if (cached) return cached;

    const row = this.db.fetchRow(id);
    const customer = new Customer(row.id, row.name, row.creditLimit);
    this.identityMap.set(id, customer);
    return customer;
  }
}

const db = new Database();
const mapper = new CustomerMapper(db);

const first = mapper.find(42);
const second = mapper.find(42);

first.creditLimit = 500;

if (first !== second) throw new Error("expected the same reference");
if (second.creditLimit !== 500) throw new Error("mutation did not propagate");
if (db.queriesIssued !== 1) throw new Error(`expected 1 query, got ${db.queriesIssued}`);

console.log("identity map ok:", first === second, "queries issued:", db.queriesIssued);
```

### Python

```python
class CustomerRow:
    def __init__(self, id_, name, credit_limit):
        self.id = id_
        self.name = name
        self.credit_limit = credit_limit


class Customer:
    def __init__(self, id_, name, credit_limit):
        self.id = id_
        self.name = name
        self.credit_limit = credit_limit


class Database:
    def __init__(self):
        self._rows = {42: CustomerRow(42, "Ada Lovelace", 1000)}
        self.queries_issued = 0

    def fetch_row(self, id_):
        self.queries_issued += 1
        if id_ not in self._rows:
            raise KeyError(f"no row for id {id_}")
        return self._rows[id_]


class CustomerMapper:
    def __init__(self, db):
        self._db = db
        self._identity_map = {}

    def find(self, id_):
        if id_ in self._identity_map:
            return self._identity_map[id_]
        row = self._db.fetch_row(id_)
        customer = Customer(row.id, row.name, row.credit_limit)
        self._identity_map[id_] = customer
        return customer


if __name__ == "__main__":
    db = Database()
    mapper = CustomerMapper(db)

    first = mapper.find(42)
    second = mapper.find(42)

    first.credit_limit = 500

    assert first is second, "expected the same object"
    assert second.credit_limit == 500, "mutation did not propagate"
    assert db.queries_issued == 1, f"expected 1 query, got {db.queries_issued}"

    print("identity map ok:", first is second, "queries issued:", db.queries_issued)
```

### Java

```java
import java.util.HashMap;
import java.util.Map;

class CustomerRow {
    final int id;
    final String name;
    final int creditLimit;

    CustomerRow(int id, String name, int creditLimit) {
        this.id = id;
        this.name = name;
        this.creditLimit = creditLimit;
    }
}

class Customer {
    final int id;
    String name;
    int creditLimit;

    Customer(int id, String name, int creditLimit) {
        this.id = id;
        this.name = name;
        this.creditLimit = creditLimit;
    }
}

class Database {
    private final Map<Integer, CustomerRow> rows = new HashMap<>();
    private int queriesIssued = 0;

    Database() {
        rows.put(42, new CustomerRow(42, "Ada Lovelace", 1000));
    }

    CustomerRow fetchRow(int id) {
        queriesIssued++;
        CustomerRow row = rows.get(id);
        if (row == null) throw new RuntimeException("no row for id " + id);
        return row;
    }

    int queriesIssued() {
        return queriesIssued;
    }
}

class CustomerMapper {
    private final Database db;
    private final Map<Integer, Customer> identityMap = new HashMap<>();

    CustomerMapper(Database db) {
        this.db = db;
    }

    Customer find(int id) {
        Customer cached = identityMap.get(id);
        if (cached != null) return cached;

        CustomerRow row = db.fetchRow(id);
        Customer customer = new Customer(row.id, row.name, row.creditLimit);
        identityMap.put(id, customer);
        return customer;
    }
}

public class IdentityMapDemo {
    public static void main(String[] args) {
        Database db = new Database();
        CustomerMapper mapper = new CustomerMapper(db);

        Customer first = mapper.find(42);
        Customer second = mapper.find(42);

        first.creditLimit = 500;

        if (first != second) throw new AssertionError("expected the same reference");
        if (second.creditLimit != 500) throw new AssertionError("mutation did not propagate");
        if (db.queriesIssued() != 1) {
            throw new AssertionError("expected 1 query, got " + db.queriesIssued());
        }

        System.out.println("identity map ok: " + (first == second)
            + " queries issued: " + db.queriesIssued());
    }
}
```

Go, Rust, and Swift are omitted from the runnable set for this entry. The
pattern is a plain keyed cache guarded by a lookup-before-construct sequence,
which translates directly and without idiom-specific complications into any of
the three, and the three languages already shown (a structurally typed
language, a dynamically typed language, and a statically typed OOP language)
cover the range of construction styles the pattern actually varies across.
