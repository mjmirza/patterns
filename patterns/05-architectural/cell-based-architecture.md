---
name: Cell-Based Architecture
slug: cell-based-architecture
family: 05-architectural
category: Architectural
aliases: [Cellular Architecture, Cell Architecture, Shuffle-Sharded Cells]
first_described: "Colm MacCarthaigh and the AWS Builders Library team, re Invent 2019, formalised in the AWS Well-Architected guide Reducing the Scope of Impact with Cell-Based Architecture"
maturity: established
related: [bulkhead, deployment-stamps, sharding, circuit-breaker, service-mesh]
incompatible_with: [shared-database-per-service]
verified: 2026-08-09
---

# Cell-Based Architecture

## 1. Name, aliases, and lineage

The canonical name in AWS documentation is Cell-Based Architecture. The AWS
Well-Architected guide "Reducing the Scope of Impact with Cell-Based
Architecture" states the origin plainly. it borrows the term from the bulkhead
in a ship, the vertical partition wall that subdivides a hull into
self-contained, watertight compartments so a breach floods one compartment,
not the whole vessel (AWS Well-Architected, "What is a cell-based
architecture?", https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/what-is-a-cell-based-architecture.html,
verified 2026-08-09). The guide names three components that recur across
every real implementation. the cell, an independent instance of the complete
workload, the cell router, "the thinnest possible layer" that maps a request
to a cell and does nothing else, and the control plane, which provisions,
de-provisions and migrates cells and their tenants (same source).

The pattern is documented publicly at AWS under this name from at least
re Invent 2019, in a talk by Colm MacCarthaigh, and carried forward into the
Builders Library article "Workload isolation using shuffle-sharding" (AWS
Builders Library, https://aws.amazon.com/builders-library/workload-isolation-using-shuffle-sharding/,
verified 2026-08-09) and the dedicated Well-Architected guide cited above.
Slack's engineering team uses the word cellular rather than cell-based for the
same idea applied at the availability-zone level, in "Slack's Migration to a
Cellular Architecture" (Slack Engineering,
https://slack.engineering/slacks-migration-to-a-cellular-architecture/,
verified 2026-08-09). Microsoft documents a closely related shape under a
different name, the Deployment Stamps pattern, and explicitly notes the
overlap. "Each copy is called a stamp, or sometimes a service unit, scale
unit, or cell" (Azure Architecture Center, "Deployment Stamps pattern",
https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp,
verified 2026-08-09).

Three names are used loosely enough in industry conversation that
distinguishing them matters, in the judgement of this entry.

- **Cell-based architecture (AWS usage).** Emphasis on fault isolation and
  blast-radius containment. A cell is a full, independently operable copy of
  the workload's runtime path, and cells are usually numerous, small, and
  interchangeable from the router's point of view.
- **Deployment stamps (Azure usage).** Emphasis on multi-tenant scale-out and
  regional placement. A stamp is the same structural idea, but Azure's own
  documentation treats stamp count as a capacity-planning control first and a
  fault-isolation control second, and explicitly relates it to, and
  distinguishes it from, the Geode and Sharding patterns in the same catalog.
- **Sharding.** A data-partitioning technique, not a full-stack isolation
  technique. A cell almost always contains a shard of data as one of its
  components, but a shard on its own says nothing about whether the compute,
  queueing, and control-plane layers above the data are also isolated. Azure's
  own page states this relationship directly. "Stamps run independently, so
  they implicitly shard your data" (same Azure source as above).

This entry uses cell-based architecture as the umbrella term and treats
deployment stamps as the Azure-flavoured name for the identical structural
pattern, because the components, the trade-offs, and the failure modes are the
same under both names.

## 2. Problem and context

A service that runs as one shared, horizontally-scaled deployment behind one
load balancer has a property that is invisible on a calm day and catastrophic
on a bad one. every request, every tenant, and every code path shares the same
fate. A bad deploy, a poison-pill request that crashes a worker, a noisy
tenant that saturates a connection pool, or a networking incident in one
availability zone degrades the service for one hundred percent of customers at
once, because there is only one instance of the system to degrade.

The context in which this becomes a real operational problem, rather than a
theoretical one, has three ingredients.

- The service is large enough, or important enough, that a full outage has a
  cost measured in real money, real trust, or a real SLA breach, and that cost
  is substantially worse than a partial outage of the same duration.
- The workload has a natural partition key already present in nearly every
  request. a tenant ID, a customer ID, a user ID, a geographic region, or a
  resource ID. Slack's incident write-up is explicit that the trigger was a
  single availability-zone networking event that caused "user-impacting
  service degradation" across the whole region, because nothing separated one
  zone's failure from the rest (Slack Engineering source above).
- Blast radius, not raw throughput, is the metric leadership actually cares
  about after an incident review. the question asked after an outage is
  usually "how many customers were affected", not "how many requests per
  second did we serve", and a single shared deployment answers that question
  with the worst possible number every time.

Cell-based architecture exists to change the answer to that question from "all
of them" to "a bounded fraction of them", by giving up some efficiency and
some operational simplicity in exchange for a hard cap on the size of any
single failure.

## 3. Forces

- **Blast radius versus efficiency.** Favoured toward blast radius. Splitting
  a workload into N independent cells means each cell typically runs with its
  own idle headroom, its own connection pools, and its own control plane
  surface, so aggregate resource utilisation is lower than one large pooled
  deployment would achieve. The AWS Well-Architected guide states this
  trade-off directly, listing "higher scalability... higher mean time between
  failure... lower mean time to recovery" as advantages while separately
  warning that "implementing cell-based architecture requires a lot of
  automation and specific tools" (AWS Well-Architected source above,
  synthesised from the guide's stated advantages and considerations sections).
- **Isolation versus operational complexity.** Sacrificed toward isolation.
  Every cell needs its own deploy pipeline, its own dashboards, its own
  on-call visibility, and its own capacity plan. Azure's Deployment Stamps
  page names this cost as "Governance and configuration drift", warning that
  "as the number of stamps increases, it becomes harder to keep security
  policies, role-based access control assignments, network controls,
  observability settings, and service configurations consistent" (Azure
  Architecture Center source above).
- **Consistency versus partition tolerance.** Sacrificed toward partition
  tolerance in the CAP sense at the workload level. Because a cell is defined
  as not sharing state with its siblings, any operation that needs a
  cross-cell consistent view, a global count, a global uniqueness constraint,
  a cross-tenant report, must either be denied, made eventually consistent, or
  routed through a separate aggregation path outside any single cell.
- **Cost versus the resilience goal.** Sacrificed toward the resilience side.
  Azure states this without softening it. "The Deployment Stamps pattern
  deploys multiple copies of your infrastructure components, which
  substantially increases the cost of operating your solution" (same Azure
  source).
- **Team topology.** Favoured. Because a cell is a complete, independently
  deployable unit, a team can own one or more cells end to end, deploy on its
  own cadence, and be paged only for its own cells, which is a genuine
  organisational win separate from the technical one.
- **Latency.** Close to neutral inside a cell, mildly sacrificed at the
  routing hop. The cell router adds one lookup and one hop before a request
  reaches its cell, and that lookup itself becomes a shared, highly-available
  dependency that must not itself become a single point of failure, which is
  why the AWS guide insists the router stay "the thinnest possible layer".
- **Cognitive load.** Sacrificed. An engineer debugging a production issue
  must now first answer "which cell is this customer in" before they can even
  begin to look at logs or metrics, an extra step that does not exist in a
  single shared deployment.

A pattern that gave up nothing here would not be a pattern, it would be free
capacity, and cell-based architecture is explicitly not that. it is a
deliberate purchase of a smaller worst case at the price of a larger typical
case cost.

## 4. Applicability and non-applicability

Reach for cell-based architecture when the following hold.

- The workload already has a stable, wide-ranging partition key present
  on nearly every inbound request, most commonly a tenant ID or customer ID,
  because without one the cell router has nothing reliable to route on.
- A full-service outage is substantially more expensive, in SLA penalties,
  reputational damage, or regulatory exposure, than a partial outage of the
  same absolute duration affecting a bounded fraction of customers.
- The team is willing to build and maintain real automation for cell
  provisioning, deployment, and traffic shifting. AWS's guide is explicit that
  cell-based architecture "requires a lot of automation and specific tools"
  and that observability across cells "is essential to take advantage of all
  the benefits" (AWS Well-Architected source above).
- The service is large enough, in request volume, revenue, or criticality,
  that the added infrastructure cost of running N independent copies is a
  rounding error against the cost of a full outage. Azure names this cost
  directly rather than hiding it, and a workload that cannot absorb it is not
  a fit.
- Different customer segments need different update schedules, data
  residency, or compliance boundaries, since Azure lists exactly this among
  its primary "when to use" reasons, alongside geopolitical and data
  sovereignty requirements (Azure Architecture Center source above).

Do NOT reach for cell-based architecture in these cases, and the reason
matters more than the rule.

- **There is no natural partition key, or the key changes mid-session.** A
  service where a single logical user session legitimately spans multiple
  tenants, or where the routing key cannot be determined until deep inside
  request processing, cannot place the cell router at the edge, which is
  where its value comes from. Forcing a key onto a workload that does not
  have one produces a router that has to inspect payload contents, which
  makes the router itself heavy, exactly what the pattern says it must never
  be.
- **The workload is small enough that a full outage is tolerable.** Azure
  states this plainly. "Your solution is simple and doesn't need to scale to a
  high degree" is one of its explicit non-applicability conditions (same
  source). An internal tool used by twelve people does not need cells.
- **The system needs strong cross-tenant consistency as its normal mode of
  operation**, not as a rare reporting job. A global leaderboard, a shared
  inventory count across all customers, or a single global namespace that
  must never permit a duplicate, works against cell isolation by definition,
  because the whole point of a cell is that it does not know what any other
  cell is doing.
- **The team cannot fund N times the operational surface.** A two-person team
  running a single-region monolith will not gain a benefit from cells, it
  will gain N deploy pipelines and N dashboards to keep in sync with two
  people to do it, which is a net loss, not a gain.
- **The failure mode you are worried about is inside a single, unavoidable
  shared dependency.** If every cell must still call one shared, uncelled
  payment gateway or one shared, uncelled identity provider, cells contain
  nothing, because the actual single point of failure was never partitioned.
  Cell-based architecture only earns its cost when the boundary genuinely
  contains the failure modes that matter.
- **Content is static and can be served from a CDN instead.** Azure lists
  this explicitly among its non-applicability cases, since a stateless static
  asset has no partition-worthy state to isolate in the first place (same
  Azure source).

## 5. Structure

Four participants, named for the role each plays, following the
Well-Architected guide's own terminology plus the addition of the partition
key as a named artefact, since without naming it explicitly engineers tend to
treat it as an implementation detail rather than the load-bearing design
decision it actually is.

- **Partition key.** The value present on (nearly) every request that
  determines which cell owns it. Customer ID, tenant ID, account ID, or a
  geographic region are the common choices. AWS's guide calls the ideal choice
  one that aligns "with the grain of the service, or the natural way that a
  service's workload can be subdivided with minimal cross-cell interactions"
  (AWS Well-Architected source above).
- **Cell router.** A thin, highly-available layer that maps the partition key
  to a cell identifier and forwards or redirects the request there, and does
  nothing else. AWS calls it "the thinnest possible layer" for a reason. any
  logic added here becomes a shared, uncelled dependency and reintroduces the
  single point of failure the pattern exists to remove.
- **Cell.** A complete, independent copy of the workload's runtime, holding
  its own compute, its own data store or data-store partition, and its own
  queues, that can serve any request whose partition key resolves to it
  without calling into a sibling cell for that request's normal path. AWS
  defines it exactly this way. "A complete workload, with everything needed
  to operate independently" (same source).
- **Control plane.** A separate, usually smaller and less request-critical
  system responsible for administrative work. provisioning new cells,
  de-provisioning empty ones, moving a tenant from one cell to another, and
  publishing the partition-key-to-cell mapping that the router consults. AWS
  names this as the third structural component alongside the router and the
  cell (same source). Azure's mapping-store example uses a geo-replicated
  Cosmos DB collection queried by the routing layer as one concrete
  realisation of this component (Azure Architecture Center source above).

The relationship worth stating plainly. the router depends on the control
plane's mapping data but never on any individual cell's internal state, and no
cell depends on any sibling cell for its own request path. The only
cross-cutting dependency that is allowed to exist, and that must itself be
made highly available, is the router-to-control-plane mapping lookup.

## 6. ASCII structure diagram

```
                              +-------------------+
                              |   Control plane    |
                              | provision, migrate, |
                              | publish key->cell   |
                              +----------+----------+
                                         |
                                         | publishes mapping
                                         v
   client --request-->  +-------------------------+
   (carries               |       Cell router        |
    partition key)        | thinnest possible layer, |
                           | key -> cell lookup only  |
                           +------------+--------------+
                                        |
                    +-------------------+-------------------+
                    |                   |                   |
                    v                   v                   v
           +----------------+  +----------------+  +----------------+
           |     Cell 1     |  |     Cell 2     |  |     Cell N     |
           |----------------|  |----------------|  |----------------|
           | compute        |  | compute        |  | compute        |
           | queue          |  | queue          |  | queue          |
           | data partition |  | data partition |  | data partition |
           +----------------+  +----------------+  +----------------+

   No arrow connects Cell 1 to Cell 2. no cell calls a sibling
   for a request on its own partition key. a failure inside
   one cell never crosses this boundary.
```

## 7. Dynamics

Two flows matter, request routing and traffic shifting during an incident.
Both are drawn from the mechanics described in the AWS Well-Architected guide
and Slack's engineering post cited above.

```
Client            Cell Router          Control Plane        Cell 3
  |                    |                     |                 |
  |-- request(key=T) ->|                     |                 |
  |                    |-- lookup(T) ------->|                 |
  |                    |<-- cell = 3 --------|                 |
  |                    |   (cached after     |                 |
  |                    |    first lookup)    |                 |
  |                    |-- forward request ------------------->|
  |                    |                     |    processes    |
  |                    |                     |    entirely     |
  |                    |                     |    inside Cell 3|
  |<-- response -----------------------------------------------|
  |                    |                     |                 |

Incident on Cell 3, traffic drain (modelled on Slack's weighted-cluster
approach, "Slack's Migration to a Cellular Architecture"):

  Operator          Control Plane           Cell Router
     |                    |                       |
     |-- drain Cell 3 --->|                       |
     |                    |-- publish weight ---->|
     |                    |   Cell3=0%, others+-->|
     |                    |   (gradual, e.g. 1%   |
     |                    |    steps per Slack's  |
     |                    |    description)       |
     |                    |                       |-- new requests
     |                    |                       |   stop reaching
     |                    |                       |   Cell 3
     |                    |                       |
     |                    |         in-flight requests already
     |                    |         inside Cell 3 finish there,
     |                    |         they are not aborted mid-flight
```

Slack's own description of this second flow states that traffic can be
shifted "gradually (with 1% granularity) and gracefully (all in-flight
requests get completed in the cell being drained)" (Slack Engineering source
above), which is why the diagram distinguishes new request routing from
already in-flight requests explicitly. a naive implementation that simply cuts
off a cell instantly turns a contained incident into a set of hard request
failures for everything that happened to be mid-flight.

## 8. Implementation variants

**Availability-zone cells.** Each cell is pinned to a single availability
zone, and every service within it talks only to peers in the same zone.
Slack's implementation is this variant, chosen specifically because the
triggering incident was an AZ-scoped networking failure (Slack Engineering
source above). Cheapest to adopt when the workload already runs across
multiple AZs, because the compute footprint does not necessarily grow, only
the routing and isolation discipline changes.

**Tenant or customer cells.** Each cell owns a fixed set of tenants,
determined by the control plane, independent of geography. This is the
default shape implied by AWS's generic "partition key" language and is the
natural fit for B2B SaaS, where tenant isolation, not zone isolation, is the
primary concern.

**Regional stamps (Azure's Deployment Stamps).** Each stamp is deployed to
one Azure region and serves a subset of tenants pinned to that region, and a
region can host more than one stamp when a single stamp's capacity is
exceeded, exactly as shown in Azure's own five-stamp example spanning three
regions (Azure Architecture Center source above). This variant folds
geography and tenant partitioning into one decision and is the shape
recommended when data residency or latency-to-region matters as much as
blast radius.

**Shuffle-sharded cells.** Rather than assigning each tenant to exactly one
cell, each tenant is assigned to a small, pseudo-random combination of two or
more cells drawn from a larger pool, so that any single tenant's noisy or
poisoned traffic is spread thin across a shard that overlaps only partially
with any other tenant's shard. The AWS Builders Library article on this
technique states the effect concretely. with eight cells partitioned into
virtual shards of two, there are 28 unique two-cell combinations, so a bad
actor mapped to one shard degrades at most that shard's specific overlap
rather than a whole dedicated cell (AWS Builders Library, "Workload isolation
using shuffle-sharding", https://aws.amazon.com/builders-library/workload-isolation-using-shuffle-sharding/,
verified 2026-08-09). This variant costs substantially more router complexity
and is reserved for multi-tenant systems where any single tenant misbehaving,
not only any single cell failing, is the threat being defended against.

**Cell-per-container-orchestration-namespace.** A cell can also be
implemented as a Kubernetes namespace or an ECS service group behind a
shared, thin routing layer, treating the container platform's existing
isolation primitives, network policies, resource quotas, separate node
pools, as the cell boundary rather than standing up entirely separate
physical infrastructure per cell. This is engineering judgement rather than
a directly sourced claim. it follows from applying the same router, cell,
control-plane structure defined in dimension 5 onto a shared cluster's
native isolation primitives. Cheapest variant to adopt for a team already
running on a shared cluster, at the cost of a weaker isolation guarantee than
fully separate infrastructure, since a cluster-level control-plane failure
can still cross cell boundaries.

**Platform note.** Cell-based architecture is a system-topology pattern, not
a language-level construct, so there is no idiomatic per-language variant
the way Factory Method has one. what differs by platform is the routing
mechanism. Kubernetes and service-mesh environments typically implement the
router as an ingress controller or an Envoy xDS control plane consulting an
external mapping store, exactly as Slack's Rotor system does (Slack
Engineering source above), while simpler deployments implement the router as
an application-layer function, shown in the code examples below.

## 9. Known production uses

**Slack, cellular architecture pinned to availability zones.** Slack migrated
its most critical user-facing services to a cell-based design after a June
2021 AZ-scoped networking incident caused visible errors across the whole
region, choosing an availability zone as the cell boundary and Envoy
weighted-cluster routing, controlled by an internal system called Rotor, to
drain traffic away from an unhealthy AZ with 1 percent granularity. Slack
Engineering, "Slack's Migration to a Cellular Architecture",
https://slack.engineering/slacks-migration-to-a-cellular-architecture/,
verified 2026-08-09.

**Amazon's own DNS and internal services, shuffle-sharded cells.** The AWS
Builders Library documents that AWS itself uses shuffle sharding across
cells inside its own services, so that a single misbehaving customer or
resource is contained to a small overlapping combination of cells rather
than one dedicated cell or the whole fleet. Colm MacCarthaigh, AWS Builders
Library, "Workload isolation using shuffle-sharding",
https://aws.amazon.com/builders-library/workload-isolation-using-shuffle-sharding/,
verified 2026-08-09.

**Microsoft Azure reference architecture, Deployment Stamps for
multitenant SaaS.** Azure's own architecture guidance documents the pattern
as the recommended shape for SaaS vendors that need to scale near-linearly
across tenants, isolate specific customers onto dedicated infrastructure, and
run different update schedules per customer segment, with a worked example
routing through Azure Front Door and API Management to five stamps spread
across three regions. Microsoft, Azure Architecture Center, "Deployment
Stamps pattern", https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp,
verified 2026-08-09.

**AWS Well-Architected reference guidance itself, cell-based workloads on
AWS.** AWS publishes a dedicated Well-Architected guide, distinct from the
generic Well-Architected Framework, entirely devoted to cell-based
architecture as a recommended pattern for AWS customers building dependable
multi-tenant and high-scale workloads, naming cell router, cell, and control
plane as the three components every implementation needs. AWS
Well-Architected, "Reducing the Scope of Impact with Cell-Based
Architecture", https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/reducing-scope-of-impact-with-cell-based-architecture.html,
verified 2026-08-09.

## 10. Consequences

Positive.

- A failure inside one cell, a bad deployment, a poison-pill request, a
  resource leak, or an AZ networking incident, is contained to that cell's
  share of traffic instead of degrading every customer at once, and AWS
  quantifies the shape of this benefit directly. ten cells serving equal
  shares of traffic means a single cell's failure affects roughly ten percent
  of requests rather than one hundred percent (AWS Well-Architected source
  above).
- Deployments and rollbacks can proceed cell by cell, giving a natural, low
  risk canary boundary with no extra tooling beyond the cell router already
  required for normal operation.
- Traffic can be shifted away from an unhealthy cell gradually and gracefully,
  as Slack's 1 percent granularity weighted-cluster mechanism demonstrates,
  without hard-cutting requests that are already mid-flight.
- Teams can own cells end to end, which aligns deployment and on-call
  boundaries with organisational boundaries rather than forcing every team to
  coordinate changes to one shared deployment.
- New capacity scales out horizontally by adding cells, which AWS notes
  supports "scale-out over scale-up" as one of the pattern's core advantages,
  avoiding the cliff-edge cost curves that a single, ever-larger deployment
  eventually hits.

Negative.

- Infrastructure cost rises, sometimes substantially, because idle headroom,
  connection pools, and control-plane surface area are now duplicated per
  cell rather than pooled once. Azure states this without qualification as a
  named consideration of the pattern.
- Operational surface area multiplies. dashboards, alerts, deploy pipelines,
  and security policy all need to exist, and stay consistent, per cell, and
  Azure separately names configuration drift across stamps as a real,
  growing risk as stamp count increases.
- Cross-cell operations become genuinely hard. counting total customers,
  building a global report, or moving a single tenant from one cell to
  another all require either querying every cell and aggregating, a
  centralised reporting pipeline outside any cell, or custom migration logic
  with its own consistency and backplane requirements, which Azure calls out
  explicitly under "Moving between stamps".
- The cell router and the control-plane mapping store become a new, shared,
  must-be-highly-available dependency in their own right, and if that
  dependency is not kept genuinely thin and genuinely reliable, it becomes
  the single point of failure the whole pattern exists to eliminate.
- Debugging becomes a two-step process for every incident. first identify
  which cell the affected customer is in, then debug inside that cell, adding
  latency to every human investigation even when the underlying bug would
  have been equally fast to find in a single shared deployment.

## 11. Failure modes and misuse

**The router grows a brain.** Symptom. The routing layer starts making
business decisions, applying rate limits, doing authentication, or inspecting
request bodies to decide routing, and it becomes a single deployable service
that every team is afraid to touch. Cause. Feature creep on the one component
the pattern explicitly demands stay minimal. AWS's own phrase for the router
is "the thinnest possible layer" for exactly this reason. Fix. Push every
piece of logic beyond key extraction and lookup back into the cells
themselves, or into a genuinely separate, independently-scaled edge layer
that sits in front of the cell router rather than inside it.

**Cells that quietly share a database.** Symptom. Two "isolated" cells both
degrade during the same incident even though the incident report says only
one cell's compute was affected. Cause. The cells share a single underlying
data store, a single message broker cluster, or a single third-party
dependency that was never itself partitioned, so the compute-level isolation
was cosmetic. Fix. Audit every dependency a cell calls and confirm each one
either has its own per-cell instance or is explicitly documented and
monitored as an accepted shared dependency outside the isolation boundary.

**Uneven cell sizing.** Symptom. One cell's dashboards are consistently
hotter than its siblings, and incidents disproportionately originate there.
Cause. Tenants were assigned to cells without a capacity-aware policy, so a
handful of large customers landed in the same cell and pushed it past the
sizing assumptions the rest of the fleet was built around. Fix. Cap cell size
by a proxy metric agreed up front, monitor per-cell utilisation against that
cap, per Azure's explicit "Scale-out policies" guidance to monitor available
and used capacity and proactively provision new cells, and rebalance tenants
through the control plane before a cell reaches its cap.

**Migration between cells with no backplane.** Symptom. Moving a single
tenant off an overloaded cell takes a maintenance window, manual scripts, and
visible downtime for that tenant, every single time. Cause. The control plane
was built to provision new cells but never to move a tenant's live data and
in-flight state between two existing cells. Azure names this directly as a
real cost of the pattern, warning that a backplane for cross-stamp
communication "further increases the complexity of your solution." Fix.
Design the tenant-migration path, dual-write or dual-read during migration,
a cutover point, and a rollback plan, before the first tenant needs to move,
not during the incident that forces the first move.

**Instant cutover instead of graceful drain.** Symptom. Draining an unhealthy
cell produces a spike of hard failures for requests that were already in
flight, even though the goal was to reduce customer impact. Cause. The
traffic-shifting mechanism sets a cell's weight to zero all at once instead
of ramping it down and letting in-flight work finish. Slack's own
description of its drain mechanism specifically calls out gradual,
1-percent-granularity shifting and letting in-flight requests complete as the
correct shape. Fix. Implement weighted, incremental traffic shifting at the
router, and treat "cells being drained still serve in-flight requests" as a
hard requirement of the drain mechanism, not an optimisation.

**No cross-cell observability.** Symptom. An operator can see that overall
error rate rose but cannot tell within minutes which cell is responsible.
Cause. Metrics, logs, and traces are collected per cell but never aggregated
with a consistent cell-identifying label, so answering "which cell" requires
manually checking each cell's dashboard in turn. AWS calls observability
"essential to take advantage of all the benefits" of the pattern for exactly
this reason. Fix. Tag every metric, log line, and trace with the cell
identifier at the point of emission and build one fleet-wide dashboard that
can be filtered or grouped by cell, not N separate per-cell dashboards that a
human has to visit one at a time.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Cell-based architecture | Single shared deployment | Database sharding alone | Bulkhead (in-process) | Multi-region active-active (single fleet) |
|---|---|---|---|---|---|
| Blast radius on a bad deploy | Bounded to one cell's share | 100 percent of traffic | 100 percent of compute, data isolated only | Bounded to one resource pool inside a process | Bounded to one region, not below it |
| Blast radius on a noisy tenant | Bounded, better with shuffle sharding | 100 percent, one tenant can starve everyone | Bounded to that tenant's shard's compute, if compute is also shard-aware | Bounded only if the tenant's calls hit an isolated pool | Not addressed, tenants still share regional compute |
| Infrastructure cost | High, N times the headroom | Lowest, one pooled deployment | Medium, data layer duplicated, compute usually shared | Low, isolation is a code-level construct | High, but shared with the same goal already being paid for |
| Operational surface | High, N pipelines and dashboards | Lowest, one of everything | Medium, one extra dimension on the data layer | Lowest, contained inside existing services | High, but usually already budgeted for other reasons |
| Cross-tenant consistency | Hard, needs an aggregation path outside any cell | Easy, one shared state | Hard for cross-shard, easy within a shard | Easy, still one process | Hard across regions, easier within one |
| Deploy and rollback granularity | Per cell, natural canary boundary | All or nothing | All or nothing at the compute layer | All or nothing at the process level | Per region, coarser than per cell |
| Team ownership alignment | Strong, a team can own whole cells | Weak, one shared deployment for everyone | Weak to medium | Weak, still one shared process | Medium, teams can align to regions |
| Addresses a single-region networking incident | Yes, if cells are zone-scoped | No | No, only the data layer moves | No | Yes, but at a coarser, more expensive granularity |

Reading of the table. cell-based architecture wins decisively on blast radius
and deployment granularity, and it is the only row in this table that
addresses a noisy-tenant failure mode as well as an infrastructure failure
mode. It loses decisively on cost and operational surface against every
lighter-weight alternative. Database sharding alone is the cheapest partial
substitute when the actual failure being defended against is a data-layer
hot spot rather than a compute-layer cascading failure, since it isolates
storage without duplicating the whole runtime. Multi-region active-active
addresses a similar class of concern at a coarser grain and is often already
justified for latency reasons independent of blast radius, so the two
patterns frequently compose. cells within a region, regions across the
globe, rather than compete.

## 13. Related and incompatible patterns

- **Bulkhead pattern.** The direct conceptual ancestor, cited explicitly in
  AWS's own naming rationale. bulkhead is usually applied inside one process
  or one service, isolating thread pools or connection pools, while
  cell-based architecture applies the identical idea at the scale of an
  entire independently-deployable system. A cell can, and usually should,
  contain bulkheads internally as a second, finer-grained layer of isolation.
- **Deployment Stamps pattern.** Effectively the same structural pattern
  under a different name, with Azure's own catalog explicitly stating that a
  stamp is "sometimes" called a cell. Where this entry and the Azure Deployment
  Stamps page differ is emphasis. Azure leans toward multi-tenant scale-out
  and regional placement as the primary motivation, this entry, following the
  AWS documentation, leans toward blast-radius containment as the primary
  motivation. The two motivations are not in conflict and most real
  implementations pursue both at once.
- **Sharding.** A necessary but not sufficient component of most cells. every
  cell that owns data almost always shards that data by the same partition
  key the router uses, but sharding data alone, with a single shared compute
  fleet reading from all shards, does not produce cell-level isolation and
  does not contain a bad deployment or a compute-layer cascading failure.
- **Circuit breaker.** Composes cleanly and operates at a different layer.
  a circuit breaker protects one service from a failing downstream call it is
  actively making, while a cell boundary protects everything outside the
  cell from a failure happening inside it. A well-built cell still uses
  circuit breakers internally for its own outbound calls.
- **Service mesh.** A common implementation vehicle for the cell router and
  for cell-internal service-to-service isolation, as Slack's use of Envoy and
  its internal xDS control plane, Rotor, demonstrates. A service mesh is not
  itself cell-based architecture, it is infrastructure that a cell-based
  design can be built on top of.
- **Shared database per service (incompatible).** A design where multiple
  logically-separate services all read and write one shared database
  instance actively conflicts with cell-based architecture, because the
  shared database becomes an uncelled dependency that reintroduces the single
  point of failure the pattern exists to remove, regardless of how well the
  compute layer above it is partitioned. Adopting cells without first
  addressing a shared database dependency produces the false sense of
  isolation described in dimension 11's second failure mode.
- **Blue-green and canary deployment.** Complementary rather than competing.
  cells give a natural, tenant-real canary boundary (deploy to one cell
  first, watch it, then roll forward), while blue-green deployment is
  typically applied within a single cell's own deploy pipeline to reduce risk
  further at an even finer grain.

## 14. Refactoring path in and out

Introducing the pattern into a system that runs as one shared deployment.
There is no single named refactoring for this in the classical refactoring
catalogs, because the scope is architectural rather than code-level, but the
steps below follow the sequence implied by AWS's own guidance and by the
patterns already described in dimension 8.

1. Identify the partition key. confirm a stable, wide-ranging identifier
   is present on nearly every inbound request today, and audit how many
   request paths lack it, since those paths will need special handling or a
   cell-agnostic shared path.
2. Introduce the control-plane mapping store first, even before any second
   cell exists, mapping every current partition key value to a single cell
   identifier, "cell-1". this makes zero behavioural difference today and
   proves the mapping mechanism works under real traffic.
3. Introduce the cell router as a pass-through in front of the existing
   deployment, consulting the mapping store and forwarding every request to
   "cell-1", the only cell that exists. Confirm latency overhead from this
   extra hop is acceptable before proceeding.
4. Stand up a second, fully independent copy of the deployment, "cell-2",
   with its own compute and its own data partition, and migrate a small,
   low-risk slice of tenants to it via the control plane. Watch its
   dashboards in isolation.
5. Audit every cross-cell dependency this migration surfaces, shared caches,
   shared message topics, shared third-party API keys with global rate
   limits, and either duplicate them per cell or explicitly document and
   monitor them as accepted shared dependencies.
6. Build the graceful traffic-shifting mechanism, weighted routing with
   incremental steps and in-flight request completion, before treating the
   pattern as operationally complete, since an instant-cutover router turns
   every future incident response into a source of additional hard failures.
7. Repeat steps 4 through 6, adding cells and rebalancing tenants, until the
   fleet reaches the target cell count and cell-size cap agreed in
   capacity planning.

Removing the pattern when it stops earning its place. the honest signal that
cells should be consolidated is a workload that has shrunk, in traffic,
tenant count, or criticality, to the point where the fixed per-cell
operational overhead now costs more than the blast-radius protection it buys.

1. Confirm the reduction in scale is durable, not a temporary dip, since
   consolidating and later re-splitting cells is expensive in both directions.
2. Pick a single surviving cell as the consolidation target and migrate
   tenants from the remaining cells into it through the same control-plane
   migration path built in step 5 above, one cell at a time.
3. Once a cell is empty, de-provision it through the control plane and remove
   its entry from the routing mapping.
4. When exactly one cell remains, the cell router becomes a pure pass-through
   again, at which point it can be safely removed and traffic pointed
   directly at the remaining deployment, completing the reverse of step 3 in
   the introduction path above.
5. Retain the partition key on requests even after removing cells, since
   re-adding cell-based routing later is substantially cheaper if the key never
   disappeared from the request shape in the first place.

## 15. Testing and verification

Easier because of the pattern.

- Failure injection can be scoped to exactly one cell, letting a team run
  fault-injection experiments, kill a database, saturate CPU, drop network
  packets, against a real cell serving real (or shadow) traffic while every
  other cell continues serving customers normally, which is a substantially
  safer blast radius for fault-injection testing than testing against the
  single production deployment of a non-celled system.
- A new cell can be validated with synthetic or shadow traffic before it
  receives any real tenant, since the control plane already has to support
  provisioning a cell with zero tenants assigned as a normal step in the
  scale-out path.
- Canary deployments have a natural, genuine boundary. roll a new build to
  one cell, watch its error rate and latency against its siblings for a
  fixed window, and only then advance to the rest of the fleet, without
  needing separate canary tooling beyond the cell router already in place.

Harder because of the pattern.

- End-to-end tests that exercise a cross-tenant workflow, an admin report
  spanning all customers, a support tool that looks up any tenant by ID, now
  need to exercise the fan-out-and-aggregate path across every cell rather
  than a single query, and that fan-out path is itself new production code
  that needs its own test coverage.
- Testing the router and the control plane in isolation from any real cell
  requires a fake or minimal cell that can accept traffic and report health,
  since the router's correctness depends on believable cell behaviour, not
  only a static mapping table.
- Migration correctness, moving a tenant from cell A to cell B without data
  loss, without a window where the tenant is unreachable, and without
  duplicate processing during the cutover, is a genuinely hard distributed
  systems problem to test, and Azure's own naming of "moving between stamps"
  as a hard problem is a signal that this deserves dedicated integration
  tests rather than being treated as a corner case.

Techniques that apply.

- **Per-cell fault-injection experiments.** Inject a specific fault, a full
  cell outage, a database connection exhaustion, a poison-pill message, into
  one cell under real or shadowed traffic and assert two things. that the
  target cell degrades as expected, and that every sibling cell's error rate
  and latency stay flat throughout the experiment. The second assertion is
  the one that actually proves isolation, not the first.
- **Router contract tests against a mapping fixture.** A fixed, versioned
  fixture of partition-key-to-cell mappings, run through the router in
  isolation, asserting deterministic routing for every key in the fixture and
  a defined, tested fallback behaviour for an unknown key, since an unknown
  key falling through to an arbitrary cell is a realistic production bug
  class.
- **Migration integration test with a synthetic tenant.** Provision a
  synthetic tenant with representative data volume, run it through the full
  migration path from cell A to cell B under simulated concurrent traffic,
  and assert zero data loss and a bounded, measured window of degraded
  availability, treating that window's length as a regression-tracked
  metric over time, not a one-off pass or fail.
- **Cross-cell aggregation golden tests.** For any admin or reporting path
  that fans out across cells, load a fixed, known data set spread across
  multiple cells and assert the aggregated result matches a precomputed
  golden value, catching the class of bug where one cell is silently
  skipped during fan-out.

## 16. Observability signals

The pattern's entire value proposition depends on being able to see per-cell
health at a glance, so observability is not optional polish here, it is load
bearing. AWS's guide states this as a hard requirement rather than a nice
to have.

What to record, all consistently tagged with the cell identifier at the point
of emission.

- Request count, error rate, and latency percentiles per cell, so a
  fleet-wide dashboard can be grouped or filtered by cell without visiting N
  separate dashboards.
- Per-cell capacity utilisation against the agreed sizing cap, since Azure's
  guidance is explicit that stamps should be monitored for "available and
  used capacity" so new stamps can be provisioned proactively rather than
  reactively.
- Router-level metrics, separate from any individual cell's metrics. lookup
  latency against the control-plane mapping store, cache hit rate for that
  lookup, and the count and rate of requests falling through to any fallback
  or default cell.
- Cell-drain progress during an incident, the live traffic-weight percentage
  currently assigned to each cell, so an operator running Slack-style
  gradual draining can watch the shift happen in real time rather than
  guessing whether the weight change has propagated.
- Tenant-to-cell distribution as a gauge, so an operator can see at a glance
  whether tenant assignment across cells is roughly even or has drifted
  toward a hot cell.
- Control-plane migration events, start, progress, completion or rollback,
  for every tenant migration between cells, since a stuck or silently-failed
  migration is otherwise invisible until the tenant notices something is
  wrong.

A healthy fleet on a dashboard. every cell's error rate and latency track
closely with its siblings, capacity utilisation sits comfortably below the
agreed cap on every cell, and the tenant-distribution gauge is roughly flat
across cells. A single cell running visibly hotter than the rest, with no
active migration in progress, is a scale-out or rebalancing signal, not
necessarily an incident.

A failing fleet. one cell's error rate spikes while every sibling stays flat,
which is the isolation working as intended and the signal to begin a
Slack-style graceful drain of that specific cell. Router-level lookup
latency rising fleet-wide, independent of any single cell's health, points
at the control-plane mapping store itself becoming a bottleneck, exactly the
uncelled single point of failure the pattern is meant to avoid, and deserves
the same urgency as a cell-level incident, arguably more, since it can
degrade every cell at once. A tenant-distribution gauge that drifts
steadily toward one cell over weeks, with no corresponding capacity
adjustment, is the slow-motion version of the uneven-sizing failure mode
described in dimension 11.

## 17. Security and privacy implications

Cell-based architecture has real, non-neutral security and privacy
consequences precisely because its whole purpose is controlling which
systems can see which customers' data and traffic.

**Isolation as a compliance and data-residency control.** Because a cell is
a genuinely separate deployment, it can be pinned to a specific region or
jurisdiction to satisfy data-residency or data-sovereignty requirements,
which Azure's own guidance names as one of the primary reasons to reach for
the pattern. done well, this turns cell placement into an enforceable
technical control rather than a policy document that hopes nobody routes a
request the wrong way.

**Cross-tenant leakage risk concentrated at the router and control plane.**
Every guarantee the pattern makes about tenant A never touching tenant B's
data collapses to a single question. does the router and the control-plane
mapping ever misroute a request to the wrong cell. A bug in partition-key
extraction, a stale cache entry in the mapping lookup during an in-progress
migration, or an unauthenticated internal call that bypasses the router
entirely, each turns a supposedly hard tenant boundary into a soft one. this
makes the router and the mapping store, together, the single highest-value
security review target in the whole system, disproportionate to their small
code size.

**The migration window is a genuine attack and error surface.** During the
period a tenant is being moved from one cell to another, the system must, by
construction, briefly know about that tenant's data in two places at once.
Any authorization check, cache, or audit log that assumes a tenant lives in
exactly one cell at all times can be fooled or confused during this window,
and an attacker with insider knowledge of migration timing has a narrower
but real opportunity to exploit stale authorization state in the
soon-to-be-decommissioned cell. Migration logic should be reviewed with the
same rigour as authentication logic, not treated as a purely operational
concern.

**Noisy-tenant containment is itself a security property, not only an
availability one.** A tenant that is compromised, or is deliberately abusive,
generating a flood of traffic, is contained by cell boundaries the same way
an accidental failure is, which limits the blast radius of an active attack
originating from inside one tenant's account, not only the blast radius of
an accidental bug. Shuffle sharding strengthens this specifically against a
targeted or coordinated multi-tenant attack, since AWS's own explanation of
the technique frames it explicitly in terms of limiting the scope of impact
from misbehaving customers, which includes malicious ones.

On raw data-at-rest or data-in-transit encryption the pattern is neutral,
each cell still needs the same encryption, key management, and access
control discipline any single deployment would need, cell-based architecture
neither weakens nor strengthens that layer on its own.

## 18. References

1. AWS Well-Architected. "Reducing the Scope of Impact with Cell-Based
   Architecture", section "What is a cell-based architecture?".
   https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/what-is-a-cell-based-architecture.html
   Verified 2026-08-09. Source for the bulkhead origin story, the definitions
   of cell, cell router, and control plane, the partition-key and grain
   concept, and the ten-cell blast-radius example.
2. Colm MacCarthaigh, AWS Builders Library. "Workload isolation using
   shuffle-sharding".
   https://aws.amazon.com/builders-library/workload-isolation-using-shuffle-sharding/
   Verified 2026-08-09. Source for the shuffle-sharding variant, the
   eight-cell twenty-eight-combination example, and AWS's own internal use of
   the technique.
3. Slack Engineering. "Slack's Migration to a Cellular Architecture".
   https://slack.engineering/slacks-migration-to-a-cellular-architecture/
   Verified 2026-08-09. Source for the availability-zone cell variant, the
   June 2021 triggering incident, the Envoy and Rotor routing mechanism, and
   the 1-percent-granularity graceful traffic-draining description.
4. Microsoft, Azure Architecture Center. "Deployment Stamps pattern".
   https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp
   Verified 2026-08-09. Source for the stamp terminology and its explicit
   equivalence to cell, the applicability and non-applicability lists, the
   cost, governance-drift, and cross-stamp-migration considerations, and the
   five-stamp three-region worked example.
5. AWS Well-Architected. "Reducing the Scope of Impact with Cell-Based
   Architecture" (guide landing page).
   https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/reducing-scope-of-impact-with-cell-based-architecture.html
   Verified 2026-08-09. Source for AWS treating cell-based architecture as a
   dedicated recommended pattern in its own right, distinct from the general
   Well-Architected Framework, and as the fourth named production reference.

## Code examples

Three languages, TypeScript, Python, and Go, chosen because a cell router is
at its base an application-layer routing decision that all three express
cleanly, and because the pattern has no real language-specific idiom
the way an object-oriented creational pattern does. Each example implements a
minimal, self-contained cell router. stable hashing of a partition key onto a
fixed cell list, a mapping override for explicit tenant placement (the
control-plane concern), and a health-aware fallback that skips an unhealthy
cell rather than routing into it, modelling the drain behaviour described in
dimension 7 in its simplest possible form.

### TypeScript

```typescript
interface Cell {
  id: string;
  healthy: boolean;
  handle(tenantId: string): string;
}

class CellRouter {
  private readonly cells: Cell[];
  private readonly overrides = new Map<string, string>();

  constructor(cells: Cell[]) {
    if (cells.length === 0) throw new Error("router needs at least one cell");
    this.cells = cells;
  }

  // control-plane concern: pin a tenant to a specific cell explicitly.
  assign(tenantId: string, cellId: string): void {
    this.overrides.set(tenantId, cellId);
  }

  private hash(key: string): number {
    let h = 0;
    for (let i = 0; i < key.length; i++) {
      h = (h * 31 + key.charCodeAt(i)) >>> 0;
    }
    return h;
  }

  private candidateCell(tenantId: string): Cell {
    const pinned = this.overrides.get(tenantId);
    if (pinned) {
      const cell = this.cells.find((c) => c.id === pinned);
      if (cell) return cell;
    }
    const index = this.hash(tenantId) % this.cells.length;
    return this.cells[index];
  }

  route(tenantId: string): string {
    const primary = this.candidateCell(tenantId);
    if (primary.healthy) return primary.handle(tenantId);

    // primary cell is draining or down: fall through the ring once.
    for (const cell of this.cells) {
      if (cell.healthy) return cell.handle(tenantId);
    }
    throw new Error("no healthy cell available");
  }
}

class InMemoryCell implements Cell {
  healthy = true;
  constructor(public readonly id: string) {}
  handle(tenantId: string): string {
    return `served ${tenantId} by ${this.id}`;
  }
}

const cells = [new InMemoryCell("cell-1"), new InMemoryCell("cell-2"), new InMemoryCell("cell-3")];
const router = new CellRouter(cells);
router.assign("tenant-vip", "cell-2");

console.log(router.route("tenant-vip"));
console.log(router.route("tenant-42"));

cells[1].healthy = false; // simulate draining cell-2
console.log(router.route("tenant-vip")); // falls through to a healthy cell
```

### Python

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Cell:
    id: str
    healthy: bool = True

    def handle(self, tenant_id: str) -> str:
        return f"served {tenant_id} by {self.id}"


class CellRouter:
    def __init__(self, cells: list[Cell]) -> None:
        if not cells:
            raise ValueError("router needs at least one cell")
        self._cells = cells
        self._overrides: dict[str, str] = {}

    def assign(self, tenant_id: str, cell_id: str) -> None:
        # control-plane concern: pin a tenant to a specific cell explicitly.
        self._overrides[tenant_id] = cell_id

    def _candidate(self, tenant_id: str) -> Cell:
        pinned = self._overrides.get(tenant_id)
        if pinned:
            for cell in self._cells:
                if cell.id == pinned:
                    return cell
        index = hash(tenant_id) % len(self._cells)
        return self._cells[index]

    def route(self, tenant_id: str) -> str:
        primary = self._candidate(tenant_id)
        if primary.healthy:
            return primary.handle(tenant_id)

        for cell in self._cells:
            if cell.healthy:
                return cell.handle(tenant_id)
        raise RuntimeError("no healthy cell available")


if __name__ == "__main__":
    cells = [Cell("cell-1"), Cell("cell-2"), Cell("cell-3")]
    router = CellRouter(cells)
    router.assign("tenant-vip", "cell-2")

    print(router.route("tenant-vip"))
    print(router.route("tenant-42"))

    cells[1].healthy = False  # simulate draining cell-2
    print(router.route("tenant-vip"))
```

### Go

```go
package main

import (
	"errors"
	"fmt"
	"hash/fnv"
)

type Cell struct {
	ID      string
	Healthy bool
}

func (c *Cell) Handle(tenantID string) string {
	return fmt.Sprintf("served %s by %s", tenantID, c.ID)
}

type CellRouter struct {
	cells     []*Cell
	overrides map[string]string
}

func NewCellRouter(cells []*Cell) (*CellRouter, error) {
	if len(cells) == 0 {
		return nil, errors.New("router needs at least one cell")
	}
	return &CellRouter{cells: cells, overrides: map[string]string{}}, nil
}

// Assign is a control-plane concern: pin a tenant to a specific cell.
func (r *CellRouter) Assign(tenantID, cellID string) {
	r.overrides[tenantID] = cellID
}

func (r *CellRouter) candidate(tenantID string) *Cell {
	if pinned, ok := r.overrides[tenantID]; ok {
		for _, c := range r.cells {
			if c.ID == pinned {
				return c
			}
		}
	}
	h := fnv.New32a()
	h.Write([]byte(tenantID))
	index := int(h.Sum32()) % len(r.cells)
	if index < 0 {
		index += len(r.cells)
	}
	return r.cells[index]
}

func (r *CellRouter) Route(tenantID string) (string, error) {
	primary := r.candidate(tenantID)
	if primary.Healthy {
		return primary.Handle(tenantID), nil
	}
	for _, c := range r.cells {
		if c.Healthy {
			return c.Handle(tenantID), nil
		}
	}
	return "", errors.New("no healthy cell available")
}

func main() {
	cells := []*Cell{
		{ID: "cell-1", Healthy: true},
		{ID: "cell-2", Healthy: true},
		{ID: "cell-3", Healthy: true},
	}
	router, err := NewCellRouter(cells)
	if err != nil {
		panic(err)
	}
	router.Assign("tenant-vip", "cell-2")

	result, _ := router.Route("tenant-vip")
	fmt.Println(result)

	result, _ = router.Route("tenant-42")
	fmt.Println(result)

	cells[1].Healthy = false // simulate draining cell-2
	result, _ = router.Route("tenant-vip")
	fmt.Println(result)
}
```

All three examples were run locally against their respective toolchains
(`npx tsc` plus `node`, `python3`, and `go run`) and produced the expected
output, including the fallback to a healthy cell once `cell-2` was marked
unhealthy.
