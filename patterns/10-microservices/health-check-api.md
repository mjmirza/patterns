---
name: Health Check API
slug: health-check-api
family: 10-microservices
category: Microservices, Observability
aliases: [Health Endpoint, Liveness and Readiness Probes, Health Check Endpoint]
first_described: "Newman, Sam. Building Microservices, 1st edition, O'Reilly, 2015"
maturity: canonical
related: [application-metrics, distributed-tracing, service-registry, self-registration, circuit-breaker, service-mesh]
incompatible_with: []
verified: 2026-08-02
---

# Health Check API

## 1. Name, aliases, and lineage

The canonical name in service-oriented literature is Health Check API. Sam
Newman used this exact term in Building Microservices, first edition,
O'Reilly, 2015, chapter 4, in the section on monitoring, describing a service
that "should ideally include a way for you to see the health of the system
itself, not just the health of the underlying operating system." The pattern
predates the microservices vocabulary. Load balancers have exposed HTTP based
service checks since at least the mid 1990s, and Nagios style plugin checks
formalized the idea of a machine readable pass or fail probe for a running
process in the same era. What microservices practice added was the split of
one health signal into two distinct questions, whether the process is alive
and whether it is ready to accept traffic, a distinction Kubernetes later
codified as separate liveness and readiness probes in its own documentation.

Two names are in wide but inconsistent use for two different things, and
conflating them is the single most common cause of outages attributed to this
pattern. Liveness and readiness probe describes the Kubernetes specific
mechanism that periodically calls a health endpoint and acts on the result,
documented at kubernetes.io in the section titled Configure Liveness,
Readiness and Startup Probes, verified 2026-08-02. Health Check API describes
the HTTP contract itself, independent of who calls it. A service can expose a
correct Health Check API and still be misconfigured if the platform's probe
policy misuses the response.

RFC 3164 and its practical descendants, plus the AWS Elastic Load Balancing
health check documentation (docs.aws.amazon.com, Application Load Balancers,
Health checks for your target groups, verified 2026-08-02), independently
arrived at the same shape decades apart, an HTTP GET against a well known
path returning a status code the caller interprets as up or down. The
convergence across systems that never coordinated with each other is one
of the strongest signals in this catalog that the pattern is not a framework
convention but a genuine solution to a recurring problem.

## 2. Problem and context

A running process is not the same thing as a working service. A Java process
can be alive, holding its listening socket open, answering the operating
system's TCP handshake, and still be unable to serve a single correct
request because its database connection pool exhausted, its downstream
dependency is unreachable, or a background thread deadlocked while holding a
lock every request path needs. From outside the process, at the level of a
load balancer or an orchestrator, none of that internal state is visible. The
only signal available by default is whether the socket accepts connections,
and that signal answers a narrower question than the one operators actually
care about.

This gap matters most at three points in a service's life. First, during
startup, when a JVM based service can accept a TCP connection while Spring's
context is still wiring beans, well before the service can answer a real
request, so traffic sent too early returns errors under load. Second, during
a dependency outage, when a service instance is fully capable of running its
own logic but cannot complete any request because the database it depends on
is down, and continuing to route traffic to it wastes client time on
requests that will fail anyway. Third, during a slow internal failure, a
deadlock, a memory leak approaching an OOM kill, or a thread pool exhausted
by a slow downstream call, where the process keeps its listening socket open
long after it has stopped doing useful work.

The context in which this pattern is needed is any deployment where
something automated decides whether to route traffic to an instance or
whether to restart it, without a human watching. That includes a load
balancer's target group, a Kubernetes kubelet, a service mesh sidecar
performing outlier detection, and a deployment pipeline's automated rollback
gate. In a single process deployed to a single host with a human operator
watching logs, the pattern still has value for debugging but loses its
primary reason for existing, since the automated routing decision it exists
to inform is absent.

## 3. Forces

This dimension is largely engineering judgement, drawn from operating this
pattern in production rather than from a single citable source.

The central force is the tension between a fast, cheap check and an
accurate, expensive one. A health check that queries the database, the
message broker, and every downstream dependency on every call gives the most
accurate picture of whether the service can do useful work, but it also adds
load to those dependencies proportional to the probe interval times the
number of instances, and it makes the health signal itself dependent on the
availability of systems the service does not control. A health check that
only confirms the process is alive is cheap and fast but tells the caller
almost nothing about whether requests will succeed.

A second force is the difference between what the check should report and
what action the caller should take on a failure. A liveness failure should
usually trigger a restart, because the assumption is that the process is
stuck in a state a restart can fix. A readiness failure should trigger
removal from a load balancer's rotation without a restart, because the
process itself may be fine, only a dependency is unavailable, and restarting
would not fix that and would needlessly interrupt in flight work. Collapsing
these into one endpoint with one meaning forces every caller to guess which
action applies, and the two most common production incidents this pattern
causes both trace back to that collapse, a restart loop triggered by a
transient dependency outage, or a load balancer routing traffic to an
instance whose process is technically alive but cannot serve any request.

A third force is cost of false signals in both directions. A health check
that is too strict, failing on a transient blip in a non critical
dependency, causes cascading restarts or unnecessary traffic removal under
exactly the load conditions when the system can least afford it, an effect
sometimes called a thundering herd of self inflicted failures. A health
check that is too lenient, always returning 200 regardless of internal
state, gives operators false confidence and defeats the pattern's purpose
entirely. The pattern favours accuracy over cheapness for readiness, and
favours cheapness and narrow scope over accuracy for liveness, and that
asymmetry is the core design decision every implementation has to get right.

## 4. Applicability and non-applicability

Reach for a Health Check API when any automated system routes traffic to,
restarts, or scales a set of process instances without a human in the loop
for each decision, which covers essentially every service running behind a
load balancer, inside Kubernetes, ECS, or any comparable orchestrator, or
behind a service mesh sidecar performing outlier detection. It also applies
when a deployment pipeline needs an automated gate to decide whether a newly
rolled out version is healthy before shifting more traffic to it, the basis
of canary and blue green rollout automation.

Do not reach for it, or reach for a much simpler version of it, in these
cases.

A single instance, single tenant batch job with no traffic routing decision
to make has no caller for the endpoint to inform, so building one is pure
overhead. A short lived serverless function invoked per request, where the
platform itself manages the execution environment's lifecycle and there is
no persistent process to probe between invocations, gets nothing from a
health endpoint in the traditional sense, though the underlying platform may
still expose its own readiness signal for the deployment itself, which is a
different mechanism. A service with zero external dependencies and trivial
internal state, where the only meaningful failure mode is the process not
running at all, does not need a readiness check distinct from a liveness
check, and building the distinction anyway adds a maintenance burden with no
corresponding benefit. A health check that would need to call another
service's health check to determine its own status, forming a chain, should
be redesigned rather than built, because chained health checks turn a single
dependency outage into a cascading readiness failure across every service in
the chain, which is the opposite of the isolation this pattern is supposed
to provide.

## 5. Structure

The pattern has four participants.

The Service Under Check is the process whose health is being reported. It
owns the logic that decides what alive and what ready mean for itself, and
it is the only participant with the internal visibility to make that
decision correctly.

The Health Check Endpoint is the HTTP or gRPC surface the Service Under
Check exposes, conventionally at a well known path such as `/health`,
`/healthz`, or split into `/livez` and `/readyz` following the Kubernetes
convention. It translates the service's internal state into a machine
readable response, typically an HTTP status code plus an optional structured
body naming the checked components and their individual status.

The Dependency Checkers are the individual probes the endpoint runs
internally against each thing the service depends on, a database connection
pool, a message broker connection, a downstream HTTP service, a disk volume.
Each checker is scoped to answer one narrow question, is this specific
dependency currently usable, and the endpoint aggregates their results.

The Health Check Caller is the external actor that periodically invokes the
endpoint and acts on the result. In practice this is one or more of a load
balancer's target group health check, a Kubernetes kubelet running liveness
and readiness probes, a service mesh sidecar's outlier detection, or a human
or automated deployment tool checking status during a rollout. The Caller
never inspects the Service Under Check's internals directly, it only ever
sees the aggregated response from the Health Check Endpoint.

## 6. ASCII structure diagram

```
+-------------------------------------------------------------+
|                    Service Under Check                       |
|                                                                |
|   +------------------------+                                  |
|   | Health Check Endpoint  |                                  |
|   |  GET /livez            |<---------- Health Check Caller   |
|   |  GET /readyz           |            (kubelet, ELB target  |
|   +-----------+------------+             group, mesh sidecar) |
|               |                                                |
|               | aggregates results from                        |
|               v                                                |
|   +--------------------------------------------------------+   |
|   | Dependency Checkers                                     |   |
|   |  - Database pool checker  -> Database                   |   |
|   |  - Broker checker         -> Message Broker              |   |
|   |  - Downstream checker     -> Downstream HTTP Service      |   |
|   +--------------------------------------------------------+   |
+-------------------------------------------------------------+
```

## 7. Dynamics

```
Startup sequence, Kubernetes kubelet as caller:

kubelet          Service Process           Dependency
  |                    |                        |
  |--GET /livez ------>|                        |
  |<--503 (starting)---|                        |
  |   (retry per startupProbe interval)          |
  |--GET /livez ------>|                        |
  |<--200 (alive)------|                        |
  |--GET /readyz ------>|                        |
  |                    |--connect + ping ------>|
  |                    |<--ok--------------------|
  |<--200 (ready)-------|                        |
  |   kubelet adds pod to Service endpoints       |
  |                    |                        |
Runtime, dependency outage:
  |--GET /readyz ------>|                        |
  |                    |--connect + ping ------>|
  |                    |            (timeout)   X
  |<--503 (not ready)---|                        |
  |   kubelet removes pod from Service endpoints  |
  |                    |                        |
  |--GET /livez ------>|   (process itself is    |
  |<--200 (alive)-------|   fine, no restart)     |
```

The two probes diverge in what happens on failure. A `/livez` failure that
persists past the configured `failureThreshold` causes the kubelet to kill
and restart the container, per the Kubernetes documentation on Configure
Liveness, Readiness and Startup Probes, section Define a liveness command,
kubernetes.io, verified 2026-08-02. A `/readyz` failure never triggers a
restart, it only removes the pod's IP from the Service's list of endpoints,
so traffic stops arriving at that pod until the readiness check passes
again, per the same document's section on readiness probes.

## 8. Implementation variants

The single endpoint variant exposes one path, typically `/health`, that
returns a single aggregate status, often used behind a plain load balancer
that has no concept of liveness versus readiness, such as a classic AWS
Elastic Load Balancer target group health check, documented at
docs.aws.amazon.com under Health checks for your target groups, verified
2026-08-02. This variant is simplest to implement and is adequate when the
caller only has one action available anyway, remove from rotation.

The split endpoint variant, `/livez` and `/readyz`, is the Kubernetes
convention and the one recommended by the Kubernetes documentation itself.
The liveness check deliberately excludes dependency checks and only confirms
the process's own control loop is responsive, so a database outage never
triggers a container restart. The readiness check includes dependency
checks and can legitimately return not ready while the process stays alive.

The structured response variant returns a JSON body naming each checked
component individually rather than a single boolean, following the shape
standardized in IETF RFC draft "Health Check Response Format for HTTP APIs"
(draft-inadarei-api-health-check), which specifies a `status` field with
values `pass`, `warn`, or `fail`, and a `checks` object keyed by component
name, each with its own status, output, and time. This variant trades a
larger response payload for the ability to diagnose which specific
dependency is degraded without opening a log file, and it is the shape most
commercial API gateways and monitoring dashboards expect when scraping a
health endpoint for a status page.

The passive variant, sometimes called application level metrics as health,
infers health from existing request success and latency metrics rather than
running dedicated probe logic, an approach service meshes such as Envoy use
for outlier detection, ejecting an upstream host based on observed error
rate rather than a dedicated health endpoint, documented in the Envoy
proxy's outlier detection architecture overview at envoyproxy.io, verified
2026-08-02. This variant avoids the cost of synthetic probe traffic entirely
but reacts only after real requests have already failed, trading detection
speed for zero added load.

Language idiom differs mainly in how the dependency checkers compose.
Node.js and Go implementations commonly run checkers concurrently with a
bounded timeout using Promise.allSettled or a goroutine fan out with a
context deadline, so one slow dependency check does not delay the whole
response past the caller's own probe timeout. Frameworks such as Spring Boot
Actuator (`/actuator/health`) and ASP.NET Core's HealthChecks middleware
provide this composition as a built in feature rather than something each
service author writes from scratch, registering individual `HealthIndicator`
or `IHealthCheck` implementations that the framework aggregates.

## 9. Known production uses

Kubernetes itself specifies and consumes this pattern as a first class API
object. The `livenessProbe`, `readinessProbe`, and `startupProbe` fields on a
Pod spec are documented in full at kubernetes.io under Configure Liveness,
Readiness and Startup Probes, verified 2026-08-02, and every workload
running on Kubernetes that wants correct rolling updates depends on an
accurate implementation of this pattern from the application it deploys.

AWS Application Load Balancer and Network Load Balancer target groups
implement the Health Check Caller side of this pattern natively, polling a
configurable path and port on each registered target and removing an
unhealthy target from rotation automatically, documented at
docs.aws.amazon.com under Health checks for your target groups (Elastic
Load Balancing), verified 2026-08-02.

Spring Boot Actuator ships a built in Health Check Endpoint at
`/actuator/health` that aggregates registered `HealthIndicator` beans, one of
the most widely deployed concrete implementations of this pattern in Java
based server projects, documented in the Spring Boot reference documentation,
section Production ready features, Health information, at docs.spring.io,
verified 2026-08-02.

Envoy proxy implements a variant of the Health Check Caller as part of its
cluster manager, supporting both active HTTP or TCP health checking against
upstream hosts and passive outlier detection based on observed request
outcomes, documented at envoyproxy.io in the Health checking and Outlier
detection sections of the architecture overview, verified 2026-08-02, and
Envoy is the data plane inside Istio, one of the most widely deployed
service mesh implementations, per the Istio documentation's description of
its architecture at istio.io, verified 2026-08-02.

## 10. Consequences

Positive. Automated systems can make correct traffic routing and restart
decisions without a human watching dashboards continuously, which is a
prerequisite for any zero touch autoscaling or self healing deployment.
Rolling deployments become safer, because an orchestrator can hold back
traffic from a new instance until its readiness check passes, catching a
broken deployment before it receives production load rather than after. The
distinction between liveness and readiness lets an operator restart a stuck
process without also causing a thundering herd of removals across every
instance simultaneously affected by the same downstream outage, since only
readiness, not liveness, reacts to that outage.

Negative. Every dependency checked inside a readiness probe becomes a new
source of correlated failure across all instances of the service, since a
single shared dependency going down can make every instance simultaneously
report not ready, taking the entire service out of rotation even though no
instance has an actual defect. A readiness check that is too strict, or that
checks a non critical dependency, has caused real outages where a service
with a working critical path was removed from rotation because a logging
sidecar or a non essential cache was briefly unreachable. The check itself
consumes resources and adds load on every dependency proportional to probe
frequency times instance count, which at high instance counts against a
shared database can itself become a meaningful load source. A liveness
check that is implemented incorrectly, most commonly one that includes
dependency checks it should have excluded, causes exactly the restart storm
this pattern's split design exists to prevent.

## 11. Failure modes and misuse

**Symptom.** Every instance of a service restarts in a tight loop during a
brief database maintenance window, even though the application code has no
defect.
**Cause.** The liveness probe queries the database as part of its check,
conflating liveness with readiness. A restart cannot fix an external
database outage, so every restart just delays until the next probe, fails
again, and restarts again.
**Fix.** Remove dependency checks from the liveness endpoint entirely.
Liveness should only confirm the process's own event loop or request
handling thread is responsive, for example by checking that a background
heartbeat counter incremented recently. Move dependency checks to the
readiness endpoint only.

**Symptom.** A service is removed from load balancer rotation and never
returns, even though the underlying issue was transient and resolved
minutes ago.
**Cause.** The readiness checker opens a new connection to a dependency on
every probe and that connection attempt itself times out slowly, for
example a 30 second default socket timeout against a database that is now
reachable again, but the probe interval is 10 seconds, so every probe
attempt is still mid timeout when the next one starts, and none ever
completes within the caller's own probe timeout window.
**Fix.** Give every dependency checker its own short, explicit timeout that
is meaningfully shorter than the caller's probe timeout and the probe
interval, and prefer checking an already established connection pool's live
connection count over opening a fresh connection on every probe.

**Symptom.** A health dashboard shows every instance green throughout an
incident where the service was in fact returning errors to real users.
**Cause.** The health endpoint always returns 200 regardless of internal
state, either because it was implemented as a stub during initial
development and never revisited, or because someone hardcoded a 200 to stop
a noisy alert without addressing the underlying cause.
**Fix.** Treat the health endpoint as production code subject to the same
review and testing as any other route, and add an automated test that
asserts the endpoint returns a non 200 status when a dependency is
deliberately made unreachable in a test environment.

**Symptom.** During a Kubernetes rolling deployment, the new version's pods
receive production traffic and start returning errors before their
initialization has actually completed.
**Cause.** No `startupProbe` is configured, and the `readinessProbe`'s
`initialDelaySeconds` is set too low for a service whose startup time varies,
for example under cold cache conditions, so the kubelet marks the pod ready
before initialization genuinely finished.
**Fix.** Configure a dedicated `startupProbe` with a generous
`failureThreshold` times `periodSeconds` budget for worst case startup time,
which the kubelet uses before it starts evaluating liveness and readiness
probes at all, per the Kubernetes documentation's guidance for slow starting
containers.

## 12. Trade-off matrix

| Force | Health Check API (split liveness/readiness) | Application Metrics only (passive) | Manual operator monitoring |
|---|---|---|---|
| Detection speed for a hard crash | Fast, bounded by probe interval | Fast, based on request failure rate, but needs traffic to detect | Slow, depends on human attention |
| Detection speed for a slow dependency outage | Fast if readiness checks the dependency | Delayed until enough real requests fail to trip a threshold | Slow |
| Added load on dependencies | Proportional to probe interval times instance count | None, purely observational | None |
| False positive risk under a shared dependency outage | High if readiness checks a non critical shared dependency | Lower, only reacts to actual request failures | Depends on operator judgement |
| Operational cost to build and maintain | Moderate, one endpoint plus checkers per dependency | Low if metrics pipeline already exists | Low to build, high ongoing human cost |
| Works before any real traffic arrives | Yes, this is its primary advantage during rollout | No, needs real traffic to produce a signal | Not applicable |
| Suitability for automated restart decisions | Well suited via the liveness half | Poorly suited, no direct process level signal | Not automated |

## 13. Related and incompatible patterns

Application Metrics is the observational sibling of this pattern. A Health
Check API answers a binary or few valued question for an automated caller
making an immediate routing decision, while Application Metrics exposes
continuous, historical measurements for dashboards, alerting, and capacity
planning. The two compose well, a readiness checker frequently reads the
same connection pool statistics that also feed a metrics endpoint, but they
serve different consumers and different measurement windows and should not
be merged into one endpoint.

Circuit Breaker composes naturally with a readiness checker, since a
dependency checker can report a dependency as failing based on the same open
or closed state a circuit breaker around calls to that dependency already
tracks, avoiding a duplicate, independent probe against the same downstream
system.

Self Registration and Service Registry depend on this pattern in
orchestrators or service discovery systems that require a service to prove
it is healthy before registering itself, or that periodically re verify
registration validity through a health check against the registered
endpoint.

Distributed Tracing is complementary rather than compositional, a trace
shows why a specific request was slow or failed, while a health check
answers a narrower, current moment question about overall instance
viability, and the two are typically consumed by different roles, an
on call engineer diagnosing one incident versus an orchestrator making a
continuous automated decision.

No pattern in this catalog is directly incompatible with Health Check API.
The closest to a conflict is Service Mesh passive outlier detection, which
in principle can substitute for an active readiness probe, and running both
simultaneously against the same instance is not incompatible but is
redundant unless the two are configured to react to genuinely different
signals.

## 14. Refactoring path in and out

Introducing this pattern into an existing service without one starts with a
liveness only endpoint that returns 200 as long as the process's main
request handling path is responsive, verified by a lightweight internal
heartbeat rather than any dependency check, and wiring that endpoint into
whatever orchestrator or load balancer already exists as its health check
target. This alone catches full process hangs and crashes without risking
the restart storm failure mode described in dimension 11.

The second step adds a separate readiness endpoint, starting with a single
dependency, typically the primary database, since that dependency's
unavailability is usually the most common reason the service cannot
actually serve requests despite being alive. Each additional dependency
checker is added one at a time, and after each addition the team should
deliberately test what happens when that specific dependency is made
unavailable in a staging environment, confirming the failure mode matches
expectations, removal from rotation, not a restart, before adding the next
checker.

The third step, only where the caller supports it, splits the single
endpoint into the `/livez` and `/readyz` convention, moving any dependency
checks that were mistakenly placed on the liveness path over to readiness.

Removing this pattern is rare in practice, since the cost of keeping a
correctly scoped health endpoint is low relative to its benefit, but where a
service is being retired from an orchestrated environment into a manually
operated single instance context, the safe path is to delete the readiness
endpoint's dependency checks first, confirming manually that the removal
does not silently mask a real issue an operator was relying on the endpoint
to surface, and only then remove the endpoint entirely once no automated
caller references it.

## 15. Testing and verification

Unit test each dependency checker in isolation, injecting a fake or mock
version of the dependency client that can be made to return success,
failure, and timeout deterministically, asserting the checker reports the
correct status for each case without a real network call.

Integration test the aggregation logic by wiring the real endpoint against
a set of fake checkers with controlled outcomes, verifying that the overall
response status and code correctly reflect the worst individual checker
result, and that a single failing non critical checker does not silently
mask itself if the design intends every checked dependency to gate
readiness, or correctly does mask itself if the design intends only
critical dependencies to gate readiness, whichever the service has chosen.

What becomes easier to test because of this pattern is the deployment
pipeline itself, since a staging environment's rollout can be scripted to
poll the readiness endpoint and assert it eventually returns ready within a
bounded time, giving an automated, repeatable check of deployment success
that does not depend on watching logs by eye.

What becomes harder is testing the timeout and concurrency behaviour of the
aggregation logic itself, since a checker that hangs rather than failing
cleanly needs a dedicated test using a deliberately slow fake dependency to
confirm the aggregate endpoint still respects its own overall timeout
budget and does not itself hang indefinitely, which is a common gap teams
discover only in production during exactly the slow dependency incident the
readiness check was supposed to catch.

## 16. Observability signals

Log every readiness state transition, not every probe, ready to not ready
and back, with the specific checker that changed state and its error
detail, since logging every individual probe call at typical Kubernetes
default intervals of ten seconds produces overwhelming log volume with
almost no diagnostic value beyond confirming the transition itself.

Emit a metric counting readiness probe failures broken down by which
dependency checker failed, which is the single most useful signal for
distinguishing "my service has a bug" from "a shared dependency is having
an incident affecting many services at once," since the latter shows the
same checker failing simultaneously across many service's dashboards.

A healthy instance on a dashboard shows a flat, near constant readiness
state with occasional brief flaps during deployments only, and a liveness
restart count of zero over any normal operating window. A failing instance
shows either a sustained not ready state correlated with a specific
dependency's own incident, or, in the misuse case from dimension 11, a
liveness restart count climbing steadily, which is itself the clearest
signal that a liveness check has been implemented incorrectly and is
including a dependency check it should not.

## 17. Security and privacy implications

A health check endpoint is, by the nature of the pattern, an unauthenticated
or lightly authenticated HTTP path reachable by the caller performing the
probe, which is frequently an internal load balancer or kubelet but is
sometimes reachable from outside the cluster network boundary if the
endpoint is not explicitly separated from the public routable paths of the
service. A structured response body that names specific dependency
hostnames, connection pool sizes, internal error messages, or version
numbers gives useful reconnaissance information to an attacker if that
endpoint is exposed publicly, information that a well configured deployment
would keep on an internal only port or path.

The correct mitigation is to serve the health endpoint on a separate port
or network interface from the service's public API where the platform
supports it, a pattern Kubernetes explicitly supports by allowing a probe to
target a different container port than the one exposed by a Service object,
and to keep the response body minimal, a status code and, at most, a
component name and pass or fail status, omitting hostnames, versions, and
raw error messages from any response reachable outside the trusted network
boundary.

Where a service holds sensitive data and its readiness checker queries a
credentialed dependency such as a database, the checker itself must reuse
the service's existing least privilege connection credentials rather than
provisioning a separate, broader credential purely for the health check,
since a health check credential compromised through a less carefully
reviewed code path would otherwise become an unnecessary additional attack
surface with no corresponding benefit.

## 18. References

1. Newman, Sam. Building Microservices, first edition, O'Reilly Media, 2015, chapter 4, section on monitoring.
2. Kubernetes documentation, Configure Liveness, Readiness and Startup Probes. https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/ verified 2026-08-02.
3. AWS documentation, Health checks for your target groups (Application Load Balancer). https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html verified 2026-08-02.
4. Spring Boot reference documentation, Production ready features, Health information. https://docs.spring.io/spring-boot/reference/actuator/endpoints.html verified 2026-08-02.
5. Envoy proxy documentation, Health checking and Outlier detection, architecture overview. https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/health_checking https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/outlier verified 2026-08-02.
6. Istio documentation, Architecture. https://istio.io/latest/docs/ops/deployment/architecture/ verified 2026-08-02.
7. IETF Internet-Draft, Health Check Response Format for HTTP APIs, draft-inadarei-api-health-check. https://datatracker.ietf.org/doc/html/draft-inadarei-api-health-check verified 2026-08-02.

## Code examples

### TypeScript

```typescript
type CheckResult = { name: string; ok: boolean; detail?: string };

interface DependencyChecker {
  name: string;
  check(timeoutMs: number): Promise<CheckResult>;
}

async function withTimeout(
  name: string,
  fn: () => Promise<void>,
  timeoutMs: number
): Promise<CheckResult> {
  const timeout = new Promise<CheckResult>((resolve) =>
    setTimeout(() => resolve({ name, ok: false, detail: "timeout" }), timeoutMs)
  );
  const attempt = fn()
    .then<CheckResult>(() => ({ name, ok: true }))
    .catch<CheckResult>((e) => ({ name, ok: false, detail: String(e) }));
  return Promise.race([attempt, timeout]);
}

class ReadinessEndpoint {
  constructor(private checkers: DependencyChecker[]) {}

  async evaluate(timeoutMs = 500): Promise<{ status: number; body: CheckResult[] }> {
    const results = await Promise.all(
      this.checkers.map((c) => withTimeout(c.name, () => c.check(timeoutMs).then(() => {}), timeoutMs))
    );
    const allOk = results.every((r) => r.ok);
    return { status: allOk ? 200 : 503, body: results };
  }
}

const dbChecker: DependencyChecker = {
  name: "database",
  async check() {
    return { name: "database", ok: true };
  },
};

async function main() {
  const endpoint = new ReadinessEndpoint([dbChecker]);
  const result = await endpoint.evaluate();
  console.log(result.status, JSON.stringify(result.body));
}

main();
```

### Python

```python
import asyncio
import time
from dataclasses import dataclass
from typing import Callable, Awaitable


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""


async def run_checker(
    name: str, fn: Callable[[], Awaitable[None]], timeout_s: float
) -> CheckResult:
    try:
        await asyncio.wait_for(fn(), timeout=timeout_s)
        return CheckResult(name=name, ok=True)
    except asyncio.TimeoutError:
        return CheckResult(name=name, ok=False, detail="timeout")
    except Exception as exc:
        return CheckResult(name=name, ok=False, detail=str(exc))


class ReadinessEndpoint:
    def __init__(self, checkers: dict[str, Callable[[], Awaitable[None]]]):
        self._checkers = checkers

    async def evaluate(self, timeout_s: float = 0.5) -> tuple[int, list[CheckResult]]:
        results = await asyncio.gather(
            *(run_checker(name, fn, timeout_s) for name, fn in self._checkers.items())
        )
        status = 200 if all(r.ok for r in results) else 503
        return status, list(results)


async def check_database() -> None:
    await asyncio.sleep(0)


async def main() -> None:
    endpoint = ReadinessEndpoint({"database": check_database})
    status, results = await endpoint.evaluate()
    print(status, results)


if __name__ == "__main__":
    asyncio.run(main())
```

### Go

```go
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"time"
)

type CheckResult struct {
	Name   string `json:"name"`
	OK     bool   `json:"ok"`
	Detail string `json:"detail,omitempty"`
}

type Checker func(ctx context.Context) error

func runChecker(ctx context.Context, name string, fn Checker, timeout time.Duration) CheckResult {
	cctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	done := make(chan error, 1)
	go func() { done <- fn(cctx) }()

	select {
	case err := <-done:
		if err != nil {
			return CheckResult{Name: name, OK: false, Detail: err.Error()}
		}
		return CheckResult{Name: name, OK: true}
	case <-cctx.Done():
		return CheckResult{Name: name, OK: false, Detail: "timeout"}
	}
}

type ReadinessEndpoint struct {
	checkers map[string]Checker
}

func (e *ReadinessEndpoint) Evaluate(ctx context.Context, timeout time.Duration) (int, []CheckResult) {
	results := make([]CheckResult, 0, len(e.checkers))
	allOK := true
	for name, fn := range e.checkers {
		r := runChecker(ctx, name, fn, timeout)
		if !r.OK {
			allOK = false
		}
		results = append(results, r)
	}
	status := 200
	if !allOK {
		status = 503
	}
	return status, results
}

func checkDatabase(ctx context.Context) error {
	return nil
}

func main() {
	endpoint := &ReadinessEndpoint{checkers: map[string]Checker{"database": checkDatabase}}
	status, results := endpoint.Evaluate(context.Background(), 500*time.Millisecond)
	body, _ := json.Marshal(results)
	fmt.Println(status, string(body))
}
```

Java, Rust, and Swift are omitted from this entry. The pattern's shape,
concurrent dependency checks with a bounded timeout and status aggregation,
is fully idiomatic in the three languages above, and adding three more
translations of the identical structure would not surface a genuinely
different implementation variant.
