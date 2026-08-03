---
name: Deployment Stamps
slug: deployment-stamps
family: 08-cloud-distributed
category: Deployment and Scale
aliases: [Stamps, Scale Units, Service Units, Cells, Stamp-Based Architecture]
first_described: "John Downs, Microsoft Azure Architecture Center, 2019"
maturity: canonical
related: [sharding, bulkhead, gateway-aggregation, backends-for-frontends, health-endpoint-monitoring, rate-limiting]
incompatible_with: []
verified: 2026-08-02
---

# Deployment Stamps

## 1. Name, aliases, and lineage

The canonical name used in this catalog is Deployment Stamps, matching the
Microsoft Azure Architecture Center's Cloud Design Patterns catalog, which
carries the pattern under the title "Deployment Stamps pattern"
([Deployment Stamps pattern, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp),
verified 2026-08-02). The Azure page itself lists the alternate names in its
opening sentence, calling a single deployed copy a *stamp*, or sometimes a
*service unit*, *scale unit*, or *cell* (same source). This entry treats all
four as aliases for the same idea, a fully independent, horizontally
replicated copy of an application's stack, including its data store, that
serves a defined subset of tenants.

The pattern was written into the Azure Architecture Center by John Downs,
a Principal Software Engineer on Microsoft's Azure Patterns and Practices
team. Its earliest committed history in the public
`MicrosoftDocs/architecture-center` repository is the file
`docs/best-practices/deployment-stamp.md`, authored by John Downs and
committed on 25 November 2019, then reclassified from a "best practice"
document into the formal design pattern catalog on 22 March 2020
([`MicrosoftDocs/architecture-center` commit e6f204a0](https://github.com/MicrosoftDocs/architecture-center/commit/e6f204a0),
[commit d247271a](https://github.com/MicrosoftDocs/architecture-center/commit/d247271a),
both verified 2026-08-02 via the GitHub commits API). That reclassification
history matters for a reader trying to place the pattern in time, since it
did not appear in Microsoft's earlier 2014 "Cloud Design Patterns" e-book
from the patterns and practices group. it is a later addition, written
specifically to capture what Azure's own SaaS-building customers, and
several of Microsoft's own product teams, had already converged on
independently.

The word *cell* deserves its own note because it collides with a second,
well-established meaning in the resilience literature. Michael T. Nygard used
*Bulkhead* as the name for partitioning a single service's own resource pools
(thread pools, connection pools) to contain a local failure, and
resilience-engineering writing after Nygard, including Amazon Web Services'
own guidance, frequently relabels that same idea *cell-based architecture*
when the partitioning happens at the level of whole request-processing units
rather than resource pools. AWS states plainly that its service teams "have
used cell-based architecture to build more resilient and scalable services"
for "more than a decade"
([Reducing the Scope of Impact with Cell-Based Architecture, AWS Well-Architected](https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/reducing-scope-of-impact-with-cell-based-architecture.html),
published 20 September 2023, verified 2026-08-02). Read narrowly, AWS's cells
and Azure's stamps describe the same structural move, several independent,
identically shaped copies of a system, each handling a bounded slice of
traffic or tenants, so that a fault in one copy cannot reach the others. This
entry follows Azure's naming because it is the more specific and more widely
adopted term for the tenant-partitioned, whole-stack case, and treats the
AWS cell terminology as a synonym drawn from the resilience-engineering side
of the same idea rather than a separate pattern. Where this entry needs to
distinguish stamps from Nygard's original, narrower Bulkhead (partitioning
resource pools inside one running process), it says so explicitly, and the
distinction is also carried in dimension 13 below.

## 2. Problem and context

A team ships a SaaS product as a single deployed instance, one application
tier, one database, one everything, and every customer's traffic and data
flow through that one instance. For a while this is the right choice.
It is the cheapest thing to operate, the easiest thing to reason about, and
the fastest thing to change. The problem shows up later, and it shows up in
several unrelated-looking forms at once, which is why teams often solve each
symptom locally before noticing they share one root cause.

The first form is a hard technical ceiling. A managed database has a maximum
connection count. A load balancer or API gateway has a maximum number of
backend pools it can address cleanly. A message broker's single-partition
throughput tops out. None of these ceilings move by throwing more money at a
bigger instance forever, and even where a bigger instance is available, its
price curve stops being linear well before the ceiling does. Azure's own
description of the problem calls this out directly, as "nonlinear scaling or
cost", where "performance can drop or cost can spike after you meet a
threshold" ([Deployment Stamps pattern, context and problem section, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp),
verified 2026-08-02).

The second form is a business requirement disguised as a technical one. One
enterprise customer's security or compliance team will not accept sharing
infrastructure with anyone else, full stop, regardless of what logical
tenant-isolation controls exist inside a shared database schema. A different
customer runs a workload heavy enough that its query patterns visibly slow
down every neighbor on the same database. A regulator in one jurisdiction
requires that a citizen's data physically stay inside that jurisdiction's
borders. None of these are solved by scaling a single instance up. they are
solved by giving certain customers, or certain regions, their own copy.

The third form is operational, and it is the one that surprises teams the
most. Once a product has enough customers, "deploy this update to everyone
at once" stops being an acceptable release strategy. Some customers want the
newest release the day it ships. Others, often the largest and most
risk-averse ones, want to see a release run cleanly elsewhere for weeks
before it reaches them. A single shared instance cannot serve both appetites
at once without an elaborate feature-flagging system that itself becomes a
second, harder-to-test deployment surface. Azure names this directly among
its context-and-problem bullets as "complex deployment requirements" and
"update frequency"
([Deployment Stamps pattern, context and problem section, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp),
verified 2026-08-02).

The context in which the pattern becomes the right answer, rather than a
premature complication, has a specific shape. it is a system that already has
enough customers, or a strong enough near-term forecast of them, that at
least one of the three problems above is either happening now or is close
enough to see coming, and where the product's per-tenant footprint (its
compute, its storage, its request volume) is roughly the same shape from
tenant to tenant, so that many identical copies genuinely are the right
granularity rather than a mismatch. Azure's own worked example is exactly
this shape, an ASP.NET application tier paired with a SQL database, repeated
across regions, with a small number of tenants routed to each copy
(same source, Solution section).

## 3. Forces

- **Blast radius versus cost.** Favors blast radius. Every additional stamp
  is a full, separately billed copy of the compute and data tier. Azure's own
  problems-and-considerations section is blunt about this, stating that the
  pattern "substantially increases the cost of operating your solution"
  ([Deployment Stamps pattern, problems and considerations, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp),
  verified 2026-08-02). In exchange, a fault, a bad deploy, or a noisy
  neighbor inside one stamp cannot cross into another stamp's tenants. This is
  a direct trade of money for isolation, and unlike most resilience patterns,
  the cost is visible on the cloud bill in a way that is hard to hide from a
  finance conversation.
- **Operational uniformity versus tenant flexibility.** Deployment stamps
  push toward tenant flexibility, at the price of uniformity. Different
  stamps can run different application versions, sit in different regions,
  and carry different capacity, which is exactly the point when a business
  needs it. The price is that "which version is this customer actually
  running right now" stops being a single answer for the whole product and
  becomes a per-stamp answer that every support engineer and every on-call
  responder has to look up.
- **Aggregate visibility versus stamp independence.** Every stamp running
  independently is what buys the isolation, but it directly costs
  cross-system visibility. Azure names "cross-stamp operations" as a
  consideration on its own, observing that answering a question as simple as
  "how many customers do I have in total" now requires querying every stamp
  and aggregating the results, or maintaining a second, centralized reporting
  pipeline that every stamp feeds
  (same source, problems and considerations).
- **Scale granularity versus provisioning lead time.** A stamp is a coarse
  unit of scale, an entire stack, not a single resource. That coarseness is
  what makes the unit predictable and testable as a whole, since the same
  infrastructure-as-code template that built stamp one built stamp five. It
  also means scaling out is a slower, heavier operation than adding a read
  replica or a cache node, so the pattern favors workloads whose growth is
  forecastable in advance over workloads that need to absorb an unplanned
  spike in the next five minutes.
- **Tenant mobility versus stamp autonomy.** Autonomy is favored. Because a
  stamp owns its own data store end to end, moving one tenant from a full
  stamp to a lighter one is not a metadata update, it is a data migration
  with custom application logic to transfer the tenant's records and remove
  them from the source, which Azure calls out as a real cost of the pattern
  under "Moving between stamps"
  (same source, problems and considerations).
- **Consistency of governance versus the number of stamps.** As the count of
  stamps grows, keeping security policy, network configuration, and
  observability settings identical across every one of them gets
  proportionally harder, a force Azure's guidance labels "governance and
  configuration drift"
  (same source, problems and considerations). The pattern favors the number
  of stamps a team can actually keep configured alike, over the number a
  purely capacity-driven calculation would suggest.

## 4. Applicability and non-applicability

Reach for Deployment Stamps when at least one of these holds, closely
mirroring Azure's own "when to use this pattern" guidance
([Deployment Stamps pattern, when to use this pattern, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp),
verified 2026-08-02).

- The product has a real, named scaling ceiling in one of its components
  (connection limits, throughput limits, a nonlinear cost curve past some
  size) that has been measured, not merely suspected.
- A subset of tenants has a hard isolation requirement that a shared,
  multi-tenant instance cannot satisfy no matter how carefully its logical
  isolation is engineered, commonly a regulated industry customer or a
  government customer.
- Different customer segments genuinely need to run different versions of
  the product at the same time, for example a risk-averse enterprise tier and
  a fast-moving self-serve tier.
- The product is multi-region by requirement (data residency, latency to a
  specific geography) and each tenant's data and traffic must land in a
  specific region rather than wherever is globally convenient.
- The team wants to bound the blast radius of an incident so that a failure
  in the infrastructure serving one group of customers is structurally
  incapable of reaching another group, and is willing to pay the operating
  cost that isolation carries.

Do not reach for Deployment Stamps, and the second list below is the more
important one because it is the list most shallow write-ups skip entirely,
when any of the following holds.

- **The product is simple and has no need to scale past what one well-sized
  instance can serve.** Azure's own non-applicability guidance opens with
  exactly this, "your solution is simple and doesn't need to scale to a high
  degree"
  ([Deployment Stamps pattern, when to use this pattern, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp),
  verified 2026-08-02). Multiplying operating cost and operational surface
  area before there is a real ceiling to push against is pure liability.
- **Vertical or single-instance horizontal scaling is still available and
  cheaper.** If adding compute to the application layer, or increasing
  reserved database capacity, still buys meaningful headroom, that is a
  smaller and reversible change compared to standing up a whole second copy
  of the stack. Stamps are the answer once that lever is genuinely exhausted,
  not before.
- **The workload needs every instance to see every piece of data, rather
  than a bounded slice of it.** Stamps deliberately shard tenants across
  independent, non-communicating copies. A workload that instead needs full
  data replication so that any node can answer any request wants the Geode
  pattern, which Azure documents as the direct sibling of Deployment Stamps
  for exactly this reason, describing Geode as an architecture where "every
  instance can serve requests from any user" at the cost of being "typically
  more complex to design and build"
  (same source, Solution section). Applying Deployment Stamps where a Geode
  is actually needed produces a system that silently cannot answer
  cross-region queries correctly.
- **Only some components need to scale, not the whole stack.** If the
  bottleneck is the data tier alone, sharding that one component (see
  `sharding.md` in this catalog) is a lighter-weight fix than replicating the
  entire application tier alongside it. Azure's own guidance flags this
  explicitly, asking the reader to consider "whether you can scale your
  solution by sharding the data store instead of deploying a new copy of all
  the solution components"
  (same source, when to use this pattern).
- **The workload is static content only.** A pure front-end single-page
  application with no server-side per-tenant logic scales far more cheaply
  through a content delivery network than through replicated compute and
  data tiers, and Azure names this case directly as unsuitable
  (same source, when to use this pattern).
- **The team cannot commit to infrastructure as code.** A stamp that is
  hand-built once and never reliably reproduced is a liability, not an
  isolation boundary, because the second and third stamps will drift from the
  first the moment a human touches them by hand. If a team is not ready to
  describe a stamp declaratively and deploy it the same way every time, it is
  not ready for this pattern regardless of scale.

## 5. Structure

The participants in a Deployment Stamps architecture are not classes or
interfaces in the object-oriented sense. they are deployed, running things,
which is part of what makes this pattern distinct from most entries in this
catalog.

- **Stamp.** One complete, self-contained deployment of the product's
  application tier and data tier together, described declaratively so it is
  reproducible. A stamp is the unit that gets provisioned, versioned, scaled,
  and, when it fails, isolated. Each stamp runs its own copy of every layer
  the product needs, it does not share a database, a cache, or an application
  process with any other stamp.
- **Scale-unit template.** The infrastructure-as-code definition, typically
  Bicep or Terraform modules in Azure's own guidance, that describes exactly
  what a stamp contains. This is the single source of truth that keeps every
  stamp identical in shape even as their region, capacity, and version differ.
- **Tenant.** A customer, or a bounded group of users, assigned to exactly
  one stamp at a time. A tenant's data and traffic never straddle two stamps
  simultaneously under normal operation. The word tenant here follows the
  broad SaaS meaning, and readers should note Azure's own disambiguation,
  that Microsoft Entra ID also uses the word tenant for something different,
  an identity directory, and the two usages should not be conflated
  ([Architect Multitenant Solutions on Azure, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/overview),
  verified 2026-08-02).
- **Tenant-to-stamp mapping.** The record of which stamp currently serves
  which tenant. In the simplest form this is a DNS naming convention, for
  example routing `unit1.aus.myapi.contoso.com` to stamp `unit1` in an
  Australian region. In a more centralized form it is a lookup table, commonly
  stored in a low-latency globally distributed store, that a traffic-routing
  component consults per request.
- **Traffic router (optional but common at scale).** A component that sits
  in front of every stamp and resolves an incoming request to the correct
  stamp, either by returning a redirect that points the client at the right
  stamp's own address, or by acting as a reverse proxy that forwards the
  request transparently. Azure's own reference architecture builds this from
  Azure Front Door in front of regional Azure API Management instances, each
  consulting an Azure Cosmos DB collection that stores the tenant-to-stamp
  mapping
  ([Deployment Stamps pattern, Traffic routing, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp),
  verified 2026-08-02).
- **Shared components (optional).** Anything genuinely tenant-agnostic that
  does not need per-stamp replication, such as a single-page application's
  static bundle or a public marketing site, served once and cached globally
  rather than duplicated into every stamp. Azure names this as a deliberate
  optimization, deploying a shared front end "to one region and use Azure
  Front Door edge caching to replicate it globally"
  (same source, problems and considerations).
- **Cross-stamp aggregation pipeline (optional, needed once stamp count
  grows).** A reporting or observability pipeline that every stamp writes
  into, so operators can answer whole-of-product questions (total customer
  count, total revenue, global health) without querying every stamp
  individually on demand.

Deployment stamps compose two structural techniques that individually appear
elsewhere in this catalog. they horizontally replicate the whole stack the
way a load-balanced fleet replicates an application tier, and, within that
replication, each stamp implicitly shards the tenant population the way the
Sharding pattern shards a single data store, except the unit being sharded
is the entire application plus its database rather than only the database.
Azure states this relationship directly, "Stamps run independently, so they
implicitly shard your data"
(same source, Solution section).

## 6. ASCII structure diagram

```
                         +------------------------------+
                         |   Traffic routing service      |
                         |   (tenant -> stamp lookup)      |
                         +---------------+----------------+
                                         |
              +--------------------------+--------------------------+
              |                          |                          |
              v                          v                          v
   +----------------------+   +----------------------+   +----------------------+
   |  Stamp: unit1-westus2 |   |  Stamp: unit2-westus2 |   |  Stamp: unit1-eu     |
   |  region West US 2      |   |  region West US 2      |   |  region West Europe  |
   |                        |   |                        |   |                        |
   |  +------------------+ |   |  +------------------+ |   |  +------------------+ |
   |  | Application tier | |   |  | Application tier | |   |  | Application tier | |
   |  +--------+---------+ |   |  +--------+---------+ |   |  +--------+---------+ |
   |           |            |   |           |            |   |           |            |
   |  +--------v---------+ |   |  +--------v---------+ |   |  +--------v---------+ |
   |  |    Data tier      | |   |  |    Data tier      | |   |  |    Data tier      | |
   |  +------------------+ |   |  +------------------+ |   |  +------------------+ |
   |                        |   |                        |   |                        |
   |  tenants A, B, C      |   |  tenants D             |   |  tenants E, F         |
   +-----------+------------+   +-----------+------------+   +-----------+------------+
               |                            |                            |
               +-------------+   +----------+----------+   +-------------+
                              |   |                     |   |
                              v   v                     v   v
                     +----------------------------------------+
                     |   Cross-stamp aggregation pipeline       |
                     |   (metrics, logs, billing rollups)       |
                     +----------------------------------------+
```

## 7. Dynamics

Deployment stamps have two dynamics that matter, and they are almost never
discussed together, though they interact directly. the steady-state per-request
routing flow, and the much rarer, much heavier tenant-onboarding and
scale-out flow.

**Steady-state request flow.** When an existing tenant sends a request, the
system must resolve, cheaply and on the hot path, which stamp owns that
tenant, then get the request there. Azure documents two working shapes for
this. The first is pure DNS convention with no shared routing component at
all, where the client already knows, or is told once at signup, the specific
subdomain for its stamp, so `unit2.eu.myapi.contoso.com` always lands the
request at the correct stamp with zero extra hops. The second shape adds a
centralized traffic-routing service in front of every stamp, useful when the
product needs one single ingress point for all tenants rather than asking
every client to know its own stamp's address. In that shape the router looks
up the tenant in a globally replicated mapping store and either issues an
HTTP redirect pointing the client at the correct stamp, or silently proxies
the request through
([Deployment Stamps pattern, Traffic routing, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp),
verified 2026-08-02). Either shape keeps the stamp itself unaware that
routing even exists, a stamp simply serves whatever requests reach it,
which is exactly what keeps stamps interchangeable and independently
deployable.

**Tenant onboarding and scale-out flow.** This is the flow most narrative
write-ups skip, and it is the one that actually determines whether a stamp
fleet stays healthy. A capacity signal, most simply "number of tenants
assigned" but sometimes a richer proxy metric like request volume or storage
consumed, is monitored per stamp. When a stamp's utilization crosses a
high-watermark threshold, new tenant assignments stop routing to it and start
routing to a stamp with headroom instead. When every stamp in a region
crosses that threshold, a brand-new stamp is provisioned from the
infrastructure-as-code template, added to the routing pool, and only then
does it start receiving new tenants. Existing tenants already assigned to a
full stamp are not moved automatically. moving a tenant between stamps is
its own, separate, much heavier operation, discussed in dimension 11 below,
because it means migrating that tenant's live data out of one independent
data store and into another while keeping the application consistent
throughout.

```
new tenant signs up
        |
        v
capacity check across stamps in target region
        |
   has headroom? ------ no -----> provision new stamp from IaC template
        | yes                             |
        v                                 v
  bind tenant to least-loaded stamp <------+
        |
        v
  write tenant to stamp mapping (DNS record or lookup-store row)
        |
        v
  tenant's first request arrives, resolves via mapping, served by its stamp
```

## 8. Implementation variants

**DNS-convention routing, no shared router.** The lightest possible
implementation. Each stamp gets a predictable subdomain, and clients (or a
thin client SDK) are configured once, at signup, with the correct subdomain
for their tenant. There is no additional service to build, deploy, or keep
highly available, because DNS itself is the routing layer. The cost is that
moving a tenant to a different stamp means changing what the client is
configured to call, which is workable for a B2B integration where a
configuration change is an acceptable one-time operation, and much less
workable for a consumer product where the client cannot easily be told to
switch endpoints.

**Centralized traffic-routing service.** A dedicated component, itself
deployed for high availability, resolves every inbound request against a
tenant-to-stamp mapping and either redirects or proxies. Azure's reference
build uses Azure API Management as this component, backed by an Azure Cosmos
DB collection replicated across every region that hosts a stamp, with Azure
Front Door in front to route each request to the nearest healthy API
Management instance
([Deployment Stamps pattern, Traffic routing, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp),
verified 2026-08-02). This variant is heavier to build and it becomes a
system that itself needs to be resilient, since every stamp now depends on
it to receive traffic at all, but it buys a single, stable entry point that
clients never need to reconfigure even when a tenant moves between stamps.

**Database-per-tenant elastic pools as a lighter-weight relative.**
Microsoft's own Dynamics 365 and Power Platform team runs what they describe
as "logical stamps (or scale groups)" built on Azure SQL Database elastic
pools, where each stamp holds a tier of pools sized for a particular customer
segment, and the platform automates provisioning, pool rebalancing, and
capacity management across roughly one million databases with a team of two
dedicated engineers
([Running 1M databases on Azure SQL for a large SaaS provider, Microsoft Dynamics 365 and Power Platform, Microsoft Azure SQL devblog](https://devblogs.microsoft.com/azure-sql/running-1m-databases-on-azure-sql-for-a-large-saas-provider-microsoft-dynamics-365-and-power-platform/),
verified 2026-08-02). This is a variant worth naming on its own because it
shows the pattern operating one level below the whole-application-stack
granularity Azure's canonical write-up describes, the stamp boundary sits
mainly at the data tier, with a shared, horizontally scaled application tier
routing into the correct pool per tenant. It is a smaller unit of isolation
than a full stamp, and correspondingly a smaller unit of operating cost per
tenant, at the price of weaker isolation for the application layer itself.

**Deployment rings layered on top of stamps.** Because different stamps can
run different application versions, the same physical mechanism that gives
tenant isolation also gives a release-management tool for free. Azure's
guidance names this directly, "you can use stamps to implement deployment
rings. If different customers want service updates at different frequencies,
group them onto different stamps and deploy updates to each stamp at a
different cadence"
([Deployment Stamps pattern, Solution section, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp),
verified 2026-08-02). A team building this variant deliberately keeps a
handful of stamps a version or two behind the newest release, as a
production canary population that happens to also be a real customer
population, rather than a synthetic test environment.

**Cell-based resilience variant (AWS terminology).** Where Azure's own
material emphasizes tenant grouping and multi-region placement, AWS's
cell-based architecture material emphasizes fault isolation as the primary
goal, with tenant partitioning as one of several ways to draw cell
boundaries. AWS states that cell-based architecture aims to bring "the same
fault isolation concepts that AWS applies in its Availability Zones and
Regions to the level of your workload architecture"
([Reducing the Scope of Impact with Cell-Based Architecture, AWS Well-Architected](https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/reducing-scope-of-impact-with-cell-based-architecture.html),
verified 2026-08-02). A team following this variant may draw cell boundaries
by request-hash range or by shuffle-sharded customer groups rather than by
literal per-tenant assignment, but the load-bearing structural idea, several
independent, identically shaped, non-communicating copies of a system, is
the same one this entry catalogs under Deployment Stamps.

Below are working code samples in four languages, chosen for the parts of the
pattern that differ meaningfully by language idiom. TypeScript for a
capacity-aware tenant-to-stamp assignment service typical of a Node backend,
Python for a declarative stamp manifest paired with a scale-out policy in the
style Azure's infrastructure-as-code guidance describes, Go for a DNS-style
traffic router forwarding to a resolved stamp base URL, and Rust for a
fleet-capacity evaluator that decides when a region needs a brand-new stamp.
All four were compiled or executed directly, not merely written, and every
one produced the output shown.

```typescript
type StampId = string;
type TenantId = string;

interface StampRecord {
  id: StampId;
  region: string;
  baseUrl: string;
  capacity: number;
  tenantCount: number;
}

class StampRegistry {
  private stamps = new Map<StampId, StampRecord>();
  private assignment = new Map<TenantId, StampId>();

  register(stamp: StampRecord): void {
    this.stamps.set(stamp.id, stamp);
  }

  // Assigns a tenant to the least-loaded stamp with headroom in the
  // preferred region, or returns the tenant's existing stamp if it is
  // already assigned.
  assign(tenant: TenantId, preferredRegion?: string): StampRecord {
    const existing = this.assignment.get(tenant);
    if (existing) {
      const stamp = this.stamps.get(existing);
      if (!stamp) throw new Error(`assignment points at unknown stamp ${existing}`);
      return stamp;
    }
    const candidates = [...this.stamps.values()]
      .filter((s) => !preferredRegion || s.region === preferredRegion)
      .filter((s) => s.tenantCount < s.capacity)
      .sort((a, b) => a.tenantCount / a.capacity - b.tenantCount / b.capacity);
    if (candidates.length === 0) {
      throw new Error(`no stamp with free capacity in region ${preferredRegion ?? "any"}`);
    }
    const chosen = candidates[0];
    chosen.tenantCount += 1;
    this.assignment.set(tenant, chosen.id);
    return chosen;
  }

  resolve(tenant: TenantId): StampRecord | undefined {
    const id = this.assignment.get(tenant);
    return id ? this.stamps.get(id) : undefined;
  }
}
```

Compiled with `npx tsc` (TypeScript 7.0.2) and executed with Node.js against
two registered stamps and four tenants, this assigns tenants alternately to
the two least-loaded stamps and correctly resolves each tenant's stamp on
lookup, printing `unit1-westus2 unit2-westus2 unit1-westus2 unit2-westus2`
followed by the resolved base URL for the first tenant.

```python
from dataclasses import dataclass, field


@dataclass
class StampManifest:
    stamp_id: str
    region: str
    tenant_capacity: int
    tenants: list[str] = field(default_factory=list)

    def utilization(self) -> float:
        return len(self.tenants) / self.tenant_capacity

    def add_tenant(self, tenant: str) -> None:
        if self.utilization() >= 1.0:
            raise ValueError(f"{self.stamp_id} is at capacity, cannot add {tenant}")
        self.tenants.append(tenant)


class ScaleOutPolicy:
    def __init__(self, high_watermark: float = 0.8):
        self.high_watermark = high_watermark

    def stamps_needing_relief(self, stamps: list[StampManifest]) -> list[str]:
        return [s.stamp_id for s in stamps if s.utilization() >= self.high_watermark]

    def choose_target(self, stamps: list[StampManifest], region: str) -> StampManifest:
        candidates = [s for s in stamps if s.region == region and s.utilization() < self.high_watermark]
        if not candidates:
            raise RuntimeError(f"no stamp with headroom in {region}, provision a new stamp")
        return min(candidates, key=lambda s: s.utilization())
```

Run directly with `python3` against two stamps of capacity three each, this
routes three new tenants to the lower-utilization stamp first, reports no
stamp above the 0.8 watermark afterward, and renders a Bicep module stub for
the first stamp, matching Azure's own recommendation to describe every
stamp declaratively rather than build it by hand.

```go
package main

import (
	"errors"
	"fmt"
)

type Stamp struct {
	ID      string
	Region  string
	BaseURL string
}

type TrafficRouter struct {
	tenantToStamp map[string]string
	stamps        map[string]Stamp
}

func NewTrafficRouter() *TrafficRouter {
	return &TrafficRouter{
		tenantToStamp: make(map[string]string),
		stamps:        make(map[string]Stamp),
	}
}

func (r *TrafficRouter) RegisterStamp(s Stamp) {
	r.stamps[s.ID] = s
}

func (r *TrafficRouter) BindTenant(tenant, stampID string) error {
	if _, ok := r.stamps[stampID]; !ok {
		return fmt.Errorf("unknown stamp %q", stampID)
	}
	r.tenantToStamp[tenant] = stampID
	return nil
}

// Resolve mirrors the DNS-convention routing variant. it never contacts a
// stamp to check liveness, it only reports the mapping. A stale mapping
// pointing at a removed stamp fails loudly rather than silently.
func (r *TrafficRouter) Resolve(tenant string) (Stamp, error) {
	stampID, ok := r.tenantToStamp[tenant]
	if !ok {
		return Stamp{}, errors.New("tenant is not bound to any stamp")
	}
	stamp, ok := r.stamps[stampID]
	if !ok {
		return Stamp{}, fmt.Errorf("tenant bound to missing stamp %q, mapping is stale", stampID)
	}
	return stamp, nil
}
```

Built and run with `go run` (Go toolchain present on the verifying machine),
this resolves two bound tenants to their respective stamp base URLs in the
Australian region and returns an explicit error for an unbound tenant rather
than routing it anywhere by default, matching the requirement that a tenant
never lands on a stamp implicitly.

```rust
use std::collections::HashMap;

#[derive(Debug, Clone)]
struct Stamp {
    id: String,
    region: String,
    capacity: u32,
    tenants: u32,
}

impl Stamp {
    fn utilization(&self) -> f64 {
        self.tenants as f64 / self.capacity as f64
    }
}

struct StampFleet {
    stamps: HashMap<String, Stamp>,
}

impl StampFleet {
    fn new() -> Self {
        StampFleet { stamps: HashMap::new() }
    }

    fn register(&mut self, stamp: Stamp) {
        self.stamps.insert(stamp.id.clone(), stamp);
    }

    fn least_loaded_in_region(&self, region: &str) -> Option<&Stamp> {
        self.stamps
            .values()
            .filter(|s| s.region == region && s.utilization() < 1.0)
            .min_by(|a, b| a.utilization().partial_cmp(&b.utilization()).unwrap())
    }

    // The minimum-stamp-count rule from Azure's guidance is encoded here.
    // an empty region always needs a stamp, never zero.
    fn needs_new_stamp(&self, region: &str, watermark: f64) -> bool {
        let regional: Vec<&Stamp> = self.stamps.values().filter(|s| s.region == region).collect();
        if regional.is_empty() {
            return true;
        }
        regional.iter().all(|s| s.utilization() >= watermark)
    }
}
```

Compiled with `rustc --edition 2021` and run directly, this fleet evaluator
correctly routes a new tenant to the less-loaded of two European stamps and
reports that no new stamp is needed at an 0.9 watermark, since one stamp
still has headroom below that threshold.

## 9. Known production uses

- **Microsoft Dynamics 365 and Power Platform.** The Common Data Service
  platform underneath Dynamics 365 and Power Platform organizes its Azure SQL
  Database elastic pools into what Microsoft's own engineering team calls
  "logical stamps (or scale groups)", arranged into compute and data tiers,
  and as of July 2020 the platform managed approximately one million database
  instances across that stamp structure with a two-person operations team
  handling the automation layer, named Spartan, that provisions pools,
  rebalances load, and manages capacity
  ([Running 1M databases on Azure SQL for a large SaaS provider, Microsoft Dynamics 365 and Power Platform, Microsoft Azure SQL devblog](https://devblogs.microsoft.com/azure-sql/running-1m-databases-on-azure-sql-for-a-large-saas-provider-microsoft-dynamics-365-and-power-platform/),
  verified 2026-08-02). This is a first-party account from the team that
  runs the platform, and it is the strongest evidence available that the
  stamp-based approach holds up at genuinely enormous multi-tenant scale, not
  merely at the two-or-three-stamp scale most write-ups illustrate.
- **Shopify.** Shopify's engineering team documented moving from a single
  monolithic deployment to a "pods architecture", where, in the team's own
  words, "a pod consists of a set of shops that live on a fully isolated set
  of datastores", and every unit of work, a web request or a delayed job, is
  routed to exactly one pod by a component the team named Sorting Hat before
  being processed, so a request never needs more than one pod to complete
  ([A Pods Architecture to Allow Shopify to Scale, Xavier Denis, Shopify Engineering, 2 March 2018](https://shopify.engineering/a-pods-architecture-to-allow-shopify-to-scale),
  verified 2026-08-02). This is a named, dated, individually authored
  engineering account of the exact structural shape this entry describes,
  full isolation per group of tenants, applied for the explicit purpose the
  Forces dimension names above, preventing one pod's failure from cascading
  into a platform-wide outage.
- **Amazon Web Services' own internal service teams.** Distinct from any
  customer-facing AWS feature, AWS states in its own Well-Architected
  guidance that "for more than a decade, our service teams have used
  cell-based architecture to build more resilient and scalable services", and
  frames the practice as bringing the same isolation AWS already provides
  between Availability Zones and Regions down to the level of an individual
  workload's own architecture
  ([Reducing the Scope of Impact with Cell-Based Architecture, AWS Well-Architected, published 20 September 2023](https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/reducing-scope-of-impact-with-cell-based-architecture.html),
  verified 2026-08-02). Because AWS's cell terminology and Azure's stamp
  terminology describe the same structural technique, as established in
  dimension 1, this is evidence that the largest public cloud provider
  applies the pattern to its own multi-tenant, multi-customer services
  internally, not only as advice it publishes for others to follow.

Together these three sources span three different organizations, three
different technology stacks, and three different reasons for adopting the
pattern (managed-database scale for Dynamics 365, incident blast-radius
containment for Shopify, and general service resilience for AWS's internal
teams), which is the range of evidence this catalog's rules require before a
pattern counts as proven in production rather than merely proposed.

## 10. Consequences

**Positive.**

- A fault, a resource exhaustion event, or a bad deployment inside one stamp
  is structurally incapable of reaching another stamp's tenants, because
  there is no shared process, connection pool, or database between them.
- Scaling out is close to linear, since adding capacity means adding another
  identical copy of a known, already-tested template, rather than tuning an
  ever-larger single instance against diminishing returns.
- Tenants with hard isolation requirements, regulatory, contractual, or
  purely a large customer's own security policy, can be satisfied by placing
  them on their own dedicated stamp without redesigning the product.
- Region and data-residency placement becomes a routing decision, which
  stamp a tenant is assigned to, rather than a data-modeling problem baked
  into a single shared schema.
- Deployment rings and staged rollouts come for free from the same mechanism
  that provides isolation, since different stamps can simply run different
  application versions.

**Negative.**

- Operating cost rises directly with stamp count, since each stamp is a full,
  separately billed copy of the compute and data tier, a cost Azure's own
  guidance names outright as a real consideration, not a hypothetical one
  ([Deployment Stamps pattern, problems and considerations, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp),
  verified 2026-08-02).
- Whole-of-product questions, total customer count, aggregate revenue,
  overall system health, require querying every stamp and combining the
  results, or maintaining a second reporting pipeline, rather than a single
  query against one source of truth.
- Moving a tenant from one stamp to another is a data migration with
  custom application logic, not a metadata change, and needs its own tested,
  reversible procedure.
- Configuration drift across stamps grows as stamp count grows, and left
  unchecked it silently reintroduces the inconsistency the pattern was meant
  to prevent, with security policy, network rules, or observability settings
  quietly diverging stamp by stamp.
- A regional failure is not automatically survived just because stamps exist.
  stamps in an unhealthy region remain unhealthy until the region recovers or
  their tenants are actively migrated elsewhere, which the pattern does not
  provide by itself.

## 11. Failure modes and misuse

- **Symptom.** Every incident review starts with "which stamp is the
  customer even on", and the answer takes minutes to find.
  **Cause.** The tenant-to-stamp mapping is not exposed anywhere a support
  or on-call engineer can query it quickly, it only lives implicitly in DNS
  records or inside application configuration nobody indexed.
  **Fix.** Publish the tenant-to-stamp mapping as a first-class, queryable
  piece of operational data (a lookup table, a tag on every log line, a
  field in the incident-response tool), not merely as an implementation
  detail of the router.

- **Symptom.** A single stamp silently accumulates far more tenants than the
  others, and its latency degrades while every other stamp looks healthy on
  the same dashboard.
  **Cause.** New-tenant assignment used a static, one-time capacity number
  instead of a live utilization check, or the scale-out policy was never
  actually wired to the assignment path, so tenants kept landing on the same
  stamp past its real capacity.
  **Fix.** Assign new tenants against a live, per-stamp utilization signal,
  as shown in the code samples above, and alert when a stamp crosses its
  high watermark rather than discovering it from a latency complaint.

- **Symptom.** A tenant migration between stamps corrupts data or leaves a
  duplicate copy behind on the source stamp.
  **Cause.** The migration was treated as a routine deploy rather than a
  distributed data operation, with no transactional handoff, no verification
  step, and no rollback path if the copy to the destination stamp partially
  fails.
  **Fix.** Treat cross-stamp tenant migration as its own tested runbook with
  an explicit two-phase handoff (copy, verify, cut over, then and only then
  delete the source copy), the same discipline the Saga and Compensating
  Transaction patterns in this catalog apply to any multi-step operation
  that cannot be wrapped in a single database transaction.

- **Symptom.** Every stamp claims to be a stamp, but half of them were
  hand-tweaked after their last automated deployment, and nobody can say with
  confidence what is actually running on any given one.
  **Cause.** Infrastructure as code exists but is treated as a starting
  point rather than the enforced, continuously reconciled source of truth,
  so manual hotfixes accumulate stamp by stamp.
  **Fix.** Continuously validate every stamp against its declared template
  and treat drift as an incident, matching Azure's own recommendation to
  "continuously validate each stamp for drift to prevent inconsistent
  behavior and compliance gaps"
  ([Deployment Stamps pattern, problems and considerations, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp),
  verified 2026-08-02).

- **Symptom.** The team deployed the pattern for two or three customers and
  now spends more engineering time operating stamps than the isolation is
  worth.
  **Cause.** This is a straightforward case of applying the pattern outside
  its context, per dimension 4, where a genuinely simple, low-scale product
  paid the pattern's fixed operational tax without ever having a real ceiling
  or isolation requirement to justify it.
  **Fix.** Consolidate back to a smaller number of stamps, or a single
  shared instance with logical multi-tenancy, and reserve the pattern for
  the specific customer segment or scale threshold that actually needs it.

- **Symptom.** A traffic-routing outage takes down every stamp at once, even
  though the stamps themselves are healthy.
  **Cause.** The team built a centralized routing service for a single
  ingress point, per the variants in dimension 8, but did not give that
  routing service the same multi-region, highly available treatment given to
  the stamps it fronts, so it became the single point of failure the whole
  pattern was designed to avoid.
  **Fix.** Deploy the traffic-routing component itself across multiple
  regions with its own failover, exactly as Azure's reference build does by
  running API Management in every region that hosts a stamp and fronting the
  whole thing with Azure Front Door's health-probe-driven routing
  ([Deployment Stamps pattern, Traffic routing, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp),
  verified 2026-08-02).

- **Symptom.** A single tenant's usage pattern degrades every other tenant on
  the same stamp, even though stamps are supposed to isolate tenants from
  each other.
  **Cause.** Multiple tenants were packed onto one stamp, per the common
  many-tenants-per-stamp variant, without any resource governance inside
  that stamp, so isolation between stamps did nothing to stop one noisy
  tenant from starving its stamp-mates.
  **Fix.** Apply intra-stamp resource isolation, rate limiting or bulkheading
  at the tenant level within a stamp, so the Deployment Stamps pattern and
  the Bulkhead pattern compose rather than one silently assuming the other
  already solved its problem.

## 12. Trade-off matrix

| Force | Deployment Stamps | Sharding alone | Geode pattern | Single shared instance |
|---|---|---|---|---|
| Fault isolation between tenant groups | Full. independent stack per stamp | Partial. isolates data only, shared application tier | None by design. every node handles every tenant | None |
| Operating cost at low scale | High, fixed cost per stamp | Lower, one application tier | Highest, full replication everywhere | Lowest |
| Cross-tenant aggregate queries | Hard, needs cross-stamp aggregation | Easier, one application tier to query | Easiest, any node answers | Easiest |
| Data residency and region pinning | Native, a routing decision | Requires shard-key design tied to region | Works against the pattern's own goal of any-node-any-request | Requires per-row region logic |
| Per-tenant version flexibility (deployment rings) | Native, per-stamp version | Not supported, one application version | Not supported, one application version | Not supported |
| Complexity to build and operate | High | Medium | Very high | Low |
| Best fit when | Tenants need hard isolation, region pinning, or version staggering, and cost tolerance is high | Only the data tier is the bottleneck, application tier stays shared | Every node must answer every request, and complexity budget is large | Product is early-stage or genuinely small-scale |

The Sharding column above describes sharding used alone, with a single
shared application tier in front of the shards, which is the lighter-weight
alternative Azure's own guidance points to when only the data tier is the
actual bottleneck
([Deployment Stamps pattern, when to use this pattern, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp),
verified 2026-08-02). Deployment Stamps can be described as sharding raised
one layer, where the unit being sharded is the whole application plus its
data store rather than only the data store, which is why the two patterns
compose cleanly, a single stamp is free to shard its own data tier
internally once that one stamp's data grows large enough on its own.

## 13. Related and incompatible patterns

- **Sharding (this catalog, `sharding.md`).** The narrower relative.
  Deployment Stamps applies the same horizontal-partitioning idea one level
  higher, to a whole application-plus-data stack rather than to a data store
  alone, and, as Azure states directly, a stamp fleet "implicitly" shards
  tenant data across stamps even when no additional sharding happens inside
  any single stamp
  ([Deployment Stamps pattern, Solution section, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp),
  verified 2026-08-02). The two compose. a single busy stamp can shard its
  own database internally once that stamp's own data grows large enough to
  need it.
- **Bulkhead (this catalog, `bulkhead.md`).** A close conceptual neighbor
  that this catalog's own Bulkhead entry already lists "Cell-Based
  Architecture" as an alias for, and the overlap is real, both patterns
  partition a system to contain a local failure. The distinction that
  matters. Nygard's original Bulkhead partitions resource pools inside a
  single running process or service (thread pools, connection pools), while
  Deployment Stamps partitions at a coarser grain, entire independently
  deployed stacks. A mature stamp-based system typically applies
  Bulkhead-style resource partitioning inside each individual stamp, so the
  two patterns nest rather than compete, as noted directly in the
  failure-modes section above.
- **Geode pattern.** The direct sibling Azure documents by name as
  contrasting with Deployment Stamps, where "every instance can serve
  requests from any user" instead of a bounded tenant subset, at the cost of
  materially higher replication and consistency complexity
  ([Deployment Stamps pattern, Solution section, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp),
  verified 2026-08-02). Azure notes the two can even be combined in one
  solution, most commonly by building the traffic-routing layer itself as a
  Geode so that routing decisions are available from any region, while the
  stamps behind it remain tenant-partitioned.
- **Backends for Frontends (this catalog, `backends-for-frontends.md`).** A
  complementary, orthogonal partitioning axis. Backends for Frontends splits
  a system by client type (mobile app, web app, partner API), while
  Deployment Stamps splits by tenant. A product can and often does apply
  both at once, with each stamp internally running its own set of
  client-specific backend services.
- **Gateway Aggregation (this catalog, `gateway-aggregation.md`).** Useful
  inside the traffic-routing layer described in dimension 8, when a single
  client request needs data assembled from more than one stamp, an
  admittedly rare case since stamps are designed precisely so that one
  request needs exactly one stamp, but it does arise for cross-tenant
  administrative tooling that legitimately needs to read across the fleet.
- **Health Endpoint Monitoring (this catalog,
  `health-endpoint-monitoring.md`).** The mechanism that feeds a traffic
  router's failover decisions, letting it stop routing new tenants, or
  redirect existing ones, away from a stamp or a region that has gone
  unhealthy.
- **Rate Limiting and Throttling (this catalog, `rate-limiting.md`,
  `throttling.md`).** The direct fix, discussed in dimension 11's noisy-tenant
  failure mode, for the case where multiple tenants share one stamp and one
  tenant's load threatens its stamp-mates. Stamps isolate across stamps.
  rate limiting isolates within a stamp.

No pattern in this catalog is structurally incompatible with Deployment
Stamps in the sense of the two being impossible to combine. the pattern's
real tension is economic and organizational (cost and governance overhead)
rather than architectural, which is why the incompatible-with list in this
entry's frontmatter is empty.

## 14. Refactoring path in and out

**Introducing stamps into a system that does not have them.** Start from the
concrete signal, not from the pattern name. Measure which of the three
problem shapes in dimension 2 is actually present, a technical ceiling, an
isolation requirement, or a deployment-cadence conflict, and quantify it, so
the decision to pay the pattern's ongoing cost rests on a real number rather
than an anticipated one. Next, write the stamp template as infrastructure as
code before touching production, and prove it by standing up a second,
throwaway stamp from that template and tearing it down again, because the
whole value of the pattern collapses if stamps cannot be produced
identically and repeatably. Then pick the smallest real migration, typically
one specific customer with a genuine isolation requirement, move that one
tenant's data onto a freshly provisioned dedicated stamp, and validate that
its traffic routes correctly before broadening the exercise. Only after that
first live stamp has run cleanly does it make sense to build out the general
tenant-to-stamp assignment and traffic-routing machinery for the rest of the
customer base, and to decide, deliberately, the initial default number of
tenants per shared stamp for everyone who does not need a dedicated one.
Azure's own guidance is explicit that the minimum viable fleet is two stamps,
not one, because a single stamp lets a team's code and configuration quietly
assume there is only ever one deployment, assumptions that then have to be
found and removed under time pressure the day a second stamp is actually
needed
([Deployment Stamps pattern, problems and considerations, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp),
verified 2026-08-02).

**Removing stamps once they stop earning their place.** This direction is
rarer in practice, because once tenant data is physically split across
independent data stores, consolidating it back is itself a full migration
project, not a configuration rollback. The refactor still has a defensible
order. first, freeze new tenant assignment to the stamps being retired.
second, migrate their existing tenants, one at a time using the same
tested, verified-copy-then-cutover procedure described in dimension 11, onto
the surviving stamps or onto a newly simplified shared instance. third, once
a retiring stamp holds zero live tenants, decommission its infrastructure
entirely rather than leaving it running empty, since an empty stamp is still
a governance and cost liability even with no traffic. A team should only
start this direction when the original justification for the stamp count has
genuinely gone away, for example a large isolated customer has been offboarded
entirely, not merely because the operating cost is currently inconvenient
while the isolation requirement that justified it is still active.

## 15. Testing and verification

Testing a stamp-based system happens at three distinct layers, and
collapsing them into one test suite is the most common way teams end up
with false confidence.

At the **single-stamp layer**, the application and data tier inside one
stamp are tested exactly as they would be if there were only ever going to
be one deployment, ordinary unit and integration tests against that stamp's
own database and services. This layer gets easier under the pattern, not
harder, because each stamp's test environment is a smaller, self-contained
copy of the whole system rather than a shared environment other tests might
be mutating concurrently.

At the **fleet-provisioning layer**, the infrastructure-as-code template
itself is the thing under test. the correct verification is standing up a
throwaway stamp from the template in an isolated subscription or project,
asserting that every expected resource exists with the expected
configuration, and then tearing it down, run as its own automated pipeline
step distinct from any application-level test. This is also where drift
detection belongs as an ongoing, not one-time, check, comparing every live
stamp's actual configuration against the template that should have produced
it.

At the **routing and cross-stamp layer**, tests exercise the parts unique to
this pattern and easy to skip. that a request for a known tenant lands on
the correct stamp, that an unbound or unknown tenant fails safely rather
than routing to an arbitrary default stamp (as the Go sample in dimension 8
demonstrates by returning an explicit error), that new-tenant assignment
correctly avoids a stamp above its capacity watermark, and that a tenant
migration between stamps, run end to end against real (non-production) data,
leaves exactly one live copy of that tenant's data and never two. This last
check deserves its own dedicated, repeatable test, since a duplicate or lost
tenant during migration is exactly the failure mode named in dimension 11,
and it is precisely the kind of distributed, multi-step operation that a
purely unit-level test cannot catch, the same reasoning that motivates
dedicated tests for the Saga pattern elsewhere in this catalog.

Chaos and failure-injection testing earns a specific place here too, because
stamps are meant to fail independently, the strongest test of the pattern is
deliberately failing one stamp, or one region, in a non-production
environment and confirming, with evidence rather than assumption, that
tenants on every other stamp remain fully unaffected and that the traffic
router correctly stops sending new work to the failed stamp.

## 16. Observability signals

A healthy stamp fleet is visible through signals collected both per stamp
and rolled up across the fleet, and both views are necessary. per-stamp
signals catch a single stamp degrading, fleet-wide signals catch systemic
problems that no single stamp's own dashboard would ever surface.

Per stamp, the load-bearing signals are current tenant count against
configured capacity, request latency and error rate scoped to that stamp
alone, resource utilization of its application and data tier, and time since
its last successful drift check against the infrastructure template. A
stamp whose tenant count sits well above its declared capacity, or whose
latency has drifted away from its sibling stamps under comparable load, is
the earliest and cheapest signal that the scale-out policy has failed to
keep up.

Across the fleet, the signals that matter are total tenant count and total
request volume aggregated across every stamp, the spread of latency and
error rate between the best- and worst-performing stamp (a widening spread
is the leading indicator of the noisy-stamp failure mode in dimension 11,
well before any single stamp trips its own alert threshold), the count of
stamps currently above their scale-out watermark, and the count of stamps
that have drifted from their declared template. Azure's own guidance points
directly at the need for a cross-stamp view, recommending a centralized
observability platform that can "collect and correlate metrics, logs,
traces, and alerts across all stamps" precisely because "it becomes harder to
understand overall health and detect incidents quickly" as the number of
stamps grows
([Deployment Stamps pattern, problems and considerations, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp),
verified 2026-08-02).

The tenant-to-stamp mapping itself deserves its own health check, separate
from any individual stamp's health. a stale or corrupted mapping, one that
points a tenant at a stamp that no longer exists or was decommissioned, fails
silently from the traffic router's point of view (it will happily forward or
redirect based on bad data) and shows up to the affected tenant as a total
outage with no corresponding alert anywhere else in the system, exactly the
symptom named first in dimension 11.

## 17. Security and privacy implications

Deployment stamps change the security surface of a multi-tenant system in
ways that cut in both directions, and a team relying on the pattern as its
entire tenant-isolation story is making a mistake worth naming directly.

On the positive side, a stamp gives the strongest practical form of tenant
isolation available short of fully separate cloud accounts, because there is
no shared process, connection pool, cache, or database instance for a
compromise or a misconfiguration in one tenant's stamp to reach across into
another tenant's stamp. This is exactly why Azure names regulated,
security-sensitive enterprise customers as a primary use case for the
pattern, in dimension 4 above, since a per-tenant dedicated stamp genuinely
satisfies isolation requirements that logical, schema-level tenant
separation inside one shared database cannot credibly claim to satisfy on
its own.

On the negative side, the pattern multiplies, rather than reduces, the
surface a security team has to keep consistent. every stamp is its own
independently deployed collection of network rules, identity and access
bindings, encryption configuration, and patch level, and Azure's own
guidance names "governance and configuration drift" as a first-class
operational concern for exactly this reason
([Deployment Stamps pattern, problems and considerations, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp),
verified 2026-08-02). A security policy update applied to nineteen of twenty
stamps and missed on the twentieth is not a hypothetical, it is the direct,
predictable consequence of the fleet growing faster than the governance
tooling that keeps every stamp aligned, and it is the specific reason the
pattern's own guidance recommends treating governance itself as code,
continuously validated, rather than as a checklist applied by hand per
stamp.

The tenant-to-stamp mapping is itself sensitive data and needs to be treated
that way. it directly reveals which customers are grouped together, which is
occasionally itself confidential (a customer that paid for a dedicated stamp
generally does not want that fact, or the identity of any co-tenants on a
shared stamp, exposed), and it is a high-value target for an attacker
precisely because corrupting or redirecting it, as named in the
observability dimension above, can silently misroute a tenant's traffic and
data to the wrong stamp. Access to modify that mapping should be at least as
tightly controlled as access to any single tenant's data directly.

Finally, cross-region data residency, one of the pattern's strongest
selling points in dimension 4, only actually holds if the pattern is
implemented completely. a stamp pinned to a region satisfies a residency
requirement only when every layer inside that stamp, including logs,
backups, and any cross-stamp aggregation pipeline the tenant's data flows
into, also respects the same regional boundary. A cross-stamp metrics or
logging pipeline that quietly ships raw request bodies, rather than
aggregated, anonymized signals, from every region into one centralized store
can undo a data-residency guarantee the stamp architecture otherwise
correctly provides.

## 18. References

- [Deployment Stamps pattern, Azure Architecture Center, Microsoft Learn](https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp), verified 2026-08-02.
- [Architect Multitenant Solutions on Azure, Azure Architecture Center, Microsoft Learn](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/overview), verified 2026-08-02.
- [Related Resources for Multitenancy, Azure Architecture Center, Microsoft Learn](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/related-resources), verified 2026-08-02.
- John Downs, "Deployment stamp best practices", commit `e6f204a0`, `MicrosoftDocs/architecture-center`, 25 November 2019. [Commit reference, GitHub](https://github.com/MicrosoftDocs/architecture-center/commit/e6f204a0), verified 2026-08-02.
- "Move deployment stamp into design patterns", commit `d247271a`, `MicrosoftDocs/architecture-center`, 22 March 2020. [Commit reference, GitHub](https://github.com/MicrosoftDocs/architecture-center/commit/d247271a), verified 2026-08-02.
- Reducing the Scope of Impact with Cell-Based Architecture, AWS Well-Architected, published 20 September 2023. [AWS documentation](https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/reducing-scope-of-impact-with-cell-based-architecture.html), verified 2026-08-02.
- Reducing the Scope of Impact with Cell-Based Architecture, FAQ, AWS Well-Architected. [AWS documentation](https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/faq.html), verified 2026-08-02.
- "Running 1M databases on Azure SQL for a large SaaS provider, Microsoft Dynamics 365 and Power Platform", Microsoft Azure SQL devblog. [Article](https://devblogs.microsoft.com/azure-sql/running-1m-databases-on-azure-sql-for-a-large-saas-provider-microsoft-dynamics-365-and-power-platform/), verified 2026-08-02.
- Xavier Denis, "A Pods Architecture to Allow Shopify to Scale", Shopify Engineering, 2 March 2018. [Article](https://shopify.engineering/a-pods-architecture-to-allow-shopify-to-scale), verified 2026-08-02.
- Michael T. Nygard, *Release It! Design and Deploy Production-Ready Software*, Pragmatic Bookshelf, 2007, Bulkhead stability pattern (for the resource-pool-level relative distinguished in dimension 13, page reference not independently confirmed for this entry).
