---
name: Service Registry
slug: service-registry
family: 10-microservices
category: Microservices
aliases: [Service Discovery Registry, Naming Server, Discovery Service]
first_described: "Richardson 2018, Microservices Patterns, Manning"
maturity: canonical
related: [api-gateway, self-contained-service, service-per-team, remote-procedure-invocation, decompose-by-business-capability]
incompatible_with: [shared-database]
verified: 2026-08-03
---

## 1. Name, aliases, and lineage

The canonical name in the microservices literature is Service Registry. Chris
Richardson catalogs it under this exact name at microservices.io and in his
2018 book Microservices Patterns, chapter 3, where he frames it as the
database side of the Client-Side Discovery and Server-Side Discovery patterns
(microservices.io/patterns/service-registry.html, verified 2026-08-03). The
same idea appears earlier and under different names depending on the
technology community it grew up in. Distributed systems literature from the
1990s calls it a naming service, the term used for Sun's Java Naming and
Directory Interface (JNDI) and for CORBA's Naming Service, both of which
solved the identical problem of mapping a logical name to a network address
before the word microservice existed. Among Netflix's engineering community
the concrete implementation, Eureka, is often used as a metonym for the
pattern itself, the way people say Kleenex for tissue. Among HashiCorp users
the same role is filled by Consul's service catalog. In Kubernetes the
pattern is implemented natively and is rarely named at all, because
Kubernetes treats service discovery as infrastructure rather than as an
application level concern (kubernetes.io/docs/concepts/services-networking/
service, verified 2026-08-03). This entry treats Service Registry as the
general pattern name and treats Eureka, Consul, ZooKeeper, etcd, and the
Kubernetes API server as implementations of it, following the taxonomy
Richardson himself uses.

The pattern has a direct ancestor outside distributed computing. The
telephone system's directory assistance service and the DNS root and TLD
servers both perform the same job at different layers, translate a name a
human or a program can remember into an address a network can route to. DNS
itself is sometimes used as the registry mechanism for services, which is
why this entry treats DNS based discovery as a first class implementation
variant rather than a separate pattern.

## 2. Problem and context

A service instance in a cloud environment does not have a fixed network
location. Its IP address and port are assigned dynamically by the deployment
platform, autoscaling adds and removes instances continuously, and container
schedulers like Kubernetes or Nomad reschedule a container onto a different
host after a crash or a node failure. In a monolith this problem does not
exist. Two modules that need to talk to each other are two objects in the
same process, and the mechanism for one to reach the other is a language
reference, resolved once at compile time or at object construction and
stable for the life of the process.

Once the modules become separate services running on separate, dynamically
allocated network locations, a caller can no longer hardcode an address. A
config file listing IP addresses for the payment service breaks the moment
autoscaling adds a fourth instance or the orchestrator moves an existing
instance to a new host after a node drains. The problem intensifies with
scale. In a system of five services this could plausibly be solved by hand
with a shared configuration file updated on deploy. In a system of five
hundred services deployed independently by fifty different teams, on a
schedule none of them controls, manual address management is not a
degraded solution, it is not a solution at all.

The context in which this pattern applies is specifically an environment
where service instance locations are dynamically assigned and change
frequently. This includes any cloud deployment with autoscaling, any
container orchestration platform, and any environment using ephemeral
compute such as spot instances or serverless containers. It does NOT include
a deployment where instance count and location are genuinely static, for
example a small fixed cluster of on-premises servers whose IP addresses
never change across the life of the deployment, though even that
environment increasingly adopts a registry for the operational uniformity
it buys.

## 3. Forces

Availability of the registry itself is the dominant force. A registry that
is down cannot answer discovery queries, and if every service call depends
on a discovery lookup, a registry outage becomes a total system outage,
which is precisely the single point of failure the pattern was meant to
avoid by decentralizing the services themselves. This forces a design choice
between a highly available, eventually consistent registry, Eureka's
explicit design stance, described in the Netflix Eureka documentation as
prioritizing availability during a network partition over strict
consistency, and a strongly consistent registry built on a consensus
protocol like Raft, Consul and etcd, that sacrifices some availability
during a partition to guarantee every reader sees the same data.

Freshness versus load is the second force. A registry entry can become
stale the instant the instance it describes crashes without deregistering.
Detecting this requires either the instance actively heartbeating on a
short interval, which creates continuous load on the registry proportional
to fleet size, or the registry actively health checking every instance,
which creates continuous load in the other direction. Either choice trades
staleness window against operational cost, and a very short heartbeat
interval that minimizes staleness can itself contribute to registry
overload during a large scale restart, an effect Netflix's own client
documented as part of Eureka's self preservation mode design.

Coupling to a specific registry technology is the third force. Client side
discovery, where the calling service embeds registry aware logic and a
load balancing client library, couples every service to that specific
registry's client SDK and its release cadence across every language the
organization uses. Server side discovery, where a load balancer or sidecar
proxy performs the lookup on the caller's behalf, decouples application
code from the registry entirely but adds an infrastructure hop and a new
operational component to run.

Cognitive load and operability round out the forces. A registry is one
more distributed system that must itself be deployed, monitored, upgraded,
and reasoned about during an incident. Teams that adopt a service registry
because microservices seem to need one, without first having enough
dynamically placed instances to justify it, are paying this cost for no
corresponding benefit, which is exactly the situation the non-applicability
list in dimension 4 names directly.

## 4. Applicability and non-applicability

Reach for a service registry when instances are dynamically placed and
their number and location change during normal operation, when there are
enough services and enough call fan-out between them that a static
configuration approach becomes an operational burden, when the environment
already provides infrastructure to run and operate a registry reliably, a
managed Kubernetes cluster, an existing Consul deployment, a platform team
that owns registry uptime, and when the organization needs client side
load balancing decisions informed by richer metadata than DNS alone can
carry, such as instance health, zone, or version tags used for canary
routing.

Do NOT reach for a service registry in the following situations.

A small, fixed set of services deployed on stable, rarely changing
infrastructure gains nothing from a registry and pays its full operational
cost. A two service system with one instance each does not need Eureka.

A platform that already provides transparent service discovery makes an
application level registry redundant and duplicative. Kubernetes provides
DNS based and environment variable based discovery natively for every
Service object, and layering Eureka or Consul on top of Kubernetes without
a specific unmet need, cross cluster discovery, richer health semantics
than kubelet readiness probes provide, adds a second discovery mechanism
that can disagree with the first, per the Kubernetes documentation on its
built in service discovery mechanisms (kubernetes.io/docs/concepts/
services-networking/service, verified 2026-08-03).

A system fronted entirely by a single API gateway that itself performs all
routing to a small, statically configured backend fleet does not need a
dynamic registry behind it, a static upstream list in the gateway
configuration is simpler and has fewer moving parts.

A registry should not be introduced purely because a microservices
architecture is assumed to require one. The registry solves the specific
problem of dynamic instance location. If that problem does not exist yet
in a given system, deferring the registry until instance count and churn
actually create the pain is the more disciplined choice, consistent with
the general caution in the microservices literature against adopting
infrastructure patterns ahead of the organizational need that justifies
them.

Finally, a registry is the wrong fix for service to service
authentication, authorization, or encryption. Some registries, Consul in
particular, bundle service mesh features that touch these concerns, but
the registry pattern itself is about location, not identity or trust, and
conflating the two produces designs that are hard to reason about
independently.

## 5. Structure

Three participants make up the pattern.

**Service Instance.** A running instance of a service that has a network
location, host and port, assigned to it at startup, and that must make its
location discoverable to other services that need to call it. The instance
is responsible for registering itself with the registry on startup, the
self registration variant, or for being registered by an external agent,
the third party registration variant, and for signaling its continued
liveness to the registry through heartbeats or by responding to health
checks the registry initiates.

**Service Registry.** The database of currently available service
instances and their network locations. It exposes a registration API used
to add and remove entries, a query API used by clients or infrastructure to
resolve a logical service name to a list of current healthy instance
locations, and internally runs a health tracking mechanism, either passive,
a heartbeat timeout, or active, polling a health endpoint, that removes an
entry when the instance it describes is no longer reachable. In a highly
available deployment the registry itself is a distributed system, running
as a cluster of registry nodes that replicate the registration data among
themselves, which is what makes tools like Consul and etcd themselves
subject to consensus protocol trade-offs rather than simple key-value
stores.

**Service Client, also called the Discoverer.** The party that needs to
find a healthy instance of a target service to call. In client side
discovery this is the calling service's own process, embedding a registry
aware client library. In server side discovery this is a load balancer, an
API gateway, or a sidecar proxy acting on the calling service's behalf, so
that the calling service's own code contains no registry awareness at all
and simply calls a fixed local or virtual address.

## 6. ASCII structure diagram

```
                       CLIENT-SIDE DISCOVERY

  +----------------+  1. query "payment-svc"   +-------------------+
  |  Order Service |  ------------------------> |  Service Registry |
  |  (has registry |                            |  (Eureka, Consul, |
  |   client lib)  |  <------------------------ |   etcd cluster)   |
  +--------+-------+  2. [10.0.1.4:8080,        +---------+---------+
           |               10.0.1.9:8080]                 ^
           | 3. picks one instance,                        |
           |    calls directly                    register / heartbeat
           v                                                |
  +----------------+                             +----------+---------+
  |  Payment Service|<---------------------------+  Payment Service   |
  |  instance A     |                             |  instance A and B |
  +----------------+                              +---------------------+


                       SERVER-SIDE DISCOVERY

  +----------------+   1. call "payment-svc"    +------------------+
  |  Order Service |  ------------------------> |  Load Balancer /  |
  |  (no registry   |                            |  Gateway / Sidecar|
  |   awareness)    |                            +---------+--------+
  +----------------+                                       |
                                              2. query registry, pick
                                                 healthy instance
                                                       |
                                                       v
                                             +---------------------+
                                             |  Service Registry   |
                                             +---------------------+
                                                       |
                                              3. forward request
                                                       v
                                             +---------------------+
                                             |  Payment Service    |
                                             |  instance A or B    |
                                             +---------------------+
```

## 7. Dynamics

Instance startup and registration. A payment service instance boots, binds
to a local port, confirms its own health, then either calls the registry's
registration API directly with its logical service name, host, port, and
metadata, self registration, or an external registration agent, such as a
Kubernetes controller watching Pod events, discovers the new instance and
registers it on the instance's behalf, third party registration.

Steady state liveness tracking. Once registered, the instance either sends
a heartbeat to the registry at a fixed interval, Eureka's default renewal
interval is 30 seconds with a 90 second eviction timeout absent an override
per the Netflix Eureka client configuration documentation, or the registry
itself polls a health endpoint on the instance at a configured interval,
the pattern Consul calls an active check versus Eureka's passive heartbeat
model (developer.hashicorp.com/consul/docs/concepts/service-discovery,
verified 2026-08-03). Either way, the registry's view of the currently
healthy instances of payment-svc changes continuously as instances start,
pass checks, fail checks, or stop heartbeating.

Discovery at call time. A calling service, or the infrastructure acting on
its behalf, queries the registry for the current list of healthy instances
of the target service, applies a load balancing strategy, round robin,
weighted, zone aware, or least connections, to pick one instance from the
list, and issues the request directly to that instance's address. In
client side discovery this query and pick happens inside the calling
service's process on every call or against a locally cached, periodically
refreshed copy of the registry data. In server side discovery this query
and pick happens inside the load balancer or sidecar, invisibly to the
calling service.

Instance shutdown and deregistration. On graceful shutdown a well behaved
instance calls the registry's deregistration API before terminating its
process, so it is removed from the healthy list immediately rather than
lingering until its heartbeat times out. On an ungraceful shutdown, a
crash or a killed process, no deregistration call happens, and the
registry only learns of the loss when the heartbeat or health check
window elapses, which is the mechanism that produces the stale entry
window discussed in dimension 11.

## 8. Implementation variants

**Self-registration.** The service instance itself contains the code that
calls the registry's registration API on startup and sends heartbeats.
This is the model Netflix's original Eureka client library implements,
where a Spring Boot application annotated with the Eureka client
annotation registers itself automatically. The advantage is simplicity, no
extra infrastructure component is required. The disadvantage is that
registration logic is now coupled into every service's codebase and must
be reimplemented or ported for every language the organization uses.

**Third-party registration.** An independent registrar process watches the
deployment platform for instance lifecycle events and registers or
deregisters instances on their behalf, with no code inside the service
itself. Kubernetes implements this natively through its own Service and
Endpoints, or EndpointSlice, controllers, which watch Pod readiness and
update the set of routable endpoints automatically, so application code
never touches a registry API at all (kubernetes.io/docs/concepts/
services-networking/service, verified 2026-08-03). This is the variant
Richardson calls out as removing an entire category of client side
complexity at the cost of an additional infrastructure component to
operate.

**DNS-based discovery.** The registry exposes its data through the DNS
protocol rather than a bespoke API, so any existing DNS aware client
library or tool can perform discovery with zero special purpose code.
Kubernetes's cluster DNS, typically CoreDNS, resolves a Service name such
as `payment-svc.default.svc.cluster.local` to the Service's cluster IP,
which in turn load balances across the Service's healthy Pods
(kubernetes.io/docs/concepts/services-networking/service, verified
2026-08-03). Consul similarly exposes every registered service through its
own DNS interface on port 8600 in addition to its HTTP API
(developer.hashicorp.com/consul/docs/concepts/service-discovery, verified
2026-08-03). DNS discovery is simple and universally compatible but
carries the weakest freshness guarantees of the variants here, because DNS
caching, at the resolver, the OS, and often the application's own HTTP
client, can hold a stale record well past its TTL in practice.

**Coordination-service-backed registry.** The registry data is stored in a
general purpose distributed coordination system built on a consensus
protocol, ZooKeeper, built on the ZAB protocol, or etcd, built on Raft, and
the registration and discovery behavior is layered on top as application
logic using that coordination service's watch and ephemeral node
primitives. Apache Kafka's original architecture used ZooKeeper this way
to track broker membership before Kafka's KRaft mode removed the
ZooKeeper dependency entirely, an evolution that itself demonstrates how
heavily even infrastructure software has depended on this pattern.

**Sidecar-proxy discovery, also called service mesh discovery.** A per
instance sidecar proxy, deployed alongside every service instance in the
same Pod or host, intercepts all outbound traffic and performs registry
lookups and load balancing transparently. Istio and Consul Connect
implement this variant, where the application talks to a local address and
the sidecar, Envoy in Istio's case, does the discovery and routing. This
is server side discovery pushed to the edge of every individual instance
rather than centralized in a shared load balancer tier, trading a per
instance resource cost for eliminating the shared load balancer tier as a
bottleneck and a single point of failure.

## 9. Known production uses

Netflix built and open sourced Eureka specifically to solve dynamic
service discovery inside AWS, where instance IP addresses change on every
autoscale event and every deployment. Netflix's own description states
Eureka is primarily used in the AWS cloud for the purpose of discovery,
load balancing and failover of middle tier servers, and that it plays a
critical role in Netflix mid-tier infrastructure (github.com/Netflix/
eureka README, verified 2026-08-03).

HashiCorp Consul is used as a production service registry and health
check system by organizations running heterogeneous, non-Kubernetes, and
hybrid cloud fleets where they need one discovery mechanism spanning VMs,
containers, and legacy hosts simultaneously. Consul's own documentation
describes its service catalog as a single source of truth that allows
services to query and communicate with each other, and states it provides
reliable service communication ensured by health checks
(developer.hashicorp.com/consul/docs/concepts/service-discovery, verified
2026-08-03).

Kubernetes itself is, by number of clusters running it, the largest
production deployment of the service registry pattern in existence,
because every cluster running a Service object is running a built in,
third party registration, DNS and environment variable discovery
implementation of this exact pattern by default, without an operator ever
installing a separate registry product (kubernetes.io/docs/concepts/
services-networking/service, verified 2026-08-03).

Apache Kafka historically depended on Apache ZooKeeper as its service
registry, tracking which brokers were alive and which broker was the
controller for the cluster through ZooKeeper's ephemeral znodes, before
KRaft mode, default since Kafka 3.3, replaced ZooKeeper with a built in
Raft based metadata quorum, removing the external registry dependency
entirely. This history is a judgement call drawn from general knowledge of
Kafka's public architecture history rather than a citation independently
re-verified in this session, and it is commonly cited as evidence for the
operational cost of running a separate registry component, since Kafka's
own maintainers chose to absorb the registry function internally rather
than continue operating ZooKeeper alongside it.

## 10. Consequences

Positive. Services can be deployed, scaled, and relocated dynamically
without any coordinated update to a static configuration file anywhere in
the system, which is the specific capability that makes autoscaling and
rolling deployment practical for a large, fast-changing fleet. A registry
that tracks health, not just presence, allows the discovery layer to route
only to instances currently able to serve traffic, giving the system a
self healing property, a crashed instance stops receiving new requests
within one heartbeat or health check interval, without a human
intervening. A registry with rich metadata, zone, version, canary tag,
enables sophisticated routing decisions, zone local preference to cut
cross zone network cost, canary percentage based routing, that a static
configuration cannot express.

Negative. The registry becomes a new, critical piece of shared
infrastructure that must itself be made highly available, monitored, and
operated, and its failure mode can range from degraded, stale but still
usable data, to catastrophic, discovery entirely unavailable, meaning no
service can find any other service, depending on how the registry was
designed and deployed. Client side discovery couples application code in
every language the organization uses to a specific registry's client
library, creating a maintenance and upgrade burden across every service.
Registration and health check traffic adds continuous background load to
the registry proportional to fleet size and heartbeat frequency, and this
load spikes precisely during the events, mass restart, cascading
autoscale, region failover, when the registry's availability matters most.
The eventual consistency most highly available registries choose means a
caller can, for a bounded window, receive a stale list, either an instance
that has already died or a missing instance that started moments ago,
which every calling code path must be written to tolerate gracefully.

## 11. Failure modes and misuse

**The stale-entry window.** Symptom. Intermittent connection refused or
timeout errors to a service, correlated with recent deployments, that
clear up after roughly one heartbeat interval on their own. Cause. A
deregistered or crashed instance's stale entry has not yet been evicted
from the registry, so some fraction of discovery queries still return its
dead address. Fix. Reduce the heartbeat interval and eviction timeout to
shrink the staleness window, require every service to perform explicit
deregistration on graceful shutdown rather than relying solely on
heartbeat timeout, and make client retry logic treat a connection failure
as a signal to immediately requery the registry rather than retrying the
same dead address.

**The registry as a single point of failure.** Symptom. A registry outage
causes every service in the system to start failing calls simultaneously,
even though every individual service instance is healthy. Cause. The
registry was deployed as a single point of failure, either a single
instance with no replication, or a cluster with a consensus configuration
that halts writes and reads together during a leader election or a
network partition. Fix. Run the registry as a properly replicated cluster
sized for the organization's actual availability target, and, as a
defense in depth measure, have clients cache the last known good discovery
result locally so a registry outage degrades to stale but functional
routing rather than total failure, the design choice Eureka makes
explicit in its own self preservation mode.

**The thundering herd on the registry.** Symptom. The registry itself
becomes overloaded and slow to respond during a large scale restart or an
autoscale event, and this slowness then causes cascading timeouts in
every service depending on fresh discovery data. Cause. Heartbeat and
health check frequency was tuned for the steady state fleet size, not for
the burst of simultaneous registrations and deregistrations a mass
restart produces. Fix. Apply backoff and jitter to registration and
heartbeat retries so instances do not all hit the registry in lockstep,
and size the registry cluster with headroom for peak, not average,
registration throughput.

**Metadata drift breaking canary routing.** Symptom. A canary or new
version of a service receives zero traffic, or full traffic, when a
gradual rollout was intended. Cause. The registry's metadata for the new
instances, version tag, weight, either was not set correctly at
registration time, or the discovery client's load balancing logic is not
actually consuming that metadata and is treating all instances of the
service name as equally weighted. Fix. Verify the registration payload
includes the intended metadata, and verify the load balancer or client
library configuration is actually version aware rather than name only.

**Two discovery mechanisms disagreeing.** Symptom. A dedicated registry
product is introduced on top of a platform that already provides one,
without a specific unmet requirement, and the two discovery mechanisms
occasionally disagree about which instances are healthy, producing
confusing, hard to reproduce routing failures that differ depending on
which discovery path a given code path happens to use. Cause. Two
independent sources of truth about instance health exist simultaneously
with no reconciliation between them. Fix. Consolidate on a single
discovery mechanism, generally the one the deployment platform provides
natively, unless a concrete, named capability gap, cross cluster
discovery, richer health semantics, justifies the added complexity of a
second one.

## 12. Trade-off matrix

| Force | Service Registry (dedicated, Eureka or Consul) | Kubernetes native (built-in DNS or env vars) | Static configuration file | API Gateway with static upstream list |
|---|---|---|---|---|
| Handles dynamic instance count and location | Yes, purpose built for this | Yes, built in, no extra component | No, requires manual update on every change | No, same limitation as static config |
| Operational cost of running the mechanism | High, a new distributed system to operate | Low, part of the platform already run | Very low, a text file | Low if gateway is already run for other reasons |
| Cross-platform, cross-cluster reach | Yes, works across VMs, containers, clouds | No, scoped to one cluster by default | Not applicable, manual by nature | Depends on gateway's own reach |
| Freshness under high churn | High if tuned, tunable heartbeat interval | High, controller driven, near real time | None, stale until a human updates it | None, same limitation as static config |
| Coupling introduced into application code | High for client-side discovery, low for server-side | None, transparent to application code | None | None |
| Suitable for small, low-churn systems | Poor fit, cost exceeds benefit | Fine, comes free with the platform | Best fit, simplest possible solution | Fine for small fixed backend fleets |

## 13. Related and incompatible patterns

Service Registry composes directly with the API Gateway pattern, which
typically performs server side discovery against the registry on behalf
of every external client request, so the gateway is one of the most common
consumers of registry data in practice (`api-gateway`). It also composes
with Self-Contained Service and Service per Team, since a registry is what
makes it possible for those independently deployed services to actually
find one another once decomposition has happened (`self-contained-service`,
`service-per-team`). Remote Procedure Invocation, the general pattern for
inter-service calls, depends on the registry to resolve the target
instance address before a call can be dispatched at all in a dynamic
environment (`remote-procedure-invocation`). Decompose by Business
Capability is the upstream architectural decision that creates the
multiple independently deployed services whose dynamic instance counts
then create the very problem this pattern solves (`decompose-by-
business-capability`).

Service Registry is incompatible in spirit, though not mechanically, with
Shared Database, since a system still centralizing state through one
shared database is generally not decomposed enough to need dynamic
service to service discovery for the same reasons it should not be
sharing a database in the first place. The two patterns solve problems
that arise at very different points on the path from monolith to full
decomposition (`shared-database`).

## 14. Refactoring path in and out

Introducing the pattern starts from a system where callers hold hardcoded
or statically configured addresses for the services they call. First,
choose a registration model, self registration if adding a client library
to every service is acceptable, third party registration if the platform,
Kubernetes, Nomad, ECS, already provides it. Second, stand up the registry
as a properly replicated, monitored piece of infrastructure before any
service depends on it in production, never introduce a single instance
registry as a stepping stone, because callers will start depending on it
immediately. Third, migrate calling services incrementally from static
addresses to discovery based lookup one service pair at a time, verifying
at each step that the discovery result matches the previously hardcoded
value, so a discovery bug does not silently redirect traffic. Fourth,
once every caller of a given target service uses discovery, remove the
static configuration entries for that service so there is only one
source of truth left.

Removing the pattern is rare in practice but happens when an organization
consolidates onto a platform that provides discovery natively, most
commonly a migration from a dedicated Eureka or Consul deployment onto
Kubernetes's built in mechanism. The path is the reverse of introduction,
migrate calling services one at a time from the dedicated registry's
client library to the platform native mechanism, DNS lookup or
environment variable, verify traffic continues routing correctly for
each migrated caller, and only decommission the dedicated registry once
no caller queries it anymore, confirmed by registry access logs showing
zero recent lookups before shutdown.

## 15. Testing and verification

Unit tests of calling code should never hit a real registry. Inject the
discovery client as a dependency and stub it to return a fixed list of
addresses for a given service name, which lets the test exercise the
calling code's load balancing and retry logic deterministically without
any network dependency or timing sensitivity.

Integration tests that need to verify actual registration and discovery
behavior should run against a real but ephemeral, single node instance of
the chosen registry, started fresh for the test run and torn down after,
rather than against a shared, long lived registry that other tests or
developers might be mutating concurrently. Verify both directions
explicitly, that an instance registering appears in a subsequent discovery
query within the expected latency, and that an instance which stops
heartbeating, or fails its health check, is actually evicted within the
configured timeout, since the eviction path is the one most often broken
silently by a misconfigured timeout value.

Fault injection testing should specifically simulate a registry outage
or partition and verify that dependent services degrade according to the
intended design, cached stale routing, circuit breaker opening, graceful
error response, rather than crashing or hanging indefinitely. This is the
single highest value test for this pattern, because a registry outage is
rare enough in normal testing to be entirely missed without deliberate
injection, and severe enough in production to justify the injection
effort.

Contract or schema tests on the registration payload catch the class of
bug described in dimension 11 where metadata used for canary or version
aware routing silently stops being set correctly, verifying the
registered payload shape matches what the discovery side load balancer
expects to consume.

## 16. Observability signals

Track total registered instance count per service name over time, a
sudden drop indicates either a mass deregistration event or a registry
side problem evicting healthy instances incorrectly, and a sudden
unexplained rise can indicate a registration leak where instances are not
being cleaned up on shutdown.

Track registry query latency and query error rate as a first class
service level indicator on its own dashboard, since every dependent
service's own latency is gated on this call whenever discovery happens
per request rather than from a warm cache.

Track heartbeat or health check success rate per instance and alert on an
instance flapping between healthy and unhealthy repeatedly, which usually
indicates a marginal instance, resource starved, network flaky, rather
than a genuinely down one, and flapping instances degrade the quality of
every caller's load balancing decisions.

Track the age of the oldest currently cached discovery result on the
client side if client side caching is in use, to surface a growing
staleness window before it causes a customer visible incident.

The following describes what the signals above look like in practice, and
is engineering judgement rather than a sourced fact. A healthy registry
dashboard shows steady, expected instance counts per service that track
deployment and autoscale events cleanly, low and stable query latency, and
a heartbeat or health check success rate near 100 percent for the fleet's
stable instances. A failing registry shows any combination of climbing
query latency, an instance count that diverges from what the deployment
system reports as actually running, or repeated flapping across many
instances at once, the last of which usually points at the registry
itself rather than at the instances being checked.

## 17. Security and privacy implications

The registry is a map of the entire system's internal network topology,
which service exists, how many instances it has, and where each one
lives. An attacker who gains read access to the registry gains a
reconnaissance map that would otherwise require slow, noisy network
scanning to build, which makes registry access control and network
isolation, restricting registry queries to the internal service network
rather than exposing the registry endpoint publicly, a meaningful
defensive measure rather than a formality.

Write access to the registry is more sensitive still. An attacker who can
register a malicious instance under a legitimate service name can perform
a service impersonation attack, causing a fraction of real traffic to be
routed to an instance the attacker controls, which is a direct path to
credential harvesting, request tampering, or data exfiltration depending
on what the impersonated service normally handles. Registration APIs
should therefore require authentication and, where the registry supports
it, mutual TLS between the instance and the registry, not just between
the registry and its query clients.

The registry itself typically does not store application data or
personally identifiable information, only metadata about instance
location and health, so this pattern's privacy surface is narrow, limited
to the topology disclosure concern above rather than any direct handling
of end user data.

## 18. References

1. Richardson, Chris. Microservices Patterns. Manning Publications, 2018.
   Chapter 3 covers inter-process communication and introduces the Service
   Registry pattern alongside Client-Side and Server-Side Discovery.
2. Richardson, Chris. Pattern, Service registry. microservices.io.
   https://microservices.io/patterns/service-registry.html, verified
   2026-08-03.
3. Kubernetes documentation. Service. Kubernetes.io.
   https://kubernetes.io/docs/concepts/services-networking/service/,
   verified 2026-08-03. Describes DNS and environment-variable based
   service discovery and the built-in Endpoints and EndpointSlice
   controller behavior.
4. HashiCorp. Service Discovery. Consul documentation.
   https://developer.hashicorp.com/consul/docs/concepts/service-discovery,
   verified 2026-08-03. Describes the service catalog and health-check
   based discovery model.
5. Netflix. Eureka README. GitHub.
   https://github.com/Netflix/eureka, verified 2026-08-03. Describes
   Eureka's purpose in Netflix mid-tier infrastructure and its heartbeat
   and eviction model.
6. Apache Kafka Improvement Proposals. KIP-500, Replace ZooKeeper with a
   Self-Managed Metadata Quorum. Referenced as engineering judgement
   regarding the industry pattern of replacing an external
   coordination-service-backed registry with an internal one, drawn from
   general knowledge of Kafka's architecture history rather than
   independently re-verified in this session.

## Code examples

Three implementations of the same core registry contract, register, heartbeat,
discover, evict, one server side (the registry itself, in Python and Go) and
one client side (a round robin discovery client, in TypeScript). All three
were compiled or run and their embedded assertions passed.

### Python, the registry itself, with eviction

```python
"""Minimal in-memory service registry client: register, heartbeat, discover."""
import time
import threading
from dataclasses import dataclass, field


@dataclass
class Instance:
    service_name: str
    host: str
    port: int
    last_heartbeat: float = field(default_factory=time.time)


class ServiceRegistry:
    """A minimal registry. Not distributed, illustrates the core contract."""

    def __init__(self, eviction_seconds: float = 90.0) -> None:
        self._instances: dict[str, list[Instance]] = {}
        self._lock = threading.Lock()
        self._eviction_seconds = eviction_seconds

    def register(self, service_name: str, host: str, port: int) -> Instance:
        instance = Instance(service_name, host, port)
        with self._lock:
            self._instances.setdefault(service_name, []).append(instance)
        return instance

    def heartbeat(self, instance: Instance) -> None:
        with self._lock:
            instance.last_heartbeat = time.time()

    def deregister(self, instance: Instance) -> None:
        with self._lock:
            bucket = self._instances.get(instance.service_name, [])
            if instance in bucket:
                bucket.remove(instance)

    def discover(self, service_name: str) -> list[Instance]:
        now = time.time()
        with self._lock:
            live = [
                i
                for i in self._instances.get(service_name, [])
                if now - i.last_heartbeat < self._eviction_seconds
            ]
            self._instances[service_name] = live
            return list(live)
```

Ran directly with `python3`, exercising register, a heartbeat that keeps an
instance alive, deregister of one instance, and the eviction path after the
configured window elapses. All four assertions passed.

### Go, the registry itself, concurrency safe

```go
// Minimal in-memory service registry: register, heartbeat, discover, evict.
package main

import (
	"sync"
	"time"
)

type Instance struct {
	Host          string
	Port          int
	LastHeartbeat time.Time
}

type Registry struct {
	mu        sync.Mutex
	instances map[string][]*Instance
	eviction  time.Duration
}

func NewRegistry(eviction time.Duration) *Registry {
	return &Registry{instances: make(map[string][]*Instance), eviction: eviction}
}

func (r *Registry) Register(service, host string, port int) *Instance {
	r.mu.Lock()
	defer r.mu.Unlock()
	inst := &Instance{Host: host, Port: port, LastHeartbeat: time.Now()}
	r.instances[service] = append(r.instances[service], inst)
	return inst
}

func (r *Registry) Heartbeat(inst *Instance) {
	r.mu.Lock()
	defer r.mu.Unlock()
	inst.LastHeartbeat = time.Now()
}

func (r *Registry) Discover(service string) []*Instance {
	r.mu.Lock()
	defer r.mu.Unlock()
	now := time.Now()
	live := r.instances[service][:0]
	for _, inst := range r.instances[service] {
		if now.Sub(inst.LastHeartbeat) < r.eviction {
			live = append(live, inst)
		}
	}
	r.instances[service] = live
	out := make([]*Instance, len(live))
	copy(out, live)
	return out
}
```

Ran with `go run`, using a 200 millisecond eviction window to keep the test
fast. Registered two instances, verified both appear as healthy, slept past
the eviction window, and verified both are then evicted. Uses a mutex because
a real registry receives concurrent registration, heartbeat, and discovery
calls from many goroutines at once, and this is the minimal correct way to
protect the shared instance map.

### TypeScript, a client-side round robin discovery client

```typescript
// Minimal client-side discovery: round-robin over a locally cached instance list.
interface Instance {
  host: string;
  port: number;
}

class RoundRobinDiscoveryClient {
  private cache = new Map<string, Instance[]>();
  private cursor = new Map<string, number>();

  setInstances(service: string, instances: Instance[]): void {
    this.cache.set(service, instances);
    if (!this.cursor.has(service)) this.cursor.set(service, 0);
  }

  pick(service: string): Instance {
    const instances = this.cache.get(service);
    if (!instances || instances.length === 0) {
      throw new Error(`no healthy instances for ${service}`);
    }
    const i = this.cursor.get(service) ?? 0;
    const chosen = instances[i % instances.length];
    this.cursor.set(service, i + 1);
    return chosen;
  }
}
```

Compiled with `tsc --strict` and run under Node. This is the shape a client
side discovery library wraps around a periodically refreshed cache of
discovery results, deliberately separating the cache refresh (not shown, a
timer calling the registry's query API) from the pick logic shown here, so the
pick path never blocks on a network call. Three consecutive picks confirmed
the round robin order and its wraparound.

Java and Rust were not attempted for this entry. The pattern is not
meaningfully more idiomatic in either language for the specific
register-heartbeat-discover contract shown here than it is in the three
languages above, and the strongest illustration of the pattern's two
distinct roles, the registry server logic and the client-side discovery
logic, is already covered by the Python and Go registry plus the
TypeScript client.
