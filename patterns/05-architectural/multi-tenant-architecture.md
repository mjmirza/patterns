---
name: Multi-Tenant Architecture
slug: multi-tenant-architecture
family: 05-architectural
category: Architectural
aliases: [Multi-Tenancy, SaaS Tenant Isolation]
first_described: "Frederick Chong, Gianpaolo Carraro, and Roger Wolter, Multi-Tenant Data Architecture, Microsoft, 2006"
maturity: canonical
related: [sharding, bulkhead, cell-based-architecture, database-per-service]
incompatible_with: []
verified: 2026-08-22
---

# Multi-Tenant Architecture

## 1. Name, aliases, and lineage

The canonical name is Multi-Tenant Architecture, and the underlying property is
usually called multi-tenancy. AWS's own architecture writing draws a line
worth stating up front. multi-tenancy is an infrastructure property, not the
same thing as the SaaS business model itself, even though the two are almost
always discussed together. AWS states it plainly. "In this purely
infrastructure-focused view, multi-tenancy is used to describe how resources
are shared by tenants to promote agility and cost efficiency," and warns that
"equating SaaS and multi-tenancy tends to lead teams to take a purely
technical view of SaaS when, in reality, SaaS is more of a business model
than an architecture strategy." (AWS Whitepaper, "SaaS Architecture
Fundamentals," see reference 1.)

The pattern is widely credited to a named source, unlike a term such as
microservices, which has no single named originator. Frederick Chong,
Gianpaolo Carraro, and Roger Wolter published "Multi-Tenant Data
Architecture" through Microsoft in 2006, describing a tenant as an
organization using an application to access its own logically isolated data
store, and this paper is the source most later industry writing traces the
three-way isolation taxonomy back to.

A second, independent named source sits at the production-scale end of the
lineage. Craig D. Weissman and Steve Bobrowski's paper "The design of the
force.com multitenant internet application development platform,"
Proceedings of the 2009 ACM SIGMOD International Conference on Management of
Data, describes the metadata-driven architecture behind Salesforce's
platform at tens of thousands of organizations, an architecture Salesforce's
own current documentation still describes today (dimension 9).

## 2. Problem and context

A SaaS provider serves many customers, called tenants, from one running
application. Each tenant needs its own data kept apart from every other
tenant's data, needs a fair share of the shared compute and storage, and, for
some tenants, needs a level of isolation strong enough to satisfy a
regulator. Running one fully separate deployment per customer solves the
isolation problem completely but throws away the cost efficiency that made a
shared platform worth building in the first place, since idle capacity for
one customer cannot be used by another. Running everything in one shared
deployment with no separation at all solves the cost problem but risks one
tenant's bug, load spike, or breach touching every other tenant.

The problem context is a range of positions, not a binary choice. Azure's own
architecture guidance frames it this way. "Instead of viewing isolation as a
discrete property," Azure's guidance treats it instead as a continuous range,
moving from a fully isolated, shared-nothing deployment at one end to a
fully shared, shared-everything deployment at the other. (Azure Architecture
Center, "Tenancy Models for a Multitenant Solution," see reference 5.)
Multi-tenant architecture is the name for the whole family of positions
along that range, and the choice of position is made per system, per layer,
and sometimes per tenant.

## 3. Forces

- Cost efficiency against blast radius. A shared deployment scales with real
  aggregate load and sits idle for nothing, but a shared deployment also
  shares fate. AWS names both sides directly for its pooled model. "In a
  pooled environment, your system will scale based on the actual load and
  activity of all of your tenants," against "in a pooled environment, an
  outage will likely impact all the tenants of your system." (AWS Whitepaper,
  "SaaS Tenant Isolation Strategies," pool isolation, see reference 3.)
- Isolation strength against onboarding speed and operational cost. A fully
  siloed deployment per tenant "generally reduces your exposure when there
  may be some outage or event" and constrains a failure "to that
  environment," but AWS is equally direct that "with every tenant running in
  its own environment, we're missing much of the cost efficiency that is
  traditionally associated with SaaS solutions." (Same source, silo
  isolation, see reference 2.)
- Compliance and data residency against uniformity. Some tenants, by
  regulation or contract, cannot accept shared infrastructure at all. AWS
  names this directly for the silo model. "Some SaaS providers are selling
  into regulated environments that impose strict isolation requirements,"
  and offers the silo model as the option that lets a provider "offer to
  some or all of their tenants the option of being deployed in a dedicated
  model."
- Fairness and predictability against a shared resource pool. The moment
  resources are shared, one tenant's load can degrade another tenant's
  experience, a failure mode named directly by AWS's own operational
  guidance and covered in full in dimension 11.
- Granularity. Isolation does not have to be decided once for a whole
  system. AWS's bridge model and Azure's vertical and horizontal
  partitioning both describe applying a different isolation level per layer
  or per tenant group within the same solution, trading a single simple
  answer for a more precise one.

## 4. Applicability and non-applicability

Reach for a shared, pooled multi-tenant model when the tenant base is large,
individual tenants are cost-sensitive, and no regulatory or contractual
requirement forces dedicated infrastructure. This is the default a SaaS
provider starts from, because it is the model that captures the cost
efficiency the business model depends on.

Reach for a siloed, dedicated model, or the bridge model that applies silo
isolation only to specific layers or specific tenants, when a tenant's
compliance requirements demand it, when a single tenant's scale would
otherwise crowd out every other tenant sharing the same infrastructure, or
when a customer is willing to pay for guaranteed isolation as a feature.
Azure states the compliance case directly. "If your customers' isolation
requirements are high, a single-tenant infrastructure approach might be
appropriate even though it's more costly." (Azure Architecture Center, see
reference 5.)

Do not reach for multi-tenant architecture at all when there is, and will
only ever be, one customer. A single-tenant application gains nothing from
tenant-id discriminators, tenant-context propagation, or per-tenant resource
governance, and paying that complexity cost for a system that will never
actually host a second tenant is waste, not caution. Do not default every
tenant into the pooled model without checking each one's compliance posture
first. a regulated tenant forced into shared infrastructure is a liability
discovered far too late, usually during that tenant's own audit rather than
during the provider's own design review.

## 5. Structure

The participants are the tenant, an organization or account whose data and
usage must stay apart from every other tenant's; the tenant identifier, a
value, an org id, a subdomain, a JWT claim, that names which tenant a given
request or row belongs to; the isolation boundary, the actual mechanism that
enforces separation at a chosen layer, a dedicated database, a shared
database with row-level filtering, a dedicated compute cluster, or a shared
one with per-tenant quotas; and the tenant resolver, the piece of the system
that determines, at the start of a request, which tenant this is, so every
downstream layer can enforce or reuse that boundary.

## 6. ASCII structure diagram

```
Silo (dedicated stack per tenant)

  Tenant A --> [App instance A] --> [Database A]
  Tenant B --> [App instance B] --> [Database B]
  Tenant C --> [App instance C] --> [Database C]

  no shared runtime state between tenants, full blast-radius containment


Pool (shared stack, tenant_id discriminator)

  Tenant A --+
  Tenant B --+--> [Shared app tier] --> [Shared database, every row]
  Tenant C --+                          [carries a tenant_id column]

  one outage or one noisy tenant is visible to every other tenant


Bridge (mixed, per layer or per tenant)

  Tenant A --+                         +--> [Shared storage, pooled tenants]
  Tenant B --+--> [Shared web tier] ---+
  Tenant C ------ [dedicated app tier + dedicated storage, siloed tenant] --
```

## 7. Dynamics

A request arrives carrying a tenant identifier, resolved from a subdomain, a
custom domain mapping, a header, or a claim inside an authentication token.
The tenant resolver reads that identifier once, near the entry point, and
attaches it to the request's context so every layer downstream can read it
without re-deriving it. Spring Security's own multitenancy support shows
this exact shape for a token-based resolver. "One way to differentiate
tenants is by the issuer claim," resolved through a
`JwtIssuerAuthenticationManagerResolver` configured with the set of trusted
issuers, one per tenant population. (Spring Security Reference, see
reference 6.)

From there, the isolation boundary decides how the rest of the request is
served. In a siloed system, the resolved tenant identifier selects which
entirely separate application instance and database the request is routed
to, and nothing downstream needs to filter by tenant again because there is
only one tenant's data reachable at all. In a pooled system, the resolved
identifier is carried into every query as a filter, so the same shared
database serves every tenant while returning only the rows that belong to
the one that made the request. django-tenants' own schema-based
implementation shows a variant of this. "Whenever a request is made, the
host name is used to match a tenant in the database. If there's a match, the
search path is updated to use this tenant's schema," so every subsequent
query in that request transparently reaches only that tenant's schema.
(django-tenants documentation, see reference 8.)

## 8. Implementation variants

- Silo, database-per-tenant. Each tenant gets a fully separate stack,
  compute, storage, and often a fully separate deployment. AWS's own
  description names the scope precisely. "Isolation is an end-to-end
  construct that spans an entire customer stack." (AWS Whitepaper, silo
  isolation, see reference 2.)
- Pool, shared database, shared schema. All tenants share one set of
  tables, and a tenant_id column on every row is the only thing separating
  one tenant's data from another's. AWS's own pool description names this
  mechanism directly, describing "a table that is indexed by individual
  tenant identifiers." (Same source, pool isolation, see reference 3.) The
  strongest form of this variant enforces the filter at the database layer
  itself rather than trusting every application query to remember it.
  PostgreSQL's own row security feature lets "tables have row security
  policies that restrict, on a per-user or per-session basis, which rows can
  be returned by normal queries." (PostgreSQL Documentation, see reference
  7.) Crunchy Data's own worked example shows the tenant-specific form of
  this policy directly.

  ```sql
  CREATE POLICY tenant_isolation
    ON events
    TO application
    USING (org_id = current_setting('rls.org_id')::uuid);
  ```

  With the session set once per request, `SET rls.org_id = '...'`, "any
  queries executed within the request will automatically be filtered based
  on the current tenant ID," a guarantee that holds even if a specific
  application query forgets to add its own WHERE clause. (Crunchy Data
  engineering blog, see reference 9.)
- Bridge, schema-per-tenant. A middle position between silo and pool. one
  shared database instance, but a separate schema per tenant, so isolation
  is stronger than a bare tenant_id column while infrastructure is still
  shared. django-tenants names this directly as its "semi isolated
  approach." (django-tenants documentation, see reference 8.)
- Bridge, mixed by layer. AWS's own bridge model applies silo isolation to
  some layers and pool isolation to others within one solution, in their own
  words a model "focused on enabling you to apply the silo or pool model
  where it makes sense," giving the worked example of a pooled web tier in
  front of a siloed application tier and storage layer. (AWS Whitepaper,
  the bridge model, see reference 4.) Azure names the equivalent choice
  vertical partitioning, splitting which tenants land in a dedicated versus
  a shared deployment, and horizontal partitioning, splitting which layers
  of the stack are shared versus dedicated. (Azure Architecture Center, see
  reference 5.)
- Cell-based, shuffle-sharded pool. Tenants are grouped into fixed-size
  cells, each cell an independent instance of the full stack, so a noisy or
  failing tenant's effect is contained to its own cell rather than spreading
  to the whole tenant population. This is the pattern this catalogue records
  separately as Cell-Based Architecture, and it is the production shape both
  Shopify (dimension 9) and AWS's own bulkhead guidance describe.

## 9. Known production uses

- Salesforce's Force.com platform runs a pool model at very large scale, with
  the tenant identifier named explicitly. "All Salesforce Platform data,
  metadata, and pivot table structures, including underlying database
  indexes, are physically partitioned by OrgID (by tenant) using native
  database partitioning mechanisms," and "by definition, every Salesforce
  Platform query targets a specific tenant's information, so the query
  optimizer need only consider accessing data partitions that contain a
  tenant's data." (Salesforce architecture documentation, see reference
  10.) The academic account of this same platform's design is Weissman and
  Bobrowski's 2009 SIGMOD paper (dimension 1).
- Shopify runs a silo-leaning, cell-based model it calls pods. "A pod
  consists of a set of shops that live on a fully isolated set of
  datastores," routed by a component named Sorting Hat that "matches every
  request to a pod and adds a header to that request" so downstream
  services "only query a single pod at a time." Shopify names the exact
  motivation the trade-off in dimension 3 predicts. before pods, "if any of
  our shards went down, that entire action would be unavailable across the
  platform," and after, "since there is no cross-pod communication, adding
  a new pod won't cause unexpected interference with other, pre-existing
  pods." (Shopify Engineering, see reference 11.)
- Atlassian's Confluence Cloud runs a shard-based pool model where "each
  shard is a logical grouping of nodes and resources for a set of tenants,"
  and where database connection exhaustion from a single busy tenant was a
  real, named operational problem they fixed by enforcing "limits on the
  number of database connections each tenant can get." (Atlassian
  Engineering, see reference 15.)

## 10. Consequences

Positive. Shared infrastructure scales with real aggregate load instead of
the sum of every tenant's individual peak, which is the core cost advantage
of the pattern. A single codebase and a single set of operational tooling
serves every tenant, so a fix or a feature reaches all tenants at once
instead of being deployed separately per customer. The isolation strength
can be chosen per layer or per tenant rather than forced to one setting for
the whole system, letting a provider offer a cheaper shared tier and a more
expensive dedicated tier from the same underlying platform.

Negative. A shared deployment shares fate. an outage, a bug, or a heavy
tenant's load can degrade or break the experience for every other tenant on
the same shared infrastructure, the trade-off AWS names directly for its
pool model. A missing or forgotten tenant filter in application code is a
cross-tenant data exposure waiting to happen, and the cost of that mistake
scales with how many tenants share the affected table or service. Some
tenants simply cannot be served by a shared model at all, regardless of cost,
because their compliance obligations forbid it, which forces a provider to
support more than one isolation tier if it wants to serve that segment.

## 11. Failure modes and misuse

Noisy neighbor. one tenant's disproportionate load degrades performance for
every other tenant sharing the same infrastructure. AWS's own Well-Architected
guidance names it directly. "the idea behind noisy neighbor is that a user of
a system could place load on the system's resources that could have an
adverse effect on other users of the system," a risk with "expanded
relevance in a multi-tenant environment where tenants may be consuming
shared resources." (AWS Well-Architected Framework, SaaS Lens, see reference
12.) The concrete mitigation named across multiple real systems is a
per-tenant resource quota. Grafana Enterprise Metrics ships per-tenant
limits specifically so "a single tenant cannot monopolize the resources of
or threaten the stability" of the shared cluster (Grafana documentation, see
reference 13), and Atlassian's own fix, named above, was a hard limit on
per-tenant database connections.

Cross-tenant data leakage. the single most damaging failure mode of this
pattern, and it has real, dated, named precedents. In December 2022, a flaw
in Azure Cognitive Search nicknamed ACSESSED let a feature that reconfigured
network access rules silently remove the isolation boundary around a
tenant's search instance, allowing "unauthorized cross-tenant access to ACS
data planes from any location." (SecurityWeek, see reference 16.) In 2025,
researchers at Wiz found a flaw in Azure Cosmos DB, called CosmosEscape, in
which a crafted query exposed "a platform-wide signing secret and a regional
account directory," letting an attacker retrieve a master key that "unlocked
every account tested" across regions and database APIs. (The Hacker News,
see reference 17.) At the application layer rather than the platform layer,
OWASP's own Multi Tenant Security Cheat Sheet names the same failure by its
plain cause. code that only checks a resource's own identifier "not tenant
ownership" against a resource that a different tenant's identifier could
also match. (OWASP Cheat Sheet Series, see reference 18.)

Assuming a bare tenant_id column is enough without enforcing it at the
database layer. Every application query must remember the filter, and a
single missed one anywhere in the codebase is a leak. Enforcing the same
filter through PostgreSQL's own row security, as shown in dimension 8, moves
that guarantee from "every developer must remember" to "the database refuses
to return the row at all."

## 12. Trade-off matrix

| Model | Cost efficiency | Blast radius on failure | Compliance fit | Onboarding cost per tenant |
|---|---|---|---|---|
| Silo, database per tenant | Low, no shared idle capacity | Contained to one tenant | Strong, meets most strict requirements | High, a full stack per tenant |
| Pool, shared schema with tenant_id | High, scales with real aggregate load | Wide, an outage or noisy tenant reaches everyone sharing it | Weak on its own, needs added controls for regulated tenants | Low, a new row, not new infrastructure |
| Bridge, schema per tenant | Moderate | Reduced versus pool, contained to the schema | Moderate, stronger than pool | Moderate, a new schema, not new infrastructure |
| Cell-based, shuffle-sharded pool | High within a cell, some overhead across cells | Contained to one cell's tenant population | Moderate, depends on cell composition | Low, tenant placed into an existing cell |

## 13. Related and incompatible patterns

Sharding (see `sharding.md` in family 08) is a distinct, related idea often
confused with multi-tenancy. sharding splits one logical dataset or workload
across multiple physical stores for scale, while multi-tenancy is about how
infrastructure is shared across many separate customers. MongoDB's own
definition names sharding's actual purpose. "distributing data across
multiple machines" to solve capacity limits "when data sets or throughput
challenge the capacity of a single server." (MongoDB Manual, see reference
14.) In practice the two combine constantly, a pool of tenants is very often
physically sharded for scale, and a shard can hold one tenant or many, but
the concepts answer different questions.

Bulkhead (see `bulkhead.md` in family 08) is the general fault-isolation
technique multi-tenant noisy-neighbor mitigation is a specific instance of.
AWS's own bulkhead guidance names a tenant or customer identifier as a valid
partition key for a bulkhead's cells directly. "Examples of partition keys
are customer ID, resource ID, or any other parameter easily accessible in
most API calls." (AWS Well-Architected Framework, see reference 19.) A
purely siloed multi-tenant deployment is the degenerate case of a bulkhead
where each cell holds exactly one tenant.

Cell-Based Architecture (see `cell-based-architecture.md` in this family) is
the production shape multiple real systems, Shopify's pods among them,
actually build to get bulkhead-style isolation at a coarser and more
operationally practical grain than one cell per tenant.

Database-per-Service (see `database-per-service.md` in family 10) answers a
different question again, keeping one service's data private from other
services within a single tenant's own system, and composes cleanly with
multi-tenancy at a different axis. a siloed tenant's own stack can itself be
built from many services, each with its own database-per-service.

There is no pattern multi-tenant architecture is flatly incompatible with.
it is a range of isolation choices applied across a system, and every
pattern above can be composed with it at the appropriate layer.

## 14. Refactoring path in and out

In, from single-tenant to multi-tenant. Add a tenant identifier column to
every table that currently assumes one customer, and add a tenant resolver
at the request entry point that determines which tenant a request belongs
to. Update every query to filter by that identifier, and where the database
supports it, enforce the filter as a row security policy rather than trusting
every call site to remember it, exactly the PostgreSQL pattern in dimension
8. Only after every table and query is tenant-aware does the system become
safe to serve a second tenant.

In, from pool to a bridged or siloed tenant, tenant promotion. AWS's own
bridge model shows the mechanism that makes this possible without a full
rewrite. isolation is applied per layer, so a specific tenant's storage and
application tier can be moved to dedicated infrastructure while the shared
web or routing tier in front of it stays pooled for every tenant. The
trigger for this move is almost always a named, external one, a regulatory
or contractual requirement a specific tenant carries, per AWS's own guidance
that "what generally drives adoption of a silo model is strict security and
regulatory constraints." (AWS Prescriptive Guidance, see reference 20.)

Out. When a system was built multi-tenant but will only ever have one real
tenant, the tenant_id filters, the tenant resolver, and any per-tenant
configuration are complexity with no remaining purpose, and removing them
restores a simpler, single-tenant system. This is rare in practice, because
most systems that start multi-tenant were built that way because a second
tenant was always expected.

## 15. Testing and verification

The test that matters most is proving tenant boundaries hold under an
adversarial attempt to cross them, not merely that a happy-path request
returns the right tenant's data. AWS's own Well-Architected guidance names
this directly as a dedicated question. "search for opportunities to subvert
the isolation model, confirming misbehaved users cannot cross a tenant
boundary," alongside testing "various noisy neighbor conditions, assessing
the system's ability to identify and respond to scenarios where a subset of
tenants places a disproportionate load on your system." (AWS
Well-Architected Framework, SaaS Lens, REL 3, see reference 21.)

Concretely, this means a test suite that authenticates as tenant A, attempts
to read, write, or list a resource belonging to tenant B by id, and asserts
the attempt fails or returns nothing, run against every resource type the
system exposes, not only one representative table. Where row security is
enforced at the database layer, this same test also proves the database
itself, not only the application code path, holds the boundary.

## 16. Observability signals

The healthy signal is per-tenant telemetry that never shows one tenant
consuming a disproportionate share of shared resources or generating a
disproportionate share of errors. New Relic's own guidance describes tagging
telemetry with a tenant attribute specifically so a team can identify when "a
single tenant is causing a disproportionate number of errors," rather than
only seeing an aggregate error rate that hides which tenant is responsible.
(New Relic engineering blog, see reference 22.) OneUptime describes the same
pattern from the dashboard side, building per-tenant service-level
dashboards "by grouping metrics on the tenant.id attribute when your metric
instruments record that attribute on measurements." (OneUptime blog, see
reference 23.)

The failing signal is the same telemetry showing one tenant's resource
consumption, error rate, or connection usage climbing far above the rest of
the tenant population, exactly the pattern that precedes a noisy-neighbor
incident, or a resource quota alert firing repeatedly for the same tenant,
which is the per-tenant limit mechanism from dimension 11 doing its job.

## 17. Security and privacy implications

This is not a pattern where isolation is silent. it is the pattern's entire
purpose, and getting it wrong is the single most damaging failure mode
covered in dimension 11. Every layer that touches tenant data, the database,
the cache, object storage, background jobs, exports, and logs, needs the
same tenant boundary applied, because a leak through any one of them is
still a leak. OWASP's own cheat sheet names the full surface directly, "data
and metadata isolation," and "broken tenant isolation," described as
"insufficient separation at database, cache, storage, or compute layers."
(OWASP Cheat Sheet Series, see reference 18.)

Where the boundary is enforced only in application code, a single missed
filter anywhere in the codebase is a genuine breach, not a theoretical risk,
as the two real, dated incidents in dimension 11 show at platform scale.
Enforcing the boundary at the database layer, through row security or a
fully separate schema or database per tenant, removes the dependency on
every developer remembering the filter correctly, and is the stronger
default wherever the extra cost is acceptable.

## 18. References

1. AWS Whitepaper, "SaaS Architecture Fundamentals," Re-defining
   Multi-Tenancy.
   https://docs.aws.amazon.com/whitepapers/latest/saas-architecture-fundamentals/re-defining-multi-tenancy.html,
   verified 2026-08-22.
2. AWS Whitepaper, "SaaS Tenant Isolation Strategies," Silo Isolation.
   https://docs.aws.amazon.com/whitepapers/latest/saas-tenant-isolation-strategies/silo-isolation.html,
   verified 2026-08-22.
3. AWS Whitepaper, "SaaS Tenant Isolation Strategies," Pool Isolation.
   https://docs.aws.amazon.com/whitepapers/latest/saas-tenant-isolation-strategies/pool-isolation.html,
   verified 2026-08-22.
4. AWS Whitepaper, "SaaS Tenant Isolation Strategies," The Bridge Model.
   https://docs.aws.amazon.com/whitepapers/latest/saas-tenant-isolation-strategies/the-bridge-model.html,
   verified 2026-08-22.
5. Azure Architecture Center, "Tenancy Models for a Multitenant Solution."
   https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/considerations/tenancy-models,
   verified 2026-08-22.
6. Spring Security Reference, "Multi-tenancy."
   https://docs.spring.io/spring-security/reference/servlet/oauth2/resource-server/multitenancy.html,
   verified 2026-08-22.
7. PostgreSQL Documentation, "Row Security Policies."
   https://www.postgresql.org/docs/current/ddl-rowsecurity.html, verified
   2026-08-22.
8. django-tenants documentation.
   https://django-tenants.readthedocs.io/en/latest/, verified 2026-08-22.
9. Crunchy Data engineering blog, "Row Level Security for Tenants in
   Postgres." https://www.crunchydata.com/blog/row-level-security-for-tenants-in-postgres,
   verified 2026-08-22.
10. Salesforce architecture documentation, "Platform Multitenant
    Architecture." https://architect.salesforce.com/fundamentals/platform-multitenant-architecture,
    verified 2026-08-22.
11. Shopify Engineering, Xavier Denis, "A Pods Architecture to Allow
    Shopify to Scale." https://shopify.engineering/a-pods-architecture-to-allow-shopify-to-scale,
    verified 2026-08-22.
12. AWS Well-Architected Framework, SaaS Lens, "Noisy Neighbor."
    https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/noisy-neighbor.html,
    verified 2026-08-22.
13. Grafana Enterprise Metrics documentation, "Set per-tenant resource
    usage limits."
    https://grafana.com/docs/enterprise-metrics/latest/manage/tenant-management/limits/,
    verified 2026-08-22.
14. MongoDB Manual, "Sharding." https://www.mongodb.com/docs/manual/sharding/,
    verified 2026-08-22.
15. Atlassian Engineering, Bhakti Mehta, "Scaling, rearchitecting, and
    decomposing Confluence Cloud."
    https://www.atlassian.com/engineering/scaling-rearchitecting-and-decomposing-confluence-cloud,
    verified 2026-08-22.
16. SecurityWeek, "Microsoft Patches Azure Cross-Tenant Data Access Flaw,"
    December 23, 2022.
    https://www.securityweek.com/microsoft-patches-azure-cross-tenant-data-access-flaw/,
    verified 2026-08-22.
17. The Hacker News, "Azure Cosmos DB flaw exposed platform," July 2026.
    https://thehackernews.com/2026/07/azure-cosmos-db-flaw-exposed-platform.html,
    verified 2026-08-22.
18. OWASP Cheat Sheet Series, "Multi Tenant Security Cheat Sheet."
    https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html,
    verified 2026-08-22.
19. AWS Well-Architected Framework, "REL10-BP03 Use bulkhead architectures
    to limit scope of impact."
    https://docs.aws.amazon.com/wellarchitected/latest/framework/rel_fault_isolation_use_bulkhead.html,
    verified 2026-08-22.
20. AWS Prescriptive Guidance, "Silo tenant isolation model," managed
    PostgreSQL multi-tenant SaaS.
    https://docs.aws.amazon.com/prescriptive-guidance/latest/saas-multitenant-managed-postgresql/silo.html,
    verified 2026-08-22.
21. AWS Well-Architected Framework, SaaS Lens, "REL 3, testing multi-tenant
    capabilities." https://wa.aws.amazon.com/saas.question.REL_3.en.html,
    verified 2026-08-22.
22. New Relic engineering blog, "Monitoring multi-tenant SaaS applications
    with New Relic." https://newrelic.com/blog/how-to-relic/monitoring-multi-tenant-saas-applications,
    verified 2026-08-22.
23. OneUptime blog, "How to Use Per-Tenant Observability Isolation in
    Multi-Tenant SaaS."
    https://oneuptime.com/blog/post/2026-02-06-per-tenant-observability-isolation-opentelemetry/view,
    verified 2026-08-22.

**Evidence grade.** high

**Most solid findings.** The three canonical isolation models, silo, pool,
and bridge, are confirmed against AWS's own official whitepaper with exact
quotes for every model, and independently corroborated by Azure's own
architecture guidance under different but mapping names, and by
django-tenants' framework-level implementation naming the same three-way
split. The two named cross-tenant security incidents (ACSESSED and
CosmosEscape) are real, dated, and independently reported. The two named
production systems, Salesforce and Shopify, are each sourced from that
company's own engineering writing, not a third party's summary, and
represent the pool and silo models respectively.

**Unverified or unclear.** The 2006 Chong, Carraro, and Wolter paper that
this catalogue's own community credits as the origin of the pattern could
not be fetched live in full, the original hosting is dead and archived
mirrors were not reachable during this research, so its exact wording in
dimension 1 is a paraphrase built from how later, independently-verified
sources describe and cite it, not a word-for-word quote from the paper
itself. A full first-party account of a real company migrating a specific
tenant from pooled to siloed infrastructure, the tenant promotion scenario
described in dimension 14, was not found and confirmed word for word, the
migration mechanism described there is built from AWS's own architectural
and trigger guidance rather than a single company's narrated case study.

## Code examples

### TypeScript, a tenant resolver plus a repository that always filters by the tenant id

```typescript
interface TenantContext {
  tenantId: string;
}

function resolveTenant(hostHeader: string): TenantContext {
  const subdomain = hostHeader.split(".")[0];
  return { tenantId: subdomain };
}

interface Invoice {
  id: string;
  tenantId: string;
  amount: number;
}

class InvoiceRepository {
  constructor(private readonly rows: Invoice[]) {}

  listFor(ctx: TenantContext): Invoice[] {
    return this.rows.filter((row) => row.tenantId === ctx.tenantId);
  }
}

const rows: Invoice[] = [
  { id: "1", tenantId: "acme", amount: 100 },
  { id: "2", tenantId: "globex", amount: 250 },
  { id: "3", tenantId: "acme", amount: 50 },
];

const repo = new InvoiceRepository(rows);
const ctx = resolveTenant("acme.app.example.com");
const invoices = repo.listFor(ctx);
console.log(invoices.length === 2);
```

### Python, a silo registry mapping each tenant to its own isolated store

```python
class TenantStore:
    def __init__(self, tenant_id: str) -> None:
        self.tenant_id = tenant_id
        self.records: list[dict] = []

    def add(self, record: dict) -> None:
        self.records.append(record)


class SiloRegistry:
    def __init__(self) -> None:
        self._stores: dict[str, TenantStore] = {}

    def store_for(self, tenant_id: str) -> TenantStore:
        if tenant_id not in self._stores:
            self._stores[tenant_id] = TenantStore(tenant_id)
        return self._stores[tenant_id]


registry = SiloRegistry()
registry.store_for("acme").add({"amount": 100})
registry.store_for("globex").add({"amount": 250})
registry.store_for("acme").add({"amount": 50})

acme_store = registry.store_for("acme")
assert len(acme_store.records) == 2
assert acme_store.records[0]["amount"] == 100
```

### Go, a bridge router picking pooled or siloed storage per tenant tier

```go
package main

import "fmt"

type Storage interface {
	Save(tenantID string, amount int)
}

type PooledStorage struct {
	rows map[string][]int
}

func NewPooledStorage() *PooledStorage {
	return &PooledStorage{rows: make(map[string][]int)}
}

func (p *PooledStorage) Save(tenantID string, amount int) {
	p.rows[tenantID] = append(p.rows[tenantID], amount)
}

type SiloedStorage struct {
	tenantID string
	rows     []int
}

func (s *SiloedStorage) Save(tenantID string, amount int) {
	s.rows = append(s.rows, amount)
}

type BridgeRouter struct {
	pooled       *PooledStorage
	siloed       map[string]*SiloedStorage
	siloedTenant map[string]bool
}

func NewBridgeRouter() *BridgeRouter {
	return &BridgeRouter{
		pooled:       NewPooledStorage(),
		siloed:       make(map[string]*SiloedStorage),
		siloedTenant: map[string]bool{"regulated-co": true},
	}
}

func (r *BridgeRouter) Route(tenantID string) Storage {
	if r.siloedTenant[tenantID] {
		if _, ok := r.siloed[tenantID]; !ok {
			r.siloed[tenantID] = &SiloedStorage{tenantID: tenantID}
		}
		return r.siloed[tenantID]
	}
	return r.pooled
}

func main() {
	router := NewBridgeRouter()
	router.Route("acme").Save("acme", 100)
	router.Route("regulated-co").Save("regulated-co", 500)
	router.Route("globex").Save("globex", 250)

	if len(router.pooled.rows["acme"]) != 1 {
		panic("expected acme pooled row")
	}
	if len(router.siloed["regulated-co"].rows) != 1 {
		panic("expected regulated-co siloed row")
	}
	fmt.Println("routing verified")
}
```
