---
name: Cell-Based Architecture
slug: cell-based-architecture
family: 08-cloud-distributed
category: Resilience and Scale
aliases: [Cellular Architecture, Cells, Cell Router Pattern, Silo Architecture]
first_described: "AWS engineering practice, extending Nygard's Bulkhead metaphor, formalized in the AWS Well-Architected guide 'Reducing the Scope of Impact with Cell-Based Architecture'"
maturity: established
related: [bulkhead, deployment-stamps, sharding, circuit-breaker, health-endpoint-monitoring, rate-limiting, geode]
incompatible_with: []
verified: 2026-08-02
---

# Cell-Based Architecture

## 1. Name, aliases, and lineage

The canonical name used in this catalog is Cell-Based Architecture, matching
the title AWS gives its own guide, "Reducing the Scope of Impact with
Cell-Based Architecture"
([AWS Well-Architected Framework, Reducing the Scope of Impact with Cell-Based Architecture](https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/reducing-scope-of-impact-with-cell-based-architecture.html),
verified 2026-08-02). AWS also uses "Cellular Architecture" in adjacent
material, and that is the exact phrase Slack's engineering team chose for its
own migration, describing "Slack's Migration to a Cellular Architecture"
([Cooper Bethea, Slack Engineering, 22 August 2023](https://slack.engineering/slacks-migration-to-a-cellular-architecture/),
verified 2026-08-02). "Cells" alone is common shorthand once a team has
already established which flavor of cell it means.

This entry has to be honest about a naming collision that runs through this
catalog's own 08-cloud-distributed family, because the collision is real in
the industry, not an artifact of how this catalog is organized. Three entries
in this family describe closely related ideas under three different primary
names, and each treats the other two names as an alias of itself. The
Bulkhead entry in this catalog lists "Cell-Based Architecture" as one of its
own aliases, tracing to Michael T. Nygard, *Release It! Design and Deploy
Production-Ready Software*, Pragmatic Bookshelf, 2007, chapter 5, in the
stability patterns material. The Deployment Stamps entry lists "Cells" as one
of its aliases, tracing to the Azure Architecture Center's own opening
sentence, which calls a single deployed copy a stamp, "or sometimes a
service unit, scale unit, or cell"
([Deployment Stamps pattern, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp),
last updated 2026-06-03 per the page's own revision metadata, verified
2026-08-02). AWS's own cell-based architecture guide, in turn, opens its
definition by tracing the word cell straight back to Nygard's ship metaphor,
stating plainly that "a cell-based architecture comes from the concept of a
bulkhead in a ship, where vertical partition walls subdivide the ship's
interior into self-contained, watertight compartments"
([AWS Well-Architected, What is a cell-based architecture?](https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/what-is-a-cell-based-architecture.html),
verified 2026-08-02).

So all three names, Bulkhead, Deployment Stamps, and Cell-Based Architecture,
sit on the same lineage and the same core metaphor, and no single publication
holds an uncontested claim to be the one canonical source the way the Gang of
Four book is for Factory Method. This catalog resolves the collision by
splitting on operational granularity and primary intent, which is a judgment
call, stated here rather than dressed as settled fact. Bulkhead names the
technique of partitioning a shared resource pool inside one running process
or one service instance, most often thread pools or connection pools per
downstream dependency, so a slow dependency cannot starve every caller.
Deployment Stamps names Azure's framing of a fully independent, horizontally
replicated copy of an entire application stack, including its data store,
built primarily to solve per-tenant scaling and per-tenant version isolation
in a SaaS product, with fault isolation as a secondary benefit that the Azure
page calls out under "achieve resiliency during outages." Cell-Based
Architecture, as this entry treats it, names the same shape of full,
independent, replicated stack, but with the primary stated goal being
containment of the scope of impact of a failure, a router layer treated as
its own first-class, separately-hardened component, and an explicit
vocabulary for partition keys, cell capacity limits, and phased cell-by-cell
deployment that AWS has documented in more operational depth than either of
the other two sources. A reader who has already implemented Deployment Stamps
or Bulkhead has implemented most of the mechanics this entry describes. What
this entry adds is the AWS-specific vocabulary, the router-as-hardened-layer
discipline, and the blast radius math that AWS's guide works through
explicitly.

The earliest concrete, dated, named production system this entry could verify
under the specific words "cell-based architecture" is Amazon Elastic Block
Store's Physalia control-plane database, presented at USENIX NSDI in 2020 as
"Physalia, Millions of Tiny Databases," and separately recorded in an AWS
conference-talk title as "Physalia, Cell-based Architecture to Provide Higher
Availability on Amazon EBS"
([Marc Brooker et al., Millions of Tiny Databases, NSDI '20](https://www.usenix.org/conference/nsdi20/presentation/brooker);
video title verified via the AWS Prescriptive Guidance cell-router pattern's
own reference link at
[docs.aws.amazon.com/prescriptive-guidance/latest/patterns/serverless-cell-router-architecture.html](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/serverless-cell-router-architecture.html),
both verified 2026-08-02). The written AWS Well-Architected guide this entry
cites throughout carries no publish date visible in its own body text, so
this entry does not assert one.

## 2. Problem and context

A service starts as one deployed thing. One database, one fleet of
application servers, one code path that every request runs through. That
shape is easy to reason about and easy to operate, and it works exactly until
it fails, because it fails for everyone at once. A bad deployment, a
corrupted request that trips a code path nobody tested, a single overloaded
tenant, or an unlucky dependency timeout does not stay contained to the
request that caused it. It takes down the shared process, the shared
connection pool, or the shared database, and every other request in flight
pays for it. AWS's own guide names this directly. In a typical single-image
service, "this application would be serving requests from 100% of clients. In
the event of a failure, or a change in the application, 100% of customers
would be impacted"
([AWS Well-Architected, What is a cell-based architecture?](https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/what-is-a-cell-based-architecture.html),
verified 2026-08-02).

Region and Availability Zone redundancy do not solve this on their own. A
service can run identical, healthy copies in three Availability Zones and
still have every one of those copies be the same single shared-fate instance
of the application, so a bad code deploy rolled out to "the service" lands in
all three zones at once. The problem this pattern addresses sits one layer
below infrastructure redundancy. It is about splitting the workload itself,
not just its physical hosting, into pieces small enough that a failure in one
piece cannot reach the others, no matter what caused the failure. This
context matters most for services that are already past the point where a
maintenance window and a single rollback plan are acceptable, meaning
services with a large, heterogeneous customer base where a single noisy
tenant, a single malformed payload, or a single regional regulatory
requirement should never be allowed to become everyone's problem at once.
Payment processors, communication platforms, and any control plane that many
independent customers depend on concurrently are the recurring context in the
production examples this entry cites in section 9.

## 3. Forces

**Blast radius versus infrastructure cost.** Splitting one service into ten
independent replicas of everything, from load balancer to database, multiplies
the fixed cost of running the service. AWS's own guide is careful to push back
on the assumption that this multiplication is mandatory. "Building a
cell-based architecture doesn't necessarily mean having to double, triple, or
more your application's infrastructure. It might be that your application has
30 hosts, and in a cell-based architecture it has the same 30 hosts, but with
a cell router and with tasks that are distributed or grouped between cells"
(same source as above, verified 2026-08-02). The force is real but not fixed.
The actual multiplier depends on how much per-cell baseline overhead, idle
capacity, redundant control-plane components, and monitoring, each cell
carries.

**Scale-out versus scale-up.** A single, ever-growing instance eventually hits
a hard resource ceiling, whether that is a database connection limit, an
account-level service quota, or simple non-linear cost growth past a certain
size. Cells trade that ceiling for the very different problem of coordinating
many small, capped-size instances, which is harder to build but does not
degrade as the ceiling approaches.

**Testability of the whole versus testability of the part.** A workload
without an upper size bound is, in AWS's phrase, too big to test, because
simulating a full-scale failure against a system with no ceiling is
impractical for cost reasons. A cell has a known maximum size by
construction, so it "can be stress tested and pushed past their breaking
point to understand their safe operating margin" (same source, verified
2026-08-02). This is a genuine force in favor of cells, not a side effect.

**Cross-cell consistency versus isolation.** The more two cells need to agree
on anything, a global uniqueness constraint, a cross-tenant report, a shared
rate limit, the more the architecture is forced to reintroduce shared state
across the cell boundary, which is exactly what erodes the isolation the
pattern exists to buy. AWS's cell design guidance states the ideal directly
and then immediately concedes the ideal is not always reachable. "In an ideal
world, a cell is independent, is unaware of other cells, and does not share
its state with other cells... However, depending on your workload, it is not
always possible to maintain these characteristics"
([AWS Well-Architected, Cell design](https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/cell-design.html),
verified 2026-08-02).

**Operability of many versus operability of one.** One instance of a service
is one thing to deploy, patch, and page on. A hundred cells are a hundred
things, unless the tooling that provisions, deploys, and monitors them is
built as a first-class product from the start. AWS is explicit that this
force is not optional to plan for. "To avoid problems, it is essential to
have an automated CI/CD pipeline from the beginning"
([AWS Well-Architected, Cell deployment](https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/cell-deployment.html),
verified 2026-08-02).

**Latency and correctness of the extra hop.** Every request now needs to
learn which cell owns it before it can be served, which is either an extra
network hop through a router, or a client-side cache that has to be kept
correct as tenants move between cells. Getting the routing decision wrong,
even briefly, sends a request to a cell that does not hold the data it needs.

The pattern favors blast radius reduction, testability, and horizontal
scalability, and it deliberately sacrifices infrastructure cost efficiency,
architectural simplicity, and cross-cell consistency to get them. A team
adopting this pattern is choosing to pay a real, ongoing operational tax for
a bound on how bad the worst day can get.

## 4. Applicability and non-applicability

**Reach for cell-based architecture when.**

- The customer base is large and heterogeneous enough that a single tenant's
  traffic pattern, data shape, or misuse of the API should never be able to
  degrade another tenant's experience.
- The service already has, or is approaching, a scale where a bad deployment
  or a poison-pill request is a recurring category of incident, not a
  one-time event.
- The organization can build or adopt real automation for cell
  provisioning, deployment, and monitoring before the cell count grows past
  what a person can operate by hand. AWS names this explicitly as a
  prerequisite, not an afterthought, for cell deployment.
- Data residency or regulatory boundaries already require splitting
  customers by geography or market, which gives a natural, low-friction
  partition key for cells. American Express partitions by market for exactly
  this reason, covered in section 9.
- The team can tolerate, and can build tooling around, a workload that is
  genuinely a control plane and a data plane split into two lifecycles, a
  thin, highly available routing layer and many independently deployed
  cells behind it.

**Do NOT reach for cell-based architecture when.**

- The service is small enough, or young enough, that a single incident
  affecting all customers is an acceptable, recoverable cost. The AWS guide's
  own worked comparison assumes a service already worth this investment. A
  five-person startup's first product usually is not.
- The workload has hard cross-tenant consistency requirements that cannot be
  pushed to an asynchronous, out-of-band process, for example a single global
  ledger that must serialize every write across all customers. Forcing that
  workload into isolated cells recreates cross-cell coupling and destroys the
  isolation the pattern is meant to buy.
- The organization cannot commit to automating cell lifecycle management.
  Manually operating even five cells with five sets of dashboards, five
  deployment pipelines, and five capacity limits is worse than operating one
  well-tested instance, because it multiplies toil without multiplying
  safety.
- The natural partition key for the workload does not exist or is unstable.
  If requests cannot be cleanly and durably assigned to one partition, no
  tenant ID, no natural geography, a workload that is inherently
  cross-cutting, a cell router has nothing reliable to route on.
- A simpler, narrower pattern already solves the actual problem. If the real
  issue is one flaky downstream dependency exhausting a shared thread pool,
  Bulkhead in its narrower, in-process sense is the correct, much cheaper
  fix, and reaching for full cell-based architecture is solving a
  one-dependency problem with a whole-service redesign.

## 5. Structure

A cell-based architecture has four participants, described here using AWS's
own names for them where AWS names them, since the terms are not
interchangeable with generic microservices vocabulary.

- **Cell.** A complete, independently operable instance of the workload,
  including everything the workload needs to serve its own subset of
  requests, application servers, its own data store, its own queues, its own
  supporting services. AWS defines it plainly. "A cell is an instance of your
  complete workload, with everything needed to operate independently"
  ([AWS Well-Architected, Cell design](https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/cell-design.html),
  verified 2026-08-02). A cell has a fixed, tested, known maximum capacity.
- **Cell router (routing layer).** The single entry point clients see. Its
  only job is mapping an incoming request to the right cell using a
  partition key and returning or forwarding to that cell's endpoint. AWS
  calls it "the thinnest possible layer, with the responsibility of routing
  requests to the right cell, and only that" (same source). Because the
  router is shared across every cell, it is deliberately built to fail
  differently and less often than the cells it serves. AWS's serverless
  cell-router reference pattern uses client-side caching of the routing
  decision specifically so that "the intentional decoupling enables
  uninterrupted operations for existing users in the event of cell-router
  downtime"
  ([AWS Prescriptive Guidance, Set up a serverless cell router for a cell-based architecture, Mian Tariq and Ioannis Lioupras](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/serverless-cell-router-architecture.html),
  verified 2026-08-02).
- **Partition key.** The value used to decide which cell owns a given
  request. AWS's guidance says the key "needs to align with the grain of
  the service, or the natural way that a service's workload can be
  subdivided with minimal cross-cell interactions," and gives customer ID
  and resource ID as typical examples (same source as the cell router
  definition above, "What is a cell-based architecture?" page).
- **Control plane (provision and deploy layer).** The separate set of
  components responsible for creating cells, retiring cells, deploying code
  to cells in phased waves, and moving tenants between cells when
  rebalancing. AWS's reference architecture names this the vending
  machine and rebalancer role, kept operationally distinct from the data
  path so that a control-plane failure does not take down cells that are
  already running
  ([AWS Solutions Library, Guidance for Cell-Based Architecture on AWS](https://docs.aws.amazon.com/solutions/cell-based-architecture-on-aws/),
  verified 2026-08-02).

## 6. ASCII structure diagram

```
                              CLIENTS
                                 |
                                 v
                 +----------------------------------+
                 |         CELL ROUTER               |
                 |  (thinnest possible layer)         |
                 |  - looks up partition key -> cell  |
                 |  - hardened, highly available       |
                 |  - clients cache the result (TTL)  |
                 +----------------------------------+
                     |            |             |
        partition key A   partition key B   partition key C
                     |            |             |
                     v            v             v
           +-----------+  +-----------+  +-----------+
           |  CELL 1   |  |  CELL 2   |  |  CELL 3   |
           | app + DB  |  | app + DB  |  | app + DB  |
           | fixed cap |  | fixed cap |  | fixed cap |
           +-----------+  +-----------+  +-----------+
                 ^              ^              ^
                 |              |              |
                 +--------------+--------------+
                                |
                     +----------------------+
                     |    CONTROL PLANE      |
                     | - provision cells      |
                     | - deploy in waves      |
                     | - move tenants between |
                     |   cells (rebalancer)   |
                     +----------------------+

Cells share nothing with each other at runtime. Only the control
plane touches more than one cell, and only for administration.
```

## 7. Dynamics

Two distinct flows matter for a cell-based architecture, the steady-state
request path, and the failure path that is the entire point of the pattern.

In the steady-state path, a new client first contacts the cell router, which
looks up the client's partition key against its routing table and returns the
assigned cell's endpoint. AWS's serverless cell-router pattern makes an
explicit design choice here that is worth naming, routing is static rather
than proxied, meaning "the client caches the endpoints at the initial login
and subsequently establishes direct communication with the cell," with only
periodic check-ins back to the router to confirm the assignment is still
valid
([AWS Prescriptive Guidance, Set up a serverless cell router for a cell-based architecture](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/serverless-cell-router-architecture.html),
verified 2026-08-02). This choice trades a little staleness risk, a client
might briefly hold a stale cell endpoint after a migration, for removing the
router from the request path of every single call, which is the mechanism
that keeps the router's own availability requirement from becoming the
system's new single point of failure.

In the failure path, a defect, an overloaded dependency, or a bad deployment
inside one cell degrades or crashes that cell only. Every client whose
partition key routes elsewhere is unaffected, because their request never
touches the failed cell's process, database connections, or in-memory state.
AWS quantifies this directly. "If a workload uses 10 cells to service 100
requests, when a failure occurs in one cell, 90% of the overall requests
would be unaffected by the failure"
([AWS Well-Architected, What is a cell-based architecture?](https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/what-is-a-cell-based-architecture.html),
verified 2026-08-02). The same containment applies to a rollout. AWS's
deployment guidance has the control plane push a new version to one canary
cell first, watch it, and only then wave the deployment across the remaining
cells, so that "the benefits of fault isolation and blast radius reduction
with cell-based architecture are not only when processing customer traffic,
but also when deploying new features and fixing bugs"
([AWS Well-Architected, Cell deployment](https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/cell-deployment.html),
verified 2026-08-02).

```
STEADY STATE

  client --lookup--> [ROUTER] --cell endpoint--> client
  client --------------- direct traffic -----------> [CELL 2]
  (router is off the hot path after the initial lookup)

FAILURE IN ONE CELL

  [CELL 1]  X  <-- bad deploy / overload / poison pill
  [CELL 2]  ok        clients on cell 2, unaffected
  [CELL 3]  ok        clients on cell 3, unaffected
     |
     v
  control plane marks CELL 1 unhealthy, halts its
  deployment wave, alerts on-call for CELL 1 only

WAVE DEPLOYMENT

  step 1, deploy to CANARY CELL only, observe
  step 2, deploy to next 10% of cells, observe
  step 3, continue in waves. A bad wave stops and
          rolls back before it reaches the rest
```

## 8. Implementation variants

**Tenant or market as the partition key, with static or regional cells.**
American Express partitions payment traffic by attributes like "partner,
market, or payment type," and each cell is fully self-contained within a
single region, including "DNS, databases, microservices, and supporting
services"
([americanexpress.io, Cell-Based Architecture for Resilient Payment Systems, Benjamin Cane, Distinguished Engineer, 11 June 2026](https://americanexpress.io/cell-based-architecture-for-resilient-payment-systems/),
verified 2026-08-02). Their Global Transaction Router performs deterministic
routing, sending a transaction "to the cell where the right data is already
available" (same source), which is the payments-specific instance of the
partition-key discipline described in section 5.

**Availability Zone as the partition key.** Slack's implementation is a
useful contrast because its partition key is not the customer at all, it is
the physical Availability Zone the request happens to land in. "All services
are present in all AZs, but each service only communicates with services
within its AZ," so a network problem confined to one AZ is contained without
Slack needing to know or care which customer sent which request
([Slack Engineering, Slack's Migration to a Cellular Architecture, Cooper Bethea, Senior Staff Engineer, 22 August 2023](https://slack.engineering/slacks-migration-to-a-cellular-architecture/),
verified 2026-08-02). Slack built this on top of the Envoy and xDS ecosystem,
using an internal control plane called Rotor to manage weighted traffic
between zones, driven by a migration that took roughly one and a half years
and was triggered by a June 2021 outage caused by a single-AZ network
disruption (same source). This variant shows the pattern applied to an
infrastructure-level partition key rather than a business-level one, and it
is the cheapest variant to retrofit onto an existing service, since it does
not require re-architecting how tenants map to data.

**Kubernetes-cluster-per-cell.** DoorDash's "Supercell" implementation makes
the cell boundary a Kubernetes cluster boundary. "Each cell consists of
multiple Kubernetes clusters, and each microservice is deployed exclusively
to one cluster"
([InfoQ, DoorDash Uses Service Mesh and Cell-Based Architecture, Eran Stiller, 23 January 2024, reporting on DoorDash's own engineering blog](https://www.infoq.com/news/2024/01/doordash-service-mesh/),
verified 2026-08-02). This variant treats the cluster itself as the fault
isolation boundary and layers a custom Envoy-based service mesh over the
clusters to control cross-cell traffic, which is a heavier operational
investment than Slack's AZ-based split but gives finer control over which
specific service gets isolated first.

**Shuffle sharding, a lighter-weight relative.** Where a full cell holds a
fixed, disjoint slice of infrastructure, shuffle sharding assigns each
customer a virtual shard made of a random, potentially overlapping subset
of a shared worker pool. Colm MacCárthaigh, describing the technique AWS
Route 53 uses, shows the arithmetic. With 8 workers and shards of 2 workers
each, ordinary partitioning gives only 4 non-overlapping shards, but shuffle
sharding "the shards contain two random instances, and the shards... may have
some overlap," producing 56 possible distinct shard combinations from the
same 8 workers
([AWS Architecture Blog, Shuffle Sharding, Massive and Magical Fault Isolation, Colm MacCárthaigh, 14 April 2014](https://aws.amazon.com/blogs/architecture/shuffle-sharding-massive-and-magical-fault-isolation/),
verified 2026-08-02). Judgment call, stated as such rather than sourced fact.
This entry treats shuffle sharding as a related but distinct technique, not a
variant of cell-based architecture itself, because it isolates customers
probabilistically within one shared pool of workers rather than physically
across disjoint replicas of a whole stack. The two techniques are frequently
deployed together, a shuffle-sharded worker pool inside one cell, but the
cited article does not itself use the words cell-based architecture, so this
entry does not claim they are formally the same pattern.

**Extremely small cells, one per logical object.** Amazon EBS's Physalia
control-plane database sits at the far end of the cell-size spectrum from
American Express's market-level cells. Instead of a small number of large
cells, Physalia deploys what its own paper title calls "millions of tiny
databases," each one scoped tightly enough that it "focuses on being
extremely available for only the keys it knows each client needs, from the
perspective of that client," using knowledge of data center topology to place
each tiny partition where it is most likely to stay reachable even during an
Availability Zone impairment
([Marc Brooker, personal summary of Millions of Tiny Databases, NSDI '20](https://www.brooker.co.za/blog/2020/02/17/physalia.html),
verified 2026-08-02). AWS itself frames this system under the cell-based
architecture name in a conference-talk title, "Physalia, Cell-based
Architecture to Provide Higher Availability on Amazon EBS," referenced
directly from AWS's own cell-router pattern documentation cited in section 9.
This variant is the useful reminder that cell does not imply any particular
size. It implies only that each unit is small enough, and isolated enough, to
fail alone.

## 9. Known production uses

- **Slack** migrated its most critical user-facing services from a single
  shared architecture to AZ-partitioned cells over roughly one and a half
  years, driven by a June 2021 outage, using Envoy, xDS, an internal control
  plane named Rotor, and a Vitess-backed datastore with strongly consistent
  semantics for coordination
  ([Slack Engineering, Slack's Migration to a Cellular Architecture, Cooper Bethea, 22 August 2023](https://slack.engineering/slacks-migration-to-a-cellular-architecture/),
  verified 2026-08-02).
- **American Express** runs its payment-processing platform on cells
  partitioned by market and payment type, with a Global Transaction Router
  performing deterministic routing and a design that reroutes and restarts a
  transaction in a healthy cell rather than resuming it across cells if its
  original cell fails
  ([americanexpress.io, Cell-Based Architecture for Resilient Payment Systems, Benjamin Cane, 11 June 2026](https://americanexpress.io/cell-based-architecture-for-resilient-payment-systems/),
  verified 2026-08-02).
- **DoorDash's Supercell** project deploys each microservice exclusively
  into one Kubernetes cluster per cell, layered with a custom Envoy and xDS
  service mesh, and the resulting cost optimization was substantial enough
  that DoorDash reports its cloud provider reached out asking whether it was
  experiencing a production-related incident, which was simply the
  traffic-pattern change from the migration
  ([InfoQ, DoorDash Uses Service Mesh and Cell-Based Architecture, Eran Stiller, 23 January 2024](https://www.infoq.com/news/2024/01/doordash-service-mesh/),
  verified 2026-08-02).
- **Amazon EBS's Physalia** control-plane database is the cited academic
  reference implementation at the small-cell end of the spectrum, presented
  at USENIX NSDI 2020 and separately framed by AWS under the cell-based
  architecture name in an AWS re Invent talk title
  ([Marc Brooker et al., Millions of Tiny Databases, NSDI '20, USENIX](https://www.usenix.org/conference/nsdi20/presentation/brooker),
  verified 2026-08-02).
- **AWS's own reference implementation** in its Solutions Library publishes
  concrete, sourced default numbers worth recording because they are the
  kind of detail that gets invented rather than looked up. Its example
  cell-router `Scaler` function caps each cell at 500 users maximum, reserves
  a 20 percent buffer capacity so a cell is treated as full at 400 assigned
  users, and triggers the request to provision a new cell once an existing
  cell reaches 70 percent of its capacity
  ([AWS Prescriptive Guidance, Set up a serverless cell router for a cell-based architecture](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/serverless-cell-router-architecture.html),
  verified 2026-08-02). AWS explicitly labels these as illustrative defaults
  for its demonstration pattern, not a universal rule, and this entry repeats
  that caveat rather than presenting the numbers as a fact about how every
  cell-based system must be tuned.

## 10. Consequences

**Positive.**

- A failure in one cell affects only that cell's traffic share, giving the
  same order-of-magnitude blast-radius reduction as a multi-Region failure,
  without needing a full multi-Region deployment.
- Each cell has a known, testable maximum size, so load and chaos testing
  can push a cell past its real breaking point at a cost that scales with
  one cell, not with the whole customer base.
- New capacity is added by creating another cell rather than by growing an
  existing component past its tested limits, which caps the risk of hitting
  an unknown non-linear scaling wall.
- Deployments and rollbacks can be staged cell by cell, so a bad release is
  caught and rolled back after touching a small, known slice of traffic
  instead of everyone at once.
- AWS's reasoning about mean time between failures applies. Splitting `n`
  cells means `n` times as many possible failure events, but each event now
  affects only `1/n` of the traffic, and the resulting higher testability and
  faster, more predictable recovery per cell tends to raise overall
  availability rather than lower it.

**Negative.**

- Running many independent copies of a stack, even at a fixed total host
  count, adds real coordination and per-unit overhead. Monitoring,
  provisioning, and deployment tooling all have to work correctly across
  every cell, not just once.
- The choice of partition key becomes a load-bearing, hard-to-change
  architectural decision made early. A wrong or unstable key forces painful
  tenant migrations later.
- Cross-cell functionality, anything that legitimately needs to see or act
  across tenants at once, has to be built as an explicit, separate,
  asynchronous system rather than a simple query, adding real engineering
  cost for a small number of features.
- The router, however thin, is still a shared component. If it is not
  deliberately built to fail independently of the cells, through static,
  cached routing or an equally resilient design, it can reintroduce the
  single point of failure the whole architecture exists to remove.
- Migrating an existing tenant, or a large existing customer, from one cell
  to another is operationally hard, and most teams end up needing to build a
  dedicated rebalancer service rather than treating migration as a one-off
  script.

## 11. Failure modes and misuse

**Symptom.** The whole system goes down even though it has ten cells.
**Cause.** The cell router itself was built as an ordinary, single-instance
proxy sitting in the hot path of every request, so when the router process
or its dependency (commonly its own routing database) fails, every cell
becomes unreachable even though every cell is individually healthy.
**Fix.** Follow AWS's own router design constraint and keep the router "as
simplistic and horizontally scalable... as possible," and prefer static,
client-cached routing over a router that must be consulted on every single
request, so a router outage degrades only new client onboarding rather than
existing traffic
([AWS Prescriptive Guidance, Set up a serverless cell router for a cell-based architecture](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/serverless-cell-router-architecture.html),
verified 2026-08-02).

**Symptom.** A failure that should have stayed in one cell shows up in
several. **Cause.** A shared resource crept back across the cell boundary
over time, most commonly a shared database, a shared message queue, or a
shared downstream service that was never split. AWS's cell design guidance
names this directly as the risk to watch for. "Cross-cell dependencies can
quickly eliminate the benefits of a cellular architecture, so try to do this
as little as possible"
([AWS Well-Architected, Cell design](https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/cell-design.html),
verified 2026-08-02). **Fix.** Audit for cross-cell calls as a standing
practice, and where a shared component genuinely cannot be split, isolate it
under its own separate resilience pattern rather than letting it silently
reconnect every cell.

**Symptom.** One or two large tenants degrade an entire cell, even though
the tenant-to-cell mapping is correct. **Cause.** Cell-based architecture
isolates tenants from other cells, but it does nothing by itself to isolate
one noisy tenant from the other tenants who share its own cell. A single
oversized customer placed into a cell sized for many small customers can
still exhaust that cell's shared capacity. **Fix.** Give large tenants their
own dedicated cell, or cap the number and size of tenants a cell's
`Dispatcher` or equivalent assignment function will place together, the same
capacity discipline AWS's example `Scaler` function applies at the 500-user,
70-percent-trigger level cited in section 9.

**Symptom.** Cell count keeps growing and nobody can move a tenant out of an
overloaded cell. **Cause.** The control plane was built to provision new
cells but never built a working rebalancer, so tenant placement is
effectively permanent from the moment of first assignment. **Fix.** Build
tenant migration as a first-class, tested operation from the start, matching
AWS's reference design, which keeps an explicit rebalancer role that "can
move users between cells, and also create new cells as needed. After a
successful move, it updates the user-to-cell assignment"
([AWS Solutions Library, Guidance for Cell-Based Architecture on AWS](https://docs.aws.amazon.com/solutions/cell-based-architecture-on-aws/),
verified 2026-08-02).

**Symptom.** On-call cannot tell whether the system is healthy, only whether
individual cells are healthy. **Cause.** Monitoring was built per cell and
never rolled up, so a slow, systemic problem that is degrading every cell by
a small amount, rather than crashing one cell outright, is invisible until it
is already an incident. **Fix.** Build an aggregate view alongside the
per-cell dashboards from the start. AWS's reference architecture streams
changes from every cell into a central data lake queryable through Amazon
Athena and keeps "a central dashboard which contains aggregated information
(such as number of cells with and without errors)" precisely to close this
gap (same source as above).

## 12. Trade-off matrix

| Force | Cell-Based Architecture | Bulkhead (Nygard, in-process) | Deployment Stamps (Azure) | Plain Sharding | Active-active multi-Region |
|---|---|---|---|---|---|
| Primary intent | Blast radius reduction for a whole service | Isolate one resource pool inside one process | Per-tenant scale unit and version isolation | Distribute data, not necessarily fault domains | Regional disaster recovery |
| Unit of isolation | A complete stack replica (cell) | A thread or connection pool | A complete stack replica (stamp) | A data partition only | A whole Region |
| Router as a distinct hardened layer | Yes, explicit, first class | No, decision is local to the process | Sometimes, less emphasized than in AWS's framing | No, usually a data-tier concern | DNS or global load balancer |
| Infrastructure cost multiplier | Moderate to high, tunable by cell size | Low, same process, just partitioned pools | Moderate to high, similar to cells | Low relative to compute-heavy patterns | High, full duplicate Region |
| Handles a noisy neighbor within the same unit | No, by itself | Yes, that is its exact purpose | No, by itself | No, by itself | No, by itself |
| Typical granularity | Coarse to fine, tenant, market, or AZ | Very fine, per dependency | Coarse, per tenant or tenant group | Fine, per data key | Coarsest, per Region |
| Cross-unit consistency cost | High if required, pushed out-of-band | Not applicable, single process | High if required, same as cells | Moderate, common for sharded databases | Highest, cross-Region replication lag |

## 13. Related and incompatible patterns

**Bulkhead** is the narrower, in-process ancestor of this pattern's own
metaphor, and the two compose rather than compete. A well-built cell almost
always uses Bulkhead internally to isolate its own connection pools from a
noisy downstream dependency, which is exactly the gap noted in section 11
where cell-based architecture alone does not protect a cell from a single
oversized tenant sharing that cell.

**Deployment Stamps** is, as established in section 1, close enough to be the
same underlying mechanism described from Azure's perspective, with the
emphasis shifted from fault isolation toward per-tenant scaling and version
isolation. A team already running Deployment Stamps has already built most of
what this entry describes. The added value of reading this entry is the
AWS-specific router-hardening and blast-radius vocabulary.

**Sharding** solves a narrower problem, distributing data across multiple
stores for scale, without necessarily replicating the application layer or
providing fault containment. A cell typically contains its own shard of data
internally, so sharding is a component a cell uses, not a substitute for the
cell boundary itself.

**Circuit Breaker** and **Rate Limiting** are companions that a cell needs
internally and at its router. The router benefits from rate limiting to
protect itself from being overwhelmed, and each cell benefits from circuit
breakers on its own downstream calls so a struggling dependency degrades that
one cell gracefully rather than exhausting it entirely.

**Health Endpoint Monitoring** is the mechanism a cell router or control
plane uses to decide a cell is unhealthy in the first place, feeding directly
into the failure path described in section 7.

**Geode** is worth naming as the pattern this entry is not. Geode
replicates the same data and full read and write capability into every
region so any region can serve any request, which is the opposite tradeoff
from a cell, where each partition of the workload is served by exactly one
owning cell. A system can combine the two, as the Azure Deployment Stamps
documentation notes when it describes a traffic-routing layer that is itself
built as a Geode sitting in front of a set of Stamps, but the two patterns
solve different problems and should not be treated as interchangeable.

No pattern in this catalog is flagged as formally incompatible with
cell-based architecture. The closest thing to a genuine conflict is
attempting to combine cells with a design that requires strong, synchronous
consistency across the entire customer base, which section 4's
non-applicability list already rules out as a case where this pattern is the
wrong tool.

## 14. Refactoring path in and out

**Introducing cells into an existing single-instance service.**

1. Pick the partition key first, and pick it for durability, not
   convenience. Customer ID, tenant ID, market, or Availability Zone are the
   recurring choices in section 9's production examples. Whichever is chosen,
   confirm it aligns with the natural grain of the workload the way AWS's
   guidance describes, because migrating tenants across a mis-chosen key
   later is the single most expensive mistake to walk back.
2. Extract and harden the routing decision behind a dedicated, thin
   component before splitting anything else. At this stage the router can
   still send every request to the single existing instance. The goal is to
   prove the router itself can be operated reliably and independently before
   it becomes load bearing.
3. Stand up a second, fully independent instance of the stack as a real cell,
   and move a small, low-risk slice of traffic to it using the partition
   key, following the phased, wave-by-wave deployment discipline described in
   section 7.
4. Build the control-plane operations, provisioning a cell, deploying to a
   canary cell first, and moving a tenant between cells, as real, tested
   automation before growing past two or three cells. AWS's guidance treats
   this tooling as a precondition, not a later optimization.
5. Grow the cell count as capacity requires, using the fixed, tested
   per-cell capacity limit (see the concrete numbers cited in section 9) to
   decide when to provision the next cell rather than growing any single
   cell past its tested ceiling.

**Removing cells once they stop earning their place.** A cell-based
architecture is worth reversing when the customer base or traffic pattern
that justified splitting the workload has shrunk, or when the operational
tax of running many cells is consistently exceeding the incidents it
prevents. The safe path out mirrors the path in. Consolidate cells gradually,
migrating tenants from the smallest or least-loaded cells into remaining
cells using the same rebalancer built during adoption, watching blast-radius
math shift as the cell count drops, rather than collapsing directly back to
one shared instance in a single cutover, which reintroduces the very
single-point-of-failure risk the migration in was meant to remove.

## 15. Testing and verification

Cell-based architecture changes what is easy and what is hard to test
compared to a single monolithic instance. It is easier to run a genuine,
full-scale load test, because a cell has a known, capped maximum size. AWS's
own reasoning is that it is "impractical for cost reasons for large-scale
services to regularly simulate the entire workload of all their tenants, but
it is reasonable to simulate the largest workload that can fit into a cell"
([AWS Well-Architected, Why use a cell-based architecture?](https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/why-to-use-a-cell-based-architecture.html),
verified 2026-08-02). That gives testing teams a genuinely achievable target,
push one cell to its documented breaking point, rather than an untestable
moving target of "the whole system under peak load."

It becomes harder to test the properties that only emerge from the router
and the control plane. The router's routing decision has to be tested for
correctness under partition-key edge cases, a brand-new tenant with no
assignment yet, a tenant mid-migration between cells, a request with a
malformed or missing partition key. Chaos testing gains a new, valuable
target. Deliberately failing one cell in a staging environment and verifying
that the blast-radius math actually holds, meaning traffic for other cells is
genuinely unaffected and the router correctly stops sending new assignments
to the failed cell. The canary-cell deployment discipline described in
section 7 is itself a form of continuous production testing, and its
correctness depends on the control plane's ability to detect a bad wave and
halt before it reaches the remaining cells, which is worth its own explicit
integration test rather than being assumed to work.

Test doubles for this pattern typically take the shape of a fake or
in-memory cell router with a controllable routing table, so that
application-layer tests for a single cell's business logic never need a real
multi-cell environment running, and a separate, smaller suite of
router-and-control-plane tests exercises assignment, capacity thresholds, and
rebalancing logic in isolation from any real cell's application code. The
worked TypeScript, Python, and Go examples in the code examples section at
the end of this entry are exactly this shape, an in-memory router whose
behavior (least-loaded assignment, capacity thresholds, unhealthy-cell
rejection, and blast-radius math) can be exercised without any real network
or database.

## 16. Observability signals

A healthy cell-based system needs two layers of observability that a
single-instance service does not, per-cell signals, and an aggregate rollup
across all cells, because neither layer alone answers the question an
operator actually needs answered during an incident.

Per cell, the signals to watch are the same ones AWS's guidance repeatedly
returns to, current capacity utilization against the tested maximum (the
500-user, 70-percent-trigger numbers in section 9 are exactly this kind of
gauge), request success rate scoped to that cell only, and health-check
status feeding the router's routing table so an unhealthy cell stops
receiving new assignments quickly. AWS's reference architecture wires "each
cell has monitoring and alerting capabilities using Amazon CloudWatch"
directly into the design rather than treating it as an add-on
([AWS Solutions Library, Guidance for Cell-Based Architecture on AWS](https://docs.aws.amazon.com/solutions/cell-based-architecture-on-aws/),
verified 2026-08-02).

At the aggregate layer, the signal an operator actually wants during an
incident is the fraction of total traffic or total tenants currently
degraded, not a wall of a hundred individual cell dashboards. The same AWS
reference architecture streams every cell's changes into a central data lake
queryable through Amazon Athena and maintains "a central dashboard which
contains aggregated information (such as number of cells with and without
errors)" (same source), which is the concrete, sourced instance of the
aggregate rollup this section is describing.

A healthy instance of this pattern, on a dashboard, looks like a small,
roughly stable number of cells sitting near, but not over, their capacity
threshold, a near-zero count of unhealthy cells at any given moment, and a
router whose own error rate and latency are tracked completely separately
from any individual cell's metrics, since a router degradation is a
different, more severe class of incident than a single cell degrading. A
failing instance looks like either one cell pinned red while the aggregate
stays green, which is the pattern working as intended and containing the
damage, or the router's own metrics degrading in step with cell metrics,
which is the single-point-of-failure misuse pattern described in section 11.

## 17. Security and privacy implications

Cell-based architecture reduces the blast radius of a security incident the
same way it reduces the blast radius of a software failure. Because cells
share no state and, in AWS's stronger recommendation, may run in entirely
separate AWS accounts, "even the use of separate AWS accounts is encouraged"
([AWS Well-Architected, Cell design](https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/cell-design.html),
verified 2026-08-02), a compromised credential or a data leak originating in
one cell has, by construction, no direct network or credential path to reach
another cell's data. This is a genuine security property, not just a
resilience one, and it is one of the stronger reasons to prefer a hard cell
boundary over a soft, logical partition inside one shared account.

Cells also give a natural mechanism for data residency and sovereignty
requirements, since a partition key based on geography or market lets an
organization pin a specific cell, and only that cell, to a specific Region or
jurisdiction. American Express's market-based partition key is the concrete
production instance of exactly this property, cited in section 9.

The cell router is the system's clearest single point of authentication and
authorization enforcement, and AWS's reference cell-router pattern treats it
that way, running every request through Amazon Cognito for authentication and
authorization before the `Orchestrator` workflow ever runs
([AWS Prescriptive Guidance, Set up a serverless cell router for a cell-based architecture](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/serverless-cell-router-architecture.html),
verified 2026-08-02). That concentration is also a risk to weigh honestly.
The router and its routing table become a high-value target, since
compromising the routing table, the user-to-cell mapping, could let an
attacker redirect a victim's traffic to a cell the attacker controls or
observe which cell, and therefore which region or market, a given customer
is assigned to. This entry treats that as a genuine, analytical
consideration rather than a sourced finding from any of the cited material,
which does not itself discuss the routing table as an attack surface, so
teams adopting this pattern should apply the same access-control and
encryption discipline to the routing table that they would apply to any
other system holding a full customer list.

## 18. References

- AWS Well-Architected Framework, "Reducing the Scope of Impact with
  Cell-Based Architecture" (guide overview), verified 2026-08-02.
  https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/reducing-scope-of-impact-with-cell-based-architecture.html
- AWS Well-Architected Framework, "What is a cell-based architecture?",
  verified 2026-08-02.
  https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/what-is-a-cell-based-architecture.html
- AWS Well-Architected Framework, "Why use a cell-based architecture?",
  verified 2026-08-02.
  https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/why-to-use-a-cell-based-architecture.html
- AWS Well-Architected Framework, "Cell design", verified 2026-08-02.
  https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/cell-design.html
- AWS Well-Architected Framework, "Cell deployment", verified 2026-08-02.
  https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/cell-deployment.html
- AWS Well-Architected Framework, "Multi-AZ cells", verified 2026-08-02.
  https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/multi-az-cells.html
- AWS Prescriptive Guidance, "Set up a serverless cell router for a
  cell-based architecture," Mian Tariq and Ioannis Lioupras, verified
  2026-08-02.
  https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/serverless-cell-router-architecture.html
- AWS Solutions Library, "Guidance for Cell-Based Architecture on AWS,"
  verified 2026-08-02.
  https://docs.aws.amazon.com/solutions/cell-based-architecture-on-aws/
- AWS Whitepapers, "AWS Fault Isolation Boundaries, Static stability,"
  verified 2026-08-02.
  https://docs.aws.amazon.com/whitepapers/latest/aws-fault-isolation-boundaries/static-stability.html
- Amazon Builders' Library, "Static stability using Availability Zones,"
  Becky Weiss and Mike Furr, verified 2026-08-02.
  https://aws.amazon.com/builders-library/static-stability-using-availability-zones/
- AWS Architecture Blog, "Shuffle Sharding, Massive and Magical Fault
  Isolation," Colm MacCárthaigh, 14 April 2014, verified 2026-08-02.
  https://aws.amazon.com/blogs/architecture/shuffle-sharding-massive-and-magical-fault-isolation/
- Slack Engineering, "Slack's Migration to a Cellular Architecture," Cooper
  Bethea, 22 August 2023, verified 2026-08-02.
  https://slack.engineering/slacks-migration-to-a-cellular-architecture/
- americanexpress.io, "Cell-Based Architecture for Resilient Payment
  Systems," Benjamin Cane, Distinguished Engineer, 11 June 2026, verified
  2026-08-02.
  https://americanexpress.io/cell-based-architecture-for-resilient-payment-systems/
- InfoQ, "DoorDash Uses Service Mesh and Cell-Based Architecture," Eran
  Stiller, 23 January 2024, reporting on DoorDash's own engineering blog,
  verified 2026-08-02.
  https://www.infoq.com/news/2024/01/doordash-service-mesh/
- Marc Brooker, Tao Chen, and Fan Ping, "Millions of Tiny Databases,"
  USENIX NSDI '20, verified 2026-08-02.
  https://www.usenix.org/conference/nsdi20/presentation/brooker
- Marc Brooker, personal blog summary of the Physalia paper, 17 February
  2020, verified 2026-08-02.
  https://www.brooker.co.za/blog/2020/02/17/physalia.html
- Michael T. Nygard, *Release It! Design and Deploy Production-Ready
  Software*, 1st edition, Pragmatic Bookshelf, 2007, chapter 5, the Bulkhead
  pattern in the stability patterns material (chapter attribution
  corroborated via a secondary source, not independently paginated by this
  entry's author).
- Microsoft Learn, Azure Architecture Center, "Deployment Stamps pattern,"
  last updated per page metadata 3 June 2026, verified 2026-08-02.
  https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp

## Code examples

The three examples below implement the same minimal cell router. It holds a
set of fixed-capacity cells, assigns a partition key (a tenant) to the
least-loaded healthy cell, refuses to silently migrate a tenant whose cell
has been marked unhealthy, and computes the blast radius of a given cell's
failure as the fraction of already-assigned tenants that would be affected.
All three were compiled or run directly on this machine before being placed
in this entry. The TypeScript sample passed `tsc --noEmit --strict` against
a scratch project with `@types/node`. The Python sample passed
`python3 -m py_compile` and was then executed with `python3`. The Go sample
passed `go vet` and was then executed with `go run`, including once under
the `-race` detector, with no data races reported.

### TypeScript

```typescript
interface Cell {
  id: string;
  maxCapacity: number;
  usedCapacity: number;
  healthy: boolean;
}

class CellRouter {
  private readonly cells = new Map<string, Cell>();
  private readonly routingTable = new Map<string, string>();
  private readonly bufferRatio: number;

  constructor(bufferRatio = 0.2) {
    this.bufferRatio = bufferRatio;
  }

  addCell(id: string, maxCapacity: number): void {
    this.cells.set(id, { id, maxCapacity, usedCapacity: 0, healthy: true });
  }

  private effectiveCapacity(cell: Cell): number {
    return Math.floor(cell.maxCapacity * (1 - this.bufferRatio));
  }

  private leastLoadedHealthyCell(): Cell | undefined {
    let best: Cell | undefined;
    for (const cell of this.cells.values()) {
      if (!cell.healthy) continue;
      if (cell.usedCapacity >= this.effectiveCapacity(cell)) continue;
      if (!best || cell.usedCapacity < best.usedCapacity) best = cell;
    }
    return best;
  }

  assign(tenantId: string): string {
    const existing = this.routingTable.get(tenantId);
    if (existing !== undefined) {
      const cell = this.cells.get(existing);
      if (cell && cell.healthy) return existing;
      throw new Error(
        `cell ${existing} for tenant ${tenantId} is unhealthy, awaiting rebalance`
      );
    }
    const target = this.leastLoadedHealthyCell();
    if (!target) throw new Error("no cell has spare capacity, provision a new cell");
    target.usedCapacity += 1;
    this.routingTable.set(tenantId, target.id);
    return target.id;
  }

  markUnhealthy(cellId: string): void {
    const cell = this.cells.get(cellId);
    if (cell) cell.healthy = false;
  }

  blastRadius(failedCellId: string): number {
    let affected = 0;
    let total = 0;
    for (const cellId of this.routingTable.values()) {
      total += 1;
      if (cellId === failedCellId) affected += 1;
    }
    return total === 0 ? 0 : affected / total;
  }
}

function main(): void {
  const router = new CellRouter(0.2);
  for (let i = 0; i < 5; i++) router.addCell(`cell-${i}`, 10);

  for (let t = 0; t < 40; t++) router.assign(`tenant-${t}`);

  console.log("tenant-0 routed to", router.assign("tenant-0"));
  router.markUnhealthy("cell-2");
  console.log("blast radius of cell-2 failure", router.blastRadius("cell-2"));

  try {
    router.assign("tenant-2");
  } catch (err) {
    console.log("expected failure", (err as Error).message);
  }
}

main();
```

With a 20 percent buffer ratio and a maximum capacity of 10 per cell, each of
the five cells accepts 8 tenants before the router moves on to the next
least-loaded cell, so 40 tenants exactly fill 5 cells. Because every cell
starts equally loaded, the router fills them in strict round-robin order,
which puts `tenant-2` on `cell-2` and gives a verified blast radius of 0.2,
matching AWS's own "1 in n cells fails, 1/n of traffic affected" arithmetic
from section 7 for the case of five evenly loaded cells.

### Python

```python
"""Cell router. Assigns tenants to fixed-capacity cells that fail alone."""
from dataclasses import dataclass


@dataclass
class Cell:
    id: str
    max_capacity: int
    used_capacity: int = 0
    healthy: bool = True


class UnhealthyCellError(Exception):
    pass


class NoCapacityError(Exception):
    pass


class CellRouter:
    def __init__(self, buffer_ratio: float = 0.2) -> None:
        self._cells: dict[str, Cell] = {}
        self._routing_table: dict[str, str] = {}
        self._buffer_ratio = buffer_ratio

    def add_cell(self, cell_id: str, max_capacity: int) -> None:
        self._cells[cell_id] = Cell(id=cell_id, max_capacity=max_capacity)

    def _effective_capacity(self, cell: Cell) -> int:
        return int(cell.max_capacity * (1 - self._buffer_ratio))

    def _least_loaded_healthy_cell(self) -> Cell | None:
        best: Cell | None = None
        for cell in self._cells.values():
            if not cell.healthy:
                continue
            if cell.used_capacity >= self._effective_capacity(cell):
                continue
            if best is None or cell.used_capacity < best.used_capacity:
                best = cell
        return best

    def assign(self, tenant_id: str) -> str:
        existing = self._routing_table.get(tenant_id)
        if existing is not None:
            cell = self._cells[existing]
            if cell.healthy:
                return existing
            raise UnhealthyCellError(
                f"cell {existing} for tenant {tenant_id} is unhealthy, awaiting rebalance"
            )
        target = self._least_loaded_healthy_cell()
        if target is None:
            raise NoCapacityError("no cell has spare capacity, provision a new cell")
        target.used_capacity += 1
        self._routing_table[tenant_id] = target.id
        return target.id

    def mark_unhealthy(self, cell_id: str) -> None:
        if cell_id in self._cells:
            self._cells[cell_id].healthy = False

    def blast_radius(self, failed_cell_id: str) -> float:
        total = len(self._routing_table)
        if total == 0:
            return 0.0
        affected = sum(1 for c in self._routing_table.values() if c == failed_cell_id)
        return affected / total


def main() -> None:
    router = CellRouter(buffer_ratio=0.2)
    for i in range(5):
        router.add_cell(f"cell-{i}", 10)

    for t in range(40):
        router.assign(f"tenant-{t}")

    print("tenant-0 routed to", router.assign("tenant-0"))
    router.mark_unhealthy("cell-2")
    print("blast radius of cell-2 failure", router.blast_radius("cell-2"))

    try:
        router.assign("tenant-2")
    except UnhealthyCellError as err:
        print("expected failure", err)


if __name__ == "__main__":
    main()
```

Running this file prints `tenant-0 routed to cell-0`, `blast radius of
cell-2 failure 0.2`, and the expected `UnhealthyCellError` message, matching
the TypeScript run exactly, since both implement the identical deterministic
round-robin fill logic against a single-threaded call sequence.

### Go

```go
package main

import (
	"fmt"
	"sync"
)

type cell struct {
	id           string
	maxCapacity  int
	usedCapacity int
	healthy      bool
}

// CellRouter assigns tenants to fixed-capacity cells and never migrates a
// tenant across cells on its own. A separate rebalancer owns migration.
type CellRouter struct {
	mu           sync.Mutex
	cells        map[string]*cell
	routingTable map[string]string
	bufferRatio  float64
}

func NewCellRouter(bufferRatio float64) *CellRouter {
	return &CellRouter{
		cells:        make(map[string]*cell),
		routingTable: make(map[string]string),
		bufferRatio:  bufferRatio,
	}
}

func (r *CellRouter) AddCell(id string, maxCapacity int) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.cells[id] = &cell{id: id, maxCapacity: maxCapacity, healthy: true}
}

func (r *CellRouter) effectiveCapacity(c *cell) int {
	return int(float64(c.maxCapacity) * (1 - r.bufferRatio))
}

func (r *CellRouter) leastLoadedHealthyCellLocked() *cell {
	var best *cell
	for _, c := range r.cells {
		if !c.healthy {
			continue
		}
		if c.usedCapacity >= r.effectiveCapacity(c) {
			continue
		}
		if best == nil || c.usedCapacity < best.usedCapacity {
			best = c
		}
	}
	return best
}

func (r *CellRouter) Assign(tenantID string) (string, error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	if existing, ok := r.routingTable[tenantID]; ok {
		c := r.cells[existing]
		if c.healthy {
			return existing, nil
		}
		return "", fmt.Errorf(
			"cell %s for tenant %s is unhealthy, awaiting rebalance", existing, tenantID,
		)
	}

	target := r.leastLoadedHealthyCellLocked()
	if target == nil {
		return "", fmt.Errorf("no cell has spare capacity, provision a new cell")
	}
	target.usedCapacity++
	r.routingTable[tenantID] = target.id
	return target.id, nil
}

func (r *CellRouter) MarkUnhealthy(cellID string) {
	r.mu.Lock()
	defer r.mu.Unlock()
	if c, ok := r.cells[cellID]; ok {
		c.healthy = false
	}
}

func (r *CellRouter) BlastRadius(failedCellID string) float64 {
	r.mu.Lock()
	defer r.mu.Unlock()
	total := len(r.routingTable)
	if total == 0 {
		return 0
	}
	affected := 0
	for _, c := range r.routingTable {
		if c == failedCellID {
			affected++
		}
	}
	return float64(affected) / float64(total)
}

func main() {
	router := NewCellRouter(0.2)
	for i := 0; i < 5; i++ {
		router.AddCell(fmt.Sprintf("cell-%d", i), 10)
	}

	var wg sync.WaitGroup
	for t := 0; t < 40; t++ {
		wg.Add(1)
		go func(t int) {
			defer wg.Done()
			_, _ = router.Assign(fmt.Sprintf("tenant-%d", t))
		}(t)
	}
	wg.Wait()

	c, _ := router.Assign("tenant-0")
	fmt.Println("tenant-0 routed to", c)

	router.MarkUnhealthy("cell-2")
	fmt.Println("blast radius of cell-2 failure", router.BlastRadius("cell-2"))

	if _, err := router.Assign("tenant-2"); err != nil {
		fmt.Println("expected failure", err)
	}
}
```

The Go version assigns all 40 tenants concurrently across goroutines, guarded
by a single mutex, which is a realistic shape for a router under real
traffic. Running it repeatedly shows that `tenant-0`'s specific cell
assignment is not deterministic under concurrent load, since goroutine
scheduling order decides which cell wins each race for least loaded, while
the blast radius still comes out to 0.2 on every run, because the total
capacity is still spread evenly across five equal cells regardless of
assignment order. That distinction, deterministic capacity balance versus
non-deterministic individual placement, is the concrete argument for the
deterministic, hash-based partition-key routing AWS and American Express
both use in production. A system that needs a specific, reproducible
tenant-to-cell mapping, for debugging, for compliance audits, for cache
warmup, needs a router built on a deterministic function of the partition
key, not on whichever cell happened to win a capacity race.
