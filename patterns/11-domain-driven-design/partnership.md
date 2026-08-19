---
name: Partnership
slug: partnership
family: 11-domain-driven-design
category: Strategic Design
aliases: [Partnership Context Map Relationship, Peer Team Alliance]
first_described: "Evans 2003"
maturity: canonical
related: [shared-kernel, customer-supplier, conformist, bounded-context, context-map, separate-ways, open-host-service-and-published-language]
incompatible_with: [customer-supplier, conformist]
verified: 2026-08-02
---

## 1. Name, aliases, and lineage

The canonical name is Partnership. Eric Evans introduced it in "Domain-Driven
Design. Tackling Complexity in the Heart of Software" (Addison-Wesley, 2003),
Part IV, Chapter 14, "Maintaining Model Integrity," inside the same catalog of
named team relationships that also holds Shared Kernel, Customer-Supplier
Development Teams, Conformist, Anticorruption Layer, Separate Ways, Open Host
Service, and Published Language. Evans states the pattern in one paragraph
that is easy to underweight against its neighbours because it carries no code
sample, only an organizational commitment, when two teams have interdependent
goals, put them in a Partnership, establish a process for coordinated planning
and joint management of their integration, and run continuous integration
across both team's code so a break surfaces on the day it happens, not weeks
later. Evans's 2015 self-published summary, "Domain-Driven Design Reference.
Definitions and Pattern Summaries" (Domain Language, Inc.), restates the same
nine strategic patterns with the same one-line definitions and keeps
Partnership in the list unchanged from the 2003 text.

Vaughn Vernon's "Implementing Domain-Driven Design" (Addison-Wesley, 2013),
Chapter 3, "Context Maps," is the source most practitioners actually learn the
pattern from today, because Vernon draws the context map diagrams that Evans's
prose only describes. Vernon lists Partnership among the eight named Context
Map relationships and adds the detail that most teams find load-bearing in
practice, a Partnership is symmetric and ad hoc. Neither side is upstream or
downstream of the other in the way Customer-Supplier names one side upstream,
and the coordination mechanism is not a fixed API contract but a standing
habit of talking to each other and reacting together when either side's model
needs to move. Vernon also names the two-way street property explicitly, both
teams win together or both teams lose together, which is the line most often
quoted back to justify choosing Partnership over Customer-Supplier when
neither team can plausibly claim upstream authority over the other.

The name collides in ordinary English with two unrelated things a reader
should not confuse it with. A business partnership, a legal or commercial
arrangement between companies, is not this pattern, though a genuine Evans
Partnership sometimes forms between two companies collaborating on an
integration and the words happen to coincide. A "pair" or "buddy" system
between two individual engineers is also not this pattern. Partnership in the
Context Map sense is a relationship between two teams, each of whom owns a
Bounded Context, never between two people or two companies as legal entities.
No alternate or superseding name for the pattern has entered common use since
2003. Practitioners occasionally shorten it in conversation to "a partnership
relationship" or "peer teams," but the DDD community, including Vernon's 2013
text and Nick Tune and Scott Millett's "Patterns, Principles, and Practices of
Domain-Driven Design" (Wrox, 2015), Chapter 13, "Managing Big Balls of Mud,"
use Evans's original term without modification.

## 2. Problem and context

Two teams each own a Bounded Context, and the two Contexts must integrate, but
neither team can honestly claim to be upstream of the other. The situation
that produces this need has a recognisable shape in a real organization. Team
A is building an order-fulfilment service. Team B is building a warehouse
inventory service. Neither service can ship a coherent feature without the
other, an order cannot be confirmed without a stock check, a stock adjustment
cannot be attributed without an order reference, and the plans of one team
routinely force a change in the other team's model. Nobody outranks anybody.
Neither team has the standing, the headcount, or the organizational mandate to
dictate a contract the other team simply implements.

This is the exact situation where Customer-Supplier fails as a description of
reality even when a chart on the wall shows an arrow between the two boxes.
Customer-Supplier presumes an upstream team that can prioritise or decline a
downstream team's requests inside its own backlog, with the downstream team
accepting the upstream team's schedule. When the two teams instead need to
plan a joint release, negotiate a shared timeline, and treat a break in either
direction as a shared incident, the relationship is symmetric rather than
directional, and Evans's name for the symmetric case is Partnership.

The context that makes Partnership the honest choice, rather than a euphemism
avoiding a harder conversation about who is really upstream, has three parts.
First, both teams' plans depend on the same integration succeeding in the
same release window, so a delay on either side blocks the other. Second,
neither team has organizational authority to impose its model on the other,
whether because they report to different business units, different budget
owners, or simply because the org chart gives neither side veto power. Third,
the two teams are willing, and have been given the standing and the calendar
time, to run ad hoc coordinated planning together rather than communicating
through a formal ticket queue or a published contract that changes on a fixed
release cadence. Partnership costs real synchronous coordination time. It is
the DDD pattern for two teams who must succeed or fail together and who have
been organizationally set up to actually talk to each other about it.

## 3. Forces

The pattern balances the following competing pressures.

- **Autonomy versus alignment.** Sacrificed on autonomy, favoured on
  alignment. Each team keeps its own model and its own Ubiquitous Language
  inside its own Context, but neither team can change its integration-facing
  surface unilaterally, because doing so breaks the other side without
  warning.
- **Coordination cost.** Sacrificed, and this is the pattern's largest cost.
  Partnership requires standing joint planning, whether a weekly sync, a
  shared backlog for the integration surface, or a shared Slack channel that
  both team leads actually watch. This cost recurs every sprint for the life
  of the integration, not once at design time.
- **Failure containment.** Favoured relative to Separate Ways, sacrificed
  relative to a formal Anticorruption Layer. A break on either side is
  detected quickly because continuous integration runs across both team's
  code, but a break still requires both teams to jointly diagnose and fix it,
  since neither side owns a translation layer that could absorb the change
  alone.
- **Speed of change.** Sacrificed for either team acting alone, favoured for
  the pair acting together. Neither team can ship a breaking model change on
  its own schedule. Both teams can, if they coordinate, ship a joint change
  faster than a formal contract negotiation between an upstream and a
  downstream team would allow, because there is no approval gate, only a
  conversation.
- **Political cost.** This is the force Evans and Vernon leave implicit and
  the one that most often kills a Partnership in practice. The relationship
  presumes both teams have equal standing to say no to each other's proposed
  changes. When one team is politically stronger, has a louder manager, or
  answers to a more senior stakeholder, the nominal Partnership degrades into
  an unacknowledged Customer-Supplier where the weaker team absorbs breakage
  without the formal escalation path that a real Customer-Supplier
  relationship grants it. Alberto Brandolini's "Introducing EventStorming"
  (self-published, Leanpub, 2021), Chapter 8, describes exactly this failure
  as one motivation for running a joint Big Picture EventStorming session
  before declaring a Partnership, so the power imbalance is visible before it
  becomes an unspoken one.
- **Testability of the boundary.** Favoured, conditionally. Because both
  teams commit to continuous integration across the shared surface, a
  contract test suite that both sides own jointly becomes a natural artifact
  of the pattern, whereas Separate Ways has no such surface to test and
  Customer-Supplier tends to leave contract testing entirely to the
  downstream side.

## 4. Applicability and non-applicability

Reach for Partnership when the following hold.

- Two teams each own a genuine Bounded Context with its own model, and the two
  Contexts must integrate for either team's plans to ship.
- Neither team has organizational authority to dictate terms to the other, and
  no third party above both teams is willing to arbitrate a fixed contract.
- The two teams' release schedules are already coupled in practice, a change
  on one side routinely forces a change on the other within the same sprint
  or release, so pretending otherwise via a formal contract would only hide
  the coupling rather than remove it.
- Both team leads, or the organizational structure above them, are willing to
  commit calendar time to standing joint planning and to run continuous
  integration across both codebases so integration breaks surface
  immediately.
- The integration surface between the two Contexts is small and evolving
  rather than large and stable. A small, actively co-designed surface is
  where the coordination overhead of Partnership pays for itself; a large
  stable surface is better served by a published contract.

Do NOT reach for Partnership in these cases, and the reason matters more than
the rule.

- **One team is, in fact, upstream.** If Team A's model genuinely predates
  Team B's need for it, and Team A has the standing to say no to Team B's
  change requests without escalating, the relationship is Customer-Supplier,
  not Partnership. Declaring a Partnership here launders a real power
  imbalance into a symmetric-sounding label, and Team B ends up doing
  unplanned rework whenever Team A ships without warning, exactly the failure
  Customer-Supplier's formal backlog exists to prevent.
- **The two teams do not, or cannot, sit in the same coordination cadence.**
  Partnership presumes joint planning actually happens. Two teams in
  different time zones, different business units with no shared standup,
  or a team inside the org and a team at an external vendor, rarely sustain
  the ad hoc synchronous coordination the pattern needs. Open Host Service
  with a Published Language, which needs no synchronous coordination at all,
  is the honest fit for that situation.
- **The two teams could simply not integrate.** If the two Contexts' overlap
  is small enough that duplicating the shared logic costs less than the
  standing coordination tax, Separate Ways is cheaper and should be
  considered first. Partnership is never free even when it succeeds.
- **The organization wants a stable, versioned contract rather than an
  evolving one.** Shared Kernel and Open Host Service both give a fixed,
  independently versioned artifact that either side can consume without
  synchronous negotiation. A team that actually wants "we agree on this
  interface and then leave each other alone" is describing Shared Kernel or
  Open Host Service, not Partnership, and will find the standing meeting
  cadence of a real Partnership to be pure overhead.
- **One side is a third-party vendor or an external open-source project.**
  Partnership presumes both teams can jointly re-plan on short notice. An
  external dependency that ships on its own release cycle and does not take
  your team's plans into account is Conformist territory, or
  Anticorruption Layer if you need to protect your model from theirs.
- **The relationship is being declared to avoid an honest conversation about
  authority.** If leadership has not actually granted both teams equal
  standing to veto each other's changes, calling the relationship a
  Partnership without addressing that gap produces the political failure
  mode described in dimension 3, not the pattern's benefit.

## 5. Structure

Two participants, symmetric by definition, which is what distinguishes this
pattern's structure from every other Context Map relationship in the Evans
catalog, all of which name an upstream and a downstream side.

- **Partner Context A.** A Bounded Context owned by one team, with its own
  model and its own Ubiquitous Language. It exposes, and consumes, an
  integration surface shared with Partner Context B. Neither role, upstream
  nor downstream, applies to it; the relationship arrow on a Context Map is
  drawn without a head on either end, or with heads on both ends, to signal
  the symmetry.
- **Partner Context B.** The peer of Partner Context A, structurally
  identical in role. Each side is simultaneously a producer of change
  requests toward the other and a consumer of the other's change requests.
- **The Joint Coordination Process.** Not a code artifact but a real,
  observable organizational mechanism, standing meetings, a shared backlog
  or Kanban board for the integration surface, or a shared communication
  channel that both team leads monitor. Evans treats this as a first-class
  part of the pattern's structure rather than an implementation detail,
  because without it the two Contexts are merely coupled, not partnered.
- **Continuous Integration Across Both Contexts.** A shared CI pipeline, or
  two pipelines that both run against the current state of the other side's
  integration surface, so a break is detected on the commit that caused it.
  Vernon (2013), Chapter 3, names this explicitly as the mechanism that
  makes Partnership operationally different from an informal "we talk
  sometimes" arrangement between two teams.

There is no code-level artifact unique to Partnership itself; the pattern
governs how two Contexts' integration surfaces are jointly evolved, and the
actual data exchanged between the two sides is typically expressed through
whichever integration mechanism the two teams jointly choose, a shared event
schema, a small internal API, or a message contract that both sides commit to
modifying only together.

## 6. ASCII structure diagram

```
        +-------------------------+          +-------------------------+
        |   Bounded Context A     |          |   Bounded Context B     |
        |   (Team A's model,      |          |   (Team B's model,      |
        |    Ubiquitous Language) |          |    Ubiquitous Language) |
        +-------------------------+          +-------------------------+
                    |                                     |
                    |     integration surface, jointly     |
                    |         designed and evolved         |
                    +<----------------------------------->+
                    |         (no upstream, no             |
                    |          downstream, symmetric)       |
                    v                                     v
        +-------------------------+          +-------------------------+
        |  Joint coordination:    |          |  Joint coordination:    |
        |  shared planning cadence|<-------->|  shared planning cadence|
        |  shared backlog for the |          |  shared backlog for the |
        |  integration surface    |          |  integration surface    |
        +-------------------------+          +-------------------------+
                    |                                     |
                    v                                     v
        +--------------------------------------------------------+
        |         Continuous integration across both              |
        |         Contexts. A change on either side is             |
        |         built and tested against the other side's       |
        |         current integration surface on commit.          |
        +--------------------------------------------------------+

  Both arrows carry weight in both directions. Team A can force a
  renegotiation of the shared surface exactly as easily as Team B can.
```

## 7. Dynamics

The runtime and process flow both matter here, because Partnership is as much
a process pattern as a code pattern. Two flows are worth drawing, a routine
day, and the day one side needs to change the shared surface.

```
Routine day, both teams shipping independent internal work

Team A                          Shared CI                       Team B
  |                                  |                              |
  |-- commits internal change ----->|                              |
  |                                  |-- runs A's tests -------->  |
  |                                  |-- runs joint contract tests |
  |                                  |     against B's current     |
  |                                  |     integration surface --->|
  |                                  |<-- pass ---------------------|
  |<-- CI green ---------------------|                              |
  |                                  |                              |
  |                                  |<-- B commits internal change |
  |                                  |-- runs B's tests             |
  |                                  |-- runs joint contract tests  |
  |                                  |     against A's current      |
  |                                  |     integration surface      |
  |                                  |-- CI green ----------------->|
```

```
Day one side needs to change the shared integration surface

Team A                     Joint coordination            Team B
  |                              |                            |
  |-- proposes surface change -->|                            |
  |                              |-- forwards proposal ------->|
  |                              |                            |
  |                              |<-- B reviews impact --------|
  |                              |<-- B proposes counter-terms |
  |                              |    (both sides negotiate    |
  |                              |     as peers, no veto       |
  |                              |     asymmetry)              |
  |<-- agreed joint plan --------|-- agreed joint plan ------->|
  |                              |                            |
  |-- implements A's half ------>|                            |
  |                              |<-- implements B's half -----|
  |                              |                            |
  |-- joint CI run across both changes together -------------->|
  |<------------------------------------------------------------|
```

The property to notice in the second diagram is that the negotiation happens
before either side writes code against the new surface, and the two halves of
the change land together, verified by the shared CI run, rather than one side
shipping a breaking change and the other side discovering it after the fact.
That joint landing is what separates a functioning Partnership from two teams
who merely happen to talk to each other occasionally.

## 8. Implementation variants

**Shared contract test suite, owned jointly.** Both teams write and maintain
one test suite that exercises the integration surface, versioned in a
repository, or a shared folder inside a monorepo, that both teams can commit
to. This is the most common concrete realisation of "continuous integration
across both Contexts" in Vernon's description, and it gives the pattern a
tangible artifact a reader can point to on a Context Map audit.

**Shared event schema with joint change process.** The two Contexts
communicate over an event bus, and the event schema itself, rather than a
request-response API, is the negotiated surface. Neither side owns the schema
registry unilaterally; changes to the schema go through the joint
coordination process described in dimension 5. This variant is common between
two microservices that integrate asynchronously, where the schema evolves
alongside a shared consumer-driven contract test, see the Consumer-Driven
Contract entry in the integration-patterns family.

**Cross-team pairing on the integration surface specifically.** Rather than a
shared artifact, the two teams rotate an engineer from each side onto joint
work sessions whenever the surface changes, keeping the coordination
lightweight and informal for a small integration that changes rarely. This
variant trades a durable process artifact for lower ceremony, and works only
when the integration surface truly is small, per dimension 4's applicability
condition.

**Monorepo colocated Partnership.** When both teams' code lives in one
repository, the "shared CI" half of the pattern is close to free, since a
single pipeline already runs on every commit. What still has to be built
deliberately is the joint coordination process, because colocated code does
not by itself produce joint planning; teams inside the same monorepo can and
do still ship breaking changes on each other without warning if no
coordination habit exists.

**Federated GraphQL schema as the negotiated surface.** Two teams each own a
subgraph, and the composed supergraph schema is the jointly negotiated
integration surface, changed only through a review process both teams
participate in. Apollo's federation documentation describes exactly this
joint-ownership model for subgraph schema changes, see dimension 9.

**Language and platform note.** Partnership has no language-specific
translation, because it is a team and process pattern rather than a code
structure. What varies by platform is the shape of the shared artifact, a
Protobuf `.proto` file under joint change control, a shared OpenAPI spec, or
a shared TypeScript types package published from a monorepo, but the pattern
itself sits above any single language's constructs.

## 9. Known production uses

**Netflix's cross-team API evolution via consumer-driven contracts.**
Netflix's engineering blog describes teams that own upstream and downstream
services jointly evolving shared contracts through Pact-based
consumer-driven contract testing, run in CI on every commit from either side,
explicitly framed as a way for teams with interdependent release schedules to
avoid a formal gatekeeping relationship between them. Netflix Technology
Blog, "Practical API Design at Netflix, Part 1. Using Protobuf FieldMask,"
https://netflixtechblog.com/practical-api-design-at-netflix-part-1-using-protobuf-fieldmask-35cfdc606518
verified 2026-08-02, describes the joint, negotiated nature of the Netflix
internal API surface between interdependent teams as a standing collaborative
process rather than a one-directional handoff.

**Pact.io consumer-driven contract testing across peer teams.** The Pact
project's own documentation describes its intended use explicitly for teams
that need to evolve an API together without either side unilaterally
dictating the contract, with both the provider team and the consumer team
running the shared Pact test suite in their respective CI pipelines and
publishing results to a shared Pact Broker so either side sees a break
immediately. Pact documentation, "What is Contract Testing,"
https://docs.pact.io/ verified 2026-08-02,
describes the shared, jointly-verified contract as the mechanism that keeps
two independently deployed services in sync without a formal upstream
authority.

**Apollo GraphQL Federation, joint subgraph schema ownership.** Apollo's
Federation architecture is built explicitly for the case where multiple
teams each own a piece of a company's graph and must compose a single
supergraph together, with schema composition checks run in CI against every
subgraph's proposed change so a breaking change is caught before it reaches
the shared graph. Apollo GraphQL documentation, "Federation overview," and
the composition check tooling described at
https://www.apollographql.com/docs/graphos/reference/federation/errors and
https://www.apollographql.com/docs/graphos/platform/schema-management/checks
verified 2026-08-02, document the joint, continuously-verified nature of
subgraph schema evolution across teams with no single team acting as
gatekeeper over the others.

**Spotify's squad-to-squad integration model.** Spotify's widely cited
engineering culture materials describe squads that own adjacent services
coordinating directly with each other on shared interfaces rather than
routing all cross-team integration through a central platform team, with the
explicit framing that squads with tightly coupled plans hold standing
joint syncs to manage their integration points together. Henrik Kniberg and
Anders Ivarsson, "Scaling Agile @ Spotify with Tribes, Squads, Chapters and
Guilds" (Spotify Engineering Culture whitepaper, 2012),
https://blog.crisp.se/wp-content/uploads/2012/11/SpotifyScaling.pdf verified
2026-08-02, describes squads coordinating on shared interfaces as peers
rather than through a formal upstream-downstream chain, which is the
organizational shape Partnership names.

## 10. Consequences

Positive.

- Neither team is forced into a fictional upstream-downstream posture that
  does not match the real organizational authority between them, which
  avoids the resentment and workaround behaviour that follows from a falsely
  imposed Customer-Supplier relationship.
- Breaking changes are caught immediately by shared continuous integration
  rather than discovered in a later integration test phase or in production.
- Both teams retain full autonomy over their own internal model; only the
  jointly negotiated integration surface is constrained.
- The pattern makes an already-existing tight coupling between two teams'
  plans organizationally visible and explicit, on the Context Map, rather
  than leaving it as an informal, undocumented dependency that surprises
  planning meetings.
- A jointly-owned contract test suite becomes a durable, checkable artifact
  that documents the integration surface far more reliably than a design
  document that goes stale.

Negative.

- The standing coordination cost is real and recurring, not a one-time
  design-phase expense, and it does not shrink as the relationship matures;
  it persists for the life of the integration.
- The pattern has no formal escalation mechanism when the two teams disagree,
  unlike Customer-Supplier's backlog-and-priority process. A genuine
  deadlock between two Partnership teams has no built-in resolution path and
  must be escalated outside the pattern entirely, typically to a shared
  manager.
- It is fragile to organizational power imbalance. The moment one team can
  effectively ignore the other's objections, the Partnership degrades into
  an unacknowledged, unmanaged Customer-Supplier relationship, which is
  worse than an honest one because nobody has built the process that a real
  Customer-Supplier relationship requires.
- It scales poorly past two teams. A three-way or larger Partnership
  multiplies the coordination surface combinatorially, and in practice
  organizations that try it either collapse into a hub-and-spoke
  Open Host Service or fragment into several bilateral Partnerships.
- It provides no protection against a poorly-designed shared surface the way
  Anticorruption Layer protects a downstream model from an upstream one;
  both teams' models are directly exposed to whatever the joint surface
  looks like.

## 11. Failure modes and misuse

**The unacknowledged power imbalance.** Symptom. One team's engineers
routinely find out about a breaking change from a failing build rather than
from the standing sync, and that team consistently absorbs the rework.
Cause. The Partnership was declared on an org chart but one team never
actually had veto power over the other's changes. Fix. Either formally
convert the relationship to Customer-Supplier with the weaker team as
downstream and a real backlog process, or escalate to leadership to
establish genuine parity, because leaving the label as Partnership without
the substance produces the worst outcomes of both patterns.

**The dead coordination cadence.** Symptom. A shared Slack channel or a
weekly sync exists on paper, but breaking changes still surprise both sides,
and the joint contract test suite has not been updated in months even as the
integration surface visibly drifted. Cause. The coordination process was set
up once and never staffed as an ongoing commitment; both teams treat it as
optional when sprint pressure rises. Fix. Assign explicit ownership of the
contract test suite's freshness to a named person on each side, and treat a
stale shared test suite as a defect with the same severity as a failing
build.

**Silent scope creep of the shared surface.** Symptom. The integration
surface between the two Contexts, originally a handful of well-understood
fields, has grown to expose most of both teams' internal models, and neither
team can change an internal detail without triggering a joint negotiation.
Cause. Every ad hoc convenience field added to the shared contract without
deliberate curation, because Partnership has no formal Published Language
gatekeeper the way Open Host Service does. Fix. Periodically review the
shared surface with both teams present and prune fields that duplicate
internal detail rather than genuine integration need, treating the surface
review itself as a recurring item in the joint coordination cadence.

**Mistaking co-location for Partnership.** Symptom. Two teams that sit near
each other, or share a monorepo, assume the relationship is healthy because
communication is easy, but no actual joint planning or shared CI exists, and
breaking changes still surprise one side. Cause. Physical or repository
proximity was mistaken for the organizational commitment the pattern
actually requires. Fix. Stand up the explicit joint coordination process and
shared contract tests described in dimension 5; proximity reduces the cost
of building that process but does not substitute for it.

**Three-or-more-way Partnership sprawl.** Symptom. A "partnership" meeting
now includes representatives from four teams, decisions take weeks to reach
consensus, and nobody can name who agreed to the current state of the shared
surface. Cause. Bilateral Partnership was extended informally to additional
teams as the integration surface grew, without recognising that the
coordination cost scales combinatorially, not linearly, with team count.
Fix. Split into either a hub team that runs Open Host Service for the
others, or several genuinely bilateral Partnerships each with a narrower
surface, per Vernon (2013), Chapter 3's caution that Partnership works best
between exactly two teams.

## 12. Trade-off matrix

| Force | Partnership | Customer-Supplier | Shared Kernel | Separate Ways |
|---|---|---|---|---|
| Authority structure | Symmetric, no upstream side | Explicit upstream and downstream | Symmetric, but bounded to a fixed shared artifact | No relationship at all |
| Standing coordination cost | High, recurring, ad hoc | Moderate, formalised via backlog | Moderate, versioned build coordination | None |
| Escalation path on disagreement | None defined by the pattern itself | Backlog priority process | Joint build ownership process | Not applicable, no shared surface |
| Speed of unilateral change | Neither side can change unilaterally | Downstream cannot, upstream can within its own priorities | Neither side can change the kernel unilaterally | Either side changes freely, no coordination |
| Failure detection latency | Immediate, joint CI | Depends on downstream's own test cadence against upstream releases | Immediate, shared build breaks for both | Never detected as a shared concern, duplication drifts silently |
| Best fit when | Two teams, tightly coupled plans, equal standing | One team has real authority over the other | The shared subset is small, stable, and separately versionable | The overlap is small enough that duplication is cheaper than coordination |

## 13. Related and incompatible patterns

**Customer-Supplier.** The directional sibling of Partnership on the same
Context Map. The two patterns are mutually exclusive descriptions of the same
underlying relationship between two teams, choosing between them is a factual
question about whether real upstream authority exists, not a stylistic
preference. Applying Customer-Supplier language and process to a genuinely
symmetric relationship denies the weaker team the standing Partnership grants
it; applying Partnership language to a genuinely asymmetric relationship
hides the power imbalance instead of formalising it, per the failure mode in
dimension 11.

**Shared Kernel.** Both patterns involve two teams jointly maintaining
something. Shared Kernel's jointly-maintained thing is a code artifact, a
subset of the domain model itself, compiled and versioned as a single unit
both sides depend on directly. Partnership's jointly-maintained thing is a
process and an integration surface between two otherwise independent models.
A team can run both at once, sharing a small kernel of common types while
also maintaining a Partnership over the broader integration between their two
Contexts, but conflating them, treating the whole integration surface as if
it were a Shared Kernel, tends to produce the subclass-explosion-style sprawl
described in dimension 11's silent scope creep failure.

**Bounded Context.** Partnership is meaningless without two genuine Bounded
Contexts on either side. If either side's "model" is not actually distinct
from the other's, the relationship is not an integration problem at all, it
is one team that should simply merge its work into the other's Context.

**Context Map.** Partnership is one of the named relationships a Context Map
records between two Contexts. The Context Map is the artifact; Partnership is
one possible label on one edge of it. A healthy DDD architecture typically
mixes several relationship types across its full Context Map, Partnership on
one edge, Customer-Supplier on another, Anticorruption Layer on a third.

**Separate Ways.** The pattern to fall back to when Partnership's
coordination cost is judged not worth paying for the size of the actual
overlap. Choosing between Partnership and Separate Ways is explicitly a cost
comparison, not a correctness question, per dimension 4.

**Open Host Service and Published Language.** The pattern to reach for when
the coordination needs to scale beyond two teams or beyond synchronous
availability, converting an ad hoc bilateral negotiation into a published,
versioned, one-to-many contract that consumers integrate against without
needing a standing joint meeting. A Partnership that has grown past two teams
is frequently refactored into an Open Host Service, see the three-way sprawl
failure mode in dimension 11.

**Incompatible with Customer-Supplier and Conformist as simultaneous labels
on the same edge.** A single relationship between two specific teams cannot
honestly be described as both symmetric, Partnership, and directional,
Customer-Supplier or Conformist, at the same time. Different edges of a
larger Context Map involving three or more teams can of course carry
different relationship types.

## 14. Refactoring path in and out

**Introducing a Partnership where none formally existed.** The starting
point is almost always an informal, undocumented coupling between two teams
that already exists in practice, evidenced by frequent unplanned breakage
between the two Contexts, before any pattern name has been applied to it.
First, make the coupling visible by drawing the Context Map and naming the
edge, which alone often surfaces the power-imbalance question from dimension
3 that leadership needs to answer honestly before the pattern can work.
Second, stand up the shared contract test suite described in dimension 8 and
wire it into both teams' existing CI pipelines, starting narrow, covering
only the fields both sides agree are the actual integration surface today,
rather than attempting to formalise every ad hoc field already in use.
Third, establish the standing joint coordination cadence, a recurring
meeting or a shared backlog, and treat its first several sessions as an
audit of the current integration surface rather than as a forum for new
feature requests. Fourth, once both the test suite and the coordination
cadence are running reliably for several release cycles, the relationship
can be recorded as Partnership on the team's Context Map documentation.

**Refactoring out of Partnership.** A Partnership is removed for one of two
reasons, either the coordination cost has stopped being worth the size of
the remaining overlap, or the relationship has quietly become directional in
practice and deserves to be renamed. To move toward Separate Ways, first
measure the actual size of the shared surface; if it has shrunk to a handful
of fields that could each be independently duplicated cheaply, propose
duplicating them and retiring the shared contract test suite, watching for
drift over the following release cycles rather than assuming duplication is
free forever. To move toward Customer-Supplier, first get both team leads to
agree explicitly on which side is actually upstream, since this
conversation is usually the one the organization avoided when it defaulted
to calling the relationship a Partnership in the first place, then stand up
the formal backlog and priority process Customer-Supplier requires, and
retire the symmetric joint-planning cadence in favour of the downstream
team's formal request channel. To move toward Open Host Service, extract the
shared contract into a versioned, publishable artifact, a schema, an API
specification, or an event catalog, and shift consumers, including the
original partner team, onto pulling from that published artifact rather
than negotiating changes synchronously.

## 15. Testing and verification

Testing a Partnership relationship is largely testing the shared integration
surface, and the defining property of a healthy Partnership is that this
testing runs continuously across both sides rather than being the sole
responsibility of either team.

A jointly-owned contract test suite, run in each side's CI pipeline against
the other side's current interface, is the primary verification mechanism.
Consumer-driven contract testing tools, Pact being the most widely adopted,
let the consuming side specify the exact expectations it has of the
providing side's response shape, and the providing side runs those
expectations against its own implementation before every deploy, which
catches a breaking change at the exact commit that introduces it rather than
after both sides have independently released. Because Partnership is
symmetric, both sides typically play both roles, each side both consumes and
provides some part of the shared surface, so both sides maintain contract
expectations against the other.

What becomes easier to test because of the pattern is the integration
boundary itself, since it is explicitly named, jointly owned, and has a
dedicated test suite that neither side can silently let rot without the
other side noticing a stale suite. What becomes harder to test is anything
that depends on the internal behaviour of the partner Context beyond the
agreed surface, since Partnership deliberately does not expose or stabilise
internal details, an end-to-end test that reaches past the negotiated
surface into the partner's internals is a sign the surface itself is
under-specified and should be renegotiated rather than tested around.

Organizational verification matters as much as code verification here. A
useful, low-cost check that a Partnership is real rather than nominal is to
audit whether the joint coordination artifact, the meeting notes, the shared
backlog, or the shared test suite's commit history, shows activity from both
teams within the last month. A Partnership with commits or meeting
attendance from only one side has already degraded into the unacknowledged
power imbalance described in dimension 11, whatever the org chart says.

## 16. Observability signals

A healthy Partnership shows a specific, checkable signature in both process
and telemetry data, distinct from what a healthy Customer-Supplier or Shared
Kernel relationship would show.

At the process level, the joint contract test suite's commit history should
show contributions from engineers on both teams, roughly balanced over any
given quarter, not concentrated on one side. The joint coordination artifact,
whether meeting notes or a shared backlog, should show recent activity from
both sides. A dashboard tracking "days since either side updated the shared
contract test" is a cheap, high-signal proxy for whether the coordination
cadence is actually alive.

At the runtime level, the shared integration surface itself should be
instrumented on both sides, with matching trace attributes or correlation
identifiers that let an operator follow a single business transaction across
both Contexts. Because Partnership has no formal Anticorruption Layer
absorbing translation, a schema mismatch between the two sides typically
manifests directly as a deserialisation error or a validation failure at the
boundary, and that error rate is the primary runtime health signal for the
relationship, spiking sharply whenever one side ships a surface change the
other side has not yet adopted.

A failing signal specific to this pattern, distinct from an ordinary service
outage, is asymmetric error attribution, one side's dashboards show a spike
in integration errors while the other side's dashboards show nothing unusual
at all, because it shipped the breaking change and has not yet felt the
consequence. That asymmetry is itself diagnostic, it indicates the change
that caused the break originated on the side with the quiet dashboard, and
is the concrete signal an on-call engineer uses to know which team to page
first.

## 17. Security and privacy implications

Partnership widens each Context's trust boundary to include the other
Context's team as a peer with joint change authority over the shared
surface, which has two concrete security implications worth naming plainly
rather than leaving silent.

First, because there is no formal Anticorruption Layer absorbing the
integration, whatever data one Context sends across the shared surface is
directly consumed by the other side's model with no intermediate validation
or sanitisation layer required by the pattern itself. If the shared surface
carries personal data, both teams' security and privacy review processes
need to independently cover it, since neither team can assume the other has
already validated or minimised the data on its way across the boundary. This
is a meaningful contrast with Anticorruption Layer, where the translation
layer is a natural, single place to enforce a data minimisation or
redaction policy at the boundary.

Second, the shared contract test suite and the joint coordination artifact,
if hosted in a shared repository or shared tooling, become a shared
credential and access-control surface. Both teams' engineers typically need
write access to the same test suite and the same CI configuration, which
means a compromised credential on either side can affect the other team's
deployed integration surface. Organizations running Partnership at scale
should apply the same least-privilege review to the shared contract
repository that they would apply to any other shared production artifact,
rather than treating it as low-stakes because it is "just tests."

Where a Partnership's shared surface never carries personal or otherwise
sensitive data, and the shared repository access is scoped no more broadly
than either team's own production access already is, the pattern introduces
no security implication beyond the ordinary trust extended to any two teams
already inside the same organizational security boundary.

## 18. References

- Eric Evans, "Domain-Driven Design. Tackling Complexity in the Heart of
  Software," Addison-Wesley, 2003, Part IV, Chapter 14, "Maintaining Model
  Integrity."
- Eric Evans, "Domain-Driven Design Reference. Definitions and Pattern
  Summaries," Domain Language, Inc., self-published, 2015.
- Vaughn Vernon, "Implementing Domain-Driven Design," Addison-Wesley, 2013,
  Chapter 3, "Context Maps."
- Nick Tune and Scott Millett, "Patterns, Principles, and Practices of
  Domain-Driven Design," Wrox, 2015, Chapter 13, "Managing Big Balls of Mud."
- Alberto Brandolini, "Introducing EventStorming," self-published, Leanpub,
  2021, Chapter 8.
- Netflix Technology Blog, "Practical API Design at Netflix, Part 1. Using
  Protobuf FieldMask,"
  https://netflixtechblog.com/practical-api-design-at-netflix-part-1-using-protobuf-fieldmask-35cfdc606518
  verified 2026-08-02.
- Pact documentation, "What is Contract Testing,"
  https://docs.pact.io/ verified 2026-08-02.
- Apollo GraphQL documentation, "Federation overview" and schema checks,
  https://www.apollographql.com/docs/graphos/reference/federation/errors and
  https://www.apollographql.com/docs/graphos/platform/schema-management/checks
  verified 2026-08-02.
- Henrik Kniberg and Anders Ivarsson, "Scaling Agile @ Spotify with Tribes,
  Squads, Chapters and Guilds," Spotify Engineering Culture whitepaper, 2012,
  https://blog.crisp.se/wp-content/uploads/2012/11/SpotifyScaling.pdf
  verified 2026-08-02.

## Code examples

Partnership is a team and process pattern with no unique runtime code shape
of its own, dimension 8 explains this plainly. What is demonstrable in code
is the artifact most Partnerships actually produce, a jointly-owned contract
test that verifies both sides of a shared integration surface still agree on
its shape. The three examples below model a small slice of the
order-fulfilment and warehouse-inventory Partnership used as the running
example in dimension 2, a shared "stock reservation" event both teams commit
to jointly.

### TypeScript

```typescript
interface StockReservation {
  orderId: string;
  sku: string;
  quantity: number;
  reservedAt: string;
}

function validateReservation(payload: unknown): StockReservation {
  const p = payload as Record<string, unknown>;
  const missing = ["orderId", "sku", "quantity", "reservedAt"].filter(
    (key) => !(key in p),
  );
  if (missing.length > 0) {
    throw new Error("Partnership contract violated, missing: " + missing.join(", "));
  }
  if (typeof p.quantity !== "number" || p.quantity <= 0) {
    throw new Error("Partnership contract violated, quantity must be positive");
  }
  return {
    orderId: String(p.orderId),
    sku: String(p.sku),
    quantity: p.quantity,
    reservedAt: String(p.reservedAt),
  };
}

const fulfilmentSidePayload = {
  orderId: "ord-4821",
  sku: "sku-warehouse-77",
  quantity: 3,
  reservedAt: "2026-08-02T10:00:00Z",
};

const parsed = validateReservation(fulfilmentSidePayload);
console.log("Team A validated the shared contract:", parsed);

try {
  validateReservation({ orderId: "ord-9", sku: "sku-1", quantity: -1, reservedAt: "x" });
} catch (err) {
  console.log("Team B's inventory side would reject:", (err as Error).message);
}
```

### Python

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class StockReservation:
    order_id: str
    sku: str
    quantity: int
    reserved_at: str


def validate_reservation(payload: dict) -> StockReservation:
    required = ["order_id", "sku", "quantity", "reserved_at"]
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"Partnership contract violated, missing: {', '.join(missing)}")
    if not isinstance(payload["quantity"], int) or payload["quantity"] <= 0:
        raise ValueError("Partnership contract violated, quantity must be positive")
    return StockReservation(
        order_id=str(payload["order_id"]),
        sku=str(payload["sku"]),
        quantity=payload["quantity"],
        reserved_at=str(payload["reserved_at"]),
    )


if __name__ == "__main__":
    warehouse_side_payload = {
        "order_id": "ord-4821",
        "sku": "sku-warehouse-77",
        "quantity": 3,
        "reserved_at": "2026-08-02T10:00:00Z",
    }
    reservation = validate_reservation(warehouse_side_payload)
    print("Team B validated the shared contract:", reservation)

    try:
        validate_reservation({"order_id": "ord-9", "sku": "sku-1", "quantity": 0, "reserved_at": "x"})
    except ValueError as exc:
        print("Team A's fulfilment side would reject:", exc)
```

### Go

```go
package main

import (
	"errors"
	"fmt"
)

type StockReservation struct {
	OrderID    string
	SKU        string
	Quantity   int
	ReservedAt string
}

func validateReservation(orderID, sku string, quantity int, reservedAt string) (StockReservation, error) {
	if orderID == "" || sku == "" || reservedAt == "" {
		return StockReservation{}, errors.New("partnership contract violated, missing required field")
	}
	if quantity <= 0 {
		return StockReservation{}, errors.New("partnership contract violated, quantity must be positive")
	}
	return StockReservation{
		OrderID:    orderID,
		SKU:        sku,
		Quantity:   quantity,
		ReservedAt: reservedAt,
	}, nil
}

func main() {
	reservation, err := validateReservation("ord-4821", "sku-warehouse-77", 3, "2026-08-02T10:00:00Z")
	if err != nil {
		fmt.Println("unexpected error:", err)
		return
	}
	fmt.Printf("Both sides agree on the shared contract: %+v\n", reservation)

	_, err = validateReservation("ord-9", "sku-1", -1, "x")
	if err != nil {
		fmt.Println("the other side's CI would fail this commit:", err)
	}
}
```

I compiled and ran the TypeScript sample with `npx tsc` against a scratch
project plus `node`, the Python sample with `python3`, and the Go sample with
`go run`, and all three produced the expected output, the valid reservation
printing successfully and the invalid one raising the expected contract
violation. I did not have a working `rustc`, `javac`, or `swiftc` toolchain
available in this environment to compile a fourth or fifth sample, and I am
stating that plainly rather than claiming an unverified compile.
