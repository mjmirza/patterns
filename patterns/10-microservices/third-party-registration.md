---
name: Third Party Registration
slug: third-party-registration
family: 10-microservices
category: Deployment and Discovery
aliases: [3rd Party Registration, External Registration, Registrar-Managed Registration]
first_described: "Richardson 2016, microservices.io"
maturity: canonical
related: [self-registration, service-registry, client-side-discovery, server-side-discovery, sidecar]
incompatible_with: []
verified: 2026-08-02
---

# Third Party Registration

## 1. Name, aliases, and lineage

The canonical name is Third Party Registration, also written 3rd Party Registration on its home reference. Chris Richardson catalogs it at microservices.io under the URL path `patterns/3rd-party-registration.html`, where the pattern definition reads, quoted verbatim, "A 3rd party registrar is responsible for registering and unregistering a service instance with the service registry" (Richardson, microservices.io, 3rd Party Registration pattern page, https://microservices.io/patterns/3rd-party-registration.html, verified 2026-08-02). The same catalog frames the sibling pattern, Self Registration, with its own page stating "A service instance is responsible for registering itself with the service registry" (Richardson, microservices.io, Self Registration pattern page, https://microservices.io/patterns/self-registration.html, verified 2026-08-02), and the two pages cross link each other as the two named answers to the same registration question. Richardson restates and extends both patterns in his book, Chris Richardson, Microservices Patterns, Manning Publications, 2018, in the chapter on service discovery, where they sit beside Service Registry, Client Side Discovery, and Server Side Discovery as the pattern language for how a caller finds a running instance of a service.

Vendor and community writing uses several near-synonyms for the same idea. External Registration appears in operational runbooks describing a registration step performed outside the service process. Sidecar Registration and Registrar-Managed Registration both describe the same mechanism through the lens of a specific implementation shape, a companion process that watches a service and does the registry work on its behalf. Netflix's own open source registration sidecar for the Eureka registry is literally named Prana, and its own documentation describes it as filling exactly this role for services that are not JVM based and cannot embed the standard Eureka Java client directly, which the microservices.io pattern page names explicitly as one of the pattern's real world examples alongside AWS Auto Scaling Groups, Joyent's Containerbuddy, the Registrator project, and the way Kubernetes and Marathon both handle instance tracking for the workloads they schedule (Richardson, microservices.io, 3rd Party Registration pattern page, https://microservices.io/patterns/3rd-party-registration.html, verified 2026-08-02).

It is worth naming, once, a distinction that is easy to blur. Third Party Registration is not a synonym for Client Side Discovery or Server Side Discovery, even though the three names appear together constantly in the same paragraphs of the same books and blog posts. Discovery is about who resolves a service name into a concrete address at call time. Registration is about who populates the registry that the discovery step reads from. The two are orthogonal, and a real system can combine either registration mechanism with either discovery mechanism freely, a point elaborated further in dimension 13.

## 2. Problem and context

A caller wants to invoke a service that runs as more than one instance, and those instances are not static. In a system running on a container orchestration platform, a service's set of running instances changes continuously, instances scale up and down with load, a rolling deployment replaces old instances with new ones, a failed instance is rescheduled onto a different host with a different address, and none of this is visible to the caller ahead of time.

Something has to keep an accurate, close to real time list of which instances of which services are currently healthy and reachable, and something has to notice quickly when an instance stops being reachable, whether from a graceful shutdown, an unhandled crash, a full node failure, or an orchestrator deliberately evicting it. The component that holds this list is described by the Service Registry pattern, and this entry is about a narrower, more operational question that only exists once a registry is already in the picture. Who is responsible for writing to it, and who is responsible for removing an entry once the instance behind it is gone.

Two candidate owners exist for that responsibility. The instance can own it itself, calling the registry's registration API as part of its own startup sequence and calling the deregistration API, or letting a heartbeat lapse, as part of its own shutdown sequence. That is Self Registration, and it is the default most teams reach for first, because it requires nothing beyond a client library linked into the service. The alternative is to hand that responsibility to a separate, dedicated component that watches the platform the service runs on and performs registration and deregistration on the instance's behalf, without the instance's own code ever being aware that a registry exists. That separate component, and the pattern of using it, is Third Party Registration.

The context in which this second option becomes attractive, rather than merely possible, has three recurring parts. The organization runs many services written in more than one language or framework, and does not want to build, test, and keep consistent a registration client library per language. The runtime platform already exposes a reliable signal of instance lifecycle, container start, container stop, health status, that a registrar can subscribe to without inventing its own liveness detection from scratch. And there is a real desire to keep application code entirely free of any dependency on the specific registry product chosen, so that changing the registry later is an infrastructure change rather than a code change across every service.

## 3. Forces

Application coupling versus operational surface area is the dominant force this pattern trades against. Third Party Registration removes any registry dependency from application code, at the direct cost of introducing a new, separately deployed component that must itself be run, monitored, and kept available, and that new component becomes a single point of failure for the accuracy of the entire registry if it is not itself made redundant.

Consistency across languages is favoured strongly. A single registrar, written once against a container runtime's event API, treats a Java service, a Go service, and an unmodifiable third party binary identically, whereas Self Registration needs a separately maintained, separately tested client for every language in use, and any inconsistency between those clients, in retry behaviour, in how gracefully they deregister on shutdown, in how they renew a heartbeat, becomes a source of registry drift that differs service by service.

Timeliness of registration is sacrificed, at least a little. There is an inherent lag between the instant an instance is genuinely ready to serve traffic and the instant the registrar has observed the corresponding lifecycle event and completed the registry write, because the registrar's knowledge is always downstream of the platform's own knowledge. Self Registration lets the instance itself decide the exact moment it registers, which can be tied precisely to internal readiness, a warmed cache, a completed migration, a loaded model, in a way an external observer watching only container-level events cannot express as precisely.

Deregistration reliability is a genuinely double edged force. On one hand, a registrar driven by real platform events, a container actually stopping, an orchestrator actually evicting a task, can react faster and more certainly than a registry waiting out a heartbeat TTL. On the other hand, an event-driven registrar is only as reliable as the event delivery itself, and a hard kill, a network partition between the host and the registrar, or the registrar's own downtime at the wrong instant, can silently produce a stale entry unless a TTL backstop exists underneath the event path, a failure mode covered at length in dimension 11.

Operational ownership and team topology favour Third Party Registration when an organization already separates a platform team, who would own the registrar, from many product teams who would otherwise each need to correctly implement registration inside their own service. The registrar becomes shared infrastructure with one owner, rather than a piece of logic duplicated with varying correctness across every service team's codebase.

Security surface is mildly sacrificed. The registrar needs privileged, often root equivalent, access to the runtime platform's event stream or control API, which is an additional credential and an additional principal that must be scoped correctly, a concern that does not exist under Self Registration, where each instance only ever needs credentials to write about itself.

## 4. Applicability

Third Party Registration earns its added complexity when several of the following conditions hold at once. A single condition on its own rarely justifies the extra component.

- The organization runs services in more than one language or framework, and does not want to build and keep consistent a registration client per language, matching exactly the coupling force in dimension 3.
- The runtime platform already emits reliable, structured lifecycle events, container start, container stop, health status change, that a registrar can subscribe to directly, without needing to invent its own liveness protocol from nothing.
- Some services in the mix are not modifiable at all, commercial software, legacy binaries, vendor appliances, and cannot have a registration client embedded, but can still be run inside a container or process a registrar can observe from the outside.
- The organization wants a hard architectural boundary between application concerns and infrastructure concerns, and treats registration and deregistration as squarely an infrastructure responsibility.
- The runtime platform is genuinely capable of accurate, prompt liveness detection on its own, so that the registrar's deregistration decision, when it fires, can be trusted and acted on quickly rather than being a second, less reliable signal layered on top of the platform's own.

### Non-applicability

Third Party Registration is the wrong choice, or at minimum an unnecessary one, in the following situations, and this list matters as much as the applicability list above.

- Running on Kubernetes. Kubernetes's own Service and Endpoints, or EndpointSlice, machinery already performs the equivalent job through the kubelet, the Endpoints controller, and DNS resolution via kube-dns or CoreDNS, without any custom registrar component, and building a parallel registrar on top of Kubernetes usually produces a second, competing source of truth rather than a benefit. This case is elaborated in dimension 13.
- Running on a fully managed or serverless platform, AWS Lambda behind API Gateway, Azure Functions, Google Cloud Run, where the platform itself is the load balancer and there is no discrete, long lived instance for anything to register in the first place.
- A small service count and low deployment frequency, where a static configuration or simple DNS round robin approach is already sufficient, and the ongoing cost of running and monitoring a registrar would exceed the coordination problem it solves.
- Already running a service mesh, Istio, Linkerd, or Consul Connect in its mesh mode, where sidecar proxies and the mesh control plane already perform discovery and registration as a byproduct of managing mesh traffic, making a standalone registrar redundant with a mechanism the mesh already provides.
- A small number of languages in use, and a team willing to build one well tested Self Registration client library once. In that situation Richardson's own framing of Self Registration as the simpler of the two options, needing nothing beyond the client library itself, tends to win on cost, per the Self Registration pattern page cited in dimension 1.
- Any situation where the network location of an instance never changes and is known ahead of time, a fixed set of on premises hosts with static IP assignment, where dynamic registration of any kind is solving a problem that does not exist.

## 5. Structure

Four participants recur across every real implementation of this pattern, and naming their responsibilities precisely is what separates Third Party Registration from a vague description of "some service discovery thing".

The Service Instance is the unit of deployment, typically a running container or process, that carries no registration logic at all. It knows how to perform its own business function and expose a health check endpoint, and nothing more about the fact that a registry exists anywhere in the system. This absence of coupling inside the instance is the entire structural point of the pattern.

The Runtime Platform is the container engine or orchestrator, Docker Engine, Mesos paired with Marathon, or Docker Swarm being the concrete examples this pattern's canonical description most often cites, that starts, stops, and monitors service instances, and exposes an events interface or an equivalent query API that a registrar can observe. The platform is the single source of truth for whether an instance currently exists and whether it is currently healthy.

The Registrar is the third party component that gives the pattern its name. It subscribes to, or polls, the runtime platform's lifecycle signal, and for every instance it sees start or become healthy, it computes that instance's network location and any registration metadata, service name, version, tags, and calls the registry's registration API. For every instance it sees stop or fail a health check, it calls the registry's deregistration API. The registrar carries no business logic of its own, its entire job is translation, platform lifecycle signal in, registry API call out.

The Service Registry is the datastore of currently available instances and their locations, as defined by the separate Service Registry pattern. Consul, etcd, and Apache ZooKeeper are the three concrete registries this pattern's implementations and known uses most commonly involve. The registry exposes a write path for registration and deregistration, which the registrar uses, and a read or watch path, which downstream Discovery Clients use, entirely independently of how the registry got populated.

## 6. Diagram

```
+------------------------------------------------------------------+
|                     Deployment Host / Cluster                    |
|                                                                    |
|   +-----------------+   +-----------------+   +-----------------+ |
|   | Service Instance |   | Service Instance |   | Service Instance| |
|   |   (unmodified)    |   |   (unmodified)    |   |   (unmodified)   | |
|   |  no registration   |   |  no registration   |   |  no registration  | |
|   |     client code     |   |     client code     |   |     client code    | |
|   +---------+---------+   +---------+---------+   +---------+--------+ |
|             |  container lifecycle events (start / stop / health)  |
|             v                       v                       v      |
|      +---------------------------------------------------------+  |
|      |         Container / Orchestrator Runtime Events           |  |
|      |     (Docker Engine events, Marathon events, Mesos API)    |  |
|      +----------------------------+------------------------------+  |
|                                    |                                 |
|                                    v                                 |
|                       +------------------------+                    |
|                       |       Registrar         |                   |
|                       |  (third party component) |                   |
|                       |  e.g. Registrator, Prana,  |                  |
|                       |  a custom watcher process  |                  |
|                       +-----------+--------------+                   |
|                                   |                                  |
|                                   | register(instance, address, port) |
|                                   | deregister(instance)              |
|                                   v                                  |
|                       +------------------------+                    |
|                       |     Service Registry     |                  |
|                       |   (Consul / etcd / ZK)    |                  |
|                       +-----------+--------------+                  |
|                                   ^                                 |
|                                   | query registered instances       |
+-----------------------------------|---------------------------------+
                                     |
                        +------------+-------------+
                        |    Discovery Client         |
                        |  (client side or server     |
                        |   side discovery consumer)  |
                        +----------------------------+
```

## 7. Dynamics

The sequence below traces one service instance's full lifecycle under Third Party Registration, on a Marathon and Mesos style platform where the registrar subscribes to an events stream.

```
Runtime Platform     Registrar          Service Registry     Service Instance
      |                   |                     |                    |
      |  schedule new     |                     |                    |
      |  instance on host |                     |                    |
      |------------------>|                     |                    |
      |                   |                     |     (starts, binds |
      |                   |                     |      to assigned   |
      |                   |                     |      port, begins  |
      |                   |                     |      serving)      |
      |                   |                     |                    |
      | instance started  |                     |                    |
      | event (host, port,|                     |                    |
      | labels/tags)      |                     |                    |
      |------------------>|                     |                    |
      |                   | compute registration|                    |
      |                   | payload from event  |                    |
      |                   | metadata            |                    |
      |                   |                     |                    |
      |                   | register(name,      |                    |
      |                   |   host, port, tags) |                    |
      |                   |-------------------->|                    |
      |                   |                     | store entry,       |
      |                   |                     | optionally begin   |
      |                   |                     | active health poll |
      |                   |                     |------------------->|
      |                   |                     |   HTTP GET /health |
      |                   |                     |<--------------------|
      |                   |                     |     200 OK          |
      |                   |                     |                    |
      |                   |     time passes, discovery clients read  |
      |                   |     the registry and route traffic       |
      |                   |                     |                    |
      | health check      |                     |                    |
      | fails or instance |                     |                    |
      | is killed         |                     |                    |
      |------------------>|                     |                    |
      |                   | deregister(name,    |                    |
      |                   |   host, port)       |                    |
      |                   |-------------------->|                    |
      |                   |                     | remove entry,      |
      |                   |                     | future discovery   |
      |                   |                     | queries stop       |
      |                   |                     | returning it       |
```

Two secondary flows matter as much as the happy path above, because they are where nearly every real production incident in this pattern originates.

Registrar restart recovery. If the registrar itself crashes and restarts, it must reconcile its view against the runtime platform's current state, list every currently running instance, diff that list against what the registry already contains, register anything missing, deregister anything stale, rather than assuming its own prior in-memory state was still correct, because the registry can drift while the registrar is down.

Registrar unavailability during a stop event. If the registrar is unreachable, or itself mid-restart, at the exact moment an instance stops, the deregistration call for that instance is lost unless the registrar's own restart reconciliation catches it, or the registry's own TTL-based health check independently expires the now stale entry on its own schedule. Production deployments of this pattern consistently pair event driven deregistration with a registry side TTL for exactly this reason, never relying on the event path alone, a point elaborated in dimension 11.

## 8. Implementation variants

The polling registrar, where the registrar periodically asks the runtime platform for its current list of instances rather than subscribing to a push based event stream, trades a small amount of registration latency for a much simpler and more resilient implementation, because the reconciliation logic and the ongoing event handling logic collapse into the same code path, run on every poll. This is the shape used in the reference implementations in dimension 10, chosen specifically for testability without a live orchestrator.

The event subscribing registrar, where the registrar opens a long lived connection to the platform's events API and reacts to individual start, stop, and health transition events as they occur, is the shape Gliderlabs Registrator actually uses against the Docker Engine's events endpoint, and it gives lower registration latency than polling at the cost of needing the reconciliation pass in dimension 7 to correct for any event the registrar missed while it was not running.

The sidecar registrar, one registrar instance per host or even per service instance, rather than one centralized registrar for an entire cluster, is the shape both Airbnb's Nerve and Netflix's Prana use. Nerve runs on every host, health checks the local services on that host, and reports their state into ZooKeeper (Airbnb, nerve GitHub repository README, https://github.com/airbnb/nerve, verified 2026-08-02). Prana runs as a sidecar process next to a non-JVM service instance and performs the registration a JVM based Eureka client would otherwise perform for that instance directly. Both shapes distribute the registrar's own workload and blast radius across many small registrar processes instead of concentrating it in one, which directly addresses the single point of failure force named in dimension 3.

The centralized registrar, a single registrar process watching an entire cluster's orchestrator API, Marathon or Mesos being the common case, is simpler to deploy and reason about than the per host sidecar shape, but concentrates both load and failure risk into one process, and needs its own redundancy strategy, active passive failover or an active active design with idempotent registration calls, to avoid becoming the single point of failure the pattern's negative consequences describe in dimension 10.

## 9. Known production uses

Airbnb's SmartStack pairs Nerve, a registrar performing exactly this pattern's role, with Synapse, a local HAProxy based discovery client. Nerve's own GitHub README states plainly, "Nerve is a utility for tracking the status of machines and services. It runs locally on the boxes which make up a distributed system, and reports state information to a distributed key value store", and adds, "The combination of Nerve and Synapse make service discovery in the cloud easy" (Airbnb, nerve GitHub repository README, https://github.com/airbnb/nerve, verified 2026-08-02). Synapse's own README independently confirms the ZooKeeper integration, describing watchers that decode Nerve's registrations, which carry host and port, directly from ZooKeeper nodes (Airbnb, synapse GitHub repository README, https://github.com/airbnb/synapse, verified 2026-08-02).

Gliderlabs Registrator is the most widely reused generic, open source implementation, and it is named directly on Chris Richardson's own microservices.io pattern page as one of the pattern's real world examples (Richardson, microservices.io, 3rd Party Registration pattern page, https://microservices.io/patterns/3rd-party-registration.html, verified 2026-08-02). Registrator's own README states, "Registrator automatically registers and deregisters services for any Docker container by inspecting containers as they come online", and confirms pluggable backend support, "Registrator supports pluggable service registries, which currently includes Consul, etcd and SkyDNS 2" (Gliderlabs, registrator GitHub repository README, https://github.com/gliderlabs/registrator, verified 2026-08-02).

HashiCorp Consul's own catalog API documentation confirms a registration path suited to exactly this pattern, describing the low level `/catalog/register` and `/catalog/deregister` HTTP endpoints, which sit alongside the more commonly used per agent registration endpoints and exist specifically to let an external process directly write catalog entries rather than relying on a locally running Consul agent (HashiCorp, Consul HTTP API, Catalog endpoints, https://developer.hashicorp.com/consul/api-docs/catalog, verified 2026-08-02). Consul's separate services registration documentation confirms the agent facing registration path, "Send a PUT request to the /agent/service/register API endpoint to dynamically register a service and its associated health checks" (HashiCorp, Consul documentation, Register Services and Health Checks, https://developer.hashicorp.com/consul/docs/services/usage/register-services-checks, verified 2026-08-02), which is the endpoint a locally colocated registrar, running alongside the Consul agent on the same host, would typically call rather than the lower level catalog endpoints.

The microservices.io 3rd Party Registration pattern page itself names three further concrete implementations of the same pattern beyond Registrator, Netflix's Prana sidecar for non-JVM applications registering into Eureka, AWS Auto Scaling Groups managing EC2 instance membership, and Joyent's Containerbuddy acting as a Docker container's parent process to drive registration, alongside the observation that Kubernetes and Marathon both perform the equivalent function as a built in part of how they track the workloads they schedule (Richardson, microservices.io, 3rd Party Registration pattern page, https://microservices.io/patterns/3rd-party-registration.html, verified 2026-08-02).

## 10. Consequences

Positive consequences. Service code has zero coupling to the registry's client library, wire protocol, or even the fact that a registry exists at all, which is the pattern's primary benefit over Self Registration, separating a cross cutting infrastructure concern cleanly from business logic. This matters concretely for organizations running many languages, a registrar written once against a container runtime's events API behaves identically regardless of whether the service inside the container is written in Go, Java, Python, or anything else, whereas Self Registration needs a maintained client per language, and every one of those clients must independently get retry behaviour, graceful deregistration on shutdown, and heartbeat renewal correct. A single registrar is also a single place to fix a registration bug, add a new registry backend, or change metadata conventions, rather than a change that must roll out separately across every service repository.

Negative consequences. The registrar itself is new infrastructure that must be deployed, monitored, and kept highly available, and if it becomes unavailable, new instances silently fail to register and dead instances silently fail to deregister, with discovery accuracy degrading for the length of the registrar's outage plus whatever TTL backstop is configured. This trades application level coupling for a genuinely new operational single point of failure, unless the registrar itself is made redundant, per the sidecar and centralized variants in dimension 8. The registrar also needs privileged access to the runtime platform's event stream or control API, root equivalent access on a Docker host, or an authenticated client against the Mesos and Marathon control plane, which is an additional credential and an additional principal that needs correct scoping. Finally, there is an unavoidable lag between the moment an instance is genuinely ready and the moment the registrar has observed that fact and completed a registry write, a lag that does not exist, or exists differently, under Self Registration, where the instance decides for itself exactly when it registers.

## 11. Failure modes and misuse

Dead instances stay discoverable for longer than expected, and clients receive connection refused or timeout errors when routed to them, even well after the instance was actually killed. The underlying cause is almost always that the registrar's deregistration relied solely on a graceful stop event, and either the registrar was briefly unavailable at the moment that event fired, or the instance died hard enough, a SIGKILL, a node crash, a network partition, that no graceful stop event was ever emitted for anything to observe. The correct fix is to pair event driven deregistration with a registry side TTL or active health check as a mandatory backstop rather than an optional extra, so that even a completely silent instance death is caught within one or two check intervals instead of depending indefinitely on an event that may simply never arrive.

After a registrar restart, some instances that were running the entire time are missing from the registry, or instances that stopped while the registrar was down remain registered forever. This happens when a registrar is implemented as a pure event listener with no startup reconciliation, so it only ever knows about instances whose individual events it personally observed after coming back up, with no way to detect drift that accumulated while it was offline. The fix is the reconcile on startup step shown in dimension 7 and in the reference implementations, list the platform's actual current instances, diff against the registry's current entries, and correct the difference, every time the registrar starts, not only the first time.

Duplicate or inconsistent registration metadata, service name, tags, or port disagreeing, appears for what is logically a single service, because two different write paths, two registrar instances not deduplicating correctly, or a leftover Self Registration code path from an incomplete migration, are both writing to the same registry entry. This is most common during a migration between registration mechanisms, or when running one registrar per host with registration identifiers that are not kept globally unique across hosts. The fix is to derive registration identifiers from something globally unique and stable per instance, the container ID rather than a bare port number, and to fully cut over an old registration path before a new one goes live, never leaving both running indefinitely.

The registrar itself becomes a bottleneck during a large scale rolling deployment, with newly started instances taking noticeably longer to become discoverable than the deployment tool itself reports them as started. The cause is a single registrar process handling a burst of lifecycle events sequentially against a registry API that has its own rate limits or per call latency, with the burst size during a large rolling update exceeding what one registrar can process promptly. The fix is running the registrar with real redundancy, one per host being the common pattern that both Nerve and Registrator use, rather than one centralized registrar for an entire cluster, so registration work is naturally distributed and one registrar's slowness affects only its own host's instances.

## 12. Trade-off matrix

| Force | Third Party Registration | Self Registration | Platform Native Discovery (Kubernetes Services) |
|---|---|---|---|
| Application coupling to registry | None, service code never references the registry | High, a client library is linked into every service | None, discovery is a platform primitive, not application code |
| Cross language consistency | High, one registrar covers every language | Low, one client library per language, each can drift | High, uniform across every workload on the platform |
| Extra infrastructure to run | Yes, the registrar itself | No | No, already part of the platform control plane |
| Registration latency | Slightly higher, bound by event delivery to the registrar | Lowest, the instance registers at the exact moment it decides it is ready | Low, tied to kubelet and controller reconciliation intervals |
| Handles unmodifiable third party services | Yes, this is a primary reason to choose it | No, the service must embed the client | Only if the workload runs as a normal Pod the platform can observe |
| Deregistration reliability without extra work | Depends on a TTL backstop, see dimension 11 | Depends on graceful shutdown, plus a TTL backstop for hard kills | High, kubelet and readiness probes drive Endpoints updates directly |
| Best fit | Container platforms without built in discovery, Docker Swarm, Marathon, plain Docker hosts | Small language footprint, team already owns a solid client library | Any workload already running on Kubernetes |

## 13. Related and incompatible patterns

Self Registration is this pattern's direct sibling and the alternative it is almost always discussed against, and dimension 3 and dimension 12 already lay out the core trade between the two, application code coupling against operational surface area.

Service Registry is the pattern this one writes into, and the two are inseparable, discussing Third Party Registration without an existing registry to register into is meaningless. Consul, etcd, and Apache ZooKeeper are the three concrete registries this pattern's own canonical description and known uses most commonly involve.

Client Side Discovery and Server Side Discovery are the patterns that consume what Third Party Registration produces, on an orthogonal axis about how a caller resolves a service name into a concrete address once the registry is already populated, the disambiguation from dimension 1. A system can pair Third Party Registration with either discovery pattern freely, the two choices do not constrain each other.

Service Mesh, and specifically the sidecar proxy architecture used by Istio, Linkerd, and Consul Connect's mesh mode, is a frequently proposed modern replacement for a standalone registrar, because a mesh's control plane performs discovery and registration as an integral part of managing sidecar proxy configuration in the first place. This is one reason a standalone, separately operated Third Party Registration registrar is comparatively less common in systems built from scratch after roughly 2018 than it was during the 2013 to 2016 period when SmartStack and Registrator were first popularized.

Kubernetes Service Discovery is related but is not an instance of this pattern, and treating it as one is a common confusion worth naming directly. Kubernetes's kubelet and its Endpoints controller perform a functionally similar job, keeping a live record of which Pod IPs currently back a given Service selector, but they do this through the Kubernetes API server's own controller reconciliation loop and DNS based virtual IP resolution, not through a general purpose registry API a client queries directly, and not through a separately deployed registrar component in the sense this pattern describes. This is the incompatibility named in dimension 4's non-applicability list, building a custom registrar on top of Kubernetes is nearly always solving an already solved problem.

## 14. Refactoring path in and out

Introducing Third Party Registration into a system that currently has no registration mechanism at all, everything reached by static configuration or hardcoded addresses, starts by standing up a Service Registry with nothing writing to it yet, and pointing exactly one, low risk service's discovery reads at it in parallel with the existing static configuration, so the registry can be validated against known good addresses before anything depends on it. Next, deploy a registrar, the polling variant from dimension 8 is the simplest starting point, scoped to that one service, and confirm its registrations match what the static configuration already says. Only once the registry has been observed to track reality correctly for a full deployment cycle, including a rolling update and at least one instance failure, should discovery clients be switched from static configuration to reading the registry, and only then should the static configuration be removed. Widen the same sequence, one service family at a time, service registry validated, registrar deployed and observed, discovery cut over, static configuration removed, rather than attempting a system wide cutover in one step.

Migrating from Self Registration to Third Party Registration on a system that already has a working registry is a narrower, more delicate refactor, because two write paths now exist simultaneously during the migration and dimension 11's duplicate registration failure mode is the direct risk. The safe order is to deploy the registrar first, in a passive or dry run mode where it computes what it would register but does not actually write, and compare its output against what the existing Self Registration clients are actually writing, service by service, until the two agree. Only then flip the registrar to active for one service at a time, and in the same change, remove that service's own registration client code so the registrar becomes the sole writer, never leaving both paths active for a given service past that point. The rollback path is the mirror image, disable the registrar for the affected service and restore the Self Registration client, which is why the client library should not be deleted from the codebase until the migration is confirmed stable in production for a meaningful period, weeks rather than hours.

Removing Third Party Registration, most often because the system is moving onto Kubernetes or a service mesh whose own built in discovery makes the standalone registrar redundant per dimension 4's non-applicability list, follows the reverse sequence. Confirm the new platform native discovery mechanism is already populated correctly and already agrees with the existing registry for every currently running instance, cut discovery clients over to the new mechanism one service at a time while the old registry keeps being written to as a safety net, and only decommission the registrar and the registry itself once every discovery client has been confirmed to be reading from the new mechanism and no client has fallen back to the old registry in a full observation window.

## 15. Testing and verification

The registrar's core translation logic, platform lifecycle event in, registry API call out, is straightforward to unit test in isolation by substituting fake implementations of the event source and the registry, exactly the shape used in every reference implementation in dimension 10, since neither dependency needs to be a real container runtime or a real registry process for this logic to be exercised. The two properties worth asserting explicitly in that unit test layer are that a start or health-ok event always produces exactly one registration call with the correct instance metadata, and that a stop or health-fail event always produces exactly one deregistration call for the correct instance identifier, with no call at all for an event concerning an instance the registrar has not previously seen.

The reconciliation logic from dimension 7 deserves its own dedicated test, separate from the event handling test, because it is the part of the registrar most often left untested and most responsible for the failure mode described first in dimension 11. A good reconciliation test seeds the fake registry with a stale entry the fake event source no longer reports as running, seeds the fake event source with a running instance the fake registry does not yet contain, and asserts that a single reconcile call corrects both, registering the missing one and deregistering the stale one, in one pass.

Integration testing against a real registry, a local Consul agent in dev mode or a local etcd instance, is worth doing at least once per registrar implementation, because it is the layer that actually exercises the registry's real API contract, authentication requirements, and error responses, none of which a fake registry implementation can be trusted to model faithfully. A useful integration test starts a real registry, runs the registrar against a fake event source, and asserts on the registry's own query API that the expected entries appear and disappear, rather than asserting on the registrar's internal state.

End to end verification, running the actual runtime platform, Docker Engine with real containers being the simplest case, alongside the real registrar and a real registry, and observing that a container's lifecycle correctly drives registration and deregistration, is the only layer that actually validates the platform integration itself, and it is best automated as a smoke test run after every registrar deployment rather than run continuously, given the cost of standing up real containers and a real registry for every test run.

## 16. Observability signals

The registrar should emit a structured log line, or a metric increment, for every registration and every deregistration it performs, tagged with the service name and instance identifier, because this log is the primary forensic tool an operator has when a discovery incident is being diagnosed, was this instance ever registered, and if so, when was it deregistered, and why.

A healthy registrar's dashboard shows registration and deregistration counts that track the platform's own instance start and stop counts closely, with a small, roughly constant latency between a platform event and the corresponding registry write. A failing registrar shows a growing gap between the platform's reported instance count and the registry's reported entry count, which is the single clearest early signal that the registrar has stopped keeping the registry accurate, whether from an outage, a bug, or a connectivity problem to the registry itself.

The reconciliation pass from dimension 7 should emit its own metric, the count of corrections it made on each run, registrations added and deregistrations removed. A reconciliation pass that regularly needs to correct a nonzero number of entries is a strong signal that the event driven path is losing events somewhere, and is worth investigating even when the corrections themselves are small in number, because it means the registry was inaccurate for some window before the reconciliation ran.

The registry's own passive health check expirations, entries removed purely because a TTL lapsed rather than because the registrar explicitly deregistered them, are worth tracking as a distinct metric from explicit deregistrations, because a rising rate of TTL expirations relative to explicit deregistrations is exactly the signature of the deregistration reliability failure mode described first in dimension 11, and it usually means the registrar's event path is not catching instance deaths promptly enough.

## 17. Security and privacy implications

The registrar's access to the runtime platform's control API or event stream is a genuinely privileged credential, root equivalent access to the Docker socket, or an authenticated principal against the Mesos and Marathon API, and it should be scoped as narrowly as the platform allows, read only where a read only scope exists, rather than granted the same broad access an operator would use for manual administration.

The registrar's write access to the service registry is similarly privileged, since a component that can register arbitrary service instances can, if compromised, register a malicious address under a legitimate service name and redirect traffic that discovery clients believe is going to a trusted instance, which is a direct integrity concern for the registry as a whole. Registries that support access control, Consul's ACL system being the concrete example, should scope the registrar's token to only the registration and deregistration operations it actually needs, rather than an administrative token.

Registration metadata itself, the tags and labels a registrar attaches to an instance, occasionally ends up carrying more information than intended, an internal hostname pattern, a build identifier, an environment variable value accidentally surfaced through container labels the registrar reads verbatim. Because the registry's read API is often broadly accessible to every service that needs to perform discovery, registration metadata should be treated as internally visible to the whole system by default, and anything genuinely sensitive should never be placed in a container label or environment variable the registrar might pick up and republish into the registry.

There is no meaningful privacy implication specific to end user data in this pattern, since the pattern operates entirely on infrastructure level metadata, service names, hosts, ports, health status, and does not itself touch application payloads or personal data in any way.

## 18. References

Richardson, Chris. microservices.io, 3rd Party Registration pattern page. https://microservices.io/patterns/3rd-party-registration.html. Verified 2026-08-02.

Richardson, Chris. microservices.io, Self Registration pattern page. https://microservices.io/patterns/self-registration.html. Verified 2026-08-02.

Richardson, Chris. Microservices Patterns. Manning Publications, 2018. Chapter on service discovery, covering Service Registry, Self Registration, 3rd Party Registration, Client Side Discovery, and Server Side Discovery.

Airbnb. nerve GitHub repository README. https://github.com/airbnb/nerve. Verified 2026-08-02.

Airbnb. synapse GitHub repository README. https://github.com/airbnb/synapse. Verified 2026-08-02.

Gliderlabs. registrator GitHub repository README. https://github.com/gliderlabs/registrator. Verified 2026-08-02.

HashiCorp. Consul HTTP API, Catalog endpoints. https://developer.hashicorp.com/consul/api-docs/catalog. Verified 2026-08-02.

HashiCorp. Consul documentation, Register Services and Health Checks. https://developer.hashicorp.com/consul/docs/services/usage/register-services-checks. Verified 2026-08-02.

## Code examples

The three implementations below sketch a minimal registrar in TypeScript, Python, and Go, the shape described as the polling variant in dimension 8, deliberately simplified for clarity rather than production readiness, and each one models the reconcile then react structure from dimension 7.

### TypeScript

```typescript
// registrar.ts
// A minimal Third Party Registration registrar, decoupled from any
// concrete container runtime via the ContainerEventSource interface.

interface ServiceInstance {
  id: string;
  serviceName: string;
  host: string;
  port: number;
  tags: string[];
}

type LifecycleEventType = "start" | "stop" | "health_ok" | "health_fail";

interface LifecycleEvent {
  type: LifecycleEventType;
  instance: ServiceInstance;
}

interface ContainerEventSource {
  onEvent(handler: (event: LifecycleEvent) => void): void;
  listRunningInstances(): Promise<ServiceInstance[]>;
}

interface ServiceRegistry {
  register(instance: ServiceInstance): Promise<void>;
  deregister(instanceId: string): Promise<void>;
  listRegistered(): Promise<ServiceInstance[]>;
}

class InMemoryRegistry implements ServiceRegistry {
  private entries = new Map<string, ServiceInstance>();

  async register(instance: ServiceInstance): Promise<void> {
    this.entries.set(instance.id, instance);
    console.log(`registered ${instance.serviceName} at ${instance.host} port ${instance.port}`);
  }

  async deregister(instanceId: string): Promise<void> {
    if (this.entries.delete(instanceId)) {
      console.log(`deregistered instance ${instanceId}`);
    }
  }

  async listRegistered(): Promise<ServiceInstance[]> {
    return Array.from(this.entries.values());
  }
}

class Registrar {
  constructor(
    private readonly eventSource: ContainerEventSource,
    private readonly registry: ServiceRegistry,
  ) {}

  async start(): Promise<void> {
    // Reconciliation pass, correct after a registrar restart, per
    // dimension 7. Never trust in memory state alone, always
    // reconcile against the runtime platform's actual current state.
    await this.reconcile();

    this.eventSource.onEvent(async (event) => {
      switch (event.type) {
        case "start":
        case "health_ok":
          await this.registry.register(event.instance);
          break;
        case "stop":
        case "health_fail":
          await this.registry.deregister(event.instance.id);
          break;
      }
    });
  }

  private async reconcile(): Promise<void> {
    const running = await this.eventSource.listRunningInstances();
    const registered = await this.registry.listRegistered();

    const runningIds = new Set(running.map((i) => i.id));
    const registeredIds = new Set(registered.map((i) => i.id));

    for (const instance of running) {
      if (!registeredIds.has(instance.id)) {
        await this.registry.register(instance);
      }
    }
    for (const instance of registered) {
      if (!runningIds.has(instance.id)) {
        await this.registry.deregister(instance.id);
      }
    }
  }
}

class FakeDockerEvents implements ContainerEventSource {
  private handlers: Array<(e: LifecycleEvent) => void> = [];
  private running: ServiceInstance[] = [
    { id: "c-existing", serviceName: "orders", host: "10.0.0.5", port: 9001, tags: ["v2"] },
  ];

  onEvent(handler: (event: LifecycleEvent) => void): void {
    this.handlers.push(handler);
  }

  async listRunningInstances(): Promise<ServiceInstance[]> {
    return this.running;
  }

  emit(event: LifecycleEvent): void {
    if (event.type === "start") this.running.push(event.instance);
    if (event.type === "stop") this.running = this.running.filter((i) => i.id !== event.instance.id);
    for (const h of this.handlers) h(event);
  }
}

async function main() {
  const events = new FakeDockerEvents();
  const registry = new InMemoryRegistry();
  const registrar = new Registrar(events, registry);

  await registrar.start();
  console.log("after reconcile", await registry.listRegistered());

  const newInstance: ServiceInstance = {
    id: "c-new-1",
    serviceName: "orders",
    host: "10.0.0.9",
    port: 9002,
    tags: ["v2"],
  };
  events.emit({ type: "start", instance: newInstance });
  console.log("after start", await registry.listRegistered());

  events.emit({ type: "stop", instance: newInstance });
  console.log("after stop", await registry.listRegistered());
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
```

Executed with `npx tsx registrar.ts` against Node 20 with tsx 4, producing the expected reconcile, register, deregister output in order.

### Python

```python
# registrar.py
# Same pattern as the TypeScript example, targeting a registry interface
# shaped like the HashiCorp Consul HTTP catalog API, register and
# deregister by service ID, since Consul is one of the registries named
# explicitly in this pattern's known uses.

from dataclasses import dataclass, field
from typing import Callable, Dict, List
from enum import Enum


class EventType(Enum):
    START = "start"
    STOP = "stop"
    HEALTH_OK = "health_ok"
    HEALTH_FAIL = "health_fail"


@dataclass(frozen=True)
class ServiceInstance:
    instance_id: str
    service_name: str
    host: str
    port: int
    tags: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class LifecycleEvent:
    event_type: EventType
    instance: ServiceInstance


class ContainerEventSource:
    def subscribe(self, handler: Callable[[LifecycleEvent], None]) -> None:
        raise NotImplementedError

    def list_running_instances(self) -> List[ServiceInstance]:
        raise NotImplementedError


class ServiceRegistry:
    def register(self, instance: ServiceInstance) -> None:
        raise NotImplementedError

    def deregister(self, instance_id: str) -> None:
        raise NotImplementedError

    def list_registered(self) -> List[ServiceInstance]:
        raise NotImplementedError


class InMemoryConsulLikeRegistry(ServiceRegistry):
    def __init__(self) -> None:
        self._entries: Dict[str, ServiceInstance] = {}

    def register(self, instance: ServiceInstance) -> None:
        self._entries[instance.instance_id] = instance
        print(f"registered {instance.service_name} at {instance.host} port {instance.port}")

    def deregister(self, instance_id: str) -> None:
        if self._entries.pop(instance_id, None) is not None:
            print(f"deregistered instance {instance_id}")

    def list_registered(self) -> List[ServiceInstance]:
        return list(self._entries.values())


class Registrar:
    def __init__(self, event_source: ContainerEventSource, registry: ServiceRegistry) -> None:
        self._event_source = event_source
        self._registry = registry

    def start(self) -> None:
        self._reconcile()
        self._event_source.subscribe(self._handle_event)

    def _reconcile(self) -> None:
        running = {i.instance_id: i for i in self._event_source.list_running_instances()}
        registered = {i.instance_id: i for i in self._registry.list_registered()}

        for instance_id, instance in running.items():
            if instance_id not in registered:
                self._registry.register(instance)
        for instance_id in registered:
            if instance_id not in running:
                self._registry.deregister(instance_id)

    def _handle_event(self, event: LifecycleEvent) -> None:
        if event.event_type in (EventType.START, EventType.HEALTH_OK):
            self._registry.register(event.instance)
        elif event.event_type in (EventType.STOP, EventType.HEALTH_FAIL):
            self._registry.deregister(event.instance.instance_id)


class FakeEventSource(ContainerEventSource):
    def __init__(self) -> None:
        self._handlers: List[Callable[[LifecycleEvent], None]] = []
        self._running: List[ServiceInstance] = [
            ServiceInstance("c-existing", "orders", "10.0.0.5", 9001, ["v2"]),
        ]

    def subscribe(self, handler: Callable[[LifecycleEvent], None]) -> None:
        self._handlers.append(handler)

    def list_running_instances(self) -> List[ServiceInstance]:
        return list(self._running)

    def emit(self, event: LifecycleEvent) -> None:
        if event.event_type == EventType.START:
            self._running.append(event.instance)
        elif event.event_type == EventType.STOP:
            self._running = [i for i in self._running if i.instance_id != event.instance.instance_id]
        for handler in self._handlers:
            handler(event)


def main() -> None:
    events = FakeEventSource()
    registry = InMemoryConsulLikeRegistry()
    registrar = Registrar(events, registry)

    registrar.start()
    print("after reconcile", registry.list_registered())

    new_instance = ServiceInstance("c-new-1", "orders", "10.0.0.9", 9002, ["v2"])
    events.emit(LifecycleEvent(EventType.START, new_instance))
    print("after start", registry.list_registered())

    events.emit(LifecycleEvent(EventType.STOP, new_instance))
    print("after stop", registry.list_registered())


if __name__ == "__main__":
    main()
```

Executed with `python3 registrar.py` on Python 3.13. Output confirms reconcile picks up the pre-existing instance, start registers the new one, and stop deregisters it.

### Go

```go
package main

import (
	"fmt"
)

type ServiceInstance struct {
	ID          string
	ServiceName string
	Host        string
	Port        int
	Tags        []string
}

type EventType int

const (
	Start EventType = iota
	Stop
	HealthOK
	HealthFail
)

type LifecycleEvent struct {
	Type     EventType
	Instance ServiceInstance
}

type EventSource interface {
	ListRunning() []ServiceInstance
	PollEvents() []LifecycleEvent
}

type Registry interface {
	Register(instance ServiceInstance)
	Deregister(instanceID string)
	ListRegistered() []ServiceInstance
}

type InMemoryRegistry struct {
	entries map[string]ServiceInstance
}

func NewInMemoryRegistry() *InMemoryRegistry {
	return &InMemoryRegistry{entries: make(map[string]ServiceInstance)}
}

func (r *InMemoryRegistry) Register(instance ServiceInstance) {
	r.entries[instance.ID] = instance
	fmt.Printf("registered %s at %s port %d\n", instance.ServiceName, instance.Host, instance.Port)
}

func (r *InMemoryRegistry) Deregister(instanceID string) {
	if _, ok := r.entries[instanceID]; ok {
		delete(r.entries, instanceID)
		fmt.Printf("deregistered instance %s\n", instanceID)
	}
}

func (r *InMemoryRegistry) ListRegistered() []ServiceInstance {
	out := make([]ServiceInstance, 0, len(r.entries))
	for _, v := range r.entries {
		out = append(out, v)
	}
	return out
}

type Registrar struct {
	source   EventSource
	registry Registry
}

func NewRegistrar(source EventSource, registry Registry) *Registrar {
	return &Registrar{source: source, registry: registry}
}

// Reconcile brings the registry in line with the runtime platform's
// actual current state, safe to call repeatedly, which is what makes
// registrar restart recovery correct.
func (r *Registrar) Reconcile() {
	running := r.source.ListRunning()
	runningByID := make(map[string]ServiceInstance)
	for _, i := range running {
		runningByID[i.ID] = i
	}

	registered := r.registry.ListRegistered()
	registeredByID := make(map[string]ServiceInstance)
	for _, i := range registered {
		registeredByID[i.ID] = i
	}

	for id, instance := range runningByID {
		if _, ok := registeredByID[id]; !ok {
			r.registry.Register(instance)
		}
	}
	for id := range registeredByID {
		if _, ok := runningByID[id]; !ok {
			r.registry.Deregister(id)
		}
	}
}

func (r *Registrar) HandleEvent(event LifecycleEvent) {
	switch event.Type {
	case Start, HealthOK:
		r.registry.Register(event.Instance)
	case Stop, HealthFail:
		r.registry.Deregister(event.Instance.ID)
	}
}

type FakeEventSource struct {
	running []ServiceInstance
	events  []LifecycleEvent
}

func NewFakeEventSource() *FakeEventSource {
	return &FakeEventSource{
		running: []ServiceInstance{
			{ID: "c-existing", ServiceName: "orders", Host: "10.0.0.5", Port: 9001, Tags: []string{"v2"}},
		},
	}
}

func (f *FakeEventSource) ListRunning() []ServiceInstance {
	return f.running
}

func (f *FakeEventSource) PollEvents() []LifecycleEvent {
	events := f.events
	f.events = nil
	return events
}

func (f *FakeEventSource) Emit(event LifecycleEvent) {
	if event.Type == Start {
		f.running = append(f.running, event.Instance)
	}
	if event.Type == Stop {
		filtered := f.running[:0]
		for _, i := range f.running {
			if i.ID != event.Instance.ID {
				filtered = append(filtered, i)
			}
		}
		f.running = filtered
	}
	f.events = append(f.events, event)
}

func main() {
	source := NewFakeEventSource()
	registry := NewInMemoryRegistry()
	registrar := NewRegistrar(source, registry)

	registrar.Reconcile()
	fmt.Println("after reconcile", registry.ListRegistered())

	newInstance := ServiceInstance{ID: "c-new-1", ServiceName: "orders", Host: "10.0.0.9", Port: 9002, Tags: []string{"v2"}}
	source.Emit(LifecycleEvent{Type: Start, Instance: newInstance})
	for _, e := range source.PollEvents() {
		registrar.HandleEvent(e)
	}
	fmt.Println("after start", registry.ListRegistered())

	source.Emit(LifecycleEvent{Type: Stop, Instance: newInstance})
	for _, e := range source.PollEvents() {
		registrar.HandleEvent(e)
	}
	fmt.Println("after stop", registry.ListRegistered())
}
```

Executed with `go run registrar.go` on Go 1.23. Output confirms the same reconcile, register, deregister sequence as the TypeScript and Python variants. All three implementations were run and their stdout inspected for the expected sequence.
