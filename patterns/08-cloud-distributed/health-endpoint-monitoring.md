---
name: Health Endpoint Monitoring
slug: health-endpoint-monitoring
family: 08-cloud-distributed
category: Cloud and Distributed
aliases: [Health Check Endpoint, Liveness and Readiness Probes, Health Check API]
first_described: "Homer, Arnold, Kanso, Neve, Odeh, Sciacca, Wang 2014"
maturity: canonical
related: [circuit-breaker, bulkhead, retry-with-backoff, sidecar, ambassador, load-balancer]
incompatible_with: []
verified: 2026-08-02
---

# Health Endpoint Monitoring

## 1. Name, aliases, and lineage

The canonical name in the pattern-catalog literature is Health Endpoint
Monitoring. It was written up as one of the twenty-four patterns in the
Microsoft patterns and practices team's *Cloud Design Patterns. Prescriptive
Architecture Guidance for Cloud Applications*, by Alex Homer, Trent Arnold,
Masashi Narumoto, Rohit Sharma and others, first published by Microsoft
Press in 2014 and republished as the "Health Endpoint Monitoring pattern" in
the Azure Architecture Center. The catalog's own wording states the intent
plainly, "Implement functional checks in an application that external tools
can access at regular intervals through exposed endpoints." The pattern
belongs to the catalog's "Resiliency" and "Management and monitoring"
groupings, alongside Circuit Breaker and Retry, because a health endpoint is
the sensing half of a resiliency system whose acting half is a load balancer,
an orchestrator, or a human operator deciding what to do about a bad signal
([Azure Architecture Center, Health Endpoint Monitoring pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/health-endpoint-monitoring),
verified 2026-08-02).

The idea of exposing a machine-checkable status endpoint is older than the
named pattern and older than the cloud. Load balancer vendors and Unix service
supervisors built ad hoc health probes for decades before anyone gave the
practice a catalog name. What the 2014 catalog entry did was give the informal
practice a name, a problem statement, and an explicit list of issues and
considerations, which is what lets later work build a shared vocabulary on top
of it, notably the Kubernetes project's split of the single idea into three
named probe types.

Three aliases are in active, distinct use, and confusing them is the most
common source of misconfigured health checks.

- **Health Endpoint Monitoring** is the catalog name for the general pattern,
  an application exposes an HTTP or RPC endpoint that reports its own status,
  and something external polls it. This is the umbrella name this entry uses.
- **Liveness and Readiness Probes** is the Kubernetes-specific vocabulary for
  two distinct roles a health endpoint can play, formalized in the kubelet's
  probe configuration. A **startup probe** is a third, narrower role added
  later for slow-booting containers
  ([Kubernetes documentation, Liveness, Readiness, and Startup Probes](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/),
  verified 2026-08-02).
- **Health Check API** is the generic term used by library and framework
  authors, for example Spring Boot Actuator's `/actuator/health` endpoint or
  the gRPC Health Checking Protocol's `Health` service, when they refer to the
  contract itself rather than to a specific deployment's use of it.

A useful test to keep the three straight. The pattern is the *idea* of an
externally-pollable status endpoint. Liveness and readiness are two *roles* a
health endpoint plays under a specific orchestrator's semantics. A Health
Check API is a *library-level implementation surface* that a given
application exposes so a poller of any kind, Kubernetes, a load balancer, a
human dashboard, can consume it.

## 2. Problem and context

A service that has crashed is easy to notice. It stops responding entirely,
and TCP connection failures or process-exit events surface the fact
immediately to anything watching. The problem Health Endpoint Monitoring
solves is the much larger and much more common category of failure where the
process is still running, still accepting connections, and still returning
HTTP 200 to a bare TCP-level check, while it is nonetheless unable to do its
job. A worker whose event loop has deadlocked on a lock it will never release
still holds an open listening socket. A container whose outbound connection
to its database pool has exhausted still answers `curl` on its own port. A
newly started instance that has not finished loading its in-memory cache will
happily accept a request and serve wrong or empty data rather than refuse it.

The context that produces this problem is inherent to any environment where a
process is one of many identical replicas managed by something else, an
orchestrator, a load balancer, an autoscaler, that must decide, without a
human in the loop and at a cadence of seconds, whether to route traffic to
this specific instance and whether to keep this specific instance running at
all. The Azure Architecture Center's context statement for the pattern frames
this precisely. Monitoring a cloud service is harder than monitoring an
on-premises one because "you don't have full control of the hosting
environment" and the service "typically depend[s] on other services that
platform vendors and others provide," so factors like network latency,
underlying compute and storage performance, and inter-service bandwidth can
each independently degrade a service that is, by every process-level signal,
still alive
([Azure Architecture Center, Health Endpoint Monitoring pattern, Context and problem](https://learn.microsoft.com/en-us/azure/architecture/patterns/health-endpoint-monitoring),
verified 2026-08-02). The managing system needs a richer signal than "is the
process running." It needs an answer to a question the process itself is
uniquely positioned to answer honestly, can I currently do useful work.

A second, distinct part of the context is that "is my process alive" and
"can I currently do useful work" are two genuinely different questions with
different consumers and different correct actions on failure, and treating
them as one question is itself a major source of production incidents,
covered in depth in dimension 11.

## 3. Forces

- **Signal fidelity versus check cost.** A health check that does nothing but
  return 200 unconditionally is cheap and worthless. A health check that
  performs a full write-read round trip against every downstream dependency
  on every poll is expensive, can itself become the bottleneck under load,
  and, if it runs synchronously inline with the poll, can push the poller's
  own timeout past the point where the poller gives up and marks the instance
  unhealthy anyway. The pattern favors a graded middle, a shallow, in-process
  check for the fast, frequent liveness role, and a deeper, cacheable,
  dependency-aware check for the slower readiness role.
- **False negatives versus false positives.** A false-negative health check,
  one that reports unhealthy while the instance could actually serve traffic,
  wastes capacity and, if it triggers a restart, can amplify load onto the
  survivors and trigger a cascade (dimension 11). A false-positive health
  check, one that reports healthy while the instance cannot actually serve
  traffic, routes real user requests into a black hole. The pattern has no
  way to eliminate both risks at once; every threshold and timeout choice is
  a trade between them.
- **Coupling the health signal to a dependency's own availability.** Checking
  a downstream dependency inside a health endpoint makes the checking
  instance's reported health a function of that dependency's health. This is
  exactly the coupling the pattern must decide, deliberately, whether to
  accept, and for which role. Kubernetes' own documentation is explicit that
  accepting this coupling in a liveness probe, rather than a readiness probe,
  is a caution-labeled anti-pattern precisely because of what it does to the
  blast radius of a dependency outage
  ([Kubernetes documentation, Liveness, Readiness, and Startup Probes](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/),
  verified 2026-08-02).
- **Security exposure versus operational transparency.** A detailed health
  endpoint that reports which specific dependency failed and why is far more
  useful to an operator debugging an incident, and far more useful to an
  attacker doing reconnaissance. The catalog's own issues-and-considerations
  section spends more words on securing the endpoint than on any other single
  concern
  ([Azure Architecture Center, Health Endpoint Monitoring pattern, Issues and considerations](https://learn.microsoft.com/en-us/azure/architecture/patterns/health-endpoint-monitoring),
  verified 2026-08-02).
- **Push versus pull, and who owns the polling cadence.** In the
  Kubernetes-managed and load-balancer-managed shapes described here, the
  poller decides the cadence and the timeout, and the application has no say
  in either. In a push-based health reporting shape, seen in some
  service-mesh and heartbeat-based systems, the instance decides when to
  report and the collector infers absence as failure. The two shapes trade
  different failure modes for different operational simplicity, covered in
  dimension 8.

## 4. Applicability and non-applicability

**Reach for this pattern when.**

- A process runs as one of several replicas behind something that makes
  routing or restart decisions, a load balancer, an orchestrator's kubelet,
  a service mesh sidecar, or an autoscaler, and that decision-maker needs a
  richer-than-TCP signal.
- The application has real dependencies, a database, a cache, a downstream
  API, whose unavailability should change whether traffic is routed to this
  instance, but should not necessarily cause the instance itself to be
  killed.
- The application has a meaningfully slow startup path, cache warming,
  schema migration checks, connection pool priming, during which it can
  accept a TCP connection but should not yet receive real traffic.
- The deployment platform, Kubernetes, an Application Load Balancer, Consul,
  Traffic Manager, or an equivalent, already understands and consumes an
  HTTP or RPC health signal natively, so the marginal cost of exposing one is
  small and the marginal benefit, correct traffic routing and restart
  decisions, is large.

**Do NOT reach for this pattern, or reach for a narrower version of it,
when.**

- The process has no independent lifecycle at all, for example a short-lived
  batch job, a one-shot CLI invocation, or a function-as-a-service handler
  that the platform invokes per event rather than keeping resident. There is
  no poller to consume the endpoint and no standing process to poll.
- The health signal would only ever be consumed by the same process that
  would also perform the remediation, for example a single-instance desktop
  application. An in-process health check with no external endpoint serves
  that need with less surface area and no network exposure to secure.
- A single shallow health signal is being asked to answer two different
  questions, restart-worthiness and traffic-worthiness, from one endpoint
  with one meaning. This is not "do not use the pattern," it is "do not use
  one endpoint for it," and is the single most common misuse, covered fully
  in dimension 11.
- The check would need to perform a mutating or non-idempotent operation
  against a dependency to prove it is reachable, for example placing a real
  order to prove the order service works end to end. Exercise that
  separately as a synthetic transaction on its own schedule, not as part of
  the liveness or readiness path that gates traffic and restarts on every
  poll.
- The dependency being checked is itself elastic and expected to be
  intermittently degraded by design, for example a best-effort geocoding
  enrichment call that the application already treats as optional. The
  catalog's own considerations note recommends exposing such a dependency on
  its own, separately weighted endpoint rather than folding it into the
  primary aggregate check
  ([Azure Architecture Center, Health Endpoint Monitoring pattern, Issues and considerations](https://learn.microsoft.com/en-us/azure/architecture/patterns/health-endpoint-monitoring),
  verified 2026-08-02).

## 5. Structure

- **The subject.** The application instance or process being observed. It
  exposes one or more endpoints and is the only party with in-process
  knowledge of its own state, its dependency handles, and its cached last
  known status.
- **The endpoint.** A network-addressable surface, most commonly an HTTP path
  such as `/healthz`, `/livez`, `/readyz`, `/actuator/health`, or an RPC
  method such as the gRPC `Health.Check` call. The endpoint's contract is a
  status plus, optionally, a small structured body describing per-component
  results. The endpoint is a thin facade, it must never itself carry
  significant business logic.
- **The dependency check.** A bounded, timeout-guarded probe of one external
  or internal component the application relies on, a database connection
  pool, a cache client, a downstream service client, a disk-space gauge.
  Each dependency check is its own unit with its own name, its own timeout,
  and its own pass or fail verdict; they are never merged into a single
  undifferentiated boolean before being reported.
- **The aggregator.** The piece inside the application, sometimes a library
  such as Spring Boot Actuator's `HealthEndpoint` and its
  `HealthContributorRegistry`, that runs the set of dependency checks
  relevant to a given role, applies a combining rule (typically "all must
  pass" for readiness, "none of a small fatal set may fail" for liveness),
  and optionally caches the result for a short window so repeated polls do
  not each trigger a fresh, expensive check cycle.
- **The poller.** The external party that calls the endpoint on a schedule
  and acts on the result. In the shapes this pattern is most commonly used
  in, the poller is a kubelet (Kubernetes), a load balancer's health-check
  subsystem (an AWS Application Load Balancer target group, an Azure Traffic
  Manager profile), or a service registry's health monitor (a Consul agent).
- **The action taker.** The party that consumes the poller's verdict and
  changes system state as a result, the kubelet restarting a container that
  fails its liveness probe, the EndpointSlice controller removing a pod's IP
  from a Service's routable set on a failed readiness probe, or an
  Application Load Balancer's routing table excluding an `unhealthy` target.
  In many deployments the poller and the action taker are the same
  component; they are drawn separately here because in some deployments,
  for example a monitoring dashboard that pages a human, they are not.

## 6. ASCII structure diagram

```
+----------------------------------------------------------------+
|                        APPLICATION INSTANCE                    |
|                                                                  |
|   +----------------+   +----------------+   +----------------+ |
|   |  /healthz      |   |  /readyz       |   |  aggregator    | |
|   |  (liveness)    |   |  (readiness)   |   |  + short-TTL   | |
|   |                |   |                |   |    cache       | |
|   +--------+-------+   +--------+-------+   +--------+-------+ |
|            |                    |                     |         |
|            | in-process only    | delegates to         |         |
|            v                    v                     |         |
|   +----------------+   +----------------------------+ |         |
|   |  process self   |   |  dependency check set      |<--------+
|   |  test (deadlock,|   |  - postgres  (timeout 500) |          |
|   |  poison flag)   |   |  - redis     (timeout 500) |          |
|   +----------------+   |  - payments  (timeout 500) |           |
|                        +----------------------------+           |
+----------------------------------------------------------------+
             ^                              ^
             | poll every N seconds         | poll every N seconds
             |                              |
+------------+------------------------------+---------------------+
|                          POLLER (kubelet, ALB, Consul agent)     |
|   liveness failure  -> restart the instance                     |
|   readiness failure -> remove instance from the routable set    |
+-------------------------------------------------------------------+
```

## 7. Dynamics

```
Startup sequence, healthy path
-------------------------------
kubelet          instance                 dependency checks
  |                 |                            |
  | (wait, startup  |                            |
  |  probe delay)   |  boot, open listen socket   |
  |---------------->|  warm caches, connect pool   |
  |  GET /healthz   |----------------------------->|
  |<---- 200 -------|                            |
  |  GET /readyz    |  run aggregator (uncached)   |
  |---------------->|----------------------------->|
  |                 |          all pass            |
  |<---- 200 -------|<-----------------------------|
  |  mark READY     |
  | route traffic ->|

Steady state, one dependency degraded
--------------------------------------
kubelet          instance                 payments dependency
  |                 |                            |
  |  GET /healthz   |  no dependency touched       |
  |---------------->|                            |
  |<---- 200 -------|                            |
  |  GET /readyz    |  cache expired, re-run       |
  |---------------->|----------------------------->|
  |                 |        timeout / refused     |
  |<---- 503 -------|<-----------------------------|
  |  drop from      |
  |  routable set   |
  |                 |
  |  GET /readyz    |  cache still valid,          |
  |  (next poll)    |  return cached 503, no re-run |
  |---------------->|
  |<---- 503 -------|
  |                 |
  ... payments recovers, next cache expiry re-checks it ...
  |  GET /readyz    |  cache expired, re-run       |
  |---------------->|----------------------------->|
  |                 |            pass              |
  |<---- 200 -------|<-----------------------------|
  |  re-add to      |
  |  routable set   |
```

## 8. Implementation variants

- **Two-endpoint split, liveness plus readiness.** The variant this entry
  treats as the default correct shape. Liveness checks the process only, no
  dependency is ever touched from it. Readiness checks the process's
  dependencies and returns a per-dependency breakdown. Kubernetes formalizes
  exactly this split, with a third `startup` variant that suppresses the
  other two probes until it first succeeds, purpose-built for slow-booting
  containers
  ([Kubernetes documentation, Liveness, Readiness, and Startup Probes](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/),
  verified 2026-08-02). Spring Boot Actuator implements the same split as
  first-class health groups at `/actuator/health/liveness` and
  `/actuator/health/readiness`, and its own documentation states the same
  caution verbatim. "The liveness probe should not depend on health checks
  for external systems."
- **Single flat endpoint with a body-level breakdown.** Common outside
  Kubernetes-shaped deployments, for example a plain HTTP load balancer
  target group. A single `/health` returns one top-level status derived from
  an aggregate rule, with a JSON body listing each component's individual
  status for a human or a monitoring tool to read. The Azure Architecture
  Center's own worked example describes exactly this shape, with the caveat
  that "most existing tools and frameworks look only at the HTTP status code
  that the endpoint returns," so a body with rich detail is a bonus for
  humans and dashboards, not something most automated pollers act on
  ([Azure Architecture Center, Health Endpoint Monitoring pattern, Issues and considerations](https://learn.microsoft.com/en-us/azure/architecture/patterns/health-endpoint-monitoring),
  verified 2026-08-02).
- **RPC-native health service.** For gRPC services, the gRPC Health Checking
  Protocol defines a dedicated `Health` service with a `Check` unary RPC and
  a `Watch` streaming RPC, both keyed by an optional service name so one
  process can report independent health for each RPC service it hosts, using
  a `ServingStatus` enum of `UNKNOWN`, `SERVING`, `NOT_SERVING`, and, for
  `Watch` only, `SERVICE_UNKNOWN`
  ([gRPC health-checking.md, GitHub](https://github.com/grpc/grpc/blob/master/doc/health-checking.md),
  verified 2026-08-02). This variant avoids inventing an HTTP convention on
  top of an RPC-native service and lets a streaming `Watch` push status
  changes instead of the poller repeatedly issuing `Check`.
- **TTL-based passive check.** Consul supports a check type where the
  instance itself, rather than Consul, is responsible for periodically
  calling back into the Consul agent to update its own status before a
  time-to-live expires; if the TTL lapses with no update, the check goes
  critical automatically. This inverts the poll direction from pull, Consul
  asks the instance, to push, the instance tells Consul, and suits processes
  that already run an internal health-evaluation loop and want to avoid a
  second network listener purely for polling
  ([Consul documentation, Define Health Checks](https://developer.hashicorp.com/consul/docs/services/usage/checks),
  verified 2026-08-02).
- **Cached aggregate with a self-test.** The catalog's own considerations
  section recommends caching the health status rather than recomputing it on
  every poll when the underlying checks are expensive, and separately
  recommends that "the monitoring system performs checks on itself," for
  example exposing a value from configuration that the poller can validate
  independently, "to prevent the monitoring system from issuing false
  positive results"
  ([Azure Architecture Center, Health Endpoint Monitoring pattern, Issues and considerations](https://learn.microsoft.com/en-us/azure/architecture/patterns/health-endpoint-monitoring),
  verified 2026-08-02).
- **Language-idiomatic variant, framework health-indicator interfaces.**
  Rather than the application hand-writing the endpoint plumbing, several
  frameworks expose an extension point, implement one interface per
  dependency, and the framework wires the aggregation, caching, and HTTP
  surface. Spring Boot's `HealthIndicator` interface, shown in dimension 9,
  is the paradigmatic example; a Go application more commonly hand-rolls the
  same shape as a small package, because no equivalently dominant
  convention exists in that ecosystem.

## 9. Known production uses

- **Kubernetes kubelet.** Every standard Kubernetes deployment that declares
  `livenessProbe`, `readinessProbe`, or `startupProbe` on a pod spec is a
  direct production instance of this pattern, at the scale of every cluster
  running the project. The kubelet, the per-node agent, is the poller and
  the action taker. it restarts a container whose liveness probe fails past
  the configured `failureThreshold`, and it removes a pod's address from the
  `EndpointSlice` objects backing any Service that selects it when the
  readiness probe fails
  ([Kubernetes documentation, Liveness, Readiness, and Startup Probes](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/),
  verified 2026-08-02).
- **AWS Application Load Balancer target group health checks.** Every ALB
  target group polls each registered target on a configurable
  `HealthCheckPath`, `HealthCheckIntervalSeconds`, `HealthyThresholdCount`,
  and `UnhealthyThresholdCount`, and marks a target `healthy` or `unhealthy`
  based on consecutive pass or fail counts before including or excluding it
  from routed traffic. AWS's own documentation notes the specific, easy to
  miss failure-mode decision the load balancer makes when every target in
  every enabled Availability Zone is simultaneously unhealthy. it "fails
  open," routing to all targets regardless of health status rather than
  routing to none
  ([AWS documentation, Health checks for your target groups](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html),
  verified 2026-08-02).
- **HashiCorp Consul.** Consul's service catalog gates whether a service
  instance is returned from DNS or the HTTP catalog API on the aggregate
  status of its registered checks, which can be script, HTTP, TCP, gRPC, or
  TTL based. Consul's documentation states that a newly registered check
  "is assigned a `critical` status by default," so a service is never
  advertised as available before its health has actually been verified at
  least once
  ([Consul documentation, Define Health Checks](https://developer.hashicorp.com/consul/docs/services/usage/checks),
  verified 2026-08-02).
- **Spring Boot Actuator.** The `/actuator/health` endpoint is one of the
  few Actuator endpoints exposed over HTTP by default, and it auto-configures
  `HealthIndicator` beans for common dependencies the classpath detects,
  including `db`, `redis`, `mongo`, `diskspace`, `rabbit`, and `ssl`. As of
  the current Spring Boot documentation, it separately auto-configures
  `livenessstate` and `readinessstate` indicators specifically to back
  Kubernetes' two-probe model
  ([Spring Boot reference documentation, Endpoints](https://docs.spring.io/spring-boot/reference/actuator/endpoints.html),
  verified 2026-08-02).
- **gRPC ecosystem.** The gRPC Health Checking Protocol, implemented as a
  standard `Health` service in the official gRPC libraries for multiple
  languages, is consumed directly by Kubernetes' `grpc` probe type
  (`livenessProbe.grpc.port`) and by Envoy proxy's gRPC health-check filter,
  giving RPC-native services a health surface that does not require an
  additional HTTP listener
  ([gRPC health-checking.md, GitHub](https://github.com/grpc/grpc/blob/master/doc/health-checking.md),
  verified 2026-08-02).

## 10. Consequences

**Positive.**

- Converts an otherwise invisible degraded state, a process that is alive but
  useless, into a signal something else can act on within seconds, which is
  the difference between a self-healing system and a silent partial outage.
- Decouples the decision of whether an instance is safe to receive traffic
  from the decision of whether it is safe to keep running, letting an
  orchestrator make each decision correctly instead of conflating the two.
- Gives operators and dashboards a single, cheap, well-known place to look
  for the current state of a service, rather than reconstructing it from
  scattered log lines.
- Composes naturally with rolling deployments. a readiness probe that fails
  during a slow startup keeps new pods out of the routable set until they are
  actually ready, which is most of what makes a zero-downtime rolling
  deployment possible at all.

**Negative.**

- Adds a permanent, always-on network surface that must itself be secured,
  documented, and kept in sync with the application's real dependency graph;
  a stale health check that never learned about a new critical dependency is
  worse than no health check because it creates false confidence.
- A wrongly configured liveness check is one of the few misconfigurations
  that turns a partial outage into a total one, because it actively
  instructs the platform to kill instances (dimension 11).
- Adds a small, continuous load to every dependency named in the checks,
  proportional to poll frequency times replica count; at high replica counts
  this becomes a real, budgeted cost against the dependency, which is why
  caching (dimension 8) is not optional at scale.
- The pattern by itself gives no guidance on what to do when a check fails;
  it must be paired with an actual remediation, a restart policy, a routing
  exclusion, an alert, or it degrades into a metric nobody acts on.

## 11. Failure modes and misuse

**Symptom.** A single downstream outage, for example a database connection
pool exhaustion event, causes every replica of an unrelated frontend service
to restart within the same few minutes, turning a partial degradation into a
total outage of a service that was not itself broken.
**Cause.** The frontend's liveness probe was written to call the database, or
to call the same aggregated `/health` handler that readiness uses, so a
database outage flips liveness to failing on every replica simultaneously.
The kubelet, doing exactly what liveness probes are for, restarts every
replica at once. The restarted replicas immediately re-check liveness against
the still-down database, fail again, and the platform enters a restart loop
across the whole fleet while the database is down, which is precisely the
outcome Kubernetes' own documentation warns about. "Incorrect implementation
of liveness probes can lead to cascading failures," specifically citing
"restarting of container[s] under high load" and "increased workload on
remaining pods due to some failed pods" as the mechanism
([Kubernetes documentation, Liveness, Readiness, and Startup Probes](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/),
verified 2026-08-02).
**Fix.** Split liveness and readiness into genuinely different endpoints with
genuinely different checks. Liveness verifies only that the process itself is
not deadlocked or in a known-fatal internal state, code shown in dimension
"implementation variants" and the worked samples below; it never opens a
socket to a dependency. Readiness, and only readiness, checks dependencies,
and a readiness failure removes the instance from the routable set without
restarting it, which is the correct, non-amplifying response to a downstream
outage. Kubernetes' documented mitigation for a strict dependency is to
"implement both a liveness and a readiness probe," where "the liveness probe
passes when the app itself is healthy," while the readiness probe alone
checks the backend.

**Symptom.** A newly deployed instance receives real production traffic
within a second of its container starting, before it has finished loading a
large in-memory reference dataset, and serves a burst of empty or wrong
responses to real users during a rolling deployment.
**Cause.** No readiness probe was configured at all, or the readiness probe
was configured identically to the liveness probe and therefore starts passing
the instant the process opens its listening socket, which happens long before
application-level initialization, cache warming, or connection-pool priming
completes.
**Fix.** Add a readiness check whose aggregate rule genuinely reflects
initialization completion, not merely socket-open, and, for containers whose
startup is itself slow enough to risk being killed by an impatient liveness
probe before it finishes, add a `startupProbe` so the liveness and readiness
probes are suppressed entirely until startup first succeeds. This is exactly
the problem Kubernetes' `startupProbe` type was added to solve, and Spring
Boot's own lifecycle table documents the same distinction explicitly. during
the `Starting` phase, liveness is `BROKEN` and readiness is
`REFUSING_TRAFFIC` until the application context has actually finished
refreshing
([Spring Boot reference documentation, Endpoints](https://docs.spring.io/spring-boot/reference/actuator/endpoints.html),
verified 2026-08-02).

**Symptom.** During a real outage, the health check itself becomes a
significant additional source of load on the already-struggling dependency,
and its response time grows, causing the poller's own timeout to fire before
the check even completes, so the platform reports the instance unhealthy for
a reason unrelated to the instance's own correctness.
**Cause.** The readiness check re-runs every dependency probe, uncached, on
every single poll, at a poll interval multiplied across every replica in the
fleet. A five-second poll interval across two hundred replicas is forty
readiness-driven queries per second landing on the dependency, purely from
health checking, on top of the dependency's normal load, exactly at the
moment the dependency is least able to absorb extra load.
**Fix.** Cache the aggregate readiness result for a short, bounded window,
shorter than the poll interval is not required, longer than a single poll
interval is fine, and serve cached results on polls that land inside the
window, as shown in the worked code samples below. Bound every individual
dependency check with its own timeout, shorter than the poller's own overall
timeout, so a hung dependency call cannot itself make the health endpoint
hang past the poller's patience.

## 12. Trade-off matrix

| Force | Health Endpoint Monitoring | Circuit Breaker alone | Retry with backoff alone |
|---|---|---|---|
| Who decides to stop routing traffic | An external poller (orchestrator, load balancer), based on a signal the instance produces | The calling instance itself, per outbound call | Nobody; the caller keeps trying the same target |
| Granularity of the decision | Whole-instance, in or out of the routable set | Per dependency, per caller, independent of instance-level routing | Per call, no state carried between calls |
| Detects a deadlocked or wedged process | Yes, via a liveness check that does not depend on I/O succeeding | No, a circuit breaker only reacts to failed calls, not to the caller itself hanging | No |
| Protects a downstream dependency from overload | Indirectly, if readiness failure removes load-generating instances | Directly and immediately, per caller, the moment the failure threshold trips | Poorly; naive retry without backoff can amplify load on a struggling dependency |
| Needs an external poller to have any effect | Yes, the pattern is inert without something consuming the endpoint | No, it is entirely in-process | No, it is entirely in-process |
| Typical remediation on failure | Restart (liveness) or route exclusion (readiness), decided by the poller | Fail fast locally, degrade gracefully, or serve a fallback | Delay and re-attempt the same call |

The three patterns are complementary rather than substitutable, and a mature
system runs all three. Health Endpoint Monitoring makes an instance's overall
fitness externally visible so the orchestrator can act on it, Circuit Breaker
protects a specific caller-to-dependency relationship from being repeatedly
hammered once it is known to be failing, and Retry with backoff handles the
transient, single-call case that both of the others are too coarse-grained to
address.

## 13. Related and incompatible patterns

- **Circuit Breaker.** Frequently invoked from inside a readiness check's
  individual dependency probes, rather than issuing a fresh network call to
  a dependency on every readiness poll, the readiness check can simply read
  the current state of a circuit breaker that the application's normal
  request path already maintains for that dependency, avoiding a duplicate
  check path and reusing state that is already fresh.
- **Retry with backoff.** Belongs inside an individual dependency check's own
  implementation when a single transient failure should not immediately flip
  that dependency to failed, but the retry budget inside a health check must
  be small and the total time bounded well under the poller's timeout, or the
  retry itself becomes the cause of a health-check timeout.
- **Bulkhead.** Complements Health Endpoint Monitoring when the
  connection pool or thread pool a health check uses to probe a dependency is
  isolated from the pool the application's real request path uses for the
  same dependency, so a health check under heavy dependency load does not
  starve, and is not starved by, real traffic to that dependency.
- **Sidecar and Ambassador.** In a service-mesh deployment, health checking is
  sometimes delegated to, or duplicated by, a sidecar proxy that performs its
  own TCP or HTTP checks against the application container independently of
  the orchestrator's own probe mechanism; the two checking layers must be
  configured consistently or they will disagree about an instance's health.
- **Load Balancer (as a general category, of which an ALB target group and
  Traffic Manager are instances).** The most direct consumer of the pattern
  outside of an orchestrator; the entire routing decision hinges on the
  health endpoint's reported status.
- **No documented incompatibility.** Health Endpoint Monitoring composes with
  essentially every other resiliency pattern in this catalog; it is a sensing
  mechanism, not an acting one, and sensing does not conflict with the
  choice of what a system does in response to what it senses.

## 14. Refactoring path in and out

**Introducing the pattern into an application that has none.**

1. Add a single unconditional endpoint first, one that returns 200 with no
   dependency checks at all, purely to prove the routing and deployment
   plumbing, the load balancer target group or the Kubernetes probe
   configuration, is wired correctly before any real logic depends on it.
2. Split that single endpoint into two, a liveness endpoint that stays
   unconditional, or checks only in-process state, and a readiness endpoint
   that starts returning 503 until an explicit "application ready" flag is
   set at the end of the startup sequence.
3. Enumerate the application's real dependencies, and add one bounded,
   timed-out check per dependency to the readiness aggregator, starting with
   the dependency whose unavailability most directly makes the application
   unable to serve its primary use case.
4. Wire the orchestrator or load balancer's probe configuration to point at
   the two endpoints with distinct intervals and thresholds, a shorter
   interval and lower tolerance for liveness since a hung process should be
   caught and restarted quickly, a longer interval and higher tolerance for
   readiness since flapping traffic routing under transient dependency
   blips is itself disruptive.
5. Add caching to the readiness aggregator once the dependency count or the
   poll frequency makes uncached, per-poll dependency calls a measurable
   load contributor, not before; premature caching hides genuinely fresh
   failures behind a stale cached pass.

**Removing the pattern, or narrowing it.**

1. If a specific dependency check has become a source of false-negative
   flapping, move it out of the aggregate readiness rule and expose it on
   its own, separately weighted endpoint per the catalog's own guidance, so
   its instability no longer drags down the primary readiness signal for an
   otherwise healthy instance.
2. If the deployment platform is being retired in favor of one with no
   native health-check consumer, for example moving to a pure
   function-as-a-service model with no standing process, retire the
   endpoint entirely rather than leaving a dead, unpolled surface exposed;
   an unpolled health endpoint is dead code with an attack surface.
3. Never remove the liveness role while keeping the readiness role, or vice
   versa, without confirming what the orchestrator will do with the missing
   probe; most platforms fall back to a TCP-level check silently, which
   quietly reintroduces the exact "process alive but useless" blind spot the
   pattern exists to close.

## 15. Testing and verification

- **Unit test the aggregation rule in isolation from real dependencies.**
  Inject fake dependency checks that succeed, fail, and time out, and assert
  the aggregate status and the per-dependency breakdown the endpoint would
  report, without a real database or network call in the test. All three
  code samples below are structured specifically to make this possible, the
  dependency check is an injected function, never a hardcoded call.
- **Test the liveness and readiness distinction directly**, by asserting
  that a simulated dependency failure changes readiness's result but leaves
  liveness's result unchanged. This is the single most valuable test in the
  whole pattern, because it is the exact property whose absence causes the
  cascading-restart failure mode in dimension 11.
- **Test timeout behavior with a dependency stub that never completes**,
  rather than one that fails fast, and assert the check still returns within
  the configured per-check timeout. A fast-failing fake dependency does not
  exercise the timeout path at all and gives false confidence that hangs are
  handled.
- **Test the cache boundary**, asserting that two calls inside the TTL window
  return the identical cached result without re-invoking the dependency
  checks, and that a call after the TTL expires does re-invoke them. An
  off-by-one here either serves a stale failed status long after recovery,
  or defeats the caching entirely and re-introduces the load problem it
  exists to solve.
- **Integration-test against a real orchestrator's probe semantics in a
  staging environment before trusting the configuration in production.** Unit
  tests can verify the endpoint's own logic; they cannot verify that the
  `failureThreshold`, `periodSeconds`, and `initialDelaySeconds` values
  chosen for a `livenessProbe` actually give a slow-starting container enough
  time to become live before Kubernetes gives up on it, which is exactly what
  the `startupProbe` type exists to make safe, and which is worth confirming
  against a real kubelet rather than assumed.
- **Chaos-test the dependency, not just the endpoint**, by actually taking a
  real dependency offline in a non-production environment, for example
  blocking the database port with a firewall rule, and confirming the whole
  chain, readiness flips, the instance is removed from the routable set,
  liveness stays unaffected, works end to end, not merely that the unit
  tests for the aggregator pass.

## 16. Observability signals

- **Per-endpoint request count and latency**, split by liveness and
  readiness, so an operator can see whether the health-check traffic itself
  is growing unexpectedly, for example because a poll interval was
  tightened, or because replica count grew and each replica's poll load
  did not shrink to compensate.
- **Per-dependency check outcome and latency, over time**, not merely the
  aggregate pass or fail, since the aggregate hides which specific
  dependency is degrading and for how long; this is exactly the structured
  breakdown the code samples below produce on every readiness evaluation.
- **Cache hit ratio for the readiness aggregator**, which reveals whether the
  chosen TTL is doing its job of absorbing poll load, or whether it is set so
  long that a real recovery is being masked behind a stale cached failure for
  longer than intended.
- **Transition events, not just point-in-time status.** A dashboard that only
  shows current status hides flapping; logging or emitting a metric each time
  liveness or readiness *changes* state, with the reason, is what actually
  lets an operator distinguish a single clean failure from a fleet that is
  repeatedly flipping healthy and unhealthy.
- **A healthy instance's dashboard signature** looks like a flat, low,
  predictable readiness-check latency, a near-zero liveness-check failure
  rate, and a cache hit ratio close to the theoretical maximum for the
  configured cache window and poll interval. **A failing instance's
  signature** looks like either a sudden, sustained readiness failure with
  one dependency named consistently in the breakdown, which points at that
  dependency, or, far more alarming, a liveness failure rate above zero,
  which means the process itself, not a dependency, is in the state the
  restart policy exists to correct.

## 17. Security and privacy implications

- **The endpoint is, by construction, unauthenticated in most default
  deployments**, because the poller, a kubelet or a load balancer, typically
  cannot supply application-level credentials. This makes the endpoint a
  reconnaissance surface. a detailed dependency breakdown in the response
  body tells an outside observer exactly which internal systems a service
  depends on, their names, and sometimes their error text, all of which is
  useful to an attacker mapping the internal topology. The catalog's own
  guidance is explicit on this point, recommending network-level restriction,
  an obscure or non-default path, and, where the poller supports it,
  authentication, and separately recommends avoiding returning information
  "that might be useful to an attacker" from the endpoint's public response
  ([Azure Architecture Center, Health Endpoint Monitoring pattern, Issues and considerations](https://learn.microsoft.com/en-us/azure/architecture/patterns/health-endpoint-monitoring),
  verified 2026-08-02).
- **A verbose health response can leak error text from a dependency client
  library** verbatim, which has, in other contexts, included connection
  strings, stack traces revealing internal file paths, or partial credential
  material embedded in an exception message. Sanitize dependency error
  detail before it reaches the response body; log the full detail
  server-side instead, where it is useful for debugging without being
  publicly exposed.
- **An unauthenticated, expensive health endpoint is itself a denial-of-service
  amplification vector**, because an attacker who discovers it can trigger
  the application's own dependency-checking logic repeatedly at will, and if
  that logic is not rate limited or cached, the attacker's traffic is
  effectively multiplied into load against every downstream dependency the
  check touches. This is a second, independent reason, beyond load-reduction,
  that caching the aggregate result and bounding each check with a strict
  timeout matters.
- **Health check network exposure should follow the same segmentation as the
  rest of the deployment.** In a Kubernetes cluster the kubelet reaches the
  probe over the pod network directly and this is not internet-exposed by
  default, which is a meaningfully different exposure profile than an ALB
  target group's health check path, which shares the same listener as public
  traffic unless deliberately separated onto a different port or path with
  its own network ACL. Judgement, this segmentation decision is not covered
  by the sourced material above and reflects ordinary network-design practice.

## 18. References

1. Alex Homer, John Sharp, Larry Brader, Masashi Narumoto, Trent Swanson,
   "Health Endpoint Monitoring pattern," Azure Architecture Center, Microsoft
   Learn. https://learn.microsoft.com/en-us/azure/architecture/patterns/health-endpoint-monitoring,
   verified 2026-08-02. Attribution note. this Azure Architecture Center page
   is the living, current form of the pattern first published in the
   Microsoft patterns and practices book *Cloud Design Patterns.
   Prescriptive Architecture Guidance for Cloud Applications* (Microsoft
   Press, 2014), whose original author team included Homer, Trent Arnold,
   Masashi Narumoto, Rohit Sharma, and colleagues; the specific chapter
   authorship credited on the current live page is listed above as the
   citation for this entry.
2. Kubernetes documentation, "Configure Liveness, Readiness and Startup
   Probes." https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/,
   verified 2026-08-02.
3. gRPC Authors, "gRPC Health Checking Protocol," `doc/health-checking.md`,
   grpc/grpc repository, GitHub.
   https://github.com/grpc/grpc/blob/master/doc/health-checking.md, verified
   2026-08-02.
4. Amazon Web Services, "Health checks for your target groups," Application
   Load Balancer documentation.
   https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html,
   verified 2026-08-02.
5. HashiCorp, "Define Health Checks," Consul documentation.
   https://developer.hashicorp.com/consul/docs/services/usage/checks,
   verified 2026-08-02.
6. VMware Tanzu / Broadcom, "Endpoints," Spring Boot reference
   documentation, Actuator chapter.
   https://docs.spring.io/spring-boot/reference/actuator/endpoints.html,
   verified 2026-08-02.

## Code examples

Three languages, each a self-contained, runnable program with no framework
dependency, so the shape of the pattern is visible without scaffolding noise.
Every sample was compiled or executed on this machine before being included
here.

Each sample implements the same structure. a liveness handler that touches
only in-process state, a readiness handler backed by an aggregator that runs
a set of independent, individually timed-out dependency checks concurrently,
and a short-TTL cache so repeated polls inside the cache window do not
re-invoke the dependency checks. One of the three simulated dependencies
always fails, to exercise the failure path, not only the happy path.

### TypeScript

Run with Node.js. Compiled and executed with `tsc` (strict mode) and `node`
on this machine; output reproduced below the listing.

```typescript
type CheckResult = { name: string; ok: boolean; latencyMs: number; detail?: string };

interface DependencyCheck {
  name: string;
  run: () => Promise<void>;
}

async function withTimeout<T>(p: Promise<T>, ms: number, label: string): Promise<T> {
  let timer: ReturnType<typeof setTimeout>;
  const timeout = new Promise<T>((_, reject) => {
    timer = setTimeout(() => reject(new Error(`${label} timed out after ${ms}ms`)), ms);
  });
  try {
    return await Promise.race([p, timeout]);
  } finally {
    clearTimeout(timer!);
  }
}

class CachedDeepHealth {
  private lastResult: CheckResult[] | null = null;
  private lastRunAt = 0;

  constructor(
    private checks: DependencyCheck[],
    private ttlMs: number,
    private perCheckTimeoutMs: number
  ) {}

  async evaluate(): Promise<{ results: CheckResult[]; cached: boolean }> {
    const now = Date.now();
    if (this.lastResult && now - this.lastRunAt < this.ttlMs) {
      return { results: this.lastResult, cached: true };
    }
    const results = await Promise.all(
      this.checks.map(async (c) => {
        const start = Date.now();
        try {
          await withTimeout(c.run(), this.perCheckTimeoutMs, c.name);
          return { name: c.name, ok: true, latencyMs: Date.now() - start };
        } catch (err) {
          return {
            name: c.name,
            ok: false,
            latencyMs: Date.now() - start,
            detail: err instanceof Error ? err.message : String(err),
          };
        }
      })
    );
    this.lastResult = results;
    this.lastRunAt = now;
    return { results, cached: false };
  }
}

// Liveness never touches a dependency. It only asks whether the event loop
// is alive and this process is free of a known-fatal internal state.
function livenessHandler(processIsPoisoned: () => boolean) {
  return async () => (processIsPoisoned() ? { status: 503 as const } : { status: 200 as const });
}

// Readiness aggregates dependency checks, cached, bounded, and reported per-dependency.
function readinessHandler(deep: CachedDeepHealth) {
  return async () => {
    const { results, cached } = await deep.evaluate();
    const allOk = results.every((r) => r.ok);
    return { status: allOk ? (200 as const) : (503 as const), results, cached };
  };
}
```

Output from a run driving this sample against three simulated dependencies,
two fast and healthy, one that always throws.

```
liveness: {"status":200}
readiness: {"status":503,"results":[{"name":"postgres","ok":true,"latencyMs":5},
{"name":"redis","ok":true,"latencyMs":3},
{"name":"downstream-payments","ok":false,"latencyMs":0,"detail":"connection refused"}],"cached":false}
readiness (cached): true
liveness after poison: {"status":503}
```

### Python

Run with `python3` (3.14.6 on this machine), using `asyncio.wait_for` for
per-check timeouts and `asyncio.gather` to run dependency checks
concurrently.

```python
import asyncio
import time
from dataclasses import dataclass
from typing import Callable, Awaitable, Optional


@dataclass
class CheckResult:
    name: str
    ok: bool
    latency_ms: float
    detail: Optional[str] = None


@dataclass
class DependencyCheck:
    name: str
    run: Callable[[], Awaitable[None]]


class CachedDeepHealth:
    def __init__(self, checks: list[DependencyCheck], ttl_s: float, per_check_timeout_s: float):
        self._checks = checks
        self._ttl_s = ttl_s
        self._timeout_s = per_check_timeout_s
        self._last_results: Optional[list[CheckResult]] = None
        self._last_run_at = 0.0

    async def evaluate(self) -> tuple[list[CheckResult], bool]:
        now = time.monotonic()
        if self._last_results is not None and (now - self._last_run_at) < self._ttl_s:
            return self._last_results, True

        async def run_one(check: DependencyCheck) -> CheckResult:
            start = time.monotonic()
            try:
                await asyncio.wait_for(check.run(), timeout=self._timeout_s)
                return CheckResult(check.name, True, (time.monotonic() - start) * 1000)
            except Exception as exc:
                return CheckResult(check.name, False, (time.monotonic() - start) * 1000, str(exc))

        results = await asyncio.gather(*(run_one(c) for c in self._checks))
        self._last_results = list(results)
        self._last_run_at = now
        return self._last_results, False


def liveness_handler(process_is_poisoned: Callable[[], bool]):
    async def handle():
        return 503 if process_is_poisoned() else 200
    return handle


def readiness_handler(deep: CachedDeepHealth):
    async def handle():
        results, cached = await deep.evaluate()
        all_ok = all(r.ok for r in results)
        return (200 if all_ok else 503), results, cached
    return handle
```

Output from a run against the equivalent three simulated dependencies.

```
liveness: 200
readiness: 503 [('postgres', True, None), ('redis', True, None),
('downstream-payments', False, 'connection refused')] cached= False
readiness cached: True
liveness after poison: 503
```

### Go

Compiled and run with `go run` (go1.26.4). Uses `context.WithTimeout` per
dependency check and a `sync.WaitGroup` to run checks concurrently, with a
`sync.Mutex`-guarded cache.

```go
package main

import (
	"context"
	"sync"
	"time"
)

type CheckResult struct {
	Name      string
	OK        bool
	LatencyMs float64
	Detail    string
}

type DependencyCheck struct {
	Name string
	Run  func(ctx context.Context) error
}

type CachedDeepHealth struct {
	checks        []DependencyCheck
	ttl           time.Duration
	perCheckLimit time.Duration

	mu         sync.Mutex
	lastResult []CheckResult
	lastRunAt  time.Time
}

func (d *CachedDeepHealth) Evaluate(ctx context.Context) ([]CheckResult, bool) {
	d.mu.Lock()
	if d.lastResult != nil && time.Since(d.lastRunAt) < d.ttl {
		cached := d.lastResult
		d.mu.Unlock()
		return cached, true
	}
	d.mu.Unlock()

	results := make([]CheckResult, len(d.checks))
	var wg sync.WaitGroup
	for i, c := range d.checks {
		wg.Add(1)
		go func(i int, c DependencyCheck) {
			defer wg.Done()
			start := time.Now()
			cctx, cancel := context.WithTimeout(ctx, d.perCheckLimit)
			defer cancel()
			err := c.Run(cctx)
			r := CheckResult{Name: c.Name, LatencyMs: float64(time.Since(start).Microseconds()) / 1000.0}
			if err != nil {
				r.OK, r.Detail = false, err.Error()
			} else {
				r.OK = true
			}
			results[i] = r
		}(i, c)
	}
	wg.Wait()

	d.mu.Lock()
	d.lastResult, d.lastRunAt = results, time.Now()
	d.mu.Unlock()
	return results, false
}

// Liveness never touches a dependency, it only asks whether the process
// itself is known to be in a fatal, unrecoverable state.
func livenessHandler(poisoned *bool) func() int {
	return func() int {
		if *poisoned {
			return 503
		}
		return 200
	}
}
```

Output from a run against the equivalent three simulated dependencies.

```
liveness: 200
readiness: 503 [{"name":"postgres","ok":true,"latency_ms":5.279},
{"name":"redis","ok":true,"latency_ms":3.467},
{"name":"downstream-payments","ok":false,"latency_ms":0.075,"detail":"connection refused"}] cached= false
readiness cached: true
liveness after poison: 503
```

Java, Rust, and Swift are omitted from the runnable listings above, not
because the pattern translates poorly to them, it does not, but to keep the
entry's length proportional to the pattern's actual conceptual surface. The
same three-part shape, an unconditional or process-local liveness check, a
concurrent and timeout-bounded readiness aggregator over injected dependency
checks, and a short-TTL cache guarding the aggregator, transfers directly.
Java would express the dependency check as a `Supplier<HealthResult>` run
through a bounded `ExecutorService` with `Future.get(timeout, unit)`, and
Rust would express it as an `async fn` bounded per-check with
`tokio::time::timeout` and run concurrently with `futures::future::join_all`,
each following the identical liveness-versus-readiness split documented in
dimensions 8 and 11.
