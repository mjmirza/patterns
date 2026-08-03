---
name: Service per Team
slug: service-per-team
family: 10-microservices
category: Structural
aliases: [Team-Owned Service, You Build It You Run It, Single-Team-Owned Service, Stream-Aligned Service Ownership]
first_described: "Conway 1968; Vogels 2006; Richardson 2018; Skelton and Pais 2019"
maturity: canonical
related: [decompose-by-business-capability, decompose-by-subdomain, api-gateway, backends-for-frontends, strangler-fig, saga]
incompatible_with: [layered-architecture]
verified: 2026-08-02
---

# Service per Team

## 1. Name, aliases, and lineage

The canonical name in this catalog is Service per Team. It has no single
inventor and no single publication of origin the way a Gang of Four pattern
does, because it is an organizational pattern that several independent lines
of practice converged on from different directions across four decades. The
underlying mechanism was described first, the pattern was practiced next, and
the name came last, applied after the fact by people writing about
microservices in the 2010s.

The mechanism traces to Melvin E. Conway, "How Do Committees Invent",
*Datamation*, April 1968, which states that "organizations which design
systems (in the broad sense used here) are constrained to produce designs
which are copies of the communication structures of these organizations"
(https://www.melconway.com/Home/Committees_Paper.html, verified 2026-08-02).
Conway's paper is not about microservices, it predates the term by decades,
but it supplies the causal claim this pattern depends on. team boundaries
become system boundaries whether an architect intends it or not. Conway
himself later wrote a retrospective in which he extended the same claim past
software into any complex system a group of people designs together, from
housing policy to healthcare delivery, which is worth knowing because it
signals the law is about communication topology in general, not about code
specifically (https://www.melconway.com/Home/Committees_Paper.html, verified
2026-08-02).

The operational half of the name comes from Amazon. Werner Vogels, Amazon's
CTO, described the practice in an interview conducted by Jim Gray, "A
Conversation with Werner Vogels", *ACM Queue*, volume 4, number 4, 30 June
2006, where he says "You build it, you run it. This brings developers into
contact with the day-to-day operation of their software." He contrasts this
against the older model where software was handed to a separate operations
group once it was written, and states that giving builders operational
responsibility improved the quality of the resulting services because the
people who wrote the code were the same people paged when it broke
(https://queue.acm.org/detail.cfm?id=1142065, verified 2026-08-02). This is
the phrase most engineers reach for when they name the pattern in
conversation, and it is doing real work in the name. it says the team is not
just an owner on an org chart, it is the on-call rotation.

The pattern language name comes from Chris Richardson, who catalogs
microservices patterns at microservices.io and in *Microservices Patterns.
With Examples in Java*, Manning, 2018. Richardson's site states the rule
directly. "A service is owned by the team (or teams) that owns the
(non-library) subdomains" and lists "Team autonomy, a team needs to be able to
develop, test and deploy their software independently of other teams" as one
of the forces a decomposition must satisfy
(https://microservices.io/patterns/microservices.html, verified 2026-08-02).
Richardson treats service ownership as a consequence of his decomposition
patterns (Decompose by Business Capability, Decompose by Subdomain) rather
than as an independent pattern with its own name, which is one reason this
entry exists separately in this catalog. the ownership rule deserves its own
treatment because getting it wrong is a distinct and common failure
independent of getting the service boundaries right.

The most complete treatment of the organizational side is Matthew Skelton and
Manuel Pais, *Team Topologies. Organizing Business and Technology Teams for
Fast Flow*, IT Revolution Press, 2019. Skelton and Pais name the
"stream-aligned team" as the team type "aligned to a flow of work from
(usually) a segment of the business domain," describe it operating as an
end-to-end owner of its value stream under a "You Build It, You Run It"
philosophy that eliminates handoffs to other teams, and define three
interaction modes (collaboration, X-as-a-Service, facilitation) that describe
how a service-owning team's boundary is meant to behave toward its neighbors
(https://teamtopologies.com/key-concepts, verified 2026-08-02). Team
Topologies is the source most engineering organizations cite today when they
adopt the pattern deliberately rather than backing into it, because it gives
the pattern a vocabulary for the boundary itself, not just the ownership
claim.

Martin Fowler and James Lewis, "Microservices", martinfowler.com, 25 March
2014, tie these threads together in the article that popularized the term
microservice. They write that these systems favor "splitting up into services
organized around business capability" rather than technology layers, quote
Conway's Law directly, state that "Consequently the teams are cross
functional, including the full range of skills required for the development,"
and cite Amazon's you-build-it-you-run-it practice by name as the production
example, alongside the "Two Pizza Team" heuristic for keeping a service-owning
team small enough to stay coherent
(https://martinfowler.com/articles/microservices.html, verified 2026-08-02).

Aliases in real use. **You Build It You Run It**, from the Vogels quote
directly, used when the emphasis is operational responsibility rather than
code ownership. **Team-Owned Service** or **Single-Team-Owned Service**, used
in platform engineering writing when the emphasis is the cardinality
constraint (dimension 4 explains why one team, never many, matters).
**Stream-Aligned Service Ownership**, used by teams that have explicitly
adopted Team Topologies vocabulary. All four names describe the same
structural claim from a different angle, a service has exactly one team that
can change it, deploy it, and answer for it at 3 a.m.

## 2. Problem and context

A system has been split into services, using Decompose by Business Capability
or Decompose by Subdomain or simply by growing that way over years. The
services now exist as separate deployables. The question this pattern answers
is not how to draw the boundaries, that is a separate concern covered by the
decomposition patterns. it is who stands behind each boundary once it is
drawn.

Two failure shapes recur when this question is left unanswered.

The first is shared ownership. Two or more teams can each change a service's
code and each deploy it. In principle this sounds like resilience, more
people can fix it if one team is unavailable. In practice it produces the
opposite. Neither team feels fully responsible for the service's health, so
neither team invests the unglamorous maintenance work, upgrading a dependency,
paying down a slow query, improving the test suite, because that investment
benefits the other team's velocity as much as their own and free-riding is
individually rational. Deployments collide because two teams schedule releases
without a shared calendar. On-call rotations argue about whose page it is at
2 a.m. This is the tragedy of the commons transplanted into a codebase, and it
is well documented as a consequence of ambiguous ownership in the platform
engineering literature that grew out of Team Topologies
(https://teamtopologies.com/key-concepts, verified 2026-08-02).

The second is orphaned ownership. A service was built by a team that has since
been reorganized, its members moved to other teams or left the company, and no
successor team was ever assigned. The service keeps running because it works,
until it does not, at which point nobody in the organization can explain a
design decision made two years earlier, nobody has the credentials to its
database, and the fix takes a week instead of an hour because someone has to
relearn the service from its source code before touching it.

The context in which Service per Team becomes the right answer, rather than a
bureaucratic overlay, has three conditions. First, the organization has
already split its system into services along some boundary, whether by
business capability, subdomain, or historical accident, so there is a set of
deployable units to assign. Second, the organization is large enough that no
single team can hold the whole system in its head, which is the threshold at
which Conway's Law starts to bite, because below that threshold one team
naturally owns everything and the pattern is vacuous. Third, the organization
is willing to accept the staffing cost of dedicated ownership, because a team
that owns three services well is a smaller team than three teams that each
own a third of nine shared services badly, and the pattern only pays off once
that trade is made deliberately rather than left to drift.

## 3. Forces

- **Coupling.** Favored, at the organizational layer. When a service has one
  owning team, that team's internal coordination cost for changing the
  service drops to whatever the team's own process costs, no cross-team
  negotiation is required for a change confined to the service's boundary.
  This mirrors, and is caused by, the Conway's Law claim that communication
  structure and system structure converge
  (https://www.melconway.com/Home/Committees_Paper.html, verified
  2026-08-02).
- **Team autonomy.** Favored, this is the force Richardson names explicitly as
  a driver of service decomposition and, by extension, of team-based ownership
  (https://microservices.io/patterns/microservices.html, verified
  2026-08-02). A team that owns its service end to end can develop, test, and
  deploy on its own schedule.
- **Accountability.** Favored. When exactly one team can be paged for a
  service, the question of who fixes an incident has one answer. Vogels ties
  this directly to quality, arguing that operational responsibility feeding
  back to the builders improved the software because the cost of a bad
  decision was paid by the people who made it
  (https://queue.acm.org/detail.cfm?id=1142065, verified 2026-08-02).
- **Cross-cutting consistency.** Sacrificed. A cross-cutting change, a new
  authentication library, a compliance requirement, a shared logging format,
  now has to touch every owning team separately instead of being made once in
  a shared module by whoever happened to be editing it. This is the direct
  cost of the coupling reduction above, you cannot have low coordination cost
  for local changes without paying a higher coordination cost for global ones.
- **Staffing elasticity.** Sacrificed. Assigning a dedicated team to a service
  is a headcount commitment. A small or early-stage organization frequently
  does not have enough engineers to give every service its own team without
  either merging services that should stay separate or running teams so thin
  they cannot sustain on-call.
- **Cognitive load per team.** Favored, when team-to-service cardinality
  stays close to one-to-one or one-to-few. Team Topologies frames this
  directly as one of the reasons a stream-aligned team's scope must be
  actively bounded rather than allowed to grow, because a team's cognitive
  capacity is finite and a team that owns too many services degrades on every
  one of them (https://teamtopologies.com/key-concepts, verified 2026-08-02).
- **Latency and runtime performance.** Neutral. This pattern is organizational,
  it does not itself add or remove a network hop, a serialization step, or a
  database round trip. Any latency effect is a side effect of the service
  boundaries the ownership pattern is applied to, not of the ownership
  assignment itself.

## 4. Applicability and non-applicability

Reach for Service per Team when the following hold.

- The system is already decomposed into more than a handful of independently
  deployable services, so there is something concrete to assign.
- The organization is large enough that Conway's Law is already shaping the
  system whether anyone names it or not, and the goal is to shape it on
  purpose instead of by accident.
- Deployment cadence needs to differ across parts of the system. a billing
  service that changes rarely and needs heavy compliance review should not
  share a release train with a recommendations service that ships five times
  a day.
- On-call and incident response need an unambiguous first responder for each
  piece of the system, and the organization is willing to build and staff
  that rotation per team.
- The organization can tolerate, or actively wants, some duplication of
  effort across teams (each team building its own deployment tooling, its own
  test-tooling conventions) in exchange for not blocking on a shared team for
  every change.

Do not reach for Service per Team, and prefer a single team or a platform
team model instead, when the following hold.

- The organization has fewer engineers than the number of services it would
  need to assign, because splitting a five-person team across nine services
  produces nine badly maintained services, not nine well-owned ones. Merge
  services or reduce their count first.
- The system genuinely needs one consistent implementation of a cross-cutting
  concern, a single fraud detection engine, a single pricing calculation,
  where correctness depends on every caller using the identical logic, and
  where letting several teams maintain divergent copies is a compliance or
  correctness risk rather than an acceptable trade-off. Centralize that
  concern in a platform team or a shared library instead of distributing it.
- The organization is small enough, roughly a single team's worth of
  engineers, that team boundaries and service boundaries are the same thing
  by construction, and drawing an internal ownership map adds process without
  changing behavior.
- The services in question are genuinely a shared, foundational platform
  (an internal developer platform, a shared authentication service, a service
  mesh control plane) that every other team consumes as infrastructure.
  Team Topologies calls the team that owns this a **platform team**, a
  distinct team type from stream-aligned teams precisely because its
  customers are internal engineers rather than the business's end users, and
  it is deliberately staffed and evaluated differently
  (https://teamtopologies.com/key-concepts, verified 2026-08-02).
- The organization cannot commit to sustained ownership. no on-call budget,
  no dedicated headcount, a reorg every quarter. Assigning services to teams
  that will not exist in six months produces orphaned ownership faster than
  never assigning them at all, because it creates a false record that
  somebody is responsible.
- The pattern would be applied to a monolith that has not actually been
  decomposed. naming a single team the "owner" of an undivided codebase used
  by every part of the business is not this pattern, it is just naming who
  answers the phone, and it does nothing to reduce coordination cost because
  there are no service boundaries to align teams to.

## 5. Structure

- **Owning team.** A stable group of engineers, typically bounded to the "two
  pizza" size heuristic Fowler and Lewis cite from Amazon practice, roughly a
  dozen people or fewer, small enough to communicate without formal process
  overhead (https://martinfowler.com/articles/microservices.html, verified
  2026-08-02). The owning team holds write access to the service's
  repository, deploy pipeline, and production credentials, and no other team
  holds equivalent access without going through the owning team.
- **Owned service (or service group).** One or a small number of related
  deployable units. The Team Topologies literature treats "how many services
  can one team hold in its head" as a cognitive load question with no fixed
  numeric answer, it depends on the services' complexity, not a headcount
  formula (https://teamtopologies.com/key-concepts, verified 2026-08-02).
- **Consumer teams.** Teams that call the owned service through its published
  interface. A consumer team has no write access to the owning team's
  repository or deploy pipeline. Its relationship to the owning team is
  mediated entirely by the interface contract, which is the X-as-a-Service
  interaction mode in Team Topologies vocabulary.
- **Interface contract.** The API, event schema, or message format the
  service exposes. This is the seam across which the owning team's autonomy
  and the consumer team's stability requirement meet, and it is the one thing
  that must be negotiated jointly rather than owned unilaterally, because
  breaking it breaks every consumer at once.
- **On-call rotation.** The subset of the owning team, often the whole team,
  that carries the pager for the service. This is the structural element that
  turns "owns" from a label on an org chart into an operational fact, per the
  you-build-it-you-run-it framing.
- **Platform team (optional, but common at scale).** A team that owns shared
  infrastructure, CI and CD tooling, observability platforms, that every
  owning team consumes as a service in its own right. The platform team does
  not own application services, it owns the substrate every owning team
  builds on top of.

## 6. ASCII structure diagram

```
                       consumer teams (no write access)
                    +--------+  +--------+  +--------+
                    | Team B |  | Team C |  | Team D |
                    +---+----+  +---+----+  +---+----+
                        |            |            |
                        v            v            v
                  +-----------------------------------+
                  |        Interface Contract          |
                  |   (API / event schema / SLA)       |
                  +-----------------+-------------------+
                                    |
                        +-----------v-----------+
                        |     Team A (owner)     |
                        |  build, test, deploy   |
                        |  on-call, roadmap      |
                        +-----------+-----------+
                                    |
                        +-----------v-----------+
                        |    Owned Service(s)    |
                        |  repo + pipeline +     |
                        |  prod credentials      |
                        +-----------------------+

               +-------------------------------------------+
               |         Platform Team (shared substrate)   |
               |   CI/CD, observability, service mesh, IAM   |
               +---------+---------+----------+--------------+
                         |         |          |
                         v         v          v
                     Team A     Team B     Team C
                  (consumes platform as a service)
```

## 7. Dynamics

Feature change, within a single owning team's boundary.

```
Product/roadmap --> Team A backlog
Team A writes code against Owned Service
Team A runs its own CI pipeline
Team A deploys to production (no cross-team approval gate)
Team A's on-call rotation absorbs any resulting incident
```

Cross-service change, when a consumer team needs new capability.

```
Team B needs new capability from Owned Service
Team B opens a request against the interface contract, not the code
Team A evaluates, schedules the change in its own backlog
Team A implements and deploys the interface change
Team A versions or migrates the contract so Team B's existing
  integration keeps working during the transition
Team B adopts the new interface version on its own schedule
```

Incident dynamics, the operational proof of ownership.

```
Alert fires for Owned Service
Paging system routes to Team A's on-call, not a shared operations desk
Team A engineer, who wrote or maintains the code, diagnoses and fixes
Postmortem is owned and actioned by Team A
```

Reorganization dynamics, the failure mode this pattern must guard against.

```
Org restructures --> Team A is dissolved or reassigned
IF a successor owner is explicitly assigned
    Ownership record updated, on-call rotation transferred, service
    remains inside the pattern
ELSE
    Service becomes orphaned. No team's backlog contains it, no
    on-call rotation covers it, the pattern has silently failed
```

## 8. Implementation variants

- **Strict one service, one team.** The cleanest form. Each deployable unit
  has exactly one owning team, and every owning team owns exactly one
  service. This is easiest to reason about and easiest to staff into an
  on-call rotation, but it does not scale past a certain point, because the
  number of services in a growing system tends to outgrow the number of
  teams the organization can afford to run.
- **One team, several related services.** A team owns a small cluster of
  services that share a bounded context, for example an "orders" team owning
  an order-creation service, an order-history service, and an order-search
  index. This is the more common real-world shape once a system has more
  services than teams, and it is the shape Decompose by Subdomain naturally
  produces, since subdomains frequently need more than one deployable to
  implement fully.
- **Primary owner plus secondary reviewer.** Used when regulatory or
  compliance requirements demand a second set of eyes on changes to a
  sensitive service, a payments or identity service being the common case.
  One team retains sole deploy authority and on-call responsibility, a second
  team or a dedicated reviewer group has read access and a mandatory review
  gate on pull requests, but does not gain write or deploy access. This
  preserves the accountability property of the pattern (one pager, one
  answerable team) while adding a control the pure form lacks.
- **Platform-team-owned shared services.** Certain services are deliberately
  excluded from the per-feature-team assignment and owned instead by a
  platform team whose customers are the other engineering teams rather than
  end users. Team Topologies is explicit that this is a distinct team type
  with a distinct mandate, not a special case of a stream-aligned team
  (https://teamtopologies.com/key-concepts, verified 2026-08-02).
- **Rotating or shared on-call across a service group.** Several small teams
  that each own a handful of related, low-traffic services combine their
  on-call rotations into one shared schedule while keeping code ownership
  and roadmap decisions separate per service. This trades away some of the
  strict single-team accountability of the canonical pattern in exchange for
  a workable pager rotation when no individual team is large enough to
  sustain its own around-the-clock coverage.
- **Ownership registry as infrastructure.** Larger organizations formalize
  the assignment itself as a queryable artifact, a service catalog entry, a
  CODEOWNERS file, an internal developer portal record, rather than tribal
  knowledge. This does not change the pattern's structure, it makes the
  orphaned-ownership failure mode detectable by tooling instead of by
  incident.

## 9. Known production uses

- **Amazon**, described directly by CTO Werner Vogels in his 2006 interview
  with Jim Gray. teams that build a service also run it in production, with
  operational responsibility feeding back into design decisions
  (https://queue.acm.org/detail.cfm?id=1142065, verified 2026-08-02). This is
  the most frequently cited real-world instance of the pattern in the
  industry literature and is the source of the "you build it, you run it"
  name.
- **Monzo**, a UK digital bank, described in its own engineering blog. "These
  teams need to control their own development, deployment, and scale, without
  having to co-ordinate their changes with other teams," written by Oliver
  Beattie, Head of Engineering, "Building a Modern Bank Backend", Monzo
  engineering blog, 19 September 2016
  (https://monzo.com/blog/2016/09/19/building-a-modern-bank-backend, verified
  2026-08-02). Monzo is a useful production example because it is a
  regulated financial institution, showing the pattern is compatible with
  compliance obligations when combined with the primary-owner-plus-reviewer
  variant from dimension 8.
- **SoundCloud**, described by engineer Phil Calcado in a conference
  presentation on managing SoundCloud's microservices migration, summarized
  by InfoQ as addressing operations overhead under a "you build it, you run
  it vision" (https://www.infoq.com/presentations/soundcloud-microservices/,
  verified 2026-08-02). SoundCloud's migration from a Ruby on Rails monolith
  to team-owned services is one of the widely referenced early industry
  case studies of the pattern applied deliberately rather than inherited.

## 10. Consequences

Positive.

- Deployment cadence decouples across the system. one team can ship five
  times a day while another ships weekly, without either blocking on the
  other, because Conway's Law means the release process is now scoped to the
  team rather than to the whole system.
- Accountability for production incidents has one unambiguous answer, which
  shortens the time between an alert firing and the right engineer looking at
  it, because there is no routing negotiation before the fix can begin.
- Ownership creates a natural incentive to invest in maintenance. the team
  that pays the cost of a poorly tested service (their own on-call burden) is
  the same team that decides whether to invest in the test suite, aligning
  incentive with authority in a way shared ownership does not.
- Hiring and onboarding narrow. a new engineer on the owning team needs to
  learn one service's domain deeply rather than a whole system's surface
  area shallowly, which shortens ramp-up time for a specific area of the
  codebase.

Negative.

- Cross-cutting changes multiply in cost. a single security patch that would
  be one pull request in a monolith becomes N pull requests, N reviews, and N
  deploy schedules across N owning teams, and the change is only fully
  applied once every team has actually merged and deployed it.
- Duplication grows. each owning team tends to reinvent its own testing
  conventions, its own deployment scripts, its own error-handling idioms,
  because there is no single place those decisions are made once, unless a
  platform team actively works to centralize them.
- The pattern creates a staffing floor. a service cannot exist below the
  minimum viable team size the organization is willing to sustain for
  on-call, which pressures organizations either to merge services they
  would otherwise want to keep separate, or to understaff ownership and
  accept the orphaning risk from dimension 2.
- Knowledge silos harden along team lines. an engineer on Team B may have no
  practical way to safely change Team A's service even for a trivial fix,
  and is instead forced through the request-and-wait cycle described in
  dimension 7, which can feel slow for genuinely small cross-boundary
  changes.

## 11. Failure modes and misuse

- **Symptom.** A production incident sits unassigned for hours while
  engineers argue in a chat channel about whose service actually caused it.
  **Cause.** Ownership was assigned at the service-boundary level but never
  connected to the paging system, so the alert has no default recipient, or
  two teams both believe the other is on-call. **Fix.** Wire the ownership
  registry (dimension 8) directly into the alerting and paging
  configuration, so a page for a given service resolves to exactly one
  rotation without a human having to look it up during an incident.

- **Symptom.** A service has not had a dependency upgrade, a security patch,
  or a documentation update in over a year, and nobody currently on the
  engineering staff can explain a core design decision in it.
  **Cause.** The team that originally built it was reorganized or dissolved
  and no successor ownership was assigned, the orphaned-ownership failure
  from dimension 2. **Fix.** Treat ownership reassignment as a mandatory,
  tracked step of every reorganization, the same way access revocation is
  mandatory when an employee leaves, rather than an assumption that
  ownership survives a team's dissolution by default.

- **Symptom.** The same business rule, a discount calculation, a fraud
  threshold, exists with subtly different logic in three different services
  owned by three different teams, and nobody can say which one is
  authoritative. **Cause.** A shared concern was distributed to per-team
  ownership when it should have been centralized, the non-applicability case
  from dimension 4 about genuinely cross-cutting logic. **Fix.** Extract the
  shared concern into either a single service owned by one team that the
  others call, or a shared library with a single team as its maintainer, and
  retire the duplicated copies.

- **Symptom.** Every small feature request from a consumer team takes weeks
  to land, even when the actual code change is a few lines, because it has to
  wait in the owning team's backlog behind their own roadmap priorities.
  **Cause.** The interface contract from dimension 5 is too coarse, forcing
  every consumer need through the owning team instead of exposing enough
  configurability or self-service surface for consumers to satisfy small
  needs themselves. **Fix.** Invest in the interface, feature flags,
  configuration APIs, webhook customization, that lets consumer teams solve
  their own small problems without a code change from the owning team, which
  is the same self-service principle Team Topologies applies to platform
  teams (https://teamtopologies.com/key-concepts, verified 2026-08-02).

- **Symptom.** A single team's backlog is dominated by keeping five
  unrelated services alive, and none of the five gets meaningfully better
  over a quarter. **Cause.** Team-to-service cardinality grew past what the
  team's cognitive capacity can sustain, service sprawl outpacing team
  formation, a violation of the cognitive-load force from dimension 3.
  **Fix.** Either grow the number of teams to match the number of services
  that genuinely need independent ownership, or consolidate services that do
  not need to be separate, rather than letting one team silently absorb an
  unsustainable count.

- **Symptom.** A team ships a breaking API change without warning, and every
  consumer team's integration fails simultaneously. **Cause.** The team
  treated its full autonomy over the service's internals as extending to the
  interface contract, which is the one structural element from dimension 5
  that is not unilateral. **Fix.** Require explicit versioning or a
  deprecation window for any interface change, negotiated with known
  consumers, distinct from the team's freedom to change anything behind that
  interface without asking anyone.

## 12. Trade-off matrix

| Force | Service per Team | Shared ownership (no assigned owner) | Fully centralized platform team owns everything |
|---|---|---|---|
| Deploy cadence independence | High, each team ships on its own schedule | Low, deploys require cross-team coordination or a shared release train | Low, all changes route through one team's schedule |
| Incident response clarity | High, one team is paged | Low, incidents stall on "whose service is this" | High, but the responding team may lack domain context |
| Cross-cutting change cost | High, must touch every owning team | Medium, one team can change it but risks breaking others silently | Low, one team can change it once |
| Staffing requirement | High, needs enough teams to cover services | Low, no dedicated team needed per service | Medium, one large team absorbs the whole system |
| Knowledge depth per service | High, the owning team specializes | Low, no team develops deep expertise | Medium, spread across a smaller number of generalist engineers |
| Risk of orphaned ownership | Present, if reorgs are not managed carefully | Present by default, nobody ever owned it | Low, ownership is structurally centralized |
| Consistency of cross-service logic | Low, duplicated per team unless deliberately centralized | Medium, shared by accident since one group touches everything | High, one implementation |

Shared ownership is not a named pattern in the way Service per Team, Layered
Architecture, or a platform-team model are, it is the absence of a pattern,
the default state a system falls into when nobody makes the ownership
decision. It is included in this table because it is the real-world
alternative most systems are actually compared against, not because it is a
deliberate structural choice worth adopting.

## 13. Related and incompatible patterns

- **Decompose by Business Capability** and **Decompose by Subdomain.**
  These two patterns answer where the service boundaries go. Service per
  Team answers who stands behind each boundary once it is drawn. They
  compose directly, in practice a subdomain boundary and a team boundary are
  usually drawn by the same people in the same planning exercise, because
  Conway's Law means a team naturally proposes boundaries it can staff.
- **Backends for Frontends.** A BFF is frequently the clearest instance of
  this pattern applied to a client-facing seam. the team that owns a mobile
  app's experience also owns the BFF service tailored to it, rather than
  sharing a general-purpose API gateway with every other client team.
- **API Gateway.** Composes with this pattern at the boundary. the gateway
  itself is commonly owned by a platform team (dimension 8's platform-team
  variant), while the services behind it are each owned by their respective
  feature teams, which keeps the gateway's cross-cutting concerns
  (authentication, rate limiting) centralized while the business logic stays
  distributed.
- **Saga.** When a business transaction spans several team-owned services,
  the saga pattern is how those services coordinate without any one team
  needing write access to another's data. it is a common companion to
  Service per Team precisely because that ownership boundary rules out a
  shared distributed transaction across services.
- **Strangler Fig.** Frequently used as the migration path into this
  pattern. an existing monolith is incrementally carved into team-owned
  services one capability at a time, with the strangler facade routing
  traffic to the new service once a team has taken ownership of that slice.
- **Layered Architecture, listed as incompatible.** A layered architecture
  organizes code by technical concern, presentation, business logic, data
  access, rather than by business capability. A team assigned "the data
  access layer" does not own a business outcome, it owns a technical slice
  that every feature touches, which reintroduces the cross-team coordination
  cost this pattern exists to remove. Fowler and Lewis name this contrast
  directly as the reason microservice teams organize around capability
  instead of layer (https://martinfowler.com/articles/microservices.html,
  verified 2026-08-02). This is why the two patterns are marked incompatible
  in the frontmatter rather than merely different, applying Service per Team
  on top of a layered decomposition does not work, because there is no
  business-aligned boundary for a team to own in the first place.

## 14. Refactoring path in and out

Introducing Service per Team into a system that currently has shared or
orphaned ownership.

1. Inventory every deployable service and record, honestly, who currently
   has write and deploy access to it, and who is actually paged when it
   fails. This step alone frequently surfaces services with either no
   accountable team or several teams with overlapping, undocumented access.
2. For each service, assign exactly one team as the owner, favoring the team
   that already has the most domain knowledge of it rather than starting
   from a blank org chart. If Decompose by Business Capability or Decompose
   by Subdomain has already been applied, the subdomain owner is usually the
   natural service owner.
3. Restrict deploy and production access to the assigned owning team. this
   is the step organizations most often skip, leaving the ownership
   assignment as a document that access controls do not enforce, which lets
   the shared-ownership failure mode creep back in.
4. Stand up or transfer the on-call rotation to the owning team, and update
   the paging configuration so an alert for the service routes to that
   rotation by default, closing the incident-routing gap from dimension 11.
5. Publish the interface contract for the service and communicate it to
   consumer teams, so they stop depending on internal implementation details
   and start depending on the boundary the owning team is willing to
   support.
6. Record the assignment in a queryable form, a service catalog, a
   CODEOWNERS file, so the next reorganization has something to update
   rather than something to rediscover.

Removing Service per Team, when a service's ownership needs to consolidate
back into a shared or platform-owned model.

1. Identify the reason ownership needs to change. commonly, the owning team
   is being dissolved, the service has become genuinely cross-cutting
   infrastructure rather than a single team's business capability, or the
   organization has shrunk below the size that can sustain per-team
   ownership.
2. Reclassify the service explicitly rather than letting it drift into
   orphaned status. either assign it to a platform team under the
   platform-team variant from dimension 8, or merge it into a sibling
   service already owned by a team that can absorb the added scope.
3. Transfer, do not simply revoke, deploy access, on-call responsibility, and
   documentation to the new owner in a single coordinated handoff, so there
   is no window during which the service has no accountable rotation.
4. Update the service catalog and any CODEOWNERS-style record at the same
   time as the access transfer, so the record and the reality do not drift
   apart, which is exactly the failure this pattern's introduction was meant
   to prevent in the first place.

## 15. Testing and verification

This pattern is largely judgement, since it concerns process rather than
code, and the specific tests below are drawn from platform-engineering
practice rather than from a single cited source.

What this pattern makes easier to test.

- **Contract testing at the ownership boundary.** Because a consumer team
  has no write access to the owning team's internals, the only thing worth
  testing across the boundary is the published interface, which makes
  consumer-driven contract testing (a consumer team publishes the exact
  interactions it depends on, the owning team's pipeline verifies its
  service still satisfies them before deploy) a natural fit, since the
  contract is already the sole point of coupling by construction.
- **Ownership-boundary test isolation.** An owning team's own test suite can
  freely mock or stub every service it does not own, since it never touches
  those internals anyway, which keeps its test suite fast and focused on the
  logic it is actually accountable for.

What becomes harder to verify.

- **End-to-end business flows spanning several owning teams.** No single
  team's test suite can exercise a flow that crosses ownership boundaries,
  which pushes end-to-end verification into a separate, slower, and more
  fragile layer, staging environments, synthetic monitoring, or a dedicated
  cross-team integration suite that someone has to own and maintain.
- **Ownership itself.** The organizational claim, that a given team truly
  owns a given service, has no automated test. It is verified by process,
  the ownership registry from dimension 14 step 6, the paging rotation
  actually resolving correctly during a real incident, and periodic audits
  that catch drift between the recorded owner and the team that would
  actually respond.

What to verify explicitly during and after adoption.

- Fire a test page for each service and confirm it reaches the recorded
  owning team's rotation, not a stale rotation left over from before the
  assignment. This is the single most concrete verification available for
  this pattern, because it tests the accountability claim directly rather
  than inferring it from documentation.
- Audit deploy access for every service against the ownership registry on a
  fixed schedule, catching the case where access was granted for a one-off
  fix and never revoked, which quietly reintroduces shared ownership.

## 16. Observability signals

This dimension is drawn from operational practice rather than a single
cited authority and should be read as judgement.

A healthy instance of this pattern shows the following.

- A service catalog or CODEOWNERS-equivalent record with a non-empty,
  current owner for every service, and that record matching the team whose
  members actually appear in the recent deploy and commit history for that
  service.
- Page acknowledgment times for each service consistent with a team that
  knows the code, rather than a long delay followed by an escalation to a
  different team once the first responder realizes they do not actually own
  it.
- Deploy frequency per service correlated with that service's own team
  velocity, not gated on an unrelated team's release calendar.
- A low rate of "who owns this" questions in incident postmortems. a rising
  rate of that specific question, tracked over time, is one of the more
  reliable leading indicators that ownership is drifting toward the
  orphaned-ownership failure mode from dimension 11.

An unhealthy instance shows the following.

- Services with no commits or deploys in a long window, combined with an
  ownership record that lists a team that no longer exists in the current
  org chart, the direct observable signature of orphaning.
- Deploy or database access logs showing engineers from more than one team
  regularly writing to the same service, the observable signature of shared
  ownership reasserting itself even where the documentation claims a single
  owner.
- Incident postmortems that repeatedly note delayed triage due to
  ambiguous escalation paths, the direct symptom described in dimension 11's
  first failure mode.

## 17. Security and privacy implications

Service per Team has a genuine, if narrow, security surface, because it
directly determines who holds production credentials and write access.

- **Reduced blast radius per credential.** Because deploy and production
  access is scoped to the owning team rather than granted broadly, a
  compromised credential belonging to one engineer exposes at most the
  services their team owns, not the whole system. This is a natural
  consequence of the access restriction in dimension 14's refactoring path,
  not an incidental benefit, the pattern's structure is what makes least
  privilege enforceable at the service level.
- **Access review becomes tractable.** Reviewing "who can deploy this
  service" reduces to reviewing one team's membership rather than auditing a
  sprawling, undocumented set of individuals who happen to have accumulated
  access over time. This makes periodic access reviews, a common compliance
  requirement, materially cheaper to perform correctly.
- **Data ownership follows service ownership.** If a service holds
  personally identifiable or otherwise regulated data, per-team ownership
  creates a clear, single point of accountability for that data's handling,
  which data protection regimes generally expect. an unassigned or shared
  service makes it harder to answer, quickly and confidently, who is
  responsible for a given dataset when a regulator or an auditor asks.
- **The orphaning failure mode is itself a security risk, not only an
  operational one.** A service nobody actively maintains is a service whose
  dependencies quietly go unpatched, because patching requires someone with
  both the access and the incentive to do it, and orphaned services have
  neither. The Monzo and SoundCloud production examples in dimension 9 both
  operate in contexts, consumer banking and a platform handling user data
  respectively, where an unpatched, unowned service is a concrete regulatory
  and privacy exposure, not merely a maintenance inconvenience.
- **The interface contract is the security boundary consumers should trust,
  not the internals.** Because a consumer team cannot see or touch the
  internals of a service it does not own, that consumer has no way to verify
  the owning team's internal security practices directly. Organizations that
  adopt this pattern at scale typically compensate with centralized security
  scanning and policy enforcement run by a platform team across every
  service, rather than trusting each owning team to independently reach the
  same security bar.

## 18. References

1. Melvin E. Conway, "How Do Committees Invent", *Datamation*, April 1968.
   https://www.melconway.com/Home/Committees_Paper.html, verified 2026-08-02.
2. Jim Gray (interviewer), "A Conversation with Werner Vogels", *ACM Queue*,
   volume 4, number 4, 30 June 2006.
   https://queue.acm.org/detail.cfm?id=1142065, verified 2026-08-02.
3. Chris Richardson, "Pattern. Microservice Architecture", microservices.io.
   https://microservices.io/patterns/microservices.html, verified 2026-08-02.
4. Chris Richardson, *Microservices Patterns. With Examples in Java*,
   Manning, 2018.
5. Matthew Skelton and Manuel Pais, *Team Topologies. Organizing Business and
   Technology Teams for Fast Flow*, IT Revolution Press, 2019. Key concepts
   summarized at https://teamtopologies.com/key-concepts, verified
   2026-08-02.
6. Martin Fowler and James Lewis, "Microservices", martinfowler.com, 25 March
   2014. https://martinfowler.com/articles/microservices.html, verified
   2026-08-02.
7. Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*, Addison-Wesley, 2003. Supplies the bounded context concept that
   both the subdomain-decomposition and team-ownership lines of practice
   depend on, cited by Fowler and Lewis as the conceptual grounding for
   organizing around business capability.
8. Oliver Beattie, "Building a Modern Bank Backend", Monzo engineering blog,
   19 September 2016.
   https://monzo.com/blog/2016/09/19/building-a-modern-bank-backend, verified
   2026-08-02.
9. Phil Calcado, presentation on SoundCloud's microservices practice,
   summarized by InfoQ.
   https://www.infoq.com/presentations/soundcloud-microservices/, verified
   2026-08-02.

## Code examples

The pattern itself is organizational and has no runtime behavior, so the
code below models the one artifact from the pattern that does have a useful
runtime shape, an ownership registry that a paging system or a deploy
pipeline could actually query to answer "who owns this service" and "is this
assignment still valid" without a human looking it up during an incident.

### TypeScript

```typescript
interface ServiceOwnership {
  serviceName: string;
  owningTeam: string;
  onCallRotationId: string;
  lastVerified: Date;
}

class OwnershipRegistry {
  private records = new Map<string, ServiceOwnership>();

  assign(record: ServiceOwnership): void {
    if (!record.owningTeam || !record.onCallRotationId) {
      throw new Error(
        `service ${record.serviceName} cannot be assigned without a team and a rotation`
      );
    }
    this.records.set(record.serviceName, record);
  }

  ownerOf(serviceName: string): ServiceOwnership | undefined {
    return this.records.get(serviceName);
  }

  isOrphaned(serviceName: string, staleAfterDays: number): boolean {
    const record = this.records.get(serviceName);
    if (!record) {
      return true;
    }
    const ageMs = Date.now() - record.lastVerified.getTime();
    return ageMs > staleAfterDays * 24 * 60 * 60 * 1000;
  }
}

const registry = new OwnershipRegistry();
registry.assign({
  serviceName: "order-service",
  owningTeam: "orders-team",
  onCallRotationId: "orders-oncall",
  lastVerified: new Date(),
});

const owner = registry.ownerOf("order-service");
console.log(owner ? `${owner.serviceName} owned by ${owner.owningTeam}` : "unowned");
console.log(registry.isOrphaned("order-service", 90));
```

### Python

```python
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class ServiceOwnership:
    service_name: str
    owning_team: str
    on_call_rotation_id: str
    last_verified: datetime


class OwnershipRegistry:
    def __init__(self) -> None:
        self._records: dict[str, ServiceOwnership] = {}

    def assign(self, record: ServiceOwnership) -> None:
        if not record.owning_team or not record.on_call_rotation_id:
            raise ValueError(
                f"service {record.service_name} cannot be assigned "
                "without a team and a rotation"
            )
        self._records[record.service_name] = record

    def owner_of(self, service_name: str) -> ServiceOwnership | None:
        return self._records.get(service_name)

    def is_orphaned(self, service_name: str, stale_after_days: int) -> bool:
        record = self._records.get(service_name)
        if record is None:
            return True
        age = datetime.now() - record.last_verified
        return age > timedelta(days=stale_after_days)


registry = OwnershipRegistry()
registry.assign(
    ServiceOwnership(
        service_name="order-service",
        owning_team="orders-team",
        on_call_rotation_id="orders-oncall",
        last_verified=datetime.now(),
    )
)

owner = registry.owner_of("order-service")
if owner:
    print(f"{owner.service_name} owned by {owner.owning_team}")
else:
    print("unowned")

print(registry.is_orphaned("order-service", 90))
```

### Go

```go
package main

import (
	"errors"
	"fmt"
	"time"
)

type ServiceOwnership struct {
	ServiceName      string
	OwningTeam       string
	OnCallRotationID string
	LastVerified     time.Time
}

type OwnershipRegistry struct {
	records map[string]ServiceOwnership
}

func NewOwnershipRegistry() *OwnershipRegistry {
	return &OwnershipRegistry{records: make(map[string]ServiceOwnership)}
}

func (r *OwnershipRegistry) Assign(record ServiceOwnership) error {
	if record.OwningTeam == "" || record.OnCallRotationID == "" {
		return errors.New("service cannot be assigned without a team and a rotation")
	}
	r.records[record.ServiceName] = record
	return nil
}

func (r *OwnershipRegistry) OwnerOf(serviceName string) (ServiceOwnership, bool) {
	record, ok := r.records[serviceName]
	return record, ok
}

func (r *OwnershipRegistry) IsOrphaned(serviceName string, staleAfter time.Duration) bool {
	record, ok := r.records[serviceName]
	if !ok {
		return true
	}
	return time.Since(record.LastVerified) > staleAfter
}

func main() {
	registry := NewOwnershipRegistry()
	err := registry.Assign(ServiceOwnership{
		ServiceName:      "order-service",
		OwningTeam:       "orders-team",
		OnCallRotationID: "orders-oncall",
		LastVerified:     time.Now(),
	})
	if err != nil {
		fmt.Println(err)
		return
	}

	owner, found := registry.OwnerOf("order-service")
	if found {
		fmt.Printf("%s owned by %s\n", owner.ServiceName, owner.OwningTeam)
	} else {
		fmt.Println("unowned")
	}

	fmt.Println(registry.IsOrphaned("order-service", 90*24*time.Hour))
}
```

### Swift

```swift
import Foundation

struct ServiceOwnership {
    let serviceName: String
    let owningTeam: String
    let onCallRotationId: String
    let lastVerified: Date
}

enum OwnershipError: Error {
    case incompleteAssignment(String)
}

final class OwnershipRegistry {
    private var records: [String: ServiceOwnership] = [:]

    func assign(_ record: ServiceOwnership) throws {
        guard !record.owningTeam.isEmpty, !record.onCallRotationId.isEmpty else {
            throw OwnershipError.incompleteAssignment(record.serviceName)
        }
        records[record.serviceName] = record
    }

    func owner(of serviceName: String) -> ServiceOwnership? {
        records[serviceName]
    }

    func isOrphaned(_ serviceName: String, staleAfterDays: Int) -> Bool {
        guard let record = records[serviceName] else { return true }
        let staleSeconds = TimeInterval(staleAfterDays * 24 * 60 * 60)
        return Date().timeIntervalSince(record.lastVerified) > staleSeconds
    }
}

let registry = OwnershipRegistry()
try registry.assign(
    ServiceOwnership(
        serviceName: "order-service",
        owningTeam: "orders-team",
        onCallRotationId: "orders-oncall",
        lastVerified: Date()
    )
)

if let owner = registry.owner(of: "order-service") {
    print("\(owner.serviceName) owned by \(owner.owningTeam)")
} else {
    print("unowned")
}

print(registry.isOrphaned("order-service", staleAfterDays: 90))
```

Java, Rust, C#, and Kotlin are omitted from this entry. The ownership
registry above is the only artifact worth showing in code, and four language
renderings of the identical map-with-a-staleness-check already demonstrate
every idea the sample carries. A fifth or sixth rendering in another language
would repeat the same three methods without adding anything the reader has
not already seen, which is exactly the kind of padding this repository's
authoring standard exists to avoid.
