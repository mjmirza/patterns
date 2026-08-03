---
name: Gateway Routing
slug: gateway-routing
family: 08-cloud-distributed
category: Cloud and Distributed Systems
aliases: [Edge Routing, L7 Routing Gateway, API Gateway Routing, Reverse Proxy Routing]
first_described: "Microsoft Azure Architecture Center, Cloud Design Patterns catalog"
maturity: canonical
related: [gateway-aggregation, gateway-offloading, backends-for-frontends, circuit-breaker, service-discovery, strangler-fig, sidecar, ambassador]
incompatible_with: []
verified: 2026-08-02
---

# Gateway Routing

## 1. Name, aliases, and lineage

The canonical name is Gateway Routing. It is documented as one of three
gateway-family patterns in the Microsoft Azure Architecture Center's Cloud
Design Patterns catalog, alongside Gateway Aggregation and Gateway
Offloading, described as a way to "route requests to multiple services or
multiple service instances using a single endpoint" (Microsoft, Azure
Architecture Center, "Gateway Routing pattern",
https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-routing,
verified 2026-08-02). Microsoft's catalog is the closest thing this pattern
has to a formal, citable origin. The GoF catalog does not name it, because it
is a network-topology pattern rather than an object-oriented one, and it
postdates the microservices era the GoF book predates by a decade.

The name recurs under several aliases depending on which community is
speaking. Practitioners writing about API design call the same mechanism an
**API Gateway**, though that term is overloaded, see dimension 4 for why
"API Gateway" the product category and "Gateway Routing" the pattern are not
synonyms. Kubernetes and CNCF documentation calls the concept **Ingress**,
defined as "an API object that manages external access to the services in a
cluster, typically HTTP", where "traffic routing is controlled by rules
defined on the Ingress resource" (The Kubernetes Authors, Kubernetes
documentation, "Ingress",
https://kubernetes.io/docs/concepts/services-networking/ingress/, verified
2026-08-02). Service mesh literature calls the ingress-side component an
**edge proxy** or **L7 router**. Envoy's own documentation describes itself
plainly as "an L7 proxy and communication bus designed for large modern
service oriented architectures" that "supports a routing subsystem that is
capable of routing and redirecting requests based on path, authority,
content type, runtime values, etc." (Envoy Proxy project, "What is Envoy",
https://www.envoyproxy.io/docs/envoy/latest/intro/what_is_envoy, verified
2026-08-02). All four names, Gateway Routing, API Gateway routing, Ingress,
and L7 routing, describe the same structural idea. One addressable front
door, a rule table, many backends behind it.

The pattern is older in spirit than any of these names. Reverse proxies
performing path-based `location` routing existed in web server software
(Apache, then Nginx) long before "microservices" was a word, and the
pattern is best understood as that old reverse-proxy idea applied
deliberately at a service boundary, with the routing rules elevated to a
first-class, independently deployable configuration surface rather than
buried in a single web server's config file.

## 2. Problem and context

A client, whether a browser, a mobile app, or another service, needs to talk
to a system that is actually made of several independently deployed
backends. Three concrete shapes of this problem recur, and Microsoft's
catalog entry names all three explicitly.

**Disparate services behind one client.** An e-commerce storefront needs
search, a shopping cart, checkout, reviews, and order history. Each of these
is a separate deployable with its own API surface, its own release cadence,
and often its own team. If the client is coded to call each service at its
own address, then a decomposition (splitting a service in two), a
consolidation (merging two services back into one), or even a hostname
change forces a client release. In a mobile app, a client release means an
app-store review cycle measured in days, applied to backend refactoring
work that should take an afternoon.

**Multiple instances of the same service.** A service is deployed as N
replicas, possibly across regions, for load distribution or availability.
The set of live instances changes continuously as instances scale up, scale
down, fail health checks, or move between regions. A client that must track
which instances currently exist recreates service discovery inside every
client, which is exactly the kind of infrastructure logic clients should
never own.

**Multiple versions of the same service.** A team wants to run version 1.1
of a service alongside version 1.0, sending a small percentage of traffic to
the new version before a full rollout, the blue-green or canary deployment
shape. If clients pick the version, the rollout percentage becomes a
client-side configuration problem spread across every client instance in
the world, un-revertible without another client release.

The context that produces all three problems is the same underlying fact.
The address a client uses to reach "the system" and the actual topology of
services implementing that system are two different things, and that
difference changes over time faster than clients can be redeployed. Gateway
Routing exists to make that difference invisible to the client by fixing
one address and letting everything behind it move.

## 3. Forces

- **Coupling.** Favoured, for the client. The client is decoupled from
  backend topology entirely, it knows one hostname and a set of paths. The
  cost is pushed onto the gateway, which must now know the topology the
  client used to know.
- **Latency.** Sacrificed, in the strict sense. Every request now makes two
  network hops instead of one. Client to gateway, gateway to backend. In
  practice this hop is usually inside the same data center or the same
  cloud region and adds low single-digit milliseconds, but it is not zero,
  and a poorly placed gateway (see dimension 11) can add much more.
- **Operability and deployability.** Strongly favoured. A version rollout, a
  region failover, or a service split becomes a configuration change at one
  place instead of a coordinated multi-client release. Microsoft's own
  Well-Architected mapping credits the pattern for "safe deployment
  practices" and health-based routing to "only healthy nodes" (Microsoft,
  Azure Architecture Center, "Gateway Routing pattern", "Workload design"
  section, verified 2026-08-02).
- **Availability and blast radius.** Cuts both ways. The gateway can route
  around an unhealthy backend, improving availability at the backend layer.
  But the gateway itself becomes a single addressable point that, if it
  fails, takes every backend behind it offline from the client's point of
  view. Microsoft's catalog states this explicitly under "Issues and
  considerations". "The gateway service can introduce a single point of
  failure" (same source, verified 2026-08-02).
- **Public attack surface.** Favoured for security posture. Backend
  services can be moved off any public IP entirely and made reachable only
  through the gateway or a private network, shrinking what an attacker can
  address directly.
- **Cost and operational ownership.** Sacrificed in one sense, favoured in
  another. Running, scaling, and load-testing a gateway is new operational
  work with its own cost. In exchange, the routing logic that would
  otherwise be duplicated inside every service or every client is written
  and load-tested exactly once.
- **Scalability of the routing layer itself.** The gateway must scale to
  the sum of traffic for every backend behind it, not just one backend's
  share. A gateway sized for today's traffic becomes the bottleneck of
  tomorrow's traffic first, before any individual backend does.

A pattern that removed the single-point-of-failure risk entirely would not
be this pattern. Gateway Routing trades a distributed topology-awareness
problem for a concentrated availability and capacity-planning problem, and
the second is easier to solve well because it is one system to harden
instead of every client in the world.

## 4. Applicability and non-applicability

Reach for Gateway Routing when the following hold.

- A client consumes multiple services and you want it to know exactly one
  endpoint, so backend topology can change without a client release.
- Deployments need a strategy that shifts a percentage of traffic between
  service versions (canary, blue-green) and that percentage must be
  adjustable without touching client code.
- The system must expose a stable public address while the backend
  instance count changes for scaling or availability reasons.
- You need to route from an externally reachable endpoint to an internal
  or private address space, for example fronting a private virtual network
  or a cluster's internal service addresses with one public IP.
- You want to move traffic between regions, including for reasons such as
  regional carbon-intensity signals, which Microsoft's catalog names
  directly as a 2026-era use case (same source, "When to use this pattern",
  verified 2026-08-02).

Do NOT reach for Gateway Routing in these cases, and the reason matters as
much as the rule.

- **A single service, one or two endpoints total.** Microsoft's own catalog
  says this outright. The pattern "might not be suitable when you have a
  simple application that uses only one or two services" (same source,
  verified 2026-08-02). Adding a routing tier in front of one backend buys
  none of the topology-hiding benefit and adds a hop, an operational
  component, and a new single point of failure for no return.
- **The client already needs to make one call and get one combined
  response, not a routed call to one of several backends.** That is a
  different problem, chattiness reduction, and the matching pattern is
  Gateway Aggregation, covered against this one in dimension 12.
- **The cross-cutting need is security, protocol translation, or SSL
  termination, not "which backend handles this request".** That is Gateway
  Offloading's job. A gateway can, and usually does, do both offloading and
  routing at once, but naming the concern correctly matters when deciding
  what belongs in the gateway configuration versus what belongs in a
  backend.
- **Each client type (web, iOS, a partner integration) wants a genuinely
  different shaped API, not just a different backend behind the same
  shape.** That is the Backends for Frontends pattern's territory. Gateway
  Routing dispatches the same request shape to different destinations, it
  does not reshape the request or response per client.
- **You do not yet know your service boundaries, and adding a gateway would
  freeze a routing table around guesses.** Introduce Gateway Routing after
  the service seams stabilise enough that a path or host rule is a durable
  artifact, not before. An early, over-eager gateway becomes exactly the
  kind of change-resistant artifact the pattern exists to prevent
  elsewhere.
- **The team cannot commit to keeping the gateway highly available and
  properly load-tested.** Microsoft's catalog flags this directly, saying plainly
  to load test the gateway so it does not introduce cascading failures for
  the services behind it (same source, verified 2026-08-02). A gateway
  stood up without that discipline converts a distributed system's
  availability into the availability of one under-provisioned box.

## 5. Structure

- **Client.** Any caller, browser, mobile app, another service, or a
  partner integration. Knows exactly one address, the gateway.
- **Gateway (Router).** The single addressable entry point. Holds a
  routing table mapping request attributes, path prefix, hostname, header
  value, or a combination, to a destination. Performs Layer 7 (application
  layer) inspection of the request to make that decision. Microsoft's
  catalog states plainly "Gateway routing is level 7. It can be based on
  IP, port, header, or URL" (same source, verified 2026-08-02).
- **Routing rule set.** The configuration artifact, separate from
  application code, that expresses the mapping. This is the thing that
  changes on a deploy, a version rollout, or a region failover, and its
  separation from both client and backend code is the structural point of
  the whole pattern.
- **Backend (target service or service instance).** One of potentially
  many services, service versions, or service replicas that the gateway can
  route to. A backend has no awareness that a gateway sits in front of it,
  it simply receives requests as if directly addressed.
- **Health/discovery source (implicit participant in most real
  implementations).** Something, a service registry, a Kubernetes
  Endpoints object, DNS, or a static config, that tells the gateway which
  backend instances currently exist and are healthy. Not part of Microsoft's
  three-diagram description directly, but present in essentially every
  production instance of the pattern, see dimension 8 and dimension 9.

## 6. ASCII structure diagram

```
                         +-----------------------------+
                         |           Gateway            |
                         |  (single public endpoint)    |
                         |-------------------------------|
                         | Routing rule table:          |
                         |  /search*  -> search-svc     |
                         |  /orders*  -> orders-svc     |
                         |  /cart*    -> cart-svc       |
                         |  Host: v2.example.com -> v2  |
                         +---+-----------+-----------+--+
                             |           |           |
              path /search   |  path /orders  |  path /cart
                             v           v           v
                  +----------------+ +----------+ +----------------+
                  |  Search Svc    | | Orders   | |  Cart Svc      |
                  |  (N replicas)  | | Svc      | |  (N replicas)  |
                  +----------------+ +----------+ +----------------+

   Client never addresses Search, Orders, or Cart directly.
   It addresses only the Gateway, the rule table is the seam that moves.
```

```
        Same-service, multiple regions (availability / latency routing)

  Client --> Gateway --route by region/health--> Search Svc (region A)
                                              \-> Search Svc (region B)

        Same-service, multiple versions (canary / blue-green routing)

  Client --> Gateway --route by weight/header--> Search Svc v1.0 (95%)
                                              \-> Search Svc v1.1 (5%)
```

## 7. Dynamics

The gateway's decision happens once per inbound request, before any
backend sees the request at all. The routing decision is stateless per
request in the common case, a session-affinity variant, discussed in
dimension 8, is the exception.

```
Client              Gateway                          Backend (matched)
  |                    |                                      |
  |-- GET /orders/42 ->|                                      |
  |                    |-- inspect path, host, headers        |
  |                    |-- match against routing rule table   |
  |                    |     rule: prefix "/orders" -> orders |
  |                    |-- select a healthy instance          |
  |                    |   (from discovery/health source)     |
  |                    |-- forward request, same or new conn  |
  |                    |------------------------------------->|
  |                    |                                      |-- handles /orders/42
  |                    |<-------------------------------------|
  |<-- response -------|                                      |
  |                    |                                      |
```

When the rule table changes, for example a canary percentage moves from 5%
to 50%, the change takes effect on the NEXT request the gateway receives
after the configuration reload. In-flight requests already routed are
unaffected. This is the timing property that makes the pattern useful for
deployment strategy. The blast radius of a bad routing change is bounded to
requests that arrive after the change, and a revert is exactly as fast as
the next configuration reload, with no client involved.

```
      Rollout dynamics over time (canary shifting)

  t0: rule "orders -> v1.0 (100%)"
  t1: operator changes rule to "orders -> v1.0 (95%), v1.1 (5%)"
      -- reload, no client contacted, no client redeployed --
  t2: 5% of NEW inbound requests now reach v1.1
  t3: metrics on v1.1 look good, operator raises to "v1.0 (0%), v1.1 (100%)"
  t4: all NEW inbound requests reach v1.1, v1.0 can be decommissioned
```

## 8. Implementation variants

**Static path-prefix or host-based routing.** The simplest and most common
form. A fixed table maps a path prefix or hostname to a backend address.
This is exactly what Microsoft's catalog example shows using Nginx
`location` blocks, one per virtual directory, each `proxy_pass`-ing to a
different upstream (Microsoft, Azure Architecture Center, "Gateway Routing
pattern", "Example" section, verified 2026-08-02). Kubernetes Ingress
resources express the identical idea declaratively, with rules containing
"an optional host" and "a list of paths" each mapped to a "backend" service
(The Kubernetes Authors, Kubernetes documentation, "Ingress", verified
2026-08-02).

**Header or content-based routing.** The routing key is a request header,
a claim inside a JWT, or a query parameter rather than the path itself.
Used for tenant-based routing in multi-tenant systems (route by an
`X-Tenant-ID` header) or for API versioning by an `Accept` header instead
of a `/v2/` path segment. Envoy's routing subsystem explicitly supports
matching "based on path, authority, content type, runtime values, etc."
(Envoy Proxy project, "What is Envoy", verified 2026-08-02), which is this
variant generalised.

**Weighted or percentage-based routing (canary, blue-green, A/B).** The
same path maps to more than one backend, each carrying a weight that sums
to 100%. Used to shift traffic gradually to a new version. This variant
requires the routing decision itself to be probabilistic per request rather
than deterministic per path, which changes how the rule table is tested,
see dimension 15.

**Session-affinity (sticky) routing.** The gateway pins a client to the
same backend instance across a session, typically via a cookie the gateway
sets or a consistent hash of a client identifier. This is the one variant
that breaks the stateless-per-request property from dimension 7 and
reintroduces a form of coupling between the client's session and one
specific backend instance, which then needs to survive that instance's
restarts or be handled with a graceful drain.

**Retry-aware and health-aware routing.** The gateway consults a health
check result (active probes, or passive failure counting) before selecting
an instance, and can retry a failed request against a second instance
transparently to the client. Microsoft's Well-Architected mapping notes
that "Gateway routing enables you to route traffic to only healthy nodes in
your system" (Microsoft, Azure Architecture Center, "Gateway Routing
pattern", "Workload design" section, verified 2026-08-02). This variant is
where Gateway Routing starts to overlap with the Circuit Breaker pattern,
see dimension 13.

**Global versus regional gateway placement.** Microsoft distinguishes two
deployment shapes for the same pattern. A regional Layer 7 gateway (their
Application Gateway product) for fine-grained control such as balancing
traffic between virtual machines within a region, versus a global Layer 7
gateway (their Front Door product) for routing across multiple regions
(same source, "Issues and considerations" section, verified 2026-08-02).
The pattern is identical, the placement decides whether the routing
decision happens at the network edge globally or within a single data
center.

**Sidecar/service-mesh routing.** Rather than one centralised gateway,
routing logic runs as a proxy alongside every service instance (the sidecar
pattern), forming a mesh where "gateway" logic is distributed rather than
concentrated at one box. Envoy is the proxy most commonly deployed this
way, both as a standalone edge gateway and as the per-instance sidecar
proxy inside a mesh like Istio. This variant trades the single-point-of-
failure risk from dimension 3 for operational complexity across many more
moving parts, one proxy per instance instead of one gateway.

## 9. Known production uses

**Netflix Zuul.** Netflix's edge service is described in its own project
documentation as "an L7 application gateway that provides capabilities for
dynamic routing, monitoring, resiliency, security, and more", built to sit
at the edge of Netflix's cloud infrastructure and route incoming requests to
the correct backend service (Netflix, `Netflix/zuul` GitHub repository,
https://github.com/Netflix/zuul, verified 2026-08-02). Netflix moved from
the original blocking Zuul 1 to an asynchronous, non-blocking Zuul 2
specifically to sustain routing throughput at their scale, and the project
has since been adopted well beyond Netflix, integrated into Spring Cloud
and used by other companies including Riot Games as a central piece of API
infrastructure (same source, verified 2026-08-02).

**Kong Gateway.** Kong's own documentation states plainly that "an API
gateway is a reverse proxy that lets you manage, configure, and route
requests to your APIs" (Kong Inc., Kong Gateway documentation,
https://developer.konghq.com/gateway/, verified 2026-08-02). Kong's data
model is built around two entities named exactly for this pattern's
purpose. Services, representing the upstream backends Kong proxies to, and
Routes, which define "how incoming requests are directed to those
services" based on matching criteria including path, host, and header (same
source, verified 2026-08-02). Kong is deployed as an API gateway in front
of microservice backends across a wide range of production companies as a
commercial and open-source product.

**Kubernetes Ingress (and Ingress controllers such as ingress-nginx,
Traefik).** The Kubernetes project's own documentation defines Ingress as
managing "external access to the services in a cluster, typically HTTP",
where an Ingress resource's rules specify "an optional host" and a set of
paths each bound to a backend `Service`, and "HTTP (and HTTPS) requests to
the Ingress that match the host and path of the rule are sent to the listed
backend" (The Kubernetes Authors, Kubernetes documentation, "Ingress",
verified 2026-08-02). This is Gateway Routing standardised as a first-class
Kubernetes API object, implemented by any of several interchangeable
Ingress controllers, and is one of the highest-volume production instances
of the pattern given how widely Kubernetes itself is deployed.

**Envoy Proxy at Lyft and beyond.** Envoy, originally built at Lyft and now
a CNCF graduated project, is documented as "an L7 proxy and communication
bus" whose "routing subsystem" is "capable of routing and redirecting
requests based on path, authority, content type, runtime values, etc."
(Envoy Proxy project, "What is Envoy", verified 2026-08-02). Envoy's
out-of-process design, meaning it is a separate process any application in
any language can sit behind, is precisely what let it become the routing
data plane underneath Istio and other service meshes, as well as a
standalone edge gateway product (Envoy Gateway), all sharing the same
routing engine described in this dimension.

**Azure Application Gateway and Azure Front Door.** Microsoft's own catalog
names these as the reference Azure implementations of the pattern.
Application Gateway for regional Layer 7 routing, and Front Door for global
Layer 7 routing across multiple regions (Microsoft, Azure Architecture
Center, "Gateway Routing pattern", "Example" section, verified 2026-08-02).

## 10. Consequences

Positive.

- The client's contract with the system shrinks to one address, which
  makes backend decomposition, consolidation, and renaming free from the
  client's point of view.
- Traffic shifting for canary and blue-green deployments becomes a
  configuration change at one place, revertible in the time it takes the
  gateway to reload its rules, with zero client coordination.
- Unhealthy backend instances can be routed around transparently, raising
  perceived availability without any client-side retry logic.
- Public network exposure can be narrowed to one hardened front door,
  shrinking the attack surface of every backend behind it.
- Region and instance count changes never require a client release, which
  is the direct fix for the elasticity problem named in dimension 2.

Negative.

- The gateway is a new, concentrated single point of failure, explicitly
  called out in Microsoft's own catalog, and every request now depends on
  its availability, not just the backend's.
- Every request now costs an extra network hop and an extra hop's worth of
  serialization and connection overhead, even when small in absolute terms.
- The gateway must be capacity-planned for the SUM of traffic across every
  backend behind it, which is a different, larger scaling problem than any
  single backend faces.
- Debugging moves one layer away from the client's mental model, a client
  seeing an error must now determine whether the gateway, the routing
  decision, or the selected backend produced it.
- The routing rule table becomes a piece of infrastructure that itself
  needs review, versioning, and testing discipline, or it silently becomes
  the least-observed, highest-blast-radius config file in the system.

## 11. Failure modes and misuse

**The gateway becomes the outage.** Symptom. Every backend reports healthy
in its own dashboards, but every client-facing request fails or times out.
Cause. The gateway itself is under-provisioned, has run out of connections,
or has crashed, and because it is the single addressable front door, its
failure looks identical to a total system outage from outside. Fix. Run the
gateway as a horizontally scaled, load-balanced fleet behind its own health
checks, never as one instance, and load test the gateway itself under
realistic aggregate traffic, exactly as Microsoft's catalog warns.

**Business logic creeps into the routing layer.** Symptom. A rule table
that started as "path X goes to service Y" grows conditionals referencing
request bodies, user roles, and feature flags, until nobody can predict
where a given request will land without reading gateway configuration
alongside application code. Cause. Routing rules and business rules were
never kept separate, every "just one more special case" made the gateway
config Turing-complete by accretion. Fix. Push logic that depends on
request content or business state back into a backend or into Gateway
Aggregation's dedicated aggregation service, keep the routing table to
addressing decisions only (path, host, header, weight).

**Silent routing to a decommissioned or wrong-version backend.** Symptom.
A subset of users receive stale behavior for weeks after a "completed"
migration, and support tickets do not correlate with any single deploy.
Cause. A canary or blue-green weight was left non-zero after the rollout
was declared finished, so a fixed percentage of traffic quietly kept
hitting the old version indefinitely. Fix. Treat routing-weight changes as
auditable deploy events with an expiry check, and alert when a non-default
weight persists past a defined window.

**Cascading failure from unbounded gateway-to-backend retries.** Symptom.
One backend slows down, and the gateway's automatic retries against that
backend, intended to improve resilience, multiply the load the struggling
backend receives, taking it fully down. Cause. Health-aware retry routing
(dimension 8) with no retry budget or circuit breaker, so a slow backend is
hammered harder exactly when it can least afford it. Fix. Combine
health-aware routing with the Circuit Breaker pattern and bounded retry
budgets, never unlimited retries.

**Backends reachable directly, bypassing the gateway entirely.** Symptom.
A security review finds that backend services are still reachable on their
original public IPs or ports, months after a gateway was introduced to
"be the single entry point." Cause. The gateway was added in front of
clients that adopted it, but nothing removed the old direct network path,
so the security and consistency benefits of the pattern were only partial.
Fix. Firewall backend services to accept traffic only from the gateway's
address range or a private network, as Microsoft's catalog recommends under
"Issues and considerations."

**Path-matching ambiguity produces the wrong backend.** Symptom. A request
to `/ordersarchive` is silently routed to the `orders` service instead of a
404 or the intended target. Cause. Prefix matching (`/orders*`) was used
where exact or properly delimited matching (`/orders/*`) was intended, and
two rule prefixes overlapped in a way nobody tested. Fix. Test the routing
table itself as a first-class artifact, including negative cases for
near-miss paths, see dimension 15.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Gateway Routing | Gateway Aggregation | Gateway Offloading | Backends for Frontends | Client-side service discovery (no gateway) |
|---|---|---|---|---|---|
| What it decides | Which single backend handles this request | How to combine several backend calls into one response | Which cross-cutting concern (TLS, auth, throttling) to strip off the request | Which API shape a specific client type sees | Which backend instance to call, decided inside the client |
| Client complexity | Low. One address, one request out | Low. One address, one request out, one response in | Low. Client is unaware the concern was offloaded | Low per client type, one tailored API each | High. Client embeds discovery and load-balancing logic |
| Backend coupling to client type | None. Same rule serves any client | None. Aggregation is client-agnostic by default | None | Strong by design. One BFF per client type | None, but discovery logic is duplicated per client |
| Chattiness reduction | Not addressed. One inbound request maps to one outbound request | Directly addressed. That is its purpose | Not addressed | Can incidentally reduce it via a tailored shape | Not addressed, and often worse, since the client makes multiple direct calls |
| Deployment/version rollout control | Strong. Weighted routing is native to it | Not addressed | Not addressed directly | Not addressed directly | Weak. Rollout logic must live in every client |
| Single point of failure risk | Present, explicitly named by Microsoft's catalog | Present, same gateway usually hosts both | Present, same gateway usually hosts both | Present per BFF instance, smaller blast radius each | Absent as a gateway concern, but discovery service can still be one |
| Where cross-cutting concerns (TLS, auth) live | Not its job, though often colocated with it | Not its job, though often colocated with it | Exactly its job | Delegated to whichever gateway sits behind each BFF | Duplicated per client unless a shared library is used |
| Best fit | Many backends, one client, topology changes over time | One client operation needs data from many backends in one round trip | Many backends share an identical infrastructure concern | Multiple client types need genuinely different API shapes | Very small systems, or systems where an operator wants zero extra network hops |

Reading of the table. Gateway Routing answers "which one backend handles
this," Gateway Aggregation answers "how do I combine several backends into
one answer," and Gateway Offloading answers "what shared concern do I strip
off before the backend sees the request." Real production gateways
(Kong, Envoy, Azure Application Gateway) typically implement all three at
once, but the three are distinct DECISIONS, and conflating them in a rule
table is the business-logic-creep failure mode from dimension 11.
Client-side service discovery is the honest alternative to a gateway
entirely, and it wins only when the operational cost of a gateway fleet
outweighs the duplication cost of discovery logic living in every client,
which is rare outside very small systems or systems with a strict
zero-extra-hop latency budget.

## 13. Related and incompatible patterns

- **Gateway Aggregation.** A sibling gateway-family pattern solving a
  different problem, reducing round trips by combining several backend
  calls into one response, rather than choosing one backend among many. The
  two commonly live in the same physical gateway process, but as distinct
  configuration concerns, conflating them is the business-logic-creep
  failure mode in dimension 11. See Microsoft's own cross-reference between
  the two catalog entries.
- **Gateway Offloading.** The third sibling. Moving a shared, cross-cutting
  concern (TLS termination, authentication, rate limiting, protocol
  translation) into the gateway so backends do not each reimplement it.
  Gateway Routing decides WHERE a request goes, Gateway Offloading decides
  WHAT gets stripped off or handled centrally before it gets there. The
  same physical gateway frequently does both.
- **Backends for Frontends (BFF).** A structural cousin, not a substitute.
  A BFF is a per-client-type API tailoring layer, and it is commonly placed
  BEHIND a Gateway Routing layer (the shared edge gateway routes to the
  correct BFF, and the BFF then routes or aggregates further). Reach for
  BFF when the problem is "different clients need different shapes," not
  "which backend handles this."
- **Circuit Breaker.** Composes directly with the health-aware routing
  variant from dimension 8. A gateway that retries against unhealthy
  backends without a circuit breaker risks the cascading-failure mode in
  dimension 11, adding one gives the gateway a principled way to stop
  sending traffic to a backend that is failing rather than retrying
  blindly.
- **Service Discovery.** A near-mandatory implicit dependency, not
  optional. A gateway routing to "multiple instances of the same service"
  (dimension 2) needs to know which instances currently exist, that
  knowledge is exactly what a service discovery mechanism (DNS, a registry,
  Kubernetes Endpoints) supplies. Gateway Routing without a discovery
  source degenerates to a static, manually maintained instance list.
- **Strangler Fig.** Frequently the reason a gateway is introduced in the
  first place. During an incremental migration from a monolith to services,
  a routing gateway is the mechanism that lets traffic for a given path be
  redirected from the old monolith to a new extracted service, one path at
  a time, without the client ever noticing the migration is in progress.
- **Sidecar and Ambassador.** A distributed alternative structure for the
  same routing logic. Instead of one centralised gateway, a routing proxy
  runs alongside every service instance. Envoy deployed as an Istio sidecar
  is this variant, Envoy deployed as a standalone edge gateway is the
  centralised variant from dimension 5. The two are not incompatible, a
  real mesh topology often uses a centralised edge gateway for
  north-south (client-to-cluster) traffic and sidecars for east-west
  (service-to-service) traffic, both running the identical routing engine.
- **Load Balancer.** Overlaps heavily and is sometimes conflated with this
  pattern, but is narrower. A pure Layer 4 (TCP/UDP) load balancer
  distributes connections without inspecting HTTP content, it cannot make a
  path- or header-based decision. Gateway Routing specifically requires
  Layer 7 visibility, per Microsoft's catalog statement that "gateway
  routing is level 7." A Layer 4 load balancer often sits in front of a
  Layer 7 gateway rather than replacing it.

## 14. Refactoring path in and out

Introducing the pattern into a system that does not have it.

1. Inventory every address a client currently calls directly. This is the
   full list of things the new gateway must be able to reach and route to
   before any client is repointed.
2. Stand up the gateway with a routing table that is, for the first
   version, an exact mirror of the current direct-call topology, one rule
   per existing service, no behavior change yet.
3. Repoint ONE low-risk client, or a canary slice of one client's traffic,
   at the gateway instead of the direct backend addresses. Confirm
   behavior is identical before proceeding.
4. Repoint the remaining clients incrementally, monitoring gateway latency
   and error rate against the pre-gateway baseline at each step.
5. Once all client traffic flows through the gateway, firewall the backend
   services so they are reachable only from the gateway's network range,
   closing the direct-access path Microsoft's catalog warns must not be
   left open.
6. Only now begin using the gateway's routing flexibility for its actual
   payoff, weighted rollouts, region-aware routing, or service
   decomposition behind an unchanged client-facing path. Introducing this
   flexibility before step 5 risks debugging drift, where some traffic
   still bypasses the gateway and diverges from what the routing table
   claims is happening.

Removing the pattern when it stops earning its place. This is rare in
practice, since the elasticity and versioning problems the pattern solves
tend to persist for the life of a distributed system, but it does happen
when a system is deliberately consolidated back toward a monolith.

1. Confirm the routing table has settled to effectively one rule, one
   client type, one backend, with no active weighted rollouts or
   region-based branching. A gateway routing to one thing 100% of the time
   is a candidate for removal.
2. Reintroduce direct network reachability from client to backend
   gradually, mirroring step 5 above in reverse, and verify with the same
   canary discipline used to introduce the pattern.
3. Move any cross-cutting concern that had been colocated in the gateway
   (see Gateway Offloading) to wherever it will live post-removal before
   removing routing, so the two changes are not conflated in one risky
   step.
4. Decommission the gateway only after a full traffic-shift window has
   passed with the direct path proven stable, and only after backend
   firewalling is relaxed to allow the reintroduced direct client traffic.

## 15. Testing and verification

Easier because of the pattern.

- The routing table is a declarative artifact (an Nginx config, a
  Kubernetes Ingress manifest, a Kong Route definition) and can be unit
  tested in isolation from any running backend. Given a request shape, does
  the table select the expected backend, with no network call involved.
- Canary and blue-green rollouts become testable as configuration diffs.
  A weight change from 0% to 5% can be reviewed and simulated before it
  ever reaches production traffic.
- Backends can be tested completely independently of routing concerns,
  since from a backend's point of view it is simply receiving requests, the
  gateway's presence is invisible to backend-level tests.

Harder because of the pattern.

- End-to-end tests must now exercise the gateway itself, not just the
  backend, or a routing-table bug (the path-matching ambiguity from
  dimension 11) will never be caught by backend-only test suites.
- Weighted and probabilistic routing is inherently harder to assert
  deterministically, a test asserting "5% of requests reach v1.1" needs
  either a large sample size or a seam that lets the test fix the
  randomness source.

Techniques that apply.

- **Table-driven routing tests.** A test suite that feeds the routing
  engine a list of (request path, host, headers) tuples and asserts the
  expected backend selection for each, including the near-miss and
  ambiguous cases from dimension 11's path-matching failure mode. This is
  the single highest-value test for this pattern and should exist before
  any weighted or conditional rule is added.
- **Contract or smoke test against the gateway, not just the backend.** A
  small suite that runs the actual gateway configuration (in Kubernetes
  terms, applying the real Ingress manifest to a test cluster) and asserts
  real HTTP responses come back from the correct backend, catching drift
  between the declared routing intent and what the deployed gateway
  actually does.
- **Weight-injection for deterministic canary tests.** Rather than
  asserting a statistical distribution, inject a controllable randomness
  source (a header the test sets, or a seeded generator behind a feature
  flag) so a test can force "always route to v1.1" and assert that path
  deterministically, then separately assert the production configuration's
  declared weight without relying on live traffic sampling.
- **Chaos testing of the gateway itself.** Because the gateway is the
  single point of failure named in dimension 3, testing its behavior under
  its own failure (a gateway instance killed, a backend health check
  failing) is part of verifying the pattern was implemented correctly, not
  an optional extra.

## 16. Observability signals

What to record.

- Per-route request count, latency, and error rate, labelled by the
  matched rule (not just the backend), so a routing-table change's effect
  is visible independent of backend-level metrics.
- The routing decision itself, logged or traced as a span attribute (which
  rule matched, which backend instance was selected), so a support
  investigation can answer "where did this specific request go" without
  guessing from the rule table alone.
- Gateway-level saturation metrics distinct from any single backend's
  metrics. Open connection count, request queue depth, and gateway CPU and
  memory, since the gateway is capacity-planned against the sum of all
  backend traffic per dimension 10.
- Health-check pass and fail counts per backend instance, and how often
  the gateway routes around a failing instance, which is the direct signal
  for whether the health-aware variant (dimension 8) is doing its job.
- For weighted routing, the ACTUAL observed traffic split per backend
  version, compared against the CONFIGURED weight, catching the silent
  stale-weight failure mode from dimension 11 as a metric rather than a
  support ticket weeks later.

A healthy instance on a dashboard. Per-route latency tracks close to the
matched backend's own reported latency, with the gateway's own added
overhead a small, stable, near-constant delta. The observed traffic split
for any weighted rule matches its configured weight within normal
statistical noise. Gateway saturation metrics sit well under capacity even
at peak aggregate traffic across all routed backends.

A failing instance. Gateway-added latency grows disproportionately to
backend latency, pointing at gateway-side saturation rather than a backend
problem. A weighted rule's observed split has drifted from its configured
value, or has been stuck at a non-default value long past an expected
rollout window, either the stale-weight failure mode or a configuration
propagation bug. A backend's health-check failure count is climbing while
the gateway continues sending it a steady share of traffic, meaning the
health-aware routing path is not actually engaged. Or the per-route error
rate for one rule is elevated while the underlying backend's own reported
error rate is normal, which localises the fault to the gateway's routing or
proxying logic rather than to the backend itself.

## 17. Security and privacy implications

The pattern has real, not incidental, security implications, because it
concentrates the network path every client request travels through.

**Reduced attack surface, if enforced.** The strongest security benefit is
also conditional. Microsoft's catalog explicitly recommends limiting public
network access to backend services "by making the services only accessible
via the gateway or via a private virtual network" (Microsoft, Azure
Architecture Center, "Gateway Routing pattern", "Issues and considerations"
section, verified 2026-08-02). This benefit is only realised if that
firewalling is actually done, the backend-still-reachable-directly failure
mode in dimension 11 is precisely this benefit going unrealised.

**A single hardened choke point for authentication and inspection.**
Because every request passes through the gateway, it is a natural place to
enforce authentication, rate limiting, and web application firewall rules
consistently, rather than trusting every backend to implement them
identically. This is more properly the concern of Gateway Offloading, but
because the two patterns so often share one process, a routing-only
gateway that has no offloading concerns should still be evaluated for
whether request inspection at this choke point is being left on the table.

**Routing-table injection and confused-deputy risk.** If the routing
decision is influenced by a client-supplied header (the header-based
routing variant, dimension 8) without validating who is allowed to set that
header, a malicious client can potentially route its own request to an
internal-only backend the gateway would otherwise never expose, or spoof a
tenant identifier to reach another tenant's data. Any header used as a
routing key must be one the gateway itself sets or validates, never one
trusted verbatim from an untrusted client.

**A single point of observability and a single point of compromise.** The
same concentration that makes the gateway a good place to log and audit
every request also makes it an especially high-value target. Compromising
the gateway can expose the full backend topology, credentials used for
gateway-to-backend authentication, and the traffic of every client and
every backend at once. Gateway configuration changes deserve the same
change-control rigor as a production credential rotation, not the lighter
rigor sometimes applied to "just a routing rule."

On privacy specifically, the pattern is not neutral once request-level
logging (dimension 16) is in place. The gateway sees every path, header,
and, depending on configuration, every request body that flows through the
system, concentrated in one place rather than scattered across many
backends' own logs. That concentration is operationally valuable and
simultaneously a concentrated data-handling responsibility, gateway logs
containing paths, headers, or bodies with personal data need the same
retention and access controls as any other system holding that data, and
arguably tighter ones given how much traffic passes through one log
stream.

## Code examples

Three languages where a hand-rolled Layer 7 gateway is genuinely idiomatic
to write directly against the standard library, without a framework, which
keeps the routing decision itself visible rather than hidden inside a
product's configuration DSL. Each example starts two backend HTTP servers
in-process, then a gateway that inspects the request path and proxies to
the matching backend, then issues three requests, two that match a rule and
one that matches nothing, to show both the routed and the unmatched case
from dimension 6's structure diagram. Go is shown first because
`net/http/httputil.ReverseProxy` is the standard library's purpose-built
primitive for exactly this pattern. TypeScript and Python are shown next
because Node's and Python's standard `http` modules make the same shape
explicit at the socket level, which is useful for understanding what a
product gateway is doing underneath its configuration surface.

### Go

```go
package main

import (
	"fmt"
	"io"
	"log"
	"net/http"
	"net/http/httptest"
	"net/http/httputil"
	"net/url"
	"strings"
	"time"
)

type route struct {
	prefix string
	target *httputil.ReverseProxy
}

type gateway struct {
	routes []route
}

func (g *gateway) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	for _, rt := range g.routes {
		if strings.HasPrefix(r.URL.Path, rt.prefix) {
			rt.target.ServeHTTP(w, r)
			return
		}
	}
	http.Error(w, "no route matches "+r.URL.Path, http.StatusNotFound)
}

func newBackend(name string) *httptest.Server {
	return httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "%s handled %s", name, r.URL.Path)
	}))
}

func proxyFor(rawURL string) *httputil.ReverseProxy {
	u, err := url.Parse(rawURL)
	if err != nil {
		log.Fatal(err)
	}
	return httputil.NewSingleHostReverseProxy(u)
}

func main() {
	search := newBackend("search-service")
	defer search.Close()
	orders := newBackend("orders-service")
	defer orders.Close()

	gw := &gateway{routes: []route{
		{prefix: "/search", target: proxyFor(search.URL)},
		{prefix: "/orders", target: proxyFor(orders.URL)},
	}}

	front := httptest.NewServer(gw)
	defer front.Close()

	client := &http.Client{Timeout: 5 * time.Second}
	for _, path := range []string{"/search?q=shoes", "/orders/42", "/cart"} {
		resp, err := client.Get(front.URL + path)
		if err != nil {
			log.Fatal(err)
		}
		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		fmt.Printf("GET %-20s -> %d %s\n", path, resp.StatusCode, string(body))
	}
}
```

Run with `go run gateway.go`. Confirmed output.

```
GET /search?q=shoes      -> 200 search-service handled /search?q=shoes
GET /orders/42           -> 200 orders-service handled /orders/42
GET /cart                -> 404 no route matches /cart
```

`httputil.ReverseProxy` is the routing engine's core primitive. The
gateway's own logic is only the `strings.HasPrefix` rule table lookup in
`ServeHTTP`, and everything else, the actual proxying, is the standard
library's reverse-proxy implementation, the same mechanism a production
gateway builds a configuration DSL on top of.

### TypeScript

```typescript
import * as http from "node:http";
import type { AddressInfo } from "node:net";

interface Route {
  prefix: string;
  target: string;
}

function startBackend(name: string): Promise<http.Server> {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      res.writeHead(200, { "content-type": "text/plain" });
      res.end(`${name} handled ${req.url}`);
    });
    server.listen(0, () => resolve(server));
  });
}

function startGateway(routes: Route[]): http.Server {
  return http.createServer((req, res) => {
    const path = req.url ?? "/";
    const match = routes.find((r) => path.startsWith(r.prefix));
    if (!match) {
      res.writeHead(404);
      res.end(`no route matches ${path}`);
      return;
    }
    const upstream = http.request(
      match.target + path,
      { method: req.method, headers: req.headers, timeout: 5000 },
      (upstreamRes) => {
        res.writeHead(upstreamRes.statusCode ?? 502, upstreamRes.headers);
        upstreamRes.pipe(res);
      },
    );
    upstream.on("timeout", () => upstream.destroy(new Error("upstream timeout")));
    upstream.on("error", (err) => {
      res.writeHead(502);
      res.end(String(err));
    });
    req.pipe(upstream);
  });
}

function fetchOnce(gatewayUrl: string, path: string): Promise<string> {
  return new Promise((resolve, reject) => {
    http.get(gatewayUrl + path, { timeout: 5000 }, (res) => {
      let body = "";
      res.on("data", (chunk) => (body += chunk));
      res.on("end", () =>
        resolve(`GET ${path.padEnd(20)} -> ${res.statusCode} ${body}`),
      );
    }).on("error", reject);
  });
}

async function main() {
  const search = await startBackend("search-service");
  const orders = await startBackend("orders-service");
  const searchAddr = search.address() as AddressInfo;
  const ordersAddr = orders.address() as AddressInfo;

  const gateway = startGateway([
    { prefix: "/search", target: `http://127.0.0.1:${searchAddr.port}` },
    { prefix: "/orders", target: `http://127.0.0.1:${ordersAddr.port}` },
  ]);
  await new Promise<void>((resolve) => gateway.listen(0, resolve));
  const gatewayAddr = gateway.address() as AddressInfo;
  const gatewayUrl = `http://127.0.0.1:${gatewayAddr.port}`;

  for (const path of ["/search?q=shoes", "/orders/42", "/cart"]) {
    console.log(await fetchOnce(gatewayUrl, path));
  }

  gateway.close();
  search.close();
  orders.close();
}

main();
```

Compiled with `tsc --target es2020 --module commonjs` against `@types/node`
and run with `node`. Confirmed output.

```
GET /search?q=shoes      -> 200 search-service handled /search?q=shoes
GET /orders/42           -> 200 orders-service handled /orders/42
GET /cart                -> 404 no route matches /cart
```

The routing decision, `routes.find((r) => path.startsWith(r.prefix))`, is a
single line, deliberately, to make the point from dimension 5 concrete. The
structural core of Gateway Routing is a rule lookup, and everything a
production gateway product adds on top, health checks, weighted
distribution, TLS, is built around that one lookup rather than replacing
it.

### Python

```python
from __future__ import annotations

import threading
import urllib.error
import urllib.request
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer


def start_backend(name: str) -> HTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            body = f"{name} handled {self.path}".encode()
            self.send_response(200)
            self.send_header("content-type", "text/plain")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt: str, *args: object) -> None:
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


@dataclass
class Route:
    prefix: str
    target_port: int


def start_gateway(routes: list[Route]) -> HTTPServer:
    def make_handler() -> type[BaseHTTPRequestHandler]:
        class GatewayHandler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                match = next((r for r in routes if self.path.startswith(r.prefix)), None)
                if match is None:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(f"no route matches {self.path}".encode())
                    return
                upstream_url = f"http://127.0.0.1:{match.target_port}{self.path}"
                try:
                    with urllib.request.urlopen(upstream_url, timeout=5) as upstream:
                        self.send_response(upstream.status)
                        self.end_headers()
                        self.wfile.write(upstream.read())
                except urllib.error.URLError as exc:
                    self.send_response(502)
                    self.end_headers()
                    self.wfile.write(str(exc).encode())

            def log_message(self, fmt: str, *args: object) -> None:
                return

        return GatewayHandler

    server = HTTPServer(("127.0.0.1", 0), make_handler())
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def fetch_once(gateway_url: str, path: str) -> str:
    try:
        with urllib.request.urlopen(gateway_url + path, timeout=5) as resp:
            body = resp.read().decode()
            return f"GET {path:<20} -> {resp.status} {body}"
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        return f"GET {path:<20} -> {exc.code} {body}"


def main() -> None:
    search = start_backend("search-service")
    orders = start_backend("orders-service")

    gateway = start_gateway(
        [
            Route(prefix="/search", target_port=search.server_address[1]),
            Route(prefix="/orders", target_port=orders.server_address[1]),
        ]
    )
    gateway_url = f"http://127.0.0.1:{gateway.server_address[1]}"

    for path in ["/search?q=shoes", "/orders/42", "/cart"]:
        print(fetch_once(gateway_url, path))

    gateway.shutdown()
    search.shutdown()
    orders.shutdown()


if __name__ == "__main__":
    main()
```

Run with `python3 gateway.py`. Confirmed output.

```
GET /search?q=shoes      -> 200 search-service handled /search?q=shoes
GET /orders/42           -> 200 orders-service handled /orders/42
GET /cart                -> 404 no route matches /cart
```

Go, TypeScript, and Java are the languages where production gateways
(Envoy in C++ aside) are most commonly implemented or extended in practice.
Rust and Swift are omitted here because a hand-rolled reverse-proxy example
in either would repeat the identical `startswith`-and-forward shape already
shown three times above with no new idiom to demonstrate, and the pattern's
production instances (dimension 9) are not written in either language.

## 18. References

1. Microsoft. Azure Architecture Center, "Gateway Routing pattern".
   https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-routing
   Verified 2026-08-02. Source of the canonical definition, the three
   context-and-problem scenarios, the issues and considerations list, the
   when-to-use and when-not-to-use guidance, the Layer 7 statement, the
   Nginx example, and the Application Gateway and Front Door references.
2. Microsoft. Azure Architecture Center, "Gateway Aggregation pattern".
   https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-aggregation
   Verified 2026-08-02. Source for the discriminating comparison in
   dimension 4, dimension 12, and dimension 13 against Gateway Aggregation.
3. Microsoft. Azure Architecture Center, "Gateway Offloading pattern".
   https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-offloading
   Verified 2026-08-02. Source for the discriminating comparison in
   dimension 4, dimension 12, and dimension 13 against Gateway Offloading,
   and for the "business logic should never be offloaded to the gateway"
   principle echoed in dimension 11.
4. The Kubernetes Authors. Kubernetes documentation, "Ingress".
   https://kubernetes.io/docs/concepts/services-networking/ingress/
   Verified 2026-08-02. Source for the Ingress alias, the host-and-path
   rule model, and the Kubernetes production use in dimension 9.
5. Netflix. `Netflix/zuul` GitHub repository.
   https://github.com/Netflix/zuul
   Verified 2026-08-02. Source for the Zuul production use in dimension 9,
   the Zuul 1 to Zuul 2 asynchronous migration, and the Spring Cloud and
   Riot Games adoption note.
6. Kong Inc. Kong Gateway documentation.
   https://developer.konghq.com/gateway/
   Verified 2026-08-02. Source for the Kong production use in dimension 9
   and the Services-and-Routes data model description.
7. Envoy Proxy project. "What is Envoy".
   https://www.envoyproxy.io/docs/envoy/latest/intro/what_is_envoy
   Verified 2026-08-02. Source for the Envoy production use in dimension 9,
   the L7 proxy and routing-subsystem definition quoted in dimension 1 and
   dimension 8, and the out-of-process design note.
8. Go project. Go standard library documentation, `net/http/httputil`
   package, `ReverseProxy` type.
   https://pkg.go.dev/net/http/httputil#ReverseProxy
   Package documentation for the reverse-proxy primitive used in the Go
   code example. Not independently WebFetch-verified in this session, the
   API usage was verified empirically by compiling and running the example
   against the live package with `go run`, confirmed 2026-08-02.
9. Node.js project. Node.js documentation, `http` module,
   `http.request()` and `http.createServer()`.
   https://nodejs.org/api/http.html
   Package documentation for the primitives used in the TypeScript code
   example. Not independently WebFetch-verified in this session, the API
   usage was verified empirically by compiling with `tsc` and running with
   `node`, confirmed 2026-08-02.
10. Python Software Foundation. Python 3 documentation, `http.server` and
    `urllib.request` modules.
    https://docs.python.org/3/library/http.server.html
    Standard library documentation for the primitives used in the Python
    code example. Not independently WebFetch-verified in this session, the
    API usage was verified empirically by running the example with
    `python3`, confirmed 2026-08-02.
