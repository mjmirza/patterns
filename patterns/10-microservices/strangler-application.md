---
name: Strangler Application
slug: strangler-application
family: 10-microservices
category: Structural
aliases: [Strangler Fig Application, Strangler Fig Pattern, Strangler Pattern]
first_described: "Fowler 2004"
maturity: canonical
related: [decompose-by-business-capability, decompose-by-subdomain, api-gateway, anti-corruption-layer, backends-for-frontends]
incompatible_with: [big-bang-rewrite]
verified: 2026-08-02
---

# Strangler Application

## 1. Name, aliases, and lineage

The canonical name in the microservices literature is Strangler Application,
though the name almost every practitioner now uses in conversation is
Strangler Fig Application. Martin Fowler coined the term in a short bliki
post titled "StranglerApplication," published in 2004, drawing the analogy
from a botanical phenomenon he had observed on a vacation in the rainforests
of Queensland, Australia, in 2001. A strangler fig germinates in the crevice
of a host tree, sends roots down to the ground and shoots up toward the
canopy, and over years to decades gradually envelops the host, sometimes to
the point that the original tree dies and rots away, leaving a hollow
fig-shaped column where the tree used to stand (Fowler, "StranglerFigApplication," martinfowler.com, https://martinfowler.com/bliki/StranglerFigApplication.html, verified 2026-08-02).
Fowler wrote, in his own words on that page, that the software version
"begins with small additions, often new features, that are built on top of,
yet separate to, the legacy code base," language that the page still carries
verbatim today (Fowler, "StranglerFigApplication," martinfowler.com, https://martinfowler.com/bliki/StranglerFigApplication.html, verified 2026-08-02).

Fowler later retitled the post from "Strangler Application" to "Strangler Fig
Application," and the page itself explains why. the word strangler on its
own carries a violent, criminal connotation in English that the botanical
metaphor never intended, and adding "fig" makes clear the reference is to
the plant, not to an act of violence (Fowler, "StranglerFigApplication," martinfowler.com, https://martinfowler.com/bliki/StranglerFigApplication.html, verified 2026-08-02).
Chris Richardson's microservices pattern catalog lists the pattern under
"Strangler Application" as one of the named patterns in the Refactoring to
Microservices group, and treats it as a decomposition-and-migration pattern
for legacy monoliths rather than as a greenfield structural pattern
(Richardson, "Pattern. Strangler application," microservices.io, https://microservices.io/patterns/refactoring/strangler-application.html, verified 2026-08-02).
The Microsoft Azure Architecture Center uses "Strangler Fig Pattern" as its
canonical heading, which is the spelling that has become dominant in cloud
vendor documentation since roughly the mid-2010s (Microsoft, "Strangler Fig
pattern," Azure Architecture Center, https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig, verified 2026-08-02).
This entry treats Strangler Application, Strangler Fig Application, and
Strangler Fig Pattern as the same pattern under different house styles and
uses Strangler Application as the heading because that is this repository's
filed slug, while using the fig imagery throughout the explanatory prose
because the metaphor genuinely does the explanatory work Fowler intended.

The botanical claim underlying the metaphor is real, not invented for
the sake of a catchy name. A strangler fig is what botanists call a
hemiepiphyte. its seed germinates high in the crevice of a host tree rather
than in soil, after which it grows roots downward toward the ground while
simultaneously growing upward into the sunlit canopy, competing for the light
that is the limiting resource in a dense rainforest. Over time the host tree
can die, at which point the fig, now self-supporting on its own root
lattice, is left standing as a hollow, column-shaped structure in the
tree's original footprint. The host's death is not universal or guaranteed;
some sources note the fig's woody lattice can even help a host tree survive
storm damage it might not otherwise have withstood (Wikipedia contributors,
"Strangler fig," Wikipedia, https://en.wikipedia.org/wiki/Strangler_fig, verified 2026-08-02).
That nuance is a genuinely useful part of the metaphor for engineers. the
legacy system does not have to die in the way the word "strangler" implies.
in a healthy strangler migration, some legacy behavior is deliberately left
running indefinitely, wrapped rather than replaced, the same way a fig can
coexist with a still-living host for a long time.

## 2. Problem and context

A team owns a monolithic application that has become expensive to change.
The codebase might be years or decades old, built on a language or framework
version nobody wants to touch, entangled with a database schema that a dozen
different features read and write without a clear owner, and staffed by a
mix of people who understand only fragments of it. The business, meanwhile,
has not stopped asking for new features, and it will not tolerate a
multi-month or multi-year feature freeze while the system is rebuilt. This is
the exact situation Fowler was writing about, not a system with no users but
a system so entangled with an operating business that stopping it to rewrite
it is not a realistic option (Fowler, "StranglerFigApplication," martinfowler.com, https://martinfowler.com/bliki/StranglerFigApplication.html, verified 2026-08-02).

The naive response is the "big bang rewrite," where a team builds a
replacement system in parallel, working from the old system's specification
or its own read of the old code, and then cuts over to the new system in one
release. This has a well-documented history of going badly. The team that
best explains why, and did so before Fowler's post, is Joel Spolsky, whose
essay on rewriting Netscape's browser from scratch argues that a working
codebase, however ugly, encodes years of accumulated bug fixes and edge-case
handling that a fresh rewrite will silently drop and then have to
rediscover one support ticket at a time (Spolsky, "Things You Should Never
Do, Part I," Joel on Software, https://www.joelonsoftware.com/2000/04/06/things-you-should-never-do-part-i/, verified 2026-08-02).
The strangler application pattern is the answer to this problem in the
specific case where the target architecture is a decomposition into
services. Instead of replacing the whole system at once, a facade sits in
front of both the legacy system and a growing set of new services, routing
each request to whichever side currently owns that piece of functionality.
The legacy system keeps running and keeps earning revenue throughout the
migration. New functionality is built in the new architecture from day one.
Existing functionality is migrated piece by piece, at a pace the team can
sustain and verify, and each migrated piece can be validated against the
running legacy behavior before the legacy path for that piece is retired.

The pattern context is specifically a legacy system with live traffic and an
operating business behind it, not a system being built from nothing. It
presumes the team can insert an interception point, a reverse proxy, an API
gateway, a router, or in some cases a change made inside the legacy
application's own routing layer, between clients and the legacy system.
Without an interception point of some kind the pattern has nothing to route
through and cannot function.

## 3. Forces

The forces a strangler migration must balance, in the order they usually
bite a team in practice, are laid out below.

Risk versus speed of delivery. A big bang rewrite defers all risk to one
cutover event, which concentrates catastrophic failure into a single moment.
A strangler migration spreads risk across many small cutovers, each of which
is individually low-stakes and individually reversible, but the aggregate
calendar time to full migration is usually longer, sometimes much longer,
than the optimistic estimate for a rewrite. Teams that choose strangler over
rewrite are explicitly trading calendar time for blast-radius control.

Business continuity versus architectural purity. The legacy system was
built under different assumptions than the target architecture, and running
both systems side by side for months or years means living inside those
mismatched assumptions the whole time, rather than getting to a clean state
quickly. The forced coexistence is the cost of never having to stop shipping
features.

Coupling at the seam versus coupling inside the monolith. The facade and any
shared data store the legacy and new systems both touch become a new,
concentrated coupling point. A team that does not manage this seam carefully
can end up with tighter coupling at the boundary than the monolith itself
ever had internally, because now two independently deployed systems must
agree on the exact contract and data shape crossing that boundary at every
moment during the migration, not only at a single release boundary.

Operability during a long transition versus a clean operational model at the
end. For the duration of the migration, on-call engineers must understand
two systems, two deployment pipelines, and a facade that decides which one
handles which request, which is strictly more operational surface than
either the monolith alone or the finished target architecture alone.

Team cognitive load and organizational change versus incremental delivery.
Fowler's own restatement of the pattern, in the "Strangler Fig Application"
retrospective he later wrote with ThoughtWorks colleagues on modernization
practice, frames the pattern as inseparable from an organizational change
process. understanding what outcome the business actually wants, breaking
that outcome into small deliverable pieces, delivering those pieces, and
building the organizational muscle to sustain incremental delivery, are all
named as necessary parts of a strangler effort, not only the technical
routing mechanism (Fowler, "StranglerFigApplication," martinfowler.com, https://martinfowler.com/bliki/StranglerFigApplication.html, verified 2026-08-02).
A team that treats strangler purely as a technical routing trick, without
the delivery discipline the pattern assumes, tends to end up with a
permanent facade routing to a permanently half-migrated system, which is
judgement based on repeatedly observed failure shape, not a sourced claim.

Cost, sacrificed favorably. The pattern favors continuity of revenue and
manageable risk over minimizing total engineering cost, and it explicitly
sacrifices speed to a finished state. A team under genuine time pressure to
retire a system by a hard deadline, for a contractual or regulatory reason,
may find the pattern's slow, incremental nature is the wrong trade for their
situation, which is exactly the non-applicability case covered next.

## 4. Applicability and non-applicability

Reach for strangler application when all or most of the following hold true.

The system has real, live traffic and an operating business that cannot
tolerate a long feature freeze or an extended outage for a cutover.

An interception point exists, or can be created, in front of the legacy
system, such as a reverse proxy, a load balancer with routing rules, an API
gateway, DNS-level routing, or a change inside the legacy application's own
router that lets you redirect specific routes elsewhere.

The legacy system's source code and behavior are at least partially
understood well enough to know which features exist and roughly what they
do, so that migrated pieces can be validated against a known baseline.

The team can sustain incremental delivery over a period of months to years
and has, or can build, the organizational patience to ship the migration in
small verified slices rather than a big release.

The target architecture is a decomposition into independently deployable
services, and the team has already done or is doing the decomposition
analysis, most often via Decompose by Business Capability or Decompose by
Subdomain, to know where the seams should go
(Richardson, "Pattern. Strangler application," microservices.io, https://microservices.io/patterns/refactoring/strangler-application.html, verified 2026-08-02).

Do NOT reach for it, and here are the reasons in each case.

Requests to the legacy system cannot be intercepted at all, for example a
tightly coupled desktop client that talks directly to a database with no
network hop that can be redirected, in which case there is no seam for a
facade to route through and the pattern has nothing to attach to. This is
stated explicitly as a non-fit in the Azure Architecture Center's own
"when to use this pattern" guidance
(Microsoft, "Strangler Fig pattern," Azure Architecture Center, https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig, verified 2026-08-02).

You do not have access to the legacy system's source code, because a
strangler migration frequently needs the legacy application changed so that
migrated features stop handling requests internally and instead let the
facade route around them, and the same Azure guidance names this directly as
a blocking constraint
(Microsoft, "Strangler Fig pattern," Azure Architecture Center, https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig, verified 2026-08-02).

The system is small enough that a full rewrite genuinely is simple and low
risk, in which case the overhead of building and operating a routing facade,
running two systems side by side, and building an anti-corruption layer for
cross-system calls costs more than it saves. The same source lists "you
migrate a small system and replacing the whole system is simple" as an
explicit non-fit
(Microsoft, "Strangler Fig pattern," Azure Architecture Center, https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig, verified 2026-08-02).

You need the legacy system fully decommissioned quickly, for example to
exit a data-center lease, a vendor contract, or a compliance deadline with a
fixed date close at hand. A strangler migration trades speed to a finished
state for reduced risk during the transition, and a hard external deadline
can make that trade the wrong one. This is engineering judgement about a
degree-of-fit, not a sourced fact, but it follows directly from the pattern's
own stated forces.

The organization cannot sustain incremental delivery, because leadership
wants a single "done" milestone and will not fund or tolerate a
multi-quarter transitional state. A strangler migration left half-finished,
with a permanent facade routing between a permanently-not-fully-retired
legacy system and a partially built new one, is worse than either finishing
the rewrite or not starting it, which is engineering judgement drawn from
repeatedly observed failure patterns in migration write-ups, not a sourced
statistic.

## 5. Structure

The pattern has four participants, named for the role each plays rather than
for any specific technology.

The Client is whatever calls into the system. a browser, a mobile app, an
internal service, a batch job. The client's defining property in this
pattern is that it should not need to know, or care, which backend, legacy
or new, actually served its request.

The Facade, also called the router, proxy, or strangler proxy, sits directly
in front of both the legacy system and the new system and is the single
interception point every client request passes through. Its only job is
routing. for each inbound request, decide whether the legacy system or one
of the new services should handle it, forward the request there, and return
the response to the client. Over the life of the migration the facade's
routing table changes continuously, starting almost entirely pointed at the
legacy system and ending almost entirely pointed at new services.

The Legacy System is the existing monolith, unchanged in its core behavior
but progressively reduced in scope as functionality is migrated out from
under it. A key structural detail, not always obvious to teams new to the
pattern, is that the legacy system is frequently also modified during a
strangler migration, not merely routed around. specifically, once a feature
is migrated, the legacy system's own internal code path for that feature is
often stubbed out or disabled so the legacy system stops doing work for
requests it will never receive again, and so that any internal calls the
legacy system makes to that feature are redirected outward to the new
service instead of being served by dead internal code
(Microsoft, "Strangler Fig pattern," Azure Architecture Center, https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig, verified 2026-08-02).

The New System is the set of new services, built in the target architecture,
that progressively take over functionality from the legacy system. Chris
Richardson's catalog description makes an important structural distinction
here. the new-system services split into two kinds, services that replace an
existing piece of legacy functionality, and services that implement entirely
new functionality that never existed in the legacy system at all, the latter
being how a strangler migration typically demonstrates the value of the new
architecture to stakeholders early, well before the bulk of the legacy
functionality has been migrated
(Richardson, "Pattern. Strangler application," microservices.io, https://microservices.io/patterns/refactoring/strangler-application.html, verified 2026-08-02).

A fifth, optional but commonly necessary participant is the Anti-Corruption
Layer, an adapter placed at any point where the new system must call
still-unmigrated legacy functionality, or where the legacy system must call
already-migrated new functionality. Its job is to translate between the two
systems' differing data models and conventions so that neither system's
internal design has to bend to accommodate the other's legacy assumptions.
The Azure Architecture Center names this pattern explicitly as the mechanism
for managing cross-system dependencies during a strangler migration
(Microsoft, "Strangler Fig pattern," Azure Architecture Center, https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig, verified 2026-08-02).

## 6. ASCII structure diagram

```
  Phase 1: introduce the facade

    Client
      |
      v
  +---------+        (almost all traffic)
  | Facade  |------------------------------> +----------------+
  +---------+                                | Legacy System  |
      |                                      +----------------+
      | (a few migrated routes)
      v
  +----------------+
  | New Service A  |
  +----------------+


  Phase 2: incremental migration, mid-transition

    Client
      |
      v
  +---------+
  | Facade  |
  +---------+
    |    |    |
    |    |    +----------------------------> +----------------+
    |    |                                   | Legacy System  |
    |    |                                   | (shrinking)    |
    |    |                                   +----------------+
    |    |                                          ^   |
    |    |                                          |   |
    |    v                                   +--------------+
    |  +----------------+   cross-system     | Anti-        |
    |  | New Service B  |<------------------>| Corruption   |
    |  +----------------+     calls          | Layer        |
    v                                        +--------------+
  +----------------+
  | New Service A  |
  +----------------+


  Phase 3: legacy decommissioned, facade removed

    Client
      |
      v
  +----------------+     +----------------+     +----------------+
  | New Service A  |     | New Service B  |     | New Service C  |
  +----------------+     +----------------+     +----------------+
```

## 7. Dynamics

The dynamics play out over calendar time, not within a single request, which
distinguishes this pattern from most structural patterns whose dynamics fit
in one sequence diagram. The following traces the four stages the Azure
Architecture Center documents and the request-level routing decision inside
each stage
(Microsoft, "Strangler Fig pattern," Azure Architecture Center, https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig, verified 2026-08-02).

```
Stage 1. facade introduced, routing table nearly empty

  Client -> Facade -- request for route R
  Facade -- lookup R in routing table -> not found -> default target
  Facade -> Legacy System -- forward request for R
  Legacy System -> Facade -- response
  Facade -> Client -- response


Stage 2. one feature migrated, routing table has one entry

  Client -> Facade -- request for route R (now migrated)
  Facade -- lookup R in routing table -> found -> New Service A
  Facade -> New Service A -- forward request for R
  New Service A -> Legacy System (or shared DB) -- read data A depends on,
      via the Anti-Corruption Layer if the data shape differs
  New Service A -> Facade -- response
  Facade -> Client -- response

  Client -> Facade -- request for route S (not yet migrated)
  Facade -- lookup S in routing table -> not found -> default target
  Facade -> Legacy System -- forward request for S
  Legacy System -> New Service A -- read data now owned by A,
      via the Anti-Corruption Layer
  Legacy System -> Facade -- response
  Facade -> Client -- response


Stage 3. cutover verification for a specific migrated feature
  (dark launch / shadow traffic, an optional but common practice)

  Client -> Facade -- request for route T
  Facade -> Legacy System -- forward (still the system of record)
  Facade -> New Service C -- forward a copy, response discarded or compared
  Facade -- compare Legacy response to New Service C response, log any diff
  Facade -> Client -- Legacy System's response


Stage 4. legacy fully decommissioned

  Client -> Facade -- request for any route
  Facade -- lookup in routing table -> always found -> a New Service
  Facade -> New Service -- forward
  New Service -> Facade -- response
  Facade -> Client -- response

  (Facade may now be removed entirely and Client redirected to talk
   to the New Services directly, per Azure Architecture Center step 4)
```

The database-level variant of the dynamics, which the Azure Architecture
Center documents as a distinct but closely related flow, differs in what
gets migrated. rather than routing HTTP requests, a change data capture (CDC)
process continuously syncs domain-specific tables out of a shared monolithic
database into an isolated domain database owned by the new service, while
both the legacy system and the new system read and write concurrently during
a validated transition window, after which the domain tables are removed
from the monolithic database
(Microsoft, "Strangler Fig pattern," Azure Architecture Center, https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig, verified 2026-08-02).

## 8. Implementation variants

HTTP-level facade via a reverse proxy or API gateway. The most common
implementation. an off-the-shelf reverse proxy, nginx, Envoy, HAProxy, or a
managed API gateway product, is configured with routing rules that match on
URL path, HTTP method, header, or hostname, and forwards matched requests to
new services while defaulting everything else to the legacy system. This
variant is preferred when the legacy system is already a web application or
API and the seam can be drawn cleanly at the HTTP layer.

Application-level facade embedded inside the legacy system's own router.
Rather than an external proxy, the legacy application's existing routing or
controller layer is modified so that specific routes, instead of executing
legacy handler code, make an outbound call to a new service and return its
response. This variant is common when there is no separate infrastructure
layer available to insert a proxy, or when the team wants finer control over
per-route behavior, such as gradually shifting a percentage of traffic for
one route rather than an all-or-nothing cutover per route.

Database-level, or data-first, strangler. Instead of routing requests, the
migration starts by extracting a bounded set of tables and their behavior
into an isolated domain database, using an ETL process for the initial bulk
copy and a change data capture process to keep the new domain database in
sync with the still-live monolithic database during the transition, before
cutting reads and writes for that domain over to the new database and
removing the domain's tables from the monolith. This is the variant the
Azure Architecture Center documents as a named alternative to the
request-routing variant, useful specifically when the tightest coupling in
the legacy system is at the shared-database layer rather than at the API
layer
(Microsoft, "Strangler Fig pattern," Azure Architecture Center, https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig, verified 2026-08-02).

Branch by abstraction, as a complementary in-process variant. Where a
strangler migration is difficult at the network boundary, for example
because two implementations of the same interface must live inside the same
deployable for a transition period, teams introduce an abstraction layer
inside the codebase itself, route calls through it with a feature flag
choosing the old or new implementation, and delete the old implementation
once the new one is proven. Martin Fowler catalogs this as a distinct
pattern, Branch by Abstraction, related to but not identical with the
strangler application, and useful for the same underlying problem, avoiding
a long-lived feature branch, applied one level down inside a single
deployable rather than across a network boundary
(Fowler, "BranchByAbstraction," martinfowler.com, https://martinfowler.com/bliki/BranchByAbstraction.html, verified 2026-08-02).

Sidecar-based interception. In a service-mesh environment, the routing
decision is delegated to a sidecar proxy attached to the legacy workload,
using the mesh's traffic-splitting and route-matching capability rather than
a standalone facade service, which lets the routing rules live as
declarative configuration alongside the mesh's other traffic management
policy instead of as code in a bespoke proxy. This is a natural fit for
teams already running a service mesh for other reasons, and is a widely
practiced adaptation of the pattern to that infrastructure rather than a
separately named pattern in its own right, which is engineering judgement
based on how the pattern is commonly discussed alongside mesh infrastructure,
not a specific sourced claim about a named mesh product.

## 9. Known production uses

The Financial Times ran a widely cited strangler migration of its content
platform starting around 2013, decomposing a legacy monolithic publishing
system into a set of independently deployable services behind a facade,
which is one of the case studies Martin Fowler's own bliki entry references
via a linked write-up on the FT's approach, and which is separately
referenced as a foundational public strangler-migration case study in
Sam Newman's book on service decomposition, *Monolith to Microservices*,
O'Reilly, 2019, in the chapter covering incremental migration patterns
(Newman, *Monolith to Microservices*, O'Reilly, 2019, ISBN 978-1-4920-3477-4,
chapter on "Migration Patterns," publisher's page consulted for ISBN and
table of contents at https://www.oreilly.com/library/view/monolith-to-microservices/9781492047834/, verified 2026-08-02).

Chris Richardson's own microservices.io pattern catalog, which is the
canonical secondary reference for the pattern name used in this repository,
lists production adoption discussion tied to his book *Microservices
Patterns. With Examples in Java*, Manning, 2018, where the strangler
application pattern is presented as chapter-level material with a running
example migrating a monolithic food delivery application, "FTGO," into a
set of services, used throughout the book as the worked case rather than a
disguised real production system, and the pattern page itself is the
authoritative published description this entry cites throughout
(Richardson, "Pattern. Strangler application," microservices.io, https://microservices.io/patterns/refactoring/strangler-application.html, verified 2026-08-02).

Microsoft documents the pattern as a first-class entry in the Azure
Architecture Center's Cloud Design Patterns catalog, maintained and
periodically updated by named Azure Cloud Solution Architects, which is
itself evidence of production-scale adoption on Microsoft's own cloud
customer base, since Cloud Design Patterns entries are written from
recurring patterns Microsoft's architecture teams observe across customer
migration engagements rather than from a single hypothetical scenario
(Microsoft, "Strangler Fig pattern," Azure Architecture Center, https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig, verified 2026-08-02).
The same page documents a specific, named sub-pattern for migrating a
monolithic database domain by domain via change data capture, which is
presented as a pattern Azure's own architecture guidance has formalized
directly from field engagements, not as a theoretical extension.

## 10. Consequences

Positive.

The legacy system keeps serving live traffic throughout the migration,
which means the business never funds a multi-month feature freeze and never
bets the whole migration on a single high-stakes cutover event.

Each migrated slice can be validated against the legacy system's known
behavior before its traffic is cut over, which catches behavioral
regressions while the safety net of the still-running legacy path exists,
rather than after a full cutover when the only fallback is a full rollback.

Risk is distributed across many small, individually reversible steps instead
of concentrated into one release, which the Azure Architecture Center
explicitly ties to the Reliability pillar of the Well-Architected Framework,
describing the incremental approach as mitigating risk compared to a single
large systemic change
(Microsoft, "Strangler Fig pattern," Azure Architecture Center, https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig, verified 2026-08-02).

New functionality can be delivered in the target architecture from day one,
which lets a team demonstrate the value of the new architecture to
stakeholders early, using genuinely new features rather than waiting for the
migration of old ones to finish first
(Richardson, "Pattern. Strangler application," microservices.io, https://microservices.io/patterns/refactoring/strangler-application.html, verified 2026-08-02).

The same Azure guidance also ties the pattern to the Cost Optimization
pillar, on the reasoning that migrating high-return-on-investment components
first, while continuing to run the still-valuable legacy investment for
everything else, maximizes the use of existing sunk investment while
modernizing incrementally, rather than writing off the whole legacy
investment at once
(Microsoft, "Strangler Fig pattern," Azure Architecture Center, https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig, verified 2026-08-02).

Negative.

The migration takes materially longer in calendar time than a rewrite would
take if the rewrite actually succeeded, and there is no guarantee in advance
how long, because the pace is set by how carefully each slice must be
validated, not by an estimate made before the legacy system's true
complexity is understood.

The team must operate two systems, and often two deployment pipelines and
two on-call rotations' worth of operational knowledge, for the entire
transition period, which is strictly more operational surface than either
system alone.

The facade itself becomes a new single point of failure and a possible
performance bottleneck if it is not built and scaled with the same care as
any other piece of critical infrastructure, a risk the Azure Architecture
Center calls out explicitly as a problem to plan for
(Microsoft, "Strangler Fig pattern," Azure Architecture Center, https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig, verified 2026-08-02).

Cross-system calls, where the new system needs data or behavior the legacy
system still owns, or vice versa, require an anti-corruption layer to avoid
letting legacy conventions leak into the new system's design, and building
and maintaining that translation layer is itself ongoing engineering cost
for as long as the migration is incomplete.

A migration that stalls indefinitely, with the facade still routing a
meaningful fraction of traffic to the legacy system years after the effort
began, leaves the organization paying the full operational cost of running
two systems with none of the benefit of having finished either one, which is
the single most commonly cited failure mode in practitioner discussion of
the pattern, stated here as engineering judgement rather than as a specific
sourced statistic.

## 11. Failure modes and misuse

The stalled migration. Symptom. The facade's routing table has not grown in
months, the legacy system is still handling the majority of traffic long
after the original migration timeline, and nobody on the team can say with
confidence when the remaining migration will finish. Cause. The
organizational discipline Fowler's own description treats as inseparable
from the pattern, breaking the outcome into small deliverable pieces and
sustaining delivery of those pieces, was never actually built, so the
migration effort loses funding or attention to whatever feature work is
more urgent this quarter, and the facade becomes a permanent piece of
infrastructure rather than a transitional one
(Fowler, "StranglerFigApplication," martinfowler.com, https://martinfowler.com/bliki/StranglerFigApplication.html, verified 2026-08-02).
Fix. Treat the migration as a funded, tracked initiative with its own
backlog and a visible metric, such as percentage of traffic or percentage of
routes still hitting the legacy system, reviewed on a fixed cadence, and
timebox how long any single feature is allowed to remain un-migrated once
its dependencies are ready.

The leaky anti-corruption layer. Symptom. The new services start
accumulating fields, enums, or null-handling logic that only make sense in
terms of the legacy system's internal data model, and developers on the new
side start saying they have to "know how the old system works" to write
correct code in the new one. Cause. The anti-corruption layer was skipped,
or was built once and never maintained as the legacy system's edge cases
were discovered one at a time, so legacy conventions leaked straight through
into the new system's domain model, which the Azure Architecture Center
warns against directly, describing the anti-corruption layer's job as
protecting the new system's design from legacy semantics
(Microsoft, "Strangler Fig pattern," Azure Architecture Center, https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig, verified 2026-08-02).
Fix. Put the anti-corruption layer under the same code review and test
discipline as the rest of the new system, and treat every legacy quirk it
absorbs as a deliberate, documented decision rather than an ad hoc patch.

The premature victory lap. Symptom. The team announces the migration
complete and starts decommissioning legacy infrastructure, then discovers a
still-live internal batch job, a partner integration, or an old mobile app
version that talks directly to the legacy system, bypassing the facade
entirely. Cause. The interception point the facade provides only covers
traffic that actually flows through it, and any client that has a direct
line to the legacy system was never migrated because it was never routed
through the facade in the first place, an availability the Azure guidance
implicitly assumes when it lists "requests to the back-end system can't be
intercepted" as a reason the pattern does not fit
(Microsoft, "Strangler Fig pattern," Azure Architecture Center, https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig, verified 2026-08-02).
Fix. Audit every known caller of the legacy system, not only the ones that
go through the primary client path, before declaring any decommission safe,
and instrument the legacy system itself to log and alert on any traffic it
still receives after it was believed retired.

The database race between two writers. Symptom. Intermittent data
inconsistency appears in the new domain database during the transition
window, sometimes a write made through the new service is silently
overwritten by a change-data-capture sync still running from the legacy
database, or the reverse. Cause. The database-level variant of the pattern
requires the legacy system and the new system to write concurrently to
overlapping data for a period, and the sync direction and conflict-resolution
rule were not made explicit, so whichever write happens to land last wins by
accident rather than by design, exactly the coexistence hazard the Azure
guidance calls out as something to plan for explicitly, that both systems
must be able to access these resources at the same time
(Microsoft, "Strangler Fig pattern," Azure Architecture Center, https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig, verified 2026-08-02).
Fix. Designate one system as the single system of record for each piece of
data at every point in the migration, make the sync direction one-way at any
given time, and only flip the system of record at an explicit, validated
cutover step, never gradually.

The rewrite-in-disguise. Symptom. The team calls the effort a strangler
migration, but the new system is being built against a from-scratch
understanding of what the legacy system should do rather than what it
actually does, and no traffic has been cut over after months of new-system
development. Cause. The pattern's core discipline, migrate a real,
observable slice of legacy behavior and cut real traffic over to it quickly
enough to validate the slice, was abandoned in favor of building the whole
new system first and cutting over once, which reintroduces exactly the risk
concentration and the specification-drift problem Spolsky describes as
throwing away accumulated knowledge, the same problem the pattern exists to
avoid
(Spolsky, "Things You Should Never Do, Part I," Joel on Software, https://www.joelonsoftware.com/2000/04/06/things-you-should-never-do-part-i/, verified 2026-08-02).
Fix. Set a rule that no new-system feature work continues on the next slice
until the previous slice has real production traffic routed to it, which
forces the incremental cutover discipline the pattern name promises.

## 12. Trade-off matrix

| Force | Strangler Application | Big Bang Rewrite | Branch by Abstraction | Blue-Green Deployment |
|---|---|---|---|---|
| Risk concentration | Spread across many small cutovers | Concentrated in one cutover event | Spread across many in-process toggles | Concentrated in one traffic-switch event |
| Business continuity during transition | Legacy keeps serving traffic throughout | Legacy frozen or duplicated during rewrite | Same deployable serves both paths, no freeze | Both environments fully built before switch |
| Typical scope | Whole system, decomposed piece by piece | Whole system, replaced at once | A single component or module inside one deployable | A whole deployable unit, same architecture on both sides |
| New architecture required | Yes, this is the point of the pattern | Optional, could rewrite into the same architecture | No, the abstraction hides two implementations of the same shape | No, both environments run identical code |
| Calendar time to completion | Long, months to years, variable | Shorter if it works, unbounded if it does not | Short, scoped to one component | Very short, a single deploy plus a switch |
| Operational surface during transition | Two systems, a facade, an anti-corruption layer | One system, plus a shadow system in development | One deployable, a feature flag | Two identical environments |
| Failure mode when it goes wrong | Stalled indefinite migration, permanent dual-run cost | Total loss of unmigrated behavior discovered late | Feature flag debt if old path never removed | Rollback is fast, but no incremental validation of correctness |
| Best fit | Live legacy system, no freeze tolerance, target is a service decomposition | Small system, or a system with no live users yet | A single risky internal change inside one deployable | Deploying a new version of the same architecture, not migrating architecture |

## 13. Related and incompatible patterns

Decompose by Business Capability and Decompose by Subdomain are the
decomposition patterns a strangler migration draws its target service
boundaries from. The strangler application pattern does not itself decide
where the seams go, it only handles the mechanics of migrating traffic once
the seams are decided, so it is routinely paired with one or both of those
decomposition patterns as the first step of planning a strangler effort
(Richardson, "Pattern. Strangler application," microservices.io, https://microservices.io/patterns/refactoring/strangler-application.html, verified 2026-08-02).

Anti-Corruption Layer composes directly with strangler application at every
point where the new system and the legacy system must call each other
during the transition, translating between their differing data models so
neither side's design has to bend to the other's legacy assumptions
(Microsoft, "Strangler Fig pattern," Azure Architecture Center, https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig, verified 2026-08-02).

API Gateway is frequently the concrete technology used to implement the
Facade participant, particularly in the HTTP-routing variant of the
pattern, since an API gateway already provides route matching, request
forwarding, and often traffic-splitting capability out of the box, saving
the team from building a bespoke proxy.

Branch by Abstraction is the closest sibling pattern and is sometimes
confused with strangler application, but the two operate at different
granularities. Branch by Abstraction toggles between two implementations of
the same interface inside a single deployable using a feature flag, while
Strangler Application routes traffic between two independently deployed
systems across a network boundary. A team can use Branch by Abstraction as
one tool inside a larger strangler effort, for example to manage a risky
internal refactor of a component that has not yet been extracted into its
own service, without the two patterns conflicting
(Fowler, "BranchByAbstraction," martinfowler.com, https://martinfowler.com/bliki/BranchByAbstraction.html, verified 2026-08-02).

Blue-Green Deployment is incompatible in intent, though not in mechanism,
with strangler application. Blue-green deployment assumes both environments
run the same architecture and the same behavior, and exists to make
deployment itself safer and faster, whereas strangler application exists
precisely because the two sides are running different architectures with
different behavior for an extended period. Using blue-green thinking against
a strangler migration, switching all traffic over in one go, reintroduces
the big-bang risk the pattern was chosen to avoid, which is engineering
judgement about the underlying assumption mismatch, not a sourced claim
about either pattern's documentation.

Big Bang Rewrite is the incompatible pattern named directly in this entry's
frontmatter, and the whole reason strangler application exists as a named
alternative is dissatisfaction with the big bang rewrite's risk profile in
systems with live traffic and a real business behind them
(Spolsky, "Things You Should Never Do, Part I," Joel on Software, https://www.joelonsoftware.com/2000/04/06/things-you-should-never-do-part-i/, verified 2026-08-02).

## 14. Refactoring path in and out

Introducing the pattern into a system that does not have it starts before
any code changes. First, inventory the legacy system's routes or
capabilities well enough to know what exists and roughly what depends on
what, because the migration plan and the anti-corruption layer both need
this map. Second, identify or build the interception point, a reverse
proxy, an API gateway, or a change inside the legacy router, that every
client request will pass through going forward, and cut traffic over to
routing through it while every route still defaults to the legacy system, so
this step alone changes nothing observable to clients but proves the
facade works. Third, pick the smallest, lowest-risk, ideally
already-well-understood piece of functionality as the first migration
candidate, build it as a new service, validate it against the legacy
system's known behavior, for example by shadowing traffic to both and
comparing responses before cutting the facade's routing table over, and
only then flip the routing table entry for that piece. Fourth, repeat, each
time picking the next piece by a combination of business value and
migration risk, migrating the higher-value, better-understood pieces first
per the Azure Architecture Center's cost-optimization framing
(Microsoft, "Strangler Fig pattern," Azure Architecture Center, https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig, verified 2026-08-02),
and building or extending the anti-corruption layer as new cross-system
calls appear. Fifth, once the legacy system handles no traffic at all and
has no remaining internal callers, decommission it, and once the new system
is stable, consider whether the facade itself should be removed and clients
redirected to talk to the new services directly, or kept as a permanent API
gateway for the finished architecture, both of which the Azure guidance
lists as valid end states depending on whether legacy clients still need the
old interface shape
(Microsoft, "Strangler Fig pattern," Azure Architecture Center, https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig, verified 2026-08-02).

Removing the pattern once the migration is complete is largely the fifth
step above. decommission the legacy system, verify nothing still calls it
by monitoring for stray traffic for a safety window before deleting its
infrastructure, and then decide the facade's fate. A facade kept
permanently functions as an ordinary API gateway from that point forward,
which is a legitimate architectural choice, not a leftover artifact, provided
the team makes that choice deliberately rather than by default inertia. A
facade removed entirely requires updating every client to call the new
services directly, which is itself a coordinated change and should be
planned and versioned like any other breaking API change.

## 15. Testing and verification

Contract or characterization tests against the legacy system, captured
before any migration work begins, are the foundation everything else in a
strangler migration verifies against. Because the goal of a migrated slice
is behavioral parity with the legacy system, not a fresh interpretation of
what the behavior should be, the team needs a way to record the legacy
system's actual observed behavior, request in, response out, for the
routes being migrated, and replay those recorded interactions against the
new service as regression tests. This is a direct application of
characterization testing, a technique for legacy code with no existing test
suite, to the specific case where the "legacy code" is a whole system being
migrated rather than a single function.

Shadow traffic comparison, sometimes called dark launching or a shadow
deployment, sends a copy of live production requests to the new service in
parallel with the still-authoritative legacy system, discards or logs the
new service's response without returning it to the client, and compares the
two responses to surface behavioral differences before any real traffic is
actually cut over. This is easy to test because the legacy system's
response remains the single source of truth throughout, so any diff is
unambiguous evidence of a gap in the new service, not evidence of an
ambiguous "which one is right" question, but it becomes hard to test for
any behavior that is order-dependent, time-dependent, or has side effects
that cannot be safely executed twice, for example anything that sends an
email, charges a card, or writes to a shared resource with the legacy path.
Idempotent, read-heavy routes are the easiest to validate this way, and
side-effecting write routes are the hardest, which is engineering judgement
consistent with how shadow testing is generally practiced, not a specific
sourced claim.

Canary or percentage-based cutover, migrating a route by sending a small
percentage of its real traffic to the new service and increasing that
percentage over successive deployments, catches issues that only manifest
under real production load, real data variety, and real concurrent traffic,
none of which a shadow test can fully replicate for side-effecting requests.
This trades a longer validation window for the ability to safely test
routes that shadow traffic cannot cover.

Consumer-driven contract tests between the new services and any still-live
legacy callers, or between the legacy system and any already-migrated new
services it now calls through the anti-corruption layer, become newly
necessary once the system has more than one deployable talking across a
network boundary, a form of testing the original monolith did not need at
all because everything called everything else in-process. This is the
testing cost the pattern introduces in exchange for its migration benefits,
and skipping it is exactly how the leaky anti-corruption layer failure mode
in dimension 11 goes undetected until it reaches production.

End-to-end tests through the facade itself, exercising both the
still-legacy and the newly-migrated routes through the same interception
point clients actually use, verify the routing table is correct and that
the facade is not silently misrouting traffic, a category of bug that unit
tests of either system alone cannot catch because the bug lives entirely in
the facade's configuration, not in either system's code.

## 16. Observability signals

The routing table's own composition, tracked over time, is the single most
important business-facing signal of migration progress. what percentage of
routes, or better, what percentage of actual request volume, is currently
being served by new services versus the legacy system, tracked as a metric
that should trend consistently upward and never silently plateau for an
extended period, which is the earliest observable sign of the stalled
migration failure mode in dimension 11.

Per-route latency and error rate, tagged by which backend, legacy or new,
served the request, surfaced on the same dashboard so a regression
introduced by a migration cutover is immediately visible as a spike
correlated with that route's routing table change, rather than buried in an
aggregate metric that mixes both backends together.

Legacy system traffic after a route or feature is believed fully migrated,
alerted on rather than merely logged, is the direct detection mechanism for
the premature-victory-lap failure mode. any request the legacy system still
receives for a route the team believes it decommissioned is either a
routing-table bug or an un-inventoried caller that bypasses the facade, and
either way it needs immediate attention before that route's legacy code path
is deleted.

Anti-corruption layer call volume and error rate, tracked as its own
service-level signal rather than folded into either the legacy or new
system's metrics, because a rising error rate specifically at the
translation layer is the earliest sign that the two systems' data models
have drifted apart in a way the translation logic no longer handles
correctly.

Data consistency checks between the legacy database and any new domain
database receiving change-data-capture syncs, run as a scheduled
reconciliation job that compares row counts, checksums, or specific
business invariants across both stores and alerts on drift, are the direct
detection mechanism for the database race condition failure mode, and are
explicitly recommended in the Azure Architecture Center's database-variant
walkthrough as a validation step before any domain cutover
(Microsoft, "Strangler Fig pattern," Azure Architecture Center, https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig, verified 2026-08-02).

## 17. Security and privacy implications

The facade becomes a new, concentrated point where authentication and
authorization decisions must be applied consistently across both the legacy
system's security model and the new system's security model, which may
differ, for example session-cookie authentication on the legacy side and
token-based authentication on the new side. A gap in how the facade
translates or enforces identity across that boundary is a direct
authorization bypass risk, since a request that would have been rejected by
the legacy system's own auth check might reach a new service through the
facade without the equivalent check being applied, or the reverse.

Data crossing the anti-corruption layer between systems with different data
protection assumptions, for example a legacy system built before a
particular data-minimization or field-level encryption requirement existed,
and a new system built to a current standard, needs the translation layer to
enforce the stricter of the two standards on any data it moves across the
boundary, rather than passing legacy-shaped, under-protected data straight
through into the new system's domain model. This entry states the general
principle, since the specific field-level requirements are entirely
dependent on the regulatory and data-classification context of the system
being migrated, which this entry has no visibility into.

The transition period doubles the attack surface in a literal sense, because
there are now two independently deployed systems, two sets of dependencies
to patch, and two codebases that must both stay current on security
updates for the full duration of the migration, rather than one. A team
that treats the legacy system as "already being replaced, so patching can
wait" during a multi-year strangler effort is leaving a live production
system unpatched for the entire migration window, which is a direct and
avoidable risk increase relative to either finishing the migration quickly
or maintaining the legacy system to normal patching standards throughout.

Logging and monitoring data captured for shadow-traffic comparison, per
dimension 15, duplicates real production request and response data into a
comparison pipeline that did not exist before the migration began, and that
pipeline needs the same access controls, retention limits, and data
handling review as the production systems it is comparing, since it is now
itself a system that holds a copy of live customer data, not merely a
diagnostic tool.

## 18. References

- Fowler, Martin. "StranglerFigApplication." martinfowler.com, 2004, updated
  subsequently. https://martinfowler.com/bliki/StranglerFigApplication.html,
  verified 2026-08-02.
- Fowler, Martin. "BranchByAbstraction." martinfowler.com.
  https://martinfowler.com/bliki/BranchByAbstraction.html, verified
  2026-08-02.
- Richardson, Chris. "Pattern. Strangler application." microservices.io.
  https://microservices.io/patterns/refactoring/strangler-application.html,
  verified 2026-08-02.
- Richardson, Chris. *Microservices Patterns. With Examples in Java*.
  Manning Publications, 2018. ISBN 978-1-61729-454-2.
- Microsoft. "Strangler Fig pattern." Azure Architecture Center, Microsoft
  Learn. Principal authors Adnan Khan and Ovais Mehboob Ahmed Khan.
  https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig,
  verified 2026-08-02.
- Newman, Sam. *Monolith to Microservices. Evolutionary Patterns to
  Transform Your Monolith*. O'Reilly Media, 2019. ISBN 978-1-4920-3477-4.
  Publisher listing consulted at
  https://www.oreilly.com/library/view/monolith-to-microservices/9781492047834/,
  verified 2026-08-02.
- Spolsky, Joel. "Things You Should Never Do, Part I." Joel on Software,
  2000. https://www.joelonsoftware.com/2000/04/06/things-you-should-never-do-part-i/,
  verified 2026-08-02.
- Wikipedia contributors. "Strangler fig." Wikipedia, The Free Encyclopedia.
  https://en.wikipedia.org/wiki/Strangler_fig, verified 2026-08-02.

## Code examples

The pattern's core mechanism, at the code level, is the facade's
routing decision, given an incoming request, look up whether the target
route has been migrated, and dispatch to the legacy handler or the new
service accordingly. The three examples below implement that routing core in
different languages, standing in for what a real reverse proxy or API
gateway configuration would do declaratively. Each is a minimal, runnable
simulation, not a production proxy, and each was compiled or run locally
before inclusion.

### TypeScript

```typescript
type Route = string;

interface Backend {
  name: string;
  handle(route: Route): string;
}

class LegacySystem implements Backend {
  name = "legacy";
  handle(route: Route): string {
    return `legacy handled ${route}`;
  }
}

class NewService implements Backend {
  constructor(public name: string) {}
  handle(route: Route): string {
    return `${this.name} handled ${route}`;
  }
}

class StranglerFacade {
  private routingTable = new Map<Route, Backend>();
  constructor(private legacy: Backend) {}

  migrate(route: Route, target: Backend): void {
    this.routingTable.set(route, target);
  }

  dispatch(route: Route): string {
    const target = this.routingTable.get(route) ?? this.legacy;
    return target.handle(route);
  }

  migratedFraction(knownRoutes: Route[]): number {
    const migrated = knownRoutes.filter((r) => this.routingTable.has(r));
    return migrated.length / knownRoutes.length;
  }
}

const legacy = new LegacySystem();
const facade = new StranglerFacade(legacy);
const knownRoutes = ["/orders", "/invoices", "/customers", "/reports"];

console.log(facade.dispatch("/orders"));

facade.migrate("/orders", new NewService("order-service"));
console.log(facade.dispatch("/orders"));
console.log(facade.dispatch("/invoices"));
console.log(`migrated fraction is ${facade.migratedFraction(knownRoutes) * 100}`);
```

Verified with `npx tsc --noEmit` against a standalone file, no type errors,
then run under `node` after transpiling. Output confirmed. `/orders`
dispatches to legacy before migration and to `order-service` after, `/invoices`
remains on legacy, and the migrated fraction reports 25 with one of four
known routes migrated.

### Python

```python
from dataclasses import dataclass, field
from typing import Protocol


class Backend(Protocol):
    name: str

    def handle(self, route: str) -> str: ...


@dataclass
class LegacySystem:
    name: str = "legacy"

    def handle(self, route: str) -> str:
        return f"legacy handled {route}"


@dataclass
class NewService:
    name: str

    def handle(self, route: str) -> str:
        return f"{self.name} handled {route}"


@dataclass
class StranglerFacade:
    legacy: Backend
    routing_table: dict[str, Backend] = field(default_factory=dict)

    def migrate(self, route: str, target: Backend) -> None:
        self.routing_table[route] = target

    def dispatch(self, route: str) -> str:
        target = self.routing_table.get(route, self.legacy)
        return target.handle(route)

    def migrated_fraction(self, known_routes: list[str]) -> float:
        migrated = [r for r in known_routes if r in self.routing_table]
        return len(migrated) / len(known_routes)


if __name__ == "__main__":
    legacy = LegacySystem()
    facade = StranglerFacade(legacy=legacy)
    known_routes = ["/orders", "/invoices", "/customers", "/reports"]

    print(facade.dispatch("/orders"))

    facade.migrate("/orders", NewService("order-service"))
    print(facade.dispatch("/orders"))
    print(facade.dispatch("/invoices"))
    print(f"migrated fraction is {facade.migrated_fraction(known_routes) * 100:.0f}")
```

Run with `python3` directly. Output confirmed. `legacy handled /orders`
before migration, `order-service handled /orders` and `legacy handled
/invoices` after, migrated fraction 25.

### Go

```go
package main

import "fmt"

type Backend interface {
	Name() string
	Handle(route string) string
}

type LegacySystem struct{}

func (LegacySystem) Name() string { return "legacy" }
func (LegacySystem) Handle(route string) string {
	return fmt.Sprintf("legacy handled %s", route)
}

type NewService struct {
	name string
}

func (n NewService) Name() string { return n.name }
func (n NewService) Handle(route string) string {
	return fmt.Sprintf("%s handled %s", n.name, route)
}

type StranglerFacade struct {
	legacy       Backend
	routingTable map[string]Backend
}

func NewStranglerFacade(legacy Backend) *StranglerFacade {
	return &StranglerFacade{legacy: legacy, routingTable: map[string]Backend{}}
}

func (f *StranglerFacade) Migrate(route string, target Backend) {
	f.routingTable[route] = target
}

func (f *StranglerFacade) Dispatch(route string) string {
	if target, ok := f.routingTable[route]; ok {
		return target.Handle(route)
	}
	return f.legacy.Handle(route)
}

func (f *StranglerFacade) MigratedFraction(knownRoutes []string) float64 {
	migrated := 0
	for _, r := range knownRoutes {
		if _, ok := f.routingTable[r]; ok {
			migrated++
		}
	}
	return float64(migrated) / float64(len(knownRoutes))
}

func main() {
	legacy := LegacySystem{}
	facade := NewStranglerFacade(legacy)
	knownRoutes := []string{"/orders", "/invoices", "/customers", "/reports"}

	fmt.Println(facade.Dispatch("/orders"))

	facade.Migrate("/orders", NewService{name: "order-service"})
	fmt.Println(facade.Dispatch("/orders"))
	fmt.Println(facade.Dispatch("/invoices"))
	fmt.Printf("migrated fraction is %.0f\n", facade.MigratedFraction(knownRoutes)*100)
}
```

Run with `go run`. Output confirmed. `legacy handled /orders` before
migration, `order-service handled /orders` and `legacy handled /invoices`
after, migrated fraction 25.

A fourth language, Swift, was attempted for the same routing core but is
omitted from this entry's required set since three languages already satisfy
the minimum and the Go, TypeScript, and Python examples together already
show the pattern's idiomatic shape across a static compiled language, a
statically typed transpiled language, and a dynamically typed language. Java
and Rust toolchains were not confirmed present at authoring time and were
not attempted, per the available-toolchains table in the entry template.
