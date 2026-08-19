---
name: Aggregate
slug: aggregate
family: 11-domain-driven-design
category: Domain-Driven Design
aliases: [Consistency Boundary, Transaction Boundary, Cluster of Entities]
first_described: "Evans 2003"
maturity: canonical
related: [aggregate-root, entity, value-object, repository, domain-event, factory, bounded-context]
incompatible_with: []
verified: 2026-08-02
---

# Aggregate

## 1. Name, aliases, and lineage

The canonical name is Aggregate. Eric Evans introduced it in *Domain-Driven
Design. Tackling Complexity in the Heart of Software*, Addison-Wesley, 2003,
Chapter 6, "The Life Cycle of a Domain Object", in the section titled
Aggregates. Evans defines it as "a cluster of associated objects that we treat
as a unit for the purpose of data changes", and pairs the definition with a
rule of access. "Choose one Entity to be the root of each Aggregate, and
control all access to the objects inside the boundary through the root."

Martin Fowler's bliki page restates the same shape in a form that is now the
most frequently linked secondary source for the term. "A DDD aggregate is a
cluster of domain objects that can be treated as a single unit", where "any
references from outside the aggregate should only go to the aggregate root"
(Martin Fowler, "DDD_Aggregate," verified 2026-08-02,
https://martinfowler.com/bliki/DDD_Aggregate.html).

Aggregate is easy to confuse with Aggregate Root because catalogs often blur
the two, and this repository keeps them as separate entries deliberately, see
`aggregate-root.md`. Aggregate names the whole, the cluster of Entities and
Value Objects that must change together as one unit, bounded by a single
transaction. Aggregate Root names the one object inside that cluster that
outside code is permitted to reference and through which every mutation must
pass. A cluster with no root is not an aggregate, it is an unenforced grouping.
A root with no notion of what it bounds is a lone object with an inflated
title. Microsoft's Azure Architecture Center makes the same distinction the
same way in its tactical DDD guide. "An aggregate defines a consistency
boundary around one or more entities. Exactly one entity in an aggregate is
the root", and it adds a clarification catalogs frequently omit, "an aggregate
can consist of a single entity without child entities. What makes it an
aggregate is the transactional boundary" (Microsoft Learn, "Use Tactical DDD
to Design Microservices," verified 2026-08-02,
https://learn.microsoft.com/en-us/azure/architecture/microservices/model/tactical-domain-driven-design).
That last sentence is worth sitting with. Aggregate is not defined by having
child objects. It is defined by having a transaction drawn around it.

Vaughn Vernon extended the pattern further in *Implementing Domain-Driven
Design*, Addison-Wesley, 2013, Chapter 10, "Aggregates", and in a widely
circulated three-part community essay, "Effective Aggregate Design",
published through the Domain-Driven Design community site (Vaughn Vernon,
"Effective Aggregate Design," dddcommunity.org, PDF, verified 2026-08-02,
https://www.dddcommunity.org/wp-content/uploads/files/pdf_articles/Vernon_2011_1.pdf).
Vernon's contribution is not a new pattern, it is a set of hard-won sizing and
referencing rules that turn Evans's abstract definition into something a team
can actually apply without producing an aggregate the size of the whole
database. Those rules are load-bearing enough that dimension 3 below is built
directly on them.

## 2. Problem and context

A domain model contains rules that span more than one object. An `Order`'s
total must equal the sum of its `OrderLine` items minus any applied discount.
A `Playlist` must never exceed its subscription tier's track limit. A
`BankAccount`'s balance must never go negative once an overdraft protection
flag is off. Each of these rules involves at least two pieces of state that
must be read and written together, inside one atomic operation, or the rule
can be violated by two operations that each look correct in isolation.

The concrete failure this produces, seen in almost every codebase that grew
without a designated consistency boundary. A shipping module needs an order's
destination address, so it loads the `Order` row and, because `OrderLine` is
its own independently addressable table with its own repository, a different
module inserts a discount line directly into that table to apply a promotion.
Nothing in the schema or the type system stops this. The insert commits.
The order's own logic, which would have checked whether a discount is already
applied and whether this brings the total below the minimum order value,
never ran, because the mutation entered through a side door. Two features,
each independently correct against its own requirements, together produce an
order with a broken total. Nobody who worked on either feature would think to
audit the other, because from where they stood, they never touched the order.

This is a concurrency problem as much as a modeling problem. Two requests can
race to update a `Playlist`'s track count and its list of tracks
independently, and if the count and the list live in separate rows updated by
separate statements, the count can drift from the true length of the list
under load, silently, without either statement raising an error. The Aggregate
pattern exists because a domain rule that spans multiple objects needs
exactly one thing to make it enforceable, a boundary such that every write
touching any object inside it goes through a single transaction, gated by a
single object that can check the rule before the transaction commits. That
boundary is the aggregate, and dimension 3 explains why that boundary should
usually be drawn small rather than large.

## 3. Forces

Consistency versus concurrency. A larger aggregate can hold more invariants
true at all times, because more state sits inside one transaction. But every
write to any part of a large aggregate contends for the same lock or the same
optimistic-concurrency version, so two users editing unrelated parts of a
large aggregate collide on writes that have nothing to do with each other.
Vernon's first rule of thumb in *Implementing Domain-Driven Design* is
"protect true invariants in consistency boundaries", which reads as a
narrowing instruction. Protect only the rules that genuinely must be atomic,
and nothing else, because everything added to the boundary is contention
being chosen to pay for.

Coupling versus expressiveness. An aggregate that holds direct object
references to other aggregates lets code walk the whole graph naturally,
`order.customer.address`, which reads well and compiles easily. But that
reference is exactly the side door from dimension 2, because it lets code
outside the customer aggregate reach in and mutate customer state while
believing it is only reading an order. Vernon's second rule, echoed by the
Azure Architecture Center guide's line "reference other aggregates by identity
only", trades that navigational convenience for isolation. `order.customerId`
compiles to a lookup, not a mutation path.

Transaction cost versus staleness. Keeping every related fact inside one
aggregate means every read of that aggregate is guaranteed fresh and every
invariant is checked on every write. But loading a large aggregate, even to
change one field, means loading and locking everything else inside it, which
is expensive under load and gets worse as the aggregate grows. Vernon's third
rule, "update other aggregates using eventual consistency", accepts staleness
between aggregates as the price of keeping each individual aggregate small and
each individual transaction cheap.

Team topology and cognitive load. A small number of large aggregates makes it
easier for a person to hold the whole order subsystem in their head, because
fewer boundaries exist to track. A larger number of small aggregates
distributes ownership more cleanly across teams, because each team's aggregate
is genuinely independent of the others' internals, at the cost of more
boundaries and more explicit coordination code, domain events and sagas,
between them.

Operability. A small aggregate is a small unit of database locking, a small
unit of cache invalidation, and, in an event-sourced system, a short event
stream to replay on load. A large aggregate concentrates operational risk.
One hot aggregate under contention becomes a single point of throughput
degradation for the whole feature built on top of it.

The pattern's own literature is explicit that it favors the first side of
almost every one of these trade-offs. Small aggregates, reference by identity,
eventual consistency between aggregates. The forces are not balanced evenly.
The documented, hard-won advice consistently sacrifices convenience and raw
consistency scope for concurrency and decoupling, because the failure mode of
an aggregate that is too large, lock contention, stale reads across an
oversized graph, tangled invariants, is judged worse in practice than the
failure mode of an aggregate that is too small, an extra event, an extra
eventually-consistent read, a slightly less convenient object graph.

## 4. Applicability and non-applicability

Reach for an Aggregate when a rule must hold true at the instant a transaction
commits and cannot be allowed to be false even momentarily. An account balance
that must never go negative under concurrent withdrawals. An inventory count
that must never be sold below zero units. A booking system that must never
double book the same seat in the same show. In each case the rule spans more
than one piece of state, balance and withdrawal, stock and sale, seat and
booking, and the cost of violating it, even briefly, is a real world
inconsistency a person notices, an overdraft, an oversold seat.

Reach for it when the transactional boundary has already been identified and
a place is needed for the invariant checking logic, not as a generic grouping
device for things that are merely related. Relatedness is not the criterion.
Transactional necessity is.

Do not reach for it as the default shape for every Entity in a domain model. A
single freestanding Entity with no invariant that spans other objects, for
example a `Category` record used purely as a lookup value with no rule
governing it beyond uniqueness of its own name, does not need an aggregate
boundary drawn around anything, because there is nothing else it must stay
consistent with. Wrapping every entity in an aggregate abstraction because it
is DDD produces ceremony with no corresponding benefit.

Do not use Aggregate to model a purely read oriented view that spans many
records for display purposes, such as an order history report joining orders,
customers, and products. That is a query concern, typically served by a
read-only projection or a CQRS read model, not a consistency boundary, because
nothing is being written and there is no invariant to protect. Forcing a
report through an aggregate's repository adds write path overhead, loading the
whole graph, locking, to a path that never writes.

Do not let an aggregate span two things that genuinely have independent life
cycles just because they are usually created together. Vernon's own drone
delivery example from the Azure Architecture Center guide separates
`Delivery`, `Package`, `Drone`, and `Account` into four aggregates precisely
because, although a delivery references a package, a drone, and an account,
each of those four has its own life cycle, its own rate of change, and its own
owner, and combining them "forces unrelated updates to compete for the same
locks" (Microsoft Learn, "Use Tactical DDD to Design Microservices," verified
2026-08-02).

Do not reach for Aggregate to solve a purely technical persistence concern,
such as two tables always being joined in the same query, so making them one
aggregate for efficiency. Aggregate boundaries are drawn by invariants, not by
query patterns. A boundary drawn for query convenience routinely produces an
aggregate that is too large for its actual consistency needs, reintroducing
the contention problem dimension 3 describes.

Do not use it inside a bounded context that has no genuine business
invariants worth protecting, most commonly a thin CRUD administrative screen
over a single table with no cross field rule. An anemic Entity with a plain
repository is the honest, simpler shape there, and reaching for Aggregate adds
a root object, an invariant checking method, and a mental model with nothing
underneath it to justify the cost.

## 5. Structure

Aggregate Root. Exactly one Entity inside the cluster, the sole object any
code outside the aggregate is permitted to hold a reference to or invoke a
method on. Every command that mutates the aggregate's state is a method call
on the root. The root is responsible for keeping every invariant that spans
the whole cluster true at the end of every method call. See `aggregate-root.md`
for the deep treatment of this participant on its own.

Local Entities. Zero or more Entities that exist only inside the boundary of
one aggregate instance and have no identity meaningful outside it. An
`OrderLine` inside an `Order` aggregate is addressed, from outside the
aggregate, only by loading the `Order` and navigating to it, never by an
independent repository of its own. A local Entity's identity is typically
scoped to its parent, a line number unique within an order rather than
globally unique, which is the structural signal that it belongs inside the
boundary rather than standing alone.

Value Objects. Immutable objects with no identity, owned by the root or by a
local Entity, used to represent measured or descriptive facts inside the
aggregate. `Money`, `Address`, `Quantity`. See `value-object.md` for the
pattern on its own. Value Objects never carry their own identity and are
always replaced wholesale on change, never mutated in place.

The Invariant. The rule or set of rules the aggregate exists to protect, kept
consistent at the end of every root method that changes state. This is not a
structural participant in the usual sense, it has no class of its own, but it
is the reason the boundary is drawn where it is drawn, and every method on the
root is written against it.

The Transaction Boundary. The technical mechanism, most often a database
transaction or an optimistic concurrency check on a version field, that
enforces the rule of one aggregate instance, one transaction, per write. This
boundary is what turns "we intend the invariant to hold" into "the invariant
provably holds after every commit".

External References. Other aggregates are referenced from inside this one by
identity value only, never by object reference. An `Order` aggregate holds a
`CustomerId`, not a `Customer` object, and any code inside the `Order`
aggregate that needs customer data performs a separate lookup through the
customer aggregate's own repository, outside the order's transaction.

## 6. ASCII structure diagram

```
                          Aggregate boundary
                     (one transaction, one lock)
   +---------------------------------------------------------+
   |                                                           |
   |    Aggregate Root: Order                                 |
   |    +------------------------------------------------+    |
   |    | id: OrderId                                     |    |
   |    | status: OrderStatus                             |    |
   |    | total: Money            <-- Value Object         |    |
   |    | customerId: CustomerId  <-- reference by id only |    |
   |    +------------------------------------------------+    |
   |         |                                                 |
   |         | owns (local, no independent identity)           |
   |         v                                                 |
   |    +----------------------+   +----------------------+    |
   |    | OrderLine (local)    |   | OrderLine (local)     |    |
   |    | lineNo: int          |   | lineNo: int            |    |
   |    | qty: Quantity        |   | qty: Quantity          |    |
   |    | unitPrice: Money     |   | unitPrice: Money       |    |
   |    +----------------------+   +----------------------+    |
   |                                                           |
   +---------------------------------------------------------+
          |                                    |
          | id reference only                  | id reference only
          v                                    v
   +---------------+                    +----------------+
   | Customer      |                    | Product        |
   | (separate     |                    | (separate      |
   |  aggregate)   |                    |  aggregate)    |
   +---------------+                    +----------------+
```

Everything inside the outer box loads, locks, and commits as one unit through
the `Order` root. Everything outside it, `Customer` and `Product`, is reached
only through an id, never a live reference, so a write to `Order` never
touches, locks, or races against a write to `Customer`.

## 7. Dynamics

The canonical write sequence, load, invoke, persist, is the same shape for
every command against an aggregate, whether the aggregate is stored as rows in
a relational table or reconstructed from an event stream.

```
Client                Application Service        Repository        Aggregate Root
  |                          |                        |                   |
  | placeOrder(cmd)          |                        |                   |
  |------------------------->|                        |                   |
  |                          | load(orderId)          |                   |
  |                          |----------------------->|                   |
  |                          |                        | fetch row(s),     |
  |                          |                        | rehydrate root    |
  |                          |                        | + local entities  |
  |                          |<-----------------------|                   |
  |                          |             order (in-memory aggregate)    |
  |                          |------------------------------------------->|
  |                          |    order.addLine(productId, qty, price)    |
  |                          |                        |                   |
  |                          |                        |    check invariant
  |                          |                        |    total + line vs limit
  |                          |                        |    raise DomainEvent
  |                          |<-------------------------------------------|
  |                          | ok / DomainError                           |
  |                          | save(order)             |                   |
  |                          |----------------------->|                   |
  |                          |                        | begin tx           |
  |                          |                        | write root row,    |
  |                          |                        | write local rows,  |
  |                          |                        | check version      |
  |                          |                        | commit tx (atomic) |
  |                          |<-----------------------|                   |
  |<-------------------------|                        |                   |
```

Exactly one transaction spans the whole write. If the version check at commit
fails because another process changed the same aggregate concurrently, the
whole write is rejected and retried from the top, never partially applied.
This is the mechanism that makes one aggregate, one transaction more than a
guideline, it is enforced by the repository and the database on every call.

The cross-aggregate flow is deliberately different in shape. A domain event
raised inside one aggregate's transaction is published only after that
transaction commits, and a separate handler, running in its own transaction
against a different aggregate, reacts to it.

```
  Order aggregate tx                         (commit)          Inventory aggregate tx
  ----------------------                    ---------          -----------------------
  order.confirm()
    invariant checked, ok
    raises OrderConfirmed(orderId, lines)
  save(order)  --------------------------------> commit --.
                                                             \
                                                              v
                                              event bus / outbox delivers OrderConfirmed
                                                              |
                                                              v
                                          InventoryHandler.on(OrderConfirmed)
                                                              |
                                              inventory.reserve(lines)
                                              invariant checked, ok
                                              save(inventory) -----------------> commit
```

Between the first commit and the second, the system is in a state where the
order says confirmed but inventory has not yet reserved stock. That window is
the eventual consistency dimension 3 names explicitly, and it is a designed
property of the pattern, not a bug the pattern fails to prevent.

## 8. Implementation variants

State-based persistence. The aggregate's current field values are read from
and written to storage directly, typically one row per root plus one or more
child tables for local entities, all inside one transaction with an
optimistic concurrency version column. This is the default, most widely used
shape, exemplified by Spring Data JDBC's aggregate model, discussed under
dimension 9.

Event-sourced persistence. The aggregate's current state is never stored
directly. Instead every state change is appended as an immutable domain event
to a stream keyed by the aggregate's id, and the aggregate is rebuilt by
replaying its events from the start, or from the last snapshot, whenever it is
loaded. The invariant check happens against the rebuilt in-memory state before
a new event is appended. This variant trades read cost, replay on every load,
mitigated by snapshotting, for a complete, immutable audit trail and native
support for temporal queries. Axon Framework implements this variant, where
"command handlers live on the entity class itself, alongside its state fields
and event sourcing handlers" (Axon Framework Reference, "Commands," verified
2026-08-02, https://docs.axoniq.io/axon-framework-reference/5.0/commands/).

Aggregate as a plain in-memory object with no framework. Many production
codebases implement the pattern with nothing more than a class that enforces
its invariants in its own methods and a hand-written repository that wraps a
database transaction. No annotation, no event store, no special base class.
This is the shape shown in the code samples below, and it is the correct
starting point for most teams, because the pattern's value is the discipline
of the boundary, not any particular framework's machinery.

Language-idiomatic shape in a functional-leaning style. Rather than a mutable
object whose methods enforce invariants in place, the aggregate is modeled as
an immutable value plus a set of pure functions, decide(command, state)
returning an event, and evolve(state, event) returning a new state, common in
event-sourced systems written in Rust, F#, or functional TypeScript. The
invariant check happens inside decide, which returns either an event to apply
or a rejection, and no mutation occurs until the caller applies the returned
event through evolve. This shape makes the invariant check a pure, trivially
unit-testable function with no database or object-identity concerns at all.

Aggregate as owned entity graph in an ORM. In an object-relational mapper,
the aggregate is expressed as a graph of owned or embedded types rooted at one
mapped entity, where the child types have no independent table level identity
of their own and are always loaded, saved, and deleted as part of the owner.
Entity Framework Core's owned entity types are explicitly modeled this way,
described in Microsoft's own documentation as "conceptually similar to
aggregates" and constrained so that "instances of owned entity types cannot be
shared by multiple owners" (Microsoft Learn, "Owned Entity Types - EF Core,"
verified 2026-08-02,
https://learn.microsoft.com/en-us/ef/core/modeling/owned-entities).

## 9. Known production uses

Spring Data JDBC treats the aggregate as its central persistence concept
rather than an optional add-on. Its own reference documentation states, "all
entities reachable from an aggregate root are considered to be part of that
aggregate root," and that the framework "assumes that only the aggregate has a
foreign key to a table storing non-root entities of the aggregate and no other
entity points toward non-root entities." It states the cross-aggregate
consequence in the same terms Vernon uses. "References across aggregates are
not guaranteed to be consistent at all times. They are guaranteed to become
consistent eventually." (Spring Data JDBC Reference Documentation, "Domain
Driven Design and Spring Data JDBC," verified 2026-08-02,
https://docs.spring.io/spring-data/relational/reference/jdbc/domain-driven-design.html).

Axon Framework, a Java framework for building event-driven and CQRS-style
applications, models the aggregate directly as an addressable object whose
command handlers and event-sourcing handlers live together on the same class,
loaded and locked as a unit per command, and rebuilt from its own event stream
(Axon Framework Reference, "Commands," verified 2026-08-02,
https://docs.axoniq.io/axon-framework-reference/5.0/commands/).

Entity Framework Core's owned entity type feature exists specifically to let
.NET applications persist an aggregate as one unit without giving the child
types their own database level identity or independent DbSet, so a
StreetAddress embedded in an Order cannot be queried, tracked, or shared
independently of the Order that owns it (Microsoft Learn, "Owned Entity Types
EF Core," verified 2026-08-02,
https://learn.microsoft.com/en-us/ef/core/modeling/owned-entities).

Microsoft's own Azure Architecture Center uses the pattern as the primary tool
for deciding microservice boundaries in its reference drone delivery
architecture, deliberately splitting `Delivery`, `Package`, `Drone`, and
`Account` into four separate aggregates, each independently loadable,
lockable, and deployable, communicating across the boundary only through
domain events such as `DeliveryCompleted` (Microsoft Learn, "Use Tactical DDD
to Design Microservices," verified 2026-08-02,
https://learn.microsoft.com/en-us/azure/architecture/microservices/model/tactical-domain-driven-design).
The guide states its sizing principle for microservice decomposition directly
in aggregate terms. "Design a microservice to be no smaller than an aggregate
and no larger than a bounded context," which places the pattern at the exact
lower bound of what a single deployable service is allowed to be.

## 10. Consequences

Positive. The invariant that motivated the boundary is provably true after
every commit, never merely true in the common case. Every write to the
protected state passes through one method on one root, which is the single
place a reader looks to understand the rule, rather than the rule being spread
across every module that happens to touch the data. Small, well-bounded
aggregates reduce lock contention because unrelated features stop competing
for the same rows. The repository per aggregate root, see `repository.md`,
gives every use case one clean load-mutate-save unit to reason about, test,
and mock. In an event-sourced variant, the aggregate's history is a complete,
replayable audit log for free.

Negative. Any state that must be consistent across two aggregates is no
longer consistent inside one transaction, and the application must accept and
design for the resulting window of staleness, typically closed by a domain
event and an eventually-consistent handler. This is a real design cost, not a
detail, because it means every cross-aggregate business process needs its own
compensating logic for the case where the second step fails after the first
one committed, the classic partial-failure problem sagas exist to solve. A
poorly sized aggregate, too large, reproduces the exact contention the pattern
exists to avoid, and too small, pushes an invariant that genuinely needed
atomicity out into eventually-consistent territory where it can be
momentarily false in a way a user or auditor can observe. Loading a large
aggregate, even to read one field, costs a full graph load, which is a real
performance tax paid on every access, not only on writes. The discipline of
reference by identity, not object reference, adds a lookup indirection every
time code legitimately needs data from a neighboring aggregate, which some
teams new to the pattern experience as friction relative to a plain ORM graph
where every association is a live, navigable reference.

## 11. Failure modes and misuse

Symptom. The aggregate's repository or ORM mapping shows dozens of child
tables joined into a single load, and a simple status update takes
noticeably longer under load than an equivalent single-table update
elsewhere in the same codebase.
Cause. The aggregate boundary was drawn around everything that seemed
related rather than around the actual invariant, producing what practitioners
commonly call a God aggregate, one boundary trying to protect too many
independent rules at once.
Fix. Identify which invariants genuinely require atomicity and which merely
happened to be modeled together. Split the aggregate along the seam between
them, replacing the direct in-memory reference between the two halves with an
id reference and, where a rule must still react across the new boundary, a
domain event.

Symptom. Two features that touch what looks like unrelated data intermittently
deadlock or throw optimistic concurrency exceptions against each other under
concurrent load, even though the features are, from a product standpoint,
about completely different things.
Cause. Both features are writing to the same oversized aggregate, so their
unrelated writes contend for the same row lock or the same version number,
exactly the failure Vernon's rule to design small aggregates exists to avoid.
Fix. Trace both write paths back to the shared aggregate root and split it,
same remedy as above, this time driven by the concurrency evidence rather than
by inspection of the model alone.

Symptom. A report or a downstream service occasionally shows data that
contradicts what a user just did seconds earlier, an order was confirmed but
the inventory count still shows the old value.
Cause. This can be a genuine, correctly designed consequence of eventual
consistency between two aggregates, and the fix in that case is UX, not code,
showing the order as confirmed while the reservation is pending. But it is
also the symptom produced when the event that should propagate the change
across the boundary is dropped, never published, or the handler on the far
side silently fails without retry.
Fix. First confirm which case this is. If the design intends eventual
consistency, the fix is to surface pending state honestly in the UI rather
than hide it. If the event delivery is genuinely unreliable, the fix is a
transactional outbox or an equivalent at-least-once delivery mechanism so the
publish of the event and the commit of the originating aggregate cannot
diverge.

Symptom. Code outside the aggregate directly mutates a field on a child object
reached through the root, calling a setter on a line inside an order's list
directly rather than through the order's own method.
Cause. The local Entities or their collections were exposed with public
setters or a mutable collection reference, so the root's method-based
enforcement was bypassed entirely, the same side-door failure described in
dimension 2, now happening inside the codebase that supposedly implements the
pattern rather than around it.
Fix. Expose child collections as read-only views, and require every mutation
to go through an intention-revealing method on the root, such as
changeLineQuantity, so the invariant check is structurally unavoidable, not
merely a convention nobody enforces.

Symptom. Every use case in the application ends up loading the entire
aggregate graph even when it only needs to read one summary field, producing
consistently high query latency for what should be a cheap read.
Cause. The team conflated the write model with the only model, forcing every
read path through the same aggregate-shaped repository that the write path
uses, instead of serving reads from a separate, denormalized projection.
Fix. Introduce a read model or projection alongside the aggregate, per the
CQRS pattern, reserving the aggregate's load path for the transactional write
path it was actually designed for.

## 12. Trade-off matrix

| Force | Aggregate | Single database transaction, no explicit boundary | Distributed saga across services with no local invariant object | Anemic entities plus a coordinating service |
|---|---|---|---|---|
| Enforces invariant on every write | Yes, structurally, through the root | Only if every caller remembers to include the check | No, invariant checking is scattered across the saga's steps | Only if the service remembers to check it every time |
| Concurrency under load | Good, scoped to a small, well-drawn boundary | Poor, whole-table or whole-database locking pressure | Good within each service, but the overall business invariant can be violated mid-saga | Poor, no natural lock scope, prone to races |
| Cross-boundary consistency | Eventual, via domain events | Immediate, but only within one database | Eventual, explicitly compensated | Eventual or immediate depending on ad hoc code, inconsistent |
| Where the rule lives | On the root, one findable place | Scattered across every caller that touches the tables | Scattered across saga steps and compensations | Scattered across service methods |
| Suitability for microservice boundary | Natural minimum service size, per Azure Architecture Center guidance | Not a boundary at all, encourages a shared database anti-pattern | Natural for cross-service processes, but needs a local aggregate at each step to be safe | Weak, invites duplicated or inconsistent logic per service |
| Testability of the rule | High, a pure unit test against the root's methods | Low, requires a real transaction and every caller under test | Low, requires orchestrating the whole saga or heavy mocking | Low, the rule is implicit in service code, easy to test around by accident |

## 13. Related and incompatible patterns

Aggregate Root, `aggregate-root.md`, is the mechanism, not a separate concept.
Aggregate names the boundary, Aggregate Root names the single gated entry
point through which the boundary is enforced. Every aggregate has exactly one
root, and the two entries are meant to be read together.

Entity, `entity.md`, and Value Object, `value-object.md`, are the raw
materials an aggregate is built from. The root is always an Entity. Local
objects inside the aggregate may be either, depending on whether they need
identity tracked over time, a local Entity, or are fully described by their
current attributes, a Value Object, always replaced, never mutated in place.

Repository, `repository.md`, is the pattern that persists and reconstitutes
an aggregate as a whole. The rule of one repository per aggregate root, never
per child entity, is a direct structural consequence of the aggregate
boundary, because a repository for a local Entity would let outside code load
and save that Entity independently of the invariant its root exists to
protect.

Factory, `factory.md`, is frequently used to construct a new aggregate
instance in a valid state from the first moment it exists, particularly when
construction itself involves an invariant, such as an order that cannot be
created with zero lines, that is awkward to express inside a plain
constructor.

Domain Event, `domain-event.md`, is the standard mechanism for coordinating
across two aggregate boundaries once they cannot share one transaction. The
root raises the event as part of its own transaction, and a handler reacting
to it, in a separate transaction against a different aggregate, is how the
eventual-consistency force from dimension 3 is actually implemented in code
rather than merely accepted as a fact about the system.

Bounded Context, `bounded-context.md`, is the larger container an aggregate
lives inside. Multiple aggregates typically live in one bounded context, and
the Azure Architecture Center's own sizing rule, no smaller than an aggregate
and no larger than a bounded context, places Aggregate at the lower structural
bound and Bounded Context at the upper one for what a single microservice is
allowed to be.

Incompatible with treating the whole domain model as one giant aggregate,
sometimes produced by an ORM's default load-everything-reachable behavior.
That shape defeats the pattern's entire purpose, because a single
all-encompassing consistency boundary reintroduces exactly the lock
contention and whole-graph loading cost the pattern exists to eliminate, and
it typically signals that no genuine invariant analysis, dimension 3,
dimension 4, was ever performed.

## 14. Refactoring path in and out

Introducing an Aggregate into code that has none, most often a set of plain
Entities each with their own independent repository and no enforced
invariant, proceeds in stages.

Step one. Name the invariant explicitly, in one sentence, before writing any
code. "The order total must always equal the sum of its lines minus any
applied discount" is a testable sentence. "The order and its lines should be
consistent" is not, and cannot be turned into a unit test.

Step two. Identify every piece of state the invariant reads or writes. That
set of state is the candidate aggregate boundary, and nothing more should be
pulled in on the grounds that it is merely related.

Step three. Pick the root. It is the object every external caller should
reference going forward, typically the object that already has the most
natural external identity, an order number, an account number.

Step four. Remove independent repositories or independent update paths for
every other object identified in step two, and replace them with methods on
the root, addLine and applyDiscount rather than direct table access, each of
which re-checks the invariant before returning.

Step five. Replace any live object reference this cluster held to another
aggregate with an id, and move any code that needed to reach through that
reference into an explicit, separate lookup call against the other
aggregate's own repository.

Step six. Wrap the whole set of writes in one transaction inside the
repository's save method, and add an optimistic concurrency version to the
root's storage row so concurrent writers are detected rather than silently
overwritten.

Removing an Aggregate, when it stops earning its place, most commonly because
the invariant that justified the boundary was relaxed by a later business
decision or never existed as tightly as originally modeled, is the mirror
image. Confirm the invariant is genuinely gone or genuinely no longer needs
atomicity, split the local entities back into independently addressable
objects with their own repositories if they now have real independent life
cycles, and delete the root's invariant-checking methods in favor of direct
CRUD, only after confirming no caller anywhere still depends on the atomicity
guarantee that is about to be removed.

## 15. Testing and verification

The aggregate root's invariant is, by design, testable as a pure in-memory
unit test with no database, no transaction, and no framework. Construct the
root, directly or through its factory, call the method that should enforce
the rule, and assert either the resulting state or the raised domain error.
This is one of the pattern's strongest practical benefits, because the
invariant, the exact thing that motivated drawing the boundary in the first
place, ends up being the cheapest and fastest thing in the whole system to
test.

Write a test for every branch of the invariant, not only the success path.
For an order line limit, test at the limit, one under, and one over, and test
that the rejected call leaves the aggregate's in-memory state unchanged, since
a common bug is a partial mutation applied before the invariant check fails.

Test the repository separately from the aggregate's own logic, using an
integration test against a real, or test-container, database, specifically to
verify the concurrency mechanism. Load the same aggregate in two separate
in-memory instances, save the first, then attempt to save the second, and
assert that the second save is rejected rather than silently overwriting the
first. This is the test that actually proves the transaction boundary from
dimension 5 is real rather than assumed, and it is routinely the test teams
skip, because it requires deliberately simulating a race rather than a single
happy-path call.

For an event-sourced aggregate, test decide and evolve as separate pure
functions where the implementation variant allows it, dimension 8. Given a
sequence of prior events, the aggregate's history, and a new command, assert
the exact event decide returns, or the exact rejection. This makes even a
long, complex history trivially reproducible in a test without touching an
event store, because the given, when, then shape of the test maps directly
onto prior events, new command, expected event.

Test cross-aggregate coordination, the domain event handler that reacts in a
different aggregate's transaction, as its own separate test, asserting that
the handler correctly applies the change and that a failure inside the
handler does not silently swallow the event, since that failure mode is the
direct cause of the confirmed-order-unreserved-inventory symptom in dimension
11.

## 16. Observability signals

Log or trace every aggregate command with the aggregate's type, its id, and
the command name at minimum, so a single confusing production incident, such
as an order showing the wrong total, can be answered by pulling every command
that ever touched that specific aggregate instance, in order.

Instrument optimistic concurrency conflicts as a first-class metric, a counter
incremented every time a save is rejected because the loaded version does not
match the current stored version. A healthy aggregate shows a low, steady rate
of conflicts proportional to genuine concurrent access. A rising rate against
one specific aggregate type, especially one that grows disproportionately to
traffic, is the earliest reliable signal that the aggregate has become too
large or too hot, exactly the symptom named in dimension 11.

Measure aggregate load size, the number of child rows or events fetched per
load, as a distribution, not an average. A healthy small aggregate shows a
tight, low distribution. A long tail, some instances loading orders of
magnitude more child data than the median, usually means the boundary was
drawn around an unbounded collection, a customer aggregate that grows an
orders list forever rather than referencing orders by id, which is exactly
the kind of drift the pattern's own reference-other-aggregates-by-identity
rule exists to prevent.

For domain events crossing an aggregate boundary, track publish success, the
time between the originating commit and the event reaching its handler, and
handler failure rate separately. A widening gap between those two, or a
nonzero, unmonitored handler failure rate, is the direct operational cause of
the stale cross-aggregate reads described in dimension 11, and it is the
signal that should trigger investigation before a user notices the
inconsistency.

## 17. Security and privacy implications

The aggregate boundary is, incidentally, an authorization boundary that is
easy to get right or wrong depending on where checks are placed. Because every
mutation to the cluster is required to pass through the root's methods, that
is also the single, correct place to enforce that the calling user is
authorized to perform the specific mutation, such as only the order's owner
or an agent with an override permission being allowed to apply a discount.
Placing the authorization check inside the root method, rather than in the
calling application service alone, means the check travels with the invariant
and cannot be bypassed by a second call site that forgot to repeat it,
mirroring the exact discipline the pattern already enforces for the domain
rule itself.

The reference-by-identity discipline between aggregates, dimension 3, load
across boundaries only by id, has a privacy benefit that is easy to overlook.
An aggregate that references another only by an opaque identifier, rather than
by embedding a live copy of that other aggregate's fields, cannot accidentally
leak that other aggregate's sensitive data into a log, a cache entry, or a
serialized API response simply because it happened to be reachable through an
object graph. An `Order` that holds `customerId` cannot leak the customer's
address by accident. An `Order` that embeds a full `Customer` object can, the
moment anyone serializes the order for logging or for an event payload without
remembering to strip it first.

Domain events published across an aggregate boundary should carry the minimum
data the handler actually needs, not a full snapshot of the originating
aggregate's state, because that event typically travels through an event bus
or message broker with its own retention, replication, and access-control
characteristics, distinct from the originating database's. An `OrderConfirmed`
event carrying full customer payment details because it was convenient to
include widens the blast radius of any downstream system that consumes that
event, well past whatever access controls the order's own repository
enforces.

Event-sourced aggregates, dimension 8, accumulate an immutable, permanent
history of every state change by design, which is a real conflict with any
requirement to delete or amend a specific piece of personal data after the
fact, since the value the pattern deletion is trying to remove may still be
recoverable by replaying earlier events. Teams choosing event sourcing for an
aggregate that will hold regulated personal data should decide, before the
first event is written, on an explicit strategy, encryption keyed per subject
and destroyed on erasure, or field-level redaction applied at the projection
layer rather than the append-only store, because retrofitting either approach
onto an event store already carrying years of unredacted history is
considerably harder than designing it in from the first commit.

## 18. References

1. Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*, Addison-Wesley, 2003, Chapter 6, "The Life Cycle of a Domain
   Object", section "Aggregates".
2. Vaughn Vernon, *Implementing Domain-Driven Design*, Addison-Wesley, 2013,
   Chapter 10, "Aggregates".
3. Vaughn Vernon, "Effective Aggregate Design," dddcommunity.org, PDF
   article, verified 2026-08-02,
   https://www.dddcommunity.org/wp-content/uploads/files/pdf_articles/Vernon_2011_1.pdf
4. Martin Fowler, "DDD_Aggregate," martinfowler.com bliki, verified
   2026-08-02, https://martinfowler.com/bliki/DDD_Aggregate.html
5. Microsoft Learn, "Use Tactical DDD to Design Microservices," Azure
   Architecture Center, verified 2026-08-02,
   https://learn.microsoft.com/en-us/azure/architecture/microservices/model/tactical-domain-driven-design
6. Microsoft Learn, "Use Domain Analysis to Model Microservices," Azure
   Architecture Center, verified 2026-08-02,
   https://learn.microsoft.com/en-us/azure/architecture/microservices/model/domain-analysis
7. Spring Data JDBC Reference Documentation, "Domain Driven Design and
   Spring Data JDBC," verified 2026-08-02,
   https://docs.spring.io/spring-data/relational/reference/jdbc/domain-driven-design.html
8. Axon Framework Reference Guide, "Commands," verified 2026-08-02,
   https://docs.axoniq.io/axon-framework-reference/5.0/commands/
9. Microsoft Learn, "Owned Entity Types - EF Core," verified 2026-08-02,
   https://learn.microsoft.com/en-us/ef/core/modeling/owned-entities

## Code examples

### TypeScript

```typescript
type Money = { readonly cents: number; readonly currency: string };

function addMoney(a: Money, b: Money): Money {
  if (a.currency !== b.currency) {
    throw new Error("currency mismatch");
  }
  return { cents: a.cents + b.cents, currency: a.currency };
}

interface OrderLine {
  readonly lineNo: number;
  readonly productId: string;
  readonly quantity: number;
  readonly unitPrice: Money;
}

class DomainError extends Error {}

class Order {
  private readonly _id: string;
  private readonly _customerId: string;
  private _lines: OrderLine[] = [];
  private _confirmed = false;

  private static readonly MAX_LINES = 25;

  private constructor(id: string, customerId: string) {
    this._id = id;
    this._customerId = customerId;
  }

  static create(id: string, customerId: string): Order {
    return new Order(id, customerId);
  }

  get id(): string {
    return this._id;
  }

  get lines(): readonly OrderLine[] {
    return this._lines;
  }

  get total(): Money {
    return this._lines.reduce(
      (sum, l) => addMoney(sum, { cents: l.unitPrice.cents * l.quantity, currency: l.unitPrice.currency }),
      { cents: 0, currency: "USD" }
    );
  }

  addLine(productId: string, quantity: number, unitPrice: Money): void {
    if (this._confirmed) {
      throw new DomainError("cannot modify a confirmed order");
    }
    if (this._lines.length >= Order.MAX_LINES) {
      throw new DomainError(`order cannot exceed ${Order.MAX_LINES} lines`);
    }
    if (quantity <= 0) {
      throw new DomainError("quantity must be positive");
    }
    const lineNo = this._lines.length + 1;
    this._lines = [...this._lines, { lineNo, productId, quantity, unitPrice }];
  }

  confirm(): void {
    if (this._lines.length === 0) {
      throw new DomainError("cannot confirm an order with no lines");
    }
    this._confirmed = true;
  }
}

function main(): void {
  const order = Order.create("ord-1", "cust-42");
  order.addLine("sku-1", 2, { cents: 500, currency: "USD" });
  order.addLine("sku-2", 1, { cents: 1200, currency: "USD" });
  console.log("total cents before confirm", order.total.cents);
  order.confirm();

  try {
    order.addLine("sku-3", 1, { cents: 100, currency: "USD" });
  } catch (e) {
    if (e instanceof DomainError) {
      console.log("rejected as expected", e.message);
    }
  }
}

main();
```

### Python

```python
from __future__ import annotations
from dataclasses import dataclass, field


class DomainError(Exception):
    pass


@dataclass(frozen=True)
class Money:
    cents: int
    currency: str

    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise DomainError("currency mismatch")
        return Money(self.cents + other.cents, self.currency)


@dataclass(frozen=True)
class OrderLine:
    line_no: int
    product_id: str
    quantity: int
    unit_price: Money

    def line_total(self) -> Money:
        return Money(self.unit_price.cents * self.quantity, self.unit_price.currency)


MAX_LINES = 25


@dataclass
class Order:
    order_id: str
    customer_id: str
    _lines: list[OrderLine] = field(default_factory=list)
    _confirmed: bool = False

    @property
    def lines(self) -> tuple[OrderLine, ...]:
        return tuple(self._lines)

    def total(self) -> Money:
        result = Money(0, "USD")
        for line in self._lines:
            result = result.add(line.line_total())
        return result

    def add_line(self, product_id: str, quantity: int, unit_price: Money) -> None:
        if self._confirmed:
            raise DomainError("cannot modify a confirmed order")
        if len(self._lines) >= MAX_LINES:
            raise DomainError(f"order cannot exceed {MAX_LINES} lines")
        if quantity <= 0:
            raise DomainError("quantity must be positive")
        line_no = len(self._lines) + 1
        self._lines.append(OrderLine(line_no, product_id, quantity, unit_price))

    def confirm(self) -> None:
        if not self._lines:
            raise DomainError("cannot confirm an order with no lines")
        self._confirmed = True


def main() -> None:
    order = Order(order_id="ord-1", customer_id="cust-42")
    order.add_line("sku-1", 2, Money(500, "USD"))
    order.add_line("sku-2", 1, Money(1200, "USD"))
    print("total cents before confirm", order.total().cents)
    order.confirm()

    try:
        order.add_line("sku-3", 1, Money(100, "USD"))
    except DomainError as e:
        print("rejected as expected", e)


if __name__ == "__main__":
    main()
```

### Rust

```rust
#[derive(Debug, Clone, Copy, PartialEq)]
struct Money {
    cents: i64,
    currency: &'static str,
}

impl Money {
    fn add(self, other: Money) -> Result<Money, DomainError> {
        if self.currency != other.currency {
            return Err(DomainError::CurrencyMismatch);
        }
        Ok(Money { cents: self.cents + other.cents, currency: self.currency })
    }
}

#[derive(Debug)]
enum DomainError {
    CurrencyMismatch,
    OrderConfirmed,
    TooManyLines,
    NonPositiveQuantity,
    NoLines,
}

impl std::fmt::Display for DomainError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            DomainError::CurrencyMismatch => write!(f, "currency mismatch"),
            DomainError::OrderConfirmed => write!(f, "cannot modify a confirmed order"),
            DomainError::TooManyLines => write!(f, "order cannot exceed max lines"),
            DomainError::NonPositiveQuantity => write!(f, "quantity must be positive"),
            DomainError::NoLines => write!(f, "cannot confirm an order with no lines"),
        }
    }
}

#[derive(Debug, Clone)]
struct OrderLine {
    line_no: u32,
    product_id: String,
    quantity: u32,
    unit_price: Money,
}

impl OrderLine {
    fn line_total(&self) -> Money {
        Money { cents: self.unit_price.cents * self.quantity as i64, currency: self.unit_price.currency }
    }
}

const MAX_LINES: usize = 25;

struct Order {
    id: String,
    customer_id: String,
    lines: Vec<OrderLine>,
    confirmed: bool,
}

impl Order {
    fn new(id: &str, customer_id: &str) -> Self {
        Order { id: id.to_string(), customer_id: customer_id.to_string(), lines: Vec::new(), confirmed: false }
    }

    fn total(&self) -> Result<Money, DomainError> {
        let mut sum = Money { cents: 0, currency: "USD" };
        for line in &self.lines {
            sum = sum.add(line.line_total())?;
        }
        Ok(sum)
    }

    fn add_line(&mut self, product_id: &str, quantity: u32, unit_price: Money) -> Result<(), DomainError> {
        if self.confirmed {
            return Err(DomainError::OrderConfirmed);
        }
        if self.lines.len() >= MAX_LINES {
            return Err(DomainError::TooManyLines);
        }
        if quantity == 0 {
            return Err(DomainError::NonPositiveQuantity);
        }
        let line_no = self.lines.len() as u32 + 1;
        self.lines.push(OrderLine { line_no, product_id: product_id.to_string(), quantity, unit_price });
        Ok(())
    }

    fn confirm(&mut self) -> Result<(), DomainError> {
        if self.lines.is_empty() {
            return Err(DomainError::NoLines);
        }
        self.confirmed = true;
        Ok(())
    }
}

fn main() {
    let mut order = Order::new("ord-1", "cust-42");
    order.add_line("sku-1", 2, Money { cents: 500, currency: "USD" }).unwrap();
    order.add_line("sku-2", 1, Money { cents: 1200, currency: "USD" }).unwrap();
    println!("total cents before confirm {}", order.total().unwrap().cents);
    order.confirm().unwrap();

    match order.add_line("sku-3", 1, Money { cents: 100, currency: "USD" }) {
        Ok(_) => println!("unexpected success"),
        Err(e) => println!("rejected as expected {}", e),
    }
}
```
