---
name: Shared Database
slug: shared-database
family: 10-microservices
category: Integration
aliases: [Shared Database Per Service, Integration Database, Database As Integration Point]
first_described: "Richardson 2014, microservices.io pattern catalog"
maturity: contested
related: [database-per-service, saga, api-composition, cqrs, strangler-fig]
incompatible_with: [database-per-service]
verified: 2026-08-02
---

# Shared Database

## 1. Name, aliases, and lineage

The canonical name in the microservices pattern literature is Shared Database,
sometimes written Shared Database Per Service to make clear that the sharing
happens across service boundaries rather than within one service. Chris
Richardson catalogs it under exactly this name at microservices.io, in the Data
Management section of his pattern language, with Database Per Service listed as
the companion pattern it is usually contrasted against (https://microservices.io/patterns/data/shared-database.html,
verified 2026-08-02).

Martin Fowler uses a different but overlapping name, Integration Database, in a
bliki entry dated 25 May 2004 and last updated 1 July 2015. Fowler's term is
broader. it covers any database that serves more than one application, whether
those applications are microservices, monolith modules, or entirely separate
products, not only services inside one microservices system
(https://martinfowler.com/bliki/IntegrationDatabase.html, verified 2026-08-02).
The two names describe the same structural idea from two angles. Richardson's
name is scoped to service architecture, Fowler's name is scoped to the
database's role as an integration mechanism. This entry uses Shared Database as
the primary name because that is the term the microservices community settled
on, and treats Integration Database as a synonym drawn from the wider
application-integration literature that predates the microservices vocabulary.

AWS's own modernization guidance calls it the shared-database-per-service
pattern and treats it as a legitimate, named interim architecture for
organizations migrating off a monolith, not merely a mistake to be named and
shamed (https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/shared-database.html,
verified 2026-08-02). Microsoft's Azure Architecture Center takes the opposite
editorial stance and states the rule directly. "Two services shouldn't share a
data store" (https://learn.microsoft.com/en-us/azure/architecture/microservices/design/data-considerations,
verified 2026-08-02, page dated 2022-07-26). The pattern is therefore contested
in the sense the maturity field states. it is real, it is common, and the
practitioner literature disagrees about whether it should be recommended,
tolerated, or actively refactored away.

## 2. Problem and context

A codebase is being decomposed into services, or several teams are building
services that need to see overlapping pieces of business data. Order data and
inventory data both describe the same product. Billing data and shipping data
both need to know whether an order is paid. The team building the new services
inherits a database that already exists, already has referential integrity
enforced by foreign keys, and already has reporting and analytics jobs running
against it. Splitting that database into one database per service means
rewriting every cross-entity query as a network call, replacing every foreign
key with an application-level check, and replacing every multi-table
transaction with a saga or another compensating mechanism. None of that is
free, and none of it can be done on day one of a decomposition project.

The shared database pattern is the answer teams reach for in that moment, not
usually as a considered architectural choice made from a blank page, but as the
path of least resistance when a monolith's database is still there and multiple
new services need data from it. The context that makes this a real problem,
rather than a solved one, is that decomposition is incremental. A team rarely
gets to redesign the whole persistence layer before shipping the first service.
The shared database is what makes the first service shippable quickly, and what
makes the tenth service painful to change.

## 3. Forces

Consistency versus autonomy is the central force. A single database with ACID
transactions gives every service consuming it strong consistency for free, in
the ordinary relational sense of atomic multi-row commits and foreign key
enforcement. The moment two services split the data across two databases, that
consistency becomes eventual, and the team has to build and reason about
compensation logic, retries, and idempotency to recover it. Strong consistency
is convenient. It is also the direct cause of the coupling this pattern is
known for, because the mechanism that gives you free consistency, the shared
schema, is the same mechanism that ties every consumer to every other
consumer's assumptions about that schema.

Development velocity versus runtime isolation is the second force. Operating
one database is genuinely simpler than operating five. one backup strategy,
one connection pool to size, one place to look for slow queries. That
operational simplicity is real and AWS names it explicitly as a reason to
choose the pattern (source above). But the same single database becomes a
single point of runtime contention. A long-running report query in one service
can hold a lock that blocks a write in another service, and neither service's
on-call engineer has visibility into the other service's query patterns.
Operability at the infrastructure layer improves while operability at the
per-service layer degrades.

Migration cost versus migration risk is the third force, and it is specific to
teams doing an incremental decomposition rather than a greenfield build. Moving
a table out of a shared database into a new service-owned database is a data
migration with real risk of downtime, of temporarily inconsistent reads during
the cutover, and of missed foreign key dependents that nobody remembered
existed. Staying on the shared database defers that risk indefinitely, at the
cost of the coupling described above compounding with every service added.

Team topology is the fourth force and the one the pattern's critics weigh most
heavily. Conway's Law observation applies directly. a shared database requires
schema changes to be coordinated across every team whose service touches the
affected tables, which means the database schema becomes a synchronization
point between teams that were supposed to be able to move independently.
AWS's own guidance names this directly as the primary cost. "This creates
development time coupling. this pattern does not reduce dependencies between
development teams" (source above).

Cognitive load is the fifth force, and it cuts in the pattern's favor at small
scale and against it at large scale. A single schema is one thing to hold in
your head. As the number of services sharing that schema grows, the schema
accretes tables, columns, and indexes that serve one service's narrow need but
that every developer touching the database must now understand well enough not
to break.

## 4. Applicability and non-applicability

Reach for a shared database when the team is early in an incremental monolith
decomposition and the alternative is blocking every new service on a data
migration project. Reach for it when the services genuinely need strong,
same-transaction consistency across entities that are difficult to split
cleanly, for example a ledger and its running balance, where a saga's eventual
consistency window is a correctness problem rather than a UX inconvenience.
Reach for it when the number of services touching the shared data is small,
typically two or three, and is unlikely to grow, because the coordination cost
scales with the number of independent teams reading and writing the same
schema, not with the number of tables. Reach for it when the team explicitly
plans this as a transitional state on the way to Database Per Service, as part
of a Strangler Fig migration, and has a concrete trigger condition for when to
split.

Do not reach for it when the services are being built by independent teams
that need to deploy on independent schedules, because schema coordination
across independent release trains is exactly the coupling that erases the
independent-deployability benefit microservices exist to provide. Do not reach
for it when the services have materially different data access patterns, for
example one service needs high-throughput key-value lookups and another needs
complex analytical joins, because a single relational schema optimized for one
access pattern degrades the other. Do not reach for it as a permanent
architecture for a system with more than a handful of services sharing the
same tables, because the coordination cost and the blast radius of a single
outage both grow with the service count and neither growth is bounded. Do not
reach for it when regulatory or data-residency requirements mean different
services must isolate their data at the storage layer, since a shared database
makes that isolation impossible to enforce mechanically. Do not reach for it
purely out of a wish to avoid learning eventual consistency, if the actual
business requirement tolerates it. that trade should be made deliberately, not
by default.

## 5. Structure

The participants are the Shared Database itself, one or more Consuming
Services, and, implicitly, the Schema that the database exposes.

The Shared Database is the single physical or logical database instance that
holds tables belonging conceptually to more than one service's domain. It is
the one component every consuming service depends on directly, and the one
component whose downtime or degradation affects every consuming service at
once.

Each Consuming Service is a service that reads or writes tables in the shared
database using its own connection pool but the same schema definitions as
every other consumer. A consuming service typically owns some tables outright,
in the sense that no other service writes to them, while also reading or
writing tables it does not conceptually own, which is the structural feature
that distinguishes this pattern from Database Per Service.

The Schema is the set of table definitions, foreign keys, indexes, and
constraints that every consuming service must agree on. In this pattern the
schema is not owned by any single service. it is a shared, implicitly-versioned
artifact that changes only when every consuming service's code has been
verified compatible with the change, which is the coordination cost named in
the Forces section.

An optional but common fourth participant is a Migration Tool or schema
version tracker, for example a Flyway or Liquibase migration history table,
which every consuming service's deployment pipeline runs against before that
service can safely assume the schema is at the version its code expects.

## 6. ASCII structure diagram

```
+------------------+       +------------------+
|  Billing Service |       | Shipping Service |
|  (owns nothing   |       | (owns nothing    |
|   exclusively)   |       |  exclusively)    |
+---------+--------+       +---------+--------+
          |                          |
          |  reads/writes            |  reads/writes
          |  orders, payments        |  orders, shipments
          v                          v
   +-----------------------------------------+
   |            Shared Database               |
   |-------------------------------------------|
   |  orders (owned by Order Service, below)  |
   |  payments (owned by Billing Service)     |
   |  shipments (owned by Shipping Service)   |
   +---------+---------------------------------+
             ^
             |  reads/writes orders, payments
             |
   +---------+--------+
   |  Order Service    |
   +--------------------+
```

Every arrow is a direct schema-level dependency. any table any service both
reads and does not own is a coupling point, drawn here as orders, which
Billing and Shipping both read but only Order Service is meant to write.

## 7. Dynamics

```
BillingService              SharedDatabase              ShippingService
     |                            |                            |
     | UPDATE orders               |                           |
     |   SET status='paid'         |                           |
     |   WHERE id='o-1'  --------> | (row lock acquired)        |
     |                            |                            |
     |                            |  <---- SELECT status FROM   |
     |                            |        orders WHERE id='o-1'|
     |                            |        (blocks on lock)     |
     |                            |                            |
     | COMMIT  ------------------>| (lock released)            |
     |                            |------- row returned ------>|
     |                            |                            |
```

The sequence shows the runtime coupling directly. Shipping Service's read of
the same row Billing Service is mid-transaction on blocks until Billing
commits, even though the two services have no network dependency on each
other and neither call the other's API. The dependency is entirely mediated
by the shared table and its lock, which is invisible to both services' own
tracing and logging unless the database's own lock-wait metrics are being
watched.

A second, slower-moving dynamic happens at deploy time rather than request
time. a developer on the Billing team renames the status column to
payment_status as part of an unrelated refactor, tests pass because
Billing's own test suite only exercises Billing's code paths, and the change
ships. Shipping Service's code, which still reads status, now either errors
or, worse, silently reads null and treats every order as unshippable. This
failure mode has no request-time signature at all until the first Shipping
Service call after the Billing deploy, which is why schema changes in this
pattern require cross-team review as a mandatory step rather than a
suggestion.

## 8. Implementation variants

Ownership-tagged shared schema. Every table in the shared database is
explicitly assigned one owning service in documentation, database comments, or
a machine-readable manifest, and only the owning service is permitted to run
migrations against its tables, even though other services may read them
through views or direct queries. This variant does not solve the coupling
problem but makes the current ownership state visible, which is a prerequisite
for eventually extracting each table into its own service database.

Schema-per-service, database-per-server. The database server is shared,
but each service gets its own schema or namespace within it, with database
users scoped so a service's credentials cannot touch another service's schema
even though both live on the same physical instance. AWS's guidance explicitly
distinguishes this from full table sharing. "Services can safely share the
same physical database server. Problems occur when services share the same
schema" per the Azure Architecture Center source above. This variant keeps the
single-instance operational simplicity while removing the schema-level
coupling that causes the coordinated-migration and lock-contention problems,
at the cost of losing cross-service ACID transactions, since most relational
engines cannot commit a single transaction across two schemas the way they can
across two tables in one schema. Some engines, notably PostgreSQL with the
dblink or foreign data wrapper extensions, and most enterprise engines using
two-phase commit, can approximate this, but the operational complexity of
distributed transactions across schemas usually exceeds the complexity a team
was trying to avoid by not doing full database-per-service.

Read-only shared replica. Only one service, the table's owner, writes to
the shared database. Every other service is granted read-only access to a
replica, often via change-data-capture or logical replication rather than a
live read connection to the primary. This variant removes the write-side
coordination and lock-contention problems while keeping the free-consistency
read benefit for consumers who tolerate the replica's replication lag, and is
a common intermediate step on the migration path toward Database Per Service,
since it forces every consumer except the true owner to stop writing before
the schema is physically split.

View-mediated access. Consuming services query a set of database views
rather than the base tables directly. The owning service can then change the
underlying table structure without breaking consumers, as long as it keeps the
view's contract stable, which converts the shared database's implicit schema
contract into an explicit, versionable one, closer in spirit to an API
contract than to raw table access.

## 9. Known production uses

Amazon's own pre-2002 internal architecture is a documented, named case of a
company built directly on the shared database pattern and then deliberately
ending it. Steve Yegge's widely cited internal memo, later leaked publicly,
describes the mandate Jeff Bezos issued that ended the pattern company-wide.
"All teams will henceforth expose their data and functionality through service
interfaces. Teams must communicate with each other through these interfaces.
There will be no other form of interprocess communication allowed. no direct
linking, no direct reads of another team's data store, no shared-memory model,
no back-doors whatsoever." (Steve Yegge, "Stevey's Google Platforms Rant",
2011, https://gist.githubusercontent.com/chitchcock/1281611/raw/, verified
2026-08-02). The memo is retrospective, describing a transformation that
Yegge dates to the early-to-mid 2000s, and it names direct reads of another
team's data store specifically as the practice being banned, which is the
shared database pattern by another name.

AWS Prescriptive Guidance documents shared-database-per-service as a named,
recommended interim pattern inside its own modernization playbook, the
guidance its Professional Services organization uses on real enterprise
migration engagements, complete with the operational caveats about hot tables
and backward-compatible schema changes quoted in section 3 above
(https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/shared-database.html,
verified 2026-08-02). This is a named, sourced, currently-maintained piece of
guidance from a cloud provider whose customers run this pattern in production
at scale, distinct from a single company's internal case study but no less a
real-world use of the pattern as a deliberate architectural choice rather than
an accident.

Microsoft's Azure Architecture Center documents the opposite production
decision inside its own reference architecture for a drone delivery
microservices system, explicitly modeling per-service data stores, Azure
Managed Redis for the delivery service, Azure Data Lake Storage plus Azure
Cosmos DB for the delivery history service, and a separate document store for
the package service, each chosen because "each microservice might also have
unique data models, queries, or read and write patterns. A shared data store
limits each team's ability to optimize data storage for its specific service"
(https://learn.microsoft.com/en-us/azure/architecture/microservices/design/data-considerations,
verified 2026-08-02). This is included as a production use in the negative
sense required by an honest catalog entry. it is a named, sourced,
currently-published reference architecture that rejects the shared database
pattern by design, and its stated reasoning is direct evidence for the forces
in section 3 rather than for the pattern's benefits.

## 10. Consequences

Positive consequences. Cross-entity queries and reports are simple SQL joins
rather than application-level data aggregation across service boundaries.
Referential integrity between entities owned by different services is
enforced by the database engine itself, catching a class of bugs, orphaned
foreign keys, that a distributed system without shared storage has to catch
with application code or accept as eventual-consistency noise. Multi-entity
writes that must succeed or fail together get that guarantee for free from the
database's transaction manager, without a saga, an outbox, or a distributed
lock. Operating one database, one backup schedule, one connection pool budget,
one place to tune indexes, is measurably simpler than operating N databases,
which matters directly for a small team's operational capacity.

Negative consequences. Every schema change becomes a cross-team coordination
event, which slows the exact kind of independent deployment velocity
microservices are usually adopted to gain, as AWS's own guidance states
plainly. Runtime contention, most visibly lock waits from long-running
transactions, couples the latency and availability of every consuming service
to every other consuming service's query patterns, even when those services
have no logical relationship to each other. The single database becomes a
single point of failure and a single scaling ceiling for the whole system,
so a write-heavy service and a read-heavy service can no longer be scaled
independently at the storage layer, only at the application layer. The schema
itself accretes technical debt, because no single team has full authority or
full context to refactor it, and every migration off the pattern gets more
expensive the longer the pattern is in place, since more services accrete more
implicit dependencies on more tables over time.

## 11. Failure modes and misuse

Uncoordinated schema drift. Symptom, a service starts returning null or
throwing a deserialization error for a field that used to work, with no
deploy of that service's own code in the recent history. Cause, another
service's team renamed, dropped, or changed the type of a column the first
service reads, without coordinating the change, because nothing in the system
enforces that coordination mechanically. Fix, require every migration to be
reviewed by every team whose service reads the affected table, enforced by a
CODEOWNERS-style rule on the migration directory, and prefer additive changes,
adding a new column and dual-writing during a transition window, over
destructive ones.

Hot table lock contention. Symptom, p99 latency on an unrelated service
spikes at a time that correlates with a batch job, report, or bulk import
running in a completely different service, with no code change in the slow
service itself. Cause, the batch job holds a long-running transaction or a
full-table scan that takes a lock overlapping rows the other service needs to
read or write, exactly as demonstrated in section 7's sequence. Fix, move
long-running reporting queries to a read replica rather than the primary, and
audit for transactions that hold locks longer than necessary by keeping
transaction scope as small as possible around the actual write.

Silent write-side ownership violation. Symptom, a row's value changes to
something that does not match any of the business rules the row's owning
service enforces, and the owning service's own audit log has no record of
having made that change. Cause, a second service has direct write access to a
table it does not conceptually own, and one of its code paths writes to that
table to work around a missing API rather than calling the owning service.
Fix, revoke write grants on tables from every database user except the owning
service's, so this failure mode becomes a database permission error at write
time instead of a silent data integrity bug discovered later.

The permanent transitional state. Symptom, a shared database that was
adopted explicitly as a temporary step in a monolith decomposition is still in
place, unchanged, three or more years later, and the number of services
depending on it has grown rather than shrunk. Cause, there was no concrete
trigger condition, an owner, or a deadline attached to the migration off the
pattern when it was adopted, so the coordination cost of finally splitting it
now exceeds the coordination cost that motivated adopting it in the first
place. Fix, whenever the pattern is adopted deliberately as an interim state,
record the trigger condition, for example team count reaches four, or table
count reaches twenty, that forces the migration conversation, rather than
leaving the transition to happen on its own.

## 12. Trade-off matrix

| Force | Shared Database | Database Per Service | API Composition over separate stores |
|---|---|---|---|
| Cross-entity consistency | Strong, native ACID transactions | Eventual, requires a saga or compensation | Eventual, and only as strong as the slowest source system |
| Schema change coordination cost | High, every consumer's team must review | Low, each service owns and versions its own schema | Low for storage, but API contract changes still need coordination |
| Runtime isolation between services | Low, shared locks and connection pool | High, an outage in one store does not directly affect another | High for storage, but composition-layer latency couples query performance |
| Cross-entity query complexity | Low, a single SQL join | High, requires application-side aggregation or a dedicated read model | Medium, the composition layer does the join in memory across service calls |
| Operational overhead | Low, one database to run | High, N databases to provision, back up, and monitor | Medium, N databases plus a composition layer to operate |
| Independent service scaling | Low, storage layer scales as one unit | High, each service's storage scales to its own load profile | High for storage, limited by the composition layer's own throughput |
| Migration effort to establish | Low, especially from an existing monolith schema | High, requires splitting data and rewriting cross-entity logic | Medium, requires the split plus building the composition layer |

## 13. Related and incompatible patterns

Database Per Service is the direct alternative and the pattern most catalog
entries define this one in opposition to. every consequence in section 10 and
every failure mode in section 11 is, from another angle, an argument for
migrating to Database Per Service once the team can afford the migration cost.
The two patterns are mutually exclusive for a given table at a given point in
time. a table is either shared or it is not, though a whole system commonly
runs a mix, some tables migrated to Database Per Service and others still
shared, during a Strangler Fig migration.

Saga is the pattern that replaces the free cross-entity ACID transaction this
pattern provides, once the underlying tables are split across service-owned
databases. A team choosing to leave the shared database pattern needs a saga,
or an equivalent compensating-transaction mechanism, for every business
operation that previously relied on a single database transaction spanning
what are now two databases.

API Composition and CQRS are the patterns that replace the free SQL join this
pattern provides for cross-entity reads. once data is split across services,
a query that used to be one join becomes either a request-time composition
across service APIs, or a precomputed read model built by a CQRS-style
projection that listens to events from the owning services and materializes
its own join ahead of time.

Strangler Fig is the migration pattern this entry's applicability section
points to directly. a shared database is frequently the correct, deliberately
chosen state for the tables that have not yet been strangled out of the
monolith, while tables that have already been extracted move to Database Per
Service, so a single system in the middle of a Strangler Fig migration
legitimately runs both patterns side by side, distinguished table by table.

## 14. Refactoring path in and out

Path in, from Database Per Service, happens rarely and almost always
under duress, most often when two services turn out to need much stronger
consistency between their data than eventual consistency can provide and the
saga complexity built to bridge that gap has itself become the maintenance
burden. The refactor is to pick the smaller of the two services' databases,
migrate its data into the larger one, point its code at the merged schema,
and decommission the smaller database, accepting the coupling this entry
describes as a deliberate, documented trade for the simpler consistency
model.

Path out, to Database Per Service, is the far more common direction and
proceeds in five steps. First, assign explicit ownership to every table in
the shared schema, even tables with no clear single owner, since ambiguous
ownership is what allows the pattern's failure modes to persist. Second, for
every table, identify every service that reads or writes it without being the
owner, and replace those direct queries with calls to the owning service's
API, one table at a time, starting with the tables that have the fewest
non-owner consumers. Third, once a table has no non-owner readers or writers
left, physically move it to a new database instance, using logical
replication or change-data-capture to keep the old and new copies in sync
during the cutover window rather than taking a hard downtime cut. Fourth,
replace any cross-table transaction that used to span the migrated table and
a still-shared table with a saga, testing the saga's compensation path
explicitly rather than only its happy path. Fifth, remove the owning
service's access to the old shared database entirely once the cutover is
verified, so a regression cannot silently fall back to the old table. This
sequence mirrors the extraction steps AWS's own Prescriptive Guidance
describes at a higher level in the source cited in section 1.

## 15. Testing and verification

Contract tests between the owning service and its consumers are the single
highest-value testing investment for this pattern, because the failure
mode in section 11 that causes the most production incidents, uncoordinated
schema drift, is exactly what a contract test catches before deploy rather
than after. A contract test in this context asserts that a given query
against a given table returns rows shaped the way a specific consumer expects,
and it is run in the owning team's CI pipeline against every schema migration
before that migration merges, so a breaking rename fails the build instead of
failing a downstream service at runtime.

Schema migration tests should run every pending migration against a snapshot
of production data volume and shape, not against an empty test database,
because lock contention and migration duration are functions of table size,
and a migration that runs instantly against an empty table can lock a
production table for minutes.

Integration tests that exercise two or more services against one shared test
database instance are more valuable here than they are for Database Per
Service, because they are the only test layer that can catch a lock-contention
or transaction-isolation bug, which by definition cannot be reproduced by
either service's isolated unit tests. These tests are slower and more brittle
than unit tests and should be limited to the specific cross-service scenarios
that are known to be risky, rather than run for every code path.

What became harder to test, relative to Database Per Service, is verifying
that a service's own logic is correct in isolation, since a shared test
database means one service's test data setup can leak into another service's
test assertions if the test suite does not carefully scope and clean up its
fixtures per test, which is a discipline shared-schema test suites need and
isolated-schema test suites get for free.

## 16. Observability signals

Per-table lock wait time and lock wait count, broken down by the query or
transaction that is holding the lock and the query that is waiting, is the
single most important metric for this pattern, since it directly surfaces the
runtime coupling described in section 7 that is otherwise invisible to each
service's own tracing. Most relational engines expose this through built-in
views, for example PostgreSQL's pg_locks and pg_stat_activity, or MySQL's
performance schema lock-wait tables.

Connection pool saturation per consuming service, not just for the database
as a whole, distinguishes a genuinely overloaded database from one service
that is misbehaving and starving the others of connections, which is a
distinction the database's own aggregate connection count cannot make on its
own.

Schema version drift alerts, comparing the migration version each running
service instance was built against to the actual current schema version,
catch the case where a service was deployed against an old schema
expectation and the schema has since moved on, which is the earliest possible
detection point for the uncoordinated-drift failure mode in section 11, well
before that service's business logic actually breaks.

A healthy instance of this pattern shows lock wait time near zero outside of
known batch windows, connection pool usage below 70 percent per service at
peak, and zero schema version drift alerts. A failing instance shows lock
wait spikes correlated with unrelated services' deploys or batch jobs, one
service's connection pool starving another's, and schema version drift
alerts that recur every time a migration ships, which signals the
cross-team review step in section 11's fix is not actually being followed.

## 17. Security and privacy implications

A shared database means every consuming service's database credentials
typically have broader access than that service's own business logic needs,
because table-level or row-level grants are coarser and harder to maintain
precisely than the API-level authorization a service-owned database and API
boundary would enforce naturally. This is a real attack surface expansion. a
credential leak or a SQL injection vulnerability in any one consuming service
can potentially reach data belonging to every other service sharing the
database, not just the vulnerable service's own data, unless database-level
grants are scoped tightly per service, which section 8's ownership-tagged
variant is partly designed to make possible.

Data residency and data classification boundaries are difficult to enforce
mechanically in a shared database, since a single schema has no structural
way to guarantee that a table containing regulated personal data is never
joined, in an ad hoc query written by an unrelated service's engineer, against
a table it should never be correlated with. Where regulatory requirements
demand this kind of isolation, for example GDPR data minimization or
sector-specific data residency rules, the shared database pattern makes
compliance a matter of policy and code review discipline rather than a
property the architecture enforces on its own, which is the concrete reason
the applicability section names data-residency requirements as a
disqualifying condition for choosing this pattern.

Audit logging is also weaker by default in this pattern, because a shared
database's native audit log, where one exists, records which database user
made a change, not which business action in which service triggered it,
so distinguishing "Billing Service updated this row as part of a refund" from
"Shipping Service updated this row through a bug" requires the owning
service's own application-level audit trail to be complete and trustworthy,
since the database log alone cannot make that distinction.

## 18. References

1. Chris Richardson. "Pattern. Shared database." microservices.io.
   https://microservices.io/patterns/data/shared-database.html. Verified
   2026-08-02.
2. Martin Fowler. "IntegrationDatabase." martinfowler.com bliki, 25 May 2004,
   updated 1 July 2015. https://martinfowler.com/bliki/IntegrationDatabase.html.
   Verified 2026-08-02.
3. Amazon Web Services. "Shared-database-per-service pattern." AWS
   Prescriptive Guidance, Modernization Data Persistence guide.
   https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/shared-database.html.
   Verified 2026-08-02.
4. Microsoft. "Data considerations for microservices." Azure Architecture
   Center, dated 2022-07-26.
   https://learn.microsoft.com/en-us/azure/architecture/microservices/design/data-considerations.
   Verified 2026-08-02.
5. Steve Yegge. "Stevey's Google Platforms Rant." 2011, publicly archived
   memo describing Amazon's internal service-interface mandate.
   https://gist.githubusercontent.com/chitchcock/1281611/raw/. Verified
   2026-08-02.

## Code examples

The three examples below model the pattern's coupling directly rather than
connecting to a real database engine, so each one runs standalone with no
external service. Each simulates a "shared table" as a single in-memory store
that two services hold a reference to, which is the structural property that
matters for this pattern, not the specific storage engine underneath it.

### TypeScript

Demonstrates the deploy-time failure mode from section 11. Billing Service
renames a field without coordinating with Shipping Service, and Shipping
Service's read silently starts returning the wrong answer.

```typescript
type Order = { id: string; status: string; totalCents: number };

class SharedTable {
  private rows = new Map<string, Order>();
  insert(o: Order) { this.rows.set(o.id, o); }
  get(id: string) { return this.rows.get(id); }
  update(id: string, patch: Partial<Order>) {
    const row = this.rows.get(id);
    if (!row) throw new Error("missing row");
    this.rows.set(id, { ...row, ...patch });
  }
}

class BillingService {
  constructor(private table: SharedTable) {}
  markPaid(id: string) {
    this.table.update(id, { status: "paid" });
  }
}

class ShippingService {
  constructor(private table: SharedTable) {}
  canShip(id: string): boolean {
    const row = this.table.get(id);
    return row !== undefined && row.status === "paid";
  }
}

const orders = new SharedTable();
orders.insert({ id: "o-1", status: "pending", totalCents: 4200 });

const billing = new BillingService(orders);
const shipping = new ShippingService(orders);

console.log("before payment, can ship.", shipping.canShip("o-1"));
billing.markPaid("o-1");
console.log("after payment, can ship.", shipping.canShip("o-1"));

// Billing renames "status" to "paymentStatus" without telling Shipping.
orders.update("o-1", { status: "paid" });
const raw = orders.get("o-1") as any;
raw.paymentStatus = raw.status;
delete raw.status;
console.log("after uncoordinated rename, can ship.", shipping.canShip("o-1"));
```

Compiled with npx tsc, targeting es2020 and commonjs, and run with node.
Actual output, three lines.

```
before payment, can ship: false
after payment, can ship: true
after uncoordinated rename, can ship: false
```

The last line is the bug. Shipping Service's logic never changed, and its own
tests still pass in isolation, but a change made entirely inside Billing's
codebase silently broke it in production.

### Python

Demonstrates the runtime lock-contention failure mode from section 11 using a
lock to stand in for a database row or table lock. One service holds the lock
for a long-running operation while a second, unrelated service waits on the
same lock for an unrelated write.

```python
import threading
import time

shared_table_lock = threading.Lock()
shared_orders = {"o-1": {"status": "pending"}}


def order_service_long_report():
    with shared_table_lock:
        started = time.monotonic()
        time.sleep(0.3)
        elapsed = time.monotonic() - started
        print(f"order-service report scan held table lock for {elapsed:.2f}s")


def inventory_service_write():
    started = time.monotonic()
    with shared_table_lock:
        shared_orders["o-1"]["status"] = "reserved"
    waited = time.monotonic() - started
    print(f"inventory-service write waited {waited:.2f}s for the same table lock")


t1 = threading.Thread(target=order_service_long_report)
t2 = threading.Thread(target=inventory_service_write)
t1.start()
time.sleep(0.05)
t2.start()
t1.join()
t2.join()
print("final row.", shared_orders["o-1"])
```

Run with python3 against the script above. Actual output, three lines.

```
order-service report scan held table lock for 0.30s
inventory-service write waited 0.25s for the same table lock
final row: {'status': 'reserved'}
```

Inventory Service, which has no code dependency on Order Service and does not
call it over the network, still had its write latency dictated almost
entirely by how long Order Service's unrelated report query happened to hold
the shared table's lock.

### Go

Demonstrates the structural coupling directly. two independent service types
share one shared table value, and both are compiled against the same row
schema, which is the shared-schema dependency described in section 5.

```go
package main

import (
	"fmt"
	"sync"
)

type SharedTable struct {
	mu   sync.Mutex
	rows map[string]string
}

func NewSharedTable() *SharedTable {
	return &SharedTable{rows: make(map[string]string)}
}

func (t *SharedTable) Set(id, status string) {
	t.mu.Lock()
	defer t.mu.Unlock()
	t.rows[id] = status
}

func (t *SharedTable) Get(id string) (string, bool) {
	t.mu.Lock()
	defer t.mu.Unlock()
	v, ok := t.rows[id]
	return v, ok
}

type BillingService struct {
	table *SharedTable
}

func (b *BillingService) MarkPaid(id string) {
	b.table.Set(id, "paid")
}

type ShippingService struct {
	table *SharedTable
}

func (s *ShippingService) CanShip(id string) bool {
	status, ok := s.table.Get(id)
	return ok && status == "paid"
}

func main() {
	table := NewSharedTable()
	table.Set("o-1", "pending")

	billing := &BillingService{table: table}
	shipping := &ShippingService{table: table}

	fmt.Println("before payment, can ship.", shipping.CanShip("o-1"))
	billing.MarkPaid("o-1")
	fmt.Println("after payment, can ship.", shipping.CanShip("o-1"))
}
```

Run with go run against the file above. Actual output, two lines.

```
before payment, can ship: false
after payment, can ship: true
```

Java and Rust are omitted here. neither adds a genuinely different angle on
this pattern beyond what the mutex-guarded shared-map model above already
shows, and the pattern's substance is the coupling, not any language-specific
mechanism for holding a database connection.
