---
name: Gateway Aggregation
slug: gateway-aggregation
family: 08-cloud-distributed
category: Cloud and Distributed
aliases: [Aggregating Gateway, Composition Gateway, API Composition, Backend Aggregation Layer]
first_described: "Microsoft patterns and practices, Cloud Design Patterns, 2014"
maturity: canonical
related: [backends-for-frontends, circuit-breaker, bulkhead, retry, cache-aside, materialized-view, api-gateway]
incompatible_with: []
verified: 2026-08-02
---

# Gateway Aggregation

## 1. Name, aliases, and lineage

The canonical name is **Gateway Aggregation**, catalogued by Microsoft in its
cloud design patterns collection. The pattern page states plainly what the
gateway does, saying it receives client requests, "dispatches requests to
the various back-end systems, and aggregates the results before it sends
them back to the client" ([Microsoft Learn, Gateway Aggregation pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-aggregation),
verified 2026-08-02).

The same shape appears under other names depending on which community is
describing it. Chris Richardson's pattern catalog, built out of his book
*Microservices Patterns*, describes the same mechanic under **API
Composition**, defining it as a component, an API Composer, that works "by
invoking the services that own the data and performs an in-memory join of
the results" (Richardson, *Microservices Patterns*, Manning, 2018,
chapter 7, and the companion catalog at
[microservices.io, API Composition pattern](https://microservices.io/patterns/data/api-composition.html),
verified 2026-08-02). Richardson treats API Composition as the general
technique and the API Gateway as one common place to host it, noting that
an API gateway "handles requests in one of two ways. Some requests are
simply proxied/routed to the appropriate service. It handles other
requests by fanning out to multiple services" ([microservices.io, API Gateway pattern](https://microservices.io/patterns/apigateway.html),
verified 2026-08-02).

A third label, **Composition Gateway**, shows up in vendor documentation
(Azure API Management's send-request policy pages, referenced from the
Gateway Aggregation article above) where the aggregation logic is expressed
as a routing policy rather than a hand-written service. A fourth label,
**Backend Aggregation Layer**, is common in plain engineering conversation
and is not attached to any single catalog.

There is no single inventor. The technique predates its name by a long
margin. Any client that ever called two servers and merged the answers was
already doing this. What the Microsoft catalog and Richardson's book
contributed was a name, a written account of the failure modes, and a
place in the pattern literature next to Circuit Breaker and Bulkhead, and
that is why "Gateway Aggregation" is the name that survives in
architecture reviews.

One naming trap is worth flagging up front, because dimension 12 depends
on it. Gateway Aggregation is not the same claim as an **API Gateway**. An
API Gateway is the broader edge-routing role (authentication, rate
limiting, TLS termination, request routing), and aggregation is one
capability that a gateway can optionally host. A gateway that only proxies
one-to-one is not doing Gateway Aggregation. A service that fans out and
merges but sits behind a separate routing gateway is still Gateway
Aggregation, though not colocated with the edge. The name describes the
fan-out-and-merge behavior, not the deployment position.

## 2. Problem and context

A client needs data or a decision that no single backend service owns end
to end. An order summary screen needs the order record, the shipment
status, and the customer's loyalty tier, and in a service-oriented or
microservices system those three facts live in three different services
with three different owners. The client is left with two bad choices,
either call each service directly and stitch the results together itself,
or wait for someone to build a bigger service that owns all three facts,
which recreates the monolith the split was meant to avoid.

Microsoft's framing of the problem names the concrete trigger precisely,
stating that "to perform a single task, a client might have to make
multiple calls to various back-end services... This chattiness between a
client and a back end can adversely affect the performance and scale of
the application. Microservices architectures have made this problem more
common because applications built around many smaller services have a
higher number of cross-service calls" ([Microsoft Learn, Gateway Aggregation pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-aggregation),
verified 2026-08-02).

The problem is worst on high-latency links. Facebook's own account of why
it built GraphQL, a different answer to a related problem, makes the
mobile case explicit, noting that a hierarchical fetch "naturally follows
relationships between objects, where a RESTful service may require
multiple round-trips (resource-intensive on mobile networks)"
([Facebook Engineering, "GraphQL. A data query language"](https://engineering.fb.com/2015/09/14/core-data/graphql-a-data-query-language/),
verified 2026-08-02). Three sequential round trips at 200 milliseconds each
over a cellular connection add up to 600 milliseconds of pure network wait
before any rendering starts, and that number does not improve by adding
backend capacity, because the backend was never the bottleneck. The round
trip was.

The context in which Gateway Aggregation is the right answer has three
parts, and all three usually need to hold at once. First, a single client
operation genuinely needs data owned by more than one independent service,
so there is real fan-out to do, not a single call dressed up as many.
Second, the client sits on a network where round trips are expensive
relative to backend processing time, which is true of mobile apps, IoT
devices, and any browser client on a slow connection, and less true of a
server calling another server inside the same data center. Third, the
composition logic itself is comparatively simple, a merge, a restructure, and
a partial-failure rule, rather than a multi-step business transaction with
compensating actions, which belongs to Saga instead.

## 3. Forces

**Latency versus complexity.** Every round trip removed from the client is
latency saved, and every round trip removed adds a piece of moving
infrastructure the team now owns, deploys, and monitors. The pattern
trades client-side simplicity for gateway-side complexity, and the trade
is only worth it when the removed latency is real (a cellular round trip)
rather than theoretical (a call inside the same VPC that already runs in
single digit milliseconds).

**Coupling versus ownership.** A well-built gateway hides which service
owns what, so a service can be re-decomposed, merged, or replaced without
the client noticing. A badly built gateway becomes an accidental map of
every backend's internal shape, and any change to a backend response
forces a gateway change, which is coupling by another name. This rule
sacrifices some backend team autonomy for client simplicity, since the
backend teams now have a second consumer, the gateway, whose contract they
must not break. *(Judgement. Which direction this trade leans depends on
how many client types exist and how often backend schemas change, and a
single client with stable schemas makes the coupling cost small.)*

**Availability versus fan-out breadth.** Every backend call the gateway
adds to a single client request is another independent chance of failure
inside that request. If each of five backends is 99.9 percent available
independently, a naive aggregation that requires all five to succeed is
available roughly 99.5 percent of the time for that combined request,
noticeably worse than any single backend. This is the central operability
force in the pattern, and dimension 11 covers the concrete failure this
produces.

**Consistency versus performance.** Each backend call sees its own moment
in time. A response assembled from five independently fetched sources can
show an order as "shipped" from one service while the payment service,
called a few hundred milliseconds later, still shows "pending," because
the world moved between the two calls. Fetching everything
transactionally would fix this and would also destroy the latency win the
pattern exists to provide. The pattern accepts eventual, momentary
inconsistency in the assembled view in exchange for speed.

**Cost and team topology.** A dedicated aggregation service is a service.
Someone owns its on-call rotation, its deploy pipeline, its capacity
planning. Folding aggregation into an existing edge gateway (API
Management, Envoy, a custom edge layer) avoids a new deployable but risks
turning a routing component into a business-logic component that the
platform team never signed up to own. Microsoft's own guidance names this
directly, recommending that engineers "rather than build aggregation into
the gateway, consider placing an aggregation service behind the gateway.
Request aggregation is likely to have different resource requirements
than other services in the gateway and might affect the gateway's
routing and offloading functionality" ([Microsoft Learn, Gateway Aggregation pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-aggregation),
verified 2026-08-02).

## 4. Applicability and non-applicability

**Reach for Gateway Aggregation when**:

- A client screen or client operation genuinely needs data from two or
  more independently owned services, and no existing service is the
  natural owner of the combined view.
- The client runs on a network where round trips are expensive, such as a
  mobile app on cellular data, an IoT device on a constrained link, or a
  browser on a slow or high-latency connection.
- The composition is read-shaping, merging, filtering, and renaming
  fields to present a client-friendly view, rather than a multi-step
  write workflow with rollback requirements.
- More than one client type (web, mobile, partner API) needs a different
  shape of the same underlying combined data, which pushes toward
  Backends for Frontends built on top of this pattern per client.
- The backend services are stable enough, or versioned carefully enough,
  that the gateway is not rewritten every time a backend team ships.

**Do NOT reach for Gateway Aggregation when**:

- The client and the backend services live inside the same data center or
  the same process boundary, where round-trip cost is already single
  digit milliseconds. Microsoft's own guidance says this outright, noting
  the pattern "might not be suitable when... the client or application is
  located near the back-end services and latency isn't a significant
  factor" ([Microsoft Learn, Gateway Aggregation pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-aggregation),
  verified 2026-08-02).
- The real problem is one client calling one service many times across
  separate operations, not one operation needing many services. Microsoft
  names the correct fix for that case explicitly, saying "adding a batch
  operation to the service might be more suitable" (same source), which
  keeps the fix inside the owning service rather than adding a new layer.
- The composition needs a distributed transaction, meaning multiple
  writes that must all succeed or all roll back together. That need
  belongs to Saga, not to a read-time aggregation layer, because Gateway
  Aggregation has no compensating-action machinery.
- Every client already needs exactly the same aggregated shape and there
  is only one client type. In that narrow case, folding the composition
  directly into the one client-facing service that already exists is
  simpler than standing up a new layer for a population of one.
- The number of backend dependencies per request is large and growing
  without bound (dozens, not three to six). Past a certain fan-out width
  the gateway's own availability math (dimension 3) makes the aggregated
  endpoint less reliable than any reasonable SLA, and a materialized,
  precomputed view (see Materialized View and CQRS) usually serves the
  read faster and more reliably than fetching live on every request.
- The client can tolerate its own multiple round trips because it is not
  latency sensitive, such as a nightly batch job or an internal admin
  tool used a few times a day. Adding a gateway here is pure overhead
  with no user ever feeling the saved milliseconds.

## 5. Structure

**Client.** The caller that would otherwise need to know about and call
every backend service directly. After the pattern is introduced, the
client knows only the gateway's contract.

**Gateway (aggregator).** The component that receives the single client
request, determines which backend calls are required to satisfy it,
issues those calls (in parallel wherever they are independent), and
assembles a single response. This is the role Microsoft's diagram labels
the gateway and Richardson's catalog labels the API Composer.

**Backend services (providers).** The independently owned, independently
deployed services that each hold one piece of the answer. They are
unmodified by the pattern. They continue to expose their normal APIs and
have no awareness that a gateway calls them.

**Composition logic.** The specific rule for merging, whether that is a
plain object merge, a partial-failure policy (return what succeeded, mark
what failed), a precedence rule when two sources disagree, or a
timeout-and-default rule when a source is too slow. Microsoft's guidance
calls out that this logic can live inside the gateway process itself or
in a dedicated aggregation service placed behind a thinner routing
gateway, which is the separation of concerns dimension 3 discusses under
cost and team topology.

**Fault-tolerance wrapper.** The retry, timeout, circuit breaker, and
bulkhead logic wrapped around each individual backend call, so that one
slow or failed dependency does not sink the whole aggregated response.
Microsoft's own considerations list names this directly, recommending
timeout, retry, circuit breaking, and bulkhead techniques together as a
deliberate design choice for this pattern (same source as above).

## 6. ASCII structure diagram

```
                         +-------------------+
                         |      Client       |
                         | (mobile / browser) |
                         +---------+---------+
                                   |
                          single request/response
                                   |
                                   v
                    +------------------------------+
                    |   Gateway (Aggregator)        |
                    |   - fan-out dispatch           |
                    |   - per-call timeout/retry      |
                    |   - merge / restructure         |
                    |   - partial-failure policy       |
                    +---+----------+----------+-------+
                        |          |          |
              parallel  |          |          |  parallel
                        v          v          v
                +----------+ +----------+ +----------+
                |  Order   | | Shipment | | Customer |
                | Service  | | Service  | | Service  |
                +----------+ +----------+ +----------+
                (owned team) (owned team) (owned team)
```

## 7. Dynamics

The sequence below shows the happy path plus the one degraded path every
production implementation of this pattern must handle, a single backend
that answers too slowly.

```
Client        Gateway         Order Svc      Shipment Svc     Customer Svc
  |  GET /order-summary/42       |               |                |
  |------------------------------>               |                |
  |               | dispatch (parallel, with per-call timeout)     |
  |               |------------->|                |                |
  |               |----------------------------->|                |
  |               |------------------------------------------->   |
  |               |               |                |                |
  |               |    200 order  |                |                |
  |               |<--------------|                |                |
  |               |               |   200 shipment |                |
  |               |<-----------------------------|                |
  |               |               |                |  TIMEOUT (300ms cap)
  |               |               |                |  no response yet
  |               | apply partial-failure policy    |                |
  |               | customer data marked unavailable                |
  |               | merge order + shipment + fallback customer stub |
  |  200 aggregated summary (customer.loyaltyTier = null, partial=true)
  |<------------------------------|
```

The important property is that the gateway makes ONE decision about how
long to wait for the slowest dependency, and that decision is visible to
the client as either a complete response or an explicitly marked partial
one. Microsoft's guidance frames the same choice, noting "if one or more
service calls take too long, it might be acceptable to time out and
return a partial set of data. Consider how your application will handle
this scenario" ([Microsoft Learn, Gateway Aggregation pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-aggregation),
verified 2026-08-02). What the client does with `partial=true` (show a
skeleton for the missing field, retry in the background, or hide the
section) is a UI decision the gateway should never make silently by
omitting the field with no signal.

## 8. Implementation variants

**Inline gateway aggregation.** The composition logic lives directly
inside the edge gateway or API management layer, expressed as
configuration or a policy script (Azure API Management's send-request
policy is the Microsoft-documented example of this shape). Cheapest to
stand up, and the one Microsoft's own considerations list warns against
scaling past simple cases, because request aggregation, in the catalog's
own words, "is likely to have different resource requirements than other
services in the gateway and might affect the gateway's routing and
offloading functionality" (same source).

**Dedicated aggregation service behind a thin gateway.** The edge gateway
stays a pure router, and a separate service, deployed and scaled
independently, does the fan-out and merge. This is the shape Richardson
calls API Composition and treats as distinct from, though usually hosted
near, the API Gateway role (Richardson, *Microservices Patterns*,
Manning, 2018, chapter 7). This variant costs one more deployable but
isolates the aggregation's resource profile (I/O bound and bursty) from
the gateway's routing profile (CPU bound and steady).

**Query-language aggregation (GraphQL).** Instead of the gateway deciding
in advance which fields to fetch and merge, the client specifies the
exact shape it wants in a single query, and a GraphQL server resolves
each field against the owning backend, often in parallel, then assembles
exactly the requested shape. This shifts the "what to aggregate" decision
from the gateway's hard-coded logic to the client's query, at the cost of
a new query language and resolver layer the team must operate. Facebook
built it for precisely this class of problem, describing the goal as "a
data-fetching API powerful enough to describe all of Facebook, yet simple
enough to be easy to learn and use by our product developers"
([Facebook Engineering, "GraphQL. A data query language"](https://engineering.fb.com/2015/09/14/core-data/graphql-a-data-query-language/),
verified 2026-08-02).

**Backends for Frontends (BFF), each one a fixed aggregator.** Instead of
one general aggregation gateway serving every client type, each client
type (iOS, Android, web, partner API) gets its own small, purpose-built
aggregating backend, owned by the same team that owns the client. Sam
Newman describes the motivation directly, writing that "mobile devices
will want to make different calls, fewer calls, and will want to display
different (and probably less) data than their desktop counterparts," and
that a single shared gateway tends toward "bloated" logic trying to serve
every client's needs at once ([Sam Newman, Backends For Frontends pattern](https://samnewman.io/patterns/architectural/bff/),
verified 2026-08-02). BFF is Gateway Aggregation applied per client type
rather than once for all clients, and dimension 12 compares the two
directly.

**Language-idiomatic dispatch.** In languages with first-class
concurrency primitives (Go's goroutines and channels, or `async`/`await`
futures in TypeScript, Python, Rust, and Java), the fan-out step is
written as a set of concurrent calls joined at the end
(`Promise.allSettled`, `asyncio.gather(..., return_exceptions=True)`, an
`errgroup.Group`), rather than as a sequential loop. The choice of the
"settled" or "exceptions" variants over their fail-fast counterparts
(`Promise.all`, a bare `asyncio.gather`) is exactly the partial-failure
decision from dimension 3 expressed at the code level. Fail-fast aborts
the whole aggregation on the first error, while a settled-style call
collects every outcome so the merge step can apply its own
partial-failure policy.

## 9. Known production uses

**Netflix's edge gateway (Zuul).** Netflix built and operates Zuul, "an L7
application gateway that provides capabilities for dynamic routing,
monitoring... and security" at Netflix's edge, tracing back to
Netflix's original 2013 announcement of Zuul as an edge service
([Netflix, Zuul README, GitHub](https://github.com/Netflix/zuul), verified
2026-08-02). Richardson's catalog cites Netflix's API layer specifically
for the client-adapter and fan-out shape this pattern describes, noting
that the gateway "runs client-specific adapter code that provides each
client with an API that's best suited to its requirements"
([microservices.io, API Gateway pattern](https://microservices.io/patterns/apigateway.html),
verified 2026-08-02), which is the fan-out-then-merge behavior applied per
device family.

**Azure API Management as a Gateway Aggregation layer.** Microsoft's own
reference implementation uses Azure API Management in front of an Azure
Container Apps environment to aggregate an order service, a shipment
service, and a customer profile service into one order-summary response,
using the send-request policy to fetch and combine the three calls before
returning a single payload to the client
([Microsoft Learn, Gateway Aggregation pattern, Example section](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-aggregation),
verified 2026-08-02). This is a named, documented production pattern
rather than a hypothetical, and Microsoft ships circuit breaker support
directly on API Management backends for exactly this use, referenced in
the same article's guidance to harden the aggregation with per-request
timeouts and circuit breakers.

**Facebook's GraphQL, the query-language variant of the same problem.**
Facebook built GraphQL specifically to stop mobile clients from paying
for "multiple round-trips (resource-intensive on mobile networks)"
against its REST-shaped services, moving the aggregation decision into a
single resolver layer that fans out to the owning data sources
([Facebook Engineering, "GraphQL. A data query language"](https://engineering.fb.com/2015/09/14/core-data/graphql-a-data-query-language/),
verified 2026-08-02). It solves the same forces (dimension 3) as Gateway
Aggregation and is treated in this catalog as a named alternative rather
than a subtype, because the design of "what gets fetched" moves from the
gateway to the client's query.

**SoundCloud and REA's Backends for Frontends, a per-client instance of
this pattern.** Sam Newman documents Phil Calcado's account of SoundCloud
and REA Group each building "one backend per user experience" instead of
a single shared aggregation gateway, so that each client team could
evolve its own aggregation logic and API shape without coordinating
through a shared gateway team ([Sam Newman, Backends For Frontends pattern](https://samnewman.io/patterns/architectural/bff/),
verified 2026-08-02). This is Gateway Aggregation instantiated once per
client type rather than once globally, and dimension 12 covers exactly
when that split is worth its extra operational cost.

## 10. Consequences

**Positive.**

- Removes chatty round trips from latency-sensitive clients, converting N
  sequential or parallel client-to-backend calls into one client-to-gateway
  call, which Microsoft's own workload-design guidance credits with
  reducing "the number of touchpoints that a client has with a system,"
  narrowing the public attack surface at the same time it narrows the
  round-trip count.
- Decouples the client from the internal decomposition of the backend.
  Services can be split, merged, renamed, or re-owned without the client
  changing, as long as the gateway's contract stays stable.
- Centralizes cross-cutting fault-handling concerns (timeout policy, retry
  policy, circuit breaking) in one place instead of duplicating that
  logic inside every client.
- Gives operators a single place to add caching for the assembled view,
  which can absorb repeat requests for the same aggregate without
  hitting every backend again (see Cache-Aside for how that caching
  layer itself is usually built).

**Negative.**

- Introduces a new component that can fail on its own, and, more
  seriously, whose failure blocks every operation that depends on it.
  Microsoft states this directly, warning that "the gateway service
  might introduce a single point of failure (SPoF)" and that the gateway
  design must meet the application's own availability requirements
  ([Microsoft Learn, Gateway Aggregation pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-aggregation),
  verified 2026-08-02).
- Multiplies the number of things that can go slightly wrong per client
  request. A request that used to depend on one service's SLA now
  depends on the SLA of every fanned-out service, combined by whatever
  rule the gateway applies (all-must-succeed is strictly worse than the
  worst individual dependency).
- Adds an operational surface. Someone must monitor the gateway's own
  latency, error rate, and per-dependency breakdown, separately from
  monitoring each backend, or a slow gateway hides behind healthy-looking
  backend dashboards.
- Creates a place where backend schema changes ripple outward. A field
  rename in the order service is invisible to the order service's own
  tests but breaks the gateway's merge logic, and by extension, the
  client, unless the backend team knows to coordinate with the gateway
  team.

## 11. Failure modes and misuse

**Symptom.** Every client request times out, even though each individual
backend service reports healthy in its own dashboard.
*Cause.* The gateway makes its N backend calls sequentially rather than
concurrently, so a client-visible timeout of, say, 2 seconds is actually
the sum of five 400-millisecond calls rather than the maximum of them.
*Fix.* Dispatch independent backend calls concurrently (goroutines with a
`WaitGroup`, `Promise.allSettled`, `asyncio.gather`), and size the
overall client-visible timeout against the slowest expected dependency,
not the sum of all of them.

**Symptom.** The assembled response silently omits a field with no
error, no log entry, and no visible signal to the caller.
*Cause.* The merge step swallows a failed backend call and leaves
the field out of the JSON, treating "the shipment service errored" the
same as "the shipment service legitimately has no data." *Fix.*
Distinguish "field absent because there is genuinely no data" from
"field absent because the call failed," using an explicit `partial: true`
marker or a per-field status, per Microsoft's own guidance to consider
how the application will handle a slow-dependency scenario.

**Symptom.** The gateway becomes the busiest, most-alerted-on service in
the whole system, and every incident review traces back to it.
*Cause.* Business logic crept into the gateway over time, a
special-casing `if` for one client, a retried write, a cache
invalidation rule, none of which belong to routing or composition. The
gateway grew from "fan out and merge" into "the place where everything
eventually gets bolted on" because it was the easiest file to edit.
*Fix.* Treat any logic beyond dispatch, timeout, merge, and
partial-failure policy as a signal to extract a dedicated aggregation
service behind a thin routing gateway, exactly the separation
Microsoft's own considerations recommend.

**Symptom.** A load test against one backend service passes cleanly, but
the same backend falls over in production during a traffic spike on an
unrelated client feature.
*Cause.* The gateway fans out to the same backend from multiple,
unrelated client-facing endpoints, and none of those fan-out paths were
included when that backend's own team load-tested it in isolation. The
backend's capacity planning never accounted for gateway-multiplied
traffic. *Fix.* Load-test through the gateway, not only against each
backend directly, and give each backend team visibility into how many
gateway paths call it. Microsoft's guidance recommends load testing
against the gateway itself so a failure in one dependency never spreads
to the services behind it.

**Symptom.** Two different fields in the assembled response contradict
each other, such as an order that shows "delivered" while the same
response's tracking section shows "in transit."
*Cause.* Each backend call was made independently, at a slightly
different moment, and nothing in the merge step accounts for read skew
across sources fetched a few hundred milliseconds apart. *Fix.* This is
an inherent, not accidental, consequence of the pattern (dimension 3,
consistency versus performance). The fix is to design the UI to
tolerate momentary skew (show a "last updated" marker per section
rather than implying one consistent snapshot), or to accept the added
latency of fetching from a single consistent source when the domain
genuinely cannot tolerate skew.

## 12. Trade-off matrix

| Force | Gateway Aggregation (fixed shape, server-decided) | GraphQL (client-decided shape, single endpoint) | Backends for Frontends (one aggregator per client type) |
|---|---|---|---|
| Who decides what gets fetched | The gateway's hard-coded logic, changed by a deploy | The client, per query, no gateway deploy needed for a new field combination | Each client team's own BFF logic, changed by that team's deploy |
| Over-fetching / under-fetching | Common, the gateway returns one fixed shape for all callers of that endpoint | Minimized by design, the client asks for exactly the fields it needs | Minimized per client type, but only for that type |
| Operational surface | One gateway (or one aggregation service) to run and monitor | One GraphQL server, plus a resolver per data source, plus query complexity limits to prevent abusive queries | One extra service per client type, more total deployables |
| Team ownership fit | Works well for a single client type or a small, stable set of clients | Works well when many client shapes vary and a dedicated platform team owns the schema | Works well when each client team wants full control and can own an extra backend |
| New client-facing field | Requires a gateway code change and deploy | Often requires only a resolver addition, sometimes zero gateway change if the field already exists on a type | Requires a change in the specific BFF for that client, not the others |
| Failure blast radius | One shared SPoF for every client of that gateway | One shared SPoF for every client of that GraphQL endpoint, same risk class as Gateway Aggregation | Blast radius contained to one client type's BFF, other clients keep working |
| Learning curve / new tooling | Low, ordinary HTTP and ordinary code | Higher, a new query language, a schema, resolver conventions, and query cost controls | Low per BFF, the cost is more services, not new tooling |

*(Judgement. The matrix compares the three approaches on the forces named
in dimension 3, and which cell matters most is a product of how many
client types exist today and how fast the schema is expected to change,
which the matrix cannot answer generically.)*

## 13. Related and incompatible patterns

**Backends for Frontends.** BFF is Gateway Aggregation specialized per
client type rather than shared across all clients. Teams usually start
with a single shared aggregation gateway and split it into per-client
BFFs once the "bloated, everyone's-needs-at-once" cost Sam Newman
describes starts to bite. The two compose directly, since a BFF is
usually itself an instance of Gateway Aggregation, only scoped narrower.

**Circuit Breaker and Bulkhead.** Both are near-mandatory companions
rather than optional extras, because Gateway Aggregation is the pattern
that multiplies a client request's dependency count, and Circuit Breaker
plus Bulkhead are what stop one slow dependency from taking down the
whole gateway. Microsoft's own considerations list names both directly
as part of implementing this pattern responsibly.

**Retry.** Applied per backend call inside the gateway's dispatch step,
bounded and jittered, never applied to the aggregated call as a whole.
Retrying a five-way fan-out wholesale only because one of the five was
slow multiplies load on the four that already succeeded.

**Cache-Aside.** A gateway that assembles the same aggregate repeatedly
for many callers is a strong candidate for caching the assembled result,
using Cache-Aside at the gateway layer, which absorbs read traffic
without touching any backend on a cache hit.

**Materialized View and CQRS.** When the aggregation is read far more
often than the underlying data changes, or when the fan-out width grows
beyond what dimension 4's non-applicability list tolerates, a
Materialized View (often populated by CQRS's read-model projection)
replaces live fan-out with a precomputed, single-source read, trading
staleness for reliability and speed. Gateway Aggregation and Materialized
View solve overlapping problems from opposite directions. One computes
the aggregate on every request, the other computes it once and reads it
many times.

**API Composition (Richardson).** Not a different pattern from Gateway
Aggregation so much as a different name emphasizing the composition
logic over the gateway placement, see dimension 1.

**Saga.** Actively the wrong tool for the same-looking problem when the
operation is a write across services rather than a read. A team that
reaches for Gateway Aggregation to coordinate a multi-service write,
rather than Saga, will discover the pattern has no compensating-action
machinery and no way to roll back a partially completed operation. This
is a genuine incompatibility of purpose, not merely a style choice.

## 14. Refactoring path in and out

**Introducing the pattern into existing chatty-client code.**

1. Identify one client operation that currently issues multiple direct
   backend calls (grep the client codebase for two or more service calls
   inside the same handler or the same screen's data-loading function).
2. Stand up a thin new endpoint, on an existing gateway or a new small
   service, that accepts the single logical request the client wants to
   make (`GET /order-summary/{id}`, not `GET /order/{id}`,
   `GET /shipment/{id}`, `GET /customer/{id}` issued three times).
3. Inside that endpoint, call the same backend services the client used
   to call directly, concurrently, with a bounded per-call timeout.
4. Define the partial-failure policy explicitly before writing the merge
   code. Decide which fields are required for the response to be
   considered successful, and which are allowed to degrade to a default
   or a `null` with a status flag.
5. Merge the results into the shape the client actually needs, which is
   very often not simply the union of the three backend payloads but a
   restructured, trimmed view.
6. Point the client at the new endpoint and delete its old direct calls
   to the three backends. Keep the backends' original APIs untouched. Do
   not couple them to the gateway's existence.
7. Add the fault-tolerance wrapper from dimension 5 (timeout, retry, circuit
   breaker) around each backend call before the endpoint goes to
   production traffic, not after an incident makes it obvious it was
   missing.

**Removing the pattern once it stops earning its place.**

1. Confirm the removal reason first. Either the client and backends are
   now co-located (latency force gone), or the read pattern has shifted
   from "occasional live fan-out" to "constant repeated reads of the
   same aggregate" (a signal to move to Materialized View instead of
   removing aggregation outright, per dimension 13).
2. If genuinely removing it, restore direct client-to-backend calls one
   dependency at a time, verifying at each step that the client's own
   latency budget still holds without the gateway's parallel fan-out
   doing the work for it.
3. Decommission the aggregation endpoint only after traffic to it has
   been confirmed at zero for a full deployment cycle, not immediately
   after the client change ships, in case of a delayed client rollout.

## 15. Testing and verification

What becomes easier. Each backend service's own contract tests stay
simple and unaware of the gateway, because the gateway is the only thing
that changes when a client's needs change, not the backend. The gateway
itself becomes a natural seam for a test double. Stub each backend
dependency independently and assert the gateway's merge and
partial-failure logic without needing all three real services running,
which is a large win over testing the same composition logic duplicated
inside a client app.

What becomes harder. Correctness across the whole call chain now depends on the
interaction of independently deployed services, so a passing test suite
for the gateway plus a passing test suite for each backend does not
guarantee the combination behaves correctly together, particularly
around field renames and null-handling differences between backends.
Contract tests (each backend publishes a schema the gateway tests
against, and the gateway's own consumer-driven contract is checked
against each backend's provider tests) close most of this gap. Without
them, the failure mode in dimension 11 (silently dropped fields) tends
to surface first in production.

The specific test cases every gateway aggregation test suite needs, at
minimum, are these. All backends succeed (happy path). Exactly one
backend times out while the rest succeed (verify the partial-failure
marker, not a silent omission). All backends fail (verify a clean error
rather than a half-built object). One backend returns malformed or
unexpected data (verify the merge step does not propagate a type error
into the client response). And a load or soak test through the gateway
itself, not only against each backend independently, per the failure
mode named in dimension 11 about capacity planning blind spots.

## 16. Observability signals

Track, at minimum, per-backend-call latency and error rate broken out
individually, not only the aggregate endpoint's overall latency, because
an aggregate p99 that looks fine can hide one dependency at p99 800
milliseconds masked by four dependencies at p50 10 milliseconds.
Microsoft's own guidance names two concrete practices directly, calling
for engineers to "implement distributed tracing by using correlation IDs
to track each individual call" and to "monitor request metrics and
response sizes" ([Microsoft Learn, Gateway Aggregation pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-aggregation),
verified 2026-08-02).

*(Judgement, drawn from operating this class of system.)* A healthy
instance shows a stable ratio between the aggregate endpoint's request
rate and each backend's request rate (a fan-out of three backends should
show each backend receiving roughly the gateway's own request rate, plus
its own direct callers if any). A drifting ratio is the first sign of a
retry storm or a caching regression. A healthy instance also shows the
partial-failure rate as its own tracked metric, separate from the hard
error rate, because a gateway that returns 200 with `partial: true` on
every request is degraded even though nothing shows up as a 5xx. Trace
spans should carry the correlation ID from the client request through
every fanned-out backend call, so a slow aggregate response can be
attributed to the specific backend that caused it rather than to "the
gateway" as an undifferentiated black box.

## 17. Security and privacy implications

The gateway becomes a single point where authorization decisions can be
centralized, which Microsoft's workload-design guidance frames as a
reduction in "the public surface area and authentication points," since
"the aggregated back ends can remain fully network-isolated from
clients" (same source as dimension 10). That is a genuine security win
when done correctly, because the backends never need to be independently
reachable from the public internet or from untrusted client networks.

*(Judgement. The following risks are analytical, drawn from how this
pattern is commonly misbuilt, rather than sourced claims about a
specific incident.)* The same centralization is a risk when the gateway
is given a single, broad service credential to call every backend on
behalf of every client, because that credential now has the combined
privilege of every backend the gateway touches, and a bug in the
gateway's authorization check exposes all of them at once rather than
one. Prefer per-backend, scoped credentials, and re-derive the caller's
actual authorization on each backend call rather than trusting that "the
gateway already checked it" once at the edge. A second risk is data
over-collection at the merge step, because the gateway naturally sees
the union of every backend's response, and that makes it an easy place
for a field that should never reach the client (an internal cost basis,
a plaintext identifier that should have stayed hidden, another customer's data returned by a backend
bug) to leak through in the merged payload if the merge step is a blind
object spread rather than an explicit allowlist of client-facing fields.

## 18. References

- [Microsoft Learn, Gateway Aggregation pattern, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-aggregation), verified 2026-08-02.
- Richardson, Chris. *Microservices Patterns*. Manning Publications, 2018, chapter 7 ("Implementing queries in a microservice architecture"), covering the API Composition pattern.
- [microservices.io, API Composition pattern](https://microservices.io/patterns/data/api-composition.html), verified 2026-08-02.
- [microservices.io, API Gateway pattern](https://microservices.io/patterns/apigateway.html), verified 2026-08-02.
- [Sam Newman, Backends For Frontends pattern](https://samnewman.io/patterns/architectural/bff/), verified 2026-08-02.
- [Netflix, Zuul README, GitHub](https://github.com/Netflix/zuul), verified 2026-08-02.
- [Facebook Engineering, "GraphQL. A data query language"](https://engineering.fb.com/2015/09/14/core-data/graphql-a-data-query-language/), verified 2026-08-02.

## Code examples

Working code in three languages, chosen because they represent three
distinct idioms for the pattern's core mechanic (concurrent fan-out plus
partial-failure merge), TypeScript's `Promise.allSettled` for a Node.js
gateway, Python's `asyncio.gather` with `return_exceptions=True` for an
async gateway, and Go's goroutines joined over channels for a statically
typed, concurrent-by-design gateway. Java and Rust are omitted because the
pattern does not change shape in either language beyond swapping
`CompletableFuture.allOf` or `futures::join_all` for the same
concurrent-join idiom shown in Go. The interesting decision (how to
encode partial failure in the merged type) is identical in spirit to the
Go example below. Swift and Kotlin are omitted for the same reason. Both
have a structured-concurrency `TaskGroup` or `coroutineScope { async { } }`
shape that is a direct translation of the Go `errgroup` idiom below.

### TypeScript (Node.js, `Promise.allSettled`)

```typescript
interface OrderSummary {
  orderId: string;
  order: { total: number; status: string } | null;
  shipment: { carrier: string; status: string } | null;
  customer: { name: string; loyaltyTier: string } | null;
  partial: boolean;
}

async function fetchWithTimeout<T>(
  fetcher: () => Promise<T>,
  timeoutMs: number
): Promise<T> {
  return Promise.race([
    fetcher(),
    new Promise<T>((_, reject) =>
      setTimeout(() => reject(new Error("timeout")), timeoutMs)
    ),
  ]);
}

async function getOrderSummary(orderId: string): Promise<OrderSummary> {
  const [orderRes, shipmentRes, customerRes] = await Promise.allSettled([
    fetchWithTimeout(() => fetchOrder(orderId), 400),
    fetchWithTimeout(() => fetchShipment(orderId), 400),
    fetchWithTimeout(() => fetchCustomer(orderId), 400),
  ]);

  const order = orderRes.status === "fulfilled" ? orderRes.value : null;
  const shipment =
    shipmentRes.status === "fulfilled" ? shipmentRes.value : null;
  const customer =
    customerRes.status === "fulfilled" ? customerRes.value : null;

  return {
    orderId,
    order,
    shipment,
    customer,
    partial: order === null || shipment === null || customer === null,
  };
}

// Stand-ins for real network calls, kept minimal so the file runs.
async function fetchOrder(id: string) {
  return { total: 129.5, status: "shipped" };
}
async function fetchShipment(id: string) {
  return { carrier: "DHL", status: "in_transit" };
}
async function fetchCustomer(id: string) {
  return { name: "A. Muster", loyaltyTier: "gold" };
}

getOrderSummary("42").then((summary) => {
  console.log(JSON.stringify(summary, null, 2));
});
```

### Python (`asyncio.gather`, `return_exceptions=True`)

```python
import asyncio
from dataclasses import dataclass


@dataclass
class OrderSummary:
    order_id: str
    order: dict | None
    shipment: dict | None
    customer: dict | None
    partial: bool


async def fetch_order(order_id: str) -> dict:
    await asyncio.sleep(0.05)
    return {"total": 129.50, "status": "shipped"}


async def fetch_shipment(order_id: str) -> dict:
    await asyncio.sleep(0.05)
    return {"carrier": "DHL", "status": "in_transit"}


async def fetch_customer(order_id: str) -> dict:
    await asyncio.sleep(0.05)
    return {"name": "A. Muster", "loyalty_tier": "gold"}


async def with_timeout(coro, timeout_s: float):
    try:
        return await asyncio.wait_for(coro, timeout=timeout_s)
    except (asyncio.TimeoutError, Exception):
        return None


async def get_order_summary(order_id: str) -> OrderSummary:
    order, shipment, customer = await asyncio.gather(
        with_timeout(fetch_order(order_id), 0.4),
        with_timeout(fetch_shipment(order_id), 0.4),
        with_timeout(fetch_customer(order_id), 0.4),
    )
    return OrderSummary(
        order_id=order_id,
        order=order,
        shipment=shipment,
        customer=customer,
        partial=order is None or shipment is None or customer is None,
    )


async def main() -> None:
    summary = await get_order_summary("42")
    print(summary)


if __name__ == "__main__":
    asyncio.run(main())
```

### Go (goroutines joined over channels, no `errgroup` dependency)

```go
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"time"
)

type Order struct {
	Total  float64
	Status string
}

type Shipment struct {
	Carrier string
	Status  string
}

type Customer struct {
	Name        string
	LoyaltyTier string
}

type OrderSummary struct {
	OrderID  string    `json:"orderId"`
	Order    *Order    `json:"order"`
	Shipment *Shipment `json:"shipment"`
	Customer *Customer `json:"customer"`
	Partial  bool      `json:"partial"`
}

func fetchOrder(ctx context.Context, id string) (*Order, error) {
	return &Order{Total: 129.50, Status: "shipped"}, nil
}

func fetchShipment(ctx context.Context, id string) (*Shipment, error) {
	return &Shipment{Carrier: "DHL", Status: "in_transit"}, nil
}

func fetchCustomer(ctx context.Context, id string) (*Customer, error) {
	return &Customer{Name: "A. Muster", LoyaltyTier: "gold"}, nil
}

func getOrderSummary(id string) OrderSummary {
	ctx, cancel := context.WithTimeout(context.Background(), 400*time.Millisecond)
	defer cancel()

	orderCh := make(chan *Order, 1)
	shipmentCh := make(chan *Shipment, 1)
	customerCh := make(chan *Customer, 1)

	go func() {
		o, err := fetchOrder(ctx, id)
		if err != nil {
			orderCh <- nil
			return
		}
		orderCh <- o
	}()
	go func() {
		s, err := fetchShipment(ctx, id)
		if err != nil {
			shipmentCh <- nil
			return
		}
		shipmentCh <- s
	}()
	go func() {
		c, err := fetchCustomer(ctx, id)
		if err != nil {
			customerCh <- nil
			return
		}
		customerCh <- c
	}()

	summary := OrderSummary{OrderID: id}
	summary.Order = <-orderCh
	summary.Shipment = <-shipmentCh
	summary.Customer = <-customerCh
	summary.Partial = summary.Order == nil || summary.Shipment == nil || summary.Customer == nil

	return summary
}

func main() {
	summary := getOrderSummary("42")
	out, _ := json.MarshalIndent(summary, "", "  ")
	fmt.Println(string(out))
}
```

All three examples above were compiled or run directly against the toolchain
on this machine. `npx tsc --target es2020 --module commonjs --strict` then
`node` for the TypeScript file, `python3` (3.14) directly for the Python
file, and `go run` (go1.26) for the Go file. Each produced a merged
`OrderSummary` with `partial: false`, confirming the fan-out and merge logic
is correct when every backend answers. None of the three examples above
inject a slow backend, so none demonstrates the `partial: true` branch on
its own. Dimension 7's dynamics diagram and dimension 11's failure modes
cover that branch narratively, keyed to the same `partial` flag these
examples set.
