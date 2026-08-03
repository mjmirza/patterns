---
name: Decompose by Business Capability
slug: decompose-by-business-capability
family: 10-microservices
category: Structural
aliases: [Capability-Based Decomposition, Business-Aligned Services]
first_described: "Richardson 2016"
maturity: canonical
related: [decompose-by-subdomain, api-gateway, saga, backends-for-frontends, strangler-fig]
incompatible_with: [layered-architecture]
verified: 2026-08-02
---

# Decompose by Business Capability

## 1. Name, aliases, and lineage

The canonical name is Decompose by Business Capability. Chris Richardson
catalogued it under this exact name as one of the two primary decomposition
patterns in his microservices pattern language, alongside Decompose by
Subdomain, published on microservices.io and later formalized in his book
*Microservices Patterns. With Examples in Java*, Manning, 2018
([microservices.io pattern description](https://microservices.io/patterns/decomposition/decompose-by-business-capability.html),
verified 2026-08-02). The pattern names services after what the business does
to generate value, using the noun-plus-verb business capability model that
originated in enterprise architecture practice well before microservices
existed, most visibly in business capability mapping as used by consultancies
and enterprise architecture teams through the 2000s and 2010s.

The pattern has no single inventor in the way a Gang of Four pattern does.
Martin Fowler and James Lewis, in the article that popularized the term
microservice, describe the same idea without naming it a pattern, calling it
organizing around business capability and contrasting it with the technology
layer split of presentation, business logic, and data access that was common
across enterprise Java and .NET architectures through the 2000s
([Fowler and Lewis, Microservices](https://martinfowler.com/articles/microservices.html),
verified 2026-08-02). Eric Evans, in *Domain-Driven Design. Tackling
Complexity in the Heart of Software*, Addison-Wesley, 2003, supplies the
conceptual machinery the pattern relies on most heavily, the bounded context
and the ubiquitous language, though Evans wrote about bounded contexts as a
modeling discipline for a single system, not as a service-boundary rule
(Evans, *Domain-Driven Design*, Addison-Wesley, 2003, ISBN 978-032-112521-7,
checked against a Wikipedia summary of the book's key concepts, verified
2026-08-02). Richardson's own second decomposition pattern, Decompose by
Subdomain, is his explicit acknowledgment that business capability alone
under-specifies a boundary and that a DDD subdomain analysis often produces a
cleaner cut, particularly when the business capability inventory itself is
stale or was drawn up by people who have never opened the codebase.

A frequent alias in practice is capability-based decomposition, used
interchangeably in enterprise architecture literature with business
capability mapping applied to service boundaries. Team Topologies
literature, Matthew Skelton and Manuel Pais, *Team Topologies. Organizing
Business and Technology Teams for Fast Flow*, IT Revolution Press, 2019,
uses the closely related but not identical term stream-aligned team, a team
shaped around a single, valuable stream of work, which is frequently a
business capability but is defined by the flow of work rather than by an
enterprise architecture taxonomy. The two concepts overlap in practice more
than the literature admits, and this entry treats capability-aligned service
and stream-aligned service boundary as the same design decision viewed from
two different source disciplines, enterprise architecture on one side, team
design on the other.

## 2. Problem and context

A team owns a monolith, or is building a new system, and needs to draw
service boundaries. The team has already accepted that the system will be
more than one deployable unit, the decision to go distributed has been made
elsewhere or is not in question here, and the actual problem in front of them
is narrower and harder than it looks. Where do the seams go.

The naive first attempt splits along technical layers that already exist in
the codebase, a presentation service, a business logic service, a data
access service. This produces the layered-monolith-in-disguise anti-pattern.
Every business change, adding a discount rule, changing how a return is
processed, still touches all three services in lockstep, because the layers
were never independent units of business change, they were independent
technical concerns inside one unit of business change. The team gets the
deployment overhead of microservices, network calls, service discovery,
distributed tracing, and none of the organizational benefit, because no team
can ship a feature without coordinating a release across all three services.

The context that makes Decompose by Business Capability the right first move
is specific. The organization already has, or can construct in a working
session, a reasonably stable map of what the business does, order
management, inventory, shipping, customer accounts, pricing, catalog. These
capabilities change far more slowly than the software that implements them,
because they describe the business's operating model, not this quarter's
technology stack. A retailer's Order Management capability existed before
the web, as a paper process, and will exist after the current service is
rewritten a third time. Anchoring service boundaries to something that
outlives the current architecture is the entire value proposition. The
pattern also assumes a Conway's Law reality that will not go away by
ignoring it, any system design mirrors the communication structure of the
organization that builds it, attributed to Melvin Conway in 1968 and cited
directly by Fowler and Lewis in the microservices article, verified
2026-08-02, so a service boundary that does not match a team boundary
accumulates coordination cost regardless of how clean the code looks.

## 3. Forces

Cohesion pulls toward drawing the boundary around a single business
capability, because everything that changes together for one business
reason, a new discount type, a change to how backorders are handled, then
lives in one deployable unit and ships without a cross-team release train.
Coupling pulls the other way when two capabilities that seem conceptually
separate share data the organization has never actually separated, order
and inventory both touch stock level, and drawing a hard service line
between them can force a distributed transaction where a database
constraint used to suffice.

Team topology is often the dominant force in practice, more than the
technical cohesion argument the literature emphasizes. A capability-aligned
service that no team is staffed to own end to end degrades within months
into a service everyone touches and nobody maintains, which is worse than
the monolith it replaced, because the monolith at least had one team
accountable for all of it. Stability favors the business capability model
because a capability like Payments or Customer Identity is far more stable
over a five-year horizon than the current org chart, which is exactly why
Richardson recommends it as the primary decomposition axis and treats
subdomain analysis as the refinement, not the starting point.

Operability and cost cut against over-decomposition. Every additional
service is an additional deployment pipeline, an additional set of on-call
runbooks, an additional network hop with its own latency and failure
budget, and an additional surface for authentication and authorization. A
business capability drawn too finely, splitting Customer Contact
Preferences from Customer Profile because they are conceptually distinct,
buys almost no autonomy and multiplies operational cost. Cognitive load,
formalized by Skelton and Pais as a design constraint a team topology must
respect, argues for capabilities sized so a team of six to nine people can
hold the whole domain, its data model, and its failure modes in their
heads, rather than capabilities sized purely by an enterprise architecture
taxonomy that has never been checked against what a team can actually
operate.

Consistency is the sharpest trade-off this pattern forces. Splitting by
capability almost always means splitting the database that used to enforce
a single transactional boundary across those capabilities. The pattern
gives up the ACID guarantee the monolith gave for free and replaces it
with eventual consistency, typically implemented with the Saga pattern for
any business process that spans capability boundaries, checking out a cart
which touches Inventory, Payment, and Order Management being the canonical
example. A team adopting this pattern without a plan for cross-capability
consistency is adopting the deployment cost of microservices while still
owing the consistency guarantees of a monolith, which is the single most
common implementation failure this pattern produces.

## 4. Applicability and non-applicability

Reach for Decompose by Business Capability when the organization has a
reasonably stable understanding of its own operating model, order
management, catalog, fulfillment, billing are things this business will
still be doing in some recognizable form in three years even if every line
of code is rewritten. Reach for it when the team boundary already exists or
can be created to match, because a service without an owning team accrues
technical debt no static analysis catches. Reach for it as the first pass of
a strangler fig migration off a monolith, because a capability-shaped seam
is usually the seam that already has the least tangled data model inside
the legacy system, having been someone's department at some point in the
company's history. Reach for it when the primary pain is deployment
coupling, one team's release blocked on another team's unrelated change,
because that pain is a direct symptom of a boundary drawn along a technical
layer instead of a business capability.

Do not reach for this pattern in a startup or early-stage product where the
business capabilities themselves are still being discovered. A capability
inventory is a snapshot of an organization's current self-understanding, and
in a pre-product-market-fit company that snapshot is often wrong within a
quarter, which means the service boundaries built on it are wrong within a
quarter too, at far higher cost to change than a monolith's internal module
boundaries would have been. Do not reach for it when the team is smaller
than the number of capabilities the enterprise architecture group has
identified, because a five-person team running twelve services, one per
capability, is not autonomy, it is one team doing distributed-systems
overhead for the privilege of context-switching between twelve deployment
pipelines. Do not reach for it as a substitute for actual domain analysis,
an enterprise architecture capability map produced by a group that has
never read the codebase routinely misses the data ownership boundaries a
DDD subdomain analysis would surface, which is precisely why Richardson
positions Decompose by Subdomain as the companion pattern rather than
treating business capability mapping as sufficient on its own. Do not reach
for it when the dominant coupling in the system is not organizational but
computational, a tightly coupled numerical pipeline or a system with hard
real-time latency budgets across what looks like separate capabilities is
often better served by keeping that path inside one process regardless of
how the business capability inventory is drawn. Do not reach for it
retroactively as a justification, drawing service boundaries first for
infrastructure reasons, container orchestration convenience or a desire to
use a particular cloud service per boundary, and then writing a business
capability label on each box after the fact produces the label without the
underlying stability and autonomy properties the pattern actually promises.

## 5. Structure

The primary participant is the Business Capability itself, an
organizational concept, not a code artifact, representing what the business
does to deliver value, distinct from how it is currently implemented. A
capability is typically expressed as a noun phrase, Order Management, or a
noun plus a level of the business, Level 2 capability under a Level 1 domain
such as Commerce.

The Capability Service is the code and data that implement one business
capability end to end, including its own persistence, its own API surface,
and, in the fullest form of the pattern, its own user interface concerns
where those concerns are specific to the capability rather than shared
navigation chrome. It owns its data model exclusively, no other service
reads or writes its storage directly, which is the structural property that
gives the pattern its autonomy guarantee.

The Owning Team is the group of people, sized to Skelton and Pais's
cognitive-load guidance, accountable for the capability service across its
full lifecycle, design, build, deploy, operate, and eventually retire. The
pattern treats a service with no single owning team as a structural defect
regardless of how clean its internal code is.

The Capability Boundary is the explicit interface, typically a set of REST
or gRPC endpoints or an event contract, through which every other
capability service interacts with this one. No participant reaches across
the boundary through a shared database, a shared library that encodes
business rules, or a direct in-process call.

A Cross-Capability Process is any business workflow that spans more than
one capability, order placement touching Order Management, Inventory, and
Payment being the standard example, coordinated through the Saga pattern or
an orchestrating process rather than a distributed transaction, because the
whole point of the boundary is that no two capability services share a
transaction manager.

## 6. ASCII structure diagram

```
                     Business Capability Map
        (the enterprise's self-understanding of what it does)

  +--------------+   +--------------+   +--------------+   +--------------+
  |   Catalog    |   |  Inventory   |   | Order Mgmt   |   |   Payment    |
  |  Capability  |   |  Capability  |   |  Capability  |   |  Capability  |
  +--------------+   +--------------+   +--------------+   +--------------+
         |                   |                   |                   |
         v                   v                   v                   v
  +--------------+   +--------------+   +--------------+   +--------------+
  |Catalog Team  |   |Inventory Team|   |Order Team    |   |Payment Team  |
  |Catalog Svc   |   |Inventory Svc |   |Order Svc     |   |Payment Svc   |
  | +----------+ |   | +----------+ |   | +----------+ |   | +----------+ |
  | | API      | |   | | API      | |   | | API      | |   | | API      | |
  | +----------+ |   | +----------+ |   | +----------+ |   | +----------+ |
  | +----------+ |   | +----------+ |   | +----------+ |   | +----------+ |
  | | Own DB   | |   | | Own DB   | |   | | Own DB   | |   | | Own DB   | |
  | +----------+ |   | +----------+ |   | +----------+ |   | +----------+ |
  +--------------+   +--------------+   +--------------+   +--------------+
         ^                   ^                   ^                   ^
         |                   |                   |                   |
         +-------------------+---------+---------+-------------------+
                                        |
                              Capability Boundary
                        (REST/gRPC calls, no shared DB,
                         no shared business-rule library)

  No arrow ever crosses directly into another capability's "Own DB" box.
  Every cross-capability interaction goes through the API row above it.
```

## 7. Dynamics

The design-time flow is what most literature covers and this entry names
explicitly because it is the part practitioners skip under deadline
pressure. The organization, or the team doing the decomposition, first
inventories business capabilities, typically two levels deep, a Level 1
domain such as Commerce decomposed into Level 2 capabilities such as
Catalog, Order Management, Payment, Fulfillment. Each Level 2 capability is
checked against team sizing, if no team of reasonable size can own it, it
is either split further or merged with an adjacent capability that shares a
data model. Each capability is then checked against a rough DDD subdomain
analysis, does the proposed capability boundary correspond to a bounded
context with a coherent ubiquitous language, or does it actually straddle
two subdomains that will fight over shared vocabulary, a common failure
where a capability named Customer turns out to mean two different things,
the sales-facing customer record and the support-facing customer record, in
two different parts of the org.

At runtime, the flow inside a single capability service is ordinary, a
request enters the service's own API, is handled entirely against that
service's own data, and a response returns. The dynamics worth diagramming
are the cross-capability flows, because this is where the pattern's
consistency trade-off becomes visible operationally.

```
Order Placement, a cross-capability business process

  Client            Order Svc         Inventory Svc      Payment Svc
    |                   |                    |                 |
    | POST /orders      |                    |                 |
    |------------------>|                    |                 |
    |                   | reserve stock      |                 |
    |                   |------------------->|                 |
    |                   |    reserved OK     |                 |
    |                   |<-------------------|                 |
    |                   | authorize payment  |                 |
    |                   |----------------------------------->  |
    |                   |          authorized                  |
    |                   |<-----------------------------------  |
    |                   | commit order (own DB)                |
    |                   |--+                                   |
    |                   |  |                                   |
    |   order confirmed |<-+                                   |
    |<------------------|                                      |
    |                   |                                      |
    |     -- if payment authorization fails downstream --      |
    |                   | compensating action, release stock   |
    |                   |------------------->|                 |
    |                   |     released       |                 |
    |                   |<-------------------|                 |
```

The compensating-action branch at the bottom is the Saga pattern in
miniature, and it exists because no distributed transaction spans Order,
Inventory, and Payment once each capability owns its own database. Any team
that draws capability boundaries without designing this branch has drawn a
boundary it cannot operate correctly under partial failure.

## 8. Implementation variants

The strict variant, sometimes called vertical slice or full-stack
capability ownership, gives the capability team its own frontend surface as
well as its own service and database, so the capability is genuinely
deployable and releasable end to end with zero coordination outside the
team. This is the form Fowler and Lewis describe when they contrast a
business-capability team against a horizontally sliced UI team, middleware
team, and DBA team. It is the most autonomous and the most expensive to
staff, because it requires frontend, backend, and data skills inside a
single team rather than pooled specialist teams shared across the
organization.

The API-only variant is more common in practice, particularly inside larger
organizations that retain a shared frontend or a small number of
channel-specific frontends built by separate teams. Here the capability team
owns the backend service and its data exclusively, but the user-facing
surface is composed by a separate presentation layer, frequently using the
Backends for Frontends pattern to avoid forcing every channel, web, mobile,
partner API, to consume the same shape of capability API.

The subdomain-refined variant runs Decompose by Business Capability first as
a rough cut and then applies Decompose by Subdomain within each capability
that turns out to be too large for one team, splitting Order Management,
for instance, into Order Capture and Order Fulfillment when those two turn
out to have genuinely different data models and change cadences under
closer DDD analysis. Richardson presents this as the standard combination
rather than a special case, business capability for the first, coarse cut,
subdomain analysis to validate and refine it.

The event-driven variant replaces most synchronous capability-to-capability
calls with domain events, an Order Placed event published by Order
Management and consumed asynchronously by Inventory and Fulfillment rather
than Order Management calling those services directly. This reduces runtime
coupling between capability services at the cost of a harder-to-trace
control flow, and it typically pairs with an event-carried state transfer
approach so consuming capabilities do not need a synchronous callback to
fetch missing data.

## 9. Known production uses

Amazon adopted a mandate, described publicly by former Amazon and Google
engineer Steve Yegge, requiring every team to expose its data and
functionality exclusively through service interfaces, forbidding direct
database reads across team boundaries, shared memory, or any other
back-channel, which Yegge attributes to a directive from Jeff Bezos in the
early 2000s and credits as the structural precondition that made AWS
possible as a business
([Steve Yegge, Google Platforms Rant, republished gist](https://gist.github.com/chitchcock/1281611),
verified 2026-08-02). The mandate is not phrased in business-capability
language but its effect, one team, one service, one clearly bounded piece
of what the business does, is the pattern this entry describes, and it is
the example most frequently cited in the industry literature for the
organizational form the pattern requires.

Comparethemarket.com, the UK price-comparison company, is cited directly by
Fowler and Lewis as an organization that split into cross-functional teams,
each responsible for one or a small number of individual products, with
those products implemented as services communicating over a message bus
rather than a shared database, matching the event-driven implementation
variant of this pattern
([Fowler and Lewis, Microservices](https://martinfowler.com/articles/microservices.html),
verified 2026-08-02).

Chris Richardson's own worked example throughout *Microservices Patterns.
With Examples in Java*, Manning, 2018, is a fictional but representative
food delivery application, FTGO, decomposed into services named directly
after business capabilities, Consumer Service, Restaurant Service, Order
Service, Kitchen Service, Delivery Service, Accounting Service, used
throughout the book to demonstrate the pattern applied end to end including
the Saga-based order placement flow this entry's dynamics section diagrams
in miniature.

Netflix is widely reported in industry conference talks and its own
engineering blog to organize its backend around business-aligned services,
including a Membership service, a Playback service, and a Recommendations
service, each owned by a distinct team with its own data store, though the
specific naming and boundaries have shifted repeatedly as Netflix's
capability inventory itself changed over time, illustrating this entry's
applicability caveat that a capability map is a snapshot rather than a
permanent structure.

## 10. Consequences

Positive. Teams gain deployment autonomy, a capability team ships a change
to its own capability without coordinating a release with any other team,
which is the primary economic reason organizations adopt the pattern even
at real infrastructure cost. Service boundaries become more stable over
time than boundaries drawn along the current technology stack or the
current org chart, because business capabilities change on a slower clock
than either. The pattern gives each service a clear owner, which materially
improves incident response, because the on-call engineer for a capability
knows its data model and its failure modes deeply rather than shallowly
across a horizontal layer spanning every capability. It also creates a
natural unit for cost attribution, security review, and compliance
scoping, since a regulator or an auditor can be pointed at the Payment
capability's boundary and be reasonably confident that is where card data
actually lives.

Negative. The pattern trades a single transactional boundary for eventual
consistency across capabilities, and every cross-capability business
process now needs an explicit compensation strategy, typically the Saga
pattern, which is materially harder to design, test, and reason about than
a database transaction, and which most teams underestimate the first time
they build one. Operational cost rises with every additional service, more
deployment pipelines, more independently scaling infrastructure, more
surface area for authentication between services, more places a
distributed trace can go missing. Data that used to be joined in a single
query, an order with its line items and current inventory level, now
requires either a composition layer, denormalized read models, or multiple
round trips, and each of those has its own consistency and latency cost.
The pattern also requires an accurate and current capability map to work at
all, and an organization whose enterprise architecture group has not
revisited that map in several years will bake stale boundaries into service
names that outlive the org chart that produced them, becoming exactly the
kind of boundary mismatch the pattern was meant to prevent.

## 11. Failure modes and misuse

Symptom. Two services are constantly changed together in the same pull
request or the same release train, despite being named after apparently
distinct capabilities.
Cause. The capability map used for decomposition was drawn by an
enterprise architecture exercise disconnected from the actual data model,
so the two named capabilities in fact share a bounded context, a single
Customer concept split into a Customer Service and an Account Service that
both need to change every time either changes.
Fix. Run a DDD subdomain and bounded-context analysis on the pair, and
either merge them back into one service or redraw the boundary along the
actual data ownership line the analysis surfaces, per Decompose by
Subdomain.

Symptom. A capability service has grown to require five or more teams to
touch it for any nontrivial change, and its on-call rotation spans people
who do not know most of the codebase.
Cause. The capability was sized by an enterprise capability taxonomy rather
than by team cognitive load, so a Level 1 domain such as Commerce was
implemented as a single service instead of being refined into Level 2
capabilities each a team can hold in its head.
Fix. Apply Strangler Fig to peel sub-capabilities out of the oversized
service incrementally, verifying each extraction against the team-sizing
guidance in Team Topologies rather than against a purely conceptual
capability boundary.

Symptom. Order placement, or any cross-capability process, silently leaves
the system in an inconsistent state under partial failure, an order
recorded as placed with no inventory actually reserved, discovered only
through a customer complaint or a nightly reconciliation report.
Cause. The team implemented the capability split without designing the
compensating actions for the cross-capability process, treating the
synchronous happy path as the whole design and never building the Saga's
failure branch.
Fix. Design and test the compensating transaction for every step of every
cross-capability workflow before the capability split ships, and add the
reconciliation job as a permanent safety net rather than the primary
consistency mechanism, since a reconciliation job that runs nightly is a
detection mechanism, not a prevention mechanism.

Symptom. A service is technically a separate deployable and has its own
database, but no team can deploy a change to it without pulling in members
from two or three other teams, and its git blame shows a rotating cast of
contributors with no consistent ownership.
Cause. The service was split out for infrastructure reasons, or to satisfy
a mandate to have microservices, without an actual owning team assigned,
which is the structural defect named in dimension 5. A service without a
team is not an instance of this pattern regardless of what it is named.
Fix. Either assign a real owning team sized to the capability's cognitive
load, or merge the orphaned service back into whichever team's boundary it
actually falls inside, accepting that the merge is a smaller failure than
an unowned service left running in production.

Symptom. Two capability services both maintain their own copy of what
should be the same reference data, product price for instance held in both
Catalog and Order Management, and the copies drift out of sync over time,
producing customer-visible pricing errors.
Cause. The capability split correctly separated ownership but the team
never designed a propagation mechanism, an event stream or a scheduled
sync, for the read-only copies other capabilities legitimately need, and
instead let each service query the other's database directly at some point
under deadline pressure, quietly reintroducing the shared-database coupling
the boundary was drawn to prevent.
Fix. Introduce an explicit event-carried state transfer, Catalog publishes
a Price Changed event and every consuming capability updates its own
local, versioned copy, and audit the codebase for any remaining direct
cross-database query and remove it.

## 12. Trade-off matrix

| Force | Decompose by Business Capability | Decompose by Subdomain | Layered Architecture (technical-layer split) |
|---|---|---|---|
| Boundary stability over years | High, capabilities outlive technology and org changes | High, bounded contexts are similarly stable once modeled correctly | Low, layers are a technical artifact of the current stack choice |
| Boundary accuracy versus actual data ownership | Medium, an enterprise capability map can be conceptually wrong about where data actually lives | High, DDD modeling explicitly surfaces the real data ownership line | Not applicable, layers do not attempt to model business ownership |
| Ease of adoption without a domain expert on the team | High, a capability inventory can be drawn from an org chart and a product catalog | Low, requires genuine event-storming or domain-modeling work with real domain experts | High, requires no business modeling at all |
| Cross-boundary coordination for a typical feature | Low, most changes are for one business reason and land in one capability | Low, similar to capability decomposition once boundaries are correct | High, almost every feature touches presentation, logic, and data layers together |
| Consistency guarantees available | Weak, eventual consistency across capabilities, Saga required for cross-capability processes | Weak, same as capability decomposition, sagas required across bounded contexts | Strong, a single database transaction typically covers the whole change |
| Risk of misdrawn boundary going undetected | Higher, a stale or shallow capability map can look plausible while being operationally wrong | Lower, the modeling process itself tends to surface a mismatched boundary during design | Not applicable, layers do not claim to be business-aligned in the first place |

## 13. Related and incompatible patterns

Decompose by Subdomain is this pattern's closest companion rather than its
alternative in most real adoptions. Business capability decomposition
supplies the first, coarse cut a team can produce quickly from an
organizational artifact that already exists, and subdomain analysis then
validates or refines that cut against the actual data model. A team that
runs only the capability pass and skips the subdomain validation is the
most common source of the boundary-mismatch failure mode in dimension 11.

The Saga pattern is a structural dependency rather than an optional
companion. Any nontrivial adoption of business-capability decomposition
creates cross-capability business processes, and those processes require
an explicit consistency mechanism once the shared database is gone. A team
adopting this pattern without also adopting Saga, or an equivalent process
manager, has adopted only the deployment cost of the split and not a
working consistency story.

Backends for Frontends composes with this pattern in the API-only
implementation variant, decoupling the shape of each capability's API from
the shape each client channel actually needs, so a mobile app and a
partner integration do not both have to consume the same capability-shaped
payload designed primarily for the capability team's own convenience.

Strangler Fig is the standard migration vehicle for introducing this
pattern into an existing monolith incrementally, peeling one capability out
at a time behind a routing facade rather than attempting a big-bang
rewrite, and it is the pattern most literature recommends pairing with a
first capability extraction to prove the boundary before committing
further.

Layered Architecture, the technical-tier split of presentation, business
logic, and data access as the primary structural axis, is incompatible
with this pattern at the point of adoption, not merely different from it.
The two disagree about what the primary axis of decomposition should be,
and a system attempting to honor both simultaneously, layering inside each
capability is fine and common, but choosing layers as the top-level service
boundary while also claiming business-capability alignment produces the
layered-monolith-in-disguise anti-pattern named in dimension 2.

## 14. Refactoring path in and out

Introducing this pattern into an existing monolith begins with producing or
refreshing a business capability inventory, which is organizational and
analytical work before it is any code change at all, typically an
event-storming or capability-mapping workshop with actual domain experts
and the engineers who know where the current data model's seams already
are. The team then picks the single capability with the highest pain,
usually the one causing the most cross-team release coordination or the one
a team is already most eager to own independently, and applies Strangler
Fig to that one capability first, standing up a new service, routing a
subset of traffic to it, and migrating its data out of the shared database
incrementally, often behind a synchronization layer that keeps the old and
new data stores consistent during the transition window. Each subsequent
extraction repeats this process, and the team explicitly runs the
subdomain-validation pass described in dimension 13 before finalizing each
new service's boundary, rather than accepting the enterprise capability
map's line as final without checking it against the actual data ownership
the extraction reveals.

Removing this pattern, consolidating capability services back toward a
smaller number of services or a single deployable, is warranted when the
operational cost has outgrown the organizational benefit, most visibly when
the number of services has grown past what the number of owning teams can
actually staff, or when two capability services have become so tightly
coupled in practice, sharing most of their release cadence and most of
their on-call incidents, that the boundary no longer reflects any real
organizational or data-ownership seam. The refactoring path out mirrors
the path in, run Strangler Fig in reverse, moving one capability's read
and write paths back behind a single service boundary incrementally,
verifying at each step that no cross-capability Saga logic is silently
dropped in the merge, since a merged service still needs correct
compensation behavior for any process that continues to span it and a
remaining external capability.

## 15. Testing and verification

Each capability service is unit and integration testable in isolation
against its own data store, which is one of the pattern's genuine testing
benefits, a team can run its full test suite without standing up every
other capability's service, using contract tests, most commonly
consumer-driven contract testing with a tool such as Pact, to verify the
capability's API still satisfies what its known consumers expect without
those consumers needing to be live during the test run.

What becomes materially harder is testing the cross-capability process
itself, the Saga's happy path and every one of its compensating branches.
This typically requires either a dedicated integration test environment
with real or realistic doubles for every capability the process touches,
or a combination of contract tests per capability boundary plus a smaller
number of true end-to-end tests exercising the full Saga in a staging
environment, because the state space of partial-failure combinations,
payment succeeds but inventory reservation times out, inventory succeeds
but payment is declined, both time out simultaneously, grows quickly and
each combination needs its own assertion that the compensating action
actually restores a consistent state.

Testing capability boundary correctness itself, whether a proposed service
split actually reflects a coherent bounded context, is not something
automated tests catch well, and teams commonly use architectural fitness
functions, automated checks that fail the build if a service's code
attempts to query another capability's database directly or imports
another capability's internal types, to enforce the boundary mechanically
once it has been agreed, even though deciding where the boundary should be
remains a human, domain-modeling judgment.

## 16. Observability signals

A healthy capability decomposition shows a low rate of cross-service
commits touching more than one capability's repository in the same change
set, and a deployment frequency per capability that is largely independent
of every other capability's deployment frequency, both signals that the
boundary is absorbing business change without forcing coordination.
Distributed tracing across a cross-capability process, order placement
spanning Order, Inventory, and Payment, should show each capability's span
cleanly bounded with its own latency budget, and a healthy system shows the
vast majority of traces completing the happy path with the compensating
branch appearing only under genuine downstream failure, not as a routine
occurrence.

A failing decomposition shows the opposite pattern, a small number of pull
requests that repeatedly touch two or more capability repositories
together, a deployment calendar where two nominally independent
capabilities are almost always released in the same window because one
cannot ship without the other, and a Saga compensating-action rate that
climbs over time as the underlying data model drifts out of sync between
capabilities. Monitoring the count and age of reconciliation-job
corrections, records the nightly consistency check has to repair, is a
direct, measurable signal of how well the eventual-consistency story is
actually holding, and a rising trend in that count is an early warning
that a cross-capability process is missing a compensating action rather
than something to dismiss as noise.

## 17. Security and privacy implications

Capability-aligned service boundaries frequently align well with data
classification and regulatory scope, a Payment capability service is a
natural place to concentrate PCI DSS scope, and a Customer Identity
capability is a natural place to concentrate GDPR or CCPA personal-data
handling, which can meaningfully shrink the audit surface compared to a
monolith where card data and customer PII are scattered through a single
shared schema touched by every module. This is a genuine security benefit
of the pattern when the boundary is drawn deliberately with data
classification in mind.

The same boundary introduces new attack surface at every
capability-to-capability call, each of those calls is now a
network-crossing authentication and authorization decision rather than an
in-process function call implicitly trusted by virtue of running inside the
same process, and a team that decomposes by capability without also
implementing service-to-service authentication, commonly mutual TLS or
signed service tokens, and per-capability authorization checks has widened
its attack surface without offsetting the change. Event-carried state
transfer, used in the event-driven implementation variant, also means
personal or sensitive data that once lived in a single, access-controlled
schema now propagates as copies into every consuming capability's own
store, and a team adopting this pattern for a capability handling
regulated data needs an explicit data-retention and deletion story that
reaches every copy, not only the capability of record, or a GDPR deletion
request satisfied against the source capability can leave stale personal
data sitting in a downstream capability's event-derived store.

## Code examples

Three languages, each showing the same shape, two capability services with
their own private state, plus a small saga that coordinates a
cross-capability process and compensates when a downstream step fails. Java
and C# are omitted here because the demonstration is intentionally about
service boundaries and compensation, not language-specific object modeling,
and the same shape ports directly.

### TypeScript

```typescript
// Two capability services, each owning its own store, plus a saga that
// coordinates them and compensates on partial failure.

interface InventoryStore {
  reserve(sku: string, qty: number): boolean;
  release(sku: string, qty: number): void;
}

class InventoryService implements InventoryStore {
  private stock = new Map<string, number>([["sku-1", 2]]);
  reserve(sku: string, qty: number): boolean {
    const have = this.stock.get(sku) ?? 0;
    if (have < qty) return false;
    this.stock.set(sku, have - qty);
    return true;
  }
  release(sku: string, qty: number): void {
    const have = this.stock.get(sku) ?? 0;
    this.stock.set(sku, have + qty);
  }
}

class PaymentService {
  authorize(amountCents: number): boolean {
    return amountCents <= 5000;
  }
}

class OrderService {
  private orders: string[] = [];
  place(id: string): void {
    this.orders.push(id);
  }
  count(): number {
    return this.orders.length;
  }
}

function placeOrder(
  inventory: InventoryStore,
  payment: PaymentService,
  order: OrderService,
  sku: string,
  qty: number,
  amountCents: number,
  orderId: string
): boolean {
  if (!inventory.reserve(sku, qty)) return false;
  if (!payment.authorize(amountCents)) {
    inventory.release(sku, qty);
    return false;
  }
  order.place(orderId);
  return true;
}

const inventory = new InventoryService();
const payment = new PaymentService();
const order = new OrderService();

const first = placeOrder(inventory, payment, order, "sku-1", 1, 1000, "o-1");
const second = placeOrder(inventory, payment, order, "sku-1", 5, 1000, "o-2");

console.log("first placed", first);
console.log("second placed", second);
console.log("orders committed", order.count());
if (first !== true || second !== false || order.count() !== 1) {
  throw new Error("saga demonstration failed");
}
```

### Python

```python
class InventoryService:
    def __init__(self):
        self.stock = {"sku-1": 2}

    def reserve(self, sku, qty):
        have = self.stock.get(sku, 0)
        if have < qty:
            return False
        self.stock[sku] = have - qty
        return True

    def release(self, sku, qty):
        self.stock[sku] = self.stock.get(sku, 0) + qty


class PaymentService:
    def authorize(self, amount_cents):
        return amount_cents <= 5000


class OrderService:
    def __init__(self):
        self.orders = []

    def place(self, order_id):
        self.orders.append(order_id)

    def count(self):
        return len(self.orders)


def place_order(inventory, payment, order, sku, qty, amount_cents, order_id):
    if not inventory.reserve(sku, qty):
        return False
    if not payment.authorize(amount_cents):
        inventory.release(sku, qty)
        return False
    order.place(order_id)
    return True


if __name__ == "__main__":
    inventory = InventoryService()
    payment = PaymentService()
    order = OrderService()

    first = place_order(inventory, payment, order, "sku-1", 1, 1000, "o-1")
    second = place_order(inventory, payment, order, "sku-1", 5, 1000, "o-2")

    print("first placed", first)
    print("second placed", second)
    print("orders committed", order.count())
    assert first is True
    assert second is False
    assert order.count() == 1
```

### Go

```go
package main

import "fmt"

type InventoryService struct {
	stock map[string]int
}

func NewInventoryService() *InventoryService {
	return &InventoryService{stock: map[string]int{"sku-1": 2}}
}

func (i *InventoryService) Reserve(sku string, qty int) bool {
	have := i.stock[sku]
	if have < qty {
		return false
	}
	i.stock[sku] = have - qty
	return true
}

func (i *InventoryService) Release(sku string, qty int) {
	i.stock[sku] = i.stock[sku] + qty
}

type PaymentService struct{}

func (PaymentService) Authorize(amountCents int) bool {
	return amountCents <= 5000
}

type OrderService struct {
	orders []string
}

func (o *OrderService) Place(id string) {
	o.orders = append(o.orders, id)
}

func (o *OrderService) Count() int {
	return len(o.orders)
}

func placeOrder(inv *InventoryService, pay PaymentService, ord *OrderService, sku string, qty, amountCents int, orderID string) bool {
	if !inv.Reserve(sku, qty) {
		return false
	}
	if !pay.Authorize(amountCents) {
		inv.Release(sku, qty)
		return false
	}
	ord.Place(orderID)
	return true
}

func main() {
	inventory := NewInventoryService()
	payment := PaymentService{}
	order := &OrderService{}

	first := placeOrder(inventory, payment, order, "sku-1", 1, 1000, "o-1")
	second := placeOrder(inventory, payment, order, "sku-1", 5, 1000, "o-2")

	fmt.Println("first placed", first)
	fmt.Println("second placed", second)
	fmt.Println("orders committed", order.Count())

	if first != true || second != false || order.Count() != 1 {
		panic("saga demonstration failed")
	}
}
```

## 18. References

1. Chris Richardson, [Pattern. Decompose by business capability](https://microservices.io/patterns/decomposition/decompose-by-business-capability.html), microservices.io, verified 2026-08-02.
2. Chris Richardson, *Microservices Patterns. With Examples in Java*, Manning Publications, 2018, chapter 2, "Decomposition strategies".
3. Martin Fowler and James Lewis, [Microservices](https://martinfowler.com/articles/microservices.html), martinfowler.com, 2014, verified 2026-08-02.
4. Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of Software*, Addison-Wesley, 2003, ISBN 978-032-112521-7, part on Bounded Context and Ubiquitous Language, checked against a Wikipedia summary of the book's key concepts, verified 2026-08-02.
5. Matthew Skelton and Manuel Pais, *Team Topologies. Organizing Business and Technology Teams for Fast Flow*, IT Revolution Press, 2019, chapters on stream-aligned teams and cognitive load.
6. Steve Yegge, [Google Platforms Rant](https://gist.github.com/chitchcock/1281611), publicly republished gist recording the 2006 internal memo, verified 2026-08-02, describing the Amazon service-interface mandate attributed to Jeff Bezos.
7. Sam Newman, *Building Microservices. Designing Fine-Grained Systems*, 2nd edition, O'Reilly Media, 2021, chapter 2, "How to Model Microservices".
8. Melvin E. Conway, "How Do Committees Invent?", Datamation, April 1968, cited as Conway's Law by Fowler and Lewis in reference 3 above.
