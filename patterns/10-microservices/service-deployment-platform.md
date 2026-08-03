---
name: Service Deployment Platform
slug: service-deployment-platform
family: 10-microservices
category: Deployment
aliases: [Deployment Platform, Container Orchestration Platform, Application Platform]
first_described: "Richardson microservices.io deployment pattern catalog, circa 2016"
maturity: canonical
related: [service-instance-per-container, service-instance-per-vm, service-instance-per-host, serverless-deployment, service-registry, server-side-service-discovery, sidecar]
incompatible_with: []
verified: 2026-08-02
---

# Service Deployment Platform

## 1. Name, aliases, and lineage

The canonical name in the microservices deployment literature is Service
Deployment Platform. Chris Richardson's microservices.io pattern catalog
defines it plainly, stating "Use a deployment platform, which is automated
infrastructure for application deployment. It provides a service abstraction,
which is a named, set of highly available (e.g. load balanced) service
instances" (microservices.io, "Service deployment platform" pattern page,
https://microservices.io/patterns/deployment/service-deployment-platform.html,
verified 2026-08-02). The catalog lists three concrete families under this
name. Docker orchestration frameworks such as Docker Swarm Mode and
Kubernetes, serverless platforms such as AWS Lambda, and platform as a
service solutions such as Cloud Foundry and AWS Elastic Beanstalk (same
source, verified 2026-08-02).

The pattern is a level of abstraction above its sibling patterns in the same
family. Service Instance per Container, Service Instance per VM, and Service
Instance per Host each answer one narrower question, what packaging unit
does a single service instance run inside. Service Deployment Platform
answers a broader question, what system is responsible for scheduling,
scaling, healing, and exposing every service instance across the whole
application, regardless of which packaging unit it chose. A reader can
correctly pick Service Instance per Container as the packaging answer and
still have an open question, namely which platform places, restarts, and load
balances those containers. That second question is this pattern.

Aliases in real use, and why each exists.

- **Deployment Platform.** The short form used inside the same catalog entry
  and inside most production conversation, where the microservices-specific
  qualifier is dropped once the context is already established.
- **Container Orchestration Platform.** The phrasing common in container
  tooling circles specifically, emphasising the scheduling and orchestration
  responsibility over the broader deployment abstraction. Kubernetes
  documents itself under exactly this framing, stating "Kubernetes provides
  you with a framework to run distributed systems resiliently. It takes care
  of scaling and failover for your application, provides deployment
  patterns, and more" (Kubernetes documentation, "What is Kubernetes",
  https://kubernetes.io/docs/concepts/overview/, verified 2026-08-02). This
  alias is narrower than the pattern proper because it typically excludes
  serverless and PaaS platforms from its scope, even though both are named
  members of the pattern family in the canonical definition above.
- **Application Platform.** The phrasing used by PaaS vendors such as Cloud
  Foundry and AWS Elastic Beanstalk, who present the same underlying
  responsibility, taking application artifacts and turning them into
  running, load balanced, self healing instances, without exposing the
  orchestration layer to the operator at all.

A related but distinct idea that this entry does not cover in depth is
Service Registry. A deployment platform frequently includes, or is paired
with, a service registry so that instances it schedules can be found by
their callers. The pattern catalog states this relationship directly,
noting "Some deployment platforms provide Service Registry and Server-Side
Discovery. Internally, they may use containers or virtual machines to deploy
services" (microservices.io, same source as above, verified 2026-08-02).
Dimension 13 below expands on exactly which platforms bundle which
capability.

## 2. Problem and context

A team has decomposed an application into a set of independently deployable
services, following one of the decomposition patterns in this family, and
has chosen how a single service instance is packaged, a container, a
virtual machine, or a bare process on a host. Neither decision answers the
operational question that determines whether the system survives contact
with production traffic and production failure. Who places each instance on
a piece of compute. Who notices when an instance dies and replaces it. Who
load balances traffic across the healthy instances of a service. Who
enforces the CPU and memory budget so one runaway service instance cannot
starve its neighbors. Who exposes a uniform way to deploy the next version
of any of the, in a mature microservices system, dozens or hundreds of
independently built services.

Before this pattern is adopted, teams commonly hand roll each of these
responsibilities. A deploy script that SSHes into a fixed list of hosts. A
process supervisor per host with no cross host awareness. A load balancer
configuration hand edited whenever an instance count changes. Each of these
solves one narrow slice of the problem for one team, on one day, and the
approach does not generalize across a growing number of independently owned
services written in different languages, released on different schedules,
by different teams. The problem context that makes a platform the right
answer, rather than a bigger deploy script, is specifically the combination
of many independently deployable units, elastic and unpredictable load, the
expectation of automatic recovery from individual instance failure, and an
organization large enough that the deployment mechanism itself becomes a
shared, reusable piece of infrastructure rather than a one off script owned
by a single team.

## 3. Forces

The forces below are the ones the microservices.io pattern catalog names
directly as the pressures a deployment platform must resolve at once
(microservices.io, "Service deployment platform" pattern page, verified
2026-08-02), restated here with the engineering reasoning behind each.

- **Language and framework diversity.** Services are written using a
  variety of languages, frameworks, and framework versions. A platform that
  only understands one runtime forces every team onto that runtime, which
  defeats one of the stated benefits of microservices, that each service
  can pick the best tool for its own job.
- **Multiple instances per service.** Each service consists of multiple
  service instances for throughput and availability, so the platform's unit
  of work cannot be "the service", it has to be "an instance of the
  service", managed as a fungible, replaceable set.
- **Independent deployability and capacity.** A service must be
  deployable on its own schedule and able to add or remove its own
  instances without touching any other service, so a deploy or a capacity
  change for one service must never require coordinating a deploy or a
  capacity change for another.
- **Instance isolation.** Service instances need to be isolated from one
  another, both so one instance's resource consumption does not degrade a
  neighbor, and so one instance's crash does not take a neighbor down with
  it.
- **Deployment velocity.** Teams need to be able to quickly build and
  deploy a service, which pulls toward automation and away from any manual
  step in the path from a code change to a running instance.
- **Resource constraints.** The platform must constrain the CPU and memory
  each service consumes, or a single service can degrade every other
  service sharing the same compute.
- **Observability.** Operators need to monitor the behavior of each
  service instance individually, which the platform has to make possible by
  exposing per instance health, logs, and metrics rather than only
  aggregate, whole cluster numbers.
- **Reliability.** Deployment itself needs to be reliable, meaning a
  failed or partial deploy should not leave the system in a worse state
  than before the deploy started, which pulls toward rolling updates,
  health checks gating traffic shift, and automated rollback.
- **Cost.** The application has to be deployed as cost effectively as
  possible, which pulls toward bin packing many small instances onto shared
  compute rather than dedicating a whole machine to every instance,
  something the platform has to do automatically rather than by hand.

These forces are genuinely in tension with each other. Bin packing for cost
pushes multiple unrelated services onto the same physical machine, which
works against the isolation force unless the platform also enforces
resource limits and process or container boundaries. Deployment velocity
pushes toward fewer gates in the release path, while reliability pushes
toward more gates, health checks, canary windows, and rollback triggers. A
concrete platform is best understood as a particular, opinionated
resolution of these tensions, not as a neutral tool that satisfies all of
them equally. Kubernetes, for example, resolves the isolation and cost
tension primarily through container based cgroup and namespace isolation
plus a bin packing scheduler, while a PaaS such as Cloud Foundry resolves
the same tension by hiding the placement decision from the operator
entirely.

## 4. Applicability and non-applicability

Reach for a deployment platform when:

- The system already has, or is expected to grow into, more than a handful
  of independently deployable services, each needing its own release
  cadence.
- Traffic or load is variable enough that manual capacity planning per
  service is not sustainable.
- Instances are expected to fail, whether from hardware, from bugs, or from
  planned maintenance, and automatic replacement is required rather than a
  human paged to restart something at 3am.
- More than one team owns services, and a shared, self service deployment
  mechanism removes a bottleneck through a central operations team.
- Multiple languages or runtimes are in use across the service portfolio,
  and a language neutral packaging and scheduling layer, most often the
  container, is wanted as the common interface between every service and
  the platform.

Do NOT reach for a deployment platform, or reach for the lightest possible
one, when:

- The system is a single deployable monolith, or a small number of
  services, small enough that a simple, well understood deploy script and a
  fixed set of hosts is genuinely easier to reason about and to debug than
  a general purpose scheduler. Adopting a platform such as Kubernetes for
  one or two services adds an entire second system, the platform's own
  control plane, that now has to be operated, upgraded, and secured, for a
  problem that a process manager and a load balancer already solve.
- The team operating the system does not have the operational capacity to
  run the platform itself. A self managed Kubernetes cluster has its own
  failure modes, its own upgrade cadence, and its own security surface, and
  a team that adopts it purely to get "the microservices way of doing
  things" without that capacity has traded one operational burden for a
  larger one. This is exactly why managed and serverless variants of the
  pattern exist, see dimension 8.
- Workloads are overwhelmingly stateful, tightly coupled, and rarely
  restarted, for example a small number of long lived databases managed by
  a dedicated database team using well established, non container native
  tooling. Running such workloads on a general purpose orchestration
  platform is possible but frequently fights the platform's assumptions
  about instances being interchangeable and disposable.
- Regulatory or contractual constraints require a specific, certified,
  vendor controlled runtime environment that a general purpose platform
  cannot satisfy, and a narrower managed PaaS or a bespoke deployment
  pipeline is a better fit for that constraint than a general orchestrator.
- The cost of running the platform's own control plane, whether self
  hosted or a managed service fee, exceeds the cost the platform is meant
  to save through better bin packing and automation, which is a real risk
  for small or spiky workloads on the smallest managed tiers.

## 5. Structure

- **Control plane.** The brain of the platform. Accepts a declarative or
  imperative description of what should be running, an API request, a
  configuration file, a container image reference, and reconciles the
  actual state of the cluster toward that description. Holds the source of
  truth for what "correct" looks like right now.
- **Scheduler.** The component inside, or adjacent to, the control plane
  that decides which piece of compute a given service instance should run
  on, based on the instance's declared resource requirements, the current
  load on each candidate machine, and any placement constraints such as
  affinity or anti affinity rules.
- **Worker nodes.** The compute, virtual machines or bare metal, on which
  service instances actually execute. Each worker node runs an agent that
  reports its own health and capacity to the control plane, and that
  receives and executes placement decisions from the scheduler.
- **Service abstraction.** A named, stable identity that fronts a set of
  interchangeable service instances, most commonly backed by an internal
  load balancer or a DNS entry, so that callers address "the service"
  rather than any individual instance, which may be replaced at any moment.
- **Health checker.** The mechanism, whether a liveness probe, a readiness
  probe, or an external health check endpoint, by which the platform
  learns that an instance has failed or become unfit to receive traffic,
  and that triggers the platform's self healing response.
- **Image or artifact registry.** The store from which the platform pulls
  the packaged, versioned unit it is about to run, most commonly a
  container image registry, but in a PaaS the equivalent is a build pack
  or an application artifact store.
- **Resource governor.** The subsystem, cgroups on Linux for container
  platforms, or a comparable mechanism on a PaaS, that enforces the CPU
  and memory limits declared for each instance so that one instance cannot
  starve its neighbors on the same worker node.
- **Deployment operator.** The human or automated pipeline, most often a
  CI/CD system, that submits a new desired state to the control plane
  whenever a new version of a service is prepared for release, and that
  monitors the rollout for success or triggers a rollback on failure.

## 6. ASCII structure diagram

```
                          +-----------------------+
   deployment operator -->|      Control Plane     |
   (CI/CD pipeline)       |  desired state store   |
                          |  reconciliation loop   |
                          |  scheduler              |
                          +-----------+-------------+
                                      |
                     places instances on worker nodes
                                      |
        +-----------------+----------+----------+-----------------+
        |                 |                     |                 |
        v                 v                     v                 v
  +-----------+     +-----------+         +-----------+     +-----------+
  | Worker A  |     | Worker B  |         | Worker C  |     | Worker D  |
  | node agent|     | node agent|         | node agent|     | node agent|
  | +-------+ |     | +-------+ |         | +-------+ |     | +-------+ |
  | |svc-1  | |     | |svc-1  | |         | |svc-2  | |     | |svc-1  | |
  | |inst i1| |     | |inst i2| |         | |inst j1| |     | |inst i3| |
  | +-------+ |     | +-------+ |         | +-------+ |     | +-------+ |
  +-----------+     +-----------+         +-----------+     +-----------+
        ^                 ^                     ^                 ^
        |                 |    health checks    |                 |
        +-----------------+----------+----------+-----------------+
                                      |
                          +-----------v-------------+
                          |  Service Abstraction      |
                          |  svc-1 -> {i1, i2, i3}    |
                          |  svc-2 -> {j1}            |
                          +-----------+---------------+
                                      |
                                   caller
```

## 7. Dynamics

```
Deploy path, new version of svc-1

operator          control plane            scheduler        worker node
   |                    |                        |                |
   | submit new desired |                        |                |
   | state, image v2    |                        |                |
   |------------------->|                        |                |
   |                    | reconcile: current=v1, |                |
   |                    | desired=v2, diff found |                |
   |                    |----------------------->|                |
   |                    |                        | pick worker     |
   |                    |                        | with capacity   |
   |                    |                        |--------------->|
   |                    |                        |                | start v2
   |                    |                        |                | instance
   |                    |                        |    readiness   |
   |                    |                        |<---------------|
   |                    |    v2 healthy,          |                |
   |                    |    add to service       |                |
   |                    |    abstraction          |                |
   |                    |<-----------------------|                |
   |                    | drain and stop one      |                |
   |                    | v1 instance             |                |
   |                    |----------------------->|--------------->|
   |                    |          repeat until all v1 replaced    |
   |   deploy complete   |                        |                |
   |<-------------------|                        |                |

Failure and self healing path, instance crashes

worker node                control plane              scheduler
   |                             |                          |
   | instance i2 process dies    |                          |
   |----------------------------> (missed heartbeat / probe) |
   |                             | remove i2 from service    |
   |                             | abstraction immediately   |
   |                             | reconcile: current has    |
   |                             | 1 fewer instance than     |
   |                             | desired replica count     |
   |                             |------------------------->|
   |                             |                          | pick worker,
   |                             |                          | start replacement
   |                             |<-------------------------|
   |         new instance i4 starts, passes health check,   |
   |         added back into service abstraction            |
```

## 8. Implementation variants

- **Self managed container orchestrator.** The team runs the control plane
  and worker nodes itself, on infrastructure it owns or rents. Kubernetes
  and Docker Swarm Mode are the two named examples in the canonical
  definition. This variant gives the most control over placement policy,
  networking, and upgrade timing, at the cost of the team having to
  operate the orchestrator's own control plane as a critical piece of
  production infrastructure, with its own on call burden.
- **Managed container orchestrator.** A cloud provider runs and patches
  the control plane, and the customer supplies worker node capacity and
  the application workloads, examples being a managed Kubernetes offering
  or Amazon ECS, described by AWS as "a fully managed container
  orchestration service that enables teams to build, manage, and run even
  the most demanding containerized workloads without the complexity of
  infrastructure management" (Amazon Web Services, "Amazon ECS" product
  page, https://aws.amazon.com/ecs/, verified 2026-08-02). This variant
  removes control plane operations from the customer's responsibility
  while keeping the same instance and service abstractions.
- **Fully serverless deployment platform.** The platform owns both the
  control plane and the compute, and the customer supplies only
  application code or a container image plus a trigger, without ever
  provisioning or sizing a worker node. AWS Lambda is the named example in
  the canonical microservices.io definition. Instance count, placement,
  and scaling to zero are handled entirely by the platform. This variant
  gets the lowest cost for spiky or idle heavy workloads and removes
  almost all operational burden, at the cost of constraints on execution
  duration, cold start latency, and the runtime environments supported.
  See the Serverless Deployment pattern entry in this same family for the
  deeper treatment of this specific variant.
- **Platform as a service.** The platform hides the service, instance,
  and scheduling abstractions from the operator almost entirely, and
  exposes a higher level abstraction, an application and a set of bound
  services such as a database. Cloud Foundry and AWS Elastic Beanstalk are
  the named examples. This variant trades the most control for the least
  operational burden, and is frequently the right choice for teams whose
  primary skill is application development rather than infrastructure
  operation.
- **Workload agnostic orchestrator.** A smaller category of platform,
  represented here by HashiCorp Nomad, that deliberately supports more
  than containers as its schedulable unit. Nomad is described by its own
  documentation as "a flexible workload orchestrator that enables an
  organization to easily deploy and manage any containerized or legacy
  application using a single, unified workflow" (HashiCorp, "What is
  Nomad", https://developer.hashicorp.com/nomad/docs/what-is-nomad,
  verified 2026-08-02). This variant is a deliberate response to the
  force named in dimension 3 about language and framework diversity,
  extended to include workloads that were never containerized at all,
  such as a legacy Java application run directly on a JVM driver,
  alongside newer containerized services, under one scheduler.

## 9. Known production uses

- **Kubernetes at Google and across the Cloud Native Computing
  Foundation.** Kubernetes was open sourced by Google in 2014, and the
  project's own documentation states it "combines over 15 years of
  Google's experience running production workloads at scale with
  best-of-breed ideas and practices from the community" (Kubernetes
  documentation, "What is Kubernetes",
  https://kubernetes.io/docs/concepts/overview/, verified 2026-08-02). The
  Cloud Native Computing Foundation accepted Kubernetes at the incubating
  maturity level on March 10, 2016, and it advanced to graduated status,
  the foundation's highest maturity designation, on March 6, 2018 (Cloud
  Native Computing Foundation, "Kubernetes" project page,
  https://www.cncf.io/projects/kubernetes/, verified 2026-08-02).
- **HashiCorp Nomad at PagerDuty, Target, Roblox, and eBay.** HashiCorp's
  own documentation lists PagerDuty, Target, Citadel, Trivago, SAP,
  Pandora, Roblox, and eBay among organizations running Nomad in
  production, and states that Nomad "has been proven to scale to cluster
  sizes that exceed 10,000 nodes in real-world production environments,"
  alongside published benchmark runs of 1 million containers in 2016 and 2
  million containers in 2020 (HashiCorp, "What is Nomad",
  https://developer.hashicorp.com/nomad/docs/what-is-nomad, verified
  2026-08-02).
- **Amazon ECS as the managed variant of this pattern.** AWS positions
  Amazon ECS as letting teams "easily build, manage, and run containerized
  applications at any scale" without operating the orchestrator's own
  control plane (Amazon Web Services, "Amazon ECS" product page,
  https://aws.amazon.com/ecs/, verified 2026-08-02), making it the named,
  widely deployed representative of the managed container orchestrator
  variant described in dimension 8.
- **AWS Lambda as the named serverless example in the canonical
  definition.** The microservices.io pattern catalog names AWS Lambda
  directly as an example of a serverless deployment platform in the same
  sentence that defines this pattern (microservices.io, "Service
  deployment platform" pattern page,
  https://microservices.io/patterns/deployment/service-deployment-platform.html,
  verified 2026-08-02), establishing it as a canonical production instance
  of the fully serverless variant.

## 10. Consequences

Positive.

- A single, learnable, reusable mechanism exists for deploying every
  service, rather than each team inventing and maintaining its own deploy
  tooling, which is a direct answer to the deployment velocity force in
  dimension 3.
- Automatic instance replacement on failure removes a large class of
  paged incidents, "the process died and nobody restarted it", that would
  otherwise require a human response at any hour.
- Resource limits enforced by the platform allow safe bin packing of many
  small services onto shared compute, improving utilization and lowering
  cost compared to dedicating a machine per service.
- A uniform service abstraction decouples callers from the churn of
  individual instances being started, stopped, and replaced, which is the
  precondition the Server-Side Service Discovery and Service Registry
  patterns build on.
- Rolling, health checked deployment reduces the blast radius of a bad
  release, because the platform can detect a failing new version and halt
  or reverse the rollout before every instance of a service has been
  replaced.

Negative.

- The platform itself becomes a new, critical piece of infrastructure. An
  outage in the control plane, whether self managed or a managed service
  provider's outage, can take down the ability to deploy, scale, or even
  self heal every service that depends on it, which is a systemic risk
  that did not exist, at this scope, before the platform was adopted.
- Operational complexity increases sharply for a self managed variant.
  Learning, securing, and upgrading a general purpose orchestrator such as
  Kubernetes is itself a considerable, ongoing engineering investment,
  independent of and in addition to the applications the platform runs.
- The platform's abstractions leak. Debugging a networking issue, a
  scheduling decision, or a resource throttling event requires operators
  to understand the platform's internals, not only their own application
  code, which requires more specialist skill from on call engineers.
- Cost can move in either direction depending on workload shape. Bin
  packing saves money for many small, variably loaded services, but the
  platform's own control plane and, for managed variants, its service fee,
  can make the smallest workloads more expensive than a single, simple
  virtual machine.
- Vendor and platform lock in risk grows with the depth of platform
  specific features used, such as a PaaS's proprietary service binding
  mechanism or a managed orchestrator's non standard extensions, which can
  make migrating to a different platform later a substantial project of
  its own.

## 11. Failure modes and misuse

- **Symptom.** New instances repeatedly start and are killed within
  seconds, in a visible restart loop.
  **Cause.** The health check configured on the platform, whether a
  liveness probe or an equivalent, is checking a condition the application
  cannot satisfy quickly enough at startup, commonly because the check
  begins before a slow dependency, such as a database connection pool, has
  finished initializing.
  **Fix.** Separate the readiness check, which gates traffic, from the
  liveness check, which gates restart, and give the readiness check a
  startup grace period, or an explicit startup probe, long enough for real
  initialization to complete.
- **Symptom.** One service's instances are frequently evicted or
  throttled even though the cluster overall reports spare capacity.
  **Cause.** The service declared no resource requests or limits, or
  declared them far below its real usage, so the scheduler under packs the
  node it lands on and a neighboring, correctly declared service then
  exceeds its own limit and triggers eviction pressure on the whole node.
  **Fix.** Declare accurate CPU and memory requests based on observed
  usage, and set limits that reflect genuine measured maximums rather than
  a guess, then monitor actual usage against the declared numbers over
  time and adjust.
- **Symptom.** A rolling deployment replaces every healthy instance of a
  service with a broken new version before anyone notices.
  **Cause.** The readiness check used to gate the rollout only verifies
  that the process is listening on a port, not that the new version is
  functionally correct, so a version with a broken business logic path
  still reports ready and the platform happily proceeds to replace every
  instance.
  **Fix.** Make the readiness check exercise a representative code path,
  and pair the platform's rollout mechanism with an automated canary
  analysis or a manual bake time before proceeding to replace the
  remaining instances.
- **Symptom.** The platform's control plane itself becomes slow or
  unresponsive during an incident, and operators cannot deploy a fix or
  even scale up capacity to absorb load.
  **Cause.** A high rate of reconciliation events, commonly triggered by a
  large number of services flapping between healthy and unhealthy at
  once, overwhelms the control plane's own capacity, which was sized for
  steady state operation rather than a cascading, cluster wide incident.
  **Fix.** Size and, where the platform allows it, horizontally scale the
  control plane independently of the workload it manages, and rate limit
  or circuit break the reconciliation loop's response to a sudden burst of
  state changes so a cascading failure in the workload does not also take
  down the operator's ability to intervene.
- **Symptom.** A team treats the deployment platform as a substitute for
  application level resilience, and the application falls over the first
  time a dependency is slow rather than unavailable.
  **Cause.** Misuse of the pattern's scope. The platform restarts a dead
  process and reroutes traffic away from a failed health check, but it has
  no visibility into, and cannot fix, an application that hangs
  indefinitely waiting on a slow downstream call, because from the
  platform's point of view that instance still looks alive.
  **Fix.** Pair the deployment platform with application level resilience
  patterns, timeouts, retries with backoff, and circuit breakers, inside
  the service itself, since the platform's self healing operates at the
  instance level and cannot substitute for request level resilience inside
  a single, still nominally healthy instance.

## 12. Trade-off matrix

| Force | Self managed orchestrator (Kubernetes, Nomad) | Managed orchestrator (Amazon ECS) | Fully serverless (AWS Lambda) | PaaS (Cloud Foundry, Elastic Beanstalk) |
|---|---|---|---|---|
| Operational burden | Highest, team runs the control plane | Medium, provider runs control plane, team runs workers or a serverless capacity mode | Lowest, provider runs everything | Low, provider runs everything, higher level abstraction |
| Control over placement and networking | Highest | Medium | Lowest | Lowest |
| Language and runtime flexibility | Highest, any container or, for Nomad, non containerized workload | High, container based | Constrained to supported runtimes and execution duration | Constrained to supported build packs or runtimes |
| Cost efficiency for spiky, idle heavy load | Requires manual tuning to avoid paying for idle capacity | Improved with a serverless capacity option, still generally provisioned | Highest, scales to zero automatically | Medium, some providers offer scale to zero |
| Time to first production deploy | Slowest, cluster must be stood up first | Fast, no cluster to build | Fastest, only code and a trigger needed | Fast, push code and bind services |
| Vendor lock in risk | Lowest for the orchestration layer itself, portable across clouds | Medium, tied to the managed service's API | Highest, execution model and triggers are provider specific | High, proprietary service binding and build pack model |

## 13. Related and incompatible patterns

- **Service Instance per Container, Service Instance per VM, Service
  Instance per Host.** These three patterns answer the narrower packaging
  question that this pattern's platform then schedules and operates. A
  deployment platform is typically built around one of these as its
  native unit, Kubernetes and Docker Swarm Mode around the container, and
  a small number of legacy platforms around the VM or the host. Choosing
  this pattern does not remove the need to also choose a packaging
  pattern, the two compose.
- **Serverless Deployment.** The fully serverless variant of this
  pattern, see dimension 8, is a large enough topic in its own right that
  this repository carries it as a separate entry. Read that entry for the
  execution model, cold start, and duration limit details specific to
  that variant.
- **Service Registry and Server-Side Service Discovery.** The pattern
  catalog states directly that "some deployment platforms provide Service
  Registry and Server-Side Discovery" (microservices.io, "Service
  deployment platform" pattern page, verified 2026-08-02). Kubernetes
  bundles both responsibilities, its internal DNS and Service resources
  function as a registry and as server side discovery at once. A platform
  that does not bundle these, particularly a bare set of virtual machines
  with no orchestrator, requires the application or a separate piece of
  infrastructure to provide them, which is the case this repository's
  Service Registry and Server-Side Service Discovery entries treat in
  depth.
- **Sidecar and Ambassador.** Both patterns depend on the deployment
  platform supporting more than one container, or more than one process,
  per scheduled unit, and on the platform providing a shared network
  namespace or an equivalent between them. Kubernetes's Pod abstraction is
  the canonical enabling mechanism for both patterns in a container based
  deployment platform.
- **Circuit Breaker, Retry, and other application level resilience
  patterns.** As covered in dimension 11's last failure mode, these
  patterns are not provided by the deployment platform and are not made
  unnecessary by it. They compose with this pattern rather than
  substitute for it, the platform handles instance level failure, these
  patterns handle request level failure inside a still healthy instance.
- **No named incompatibility.** This pattern is compatible with every
  other pattern in this family. It is, by design, an operational layer
  underneath the application's own architecture, and no combination of
  application level patterns is known to conflict with the choice of
  deployment platform underneath them.

## 14. Refactoring path in and out

Introducing a deployment platform into a system that does not yet have
one.

1. Establish the packaging unit first. Pick and apply one of Service
   Instance per Container, Service Instance per VM, or Service Instance per
   Host, since the deployment platform needs a stable unit to schedule.
   Container is the overwhelmingly common choice for new adoption, given
   its portability across every major platform named in this entry.
2. Containerize, or otherwise package, a single, low risk service first,
   rather than every service at once. Deploy it onto the new platform
   alongside the existing deployment mechanism, running both in parallel,
   so the platform can be validated under real but limited traffic.
3. Establish observability for the new platform before moving more
   traffic onto it. Confirm that per instance logs, metrics, and health
   status are visible and alertable, since operators will lose the old
   deployment mechanism's familiar signals once the migration proceeds.
4. Migrate services incrementally, service by service, favoring services
   with simpler dependency graphs and fewer stateful concerns first. Use
   the Strangler Application pattern from this same family where a service
   itself needs to be incrementally decomposed as part of the same
   migration.
5. Decommission the old deployment mechanism only after every service that
   depended on it has been migrated and has run successfully on the new
   platform through at least one full release cycle, so a rollback path
   exists for the length of the migration.

Removing a deployment platform, or moving off one variant onto a simpler
one.

1. Confirm the trigger. The most common honest reasons to remove or
   downgrade a platform are operational burden that exceeds the team's
   capacity, established in dimension 4's non-applicability list, or a
   workload profile that has shrunk to a size where a general purpose
   orchestrator's overhead no longer earns its cost.
2. Inventory every platform specific feature in active use, custom
   scheduling rules, platform specific autoscaling policies, proprietary
   service bindings on a PaaS, since each one becomes migration work
   rather than a simple lift and shift.
3. Move to the simplest platform variant that still satisfies the forces
   in dimension 3 for the remaining workload, rather than removing the
   pattern entirely, since the underlying problem, multiple instances,
   health checking, and load balancing, does not go away merely because
   the team no longer wants to operate a general purpose orchestrator.
4. Migrate incrementally in the same direction as the introduction path,
   service by service, with the old platform kept running in parallel
   until the new, simpler one has proven itself under real traffic.

## 15. Testing and verification

What becomes easier because of this pattern:

- Fault injection and resilience testing becomes tractable, because the
  platform already exposes a mechanism to kill an instance deliberately
  and observe whether the service abstraction correctly routes around it,
  without the test needing to know which specific instance or machine is
  involved.
- Rollout correctness can be tested in isolation from application logic,
  by deploying a deliberately broken version of a service and confirming
  the platform's readiness gating and rollback behavior actually halts the
  rollout, since the platform's own behavior is now a piece of testable
  infrastructure rather than an assumption.
- Resource limit enforcement can be verified directly, by deploying a
  deliberately memory hungry test workload and confirming the platform
  terminates or throttles it at the declared limit rather than allowing it
  to degrade neighboring workloads.

What becomes harder because of this pattern:

- End to end integration tests that previously ran against a fixed,
  well known set of hosts now have to account for instances that may be
  rescheduled to different, ephemeral network locations mid test, which
  pushes tests toward addressing the service abstraction rather than any
  specific instance address.
- Reproducing a production incident locally becomes harder, because the
  scheduler's specific placement decision, the exact resource pressure on
  a specific node, and the exact sequence of health check failures are
  difficult to recreate outside the real platform, which pushes teams
  toward running a scaled down but structurally identical version of the
  platform in a staging environment rather than mocking it away entirely.
- Test doubles for "the platform" itself are rarely useful. Unlike a
  database or a message broker, the deployment platform is closer to the
  execution environment than to a dependency the application calls, so
  most teams verify platform behavior against a real, if smaller,
  instance of the platform, commonly a local single node cluster for a
  container orchestrator, rather than mocking the platform's API.

## 16. Observability signals

- **Per instance health status over time.** How many instances of each
  service are currently healthy, unhealthy, or in a restart loop, tracked
  as a time series rather than a single point in time snapshot, since a
  platform that reports "all healthy right now" can still be masking a
  service that has restarted forty times in the last hour.
- **Scheduling latency.** The time between the platform accepting a
  request to place a new instance and that instance actually reaching a
  healthy, ready state. A healthy platform keeps this in the low single
  digit seconds to low minutes range depending on image pull time. A
  rising trend here is an early signal of either resource exhaustion on
  the cluster or a slow, bloated deployment artifact.
- **Control plane resource usage and API latency.** The control plane's
  own CPU, memory, and API request latency, since the control plane is
  itself a piece of software that can degrade under load, and degradation
  here affects every service on the platform at once rather than one
  service in isolation.
- **Resource request versus actual usage per service.** The gap between
  what each service declared it needs, its CPU and memory request, and
  what it actually consumes in steady state. A large, persistent gap in
  either direction, over provisioned or under provisioned, is a direct
  signal that the declared limits from dimension 11 need to be revisited.
- **Deployment success and rollback rate.** The fraction of deployments
  that complete successfully versus the fraction that trigger an
  automatic or manual rollback, tracked per service and in aggregate. A
  healthy platform shows a very high success rate with a low, well
  understood tail of legitimate rollbacks. A rising rollback rate across
  many services at once is more likely to indicate a platform level
  problem than many simultaneous, unrelated application bugs.

A healthy dashboard shows a stable or slowly rising instance count that
tracks declared replica counts closely, scheduling latency in a tight,
predictable band, and a rollback rate near zero. A failing platform shows a
sawtooth instance count as instances repeatedly crash and restart, rising
scheduling latency as the cluster runs out of placeable capacity, and a
control plane whose own API latency is climbing, which is the leading
indicator that the operator's ability to intervene is itself degrading.

## 17. Security and privacy implications

The deployment platform sits directly in the path of every service's
lifecycle, which makes its own access control surface a high value
target. A credential that can submit a new desired state to the control
plane can deploy arbitrary code onto any node the platform schedules onto,
so the platform's own authentication and authorization mechanism, role
based access control on Kubernetes, IAM policy on Amazon ECS, deserves the
same scrutiny as production database credentials, not less.

The platform's shared compute model means workloads from different
services, and on a multi tenant cluster potentially different teams, run
on the same physical or virtual machine, separated only by the isolation
mechanisms named in dimension 5, primarily container namespaces and
cgroups for the container based variants. A container escape
vulnerability, or a misconfigured privileged container, threatens every
co located workload on that node, not only the compromised one, which is
a materially different blast radius than a single, dedicated virtual
machine per service would carry.

Secrets management is a direct platform concern rather than an
application concern once a deployment platform is in place, because the
platform is the mechanism that delivers a database password, an API key,
or a certificate into a running instance. A platform's built in secret
storage, if used without an additional layer of encryption at rest and
tight access control, can become the single highest value target in the
entire system, since compromising the platform's secret store compromises
every service that platform runs. This repository is silent on which
specific secrets manager to pair with a given platform, since that choice
is deployment specific rather than a property of this pattern itself.

Image or artifact provenance is a supply chain concern the platform
inherits directly. A deployment platform will faithfully and efficiently
deploy a compromised container image or artifact exactly as reliably as
it deploys a legitimate one, so the platform's trust in its image
registry, and any signature verification the platform enforces before
scheduling an image, is part of the security boundary of the whole
system, not an optional add on.

## 18. References

- microservices.io, "Service deployment platform" pattern page, Chris
  Richardson, https://microservices.io/patterns/deployment/service-deployment-platform.html,
  verified 2026-08-02.
- microservices.io, "Service per Container" pattern page, Chris
  Richardson, https://microservices.io/patterns/deployment/service-per-container.html,
  verified 2026-08-02.
- Kubernetes documentation, "What is Kubernetes",
  https://kubernetes.io/docs/concepts/overview/, verified 2026-08-02.
- Cloud Native Computing Foundation, "Kubernetes" project page,
  https://www.cncf.io/projects/kubernetes/, verified 2026-08-02.
- HashiCorp, "What is Nomad",
  https://developer.hashicorp.com/nomad/docs/what-is-nomad, verified
  2026-08-02.
- Amazon Web Services, "Amazon ECS" product page,
  https://aws.amazon.com/ecs/, verified 2026-08-02.
- Docker documentation, "Multi-service containers",
  https://docs.docker.com/config/containers/multi-service_container/,
  verified 2026-08-02.

## Code examples

Three languages are provided. Go and TypeScript are used because both are
common client languages for calling a deployment platform's control plane
API. Python is used because it is the most common language for writing
the operational tooling, health check scripts and deployment automation,
that sits around a deployment platform. All three examples model the same
concept, a minimal client against a deployment platform's declarative
desired state API, deliberately kept free of any specific vendor SDK so
the example illustrates the pattern's structure rather than one product's
API surface.

### Go

```go
package main

import "fmt"

// DesiredState is the declarative shape a deployment platform's control
// plane reconciles the cluster toward.
type DesiredState struct {
	Service       string
	Image         string
	ReplicaCount  int
	CPURequestM   int
	MemRequestMiB int
}

// ClusterState is a minimal view of what the platform reports as running.
type ClusterState struct {
	HealthyReplicas int
}

// Reconciler is a deliberately tiny stand in for a deployment platform's
// control plane reconciliation loop.
type Reconciler struct {
	desired map[string]DesiredState
	actual  map[string]ClusterState
}

func NewReconciler() *Reconciler {
	return &Reconciler{
		desired: make(map[string]DesiredState),
		actual:  make(map[string]ClusterState),
	}
}

func (r *Reconciler) Submit(state DesiredState) {
	r.desired[state.Service] = state
}

func (r *Reconciler) ReportHealthy(service string, healthy int) {
	r.actual[service] = ClusterState{HealthyReplicas: healthy}
}

// Reconcile returns how many replicas still need to be started or stopped
// to match the desired state, the core loop every deployment platform runs.
func (r *Reconciler) Reconcile(service string) int {
	desired, ok := r.desired[service]
	if !ok {
		return 0
	}
	actual := r.actual[service]
	return desired.ReplicaCount - actual.HealthyReplicas
}

func main() {
	r := NewReconciler()
	r.Submit(DesiredState{
		Service:       "checkout",
		Image:         "registry.example/checkout:v2",
		ReplicaCount:  3,
		CPURequestM:   250,
		MemRequestMiB: 256,
	})
	r.ReportHealthy("checkout", 1)

	delta := r.Reconcile("checkout")
	fmt.Printf("checkout needs %d more healthy replicas\n", delta)
}
```

Compiled and run with `go run main.go` in this repository's environment.
Output confirmed. `checkout needs 2 more healthy replicas`.

### TypeScript

```typescript
interface DesiredState {
  service: string;
  image: string;
  replicaCount: number;
  cpuRequestMilli: number;
  memRequestMiB: number;
}

interface ClusterState {
  healthyReplicas: number;
}

class Reconciler {
  private desired = new Map<string, DesiredState>();
  private actual = new Map<string, ClusterState>();

  submit(state: DesiredState): void {
    this.desired.set(state.service, state);
  }

  reportHealthy(service: string, healthy: number): void {
    this.actual.set(service, { healthyReplicas: healthy });
  }

  // Reconcile mirrors a deployment platform's core loop, comparing
  // desired replica count against currently healthy instances.
  reconcile(service: string): number {
    const desired = this.desired.get(service);
    if (!desired) {
      return 0;
    }
    const actual = this.actual.get(service) ?? { healthyReplicas: 0 };
    return desired.replicaCount - actual.healthyReplicas;
  }
}

const reconciler = new Reconciler();
reconciler.submit({
  service: "checkout",
  image: "registry.example/checkout:v2",
  replicaCount: 3,
  cpuRequestMilli: 250,
  memRequestMiB: 256,
});
reconciler.reportHealthy("checkout", 1);

const delta = reconciler.reconcile("checkout");
console.log(`checkout needs ${delta} more healthy replicas`);
```

Compiled with `npx tsc --strict --noEmit` in this repository's environment
with zero errors, then run under Node after transpilation, producing the
expected line, `checkout needs 2 more healthy replicas`.

### Python

```python
from dataclasses import dataclass


@dataclass
class DesiredState:
    service: str
    image: str
    replica_count: int
    cpu_request_milli: int
    mem_request_mib: int


@dataclass
class ClusterState:
    healthy_replicas: int


class Reconciler:
    """A minimal stand in for a deployment platform's reconciliation loop."""

    def __init__(self) -> None:
        self._desired: dict[str, DesiredState] = {}
        self._actual: dict[str, ClusterState] = {}

    def submit(self, state: DesiredState) -> None:
        self._desired[state.service] = state

    def report_healthy(self, service: str, healthy: int) -> None:
        self._actual[service] = ClusterState(healthy_replicas=healthy)

    def reconcile(self, service: str) -> int:
        desired = self._desired.get(service)
        if desired is None:
            return 0
        actual = self._actual.get(service, ClusterState(healthy_replicas=0))
        return desired.replica_count - actual.healthy_replicas


if __name__ == "__main__":
    reconciler = Reconciler()
    reconciler.submit(
        DesiredState(
            service="checkout",
            image="registry.example/checkout:v2",
            replica_count=3,
            cpu_request_milli=250,
            mem_request_mib=256,
        )
    )
    reconciler.report_healthy("checkout", 1)

    delta = reconciler.reconcile("checkout")
    print(f"checkout needs {delta} more healthy replicas")
```

Run with `python3 reconciler.py` in this repository's environment. Output
confirmed. `checkout needs 2 more healthy replicas`.

Java and Rust are omitted for this entry. The pattern's core idea, a
declarative desired state reconciled against observed actual state, is
fully captured by the three examples above, and a fourth or fifth
language would repeat the identical logic without adding a genuinely
different idiomatic angle the way, for example, a language with first
class coroutines changes the shape of an async pattern. Swift, Java, and
Rust versions were considered and set aside for this reason rather than
for lack of toolchain availability.
