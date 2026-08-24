---
name: Lazy Load
slug: lazy-load
family: 06-enterprise-application-architecture
category: Object-Relational Behavioral
aliases: [Lazy Initialization, Virtual Proxy, Value Holder, Ghost]
first_described: "Fowler 2002"
maturity: canonical
related: [identity-map, unit-of-work, data-mapper, active-record, proxy]
incompatible_with: []
verified: 2026-08-02
---

# Lazy Load

## 1. Name, aliases, and lineage

The canonical name is Lazy Load. It is documented in Martin Fowler, with
contributions from David Rice and Matthew Foemmel, *Patterns of Enterprise
Application Architecture*, Addison-Wesley, 2002, chapter 18, Object-Relational
Behavioral Patterns, the Lazy Load entry. Fowler states the intent in one
sentence, an object that does not contain all of the data you need but knows
how to get it (Martin Fowler, "Lazy Load", https://martinfowler.com/eaaCatalog/lazyLoad.html,
verified 2026-08-02, the web catalog mirror of the book chapter).

The book does not present Lazy Load as one technique. It presents it as a
problem with four named answers, and each answer has since become a name in
its own right in the frameworks that implement it.

- **Lazy Initialization.** A field starts at a marker value, usually null,
  and every accessor checks the marker before returning. The check happens on
  the object's own field, so no second object is involved.
- **Virtual Proxy.** A stand-in object implements the same interface as the
  real object and holds only its identity. The first method call on the proxy
  triggers the load of the real object, after which the proxy either
  delegates every call or replaces itself in the parent's reference.
- **Value Holder.** A generic wrapper object exposes a single accessor,
  commonly named getValue, and the caller must call through the wrapper
  rather than treat it as the real object. The wrapper does not pretend to
  be the target's interface.
- **Ghost.** The real object itself is constructed in a partial state, with
  only its identifier field set, and the first call to any of its other
  accessors populates every field on the object. A Ghost is not a stand-in,
  it is the object, briefly hollow.

These four earlier appeared without a shared name inside the object-oriented
persistence literature of the 1990s, the pattern the GoF Proxy entry calls a
Virtual Proxy is one of the four (Erich Gamma, Richard Helm, Ralph Johnson,
John Vlissides, *Design Patterns*, Addison-Wesley, 1994, chapter 4, Structural
Patterns, Proxy, page 208, the Virtual Proxy example loads an expensive image
object on first draw). Fowler's contribution was not to invent any of the four,
it was to name the shared problem, catalog the four solutions side by side, and
tie the choice explicitly to the object-relational mapping context, where
loading a graph of related rows is the recurring trigger.

## 2. Problem and context

An object graph persisted in a relational database is, by its nature, larger
than any single query needs. A Customer row references an Order table that can
hold years of history, an Order references OrderLine rows, an OrderLine
references a Product, and a Product references a Supplier. Reconstructing a
Customer object from the database means deciding, at the moment of the query,
how much of that graph to bring into memory.

Two answers are both wrong on their own. Load everything reachable from every
query, and a single Customer fetch drags in every order the customer ever
placed, every line on every order, every product referenced by every line, an
amount of I/O that has nothing to do with what the calling code asked for.
Load only the requested row and nothing else, and the very next line of code
that reads customer.orders() throws a null reference or returns an empty
placeholder, because the mapping layer never populated the association.

The context in which Lazy Load becomes necessary, rather than merely
convenient, has three properties. First, the domain object model is built
independently of any particular use case, so the object cannot know in advance
which of its associations the caller will traverse, per Fowler's framing of
the Domain Model pattern in the same book (Martin Fowler, *Patterns of
Enterprise Application Architecture*, Addison-Wesley, 2002, chapter 9, page
116). Second, the underlying store is remote relative to memory access, a
network round trip or a disk seek, so the cost of an unnecessary fetch is not
negligible the way an unnecessary field read in memory is. Third, the object
model exposes plain accessors, getOrders, getSupplier, rather than an explicit
loadOrders call, so the calling code has no syntactic signal that a particular
accessor is expensive and the mapping layer must intercept the ordinary
accessor to insert the deferred fetch.

Outside this triangle, deferred initialization is still a useful technique,
but it is not the Lazy Load pattern described here. A field computed once and
cached inside a single process, with no remote store behind it, is a simpler
idiom sometimes also called lazy initialization in general programming
language literature (Joshua Bloch, *Effective Java*, 3rd edition,
Addison-Wesley, 2018, Item 83, "Use lazy initialization judiciously", pages
319 to 323, which treats the technique purely as a local optimization with no
mention of a proxy, a database, or an object-relational mapper).

## 3. Forces

- **Query cost against traversal completeness.** Every association eagerly
  fetched grows the query. Every association deferred risks a second round
  trip the caller did not anticipate. The pattern exists because no single
  fetch depth is correct for every caller of the same class.
- **Transparency against control.** A Ghost or a bytecode-instrumented field
  check lets calling code write ordinary property access and never think
  about loading. A Value Holder makes the deferred nature visible in the
  type signature, at the cost of every caller writing getValue instead of a
  plain accessor. Fowler notes this trade directly, the more transparent
  mechanisms cost more in implementation complexity (Martin Fowler, *Patterns
  of Enterprise Application Architecture*, Addison-Wesley, 2002, page 202).
- **Session lifetime against object lifetime.** The load, when it fires, needs
  a live connection or a live unit of work to run the query against. If the
  object outlives that session, the deferred load has nothing to load from,
  which is the source of the pattern's most common production failure, see
  dimension 11.
- **Predictability of latency.** A caller that reads ten fields on ten objects
  in a tight loop, each triggering its own query, pays ten round trips where
  a single eager join would have paid one. The pattern trades an easy mental
  model, plain field access, for latency that is invisible in the source code
  and only visible in a query log.
- **Memory footprint against I/O count.** Loading eagerly favours fewer, larger
  round trips at the cost of holding data nobody reads. Loading lazily favours
  many small round trips, each exactly matched to what is read. Which side
  wins depends on the ratio of association traversal to construction, a ratio
  that differs by use case and cannot be fixed once for the whole object.

## 4. Applicability and non-applicability

Reach for Lazy Load when the object graph reachable from a root entity is
large relative to what a typical caller reads, when different callers of the
same class read different subsets of its associations, when the underlying
store access is expensive enough that avoiding an unnecessary fetch matters
more than the bookkeeping the pattern adds, and when the calling code can be
trusted to run inside a live session or connection scope for as long as the
lazily loaded object is in use.

Do not reach for it in these situations.

- **The association is read on every code path that constructs the object.**
  If every caller of Order immediately reads its OrderLines, deferring the
  load only adds a round trip that always fires, with no case where it is
  ever skipped. Eager loading, or a dedicated query that joins the association
  up front, is both simpler and faster.
- **The object crosses a process or session boundary before it is read.** A
  Lazy Load field depends on a live connection or unit of work to satisfy its
  deferred fetch. Serializing the object to a queue message, a cache entry, or
  an HTTP response and reading it later, after the originating session has
  closed, produces the LazyInitializationException class of failure described
  in dimension 11. Data Transfer Objects that are fully populated before they
  leave the session boundary exist for exactly this reason (Martin Fowler,
  *Patterns of Enterprise Application Architecture*, Addison-Wesley, 2002,
  chapter 15, Data Transfer Object, page 401).
- **The object is small enough that the whole graph fits comfortably in one
  query.** A Customer with three or four scalar fields and no collection
  association gains nothing from Lazy Load and only gains the bookkeeping cost.
- **The code needs predictable, bounded latency**, for example a request
  handler with a strict timeout budget where an unbounded chain of deferred
  fetches, each firing inside a serialization loop, could turn one request
  into dozens of sequential queries. This is the N plus 1 failure mode, and
  the fix in that context is almost always to remove the laziness for that
  specific access path, not to keep it and hope the caller remembers to
  prefetch.
- **The domain has no persistence layer to defer to.** In a pure in-memory
  object model with no database, no remote service, and no file behind an
  association, there is nothing expensive to postpone, and Lazy Load adds
  complexity to solve a cost that does not exist.

## 5. Structure

- **Client.** Code outside the persistence layer that calls an ordinary
  accessor on a domain object and expects the return value to be fully
  usable, with no awareness of whether the underlying data has been loaded
  yet.
- **Real Subject.** The domain object, or the data the domain object needs,
  in its fully populated form. In the Ghost variant this role and the
  Subject role below are the same object at different points in its
  lifecycle. In the Virtual Proxy and Value Holder variants they are
  separate objects.
- **Subject.** The object the client actually holds a reference to. In Lazy
  Initialization and Ghost, the Subject is the Real Subject itself, carrying
  either a marker value or an unpopulated state. In Virtual Proxy, the
  Subject is a stand-in that exposes the same interface as the Real Subject.
  In Value Holder, the Subject is a wrapper with its own, narrower interface.
- **Data Source.** The mapper, repository, or query object that knows how to
  fetch the missing data. The Subject holds, directly or indirectly, enough
  identifying information, usually a primary key, to ask the Data Source
  for the Real Subject's data on demand.
- **Loading trigger.** The specific accessor call, field read, or method
  invocation that the Subject intercepts in order to check whether loading is
  needed and to perform it if so. This is the one piece of machinery every
  variant must have, and the four variants differ mainly in where this trigger
  lives and how visible it is to the Client.

## 6. ASCII structure diagram

```
  Lazy Initialization                    Virtual Proxy

  +----------------+                     +----------------+
  |     Client      |                     |     Client      |
  +--------+--------+                     +--------+--------+
           | getSupplier()                         | getSupplier()
           v                                        v
  +----------------+                     +----------------+
  |    Product      |                     |    Product      |
  |  supplier: null |------ marker ----->  |  supplier ------+
  | until first read|                     +----------------+ |
  +----------------+                                          |
           | on first call, checks marker,                    v
           | queries Data Source, caches result       +------------------+
           v                                          | SupplierProxy    |
  +----------------+                                  | id: 42           |
  |   Data Source   |                                  | real: null       |
  +----------------+                                  +--------+---------+
                                                                 | first call
                                                                 v
                                                        +------------------+
                                                        |   Data Source     |
                                                        +------------------+
                                                                 |
                                                                 v
                                                        +------------------+
                                                        |  real Supplier    |
                                                        +------------------+


  Value Holder                            Ghost

  +----------------+                     +----------------+
  |     Client      |                     |     Client      |
  +--------+--------+                     +--------+--------+
           | supplierHolder.getValue()             | getSupplierName()
           v                                        v
  +----------------+                     +----------------+
  |ValueHolder<Sup> |                     |    Supplier     |
  |  loaded: false  |                     | state: GHOST     |
  |  target: null   |                     | id: 42, name: -- |
  +--------+--------+                     +--------+---------+
           | on getValue, checks loaded,           | on any accessor other
           | queries Data Source                   | than id, checks state,
           v                                        | queries Data Source,
  +----------------+                                | fills every field
  |   Data Source   |                                v
  +----------------+                     +----------------+
                                          |   Data Source   |
                                          +----------------+
```

## 7. Dynamics

The four variants share one dynamic skeleton and differ in where the check
sits. The skeleton, using Virtual Proxy as the concrete example because it
makes the intercepted call explicit.

```
Client                Product              SupplierProxy         Data Source
  |                       |                       |                    |
  |  new Product(id=7)    |                       |                    |
  |---------------------->|                       |                    |
  |                       | new SupplierProxy(42)  |                    |
  |                       |----------------------->|                    |
  |  product.getSupplier()|                       |                    |
  |---------------------->|                       |                    |
  |                       | return proxy reference |                    |
  |                       |<-----------------------|                    |
  |  supplierRef          |                       |                    |
  |<-----------------------                       |                    |
  |  supplierRef.getName()                        |                    |
  |----------------------------------------------->|                    |
  |                       |                       | real == null ?     |
  |                       |                       | yes, so query      |
  |                       |                       |------------------->|
  |                       |                       |  SELECT * FROM     |
  |                       |                       |  supplier WHERE    |
  |                       |                       |  id = 42           |
  |                       |                       |<--------------------
  |                       |                       | real = Supplier(..)|
  |                       |                       | cache real         |
  |  supplierRef.getName()                        |                    |
  |<-------------------------------------------- delegate to real ----|
  |  supplierRef.getAddress()                      |                    |
  |----------------------------------------------->|                    |
  |                       |                       | real != null,       |
  |                       |                       | delegate directly,  |
  |                       |                       | no second query     |
  |<-------------------------------------------- delegate to real ----|
```

The load fires exactly once, on the first accessor call after construction,
and every subsequent accessor call on the same reference reuses the cached
real object. This one shot guarantee is what makes Lazy Load compose safely
with an Identity Map, since the second access to the same association never
issues a second query, per Fowler's own cross reference between the two
patterns (Martin Fowler, *Patterns of Enterprise Application Architecture*,
Addison-Wesley, 2002, chapter 18, page 202, and chapter 18, Identity Map,
page 195).

## 8. Implementation variants

**Lazy Initialization with a null marker.** The simplest variant, and the one
most vulnerable to a specific bug, the marker value is indistinguishable from
a legitimately absent association. If Product.supplier can genuinely be
null for a product with no supplier on record, a null check alone cannot tell
apart not yet loaded from loaded and empty, and the field will be re-queried
on every access. The fix is a second boolean field, loaded, checked before
the value field, which is exactly the shape the Value Holder variant makes
explicit as a separate type instead of a pair of fields on the domain object.

**Virtual Proxy with an interface stand-in.** The client-facing type is an
interface or an abstract base that both the proxy and the real object
implement, so the client's variable declaration never changes when the proxy
resolves. Two sub-variants exist for how the proxy hands off after loading,
delegation, where the proxy keeps forwarding every call to the now-loaded
real object forever, and swap, where the proxy replaces itself in the
parent's field once loaded so subsequent access skips the proxy entirely.
Fowler favours delegation for simplicity, at the cost of one extra pointer
indirection for the lifetime of the object (Martin Fowler, *Patterns of
Enterprise Application Architecture*, Addison-Wesley, 2002, page 203).

**Value Holder with a generic wrapper.** Because the wrapper's interface,
commonly a single getValue method, does not match the wrapped type's own
interface, every field of this shape in a codebase is immediately visible in
the type signature, ValueHolder or Lazy, which several statically typed
languages standardize as a first class library type rather than leaving each
project to invent its own, for example the Lazy generic type documented for
the .NET base class library, initialized either with a factory delegate or
left to call a parameterless constructor on first access (Microsoft,
".NET, System.Lazy Class", https://learn.microsoft.com/en-us/dotnet/api/system.lazy-1,
verified 2026-08-02).

**Ghost with a partial object.** The domain object itself carries a state
field, commonly an enum with values such as HOLLOW, LOADING, and LOADED. The
constructor that produces a Ghost sets only the identifier and marks the
state HOLLOW. Every accessor other than the identifier accessor checks the
state before returning and triggers a load on HOLLOW, transitioning through
LOADING to LOADED. This is the variant most object-relational mapping tools
choose for entities, because it lets the same class serve as both the query
result placeholder and the fully populated domain object, with no second
class to maintain, which is precisely how Hibernate's own proxy and bytecode
enhancement mechanisms are described, generating either a subclass proxy or
enhancing the entity class's bytecode directly to intercept field access
(Hibernate ORM team, "Hibernate ORM User Guide, Fetching", https://docs.hibernate.org/orm/6.4/userguide/html_single/Hibernate_User_Guide.html,
verified 2026-08-02, describing bytecode enhancement based lazy loading of
both associations and individual basic attribute values).

**Bytecode instrumentation as a fifth mechanism.** Fowler's four variants
predate widespread bytecode manipulation tooling and describe hand written
proxies and wrappers. Modern object-relational mapping frameworks frequently
generate the Virtual Proxy or Ghost machinery at build time or class load
time instead of asking the developer to write it, so the domain class in
source code looks like a plain object with no lazy loading code visible at
all, while the runtime class is a generated subclass or an instrumented
version of the same class. This shifts the implementation cost from the
application developer to the framework, without changing which of Fowler's
four patterns is actually running underneath.

## 9. Known production uses

- **Hibernate ORM**, the Java object-relational mapper, defaults collection
  associations, annotated `@OneToMany` and `@ManyToMany`, to lazy fetching,
  and implements the load either through a dynamically generated proxy
  subclass or, for basic attribute and to-one association lazy loading,
  through Byte Buddy based bytecode enhancement applied at build time
  (Hibernate ORM team, "Hibernate ORM User Guide, chapter on Fetching",
  https://docs.hibernate.org/orm/6.4/userguide/html_single/Hibernate_User_Guide.html,
  verified 2026-08-02). This is a direct implementation of the Ghost and
  Virtual Proxy variants, generated rather than hand written.
- **Ruby on Rails Active Record**, whose own querying guide states plainly
  that Active Record uses lazy loading for associations by default, and
  documents the resulting cost, retrieving ten books and then reading each
  book's author executes one query for the books plus one query per book for
  the author, eleven queries in total, with `includes`, `preload`, and
  `eager_load` offered as the deliberate opt out (Ruby on Rails team,
  "Active Record Query Interface", https://guides.rubyonrails.org/active_record_querying.html,
  verified 2026-08-02). This is Lazy Initialization at the association level,
  implemented on top of Fowler's own Active Record pattern from the same
  book, a naming collision between two entirely different Fowler patterns
  sharing the term Active Record that is worth flagging explicitly so a
  reader does not conflate them.
- **Doctrine ORM**, the PHP object-relational mapper, generates proxy classes
  for entities so that a reference obtained through `getReference` or through
  a to-one association returns a proxy carrying only the identifier, with the
  remaining fields populated on first access, which the project's own
  reference documentation on advanced configuration describes under lazy
  object generation (Doctrine Project, "Doctrine ORM, Advanced Configuration",
  https://www.doctrine-project.org/projects/doctrine-orm/en/current/reference/advanced-configuration.html,
  verified 2026-08-02). This is a direct, named Virtual Proxy implementation.
- **Entity Framework Core**, the .NET object-relational mapper, offers lazy
  loading as an explicit, opt in feature built on runtime generated proxies,
  requiring the `Microsoft.EntityFrameworkCore.Proxies` package and a call to
  `UseLazyLoadingProxies`, after which any `virtual` navigation property on an
  inheritable entity class is lazily loaded, with the documentation's own
  warning that this "can cause unneeded extra database roundtrips" and
  pointing readers at the N plus 1 discussion in its performance guidance
  (Microsoft, "Lazy Loading of Related Data, EF Core",
  https://learn.microsoft.com/en-us/ef/core/querying/related-data/lazy,
  verified 2026-08-02). EF Core also documents a proxy free implementation of
  the same idea through an injected `ILazyLoader` service, which is Fowler's
  Value Holder pattern applied per navigation property rather than to the
  whole entity.

## 10. Consequences

Positive consequences.

- A single object model serves every caller regardless of how much of its
  graph a given caller needs, without the model author having to predict
  every access pattern up front.
- Object construction from a root query stays cheap, proportional to the row
  or rows fetched by that query rather than to the full transitive closure of
  every association reachable from it.
- The mapping layer, not the calling code, owns the decision of when a
  fetch happens, which keeps loading policy centralized and changeable in
  one place, usually through fetch strategy configuration, rather than
  scattered across every call site that happens to touch an association.

Negative consequences.

- The pattern hides an expensive operation, a network round trip or a disk
  read, behind syntax that looks exactly like a cheap field read, which is
  precisely the property that produces the N plus 1 failure mode described
  in dimension 11, and which several practitioners have criticized as an
  attractive nuisance for exactly this reason.
- Every Lazy Load field depends on a live session, connection, or unit of
  work being available at the moment the deferred fetch fires, which ties
  the lifetime of the domain object to infrastructure state that has nothing
  to do with the object's own meaning, and which breaks the moment the
  object is serialized, cached, or handed to a background thread that
  outlives the originating request.
- Testing an object with Lazy Load fields requires either a live data source
  double behind every association or careful attention to which accessors a
  given test actually exercises, since a test that never triggers the load
  will pass even if the load mechanism is broken, and a test double that
  eagerly populates everything defeats the purpose of testing the deferred
  behaviour at all.
- Debugging is harder because a stack trace pointing at a getter no longer
  tells the reader whether that getter is a cheap field read or a query,
  and the two look identical in source.

## 11. Failure modes and misuse

- **LazyInitializationException, or its equivalent under any name.**
  Symptom, an exception thrown from deep inside a serializer or a view
  template, complaining that a session or connection is closed, when the
  code that constructed the object ran successfully and returned long
  before. Cause, the object crossed a session boundary, most commonly by
  being returned from a request handler after the transaction committed and
  then read again during JSON serialization or template rendering, and one
  of its Lazy Load fields is accessed for the first time after the
  originating unit of work has already ended. Fix, populate every field the
  downstream layer will read before the session closes, either by explicit
  eager fetch on the original query or by mapping to a fully populated Data
  Transfer Object inside the still open session, never by widening the
  session's lifetime to match the serializer's, which reintroduces
  connection pool exhaustion under load.
- **N plus 1 queries.** Symptom, a request that should cost one or two
  queries instead issues one query per row of a collection, visible as a
  sawtooth pattern of near identical queries in a query log or an
  application performance monitoring trace, and as latency that grows
  linearly with result set size on an endpoint that looks, from the source
  code, like a single fixed cost operation. Cause, a loop over a lazily
  loaded collection where each iteration touches a lazily loaded association
  on the current element, so what reads as one fetch is actually one plus
  one per element. Fix, replace the implicit lazy traversal with an explicit
  eager fetch, a join fetch, or a batch fetch sized to the loop, chosen at
  the specific call site rather than by changing the association's default
  fetch type globally, since a global change to eager can reintroduce the
  opposite problem on every other call site that never needed the
  association at all.
- **Silent re-query from a broken loaded flag.** Symptom, the same
  association is queried more than once for the same object within a single
  unit of work, visible as duplicate identical queries in a log that should
  by construction only ever run once per object per session. Cause, a Lazy
  Initialization implementation that used a null check instead of a
  dedicated loaded boolean, so a legitimately absent value, an order with no
  discount code, is indistinguishable from an unloaded value and is
  re-queried on every access. Fix, use an explicit sentinel state rather than
  overloading the domain's own null, which is exactly the distinction
  between Lazy Initialization done carelessly and the Ghost or Value Holder
  variants, both of which carry a dedicated state field for this reason.
- **Proxy identity confusion.** Symptom, an equality check or a type check
  that should succeed fails, `instanceof Supplier` returns false for an
  object that is, semantically, a Supplier, or `object.getClass() ==
  Supplier.class` fails when the object came back as a proxy subclass. Cause,
  the proxy generation mechanism produced a runtime subclass or an
  instrumented type rather than the exact declared class, and code
  elsewhere in the system compares classes by reference equality instead of
  by the interface or by a framework provided unproxy helper. Fix, compare
  by the domain interface or by identity, the primary key, never by exact
  runtime class, and where a framework offers an explicit unproxy or
  initialize helper, call it before doing reflective type inspection.
- **Detached collection mutation exceptions.** Symptom, adding or removing an
  element from a lazily loaded collection throws, even though the collection
  looked like an ordinary list from the outside. Cause, some frameworks
  return a specialized, framework owned collection type in place of the
  lazily loaded association, and that type enforces its own invariants,
  including refusing mutation once its owning session has closed. Fix, treat
  the returned collection as read only outside the originating session, and
  perform mutation through the framework's own association management
  methods, called while the session is still open, rather than treating the
  return value as a plain, freely mutable list.

## 12. Trade-off matrix

| Force | Lazy Initialization | Virtual Proxy | Value Holder | Ghost | Eager Load, no laziness |
|---|---|---|---|---|---|
| Transparency to caller | High, plain field access | High, same interface as real object | Low, caller must call getValue | High, plain field access | Highest, nothing is deferred |
| Extra type needed | None, extra field on same object | One proxy type per association type | One generic wrapper type, reusable | None, one state field on same object | None |
| Distinguishes absent from unloaded | Only with a second flag | Yes, proxy presence itself is the signal | Yes, wrapper's loaded flag | Yes, explicit state field | Not applicable, always populated |
| Cost when the association is never read | Lowest, one marker check | Low, one allocation plus one check | Low, one allocation plus one check | Lowest, one state check | Highest, the fetch always runs |
| Cost when the association is always read | One extra round trip versus eager | One extra round trip plus one extra allocation versus eager | One extra round trip plus one extra allocation versus eager | One extra round trip versus eager | None, cost is paid once, up front |
| Session lifetime coupling | Tight | Tight | Tight | Tight | None, fully resolved at construction |
| Typical mechanism in modern frameworks | Hand written or generated field check | Generated proxy subclass | Framework provided generic type, for example .NET's Lazy | Generated bytecode enhancement | Explicit join or batch fetch at the query |

## 13. Related and incompatible patterns

- **Identity Map.** Lazy Load and Identity Map are almost always deployed
  together in object-relational mapping tools, because the Identity Map is
  what guarantees that the second reference to an already loaded object
  returns the same instance rather than issuing a second query and
  constructing a duplicate, which is what makes the one shot loading
  guarantee in dimension 7 hold across an entire unit of work rather than
  only within a single object.
- **Unit of Work.** The session or transaction boundary a Unit of Work
  manages is the same boundary that every Lazy Load field's deferred fetch
  depends on, per dimension 11's LazyInitializationException failure mode,
  which means the two patterns share a lifetime contract that the calling
  code must respect even when it never interacts with either pattern's
  machinery directly.
- **Data Mapper and Active Record.** Both persistence patterns can host Lazy
  Load fields, since the pattern concerns how an individual association is
  populated, not how the owning object maps its own table, and Fowler
  presents Lazy Load as orthogonal to that choice, applicable under either
  persistence strategy.
- **Data Transfer Object.** DTOs are the standard way to escape the session
  boundary problem, a DTO is populated eagerly, inside the still open
  session, from the fully or partially loaded domain object, and then
  crosses the boundary as a plain, fully resolved value with no lazy fields
  of its own, which is why a DTO assembler is frequently the single place in
  a codebase responsible for deciding which lazily loaded associations to
  force before the session closes.
- **Proxy, from the Gang of Four catalog.** Virtual Proxy, one of Fowler's
  four Lazy Load variants, is the same structural shape as the GoF Proxy
  pattern's Virtual Proxy variant, applied specifically to the
  object-relational context. The relationship is specialization, not
  conflict, Fowler's entry names a general purpose structural pattern and
  narrows it to one particular trigger, an expensive remote data fetch.
- **Incompatible with nothing at the structural level**, but functionally at odds with
  any design goal that requires predictable, bounded latency per accessor
  call, since the entire point of the pattern is to make some accessor calls
  cost more than others, invisibly.

## 14. Refactoring path in and out

Introducing Lazy Load into code that currently loads everything eagerly.

1. Identify a specific association that is read by only a subset of the
   callers of its owning class, using a query log or a profiler rather than
   guessing, since intuition about which associations are read where is
   frequently wrong in a codebase of any size.
2. Confirm every caller of the owning class either already runs inside a
   session or unit of work for the object's full useful lifetime, or is
   changed to do so, or is changed to receive a fully populated DTO instead
   of the domain object directly. Skipping this step is what produces the
   LazyInitializationException failure mode the very first time the code
   ships.
3. Choose the variant that matches the codebase's existing idioms, a Ghost
   if the class already goes through a framework capable of bytecode
   enhancement or proxy generation, a Value Holder if the language or
   framework already offers a generic lazy wrapper type, a hand rolled
   Virtual Proxy or Lazy Initialization only where no framework support
   exists.
4. Change the association's fetch configuration, or introduce the wrapper
   type, for that one association only, leaving every other association at
   its current fetch behaviour.
5. Re-run the query log or profiler against the same representative
   workload used in step 1 and confirm the round trip count actually
   dropped for the callers that never read the association, and did not
   silently regress into an N plus 1 pattern for the callers that iterate
   over collections of the owning class.
6. Repeat for the next association only after the first is verified in
   production or in a production-representative load test, never batch
   multiple associations into a single change, since the failure modes in
   dimension 11 compound and become harder to isolate when several
   associations change fetch behaviour at once.

Removing Lazy Load once it stops earning its place.

1. Confirm, again from a query log rather than from memory, that the
   association in question is now read by nearly every caller of the owning
   class, which is the condition under which the deferred fetch always
   fires and therefore only adds latency with no corresponding saving.
2. Change the association's fetch configuration back to eager, or delete
   the wrapper type and inline the eager fetch into the owning class's
   construction or mapping step.
3. Delete the now unused proxy or wrapper type if nothing else in the
   codebase references it, following the project's own dead code removal
   discipline rather than leaving an unused Virtual Proxy class as a trap
   for the next reader.
4. Re-run the same representative workload from before and confirm the
   change reduced total round trips rather than merely moving cost from many
   small queries into one large one that is, empirically, slower for this
   particular access pattern, since eager is not always faster,
   only more predictable.

## 15. Testing and verification

Testing code that owns Lazy Load fields is easier on the write path and
harder on the read path than testing an eagerly loaded equivalent.

The write path is easier because constructing a test fixture for the owning
object does not require populating every association, only the fields the
specific test actually exercises, which keeps fixture setup code shorter and
less coupled to the full shape of the domain model.

The read path is harder for two distinct reasons. First, a test that never
calls the accessor behind a Lazy Load field will pass even if the underlying
load mechanism is completely broken, which means test coverage of the
domain object's public interface does not, by itself, prove the loading
machinery works, and a dedicated test that explicitly calls the lazy
accessor and asserts on the result is required in addition to whatever tests
exercise the object's other behaviour. Second, a test double for the Data
Source, a fake repository or a mocked mapper, must decide whether to
eagerly populate everything it returns, which silently defeats the purpose
of testing lazy behaviour at all, or to genuinely defer, which requires the
test double to implement the same state machine as the real Data Source,
Ghost or proxy included.

The technique that resolves both problems is a small, purpose built in
memory Data Source test double that genuinely tracks whether each
association has been loaded, exposes a query count the test can assert
against, and fails loudly if an association is queried more than once for
the same object within a single simulated unit of work, which turns the
silent re-query failure mode from dimension 11 into a test assertion instead
of a production incident. A second, separate test category exercises the
session boundary failure directly, constructing the owning object, closing
or disposing the simulated session, and asserting that the specific,
expected exception or error is what happens on the next accessor call,
rather than a null reference or a hang, which is the class of bug most
likely to reach production because it only manifests under a code path,
serialization after the transaction commits, that many test suites never
exercise.

## 16. Observability signals

- **Query count per unit of work, and its distribution across requests of
  the same logical shape.** A healthy instance shows a tight distribution,
  most requests that construct the same kind of object graph issue nearly
  the same number of queries. A widening distribution, or a query count that
  grows linearly with the size of a returned collection, is the N plus 1
  failure mode surfacing as a metric rather than as a symptom a person
  happened to notice.
- **Time to first byte against total query time on the same request.** A
  request whose total query time is made up mostly of many small, sequential
  queries rather than by one or two larger ones is a strong signal that Lazy
  Load fields are firing serially inside a loop, and the fix belongs at the
  specific call site identified by tracing which queries those are.
- **Rate of session or connection boundary exceptions, tagged by the
  originating association.** Tracking LazyInitializationException, or the
  equivalent for the stack in use, as a first class error metric, broken out
  by which association triggered it, turns a class of bug that otherwise
  shows up as an unexplained spike in 500 responses into a clear signal
  pointing at exactly which DTO assembler or serializer is missing an
  eager fetch.
- **Proxy or Ghost cache hit rate within a single unit of work.** Where the
  underlying framework exposes it, the ratio of accessor calls that hit an
  already loaded association against the total accessor calls for that
  association type is a direct measure of whether the Identity Map and Lazy
  Load are working together as intended, a low hit rate on an association
  that should only ever load once per object per session points at a broken
  loaded flag, the silent re-query failure mode.
- **Connection pool saturation correlated with request duration.** Because
  every Lazy Load field's deferred fetch needs a live connection, a workload
  with heavy lazy traversal inside long lived requests is a common,
  underappreciated driver of connection pool exhaustion, and correlating
  pool saturation events against endpoints known to traverse deep object
  graphs is a faster diagnostic path than starting from the pool metric
  alone.

## 17. Security and privacy implications

Lazy Load itself introduces no new attack surface, it does not parse
untrusted input, and it does not change what data an authorized caller can
eventually reach, only when the fetch for that data happens. The implications
that do matter are indirect, arising from how the pattern interacts with
authorization and with data minimization.

An authorization check written against the eagerly loaded shape of an object
graph can be silently bypassed if a later refactor introduces Lazy Load on
the association the check depends on and the check is evaluated before that
association has been accessed, since a check that reads a not yet loaded
field may see a default or empty value rather than the real one, depending on
which of the four variants is in use and how it initializes its placeholder
state. Any authorization logic that reads a Lazy Load field must therefore
either force the load explicitly before evaluating the check, or the field's
default, unloaded state must be a value that fails closed rather than one
that fails open, for example an empty permissions collection that denies
by default rather than one that is indistinguishable from a genuinely empty,
intentionally granted set of permissions.

The pattern has a data minimization implication in the opposite direction as
well, stated plainly, deferred loading means a request that only
needed a subset of an object's data genuinely never fetches, logs, or holds
in memory the data it did not need, which is a small but real benefit for
any system handling regulated personal data under a data minimization
requirement, since data that was never loaded cannot appear in an
accidental log line, a stack trace, or a memory dump taken during that
request. This benefit only holds if the eager fallback path, DTO assembly
or explicit joins added to fix an N plus 1 problem, is scoped narrowly to
the specific fields the fix actually needs, rather than defaulting to
loading the entire graph as the easiest way to make a query count metric
look better, which would quietly erase the minimization benefit the pattern
was providing.

## 18. References

1. Martin Fowler, with David Rice and Matthew Foemmel, *Patterns of
   Enterprise Application Architecture*, Addison-Wesley, 2002, chapter 18,
   Object-Relational Behavioral Patterns, Lazy Load, page 200 (chapter
   opening, book pagination), Identity Map, page 195.
2. Martin Fowler, "Lazy Load", https://martinfowler.com/eaaCatalog/lazyLoad.html,
   verified 2026-08-02.
3. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides, *Design
   Patterns. Elements of Reusable Object-Oriented Software*, Addison-Wesley,
   1994, chapter 4, Structural Patterns, Proxy, page 208.
4. Joshua Bloch, *Effective Java*, 3rd edition, Addison-Wesley, 2018, Item
   83, "Use lazy initialization judiciously", pages 319 to 323.
5. Hibernate ORM team, "Hibernate ORM User Guide, Fetching",
   https://docs.hibernate.org/orm/6.4/userguide/html_single/Hibernate_User_Guide.html,
   verified 2026-08-02.
6. Ruby on Rails team, "Active Record Query Interface, Eager Loading
   Associations", https://guides.rubyonrails.org/active_record_querying.html,
   verified 2026-08-02.
7. Doctrine Project, "Doctrine ORM, Advanced Configuration",
   https://www.doctrine-project.org/projects/doctrine-orm/en/current/reference/advanced-configuration.html,
   verified 2026-08-02.
8. Microsoft, "Lazy Loading of Related Data, EF Core",
   https://learn.microsoft.com/en-us/ef/core/querying/related-data/lazy,
   verified 2026-08-02.
9. Microsoft, ".NET, System.Lazy Class",
   https://learn.microsoft.com/en-us/dotnet/api/system.lazy-1,
   verified 2026-08-02.

## Code examples

Java, a self contained Ghost variant, using a state field on the entity
itself rather than a separate proxy type, with an in memory Data Source
stand in so the example compiles and runs without an external database.

```java
import java.util.HashMap;
import java.util.Map;

class SupplierDataSource {
    private final Map<Integer, String> names = new HashMap<>();
    private int queryCount = 0;

    SupplierDataSource() {
        names.put(42, "Acme Fasteners");
    }

    String fetchName(int id) {
        queryCount++;
        String name = names.get(id);
        if (name == null) {
            throw new IllegalStateException("no supplier " + id);
        }
        return name;
    }

    int getQueryCount() {
        return queryCount;
    }
}

enum LoadState { HOLLOW, LOADED }

class Supplier {
    private final int id;
    private LoadState state;
    private String name;
    private final SupplierDataSource dataSource;

    Supplier(int id, SupplierDataSource dataSource) {
        this.id = id;
        this.dataSource = dataSource;
        this.state = LoadState.HOLLOW;
    }

    int getId() {
        return id;
    }

    String getName() {
        if (state == LoadState.HOLLOW) {
            name = dataSource.fetchName(id);
            state = LoadState.LOADED;
        }
        return name;
    }
}

public class LazyLoadDemo {
    public static void main(String[] args) {
        SupplierDataSource source = new SupplierDataSource();
        Supplier supplier = new Supplier(42, source);

        System.out.println("query count before access: " + source.getQueryCount());
        System.out.println("name: " + supplier.getName());
        System.out.println("name again: " + supplier.getName());
        System.out.println("query count after two reads: " + source.getQueryCount());

        if (source.getQueryCount() != 1) {
            throw new AssertionError("expected exactly one query, the second read must be cached");
        }
        System.out.println("PASS, one query served two reads");
    }
}
```

Python, a Value Holder variant, a small generic wrapper type distinct from
the domain object's own interface, matching Fowler's description of a
wrapper the caller must call through rather than mistake for the real
object.

```python
from typing import Callable, Generic, Optional, TypeVar

T = TypeVar("T")


class ValueHolder(Generic[T]):
    def __init__(self, loader: Callable[[], T]) -> None:
        self._loader = loader
        self._value: Optional[T] = None
        self._loaded = False

    def get_value(self) -> T:
        if not self._loaded:
            self._value = self._loader()
            self._loaded = True
        return self._value

    def is_loaded(self) -> bool:
        return self._loaded


class SupplierDataSource:
    def __init__(self) -> None:
        self._names = {42: "Acme Fasteners"}
        self.query_count = 0

    def fetch_name(self, supplier_id: int) -> str:
        self.query_count += 1
        return self._names[supplier_id]


class Product:
    def __init__(self, name: str, supplier_id: int, data_source: SupplierDataSource) -> None:
        self.name = name
        self.supplier_name = ValueHolder(lambda: data_source.fetch_name(supplier_id))


def main() -> None:
    source = SupplierDataSource()
    product = Product("Steel Bracket", 42, source)

    assert source.query_count == 0, "constructing the product must not query the supplier"
    assert product.supplier_name.get_value() == "Acme Fasteners"
    assert product.supplier_name.get_value() == "Acme Fasteners"
    assert source.query_count == 1, "the second read must be served from the cached value"

    print("PASS, product built with zero queries, one query on first read, cached on the second")


if __name__ == "__main__":
    main()
```

TypeScript, a Virtual Proxy variant, an interface shared by the proxy and the
real object so the caller's declared type never changes, with a Promise
based Data Source to match how a lazily loaded association behaves in a
JavaScript runtime with no synchronous database call available.

```typescript
interface Supplier {
  getName(): Promise<string>;
}

class RealSupplier implements Supplier {
  constructor(private readonly name: string) {}
  async getName(): Promise<string> {
    return this.name;
  }
}

class SupplierDataSource {
  private readonly names = new Map<number, string>([[42, "Acme Fasteners"]]);
  queryCount: number = 0;

  async fetchName(id: number): Promise<string> {
    this.queryCount += 1;
    const name = this.names.get(id);
    if (name === undefined) {
      throw new Error(`no supplier ${id}`);
    }
    return name;
  }
}

class SupplierProxy implements Supplier {
  private real: RealSupplier | null = null;

  constructor(private readonly id: number, private readonly dataSource: SupplierDataSource) {}

  async getName(): Promise<string> {
    if (this.real === null) {
      const name = await this.dataSource.fetchName(this.id);
      this.real = new RealSupplier(name);
    }
    return this.real.getName();
  }
}

async function main(): Promise<void> {
  const source = new SupplierDataSource();
  const supplier: Supplier = new SupplierProxy(42, source);

  const queriesBeforeAccess: number = source.queryCount;
  if (queriesBeforeAccess !== 0) {
    throw new Error("constructing the proxy must not query the supplier");
  }

  const first = await supplier.getName();
  const second = await supplier.getName();

  if (first !== "Acme Fasteners" || second !== "Acme Fasteners") {
    throw new Error("unexpected supplier name");
  }
  const queriesAfterAccess: number = source.queryCount;
  if (queriesAfterAccess !== 1) {
    throw new Error("expected exactly one query, the second read must delegate to the cached real object");
  }

  console.log("PASS, proxy served two reads with one underlying query");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
```
