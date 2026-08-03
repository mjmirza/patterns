---
name: Service Instance per Host
slug: service-instance-per-host
family: 10-microservices
category: Deployment
aliases: [Single Service Instance per Host, One Service per Host, Dedicated Host Deployment]
first_described: "Chris Richardson, microservices.io deployment pattern language, published as part of the site's pattern catalog, canonical form appears in Richardson, Microservices Patterns, Manning, 2019, chapter 12"
maturity: established
related: [service-per-vm, service-per-container, multiple-services-per-host, service-registry, self-contained-service, database-per-service, sidecar]
incompatible_with: [multiple-services-per-host]
verified: 2026-08-03
---

# Service Instance per Host

## 1. Name, aliases, and lineage

The canonical name in the deployment pattern language that Chris Richardson
maintains at microservices.io is "Single Service Instance per Host", and the
page itself titles the pattern "Pattern. Single Service Instance per Host"
(microservices.io, "Pattern. Single Service Instance per Host",
https://microservices.io/patterns/deployment/single-service-per-host.html,
verified 2026-08-03). The shorter "Service Instance per Host" is the name this
catalog uses because it reads better alongside the sibling entries
`service-per-vm` and `multiple-services-per-host`, and because Richardson's own
book, *Microservices Patterns* (Manning Publications, 2019), groups all three
under one deployment pattern family in chapter 12, "Deploying microservices",
so the shorter name is not a departure from the source, it is the same pattern
referred to by its family position rather than by the page title.

The idea predates the word microservice by a wide margin. Dedicating one
physical machine, and later one virtual machine, to a single running
application was the default operational model in enterprise Java and .NET
shops through the 1990s and 2000s, before hypervisor-based virtualization made
per-application machines cheap enough to provision on demand and before
containers made per-application isolation cheap enough to provision in
seconds. What changed with the microservices literature was not the mechanism,
it was naming the mechanism as a deliberate architectural choice with a stated
set of forces, rather than treating it as an unexamined default inherited from
how procurement happened to allocate hardware. Richardson's pattern language
gives the choice a name, a context, a set of forces, and two explicit
refinements, Service per VM and Service per Container, plus a named
alternative, Multiple Services per Host, which is the structure this entry
follows.

Sam Newman's *Building Microservices*, 2nd edition (O'Reilly, 2021), does not
use Richardson's exact pattern name but discusses the same deployment shape at
length in the chapter on deployment, where Newman distinguishes "single-purpose
hosts" from a host running many application processes and argues that the
isolation single-purpose hosts buy is one of the enabling factors that made
independent service deployability practical at scale for organizations moving
away from shared application servers. Because Newman's discussion is framed as
a deployment principle rather than a named pattern with a fixed title, this
entry treats microservices.io as the primary naming source and Newman as
corroborating literature that describes the same shape under different words.

## 2. Problem and context

You have already decomposed a system into services, and each service runs as
one or more service instances for throughput and redundancy, the same starting
context Richardson states explicitly on the pattern page. Now those service
instances have to be packaged and placed onto physical or virtual compute so
they actually run. The question this pattern answers is a placement question,
not a design question inside the service, given N service instances and M
hosts, what is the mapping from instances to hosts.

The problem becomes concrete the moment two services with different resource
appetites, different language runtimes, or different library dependency
versions are candidates for the same host. A Python service that pins an old
version of a native extension and a Java service that wants a particular JVM
heap size were, before containers were common, difficult to run side by side
on one operating system without one of them fighting the other for memory, or
without a dependency conflict that could only be resolved by giving each
service its own isolated operating environment. The context in which this
pattern earns its place is exactly that, multiple independently developed
services, built by different teams, at different release cadences, in
possibly different languages, that need to be deployed and scaled without one
service's resource use or software footprint affecting another's.

The pattern also arises from an operational question that has nothing to do
with code, when something goes wrong at 3 a.m., how much do you have to reason
about to isolate the cause. A host running exactly one service instance
answers that question with the smallest possible blast radius, a saturated CPU
on that host has exactly one plausible suspect. A host running twelve
unrelated service instances answers it with an investigation.

## 3. Forces

Richardson's own forces list on the pattern page names eight pressures
directly, and this entry restates them with the weighting that experience adds
on top of the source list (microservices.io, "Pattern. Single Service Instance
per Host", verified 2026-08-03). Services are written in a variety of
languages, frameworks, and framework versions, and letting each service pin its
own runtime without coordinating with every sibling service on the same
machine is a real constraint that grows sharper as an organization's service
count grows. Each service typically runs as more than one instance for
throughput and availability, so the placement decision is not made once per
service, it is made once per instance and repeated continuously as instances
scale up, scale down, fail, and get replaced. Services must be independently
deployable and independently scalable, which argues against any shared
resource that would force two services to be redeployed or rescaled together.
Instances need isolation from one another, both for security, so one
compromised process cannot reach into a sibling's memory or file descriptors,
and for resource fairness, so a runaway service cannot starve a well-behaved
neighbor. Teams need to build and deploy quickly, which argues for a simple,
repeatable packaging step rather than a bespoke provisioning script per
service. Teams need to constrain the CPU and memory a service instance can
consume, which is difficult to guarantee on a shared, unconstrained host
without an isolation primitive. Teams need to monitor the behavior of each
instance, which is far easier when a monitoring agent can attribute one host's
entire resource profile to one instance rather than disaggregating a shared
host's metrics after the fact. Deployment needs to be reliable, so that a
failed deploy of one service cannot leave a sibling service in an inconsistent
state on the same host. And the whole exercise has to be affordable, because
dedicating a full host to every instance is the most expensive way to satisfy
every other force on this list.

That last force is the one every other force pushes against. Isolation,
independent scaling, independent deployability, blast-radius containment, and
straightforward per-instance monitoring all favor giving each instance its own
host. Cost efficiency favors packing many instances onto fewer hosts. The
pattern is a deliberate trade of density for isolation, and the entry's
consequences and trade-off sections below make that trade explicit rather than
treating it as a free choice.

A force Richardson's page does not name directly, but that shows up
repeatedly in production incident retrospectives, is noisy-neighbor
elimination. On a shared host, a service instance's tail latency can degrade
because an unrelated instance on the same kernel triggered a garbage
collection pause, saturated a shared network interface, or exhausted the
page cache. A dedicated host removes that class of failure entirely, which is
one reason latency-sensitive services, and infrastructure agents that must
observe every host regardless of what else runs there, gravitate toward this
pattern even in organizations that pack most other workloads densely.

## 4. Applicability and non-applicability

Reach for Service Instance per Host when the workload is latency sensitive and
a shared host's resource contention would show up as tail-latency variance
that the business cannot absorb, for example a payment authorization path, a
real-time bidding service, or a matching engine. Reach for it when regulatory
or contractual isolation requirements exist, for example a service that
processes one tenant's regulated data and must not share a kernel, a network
namespace, or a hypervisor with a service that processes another tenant's
data under a different compliance regime. Reach for it when a service's
resource footprint is highly variable and difficult to predict, so that
co-locating it with anything else risks an unbounded neighbor effect, or when
the software stack itself is incompatible with co-location, for example a
service that requires kernel-level tuning, a specific kernel module, or
exclusive access to a hardware device such as a GPU or an FPGA. Reach for it
when the deployment unit already has to be a whole VM or a whole bare-metal
machine for reasons outside the pattern's own scope, for example a licensing
term that is billed per physical host, in which case running one service
instance per host at least avoids paying that license cost for services that
did not need to be there. Reach for the container-based refinement of this
pattern, Service per Container, when the isolation and per-instance
monitoring benefits are wanted but the cost of a dedicated VM or dedicated
bare-metal host per instance is not affordable, because a container gives
process and namespace isolation on a shared kernel at a fraction of the
overhead of a dedicated VM.

Do not reach for this pattern when the fleet has hundreds or thousands of
low-traffic service instances and the organization cannot absorb one host's
worth of idle capacity per instance, because the pattern's own listed
drawback is exactly this, potentially less efficient resource utilization
compared to Multiple Services per Host, since there are more hosts
(microservices.io, "Pattern. Single Service Instance per Host", "Resulting
context" section, verified 2026-08-03). Do not reach for it as the default
placement strategy inside a container orchestrator that already provides
process isolation, resource quotas, and per-container monitoring, because a
Kubernetes Pod, for example, already gives most of this pattern's isolation
benefit while the orchestrator's own scheduler bin-packs many Pods per Node
for density, and manually forcing one Pod per Node for every workload
discards the orchestrator's main efficiency argument without buying isolation
the orchestrator did not already provide. Do not reach for it purely out of
habit inherited from a pre-container era where per-application VMs were the
only isolation primitive available, because that habit is precisely the
inefficiency Google's Borg paper cites as a motivation for building an
efficient, shared-cluster scheduler in the first place, describing Borg as
achieving high utilization by combining admission control, efficient
task-packing, over-commitment, and machine sharing with process-level
performance isolation, which is the opposite allocation philosophy from one
service per host (Verma, Pedrosa, Korupolu, Oppenheimer, Tune, and Wilkes,
"Large-scale cluster management at Google with Borg", EuroSys 2015 paper
summary, Google Research publication page,
https://research.google/pubs/large-scale-cluster-management-at-google-with-borg/,
abstract, verified 2026-08-03). Do not reach for it for stateless, bursty,
short-lived workloads whose traffic is spiky and unpredictable across a large
fleet, since the fixed overhead of a whole host per instance means autoscaling
has to provision and de-provision entire machines to track load, which is
slower and more wasteful than an orchestrator scaling containers within an
already-warm pool of hosts. Do not reach for it as a substitute for actual
security controls, since dedicating a host is a strong but blunt isolation
boundary, and a service that genuinely needs a hardened trust boundary, for
example a secrets-management service, still needs its own access controls,
encryption, and audit logging regardless of whether it happens to be alone on
its host.

## 5. Structure

The participants in this pattern are deliberately few, because the pattern
describes a placement relationship, not an in-process collaboration between
objects.

The **service instance** is one running process, or one running virtual
machine, or one running container, depending on which refinement of the
pattern is in use, that executes a single deployable unit of one service's
code. It owns the entirety of the compute resources allocated to its host and
nothing else runs alongside it at the same isolation level.

The **host** is the isolation boundary. It may be a bare-metal physical
machine, a virtual machine such as an AWS EC2 instance, or, in the
container-based refinement, a container that shares a kernel with other
containers on the same underlying node but is otherwise treated as a
dedicated, single-tenant unit for exactly one service instance. The host's
defining property under this pattern is that it hosts one, and only one,
service instance for its entire lifetime.

The **deployment pipeline**, or build system, is the participant that
packages a service's code, together with its language runtime and
dependencies, into whatever artifact the chosen host type consumes, for
example a machine image, a container image, or a deployable archive plus a
provisioning script. Richardson's pattern page lists the packaging and
deployment question as the exact problem this pattern answers, so the build
system's role in producing a self-contained artifact per instance is part of
the pattern's structure, not an implementation detail outside it
(microservices.io, "Pattern. Single Service Instance per Host", "Problem"
section, verified 2026-08-03).

The **placement authority** decides which service instance lands on which
host. In the simplest form this is a human running a provisioning script or a
manual runbook. In a mature deployment this is an orchestrator, an
autoscaling group, or a scheduler that enforces the one-instance-per-host
invariant on every placement decision, the same role a Kubernetes DaemonSet
controller plays when it schedules exactly one Pod per eligible Node
(Kubernetes documentation, "DaemonSet",
https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/,
verified 2026-08-03).

The **monitoring and health-check agent** observes one host, and because the
host runs one service instance, every metric that agent reports can be
attributed to that instance without disaggregation. This is the structural
reason the pattern's "resulting context" section lists straightforward
monitoring as a direct benefit.

## 6. ASCII structure diagram

```
  Build system                Placement authority
  (packages one                (assigns instance
   instance's artifact)         to a free host)
        |                              |
        v                              v
  +-----------------+          +-----------------+
  | Artifact         |  place  | Host registry     |
  | (VM image,       |-------->| host-a  [free]    |
  |  container image,|         | host-b  [free]    |
  |  or archive)     |         | host-c  [occupied] |
  +-----------------+          +-----------------+
                                        |
                                        v
        +-------------------------------------------------+
        |                    Host. host-a                  |
        |  +-----------------------------------------+     |
        |  |          Service instance                |     |
        |  |   order-service, replica 1               |     |
        |  |   owns 100% of host-a's CPU and memory   |     |
        |  +-----------------------------------------+     |
        |                                                   |
        |  Monitoring agent (host-a)                        |
        |   every metric here is order-service's metric     |
        +---------------------------------------------------+

        +-------------------------------------------------+
        |                    Host. host-b                  |
        |  +-----------------------------------------+     |
        |  |          Service instance                |     |
        |  |   payment-service, replica 1             |     |
        |  |   owns 100% of host-b's CPU and memory   |     |
        |  +-----------------------------------------+     |
        +---------------------------------------------------+

  No host runs a second, unrelated service instance.
  Multiple Services per Host is the pattern that allows this box to
  contain more than one unrelated instance, and is not compatible
  with this diagram by definition.
```

## 7. Dynamics

The runtime dynamics of this pattern have two distinct phases, a placement
phase that happens once per instance's lifetime and a steady-state phase that
repeats for as long as the instance runs.

In the placement phase, a deploy is triggered, either by a person, a CI
pipeline, or an autoscaling policy reacting to load. The build system produces
one artifact for the service instance being deployed, for example a Docker
image tagged with the service's version, or a machine image baked with the
service's code and its runtime pre-installed. The placement authority
consults its host registry, finds a host with no existing instance and enough
free capacity to satisfy the new instance's declared resource requirements,
and reserves that host. The artifact is transferred to the host and started.
Once the process, VM, or container is confirmed healthy, usually by a
readiness probe or a health-check endpoint responding successfully, the
placement authority marks the host as occupied and, if the system uses a
service registry, registers the new instance so traffic can begin routing to
it, a step this pattern composes with directly, see `service-registry` under
related patterns.

```
  Deploy trigger      Placement authority        Host          Service registry
       |                     |                     |                  |
       |--request deploy---->|                     |                  |
       |                     |--find free host---->|                  |
       |                     |<---host-a selected--|                  |
       |                     |--transfer artifact-->|                  |
       |                     |--start instance----->|                  |
       |                     |                     |--boot process---|
       |                     |<--health check ok----|                  |
       |                     |--mark host occupied-|                  |
       |                     |--register instance------------------->|
       |                     |                     |                  |
       |               [ steady state. host-a runs exactly one        |
       |                 instance until it is explicitly retired ]    |
       |                     |                     |                  |
       |--request retire---->|                     |                  |
       |                     |--deregister instance------------------>|
       |                     |--stop instance------>|                  |
       |                     |<--stopped-----------|                  |
       |                     |--mark host free----|                  |
```

In the steady-state phase, the monitoring agent on the host samples CPU,
memory, disk, and network usage continuously and attributes all of it to the
single instance, since nothing else on the host could have produced it. A
liveness probe restarts the instance in place if it stops responding, and
because there is no neighbor on the host, restarting or resource-throttling
the instance never affects an unrelated service. When the instance is scaled
down, the placement authority stops the instance, deregisters it from the
service registry, and either terminates the host entirely, in the VM and
container refinements this typically means destroying the VM or container so
the underlying cluster's capacity is freed, or, in the bare-metal case,
returns the host to a pool of hosts available for the next placement.

## 8. Implementation variants

The bare-metal variant dedicates a physical machine to one service instance.
This is now rare outside of specialized workloads, for example a database
that wants direct access to NVMe storage without a hypervisor's I/O overhead,
or an on-premises deployment where the organization already owns the hardware
and virtualization would add no benefit. Cost and provisioning lead time are
the main drawbacks, since acquiring or reimaging a physical machine takes
minutes to days rather than the seconds a cloud API call takes for a VM or a
container.

The **Service per VM** variant, which Richardson lists as an explicit
refinement of this pattern on the pattern page itself (microservices.io,
"Pattern. Single Service Instance per Host", "Related patterns" section,
verified 2026-08-03), packages the service as a virtual machine image and
deploys each instance as a separate VM. This is the variant Richardson names
Netflix as using directly, packaging each service as an EC2 AMI and deploying
each instance as an EC2 instance (microservices.io, "Pattern. Service Instance
per VM", https://microservices.io/patterns/deployment/service-per-vm.html,
"Examples" section, verified 2026-08-03). The VM boundary gives the same
isolation guarantee as bare metal, cold-boot time is measured in tens of
seconds to a few minutes rather than hours, and cloud autoscaling groups can
launch and terminate VMs on demand, which is what makes this variant practical
at Netflix's scale.

The **Service per Container** variant, also listed by Richardson as a
refinement of the same parent pattern (microservices.io, "Pattern. Single
Service Instance per Host", "Related patterns" section, verified 2026-08-03),
packages the service as a container image, typically a Docker image, and
deploys each instance as a container. Richardson's own page for this
refinement states that Docker is an extremely popular way of packaging and
deploying services this way and names Kubernetes and Marathon among the
clustering frameworks used to run containers at scale
(microservices.io, "Pattern. Service Instance per Container",
https://microservices.io/patterns/deployment/service-per-container.html,
"Examples" section, verified 2026-08-03). Container startup is measured in
single-digit seconds, which is what makes this variant the default choice for
most organizations adopting the pattern today, and Heroku's dyno model is a
production example of this shape at the platform-as-a-service layer, where
Heroku documents that all dynos are strongly isolated from one another using
OS containerization, with additional custom hardening restricting access
between them (Heroku Dev Center, "Dynos and the Dyno Manager",
https://devcenter.heroku.com/articles/dynos, "Isolated and Secure" section,
verified 2026-08-03).

A fourth variant, less commonly discussed but structurally the same pattern,
is the **serverless function per invocation** shape, where a cloud provider's
function-as-a-service platform gives every concurrent invocation its own
execution environment, isolated from every other invocation of the same or a
different function. Richardson himself lists serverless deployment as an
alternative solution rather than a refinement of this pattern on the pattern
page (microservices.io, "Pattern. Single Service Instance per Host", "Related
patterns" section, verified 2026-08-03), and this entry follows that
distinction, since a serverless invocation is not a long-lived, addressable
host in the sense the rest of this pattern language assumes, and a cold-start
invocation does not carry the same monitoring or capacity-planning story a
dedicated host does. It is worth naming here because the isolation goal is
identical even though the mechanism and the pattern-language placement
differ.

A fifth structural variant worth naming explicitly, because it inverts the
usual justification for this pattern, is the **DaemonSet-style node agent**
shape used in Kubernetes. Here the "service" is not a business capability but
an infrastructure concern that must observe or act on every node in a
cluster, for example a log-shipping agent, a node-level monitoring exporter,
or a network plugin. Kubernetes' own documentation states that a DaemonSet
places a copy of a Pod on all, or some, nodes at all times, and names running a
cluster storage daemon, a logs collection daemon, and a node monitoring
daemon on every node as typical uses (Kubernetes documentation, "DaemonSet",
"DaemonSet" section, verified 2026-08-03). This is Service Instance per Host
applied at the infrastructure layer rather than the application layer, one
instance per host, enforced structurally by the scheduler rather than by
capacity planning, and it coexists on the same physical or virtual node as an
ordinary densely packed application Pod without contradiction, because the
DaemonSet's one-per-node instance and the application scheduler's
many-per-node instances are answering different placement questions at
different layers.

## 9. Known production uses

Netflix is the example Richardson names directly on the microservices.io
pattern page for the Service per VM refinement, packaging each service as an
Amazon EC2 AMI and deploying each service instance as a separate EC2 instance
(microservices.io, "Pattern. Service Instance per VM", "Examples" section,
verified 2026-08-03). Netflix's own open source Spinnaker project, which the
company built and describes as a multi-cloud continuous delivery platform
that manages deployments across cloud provider resources such as VM instance
groups on a per-application basis, is the tooling that operationalizes this
placement pattern across hundreds of Netflix services (Spinnaker project
documentation, "What is Spinnaker", https://spinnaker.io, verified
2026-08-03).

Heroku is a production example of the container-based refinement, where the
platform's own documentation states plainly that every dyno, Heroku's unit of
process execution, is strongly isolated from every other dyno using OS
containerization with additional custom hardening, and that some dyno tiers
carry their own dedicated compute instance or dedicated networking (Heroku
Dev Center, "Dynos and the Dyno Manager", "Isolated and Secure" section,
verified 2026-08-03). Every web process, worker process, or scheduled job a
Heroku customer runs is its own dyno, and the platform never places two
customers' processes, or even two of one customer's differently named
processes, inside the same isolated unit.

Kubernetes' DaemonSet controller is a third, currently maintained, widely
deployed production instance of this pattern, applied to infrastructure
agents rather than business services. The Kubernetes project's own
documentation lists running a cluster storage daemon, a logs collection
daemon, and a node monitoring daemon on every node as typical DaemonSet uses,
and states that as nodes are added to the cluster, Pods are added to them, and
as nodes are removed, those Pods are garbage collected (Kubernetes
documentation, "DaemonSet",
https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/,
verified 2026-08-03). Widely used infrastructure agents deployed this way in
real production Kubernetes clusters include the Datadog Agent, Fluentd and
Fluent Bit log collectors, the Prometheus Node Exporter, and Kubernetes' own
`kube-proxy` component, each of which is documented by its respective project
as intended for one-per-node deployment via a DaemonSet, guaranteeing exactly
one running instance of the agent per host in the cluster.

## 10. Consequences

The positive consequences follow directly from the forces the pattern
satisfies. Service instances are fully isolated from one another, so there is
no possibility of conflicting resource requirements, incompatible library
versions, or one service's process accidentally reading another's memory,
which is the exact benefit Richardson's pattern page states first
(microservices.io, "Pattern. Single Service Instance per Host", "Resulting
context" section, verified 2026-08-03). A service instance can consume at
most the resources of the single host it occupies, which turns a runaway
memory leak or an infinite loop into a contained, single-instance incident
rather than a cluster-wide one. Monitoring, capacity planning, and
troubleshooting are straightforward, because every signal from a host maps to
exactly one instance with no disaggregation step required. Deployment and
rollback of one instance can never partially affect an unrelated service that
happens to share infrastructure, since there is no shared infrastructure at
the host level. Security auditing and compliance boundary drawing are
simpler, because the host itself is a natural, defensible unit of scope.

The negative consequences are equally direct. Resource utilization is
potentially far lower than a densely packed alternative, since a service
instance that only needs a fraction of a host's CPU and memory still occupies
the entire host, and the unused capacity cannot be reclaimed by any other
workload, which is the exact drawback Richardson's page states
(microservices.io, "Pattern. Single Service Instance per Host", "Resulting
context" section, verified 2026-08-03). Cost scales with the number of hosts
rather than with actual resource consumption, which is expensive at high
service-instance counts, and this cost pressure is precisely what motivated
Google to build Borg around efficient task-packing, over-commitment, and
machine sharing rather than one-task-per-machine allocation (Verma et al.,
"Large-scale cluster management at Google with Borg", abstract, verified
2026-08-03). Autoscaling reaction time is bound by how quickly a whole host,
or a whole VM, can be provisioned and become ready, which for bare metal and
some VM images is measurably slower than scaling a container within an
already-running, already-warm node pool. Fleet-wide operational overhead
grows with host count independent of workload, since every host still needs
patching, an operating system lifecycle, and its own network configuration,
even when its single occupant barely uses it.

## 11. Failure modes and misuse

**Symptom.** Cloud spend grows linearly with service count while average CPU
utilization sits in the single digits across the fleet. **Cause.** The
organization applied Service Instance per Host uniformly to every service
regardless of traffic volume or isolation need, so hundreds of low-traffic
services each occupy a whole host or a whole VM sized for peak, not average,
load. **Fix.** Reserve this pattern for the services whose forces actually
justify it, latency-sensitive paths, regulated data boundaries, and
infrastructure agents, and move the long tail of low-traffic services to a
densely packed alternative such as Multiple Services per Host or a container
orchestrator's default bin-packing scheduler, which is exactly the trade the
pattern's own related-patterns list names as the alternative
(microservices.io, "Pattern. Single Service Instance per Host", "Related
patterns" section, verified 2026-08-03).

**Symptom.** A service that was supposed to be alone on its host is
intermittently slow, and the on-call engineer cannot find a co-located
neighbor to blame, yet the slowness correlates with deploys of a completely
different service. **Cause.** The pattern is being applied at the VM or
container layer but the underlying physical node, or the underlying
hypervisor, is shared with other tenants whose noisy behavior the isolation
layer does not fully contain, a known limitation of container-based isolation
in particular, since containers share a kernel and can contend for
kernel-level resources such as the page cache or network interface queues
even when each container is nominally dedicated to one service. **Fix.**
Verify the actual isolation boundary matches the isolation the incident
response assumes. If kernel-level contention is unacceptable, move to the VM
or bare-metal refinement, which isolates at a boundary containers do not
fully replicate.

**Symptom.** A DaemonSet-style one-per-node agent is missing from some nodes
in a cluster, and the gap is only noticed when an outage happens on exactly
the node that was missing the log collector or the monitoring exporter.
**Cause.** Node taints, resource pressure, or a misconfigured node selector
prevented the DaemonSet controller from scheduling its Pod onto every
eligible node, which silently breaks the one-instance-per-host invariant this
variant exists to guarantee. **Fix.** Alert on DaemonSet Pod count against
expected node count as a first-class health signal, not as an afterthought,
since the entire value of this pattern's infrastructure-agent variant depends
on the invariant holding on every host without exception.

**Symptom.** Teams provision a new dedicated host for every new service
instance by copying an old runbook, and the runbook has drifted from the
current build system, so new hosts are inconsistently configured. **Cause.**
Treating one instance per host as a manual provisioning discipline instead of
an enforced placement rule, so the pattern's isolation benefit is real but
its consistency benefit is lost to human error. **Fix.** Encode the
packaging step, whether it produces a VM image, a container image, or a
bare-metal provisioning script, as a single, versioned, automated build
artifact, which is the exact role Richardson assigns the problem statement,
how are services packaged and deployed, and is the reason this pattern's
implementation variants each name a specific artifact type rather than
leaving packaging as an undefined manual step.

## 12. Trade-off matrix

| Force | Service Instance per Host | Multiple Services per Host | Service per Container (Kubernetes bin-packing) |
|---|---|---|---|
| Isolation from noisy neighbors | Strongest, no co-located unrelated workload at the host level | Weakest, unrelated processes share the same OS and resources directly | Strong at the process and namespace level, weaker at the kernel and hardware level than a dedicated host |
| Resource utilization efficiency | Weakest, unused host capacity cannot be reclaimed by another service | Strongest, a host's spare capacity is available to any co-located service | Strong, an orchestrator's scheduler bin-packs many containers per node to raise utilization |
| Provisioning and scale-out latency | Slowest for bare metal and most VM images, tens of seconds to minutes | Fast, a new instance is one more process or JVM on an already-running host | Fastest, a new container starts on an already-warm node in single-digit seconds |
| Monitoring and blast-radius clarity | Every host metric maps to exactly one instance, no disaggregation needed | Requires per-process metric attribution on a shared host | Requires per-container metric attribution, but the container runtime typically provides it natively |
| Operational overhead per host | Highest per unit of useful work, since idle capacity still needs patching and lifecycle management | Lower, since fewer hosts carry the same number of instances | Lowest, since the orchestrator automates most host lifecycle work and hosts are shared |
| Fit for regulated or compliance-bound isolation | Best fit, a dedicated host is a natural, defensible compliance boundary | Poor fit, shared hosts complicate compliance scoping | Moderate fit, namespace isolation helps but rarely satisfies a strict regulatory boundary on its own |

## 13. Related and incompatible patterns

Service per VM and Service per Container are refinements of this pattern, not
alternatives to it, since both satisfy the same one-instance-per-host
invariant, they simply choose a different, progressively cheaper isolation
mechanism to enforce it, exactly as Richardson's pattern page lists them
(microservices.io, "Pattern. Single Service Instance per Host", "Related
patterns" section, verified 2026-08-03). Serverless deployment is named as an
alternative solution rather than a refinement, because a serverless
invocation's per-invocation isolation is structurally similar in spirit but
lacks the addressable, long-lived host this pattern language otherwise
assumes.

Multiple Services per Host is the direct, named, incompatible alternative,
the two patterns cannot both be true of the same host at the same time, since
one asserts exactly one instance per host and the other explicitly allows
more than one. An organization can, and often does, apply Service Instance
per Host to a small set of workloads that need it while applying Multiple
Services per Host, or a container orchestrator's default bin-packing, to
everything else, which is not a contradiction, it is choosing the right
pattern per workload rather than one pattern for the whole fleet.

Service Registry composes naturally with this pattern, since every new host
that comes up with a freshly placed instance needs to announce its address so
traffic can find it, and every host that is retired needs to deregister
cleanly, the same registration and deregistration steps this entry's dynamics
section walks through.

Self-Contained Service composes with this pattern at a different layer,
because a self-contained service's requirement to be independently
deployable and independently releasable is easier to satisfy when its
instances are not entangled with an unrelated service's instances on a
shared host, though a self-contained service can equally well be deployed
using Multiple Services per Host if the density trade-off is acceptable for
that particular service.

The Sidecar pattern and this pattern's DaemonSet-style infrastructure-agent
variant are close cousins but answer different questions, a sidecar shares a
Pod, and therefore a host, with exactly the one application container it
supports, while a DaemonSet-style agent runs once per host regardless of how
many application Pods that host carries. Both achieve a form of
per-something isolation, one per-application, one per-host, and a
production system commonly uses both at once without conflict.

## 14. Refactoring path in and out

To introduce this pattern into a system currently running Multiple Services
per Host, start by identifying the specific services whose forces actually
justify the change, the latency-sensitive path, the regulated-data service,
or the resource-unpredictable service, rather than migrating every service at
once. Package that service's build artifact into whichever variant fits the
organization's existing tooling, a container image if a container
orchestrator is already in use, a VM image if the organization already
provisions VMs per environment, or a bare-metal image only if the specific
hardware requirement demands it. Update the placement authority, whether that
is an autoscaling group's launch configuration, a Kubernetes node affinity
and anti-affinity rule, or a manual provisioning runbook, to enforce the
one-instance-per-host invariant for that service specifically. Verify the
service's monitoring dashboards now attribute every host-level metric to the
single instance cleanly, which is the fastest way to confirm the migration
actually took effect rather than merely changing where the artifact runs
without changing how many instances share a host.

To remove this pattern, generally because the cost of dedicated hosts has
become harder to justify than the isolation the pattern buys, first confirm
which of the pattern's original forces are still in play for the specific
service. If regulatory isolation is still required, this pattern cannot be
safely removed regardless of cost pressure, and the refactor should stop
there. If the original justification was simply an inherited default rather
than an active force, move the service into a shared host or a densely
packed orchestrator's default scheduling behavior, watch its monitoring
dashboards for any regression in tail latency or noisy-neighbor incidents for
at least one full traffic cycle, including peak load, before declaring the
migration complete, and keep the ability to move the service back to a
dedicated host quickly, since the whole point of testing under real peak
traffic is to catch a regression the pattern was quietly preventing.

## 15. Testing and verification

Testing this pattern is largely an infrastructure-verification exercise
rather than a unit-testing exercise, because the pattern makes no claim about
the internal structure of the service's code, only about where and how many
copies of it run.

The most direct test is a placement invariant test. After every deploy or
autoscale event, assert that no host in the fleet carries more than one
service instance, which is exactly the invariant the code samples accompanying
this entry check programmatically, the TypeScript scheduler rejects a second
placement attempt on an already-occupied host, and the Go placement function
returns an explicit error the moment a node with `HasInstance` set true is
offered a second instance. In a Kubernetes-based deployment, the equivalent
check is verifying that a DaemonSet's `desired`, `current`, and `ready` Pod
counts all equal the cluster's eligible node count, since any gap between
those numbers means the one-per-node invariant is currently violated.

Resource-isolation testing verifies the isolation the pattern is meant to
buy actually holds under load. A load test that saturates one service
instance's host should show zero measurable impact on any other service's
p99 latency, and if it does not, the isolation boundary is leaking, most
commonly through a shared network path, a shared storage backend, or, in the
container refinement, shared kernel resources the container runtime does not
fully partition.

Failure-injection testing should confirm that killing one host's instance
never cascades to a sibling host, which is trivially true by construction if
the placement invariant holds, but is worth verifying explicitly because a
misconfigured health check or a shared upstream dependency, for example a
single database connection pool the whole fleet shares, can reintroduce a
cross-instance failure mode the pattern otherwise eliminates at the host
level.

Cost and utilization testing, while not correctness testing in the strict
sense, belongs in the same verification suite for this pattern specifically,
since the pattern's central trade-off is cost against isolation, and a
regression in that trade-off, for example a service instance's actual CPU
and memory use falling far below what its dedicated host provides, is a
signal worth alerting on even though nothing is functionally broken.

## 16. Observability signals

A healthy instance of this pattern shows a one-to-one mapping between hosts
and running service instances in the fleet inventory at all times, with zero
hosts reporting more than one instance and zero hosts reporting zero
instances for longer than the expected placement latency window. Per-host
CPU, memory, disk, and network metrics attribute cleanly to a single named
service and a single instance identifier, with no metric requiring
disaggregation logic downstream.

A failing or degraded instance of this pattern shows a growing count of hosts
either sitting idle with no instance assigned, which signals the placement
authority is falling behind demand or is stuck, or, more seriously, showing
more than one instance, which signals the one-per-host invariant has been
violated, most commonly by a manual deploy that bypassed the placement
authority. For the DaemonSet-style infrastructure-agent variant specifically,
the health signal to watch is the gap between a DaemonSet's desired Pod count
and its ready Pod count, since Kubernetes' own controller model treats that
gap as the primary indicator of whether every eligible node currently carries
its required agent (Kubernetes documentation, "DaemonSet", verified
2026-08-03).

Utilization dashboards for this pattern should track the ratio of a service
instance's actual resource consumption to its host's total capacity, since
that ratio is the direct, numeric measure of the pattern's central cost
trade-off, a ratio that stays persistently low across many instances is the
earliest, cheapest signal that the pattern is being over-applied relative to
the forces that justify it.

## 17. Security and privacy implications

This is largely engineering judgement rather than a sourced claim, reasoned
from the isolation properties the pattern's own forces and consequences
already establish.

Dedicating a host to one service instance closes an entire class of
cross-tenant attack, since a compromised process on one host has no memory,
file descriptor, or kernel namespace in common with any other service's
process, which is a meaningfully stronger boundary than process-level
isolation on a shared host. This makes the pattern a reasonable default for
services that handle secrets, regulated personal data, or payment card data,
where an auditor is likely to ask directly whether a given service's runtime
environment is shared with anything outside its own compliance scope, a
question this pattern answers cleanly.

The pattern does not, by itself, secure the network path between hosts, and a
compromised instance on its own dedicated host can still reach any service it
is network-permitted to reach, so network segmentation, mutual TLS between
services, and least-privilege service-to-service authorization remain
necessary regardless of host-level isolation. The pattern also does not
reduce the attack surface of the host's own operating system, and in fact
increases the total number of operating system instances an organization
must patch and monitor compared to a densely packed alternative, which is a
real operational security cost that should be weighed against the isolation
benefit rather than assumed away.

For the container-based refinement specifically, the isolation is weaker than
a dedicated VM or bare-metal host, because containers on the same node share
a kernel, and a kernel-level vulnerability, or a container escape, can in
principle cross the boundary this pattern otherwise treats as absolute. Where
the threat model specifically includes kernel-level compromise, the VM or
bare-metal refinement, or a hardened container runtime with additional
sandboxing, is the more defensible choice.

## 18. References

microservices.io, "Pattern. Single Service Instance per Host", Chris
Richardson, https://microservices.io/patterns/deployment/single-service-per-host.html,
verified 2026-08-03.

microservices.io, "Pattern. Service Instance per VM", Chris Richardson,
https://microservices.io/patterns/deployment/service-per-vm.html, verified
2026-08-03.

microservices.io, "Pattern. Service Instance per Container", Chris
Richardson, https://microservices.io/patterns/deployment/service-per-container.html,
verified 2026-08-03.

microservices.io, "Pattern. Multiple Service Instances per Host", Chris
Richardson, https://microservices.io/patterns/deployment/multiple-services-per-host.html,
verified 2026-08-03.

Chris Richardson, *Microservices Patterns*, Manning Publications, 2019,
chapter 12, "Deploying microservices".

Sam Newman, *Building Microservices*, 2nd edition, O'Reilly Media, 2021,
chapter on deployment, discussion of single-purpose hosts.

Kubernetes documentation, "DaemonSet",
https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/, verified
2026-08-03.

Kubernetes documentation, "Assigning Pods to Nodes",
https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/,
verified 2026-08-03.

Heroku Dev Center, "Dynos and the Dyno Manager",
https://devcenter.heroku.com/articles/dynos, verified 2026-08-03.

Abhishek Verma, Luis Pedrosa, Madhukar Korupolu, David Oppenheimer, Eric
Tune, and John Wilkes, "Large-scale cluster management at Google with Borg",
EuroSys 2015, Google Research publication page,
https://research.google/pubs/large-scale-cluster-management-at-google-with-borg/,
verified 2026-08-03.

Spinnaker project documentation, "What is Spinnaker", https://spinnaker.io,
verified 2026-08-03.

## Code examples

The examples below model the placement decision this pattern makes, one
service instance to one host, enforced as an explicit constraint a scheduler
checks and rejects a violation of, rather than modeling the service's own
business logic, since this pattern is a deployment and placement concern, not
an in-process design pattern.

### TypeScript, a capacity-aware placement scheduler

```typescript
interface Host {
  id: string;
  cpuCores: number;
  memoryMb: number;
}

interface ServiceInstance {
  id: string;
  serviceName: string;
  cpuCores: number;
  memoryMb: number;
}

class SingleInstancePerHostScheduler {
  private assignments = new Map<string, ServiceInstance>();

  constructor(private hosts: Host[]) {}

  place(instance: ServiceInstance): string {
    const candidate = this.hosts.find((host) => {
      const occupied = this.assignments.has(host.id);
      const fits = host.cpuCores >= instance.cpuCores && host.memoryMb >= instance.memoryMb;
      return !occupied && fits;
    });
    if (!candidate) {
      throw new Error(`no free host can host instance ${instance.id} of ${instance.serviceName}`);
    }
    this.assignments.set(candidate.id, instance);
    return candidate.id;
  }

  release(hostId: string): void {
    this.assignments.delete(hostId);
  }

  utilization(hostId: string): number {
    const host = this.hosts.find((h) => h.id === hostId);
    const instance = this.assignments.get(hostId);
    if (!host || !instance) return 0;
    return instance.memoryMb / host.memoryMb;
  }
}

function main() {
  const hosts: Host[] = [
    { id: "host-a", cpuCores: 4, memoryMb: 8192 },
    { id: "host-b", cpuCores: 8, memoryMb: 16384 },
  ];
  const scheduler = new SingleInstancePerHostScheduler(hosts);

  const orderService: ServiceInstance = { id: "order-1", serviceName: "order-service", cpuCores: 2, memoryMb: 4096 };
  const paymentService: ServiceInstance = { id: "payment-1", serviceName: "payment-service", cpuCores: 4, memoryMb: 12288 };

  const hostForOrder = scheduler.place(orderService);
  const hostForPayment = scheduler.place(paymentService);
  console.log(`order-service placed on ${hostForOrder}, utilization ${scheduler.utilization(hostForOrder)}`);
  console.log(`payment-service placed on ${hostForPayment}, utilization ${scheduler.utilization(hostForPayment)}`);

  try {
    scheduler.place({ id: "order-2", serviceName: "order-service", cpuCores: 1, memoryMb: 1024 });
  } catch (err) {
    console.log(`third placement rejected as expected: ${(err as Error).message}`);
  }
}

main();
```

Compiled with `npx tsc --target es2020 --module commonjs` and run with
`node`, verified locally. Output confirms both real placements succeed and
the third placement, which has no remaining free host, is rejected with the
exact error the invariant should produce.

### Python, a host agent that owns one instance's full lifecycle

```python
from __future__ import annotations
import subprocess
import time
from dataclasses import dataclass


@dataclass
class ServiceInstanceSpec:
    name: str
    command: list[str]
    max_restarts: int = 3


class HostAgent:
    """Owns the full lifecycle of exactly one service instance on this host.

    Mirrors the operational shape of a systemd unit or a supervisord process
    group dedicated to a single service instance per host.
    """

    def __init__(self, spec: ServiceInstanceSpec) -> None:
        self.spec = spec
        self.process: subprocess.Popen | None = None
        self.restart_count = 0

    def start(self) -> None:
        if self.process is not None and self.process.poll() is None:
            raise RuntimeError(f"{self.spec.name} is already running on this host")
        self.process = subprocess.Popen(self.spec.command)

    def health_check(self) -> bool:
        if self.process is None:
            return False
        return self.process.poll() is None

    def supervise_once(self) -> None:
        if self.health_check():
            return
        if self.restart_count >= self.spec.max_restarts:
            raise RuntimeError(f"{self.spec.name} exceeded max restarts, host is unhealthy")
        self.restart_count += 1
        self.start()

    def stop(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            self.process.wait(timeout=5)


def main() -> None:
    spec = ServiceInstanceSpec(name="order-service-1", command=["python3", "-c", "import time; time.sleep(0.3)"])
    agent = HostAgent(spec)
    agent.start()
    print(f"{spec.name} started, healthy={agent.health_check()}")
    time.sleep(0.5)
    print(f"{spec.name} exited on its own, healthy={agent.health_check()}")
    agent.supervise_once()
    print(f"{spec.name} restarted by host agent, restart_count={agent.restart_count}")
    agent.stop()


if __name__ == "__main__":
    main()
```

Run with `python3 host_agent.py`, verified locally. The `HostAgent` is
deliberately scoped to exactly one `ServiceInstanceSpec`, mirroring the
pattern's own structural rule, a host owns one instance for its entire
lifetime, never a pool of instances it multiplexes between.

### Go, a one-instance-per-node placement validator

```go
package main

import (
	"fmt"
)

type Node struct {
	ID           string
	HasInstance  bool
	CPUAvailable int
}

type PlacementRequest struct {
	ServiceName string
	CPURequired int
}

// oneInstancePerNode mirrors a Kubernetes DaemonSet-style placement rule.
// exactly one instance of the service lands on each eligible node, never two
// on one node and never a node left without a required agent.
func oneInstancePerNode(nodes []*Node, req PlacementRequest) ([]string, error) {
	placed := make([]string, 0, len(nodes))
	for _, n := range nodes {
		if n.HasInstance {
			return nil, fmt.Errorf("node %s already hosts an instance, violates one-per-host", n.ID)
		}
		if n.CPUAvailable < req.CPURequired {
			return nil, fmt.Errorf("node %s lacks %d cpu for %s", n.ID, req.CPURequired, req.ServiceName)
		}
		n.HasInstance = true
		n.CPUAvailable -= req.CPURequired
		placed = append(placed, n.ID)
	}
	return placed, nil
}

func main() {
	nodes := []*Node{
		{ID: "node-1", CPUAvailable: 2},
		{ID: "node-2", CPUAvailable: 2},
		{ID: "node-3", CPUAvailable: 1},
	}
	req := PlacementRequest{ServiceName: "log-collector", CPURequired: 1}

	placed, err := oneInstancePerNode(nodes, req)
	if err != nil {
		fmt.Println("placement failed.", err)
		return
	}
	fmt.Printf("placed %s on %d of %d nodes. %v\n", req.ServiceName, len(placed), len(nodes), placed)

	_, err = oneInstancePerNode(nodes, req)
	if err != nil {
		fmt.Println("second pass correctly rejected.", err)
	}
}
```

Run with `go run main.go`, verified locally. This models the DaemonSet-style
variant from dimension 8, placing one instance per node across an entire
fleet in a single pass and rejecting any attempt to place a second instance
on an already-occupied node, the exact invariant a real DaemonSet controller
enforces.

Java, Rust, and Swift are not included as separate samples for this entry.
This pattern is a deployment and infrastructure placement concern rather than
an in-language design pattern, and the three samples above already cover a
static-typed compiled language, a dynamic language used for operational
tooling, and a systems language typical of orchestrator internals, which
between them represent the idiomatic language choices actually used to build
placement and scheduling logic in production, without the exercise becoming a
mechanical restatement of the same twenty lines in five more syntaxes.
