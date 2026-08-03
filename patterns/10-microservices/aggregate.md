---
name: Aggregate
slug: aggregate
family: 10-microservices
category: Domain Modeling
aliases: [Aggregate Root, DDD Aggregate, Consistency Boundary, Transactional Boundary]
first_described: "Evans 2003, tactical pattern chapter; formalized for microservice boundaries by Richardson 2018"
maturity: canonical
related: [decompose-by-subdomain, saga, cqrs, event-sourcing, database-per-service, repository, optimistic-offline-lock, domain-event]
incompatible_with: [shared-database]
verified: 2026-08-03
---

# Aggregate

## 1. Name, aliases, and lineage

The canonical name is Aggregate, sometimes written Aggregate Root to name the
single entity that fronts it. Eric Evans introduced the term in *Domain-Driven
Design. Tackling Complexity in the Heart of Software*, Addison-Wesley, 2003,
in the tactical patterns chapter that also gives Entity, Value Object,
Repository, and Domain Service. Evans defines an aggregate as a cluster of
associated objects treated as a unit for the purpose of data changes, with one
member designated the root, and states that objects outside the aggregate may
hold a reference only to the root, never to an internal member (Wikipedia
contributors, "Domain-driven design", https://en.wikipedia.org/wiki/Domain-driven_design,
verified 2026-08-02, summarizing Evans 2003, and citing the book directly at
the end of the article).

Martin Fowler's bliki restates the same idea in a single sentence that has
become the working definition most engineers quote from memory. He writes
that an aggregate is "a cluster of domain objects that can be treated as a
single unit" (Martin Fowler, "DDD Aggregate",
https://martinfowler.com/bliki/DDD_Aggregate.html, verified 2026-08-02). The
same page states the reference rule plainly, "any references from outside the
aggregate should only go to the aggregate root," which is the sentence most
implementations get wrong first and correct later, usually the hard way, in
production.

Chris Richardson's microservices pattern catalog carries a shorter, framework
neutral phrasing, "a graph of objects that can be treated as a unit"
(microservices.io, "Pattern. Aggregate", https://microservices.io/patterns/data/aggregate.html,
verified 2026-08-02), and points readers to his book, Chris Richardson,
*Microservices Patterns*, Manning, 2019, for the depth this landing page omits.
Richardson's contribution is not a new definition of the pattern, it is the
argument that follows from it. In a microservices architecture, where a
distributed ACID transaction across services is off the table, the aggregate
is the largest unit that can still be updated inside one local database
transaction, and that fact makes aggregate boundaries the natural first draft
of service boundaries, not an afterthought once the services already exist.

Vaughn Vernon extended the pattern past Evans's original chapter with a set of
concrete, testable rules for sizing an aggregate correctly, published across a
three part series and later folded into his book, Vaughn Vernon,
*Implementing Domain-Driven Design*, Addison-Wesley, 2013, chapter 10,
Aggregates. His central rules, restated in the widely cited summary "model
true invariants in consistency boundaries," "design small aggregates," and
"reference other aggregates by identity only," are the rules this entry treats
as normative for how an aggregate is actually built, because they turn Evans's
prose definition into a checklist an engineer can apply to a real class.

Three separate ideas share the English word aggregate, and conflating them is
the single most common source of confusion when the word appears in a design
review.

- **DDD Aggregate (this entry).** A cluster of one or more entities and value
  objects, fronted by a root, that forms a transactional consistency boundary.
  It is a modeling and persistence pattern, not a data operation.
- **SQL aggregate function.** `SUM`, `COUNT`, `AVG`, and similar functions that
  collapse many rows into one value. This meaning predates DDD by decades and
  has nothing to do with consistency boundaries, though the shared word causes
  a genuine mix up the first time a database engineer sits in a domain
  modeling session.
- **API Composition style aggregation.** Combining responses from several
  microservices into one client facing payload, the subject of the API
  Composition pattern in this same repository. That is a read time assembly
  concern across service boundaries, the opposite of a DDD aggregate, which is
  a write time consistency concern inside one boundary.

A useful test for which meaning is in play settles the question quickly. If
the conversation is about whether a change to several fields must commit
together or not at all, it is the DDD aggregate. If the conversation is about
collapsing rows or combining responses, it is one of the other two.

## 2. Problem and context

A service, whether a monolith module or a microservice, owns a piece of the
domain that contains more than one related object, and some of the rules that
govern that piece span more than one object at once. An order has line items,
and the sum of the line items must not exceed a credit limit. A bank account
has a balance and a set of pending holds, and the balance minus the holds must
never go negative. A shopping cart has items and a coupon, and the coupon must
be valid for the combined total, not any single item.

Without a named pattern, teams solve this in one of two ways, and both break
down as the system grows. The first is to let any code path that touches any
of the related objects update them directly, trusting that every call site
remembers every rule. This is the anemic domain model failure mode. The
objects become plain data holders, and the actual business rules scatter
across service classes, script files, and, eventually, database triggers,
because nobody can be certain every writer already knows every rule. The
second is to wrap the entire domain in one enormous transaction scope and load
most of the database on every write, which keeps the rules in one place but
makes every write compete for the same locks as every other write, so
throughput collapses as the team and the object graph grow.

The Aggregate pattern names the correct middle ground. Draw an explicit
boundary around the smallest cluster of objects that must be consistent with
each other at the end of every transaction, put exactly one entity in charge
of enforcing that consistency, and never let outside code reach past that
entity to mutate an internal member directly. Everything the boundary
excludes is either eventually consistent with the aggregate, reachable only by
identity rather than direct reference, or simply not the aggregate's concern
at all.

The context that makes this the right tool has three parts, and each is worth
naming because dropping any one of them turns the pattern into overhead rather
than a benefit.

- There is a real invariant, a rule that must hold true at the end of every
  transaction, not a convenience grouping of objects that happen to appear on
  the same screen.
- The invariant spans more than a single scalar field, so it cannot be
  enforced with a database column constraint alone.
- The system needs a place to put the enforcement logic that the storage layer
  cannot express, and the aggregate root method is that place.

Where none of the three hold, an aggregate is unnecessary machinery around a
plain entity, and dimension 4 names that case directly.

## 3. Forces

- **Consistency.** Favoured, strongly, but only within the boundary. Every
  invariant the aggregate declares is guaranteed true at the end of every
  successful transaction against it. Consistency between two different
  aggregates is explicitly not guaranteed by this pattern, and the pattern
  says so out loud rather than pretending otherwise.
- **Concurrency and lock contention.** Sacrificed as the aggregate grows.
  Every write to any part of the boundary competes for the same row locks or
  the same optimistic version counter as every other write to that boundary.
  A large aggregate that models an entire customer account, including every
  historical order, turns every unrelated update into a serialization point.
- **Coupling.** Favoured outward, sacrificed inward. Code outside the boundary
  depends only on the root's public methods and its identity, never on the
  internal shape, so the root can restructure its members freely. Inside the
  boundary, the members are tightly bound to the root's invariant enforcement
  by design, and that tight coupling is the whole point.
- **Latency.** Sacrificed for large aggregates, close to neutral for small
  ones. Loading an aggregate typically means loading the full object graph the
  root is responsible for, not a single row, so a poorly sized aggregate turns
  every read before a write into a wide, slow fetch.
- **Team topology.** Favoured. An aggregate boundary is a natural place to
  draw a service boundary and an ownership boundary at once, since
  Richardson's argument in dimension 1 is precisely that the transactional
  boundary and the team boundary should coincide.
- **Cognitive load.** Favoured for the invariant itself, since a reader can
  find every rule about an order's line items inside the `Order` class rather
  than scattered across the codebase. Sacrificed for cross-aggregate reasoning,
  since the reader must now separately track which invariants are eventually
  consistent through domain events rather than guaranteed at commit time.
- **Operability.** Mixed. A version field or an event stream on the aggregate
  gives an operator a clean signal for concurrency conflicts and state
  transitions, but a system with dozens of small aggregates coordinated by
  events is harder to trace end to end than one large transaction, because the
  full business process is no longer visible in a single stack trace.
- **Cost of change.** Favoured for adding behaviour inside an existing
  aggregate, sacrificed for moving an entity from one aggregate to another,
  because that move changes the transactional guarantee every caller already
  relies on, and every caller has to be re-audited against the new boundary.

No design that draws a boundary gets consistency for free everywhere. The
price the Aggregate pattern pays is that everything outside the boundary is
eventually consistent at best, and the discipline the pattern demands is
accepting that trade honestly rather than quietly widening the boundary until
the transaction covers the whole database again.

## 4. Applicability and non-applicability

Reach for an aggregate when the following hold.

- A group of objects has a real invariant that must be true at the end of
  every transaction that touches any of them, for example a total that must
  not exceed a limit, or a state machine transition that must not skip a
  step.
- The invariant naturally spans more than one entity or value object, so a
  single database constraint on one table cannot express it.
- The system needs a place, addressable by identity, that other parts of the
  domain can reference without reaching into its internals, matching the
  identity by reference rule from dimension 1.
- The team is willing to accept eventual consistency, coordinated by domain
  events, for anything that falls outside the boundary, rather than widening
  the boundary until the whole write path is one transaction again.
- The persistence technology can commit the whole boundary atomically, which
  a single relational database, a single document, or a single event stream
  per aggregate instance all satisfy.

Non-applicability. Do not reach for an aggregate in these situations, and each
line names the concrete reason rather than a general caution.

- **A single entity with no cross-object invariant.** A `Product` with a name,
  a SKU, and a price has no rule that spans more than one field, so wrapping
  it in aggregate ceremony, a root class plus a repository plus an event list,
  adds indirection with no consistency benefit. Model it as a plain entity.
- **Pure reference or lookup data.** Country codes, currency lists, and
  similar reference tables have no transactional invariant to protect, only a
  need to be read quickly and consistently across the system. A cache or a
  read model serves this better than a transactional boundary.
- **Reporting and analytics.** A read model that answers "what were total
  sales by region last quarter" is by definition a query across many
  transactional boundaries, not a candidate to become one. Forcing it inside
  an aggregate boundary either makes the aggregate impossibly wide or forces
  the report to run inside every write transaction, both wrong.
- **When the true invariant does not actually require synchronous
  consistency.** If a "rule" can tolerate a short delay, for example an
  inventory count that is corrected asynchronously rather than blocking every
  sale, it is not a true invariant in Vernon's sense, and forcing it into a
  synchronous aggregate boundary only adds contention for a guarantee the
  business never actually needed. This is the single most common
  over-application of the pattern, and it is the direct cause of the large
  aggregate failure mode in dimension 11.
- **Simple CRUD screens with no business rule at all.** A settings page that
  writes one row with no validation beyond type checking does not need a
  domain model, an aggregate root, or a repository. Plain data access is
  simpler, faster to build, and just as correct.
- **When cross-service ACID is what is actually needed.** If a use case
  genuinely requires two different services' data to change together, an
  aggregate inside either service cannot provide that. Reach for a Saga to
  coordinate the two transactions instead, and treat that as a signal the
  service boundary itself may be drawn in the wrong place.

## 5. Structure

- **Aggregate Root.** The single entity that every outside reference points
  to. It owns the aggregate's identity, exposes the only methods that may
  mutate anything inside the boundary, and is responsible for checking every
  invariant before a change is accepted. Every command against the aggregate
  enters through the root, never through an internal member directly.
- **Internal entities.** Objects inside the boundary that have their own
  identity but whose lifecycle is entirely owned by the root. An `OrderLine`
  has an identity distinct from the `Order`, but it is created, changed, and
  removed only by calling methods on the `Order`, and it is never looked up
  independently by a repository.
- **Value objects.** Objects inside the boundary defined entirely by their
  attributes, with no independent identity, immutable once created. A `Money`
  amount or an `Address` used inside the aggregate is replaced wholesale, not
  mutated in place.
- **Invariants.** The rules the root enforces on every state change, expressed
  as guard clauses inside the root's methods rather than as validation code
  living outside the class.
- **Repository.** The persistence gateway that loads and saves the aggregate
  as a whole. A repository exists per aggregate type, never per internal
  entity, which is the structural expression of the reference rule from
  dimension 1. Nothing outside the boundary can load or save an internal
  member independently of its root.
- **Domain events.** The record of what happened inside the aggregate that
  the rest of the system might care about. The root appends events during a
  state change and exposes them for the application layer to publish once the
  transaction that produced them has committed, never before.
- **Identity and version.** The root's identity is the address the rest of
  the domain uses to reference the aggregate. A version number or timestamp,
  incremented on every successful change, is the mechanism that detects a
  concurrent write from a different transaction before it silently
  overwrites another one, discussed further in dimension 8.

## 6. ASCII structure diagram

```text
                       +-------------------------------------+
                       |         Aggregate boundary           |
                       |         (transactional unit)          |
                       |                                        |
  another aggregate    |   +-----------------+                  |
  (holds only an id)   |   |  Aggregate Root  |                  |
       Order ---------------> Order           |                  |
       (by identity)   |   |  id  OrderId     |                  |
                       |   |  version  int    |                  |
                       |   +--------+---------+                  |
                       |            | owns, enforces invariants   |
                       |    +-------+--------+-------------+     |
                       |    v                v             v     |
                       | +--------+   +-----------+  +-----------+
                       | |OrderLine|   |OrderLine  |  | ShippingAddr|
                       | | entity |   | entity    |  |value object |
                       | +--------+   +-----------+  +-----------+
                       |                                        |
                       +-------------------------------------+
                                       ^
                                       |  load / save the whole graph
                                       |  in one local transaction
                              +--------+---------+
                              |  OrderRepository  |
                              +------------------+
```

No code outside the box may hold a pointer to an `OrderLine` or the
`ShippingAddr` value object independently of the `Order` root, and no
repository exists for `OrderLine` on its own. A second aggregate, for example
a `Customer`, references this one only by its `OrderId`, never by an object
reference into the box.

## 7. Dynamics

```text
Application Service          Aggregate Root            Repository / Store
        |                          |                          |
        | 1. load(orderId)         |                          |
        |------------------------------------------------------>
        |                          |     <-- deserialize -----|
        | <-------------- Order instance, version=3 ----------|
        |                          |                          |
        | 2. order.place()         |                          |
        |------------------------->|                          |
        |                          | 3. check invariants      |
        |                          |    (lines not empty,     |
        |                          |     not already placed)  |
        |                          | 4. mutate state          |
        |                          | 5. append OrderPlaced    |
        |                          |<-- return, no exception -|
        |                          |                          |
        | 6. save(order, expectedVersion=3)                    |
        |------------------------------------------------------>
        |                          |     7. WHERE version=3   |
        |                          |        UPDATE ... SET    |
        |                          |        version=4         |
        |                          |     8. rows affected==0? |
        |                          |        raise Concurrency |
        |                          |        Error, abort      |
        | <----------- success (version now 4) ---------------|
        |                          |                          |
        | 9. pull events, publish OrderPlaced AFTER commit     |
        |------------------------------------------------------>  event bus
```

The order of operations is the part implementers routinely get backwards.
Steps 1 through 5 happen entirely in memory, against a single in-process
object graph, so the invariant check in step 3 can inspect every member of the
aggregate with no network round trip and no partial state visible to any other
transaction. Step 6 is the single point of commitment. The repository
persists the whole boundary as one atomic write, and the version check in
steps 7 and 8 is what a second, concurrent transaction against the same root
would fail against, which is the mechanism dimension 8 calls optimistic
concurrency. Step 9, publishing the event, happens only after the commit in
step 6 succeeds. Publishing before the commit is a specific and common
misuse, discussed as a failure mode in dimension 11, because a subscriber can
then react to a change that a rolled back transaction later erases.

## 8. Implementation variants

- **State-based persistence through an ORM or a document store.** The root
  and its members are mapped to relational tables or embedded inside one
  document, and the repository loads and saves the current state of the whole
  graph on every transaction. This is the shape shown in dimension 6 and the
  code examples below, and it is by far the most common variant, because it
  works with ordinary relational tooling and requires no special
  infrastructure.
- **Event-sourced aggregates.** Instead of persisting current state, the
  repository persists the sequence of domain events the root produced, and
  reconstructs the root by replaying that sequence from the beginning, or from
  the nearest saved snapshot. This is the variant Axon Framework's aggregate
  model is built around, where an `@Aggregate` annotated class exposes command
  handling methods and event sourcing handling methods that mutate state only
  in response to an already-recorded event, never directly (AxonIQ, "Axon
  Framework", https://www.axoniq.io/products/axon-framework, verified
  2026-08-02, describing Axon as offering first-class support for DDD, CQRS,
  and event sourcing). This composes directly with the Event Sourcing pattern
  in this repository and gives a full audit trail as a side effect of the
  persistence mechanism itself, at the cost of the replay and snapshotting
  machinery dimension 11 discusses.
- **Aggregate as an actor or a virtual entity.** Frameworks such as Akka
  Persistence, Microsoft Orleans, or Dapr's actor model map one aggregate
  instance to one long lived, single threaded actor. Because an actor
  processes one message at a time by construction, this variant gets
  serialized access to the aggregate for free, without an explicit version
  field, at the cost of tying the aggregate's lifecycle to the actor
  runtime's activation and passivation model.
- **Aggregate as the unit a microservice owns entirely.** In a fully
  decomposed microservices system, a single, small aggregate can be the whole
  domain model of a service, with the service's database holding nothing but
  that aggregate's table or document. This is the shape the Azure
  Architecture Center's drone delivery reference design uses for `Delivery`,
  `Package`, `Drone`, and `Account`, each modeled as an independent aggregate
  with its own life cycle and referencing the others by identifier only
  (Microsoft, "Use Tactical DDD to Design Microservices",
  https://learn.microsoft.com/en-us/azure/architecture/microservices/model/tactical-domain-driven-design,
  verified 2026-08-02).
- **Optimistic concurrency via version number, versus pessimistic locking.**
  Most implementations, including the code examples in this entry, use a
  version counter checked at write time, which never blocks a reader and only
  rejects a writer that raced another writer. A pessimistic alternative takes
  a database row lock for the duration of the transaction, which trades a
  small amount of contention for the certainty that a conflicting writer
  simply waits rather than fails and retries. The version based approach is
  the default in nearly every reference implementation surveyed for this
  entry, because it scales better under read-heavy load and fails loudly
  rather than silently blocking.

## 9. Known production uses

- **eShopOnContainers, Microsoft's official microservices reference
  architecture.** Its ordering microservice models `Order` as an aggregate
  root explicitly, with the class declared `public class Order : Entity,
  IAggregateRoot` inside a namespace literally named `OrderAggregate`, and a
  source comment in the file noting that private backing fields are "a much
  better encapsulation aligned with DDD Aggregates and Domain Entities"
  (Microsoft, `eShopOnContainers` source, `Order.cs`,
  https://github.com/dotnet-architecture/eShopOnContainers/blob/dev/src/Services/Ordering/Ordering.Domain/AggregatesModel/OrderAggregate/Order.cs,
  verified 2026-08-02). The accompanying architecture guide describes this
  service as using "a simplified CQRS approach" that separates queries from
  "the commands, domain model, and transactions following the CQRS pattern,"
  with the aggregate as the transactional half (Microsoft, ".NET
  Microservices Architecture for Containerized .NET Applications",
  https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/apply-simplified-microservice-cqrs-ddd-patterns,
  verified 2026-08-02).
- **Axon Framework, the widely used open source Java toolkit for CQRS and
  event sourcing.** Its documentation and product page describe the framework
  as "Java-native with first-class support for DDD, CQRS, and event sourcing,"
  built around aggregates that handle commands and produce events, with
  "replayable event streams" as a direct consequence of modeling every
  aggregate change as a persisted event rather than an overwritten row
  (AxonIQ, "Axon Framework", https://www.axoniq.io/products/axon-framework,
  verified 2026-08-02).
- **Azure Architecture Center's drone delivery reference design.** Microsoft's
  own guidance for designing microservices around DDD models `Delivery`,
  `Package`, `Drone`, and `Account` as four separate aggregates, each with an
  independent life cycle, explicitly instructing that the `Delivery`
  aggregate "stores a `DroneId` and a `PackageId`, not direct references to
  those objects," and that the design should "use eventual consistency across
  aggregates" through domain events rather than a shared transaction
  (Microsoft, "Use Tactical DDD to Design Microservices",
  https://learn.microsoft.com/en-us/azure/architecture/microservices/model/tactical-domain-driven-design,
  verified 2026-08-02). The same guide states the general sizing principle
  directly, "design a microservice to be no smaller than an aggregate and no
  larger than a bounded context," which ties this pattern to service
  decomposition in the same sentence Richardson's argument in dimension 1
  predicts.

## 10. Consequences

Positive.

- Every invariant the domain actually cares about lives inside one class, so
  a reader auditing a business rule has exactly one file to open, not a
  scavenger hunt across services, controllers, and stored procedures.
- The transactional guarantee is explicit and bounded, so a developer never
  has to guess whether a given write is safe from a concurrent conflicting
  write, the version check answers that question mechanically.
- A well-sized aggregate maps naturally onto a service boundary and a team
  boundary at once, giving the organization a single seam to reason about for
  ownership, deployment, and data.
- Domain events fall out of the pattern for free, since the root is already
  the one place that knows exactly what changed and why, which gives the rest
  of the system a clean integration point without inventing a separate
  change-notification mechanism.

Negative.

- A poorly sized aggregate becomes a serialization bottleneck, since every
  write to any part of the boundary competes for the same lock or version
  counter as every other write, which is the direct cause of the deadlock and
  timeout failure mode in dimension 11.
- Everything outside the boundary is only eventually consistent, which is a
  real cost the business has to accept, not a technical detail to hide,
  because a query issued a moment after a cross-aggregate change can
  legitimately see stale data.
- The pattern adds real structure, a root, a repository, an event list, over
  a plain data class, and that structure is wasted ceremony on the large
  share of entities that have no real cross-object invariant, exactly the
  case dimension 4 excludes.
- Getting the boundary wrong is expensive to fix later, because every caller
  already depends on the transactional guarantee the current boundary
  provides, and widening or narrowing it later is a behavior change, not a
  refactor, discussed in dimension 14.

## 11. Failure modes and misuse

Judgement note. The symptoms below are drawn from widely documented practice
across the DDD and microservices community, not from a single sourced
incident report, and are labelled here as engineering judgement per the
non-applicability and judgement guidance this repository follows.

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 1 | Frequent lock timeouts or deadlocks under moderate write load, worse at peak traffic | The aggregate boundary is too large, including entities with independent, high frequency write paths, for example an entire `Customer` aggregate that embeds every historical `Order` | Split the aggregate along independent life cycles. Reference the split-off entity by identity only, and let cross-aggregate rules become eventually consistent through a domain event, per Vernon's "design small aggregates" rule |
| 2 | Two concurrent requests both appear to succeed, but the second silently discards the first request's change | The repository saves current state with a blind overwrite, with no version check on write | Add a version number or timestamp column, check it in the WHERE clause of the update, and raise a concurrency error when zero rows are affected, as shown in dimension 7's dynamics diagram |
| 3 | A rule everyone agrees on in design review is violated in production, and nobody can find where it was supposed to be enforced | The invariant lives in an application service or a UI form validator instead of inside the aggregate root's methods, so a second entry point, a batch job, an admin tool, a different API version, bypasses it entirely | Move the guard clause into the root's method itself, so every caller, present and future, goes through the same enforcement path, and delete the duplicate check at the call site |
| 4 | Loading a single aggregate instance is slow and memory heavy, and gets worse every month | The aggregate eagerly loads an unbounded or ever-growing collection, for example every line item an order has ever had rather than the current open order, or every event since the beginning of time with no snapshot | Bound the collection to what the current invariant actually needs, move historical data to a read model outside the aggregate, and for event-sourced aggregates, introduce periodic snapshotting so replay starts from a recent state rather than from event zero |
| 5 | A feature needs to update two aggregates together and the team reaches for a distributed transaction or a two-phase commit across services to make it work | A single business action genuinely spans two consistency boundaries, and the team is trying to force synchronous consistency the pattern deliberately does not provide | Coordinate the two updates with a Saga, accept eventual consistency between the two aggregates, and add compensating actions for the case where the second step fails after the first has committed |
| 6 | A subscriber processes an event for a state change that never actually happened, because the originating transaction rolled back after the event was already sent | The application layer publishes the aggregate's pending events before the repository's save call has committed, rather than after | Publish events only after the transaction that produced them commits successfully, using the outbox pattern or an equivalent transactional guarantee if the event bus and the database cannot share one transaction |

## 12. Trade-off matrix

Compared against three named alternatives for enforcing a multi-object
business rule.

| Force | Aggregate | Anemic domain model + service layer validation | Transaction Script | Single unbounded transaction across the whole write model |
|---|---|---|---|---|
| Where the invariant lives | Inside the root's methods, one place | Scattered across every service method that touches the objects | Inside the script, duplicated per use case | Nowhere explicit, implied by whatever the whole transaction happens to touch |
| Consistency guarantee | Explicit and bounded, guaranteed inside the boundary, eventual outside it | Implicit, only as strong as the discipline of every call site | Strong per script, but two scripts touching the same data can still race | Strongest possible, at the cost described below |
| Concurrency under load | Good, if the boundary is sized to the true invariant | Depends entirely on ad hoc locking the team invents case by case | Similar to aggregate, scoped per script rather than per domain concept | Poor, every write serializes against every other write in the whole model |
| Coupling for new features | Low, callers depend only on the root's public methods and identity | High, every new call site must rediscover every rule that applies | Low between scripts, but high duplication across scripts that share data | Very high, any change risks the shared transaction's behavior everywhere |
| Cost to introduce | Moderate, requires modeling discipline up front | Low up front, high later as rules multiply and drift apart | Low, matches how many teams already think about a single use case | Low to introduce, catastrophic to operate at scale |
| Best fit | A real cross-object invariant that must be enforced consistently across many call sites | Never recommended as a starting design, arises by drift, not by choice | A handful of use cases with genuinely independent rules and low reuse | Essentially never chosen deliberately, appears as an anti-pattern in legacy monoliths |

## 13. Related and incompatible patterns

- **Repository.** The aggregate's sole persistence gateway. A repository is
  scoped one-to-one with an aggregate type, never with an internal entity,
  which is the direct structural consequence of the identity-only reference
  rule in dimension 1.
- **Domain Event.** The aggregate's mechanism for telling the rest of the
  system what changed, published only after the local transaction commits, as
  shown in dimension 7. Domain events are how two aggregates stay eventually
  consistent without a shared transaction.
- **Saga.** Where a business process genuinely spans more than one aggregate,
  and by extension often more than one service, a Saga coordinates the
  sequence of local transactions and supplies compensating actions for
  partial failure. An aggregate never spans a Saga's boundary, it is one step
  inside it.
- **CQRS.** Aggregates naturally belong to the write side of a CQRS split,
  since their invariant checking and version conflict handling exist to
  protect writes, while the read side serves queries from a separately
  optimized model that does not need to load a whole aggregate to answer a
  question (Microsoft, "CQRS pattern", https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs,
  verified 2026-08-02, describing the write model as treating "a set of
  associated objects as a single unit for data changes, which is known as an
  aggregate in domain-driven design terminology").
- **Event Sourcing.** A persistence implementation choice for an aggregate,
  described as a variant in dimension 8, where the event stream itself is the
  source of truth and current state is a derived, replayable projection.
- **Decompose by Subdomain and Database per Service.** In a microservices
  system, the aggregate is frequently the unit a single service owns end to
  end, so these two patterns and this one reinforce each other, an aggregate
  gives the subdomain boundary a concrete, testable transactional shape.
- **Optimistic Offline Lock.** The version-checked write described in
  dimension 7 is a direct application of this older enterprise pattern to the
  aggregate's persistence boundary.
- **Incompatible with Shared Database.** A shared database that lets more
  than one service write to the tables an aggregate owns defeats the entire
  point of the boundary, since a second writer can bypass the root's
  invariant checks entirely by issuing SQL directly against the underlying
  tables. The two patterns are structurally opposed, not merely in tension.

## 14. Refactoring path in and out

Introducing an aggregate into code that lacks one, working from an anemic
domain model plus scattered service-layer validation.

1. Identify the true invariant first, in the sense of dimension 4's
   non-applicability list. Write down the exact rule that must hold at the
   end of every transaction, in one sentence, before writing any code.
2. Find every existing call site that currently enforces, or is supposed to
   enforce, that rule. This is usually more places than the team expects,
   because the anemic model failure mode means the same check was
   reimplemented independently more than once.
3. Introduce a new class for the root, initially wrapping the existing data
   access rather than replacing it, and move the invariant check from the
   first call site into a new method on that class.
4. One at a time, redirect every other call site found in step 2 to call the
   new method instead of duplicating the check, deleting the duplicate as
   each call site is migrated. Keep the old and new paths correct
   simultaneously during this window, do not do a big bang cutover.
5. Once every call site goes through the root, make the previously public
   setters or fields on the internal entities package-private or otherwise
   inaccessible from outside the aggregate, so the compiler, not just
   convention, enforces the boundary from this point forward.
6. Introduce the repository as the single load and save path, replacing any
   direct data access to the internal entities that step 5 just sealed off.
7. Add the version field and the optimistic concurrency check from dimension
   7 last, once the boundary itself is stable, since it is easiest to test in
   isolation after the invariant logic is already correct.

Removing an aggregate that has outlived its usefulness, most often because
the modeled invariant turned out not to need synchronous enforcement after
all.

1. Confirm the invariant is genuinely no longer required to be synchronous,
   for example the business has explicitly accepted a short window of
   inconsistency that can be corrected after the fact. Get this confirmed by
   whoever owns the business rule, not assumed by the engineering team.
2. Relax the guard clause inside the root to a warning or a logged event
   rather than a hard rejection, and observe production behavior for a full
   cycle of the process the rule protects, to catch any hidden dependency on
   the old guarantee before removing it.
3. Move the check, if it is still wanted at all, to an asynchronous process
   that reads the domain events the aggregate already emits, rather than to
   the synchronous write path.
4. Only after step 3 is running cleanly, collapse the aggregate root back
   into a plain entity, removing the repository indirection and the version
   field, and delete the now-unused invariant enforcement code.

## 15. Testing and verification

An aggregate is unusually easy to unit test compared to most enterprise
patterns, because its whole job is expressed as pure, in-memory behavior with
no network or database dependency required to exercise it.

- **Given-when-then against behavior, not storage.** Construct the root in a
  known starting state, invoke one method, and assert on either the resulting
  state or, for an event-sourced aggregate, on the exact sequence of events
  produced. This style needs no database, no mocked repository, and no test
  container, because the root's methods are ordinary synchronous functions.
- **Invariant violation tests are the highest-value tests to write.** For
  every guard clause inside the root, write a test that proves the clause
  actually rejects the invalid transition, not only that the valid path
  succeeds. A pattern whose only test coverage is the happy path has not
  actually verified the thing the pattern exists to protect.
- **Property-based testing for size and ordering invariants.** Where an
  invariant involves a bound, for example the maximum line count in the code
  example below, a property test that adds a randomized, growing number of
  lines and asserts the boundary is enforced at exactly the configured limit
  catches off-by-one errors that a handful of hand-picked examples miss.
- **In-memory fake repositories for application-service level tests.** A
  repository interface, as shown in dimension 6 and the code examples, is
  easy to fake with a plain in-memory map, which lets a test exercise the
  full load, mutate, save sequence including the optimistic concurrency check
  without a real database, keeping these tests fast enough to run on every
  commit.
- **Concurrency conflict tests deserve an explicit test, not an assumption.**
  Load the same aggregate instance twice inside a test, apply a change to the
  first copy and save it, then attempt to save the second, unmodified copy,
  and assert the repository rejects the second write. This is the one part
  of the pattern that is easy to implement incorrectly without a test
  catching it, because both the happy path and the naive, unchecked path
  compile and appear to work in isolation.
- **Snapshot replay tests for event-sourced aggregates.** Where dimension 8's
  event-sourced variant is in use, a dedicated test that replays a recorded
  event stream and asserts the reconstructed state matches the state that
  originally produced those events guards against a mutation being applied
  during replay that was not applied during the original command handling.

## 16. Observability signals

- **Concurrency conflict rate.** The count of optimistic concurrency
  rejections per aggregate type, per unit time. A rate near zero on a busy
  aggregate suggests the boundary may be smaller than the actual write
  pattern needs and is a candidate for a closer look, while a rising rate
  under normal load is the earliest available signal of the too-large
  boundary failure mode in dimension 11.
- **Aggregate load size and load latency.** The number of internal entities
  or events read on a typical load, and the time that load takes. A load size
  that grows month over month with no corresponding business growth points at
  the unbounded collection failure mode in dimension 11, well before it
  becomes a production incident.
- **Command to event ratio.** The count of accepted commands against the
  count of domain events produced. A root that produces more than one event
  category per command is not necessarily wrong, but a sudden change in this
  ratio after a deployment is a fast signal that a refactor accidentally
  changed the root's behavior.
- **Version distribution per instance.** For a system with millions of
  aggregate instances, the distribution of version numbers across instances
  shows which instances are hot, mutated frequently, versus cold, created
  once and rarely touched again, which is useful input for deciding where a
  smaller boundary would actually help.
- **Event publish lag.** For an outbox-based publish, discussed in dimension
  11's fix for premature publishing, the delay between the local transaction
  committing and the corresponding event reaching the message broker. A
  growing lag here is an early signal of a struggling event relay before any
  downstream subscriber notices missing events.
- **Rejected invariant count by rule.** Logging which specific guard clause
  rejected a command, not only that a command was rejected, turns the
  aggregate into a direct source of business-rule analytics, since a spike in
  one specific rejection, for example "cannot place an order with no lines,"
  usually points at a client-side bug rather than a genuine business
  violation.

## 17. Security and privacy implications

An aggregate is, by construction, a single point through which every mutation
of the data it owns must pass, and that concentration is a genuine security
benefit as well as a consistency benefit. Authorization checks placed on the
root's methods cannot be bypassed by a second entry point that reaches an
internal entity directly, because dimension 5's structure rule says no such
entry point should exist in the first place. A codebase that violates the
identity-only reference rule, by exposing an internal entity's repository or
its setters to outside callers, reopens exactly the authorization bypass the
boundary was meant to close, which makes the reference-rule violation in
dimension 11 a security concern as well as a consistency one.

Data that is genuinely personal or otherwise sensitive, when it lives inside
an aggregate, inherits the aggregate's version-checked, atomic write path,
which is a reasonable place to enforce field-level access rules or redaction
before a value object leaves the boundary in a domain event, since an event
published from inside the root's method is the one place every downstream
consumer of that data can be guaranteed to pass through. Where the pattern is
event-sourced, per dimension 8, this implies an additional and often
underestimated obligation. An event log is typically append-only and
long-lived by design, so a value that later needs to be forgotten under a
data protection request cannot simply be deleted from a single row, and the
system needs a separate, deliberate mechanism, for example encrypting
personal fields with a key that can itself be deleted, sometimes called
crypto-shredding, to honor an erasure request without breaking the event
stream's integrity. This is not a concern the Aggregate pattern itself solves,
and an implementation that adopts event sourcing without planning for it is
taking on a real, documented obligation silently.

The pattern says nothing about network transport security, authentication, or
encryption at rest, all of which are the responsibility of the surrounding
service and its persistence layer, not of the aggregate's modeling
discipline.

## Code examples

Three languages that show the pattern in genuinely different idioms.
TypeScript and Python both show the classical object-oriented shape, a root
class with private state, guard clauses, and a pulled event list, matched
against an in-memory repository that performs the optimistic concurrency
check from dimension 7. Go is included specifically because it has no
exceptions and no true private-by-default fields inside a package boundary in
the same sense the other two languages do, so the invariant enforcement has
to be expressed through error-returning methods rather than thrown
exceptions, which is the idiomatic Go shape for the same guarantee. Java and
Rust are omitted here only for space, not because either language fits the
pattern poorly. Axon Framework in dimension 9 is itself a Java example of the
identical shape shown below with annotation-driven command handling in place
of the explicit method calls.

### TypeScript

```typescript
class DomainError extends Error {}

interface DomainEvent {
  readonly kind: string;
}

class OrderPlaced implements DomainEvent {
  readonly kind = "OrderPlaced";
  constructor(readonly orderId: string, readonly total: number) {}
}

class OrderLine {
  constructor(
    readonly sku: string,
    readonly quantity: number,
    readonly unitPrice: number
  ) {
    if (quantity <= 0) {
      throw new DomainError("quantity must be positive");
    }
  }

  get lineTotal(): number {
    return this.quantity * this.unitPrice;
  }
}

const MAX_LINES = 25;

class Order {
  private readonly lines: OrderLine[] = [];
  private placed = false;
  private readonly events: DomainEvent[] = [];
  private _version = 0;

  private constructor(readonly id: string) {}

  static create(id: string): Order {
    return new Order(id);
  }

  get version(): number {
    return this._version;
  }

  addLine(line: OrderLine): void {
    if (this.placed) {
      throw new DomainError("cannot add a line to a placed order");
    }
    if (this.lines.length >= MAX_LINES) {
      throw new DomainError(`an order cannot exceed ${MAX_LINES} lines`);
    }
    this.lines.push(line);
    this._version += 1;
  }

  place(): void {
    if (this.placed) {
      throw new DomainError("order is already placed");
    }
    if (this.lines.length === 0) {
      throw new DomainError("cannot place an order with no lines");
    }
    this.placed = true;
    this._version += 1;
    this.events.push(new OrderPlaced(this.id, this.total()));
  }

  total(): number {
    return this.lines.reduce((sum, l) => sum + l.lineTotal, 0);
  }

  pullEvents(): DomainEvent[] {
    const pending = [...this.events];
    this.events.length = 0;
    return pending;
  }
}

interface OrderRepository {
  load(id: string): Order | undefined;
  save(order: Order, expectedVersion: number): void;
}

class ConcurrencyError extends Error {}

class InMemoryOrderRepository implements OrderRepository {
  private readonly store = new Map<string, { order: Order; version: number }>();

  load(id: string): Order | undefined {
    return this.store.get(id)?.order;
  }

  save(order: Order, expectedVersion: number): void {
    const existing = this.store.get(order.id);
    if (existing && existing.version !== expectedVersion) {
      throw new ConcurrencyError(`order ${order.id} was modified concurrently`);
    }
    this.store.set(order.id, { order, version: order.version });
  }
}

function placeOrder(repo: OrderRepository, id: string): void {
  const order = repo.load(id);
  if (!order) {
    throw new DomainError(`order ${id} not found`);
  }
  const expected = order.version;
  order.place();
  repo.save(order, expected);
  for (const event of order.pullEvents()) {
    console.log(`published ${event.kind}`);
  }
}

const repo: OrderRepository = new InMemoryOrderRepository();
const order = Order.create("order-1");
order.addLine(new OrderLine("sku-1", 2, 19.99));
repo.save(order, 0);
placeOrder(repo, "order-1");
```

The guard clauses inside `addLine` and `place` are the invariant enforcement
from dimension 5, and note that nothing outside this file can construct an
`OrderLine` array of its own and hand it to an `Order`, since `Order`'s only
public constructor is the static `create` method and the private `lines`
array is never exposed. The `InMemoryOrderRepository.save` method is the
exact optimistic concurrency check drawn in dimension 7's dynamics diagram,
expressed as a version comparison rather than a database WHERE clause,
because the storage engine here is a plain map.

### Python

```python
from __future__ import annotations

from dataclasses import dataclass


class DomainError(Exception):
    pass


class ConcurrencyError(Exception):
    pass


@dataclass(frozen=True)
class OrderPlaced:
    order_id: str
    total: float


@dataclass(frozen=True)
class OrderLine:
    sku: str
    quantity: int
    unit_price: float

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise DomainError("quantity must be positive")

    @property
    def line_total(self) -> float:
        return self.quantity * self.unit_price


MAX_LINES = 25


class Order:
    def __init__(self, order_id: str) -> None:
        self.id = order_id
        self._lines: list[OrderLine] = []
        self._placed = False
        self._events: list[object] = []
        self.version = 0

    def add_line(self, line: OrderLine) -> None:
        if self._placed:
            raise DomainError("cannot add a line to a placed order")
        if len(self._lines) >= MAX_LINES:
            raise DomainError(f"an order cannot exceed {MAX_LINES} lines")
        self._lines.append(line)
        self.version += 1

    def place(self) -> None:
        if self._placed:
            raise DomainError("order is already placed")
        if not self._lines:
            raise DomainError("cannot place an order with no lines")
        self._placed = True
        self.version += 1
        self._events.append(OrderPlaced(self.id, self.total()))

    def total(self) -> float:
        return sum(line.line_total for line in self._lines)

    def pull_events(self) -> list[object]:
        pending, self._events = self._events, []
        return pending


class InMemoryOrderRepository:
    def __init__(self) -> None:
        self._store: dict[str, tuple[Order, int]] = {}

    def load(self, order_id: str) -> Order | None:
        entry = self._store.get(order_id)
        return entry[0] if entry else None

    def save(self, order: Order, expected_version: int) -> None:
        existing = self._store.get(order.id)
        if existing is not None and existing[1] != expected_version:
            raise ConcurrencyError(f"order {order.id} was modified concurrently")
        self._store[order.id] = (order, order.version)


def place_order(repo: InMemoryOrderRepository, order_id: str) -> None:
    order = repo.load(order_id)
    if order is None:
        raise DomainError(f"order {order_id} not found")
    expected = order.version
    order.place()
    repo.save(order, expected)
    for event in order.pull_events():
        print(f"published {type(event).__name__}")


if __name__ == "__main__":
    repo = InMemoryOrderRepository()
    order = Order("order-1")
    order.add_line(OrderLine("sku-1", 2, 19.99))
    repo.save(order, 0)
    place_order(repo, "order-1")
```

The leading `_` on `_lines`, `_placed`, and `_events` is a Python naming
convention rather than an enforced boundary, since Python has no true private
attribute, but it communicates the same intent as the TypeScript `private`
keyword. Nothing outside this class is meant to reach these fields, and every
mutation is meant to go through `add_line` or `place`. `OrderLine` is a frozen
dataclass, which gives the value-object immutability from dimension 5 for
free, and its `__post_init__` hook is where its own, narrower invariant, a
positive quantity, is enforced before the object can exist at all.

### Go

```go
package main

import "fmt"

type DomainError struct{ msg string }

func (e *DomainError) Error() string { return e.msg }

type ConcurrencyError struct{ msg string }

func (e *ConcurrencyError) Error() string { return e.msg }

type OrderLine struct {
	SKU       string
	Quantity  int
	UnitPrice float64
}

func NewOrderLine(sku string, quantity int, unitPrice float64) (OrderLine, error) {
	if quantity <= 0 {
		return OrderLine{}, &DomainError{"quantity must be positive"}
	}
	return OrderLine{sku, quantity, unitPrice}, nil
}

func (l OrderLine) LineTotal() float64 {
	return float64(l.Quantity) * l.UnitPrice
}

const maxLines = 25

type OrderPlaced struct {
	OrderID string
	Total   float64
}

type Order struct {
	ID      string
	lines   []OrderLine
	placed  bool
	events  []interface{}
	Version int
}

func NewOrder(id string) *Order {
	return &Order{ID: id}
}

func (o *Order) AddLine(line OrderLine) error {
	if o.placed {
		return &DomainError{"cannot add a line to a placed order"}
	}
	if len(o.lines) >= maxLines {
		return &DomainError{fmt.Sprintf("an order cannot exceed %d lines", maxLines)}
	}
	o.lines = append(o.lines, line)
	o.Version++
	return nil
}

func (o *Order) Place() error {
	if o.placed {
		return &DomainError{"order is already placed"}
	}
	if len(o.lines) == 0 {
		return &DomainError{"cannot place an order with no lines"}
	}
	o.placed = true
	o.Version++
	o.events = append(o.events, OrderPlaced{o.ID, o.Total()})
	return nil
}

func (o *Order) Total() float64 {
	sum := 0.0
	for _, l := range o.lines {
		sum += l.LineTotal()
	}
	return sum
}

func (o *Order) PullEvents() []interface{} {
	pending := o.events
	o.events = nil
	return pending
}

type OrderRepository struct {
	store map[string]struct {
		order   *Order
		version int
	}
}

func NewOrderRepository() *OrderRepository {
	return &OrderRepository{store: make(map[string]struct {
		order   *Order
		version int
	})}
}

func (r *OrderRepository) Load(id string) (*Order, bool) {
	entry, ok := r.store[id]
	if !ok {
		return nil, false
	}
	return entry.order, true
}

func (r *OrderRepository) Save(order *Order, expectedVersion int) error {
	entry, ok := r.store[order.ID]
	if ok && entry.version != expectedVersion {
		return &ConcurrencyError{fmt.Sprintf("order %s was modified concurrently", order.ID)}
	}
	r.store[order.ID] = struct {
		order   *Order
		version int
	}{order, order.Version}
	return nil
}

func PlaceOrder(repo *OrderRepository, id string) error {
	order, ok := repo.Load(id)
	if !ok {
		return &DomainError{fmt.Sprintf("order %s not found", id)}
	}
	expected := order.Version
	if err := order.Place(); err != nil {
		return err
	}
	if err := repo.Save(order, expected); err != nil {
		return err
	}
	for _, event := range order.PullEvents() {
		fmt.Printf("published %T\n", event)
	}
	return nil
}

func main() {
	repo := NewOrderRepository()
	order := NewOrder("order-1")
	line, err := NewOrderLine("sku-1", 2, 19.99)
	if err != nil {
		panic(err)
	}
	if err := order.AddLine(line); err != nil {
		panic(err)
	}
	if err := repo.Save(order, 0); err != nil {
		panic(err)
	}
	if err := PlaceOrder(repo, "order-1"); err != nil {
		panic(err)
	}
}
```

Go's lowercase field names, `lines`, `placed`, `events`, are unexported at the
package level, which is the language's actual privacy boundary, tighter than
Python's naming convention and closer in effect to TypeScript's `private`
keyword. `AddLine` and `Place` return an `error` value rather than throwing,
which is idiomatic Go, and every caller in `PlaceOrder` and `main` checks that
error immediately rather than letting an invalid state propagate silently,
the same discipline the guard clauses enforce in the other two languages
through exceptions instead.

## 18. References

1. Eric Evans. *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*. Addison-Wesley, 2003. ISBN 0-321-12521-5. Tactical patterns
   chapter, source of the Aggregate, Aggregate Root, Entity, and Value Object
   definitions used throughout dimensions 1, 5, and 6.
2. Vaughn Vernon. *Implementing Domain-Driven Design*. Addison-Wesley, 2013.
   ISBN 978-0-321-83457-7. Chapter 10, Aggregates. Source of the "design small
   aggregates" and "reference other aggregates by identity only" rules used
   in dimensions 1, 4, and 11.
3. Wikipedia contributors. "Domain-driven design".
   https://en.wikipedia.org/wiki/Domain-driven_design
   Verified 2026-08-02. Used to confirm the aggregate root reference rule and
   the citation to Evans 2003, quoted in dimension 1.
4. Martin Fowler. "DDD_Aggregate".
   https://martinfowler.com/bliki/DDD_Aggregate.html
   Verified 2026-08-02. Source of the working definition, "a cluster of
   domain objects that can be treated as a single unit," and the
   root-only-reference rule quoted in dimension 1.
5. Chris Richardson. "Pattern. Aggregate". microservices.io.
   https://microservices.io/patterns/data/aggregate.html
   Verified 2026-08-02. Source of the framework-neutral definition, "a graph
   of objects that can be treated as a unit," quoted in dimension 1, and the
   pointer to Richardson's book for the microservices-specific argument.
6. Chris Richardson. *Microservices Patterns*. Manning, 2019.
   ISBN 978-1-61729-454-9. Source of the argument that an aggregate is the
   largest unit updatable inside one local ACID transaction in a
   microservices architecture, used in dimension 1 and dimension 3.
7. Microsoft. "Use Tactical DDD to Design Microservices". Azure Architecture
   Center.
   https://learn.microsoft.com/en-us/azure/architecture/microservices/model/tactical-domain-driven-design
   Verified 2026-08-02. Source of the drone delivery `Delivery`, `Package`,
   `Drone`, `Account` aggregate example, the "design small aggregates" and
   "reference other aggregates by identity only" restatement, and the "no
   smaller than an aggregate and no larger than a bounded context" sizing
   principle, used in dimensions 8, 9, and 12.
8. Microsoft. "Use Domain Analysis to Model Microservices". Azure
   Architecture Center.
   https://learn.microsoft.com/en-us/azure/architecture/microservices/model/domain-analysis
   Verified 2026-08-02. Used for the bounded context and strategic DDD
   context surrounding tactical patterns, referenced in dimension 2.
9. Microsoft. `eShopOnContainers` source repository, `Order.cs`.
   https://github.com/dotnet-architecture/eShopOnContainers/blob/dev/src/Services/Ordering/Ordering.Domain/AggregatesModel/OrderAggregate/Order.cs
   Verified 2026-08-02. Source of the `IAggregateRoot` and `OrderAggregate`
   naming used as a named production use in dimension 9.
10. Microsoft. ".NET Microservices Architecture for Containerized .NET
    Applications", "Applying simplified CQRS and DDD patterns in a
    microservice".
    https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/apply-simplified-microservice-cqrs-ddd-patterns
    Verified 2026-08-02. Source of the CQRS description of the
    eShopOnContainers ordering microservice quoted in dimension 9, and the
    relationship between CQRS and aggregates discussed in dimension 13.
11. Microsoft. "CQRS pattern". Azure Architecture Center.
    https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs
    Verified 2026-08-02. Source of the direct statement that the CQRS write
    model treats "a set of associated objects as a single unit for data
    changes, which is known as an aggregate in domain-driven design
    terminology," quoted in dimension 13.
12. AxonIQ. "Axon Framework".
    https://www.axoniq.io/products/axon-framework
    Verified 2026-08-02. Source of the Axon Framework named production use
    in dimension 9 and the event-sourced aggregate variant description in
    dimension 8.
