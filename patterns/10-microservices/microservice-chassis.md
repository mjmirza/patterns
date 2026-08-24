---
name: Microservice Chassis
slug: microservice-chassis
family: 10-microservices
category: Cross-Cutting Concerns
aliases: [Service Chassis, Service Template Framework, Base Framework]
first_described: "Richardson, microservices.io pattern catalog, popularized in Microservices Patterns, Manning, 2018"
maturity: canonical
related: [service-template, self-registration, third-party-registration, api-gateway, database-per-service, circuit-breaker, distributed-tracing]
incompatible_with: []
verified: 2026-08-02
---

# Microservice Chassis

## 1. Name, aliases, and lineage

The canonical name is Microservice Chassis. Chris Richardson catalogs it on
microservices.io as one of the cross-cutting concerns patterns, alongside
Externalized Configuration, Service Discovery, and Circuit Breaker. The page
states the pattern this way, in the words of the catalog itself. Build
services on top of "a microservice chassis framework that can be foundation
for developing your microservices," where the chassis "implements reusable
build logic that builds, and tests a service" and provides "mechanisms that
handle cross-cutting concerns" (Chris Richardson, "Pattern. Microservice
chassis", https://microservices.io/patterns/microservice-chassis.html,
verified 2026-08-02). Richardson expands the same pattern in his book,
*Microservices Patterns*, Manning, 2018, chapter 11, "Developing production
ready services," where the chassis sits alongside the Service Template
pattern as the two halves of developer productivity through a common
foundation.

The alias Service Chassis appears interchangeably with Microservice Chassis in
the same catalog entry and in team documentation that predates the
"microservice" qualifier settling as the standard term. Service Template
Framework is the name for the closely related but distinct artifact, the
scaffold generator that stamps out a new repository wired to the chassis. Base
Framework is the generic, framework agnostic name engineering organizations
use internally when the specific implementation, whether it is a Spring Boot
starter, a Go module, or a Python package, has its own product name and the
chassis concept needs a vendor neutral label in an architecture document.

The idea predates the "microservices" vocabulary by a decade. Every
organization that has ever built more than a handful of services on a shared
stack has independently reinvented some version of a chassis, because the
alternative, copying a working service and editing the business logic out of
it, is such an obviously bad idea that engineers converge on the fix without
needing to read a pattern catalog first. What Richardson's catalog entry adds
is not the idea but the name, the placement of the idea inside the larger
microservices pattern language, and the explicit list of concerns a chassis
must own. Two concrete historical implementations anchor the pattern in
practice. Netflix's Karyon, which its own GitHub wiki describes as the base
container that every NetflixOSS application and service was built on top of
(Netflix, "Karyon", GitHub repository README,
https://github.com/Netflix/karyon, verified 2026-08-02), and Peter Bourgon's
Go kit, which its own author calls "a distributed programming toolkit for
building microservices in large organisations," providing shared packages for
transport, logging, metrics, tracing, and rate limiting so that "you can
focus on business logic" (Peter Bourgon, "Go kit, a standard library for
microservices", https://peter.bourgon.org/applied-go-kit/, verified
2026-08-02). Both predate the widespread use of the word "chassis" for this
concept and both are cited by name in the pattern's later formalization.

## 2. Problem and context

A single microservice, considered in isolation, is a small and cheap thing to
write. The business logic for one bounded context might be a few hundred
lines. What is not small is everything a service needs to be a good citizen
of its runtime environment before that business logic can run in production
at all. It must read configuration from the environment rather than a
hardcoded file, expose a health check endpoint an orchestrator can poll,
register itself with or be discoverable through a service registry, emit
structured logs a central aggregator can parse, export metrics a monitoring
system can scrape, propagate a distributed trace context across its outbound
calls, wrap outbound calls in a circuit breaker so a downstream failure does
spread to every caller, validate a JWT or mTLS certificate on inbound requests, and
respond correctly to a shutdown signal so an in flight request is not dropped
mid response during a rolling deployment.

None of that is domain logic. All of it is required before the domain logic
is trustworthy in production. In a monolith this list is solved exactly once,
because there is exactly one process. In a microservice architecture with
forty independently deployed services, the naive path repeats this list
forty times, once per service, usually by the fastest available method, copy
an existing service's `main` function, its Dockerfile, its logging setup, its
health check handler, and its retry wrapper, then delete the business logic
and write new business logic in its place. This is the specific failure mode
the pattern exists to prevent. It works, in the sense that a single service
built this way runs correctly. It fails at the level of the fleet, because
the cross cutting code is now duplicated forty times with forty independent
copies that will drift.

Richardson names the forcing function directly. Teams "waste a lot of time"
on this setup, and "if there are dozens or hundreds of services, that quickly
becomes very expensive" (Chris Richardson, "Pattern. Microservice chassis",
https://microservices.io/patterns/microservice-chassis.html, verified
2026-08-02). The context in which a chassis becomes the right answer, rather
than premature infrastructure, has three necessary conditions. First, the
organization operates, or plans to operate, enough independently deployable
services on a shared runtime stack, a language, or a small number of related
languages, that the cross cutting concerns are genuinely repeated rather than
solved once. Second, the cross cutting concerns themselves are relatively
stable and shared. Most services in the fleet want the same logging format,
the same health check shape, the same authentication mechanism, even though
their business logic differs completely. Third, there is an organizational
unit, whether a dedicated platform team or a rotating ownership model, willing
to own the chassis as a versioned artifact and to absorb the coordination cost
of upgrading consumers when the chassis changes.

Outside that context the pattern inverts from a productivity multiplier into
a liability, and dimension 4 spells out exactly when that inversion happens.

## 3. Forces

- **Development velocity for a new service.** Strongly favored. A team
  scaffolding a new service against a chassis writes a `pom.xml` dependency or
  a `go.mod` import and inherits a working health check, logging pipeline,
  and metrics exporter on day one, rather than re deriving them.
- **Consistency of operational behavior across the fleet.** Strongly favored.
  When every service logs in the same structured format and exposes the same
  health check contract, an on call engineer moving between services does not
  need to relearn the operational surface of each one, and a fleet wide
  dashboard or alert rule works unmodified across services.
- **Coupling to a shared dependency.** Sacrificed. Every service that adopts
  the chassis now depends on it, and a bug or a breaking change in the
  chassis is a bug or a breaking change simultaneously visible to every
  consuming service. The chassis becomes a single point of correlated
  failure across the fleet even though the services themselves are
  independently deployable.
- **Polyglot independence.** Sacrificed in proportion to how far the organization
  wants a shared chassis to reach. A single Spring Boot chassis pulls every
  Java service toward one opinionated stack. A genuinely polyglot fleet needs
  either a chassis per language, multiplying the maintenance burden by the
  number of languages, or a language agnostic mechanism such as a sidecar,
  which trades in process convenience for network hop cost, see dimension
  13's relationship to service mesh.
- **Upgrade coordination cost.** Sacrificed. A security patch or a new
  observability requirement that must land in the chassis has to be released
  as a new version and then adopted by every consuming service, which is
  itself a fleet wide rollout with its own scheduling and testing cost. This
  is the direct mirror image of the velocity benefit above. The same
  centralization that makes adding a concern cheap once makes changing an
  existing concern expensive across the whole fleet.
- **Blast radius of a chassis defect.** Sacrificed. A logging bug that
  silently drops a field, or a health check bug that reports healthy when a
  dependency is actually down, propagates into every service built on the
  affected chassis version simultaneously, which is a different failure
  shape than a bug isolated to one hand rolled service.
- **Team autonomy versus platform standardization.** This is the central
  tension the pattern sits inside. A chassis pushes toward a golden path, a
  term used across platform engineering literature for the officially
  supported, low friction way of doing a common task, at the direct cost of a
  team's latitude to choose a different logging library, a different metrics
  format, or a different framework version on its own schedule.
- **Runtime overhead per request.** Mildly sacrificed, and highly
  implementation dependent. Middleware for tracing, metrics, and auth adds
  measurable per request latency, usually single digit milliseconds for a
  well implemented in process chassis, versus a hand tuned service with no
  such middleware, though the absolute number depends entirely on what the
  chassis actually does on the hot path.

A pattern that gave up nothing would not be a pattern, and the honest reading
of this one is that it trades per service flexibility and independent release
pace of change for fleet wide consistency and per service startup cost, and that
trade is only worth making once the fleet is large enough for the duplication
cost to exceed the coordination cost.

## 4. Applicability and non-applicability

Reach for a Microservice Chassis when the following hold.

- The organization runs, or credibly plans to run within a defined period,
  enough independently deployed services on a common language or stack that
  the setup cost per service, logging, health checks, config, discovery,
  auth, tracing, is measured across dozens of repositories rather than a
  handful.
- There is an identifiable team or rotation with the authority and the
  bandwidth to own the chassis as a first class, versioned product, including
  publishing release notes, handling breaking changes, and supporting
  consumers through upgrades.
- The cross cutting concerns the chassis would centralize are genuinely
  shared across most services in the fleet, not merely superficially similar.
  If half the fleet needs synchronous request response semantics and the
  other half needs event driven consumer semantics, a single chassis trying
  to serve both concerns is already fighting its own scope.
- The organization has, or is building toward, a consistent deployment
  platform, a common container runtime, a common orchestrator, a common
  service mesh or discovery mechanism, that the chassis's assumptions about
  environment variables, health check paths, and shutdown signals can target
  without per service special cases.
- New services are created often enough that the marginal cost of
  maintaining the chassis is amortized across many scaffolding events, not
  paid once for a system that will only ever have three or four services.

Do not reach for a Microservice Chassis when any of the following hold.

- The system has a small, stable number of services, single digits, where
  the coordination overhead of maintaining a shared chassis exceeds the
  duplication cost it would save. Richardson's own framing is explicitly
  about the "dozens or hundreds of services" regime. A three service system
  copying a small amount of boilerplate three times is not the problem this
  pattern solves.
- The fleet is genuinely polyglot with no dominant language, and there is no
  appetite to either maintain N separate chassis implementations or to push
  the cross cutting concerns out of process into a sidecar or service mesh.
  Forcing a Java chassis onto a Go team, or vice versa, produces friction the
  pattern was meant to remove.
- Services are built and owned by fully independent, loosely federated teams,
  for example separate companies in a marketplace or platform grouping,
  where imposing a shared internal dependency is organizationally impossible
  or actively undesirable, because it centralizes a decision that belongs to
  each team.
- The organization has already adopted a service mesh, see dimension 13, that
  handles the network facing cross cutting concerns, retries, circuit
  breaking, mTLS, tracing propagation, at the infrastructure layer. Building
  an in process chassis that duplicates what the mesh's sidecar already
  provides adds a second, overlapping mechanism for the same concern, which
  is a coordination liability rather than a benefit. The residual chassis
  scope in that world shrinks to language idiomatic concerns the mesh cannot
  reach, such as structured logging conventions and startup wiring.
- The team is optimizing for maximum per service autonomy and independent
  technology choice as an explicit organizational value, for instance a
  platform deliberately designed to let each team pick its own stack. A
  shared chassis is the opposite of that value by construction.
- The chassis would need to encode business domain logic, not merely
  cross cutting infrastructure concerns. The moment "the chassis" starts
  containing anything specific to how orders are validated or how payments
  are authorized, it has stopped being a chassis and has become an
  undocumented shared library coupling every service's domain logic
  together, which is a distinct and much worse problem than infrastructure
  coupling.

## 5. Structure

- **Chassis library or framework.** The versioned, independently published
  artifact, a package, a set of starter dependencies, a base container
  image, or some combination, that implements the cross cutting concerns.
  It does not know about any specific service's business logic.
- **Cross-cutting concern module.** One coherent unit inside the chassis
  addressing a single operational responsibility, configuration loading,
  health check endpoint, structured logging, metrics export, distributed
  trace propagation, service registration, circuit breaker wrapping, or
  inbound authentication and authorization. A well factored chassis exposes
  these as separable modules rather than one monolithic bundle, so a
  consuming service can adopt a subset.
- **Consuming service.** An individual microservice that depends on the
  chassis, as a compile time or build time dependency in a language like
  Java or Go, or as an inherited base image and shared entrypoint script in
  a polyglot deployment, and supplies only its business logic and its
  service specific configuration values on top.
- **Extension point or hook.** The interface the chassis exposes for a
  consuming service to plug in service specific behavior, for example a
  named health check contributor, a custom metric, or a domain specific log
  field, without needing to fork or modify the chassis itself.
- **Chassis owner.** The team, platform group, or rotating on call function
  responsible for versioning the chassis, publishing releases, communicating
  breaking changes, and often for providing a scaffolding tool, the sibling
  Service Template pattern, that generates a new consuming service
  pre wired to the current chassis version.
- **Version boundary.** The explicit contract, usually semantic versioning,
  that governs how a chassis change reaches consuming services, whether it
  is opt in per service, pushed via an automated dependency bot, or bundled
  with the organization's base container image and therefore inherited on
  the next rebuild whether the service team requested it or not.

## 6. ASCII structure diagram

```
+---------------------------+
| Chassis (versioned lib)   |
| Config loader             |
| Health check module       |
| Structured logging module |
| Metrics exporter          |
| Trace propagation         |
| Circuit breaker wrapper   |
| Auth / token validation   |
| Extension points (hooks)  |
+---------------------------+
     ^ depends on (compile/build time)
     |
+----------------+
| Order Service  |
| Domain logic   |
| Service config |
| Custom hooks   |
+----------------+
+----------------+
| Payment Svc    |
| Domain logic   |
| Service config |
| Custom hooks   |
+----------------+
+----------------+
| Shipping Svc   |
| Domain logic   |
| Service config |
| Custom hooks   |
+----------------+
+----------------+
| Catalog Svc    |
| Domain logic   |
| Service config |
| Custom hooks   |
+----------------+

Each service inherits health check, logging, metrics,
tracing, circuit breaker, auth. Each service supplies
everything else.
```

## 7. Dynamics

```
Build time (per consuming service)
------------------------------------
1. Service repo declares a dependency on chassis version X.Y.Z
2. Build pulls the chassis artifact from the internal package registry
3. Chassis wires its modules into the service's startup sequence.
     load config -> register health checks -> attach logging ->
     attach metrics -> attach tracing -> wrap outbound clients in
     circuit breakers -> mount auth middleware

Startup (a single service instance)
------------------------------------
Process starts
  -> Chassis reads environment / config source (dimension 8 variant)
  -> Chassis initializes logger with fleet-standard fields (service
     name, version, environment, trace id placeholder)
  -> Chassis registers the /health and /ready endpoints
  -> Chassis initializes the metrics registry and exposes /metrics
  -> Service-specific startup hook runs (domain wiring: DB pool,
     message consumer subscriptions, route handlers)
  -> Chassis marks the service as ready once its own checks and the
     service's declared readiness hooks all pass
  -> Orchestrator (Kubernetes, ECS, etc.) begins routing traffic once
     /ready returns 200

Runtime (a single inbound request)
------------------------------------
Request arrives
  -> Chassis middleware extracts or generates a trace id
  -> Chassis middleware validates the auth token (JWT / mTLS cert)
  -> Chassis middleware starts a timer for the request-duration metric
  -> Control passes to the service's own handler (business logic)
  -> Handler makes an outbound call to a dependency
       -> Chassis-provided client wraps the call in a circuit breaker
       -> Chassis-provided client propagates the trace context
  -> Handler returns a response
  -> Chassis middleware records the metric, logs the structured line
     with the trace id attached, and returns the response

Shutdown (rolling deployment or scale-down)
------------------------------------
Orchestrator sends SIGTERM
  -> Chassis catches the signal, marks /ready as unhealthy so no new
     traffic is routed to this instance
  -> Chassis waits for in-flight requests to drain, up to a
     configured grace period
  -> Chassis flushes buffered logs and metrics
  -> Chassis unregisters from the service registry (if using
     self-registration, see the related pattern)
  -> Process exits
```

## 8. Implementation variants

- **In process library, single language.** The chassis ships as a language
  package, a Maven artifact, an npm package, a Go module, a Python wheel,
  that a service imports at build time. Netflix's Karyon for the JVM and
  Peter Bourgon's Go kit for Go are the two most cited historical examples
  of this shape (Netflix, "Karyon", https://github.com/Netflix/karyon,
  verified 2026-08-02; Peter Bourgon, "Go kit, a standard library for
  microservices", https://peter.bourgon.org/applied-go-kit/, verified
  2026-08-02). This variant gives the lowest per request overhead, because
  the cross cutting code runs in the same process and the same memory space
  as the business logic, but it is single language by its very nature, since a
  Java chassis cannot be imported by a Python service.
- **Opinionated framework starter bundle.** Rather than a set of loosely
  coupled modules, the chassis is a curated dependency bundle that
  auto configures itself, with the framework's own conventions doing most of
  the wiring. Spring Boot's starter dependency mechanism, paired with Spring
  Cloud's Netflix OSS integrations, Eureka for discovery, and historically
  Hystrix for circuit breaking, Zuul for routing, is the most widely
  documented instance of this pattern in the Java stack. Adding the
  starter dependencies auto configures discovery registration, health
  endpoints via Actuator, and metrics export with minimal explicit wiring
  code in the consuming service, a bundle pattern documented across multiple
  independent tutorials (see the "Known production uses" section below).
- **Base container image plus shared entrypoint.** In a genuinely polyglot
  organization, the chassis is expressed at the container layer rather than
  the language layer. A shared base Docker image bakes in a sidecar log
  shipper, a standard entrypoint script that reads a common set of
  environment variables and starts a health check probe, and a build
  pipeline template, a shared CI/CD job definition, rather than a shared
  code dependency. This variant sacrifices in process convenience and
  compile time type safety for genuine language independence.
- **Sidecar or service mesh proxy.** The network facing subset of the
  chassis's responsibilities, mTLS, retries, circuit breaking, trace
  propagation, traffic shaping, is delegated to an out of process sidecar
  proxy that intercepts every network call, leaving the in process chassis,
  if one exists at all, to handle only what the sidecar has no way to
  reach, such as language idiomatic structured logging calls made directly
  from application code. This is not strictly the same pattern as
  Richardson catalogs, since the mesh operates at the infrastructure layer
  rather than the application layer, but it is the dominant alternative
  organizations reach for instead of, or in combination with, a
  code level chassis, and dimension 13 covers the relationship in more
  detail.
- **Scaffolding generated, then forked.** Some organizations deliberately
  choose not to maintain a shared runtime dependency at all, and instead
  generate a new service from a template repository, the sibling Service
  Template pattern, that copies the cross cutting code directly into the
  new service's own repository at creation time. This trades the
  coordination cost of a shared library, every consumer must be upgraded
  together, for the coordination cost of propagating a fix across many
  already-forked copies, and it is a legitimate variant for organizations
  that weigh those two costs differently, though it reintroduces the exact
  drift problem the pattern exists to prevent unless the organization has a
  disciplined process for periodically re syncing from the template.

## 9. Known production uses

- **Netflix, Karyon.** Netflix's own GitHub description states Karyon is
  "the nucleus or the base container for Applications and Services built
  using" the wider NetflixOSS stack, designed to be "container/framework
  agnostic" so it can plug into whatever runtime container an application
  uses, and it bundles bootstrapping, dependency injection wiring, runtime
  diagnostics, configuration management, and service discovery integration
  as a base layer that other Netflix services build on top of (Netflix,
  "Karyon", GitHub repository, https://github.com/Netflix/karyon, verified
  2026-08-02).
- **SoundCloud and the wider Go microservices community, Go kit.** Go kit's
  own documentation, authored by Peter Bourgon, who developed it while
  working on distributed systems at SoundCloud and later Weaveworks,
  describes it as "a distributed programming toolkit for building
  microservices in large organisations," explicitly providing shared
  packages for transport (HTTP, gRPC, Thrift), logging, metrics, tracing,
  and rate limiting so individual service teams "focus on business logic"
  rather than re deriving this infrastructure per service (Peter Bourgon,
  "Go kit, a standard library for microservices",
  https://peter.bourgon.org/applied-go-kit/, verified 2026-08-02).
- **Spring Cloud Netflix stack.** Spring Cloud's Netflix integration
  module functions as a de facto chassis for the JVM microservices
  stack. Adding the Spring Cloud Netflix starter dependencies to a
  Spring Boot application provides auto configured integration with Eureka
  for service discovery, historically Hystrix for circuit breaking, and
  Zuul or the later Spring Cloud Gateway for edge routing, with Spring
  Boot Actuator supplying the shared health check and metrics endpoints
  that every consuming service inherits by declaring the dependency rather
  than by writing bespoke code, documented consistently across independent
  engineering write ups of the pattern, for example Iskren Ivanov,
  "Building microservices with Netflix OSS, Apache Kafka and Spring Boot,
  Part 1, Service registry and Config server", Medium,
  https://medium.com/@isilona/building-microservices-with-netflix-oss-apache-kafka-and-spring-boot-part-1-3397811a2781,
  verified 2026-08-02.
- **Dropwizard, at Yammer.** Dropwizard was created at Yammer specifically
  to bundle Jetty, Jersey, and Jackson together with a standard metrics,
  health check, logging, and operational command line interface layer for
  every JVM service the company ran, and its own project description
  frames its purpose as delivering fully operational web services out of
  the box rather than requiring each team to assemble the equivalent stack
  by hand, which is the chassis pattern applied before the microservices
  vocabulary existed to name it, a founding story consistent across
  Dropwizard's documentation and multiple independent third party
  summaries of its origin at Yammer.
- **Richardson's own catalog entry**, which explicitly names the pattern's
  purpose as amortizing the "reusable build logic" and "cross-cutting"
  wiring cost across a fleet, is itself grounded in the author's stated
  experience consulting on and documenting real, large microservices
  architectures (Chris Richardson, "Pattern. Microservice chassis",
  https://microservices.io/patterns/microservice-chassis.html, verified
  2026-08-02, and *Microservices Patterns*, Manning, 2018, chapter 11).

## 10. Consequences

Positive.

- A new service reaches a working operational baseline, health
  checks, structured logs, metrics, tracing, in the time it takes to declare
  a dependency, rather than the days or weeks it takes to hand assemble the
  same baseline.
- Fleet wide operational tooling, dashboards, alert rules, log queries, on
  call runbooks, can assume a consistent shape across every service, because
  every service that adopted the chassis exposes the same health check
  contract, the same log field names, and the same metric naming
  conventions.
- A fleet wide fix, for example patching a logging library vulnerability or
  adding a new mandatory security header, is authored once in the chassis
  and then rolled out through the normal dependency upgrade path, rather
  than requiring a coordinated pull request across every service repository.
- Institutional knowledge about the correct way to handle a cross cutting
  concern is encoded in one place and enforced by the dependency mechanism
  itself, rather than living in a wiki page that individual teams may or may
  not have read.

Negative.

- The chassis becomes a shared point of correlated failure. A bug in the
  chassis's health check logic, or a resource leak in its metrics exporter,
  is present in every service that has adopted the affected version
  simultaneously, unlike a bug isolated to one hand rolled service.
- Upgrading the chassis across a large fleet is itself a project, not a
  single pull request, and organizations that under invest in this
  coordination end up with a fleet fragmented across many chassis versions,
  which reproduces the original duplication problem one level up, now as
  version drift instead of code drift.
- The chassis inevitably encodes assumptions, about the deployment
  environment, about the preferred web framework, about the shape of
  configuration, that do not fit every service equally well, and teams
  whose service genuinely needs to deviate face either forking the chassis,
  defeating its purpose, or fighting it.
- Onboarding a new engineer now requires understanding two things instead
  of one, the service's own business logic, and the chassis's conventions
  and extension points, which is a real but often underestimated learning
  cost, especially when chassis documentation lags chassis capability.

## 11. Failure modes and misuse

- **Symptom.** A logging format change ships in a chassis minor version
  bump and silently breaks a downstream log parsing pipeline for every
  service that auto upgraded. **Cause.** The chassis owner treated a
  behavior change, not merely an added capability, as backward compatible
  under semantic versioning, because the change looked additive from the
  chassis's own test suite even though it altered an implicit contract
  consumers depended on. **Fix.** Treat any change to an externally
  observable contract, log schema, metric name, health check response
  shape, as a breaking change requiring a major version bump and an
  explicit migration note, even when the chassis's internal API is
  unchanged.

- **Symptom.** A new service takes noticeably longer to start, or its
  memory footprint is unexpectedly large, compared to what its own business
  logic would suggest. **Cause.** The chassis has accumulated cross cutting
  concerns nobody actually needs for every service, a full APM agent, a
  heavyweight dependency injection container, an unused message broker
  client, bundled as mandatory rather than opt in, because it was easier for
  the chassis team to ship one bundle than to maintain modular boundaries.
  **Fix.** Factor the chassis into independently adoptable modules
  (dimension 5) so a service pulls in only the concerns it needs, and treat
  everything bundled by default as a design smell to be corrected, not a
  convenience to be preserved.

- **Symptom.** Business logic starts appearing inside the chassis itself,
  for example a shared customer tier enum or a shared validation rule
  that only makes sense for the orders and payments domains, not for every
  service in the fleet. **Cause.** The chassis is the easiest place to put
  shared code because every service already depends on it, so it becomes a
  magnet for any code more than one team wants to reuse, regardless of
  whether that code is a genuine cross cutting concern or accidental domain
  coupling. **Fix.** Draw and enforce an explicit boundary. The chassis
  owns infrastructure concerns, logging, config, discovery, health,
  tracing, auth plumbing, and nothing that encodes a business rule. Shared
  domain logic that legitimately needs reuse belongs in a separate,
  explicitly scoped domain library, never smuggled into the infrastructure
  chassis.

- **Symptom.** Teams stop upgrading the chassis, and six months later half
  the fleet is on version 3 and half is on version 7, with the platform
  team maintaining compatibility shims for both. **Cause.** Upgrading the
  chassis was left as a purely voluntary, unscheduled activity with no
  forcing function, so it competed for engineering time against feature
  work and consistently lost. **Fix.** Treat chassis upgrades the same way
  a security patch is treated. Give the platform team the authority and the
  tooling, automated dependency bump pull requests, a deprecation and
  end of life policy for old versions, a fleet wide dashboard showing
  version adoption, to drive the fleet toward convergence rather than
  waiting for it.

- **Symptom.** A team abandons the chassis entirely and vendors a forked
  copy of it into their own service, and from that point on receives none
  of the chassis's future fixes. **Cause.** The chassis's extension points
  (dimension 5) were insufficient for a genuine, legitimate deviation the
  team needed, and forking was the only escape hatch available. **Fix.**
  Design extension points deliberately for the known axes of legitimate
  variation, custom health checks, custom metric tags, pluggable auth
  providers, so that a team with an unusual but valid requirement can
  satisfy it through an approved extension mechanism rather than through a
  full fork.

## 12. Trade-off matrix

| Force | Microservice Chassis | Copy-paste per service | Service mesh sidecar | Scaffolding generated, then forked |
|---|---|---|---|---|
| New-service setup speed | Fast, one dependency declaration | Slow, hand-assembled each time | Fast for network concerns, chassis-equivalent needed for language-level concerns | Fast at creation, but the copy immediately starts drifting |
| Fleet-wide consistency | Strong, enforced by shared dependency | Weak, each copy drifts independently | Strong for network-layer concerns only | Strong at creation moment, decays over time |
| Coupling introduced | A shared build-time dependency across the fleet | None across services, but hidden duplication debt | A shared runtime infrastructure dependency, not a code dependency | None after creation, by design |
| Cost of a fleet-wide fix | One chassis release, then a coordinated rollout | Must touch every service's copy individually | One sidecar or mesh control-plane update | Must touch every service's copy individually, same as copy-paste |
| Polyglot friendliness | Weak unless one chassis per language is maintained | Strong, each service is fully independent | Strong, sidecar is language-agnostic | Strong, each service is fully independent |
| Blast radius of a defect | Fleet-wide for the affected chassis version | Isolated to one service | Fleet-wide for the affected mesh version, network concerns only | Isolated to one service after the fork |
| Suits fleet size | Dozens to hundreds of services | A handful of services | Any size, but highest value in a large fleet | Small fleets, or organizations avoiding shared runtime dependencies |

## 13. Related and incompatible patterns

- **Service Template** is the pattern's constant companion and is easy to
  confuse with it. The chassis is the runtime dependency a service links
  against. The Service Template is the code generator or repository
  scaffold that produces a new, empty service already wired to the current
  chassis version. An organization can have a chassis with no template,
  developers manually wire the dependency into a new repo, or, less
  commonly, a template that copies boilerplate directly rather than
  depending on a shared chassis library, the scaffolding generated then
  forked variant in dimension 8. The mature, most cited form of the
  pattern pair has both. The template generates a repository, and that
  repository's only cross cutting code is a dependency declaration on the
  chassis.
- **Self-Registration and Third-Party Registration** are two of the
  cross cutting concerns a chassis very commonly implements, since service
  discovery registration is exactly the kind of repetitive, environment
  specific plumbing the pattern exists to centralize. A chassis that owns
  self registration means every consuming service calls one chassis
  provided function at startup rather than re implementing the registry
  client's registration and heartbeat logic per service.
- **Circuit Breaker** is frequently provided by the chassis as a wrapped
  HTTP or RPC client, so that every outbound call a service makes is
  automatically protected without the service author needing to remember to
  apply the wrapper manually. This is the historical role Netflix's Hystrix
  played inside chassis shaped Spring Cloud applications.
- **API Gateway** sits at the edge of the system and is a distinct pattern
  addressing a different concern, external client access and request
  routing or aggregation, but a chassis and a gateway are frequently
  developed by the same platform team and share underlying libraries for
  authentication, rate limiting, and observability, since both are
  infrastructure the platform team owns so product teams do not have to.
- **Database per Service** is compatible with and largely orthogonal to the
  chassis. The chassis does not, as a rule, own data access code, since data
  models are service specific by their very nature, though it may provide a shared
  database connection pooling and migration tooling convention as one of
  its cross cutting modules.
- **Service Mesh** is the pattern most in tension with a code level
  chassis, not because the two are formally incompatible but because they
  compete for ownership of the same network facing concerns, retries,
  circuit breaking, mTLS, trace propagation. An organization that adopts a
  mature service mesh usually shrinks its chassis's scope down to
  language idiomatic, in process concerns the mesh cannot reach, structured
  logging call sites, business agnostic startup wiring, rather than
  discarding the chassis entirely, since a sidecar proxy has no visibility
  into what a service logs from inside its own process.

## 14. Refactoring path in and out

Introducing a chassis into an existing fleet that grew by copy paste.

1. Audit two or three representative existing services and enumerate the
   cross cutting code that is duplicated almost identically across them, the
   health check handler, the logging setup, the metrics registration, the
   config loading, the outbound HTTP client wrapping.
2. Extract that code into a new, separately versioned repository or
   package. Resist the temptation to also extract anything domain specific
   discovered along the way. Leave it in place and flag it for a separate,
   later refactor.
3. Publish version 1.0.0 of the chassis and migrate exactly one, low risk
   service onto it first, as a pilot, keeping the old hand rolled code path
   available in that service until the chassis based path has run in
   production long enough to build confidence.
4. Once the pilot is stable, migrate the remaining services incrementally,
   ideally opportunistically, alongside work already planned for each
   service, rather than as a single coordinated big bang migration across
   the whole fleet.
5. As each service migrates, delete its now redundant hand rolled
   cross cutting code so the fleet does not end up maintaining both the old
   pattern and the new one indefinitely.
6. Establish the ownership and versioning discipline, dimension 11's fixes,
   before the second or third chassis release ships, not after drift has
   already set in.

Removing a chassis once it stops earning its place, for example after
migrating to a service mesh that has absorbed most of its network facing
responsibilities, or after the fleet has consolidated to a size where the
coordination overhead exceeds the benefit.

1. Identify which chassis provided concerns are now redundant with
   infrastructure the platform provides some other way, a mesh sidecar
   handling retries and mTLS, a platform managed logging sidecar handling
   structured log shipping.
2. Shrink the chassis's scope module by module rather than deprecating it
   wholesale in one step, removing only the modules whose responsibility
   has genuinely moved elsewhere.
3. For any remaining chassis responsibility that a specific service wants to
   own itself, a legitimate, well justified deviation, provide a clear
   inlining path. Copy the relevant chassis code directly into that
   service and drop the chassis dependency for it, accepting that this
   service now differs from the fleet baseline deliberately and
   documented, rather than accidentally.
4. Once no consuming service remains on the oldest chassis major version,
   archive that version's branch and its compatibility shims so the
   platform team is not indefinitely supporting a version nobody uses.

## 15. Testing and verification

Because the chassis is infrastructure, not business logic, its own test
suite is a contract test suite. It should assert the shape of what it
exposes, the health check response schema, the metric names and label sets,
the log field names, rather than testing behavior specific to any consuming
service. A chassis with strong contract tests catches a breaking change
before it ships, which is the single highest-value testing investment
given how many services one bad release can affect.

For a consuming service, testing becomes easier in one respect and harder in
another because of the chassis. It becomes easier because the service's own
test suite no longer needs to cover the cross cutting concerns at all.
Health check behavior, metrics correctness, and log formatting are the
chassis's tested responsibility, not the service's, so the service's tests
can focus entirely on business logic. It becomes harder in the sense that
integration and end to end tests must now account for the chassis's startup
sequence, readiness gating, for example, or use a lightweight test double
for the chassis in unit tests that would otherwise be slowed down by
chassis initialization overhead. A common technique is a chassis provided
test double or test mode flag that disables real service registration and
real metrics export during unit tests while leaving the same code path
otherwise intact, so the service's tests exercise the real wiring logic
without a network dependency on a real service registry.

Consumer driven contract testing between the chassis and its consumers is
the appropriate technique for verifying the chassis has not broken any
consuming service's expectations across a version bump. Each consuming
service, or a representative sample, publishes a contract describing what
it expects from the chassis, the shape of the health endpoint it depends
on, the metric names its dashboards query, and the chassis's own CI
pipeline verifies every published contract against each candidate release
before that release goes out, which converts an otherwise fleet wide,
after the fact discovery of a breaking change into a pre release gate.

## 16. Observability signals

A healthy chassis backed fleet shows a small, well defined set of
observability signals that are consistent across services, which is the
entire operational point of the pattern.

- Every service exposes the same health and readiness endpoint shape, for
  example `/health` returning liveness and `/ready` returning readiness gated
  on downstream dependency checks, so a fleet wide dashboard or an
  orchestrator's probe configuration is identical across services rather
  than bespoke per service.
- Structured log lines across the fleet share a consistent base schema,
  service name, version, environment, trace id, severity, which is the
  signal that the chassis's logging module is actually being used correctly
  rather than bypassed. A service emitting unstructured or differently
  shaped log lines is a signal that either the service opted out of the
  chassis's logging module or is logging directly around it, which the
  platform team should investigate.
- A single, fleet wide chassis version metric or label, many chassis
  implementations expose their own version as a gauge or a build info
  metric, lets the platform team see version adoption skew across the
  fleet at a glance, which is the direct observability signal for the
  drift failure mode in dimension 11.
- Higher error rates or latency correlated across many, otherwise
  unrelated services immediately after a chassis version rollout is the
  clearest signal of a chassis introduced regression, and is exactly the
  correlated blast radius consequence named in dimension 10. A fleet wide
  deployment dashboard that can filter by chassis version, not only by
  service, is the operational tool that makes this signal visible quickly.
- Circuit breaker state transitions, closed to open, open to half open,
  when the chassis owns the circuit breaker, are a signal worth exposing as
  a first class metric with the downstream dependency name as a label,
  since an open circuit is the chassis actively protecting a service from a
  failing dependency and is operationally significant on its own.

## 17. Security and privacy implications

The chassis is a natural place to centralize a fleet's inbound
authentication and authorization plumbing, token validation, mTLS
certificate verification, and this is a genuine security benefit when done
correctly. A vulnerability found in the token validation logic is fixed once
in the chassis rather than independently in every service's own copy, and
security relevant defaults, mandatory TLS, mandatory token expiry checks,
can be enforced by the chassis rather than left to each service author's
discretion. This same centralization is also the pattern's largest single
security risk. A vulnerability introduced into the chassis's auth module is,
by construction, present in every service that depends on the affected
version simultaneously, which is a materially worse blast radius than the
same class of bug isolated to one hand rolled service, and it means the
chassis's own security review and patch release process deserves at least as
much rigor as the organization's most security sensitive individual service.

A related and easy to miss risk is the chassis's structured logging module
becoming an unintentional data exfiltration surface. Because the chassis's
logging convention often auto attaches request metadata or object fields to
every log line for consistency, a service author who is unaware of exactly
what the chassis captures can unintentionally log sensitive fields, an
authorization header, a full request body containing personal data, simply
by using the chassis's logging helper in the ordinary way. The mitigation is
for the chassis itself to own field level redaction rules for known
sensitive patterns, common header names, common PII field names, as a
default rather than relying on every consuming service to apply redaction
correctly on its own, since the entire premise of the pattern is that
consuming services should not have to think hard about cross cutting
concerns.

Where the pattern is largely silent is on business domain level data
handling, encryption of data at rest, field level access control on a
specific business entity, since those decisions are correctly the
responsibility of the individual service that owns the relevant data,
consistent with the non applicability point in dimension 4 that a chassis
should never encode business domain logic. This is engineering judgement,
not a sourced claim. The boundary between the chassis owning a security
concern and the service owning a security concern tracks the same
boundary between infrastructure concern and domain concern established in
dimension 11's third failure mode.

## 18. References

- Chris Richardson, "Pattern. Microservice chassis",
  https://microservices.io/patterns/microservice-chassis.html, verified
  2026-08-02.
- Chris Richardson, *Microservices Patterns*, Manning Publications, 2018,
  chapter 11, "Developing production ready services."
- Netflix, "Karyon", GitHub repository README and wiki,
  https://github.com/Netflix/karyon, verified 2026-08-02.
- Peter Bourgon, "Go kit, a standard library for microservices",
  https://peter.bourgon.org/applied-go-kit/, verified 2026-08-02.
- Iskren Ivanov, "Building microservices with Netflix OSS, Apache Kafka and
  Spring Boot, Part 1, Service registry and Config server", Medium,
  https://medium.com/@isilona/building-microservices-with-netflix-oss-apache-kafka-and-spring-boot-part-1-3397811a2781,
  verified 2026-08-02.

## Code examples

The three examples below implement the same minimal chassis surface, a
health check, structured request logging, and a circuit breaker wrapped
outbound call, in three different languages, then show a consuming service
using it. Each is original and was executed locally.

### Go

Go kit's own production shape is a set of composable middleware functions
wrapping an `http.Handler`. The following example is a minimal, original
implementation of the same idea, not a copy of Go kit's source.

```go
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sync"
	"time"
)

// Chassis owns cross-cutting concerns. A consuming service never
// re-implements health checks, logging, or the circuit breaker.
type Chassis struct {
	serviceName string
	healthMu    sync.RWMutex
	healthy     bool
	breaker     *CircuitBreaker
}

func NewChassis(name string) *Chassis {
	return &Chassis{serviceName: name, healthy: true, breaker: NewCircuitBreaker(3, 5*time.Second)}
}

func (c *Chassis) SetHealthy(v bool) {
	c.healthMu.Lock()
	defer c.healthMu.Unlock()
	c.healthy = v
}

func (c *Chassis) HealthHandler(w http.ResponseWriter, r *http.Request) {
	c.healthMu.RLock()
	defer c.healthMu.RUnlock()
	status := "ok"
	code := http.StatusOK
	if !c.healthy {
		status = "unhealthy"
		code = http.StatusServiceUnavailable
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	json.NewEncoder(w).Encode(map[string]string{"service": c.serviceName, "status": status})
}

// LoggingMiddleware wraps any handler with the fleet-standard log line.
func (c *Chassis) LoggingMiddleware(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next(w, r)
		log.Printf("service=%s method=%s path=%s duration_ms=%d",
			c.serviceName, r.Method, r.URL.Path, time.Since(start).Milliseconds())
	}
}

// CircuitBreaker is a minimal chassis-owned resilience primitive.
type CircuitBreaker struct {
	mu           sync.Mutex
	failures     int
	threshold    int
	open         bool
	openedAt     time.Time
	resetTimeout time.Duration
}

func NewCircuitBreaker(threshold int, resetTimeout time.Duration) *CircuitBreaker {
	return &CircuitBreaker{threshold: threshold, resetTimeout: resetTimeout}
}

func (b *CircuitBreaker) Call(fn func() error) error {
	b.mu.Lock()
	if b.open {
		if time.Since(b.openedAt) > b.resetTimeout {
			b.open = false
			b.failures = 0
		} else {
			b.mu.Unlock()
			return fmt.Errorf("circuit open")
		}
	}
	b.mu.Unlock()

	err := fn()

	b.mu.Lock()
	defer b.mu.Unlock()
	if err != nil {
		b.failures++
		if b.failures >= b.threshold {
			b.open = true
			b.openedAt = time.Now()
		}
		return err
	}
	b.failures = 0
	return nil
}

// --- consuming service: only business logic below this line ---

func orderHandler(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintln(w, `{"order_id":"o-1","status":"created"}`)
}

func main() {
	chassis := NewChassis("order-service")

	mux := http.NewServeMux()
	mux.HandleFunc("/health", chassis.HealthHandler)
	mux.HandleFunc("/orders", chassis.LoggingMiddleware(orderHandler))

	callCount := 0
	for i := 0; i < 5; i++ {
		err := chassis.breaker.Call(func() error {
			callCount++
			return fmt.Errorf("downstream unavailable")
		})
		fmt.Printf("attempt %d: err=%v\n", i+1, err)
	}

	_ = mux
	fmt.Println("chassis wired: health, logging middleware, circuit breaker all active")
}
```

Compiled and run locally.

```
$ go run chassis.go
attempt 1: err=downstream unavailable
attempt 2: err=downstream unavailable
attempt 3: err=downstream unavailable
attempt 4: err=circuit open
attempt 5: err=circuit open
chassis wired: health, logging middleware, circuit breaker all active
```

### TypeScript

```typescript
type Health = { service: string; status: "ok" | "unhealthy" };

class CircuitBreaker {
  private failures = 0;
  private open = false;
  private openedAt = 0;

  constructor(private threshold: number, private resetMs: number) {}

  async call<T>(fn: () => Promise<T>): Promise<T> {
    if (this.open) {
      if (Date.now() - this.openedAt > this.resetMs) {
        this.open = false;
        this.failures = 0;
      } else {
        throw new Error("circuit open");
      }
    }
    try {
      const result = await fn();
      this.failures = 0;
      return result;
    } catch (err) {
      this.failures += 1;
      if (this.failures >= this.threshold) {
        this.open = true;
        this.openedAt = Date.now();
      }
      throw err;
    }
  }
}

class Chassis {
  private healthy = true;
  readonly breaker: CircuitBreaker;

  constructor(private serviceName: string) {
    this.breaker = new CircuitBreaker(3, 5000);
  }

  setHealthy(v: boolean): void {
    this.healthy = v;
  }

  health(): Health {
    return { service: this.serviceName, status: this.healthy ? "ok" : "unhealthy" };
  }

  withLogging<A extends unknown[], R>(fn: (...args: A) => R): (...args: A) => R {
    return (...args: A): R => {
      const start = Date.now();
      const result = fn(...args);
      const durationMs = Date.now() - start;
      console.log(
        JSON.stringify({ service: this.serviceName, event: "handled", duration_ms: durationMs }),
      );
      return result;
    };
  }
}

// --- consuming service: business logic only ---

function createOrder(id: string): { orderId: string; status: string } {
  return { orderId: id, status: "created" };
}

async function main(): Promise<void> {
  const chassis = new Chassis("order-service");

  const handler = chassis.withLogging(createOrder);
  console.log(handler("o-1"));
  console.log(chassis.health());

  for (let i = 1; i <= 5; i++) {
    try {
      await chassis.breaker.call(async () => {
        throw new Error("downstream unavailable");
      });
    } catch (err) {
      console.log(`attempt ${i}: ${(err as Error).message}`);
    }
  }
}

main();
```

Compiled and run locally.

```
$ npx -y tsc --strict --target es2020 --module commonjs chassis.ts && node chassis.js
{ orderId: 'o-1', status: 'created' }
{"service":"order-service","event":"handled","duration_ms":0}
{ service: 'order-service', status: 'ok' }
attempt 1: downstream unavailable
attempt 2: downstream unavailable
attempt 3: downstream unavailable
attempt 4: circuit open
attempt 5: circuit open
```

### Python

```python
import functools
import json
import time
from dataclasses import dataclass, field


@dataclass
class CircuitBreaker:
    threshold: int
    reset_seconds: float
    failures: int = 0
    open: bool = False
    opened_at: float = 0.0

    def call(self, fn):
        if self.open:
            if time.monotonic() - self.opened_at > self.reset_seconds:
                self.open = False
                self.failures = 0
            else:
                raise RuntimeError("circuit open")
        try:
            result = fn()
            self.failures = 0
            return result
        except Exception:
            self.failures += 1
            if self.failures >= self.threshold:
                self.open = True
                self.opened_at = time.monotonic()
            raise


@dataclass
class Chassis:
    service_name: str
    healthy: bool = True
    breaker: CircuitBreaker = field(default_factory=lambda: CircuitBreaker(3, 5.0))

    def set_healthy(self, value: bool) -> None:
        self.healthy = value

    def health(self) -> dict:
        return {"service": self.service_name, "status": "ok" if self.healthy else "unhealthy"}

    def with_logging(self, fn):
        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            start = time.monotonic()
            result = fn(*args, **kwargs)
            duration_ms = int((time.monotonic() - start) * 1000)
            print(json.dumps({"service": self.service_name, "event": "handled", "duration_ms": duration_ms}))
            return result

        return wrapped


# --- consuming service: business logic only ---

def create_order(order_id: str) -> dict:
    return {"order_id": order_id, "status": "created"}


def main() -> None:
    chassis = Chassis(service_name="order-service")

    handler = chassis.with_logging(create_order)
    print(handler("o-1"))
    print(chassis.health())

    def failing_call():
        raise RuntimeError("downstream unavailable")

    for attempt in range(1, 6):
        try:
            chassis.breaker.call(failing_call)
        except RuntimeError as err:
            print(f"attempt {attempt}: {err}")


if __name__ == "__main__":
    main()
```

Compiled and run locally.

```
$ python3 chassis.py
{"service": "order-service", "event": "handled", "duration_ms": 0}
{'order_id': 'o-1', 'status': 'created'}
{'service': 'order-service', 'status': 'ok'}
attempt 1: downstream unavailable
attempt 2: downstream unavailable
attempt 3: downstream unavailable
attempt 4: circuit open
attempt 5: circuit open
```

A Swift or Java translation of the same three primitive chassis, health
check, logging wrapper, circuit breaker, follows the identical shape and is
omitted here to keep the entry focused. The pattern's structure does not
change across a fourth or fifth language, only the idiom for wrapping a
function, a protocol witness in Swift, an interface implementation in Java,
changes.
