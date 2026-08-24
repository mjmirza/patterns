---
name: Health Endpoint Monitoring
slug: health-endpoint-monitoring
family: 08-cloud-distributed
category: Reliability
aliases: [Health Check Pattern, Health Probe, Liveness and Readiness Probes]
first_described: "Microsoft patterns and practices group, Cloud Design Patterns, January 2014"
maturity: canonical
related: [circuit-breaker, retry, bulkhead, throttling, leader-election]
incompatible_with: []
verified: 2026-08-02
---

# Health Endpoint Monitoring

## 1. Name, aliases, and lineage

The canonical name in the pattern literature is Health Endpoint Monitoring. It was
catalogued by the Microsoft patterns and practices group in the guide *Cloud Design
Patterns, Prescriptive Architecture Guidance for Cloud Applications*, published
January 2014, and it remains listed under that name in the current Azure
Architecture Center pattern catalog, categorized under the Reliability,
Operational Excellence, and Performance Efficiency pillars of the Azure
Well-Architected Framework
([learn.microsoft.com, Health Endpoint Monitoring pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/health-endpoint-monitoring),
verified 2026-08-02;
[learn.microsoft.com, archived Cloud Design Patterns guide, January 2014](https://learn.microsoft.com/en-us/previous-versions/msp-n-p/dn568099(v=pandp.10)),
verified 2026-08-02).

Two aliases are in wide day-to-day use, and neither one is a synonym for the
whole pattern, only for one half of it. **Health Check** is the generic industry
term used by container orchestrators, load balancers, and service meshes for
any endpoint or command that reports a component's operational state, a term
that appears throughout the Kubernetes probe documentation and the Docker
`HEALTHCHECK` instruction reference, both cited below. **Liveness and
Readiness Probes** is the Kubernetes-specific vocabulary for two of the
distinct checks the pattern composes. A liveness probe asks whether this
process should be restarted. A readiness probe asks whether this process
should receive traffic right now
([kubernetes.io, Configure Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/),
verified 2026-08-02).

Health Endpoint Monitoring is not one check. It is a family of checks, exposed
through one or more endpoints, each answering a different question about the
same running instance. Conflating the questions is the single most common
mistake made when implementing this pattern, and most of the failure modes in
dimension 11 trace back to exactly that conflation. The pattern is older than
Kubernetes and older than the cloud load balancer. Any networked service that
another process must route around when it fails needs some signal that says
route around me, and the shape of that signal, an inexpensive endpoint an
external caller can poll on an interval, has stayed stable since the earliest
load-balanced web farms of the late 1990s, even though the catalogued name for
it dates only to 2014.

## 2. Problem and context

A service running behind a load balancer, an orchestrator, or a service mesh
can fail in ways that are invisible from outside the process. The operating
system reports the process as running. The port is open and accepting TCP
connections. Yet the process cannot do useful work, because its database
connection pool is exhausted, its downstream dependency is unreachable, its
disk is full, or a background thread has deadlocked while the request-handling
threads carry on accepting connections that will never complete. A caller
routing traffic to that instance sees timeouts or errors, and because the
process itself never crashed, nothing outside the process notices until a
person is paged.

The context that creates this problem is distributed by nature. Once an
application is decomposed into multiple instances behind a router, or into
multiple services calling one another over a network, no single observer has
a full view of every instance's internal state. The router that decides where
to send the next request needs a cheap, frequent, external signal it can act
on in milliseconds, because it cannot wait for a person to read a dashboard
before it stops sending traffic to a broken instance. At the same time, the
process supervisor that decides whether to restart a stuck process needs a
different signal, because restarting a healthy process that is merely
overloaded, or restarting a process whose only fault is a temporarily
unreachable dependency, makes an outage worse rather than better. Cloud-hosted
services add a further wrinkle. The platform vendor controls the network
path, the storage layer, and often the compute layer underneath the
application, so an instance can look correct in every way the application
controls and still be unreachable because of a fault in a layer the
application does not control
([learn.microsoft.com, Health Endpoint Monitoring pattern, Context and
problem section](https://learn.microsoft.com/en-us/azure/architecture/patterns/health-endpoint-monitoring),
verified 2026-08-02).

The problem, stated plainly, is that health is not visible from the outside
unless the application says so, on purpose, through an interface built for
that purpose, and a single yes-or-no answer to are you healthy is the wrong
shape for the several different consumers who each need a different answer.

## 3. Forces

**Cost of checking versus cost of not checking.** A check that queries a real
database, calls a real downstream service, or reads from disk costs CPU time,
network round trips, and connection pool slots on every poll. Running that
check every few seconds across every instance in a large fleet adds real,
continuous load. Not running a real check, and instead returning a bare
process-alive signal, costs nothing at check time but leaves the router
blind to the exact failures the pattern exists to catch. The pattern always
sits somewhere on this line, and where it sits should be a conscious choice
per endpoint rather than an accident of what was easiest to write.

**Speed of detection versus stability of the fleet.** A short check interval
and a low failure threshold detect a broken instance in seconds. The same
settings also mean a single slow garbage-collection pause or one dropped
packet can pull a perfectly healthy instance out of rotation, and if every
instance in a fleet is under the same transient load at once, an aggressive
threshold can pull the whole fleet out of rotation simultaneously, which is
strictly worse than doing nothing. A longer interval and a higher consecutive-
failure threshold survive noise better and detect real failures more slowly.

**Isolation of the check from the failure it detects.** The check runs inside
the same process, on the same host, sharing the same thread pool, connection
pool, and memory as the workload it is meant to report on. A check that
shares a resource with the failure mode it is supposed to catch can itself
be starved by that failure, so the very moment the process most needs to
report itself unhealthy is the moment the health-check code path is least
likely to run promptly.

**Simplicity of a single answer versus the several different questions
callers actually ask.** A load balancer asks whether it should send this
instance a request right now. An orchestrator asks whether it should restart
this process. A dashboard asks whether anything is about to break. A
dependency graph tool asks which of its downstream services is currently
degraded, and why. One endpoint returning one boolean cannot answer all four
questions correctly at once, but building and maintaining four separate
endpoints, each with its own check logic and its own consumer, is real
ongoing engineering cost that grows with the size of the dependency graph.

**Security exposure versus operability.** The endpoint that reports the most
useful diagnostic detail, database latency, queue depth, downstream error
rates, is also the endpoint most useful to an attacker mapping the internal
topology of the system. Locking the endpoint down with authentication limits
who can read it, but also limits which automated tools, some of which cannot
easily be configured to authenticate, can act on it.

## 4. Applicability and non-applicability

Reach for Health Endpoint Monitoring when.

- A load balancer, reverse proxy, or service mesh routes traffic across
  more than one instance of a service, and traffic needs to route around an
  instance that cannot serve it correctly.
- A process supervisor or container orchestrator needs a signal to decide
  whether a stuck process should be restarted, separate from whether it
  should currently receive traffic.
- The application depends on one or more external resources, a database, a
  cache, a message queue, another internal service, whose unavailability
  should change how the platform treats this instance.
- An external uptime monitor, synthetic transaction tool, or alerting system
  needs a stable, low-cost way to confirm the service is up from outside the
  data center, independent of the platform's own internal health signals
  ([learn.microsoft.com, Health Endpoint Monitoring pattern, When to use this
  pattern section](https://learn.microsoft.com/en-us/azure/architecture/patterns/health-endpoint-monitoring),
  verified 2026-08-02).
- A service starts slowly, for example because it warms a cache or loads a
  large model into memory, and a naive liveness check would restart it
  before it ever finishes starting.

Do NOT reach for Health Endpoint Monitoring, or reach for it very
differently than the default shape, when.

- The service is a single-instance batch job or a one-shot script with no
  router deciding where to send traffic and no supervisor deciding whether
  to restart it mid-run. There is no consumer for the signal, so the
  endpoint is pure overhead.
- The health signal would need to reflect business-level correctness, for
  example whether last night's batch reconciliation actually balanced,
  rather than operational availability. That is a monitoring and alerting
  concern with its own instrumentation, not a router-facing yes-or-no
  endpoint, and folding it into the same check conflates two different
  audiences the way dimension 3 warns against.
- The check itself would need to perform a write, a state-changing side
  effect, or a call that is not safe to run repeatedly and concurrently
  from multiple callers on a short interval. A health check must be a pure,
  cheap, idempotent read, and a dependency that cannot offer one should not
  be probed directly. Probe a cached proxy for it instead.
- The team cannot commit to keeping the check honest as the system changes.
  A stale health check that always answers healthy is worse than no check
  at all, because it actively misleads every consumer that trusts it, and a
  team that will not maintain it should not ship it.
- The service already sits behind a platform-managed health mechanism that
  fully covers the need, for example a fully managed serverless function
  whose platform already handles instance replacement transparently. Adding
  an application-level check on top gains little and adds a second thing to
  keep correct.

## 5. Structure

- **Health endpoint.** A route or command, `GET /healthz` or an equivalent,
  exposed by the running instance. It is the interface, not the logic.
- **Check.** A single, focused test of one fact. A check either passes,
  fails, or times out. A check never performs a write and never blocks
  indefinitely, so it always runs against an explicit timeout.
- **Check registry.** The list of checks a given endpoint runs, together
  with each check's timeout and whether that check's failure should count
  toward liveness, readiness, or an informational status report only.
- **Aggregator.** The logic that reduces the individual check results into
  the one status the endpoint returns. A simple aggregator is a logical AND
  across a fixed list. A more capable aggregator can weight checks
  differently, so a low-priority dependency's failure degrades the status
  without taking the whole instance out of rotation.
- **Cache or poller.** An optional component that runs the checks on a
  background interval and serves the cached result to each incoming
  request, so the request path never pays the cost, or the latency risk, of
  a live dependency call.
- **Consumer.** The external actor that polls the endpoint and acts on the
  result. Typical consumers are a load balancer's health-check subsystem, a
  container orchestrator's probe runner, a service mesh sidecar, and an
  external synthetic-monitoring tool. Each consumer type wants a different
  question answered, which is why a mature implementation exposes more than
  one endpoint rather than one shared endpoint serving every consumer.

## 6. ASCII structure diagram

```
+---------------------------------------------+
| Load Balancer / Orchestrator / Service Mesh |
+---------------------------------------------+
           | poll
           v
+-----------------+
| Health Endpoint |
| /healthz/ready  |
| /healthz/live   |
+-----------------+
           | 200/503, returned to caller above
           v
           | reads cached snapshot
           v
+-------------------------------------+
| Aggregator                          |
| AND over checks, or weighted status |
+-------------------------------------+
           ^
           | writes snapshot
           |
+---------------------+
| Poller (background) |
| runs on interval N  |
+---------------------+
           |
     +-----+-----+-----+
     |           |     |
+------------------+ +------------------+ +------------------+
| Check DB         | | Check Cache      | | Check Message    |
| ping, timeout    | | ping, timeout    | | queue reachable  |
+------------------+ +------------------+ +------------------+
```

## 7. Dynamics

The pattern has two distinct dynamics, and confusing them is the source of
most production incidents attributed to this pattern.

The first dynamic is the poll-and-cache loop, running on the instance's own
schedule, decoupled from any inbound request. On a fixed interval, the
poller runs every registered check with its own timeout, collects the
results, and writes a snapshot that later requests will read. This loop
never runs inside the request path. It is the reason a health endpoint can
answer in single-digit milliseconds even when one of its dependencies is
timing out.

The second dynamic is the request-response exchange between a consumer and
the endpoint, which reads the most recent snapshot and returns it, adding a
staleness check so a poller that has itself stalled is reported honestly
rather than silently serving an old, possibly stale, healthy result forever.

```
Poller thread                Snapshot store            Endpoint handler
     |                             |                          |
     | run check 1..N (parallel,   |                          |
     | each with its own timeout)  |                          |
     |----------------------------.|                          |
     |                             |                          |
     | aggregate results           |                          |
     |---------------------------->| write {ok, results, ts}  |
     |                             |                          |
     | sleep(interval)             |                          |
     |----------------------------.|                          |
     |                             |                          |

Load balancer                                     Endpoint handler
     |  GET /healthz/ready                             |
     |------------------------------------------------>|
     |                                                  | read snapshot
     |                                                  | if now - ts > staleness
     |                                                  |   return 503 unknown
     |                                                  | else
     |                                                  |   return 200 or 503
     |<-------------------------------------------------|
     |  200 OK  or  503 Service Unavailable            |
```

For the liveness question specifically, the dynamic collapses to almost
nothing. A liveness handler typically does not consult the poller at all. It
returns 200 the instant the process can schedule and run the handler code,
because the only fact liveness is meant to confirm is that the process is
not deadlocked or wedged. Adding dependency checks to the liveness path
reintroduces the exact coupling the split was meant to remove, and the
Kubernetes documentation is explicit that a liveness probe exists to catch a
process that has transitioned to a broken state and cannot recover except by
restart, a narrower question than readiness answers
([kubernetes.io, Configure Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/),
verified 2026-08-02).

## 8. Implementation variants

**Shallow process check.** The endpoint returns 200 the instant the HTTP
listener can accept the connection and route to the handler, with no
dependency logic at all. This is the correct shape for a liveness probe and
the wrong shape for readiness, because a process can accept connections
while every dependency it needs is unreachable.

**Deep synchronous check, no cache.** The handler calls every dependency
directly, in the request path, on every poll. This is the simplest variant
to write and the most dangerous to run at scale, because it multiplies the
polling interval and fleet size directly into load on shared dependencies,
and a slow dependency turns into a slow, or hanging, health endpoint,
exactly the anti-pattern described in dimension 11.

**Deep check with a background poller and cache.** The variant built in the
code examples for this entry. A background loop runs the deep checks on a
fixed interval and stores the result, and the request handler only reads the
cached value. The Azure Architecture Center guidance names this directly as
a mitigation, stating plainly, "Consider caching the endpoint status. Running
the health check frequently might be expensive."
([learn.microsoft.com, Health Endpoint Monitoring pattern, Issues and
considerations section](https://learn.microsoft.com/en-us/azure/architecture/patterns/health-endpoint-monitoring),
verified 2026-08-02), then recommends running a periodic system-health check
and exposing an endpoint that serves the cached result.

**Threshold-debounced status.** Rather than trusting a single raw pass or
fail, the aggregator only flips the reported status after N consecutive
identical results. The AWS Application Load Balancer implements exactly
this shape at the infrastructure layer, with a default of 2 consecutive
failed checks, its `UnhealthyThresholdCount`, to mark a target unhealthy and
5 consecutive successes, its `HealthyThresholdCount`, to mark it healthy
again, each check on a default 30-second interval with a default 5-second
timeout
([docs.aws.amazon.com, Health checks for your target groups](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html),
verified 2026-08-02). Applying the same debounce inside the application, not
only at the load balancer, protects readiness state from flapping on a
single noisy check even when the load balancer sits multiple hops away or
the platform's own debounce settings are out of the application's control.

**Weighted or tiered checks.** Not every dependency deserves equal say over
readiness. A tiered aggregator marks some checks as hard blockers, for
example the primary database, and others as soft signals that degrade a
status field without pulling the instance out of rotation, for example an
optional recommendations service. The Azure guidance recommends exposing
separate endpoints, or at minimum separate status granularity, for core
services versus lower-priority services for exactly this reason
([learn.microsoft.com, Health Endpoint Monitoring pattern, Issues and
considerations section](https://learn.microsoft.com/en-us/azure/architecture/patterns/health-endpoint-monitoring),
verified 2026-08-02).

**Framework-provided health groups.** Spring Boot Actuator ships a
`/actuator/health` endpoint composed from `HealthContributor` beans, with
two purpose-built groups, `/actuator/health/liveness` backed by a
`LivenessStateHealthIndicator` and `/actuator/health/readiness` backed by a
`ReadinessStateHealthIndicator`, both enabled by default and documented as
the direct mapping onto Kubernetes `livenessProbe` and `readinessProbe`
configuration
([docs.spring.io, Endpoints reference, health endpoint and Kubernetes
probes](https://docs.spring.io/spring-boot/reference/actuator/endpoints.html),
verified 2026-08-02). This is the pattern implemented once, inside a widely
used framework, so every application built on that framework inherits a
correct split between the two questions without writing the split by hand.

**Container-runtime health check.** Docker's `HEALTHCHECK` Dockerfile
instruction runs a command inside the container itself on an interval, and
reports the container's status as healthy, unhealthy, or starting based on
the command's exit code and a configurable retry count, entirely
independent of any HTTP endpoint
([docs.docker.com, Dockerfile reference, the HEALTHCHECK instruction](https://docs.docker.com/reference/dockerfile/#healthcheck),
verified 2026-08-02). This variant is useful when the process being checked
does not, or cannot, speak HTTP, and it demonstrates that the pattern's
shape, a cheap periodic probe with a debounced status, is not tied to any
one transport.

**Passive check via instrumentation instead of an active probe.** Rather
than exposing an endpoint a caller polls, the instance emits health-relevant
metrics continuously, error rate, queue depth, saturation, and an external
system derives a health verdict from the metric stream. This trades a
simple pull model for a richer, but more infrastructure-dependent, push
model, and is common in service meshes that already collect per-request
success and latency data from every call.

## 9. Known production uses

**Kubernetes.** Every pod-based deployment on Kubernetes can declare three
distinct probe types on each container, a liveness probe that triggers a
restart when it fails, a readiness probe that removes the pod from a
Service's endpoint list when it fails without restarting the container, and
a startup probe that suppresses the other two probes until a slow-starting
application reports itself started, specifically so that a long
initialization phase is not mistaken for a liveness failure
([kubernetes.io, Configure Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/),
verified 2026-08-02). This is the single most widely deployed instance of
the pattern in current production infrastructure, because it is built into
the default deployment path for containerized workloads on the platform.

**AWS Application Load Balancer.** Every target group registered behind an
Application Load Balancer is health-checked on a configurable interval,
protocol, path, and response-code matcher, with the healthy and unhealthy
transitions gated by consecutive-result thresholds rather than a single
poll. AWS also documents an explicit fail-open behavior. If every target in
every enabled Availability Zone is simultaneously unhealthy, the load
balancer routes to all of them anyway rather than accepting total traffic
loss
([docs.aws.amazon.com, Health checks for your target groups](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html),
verified 2026-08-02).

**Spring Boot Actuator.** As described in dimension 8, Actuator ships the
liveness and readiness split as first-class, separately addressable
endpoints, wired directly to Kubernetes probe configuration in Spring's own
documentation
([docs.spring.io, Endpoints reference](https://docs.spring.io/spring-boot/reference/actuator/endpoints.html),
verified 2026-08-02). Given how widely Spring Boot is deployed for
enterprise Java services, this is a second concrete, large-scale instance of
the pattern shipped inside a framework rather than hand-built per service.

**Docker.** The `HEALTHCHECK` instruction is part of the standard Dockerfile
syntax and is honored by the Docker Engine, `docker ps`, and downstream
orchestration tools that read container health status
([docs.docker.com, Dockerfile reference](https://docs.docker.com/reference/dockerfile/#healthcheck),
verified 2026-08-02).

**Azure Traffic Manager and Azure App Service.** The Azure Architecture
Center's own reference implementation describes Traffic Manager regularly
pinging a configured URL, port, and path across regions, marking an
application available on an HTTP 200 and offline on any other response, and
rerouting traffic between regional deployments based on the result, while
Azure App Service ships a built-in health-check feature that integrates
with the platform's own authentication layer
([learn.microsoft.com, Health Endpoint Monitoring pattern, Monitor
endpoints in Azure-hosted applications section](https://learn.microsoft.com/en-us/azure/architecture/patterns/health-endpoint-monitoring),
verified 2026-08-02).

## 10. Consequences

Positive consequences.

- A failing instance stops receiving traffic within one polling interval
  instead of continuing to serve errors until a person intervenes.
- A stuck-but-not-crashed process can be detected and restarted
  automatically, converting a silent hang into a short, self-healing blip.
- Slow-starting processes, warming a cache or loading a large artifact into
  memory, can finish starting before they are judged, when a startup probe
  or its equivalent is used, instead of being killed in a restart loop.
- The signal is cheap for the platform to consume. A single HTTP request
  with a status code is far less work for a load balancer to interpret than
  parsing application logs or metrics.
- Separating liveness from readiness lets an operator distinguish restart
  this from stop sending it traffic for now as two different remedies,
  rather than being forced to pick one blunt action for every kind of
  trouble.

Negative consequences.

- Every check the pattern adds is more code, and code that runs on every
  poll for the lifetime of every instance, so it must be maintained with
  the same care as the request path it protects.
- A deep check touches real dependencies, and at fleet scale, the polling
  traffic itself becomes a load the dependency must absorb, on top of the
  application's real traffic.
- A misconfigured check can do active harm. An overly aggressive liveness
  probe that restarts a merely busy process converts a transient slowdown
  into a hard outage, and a readiness check that is too strict can pull an
  entire fleet out of rotation at once if all instances share the same
  transient dependency blip.
- The endpoint itself is new attack surface. If it returns detailed
  diagnostic information, it can leak internal topology to anyone who can
  reach it, and if it is left unauthenticated on a public interface, it can
  become a target for denial-of-service traffic
  ([learn.microsoft.com, Health Endpoint Monitoring pattern, Issues and
  considerations section](https://learn.microsoft.com/en-us/azure/architecture/patterns/health-endpoint-monitoring),
  verified 2026-08-02).
- The pattern only reports what it was told to check. A dependency that was
  never added to the registry, or a new failure mode nobody anticipated,
  passes silently, and a health endpoint that always answers healthy gives
  false confidence that is worse than having no health signal at all.

## 11. Failure modes and misuse

**Deep check cascading failure.** This is the most damaging misuse of the
pattern and the one this entry treats in the most detail. Symptom. Multiple
instances flip to unready, or are killed and restarted, within the same
short window, even though the instances' own code paths are otherwise
healthy, and the failure appears to spread across the fleet in the same
interval a shared dependency degraded, rather than being confined to
requests that actually needed that dependency. Cause. A liveness or
readiness endpoint performs a deep, uncached call to a real dependency on
every single poll, and when that dependency becomes slow rather than fully
down, every instance in the fleet starts holding open a connection, a
thread, or a connection-pool slot per poll, for as long as the dependency
takes to respond or the check's own timeout to fire. If the check has no
timeout, or a timeout longer than the platform's polling interval, the
checks pile up faster than they complete, and the health check is now
competing with real requests for the exact resource the slow dependency is
starving, so the more the dependency degrades, the more the health check
starves alongside it. Fix. Give every dependency check its own strict
timeout, well under the polling interval. Run checks from a background
poller rather than the request path so the failure never touches
request-handling resources. Cap how much processing a check performs at
all, per the Azure Architecture Center's own warning, which states,
"Performing excessive processing during the check can overload the
application and affect other users. The processing time might also exceed
the timeout of the monitoring system. As a result, the system might mark
the application as unavailable."
([learn.microsoft.com, Health Endpoint Monitoring pattern, Issues and
considerations section](https://learn.microsoft.com/en-us/azure/architecture/patterns/health-endpoint-monitoring),
verified 2026-08-02). Also consider whether a dependency belongs behind a
Circuit Breaker so a health check against it fails fast once the breaker is
already open instead of waiting out a fresh timeout on every poll.

**Health check flapping under threshold-free evaluation.** Symptom. An
instance is repeatedly marked ready, then unready, then ready again,
several times a minute, with no sustained outage visible anywhere else in
the system, and every flip generates a routing change and often a paging
alert. Cause. The aggregator acts on the single most recent check result
instead of requiring several consecutive identical results, so one slow
packet, one garbage-collection pause, or one dropped connection is enough
to flip the reported state. Fix. Apply a consecutive-threshold debounce on
both the healthy and unhealthy transitions, the same mechanism AWS's
Application Load Balancer applies by default at the infrastructure layer
with its `HealthyThresholdCount` and `UnhealthyThresholdCount` settings
([docs.aws.amazon.com, Health checks for your target groups](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html),
verified 2026-08-02), and apply the same debounce inside the application
layer too, because the load balancer's debounce does not help a Kubernetes
readiness probe evaluated closer to the pod.

**Conflated liveness and readiness.** Symptom. The platform restarts pods
in a loop, sometimes several times a minute, whenever a downstream
dependency is degraded, even though the application code itself never
crashed or hung. Cause. The same handler, or the same check registry, is
wired to both the liveness probe and the readiness probe, so a downstream
outage that should only pull the instance out of the traffic rotation
instead triggers a restart, which does nothing to fix an external
dependency and adds restart churn, container image pulls, and cold-start
latency on top of an outage that was never the instance's own fault. Fix.
Give liveness its own narrow handler that answers only whether this
process is alive, typically without touching any external dependency at
all, and give readiness its own separate handler that is allowed to
consult dependency state, matching the distinction Kubernetes itself draws
between the two probe types
([kubernetes.io, Configure Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/),
verified 2026-08-02).

**Slow-start restart loop.** Symptom. A service that takes tens of seconds
or minutes to finish initializing, for example loading a large in-memory
index, is killed and restarted repeatedly before it ever finishes starting,
and never reaches a running state. Cause. A liveness probe with a short
initial delay starts evaluating before initialization has finished, and the
first few failures accumulate past the failure threshold before the
process is done starting. Fix. Use a startup probe, or an equivalent
grace-period mechanism, that suppresses liveness and readiness evaluation
until the application signals it has finished starting, exactly the
purpose Kubernetes documents for the startup probe type
([kubernetes.io, Configure Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/),
verified 2026-08-02).

**Stale but trusted cached status.** Symptom. An instance keeps answering
healthy long after it has actually degraded, and the router keeps sending
it traffic that fails. Cause. The background poller thread has itself
crashed, deadlocked, or been starved, but the request handler only ever
reads the last cached snapshot and has no logic to notice how old that
snapshot is. Fix. Stamp every snapshot with the time it was produced, and
have the endpoint treat a snapshot older than some multiple of the polling
interval as unknown or unhealthy rather than trusting it forever, the
approach demonstrated in the code examples below.

**Unauthenticated diagnostic leak.** Symptom. An external actor is able to
enumerate internal service names, database vendor and version, or queue
depth by requesting the health endpoint from outside the trust boundary.
Cause. The endpoint returns full diagnostic detail on every request with no
authentication, on the assumption that only trusted infrastructure will
ever call it, an assumption that does not hold once the endpoint is
reachable from the public internet. Fix. Separate a minimal, unauthenticated
status code for infrastructure consumers from a detailed, authenticated
diagnostic view for operators, following the layered security guidance
below in dimension 17.

## 12. Trade-off matrix

| Force | Health Endpoint Monitoring | Circuit Breaker | Retry |
|---|---|---|---|
| Who decides to stop sending traffic | An external consumer, a router or orchestrator, based on a periodic poll | The calling instance itself, based on recent call outcomes | No decision to stop, only to try again |
| Detection latency | One or more polling intervals, typically seconds | Immediate, on the next call after the threshold trips | Not applicable, it reacts per call |
| Scope of protection | The whole instance, removed from rotation entirely | One specific downstream dependency, per call site | One specific call, per attempt |
| Cost when the dependency is healthy | A small, steady polling cost, independent of real traffic | Effectively free, only tracks outcomes of real calls | Free, only activates on failure |
| Cost when the dependency is unhealthy | Bounded by check timeout times poll rate | Bounded, calls fail fast once open | Can amplify load through repeated attempts |
| Primary failure mode if misapplied | Cascading check failures, flapping, restart loops | Breaker stuck open or never opens | Retry storm against an already struggling dependency |

Health Endpoint Monitoring and Circuit Breaker answer different questions
and are usually deployed together rather than as alternatives to each
other. A readiness check can, and often should, ask a Circuit Breaker
guarding a given dependency whether it is currently open, rather than
calling the dependency directly on every poll, which gives the check
sub-millisecond latency and avoids adding poll traffic on top of an already
struggling dependency. Retry, by contrast, operates entirely inside a single
call and has no concept of an instance-wide status at all, so comparing it
to Health Endpoint Monitoring is really a comparison of adjacent layers in
the same resilience approach rather than two solutions to one problem.

## 13. Related and incompatible patterns

**Circuit Breaker.** The natural companion. A readiness check can query the
current state of a Circuit Breaker instead of calling the guarded dependency
directly, converting the deep-check cascading failure described in
dimension 11 into a near-free state read once the breaker is already open.

**Retry.** Retry governs how a single call to a dependency is attempted
again after failure. A health check should generally not retry a failing
dependency call inline, because that only extends how long the check takes
to fail and increases how long a request handler blocks waiting on the
snapshot to update. A single attempt with a strict timeout, run from the
background poller, is the correct interaction between the two patterns.

**Bulkhead.** Isolating the resources a health check uses, its own thread
pool, its own connection pool slot, from the resources the main workload
uses is a direct application of Bulkhead to the health-check subsystem
itself, and is one of the more effective ways to keep a degraded dependency
from also degrading the ability to report that degradation.

**Leader Election.** In a clustered service where only one node should
perform a given role at a time, the health endpoint is often the mechanism
an external supervisor uses to detect that the current leader has stopped
responding and a new election should begin, making the two patterns
frequently paired in practice even though they solve different problems.

**Throttling.** A health endpoint that is itself rate-limited the same way
as ordinary application traffic can be starved out by an attacker or by a
traffic spike exactly when its signal matters most. Health endpoints are
usually exempted from general-purpose throttling, or given their own
separate, generous allowance, so the two patterns are compatible but need
deliberate configuration to avoid the endpoint becoming collateral damage of
protection meant for something else.

No pattern in this catalog is incompatible with Health Endpoint Monitoring
in the sense of actively conflicting with it. The closest thing to an
incompatibility is architectural rather than pattern-level. A fully
stateless, fully platform-managed serverless function whose invocation
model already replaces failed executions transparently gains comparatively
little from an additional custom health endpoint, as noted in dimension 4.

## 14. Refactoring path in and out

**Introducing the pattern into a service that has none.**

1. Add a minimal liveness endpoint first, one that returns 200 with no
   dependency logic at all, wired to the platform's liveness or restart
   mechanism. This alone catches deadlocked and wedged processes with
   almost no engineering risk, because a handler with no external calls has
   almost nothing to get wrong.
2. Enumerate the service's real dependencies, and for each one decide
   explicitly whether its unavailability should remove the instance from
   rotation, a hard dependency, or only degrade a status field, a soft
   dependency, rather than defaulting every dependency into the same
   bucket.
3. Build the check registry and the background poller before writing the
   readiness handler itself, so the handler only ever reads a cached
   snapshot from day one and the deep-check-in-the-request-path mistake
   from dimension 11 is never introduced in the first place.
4. Wire the readiness endpoint into the platform's routing decision, watch
   it in a staging environment under simulated dependency failure before
   relying on it in production, and confirm both that a real dependency
   failure removes the instance from rotation and that a healthy instance
   is never wrongly marked unready.
5. Add the consecutive-threshold debounce once the basic pass and fail
   paths are proven correct, tuning the thresholds against the service's
   own observed noise rather than copying another service's numbers
   unexamined.

**Removing or simplifying the pattern.**

1. Confirm the platform layer underneath the application, a managed load
   balancer, a fully managed serverless runtime, does not already provide
   an equivalent signal that would make the application-level check
   redundant, per the non-applicability guidance in dimension 4.
2. Retire individual checks one at a time, starting with any check that has
   not caught a real incident in the observable history of the service,
   watching for a period afterward to confirm nothing regresses silently.
3. Collapse a set of checks that always pass or fail together back into a
   single check, reducing maintenance surface without reducing detection
   power, if the operational history shows they never diverge in practice.
4. Only remove the endpoint entirely, rather than simplifying it, once
   there is no consumer left, since a load balancer or orchestrator
   pointed at a now-deleted endpoint typically fails closed and stops
   routing traffic to the instance altogether, turning a cleanup task into
   an outage if done out of order.

## 15. Testing and verification

A health check is a piece of production logic and deserves the same test
discipline as the request path it protects, with the added requirement that
its failure behavior is what actually gets exercised in production, so the
failure path needs testing at least as thoroughly as the success path.

**Unit test the aggregator in isolation from real dependencies.** Feed the
aggregator a fixed set of check results, some passing, some failing, some
timed out, and confirm the resulting status matches the intended policy,
hard dependency failure blocks readiness, soft dependency failure only
changes a status field, and confirm the threshold debounce logic requires
the correct number of consecutive results before flipping state in either
direction.

**Use a fake or stub for each dependency check, not the real dependency.**
A database check under test should exercise the code path against a fake
that can be told to hang past the timeout, return an error, or return a
slow but successful response, so the test suite proves the timeout
mechanism actually fires rather than proving only that a real, healthy
local database answers quickly.

**Simulate the deep-check cascading failure directly.** Configure a fake
dependency to hang indefinitely and confirm the check still returns within
its configured timeout, the poller loop is not blocked by the hang, and the
request-handling path is unaffected while the dependency is stuck. This is
the single most valuable test this pattern can carry, because it is a
direct regression test for the most damaging failure mode in dimension 11.

**Test the staleness path.** Freeze or mock the poller so no fresh snapshot
is ever written, and confirm the endpoint reports unknown or unhealthy after
the staleness window elapses rather than serving a stale cached healthy
result forever.

**Exercise it against the real platform in a staging environment before
trusting it in production.** Kill a real dependency in staging and observe
whether the orchestrator actually removes the instance from rotation, and
separately restart the process and confirm the startup grace period
behaves as configured. A unit-tested aggregator proves the internal logic
is correct, but only an end-to-end run against the real platform proves the
wiring between the endpoint and the consumer is correct.

## 16. Observability signals

**Per-check latency and outcome, logged and exported as a metric on every
poll**, not only on failure, so a slow but not yet failing dependency is
visible as a trend before it crosses the failure threshold.

**Consecutive-failure and consecutive-success counters per check**, mirroring
the threshold state used by the debounce logic itself, so an operator can
see exactly how close a flapping check is to flipping state rather than
only seeing the binary result after the fact.

**Time since the last successful poller run**, exposed directly, because
this is the metric that catches the stale but trusted failure mode from
dimension 11 before an outside observer notices the endpoint is lying.

**Rate of readiness transitions per instance and per fleet**, because a
single instance flipping occasionally is normal noise, while every instance
in a fleet flipping within the same short window is a signal that the
problem is a shared dependency rather than any one instance.

**A dashboard that shows healthy, unready, and unknown counts across the
fleet, drawn from the platform's own view of the state**, not the
application's self-reported state, because the two can disagree, for
example when a network partition prevents the platform from reaching an
instance the instance itself still believes is healthy. The AWS
Application Load Balancer exposes exactly this kind of state, with reason
codes distinguishing a target-side failure from a load-balancer-side
internal error
([docs.aws.amazon.com, Health checks for your target groups](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html),
verified 2026-08-02).

**What a healthy instance looks like.** Near-zero per-check latency
variance, zero or low single-digit consecutive-failure counts across the
fleet at any given moment, a poller age metric that never exceeds roughly
one polling interval, and a readiness-transition rate close to zero outside
of planned deploys.

**What a failing instance looks like.** One check's latency trending
upward over minutes before it ever crosses the failure threshold, which is
the leading indicator worth alerting on before the lagging binary status
flips at all, followed by a rising consecutive-failure counter and, in a
shared-dependency incident, the same trend appearing on multiple instances
within the same short window.

## 17. Security and privacy implications

The health endpoint is reachable, by design, by automated infrastructure
that often sits outside the application's own authentication layer, a load
balancer's health-check subsystem, a container orchestrator's kubelet, an
external synthetic monitor, which creates real tension with normal access
control. A completely locked-down endpoint that requires the same
authentication as the rest of the API can be unreachable by the very
infrastructure that needs to poll it, while a completely open endpoint is
reachable by anyone who can route a packet to it.

The practical resolution used across the production systems in dimension 9
is a two-tier design. A minimal, unauthenticated endpoint returns only a
status code, healthy or unhealthy, with no body content and no internal
detail, for infrastructure consumers that cannot easily authenticate. A
separate, authenticated or network-restricted endpoint returns the full
diagnostic breakdown, per-check latency, error messages, dependency names,
for human operators and internal dashboards. The Azure Architecture Center
guidance lists concrete techniques for that restricted tier. Requiring
authentication where the monitoring tool supports it, placing the endpoint
on a non-default port or an obscure path, and treating obscurity alone as
insufficient, favoring an encrypted transport and access control rather
than relying on a hidden URL as the only protection
([learn.microsoft.com, Health Endpoint Monitoring pattern, Issues and
considerations section](https://learn.microsoft.com/en-us/azure/architecture/patterns/health-endpoint-monitoring),
verified 2026-08-02).

Two further, more specific implications are worth naming directly. First,
an unauthenticated deep-check endpoint is an amplification and
denial-of-service target. An attacker who can trigger repeated calls to it
can force the instance to repeatedly call its own backend dependencies,
turning a cheap request against the health endpoint into an expensive chain
of calls against a database or downstream service, which is exactly why
dimension 11 treats uncached deep checks as a cascading-failure risk even
without any attacker involved. Second, detailed diagnostic output, error
messages, stack traces, internal hostnames, is genuinely useful for
debugging and genuinely useful for an attacker mapping the internal
topology of a system, so the choice of what detail to expose in the
unauthenticated tier is a real security decision, not a cosmetic one, and
the safe default is to expose the least detail that still lets the
infrastructure make its routing and restart decisions correctly.

## Code examples

Three implementations follow, each demonstrating a different facet of the
pattern rather than repeating the same one. All three were compiled or run
directly rather than only written, and each produced the output shown in
its own paragraph below.

The TypeScript example demonstrates the split between a liveness handler
that touches nothing external and a readiness handler that reads a
background-polled, cached snapshot with a staleness check. It was compiled
with `npx tsc --strict` against Node's `@types/node`, then run under Node
23, and it printed the output below.

```
listening on 8091
live -> 200 {"status":"alive"}
ready -> 200 {"status":"ready","checks":[{"name":"primary-db","ok":true,"ms":10},{"name":"cache","ok":true,"ms":5}]}
```

```typescript
import { createServer, IncomingMessage, ServerResponse } from "node:http";

type CheckResult = { name: string; ok: boolean; ms: number; detail?: string };

interface DependencyCheck {
  name: string;
  timeoutMs: number;
  run: () => Promise<void>;
}

async function withTimeout(p: Promise<void>, ms: number): Promise<void> {
  let timer: NodeJS.Timeout;
  const timeout = new Promise<void>((_, reject) => {
    timer = setTimeout(() => reject(new Error("timeout after " + ms + "ms")), ms);
  });
  try {
    await Promise.race([p, timeout]);
  } finally {
    clearTimeout(timer!);
  }
}

async function runCheck(check: DependencyCheck): Promise<CheckResult> {
  const start = Date.now();
  try {
    await withTimeout(check.run(), check.timeoutMs);
    return { name: check.name, ok: true, ms: Date.now() - start };
  } catch (err) {
    return { name: check.name, ok: false, ms: Date.now() - start, detail: String(err) };
  }
}

// A poller runs deep checks off the request path and caches the
// result, so a slow dependency never adds latency to a real request.
class ReadinessPoller {
  private cached: { ok: boolean; results: CheckResult[]; checkedAt: number } = {
    ok: false,
    results: [],
    checkedAt: 0,
  };
  private timer?: NodeJS.Timeout;

  constructor(private checks: DependencyCheck[], private intervalMs: number) {}

  start(): void {
    const tick = async () => {
      const results = await Promise.all(this.checks.map(runCheck));
      this.cached = { ok: results.every((r) => r.ok), results, checkedAt: Date.now() };
    };
    tick();
    this.timer = setInterval(tick, this.intervalMs);
  }

  stop(): void {
    if (this.timer) clearInterval(this.timer);
  }

  snapshot() {
    return this.cached;
  }
}

const dependencyChecks: DependencyCheck[] = [
  { name: "primary-db", timeoutMs: 300, run: async () => { await new Promise((r) => setTimeout(r, 10)); } },
  { name: "cache", timeoutMs: 150, run: async () => { await new Promise((r) => setTimeout(r, 5)); } },
];

const poller = new ReadinessPoller(dependencyChecks, 5000);
poller.start();

function send(res: ServerResponse, status: number, body: unknown): void {
  res.writeHead(status, { "Content-Type": "application/json" });
  res.end(JSON.stringify(body));
}

const server = createServer((req: IncomingMessage, res: ServerResponse) => {
  const url = req.url ?? "/";

  if (url === "/healthz/live") {
    send(res, 200, { status: "alive" });
    return;
  }

  if (url === "/healthz/ready") {
    const snap = poller.snapshot();
    const staleMs = Date.now() - snap.checkedAt;
    if (staleMs > 20000) {
      send(res, 503, { status: "unknown", reason: "checker stalled", staleMs });
      return;
    }
    send(res, snap.ok ? 200 : 503, { status: snap.ok ? "ready" : "not-ready", checks: snap.results });
    return;
  }

  send(res, 404, { error: "not found" });
});

server.listen(8091);
```

The Python example demonstrates the consecutive-threshold debounce,
mirroring AWS's `HealthyThresholdCount` and `UnhealthyThresholdCount`
semantics inside the application itself, plus a per-check timeout enforced
with a daemon thread and a join deadline, avoiding a dependency that
ignores cancellation from hanging the poller. It ran under CPython 3.14
with no third-party packages, and printed the output below.

```
live -> 200 {"status": "alive"}
ready -> 200 {"status": "healthy", "checks": [{"name": "primary-db", "ok": true, "ms": 12.7, "detail": ""}, {"name": "message-queue", "ok": true, "ms": 6.4, "detail": ""}]}
```

```python
import http.server
import json
import socketserver
import threading
import time
from dataclasses import dataclass
from typing import Callable


@dataclass
class DependencyCheck:
    name: str
    timeout_s: float
    probe: Callable[[], None]


def run_check(check: DependencyCheck) -> tuple[bool, float, str]:
    start = time.monotonic()
    holder: dict[str, Exception | None] = {"err": None}

    def target() -> None:
        try:
            check.probe()
        except Exception as exc:
            holder["err"] = exc

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(check.timeout_s)
    elapsed = time.monotonic() - start
    if thread.is_alive():
        return False, elapsed, "timeout after {:.0f}ms".format(check.timeout_s * 1000)
    if holder["err"] is not None:
        return False, elapsed, str(holder["err"])
    return True, elapsed, ""


class ThresholdGate:
    # Debounces a raw pass/fail signal into a stable state, the way a
    # load balancer's healthy and unhealthy thresholds debounce a target.
    def __init__(self, healthy_threshold: int, unhealthy_threshold: int) -> None:
        self.healthy_threshold = healthy_threshold
        self.unhealthy_threshold = unhealthy_threshold
        self.consecutive_ok = 0
        self.consecutive_fail = 0
        self.state = "unhealthy"

    def observe(self, ok: bool) -> str:
        if ok:
            self.consecutive_ok += 1
            self.consecutive_fail = 0
            if self.consecutive_ok >= self.healthy_threshold:
                self.state = "healthy"
        else:
            self.consecutive_fail += 1
            self.consecutive_ok = 0
            if self.consecutive_fail >= self.unhealthy_threshold:
                self.state = "unhealthy"
        return self.state


checks = [
    DependencyCheck("primary-db", 0.3, lambda: time.sleep(0.01)),
    DependencyCheck("message-queue", 0.15, lambda: time.sleep(0.005)),
]
gate = ThresholdGate(healthy_threshold=2, unhealthy_threshold=2)
lock = threading.Lock()
snapshot: dict = {"state": "unhealthy", "results": []}


def poll_loop(stop_event: threading.Event) -> None:
    while not stop_event.is_set():
        results = [run_check(c) for c in checks]
        raw_ok = all(ok for ok, _, _ in results)
        with lock:
            state = gate.observe(raw_ok)
            snapshot["state"] = state
            snapshot["results"] = [
                {"name": c.name, "ok": ok, "ms": round(ms * 1000, 1), "detail": detail}
                for c, (ok, ms, detail) in zip(checks, results)
            ]
        stop_event.wait(1.0)


class HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/healthz/live":
            self._respond(200, {"status": "alive"})
            return
        if self.path == "/healthz/ready":
            with lock:
                state = snapshot["state"]
                body = {"status": state, "checks": snapshot["results"]}
            self._respond(200 if state == "healthy" else 503, body)
            return
        self._respond(404, {"error": "not found"})

    def _respond(self, code: int, body: dict) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


with socketserver.ThreadingTCPServer(("127.0.0.1", 8092), HealthHandler) as httpd:
    threading.Thread(target=poll_loop, args=(threading.Event(),), daemon=True).start()
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
```

The Go example demonstrates a composable `Checker` interface with a
concurrent, per-check-timeout poller behind a `Registry`, and a request
handler that only reads a lock-protected snapshot. It was built and run
with `go run` under Go 1.26, and printed the output below.

```
live -> 200
ready -> 200
```

```go
package main

import (
	"context"
	"encoding/json"
	"net/http"
	"sync"
	"time"
)

// Checker is a single dependency probe. Deep checkers hit a real
// dependency; shallow checkers only confirm the process can respond.
type Checker interface {
	Name() string
	Check(ctx context.Context) error
}

type funcChecker struct {
	name string
	fn   func(ctx context.Context) error
}

func (f funcChecker) Name() string                    { return f.name }
func (f funcChecker) Check(ctx context.Context) error { return f.fn(ctx) }

type checkResult struct {
	Name  string `json:"name"`
	OK    bool   `json:"ok"`
	Ms    int64  `json:"ms"`
	Error string `json:"error,omitempty"`
}

// Registry polls checkers on an interval and caches the result, so a
// request never blocks on a live dependency call.
type Registry struct {
	mu       sync.RWMutex
	checkers []Checker
	timeout  time.Duration
	results  []checkResult
	ready    bool
	checked  time.Time
}

func NewRegistry(timeout time.Duration, checkers ...Checker) *Registry {
	return &Registry{checkers: checkers, timeout: timeout}
}

func runSingleCheck(c Checker, timeout time.Duration) checkResult {
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()
	start := time.Now()
	err := c.Check(ctx)
	res := checkResult{Name: c.Name(), OK: err == nil, Ms: time.Since(start).Milliseconds()}
	if err != nil {
		res.Error = err.Error()
	}
	return res
}

func (r *Registry) runOnce() {
	results := make([]checkResult, len(r.checkers))
	var wg sync.WaitGroup
	for i, c := range r.checkers {
		wg.Add(1)
		go func(i int, c Checker) {
			results[i] = runSingleCheck(c, r.timeout)
			wg.Done()
		}(i, c)
	}
	wg.Wait()

	ok := true
	for _, res := range results {
		if !res.OK {
			ok = false
			break
		}
	}

	r.mu.Lock()
	r.results, r.ready, r.checked = results, ok, time.Now()
	r.mu.Unlock()
}

func (r *Registry) Start(interval time.Duration, stop <-chan struct{}) {
	r.runOnce()
	ticker := time.NewTicker(interval)
	go func() {
		defer ticker.Stop()
		for {
			select {
			case <-ticker.C:
				r.runOnce()
			case <-stop:
				return
			}
		}
	}()
}

func (r *Registry) Snapshot() (bool, []checkResult, time.Time) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.ready, r.results, r.checked
}

func writeJSON(w http.ResponseWriter, status int, body any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(body)
}

func readinessHandler(reg *Registry) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ok, results, checked := reg.Snapshot()
		if time.Since(checked) > 20*time.Second {
			writeJSON(w, http.StatusServiceUnavailable, map[string]any{"status": "unknown"})
			return
		}
		status, state := http.StatusOK, "ready"
		if !ok {
			status, state = http.StatusServiceUnavailable, "not-ready"
		}
		writeJSON(w, status, map[string]any{"status": state, "checks": results})
	}
}
```

A fourth or fifth language, Java, Rust, or Swift, was not added, because the
three shown already cover three distinct implementation techniques this
entry names, a raw async runtime, a thread-and-lock based server, and a
statically typed concurrent server, and a fourth sample would repeat one of
those three techniques in different syntax rather than teach a new one.

## 18. References

- Microsoft patterns and practices group, *Cloud Design Patterns,
  Prescriptive Architecture Guidance for Cloud Applications*, January 2014,
  Health Endpoint Monitoring Pattern chapter,
  [learn.microsoft.com, archived guide](https://learn.microsoft.com/en-us/previous-versions/msp-n-p/dn568099(v=pandp.10)),
  verified 2026-08-02.
- Microsoft, "Health Endpoint Monitoring pattern," Azure Architecture
  Center, [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/architecture/patterns/health-endpoint-monitoring),
  verified 2026-08-02.
- Kubernetes documentation, "Configure Liveness, Readiness and Startup
  Probes," [kubernetes.io](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/),
  verified 2026-08-02.
- Amazon Web Services, "Health checks for your Application Load Balancer
  target groups,"
  [docs.aws.amazon.com](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html),
  verified 2026-08-02.
- VMware Tanzu and Spring, "Endpoints," Spring Boot Reference Documentation,
  health endpoint and Kubernetes probes section,
  [docs.spring.io](https://docs.spring.io/spring-boot/reference/actuator/endpoints.html),
  verified 2026-08-02.
- Docker Inc, "Dockerfile reference," HEALTHCHECK instruction,
  [docs.docker.com](https://docs.docker.com/reference/dockerfile/#healthcheck),
  verified 2026-08-02.
- Microsoft, "Cloud design patterns," Azure Architecture Center pattern
  catalog index,
  [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/architecture/patterns/),
  verified 2026-08-02.
