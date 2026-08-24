---
name: Entity Service
slug: entity-service
family: 18-anti-patterns
category: Anti-pattern
aliases: [CRUD Service, CRUDy Service, Table-per-Service, Data-Centric Service, Entity-Centric Business Service, Anemic Microservice]
first_described: "Erl 2008 (entity-centric business service, a neutral SOA service model); Nygard 2017 (named as an anti-pattern for microservices)"
maturity: contested
related: [anemic-domain-model, big-ball-of-mud, god-object, bounded-context, aggregate, backend-for-frontend, saga]
incompatible_with: [bounded-context, aggregate]
verified: 2026-08-02
---

# Entity Service

## 1. Name, aliases, and lineage

The name Entity Service carries two separate histories that point in opposite
directions, and confusing them is the first mistake a reader makes.

The term entered service-oriented architecture literature through Thomas Erl,
who classified business services into three models. task services, entity
services, and utility services. Erl's own pattern catalog, maintained by his
organization Arcitura, describes an entity service as "a business-centric
service that bases its functional boundary and context on one or more related
business entities" (Arcitura Patterns, "Entity Services",
https://patterns.arcitura.com/soa-patterns/basics/soamethodology/entity_services
verified 2026-08-02). In this framing the service is modeled around a noun the
enterprise already recognizes, customer, invoice, claim, and exposes
operations that read like create, read, update, and delete. Erl's stated
reason for wanting this shape was reuse. an entity service that stays agnostic
of any one business process can be called by many different workflows across
an organization, which was the governing value inside a centrally governed
SOA with a shared registry and an enterprise service bus in the middle. In
that lineage entity service is not a pejorative. it is a deliberate, reusable
building block.

The second lineage begins a decade later, once the same shape got carried into
microservice architecture, where each service is a separately deployed,
separately owned, network-addressable process rather than a component behind
a shared bus. Michael Nygard named the result an antipattern in a widely
cited 2017 post, arguing that when every business entity becomes its own
network service, "entity services are invoked on nearly every request, so
they will become heavily loaded," and the whole system's availability ends up
coupled to services that were supposed to be independent (Michael Nygard,
"The Entity Service Antipattern", December 2017,
https://www.michaelnygard.com/blog/2017/12/the-entity-service-antipattern/
verified 2026-08-02). Ben Morris made the same argument from a different
angle, calling entity services "finely-grained services that look after a
single data entity, normally exposing nothing more than simple CRUD methods"
and arguing that at that grain the resulting system can behave worse than
the monolith it replaced (Ben Morris, "Entity services. when microservices
are worse than monoliths",
https://www.ben-morris.com/entity-services-when-microservices-are-worse-than-monoliths/
verified 2026-08-02).

Common aliases in the second lineage include CRUD Service, CRUDy Service,
Table-per-Service, and Data-Centric Service, none of them flattering. Tareq
Abedrabbo, writing for InfoQ, described entity services as "conceptually
small but shallow," meaning they do very little beyond manipulating or
exposing their own internal state (Tareq Abedrabbo, "Entity Services
Complexity", InfoQ, July 2018,
https://www.infoq.com/news/2018/07/entity-services-complexity/
verified 2026-08-02). That word, shallow, echoes a term from a different
book entirely. John Ousterhout defines a shallow module as one whose
interface is almost as complex as its implementation, so the abstraction it
offers barely pays for itself (John Ousterhout, A Philosophy of Software
Design, 2nd edition, Yaknyam Press, 2021, the chapter on module depth).
Ousterhout never wrote about entity services specifically, but the shape he
describes, a large interface hiding very little real behavior, is exactly
what critics of entity services are pointing at.

This entry catalogs the second lineage, the one filed here as an anti-pattern,
while keeping the first lineage visible, because the same shape is a
reasonable, even recommended, design choice in a different deployment
context. What changed between 2008 and 2017 is not the shape of the service.
it is where the network boundary sits relative to that shape. That tension is
unresolved in the industry today. Erl's own catalog still lists entity
services without a warning label, while the microservices literature treats
the term as shorthand for a mistake. This entry marks the maturity of that
classification as contested rather than settled, and the applicability
section below draws the line as precisely as the sources allow.

## 2. Problem and context

A team decomposes a monolith, or designs a new distributed system from
scratch, and reaches for the most obvious axis of decomposition available.
the nouns already sitting in the domain. There is a Product table, an Account
table, an Order table, an Inventory table, so the team stands up a
ProductService, an AccountService, an OrderService, an InventoryService, each
owning exactly one of those tables and exposing create, read, update, and
delete operations over it. Every service maps cleanly to a bounded piece of
the schema. Every service has an obvious owning team. The architecture
diagram looks tidy, one box per noun, and it survives a whiteboard review
without objection, because nothing about it looks wrong in isolation.

The problem surfaces the first time somebody has to satisfy a real business
operation rather than read or write a single record. Pricing a shopping cart
needs the cart's line items, the current price and availability of each
product in those lines, and the tax rate tied to the customer's account.
None of that data lives in one service. The client, or some coordinating
layer sitting above the entity services, now issues one network call per
product in the cart plus one call for the account, just to compute a single
number. As the business grows more features, checkout, recommendations,
order history, refunds, each one turns out to need the same handful of
entities in a different combination, so the fan-out repeats itself across
every feature rather than staying isolated to one.

The context that produces this problem has three recognizable ingredients.
First, decomposition happened along data ownership rather than along
business capability, so the resulting services mirror the schema instead of
mirroring what the business actually does. Second, the operations that
matter to users, checking out, shipping an order, approving a claim, span
more than one entity, because almost no real business transaction touches
exactly one table. Third, the services were given a network boundary, a
separate deployment, a separate database or schema, and a separate release
cadence, so every cross-entity read that used to be a function call or a SQL
join is now a remote call with its own latency, its own failure mode, and
its own version to negotiate. Inside a single process none of this would be
visible. across a network it becomes the defining cost of the design.

## 3. Forces

The following weighting reflects engineering judgement about where the
pattern's costs and benefits actually land, informed by the cited sources
rather than a single controlled benchmark.

- **Reuse.** Favoured, and this is the pattern's original selling point. one
  entity service can serve dozens of unrelated workflows without knowing
  about any of them, which is exactly the value Erl's SOA model was built
  around.
- **Coupling at the network layer.** Sacrificed once a deployment boundary
  sits at entity granularity. Nygard's central claim is that entity services
  create operational coupling that undermines the independence microservices
  are meant to buy, because most features touch several entities at once.
- **Team autonomy on paper.** Favoured, in the sense that each team owns a
  clean, small surface. Sacrificed in practice, because Nygard also notes
  that even when teams "can still deploy in their own cadence," the semantic
  coupling between entities "requires cross-team negotiation" whenever a
  shared field or contract changes.
- **Latency.** Sacrificed. Every cross-entity read that used to be an
  in-process call becomes a network round trip, and the number of round
  trips grows with the size of the composite operation rather than staying
  constant.
- **Availability.** Sacrificed, and this is the sharpest cost. Ben Morris
  observes that when small, interdependent services must collaborate to
  answer basic questions, "a single service failure can have a cascading
  effect that brings down numerous different processes." A checkout that
  calls five entity services is only as available as the least available of
  the five, multiplied together.
- **Cognitive load, locally.** Favoured. Any one entity service is trivial to
  read, understand, and change, because it does one narrow thing.
- **Cognitive load, systemically.** Sacrificed. The business logic that ties
  entities together does not disappear, it moves into whatever aggregator,
  gateway, or client happens to call the entity services, and that logic is
  now scattered and often undocumented.
- **Consistency.** Sacrificed for any operation that must update more than
  one entity together, since there is no shared transaction across separate
  databases without a saga or a two-phase commit, both of which cost more
  than the equivalent in-process transaction would have.
- **Governance reuse in a centrally managed enterprise.** Favoured, which is
  the one force that explains why the same shape is not automatically wrong.
  a large organization with a shared registry, a shared bus, and a small
  number of well-known consumer teams gets real value from a single,
  reusable Customer service, because the alternative is dozens of teams each
  building their own partial copy of customer logic.

## 4. Applicability and non-applicability

Reach for an entity-shaped service, or accept one that already exists, when
any of these hold.

- The service lives inside a single deployable process or a modular monolith,
  where "calling" another entity's owner is a function call, not a network
  hop, and the cost profile from dimension 3 simply does not apply. This is
  the Repository or Aggregate pattern wearing the same clothes, not the
  antipattern.
- The organization runs a genuinely centralized SOA with a shared bus and a
  small, known set of consumers, and the entity service's whole purpose is
  reuse across many workflows that would otherwise duplicate the same data
  access logic. This is Erl's original context, and the value proposition
  still holds there.
- The data is reference data or configuration that changes rarely, is read
  by many callers, and is not part of any transactional workflow, a
  currency-exchange-rate table or a country-and-region lookup, for example.
  Coupling to it costs little because it almost never changes and almost
  never needs to be combined with anything else in a single transaction.
- The service is a deliberately generated, low-ceremony persistence layer for
  early-stage prototyping, where the team has explicitly chosen speed over
  architectural purity and knows it. Spring Data REST exists precisely for
  this case, generating a CRUD REST resource for every repository with no
  hand-written controller, which is the entity-service shape produced on
  purpose (Spring Data REST reference documentation,
  https://docs.spring.io/spring-data/rest/reference/index.html verified
  2026-08-02).
- Microsoft's own guidance for eShopOnContainers, a reference microservices
  application, states plainly that "many subsystems, BCs, or microservices
  are simpler and can be implemented more easily using simple CRUD services
  or using another approach" than DDD and CQRS (.NET Docs, "Applying
  simplified CQRS and DDD patterns in a microservice", the eShopOnContainers
  ordering microservice, dotnet/docs on GitHub,
  https://github.com/dotnet/docs/blob/main/docs/architecture/microservices/microservice-ddd-cqrs-patterns/eshoponcontainers-cqrs-ddd-microservice.md
  verified 2026-08-02). Simple subsystems with no real cross-entity
  workflow are the honest use case this quote is describing.

Do NOT reach for it, and treat an existing one as a liability to refactor,
when any of the following hold, because these are exactly the conditions
under which the sources above documented real cost.

- A network or deployment boundary separates the entity from the business
  operations that most commonly need it. If checkout, pricing, or shipping
  routinely call three or four entity services synchronously to answer one
  question, the boundary is in the wrong place, not the business logic.
- The system decomposes ALONG NOUNS AS THE ONLY AXIS, with no service drawn
  around a business capability or workflow. A system that is entirely
  ProductService, AccountService, OrderService, InventoryService, and
  nothing else, has no home for the logic that actually runs the business,
  and that logic ends up duplicated in every client instead.
- Several teams must renegotiate a shared contract every time one entity's
  shape changes, because the entity service has become a hub that many
  unrelated workflows quietly depend on. This is the same operational and
  semantic coupling Nygard describes, and it defeats the independent
  deployability that justified separate services in the first place.
- The data changes often and downstream consumers need the current value on
  every request rather than an eventually consistent copy, which forces
  synchronous fan-out on the hot path instead of an asynchronous, cached, or
  denormalized read.
- The team lacks the operational maturity, distributed tracing, a service
  mesh or comparable request-tracking tool, well-understood retry and
  timeout policy, to diagnose failures across a graph of chatty services.
  Nygard notes that debugging this shape typically forces teams to adopt a
  tool like Zipkin just to see where a slow or failed request actually went.
- The operation genuinely needs transactional consistency across more than
  one entity, debiting one account while crediting another, for example.
  Splitting the two into separate entity services and hoping the client
  calls both correctly is not a consistency strategy. Aggregate and Saga
  exist to solve this properly, see dimension 13.

## 5. Structure

Four participants, named by the role each plays in the failure mode this
entry documents, not by a generic class name.

- **EntityService.** Owns exactly one business entity, one table or a small
  cluster of closely related tables, and exposes it through create, read,
  update, and delete operations that mirror the persistence model almost
  one to one. It contains little to no domain logic of its own, because its
  design intent is data ownership, not behavior.
- **ConsumingClient.** Any caller, a mobile app, a web backend, another
  service, that needs the entity's data as one ingredient in a larger
  business operation. It never gets what it actually wants, a priced cart, a
  shippable order, from a single entity service.
- **ImplicitAggregator.** The place where the fan-out actually happens. In
  the antipattern's usual, undesigned form this is not a named component at
  all, it is whatever client code, mobile app, web controller, another
  microservice, happens to issue the several calls and stitch the results
  together. Its logic is duplicated wherever the same composite question is
  asked, because nothing owns it centrally.
- **SharedPersistenceOrRegistry.** In Erl's original SOA context this
  participant is a shared enterprise service bus and a service registry
  that make reuse cheap and governance possible. In the microservices
  antipattern this participant is usually absent or replaced by point-to-point
  HTTP calls with no shared contract enforcement, which is part of why the
  same shape behaves so differently in the two settings.

## 6. ASCII structure diagram

```
    SOA lineage, Erl 2008. entity service inside a governed bus
    +--------------------+        +-------------------------+
    |  Task Service A     |------->|                          |
    +--------------------+        |   Enterprise Service Bus |
    +--------------------+        |   (shared registry,      |
    |  Task Service B     |------->|    contract governance)  |
    +--------------------+        |                          |
                                   +-----------+--------------+
                                               |
                                               v
                                   +-------------------------+
                                   |   Customer EntityService |
                                   |   (create/read/update/   |
                                   |    delete, reused by A   |
                                   |    and B, and by others) |
                                   +-------------------------+

    Microservices antipattern, Nygard 2017. the same shape, no bus
    +---------------------+   HTTP    +----------------------+
    |  Web / Mobile Client |---------->|   AccountService     |
    |  (ImplicitAggregator)|           |   (CRUD, one table)  |
    |                      |   HTTP    +----------------------+
    |  fans out N calls    |---------->+----------------------+
    |  per business op     |           |   ProductService     |
    |                      |           |   (CRUD, one table)  |
    |                      |   HTTP    +----------------------+
    |                      |---------->+----------------------+
    +----------------------+           |   InventoryService   |
                                        |   (CRUD, one table)  |
                                        +----------------------+

    Nothing in this second diagram owns "price this cart".
    Every client that needs it repeats the same three calls.
```

## 7. Dynamics

The runtime flow that exposes the problem is a single business operation,
pricing a cart, that must touch three unrelated entity services to produce
one number. The important detail is where the composition logic lives. it is
not inside any of the three services, it is inside the caller, and that
caller has no way to know whether the three calls are consistent with each
other at the moment they are combined.

```
Client                AccountService        ProductService (x N items)
  |                          |                         |
  |-- GET /accounts/a1 ----->|                         |
  |<-- {taxRate 0.19} -------|                         |
  |                          |                         |
  |-- GET /products/p1 ---------------------------------->|
  |<-- {price 1999} ----------------------------------------|
  |                          |                         |
  |-- GET /products/p2 ---------------------------------->|
  |<-- {price 500} -----------------------------------------|
  |                          |                         |
  |  (client now computes subtotal times one plus       |
  |   taxRate locally, and nothing recorded that these   |
  |   three reads were consistent with each other)       |
  |                          |                         |
```

Two properties of this flow matter for the failure modes in dimension 11.
First, the number of remote calls grows linearly with the number of distinct
entities the operation touches, so a five-item cart and a fifty-item cart
issue very different numbers of calls even though the business logic is
identical in shape. Second, because AccountService and ProductService do not
know about each other, and neither knows about the client's larger
operation, there is no natural place to add a timeout budget, a retry
policy, or a circuit breaker that understands the operation as a whole.
Whatever resilience exists has to be reinvented at every call site that
performs this fan-out, or centralized later in an aggregator that did not
exist on day one, see the refactoring path in dimension 14.

## 8. Implementation variants

**Pure CRUD, no aggregation layer.** The form this entry mainly critiques.
Clients or other services call each entity service directly and combine the
results themselves. Cheapest to build, and the one that accumulates
duplicated composition logic across every consumer.

**Framework-generated entity services.** Spring Data REST and comparable
tools generate one CRUD resource per repository automatically, with almost
no hand-written code. This is the shape in its most concentrated form,
useful for admin tooling, internal back-office systems, and rapid
prototyping where the cost described in dimension 3 is acceptable because
the audience is small and the operations stay simple.

**Entity service plus a shared enterprise bus.** Erl's original context. a
central integration layer enforces the contract, mediates protocol
differences, and lets many task services reuse the same entity service
without ever calling it directly over the open network. The bus absorbs some
of the coupling cost, at the price of the bus itself becoming a shared,
governed, and often slow-to-change component.

**Entity service plus an aggregator or Backend for Frontend.** A dedicated
component sits between clients and the entity services and owns the
composition logic that would otherwise be duplicated at every call site.
This is close to the pattern Phil Calcado documented at SoundCloud, where a
generic public API required many calls per screen and per-client backend
services were introduced to aggregate and shape data for one specific
frontend (Phil Calcado, "The Back-end for Front-end Pattern (BFF)",
September 18, 2015,
https://philcalcado.com/2015/09/18/the_back_end_for_front_end_pattern_bff.html
verified 2026-08-02). The entity services survive unchanged. what changes is
that the fan-out logic finally has one owner.

**Task service replaces the entity service for the hot path.** Rather than
adding an aggregator in front of several entity services, the team writes a
capability-oriented service, CheckoutService, ShippingService, that owns
whatever local data it needs, often a denormalized copy or snapshot, and
stops calling other services synchronously on the hot path. This is the
refactor demonstrated in the Python example under Code examples, and it is
the shape Erl's own taxonomy calls a task service, one whose functional
boundary is drawn around a business process rather than around a noun.

**Event-driven read models.** Instead of any synchronous call at read time,
each consumer subscribes to change events published by the entity's owner
and maintains its own local, eventually consistent copy of exactly the
fields it needs. This removes the fan-out entirely at the cost of eventual
rather than immediate consistency, and it requires an event backbone the
team must build and operate.

## 9. Known production uses

**Spring Data REST, a framework that implements the pattern by design.**
Spring Data REST "exports Spring Data repositories as REST resources," so
every JPA entity annotated as a repository automatically receives a full set
of CRUD HTTP endpoints with no controller code written by hand (Spring Data
REST reference documentation,
https://docs.spring.io/spring-data/rest/reference/index.html verified
2026-08-02). This is the entity-service shape shipped as a first-class,
widely deployed library feature rather than something a team accidentally
backs into, and it is the clearest evidence that the shape has a genuine,
narrow, intentional use case.

**Segment, a customer data platform later acquired by Twilio, and its
"Goodbye Microservices" migration.** Segment's architecture grew to more
than 140 separately deployed services, one per destination integration, each
small and focused on a narrow piece of work, structurally the same shallow,
single-purpose shape critics of entity services describe even though the
axis of decomposition here was integrations rather than database tables.
Alexandra Noonan's account of the migration documents "exploding defect
rates" and "plummeting velocity" as the service count grew, three new
destinations added per month on average, and a team of three engineers
spending most of their time keeping the fleet of services running (Alexandra
Noonan, "Goodbye Microservices. From 100s of Problem Children to 1
Superstar", Twilio Segment engineering blog, July 10, 2018,
https://www.twilio.com/en-us/blog/developers/best-practices/goodbye-microservices
verified 2026-08-02). The team consolidated 120 unique dependencies and all
of the per-destination code into a single service they called Centrifuge,
and reported that shared library improvements roughly doubled in the first
year after the change. The specific entities in play differed from the
canonical product-and-account example, but the operational shape, many
small, narrowly scoped services that fan out and must be kept individually
healthy for the whole system to work, is the same failure this entry
catalogs.

**Microsoft's eShopOnContainers reference architecture.** Microsoft's own
.NET microservices architecture guidance, embodied in the open-source
eShopOnContainers sample, documents choosing simple CRUD services for
several of its own subsystems while reserving DDD and CQRS for the ordering
microservice specifically, stating that "many subsystems, BCs, or
microservices are simpler and can be implemented more easily using simple
CRUD services or using another approach" (.NET Docs, "Applying simplified
CQRS and DDD patterns in a microservice",
https://github.com/dotnet/docs/blob/main/docs/architecture/microservices/microservice-ddd-cqrs-patterns/eshoponcontainers-cqrs-ddd-microservice.md
verified 2026-08-02). This is a named, real, widely referenced reference
implementation that consciously accepts the entity-service shape for parts
of the system and consciously moves away from it for the part, ordering,
where cross-entity business rules actually live, which makes it useful
evidence for both sides of the applicability question in dimension 4.

## 10. Consequences

The following costs are stated as a matter of degree rather than a fixed
number, since the size of the effect depends on how many entities a typical
operation touches and how the team's infrastructure absorbs network calls.

Positive.

- Each individual service is small, easy to read in full, and cheap for a
  new engineer to understand end to end.
- Ownership of any one piece of data is unambiguous, which simplifies who to
  ask when a field's meaning is unclear.
- The service can be reused by any number of unrelated workflows without
  those workflows depending on each other, which is real value in a large,
  governed organization.
- Schema changes to one entity are, in principle, isolated to one team and
  one deployable, at least until another team's workflow depends on the
  changed field.

Negative.

- Business logic that spans more than one entity has no home inside the
  services themselves, so it accumulates in clients, aggregators, or
  wherever the fan-out happens to be written, often duplicated across many
  call sites.
- Network calls replace what would have been in-process function calls or
  SQL joins, so latency and failure probability both grow with the number of
  entities a business operation touches.
- Overall system availability becomes the product of the availability of
  every entity service a common operation depends on, which is worse than
  any single service's own availability number suggests.
- Deployments that look independent on paper are semantically coupled in
  practice, because a change to a shared entity's contract still requires
  coordinating with every team that consumes it.
- Debugging a slow or failed business operation requires tracing across
  several independently deployed services rather than reading one stack
  trace, which raises the operational maturity bar for the whole team.

## 11. Failure modes and misuse

**The checkout fan-out.** Symptom. A single user-facing action, pricing a
cart, submitting an order, triggers five or more synchronous calls to
different services, visible as a wide, shallow trace in any distributed
tracing tool. Cause. The operation's data lives across several entity
services and nothing owns the composition. Fix. Introduce an aggregator or a
task service that owns the composed operation, per dimension 14, or move to
an event-driven read model that avoids the synchronous calls entirely.

**The cascading outage.** Symptom. One entity service, often the one with
the most callers, goes down or slows down, and error rates spike across
several apparently unrelated features at the same time. Cause. Many
different workflows all synchronously depend on the same hub entity service
without a fallback, exactly the operational coupling Ben Morris describes.
Fix. Add timeouts, circuit breakers, and a defined degraded mode for every
synchronous dependency, and consider whether the dependent workflow actually
needs live data or could tolerate a cached or slightly stale copy.

**The unowned business rule.** Symptom. The same validation or calculation,
a discount rule, a tax rule, is implemented slightly differently in two or
three different clients that all call the same entity services, and they
occasionally disagree. Cause. Because entity services deliberately avoid
business logic, and nobody built a task service to own the operation, every
caller reimplements the rule independently. Fix. Extract the rule into a
task-oriented service or a shared library with a single source of truth, and
have every caller depend on that instead of on the entity services directly.

**The forced negotiation.** Symptom. A schema change that looks purely
internal to one team, renaming a field, adding a required value, requires a
multi-team migration meeting before it can ship. Cause. Enough workflows
have come to depend directly on that entity service's shape that it has
become a de facto shared contract, even though the team never intended to
publish one. Fix. Version the entity service's public contract explicitly,
and consider whether a stable, intentionally narrow API surface, rather than
the raw persistence model, should be what other teams actually depend on.

**The half-updated transaction.** Symptom. A refund or a transfer sometimes
leaves the system in a state where money moved out of one entity but never
arrived at the other, discovered days later during reconciliation. Cause.
The operation needed atomic consistency across two entity services, and the
client performed two separate calls with no compensating action if the
second one failed. Fix. Use a Saga with explicit compensating transactions,
or redesign the boundary so both pieces of state that must change together
live inside one service's transaction, see dimension 13.

**The N+1 fan-out at scale.** Symptom. A list screen or a batch job that
worked fine in testing with ten records becomes unusably slow in production
with ten thousand, because it calls an entity service once per record in a
loop. Cause. The same per-item call pattern shown in the diagram in
dimension 7 scales linearly instead of being batched. Fix. Add a genuine
batch-read endpoint to the entity service, or precompute and cache the data
the loop needs rather than calling out per item.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Entity Service | Task Service (capability-oriented) | Backend for Frontend / Aggregator | Aggregate (DDD, transactional boundary) | Shared enterprise bus with entity services (Erl's original context) |
|---|---|---|---|---|---|
| Reuse across unrelated workflows | High, that is its purpose | Low, it is shaped for one workflow | Medium, shaped for one client type | Low, it is shaped for one consistency boundary | High, the bus is designed for this |
| Business logic ownership | Weak or absent | Strong, the service owns the operation | Strong for composition, weak for domain rules | Strong, invariants live inside the boundary | Weak, logic still lives in task services above it |
| Cross-entity operations | Poor, forces client-side fan-out | Good, that is the point | Good, one place composes the calls | Not applicable at this scope | Poor, the entity service still fans nothing in itself |
| Transactional consistency | None across services | Depends on internal design | None, it composes reads and writes it does not own | Strong, within the aggregate boundary | None |
| Latency for a composite operation | Grows with number of entities touched | Flat, one call to the task service | One extra hop, then flat | Not applicable, in-process | Grows, plus bus overhead |
| Team autonomy | High on paper, low in practice | Medium, the task service still depends on data owners | Medium, the aggregator depends on entity services | High within the boundary | Low, governed centrally |
| Operational complexity | High once several services are chained | Medium, one more service to run | Medium, one more service to run | Low, no new network hop | High, the bus itself is infrastructure |
| Best fit | Reference data, admin CRUD, governed SOA reuse | Any real user-facing business operation | Multiple client types needing different shaped composites | Any operation needing atomic, all-or-nothing state changes | Large, centrally governed enterprises |

Reading of the table. Entity Service wins on reuse and loses on almost every
force that matters for a business operation that spans more than one
record. Task Service and Backend for Frontend both exist specifically to
give the composition logic a home, the first by owning data locally, the
second by owning the call orchestration. Aggregate solves a narrower but
harder problem, atomic consistency, that entity services cannot solve at
all across a network boundary. The shared bus column exists to show that
Erl's original context genuinely changes several of these answers, which is
why this entry treats the pattern's classification as contested rather than
uniformly bad.

## 13. Related and incompatible patterns

- **Anemic Domain Model.** The closest conceptual relative, one level down
  from the network. Martin Fowler describes it as domain objects that are
  "little more than bags of getters and setters," with all the real logic
  pulled out into separate service objects, and warns that "if all your
  logic is in services, you've robbed yourself blind" (Martin Fowler,
  "AnemicDomainModel", martinfowler.com bliki, 2003,
  https://martinfowler.com/bliki/AnemicDomainModel.html verified
  2026-08-02). Entity Service is what happens when that same separation of
  data from behavior is pushed across a network boundary rather than kept
  inside one process. Fixing the anemic model inside a service does not fix
  the entity-service problem between services, and fixing the boundary
  between services does not fix an anemic model inside any one of them. The
  two are genuinely separate defects that happen to rhyme.
- **Aggregate (Domain-Driven Design).** The intended structural fix at the
  domain-modeling level. Eric Evans describes an Entity, inside DDD, as an
  object with identity that persists across state changes, and an Aggregate
  as a cluster of entities and value objects treated as one consistency
  boundary with a single root (Eric Evans, Domain-Driven Design. Tackling
  Complexity in the Heart of Software, Addison-Wesley, 2003, the chapters
  on entities and aggregates). An entity service that maps one table to one
  network service has usually drawn its boundary at the wrong granularity.
  the Aggregate boundary, not the individual table, is normally the right
  place to put a service boundary when one is needed at all.
- **Backend for Frontend.** A composing fix rather than a competing pattern.
  It leaves the entity services in place and gives their composition logic
  a single, named owner, see dimension 8 and dimension 14.
- **Saga.** The fix for the transactional consequence of entity services,
  see the half-updated transaction failure mode in dimension 11. A saga
  coordinates a sequence of local transactions with explicit compensating
  actions when one step fails, which is what an entity-service architecture
  is missing by default.
- **Bounded Context.** Actively in tension with entity service as commonly
  practiced. A bounded context is drawn around a coherent model and the
  language that describes it, which frequently groups several entities
  together inside one boundary precisely because they change together and
  are meaningless apart. Slicing a bounded context along individual entities
  instead produces the coupling this entry describes, because the pieces
  that should have stayed together are now separated by a network call.
- **Big Ball of Mud.** The perverse convergent outcome. a system built from
  many small entity services, each individually clean, whose composition
  logic has scattered across every client and every ad hoc aggregator ends
  up exhibiting the same undocumented, tangled dependency graph that the Big
  Ball of Mud describes at the module level, just spread across network
  boundaries instead of files.
- **God Object.** The opposite failure at the other extreme, everything
  crammed into one service or class. Entity Service and God Object sit at
  two ends of the same axis, decomposition granularity, and a team
  overcorrecting away from one frequently lands on the other.

## 14. Refactoring path in and out

Entity services are rarely introduced deliberately as an antipattern.
teams back into them by decomposing along the schema. So the more useful
refactoring path is almost always out, from an existing fleet of entity
services toward a shape organized around business capability. The steps
below describe that direction.

1. Identify the business operations that currently fan out across several
   entity services, checkout, shipment creation, refund processing, by
   reading the traces or logs for the widest, most frequent request
   patterns.
2. For each operation, decide whether it needs strict, immediate consistency
   with the underlying entity data, or whether an eventually consistent,
   locally owned copy is acceptable. Payment amounts usually need the first.
   a product's marketing description usually tolerates the second.
3. For operations that can tolerate eventual consistency, introduce a task
   service that subscribes to change events from the entity services it
   depends on and maintains its own denormalized read model, removing the
   synchronous fan-out entirely. This is the shape demonstrated in the
   Python example under Code examples.
4. For operations that must stay synchronous but are called from many
   different clients, introduce a Backend for Frontend or a general
   aggregator that owns the composition logic once, so it stops being
   reimplemented at every call site. This is the shape demonstrated in the
   Go example under Code examples.
5. For operations that must change more than one entity atomically, do not
   solve it with a bigger client-side transaction across two remote calls.
   introduce a Saga with explicit compensating actions, or, if the two
   pieces of state genuinely belong together, merge them into one Aggregate
   owned by one service.
6. Once a task service or aggregator exists and is stable, the underlying
   entity services can often shrink back toward Erl's original, narrower
   intent, small, reusable, business-process-agnostic CRUD surfaces that
   other services call through the new composition layer rather than
   directly.
7. Re-measure the fan-out from step 1 after the change. the number of
   synchronous cross-service calls on the hot path for the target operation
   should have dropped to at most one, the call into the new task service or
   aggregator.

Introducing an entity service deliberately, the rare case where it is the
right call, follows a much shorter path. confirm the data is genuinely
reference-like or governed for wide reuse per dimension 4, expose the
narrowest CRUD surface the consumers actually need rather than the raw
persistence model, and document the contract as public and versioned from
day one, since dimension 11's forced-negotiation failure mode shows what
happens when that step is skipped.

## 15. Testing and verification

Easier because of the pattern.

- Each entity service in isolation is simple to test. its behavior is close
  to a thin layer over a database, so contract tests and straightforward
  CRUD assertions cover most of its surface with little setup.
- Because the service does not hold cross-cutting business rules, tests for
  it rarely need elaborate fixtures representing other parts of the domain.

Harder because of the pattern.

- The business logic that actually matters, the composition across
  entities, has no single owner to unit test, so it either gets tested
  indirectly through slow, brittle end-to-end tests that spin up several
  services, or it does not get systematically tested at all.
- A bug caused by two entity services disagreeing about a shared value at
  the moment a client combined them is close to impossible to reproduce with
  a unit test, since it depends on the interleaving of two independent
  systems.
- Consumer-driven contract tests become necessary wherever a workflow
  synchronously depends on another team's entity service, and skipping them
  is how the forced-negotiation failure mode in dimension 11 goes
  undetected until it breaks something.

Techniques that apply.

- **Contract tests, consumer-driven.** Each consumer of an entity service
  publishes the shape of the response it depends on, and the entity
  service's own test suite verifies it still satisfies every published
  contract before deploying, catching a breaking change before it reaches
  production rather than after.
- **Fan-out counting as a test assertion.** Once a task service or
  aggregator exists, assert directly on the number of downstream calls a
  given operation makes, the same counter demonstrated in the code examples
  below, so a regression that reintroduces a per-item loop calling an
  entity service fails the build rather than only showing up as a latency
  regression later.
- **Contract-first integration tests against a task service, not against
  the raw entity services.** Testing the composed operation through its
  single owning service, rather than re-testing the fan-out logic at every
  call site, keeps the test suite proportional to the number of business
  operations rather than the number of clients that happen to call them.
- **Chaos testing for the failure modes in dimension 11.** Deliberately
  failing or delaying one entity service in a staging environment and
  observing whether the dependent operation degrades gracefully or cascades
  is the most direct way to verify the availability coupling Ben Morris
  describes has actually been addressed.

## 16. Observability signals

What to record, per entity service and per composite operation.

- A per-request counter of how many downstream entity-service calls a given
  business operation issues, labelled by operation name. This is the single
  most direct signal for the fan-out failure mode, and it is exactly what
  the code examples below expose as `calls` and `catalog_calls`.
- Distributed tracing spans covering the whole composite operation, not just
  each individual entity-service call, so a slow checkout can be attributed
  to the specific downstream call that is slow rather than to the operation
  as a whole. Nygard notes that teams building this shape typically end up
  needing a tracing tool such as Zipkin for exactly this reason.
- Per-service error rate and latency percentiles, correlated against the
  error rate and latency of every operation that depends on it, so an
  on-call engineer can see at a glance which downstream services a given
  outage is coupled to.
- A dependency graph, built from tracing data rather than maintained by
  hand, showing which services are called by how many distinct upstream
  operations. A service that appears as a dependency of a large fraction of
  the system's operations is a hub, and deserves the same reliability
  investment as a database.
- Cache hit rate and staleness, for any operation that has been refactored
  toward a locally owned read model, since a falling hit rate or growing
  staleness there is an early warning that the denormalized copy has drifted
  from the source of truth.

A healthy instance on a dashboard. the per-operation fan-out count is flat
and matches the number of entities the operation was designed to touch, not
the size of whatever collection the operation happens to be processing. The
dependency graph shows a small number of hub services, each individually
well within its availability budget, and no operation with more than two or
three synchronous hops on its hot path.

A failing instance. the fan-out count for an operation grows with input
size, indicating the N+1 misuse from dimension 11. A hub service's error
rate spike is visible as a simultaneous error spike across several
apparently unrelated operations, indicating the cascading-outage failure
mode. Tracing shows the same three or four entity-service calls repeated
inside many different operations with no shared aggregator, indicating the
unowned-business-rule failure mode from dimension 11.

## 17. Security and privacy implications

This section is analytical judgement rather than a set of sourced facts,
since none of the cited sources address security or privacy directly.

**A wider authenticated attack surface.** Where a single well-designed
service might expose a handful of purposeful operations, an entity-service
architecture typically exposes one full CRUD surface per entity, and each of
those surfaces needs its own authentication and authorization enforcement.
More endpoints, each capable of reading or writing raw persisted state,
means more places an authorization check can be missed or implemented
inconsistently across teams.

**Over-exposed persistence fields.** Because an entity service's interface
tends to mirror its table almost directly, it is easy to expose a column
that was never meant to leave the database, an internal risk score, a
partner's negotiated price, a soft-delete flag, simply because nobody
designed a narrower response shape the way a purposeful API would. Frameworks
that generate the CRUD surface automatically, such as Spring Data REST,
raise this risk further, since a newly added column is exposed by default
unless explicitly excluded, rather than requiring an explicit decision to
expose it.

**Trust-boundary assumptions inside the fan-out.** Because entity services
are usually reached from inside the system rather than directly from the
public internet, teams frequently authenticate the aggregator or the
gateway and then treat calls between internal entity services as implicitly
trusted. That assumption breaks down as soon as any one internal service is
compromised or misconfigured, since a flat, trusting internal network gives
a single foothold access to every entity service behind it. Applying the
same authorization checks at every internal hop, not only at the public
edge, is the direct mitigation.

**Amplification through fan-out.** A single malicious or malformed request
that triggers a large, unbatched loop of entity-service calls, the N+1
misuse from dimension 11, amplifies one inbound request into many outbound
ones, which is a denial-of-service risk against the downstream entity
services even without any deliberate attack, simply through an
unintentionally large input. Bounding the number of downstream calls a
single inbound request can trigger, and rejecting or paginating inputs that
would exceed that bound, closes this off.

On privacy specifically, the practical caveat is the same one raised in
dimension 16. any log field or trace attribute that records which entities a
request combined, a customer ID alongside a product ID and an account ID in
one trace span, can itself become personally identifiable information once
correlated, and should be retained and access-controlled under the same
policy as any other identifier rather than assumed to be safe because it
originated as operational telemetry.

## 18. References

1. Arcitura Patterns. "Entity Services", part of Thomas Erl's SOA Patterns
   catalog.
   https://patterns.arcitura.com/soa-patterns/basics/soamethodology/entity_services
   Verified 2026-08-02. Source for the original, neutral SOA definition of
   entity-centric business services and the reuse rationale behind them.
2. Michael Nygard. "The Entity Service Antipattern". December 2017.
   https://www.michaelnygard.com/blog/2017/12/the-entity-service-antipattern/
   Verified 2026-08-02. Source for the microservices-era naming of the
   antipattern, the operational and semantic coupling claims, and the
   Zipkin observation in dimension 16.
3. Ben Morris. "Entity services. when microservices are worse than
   monoliths".
   https://www.ben-morris.com/entity-services-when-microservices-are-worse-than-monoliths/
   Verified 2026-08-02. Source for the CRUD-only definition and the
   cascading-failure claim in dimension 3 and dimension 11.
4. Tareq Abedrabbo. "Entity Services Complexity". InfoQ, July 2018.
   https://www.infoq.com/news/2018/07/entity-services-complexity/
   Verified 2026-08-02. Source for the "shallow" characterization quoted in
   dimension 1.
5. Spring Data REST reference documentation.
   https://docs.spring.io/spring-data/rest/reference/index.html
   Verified 2026-08-02. Source for the framework-generated entity-service
   production use in dimension 9 and the applicability case in dimension 4.
6. Alexandra Noonan. "Goodbye Microservices. From 100s of Problem Children
   to 1 Superstar". Twilio Segment engineering blog, July 10, 2018.
   https://www.twilio.com/en-us/blog/developers/best-practices/goodbye-microservices
   Verified 2026-08-02. Source for the Segment production migration and its
   numbers in dimension 9.
7. .NET Docs (Microsoft). "Applying simplified CQRS and DDD patterns in a
   microservice", eShopOnContainers reference architecture.
   https://github.com/dotnet/docs/blob/main/docs/architecture/microservices/microservice-ddd-cqrs-patterns/eshoponcontainers-cqrs-ddd-microservice.md
   Verified 2026-08-02. Source for the eShopOnContainers production use and
   the applicability quote in dimension 4.
8. Martin Fowler. "AnemicDomainModel". martinfowler.com bliki, 2003.
   https://martinfowler.com/bliki/AnemicDomainModel.html
   Verified 2026-08-02. Source for the Anemic Domain Model definition and
   quotes in dimension 13.
9. Eric Evans. Domain-Driven Design. Tackling Complexity in the Heart of
   Software. Addison-Wesley, 2003. ISBN 0-321-12521-5. The chapters covering
   Entities and Aggregates. Source for the Aggregate and Entity definitions
   in dimension 13.
10. Phil Calcado. "The Back-end for Front-end Pattern (BFF)". September 18,
    2015.
    https://philcalcado.com/2015/09/18/the_back_end_for_front_end_pattern_bff.html
    Verified 2026-08-02. Source for the Backend for Frontend variant in
    dimension 8 and its origin at SoundCloud.
11. John Ousterhout. A Philosophy of Software Design, 2nd edition. Yaknyam
    Press, 2021. ISBN 978-1732102217. The chapter on module depth. Source
    for the deep-module and shallow-module concept referenced in dimension
    1, offered as a parallel framing rather than a claim that Ousterhout
    wrote about entity services directly.

## Code examples

Three languages, each illustrating a different facet of the pattern.
TypeScript demonstrates the antipattern itself, a client fanning out across
two entity services to answer one question, with an explicit counter making
the fan-out observable. Python demonstrates the task-service refactor from
dimension 14, replacing synchronous fan-out with a locally owned price
snapshot captured once. Go demonstrates the Backend for Frontend refactor,
keeping the entity services intact but giving their composition a single
owner. Java is omitted because the pattern's failure mode is about service
granularity and network boundaries rather than a language feature, and the
same shape shown in TypeScript translates directly with no Java-specific
detail worth adding. Rust and Swift are omitted for the same reason.

### TypeScript, the antipattern

```typescript
interface Product {
  id: string;
  price: number;
}

interface Account {
  id: string;
  taxRate: number;
}

interface CartItem {
  productId: string;
  qty: number;
}

class ProductService {
  private readonly products = new Map<string, Product>([
    ["p1", { id: "p1", price: 1999 }],
    ["p2", { id: "p2", price: 500 }],
  ]);

  async get(id: string): Promise<Product> {
    const p = this.products.get(id);
    if (!p) throw new Error(`unknown product ${id}`);
    return p;
  }
}

class AccountService {
  private readonly accounts = new Map<string, Account>([
    ["a1", { id: "a1", taxRate: 0.19 }],
  ]);

  async get(id: string): Promise<Account> {
    const a = this.accounts.get(id);
    if (!a) throw new Error(`unknown account ${id}`);
    return a;
  }
}

// CartService owns no pricing data of its own, so answering one
// business question, the cart total, means calling out to every
// other entity service once per line item plus once for the account.
class CartService {
  calls = 0;

  constructor(
    private readonly products: ProductService,
    private readonly accounts: AccountService,
  ) {}

  async total(accountId: string, items: CartItem[]): Promise<number> {
    const account = await this.accounts.get(accountId);
    this.calls++;
    let subtotal = 0;
    for (const item of items) {
      const product = await this.products.get(item.productId);
      this.calls++;
      subtotal += product.price * item.qty;
    }
    return Math.round(subtotal * (1 + account.taxRate));
  }
}

async function main(): Promise<void> {
  const cart = new CartService(new ProductService(), new AccountService());
  const items: CartItem[] = [
    { productId: "p1", qty: 1 },
    { productId: "p2", qty: 3 },
  ];
  const total = await cart.total("a1", items);
  // Two products plus the account produced three separate entity
  // service calls for one checkout, and the count grows linearly
  // with the number of distinct items in the cart.
  console.log(total, cart.calls);
}

main();
```

### Python, the task-service refactor

```python
from dataclasses import dataclass


@dataclass
class PriceSnapshot:
    unit_price_cents: int
    tax_rate: float


@dataclass
class CartLine:
    product_id: str
    qty: int
    snapshot: PriceSnapshot


class Catalog:
    """Stands in for the ProductService entity service. Returns a
    snapshot rather than forcing every reader to fetch the live
    record on every access."""

    _prices = {
        "p1": PriceSnapshot(unit_price_cents=1999, tax_rate=0.19),
        "p2": PriceSnapshot(unit_price_cents=500, tax_rate=0.19),
    }

    def snapshot(self, product_id: str) -> PriceSnapshot:
        return self._prices[product_id]


class Checkout:
    """A task service. It owns the cart aggregate and captures a
    price snapshot per line at the moment an item is added, so
    pricing the cart later needs no call back to the catalog."""

    def __init__(self, catalog: Catalog) -> None:
        self.catalog = catalog
        self.lines: list[CartLine] = []
        self.catalog_calls = 0

    def add_item(self, product_id: str, qty: int) -> None:
        snapshot = self.catalog.snapshot(product_id)
        self.catalog_calls += 1
        self.lines.append(CartLine(product_id, qty, snapshot))

    def total_cents(self) -> int:
        # No catalog call here at all. The snapshot travels with
        # the line, so the total is computed entirely locally.
        subtotal = sum(line.snapshot.unit_price_cents * line.qty for line in self.lines)
        tax_rate = self.lines[0].snapshot.tax_rate if self.lines else 0.0
        return round(subtotal * (1 + tax_rate))


if __name__ == "__main__":
    checkout = Checkout(Catalog())
    checkout.add_item("p1", 1)
    checkout.add_item("p2", 3)
    print(checkout.total_cents(), checkout.catalog_calls)
```

### Go, the Backend for Frontend refactor

```go
package main

import "fmt"

// Product and Account stand in for two separately owned entity
// services, reached over the network in a real deployment.
type Product struct {
	ID    string
	Price int
}

type Account struct {
	ID      string
	TaxRate float64
}

type ProductService struct{ store map[string]Product }

func (s ProductService) Get(id string) (Product, error) {
	p, ok := s.store[id]
	if !ok {
		return Product{}, fmt.Errorf("unknown product %s", id)
	}
	return p, nil
}

type AccountService struct{ store map[string]Account }

func (s AccountService) Get(id string) (Account, error) {
	a, ok := s.store[id]
	if !ok {
		return Account{}, fmt.Errorf("unknown account %s", id)
	}
	return a, nil
}

// Line describes one item a client wants priced.
type Line struct {
	ProductID string
	Qty       int
}

// CheckoutAggregator is the single place that knows how to combine
// the two entity services for the operation clients actually need.
// The entity services stay unchanged and stay reusable elsewhere.
type CheckoutAggregator struct {
	products ProductService
	accounts AccountService
}

func (a CheckoutAggregator) Total(accountID string, lines []Line) (int, error) {
	account, err := a.accounts.Get(accountID)
	if err != nil {
		return 0, err
	}
	subtotal := 0
	for _, l := range lines {
		p, err := a.products.Get(l.ProductID)
		if err != nil {
			return 0, err
		}
		subtotal += p.Price * l.Qty
	}
	return int(float64(subtotal) * (1 + account.TaxRate)), nil
}

func main() {
	aggregator := CheckoutAggregator{
		products: ProductService{store: map[string]Product{
			"p1": {ID: "p1", Price: 1999},
			"p2": {ID: "p2", Price: 500},
		}},
		accounts: AccountService{store: map[string]Account{
			"a1": {ID: "a1", TaxRate: 0.19},
		}},
	}
	total, err := aggregator.Total("a1", []Line{{"p1", 1}, {"p2", 3}})
	if err != nil {
		panic(err)
	}
	fmt.Println(total)
}
```
