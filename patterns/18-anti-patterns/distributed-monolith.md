---
name: Distributed Monolith
slug: distributed-monolith
family: 18-anti-patterns
category: Architectural
aliases: [Distributed Big Ball of Mud, Monolith in Disguise, Fauxcroservices]
first_described: "Ben Christensen, Microservices Practitioner Summit, 2016 (informal name); Newman 2015/2021"
maturity: established
related: [big-ball-of-mud, bounded-context, shared-database, strangler-fig, saga, circuit-breaker]
incompatible_with: []
verified: 2026-08-02
---

# Distributed Monolith

## 1. Name, aliases, and lineage

A distributed monolith is a system built as a set of independently deployable
services that nonetheless cannot be deployed, scaled, tested, or run
independently in practice, because a synchronous call chain, a shared
database, or a shared library binds them into one release unit. It has every
network hop of a distributed system and every coupling problem of a monolith,
with the strengths of neither.

The term is used loosely by practitioners and has no single canonical paper.
The earliest documented public use of the exact phrase in the context of
service decomposition is from Ben Christensen, then at Netflix and later at
Facebook, speaking at the Microservices Practitioner Summit in 2016. InfoQ's
coverage reports that Christensen described a system where a service cannot
run unless a set of shared libraries is also available on every caller, and
that he called this shape a distributed monolith, spreading the code of a
monolith across a network while paying the network's costs and forfeiting the
independence microservices are meant to buy (InfoQ, `Services or Objects,
Distributed Monoliths, and Untangling Deployment from Release`,
https://www.infoq.com/news/2016/02/services-distributed-monolith/, verified
2026-08-02). Community discussion around the same period traces informal use
of the phrase back further still, with no single credited coiner, which is
consistent with the concept describing a failure mode practitioners kept
independently rediscovering rather than a design invented and named once.

Two bodies of earlier work describe the same failure without using the phrase,
and both are worth citing because they explain why the shape recurs.

Sam Newman's *Building Microservices*, the reference text most engineers point
to when this anti-pattern comes up, describes the underlying causes directly.
A shared database read and written by more than one service creates coupling
at the schema level that no amount of service boundary drawing removes, and a
synchronous request chain across services reproduces the call-stack coupling
of a monolith while adding network latency and partial failure on top (Sam
Newman, *Building Microservices*, 2nd edition, O'Reilly, 2021, chapter 4,
`Splitting the Monolith`, and chapter 11, `Testing`). Martin Fowler's essay
`MonolithFirst` makes the companion observation from the other direction,
that almost every microservice system he had heard of that started as
microservices from day one ran into serious trouble, because service
boundaries drawn before the domain is understood tend to be wrong, and wrong
boundaries force cross-service calls that would have been in-process function
calls in a well-modularised monolith (Martin Fowler, `MonolithFirst`,
https://martinfowler.com/bliki/MonolithFirst.html, verified 2026-08-02. "You
cannot assume that you can take an arbitrary system and break it into
microservices. Most systems acquire too many dependencies between their
modules, and thus can't be sensibly broken apart.").

A distributed monolith is therefore best understood as a specific, well
attested consequence of two separate design mistakes converging. Drawing
service boundaries along the wrong seam, and choosing synchronous or
shared-state communication across those boundaries once drawn. The name
Fauxcroservices appears in developer commentary as a deliberately mocking
label for the same shape, services in name, monolith in behaviour. Distributed
Big Ball of Mud is the more precise technical alias, because it points at the
lineage in dimension 13, this anti-pattern relates to a well known code-level
anti-pattern in the same way a network diagram relates to a class diagram.

## 2. Problem and context

A team decomposes a monolith, or designs a new system, into a set of services
with separate repositories, separate deployment pipelines, and separate
runtime processes, expecting the standard microservices payoff, independent
deployability, independent scaling, and fault isolation. Months later the team
discovers that a change to one service still requires coordinated deployment
of three or four others, that a single slow database query in one service
degrades response time across the whole system, and that an integration test
suite has to boot the entire constellation of services to pass, because no
individual service can be verified in isolation.

The context in which this happens is specific and recognisable. The team drew
service boundaries around technical layers, a data-access service, a
business-logic service, a presentation service, rather than around business
capabilities. Or the team drew boundaries correctly on paper but connected the
resulting services with synchronous HTTP or RPC calls arranged in a chain, so
that handling one user request requires service A to call B, which calls C,
which calls D, and any one of the four being slow or down fails the whole
request. Or the team shares one relational database across several services,
so that a schema migration in one service can silently break a query in
another that nobody remembers depends on that table. Or the team extracts a
shared library, often a domain model or a validation library, and every
service pins a version of it, so a bug fix in the library requires a
coordinated release of every service that consumes it.

None of these decisions looks wrong locally. Reusing a validation library
feels responsible. Calling a service synchronously so the caller can react to
the result feels correct. Sharing one production database avoids the
duplication a service-owned database would require. Each choice is a small,
reasonable step, and the distributed monolith is what those small, reasonable
steps sum to when nobody is watching the whole system's coupling.

## 3. Forces

This entry describes an anti-pattern, so the forces below are named to explain
why systems drift into this shape rather than to justify choosing it.

- **Familiarity versus new discipline.** A team fluent in monolithic,
  in-process design reaches for a synchronous call and a shared table because
  those are the tools it already trusts, and distributed-systems discipline,
  idempotent retries, eventual consistency, contract testing, has to be learned
  deliberately. The path of least resistance recreates the monolith's
  programming model over a network.
- **Perceived simplicity versus actual coupling.** A synchronous call chain is
  easy to reason about for a single happy-path request and hides its coupling
  cost until a downstream service is slow, at which point the cost surfaces as
  latency and cascading failure rather than as a compile error, so the
  feedback arrives late and expensively.
- **Short-term velocity versus long-term independence.** Sharing a database or
  a library across two services is faster to build the first time than
  building the duplicated data store or the versioned contract that
  independence requires, and the true cost only shows up on the second and
  third change, when the coupling has to be paid down under production
  pressure rather than designed away calmly.
- **Organisational boundaries versus service boundaries.** Conway's Law
  predicts that the shape of communication in an organisation shows up in the
  shape of the system it builds. A team split by technical layer, one team on
  the database, one on the API, one on the frontend, tends to produce services
  split the same way, which is precisely the layered decomposition that
  forces cross-service chatter for every business operation. Fixing the
  services without fixing the team structure tends to regress.
- **Operational cost versus development cost.** Real independence, a database
  per service, asynchronous messaging, contract-tested APIs, costs more to
  build and to operate, more infrastructure, more moving parts, more places a
  message can get stuck. The distributed monolith is in part what happens
  when a team pays the deployment overhead of many services without paying
  the design overhead that would make many services worth it.

## 4. Applicability and non-applicability

A distributed monolith is an anti-pattern. It has no applicability list in the
sense the other entries in this repository carry, because nobody sets out to
build one on purpose. What belongs here instead is the boundary between a
genuine, still-forming distributed system and one that has already tipped
into this failure mode, because the two are easy to confuse from the inside.

Not yet a distributed monolith, still a normal stage of building a distributed
system.

- Two services share a small, stable, rarely-changing contract and version
  it explicitly. Coupling to a versioned contract is not the same coupling
  as an unversioned shared library, see dimension 8.
- A synchronous call exists at a genuine request-response boundary where the
  caller truly needs an immediate answer, is protected by a timeout and a
  circuit breaker, and does not sit in a chain longer than two hops.
- Two services temporarily share infrastructure, a queue, a cache, during a
  migration, with an explicit plan and date to split it, tracked as technical
  debt rather than accepted as permanent.
- A new system is deliberately built as a modular monolith first, with clean
  internal module boundaries and no shared mutable state between modules,
  as a staging ground for extraction later. Fowler's MonolithFirst argument
  from dimension 1 describes exactly this as the sound path.

Already a distributed monolith, the anti-pattern is present.

- No service can be deployed without also deploying at least one other
  service in the same release, because of a shared database schema, a shared
  library version pin, or an implicit ordering requirement between rollouts.
- A single integration test suite has to boot every service to pass, and no
  individual service has a test suite that exercises its own contract against
  a fake or a stub of its collaborators.
- A request to the system as a whole routinely traverses four or more
  synchronous hops, and a slow or failing service anywhere in that chain
  degrades or fails requests that have nothing to do with that service's
  actual responsibility.
- Two or more services read and write the same tables in the same database,
  and a schema change in one service has broken another service's queries at
  least once already.
- The services were split along a technical layer, controllers in one
  service, business rules in another, persistence in a third, rather than
  along a business capability, so that almost every user-facing feature
  requires a change that touches all three services in lockstep.

The presence of one item from the second list is a warning. The presence of
several, especially the lockstep deployment symptom, means the system has
already arrived.

## 5. Structure

A distributed monolith has no canonical structure in the way a design pattern
does, because it is a failure mode rather than a design, but the shape it
takes is consistent enough to name its recurring participants.

- **Nominal service boundary.** A repository, a deployment pipeline, and a
  running process exist per service, so the system looks decomposed from the
  outside, in an architecture diagram or a list of deployables.
- **Hidden coupling channel.** The actual binding force that removes
  independence. In practice this is almost always one of three things, a
  shared mutable database, a synchronous call chain with no isolation, or a
  shared library that every service must upgrade in lockstep. A given
  distributed monolith commonly exhibits more than one of these at once.
- **Coordinated release unit.** The real, unacknowledged deployable is not
  any single service but the set of services that the hidden coupling channel
  forces to move together. This unit is invisible in the org chart and the
  repository list, and becomes visible only through outage postmortems and
  release runbooks that say things like deploy service B before service A.
- **Cross-cutting failure domain.** Because requests traverse the coupling
  channel, an incident in one nominal service propagates to the availability
  and latency of others that share the channel, so the actual failure domain
  is again the coordinated release unit, not any individual service.

## 6. ASCII structure diagram

```
  What the org chart and the deploy list show, five independent services

   +----------+   +----------+   +----------+   +----------+   +----------+
   | Service  |   | Service  |   | Service  |   | Service  |   | Service  |
   |    A     |   |    B     |   |    C     |   |    D     |   |    E     |
   +----------+   +----------+   +----------+   +----------+   +----------+

  What the coupling channel actually forces at deploy time

   +------------------------------------------------------------------+
   |                    ACTUAL COORDINATED RELEASE UNIT                |
   |                                                                    |
   |   +----------+  sync call  +----------+  sync call  +----------+  |
   |   | Service  | ----------> | Service  | ----------> | Service  |  |
   |   |    A     |             |    B     |             |    C     |  |
   |   +----------+             +----------+             +----------+  |
   |        |                        |                        |        |
   |        |     shared library v3.4.1, pinned everywhere    |        |
   |        +------------------------+------------------------+        |
   |                                 |                                 |
   |                        +----------------+                         |
   |                        |  shared table  |  Service D reads and    |
   |                        |    "orders"    |  writes it too          |
   |                        +----------------+                         |
   |                                 ^                                 |
   |                                 |                                 |
   |                          +----------+                             |
   |                          | Service  |                             |
   |                          |    D     |                             |
   |                          +----------+                             |
   +------------------------------------------------------------------+

   Service E has no shared channel with the rest and is the only one of the
   five that is genuinely independently deployable.
```

## 7. Dynamics

The runtime behaviour that reveals a distributed monolith is a request that
crosses the coupling channel and pays for every hop it did not need to make.
The sequence below shows a single user request degrading because of an
unrelated slowdown three hops away, the pattern that most often triggers the
postmortem that finally names the anti-pattern out loud.

```
Client        Service A        Service B        Service C        Shared DB
  |               |                |                |                |
  |-- POST /order->|                |                |                |
  |               |-- sync call -->|                |                |
  |               |  (no timeout)  |                |                |
  |               |                |-- sync call -->|                |
  |               |                |  (no timeout)  |                |
  |               |                |                |-- slow query ->|
  |               |                |                |   (contention  |
  |               |                |                |    from        |
  |               |                |                |    Service D)  |
  |               |                |                |<-- 4200 ms ----|
  |               |                |<-- 4200 ms ----|                |
  |               |<-- 4200 ms ----|                |                |
  |<-- 4200 ms ---|                |                |                |
  |  (timeout at  |                |                |                |
  |   5000 ms,    |                |                |                |
  |   barely      |                |                |                |
  |   survives)   |                |                |                |
  |               |                |                |                |
  |  A thousand concurrent requests like this one exhaust Service A's|
  |  thread pool while waiting on Service C, so unrelated endpoints  |
  |  on Service A start failing too, even though Service A's own code|
  |  did nothing wrong.                                              |
```

Deploy-time dynamics show the same coupling from a different angle. A schema
migration to the shared "orders" table forces this ordering, which a release
runbook eventually has to document by hand because nothing in the system
enforces it.

```
1. Freeze deploys of Service B, Service C, and Service D.
2. Deploy the migration that adds a nullable column to "orders".
3. Deploy Service D first, because it is the only service that both reads
   and writes the new column and must tolerate the old and new shape during
   rollout.
4. Deploy Service C, which starts reading the new column.
5. Deploy Service B last, because Service B's shared-library version pin was
   bumped to the version that assumes the column exists.
6. Un-freeze. If any step failed, roll back in reverse order or the schema
   and the code disagree.
```

## 8. Implementation variants

The distributed monolith is not a variant-carrying design pattern, but it
reliably appears in a small number of recognisable shapes, and naming them
helps a team recognise which one it is looking at.

**The shared-database variant.** Two or more services connect to the same
schema. This is the variant Chris Richardson's microservices pattern language
treats as the load-bearing counter-example, arguing that a Database per
Service is what actually decouples services, because a shared database means
a schema change in one service can silently break another, and it becomes
impossible to enforce that a service's persistence details are private to
that service (Chris Richardson, microservices.io, `Pattern. Shared database`,
https://microservices.io/patterns/data/shared-database.html, verified
2026-08-02).

**The synchronous call-chain variant.** Services communicate exclusively
through blocking request-response calls arranged so that handling one
business operation requires a chain of several hops, none of them protected
by a circuit breaker or a sensible timeout. Microsoft's Azure Architecture
Center documents the trade-off directly, that synchronous APIs require the
downstream service to be available or the operation fails, and that a chain
of service dependencies compounds latency and failure probability with every
added hop (Microsoft, `Interservice communication in microservices`, Azure
Architecture Center,
https://learn.microsoft.com/en-us/azure/architecture/microservices/design/interservice-communication,
verified 2026-08-02).

**The shared-library variant.** Business logic, a domain model, or validation
rules live in a library that every service imports and pins to a specific
version, so a change to the shared logic requires every consuming service to
bump its dependency and redeploy before the change takes effect everywhere.
This is the exact shape Ben Christensen named in dimension 1, a service that
cannot run correctly unless a particular version of a shared library is also
present.

**The layered-decomposition variant.** Services are split by technical
concern, an API layer service, a business logic service, a data access
service, rather than by business capability. Every feature then requires a
coordinated change across all three, which is functionally identical to a
layered monolith with the layers moved into separate processes and given
network calls in place of function calls. Sam Newman calls this splitting the
wrong way and contrasts it directly with splitting by business capability
(Sam Newman, *Building Microservices*, 2nd edition, O'Reilly, 2021, chapter
4).

**The event-driven variant that still couples.** A team adopts asynchronous
messaging, expecting it to remove coupling by itself, but publishes fine
grained internal events that encode implementation details, so a consumer
still has to understand the producer's internal model to react correctly, and
a change to the producer's internals still breaks consumers even though no
synchronous call exists. This is a subtler distributed monolith, because the
transport layer looks decoupled while the data contract is not, and it is
covered further in dimension 11.

## 9. Known production uses

Distributed monolith is an anti-pattern, so its known instances are companies
publicly describing how they fell into it and, in two of the three cases
below, what they did to climb back out. Naming the failure with a real system
and a real source is the honest version of dimension 9 for this family.

**Segment's 140-plus microservice architecture, publicly retired in 2018.**
Segment built one microservice per third-party destination integration,
reaching over 140 services. The team's own postmortem describes the exact
distributed monolith symptoms, dependency version divergence across shared
libraries that were supposed to be reusable, deployment complexity that
required touching every service to change shared code, and operational
overhead that grew linearly with every added service rather than staying flat.
The team consolidated the 140-plus services back into a single service
handling all destinations, restoring the ability to deploy and test as one
unit (Segment engineering blog, published on the Twilio blog, `Goodbye
Microservices. From 100+ Problem Children to 1 Superstar`,
https://www.twilio.com/en-us/blog/developers/best-practices/goodbye-microservices/,
verified 2026-08-02. "Testing and deploying changes to these shared libraries
impacted all of our destinations. It began to require considerable time and
effort to maintain.").

**Ben Christensen's account of the Netflix and broader industry pattern,
2016.** Speaking at the Microservices Practitioner Summit, Christensen
described systems where a service could not interact within the wider system
unless a set of shared libraries was present on the caller too, which he
named a distributed monolith and characterised as paying network cost while
gaining none of the isolation benefit of microservices. InfoQ's report frames
this as a pattern Christensen observed recurring across teams, not a
one-off incident (InfoQ, `Services or Objects, Distributed Monoliths, and
Untangling Deployment from Release`,
https://www.infoq.com/news/2016/02/services-distributed-monolith/, verified
2026-08-02).

**Deliveroo's early microservices decomposition, reported by InfoQ in
2017.** Coverage of a talk by Deliveroo engineers describes a system that
started splitting a Rails monolith into services and, in the early stages, hit
tightly coupled synchronous chains between the newly separated services,
because the boundaries had been drawn without first understanding where the
domain actually separated cleanly, echoing the same MonolithFirst warning
from dimension 1 (InfoQ, `How Deliveroo Moved from a Monolith to Microservices
and What They Learned`, https://www.infoq.com/news/2017/03/deliveroo-monolith-distributed,
verified 2026-08-02).

## 10. Consequences

Because this is an anti-pattern, its consequences are overwhelmingly negative,
and the entry treats them as the load-bearing content rather than balancing
them against invented positives.

Negative.

- Deployments require coordination across services that were supposed to be
  independently deployable, which reintroduces the release-train problem
  microservices were adopted to avoid, and does so with more moving parts and
  more places for the coordination to fail than a single monolithic release.
- A slowdown or an outage in one service propagates through synchronous call
  chains or shared infrastructure and degrades services that have no logical
  relationship to the failing one, so the system's actual availability is
  bounded by its least reliable component multiplied across every hop in the
  chain, not by any individual service's own reliability.
- Testing requires standing up the whole constellation of services to verify
  behaviour that should have been verifiable against a single service and a
  contract, which slows the feedback loop that automated testing exists to
  shorten and pushes teams toward manual, end-to-end verification instead.
- Operational overhead scales with the number of services rather than with
  genuine business complexity, because every service still needs its own
  deployment pipeline, its own monitoring, and its own on-call rotation, while
  delivering none of the independent-scaling or independent-ownership benefit
  that would justify that overhead.
- Teams lose the ability to reason locally about a service's behaviour,
  because correctness depends on the state or the version of other services
  that the team does not own, which erodes the team-autonomy argument that
  is usually the actual business reason an organisation adopted microservices
  in the first place.
- The false appearance of decomposition delays the fix. A monolith's coupling
  is visible in one codebase and gets noticed. A distributed monolith's
  coupling is spread across repositories, teams, and deployment pipelines, and
  frequently is not recognised as a single problem until an incident
  postmortem connects the dots.

Positive, stated honestly and narrowly.

- Recognising the pattern is itself valuable, because it gives a team a name
  for a diffuse pain they were otherwise attributing to individual services
  being badly built, when the actual cause is the coupling channel between
  them.
- The transitional state is sometimes an acceptable, temporary waypoint on
  the way to a genuinely decoupled system, provided the team tracks it as debt
  with an explicit plan, per the applicability boundary in dimension 4, rather
  than mistaking the waypoint for the destination.

## 11. Failure modes and misuse

**Cascading latency from an unprotected synchronous chain.** Symptom. A
single slow dependency several hops deep causes timeouts and thread pool
exhaustion in services that never call the slow dependency directly, and the
incident dashboard shows elevated error rates across the board with no single
obvious root cause. Cause. Synchronous calls with no timeout, no circuit
breaker, and no bulkhead isolating the caller's own resources from the
callee's slowness. Fix. Add explicit timeouts and a circuit breaker at every
synchronous boundary, per the Circuit Breaker entry, and consider converting
the chain to asynchronous messaging where the caller does not need an
immediate answer.

**Schema coupling through a shared database.** Symptom. A migration in one
service's codebase breaks a query written by a different team in a different
service, discovered only when that other service starts throwing errors in
production, because nothing in either codebase declared the dependency.
Cause. Two or more services read or write the same tables directly rather than
through the owning service's API. Fix. Assign clear ownership of every table
to exactly one service, migrate other services to call that service's API
instead of querying its tables, and use the Database per Service pattern
going forward, per Richardson's shared-database write-up cited in dimension 8.

**Lockstep releases hidden behind independent-looking pipelines.** Symptom.
A runbook exists, written by hand, that says deploy service X before service
Y, or the team has learned through repeated incidents to always deploy two or
three specific services together even though nothing in the tooling enforces
it. Cause. An implicit version or ordering dependency between services,
usually from a shared library pin or an API contract change that was not
made backward compatible. Fix. Version APIs explicitly and support at least
one prior version during rollout, and treat any discovered lockstep
requirement as an incident worth its own postmortem, not a known quirk to
work around forever.

**Chatty decomposition along technical layers.** Symptom. Almost every
feature ticket touches three or four services in a fixed order, controller
service, then business-rule service, then persistence service, and a
developer estimating a small feature routinely has to coordinate across three
teams to ship it. Cause. Services were split by technical layer instead of by
business capability. Fix. Re-draw the boundaries around a business
capability or a bounded context, per Newman's guidance in dimension 8 and the
Bounded Context entry, so that one service owns a complete vertical slice of
behaviour and rarely needs a synchronous partner to finish a request.

**Fine-grained event payloads that still leak the producer's internal
model.** Symptom. A consumer service breaks whenever the producer changes an
internal field, even though the two communicate only through an event bus
and no synchronous call exists between them, so the team is confused why
supposedly decoupled messaging still produced tight coupling. Cause. The
event schema mirrors the producer's internal representation rather than a
deliberately designed, versioned public contract, so every internal refactor
is also a breaking public API change. Fix. Design event schemas as an
explicit public contract, separate from internal representations, version
them, and treat a breaking schema change with the same discipline as a
breaking REST API change.

**Mistaking the symptom for the disease and adding more services.** Symptom.
A team responds to the pain of a distributed monolith by splitting the
already-too-fine-grained services further, hoping smaller services will be
more independent, and operational overhead climbs while the coupling
symptoms persist unchanged, because the coupling channel, the shared database
or the synchronous chain, was never addressed. Cause. Treating service count
as the metric to optimise rather than coupling. Fix. Diagnose which coupling
channel from dimension 8 is actually present before changing service
boundaries again, and consider consolidation, as Segment did in dimension 9,
when the honest diagnosis is that the services were split too finely for the
team's ability to keep them decoupled.

## 12. Trade-off matrix

The comparison below is not between a distributed monolith and alternative
architectures in the usual sense, since nobody chooses this shape on purpose.
It compares the recognisable end states a team can deliberately choose
instead, once it has diagnosed itself as living inside a distributed
monolith, across the forces named in dimension 3.

| Force | Distributed monolith (current state) | Modular monolith | Microservices decomposed by business capability with asynchronous messaging | Strangler Fig migration in progress |
|---|---|---|---|---|
| Independent deployability | None in practice, despite separate pipelines | None, single deployable by design, but internal boundaries are clean | High, each service ships on its own schedule | Partial, growing as modules are extracted |
| Blast radius of a slow dependency | Large, propagates across synchronous chains | Contained to a process crash or a slow request inside one deploy | Bounded, asynchronous messaging isolates a slow consumer from the producer | Mixed, legacy and extracted parts have different blast radii |
| Operational overhead | High, many services, no independence to show for it | Low, one thing to deploy and monitor | Moderate to high, but proportional to genuine scaling need | Moderate, running two systems side by side temporarily |
| Test feedback loop | Slow, full constellation required to verify anything | Fast, in-process integration tests | Fast per service, contract tests replace end-to-end runs | Slow during the transition, improves as it completes |
| Schema and contract discipline required | Low, which is the root cause | Low, compiler enforces module boundaries | High, versioned APIs and event schemas required | Growing, the facade layer forces contract discipline early |
| Suitable team size and maturity | Not a deliberate choice, an accident | Small teams, teams new to service decomposition | Multiple autonomous teams with distributed-systems experience | Any team migrating a monolith with domain uncertainty |
| Cost to fix once diagnosed | This is the state being fixed | Cheap starting point, cited as the sound default by Fowler | Correct end state if boundaries and independence are genuinely needed | The recommended path from monolith or distributed monolith to microservices |

Reading of the table. The distributed monolith loses on every force that
matters, deployability, blast radius, feedback loop speed, because it pays
the structural cost of distribution without the discipline that would earn
that cost back. A modular monolith is usually the cheaper and more honest
choice when a team cannot yet commit to the contract and schema discipline
microservices require. A Strangler Fig migration is the recommended way to
move from either a plain monolith or an already-diagnosed distributed
monolith toward a genuinely decoupled architecture, because it forces the
facade and contract discipline to exist before extraction is declared
finished.

## 13. Related and incompatible patterns

- **Big Ball of Mud.** The direct lineage. A distributed monolith is what a
  Big Ball of Mud looks like once its tangled internals have been physically
  spread across separate processes and repositories without untangling the
  dependencies first. The coordination costs of a distributed system are
  added on top of the coupling costs of an unstructured one, rather than
  either being solved.
- **Bounded Context.** The corrective concept. Drawing service boundaries
  around a bounded context, in the Domain-Driven Design sense, is the design
  discipline that, applied before extraction, prevents the layered and
  chatty decomposition variant described in dimension 8. A service whose
  boundary matches a bounded context rarely needs a synchronous partner to
  complete a request.
- **Shared Database.** The anti-pattern this entry's shared-database variant
  is built on. Database per Service is the corrective pattern, and choosing a
  shared database deliberately, as an interim measure with an extraction plan,
  is the boundary case discussed in dimension 4.
- **Strangler Fig.** The standard remediation path. A Strangler Fig migration
  extracts capability incrementally behind a facade, forcing an explicit,
  versioned contract to exist at the extraction boundary from day one, which
  is precisely the discipline a distributed monolith lacks. Teams that have
  diagnosed themselves as living in a distributed monolith typically use a
  Strangler Fig approach in reverse, consolidating or re-drawing boundaries
  behind a facade rather than extracting further.
- **Saga.** Composes with the fix, not the problem. Once synchronous chains
  are replaced with asynchronous messaging to remove cascading failure, a
  multi-step business transaction that used to be a synchronous call chain
  needs an explicit coordination pattern to preserve consistency, and Saga is
  that pattern. Adopting Saga without first fixing the underlying coupling
  channel does not resolve a distributed monolith, it only changes which
  coupling mechanism carries the same tight dependency.
- **Circuit Breaker.** A tactical mitigation, not a cure. A circuit breaker at
  every synchronous boundary reduces the blast radius described in dimension
  11 and buys time, but it does not remove the underlying coupling, a service
  behind an open circuit breaker still cannot complete its work, it merely
  fails fast and predictably instead of slowly and unpredictably.
- **Monolith First.** Actively compatible as a preventive strategy rather
  than a remediation. Fowler's argument, cited in dimension 1, is that
  building a well modularised monolith first and extracting services once
  boundaries are proven by real usage avoids ever entering the distributed
  monolith state, because the boundaries are drawn with domain knowledge the
  team did not have on day one.

## 14. Refactoring path in and out

There is no path in to author deliberately, since this is an anti-pattern
that a team arrives at rather than designs. What belongs here is the honest
diagnostic and remediation path a team follows once it recognises the state
described in dimension 4.

Diagnosing whether the system has become a distributed monolith.

1. List every service and, for each pair of services, note whether a
   deployment of one has ever required a coordinated deployment of the other
   within the last quarter. A yes answer on any pair is the strongest single
   signal.
2. For each service, check whether its own automated test suite can pass
   against a stub or a contract test of its collaborators, without booting
   the collaborators themselves. If the answer is no for most services, the
   test-isolation symptom from dimension 4 is present.
3. Trace the longest synchronous call chain a single user-facing request can
   trigger. Count the hops. Four or more synchronous hops with no circuit
   breaker at each is a strong signal, per dimension 11.
4. List every table in every shared database instance and, for each table,
   name the services that read or write it directly, not through an API.
   More than one writer to the same table is the shared-database variant from
   dimension 8.
5. Check whether any internal library is version-pinned identically across
   every service and whether a bug fix to that library has ever required
   coordinated redeployment of more than two services to take effect.

Remediating a diagnosed distributed monolith, in order.

1. Pick the coupling channel causing the most incident pain first, usually
   the synchronous chain if outages are the presenting symptom, or the shared
   database if schema breakage is the presenting symptom. Fixing every
   channel at once is rarely tractable, so sequence the work by measured
   incident cost.
2. For a synchronous-chain problem, introduce a timeout and a circuit breaker
   at every hop immediately, as a stabilising step, then identify which hops
   genuinely need a synchronous answer and which can become asynchronous
   messages, converting the latter first since they carry the least risk.
3. For a shared-database problem, assign single ownership of each table to
   one service, then migrate other services' direct queries to calls against
   the owning service's API one table at a time, verified by contract tests
   before the direct query is removed.
4. For a shared-library problem, extract the parts of the library that
   represent a genuine shared contract into a versioned, published package
   with an explicit deprecation policy, and inline or duplicate the parts
   that were actually business logic specific to one service, since sharing
   business logic across service boundaries is usually the layered-
   decomposition mistake from dimension 8 in disguise.
5. For a layered-decomposition problem, this is the deepest fix and the one
   most likely to require re-drawing service boundaries entirely around
   business capabilities or bounded contexts, following the Strangler Fig
   approach so the re-decomposition can happen incrementally behind a stable
   facade rather than as a risky big-bang rewrite.
6. If the diagnosis, honestly made, is that the team lacks the operational
   maturity or the genuine scaling need to sustain the number of services it
   currently runs, consolidation is a legitimate outcome, not a failure,
   exactly as Segment's postmortem in dimension 9 describes. Merge services
   back where the coupling cost consistently exceeds the independence
   benefit.

## 15. Testing and verification

Testing a system that has already become a distributed monolith is
characteristically hard in exactly the way dimension 10 describes, and the
techniques below are both diagnostic, they reveal how deep the coupling goes,
and remedial, applying them forces the contract discipline that fixes the
underlying problem.

Harder because of the anti-pattern.

- End-to-end tests become the only tests that reliably catch integration
  bugs, because unit and component tests cannot exercise the shared database
  or the synchronous chain in isolation, which makes the test suite slow and
  brittle in exactly the way independent, per-service testing was supposed to
  avoid.
- A change confined to one service's internals routinely breaks a test in a
  different service's suite, which is itself a diagnostic signal, a
  well-isolated service's tests should never depend on another service's
  internal behaviour.
- Flaky tests proliferate, because tests that boot several real services
  inherit every one of those services' own flakiness, timing sensitivity, and
  external dependencies.

Techniques that both diagnose and remediate.

- **Consumer-driven contract testing.** Each consumer of a service publishes
  the contract it depends on, and the provider service runs those contracts
  in its own pipeline before deploying. This directly replaces the need to
  boot the whole constellation to catch a breaking change, and a team that
  cannot write a consumer-driven contract for a given dependency has just
  located an undocumented coupling worth investigating.
- **Schema migration tests against a shared table.** Before removing direct
  cross-service table access, add a test that runs every known consuming
  service's queries against the target schema before a migration ships, which
  both catches breakage early and produces the ownership map dimension 14
  step 3 needs.
- **Chaos or fault-injection testing on synchronous chains.** Deliberately
  inject latency or failure into one service in a staging environment and
  observe which unrelated services degrade. A distributed monolith reveals
  itself here as a wide blast radius, and this test doubles as the
  verification that a circuit breaker introduced in remediation actually
  contains the failure once fixed.
- **Deployment-order tests.** Where a lockstep deployment requirement is
  suspected, script the deployment order in a staging pipeline and assert
  that deploying services out of the suspected order does not cause errors.
  A failure here converts a folklore runbook into a documented, testable
  dependency, which is the first step toward removing it.

## 16. Observability signals

A distributed monolith hides in plain sight in most dashboards, because each
service's own metrics look individually fine while the coupling channel is
where the actual problem lives. The signals below are chosen specifically to
surface the coupling rather than any one service's health.

What to record.

- Cross-service call latency and error rate, broken down by the calling
  service and the called service as a pair, not aggregated per service alone,
  so a chain's weakest hop is visible directly rather than averaged away.
- Distributed traces spanning the full request path, with span boundaries at
  every service hop, so the longest synchronous chain from dimension 14 step
  3 can be measured from real traffic rather than estimated by reading code.
- Deployment correlation, a log or a dashboard panel showing deployments of
  every service on a shared timeline, so a human reviewing an incident can
  see at a glance whether two services were deployed close together, which is
  the cheapest way to surface an undocumented lockstep dependency.
- Database connection and query attribution by calling service, where a
  database is shared, so that queries against a table can be traced back to
  which service issued them, surfacing undeclared readers and writers.
- Circuit breaker state transitions per dependency, open, half-open, closed,
  which reveals both how often a downstream dependency is unhealthy and, more
  importantly for this anti-pattern, how many upstream services share that
  same circuit, showing the blast radius directly.

A healthy instance on a dashboard, once the coupling has been addressed. Per
pair latency is stable and each hop's error rate reflects only that hop's own
dependencies. Distributed traces show request paths of two or three hops for
most operations, not four or more. Deployments happen on independent
schedules with no visible clustering. Circuit breakers open rarely and in
isolation, one dependency at a time, never cascading into a second breaker
tripping because the first one's caller was itself overloaded.

A failing, still-distributed-monolith instance. Per pair latency for one hop
spikes and the error rate for two or three unrelated downstream services
spikes within the same minute. Traces regularly show four-plus hop chains for
ordinary requests. The deployment timeline shows the same cluster of two or
three services deploying together, release after release, with no ticket
that says why. A single circuit breaker opening is immediately followed by a
second, unrelated breaker opening a few seconds later, which is the traced
signature of the cascading failure described in dimension 7.

## 17. Security and privacy implications

The distributed monolith's security implications follow directly from its
structural properties rather than from anything specific to the code inside
any one service, and they are genuine, not invented for completeness.

**Expanded attack surface with monolithic blast radius.** Splitting a system
into services multiplies the number of network endpoints, authentication
checkpoints, and inter-service credentials that must be secured, which is a
real cost of any microservices decomposition. A distributed monolith pays
this full cost while still failing as one unit when any single hop is
compromised, because a synchronous chain with no isolation between hops means
a credential or a request forged at one service can reach every service
downstream of it in the chain with the same trust level the legitimate caller
had. The Azure Architecture Center's coverage of interservice communication,
cited in dimension 8, recommends mutual TLS authentication between services
specifically because the network between services is not inherently trusted,
a recommendation that matters more, not less, once a distributed monolith's
chains routinely span four or more hops.

**Shared database as a single point of data exposure.** When several
services connect to one database, a single compromised database credential,
or a single SQL injection vulnerability in any one of the connecting
services, exposes the data of every service sharing that database, not only
the data the vulnerable service itself owns. A properly decoupled system with
one database per service contains a credential compromise to that one
service's data. The shared-database variant of the distributed monolith turns
a local vulnerability into a systemic one.

**Coordinated deploys widen the window for a bad rollback.** A lockstep
deployment requirement means a security patch to one service cannot ship
alone if it depends on a version bump in a shared library or a schema change
elsewhere, which delays the patch behind the coordination overhead described
in dimension 10, and a delayed patch is exposure time. Teams that have
diagnosed a distributed monolith should treat the delay this coupling adds to
security patch rollout as an explicit risk to track, not only an efficiency
complaint.

**Data residency and cross-boundary logging.** Distributed tracing, one of
the observability signals recommended in dimension 16, propagates
correlation identifiers and often request metadata across every hop in a
chain. Where different services in the chain operate under different data
residency or retention requirements, for instance because one service was
extracted for a specific regulatory reason, a trace or a log field that
crosses that boundary without redaction can leak data outside its intended
jurisdiction. This is a general distributed-tracing caution and not unique to
this anti-pattern, but the longer chains typical of a distributed monolith
increase the number of boundaries a trace crosses and therefore the number of
places this can go wrong.

## Code examples

Three languages, chosen to show the anti-pattern's runtime signature rather
than to show three different implementations of the same feature, since a
distributed monolith is a property of how services are wired together, not a
type of code any one service contains. Each example is runnable and each one
prints output demonstrating the coupling failure, followed by a corrected
version demonstrating the fix, so the difference is observable rather than
asserted. Go is omitted because the pattern being demonstrated is identical
in shape across languages, three faithful renditions of the same latency
cascade would add length without adding a distinct lesson, and the three
languages chosen already span a compiled, a scripted, and a typed-scripted
environment.

### Python

Simulates the cascading-latency dynamics from dimension 7. Three in-process
functions stand in for three network services connected synchronously with no
timeout, then the same chain with a timeout and a circuit breaker applied.

```python
import time


class CircuitOpen(Exception):
    pass


class CircuitBreaker:
    def __init__(self, failure_threshold=2, cooldown_seconds=5.0):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.failures = 0
        self.opened_at = None

    def call(self, fn, timeout_seconds):
        if self.opened_at is not None:
            if time.monotonic() - self.opened_at < self.cooldown_seconds:
                raise CircuitOpen("circuit open, failing fast")
            self.opened_at = None
            self.failures = 0
        start = time.monotonic()
        result = fn()
        elapsed = time.monotonic() - start
        if elapsed > timeout_seconds:
            self.failures += 1
            if self.failures >= self.failure_threshold:
                self.opened_at = time.monotonic()
            raise TimeoutError(f"call exceeded {timeout_seconds}s, took {elapsed:.2f}s")
        return result


def service_c_slow_query():
    time.sleep(0.30)
    return "order-42"


def service_b_calls_c_no_isolation():
    return service_c_slow_query()


def service_a_calls_b_no_isolation():
    return service_b_calls_c_no_isolation()


def unrelated_endpoint_on_service_a():
    return "health check ok"


def demo_coupled_chain():
    print("Coupled chain, no timeout, no circuit breaker.")
    start = time.monotonic()
    result = service_a_calls_b_no_isolation()
    elapsed = time.monotonic() - start
    print(f"  order request took {elapsed:.2f}s, result={result}")
    print("  Service A's thread is blocked for the full 0.30s even though")
    print("  the slow work happened three hops away in Service C.")


def demo_isolated_chain():
    print("\nSame chain with a timeout and a circuit breaker on A to B.")
    breaker = CircuitBreaker(failure_threshold=1, cooldown_seconds=1.0)
    for attempt in range(1, 3):
        try:
            breaker.call(service_b_calls_c_no_isolation, timeout_seconds=0.10)
        except TimeoutError as e:
            print(f"  attempt {attempt}: {e}")
        except CircuitOpen as e:
            print(f"  attempt {attempt}: {e}")
    print(f"  unrelated endpoint still responds: {unrelated_endpoint_on_service_a()}")
    print("  Service A fails fast on the slow dependency instead of")
    print("  exhausting its own capacity waiting on it.")


if __name__ == "__main__":
    demo_coupled_chain()
    demo_isolated_chain()
```

### TypeScript

Simulates the shared-database write-conflict symptom from dimension 11, two
services writing the same in-memory table with no ownership boundary, then
the corrected version where only the owning service writes and the other
calls its API.

```typescript
type Order = { id: string; status: string; total: number };

// The anti-pattern: two services hold direct write access to one table.
class SharedOrdersTable {
  private rows = new Map<string, Order>();

  write(order: Order): void {
    this.rows.set(order.id, order);
  }

  read(id: string): Order | undefined {
    return this.rows.get(id);
  }
}

class BillingServiceDirectWrite {
  constructor(private readonly table: SharedOrdersTable) {}

  markPaid(id: string): void {
    const order = this.table.read(id);
    if (!order) throw new Error("order not found");
    // Billing writes directly to a column Fulfillment also owns.
    this.table.write({ ...order, status: "paid" });
  }
}

class FulfillmentServiceDirectWrite {
  constructor(private readonly table: SharedOrdersTable) {}

  ship(id: string): void {
    const order = this.table.read(id);
    if (!order) throw new Error("order not found");
    // Fulfillment overwrites status with no knowledge Billing just set it.
    this.table.write({ ...order, status: "shipped" });
  }
}

function demoSharedDatabaseConflict(): void {
  console.log("Shared table, two services writing status directly.");
  const table = new SharedOrdersTable();
  table.write({ id: "o1", status: "new", total: 42 });
  const billing = new BillingServiceDirectWrite(table);
  const fulfillment = new FulfillmentServiceDirectWrite(table);
  billing.markPaid("o1");
  fulfillment.ship("o1");
  console.log("  final status:", table.read("o1")?.status);
  console.log("  the paid fact from Billing is silently lost, because");
  console.log("  Fulfillment's write raced it with no coordination.");
}

// The fix: Fulfillment owns the table, Billing calls its API instead.
class FulfillmentOwnedTable {
  private rows = new Map<string, Order & { paid: boolean }>();

  create(order: Order): void {
    this.rows.set(order.id, { ...order, paid: false });
  }

  markPaidViaApi(id: string): void {
    const order = this.rows.get(id);
    if (!order) throw new Error("order not found");
    this.rows.set(id, { ...order, paid: true });
  }

  ship(id: string): void {
    const order = this.rows.get(id);
    if (!order) throw new Error("order not found");
    if (!order.paid) throw new Error("cannot ship an unpaid order");
    this.rows.set(id, { ...order, status: "shipped" });
  }

  read(id: string) {
    return this.rows.get(id);
  }
}

function demoOwnedApiContract(): void {
  console.log("\nOwnership boundary, Billing calls Fulfillment's API.");
  const owned = new FulfillmentOwnedTable();
  owned.create({ id: "o1", status: "new", total: 42 });
  owned.markPaidViaApi("o1"); // stands in for a call to Fulfillment's API
  owned.ship("o1");
  console.log("  final state:", owned.read("o1"));
  console.log("  the paid flag is preserved because there is one writer,");
  console.log("  and the API contract even enforces the business rule");
  console.log("  that an unpaid order cannot ship.");
}

demoSharedDatabaseConflict();
demoOwnedApiContract();
```

### Java

Simulates the lockstep-deployment symptom from dimension 11, a shared library
version mismatch between two services causing a runtime contract failure that
neither service's own tests would catch in isolation.

```java
import java.util.HashMap;
import java.util.Map;

public class DistributedMonolithDemo {

    // Stands in for a shared validation library pinned at different
    // versions in two services. v1 allows a null discount, v2 requires it.
    interface OrderValidatorV1 {
        boolean isValid(Map<String, Object> order);
    }

    interface OrderValidatorV2 {
        boolean isValid(Map<String, Object> order);
    }

    static class ValidatorV1 implements OrderValidatorV1 {
        public boolean isValid(Map<String, Object> order) {
            return order.containsKey("total");
        }
    }

    static class ValidatorV2 implements OrderValidatorV2 {
        public boolean isValid(Map<String, Object> order) {
            return order.containsKey("total") && order.containsKey("discount");
        }
    }

    // Service A was redeployed with the shared library at v2.
    static class ServiceAWithNewLibrary {
        private final OrderValidatorV2 validator = new ValidatorV2();

        Map<String, Object> buildOrder(double total) {
            Map<String, Object> order = new HashMap<>();
            order.put("total", total);
            // Service A forgot to bump this call site to add "discount"
            // because the library upgrade was applied without reading
            // every call site, which is exactly how a version bump in a
            // shared library becomes a lockstep deployment requirement.
            return order;
        }

        boolean submit(Map<String, Object> order) {
            return validator.isValid(order);
        }
    }

    // Service B is still on the old library version and never noticed.
    static class ServiceBWithOldLibrary {
        private final OrderValidatorV1 validator = new ValidatorV1();

        boolean accept(Map<String, Object> order) {
            return validator.isValid(order);
        }
    }

    public static void main(String[] args) {
        System.out.println("Shared-library version drift across services.");

        ServiceAWithNewLibrary serviceA = new ServiceAWithNewLibrary();
        Map<String, Object> order = serviceA.buildOrder(99.5);

        boolean serviceAAccepts = serviceA.submit(order);
        System.out.println("  Service A's own validator (v2) says valid, " + serviceAAccepts);

        ServiceBWithOldLibrary serviceB = new ServiceBWithOldLibrary();
        boolean serviceBAccepts = serviceB.accept(order);
        System.out.println("  Service B's validator (v1) says valid, " + serviceBAccepts);

        System.out.println("  Service A silently produces an order that fails");
        System.out.println("  its own upgraded rule, and only Service B's older,");
        System.out.println("  looser rule happens to let it through today. The");
        System.out.println("  moment Service B is upgraded to v2 too, every order");
        System.out.println("  Service A already built starts failing downstream,");
        System.out.println("  with no code change in Service A to explain why.");
    }
}
```

Java's version was compiled and run with `javac` and `java` from the JDK
present on this machine. Python's version was run with `python3`. TypeScript's
version was compiled with `npx tsc` against a CommonJS target and run with
`node`. All three produced the output described in the comments above.

## 18. References

1. InfoQ. `Services or Objects, Distributed Monoliths, and Untangling
   Deployment from Release`, coverage of Ben Christensen's talk at the
   Microservices Practitioner Summit.
   https://www.infoq.com/news/2016/02/services-distributed-monolith/
   Verified 2026-08-02. Source for the named coinage in dimension 1 and the
   Netflix and industry-wide pattern in dimension 9.
2. Sam Newman. *Building Microservices*, 2nd edition. O'Reilly Media, 2021.
   ISBN 978-1-4920-3402-5. Chapter 4, `Splitting the Monolith`, and chapter
   11, `Testing`. Source for the shared-database and synchronous-chain
   coupling analysis, and the business-capability decomposition guidance in
   dimensions 1, 8, 11, and 13.
3. Martin Fowler. `MonolithFirst`.
   https://martinfowler.com/bliki/MonolithFirst.html
   Verified 2026-08-02. Source for the argument that boundaries drawn before
   the domain is understood tend to be wrong, cited in dimensions 1 and 13.
4. Chris Richardson. `Pattern. Shared database`, microservices.io.
   https://microservices.io/patterns/data/shared-database.html
   Verified 2026-08-02. Source for the shared-database variant analysis in
   dimensions 8 and 11.
5. Microsoft. `Interservice communication in microservices`, Azure
   Architecture Center.
   https://learn.microsoft.com/en-us/azure/architecture/microservices/design/interservice-communication
   Verified 2026-08-02. Source for the synchronous versus asynchronous
   trade-off, the retry and circuit breaker patterns, and the mutual TLS
   recommendation in dimensions 8 and 17.
6. Segment engineering blog, published on the Twilio blog. `Goodbye
   Microservices. From 100+ Problem Children to 1 Superstar`.
   https://www.twilio.com/en-us/blog/developers/best-practices/goodbye-microservices/
   Verified 2026-08-02. Source for the 140-plus service consolidation
   production case in dimension 9.
7. InfoQ. `How Deliveroo Moved from a Monolith to Microservices and What
   They Learned`.
   https://www.infoq.com/news/2017/03/deliveroo-monolith-distributed
   Verified 2026-08-02. Source for the third production case in dimension 9.
8. Wikipedia contributors. `Fallacies of distributed computing`.
   https://en.wikipedia.org/wiki/Fallacies_of_distributed_computing
   Verified 2026-08-02. Background source confirming the eight fallacies
   attributed to L. Peter Deutsch and, later, James Gosling at Sun
   Microsystems, informing the security and reliability discussion in
   dimension 17 about why synchronous network calls cannot be treated as
   free or reliable.
