---
name: Microservices Architecture
slug: microservices-architecture
family: 05-architectural
category: Architectural
aliases: [Microservice Architecture, Fine-Grained SOA, Service-Based Architecture]
first_described: "Fowler, Lewis 2014, popularizing a style already in production at Amazon and Netflix in the mid-2000s"
maturity: established
related: [database-per-service, api-gateway, circuit-breaker, saga, event-driven-architecture, cqrs, strangler-fig, service-mesh]
incompatible_with: [shared-database-per-service, distributed-monolith]
verified: 2026-08-02
---

## 1. Name, aliases, and lineage

The canonical name is Microservices, sometimes written Microservice Architecture
or, in older enterprise documents, Fine-Grained Service-Oriented Architecture.
The name was popularized by Martin Fowler and James Lewis in their March 2014
article "Microservices," published on martinfowler.com, which opens by
defining the style as "an approach to developing a single application as a
suite of small services, each running in its own process and communicating
with lightweight mechanisms, often an HTTP resource API" (Fowler, Lewis,
"Microservices," martinfowler.com, 2014, https://martinfowler.com/articles/microservices.html,
verified 2026-08-02).

The word itself predates the article. Fowler and Lewis note that the term had
circulated in workshops and among practitioners since around 2011, but their
article is the piece that fixed the vocabulary the industry now uses. The
practice, as opposed to the name, is older still. Amazon's internal
service-oriented mandate and Netflix's post-2008 migration off a monolithic
data center stack both predate the term by several years, and both are cited
repeatedly in the industry's own retrospective writing as the two systems that
proved the style in large production deployments before it had a name (Newman,
"Building Microservices," 2nd edition, O'Reilly, 2021, Chapter 1). This entry
treats "Microservices Architecture" as the name of a style, not a single
pattern, because the eighteen-dimension template below is being applied to a
family of composed decisions rather than one structural device, and that
composition is exactly what dimension 5 describes.

The style is also sometimes described by what it replaces or resists. A
"distributed monolith" is the pejorative name practitioners use for a set of
services that are deployed independently but still share a database, a
release train, or a synchronous call chain deep enough that no service can
actually change without coordinating with the others. That failure mode is
common enough that it earns its own entry in dimension 11.

## 2. Problem and context

A single deployable application, however well factored internally, eventually
runs into three problems that module boundaries inside one process cannot
solve. First, every team that touches the codebase shares one build, one test
suite, and one release train, so the release schedule of the whole system is
capped by the slowest, riskiest, or most contested change in flight. Second,
the whole application scales as one unit, so a component that needs ten times
the compute of its neighbors forces the operator to either over-provision the
entire process or accept that the bottleneck component throttles everything
sharing its host. Third, a runtime failure inside one module, an unbounded
loop, a memory leak, an unhandled exception in a background thread, can bring
down the whole process, because there is no process boundary between a
reporting feature and the checkout flow.

The context in which these three pressures become acute is a large
organization with many teams working on one system, where the system's
domains genuinely have different scaling profiles, different release
schedules, and different failure tolerances. A five-person team building an
internal tool for forty users has none of these pressures and gains nothing
from this architecture, an observation that is the entire content of
dimension 4. The pattern's real audience is an organization that has already
outgrown the communication bandwidth needed to coordinate a single
deployable, a situation Fowler and Lewis describe through Conway's Law, the
observation that an organization's software architecture tends to mirror its
communication structure, so once an organization has grown past the point
where all its engineers can coordinate one release, the software will
fragment along the same lines whether the architects intend it to or not
(Melvin E. Conway, "How Do Committees Invent?" Datamation, vol. 14, no. 5,
April 1968, pages 28 to 31; the quoted formulation is "organizations which
design systems... are constrained to produce designs which are copies of the
communication structures of these organizations," verified via secondary
citation of the primary text 2026-08-02).

## 3. Forces

Independent deployability against operational uniformity. Every service that
can ship on its own schedule is a service whose team no longer waits on
another team's release train, but every independently deployable unit is also
one more thing to build, containerize, version, monitor, and patch for
security, and that operational tax is paid whether or not the service changes
often.

Fault isolation against distributed complexity. A crash inside one service no
longer takes down its neighbors, and that is the single most concrete
reliability win the style offers. But the price is that a call which used to
be a language-level function invocation, cheap, synchronous, and
type-checked, is now a network call across a boundary that can be slow,
partitioned, or simply absent, and every one of those calls needs a timeout,
a retry policy, and a fallback that the in-process version never needed.

Team autonomy against system-wide consistency. Splitting a system along
business-capability boundaries lets each team choose its own language,
storage engine, and release schedule, which is the entire point of the
"decentralized governance" and "decentralized data management"
characteristics that Fowler and Lewis name explicitly (Fowler, Lewis,
"Microservices," 2014). That same latitude means the organization gives up a
single source of truth for any piece of data that spans two services, and it
gives up the ability to run one cross-cutting database transaction across a
business operation, forcing the eventual-consistency and saga machinery
described in the related-patterns section.

Latency against modularity. Decomposing a monolith's internal call graph into
network calls between processes trades a nanosecond-to-microsecond in-process
call for a call that, even on a fast internal network, costs low
single-digit milliseconds plus serialization overhead, and that cost compounds
multiplicatively across a deep call chain. The forces this pattern favors most
strongly are independent deployability and fault isolation at organizational
scale. The forces it most reliably sacrifices are full-path latency
predictability and the simplicity of a single, ACID-transactional data store.

## 4. Applicability and non-applicability

Reach for a microservices architecture when the organization has multiple
teams that need to ship independently on different schedules, when distinct
business capabilities inside the system have genuinely different scaling
profiles (an image-processing pipeline and a user-profile lookup do not need
the same number of replicas), when a specific capability needs a different
storage technology or runtime than the rest of the system (a
recommendation engine that benefits from a graph database sitting inside an
otherwise relational system), when the organization needs to isolate a
regulated or high-risk domain, such as payments, behind its own deployment and
audit boundary, or when an existing monolith has grown large enough that its
build, test, and deploy cycle has become the primary bottleneck on
engineering velocity, in which case the Strangler Fig entry describes the
incremental migration path.

Do not reach for it when the team is smaller than roughly two Scrum-team's
worth of engineers, because the operational tax, service lookup and
registration, distributed tracing, per-service CI and deployment pipelines,
on-call rotation across many small deployables, will exceed any coordination
savings. Do not reach for it when the domain model is not yet well
understood, because splitting a system along the wrong seams produces a
distributed monolith that is strictly worse than a well-factored single
deployable, since the boundaries are now expensive to move. Sam Newman makes
this point directly. premature decomposition before the domain boundaries
are understood is one of the most common and most costly microservices
mistakes, and a modular monolith is the safer default until those boundaries
are proven stable (Newman, "Building Microservices," 2nd edition, O'Reilly,
2021, Chapter 1, "Monolith First"). Do not reach for it when the system's
transactions are genuinely multi-entity and strongly consistent, such as a
double-entry ledger, because forcing that domain across service boundaries
either produces a distributed transaction nightmare or forces a redesign
around eventual consistency that the business does not actually want.
Segment's own 2018 retrospective on merging around 140 services back into a
single deployable is the clearest documented case of an organization
concluding the trade was working against them. "The overhead from managing
all of these services was a huge tax on our team. We were literally losing
sleep over it since it was common for the on-call engineer to get paged to
deal with load spikes" (Twilio Segment Engineering, "Goodbye Microservices,"
10 July 2018,
https://www.twilio.com/en-us/blog/developers/best-practices/goodbye-microservices/,
verified 2026-08-02). Finally, do not reach for it purely to follow industry
fashion, the decision should be driven by the three organizational pressures
in dimension 2, not by the belief that microservices are more modern or more
correct than a well-designed single deployable.

## 5. Structure

The style is a composition of several participants working together, not one
class hierarchy, which is why dimension 6 needs a system diagram rather than
a class diagram.

A service is the core unit, an independently deployable process that owns a
single, cohesive business capability and exposes it through an explicit,
versioned API, commonly HTTP or gRPC for request and response interaction,
and a message broker for asynchronous events. A service owns its own
persistent state. Nothing outside the service reads or writes that state
directly, a rule formalized in the Database per Service pattern (dimension
13).

A service registry or lookup mechanism tracks which network addresses
currently serve which service, since service instances in a cloud or
container environment are ephemeral. In a Kubernetes deployment this role is
filled by the Service object, which the Kubernetes documentation describes as
solving the problem, "if some set of Pods... provides functionality to other
Pods... inside your cluster, how do the frontends find out and keep track of
which IP address to connect to," by giving that set of Pods "a stable,
single outward-facing endpoint" that survives individual Pod restarts
(Kubernetes documentation, "Service," https://kubernetes.io/docs/concepts/services-networking/service/,
verified 2026-08-02).

An API gateway sits at the system's edge, terminating external traffic,
routing it to the correct internal service, and centralizing cross-cutting
concerns, authentication, rate limiting, and response aggregation, so that
individual services do not each reimplement them. Uber's Domain-Oriented
Microservice Architecture generalizes this idea into per-domain gateways,
described as "a single entry point" that "abstract[s] internal domain
complexity from external consumers," one layer inward from the system-wide
edge gateway (Uber Engineering, "Rethinking Microservice Architecture,"
https://www.uber.com/blog/microservice-architecture/, verified 2026-08-02).

An inter-service communication layer carries the actual traffic between
services, split into two shapes. Synchronous request and response is used
when the caller needs an immediate answer, and asynchronous messaging through
an event bus or broker is used when the caller only needs to know that a
fact happened and does not need to block on a downstream consumer's
processing of that fact. A resilience layer, timeouts, retries with backoff,
and circuit breakers, wraps every synchronous call, because a network call,
unlike an in-process call, can fail in ways an in-process call cannot,
partially, slowly, or not at all with no error returned. Finally, an
observability layer, structured logs, metrics, and distributed traces
correlated by a request ID that propagates across every hop, is a structural
requirement rather than an afterthought, because no single engineer can hold
the full call graph of a production incident in their head once that graph
spans a dozen independently deployed processes. Dimension 16 covers this in
detail.

## 6. ASCII structure diagram

```
                         +-------------------+
   external client ----> |    API Gateway    |
                         | (auth, routing,    |
                         |  rate limiting)     |
                         +----+-----------+----+
                              |           |
                 sync HTTP/gRPC           |  sync HTTP/gRPC
                              v           v
                    +------------+   +------------+
                    |  Service A |   |  Service B |
                    | (Orders)   |   | (Users)    |
                    | own DB     |   | own DB     |
                    +-----+------+   +-----+------+
                          |                |
                 publish  |        publish |
                          v                v
                    +---------------------------+
                    |   Event Bus / Broker       |
                    |   (Kafka, RabbitMQ, SNS)    |
                    +------+----------------+----+
                           |                |
                 subscribe|        subscribe|
                           v                v
                    +------------+   +------------+
                    |  Service C |   |  Service D |
                    | (Billing)  |   | (Notify)   |
                    | own DB     |   | own DB     |
                    +------------+   +------------+

  All service-to-service calls carry a correlation ID that
  the tracing layer (not shown) stitches into one trace.
  Lookup (not shown) resolves each service name to a
  current, healthy set of instances.
```

## 7. Dynamics

The two dynamics that matter most are a synchronous request that fans out
across services, and an asynchronous event that decouples a producer from its
consumers.

```
Synchronous fan-out. "place an order"

client   gateway   Orders   Inventory   Payment
  |         |         |         |          |
  | POST    |         |         |          |
  |-------->|         |         |          |
  |         | route   |         |          |
  |         |-------->|         |          |
  |         |         | check   |          |
  |         |         |-------->|          |
  |         |         |   ok    |          |
  |         |         |<--------|          |
  |         |         | charge             |
  |         |         |------------------->|
  |         |         |     charged        |
  |         |         |<-------------------|
  |         |  201    |                    |
  |         |<--------|                    |
  |  201    |         |                    |
  |<--------|         |                    |
```

```
Asynchronous decoupling. "order placed" event

  Orders service          Event Bus         Billing    Notification
       |                      |                |            |
       | publish OrderPlaced  |                |            |
       |--------------------->|                |            |
       |   ack (durable)      |                |            |
       |<----------------------                |            |
       |                      | deliver        |            |
       |                      |--------------->|            |
       |                      | deliver                    |
       |                      |----------------------------->
       |                      |                | invoice   |
       |                      |                | generated  |
       |                      |                |            | send push
       |                      |                |            | notification
```

The synchronous chain is a request-response tree with a caller waiting for
the deepest leaf to answer before anything returns, which means the chain's
total latency is bounded below by the sum of its slowest path and its total
reliability is bounded above by the product of every hop's individual
reliability, since the whole chain fails if any hop times out without a
fallback. The asynchronous flow inverts both properties. The producer's
request completes as soon as the broker durably accepts the event, consumers
process it independently and at their own pace, and a slow or temporarily
unavailable consumer degrades only that consumer's own freshness, not the
producer's response time or any sibling consumer's.

## 8. Implementation variants

Synchronous REST over HTTP with JSON is the most common variant for
externally facing and coarse-grained internal APIs, favored for its
ubiquity, human-readable payloads, and broad tooling support, at the cost of
serialization overhead and the absence of a strict schema contract unless
one is layered on with OpenAPI.

gRPC over HTTP/2 with Protocol Buffers is the common variant for
high-throughput internal service-to-service calls, trading REST's human
readability for a strongly typed, code-generated contract and substantially
lower serialization overhead. Monzo's engineering team describes exactly
this choice, running "services in Java, Python, and Scala" behind a common
"Linkerd" RPC proxy so the transport contract stays uniform even though the
service implementations do not (Monzo Engineering, "Building a modern bank
backend," 19 September 2016,
https://monzo.com/blog/2016/09/19/building-a-modern-bank-backend, verified
2026-08-02).

Event-driven, choreography-based communication routes state changes through
a durable broker rather than direct service-to-service calls, trading the
simplicity of a synchronous call for looser coupling and better resilience
to a downstream consumer's outage. This variant underlies the Event-Driven
Architecture and Saga entries and is discussed further there.

Container-orchestrated deployment, most commonly on Kubernetes, is the
dominant infrastructure variant, because a fleet of many small, independently
scaled processes needs automated scheduling, health checking, and service
lookup that manual deployment cannot provide once the fleet grows large. The
Kubernetes Service object described in dimension 5 is the concrete
mechanism.

Serverless functions as the unit of deployment, rather than a long-running
service process, is a lighter-weight variant sometimes called
"nanoservices," trading operational simplicity and pay-per-invocation cost
for cold-start latency and a more constrained execution model. It is most
appropriate for event handlers and low-traffic, bursty workloads rather than
for a system's core, latency-sensitive request path.

Domain-oriented layering, as in Uber's DOMA, is an organizational variant
rather than a transport variant. Rather than treating every microservice as a
flat, independent unit, services are grouped into domains, and calls are
restricted by an explicit layer hierarchy "from infrastructure to edge
services" so that a service in one layer cannot silently create a circular
dependency on a service above it (Uber Engineering, "Rethinking Microservice
Architecture," https://www.uber.com/blog/microservice-architecture/, verified
2026-08-02).

## 9. Known production uses

Netflix migrated from a monolithic data center architecture to a
cloud-native microservices architecture beginning around 2009, and its
engineering organization subsequently built and open sourced Hystrix, "a
sophisticated tool for dealing with latency and fault tolerance for
distributed systems" that combines a circuit breaker with thread-pool
isolation specifically because Netflix's own production traffic demonstrated
that a slow or failing downstream dependency could otherwise spread into a
system-wide outage (cited via Fowler, "CircuitBreaker,"
https://martinfowler.com/bliki/CircuitBreaker.html, verified 2026-08-02,
which in turn cites the Netflix Tech Blog's own writing on the tool).

Uber operates, as of a 2020 engineering-blog account, "around 2,200 critical
microservices," which the team subsequently classified into roughly 70
domains under the Domain-Oriented Microservice Architecture described in
dimensions 5 and 8, explicitly because a flat fleet of that size had become
"complex" rather than "comprehensible" without an added layer of domain
structure (Uber Engineering, "Rethinking Microservice Architecture,"
https://www.uber.com/blog/microservice-architecture/, verified 2026-08-02).

Monzo, a UK-regulated retail bank, built its backend from the ground up as a
microservices system, reporting "nearly 100 services" at its public beta
launch, growing to "about 150" by the time of its 2016 engineering writeup,
running primarily on Go with polyglot services in "Java, Python, and Scala"
behind a Linkerd RPC layer, on Kubernetes with Kafka for asynchronous
messaging (Monzo Engineering, "Building a modern bank backend," 19 September
2016, https://monzo.com/blog/2016/09/19/building-a-modern-bank-backend,
verified 2026-08-02). Monzo's case is notable because a regulated financial
institution chose this style from inception rather than migrating into it,
which is the exception rather than the rule among the documented cases here.

Segment operated over 140 independently deployed microservices supporting
its data-destination integrations, then deliberately consolidated them back
into a single deployable in 2018 after concluding the operational cost, "the
overhead from managing all of these services was a huge tax on our team,"
exceeded the isolation benefit for their specific workload shape, where each
new integration destination added roughly three more services per month
(Twilio Segment Engineering, "Goodbye Microservices," 10 July 2018,
https://www.twilio.com/en-us/blog/developers/best-practices/goodbye-microservices/,
verified 2026-08-02). Segment's account is cited here specifically because a
named, sourced case of an organization moving away from the style is exactly
the kind of counter-evidence dimension 4's non-applicability list depends on,
and it demonstrates that the pattern is a genuine trade-off rather than a
strictly dominant choice.

## 10. Consequences

The style delivers several positive consequences. Each service can be
deployed on its own schedule, independently of every other service's release
cycle, which removes the single-release-train bottleneck described in
dimension 2. Each service can be scaled independently, so compute spend
tracks the actual demand profile of each business capability rather than the
demand profile of the busiest component multiplied across the whole system.
A failure inside one service's process boundary does not, by default, crash
any other service's process, which is a real and measurable reliability
improvement over a shared process. Teams can choose the language, framework,
and storage engine best suited to their specific service, as Monzo's
polyglot Java, Python, Scala, and Go fleet demonstrates. New engineers can
understand and safely modify a single, small service without needing to hold
the entire system's codebase in their head, which lowers the cognitive load
of any individual change even as it raises the cognitive load of reasoning
about the system as a whole.

The style also carries real negative consequences. The system's overall
complexity does not disappear when a monolith is split into services, it
moves from inside one process, where a debugger and a stack trace can follow
it, to the network, where it must be reconstructed from logs, metrics, and
traces across many processes. Data consistency across service boundaries
becomes eventual rather than transactional by default, which forces every
cross-service business operation that used to be one ACID transaction into
an explicit saga or choreography, described in the related-patterns entry.
Testing a single business flow now requires either a full integration
environment with every dependency running, or a disciplined investment in
contract tests, described in dimension 15. A unit test suite alone cannot
catch a mismatch between two services' API contracts. Operational overhead
scales with the number of services rather than with the size of the
codebase, since each service needs its own build pipeline, its own
deployment manifest, its own monitoring dashboards, and its own on-call
runbook, which is exactly the cost Segment's retrospective names as the
deciding factor in their 2018 reversal. Finally, network latency becomes a
first-class design constraint rather than an implementation detail, because
every hop that used to be a function call is now a request that can be slow,
can fail independently, and must be budgeted for in the system's overall
latency target.

## 11. Failure modes and misuse

A common symptom is a change to Service A's response schema breaking Service
B in production even though B's own code and B's own tests were untouched.
The underlying cause is that services were split along technical layers or
team ownership rather than along stable business-capability boundaries, so
the API contract between A and B changes as often as either service's
internals do, and no contract test caught the drift before deployment. The
fix is to redraw the boundary around a business capability with a naturally
stable contract, and add consumer-driven contract tests, described in
dimension 15, so a breaking change fails CI before it reaches production.

A second symptom is that every request to a customer-facing endpoint takes
several hundred milliseconds even though each individual service in the call
path responds in single-digit milliseconds. The cause is a deep synchronous
call chain, where Service A calls B, which calls C, which calls D, has
stacked network round-trip latency across four hops instead of collapsing to
one, and no service in the chain fans requests out in parallel where the
domain would allow it. The fix is to flatten the call graph where possible,
parallelize independent downstream calls instead of chaining them serially,
and consider moving genuinely non-blocking work to the asynchronous flow in
dimension 7.

A third symptom is that services are individually deployable but a
production change still requires releasing three or four of them together,
in a specific order, or the system breaks. This is the distributed monolith
failure mode named in dimension 1, produced by a shared database, a
synchronous call chain with no independent versioning, or a shared client
library whose breaking changes ripple across every service that imports it.
The fix is to enforce Database per Service as described in dimension 13,
version every public API explicitly, and never let a shared library carry
business logic that multiple services depend on synchronously. Shared
infrastructure code is fine, shared domain logic is the trap.

A fourth symptom is that a single slow or failing downstream dependency
causes an outage across services that have no direct relationship to it. The
cause is that no circuit breaker or bulkhead isolates the caller's thread
pool or connection pool from the failing dependency, so retries and blocked
threads exhaust a shared resource pool and starve unrelated requests, exactly
the compounding failure pattern that motivated Netflix to build Hystrix
(Fowler, "CircuitBreaker," https://martinfowler.com/bliki/CircuitBreaker.html,
verified 2026-08-02). The fix is to wrap every synchronous cross-service
call in a circuit breaker with a bounded timeout and an explicit fallback,
and isolate the connection or thread pool per downstream dependency rather
than sharing one pool across all outbound calls.

A fifth symptom is that the organization has adopted microservices, but
on-call burden, build time, and the number of moving pieces have gone up
while shipping velocity has gone down. This is the misuse case Segment's
engineering team documented directly. The service count grew faster than the
organization's ability to operate each one well, three new services per
month against a team that had not scaled proportionally, and the isolation
benefit never materialized because the services in question shared a similar
load profile that a single, well-scaled deployable could have absorbed
(Twilio Segment Engineering, "Goodbye Microservices,"
https://www.twilio.com/en-us/blog/developers/best-practices/goodbye-microservices/,
verified 2026-08-02). The honest fix, per Segment's own account, was to
consolidate. The general lesson is to periodically re-examine whether the
number of services still matches the number of independent scaling,
deployment, and failure domains the organization actually has, rather than
treating "more services" as an unqualified good.

## 12. Trade-off matrix

| Force | Microservices | Modular Monolith | Event-Driven Architecture (standalone) |
|---|---|---|---|
| Independent deployability | Native; each service ships alone | None; one release train for the whole app | Depends; often paired with microservices, not a substitute for the deployment unit |
| Cross-cutting transactions | Requires a saga or choreography; no native ACID span | Native, single-process ACID transactions across modules | Same eventual-consistency cost as microservices for cross-boundary state |
| Operational overhead | High; per-service build, deploy, and on-call surface | Low; one build, one deploy, one on-call surface | High if services are also split; the pattern itself is about communication style, not deployment topology |
| Fault isolation | Strong; a crash in one service does not crash siblings | Weak; an unhandled fault can take down the whole process | Strong for consumers of an event; a slow consumer does not block the producer |
| Team autonomy | High; teams pick their own stack and schedule per service | Low; teams share one codebase's conventions and release cycle | Orthogonal; autonomy comes from the service boundary, not the messaging style alone |
| Onboarding a new engineer | Easier per-service, harder for the whole system's mental model | Harder per-module in a large codebase, easier for the whole system's mental model | Similar to whatever deployment topology it is paired with |

Note that Event-Driven Architecture, as a standalone entry, is a
communication pattern rather than a deployment-topology pattern, so this row
represents its effect when layered on top of a given topology rather than a
fully independent alternative to microservices. It is listed here because
practitioners frequently conflate the two, and the distinction matters when
choosing which trade-off is actually in play.

## 13. Related and incompatible patterns

Database per Service is close to a load-bearing precondition for
microservices rather than an optional companion. Chris Richardson's
description of the pattern states plainly that "services must be loosely
coupled so that they can be developed, deployed and scaled independently,"
and that decoupling only holds if each service's data is private to that
service (Richardson, "Database per Service" pattern page, microservices.io,
https://microservices.io/patterns/data/database-per-service.html, verified
2026-08-02). A system that calls itself microservices but shares one
database across services has not actually achieved the independent-
deployability property that motivates the style, and is a distributed
monolith by dimension 11's definition.

API Gateway composes with microservices as the edge participant described in
dimension 5, centralizing cross-cutting concerns so that individual services
do not each reimplement authentication and rate limiting.

Circuit Breaker composes with microservices as a required resilience
primitive on every synchronous inter-service call, for exactly the reason
described in dimension 11's fourth failure mode. A microservices system
without circuit breakers on its synchronous call paths is one slow
dependency away from a compounding outage.

Saga composes with microservices to restore a controlled, compensating-action
form of cross-service consistency once the native ACID transaction that a
monolith would have used is no longer available across a service boundary.

Event-Driven Architecture composes with microservices as the asynchronous
half of dimension 7's two dynamics, and is frequently the mechanism that
keeps services loosely coupled at the messaging layer even when they remain
tightly coupled at the domain-model layer. The two patterns solve different
problems and neither is a substitute for the other.

Strangler Fig is the incremental migration path into microservices from an
existing monolith, letting an organization carve capabilities out one at a
time behind a routing facade rather than attempting a single, high-risk
rewrite.

Shared Database Per Service is directly incompatible. It is the specific
anti-pattern that Database per Service exists to prevent, and adopting it
converts the system into a distributed monolith regardless of how many
independently deployable processes exist on top of it.

## 14. Refactoring path in and out

Introducing microservices into an existing monolith is best done
incrementally rather than as a single rewrite, following the Strangler Fig
approach. Identify one business capability with a clear, stable boundary and
comparatively low coupling to the rest of the system, extract its domain
logic and its data access behind a new internal interface inside the
monolith first, verify that the interface holds under real traffic with the
data still colocated, then move that capability's code and its data into a
new, independently deployed service, route a small percentage of live
traffic to it, and only once the new service has proven itself in production
does the corresponding code path get deleted from the monolith. Newman
argues for exactly this "Monolith First" sequencing precisely because
extracting a badly understood boundary is more expensive to reverse once it
is a network boundary than while it is still an in-process one (Newman,
"Building Microservices," 2nd edition, O'Reilly, 2021, Chapter 1). Repeat
this extraction one capability at a time, prioritizing the capability whose
independent scaling, release schedule, or failure isolation need is most
acute, rather than attempting to decompose the whole system at once.

Removing microservices, consolidating services back toward a monolith or a
smaller number of coarser services, follows roughly the reverse sequence,
and Segment's own account is the clearest documented example of the process.
Identify services whose load profiles, release schedules, and failure modes
are similar enough that splitting them apart is not earning its operational
cost, merge their code into one deployable behind a single build and deploy
pipeline, and consolidate their previously separate resource pools so that
traffic spikes in one absorb into the shared pool rather than paging an
on-call engineer for a single narrowly scoped service (Twilio Segment
Engineering, "Goodbye Microservices,"
https://www.twilio.com/en-us/blog/developers/best-practices/goodbye-microservices/,
verified 2026-08-02). The reversal is safest when done for the same reason
the original split was made, because the organizational or scaling
pressures that justified the split have genuinely changed, not merely
because the operational overhead is currently annoying.

## 15. Testing and verification

Unit tests inside each service verify that service's own business logic in
isolation and are unaffected by the architectural style. This is the layer
of testing microservices does not make harder.

Contract tests, most commonly implemented with a consumer-driven contract
tool such as Pact, verify that a service's API continues to satisfy the
expectations of every consumer that depends on it, without requiring the
consumer and the provider to run together in the same test environment. This
is the testing layer microservices makes newly necessary. A unit test suite
inside Service A cannot catch a breaking change to the schema Service B
depends on, because B's expectations live outside A's own test suite
entirely, and this is the direct mitigation for dimension 11's first failure
mode.

Component tests run a single service against stubbed or virtualized versions
of its downstream dependencies, verifying the service's behavior in
isolation from the reliability and availability of every other service in
the system, which is what makes it possible to run this layer of tests in CI
without standing up the whole distributed system.

Integration and full-path tests exercise a real, deployed subset or the
full set of services together, and are deliberately the smallest and
slowest layer of the test pyramid in a microservices system precisely
because standing up the full dependency graph is expensive and because a
failure in this layer is the hardest to localize to a single cause. A
disciplined team relies primarily on contract tests to catch cross-service
breakage and reserves full-path tests for the handful of business-critical
flows that must be verified working from request to response before a
release.

Fault-injection and resilience testing, deliberately injecting latency,
timeouts, or outright failures into a downstream dependency in a controlled
environment, verifies that the circuit breakers, retries, and fallbacks
described in dimension 11 actually behave as designed under failure, rather
than merely existing in the code. Netflix's development of deliberate
failure-injection practice alongside Hystrix is the origin of this testing
discipline in the microservices context (cited via Fowler, "CircuitBreaker,"
https://martinfowler.com/bliki/CircuitBreaker.html, verified 2026-08-02).

## 16. Observability signals

A healthy microservices system shows a request rate, error rate, and
duration histogram, the "RED" metrics, per service and per endpoint, with
error rates staying within an agreed budget and duration percentiles, p50,
p95, p99, staying inside the service's declared latency target. Each service
also emits saturation signals for its own resource pools. CPU, memory,
connection-pool utilization, and thread-pool utilization are the earliest
warning signs of the compounding-failure mode described in dimension 11 when
any one of them approaches exhaustion.

Distributed tracing, where every request carries a correlation ID that
propagates across every service hop and every span in that trace is recorded
with its own start time, duration, and outcome, is the signal that answers
the question a microservices system cannot answer any other way, which
specific hop, in a call chain spanning several independently deployed
processes, is responsible for a given request's latency or failure. Without
distributed tracing, diagnosing a slow request in a system with more than a
handful of services degrades into manually correlating timestamps across
separate log streams, which does not scale past a small number of hops.

Circuit breaker state is itself an observability signal worth exposing
directly. A breaker that has tripped open, meaning it is currently rejecting
calls to a downstream dependency without attempting them, is a leading
indicator of a downstream outage that an aggregate error-rate metric alone
might dilute across many services' worth of otherwise-healthy traffic.

A failing instance of this pattern shows the opposite of all of the above,
error budgets consumed silently because no per-service dashboard exists, a
single team paged for an incident whose root cause is three hops away in a
service they do not own, and a mean time to diagnosis measured in hours
because no correlation ID connects the log lines across the failing call
chain.

## 17. Security and privacy implications

Splitting a system into many independently deployed services multiplies the
network attack surface. Every inter-service call that used to be an
in-process function call is now a network call that, absent explicit
protection, is interceptable or spoofable on a shared network, which is why
production microservices deployments commonly enforce mutual TLS between
services rather than trusting network-layer isolation alone.

Authentication and authorization decisions must be made consistently across
every service rather than once at a single application boundary, because a
request that has already passed the edge gateway's authentication check
still needs each downstream service to enforce its own authorization rules
for the specific resource it owns. Centralizing this logic in a shared
library or a sidecar proxy, rather than reimplementing it per service, is
the common mitigation for the risk of one service silently omitting a check
the others enforce.

Each service's independent data store, the direct consequence of Database
per Service in dimension 13, means sensitive data can end up replicated or
derived across more storage locations than a single monolithic database
would have held it in, which increases the number of places a data-retention
policy, an encryption-at-rest requirement, or a right-to-erasure request
under a privacy regulation must actually be enforced, rather than enforced
once at a single data store.

Distributed tracing and centralized logging, the observability signals
described in dimension 16, themselves become a privacy surface if request
payloads or trace attributes are logged in full, unredacted form, since a
trace that correlates a user's request across a dozen services can
reconstruct a detailed behavioral record of that user's activity if it is
not scrubbed of personal data before it is stored. This is an analytical
implication rather than a claim about any specific vendor's default
behavior, and each deployment needs its own explicit policy on what a trace
span is permitted to carry.

## 18. References

- Fowler, M., Lewis, J. "Microservices." martinfowler.com, 25 March 2014.
  https://martinfowler.com/articles/microservices.html. Verified 2026-08-02.
- Fowler, M. "CircuitBreaker." martinfowler.com bliki, 2014.
  https://martinfowler.com/bliki/CircuitBreaker.html. Verified 2026-08-02.
- Conway, M. E. "How Do Committees Invent?" Datamation, vol. 14, no. 5, April
  1968, pages 28 to 31.
- Newman, S. "Building Microservices." 2nd edition, O'Reilly Media, 2021,
  Chapter 1.
- Richardson, C. "Database per Service" pattern page. microservices.io.
  https://microservices.io/patterns/data/database-per-service.html. Verified
  2026-08-02.
- Kubernetes documentation. "Service." kubernetes.io.
  https://kubernetes.io/docs/concepts/services-networking/service/. Verified
  2026-08-02.
- Uber Engineering. "Rethinking Microservice Architecture." uber.com/blog,
  2020. https://www.uber.com/blog/microservice-architecture/. Verified
  2026-08-02.
- Monzo Engineering. "Building a modern bank backend." monzo.com/blog, 19
  September 2016.
  https://monzo.com/blog/2016/09/19/building-a-modern-bank-backend. Verified
  2026-08-02.
- Twilio Segment Engineering. "Goodbye Microservices." twilio.com/blog, 10
  July 2018.
  https://www.twilio.com/en-us/blog/developers/best-practices/goodbye-microservices/.
  Verified 2026-08-02.

## Code examples

The following examples model the resilience layer described in dimensions 5
and 11, a service client wrapping a downstream call with a timeout, bounded
retries, and a circuit breaker that opens after repeated failures, falling
back to a cached or default response rather than propagating the failure to
its own caller. This is deliberately not a network-transport example,
because the pattern's structural contribution is the resilience wrapper
around any call, not any single wire protocol.

### TypeScript

```typescript
type Result<T> = { ok: true; value: T } | { ok: false; error: Error };

class CircuitBreaker {
  private failures = 0;
  private state: "closed" | "open" | "half-open" = "closed";
  private openedAt = 0;

  constructor(
    private readonly threshold: number,
    private readonly resetAfterMs: number
  ) {}

  private canAttempt(): boolean {
    if (this.state === "open" && Date.now() - this.openedAt > this.resetAfterMs) {
      this.state = "half-open";
    }
    return this.state !== "open";
  }

  private onSuccess(): void {
    this.failures = 0;
    this.state = "closed";
  }

  private onFailure(): void {
    this.failures += 1;
    if (this.failures >= this.threshold) {
      this.state = "open";
      this.openedAt = Date.now();
    }
  }

  async call<T>(fn: () => Promise<T>, fallback: () => T): Promise<Result<T>> {
    if (!this.canAttempt()) {
      return { ok: true, value: fallback() };
    }
    try {
      const value = await fn();
      this.onSuccess();
      return { ok: true, value };
    } catch (err) {
      this.onFailure();
      return { ok: true, value: fallback() };
    }
  }
}

async function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return Promise.race([
    promise,
    new Promise<T>((_, reject) =>
      setTimeout(() => reject(new Error("downstream call timed out")), ms)
    ),
  ]);
}

async function fetchPricing(orderId: string): Promise<{ total: number }> {
  const breaker = new CircuitBreaker(3, 5000);
  const result = await breaker.call(
    () => withTimeout(callPricingService(orderId), 200),
    () => ({ total: -1 })
  );
  return result.ok ? result.value : { total: -1 };
}

async function callPricingService(orderId: string): Promise<{ total: number }> {
  const res = await fetch(`http://pricing-service/orders/${orderId}/total`);
  if (!res.ok) throw new Error(`pricing service returned ${res.status}`);
  return res.json() as Promise<{ total: number }>;
}

async function main(): Promise<void> {
  const pricing = await fetchPricing("order-123");
  console.log(`resolved total: ${pricing.total}`);
}

main();
```

### Python

```python
import time
import random
from dataclasses import dataclass
from enum import Enum, auto


class BreakerState(Enum):
    CLOSED = auto()
    OPEN = auto()
    HALF_OPEN = auto()


@dataclass
class PricingResult:
    total: float
    from_fallback: bool


class CircuitBreaker:
    def __init__(self, threshold: int, reset_after_seconds: float) -> None:
        self.threshold = threshold
        self.reset_after_seconds = reset_after_seconds
        self.failures = 0
        self.state = BreakerState.CLOSED
        self.opened_at = 0.0

    def _can_attempt(self) -> bool:
        if self.state == BreakerState.OPEN:
            if time.monotonic() - self.opened_at > self.reset_after_seconds:
                self.state = BreakerState.HALF_OPEN
        return self.state != BreakerState.OPEN

    def _on_success(self) -> None:
        self.failures = 0
        self.state = BreakerState.CLOSED

    def _on_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.threshold:
            self.state = BreakerState.OPEN
            self.opened_at = time.monotonic()

    def call(self, fn, fallback):
        if not self._can_attempt():
            return fallback()
        try:
            value = fn()
            self._on_success()
            return value
        except Exception:
            self._on_failure()
            return fallback()


def call_pricing_service(order_id: str) -> float:
    # Simulated downstream call. Raises to model a flaky dependency.
    if random.random() < 0.4:
        raise ConnectionError("pricing service unavailable")
    return 42.50


def fetch_pricing(order_id: str, breaker: CircuitBreaker) -> PricingResult:
    value = breaker.call(
        fn=lambda: call_pricing_service(order_id),
        fallback=lambda: -1.0,
    )
    return PricingResult(total=value, from_fallback=value == -1.0)


def main() -> None:
    breaker = CircuitBreaker(threshold=3, reset_after_seconds=5.0)
    for i in range(6):
        result = fetch_pricing(f"order-{i}", breaker)
        print(f"order-{i} total={result.total} fallback={result.from_fallback}")


if __name__ == "__main__":
    main()
```

### Go

```go
package main

import (
	"errors"
	"fmt"
	"math/rand"
	"sync"
	"time"
)

type breakerState int

const (
	stateClosed breakerState = iota
	stateOpen
	stateHalfOpen
)

type circuitBreaker struct {
	mu         sync.Mutex
	threshold  int
	resetAfter time.Duration
	failures   int
	state      breakerState
	openedAt   time.Time
}

func newCircuitBreaker(threshold int, resetAfter time.Duration) *circuitBreaker {
	return &circuitBreaker{threshold: threshold, resetAfter: resetAfter, state: stateClosed}
}

func (b *circuitBreaker) canAttempt() bool {
	b.mu.Lock()
	defer b.mu.Unlock()
	if b.state == stateOpen && time.Since(b.openedAt) > b.resetAfter {
		b.state = stateHalfOpen
	}
	return b.state != stateOpen
}

func (b *circuitBreaker) onSuccess() {
	b.mu.Lock()
	defer b.mu.Unlock()
	b.failures = 0
	b.state = stateClosed
}

func (b *circuitBreaker) onFailure() {
	b.mu.Lock()
	defer b.mu.Unlock()
	b.failures++
	if b.failures >= b.threshold {
		b.state = stateOpen
		b.openedAt = time.Now()
	}
}

func (b *circuitBreaker) call(fn func() (float64, error), fallback func() float64) float64 {
	if !b.canAttempt() {
		return fallback()
	}
	value, err := fn()
	if err != nil {
		b.onFailure()
		return fallback()
	}
	b.onSuccess()
	return value
}

func callPricingService(orderID string) (float64, error) {
	if rand.Float64() < 0.4 {
		return 0, errors.New("pricing service unavailable")
	}
	return 42.50, nil
}

func fetchPricing(orderID string, b *circuitBreaker) float64 {
	return b.call(
		func() (float64, error) { return callPricingService(orderID) },
		func() float64 { return -1.0 },
	)
}

func main() {
	breaker := newCircuitBreaker(3, 5*time.Second)
	for i := 0; i < 6; i++ {
		orderID := fmt.Sprintf("order-%d", i)
		total := fetchPricing(orderID, breaker)
		fmt.Printf("%s total=%.2f\n", orderID, total)
	}
}
```

Java, Rust, and Swift are omitted from the runnable set for this entry.
Java's idiomatic equivalent would ordinarily use a library such as
Resilience4j rather than a hand-rolled breaker, and reproducing that
library's contract in raw Java would misrepresent how the pattern is
actually used in production Java code. The toolchain note in the template
records that `javac` was available to compile a hand-rolled version, but a
hand-rolled version was judged less representative than citing the standard
library-based idiom. Rust and Swift were skipped for the same reason. The
pattern's idiomatic shape in both languages leans heavily on an async
runtime and an HTTP client crate or framework respectively, and a minimal
from-scratch reproduction would teach the state machine already shown in
three other languages rather than teach anything language-specific about
Rust's or Swift's approach to the pattern.
