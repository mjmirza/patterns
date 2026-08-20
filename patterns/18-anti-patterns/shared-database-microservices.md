---
name: Shared Database Microservices
slug: shared-database-microservices
family: 18-anti-patterns
category: Anti-Pattern
aliases: [Shared Database, Shared Database per Service, Database Monolith in Disguise, Shared Persistence Microservices]
first_described: "Richardson 2018"
maturity: established
related: [database-per-service, saga, api-composition, cqrs, event-sourcing, materialized-view, strangler-fig, distributed-monolith]
incompatible_with: [database-per-service, bounded-context, polyglot-persistence]
verified: 2026-08-02
---

# Shared Database Microservices

## 1. Name, aliases, and lineage

The canonical name for this entry is Shared Database Microservices. It describes
a system that has several deployable services but lets those services read or
write the same operational database tables. The common shorter name is Shared
Database. Chris Richardson's Microservices.io catalog names it "Shared
database" in the context of microservice data architecture and describes
services that freely access data owned by other services through local ACID
transactions (Chris Richardson, "Pattern: Shared database,"
https://microservices.io/patterns/data/shared-database.html, verified
2026-08-02). AWS Prescriptive Guidance uses the name
"shared-database-per-service pattern" for the same shape, where several
microservices use the same database and must coordinate schema changes (AWS
Prescriptive Guidance, "Shared-database-per-service pattern,"
https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/shared-database.html,
verified 2026-08-02).

In this repository the entry is classified as an anti-pattern, not because a
shared database is always wrong, but because the phrase "microservices" promises
independent service ownership. Microsoft Learn says that microservices differ
from traditional centralized data-layer models by owning their own data or
external state and communicating through published APIs (Microsoft Learn,
"Microservices architecture style,"
https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/microservices,
verified 2026-08-02). When services share the same tables, the runtime topology
looks distributed while the change boundary is still centralized.

The lineage comes from the data-management chapter of the microservices
movement. Richardson covers database-per-service, shared database, saga, API
composition, and CQRS as related data patterns in *Microservices Patterns*,
Manning, 2018, chapter 4, "Managing transactions with sagas." The public
Microservices.io pages verify the naming, the basic forces, and the benefits
and drawbacks of the shared database form. AWS and Microsoft later documented
the same split in cloud architecture guidance, with AWS presenting both
database-per-service and shared-database-per-service as migration choices, and
Microsoft presenting service-owned data as the target for microservices
architecture (AWS, "Database-per-service pattern,"
https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/database-per-service.html,
verified 2026-08-02; Microsoft Learn, "Data considerations for microservices,"
https://learn.microsoft.com/en-us/azure/architecture/microservices/design/data-considerations,
verified 2026-08-02).

The aliases matter because each one points at a different failure story.
"Shared Database" is the neutral catalog term. "Shared Database per Service" is
the migration-stage wording used by AWS. "Database Monolith in Disguise" is the
diagnostic phrase teams use when service extraction has left the data model
unchanged. "Shared Persistence Microservices" is less common, but it helps in
systems where the shared store is not SQL, for example a shared document
collection or a shared key-value namespace.

## 2. Problem and context

A team extracts code from a monolith into several independently deployed
services. Order logic moves to an Order service. Billing logic moves to a
Billing service. Customer profile logic moves to a Customer service. The
deployment graph now has service names, containers, health checks, and separate
pipelines. The database, however, is still one operational schema. The Order
service reads customer credit rows. The Billing service updates order status.
The Customer service joins against order history. Every team can run SQL against
tables whose meaning belongs to another team.

The move feels practical at first. Local SQL joins are fast. Local ACID
transactions are familiar. Existing reports keep working. The team avoids a
large data migration during an already risky service split. AWS lists these as
real reasons for using the shared-database-per-service pattern during
modernization, including low refactoring effort, one database to operate, and
interdependencies that make database-per-service hard to adopt (AWS
Prescriptive Guidance, "Shared-database-per-service pattern," verified
2026-08-02).

The problem appears later, when the service boundary needs to earn its cost. A
database column cannot be renamed until every service and every batch job has
changed. A long transaction in one service blocks a hot table used by another.
A service that should scale independently still waits on the shared database's
connection pool, locks, migration window, and backup policy. A security review
finds that a service has read access to tables far outside its business role.
Microsoft's data guidance states the underlying rule plainly: two services
should not share a data store, and trouble starts when services share schemas or
read and write the same tables (Microsoft Learn, "Data considerations for
microservices," verified 2026-08-02).

Engineering judgement. This anti-pattern is most damaging when the organization
also expects team autonomy. If one team owns all services and deploys them
together, the shared database is often only a modular monolith with extra
processes. If five teams own the services and plan independently, the database
has become the real integration API, but without versioning, access contracts,
or consumer visibility.

## 3. Forces

Engineering judgement. The anti-pattern is attractive because it favors short
term delivery and immediate consistency, then charges the cost through change
coordination, operational blast radius, and weak ownership.

- **Latency.** Favored at first. A local SQL join inside one database is often
  faster than calling another service, waiting for an event projection, or
  composing a response through an API gateway. The sacrifice is that the latency
  dependency is hidden behind database load, locks, query plans, and connection
  pools rather than appearing as a service call.
- **Coupling.** Sacrificed. A table name, column type, foreign key, trigger, or
  view becomes a cross-service contract. AWS says schema changes in this pattern
  create development-time coupling and require coordination among services (AWS
  Prescriptive Guidance, "Shared-database-per-service pattern," verified
  2026-08-02).
- **Consistency.** Favored for invariants that fit one database transaction.
  The database can commit or roll back multiple table changes together.
  Richardson's catalog names local ACID transactions as the main benefit of the
  shared database approach (Microservices.io, "Pattern: Shared database,"
  verified 2026-08-02). The sacrifice is that domain ownership becomes unclear:
  every service can enforce, bypass, or accidentally duplicate another service's
  rules.
- **Operability.** Mixed. One database is easier to back up, patch, observe, and
  staff than many stores. It is also one shared failure domain. Microsoft says a
  data store failure in one database-per-microservice model does not directly
  affect other services, which is the isolation this anti-pattern gives up
  (Microsoft Learn, "Cloud-native data patterns," verified 2026-08-02).
- **Cost.** Favored early. One database license, one managed instance, one set
  of backups, and fewer migration projects. Later cost appears as coordination
  time, incident blast radius, and platform work needed to separate access.
- **Team topology.** Sacrificed when teams are separate. A team cannot own its
  service if another team can change its tables or depend on its private schema.
  Microsoft defines microservices as small, independent, loosely coupled
  components owned by small teams (Microsoft Learn, "Microservices architecture
  style," verified 2026-08-02).
- **Cognitive load.** Favored for a small system, because every fact is in one
  place and a developer can answer questions with SQL. Sacrificed in a mature
  system, because the call graph is incomplete unless it includes database
  queries, triggers, reports, migrations, and unowned table reads.
- **Data fit.** Sacrificed. One database engine and one schema style must serve
  transactional writes, search, graph traversal, read-heavy projections,
  analytics extracts, and retention rules. Microsoft and AWS both describe
  database-per-service as allowing each service to choose storage that fits its
  workload (Microsoft Learn, "Cloud-native data patterns," verified
  2026-08-02; AWS Prescriptive Guidance, "Database-per-service pattern,"
  verified 2026-08-02).

## 4. Applicability and non-applicability

Use Shared Database Microservices only as a conscious stage, and write down the
exit rule when it is chosen.

- **A legacy decomposition needs a low-risk first cut.** Services can be split
  around code first while the data boundary is measured. AWS explicitly lists
  low refactoring appetite and difficult interdependencies as reasons a team may
  choose this pattern (AWS Prescriptive Guidance, "Shared-database-per-service
  pattern," verified 2026-08-02).
- **A single team owns the whole system and deploys all services together.** The
  autonomy claim is weak, but the operational model may still be rational. In
  that case, call it a distributed modular monolith, not mature microservices.
- **The shared database is read-only reference data.** Country codes, tax-rate
  tables, feature flags, and product catalogs sometimes start as shared reads.
  This is lower risk when there is one writer, read contracts are versioned, and
  readers do not join back into writer-owned tables.
- **A transaction invariant is legally or financially hard to relax.** A shared
  transaction may be a temporary bridge while the team designs a saga,
  reservation model, or escrow model. Treat the transaction as debt with an
  owner.
- **The services share only a physical database server, not tables or schemas.**
  Microsoft states that services can safely share a physical server and that
  problems occur when they share schemas or the same tables (Microsoft Learn,
  "Data considerations for microservices," verified 2026-08-02). This is a
  deployment optimization, not the anti-pattern.

Do NOT use it in the following cases.

- **Independent deployment is a stated goal.** Shared schema access means every
  table change may need consumer coordination, so independent deployment becomes
  conditional on database compatibility windows.
- **Different teams own different business capabilities.** A shared table
  turns into a negotiation surface where no team can change its model without
  asking unknown consumers.
- **The service needs a different storage model.** A fraud service may need a
  graph or feature store, a search service may need an inverted index, and an
  order service may need relational constraints. One shared relational schema
  forces compromise.
- **The service has stricter privacy, retention, or compliance rules.** If one
  service handles consent or regulated identifiers, broad database access makes
  least privilege hard to prove.
- **The database is already a bottleneck.** Splitting compute while keeping one
  write primary does not remove write saturation, lock contention, or connection
  exhaustion.
- **Cross-service queries are the only reason.** API composition, CQRS
  projections, materialized views, search indexes, and analytical replicas all
  answer cross-domain reads without letting every service own every join.
- **The boundary is unclear.** If the team cannot say which service owns each
  table, the database is the first design problem to solve. Adding deployables
  will not make the ownership clearer.
- **The organization lacks migration discipline.** Shared databases require
  backward-compatible schema changes, consumer discovery, staged rollout, and
  rollback. Without those practices, the shared store will freeze change.

## 5. Structure

The participants are named by the responsibility they carry in the anti-pattern.

- **Service A, Service B, Service C.** Independently deployed processes with
  separate runtime ownership. They expose APIs, jobs, or event consumers, but
  they also open direct database connections.
- **Shared Operational Database.** The single system of record for tables used
  by multiple services. It may be one schema, several schemas in one database,
  or one database server with access controls so broad that service boundaries
  are not real.
- **Shared Tables.** Tables whose columns, indexes, constraints, and meanings
  are consumed by more than one service. These are the real integration points.
- **Database Migration Pipeline.** The schema change path. It now has to account
  for all service versions that may be live during a deployment.
- **Human Coordination Layer.** The meetings, ownership spreadsheets, Slack
  threads, migration calendars, and release freezes needed because the database
  does not know the service boundary.
- **Hidden Consumers.** Reports, notebooks, background jobs, data exports, and
  older service versions that read the same tables but may not appear in the
  service catalog.

The defining relationship is direct table access across ownership boundaries. A
service may call another service's API and still be a participant in the
anti-pattern if it also reads or writes the other service's tables. The API is
then documentation for polite consumers, while the database remains the path for
power consumers.

## 6. ASCII structure diagram

```
       +----------------+       +----------------+       +----------------+
       | Order Service  |       | Billing Service|       | Customer Svc   |
       |----------------|       |----------------|       |----------------|
       | owns order API |       | owns invoices  |       | owns profiles  |
       | opens DB conn  |       | opens DB conn  |       | opens DB conn  |
       +-------+--------+       +-------+--------+       +-------+--------+
               |                        |                        |
               | SQL                    | SQL                    | SQL
               v                        v                        v
       +---------------------------------------------------------------+
       |                 Shared Operational Database                   |
       |---------------------------------------------------------------|
       | orders      customers      invoices      payments      views  |
       | FK links    triggers       stored procs   shared indexes      |
       +---------------------------------------------------------------+
               ^                        ^                        ^
               |                        |                        |
       +-------+--------+       +-------+--------+       +-------+--------+
       | Report Job     |       | Migration Job  |       | Notebook      |
       | hidden reader  |       | schema writer  |       | ad hoc reader |
       +----------------+       +----------------+       +----------------+

       The database, not the service API, is the strongest coupling point.
```

## 7. Dynamics

Runtime flow is simple until change arrives. The simplest read path is a local
join. The hardest path is a schema change, because the database migration has
to be compatible with old service code, new service code, batch jobs, and
hidden readers.

```
Order Service        Shared DB          Billing Service      Customer Service
     |                   |                    |                    |
     | begin tx          |                    |                    |
     |------------------>|                    |                    |
     | read customers    |                    |                    |
     |------------------>|                    |                    |
     | read invoices     |                    |                    |
     |------------------>|                    |                    |
     | insert order      |                    |                    |
     |------------------>|                    |                    |
     | commit            |                    |                    |
     |------------------>|                    |                    |
     |                   |                    |                    |
     |                   |<--- long query ----|                    |
     |                   | holds lock         |                    |
     |                   |                    |                    |
     | update order      |                    |                    |
     |------------------>| waits on lock      |                    |
     | timeout           |                    |                    |
     |<------------------|                    |                    |
     |                   |                    |                    |
     | deploy migration  |                    |                    |
     |------------------>| column changes     |                    |
     |                   |                    | stale query breaks |
     |                   |                    |<-------------------|
```

During normal operation, this path hides a service dependency inside SQL. During
an incident, the owner of the waiting request has to diagnose a database lock
held by another service. During a schema change, the owner has to find every
consumer of the table before the change can be made. Datadog's migration writeup
describes this discovery step as analyzing query samples and checking domain
clusters with engineers across more than 30 teams before creating private
schemas and removing broad access (Datadog Engineering, "Breaking up a
monolith: How we're unwinding a shared database at scale,"
https://www.datadoghq.com/blog/engineering/unwinding-shared-database/,
verified 2026-08-02).

## 8. Implementation variants

**One schema, one database user.** Every service connects with the same database
credentials and can query all tables. It is the fastest form to start and the
hardest form to audit. Ownership is social, not technical.

**One schema, separate service users.** Each service has its own database user,
but privileges are still broad. This gives telemetry by user and lets teams
start revoking access. Datadog describes tracking connection use and reducing
access as a phase in its shared database separation work (Datadog Engineering,
"Breaking up a monolith," verified 2026-08-02).

**Schema per domain in one database.** Tables are grouped into domain schemas,
often with one writer and many readers. This is a useful migration stage because
it makes ownership visible. It remains the anti-pattern if other services still
read or write those schemas directly instead of using APIs, events, or
projections.

**Read-only shared tables.** A service owns writes while other services read.
This is safer than shared writes, but it still couples readers to the table
shape. Versioned views, read replicas, or event-built projections reduce the
risk.

**Shared database with stored procedures as service boundary.** Services call
stored procedures rather than reading tables directly. This hides schema shape
better than ad hoc SQL but moves domain logic into the database. It can become
the Busy Database anti-pattern when the database also owns workflow and policy.

**Shared event log or collection.** In NoSQL stores the same problem appears as
multiple services writing the same collection, topic-compacted log, bucket, or
key prefix. The lack of a relational schema does not remove ownership coupling.

**Temporary strangler bridge.** A new service reads the old monolith database
while the team adds an API, event stream, or projection. This can be a rational
step in a Strangler Fig migration. It becomes the anti-pattern when the bridge
has no deletion date.

**Physical server sharing without logical sharing.** Several service-owned
databases can sit on the same database server or managed cluster. This is not
the anti-pattern when each service has a private schema or database, separate
credentials, and no direct access to another service's tables. Microsoft makes
this distinction explicit in its data guidance (Microsoft Learn, "Data
considerations for microservices," verified 2026-08-02).

## 9. Known production uses

The examples below are named production systems where public sources describe a
shared operational database and the work to move away from it or constrain it.
They are not endorsements of the anti-pattern as an end state.

**Datadog.** Datadog Engineering describes a large shared relational database
used across many teams, with problems such as database upgrades that need broad
coordination, schemas acting as APIs, noisy neighbors, and teams unable to know
who depends on their tables. Their migration plan uses logical separation,
access reduction, and physical separation, with Postgres as the database and
PG Proxy plus OrgStore as migration support. The article states that Phase 1
ran from Q1 2024 to mid Q1 2025, Phase 2 continues through 2026, and Phase 3
also continues through 2026 (Datadog Engineering, "Breaking up a monolith,"
https://www.datadoghq.com/blog/engineering/unwinding-shared-database/,
verified 2026-08-02).

**GitLab.com.** GitLab described its production architecture before
decomposition as one PostgreSQL database cluster storing almost all data
generated by GitLab.com users, with the single primary limiting write scaling.
The CI decomposition project split CI tables from the main database, and GitLab
reported that all developed capabilities for the split were already running in
production before the final cutover. GitLab later documented `main`, `ci`, and
`sec` as decomposed databases for GitLab.com (GitLab, "Decomposing the GitLab
backend database, Part 1,"
https://about.gitlab.com/blog/path-to-decomposing-gitlab-database-part1/,
verified 2026-08-02; GitLab Docs, "Multiple Databases,"
https://docs.gitlab.com/development/database/multiple_databases/, verified
2026-08-02).

**Samsung Account.** AWS's Samsung case study describes Samsung Account as the
gateway for Samsung devices and services, including Bixby, SmartThings, and
Samsung Pay, with 1.1 billion users and about 400 million active users. The
case study says Samsung wanted a microservices architecture and needed to move
away from a central Oracle database by breaking databases into sections suited
for microservice use. The migration used AWS Database Migration Service and
Aurora PostgreSQL compatibility across EU, China, and US migrations (AWS Case
Study, "Samsung Migrates 1.1 Billion Users across Three Continents from Oracle
to Amazon Aurora with AWS Database Migration Service,"
https://aws.amazon.com/solutions/case-studies/samsung-migrates-off-oracle-to-amazon-aurora/,
verified 2026-08-02).

## 10. Consequences

Engineering judgement. The positive consequences are real, especially early in
a migration. The negative consequences grow with team count, traffic, and the
number of hidden consumers.

Positive.

- Local ACID transactions can protect invariants that span several tables while
  the domain split is still immature.
- Cross-domain reads are easy to write and can be fast because they use local
  joins instead of service calls or asynchronous projections.
- One database is easier to operate than many stores when the team lacks a data
  platform.
- Existing reports, exports, and back-office tools can keep running during the
  first phase of service extraction.
- The team can learn real access patterns before choosing final data
  boundaries. Query logs can reveal which tables belong together.
- Rollback can be simpler during a strangler migration because old and new code
  still observe the same state.

Negative.

- The service API is no longer the only contract. Tables, columns, indexes,
  constraints, triggers, and stored procedures are also public contracts.
- Independent deployment weakens because schema changes must tolerate multiple
  service versions and unknown readers.
- Runtime failures cross service boundaries through locks, pool exhaustion,
  slow queries, replication lag, and backup pressure.
- Least privilege is hard to prove when services hold broad database roles.
- The database engine is chosen once for all services, even if workload needs
  diverge.
- Ownership becomes ambiguous. A table touched by five services often has no
  real owner until an incident forces a decision.
- Migration away is expensive because every direct SQL dependency has to be
  found, replaced, tested, and observed.
- Product teams can avoid designing domain events or read models because the
  shared join remains convenient.

## 11. Failure modes and misuse

Engineering judgement. These triples name symptoms an operator, reviewer, or
team lead can observe without reading every line of code.

**Symptom.** A harmless column rename needs a release train with five services,
two report jobs, and a manual checklist. **Cause.** The column is a shared
contract, but the contract has no versioning or consumer registry. **Fix.** Add
expand and contract migration rules, instrument query consumers, publish a
versioned API or projection, then revoke direct reads.

**Symptom.** One service times out while another service runs a report or batch
job. Database metrics show lock waits or saturated connections. **Cause.** The
services share runtime resources and hot tables. **Fix.** Move reporting to a
replica or warehouse, add per-service database users and pool limits, then split
the owning tables or build a read model.

**Symptom.** A service deploy passes its own tests but breaks a different
service after migration. **Cause.** The first service changed shared schema
shape without testing consumers. **Fix.** Add cross-service schema compatibility
tests, block destructive migrations until old service versions age out, and
move consumers behind owner APIs.

**Symptom.** Security review finds a service can read customer consent,
payment, or identity tables that it does not need. **Cause.** Broad database
roles were copied from the monolith. **Fix.** Create one database identity per
service, grant only owned tables first, grant temporary reads with expiry dates,
and alert on direct access to protected schemas.

**Symptom.** No team will approve deleting an old table because nobody knows
who reads it. **Cause.** Hidden consumers use SQL outside the service catalog.
**Fix.** Turn on query sampling, tag connections by service, alert on reads,
and require owners for every table before deletion.

**Symptom.** A new service becomes a thin SQL wrapper around another service's
tables. **Cause.** The team extracted deployment units before defining bounded
contexts. **Fix.** Collapse the service back into the owner or give it an
owned model, owned API, and owned data store.

**Symptom.** Engineers keep adding foreign keys across service areas because
the database permits it. **Cause.** The data model still treats the system as
one normalized schema. **Fix.** Replace cross-domain foreign keys with owner
IDs, domain events, reconciliation jobs, or explicit consistency checks.

**Symptom.** A service cannot scale independently even after compute replicas
are added. **Cause.** The bottleneck is the shared write primary, a shared hot
index, or a global connection pool. **Fix.** Measure write ownership by table,
split the hottest domain first, and route that domain to its own store.

## 12. Trade-off matrix

Compared against named alternatives across the forces from dimension 3.

| Force | Shared Database Microservices | Database per Service | API Composition | CQRS with Materialized Views | Saga | Modular Monolith |
|---|---|---|---|---|---|---|
| Latency for cross-domain reads | Low when a local join works | Medium to high unless data is local | Medium, depends on downstream calls | Low for reads after projection catch-up | Not a read pattern | Low inside one process |
| Coupling | High through schema and locks | Low through service APIs and events | Medium through API contracts | Medium through event contracts | Medium through commands or events | High inside codebase, lower ops cost |
| Consistency | Strong inside one database transaction | Local per service, cross-service eventual | Read-time composition only | Read model is delayed | Coordinates multi-step writes | Strong if one database remains |
| Operability | One store, one shared blast radius | Many stores, smaller blast radius | More service calls to observe | Projection lag and replay to observe | Compensation and retries to observe | One deployable or release unit |
| Cost | Low early, high coordination later | Higher platform cost | Moderate runtime and testing cost | Higher data duplication cost | Higher design and failure handling cost | Lower distributed systems cost |
| Team autonomy | Weak when teams share tables | Strong when ownership is real | Moderate, consumers depend on APIs | Stronger for readers | Stronger for writers after design | Weak if many teams share one codebase |
| Cognitive load | Low at first, high once consumers hide | Medium, ownership is visible | Medium, call graph is visible | High, projections and lag exist | High, failure paths are explicit | Medium, fewer network edges |
| Data fit | One database style for all | Per-service storage choice | Does not decide storage | Read stores can differ from write stores | Does not decide storage | One model unless split internally |
| Migration effort | Low to adopt, high to leave | High to adopt from legacy | Medium | High for event and replay design | High for invariants | Low if services were premature |

Reading the table. Shared Database Microservices wins when the team values
fast code extraction, local joins, and one operational database more than team
autonomy. Database per Service wins when ownership and independent change are
the goal. API Composition and CQRS handle reads without direct table access.
Saga handles write consistency without a single transaction. Modular Monolith is
often the more honest alternative when one team owns all code and data.

## 13. Related and incompatible patterns

- **Database per Service.** The primary replacement. Each service owns its
  persistent data and exposes access through APIs, events, or projections. AWS
  states that database-per-service means individual data stores cannot be
  directly accessed by other microservices (AWS Prescriptive Guidance,
  "Database-per-service pattern," verified 2026-08-02).
- **Saga.** A replacement for cross-service ACID transactions. AWS describes a
  microservices transaction as multiple local transactions and points to Saga
  when rollback across earlier local transactions is needed (AWS Prescriptive
  Guidance, "FAQ," verified 2026-08-02).
- **API Composition.** A replacement for cross-service joins in request paths.
  A composer calls owner APIs and merges the response. It keeps data ownership
  intact but can add latency and partial-failure handling.
- **CQRS with Materialized Views.** A replacement for repeated cross-domain
  reads. Microsoft describes a local read model containing denormalized data
  from other services, synchronized when the system of record changes
  (Microsoft Learn, "Cloud-native data patterns," verified 2026-08-02).
- **Event Sourcing.** Sometimes replaces shared current-state tables by making
  changes append-only and projecting views for each service. It raises
  complexity and should be adopted for a domain reason, not as ceremony.
- **Strangler Fig.** Often composes with a temporary shared database. The old
  system remains the data source while new services grow around it. The bridge
  must shrink over time.
- **Distributed Monolith.** The architectural smell that often results.
  Services deploy separately but must change, test, and recover together.
- **Bounded Context.** Incompatible with shared writes across one model. A
  bounded context owns its language and model boundary; a shared table pressures
  contexts back into one vocabulary.
- **Busy Database.** A frequent companion when shared stored procedures,
  triggers, reporting, and workflow logic accumulate in the database because all
  services can reach it.

## 14. Refactoring path in and out

Introducing the pattern should be rare, but a team may choose it as a bridge
during monolith decomposition.

1. Name it as a temporary shared database bridge in the architecture decision
   record. Include an owner, a review date, and deletion criteria.
2. Create a database identity per service before code extraction. Do not let
   services share the monolith's all-powerful user.
3. Tag every connection with service name, deploy version, and job name so query
   sampling can find consumers later.
4. Define table ownership even if access is still broad. Every table must have
   one owner and one route for change requests.
5. Require expand and contract migrations. Add nullable columns before reads,
   dual-write if needed, backfill, move consumers, then drop later.
6. Block new cross-domain foreign keys and new shared writes unless a named
   migration owner accepts the exit work.

Refactoring out is the normal direction.

1. Inventory real access. Use database logs, query samples, static SQL search,
   ORM model references, BI queries, and migration history. Datadog used DBM
   query samples and engineering review across more than 30 teams to find
   domain clusters (Datadog Engineering, "Breaking up a monolith," verified
   2026-08-02).
2. Group tables by business domain and owner. The first cut should minimize
   cross-domain writes, not maximize conceptual purity.
3. Create private schemas or database users. Revoke writes before reads. Writes
   define ownership and carry the highest risk.
4. Replace direct reads with one of four routes: owner API, event-built
   projection, materialized view, or analytical replica.
5. Add compatibility tests that fail on new cross-domain joins or transactions.
   GitLab used detection and allowlists to prevent new violations while working
   through old ones (GitLab, "Decomposing the GitLab backend database, Part 1,"
   verified 2026-08-02).
6. Split the first low-coupling domain physically. Choose a domain with clear
   ownership, few cross-domain joins, and high pain from sharing.
7. Run dual reads or replication during cutover. Keep rollback paths short and
   measured.
8. Delete data from the shared database after cutover, or consumers will drift
   back to the old source.
9. Repeat per domain. The long tail is where discipline matters most.

Named refactorings that apply are Extract Service, Move Field, Move Method,
Encapsulate Record, Replace Query with Parameterized Query, and Strangler Fig.
The architectural move is from shared schema integration to published contract
integration.

## 15. Testing and verification

Engineering judgement. Testing has to cover both behavior and ownership, because
the anti-pattern's failures often arrive through a different service from the
one under test.

What is easier.

- Transactional tests can assert multi-table invariants inside one database.
- Integration tests can seed one schema and exercise several services without
  building event projections.
- Migration tests can run against one database snapshot.

What is harder.

- Service tests are less isolated because the database fixture must include
  tables owned by other services.
- Contract tests are unclear because the contract is a schema, not an API.
- Destructive migration tests must account for old service versions and hidden
  consumers.
- Performance tests need realistic cross-service query mixes, not one service's
  workload in isolation.

Verification practices.

- **Schema ownership tests.** Fail the build when a service imports another
  service's ORM model, writes to another domain schema, or introduces a
  cross-domain foreign key.
- **Migration compatibility tests.** Run old and new service versions against
  the expanded schema before any destructive migration.
- **Query allowlist tests.** Capture known cross-domain queries, allowlist them
  with owners and expiry dates, and fail on new ones. This mirrors the approach
  GitLab described for preventing new database decomposition violations while
  old ones were being removed (GitLab, "Decomposing the GitLab backend database,
  Part 1," verified 2026-08-02).
- **Consumer discovery tests.** In staging, revoke a read grant from a target
  table and watch for failures before trying it in production.
- **Concurrency tests.** Run long transactions from one service while another
  service writes the same table, then assert timeouts, lock waits, and retry
  behavior.
- **Projection parity tests.** When replacing a join with a read model, compare
  old SQL results with the new projection until the error budget is understood.

## 16. Observability signals

Engineering judgement. The dashboard has to make hidden database coupling
visible. Service metrics alone will not show it.

Record these signals.

- Query count, latency, rows scanned, rows returned, and error count labelled by
  database user, service, table, and operation.
- Lock wait time, deadlocks, blocked sessions, and the blocking database user.
- Connection pool use per service and per database role.
- Schema migration duration, lock time, and number of dependent services
  detected before rollout.
- Table read and write ownership, with alerts when a non-owner writes.
- Cross-domain join count and transaction count.
- Replication lag for read replicas and projections used to move consumers away
  from direct reads.
- Counts of queries using deprecated columns or tables during an expand and
  contract migration.
- Access-control drift, for example services with grants to tables outside
  their domain.

A healthy shared database bridge has a shrinking number of shared tables,
shrinking non-owner reads, zero non-owner writes for domains being extracted,
and a visible owner for every remaining shared dependency. Migration dashboards
show expand and contract phases aging out on schedule. Query latency remains
inside service budgets and lock waits are rare.

A failing bridge has rising cross-domain joins, new shared writes, broad grants
that never expire, lock waits with blockers from unrelated services, migration
windows that need organization-wide freezes, and tables with no known owner.
Datadog's published migration progress metrics include table counts by schema,
connections using a shared user, ACL group membership, and traffic to new
database clusters, all of which are practical examples of making the coupling
visible (Datadog Engineering, "Breaking up a monolith," verified 2026-08-02).

## 17. Security and privacy implications

Engineering judgement. The security problem is not that SQL is unsafe. The
problem is that broad direct access defeats least privilege and makes privacy
boundaries harder to prove.

**Least privilege.** A service should have access to the data needed for its
business role. Shared database roles often inherit monolith-era power, so a
service that only needs order totals can read customer consent, payment tokens,
or internal notes. Fix with per-service roles, owner schemas, read grants with
expiry dates, and alerts for non-owner access.

**Auditability.** If many services share one database user, audit logs cannot
name the true caller. That weakens incident response and privacy review. The
minimum control is one credential per service and per job type, with connection
tags that survive pooling.

**Data minimization.** Service-owned APIs can return narrow responses. Shared
tables expose every column the role can read, including fields added later. A
schema change can silently widen access. Views or projections should expose
only the fields a consumer contract needs.

**Tenant and region isolation.** Shared operational tables can mix tenants,
regions, or retention classes. A missing predicate can become a privacy
incident. If shared storage remains, enforce tenant and region predicates at
the database policy layer where the engine supports it, and test those policies
with negative cases.

**Destructive migrations.** A privacy deletion flow may delete or anonymize a
row for one service while another service has copied the data into a shared
table or report. Data lineage has to include direct SQL consumers, projections,
exports, and backups.

**Blast radius.** A compromised service credential can read or alter every table
granted to that credential. In database-per-service, the same compromise is
bounded by the service's own store. That is a security argument for ownership,
not only an architecture argument.

## Code examples

The samples model the same small checkout domain. Each first sample shows the
anti-pattern, where one service reads or writes tables owned by another. Each
second sample shows the safer replacement: the service talks to an owner API or
uses a local projection. The examples use in-memory structures so they can run
without a database server.

### TypeScript

```typescript
type CustomerRow = { id: string; creditLimit: number };
type OrderRow = { id: string; customerId: string; total: number };

class SharedDatabase {
  customers = new Map<string, CustomerRow>();
  orders = new Map<string, OrderRow>();
}

class OrderServiceWithSharedDb {
  constructor(private readonly db: SharedDatabase) {}

  placeOrder(id: string, customerId: string, total: number): string {
    const customer = this.db.customers.get(customerId);
    if (!customer) return "missing customer";

    let openTotal = 0;
    for (const order of this.db.orders.values()) {
      if (order.customerId === customerId) openTotal += order.total;
    }

    if (openTotal + total > customer.creditLimit) return "credit exceeded";
    this.db.orders.set(id, { id, customerId, total });
    return "accepted";
  }
}

interface CustomerCreditApi {
  canReserve(customerId: string, amount: number): boolean;
}

class CustomerService implements CustomerCreditApi {
  private customers = new Map<string, CustomerRow>();
  private reserved = new Map<string, number>();

  addCustomer(row: CustomerRow): void {
    this.customers.set(row.id, row);
  }

  canReserve(customerId: string, amount: number): boolean {
    const customer = this.customers.get(customerId);
    if (!customer) return false;
    const current = this.reserved.get(customerId) ?? 0;
    if (current + amount > customer.creditLimit) return false;
    this.reserved.set(customerId, current + amount);
    return true;
  }
}

class OrderServiceWithApi {
  private orders = new Map<string, OrderRow>();

  constructor(private readonly credit: CustomerCreditApi) {}

  placeOrder(id: string, customerId: string, total: number): string {
    if (!this.credit.canReserve(customerId, total)) return "credit exceeded";
    this.orders.set(id, { id, customerId, total });
    return "accepted";
  }
}

const shared = new SharedDatabase();
shared.customers.set("c1", { id: "c1", creditLimit: 100 });
console.log(new OrderServiceWithSharedDb(shared).placeOrder("o1", "c1", 30));

const customers = new CustomerService();
customers.addCustomer({ id: "c1", creditLimit: 100 });
console.log(new OrderServiceWithApi(customers).placeOrder("o2", "c1", 30));
```

### Python

```python
from dataclasses import dataclass, field


@dataclass
class SharedDatabase:
    customers: dict[str, int] = field(default_factory=dict)
    orders: dict[str, tuple[str, int]] = field(default_factory=dict)


class BillingServiceWithSharedDb:
    def __init__(self, db: SharedDatabase) -> None:
        self.db = db

    def invoice_total(self, customer_id: str) -> int:
        if customer_id not in self.db.customers:
            return 0
        return sum(
            total for owner, total in self.db.orders.values()
            if owner == customer_id
        )


class OrderProjection:
    def __init__(self) -> None:
        self.totals: dict[str, int] = {}

    def apply_order_placed(self, customer_id: str, total: int) -> None:
        self.totals[customer_id] = self.totals.get(customer_id, 0) + total


class BillingServiceWithProjection:
    def __init__(self, projection: OrderProjection) -> None:
        self.projection = projection

    def invoice_total(self, customer_id: str) -> int:
        return self.projection.totals.get(customer_id, 0)


db = SharedDatabase(customers={"c1": 100}, orders={"o1": ("c1", 40)})
print(BillingServiceWithSharedDb(db).invoice_total("c1"))

projection = OrderProjection()
projection.apply_order_placed("c1", 40)
print(BillingServiceWithProjection(projection).invoice_total("c1"))
```

### Go

```go
package main

import "fmt"

type SharedDatabase struct {
	customers map[string]int
	orders    map[string]Order
}

type Order struct {
	customerID string
	total      int
}

type ShippingServiceWithSharedDB struct {
	db *SharedDatabase
}

func (s ShippingServiceWithSharedDB) CanShip(orderID string) bool {
	order, ok := s.db.orders[orderID]
	if !ok {
		return false
	}
	_, customerExists := s.db.customers[order.customerID]
	return customerExists
}

type OrderStatusAPI interface {
	ReadyToShip(orderID string) bool
}

type OrderService struct {
	ready map[string]bool
}

func (o OrderService) ReadyToShip(orderID string) bool {
	return o.ready[orderID]
}

type ShippingServiceWithAPI struct {
	orders OrderStatusAPI
}

func (s ShippingServiceWithAPI) CanShip(orderID string) bool {
	return s.orders.ReadyToShip(orderID)
}

func main() {
	db := &SharedDatabase{
		customers: map[string]int{"c1": 100},
		orders:    map[string]Order{"o1": {customerID: "c1", total: 40}},
	}
	fmt.Println(ShippingServiceWithSharedDB{db: db}.CanShip("o1"))

	orders := OrderService{ready: map[string]bool{"o1": true}}
	fmt.Println(ShippingServiceWithAPI{orders: orders}.CanShip("o1"))
}
```

## 18. References

1. Chris Richardson. *Microservices Patterns*. Manning, 2018. Chapter 4,
   "Managing transactions with sagas." Source for the microservices data
   pattern family: shared database, database-per-service, saga, API composition,
   CQRS, and event sourcing.
2. Chris Richardson. "Pattern: Shared database." Microservices.io.
   https://microservices.io/patterns/data/shared-database.html
   Verified 2026-08-02. Source for the shared database name, context, benefits,
   and drawbacks.
3. AWS Prescriptive Guidance. "Shared-database-per-service pattern."
   https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/shared-database.html
   Verified 2026-08-02. Source for AWS naming, applicability, and coupling
   warnings.
4. AWS Prescriptive Guidance. "Database-per-service pattern."
   https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/database-per-service.html
   Verified 2026-08-02. Source for the service-owned database alternative.
5. AWS Prescriptive Guidance. "FAQ."
   https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/faq.html
   Verified 2026-08-02. Source for data privacy, shared database cautions, and
   saga guidance.
6. Microsoft Learn. "Microservices architecture style."
   https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/microservices
   Verified 2026-08-02. Source for service autonomy, bounded context, and
   service-owned data guidance.
7. Microsoft Learn. "Data considerations for microservices."
   https://learn.microsoft.com/en-us/azure/architecture/microservices/design/data-considerations
   Verified 2026-08-02. Source for the rule that services should not share a
   data store and the distinction between physical server sharing and shared
   schemas or tables.
8. Microsoft Learn. "Cloud-native data patterns."
   https://learn.microsoft.com/en-us/dotnet/architecture/cloud-native/distributed-data
   Verified 2026-08-02. Source for database-per-microservice, materialized
   views, saga, CQRS, and event sourcing discussion.
9. Datadog Engineering. Fabiana Scala and Tali Gutman. "Breaking up a monolith:
   How we're unwinding a shared database at scale." Datadog, June 17, 2025.
   https://www.datadoghq.com/blog/engineering/unwinding-shared-database/
   Verified 2026-08-02. Source for the Datadog production example and migration
   practices.
10. GitLab. Dylan Griffith. "Decomposing the GitLab backend database, Part 1:
    Designing and planning." GitLab Blog, August 4, 2022.
    https://about.gitlab.com/blog/path-to-decomposing-gitlab-database-part1/
    Verified 2026-08-02. Source for the GitLab.com production example and
    decomposition process.
11. GitLab Docs. "Multiple Databases."
    https://docs.gitlab.com/development/database/multiple_databases/
    Verified 2026-08-02. Source for GitLab's decomposed database state and
    schema classification.
12. AWS Case Study. "Samsung Migrates 1.1 Billion Users across Three Continents
    from Oracle to Amazon Aurora with AWS Database Migration Service."
    https://aws.amazon.com/solutions/case-studies/samsung-migrates-off-oracle-to-amazon-aurora/
    Verified 2026-08-02. Source for the Samsung Account production migration
    example.
