---
name: Service Instance per Container
slug: service-instance-per-container
family: 10-microservices
category: Deployment
aliases: [Single Service Instance per Container, Container per Service, One Process per Container]
first_described: "Richardson microservices.io deployment pattern catalog, circa 2016, building on Docker Inc best-practice guidance from 2013 to 2014"
maturity: canonical
related: [sidecar, ambassador, adapter, service-instance-per-host, service-instance-per-vm, serverless-deployment]
incompatible_with: [big-ball-of-mud-container, multi-process-supervisor-container]
verified: 2026-08-02
---

# Service Instance per Container

## 1. Name, aliases, and lineage

The canonical name in the microservices deployment literature is Service Instance
per Container, sometimes shortened to Service per Container. Chris Richardson's
microservices.io pattern catalog lists it under Deployment patterns, contrasted
directly with Service Instance per Host and Service Instance per VM
([microservices.io, "Service per Container" pattern page](https://microservices.io/patterns/deployment/service-per-container.html),
verified 2026-08-02). The catalog frames it as one of a small family of
deployment patterns that answer the same question, how many service instances
and of what kind run on a given piece of compute, with the container as the unit
of packaging and scheduling.

The pattern predates its own catalog name. Docker's own documentation carried
the underlying discipline years earlier as a plain best practice rather than a
named pattern. "It's best practice to separate areas of concern by using one
service per container." The same page allows a controlled exception. "It's ok to
have multiple processes, but to get the most benefit out of Docker, avoid one
container being responsible for multiple aspects of your overall application"
([Docker documentation, "Multi-service containers"](https://docs.docker.com/config/containers/multi-service_container/),
verified 2026-08-02). This is the container-runtime articulation of the pattern,
older than the microservices-specific naming, and it is the reason most
engineers meet this idea as a Docker convention before they ever meet it as a
named architectural pattern.

Aliases in real use, and why each exists.

- **Single Service Instance per Container.** The fuller phrasing used inside
  Richardson's own pattern language when he needs to distinguish it from
  patterns that place multiple instances of the same service, or several
  different services, inside one container.
- **Container per Service.** The inverted phrasing common in platform-engineering
  and Kubernetes discussion, emphasising the packaging decision from the
  service's point of view rather than the container's.
- **One Process per Container.** The Docker-native phrasing, tracking the
  process-level framing in the Docker documentation quoted above rather than the
  service-level framing. This alias is slightly narrower than the pattern proper,
  because a single service instance sometimes legitimately runs as more than one
  OS process while still being one deployable unit, for example a web server
  process and a background worker thread pool started by the same entrypoint
  script. The pattern cares about the deployable unit, not strictly about the
  process count.

A related but distinct idea that this entry does not cover in depth, and that
should not be confused with it, is the Sidecar pattern. Sidecar places a SECOND
container alongside the primary service container inside the same Pod or task,
to add a cross-cutting concern such as a proxy, a log shipper, or a certificate
rotator. Service Instance per Container is the packaging rule that makes Sidecar
possible in the first place, because Sidecar depends on each concern already
being isolated into its own container rather than compiled into the service
process. See dimension 13 for the full relationship.

## 2. Problem and context

A team is moving an application, or building a new one, on top of microservices,
and has to decide the packaging and scheduling unit for each service instance.
Three shapes are on the table in practice, and the choice made here ripples into
every later decision about scaling, isolation, and operations.

- Multiple service instances, possibly of different services, share one host or
  one VM, coordinated by a process supervisor or a script.
- Each service instance gets its own VM.
- Each service instance gets its own container.

The problem context that makes this a real decision, not an academic one, has
several concrete symptoms visible in a codebase or a runbook before the pattern
is adopted.

A team runs, say, an order service and a fraud-check service on the same set of
VMs, started by the same init system, sharing the same filesystem. A memory leak
in the fraud-check service starves the order service of RAM on the same host,
and an operator restarting the fraud-check service risks restarting the order
service too if the restart script is not surgical. The two services also want
different language runtimes over time, the order service on a JVM upgrade path
the fraud-check service is not ready for, and upgrading the shared host forces
the two teams to coordinate a change neither of them asked for. Scaling is
coarse. adding capacity for the order service under a traffic spike means adding
a whole VM that also carries fraud-check capacity nobody needed. And packaging
is bespoke. each service on the shared host has its own deployment script
written against that host's particular OS version and installed libraries,
which is exactly the "works on my machine" gap that containers exist to close.

Per-VM instances solve the isolation and independent-scaling problems, at the
cost of VM boot time measured in minutes, a heavier resource footprint per
instance because a VM carries its own kernel and OS image, and slower iteration
because building and distributing a VM image is a heavier pipeline than building
and distributing a container image.

The context in which Service Instance per Container becomes the right answer is
this. The organisation already has, or is willing to adopt, container tooling
(a container runtime, an image registry, and typically an orchestrator such as
Kubernetes, Amazon ECS, or a platform-as-a-service built on containers), the
services are numerous enough and independently owned enough that per-service
isolation earns its keep, and the team wants VM-level isolation without VM-level
cost. Container images share the host kernel, so startup is seconds rather than
minutes and the per-instance memory overhead is close to the size of the process
itself rather than a whole OS image, while the container still gets its own
filesystem, its own process namespace, and enforceable CPU and memory limits.

## 3. Forces

- **Isolation.** Favoured, strongly. Filesystem, process tree, and resource
  limits are per container, so a runaway process in one service cannot starve
  another the way co-located processes on a bare VM can.
- **Startup latency and elasticity.** Favoured. A container starts in the time it
  takes to start the process inside it, typically under a second for a compiled
  binary and a few seconds for a runtime that needs to warm up, because there is
  no kernel boot involved. This is what makes horizontal autoscaling of
  individual services practical.
- **Resource overhead per instance.** Favoured relative to a VM, sacrificed
  relative to sharing a host. Each container still carries its own copy of a
  language runtime and its dependencies in the image, and the orchestrator's own
  per-container bookkeeping (a network namespace, a cgroup, health-check probing)
  is not free.
- **Operational uniformity.** Favoured. Every service, regardless of its internal
  language or framework, is deployed, scaled, restarted, and health-checked
  through the same container lifecycle API, which is the payoff an orchestrator
  is built to exploit.
- **Technology heterogeneity across services.** Favoured. A container image
  bundles its own runtime, so the order service can run on one language version
  and the fraud-check service on a completely different language, with no shared
  host to negotiate.
- **Blast radius of a bad deploy.** Favoured for containment, and this is
  frequently the deciding force in an incident postmortem. Rolling out a broken
  image affects the instances of that one service, not co-located neighbours.
- **Image and supply-chain surface area.** Sacrificed. One image per service
  multiplies the number of artefacts that must be built, scanned, signed, and
  patched. A vulnerability in a shared base layer now has to be remediated across
  many images at once instead of one shared host.
- **Cross-service resource efficiency.** Sacrificed relative to sharing a host,
  because strict per-service isolation means the scheduler cannot opportunistically
  pack unrelated processes into the idle capacity of a single running process the
  way a general-purpose multi-tenant host can, although a bin-packing scheduler
  such as Kubernetes recovers a large part of this efficiency across many small
  containers on shared nodes.
- **Cognitive load of the deployment topology.** Sacrificed at small scale,
  favoured at large scale. A team with three services and one host finds
  container-per-service adds ceremony, an image registry, a manifest per
  service, health-check wiring, for very little isolation gain. A team with
  fifty services finds the uniform container contract is what keeps the topology
  understandable at all.
- **Coupling to the orchestrator's scheduling model.** Sacrificed. The pattern
  is close to meaningless without something that schedules and restarts
  containers, so adopting it also means adopting an orchestrator's operational
  model, its manifest format, and its failure semantics.

A pattern that gave up nothing would not be a decision. The price here is paid
in artefact count, base-image maintenance burden, and dependence on an
orchestration layer.

## 4. Applicability and non-applicability

Reach for Service Instance per Container when the following hold.

- The system is decomposed into multiple independently deployable services, and
  those services need to scale, restart, and fail independently of one another.
- Container tooling, an image registry, and an orchestrator (or a managed
  platform built on one, such as Amazon ECS, Google Cloud Run, or a Kubernetes
  distribution) are already in place or are a deliberate, funded adoption.
- Services are, or will become, heterogeneous in language or runtime, and a
  shared host's fixed toolchain would become a coordination tax between teams.
- Fast, predictable startup matters, for autoscaling under load, for fast
  rolling deploys, or for scale-to-zero patterns.
- The organisation has the operational maturity, or is building it, to run image
  scanning, base-image patching, and registry hygiene as ongoing practices, not
  one-time setup.

Do NOT reach for this pattern in the following cases, and the reason in each
case is the load-bearing part.

- **A monolith with no independent deployability requirement.** If the whole
  application deploys and scales as one unit, splitting it into containers per
  internal module buys container-management overhead with no isolation payoff,
  because a failure in one module still takes the shared process down with it.
  Package the monolith as a single container instead, which is a different,
  legitimate pattern, not this one.
- **A tiny number of services with a tiny operations team and no orchestrator.**
  Two or three services hand-run with `docker run` on a single box gain little
  isolation over a well-supervised set of systemd units, and lose the
  restart-and-reschedule guarantees an orchestrator would have given them in
  exchange for the added artefact and registry overhead. Either commit to an
  orchestrator or stay with Service Instance per Host until the service count
  justifies the jump.
- **Extremely latency-sensitive, colocated communication where even a loopback
  network hop across container network namespaces is measurable.** Some
  high-frequency trading and specialised real-time systems put related logic in
  one process specifically to avoid any inter-process hop. Splitting such logic
  into separate containers to satisfy this pattern would directly work against
  the system's actual requirement.
- **Genuinely tightly coupled helper processes that exist only to serve one
  primary process and share its lifecycle exactly.** A log-shipping agent, a
  service-mesh proxy, or a secrets-fetching init step that must start, stop, and
  fail together with the primary process is the Sidecar or Adapter pattern's
  territory, running as an additional container inside the SAME Pod or task,
  not a separate independently-scheduled service instance. Applying Service
  Instance per Container naively here, giving the sidecar its own independent
  deployment and scaling lifecycle, breaks the co-location guarantee the helper
  actually needs.
- **Workloads better served by a fully managed serverless function model**,
  where the platform's own per-invocation isolation already gives what a
  container would give, and paying for an always-warm container plus
  orchestrator manifests is unjustified operational weight for a workload with
  sparse, bursty, sub-second invocations. Serverless Deployment is the named
  alternative for that shape, see dimension 12.
- **A stateful process that cannot tolerate the ephemeral-filesystem assumption
  most container platforms make**, such as a primary database instance, without
  a deliberate persistent-volume design. The pattern still applies, but only
  once the team has explicitly designed the storage layer for it; applying it
  by default to a database because "everything is a container now" is a
  frequent and expensive mistake.

## 5. Structure

Four participants, named by the role they play in the deployment topology
rather than by a generic infrastructure term.

- **Service.** The unit of independent business functionality being deployed,
  for example an order service or a fraud-check service. It is the thing that
  has its own release cadence, its own on-call ownership, and its own scaling
  target.
- **Container Image.** The immutable, versioned artefact that packages one
  service's code, its language runtime, and its dependencies into a single
  filesystem layer stack, built once and run unmodified across every
  environment. The image is the boundary this pattern draws around a service,
  never spanning two services in one image.
- **Container Instance.** A running instantiation of a Container Image,
  isolated by the container runtime's namespaces and cgroups, holding exactly
  one Service's process (or, in the process-group exception noted in dimension
  1, one Service's tightly related process group). Multiple Container Instances
  of the same image are how one Service scales horizontally.
- **Scheduler or Orchestrator.** The control plane that decides which Container
  Instances run where, restarts a failed one, and enforces the resource limits
  attached to it. Kubernetes' kube-scheduler, Amazon ECS's task placement
  engine, and Nomad's scheduler each play this role. The pattern presumes this
  participant exists; without it, container-per-service degrades to manually
  running `docker run` commands and loses most of its operational value.

Relationships. Exactly one Service maps to exactly one Container Image
definition (though that image may be built in several tagged versions over
time). One Container Image maps to zero, one, or many Container Instances at
any given moment, and the count is the Service's current scale. The Scheduler
holds the association from a desired-state description of Container Instances
to the physical hosts that actually run them, and it is the Scheduler, not the
Service's own code, that decides placement.

## 6. ASCII structure diagram

```
  +-----------------------+
  | Order Service         |
  | (source + Dockerfile) |
  +-----------------------+
            |
            | builds into
            v
  +--------------------+
  | order-service:v1.4 |
  | Container Image    |
  +--------------------+
            |
            | instantiated as N replicas (N=3 here)
      +-----+-----+
      v     v     v
  +------------+  +------------+  +------------+
  | instance 1 |  | instance 2 |  | instance 3 |
  | cpu 0.5    |  | cpu 0.5    |  | cpu 0.5    |
  | mem 256Mi  |  | mem 256Mi  |  | mem 256Mi  |
  +------------+  +------------+  +------------+
      ^     ^     ^
      +-----+-----+
            |
            | place, health-check, restart
            v
  +--------------------------+
  | Scheduler / Orchestrator |
  | (Kubernetes, ECS, ...)   |
  +--------------------------+

  A second, unrelated service (fraud-check) builds and scales
  through the same shape independently, with no shared image,
  no shared host assumption, and no coupling to order-service's
  scaling decisions.

  +---------------------+
  | Fraud Check Service |
  +---------------------+
            |
            | builds into
            v
  +------------------+
  | fraud-check:v0.9 |
  | Container Image  |
  +------------------+
            |
            | 1 replica right now
            v
  +-------------+
  | instance 1  |
  | fraud-check |
  +-------------+
```

## 7. Dynamics

The runtime flow that matters most for this pattern is not a request path, it is
the deploy-and-scale lifecycle, because that is what the pattern is actually
buying. The sequence below shows a rolling deployment of a new image version
under an orchestrator, and a horizontal scale-out event triggered separately.

```
Operator/CI      Registry         Orchestrator         Container Runtime (node)   Running Instance
    |                |                  |                        |                       |
    |-- push image ->|                  |                        |                       |
    |  order-service:v1.5               |                        |                       |
    |                |                  |                        |                       |
    |-- apply desired state (image=v1.5, replicas=3) ------------>|                       |
    |                |                  |                        |                       |
    |                |                  |-- pull image v1.5 ----->|                       |
    |                |<-----------------|                        |                       |
    |                |-- image layers ->|                        |                       |
    |                |                  |-- start container ---->|                       |
    |                |                  |                        |-- run entrypoint ---->|
    |                |                  |                        |                       |-- listen, ready
    |                |                  |<-- readiness probe OK -|<----------------------|
    |                |                  |                        |                       |
    |                |                  |-- route traffic to new instance                |
    |                |                  |-- stop one v1.4 instance (send SIGTERM) ------->|
    |                |                  |                        |-- drain, exit 0 ------|
    |                |                  |   (repeat per instance, one at a time)          |
    |                |                  |                        |                       |
    |                |                  |    ... rollout completes, all 3 on v1.5 ...     |

Separately, a scale-out event:

    Metrics/HPA          Orchestrator         Container Runtime         New Instance
        |                     |                       |                       |
        |-- CPU > 70% ------->|                       |                       |
        |                     |-- desired replicas 3 -> 5                     |
        |                     |-- start 2 more instances ------------------->|
        |                     |                       |-- entrypoint runs -->|
        |                     |<-- readiness probe OK ------------------------|
        |                     |-- add to load balancing pool                  |
```

Two timing notes carried directly from operational practice, not from academic
description. First, the orchestrator must not route traffic to a Container
Instance before its readiness signal fires, and it must stop routing before it
sends the termination signal, or requests land on an instance that is not yet,
or is no longer, able to serve them; this is the readiness and liveness probe
contract Kubernetes documents explicitly (see dimension 9). Second, the
container's main process must actually handle the termination signal (SIGTERM
on Linux) and exit promptly, because most orchestrators escalate to a hard kill
after a fixed grace period, commonly 30 seconds in Kubernetes by default, and a
process that ignores the signal loses its chance to drain connections cleanly
and is killed mid-request instead.

## 8. Implementation variants

**One process, one container, the canonical form.** The image's entrypoint
starts a single long-running process that is the service itself. This is the
form the Docker documentation describes as best practice and the form the code
examples in this entry implement.

**One tightly coupled process group per container, via `--init` or a minimal
init.** Some services legitimately need more than one OS process inside one
container instance, for example a supervisor that also spawns a short-lived
background job runner sharing the same image and lifecycle. Docker's own
guidance for this case is explicit. use the `--init` flag rather than a
full-fledged init system such as `sysvinit` or `systemd`, because the flag
"inserts a tiny init-process into the container as the main process, and
handles reaping of all processes when the container exits"
([Docker documentation, "Multi-service containers"](https://docs.docker.com/config/containers/multi-service_container/),
verified 2026-08-02). This variant still fits the pattern's intent, because
the process group as a whole is still one Service's deployable, independently
scaled unit; it differs from the anti-pattern of packing unrelated services
into one container only in that the processes here genuinely share a single
purpose and a single lifecycle.

**Multi-container Pod as a variant, not a violation.** Kubernetes explicitly
supports "Multiple Container Pods" for "tightly coupled containers that need to
share resources" that "form a single cohesive unit" and are "recommended only
when containers have interdependencies" ([Kubernetes documentation, "Pods"](https://kubernetes.io/docs/concepts/workloads/pods/),
verified 2026-08-02). A Pod carrying a primary service container plus a Sidecar
container is still, at the level of the primary Service, one instance of that
Service per Pod; the sidecar is an implementation detail of how that instance
is composed, not a second independently scaled service instance. This is the
precise boundary between "still this pattern" and "actually the Sidecar
pattern doing the composing", covered further in dimension 13.

**Distroless or scratch-based minimal images.** Rather than a full OS
userland, the image contains only the compiled binary (or, for an interpreted
language, the runtime plus the application) and its direct dependencies, with
no shell, package manager, or unrelated tooling. This variant trades some
in-container debuggability for a materially smaller attack surface and image
size, which matters more as the number of per-service images grows, because
image count multiplies patching effort.

**Immutable image, externalised configuration.** The same built image is
promoted unmodified from a staging environment to production, with
environment-specific values supplied at container start through environment
variables, mounted config, or a secrets manager, rather than baked into
per-environment image builds. This is close to load-bearing for the pattern to
deliver its promised deployment consistency; an image that differs per
environment reintroduces the "works in staging, breaks in production" gap the
pattern exists to close.

**Language-idiomatic entrypoint shape.** The pattern itself is language-agnostic
because it operates at the packaging layer, one level above any single
language's runtime, but the way a process becomes container-friendly differs by
language stack. A compiled Go or Rust binary needs no runtime installed in the
image at all beyond its own binary and, for Go, optionally CA certificates; a
Python or Node.js service needs its interpreter and dependency tree present in
the image; a JVM-based service needs a JRE and typically benefits from
container-aware heap sizing flags so the JVM respects the container's cgroup
memory limit rather than the host's total physical memory. The code examples in
this entry show the common contract, listen on a configurable port, respond to
a health check, and shut down cleanly on SIGTERM, expressed once in each of
three language stacks.

## 9. Known production uses

**Kubernetes itself, as the reference orchestrator built around this exact
unit.** The Kubernetes Pod concept is documented as "a group of one or more
containers, with shared storage and network resources, and a specification for
how to run the containers," whose "contents are always co-located and
co-scheduled, and run in a shared context," with the single-container Pod being
the most common case in practice ([Kubernetes documentation, "Pods"](https://kubernetes.io/docs/concepts/workloads/pods/),
verified 2026-08-02). Every workload running on any Kubernetes cluster,
including the managed offerings from every major cloud provider, is scheduled
in this unit.

**Amazon Elastic Container Service (ECS) task definitions.** AWS documents a
task definition as "a blueprint for your application," a JSON document that
"describes the parameters and one or more containers that form your
application," which is then run as a task, and an ECS service "runs and
maintains your desired number of tasks simultaneously," relaunching a
replacement automatically when a task fails or stops ([AWS documentation,
"Amazon ECS task definitions"](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definitions.html),
verified 2026-08-02). AWS's own guidance for task definition design steers
toward one container per concern within a task in the same spirit as the
Docker best-practice framing quoted in dimension 1, and ECS's per-task scaling
API operates on exactly this granularity.

**Google Borg, the internal predecessor to Kubernetes and the direct lineage
this pattern's orchestration model descends from.** Borg is documented as "a
cluster manager that runs hundreds of thousands of jobs, from many thousands of
different applications, across a number of clusters each with up to tens of
thousands of machines," achieving high utilisation "by combining admission
control, efficient task-packing, over-commitment, and machine sharing with
process-level performance isolation" (Abhishek Verma, Luis Pedrosa, Madhukar R.
Korupolu, David Oppenheimer, Eric Tune, John Wilkes, "Large-scale cluster
management at Google with Borg," EuroSys 2015, published by Google Research;
paper page confirmed at
[research.google, "Large-scale cluster management at Google with Borg"](https://research.google/pubs/large-scale-cluster-management-at-google-with-borg/),
verified 2026-08-02). Borg's task, the unit it schedules and isolates with
per-process performance controls, is the direct conceptual ancestor of the
Kubernetes Pod and, through it, of the packaging convention this entry
describes; the paper itself documents that Kubernetes was built by engineers
who had operated Borg and explicitly carried its lessons forward, though the
specific engineering-blog framing of that history is not independently quoted
here to avoid overreaching a single-source claim.

**Netflix's Titus container platform.** Netflix built and operated Titus as its
internal container orchestration platform specifically to run each of its many
independently owned microservices as scheduled container instances at fleet
scale, replacing an earlier model of one service per Amazon EC2 Auto Scaling
Group with one service per container running under a shared orchestrator. This
production use is widely reported in Netflix's own conference talks and
engineering communications about Titus; because a single durable, precisely
quotable primary-source URL for the specific claim was not independently
verified during authoring of this entry, it is recorded here as a named,
well-known industry deployment rather than backed by an inline citation, and a
reader should treat it as directionally reliable but not sourced to the same
bar as the three citations above.

## 10. Consequences

Positive.

- Each service instance is isolated from every other by the container
  runtime's namespace and cgroup boundaries, so a resource leak, a crash, or a
  bad deploy in one service cannot directly starve or crash a co-located,
  unrelated service.
- Startup time is primarily determined by process startup rather than OS boot,
  which makes fast horizontal autoscaling, fast rolling deploys, and fast
  recovery from a failed instance all practical in the same way a VM-based
  deployment cannot match at comparable cost.
- Different services can use entirely different languages, runtimes, and
  dependency versions without any negotiation over a shared host's toolchain,
  because each image is self-contained.
- The deployment, scaling, and health-check contract is uniform across every
  service regardless of what is inside it, which is what lets a single
  orchestrator, and a single on-call runbook, manage a fleet of heterogeneous
  services.
- The built image is an immutable, versioned, reproducible artefact, so "it
  worked in staging" becomes a much stronger statement than it is when staging
  and production are hand-configured hosts that have drifted apart over time.

Negative.

- The number of build, scan, and patch targets multiplies to roughly one per
  service, and every image independently carries a base-layer supply-chain
  surface that has to be tracked and updated, which is real, ongoing
  operational cost rather than a one-time setup cost.
- The pattern is close to worthless without an orchestrator, so adopting it
  also means committing to that orchestrator's operational model, failure
  semantics, and manifest complexity, which is a large dependency for a
  small team to take on.
- Per-instance resource overhead, while far lighter than a VM, is not zero;
  many small containers each carrying their own copy of a runtime and
  dependency tree can add up to meaningfully more aggregate memory than the
  same processes sharing one host's runtime installation would use.
- Debugging across container boundaries is harder than debugging a single
  shared process, because a request that spans several service instances now
  spans several isolated filesystems, several isolated process namespaces, and
  typically a network hop between each, which is what makes distributed
  tracing close to mandatory rather than optional at this pattern's natural
  scale.
- The pattern assumes an ephemeral, disposable instance model, which is a
  genuine mismatch for stateful workloads unless storage is deliberately
  designed around persistent volumes, and teams that apply the pattern to
  stateful services by default rather than by design pay for that mismatch in
  data-loss incidents.

## 11. Failure modes and misuse

**The fat container.** Symptom. One image, when inspected, is found to start a
web server, a cron daemon, and a background queue worker inside the same
container, none of them independently restartable or independently scalable
from the orchestrator's point of view. Cause. The team adopted containers as a
packaging format without adopting the isolation discipline the pattern is
actually for, treating the container as a lightweight VM rather than as a
one-service boundary. Fix. Split each independently schedulable concern into
its own image and its own orchestrator-managed unit, keeping only genuinely
co-lifecycle processes together under the `--init` variant from dimension 8.

**Ignoring SIGTERM.** Symptom. Every rolling deploy produces a burst of
5xx errors or dropped connections for a few seconds, and the errors correlate
exactly with instance termination events in the orchestrator's logs. Cause.
The process inside the container does not handle the termination signal, so
the orchestrator's graceful-shutdown window expires unused and the process is
hard-killed mid-request once the grace period elapses. Fix. Register a signal
handler that stops accepting new connections, finishes in-flight requests, and
exits zero, as shown in the code examples for this entry; verify the fix by
timing a controlled rolling deploy and confirming the error count during it is
zero, not merely low.

**Health check that lies.** Symptom. The orchestrator reports an instance as
healthy and keeps routing traffic to it while the service is actually unable
to do real work, for example because its database connection pool is
exhausted, and users see intermittent failures the platform's own dashboards
do not explain. Cause. The readiness or liveness probe endpoint returns a
trivial 200 with no check of the dependencies the service actually needs to
function, often because the probe was added as an afterthought to satisfy the
orchestrator's requirement rather than designed to reflect true readiness.
Fix. Make the readiness probe check the specific dependencies the request path
actually needs, and make the liveness probe check only that the process itself
is not deadlocked, since conflating the two causes an orchestrator to restart
a perfectly live process whenever a downstream dependency has a bad moment.

**Baking environment-specific configuration into the image.** Symptom. There
are three near-identical images, `order-service-staging`, `order-service-prod`,
that differ only in a hardcoded database hostname, and a bug fix has to be
rebuilt and re-tagged three times, occasionally drifting because one build was
forgotten. Cause. Configuration was compiled or copied into the image at build
time instead of supplied at container start. Fix. Externalise configuration
through environment variables or a mounted config source and promote the exact
same image digest through every environment, which restores the reproducibility
the pattern is meant to deliver.

**Latent image bloat and an unpinned base layer.** Symptom. A security scan
turns up dozens of CVEs in a service's image that the team never wrote a line
of code touching, and a routine `docker build` on a Tuesday silently pulls a
newer, sometimes broken, base image because the Dockerfile referenced `:latest`
rather than a pinned digest. Cause. Multiplying the image count multiplies the
attack surface tracked per service, and an unpinned base tag turns every future
build into a moving target. Fix. Pin base images by digest, run automated image
scanning in CI as a required check rather than an advisory one, and schedule
routine base-layer bumps as their own tracked, tested change rather than an
incidental side effect of an unrelated code change.

**Resource limits set from guesswork, not measurement.** Symptom. Instances of
one service are repeatedly OOM-killed under normal load, or the opposite, one
service reserves so much CPU and memory headroom that the cluster's bin-packing
efficiency collapses and infrastructure cost rises with no corresponding
traffic growth. Cause. The container's resource requests and limits were set
once at initial deployment and never revisited against real observed usage.
Fix. Set requests and limits from measured p95 to p99 resource consumption
under representative load, and revisit them on a schedule or in response to an
alert, rather than treating the initial guess as permanent.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Service Instance per Container | Service Instance per VM | Service Instance per Host (shared) | Serverless Deployment (FaaS) |
|---|---|---|---|---|
| Isolation | Strong. Namespaces plus cgroups per instance | Strongest. Full kernel and OS boundary | Weak. Shared kernel, shared filesystem, shared blast radius | Strong. Platform-enforced per-invocation isolation |
| Startup latency | Seconds, primarily process start time | Minutes, primarily OS boot time | Effectively zero if the process is already running | Sub-second to a few seconds, plus cold-start overhead on the first invocation after idle |
| Resource overhead per instance | Low. Shares host kernel | High. Each instance carries a full OS image | Lowest. Only the process itself, no isolation cost | Managed away, but billed per invocation rather than per reserved capacity |
| Technology heterogeneity across services | High. Each image is self-contained | High, at greater cost per instance | Low. Shared host toolchain constrains every co-located service | High, within the platform's supported runtimes |
| Independent scaling per service | Strong and fast, the pattern's core payoff | Strong but slow, VM boot limits scale-out speed | Poor. Scaling one service means adding capacity for its neighbours too | Automatic and extremely fine-grained, down to per-request |
| Operational uniformity | High, via a single orchestrator API | Moderate, VM tooling is heavier and less uniform across providers | Low. Ad hoc per-host scripting is common | High, but the operational model is the platform's, with far less control |
| Artefact and supply-chain surface | High. One image per service, growing with service count | High, and each artefact is heavier to build and store | Low. Fewer artefacts, but they are less reproducible | Low from the team's side, shifted onto the platform vendor |
| Dependency on an orchestration layer | Required for the pattern to pay off | Required at similar strength, e.g. cloud auto-scaling groups | Not required, which is both its appeal and its ceiling | Fully delegated to the platform, no orchestrator to operate |
| Fit for stateful primary workloads | Requires deliberate persistent-volume design | Natural fit, VM-attached disks are a familiar model | Natural fit if the host itself is treated as long-lived | Poor fit, the model assumes statelessness |
| Cost at very low, bursty traffic | Pays for reserved capacity even when idle, unless scaled to zero deliberately | Pays for reserved capacity, and VM minimums are coarser | Pays for the host regardless of load | Often cheapest, since billing follows actual invocations |

Reading of the table. Service Instance per Container wins when a team already
has, or is building, an orchestration layer and needs fast, independent scaling
across many heterogeneous services without paying full VM cost per instance.
Service Instance per VM wins when the isolation requirement is regulatory or
security-driven and justifies the heavier cost, for example multi-tenant
workloads that must not share a kernel. Service Instance per Host wins only at
very small scale where the coordination and artefact overhead of the other
three genuinely is not earned yet. Serverless Deployment wins for sparse,
bursty, stateless workloads where even a scaled-to-zero container's cold-start
and operational overhead exceeds what a managed function platform offers.

## 13. Related and incompatible patterns

- **Sidecar.** Composes directly on top of this pattern rather than competing
  with it. Sidecar places a second, helper container inside the same
  co-scheduled unit (a Kubernetes Pod, an ECS task) as the primary service
  container, to add a cross-cutting concern such as a service-mesh proxy, a log
  shipper, or a TLS-terminating gateway, without modifying the primary
  service's own code or image. Service Instance per Container is the packaging
  discipline that makes this composition possible in the first place, because
  it is the discipline that keeps a cross-cutting concern out of the primary
  service's process to begin with, leaving room for it to live in its own
  container next door.
- **Ambassador.** A specialisation of Sidecar, where the helper container
  specifically proxies outbound calls from the primary service, for example
  handling retries, circuit breaking, or protocol translation to an external
  dependency on the service's behalf. It relates to this entry the same way
  Sidecar does, as a composition built on top of the one-container-per-concern
  boundary this pattern establishes.
- **Adapter.** Another Sidecar specialisation, where the helper container
  exposes a standardised interface, such as a common metrics or logging format,
  in front of a primary service that speaks something nonstandard internally.
  Same relationship to this entry as Sidecar and Ambassador.
- **Service Instance per Host and Service Instance per VM.** Named alternatives
  at the same decision point, not compositions. A given service picks exactly
  one of these three at a time for a given deployment target, and the choice is
  the subject of dimension 12's trade-off table.
- **Serverless Deployment.** Also a named alternative at the same decision
  point, sitting one level further from infrastructure ownership than any of
  the container or VM options, and appropriate for a different traffic and
  statelessness profile as discussed above.
- **Circuit Breaker, Retry, and Bulkhead patterns from resilience engineering.**
  Compose cleanly on top of this pattern rather than conflicting with it,
  because the network calls between independently containerised service
  instances are exactly the calls those resilience patterns exist to protect;
  a monolith sharing one process would not need them in the same way.
- **A "big ball of mud" container, listed as incompatible in this entry's
  frontmatter.** This is not a formally named pattern but the well-recognised
  anti-pattern of packing unrelated services into one container image, which
  directly negates the isolation and independent-scaling payoff this pattern
  exists to provide; see dimension 11's "fat container" failure mode for its
  concrete symptom.
- **Multi-process supervisor container, also listed as incompatible.** Using a
  full init system such as systemd inside a container to run several unrelated
  long-lived services under one supervisor reproduces the shared-host coupling
  problem this pattern exists to remove, and Docker's own documentation
  explicitly steers away from it in favour of the narrow `--init` exception
  described in dimension 8.

## 14. Refactoring path in and out

Introducing the pattern into a system that currently deploys services on
shared hosts or as a monolith. Ordered steps, written for the realistic case of
an incremental migration rather than a rewrite.

1. Pick one service, ideally one with a clear ownership boundary and a
   relatively self-contained dependency footprint, as the pilot. Do not attempt
   to containerise the whole estate at once.
2. Write a Dockerfile for that service that installs only what the service
   itself needs, pin the base image by digest, and confirm the built image runs
   correctly with the same behaviour as the existing deployment, tested against
   the same integration suite the current deployment uses.
3. Add a health-check endpoint if the service does not already have one, and
   wire a signal handler for graceful shutdown, since both are load-bearing
   requirements for step 5, not optional polish.
4. Externalise any configuration currently baked into the deployment artefact
   or the host, so the built image is identical across every environment and
   only its runtime configuration differs.
5. Deploy the pilot service's container image under the chosen orchestrator
   alongside its still-running host-based deployment, routing a small
   percentage of traffic to it, and compare error rates, latency, and resource
   usage before cutting over fully.
6. Once the pilot is stable in production for a full deployment cycle,
   including at least one rolling deploy and one scale event, decommission its
   host-based deployment and document the pattern's contract, health-check
   shape, shutdown behaviour, resource limit methodology, so the next service's
   migration is faster than the pilot's was.
7. Repeat per service, treating each migration as its own small, reversible
   change rather than a single large cutover, and track image count, base-image
   currency, and scan findings as an ongoing operational metric from the first
   service onward rather than deferring it until the fleet is large.

Removing the pattern when it stops earning its place, which happens most often
when a service count shrinks, a team consolidates, or the operational cost of
running the orchestrator outweighs the isolation benefit for a small, stable
set of services.

1. Confirm the services being consolidated genuinely no longer need independent
   scaling or independent restart, since that is the concrete capability being
   given up, not merely a preference to simplify tooling.
2. Choose the shared target, a smaller number of hosts or VMs, and migrate
   configuration from the container-native externalised form to whatever the
   target's convention is, keeping the same discipline of not baking
   environment-specific values into a build artefact.
3. Move one service at a time back onto the shared target, verifying behaviour
   at each step the same way step 5 above verified the forward migration.
4. Retire the orchestrator, image registry, and per-service CI pipelines only
   after every service has moved, and only once the team has confirmed no
   remaining workload still depends on the container-level isolation the
   pattern provided.

## 15. Testing and verification

Easier because of the pattern.

- Each service's built image can be tested in complete isolation from every
  other service's runtime environment, because it carries its own dependencies;
  a test run against the image is a test run against exactly what will ship,
  not against a developer's locally drifted machine.
- Contract and integration tests between services can run the actual container
  images against each other locally, using the same image the orchestrator will
  run in production, which closes a large class of "works locally, fails in
  production" gaps that shared-host deployments are prone to.
- Resource-limit behaviour, what happens when a service hits its memory limit,
  is directly testable by running the container under the same cgroup
  constraints it will have in production, rather than being an untestable
  property of a shared host's aggregate behaviour.

Harder because of the pattern.

- End-to-end tests that exercise a request across several services now require
  either standing up several containers together, commonly with a tool such as
  Docker Compose or a local Kubernetes distribution, or accepting a slower
  feedback loop against a shared staging environment.
- Debugging a failure that only reproduces under the orchestrator's actual
  scheduling and networking behaviour, for instance a race during a rolling
  deploy, is harder to reproduce on a single developer machine than debugging a
  single shared process would be.

Techniques that apply.

- **Container-level unit and integration tests as part of the image build.**
  Run the service's own test suite inside the same base image that will ship,
  as an explicit CI stage before the image is tagged and pushed, so a passing
  build is a build that was tested in its actual runtime environment.
- **Local multi-container composition for cross-service testing.** Tools that
  run several images together on a developer machine, matching the shape the
  orchestrator will use in production, close most of the gap between "tested
  locally" and "tested as deployed" for multi-service flows.
- **Signal-handling verification as an explicit test.** Send SIGTERM to a
  running container under load in a test environment and assert that in-flight
  requests complete and new connections are refused, rather than assuming the
  shutdown handler from dimension 11 works because it compiles; this is
  precisely the failure mode that is invisible until a real rolling deploy.
- **Chaos and resource-limit testing.** Deliberately run a service instance
  against its production memory and CPU limits under realistic load in a
  pre-production environment, and deliberately kill instances during a load
  test, to verify the orchestrator's restart and rescheduling behaviour matches
  what the service actually needs to stay healthy.

## 16. Observability signals

The pattern multiplies the number of independently running units, so the
signals that matter most are the ones that let an operator reason about the
fleet of instances as a whole, not only about one instance in isolation.

What to record.

- Per-instance CPU and memory usage against the configured requests and
  limits, so a dashboard can show both individual instance health and whether
  the configured limits, from dimension 11's "resource limits set from
  guesswork" failure mode, still match reality.
- Container restart count per service, labelled by the reason the orchestrator
  gives for the restart, since a rising restart count with no corresponding
  deploy event is one of the clearest early signals of a health-check or
  resource-limit problem.
- Time from a scheduling decision to a container reporting ready, which
  directly measures whether the pattern's promised fast-scaling behaviour is
  actually being delivered or has regressed, for example because an image grew
  too large or a startup dependency became slow.
- Image age and CVE count per running image tag, tracked as a fleet-wide
  metric, since this is the operational cost side of the pattern that is easy
  to let drift silently without an explicit signal for it.
- Request success rate and latency during rolling deploys specifically, split
  out from steady-state traffic, since dimension 11's "ignoring SIGTERM"
  failure mode is invisible in aggregate metrics and only shows up when deploy
  windows are isolated in the data.

A healthy fleet on a dashboard. Restart counts are flat except around
deliberate deploys. Resource usage sits comfortably inside configured limits
with headroom that reflects measured, not guessed, usage. Time-to-ready is
stable release over release. Deploy-window error rates are indistinguishable
from steady-state error rates. Running image ages cluster near the most recent
base-image patch rather than spreading across many stale versions.

A failing fleet. A single service's restart count climbs while its deploy
history shows nothing new, which points at a health-check or resource-limit
problem rather than a code regression. Deploy-window error rates spike above
steady-state consistently, which is the SIGTERM-handling failure mode from
dimension 11 made visible. Time-to-ready creeps upward release over release,
which usually traces to image bloat or a slow startup dependency added without
anyone noticing the cumulative cost. Image ages spread widely across the
fleet, which is the base-layer patching discipline from dimension 11 quietly
lapsing.

## 17. Security and privacy implications

The pattern is not neutral on security. It reshapes the attack surface rather
than simply reducing or increasing it, and treating it as a pure security win
because "containers are isolated" understates the real picture.

**Kernel sharing is the isolation ceiling.** Every container instance on a
given host shares that host's kernel, unlike the VM-per-instance alternative
which gives each instance its own kernel. A kernel-level vulnerability or
container-escape exploit therefore has a larger blast radius across
co-located, unrelated services than the same exploit would have on a
VM-isolated deployment. Where the isolation requirement is genuinely
regulatory or adversarial-tenant grade, this is the concrete reason to prefer
Service Instance per VM, or a container runtime with stronger sandboxing, over
the plain container form.

**Image-count multiplication is a supply-chain multiplication.** As dimension
11 describes operationally, adopting this pattern multiplies the number of
independently built and maintained artefacts, and each one independently
carries whatever vulnerabilities exist in its base image and its dependency
tree at build time. A fleet-wide image scanning and patching discipline is not
optional hardening, it is the direct security cost this pattern's isolation
benefit is traded against, and skipping it accumulates risk silently across
every image rather than in one visible place.

**Secrets handling moves from "one host's configuration" to "many containers'
runtime injection."** Externalising configuration, the practice dimension 8
and dimension 11 both describe as necessary for the pattern to deliver its
reproducibility promise, means secrets must be injected into many ephemeral
container instances rather than configured once on a long-lived host. This
is generally a security improvement when done through a proper secrets
manager with per-container scoped access, because a compromised instance can
be limited to the secrets it actually needs and rotated quickly, but it is a
regression if the team instead bakes secrets into the image itself or passes
them as plain environment variables visible to anyone who can inspect the
running container or the orchestrator's own API.

**Registry access is a new privileged surface.** The image registry that
every container image is pulled from becomes a high-value target, because
compromising it, or compromising the CI pipeline that pushes to it, allows an
attacker to substitute a malicious image for a trusted one across every
instance the orchestrator subsequently schedules. Signed images, and an
orchestrator configured to verify signatures before running an image, close
this specific gap; an unsigned, unauthenticated pull path leaves it open.

On privacy, the pattern's most direct implication is indirect. because a
single logical request now typically traverses several isolated container
instances rather than staying inside one process, the distributed tracing and
centralised logging infrastructure this pattern all but requires (see
dimension 15 and dimension 16) becomes a new place where personal data can
leak if trace and log payloads are not deliberately scrubbed of sensitive
fields before they are centralised. A team adopting this pattern should treat
its tracing and logging pipeline as a data-handling surface subject to the
same retention and access rules as any other store of personal data, not as
purely an operational convenience.

## Code examples

Three languages, chosen because each represents a genuinely different way a
process becomes container-idiomatic. Go shows a compiled, statically linked
binary needing no runtime installed in its own image, the shape most native to
minimal or distroless containers. Python shows an interpreted service that must
ship its interpreter and dependencies inside the image, the shape most common
in data and scripting-heavy services. TypeScript, compiled to JavaScript and run
under Node.js, shows the same contract in the language stack most common for
lightweight API services and edge-adjacent workloads. Rust and Swift are
omitted from the runnable examples in this entry because they add no further
distinct packaging shape for this specific pattern beyond what Go already
demonstrates, a compiled binary with no required runtime, and because the load
already carried by three verified, running examples was judged to cover the
pattern's actual variation, which is a packaging and lifecycle concern common
across languages rather than a language-feature concern the way earlier
GoF-style entries in this repository are. Every example below implements the
same minimal, load-bearing contract this pattern's whole payoff depends on. a
configurable listen port, a health-check endpoint the orchestrator can probe,
and a clean shutdown on SIGTERM.

### Go

Compiled and run directly. No language runtime is required inside the shipped
image beyond the binary itself.

```go
package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	mux := http.NewServeMux()
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprint(w, "ok")
	})
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprint(w, "order-service\n")
	})
	srv := &http.Server{Addr: ":" + port, Handler: mux}

	go func() {
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("listen: %v", err)
		}
	}()

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGTERM, syscall.SIGINT)
	<-stop
	log.Println("SIGTERM received, draining connections")
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := srv.Shutdown(ctx); err != nil {
		log.Fatalf("shutdown: %v", err)
	}
}
```

A minimal Dockerfile that keeps exactly one process, this binary, as the
container's image contents, using a multi-stage build so the shipped image
carries no compiler and no source.

```dockerfile
FROM golang:1.23 AS build
WORKDIR /src
COPY svc.go .
RUN CGO_ENABLED=0 go build -o /out/order-service svc.go

FROM gcr.io/distroless/static-debian12
COPY --from=build /out/order-service /order-service
EXPOSE 8080
ENTRYPOINT ["/order-service"]
```

### Python

Run with the standard library only, no third-party dependency, so the shipped
image needs nothing beyond a Python interpreter.

```python
import http.server
import os
import signal
import socketserver
import sys
import threading


PORT = int(os.environ.get("PORT", "8080"))


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/healthz":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
            return
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"order-service\n")

    def log_message(self, fmt, *args):
        pass


def install_shutdown_handler(server):
    def handler(signum, frame):
        print("SIGTERM received, draining connections", file=sys.stderr)
        threading.Thread(target=server.shutdown).start()

    return handler


def main():
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as server:
        signal.signal(signal.SIGTERM, install_shutdown_handler(server))
        print(f"listening on {PORT}", file=sys.stderr)
        server.serve_forever()


if __name__ == "__main__":
    main()
```

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY svc.py .
EXPOSE 8080
ENTRYPOINT ["python3", "svc.py"]
```

### TypeScript

Compiled with `tsc` to plain JavaScript and run under Node.js. The shipped
image installs the Node.js runtime, not a TypeScript toolchain, since
compilation happens at build time, not inside the running container.

```typescript
import http from "node:http";

const port = Number(process.env.PORT ?? "8080");

const server = http.createServer((req, res) => {
  if (req.url === "/healthz") {
    res.writeHead(200);
    res.end("ok");
    return;
  }
  res.writeHead(200);
  res.end("order-service\n");
});

server.listen(port, () => {
  console.error(`listening on ${port}`);
});

process.on("SIGTERM", () => {
  console.error("SIGTERM received, draining connections");
  server.close(() => process.exit(0));
});
```

```dockerfile
FROM node:22-slim AS build
WORKDIR /app
COPY svc.ts .
RUN npm install -g typescript @types/node \
 && tsc --target es2020 --module commonjs --types node svc.ts

FROM node:22-slim
WORKDIR /app
COPY --from=build /app/svc.js .
EXPOSE 8080
ENTRYPOINT ["node", "svc.js"]
```

All three programs were run directly on the authoring machine, outside a
container, listening on a local port, and verified to answer `/healthz` with
`ok` and to log a drain message and exit cleanly on receipt of SIGTERM, which
is the exact runtime contract each Dockerfile above packages as a container
image. The TypeScript source was additionally compiled cleanly with `tsc`
targeting ES2020 and CommonJS, with `@types/node` present, producing zero
compiler errors. The Go source was built with `go build` on the authoring
machine and produced a working binary. The Dockerfiles themselves were not
built inside a container runtime during authoring, since no Docker daemon was
available in the authoring environment; their shape follows Docker's own
documented multi-service and best-practice guidance cited in dimensions 1, 8,
and 18, and each mirrors a conventional, widely used base-image pattern for
its respective language.

## 18. References

1. Docker Inc. *Docker documentation*, "Multi-service containers".
   https://docs.docker.com/config/containers/multi-service_container/
   Verified 2026-08-02. Source of the one-service-per-container best-practice
   quotation, the multi-process exception, and the `--init` flag guidance in
   dimensions 1 and 8.
2. Kubernetes Authors. *Kubernetes documentation*, "Pods".
   https://kubernetes.io/docs/concepts/workloads/pods/
   Verified 2026-08-02. Source of the Pod definition, the co-location and
   co-scheduling quotation, and the multi-container Pod guidance used in
   dimensions 4, 6, 8, 9, and 13.
3. Chris Richardson. *microservices.io pattern catalog*, "Service per Container".
   https://microservices.io/patterns/deployment/service-per-container.html
   Verified 2026-08-02. Source of the pattern's name, its forces, and its
   contrast with Service Instance per Host and Service Instance per VM, used
   throughout dimensions 1, 2, 3, and 12.
4. Amazon Web Services. *Amazon ECS Developer Guide*, "Amazon ECS task
   definitions".
   https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definitions.html
   Verified 2026-08-02. Source of the ECS task definition production use in
   dimension 9.
5. Abhishek Verma, Luis Pedrosa, Madhukar R. Korupolu, David Oppenheimer, Eric
   Tune, John Wilkes. "Large-scale cluster management at Google with Borg."
   EuroSys 2015. Published by Google Research.
   https://research.google/pubs/large-scale-cluster-management-at-google-with-borg/
   Verified 2026-08-02. Source of the Borg production use and abstract
   quotation in dimension 9, and of the historical lineage claim in dimension
   1, applied narrowly to what the paper itself supports.

Netflix's Titus platform is named as a production use in dimension 9 based on
widely reported industry knowledge rather than a single independently
quoted primary source verified during authoring, and is flagged there
explicitly as carrying a lower sourcing bar than references 1 through 5 above.
