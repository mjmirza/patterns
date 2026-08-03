---
name: Service Instance per VM
slug: service-instance-per-vm
family: 10-microservices
category: Deployment
aliases: [Service per VM, One Service per Host, Single Service per Machine Image, AMI-per-service]
first_described: "Chris Richardson, microservices.io, deployment patterns, and Microservices Patterns, Manning, 2019"
maturity: established
related: [service-per-container, sidecar, ambassador, health-check-api, self-registration, service-registry, circuit-breaker]
incompatible_with: [service-instance-per-container, serverless-deployment]
verified: 2026-08-02
---

# Service Instance per VM

## 1. Name, aliases, and lineage

The canonical name is Service Instance per VM. It is catalogued as a deployment
pattern for microservice architectures on Chris Richardson's microservices.io
site, in the deployment patterns section, under the page "Deploy a service
instance per VM". The page states the solution as "package the service as a
virtual machine image and deploy each service instance as a separate VM"
(https://microservices.io/patterns/deployment/service-per-vm.html, fetched and
verified 2026-08-02). The same pattern appears as a named deployment strategy
in Chris Richardson, *Microservices Patterns. With Examples in Java*, Manning
Publications, 2019, chapter 12, "Deploying microservices", where deployment
onto a virtual machine per service instance is contrasted with container and
serverless deployment as one of three general strategies for packaging and
running a microservice.

Common aliases in practice. **Service per VM** and **One Service per Host**,
used interchangeably in operations writing when the emphasis is on the
one-to-one binding between a running service process and a dedicated compute
host, whether that host is virtualized or bare metal. **Single Service per
Machine Image** and **AMI-per-service**, used specifically inside the Amazon
Web Services ecosystem, where the unit that is built and versioned is the
Amazon Machine Image rather than the VM instance itself, and a fleet of
identical VM instances is launched from that one image (Amazon Web Services,
"Amazon Machine Images (AMI)", AWS EC2 User Guide,
https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AMIs.html, fetched and
verified 2026-08-02, which states an AMI "provides the software that is
required to set up and boot an Amazon EC2 instance" and that "you can launch
multiple instances from a single AMI when you require multiple instances with
the same configuration").

The pattern predates the word microservice. It is the deployment model that
service-oriented architecture inherited directly from the shift away from
physical, dedicated servers into infrastructure as a service in the late
2000s, and it is best understood as the old model of one application on one
machine done again with the machine now being a virtual machine created and
destroyed on demand, rather than as a new invention. Richardson's own framing
on microservices.io is explicit that the pattern is a refinement of the more
general Single Service per Host idea, narrowed to the specific case where the
host is a virtual machine rather than a physical server or a container.

## 2. Problem and context

A team has already split a system into microservices, one deployable unit per
business capability, following the Microservice Architecture pattern. Splitting
the code was the easy half of the decision. The team now has to decide how each
of those services actually gets onto a running machine, how many copies of each
service run at once, how a copy is replaced when it crashes or when a new
version ships, and how the whole thing avoids one service's runaway memory
leak taking down every other service on the same box.

The concrete situation that creates the need runs like this. Before
microservices, an organization typically ran a small number of monolithic
applications, each given its own physical server or its own dedicated virtual
machine, sized once at provisioning time and rarely touched again. That model
breaks the moment the architecture fans out into tens or hundreds of
independently deployable services, because provisioning a dedicated physical
machine per service is both financially absurd and operationally too slow for
the release cadence a microservice architecture is meant to enable. At the same
time, the organization usually already has deep experience running virtual
machines. It has an existing hypervisor or cloud VM product, existing
monitoring tooling built around VM metrics, existing security scanning built
around a machine image, and an existing on-call culture that understands what
a VM crash looks like. Service Instance per VM is the pattern that answers how
to deploy a hundred services using exactly that existing muscle memory, one VM
instance per running copy of one service, provisioned from infrastructure as a
service.

The pattern sits at a specific point in the history of deployment technology.
It came first, ahead of the container-per-service pattern it is most often
compared against, because widespread, cheap, on-demand virtual machines
predate widespread, production-grade container orchestration by several
years. Netflix's well-documented move onto Amazon EC2, beginning around 2008
and largely complete by 2011, is the most frequently cited real case of this
pattern applied at scale, packaging each of its many internally developed
services as its own Amazon Machine Image and running a fleet of EC2 instances
per service. This production case, including the summary that Netflix
packages each service as an EC2 AMI and deploys each instance as an EC2
instance, is recorded on the microservices.io Service Instance per VM page
cited above, fetched and verified 2026-08-02.

The context in which the pattern belongs, stated plainly, is this. The
organization has already committed to a microservice architecture, already
has or is willing to build machine-image tooling, and needs strong isolation
between service instances more than it needs fast build and deploy cycles.

## 3. Forces

The following pressures are in direct tension, and the pattern resolves them
by leaning hard toward isolation and away from speed.

- **Isolation.** Strongly favoured. Every service instance gets the entire VM
  to itself, its own kernel, its own filesystem, its own network stack, its
  own resource limits enforced by the hypervisor rather than by a
  best-effort cgroup. A memory leak, a runaway thread pool, or a compromised
  dependency in one service cannot directly starve or observe another
  service's process, because there is no other process on the machine.
- **Build and deploy speed.** Sacrificed, and this is the pattern's defining
  cost. Building a machine image means installing an operating system,
  applying patches, installing a language runtime, installing the
  application, and then snapshotting the whole disk, which for a moderately
  sized image commonly takes several minutes rather than the seconds a
  container image build takes. The microservices.io page cited above records
  this directly as a drawback, that building a VM image is slow and time
  consuming, fetched and verified 2026-08-02.
- **Resource density.** Sacrificed. A VM reserves a whole allocation of CPU
  and memory for the hypervisor and guest kernel before the application ever
  runs, and a fleet of small services each wrapped in a full VM wastes far
  more idle capacity than the same services packed several to a host inside
  containers.
- **Operational maturity reuse.** Favoured, and this is the pattern's most
  underrated benefit. Every piece of tooling an organization already has for
  patching, scanning, snapshotting, auditing, and billing a virtual machine
  applies unmodified to a service instance, because a service instance is a
  virtual machine.
- **Multi-tenancy trust boundary.** Favoured. Where the surrounding platform,
  the cloud provider or the on-premises hypervisor, does not offer a
  container isolation boundary the organization trusts for adversarial or
  regulated workloads, the VM boundary is the trust boundary already accepted
  by security and compliance teams, and reusing it avoids a fresh accreditation
  cycle.
- **Elasticity latency.** Sacrificed relative to containers, favoured over
  physical hardware. A VM boots in tens of seconds to a couple of minutes
  depending on the image and the cloud provider, which is fast against
  physical provisioning but slow against the sub-second start of an already
  running container being handed a new request, or the few seconds a
  container image pull and start typically takes.
- **Version pinning per service.** Favoured. Because each service owns its
  entire operating system image, one service can sit on an old, unpatched
  kernel or an old language runtime version indefinitely without that choice
  leaking into any other service's environment, which is a genuine advantage
  during a slow migration but also the seed of the drift failure mode covered
  in dimension 11.

The pattern does not give up anything for free. It buys strong,
well-understood, tooling-compatible isolation at the direct cost of image
build time, deploy latency, and machine utilization, and that trade is the
entire reason to choose it or to reject it.

## 4. Applicability and non-applicability

Reach for Service Instance per VM when the following hold.

- The organization already runs a mature virtual machine platform, whether
  that is a public cloud IaaS product or an on-premises hypervisor, and
  already has working pipelines to bake, patch, scan, and roll out machine
  images.
- Regulatory, contractual, or internal security policy requires the stronger
  isolation boundary a hypervisor provides over the kernel-namespace boundary
  a container provides, which matters most for multi-tenant workloads running
  code the organization does not fully control.
- The services being deployed are heterogeneous at the operating system
  level, for example a mix of Windows Server and Linux services, or services
  that need direct hardware access, custom kernel modules, or a specific
  kernel version that a shared container host cannot offer per service.
- The team is small and the service count is modest enough that per-service
  image-build time is not yet a bottleneck on release cadence, and the team
  wants to defer the operational investment a container orchestrator such as
  Kubernetes demands.
- The deployment target is a private cloud or a hosting provider that offers
  mature VM primitives, such as instance auto scaling groups and health-check
  driven replacement, but does not offer a managed container orchestration
  product the team trusts for production.

Do NOT reach for Service Instance per VM in these cases, and the reason
matters more than the rule.

- **The service count is large and growing, and deploy velocity matters more
  than isolation strength.** A fleet of fifty or more services each requiring
  a multi-minute image bake and a multi-second boot before it can serve
  traffic turns every release into a slow, expensive operation, and Service
  Instance per Container removes that cost with a materially weaker but for
  most workloads sufficient isolation boundary. Applying VM-per-service here
  is choosing the wrong tool because the isolation the pattern buys was never
  the scarce resource, deploy speed was.
- **The workload is genuinely event-driven, spiky, or idle most of the time.**
  A VM that must stay booted to be ready for the next request wastes money and
  capacity relative to a serverless deployment that scales to zero. Applying
  VM-per-service to a rarely invoked webhook handler is paying for a
  reservation nobody is using.
- **The organization has no existing VM-baking pipeline and would have to
  build one from nothing.** Building an image pipeline, an image versioning
  scheme, a patch cadence, and a rollback procedure is a real, ongoing
  operational investment. A team starting fresh with no such pipeline and no
  regulatory reason to accept VM isolation is almost always better served
  starting with containers, where the equivalent tooling is more standardized
  and the community support is deeper.
- **Cost per instance is a binding constraint and utilization matters more
  than isolation.** Because each VM reserves its own kernel and its own
  minimum memory footprint, packing many low-traffic services onto shared VM
  capacity via containers is materially cheaper, and choosing VM-per-service
  here burns budget on isolation the workload does not need.
- **The service must scale in seconds in response to a traffic spike.** Boot
  time on the order of tens of seconds to minutes makes VM-per-service a poor
  fit for workloads that need to absorb a sudden burst faster than a fresh
  instance can come up, unless the team keeps a standing over-provisioned
  buffer, which reintroduces the cost problem above.
- **The service is a short-lived batch job or a single function invoked on an
  event.** A whole VM lifecycle, boot, run, terminate, is heavyweight
  machinery for a workload that finishes in milliseconds to seconds, and a
  serverless function deployment fits that shape directly without the boot
  latency tax.

## 5. Structure

Five participants, named by the role each plays in the deployed system rather
than by a generic infrastructure term.

- **Service.** The unit of independently deployable business capability, the
  same Service that the Microservice Architecture pattern defines at the
  architecture level. It has exactly one runtime process type associated with
  it in this pattern, even though many running copies of that process exist
  simultaneously.
- **Machine Image.** The baked, versioned artifact that contains the
  operating system, the language runtime, every operating system and
  application dependency, and the compiled or interpreted service code,
  ready to boot with no further installation step. This is the unit that a
  build pipeline produces and that a release actually promotes through
  environments. On AWS this is an Amazon Machine Image, on Azure a Managed
  Image or Shared Image Gallery image, on Google Cloud a Compute Engine
  image, and on-premises typically a VMware template or a Packer-produced
  QEMU or VHD image.
- **VM Instance.** A single running virtual machine booted from the Machine
  Image, hosting exactly one Service process bound to the machine's network
  interface. This is the participant the pattern's name refers to directly,
  the one-to-one pairing of one running copy of a service and one virtual
  machine.
- **Instance Group.** The set of VM Instances currently running for one
  Service, managed as a unit for scaling and replacement. This maps to an AWS
  Auto Scaling Group, an Azure Virtual Machine Scale Set, or a Google Cloud
  Managed Instance Group, and it is what makes the pattern operable rather
  than a manual per-machine chore, since the group owns launching a
  replacement when a health check fails and adding instances when load
  crosses a threshold.
- **Hypervisor or IaaS Control Plane.** The layer beneath every VM Instance
  that enforces the isolation boundary the pattern depends on, schedules
  physical resources, and exposes the API a build pipeline calls to bake a
  Machine Image and the API an Instance Group calls to launch or terminate a
  VM Instance. This participant does the actual isolation work. The pattern's
  isolation benefit is a property of this layer, not of the Service code.

Relationships. Machine Image is built once per Service version and versioned
independently of any running instance. Instance Group holds a reference to
exactly one Machine Image version at a time and is the only participant
permitted to create or destroy VM Instances. VM Instance runs exactly one
Service process and never shares its machine with any other Service. The
Hypervisor or IaaS Control Plane sits beneath every other participant and is
consulted by the build pipeline to produce a Machine Image and by the
Instance Group to manage VM Instance lifecycle, but it has no direct
relationship to the Service's business logic.

## 6. ASCII structure diagram

```
  build pipeline                     hypervisor / IaaS control plane
  +---------------+                  +----------------------------+
  | source code   |                  |  compute capacity           |
  | + dependencies|--- bake -------->|  network + storage          |
  | + OS base     |                  |  isolation enforcement      |
  +---------------+                  +----------------------------+
          |                                       ^
          v                                       | launch / terminate
  +------------------+                            |
  |   Machine Image   |  v3, v4, v5 ...            |
  |  (AMI / VM image)  |                           |
  +------------------+                            |
          |                                       |
          | referenced by                         |
          v                                       |
  +--------------------------------------------------------------+
  |                       Instance Group (Service A)               |
  |  min=2  max=6  desired=3  health check GET /health every 10s  |
  +--------------------------------------------------------------+
          |                    |                    |
          v                    v                    v
  +---------------+   +---------------+   +---------------+
  |  VM Instance  |   |  VM Instance  |   |  VM Instance  |
  |---------------|   |---------------|   |---------------|
  | Service A proc|   | Service A proc|   | Service A proc|
  | port 8080     |   | port 8080     |   | port 8080     |
  | whole host OS |   | whole host OS |   | whole host OS |
  +---------------+   +---------------+   +---------------+
          ^                    ^                    ^
          |                    |                    |
          +--------- load balancer / service discovery
                      routes traffic to healthy instances only

  A second Service B has its own Machine Image and its own Instance
  Group, entirely separate from Service A. No VM Instance ever hosts
  more than one Service's process.
```

## 7. Dynamics

The runtime flow that matters most for this pattern is not a single request,
it is the lifecycle of a deployment, since the pattern is a deployment
pattern and the interesting behaviour happens at release and replacement time
rather than inside a single request handler.

```
Build system      Machine Image        Instance Group      VM Instance (new)   VM Instance (old)   Load Balancer
     |                    |                    |                    |                    |               |
     |-- compile ------->|                    |                    |                    |               |
     |-- bake image ---->|                    |                    |                    |               |
     |                    |-- image v5 ready ->|                    |                    |               |
     |                    |                    |-- launch --------->|                    |               |
     |                    |                    |                    |-- boot OS -------->|               |
     |                    |                    |                    |-- start service -->|               |
     |                    |                    |                    |<-- healthy --------|               |
     |                    |                    |<-- healthy --------|                    |               |
     |                    |                    |-- register ------------------------------------------->|
     |                    |                    |                    |                    |               |
     |                    |                    |                    |     traffic now split old + new    |
     |                    |                    |-- drain -------------------------------->|               |
     |                    |                    |                    |                    |-- deregister ->|
     |                    |                    |                    |                    |-- SIGTERM ---->|
     |                    |                    |                    |                    | (graceful stop)|
     |                    |                    |-- terminate ---------------------------->|               |
     |                    |                    |                    |                    |               |
     |                    |                    |          rolling replacement continues instance by      |
     |                    |                    |          instance until every old-image VM is gone       |
```

Two timing properties are specific to this pattern and worth stating plainly.
First, the interval between launch and healthy is dominated by VM boot
time, which is orders of magnitude larger than the equivalent interval for a
container, because the guest operating system itself must boot before the
Service process can even start. Second, a rolling deployment across an
Instance Group necessarily runs two Machine Image versions simultaneously for
some period, old-version VM Instances and new-version VM Instances answering
the same load-balanced traffic at once, so every release of a Service under
this pattern is implicitly a brief canary and the Service must tolerate two
versions of itself being live together, which is the same requirement the
Blue-Green Deployment and Canary Release patterns make explicit at the
infrastructure level.

## 8. Implementation variants

**Golden image, fully baked.** The Machine Image contains the operating
system, the runtime, and the compiled application, with no further
installation step at boot. Boot time is minimized since nothing is
downloaded or installed after launch. Cost is a slower, heavier build
pipeline and a new full image for every code change, however small.

**Base image plus bootstrap script.** The Machine Image contains only the
operating system and the runtime, and a boot-time script, commonly delivered
as cloud-init user data on AWS, Azure, and Google Cloud, downloads and
installs the current application version at first boot. This shortens the
image build cycle because the base image changes rarely, at the direct cost
of a slower and less deterministic instance boot, since the boot script now
depends on network access to an artifact store at launch time, which is a
real production failure mode covered in dimension 11.

**Immutable, versioned AMI per release, Netflix's documented model.**
Every code change produces a brand new, fully baked Machine Image, tagged
with a build number, and no VM Instance is ever patched in place after
launch. Rollback is replacing the Instance Group's referenced image version
and rolling instances, never editing a running machine. This is the variant
Netflix's tooling automated, baking a fresh AMI on every build so that
instances are never patched, they are replaced. This immutable philosophy is
the direct rationale behind Netflix's documented move to per-service AMI
baking on EC2, as recorded in the microservices.io production example cited
in dimension 9.

**Auto scaling group with health-check-driven replacement.** The Instance
Group continuously polls a health-check endpoint, per the Health Check API
pattern, on each VM Instance and automatically terminates and relaunches any
instance that fails the check, without human intervention. This variant is
what turns the pattern from a machine someone remembers to reboot into an
operable, self-healing fleet, and it is close to universal in production use
of this pattern on public cloud IaaS.

**PaaS-managed VM per role instance.** The platform, rather than the team,
decides when and how many VM Instances to create for a declared role or
worker type, and the team supplies only a configuration count. Azure Cloud
Services (classic) is the clearest documented example, where a developer
declares three web role instances and two worker role instances in
configuration and the platform provisions the backing VM Instances, one per
declared role instance, without the developer ever creating a VM directly.
Microsoft's own documentation puts it plainly, saying you provide a
configuration file that tells Azure how many of each you would like and the
platform then creates them for you (Microsoft, "What is Azure Cloud Services
(classic)", Azure documentation archive,
https://learn.microsoft.com/en-us/previous-versions/azure/cloud-services/cloud-services-choose-me,
fetched and verified 2026-08-02). This variant trades direct control over
the machine for a materially simpler deployment model, and it is worth
noting explicitly for posterity, since this exact product was deprecated for
all customers on 1 September 2024 per the same page, which is itself a
lesson in dimension 11 about coupling a deployment pattern to a single
vendor's product lifecycle.

**Bare-metal-adjacent variant, one service per physical or dedicated hardware
partition.** Where true VM isolation is unavailable or insufficiently
trusted, the same one-process-one-machine shape is realized on dedicated
hardware or a hardware partition instead of a hypervisor guest. This variant
is rarer in modern practice but is the direct ancestor of the pattern and
still appears where regulatory rules forbid shared hypervisor tenancy
entirely.

## 9. Known production uses

**Netflix, per-service Amazon Machine Images on Amazon EC2.** Netflix's
documented migration onto AWS packaged each internally built microservice as
its own Amazon Machine Image and ran a dedicated fleet of EC2 instances per
service, one running service instance per EC2 VM instance. This is the
production example recorded directly on the canonical pattern page, stating
that Netflix packages each service as an EC2 AMI and deploys each instance as
an EC2 instance. Chris Richardson, microservices.io, "Deploy a service
instance per VM", https://microservices.io/patterns/deployment/service-per-vm.html,
fetched and verified 2026-08-02.

**Amazon EC2 itself, the underlying primitive.** Amazon Web Services
documents the Amazon Machine Image as the artifact used to boot an EC2
instance, and documents explicitly that multiple instances can be launched
from a single AMI when multiple instances with the same configuration are
required, which is the mechanism every AMI-per-service deployment on EC2
relies on to run several instances of one service. Amazon Web Services,
"Amazon Machine Images (AMI)", Amazon EC2 User Guide,
https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AMIs.html, fetched and
verified 2026-08-02.

**Azure Cloud Services (classic), web and worker roles.** Each declared web
role or worker role instance ran as its own dedicated virtual machine, with
the platform, not the developer, provisioning the backing VM per instance
count declared in configuration, and with the platform explicitly stating
that all the VMs backing a single application run in the same cloud service
and are load balanced across the application's VMs. Microsoft, "What is
Azure Cloud Services (classic)", Azure documentation archive,
https://learn.microsoft.com/en-us/previous-versions/azure/cloud-services/cloud-services-choose-me,
fetched and verified 2026-08-02. This product is now deprecated, per the same
page, with running deployments shut down and data permanently lost starting
October 2024, in favour of the Azure Resource Manager based Cloud Services
(extended support) model, which is itself a real datapoint for dimension 11
on vendor-lifecycle risk in this pattern.

**HashiCorp Packer as the tooling generalisation.** Packer is an
infrastructure automation tool whose stated purpose is to build identical
machine images for multiple platforms, Amazon EC2 AMIs, Azure Managed
Images, Google Compute Engine images, and VMware templates, from a single
declarative template, which is the exact build-time half of this pattern
generalised across cloud providers rather than tied to one vendor's tooling.
HashiCorp, Packer documentation, "What is Packer?",
https://developer.hashicorp.com/packer/docs, fetched and verified 2026-08-02.

## 10. Consequences

Positive.

- Every running instance of a service is fully isolated at the kernel level
  from every other service on the same physical host, which is the strongest
  isolation boundary commonly available in cloud infrastructure short of
  dedicated hardware, and it requires no additional tooling beyond the VM
  platform itself.
- The organization reuses its existing VM operational tooling for patching,
  monitoring, security scanning, and cost allocation directly, with no need
  to stand up a parallel toolchain for a different runtime substrate.
- Resource limits, CPU, memory, disk, and network, are enforced by the
  hypervisor rather than negotiated at the application layer, so one
  service's misbehaviour cannot silently steal capacity from a neighbour.
- The deployment artifact, the Machine Image, is a complete, self-contained,
  immutable snapshot that can be booted identically in any environment the
  hypervisor supports, which makes environment drift easier to detect and
  rule out as a cause of a production-only bug.
- The failure domain of a single VM crash is well understood by every
  operations team that has run VMs before microservices existed, which
  lowers the training cost of adopting a microservice architecture for teams
  coming from a VM-centric operational culture.

Negative.

- Image build time is measured in minutes rather than seconds, which slows
  the feedback loop between a code change and a running, testable instance,
  and this cost is paid on every single release of every single service.
- Resource utilization is materially worse than container-based alternatives,
  because every VM Instance pays the fixed overhead of a full guest kernel
  and a minimum memory reservation before the application itself runs at
  all, and a fleet of many small, low-traffic services multiplies that fixed
  overhead across the whole fleet.
- Boot time, tens of seconds to a few minutes depending on image size and
  cloud provider, makes the pattern a poor fit for workloads that must scale
  in response to sudden traffic spikes faster than a new instance can come
  up.
- The team must build and maintain an image-baking pipeline, a versioning and
  promotion scheme for images across environments, and a patching cadence for
  the base operating system layer inside every image, which is real,
  continuing operational work distinct from the application code itself.
- Coupling the deployment model to a specific cloud provider's VM and image
  product, as opposed to the more portable container image format, raises
  migration cost if the organization later needs to change provider, and the
  Azure Cloud Services deprecation recorded in dimension 9 is a concrete case
  of that coupling turning into forced migration.

## 11. Failure modes and misuse

**Boot-time dependency on an external artifact store.** Symptom. A rolling
deployment stalls or a fresh instance never becomes healthy, and the incident
correlates with an outage or a rate limit on an unrelated artifact repository
or package mirror. Cause. The bootstrap-script variant from dimension 8
downloads the application or its dependencies at boot time rather than baking
them into the image, so the VM's readiness now depends transitively on a
service that has nothing to do with the application being deployed. Fix.
Move to a fully baked golden image so boot requires no network calls beyond
the hypervisor's own metadata service, or at minimum cache the artifact in a
region-local store with its own availability guarantee separate from the
production dependency it is caching.

**Configuration drift between the image and reality.** Symptom. A service
behaves differently in production than in the environment where the image
was tested, and nobody can reproduce the difference locally. Cause. An
operator SSHed into a running VM Instance to apply a manual fix or a manual
configuration change, which now exists only on that one running instance and
was never folded back into the Machine Image, so the next instance the
Instance Group launches, whether from a scale-out event or a health-check
replacement, comes up without the fix. Fix. Treat every running VM Instance
as immutable in practice, not only in policy, by removing SSH access to
production instances by default and routing every change, including
emergency fixes, through a new image build and a rolling replacement.

**Slow rollback under incident pressure.** Symptom. During an active
incident, the team wants to revert to the previous version and the rollback
itself takes as long as the original deployment did, extending the outage.
Cause. Rollback under this pattern means baking or re-referencing a previous
Machine Image and rolling every VM Instance in the Instance Group, which pays
the same minutes-scale image and boot latency as a forward deployment, unlike
a container rollback which is typically a fast image-tag swap. Fix. Keep the
previous few image versions warm and pre-validated so rollback only needs to
change the Instance Group's referenced image and trigger a rolling
replacement, never a fresh bake, and rehearse the rollback path before an
incident rather than during one.

**Fleet-wide staleness from a paused patch pipeline.** Symptom. A security
scan flags a large batch of running instances across many services for the
same operating system vulnerability, all at once, weeks after the fix
shipped upstream. Cause. Because each Service owns its own Machine Image
lineage independently, per the isolation force in dimension 3, there is no
single shared base layer automatically pulling every service forward the way
a shared container base image can, so a base-image patch pipeline that stops
running silently, whether from a broken build or an abandoned owner, leaves
every dependent service frozen on an old, vulnerable OS layer with no forcing
function to notice. Fix. Rebuild every service's Machine Image from a common,
centrally maintained base layer on a fixed schedule regardless of whether the
application code changed, and alert on any Machine Image whose base layer age
exceeds a defined threshold.

**Health check that only proves the process started, not that it works.**
Symptom. The Instance Group reports every VM Instance healthy while users
experience errors, and the on-call engineer has to manually verify instances
one at a time to find the bad one. Cause. The health-check endpoint checks
only that the process is listening on its port, which a process can do
before it has finished initializing its database connection pool or loading
required configuration. Fix. Make the health check exercise the service's
real dependencies, per the Health Check API pattern, and fail the check
during initialization, not only during a crash.

**Cost surprise from idle reserved capacity.** Symptom. A cloud bill review
finds a large fleet of VM Instances running at low CPU and memory
utilization for services with genuinely low and predictable traffic. Cause.
Because the minimum viable Instance Group size under this pattern is at
least one whole VM per service for availability, a large number of
low-traffic services each reserve a full VM's worth of capacity around the
clock, which is the resource-density cost from dimension 3 made concrete on
an invoice. Fix. Consolidate genuinely low-traffic services onto a
Service Instance per Container deployment instead, reserving VM-per-service
for the services whose isolation or compliance requirement justifies the
cost.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Service Instance per VM | Service Instance per Container | Serverless (function) deployment | Multiple Service Instances per Host |
|---|---|---|---|---|
| Isolation strength | Strong, hypervisor and kernel boundary | Moderate, shared host kernel with namespace isolation | Strong for the invocation, but the runtime is provider-managed and opaque | Weak, shared process space or shared VM resources across services |
| Build artifact time | Minutes, full OS image bake | Seconds to low minutes, layered image build | None for the team, provider builds the execution environment | None, no per-service artifact beyond the application binary |
| Boot or cold-start latency | Tens of seconds to minutes | Sub-second to a few seconds | Provider-dependent, often hundreds of milliseconds on a cold start | None, process is already running |
| Resource utilization | Poor, fixed per-VM kernel overhead | Good, many containers share one kernel and its overhead | Excellent, scales to zero when idle | Excellent, one host serves many services |
| Operational tooling reuse | High, reuses existing VM tooling | Requires container and orchestrator tooling | Requires provider-specific tooling, little reuse of VM operations knowledge | High, reuses existing VM tooling since it is one VM |
| Scaling latency under load spike | Slow, bounded by VM boot time | Fast, bounded by container start time | Very fast, provider absorbs concurrency automatically | Fast for the host, but a shared host may be the bottleneck |
| Blast radius of one service's failure | Contained to its own VM | Contained to its own container, weaker than a VM | Contained to the single invocation | Can affect every co-located service on the host |
| Cost model fit for spiky, low-traffic workloads | Poor, pays for standing capacity | Moderate, still pays for a standing host unless using serverless containers | Excellent, pay per invocation | Good, cost is shared across co-located services |
| Regulatory or multi-tenant trust fit | Strong, matches accepted VM trust boundaries | Depends on the orchestrator's isolation guarantees and the auditor's trust in them | Depends entirely on the provider's stated isolation guarantees | Weak, generally unsuitable for adversarial multi-tenancy |
| Team operational maturity required | Moderate, VM operations plus an image pipeline | Higher, container orchestration expertise | Lower for the team, but real vendor lock-in and cold-start debugging skill required | Lower, closest to traditional server administration |

Reading of the table. Service Instance per VM wins on isolation strength and
on reuse of existing VM operational maturity, and loses on build time, boot
latency, and resource density against the container alternative. It is the
right choice when the isolation and tooling-reuse cells matter more to the
organization than the speed and density cells, and the wrong choice when the
reverse is true, which in most greenfield microservice adoptions in 2026 it
is.

## 13. Related and incompatible patterns

- **Service Instance per Container.** The direct successor pattern and the
  most common alternative choice for the same problem. It keeps the
  one-process-one-deployable-unit shape this pattern establishes, but moves
  the isolation boundary down from the hypervisor to the container runtime,
  trading some isolation strength for materially faster build and boot
  times and much better resource density. Most organizations that adopt
  Service Instance per VM first, for the tooling-reuse reasons in dimension
  3, later migrate individual services to Service Instance per Container as
  their orchestration maturity grows, rather than migrating the whole fleet
  at once.
- **Health Check API.** A required companion, not an optional extra. The
  Instance Group cannot make a correct replace-or-keep decision about a VM
  Instance without a health-check endpoint the Service exposes, and every
  production use recorded in dimension 9 pairs this pattern with automated
  health checking.
- **Self-Registration or Third-Party Registration, and Service Registry.**
  A VM Instance's IP address is not known until the instance actually boots,
  unlike a fixed, hand-configured server, so this pattern depends on some
  form of dynamic service discovery to let callers find the currently
  healthy set of instances for a Service, either the instance registering
  itself on startup or a separate registrar watching the Instance Group.
- **Blue-Green Deployment and Canary Release.** Natural fits at the
  infrastructure level, because an Instance Group already runs old and new
  Machine Image versions side by side during a rolling update, per dimension
  7, and a deliberate blue-green or canary strategy is simply a more
  controlled version of that same transient dual-version state.
- **Circuit Breaker and Retry.** Compose above this pattern rather than with
  it directly, since the longer boot and replacement latency of a VM
  Instance, relative to a container, means a caller is more likely to
  observe a temporarily unavailable downstream during a rolling deployment
  or a health-check-triggered replacement, and needs resilience patterns
  tuned for that longer window.
- **Multiple Service Instances per Host, and Serverless deployment.** Both
  are named as alternatives on the same microservices.io deployment
  patterns page this entry's canonical source belongs to, and this entry's
  `incompatible_with` frontmatter lists Service Instance per Container and
  Serverless deployment specifically, because a single Service instance
  cannot simultaneously be deployed as a whole dedicated VM and as a
  container or a function invocation. A system can mix strategies across
  different services, but not for one running instance of one service.
- **Sidecar and Ambassador.** Compose awkwardly under this pattern compared
  to under Service Instance per Container. A sidecar process, for example a
  service mesh proxy, still runs as a second process inside the same VM
  Instance, which is possible but partially erodes the pure one-process
  isolation this pattern is chosen for, and teams that want a sidecar mesh
  at scale more often adopt it alongside Service Instance per Container
  instead, where the sidecar is a genuinely separate, resource-limited
  container.

## 14. Refactoring path in and out

Introducing the pattern where services currently share a smaller number of
larger machines, whether a monolith on dedicated hardware or several
services co-located on shared VMs.

1. Pick the first candidate service, ideally one with a clear ownership
   boundary and a modest, well-understood resource footprint, so the first
   attempt is not also the hardest one.
2. Build a minimal, fully baked Machine Image for that service, containing
   only the operating system, the runtime, and the application, with no
   manual post-boot steps. Verify it boots to a healthy state using the same
   health check the eventual Instance Group will use.
3. Stand up a small Instance Group, size one to start, referencing that
   image, and route a small, reversible slice of production traffic to it
   using whichever load balancer or service mesh the organization already
   operates.
4. Confirm the health check correctly detects both a fully broken instance
   and a slow-starting instance before increasing the desired instance
   count, since a wrong health check here silently produces the process
   started but not really ready failure mode from dimension 11.
5. Grow the Instance Group's desired size and enable automated
   health-check-driven replacement, then retire the old co-located or shared
   deployment path for that one service.
6. Establish the base-image patch cadence from dimension 11 before adding a
   second service, so the fix for the fleet-wide staleness failure mode is in
   place before the fleet exists to go stale.
7. Repeat per service, treating each migration as independent, since one of
   this pattern's advantages is that services do not need to migrate
   together.

Removing the pattern when it stops earning its place, most commonly when
build time or resource cost has become the dominant operational pain rather
than isolation strength.

1. Confirm the isolation requirement that originally justified the VM
   boundary, whether regulatory, contractual, or a genuine cross-tenant
   trust concern, either no longer applies to this service or can be met by
   the container runtime's isolation guarantees instead.
2. Containerize the application from the same source the Machine Image was
   built from, reusing the application-level dependency list rather than
   rediscovering it, and verify the container passes the identical health
   check the VM Instance used.
3. Stand up a small container deployment alongside the existing Instance
   Group and route a small, reversible slice of traffic to it, exactly
   mirroring step 3 of the introduction path in reverse.
4. Grow the container deployment's instance count while shrinking the VM
   Instance Group's desired size in step, watching the same health and
   latency signals from dimension 16 for both deployment paths side by side.
5. Once the container deployment fully absorbs production traffic, decommission
   the Instance Group and stop the Machine Image build pipeline for that
   service, and archive rather than delete the last several image versions
   in case an unrelated rollback need surfaces later.
6. Update the service's runbook and on-call documentation to remove
   VM-specific operational steps, since leaving stale VM troubleshooting
   instructions in a runbook for a service that no longer runs on a VM is a
   common, avoidable source of on-call confusion during an incident.

## 15. Testing and verification

Easier because of the pattern.

- A Machine Image can be booted in an isolated test environment and exercised
  exactly as it will run in production, since the image is the same artifact
  in both places, which removes an entire class of works-on-my-machine
  discrepancy that afflicts less immutable deployment models.
- Because the VM Instance boundary matches the hypervisor's own isolation
  guarantee, chaos and fault-injection testing that kills, restarts, or
  network-partitions a whole instance exercises a real, production-faithful
  failure mode rather than a simulated one.
- Resource-limit testing is straightforward, since the CPU and memory ceiling
  a test needs to validate against is the same hard hypervisor-enforced
  ceiling production will apply, with no risk of a shared-host neighbour
  skewing the result.

Harder because of the pattern.

- The feedback loop from a code change to a testable, booted instance is
  slow, the same minutes-scale image build cost from dimension 3 applies to
  every test run against a real image, which pushes most functional testing
  earlier in the pipeline, before the image bake, and reserves the full-image
  boot test for a smaller number of integration and pre-release checks.
- Testing a rolling deployment's dual-version behaviour, where old and new
  Machine Image versions serve traffic simultaneously per dimension 7,
  requires standing up two Instance Groups or two image versions
  concurrently in a test environment, which is more expensive to set up than
  the equivalent container-based blue-green test.
- Testing the boot-time bootstrap-script variant's failure modes, per
  dimension 11, requires deliberately breaking the artifact store or network
  path the bootstrap script depends on, which is easy to forget to test and
  is exactly the scenario that most often causes a real incident.

Techniques that apply.

- **Image validation pipeline.** Boot every newly baked Machine Image in an
  automated, disposable test environment immediately after the build, and
  run the same health check the production Instance Group will use, so a
  broken image is caught before it is ever referenced by a production
  Instance Group.
- **Chaos testing at the instance level.** Deliberately terminate a random
  healthy VM Instance in a non-production Instance Group and assert that the
  group replaces it and that traffic recovers within the expected window,
  which validates the health-check-driven replacement loop from dimension 8
  under realistic conditions rather than only in documentation.
- **Rollback rehearsal.** Periodically exercise the rollback path from
  dimension 11 against a previous, warm Machine Image version in a
  non-production environment, timing the rollback, so the first real
  rollback under incident pressure is not also the first time anyone has
  timed it.
- **Configuration drift detection.** Periodically diff a sample of live,
  running VM Instances against the Machine Image they were launched from, to
  catch the manual-fix drift failure mode from dimension 11 before it hides
  a real bug for weeks.

## 16. Observability signals

Because the deployable unit under this pattern is a whole machine, most of
the signals that matter are machine-level signals correlated with the
service running on that machine, not only application-level metrics.

What to record.

- Per-VM-Instance CPU, memory, disk, and network utilization, labelled by
  Service name, Machine Image version, and Instance Group, since a
  utilization anomaly on one image version and not another is usually the
  first sign of a regression shipped in that version.
- Health-check pass and fail counts per VM Instance, and the time to first
  healthy check after boot, since a slowly rising time to healthy across
  successive deployments is an early signal of an initialization
  regression, well before it is severe enough to fail a check outright.
- Instance Group scaling events, launches and terminations, each tagged
  with the reason, a scale-out threshold, a health-check failure, or a
  deliberate deployment, since conflating these three causes in a single
  undifferentiated count hides whether the fleet is unhealthy or simply
  busy.
- Machine Image age, per running VM Instance, measured from the image's
  build timestamp, to directly catch the fleet-wide staleness failure mode
  from dimension 11 before a security scan finds it first.
- Boot-to-healthy latency distribution, per Machine Image version, which
  both tracks the pattern's inherent boot-time cost from dimension 3 and
  flags a regression, for example the bootstrap-script variant suddenly
  taking longer because an upstream artifact store slowed down.

A healthy instance on a dashboard. Every VM Instance in an Instance Group
reports the same health-check pass rate, close to one hundred percent, with
no persistent stragglers. Boot-to-healthy latency is tight and consistent
across instances of the same Machine Image version. Machine Image age across
the fleet stays under whatever patch-cadence threshold the organization has
set, per dimension 11's fix. Scaling events during a deployment show a clean,
short-lived overlap of old and new image versions, per dimension 7, that
resolves to entirely the new version within the expected rolling-update
window.

A failing instance looks different in a few recognizable ways. A single VM
Instance's health check fails repeatedly while its siblings on the same
Machine Image version pass, which points at that instance rather than that
version, and is the concrete production signature of the configuration-drift
failure mode when it correlates with that instance having been manually
accessed. Boot-to-healthy latency climbing steadily across successive
deployments of the same service, with no change in image size, which points
at a growing external dependency in the boot path, the bootstrap-script
failure mode from dimension 11. Machine Image age climbing without bound for
one service while every other service's image age stays flat, which is the
fleet-wide staleness failure mode isolated to a single owner's broken or
abandoned patch pipeline. A rolling deployment whose old-version and
new-version instance counts stop converging, staying stuck at a partial
split, which usually means the new version is failing its health check and
the Instance Group is correctly refusing to finish the rollout, and is the
signal that should trigger the rollback rehearsal from dimension 15 rather
than a manual, ad hoc intervention.

## 17. Security and privacy implications

The pattern's central security property is real and load-bearing, not
incidental. The hypervisor boundary between VM Instances is the strongest
commonly available multi-tenant isolation short of dedicated physical
hardware, and this is precisely why regulated and adversarial multi-tenant
workloads reach for this pattern, per dimension 4, rather than for a
container-based alternative whose isolation rests on a shared kernel.

**Image supply chain integrity.** The Machine Image is now the artifact an
attacker most wants to compromise, since a poisoned base image or a
compromised dependency baked into the image runs with the full privileges of
every VM Instance launched from it, and, unlike a container image, is far
harder to inspect layer by layer at runtime because the whole disk is opaque
once booted. Sign and verify Machine Images before an Instance Group is
permitted to launch from them, and scan the image for known vulnerabilities
before it is promoted out of the build pipeline, not only after it is
already running in production.

**Long-lived credentials baked into an image.** A Machine Image that embeds a
static credential, an API key, a database password, or a private key,
directly into the disk rather than fetching it at boot from a secrets
manager, means that credential exists in every historical image version ever
built, including old versions retained for the rollback rehearsal in
dimension 15, and in every disk snapshot of every instance ever launched
from it. Fetch secrets at boot time from a dedicated secrets manager scoped
to the instance's identity, never bake a long-lived credential into the
image itself.

**SSH access as the primary threat surface for configuration drift.** The
configuration-drift failure mode in dimension 11 is also a security concern,
not only an operational one, because any channel that lets an operator or an
attacker make an undocumented change to a running VM Instance, most commonly
direct SSH access, both breaks the immutability the pattern depends on and
creates an unaudited path to modify production behaviour. Restrict direct
access to running instances as tightly as the organization's incident
response process allows, and treat any access that does occur as an event
that should trigger a rebuild rather than being trusted to have been
reverted correctly by hand.

**Patch latency as a direct vulnerability window.** Because the fleet-wide
staleness failure mode in dimension 11 can leave an entire service's fleet
on an unpatched operating system layer for an extended period with no
automatic forcing function, the base-image patch cadence recommended there
is a security control, not only a hygiene practice, and the alerting
threshold on Machine Image age should be treated with the same seriousness
as any other vulnerability management commitment.

On privacy, the pattern is largely neutral in itself, with one specific,
concrete caveat worth stating plainly. A VM Instance's local disk can retain
temporary files, logs, or cached data containing personal data from the
requests it served, and because instances under this pattern are eventually
terminated rather than reused indefinitely, the termination and disk
disposal step in the Instance Group's lifecycle is the point where that
retained data must actually be destroyed. Confirm the cloud provider's or
hypervisor's volume deletion behaviour on instance termination meets the
organization's data retention and deletion obligations, rather than assuming
termination alone is sufficient, since some providers retain deleted-volume
data for a recovery window before it is actually erased.

## Code examples

Three examples covering the parts of this pattern that are genuinely
codeable rather than purely infrastructure configuration. The pattern itself
is a deployment decision, not an object-oriented design, so the code here
targets the pieces every real implementation needs, a health-check endpoint
the Instance Group polls, an Instance Group state machine a team would
otherwise hand-roll around their cloud provider's raw API, and a typed model
of a rolling deployment plan. Java and Swift are omitted here because
neither language changes the shape of this particular deployment-level code
in a way worth demonstrating a fourth and fifth time, the pattern from
dimension 3 onward is about infrastructure lifecycle, not language-specific
object modelling, and the three languages below already cover a compiled
systems language, a scripting language, and a typed application language.

### Go, the health-check endpoint a VM Instance exposes

Compiled and run with `go run health.go` during authoring, verified to build
cleanly with `go vet` and `go build`.

```go
package main

import (
	"encoding/json"
	"log"
	"net/http"
	"sync/atomic"
	"time"
)

var ready int32 // 0 = not ready, 1 = ready

type healthResponse struct {
	Status string `json:"status"`
	Uptime string `json:"uptime"`
	Ready  bool   `json:"ready"`
}

func main() {
	start := time.Now()

	// Simulate slow startup work, e.g. warming a connection pool,
	// so the health check correctly reports not-ready until real work is done.
	go func() {
		time.Sleep(2 * time.Second)
		atomic.StoreInt32(&ready, 1)
	}()

	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		isReady := atomic.LoadInt32(&ready) == 1
		status := "starting"
		if isReady {
			status = "healthy"
		}
		w.Header().Set("Content-Type", "application/json")
		if !isReady {
			w.WriteHeader(http.StatusServiceUnavailable)
		}
		json.NewEncoder(w).Encode(healthResponse{
			Status: status,
			Uptime: time.Since(start).Round(time.Second).String(),
			Ready:  isReady,
		})
	})

	log.Println("VM instance listening on :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}
```

### Python, an in-memory Instance Group state machine

Runnable with `python3 instance_group.py`, standard library only, no external
dependencies.

```python
from dataclasses import dataclass, field
from enum import Enum


class State(Enum):
    LAUNCHING = "launching"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DRAINING = "draining"
    TERMINATED = "terminated"


@dataclass
class VMInstance:
    instance_id: str
    image_version: str
    state: State = State.LAUNCHING
    consecutive_failed_checks: int = 0


@dataclass
class InstanceGroup:
    service_name: str
    desired_count: int
    instances: list[VMInstance] = field(default_factory=list)
    max_failed_checks_before_replace: int = 3

    def launch(self, image_version: str) -> VMInstance:
        instance = VMInstance(
            instance_id=f"{self.service_name}-{len(self.instances) + 1}",
            image_version=image_version,
        )
        self.instances.append(instance)
        return instance

    def mark_health_check(self, instance_id: str, passed: bool) -> None:
        instance = self._find(instance_id)
        if passed:
            instance.consecutive_failed_checks = 0
            instance.state = State.HEALTHY
        else:
            instance.consecutive_failed_checks += 1
            if instance.consecutive_failed_checks >= self.max_failed_checks_before_replace:
                instance.state = State.UNHEALTHY

    def replace_unhealthy(self, image_version: str) -> list[str]:
        replaced = []
        for instance in list(self.instances):
            if instance.state == State.UNHEALTHY:
                instance.state = State.TERMINATED
                self.instances.remove(instance)
                new_instance = self.launch(image_version)
                replaced.append(f"{instance.instance_id} -> {new_instance.instance_id}")
        return replaced

    def healthy_count(self) -> int:
        return sum(1 for i in self.instances if i.state == State.HEALTHY)

    def _find(self, instance_id: str) -> VMInstance:
        for instance in self.instances:
            if instance.instance_id == instance_id:
                return instance
        raise KeyError(f"no such instance {instance_id}")


if __name__ == "__main__":
    group = InstanceGroup(service_name="order-service", desired_count=3)
    for _ in range(3):
        instance = group.launch(image_version="v5")
        group.mark_health_check(instance.instance_id, passed=True)

    # simulate one instance failing its health check repeatedly
    failing_id = group.instances[0].instance_id
    for _ in range(3):
        group.mark_health_check(failing_id, passed=False)

    print("before replace, healthy", group.healthy_count())
    print("replaced", group.replace_unhealthy(image_version="v5"))
    for instance in group.instances:
        group.mark_health_check(instance.instance_id, passed=True)
    print("after replace, healthy", group.healthy_count())
```

### TypeScript, a typed rolling-deployment planner

Type-checked with `npx tsc --strict --noEmit rolling_deploy.ts` and run with
`npx tsx rolling_deploy.ts` or compiled to JavaScript with `tsc` and then run
with `node`, no external dependencies beyond the TypeScript compiler.

```typescript
type ImageVersion = string;

interface InstanceGroupState {
  serviceName: string;
  desiredCount: number;
  oldImage: ImageVersion;
  newImage: ImageVersion;
  oldCount: number;
  newCount: number;
}

// One rolling-update step. Replace exactly one old-image instance
// with a new-image instance, never more than the desired count.
function step(state: InstanceGroupState): InstanceGroupState {
  if (state.oldCount === 0) {
    return state; // rollout already complete
  }
  return {
    ...state,
    oldCount: state.oldCount - 1,
    newCount: state.newCount + 1,
  };
}

function isRolloutComplete(state: InstanceGroupState): boolean {
  return state.oldCount === 0 && state.newCount === state.desiredCount;
}

function planRollout(
  serviceName: string,
  desiredCount: number,
  oldImage: ImageVersion,
  newImage: ImageVersion
): InstanceGroupState[] {
  let state: InstanceGroupState = {
    serviceName,
    desiredCount,
    oldImage,
    newImage,
    oldCount: desiredCount,
    newCount: 0,
  };

  const history: InstanceGroupState[] = [state];
  while (!isRolloutComplete(state)) {
    state = step(state);
    history.push(state);
  }
  return history;
}

const history = planRollout("order-service", 4, "v4", "v5");
for (const state of history) {
  console.log(
    `${state.serviceName} old(${state.oldImage})=${state.oldCount} ` +
      `new(${state.newImage})=${state.newCount}`
  );
}

const complete = isRolloutComplete(history[history.length - 1]);
console.log("rollout complete", complete);
```

## 18. References

1. Chris Richardson. microservices.io, deployment patterns, "Deploy a service
   instance per VM". https://microservices.io/patterns/deployment/service-per-vm.html
   Fetched and verified 2026-08-02. Source for the pattern's canonical name,
   context, problem, forces, solution, benefits, drawbacks, the Netflix
   production example, and the related and incompatible patterns listed in
   dimension 13.
2. Chris Richardson. *Microservices Patterns. With Examples in Java*. Manning
   Publications, 2019. ISBN 978-1-61729-454-9. Chapter 12, "Deploying
   microservices", which frames deployment onto a virtual machine per
   service instance as one of the book's general deployment strategies,
   alongside container and serverless deployment. Cited for the
   `first_described` attribution and for the historical framing in dimension
   2 and dimension 4.
3. Amazon Web Services. "Amazon Machine Images (AMI)". Amazon EC2 User Guide.
   https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AMIs.html Fetched and
   verified 2026-08-02. Source for the Amazon Machine Image definition and
   the multiple-instances-from-one-image mechanism cited in dimension 1 and
   dimension 9.
4. Microsoft. "What is Azure Cloud Services (classic)". Azure documentation
   archive. https://learn.microsoft.com/en-us/previous-versions/azure/cloud-services/cloud-services-choose-me
   Fetched and verified 2026-08-02. Source for the web role and worker role
   per-VM-instance model in dimension 8, the production use in dimension 9,
   and the deprecation lifecycle datapoint used in dimension 9 and dimension
   10.
5. HashiCorp. Packer documentation, "What is Packer?".
   https://developer.hashicorp.com/packer/docs Fetched and verified
   2026-08-02, describing Packer as building identical machine images for
   multiple platforms from a single source configuration. Cited as the
   cross-provider generalisation of the image-baking tooling in dimension 9.
6. Go project. `net/http` package documentation, standard library.
   https://pkg.go.dev/net/http Referenced for the standard library HTTP
   server API used in the Go code example, no separate live verification
   needed beyond confirming the sample builds with the installed Go 1.26
   toolchain, which it does.

Unverifiable or judgement-labelled claims, stated plainly rather than
disguised as sourced fact. The specific boot-time figures given in dimension
3 and dimension 6, tens of seconds to a few minutes, are engineering
judgement drawn from common public-cloud VM boot behaviour rather than a
single cited benchmark, and are stated as an order-of-magnitude comparison
against container start time rather than as a precise, sourced number. The
Netflix Aminator tooling's internal mechanics were not independently
re-verified beyond the production-use summary already recorded on the
microservices.io page cited in reference 1, because the original Netflix
Technology Blog post could not be fetched directly in this session, its URL
redirected through a Medium authentication gate this tool could not follow,
so no claim in this entry rests on that specific post, and the Netflix
production use is instead sourced entirely to reference 1, which
independently states the same fact.
