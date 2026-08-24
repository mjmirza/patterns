---
name: Decompose by Subdomain
slug: decompose-by-subdomain
family: 10-microservices
category: Structural
aliases: [Domain-Oriented Decomposition, DDD-Aligned Service Boundaries, Subdomain-Driven Decomposition]
first_described: "Richardson 2018 (pattern catalog), building on Evans 2003 (DDD subdomains)"
maturity: established
related: [decompose-by-business-capability, strangler-fig, bounded-context, saga, api-gateway, backends-for-frontends]
incompatible_with: [shared-database]
verified: 2026-08-02
---

# Decompose by Subdomain

## 1. Name, aliases, and lineage

The canonical name is **Decompose by Subdomain**. It is documented as one of
two sibling patterns for breaking an application into services in Chris
Richardson's microservices pattern catalog, alongside Decompose by Business
Capability. The catalog page states the intent plainly: define services
corresponding to Domain-Driven Design subdomains
([microservices.io, "Pattern. Decompose by subdomain"](https://microservices.io/patterns/decomposition/decompose-by-subdomain.html),
verified 2026-08-02). Richardson later expanded the same material into a book,
*Microservices Patterns. With examples in Java*, Manning, 2019, where the
decomposition patterns sit in the chapter on decomposition strategies.

The pattern borrows its vocabulary wholesale from Domain-Driven Design. Eric
Evans introduced the idea that a large business domain is not one thing to
model, it is a set of subdomains of differing importance, in Eric Evans,
*Domain-Driven Design. Tackling Complexity in the Heart of Software*,
Addison-Wesley, 2003. The microservices.io catalog page restates Evans'
three-way split directly. **Core subdomain**, the part of the business that
provides competitive advantage and deserves the best engineers and the most
custom code. **Supporting subdomain**, necessary but not differentiating, and
a reasonable candidate for a thinner build. **Generic subdomain**, a solved
problem with no competitive value, and the strong recommendation is to buy or
adopt an existing implementation rather than write one
([microservices.io, "Pattern. Decompose by subdomain"](https://microservices.io/patterns/decomposition/decompose-by-subdomain.html),
verified 2026-08-02).

No alias in the literature calls this pattern anything but variations on
"domain-oriented" or "subdomain-driven" decomposition, but the name is
frequently and incorrectly used as a synonym for Bounded Context. It is not.
A subdomain is a fact about the business, discovered by studying how the
organization actually works, independent of any software. A bounded context
is a fact about the software, a boundary the team draws around one internal
model and one ubiquitous language. Martin Fowler is explicit that DDD gives up
on a single unified model for a whole system and instead accepts multiple
models, each valid inside its own boundary
([Martin Fowler, "BoundedContext"](https://martinfowler.com/bliki/BoundedContext.html),
15 January 2014, verified 2026-08-02). The healthy case is one bounded context
implementing one subdomain, but the two ideas answer different questions, one
is discovered, the other is designed, and conflating them is the single most
common source of confusion when teams first try to apply this pattern. Dimension
11 returns to what goes wrong when the two drift apart.

## 2. Problem and context

A team owns a system that has grown past the point where one deployable, one
shared database, and one release train can move at the speed the business
needs. The usual trigger is not code size on its own. It is that unrelated
parts of the business now have to change on unrelated schedules, and every
change still has to pass through the same build, the same regression suite,
and the same release calendar, so a marketing team's pricing experiment and a
finance team's tax-rule fix contend for the same deploy window and the same
merge queue.

The team has already decided to split the system, and the real question in
front of them is where the cuts go. Two decompositions are available and they
disagree. A cut along **technical layers** produces a UI team, a
business-logic team, and a database team, each shipping a slice of every
feature and none of them able to ship anything alone, because a single user
story crosses every layer. A cut along **business capability or subdomain**
produces a team that owns everything needed to deliver one piece of business
value end to end, front to back, including its own data. Martin Fowler frames
this exact contrast as the layer-first instinct that produces slow,
cross-team, everything-touches-everything work against the microservice
instinct to organize around capability instead
([Martin Fowler, "Microservices"](https://martinfowler.com/articles/microservices.html),
25 March 2014, verified 2026-08-02).

Decompose by Subdomain answers the "where do the cuts go" question with a
specific, repeatable method rather than an intuition. Study the business, not
the org chart and not the existing code, find the subdomains the business
already has whether anyone wrote them down or not, and let each service
boundary follow a subdomain boundary. The context in which this pattern earns
its keep is a domain that is genuinely heterogeneous, some parts of it are
where the company makes its money and deserve investment, other parts are
necessary plumbing that any competitor also has, and a few parts are commodity
concerns better bought than built. A domain that is small, uniform, or still
being discovered does not have stable subdomains to decompose along, and
applying this pattern there produces boundaries that will be wrong within a
quarter.

## 3. Forces

**Team autonomy against cross-team coordination.** A subdomain-shaped service
lets one team own the business logic, the schema, and the deploys for a
complete piece of business capability, which is the whole point. The cost is
that anything that genuinely spans two subdomains, a promotion that touches
both pricing and inventory, now needs two teams to agree on a contract instead
of one team touching two files.

**Stability against discoverability.** Subdomains change slowly because they
track the business itself, and the business changes slower than the code.
Richardson's catalog cites this as a chief benefit, services stay relatively
stable even while the application built on them evolves rapidly
([microservices.io, "Pattern. Decompose by subdomain"](https://microservices.io/patterns/decomposition/decompose-by-subdomain.html),
verified 2026-08-02). The cost is upfront. Finding the real subdomains
requires business understanding that a purely technical reading of the
codebase will not give you, and getting it wrong early is expensive to unwind
later, because by the time the mistake is visible, several teams and several
databases have grown around the wrong line.

**Cohesion against granularity.** A well-drawn subdomain groups things that
change together and separates things that do not, which is Constantine and
Yourdon's coupling and cohesion argument applied at the service level rather
than the module level. The competing pressure is that subdomains do not come
pre-sized. Order Management might be one subdomain the size of ten
microservices at one company and a single service at another, and there is no
formula that hands you the right granularity, only judgement against the team
that will own the result.

**Consistency against availability.** Once the business logic that used to
share one database now lives in two or three subdomain-owned databases, any
operation that used to be one local transaction becomes a distributed one. The
pattern trades the strong consistency a monolith gets almost for free against
the independent scaling, independent failure, and independent deployment that
subdomain-owned data makes possible. This is the same trade every data
decomposition in this family makes, and it is why Decompose by Subdomain is
never adopted alone. See dimension 13 for the patterns that absorb the cost.

**Cost of change against cost of coordination.** A generic subdomain, in
Evans' framing, is explicitly not worth custom engineering investment. The
force here is organizational, not technical. Building it in-house anyway
because "it is easier to keep it in the monolith for now" quietly converts
engineering time that should go to the core subdomain into maintenance of a
solved problem, and that opportunity cost rarely shows up on anyone's
dashboard.

**Team topology against Conway's Law.** Decompose by Subdomain only produces
autonomous teams when the org chart is redrawn to match the subdomain map.
Fowler's article on microservices ties the business-capability cut directly to
cross-functional teams sized for independent ownership, citing Amazon's
"two-pizza team" sizing as a norm that grew up alongside this style of
decomposition
([Martin Fowler, "Microservices"](https://martinfowler.com/articles/microservices.html),
25 March 2014, verified 2026-08-02). A subdomain map imposed on a team
structure that stays organized by technical layer produces service boundaries
nobody actually owns end to end, and Conway's Law reasserts itself, the
software boundary drifts back toward the communication boundary that already
exists.

## 4. Applicability and non-applicability

Reach for Decompose by Subdomain when the following hold together, not in
isolation.

- The business itself is heterogeneous enough to have a real core subdomain,
  the part that differentiates the company, sitting alongside supporting and
  generic subdomains that everyone in the industry needs and nobody
  differentiates on.
- The team has, or can get, genuine domain expertise. Someone in the room can
  explain how the business actually works well enough to argue about where a
  capability belongs, not just how the current code happens to be organized.
- The organization is willing to restructure teams to match the subdomain
  map, because a subdomain-shaped service with a layer-shaped team behind it
  reverts to the coordination problem this pattern exists to remove.
- The system is large enough, or growing fast enough, that a single shared
  model and a single release train are already visibly the bottleneck, not a
  theoretical future one.
- Data ownership can plausibly follow the same boundary, so each subdomain
  service can own its schema rather than reading and writing tables another
  team considers theirs.

Do NOT reach for it when any of these hold.

- **The domain is not yet understood.** A brand new product, a prototype, or
  an early-stage startup exploring product-market fit does not have stable
  subdomains, because nobody yet knows which parts of the business will turn
  out to matter. Drawing service boundaries before the domain model has
  settled locks in guesses that will be expensive to change once data and
  deploy pipelines exist on both sides of the line.
- **The team is small enough to fit around one table.** The coordination cost
  this pattern removes only exists once there are enough people that
  cross-team communication has real overhead. A team of four gains nothing
  from service boundaries that exist only to avoid talking to each other,
  because there is no one else to avoid talking to.
- **The organization cannot or will not restructure around the subdomains.**
  If the team topology is fixed by policy, budget, or history, imposing a
  subdomain-shaped service architecture on it produces the layered-team
  problem again, now with network calls between the layers instead of
  function calls.
- **Read and write patterns cross subdomain lines constantly and cheaply
  inside a single transaction today.** If most business operations already
  need strong consistency across what would become two services, subdomain
  decomposition forces every one of those operations to become a distributed
  transaction or an eventually-consistent saga, and that cost has to be worth
  paying, not merely tolerated.
- **The goal is a technical split, not a business one.** Splitting off an
  authentication service, a caching layer, or a search index is a legitimate
  thing to do, but it is Decompose by Business Capability or plain
  infrastructure extraction, not this pattern. Forcing every technical
  extraction through subdomain language produces subdomains that map to
  nothing a business stakeholder would recognize.

## 5. Structure

**Business Domain.** The whole area of business activity the software
supports. Not itself a software artifact, the reference point everything else
is measured against.

**Subdomain.** A discovered, not designed, division of the business domain.
Identified by studying how the business actually operates, not the code.
Classified as Core, Supporting, or Generic.

**Core Subdomain.** The subdomain that carries the company's competitive
advantage. Receives the most senior engineering attention and the most custom
modeling effort, because this is the part a competitor cannot buy off the
shelf.

**Supporting Subdomain.** Necessary to the business, not itself
differentiating. Built with a level of investment proportional to its
importance, often simpler and more conventional than the core.

**Generic Subdomain.** A solved problem with no competitive value attached to
solving it uniquely. The recommended treatment is to adopt an existing product
or service rather than build custom software, per the microservices.io
catalog's explicit guidance
([microservices.io, "Pattern. Decompose by subdomain"](https://microservices.io/patterns/decomposition/decompose-by-subdomain.html),
verified 2026-08-02).

**Subdomain-Aligned Service.** The unit this pattern actually produces. One
deployable, one owned data store, one team, implementing one subdomain, ideally
sitting inside its own bounded context so the model does not have to serve two
masters.

**Owning Team.** The people responsible for a subdomain-aligned service end to
end, sized so that the team can plausibly hold the whole subdomain in its
collective head, a rough target Richardson's catalog names as the classic
"two pizza" range of roughly six to ten people
([microservices.io, "Pattern. Decompose by subdomain"](https://microservices.io/patterns/decomposition/decompose-by-subdomain.html),
verified 2026-08-02).

**Integration Contract.** The interface, event schema, or API through which
one subdomain-aligned service talks to another. The only thing that is allowed
to cross the boundary, because the whole point of the boundary is that
internals on either side stay private.

## 6. ASCII structure diagram

```
                     Business Domain
        (studied, not designed. exists whether modeled or not)
                            |
        +-------------------+-------------------+
        |                   |                   |
  Core Subdomain     Supporting Subdomain   Generic Subdomain
 (competitive edge)   (necessary, plain)    (solved elsewhere)
        |                   |                   |
        v                   v                   v
 +---------------+   +---------------+   +------------------+
 | Order Service |   | Catalog       |   | Shipping Adapter |
 | (owning team) |   | Service       |   | (wraps a bought  |
 |               |   | (owning team) |   | carrier product) |
 | owned schema  |   | owned schema  |   | no custom schema |
 +-------+-------+   +-------+-------+   +---------+--------+
         |                   |                     |
         |   Integration Contract (API / event)     |
         +-----------------------+-------------------+
                                 |
                        No shared database.
                No service reads another's internal tables.
```

## 7. Dynamics

The pattern is used twice, once at design time to draw the boundaries, and
continuously at runtime as the resulting services collaborate. Both matter.

**Design-time dynamics, the domain-to-service mapping.**

```
1. Interview the business, not the codebase.
      "What are the distinct areas of activity here,
       and which one makes us money that a competitor cannot copy."

2. Classify each candidate as Core, Supporting, or Generic.

3. For each subdomain, ask. Does this need its own model,
   its own team, its own release cadence.
      yes -> candidate service boundary
      no  -> fold into a neighboring subdomain's service

4. Check the classification against the org chart.
      subdomain has no plausible owning team -> restructure the
      team map, or do not split yet.

5. Draw the integration contracts between the resulting
   services BEFORE writing code inside any of them.
```

**Runtime dynamics, a cross-subdomain business operation.**

```
Client            Order Service          Catalog Service     Shipping Adapter
  |  place order        |                       |                    |
  |--------------------->                       |                    |
  |                      | GET product snapshot  |                    |
  |                      |----------------------->                   |
  |                      |     price, availability|                   |
  |                      |<-----------------------|                   |
  |                      | order created locally  |                    |
  |                      | (owns its own schema)  |                    |
  |                      | publish OrderPlaced    |                    |
  |                      |------------------------------------------->|
  |                      |                       |    schedule pickup |
  |                      |                       |    (via bought API)|
  |   order confirmed    |                       |                    |
  |<---------------------|                       |                    |
```

Note what does not happen. The Order Service never opens a connection to the
Catalog Service's database, and the Shipping Adapter never receives a full
domain object from Order, only the fields the integration contract defines.
Each arrow crosses a subdomain boundary through a narrow, versioned interface,
which is the property this pattern exists to create.

## 8. Implementation variants

**Green-field subdomain-first.** The team maps subdomains before any code
exists and stands up one deployable per subdomain from day one. Cleanest
outcome, rarest in practice, because it requires domain understanding the team
usually does not have until the product has been live for a while.

**Modular monolith rehearsal.** The team keeps one deployable but enforces
subdomain boundaries as internal module boundaries, one package per subdomain,
no cross-module reach into another module's internal types, integration only
through a small exported interface. This is the variant demonstrated in the
code examples below. It lets a team validate the subdomain map, catch a wrong
boundary while the cost of fixing it is a package rename, and defer the
distributed-systems cost until the boundaries have proven stable. Sam Newman
recommends exactly this staged approach when the domain model is not yet
trustworthy enough to commit to network boundaries, in Sam Newman, *Monolith
to Microservices*, O'Reilly, 2019, in the chapters on splitting the monolith
incrementally.

**Strangler-driven extraction.** An existing monolith is decomposed
incrementally, one subdomain at a time, routing traffic for the extracted
subdomain to a new service while the rest continues to be served by the
monolith. See the Strangler Fig entry for the routing mechanics this variant
depends on.

**Domain grouping with layered dependency rules.** Rather than one service per
subdomain, subdomains are grouped into layers with a strict dependency
direction, infrastructure at the bottom, product-specific logic at the top,
and services within a layer may only depend downward. This is the shape Uber
adopted at scale, see dimension 9.

**Generic subdomain as a wrapper, not a build.** The generic subdomain is
implemented as a thin adapter around a purchased product or third-party API
rather than as custom domain logic, so the "service" is mostly an anti-
corruption layer translating between the vendor's model and the rest of the
system's model.

**Language note.** This pattern is architectural, not syntactic, so it has no
language-specific shape the way a design pattern like Factory Method does. The
distinguishing choice by language ecosystem is how the module boundary is
enforced before it becomes a network boundary. Go enforces it with unexported
identifiers and internal packages, Rust with `pub(crate)` visibility and
workspace crates, Java with module boundaries in the module system or simply
package-private types, TypeScript and Python with convention and lint rules
since neither has a hard compiler-enforced internal-package concept by
default.

## 9. Known production uses

**Uber, Domain-Oriented Microservice Architecture (DOMA).** Uber classified
more than 2,200 existing microservices into roughly 70 domains, where a domain
is defined as a collection of one or more microservices tied to a logical
grouping of business functionality, with domain size varying from a single
service to dozens. The architecture layers domains by dependency direction and
reports onboarding time reduced by 25 to 50 percent and platform support costs
reduced by an order of magnitude after adoption. Uber Engineering Blog,
"Introducing Domain-Oriented Microservice Architecture", 23 July 2020,
https://www.uber.com/blog/microservice-architecture/ verified 2026-08-02.

**SoundCloud, splitting the Mothership monolith along Bounded Contexts.**
SoundCloud's engineering team described separating domain logic into small
components, each exposing a well-defined API and implementing a Bounded
Context, as the mechanism for pulling new functionality out of their Rails
monolith, referring readers directly to Martin Fowler's definition of the term
they were applying. Phil Calçado, SoundCloud Developers Blog, "Building
Products at SoundCloud, Part 1. Dealing with the Monolith", 11 June 2014,
https://developers.soundcloud.com/blog/building-products-at-soundcloud-part-1-dealing-with-the-monolith
verified 2026-08-02.

**Amazon, capability-owning two-pizza teams.** Amazon is documented as
organizing service boundaries around business capability and sizing the
owning team so it can be fed by two pizzas, a norm widely cited as the origin
of the small, autonomous, full-stack-ownership team shape that subdomain and
capability decomposition both depend on for their claimed benefits. This is
the sibling pattern, Decompose by Business Capability, rather than a strict
DDD-subdomain exercise, and the two are frequently blended in practice, which
is itself evidence for how closely related the patterns are. Martin Fowler,
"Microservices", 25 March 2014,
https://martinfowler.com/articles/microservices.html verified 2026-08-02.

## 10. Consequences

**Positive.**

- Service boundaries track business reality instead of an accident of the
  existing codebase, which the microservices.io catalog names as the source
  of the pattern's architectural stability, because subdomains change more
  slowly than the software layered on top of them
  ([microservices.io, "Pattern. Decompose by subdomain"](https://microservices.io/patterns/decomposition/decompose-by-subdomain.html),
  verified 2026-08-02).
- Teams gain end-to-end ownership of a complete piece of business value,
  which removes the layer-crossing coordination tax Fowler describes as the
  characteristic failure mode of technically layered organizations
  ([Martin Fowler, "Microservices"](https://martinfowler.com/articles/microservices.html),
  25 March 2014, verified 2026-08-02).
- Investment concentrates where it earns the most, senior engineering effort
  on the core subdomain, adequate but unglamorous effort on supporting
  subdomains, and a buy decision on generic ones, instead of every part of the
  domain receiving uniform, undifferentiated attention.
- At scale it produces a legible map of the system. Uber's own account
  describes classifying thousands of services into domains as the step that
  made onboarding and cross-team reasoning tractable again
  ([Uber Engineering Blog](https://www.uber.com/blog/microservice-architecture/),
  23 July 2020, verified 2026-08-02).

**Negative.**

- Finding the real subdomains is genuinely hard and requires business
  knowledge many engineering teams do not have on day one, and a wrong
  classification is expensive to correct once teams, deploy pipelines, and
  databases have grown around it.
- What used to be in-process calls and local transactions inside one
  deployable become network calls and distributed transactions across
  services, with all the latency, partial-failure, and consistency cost that
  implies.
- Data that once lived in one normalized schema is now duplicated or
  denormalized across subdomain boundaries, and keeping those copies
  consistent is ongoing work, not a one-time migration cost.
- The pattern only pays off when the organization restructures around it. A
  subdomain map with no matching team structure produces service boundaries
  that are subdomain-shaped on a diagram and layer-shaped in practice, because
  the people who actually own the work are still organized the old way.
- Operational surface area multiplies. Each subdomain-aligned service needs
  its own deployment pipeline, its own on-call rotation, and its own
  observability, which is a real ongoing cost the pattern trades against the
  coordination cost it removes.

## 11. Failure modes and misuse

**Symptom.** Two services constantly need to change together, and every
release requires coordinating a deploy order between them.
**Cause.** The boundary was drawn along an org-chart line or a technology
line, not a genuine subdomain line, so what looks like two subdomains on the
diagram is actually one subdomain that got split in half.
**Fix.** Re-run the subdomain discovery exercise against actual business
behavior rather than the existing team structure, and merge the two services
back into one if the coupling turns out to be intrinsic to the underlying
business capability rather than accidental.

**Symptom.** The "subdomain" services all still read and write the same
shared database, just from different codebases.
**Cause.** The team drew the service boundary before deciding on the data
boundary, so the code was split but the schema was not, which leaves every
implicit coupling the shared database used to hide fully intact, now hidden
behind a network hop instead of a function call.
**Fix.** Give each subdomain-aligned service its own schema, migrate data
ownership one table at a time, and replace direct cross-schema reads with the
integration contract, an API call or a published event, even where that
requires accepting eventual consistency the shared database used to provide
for free.

**Symptom.** A subdomain is confused with a bounded context, and the team
builds exactly one bounded context per discovered subdomain even where the
subdomain is large and internally heterogeneous.
**Cause.** Treating "subdomain" and "bounded context" as synonyms, when Evans
and Fowler both treat them as related but distinct, a subdomain is discovered
from the business, a bounded context is a modeling boundary the team chooses,
and a single large subdomain can legitimately be served by more than one
bounded context, or occasionally by a bounded context that spans parts of two
adjacent subdomains during a transition period.
**Fix.** Model the bounded contexts on their own merits, informed by the
subdomain map but not mechanically copied from it, and treat a mismatch
between the two as a normal, expected outcome of modeling rather than a bug to
eliminate.

**Symptom.** A generic subdomain, something like tax calculation or address
validation, has its own dedicated team writing and maintaining custom code
year after year, with no competitive benefit to show for it.
**Cause.** The team never applied the "buy, do not build" guidance the pattern
explicitly carries for generic subdomains, often because the initial build was
cheap and switching later feels riskier than it is.
**Fix.** Replace the custom generic-subdomain service with a thin adapter
around a bought product or hosted API, and redirect the engineering capacity
that used to maintain it toward the core subdomain, where the same effort
earns a competitive return instead of maintaining a solved problem.

**Symptom.** A cross-subdomain business operation regularly ends up half
completed, an order is recorded but payment never clears, or inventory is
reserved but the order is never confirmed.
**Cause.** The team decomposed the services correctly but did not replace the
local transaction the monolith used to provide with an explicit distributed
transaction strategy, so a partial failure across the new service boundary
silently leaves the system in an inconsistent state.
**Fix.** Introduce an explicit Saga to coordinate the multi-service operation
with defined compensating actions, rather than hoping every downstream call
succeeds. See the Saga entry.

**Symptom.** Two teams cannot agree on whose subdomain owns a capability, and
the disagreement recurs every quarter with a different answer each time.
**Cause.** The capability genuinely sits on the seam between two subdomains,
which is common and not itself a failure, but the team never made an explicit,
written ownership decision, so the ambiguity resurfaces every time either team
wants to change the behavior.
**Fix.** Make an explicit, documented ownership call, even an imperfect one,
and record the contract at the seam so both teams can build against a fixed
interface instead of relitigating the boundary on every change.

## 12. Trade-off matrix

| Force | Decompose by Subdomain | Decompose by Business Capability | Layered monolith (no split) | Decompose by team size alone |
|---|---|---|---|---|
| Boundary source | Discovered from the business domain model, DDD-flavored | Discovered from what the business does operationally | None, one deployable | Arbitrary, matches current headcount |
| Stability of boundary over time | High, subdomains change slowly | Moderate, capabilities can be reorganized more often than the underlying subdomains that motivate them | Not applicable, no boundary | Low, boundary shifts every reorg |
| Requires deep domain modeling upfront | Yes, this is the main cost | Less, capability lists are easier to enumerate than subdomain classification | No | No |
| Team autonomy achieved | High, once org matches the map | High | Low, everyone shares the release train | Superficial, teams own arbitrary slices |
| Data consistency across a business operation | Requires sagas or eventual consistency across services | Same as subdomain decomposition, both split data ownership | Strong, one local transaction | Same distributed-consistency cost, without the benefit of a principled boundary |
| Risk of a wrong boundary being expensive to fix | High if data has already diverged | Moderate, capability lists are easier to revise than a domain model | Not applicable | High, and the boundary was arbitrary to begin with |
| Best fit | Mature domain with a clear core, supporting, and generic split | Domain where "what we do" is clearer than "what our essential business concepts are" | Small system, small team, uniform domain | Never a deliberate choice, a symptom to fix |

## 13. Related and incompatible patterns

**Decompose by Business Capability.** The direct sibling pattern and the most
common point of confusion. Both split a monolith into services along
business-driven lines rather than technical layers, and in practice the two
overlap heavily, a well-run capability inventory and a well-run subdomain
analysis often land on nearly the same service list. The difference is
methodology, business capability decomposition asks what the organization
does, subdomain decomposition asks what distinct areas of knowledge and
competitive advantage the business domain contains, per the DDD framing. Teams
frequently use one to sanity-check the other rather than choosing exactly one.

**Bounded Context.** Not the same idea, closely coupled in practice. A
subdomain is what you find by studying the business. A bounded context is the
modeling and implementation boundary the team chooses in response, and the
healthy target is one bounded context per subdomain-aligned service, though
the mapping is not required to be one-to-one. See dimension 11 for what goes
wrong when the two are treated as interchangeable.

**Strangler Fig.** The incremental extraction mechanism most teams use to get
from an existing monolith to subdomain-aligned services without a rewrite.
Decompose by Subdomain answers where the cuts go, Strangler Fig answers how to
move traffic across the cut safely, one subdomain at a time, while the
monolith continues to serve everything not yet extracted.

**Saga.** Once data ownership follows subdomain boundaries, a business
operation that used to be one local transaction across several tables becomes
a sequence of calls across several services, and Saga is the pattern that
coordinates that sequence with compensating actions instead of relying on a
distributed transaction the boundary no longer allows.

**API Gateway and Backends for Frontends.** Once subdomain-aligned services
exist, a client that needs data assembled from more than one of them needs
somewhere to do that assembly. These two patterns are the usual answer, and
neither one is optional once the decomposition has actually happened, because
without them every client has to know the full service topology itself.

**Shared Database, incompatible.** Decompose by Subdomain explicitly assumes
each subdomain-aligned service owns its own schema. A shared database across
service boundaries reintroduces the exact coupling the decomposition was meant
to remove, now with the added cost of a distributed deployment on top of it,
which is why the pattern lists Shared Database as incompatible rather than
merely undesirable.

## 14. Refactoring path in and out

**Path in, from a monolith.**

1. Run a domain-modeling exercise against the actual business, not the
   existing code, and produce a first-pass list of candidate subdomains
   classified as core, supporting, or generic.
2. Cross-check the candidate list against the current org chart and identify
   which subdomains already have a plausible owning team and which do not.
3. Enforce the candidate subdomain boundaries as internal module boundaries
   inside the existing monolith first, one package per subdomain, with all
   cross-module access going through a small exported interface, matching the
   modular-monolith variant in dimension 8. Let the team live with this shape
   long enough to find the boundaries that were wrong.
4. Give each internal module its own tables inside the shared database, and
   replace any remaining cross-module SQL join with a call through the
   exported interface, so the schema boundary matches the module boundary
   before it has to match a network boundary.
5. Extract one subdomain at a time into its own deployable and its own
   database using a Strangler Fig, starting with whichever subdomain has the
   fewest remaining direct dependencies on the others, so the first extraction
   is the cheapest one to validate the process.
6. For every operation that now crosses a service boundary and used to be a
   local transaction, introduce an explicit Saga with compensating actions
   before removing the monolith's version of that operation.
7. Repeat extraction, subdomain by subdomain, re-validating the subdomain map
   against real usage after each extraction rather than committing to the
   entire original map upfront.

**Path out, when a subdomain-aligned service stops earning its place.**

1. This usually happens when a subdomain that was split out turns out to be
   too small or too tightly coupled to a neighbor to justify its own
   deployment, team, and database, an over-decomposition rather than a
   modeling failure.
2. Confirm the direction of the merge, which subdomain absorbs which, using
   the same core, supporting, generic classification used to split them
   originally, so the merge target is the more central subdomain of the pair.
3. Fold the smaller service's schema into the target service's database as a
   set of new tables it owns, rather than merging table by table into
   existing ones, preserving the internal module boundary even after the
   deployable boundary disappears.
4. Route the smaller service's API calls to internal calls inside the target
   service, retire its deployment pipeline, and keep the old module boundary
   in code for a release or two before deleting it, in case the merge needs
   to be reversed.
5. Update the subdomain map and the team's ownership documentation
   immediately, because a stale subdomain map is worse than none, it actively
   misleads the next person who tries to extract a service along the old,
   now-incorrect line.

## 15. Testing and verification

Subdomain decomposition makes each service's own business logic easier to test
in isolation, because a subdomain-aligned service has a narrower, more
coherent domain model than a slice of a monolith did, and its unit tests no
longer need to set up unrelated parts of the system to exercise one behavior.
That gain is real and it is also the easy part.

What becomes harder is everything that used to be verified implicitly by a
single process and a single transaction. Contract tests at each integration
boundary, verifying the schema of a request or an event against what the
consuming service actually expects, are not optional once two teams can change
their side of an integration independently, because a passing test suite
inside one service says nothing about whether the other service's assumptions
still hold. Consumer-driven contract testing, where the consuming team
publishes the shape of the interaction it depends on and the providing team
runs that contract in its own pipeline before every release, is the standard
technique for catching a breaking change before it reaches a shared
environment.

Cross-subdomain business operations need their own test layer above the
per-service unit tests, exercising the full saga or workflow across real or
faked service boundaries, including the failure paths, what happens when the
payment call times out after inventory has already been reserved, because
those failure paths are exactly what a per-service unit test cannot see.

Test doubles change shape too. Where a monolith's tests could construct a
real, in-process instance of another module, a subdomain-aligned service's
tests need a fake or a stub for the services on the other side of its
integration contracts, and that stub has to be kept honest against the real
contract, which is what the contract tests above are for. A stub that has
quietly drifted from the real service's behavior is worse than no stub, it
produces a green test suite over a broken integration.

## 16. Observability signals

Each subdomain-aligned service should expose the standard health and
throughput signals for its own runtime, request rate, error rate, latency
percentiles, and resource saturation, scoped to that service alone so an
on-call engineer for one subdomain never has to read another subdomain's
dashboard to diagnose their own service.

The signal specific to this pattern is at the boundary, not inside any one
service. Distributed tracing across an operation that crosses subdomain
boundaries is the primary tool for seeing whether the decomposition is
actually working, because a trace that shows an order-placement operation
touching Catalog, then Order, then Shipping, with a clear parent-child span
structure and no unexpected hops back through a shared database, is direct
evidence the boundaries hold at runtime the way they were drawn on the
diagram.

A healthy subdomain map shows up as low cross-service call fan-out for most
operations, most requests to one subdomain's service stay inside that service
or make a small, stable number of calls to a small, stable set of neighbors,
and as saga completion rates near the successful path, with compensating
actions firing rarely and being visible and alertable when they do.

An unhealthy subdomain map shows up as chatty cross-service traffic where a
single client-facing operation fans out into dozens of calls across many
services, as a small number of services that appear in almost every trace
regardless of what the operation is, which usually means a subdomain was
split too finely or a shared, generic concern was never properly extracted,
and as data drift between duplicated fields across services, caught by
comparing an event-derived read model in one service against the
system-of-record value in the owning service and alerting on divergence.

## 17. Security and privacy implications

This dimension is largely engineering judgement, drawn from how data ownership
and integration boundaries in this pattern change the attack surface, rather
than from a single citable source.

Subdomain-aligned data ownership is a genuine privacy benefit when it is done
well. Personal data that belongs conceptually to one subdomain, a customer's
payment instrument inside a Payments subdomain, for example, can be stored,
access-controlled, and audited in one place, with every other subdomain
receiving only the minimum it needs, a payment token rather than a card
number, through the integration contract. That is a stronger data-minimization
posture than a monolith's single shared schema usually achieves in practice,
because the monolith's schema tends to accumulate broad read access to
everything over time as more code gets written against it.

The same boundary is also where new risk enters. Each integration contract
between subdomains is a network-exposed surface that did not exist inside a
monolith, and it needs its own authentication, authorization, and input
validation, independent of whatever the caller already proved to its own
users, because a compromised or misbehaving caller on one side of the boundary
should not be able to reach past the contract into the callee's internals.
Service-to-service authentication, typically mutual TLS or short-lived tokens
scoped to the specific interaction, is a required addition this pattern
creates a need for, not an optional hardening step.

Data duplication across subdomain boundaries, the denormalized copies that
replace what used to be a single-source-of-truth table, multiplies the number
of places a sensitive field lives, and each copy needs the same retention,
deletion, and access-control policy as the original, or a deletion request
handled correctly in the owning subdomain can leave the same personal data
sitting untouched in a downstream copy the deletion process never reached.

Finally, the observability signals in dimension 16, especially distributed
tracing, themselves carry data across subdomain boundaries by design, and
trace payloads that carelessly include personal data in span attributes turn
the tracing system into an unintended second copy of sensitive fields, spread
across every service the trace passes through.

## 18. References

1. Chris Richardson, microservices.io, "Pattern. Decompose by subdomain",
   https://microservices.io/patterns/decomposition/decompose-by-subdomain.html
   verified 2026-08-02.
2. Chris Richardson, microservices.io, "Pattern. Decompose by business
   capability",
   https://microservices.io/patterns/decomposition/decompose-by-business-capability.html
   verified 2026-08-02.
3. Chris Richardson, *Microservices Patterns. With examples in Java*, Manning
   Publications, 2019, chapter on decomposition strategies.
4. Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*, Addison-Wesley, 2003.
5. Martin Fowler, "BoundedContext",
   https://martinfowler.com/bliki/BoundedContext.html, published 15 January
   2014, verified 2026-08-02.
6. Martin Fowler, "Microservices",
   https://martinfowler.com/articles/microservices.html, published 25 March
   2014, verified 2026-08-02.
7. Sam Newman, *Monolith to Microservices*, O'Reilly Media, 2019, chapters on
   splitting the monolith incrementally.
8. Uber Engineering Blog, "Introducing Domain-Oriented Microservice
   Architecture", https://www.uber.com/blog/microservice-architecture/,
   published 23 July 2020, verified 2026-08-02.
9. Phil Calçado, SoundCloud Developers Blog, "Building Products at
   SoundCloud, Part 1. Dealing with the Monolith",
   https://developers.soundcloud.com/blog/building-products-at-soundcloud-part-1-dealing-with-the-monolith,
   published 11 June 2014, verified 2026-08-02.

## Code examples

The three examples below implement the same decomposition, a small e-commerce
domain split into a Catalog subdomain, an Order subdomain, and a Delivery
subdomain wrapping a bought shipping capability, using the modular-monolith
rehearsal variant from dimension 8. Each subdomain owns its own model of the
concepts it cares about, none of them share an internal type, and all
cross-subdomain interaction goes through a small, explicit interface, the
integration contract from dimension 5. This is deliberately not a
multi-process network example, because the pattern's essential property, the
model and ownership boundary, is fully demonstrable in one process, and a
faked network call would only add incidental complexity without adding
anything to what the pattern is teaching.

### Go

```go
package main

import "fmt"

// Catalog subdomain owns its own model of a product.
type CatalogProduct struct {
	SKU   string
	Price int
	InStock bool
}

type Catalog struct {
	products map[string]CatalogProduct
}

func NewCatalog() *Catalog {
	return &Catalog{products: map[string]CatalogProduct{
		"WIDGET-1": {SKU: "WIDGET-1", Price: 1999, InStock: true},
	}}
}

// ProductSnapshot is the integration contract, the only thing
// Catalog ever hands to another subdomain.
type ProductSnapshot struct {
	SKU   string
	Price int
}

func (c *Catalog) Lookup(sku string) (ProductSnapshot, error) {
	p, ok := c.products[sku]
	if !ok || !p.InStock {
		return ProductSnapshot{}, fmt.Errorf("catalog: %s not available", sku)
	}
	return ProductSnapshot{SKU: p.SKU, Price: p.Price}, nil
}

// CatalogLookup is the port the Order subdomain depends on.
// Order never imports Catalog's internal type CatalogProduct.
type CatalogLookup interface {
	Lookup(sku string) (ProductSnapshot, error)
}

// Order subdomain owns its own model of a line item, distinct
// from CatalogProduct even though both describe "a product".
type LineItem struct {
	SKU      string
	UnitCents int
}

type Order struct {
	ID    string
	Items []LineItem
}

type OrderService struct {
	catalog CatalogLookup
}

func NewOrderService(catalog CatalogLookup) *OrderService {
	return &OrderService{catalog: catalog}
}

func (s *OrderService) PlaceOrder(id string, skus []string) (Order, error) {
	order := Order{ID: id}
	for _, sku := range skus {
		snap, err := s.catalog.Lookup(sku)
		if err != nil {
			return Order{}, err
		}
		order.Items = append(order.Items, LineItem{SKU: snap.SKU, UnitCents: snap.Price})
	}
	return order, nil
}

func main() {
	catalog := NewCatalog()
	orders := NewOrderService(catalog)

	order, err := orders.PlaceOrder("ord-1", []string{"WIDGET-1"})
	if err != nil {
		fmt.Println("failed:", err)
		return
	}
	fmt.Printf("order %s has %d line item(s), first unit price %d cents\n",
		order.ID, len(order.Items), order.Items[0].UnitCents)
}
```

### Python

```python
from dataclasses import dataclass
from typing import Protocol


# Delivery subdomain is generic. It wraps a bought carrier API
# rather than modeling shipping logic itself.
@dataclass(frozen=True)
class ShipmentRequest:
    order_id: str
    weight_grams: int


class CarrierProvider(Protocol):
    def schedule_pickup(self, request: ShipmentRequest) -> str: ...


class ThirdPartyCarrierAdapter:
    """Anti-corruption layer around a fictional bought carrier API."""

    def schedule_pickup(self, request: ShipmentRequest) -> str:
        return f"CARRIER-TRACKING-{request.order_id}"


class DeliveryService:
    def __init__(self, carrier: CarrierProvider) -> None:
        self._carrier = carrier

    def ship(self, order_id: str, weight_grams: int) -> str:
        request = ShipmentRequest(order_id=order_id, weight_grams=weight_grams)
        return self._carrier.schedule_pickup(request)


# Order subdomain, unaware of the carrier's internal request shape.
@dataclass
class ConfirmedOrder:
    order_id: str
    tracking_number: str


def confirm_and_ship(order_id: str, weight_grams: int, delivery: DeliveryService) -> ConfirmedOrder:
    tracking = delivery.ship(order_id, weight_grams)
    return ConfirmedOrder(order_id=order_id, tracking_number=tracking)


if __name__ == "__main__":
    delivery = DeliveryService(ThirdPartyCarrierAdapter())
    confirmed = confirm_and_ship("ord-42", weight_grams=450, delivery=delivery)
    print(f"order {confirmed.order_id} shipped, tracking {confirmed.tracking_number}")
```

### TypeScript

```typescript
// Order subdomain publishes a domain event. It does not know,
// and does not import, anything from the Delivery subdomain.
interface OrderPlaced {
  kind: "OrderPlaced";
  orderId: string;
  skus: string[];
}

type DomainEvent = OrderPlaced;

interface EventBus {
  publish(event: DomainEvent): void;
  subscribe(handler: (event: DomainEvent) => void): void;
}

class InProcessEventBus implements EventBus {
  private handlers: Array<(event: DomainEvent) => void> = [];

  publish(event: DomainEvent): void {
    for (const handler of this.handlers) {
      handler(event);
    }
  }

  subscribe(handler: (event: DomainEvent) => void): void {
    this.handlers.push(handler);
  }
}

class OrderService {
  constructor(private readonly bus: EventBus) {}

  placeOrder(orderId: string, skus: string[]): void {
    this.bus.publish({ kind: "OrderPlaced", orderId, skus });
  }
}

// Delivery subdomain owns its own model, a Shipment, unrelated
// to Order's LineItem or Catalog's product model.
interface Shipment {
  orderId: string;
  trackingNumber: string;
}

class DeliverySubscriber {
  public shipments: Shipment[] = [];

  constructor(bus: EventBus) {
    bus.subscribe((event) => {
      if (event.kind === "OrderPlaced") {
        this.shipments.push({
          orderId: event.orderId,
          trackingNumber: `TRACK-${event.orderId}`,
        });
      }
    });
  }
}

function main(): void {
  const bus = new InProcessEventBus();
  const delivery = new DeliverySubscriber(bus);
  const orders = new OrderService(bus);

  orders.placeOrder("ord-7", ["WIDGET-1", "WIDGET-2"]);

  console.log(
    `delivery subdomain scheduled ${delivery.shipments.length} shipment(s), ` +
      `tracking ${delivery.shipments[0]?.trackingNumber}`,
  );
}

main();
```

Java, Rust, and Kotlin are omitted from the runnable examples not because the
pattern does not apply there, it applies identically in any language with a
module or package system, but because the demonstration hinges on the
integration-contract boundary rather than on any language-specific mechanism,
and the three examples above already cover an explicit-interface style, a
protocol-based dependency-injection style, and an event-driven style, which
are the three integration shapes this pattern actually uses in practice
regardless of implementation language.
