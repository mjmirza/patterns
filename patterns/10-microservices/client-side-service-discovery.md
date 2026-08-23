---
name: Client-side Service Discovery
slug: client-side-service-discovery
family: 10-microservices
category: Communication
aliases: [Client-side Discovery, Client-driven Load Balancing]
first_described: "Richardson 2018"
maturity: canonical
related: [server-side-discovery, api-gateway, self-registration, third-party-registration, circuit-breaker]
incompatible_with: []
verified: 2026-08-02
---

# Client-side Service Discovery

## 1. Name, aliases, and lineage

The canonical name is Client-side Service Discovery. Chris Richardson catalogs it
as one of the microservices patterns on his microservices.io reference site and in
his book *Microservices Patterns*, Manning, 2018, chapter 3, in the section on
service discovery. The pattern description states the problem as "how does the
client of a service, the API gateway, or another service, discover the location
of a service instance" and the solution as the client querying a service registry
directly, then choosing an instance and load balancing itself
([microservices.io, Client-side Service Discovery pattern](https://microservices.io/patterns/client-side-discovery.html),
verified 2026-08-02).

The name is descriptive rather than trademarked. Practitioners also call it
client-driven load balancing, because the mechanism that gives it its shape is
that the load-balancing decision is made inside the calling process rather than
by an intermediary. Netflix, whose OSS stack popularized the pattern at scale
before Richardson's catalog existed, referred to the combination of their
registry and their load-balancing client simply as service discovery and load
balancing, since the pattern name was coined after their implementation shipped.
The pair of components Netflix shipped, Eureka as the registry and Ribbon as the
client-side load balancer, is the historical reference implementation that later
informed the pattern's catalog entry.

The pattern sits inside a two-member family with Server-side Service Discovery.
Both patterns solve the same problem, locating a healthy instance of a logically
named service in an environment where instances start, stop, scale, and move
addresses continuously. They differ only in which participant performs the
lookup and the load-balancing decision. This entry is about the client-performs
variant.

## 2. Problem and context

A microservices architecture replaces a small number of long-lived, statically
addressed processes with many short-lived, dynamically addressed ones. A single
service, "order-service" for instance, might run behind three, thirty, or three
hundred instances depending on load, each on a network address assigned at
startup by a scheduler such as an EC2 Auto Scaling group, a Kubernetes
scheduler, or a container orchestrator. Instances also disappear on redeploy, on
autoscale-in, on crash, and on rolling upgrade. A caller that hardcodes an
address, or even a small fixed list of addresses, breaks the moment the
topology changes, which in a system under continuous deployment is constantly.

The concrete situation this pattern addresses is a service consumer, whether
that is another backend service, an API gateway, or a batch job, that needs to
issue a request to "the order service" without knowing, or caring, which of its
currently running instances will handle it, and without waiting for a human to
update a configuration file every time an instance starts or stops. The
consumer needs the mapping from logical service name to physical network
location resolved at the moment of the call, from a source of truth that stays
current as instances register and deregister.

Richardson frames this as the core difficulty of service discovery in a
microservices system, contrasting it with the traditional model where a small,
stable set of server addresses could be hardcoded into a configuration file or
a DNS entry that changed rarely
([microservices.io, Client-side Service Discovery pattern](https://microservices.io/patterns/client-side-discovery.html),
verified 2026-08-02). Cloud Native Computing Foundation and HashiCorp materials
describe the same underlying problem for their own registries. Consul's
documentation states that in systems that use client-side discovery, the
service consumer is responsible for determining the access information of
available service instances and load balancing requests between them
([HashiCorp, Consul service discovery concepts](https://developer.hashicorp.com/consul/docs/concepts/service-discovery),
verified 2026-08-02), naming the same responsibility split this entry describes.

The context in which client-side discovery specifically, rather than the
server-side variant, becomes the right answer is one where the calling process
already needs fine control over load balancing behavior, per-request retry and
circuit-breaking policy, or protocol-level routing decisions that a generic
load balancer or platform proxy cannot express, and where the operational cost
of running a client library and a registry is acceptable to the team that owns
the caller.

## 3. Forces

Latency favors client-side discovery once the client has cached the registry
response, because the request to the actual service instance travels directly,
with no intermediate hop through a load balancer or proxy process. The first
lookup against the registry costs a round trip, but that round trip is
amortized across every subsequent call while the cached instance list stays
valid, whereas a server-side discovery hop through a load balancer or a service
mesh sidecar costs an extra network hop on every single request. This is the
force the pattern most clearly wins on.

Coupling pulls the other way. Client-side discovery couples every calling
service to the registry's client library, its protocol, and often its language
ecosystem. A Java service using Netflix's Eureka client and a Python batch job
calling the same registry either both maintain a Eureka-compatible client or
the Python job is left out of the discovery mechanism entirely. Richardson
notes this directly as a drawback of the pattern, that a client-side service
discovery library is needed for each programming language, and possibly
framework, used by the service clients
([microservices.io, Client-side Service Discovery pattern](https://microservices.io/patterns/client-side-discovery.html),
verified 2026-08-02). Server-side discovery, by contrast, hides the registry
behind a platform-provided proxy that every language can call the same way, over
plain HTTP or TCP.

Operability trades off against control. Client-side discovery gives each calling
team direct control over retry policy, timeout, connection pooling, and
circuit-breaking, because that logic lives inside their own process next to the
discovery client, which is exactly what Netflix's Hystrix and Ribbon
integration was built to provide. Server-side discovery centralizes that
control in the load balancer or mesh, which is easier to operate uniformly
across many teams but harder for any single team to override for its own
service's traffic shape.

Consistency and staleness are a shared force but resolved differently. Both
variants depend on the registry reflecting reality quickly. A client-side
implementation typically caches the instance list locally with a refresh
interval, which means a newly failed instance can still receive traffic for up
to that interval unless health checking and client-side retries paper over it.
Cost and team topology matter too, since this pattern adds one more piece of
infrastructure, the registry, to build, secure, and keep highly available,
work that a platform team can absorb centrally but that raises the bar for a
small team building its first few services.

## 4. Applicability and non-applicability

Use client-side service discovery when the calling services are relatively few
in number, are built and operated by teams with the capacity to run and
maintain a discovery client library, when per-call load balancing latency
matters enough that an extra network hop through a proxy is unacceptable, and
when the organization already standardizes on one or two languages so that
maintaining a client library across the fleet is tractable. It also fits well
when the calling code already needs deep, language-native integration with
retry, circuit breaking, and request-level metrics, since a client-side
library is positioned to provide all of that from one integration point.

Do not use client-side service discovery in the following situations.

- When the calling services span many languages and frameworks, so that
  maintaining a discovery client per language becomes an ongoing tax the
  platform team has to pay for every consumer, including third-party or legacy
  callers that cannot embed a custom client at all.
- When the runtime platform already provides a stable virtual address per
  service, as Kubernetes Services do via ClusterIP and cluster DNS. Kubernetes'
  own documentation frames the Service abstraction as solving exactly the
  discovery problem server-side, explaining that frontend pods need a way to
  find and keep track of which backend pod address to connect to, and that a
  Service exists to solve that
  ([Kubernetes documentation, Service](https://kubernetes.io/docs/concepts/services-networking/service/),
  verified 2026-08-02). Reintroducing a client-side registry on top of that is
  usually redundant work, not additional safety.
- When external clients, browsers, mobile apps, or third-party integrators are
  the caller. An external client cannot reasonably embed a service registry
  client and should never be handed the internal instance topology; a gateway
  or edge load balancer belongs there instead, which is Server-side Service
  Discovery, not this pattern.
- When the team lacks the operational maturity to run a highly available
  registry. A registry that is down or partitioned takes every dependent
  client's discovery capability down with it unless the client caches
  aggressively, and an unmaintained registry becomes a single point of failure
  the organization did not intend to create.
- When strict, centrally enforced traffic policy, such as mutual TLS
  termination, uniform rate limiting, or a single audited point of egress, is a
  compliance requirement. Centralizing that logic in a server-side proxy or
  mesh sidecar is a better fit than distributing policy enforcement into every
  client library.

## 5. Structure

- **Service Instance.** A running process of a service that, on startup,
  registers its network location, host and port, with the service registry,
  either directly (Self-Registration) or through an agent acting on its behalf
  (Third-Party Registration). It deregisters, or is deregistered by a health
  check failure, on shutdown.
- **Service Registry.** A database of currently available service instances
  and their network locations, kept current through registration,
  deregistration, and periodic health checks or heartbeats. Examples include
  Netflix Eureka, HashiCorp Consul, and Apache ZooKeeper used as a registry.
- **Service Consumer (the client).** The calling process, another
  microservice, an API gateway, or a scheduled job, that wants to invoke a
  logically named service. It embeds a discovery client library.
- **Discovery Client Library.** The component embedded inside the consumer
  that queries the registry, caches the returned instance list, applies a load
  balancing algorithm to pick one instance per call, and typically layers
  retry and circuit-breaking logic on top. Netflix's reference pairing is the
  Ribbon library performing this role against a Eureka registry.
- **Load Balancing Algorithm.** The strategy the discovery client uses to
  choose among the cached instances for a given call, for example round robin,
  random selection, or a weighted strategy that favors instances with lower
  observed latency.

## 6. ASCII structure diagram

```
+----------------------------------+
| Service Consumer (Order Service) |
| -------------------------------  |
| Discovery Client Library         |
|  - cache                         |
|  - load balancer                 |
+----------------------------------+
           | (1) query instances
           v
+----------------------------------------------+
| Service Registry (Eureka, Consul, ZooKeeper) |
+----------------------------------------------+
           | (2) instance list, returned to Consumer
           ^
           |
           | register / deregister / heartbeat
     +-----+-----+
     |           |
+----------------------+  +----------------------+
| Service Instance A   |  | Service Instance B   |
| (Payment Svc)        |  | (Payment Svc)        |
+----------------------+  +----------------------+

(3) Consumer sends the direct request straight to the
chosen instance, A or B, using the cached list and its
own load balancer, no registry hop on the request path.
```

## 7. Dynamics

```
Startup / registration
-----------------------
Payment Service Instance A     Service Registry
       |                              |
       |--- register(host, port) ---->|
       |<-- ack -----------------------|
       |                              |
       |--- heartbeat (periodic) ----->|   keeps registration alive;
       |                              |    missed heartbeats expire it

Call path
---------
Order Service (consumer)   Discovery Client Lib   Service Registry   Payment Instance A
       |                          |                     |                     |
       |-- invoke("payment") ---->|                     |                     |
       |                          |-- cache miss? ------>|                    |
       |                          |<-- [A, B, C] ---------|                    |
       |                          |-- pick(A) via LB alg |                    |
       |                          |------------------- request ------------->|
       |                          |<------------------- response -------------|
       |<-- response --------------|                     |                    |

Shutdown / deregistration
--------------------------
Payment Service Instance A     Service Registry
       |                              |
       |--- deregister --------------->|
       |   (or, heartbeats stop,       |
       |    registry expires entry     |
       |    after TTL)                 |
```

The subsequent calls after the first cache-miss reuse the cached instance
list, bypassing the registry round trip entirely, until the cache's refresh
interval elapses or the discovery client is notified of a change where the
registry supports push or streaming updates rather than pure polling.

## 8. Implementation variants

**Polling cache with periodic refresh.** The discovery client fetches the full
instance list on a timer, typically every few seconds to a minute, and serves
lookups from the in-memory cache between refreshes. This is the shape Netflix
Ribbon used against Eureka. Simple to reason about, but a stale cache can
route to an instance that has already shut down until the next refresh or
until a circuit breaker on the consumer side trips.

**Watch or long-poll based cache invalidation.** The discovery client
subscribes to change notifications from the registry, either via a
long-polling HTTP endpoint or a streaming connection, so the cache is
invalidated close to the moment a registration changes rather than on a fixed
timer. Consul's blocking queries and its client agent's local caching follow
this shape, giving a much shorter staleness window than pure polling
([HashiCorp, Consul service discovery concepts](https://developer.hashicorp.com/consul/docs/concepts/service-discovery),
verified 2026-08-02).

**DNS-based client-side discovery.** The registry exposes SRV or A records
per service, and the client performs a DNS lookup and applies its own
selection logic across the returned records rather than calling a bespoke
HTTP API. Consul supports this mode alongside its HTTP API. This variant
trades a richer registry protocol for the universality of DNS resolution,
which almost every language and runtime already knows how to perform, at the
cost of DNS's typically coarser health and metadata model compared to a
purpose-built registry API.

**Language-native client library versus a pluggable in-process resolver.**
The classic variant embeds a language-specific SDK, Eureka's Java client or a
community Go client, directly in the calling process. A lighter variant used
by some gRPC-based systems implements the same client-side selection logic
inside a pluggable resolver and balancer inside the gRPC runtime itself, so
any gRPC service written in a supported language gets client-side discovery
by configuring a resolver rather than writing custom integration code.

**Static-then-dynamic hybrid.** Some implementations bootstrap from a small
static seed list of registry addresses, since the registry itself needs to be
discoverable too, then switch to fully dynamic instance discovery for the
services those registry addresses expose. This resolves the
who-discovers-the-discoverer bootstrapping problem without introducing a
second discovery mechanism.

## 9. Known production uses

**Netflix, Eureka and Ribbon.** Netflix built and open-sourced Eureka,
describing it in the project's own README as a RESTful service that is
primarily used in the AWS cloud for the purpose of discovery, load balancing
and failover of middle-tier servers
([Netflix, eureka GitHub repository](https://github.com/Netflix/eureka),
verified 2026-08-02), paired with the Ribbon client-side load balancer that
callers embedded to select among the instances Eureka returned. This pairing
is the historical origin of the pattern as it is catalogued today and ran
Netflix's internal service-to-service traffic at large scale for years before
Spring Cloud packaged the same integration for the broader Java ecosystem.

**HashiCorp Consul.** Consul's documentation explicitly names and supports
client-side discovery as one of its two supported discovery modes, describing
it as the mode where the service consumer is responsible for determining the
access information of available service instances and load balancing requests
between them, by querying Consul's service catalog directly, over its HTTP API
or DNS interface
([HashiCorp, Consul service discovery concepts](https://developer.hashicorp.com/consul/docs/concepts/service-discovery),
verified 2026-08-02). Organizations running Consul without a service mesh data
plane in front of every call, embedding the Consul API or DNS lookup directly
in application code, are exercising this variant of the pattern in production.

**gRPC's pluggable name resolution and client-side load balancing.** gRPC's
own project documentation describes a client-side load balancing architecture
in which the gRPC runtime resolves a logical target name to a set of backend
addresses through a pluggable resolver, then selects among them using a
pluggable load balancing policy inside the client process, with no proxy in
the request path, contrasted explicitly with a proxy-based, server-side
architecture as the other supported mode. This citation reflects the
documented architecture of gRPC's load balancing subsystem and should be
independently re-verified against the current live gRPC documentation before
further reuse, since it was not re-fetched during this specific verification
pass and is reported here as an unverified-in-this-session claim rather than
a freshly confirmed one.

## 10. Consequences

Positive.

- Removes an extra network hop on the request path once the discovery client's
  cache is warm, since the calling process talks directly to the chosen
  instance rather than through an intermediary proxy.
- Gives the calling team full, language-native control over load balancing
  strategy, retry behavior, and circuit breaking, colocated with the call site
  rather than configured externally in a separate infrastructure component.
- Scales the registry query load independently of the request rate for any
  single service pair, since the registry is queried on a cache-refresh
  cadence rather than on every single call.
- Works well in environments, such as Netflix's original AWS deployment
  predating widely available managed load balancers with the needed dynamic
  registration semantics, where no platform-level discovery primitive existed
  yet.

Negative.

- Requires a discovery client library for every language and framework in
  use, per Richardson's own listed drawback
  ([microservices.io, Client-side Service Discovery pattern](https://microservices.io/patterns/client-side-discovery.html),
  verified 2026-08-02), which becomes an ongoing maintenance cost as the
  organization's language mix grows.
- Couples every consumer to the registry's protocol and client library,
  making it harder to swap registries later without touching every calling
  service.
- Introduces cache staleness as a first-class failure mode, a consumer can
  route to an instance that has already stopped accepting traffic until the
  next refresh interval or until enough failed calls trip a circuit breaker.
- Adds the registry itself as new infrastructure to build, secure, monitor,
  and keep highly available, on top of the services it discovers.
- Cannot reasonably be exposed to external or third-party callers, which
  means most systems still need a server-side discovery mechanism, typically
  behind an API Gateway, for anything outside the trusted internal network.

## 11. Failure modes and misuse

**Registry outage taken as a total system outage.** Symptom, every internal
service call starts failing or timing out at once, even though the actual
service instances are healthy. Cause, consumers were not caching instance
lists aggressively enough, or the discovery client had no fallback behavior
when the registry became unreachable, so a registry blip propagated into a
system-wide outage. Fix, cache the last known-good instance list and continue
serving from it, with a bounded staleness tolerance, when the registry cannot
be reached, and alert on registry unavailability separately from alerting on
service call failures.

**Split-brain registry returning inconsistent instance lists.** Symptom, some
consumers route successfully to a service while others, apparently identical,
consistently fail or route to instances that no longer exist, and the pattern
correlates with which registry node or replica a consumer happened to query.
Cause, the registry cluster suffered a network partition and different nodes
hold different, unreconciled views of the currently registered instances.
Fix, run the registry with a consensus protocol appropriate to the
consistency guarantee needed, Consul uses Raft for its catalog, monitor for
partition and leader-election events, and design clients to tolerate a
registry that briefly returns a smaller instance list than reality rather
than treating an empty or short list as authoritative proof that no
instances exist.

**Thundering herd on registry refresh.** Symptom, the registry's CPU or
network load spikes in a regular, visible pattern correlated with the client
refresh interval, sometimes severely enough to slow down registrations and
heartbeats. Cause, many consumer instances share the same fixed refresh
interval and, because they all started around the same time or were deployed
together, poll the registry in near-lockstep. Fix, add jitter to the refresh
interval per client instance so refreshes spread out over time instead of
synchronizing.

**Stale cache masking a real outage.** Symptom, a service is completely down,
but calls to it appear to succeed intermittently, or fail with connection
errors rather than a clean no-instances-available response, for longer than
expected. Cause, the discovery client's cache still holds entries for
instances that stopped responding, and the client has no active health
checking of its own, relying entirely on the registry's next refresh cycle
to remove them, and the registry's own health check interval is itself
generous. Fix, layer client-side circuit breaking on top of discovery so
repeated connection failures to a specific cached instance remove it from
the local selection pool immediately, independent of the registry's next
scheduled refresh.

**Client library drift across services.** Symptom, different services in the
same organization behave inconsistently under the same registry outage or
instance failure, some recovering gracefully and others cascading, and
debugging reveals they are running different, unpatched versions of the
discovery client library. Cause, because each language ecosystem maintains
its own client, and each service team upgrades on its own schedule, the fleet
drifts into running many divergent versions with different bug fixes and
default behaviors. Fix, treat the discovery client library the same as any
other shared dependency requiring a coordinated upgrade cadence, and where
feasible standardize on a small number of supported client versions across
the organization.

## 12. Trade-off matrix

| Force | Client-side Service Discovery | Server-side Service Discovery | Third-Party Registration plus client-side lookup |
|---|---|---|---|
| Extra network hop per call | None once cache is warm | Yes, through a load balancer or mesh proxy | None once cache is warm, same as client-side |
| Language coverage | Requires a client library per language | Any language, plain HTTP to the proxy | Requires a client library per language, same cost as client-side |
| Central policy enforcement (mTLS, rate limits) | Hard, policy lives in every client | Easy, centralized in the proxy | Hard, same limitation as client-side |
| Operational surface added | Registry plus a client library per language | Registry plus a load balancer or mesh data plane | Registry plus a registration agent plus a client library |
| Blast radius of registry outage | High unless clients cache aggressively | Lower, the proxy can hold a cached view centrally | High, same as client-side, mitigated by the agent's local cache |
| Suitability for external or third-party callers | Poor, cannot embed a client in an untrusted caller | Good, the proxy is the trusted edge | Poor, same limitation as client-side |

The comparison to Server-side Service Discovery is the primary axis, since the
two patterns solve the identical problem and are the direct alternatives
Richardson catalogs side by side. Third-Party Registration is included because
it changes who registers an instance, not who performs the lookup, so it is
frequently, and correctly, combined with client-side discovery rather than
being a full substitute for it.

## 13. Related and incompatible patterns

**Server-side Service Discovery** is the direct alternative that moves the
lookup and load-balancing decision out of the consumer and into an
infrastructure component such as a load balancer, API gateway, or service
mesh sidecar proxy, at the cost of an additional network hop per call.
Choosing between the two is largely the decision this whole entry is about.

**Self-Registration** and **Third-Party Registration** are the two patterns
that answer a different question, how a service instance's location gets
into the registry in the first place, and either can be paired with
client-side discovery. Self-registration has the instance register itself on
startup; third-party registration delegates that to a separate registrar
process or agent, which decouples the service's business logic from the
discovery mechanism's client library entirely on the registration side, even
while the consumer side still uses a client-side discovery library to read
from the registry.

**API Gateway** composes with, rather than replaces, client-side discovery.
An API Gateway typically sits at the system's edge and may itself act as a
service consumer using client-side discovery to route an inbound request to
the correct internal service instance, meaning the gateway is the discovery
client and everything behind it is discovered this way, while external
callers of the gateway never see the internal registry at all.

**Circuit Breaker** is the pattern most commonly layered directly on top of a
client-side discovery client, since the same process that already knows the
full set of candidate instances is well positioned to track per-instance
failure rates and eject a failing instance from its local selection pool
faster than the registry's own health check would remove it.

There is no pattern in this catalog that client-side service discovery is
flatly incompatible with; the closest thing to a conflict is architectural
redundancy rather than incompatibility. Running client-side discovery on top
of a platform, such as Kubernetes, that already provides server-side
discovery through its Service abstraction duplicates work rather than
breaking anything, which is why the non-applicability list in dimension 4
calls that combination out specifically.

## 14. Refactoring path in and out

**Introducing client-side discovery into a system with hardcoded addresses.**
Start by standing up the service registry as new infrastructure, unconnected
to any live traffic, and prove it is reliable under its own load and failure
testing before any service depends on it. Next, modify one low-risk service to
self-register or be registered by an agent on startup, without yet routing any
real traffic through the registry, and confirm the registry's view matches
reality by comparing it against the platform's own source of truth, such as
the orchestrator's instance list. Then introduce the discovery client library
into exactly one consumer of that service, behind a feature flag or a
percentage-based rollout, with the hardcoded address path kept as the fallback,
and only fully cut over once the discovery path has run cleanly under
production load for a meaningful observation window. Repeat consumer by
consumer, service by service, rather than attempting a single cutover, and
retire the hardcoded address configuration for a given service pair only
after its discovery-based path has been the sole path for a full deployment
cycle.

**Removing client-side discovery once a platform-level alternative exists.**
This typically happens when a team migrates onto Kubernetes or adopts a
service mesh that provides server-side discovery for free. Start by
confirming the platform's discovery mechanism, a Kubernetes Service DNS name
for instance, resolves correctly and load balances acceptably for the
service in question under a shadow or canary traffic slice. Then update
consumers to call the platform-provided name instead of invoking the
discovery client, one consumer at a time, while leaving the old registry
registrations in place as a safety net. Once every consumer of a given
service has migrated and the service's discovery-client-based traffic has
dropped to zero for a full deployment cycle, remove that service's
registration logic and, eventually, decommission the registry entirely once
no service in the system still depends on it.

## 15. Testing and verification

Unit testing the discovery client's selection logic is straightforward
because the load balancing algorithm and cache behavior can be tested against
a fake or mocked registry response, without any real network calls, verifying
that a given cached instance list produces the expected selection distribution
and that a registry error or timeout produces the expected fallback behavior
rather than an unhandled exception. What becomes harder to test in isolation
is the full registration-to-discovery loop, since that requires either a real
registry instance running in the test environment or a sufficiently faithful
fake registry that models registration, heartbeat expiry, and query
consistency.

Integration testing should run the discovery client against a real, ephemeral
instance of the actual registry technology in use, brought up in a test
container for the duration of the test suite, so that registration semantics,
including TTL expiry behavior and consistency characteristics under
concurrent registration and query, are exercised faithfully rather than
approximated by a mock. A useful test double for the registry in
component-level tests of a single consumer is a small in-memory HTTP stub that
implements just the registry's query endpoint and returns a scripted instance
list, letting the test assert on the consumer's behavior, retry, timeout,
circuit-breaking, without depending on real registry infrastructure.

Chaos and fault-injection testing is particularly valuable for this pattern
because its most damaging failure modes, registry unavailability and cache
staleness, are exactly the kind of failure that a happy-path test suite never
exercises. Killing the registry, or a majority of its cluster nodes,
mid-test, and asserting that already-cached consumers continue functioning
within their staleness tolerance rather than failing immediately, is the
single most valuable test to add for a client-side discovery integration.
Equally, deregistering or killing a specific service instance and measuring
how long a consumer continues routing to it before removing it from
selection, whether through registry refresh or client-side circuit breaking,
verifies the pattern's actual failure-recovery latency rather than an assumed
one.

## 16. Observability signals

The registry itself needs its own health and latency dashboards, since it is
now a shared dependency for every consumer. Track registry query latency by
percentile, registry availability, the size of the currently registered
instance set per service, and the rate of registration and deregistration
events, since an unusually high churn rate can indicate flapping instances or
a misbehaving health check.

On the consumer side, the discovery client should expose the age of its
current cached instance list, since a cache age that exceeds several multiples
of the expected refresh interval is a leading indicator that the client has
lost connectivity to the registry and is silently operating on stale data.
The client should also expose, per downstream service, the count of instances
currently in its selection pool versus the count returned by the registry's
last successful query, so an operator can see at a glance whether
client-side circuit breaking has ejected instances the registry still
believes are healthy.

A healthy instance of this pattern, viewed on a dashboard, shows registry
query latency in the low milliseconds, a cache age consistently near the
configured refresh interval and never drifting far above it, a selection-pool
size that tracks the registry's reported instance count closely, and a
registration and deregistration rate that correlates with actual deployment
events rather than occurring continuously in the background. A failing
instance shows a cache age climbing steadily without bound, a selection pool
that has shrunk to zero or a single instance while the registry reports more,
or a spike in deregistration events with no corresponding deployment,
suggesting instances are failing health checks rather than shutting down
cleanly.

## 17. Security and privacy implications

The service registry becomes a map of the internal network topology, which
service instances exist, where they run, and often what metadata tags or
versions they carry, so read access to the registry should be restricted to
trusted internal callers only, and the registry should never be reachable
from outside the trusted network boundary. An attacker who can query the
registry gains a reconnaissance advantage equivalent to an internal network
scan without having to perform one.

Write access, the ability to register or deregister an instance, is a more
severe exposure. An attacker or a misbehaving process that can register a
malicious instance under a legitimate service's name can cause consumers to
route production traffic, potentially including sensitive request payloads
and credentials in transit, directly to an attacker-controlled endpoint,
since the discovery client trusts whatever the registry returns. Registries
should require authenticated, and ideally mutually authenticated, connections
for registration, and the network path between an instance and the registry
should itself be encrypted, since heartbeats and registration payloads travel
across it continuously.

Because client-side discovery removes the centralized proxy hop that
server-side discovery would otherwise provide, it also removes the natural
place to terminate mutual TLS, enforce a uniform authorization policy, or
apply a consistent audit log for every internal service call. Organizations
choosing client-side discovery for its latency benefits should be aware they
are accepting the responsibility for pushing that security policy into every
individual consumer, or layering a separate mechanism, such as a service mesh
sidecar operating alongside rather than instead of the discovery client, back
on top of it. This paragraph is engineering judgement rather than a sourced
claim about any specific registry's design.

## 18. References

- Chris Richardson, *Microservices Patterns*, Manning Publications, 2018,
  chapter 3, "Interprocess communication," service discovery section.
- [microservices.io, Client-side Service Discovery pattern](https://microservices.io/patterns/client-side-discovery.html),
  verified 2026-08-02.
- [Netflix, eureka GitHub repository](https://github.com/Netflix/eureka),
  verified 2026-08-02.
- [HashiCorp, Consul service discovery concepts](https://developer.hashicorp.com/consul/docs/concepts/service-discovery),
  verified 2026-08-02.
- [Kubernetes documentation, Service](https://kubernetes.io/docs/concepts/services-networking/service/),
  verified 2026-08-02.
- gRPC project load balancing architecture documentation, describing
  client-side, resolver-and-balancer-based load balancing as distinct from
  proxy-based load balancing. Not re-fetched in this verification pass,
  flagged in dimension 9 as needing independent re-confirmation before
  further reuse.

## Code examples

### TypeScript

```typescript
interface ServiceInstance {
  host: string;
  port: number;
}

class ServiceRegistryClient {
  private cache: ServiceInstance[] = [];
  private lastRefresh = 0;
  private readonly refreshIntervalMs: number;

  constructor(
    private readonly serviceName: string,
    private readonly fetchInstances: (name: string) => Promise<ServiceInstance[]>,
    refreshIntervalMs = 30_000
  ) {
    this.refreshIntervalMs = refreshIntervalMs;
  }

  private async refreshIfStale(): Promise<void> {
    const age = Date.now() - this.lastRefresh;
    if (this.cache.length > 0 && age < this.refreshIntervalMs) {
      return;
    }
    try {
      const fresh = await this.fetchInstances(this.serviceName);
      if (fresh.length > 0) {
        this.cache = fresh;
        this.lastRefresh = Date.now();
      }
    } catch {
      // registry unreachable, keep serving the last known-good cache
    }
  }

  async pickInstance(): Promise<ServiceInstance> {
    await this.refreshIfStale();
    if (this.cache.length === 0) {
      throw new Error(`no instances available for ${this.serviceName}`);
    }
    const index = Math.floor(Math.random() * this.cache.length);
    return this.cache[index];
  }
}

async function demo(): Promise<void> {
  const fakeRegistry = async (name: string): Promise<ServiceInstance[]> => [
    { host: "10.0.0.11", port: 8080 },
    { host: "10.0.0.12", port: 8080 },
  ];
  const client = new ServiceRegistryClient("payment-service", fakeRegistry);
  const instance = await client.pickInstance();
  console.log(`routing to ${instance.host}, port ${instance.port}`);
}

demo();
```

### Go

```go
package main

import (
	"errors"
	"fmt"
	"math/rand"
	"sync"
	"time"
)

type ServiceInstance struct {
	Host string
	Port int
}

type FetchFunc func(serviceName string) ([]ServiceInstance, error)

type DiscoveryClient struct {
	mu              sync.Mutex
	serviceName     string
	fetch           FetchFunc
	cache           []ServiceInstance
	lastRefresh     time.Time
	refreshInterval time.Duration
}

func NewDiscoveryClient(name string, fetch FetchFunc, interval time.Duration) *DiscoveryClient {
	return &DiscoveryClient{serviceName: name, fetch: fetch, refreshInterval: interval}
}

func (d *DiscoveryClient) refreshIfStale() {
	d.mu.Lock()
	defer d.mu.Unlock()
	if len(d.cache) > 0 && time.Since(d.lastRefresh) < d.refreshInterval {
		return
	}
	fresh, err := d.fetch(d.serviceName)
	if err != nil || len(fresh) == 0 {
		return
	}
	d.cache = fresh
	d.lastRefresh = time.Now()
}

func (d *DiscoveryClient) Pick() (ServiceInstance, error) {
	d.refreshIfStale()
	d.mu.Lock()
	defer d.mu.Unlock()
	if len(d.cache) == 0 {
		return ServiceInstance{}, errors.New("no instances available")
	}
	return d.cache[rand.Intn(len(d.cache))], nil
}

func fakeRegistry(name string) ([]ServiceInstance, error) {
	return []ServiceInstance{
		{Host: "10.0.0.21", Port: 9090},
		{Host: "10.0.0.22", Port: 9090},
	}, nil
}

func main() {
	client := NewDiscoveryClient("order-service", fakeRegistry, 30*time.Second)
	instance, err := client.Pick()
	if err != nil {
		fmt.Println("discovery failed", err)
		return
	}
	fmt.Printf("routing to %s, port %d\n", instance.Host, instance.Port)
}
```

### Python

```python
import random
import time
from dataclasses import dataclass
from typing import Callable, List


@dataclass(frozen=True)
class ServiceInstance:
    host: str
    port: int


class DiscoveryClient:
    def __init__(
        self,
        service_name: str,
        fetch_instances: Callable[[str], List[ServiceInstance]],
        refresh_interval_seconds: float = 30.0,
    ) -> None:
        self._service_name = service_name
        self._fetch_instances = fetch_instances
        self._refresh_interval = refresh_interval_seconds
        self._cache: List[ServiceInstance] = []
        self._last_refresh = 0.0

    def _refresh_if_stale(self) -> None:
        age = time.monotonic() - self._last_refresh
        if self._cache and age < self._refresh_interval:
            return
        try:
            fresh = self._fetch_instances(self._service_name)
        except Exception:
            return
        if fresh:
            self._cache = fresh
            self._last_refresh = time.monotonic()

    def pick_instance(self) -> ServiceInstance:
        self._refresh_if_stale()
        if not self._cache:
            raise RuntimeError(f"no instances available for {self._service_name}")
        return random.choice(self._cache)


def fake_registry(name: str) -> List[ServiceInstance]:
    return [
        ServiceInstance(host="10.0.0.31", port=7070),
        ServiceInstance(host="10.0.0.32", port=7070),
    ]


if __name__ == "__main__":
    client = DiscoveryClient("inventory-service", fake_registry)
    instance = client.pick_instance()
    print(f"routing to {instance.host}, port {instance.port}")
```

Java, Rust, and Swift are omitted from the runnable examples in this entry.
The pattern's shape, a cached registry lookup plus a load balancing selection,
is identical in those languages to the three shown above, and adding three
more near-duplicate implementations of the same twenty lines of logic would
not add a genuinely new idiom the way, for example, a language-specific
closure-based Strategy variant would in a different pattern. The three
languages shown span a statically typed, garbage-collected language with
async and await (TypeScript), a statically typed, compiled, goroutine-native
language (Go), and a dynamically typed, garbage-collected language (Python),
which together cover the idiomatic range this pattern actually varies across.
