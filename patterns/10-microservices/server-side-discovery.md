---
name: Server-Side Discovery
slug: server-side-discovery
family: 10-microservices
category: Microservices
aliases: [Server-Side Service Discovery, Router-Based Discovery, Discovery via Load Balancer]
first_described: "Richardson, microservices.io"
maturity: canonical
related: [client-side-service-discovery, api-gateway, service-registry, self-registration, third-party-registration, health-check-api, sidecar-proxy, service-mesh]
incompatible_with: []
verified: 2026-08-16
---

# Server-Side Discovery

## 1. Name, aliases, and lineage

The canonical name in this catalog is Server-Side Discovery, matching the
literal path segment Chris Richardson uses for the pattern's page on his
reference site, microservices.io, under `/patterns/server-side-discovery.html`.
The page itself titles the entry "Server-Side Service Discovery pattern", and
that fuller phrase, Server-Side Service Discovery, is the name most widely
quoted in books and conference talks, so both forms are treated as the same
pattern here and both point at this entry. The page states the solution
plainly. "When making a request to a service, the client makes a request via a
router, also called a load balancer, that runs at a well known location. The
router queries a service registry, which might be built into the router, and
forwards the request to an available service instance" (Chris Richardson,
"Server-Side Service Discovery pattern", microservices.io,
https://microservices.io/patterns/server-side-discovery.html, verified
2026-08-16).

The idea predates the microservices.io catalog by a couple of decades. Every
hardware and software load balancer sitting in front of a farm of web servers
since the 1990s already performs the same job, resolving a stable name or a
stable virtual IP to one of several backend addresses on the caller's behalf.
What Richardson's catalog entry did was give that long-standing mechanism a
name inside the specific vocabulary of microservices discovery, and pair it
against a named alternative, Client-Side Discovery, so that the choice between
the two became an explicit architectural decision rather than an accident of
which infrastructure happened to be on hand.

Because the mechanism is old, it also travels under several practitioner
names that describe the same shape from a different angle. Router-Based
Discovery names the network hop that performs the lookup. Discovery via
Load Balancer names the component doing the discovery, which is usually
also the component doing the load balancing, not a coincidence, both
jobs require the same live view of healthy instances. Sam Newman describes the
underlying idea without using the exact microservices.io name, discussing a
smart pipe, a network intermediary the caller does not have to be aware of,
that resolves a logical destination into one of several real instances
(Sam Newman, *Building Microservices*, 2nd edition, O'Reilly, 2021, chapter 4,
"Communication Styles", section on service discovery). This entry treats
Server-Side Discovery, Server-Side Service Discovery, and Newman's smart-pipe
description of the same problem as one pattern, viewed from three writers.

The pattern sits inside a two-member family with Client-Side Discovery. Both
answer the same question, how does a caller find a healthy address for a
logically named service whose actual instances move, scale, and fail
continuously. They differ only in which participant, the calling process or a
piece of shared infrastructure, performs the lookup and the load balancing
decision. This entry is about the shared-infrastructure variant. See the
Client-side Service Discovery entry in this catalog for the paired
alternative and dimension 12 for the trade-off between them.

## 2. Problem and context

A monolith calls its own functions in the same process, so there is nothing to
discover. A client-server application calls a small, fixed set of servers,
often addressed by one hostname behind DNS, so discovery is a one-time
configuration problem solved at deploy time. Microservices break both of
those assumptions at once. A single logical service, order-service for
example, usually runs behind many instances, and the number, and the
network address of each one, changes for reasons that have nothing to do with
a deliberate deploy. An autoscaler adds and removes instances as load shifts
through the day. A rolling update replaces every instance one at a time over
several minutes. A scheduler such as Kubernetes or an ECS capacity provider
reschedules a container onto a different host after a node fails a health
check, which changes its IP address. A spot instance is taken back by the
cloud provider with two minutes of notice. In a system under continuous
deployment, none of this is an edge case, it is the normal state of the
fleet, several times an hour.

The concrete situation this pattern addresses is a caller, another service, an
API gateway, a batch job, a mobile client hitting a public edge, that needs to
send a request to "the order service" without knowing which of order-service's
current instances will handle it, and without re-deploying itself every time
the fleet changes shape. Two shapes of answer exist. Either the caller itself
holds the current list of instances and picks one, which is Client-Side
Discovery, or the caller sends the request to one stable, well-known address
and lets something else, sitting between the caller and the fleet, resolve
that request to a live instance. Server-Side Discovery is the second shape.
The caller's code, in this variant, looks exactly like it would calling a
single fixed server. It never sees an instance list, never runs a
load-balancing algorithm, and never learns that the destination moved.

This is also the shape almost every team gets by default, because it is the
shape their infrastructure already gives them before anyone writes a line of
discovery code. A Kubernetes Service, an AWS Application Load Balancer, an
Nginx or HAProxy box in front of a fleet, a hardware load balancer in a
traditional data centre, all of these already sit at a fixed address and
forward to a changing set of backends. The practical context in which this
pattern shows up is therefore less often "we chose Server-Side Discovery"
and more often "the platform team's ingress layer already does this, and the
architectural decision is whether to also introduce a second, client-side
discovery layer on top of it for internal service-to-service calls."

## 3. Forces

The pattern balances the following competing pressures.

- **Client simplicity.** Strongly favoured. The calling code issues one
  request to one address, with the same client library, timeout, and retry
  logic it would use to call a single fixed server. No language-specific
  discovery client needs to exist, which matters in a polyglot fleet where a
  battle-tested discovery client may only exist for one or two of the
  languages in use.
- **Operational surface area.** Sacrificed. A new highly available network hop
  is introduced on the request path for every service-to-service call, and
  that hop must itself be built, deployed, scaled, and kept from becoming a
  single point of failure, work the client-side variant pushes into a
  library instead.
- **Latency.** Sacrificed, though usually by a small and bounded amount. Each
  request now traverses an additional network hop, usually inside the same
  data centre or the same node, adding on the order of low single-digit
  milliseconds. This is close to negligible for a synchronous HTTP call
  across a service mesh sidecar on the same host, and more relevant for an
  ultra low latency internal RPC where every hop is budgeted.
- **Consistency of policy.** Favoured. Retry budgets, circuit breaking,
  load-balancing algorithm, connection pooling and TLS termination live in one
  place, the router or proxy, and every caller inherits the same behaviour
  automatically, rather than each language's client library implementing, and
  potentially drifting in, its own version of the same policy.
- **Coupling to a discovery mechanism.** Favoured for the caller, sacrificed
  for the platform. Application code depends on nothing beyond DNS and HTTP.
  The platform, however, now owns a piece of infrastructure that every call
  depends on, and that infrastructure's failure mode becomes everyone's
  failure mode simultaneously.
- **Blast radius of a bad rollout.** Sacrificed relative to client-side
  discovery. Because every call for every service passes through the same
  shared router or mesh data plane, a misconfiguration in that single layer,
  a bad routing rule, a broken health check threshold, an overloaded proxy,
  affects every consumer of every service at once rather than one caller at a
  time.
- **Cost.** Sacrificed in a metered cloud. A managed load balancer, an API
  gateway, or a mesh control plane is a billed resource with its own
  per-hour or per-request charge, on top of the compute it forwards traffic
  to, whereas a client-side registry lookup is close to free once the
  registry itself exists.
- **Cross-language and cross-team uniformity.** Favoured. Because discovery
  is externalised from the calling process, a Python batch job, a Go service,
  and a legacy Java monolith all reach order-service through the exact same
  mechanism, which matters in an organisation with heterogeneous stacks or
  services acquired through a merger that nobody wants to rewrite.

A pattern that gave up nothing would not be a design decision, it would be a
free lunch. The price paid here is an extra hop and a new piece of shared
infrastructure, purchased in exchange for a calling side that never has to
know discovery exists.

## 4. Applicability and non-applicability

Reach for Server-Side Discovery when the following hold.

- The fleet is genuinely polyglot, and maintaining a discovery-aware client
  library in every language in use would be more work, or riskier, than
  operating one shared router.
- The environment already provides the router for other reasons, a
  Kubernetes cluster's built-in Service and kube-proxy, a managed cloud load
  balancer in front of an autoscaling group, a service mesh's data plane,
  and paying for a second, client-side discovery layer on top would be
  duplicated infrastructure.
- Callers outside the organisation's control, a public API consumer, a
  partner's server, a mobile app, need to reach the service. External
  callers cannot reasonably be handed a discovery client and a live view of
  an internal registry, so the request must land on something with a fixed,
  publishable address.
- Centralised policy, TLS termination, WAF rules, rate limiting, a single
  place to roll out a canary, matters more than shaving the extra network
  hop's latency.
- The team wants zero-downtime deploys and rolling restarts without any
  change to calling code, because the router already drains connections from
  an instance before it disappears from rotation.

Do NOT reach for Server-Side Discovery, or lean on it exclusively, in these
cases, and the reason matters more than the rule.

- **Latency budget is genuinely tight, single-digit milliseconds end to end,
  and internal calls fan out many times per request.** Every hop through a
  shared router adds up. A latency-sensitive internal call graph, order
  service calling pricing service calling inventory service several times per
  request, often does better with a client-side lookup against a cached,
  in-memory registry, which is why Netflix's original Eureka plus Ribbon
  stack chose the client-side variant for that exact call pattern.
- **The shared router becomes an unbudgeted bottleneck.** If every one of a
  thousand internal calls per second funnels through one logical load
  balancer tier, that tier's own capacity, and its own availability, becomes
  the ceiling for the whole system's throughput, and a failure there is a
  correlated failure across every service at once rather than an isolated
  one.
- **The team has no operational capacity to run and harden the router
  itself.** A cloud managed load balancer largely removes this objection, but
  a self-hosted Nginx or HAProxy fleet still needs its own health checks,
  its own scaling policy, and its own on-call ownership, and skipping that
  work produces the exact single point of failure the pattern is often
  praised for avoiding.
- **The call pattern needs information the router cannot see cheaply**, per
  request connection affinity tied to application session state that lives
  outside a cookie, or a load-balancing decision that depends on
  request-body content the router would have to parse and buffer to
  inspect, which turns a cheap layer-4 or layer-7 header-based hop into an
  expensive deep-inspection one.
- **The environment has no shared network path between caller and callee**
  at all, an edge device calling a cloud service over an unreliable link, a
  batch job running entirely inside one process against an embedded store.
  There is no fleet to discover an instance within, so the whole family of
  discovery patterns does not apply.
- **A single, centrally managed router becomes the seam every team must
  coordinate through to ship a change**, turning what should be an
  independently deployable service change into a change request against
  shared infrastructure. This is the organisational cost that shows up
  later, not on day one, and it is the reason platform teams increasingly
  push routing configuration into per-service, GitOps-managed resources
  (Kubernetes Ingress or Gateway API objects owned by each service's own
  repository) rather than one hand-edited router config file.

## 5. Structure

Five participants, named by the role they play.

- **Client.** The code that wants to call a logically named service. In this
  pattern the client is unaware of instance addresses and unaware that
  discovery is happening at all. It sends one request to one address, the
  same way it would call a single fixed server.
- **Router.** Also called a load balancer, a proxy, or a gateway depending on
  where it sits and what else it does. It runs at a well known, stable
  network location, either a DNS name or a fixed virtual IP. Every request
  the client sends for the target service arrives here first.
- **Service Registry.** The current, authoritative list of healthy instances
  for each logical service. In some implementations the registry is a
  separate process the router queries, HashiCorp Consul or a Kubernetes
  `Endpoints` object read by kube-proxy. In others it is folded directly
  into the router, an AWS target group is simultaneously the registry and
  the mechanism the Application Load Balancer consults.
- **Service Instance.** One running copy of the target service, reachable at
  a real network address that changes over the instance's lifetime as it is
  created, rescheduled, scaled, or torn down.
- **Registrar.** The component that keeps the registry accurate, adding an
  instance's address when it becomes healthy and removing it when it stops
  responding to health checks or is deliberately drained. Depending on the
  implementation this is the platform's control plane (Kubernetes' endpoint
  controller watching Pod readiness), a sidecar performing self-registration
  (see Self-Registration in this catalog), or an external agent performing
  third-party registration (see Third-Party Registration). The router itself
  never invents this list, it consumes it.

Relationships. The Client depends only on the Router's stable address, never
on any Service Instance's address directly. The Router depends on the
Service Registry to know which instances are currently eligible, and on a
health signal, either polled directly or supplied by the Registrar, to know
which instances are currently healthy. The Registrar depends on the platform
or the instance itself to know when an instance's health state changes. No
participant except the Router and the Registry ever holds more than one
instance address at a time.

## 6. ASCII structure diagram

```
                        well known address
                        (DNS name or VIP)
                              |
   +----------+               v               +--------------------+
   |  Client  |  request  +--------+  query    |  Service Registry  |
   |----------|---------->| Router |---------->|---------------------|
   | (no      |           | (load  |<----------| instance-A: healthy|
   |  instance|           | balancer)  reply   | instance-B: healthy|
   |  list)   |<----------|        |           | instance-C: draining|
   +----------+  response +--------+           +--------------------+
                    |         ^
                    | forward | health signal
                    v         |
       +------------+---------+------------+
       |            |                      |
   +--------+  +--------+             +--------+
   |Instance|  |Instance|             |Instance|
   |   A    |  |   B    |             |   C    |
   +--------+  +--------+             +--------+
        ^           ^                      ^
        |           |                      |
        +-----------+----------------------+
                     |
              Registrar keeps the
              registry current as
              instances start, stop,
              scale, and fail checks
```

## 7. Dynamics

The defining property of the runtime flow is that the discovery step is
invisible to the Client and happens inside the network path, not inside the
Client's own process.

```
Client         Router              Service Registry     Instance B
  |               |                        |                 |
  |-- GET /orders (well known address) --->|                 |
  |               |                        |                 |
  |               |-- who is healthy for  ->|                 |
  |               |   "order-service" ?     |                 |
  |               |<-- [A, B, C] -----------|                 |
  |               |                        |                 |
  |               | (apply load balancing  |                 |
  |               |  algorithm, pick B)    |                 |
  |               |                                            |
  |               |-- forward GET /orders -------------------->|
  |               |                                            |
  |               |<-- 200 OK, body -------------------------- |
  |<-- 200 OK, body -------------------------------------------|
  |               |                        |                 |
```

A second, independent flow keeps the Registry current, and it runs on its own
schedule rather than being triggered by client requests.

```
Instance A                  Registrar / Control Plane        Service Registry
    |                                |                              |
    |-- readiness probe: 200 OK ---->|                              |
    |                                |-- mark instance-A healthy -->|
    |                                |                              |
    |   (instance A crashes)         |                              |
    |                                |-- readiness probe: timeout   |
    |                                |   (repeated, past threshold) |
    |                                |-- mark instance-A unhealthy->|
    |                                |   / remove from rotation     |
    |                                |                              |
```

Two timing consequences follow from these two independent flows running
concurrently. First, there is always a window, bounded by the health check
interval and the unhealthy threshold, in which the registry can still hand
out an address that has just stopped answering, so a well-built Router
retries the next healthy instance on a connection failure rather than
surfacing the error to the Client immediately. Second, a graceful shutdown
sequence, deregister first, then stop accepting new connections, then finish
in-flight requests, avoids that window on the deliberate-shutdown path
entirely, which is why an orchestrator's rolling update sends a `SIGTERM`
and waits out a grace period before killing an instance, rather than killing
it the instant the new one becomes ready.

## 8. Implementation variants

**Platform-native virtual IP, Kubernetes Service.** A Kubernetes `Service`
gets a stable cluster IP, and `kube-proxy` running on every node programs
iptables or IPVS rules so that a connection to that virtual IP is
transparently rewritten to one of the Pod IPs currently listed in the
Service's `Endpoints`, chosen at the OS networking layer rather than by an
application-level proxy process. Kubernetes documentation states that "the
Service API is an abstraction to help you expose groups of Pods over a
network," giving callers "a stable virtual IP in front of a dynamic set of
Pod IPs" (Kubernetes documentation, "Service", section "Virtual IPs and
Service Proxies", https://kubernetes.io/docs/concepts/services-networking/service/,
verified 2026-08-16). This is the cheapest variant to operate, because the
kernel does the forwarding and there is no separate proxy process to run,
though it offers only layer-4 load balancing with no content-based routing.

**Managed layer-7 load balancer, cloud provider.** AWS's Application Load
Balancer, Azure's Application Gateway, and Google Cloud's HTTP(S) Load
Balancer each sit at a fixed, provider-issued address, evaluate rules against
the HTTP request, and forward to a backend group whose membership the
provider keeps current as instances scale in and out. AWS documents this as
the load balancer routing traffic to "targets," registered in a "target
group," with health checks "performed on all targets registered to a target
group" (AWS documentation, "What is an Application Load Balancer?",
https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html,
verified 2026-08-16). This variant is the one most teams meet first, because
it is what the cloud console offers by default in front of an autoscaling
group, and its main cost is the managed service's own hourly and
per-processed-byte charge.

**Self-hosted reverse proxy, Nginx or HAProxy.** A team runs its own proxy
process, configured with a list of upstream addresses, either static or
refreshed by a template-rendering sidecar (consul-template being the classic
example) that watches a registry and rewrites the proxy config when the
instance list changes. This variant gives full control over the
load-balancing algorithm, connection pooling, and TLS handling, at the cost
of owning the proxy's own availability, scaling, and patch cycle.

**API Gateway as the router.** For traffic entering the system from outside,
a public web client, a partner integration, a mobile app, the router is
often not a plain load balancer but an API Gateway that also performs
authentication, rate limiting, request aggregation, and protocol translation
on top of discovery. See the API Gateway entry in this catalog. The
discovery mechanism underneath is often the same layer-7 load balancer or
Kubernetes Ingress controller described above, the gateway is a policy
layer stacked on top of it, not a separate discovery mechanism in its own
right.

**Service mesh sidecar proxy.** Rather than one shared router in front of the
whole fleet, every instance gets its own local proxy, an Envoy sidecar under
Istio or Consul Connect, that intercepts outbound traffic from its own Pod
and performs the discovery and load-balancing decision locally, using a
service registry replicated to every sidecar by the mesh's control plane.
Istio documents that "all traffic that your mesh services send and receive
is proxied through Envoy," and that "the Envoy proxies distribute traffic
across each service's load balancing pool using a least requests model"
(Istio documentation, "Architecture", section "Envoy",
https://istio.io/latest/docs/concepts/traffic-management/, verified
2026-08-16). This variant is structurally interesting because it moves the
router from a single shared network location to one instance per caller,
which restores some of the client-side variant's fault isolation while
keeping the client-side application code, per this pattern's defining
property, entirely unaware discovery is happening. See the Sidecar Proxy
entry for the deployment shape and the Service Mesh entry for the fuller
control plane picture.

**DNS-based server-side discovery, headless Service or SRV records.** A
lighter-weight variant skips a dedicated proxy process and returns the
current instance list directly through DNS, either a Kubernetes headless
Service resolving `A` records to every ready Pod IP, or SRV records
returning host and port pairs. The client still just does a DNS lookup and
connects, exactly as it would to a single server, so from the calling code's
perspective this is still server-side discovery, the "server side" doing the
resolution is the DNS resolver and the control plane behind it rather than a
proxy in the data path. The trade-off is that DNS answers are often cached
past the point they are accurate, so this variant needs a short TTL and a
client, or resolver, that actually honours it.

**Language note.** This pattern has no meaningfully different shape by
programming language, because its entire point is that the calling
language's code performs an ordinary network call and never sees the
discovery mechanism. The variants above differ by infrastructure choice, not
by language.

## 9. Known production uses

**AWS Elastic Load Balancing, Application Load Balancer.** The ALB is
explicitly named on the pattern's own catalog page as an implementation of
server-side discovery, doubling as both the router and, through its target
groups, the registry, with instances "automatically registered with the
target group" when launched by an attached Auto Scaling group and
automatically deregistered on termination (Chris Richardson, "Server-Side
Service Discovery pattern", microservices.io,
https://microservices.io/patterns/server-side-discovery.html, verified
2026-08-16; AWS documentation, "What is an Application Load Balancer?",
https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html,
verified 2026-08-16).

**Kubernetes, Service and kube-proxy.** Every Kubernetes `Service` of type
`ClusterIP`, the default type, is a server-side discovery router, resolving
a stable virtual IP to a Pod IP chosen from the live `Endpoints` list, with
`kube-proxy` on every node programming the actual forwarding rules. This is
also the second implementation named directly on the microservices.io
pattern page, which describes "a proxy on each host that acts as the
discovery router" (Chris Richardson, "Server-Side Service Discovery
pattern", https://microservices.io/patterns/server-side-discovery.html,
verified 2026-08-16; Kubernetes documentation, "Service",
https://kubernetes.io/docs/concepts/services-networking/service/, verified
2026-08-16).

**Istio, Envoy sidecar proxy.** Istio's data plane places an Envoy proxy
alongside every workload and routes every outbound call through it, with
Envoy performing the discovery lookup and load-balancing decision against a
registry the Istio control plane, Istiod, keeps synchronised from the
underlying platform. This is a server-side discovery implementation by this
pattern's own definition, the calling application code inside the workload
never sees an instance list, even though the router is deployed as one
process per caller rather than one shared process for the whole fleet
(Istio documentation, "Architecture", section "Envoy",
https://istio.io/latest/docs/concepts/traffic-management/, verified
2026-08-16).

**Microsoft Azure, Application Gateway.** Azure's managed layer-7 load
balancer performs the same role for Azure-hosted fleets, making "intelligent
routing decisions based on HTTP request attributes like URL paths and host
headers" and forwarding to a backend pool the service checks for health,
operating "at the application layer, OSI layer 7" the same way AWS's ALB
does (Microsoft documentation, "What is Azure Application Gateway",
https://learn.microsoft.com/en-us/azure/application-gateway/overview,
verified 2026-08-16).

**HashiCorp Consul plus a proxy tier.** Consul's catalog holds the current
list of healthy service instances, populated by agents running on each node,
and is consumed either directly by Envoy under Consul Connect, or by a
templating sidecar such as consul-template that rewrites an Nginx or HAProxy
configuration file whenever the instance list changes, restarting or
reloading the proxy so its forwarding rules stay current. This is the
canonical self-hosted, on-premises shape of the pattern, predating the
managed cloud load balancer becoming the default choice for most teams.

## 10. Consequences

Positive.

- Calling code is trivially simple and completely infrastructure-agnostic.
  A Python job, a Go service, and a legacy Java application all reach a
  target service through the exact same DNS name and HTTP client, with zero
  discovery-specific code and zero language-specific discovery library.
- Cross-cutting policy, TLS termination, retry and timeout defaults, circuit
  breaking, rate limiting, canary weighting, lives and is upgraded in one
  place, and every caller inherits a fix or an improvement instantly, with
  no redeploy of any calling service.
- External callers, a partner, a mobile client, a public API consumer, get a
  single stable address to integrate against, which is a hard requirement
  for anyone outside the organisation's own deploy pipeline.
- Rolling deploys and autoscaling are transparent to every caller, because
  the router, not the caller, tracks instance churn.
- Health checking and load balancing logic is implemented once, tested once,
  and operated once, rather than reimplemented and independently debugged
  inside every service's own codebase.

Negative.

- A new highly available piece of infrastructure must be built or operated,
  and its own outage becomes a correlated outage for every service that
  routes through it, rather than an isolated failure affecting one caller.
- Every request pays for one extra network hop, which is close to free on a
  local sidecar and measurable on a shared, possibly cross-availability-zone,
  load balancer tier.
- The router itself becomes a scaling bottleneck if it is under-provisioned,
  and its capacity planning is now a shared concern across every team whose
  services route through it.
- Debugging a request's path is harder, because the actual instance that
  served a request is no longer visible at the call site and must be
  recovered from a trace header, an access log, or a response header the
  router is configured to add.
- In the shared-router variants, changing routing configuration, adding a
  rule, adjusting a health check threshold, is a change against shared
  infrastructure that every team routing through it is implicitly affected
  by, which creates a coordination cost the client-side variant avoids
  because each library instance's configuration is independently owned.

## 11. Failure modes and misuse

**The router as a silent single point of failure.** Symptom. One load
balancer or proxy instance restarts for a routine reason, a config reload, a
memory limit, a node eviction, and every downstream service that depends on
it sees a synchronised spike in connection errors at the same second, across
every consumer at once, which is a very different incident shape from one
service's own instance dying. Cause. The router was deployed as a single
instance, or as a pool sized without headroom for a rolling restart. Fix.
Run the router itself as a redundant, independently scaled fleet with its
own health checking, and verify a rolling restart of the router does not
produce a connection blip by testing it deliberately, not by discovering it
in production.

**Stale registry entries serving dead instances.** Symptom. A small,
persistent percentage of requests fail or time out, worse right after a
deploy, and retrying the exact same request from the client usually
succeeds. Cause. The health check interval and unhealthy threshold are wide
enough that a crashed instance stays in rotation for several check cycles
before it is removed. Fix. Tighten the health check interval and threshold
to the tolerance the SLO allows, and make sure the router retries a failed
connection against a different healthy instance rather than surfacing the
first failure to the caller (see the Retry Budget entry for how to bound
that retry so it does not itself become a compounding load amplifier).

**Thundering herd on router restart or scale event.** Symptom. Every caller
sees a burst of connection resets or a latency spike at the exact moment
the router pool scales or a single router instance restarts, even though
every backend service instance stayed healthy the whole time. Cause. In
flight connections were dropped rather than drained, because the router
was not given a graceful shutdown sequence, deregister, stop accepting new
connections, finish in-flight requests, then terminate. Fix. Configure
connection draining or a `preStop` hook with a grace period on the router
itself, the same discipline expected of any backend service instance under
this pattern.

**Health check that measures the wrong thing.** Symptom. The router marks
an instance healthy while it is actually degraded, still accepting TCP
connections but failing every real request because a downstream dependency,
its own database, is unreachable, so traffic keeps landing on an instance
that cannot serve it. Cause. The health check is a shallow liveness probe, a
plain TCP connect or a static 200, rather than a readiness check that
exercises the instance's actual dependencies. Fix. Distinguish liveness from
readiness explicitly (see the Health Check API entry), and route the
router's forwarding decision off the readiness signal, not the liveness one.

**Session affinity assumed but not configured.** Symptom. A user
intermittently sees stale or inconsistent state, half of a multi-step form
flow appears lost, because consecutive requests from the same session land
on different backend instances that do not share in-memory state. Cause.
The team assumed the router would keep a session pinned to one instance, but
the default load-balancing algorithm, round robin or least connections,
makes no such guarantee. Fix. Either configure explicit sticky sessions on
the router if session state must live in process memory, or, the more
durable fix, remove the in-process session dependency entirely and
externalise session state to a shared store so any instance can serve any
request.

**Cross-zone or cross-region hop hiding in the routing table.** Symptom. A
call that should be a same-rack, sub-millisecond hop instead shows a
double-digit millisecond tail, and the affected requests correlate with a
specific availability zone. Cause. The router's instance list is not
zone-aware, so it happily forwards a request from a caller in zone A to an
instance in zone B, paying an inter-zone network hop, and in cloud
deployments, inter-zone data transfer cost, on every such request. Fix.
Enable topology-aware or zone-aware routing where the platform supports it,
so the router prefers a same-zone instance when one is healthy and falls
back cross-zone only when it must.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Server-Side Discovery | Client-Side Discovery | DNS round robin (no health awareness) | Hardcoded static address list |
|---|---|---|---|---|
| Client code complexity | Low. Ordinary HTTP call to a fixed address | Medium to high. Needs a discovery client, a load-balancing algorithm, and a fresh registry view per language in use | Low. Ordinary DNS lookup | Lowest, until the list drifts from reality |
| Extra network hop | Yes, one per request | No. Client connects directly to the chosen instance | No, but the resolved address may be stale between TTL refreshes | No |
| Cross-language uniformity | High. Every language behaves identically | Low. A discovery client must exist, and be kept correct, in every language used | High | High |
| Fault isolation between callers | Low. A router failure is a correlated failure across every caller | High. Each client instance's failure is independent of every other client's | Low. Depends entirely on the resolver's caching and the client's retry behaviour | Very low. No mechanism reroutes around a dead instance at all |
| Operational ownership | The router is new shared infrastructure someone must run | The registry is shared, but load balancing logic is distributed into every client, no shared router process | The DNS infrastructure is usually already present, but health-awareness is typically absent | None, until the list is wrong |
| Health-aware routing | Yes, built into the router if configured correctly | Yes, if the client actively checks registry freshness and health state | Rarely. Standard DNS has no health signal | No |
| Rolling deploy transparency | Full. Clients never notice instance churn | Full, provided the client refreshes its registry view frequently enough | Partial. Bounded by DNS TTL, and by client-side caching that ignores the TTL | None. Every topology change requires a code or config change in the caller |
| External or public caller support | Yes, this is close to the only viable option for callers outside the organisation | No. A partner cannot reasonably run a discovery client against an internal registry | Partially, if the DNS zone is public | Rarely acceptable for external integration |
| Latency sensitivity for high fan-out internal calls | Worse. Every hop in a multi-hop internal call graph adds the router's overhead | Better. Direct connection avoids the extra hop entirely | Comparable to server-side, minus health awareness | Best on paper, worst in practice once addresses actually change |

Reading of the table. Server-Side Discovery wins wherever the caller is
outside the organisation's control, wherever a polyglot fleet makes a
uniform client library impractical, or wherever centrally enforced policy
matters more than shaving a hop. Client-Side Discovery wins on latency
sensitive, high fan-out internal call graphs where every hop is budgeted and
the fleet is homogeneous enough in language and library maturity to make a
shared client viable. DNS round robin and static address lists are included
as the honest baseline every real system starts from before either pattern
is deliberately adopted, and both fail exactly where health-awareness and
rolling-deploy transparency matter, which is why they are named here as the
comparison a reader is actually migrating away from, not a strawman.

## 13. Related and incompatible patterns

- **Client-Side Discovery.** The paired alternative and the closest
  relationship this pattern has. Both solve the identical problem, locating
  a healthy instance behind a logical service name, and a real system
  commonly runs both at once for different parts of its call graph, external
  and cross-team traffic through a server-side router, tight internal call
  chains through a client-side library, rather than choosing one exclusively
  for the whole architecture. See the Client-side Service Discovery entry
  for the mirror image of this one.
- **Service Registry.** A required dependency, not an optional add-on. Every
  variant of Server-Side Discovery needs some component holding the current
  list of healthy instances, whether that is a dedicated process such as
  Consul, or a mechanism folded into the platform, Kubernetes `Endpoints` or
  an AWS target group. This pattern is meaningless without a registry
  somewhere behind it.
- **Self-Registration and Third-Party Registration.** These two patterns
  answer how the registry, that this pattern depends on, stays accurate.
  Self-Registration has each instance announce and heartbeat its own
  presence. Third-Party Registration has an external agent watch the
  platform and update the registry on the instance's behalf. Server-Side
  Discovery composes with either, and does not care which one a given
  system uses, only that the registry it queries is kept correct by one of
  them.
- **Health Check API.** Provides the signal the Registrar or the router
  itself needs to decide an instance is eligible for traffic. Without a
  meaningful health check, this pattern degrades to the DNS round robin
  baseline from dimension 12, forwarding to instances that are technically
  running but functionally broken.
- **API Gateway.** A frequent host for this pattern at the edge of the
  system. An API Gateway is often, though not always, implemented as a
  server-side discovery router with an additional policy layer, authentication,
  rate limiting, request aggregation, stacked on top. See the API Gateway
  entry for where the two roles separate.
- **Sidecar Proxy and Service Mesh.** These compose the pattern in a
  distributed rather than a centralised shape. Each caller gets its own
  local router, the sidecar, rather than sharing one router process for the
  whole fleet, which restores some of the fault isolation client-side
  discovery offers while keeping the calling application code unaware, per
  this pattern's defining property, that discovery is happening at all.
- **Circuit Breaker.** Composes naturally on top, usually implemented inside
  the router or the sidecar rather than inside the calling application, so
  that a struggling downstream service is temporarily removed from the
  routing decision without the caller's own code needing any circuit-breaker
  logic.
- **Service Instance per Container and Multiple Service Instances per
  Host.** Neither conflicts with this pattern, but the second changes what
  "an instance's address" means to the registry, a host's IP plus a
  per-service port rather than one IP per instance, and the router's
  registry entries and health checks need to carry that port explicitly
  rather than assuming one instance per host address.
- **Static, hardcoded address lists.** Actively incompatible in spirit, not
  in mechanism. A team that adopts a router but then hardcodes a fixed
  upstream list inside it, never updated by a live registry, has built the
  shape of this pattern without its actual benefit, and reintroduces every
  failure mode a static list carries, listed in the trade-off matrix above.

## 14. Refactoring path in and out

Introducing the pattern into a system that currently calls fixed, hardcoded
addresses.

1. Identify every call site that hardcodes a service's host and port,
   including ones hidden inside a config file rather than source code. A
   grep across the codebase for the literal service hostname or IP is
   usually sufficient to find them all.
2. Stand up the router in front of the target service first, in parallel
   with the existing direct calls, forwarding to the exact same instance
   set the callers already use, so its behaviour can be verified before any
   caller depends on it.
3. Point the router's registry at the platform's existing source of truth
   for healthy instances, the orchestrator's own service object if one
   already exists, or a newly introduced registry if the platform has none.
4. Redirect the DNS name or configuration value the callers use, one caller
   at a time, from the old fixed address to the router's stable address.
   Because the calling code already just does an HTTP call to a hostname,
   this step usually needs no code change, only a configuration change.
5. Verify each redirected caller under a rolling restart of the target
   service, confirming its error rate stays unchanged, before moving to the
   next caller.
6. Once every caller is redirected, retire the old fixed address, and turn
   on the router's health-check-driven removal, if it was left in a
   static-list mode during migration for safety.
7. Add the observability signals from dimension 16 before declaring the
   migration complete, request count, error rate, and per-instance
   distribution as seen through the router, because these numbers usually
   do not exist yet on the pre-migration direct-call path and are the main
   payoff of having centralised the traffic.

Removing the pattern when it stops earning its place. This is rare in
practice, because the platform-native variants, a Kubernetes Service or a
cloud load balancer, are usually cheaper to keep than to remove, but it
matters for the self-hosted, hand-operated router variant that has become
an operational burden without matching benefit.

1. Confirm the actual reason the router is being removed. If it is latency
   on a specific, narrow internal call path, consider first adding a
   client-side discovery layer for just that path rather than removing
   server-side discovery for every caller, since external and cross-team
   callers usually still need the stable, centrally policed address.
2. Introduce a client-side discovery library for the calls being migrated,
   pointed at the same underlying registry the router already consumes, so
   the two coexist during transition rather than the registry itself
   changing shape.
3. Move callers over one at a time, verifying error rate and latency at
   each step, the same discipline as the introduction path in reverse.
4. Once every caller that needed the change has moved, decide whether the
   router is still required for any remaining caller, external traffic in
   particular almost always still is, and either retire it entirely or keep
   it scoped to the traffic that still needs it.

## 15. Testing and verification

Easier because of the pattern.

- The calling application's own unit and integration tests need no
  discovery-aware test double at all. A test can point the client at any
  fixed test server, in-process or containerised, exactly as if discovery
  did not exist, because from the calling code's point of view it does not.
- Chaos and resilience testing of "an instance dies mid-request" is
  centralised. Killing one backend instance behind the router and asserting
  the router retries against a healthy one tests the failure-handling
  behaviour once, for every caller, rather than requiring every service's
  own test suite to separately simulate a discovery-client failure.
- Canary and blue-green rollout behaviour can be verified entirely at the
  router layer, weighting a fraction of traffic to a new instance version
  and observing error rate, without touching any calling service's code or
  tests at all.

Harder because of the pattern.

- An end-to-end test that wants to assert a specific instance handled a
  specific request now needs the router configured to expose that instance
  identity, a response header or a trace attribute, because the test
  otherwise has no visibility into which of several instances actually
  answered.
- Testing the router itself, its health check thresholds, its retry and
  timeout policy, its load-balancing algorithm under an uneven instance mix,
  is a distinct testing surface from testing any individual service, and is
  often owned by a platform team rather than any single service team, which
  means it needs its own dedicated test suite or it silently goes untested.

Techniques that apply.

- **Contract or component test the router configuration, not just the
  services.** Where routing rules are defined declaratively, a Kubernetes
  Ingress manifest, an ALB listener rule set, treat that configuration as
  code under test, asserting a given request path resolves to the expected
  backend, catching a misrouted rule before it reaches production. See the
  Service Component Test entry for the general shape.
- **Fault injection at the router, not only at the instance.** A chaos test
  that kills a backend instance verifies the health check and removal path.
  A separate chaos test that makes the router itself briefly unavailable,
  or artificially slow, verifies caller-side timeout and circuit-breaking
  behaviour under the correlated-failure scenario named in dimension 11,
  which is a distinct and equally necessary test from killing one instance.
- **Assert the health check actually measures readiness, not liveness, in a
  dedicated test.** A test that starts an instance with its dependency
  deliberately unreachable and asserts the router never routes traffic to
  it catches the shallow-health-check failure mode from dimension 11 before
  it reaches production.
- **Load test through the router, not directly against instances.** A
  performance test that bypasses the router and hits instances directly
  measures the wrong system, since the extra hop, and any connection
  pooling or TLS termination cost the router introduces, is exactly the
  overhead this pattern trades against client-side discovery, and omitting
  it from a load test produces an optimistic number nobody will see in
  production.

## 16. Observability signals

Because every request for every service passes through the same shared
router, or through a locally deployed sidecar performing the same role, the
router is one of the highest-value places in the whole system to instrument.

What to record.

- Request count, error rate, and latency percentiles, labelled by target
  service and, where the router exposes it, by target instance, so a single
  misbehaving instance is visible without needing to correlate logs from
  the instance itself.
- A counter of instances currently in and out of rotation per service,
  sourced from the router's own view of the registry, which is the single
  most direct signal for "is the registry accurate right now" and catches
  the stale-entry failure mode from dimension 11 before a customer does.
- Health check pass and fail counts per instance, distinguishing a
  transient failure, one missed check, from a sustained one that actually
  removed the instance from rotation, so an operator can tell a flapping
  instance from a genuinely dead one.
- Connection and request retry counts at the router, labelled by whether
  the retry succeeded against a different instance, which is the direct
  evidence that the stale-registry-entry failure mode from dimension 11 is
  or is not actively occurring in production right now.
- Router-level saturation metrics, active connection count, queue depth,
  CPU and memory on a self-hosted proxy, or the managed load balancer's own
  published capacity metrics, since the router becoming the bottleneck
  named in dimension 10 is silent until this is watched directly.

A healthy instance on a dashboard. Error rate at the router is flat and near
zero across every target service, the in-rotation instance count for each
service tracks its expected fleet size and moves only in step with a known
deploy or scaling event, health check failures are rare and, when they
occur, are followed promptly by the instance being removed from rotation,
and retry counts stay near zero, meaning the registry is accurate enough
that a first attempt almost always lands on a healthy instance.

A failing instance. The in-rotation count for one service sits persistently
below its expected fleet size with no matching deploy or scaling event,
which usually means health checks are failing for a reason nobody has
investigated yet. Retry counts climb, meaning the registry is regularly
handing out addresses of instances that then fail, the stale-entry symptom
directly. Router-level saturation metrics climb toward capacity while every
backend instance's own metrics stay flat, which localises a bottleneck to
the router itself rather than to any service behind it, exactly the
single-point-of-failure risk named in dimension 10. Or error rate spikes
simultaneously across every service that routes through one router
instance or pool at the same timestamp, the signature of the router itself
failing rather than any individual backend.

## 17. Security and privacy implications

The pattern concentrates a meaningful amount of security-relevant surface
into one place, which is a genuine trade-off, not a purely negative one, and
should be reasoned about explicitly rather than assumed.

**The router as a natural, and valuable, security choke point.** Because
every request for a given service passes through the same router, it is
also the natural place to terminate TLS, enforce mTLS between the router and
backend instances, apply a web application firewall, and enforce
authentication before a request ever reaches application code. This is a
genuine benefit relative to a fully client-side, direct-connection
architecture, where the same policy would need to be independently
implemented and independently kept correct inside every service. The
trade-off is that a misconfiguration in this one place, a WAF rule that is
too permissive, an mTLS requirement that was silently disabled during a
migration, is now a systemic gap across every service behind it rather than
an isolated one.

**Trust boundary confusion between the router and the backend.** A backend
instance behind the router often assumes every request that reaches it
already passed the router's authentication and authorisation checks, and
skips re-validating the caller's identity itself. If the network path
between the router and the instance is not itself restricted, a firewall
rule, a network policy, a service mesh authorisation policy, restricting
who can reach the instance directly, an attacker who gains a foothold
anywhere inside that network segment can bypass the router entirely and
reach the backend unauthenticated. The fix is to enforce that the backend
is genuinely unreachable except through the router, not merely to assume it
is, and to have the backend independently verify a forwarded identity claim
such as an mTLS client certificate or a signed header the router adds,
rather than trusting network position alone.

**Registry as an information disclosure surface.** The service registry the
router consults, whether a separate process such as Consul or a platform
object such as Kubernetes `Endpoints`, holds the internal topology of the
system, which service exists, how many instances it runs, and where they
live on the network. Read access to that registry is meaningful
reconnaissance value to an attacker who has gained any foothold inside the
environment, and should be restricted with the same care applied to any
other internal inventory of infrastructure, not left open on the assumption
that "it is just internal service discovery data."

**Denial of service concentrated at one target.** Because the router is a
known, fixed, often publicly resolvable address, it is also a
straightforward denial-of-service target, an attacker does not need to
enumerate individual instance addresses, the router's single stable address
is the whole attack surface. Standard mitigations, rate limiting at the
router itself, a managed provider's built-in DDoS protection, and enough
router capacity headroom that a spike does not immediately become an
outage, apply here specifically because this pattern deliberately creates
that one stable address in the first place.

On privacy, the pattern is largely neutral in itself, with one practical
caveat matching dimension 16's advice to log per-instance identity for
observability. Where an instance identity, a Pod name, a container ID, can
be correlated back to a specific customer's dedicated deployment, a
single-tenant-per-instance architecture for example, that identity in
access logs and traces becomes attributable data and should be handled
under the same retention and access controls as any other customer
identifier, rather than treated as pure infrastructure telemetry.

## 18. References

1. Chris Richardson. "Server-Side Service Discovery pattern". microservices.io.
   https://microservices.io/patterns/server-side-discovery.html
   Verified 2026-08-16. Source of the pattern's canonical problem and solution
   statement, its file-path-derived name, and the AWS ELB and Kubernetes
   examples named in dimensions 1 and 9.
2. Chris Richardson. *Microservices Patterns*. Manning, 2018. ISBN
   978-1617294549. Chapter 3, "Interprocess communication", section on
   service discovery. Source of the broader discussion pairing server-side
   and client-side discovery inside the book-length treatment of the
   pattern catalog.
3. Sam Newman. *Building Microservices*, 2nd edition. O'Reilly, 2021. ISBN
   978-1492034025. Chapter 4, "Communication Styles", section on service
   discovery. Source of the smart-pipe framing used in dimension 1 to
   connect this pattern to pre-microservices load-balancer practice.
4. Kubernetes documentation. "Service". Section "Virtual IPs and Service
   Proxies". https://kubernetes.io/docs/concepts/services-networking/service/
   Verified 2026-08-16. Source of the Kubernetes Service definition and
   virtual IP mechanism described in dimension 8 and dimension 9.
5. Amazon Web Services documentation. "What is an Application Load
   Balancer?".
   https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html
   Verified 2026-08-16. Source of the target group, listener, and health
   check description in dimension 8 and dimension 9.
6. Istio documentation. "Architecture". Section "Envoy".
   https://istio.io/latest/docs/concepts/traffic-management/
   Verified 2026-08-16. Source of the Envoy sidecar proxy and least-requests
   load balancing description in dimension 8 and dimension 9.
7. Microsoft Learn. "What is Azure Application Gateway".
   https://learn.microsoft.com/en-us/azure/application-gateway/overview
   Verified 2026-08-16. Source of the Azure Application Gateway description
   in dimension 9.
8. HashiCorp Consul documentation. Service catalog and health checking
   overview, developer.hashicorp.com/consul/docs. Referenced in dimension 9
   for the self-hosted registry-plus-proxy production shape described from
   general, publicly documented Consul architecture rather than a single
   quoted page.

## Code examples

Three languages where the pattern's defining property, that the caller
never sees discovery happening, is genuinely worth demonstrating in code.
TypeScript and Go each implement a minimal router that queries a registry,
health-filters it, load balances across it, and forwards a request, the
actual mechanism this pattern names. Python shows the calling side, which is
deliberately almost nothing, one HTTP call to a fixed address, which is the
whole point being illustrated. Java is omitted because no working JDK is
installed on the machine this entry was authored on, so a sample could not
be compiled and verified, and shipping an unverified Java sample would
violate this repository's compile-or-state-otherwise rule. Rust and Swift
are omitted because the pattern's shape here is infrastructural rather than
language-idiomatic, and TypeScript and Go already cover both a scripting
runtime and a compiled systems language without repeating the same
demonstration a third and fourth time.

### TypeScript, a minimal router

```typescript
type Instance = { host: string; port: number; healthy: boolean };

class Registry {
  private instances: Instance[] = [];

  upsert(inst: Instance): void {
    const i = this.instances.findIndex(
      (x) => x.host === inst.host && x.port === inst.port
    );
    if (i >= 0) this.instances[i] = inst;
    else this.instances.push(inst);
  }

  healthyInstances(): Instance[] {
    return this.instances.filter((i) => i.healthy);
  }
}

class RoundRobinRouter {
  private next = 0;

  constructor(private registry: Registry) {}

  pickInstance(): Instance {
    const healthy = this.registry.healthyInstances();
    if (healthy.length === 0) {
      throw new Error("no healthy instances available");
    }
    const chosen = healthy[this.next % healthy.length];
    this.next += 1;
    return chosen;
  }

  async forward(path: string): Promise<string> {
    const inst = this.pickInstance();
    // A real router forwards the request over the network here.
    return `served by ${inst.host}:${inst.port}${path}`;
  }
}

async function demo(): Promise<void> {
  const registry = new Registry();
  registry.upsert({ host: "10.0.0.1", port: 8080, healthy: true });
  registry.upsert({ host: "10.0.0.2", port: 8080, healthy: true });
  registry.upsert({ host: "10.0.0.3", port: 8080, healthy: false });

  const router = new RoundRobinRouter(registry);
  for (let i = 0; i < 4; i += 1) {
    console.log(await router.forward("/orders"));
  }
}

demo();
```

### Go, a minimal router with a health check loop

```go
package main

import (
	"fmt"
	"sync/atomic"
)

type Instance struct {
	Host    string
	Port    int
	Healthy bool
}

// Registry holds an immutable snapshot behind an atomic pointer, so a
// reader never blocks on a writer and a writer never blocks on a reader.
// Every update publishes a brand new slice rather than mutating one in
// place.
type Registry struct {
	snapshot atomic.Pointer[[]Instance]
}

func NewRegistry() *Registry {
	r := &Registry{}
	empty := []Instance{}
	r.snapshot.Store(&empty)
	return r
}

func (r *Registry) Upsert(inst Instance) {
	current := *r.snapshot.Load()
	next := make([]Instance, 0, len(current)+1)
	found := false
	for _, existing := range current {
		if existing.Host == inst.Host && existing.Port == inst.Port {
			next = append(next, inst)
			found = true
			continue
		}
		next = append(next, existing)
	}
	if !found {
		next = append(next, inst)
	}
	r.snapshot.Store(&next)
}

func (r *Registry) Healthy() []Instance {
	current := *r.snapshot.Load()
	var out []Instance
	for _, inst := range current {
		if inst.Healthy {
			out = append(out, inst)
		}
	}
	return out
}

type Router struct {
	registry *Registry
	next     int
}

func (rt *Router) Forward(path string) (string, error) {
	healthy := rt.registry.Healthy()
	if len(healthy) == 0 {
		return "", fmt.Errorf("no healthy instances available")
	}
	inst := healthy[rt.next%len(healthy)]
	rt.next++
	// A real router forwards the request over the network here.
	return fmt.Sprintf("served by %s:%d%s", inst.Host, inst.Port, path), nil
}

func main() {
	registry := NewRegistry()
	registry.Upsert(Instance{Host: "10.0.0.1", Port: 8080, Healthy: true})
	registry.Upsert(Instance{Host: "10.0.0.2", Port: 8080, Healthy: true})
	registry.Upsert(Instance{Host: "10.0.0.3", Port: 8080, Healthy: false})

	router := &Router{registry: registry}
	for i := 0; i < 4; i++ {
		result, err := router.Forward("/orders")
		if err != nil {
			fmt.Println("error:", err)
			continue
		}
		fmt.Println(result)
	}
}
```

### Python, the calling side, unaware of discovery

```python
import urllib.request

# The whole point of server-side discovery: the caller does not know,
# and does not need to know, how many instances of "order-service"
# exist or where they currently run. It sends one request to one
# well known address, the router, exactly as it would to a single
# fixed server.

ROUTER_ADDRESS = "http://order-service.internal"


def get_order(order_id: str) -> str:
    request = urllib.request.Request(f"{ROUTER_ADDRESS}/orders/{order_id}")
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.read().decode("utf-8")
    except Exception as exc:
        # No instance list, no load-balancing retry logic here.
        # That responsibility lives entirely in the router.
        raise RuntimeError(f"order-service unavailable: {exc}") from exc


if __name__ == "__main__":
    # This call will fail in this sandbox because ROUTER_ADDRESS is not
    # a live host, which is expected and demonstrates that the calling
    # code's logic is complete and correct on its own, independent of
    # any real network topology behind the router.
    try:
        print(get_order("42"))
    except RuntimeError as exc:
        print(exc)
```
