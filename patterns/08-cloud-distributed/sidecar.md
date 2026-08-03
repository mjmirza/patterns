---
name: Sidecar
slug: sidecar
family: 08-cloud-distributed
category: Cloud and Distributed Systems
aliases: [Sidekick Pattern, Sidecar Container, Sidecar Proxy]
first_described: "Burns and Oppenheimer 2016 (Design patterns for container-based distributed systems), USENIX HotCloud"
maturity: canonical
related: [ambassador, adapter, service-mesh, gatekeeper, circuit-breaker, bulkhead, gateway-offloading]
incompatible_with: []
verified: 2026-08-02
---

# Sidecar

## 1. Name, aliases, and lineage

The canonical name is Sidecar. The pattern was formalized by Brendan Burns and
David Oppenheimer of Google in "Design patterns for container-based
distributed systems," presented at the USENIX Workshop on Hot Topics in Cloud
Computing (HotCloud) 2016. The paper classifies the pattern under
"single-node patterns," meaning patterns built from two or more containers
co-scheduled onto one host as an atomic unit, an abstraction Kubernetes calls
a Pod and Nomad calls a task group. The paper's own framing of the pattern is
worth quoting directly, because it is the source every later description
paraphrases. It states, "The first and most common pattern for multi-container
deployments is the sidecar pattern. Sidecars extend and enhance the main
container." Its worked example is a web server container paired with a
"logsaver" sidecar container that reads the web server's logs from a shared
local disk volume and streams them to cluster storage (Brendan Burns and
David Oppenheimer, "Design patterns for container-based distributed
systems," USENIX HotCloud '16, 2016, section 4.1, page 2, PDF at
[static.googleusercontent.com/media/research.google.com/en//pubs/archive/45406.pdf](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/45406.pdf),
verified 2026-08-02). Burns later expanded the same catalog, with the Sidecar
pattern given its own chapter, in *Designing Distributed Systems. Patterns and
Paradigms for Scalable, Reliable Services*, O'Reilly Media, 2018. That book's
exact chapter number was not independently re-verified for this entry and is
reported here as unverified in this entry's closing notes rather than
asserted as fact.

The alias **Sidekick Pattern** is the name Microsoft's Azure Architecture
Center uses in its own catalog entry, which opens with the analogy the alias
is built on. It reads, "Like a motorcycle sidecar, these components attach to
a parent application and share its life cycle, so you create and retire them
together" (Microsoft, "Sidecar pattern," Azure Architecture Center,
[learn.microsoft.com/en-us/azure/architecture/patterns/sidecar](https://learn.microsoft.com/en-us/azure/architecture/patterns/sidecar),
verified 2026-08-02). The same page states plainly that "This pattern is
also known as the Sidekick pattern," which is the direct source for that
alias. **Sidecar Proxy** and **Sidecar Container** are not separate
patterns, they are the two most common concrete shapes the pattern takes.
Kubernetes uses **Sidecar Container** as its literal, load-bearing API term.
Since Kubernetes 1.29 an `initContainers` entry can carry
`restartPolicy: Always`, and the Kubernetes glossary and the workloads
documentation both call the resulting long-lived helper container a sidecar
container by name, a designation that reached General Availability, meaning
the feature gate `SidecarContainers` is enabled by default and the feature
state is stable, as of Kubernetes 1.33 (Kubernetes documentation, "Sidecar
Containers,"
[kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/](https://kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/),
verified 2026-08-02).

Two distinctions worth naming up front, because the literature blurs them.

- **Sidecar versus Ambassador.** Burns and Oppenheimer treat Ambassador as a
  *specialization* of Sidecar rather than a sibling pattern. An Ambassador is
  a sidecar whose entire job is proxying outbound calls to a specific remote
  dependency (their example is a `twemproxy` container sharding calls to
  memcache nodes). Every Ambassador is a Sidecar. Not every Sidecar is an
  Ambassador. A log-shipping sidecar or a certificate-rotation sidecar does no
  proxying at all. See the separate entry for Ambassador in this repository
  for the narrower pattern.
- **Sidecar as topology versus "sidecar proxy" as a service mesh data
  plane.** When people say "Istio uses sidecars," the co-scheduled container
  is specifically an Envoy proxy instance, and the sidecar topology is the
  deployment mechanism a service mesh chooses for its data plane, not a
  synonym for the mesh itself. A mesh can run its proxy as a node-level
  DaemonSet agent instead, at the cost of losing several of the guarantees
  described in dimension 3 below.

## 2. Problem and context

A service needs a capability that is not part of its core business logic.
Shipping logs off the local disk, terminating and rotating mTLS certificates,
enforcing retry and timeout policy on outbound calls, exposing metrics in a
format a monitoring system understands, or synchronizing configuration and
static content from a remote source onto local disk are all common examples.
The service could implement this capability itself, but three pressures push
against that.

First, the organization runs the same capability across many services
written in different languages, owned by different teams, on different
release cadences. A metrics-export library has to be reimplemented, or at
least re-integrated, once per language runtime, and every reimplementation
drifts slightly from the others in behavior and configuration surface.
Second, the capability has an operational lifecycle of its own. A
certificate rotator needs to be patched for a new CA format on its own
schedule, independent of the application it serves, and coupling that patch
to an application redeploy means either the platform team blocks on the
application team's release calendar or the application team carries platform
code they did not write and cannot debug. Third, the capability competes for
the same process's resources and failure domain as the business logic. A log
shipper with a memory leak, embedded as a library, takes the whole
application process down with it. A metrics exporter that blocks on a slow
network call stalls request handling in the same thread pool it shares with
everything else.

The context in which Sidecar becomes the right answer, rather than a library
or a remote service, is specifically the case where the capability needs
proximity. It must read the application's local disk, intercept the
application's local network traffic, or otherwise act as if it were part of
the same host, but it does not need to run inside the same process, share
the same memory space, or be written in the same language. Container
orchestration made this context common at scale, because a Kubernetes Pod
(or a Nomad task group) gives two or more containers a genuinely shared
network namespace and, optionally, shared volumes, while still keeping each
container as its own process, its own filesystem, its own resource cgroup,
and its own restart and image-update unit.

## 3. Forces

Sidecar sits at the intersection of several competing pressures, and which
way it resolves each one is a judgement call this entry states plainly
rather than dresses up as settled fact.

- **Coupling versus latency.** A library call is a function call, adding almost
  no latency, but the library's code, dependencies, and crash surface
  become part of the calling process. A remote microservice call removes that
  coupling entirely, but pays a network round trip, typically single-digit to
  low double-digit milliseconds even on a fast internal network, plus the
  operational cost of service discovery and its own availability story. A
  sidecar sits in between. It is out-of-process, so it is decoupled in
  language, dependency graph, and crash domain, but because it shares the
  pod's network namespace the call to it is a loopback call over `localhost`,
  which on Linux is a fraction of a millisecond, not a real network hop.
  Judgement. For the specific shape of a cross-cutting, per-instance,
  latency-sensitive concern, this is usually the best latency-versus-coupling
  trade available, which is exactly why service meshes chose it over both a
  library and a shared remote proxy tier.
- **Operational independence versus deployment coupling.** The sidecar can be
  patched, rolled back, and versioned on its own schedule, which is the whole
  operational point. But it still shares the Pod's lifecycle. It is created
  and, in most implementations before native ordering support, torn down
  alongside the main container, and if it crash-loops the Pod as a whole is
  not Ready. The pattern trades away full independent scheduling in exchange
  for keeping the two containers co-located, and that trade is the source of
  most of the failure modes in dimension 11.
- **Resource isolation versus resource cost.** Burns and Oppenheimer are
  explicit that "the container is the unit of resource accounting and
  allocation," so a sidecar gets its own CPU and memory limits and cannot
  starve the main container the way an in-process leak can (Burns and
  Oppenheimer 2016, section 4.1, page 2, cited above). The cost is that every
  Pod now runs N+1 processes instead of N, which is real memory and CPU
  overhead multiplied by the instance count, not a one-time cost.
- **Consistency and reuse versus per-team autonomy.** A shared sidecar image
  gives every team an identical implementation of a cross-cutting concern,
  which is a consistency and audit win for a platform team. It is a
  reduction in autonomy for the application team, who no longer choose their
  own logging or proxy library and instead inherit a platform decision, its
  bugs, and its release cadence.
- **Cognitive load.** A single-process application is one thing to reason
  about. A Pod with a sidecar is two processes, two log streams, two sets of
  resource limits, and at least one new failure mode, the sidecar being
  degraded while the main container looks healthy. Judgement. This cost is
  usually paid once by a platform team building the sidecar and amortized
  across every application team that adopts it without having to think about
  the internals, which is the trade the pattern is betting on.

## 4. Applicability and non-applicability

Reach for Sidecar when the following hold.

- The capability needs local proximity, meaning it reads the application's
  local disk or intercepts the application's local network traffic, rather
  than being reachable over any ordinary network call.
- The capability must be implemented once and reused, unmodified, across
  services written in different languages, which is the specific advantage
  the Azure Architecture Center names first. Its own words are "Language
  independence. The sidecar runs independently from the primary
  application's runtime environment and programming language" (Microsoft,
  "Sidecar pattern," Azure Architecture Center, cited above, verified
  2026-08-02).
- A separate team, or a separate release cadence, owns the cross-cutting
  concern, and coupling its release to the application's release is
  unacceptable to either team.
- Per-instance behavior is required, meaning every application replica needs
  its own instance of the capability, its own proxy or its own log shipper,
  as opposed to a shared, centralized instance that could serve many
  replicas at once.
- Fine-grained, per-component resource limits matter, for example capping a
  telemetry agent's memory independently of the application it observes.

Do NOT reach for Sidecar in these cases, and the reason matters more than
the rule.

- **The call is on a genuinely hot, latency-critical path where even a
  loopback hop is unacceptable.** A hand-off across process boundaries,
  through the kernel's networking stack even on `localhost`, involves a
  context switch and, if TLS or serialization is added, real CPU work per
  call. For an in-memory cache lookup measured in nanoseconds, a sidecar hop
  measured in tens or low hundreds of microseconds is a multiple-order-of-
  magnitude regression. A library or an in-process call is correct here.
- **The application platform has no notion of co-scheduled containers at
  all**, for example a traditional PaaS that deploys one process per
  application slot, or a Function-as-a-Service platform whose execution
  model is a single short-lived function invocation with no persistent
  co-located process to attach a sidecar to. Some FaaS platforms have since
  added their own sidecar-like "layers" or "extensions" mechanisms, but
  those are a different, platform-specific pattern, not the container
  Sidecar this entry describes.
- **The capability must be scaled independently of the application it
  serves.** If a component needs three replicas while the application needs
  thirty, or vice versa, coupling their lifecycles with Sidecar is the wrong
  shape. Deploy the component as its own service instead. The Azure
  Architecture Center makes exactly this point, recommending the pattern
  when a service "shares the overall life cycle of your main application,"
  and steering away from it when "you need to scale the component
  independently" (Microsoft, "Sidecar pattern," cited above, verified
  2026-08-02).
- **The application is genuinely small and low-instance-count**, so the
  fixed per-instance overhead of an extra process, extra memory footprint,
  and extra image to patch outweighs the isolation benefit. A single-replica
  internal tool does not need its own private Envoy instance.
- **The underlying platform already provides the capability natively at a
  layer the application does not have to think about.** If the cloud load
  balancer already terminates TLS and enforces retries, adding a sidecar to
  redo that work adds complexity with no offsetting benefit.
- **The team cannot yet operate two containers reliably in one Pod.** Health
  checks, log aggregation, and CI pipelines all need to understand that Pod
  readiness now depends on two containers agreeing they are healthy. A team
  without that operational maturity will produce more incidents adopting
  Sidecar than it prevents.

## 5. Structure

- **Main container (the application).** Owns the business logic. In the
  purest form of the pattern it does not know a sidecar exists. It either
  reads and writes to a shared local resource, disk, a named pipe, or a
  Unix domain socket, that the sidecar also touches, or it sends its network
  traffic to `localhost`, unaware that a sidecar intercepts it there instead
  of the traffic going directly out to the network.
- **Sidecar container (the helper).** Runs the cross-cutting concern,
  proxying, log shipping, certificate management, configuration
  synchronization, or metrics scraping. It is deployed, versioned, and scaled
  as a unit with the main container but is a separate OS process with its
  own filesystem, its own dependency graph, and, in a container runtime, its
  own resource cgroup.
- **Pod (or task group, the co-scheduling unit).** The orchestration
  abstraction that guarantees the main container and the sidecar are
  scheduled onto the same host, share a network namespace, so `localhost`
  means the same loopback interface to both, and optionally share one or
  more volumes. Burns and Oppenheimer's paper predates Kubernetes formally
  naming this the Pod but describes exactly this co-scheduling requirement
  as "a required feature for enabling the patterns we describe in this
  section" (Burns and Oppenheimer 2016, section 4, page 2, cited above).
- **Shared channel or channels.** Either a shared volume, a disk directory
  both containers mount, a shared network namespace, so the sidecar can bind
  to `127.0.0.1` and the main container can call it there or vice versa, or
  both. This is the only communication surface between the two containers in
  the canonical form of the pattern. There is deliberately no coupling
  through a shared library, a shared memory region, or direct process
  signals.
- **Injector or deployment mechanism, optional but common at scale.** A
  mutating admission webhook, Istio's sidecar injector for example, a CLI
  flag such as `dapr run`, or a manual Pod spec edit that adds the sidecar
  container definition to every workload that opts in. This is not part of
  the runtime pattern itself but is how the pattern is applied consistently
  across hundreds or thousands of workloads without hand-editing every
  manifest.

## 6. ASCII structure diagram

```
+---------------------------------------------------------------+
|                              Pod                               |
|   (one scheduling unit, one network namespace, shared volumes) |
|                                                                  |
|  +------------------------+      +-------------------------+   |
|  |    Main container      |      |     Sidecar container    |   |
|  |   (business logic)     |      |   (cross-cutting concern) |   |
|  |                        |      |                           |   |
|  |  writes logs to     -->|----->|--> reads logs, ships them |   |
|  |  /var/log (volume)     |      |    to cluster storage     |   |
|  |                        |      |                           |   |
|  |  outbound HTTP call -->|----->|--> proxies, retries, adds  |   |
|  |  to localhost:15001    |      |    mTLS, reports metrics   |   |
|  +------------------------+      +-------------------------+   |
|             |                                |                  |
|             +---------- shared volume --------+                 |
|             +---------- localhost network -----+                |
+---------------------------------------------------------------+
                     |
                     v
          [ external network / cluster storage / mesh control plane ]
```

## 7. Dynamics

The runtime behavior varies by which shared channel the sidecar uses, but the
two dominant flows are the shared-volume flow, a log or content sidecar, and
the network-interception flow, a proxy sidecar. Both are drawn below.

```
Shared-volume sidecar (log shipping), sequence over time:

  Main container         Shared volume          Sidecar container
       |                       |                        |
       |--- write log line --->|                        |
       |                       |<--- tail file ----------|
       |                       |                        |
       |--- write log line --->|                        |
       |                       |<--- tail file ----------|
       |                       |         |--- batch and ship to
       |                       |         |    cluster storage
       |                       |         |    (async, own cadence)
       |                       |                        |
   [main container crashes]    |                        |
       |                       |    sidecar keeps running,
       |                       |    finishes shipping the
       |                       |    remaining buffered lines
```

```
Network-interception sidecar (proxy), sequence over one call:

  Application code     Sidecar (localhost)      Remote dependency
       |                       |                        |
       |--- GET /orders ------>|                        |
       |   (thinks it is       |--- inject trace id,     |
       |    calling the real   |    apply mTLS,          |
       |    dependency)        |    enforce retry/timeout,|
       |                       |    record metric  ------>|
       |                       |                        |
       |                       |<----- 200 OK -----------|
       |<---- 200 OK ----------|                        |
       |   (never learns the   |                        |
       |    remote address,    |                        |
       |    protocol, or       |                        |
       |    retry policy)      |                        |
```

The second diagram is exactly the behavior the Azure Architecture Center
names as the pattern's chief runtime benefit. It states that "The sidecar's
proximity to the primary application minimizes communication latency,"
because the hop from the application to its sidecar never leaves the host
(Microsoft, "Sidecar pattern," cited above, verified 2026-08-02).

## 8. Implementation variants

- **Native init-container sidecar (Kubernetes 1.29+, stable at 1.33).** The
  sidecar is declared in the Pod's `initContainers` list with
  `restartPolicy: Always`. The kubelet starts it before the main containers
  and keeps it running for the Pod's full lifetime rather than exiting it
  once, and, critically, gates ordered readiness on it. The Kubernetes
  documentation's own example is a log-shipping container with exactly this
  shape, an `initContainers` entry named `logshipper`, image `alpine:latest`,
  `restartPolicy: Always`, and command `['sh', '-c', 'tail -F
  /opt/logs.txt']` (Kubernetes documentation, "Sidecar Containers," cited
  above, verified 2026-08-02). This variant solves the startup-ordering
  failure mode described in dimension 11, because init containers are
  guaranteed to be running before the main container starts.
- **Manually declared regular container (pre-1.29 idiom).** Before native
  sidecar support, teams simply added a second entry to `spec.containers`
  with no ordering guarantee at all. Both containers start roughly
  simultaneously and neither is guaranteed to be ready before the other.
  This is still common in the wild on clusters that have not adopted the
  native feature, and it is the version most exposed to the startup-race
  failure mode below.
- **Injected via a mutating admission webhook.** Istio's control plane,
  Istiod, ships a sidecar injector that automatically adds an Envoy
  container to any Pod in a labeled namespace, either "automatic using the
  sidecar injector webhook or manually using istioctl CLI" (Istio
  documentation, "Istio Service Mesh Architecture,"
  [istio.io/latest/docs/ops/deployment/architecture/](https://istio.io/latest/docs/ops/deployment/architecture/),
  verified 2026-08-02). This is the mechanism that lets a platform team roll
  out a mesh sidecar across an entire cluster's workloads without editing
  every manifest by hand.
- **Launched as a CLI-managed process alongside the app (self-hosted, not
  containers).** Dapr's `daprd` sidecar can run as a plain OS process,
  started by the `dapr run` CLI command next to the application process on
  a developer machine, which is the same pattern applied outside a
  container runtime entirely. The Dapr documentation is explicit that "In
  Self-Hosted mode, the daprd binary runs as a separate process launched via
  the CLI run command," while on Kubernetes the identical binary is injected
  as either a regular container by the `dapr-sidecar-injector` or, "In
  Kubernetes 1.28+, this can use native sidecars, injecting daprd as an init
  container with automatic restart capabilities" (Dapr documentation, "The
  Dapr sidecar,"
  [docs.dapr.io/concepts/dapr-services/sidecar/](https://docs.dapr.io/concepts/dapr-services/sidecar/),
  verified 2026-08-02).
- **Transparent traffic interception via `iptables` rules.** Rather than the
  application code explicitly calling `localhost`, an init container
  rewrites the Pod's networking rules so all inbound and outbound TCP is
  silently routed through the sidecar proxy, and the application never
  changes a line of code. Linkerd's data plane works this way. The
  `linkerd-init` container, running as a Kubernetes init container before
  other containers start, establishes these routing rules to "route all TCP
  traffic to and from the pod through the proxy" (Linkerd documentation,
  "Architecture,"
  [linkerd.io/2.11/reference/architecture/](https://linkerd.io/2.11/reference/architecture/),
  verified 2026-08-02).
- **Explicit local-endpoint client library, no traffic interception.** Dapr's
  building-block APIs are called explicitly by application code against a
  well-known local address, `http://localhost:3500` by default, rather than
  intercepted transparently. This is a deliberate variant. The application
  knows a sidecar exists and calls it on purpose, trading pattern purity for
  an explicit and debuggable API surface.

## 9. Known production uses

- **Kubernetes native sidecar containers.** As of Kubernetes 1.33 the
  `SidecarContainers` feature is stable and enabled by default, letting any
  cluster declare an `initContainers` entry with `restartPolicy: Always` to
  get an orchestrator-native, ordered sidecar (Kubernetes documentation,
  "Sidecar Containers," cited above, verified 2026-08-02).
- **Istio, using Envoy as its data-plane sidecar.** Istio "deploys Envoy
  proxies as sidecars alongside each microservice," and its control plane,
  Istiod, "converts high level routing rules that control traffic behavior
  into Envoy-specific configurations, and propagates them to the sidecars at
  runtime" (Istio documentation, "Istio Service Mesh Architecture," cited
  above, verified 2026-08-02).
- **Envoy itself**, the proxy Istio embeds, is described in its own
  documentation as running "as a self-contained process" alongside each
  application server rather than as a library, so that one Envoy deployment
  can bridge services written in languages including Java, C++, Go, PHP, and
  Python, without any of them needing its own client library (Envoy
  documentation, "What is Envoy,"
  [envoyproxy.io/docs/envoy/latest/intro/what_is_envoy](https://www.envoyproxy.io/docs/envoy/latest/intro/what_is_envoy),
  verified 2026-08-02).
- **Linkerd**, whose data plane is "ultralight micro-proxies which are
  deployed as sidecar containers inside application pods," implemented in
  Rust as the `linkerd2-proxy` component specifically because it is "not
  designed as a general-purpose proxy" the way Envoy is, trading generality
  for a smaller and more predictable footprint (Linkerd documentation,
  "Architecture," cited above, verified 2026-08-02).
- **Dapr (Distributed Application Runtime).** The Azure Architecture Center
  names Dapr directly as its worked example for the dependency-abstraction
  use case of Sidecar, where the sidecar "handles concerns like logging,
  configuration, service discovery, state management, and health checks"
  behind a single local API, replacing per-language client libraries
  (Microsoft, "Sidecar pattern," cited above, verified 2026-08-02, citing
  [docs.dapr.io/concepts/dapr-services/sidecar/](https://docs.dapr.io/concepts/dapr-services/sidecar/)).
- **OpenTelemetry Collector**, which the same Azure Architecture Center page
  names as a telemetry-enrichment example. Components built on it "can run
  as sidecars to normalize, enrich, or route telemetry separately from the
  application," rather than every service shipping its own telemetry
  pipeline logic (Microsoft, "Sidecar pattern," cited above, verified
  2026-08-02).

## 10. Consequences

**Positive.**

- Language and runtime independence. One sidecar implementation serves
  every application language in the fleet, cited directly above.
- Independent versioning and rollback of the cross-cutting concern, without
  coordinating an application redeploy.
- Independent resource accounting. Because "the container is the unit of
  resource accounting and allocation," a sidecar's CPU and memory limits are
  set and enforced separately from the main container's (Burns and
  Oppenheimer 2016, section 4.1, page 2, cited above).
- Failure containment. The same source states the pattern lets "the overall
  system degrade gracefully," giving the concrete example that "the web
  server can continue serving even if the log saver has failed" (Burns and
  Oppenheimer 2016, section 4.1, page 2, cited above).
- Reuse across many main containers, since "the container is the unit of
  reuse, so sidecar containers can be paired with numerous different 'main'
  containers" (Burns and Oppenheimer 2016, section 4.1, page 2, cited
  above).
- Team separation. Serving and log-saving responsibilities can be "divided
  between two separate programming teams, and allows them to be tested
  independently as well as together" (Burns and Oppenheimer 2016, section
  4.1, page 2, cited above).
- Low added latency relative to a remote call, because the hop stays on the
  loopback interface, discussed in dimension 3 and dimension 7.

**Negative.**

- Combinatorial version testing. Burns and Oppenheimer note the same
  independent-deployment benefit "also comes with a downside," and go on to
  state that "the test matrix for the overall system must consider all of
  the container version combinations that might be seen in production,
  which can be large since sets of containers generally can't be upgraded
  atomically" (Burns and Oppenheimer 2016, section 4.1, page 2, cited
  above).
- Per-instance resource overhead. Every replica of the main container now
  runs an extra process, which multiplies memory and CPU baseline cost
  across the fleet in a way a shared, centralized service does not.
- Startup and shutdown ordering complexity. Unless the platform's native
  sidecar ordering feature is used, there is no guarantee the sidecar is
  ready before the main container needs it, or that it stays alive long
  enough to finish its work after the main container exits, both detailed
  in dimension 11.
- A new, easy-to-miss single point of degradation. The Pod as a whole can
  look Ready while the sidecar silently stopped doing its job, because
  Kubernetes readiness by default reflects the main container's probe, not
  the sidecar's internal health, unless that is wired in deliberately.
- An additional network hop, even though it is a fast loopback hop, on
  every intercepted call, which is nonzero and, for extremely latency
  sensitive paths, can matter.
- Operational and cognitive overhead. Log aggregation, CI, local
  development, and debugging tooling all now have to account for two
  processes per instance instead of one.

## 11. Failure modes and misuse

**Startup race, the sidecar is not ready when the app needs it.**
Symptom. The application's first outbound calls fail with connection
refused or reset, then start succeeding a few hundred milliseconds later,
producing intermittent failures concentrated in the first seconds after a
Pod starts, especially visible during rolling deploys and autoscaling
events. Cause. In a manually declared, non-native sidecar, the pre-1.29
idiom above, Kubernetes starts the main container and the sidecar
container concurrently with no ordering guarantee, so the application can
issue its first request to `localhost` before the proxy has bound its
listening socket. Fix. Adopt native sidecar containers, which Kubernetes
guarantees are started, and can be made to wait until healthy, before the
regular containers start. Where the native feature is unavailable, add an
explicit startup probe on the sidecar and gate the main container's start,
or have the application retry its first connection with backoff instead of
failing immediately.

**Shutdown race, the sidecar exits before the app finishes using it.**
Symptom. The last few seconds of logs, traces, or metrics from a Pod that is
terminating are silently lost, most visible as a gap right before a
deployment's old Pods disappear. Cause. Without ordered termination,
Kubernetes can send `SIGTERM` to the sidecar at the same time as the main
container, and the sidecar can finish exiting first even though the main
container is still flushing its final writes through the sidecar. Fix. Use
native sidecar semantics, which are specified to terminate sidecar
containers only after the main containers have exited, or add an explicit
`preStop` hook and a longer `terminationGracePeriodSeconds` on the sidecar
so it drains any in-flight work before it exits.

**Combinatorial version skew.** Symptom. A bug reproduces only on some
fraction of Pods in a fleet and is impossible to reproduce locally, and
investigation eventually finds that the affected Pods are running one
sidecar image version paired with an older or newer main-container image
version than the pair the bug was tested against. Cause. This is exactly the
downside Burns and Oppenheimer name directly, that because the two
containers "can't be upgraded atomically," in production there is a real
cross-product of main-container versions times sidecar versions in flight
simultaneously, especially during a slow rolling deploy (Burns and
Oppenheimer 2016, section 4.1, page 2, cited above). Fix. Pin and test
explicit compatible version ranges between the sidecar and the application
contract it serves, roll out sidecar upgrades with the same staged-canary
discipline as application releases rather than as a silent fleet-wide bump,
and add a contract test that runs the oldest supported main-container
version against the newest supported sidecar version, and vice versa.

**Health-check masking.** Symptom. Requests silently stop being retried, or
mTLS silently stops being enforced, or logs silently stop shipping, while
every dashboard shows the Pod as healthy and Ready. Cause. The Pod's
readiness and liveness probes are attached only to the main container's
`/healthz` endpoint, which has no visibility into the sidecar's internal
state, so a crashed, wedged, or misconfigured sidecar does not remove the
Pod from load balancer rotation or trigger a restart. Fix. Add readiness and
liveness probes on the sidecar container itself, and, where the sidecar is
load-bearing for correctness, an mTLS-terminating proxy for example, make
the application's own health check verify it can actually reach the sidecar
rather than only checking its own internal state.

**Resource starvation from a shared node budget.** Symptom. The application
container is repeatedly throttled or OOM-killed under load that used to be
handled fine, and profiling the application in isolation shows nothing
wrong. Cause. The sidecar's CPU or memory limits were set too low for
production traffic, or too high, starving its neighbor on a resource-
constrained node, and because the two containers' limits are set
independently, a mis-sized sidecar limit is invisible from inside the
application's own metrics. Fix. Load-test the Pod as a unit, not the
application container alone, size both containers' `requests` and `limits`
from that combined load test, and alert on the sidecar's own resource
utilization, not only the application's.

**Mistaking the sidecar for a security boundary.** Symptom. A security
review assumes traffic between the application and its sidecar is
inherently trusted and skips authenticating or validating it, and later an
audit finds any process able to bind inside the Pod's network namespace, or
any container sharing that namespace by misconfiguration, can talk to the
application on `localhost` unauthenticated. Cause. Sharing a network
namespace means every process in the Pod, not only the intended sidecar,
can reach every other process's `localhost` ports. Proximity is a
performance property of the pattern, not a security guarantee. Fix. Treat
the localhost boundary as trusted only to the extent the Pod's own
container list and any admission controls are trusted, and add real
authentication, a shared secret, a local Unix domain socket with file
permissions, or mTLS even over loopback, for anything the sidecar exposes
that would be damaging if reached by an unintended process.

**Sidecar for everything, turning a Pod into a distributed monolith.**
Symptom. A single Pod accumulates a logging sidecar, a metrics sidecar, a
config-sync sidecar, a proxy sidecar, and a certificate sidecar, and the
Pod's total resource footprint, startup time, and failure surface area
start to dominate operational discussion more than the application itself
does. Cause. Sidecar is reached for by default for every cross-cutting
concern without asking whether some of those concerns would be better
served by a shared, centralized service, a DaemonSet-level node agent, or
simply a library, per dimension 4. Fix. Apply the non-applicability list in
dimension 4 to each candidate concern individually rather than
standardizing on always adding a sidecar, and consolidate genuinely related
concerns, metrics plus tracing plus logging for instance, into a single
observability sidecar rather than three separate ones.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Sidecar | In-process library | Remote/centralized service | Node-level DaemonSet agent | Ambassador (a Sidecar subset) |
|---|---|---|---|---|---|
| Latency added | Low, a loopback hop | None | High, a real network hop | Low to medium, a loopback or same-host hop | Low, a loopback hop |
| Language independence | Full, any language calls the same sidecar | None, must be reimplemented per language | Full | Full | Full |
| Failure isolation from app process | Strong, separate process and cgroup | None, shares the app's process and crash domain | Strong | Strong | Strong |
| Independent versioning | Yes, own image and rollout | No, tied to the app's build and release | Yes, and centrally so | Yes, but shared across every Pod on the node | Yes |
| Resource overhead per app instance | One extra process per instance | None extra | None extra locally, cost is centralized | Amortized across every Pod on the node | One extra process per instance |
| Blast radius of a bad rollout | One Pod at a time | One app release at a time | Every caller, all at once | Every Pod on the affected node, all at once | One Pod at a time |
| Suited to per-instance state (per-connection retries, per-instance mTLS identity) | Strong | Strong | Weak, state must be partitioned per caller | Weak, shared across many callers on the node | Strong |
| Team-owned upgrade cadence, independent of app team | Yes | No | Yes | Partially, node-wide changes affect every tenant on that node | Yes |
| Operational novelty for teams new to containers | Medium, one extra container to reason about per Pod | Low, still one process | Medium, a new service to operate and keep available | Medium to high, cluster-wide agent lifecycle | Medium |

Reading of the table. Sidecar wins specifically where per-instance,
low-latency, language-agnostic, independently-upgradable behavior is needed
at once. Give up any one of those four requirements and a simpler
alternative usually wins. A library wins when latency must be as close to
zero as possible and the team controls, or does not mind coupling to, every
caller's language. A remote centralized service wins when the concern is
naturally shared state or a scarce resource, a rate limiter's shared
counter for example, rather than per-instance behavior. A node-level
DaemonSet agent wins when the concern truly is node-wide, log collection
from every Pod on a node or node-level security scanning, rather than
per-application-instance, at the cost of every tenant on that node sharing
one agent's fate. Ambassador is not a genuine alternative to Sidecar, it is
the specific case of Sidecar where the concern is entirely proxying outbound
calls to one dependency, and the row differences above between Sidecar and
Ambassador are cosmetic rather than structural.

## 13. Related and incompatible patterns

- **Ambassador.** A strict specialization of Sidecar, restricted to
  outbound-proxying concerns. Every design consideration in this entry
  applies to Ambassador. Ambassador further narrows the scope to a
  single remote dependency and typically presents the application with a
  simplified, fixed local address to call. See this repository's Ambassador
  entry, which cites the same Burns and Oppenheimer 2016 source for its own
  formal origin.
- **Adapter (Burns and Oppenheimer's container adapter, not the GoF
  Adapter).** The other single-node, co-scheduled pattern from the same
  paper. A sidecar whose job is normalizing the main container's own output
  or interface to match a system-wide standard, for example translating an
  application-specific metrics format into a monitoring system's expected
  format. Structurally identical to Sidecar. The distinction is purely
  intent, inbound-normalizing versus outbound-proxying versus general
  augmentation.
- **Service Mesh.** A service mesh is a composition built on Sidecar, not a
  different pattern. The mesh's data plane is a fleet of sidecar proxies, as
  documented for Istio and Linkerd in dimension 9, coordinated by a
  separate control plane that pushes configuration to every sidecar. A mesh
  cannot exist without the Sidecar pattern underneath it, though, as noted
  in the trade-off matrix, some meshes offer a node-agent deployment mode
  as an alternative to per-Pod sidecars, trading per-instance isolation for
  lower resource overhead.
- **Circuit Breaker and Retry policy.** These are commonly implemented
  inside a proxy sidecar rather than in application code, which is precisely
  how Istio and Linkerd apply per-call retry and circuit-breaking behavior
  without the application needing a circuit-breaker library at all. The
  sidecar is the deployment mechanism. Circuit Breaker is the behavior
  deployed inside it.
- **Bulkhead.** Composes naturally. The sidecar's own resource limits act as
  a bulkhead around the cross-cutting concern, isolating a runaway proxy or
  log shipper from starving the application it serves, which is the direct
  mechanism behind the failure-containment-boundary benefit in dimension
  10.
- **Gatekeeper.** Where Gatekeeper places a dedicated, hardened process in
  front of a backend to validate and sanitize inbound requests before they
  reach it, an inbound-facing sidecar, an Envoy or Linkerd proxy configured
  for ingress rather than egress, is frequently the concrete implementation
  vehicle for a per-instance Gatekeeper.
- **Strangler Fig.** Not incompatible, but a common misuse to guard against.
  A team migrating a monolith sometimes reaches for a sidecar as a shortcut
  to intercept and gradually reroute traffic, when what they actually need
  is Strangler Fig's facade-and-gradual-cutover discipline at the routing
  layer above any individual Pod, not per-instance interception inside each
  one.
- **No genuine incompatibility exists at the structural level.** Sidecar is
  a deployment topology, and it can, in principle, coexist with almost any
  behavioral pattern implemented inside the sidecar container itself. The
  closest thing to an incompatibility is architectural rather than
  structural. An execution environment with no notion of co-scheduled,
  long-lived, network-namespace-sharing processes, see dimension 4's FaaS
  non-applicability point, cannot host the pattern in its canonical form at
  all, though some platforms provide narrower, platform-specific
  equivalents.

## 14. Refactoring path in and out

**Introducing a sidecar into an existing single-container deployment.**

1. Identify the cross-cutting concern currently embedded in the application
   process, a logging library, a hand-rolled retry loop around outbound
   calls, or an in-process metrics exporter, and confirm it satisfies the
   applicability checklist in dimension 4, especially proximity and
   per-instance behavior.
2. Extract the concern's configuration surface first, without moving any
   code yet. Make the application's use of it fully driven by environment
   variables or a config file, so the eventual sidecar and the current
   in-process implementation can be swapped without touching call sites.
3. Build the sidecar as a standalone process that reproduces the same
   behavior, reachable over `localhost` or a shared volume, and run it
   side by side with the existing in-process implementation in a
   non-production environment, comparing output for parity.
4. Add the sidecar container to the Pod spec, preferring the native
   `initContainers` with `restartPolicy: Always` shape on Kubernetes 1.29
   or newer to sidestep the startup-race failure mode from dimension 11,
   and add explicit readiness and liveness probes on the sidecar.
5. Cut the application over to call the sidecar, or, for a shared-volume
   sidecar, simply stop performing the work in-process and let the sidecar
   take over reading the shared volume, behind a feature flag. Roll out to
   a small canary of instances, and watch the health-check-masking and
   resource-starvation failure modes specifically during the canary window.
6. Once parity is confirmed at full rollout, delete the in-process
   implementation and its dependency from the application, completing the
   extraction.

**Removing a sidecar that no longer earns its place.**

1. Confirm the removal reason against dimension 4's non-applicability list.
   The most common reasons are that the concern turned out to need
   independent scaling, move it to its own service, or the per-instance
   overhead stopped being worth it for a small, low-traffic application,
   fold the capability back into a library or drop it if the platform now
   provides it natively.
2. Reintroduce the capability at its new home, a library dependency, a
   centralized service, or platform-native support, behind the same
   configuration surface preserved in step 2 of the introduction path
   above, so call sites do not change twice.
3. Run both the sidecar and the new implementation in parallel in a
   non-production environment and compare behavior, exactly mirroring step
   3 of introduction.
4. Cut traffic over behind a feature flag, canary the rollout, and only
   then remove the sidecar container from the Pod spec and delete its
   image from the deployment pipeline.

## 15. Testing and verification

What becomes easier because of Sidecar. The cross-cutting concern can be
unit-tested and released completely independently of the application, using
its own test suite, its own CI pipeline, and its own versioned image, with
no need to build or deploy the application at all to verify a sidecar
change. Multiple application teams can also run integration tests against
the exact same sidecar image, giving stronger confidence that production
behavior will match test behavior than N separate library integrations
would.

What becomes harder. Local development now needs two processes running
together instead of one, and a naive run-the-app-binary workflow no
longer reproduces production behavior if the sidecar changes the
application's effective network path or filesystem contents. Address this
by shipping a docker-compose or equivalent local multi-container
definition alongside the Pod manifest, so `docker compose up`, or the
team's local equivalent, reproduces the same two-container topology
developers will see in production, rather than developers running the
application alone and being surprised later.

Integration testing must specifically exercise the two failure modes unique
to the pattern. A startup-order test starts the Pod and asserts the
application's first real request succeeds rather than merely asserting the
Pod eventually becomes Ready, and a version-skew test, from dimension 11,
pairs the oldest supported main-container version with the newest
supported sidecar version and vice versa. Chaos-style tests that kill only
the sidecar container, leaving the main container running, are the direct
way to verify the health-check-masking failure mode has actually been
closed. After killing the sidecar, the Pod's readiness status should
reflect the degraded state within one probe interval, not stay Ready
indefinitely.

## 16. Observability signals

Log and metric each container as its own named signal source, never
merged, so a dashboard can distinguish an application slowdown from a
sidecar slowdown. At minimum instrument the following.

- **Sidecar process health.** Its own liveness and readiness state, CPU and
  memory utilization against its `requests` and `limits`, and restart
  count, alerted separately from the main container's equivalents.
- **Local hop latency and error rate.** The time and outcome of calls from
  the application to the sidecar over `localhost`, which is the signal that
  distinguishes a slow remote dependency from a sidecar itself adding
  latency or failing calls before they even leave the host. Istio and
  Linkerd both expose this by default because the proxy sits directly in
  the request path and can time and count every hop it handles.
- **Version skew inventory.** A fleet-wide view of which main-container
  image version is paired with which sidecar image version across every
  running Pod, specifically to catch the combinatorial-skew failure mode
  from dimension 11 before it produces a hard-to-reproduce bug report.
- **Startup and shutdown ordering timestamps.** When each container in the
  Pod reported ready and when each container received its termination
  signal versus when it actually exited, to catch startup and shutdown race
  regressions after any change to probe configuration or termination grace
  periods.
- **Shared-volume backlog.** For a log or content-sync sidecar, how far
  behind the sidecar is relative to what the main container has written,
  since a growing backlog signals the sidecar is falling behind under load
  well before it fails outright.

## 17. Security and privacy implications

The pattern's core mechanism, a shared network namespace and often a shared
volume, is precisely the surface that needs deliberate security treatment
rather than assumed trust, per the health-check-masking and
mistaken-security-boundary failure modes in dimension 11. Any process able
to join the Pod's network namespace, whether the intended sidecar or an
unintended one introduced by a misconfigured admission policy, can reach
every other container's `localhost`-bound ports. Loopback traffic inside a
Pod is not automatically encrypted or authenticated by the platform unless
the sidecar itself, or the orchestrator's network policy layer, enforces
it. This is exactly why service-mesh sidecars, Istio and Linkerd both, treat
mTLS as core rather than optional functionality. The sidecar terminates and
originates TLS on the application's behalf specifically because the
application itself is not expected to, so if the sidecar is compromised or
misconfigured, the application's traffic can silently revert to
unauthenticated plaintext without the application's own code changing at
all.

A shared volume used for log shipping or configuration synchronization
carries its own data-handling implication. The sidecar, by design, has read
access to whatever the application writes there, including any sensitive
data that ends up in application logs. A sidecar image maintained by a
platform team, which may carry a different security review cadence than
the application it serves, effectively becomes a party with access to that
data, which is a real privacy and data-governance concern for regulated
data and should be reflected in the same access-control review the
application itself receives, not assumed to be covered because it is just a
sidecar. Because sidecars are commonly injected automatically by a
mutating admission webhook across an entire namespace or cluster, a
compromised or misconfigured injector is also a supply-chain risk with a
blast radius of every workload it touches, which argues for pinning and
auditing sidecar images with the same rigor as application images rather
than treating platform-injected containers as implicitly trusted.

## Code examples

Each example below implements the pattern's core mechanism. A small
out-of-process helper intercepts traffic bound for a local application,
injects a cross-cutting concern (a trace identifier, in this case), and logs
the interaction, all without the application code needing to know the
helper exists on the wire path. Every sample was compiled or run directly
during authoring. The exact commands and their output are noted per
language. Java was omitted. This machine currently has no installed Java
Runtime Environment, so `javac`-compiled output could not be executed and
is not claimed to have been run.

### Go

Compiled and run with `go run proxy.go` (Go's toolchain compiles and
executes in one step). Output reproduced verbatim below the listing.

```go
package main

import (
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"net/http/httputil"
	"net/url"
	"time"
)

// sidecar sits in front of the app process and injects a header plus a
// one-line access log for every request, without the app knowing.
func main() {
	appAddr := startApp()
	target, _ := url.Parse("http://" + appAddr)
	proxy := httputil.NewSingleHostReverseProxy(target)

	orig := proxy.Director
	proxy.Director = func(r *http.Request) {
		orig(r)
		r.Header.Set("X-Sidecar-Injected-Trace-Id", "trace-0001")
	}

	sidecarLn, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	go func() {
		http.Serve(sidecarLn, logging(proxy))
	}()

	resp, err := http.Get("http://" + sidecarLn.Addr().String() + "/hello")
	if err != nil {
		log.Fatal(err)
	}
	body, _ := io.ReadAll(resp.Body)
	fmt.Printf("client saw: %s\n", body)
}

func logging(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		fmt.Printf("sidecar log: %s %s in %s\n", r.Method, r.URL.Path, time.Since(start))
	})
}

func startApp() string {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatal(err)
	}
	mux := http.NewServeMux()
	mux.HandleFunc("/hello", func(w http.ResponseWriter, r *http.Request) {
		trace := r.Header.Get("X-Sidecar-Injected-Trace-Id")
		fmt.Fprintf(w, "app received trace=%s", trace)
	})
	go http.Serve(ln, mux)
	return ln.Addr().String()
}
```

Verified output.

```
sidecar log: GET /hello in 295.583µs
client saw: app received trace=trace-0001
```

### Python

Run with `python3 proxy.py`. Output reproduced verbatim below the listing.

```python
"""A minimal sidecar: a TCP proxy that adds a trace header and logs each
request, sitting in front of an unmodified app socket server."""
import socketserver
import threading
import time


class AppHandler(socketserver.StreamRequestHandler):
    def handle(self):
        line = self.rfile.readline().decode().strip()
        self.wfile.write(f"app received: {line}\n".encode())


class SidecarHandler(socketserver.StreamRequestHandler):
    app_port = None

    def handle(self):
        start = time.time()
        request = self.rfile.readline().decode().strip()
        injected = f"{request} trace_id=trace-0001"

        import socket

        with socket.create_connection(("127.0.0.1", self.app_port)) as app_sock:
            app_sock.sendall((injected + "\n").encode())
            response = app_sock.recv(4096)
        self.wfile.write(response)
        elapsed_ms = (time.time() - start) * 1000
        print(f"sidecar log: {request!r} in {elapsed_ms:.3f}ms")


def serve_once(server):
    server.handle_request()


def main():
    app_server = socketserver.TCPServer(("127.0.0.1", 0), AppHandler)
    app_thread = threading.Thread(target=serve_once, args=(app_server,))
    app_thread.start()

    SidecarHandler.app_port = app_server.server_address[1]
    sidecar_server = socketserver.TCPServer(("127.0.0.1", 0), SidecarHandler)
    sidecar_thread = threading.Thread(target=serve_once, args=(sidecar_server,))
    sidecar_thread.start()

    import socket

    with socket.create_connection(("127.0.0.1", sidecar_server.server_address[1])) as client:
        client.sendall(b"GET /hello\n")
        print("client saw:", client.recv(4096).decode().strip())

    app_thread.join()
    sidecar_thread.join()


if __name__ == "__main__":
    main()
```

Verified output.

```
sidecar log: 'GET /hello' in 0.297ms
client saw: app received: GET /hello trace_id=trace-0001
```

### Rust

Compiled with `rustc -O proxy.rs -o proxy_rs`, then run with `./proxy_rs`.
Uses only the standard library, no external crates, so it also demonstrates
the zero-dependency-proxy implementation variant from dimension 8. Output
reproduced verbatim below the listing.

```rust
// A minimal sidecar proxy: sits in front of an app socket, injects a
// trace id, and logs the request. Uses only std, no external crates,
// so it mirrors how a hand-rolled sidecar can be built with zero deps.
use std::io::{BufRead, BufReader, Write};
use std::net::{TcpListener, TcpStream};
use std::thread;
use std::time::Instant;

fn start_app() -> u16 {
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let port = listener.local_addr().unwrap().port();
    thread::spawn(move || {
        if let Ok((stream, _)) = listener.accept() {
            handle_app(stream);
        }
    });
    port
}

fn handle_app(mut stream: TcpStream) {
    let mut reader = BufReader::new(stream.try_clone().unwrap());
    let mut line = String::new();
    reader.read_line(&mut line).unwrap();
    let reply = format!("app received: {}\n", line.trim_end());
    stream.write_all(reply.as_bytes()).unwrap();
}

fn start_sidecar(app_port: u16) -> u16 {
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let port = listener.local_addr().unwrap().port();
    thread::spawn(move || {
        if let Ok((stream, _)) = listener.accept() {
            handle_sidecar(stream, app_port);
        }
    });
    port
}

fn handle_sidecar(mut client: TcpStream, app_port: u16) {
    let start = Instant::now();
    let mut reader = BufReader::new(client.try_clone().unwrap());
    let mut request = String::new();
    reader.read_line(&mut request).unwrap();
    let request = request.trim_end();

    let injected = format!("{} trace_id=trace-0001\n", request);
    let mut app = TcpStream::connect(("127.0.0.1", app_port)).unwrap();
    app.write_all(injected.as_bytes()).unwrap();

    let mut app_reader = BufReader::new(app);
    let mut response = String::new();
    app_reader.read_line(&mut response).unwrap();
    client.write_all(response.as_bytes()).unwrap();

    println!(
        "sidecar log: {:?} in {:.3?}",
        request,
        start.elapsed()
    );
}

fn main() {
    let app_port = start_app();
    let sidecar_port = start_sidecar(app_port);

    let mut client = TcpStream::connect(("127.0.0.1", sidecar_port)).unwrap();
    client.write_all(b"GET /hello\n").unwrap();
    let mut reader = BufReader::new(client);
    let mut response = String::new();
    reader.read_line(&mut response).unwrap();
    println!("client saw: {}", response.trim_end());

    thread::sleep(std::time::Duration::from_millis(50));
}
```

Verified output.

```
sidecar log: "GET /hello" in 192.041µs
client saw: app received: GET /hello trace_id=trace-0001
```

### TypeScript

This example shows the alternate, explicit-call variant from dimension 8,
the Dapr shape, where the application deliberately calls a well-known local
sidecar address rather than having its traffic transparently intercepted.
Compiled with `npx tsc --target ES2020 --module commonjs proxy.ts`, then
run with `node proxy.js`. The HTTP call to the sidecar is stubbed to keep
the sample dependency-free and deterministic. In production this is a real
HTTP or gRPC call to `127.0.0.1:<sidecarPort>`. Output reproduced verbatim
below the listing.

```typescript
// A sidecar client SDK, the Dapr-style shape: application code talks
// only to a well-known local sidecar endpoint and never to the remote
// dependency directly. The sidecar process is out of scope here; this
// is the calling convention the pattern gives application code.
interface SidecarClient {
  invokeService(appId: string, method: string, body: unknown): Promise<unknown>;
  getState(store: string, key: string): Promise<unknown>;
  publish(topic: string, event: unknown): Promise<void>;
}

class LocalSidecarClient implements SidecarClient {
  constructor(private readonly baseUrl: string) {}

  private async call(path: string, body?: unknown): Promise<unknown> {
    // In production this is an HTTP or gRPC call to 127.0.0.1:<sidecarPort>.
    // Stubbed here so the sample runs with zero network dependency.
    return { path, base: this.baseUrl, echoed: body ?? null };
  }

  invokeService(appId: string, method: string, body: unknown): Promise<unknown> {
    return this.call(`/v1.0/invoke/${appId}/method/${method}`, body);
  }

  getState(store: string, key: string): Promise<unknown> {
    return this.call(`/v1.0/state/${store}/${key}`);
  }

  publish(topic: string, event: unknown): Promise<void> {
    return this.call(`/v1.0/publish/${topic}`, event).then(() => undefined);
  }
}

async function main(): Promise<void> {
  const sidecar: SidecarClient = new LocalSidecarClient("http://127.0.0.1:3500");
  const result = await sidecar.invokeService("orders-service", "createOrder", {
    sku: "widget-1",
    qty: 3,
  });
  console.log("app called sidecar, got:", JSON.stringify(result));

  await sidecar.publish("order-events", { type: "OrderCreated", sku: "widget-1" });
  console.log("app never learned the message broker's address or protocol");
}

main();
```

Verified output.

```
app called sidecar, got: {"path":"/v1.0/invoke/orders-service/method/createOrder","base":"http://127.0.0.1:3500","echoed":{"sku":"widget-1","qty":3}}
app never learned the message broker's address or protocol
```

## 18. References

1. Brendan Burns and David Oppenheimer, "Design patterns for container-based
   distributed systems," USENIX Workshop on Hot Topics in Cloud Computing
   (HotCloud '16), 2016, section 4.1, page 2. PDF verified at
   [static.googleusercontent.com/media/research.google.com/en//pubs/archive/45406.pdf](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/45406.pdf),
   verified 2026-08-02.
2. Brendan Burns, *Designing Distributed Systems. Patterns and Paradigms for
   Scalable, Reliable Services*, O'Reilly Media, 2018. Cited here for the
   book's existence and topic as the expanded successor to reference 1. The
   exact chapter and page covering Sidecar were not independently
   re-verified via a live fetch for this entry and should be treated as
   unverified until confirmed against a copy of the book.
3. Microsoft, "Sidecar pattern," Azure Architecture Center,
   [learn.microsoft.com/en-us/azure/architecture/patterns/sidecar](https://learn.microsoft.com/en-us/azure/architecture/patterns/sidecar),
   verified 2026-08-02.
4. Kubernetes documentation, "Sidecar Containers,"
   [kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/](https://kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/),
   verified 2026-08-02.
5. Istio documentation, "Istio Service Mesh Architecture,"
   [istio.io/latest/docs/ops/deployment/architecture/](https://istio.io/latest/docs/ops/deployment/architecture/),
   verified 2026-08-02.
6. Envoy documentation, "What is Envoy,"
   [envoyproxy.io/docs/envoy/latest/intro/what_is_envoy](https://www.envoyproxy.io/docs/envoy/latest/intro/what_is_envoy),
   verified 2026-08-02.
7. Linkerd documentation, "Architecture,"
   [linkerd.io/2.11/reference/architecture/](https://linkerd.io/2.11/reference/architecture/),
   verified 2026-08-02.
8. Dapr documentation, "The Dapr sidecar,"
   [docs.dapr.io/concepts/dapr-services/sidecar/](https://docs.dapr.io/concepts/dapr-services/sidecar/),
   verified 2026-08-02.
