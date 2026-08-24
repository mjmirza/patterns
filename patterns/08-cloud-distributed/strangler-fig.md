---
name: Strangler Fig
slug: strangler-fig
family: 08-cloud-distributed
category: Migration
aliases: [Strangler Application, Strangler Application Pattern, Strangler Pattern, Ship of Theseus Pattern]
first_described: "Fowler 2004"
maturity: canonical
related: [anti-corruption-layer, circuit-breaker, branch-by-abstraction, feature-toggle, blue-green-deployment]
incompatible_with: []
verified: 2026-08-02
---

# Strangler Fig

## 1. Name, aliases, and lineage

The canonical name is the Strangler Fig pattern. Martin Fowler introduced the
idea on his personal site under the title "Strangler Application" and later
retitled the same page "Strangler Fig Application" (Martin Fowler, "Strangler
Fig Application", martinfowler.com bliki, originally published 2004, page
retitled and revised 22 August 2024,
https://martinfowler.com/bliki/StranglerFigApplication.html, verified
2026-08-02). Fowler explains the rename directly on the page. he grew
uncomfortable with the violent connotation of the bare word "strangler" once
readers stopped connecting it to the plant, and he changed the title to
"Strangler Fig Application" so the metaphor points at the specific botanical
process rather than at killing something (Fowler, martinfowler.com,
verified 2026-08-02).

The metaphor comes from a real observation. Fowler describes seeing strangler
fig vines during a trip to Queensland, Australia, in 2001. A strangler fig
seed germinates in a nook high in the canopy of a host tree, sends roots down
to the ground, and grows a lattice of vines around the host's trunk. Over
years the fig's own root and branch structure thickens until it can stand
without support. The host tree, meanwhile, is shaded out and starved of
resources, and in many cases eventually dies and rots away, leaving a
free-standing fig that is, structurally, a hollow lattice in the exact shape
of the tree it replaced (Fowler, martinfowler.com, verified 2026-08-02). The
software analogy Fowler draws is precise. a new system grows around an old
one, starts small, gradually takes over each function the old one performed,
and eventually the old system can be removed while the new one keeps running
in its place, having assumed the same external shape.

Fowler's original wording of the core idea is short. "It begins with small
additions, often new features, that are built on top of, yet separate to the
legacy code base" (Fowler, martinfowler.com, verified 2026-08-02). This is a
narrower framing than most later treatments give the pattern. Fowler's own
essay is mostly about a single big web application being extended safely by
routing whole URLs to a new codebase, one path at a time, rather than a
general theory of legacy replacement. The generalization to "any legacy
system, any interception point, any granularity of migrated unit" is the
industry's later broadening of the term, most visibly formalized by cloud
vendors, see dimension 9.

Wikipedia records an additional alias, "Ship of Theseus pattern", after the
philosophical puzzle about whether a ship remains the same ship once every
plank has been replaced (Wikipedia contributors, "Strangler fig pattern",
https://en.wikipedia.org/wiki/Strangler_fig_pattern, verified 2026-08-02, used
here only to confirm the alias and the attribution to Fowler, not as an
explanatory source). The alias is apt. the pattern's whole promise is that the
system a customer talks to on the last day of the migration is functionally
continuous with the system on the first day, even though not one line of the
implementation underneath survived.

Two names get used almost interchangeably in day to day conversation and are
worth separating here, because dimension 4 depends on the distinction.

- **Strangler Fig pattern (Fowler's original sense).** The old system is not
  touched from the outside except through the interception point. Traffic is
  redirected wholesale to the new implementation of a function once that
  function is ready, and the interception point is where the switch happens.
- **Strangler Fig pattern (the broadened, common industry sense).** Any
  incremental replace-in-place migration where a facade or router sits between
  callers and two competing implementations, gradually shifting traffic from
  old to new. This sense covers database table extraction, event-driven
  synchronization, and multi-year, multi-team programs, not only a single
  application's URL space.

This entry covers the broadened sense, because that is the sense almost every
production reference, including Fowler's own later writing and every major
cloud vendor's architecture guide, now uses.

## 2. Problem and context

A system has been running in production for years. It works, it has real
users, and it earns real money or does real work, but its internals have
become hard to change safely. The reasons are familiar to anyone who has
maintained a system past its first five years. the framework it was built on
is out of support, the team that understood a subsystem has moved on, the
data model has accumulated years of special cases, the deployment process
takes hours and any change risks the whole system rather than one feature,
and every added capability makes the next change slower rather than faster.

The organization decides the system needs to be replaced or substantially
re-architected, and this is where the problem the pattern answers begins. A
full rewrite, built separately and switched over on a single cutover date,
carries three well known and often fatal risks. First, the rewrite competes
with new feature work for the same engineers, and business stakeholders will
not agree to freeze feature delivery for the months or years a rewrite takes,
so the rewrite team perpetually chases a moving target as the legacy system
keeps changing under them. Second, a system with years of production history
has accumulated undocumented behavior, edge cases nobody remembers deciding
on, and workarounds for problems that no longer exist but whose absence would
break something else. A rewrite from a specification, rather than from the
running system's actual behavior, reliably drops some of this. Third, the
cutover itself is an all-or-nothing event. every bug in the new system is
discovered by production traffic on day one, at the exact moment stakes are
highest and rollback is hardest.

The context that makes the Strangler Fig pattern the right answer has three
parts, matching the reasoning the Azure Architecture Center gives for the
pattern. the calling code can be intercepted, meaning requests to the system
pass through a point that can be altered to redirect some of them; the
existing system's source is available and can be modified, at least enough to
add the redirection and any adapter layer the migration needs; and there is
appetite in the organization for a migration that plays out over months, with
partial progress visible and valuable at every step, rather than a single
release event (Microsoft, "Strangler Fig pattern", Azure Architecture Center,
https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig,
verified 2026-08-02).

Concretely, the pattern is reached for in situations like these. an online
retailer's monolithic order system needs to move to a service-per-domain
architecture without a maintenance window during a peak sales period. a
government agency's mainframe benefits claims system needs modern APIs while
the mainframe continues to be the system of record for years, because
migrating the underlying COBOL logic and the data it depends on cannot happen
overnight. a company acquired through a merger runs two customer databases
and wants one of them to become the record of truth over an eighteen month
integration window while both keep serving live customers.

## 3. Forces

- **Business continuity versus internal cleanliness.** Favors continuity.
  Users, revenue, and compliance keep flowing through the legacy system for
  most of the migration, at the cost of running two systems that must both be
  kept correct and both be operated.
- **Risk exposure per change.** Favors the pattern strongly. A single route,
  table, or feature moved at a time means a defect in the new implementation
  affects a bounded slice of traffic, and rollback means flipping that one
  route back rather than reverting an entire system.
- **Cost.** Sacrificed for the duration of the migration. Two systems, two
  on-call rotations, an interception layer, and, when data is shared, a
  synchronization mechanism, all cost real infrastructure and engineering
  attention on top of what either system alone would cost. This is the price
  paid to buy down the cutover risk.
- **Speed of full completion.** Sacrificed compared to a rewrite executed on
  a fixed schedule with a hard cutover date. A strangler fig migration has no
  natural endpoint forced on it, and, as dimension 11 covers in depth, this is
  exactly what allows it to stall indefinitely rather than merely take longer.
- **Team autonomy and parallel work.** Favored. Once the interception point
  exists, different teams can migrate different routes, tables, or features in
  parallel, on independent schedules, without coordinating a shared release
  train, provided the interception layer's routing rules do not collide.
- **Consistency of state shared between the two systems.** Sacrificed. Any
  data both systems touch during the coexistence phase needs an explicit
  synchronization or ownership decision, and every such decision introduces
  either eventual consistency, dual writes, or a single point that both
  systems must call through, none of which is free of failure modes.
- **Operability and observability.** Mixed. Per-route rollback and gradual
  exposure are wins for operability, but a request's path through the
  interception layer, possibly the legacy system, possibly an anti-corruption
  layer, and possibly the new service, is longer and harder to reason about
  than either system alone, and the interception layer itself becomes a piece
  of infrastructure that must be monitored, capacity-planned, and kept from
  becoming a single point of failure (AWS, "Strangler fig pattern", AWS
  Prescriptive Guidance,
  https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html,
  verified 2026-08-02, "Proxy layer failure" under Issues and considerations).
- **Reversibility.** Favored while the legacy system remains intact behind
  the interception layer. This reversibility decays over time as legacy code
  paths for already-migrated features are deleted, so the pattern trades early
  reversibility for later irreversibility, on a schedule the team controls.

No pattern gets all of these for free. the trade this one makes is
concentrated cost and coordination overhead during the migration window, paid
in exchange for a bounded, reversible, incremental path instead of one large,
irreversible bet.

## 4. Applicability and non-applicability

Reach for the Strangler Fig pattern when the following hold.

- The system being replaced is large or complex enough that a full rewrite
  followed by a single cutover carries unacceptable business risk, and the
  organization can tolerate the two systems running side by side for weeks,
  months, or, for very large systems, years.
- Requests, calls, or data access to the legacy system can be intercepted at
  some seam. an HTTP layer, a message queue, a database access layer, or a
  deployable's entry point, so that some fraction of traffic can be redirected
  without touching every caller.
- The legacy system's source is available and modifiable, at least enough to
  add the redirection point and, where needed, an adapter that lets the two
  systems call each other correctly during coexistence.
- The system can be decomposed into pieces, whether by route, by table, by
  bounded context, or by tenant, that can be migrated and validated one at a
  time, each piece delivering value on its own once it lands.
- Stakeholders want or need new features delivered continuously through the
  migration window, rather than accepting a feature freeze until a rewrite
  ships.
- Rollback of an individual migrated piece needs to be fast and low-drama, for
  example because the system is customer-facing and a full-system outage is
  not an acceptable price for finding a bug in the new implementation.

Do NOT reach for the Strangler Fig pattern in these cases, and the reason
matters as much as the rule itself.

- **Requests to the legacy system cannot be intercepted.** If the calling
  surface cannot be put behind a router, a proxy, or an equivalent seam, there
  is no place to redirect traffic from, and the pattern has no mechanism to
  attach to. Microsoft's own guidance names this directly as a case where the
  pattern does not apply (Microsoft, Azure Architecture Center, verified
  2026-08-02, "When to use this pattern"). This is common with systems reached
  only through proprietary client software, tightly coupled desktop
  applications, or hardware with a fixed protocol nobody can proxy.
- **The legacy system's source code is not available or not modifiable.** AWS
  states this plainly. "To implement the strangler fig pattern, you must have
  access to the monolith application's code base... You cannot intercept
  calls without code base access" (AWS Prescriptive Guidance, verified
  2026-08-02, "Code base access" under Issues and considerations). A vendored
  black box that exposes no seam to redirect from is a wrapper or an
  anti-corruption layer problem, not a Strangler Fig migration.
- **The system is small enough that a full rewrite is genuinely cheap and
  low-risk.** AWS names this too. "Large monoliths benefit the most from the
  strangler fig pattern. For small applications... it might be more efficient
  to rewrite the application... instead of migrating it" (AWS Prescriptive
  Guidance, verified 2026-08-02, "Application complexity"). Building the
  proxy layer, the adapter, and the synchronization mechanism has a fixed
  cost that a genuinely small system will never earn back.
- **The organization needs the legacy system fully decommissioned by a hard,
  near-term date**, such as a mandated end-of-support deadline weeks away.
  The pattern's whole value is that migration proceeds at a sustainable,
  validated pace, and compressing that pace to hit a hard near-term deadline
  reintroduces the big-bang risk the pattern exists to avoid.
- **The domain boundaries of the target architecture are not understood
  yet.** AWS flags premature decomposition as a real cost, not a hypothetical
  one, and recommends domain-driven design and event storming before choosing
  service boundaries (AWS Prescriptive Guidance, verified 2026-08-02,
  "Unclear domain"). Strangling toward the wrong boundaries produces the same
  tangled coupling in a new, harder-to-see place.
- **The two systems cannot tolerate any data or behavioral divergence during
  coexistence**, for example a financial ledger where even a
  microsecond-scale window of disagreement between old and new balances is
  unacceptable. Some domains need a different technique entirely, such as a
  synchronized parallel run with reconciliation and an explicit cutover once
  outputs are proven identical over a real workload, rather than a gradual,
  per-route strangle.
- **The team lacks the discipline or the organizational mandate to actually
  retire migrated legacy code once it is replaced.** Dimension 11 covers this
  as the pattern's most common real-world failure. attempting the pattern
  without a forcing function to remove dead legacy paths tends to produce two
  permanent systems rather than one finished migration.

## 5. Structure

Four participants, named by the role each plays, following the shape both
Fowler's original essay and the cloud vendor guides converge on.

- **Client.** Any caller of the system being migrated. a browser, a mobile
  app, another internal service, a batch job. The client's contract does not
  change across the whole migration. it keeps calling the same address, path,
  or interface it always called.
- **Facade (also called the strangler facade, the interception layer, or,
  when implemented on a network boundary, the proxy or gateway).** Sits
  between the client and both systems. Decides, per request, whether the
  legacy system or the new system should handle it, and forwards accordingly.
  Microsoft's own diagram calls this component the "Strangler Fig facade"
  (Microsoft, Azure Architecture Center, verified 2026-08-02). The facade is
  the one component that must be highly available and low-latency, because
  every request, migrated or not, now passes through it.
- **Legacy system.** The existing system being replaced. During coexistence
  it continues to serve every function not yet migrated, and it is still
  patched for bugs and kept running, even though no new functionality is
  built inside it.
- **New system.** The replacement, built up incrementally, one migrated piece
  at a time. Each piece the new system gains is a piece the legacy system
  loses responsibility for, and the facade's routing table is the record of
  which piece currently belongs to which side.

A fifth, optional but frequently necessary participant appears whenever the
two systems must call each other during coexistence, which is common when a
newly migrated service depends on data or logic that has not moved yet.

- **Anti-Corruption Layer (ACL).** An adapter, usually implemented inside the
  legacy system for calls travelling toward the new system, or inside the new
  system for calls travelling toward the legacy one, that translates between
  the two systems' models so neither has to adopt the other's internal shape.
  AWS's own walkthrough of the pattern builds one explicitly, implemented as a
  facade class such as `UserServiceFacade`, and states plainly that "the ACL
  must be decommissioned after all dependent services have been migrated"
  (AWS Prescriptive Guidance, verified 2026-08-02, "Adding an anti-corruption
  layer"). This is the same Anti-Corruption Layer pattern used on its own,
  see dimension 13, but here its lifetime is bounded to the migration window
  rather than being a permanent architectural fixture.

Relationships. the Client depends only on the Facade's address, never
directly on the Legacy system's or the New system's address. The Facade holds
a routing table, keyed by whatever unit the migration is granular to. URL
path, database table, tenant identifier, feature flag, or message type. and
consults that table on every request to decide where to forward. The Legacy
system and the New system are peers from the Facade's point of view. neither
one is privileged, and the Facade's job is exactly to make swapping which one
answers a given request an operation with no visible effect on the Client.
When the ACL is present, it sits on the boundary between the two systems, not
between either system and the Facade or the Client.

## 6. ASCII structure diagram

```
                          +-------------------+
                          |      Client       |
                          | (browser, service, |
                          |   mobile app)      |
                          +---------+----------+
                                    |
                                    | one stable address,
                                    | never changes
                                    v
                          +-------------------+
                          |      Facade       |
                          |  (proxy, gateway,  |
                          |  strangler router) |
                          |--------------------|
                          | routing table      |
                          |  /user   -> NEW    |
                          |  /cart   -> NEW    |
                          |  /account-> LEGACY |
                          +----+----------+----+
                               |          |
                unmigrated     |          |   migrated
                routes         |          |   routes
                               v          v
                   +-----------------+   +-----------------+
                   |  Legacy System  |<->|   New System    |
                   |  (the monolith  |   |  (microservices |
                   |   being         |   |   or the target |
                   |   replaced)     |   |   architecture) |
                   +-----------------+   +-----------------+
                            ^                     ^
                            |                     |
                            +---- Anti-Corruption -+
                                  Layer (ACL), only
                                  where cross calls
                                  are needed during
                                  coexistence

   The Facade is the only component the Client ever addresses.
   Moving a route from LEGACY to NEW is a routing table edit,
   not a Client-visible change and not a redeploy of the Client.
```

## 7. Dynamics

Two different timescales matter for this pattern, and conflating them is a
common source of confusion, so both are shown here separately.

First, the per-request dynamics at any single point during the migration.
this is the same for every request regardless of how far along the migration
is, only the routing decision's outcome changes over time.

```
Client          Facade              Legacy System        New System
  |                |                       |                   |
  |-- request ---->|                       |                   |
  |                |-- look up route ----->|                   |
  |                |   in routing table    |                   |
  |                |                       |                   |
  |                |  route says LEGACY    |                   |
  |                |---------------------->|                   |
  |                |                       |-- handles it ---->|
  |                |                       |   (may call ACL   |
  |                |                       |    if it needs a  |
  |                |                       |    migrated part) |
  |                |<---- response --------|                   |
  |<-- response ---|                       |                   |
  |                |                       |                   |
  |-- request ---->|                       |                   |
  |                |  route says NEW       |                   |
  |                |------------------------------------------>|
  |                |                       |                   |-- handles it
  |                |<----------------------------- response ---|
  |<-- response ---|                       |                   |
```

Second, the migration-level dynamics, which is where the actual pattern lives.
this is not a per-request flow but a sequence of deployments and routing table
changes spread across the whole migration window.

```
 time -->

 phase 1, introduce         phase 2, migrate            phase 3, decommission
 the facade                 incrementally                and remove

 [Client]                   [Client]                     [Client]
    |                          |                             |
 [Facade]                   [Facade]                       [New System]
  all routes -> LEGACY     each landed feature flips
    |                       its route to NEW, one at
 [Legacy System]            a time, validated in           (Facade removed,
  100% of traffic           production before the           Client now talks
                             next route moves               to New System
                                 |             |             directly, unless
                              [Legacy]      [New System]     the Facade is
                              shrinking      growing         kept permanently
                              share          share            as an adapter
                                                               for old clients)
```

The second diagram is the one Microsoft's Azure Architecture Center depicts
directly, showing the facade routing "most requests to the legacy system"
initially, then shifting the balance over successive iterations, then routing
"all requests exclusively to the new system," and finally being removed so
"the client app communicates directly with the new system" (Microsoft, Azure
Architecture Center, verified 2026-08-02, description of the four-phase
diagram under Solution). One timing detail worth naming plainly. the facade's
routing table changes far more slowly than any single request's round trip,
often on the order of days or weeks between changes, which is exactly why the
pattern buys the option to observe a newly migrated route in production for
a real length of time before committing to the next one.

## 8. Implementation variants

**HTTP or API gateway interception.** The most common variant. an API
gateway, reverse proxy, or service mesh sits in front of the system and
routes by URL path, hostname, or header. AWS's reference implementation uses
Amazon API Gateway as this layer, with routes added one at a time as each
service migrates (AWS Prescriptive Guidance, verified 2026-08-02,
"Implementation"). This variant is cheapest to introduce when the system
already speaks HTTP, because most API gateway and reverse proxy products
support path-based and weighted routing out of the box.

**Database-level strangling.** Instead of, or in addition to, intercepting
calls, the target of migration is the shared monolithic database itself.
Domain-specific tables, stored procedures, and their data are extracted into
an isolated database per bounded context, one domain at a time, typically
using an extract-transform-load pass for the historical data followed by
change data capture to keep the new store synchronized until cutover, at
which point the corresponding objects are removed from the monolithic
database (Microsoft, Azure Architecture Center, verified 2026-08-02,
"Example"). This variant answers a different question than the HTTP variant.
it is not about who answers a request, it is about who owns a piece of data,
and the two are frequently combined, with the HTTP facade strangling the API
surface while a parallel data migration strangles the schema underneath it.

**Event or message-based interception.** Where the legacy system is
integrated through a message bus rather than synchronous calls, the
interception point becomes the topic or queue. a router consumes the
original topic and republishes to either the legacy consumer's queue or the
new consumer's queue based on message content or a routing key, and
producers never learn that a redirection is happening.

**Feature-flag strangling inside a single deployable.** When the legacy and
new implementations live in the same running process, for example during a
language-preserving internal rewrite of one module, the interception point
degenerates to an in-process conditional guarded by a feature flag or a
configuration value, rather than a network hop. This loses the strong
isolation of a network facade, since a bug in the new code path can still
crash the shared process, but it avoids the cost and latency of a separate
proxy tier and suits situations where a network seam genuinely does not
exist, see Branch by Abstraction in dimension 13, which is essentially this
variant given a name of its own.

**Managed cloud tooling.** Cloud vendors ship products purpose-built to
operate the facade and routing table so that application teams do not have
to hand-build and hand-operate a proxy tier. AWS Migration Hub Refactor
Spaces is the clearest named example. its own documentation states outright
that it "provides an application that models the Strangler Fig pattern for
incremental refactoring" by orchestrating "Amazon API Gateway, Network Load
Balancer, and resource-based AWS Identity and Access Management (IAM)
policies" behind a single external endpoint, and it links directly to
Fowler's original page as the definition it implements (AWS, "What is AWS
Migration Hub Refactor Spaces?",
https://docs.aws.amazon.com/migrationhub-refactor-spaces/latest/userguide/what-is-mhub-refactor-spaces.html,
verified 2026-08-02). See dimension 9 for its production status.

**Reverse strangler, for downstream dependents.** A variant named explicitly
by the UK Government Digital Service. once the new system exists, other
systems still depending on the legacy interface are given a wrapper that
presents the old interface backed by the new implementation, so those
dependents can be migrated onto the new system's semantics on their own
schedule rather than blocking the legacy system's decommissioning ("Moving
away from legacy systems", GOV.UK Service Manual,
https://www.gov.uk/service-manual/technology/moving-away-from-legacy-systems,
verified 2026-08-02, "you may want to employ a reverse of the strangler
pattern"). This is structurally the same Facade and routing idea, aimed the
opposite direction, at systems that call the one being replaced rather than
at the system's own external clients.

## 9. Known production uses

**UK Government Digital Service, GOV.UK Service Manual.** The organization
that runs the United Kingdom's central government digital services documents
the strangler pattern, by that name, as its own prescribed approach to
retiring legacy technology, describing it as introducing "the API we want as
a wrapper around the legacy system" so the legacy system can "be replaced
independently of our new code," alongside the named reverse-strangler variant
for downstream dependents. GOV.UK Service Manual, "Moving away from legacy
systems", https://www.gov.uk/service-manual/technology/moving-away-from-legacy-systems,
verified 2026-08-02.

**AWS Migration Hub Refactor Spaces.** A shipped, named AWS service whose own
documentation states it "models the Strangler Fig pattern for incremental
refactoring," orchestrating Amazon API Gateway, a Network Load Balancer, and
IAM policies to give customers a managed facade and routing layer for
production migrations, with a companion Iterative App Modernization Workshop
walking through a full worked example. The service was made unavailable to
new customers as of 7 November 2025, with AWS pointing existing users toward
AWS Transform for equivalent capability, but the documentation, its explicit
naming of the pattern, and the reference architecture remain published and
verifiable. AWS, "What is AWS Migration Hub Refactor Spaces?",
https://docs.aws.amazon.com/migrationhub-refactor-spaces/latest/userguide/what-is-mhub-refactor-spaces.html,
verified 2026-08-02, and AWS, "Strangler fig pattern", AWS Prescriptive
Guidance,
https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html,
verified 2026-08-02.

**Green Button DataCustodian, migrated with Domain-Driven Design and the
Strangler Fig pattern.** A peer-reviewed case study migrates the DataCustodian
reference implementation of the Green Button standard, the United States
energy-industry data-sharing initiative that lets utility customers download
their own standardized energy usage data, into a microservice architecture
using the Strangler Fig pattern paired with domain-driven design to identify
service boundaries. Shang-Pin Ma, Chia-Yu Li, Wen-Tin Lee, and Shin-Jie Lee,
"Microservice Migration Using Strangler Fig Pattern and Domain-Driven
Design", Journal of Information Science and Engineering, volume 38, issue 6,
November 2022, verified 2026-08-02 via the publication record at
National Cheng Kung University's research output service,
https://researchoutput.ncku.edu.tw/en/publications/microservice-migration-using-strangler-fig-pattern-and-domain-dri/.

**ThoughtWorks client engagements, published as a technique guide.**
ThoughtWorks, the consultancy Fowler is Chief Scientist of, publishes a
worked walkthrough of applying the pattern to a coupon-management API for
what it describes as "a large grocery retailer" it worked with, showing an
API gateway passthrough that exempts one modernized endpoint,
`GET /coupons`, while every other request continues to the legacy system
unchanged. ThoughtWorks does not name the retailer, so this is cited as a
documented consulting technique rather than a named company, distinct from
the three uses above which do name the operating organization or product.
ThoughtWorks, "Embracing the Strangler Fig pattern for legacy modernization,
part one",
https://www.thoughtworks.com/en-us/insights/articles/embracing-strangler-fig-pattern-legacy-modernization-part-one,
verified 2026-08-02.

## 10. Consequences

Positive.

- Migration proceeds in small, independently shippable, independently
  reversible increments, so a defect in the new implementation of one piece
  never takes down the pieces that have not moved yet or the pieces that have
  already proven themselves.
- The legacy system keeps earning its keep throughout the migration. there is
  no feature freeze forced on the business while the new system catches up,
  because new features can be built directly in the new system's target
  architecture from day one.
- Confidence in the new system builds from real production traffic and real
  production data, one slice at a time, rather than from a specification the
  rewrite team hoped was complete.
- Rollback of any single migrated piece is a routing table change, not a
  full-system restore, which lowers the cost of admitting a mistake and
  therefore makes the team more willing to ship early and often.
- Multiple teams can migrate different pieces in parallel behind the shared
  facade once it exists, without a shared release train, as long as the
  routing table's ownership is coordinated.

Negative.

- Two systems must be operated, monitored, secured, and kept correct for as
  long as the coexistence phase lasts, which is a real, recurring cost on top
  of what either system alone would cost, and that duration is often
  underestimated at the start.
- The facade itself becomes critical infrastructure. every request, migrated
  or not, now depends on it, so its own availability, latency, and capacity
  become a new operational surface that did not exist before the migration
  began.
- Cross-system calls during coexistence need an anti-corruption layer or an
  equivalent adapter, which is itself code that must be built, tested, and
  eventually torn down, adding real effort that produces no lasting value
  beyond the migration window.
- Shared data that both systems touch needs an explicit synchronization
  strategy, and every synchronization strategy trades away either strict
  consistency, write latency, or operational simplicity, as AWS's own guidance
  concedes when it calls dual-write synchronization "a tactical solution
  until you can establish a long-term solution" (AWS Prescriptive Guidance,
  verified 2026-08-02, "Data consistency").
- The pattern has no forcing function that compels completion. as dimension
  11 covers, the absence of a hard deadline that a full rewrite would have
  imposed is exactly what lets a strangler fig migration continue
  indefinitely without ever finishing.

## 11. Failure modes and misuse

**The migration stalls and the organization runs two systems forever.**
Symptom. eighteen months, three years, five years after the migration
started, the legacy system is still handling a meaningful share of traffic,
the routing table has not changed in a quarter, the team that started the
migration has partly rotated onto other work, and nobody can say with
confidence when, or whether, the legacy system will be fully retired. New
engineers joining the team have to learn both systems and the routing rules
between them just to be productive, which is a permanent tax the pattern was
supposed to be temporary. Cause. this is engineering judgment drawn from how
the pattern's own incentives work, not a claim from a specific measured
study. Because each migrated piece delivers value on its own and nothing
forces the LAST piece to move, the pattern trades the forced completion of a
big-bang rewrite for a completion that depends entirely on sustained
organizational will. Once the easiest, highest-value routes have moved, the
routes left tend to be the hardest ones, often exactly the parts of the
legacy system too tangled or too poorly understood to have been migrated
first, and those are also the routes most likely to be deprioritized the
moment a business emergency competes for the same engineers. The coexistence
period, deliberately built to be low-drama, has no equivalent of a rewrite's
hard cutover date to force a decision. Fix. treat the migration as a project
with an owner, a budget, and a target completion state from day one, not an
open-ended technical improvement. Track the routing table's shrinking legacy
share as a first-class metric that is reviewed on a cadence, the same way an
error budget or a cost budget is reviewed, and set an explicit deadline after
which the remaining legacy routes are treated as a dedicated project rather
than background work squeezed between features. Some teams schedule a
deliberate, time-boxed "strangulation sprint" once the easy routes are gone,
specifically to keep the hard tail from becoming permanent.

**The anti-corruption layer never gets removed.** Symptom. a class named
something like `LegacyUserAdapter` or `UserServiceFacade`, built as a
temporary translation layer, is still present in the codebase years after the
service it was adapting for finished migrating, and new code has started
depending on it as if it were permanent infrastructure. Cause. removing an
adapter that still works produces no visible benefit and carries a small risk
of breaking something, so it is deprioritized indefinitely, exactly the same
incentive problem as the legacy system itself. Fix. attach the ACL's removal
to the same completion criteria as the migrated piece it exists for, and
track it in the same backlog, so "migration done" explicitly includes "ACL
removed," not just "new system live."

**The facade becomes an unplanned bottleneck or single point of failure.**
Symptom. a latency spike or an outage in the facade layer takes down both the
legacy and the new system simultaneously, even though neither system itself
is degraded, and the incident review discovers the facade was sized for the
traffic the legacy system alone used to receive, not for a proxy layer that
now sits in front of everything. Cause. teams frequently under-invest in the
facade because it is seen as glue code rather than a product, when in fact it
is now the single most load-bearing component in the architecture. AWS names
this directly as a risk to plan for, recommending a serverless, multi-availability-
zone product specifically to mitigate it (AWS Prescriptive Guidance, verified
2026-08-02, "Proxy layer failure"). Fix. treat the facade with the same
production rigor as any tier-one service. capacity planning, health checks,
graceful degradation, and its own on-call ownership, from the day it is
introduced, not after the first incident it causes.

**Data drifts silently between the two systems during coexistence.** Symptom.
a customer sees different values for the same piece of information depending
on which code path happened to serve their request, discovered not by
monitoring but by a support ticket. Cause. an ad hoc or partially implemented
synchronization mechanism, often a queue-and-agent pattern added quickly to
unblock one migrated feature, that has gaps under specific failure conditions
such as a dropped message, an out-of-order update, or a race between two
writers. Fix. make the synchronization mechanism's correctness a tested,
monitored property in its own right, with reconciliation checks that compare
the two stores on a schedule and alert on divergence, rather than trusting the
mechanism to be correct because it was correct in initial testing.

**Premature strangling along the wrong domain boundaries.** Symptom. the new
system ends up with the same tangled coupling the legacy system had, just
spread across more deployable units, and cross-service calls multiply faster
than the migration progresses. Cause. routes, tables, or features were peeled
off in whatever order was easiest to code first, rather than along real
domain boundaries, so the seams chosen do not match where the actual
coupling in the business logic lives. Fix. invest in understanding the domain
before choosing what to strangle first. AWS recommends domain-driven design
and event storming specifically to avoid this (AWS Prescriptive Guidance,
verified 2026-08-02, "Unclear domain"), and the peer-reviewed Green Button
case study pairs the pattern with domain-driven design for the same reason
(Ma, Li, Lee, and Lee, Journal of Information Science and Engineering,
verified 2026-08-02).

**The pattern is used as cover for never finishing a decision.** Symptom. the
existence of the strangler facade is cited, repeatedly, as the reason a hard
architectural decision, such as which system owns a given piece of data, does
not need to be made yet, and the deferral compounds over successive migrated
features until the ownership question becomes far more expensive to resolve
than it would have been at the start. Cause. the pattern's genuine strength,
letting migration proceed without answering every question up front, gets
mistaken for a license to answer no questions at all. Fix. distinguish
between decisions the pattern genuinely lets you defer, such as exactly when
a given low-traffic route migrates, and decisions it does not, such as who
owns a piece of shared data once more than one system reads or writes it, and
force the second category to a decision at the point the second caller
appears, not later.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Strangler Fig | Big-bang rewrite | Branch by Abstraction | Parallel Run (shadow) | Blue-green deployment |
|---|---|---|---|---|---|
| Risk per unit of change | Low. one route or table at a time | High. the whole system switches at once | Low. one abstraction seam, in-process | Low to the read path, real writes still risky | Medium. whole deployable switches, but instantly reversible |
| Feature delivery during migration | Continues normally in both systems | Usually frozen or slowed on the legacy side | Continues, since the same deployable ships either way | Continues, the shadow path adds no user-visible risk | Continues on whichever environment is live |
| Operational cost during transition | High. two systems, a facade, and often an ACL | Low until cutover, then a spike of risk | Low. no second deployable or facade | Medium. traffic is duplicated to a target that does no real work yet | Low to medium. two environments, but no facade needed |
| Natural forcing function to finish | Weak, see dimension 11 | Strong. the cutover date is the finish line | Weak, same incentive problem as here | Strong for validation, but still needs a separate cutover step | Strong. the old environment is decommissioned quickly |
| Granularity of migration | Fine. per route, table, tenant, or feature | Coarse. the whole system | Fine, but limited to in-process code paths | Coarse. validates the whole new system before any real cutover | Coarse. whole deployable |
| Where it shines | Large, long-lived systems with external clients that cannot change | Small systems, or systems that must be replaced by a hard deadline | A rewrite confined to one codebase, no separate deployable wanted | High confidence needed in a new system's correctness before it takes real traffic | Stateless services where a full environment swap is cheap |
| Cross-system data consistency needs | Must be designed explicitly, often the hardest part | Not applicable, only one system is ever live | Not applicable, one deployable, one data store | The shadow path reads real data but its writes are typically discarded, so consistency questions are avoided rather than solved | Not applicable if both environments share the same data store |

Reading of the table. the Strangler Fig pattern wins specifically when the
system is large, has external callers that cannot be forced to change on a
fixed date, and the organization can sustain a longer transition in exchange
for a much smaller blast radius per change. A big-bang rewrite wins when the
system is small enough, or the deadline hard enough, that the coordination
overhead of running two systems is not worth paying. Branch by Abstraction is
the right tool when the change stays inside one codebase and never needs a
second, independently deployable system. Parallel Run is complementary
rather than competing. it is frequently used inside a Strangler Fig migration
to validate one specific migrated piece's correctness before flipping its
route for real, see dimension 13. Blue-green deployment solves a different
problem, an instant, whole-environment cutover, and composes naturally with
Strangler Fig as the mechanism used for the final decommissioning step once
every route has moved.

## 13. Related and incompatible patterns

- **Anti-Corruption Layer.** The most frequent companion. wherever the legacy
  and new systems must call each other during coexistence, an ACL translates
  between their models so neither is forced to adopt the other's shape. Its
  lifetime inside a Strangler Fig migration is explicitly temporary, unlike a
  standalone ACL used permanently to isolate a system from an external
  dependency's model. AWS's own reference implementation names and builds
  this exact combination (AWS Prescriptive Guidance, verified 2026-08-02).
- **Branch by Abstraction.** The in-process cousin of this pattern. where
  Strangler Fig routes traffic between two separately deployable systems
  through an external facade, Branch by Abstraction introduces an interface
  inside a single codebase and switches implementations behind it, typically
  guarded by a feature flag, with no separate deployable and no network hop.
  The two are often confused because both describe gradual replacement behind
  a seam, but Branch by Abstraction cannot answer the case where the
  replacement genuinely needs to be a separate service, and Strangler Fig is
  unnecessarily heavy for a change that stays inside one process.
- **Feature Toggle.** A frequent implementation detail inside both of the
  patterns above. the routing decision at the facade, or the branch decision
  inside a single process, is commonly implemented as a feature flag lookup,
  which gives operators a fast, centrally controlled way to move a route
  without a redeploy. Feature Toggle is a general-purpose mechanism. Strangler
  Fig is one of many patterns that uses it.
- **Circuit Breaker.** Composes cleanly and is frequently necessary rather
  than optional. once the facade or an ACL is calling across a network
  boundary between the two systems, that call needs the same protection any
  cross-service call needs, so a failing new system does not cascade a
  failure into a legacy system that was working fine on its own, and vice
  versa.
- **Parallel Run (also called Shadow Traffic or Dark Launch).** A frequent
  validation step used before a route's traffic is actually flipped at the
  facade. the new implementation receives a copy of real production traffic,
  its output is compared against the legacy system's real answer, and only
  once the two agree over a real production workload does the route's traffic
  in the facade genuinely switch. Parallel Run answers whether the new
  implementation is correct, while Strangler Fig answers how to cut over
  without risk, and the two combine naturally, with Parallel Run typically
  running just before a given route's Strangler Fig cutover.
- **Blue-Green Deployment.** Usually the mechanism used for the pattern's
  final step, decommissioning. once every route has been strangled onto the
  new system and the legacy system carries no live traffic, taking the legacy
  environment fully offline, or cutting the facade itself over to point
  directly at the new system, is naturally executed as a blue-green switch,
  since at that point it is a whole-environment cutover with nothing left to
  migrate piece by piece.
- **CQRS and Event Sourcing.** Frequently entangled with the database-level
  variant of this pattern, described in dimension 8. extracting a domain's
  data into its own store often happens alongside a move to separate read and
  write models or to an event-sourced history, but the two are independent
  decisions. a team can strangle a monolith's database into per-domain stores
  without adopting either CQRS or event sourcing in the target stores.
- **Big-bang rewrite.** Directly competing, not composing. see dimension 12
  for when each wins. a team occasionally starts a Strangler Fig migration
  and, having proven the new system's viability on the first few migrated
  pieces, switches strategy and cuts the remaining, less-coupled pieces over
  in one deliberate final move rather than continuing piecemeal, which is a
  legitimate hybrid rather than a failure of either pattern.

## 14. Refactoring path in and out

Introducing the pattern into a system that has none of this infrastructure
yet.

1. Identify the seam. find the point every external caller already passes
   through, whether that is a load balancer, a reverse proxy, an API gateway,
   or, if none exists yet, the single entry point of the deployable itself.
   Confirm every caller genuinely goes through this point. a seam that
   catches ninety percent of traffic but is silently bypassed by a legacy
   batch job or an old mobile client version defeats the pattern for exactly
   the traffic that bypasses it.
2. Insert the facade at that seam, initially configured to route one hundred
   percent of traffic to the legacy system unchanged. Deploy this step on its
   own and verify, in production, that behavior is identical to before the
   facade existed. This step should be invisible to every caller and carries
   its own real risk, since a bug in the facade itself, even one routing
   everything to the unchanged legacy system, can still take the whole system
   down.
3. Pick the first piece to migrate using two criteria together, not one.
   pick something with real, if modest, business value once migrated, and
   pick something whose domain boundary is well understood, so the team's
   first migration proves the mechanism works without also fighting an
   unclear domain model. AWS's own worked example starts with a self-contained
   user service for exactly this reason (AWS Prescriptive Guidance, verified
   2026-08-02).
4. Build the first piece in the new system. where the new implementation
   needs to call functionality that has not migrated yet, build the
   anti-corruption layer for that specific call, scoped as narrowly as the
   current piece needs, not speculatively for calls that might be needed
   later.
5. If shared data is involved, put a synchronization mechanism in place and
   validate it against real data before cutting the route over, using a
   Parallel Run if the risk of the new implementation being wrong is
   meaningful. see dimension 13.
6. Flip the facade's routing entry for this one piece from legacy to new.
   Watch it in production. keep the legacy code path for this piece intact
   and reachable for a defined rollback window rather than deleting it
   immediately, so a defect discovered after cutover can be reverted with a
   routing change rather than a redeploy.
7. Once the piece is proven stable past its rollback window, delete the
   corresponding legacy code path and, if it exists, the corresponding half
   of the anti-corruption layer. This step is frequently skipped in practice,
   which is exactly the failure mode in dimension 11. treat it as part of
   "done," not as optional cleanup.
8. Repeat steps 3 through 7 for the next piece, tracking the shrinking legacy
   share as a metric the team reviews on a cadence, not merely as a side
   effect of individual migrations happening.

Removing the pattern once the migration is complete.

1. Confirm the routing table sends one hundred percent of traffic to the new
   system and has for a defined stability period, with no remaining legacy
   code paths reachable.
2. Decommission the legacy system's infrastructure. servers, databases no
   longer written to, and any scheduled jobs that existed only to support it.
3. Decide the facade's fate. some teams remove it entirely and repoint
   clients directly at the new system, which requires every client to be
   updated, or, where clients cannot be changed, some teams deliberately keep
   the facade permanently as a stable public interface in front of an
   internal architecture that may keep evolving, which Microsoft's own
   guidance explicitly allows as an option, calling it maintaining the facade
   "as an adapter for legacy clients to use while you update the core system
   for newer clients" (Microsoft, Azure Architecture Center, verified
   2026-08-02, "Problems and considerations").
4. If any reverse-strangler wrappers were built for downstream dependents,
   confirm each dependent has migrated onto the new system's real interface
   before removing its wrapper, per the GOV.UK guidance's own caution that
   these wrappers exist specifically to let dependents move on their own
   schedule (GOV.UK Service Manual, verified 2026-08-02).

## 15. Testing and verification

Easier because of the pattern.

- Each migrated piece can be tested and validated on its own, against real
  production traffic if a Parallel Run precedes its cutover, without the new
  system needing to be complete or correct end to end first.
- Rollback itself is directly testable. a game-day exercise can flip a
  route's flag back to legacy and confirm the system behaves correctly,
  something that is meaningless to rehearse against a big-bang rewrite, which
  has no equivalent partial-rollback state.
- The facade's routing table gives a single, inspectable source of truth for
  which system currently owns which piece of functionality, which supports a
  simple, high-value contract test. assert, for every route the team believes
  has been migrated, that the facade actually routes it to the new system,
  catching the same kind of forgotten-flip mistake that a forgotten override
  causes in Factory Method.

Harder because of the pattern.

- A full-flow test that spans both a migrated and
  an unmigrated piece must account for a request crossing the facade,
  possibly the ACL, and both systems, which is a longer and more fragile path
  to set up in a test environment than testing either system in isolation.
- Data consistency between the two systems is not something a request-response
  test alone can verify. it needs its own reconciliation tests that compare
  state between the legacy and new stores after a representative volume of
  writes, ideally on a recurring schedule in production, not only once in a
  staging environment.
- A defect in the interaction between the ACL and either system can be
  invisible to unit tests of either system alone, since neither system, taken
  by itself, is doing anything wrong. only the translation between them is.

Techniques that apply.

- **Parallel Run with a diffing tool.** Route a copy of real production
  requests to the candidate new implementation, discard its side effects, and
  compare its response against the legacy system's real response,
  automatically flagging divergence. This is the strongest verification
  technique available for this pattern precisely because it tests against
  real traffic shapes rather than a test suite's guesses about what real
  traffic looks like.
- **Contract tests at the facade.** One test suite asserting the routing
  table's actual state matches the team's intended migration state, run on
  every deployment of the facade's configuration, catching accidental
  regressions where a route silently reverts to legacy, for example because a
  configuration rollback undid an intentional flip along with an unintentional
  one.
- **Reconciliation jobs as tests, not only as production tooling.** The same
  job that compares the legacy and new data stores in production doubles as a
  correctness test when run against a synthetic, seeded dataset in a lower
  environment, giving fast feedback on synchronization logic changes without
  needing real production data.
- **Chaos and rollback drills on the facade itself.** Given the facade's
  criticality, described in dimension 3 and dimension 11, its failure modes
  deserve the same deliberate testing any tier-one service gets. what happens
  to a request if the new system times out, if the routing table fails to
  load, if the ACL itself errors.

## 16. Observability signals

The facade is the single point where the whole migration's progress and
health are visible, so it deserves purpose-built instrumentation from the
day it is introduced, not after the first incident.

What to record.

- A counter of requests, labelled by route and by which system, legacy or
  new, actually served each one. This single signal, tracked over the whole
  migration window, is the most direct measure of migration progress that
  exists, and it is the number that should be reviewed on a cadence to catch
  the stall described in dimension 11 before it becomes a permanent state.
- Latency and error rate, labelled the same way, so a newly migrated route's
  behavior can be compared directly against the same route's historical
  behavior when it was still served by the legacy system, which is the
  cleanest signal available that a migration made things worse rather than
  better.
- The facade's own health. its request rate, latency, and error rate as a
  component in its own right, separate from either backend, since the facade
  can fail in ways neither backend causes, for example a bad deployment of
  its routing configuration.
- For any synchronization mechanism, a divergence count from the
  reconciliation job comparing the legacy and new data stores, and the age of
  the oldest unresolved divergence, which surfaces silent data drift before a
  customer does.
- A gauge, reviewed on a fixed cadence rather than only glanced at
  informally, of the count and share of routes still pointed at the legacy
  system, alongside the date each remaining route was last touched, which
  turns dimension 11's failure mode into something a dashboard can catch
  rather than something discovered by accident eighteen months later.

A healthy instance on a dashboard. the share of traffic served by the new
system climbs steadily over the migration window, latency and error rate for
newly migrated routes track close to their legacy predecessors or improve,
the facade's own error rate stays flat and low regardless of how the routing
mix shifts underneath it, and the reconciliation divergence count sits at or
near zero with no long-lived unresolved entries.

A failing instance. the legacy traffic share plateaus for an extended period
with no explanation tied to an active migration effort, which is the leading
indicator of the stall in dimension 11. a newly migrated route shows a
latency or error spike relative to its legacy baseline, which points at a
correctness or capacity problem in the new implementation rather than at the
migration mechanism itself. the facade's own error rate rises independent of
either backend's health, which points at the facade becoming the bottleneck
named in dimension 11. or the reconciliation divergence count grows instead
of shrinking, which means the synchronization mechanism is losing ground
against the write rate rather than keeping the two stores aligned.

## 17. Security and privacy implications

The pattern changes the system's attack surface and its data handling in
several concrete ways, each of which is a genuine implication rather than an
invented concern.

**The facade is a new, and now unavoidable, network boundary.** Every request
to either system, migrated or not, now passes through the facade, which makes
it the single place where authentication, authorization, rate limiting, and
input validation can be enforced consistently across both the legacy and new
systems during the entire migration. Conversely, a vulnerability or a
misconfiguration in the facade itself, for example a routing rule that
accidentally exposes an internal-only endpoint to external callers, now
compromises whichever system that route points to, legacy or new, in a way
that bypasses whatever protections either system had on its own before the
facade existed. AWS's guidance for the pattern already treats the facade as
a piece of production infrastructure deserving of the same rigor as any
other, for reliability reasons (AWS Prescriptive Guidance, verified
2026-08-02, "Proxy layer failure"), and the same rigor applies for security.

**The anti-corruption layer is a translation point where data can leak or be
mishandled.** Because the ACL exists specifically to reshape data between two
different models, it is a place where a field that carried an implicit
access restriction in one system's model, for example a flag meaning that
data must not be exposed to a certain class of caller, can be silently
dropped or misapplied during translation, exposing data that neither system
alone would have exposed under its own rules. Review the ACL's field-by-field
mapping specifically for access-control and data-classification fields, not
only for functional correctness.

**Two systems, two attack surfaces, for the whole coexistence window.**
Every vulnerability class that applies to the legacy system continues to
apply to it for as long as it keeps running, even for pieces of functionality
that have already been migrated elsewhere, because the legacy code for an
unmigrated piece is still live and reachable through the facade. A team that
stops patching the legacy system's dependencies once migration begins,
reasoning that it is "going away soon," extends its real exposure window for
exactly as long as the migration in dimension 11 can stall for, which, left
unmanaged, is measured in years rather than weeks.

**Data synchronization mechanisms widen where sensitive data flows.** A
queue-and-agent or change-data-capture mechanism built to keep the legacy and
new data stores aligned during coexistence, described in dimensions 2 and 8,
is a new path that customer data now travels through, and it needs the same
encryption in transit, access control, and audit logging any other data
pipeline carrying the same class of data would need. It is common for this
mechanism to be built quickly to unblock one migrated feature and to receive
less security review than either of the two systems it connects, precisely
because it looks like glue code rather than a first-class data path.

On privacy specifically, the dual-write or synchronization period the
pattern often introduces means a person's data can, for a real window of
time, exist in two places with two different retention and deletion
policies, if the two systems were not built to the same policy from the
start. a deletion or a consent withdrawal processed against one system during
coexistence must be confirmed to actually propagate to the other, or the
organization can find itself still holding data it told a person, and
possibly a regulator, it had deleted.

## 18. References

1. Martin Fowler. "Strangler Fig Application". martinfowler.com bliki.
   Originally published 2004, title changed and page revised 22 August 2024.
   https://martinfowler.com/bliki/StranglerFigApplication.html
   Verified 2026-08-02. Source of the name, the rename rationale, the tree
   metaphor, and the original narrow framing of the pattern.
2. Microsoft. "Strangler Fig pattern". Azure Architecture Center.
   https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig
   Verified 2026-08-02. Source for the context and problem framing, the
   four-phase facade diagram, the issues and considerations list, the
   database-level migration example, and the option to retain the facade
   permanently after migration.
3. AWS. "Strangler fig pattern". AWS Prescriptive Guidance, Cloud Design
   Patterns guide.
   https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html
   Verified 2026-08-02. Source for the code-base-access and small-application
   non-applicability points, the anti-corruption layer worked example, the
   data synchronization guidance, the proxy layer failure risk, and the AWS
   Migration Hub Refactor Spaces reference architecture.
4. AWS. "What is AWS Migration Hub Refactor Spaces?"
   https://docs.aws.amazon.com/migrationhub-refactor-spaces/latest/userguide/what-is-mhub-refactor-spaces.html
   Verified 2026-08-02. Source for the named production tool that explicitly
   states it models the Strangler Fig pattern, and its retirement to new
   customers as of 7 November 2025.
5. GOV.UK Service Manual. "Moving away from legacy systems".
   https://www.gov.uk/service-manual/technology/moving-away-from-legacy-systems
   Verified 2026-08-02. Source for the named production use by the UK
   Government Digital Service, and for the reverse strangler variant.
6. Shang-Pin Ma, Chia-Yu Li, Wen-Tin Lee, and Shin-Jie Lee. "Microservice
   Migration Using Strangler Fig Pattern and Domain-Driven Design". Journal
   of Information Science and Engineering, volume 38, issue 6, November
   2022. Publication record verified 2026-08-02 via
   https://researchoutput.ncku.edu.tw/en/publications/microservice-migration-using-strangler-fig-pattern-and-domain-dri/
   Source for the peer-reviewed Green Button DataCustodian production case
   study, and for pairing the pattern with domain-driven design.
7. ThoughtWorks. "Embracing the Strangler Fig pattern for legacy
   modernization, part one".
   https://www.thoughtworks.com/en-us/insights/articles/embracing-strangler-fig-pattern-legacy-modernization-part-one
   Verified 2026-08-02. Source for the anonymized retailer coupon-management
   worked example and the API gateway passthrough implementation detail.
8. Sam Newman. "Pattern. Strangler Fig Application". Companion reference site
   for the book Monolith to Microservices. O'Reilly Media, 2019, ISBN
   978-1-4920-4783-4.
   https://samnewman.io/patterns/refactoring/strangler-fig-application/
   Verified 2026-08-02. Source confirming the pattern's coverage in Newman's
   book and its wrap-and-intercept framing.
9. Wikipedia contributors. "Strangler fig pattern".
   https://en.wikipedia.org/wiki/Strangler_fig_pattern
   Verified 2026-08-02. Used only to confirm the Fowler attribution and the
   Ship of Theseus alias, not as a source of technical explanation.

## Code examples

Three languages, chosen because each shows a different, genuinely idiomatic
way to build the facade's routing decision. TypeScript shows the network
facade as it is usually implemented today, a thin HTTP layer holding a
routing table. Python shows the same idea plus an explicit
Anti-Corruption Layer, because Python is the language most of the cited
guidance's worked examples use for adapter code. Go shows the in-process
variant, closer to Branch by Abstraction, because Go's `net/http` makes a
single-process reverse proxy short enough to read in full. Rust is omitted
because the pattern's shape is identical to the Go version once written in
any statically typed, compiled language with an HTTP library, and showing it
a third time would not add a genuinely new implementation idea.

### TypeScript

A facade that owns a routing table keyed by path, and forwards to whichever
backend the table currently names. This is the shape most API gateway and
reverse proxy configurations encode declaratively, shown here in code so the
decision logic is explicit.

```typescript
type Backend = "legacy" | "new";

interface RouteTable {
  [path: string]: Backend;
}

class StranglerFacade {
  constructor(
    private routes: RouteTable,
    private legacy: (path: string) => string,
    private replacement: (path: string) => string,
  ) {}

  handle(path: string): { backend: Backend; body: string } {
    const backend = this.routes[path] ?? "legacy";
    const body =
      backend === "new" ? this.replacement(path) : this.legacy(path);
    return { backend, body };
  }

  migrate(path: string): void {
    this.routes[path] = "new";
  }

  rollback(path: string): void {
    this.routes[path] = "legacy";
  }
}

const legacySystem = (path: string) => `legacy handled ${path}`;
const newSystem = (path: string) => `new system handled ${path}`;

const facade = new StranglerFacade(
  { "/account": "legacy" },
  legacySystem,
  newSystem,
);

console.log(facade.handle("/account"));
facade.migrate("/user");
console.log(facade.handle("/user"));
facade.rollback("/user");
console.log(facade.handle("/user"));
```

### Python

The same facade, plus an Anti-Corruption Layer used when a migrated route's
handler needs to call back into the legacy system for data that has not
moved yet, translating between the two systems' shapes.

```python
from dataclasses import dataclass


@dataclass
class LegacyUser:
    user_id: int
    full_name: str


@dataclass
class NewUser:
    id: str
    name: str


class UserAntiCorruptionLayer:
    def __init__(self, legacy_lookup):
        self._legacy_lookup = legacy_lookup

    def get_user(self, user_id: str) -> NewUser:
        legacy = self._legacy_lookup(int(user_id))
        return NewUser(id=str(legacy.user_id), name=legacy.full_name)


class StranglerFacade:
    def __init__(self):
        self.routes: dict[str, str] = {}

    def route_for(self, path: str) -> str:
        return self.routes.get(path, "legacy")

    def migrate(self, path: str) -> None:
        self.routes[path] = "new"

    def handle(self, path: str, legacy_handler, new_handler) -> str:
        if self.route_for(path) == "new":
            return new_handler(path)
        return legacy_handler(path)


def legacy_user_lookup(user_id: int) -> LegacyUser:
    return LegacyUser(user_id=user_id, full_name="Ada Lovelace")


def legacy_handler(path: str) -> str:
    return f"legacy handled {path}"


if __name__ == "__main__":
    acl = UserAntiCorruptionLayer(legacy_user_lookup)

    def new_handler(path: str) -> str:
        user = acl.get_user("42")
        return f"new system handled {path} for {user.name}"

    facade = StranglerFacade()
    print(facade.handle("/account", legacy_handler, new_handler))

    facade.migrate("/account")
    print(facade.handle("/account", legacy_handler, new_handler))
```

### Go

A single-process reverse proxy, the shape the pattern takes when the
interception point is a real network hop but the whole thing runs as one
small standalone service rather than a managed gateway product.

```go
package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"sync"
)

type StranglerFacade struct {
	mu     sync.RWMutex
	routes map[string]string
	legacy http.Handler
	newSvc http.Handler
}

func NewStranglerFacade(legacy, newSvc http.Handler) *StranglerFacade {
	return &StranglerFacade{
		routes: make(map[string]string),
		legacy: legacy,
		newSvc: newSvc,
	}
}

func (f *StranglerFacade) Migrate(path string) {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.routes[path] = "new"
}

func (f *StranglerFacade) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	f.mu.RLock()
	backend := f.routes[r.URL.Path]
	f.mu.RUnlock()

	if backend == "new" {
		f.newSvc.ServeHTTP(w, r)
		return
	}
	f.legacy.ServeHTTP(w, r)
}

func main() {
	legacy := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "legacy handled %s", r.URL.Path)
	})
	newSvc := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "new system handled %s", r.URL.Path)
	})

	facade := NewStranglerFacade(legacy, newSvc)

	server := httptest.NewServer(facade)
	defer server.Close()

	before, _ := http.Get(server.URL + "/user")
	fmt.Println("before migration", readAll(before))

	facade.Migrate("/user")

	after, _ := http.Get(server.URL + "/user")
	fmt.Println("after migration", readAll(after))
}

func readAll(resp *http.Response) string {
	defer resp.Body.Close()
	buf := make([]byte, 128)
	n, _ := resp.Body.Read(buf)
	return string(buf[:n])
}
```
