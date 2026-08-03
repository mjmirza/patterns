---
name: Database per Service
slug: database-per-service
family: 10-microservices
category: Structural
aliases: [Private Database per Service, Data Isolation Pattern]
first_described: "Richardson, Microservices Patterns, Manning, 2019, chapter 2, and microservices.io, pattern catalog, first published circa 2014"
maturity: canonical
related: [decompose-by-business-capability, decompose-by-subdomain, saga, api-composition, cqrs, event-sourcing, self-contained-service, strangler-application]
incompatible_with: [shared-database]
verified: 2026-08-03
---

# Database per Service

## 1. Name, aliases, and lineage

The canonical name in the catalog literature is Database per Service. Chris
Richardson, who curates the microservices.io pattern catalog and wrote
*Microservices Patterns*, Manning, 2019, names it exactly this way and places
it in the data-management category of his catalog, alongside its direct
opposite, the Shared Database anti-pattern
([microservices.io, "Database per service"](https://microservices.io/patterns/data/database-per-service.html),
verified 2026-08-03). The catalog page states the pattern plainly, that each
service has a private database accessible only via its API, and that no
other service can access that database directly (microservices.io, same
page, verified 2026-08-03). The alias Private Database per Service appears
in the same source and in later talks by Richardson as a way to stress the
access-control half of the definition, since the pattern is not really about
how many physical database instances exist but about who is allowed to open
a connection to them.

Sam Newman, in *Building Microservices*, 2nd edition, O'Reilly, 2021, chapter
4, "Splitting the Monolith," and chapter 5, "Data," does not use the exact
phrase Database per Service as a proper noun the way Richardson does, but
describes the identical structural commitment under the heading of
information hiding applied to data, arguing that a service's schema is part
of its internals and that another service reaching into it is exactly the
kind of coupling a service boundary exists to prevent. Newman traces the
underlying idea to the same information-hiding principle David Parnas
described in "On the Criteria to Be Used in Decomposing Systems into
Modules," *Communications of the ACM*, volume 15, issue 12, 1972, which
argued that a module's design decisions, including its internal data
structures, should be hidden from other modules and reachable only through a
defined interface. Neither Richardson nor Newman claims to have invented
data isolation as an idea. What the catalog entry contributes is the specific
name, the placement inside a named pattern language for microservice data
management, and the explicit pairing with its counter-pattern, Shared
Database, which makes the trade-off legible as a choice rather than an
accident.

The pattern also has deep roots in Domain-Driven Design's Bounded Context,
Eric Evans, *Domain-Driven Design*, Addison-Wesley, 2003, part 4, chapters
14 to 16, where Evans argues that a model, and the storage that backs it,
should be scoped to a single bounded context and never shared wholesale
across contexts that hold different meanings for the same terms. Richardson
cites this lineage directly in *Microservices Patterns*, chapter 2, in his
discussion of how to decompose an application by subdomain before deciding
how each resulting service will store its own state.

## 2. Problem and context

A team is decomposing a monolith into services, or is designing a new system
as microservices from the start, per Decompose by Business Capability or
Decompose by Subdomain. Each service is meant to be independently
deployable, independently able to scale, and ownable by one small team without
that team needing sign-off from every other team before it ships a change.
The moment two services read and write the same physical database, that
independence is a fiction. A schema migration in one service can break a
query another service depends on, a heavy analytical query from one service
can starve the connection pool another service needs for its request path,
and a locking decision made for one service's write pattern can stall a
completely unrelated service's writes. The context in which this pattern
becomes necessary is exactly the context that motivated microservices in the
first place, an organization has multiple teams that need to move at
different speeds, and a single shared schema forces them back into lockstep
even after the code has been split into separate deployable units.

The problem this pattern solves is narrower than how microservices store
data in general. It is specifically the coupling that survives a service
split when the data layer is left shared. Splitting the code but not the
data produces what practitioners sometimes call a distributed monolith,
independently deployable processes that are not actually independently
deployable in practice, because every schema change is still a cross-team
negotiation.

## 3. Forces

**Coupling versus consistency.** The strongest force in favor of the pattern
is decoupling. a service's storage schema is an implementation detail that
should be free to change without coordinating with any other team. The
strongest force against it is consistency, since a single relational
database gives you free multi-row, multi-table ACID transactions, which a
set of private databases does not. Richardson names this trade-off directly,
noting that some business transactions need to enforce invariants that span
what are now several services, and that queries needing to join data owned
by different services become substantially harder once that data lives in
different databases (microservices.io, "Database per service," verified
2026-08-03).

**Team autonomy versus operational surface.** Giving every service its own
database lets a team pick the storage technology that fits its access
pattern, a graph store for a recommendations service, a wide-column store
for a time-series service, a plain relational database for a billing
ledger. This is the polyglot persistence force. It is balanced against
operability, since every distinct database technology in production is
another thing to patch, back up, monitor, capacity-plan, and staff for, and
an organization that lets every team choose freely can end up running a
dozen storage engines with a handful of engineers per engine who actually
know how to operate it well.

**Latency versus isolation.** A cross-service query that used to be a single
SQL join is now, at minimum, two network calls and an in-memory join, or a
precomputed read model that has to be kept in sync. The pattern trades local,
low-latency joins for isolation. This is a real cost, not a rounding error,
and it is the single most common reason engineering teams report regretting
a database split done too early.

**Cost.** Running N independently sized, independently backed-up,
independently monitored databases is more expensive in both infrastructure
spend and operational headcount than running one shared cluster, at least
until the shared cluster's blast radius or contention becomes the more
expensive problem. This cost force is genuinely judgement-dependent and
scales with organization size. At ten engineers the operational tax of ten
databases can be the larger cost. At a thousand engineers the coordination
tax of one shared database is usually the larger cost instead.

**Team topology.** The pattern assumes, and reinforces, Conway's Law. teams
that own a service end to end, including its data, ship faster than teams
that must ask a shared DBA group for a schema change. Where an organization
has a centralized data team and no appetite for distributing database
administration into product teams, this pattern fights the existing team
structure rather than fitting it, and the friction shows up as slow adoption
rather than a technical failure.

**Cognitive load.** A developer working in a single service now only needs
to understand one schema, which lowers local cognitive load. The
organization as a whole, however, now needs a mental model of how data flows
between services, which service is the system of record for which fact, and
by what mechanism a fact becomes visible elsewhere, which raises
system-level cognitive load even as it lowers per-service cognitive load.

The pattern favors coupling reduction, team autonomy, and technology fit. It
sacrifices free cross-entity transactions, free cross-entity joins, and
operational simplicity, and it only pays off once the organization is large
enough, or the domain is decoupled enough, that those sacrifices are cheaper
than the coordination cost of a shared schema.

## 4. Applicability and non-applicability

Reach for Database per Service when:

- Two or more teams need to deploy changes to their own service's data model
  without waiting on a shared migration review from another team.
- The services being split genuinely have different data shapes and access
  patterns, such that a single schema, or a single storage technology, is
  already an awkward fit for at least one of them.
- The organization has decomposed by business capability or subdomain first
  (see Decompose by Business Capability and Decompose by Subdomain), so each
  service's data boundary tracks a real domain boundary rather than an
  arbitrary technical split.
- The team has, or is willing to build, the operational capability to run and
  monitor more than one database instance, and has planned for how
  cross-service data needs, queries, reports, consistency, will be met
  without a shared schema, usually via API Composition, CQRS, or an event
  stream.
- The organization needs per-service scaling, so that one service's
  read-heavy traffic cannot starve another service's write-heavy traffic on
  a shared connection pool or shared disk I/O budget.

Do not reach for it when:

- The application is a single team, single deployable monolith with no
  organizational pressure to split ownership. A private database per module
  inside one process buys none of the deployment independence the pattern
  exists for, and pays the query-joining cost anyway. Newman calls this out
  explicitly in *Building Microservices*, 2nd edition, chapter 1, arguing
  that the value of independent deployability is the actual point, and a
  pattern applied without that value being real is pure overhead.
- The domain has genuinely strong, frequent, multi-entity transactional
  invariants that the business cannot tolerate becoming eventually
  consistent, and the organization has no appetite to build or operate a
  Saga, or an equivalent distributed-transaction mechanism, to replace the
  local ACID transaction it would otherwise lose. Splitting the database
  before the team has a plan for the invariant is how correctness bugs get
  introduced silently.
- The team is early in a startup's life and has not yet found product-market
  fit. Richardson's own FTGO example in *Microservices Patterns* is
  explicitly framed as a decomposition to apply once a monolith becomes hard
  to change, not a greenfield default. A one-team startup that splits its
  database on day one is usually paying a coordination tax it does not yet
  have a coordination problem to justify.
- The organization does not have, and is not planning to build, operational
  capacity, backup, monitoring, on-call coverage, capacity planning, for more
  than one database technology or more than a small number of database
  instances. A private database per service that nobody is watching is worse
  than a shared, well-operated one.
- Reporting and analytics are a primary use case and the organization has not
  yet built a data warehouse, change-data-capture pipeline, or equivalent.
  Splitting the operational databases before the analytical read path exists
  turns every report into a bespoke cross-service integration project.

## 5. Structure

**Service.** A single deployable unit that owns exactly one logical data
store. The service is the only thing in the system permitted to open a
direct connection to that store. Every other participant in the system must
go through the service's API.

**Private data store.** The physical or logical storage backing one service.
This can be a dedicated database server, a dedicated schema inside a shared
database server, or a dedicated set of tables inside a shared schema, with
access enforced by database-level permissions. Richardson lists all three
implementation-level variants as valid instances of the same structural
pattern, differing only in how strictly isolation is enforced (microservices.io,
"Database per service," verified 2026-08-03).

**Service API.** The only sanctioned entry point into a service's data.
Every read and every write from outside the service passes through this
API, whether it is a synchronous request-response call or an asynchronous
message.

**Consuming service.** Any other service that needs data owned by a
different service. A consuming service never queries another service's
database directly. It calls the owning service's API, subscribes to events
the owning service publishes, or reads from a materialized view that was
built by consuming those events.

**Cross-service query mechanism.** A separate structural element, not the
core pattern itself but a required companion whenever more than one service
needs to be combined into a single answer. This is usually one of API
Composition, where an aggregating service or gateway calls several service
APIs and joins the results in memory, CQRS, where a separate read model is
built and kept in sync by consuming events from the owning services, or a
data warehouse fed by change-data-capture or an event stream.

## 6. ASCII structure diagram

```
+-------------------------+          +-------------------------+
|   Order Service         |          |   Inventory Service     |
|                         |          |                         |
|  +-------------------+  |          |  +-------------------+  |
|  |  Order API        |  |          |  |  Inventory API    |  |
|  +---------+---------+  |          |  +---------+---------+  |
|            |            |          |            |            |
|            v            |          |            v            |
|  +-------------------+  |          |  +-------------------+  |
|  |  Orders DB        |  |          |  |  Stock DB         |  |
|  |  (private)        |  |          |  |  (private)        |  |
|  +-------------------+  |          |  +-------------------+  |
+------------^------------+          +------------^------------+
             |                                     |
             |  API calls only                     |  API calls only
             |  no direct DB access                |  no direct DB access
             |                                     |
             +------------------+------------------+
                                |
                       +--------v---------+
                       |  Consuming        |
                       |  service or       |
                       |  gateway          |
                       +-------------------+

FORBIDDEN LINK, the anti-pattern this structure exists to block.

  Order Service  ------X----->  Stock DB   (direct cross-service query)
```

## 7. Dynamics

Two runtime flows illustrate how a system built on Database per Service
behaves, a normal request that stays inside one service, and a request that
needs data from two services.

```
Single-service write, the common case
---------------------------------------
Client -> Order API. POST /orders
Order API -> Orders DB. INSERT order row
Orders DB -> Order API. row id
Order API -> Client. 201 Created

Cross-service read, via API composition
------------------------------------------
Client -> Composition Gateway. GET /orders/42/detail
Composition Gateway -> Order API. GET /orders/42
Order API -> Orders DB. SELECT order WHERE id = 42
Orders DB -> Order API. order row
Order API -> Composition Gateway. order JSON

Composition Gateway -> Inventory API. GET /stock?sku=order.sku
Inventory API -> Stock DB. SELECT stock WHERE sku = ?
Stock DB -> Inventory API. stock row
Inventory API -> Composition Gateway. stock JSON

Composition Gateway -> Composition Gateway. merge order + stock
Composition Gateway -> Client. combined JSON

Cross-service write invariant, via choreographed events
-----------------------------------------------------------
Client -> Order API. POST /orders (place order)
Order API -> Orders DB. INSERT order (status = PENDING)
Order API -> Event Bus. publish OrderPlaced{orderId, sku, qty}

Event Bus -> Inventory Service. deliver OrderPlaced
Inventory Service -> Stock DB. UPDATE stock SET reserved += qty
Inventory Service -> Event Bus. publish StockReserved{orderId}
   (or publish StockReservationFailed{orderId} on insufficient stock)

Event Bus -> Order Service. deliver StockReserved
Order Service -> Orders DB. UPDATE order SET status = CONFIRMED
```

The third flow is a minimal Saga, and it is drawn here specifically to show
what replaces the local transaction that a shared database would have given
for free. the invariant that an order is only confirmed if stock was
successfully reserved now spans two private databases and is enforced by an
explicit choreography of events rather than by a database engine's
transaction manager.

## 8. Implementation variants

**Separate database server per service.** The strictest isolation. Each
service runs its own database process, on its own host or its own managed
instance, with its own connection credentials that no other service holds.
This is the variant Richardson lists first and calls the option with the
fewest shared-failure risks, at the cost of the highest operational overhead
(microservices.io, "Database per service," verified 2026-08-03).

**Private schema per service, shared database server.** Multiple services
share one physical database server, but each service is granted its own
schema, and database-level permissions prevent any service's credentials
from reaching another service's schema. This reduces the number of servers
to operate while keeping logical isolation, at the cost of shared blast
radius if the server itself has an incident, and shared resource contention
for CPU, memory, and disk I/O across services.

**Private tables in a shared schema, enforced by convention or by
permission grants.** The loosest and cheapest variant. Tables are prefixed
or namespaced by service, and access is restricted either purely by team
discipline, weakest, and generally not recommended as a long-term state, or
by row-level and table-level grants issued per service credential, stronger.
Richardson notes this variant is the easiest to retrofit onto an existing
shared database as an incremental step, and the easiest for one service to
accidentally violate if grants are not enforced mechanically
(microservices.io, "Database per service," verified 2026-08-03).

**Polyglot persistence.** Any of the above three, but where different
services deliberately choose different storage technologies. A relational
database for a service whose data is naturally tabular and transactional, a
document store for a service whose data is naturally hierarchical and
schema-flexible, a wide-column or time-series store for a service with heavy
write throughput and range-scan read patterns. This is not a separate
structural pattern so much as a consequence that Database per Service makes
possible, since nothing forces every service onto the same engine once each
service's database is private.

**Managed multi-tenant instance with logical isolation.** In cloud-native
deployments, teams increasingly use one managed database service, for
example one managed relational instance or one managed document database
account, but provision a separate database or container per microservice
inside it, relying on the cloud provider's access-control primitives instead
of self-hosted permission management. This is functionally the private
schema variant, implemented on top of managed infrastructure rather than
self-hosted servers, and it is the variant most commonly recommended in the
AWS microservices whitepaper's reference architecture, which frames data
store choice per service as a first-class architectural decision alongside
service boundary design
([AWS, "Implementing Microservices on AWS," whitepaper, published 2023-07-31](https://docs.aws.amazon.com/whitepapers/latest/microservices-on-aws/microservices-on-aws.html),
verified 2026-08-03).

## 9. Known production uses

**Amazon Web Services' own architectural guidance.** AWS's "Implementing
Microservices on AWS" whitepaper recommends that teams organized around the
two-pizza-team model take full ownership of their services, from creation
to deployment and maintenance, which the whitepaper frames as inseparable
from each team choosing and operating its own data store rather than sharing
one across teams (AWS, "Implementing Microservices on AWS," section
"Modernizing to microservices," verified 2026-08-03). This is guidance drawn
directly from AWS's internal experience running services at large scale
under team ownership, and it is published as prescriptive architecture
advice to every AWS customer building microservices on the platform, which
makes it a named, sourced instance of the pattern being recommended as
default practice by a major cloud vendor rather than a theoretical
suggestion.

**Chris Richardson's FTGO reference application.** *Microservices Patterns*,
Manning, 2019, builds its entire running example, FTGO, a food-delivery
platform, around Database per Service as the default for every service in
the decomposition, and the book's companion source code implements Order
Service, Kitchen Service, Delivery Service, Accounting Service, and
Restaurant Service each with their own MySQL schema, using a Saga to keep
the order-placement invariant consistent across them (Richardson,
*Microservices Patterns*, chapter 4, "Managing transactions with sagas," and
chapter 2, "Decomposition strategies"). This is a named, published, working
reference implementation of the pattern, not an abstract description, and it
is the book that also coined the microservices.io catalog entry cited
throughout this document.

**Sam Newman's documented consulting engagements.** In *Building
Microservices*, 2nd edition, O'Reilly, 2021, chapter 5, "Data," Newman
describes multiple real client engagements, without naming the companies
under NDA but describing the pattern as the default recommendation he gives
teams migrating off a shared monolithic schema, and specifically documents
the incremental migration path of first separating schemas logically inside
the existing database server before physically separating the servers, as
the lower-risk on-ramp he has used repeatedly in practice. This is reported
here as Newman's own documented professional practice, not an anonymous
claim, since the book states the recommendation as his personal, repeated
consulting experience rather than a single named case study.

## 10. Consequences

**Positive.**

- Each service's schema can change without a cross-team migration review,
  which removes the single most common source of release-train coordination
  in a shared-database system.
- A service can choose the storage technology that fits its access pattern,
  instead of forcing every domain's data into one engine's shape.
- A service's data volume and query load can be scaled, sharded, or
  replicated independently of every other service's, so one service's
  traffic spike does not degrade another service's latency through shared
  connection-pool or disk contention.
- Failure isolation improves at the storage layer. a corrupted index, a full
  disk, or a runaway query in one service's database does not take down a
  database that other, unrelated services depend on.
- The service's API becomes the only contract other teams need to
  understand, which makes the schema a true implementation detail that can
  be refactored freely as long as the API contract is preserved.

**Negative.**

- Multi-entity transactional invariants that used to be a single database
  transaction now require a Saga, or an equivalent compensating-action
  mechanism, which is strictly more code, more failure modes to reason
  about, and, during the transaction's in-flight window, a period where the
  system is observably inconsistent.
- Queries that join data across services can no longer be a single SQL
  statement. They require API Composition, a duplicated read model kept in
  sync via CQRS, or a downstream data warehouse, all of which add either
  latency, staleness, or both.
- Operational cost rises with the number of independent data stores, more
  backup jobs, more monitoring dashboards, more capacity planning, and, in
  the polyglot case, more distinct technologies engineers need to be
  competent operating.
- Referential integrity enforced by a foreign key in a shared database is
  gone. The equivalent invariant has to be enforced in application code,
  usually by validating references via a synchronous call or by tolerating
  and detecting eventual consistency, which is a real increase in the
  surface area for correctness bugs.
- Reporting becomes harder at a structural level. A report that used to be one SQL
  query against a shared warehouse-shaped schema now needs a purpose-built
  aggregation pipeline.

## 11. Failure modes and misuse

Symptom. A private database that three other services actually query
directly. Cause. The isolation was established as a naming convention or a
team agreement, with no enforcing database permission, and under deadline
pressure a developer on a different team added a direct connection string
because it was faster than building or waiting on an API endpoint. Fix.
Enforce isolation with database-level access grants scoped to the owning
service's credentials, not with a wiki page. If the organization cannot yet
grant per-service credentials, that is a signal the migration is not
actually finished, and the system should be treated, and monitored, as a
Shared Database anti-pattern until it is.

Symptom. A distributed transaction implemented as a chain of synchronous
calls with no compensation logic, that leaves the system in a
half-completed state whenever a downstream call fails. Cause. The team
split the database without first designing the Saga, or equivalent
compensating-transaction mechanism, that the split requires, and treated the
old single-transaction invariant as something that would mostly still work
with synchronous calls. Fix. Design the Saga explicitly, including its
compensating actions for every step that can fail after a prior step has
already committed, before the database split ships, not after the first
production incident surfaces the gap.

Symptom. Report generation that takes minutes and hammers every service's
production API. Cause. An analytics or reporting team, lacking a
purpose-built read path, built a nightly job that calls every service's API
in a loop to reconstruct a wide table, and that job now competes for the
same capacity as real user traffic. Fix. Build a dedicated analytical path,
usually change-data-capture into a warehouse or a CQRS read model, so
reporting reads never touch the operational APIs at production-traffic
priority.

Symptom. Two services silently disagree about the same real-world fact, for
example an order that Order Service believes is confirmed while Inventory
Service still shows the stock as reserved but not consumed, with no
automated detection. Cause. The event-driven synchronization between the
two private databases has a bug, or an event was dropped or processed out
of order, and nothing is watching for the two databases to drift apart.
Fix. Build reconciliation, either a periodic consistency-check job comparing
the two systems' views of the same entity, or idempotent, ordered event
processing with dead-letter handling, and alert on detected drift rather
than discovering it from a customer complaint.

Symptom. The team splits the database on day one of a new product, before
the domain boundaries are understood, and spends the next six months
undoing an over-eager split as the correct boundary turns out to be
different from the first guess. Cause. Applying Database per Service as a
default rather than as a response to an actual coordination problem the
team is experiencing. Fix. Start with a single database, even inside a
service-oriented codebase, and split it once a specific team or a specific
scaling need makes the coupling cost of the shared schema exceed the cost of
splitting it. This mirrors the general caution Newman gives in *Building
Microservices*, 2nd edition, chapter 1, against adopting microservice
patterns before their underlying pain is actually being felt.

## 12. Trade-off matrix

| Force | Database per Service | Shared Database (anti-pattern) | CQRS (as a companion, not a substitute) | Saga (as a companion, not a substitute) |
|---|---|---|---|---|
| Cross-service transactional consistency | Requires an explicit Saga, not free | Free, via a single local ACID transaction | Does not address writes, addresses reads only | Provides eventual consistency with defined compensation, not atomicity |
| Cross-service query and join | Requires API Composition, a read model, or a warehouse | Free, via a single SQL join | Solves reads well, by design | Not applicable, this is a write-side pattern |
| Deployment independence per team | High, schema changes never require cross-team review | Low, every schema change is a shared negotiation | Improves read-side independence only | Improves write-side consistency handling, not deployment coupling |
| Operational overhead | Higher, N stores to run and monitor | Lower, one store to run and monitor | Adds a materialized view to build and keep fresh | Adds orchestration or choreography logic and monitoring |
| Failure isolation | High, one service's storage incident does not affect others | Low, a shared-database incident is an all-services incident | Improves read-path isolation from the write path | Improves failure containment per saga step, with defined rollback |
| Best fit | Multiple teams, decoupled domains, independent scaling needs | Single team, tightly coupled domain, low organizational coordination cost | Any system, once cross-service reads are a real bottleneck | Any system, once cross-service writes need a real invariant |

## 13. Related and incompatible patterns

**Decompose by Business Capability and Decompose by Subdomain.** These are
the patterns that decide where a service boundary goes in the first place.
Database per Service is what happens to the data once that boundary is
drawn. Applying it before the boundary is well understood is how the
over-eager-split failure mode in dimension 11 happens.

**Saga.** The direct companion pattern for writes. Once a multi-entity
transactional invariant can no longer be a single local transaction, a Saga,
choreographed via events or orchestrated by a coordinator, is the mechanism
that replaces it. Database per Service without a Saga plan for its known
invariants is an incomplete migration.

**API Composition.** The direct companion pattern for reads that must join
data owned by more than one service. Where a query needs data from two
services and the join can tolerate the latency of two API calls plus an
in-memory merge, API Composition is the lighter-weight companion to Database
per Service, compared to building a full CQRS read model.

**CQRS.** The heavier-weight companion for reads, used when API Composition's
per-request fan-out is too slow or too expensive, and a precomputed,
continuously updated read model is worth the added infrastructure of an
event pipeline and a separate read store.

**Event Sourcing.** Frequently paired with Database per Service and Saga,
since a service that stores its state as an append-only event log naturally
publishes the same events other services, and CQRS read models, consume to
stay in sync. Event Sourcing is not required by Database per Service, but
the two compose cleanly because both already assume the service's data is
owned exclusively by that service.

**Self-Contained Service.** A broader structural pattern that includes
Database per Service as one of its defining characteristics, alongside UI
ownership and asynchronous-first communication. Every Self-Contained Service
uses Database per Service. Not every service using Database per Service is
necessarily a full Self-Contained Service, since the latter also constrains
UI and communication style.

**Strangler Application.** The migration pattern most often used to
introduce Database per Service into an existing monolith incrementally,
routing traffic for a newly extracted capability to a new service with its
own private store while the old monolith's schema is gradually drained of
that capability's tables.

**Shared Database, incompatible.** This is the pattern's direct opposite and
is listed as incompatible because the two describe mutually exclusive states
of the same system. a table is either exclusively owned and accessed through
one service's API, or it is shared, and a system cannot be in both states
for the same table at the same time. A system can, and often does, have some
tables under Database per Service and others still under Shared Database
during a migration, but that is two patterns applied to two different parts
of the schema, not one pattern applied twice to the same part.

## 14. Refactoring path in and out

**Introducing the pattern into a monolith with one shared schema.** Newman's
documented incremental approach, per *Building Microservices*, 2nd edition,
chapter 5, proceeds in stages rather than as a single cutover. First,
identify the tables a given bounded context or future service actually owns,
by tracing which code paths read and write them. Second, inside the existing
database server, move those tables into a separate schema or namespace, and
change the application code so only the code that will become the new
service still queries them directly, replacing every other caller's direct
query with a call through the future service's planned API, even while both
still run inside the same monolith process. Third, once every remaining
caller goes through the API rather than the shared table, extract the
service into its own deployable process, still pointed at the same database
server but its own schema. Fourth, once the schema is fully decoupled in
code, migrate the schema onto its own physical database server if
operational isolation is also needed. Each stage is independently shippable
and independently reversible, which keeps the migration low-risk compared to
a single big-bang cutover.

At the point where a shared-invariant boundary is crossed, a business rule
that used to be enforced by a foreign key or a single transaction spanning
what will become two services, design the replacement Saga before completing
the physical split, not after. Splitting the tables first and discovering
the missing invariant enforcement in production is the most common way this
refactor introduces a correctness regression.

**Removing the pattern, merging services back together.** This is rarer in
practice than the introduction path, but it happens when a split was made
too early, per the misuse case in dimension 11, or when two services turned
out to change together so often that the coordination overhead of keeping
their databases separate outweighs the isolation benefit. The path runs in
reverse. First merge the two services' code into one deployable, while still
pointed at two separate schemas, replacing the Saga or API Composition calls
between them with in-process function calls. Second, once the in-process
calls are stable, migrate the two schemas onto one physical database server.
Third, merge the schemas, resolving any duplicated or conflicting concepts
that the earlier split had allowed to drift apart, which is frequently the
most labor-intensive step, since the two services' models of overlapping
entities may have grown apart in the time they were separate.

## 15. Testing and verification

Database per Service makes unit and component testing of a single service
easier, because the service's data store can be spun up in isolation, an
in-memory database, a disposable containerized instance, or a test-scoped
schema, without needing the rest of the system running. This is a direct
benefit of the isolation. a test suite for Order Service only ever needs an
Orders database, never a shared fixture that also has to populate Inventory,
Delivery, and Accounting tables to satisfy foreign keys those services no
longer share.

What becomes harder is integration testing across service boundaries.
Because the invariant that used to be enforced by a database transaction is
now enforced by a Saga or by eventual consistency, tests need to cover the
Saga's failure and compensation paths explicitly, not only its happy path.
A useful technique is contract testing at the API boundary, verifying that
Order Service's assumptions about Inventory Service's API match what
Inventory Service actually implements, combined with consumer-driven
contract tools, so that a schema change inside one service's private
database can be verified not to have broken the API contract other services
depend on, without needing every consuming service running in the same test
environment.

For the eventual-consistency window itself, tests should assert on the
system reaching the expected final state within a bounded time, using
polling or an explicit wait-for-event-delivered test double, rather than
asserting on immediate post-write state the way a single-database test
would. A test that asserts an invariant holds immediately after a write, in
a system whose invariant is enforced asynchronously by a Saga, is a test
that will pass in isolation and fail intermittently under real load, which
is the testing-layer version of the reconciliation gap described in
dimension 11.

## 16. Observability signals

Each private database needs the same baseline signals any production
database needs, query latency percentiles, connection pool saturation, disk
and I/O utilization, replication lag if replicated, and slow-query logs.
What Database per Service adds on top of that baseline is cross-service
consistency observability, since the invariants that used to be enforced by
the database engine itself now need to be watched explicitly.

A healthy instance of this pattern shows per-service database metrics that
are each independently interpretable without needing to correlate against
another service's database, a Saga or event-consumer dashboard showing
in-flight transaction counts, completion rates, and compensation rates,
ideally near zero compensations under normal operation, and a reconciliation
job's mismatch-detection metric staying at or near zero, with any nonzero
reading treated as an incident, not background noise.

A failing instance shows a rising number of stuck in-flight Sagas that never
reach either a completed or a compensated state, which usually means an
event was lost or a downstream service is failing silently, a growing
mismatch in a reconciliation job between two services' views of the same
entity, and, if isolation has been violated per the misuse case in dimension
11, unexpected connections to a service's database from a source IP or
service identity that does not match the owning service, which is worth
alerting on directly if the database supports connection-source auditing.

## 17. Security and privacy implications

Database per Service is, on balance, a security improvement over a shared
database, because it narrows the blast radius of a compromised credential.
A leaked credential for one service's database grants an attacker access to
that service's data only, not to every table in the system, which is the
same principle of least privilege applied at the storage layer that the
pattern already applies at the code layer. This also simplifies
data-residency and regulatory scoping, since a service handling
personally-identifiable or otherwise regulated data can have its private
database placed under stricter access controls, encryption requirements, or
even a different physical region, without those requirements leaking onto
unrelated services that happen to share a database server under the old
shared-schema arrangement.

The cost side is that the pattern increases the number of places secrets
must be managed. N private databases means N sets of credentials to
provision, rotate, and audit, instead of one, which raises the operational
burden on whatever secrets-management system the organization uses, and
raises the number of places a misconfigured access grant could silently
create the isolation violation described in dimension 11. Cross-service data
flows, whether via API calls, published events, or a CQRS read model, are
also a new place personal data can end up duplicated across more than one
store, which is a real consideration under regimes like the EU's GDPR. a
right-to-erasure request now has to be fulfilled against every store that
copy of the data has flowed into, not only the original system of record,
and that fan-out needs to be designed for deliberately rather than
discovered during a compliance audit.

## 18. References

1. Richardson, Chris. "Database per service." microservices.io.
   https://microservices.io/patterns/data/database-per-service.html.
   Verified 2026-08-03.
2. Richardson, Chris. *Microservices Patterns*. Manning Publications, 2019.
   Chapter 2, "Decomposition strategies." Chapter 4, "Managing transactions
   with sagas."
3. Newman, Sam. *Building Microservices*, 2nd edition. O'Reilly Media, 2021.
   Chapter 1, "Microservices." Chapter 4, "Splitting the Monolith." Chapter
   5, "Data."
4. Evans, Eric. *Domain-Driven Design, Tackling Complexity in the Heart of
   Software*. Addison-Wesley, 2003. Part 4, chapters 14 to 16, on Bounded
   Context.
5. Parnas, David L. "On the Criteria to Be Used in Decomposing Systems into
   Modules." *Communications of the ACM*, volume 15, issue 12, December
   1972, pages 1053 to 1058.
6. Amazon Web Services. "Implementing Microservices on AWS." Whitepaper,
   published 2023-07-31.
   https://docs.aws.amazon.com/whitepapers/latest/microservices-on-aws/microservices-on-aws.html.
   Verified 2026-08-03.

## Code

What is worth demonstrating in code is not a real database driver, it is the
shape the pattern forces. two services, each holding its own private store
behind a plain map, communicating only through an event bus, never through a
shared table. The samples below model the choreographed Saga from dimension
7. Order Service publishes OrderPlaced, Inventory Service reacts against its
own private stock store and publishes StockReserved or
StockReservationFailed, and Order Service reacts to that outcome against its
own private order store. Neither service ever reads the other's map.

### TypeScript

```typescript
type OrderPlaced = { orderId: string; sku: string; qty: number };
type StockReserved = { orderId: string };
type StockReservationFailed = { orderId: string; reason: string };

class EventBus {
  private handlers: Record<string, Array<(payload: unknown) => void>> = {};
  on(topic: string, handler: (payload: unknown) => void): void {
    (this.handlers[topic] ??= []).push(handler);
  }
  publish(topic: string, payload: unknown): void {
    for (const h of this.handlers[topic] ?? []) h(payload);
  }
}

class InventoryService {
  private stock: Map<string, number> = new Map([["sku-1", 5]]);
  constructor(private bus: EventBus) {
    bus.on("OrderPlaced", (p) => this.onOrderPlaced(p as OrderPlaced));
  }
  private onOrderPlaced(event: OrderPlaced): void {
    const available = this.stock.get(event.sku) ?? 0;
    if (available >= event.qty) {
      this.stock.set(event.sku, available - event.qty);
      this.bus.publish("StockReserved", { orderId: event.orderId } as StockReserved);
    } else {
      this.bus.publish("StockReservationFailed", {
        orderId: event.orderId,
        reason: "insufficient stock",
      } as StockReservationFailed);
    }
  }
}

class OrderService {
  private orders: Map<string, string> = new Map();
  constructor(private bus: EventBus) {
    bus.on("StockReserved", (p) => this.onStockReserved(p as StockReserved));
    bus.on("StockReservationFailed", (p) =>
      this.onStockReservationFailed(p as StockReservationFailed)
    );
  }
  placeOrder(orderId: string, sku: string, qty: number): void {
    this.orders.set(orderId, "PENDING");
    this.bus.publish("OrderPlaced", { orderId, sku, qty } as OrderPlaced);
  }
  private onStockReserved(event: StockReserved): void {
    this.orders.set(event.orderId, "CONFIRMED");
  }
  private onStockReservationFailed(event: StockReservationFailed): void {
    this.orders.set(event.orderId, "CANCELLED");
  }
  statusOf(orderId: string): string {
    return this.orders.get(orderId) ?? "UNKNOWN";
  }
}

const bus = new EventBus();
const inventory = new InventoryService(bus);
const orders = new OrderService(bus);
orders.placeOrder("o-1", "sku-1", 2);
orders.placeOrder("o-2", "sku-1", 10);
console.log(`o-1 status: ${orders.statusOf("o-1")}`);
console.log(`o-2 status: ${orders.statusOf("o-2")}`);
```

### Python

```python
from dataclasses import dataclass
from typing import Callable


@dataclass
class OrderPlaced:
    order_id: str
    sku: str
    qty: int


@dataclass
class StockReserved:
    order_id: str


@dataclass
class StockReservationFailed:
    order_id: str
    reason: str


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[[object], None]]] = {}

    def on(self, topic: str, handler: Callable[[object], None]) -> None:
        self._handlers.setdefault(topic, []).append(handler)

    def publish(self, topic: str, payload: object) -> None:
        for handler in self._handlers.get(topic, []):
            handler(payload)


class InventoryService:
    def __init__(self, bus: EventBus) -> None:
        self._bus = bus
        self._stock: dict[str, int] = {"sku-1": 5}
        bus.on("OrderPlaced", self._on_order_placed)

    def _on_order_placed(self, payload: object) -> None:
        event = payload
        assert isinstance(event, OrderPlaced)
        available = self._stock.get(event.sku, 0)
        if available >= event.qty:
            self._stock[event.sku] = available - event.qty
            self._bus.publish("StockReserved", StockReserved(event.order_id))
        else:
            self._bus.publish(
                "StockReservationFailed",
                StockReservationFailed(event.order_id, "insufficient stock"),
            )


class OrderService:
    def __init__(self, bus: EventBus) -> None:
        self._bus = bus
        self._orders: dict[str, str] = {}
        bus.on("StockReserved", self._on_reserved)
        bus.on("StockReservationFailed", self._on_failed)

    def place_order(self, order_id: str, sku: str, qty: int) -> None:
        self._orders[order_id] = "PENDING"
        self._bus.publish("OrderPlaced", OrderPlaced(order_id, sku, qty))

    def _on_reserved(self, payload: object) -> None:
        event = payload
        assert isinstance(event, StockReserved)
        self._orders[event.order_id] = "CONFIRMED"

    def _on_failed(self, payload: object) -> None:
        event = payload
        assert isinstance(event, StockReservationFailed)
        self._orders[event.order_id] = "CANCELLED"

    def status_of(self, order_id: str) -> str:
        return self._orders.get(order_id, "UNKNOWN")


if __name__ == "__main__":
    bus = EventBus()
    inventory = InventoryService(bus)
    orders = OrderService(bus)
    orders.place_order("o-1", "sku-1", 2)
    orders.place_order("o-2", "sku-1", 10)
    print(f"o-1 status: {orders.status_of('o-1')}")
    print(f"o-2 status: {orders.status_of('o-2')}")
```

### Go

```go
package main

import "fmt"

type OrderPlaced struct {
	OrderID string
	SKU     string
	Qty     int
}

type StockReserved struct {
	OrderID string
}

type StockReservationFailed struct {
	OrderID string
	Reason  string
}

type EventBus struct {
	orderPlacedHandlers    []func(OrderPlaced)
	stockReservedHandlers  []func(StockReserved)
	stockFailedHandlers    []func(StockReservationFailed)
}

func (b *EventBus) OnOrderPlaced(h func(OrderPlaced)) {
	b.orderPlacedHandlers = append(b.orderPlacedHandlers, h)
}

func (b *EventBus) OnStockReserved(h func(StockReserved)) {
	b.stockReservedHandlers = append(b.stockReservedHandlers, h)
}

func (b *EventBus) OnStockReservationFailed(h func(StockReservationFailed)) {
	b.stockFailedHandlers = append(b.stockFailedHandlers, h)
}

func (b *EventBus) PublishOrderPlaced(e OrderPlaced) {
	for _, h := range b.orderPlacedHandlers {
		h(e)
	}
}

func (b *EventBus) PublishStockReserved(e StockReserved) {
	for _, h := range b.stockReservedHandlers {
		h(e)
	}
}

func (b *EventBus) PublishStockReservationFailed(e StockReservationFailed) {
	for _, h := range b.stockFailedHandlers {
		h(e)
	}
}

type InventoryService struct {
	bus   *EventBus
	stock map[string]int
}

func NewInventoryService(bus *EventBus) *InventoryService {
	s := &InventoryService{bus: bus, stock: map[string]int{"sku-1": 5}}
	bus.OnOrderPlaced(s.onOrderPlaced)
	return s
}

func (s *InventoryService) onOrderPlaced(e OrderPlaced) {
	available := s.stock[e.SKU]
	if available >= e.Qty {
		s.stock[e.SKU] = available - e.Qty
		s.bus.PublishStockReserved(StockReserved{OrderID: e.OrderID})
	} else {
		s.bus.PublishStockReservationFailed(StockReservationFailed{
			OrderID: e.OrderID,
			Reason:  "insufficient stock",
		})
	}
}

type OrderService struct {
	bus    *EventBus
	orders map[string]string
}

func NewOrderService(bus *EventBus) *OrderService {
	s := &OrderService{bus: bus, orders: map[string]string{}}
	bus.OnStockReserved(s.onStockReserved)
	bus.OnStockReservationFailed(s.onStockReservationFailed)
	return s
}

func (s *OrderService) PlaceOrder(orderID, sku string, qty int) {
	s.orders[orderID] = "PENDING"
	s.bus.PublishOrderPlaced(OrderPlaced{OrderID: orderID, SKU: sku, Qty: qty})
}

func (s *OrderService) onStockReserved(e StockReserved) {
	s.orders[e.OrderID] = "CONFIRMED"
}

func (s *OrderService) onStockReservationFailed(e StockReservationFailed) {
	s.orders[e.OrderID] = "CANCELLED"
}

func (s *OrderService) StatusOf(orderID string) string {
	if status, ok := s.orders[orderID]; ok {
		return status
	}
	return "UNKNOWN"
}

func main() {
	bus := &EventBus{}
	NewInventoryService(bus)
	orders := NewOrderService(bus)
	orders.PlaceOrder("o-1", "sku-1", 2)
	orders.PlaceOrder("o-2", "sku-1", 10)
	fmt.Printf("o-1 status: %s\n", orders.StatusOf("o-1"))
	fmt.Printf("o-2 status: %s\n", orders.StatusOf("o-2"))
}
```
