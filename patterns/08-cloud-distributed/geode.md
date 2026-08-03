---
name: Geode
slug: geode
family: 08-cloud-distributed
category: Geo-Distribution and Availability
aliases: [Geode Pattern, Active-Active Geo-Distribution, Geo-Replicated Compute]
first_described: "Microsoft Azure Architecture Center, Cloud Design Patterns catalog"
maturity: established
related: [deployment-stamps, sharding, gateway-routing, health-endpoint-monitoring, materialized-view, circuit-breaker]
incompatible_with: []
verified: 2026-08-02
---

# Geode

## 1. Name, aliases, and lineage

The canonical name used in this catalog is Geode, matching the title Microsoft
gives the entry in the Azure Architecture Center's Cloud Design Patterns
catalog, where the pattern is defined as deploying "a collection of backend
services into a set of geographical nodes, each of which can service any
request from any client in any region"
([Geode pattern, Azure Architecture Center, Microsoft Learn](https://learn.microsoft.com/en-us/azure/architecture/patterns/geodes),
verified 2026-08-02). The page's own wordplay explains the name directly in
its opening line, splicing "geographical" and "node" into "ge (ographical)
node (e)", which is why every deployed unit in the pattern is itself called a
geode, the same word used for the pattern as a whole (same source).

This entry treats three phrases as aliases for the identical idea. Geode
Pattern is simply the formal catalog title with its type made explicit.
Active-Active Geo-Distribution names the operational property the pattern
buys, every deployed region actively serves both reads and writes at once,
in contrast to an active-passive or single-write-region design. Geo-Replicated
Compute is the phrase this entry uses when emphasizing the solution's actual
mechanism, the source states plainly that the pattern "brings the compute to
the data" rather than the more classical approach of bringing remote data to
one centralized compute tier (same source, Context and problem section).

The Azure Architecture Center does not attribute Geode to a single named
author the way it does for some sibling entries in this same catalog family.
The page's current metadata lists Clayton Siemens as its maintaining author of
record, with a last major content update recorded as 18 March 2024 and
a most recent editorial pass on 9 December 2025
([`geodes.yml` source, `MicrosoftDocs/architecture-center-pr`](https://learn.microsoft.com/en-us/azure/architecture/patterns/geodes),
verified 2026-08-02), but this reflects ownership of the current text rather
than original authorship, and this catalog does not assert a first-described
person or year for Geode with the same confidence it can for, say, Deployment
Stamps in this same family. What can be said with confidence is that Geode
sits inside the same Cloud Design Patterns catalog that Microsoft's patterns
and practices group began publishing in 2014 and has continued to extend, and
that the pattern's own text names a real, much older system as an early,
partial instance of the same idea, discussed in dimension 9 below.

One naming confusion is worth heading off early because it recurs constantly
in search results and in casual conversation among engineers. Apache Geode is
an entirely separate, unrelated piece of software, an in-memory data grid
originally built as GemFire by GemStone Systems and now an Apache Software
Foundation project, distributed under the Apache License 2.0
([`apache/geode`, GitHub](https://github.com/apache/geode), verified
2026-08-02). Apache Geode is a specific product a team installs and runs. The
Geode pattern documented in this entry is an architectural shape a team can
build with many different products, Azure's own worked solution happens to use
Azure Cosmos DB as the replicated data plane, and nothing in the pattern
requires Apache Geode's software at all. The shared word is a coincidence of
naming, not a relationship, and this entry is about the architectural pattern,
never the Apache project.

## 2. Problem and context

A service with users spread across a continent, or across the world, starts
from the simplest possible shape. one region hosts the application tier, one
region hosts the database, and every request from every user, no matter how
far away they are, travels to that one place and back. Azure's own framing of
the problem calls this "bring the data to the compute", describing the classic
design as storing data in a remote server that also serves as the compute
tier, relying on vertical scale-up as the only tool for growth
([Geode pattern, Context and problem, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/geodes),
verified 2026-08-02). This shape is not a mistake. it is the correct starting
point for almost every service, and it works fine for a long time.

Three separate pressures eventually break it, and Azure names all three in the
same short paragraph. The first is raw physics. a user on the far side of the
globe from the single hosting region pays a network latency tax on every
request that a user near the region never pays, and no amount of application
optimization removes speed-of-light distance. The second is burst capacity. a
single region absorbs one country's or one continent's entire demand curve at
once, so a promotional spike, a news event, or a seasonal peak in one part of
the world has nowhere to go but through that one region's capacity limit.
The third is cost and operational complexity of the naive fix. an engineering
team's first instinct is often to stand up full, independent copies of the
whole application in every region a user base cares about, and Azure calls
this "cost-prohibitive" as a standing practice for a service that must run
continuously (same source).

Cloud platforms changed what is achievable here in a specific way. front-end
load balancing across regions has become a largely off-the-shelf capability,
so routing a user's request to a nearby edge point of presence is no longer
the hard part. What remains hard, and what the Geode pattern directly
addresses, is the back end. once a request reaches a nearby region, that
region needs a locally available, sufficiently fresh copy of whatever data
the request needs, or the network-latency win from smart front-end routing is
undone the moment the application tier turns around and calls back to a
single, far-away database. Azure states the resulting design principle
directly. "For availability and performance, getting data closer to the user
is good," and once a user base is itself spread across the globe, "the
geo-distributed datastores should also be colocated with the compute
resources that process the data" (same source). The pattern's solution
follows from that principle exactly, brought to its logical conclusion. deploy
complete, self-sufficient units of both compute and data together, in as many
geographic locations as the user base and the availability target require,
and make every one of those units capable of answering any request on its
own.

The context in which this becomes the right answer, rather than an expensive
overreaction, has a specific shape too, and it is a demanding one. the
service's user base is genuinely spread over a wide geography, the workload's
availability requirement is extreme enough that surviving the simultaneous
loss of more than one region matters, and the team building it is working
as a cloud-native system from the start rather than retrofitting an existing
single-region system, a constraint the source itself calls out directly in
its own guidance on when not to use the pattern, discussed fully in dimension
4.

## 3. Forces

- **Latency versus write consistency.** Geode favors latency, decisively.
  Every geode answers a nearby user without a cross-ocean round trip, which is
  the entire point, but that requires accepting that a write landing in one
  geode is not instantly visible everywhere else. Azure Cosmos DB, the data
  plane the source names explicitly for this pattern, makes the trade
  structural rather than merely a tuning choice. an account configured for
  multiple write regions "can't use strong consistency" at all, because a
  distributed system cannot deliver a zero recovery point objective and a
  zero recovery time objective simultaneously across regions that are all
  independently writable
  ([Consistency levels, Strong consistency and multiple write regions, Azure Cosmos DB documentation](https://learn.microsoft.com/en-us/azure/cosmos-db/consistency-levels),
  verified 2026-08-02). A genuine, all-writable Geode fleet therefore always
  operates on the eventual side of the consistency scale for cross-region
  visibility, whatever level an individual read chooses locally.
- **Availability versus operational surface area.** Availability wins, at a
  real operational cost. The pattern's stated benefit is that "the resiliency
  of the whole solution increases with each added geode," to the point that a
  fleet "can survive the loss of multiple service regions at the same time"
  ([Geode pattern, When to use this pattern, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/geodes),
  verified 2026-08-02). The same source is equally direct that this
  multiplies the number of secrets, ingress points, and independently
  deployed components a security and operations team must keep hardened and
  observed, a cost that grows in direct proportion to the geode count that buys the
  resilience.
- **Uniformity versus tenant or region-specific needs.** Geode pushes hard
  toward uniformity, harder than most patterns in this family. every geode
  must be an identical, interchangeable copy of the same deployable template,
  because the entire routing model depends on any geode being able to answer
  any request. This is close to the opposite of Deployment Stamps, this
  catalog's sibling pattern, where different stamps are explicitly permitted
  to diverge in version or capacity to serve different tenant needs. A
  workload with a real per-tenant difference, a per-customer version pin, or a
  data-residency carve-out, fights this force rather than being served by it,
  which is exactly why the source treats the two patterns as a documented
  fork with each side ruling out the other, rather than a middle ground a
  team can dial up or down.
- **Cost versus idle capacity.** Every geode is a standing, provisioned copy
  of both the compute and the data tier, and the source is explicit that
  "deployment of additional geodes...come with increased costs for the
  additional memory and compute, but do not do so on a per transaction basis"
  (same source, Issues and considerations). A geode serving a thin slice of
  global traffic still pays close to the full fixed cost of a geode serving a
  heavy one, which is the force that pushes the pattern's own guidance toward
  serverless compute where the platform allows it.
- **Simplicity of the request path versus complexity of everything around
  it.** From a single request's point of view, a Geode fleet is almost plain,
  a nearby node answers locally with no cross-region call on the hot path.
  Everything that is not the request path, conflict resolution, cross-region
  tracing, secret distribution, capacity planning per geode, carries the
  complexity instead. The source's own considerations section reads as a
  list of exactly these knock-on concerns, which is a fair signal that
  the pattern's true cost lives outside the request path rather than inside
  it.

## 4. Applicability and non-applicability

Reach for Geode when the workload's shape matches what Azure's own guidance
states directly.

- The platform genuinely needs high scale with users distributed over a wide
  geographic area, not merely users in two or three metropolitan areas that a
  single well-placed region and a content delivery network could already
  serve adequately.
- The service's availability and resilience requirements are extreme, to the
  point that surviving the simultaneous loss of more than one region is a
  real, stated requirement rather than a nice-to-have, since Azure's own
  when-to-use guidance frames the pattern's payoff specifically in terms of
  multi-region loss, not single-region loss alone
  ([Geode pattern, When to use this pattern, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/geodes),
  verified 2026-08-02).
- The team is building as a cloud-native system from the outset and can commit to the
  operational discipline the pattern demands, modern DevOps and
  infrastructure-as-code practices sufficient to produce and deploy identical
  geodes rapidly across many regions, since geodes are only interchangeable
  if they are provably identical (same source, Issues and considerations).
- The workload can tolerate, or is explicitly designed around, cross-region
  data replication that is not instantaneous, and the business has already
  decided what staleness window is acceptable for which categories of data.

Do not reach for Geode, and this list matters more than the first, when any of
the following holds, mirroring the pattern's own stated non-applicability
directly.

- **Not every geode can be treated as equal for data storage.** The source
  names this exact failure mode. data residency requirements pin certain
  data to certain jurisdictions, an application needs to maintain per-session
  temporary state tied to wherever that session started, or traffic is
  heavily weighted toward one region rather than genuinely global. In any of
  these cases the source recommends Deployment Stamps combined with a global
  routing plane that is aware of which stamp actually holds a given user's
  data, rather than Geode
  ([Geode pattern, When to use this pattern, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/geodes),
  verified 2026-08-02).
- **There is no genuine geographical distribution requirement.** A service
  whose users sit inside one country, or one metropolitan cluster, gains
  nothing from paying Geode's cost. availability zones and paired regions
  inside a single cloud region already deliver strong local resilience at a
  fraction of the operational surface (same source).
- **The platform is a legacy system that needs to be retrofitted, not built
  fresh.** The source states this without hedging. the pattern "works for
  cloud-native development only, and can be difficult to retrofit" (same
  source). Bolting Geode onto an existing single-region monolith is a
  multi-year architectural rewrite disguised as an infrastructure change, and
  teams underestimate this constantly.
- **The architecture and its requirements are simple.** When geo-redundancy
  and global geo-distribution are not required or advantageous for the
  workload at hand, the source is explicit that Geode is not the answer (same
  source). The pattern's baseline cost is high enough that applying it as a
  default, rather than as a response to a proven need, is close to always a
  mistake.
- **Bounded staleness is being reached for as the consistency model alongside
  multiple write regions.** This is a narrower, more technical
  non-applicability that the underlying data platform states about itself
  rather than the pattern page. Cosmos DB's own documentation calls bounded
  staleness in a multi-write account "an anti-pattern", because its guarantee
  is defined in terms of replication lag between a primary and its
  secondaries, a relationship that stops holding once every region can also
  write locally
  ([Consistency levels, Bounded staleness consistency, Azure Cosmos DB documentation](https://learn.microsoft.com/en-us/azure/cosmos-db/consistency-levels),
  verified 2026-08-02). A team building a real, all-writable Geode fleet on
  Cosmos DB needs session or eventual consistency, not bounded staleness,
  covered further in dimension 8.

## 5. Structure

The participants in a Geode architecture are deployed, running units and the
platform services that connect them, not classes in the object-oriented
sense, the same character this pattern shares with its sibling, Deployment
Stamps.

- **Geode.** One complete, self-contained satellite deployment holding both
  an application compute tier and a full, locally readable and locally
  writable copy of the data tier. A geode has no dependency outside its own
  footprint, so if one fails outright, every other geode keeps operating
  without interruption
  ([Geode pattern, Solution, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/geodes),
  verified 2026-08-02).
- **Front-end routing and acceleration layer.** A global load balancer or
  edge routing service that sits in front of every geode and directs a
  client's request over the shortest available network path to a nearby
  geode. Azure names Azure Front Door as the reference example, calling out
  its dynamic content acceleration, routing through an optimal point of
  presence, and Split TCP as concrete mechanisms this layer relies on (same
  source, Issues and considerations).
- **Replication backplane.** A geo-replicated, read-write data service that
  every geode's application tier talks to for its own local reads and
  writes, and which is itself responsible for propagating each geode's writes
  to every other geode and reconciling any conflicting writes that land at
  the same logical record in more than one geode at once. Azure names Azure
  Cosmos DB as the reference backplane precisely because it offers configurable
  multi-region writes with a defined conflict-resolution policy (same source).
- **Change feed and cross-geode messaging.** An optional, but commonly used,
  event stream derived from the backplane's own write log, letting one
  geode react to data that changed in another geode without either geode
  needing to know the other exists. Azure's own considerations describe
  wiring this through the Cosmos DB change feed's lease container concept and
  a corresponding lease collection prefix in an Azure Functions binding, and
  note that geodes "can communicate with remote users via other geodes in a
  mesh pattern, without knowing or caring where the remote user is located"
  (same source, Issues and considerations).
- **Per-geode API layer (optional).** A lightweight API management surface in
  front of each geode's own compute, applying rate limiting or other request
  shaping at the region closest to the caller rather than centrally (same
  source).
- **Cross-geode observability plane.** A centralized destination that every
  geode's front-end and compute layer feeds telemetry into, so that a request
  that touched more than one geode asynchronously can still be traced as one
  logical operation, discussed fully in dimension 16.

A structural distinction the source draws directly, and one that is easy to
get wrong, is that a Geode fleet is not a cluster in the classical
distributed-systems sense. "Geodes aren't the same as clusters because they
share a replication backplane, so the platform takes care of quorum issues"
(same source, Solution). The correctness-critical coordination work that a
hand-built cluster would normally solve with a consensus protocol is instead
delegated entirely to the replication backplane, and a Geode implementation
that reinvents a leader-election or quorum layer on top of that backplane has
misunderstood the pattern, a point returned to directly in dimension 11.

## 6. ASCII structure diagram

```
                          Global users, world-wide
                                     |
                                     v
                +----------------------------------------+
                |  Front-end routing and acceleration      |
                |  (global load balancer / edge network)   |
                +---------+-----------+-----------+--------+
                          |           |           |
          shortest path   |           |           |   shortest path
                          v           v           v
             +------------+  +------------+  +------------+
             |  Geode: EU  |  |  Geode: US  |  |  Geode: APAC|
             |  West       |  |  East       |  |  South      |
             |             |  |             |  |             |
             | +---------+ |  | +---------+ |  | +---------+ |
             | | App tier| |  | | App tier| |  | | App tier| |
             | +----+----+ |  | +----+----+ |  | +----+----+ |
             |      |      |  |      |      |  |      |      |
             | +----v----+ |  | +----v----+ |  | +----v----+ |
             | |Local copy| |  | |Local copy| |  | |Local copy| |
             | |of data   | |  | |of data   | |  | |of data   | |
             | +----+----+ |  | +----+----+ |  | +----+----+ |
             +------|------+  +------|------+  +------|------+
                    |                |                |
                    +--------+-------+--------+-------+
                             |                |
                             v                v
                +----------------------------------------+
                |   Replication backplane                  |
                |   (geo-replicated read-write data plane, |
                |    conflict resolution, change feed)      |
                +----------------------------------------+
```

## 7. Dynamics

Three flows matter for a Geode fleet, and each stresses a different part of
the structure above. steady-state request handling, conflict resolution
between concurrently accepted writes, and the failover behavior that is the
pattern's whole reason to exist.

**Steady-state request flow.** A client's request first reaches the front-end
routing layer, which resolves the nearest, currently healthy geode, most
commonly through anycast networking or geo-aware DNS, and forwards the request
there without exposing the client to the underlying topology. The geode's
application tier serves a read directly from its own local copy of the data,
paying no cross-region latency at all for that read. A write follows the same
initial path, landing at the nearest geode's local data copy first, and the
backplane then propagates that write asynchronously to every other geode's
copy. Which consistency guarantee that write's visibility elsewhere carries is
a property of the backplane's configuration, covered fully in dimension 8, not
of the routing layer.

```
client request arrives at edge
        |
        v
front-end routing resolves nearest healthy geode
        |
        v
request served entirely inside that geode (local read or local write)
        |
   was it a write? ---- yes ----> backplane propagates the write asynchronously
        | no                            to every other geode's local copy
        v                                        |
  response returned to client                    v
                                     each other geode's local copy updated,
                                     bounded by the configured staleness window
```

**Conflict resolution flow.** Because every geode accepts writes locally, two
different geodes can accept a write to the identical logical record at nearly
the same moment, one user updating their profile from a session that happens
to route to the EU geode while a second update to the same record, perhaps
from a different device, routes to the US geode. The backplane detects this as
a write conflict once both updates reach it and applies whatever conflict
resolution policy the team configured. Azure Cosmos DB's default policy is
last-write-wins by timestamp, where "the item with the highest value for the
conflict resolution path becomes the winner," and the system arbitrates
deterministically if two writes carry the exact same timestamp value
([Conflict resolution policies, Azure Cosmos DB documentation](https://learn.microsoft.com/en-us/azure/cosmos-db/conflict-resolution-policies),
verified 2026-08-02). The alternative is a custom, application-registered
merge procedure invoked automatically by the platform whenever a conflict is
detected, with any conflict that procedure cannot resolve, or that throws an
exception, written to a durable conflicts feed for the application to resolve
by hand later (same source). Whichever policy runs, every geode eventually
converges on the identical winning value, which is the property that lets any
geode keep answering any request correctly once replication catches up.

**Regional failure and failover flow.** When a geode becomes unreachable or is
detected as unhealthy, the front-end routing layer stops directing new
requests to it and instead resolves the next-nearest healthy geode for every
client that would previously have landed there. Because every surviving geode
already holds its own full copy of the data, it can serve those redirected
requests immediately, with no data-loading or warm-up step required, which is
the concrete mechanism behind the resilience claim discussed in dimension 3.
The honest caveat, covered fully as a failure mode in dimension 11, is that
any write accepted by the failed geode but not yet propagated to the
surviving geodes before the failure is, from the surviving geodes' point of
view, gone, so the pattern's recovery point objective during a regional loss
is bounded by whatever replication lag existed at the moment of failure,
never zero for a genuinely multi-write deployment.

## 8. Implementation variants

**Full active-active, every geode writable (the canonical form).** Every
geode's application tier accepts both reads and writes locally, and the
backplane is configured for multi-region writes with an explicit conflict
resolution policy. This is the shape the source's own definition describes,
"every instance can service any request from any client", and it is the
variant that delivers the lowest write latency for a nearby user while
carrying the highest complexity a team must manage
([Geode pattern, Azure Architecture Center, Microsoft Learn](https://learn.microsoft.com/en-us/azure/architecture/patterns/geodes),
verified 2026-08-02). Cosmos DB's consistency guidance for this shape is
specific. session consistency is the level its own documentation calls "the
most widely used consistency level for single-region and globally distributed
applications," offering read-your-writes and write-follows-reads guarantees
scoped to one client session while keeping write latency close to eventual
consistency's
([Consistency levels, Session consistency, Azure Cosmos DB documentation](https://learn.microsoft.com/en-us/azure/cosmos-db/consistency-levels),
verified 2026-08-02).

**Single-write-region with globally distributed reads (the hybrid, read-only
geode variant).** Only one region accepts writes, and every other geode holds
a read-only replica kept current by the same replication backplane, refreshed
either continuously or within a configured staleness bound. This shape gives
up the pattern's full any-geode-any-write property in exchange for a much
simpler consistency story, and it is the shape for which Cosmos DB's bounded
staleness level is actually appropriate, since bounded staleness is "primarily
beneficial to single-region write accounts with two or more regions" and the
same documentation calls the same level applied to a multi-write account "an
anti-pattern"
([Consistency levels, Bounded staleness consistency, Azure Cosmos DB documentation](https://learn.microsoft.com/en-us/azure/cosmos-db/consistency-levels),
verified 2026-08-02). Teams commonly land here as an intentional, permanent
middle ground, not merely as a stepping stone, when write volume is low
relative to read volume and a slightly longer write path to one home region
is an acceptable cost for a materially simpler system.

**Geography-partitioned writes with full read replication (the zone-sharded
hybrid).** Rather than every geode being symmetric for writes, the data plane
is divided by row, so a given record's home region is a fixed property of
that record, while replicas of every record still exist in every region.
CockroachDB's `REGIONAL BY ROW` table locality implements exactly this shape.
each row carries a hidden `crdb_region` column recording its home region,
"each row is optimized for access from a specific home region," and the
database automatically places that row's leaseholder, the replica that
serves the row's writes, inside its home region, while the table and its
indexes are partitioned by region underneath the covers
([Table Localities, CockroachDB documentation](https://www.cockroachlabs.com/docs/stable/table-localities),
verified 2026-08-02). This variant trades away some of the pure pattern's
write symmetry in exchange for avoiding true multi-master conflict resolution
entirely, since only one region is ever the leaseholder of record for a given
row's writes at any moment.

**Change-feed-driven local aggregation versus centralize-then-replicate.** For
workloads that compute an aggregate over data rather than simply storing and
retrieving individual records, the source names two distinct, competing
implementation choices, each with real trade-offs. one path processes and
aggregates data independently inside every geode, the other computes the
aggregation once, in a single geode, and replicates only the finished result
outward to every other geode, with the Cosmos DB change feed processor's lease
container concept, and the corresponding lease collection prefix setting in
an Azure Functions binding, offered as the concrete mechanism for controlling
which geode owns which slice of the change feed
([Geode pattern, Issues and considerations, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/geodes),
verified 2026-08-02).

**Big data and near-edge compute variant.** The source names, without
elaborating in detail, that the same underlying idea, colocating compute with
data across many independent nodes and later consolidating results, occurs in
big data architectures that process data on commodity hardware local to where
it lives and use a MapReduce-style step to consolidate results across
machines, and separately in near-edge compute deployments that push
processing physically close to the network edge to reduce response time (same
source). This entry treats both as a named category rather than a specific
system, since the source itself does not point to a single reference
implementation for either.

**Windows Active Directory, an early, partial variant.** The source itself
names Active Directory as an example predating the cloud-era pattern by
decades, describing it as implementing multi-primary replication where "all
updates and requests can in theory be served from all serviceable nodes,"
while immediately qualifying that description. Flexible Single Master
Operation roles mean "all geodes aren't equal", since certain operations, such
as schema changes, are still handled by one distinguished domain controller
rather than being fully symmetric across every node (same source, Examples).
This is the clearest, source-provided illustration that "every node can
answer" and "every node is identical for every operation" are two separate
promises, and a real system can deliver the first without fully delivering
the second.

**Reference implementation sketches.** The three concerns above, routing a
client to the nearest healthy geode, resolving a write conflict once one is
detected, and failing over cleanly when a geode goes dark, are small enough
to demonstrate directly, independent of any specific cloud platform.

The first sketch is the front-end routing layer from dimension 5, written in
TypeScript. it picks the nearest geode by great-circle distance and refuses
to route to an unhealthy one.

```typescript
interface Geode {
  id: string;
  lat: number;
  lon: number;
  healthy: boolean;
}

function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371;
  const toRad = (d: number) => (d * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

// Routes a client to the nearest geode that is currently healthy.
// Throws if every geode in the fleet has failed its health probe.
function routeToNearestGeode(
  clientLat: number,
  clientLon: number,
  geodes: Geode[]
): Geode {
  const candidates = geodes.filter((g) => g.healthy);
  if (candidates.length === 0) {
    throw new Error("no healthy geode available in the fleet");
  }
  return candidates.reduce((best, g) => {
    const dBest = haversineKm(clientLat, clientLon, best.lat, best.lon);
    const dG = haversineKm(clientLat, clientLon, g.lat, g.lon);
    return dG < dBest ? g : best;
  });
}

const fleet: Geode[] = [
  { id: "geode-eu-west", lat: 53.3498, lon: -6.2603, healthy: true },
  { id: "geode-us-east", lat: 39.0438, lon: -77.4874, healthy: true },
  { id: "geode-ap-south", lat: 19.076, lon: 72.8777, healthy: true },
];

const munich = { lat: 48.1351, lon: 11.582 };
const chosen = routeToNearestGeode(munich.lat, munich.lon, fleet);
console.log(`client in Munich routed to ${chosen.id}`);
if (chosen.id !== "geode-eu-west") {
  throw new Error("expected the EU geode to win for a Munich client");
}

const failedOver = fleet.map((g) =>
  g.id === "geode-eu-west" ? { ...g, healthy: false } : g
);
const rerouted = routeToNearestGeode(munich.lat, munich.lon, failedOver);
console.log(`after geode-eu-west failure, Munich client routed to ${rerouted.id}`);
if (rerouted.id === "geode-eu-west") {
  throw new Error("router must never select an unhealthy geode");
}
```

Compiled with `tsc --target es2020 --module commonjs --strict` and run under
Node, this prints the Munich client landing on `geode-eu-west`, then on
`geode-ap-south` once the EU geode is marked unhealthy, matching the
steady-state and failover flows from dimension 7.

The second sketch is the conflict resolution flow from dimension 7, written
in Python. it models three geodes each holding their own local store and
converges them with a last-write-wins policy after a simulated write burst.

```python
from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class Geode:
    geode_id: str
    store: Dict[str, Tuple[str, float]] = field(default_factory=dict)

    def write(self, key: str, value: str, ts: float) -> None:
        self.store[key] = (value, ts)


def resolve_last_write_wins(
    a: Tuple[str, float], b: Tuple[str, float], a_id: str, b_id: str
) -> Tuple[str, float]:
    # Higher timestamp wins. On an exact tie, the higher geode id wins,
    # matching Cosmos DB's documented tie-break of a system-chosen winner.
    if a[1] != b[1]:
        return a if a[1] > b[1] else b
    return a if a_id > b_id else b


def replicate(geodes: list[Geode]) -> None:
    all_keys = set()
    for g in geodes:
        all_keys |= g.store.keys()
    for key in all_keys:
        winner = None
        winner_id = None
        for g in geodes:
            entry = g.store.get(key)
            if entry is None:
                continue
            if winner is None:
                winner, winner_id = entry, g.geode_id
            else:
                winner = resolve_last_write_wins(winner, entry, winner_id, g.geode_id)
                winner_id = g.geode_id if winner is entry else winner_id
        for g in geodes:
            g.store[key] = winner


def main() -> None:
    eu = Geode("geode-eu-west")
    us = Geode("geode-us-east")
    ap = Geode("geode-ap-south")
    fleet = [eu, us, ap]

    eu.write("cart:42", "3 items", ts=100.0)
    us.write("cart:42", "5 items", ts=103.5)
    ap.write("profile:9", "name=alice", ts=50.0)

    replicate(fleet)

    for g in fleet:
        assert g.store["cart:42"] == ("5 items", 103.5), g.store["cart:42"]
        assert g.store["profile:9"] == ("name=alice", 50.0)

    print("all geodes converged on cart:42 ->", eu.store["cart:42"])
    print("all geodes converged on profile:9 ->", eu.store["profile:9"])


if __name__ == "__main__":
    main()
```

Run under `python3`, this prints that every geode in the fleet converges on
the identical winning value for both keys after `replicate()` runs, the
concrete behavior the source describes when it says a Geode fleet's
replication backplane "takes care of quorum issues" on the team's behalf.

The third sketch is the health-driven failover flow, written in Go, and it
exercises the concurrency angle directly. fifty concurrent goroutines all
resolve the same healthy geode, then the registry is driven through a
failure and a recovery.

```go
package main

import (
	"fmt"
	"sync"
)

type Registry struct {
	mu      sync.RWMutex
	healthy map[string]bool
	order   []string
}

func NewRegistry(ids ...string) *Registry {
	h := make(map[string]bool, len(ids))
	for _, id := range ids {
		h[id] = true
	}
	return &Registry{healthy: h, order: ids}
}

func (r *Registry) MarkUnhealthy(id string) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.healthy[id] = false
}

func (r *Registry) MarkHealthy(id string) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.healthy[id] = true
}

// Route returns the first geode still marked healthy, in registration order.
// No global lock is held while probes run concurrently against other geodes.
func (r *Registry) Route() (string, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	for _, id := range r.order {
		if r.healthy[id] {
			return id, nil
		}
	}
	return "", fmt.Errorf("no healthy geode available in the fleet")
}

func main() {
	reg := NewRegistry("geode-eu-west", "geode-us-east", "geode-ap-south")

	var wg sync.WaitGroup
	results := make(chan string, 100)
	for i := 0; i < 50; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			id, err := reg.Route()
			if err != nil {
				results <- "ERROR: " + err.Error()
				return
			}
			results <- id
		}()
	}
	wg.Wait()
	close(results)

	counts := map[string]int{}
	for r := range results {
		counts[r]++
	}
	fmt.Println("routing before failure:", counts)
	if counts["geode-eu-west"] != 50 {
		panic("expected all 50 concurrent requests to land on the first healthy geode")
	}

	reg.MarkUnhealthy("geode-eu-west")
	id, err := reg.Route()
	if err != nil {
		panic(err)
	}
	fmt.Println("after geode-eu-west fails, traffic routes to:", id)
	if id != "geode-us-east" {
		panic("expected failover to the next healthy geode")
	}

	reg.MarkHealthy("geode-eu-west")
	id, err = reg.Route()
	if err != nil {
		panic(err)
	}
	fmt.Println("after geode-eu-west recovers, traffic routes to:", id)
}
```

Run with `go run`, this prints all fifty concurrent lookups landing on
`geode-eu-west`, then failing over to `geode-us-east` the moment
`MarkUnhealthy` runs, then returning to `geode-eu-west` once it recovers,
which is the failover flow from dimension 7 exercised under real
concurrency rather than described in prose alone.

## 9. Known production uses

- **Windows Active Directory (Microsoft), multi-primary domain controller
  replication.** Azure's own Geode pattern page names Active Directory
  directly as an early variant of the pattern, describing its multi-primary
  replication model where in theory any domain controller can serve any
  update or request, while noting that Flexible Single Master Operation
  roles mean the domain controllers are not fully interchangeable for every
  kind of operation
  ([Geode pattern, Examples, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/geodes),
  verified 2026-08-02). This is a useful production example precisely
  because it predates the term Geode by roughly two decades and shows the
  underlying architectural idea was already solving a real operational
  problem, keeping directory lookups and writes available and local across a
  large distributed organization, long before cloud platforms made a
  fully-managed geo-replicated data plane an off-the-shelf building block.
- **Netflix, Active-Active multi-regional resiliency.** Netflix engineers
  Ruslan Meshenberg, Naresh Gopalani, and Luke Kosewski documented Netflix's
  own move to serving all production traffic from two independently
  sufficient AWS regions, US-East-1 and US-West-2, simultaneously, describing
  the design requirement plainly. "Services must be stateless, all data and
  state replication needs to be handled in the data tier," with every
  service instance accessing resources local to its own region so that no
  cross-region call sits on the user request path
  ([Active-Active for Multi-Regional Resiliency, Netflix Technology Blog, 12 February 2013](https://netflixtechblog.com/active-active-for-multi-regional-resiliency-c47719f6685b),
  verified 2026-08-02). Netflix's implementation used Apache Cassandra's
  multi-directional, multi-region asynchronous replication for durable data,
  and a caching layer built on EVCache with cross-region cache invalidation
  delivered over Amazon SQS, and under normal operation split roughly half of
  incoming traffic to each region by geo-DNS, with tooling to override that
  routing and send all traffic to the surviving region during a regional
  outage of any real size (same source). This is the clearest large-scale,
  independently documented instance of the canonical, fully active-active
  variant described in dimension 8, built years before Azure formally named
  the pattern.
- **CockroachDB, `REGIONAL BY ROW` multi-region table locality.** Cockroach
  Labs' own product documentation describes a multi-region deployment where
  a table's rows are automatically partitioned by a home region column, "each
  row is optimized for access from a specific home region," with that row's
  write-serving replica placed inside its home region and read replicas of
  every region's data distributed across the rest of the cluster
  ([Table Localities, CockroachDB documentation](https://www.cockroachlabs.com/docs/stable/table-localities),
  verified 2026-08-02). This is a named, currently shipping, generally
  available commercial database implementing the zone-sharded hybrid variant
  described in dimension 8, and it is useful evidence that the pattern's core
  idea, colocating writable data with the geography that generates it, has
  been productized directly into a mainstream distributed database rather
  than remaining a bespoke architecture every team must assemble from
  primitives by hand.

## 10. Consequences

**Positive consequences.**

- Every user is served from a nearby geode for both reads and, in the
  canonical variant, writes, removing cross-continent network latency from
  the request path entirely rather than merely caching around it.
- The fleet's resilience genuinely scales with the number of geodes deployed,
  and a well-built fleet can survive the concurrent loss of more than one
  region at once, a stronger guarantee than a typical single-region or
  paired-region deployment offers
  ([Geode pattern, When to use this pattern, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/geodes),
  verified 2026-08-02).
- Failover requires no data warm-up step. because every surviving geode
  already carries its own full copy of the data, it answers a redirected
  request immediately rather than needing to fetch, rebuild, or rehydrate
  state first.
- Scaling out is additive rather than disruptive. adding a new geode extends
  geographic coverage and capacity without requiring a redesign of the
  routing or data model, provided the deployment template stays reproducible.
- The design forces an application to be honest about its own state
  management early. a team cannot half-build a Geode fleet with hidden
  in-memory session state living only in one node's process, because that
  state would silently disappear the moment routing sent a user's next
  request somewhere else, so the discipline the pattern demands tends to
  surface latent bugs that a single-region design would have let slide.

**Negative consequences.**

- The pattern gives up strong, cross-region consistency by construction in
  its canonical, fully writable form, since the underlying data platform
  cannot offer strong consistency once more than one region is independently
  writable
  ([Consistency levels, Strong consistency and multiple write regions, Azure Cosmos DB documentation](https://learn.microsoft.com/en-us/azure/cosmos-db/consistency-levels),
  verified 2026-08-02), so application logic must be written to tolerate, or
  actively work around, eventual visibility of writes across geodes.
- Operating cost rises with every geode added, and does so on a standing,
  fixed-capacity basis rather than in proportion to the traffic each geode
  actually carries, which the source states directly
  ([Geode pattern, Issues and considerations, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/geodes),
  verified 2026-08-02).
- The operational and security surface area multiplies with the geode count,
  more secrets to manage, more network ingress points to lock down, and more
  independent deployments to keep patched and configured identically (same
  source), a cost discussed fully as a security implication in dimension 17.
- The design is explicitly and admittedly cloud-native only, and the source
  states it can be difficult to retrofit onto an existing platform (same
  source), meaning a team cannot ease into this pattern incrementally on top
  of legacy infrastructure the way some other resilience patterns allow.
- Tracing and debugging get harder, not easier, because the pattern
  "implicitly decouples everything", so following one logical user request
  across geodes, especially when it involves asynchronous, change-feed-driven
  cross-geode communication, requires deliberate, centralized correlation
  that a single-region system never had to build (same source).

## 11. Failure modes and misuse

- **Symptom.** A write a user made shortly before a regional outage appears to
  have disappeared once the region recovers or once the user's traffic fails
  over to another geode. **Cause.** Cross-region replication in a genuinely
  active-active deployment is asynchronous, so a write accepted by the
  failed geode but not yet propagated to any surviving geode is, from every
  surviving geode's point of view, a write that never happened, and the
  data platform's own documentation states the resulting recovery point
  objective is bounded, not zero, for every consistency level below strong
  ([Consistency levels, Consistency levels and data durability, Azure Cosmos DB documentation](https://learn.microsoft.com/en-us/azure/cosmos-db/consistency-levels),
  verified 2026-08-02). **Fix.** Choose a consistency and replication
  configuration whose stated recovery point objective the business has
  explicitly accepted for the affected data category, and design write flows
  to be idempotent and safely retriable, so a client that notices a write did
  not survive a failover can simply resubmit it rather than the application
  silently losing user intent.
- **Symptom.** Two updates a user made in quick succession, from two
  different devices or sessions, resolve to only one of them taking effect,
  with no error surfaced anywhere. **Cause.** Both updates were accepted
  locally by two different geodes at nearly the same time, the backplane's
  conflict resolution policy is last-write-wins by timestamp, and the
  documentation is explicit that "the item with the highest value for the
  conflict resolution path becomes the winner"
  ([Conflict resolution policies, Azure Cosmos DB documentation](https://learn.microsoft.com/en-us/azure/cosmos-db/conflict-resolution-policies),
  verified 2026-08-02), so the earlier write is discarded silently rather
  than merged or flagged. **Fix.** Register a custom, application-aware
  conflict resolution procedure for record types where silent
  last-write-wins is unacceptable, or route a given logical owner's writes
  through session affinity so the same user's own updates never race against
  each other across two different geodes in the first place.
- **Symptom.** A team enables bounded staleness consistency on a multi-write
  Geode deployment expecting a strong-consistency-like guarantee, and later
  discovers correctness assumptions the team built on that guarantee do not
  hold. **Cause.** The underlying platform documents this configuration as an
  explicit anti-pattern, stating plainly that "Bounded Staleness in a
  multi-write account is an anti-pattern," since the level's guarantee is
  defined relative to a primary-to-secondary replication lag that no longer
  has a single meaning once every region can write locally
  ([Consistency levels, Bounded staleness consistency, Azure Cosmos DB documentation](https://learn.microsoft.com/en-us/azure/cosmos-db/consistency-levels),
  verified 2026-08-02). **Fix.** Use session consistency for a genuinely
  multi-write Geode fleet, and reserve bounded staleness for the
  single-write-region, many-read-region hybrid variant described in
  dimension 8, where the level's underlying assumption actually holds.
- **Symptom.** A multi-year effort to convert an existing, single-region
  production system into a Geode fleet repeatedly stalls or ships a design
  that quietly falls back to single-region behavior under load. **Cause.**
  The pattern's own guidance states directly that it "works for cloud-native
  development only, and can be difficult to retrofit"
  ([Geode pattern, When to use this pattern, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/geodes),
  verified 2026-08-02), and an existing system almost always carries
  assumptions, a single writable database connection string hardcoded deep
  in a library, a background job that assumes it is the only instance
  running, that a retrofit effort discovers only one at a time under
  production load. **Fix.** Treat the migration as an incremental
  replacement of specific capabilities using the Strangler Fig pattern (see
  `strangler-fig.md` in this catalog) rather than a single cutover, standing
  up new, genuinely cloud-native, geode-shaped services around the legacy
  core and migrating traffic capability by capability.
- **Symptom.** A single high-value user's session behaves inconsistently,
  the shopping cart looks different on two consecutive page loads, or a
  multi-step checkout appears to lose state partway through. **Cause.** The
  front-end routing layer routes per request or per connection, not per
  logical user session, so if session-relevant state is held only in one
  geode's local application memory rather than in the replicated data plane,
  a later request from the same user that lands at a different geode simply
  cannot see it. **Fix.** Keep every piece of session-relevant state in the
  geo-replicated backplane rather than in geode-local memory, or add explicit
  session affinity at the front-end routing layer, while testing that the
  affinity mechanism itself does not become a new single point of failure.
- **Symptom.** The cloud bill grows noticeably faster than user traffic does
  after a new geode is added to serve a comparatively small user population.
  **Cause.** Each geode is a standing deployment of both compute and
  provisioned data-plane capacity, and the source states this cost is
  incurred "not on a per transaction basis"
  ([Geode pattern, Issues and considerations, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/geodes),
  verified 2026-08-02), meaning a lightly used geode still carries close to
  the full fixed cost of a heavily used one. **Fix.** Prefer serverless
  compute for each geode's application tier where the platform supports it,
  and provision the data plane's throughput with autoscaling rather than a
  fixed reservation, both explicitly named in the source's own considerations
  as the mitigation for this exact cost pattern (same source).
- **Symptom.** On-call cannot determine which geode actually served a failing
  request, or cannot reconstruct the sequence of events across regions during
  an incident review. **Cause.** The pattern "implicitly decouples
  everything," and cross-geode interactions that happen asynchronously
  through the change feed have no inherent single trace connecting them (same
  source, Issues and considerations). **Fix.** Propagate a single correlation
  identifier through every hop of a logical request, including asynchronous
  change-feed-driven cross-geode messages, and centralize collection from
  every geode's front-end, compute, and data-plane diagnostics into one
  queryable observability store, discussed fully in dimension 16.
- **Symptom.** A team builds a hand-rolled leader-election or quorum
  mechanism across the geode fleet to coordinate writes, adding a new,
  independent point of failure that was never part of the original design.
  **Cause.** A misapplied mental model treating the geode fleet as a
  classical distributed cluster requiring its own consensus layer, when the
  source is explicit that "geodes aren't the same as clusters because they
  share a replication backplane, so the platform takes care of quorum
  issues"
  ([Geode pattern, Solution, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/geodes),
  verified 2026-08-02). **Fix.** Delegate all cross-geode write coordination
  and conflict handling to the replication backplane's own documented
  mechanism, and treat a proposal to add a second, application-level
  consensus layer on top of it as a signal that the team has not fully
  understood which problems the backplane already solves.

## 12. Trade-off matrix

| Force | Geode (canonical) | Geode, single-write hybrid | Deployment Stamps | Single shared region |
|---|---|---|---|---|
| Cross-region write latency | Lowest, every geode writes locally | High for the one write region, low for reads elsewhere | Not applicable, a stamp owns a bounded tenant set locally | Highest for distant users |
| Consistency model | Session or eventual only, strong unavailable with multi-write | Bounded staleness or strong achievable, one write region | Strongly consistent within a stamp's own store | Strongly consistent, single store |
| Fault isolation across regions | Every geode is a full peer, any can absorb failover instantly | Read geodes survive, but writes stop if the one write region fails | Full, a stamp's fault never reaches another stamp's tenants | None, one region is the whole system |
| Data residency and locality rules | Works against the pattern, every record can land anywhere | Better, but reads still replicate everywhere by default | Native, a routing decision pins a tenant to a region | Trivial, there is only one region |
| Operating cost at moderate scale | Highest, full compute and data cost per geode | Lower, read replicas are cheaper than full write capacity | High, one full stack per stamp | Lowest |
| Complexity to design and operate | Very high, conflict resolution plus tracing plus secrets sprawl | High, simpler consistency but still multi-region operations | High, but each stamp is individually simple | Low |
| Best fit when | Every region must both read and write locally, and multi-region loss must be survivable | Read volume is far higher than write volume and one home region for writes is acceptable | Tenants need hard isolation, region pinning, or version staggering | Product is small, early, or genuinely single-region |

The Deployment Stamps column describes this catalog's own sibling pattern
(see `deployment-stamps.md`), which partitions tenants across independent,
non-communicating stacks rather than replicating all data everywhere, and
which this same Azure catalog documents as Geode's direct structural
counterpart for exactly the case where not every region should be allowed to
hold every tenant's data.

## 13. Related and incompatible patterns

- **Deployment Stamps (this catalog, `deployment-stamps.md`).** The direct
  structural counterpart. where Geode replicates all data to every node so
  any node can answer any request, Deployment Stamps partitions tenants
  across independent stacks that never share data at all. Azure's own
  Deployment Stamps guidance names Geode directly as the pattern to reach
  for instead when a workload needs every instance to see every piece of
  data rather than a bounded tenant slice. A single fleet can combine both,
  most commonly by building the global traffic-routing layer itself as a
  Geode, so routing decisions are available from any region, while the
  tenant-serving stacks behind it remain Deployment Stamps.
- **Sharding (this catalog, `sharding.md`).** A narrower, single-tier
  relative. Sharding partitions a data store alone, commonly to solve a
  throughput or storage limit inside one region, while Geode replicates an
  entire application-plus-data stack across regions for latency and
  availability. The zone-sharded hybrid described in dimension 8 sits
  directly between the two, partitioning writes by geography the way
  sharding partitions by key, while still replicating reads the way a full
  Geode would.
- **Gateway Routing (this catalog, `gateway-routing.md`).** The mechanism
  that implements the front-end routing layer described in dimension 5,
  resolving a client's request to the nearest healthy geode. A Geode fleet's
  routing rules are a specialized case of gateway routing, keyed on
  geography and health rather than on URL path or header content.
- **Health Endpoint Monitoring (this catalog,
  `health-endpoint-monitoring.md`).** The mechanism that feeds the routing
  layer's failover decisions, detecting that a geode has become unhealthy so
  traffic stops landing there before users experience failed requests.
- **Materialized View (this catalog, `materialized-view.md`).** A close
  conceptual cousin at a smaller scale. a materialized view precomputes and
  stores a read-optimized projection of data local to where it is queried,
  which works the same way a read-only geode does for an entire
  region's worth of data in the single-write-region hybrid variant.
- **Circuit Breaker (this catalog, `circuit-breaker.md`).** A complementary
  pattern applied inside a single geode's own outbound calls, for example
  calls from a geode's compute tier to the replication backplane, so that a
  slow or failing backplane response does not spread into exhausting that
  geode's own request-handling capacity while it is still otherwise healthy.
- **Saga (this catalog, `saga.md`).** Relevant when a single logical business
  transaction must touch data that a Geode fleet's conflict resolution policy
  cannot safely arbitrate on its own, for example a multi-step operation
  with side effects outside the data plane. Saga's compensating-action
  discipline gives such an operation a defined way to unwind cleanly if a
  conflict or a partial failure leaves it inconsistent across geodes.

No pattern in this catalog is impossible, in its own construction, to combine with Geode,
so this entry's incompatible-with list in the frontmatter is empty, matching
the same reasoning this catalog's Deployment Stamps entry gives for its own
empty list. the real tension Geode creates is with consistency guarantees and
cost, not with any other named architectural pattern.

## 14. Refactoring path in and out

**Introducing Geode into a system that does not have it.** Start from
whatever the current deployment already is, most commonly a single region,
and confirm against dimension 4 that the workload genuinely needs
geo-distribution before doing anything else, since the source is explicit
this pattern only fits cloud-native systems with a real cross-region need. The
first concrete step is enabling multi-region reads on the data plane alone,
with writes still pinned to the original home region, which already delivers
a real latency win for distant readers without touching write
correctness at all. The second step stands up compute in a second region
reading from that same replica, still forwarding every write back to the one
home region, which is the single-write-region hybrid variant from dimension
8 and a legitimate, permanent stopping point for many teams. Only after
conflict handling, idempotent retries, and session-affinity behavior have
been proven under that hybrid, using the verification methods in dimension
15, does a team flip the data plane to accept writes in more than one region
and complete the move to the canonical, fully active-active form.

**Removing Geode from a system that has outgrown the need for it, or that
overbuilt it too early.** Reverse the same steps in order rather than tearing
the fleet down all at once. first disable multi-region writes, pinning writes
for each tenant or user back to one designated home region, which
immediately collapses the hardest correctness problem, cross-region write
conflicts, without requiring any application code change beyond the data
plane's own configuration. With writes single-region again, decommission the
now-redundant write capacity in the other geodes one at a time rather than
simultaneously, watching the region-skew observability signal from dimension
16 to confirm traffic has genuinely stopped depending on each geode before it
is removed, since DNS and routing caches can keep sending a trickle of
traffic to a decommissioned endpoint for longer than a team expects. Finally
collapse any remaining read-replica regions once telemetry confirms no
real read traffic still depends on them.

## 15. Testing and verification

- **Conflict resolution unit tests.** Test the chosen conflict resolution
  policy in isolation, feeding it two synthetic conflicting versions of the
  same record with controlled timestamps or custom conflict keys, and
  asserting the resolved winner matches the documented policy exactly,
  including the documented tie-break behavior for two writes that arrive
  with identical timestamps.
- **Forced-failover tests.** Under representative load, force one geode
  unhealthy at the routing layer, or kill it outright, and assert two things
  together. client-observed availability continues without an error spike,
  and any measured data loss stays within the recovery point objective the
  team accepted for the configured consistency level, rather than merely
  asserting that requests kept succeeding.
- **Multi-region propagation tests.** Write to one geode and poll a second
  geode until the write becomes visible there, asserting the observed
  propagation time stays inside whatever staleness bound the consistency
  configuration promises, so a silent regression in replication lag is
  caught before it reaches production users.
- **Idempotency and retry tests.** Because a network partition or a failover
  during a write can cause a client to retry an operation that may have
  already partially succeeded, test that every write handler produces the
  identical end state whether it runs once or is retried multiple times with
  the same idempotency key.
- **Per-geode load tests.** The source itself recommends this directly,
  advising a team to "load test the API architecture once deployed and
  contrast increasing the numbers of geodes with increasing the pricing
  tier" to find the most cost-efficient configuration for the workload's
  actual shape
  ([Geode pattern, Issues and considerations, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/geodes),
  verified 2026-08-02), rather than assuming more geodes is always the right
  mechanism to reach for more capacity.
- **Session-affinity end-to-end tests.** For any workload relying on
  session-level state, drive a simulated multi-request user session through
  the front-end routing layer under realistic network conditions and assert
  that the read-your-own-writes guarantee the application depends on
  actually holds across the session, not merely within a single request.
- **Multi-region loss game days.** Since the pattern's stated benefit is
  specifically surviving the concurrent loss of more than one region, a
  test that only ever removes a single geode never actually exercises the
  scenario the fleet was built to survive. schedule a periodic exercise that
  removes two or more geodes simultaneously and verifies the remaining
  fleet continues serving all traffic within its stated availability target.

## 16. Observability signals

- **Per-geode health and readiness.** The signal that directly feeds the
  front-end routing layer's failover decisions, and the mechanism this
  catalog's Health Endpoint Monitoring entry documents in full. a geode
  reporting unhealthy should stop receiving new traffic within one health
  check interval.
- **Cross-region replication lag.** Azure Cosmos DB exposes this directly in
  its own portal, letting an operator "monitor the replication latencies
  between various regions that are associated with your Azure Cosmos DB
  account" from the Metrics section's Consistency view
  ([Consistency levels, Write latency and Strong consistency, Azure Cosmos DB documentation](https://learn.microsoft.com/en-us/azure/cosmos-db/consistency-levels),
  verified 2026-08-02), and this per-region-pair lag is the single most
  direct measure of how stale a read from any given geode might be relative
  to the rest of the fleet at any moment.
- **Probabilistically Bounded Staleness.** For any consistency level weaker
  than strong, the platform-exposed PBS metric answers, in practice, how
  eventual the eventual consistency actually is, reporting the measured
  probability of getting a strongly consistent read for a given combination
  of write and read regions rather than only the theoretical worst case
  ([Consistency levels, Consistency guarantees in practice, Azure Cosmos DB documentation](https://learn.microsoft.com/en-us/azure/cosmos-db/consistency-levels),
  verified 2026-08-02).
- **Conflict rate per record type.** A rising conflict rate on a specific
  entity type is an early signal that either that entity type is being
  written by more than one geode more often than expected, or that a record
  logically owned by a single user or tenant needs session affinity or
  application-level partitioning that has not yet been added.
- **Request distribution versus expected population distribution.** A geode
  receiving noticeably more or less traffic than its region's user
  population would predict signals either a routing misconfiguration, or a
  neighboring geode having silently failed and dumped its traffic onto this
  one, either of which deserves investigation before it becomes an incident.
- **Write latency at the 50th and 99th percentile, per region.** For any
  configuration approaching strong consistency across regions, Cosmos DB's
  own documentation gives an exact formula worth alerting against, write
  latency is "equal to two times round-trip time between any of the two
  farthest regions, plus 10 milliseconds at the 99th percentile"
  (same source, Write latency and Strong consistency), a useful reference
  point even for teams running a weaker consistency level day to day, since
  it bounds what a temporary consistency escalation during an incident would
  cost.
- **Correlation-id coverage across the change feed.** Since the pattern's own
  guidance names full decoupling and the resulting tracing difficulty
  directly as a real cost, a dashboard tracking what fraction of cross-geode,
  change-feed-driven events carry a propagated correlation id is a leading
  indicator of whether an incident review will actually be able to
  reconstruct what happened.

## 17. Security and privacy implications

Judgement. this dimension draws heavily on the source's own stated
considerations, applied to general security practice, rather than on a single
independently sourced security audit of the pattern.

Every geode added to a fleet is a new, complete deployment footprint, and the
source is direct about the consequence. "distributed deployments have a
greater number of secrets and ingress points that require proper security
measures"
([Geode pattern, Issues and considerations, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/geodes),
verified 2026-08-02). The source's own recommended mitigation is centralizing
secret storage in a managed key vault service, and restricting each layer of
the architecture so the only externally reachable ingress point is the
front-end routing layer itself, with the data plane restricted to accept
traffic only from the compute tier and the compute tier restricted to accept
traffic only from the front end, enforced through identity-based access
controls or IP restriction rather than through obscurity alone (same source).

The pattern's core mechanism, every geode holding a full, writable copy of
every record, is itself a data residency and sovereignty risk when applied
without care, and this is exactly why dimension 4's non-applicability list
names data residency requirements as a reason to choose Deployment Stamps
instead. A team handling data subject to a jurisdictional locality
requirement, personal data under a regulation that restricts cross-border
transfer, most obviously, must either exclude that specific data category
from full geo-replication and route it through a region-pinned path instead,
or accept that a naive, fully replicated Geode design will place regulated
data outside its permitted jurisdiction the first time a write happens to
land at the wrong geode.

A compromised geode carries a larger blast radius in this pattern than in
Deployment Stamps, and this is worth stating plainly rather than leaving
implicit. because every geode is a fully writable peer, a credential
compromise at any single geode's compute tier can inject a malicious write
that the replication backplane then propagates, by design, to every other
geode in the fleet, whereas a compromised stamp in a Deployment Stamps
architecture stays contained to that one stamp's own tenants by construction. the
mitigation is strict, least-privilege, per-geode workload identity for the
data plane, and, wherever the data platform supports it, application-level
write validation ahead of the conflict resolution path rather than trusting
every accepted write implicitly.

Finally, session tokens used to deliver read-your-writes guarantees under
session consistency are themselves sensitive, transport-level artifacts, not
merely opaque cache keys. Cosmos DB's own documentation warns directly that
"if Session Tokens are being passed from one client instance to another, the
contents of the token shouldn't be modified"
([Consistency levels, Session consistency, Azure Cosmos DB documentation](https://learn.microsoft.com/en-us/azure/cosmos-db/consistency-levels),
verified 2026-08-02), which in practice means a session token deserves the
same transport protection, encryption in transit and exclusion from
application logs, that any other credential-adjacent piece of client state
would receive.

## 18. References

- [Geode pattern, Azure Architecture Center, Microsoft Learn](https://learn.microsoft.com/en-us/azure/architecture/patterns/geodes), verified 2026-08-02.
- [Deployment Stamps pattern, Azure Architecture Center, Microsoft Learn](https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp), verified 2026-08-02.
- [Consistency levels, Azure Cosmos DB documentation, Microsoft Learn](https://learn.microsoft.com/en-us/azure/cosmos-db/consistency-levels), verified 2026-08-02.
- [Conflict resolution policies, Azure Cosmos DB documentation, Microsoft Learn](https://learn.microsoft.com/en-us/azure/cosmos-db/conflict-resolution-policies), verified 2026-08-02.
- Ruslan Meshenberg, Naresh Gopalani, and Luke Kosewski, "Active-Active for Multi-Regional Resiliency", Netflix Technology Blog, 12 February 2013. [Article](https://netflixtechblog.com/active-active-for-multi-regional-resiliency-c47719f6685b), verified 2026-08-02.
- [Table Localities, CockroachDB documentation, Cockroach Labs](https://www.cockroachlabs.com/docs/stable/table-localities), verified 2026-08-02.
- [`apache/geode`, GitHub repository, Apache Software Foundation](https://github.com/apache/geode), verified 2026-08-02, cited only to distinguish the unrelated Apache Geode software project by the same name from the architectural pattern this entry documents.
- [Apache Geode homepage, geode.apache.org](https://geode.apache.org/), verified 2026-08-02, same purpose as the entry above.
