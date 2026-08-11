---
name: Aggregate Root
slug: aggregate-root
family: 11-domain-driven-design
category: Domain-Driven Design
aliases: [Root Entity, Aggregate Boundary, Consistency Boundary]
first_described: "Evans 2003"
maturity: canonical
related: [entity, factory, repository, bounded-context, ubiquitous-language, domain-event]
incompatible_with: []
verified: 2026-08-02
---

# Aggregate Root

## 1. Name, aliases, and lineage

The canonical name is Aggregate Root. It was introduced by Eric Evans in
*Domain-Driven Design. Tackling Complexity in the Heart of Software*,
Addison-Wesley, 2003, Chapter 6, "The Life Cycle of a Domain Object", in the
section titled Aggregates. Evans defines an Aggregate as "a cluster of
associated objects that we treat as a unit for the purpose of data changes",
and the Aggregate Root as the single Entity inside that cluster that outside
objects are permitted to hold a reference to.

Martin Fowler's independent restatement in his bliki gives the same shape in
different words. "An aggregate will have one of its component objects be the
aggregate root", and "any references from outside the aggregate should only
go to the aggregate root", with the root left as the sole object responsible
for the whole cluster's consistency (Martin Fowler, "DDD_Aggregate," verified
2026-08-02, https://martinfowler.com/bliki/DDD_Aggregate.html). Fowler's page
is the most commonly linked secondary source for the pattern, and it is
careful to note that Evans's own writing on Aggregate is, in Fowler's words,
some of the hardest passage in the book to absorb on a first read, which is
one reason the pattern accumulates informal restatements the way Factory
Method or Observer do not.

Two aliases are in genuine circulation, and they name the same object from two
different angles. Root Entity describes what the object IS, an Entity per the
Entity pattern (see the related entry `entity.md` in this same family), that
happens to sit at the top of an Aggregate's internal object graph. Aggregate
Boundary, and its close cousin Consistency Boundary, describe what the object
DOES, it is the single gate through which every external access, mutation, and
transaction to the cluster passes. Vaughn Vernon, in *Implementing
Domain-Driven Design*, Addison-Wesley, 2013, Chapter 10, "Aggregates", uses
Consistency Boundary as the operative phrase throughout his four rules of
thumb for aggregate design, discussed under dimension 3 below, because for
Vernon the transactional guarantee is the entire reason the pattern exists,
not an incidental property of it.

A distinction worth making at the outset, because catalog summaries routinely
blur it. Aggregate is the name of the cluster, the group of Entities and Value
Objects that changes together. Aggregate Root is the name of the one Entity
inside that cluster that mediates every external interaction with it. A
codebase that has "an Aggregate" without a designated root has not applied the
pattern, it has merely drawn a boundary on a whiteboard. The root is not
optional set dressing, it is the mechanism that makes the boundary
enforceable in code rather than aspirational in documentation.

## 2. Problem and context

A domain model accumulates Entities and Value Objects that reference one
another. An `Order` has `OrderLine` items. A `Customer` has `Address` records
and open `Order` references. A `Playlist` has `Track` entries with per-track
metadata. Left alone, any part of an application that holds a reference to any
of these objects can walk the graph and mutate anything reachable from it,
because object references in most mainstream languages carry no notion of
"you may read this but you may not write to it from here".

The concrete failure this produces, seen repeatedly in codebases that grew
without a designated ownership boundary. A shipping module loads an `Order`
purely to read its destination address, and because `OrderLine` is a public,
independently addressable class, the shipping module also adds a discount
line directly to the order's line collection, bypassing whatever rule the
order's own logic would have applied to a discount, a minimum order total, a
one-discount-per-order limit, a recalculation of the order's total. Nothing
in the type system stops this. The order's invariant, "the total always
equals the sum of the lines minus any valid discount", silently breaks, and it
breaks in a part of the codebase nobody working on `Order` would think to
audit, because the mutation happened through a different entry point
entirely.

The same failure shows up at the transactional layer. Two different requests,
handled concurrently, each load a `BankAccount` aggregate and, without
realising it, also separately load and modify the same `AuditLog` record that
happens to be reachable from the account. Two unrelated business operations
now silently contend for one row that neither operation's author knew the
other was touching, because the object graph made the `AuditLog` reachable
from two directions with no rule stating it belongs to exactly one of them.

The context in which Aggregate Root becomes the right tool has three
recognisable ingredients, and all three should be present, not only one.

- The domain has one or more Entities whose fields must satisfy an invariant
  that spans more than one field or more than one child object, so a check
  performed only at the point of a single field write cannot be trusted to
  hold the invariant.
- The object graph is deep enough, an Entity referencing child Entities that
  reference further child Entities or Value Objects, that "anyone with a
  reference can mutate anything reachable from it" becomes a real risk rather
  than a theoretical one.
- The system persists this data transactionally, and the team needs a
  principled answer to the question "what is the smallest unit that must be
  loaded, locked, and saved together to keep the data consistent", because
  that question determines transaction scope, locking granularity, and
  eventual-consistency boundaries for the rest of the system's life.

## 3. Forces

**Consistency versus concurrency.** The tighter the consistency boundary, the
fewer operations two concurrent transactions can safely interleave without
conflict, and the coarser the lock, or the more frequent the optimistic
concurrency failure, on write. A single, large Aggregate that folds many
Entities under one root increases the invariants it can enforce in one
transaction, and reduces how many operations different users can perform on
related data at the same time. Vernon's rules of thumb (Vaughn Vernon,
"Effective Aggregate Design," discussed on InfoQ, verified 2026-08-02,
https://www.infoq.com/news/2014/12/aggregates-ddd) resolve this force
explicitly in favour of concurrency. "Design small aggregates, with a single
entity the smallest possible", and reserve a larger Aggregate only for the
Entities that genuinely must be consistent within the same transaction.

**Coupling versus navigability.** An Aggregate Root that forbids outside code
from holding a reference to its internal Entities is, by construction, less
convenient to query than a flat object graph where every Entity is directly
addressable. The force this trades away is developer convenience for a
guarantee, an external caller cannot accidentally corrupt internal state
because it literally cannot reach it without going through the root's public
methods, which is where the invariant checks live.

**Cost of enforcement versus cost of a subtle bug.** Enforcing the Aggregate
Root boundary correctly, refusing to return internal mutable collections,
refusing to accept a raw child Entity as a constructor argument from outside
the aggregate, costs upfront implementation effort in every language that
does not have a native access-control mechanism scoped to "objects reachable
only through this root". The alternative, an unenforced convention, costs
nothing to write and is the exact condition that produces the invariant
violation described in dimension 2, discovered weeks or months later by
someone debugging a total that does not add up.

**Team topology and cognitive load.** Vernon's rule "reference other
Aggregates only by identity" (same InfoQ source above) exists partly for a
concurrency reason and partly for a team-scaling reason. When Aggregate A
holds only the identifier of Aggregate B rather than a live object reference,
a team that owns B can change B's internal shape without breaking A's
compilation or A's runtime behaviour, so long as B's identifier type stays
stable. This decouples the release schedule of the two Aggregates' owning
teams, at the operational cost that A can no longer read a fresh value from B
without an explicit lookup, which is the same eventual-consistency trade the
pattern makes at the transaction level, now visible at the organisational
level.

**Operability.** A codebase organised around clear Aggregate boundaries has an
obvious answer to "what does this transaction touch, and what does it lock",
which is directly useful when diagnosing a deadlock, a lock-wait timeout, or a
hot row in production. A codebase without them has to reconstruct the answer
from the actual SQL or event log at incident time, which is strictly harder
under pressure.

## 4. Applicability and non-applicability

Reach for Aggregate Root when the domain has a genuine invariant that spans
more than one object and that invariant must never be observably violated,
even momentarily, within a single transaction. An `Order` whose total must
always equal the sum of its lines, a `BankAccount` whose balance must never go
negative under an overdraft rule, a `SeatingChart` where two bookings must
never claim the same seat, are all Entity clusters whose correctness genuinely
depends on being changed together, through one gate, that can check the whole
rule before committing. Reach for it, too, when persistence needs a
principled transaction and lock boundary and the team currently has none,
because the question "what is the unit of consistency" is going to be
answered one way or another, and answering it deliberately with a named
pattern is cheaper than answering it by accident with whatever the ORM's
default relationship-persistence behaviour happens to do.

Do NOT reach for Aggregate Root in these situations, each with its reason.

- **A single, standalone Entity with no invariant that spans other objects.**
  Wrapping a lone `User` Entity in an "aggregate" that consists only of itself
  adds a name and a mental model with no enforcement benefit over simply
  treating the Entity as an Entity. The pattern earns its keep specifically
  when there is a cluster to protect, not for every Entity a domain happens
  to have.
- **A purely read-oriented reporting or analytics model.** A denormalised
  view built to answer "total revenue by region this quarter" has no write
  invariant to protect, because it is never the target of a domain command.
  Applying Aggregate Root here forces read traffic through a write-side
  abstraction it does not need, and CQRS's read model, see the CQRS entry in
  this repository's application-architecture family, is the better fit.
- **Two objects that change together for convenience but have no
  transactional invariant linking them.** A `BlogPost` and its `Comment`
  entries are frequently modelled as separate Aggregates, each with its own
  identity and its own moderation lifecycle, precisely because a comment
  being added does not need to be atomic with the post's own edit history,
  and forcing them into one Aggregate would serialise every comment write
  against every post edit for no domain reason. Vernon's own worked
  example in *Implementing Domain-Driven Design*, Chapter 10, revisits
  exactly this shape, treating a large "everything an order touches"
  Aggregate as the anti-pattern the small-aggregate rule of thumb corrects.
- **A system where eventual consistency across the whole cluster is already
  acceptable and no synchronous rule needs to hold.** If "the customer's
  total lifetime spend" can lag reality by seconds without harm, computing it
  from a stream of domain events raised by many small Aggregates is a better
  fit than forcing every order-placing transaction to also update a running
  total field on a `Customer` Aggregate, which would serialise every order
  for a given customer against every other order for that same customer.
- **Anemic CRUD screens with no business rule at all**, where the "aggregate"
  would be a bare data holder with getters and setters and no invariant to
  protect. Applying the pattern here is cargo-culting DDD vocabulary onto
  code that is, correctly, only a database row wrapped in a class, and it
  adds ceremony that returns nothing.

## 5. Structure

- **Aggregate Root.** The single Entity inside the cluster that carries the
  cluster's own stable identity, the identity by which the outside world
  refers to the whole cluster. It owns every public method that can mutate
  any part of the cluster, and it is the only object in the cluster that a
  Repository, see the related Repository entry, is asked to load or save.
- **Internal Entity.** An Entity that lives inside the Aggregate but has no
  identity that matters outside it, an `OrderLine` whose identity is only
  "line 3 of order 482" and never independently addressed as "line 3" on its
  own. Internal Entities are reached only through the root's own methods,
  never handed out as a live, mutable reference to code outside the
  aggregate.
- **Value Object.** Any child object inside the cluster that has no identity
  of its own, compared purely by its field values, a `Money` amount, an
  `Address`, a `DateRange`. Value Objects are usually immutable and are
  freely shared, because sharing an immutable value carries none of the
  mutation risk that motivated the boundary in the first place.
- **Invariant.** The business rule the root exists to protect, expressed as a
  condition that must hold at the end of every public method call on the
  root, checked inside that method before the mutation is allowed to commit.
- **Identity.** The Aggregate Root's own identity is the only identity the
  outside world is permitted to hold a reference to. An external caller that
  wants to affect an internal Entity does so by calling a method on the root
  and passing that internal Entity's local identifier as an argument, never
  by obtaining a live reference to the internal Entity itself.
- **Repository, a collaborator, not part of the aggregate.** The persistence
  gateway responsible for loading a whole root, with its internal cluster
  attached, and for saving the whole cluster back atomically, in one
  transaction, whenever any part of it changed.
- **Domain Event, an optional collaborator.** A record the root raises when a
  notable state change occurs inside it, consumed asynchronously by
  other Aggregates or other Bounded Contexts, which is the mechanism Vernon's
  fourth rule of thumb, eventual consistency outside the boundary, relies on
  in practice.

## 6. ASCII structure diagram

```
                     +---------------------------+
   outside code ---->|      AGGREGATE ROOT        |
   (holds only        |  (has global identity:     |
   the root's id,      |   OrderId)                 |
   never a child       |                            |
   reference)          |  + placeOrder()            |
                        |  + addLine(sku, qty)       |
                        |  + applyDiscount(code)     |
                        |  + total(): Money          |
                        |  - checkInvariant()        |
                        +-------------+---------------+
                                      |
                       owns and enforces access to
                                      |
              +-----------------------+-----------------------+
              |                       |                       |
    +---------v---------+   +---------v---------+   +---------v---------+
    |  INTERNAL ENTITY    |   |  INTERNAL ENTITY    |   |   VALUE OBJECT      |
    |  OrderLine (local    |   |  OrderLine (local    |   |   Money             |
    |  id: "line-1", no     |   |  id: "line-2", no     |   |   (amount, currency)|
    |  meaning outside      |   |  meaning outside      |   |   compared by value |
    |  this Order)          |   |  this Order)          |   |                     |
    +-----------------------+   +-----------------------+   +---------------------+

    (unreachable directly)     (unreachable directly)      (freely shared, immutable)

    +---------------------------+          +----------------------------+
    | ANOTHER AGGREGATE ROOT     |          |         REPOSITORY          |
    | Customer                   |<---------+  loads/saves ONE root and   |
    | (Order references it by    | id only  |  its whole internal cluster |
    |  CustomerId, not by object) |          |  atomically, as one unit    |
    +-----------------------------+          +------------------------------+
```

## 7. Dynamics

```
   Client            OrderRepository         Order (Aggregate Root)      OrderLine
     |                     |                          |                     |
     | load(orderId)       |                          |                     |
     |-------------------->|                          |                     |
     |                     | SELECT order + all lines |                     |
     |                     | (one query or one         |                     |
     |                     |  transactional read set)  |                     |
     |                     |------------------------->  reconstructs the     |
     |                     |                            whole cluster in      |
     |                     |                            memory, root plus     |
     |                     |                            every internal        |
     |                     |                            Entity and Value      |
     |                     |                            Object it owns        |
     |                     |<-------------------------                       |
     |<--------------------|                          |                     |
     | order                |                          |                     |
     |                     |                          |                     |
     | order.addLine(sku, qty)                        |                     |
     |------------------------------------------------>|                     |
     |                     |                          | construct new        |
     |                     |                          | OrderLine ------------>
     |                     |                          |<-----------------------
     |                     |                          | checkInvariant()      |
     |                     |                          | (recompute total,     |
     |                     |                          |  compare against any  |
     |                     |                          |  rule, e.g. max lines) |
     |                     |                          |                     |
     |                     |                          | [invariant holds]    |
     |                     |                          | append to internal   |
     |                     |                          | lines collection      |
     |<------------------------------------------------|                     |
     | (call returns, order now reflects the new line) |                     |
     |                     |                          |                     |
     | save(order)          |                          |                     |
     |-------------------->|                          |                     |
     |                     | BEGIN TRANSACTION         |                     |
     |                     | write order row + write   |                     |
     |                     | every changed OrderLine   |                     |
     |                     | row, all as one unit       |                     |
     |                     | COMMIT                    |                     |
     |                     |<------------------------->|                     |
     |<--------------------|                          |                     |
```

The dynamics that matter are not the happy path shown above but the two
rejection paths it implies. If `checkInvariant()` fails, for example because
the order already has the maximum number of allowed lines, `addLine` raises a
domain-specific exception, or returns a Result-style failure value depending
on the language's idiom, and the internal lines collection is never mutated.
The cluster's in-memory state and its last-saved state remain identical,
there is no partial write to roll back, because nothing was written. If a
second concurrent client also calls `save(order)` on the same Aggregate after
loading an earlier version, the Repository's optimistic concurrency check, a
version column, a compare-and-swap on an aggregate version number, rejects
the second write outright, which is the mechanism that makes "the whole
Aggregate changes together, or not at all" true even under concurrency.

## 8. Implementation variants

**In-memory OO enforcement, the canonical shape.** The Aggregate Root class
exposes only behaviour-bearing public methods, `addLine`, `applyDiscount`,
`cancel`. Internal Entities and mutable collections are held as private
fields. Any method that would let outside code obtain a live, mutable
reference to an internal collection, `getLines()` returning the actual list,
is replaced with either a read-only snapshot, a `ReadonlyArray` in
TypeScript, an immutable `List` copy in Java, or a purpose-built accessor that
returns Value Objects rather than the internal Entities themselves. This is
the variant most directly matched to Evans's and Vernon's original prose, and
it is the one shown in the code examples in this entry.

**Event-sourced aggregate.** Instead of persisting current field state, the
root persists the sequence of Domain Events it has raised, and its current
state is a fold, replaying every past event through an `apply` function, over
that sequence. The command-handling method still performs the same
invariant check as the in-memory variant, but on success it produces and
appends an event, `LineAdded`, `DiscountApplied`, rather than mutating a
field directly, and a separate `apply(event)` method, used identically for
"replay from history" and "apply the decision already made", performs the actual
field mutation. Axon Framework's `@EventSourcingHandler` methods are exactly
this second function, kept syntactically separate from the `@CommandHandler`
methods that perform the invariant check (AxonIQ, "Multi-Entity Aggregates,"
verified 2026-08-02, https://docs.axoniq.io/axon-framework-reference/4.13/axon-framework-commands/modeling/multi-entity-aggregates/).
This variant makes the Aggregate's history a first-class, auditable artefact,
at the cost of needing an explicit event-replay or snapshotting strategy once
an Aggregate accumulates a long event history.

**Marker-interface aggregate, annotation-driven persistence frameworks.**
In frameworks where the persistence layer needs a cheap, reflectable way to
recognise "this class is a consistency boundary, treat it as the unit of
save", the root is decorated with an empty marker interface or attribute
rather than given distinct base-class behaviour. Microsoft's
`eShopOnContainers` reference architecture uses exactly this shape, an empty
`IAggregateRoot` interface applied to the root class of each of the order
and buyer aggregates, used purely to signal intent to the repository layer
and to reviewers, with no methods of its own (Microsoft, "Applying CQRS and
CQS approaches in a DDD microservice in eShopOnContainers," verified
2026-08-02, https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/microservice-domain-model).
This variant costs almost nothing to add and gives no runtime enforcement on
its own, it depends entirely on discipline elsewhere in the class, private
setters, no public collection exposure, to actually protect the boundary.

**Repository-mediated aggregate, framework-inferred root.** Spring Data
takes the position that "domain types" handed to a repository interface are,
by definition, aggregates, and it does not require any marker at all, the
type parameter of `CrudRepository<T, ID>` or `JpaRepository<T, ID>` simply
IS the Aggregate Root as far as the framework's persistence machinery is
concerned. "Spring Data considers domain types to be entities, more
specifically aggregates" (Spring Data, "Repositories, Core Concepts,"
verified 2026-08-02,
https://docs.spring.io/spring-data/commons/reference/repositories/core-concepts.html).
This variant is the lightest to adopt, one repository interface per
Aggregate type, but it leans on the developer never accidentally creating a
second repository interface for an internal Entity, which would silently
reintroduce a second, unprotected entry point into the cluster.

**Language-idiomatic module boundary, no OO base class at all.** In
languages without pervasive class-based encapsulation as the default,
Rust and Go both shown in this entry's code examples, the root is expressed
as a struct exposed from a module or package, with the module's own
visibility rules, Rust's `pub`/private field visibility, Go's lowercase
unexported field convention, doing the same job that private fields and
public methods do in the class-based variant. There is no ceremonial base
class or interface, the boundary is simply "which fields and types this
module chooses to export", and the invariant check lives inside the one
exported constructor and mutator functions, exactly as it does in the
class-based shape.

## 9. Known production uses

- **Spring Data, part of the Spring Data Commons project under the Spring
  Framework umbrella.** The repository abstraction that underlies Spring
  Data JPA, Spring Data MongoDB, and the rest of the Spring Data family is
  explicitly described by its own reference documentation as operating on
  aggregates, with the type parameter of every repository interface being
  treated as an Aggregate Root. "We consider domain objects in the sense of
  DDD" and "Spring Data considers domain types to be entities, more
  specifically aggregates" (Spring Data, "Repositories, Core Concepts,"
  verified 2026-08-02,
  https://docs.spring.io/spring-data/commons/reference/repositories/core-concepts.html).
- **Axon Framework**, a Java framework for building event-sourced,
  CQRS-oriented applications, structures every write-side command handler
  around an explicit Aggregate. Its `@AggregateRoot`, formerly
  `@Aggregate`, annotation designates the root class, `@AggregateIdentifier`
  designates its stable identity, and `@EntityId` plus `@AggregateMember`
  route commands to the correct internal Entity within the cluster while
  keeping the rule "each command must have exactly one handler in the
  aggregate" (AxonIQ, "Multi-Entity Aggregates," Axon Framework Reference
  4.13, verified 2026-08-02,
  https://docs.axoniq.io/axon-framework-reference/4.13/axon-framework-commands/modeling/multi-entity-aggregates/).
- **Microsoft's eShopOnContainers reference microservices architecture**,
  published as part of Microsoft's official .NET microservices guidance,
  models its Ordering domain around an `Order` Aggregate and a `Buyer`
  Aggregate, each decorated with an `IAggregateRoot` marker interface, and
  states directly that "aggregate roots are the main consistency boundaries
  in DDD" and that "for each aggregate or aggregate root, you should create
  one repository class" (Microsoft, "Applying CQRS and CQS approaches in a
  DDD microservice in eShopOnContainers," and "Designing a microservice
  domain model," verified 2026-08-02,
  https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/microservice-domain-model).

Vaughn Vernon's *Implementing Domain-Driven Design*, Addison-Wesley, 2013,
Chapter 10, is the most frequently cited practitioner-level source for the
pattern's design rules rather than a single named production system, and its
four rules of thumb, discussed in dimension 3 above, are widely reproduced in
industry conference talks and framework documentation as the de facto design
checklist for sizing an Aggregate correctly.

## 10. Consequences

**Positive.**

- Every write path to the cluster's internal state passes through one place,
  which is the single location where an invariant that spans multiple fields
  or multiple child objects can be checked before a mutation is allowed to
  commit, closing off the "mutated through a side door" failure described in
  dimension 2.
- The Aggregate gives a principled, unambiguous answer to "what is the unit
  of transactional consistency and the unit of database locking", which
  removes an entire category of ad hoc decision-making from the persistence
  layer and from incident response.
- Because outside code holds the root's identity rather than a live
  reference to internal Entities, the internal shape of the Aggregate can be
  refactored, splitting one internal Entity into two, renaming a field,
  without breaking any code outside the Aggregate, so long as the root's
  public method signatures stay stable. This is the same encapsulation
  benefit object orientation promises in general, made concrete and
  enforced specifically at the persistence and domain-invariant boundary.
- The pattern composes cleanly with Domain Events, `applyDiscount` raising a
  `DiscountApplied` event, to propagate state to other Aggregates
  asynchronously, which lets the system keep small, fast, independently
  lockable Aggregates while still eventually reflecting cross-Aggregate
  effects, resolving the concurrency-versus-consistency force from dimension
  3 in favour of concurrency by default.

**Negative.**

- A poorly sized Aggregate, one drawn too large because "these things feel
  related" rather than because a genuine invariant requires them to change
  together, directly reproduces the concurrency cost described in dimension
  3, unrelated operations on unrelated parts of the cluster now contend for
  the same lock or the same optimistic-concurrency version number for no
  domain reason.
- Enforcing the boundary correctly, no leaking internal collections, no
  accepting raw internal Entities as external constructor arguments, is
  manual discipline in most mainstream languages. Nothing in Java, C#,
  TypeScript, or Python stops a developer from adding a `getLines(): OrderLine[]`
  method that returns the live internal list, silently reopening the exact
  side door the pattern exists to close, and no compiler error will flag it.
- Cross-Aggregate invariants, "the sum of every open order for this customer
  must never exceed their credit limit", cannot be enforced synchronously
  inside a single Aggregate by construction, because the pattern's own rule
  says an Aggregate should reference other Aggregates only by identity, not
  by live reference. Teams that need such an invariant must either
  redesign the boundary, fold both into one Aggregate, at the concurrency
  cost described above, or accept a window of eventual inconsistency,
  neither of which is free.
- Persisting an entire Aggregate atomically on every save, the transactional
  guarantee that makes the pattern useful in the first place, can become an
  I/O and lock-contention cost of its own once an Aggregate's internal
  collection grows large, an `Order` with ten thousand historical line items
  being re-read and potentially re-locked on every single-field update is a
  documented real-world scaling failure mode of the pattern, not a
  hypothetical one.

## 11. Failure modes and misuse

**Symptom.** A business invariant that "always held" in code review starts
silently failing in production, a total that does not match its line items,
a balance that goes negative despite an explicit non-negative check
elsewhere in the codebase.
**Cause.** The Aggregate Root exposes a public getter or public field that
returns the internal, mutable collection or a mutable child Entity directly,
`order.lines` returning the live `List<OrderLine>` rather than a read-only
copy or a Value Object projection. Any caller holding that reference can
mutate it without ever calling a method the root's invariant check guards.
**Fix.** Return an immutable snapshot, a `ReadonlyArray` in TypeScript, an
unmodifiable view or defensive copy in Java, a copied slice in Go, from any
accessor that exposes internal state, and route every mutation exclusively
through named, behaviour-bearing methods on the root that re-check the
invariant before committing.

**Symptom.** Two Aggregates, `Order` and `Customer`, cannot be compiled,
serialised, or tested independently, changing `Customer`'s internal shape
breaks `Order`'s build even though no business rule links the two at the
field level.
**Cause.** One Aggregate holds a live, in-memory object reference to another
Aggregate's root, `order.customer` typed as `Customer`, rather than holding
only that Aggregate's stable identity, `order.customerId` typed as
`CustomerId`. This directly violates Vernon's third rule of thumb,
"reference other Aggregates only by identity" (Vaughn Vernon, "Effective
Aggregate Design," discussed on InfoQ, verified 2026-08-02,
https://www.infoq.com/news/2014/12/aggregates-ddd).
**Fix.** Replace the live reference with the referenced Aggregate's
identifier type, and resolve the actual object, when one is genuinely
needed, through an explicit Repository or an application-service-level
lookup at the point of use, not as a field baked into the referencing
Aggregate's own persisted shape.

**Symptom.** A single Aggregate has grown to hold hundreds or thousands of
internal Entities, ten thousand `OrderLine` rows on one `Order`, and the
system exhibits growing save latency and lock-wait timeouts specifically on
that Aggregate type as the dataset ages, even though no individual save
touches more than a handful of the internal rows.
**Cause.** The Aggregate boundary was drawn around "everything that is
conceptually part of an order over its whole lifetime" rather than around
"the smallest cluster that must be transactionally consistent for any single
business operation". Every save re-persists, or at minimum re-locks or
re-versions, the whole oversized cluster, which is Vernon's second rule of
thumb, "design small aggregates", being violated in the direction that
causes the concurrency force from dimension 3 to bite hardest.
**Fix.** Split the Aggregate along a genuine transactional seam, for
example separating "the live, still-editable order" from "the immutable,
append-only shipment history of that order" into two Aggregates connected
by identity and Domain Events rather than by shared internal state, so that
routine operations on the live part never need to touch the historical
part.

**Symptom.** Two concurrent requests both report success, but the resulting
persisted state violates an invariant that either request, run alone, would
have correctly enforced, for example a seat gets double-booked even though
each request individually checked "is this seat free" before booking it.
**Cause.** The invariant check and the corresponding write are not performed
atomically against a stable, versioned read of the whole Aggregate. Either
the Repository does not implement optimistic concurrency, no version column,
no compare-and-swap on save, or the check-then-act sequence spans more than
one transaction, giving a second request the chance to interleave between
the check and the write.
**Fix.** Load the Aggregate and perform the invariant check and the
resulting mutation within a single transaction guarded by an explicit
concurrency token, and treat a version conflict on save as a first-class
failure the caller must retry against a freshly loaded Aggregate, never as
an error to be silently swallowed or logged and ignored.

## 12. Trade-off matrix

| Force | Aggregate Root | Anemic Entity plus Service-layer rules | Database constraints, CHECK, FOREIGN KEY, triggers | CRDT, conflict-free replicated data type |
|---|---|---|---|---|
| Where the invariant lives | Inside the domain model, in the language the domain speaks | In a Service class, separate from the data it governs | In the schema, expressed in SQL, not domain vocabulary | By construction of the merge function, not an explicit check |
| Enforced on every write path, including bypassing code | Yes, by construction, if internal state is never leaked | No, any code that skips the Service can violate the rule | Yes, the database itself refuses the write | Yes, but only for invariants the CRDT's algebra can express |
| Concurrency model | Single-writer transaction per Aggregate instance, explicit locking or optimistic versioning | Whatever the Service layer's transaction scope happens to be | Row and constraint-level locking, database-managed | Multi-writer, no locking, convergence instead of exclusion |
| Cross-node or offline writes | Requires a synchronous connection to the transaction's data store | Same as Aggregate Root | Same as Aggregate Root | Native strength, this is the pattern's reason to exist |
| Cost to add a new invariant | A new check inside an existing root method, usually small | A new conditional in a Service method, easy to forget to call from every path | A migration, and possibly a rewrite of the triggers | Requires the invariant to be re-expressed as a monotonic merge rule, often impossible |
| Readability for a domain expert | High, method names read as business operations | Medium, logic is split between the anemic model and the Service | Low, SQL is not the language the business speaks | Low, requires understanding the CRDT's mathematics |

The Aggregate Root is the right default when the invariant is expressible as
true or false at the end of one transaction, the domain expert can name it
in business terms, and the system has a single authoritative data store for
that Aggregate at write time. Database constraints remain the correct
backstop even when Aggregate Root is used, they catch the case where a bug
bypasses the domain model entirely, for example a direct SQL fix run by an
operator. CRDTs are the correct choice only when the invariant genuinely
survives being weakened to eventually converges, which most business
invariants, an order total, a non-negative balance, an exclusive seat
assignment, do not.

## 13. Related and incompatible patterns

**Entity.** The Aggregate Root IS an Entity, specifically the one Entity in
the cluster whose identity the outside world is permitted to hold. Every
property that defines Entity, identity that persists across state changes,
identity-based rather than value-based equality, applies to the root, and
the related Entity entry in this same family (`entity.md`) covers that
foundation directly. An Aggregate without a root that satisfies Entity's own
contract is not correctly formed.

**Factory.** Constructing a new Aggregate, especially one whose invariants
must hold from the very first moment it exists, is frequently delegated to a
Factory rather than performed by a bare constructor, so that "an
incompletely valid Aggregate temporarily exists" is never a state the rest
of the codebase can observe. Evans's own text pairs Aggregate directly with
Factory and Repository as the three patterns governing a domain object's
life cycle, and the two are commonly implemented together, a static factory
method on the Aggregate Root class itself, or a dedicated Factory type for
Aggregates whose construction genuinely requires external collaborators.

**Repository.** The Repository is the persistence-facing collaborator that
loads and saves an Aggregate as a single, atomic unit. The rule "one
Repository per Aggregate Root, never a Repository for an internal Entity" is
one of the most consistently repeated corollaries of the pattern across
every production framework surveyed in dimension 9, and violating it, adding
a Repository that can independently load or save an internal `OrderLine`,
reopens the exact side-door problem the Aggregate exists to close.

**Domain Event.** The mechanism by which an Aggregate communicates a
notable state change to the rest of the system without giving other
Aggregates a live reference into itself. Domain Events are how the "use
eventual consistency outside the boundary" rule of thumb from dimension 3 is
implemented in practice, an `Order` Aggregate raises `OrderPlaced`, and a
separate `Inventory` Aggregate, in its own transaction, consumes that event
to decrement stock, rather than the `Order` Aggregate reaching directly into
`Inventory`'s internal state.

**Bounded Context.** Aggregate is a within-Bounded-Context pattern. Two
Bounded Contexts may model the same real-world concept, a customer, as two
entirely different Aggregates with different shapes and different invariants,
each valid within its own context, and the Bounded Context boundary is what
makes that difference legitimate rather than a modelling error, as covered in
this repository's `bounded-context.md` entry.

**Incompatible or in tension with CRDTs and multi-master replication.**
Aggregate Root's core guarantee, a synchronous, single-writer invariant check
that must hold at the end of every transaction, sits in direct tension with
a multi-master, offline-first system where two replicas can accept
conflicting writes and must later merge without a central arbiter. This is
not a defect in either pattern, it reflects a genuine, named force in
dimension 3 and the trade-off matrix in dimension 12, and a system that needs
both, strong invariants on some data and offline multi-writer availability
on other data, usually applies Aggregate Root to the former and a CRDT or
similar convergence structure to the latter, rather than forcing one pattern
to cover both.

## 14. Refactoring path in and out

**Introducing an Aggregate Root into code that lacks one.** Start by
identifying the invariant that is currently unenforced or enforced only
inconsistently, the exact symptom is usually a bug report where a total, a
balance, or a count is observed to be wrong despite every individual field
write looking correct in isolation. Identify every Entity and Value Object
that must be read together to check that invariant, that set is the
candidate Aggregate's internal cluster. Pick the one Entity among them that
already carries, or naturally should carry, the stable identity by which the
outside world refers to the whole cluster, and designate it the root. Then,
incrementally, replace every external accessor that currently returns a
live, mutable reference into the cluster with either a read-only projection
or a removal of that accessor entirely, redirecting every caller that used
it to mutate state through a new, named method on the root instead, each new
method re-checking the invariant before it commits. This step is
frequently the largest one, because it requires finding every existing call
site that was reaching into the cluster directly, which is exactly the class
of call site the pattern is designed to make impossible going forward.
Finally, consolidate persistence, so exactly one Repository loads and saves
the whole cluster atomically, and remove any Repository or direct
data-access code that was independently loading or saving an internal
Entity on its own.

**Removing or splitting an Aggregate Root that has stopped earning its
place.** The signal that an Aggregate should shrink is the second failure
mode in dimension 11, save latency or lock contention growing specifically
on that Aggregate as its internal cluster grows, combined with evidence that
most individual operations on it only ever touch a small, stable subset of
that cluster. Identify a genuine transactional seam inside the existing
cluster, a subset of the internal Entities whose invariant does not
actually depend on the rest of the cluster's current state at the moment of
the operation. Introduce a new Aggregate Root for that subset, give it its
own stable identity, and replace the old cluster's live internal reference
to that subset with the new Aggregate's identifier plus, where the two
genuinely need to stay informed of each other, a Domain Event flowing
between them. This is the direct converse of the introduction path, and the
two together describe Aggregate Root as a boundary whose correct size is
revisited over the system's life, not chosen once and fixed forever, which
is exactly the position Vernon's rules of thumb, start small, grow only
when a genuine transactional invariant demands it, take throughout Chapter
10 of *Implementing Domain-Driven Design*.

## 15. Testing and verification

An Aggregate Root, correctly formed, is unusually easy to unit test compared
to code that spreads the same invariant across a Service layer and several
independently addressable Entities, because the entire invariant lives
inside one class with no external collaborators required to exercise it. The
standard test shape is Given-When-Then applied directly to the root, given
an Aggregate constructed in a known starting state, when a public method is
called with a specific argument, then either the invariant-satisfying state
change is observable through the root's own read methods, or, for a call
that should be rejected, the expected domain-specific exception or failure
result is returned and the internal state is provably unchanged, verified
by asserting the root's observable state is bit-for-bit identical to what it
was before the rejected call.

What becomes harder to test, deliberately, is anything that tries to
construct an Aggregate in an intermediate, invariant-violating state purely
to see what the rest of the system does with it, because a correctly
enforced Aggregate Root makes that state unreachable from outside the class
entirely. A test that resorts to reflection, an internal test-only
constructor, or a mocking framework's ability to bypass encapsulation to
force such a state into existence is a sign the test is fighting the
pattern rather than exercising it, and it is usually evidence that the
invariant under test genuinely belongs somewhere else, or that the specific
scenario being tested is not actually reachable in production and does not
need a test at all.

For the event-sourced variant described in dimension 8, an additional test
shape is required and is worth calling out on its own. Given a specific
sequence of past events, when the `apply` function replays them in order,
then the resulting in-memory state must match hand-computed expectations,
tested entirely independently of any command-handling logic. This isolates
"does replay reconstruct state correctly" from "does the command handler
make the right decision given that state", which are two genuinely separate
concerns that a naive test suite for an event-sourced Aggregate frequently
conflates into one large, harder-to-diagnose test.

Cross-Aggregate behaviour, "when `Order` raises `OrderPlaced`, does
`Inventory` correctly decrement stock", should be tested as an integration
test spanning the event bus, not folded into either Aggregate's own unit
test suite, because doing so would reintroduce a compile-time or test-time
coupling between two Aggregates that the pattern is explicitly designed to
avoid at the production code level.

## 16. Observability signals

A well-instrumented Aggregate Root emits, at minimum, one event or log line
per successful state-changing method call, named after the business
operation rather than the technical field mutation, `OrderLineAdded` rather
than `FieldUpdated`, because the whole value of the pattern is that its
public methods already speak the domain's vocabulary, and observability
should inherit that vocabulary rather than flatten it back down to generic
CRUD terms.

The signal most specific to this pattern, and the one worth building a
dedicated dashboard for once an Aggregate is under real production load, is
save conflict rate, the fraction of save attempts on a given Aggregate
type that fail the Repository's optimistic concurrency check because
another writer committed first. A healthy Aggregate, correctly sized per
Vernon's rules of thumb, shows a save-conflict rate near zero under normal
load, because unrelated operations rarely target the same Aggregate
instance concurrently. A rising save-conflict rate on one specific Aggregate
type, especially one that correlates with a specific instance identifier
being hit repeatedly, is close to a direct production readout of the third
failure mode described in dimension 11, an Aggregate whose boundary was
drawn too large or that has become an accidental hotspot.

A second useful signal is cluster size at load time, the number of
internal Entities returned per single load of a given Aggregate type,
tracked as a distribution rather than a single number, because a distribution
whose tail keeps growing month over month, one `Order` accumulating ten
thousand `OrderLine` rows over its lifetime, is the leading indicator of the
second failure mode described in dimension 11 well before it manifests as an
observable latency regression.

Domain Events raised by an Aggregate are, separately from any generic
logging, the audit trail for the Aggregate's own history, and persisting
them, whether or not the Aggregate itself is event-sourced, gives an
operator a business-readable answer to "what happened to this specific
order over its lifetime" that a raw field-level change log never provides
on its own.

## 17. Security and privacy implications

The Aggregate Root's access-control boundary and a system's actual
authorization boundary are frequently, and incorrectly, treated as the same
thing. The pattern guarantees that a caller who is permitted to invoke a
method on the root cannot bypass that method to reach internal state
directly, but it says nothing at all about which callers should be permitted
to invoke the method in the first place. A codebase that relies on "you can
only reach an `OrderLine` through the `Order` root" as its sole defence
against, for example, one tenant in a multi-tenant system reading another
tenant's order, has confused an encapsulation boundary with a tenancy
boundary, and the Repository's own load method, `orderRepository.load(orderId)`,
must independently check the caller is authorized to load that specific
`orderId` before it ever hands the root back, because the Aggregate Root
pattern itself supplies no such check.

Because a Repository loads a root's entire internal cluster on read by
construction, an Aggregate that mixes low-sensitivity and high-sensitivity
data in the same cluster, order line items alongside a customer's stored
payment token, for example, means that every operation touching the order
also brings the payment token into memory, widening the blast radius of any
logging, error-reporting, or debugging tool that happens to serialise the
in-memory Aggregate for inspection. Where GDPR- or PCI-relevant data is
involved, this is a genuine argument for splitting an Aggregate along a
sensitivity boundary even when a naive read of the transactional invariants
alone would keep the data together, deliberately trading a small amount of
transactional convenience for a materially smaller default exposure surface.

The Aggregate Root's invariant checks are frequently the last line of
defence against a class of application-level integrity attack that
input validation at the API boundary alone cannot catch, for example a
crafted sequence of otherwise individually valid API calls that, interleaved
in a specific order, would drive a balance negative or a seat into a
double-booked state if the invariant were checked only at the API layer
rather than re-verified, transactionally, inside the Aggregate on every
single mutating call. This is the security-relevant restatement of the
consistency force from dimension 3, an invariant checked only at the edge
of the system is a suggestion, an invariant checked inside the transactional
boundary on every write is an actual guarantee.

## 18. References

1. Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*, Addison-Wesley, 2003, Chapter 6, "The Life Cycle of a Domain
   Object", section Aggregates. Original source for the Aggregate and
   Aggregate Root definitions and the pairing of Aggregate with Factory and
   Repository.
2. Vaughn Vernon, *Implementing Domain-Driven Design*, Addison-Wesley, 2013,
   Chapter 10, "Aggregates". Source for the Consistency Boundary framing and
   the worked example of over-large versus correctly sized aggregates
   referenced in dimension 4.
3. Martin Fowler, "DDD_Aggregate," verified 2026-08-02,
   https://martinfowler.com/bliki/DDD_Aggregate.html. Source for the
   restated definition and the external-reference-to-root-only rule quoted
   in dimensions 1 and 5.
4. Vaughn Vernon, "Effective Aggregate Design," summarised on InfoQ,
   verified 2026-08-02, https://www.infoq.com/news/2014/12/aggregates-ddd.
   Source for the four rules of thumb quoted directly in dimensions 3, 11,
   and 14.
5. Spring Data, "Repositories, Core Concepts," Spring Data Commons reference
   documentation, verified 2026-08-02,
   https://docs.spring.io/spring-data/commons/reference/repositories/core-concepts.html.
   Source for the Spring Data production use in dimensions 8 and 9.
6. AxonIQ, "Multi-Entity Aggregates," Axon Framework Reference 4.13,
   verified 2026-08-02,
   https://docs.axoniq.io/axon-framework-reference/4.13/axon-framework-commands/modeling/multi-entity-aggregates/.
   Source for the Axon Framework production use, the `@EntityId` and
   `@AggregateMember` command-routing model, and the single-handler-per-
   command rule in dimensions 8 and 9.
7. Microsoft, "Applying CQRS and CQS approaches in a DDD microservice in
   eShopOnContainers," and "Designing a microservice domain model," .NET
   Microservices Architecture guidance, verified 2026-08-02,
   https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/microservice-domain-model.
   Source for the eShopOnContainers `IAggregateRoot` marker-interface
   production use in dimensions 8 and 9.

## Code examples

Four languages are shown, chosen because each represents a genuinely
different implementation variant from dimension 8. TypeScript for the
canonical class-based, private-field variant, Python for the same shape with
its own idiomatic dataclass constraints, Go for the module-boundary variant
with no class-based access control at all, and Rust for the same
module-boundary variant with the compiler enforcing field privacy at the
crate boundary rather than by convention. All four were compiled or run
without error.

### TypeScript

```typescript
type Money = { amountCents: number; currency: "EUR" };

function addMoney(a: Money, b: Money): Money {
  if (a.currency !== b.currency) {
    throw new Error("currency mismatch");
  }
  return { amountCents: a.amountCents + b.amountCents, currency: a.currency };
}

class OrderLine {
  readonly id: string;
  private readonly unitPrice: Money;
  private quantity: number;

  constructor(id: string, unitPrice: Money, quantity: number) {
    this.id = id;
    this.unitPrice = unitPrice;
    this.quantity = quantity;
  }

  lineTotal(): Money {
    return { amountCents: this.unitPrice.amountCents * this.quantity, currency: this.unitPrice.currency };
  }
}

export class OrderRejected extends Error {}

export class Order {
  private readonly id: string;
  private readonly lines: OrderLine[] = [];
  private static readonly MAX_LINES = 50;

  private constructor(id: string) {
    this.id = id;
  }

  static place(id: string): Order {
    return new Order(id);
  }

  addLine(lineId: string, unitPrice: Money, quantity: number): void {
    if (quantity <= 0) {
      throw new OrderRejected("quantity must be positive");
    }
    if (this.lines.length >= Order.MAX_LINES) {
      throw new OrderRejected("order line limit reached");
    }
    this.lines.push(new OrderLine(lineId, unitPrice, quantity));
  }

  total(): Money {
    return this.lines.reduce(
      (sum, line) => addMoney(sum, line.lineTotal()),
      { amountCents: 0, currency: "EUR" } as Money,
    );
  }

  lineCount(): number {
    return this.lines.length;
  }
}

const order = Order.place("order-482");
order.addLine("line-1", { amountCents: 1500, currency: "EUR" }, 2);
order.addLine("line-2", { amountCents: 700, currency: "EUR" }, 3);
console.log(order.total(), order.lineCount());

try {
  order.addLine("line-3", { amountCents: 100, currency: "EUR" }, -1);
} catch (e) {
  console.log("rejected", (e as Error).message);
}
```

### Python

```python
from __future__ import annotations
from dataclasses import dataclass


class OrderRejected(Exception):
    pass


@dataclass(frozen=True)
class Money:
    amount_cents: int
    currency: str = "EUR"

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise OrderRejected("currency mismatch")
        return Money(self.amount_cents + other.amount_cents, self.currency)


class _OrderLine:
    def __init__(self, line_id: str, unit_price: Money, quantity: int) -> None:
        self._id = line_id
        self._unit_price = unit_price
        self._quantity = quantity

    def line_total(self) -> Money:
        return Money(self._unit_price.amount_cents * self._quantity, self._unit_price.currency)


class Order:
    _MAX_LINES = 50

    def __init__(self, order_id: str) -> None:
        self._id = order_id
        self._lines: list[_OrderLine] = []

    def add_line(self, line_id: str, unit_price: Money, quantity: int) -> None:
        if quantity <= 0:
            raise OrderRejected("quantity must be positive")
        if len(self._lines) >= self._MAX_LINES:
            raise OrderRejected("order line limit reached")
        self._lines.append(_OrderLine(line_id, unit_price, quantity))

    def total(self) -> Money:
        running = Money(0)
        for line in self._lines:
            running = running + line.line_total()
        return running

    def line_count(self) -> int:
        return len(self._lines)


if __name__ == "__main__":
    order = Order("order-482")
    order.add_line("line-1", Money(1500), 2)
    order.add_line("line-2", Money(700), 3)
    print(order.total(), order.line_count())

    try:
        order.add_line("line-3", Money(100), -1)
    except OrderRejected as exc:
        print("rejected", exc)
```

### Go

```go
package main

import "fmt"

type Money struct {
	AmountCents int
	Currency    string
}

func (m Money) add(other Money) (Money, error) {
	if m.Currency != other.Currency {
		return Money{}, fmt.Errorf("currency mismatch")
	}
	return Money{AmountCents: m.AmountCents + other.AmountCents, Currency: m.Currency}, nil
}

type orderLine struct {
	id        string
	unitPrice Money
	quantity  int
}

func (l orderLine) lineTotal() Money {
	return Money{AmountCents: l.unitPrice.AmountCents * l.quantity, Currency: l.unitPrice.Currency}
}

const maxLines = 50

// Order is the Aggregate Root. Its fields are unexported, so no package
// outside this file can construct or mutate an Order except through the
// methods below.
type Order struct {
	id    string
	lines []orderLine
}

func PlaceOrder(id string) *Order {
	return &Order{id: id}
}

func (o *Order) AddLine(lineID string, unitPrice Money, quantity int) error {
	if quantity <= 0 {
		return fmt.Errorf("quantity must be positive")
	}
	if len(o.lines) >= maxLines {
		return fmt.Errorf("order line limit reached")
	}
	o.lines = append(o.lines, orderLine{id: lineID, unitPrice: unitPrice, quantity: quantity})
	return nil
}

func (o *Order) Total() (Money, error) {
	running := Money{Currency: "EUR"}
	var err error
	for _, line := range o.lines {
		running, err = running.add(line.lineTotal())
		if err != nil {
			return Money{}, err
		}
	}
	return running, nil
}

func (o *Order) LineCount() int {
	return len(o.lines)
}

func main() {
	order := PlaceOrder("order-482")
	if err := order.AddLine("line-1", Money{AmountCents: 1500, Currency: "EUR"}, 2); err != nil {
		panic(err)
	}
	if err := order.AddLine("line-2", Money{AmountCents: 700, Currency: "EUR"}, 3); err != nil {
		panic(err)
	}
	total, _ := order.Total()
	fmt.Println(total, order.LineCount())

	if err := order.AddLine("line-3", Money{AmountCents: 100, Currency: "EUR"}, -1); err != nil {
		fmt.Println("rejected", err)
	}
}
```

### Rust

```rust
#[derive(Clone, Copy, Debug, PartialEq)]
struct Money {
    amount_cents: i64,
    currency: &'static str,
}

impl Money {
    fn add(self, other: Money) -> Result<Money, String> {
        if self.currency != other.currency {
            return Err("currency mismatch".to_string());
        }
        Ok(Money {
            amount_cents: self.amount_cents + other.amount_cents,
            currency: self.currency,
        })
    }
}

struct OrderLine {
    id: String,
    unit_price: Money,
    quantity: i64,
}

impl OrderLine {
    fn line_total(&self) -> Money {
        Money {
            amount_cents: self.unit_price.amount_cents * self.quantity,
            currency: self.unit_price.currency,
        }
    }
}

const MAX_LINES: usize = 50;

// Order is the Aggregate Root. Its fields are private to this module, so
// only the methods below can construct or mutate an Order.
struct Order {
    id: String,
    lines: Vec<OrderLine>,
}

impl Order {
    fn place(id: &str) -> Order {
        Order { id: id.to_string(), lines: Vec::new() }
    }

    fn add_line(&mut self, line_id: &str, unit_price: Money, quantity: i64) -> Result<(), String> {
        if quantity <= 0 {
            return Err("quantity must be positive".to_string());
        }
        if self.lines.len() >= MAX_LINES {
            return Err("order line limit reached".to_string());
        }
        self.lines.push(OrderLine { id: line_id.to_string(), unit_price, quantity });
        Ok(())
    }

    fn total(&self) -> Result<Money, String> {
        let mut running = Money { amount_cents: 0, currency: "EUR" };
        for line in &self.lines {
            running = running.add(line.line_total())?;
        }
        Ok(running)
    }

    fn line_count(&self) -> usize {
        self.lines.len()
    }
}

fn main() {
    let mut order = Order::place("order-482");
    order
        .add_line("line-1", Money { amount_cents: 1500, currency: "EUR" }, 2)
        .expect("valid line");
    order
        .add_line("line-2", Money { amount_cents: 700, currency: "EUR" }, 3)
        .expect("valid line");
    println!("{:?} {}", order.total().unwrap(), order.line_count());

    match order.add_line("line-3", Money { amount_cents: 100, currency: "EUR" }, -1) {
        Ok(_) => println!("unexpected success"),
        Err(e) => println!("rejected {}", e),
    }
}
```
