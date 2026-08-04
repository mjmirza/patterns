---
name: Monolithic Persistence
slug: monolithic-persistence
family: 18-anti-patterns
category: Anti-Pattern
aliases: [Integration Database, Shared Database, One Big Database, God Schema]
first_described: "Yourdon and Constantine 1979 (common coupling); Fowler 2004 (Integration Database)"
maturity: canonical
related: [repository, unit-of-work, database-per-service, saga, strangler-fig, anti-corruption-layer]
incompatible_with: [database-per-service, event-sourcing-with-service-owned-store]
verified: 2026-08-02
---

# Monolithic Persistence

## 1. Name, aliases, and lineage

The canonical name used in this entry is Monolithic Persistence. It denotes
one physical database, one schema, and one connection pool acting as the
single source of truth for every independently deployable unit in a system,
whether those units are modules inside one process or separately deployed
services. The name is a description of the shape, not a term any single
author coined first, and the literature carries several near-synonyms that
each capture one facet of the same shape.

Martin Fowler names the same shape Integration Database in his bliki entry of
25 May 2004, revised 1 July 2015, defining it as "an integration database is
a database which acts as the data store for multiple applications, and thus
integrates data across these applications"
([Fowler, "IntegrationDatabase"](https://martinfowler.com/bliki/IntegrationDatabase.html),
verified 2026-08-02). Fowler's framing centers the failure on integration,
several separately owned applications reading and writing one schema, and he
states plainly that "most software architects that I respect take the view
that integration databases should be avoided" (same source).

Chris Richardson, writing for the microservices pattern catalog, names the
identical shape Shared Database and defines it in service terms, as "a
(single) database that is shared by multiple services. Each service freely
accesses data owned by other services using local ACID transactions"
([Richardson, "Pattern. Shared database"](https://microservices.io/patterns/data/shared-database.html),
verified 2026-08-02). Richardson's definition is narrower than Fowler's
because it presupposes a service boundary already exists and has been
violated at the data layer, whereas Fowler's definition also covers the
older case of several distinct applications, not necessarily services in the
microservices sense, bolted onto one schema from the start.

The academic root sits one layer below both of these. Common coupling, one
of the coupling categories in structured design, is defined as occurring
"when several modules have access to the same global data," a category
formally catalogued in Larry Constantine, Glenford Myers, and Wayne Stevens,
"Structured Design," IBM Systems Journal, 13(2), 1974, and expanded in Edward
Yourdon and Larry Constantine, Structured Design. Fundamentals of a
Discipline of Computer Program and Systems Design, Prentice-Hall, 1979
([Wikipedia summary, "Coupling (computer programming)"](https://en.wikipedia.org/wiki/Coupling_(computer_programming)),
verified 2026-08-02, citing Stevens, Myers and Constantine 1974 and Yourdon
and Constantine 1979). A shared database is common coupling made physical
and durable. Instead of two modules sharing a mutable global variable for
the length of one process's lifetime, they share a mutable global table for
the lifetime of the business.

God Schema and One Big Database are informal, non-attributable names used in
practitioner talks and blog posts for the same shape when the emphasis is on
the schema itself sprawling to cover every bounded context rather than on
the multiple consumers that read it. This entry treats all four names as one
pattern viewed from four angles. Coupling theory names it common coupling.
Application integration names it Integration Database. Service-boundary
practice names it Shared Database. Schema design practice names it God
Schema.

A useful test separates this pattern from ordinary single-application
persistence. If more than one independently deployed unit writes to the same
table and no single unit is that table's sole owner, the shape described
here is present. If one application, owned by one team, happens to hold many
tables in one schema, it is not, even though the physical topology looks the
same on a database server's process list.

## 2. Problem and context

A system starts with one team, one codebase, and one database, and the fit
is genuinely good. Every table is reachable from every part of the
application because every part of the application is, in truth, one thing.
A query joining orders to customers to inventory is cheap to write and cheap
to run because the database engine can see all three tables in one
transaction and one query plan.

The system then grows the way most systems grow, more teams, more features,
and eventually more independently deployed processes, whether those
processes are called modules, services, or microservices. Each new team
inherits the existing schema because it is already there, it already holds
the data they need, and standing up a second database feels like needless
duplication of infrastructure that already works. A join across three tables
that used to represent one bounded concern now silently represents three
different teams' concerns, and nobody drew a line marking where one team's
authority over the data ends and another's begins.

The problem crystallizes once two of these conditions hold at the same time.
First, more than one independently deployable unit, whether a module with
its own release schedule or a separately deployed service, writes to the same
schema. Second, no single one of those units owns the schema. Each can read
and write tables it did not create and does not fully understand, because
the database imposes no boundary the way an API does. A relational engine's
referential integrity and ACID guarantees make it exceptionally good at
protecting data consistency inside one bounded concern, and exactly as good
at hiding the fact that five unrelated concerns have been merged into one.

The pattern is not, on its own, a database design mistake. It is a mismatch
between organizational and deployment boundaries on one side and data
ownership boundaries on the other. A single team building a single
deployable application with one database is not exhibiting Monolithic
Persistence in the sense this entry treats as an anti-pattern, even though
the physical topology, one process, one schema, looks identical. The
difference is entirely in who is independently changing what, which is why
dimension 4 below spends real space on the non-applicability list.

## 3. Forces

Consistency pulls toward one database. A single relational engine gives
strict, engine-enforced ACID transactions across every table it holds, so a
join or a multi-table update that spans what would otherwise be three
services becomes one transaction with no coordination protocol required.
The moment data moves to three separate stores, cross-store consistency
becomes the application's problem, solved with a saga, an outbox, or
eventual consistency, all of which cost engineering effort a shared database
gets for free.

Query power pulls the same direction. Reporting, ad hoc analytics, and any
query that reasons across what would otherwise be several service
boundaries are trivial against one schema and range from awkward to
genuinely hard once ownership splits, because a cross-service join no longer
exists as a single operation the database can execute.

Autonomy and deployability pull the other way. A team that cannot change its
own table's shape without coordinating with every other team that touches
that table has lost the single most valuable property an independently
deployable unit is supposed to have, the ability to ship a change on its own
schedule. Sam Newman states the underlying design goal plainly, that a
service should be able to change its internal implementation, including its
data store, without breaking its consumers, which requires the data store to
be private to the service (Sam Newman, Building Microservices, 2nd edition,
O'Reilly, 2021, chapter 4, on information hiding and database integration).

Coupling and blast radius pull toward separation as well. Richardson
identifies both a development-time and a runtime cost of a shared database.
He writes that "a developer working on, for example, the OrderService will
need to coordinate schema changes with the developers of other services,"
and at runtime "if [a] long running CustomerService transaction holds a lock
on the ORDER table then the OrderService will be blocked"
([Richardson, "Pattern. Shared database"](https://microservices.io/patterns/data/shared-database.html),
verified 2026-08-02). A schema migration that would be a local, reviewable
change inside one service's boundary becomes a cross-team negotiation, and a
lock held by one consumer's slow query becomes an outage for every other
consumer.

Operability and blast radius pull the same way at the infrastructure level.
One database is one scaling unit, one backup and restore unit, one failure
domain, and one capacity-planning problem for every concern it hosts. A
traffic spike in one bounded concern degrades every other concern sharing
the instance, because they share connection pool slots, IOPS, and cache
memory.

Cost and team topology are the two forces that most often decide which way
a given system should lean, and they are the two forces most catalogs
underweight. Operating N independent databases costs more in infrastructure,
backup tooling, and on-call surface area than operating one, and that cost
is real money and real toil, not merely a theoretical trade-off. A team of
four engineers building one product does not have the staffing to run five
databases well. The pattern favors consistency, query power, and low
operating cost for a small number of teams. It sacrifices autonomy,
deployability, and blast-radius isolation as the number of independently
changing units grows.

## 4. Applicability and non-applicability

Monolithic Persistence, treated as a deliberate architectural choice rather
than an accident, is the right call when the following hold.

- One team, or a small number of teams that release together on one
  schedule, own the entire schema, so there is no coordination cost to
  externalize.
- The domain benefits from cross-cutting, multi-table transactions and
  joins that would be expensive or impossible to keep consistent across
  separate stores, for example a ledger, an inventory system with hard
  consistency requirements, or a small business application where every
  table represents one bounded concern.
- The system's scale does not yet demand independent scaling of different
  concerns, so paying the operational cost of several databases would be
  pure overhead with no corresponding benefit.
- The team is small enough, or new enough, that premature service
  boundaries would be guesses rather than informed decisions, and a single
  schema keeps those boundaries cheap to redraw later. This is the
  "majestic monolith" argument as practiced by teams that deliberately keep
  one codebase and one database for as long as one team can still reason
  about the whole of it.

It is the wrong call, and becomes the anti-pattern this entry documents,
when any of the following hold.

- More than one independently deployed service reads and writes the same
  tables, and no single service is the sole writer of any given table's
  authoritative state. This is Richardson's Shared Database condition
  exactly.
- Two or more teams need to deploy schema changes on independent schedules,
  and today they cannot, because a change to a shared table requires
  coordinating with every other team that touches it.
- The system needs to scale, cache, or choose a storage engine per bounded
  concern, for example a graph store for a recommendation service and a
  column store for analytics, and a single relational schema forces every
  concern onto one engine's trade-offs.
- A regulatory or data-residency boundary requires that one category of
  data, for example payment card data or health records, be isolated with
  its own access controls, encryption at rest, and audit trail, which a
  shared schema makes it structural to enforce and easy to violate by
  accident.
- The team has already split into services along business capability
  lines for every reason except the data layer, so the service boundaries
  exist in code and in deployment pipelines but are undermined the moment
  two services touch the same table.

The single most common misapplication is treating "we already have one
database" as a sufficient reason to keep adding writers to it as the
organization splits into more teams, rather than treating it as a decision
that must be re-evaluated every time a new independently deployable unit is
proposed.

## 5. Structure

Monolithic Persistence has three participants, and the anti-pattern is
precisely the collapse of the boundary between the second and third.

- **The physical store.** One database instance, one schema namespace,
  holding tables that in a well-bounded system would belong to several
  distinct bounded contexts. It enforces referential integrity and
  transactional consistency across all of them uniformly, because the
  engine has no concept of a table belonging to one team and another table
  belonging to a different team.
- **The consumers.** Every independently deployable unit, a module, a
  service, a batch job, a reporting tool, that opens a connection to the
  store and issues queries against it. In a healthy design each consumer
  would own a disjoint subset of tables. In the anti-pattern, consumers'
  table access overlaps.
- **The absent boundary.** What is missing in structural terms is any mediating
  layer, an API, an event stream, a repository interface owned by a single
  service, between a consumer that does not own a given piece of data and
  the consumer that does. The database's own access-control and schema
  mechanisms are the only boundary present, and they were designed to
  protect data integrity within one authority, not to arbitrate between
  several.

The defining structural symptom is a table with more than one writer across
process or deployment boundaries, and a table read directly by a consumer
that did not create it, bypassing any API the owning consumer might expose.

## 6. ASCII structure diagram

```
  Healthy: database per service           Anti-pattern: monolithic persistence

  +------------+   +------------+          +------------+   +------------+
  |  Orders    |   | Inventory  |          |  Orders    |   | Inventory  |
  |  Service   |   |  Service   |          |  Service   |   |  Service   |
  +-----+------+   +-----+------+          +-----+------+   +-----+------+
        |                |                       |                |
        v                v                       v                v
  +-----+------+   +-----+------+          +-------------------------+
  | orders.db  |   | inventory  |          |      shared.db          |
  |  (owned)   |   |   .db      |          |  orders, inventory,     |
  +------------+   |  (owned)   |          |  customers, payments    |
                    +------------+          |  (owned by nobody)     |
                                             +------------+-----------+
        API calls only cross                       ^      ^
        the service boundary                        \      \
                                              +--------+   +-+----------+
                                              | Reporting |  Marketing  |
                                              |  batch job|   Service   |
                                              +-----------+ ------------+
                                              both read and write tables
                                              they did not create, with
                                              no service mediating access
```

## 7. Dynamics

The anti-pattern is invisible in the everyday flow of one working query. It
becomes visible only in the sequence of events across a schema change,
because that sequence exposes exactly how many parties must now agree
before anyone can move.

```
Consistency at write time (works fine, this is not the failure mode)

  OrdersService         Database
       |  BEGIN TRANSACTION  |
       |-------------------->|
       |  INSERT order       |
       |-------------------->|
       |  UPDATE inventory   |
       |-------------------->|
       |  COMMIT             |
       |-------------------->|
       |  200 OK, consistent |
       |<---------------------

Coordination failure at schema-change time (this is the failure mode)

  InventoryTeam    Slack/JIRA    OrdersTeam    ReportingTeam   MarketingTeam
       |                |              |               |             |
       | "renaming      |              |               |             |
       |  stock_qty"    |              |               |             |
       |--------------->|              |               |             |
       |                | "wait, our   |               |             |
       |                |  ORM maps    |               |             |
       |                |  that field" |               |             |
       |                |<-------------|               |             |
       |                | "our nightly |               |             |
       |                |  report      |               |             |
       |                |  breaks too" |               |             |
       |                |<---------------------------- |             |
       |                | "so does our |               |             |
       |                |  dashboard"  |               |             |
       |                |<---------------------------------------- |
       |  migration delayed, cross-team meeting scheduled            |
       |  a change that touches one table now blocks four teams      |

Runtime contention (a second failure mode, at the same shared table)

  CustomerService (long read)     OrderService (write)
       | BEGIN, SELECT ... FOR UPDATE |
       |------------------------------>|
       | (holds row lock, slow report) |
       |                                |  UPDATE orders SET status=...
       |                                |------------------------------>
       |                                |  BLOCKED, waiting on lock
       |                                |  ... timeout ...
       |                                |<------------------------------
```

## 8. Implementation variants

The shape recurs in several concrete forms, and recognizing which one is
present tells a reader how it is likely to have arrived and what the exit
cost will be.

- **Ball-of-mud monolith database.** One application, grown over years,
  where table ownership was never assigned because there was, historically,
  only one team. Splitting the team later without first splitting the
  schema is the single most common way this variant gets created.
- **Deliberate integration database.** A database stood up on purpose as
  the shared record between two or more originally separate applications,
  often to avoid building an integration API. Fowler's original 2004
  description targets exactly this variant.
- **Shared read-model database.** A reporting or analytics database that
  several services write into directly, bypassing their own APIs, on the
  reasoning that direct writes there are read-only in intent and therefore
  low risk. This variant is deceptively low-risk looking because reads
  outnumber writes, but any service that also writes into the reporting
  store for convenience recreates the full anti-pattern, including the
  coupling and locking problems.
- **Enterprise resource planning schema.** A single, vendor-supplied
  central schema deliberately shared across finance, sales, manufacturing,
  and human resources modules, coordinated by one platform. ERP systems
  provide, in Wikipedia's summary, "an integrated and continuously updated
  view of core business processes," commonly built on "a shared database
  managed by a database management system"
  ([Wikipedia, "Enterprise resource planning"](https://en.wikipedia.org/wiki/Enterprise_resource_planning),
  verified 2026-08-02), and the same article records the trade-off
  directly, noting that centralizing "truly independent businesses can
  create unnecessary dependencies" (same source). This variant is often a
  conscious, vendor-endorsed trade of autonomy for integration, not an
  accident, which is worth naming because it shows the pattern is not
  always a mistake. Sometimes it is exactly what a business chose to buy.
- **Shared cache or session store repurposed as system of record.** A Redis
  or similar key-value store, introduced for caching, that a second service
  starts treating as authoritative data rather than a derived, disposable
  copy. The coupling is identical in kind to a shared relational schema even
  though the technology looks nothing alike.

## 9. Known production uses

Shopify ran its entire multi-tenant commerce platform against a single,
increasingly large MySQL database for years, and by 2015 that approach had
reached a hard physical limit, stated directly in Shopify's own account,
"In 2015, it was no longer possible to continue buying a larger database
server for Shopify"
([Shopify Engineering, "A Pods Architecture to Allow Shopify to Scale"](https://shopify.engineering/a-pods-architecture-to-allow-shopify-to-scale),
verified 2026-08-02). The fix Shopify built, the pods architecture, is an
explicit repudiation of the shared-store model, described as "a pod
consists of a set of shops that live on a fully isolated set of
datastores," with the further guarantee that "all shared resources can only
ever communicate to a single pod at a time, we don't allow any actions to
reach across pods" (same source). The earlier design was not multiple
services sharing one schema in Richardson's narrow sense, it was one
growing platform on one database, but it demonstrates the same structural
failure this entry documents. A single shared store becomes the cap on the
whole system's scaling and the single point through which any part of
the platform can take down every other part.

Enterprise resource planning platforms of the kind sold by SAP and similar
vendors are the longest-running, most widely deployed instance of the
deliberate integration-database variant described in dimension 8.
Wikipedia's summary states ERP's central premise as "using a shared
database managed by a database management system" across "finance,
marketing, sales, human resource, and manufacturing applications"
([Wikipedia, "Enterprise resource planning"](https://en.wikipedia.org/wiki/Enterprise_resource_planning),
verified 2026-08-02), and records the documented downside that
"integration of truly independent businesses can create unnecessary
dependencies" (same source). This is the pattern at industry scale, sold as
a product feature, with the coupling cost as a known and accepted trade.

Twitter's original web application was built on Ruby on Rails, a framework
that in its default configuration binds one application to one relational
database ([Wikipedia, "Twitter"](https://en.wikipedia.org/wiki/Twitter),
verified 2026-08-02, confirming the Rails-based implementation of the web
application). As Twitter grew from one Rails application into many
independently operated services, extracting parts of that single-database
application onto separately owned stores was a large part of what the
industry broadly refers to as Twitter's migration away from a Rails
monolith over the following decade. This entry cites only the confirmed
starting condition, one Rails application on one database, rather than
asserting specific unverified internal details of the migration's later
timeline.

## 10. Consequences

The positive consequences are real and are the reason the pattern keeps
getting chosen.

- Cross-table transactions are trivial. The database engine's own ACID
  guarantees cover every table in the schema at no additional engineering
  cost.
- Ad hoc and cross-cutting queries, including reports that span what would
  otherwise be several bounded contexts, are simple SQL rather than a
  distributed query problem.
- Operating one database is cheaper in infrastructure, monitoring, and
  on-call effort than operating several, which matters a great deal for a
  small team.
- There is exactly one place to look for the current state of the system,
  which lowers the cognitive load of debugging for a team that is still
  small enough to hold the whole schema in its head.

The negative consequences are the reason it is catalogued as an
anti-pattern once the applicability conditions from dimension 4 stop
holding.

- Independent deployability is lost. A schema change touching a shared
  table requires coordinating every consumer of that table, which is
  exactly Richardson's development-coupling cost stated above.
- Runtime blast radius grows to the size of the whole schema. A slow query,
  a lock, or a capacity exhaustion event in one bounded concern degrades
  every other concern sharing the store, as in the runtime-contention
  dynamics shown in dimension 7.
- Ownership diffuses until nobody is accountable for a given table's
  correctness, because any consumer with a connection string can write to
  it.
- Testing and local development degrade, because standing up a realistic
  local environment now means standing up the entire schema, rather than
  only the tables one service actually needs.
- Technology choice is frozen to whatever the single engine supports, even
  when a different bounded concern would be served far better by a
  different storage model.
- Migration away from the pattern becomes progressively more expensive the
  longer it persists, because every additional consumer added to the shared
  schema is one more party that must be coordinated during the eventual
  split.

## 11. Failure modes and misuse

**Symptom.** A deploy of service A's schema migration is delayed for days
or weeks while other teams review and adjust their queries.
**Cause.** Service A does not exclusively own the table it is migrating.
Other services query it directly, so the migration is not a local change.
**Fix.** Introduce an API or event stream in front of the table, assign one
service as sole writer, and migrate other consumers to the API before the
next schema change, following the strangler fig pattern at the data layer.

**Symptom.** An unrelated feature's release is blocked by a database
outage or a slow query originating in a completely different part of the
product.
**Cause.** All features share one connection pool, one lock manager, and one
capacity limit, so contention in one bounded concern exhausts resources for
every other concern.
**Fix.** Separate the highest-contention tables onto their own database
first, prioritized by which tables generate the most cross-team lock
contention, rather than attempting a full split at once.

**Symptom.** Two services occasionally disagree about the state of what
should be the same entity, even though both read from the same table.
**Cause.** One service caches or derives a value from the shared table and
another writes to it directly, without either side coordinating on
transaction boundaries or cache invalidation. The shared schema created an
illusion of a single source of truth while the application layer quietly
built two.
**Fix.** Make table ownership explicit and enforce it in code review and,
where the database supports it, in access-control grants. Anything reading
data it does not own goes through the owning service's API, never a direct
query.

**Symptom.** A new hire cannot tell which team is responsible for a given
table, and a bug fix stalls while the right owner is located.
**Cause.** No ownership metadata exists because the schema predates the
current team structure, or the schema was designed by one team when there
was only one team.
**Fix.** Inventory every table against a named owning service before any
further schema change is approved, even if the split itself is deferred.
Ownership on paper is cheaper than ownership in infrastructure and is the
necessary first step toward the latter.

Misuse is distinct from an organic failure mode. A team deliberately avoids
building an integration API between two services because writing directly
to the other service's tables is faster to ship this sprint. This is the
deliberate-integration-database variant from dimension 8 chosen for the
wrong reason, speed over ownership, rather than chosen consciously as a
documented, revisited trade-off. The tell is that nobody can name a
decision date or a reason the coupling was accepted.

## 12. Trade-off matrix

| Force | Monolithic Persistence | Database per Service | Shared Read-Model (CQRS-style projection) |
|---|---|---|---|
| Cross-entity transaction cost | Free, native ACID | High, needs a saga or two-phase process | Not applicable to writes, reads only |
| Schema change coordination cost | High, every consumer must agree | Low, owning service changes alone | Low for the projection, but the projection itself needs its own migration discipline |
| Blast radius of one bad query | Whole schema, every consumer | One service's own store | The projection only, source stores unaffected |
| Operational cost (infra, on-call) | Low, one store to run | High, N stores to run and monitor | Medium, one extra store plus a sync pipeline |
| Cross-cutting query and reporting | Trivial, plain SQL joins | Hard, requires a separate aggregation layer | Purpose-built for exactly this, its whole reason to exist |
| Storage engine fit per bounded concern | None, one engine for everyone | Full, each service picks its own | Full for the projection's engine, source stores unaffected |
| Team autonomy and independent deploy | Low once more than one team writes | High | High for writers, the projection is a read-only dependent |
| Data freshness at the query boundary | Immediate, same transaction | Immediate within one service, stale across services without extra work | Eventually consistent, lag depends on the sync mechanism |

## 13. Related and incompatible patterns

Repository and Unit of Work compose naturally underneath a healthy,
correctly bounded persistence layer, and their absence is not the cause of
Monolithic Persistence, but a Repository that is shared and instantiated by
more than one independently deployed service against the same tables is
simply the anti-pattern wearing a repository-shaped interface. The
repository abstraction hides the anti-pattern from the code that calls it
without removing the coupling underneath.

Database per Service is the direct architectural remedy and the pattern
most catalogs present as the opposite of this entry's subject. Each
independently deployable unit owns its own schema exclusively, and every
cross-service data need goes through that service's API or an event it
publishes, never a direct query.

Saga is the consistency mechanism a system reaches for once Database per
Service removes the free cross-table transaction that Monolithic
Persistence provided. A saga coordinates a multi-step business transaction
across several independently owned stores using compensating actions
instead of a database-level rollback, and it is the direct cost paid for
gaining the isolation that splitting the schema buys.

Strangler Fig is the migration pattern used to move out of Monolithic
Persistence incrementally. New functionality is routed to a new,
independently owned store while old functionality continues reading the
shared schema, and the shared schema's surface area shrinks table by table
until it can be retired, rather than attempting a single large cutover.

Anti-Corruption Layer is the pattern used at the boundary during that
migration, translating between the legacy shared schema's model and a
newly bounded service's model so the new service does not have to adopt the
old schema's shape as its own domain model.

Monolithic Persistence is, in structural terms, incompatible with a genuine
database-per-service architecture and with an event-sourcing design where
each service owns its own append-only store, because both of those patterns
depend on exclusive write ownership as a precondition, and a table with more
than one authoritative writer violates that precondition by definition.

## 14. Refactoring path in and out

Refactoring into the pattern, deliberately, happens by consolidation. When
several previously separate services or applications are merged, or when a
small team explicitly decides the coordination overhead of separate stores
is not yet earning its keep, the correct path is to pick one schema,
migrate the surviving applications' data into it behind a single
transaction boundary, and retire the losing schemas, verifying row counts
and referential integrity at each cutover step rather than trusting a
one-shot bulk migration.

Refactoring out of the pattern, which is the far more common direction in
practice, follows the strangler fig approach at the data layer, applied one
table, or one small cluster of tightly related tables, at a time.

1. Inventory every table against the service that should be its sole
   owner, using actual query logs rather than assumptions, since the
   consumers of a given table are frequently a surprise to the team that
   thinks it owns it.
2. For the highest-contention or most frequently blocked table first, wrap
   direct access behind an API owned by the designated owning service. Any
   consumer that used to query the table directly now calls the API
   instead. This step alone removes the development-coupling cost even
   before any physical data movement happens.
3. Stand up a new, physically separate store for that table, owned
   exclusively by the designated service, and dual-write to both the old
   shared table and the new store for a bounded verification window,
   comparing the two continuously.
4. Cut reads over to the new store once the dual-write comparison shows
   agreement, then stop writing to the old shared table, then drop the
   table from the shared schema.
5. Repeat for the next table or cluster, prioritized by contention and
   coordination cost rather than by convenience, since the tables causing
   the most pain are the ones that pay back the migration cost fastest.
6. Introduce a saga, or accept eventual consistency via an outbox and event
   stream, for any business transaction that used to span tables now living
   in separate stores, before the last shared table is retired, not after.

The refactoring is safe to pause at any table boundary. Unlike an atomic
cutover, this path leaves the system in a working, if intermediate, state
after every completed table migration.

## 15. Testing and verification

Code written against a correctly bounded, single-owner store is easier to
test in isolation, because a test double or an in-memory fake for one
service's own schema is small and self-contained. Code written against a
Monolithic Persistence store is correspondingly harder to test in isolation
precisely because isolation is not something the shared schema offers. Any
realistic integration test needs the full schema populated with data
belonging to every consumer, rather than only the one under test, which is a strong
practical signal that the pattern is present even before anyone inspects
table ownership directly.

Verification that a migration out of the pattern preserved correctness
relies on dual-write comparison, described in the refactoring path above,
run continuously during the transition window rather than as a one-time
check. A row-count match at the moment of cutover says nothing about
whether concurrent writes during the transition were captured correctly by
both the old and new stores.

Contract tests belong at every new API boundary introduced during the
refactor, verifying that the API a formerly direct table consumer now calls
returns data shaped the way that consumer actually needs it, since the API
is frequently the first place anyone has explicitly specified what a given
consumer was actually reading out of the shared table.

Lock-contention and blast-radius symptoms from dimension 11 are testable
under load. A load test that deliberately runs a long-held transaction
against a shared table while measuring latency on an unrelated table's
queries will reproduce the runtime coupling directly and gives a concrete,
reproducible number to justify the migration's priority order.

## 16. Observability signals

A healthy, correctly bounded persistence layer shows per-service database
metrics. Each service's own connection pool utilization, query latency, and
error rate are independently visible and traceable back to one owner.

Monolithic Persistence shows the opposite signature on a dashboard, one
shared connection pool utilization graph that every service's dashboard
links back to, spikes in one service's error rate that correlate in time
with an unrelated service's deploy or batch job, and lock-wait time metrics
on the database engine itself that cannot be attributed to a single owning
service because several services hold locks on the same tables.

The most direct observability signal specific to this pattern is a table
access audit. Instrumenting the database or the query layer to record which
service issued each query against which table reveals, often for the first
time, exactly how many independently deployed consumers touch a given table
and which of them the team assumed nobody but the owner ever queried.
Migration-blocking incidents, tracked as a count of schema-change pull
requests that required sign-off from more than one team, are a useful
leading indicator that quantifies the coordination cost described in
dimension 3 and turns it into a number a team can watch trend downward as
the refactor in dimension 14 proceeds.

## 17. Security and privacy implications

A shared schema means a shared blast radius for access control. Granting a
new service or a new engineer read access to the database in order to serve
one legitimate need routinely grants read access to every other consumer's
data as well, because relational grants are commonly issued at the
database or schema level long before anyone gets around to column-level or
row-level security, and retrofitting fine-grained permissions onto an
already-shared schema is expensive and easy to defer indefinitely.

Regulatory data isolation requirements, payment card data under PCI DSS,
health data under jurisdiction-specific health-privacy law, or personal
data subject to a data-residency requirement, are hard, in structural terms, to
satisfy inside a shared schema, because the audit boundary a regulator
expects, a full accounting of which system touches which category of data,
does not exist when any consumer with a database connection can query any
table. This is a direct, practical consequence of the ERP variant's
documented trade-off in dimension 9, where "integration of truly
independent businesses can create unnecessary dependencies"
([Wikipedia, "Enterprise resource planning"](https://en.wikipedia.org/wiki/Enterprise_resource_planning),
verified 2026-08-02). Those dependencies are precisely the access paths a
security or compliance review has to enumerate and justify.

A single database is also a single high-value target. Compromising one set
of credentials, or one SQL-injection vulnerability in any one of the
consuming applications, exposes every bounded concern's data at once,
whereas a correctly split architecture confines the same compromise to one
service's own store. This paragraph is analytical reasoning about attack
surface, not a claim sourced to any specific documented breach, and is
stated here for the reader to weigh rather than as a recorded incident.

## 18. References

1. Martin Fowler, "IntegrationDatabase," martinfowler.com bliki, published
   25 May 2004, updated 1 July 2015.
   https://martinfowler.com/bliki/IntegrationDatabase.html
   Verified 2026-08-02.
2. Chris Richardson, "Pattern. Shared database," microservices.io.
   https://microservices.io/patterns/data/shared-database.html
   Verified 2026-08-02.
3. Wikipedia, "Coupling (computer programming)," citing Stevens, Myers and
   Constantine, "Structured Design," IBM Systems Journal 13(2), 1974, and
   Edward Yourdon and Larry Constantine, Structured Design. Fundamentals of
   a Discipline of Computer Program and Systems Design, Prentice-Hall, 1979.
   https://en.wikipedia.org/wiki/Coupling_(computer_programming)
   Verified 2026-08-02.
4. Shopify Engineering, "A Pods Architecture to Allow Shopify to Scale."
   https://shopify.engineering/a-pods-architecture-to-allow-shopify-to-scale
   Verified 2026-08-02.
5. Wikipedia, "Enterprise resource planning."
   https://en.wikipedia.org/wiki/Enterprise_resource_planning
   Verified 2026-08-02.
6. Wikipedia, "Twitter," section confirming the Ruby on Rails implementation
   of the web application.
   https://en.wikipedia.org/wiki/Twitter
   Verified 2026-08-02.
7. Sam Newman, Building Microservices, 2nd edition, O'Reilly, 2021,
   chapter 4, on information hiding and database integration. Cited for
   the general design principle that a service's data store should be
   private to that service. Specific page numbers not independently
   re-verified in this pass.

## Code examples

The pattern itself is a database-topology decision, not a language
construct, so the code below shows the same failure mode reproduced as a
runnable, self-contained simulation in three languages, two independent
services sharing one in-memory table, with no mediating API, causing an
uncoordinated write. Each sample was executed locally.

### TypeScript

```typescript
// monolithic-persistence.ts
// Two "services" share one table directly, no owning service, no API.

type OrderRow = { id: number; status: string; total: number };

class SharedDatabase {
  orders: Map<number, OrderRow> = new Map([[1, { id: 1, status: "new", total: 100 }]]);
}

class OrderService {
  constructor(private db: SharedDatabase) {}
  markShipped(id: number): void {
    const row = this.db.orders.get(id)!;
    row.status = "shipped";
    this.db.orders.set(id, row);
  }
}

class MarketingService {
  constructor(private db: SharedDatabase) {}
  applyDiscount(id: number, amount: number): void {
    const row = this.db.orders.get(id)!;
    row.total -= amount;
    this.db.orders.set(id, row);
  }
}

const db = new SharedDatabase();
const orders = new OrderService(db);
const marketing = new MarketingService(db);

orders.markShipped(1);
marketing.applyDiscount(1, 15);

console.log(db.orders.get(1));
// { id: 1, status: 'shipped', total: 85 }
// Both services wrote the same row with no API between them and no
// single owner. Nothing stops MarketingService from shipping an order
// or OrderService from setting a negative total.
```

Run with `npx tsc monolithic-persistence.ts && node monolithic-persistence.js`.

### Python

```python
# monolithic_persistence.py
# Same shared-table shape, no owning service, reproduced in Python.

class SharedDatabase:
    def __init__(self):
        self.orders = {1: {"id": 1, "status": "new", "total": 100}}


class OrderService:
    def __init__(self, db: SharedDatabase):
        self.db = db

    def mark_shipped(self, order_id: int) -> None:
        row = self.db.orders[order_id]
        row["status"] = "shipped"


class ReportingJob:
    def __init__(self, db: SharedDatabase):
        self.db = db

    def zero_out_refunded(self, order_id: int) -> None:
        row = self.db.orders[order_id]
        row["total"] = 0


if __name__ == "__main__":
    db = SharedDatabase()
    orders = OrderService(db)
    reporting = ReportingJob(db)

    orders.mark_shipped(1)
    reporting.zero_out_refunded(1)

    print(db.orders[1])
    # {'id': 1, 'status': 'shipped', 'total': 0}
    # ReportingJob, which should only read, can silently corrupt the
    # order total because no boundary stops it from writing.
```

Run with `python3 monolithic_persistence.py`.

### Go

```go
// monolithic_persistence.go
// Same shape again, no owning service, direct shared-map access.
package main

import "fmt"

type Order struct {
	ID     int
	Status string
	Total  int
}

type SharedDatabase struct {
	Orders map[int]*Order
}

func NewSharedDatabase() *SharedDatabase {
	return &SharedDatabase{Orders: map[int]*Order{
		1: {ID: 1, Status: "new", Total: 100},
	}}
}

type OrderService struct{ DB *SharedDatabase }

func (s *OrderService) MarkShipped(id int) {
	s.DB.Orders[id].Status = "shipped"
}

type BillingBatchJob struct{ DB *SharedDatabase }

func (b *BillingBatchJob) ApplyLateFee(id int, fee int) {
	s := b.DB.Orders[id]
	s.Total += fee
}

func main() {
	db := NewSharedDatabase()
	orders := &OrderService{DB: db}
	billing := &BillingBatchJob{DB: db}

	orders.MarkShipped(1)
	billing.ApplyLateFee(1, 20)

	fmt.Printf("%+v\n", *db.Orders[1])
	// {ID:1 Status:shipped Total:120}
	// BillingBatchJob and OrderService both hold a direct reference to
	// the same row with no service boundary and no API contract between
	// them, so either can change fields the other owns.
}
```

Run with `go run monolithic_persistence.go`.

C#, Kotlin, and Swift are omitted here deliberately. This pattern's failure
mode is a database-topology and organizational-boundary problem, not a
language-idiom problem, and the three samples above already show the same
shape is language-independent. A fourth or fifth language sample would
repeat the same three lines of logic without adding a genuinely new
implementation variant.
