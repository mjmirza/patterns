---
name: Self Registration
slug: self-registration
family: 10-microservices
category: Microservices
aliases: [Client-Side Registration, Push Registration, Service Self-Registration]
first_described: "Richardson 2018, Microservices Patterns, Manning"
maturity: canonical
related: [service-registry, client-side-service-discovery, server-side-service-discovery, self-contained-service]
incompatible_with: []
verified: 2026-08-02
---

# Self Registration

## 1. Name, aliases, and lineage

The canonical name is Self Registration, cataloged by Chris Richardson at
microservices.io under this exact name and treated as the counterpart to
Third-Party Registration in his book Microservices Patterns, Manning, 2018,
chapter 3. The microservices.io entry states the pattern plainly. "A service
instance is responsible for registering itself with the service registry. On
startup the service instance registers itself, host and IP address, with the
service registry and makes itself available for discovery"
(https://microservices.io/patterns/self-registration.html, verified 2026-08-02).

The pattern predates the word microservice. Distributed systems built on Sun's
Java Naming and Directory Interface (JNDI) and on CORBA's Naming Service in the
1990s already had objects bind their own reference into a directory at startup,
the same shape under a different name, and the JNDI specification calls this
operation `bind`, performed by the object itself against a `Context`
(https://docs.oracle.com/javase/jndi/tutorial/basics/directory/bind.html, verified
2026-08-02, page confirms `Context.bind` is invoked by the object publishing its
own reference). Netflix's Eureka client library is the implementation most
engineers meet first, and inside that community "self-registering with Eureka"
is used as a near-synonym for the pattern name. HashiCorp's Consul calls the
same act service registration and exposes it as an HTTP call an application
makes against its local agent (https://developer.hashicorp.com/consul/docs/services/usage/register-services-checks,
verified 2026-08-02, the page instructs sending "a PUT request to the
/agent/service/register API endpoint to dynamically register a service").
Apache ZooKeeper's ensemble has no built-in notion of a service at all. an
application that wants Self Registration on ZooKeeper creates an ephemeral
znode itself under a well-known path, and the ephemeral lifetime, tied to the
client's session, is what gives the pattern its automatic cleanup on crash
(ZooKeeper Programmer's Guide, "Ephemeral Nodes" section,
https://zookeeper.apache.org/doc/current/zookeeperProgrammers.html, verified
2026-08-02). This entry follows Richardson's naming and treats Eureka, Consul,
and a hand-rolled ZooKeeper client as three implementations of one pattern.

Two adjacent uses of the word registration are not this pattern and confusing
them is the most common mistake in casual conversation about it. DNS SRV
record publication by a DHCP or dynamic DNS client is address registration at
the network layer, not application-layer service metadata. Kubernetes Pod
readiness reported through a readiness probe is not registration either,
because the Kubernetes control plane, not the Pod, is what writes the
EndpointSlice entry, the exact opposite direction of data flow from Self
Registration (see dimension 4).

## 2. Problem and context

A service instance's network location changes on every deployment, every
autoscaling event, and every crash-and-restart. In a virtual machine or bare
metal world locations moved rarely and were kept current by hand in a
configuration file or a load balancer's static pool. In a world where an
orchestrator can replace an instance in seconds and can run tens of identical
instances behind one logical name, a human updating a file cannot keep pace,
and every client, or every reverse proxy standing in for the clients, needs a
current answer to "where is a healthy instance of the payment service right
now."

The context in which this specific pattern, as opposed to Service Registry in
general, becomes the right question is narrower. it is a question about who
writes to the registry, not whether a registry exists at all. Given that a
Service Registry (see the sibling entry) holds the current set of instance
locations, something has to populate it, and there are exactly two directions
data can flow. the instance pushes its own record in, which is Self
Registration, or an external process discovers the instance and pushes the
record in on the instance's behalf, which is Third-Party Registration
(https://microservices.io/patterns/self-registration.html, verified 2026-08-02, states
the two patterns as the direct alternative to each other). Self Registration
fits when the instance itself is the party best positioned to know it is ready,
because readiness for one service can mean "warmed a connection pool and
finished a cache preload," a fact no external health check endpoint reveals
until the instance chooses to expose it. It also fits when the platform
supplies no infrastructure-level registration hook at all, which was Netflix's
own situation before Eureka existed, EC2 instances launched by Auto Scaling
groups with no platform-native service catalog to lean on.

## 3. Forces

**Simplicity of infrastructure versus coupling of application code.** Self
Registration needs no separate agent process and no orchestrator integration,
a library linked into the service is the entire mechanism. The price is that
every service, in every language the organization runs, now carries a
dependency on the registry client and on the registry's availability
characteristics.

**Freshness of readiness versus blast radius of a bad deploy.** Because the
instance decides for itself when it is ready to register, and can defer
registration until an internal warm-up finishes, the registry reflects a
richer notion of health than a generic TCP check. The same freedom means a
buggy service that registers itself while still broken degrades the whole
pool, because nothing outside the instance vetoes the decision.

**Failure isolation versus split-brain risk.** If the instance is also
responsible for deregistering itself and for renewing its own lease, an
instance that is alive but network-partitioned from the registry looks
identical, from the registry's point of view, to one that has crashed. Both
stop renewing. The registry has to decide, using only a timeout, which one it
is looking at, and it will sometimes get this wrong in both directions (see
dimension 11).

**Language homogeneity versus polyglot cost.** An organization running one
language and one framework can ship registration as a shared internal library
once and be done. An organization running Java, Go, Python, and a legacy PHP
monolith side by side has to either write and maintain a self-registration
client per language, or accept that some services cannot participate, which
usually forces a Third-Party Registration fallback for exactly those services
and produces a mixed-strategy system (Richardson, Microservices Patterns,
Manning, 2018, section 3.2.3, discusses the polyglot registration client cost
as the primary argument for Third-Party Registration instead).

**Operational cost versus feature richness.** A self-registering client can
report a graded state, `STARTING`, `UP`, `DRAINING`, `DOWN`, and can hold a
connection open specifically to signal liveness (Eureka's renewal heartbeat is
exactly this). A registry-side health checker run by a separate agent, as in
Third-Party Registration, is usually limited to what it can observe from
outside, typically a TCP connect or an HTTP status code, and cannot see
`DRAINING` unless the application exposes it through that same external
surface anyway.

## 4. Applicability and non-applicability

Reach for Self Registration when:

- The organization already standardizes on one or two languages and can afford
  to build or adopt one registration client library once.
- Individual services have meaningful internal warm-up or shutdown sequences
  that only the process itself can observe, and the registry needs to reflect
  states beyond simple network reachability.
- The deployment platform provides no native service catalog, or the team does
  not want to depend on one, for example a fleet of EC2 instances behind Auto
  Scaling with no Kubernetes or Nomad control plane underneath them.
- The team is comfortable operating a dedicated registry, Eureka, Consul, or
  ZooKeeper, as a piece of infrastructure with its own availability
  requirements.

Do NOT reach for Self Registration when:

- The platform already performs Third-Party Registration for free. Running on
  Kubernetes and hand-rolling a Eureka-style client inside every Pod duplicates
  work the kubelet and the EndpointSlice controller already do, and it
  introduces a second, competing source of truth about which instances exist
  (https://kubernetes.io/docs/concepts/services-networking/service, verified
  2026-08-02, confirms the control plane populates EndpointSlices from Pod
  selectors with no application involvement, "you don't need to modify your
  existing application to use an unfamiliar service discovery mechanism").
- The organization runs a genuinely polyglot fleet, five or more languages
  each with a handful of services, where the cost of maintaining that many
  registration clients exceeds the cost of running one external registrar
  process per host or per platform integration instead.
- The service is a batch job, a cron-triggered worker, or anything without a
  long-lived listening endpoint. registration exists to answer "where can I
  send a request to this," and nothing sends requests to a batch job.
- Regulatory or security policy forbids a workload from holding outbound
  network credentials to a shared control-plane service, which some Third-Party
  Registration setups avoid by keeping that credential on a sidecar or agent
  the application process never touches directly.
- The team cannot commit to operating the registry itself as reliable
  infrastructure. a registry that is down more often than the services it
  tracks makes every consumer of Self Registration worse off than no registry
  at all.

## 5. Structure

**Service instance.** The running process. Owns a registration client, decides
when it is ready to accept traffic, and is responsible for calling register on
startup, renew on an interval, and deregister on graceful shutdown.

**Registration client.** A library, in-process, linked into the service
instance. Wraps the wire protocol to the registry, holds the instance's own
metadata (host, port, health-check URL, version tag, zone), and runs the
background renewal timer. In Eureka this is `DiscoveryClient`. in Consul it is
whatever HTTP client the application uses to call the local agent's
`/v1/agent/service/register` endpoint. in a ZooKeeper approach it is the
znode-creation call the application makes itself.

**Service Registry.** The external, shared store of current instance
locations. Exposes a register operation, a renew or heartbeat operation, a
deregister operation, and a query operation that Client-Side or Server-Side
Discovery reads from. See the Service Registry entry for its own internal
structure, this pattern only describes the write path into it.

**Health signal.** Either a value the instance pushes as part of its heartbeat,
Eureka's status field, `UP`, `DOWN`, `STARTING`, `OUT_OF_SERVICE`, or a
liveness mechanism the registry infers from the presence or absence of a
timely renewal, an expired lease, or a lost session. Which one applies depends
on the registry implementation, both exist in the wild.

**Consumer.** Anything that reads the registry to route a request, a client
performing Client-Side Discovery or a load balancer performing Server-Side
Discovery. Structurally outside this pattern's boundary, present only because
the write path exists to serve the read path.

## 6. ASCII structure diagram

```
+------------------------------+           +---------------------------+
|      Service Instance         |           |      Service Registry     |
|                                |           |                            |
|  +--------------------------+  |  register |  +----------------------+  |
|  | Application code         |  | --------> |  | Registration table   |  |
|  +--------------------------+  |           |  |  instance -> host    |  |
|  +--------------------------+  |  renew    |  |  instance -> port    |  |
|  | Registration client       |  | --------> |  |  instance -> status |  |
|  |  (library, in-process)    |  |           |  |  instance -> lease   |  |
|  +--------------------------+  |  dereg    |  |     expiry           |  |
|                                | --------> |  +----------------------+  |
+------------------------------+           +---------------------------+
                                                        ^
                                                        | query
                                                        |
                                            +---------------------------+
                                            |  Consumer                  |
                                            |  (Client-Side or           |
                                            |   Server-Side Discovery)   |
                                            +---------------------------+
```

## 7. Dynamics

Startup, healthy path.

```
Instance          Registration Client      Service Registry
  |  process starts        |                      |
  | ----------------------> |                      |
  |  init connections,      |                      |
  |  warm caches             |                      |
  |  (internal readiness)    |                      |
  | ----------------------> |                      |
  |  signal "ready"          |  register(host, port, meta)
  |                          | -------------------> |
  |                          |                      | store record,
  |                          |                      | status = UP,
  |                          |                      | start lease timer
  |                          | <------------------- | ack, lease TTL
  |                          |  start renew loop     |
  |                          |  (interval < TTL/2)   |
```

Steady state, renewal.

```
Registration Client                     Service Registry
  |  every N seconds                          |
  |  renew(instance_id)                        |
  | ------------------------------------------> |
  |                                              | reset lease timer
  | <-------------------------------------------- | ack
```

Graceful shutdown.

```
Instance                Registration Client        Service Registry
  |  SIGTERM received           |                        |
  | --------------------------> |  deregister(instance_id) |
  |  stop accepting new work     | -----------------------> |
  |  drain in-flight requests    |                          | remove record
  |                              | <----------------------- | ack
  |  process exits                |                          |
```

Crash without deregistration, the case the pattern cannot make graceful.

```
Instance                Registration Client        Service Registry
  |  process crashes (no        |                        |
  |  SIGTERM handler run)        |                        |
  |  X                           X                        |
  |                                            (silence, no renew calls)
  |                                                        |
  |                                     lease TTL elapses without renewal
  |                                                        |
  |                                         status -> DOWN, or record evicted
```

## 8. Implementation variants

**Push-heartbeat registration (Eureka-style).** The client calls register once
and then calls renew on a timer strictly shorter than the server's lease
duration. Netflix's Eureka defaults this to a 30-second renewal interval
against a 90-second lease duration, verified against the constants
`DEFAULT_LEASE_RENEWAL_INTERVAL = 30` and `DEFAULT_LEASE_DURATION = 90` defined
in `LeaseInfo.java` in the Eureka source
(https://raw.githubusercontent.com/Netflix/eureka/master/eureka-client/src/main/java/com/netflix/appinfo/LeaseInfo.java,
verified 2026-08-02). Missing three consecutive renewals is what expires the
lease under those defaults. This variant favors freshness at the cost of
constant background chatter proportional to instance count.

**Session-bound ephemeral node (ZooKeeper-style).** The client creates an
ephemeral znode as part of establishing its session with the ensemble. no
separate heartbeat call exists at the application level, because the
ZooKeeper client library maintains the session's own liveness underneath the
application, and the ensemble deletes the znode automatically when the session
expires (ZooKeeper Programmer's Guide, "Ephemeral Nodes,"
https://zookeeper.apache.org/doc/current/zookeeperProgrammers.html, verified
2026-08-02). This variant pushes the renewal mechanics down into the client
library, which the application author never touches directly, at the cost of
depending on ZooKeeper's own session and quorum behavior.

**Sidecar-delegated self-registration (Consul agent).** The application still
initiates registration, but it registers with a Consul agent running on the
same host rather than with the cluster directly, either by writing a service
definition file the agent reads on start, or by calling the agent's local
`/v1/agent/service/register` HTTP endpoint
(https://developer.hashicorp.com/consul/docs/services/usage/register-services-checks,
verified 2026-08-02). The agent then handles the harder problem of gossiping
that fact to the rest of the cluster and running the actual health check
(TTL, HTTP, TCP, or script) on the application's behalf. This is a hybrid.
the application still decides what to register and when, which keeps it Self
Registration in spirit, but it delegates the network-hard part, cluster-wide
propagation, to infrastructure.

**Framework-integrated auto-registration.** Spring Cloud Netflix's
`@EnableEurekaClient` and its Consul equivalent wire the register call into the
framework's own application-context lifecycle, so an ordinary Spring Boot
application gets Self Registration by adding a dependency and an annotation,
with no explicit register or renew call written by the application author. The
pattern's shape does not change, the registration client still runs
in-process and still initiates the calls, only the amount of code the
application author has to write by hand shrinks to nearly zero.

## 9. Known production uses

Netflix's own microservices platform is the pattern's most cited real-world
instance. every service built on the internal platform links the Eureka
client, and the client both registers on startup and renews on the 30-second
interval described above, with Netflix's own engineering wiki documenting the
peer replication and reconciliation behaviour that keeps registry state
consistent across zones (https://github.com/Netflix/eureka/wiki, verified 2026-08-02,
states operations performed on one server are replicated to peer nodes and
reconciled on the next heartbeat).

HashiCorp Consul is used for Self Registration by a wide range of companies
running mixed VM and container fleets. HashiCorp's own documentation frames
the primary registration path as the application, or a script wrapping it,
calling the local agent's register endpoint or dropping a service definition
file for the agent to pick up
(https://developer.hashicorp.com/consul/docs/services/usage/register-services-checks,
verified 2026-08-02).

Apache Cassandra's gossip protocol performs a structurally identical act at
the cluster-membership layer rather than the service-catalog layer, each node
announces its own presence and state to the ring on startup rather than
waiting for an external process to discover it, following the same
push-your-own-record shape this pattern names, described in the Cassandra
architecture documentation on gossip
(https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html section on
gossip, verified 2026-08-02, describes gossip as a peer-to-peer protocol
where "nodes periodically exchange state information about themselves").

Spring Cloud Netflix packages this pattern as a drop-in library for the Java
ecosystem, its own reference documentation describes the
`EurekaAutoServiceRegistration` bean as automatically registering the local
service instance with the Eureka server on application startup
(https://docs.spring.io/spring-cloud-netflix/docs/current/reference/html/#service-discovery-eureka-clients,
verified 2026-08-02, section "Registering with Eureka" states the client
"will register the service with the Eureka Server").

## 10. Consequences

Positive.

- No separate agent process or orchestrator integration is required, the
  registration client is the entire infrastructure footprint beyond the
  registry itself.
- The instance can encode a richer readiness signal than an external checker
  can observe, including multi-step internal warm-up and graceful drain
  states.
- Deregistration on graceful shutdown can be immediate and deterministic,
  because the instance itself triggers it as part of its own shutdown
  sequence, rather than waiting for an external health check to time out.
- Works identically regardless of the underlying compute platform, virtual
  machine, bare metal, or container, because it depends on nothing but network
  reachability to the registry.

Negative.

- Every language and framework the organization runs needs its own
  registration client, or a hand-written equivalent, which is real, ongoing
  maintenance work multiplied by the number of languages in use.
- Couples every service's codebase to the registry's client library and its
  failure modes, an outage or a bug in the registration client can crash or
  hang an unrelated business service.
- A crashed instance that never called deregister relies entirely on a
  timeout-based lease expiry to be removed, which means there is always a
  window, bounded by the lease duration, during which the registry reports a
  dead instance as alive.
- A network partition between an otherwise-healthy instance and the registry
  is indistinguishable, from the registry's perspective, from that instance
  having crashed, because both manifest as missed renewals.

## 11. Failure modes and misuse

**Symptom.** Consumers intermittently receive connection refused or timeout
errors against an instance that the registry still lists as UP, minutes after
that instance was terminated. **Cause.** The instance was killed with SIGKILL,
by an out-of-memory killer or a forceful platform terminate, bypassing the
graceful-shutdown code path that would have called deregister, and the
registry is waiting out the full lease TTL before evicting the stale record.
**Fix.** Shorten the lease TTL and renewal interval to match the tolerance for
stale entries the business can accept, and separately have consumers apply a
circuit breaker or retry-with-backoff against individual instance failures
rather than trusting registry freshness as the only defense.

**Symptom.** A newly deployed instance receives production traffic
immediately, before its connection pools are warm, causing a burst of slow
responses right after every deploy. **Cause.** The registration client was
wired to call register as the very first action on process start rather than
after application-level readiness, so the registry marks the instance UP
before it can actually serve fast responses. **Fix.** Gate the register call
behind the application's own readiness check, do not register on process
start, register after the last warm-up step completes.

**Symptom.** During a rolling deploy, half the fleet briefly disappears from
the registry query results even though every instance is healthy. **Cause.**
Renewal calls from surviving instances are timing out because the registry
itself is under load or is mid-election in a Raft or Paxos-based
implementation, and the client's renewal library treats a timeout the same as
an explicit failure and lets the lease lapse. **Fix.** Configure the
registration client's renewal retry policy with jittered backoff and a retry
budget that exceeds a single missed renewal interval, so a transient registry
hiccup does not cascade into a mass deregistration.

**Symptom.** Two instances with the same logical service name and different
physical addresses are both marked UP, but one of them silently stopped doing
useful work hours ago, for example it lost its database connection while
staying network-reachable to the registry itself. **Cause.** The
registration client's health signal is checking only that the process is
alive and can reach the registry, not that the process can do its actual job,
so a "brownout" state never surfaces as anything other than UP. **Fix.**
Push a real application-level health check, not a liveness ping, into the
periodic renewal payload, and have the instance transition its own status to
`OUT_OF_SERVICE` when a critical downstream dependency it needs is
unreachable.

**Symptom.** The registration client library itself becomes a single point of
failure, an unhandled exception inside the renewal thread crashes the whole
process, taking down a service that was otherwise functioning correctly.
**Cause.** Registration and business logic run in the same process with
shared failure domains, and the registration client was not defensively
isolated, for example its background thread has no top-level exception
handler. **Fix.** Run the renewal loop in a supervised background thread with
its own exception boundary, so a registry-side failure degrades discoverability
without crashing the service that is otherwise doing its job fine.

## 12. Trade-off matrix

| Force | Self Registration | Third-Party Registration | Kubernetes-native discovery |
|---|---|---|---|
| Extra infrastructure to run | None beyond the registry itself | A registrar process per host or platform, for example Netflix's Prana sidecar or Kubernetes's own controller | None beyond the cluster control plane already required to run Kubernetes at all |
| Application code coupling | High, every service links a client library | Low to none, the application need not know a registry exists | None, standard Kubernetes manifests are enough |
| Readiness expressiveness | High, the instance decides exactly when and with what metadata to register | Bounded by whatever the registrar can observe externally | Bounded by the readiness probe's HTTP or TCP contract |
| Polyglot cost | High, one client per language | Low, one registrar handles every language uniformly | Low, one kubelet mechanism handles every language uniformly |
| Deregistration timing on crash | Delayed until lease TTL expiry | Delayed until the registrar's external health check fails | Delayed until the readiness probe fails and the endpoint controller reconciles |
| Portability across platforms | High, depends only on network reachability | Depends on platform hooks existing | None, tied specifically to Kubernetes |

## 13. Related and incompatible patterns

**Service Registry.** Self Registration is meaningless without a Service
Registry to write into. the two are always paired, and the registry entry
describes the store, this entry describes the write path into it.

**Third-Party Registration.** The direct alternative for who performs the
write. mutually exclusive in a strict sense for a single service, though a
mixed fleet can run some services with Self Registration and others behind a
platform-provided Third-Party Registration mechanism side by side.

**Client-Side Service Discovery and Server-Side Service Discovery.** Both are
downstream consumers of whatever Self Registration wrote into the registry,
neither cares which registration strategy populated it, so this pattern
composes cleanly with either.

**Self-Contained Service.** A service that owns its own registration client
in-process is exercising the same instinct, the instance is responsible for
its own operational concerns, that Self-Contained Service applies to
deployment and runtime dependencies more broadly.

**Circuit Breaker.** Not a composition partner at the registry layer but a
necessary companion at the consumer layer, because Self Registration's
inherent staleness window (dimension 10 and 11) means a consumer that trusts
the registry blindly will occasionally call a dead instance, and a circuit
breaker is what keeps that occasional failure from cascading.

No pattern in this catalog is fundamentally incompatible with Self
Registration, the closest to a real tension is running it alongside a
platform, such as Kubernetes, that already performs an equivalent function,
where the two mechanisms can produce two different, disagreeing views of which
instances currently exist.

## 14. Refactoring path in and out

**Introducing it.** Start by choosing the registry technology and running it
as a small, separately deployed piece of infrastructure with its own
availability target, before touching any service code. Add the registration
client dependency to one low-traffic service first and wire register on
readiness and deregister on shutdown signal, verify in the registry's own
dashboard or query API that the entry appears and disappears as expected
across several deploys before expanding to a second service. Only after two
or three services demonstrate the pattern working reliably should the
registration client be pushed into a shared internal library and rolled out
fleet-wide, because retrofitting a broken registration contract across many
services later is far more expensive than fixing it in one.

**Removing it.** Confirm what the registry is actually being used for, if
every consumer already reads through a platform-provided discovery mechanism
and the registry has become a second, unused source of truth, that is the
signal to remove it. Stop new deploys from linking the registration client
first, so the registry's contents shrink to only the older instances still
running the old code, then let those age out through normal deploy cadence
rather than force-killing them, and finally decommission the registry
infrastructure once its instance count reaches zero for a full deploy cycle.

## 15. Testing and verification

Unit test the registration client's state machine in isolation, mocking the
registry's HTTP or RPC surface, asserting register is called exactly once
after readiness and never before, and that deregister is called exactly once
on a shutdown signal and is idempotent if called twice, because shutdown
sequences racing with a second SIGTERM are a real production occurrence.

Integration test against a real, ephemeral instance of the registry
technology, a container running Eureka, Consul in dev mode, or a single-node
ZooKeeper, and assert the full round trip. start the service, poll the
registry's query API until the entry appears, kill the service process with
SIGTERM, poll until the entry disappears within the expected drain window.

Chaos test the crash path specifically, because it is the path unit tests
cannot exercise honestly. kill the service process with SIGKILL rather than
SIGTERM, and assert the registry entry is eventually evicted within the
configured lease TTL, not immediately, and assert consumers with a circuit
breaker or retry policy in front of the registry tolerate the staleness
window without cascading failures of their own.

Load test the registry's renewal path under realistic instance counts before
depending on it in production, because the aggregate renewal traffic scales
linearly with fleet size and a registry that performs well at ten instances
can fall over at ten thousand.

## 16. Observability signals

Track the registered-instance count for each service name as a time series
and alert on a sudden drop, a drop that does not correspond to an intentional
scale-down is the earliest external signal of a registration or renewal
failure. Track renewal call latency and failure rate from the client side,
distinct from the registry's own reported health, because a client that is
timing out on renewal calls will show up here before the registry's own
metrics reflect anything unusual. Track the gap between actual process
termination time and registry-side deregistration time, this gap is the
staleness window from dimension 10 made concrete, and a growing gap over time
usually indicates a rising rate of SIGKILL-style terminations rather than
graceful shutdowns. On the registry side itself, track lease expiry events
distinct from explicit deregister events, a service whose entries are almost
always removed via expiry rather than explicit deregistration is a service
whose shutdown handling is broken.

## 17. Security and privacy implications

The registration payload typically carries an internal hostname or IP
address and a port, which is topology information an organization generally
does not want exposed outside its own network boundary, so the registry
itself needs to sit behind the same network segmentation as the services it
tracks, never on a public-facing endpoint. Because the registration client
runs in-process inside every service, it needs credentials, an API token, a
mutual TLS certificate, or a network-level allowlist entry, to talk to the
registry, and that credential is now present inside every service's runtime
environment. a compromise of any single service that can reach the registry
credential can register a malicious phantom instance under a
trusted service name, which is a realistic vector for traffic interception if
the registry and the discovery mechanism reading from it do not separately
authenticate which entries are legitimate. Registries that also
propagate arbitrary metadata tags supplied at registration time, version
strings, zone labels, custom key-value pairs, should treat that metadata as
untrusted input from the registering service and never let it flow unescaped
into a system that renders it, for example an operational dashboard, without
sanitization.

## 18. References

1. Chris Richardson, "Self registration" (pattern entry),
   https://microservices.io/patterns/self-registration.html, verified 2026-08-02.
2. Chris Richardson, Microservices Patterns, Manning Publications, 2018,
   chapter 3, "Interprocess communication in a microservice architecture,"
   section on service discovery.
3. Oracle, "The Basics of Directory Operations, Binding a Name,"
   https://docs.oracle.com/javase/jndi/tutorial/basics/directory/bind.html, verified
   2026-08-02.
4. HashiCorp, "Register services and health checks,"
   https://developer.hashicorp.com/consul/docs/services/usage/register-services-checks,
   verified 2026-08-02.
5. Apache Software Foundation, "ZooKeeper Programmer's Guide, Ephemeral
   Nodes," https://zookeeper.apache.org/doc/current/zookeeperProgrammers.html,
   verified 2026-08-02.
6. Netflix, "Understanding Eureka Peer to Peer Communication,"
   https://github.com/Netflix/eureka/wiki/Understanding-Eureka-Peer-to-Peer-Communication,
   verified 2026-08-02.
7. Netflix, `LeaseInfo.java`, Eureka source,
   https://github.com/Netflix/eureka/blob/master/eureka-client/src/main/java/com/netflix/appinfo/LeaseInfo.java,
   verified 2026-08-02, confirming `DEFAULT_LEASE_RENEWAL_INTERVAL = 30` and
   `DEFAULT_LEASE_DURATION = 90`.
8. Kubernetes, "Service,"
   https://kubernetes.io/docs/concepts/services-networking/service, verified
   2026-08-02.
9. Apache Software Foundation, "Cassandra Architecture, Gossip,"
   https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html,
   verified 2026-08-02.
10. VMware Tanzu, "Spring Cloud Netflix Reference Documentation, Registering
    with Eureka,"
    https://docs.spring.io/spring-cloud-netflix/docs/current/reference/html/#service-discovery-eureka-clients,
    verified 2026-08-02.

## Code examples

Self Registration's core is a client that registers on readiness, renews on a
timer, and deregisters on shutdown. The examples below build a minimal, working
version of that lifecycle against an in-memory HTTP registry stand-in, so the
control flow is visible without pulling in a real Eureka or Consul dependency.
All four were run against the Node, Go, Rust, and Python toolchains present on
this machine. Java was not available to compile on this machine, and Java's
real production shape is already shown through Spring Cloud Netflix in
dimension 9, so it is omitted here rather than shipped unverified.

### TypeScript

```typescript
type Status = "STARTING" | "UP" | "OUT_OF_SERVICE" | "DOWN";

interface RegistryClient {
  register(instanceId: string, host: string, port: number): Promise<void>;
  renew(instanceId: string): Promise<boolean>;
  deregister(instanceId: string): Promise<void>;
}

class InMemoryRegistry implements RegistryClient {
  private leases = new Map<string, number>();

  async register(instanceId: string, host: string, port: number): Promise<void> {
    this.leases.set(instanceId, Date.now());
    console.log(`registered ${instanceId} at ${host}:${port}`);
  }

  async renew(instanceId: string): Promise<boolean> {
    if (!this.leases.has(instanceId)) return false;
    this.leases.set(instanceId, Date.now());
    return true;
  }

  async deregister(instanceId: string): Promise<void> {
    this.leases.delete(instanceId);
    console.log(`deregistered ${instanceId}`);
  }
}

class SelfRegisteringInstance {
  private status: Status = "STARTING";
  private renewTimer: ReturnType<typeof setInterval> | null = null;

  constructor(
    private readonly instanceId: string,
    private readonly host: string,
    private readonly port: number,
    private readonly registry: RegistryClient,
    private readonly renewIntervalMs = 30_000,
  ) {}

  async warmUp(): Promise<void> {
    await new Promise((resolve) => setTimeout(resolve, 5));
    this.status = "UP";
  }

  async start(): Promise<void> {
    await this.warmUp();
    if (this.status !== "UP") {
      throw new Error("cannot register before readiness");
    }
    await this.registry.register(this.instanceId, this.host, this.port);
    this.renewTimer = setInterval(async () => {
      const ok = await this.registry.renew(this.instanceId);
      if (ok) {
        console.log(`renewed ${this.instanceId}`);
      } else {
        console.error(`renew failed for ${this.instanceId}, re-registering`);
        await this.registry.register(this.instanceId, this.host, this.port);
      }
    }, this.renewIntervalMs);
  }

  async shutdown(): Promise<void> {
    if (this.renewTimer) clearInterval(this.renewTimer);
    this.status = "DOWN";
    await this.registry.deregister(this.instanceId);
  }
}

async function main() {
  const registry = new InMemoryRegistry();
  const instance = new SelfRegisteringInstance("payments-7f3a", "10.0.4.12", 8080, registry, 50);
  await instance.start();
  await new Promise((resolve) => setTimeout(resolve, 120));
  await instance.shutdown();
}

main();
```

Compiled and ran with `npx tsc --strict --target es2020 --module commonjs
self-registration.ts` followed by `node self-registration.js` on Node v23.11.0
and TypeScript 7.0.2. Output confirmed registration, followed by two renewal
cycles, followed by deregistration, no errors.

### Go

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

type Status int

const (
	Starting Status = iota
	Up
	Down
)

type Registry struct {
	mu     sync.Mutex
	leases map[string]time.Time
}

func NewRegistry() *Registry {
	return &Registry{leases: make(map[string]time.Time)}
}

func (r *Registry) Register(id, host string, port int) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.leases[id] = time.Now()
	fmt.Printf("registered %s at %s:%d\n", id, host, port)
}

func (r *Registry) Renew(id string) bool {
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, ok := r.leases[id]; !ok {
		return false
	}
	r.leases[id] = time.Now()
	return true
}

func (r *Registry) Deregister(id string) {
	r.mu.Lock()
	defer r.mu.Unlock()
	delete(r.leases, id)
	fmt.Printf("deregistered %s\n", id)
}

type Instance struct {
	id       string
	host     string
	port     int
	status   Status
	registry *Registry
	stopCh   chan struct{}
	doneCh   chan struct{}
}

func NewInstance(id, host string, port int, registry *Registry) *Instance {
	return &Instance{
		id:       id,
		host:     host,
		port:     port,
		status:   Starting,
		registry: registry,
		stopCh:   make(chan struct{}),
		doneCh:   make(chan struct{}),
	}
}

func (in *Instance) warmUp() {
	time.Sleep(5 * time.Millisecond)
	in.status = Up
}

func (in *Instance) Start(renewInterval time.Duration) {
	in.warmUp()
	if in.status != Up {
		panic("cannot register before readiness")
	}
	in.registry.Register(in.id, in.host, in.port)

	ticker := time.NewTicker(renewInterval)
	go func() {
		defer close(in.doneCh)
		for {
			select {
			case <-ticker.C:
				if in.registry.Renew(in.id) {
					fmt.Printf("renewed %s\n", in.id)
				} else {
					fmt.Printf("renew failed for %s, re-registering\n", in.id)
					in.registry.Register(in.id, in.host, in.port)
				}
			case <-in.stopCh:
				ticker.Stop()
				return
			}
		}
	}()
}

func (in *Instance) Shutdown() {
	close(in.stopCh)
	<-in.doneCh
	in.status = Down
	in.registry.Deregister(in.id)
}

func main() {
	registry := NewRegistry()
	instance := NewInstance("payments-7f3a", "10.0.4.12", 8080, registry)
	instance.Start(50 * time.Millisecond)
	time.Sleep(120 * time.Millisecond)
	instance.Shutdown()
}
```

Compiled and ran with `go run self-registration.go` on go1.26.4 darwin/arm64.
Output confirmed registration, at least two renewal cycles, and a clean
deregistration on shutdown, with no data race reported under `go run -race`.

### Rust

```rust
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

#[derive(Clone, Copy, PartialEq, Debug)]
enum Status {
    Starting,
    Up,
    Down,
}

struct Registry {
    leases: Mutex<HashMap<String, Instant>>,
}

impl Registry {
    fn new() -> Self {
        Registry {
            leases: Mutex::new(HashMap::new()),
        }
    }

    fn register(&self, id: &str, host: &str, port: u16) {
        self.leases
            .lock()
            .unwrap()
            .insert(id.to_string(), Instant::now());
        println!("registered {} at {}:{}", id, host, port);
    }

    fn renew(&self, id: &str) -> bool {
        let mut leases = self.leases.lock().unwrap();
        if leases.contains_key(id) {
            leases.insert(id.to_string(), Instant::now());
            true
        } else {
            false
        }
    }

    fn deregister(&self, id: &str) {
        self.leases.lock().unwrap().remove(id);
        println!("deregistered {}", id);
    }
}

struct Instance {
    id: String,
    host: String,
    port: u16,
    status: Status,
}

impl Instance {
    fn new(id: &str, host: &str, port: u16) -> Self {
        Instance {
            id: id.to_string(),
            host: host.to_string(),
            port,
            status: Status::Starting,
        }
    }

    fn warm_up(&mut self) {
        thread::sleep(Duration::from_millis(5));
        self.status = Status::Up;
    }
}

fn main() {
    let registry = Arc::new(Registry::new());
    let mut instance = Instance::new("payments-7f3a", "10.0.4.12", 8080);

    instance.warm_up();
    assert_eq!(instance.status, Status::Up, "cannot register before readiness");
    registry.register(&instance.id, &instance.host, instance.port);

    let stop = Arc::new(Mutex::new(false));
    let renew_registry = Arc::clone(&registry);
    let renew_id = instance.id.clone();
    let renew_stop = Arc::clone(&stop);
    let renew_host = instance.host.clone();
    let renew_port = instance.port;

    let handle = thread::spawn(move || loop {
        thread::sleep(Duration::from_millis(50));
        if *renew_stop.lock().unwrap() {
            break;
        }
        if renew_registry.renew(&renew_id) {
            println!("renewed {}", renew_id);
        } else {
            println!("renew failed for {}, re-registering", renew_id);
            renew_registry.register(&renew_id, &renew_host, renew_port);
        }
    });

    thread::sleep(Duration::from_millis(120));

    *stop.lock().unwrap() = true;
    handle.join().unwrap();

    instance.status = Status::Down;
    registry.deregister(&instance.id);
}
```

Compiled and ran with `rustc self-registration.rs -o self-registration`
followed by `./self-registration` on rustc 1.97.1. Output confirmed
registration, at least two renewal cycles, and a clean deregistration on
shutdown.

### Python

```python
import threading
import time
from dataclasses import dataclass, field
from enum import Enum, auto


class Status(Enum):
    STARTING = auto()
    UP = auto()
    DOWN = auto()


@dataclass
class Registry:
    leases: dict = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def register(self, instance_id: str, host: str, port: int) -> None:
        with self.lock:
            self.leases[instance_id] = time.monotonic()
        print(f"registered {instance_id} at {host}:{port}")

    def renew(self, instance_id: str) -> bool:
        with self.lock:
            if instance_id not in self.leases:
                return False
            self.leases[instance_id] = time.monotonic()
            return True

    def deregister(self, instance_id: str) -> None:
        with self.lock:
            self.leases.pop(instance_id, None)
        print(f"deregistered {instance_id}")


class SelfRegisteringInstance:
    def __init__(self, instance_id: str, host: str, port: int, registry: Registry, renew_interval: float = 0.05):
        self.instance_id = instance_id
        self.host = host
        self.port = port
        self.registry = registry
        self.renew_interval = renew_interval
        self.status = Status.STARTING
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _warm_up(self) -> None:
        time.sleep(0.005)
        self.status = Status.UP

    def start(self) -> None:
        self._warm_up()
        if self.status is not Status.UP:
            raise RuntimeError("cannot register before readiness")
        self.registry.register(self.instance_id, self.host, self.port)

        def renew_loop() -> None:
            while not self._stop.wait(self.renew_interval):
                if self.registry.renew(self.instance_id):
                    print(f"renewed {self.instance_id}")
                else:
                    print(f"renew failed for {self.instance_id}, re-registering")
                    self.registry.register(self.instance_id, self.host, self.port)

        self._thread = threading.Thread(target=renew_loop, daemon=True)
        self._thread.start()

    def shutdown(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join()
        self.status = Status.DOWN
        self.registry.deregister(self.instance_id)


if __name__ == "__main__":
    registry = Registry()
    instance = SelfRegisteringInstance("payments-7f3a", "10.0.4.12", 8080, registry)
    instance.start()
    time.sleep(0.12)
    instance.shutdown()
```

Ran with `python3 self-registration.py` on Python 3.14.6. Output confirmed
registration, at least two renewal cycles, and a clean deregistration on
shutdown, with no thread left dangling.
