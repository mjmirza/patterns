---
name: Load Balancing
slug: load-balancing
family: 08-cloud-distributed
category: Traffic Distribution
aliases: [Load Sharing, Server Load Balancing, Traffic Distribution]
first_described: "IETF RFC 2391, Load Sharing using IP Network Address Translation (LSNAT), August 1998"
maturity: canonical
related: [circuit-breaker, health-endpoint-monitoring, sharding, gateway-routing, rate-limiting, consistent-hashing, client-side-service-discovery, server-side-service-discovery]
incompatible_with: []
verified: 2026-08-22
---

# Load Balancing

## 1. Name, aliases, and lineage

The canonical name is Load Balancing. Earlier and adjacent literature also calls
it Load Sharing or Server Load Balancing, and both terms still appear in vendor
and standards documents today.

The earliest formal definition found in IETF literature is RFC 2391, Load
Sharing using IP Network Address Translation, published in August 1998. The RFC
states the trigger condition plainly. session load can be spread across a pool
of servers instead of directed to one, because a single server is not able to
cope with increasing demand for multiple sessions at the same time
([RFC 2391](https://datatracker.ietf.org/doc/html/rfc2391), verified
2026-08-22). The RFC also names and critiques the informal technique already in
wide use at the time, round robin DNS, pointing out that DNS answers can take
minutes to change and so cannot track real-time server load.

Dedicated hardware for this problem predates the RFC by two years. F5 was
founded in February 1996 and shipped its first hardware appliance, BIG-IP, in
1997, to direct traffic away from an overloaded server ([Wikipedia, F5,
Inc.](https://en.wikipedia.org/wiki/F5_Networks), verified 2026-08-22). This date
rests on a single tertiary source rather than a primary company record, noted
here at moderate confidence rather than as a settled fact.

Software load balancing at planet scale has a better documented lineage.
Google built Maglev, a load balancer that runs as a distributed software system
on ordinary Linux servers, specifically because the hardware appliances it had
been using ran into a scale ceiling per unit, gave only 1 plus 1 redundancy, and
were slow and costly to change. Maglev has carried Google's traffic since 2008
and now also sits under Google Cloud's passthrough network load balancers
(Eisenbud et al., Google Research, [Maglev, A Fast and Reliable Software
Network Load Balancer](https://research.google/pubs/maglev-a-fast-and-reliable-software-network-load-balancer/),
verified 2026-08-22, presented at USENIX NSDI 2016 per the paper's own section
3.4 as cited by [Envoy's Maglev load balancer
documentation](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/load_balancing/load_balancers),
verified 2026-08-22).

One negative finding is worth recording so it is never miscited. Dan Kegel's
widely referenced C10K document, on handling ten thousand simultaneous
connections, is about tuning a single server's I/O and threading model. It does
not cover distributing load across multiple servers and should not be cited as
a load balancing source ([kegel.com/c10k.html](http://www.kegel.com/c10k.html),
verified 2026-08-22).

## 2. Problem and context

A service running on one machine has a hard ceiling on the traffic it can
handle. Past that ceiling, requests queue, latency climbs, and eventually the
machine refuses new connections outright. Adding a second machine solves the
capacity problem only if something decides, for every incoming request, which
of the machines should answer it, and only routes to a machine that is actually
able to answer.

Cloudflare frames the everyday version of this problem with a grocery store
analogy. one open checkout lane creates a long line and slow service; opening
all eight lanes cuts the wait sharply. The same shape applies to a web service.
without something spreading requests across servers, one overloaded server
degrades the whole application even while its neighbors sit idle
([Cloudflare, What Is Load Balancing](https://www.cloudflare.com/en-gb/learning/performance/what-is-load-balancing/),
verified 2026-08-22).

AWS's own framing ties load balancing to two separate goals that are easy to
conflate. capacity (spreading work so no single compute resource is
overloaded) and fault tolerance (routing only to targets that pass a health
check, so a broken instance stops receiving traffic)
([AWS, What is Elastic Load Balancing](https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/what-is-load-balancing.html),
verified 2026-08-22). These two goals point at the same mechanism from
different directions. capacity needs an even split of work, fault tolerance
needs a current, accurate view of which servers can safely receive it. A load
balancer that only does the first, without health checking, will happily keep
sending a fair share of traffic to a server that already crashed.

The problem gets sharper, not simpler, at scale. A fleet of a hundred servers
still needs the same two things a fleet of two servers needs, but now the
mechanism making the routing decision is itself a piece of shared
infrastructure that every request depends on. What happens when that mechanism
itself breaks is covered in full in dimension 11, because it is one of the
more instructive failure modes in this whole family of patterns.

## 3. Forces

**Speed versus routing intelligence (Layer 4 versus Layer 7).** A load
balancer working at the transport layer reads only IP addresses, ports, and
protocol, and can forward a connection with almost no added work. A load
balancer working at the application layer reads the HTTP request itself, method,
path, headers, and cookies, so it can make far smarter routing choices, but the
work of parsing that data costs CPU and adds latency. Google Cloud states this
distinction directly. Layer 4 load balancing directs traffic using network and
transport protocol data such as TCP, UDP, and ICMP, while Layer 7 load
balancing adds routing decisions based on attributes such as the HTTP header
([Google Cloud, Load balancing
overview](https://docs.cloud.google.com/load-balancing/docs/load-balancing-overview),
verified 2026-08-22). AWS's own product line makes the trade concrete rather
than abstract. its Application Load Balancer works at Layer 7 and supports
content-based routing, sticky sessions, and a gradual traffic ramp-up feature
called slow start, none of which its Network Load Balancer supports at Layer 4,
where the product instead advertises higher raw throughput and a static IP
address ([AWS, Elastic Load Balancing
Features](https://aws.amazon.com/elasticloadbalancing/features/), verified
2026-08-22).

**Session affinity versus even distribution.** Some applications keep state on
the specific server a client first connected to, an in-memory shopping cart or
a WebSocket connection. To serve those applications correctly, a load balancer
can pin a client to one backend for the life of a session, using a cookie or a
hash of the client's address. NGINX documents its address-based version of
this, ip_hash, as routing all requests from one client IP to the same server so
that the client's session stays on one machine
([NGINX, HTTP load
balancing](https://nginx.org/en/docs/http/load_balancing.html), verified
2026-08-22). The cost of this choice is that load can no longer be perfectly
even. a handful of unusually active clients pinned to the same backend can
create a hot node while its neighbors stay light, a cost that is standard,
widely understood operational knowledge rather than something any single
source states outright, and is labelled here as engineering judgement.

**Cold recovery versus flooding a fragile server.** A backend that recently
failed and came back has empty caches, cold connection pools, and possibly
still recovering internal state. Sending it a full, immediate share of traffic
the moment its health check passes risks knocking it straight back down, a
thundering herd aimed at the one server least able to absorb it. NGINX's own
answer to this is a first-class configuration option. slow_start sets the time
over which a server's weight climbs from zero back to its normal value after it
becomes healthy again, and defaults to zero, meaning the ramp is off unless an
operator turns it on ([NGINX, ngx_http_upstream_module
reference](https://nginx.org/en/docs/http/ngx_http_upstream_module.html),
verified 2026-08-22). The mere existence of this parameter as a documented,
named feature is itself evidence that the failure mode is common enough to
warrant a dedicated fix, and it is picked up again in dimension 11.

**Cost of the algorithm versus its resistance to stale information.** The
cheapest possible algorithm, round robin, tracks no state about any backend and
costs nothing to run, but it has no way to notice that one backend is currently
slower or busier than another. A load balancer that instead tracks each
backend's active connection count, or samples two random candidates and keeps
the lesser loaded one, an approach covered in dimension 8 as Power of Two
Choices, makes a better-informed choice at the price of maintaining and reading
that state on every request. Marc Brooker's plain-language description of the
trade names the failure mode the cheap algorithm invites. relying on stale load
data produces herd behavior, where requests keep piling onto a server that
recently looked quiet for far longer than it takes to make that server
genuinely overloaded ([Marc Brooker's engineering blog,
brooker.co.za](https://brooker.co.za/blog/2012/01/17/two-random.html),
verified 2026-08-22).

## 4. Applicability and non-applicability

**Reach for a load balancer when.**

- More than one instance of a logical service exists, and something needs to
  decide, per request or per connection, which instance answers it. Every
  definitional source in dimension 1 and dimension 2 frames the pattern's own
  purpose this way, so this is close to a restatement of what the pattern is
  for rather than a separate claim.
- The application needs to survive an instance failing outright. A health
  check paired with automatic removal from rotation is what makes that
  survival possible, per AWS's own framing of fault tolerance in dimension 2.
- Traffic volume, or its variance, is large enough that a single instance's
  ceiling is a real operational risk rather than a hypothetical one.
- TLS handling, request-level security filtering, or protocol translation
  needs one shared, centrally managed place to happen rather than being
  repeated in every backend, a role covered fully in dimension 17.

**Do not reach for a load balancer when.**

- Exactly one instance of the service exists and no near-term plan calls for
  a second. There is nothing to distribute traffic across, so the pattern's
  stated purpose does not apply. This point is reasoned from the definitional
  sources above rather than stated by any source as an explicit warning, and
  is labelled here as that reasoning rather than a sourced claim.
- The call is a direct, already-addressed point-to-point connection between
  two processes that both know exactly who the other is, where the added hop
  and its latency cost buy nothing. This is an engineering judgement, not a
  claim traceable to a specific source.
- The real problem is routing a request to the specific owner of a data
  partition rather than to any interchangeable replica. That is the job of
  Sharding (dimension 13), and applying load balancing's assume-any-instance-
  will-do model to a partitioned system routes requests to servers that do
  not hold the data being asked for.

## 5. Structure

- **Client.** The process originating a request or connection. Has no
  knowledge of which specific backend will answer.
- **Load balancer.** The component that owns the routing decision. Exposes one
  stable address to clients and holds the current list of eligible backends,
  their weights, and, where used, per-client affinity state.
- **Listener.** The load balancer's entry point for a specific protocol and
  port, for example an HTTPS listener on port 443. A single load balancer can
  run more than one listener.
- **Backend pool (also called a target group or upstream group).** The set of
  server instances currently registered to receive traffic for a given
  listener or rule.
- **Algorithm.** The selection logic that, given the current pool and its
  state, picks one backend for a given request. Dimension 8 covers the real
  variants in depth.
- **Health checker.** The subsystem that probes each backend on a schedule,
  actively by sending its own request or passively by watching real traffic
  outcomes, and reports which backends are currently eligible.
- **Session affinity store (optional).** Where a cookie-based or IP-based
  pinning scheme needs to remember which backend a given client was last sent
  to.

## 6. ASCII structure diagram

```
                       +-------------------+
                       |       Client       |
                       +----------+---------+
                                  |
                                  v
                       +-------------------+
                       |   Load Balancer    |
                       | (listener + algo)  |
                       +----------+---------+
                                  |
                +-----------------+-----------------+
                |                 |                  |
                v                 v                  v
          +-----------+     +-----------+      +-----------+
          | Backend A |     | Backend B |      | Backend C |
          +-----------+     +-----------+      +-----------+
                ^                 ^                  ^
                |                 |                  |
                +-----------------+------------------+
                                  |
                       +-------------------+
                       |   Health Checker   |
                       +-------------------+
```

## 7. Dynamics

```
1. The health checker probes Backend A, B, and C on a fixed interval.
2. Backend B stops answering. After N consecutive failures the health
   checker marks Backend B unhealthy, and the load balancer drops it
   from the pool the algorithm is allowed to pick from.
3. A client sends a request to the load balancer's stable address.
4. The algorithm chooses among the remaining eligible backends, A and
   C, and forwards the request to Backend A.
5. Backend A processes the request and returns a response.
6. The load balancer relays the response to the client, updates its
   per-backend connection or load count, and the cycle repeats for the
   next request.
7. Later, Backend B passes M consecutive health checks and returns to
   the pool, often starting at a reduced weight for a short warm-up
   window rather than a full share of traffic right away.
```

## 8. Implementation variants

**Round robin.** The default and cheapest algorithm. Cycles through the pool
in order with no memory of load or response time. NGINX's own docs state that
with no method configured, round robin is what runs, and that it works best
when requests are similar in cost and processed at a similar pace
([NGINX, HTTP load
balancing](https://nginx.org/en/docs/http/load_balancing.html), verified
2026-08-22).

**Weighted round robin.** A static integer weight per backend biases the
rotation, so a server rated for three times the capacity of its neighbors
receives three times the share. NGINX's own worked example puts this plainly.
a weight of 3 on one server against the default weight of 1 on two others
sends 3 of every 5 requests to the heavier one ([NGINX, HTTP load
balancing](https://nginx.org/en/docs/http/load_balancing.html), verified
2026-08-22). Envoy also documents a dynamic variant, client-side weighted round
robin, where the weight is not set by an operator but computed continuously
from load reports the backend itself sends, combining queries per second,
errors per second, and utilization ([Envoy, Load
balancers](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/load_balancing/load_balancers),
verified 2026-08-22).

**Least connections and weighted least connections.** Routes each new request
to whichever eligible backend currently has the fewest open connections,
scaled by weight when weights are configured, with ties broken by weighted
round robin ([NGINX, ngx_http_upstream_module
reference](https://nginx.org/en/docs/http/ngx_http_upstream_module.html),
verified 2026-08-22). This is a better fit than round robin when request cost
varies a lot, since it reacts to a server that is currently busy rather than
assuming every server is equally free.

**IP hash and consistent hashing.** IP hash routes every request from a given
client address to the same backend for as long as that backend stays healthy,
giving simple session affinity with no external session store
([NGINX, HTTP load
balancing](https://nginx.org/en/docs/http/load_balancing.html), verified
2026-08-22). A plain hash of any key has a known weakness. adding or removing
one backend remaps most keys to a different server, because the modulus itself
changes. NGINX's consistent variant, using the ketama algorithm, fixes this by
remapping only a small share of keys when the pool changes, which matters most
for cache-backed servers where a remap is a cache miss
([NGINX, ngx_http_upstream_module
reference](https://nginx.org/en/docs/http/ngx_http_upstream_module.html),
verified 2026-08-22).

**Power of Two Choices (P2C).** Instead of scanning the whole pool for the
lightest backend, the algorithm samples two random eligible backends and picks
the lesser loaded of the pair. Envoy documents this as its own default
weighted least request behavior when weights are equal, an O(1) selection over
N randomly sampled hosts, two by default, choosing the one with fewer active
requests ([Envoy, Load
balancers](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/load_balancing/load_balancers),
verified 2026-08-22). This gets most of the benefit of a full least-loaded scan
at a fraction of its cost. Brooker's plain-language explainer names the
theoretical basis as survey work on this technique by Michael Mitzenmacher and
collaborators ([Marc Brooker's engineering blog,
brooker.co.za](https://brooker.co.za/blog/2012/01/17/two-random.html),
verified 2026-08-22, the exact asymptotic result from that survey was not
independently confirmed against the original paper in this research pass, so
it is not restated here as a specific figure).

**Ring hash and Maglev hashing.** Ring hash places every backend and every
request key on a fixed logical circle by hashing their addresses, then routes
a request to the nearest backend clockwise from its own position on the
circle, a technique also called ketama ([Envoy, Load
balancers](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/load_balancing/load_balancers),
verified 2026-08-22). Maglev hashing, the algorithm from Google's paper, builds
a fixed-size lookup table, 65537 entries in Envoy's own implementation, and is
documented by Envoy as a functional substitute for ring hash aimed at Layer 4,
connection-persistent, line-rate routing ([Envoy, Load
balancers](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/load_balancing/load_balancers),
verified 2026-08-22).

**Flow hashing at Layer 4.** AWS's Network Load Balancer selects a target
using a hash over the protocol, source and destination address, source and
destination port, and TCP sequence number, and keeps every packet in one TCP
connection on the same target for that connection's life
([AWS, How Elastic Load Balancing
works](https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/how-elastic-load-balancing-works.html),
verified 2026-08-22).

**Round robin DNS.** Returning a different backend IP address for each DNS
lookup, in rotation, is a much older and cruder technique that predates
purpose-built load balancers and is still seen in small deployments. RFC
2391's own critique of it, that DNS answers change too slowly to track real
load, is the reason the rest of this dimension exists as a separate class of
mechanism (see dimension 1).

## 9. Known production uses

1. **Google Maglev.** A single Maglev machine can saturate a 10 gigabit link
   even under the harder small-packet condition, and the system has carried
   Google's own traffic since 2008, later extended to underlie Google Cloud's
   network load balancers ([Eisenbud et al., Google
   Research](https://research.google/pubs/maglev-a-fast-and-reliable-software-network-load-balancer/),
   verified 2026-08-22).
2. **Cloudflare Unimog.** Cloudflare's own edge Layer 4 load balancer, running
   across more than 200 cities, uses a hash-based forwarding table with tens
   of thousands of entries per pool and a two-hop forwarding technique,
   borrowed from the Beamer research paper, to keep connections alive while
   the table is rebuilt. Cloudflare states the whole system costs under 1
   percent of processor time ([Cloudflare,
   Unimog](https://blog.cloudflare.com/unimog-cloudflares-edge-load-balancer/),
   verified 2026-08-22).
3. **AWS Elastic Load Balancing.** Three distinct product tiers, Application,
   Network, and Gateway Load Balancer, each with its own documented routing
   algorithm and use case, are in active production use across AWS's own
   customer base ([AWS, Elastic Load Balancing
   Features](https://aws.amazon.com/elasticloadbalancing/features/), verified
   2026-08-22).
4. **Dropbox's migration to Envoy.** Dropbox describes itself as one of the
   largest Envoy users anywhere after replacing NGINX at its edge, running
   tens of millions of open connections and millions of requests per second,
   and reports it was able to give back up to 60 percent of the servers that
   had previously been used only for NGINX ([Dropbox, How We Migrated Dropbox
   from Nginx to
   Envoy](https://dropbox.tech/infrastructure/how-we-migrated-dropbox-from-nginx-to-envoy),
   verified 2026-08-22).
5. **HAProxy.** HAProxy's own published benchmark reports up to 2 million
   HTTPS requests per second and 100 gigabits per second of traffic on a
   64-core ARM system, alongside support for ten distinct load balancing
   algorithms ([HAProxy, introduction
   documentation](https://docs.haproxy.org/2.8/intro.html), verified
   2026-08-22).

## 10. Consequences

**Positive.**

- Horizontal capacity growth. Adding a backend adds capacity without
  redesigning the application, as long as the application does not depend on
  sticky, un-externalized state.
- Automatic failure removal. A backend that fails its health check stops
  receiving new traffic without a person having to intervene.
- A stable address for clients. Clients depend on one address and never need
  to know how many backends exist behind it or which one answered, a
  decoupling that pairs directly with the service discovery mechanisms in
  dimension 13.
- A single, centrally managed place for cross-cutting concerns such as TLS
  termination and request-level security filtering, covered in dimension 17.

**Negative.**

- An extra network hop, and at Layer 7, extra CPU work to parse and route on
  request content, both adding latency the direct call would not have paid.
- The load balancer itself becomes shared infrastructure every request
  depends on, so its own availability now bounds the availability of
  everything behind it, the exact failure class covered first in dimension
  11.
- Session affinity, where used, concentrates load unevenly and reintroduces a
  form of the per-server state problem the pattern is often adopted to avoid.
- Cost. A managed load balancer bills for capacity units or data processed,
  and a self-run one needs its own compute, monitoring, and on-call
  ownership.

## 11. Failure modes and misuse

**The load balancer's own control plane fails.** On December 24, 2012, AWS's
Elastic Load Balancing service lost the data tracking which backend instances
belonged to which load balancer, after an internal maintenance process was run
by mistake against production state. The control plane then applied wrong
configurations to affected load balancers, degrading performance and causing
errors for the applications behind them, at its peak touching 6.8 percent of
running load balancers in that region ([AWS, Summary of the December 24, 2012
Amazon ELB Service
Event](https://aws.amazon.com/message/680587/), verified 2026-08-22). The data
plane, the actual traffic routing, kept working throughout. what broke was the
system that manages the routing rules, which is the sharper and less obvious
version of load balancer becoming a single point of failure. it is rarely the
packet-forwarding path that fails first, it is the management layer around it.

**A backend looks healthy while failing fast, and gets more traffic for it.**
Google's own SRE book documents a specific and counterintuitive failure. a
backend that has gone seriously wrong can start returning errors at very low
latency, and a load balancer using a least-loaded style algorithm reads that
low latency as spare capacity and sends the broken backend even more requests,
a pattern the book calls sinkholing traffic. The book's stated fix is graceful
shutdown, where a backend entering a lame duck state tells its clients so that
in-flight requests finish cleanly instead of every active request on that
backend failing at once ([Google, Load Balancing in the
Datacenter](https://sre.google/sre-book/load-balancing-datacenter/), verified
2026-08-22).

**Flooding a newly recovered backend.** Covered as a force in dimension 3.
NGINX's slow_start parameter exists specifically because sending a backend a
full share of traffic the instant its health check passes can push it straight
back down ([NGINX, ngx_http_upstream_module
reference](https://nginx.org/en/docs/http/ngx_http_upstream_module.html),
verified 2026-08-22).

**Failing open when every backend looks unhealthy.** Two independent systems
document the same deliberate design choice for the worst case, all targets
appearing unhealthy at once. AWS states that if a target group holds only
unhealthy targets, its Application Load Balancer routes to all of them anyway
rather than to none ([AWS, Target group health
checks](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html),
verified 2026-08-22). Envoy exposes the same behavior as a named, countable
metric, lb_healthy_panic, incrementing whenever it has run out of hosts it
currently believes are healthy and starts routing to hosts it does not
([Envoy, cluster
stats](https://www.envoyproxy.io/docs/envoy/latest/configuration/upstream/cluster_manager/cluster_stats),
verified 2026-08-22). The reasoning behind both is the same. a health check
that is itself wrong, or a real outage across the whole pool, should not turn
into every request being rejected when serving degraded traffic is the better
of two bad options.

**Sticky sessions creating a hot node.** A small number of unusually long or
heavy sessions pinned to one backend can overload that one server while its
neighbors stay light, defeating the point of load balancing for exactly the
clients affected. This is standard, uncontested operational knowledge rather
than a claim traced to a specific source in this research pass, and is
labelled here as that.

## 12. Trade-off matrix

| Algorithm | Cost per request | Reacts to real load | Session affinity | Cache locality after a pool change |
|---|---|---|---|---|
| Round robin | Lowest, no state read | No | No | N/A |
| Weighted round robin | Low, static weight read | No | No | N/A |
| Least connections | Medium, connection count read | Yes | No | N/A |
| Power of Two Choices | Low, two random samples | Yes | No | N/A |
| IP hash (plain) | Low, one hash | No | Yes, per client | Majority of keys remap when the pool changes |
| Ring hash or Maglev hashing | Low, one hash and a table lookup | No | Yes, per key | Only a small share of keys remap when the pool changes |
| Round robin DNS | Lowest, no per-request cost at the balancer | No, minutes of lag | No | N/A |

The Layer 4 versus Layer 7 choice sits outside this table because it is a
choice of what data the algorithm is even allowed to read, not a choice among
algorithms. A Layer 4 load balancer can run any of the hash-based rows above
using only address and port. a Layer 7 load balancer can additionally route on
request content, at the added parsing cost named in dimension 3.

## 13. Related and incompatible patterns

**Circuit Breaker.** Envoy's own documentation draws the line between the two
clearly. circuit breaking enforces per-client resource limits, fully local and
not coordinated with anything else, while a load balancer's job is choosing
which backend answers a given request in the first place ([Envoy, Circuit
breaking](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/circuit_breaking),
verified 2026-08-22). A load balancer decides who gets the request. a circuit
breaker decides whether the caller should even try.

**Health Endpoint Monitoring.** Load balancing depends entirely on a current,
accurate view of which backends are eligible, and that view is exactly what
Health Endpoint Monitoring supplies. the two patterns are typically implemented
together, not separately, and the failure modes named in dimension 11 mostly
trace back to a gap in this dependency rather than to the routing algorithm
itself.

**Service Discovery, both client-side and server-side.** A load balancer needs
a live list of backends before it can choose among them, and service discovery
is the mechanism that supplies and keeps that list current. Kubernetes' own
Service documentation frames this exactly. a Service's controller continuously
scans for matching pods and updates the set of reachable endpoints whenever
the pool changes, and a client connects to one stable address that is then
load balanced across whatever is currently in that set
([Kubernetes, Service](https://kubernetes.io/docs/concepts/services-networking/service/),
verified 2026-08-22). Istio documents the same relationship from the
client-side angle, where load balancing runs inside a sidecar next to each
client rather than at one central hop ([Istio, Traffic Management
concepts](https://istio.io/latest/docs/concepts/traffic-management/), verified
2026-08-22).

**Sharding.** The two patterns look similar and solve different problems.
Load balancing picks any interchangeable replica of the same service. Sharding
routes a request to the one specific partition that owns the data being asked
for. Applying load balancing's any-instance-will-do assumption to a sharded
system sends requests to servers holding the wrong data.

**Gateway Routing and Rate Limiting.** Both commonly sit at the same network
tier as a Layer 7 load balancer and are frequently implemented in the same
piece of software, an API gateway or an ingress proxy, but each answers a
different question. Gateway Routing decides which service a request belongs
to before any load balancing across that service's own instances happens.
Rate Limiting decides whether a request is allowed through at all,
independent of which backend would have served it.

**Bulkhead, also called cell-based architecture.** Microsoft's own description
of this pattern frames it as partitioning service instances into separate
pools by consumer or workload, so that overload or failure in one pool does
not spread to the others ([Microsoft Learn, Bulkhead
pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead),
verified 2026-08-22). A load balancer typically operates within one such pool,
choosing among the instances inside it. deciding which pool a given client or
tenant belongs to in the first place is Bulkhead's job, one layer above.

**Consistent Hashing.** The algorithm that ring hash and Maglev hashing, both
covered in dimension 8, are built on. Consistent Hashing is its own pattern
with its own entry in this catalogue and applies well beyond load balancing,
to any system that must map keys to a changing set of nodes with minimal
remapping.

## 14. Refactoring path in and out

**Introducing it.** Start from a single instance with clients pointed directly
at it. Add a second instance and a health check before adding any traffic
distribution, so the health check's behavior can be verified against a known,
controlled set of two backends. Put a simple, stateless algorithm such as round
robin or least connections in front of both. Only add session affinity once a
real feature needs it, and treat that need itself as a signal worth
questioning. per-server session state is a smell the codebase may be better
served by removing, by externalizing session data to a shared store, rather
than by working around it with sticky routing.

**Removing it.** Two honest reasons to remove a load balancer exist. The
service has been consolidated back down to a single instance and the pattern
no longer applies, or the routing responsibility has moved to the client side,
into a sidecar proxy running next to each caller, as in the Istio-style
architecture named in dimension 13. In the second case the load balancing
logic has not gone away, it has moved from one central hop to many
distributed ones, and the health checking and algorithm choices this entry
covers still apply, only relocated.

## 15. Testing and verification

- **Unit test the algorithm in isolation.** Build a fake pool with known,
  fixed load values per backend and assert the algorithm picks the backend
  the specific rule says it should, without a real network call anywhere in
  the test.
- **Test health check state transitions directly.** Simulate a backend that
  starts answering successfully, then starts failing, and assert it is
  removed from the eligible pool only after the configured number of
  consecutive failures, and returned only after the configured number of
  consecutive successes. This is the surface where off-by-one threshold bugs
  hide.
- **Load test for even distribution and for affinity, separately.** Send a
  large, varied volume of requests from many simulated clients and assert the
  spread across backends matches the configured weights within a reasonable
  tolerance. Separately, for a sticky configuration, send many requests from
  one simulated client and assert every one lands on the same backend.
- **Test the failure-open behavior on purpose.** Take every backend in a test
  pool unhealthy at once and confirm the system behaves the way dimension 11
  describes, whichever choice was made, rather than discovering the real
  behavior for the first time during an actual outage.

## 16. Observability signals

- **Eligible pool size.** AWS reports HealthyHostCount and UnHealthyHostCount
  per target group, and recommends alarming on a nonzero UnHealthyHostCount
  read from the minimum statistic across the fleet, so a target considered
  unhealthy by every node is caught even if most nodes still see it as
  healthy ([AWS, CloudWatch metrics for your Application Load
  Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-cloudwatch-metrics.html),
  verified 2026-08-22). Envoy exposes the equivalent as membership_healthy
  against membership_total ([Envoy, cluster
  stats](https://www.envoyproxy.io/docs/envoy/latest/configuration/upstream/cluster_manager/cluster_stats),
  verified 2026-08-22).
- **Per-target latency.** AWS's TargetResponseTime measures the time from a
  request leaving the load balancer to the target starting its response
  headers, tracked as an average and as percentiles ([AWS, CloudWatch
  metrics](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-cloudwatch-metrics.html),
  verified 2026-08-22).
- **Error responses split by origin.** AWS separates HTTPCode_Target_5XX_Count,
  errors coming from a backend, from HTTPCode_ELB_5XX_Count, errors the load
  balancer itself generated, which is what tells an operator whether a 5xx
  spike is the application's fault or the routing layer's ([AWS, CloudWatch
  metrics](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-cloudwatch-metrics.html),
  verified 2026-08-22).
- **Panic or fail-open mode as its own counter.** Envoy's lb_healthy_panic
  counter increments every time the balancer had to route to hosts it does not
  currently believe are healthy, giving a direct, alertable signal for the
  worst-case failure mode named in dimension 11 ([Envoy, cluster
  stats](https://www.envoyproxy.io/docs/envoy/latest/configuration/upstream/cluster_manager/cluster_stats),
  verified 2026-08-22).
- **A healthy dashboard versus a failing one.** Healthy looks like a stable
  HealthyHostCount close to the full pool size, tight and flat response time
  percentiles across backends, and a zero or near-zero panic counter. Failing
  looks like a HealthyHostCount dropping, response time percentiles pulling
  apart between backends, and rising target-origin 5xx counts, in that rough
  order.

## 17. Security and privacy implications

**TLS termination moves the trust boundary.** A load balancer configured to
terminate TLS decrypts client traffic before it forwards a request, and AWS's
own documentation states this plainly for its Application Load Balancer,
adding that a customer who wants encrypted traffic to reach the backend
untouched instead should use a plain TCP listener with no decryption at all
([AWS, Create an HTTPS listener for your Application Load
Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/create-https-listener.html),
verified 2026-08-22). Either choice is a deliberate trust decision. terminating
at the load balancer means the load balancer itself now sees plaintext, which
is exactly why security inspection tooling is often placed at that same point
([F5, SSL termination](https://www.f5.com/glossary/ssl-termination), verified
2026-08-22).

**Web application firewalling and denial of service protection sit at the
same tier.** AWS names its Application Load Balancer as a directly protectable
resource for both AWS WAF, which filters requests on IP, country, header
content, and known attack signatures such as SQL injection, and AWS Shield
Advanced, which adds automatic mitigation against application-layer denial of
service ([AWS, What are AWS WAF, AWS Shield
Advanced](https://docs.aws.amazon.com/waf/latest/developerguide/what-is-aws-waf.html),
verified 2026-08-22). Putting these controls at the load balancer, rather than
in every backend, is one of the pattern's clearer security benefits, already
named as a positive consequence in dimension 10.

**Affinity by client address is a routing signal, not only a convenience.**
IP hash based session affinity, covered in dimension 8, uses the client's
address as an input to a routing decision. an operator relying on it should be
aware that address alone is a weak and sometimes shared identity signal, for
instance behind a shared corporate or carrier network address translation
device, and can produce uneven or surprising affinity as a side effect rather
than a security flaw in itself.

## 18. References

1. IETF. *RFC 2391, Load Sharing using IP Network Address Translation
   (LSNAT)*, August 1998.
   https://datatracker.ietf.org/doc/html/rfc2391
   Verified 2026-08-22. Source of the formal problem statement and the
   critique of round robin DNS.
2. Wikipedia. *F5, Inc.*
   https://en.wikipedia.org/wiki/F5_Networks
   Verified 2026-08-22. Source of F5's 1996 founding date and its 1997
   BIG-IP launch, noted in the entry as moderate confidence, tertiary source.
3. Wikipedia. *Load balancing (computing)*.
   https://en.wikipedia.org/wiki/Load_balancing_%28computing%29
   Verified 2026-08-22. General definitional source, contains no dedicated
   historical section, used only for background framing.
4. AWS. *What is Elastic Load Balancing*.
   https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/what-is-load-balancing.html
   Verified 2026-08-22. Source of the capacity plus fault tolerance framing.
5. AWS. *How Elastic Load Balancing works*.
   https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/how-elastic-load-balancing-works.html
   Verified 2026-08-22. Source of the per-product routing algorithm
   descriptions for Application, Network, Gateway, and Classic Load Balancer.
6. AWS. *Elastic Load Balancing Features*.
   https://aws.amazon.com/elasticloadbalancing/features/
   Verified 2026-08-22. Source of the Layer 4 versus Layer 7 feature
   comparison table across AWS's own product line.
7. Google Cloud. *Load balancing overview*.
   https://docs.cloud.google.com/load-balancing/docs/load-balancing-overview
   Verified 2026-08-22. Source of the Layer 4 versus Layer 7 definitional
   split and the global versus regional distinction.
8. Google Research. Eisenbud, D. et al. *Maglev, A Fast and Reliable Software
   Network Load Balancer*, USENIX NSDI 2016.
   https://research.google/pubs/maglev-a-fast-and-reliable-software-network-load-balancer/
   Verified 2026-08-22. Source of Maglev's design goals, its 10 gigabit
   per-machine figure, and its 2008 production start date.
9. Envoy Project. *Envoy documentation, Load balancers*.
   https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/load_balancing/load_balancers
   Verified 2026-08-22. Source of Envoy's weighted round robin, weighted
   least request, ring hash, and Maglev algorithm descriptions.
10. Envoy Project. *Envoy documentation, Circuit breaking*.
    https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/circuit_breaking
    Verified 2026-08-22. Source of the distinction between circuit breaking
    and load balancing.
11. NGINX. *HTTP load balancing*.
    https://nginx.org/en/docs/http/load_balancing.html
    Verified 2026-08-22. Source of round robin, weighted round robin, least
    connections, and ip_hash descriptions and defaults.
12. NGINX. *ngx_http_upstream_module reference*.
    https://nginx.org/en/docs/http/ngx_http_upstream_module.html
    Verified 2026-08-22. Source of the slow_start parameter, the weighted
    least_conn tie-breaking rule, and the consistent hash directive.
13. Cloudflare. *What Is Load Balancing*.
    https://www.cloudflare.com/en-gb/learning/performance/what-is-load-balancing/
    Verified 2026-08-22. Source of the plain-language distribution framing.
14. Cloudflare. *Unimog, Cloudflare's edge load balancer*.
    https://blog.cloudflare.com/unimog-cloudflares-edge-load-balancer/
    Verified 2026-08-22. Source of the Unimog production figures and its
    relationship to Maglev, Katran, and GLB.
15. AWS. *Summary of the December 24, 2012 Amazon ELB Service Event in the
    US-East Region*.
    https://aws.amazon.com/message/680587/
    Verified 2026-08-22. Source of the control plane failure incident.
16. Google. *Site Reliability Engineering, Load Balancing in the Datacenter*.
    https://sre.google/sre-book/load-balancing-datacenter/
    Verified 2026-08-22. Source of the sinkholing traffic failure mode and
    the lame duck graceful shutdown mitigation.
17. AWS. *Target group health checks*.
    https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html
    Verified 2026-08-22. Source of the fail-open behavior when every target
    in a group is unhealthy.
18. HAProxy Technologies. *HAProxy documentation, introduction*.
    https://docs.haproxy.org/2.8/intro.html
    Verified 2026-08-22. Source of HAProxy's throughput benchmark figures
    and its stated count of supported algorithms.
19. HAProxy Technologies. *Health checks tutorial*.
    https://www.haproxy.com/documentation/haproxy-configuration-tutorials/reliability/health-checks/
    Verified 2026-08-22. Source of HAProxy's default health check interval
    and consecutive pass or fail thresholds.
20. AWS. *CloudWatch metrics for your Application Load Balancer*.
    https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-cloudwatch-metrics.html
    Verified 2026-08-22. Source of the HealthyHostCount, TargetResponseTime,
    and split 5xx metric definitions.
21. Envoy Project. *Cluster statistics*.
    https://www.envoyproxy.io/docs/envoy/latest/configuration/upstream/cluster_manager/cluster_stats
    Verified 2026-08-22. Source of the membership_healthy and
    lb_healthy_panic metric definitions.
22. AWS. *Create an HTTPS listener for your Application Load Balancer*.
    https://docs.aws.amazon.com/elasticloadbalancing/latest/application/create-https-listener.html
    Verified 2026-08-22. Source of the TLS termination versus TCP
    passthrough choice.
23. F5. *SSL termination glossary entry*.
    https://www.f5.com/glossary/ssl-termination
    Verified 2026-08-22. Source of the general SSL termination and security
    inspection framing.
24. AWS. *What are AWS WAF, AWS Shield Advanced, and AWS Firewall Manager*.
    https://docs.aws.amazon.com/waf/latest/developerguide/what-is-aws-waf.html
    Verified 2026-08-22. Source of the WAF and Shield Advanced protection
    of load balancer resources.
25. Kubernetes. *Service*.
    https://kubernetes.io/docs/concepts/services-networking/service/
    Verified 2026-08-22. Source of the service discovery to load balancing
    relationship inside Kubernetes.
26. Istio. *Traffic Management concepts*.
    https://istio.io/latest/docs/concepts/traffic-management/
    Verified 2026-08-22. Source of the sidecar-based, client-side load
    balancing architecture.
27. Microsoft Learn. *Bulkhead pattern*.
    https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead
    Verified 2026-08-22. Source of the Bulkhead, also called cell-based
    architecture, description.
28. Brooker, Marc. Personal engineering blog post on the two-random-choices
    load balancing technique.
    https://brooker.co.za/blog/2012/01/17/two-random.html
    Verified 2026-08-22. Source of the herd behavior explanation and the
    reference to Mitzenmacher's survey work.
29. Dropbox. *How We Migrated Dropbox from Nginx to Envoy*.
    https://dropbox.tech/infrastructure/how-we-migrated-dropbox-from-nginx-to-envoy
    Verified 2026-08-22. Source of Dropbox's production scale figures and
    its stated 60 percent server reduction after migration.

**Evidence grade.** high

**Most solid findings.** The AWS, Google Cloud, NGINX, Envoy, and Google
Research sources are all primary, vendor-authored documentation fetched
directly, giving high confidence to the algorithm descriptions in dimension 8,
the metric definitions in dimension 16, and the December 2012 AWS control
plane incident in dimension 11, which is a first-party AWS post-incident
account rather than a third-party summary.

**Unverified or unclear.** F5's 1996 founding date and 1997 BIG-IP launch rest
on a single tertiary source and were not cross-checked against a primary
company record. The exact asymptotic improvement figure often associated with
the two-random-choices technique was not confirmed against Mitzenmacher's
original survey paper in this research pass and is deliberately left out of
dimension 8 rather than stated as a specific number.

## Code

### TypeScript, weighted round robin with health-aware exclusion

```typescript
type Backend = {
  id: string;
  weight: number;
  healthy: boolean;
};

class WeightedRoundRobinBalancer {
  private backends: Backend[];
  private currentWeights: Map<string, number>;

  constructor(backends: Backend[]) {
    this.backends = backends;
    this.currentWeights = new Map(backends.map((b) => [b.id, 0]));
  }

  markUnhealthy(id: string): void {
    const backend = this.backends.find((b) => b.id === id);
    if (backend) backend.healthy = false;
  }

  markHealthy(id: string): void {
    const backend = this.backends.find((b) => b.id === id);
    if (backend) backend.healthy = true;
  }

  pick(): Backend {
    const eligible = this.backends.filter((b) => b.healthy);
    if (eligible.length === 0) {
      throw new Error("no healthy backends available");
    }

    let selected: Backend | null = null;
    let totalWeight = 0;

    for (const backend of eligible) {
      const current = (this.currentWeights.get(backend.id) ?? 0) + backend.weight;
      this.currentWeights.set(backend.id, current);
      totalWeight += backend.weight;
      if (selected === null || current > this.currentWeights.get(selected.id)!) {
        selected = backend;
      }
    }

    const selectedCurrent = this.currentWeights.get(selected!.id)! - totalWeight;
    this.currentWeights.set(selected!.id, selectedCurrent);
    return selected!;
  }
}

const balancer = new WeightedRoundRobinBalancer([
  { id: "a", weight: 3, healthy: true },
  { id: "b", weight: 1, healthy: true },
  { id: "c", weight: 1, healthy: true },
]);

for (let i = 0; i < 5; i++) {
  console.log(balancer.pick().id);
}
```

### Python, Power of Two Choices with active request tracking

```python
import random
from dataclasses import dataclass


@dataclass
class Backend:
    backend_id: str
    healthy: bool = True
    active_requests: int = 0


class PowerOfTwoChoicesBalancer:
    def __init__(self, backends: list[Backend]) -> None:
        self.backends = backends

    def eligible(self) -> list[Backend]:
        return [b for b in self.backends if b.healthy]

    def pick(self) -> Backend:
        pool = self.eligible()
        if not pool:
            raise RuntimeError("no healthy backends available")
        if len(pool) == 1:
            candidates = pool
        else:
            candidates = random.sample(pool, 2)
        chosen = min(candidates, key=lambda b: b.active_requests)
        chosen.active_requests += 1
        return chosen

    def finish(self, backend: Backend) -> None:
        backend.active_requests = max(0, backend.active_requests - 1)


def simulate() -> None:
    backends = [Backend("a"), Backend("b"), Backend("c")]
    balancer = PowerOfTwoChoicesBalancer(backends)
    picks = [balancer.pick().backend_id for _ in range(6)]
    print(picks)


simulate()
```

### Go, consistent hash ring with minimal remapping on backend removal

```go
package main

import (
	"fmt"
	"hash/fnv"
	"sort"
)

type Ring struct {
	replicas int
	sorted   []uint32
	nodes    map[uint32]string
}

func NewRing(replicas int) *Ring {
	return &Ring{replicas: replicas, nodes: make(map[uint32]string)}
}

func hashKey(s string) uint32 {
	h := fnv.New32a()
	h.Write([]byte(s))
	return h.Sum32()
}

func (r *Ring) Add(backend string) {
	for i := 0; i < r.replicas; i++ {
		virtualKey := fmt.Sprintf("%s#%d", backend, i)
		point := hashKey(virtualKey)
		r.nodes[point] = backend
		r.sorted = append(r.sorted, point)
	}
	sort.Slice(r.sorted, func(i, j int) bool { return r.sorted[i] < r.sorted[j] })
}

func (r *Ring) Remove(backend string) {
	var kept []uint32
	for _, point := range r.sorted {
		if r.nodes[point] != backend {
			kept = append(kept, point)
		} else {
			delete(r.nodes, point)
		}
	}
	r.sorted = kept
}

func (r *Ring) Get(key string) string {
	if len(r.sorted) == 0 {
		return ""
	}
	target := hashKey(key)
	idx := sort.Search(len(r.sorted), func(i int) bool {
		return r.sorted[i] >= target
	})
	if idx == len(r.sorted) {
		idx = 0
	}
	return r.nodes[r.sorted[idx]]
}

func main() {
	ring := NewRing(100)
	ring.Add("backend-a")
	ring.Add("backend-b")
	ring.Add("backend-c")

	keys := []string{"user-1", "user-2", "user-3", "user-4"}
	before := make(map[string]string)
	for _, k := range keys {
		before[k] = ring.Get(k)
	}

	ring.Remove("backend-b")

	moved := 0
	for _, k := range keys {
		if ring.Get(k) != before[k] {
			moved++
		}
	}
	fmt.Println("keys remapped after removing one of three backends:", moved, "of", len(keys))
}
```
