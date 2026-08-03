---
name: Server-Side Service Discovery
slug: server-side-service-discovery
family: 10-microservices
category: Microservices
aliases: [Router-Based Discovery, Load-Balancer Discovery, Proxy-Based Discovery]
first_described: "Richardson, microservices.io, documented as one of two discovery variants alongside client-side discovery"
maturity: canonical
related: [client-side-service-discovery, api-gateway, circuit-breaker, remote-procedure-invocation, self-contained-service]
incompatible_with: []
verified: 2026-08-03
---

# Server-Side Service Discovery

## 1. Name, aliases, and lineage

The canonical name is Server-Side Service Discovery. It names one of the two
resolution strategies a client can use to find a network location for a
service instance whose address is not fixed. The name is drawn directly from
the way the pattern splits responsibility. discovery of instance locations
happens on the server side of the request path, inside infrastructure the
client does not own, rather than inside the calling process itself.

Chris Richardson documents the pattern under this exact name on
microservices.io, describing it as a router, also called a load balancer, that
runs at a well known location, queries a service registry, and forwards a
client's request to an available instance
([Server-Side Service Discovery pattern, microservices.io](https://microservices.io/patterns/server-side-discovery.html),
verified 2026-08-03). The same page names the paired alternative, Client-Side
Service Discovery, where the calling process itself queries the registry and
picks an instance before making the call. The two patterns solve the identical
problem with the resolution logic moved to opposite ends of the request.

Common aliases in the field reflect the concrete infrastructure that
implements the idea rather than the abstract pattern name. Router-Based
Discovery and Load-Balancer Discovery are used interchangeably with the
canonical name because, in practice, the router is almost always a load
balancer or a reverse proxy. Proxy-Based Discovery is the name used inside
service mesh literature, where the router is a sidecar proxy deployed next to
every service instance rather than a single centralized appliance. All three
names describe the same structural decision, that the piece of software making
the routing decision is not the calling application's own code.

There is no single inventor credited with the pattern the way Gamma, Helm,
Johnson, and Vlissides are credited with the Gang of Four catalog. Server-side
discovery predates the term microservices. Hardware load balancers performing
exactly this function, terminate a client connection at a well known virtual
IP, consult a table of live backend addresses, forward the request, existed in
data centers throughout the 1990s and 2000s. What changed with the rise of
containerized microservices is the frequency of change. Backend addresses that
used to change a few times a year under a manually maintained load balancer
configuration now change every time a container scheduler reschedules a pod,
which can be dozens of times an hour in a busy cluster. The pattern's modern
documentation, principally Richardson's catalog and the corresponding chapter
structure in his book, names the same old mechanism as a first class answer to
a problem that container orchestration made urgent.

## 2. Problem and context

A service instance's network address is not static. In a system built on
virtual machines that autoscale, or containers scheduled by an orchestrator,
the IP address and port of any given instance is assigned dynamically when the
instance starts and is released when it stops. An instance can be replaced by
the scheduler after a health check failure, after a rolling deployment, after
a node drains for maintenance, or after an autoscaler adds capacity. The set
of valid addresses for a logical service therefore changes continuously, and
any caller that wants to reach that service needs a way to find a currently
valid address rather than a way to remember one.

The concrete situation looks like this inside a real system. A checkout
service needs to call an inventory service to confirm stock. In a monolith
this would be a local method call with no addressing problem at all. In a
microservice architecture the inventory service runs as some number of
replicas, that number changes as load changes, and each replica's address is
assigned by the platform, not by a developer typing a hostname into a config
file. The checkout service cannot hardcode `inventory-service:8080` and expect
that to remain valid, because the specific process bound to that address today
may be gone in five minutes and a different process may now hold a different
address entirely.

Server-side discovery answers this by inserting an intermediary, described by
Richardson as a router that runs at a well known, fixed location
([Server-Side Service Discovery pattern, microservices.io](https://microservices.io/patterns/server-side-discovery.html),
verified 2026-08-03). The checkout service sends its request to that fixed
location. The router itself is responsible for knowing, at the moment the
request arrives, which inventory instances are currently live, and forwards
the request to one of them. The calling code's job shrinks to knowing one
stable address, the router's, and never needs to know the address of any
individual backend instance.

The context in which this is the right answer has three parts that recur
across the infrastructure that implements it.

- The infrastructure layer already terminates connections and can insert
  routing logic without touching application code, which is true of every
  reverse proxy, every load balancer, and every sidecar in a service mesh.
- The organization wants client code that is agnostic to the runtime, the
  language, and the network topology of the callee, because the routing
  decision, health checking, and retry behaviour live in one place instead of
  being reimplemented per client language.
- The team accepts an additional network hop, and an additional piece of
  infrastructure to operate, in exchange for removing discovery logic from
  every service's codebase.

Kubernetes is the dominant concrete instance of this context today. A
Kubernetes Service exists specifically because Pods are ephemeral and their IP
addresses are not stable enough to call directly. The Kubernetes documentation
frames the problem the pattern exists to solve almost verbatim. "if some set
of Pods... provides functionality to other Pods... inside your cluster, how do
the frontends find out and keep track of which IP address to connect to, so
that the frontend can use the backend part of the workload? Enter Services."
([Service, Kubernetes documentation](https://kubernetes.io/docs/concepts/services-networking/service/),
verified 2026-08-03).

## 3. Forces

Server-side discovery is a specific answer to a set of forces that pull
against each other. Naming which forces it favours, and which it sacrifices,
is the difference between describing the pattern honestly and describing it as
a free win.

**Coupling versus operability.** Pushing discovery into the router lowers
coupling between calling code and the discovery mechanism. A client written in
any language, against any registry backend, makes an ordinary HTTP or TCP call
to a fixed address and never links a discovery client library. The cost lands
on operability instead. the router itself becomes a piece of infrastructure
that must be deployed, scaled, monitored, and kept in sync with the registry,
and every request now depends on that infrastructure being healthy.
Client-side discovery trades this the other way, embedding the coupling into
every service's code in exchange for removing the shared infrastructure
dependency.

**Latency versus centralization.** Routing through an intermediary adds one
network hop compared to a client that resolves an address and connects
directly. Richardson's own write-up names this cost plainly, that server-side
discovery introduces an additional network hop compared to client-side
discovery ([Server-Side Service Discovery pattern, microservices.io](https://microservices.io/patterns/server-side-discovery.html),
verified 2026-08-03). What is bought with that hop is a single place to apply
cross-cutting policy, rate limiting, mutual TLS termination, consistent health
checking, and observability, without touching the calling application at all.
For most internal, same-datacenter traffic the added hop is single digit
milliseconds and the centralization is worth more than the latency it costs.
For latency-critical hot paths inside a single process boundary, the calculus
can flip.

**Protocol generality versus simplicity.** A router that sits in front of many
different backend services generally needs to understand, or at least pass
through cleanly, whatever protocols those services speak. HTTP is easy.
gRPC, raw TCP, and stateful protocols with connection affinity are harder, and
each one the router must support is a piece of complexity the router carries
on behalf of every client rather than each client carrying it individually.
A single-language, single-protocol shop can sometimes get away with a much
simpler client-side library instead and never pay this router-side complexity
tax.

**Consistency versus staleness.** The router's view of live instances is only
as fresh as its last sync with the registry or its last health check cycle.
Kubernetes' own kube-proxy documentation explains that DNS-based approaches
are avoided for exactly this reason, application code and DNS resolvers often
cache results and ignore TTLs, which is why kube-proxy instead maintains
active packet-forwarding rules synchronized by a control loop against live
endpoint state
([Virtual IPs and Service Proxies, Kubernetes documentation](https://kubernetes.io/docs/reference/networking/virtual-ips/),
verified 2026-08-03). A router with a fast, actively synchronized view of
instance health is strictly better than a client relying on a cached DNS
answer, but the freshness of that view is an engineering property the router
implementation has to earn, not something the pattern gives for free.

**Cost and team topology.** A managed router, an AWS Application Load
Balancer or a cloud provider's managed Kubernetes Service networking, shifts
operational cost from the application team to the platform team, or to the
cloud bill. A self-hosted router, an NGINX or HAProxy fleet fronted by
Consul, shifts the operability burden onto whichever team owns that fleet.
Neither choice removes the operability cost, both choices relocate it, and
which relocation is cheaper depends entirely on team topology and existing
platform investment.

## 4. Applicability and non-applicability

### When to reach for it

- The runtime already provides a router as a first class primitive, most
  commonly a container orchestrator's Service abstraction, a cloud load
  balancer, or a service mesh sidecar, so adopting the pattern costs
  configuration rather than new infrastructure.
- Client code must remain agnostic to language, runtime, and discovery
  backend, because callers are written by many independent teams, or because
  polyglot services are a deliberate architectural choice.
- Cross-cutting network policy, mutual TLS, rate limiting, retries, circuit
  breaking, needs to be enforced consistently regardless of which language or
  team wrote the calling code, and centralizing that enforcement in the
  router is cheaper than reimplementing it per client library.
- The organization already operates, or can operate, the router
  infrastructure reliably, meaning a platform or SRE function exists that
  treats the router as a first class production system with its own SLOs.
- Traffic crosses a trust boundary, public internet to internal cluster, one
  team's services to another team's, where terminating and inspecting traffic
  at a single point is a security requirement independent of discovery.

### When not to reach for it, and why

- **A single-language monolith-adjacent deployment with few, stable
  services.** If the service topology rarely changes and every caller is
  written in the same language, the operational cost of standing up and
  running a router is not repaid. A static configuration file, or even a
  hardcoded internal DNS name that changes rarely, is cheaper.
- **Extreme low-latency, same-rack, hot-path calls.** When every microsecond
  of added hop latency is measured and matters, for example in trading
  systems or in-memory data grid lookups, the router hop is a real cost that
  client-side discovery avoids by resolving and connecting directly.
- **A team with no platform function to own router infrastructure.** A small
  team without dedicated infrastructure ownership can find itself debugging a
  load balancer's health check semantics under production pressure instead
  of shipping features. Client-side discovery libraries, or simply skipping
  discovery via a managed platform, is often the pragmatic choice until the
  team grows.
- **Protocols the router cannot cleanly proxy.** Long-lived, stateful,
  binary protocols that assume a persistent connection to a specific
  instance, certain database wire protocols, some streaming protocols, can be
  awkward or impossible to route transparently through a generic HTTP or TCP
  load balancer without specialized support. Forcing such traffic through a
  router built for stateless HTTP is a common source of subtle correctness
  bugs, particularly around connection affinity and in-flight request
  draining.
- **When the registry consistency model does not match the router's
  assumptions.** A router that polls a registry infrequently, or that relies
  on DNS caching upstream of itself, can serve stale routing decisions during
  a fast scale-down event, sending traffic to instances that have already
  terminated. If the platform cannot guarantee a synchronization loop tight
  enough for the deployment's churn rate, server-side discovery inherits the
  registry's staleness problem rather than solving it.

## 5. Structure

Four participants recur across every real implementation of this pattern,
whether the router is a cloud load balancer, an in-cluster proxy, or a
service mesh data plane.

- **Client.** The calling service or process. Sends every request to one
  fixed, well known address, the router's address, and never resolves a
  backend instance address itself. Carries no discovery logic and no
  registry client.
- **Router.** The pattern's namesake participant. Runs at a fixed, well known
  network location. Consults the service registry, either by polling it
  directly or by receiving pushed updates, to build and continuously refresh
  a table of currently live backend instances for each logical service name.
  Applies a load balancing algorithm, round robin, least connections, or a
  weighted variant, to select one instance per incoming request, and forwards
  the request to it. Often also performs health checking of backend instances
  independently of, or in addition to, whatever the registry reports.
- **Service Registry.** The database of currently available service
  instances. Populated either by instances registering and deregistering
  themselves as they start and stop, self-registration, or by an external
  registrar that watches the platform, an orchestrator's control plane, for
  example, and updates the registry on the platform's behalf,
  third-party registration. The registry is a distinct pattern in its own
  right and is the dependency this pattern always sits on top of.
- **Service Instance.** A single running process that implements the logical
  service. Registers, or is registered, with the registry once it can begin
  accepting traffic, and deregisters, or is deregistered, when it stops,
  whether through a graceful shutdown hook or through the platform detecting
  the process is gone.

## 6. ASCII structure diagram

```
                        +-----------------------+
                        |   Service Registry     |
                        |  (instances + health)  |
                        +-----------+-------------+
                                    ^  poll or push
                                    |  registration
                +-------------------+-------------------+
                |                                        |
                v                                        v
        +---------------+                       +----------------+
        |    Router      |                       | Service        |
        | (well known    |---- health check ---> | Instance A     |
        |  fixed address)|                       +----------------+
        |  load balancer |
        |  logic         |---- forwards request->+----------------+
        +-------^--------+                       | Service        |
                |                                 | Instance B     |
                | request to fixed address        +----------------+
                |
        +-------+--------+
        |     Client      |
        | (no discovery   |
        |  logic inside)  |
        +-----------------+
```

## 7. Dynamics

The pattern has two independent flows running concurrently. registration and
health synchronization on one axis, and per-request routing on the other. The
routing flow only works correctly because the registration flow keeps the
router's view of live instances current.

```
Registration and sync flow (continuous, background)
-----------------------------------------------------
Service Instance          Service Registry          Router
      |                          |                     |
      | starts, becomes able     |                     |
      | to accept traffic        |                     |
      |------------------------->|                     |
      |     register(self)       |                     |
      |                          |                     |
      |                          |<-- poll or watch ----|
      |                          |    for changes       |
      |                          |---- current set ---->|
      |                          |                     |
      | health probe fails or    |                     |
      | instance stops           |                     |
      |------------------------->|                     |
      |     deregister(self)     |                     |
      |                          |---- updated set ---->|
      |                          |                     |

Per-request routing flow
-----------------------------------------------------
Client               Router                 Instance
  |                     |                       |
  | request -> fixed    |                       |
  | router address      |                       |
  |-------------------->|                       |
  |                     | consult local table   |
  |                     | of live instances,     |
  |                     | apply LB algorithm     |
  |                     |----------------------->|
  |                     |   forward request      |
  |                     |                        |
  |                     |<---------------------- |
  |                     |     response            |
  |<---------------------|                       |
  |     response          |                       |
```

The critical detail the second diagram makes explicit is that the client's
view of the world never changes between requests, it always talks to the
router's fixed address, while the router's internal table of live instances
changes constantly and is what actually adapts to instance churn. This is the
structural point of the pattern. all of the volatility is absorbed on the
server side of the boundary, none of it leaks into the client.

## 8. Implementation variants

- **Hardware or managed cloud load balancer as router.** An AWS Application
  Load Balancer with target groups is the canonical managed implementation.
  Targets are registered with a target group, either manually, or
  automatically when attached to an Auto Scaling group, and the load
  balancer continually health checks registered targets, routing only to
  those it currently considers healthy
  ([Target groups for your Application Load Balancers, AWS documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html),
  verified 2026-08-03). This variant requires no code in the calling service
  beyond an ordinary HTTP client, and the registry role is effectively fused
  into the load balancer's own target group state, there is no separate
  registry component the team must operate.
- **In-cluster virtual IP proxy, the Kubernetes Service model.** Every node
  in a Kubernetes cluster runs kube-proxy, which is responsible for
  implementing a virtual IP mechanism for Services, capturing traffic sent to
  a Service's stable ClusterIP and redirecting it to one of the Service's
  current endpoints
  ([Virtual IPs and Service Proxies, Kubernetes documentation](https://kubernetes.io/docs/reference/networking/virtual-ips/),
  verified 2026-08-03). Two proxy implementations exist for how the
  redirection is done. iptables mode installs kernel netfilter rules per
  endpoint that select a backend Pod at random by default, while IPVS mode
  uses the kernel's IP Virtual Server subsystem with a hash table as its
  underlying data structure, which scales better for clusters with very many
  Services
  ([Virtual IPs and Service Proxies, Kubernetes documentation](https://kubernetes.io/docs/reference/networking/virtual-ips/),
  verified 2026-08-03). This variant is distinctive because the router is
  not a single centralized process. it is replicated onto every node, and
  the routing decision happens in the kernel of whichever node originated
  the traffic rather than in a dedicated appliance.
- **Reverse proxy driven by an external registry, template-generated
  configuration.** A reverse proxy such as NGINX or HAProxy is paired with a
  service registry, HashiCorp Consul is the most common pairing, and a
  templating tool renders the proxy's backend list from the registry's
  current state whenever it changes, then reloads the proxy. This variant
  decouples the choice of registry from the choice of proxy technology, at
  the cost of a reload-driven update cycle that is slower to react to churn
  than a proxy with native registry integration.
  Consul itself documents this proxy-fronted approach as one deployment
  shape, alongside its newer service mesh mode.
- **Service mesh sidecar proxy.** Every service instance runs alongside a
  dedicated proxy process, most commonly Envoy, deployed as a sidecar
  container in the same Pod or process group. The sidecar intercepts all
  inbound and outbound traffic for its instance, consults a control plane
  for the current set of live endpoints of whatever service is being called,
  and performs load balancing, retries, and often mutual TLS, transparently
  to the application. HashiCorp's own Consul Connect documentation describes
  this shape directly, that Consul can deploy Envoy sidecar proxies to
  control traffic between each service and the rest of the network, with a
  built-in certificate authority enforcing mutual TLS encryption between
  those proxies
  ([Consul Connect, HashiCorp documentation](https://developer.hashicorp.com/consul/docs/connect),
  verified 2026-08-03). This variant is structurally the same pattern as the
  centralized router variant, the discovery and routing decision still lives
  outside the calling application's own code, but it fans the single router
  out into one instance per service rather than one instance shared by
  everyone, trading a shared bottleneck for a per-instance operational
  footprint.
- **API gateway as router.** An API gateway sitting at the system's edge
  performs server-side discovery for external, north-south traffic in
  exactly the shape this pattern describes, and is frequently the first
  place teams encounter the pattern before extending it to internal,
  east-west traffic. See the related API Gateway pattern in this catalog for
  the aggregation and edge-concern responsibilities layered on top of pure
  discovery in that variant.

## 9. Known production uses

- **Amazon Web Services, Elastic Load Balancing, Application Load Balancer.**
  Registered targets, EC2 instances, IP addresses, Lambda functions, or ECS
  tasks, are grouped into target groups, and the load balancer continually
  monitors target health and routes only to targets it currently considers
  healthy, distributing traffic across Availability Zones according to a
  configurable algorithm
  ([Target groups for your Application Load Balancers, AWS documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html),
  verified 2026-08-03).
- **Kubernetes, Services and kube-proxy.** Every production Kubernetes
  cluster ships kube-proxy by default, running on every node and
  implementing the ClusterIP virtual IP mechanism that lets any Pod address
  a Service by a stable IP while the underlying set of backend Pods changes
  continuously as the scheduler reschedules them
  ([Virtual IPs and Service Proxies, Kubernetes documentation](https://kubernetes.io/docs/reference/networking/virtual-ips/),
  verified 2026-08-03). This makes it, by installed base, one of the most
  widely deployed implementations of server-side discovery in existence,
  since it ships as a default component of the platform rather than an
  opt-in add-on.
- **HashiCorp Consul, service mesh mode with Envoy sidecars.** Consul
  Connect deploys Envoy sidecar proxies alongside application instances
  across virtual machines, Kubernetes, Amazon ECS, AWS Lambda, and HashiCorp
  Nomad, and routes and secures service-to-service traffic through those
  proxies rather than requiring each service's own code to discover peers
  ([Consul Connect, HashiCorp documentation](https://developer.hashicorp.com/consul/docs/connect),
  verified 2026-08-03).
- **Marathon, on Apache Mesos clusters.** Richardson's own catalog names
  Marathon, the Mesos framework for long-running services, as running a
  proxy on each cluster host that forwards requests for a service to an
  available instance, the same server-side pattern shape as Kubernetes,
  predating Kubernetes' dominance in many production Mesos deployments
  ([Server-Side Service Discovery pattern, microservices.io](https://microservices.io/patterns/server-side-discovery.html),
  verified 2026-08-03).

## 10. Consequences

### Positive

- Calling code stays free of discovery logic and free of a registry client
  library, which means the same client code, or even the same generic HTTP
  client, works unchanged regardless of what language or platform the callee
  is written in.
- Cross-cutting concerns, health checking, load balancing algorithm choice,
  mutual TLS, rate limiting, are implemented once in the router rather than
  once per client language, which removes an entire class of drift where
  different teams implement discovery slightly differently.
- The router's view of instance health can be actively and continuously
  verified through its own health checks, independent of whatever the
  instance itself claims, catching failures that a purely registry-driven
  client-side approach would miss until the registry entry expires.
- Managed implementations, a cloud load balancer or a managed Kubernetes
  Service, let a team adopt the pattern with zero custom infrastructure to
  build, only configuration to write.
- Security policy enforcement, terminating TLS, enforcing mutual TLS between
  services, and inspecting or filtering traffic, has one natural chokepoint
  to attach to, rather than needing to be woven into every service's
  outbound call path individually.

### Negative

- Adds one network hop per call compared to a client that resolves and
  connects directly, a cost the pattern's own primary source names
  explicitly
  ([Server-Side Service Discovery pattern, microservices.io](https://microservices.io/patterns/server-side-discovery.html),
  verified 2026-08-03).
- Introduces a new piece of infrastructure, the router, that must itself be
  deployed, scaled, monitored, and treated as a production dependency with
  its own failure modes. an outage in the router is now an outage for every
  service that depends on it, a blast radius that pure client-side discovery
  does not create.
- The router must understand, or transparently pass through, whatever
  protocol the backend services speak, which is straightforward for HTTP and
  can require specialized support for gRPC, raw binary protocols, or
  stateful connections.
- Correctness now depends on the freshness of the router's synchronization
  with the registry or with the platform's control plane, and a slow or
  lagging synchronization loop reintroduces the exact staleness problem the
  pattern is meant to solve.
- In the sidecar and service mesh variant, the single shared bottleneck of a
  centralized router is traded for an operational footprint multiplied by
  the number of service instances, one sidecar per instance, which is a real
  resource and complexity cost even though it removes the single point of
  failure.

## 11. Failure modes and misuse

- **Symptom.** A rolling deployment causes a burst of failed requests,
  connection refused or connection reset, for several seconds during every
  release, even though the new instances passed their readiness checks.
  **Cause.** The router's health check or endpoint synchronization interval
  is slower than the platform's Pod or instance termination cycle, so the
  router keeps sending traffic to an instance for a window after the
  platform has already begun terminating it, or removes traffic from a new
  instance for a window before it has actually finished starting.
  **Fix.** Tighten the synchronization or health check interval to match the
  platform's termination timeline, and use a graceful shutdown sequence on
  the instance side that continues accepting in-flight connections during a
  drain period after it stops advertising itself as available, so the
  router has time to observe the change before the instance actually stops
  responding.

- **Symptom.** The router itself becomes the top entry in an incident
  postmortem, a single load balancer or a small router tier saturates and
  every downstream service reports higher latency or timeouts
  simultaneously, even though none of the actual backend services are
  individually overloaded.
  **Cause.** The router was treated as invisible infrastructure rather than
  as a first class production dependency, and was never capacity planned,
  autoscaled, or given the same on-call attention as the services it fronts.
  **Fix.** Instrument the router with the same rigor as any other production
  service, connection counts, queue depth, CPU and memory headroom, and
  autoscale or horizontally shard it ahead of the traffic growth of the
  services behind it, per the observability guidance in dimension 16 below.

- **Symptom.** A specific client intermittently connects to a stale or
  already-terminated instance long after the instance stopped, even though
  every other client is fine.
  **Cause.** DNS-level server-side discovery, where a router publishes
  backend addresses as multiple A records rather than through active packet
  forwarding, is being bypassed by that one client's caching resolver or
  application-level DNS cache, which ignores the record's TTL. Kubernetes'
  own documentation names exactly this failure mode as the reason kube-proxy
  uses active rule synchronization instead of relying on DNS round robin for
  its ClusterIP mechanism
  ([Virtual IPs and Service Proxies, Kubernetes documentation](https://kubernetes.io/docs/reference/networking/virtual-ips/),
  verified 2026-08-03).
  **Fix.** Prefer a router implementation that actively forwards packets or
  proxies connections rather than one that relies solely on DNS answers with
  a TTL, or, if DNS-based routing must be used, aggressively audit and fix
  any client-side or intermediate resolver caching that ignores TTLs.

- **Symptom.** During a partial zone or region outage, the system's overall
  failure rate spikes far higher than the fraction of actually broken
  instances would predict.
  **Cause.** The router's health threshold logic marks an entire zone or
  target group as unhealthy too aggressively, or too leniently, for the
  actual blast radius of the failure, either failing over traffic away from
  a zone that still has meaningful healthy capacity, or continuing to send
  traffic to a zone that has dropped below a survivable healthy percentage.
  AWS's own documentation describes exactly this tunable, DNS failover and
  routing failover thresholds that must be set deliberately per target group
  rather than left at defaults that do not match the deployment's actual
  redundancy
  ([Target groups for your Application Load Balancers, AWS documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html),
  verified 2026-08-03).
  **Fix.** Model the actual redundancy the deployment provides, how many
  healthy targets per zone are needed to serve real load, and set the
  router's health thresholds and failover behaviour to match that model
  explicitly, rather than accepting default thresholds tuned for a generic
  workload.

- **Misuse.** Treating server-side discovery as a substitute for client-side
  resilience patterns entirely, assuming that because the router health
  checks backends, the calling code never needs its own timeout or retry
  budget.
  **Symptom.** A single slow backend instance, one that responds but very
  slowly rather than failing outright, is not caught by the router's binary
  health check, and calling code that has no timeout of its own hangs
  indefinitely waiting on that one slow instance, even though the router
  correctly considers it healthy.
  **Fix.** Pair server-side discovery with client-side timeout and circuit
  breaker discipline regardless of how good the router's health checking is,
  because a router's health check answers only "is this instance
  reachable", not "is this instance responding fast enough for this
  particular call". See the related Circuit Breaker pattern.

## 12. Trade-off matrix

| Force | Server-Side Service Discovery | Client-Side Service Discovery | DNS Round Robin (naive) |
|---|---|---|---|
| Client code complexity | Minimal, ordinary network client only | Requires a discovery-aware client library per language | Minimal, ordinary DNS resolution |
| Added latency per call | One extra hop through the router | None, client connects directly | None, but resolution itself can be stale |
| Cross-cutting policy enforcement | Centralized in the router, applies uniformly | Must be reimplemented per client library and per language | Effectively none, no logic beyond address selection |
| New infrastructure to operate | Yes, the router is a new production dependency | No new shared infrastructure, but every client links a registry client | Minimal, but DNS TTL and caching behaviour becomes load-bearing |
| Failure blast radius | Router outage affects every dependent client at once | A single client library bug affects only that client | A stale or slow DNS update affects every client relying on that record |
| Freshness of routing decisions | As fresh as the router's sync loop with the registry | As fresh as each client's own poll interval | Bound by DNS TTL and by resolver and OS level caching, often stale |
| Protocol flexibility | Constrained by what the router can proxy or forward | Unconstrained, client connects with whatever protocol it likes | Works for anything that resolves a hostname, but load balancing granularity is coarse |
| Best fit | Polyglot systems, container platforms, service meshes | Homogeneous, single-language systems wanting to avoid a router hop | Very simple, low-churn deployments only |

## 13. Related and incompatible patterns

- **Client-Side Service Discovery.** The direct alternative, resolution
  moved into the calling process instead of a router. The two patterns are
  never combined for the same call, a given request is either resolved by
  the client or by a router, though a large system commonly uses server-side
  discovery for external, edge traffic and client-side discovery for
  latency-sensitive internal calls, or vice versa.
- **Service Registry.** A hard dependency, not an option. Server-side
  discovery has nothing to route by without a registry, or an equivalent
  source of truth about live instances, such as an orchestrator's own
  control plane state standing in for a dedicated registry.
- **API Gateway.** A specialization of server-side discovery for
  north-south, external-to-internal traffic, which typically layers request
  aggregation, protocol translation, and authentication on top of the pure
  routing responsibility this pattern describes. See the related entry in
  this catalog.
- **Circuit Breaker.** Composes with server-side discovery rather than
  replacing any part of it. The router's health checking catches instances
  that are entirely unreachable, while a circuit breaker in the calling code
  protects against instances that respond but are unacceptably slow or
  erroring, a distinction covered in dimension 11 above.
- **Remote Procedure Invocation.** The mechanism the router forwards traffic
  for, once an instance has been selected. Server-side discovery answers
  which instance to call, not how the call itself is shaped.
- **Self-Contained Service.** Independent, but complementary in deployment
  practice. a self-contained service that owns its own runtime dependencies
  is easier to schedule dynamically across a cluster, which is precisely the
  condition that makes server-side discovery necessary in the first place.
- **Incompatible with.** No named pattern in this catalog is structurally
  incompatible with server-side discovery. Its natural tension is with
  Client-Side Service Discovery at the level of a single call path, as
  described above, not an incompatibility in the same system.

## 14. Refactoring path in and out

### Introducing the pattern into a system that lacks it

1. Identify every place calling code currently hardcodes, or manually
   configures, a specific backend address or a small fixed list of
   addresses for a service that actually runs as a dynamic set of
   instances.
2. Stand up, or adopt an existing, service registry, or confirm the
   orchestration platform already provides one implicitly, a Kubernetes
   cluster's own API server and endpoint controller already fill this role.
3. Introduce a router in front of the target service, starting with the
   simplest available option for the platform, a managed cloud load
   balancer if running on a cloud provider, or the orchestrator's native
   Service abstraction if running on Kubernetes, rather than building a
   custom router first.
4. Point the router at the service's current instances, either through
   self-registration on instance startup or through the platform
   automatically registering instances, and verify health checking is
   correctly wired before removing any old, hardcoded address.
5. Change calling code to address the router's fixed, well known location
   instead of any specific backend instance, and remove the hardcoded
   address list entirely once traffic is confirmed flowing correctly
   through the router.
6. Add or verify client-side timeout and retry discipline, per the failure
   mode noted in dimension 11, since the router does not remove the need
   for it.

### Removing the pattern from a system that no longer needs it

1. Confirm the underlying condition that motivated the pattern no longer
   holds, the service topology has become stable and low-churn, or the
   number of instances has shrunk to a small, manually manageable set.
2. Measure the router's added latency and operational cost against the
   simplicity gained by removing it, rather than removing it purely on
   aesthetic grounds. removing working infrastructure without a measured
   reason is itself a risk.
3. If removal is warranted, replace the router address in calling code with
   a stable, manually maintained address or a small, explicit list, and
   decommission the router and its registry integration only after
   confirming traffic has fully cut over.
4. Reintroduce whatever cross-cutting policy the router used to enforce,
   health checking, TLS, rate limiting, directly at the target if it is
   still needed, since removing the router removes wherever that policy
   used to live.

## 15. Testing and verification

Server-side discovery moves discovery logic out of the calling code and into
infrastructure, which changes what is easy and what is hard to test.

What becomes easy. Testing the calling service's own business logic no
longer requires mocking a discovery client or a registry, because the
calling code has none, it makes an ordinary network call to a fixed test
address. Unit tests for the calling service can point at a local test
double, an in-memory HTTP server or a container running the real backend, at
that fixed address without any discovery machinery involved at all.

What becomes harder. Verifying that the router itself correctly reacts to
instance churn, an instance becoming unhealthy, a new instance starting, a
rolling deployment, cannot be tested inside the calling service's own test
suite, because that behaviour now lives entirely in infrastructure the
calling service does not control. This pushes discovery-specific testing
into a separate layer.

- **Integration tests against a real router configuration.** Stand up the
  actual router, or the closest local equivalent, an NGINX container
  fronting two backend containers, or a local Kubernetes cluster with a real
  Service and two Pod replicas, and assert that traffic is correctly
  distributed and that killing one backend instance causes the router to
  stop sending it traffic within an acceptable window.
- **Fault-injection and churn tests.** Deliberately terminate and start
  instances rapidly against a staging environment's router and measure the
  error rate and latency spike during the churn window, to catch the
  synchronization lag failure mode described in dimension 11 before it
  appears in production.
- **Health check contract tests.** Test the instance's own health check
  endpoint in isolation, confirming it correctly reports unhealthy under the
  conditions that should trigger it, since the router's correctness is
  entirely dependent on the accuracy of the signal the instance provides.
- **Load balancing distribution tests.** Send a known volume of requests
  through the router against a known number of healthy instances and assert
  the distribution matches the configured algorithm's expected shape, round
  robin should be close to uniform, least connections should favour an
  artificially slow instance less.

## 16. Observability signals

A healthy server-side discovery deployment shows a small, stable set of
signals. request latency at the router is close to the sum of network
overhead plus backend processing time, with no long tail attributable to the
router itself. the count of healthy targets or endpoints behind the router
tracks the actual number of running instances with only brief, expected dips
during deploys. and the router's own resource utilization, CPU, memory,
connection count, sits well within its provisioned capacity with headroom
for traffic spikes.

- **Healthy versus total target count.** The single most direct signal for
  whether the router's view of the world matches reality. A persistent gap
  between the number of instances the platform reports as running and the
  number the router considers healthy is the first place to look when
  investigating routing anomalies.
- **Router-attributed latency, separated from backend latency.** Measuring
  time spent in the router distinctly from time spent in the backend
  instance matters directly when diagnosing whether a latency regression is a
  routing problem or a backend problem, and most managed load balancers,
  the AWS documentation's CloudWatch metrics reference is one example, expose
  this separation natively
  ([Target groups for your Application Load Balancers, AWS documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html),
  verified 2026-08-03).
- **Registry synchronization lag.** For implementations where the router
  polls or watches an external registry rather than being fused with the
  platform's own control plane, the time between an instance's registration
  or deregistration and the router reflecting that change is a direct
  measure of the staleness window described in dimension 11.
  Kube-proxy's own synchronization period settings, `minSyncPeriod` and
  `syncPeriod`, are the concrete tunable for this signal on Kubernetes
  ([Virtual IPs and Service Proxies, Kubernetes documentation](https://kubernetes.io/docs/reference/networking/virtual-ips/),
  verified 2026-08-03).
- **Router error rate by cause.** Distinguishing connection refused, or no
  healthy backend available, errors from backend-originated error responses
  matters, because the two indicate entirely different problems, a
  discovery or health-checking failure versus an actual application bug in
  the backend.
- **Per-zone or per-shard health distribution.** In multi-zone deployments,
  aggregate health metrics can hide a single zone silently degrading while
  overall numbers look fine, which is exactly the condition the per-zone
  failover thresholds in dimension 11 exist to catch, and which needs its
  own dashboard rather than being buried in a global average.

## 17. Security and privacy implications

Server-side discovery concentrates a meaningful amount of network authority
into the router, which changes the system's attack surface in specific,
identifiable ways rather than in a vague, general sense.

The router becomes a natural, and valuable, single chokepoint for enforcing
transport security uniformly. HashiCorp's own documentation of Consul
Connect's sidecar proxy model describes exactly this benefit, a built-in
certificate authority enforcing mutual TLS encryption between every sidecar
proxy pair, giving the platform uniform encryption in transit without
requiring every application to implement TLS correctly itself
([Consul Connect, HashiCorp documentation](https://developer.hashicorp.com/consul/docs/connect),
verified 2026-08-03). This is a genuine security improvement over a system
where every service independently implements, or fails to implement,
transport security.

That same concentration is also a concentration of risk. A router that
terminates TLS on behalf of every backend it fronts becomes a single point
where a compromise, a misconfiguration, or a software vulnerability in the
router itself exposes decrypted traffic for every service behind it, rather
than the blast radius being limited to a single compromised service. The
router's own software supply chain, and the credentials it holds to
authenticate itself to the registry and to backend instances, deserve the
same security scrutiny as any other high-value, high-blast-radius production
component, arguably more, precisely because so much traffic flows through
it.

Health check and registration traffic between instances and the registry, or
between the router and the registry, is itself a channel that needs
protecting. An attacker who can inject a false registration, claiming to be
a healthy instance of a legitimate service, or who can inject a false
deregistration, removing a legitimate instance from rotation, can redirect
traffic or cause a denial of service without ever touching application code
directly. Registries and the registration channel should require
authentication commensurate with the trust being granted, since the registry
is effectively deciding where production traffic goes.

Finally, the router's exposure to the public internet, in the API gateway
and edge load balancer variants of this pattern, means it inherits every
concern that applies to any internet-facing service, request validation,
protection against volumetric and application-layer denial of service, and
careful handling of any data logged or cached at the routing layer, since
request paths and headers passing through the router can themselves carry
sensitive information even when the router never inspects the request body.

## 18. References

1. Chris Richardson. "Pattern. Server-side service discovery." microservices.io.
   https://microservices.io/patterns/server-side-discovery.html
   Verified 2026-08-03.
2. "Service." Kubernetes documentation, Services, Load Balancing, and
   Networking.
   https://kubernetes.io/docs/concepts/services-networking/service/
   Verified 2026-08-03.
3. "Virtual IPs and Service Proxies." Kubernetes documentation, Reference,
   Networking.
   https://kubernetes.io/docs/reference/networking/virtual-ips/
   Verified 2026-08-03.
4. "Target groups for your Application Load Balancers." Amazon Web Services,
   Elastic Load Balancing documentation.
   https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html
   Verified 2026-08-03.
5. "Connect (service mesh)." HashiCorp Consul documentation.
   https://developer.hashicorp.com/consul/docs/connect
   Verified 2026-08-03. Note, this URL is a 308 permanent redirect target
   from the legacy `www.consul.io/docs/connect` path, both resolve to the
   same current documentation.

## Code examples

### TypeScript

A client that never resolves a backend address, it only ever talks to the
fixed router address, with the timeout discipline dimension 11 calls out as
still necessary even when the router health-checks backends.

```typescript
// server_discovery_client.ts
// Compiled with: npx tsc --strict --target es2020 --module commonjs server_discovery_client.ts

interface RouterClientOptions {
  routerBaseUrl: string;
  timeoutMs: number;
}

class RouterOnlyServiceClient {
  private readonly routerBaseUrl: string;
  private readonly timeoutMs: number;

  constructor(options: RouterClientOptions) {
    this.routerBaseUrl = options.routerBaseUrl;
    this.timeoutMs = options.timeoutMs;
  }

  async callService(path: string): Promise<{ status: number; body: string }> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);
    try {
      const response = await fetch(this.routerBaseUrl + path, {
        signal: controller.signal,
      });
      const body = await response.text();
      return { status: response.status, body };
    } finally {
      clearTimeout(timer);
    }
  }
}

function assertEqual(actual: unknown, expected: unknown, label: string): void {
  if (actual !== expected) {
    throw new Error(`${label}: expected ${expected}, got ${actual}`);
  }
}

// The client never knows about individual backend instances, only the
// router's fixed address, which is the structural point of the pattern.
const client = new RouterOnlyServiceClient({
  routerBaseUrl: "http://inventory-router.internal:8080",
  timeoutMs: 500,
});

assertEqual(typeof client.callService, "function", "callService is a method");
console.log("RouterOnlyServiceClient constructed and type-checked cleanly.");
```

### Go

A minimal router that mirrors the structural role in dimension 5 and 7. it
holds a table of live instances, refreshes it on a timer to simulate
registry synchronization, and load balances across whatever is currently
marked healthy.

```go
// router.go
// Run with: go run router.go

package main

import (
	"fmt"
	"sync"
)

// Instance mirrors dimension 5's "Service Instance" participant.
type Instance struct {
	Address string
	Healthy bool
}

// Router mirrors dimension 5's "Router" participant. It holds a
// continuously refreshed table of live instances, exactly as described
// in the registration and sync flow in dimension 7.
type Router struct {
	mu        sync.Mutex
	instances []Instance
	next      int
}

func NewRouter() *Router {
	return &Router{}
}

// Sync replaces the router's view of live instances, standing in for a
// poll of the Service Registry participant.
func (r *Router) Sync(instances []Instance) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.instances = instances
}

// Route selects the next healthy instance using round robin, the
// simplest of the load balancing algorithms named in dimension 5.
func (r *Router) Route() (Instance, error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	healthy := make([]Instance, 0, len(r.instances))
	for _, inst := range r.instances {
		if inst.Healthy {
			healthy = append(healthy, inst)
		}
	}
	if len(healthy) == 0 {
		return Instance{}, fmt.Errorf("no healthy instance available")
	}
	chosen := healthy[r.next%len(healthy)]
	r.next++
	return chosen, nil
}

func main() {
	router := NewRouter()

	// Simulates the registry reporting three instances, one unhealthy,
	// exactly the shape dimension 11's health check symptom describes.
	router.Sync([]Instance{
		{Address: "10.0.0.1:9000", Healthy: true},
		{Address: "10.0.0.2:9000", Healthy: false},
		{Address: "10.0.0.3:9000", Healthy: true},
	})

	selections := map[string]int{}
	for i := 0; i < 6; i++ {
		inst, err := router.Route()
		if err != nil {
			panic(err)
		}
		selections[inst.Address]++
	}

	fmt.Println("Round robin distribution across healthy instances:")
	for addr, count := range selections {
		fmt.Printf("  %s -> %d requests\n", addr, count)
	}

	if selections["10.0.0.2:9000"] != 0 {
		panic("router sent traffic to an unhealthy instance")
	}
	fmt.Println("Verified: unhealthy instance received zero requests.")
}
```

### Python

A small simulation exercising both flows from dimension 7 end to end, a
registry that instances register with and deregister from, and a router
that syncs against it, so the two concurrent flows the dynamics section
describes can be seen operating together.

```python
# discovery_sim.py
# Run with: python3 discovery_sim.py

from dataclasses import dataclass, field


@dataclass
class ServiceRegistry:
    """Dimension 5's Service Registry participant."""

    _entries: dict = field(default_factory=dict)

    def register(self, name: str, address: str) -> None:
        self._entries[address] = name

    def deregister(self, address: str) -> None:
        self._entries.pop(address, None)

    def instances_for(self, name: str) -> list:
        return [addr for addr, svc in self._entries.items() if svc == name]


@dataclass
class Router:
    """Dimension 5's Router participant. Syncs against the registry and
    load balances with round robin, matching the Go example's algorithm
    so both language examples demonstrate the identical structural idea."""

    registry: ServiceRegistry
    service_name: str
    _index: int = 0

    def route(self) -> str:
        live = self.registry.instances_for(self.service_name)
        if not live:
            raise RuntimeError("no live instance available")
        chosen = live[self._index % len(live)]
        self._index += 1
        return chosen


def main() -> None:
    registry = ServiceRegistry()
    router = Router(registry=registry, service_name="inventory")

    # Registration flow, dimension 7, first diagram: instances register
    # themselves as they start.
    registry.register("inventory", "10.0.1.1:9000")
    registry.register("inventory", "10.0.1.2:9000")

    # Per-request routing flow, dimension 7, second diagram: the client
    # only ever calls Router.route(), never touches the registry.
    seen = [router.route() for _ in range(4)]
    print("Requests routed to:", seen)
    assert seen[0] != seen[1] or len(set(seen)) == 1, "round robin sanity check"

    # A deployment event: one instance stops and deregisters, dimension 7's
    # second half of the registration flow.
    registry.deregister("10.0.1.1:9000")

    seen_after = [router.route() for _ in range(4)]
    print("After deregistration, routed to:", seen_after)
    assert all(addr == "10.0.1.2:9000" for addr in seen_after), (
        "router kept sending traffic to a deregistered instance, "
        "the exact staleness failure mode in dimension 11"
    )

    print("Verified: router correctly stopped routing to the deregistered instance.")


if __name__ == "__main__":
    main()
```

Java and Rust are not included. The pattern's core mechanism, holding a
synchronized table of live addresses and applying a load balancing
algorithm, is not language-idiomatic in a way that meaningfully changes
shape in either language versus the three shown, and the three examples
above already cover a typed client-only view, TypeScript, a router
implementation with its own tests, Go, and an end-to-end simulation of both
concurrent flows, Python, which together demonstrate every structural
element in dimensions 5 through 7.
