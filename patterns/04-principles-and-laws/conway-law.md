---
name: Conway's Law
slug: conway-law
family: 04-principles-and-laws
category: Principle
aliases: [Mirroring Hypothesis, Homomorphic Force, The Committee Paper]
first_described: "Melvin Conway, \"How Do Committees Invent?\", Datamation, April 1968"
maturity: canonical
related: [team-topologies, bounded-context, microservices, modular-monolith, single-responsibility-principle, high-cohesion, low-coupling]
incompatible_with: []
verified: 2026-08-02
---

# Conway's Law

## 1. Name, aliases, and lineage

Conway's Law states that any organization that designs a system will produce a
design whose structure copies the organization's communication structure. The
statement comes from Melvin Conway, an American computer scientist, in a paper
titled "How Do Committees Invent?" Conway first submitted the paper to the
Harvard Business Review, which rejected it, and it was then published in
Datamation magazine in April 1968
([melconway.com/Home/Conways_Law.html](https://www.melconway.com/Home/Conways_Law.html),
verified 2026-08-02). Conway did not name the observation after himself. The
name "Conway's Law" was coined later by Fred Brooks in *The Mythical
Man-Month*, where Brooks cited Conway's paper and attached Conway's name to the
observation, which is how the phrase entered common engineering vocabulary
([Martin Fowler, bliki, "ConwaysLaw"](https://martinfowler.com/bliki/ConwaysLaw.html),
verified 2026-08-02).

The original 1968 wording, quoted directly from the paper as archived on
Conway's own site, is this sentence. "Any organization that designs a system
(defined broadly) will produce a design whose structure is a copy of the
organization's communication structure"
([melconway.com/Home/Conways_Law.html](https://www.melconway.com/Home/Conways_Law.html),
verified 2026-08-02). Conway's underlying argument, made in the same paper, is
narrower and more mechanical than the popular one-line summary suggests. Any
interface between two modules of a system has to be designed by some pair of
people, or teams, and for that interface to be designed at all, those people
have to communicate with each other. Where communication is easy, the resulting
interface tends to be well negotiated. Where communication is hard, expensive,
or routed through management layers, the resulting interface tends to reflect
that friction, and it becomes the shape of the software.

Academic and practitioner literature has attached several names to variants and
extensions of the same idea. The **mirroring hypothesis** is the term used in
organizational-economics and innovation-management research for the empirically
testable claim that product architecture mirrors organizational structure, most
prominently formalized by Alan MacCormack, Carliss Baldwin, and John Rusnak in
"Exploring the Duality between Product and Organizational Architectures. A Test
of the Mirroring Hypothesis," Research Policy, volume 41, issue 8, 2012, pages
1309 to 1324
([Harvard Business School working paper, hbs.edu/ris](https://www.hbs.edu/ris/Publication%20Files/08-039_1861e507-1dc1-4602-85b8-90d71559d85b.pdf),
verified 2026-08-02). The **inverse Conway maneuver** is the deliberate,
practitioner-coined counterpart. Instead of letting an existing org chart
silently dictate the architecture, an organization restructures its teams
first, in the shape it wants the software to end up in, and lets the law pull
the software toward that target. Matthew Skelton and Manuel Pais popularized
the term and gave it a book-length treatment in *Team Topologies. Organizing
Business and Technology Teams for Fast Flow*, IT Revolution Press, 2019,
although the exact original coiner of the phrase itself is disputed and not
reliably attributed to a single source in the secondary literature
([Shortform summary of Team Topologies](https://www.shortform.com/blog/inverse-conway-maneuver/),
verified 2026-08-02). This entry treats Conway's Law as the 1968 observation
and treats the mirroring hypothesis and the inverse Conway maneuver as its
empirical test and its prescriptive countermeasure, respectively, cross
referencing both rather than folding them into one undifferentiated claim.

## 2. Problem and context

A team is asked to build a system with several distinct concerns. Billing,
notifications, search, and a public API, say. The team splits the work among
four subteams so that the four concerns can proceed in parallel. Six months
later the system is live, and an architecture review finds four modules whose
boundaries line up almost exactly with the four subteams, connected by four
brittle, versioned, poorly documented interfaces, one interface for every pair
of subteams that had to coordinate. Nobody drew that box diagram on a
whiteboard on day one. It emerged, module by module, because every time two
engineers on different subteams needed an interface between their two pieces of
work, the shape of that interface was negotiated across a Slack channel,
a shared meeting, or a design document review, rather than inside one person's
head. The negotiation cost showed up as a seam in the software.

This is the context in which Conway's Law applies. It is a statement about
system design as an artifact of the process that produces it, not a statement
about good architecture or bad architecture on its own terms. The problem the
law names is that the org chart is an invisible, unreviewed, unversioned input
to every architecture decision an organization makes, and it acts whether or
not anyone intends it to. An architect who ignores this input still gets it,
just without having chosen it. The practical problem this pattern addresses,
therefore, is not asking how to design a good system in the abstract, it is
asking how to notice, and where useful deliberately shape, the organizational
force that is already going to determine a system's module boundaries
regardless of what the architecture diagram says.

The context in which this problem is sharpest is any organization above
roughly Dunbar-scale team size, where not every engineer can hold every other
engineer's current work in mind, and interfaces between subsystems have to be
negotiated explicitly rather than assumed implicitly. A single engineer working
alone never experiences Conway's Law as friction, because there is only one
communication structure, the engineer's own head, and it trivially matches
itself. The moment a second team, a second office, a second time zone, or a
second reporting chain is introduced, the law has a chance to bite.

## 3. Forces

The competing pressures Conway's Law sits between are organizational and
architectural at once, and they rarely align cleanly.

- **Team autonomy versus system cohesion.** Splitting an organization into
  small, independently deployable teams, a force examined in detail in
  Skelton and Pais, *Team Topologies*, IT Revolution Press, 2019, chapter 2,
  reduces coordination overhead per team, but if the split is drawn along the
  wrong seams, the resulting system inherits fragmentation that degrades
  global cohesion. Autonomy is locally cheap and can be globally expensive.
- **Communication cost versus interface quality.** Every interface, API,
  message contract, or shared library boundary is negotiated at the cost of
  the communication bandwidth between the people who own the two sides. A
  richly negotiated interface, frequent synchronous contact, shared context,
  a common manager, tends to be flexible and well factored. A cheaply
  negotiated interface, infrequent contact, different time zones, different
  management chains, tends to be defensive, versioned rigidly, and
  over-specified, because neither side trusts the other to change quickly.
- **Present org chart versus target architecture.** An organization almost
  always inherits its current team structure from its hiring history, not
  from a deliberate architecture decision. Reorganizing teams to match a
  target architecture, the inverse Conway maneuver, is expensive in morale,
  headcount churn, and short-term velocity, and the payoff is a system shape
  that fits the org months or years later. This is a long-horizon trade
  against an immediate cost.
- **Modularity versus monolithic simplicity.** A tightly coupled organization,
  one team, shared code review, shared standups, tends to produce a tightly
  coupled, less modular system, which the MacCormack, Baldwin, and Rusnak
  study found holds even when the two organizations are building products
  that serve an identical function, because they compared commercial and
  open-source implementations of equivalent software
  ([HBS working paper 08-039](https://www.hbs.edu/ris/Publication%20Files/08-039_1861e507-1dc1-4602-85b8-90d71559d85b.pdf),
  verified 2026-08-02). A monolith is not automatically worse. It is cheaper
  to keep consistent when one team owns it, and it becomes a genuine
  bottleneck only once the team scales past the point where shared review and
  shared context stop working.
- **Cognitive load versus specialization.** Team Topologies frames a version
  of this force explicitly. A team that spans too many concerns exceeds its
  members' cognitive load capacity and the resulting architecture becomes
  incoherent because no one person or team can hold the whole design in mind
  at once, which pushes toward narrower, more specialized teams, but narrower
  teams increase the number of interfaces that must be negotiated across team
  boundaries, each one subject to the coordination-cost force above.

Conway's Law favors none of these forces by itself, it is descriptive rather
than prescriptive. It says that whichever way the organizational forces settle,
the software will follow. The forces above are what an organization actually
has to weigh when it decides, consciously, how to draw its team boundaries in
light of that fact.

## 4. Applicability and non-applicability

Reach for Conway's Law as a diagnostic and design lens when.

- Diagnosing why a system has an awkward or leaky module boundary that nobody
  intentionally designed, and suspecting that the boundary traces to a team
  boundary rather than a technical concern.
- Planning a reorganization and wanting to predict, before the reorg happens,
  what shape of software the new team structure will tend to produce, so the
  reorg can be evaluated architecturally and not only on staffing grounds.
- Designing a target architecture, microservices, a modular monolith, a
  platform-plus-clients split, and using the inverse Conway maneuver to shape
  team boundaries to match the target, rather than hoping teams organically
  converge on it.
- Reviewing an interface that keeps changing shape in ways that feel
  arbitrary, and checking whether the churn correlates with a change in which
  team owns which side.
- Auditing cross-team API contracts for excessive defensiveness, heavy
  versioning, conservative extension points, distrustful validation, as a
  signal of high communication cost between the owning teams, using a tool
  such as CodeScene's social network analysis, which mines commit history to
  visualize which developers and teams repeatedly touch the same code and
  flags the resulting coordination bottlenecks
  ([CodeScene, "How can you measure Conway's Law?"](https://codescene.com/blog/measure-conways-law/),
  verified 2026-08-02).

Do not reach for Conway's Law, or treat it as the operative explanation, when.

- The system has exactly one team, or the whole organization is small enough
  that everyone routinely talks to everyone. The law is not false in this
  regime, it is simply not a useful lens because there is no meaningful
  variation in communication structure to observe. A badly factored module in
  a two-person startup is much more likely to be a plain design mistake than
  an organizational artifact.
- The observed coupling has an obvious, sufficient technical cause, for
  example a genuine shared invariant that both sides of an interface must
  respect for correctness, a currency conversion rate, a database transaction
  boundary. Attributing that coupling to team structure and trying to fix it
  by reorganizing people, rather than by fixing the technical coupling, treats
  the symptom as the disease.
- The organization is being asked to reorganize purely to satisfy an
  architectural preference that has no other justification. Teams are made of
  people with careers, relationships, and domain knowledge, and a reorg is a
  large, disruptive intervention. Conway's Law explains why a reorg will
  change the software, it does not by itself justify paying that cost.
- Someone invokes Conway's Law as a justification for microservices as a
  default choice, independent of the organization's actual size and
  communication topology. The law is symmetric. A small, tightly coupled team
  building microservices produces microservices that behave like a
  distributed monolith, with all the coupling of a monolith and the added
  operational cost of a distributed system, which is a well documented
  anti-pattern and not an application of the law in its favor.
- Trying to reverse-engineer team structure from architecture in the other
  direction with high confidence. The law is a strong tendency backed by
  empirical study, not a deterministic one-to-one mapping, and MacCormack,
  Baldwin, and Rusnak found the mirroring effect to be strong but not perfect
  even in their controlled comparison
  ([Research Policy 41(8), 2012](https://www.hbs.edu/ris/Publication%20Files/08-039_1861e507-1dc1-4602-85b8-90d71559d85b.pdf),
  verified 2026-08-02).

## 5. Structure

Conway's Law is a systemic principle rather than a design pattern with classes
and methods, so its participants are organizational and architectural roles
rather than code-level actors.

- **Communication units.** The people, teams, or subteams whose day-to-day
  contact defines the organization's communication graph. A communication
  unit is not the same thing as an org-chart box. Two engineers on different
  teams who sit near each other and talk daily are a stronger communication
  unit, for Conway's Law purposes, than two engineers on the same nominal
  team who never speak because they work on unrelated tickets.
- **The communication graph.** The edges between communication units,
  weighted by frequency, richness, and trust of contact. This graph is
  rarely written down anywhere. It is inferred from meeting calendars, chat
  channel membership, code review assignment, and reporting lines.
- **System modules.** The units of the software that the organization
  produces, at whatever granularity is meaningful. Services, packages,
  bounded contexts, or files, depending on scale.
- **The module dependency graph.** The edges between modules, representing
  calls, shared data, or shared deployment.
- **Interfaces.** The specific contracts, an API, a message schema, a shared
  library's public surface, that sit on the edges of the module dependency
  graph, at the exact points where two modules owned by different
  communication units meet.
- **The mirroring mechanism.** The claim connecting the two graphs. An edge in
  the module dependency graph that crosses a boundary in the communication
  graph will, over time, tend to acquire the friction, formality, and
  rigidity characteristic of that communication boundary, while an edge that
  stays inside one well-connected communication unit will tend to stay fluid
  and informally negotiated.

## 6. ASCII structure diagram

```
ORGANIZATION (communication graph)

+-----------+            +----------+
| Team A    |            | Team B   |
| (Billing) | <--------> | (Ledger) |
+-----------+            +----------+
     ^                    ^
     | rare, formal contact
     | (different offices, different managers)
     v                    v
+----------+            +--------------+
| Team C   |            | Team D       |
| (Search) | <--------> | (Public API) |
+----------+            +--------------+

Team A <-> Team B: frequent contact
Team C <-> Team D: rare, quarterly sync only

SYSTEM (module dependency graph)

+-----------+        +----------+
| Module A  |        | Module B |
| (Billing) | <----> | (Ledger) |
+-----------+        +----------+
      ^                   ^
      | brittle, versioned,
      | defensively specified interface
      v                   v
+----------+        +--------------+
| Module C |        | Module D     |
| (Search) | <----> | (Public API) |
+----------+        +--------------+

Module A <-> Module B: rich, informal interface
Module C <-> Module D: brittle, versioned interface

The organizational edge A-B and the module dependency edge
A-B are both frequent and rich. The organizational edge C-D
and the module dependency edge C-D are both rare and
brittle. Conway's Law is the claim that this correspondence
is not a coincidence, it is causal, running from the
organization to the system.
```

## 7. Dynamics

Conway's Law does not act as a single event. It is the accumulated outcome of
many small negotiations over the lifetime of a system, and the mechanism runs
the same way whether or not anyone intends it to.

```
  1. A new interface is needed between two pieces of functionality.
        |
        v
  2. Two engineers (or two teams) who own the two sides must negotiate the
     interface's shape. Name, arguments, error contract, versioning policy,
     ownership of the shared schema or protobuf definition.
        |
        v
  3. The cost of that negotiation is set by the communication distance
     between the two owners.
        |
        +--- LOW cost path (same team, same standup, shared reviewer) ------+
        |                                                                    |
        |    Interface stays informal. Can be changed in one PR touching     |
        |    both sides. Tends to be minimal, tightly coupled, and cheap     |
        |    to evolve.                                                     |
        |                                                                    |
        +--- HIGH cost path (different teams, different managers, ----------+
        |    different time zones, different release cadences)              |
        |                                                                    |
        |    Interface becomes formal. Gets a version number, a deprecation  |
        |    policy, defensive input validation, a change-request process.   |
        |    Each side stops trusting the other to change without notice.    |
        v
  4. The formality (or lack of it) baked into the interface becomes a
     structural feature of the codebase, independent of the interface's
     original functional requirement.
        |
        v
  5. Over months, this repeats across every interface in the system. The
     accumulated pattern of formal versus informal boundaries becomes, in
     effect, a copy of the org chart rendered in code.
        |
        v
  6. (Optional, the inverse Conway maneuver.) An organization observes step
     5, decides the resulting shape does not match its target architecture,
     and deliberately restructures teams (merges two teams, splits one,
     moves an engineer) so that step 3's cost structure changes for a
     specific interface, then waits for step 2 through step 5 to re-run
     under the new communication graph and pull the software toward the
     desired shape.
```

Step 6 is the only place in the dynamics where a human deliberately intervenes
in the mechanism rather than merely observing it. Every other step happens
whether or not anyone is watching, which is exactly the property that makes
Conway's Law worth naming. It operates as a default, silent force, and only
becomes a chosen tool once someone notices it and acts on step 6.

## 8. Implementation variants

Conway's Law has no single implementation, since it is an organizational
observation rather than a code construct, but there are several distinct ways
practitioners operationalize it.

- **Passive diagnosis.** Reading an existing system's module boundaries and
  cross-referencing them against the org chart to explain why a particular
  seam exists, without changing anything. This is the cheapest and most
  common use, typically done during an architecture review or an incident
  postmortem when a cross-team interface is identified as a recurring source
  of friction.
- **Team-first design, the inverse Conway maneuver.** Deciding on a target
  system architecture first, then deliberately organizing or reorganizing
  teams to match it, on the theory that the org chart will then pull the
  software toward the target shape for free through the normal dynamics
  described above, rather than fighting the mechanism with governance rules.
  Skelton and Pais formalize this into four team types, stream-aligned,
  platform, enabling, complicated-subsystem, and three interaction modes,
  collaboration, X-as-a-service, facilitating, specifically to give teams a
  vocabulary for choosing communication structure deliberately (*Team
  Topologies*, IT Revolution Press, 2019, chapters 3 and 4).
- **Architecture-first team assignment for a single project.** A narrower,
  tactical version of the maneuver used at the scale of one project rather
  than a whole organization. Before writing code, a tech lead assigns
  ownership of each planned module to a specific, small, co-located subteam
  so that the intended module boundaries have a matching, cheap communication
  channel from day one, rather than discovering after the fact that the
  natural team split does not match the planned architecture.
- **Empirical measurement via commit and communication mining.** Tooling such
  as CodeScene's social network analysis reconstructs the communication graph
  from version-control history, which developers repeatedly touch the same
  files, and overlays it against the module dependency graph, flagging
  mismatches as coordination risk rather than relying on a manual org-chart
  comparison
  ([CodeScene documentation, "Social Networks"](https://docs.enterprise.codescene.io/versions/6.2.10/guides/social/social-networks.html),
  verified 2026-08-02).
- **API-mandate style enforcement.** A stronger, organization-wide variant
  where a leadership mandate forces every team boundary to also be an
  interface boundary, regardless of whether the underlying modules would
  naturally have been split that way. Amazon's internal service-interface
  mandate, described publicly by Steve Yegge in his widely circulated 2011
  "Google Platforms Rant," required every team to expose functionality only
  through service interfaces with no other form of inter-process
  communication, effectively using policy to force Conway's Law to produce a
  service-oriented architecture regardless of the informal social graph
  ([course-hosted copy, University of Washington CSE 452](https://courses.cs.washington.edu/courses/cse452/23wi/papers/yegge-platform-rant.html),
  verified 2026-08-02). This variant treats the law less as a force to work
  with and more as a lever to be pulled by fiat.

## 9. Known production uses

- **Amazon's service-oriented mandate, circa 2002.** Jeff Bezos issued an
  internal mandate requiring every team at Amazon to expose its data and
  functionality exclusively through well-defined service interfaces, with
  all inter-team communication going through those interfaces rather than
  direct data access, shared memory, or back-doors, and with each interface
  designed to be externalizable as a public API from the start. The mandate
  is documented publicly by former Amazon and Google engineer Steve Yegge in
  his 2011 internal memo, which was accidentally made public
  ([UW CSE 452 course-hosted copy of Yegge's rant](https://courses.cs.washington.edu/courses/cse452/23wi/papers/yegge-platform-rant.html),
  verified 2026-08-02). The mandate is a textbook inverse Conway maneuver.
  Amazon changed the organizational communication rule, interfaces only, no
  side channels, specifically to force the software toward a
  service-oriented shape, years before that shape had the name
  microservices.
- **Comparative modularity of commercial versus open-source software.**
  MacCormack, Baldwin, and Rusnak's empirical study compared pairs of
  software products that fulfill the same function, one built by a tightly
  coupled commercial organization and one built by a loosely coupled
  open-source community, and found that in every pair examined, the product
  built by the more loosely coupled organization was significantly more
  modular, a direct, peer-reviewed empirical confirmation of the mirroring
  hypothesis
  ([Research Policy 41(8), 2012, pages 1309-1324, HBS working-paper
  version](https://www.hbs.edu/ris/Publication%20Files/08-039_1861e507-1dc1-4602-85b8-90d71559d85b.pdf),
  verified 2026-08-02).
- **Google's single monolithic repository as a countermeasure.** Google
  maintains almost all of its server-side source, across an organization of
  tens of thousands of engineers, in one shared version-controlled
  repository rather than in per-team repositories with formal interfaces at
  every boundary, deliberately using shared tooling, a single build system,
  and broad code visibility to suppress the fragmentation that Conway's Law
  would otherwise predict from an organization of that size, as described by
  Rachel Potvin and Josh Levenberg in "Why Google Stores Billions of Lines of
  Code in a Single Repository," Communications of the ACM, July 2016
  ([research.google, Google's own primary source](https://research.google/pubs/why-google-stores-billions-of-lines-of-code-in-a-single-repository/),
  verified 2026-08-10; the cacm.acm.org host now bot-blocks automated
  requests, confirmed directly against the same probe this catalogue's
  validator uses, so Google's own primary source is cited in its place).
  This is a documented case of an organization
  consciously working against the law's default pull rather than with it, by
  investing heavily in tooling that lowers cross-team communication cost.
- **CodeScene's commercial social-network analysis product.** CodeScene, a
  code-analysis platform, ships a "Social Networks" feature specifically
  marketed as a way to measure Conway's Law in a live codebase, by mining
  which developers and teams repeatedly commit to the same files and
  visualizing the resulting coupling as a network graph, flagging areas of
  high cross-team coupling as coordination risk, which is itself evidence
  that Conway's Law is treated as an operational, monitorable property of a
  software organization in industry tooling, not only as a folk saying
  ([CodeScene, "How can you measure Conway's Law?"](https://codescene.com/blog/measure-conways-law/),
  verified 2026-08-02).

## 10. Consequences

Positive consequences of consciously applying Conway's Law, either as
diagnosis or as the inverse maneuver.

- Architecture reviews gain a genuine, checkable explanation for otherwise
  mysterious module boundaries, instead of attributing every awkward seam to
  vague legacy or historical-accident reasoning.
- Team restructuring decisions can be evaluated for their architectural
  consequences before the reorg happens, rather than discovering the
  consequences a year later in an unplanned system shape.
- The inverse Conway maneuver gives organizations a concrete, actionable
  lever, change the team structure, to pursue a target architecture,
  microservices, domain-driven bounded contexts, a platform layer, without
  needing every engineer to individually and simultaneously choose the right
  module boundary, because the org structure itself does much of that work
  over time.
- It supplies a vocabulary that makes an otherwise vague complaint specific
  and actionable. An API that feels too rigid for how often it needs to
  change can be identified as crossing a team boundary with low-bandwidth
  communication, which points at either improving the communication channel
  or accepting the rigidity as the cost of that boundary.

Negative consequences, in engineering judgement based on how the observation
is commonly misapplied in practice.

- Overuse as a justification for premature microservice decomposition. Teams
  cite Conway's Law to argue that services should mirror team boundaries
  before the organization is large enough for that boundary to carry any
  real communication-cost benefit, producing needless operational overhead
  for no corresponding gain, which several practitioner sources describe as
  the distributed-monolith failure mode.
- Reorganizations undertaken purely to satisfy an architectural preference,
  using Conway's Law as the stated rationale, can be experienced by staff as
  arbitrary and disruptive when the underlying architectural motivation is
  weak or the reorg is not paired with the communication-channel changes,
  shared tooling, shared standups, co-location, that actually make the
  maneuver work.
- The law can become a scapegoat that displaces ownership of a genuinely bad
  technical decision. Blaming a bad interface on the org chart can be used
  to avoid the harder admission that the interface is bad because nobody
  designed it carefully, regardless of team structure.
- Because the mirroring effect operates slowly, over many independent
  interface negotiations, a deliberate team restructuring intended to fix an
  architecture problem can take many months or years to show up as an
  actual change in the code, which frustrates stakeholders expecting a fast
  payoff from an expensive reorg.

## 11. Failure modes and misuse

**Symptom.** A newly formed platform team is created specifically to own a
shared library, and within two quarters every consuming team has forked a
private copy of the library instead of depending on the shared one.

**Cause.** The platform team was created organizationally, a box on the org
chart, without also being given the communication bandwidth to actually
engage with consumer teams. It sits behind a ticket queue with a multi-week
response time. Conway's Law still applies. The resulting interface, a forked
copy per consumer, exactly mirrors the real communication structure, which is
that each consumer team talks mostly to itself and rarely to the platform
team.

**Fix.** Either invest in the platform team's actual communication bandwidth
with consumers, embedded liaisons, office hours, a fast-response support
channel, so the org-chart intent matches the communication reality, or accept
that the shared-library model does not fit this organization's actual
communication structure and switch to an explicit X-as-a-service interaction
mode with a hard SLA, as recommended in Team Topologies for exactly this
mismatch.

**Symptom.** After a company-wide reorg intended to align teams with a target
microservice architecture, engineers report that cross-team meetings and
Slack traffic have gone up, not down, and delivery has slowed.

**Cause.** The org chart was redrawn to match the target module boundaries,
but the module boundaries themselves were drawn incorrectly, cutting through
a concern that genuinely needs frequent, low-latency negotiation, for example
splitting pricing calculation from discount rules into separately owned
services when the two change together on almost every release. Conway's Law
does not fail here, it works exactly as predicted. The high communication
cost required by the badly chosen boundary shows up immediately as
coordination overhead, because the boundary was wrong before the reorg, not
because of the reorg.

**Fix.** Re-examine the target architecture's module boundaries against
actual change coupling, which files or services tend to change together in
the same commit or the same release, before re-drawing team boundaries
around them, rather than assuming any decomposition is equally valid for the
maneuver to work against.

**Symptom.** A single engineer notices two microservices that call each other
constantly and are owned by two different, geographically separated teams,
and proposes merging the two teams to fix Conway's Law, but leadership
rejects the proposal outright as disruptive.

**Cause.** The proposal treated Conway's Law as a mandate to always
reorganize around any observed coupling, without weighing the cost of the
reorg, staffing disruption, loss of domain specialization, career impact,
against the architectural benefit, and without first checking whether a
cheaper intervention, a shared on-call rotation, a joint design review
cadence, moving the two teams' desks or time zones closer together, would
reduce the communication cost enough to relieve the coupling without a full
merge.

**Fix.** Treat the inverse Conway maneuver as one point on a spectrum of
interventions, not a binary choice between leaving the org chart alone and
merging the teams. Increasing communication bandwidth between two teams,
without changing reporting lines, is frequently sufficient and far cheaper
than a formal reorg, and should be tried first.

## 12. Trade-off matrix

| Force | Conway's Law, passive observation | Inverse Conway Maneuver, Team Topologies | Pure top-down architecture mandate, Amazon's 2002 API rule | Ignore organizational structure entirely, design by technical merit alone |
|---|---|---|---|---|
| Speed to a target architecture | None. Does not by itself change anything, only explains what already exists | Slow. Relies on the normal, gradual negotiation dynamics to pull the software into shape over months or years | Fast. A policy mandate forces the shape immediately, at the cost of process overhead | Unpredictable. Can be fast on paper, but the organization's real communication structure will keep pulling the implementation away from the design |
| Cost to the organization | Zero, it is purely diagnostic | Moderate to high. Requires deliberate team restructuring, retraining, and new interaction modes | High. Requires strong, sustained leadership enforcement and can meet significant internal resistance | Low up front, but hidden cost accrues later as the org chart quietly re-asserts itself against the ideal design |
| Reliability of the resulting architecture | Not applicable, it explains, it does not produce | Reasonably reliable if the team boundaries were drawn on real domain seams, per the mirroring hypothesis's empirical support | Very reliable while the mandate is actively enforced, at risk of decay if enforcement lapses | Unreliable over time, because the design is fighting a persistent, silent organizational force |
| Best suited to | Any organization, at any point, as a first diagnostic step before choosing one of the other three approaches | Organizations already committed to a specific target architecture and willing to invest in team design as a first-class engineering artifact | Large organizations with strong central technical leadership and the authority to enforce a company-wide interface policy | Small organizations below Dunbar-scale team size, where the communication graph is dense enough that the law's effect is negligible |

## 13. Related and incompatible patterns

Conway's Law composes tightly with Team Topologies, which is best read as the
operational manual for deliberately applying the inverse Conway maneuver. Its
four team types and three interaction modes are a direct answer to the
question of what the resulting team structure should actually look like if an
organization is going to reorganize teams to shape its architecture.

It relates closely to Bounded Context from domain-driven design. A bounded
context is, in effect, a proposal for where a team's ownership and a module's
boundary should coincide, drawn from domain analysis rather than from the
existing org chart, and using it well is one of the most common ways
practitioners choose the target shape that an inverse Conway maneuver then
pulls the organization toward.

It relates to Microservices and Modular Monolith as architectural outcomes
rather than as causes. Conway's Law explains why a given organization will
tend to produce one or the other regardless of which pattern name is written
on the whiteboard, and choosing between them is partly a choice about which
organizational shape the team is willing to adopt or already has.

It relates to High Cohesion and Low Coupling at the module level. The law
essentially claims that these two familiar module-design qualities are
themselves downstream of an organizational-design quality, communication
cohesion and communication coupling between teams, which is why fixing a
low-cohesion module in isolation, without addressing the team structure that
produced it, tends not to hold.

It is not strictly incompatible with any other pattern, since it is
descriptive rather than prescriptive, but it is commonly misused in tension
with Single Responsibility Principle applied at the service level. An
architect who splits services purely to satisfy the idea of one team owning
one service, without checking whether the resulting service boundaries also
respect a genuine, cohesive responsibility, can produce services that are
Conway-aligned but functionally incoherent, which trades one problem for
another rather than solving it.

## 14. Refactoring path in and out

Introducing an inverse Conway maneuver into an organization that has not used
one before is a staged process, not a single reorg announcement.

1. Map the current state on both sides. Draw the real communication graph,
   who actually talks to whom, not the formal org chart, and the real module
   dependency graph, and overlay them, using change-coupling data from
   version control, which files change together in the same commit or pull
   request, as an objective proxy for the module graph, the same technique
   CodeScene's social network analysis automates.
2. Identify mismatches. Edges in the module graph that cross a
   high-communication-cost boundary in the org graph. These are the
   candidates for intervention, not every awkward-looking module boundary.
3. Decide, for each mismatch, on the cheapest sufficient intervention first.
   Increase communication bandwidth, shared standups, a liaison role,
   physical or timezone proximity, before considering a formal team merge or
   split.
4. For mismatches that genuinely require a structural change, define the
   target team topology explicitly, using a vocabulary such as Team
   Topologies's four team types, before moving any people, so the target is
   reviewable and not merely a reorg because of Conway's Law.
5. Execute the team change, then deliberately wait. The maneuver's mechanism
   runs through the normal, gradual interface-negotiation dynamics described
   in dimension 7, and does not produce an instant architectural change.
   Plan the review of its effect on a multi-month horizon, not a multi-week
   one.
6. Re-measure the module dependency graph after the horizon has passed and
   confirm the target boundary has actually emerged, rather than assuming
   the reorg alone was sufficient.

Removing, or more precisely, retiring, a deliberate inverse Conway
intervention is rarely a single refactoring step, because the refactoring
here is organizational, not code-level. The honest removal path is to notice
that a previously useful team split no longer earns its coordination cost,
for example because the two modules it was meant to keep separate have,
through normal evolution, become tightly coupled again for a legitimate
technical reason, and to fold the two teams back together, or change their
interaction mode from X-as-a-service to collaboration, explicitly, rather
than leaving the organizational structure stale relative to the architecture
it was built to produce.

## 15. Testing and verification

Conway's Law itself is not something a unit test verifies, because it is a
claim about the relationship between two graphs, an organizational one and a
technical one, over time. Verification is closer to an architectural fitness
function than to a conventional test.

- **Change-coupling analysis as a proxy signal.** Mine version-control
  history for files or services that are frequently modified together in the
  same commit or pull request, and treat a high change-coupling score
  between two modules owned by different teams as a signal worth
  investigating, the same underlying technique CodeScene automates
  commercially.
- **Ownership-boundary assertions.** In a monorepo, a CI check can assert
  that a given directory's CODEOWNERS entry, or an equivalent ownership
  manifest, matches the module boundary an architecture decision record
  declares for that directory, catching drift where the org has quietly
  reassigned ownership without anyone updating the intended architecture, or
  the reverse.
- **Interface staleness as an indirect signal.** An interface between two
  modules owned by the same team that has not changed in a long time is weak
  evidence of nothing in particular. An interface between two modules owned
  by different teams that has not changed in a long time, while the modules
  behind it have both changed substantially, is a candidate symptom of the
  rigid, defensively negotiated interface pattern described in dimension 7,
  and is a reasonable thing to flag in an architecture review for a human to
  investigate.
- **Post-reorg architecture review.** After deliberately applying the
  inverse Conway maneuver, the only reliable verification is re-running the
  mapping step from dimension 14 on a defined horizon, a quarter, two
  quarters, and comparing the actual resulting module dependency graph
  against the target that motivated the reorg, treating a mismatch as a
  signal to investigate rather than as proof the maneuver failed, since some
  mismatches trace to genuine technical coupling rather than to an
  incomplete organizational change.

Testing for Conway's Law is therefore about instrumenting the organization,
not the code in isolation. The code-level test suite for any individual
module behaves exactly as it would under any other architectural principle,
because the law explains why the module boundary is where it is, it does not
change how correctness is verified within that boundary.

## 16. Observability signals

Because Conway's Law is a claim about the relationship between two systems,
one social and one technical, observability signals worth tracking mix
engineering-process telemetry with more conventional code metrics. A
consciously applied inverse Conway maneuver should be able to point at these
signals as evidence it is or is not working.

- **Cross-team pull-request review latency.** A rising trend in how long a
  pull request takes to get its first review when the author and the
  reviewer are on different teams, relative to same-team review latency, is
  a leading indicator of a widening communication-cost gap that will, per
  the law, eventually harden into a more rigid interface.
- **Interface version-bump frequency by ownership pair.** Tracking how often
  a shared API's major version increments, segmented by whether the calling
  and serving teams are the same team or different teams, gives a direct,
  quantitative read on the defensiveness described in dimension 7's high-cost
  path.
- **Change-coupling heatmaps.** A file-level or service-level heatmap of
  which parts of the codebase tend to change together in the same commit,
  cross-referenced against team ownership, is the direct empirical
  approximation of whether the module graph mirrors the communication graph,
  the same measurement tools such as CodeScene's social network analysis are
  built to surface
  ([CodeScene, "How can you measure Conway's Law?"](https://codescene.com/blog/measure-conways-law/),
  verified 2026-08-02).
- **On-call escalation paths crossing team boundaries.** A rising count of
  incidents whose resolution requires paging a second team, especially when
  the paged team's on-call response time is materially slower than the
  primary team's, is an operational symptom of the same underlying
  communication-cost gap, now visible as a reliability metric rather than an
  architecture metric.
- **Meeting and channel topology.** A simple, low-tech signal. Counting how
  many recurring, cross-team meetings or shared chat channels exist per pair
  of teams that own directly dependent modules gives a coarse but honest
  measure of the current communication graph, useful as a baseline before
  and after a deliberate reorg.

A healthy state, by this lens, is one where the module dependency graph's
cross-team edges each correspond to a communication channel the org has
deliberately invested in, a defined interaction mode, a support SLA, a
recurring sync, rather than to an ad hoc, under-resourced relationship that
the architecture is quietly depending on without anyone having decided to
support it.

## 17. Security and privacy implications

Conway's Law has a real, if indirect, security and privacy implication,
chiefly through the interfaces it shapes rather than through any code-level
mechanism of its own, and this dimension is engineering judgement rather than
a sourced claim.

A module boundary that mirrors a high-friction, low-trust organizational
boundary tends to acquire the defensive validation and strict access
controls that low-trust relationships naturally produce, which is generally
a security benefit. Teams that do not fully trust each other's release
discipline tend to build stricter input validation and clearer
authentication boundaries between their systems than two engineers who share
a desk and a deploy pipeline. Conversely, a module boundary that mirrors a
low-friction, high-trust organizational boundary, for example two teams that
merged after a reorganization and now share deploy credentials or a shared
internal-only endpoint with no independent authentication, can silently
accumulate an implicit trust relationship in the software that was never
separately security-reviewed, because it grew organically from social trust
rather than from a deliberate access-control decision. When teams are later
split again, for example after a further reorganization or a divestiture, an
interface that was informally trusted because the two sides felt like one
team can be left unreviewed and under-secured even though the organizational
trust that justified the informality no longer exists. Auditing interfaces
at team boundaries after any reorganization, in either direction, for
whether their access controls still match the actual current trust
relationship between the now-separate or now-merged owning teams, is a
reasonable, targeted security-review practice that follows directly from
taking Conway's Law seriously as an organizational force.

## 18. References

1. Melvin Conway, "How Do Committees Invent?", Datamation, April 1968,
   archived with the exact quoted wording at
   [melconway.com/Home/Conways_Law.html](https://www.melconway.com/Home/Conways_Law.html),
   verified 2026-08-02.
2. Martin Fowler, "ConwaysLaw", bliki, attributing the naming of the law to
   Fred Brooks in *The Mythical Man-Month*,
   [martinfowler.com/bliki/ConwaysLaw.html](https://martinfowler.com/bliki/ConwaysLaw.html),
   verified 2026-08-02.
3. Frederick P. Brooks Jr., *The Mythical Man-Month. Essays on Software
   Engineering*, Addison-Wesley, anniversary edition, 1995, the source that
   named and popularized the observation as Conway's Law.
4. Alan MacCormack, John Rusnak, and Carliss Y. Baldwin, "Exploring the
   Duality between Product and Organizational Architectures. A Test of the
   Mirroring Hypothesis," Research Policy, volume 41, issue 8, 2012, pages
   1309 to 1324, working-paper version at
   [hbs.edu/ris](https://www.hbs.edu/ris/Publication%20Files/08-039_1861e507-1dc1-4602-85b8-90d71559d85b.pdf),
   verified 2026-08-02.
5. Matthew Skelton and Manuel Pais, *Team Topologies. Organizing Business and
   Technology Teams for Fast Flow*, IT Revolution Press, 2019.
6. Steve Yegge, internal Google memo on platform design describing Amazon's
   circa-2002 service-interface mandate under Jeff Bezos, 2011,
   course-hosted archival copy at
   [courses.cs.washington.edu/courses/cse452/23wi/papers/yegge-platform-rant.html](https://courses.cs.washington.edu/courses/cse452/23wi/papers/yegge-platform-rant.html),
   verified 2026-08-02.
7. Rachel Potvin and Josh Levenberg, "Why Google Stores Billions of Lines of
   Code in a Single Repository," Communications of the ACM, July 2016,
   [research.google/pubs/why-google-stores-billions-of-lines-of-code-in-a-single-repository](https://research.google/pubs/why-google-stores-billions-of-lines-of-code-in-a-single-repository/),
   verified 2026-08-10 (the original cacm.acm.org host now bot-blocks
   automated requests, checked directly; Google's own primary source is
   cited in its place).
8. CodeScene, "How can you measure Conway's Law?",
   [codescene.com/blog/measure-conways-law](https://codescene.com/blog/measure-conways-law/),
   verified 2026-08-02.
9. CodeScene Enterprise Documentation, "Social Networks",
   [docs.enterprise.codescene.io/versions/6.2.10/guides/social/social-networks.html](https://docs.enterprise.codescene.io/versions/6.2.10/guides/social/social-networks.html),
   verified 2026-08-02.

## Code examples

Conway's Law is an organizational principle, not an API, so there is no
single canonical function signature to implement across languages. The three
implementations below all build the same small Conway fitness function, a
tool that takes a team-ownership map and a module change-coupling graph,
mined in a real system from version-control history, and reports every
module-pair edge that crosses a low-bandwidth team boundary, which is the
concrete, checkable diagnostic described in dimension 15. Each one is a
minimal, dependency-free, runnable console program that ends by printing
every mismatch it finds.

### TypeScript

```typescript
type Team = string;
type Module = string;

interface OrgEdge {
  teamA: Team;
  teamB: Team;
  contactsPerWeek: number;
}

interface ModuleEdge {
  moduleA: Module;
  moduleB: Module;
  commitsTogether: number;
}

const ownership: Record<Module, Team> = {
  billing: "TeamA",
  ledger: "TeamB",
  search: "TeamC",
  publicApi: "TeamD",
};

const orgGraph: OrgEdge[] = [
  { teamA: "TeamA", teamB: "TeamB", contactsPerWeek: 40 },
  { teamA: "TeamC", teamB: "TeamD", contactsPerWeek: 1 },
];

const moduleGraph: ModuleEdge[] = [
  { moduleA: "billing", moduleB: "ledger", commitsTogether: 55 },
  { moduleA: "search", moduleB: "publicApi", commitsTogether: 38 },
];

function contactsFor(orgGraph: OrgEdge[], teamA: Team, teamB: Team): number {
  const edge = orgGraph.find(
    (e) =>
      (e.teamA === teamA && e.teamB === teamB) ||
      (e.teamA === teamB && e.teamB === teamA)
  );
  return edge ? edge.contactsPerWeek : 0;
}

function findMismatches(
  ownership: Record<Module, Team>,
  orgGraph: OrgEdge[],
  moduleGraph: ModuleEdge[],
  lowBandwidthThreshold: number
): string[] {
  const findings: string[] = [];
  for (const edge of moduleGraph) {
    const teamA = ownership[edge.moduleA];
    const teamB = ownership[edge.moduleB];
    if (teamA === teamB) continue;
    const contacts = contactsFor(orgGraph, teamA, teamB);
    if (contacts < lowBandwidthThreshold) {
      findings.push(
        `${edge.moduleA} <-> ${edge.moduleB}. owned by ${teamA} and ${teamB}, ` +
          `changed together ${edge.commitsTogether} times, but only ${contacts} ` +
          `contacts/week between the owning teams`
      );
    }
  }
  return findings;
}

const mismatches = findMismatches(ownership, orgGraph, moduleGraph, 5);
for (const line of mismatches) {
  console.log(line);
}
console.log(`${mismatches.length} Conway's Law mismatch(es) found`);
```

Run with `npx tsc conway.ts --outDir /tmp/conway-ts` followed by
`node /tmp/conway-ts/conway.js`. Compiled and run successfully, producing the
two expected lines, a flagged mismatch for `search <-> publicApi`, heavy code
coupling paired with one contact per week, and no mismatch for `billing <->
ledger`, heavy code coupling matched by heavy team contact.

### Python

```python
from dataclasses import dataclass


@dataclass
class OrgEdge:
    team_a: str
    team_b: str
    contacts_per_week: int


@dataclass
class ModuleEdge:
    module_a: str
    module_b: str
    commits_together: int


ownership = {
    "billing": "TeamA",
    "ledger": "TeamB",
    "search": "TeamC",
    "public_api": "TeamD",
}

org_graph = [
    OrgEdge("TeamA", "TeamB", contacts_per_week=40),
    OrgEdge("TeamC", "TeamD", contacts_per_week=1),
]

module_graph = [
    ModuleEdge("billing", "ledger", commits_together=55),
    ModuleEdge("search", "public_api", commits_together=38),
]


def contacts_for(edges: list[OrgEdge], team_a: str, team_b: str) -> int:
    for edge in edges:
        if {edge.team_a, edge.team_b} == {team_a, team_b}:
            return edge.contacts_per_week
    return 0


def find_mismatches(
    ownership: dict[str, str],
    org_graph: list[OrgEdge],
    module_graph: list[ModuleEdge],
    low_bandwidth_threshold: int,
) -> list[str]:
    findings = []
    for edge in module_graph:
        team_a = ownership[edge.module_a]
        team_b = ownership[edge.module_b]
        if team_a == team_b:
            continue
        contacts = contacts_for(org_graph, team_a, team_b)
        if contacts < low_bandwidth_threshold:
            findings.append(
                f"{edge.module_a} <-> {edge.module_b}. owned by {team_a} and "
                f"{team_b}, changed together {edge.commits_together} times, "
                f"but only {contacts} contacts/week between the owning teams"
            )
    return findings


if __name__ == "__main__":
    mismatches = find_mismatches(ownership, org_graph, module_graph, low_bandwidth_threshold=5)
    for line in mismatches:
        print(line)
    print(f"{len(mismatches)} Conway's Law mismatch(es) found")
```

Run with `python3 conway.py`. Produces the same two-line result as the
TypeScript version, one flagged mismatch for `search <-> public_api` and
none for `billing <-> ledger`.

### Go

```go
package main

import "fmt"

type orgEdge struct {
	teamA           string
	teamB           string
	contactsPerWeek int
}

type moduleEdge struct {
	moduleA         string
	moduleB         string
	commitsTogether int
}

func contactsFor(edges []orgEdge, teamA, teamB string) int {
	for _, e := range edges {
		if (e.teamA == teamA && e.teamB == teamB) || (e.teamA == teamB && e.teamB == teamA) {
			return e.contactsPerWeek
		}
	}
	return 0
}

func findMismatches(
	ownership map[string]string,
	orgGraph []orgEdge,
	moduleGraph []moduleEdge,
	lowBandwidthThreshold int,
) []string {
	var findings []string
	for _, edge := range moduleGraph {
		teamA := ownership[edge.moduleA]
		teamB := ownership[edge.moduleB]
		if teamA == teamB {
			continue
		}
		contacts := contactsFor(orgGraph, teamA, teamB)
		if contacts < lowBandwidthThreshold {
			findings = append(findings, fmt.Sprintf(
				"%s <-> %s. owned by %s and %s, changed together %d times, "+
					"but only %d contacts/week between the owning teams",
				edge.moduleA, edge.moduleB, teamA, teamB, edge.commitsTogether, contacts,
			))
		}
	}
	return findings
}

func main() {
	ownership := map[string]string{
		"billing":   "TeamA",
		"ledger":    "TeamB",
		"search":    "TeamC",
		"publicApi": "TeamD",
	}

	orgGraph := []orgEdge{
		{teamA: "TeamA", teamB: "TeamB", contactsPerWeek: 40},
		{teamA: "TeamC", teamB: "TeamD", contactsPerWeek: 1},
	}

	moduleGraph := []moduleEdge{
		{moduleA: "billing", moduleB: "ledger", commitsTogether: 55},
		{moduleA: "search", moduleB: "publicApi", commitsTogether: 38},
	}

	mismatches := findMismatches(ownership, orgGraph, moduleGraph, 5)
	for _, line := range mismatches {
		fmt.Println(line)
	}
	fmt.Printf("%d Conway's Law mismatch(es) found\n", len(mismatches))
}
```

Run with `go run conway.go`. Produces the same result as the other two, one
flagged mismatch for `search <-> publicApi`, none for `billing <->
ledger`. Java, Rust, and Swift were not chosen for this entry because a
small graph diagnostic like this one does not exercise any language-specific
idiom that changes the shape of the pattern, and three languages already
demonstrate that the underlying fitness function is a plain, portable
data-processing routine with nothing language-specific about it, consistent
with dimension 8's point that empirical measurement tooling for Conway's Law
is a general-purpose data analysis problem rather than a language-bound one.
