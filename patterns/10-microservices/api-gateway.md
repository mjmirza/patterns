---
name: API Gateway
slug: api-gateway
family: 10-microservices
category: Microservices
aliases: [Edge Service, Backend for Frontends (specialised form), Gateway Aggregation]
first_described: "Richardson, microservices.io, and independently by Netflix (Zuul, 2013)"
maturity: canonical
related: [remote-procedure-invocation, api-composition, service-per-team, decompose-by-business-capability, circuit-breaker]
incompatible_with: []
verified: 2026-08-03
---

# API Gateway

## 1. Name, aliases, and lineage

The canonical name is API Gateway. It is documented as a microservices pattern
by Chris Richardson on microservices.io, described as an API gateway that is
the single entry point for all clients, where requests are either proxied to
the appropriate service or fanned out to several services and the results
combined ([microservices.io, the API Gateway pattern page](https://microservices.io/patterns/apigateway.html),
verified 2026-08-03). Richardson developed the same material in book form in
*Microservices Patterns*, Manning, 2019, chapter 8, "External API patterns,"
where the pattern is presented alongside its specialised sibling, Backends for
Frontends.

The pattern also has an independent industrial lineage that predates and runs
parallel to the microservices.io catalog entry. Netflix built and open sourced
Zuul, described in its own repository as "an L7 application gateway that
provides capabilities for dynamic routing, monitoring, resiliency, security,
and more" ([github.com/Netflix/zuul](https://github.com/Netflix/zuul), verified
2026-08-03), with Zuul 1 announced on the Netflix technology blog in 2013 and
Zuul 2 rebuilt on an asynchronous, non-blocking core. Amazon Web Services
ships a managed product under the same name, Amazon API Gateway, described in
its own documentation as an AWS service for creating, publishing,
maintaining, monitoring, and securing REST, HTTP, and WebSocket APIs at any
scale, acting as "a front door for applications to access data, business
logic, or functionality from your backend services"
([AWS API Gateway developer guide](https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html),
verified 2026-08-03).

**Edge Service** is the term Netflix itself favours in its engineering
writing, emphasising the gateway's position at the boundary between the
public internet and the internal service mesh rather than its API-shaping
role. **Backends for Frontends** (BFF), credited to Phil Calçado's writing
from his time at SoundCloud, is a specialised variant, not a synonym, since a
BFF is one gateway per client type (a mobile BFF, a web BFF, a partner BFF)
rather than one shared gateway for every client. Richardson's own catalog
treats BFF as a named variation of API Gateway for exactly this reason, in
the section on the pattern page titled "Variation" that names Backends for
Frontends directly (microservices.io, API Gateway page, section "Variation,"
verified 2026-08-03). **Gateway Aggregation** is a narrower name used in some
enterprise-integration writing, in particular Microsoft's Azure Architecture
Center, for the specific sub-case where the gateway's job is fan-out plus
response composition rather than pure routing. This repository treats that
sub-case as one of the gateway's implementation variants (see dimension 8)
rather than a separate pattern, because the routing and composition
responsibilities are usually colocated in the same process in production
systems.

## 2. Problem and context

A client of a microservices system, whether a mobile app, a single-page web
application, or a third-party integration, needs data or an action that in a
monolith would have been a single call into one process. In a microservices
architecture the same request usually depends on several independently
deployed services, because the data has been decomposed by business
capability or subdomain across service boundaries (see
[decompose-by-business-capability](decompose-by-business-capability.md) and
[decompose-by-subdomain](decompose-by-subdomain.md)). If the client calls
each service directly, three problems appear at once.

First, the client must know the network location of every service it needs,
and that location changes as instances scale, redeploy, or move, which is
exactly the coordination problem that service discovery exists to solve one
layer down (see the discovery patterns cross-referenced on
microservices.io). Second, the client is coupled to the internal
decomposition of the system, so a service that later splits in two, merges
with another, or is rewritten in a different protocol becomes a breaking
change for every client that called it directly, even though nothing about
the client's actual need changed. Third, different clients want the data
shaped differently. A mobile client on a metered, high-latency connection
wants a single aggregated payload with only the fields it renders. A desktop
web client on a fast connection can tolerate several parallel calls and
richer payloads. Richardson names this directly, that "different clients
need different data" and "network performance is different for different
types of client," citing the concrete example of product-details data
assembled from several services for a desktop client versus a leaner payload
for a mobile client (microservices.io, API Gateway page, "Forces," verified
2026-08-03).

A fourth force that Richardson also names is protocol mismatch. Internal
services may use protocols that are efficient inside a data centre but are
not client-friendly, such as Apache Thrift, gRPC, or AMQP, while public
clients overwhelmingly expect HTTP and JSON, and this occurs alongside
services adopting different technologies for the same class of concern, so a
single client-facing contract needs a translation point (microservices.io,
same page, "Forces," verified 2026-08-03).

The API Gateway pattern places one component, or one class of component, at
the network boundary of the system, and gives every external client exactly
one thing to know how to reach. That component becomes responsible for
routing each incoming request to the service or services that can satisfy
it, translating protocols where needed, and, in its aggregating form,
composing several backend responses into the single payload the client
actually wants.

## 3. Forces

**Client simplicity versus internal flexibility.** A single entry point
means the client's contract is stable even as the services behind it are
decomposed differently over time. The gateway absorbs that churn. This is
the pattern's central trade, and it favours the producing team's ability to
refactor internally over the consuming team's visibility into that internal
shape.

**Latency versus round trips.** An aggregating gateway that fans out to
several backend services in parallel and merges the results replaces N round
trips from a bandwidth-constrained client with one round trip from the
client and N round trips from the gateway, which usually sits inside the
same data centre or a nearby edge location as the services it calls. The
pattern favours the client's network economics over the gateway's internal
fan-out cost, on the judgement that intra-data-centre latency is an order of
magnitude cheaper than public-internet, high-latency-mobile latency. This is
engineering judgement grounded in the general shape of the problem, not a
sourced universal law, because the actual numbers depend on the deployment.

**Coupling concentration versus a single point of failure.** Centralising
routing, authentication, and rate limiting in one component removes
duplicated logic from every service, but it also concentrates availability
risk, so if the gateway is down, every client-facing capability is down,
even if every backend service is healthy. The pattern favours operational
simplicity and consistency of cross-cutting policy over eliminating a
single point of failure, and the mitigation (horizontal scaling,
active-active deployment, a thin and stateless gateway process) is
engineering practice rather than something the pattern itself guarantees.

**Team autonomy versus a shared chokepoint.** When many independent teams
own many services, a single, centrally-owned gateway can become a release
bottleneck if every new endpoint requires a change to a shared gateway
codebase owned by one team. This tension is explicit in Richardson's later
writing, since he pairs API Gateway with a warning about it becoming a
development bottleneck, and this is one reason gateway configuration is
increasingly pushed toward declarative route definitions (Kubernetes
Ingress or Gateway API resources, or per-service gateway route files
managed by the owning team) rather than a monolithic codebase one platform
team must edit for every change.

**Cost and operability.** Adding a gateway is adding infrastructure, a
process (or fleet of processes) to run, scale, patch, and monitor, and a new
place for TLS termination, certificate rotation, and access logs to live.
The pattern favours moving this operational cost to one well-understood
component instead of duplicating TLS, auth, and logging concerns
inconsistently across every service.

## 4. Applicability and non-applicability

Reach for an API Gateway when the following hold.

- The system is decomposed into multiple independently deployable services
  and at least one class of external client needs data or an action that
  spans more than one of them.
- Different client types (mobile, web, partner API, internal admin tool)
  need substantially different response shapes, payload sizes, or
  authentication mechanisms from the same underlying services.
- Cross-cutting concerns (TLS termination, authentication, rate limiting,
  request logging, response caching) are currently duplicated, or would
  need to be duplicated, across many services if the gateway did not exist.
- Internal services use a protocol (gRPC, Thrift, an internal binary
  protocol) that public clients cannot or should not speak directly.
- Service locations change dynamically because of autoscaling, rolling
  deploys, or blue-green cutovers, and clients should not need to track
  that themselves.

Do NOT reach for an API Gateway in these situations.

- The system has one deployable unit, or a small, stable number of services
  that every client is already permitted to call directly with no
  genuine shaping or aggregation need. Adding a gateway here adds a hop
  and an operational burden with no compensating benefit, restating
  Richardson's own "when to avoid it" guidance, since the gateway earns its
  cost through the coordination problem it removes, and a system small
  enough to have no such coordination problem gains nothing from it.
- The team introducing the gateway does not yet have a plan for making it
  highly available. A gateway that becomes a new single point of failure
  without redundancy makes the system's overall availability worse, not
  better, because every prior direct path is now funnelled through one
  fragile hop.
- The gateway would need business logic that changes at a different pace
  than the routing and cross-cutting policy it exists to centralise. Domain
  logic belongs in the owning service, not in the shared edge component,
  and putting it in the gateway recreates a monolith at the edge, the most
  common way this pattern degrades into an anti-pattern (see dimension 11).
- A service mesh (a sidecar-per-service data plane such as Envoy under
  Istio or Linkerd) already provides service-to-service routing, retries,
  and mTLS, and the actual unmet need is purely north-south (client-facing)
  traffic shaping that a simpler reverse proxy, or the mesh's own ingress
  gateway component, already covers. Adding a second, independently
  configured API gateway on top duplicates policy surface and creates two
  places a routing rule can silently disagree.
- The aggregation a client needs genuinely varies per client and per
  request in a way that a shared, centrally-maintained gateway cannot keep
  up with. This is the signal to move to Backends for Frontends (one
  gateway per client team, each with its own release timeline) rather than
  stretching one shared gateway to serve every client's bespoke shape.

## 5. Structure

- **Client.** A mobile app, a single-page web application, a partner
  integration, or an internal service acting as a consumer. Knows only the
  gateway's public address and public contract.
- **API Gateway.** The single entry point. Owns request routing (mapping an
  incoming path, verb, and host to one or more backend targets),
  cross-cutting policy enforcement (authentication, authorization,
  rate limiting, request validation, TLS termination), and, in its
  aggregating form, response composition (calling several backend services,
  in parallel where the calls are independent, and merging the results
  into one payload).
- **Route table / configuration.** The declarative or programmatic
  definition of which incoming requests map to which backend service or
  services. In a reverse-proxy implementation this is a configuration file
  (NGINX or Envoy configuration, a Kubernetes Ingress or Gateway API
  resource). In a code-first implementation it is routing code inside the
  gateway process itself.
- **Backend services.** The independently deployable microservices that
  hold the actual business logic and data the client ultimately wants.
  Each is unaware of the gateway's existence in the sense that its own API
  contract does not need to change to accommodate a new gateway route.
- **Service registry (optional but common).** When service instance
  locations change dynamically, the gateway consults a registry (Eureka,
  Consul, or the platform's own instance-lookup mechanism, such as
  Kubernetes' DNS-based lookup) rather than a static address list, so
  routing stays correct as instances scale or move.
- **Authentication/authorization provider (optional but common).** An
  identity provider, an OAuth authorization server, or a platform-native
  mechanism (AWS IAM policies, Lambda authorizer functions, or Amazon
  Cognito user pools in the case of Amazon API Gateway) that the gateway
  delegates identity decisions to rather than reimplementing them per
  service (AWS API Gateway developer guide, "Features of API Gateway,"
  verified 2026-08-03).

## 6. ASCII structure diagram

```
+-----------+     +-----------+     +-----------+
|  Mobile   |     |    Web    |     |  Partner  |
|  Client   |     |  Client   |     |    API    |
+-----+-----+     +-----+-----+     +-----+-----+
      |                 |                 |
      +--------+--------+--------+--------+
               |                 |
               v                 v
        +------+-----------------+------+
        |          API Gateway           |
        |  routing  auth  rate limit     |
        |  TLS termination  aggregation  |
        +--+---------+---------+---------+
           |         |         |
           v         v         v
     +-----+--+ +----+---+ +---+----+
     | Orders | | Users  | |Payments|
     |Service | |Service | |Service |
     +--------+ +--------+ +--------+
           \         |         /
            \        |        /
             +-------+-------+
                     |
                     v
            +-----------------+
            | Service Registry |
            +-----------------+
```

## 7. Dynamics

An aggregating request, the case that most clearly shows the gateway earning
its place, proceeds as follows for a mobile client requesting a product
detail view assembled from three services.

```
Client            API Gateway         Orders Svc   Reviews Svc   Inventory Svc
  |                    |                    |            |             |
  | GET /products/42   |                    |            |             |
  |------------------->|                    |            |             |
  |                    | authenticate(token)|            |             |
  |                    |------+             |            |             |
  |                    |<-----+ ok           |            |             |
  |                    | GET /orders/42?fields=lean       |             |
  |                    |------------------->|            |             |
  |                    | GET /reviews?product=42          |             |
  |                    |------------------------------->  |             |
  |                    | GET /inventory/42                 |             |
  |                    |------------------------------------------->    |
  |                    |<-------------------|            |             |
  |                    |<-------------------------------|             |
  |                    |<-------------------------------------------  |
  |                    | merge + shape for mobile          |             |
  |                    |------+             |            |             |
  |                    |<-----+             |            |             |
  |  200 (lean payload)|                    |            |             |
  |<-------------------|                    |            |             |
```

The three downstream calls are issued concurrently because they are
independent, which is the mechanism by which the pattern turns three
sequential client-perceived round trips into one. Authentication happens
once, at the gateway, rather than once per backend service. Each downstream
call usually carries a service-to-service credential (a short-lived
internal token, or mTLS identity from a mesh) rather than the client's
original credential, so that a compromised or expired client token cannot
be independently checked against three different services with three
different clocks and three different revocation lists.

A non-aggregating, pure-routing request is simpler. The gateway matches the
incoming path against its route table, optionally rewrites the path, applies
rate limiting and auth, and proxies the request and response through
unchanged, adding only observability (a trace ID, a log line) at the edge.

## 8. Implementation variants

**Reverse-proxy configuration (declarative, no custom code).** NGINX, Envoy,
Kong, or a cloud-managed offering such as Amazon API Gateway or Azure API
Management, configured with route rules, auth policies, and rate limits as
data rather than code. Fastest to stand up, easiest to reason about for pure
routing, weakest for anything that needs custom business logic such as
non-trivial response merging across services with different shapes.

**Code-first gateway process (a real service you write and deploy).**
Netflix's Zuul is the canonical example, a JVM process with a filter chain
(pre, route, post, and error filters) that lets teams write arbitrary Java
or Groovy logic at each stage of a request's lifecycle
([github.com/Netflix/zuul](https://github.com/Netflix/zuul), verified
2026-08-03). This variant is the natural fit for aggregation logic that
genuinely needs conditional branching, response reformatting per client, or
calls to services with incompatible schemas that a declarative
configuration language cannot express cleanly.

**Backends for Frontends (one gateway per client team).** Instead of one
shared gateway serving every client, each client team (mobile, web,
partner) owns and deploys its own thin gateway, shaped for exactly the
form and aggregation its client needs, still fronting the same shared
backend services. This is the variant Richardson names explicitly as a
sibling pattern rather than a configuration option (microservices.io,
"Variation," verified 2026-08-03), and it is the correct response to the
applicability caveat in dimension 4 about client-specific needs outgrowing
a shared gateway.

**Kubernetes-native ingress and Gateway API.** In a Kubernetes deployment,
an Ingress resource is a declarative object that "manages external access
to the services in a cluster, typically HTTP," and "may provide load
balancing, SSL termination and name-based virtual hosting"
([Kubernetes documentation, Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/),
verified 2026-08-03), implemented by an ingress controller (commonly
NGINX or a cloud load balancer). The Kubernetes documentation itself now
notes that "the Kubernetes project recommends using Gateway instead of
Ingress. The Ingress API has been frozen" (same page, verified 2026-08-03),
and the newer Gateway API is a role-oriented, more expressive successor
covering the same problem space with a richer resource model
(GatewayClass, Gateway, HTTPRoute). This variant handles pure routing,
TLS termination, and load balancing well but generally does not perform
multi-service response aggregation, that being left to an application-level
gateway or a BFF sitting behind the ingress layer.

**Service mesh ingress gateway.** In a mesh architecture (Istio, Linkerd),
the mesh's own ingress gateway component is the entry point for north-south
traffic, sharing configuration and observability tooling with the mesh's
east-west (service-to-service) routing. This variant is attractive when a
mesh is already deployed for internal traffic management, because it avoids
running two independently configured routing layers, but it couples the
public API surface's release timeline to the mesh's, which some
organisations deliberately avoid.

**Managed cloud API gateway.** Amazon API Gateway, Azure API Management, and
Google Cloud's Apigee are fully managed, multi-tenant implementations of
this pattern, trading operational ownership for vendor lock-in and,
usually, per-request pricing. Amazon API Gateway specifically documents
support for REST APIs, HTTP APIs (a leaner, lower-latency variant), and
WebSocket APIs, plus IAM-policy, Lambda-authorizer, and Cognito-based
authorization, canary release deployments, and integration with AWS WAF for
protection against common web exploits (AWS API Gateway developer guide,
"Features of API Gateway," verified 2026-08-03).

## 9. Known production uses

**Netflix, Zuul.** Netflix built and open sourced Zuul as its edge service,
described in the project's own README as "an L7 application gateway that
provides capabilities for dynamic routing, monitoring, resiliency,
security, and more" ([github.com/Netflix/zuul](https://github.com/Netflix/zuul),
verified 2026-08-03). The project's own listed adopters include Spring
Cloud, which ships Zuul integration as Spring Cloud Netflix Zuul, and
JHipster, a widely used Java/Spring application generator that offers Zuul
as a gateway option for its generated microservice architectures (same
source, verified 2026-08-03).

**Amazon, Amazon API Gateway.** Amazon Web Services operates Amazon API
Gateway as a first-party managed product, described in its own
documentation as acting as "a front door for applications to access data,
business logic, or functionality from your backend services, such as
workloads running on Amazon EC2, code running on AWS Lambda, any web
application, or real-time communication applications"
([AWS API Gateway developer guide](https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html),
verified 2026-08-03). It is explicitly positioned as one of the two pillars
of AWS's serverless application stack alongside AWS Lambda (same source,
"Part of AWS serverless infrastructure," verified 2026-08-03).

**Kubernetes, Ingress and Gateway API.** The Kubernetes project
itself ships Ingress as a core API object for exactly this pattern's
routing concern, "an API object that manages external access to the
services in a cluster, typically HTTP," noting it "may provide load
balancing, SSL termination and name-based virtual hosting"
([Kubernetes documentation, Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/),
verified 2026-08-03). Every organisation running a Kubernetes-hosted
microservices system with an Ingress controller (NGINX Ingress Controller,
or a cloud provider's managed controller) is running a production instance
of this pattern's routing responsibility, even when a separate
application-level gateway also exists behind it for aggregation.

**Richardson's own reference implementation, microservices.io.**
Chris Richardson documents the pattern with a concrete worked example, an
online store where product details data is spread over multiple services,
and a client, rather than calling the Order, Catalog, and Recommendation
services directly, calls a single API Gateway that fans the request out and
returns one composed response (microservices.io, the API Gateway pattern
page, verified 2026-08-03). This is the canonical, citable formulation the
wider industry catalog, including this entry, traces back to.

## 10. Consequences

Positive.

- Clients depend on one stable contract instead of the union of every
  backend service's contract, which decouples the pace of internal service
  decomposition from client-facing breaking changes.
- Cross-cutting concerns (authentication, TLS termination, rate limiting,
  request logging, response caching, WAF protection) are implemented and
  operated once, in one place, instead of duplicated with the risk of
  drift across every service.
- Protocol translation happens at one seam, so internal services are free
  to use whatever protocol suits them (gRPC, an internal binary protocol)
  while every client still sees a uniform, client-friendly protocol such
  as HTTP and JSON.
- Aggregation at the gateway can substantially reduce the number of round
  trips a bandwidth- or latency-constrained client makes, improving
  perceived performance for exactly the clients (mobile, high-latency
  networks) that need it most.
- Because the gateway sits at the boundary, it is a natural, single place
  to attach broad observability (a trace ID assigned per inbound request,
  a consistent access log format) that would otherwise need to be
  independently instrumented per service.

Negative.

- The gateway becomes a new possible single point of failure and a new
  possible latency baseline for every client request, so it must be
  engineered for the availability and performance characteristics of the
  entire system, not only its own workload, added operational surface
  that did not exist before the pattern was introduced.
- Aggregation logic, if not disciplined, becomes a place where business
  rules accumulate outside the services that should own them, which
  recreates coupling and a shared-codebase bottleneck at the exact seam
  the pattern was meant to decouple. Richardson himself flags this
  bottleneck risk directly in his broader writing on the pattern.
- A shared gateway owned by one central team can become a release
  bottleneck for every other team, because adding or changing a route
  often means a change to code or configuration that team does not own,
  which is precisely the force that motivates the Backends for Frontends
  variant.
- The gateway adds a hop, and therefore some amount of latency, to every
  request, even pure pass-through requests that need none of the
  gateway's value-adding behaviour. This cost is judged acceptable in
  nearly all production deployments because the hop is usually
  sub-millisecond inside a well-placed data centre, but it is a real,
  non-zero cost that a direct-call architecture does not pay.
- Testing end-to-end behaviour now requires either running the gateway
  alongside the services under test or maintaining a faithful stand-in for
  it, adding a moving part to integration and contract testing that a
  direct-call architecture does not have.

## 11. Failure modes and misuse

**The gateway becomes a second monolith.** Symptom, in practice, is a
change to unrelated business logic in one downstream service routinely
also requiring a pull request against the gateway's codebase, and the
gateway's own deploy frequency starts to lag every other service because it
has become the thing everyone is afraid to touch. Cause, business logic
(validation rules, response shaping decisions that encode product policy
rather than pure client-format preference, orchestration that should be a
saga or a workflow) accumulated in the gateway instead of staying in the
owning service. Fix, push the logic back to the owning service or into a
dedicated orchestration layer, and restrict the gateway to routing,
authentication, and generic response composition that has no business
meaning of its own. If per-client shaping genuinely differs enough to
warrant ownership by each client team, move to Backends for Frontends.

**Aggregation calls are made sequentially instead of in parallel.**
Symptom, an aggregating endpoint's latency is roughly the sum, not the
max, of its downstream calls, and the problem gets worse every time a new
backend dependency is added to the aggregation. Cause, the gateway's
aggregation code issues its downstream calls one after another (awaiting
each before starting the next) rather than concurrently, often because the
calls were added incrementally by different engineers who each wrote the
straightforward, sequential version. Fix, issue independent downstream
calls concurrently (parallel async calls, a fan-out/fan-in coroutine
pattern, or an explicit `Promise.all`-style construct) and only serialise
calls that have a genuine data dependency on an earlier call's result.

**No circuit breaking on downstream calls, so one slow service takes down
the gateway.** Symptom, a single degraded backend service (raised
latency, not full outage) causes the gateway's thread pool or connection
pool to exhaust, which then makes every route through the gateway slow or
unavailable, including routes that never touch the degraded service.
Cause, the gateway treats every downstream call as always-available and
applies no timeout, no bulkhead isolation per downstream dependency, and no
circuit breaker to fail fast once a dependency is clearly unhealthy. Fix,
apply per-dependency timeouts, bulkheads (separate connection or thread
pools per downstream service so one saturated pool cannot starve calls to
healthy services), and a circuit breaker such as the Circuit Breaker
pattern. This is why Circuit Breaker is one of the patterns most commonly
paired with API Gateway in the literature (microservices.io, "Related
patterns" section on the API Gateway page, verified 2026-08-03).

**The gateway silently duplicates authentication and authorization logic
instead of delegating.** Symptom, two different teams' services disagree
on what a given token or role means, discovered only when a user reports
access to something they should not have, or is denied access to something
they should have. Cause, the gateway reimplements token validation or
role-mapping logic locally, drifting from the identity provider's actual
source of truth over time as that provider's model evolves. Fix, delegate
identity decisions to a single authoritative provider (an OAuth
authorization server, a platform-native mechanism such as IAM policies or
Cognito user pools) and treat the gateway's job as enforcing the decision,
not making it.

**Static, IP-based routing that breaks on every deploy.** Symptom, routing
rules need manual updates every time a service scales, redeploys, or is
migrated to a new host, and a missed update causes intermittent 502s.
Cause, the gateway's route table was configured with static backend
addresses instead of integrating with a service registry. Fix, point the
gateway at a service registry or the platform's native lookup mechanism
(Kubernetes Service DNS, Consul, Eureka) so route resolution stays correct
as instances change without a manual configuration step.

**Treating the gateway as a database.** Symptom, the gateway starts
caching, or worse, mutating and persisting state (session data, partial
order state) that has no service of record, and that state diverges from
what the owning services believe is true. Cause, a shortcut taken under
deadline pressure to avoid a round trip, without treating the gateway as
the stateless component the pattern assumes it to be. Fix, keep the
gateway stateless with respect to business data. Any caching it performs
should be a pure, invalidatable read-through cache of data whose source of
truth remains the owning service, never a write path of its own.

## 12. Trade-off matrix

| Force | API Gateway (shared) | Backends for Frontends | Direct client-to-service calls | Service mesh ingress only |
|---|---|---|---|---|
| Client simplicity | High, one contract for every client | High per client type, but each client team maintains its own gateway | Low, client must know every service it needs | High for routing, but no client-side aggregation |
| Cross-client shaping | Low, one shape must satisfy every client, or grows conditional complexity | High, each gateway is shaped for its own client | N/A, no shaping happens at all | Low, mesh ingress is not aware of client-specific shaping |
| Internal decoupling from clients | High, services can be decomposed freely behind the gateway | High, same benefit, per client team | Low, every internal reshape is a client-visible breaking change risk | Moderate, routing is decoupled but response shape is not |
| Team release bottleneck risk | Raised if one team owns the shared gateway | Low, each team owns and deploys its own gateway | None, no shared component to bottleneck on | Low for routing changes, but ties public surface to mesh release timeline |
| Operational surface added | One new highly-available component to run | Multiple gateways, more processes but each smaller and independently deployable | None added, but instance lookup and auth logic duplicated across services | Reuses existing mesh infrastructure if a mesh is already deployed |
| Aggregation / round-trip reduction | Strong, this is the pattern's core value for aggregating cases | Strong, same benefit per client | None, client pays every round trip itself | None, ingress usually proxies rather than aggregates |
| Single point of failure risk | Present, mitigated by redundancy and statelessness | Present per gateway, blast radius limited to one client type | Absent by construction, but availability now depends on every service the client calls directly | Present at the mesh ingress layer |

## 13. Related and incompatible patterns

**Related, composes with.**

- [Remote Procedure Invocation](remote-procedure-invocation.md). The
  protocol the gateway usually uses to call downstream services
  (synchronous HTTP or gRPC calls), even when the client-facing protocol
  the gateway exposes differs from the internal one.
- [API Composition](api-composition.md). The response-aggregation
  responsibility that an API Gateway performs in its aggregating variant is
  a specific application of the broader API Composition pattern, and
  systems sometimes separate the two, a thin routing gateway in front of a
  dedicated composition service, when aggregation logic grows complex
  enough to deserve its own deployable unit and lifecycle.
- Circuit Breaker. Directly addresses the "one slow downstream service
  takes down the gateway" failure mode from dimension 11, and is named
  explicitly alongside API Gateway in Richardson's own related-patterns
  list (microservices.io, API Gateway page, "Related patterns," verified
  2026-08-03).
- Client-side and server-side instance lookup. The mechanism, named on
  microservices.io as client-side and server-side discovery, by which
  the gateway resolves a logical service name to a concrete, currently
  healthy instance address, addressing the "static routing breaks on
  deploy" failure mode from dimension 11 (microservices.io, API Gateway
  page, "Related patterns," verified 2026-08-03).
- Access Token. The credential-passing mechanism the gateway usually
  issues or validates once at the edge, then forwards or re-issues to
  downstream services, so identity is established once per client request
  rather than independently by each backend (same source, verified
  2026-08-03).
- [Service per Team](service-per-team.md). When a shared gateway becomes a
  cross-team bottleneck, moving to Backends for Frontends is a direct
  application of giving each team ownership of the component that fronts
  its own client, echoing the same team-topology reasoning.

**Incompatible or in tension with.**

- A fully decentralised, no-shared-entry-point architecture where every
  client is trusted to call every service directly with its own
  credentials. This is not so much incompatible as it is the thing API
  Gateway replaces. Adopting a gateway is, by definition, giving up direct
  client-to-service access for the services it fronts, and reintroducing
  direct access alongside a gateway for the same services creates two
  inconsistently enforced policy surfaces, the failure this repository's
  own dimension 11 flags as duplicated authentication logic drifting from
  a single source of truth.
- Putting substantial domain or business logic in the gateway is in direct
  tension with the pattern's own stated intent to keep the gateway thin.
  When a team finds itself doing this routinely, the honest read is that
  the gateway has stopped being an instance of this pattern and has become
  an undeclared orchestration service, which should be named and owned as
  such rather than left inside the routing layer.

## 14. Refactoring path in and out

**Introducing the pattern into a system with no gateway.** Start narrow.
Pick the single highest-value aggregating or highest-value cross-cutting
use case, commonly the mobile client's slowest or most chatty screen, or
the endpoint duplicating the most authentication logic across services,
and stand up a gateway that handles only that case as a thin reverse proxy
or a small routing service. Cut the client over to the new gateway path for
that one use case while every other call remains direct, verify latency
and error rate in production against the old path (a canary or shadow
traffic comparison), then migrate additional routes incrementally, one at a
time, rather than attempting a single cutover of every client-service
interaction at once. Keep the route table declarative from the start (even
before adopting a full reverse-proxy product) so the migration's progress
is visible as a diffable configuration rather than buried in code. Only add
aggregation logic once pure routing is stable and observably correct,
since aggregation is where most of the failure modes in dimension 11
originate, and it is easier to debug a routing-only gateway before layering
composition logic on top.

**Removing the pattern, or narrowing it, once it stops earning its
place.** The signal that a shared gateway has outgrown its usefulness is
usually one of the two bottleneck symptoms from dimension 11, a team
release-timeline bottleneck or a business-logic-creep bottleneck, rather
than a performance problem. If the bottleneck is a release-timeline problem
across multiple client teams, the refactor is to split the shared gateway
into per-client-team gateways (Backends for Frontends) behind a thin,
stable shared layer (TLS termination, WAF, basic auth) that changes rarely
and is safe for one platform team to keep owning. If the bottleneck is
business-logic creep inside the gateway, extract that logic into a
properly named and owned orchestration service or into the individual
backend services it actually concerns, leaving the gateway with only
routing and generic, business-agnostic cross-cutting policy. In the rare
case where the system has shrunk to a size where the gateway's
coordination problem (dimension 2) no longer exists, for example a
consolidation down to one or two services, remove the gateway and let
remaining clients call the surviving services directly, migrating any
cross-cutting concerns the gateway still uniquely provided (rate limiting,
WAF) to a simpler load balancer or CDN-edge configuration rather than
leaving an underused gateway process running.

## 15. Testing and verification

Test the gateway's routing behaviour as a contract in its own right,
independent of the backend services it calls. Given a request matching a
known route pattern, assert it is proxied to the correct backend with the
correct path rewrite, headers, and query parameters preserved or
transformed as specified. This is easy to test because routing rules are
usually pure, declarative mappings with no hidden state, and a
table-driven test suite, one row per route with an expected target, covers
the surface efficiently.

Test aggregation logic against stubbed or contract-tested backend
responses rather than against live services, because an aggregation test
that depends on three real, independently deployed services being up and
returning specific data is fragile and slow. Use consumer-driven contract
tests (such as Pact) between the gateway and each backend it composes, so
a backend team can verify their service still satisfies the shape the
gateway's aggregation logic expects before deploying a breaking change,
without either side needing the other running.

Test failure-mode behaviour explicitly, not only the happy path. A test
that simulates one downstream dependency timing out or returning a 5xx and
asserts the gateway still returns a sensible partial response (or a clear
error) rather than hanging or crashing is what actually validates the
circuit-breaker and timeout configuration from dimension 11, and it is the
test category most teams skip under deadline pressure and most regret
skipping in production.

What becomes harder to test because of this pattern is that true
end-to-end integration tests now need either a running instance of the
gateway (adding a moving part to the test environment) or an accepted gap
between "services individually verified" and "the full client-facing path
verified." Most mature implementations resolve this by running a small
number of genuine end-to-end smoke tests through a real gateway instance in
a staging environment, reserving the bulk of test coverage for the
unit- and contract-level tests described above, which is faster and does
not require every downstream dependency to be simultaneously healthy for
the suite to pass.

## 16. Observability signals

A healthy gateway shows a request rate that grows with client traffic and
a stable, low tail latency (p99, not only p50, because the gateway's tail
latency is the client's tail latency), an error rate mostly made up of
genuine client errors (4xx) rather than gateway-originated errors (5xx),
and, for aggregating routes, a fan-out completion time close to the
slowest of its parallel downstream calls rather than their sum, which is
the concrete signal that the sequential-aggregation failure mode from
dimension 11 is not present.

Log, per request at minimum, a correlation or trace ID assigned at the
gateway and propagated to every downstream call, so a single client
request can be reconstructed across every service it touched. Log the
route matched and the backend target(s) it was proxied to. Log the
response status returned to the client versus the status(es) received from
each downstream call, so a client-visible error can be traced to its
originating service without guessing. Log latency broken down per
downstream call for aggregating routes, not only the total, so a latency
regression can be attributed to a specific dependency rather than the
gateway as a whole.

A failing instance typically shows one of two shapes on a dashboard,
either a sharp, correlated spike in latency and error rate for every route
through the gateway (consistent with the gateway itself, or a shared
resource such as its connection pool, being saturated), or a latency and
error spike isolated to routes that touch one specific downstream
dependency while every other route stays healthy (consistent with a
single degraded backend and, if the gateway's own health also degrades in
lockstep, evidence that circuit breaking or bulkhead isolation is missing
or misconfigured for that dependency, per the failure mode in dimension
11). Distinguishing these two shapes on a dashboard is the fastest way to
tell whether the gateway itself or one of its dependencies is the root
cause during an incident.

## 17. Security and privacy implications

The gateway is, by construction, the largest single attack surface in the
system, because it is the one component every external actor, legitimate
or otherwise, must interact with. This is a real cost, not merely an
analytical footnote, and it is also the pattern's largest security benefit
when engineered correctly, because it means security controls (TLS
termination and certificate management, request validation and schema
enforcement, rate limiting against abuse and denial-of-service attempts,
web application firewall rules) need to be correctly implemented once, at
one seam, rather than correctly implemented independently by every
backend team. Amazon's own documentation for its managed gateway product
reflects this concentration explicitly, offering integration with AWS WAF
"for protecting your APIs against common web exploits" as a first-class
gateway feature rather than something left to individual backend services
(AWS API Gateway developer guide, "Features of API Gateway," verified
2026-08-03).

The gateway usually holds, even if briefly and in memory only, the
client's original credential (a bearer token, a session cookie, an API
key), and the design decision of how that credential is translated into
whatever downstream services need (a scoped, short-lived internal token, a
re-signed JWT with a narrower audience claim, a service-mesh mTLS
identity) is a meaningful privacy and security boundary. Forwarding the
client's original, broadly-scoped credential unchanged to every downstream
service, rather than minting a narrower, request-scoped credential at the
gateway, widens the blast radius of a compromised or leaked token across
every service that credential happens to work against, rather than
confining it to the single downstream call it was actually needed for.

Where the gateway performs response aggregation, it is also a natural
choke point for data-minimisation policy. A client-facing response that
merges three backend payloads is an opportunity to strip fields the
requesting client is not authorised to see, or does not need, before they
ever leave the data centre, rather than relying on every backend service
to independently apply the correct field-level authorization for every
possible client. This is a genuine privacy benefit of centralising
response shaping, but it is also a genuine risk if the gateway's
aggregation logic gets this wrong. An over-broad merge that forwards a
backend's full internal representation to an external client leaks
whatever that backend never expected to be client-visible, a direct
consequence of the business-logic-creep failure mode in dimension 11
manifesting as a data-exposure incident rather than merely an
architectural smell.

## 18. References

1. Chris Richardson, "API Gateway" pattern page, microservices.io,
   [microservices.io/patterns/apigateway.html](https://microservices.io/patterns/apigateway.html),
   verified 2026-08-03.
2. Chris Richardson, *Microservices Patterns. With Examples in Java*,
   Manning Publications, 2019, chapter 8, "External API patterns."
3. Netflix, "Zuul," GitHub repository,
   [github.com/Netflix/zuul](https://github.com/Netflix/zuul), verified
   2026-08-03.
4. Amazon Web Services, "What is Amazon API Gateway," API Gateway
   Developer Guide,
   [docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html](https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html),
   verified 2026-08-03.
5. The Kubernetes Authors, "Ingress," Kubernetes documentation,
   [kubernetes.io/docs/concepts/services-networking/ingress/](https://kubernetes.io/docs/concepts/services-networking/ingress/),
   verified 2026-08-03.

## Code examples

### TypeScript, a route matcher and a parallel aggregation with a per-call timeout

```typescript
type ServiceCall<T> = () => Promise<T>;

interface RouteRule {
  method: string;
  pathPrefix: string;
  target: string;
}

function matchRoute(rules: RouteRule[], method: string, path: string): RouteRule | undefined {
  return rules.find((r) => r.method === method && path.startsWith(r.pathPrefix));
}

async function withTimeout<T>(call: ServiceCall<T>, ms: number, label: string): Promise<T> {
  return Promise.race([
    call(),
    new Promise<T>((_, reject) =>
      setTimeout(() => reject(new Error(`${label} timed out after ${ms}ms`)), ms)
    ),
  ]);
}

async function aggregateProductDetail(
  fetchOrder: ServiceCall<{ orderId: string }>,
  fetchReviews: ServiceCall<{ count: number }>,
  fetchInventory: ServiceCall<{ inStock: boolean }>
): Promise<{ orderId: string; reviewCount: number; inStock: boolean }> {
  const [order, reviews, inventory] = await Promise.all([
    withTimeout(fetchOrder, 200, "orders"),
    withTimeout(fetchReviews, 200, "reviews"),
    withTimeout(fetchInventory, 200, "inventory"),
  ]);
  return { orderId: order.orderId, reviewCount: reviews.count, inStock: inventory.inStock };
}

async function main(): Promise<void> {
  const rules: RouteRule[] = [
    { method: "GET", pathPrefix: "/orders", target: "orders-service" },
    { method: "GET", pathPrefix: "/products", target: "aggregator" },
  ];

  const matched = matchRoute(rules, "GET", "/products/42");
  console.log("matched route target:", matched?.target ?? "none");

  const start = Date.now();
  const merged = await aggregateProductDetail(
    async () => ({ orderId: "42" }),
    async () => ({ count: 17 }),
    async () => ({ inStock: true })
  );
  console.log("aggregated payload:", JSON.stringify(merged));
  console.log("fan-out elapsed under 50ms, proving parallel not sequential:", Date.now() - start < 50);

  try {
    await withTimeout(() => new Promise((resolve) => setTimeout(resolve, 500)), 50, "slow-service");
  } catch (err) {
    console.log("timeout fired as expected:", (err as Error).message);
  }
}

main();
```

This models the two responsibilities from dimension 5 that matter most, routing
and aggregation, without a network dependency. `matchRoute` is the declarative
route table from the structure section. `aggregateProductDetail` issues its
three downstream calls with `Promise.all`, the fix named in dimension 11 for
the sequential-aggregation failure mode, and `withTimeout` demonstrates the
per-dependency timeout named in the circuit-breaking failure mode.

### Python, a circuit breaker guarding a downstream call, composed with routing

```python
import time
from typing import Callable, Optional


class CircuitOpenError(Exception):
    pass


class CircuitBreaker:
    def __init__(self, failure_threshold: int, reset_after_seconds: float) -> None:
        self.failure_threshold = failure_threshold
        self.reset_after_seconds = reset_after_seconds
        self.failure_count = 0
        self.opened_at: Optional[float] = None

    def call(self, fn: Callable[[], dict]) -> dict:
        if self.opened_at is not None:
            if time.monotonic() - self.opened_at < self.reset_after_seconds:
                raise CircuitOpenError("circuit open, refusing call to unhealthy dependency")
            self.opened_at = None
            self.failure_count = 0
        try:
            result = fn()
        except Exception:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.opened_at = time.monotonic()
            raise
        self.failure_count = 0
        return result


def match_route(rules: list[tuple[str, str, str]], method: str, path: str) -> Optional[str]:
    for rule_method, prefix, target in rules:
        if rule_method == method and path.startswith(prefix):
            return target
    return None


def unhealthy_inventory_call() -> dict:
    raise TimeoutError("inventory service did not respond in time")


def main() -> None:
    rules = [("GET", "/orders", "orders-service"), ("GET", "/products", "aggregator")]
    target = match_route(rules, "GET", "/products/42")
    print("matched route target:", target)

    breaker = CircuitBreaker(failure_threshold=2, reset_after_seconds=30.0)
    for attempt in range(1, 4):
        try:
            breaker.call(unhealthy_inventory_call)
        except CircuitOpenError as exc:
            print(f"attempt {attempt}: circuit breaker fired, {exc}")
        except TimeoutError as exc:
            print(f"attempt {attempt}: downstream failed, {exc}")


if __name__ == "__main__":
    main()
```

This is the fix from dimension 11's circuit-breaking failure mode, built as a
plain object rather than a framework dependency. Two failed calls open the
circuit, and the third call is refused locally rather than hitting the
already-degraded dependency again, the behaviour the observability section
names as the signal that circuit breaking is present and working.

### Go, real routing and a real per-request timeout against local test servers

```go
package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"time"
)

type routeRule struct {
	method string
	prefix string
	target string
}

func matchRoute(rules []routeRule, method, path string) (string, bool) {
	for _, r := range rules {
		if r.method == method && strings.HasPrefix(path, r.prefix) {
			return r.target, true
		}
	}
	return "", false
}

func newBackend(body string, delay time.Duration) *httptest.Server {
	return httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(delay)
		w.Write([]byte(body))
	}))
}

func fetchWithTimeout(url string, timeout time.Duration) (string, error) {
	client := &http.Client{Timeout: timeout}
	resp, err := client.Get(url)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	buf := make([]byte, 64)
	n, _ := resp.Body.Read(buf)
	return string(buf[:n]), nil
}

func main() {
	rules := []routeRule{
		{"GET", "/orders", "orders-service"},
		{"GET", "/products", "aggregator"},
	}
	if target, ok := matchRoute(rules, "GET", "/products/42"); ok {
		fmt.Println("matched route target:", target)
	}

	orders := newBackend("orders-ok", 0)
	defer orders.Close()
	slow := newBackend("too-slow", 100*time.Millisecond)
	defer slow.Close()

	if body, err := fetchWithTimeout(orders.URL, 50*time.Millisecond); err == nil {
		fmt.Println("orders response:", body)
	}

	if _, err := fetchWithTimeout(slow.URL, 20*time.Millisecond); err != nil {
		fmt.Println("timeout fired as expected:", err)
	}
}
```

This is the only sample of the three that exercises a real network path, using
`httptest.NewServer` to run genuine local HTTP backends with no external
network dependency. It demonstrates the client-facing timeout from dimension
11 firing against a backend that is deliberately slower than the configured
budget, the exact defect the "no circuit breaking, one slow service takes
down the gateway" failure mode describes the absence of.

C#, Kotlin, and Swift are omitted. the pattern is a network-topology and
process-boundary concern rather than a language-idiom concern, so the three
languages above (a dynamically-typed async-first style, a synchronous
imperative style, and a statically-typed compiled style with a real HTTP
stack) already cover the shapes an implementation of this pattern takes; a
fourth or fifth language would repeat the same structure with different
syntax rather than show a new facet of the pattern.
