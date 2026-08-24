---
name: Context Map
slug: context-map
family: 11-domain-driven-design
category: Strategic Design
aliases: [Bounded Context Map, Context Mapping]
first_described: "Evans 2003"
maturity: canonical
related: [bounded-context, anticorruption-layer, shared-kernel, published-language, open-host-service, customer-supplier, conformist]
incompatible_with: []
verified: 2026-08-02
---

## 1. Name, aliases, and lineage

The canonical name is Context Map. Eric Evans introduced it in "Domain-Driven
Design. Tackling Complexity in the Heart of Software" (Addison-Wesley, 2003),
in Part IV, chapter 14, "Maintaining Model Integrity." The chapter frames the
problem this way, a single unified model across a large system is a myth once
more than one team is involved, so the honest response is to accept that
several models coexist, draw the boundary of each explicitly as a Bounded
Context, and then draw a second diagram, a map, showing how those contexts
relate to each other and translate between their models. Evans calls this
second diagram the Context Map, and the accompanying document, listing every
context and how it is connected, the Context Map document.

The term is sometimes used loosely to mean any diagram of a system's modules
or services, but in Domain-Driven Design usage it has a specific meaning, it
is a map of Bounded Contexts and the relationships between them, not a map of
deployable services or of database schemas, and not an org chart. A service
map and a context map can look similar on paper, and in a well-run
microservices system they often do line up one-to-one, but they answer
different questions. A service map answers where the code runs and how it
gets deployed. A context map answers where a word means this thing, and what
happens at the seam where a different team's word for the same concept, or
the same word for a different concept, meets ours.

Vaughn Vernon's "Implementing Domain-Driven Design" (Addison-Wesley, 2013),
chapter 3, "Context Maps," restates and extends the pattern with the same
core relationship vocabulary Evans used, and adds a sharper emphasis on
drawing the map early, during strategic design, before tactical modeling
inside any single context begins. The DDD community reference maintained by
Evans and commonly cited as the "DDD Reference," a companion document Evans
published alongside the 2003 book summarizing the pattern language and
available at domainlanguage.com, also lists Context Map as the summary
artifact of the strategic design patterns, Bounded Context, Continuous
Integration, Context Map, Shared Kernel, Customer-Supplier Development
Teams, Conformist, Anticorruption Layer, Separate Ways, Open Host Service,
and Published Language, with Partnership and Big Ball of Mud as a context
relationship added later, chiefly through Vernon's writing and community
usage. This entry treats Context Map as the parent artifact and describes
the individual relationship types, Shared Kernel, Customer-Supplier,
Conformist, Anticorruption Layer, Open Host Service, Published Language,
Partnership, Separate Ways, as the edges that populate it. Several of those
relationship types have, or will have, their own entries in this repository,
cross-referenced below, and this entry does not attempt to duplicate their
full individual treatment.

## 2. Problem and context

A system reaches a certain size and a certain number of contributing teams
before a single, internally consistent domain model stops being achievable.
Evans states this directly in DDD chapter 14. Large projects, in practice,
end up with multiple models, whether the team plans for it or not, because
different subteams evolve their own working vocabulary under time pressure,
because a system absorbs a legacy component nobody has the appetite to
rewrite, because an acquired company brings its own database and its own
meaning for "customer," or because a third-party system is integrated and
its model cannot be changed at all. The dangerous outcome is not that
multiple models exist, that is close to inevitable. The dangerous outcome is
that the team pretends a single model exists when it does not, and lets the
seams between models blur together undocumented and unmanaged. Evans's
phrase for the resulting mess is a "muddy" system where a term drifts in
meaning as code is read across module boundaries and nobody can say with
confidence which meaning is in force at a given point.

The concrete symptom a reader will recognize from their own codebase, a class
named `Customer` is passed between the billing subsystem and the support
subsystem, and both subsystems edit it, but "customer" in billing means "a
legal entity with a payment method and an outstanding balance" while
"customer" in support means "a person who has ever opened a ticket,
regardless of billing status." A field gets added to satisfy one subsystem's
need, gets silently misused or left null by the other, and eventually
somebody adds an `isBillingCustomer` boolean flag to disambiguate, which is
the code admitting, without anyone deciding it on purpose, that two models
were forced to share one class. Context Map is the pattern for making that
decision on purpose. Name each model's boundary as a Bounded Context, decide
explicitly what kind of relationship exists between any two contexts that
must communicate, and draw the whole arrangement so every team can see where
the seams are and what obligations each side has at each seam.

The context in which Context Map applies is specifically strategic, systemic
design, the level above any single context's internal class design. It is
drawn before, and continues to be maintained during, work that touches more
than one Bounded Context. A single-context project with one team and one
database has nothing to map, because there is only one model and the pattern
has no work to do.

## 3. Forces

The primary force is honesty about organizational and cognitive reality
against the appeal of a single unified model. A single model is cheaper to
reason about locally, one word means one thing everywhere, but Conway's Law,
Melvin Conway, "How Do Committees Invent?," Datamation, April 1968, the paper
that first stated that a system's design tends to mirror the communication
structure of the organization that produces it, means that once more than
one team owns more than one part of a system, forcing a single model
requires either constant cross-team synchronization overhead or one team's
authority over the others' vocabulary, and both costs grow with team count.
Context Map trades local simplicity, any code inside a context can assume
its own model is universally true, for an explicit, visible translation cost
at every seam, in exchange for letting each team move fast inside its own
boundary without waiting on cross-team model agreement.

A second force is integration cost against isolation cost. A tightly
coupled relationship between two contexts, Shared Kernel or Conformist, is
cheap to build initially, there is little or no translation code, but it
couples the two contexts' release rhythm and internal changes together,
sometimes tightly enough that neither team can refactor without breaking
the other. A loosely coupled relationship, Anticorruption Layer or Open
Host Service with a Published Language, costs more upfront translation
code and ongoing maintenance of that translation, but buys each side
genuine autonomy to evolve its internal model without a cross-team
negotiation for every change. The map exists precisely to make this trade a
conscious per-edge decision instead of an accident of whichever integration
approach a developer reached for first.

A third force, less discussed by Evans but explicit in later community
writing including Vernon 2013 chapter 3 and in numerous conference talks on
strategic DDD, is that the map itself has a cost of upkeep. It can drift out
of date the moment a relationship changes and nobody redraws it, so there is
a genuine trade between the value of a shared, current picture and the
discipline cost of keeping that picture current. Evans favors keeping the
document, imperfect and occasionally stale, over having no shared artifact
at all, on the reasoning that even an out-of-date map that is roughly right
is better than a team having no shared vocabulary for discussing integration
seams.

A fourth force is political, and Evans names it directly in DDD chapter 14
under the organizational patterns adjacent to the Context Map discussion.
Drawing a Customer-Supplier or Conformist relationship on the map is a
statement about which team has authority over a shared concept, and making
that authority explicit can surface, rather than paper over, an
organizational power imbalance or disagreement that was previously left
implicit. The pattern favors explicitness over comfort here. A map that
avoids naming an uncomfortable Conformist relationship because a team
objects to admitting it defeats the purpose of the pattern.

## 4. Applicability and non-applicability

Reach for a Context Map when a system spans more than one team, more than
one subdomain with genuinely different vocabularies, an integration with a
third-party or acquired system whose model cannot be unified with yours, a
migration in progress where legacy and new systems must coexist and
communicate, or a microservices architecture where each service is intended
to own its own model. It is applicable specifically at the moment more than
one Bounded Context needs to exchange data or behavior, because that
exchange point is exactly what the map exists to document and manage. It is
also applicable earlier than most teams reach for it. Vernon 2013 explicitly
argues for drawing an initial map during early strategic design sessions,
before code exists, as a way to surface where organizational seams will fall
and to negotiate relationship types while the cost of changing them is still
low.

Do not reach for a Context Map when the system genuinely has a single team
and a single coherent model, because there is nothing to map and drawing one
manufactures an artifact with no seams to document, pure overhead. Do not
reach for it as a substitute for defining Bounded Contexts in the first
place. A Context Map without well-considered Bounded Context boundaries is a
map of accidental module boundaries, not intentional model boundaries, and
will mislead more than it helps. Do not use it to model deployment topology,
network paths, or infrastructure, that is the job of an architecture or
deployment diagram, and conflating the two produces a document nobody trusts
for either purpose, because a service map changes with every infrastructure
decision while a context map should be comparatively stable, changing only
when a model's ownership or a relationship's kind genuinely changes. Do not
draw a Context Map at a granularity finer than Bounded Context, mapping
relationships between individual classes or modules inside one context is
tactical design, not strategic design, and belongs in a different artifact,
a class diagram or a dependency graph, entirely. Finally, do not treat an
initial Context Map as fixed. Teams that draw the map once and never revisit
it as the system evolves end up with a document that actively misleads,
which is worse than no document, because it carries false authority.

## 5. Structure

The Context Map has two participant kinds, Bounded Contexts, the nodes, and
Context Relationships, the labeled edges between them.

A Bounded Context is the explicit boundary within which a particular domain
model is defined and consistent. Evans, DDD 2003, chapter 14, "Bounded
Context," it is where a specific model applies, and it usually corresponds
to a part of the organization, though the correspondence is not guaranteed
to be exact. On the map it is drawn as a labeled region or box, named with
the subdomain or team it represents, for example "Billing," "Support,"
"Legacy Order System," "Payment Gateway, third party."

A Context Relationship is a labeled edge connecting two Bounded Contexts,
describing both the direction of influence, which context's model is
authoritative for a shared concept, or whether both evolve as equals, and
the mechanism by which the two contexts translate between their models
where they touch. The canonical relationship kinds, as named by Evans and
extended by Vernon, are as follows.

- Shared Kernel. Two contexts deliberately share a subset of the model, a
  shared code library or shared schema segment, owned jointly, changed only
  by agreement between both teams.
- Customer-Supplier Development Teams. The upstream context, the supplier,
  provides a service or model the downstream context, the customer, depends
  on, and the downstream team has planning input into the upstream team's
  future work because the downstream team's needs are treated as a
  first-class input, not an afterthought.
- Conformist. The downstream context has no negotiating power over the
  upstream model, a large external vendor, an internal team unwilling to
  accommodate requests, and simply adopts the upstream model as its own,
  translating nothing.
- Anticorruption Layer, ACL. The downstream context builds an explicit
  translation layer that converts the upstream model into the downstream
  context's own model at the boundary, protecting the downstream model's
  integrity from the upstream context's concepts leaking in.
- Open Host Service, OHS. The upstream context exposes a well-defined,
  documented protocol or API intended for consumption by multiple downstream
  contexts, rather than negotiating a bespoke integration with each one.
- Published Language. A well-documented shared interchange format, a
  schema, an API contract, a document format, used for translation at a
  boundary, frequently paired with Open Host Service.
- Partnership. Two teams have a mutual dependency and succeed or fail
  together, so they coordinate releases and future plans cooperatively, as
  equals, with neither side purely upstream or downstream.
- Separate Ways. Two contexts have no real relationship worth
  integrating, and the deliberate decision is to build no connection between
  them at all, even where a naive analysis might suggest overlap.
- Big Ball of Mud. Named on the map, per Vernon 2013, as an honest label for
  an existing region of the system with no coherent internal model at all,
  so that the boundary of the mess is at least drawn and contained rather
  than left unbounded and spreading.

On the diagram, an edge is usually annotated with U, upstream, and D,
downstream, markers at each end to show the direction of model authority,
following the U and D notation Vernon popularizes in "Implementing
Domain-Driven Design," 2013, chapter 3, in the section covering the Context
Map figures.

## 6. ASCII structure diagram

```
+-----------------------------------+
| Billing Context (Sales subdomain) |
+-----------------------------------+
           | Conformist, U/D, D: no negotiation
           v
+-----------------------------------------+
| Payment Gateway (third-party, upstream) |
+-----------------------------------------+

+-------------------------------------+
| Support Context (Support subdomain) |
+-------------------------------------+
           ^
           | Open Host Service, U: exposes stable
           | API contract
+---------------------------------------------+
| Published Lang. (shared JSON ticket schema) |
+---------------------------------------------+

Billing -> Support: Anticorruption Layer, D: Billing
owns translation.

+-----------------------------------+
| Identity Context (Core subdomain) |
+-----------------------------------+
           ^
           | Conformist, D: no negotiation
+------------------------------------------------+
| Legacy Order System (upstream, no negotiation) |
+------------------------------------------------+

Support -> Identity: Shared Kernel (jointly owned
"Account" module).

+---------------------------------------------+
| Marketing Analytics (no integration needed) |
+---------------------------------------------+
           . Separate Ways, no connection drawn
+-----------------+
| Support Context |
+-----------------+
```

## 7. Dynamics

The Context Map itself is not a runtime artifact, it describes design-time
and organizational structure, so dynamics here means how the relationships
on the map play out over the life of a change that crosses a context
boundary, and, separately, how the map itself evolves through a team's
process.

At a boundary governed by an Anticorruption Layer, a request or event
originating in the upstream context arrives in a foreign shape, is
intercepted by the ACL, which translates every field and every concept into
the downstream context's own vocabulary before anything downstream of the
ACL ever sees the foreign model, and any response flowing back is
translated in the reverse direction at the same seam. The translation logic
lives entirely in the ACL, is owned by the downstream team, and downstream
code never imports or references upstream types directly.

At a boundary governed by Open Host Service plus Published Language, the
upstream context exposes one stable, versioned interface, the OHS, described
by a shared, documented schema, the Published Language, and every
downstream consumer, however many there are, talks to that one interface
rather than negotiating a bespoke integration each. A change to the
upstream context's internal model does not force a change to any downstream
consumer as long as the published interface's contract is preserved, which
is the entire point of separating the OHS's public shape from the upstream
team's internal implementation.

At a Shared Kernel boundary, both teams read and write the same shared code
or shared schema segment directly, with no translation step at all, and any
change to that shared segment requires explicit coordination and agreement
between both teams before it ships, because an uncoordinated change breaks
the other side immediately with no translation layer to absorb the drift.

The map's own life cycle, drawn from Vernon 2013 chapter 3 and widely echoed
in strategic-DDD workshop practice, notably the context mapping facilitation
technique popularized by Alberto Brandolini's EventStorming practice,
described in Brandolini's book "Introducing EventStorming," Leanpub, 2021,
in the chapter on strategic design, usually runs as follows. A team draws
or redraws the map during a dedicated strategic design session, usually a
workshop with representatives from every affected context present, because a
map drawn by one team in isolation tends to misrepresent the other side's
actual constraints and authority. The map is revisited whenever a new
context is introduced, an existing relationship's kind changes, for example
a Conformist relationship is renegotiated into a Customer-Supplier
relationship once the downstream team gains planning influence, or a
context is retired.

## 8. Implementation variants

The map itself has no single canonical implementation format, and DDD
literature deliberately treats it as a communication artifact first. Common
concrete forms in practice are as follows.

- A whiteboard or sticky-note diagram produced live in a workshop,
  photographed and archived, valuable chiefly for the shared understanding
  built during the drawing session itself rather than for the artifact's
  long-term precision.
- A diagram maintained in a drawing tool, draw.io, Miro, Lucidchart, and
  kept under version control alongside the codebase or in a linked design
  document, so the diagram's history is inspectable and the diagram can be
  embedded in onboarding documentation.
- A text-based, version-controlled document, a markdown table or a short
  written description per relationship, favored by teams that want the map
  to live in the same repository and pull-request workflow as the code it
  describes, so a relationship change is reviewed the same way a code change
  is reviewed.
- Context Mapper, contextmapper.org, an open-source, textual domain-specific
  language and toolchain built on Eclipse Xtext, specifically for authoring
  Context Maps as code, capable of generating PlantUML diagrams from the
  textual definition and of validating a map's structure, per the Context
  Mapper project documentation, verified 2026-08-02. This is the closest
  thing DDD tooling has to a formal, machine-checkable Context Map format,
  and it lets a team express, in a structured file, each Bounded Context,
  each relationship kind, and the U and D direction, then regenerate the
  diagram whenever the file changes, avoiding the drift problem that
  afflicts hand-maintained diagrams.
- An implicit map inferred from the actual integration code and API
  contracts a codebase already contains, produced by static analysis of
  import graphs and cross-service API calls, useful as a reality check
  against a hand-drawn map that may have drifted, though this variant
  cannot recover the intended direction of authority or the reasoning
  behind a relationship choice, only the fact that a connection exists.

## 9. Known production uses

Netflix's engineering organization has published, through its technology
blog, descriptions of how domain-driven Bounded Context boundaries and
explicit context relationships, particularly Anticorruption Layer and Open
Host Service style API gateways, inform the separation between its many
independently owned microservices, discussed for example in "Engineering
Trade-Offs and The Netflix API Re-Architecture," Netflix Technology Blog,
https://netflixtechblog.com/engineering-trade-offs-and-the-netflix-api-re-architecture-a209f9e422c0,
verified 2026-08-02, which describes the API layer's role as an explicit
translation boundary between internal service models and external client
needs, the same shape as an Open Host Service with a Published Language
sitting in front of many internal Bounded Contexts.

Amazon's internal engineering culture is documented, in Werner Vogels's own
writing and in numerous derivative case studies, as organizing services
around explicit, team-owned boundaries with well-defined APIs at the seams,
formalized publicly through the two-pizza team and API-first mandate
described by Vogels in "A Conversation with Werner Vogels," ACM Queue, 2006,
https://queue.acm.org/detail.cfm?id=1142065, verified 2026-08-02, which
recounts the internal mandate that every team expose its functionality only
through a service interface, never through direct database access, the
structural precondition for treating each team's service as a Bounded
Context with an Open Host Service boundary rather than a Shared Kernel.

Vaughn Vernon's "Implementing Domain-Driven Design," Addison-Wesley, 2013,
chapter 3, documents a full worked Context Map for a fictional but
representative SaaS product-management and identity-and-access-management
system used throughout the book's examples, showing Partnership,
Customer-Supplier, Conformist, and Shared Kernel relationships between the
Identity and Access, Collaboration, and Agile Project Management Bounded
Contexts the book builds in subsequent chapters, and this worked example is
one of the most widely cited concrete illustrations of the pattern in the
DDD practitioner community.

Zalando's engineering organization documents its own API-design and team
boundary practices in the publicly available "Zalando RESTful API and Event
Guidelines," https://opensource.zalando.com/restful-api-guidelines/,
verified 2026-08-02, which mandates that every team-owned API be treated as
a Published Language contract with its own stability and versioning
obligations toward downstream consumers, and the guidelines explicitly cite
Domain-Driven Design's Bounded Context concept as the organizing principle
behind which team owns which API surface, a direct production instance of
the Open Host Service plus Published Language relationship pair from the
Context Map vocabulary.

## 10. Consequences

Positive. Making integration relationships explicit surfaces coupling and
translation cost that would otherwise be invisible, letting a team make a
conscious trade rather than discovering the cost only after a painful
production incident. It gives teams a shared vocabulary for discussing
integration seams, Shared Kernel, Conformist, ACL, and so on are terms a
team can say in a planning meeting and both sides understand precisely what
is being proposed, which reduces the ambiguity that otherwise surrounds a
phrase like "we will simply integrate with their API." It documents
organizational power dynamics honestly, a Conformist relationship named on
the map is a team admitting, in writing, that it has no negotiating power
over an upstream dependency, which can be uncomfortable but is more useful
than the same reality staying implicit and undiscussed. It supports
incremental migration, because a legacy system can be named as its own
Bounded Context with a Conformist or ACL relationship to the new system,
giving a migration team a concrete boundary to work against instead of an
undifferentiated legacy mass. It is cheap to produce relative to the
insight it buys, a whiteboard session costs an afternoon and usually
prevents months of accidental model coupling.

Negative. The map can go stale the moment a relationship changes and nobody
updates the diagram, and a stale map that still looks authoritative is
actively misleading, arguably worse than no map, because a reader trusts it
without verifying it against the current code. It requires genuine
cross-team participation to be accurate, a map drawn unilaterally by one
team about a relationship it shares with another team routinely
misrepresents the other team's actual constraints or intentions, producing a
document that looks authoritative but is wrong. It has no enforcement
mechanism by itself, nothing in most implementations of the pattern
prevents a developer from quietly building a tighter coupling than the map
declares, for example reaching directly into another context's database
instead of going through the documented Open Host Service, so the map's
accuracy depends entirely on process discipline rather than a technical
guardrail, unless a team pairs it with architectural fitness functions or
import-boundary linting to enforce what the map claims. Drawing the map, and
negotiating relationship kinds across teams, is itself a real time cost, and
on a small system with few integration points that cost may exceed the
value the map returns.

## 11. Failure modes and misuse

The diagram in the team wiki shows a clean Anticorruption Layer between two
contexts, but a code review finds a service in the protected downstream
context importing a class directly from the upstream context's package,
that is the observable symptom. The cause is that the map was drawn once,
during an initial design session, and never enforced by any technical or
process guardrail afterward, so individual engineers under deadline
pressure took the path of least resistance and bypassed the translation
layer the map claims exists. The fix is to pair the map with an enforced
module or import boundary, a build-time dependency-direction check, a
linter rule, or a monorepo package-visibility rule, so a violation of the
documented relationship fails the build rather than merely contradicting a
diagram nobody is actively checking against.

Two teams both believe they are the upstream, authoritative side of a
Customer-Supplier relationship, and each ships a change assuming the other
side will adapt to it, producing a production incident where both sides'
assumptions about who adapts to whom turn out to be wrong simultaneously,
that is the observable symptom. The cause is that the relationship was
documented, or believed to be documented, by only one team, without the
other team's explicit agreement, so the map reflects one side's aspiration
rather than a mutually negotiated reality. The fix is to treat every
relationship on the map as requiring sign-off from both connected teams
before it is considered final, and to revisit the map in a joint session,
not a single-team session, whenever a relationship's direction is in
question.

The map has grown to show dozens of contexts and a dense web of
relationships that nobody can read at a glance, and new team members report
that the map is more confusing than helpful, that is the observable
symptom. The cause is that the map was drawn at too fine a granularity,
treating every microservice or every module as its own Bounded Context
rather than grouping services that genuinely share one model under a single
context boundary, which inflates the node count without adding real
insight. The fix is to re-derive Bounded Context boundaries from actual
model boundaries, whether a shared term like "Order" means one consistent
thing, rather than from deployment units, and to merge nodes that share one
coherent model even if they are deployed as separate services.

A Shared Kernel between two teams keeps breaking one side whenever the
other side changes it, and the two teams increasingly avoid touching the
shared code at all, letting it stagnate, that is the observable symptom.
The cause is that Shared Kernel was chosen for convenience, it seemed
easier to share the code directly, without the ongoing coordination
discipline the relationship genuinely requires, since any change needs
both teams' agreement before it ships, so the relationship's real cost was
underestimated at the time it was chosen. The fix is to either invest in
the coordination process the Shared Kernel relationship demands, a shared
review gate, a shared test suite both teams must keep green, or to
renegotiate the relationship into an Open Host Service with a Published
Language so each side regains the ability to change its own internals
without coordinating every change with the other team.

## 12. Trade-off matrix

Comparing the named context-relationship choices against each other, since
the map's real decisions live at this level, not in the existence of the
map itself.

| Relationship | Coupling | Translation cost | Autonomy for downstream | Autonomy for upstream | Best fit |
|---|---|---|---|---|---|
| Shared Kernel | Highest, both sides read and write same code | Lowest, no translation exists | Low, changes need mutual agreement | Low, changes need mutual agreement | Two teams with closely aligned goals and high trust, willing to coordinate release timing |
| Customer-Supplier | Medium, downstream has planning input | Low to medium, upstream designs with downstream needs in mind | Medium, downstream can request changes | High, upstream still leads design but must consider downstream | Internal teams where downstream's needs matter to the org, but upstream leads |
| Conformist | Low coupling in code, high in vocabulary | Zero, downstream adopts upstream model wholesale | Very low, no ability to influence upstream | Very high, upstream owes nothing to downstream | An external vendor or dominant internal team with no willingness to accommodate requests |
| Anticorruption Layer | Low, isolated at the ACL boundary | High, full translation logic must be written and maintained | High, downstream model stays clean regardless of upstream changes | High, upstream is unaffected by downstream's internal model | Legacy integration, third-party system, or any upstream whose model you must not let leak in |
| Open Host Service plus Published Language | Low, many consumers share one stable contract | Medium, translation cost paid once at the published boundary, not per consumer | High, each consumer adapts to a stable, documented contract | High, upstream can change internals as long as the published contract holds | Many-to-one integration, a service consumed by several downstream contexts |
| Partnership | Medium to high, mutual dependency by design | Varies, depends on the shared interface | Medium, coordinated as equals | Medium, coordinated as equals | Two teams whose features genuinely succeed or fail together |
| Separate Ways | None | None | Full, complete independence | Full, complete independence | Two contexts with no real overlap worth the integration cost |

## 13. Related and incompatible patterns

Bounded Context is the prerequisite the Context Map depends on entirely, the
map has nothing to draw until Bounded Context boundaries have been decided,
so in practice a team defines Bounded Contexts and draws the Context Map in
the same strategic design activity, often iterating between the two as
drawing the map's relationships reveals that a proposed context boundary was
drawn in the wrong place.

Anticorruption Layer, Shared Kernel, Open Host Service, Published Language,
Customer-Supplier, Conformist, Partnership, and Separate Ways are the
individual relationship-type patterns that populate the edges of a Context
Map, each with its own more detailed tactical and organizational treatment,
several have or will have their own entries in this repository, and this
entry is the parent artifact that names, connects, and situates them
relative to each other rather than exhaustively re-describing each one.

Ubiquitous Language, Evans, DDD 2003, chapter 2, is the concept a Bounded
Context exists to protect. The Context Map is what happens when two
different Ubiquitous Languages meet at a boundary, and every relationship
type on the map is, at root, a strategy for handling that meeting,
either by unifying the languages through Shared Kernel, by one side
adopting the other's language wholesale through Conformist, or by explicit
translation at the seam through ACL or Published Language.

Hexagonal Architecture, Alistair Cockburn's Ports and Adapters, 2005, and
Onion Architecture share the Anticorruption Layer's core idea, external
concerns are kept out of the domain core through an explicit adapter layer,
and it is common in practice for a codebase's ACL to be implemented as a
set of hexagonal-style adapters at the context's boundary, so the two
patterns compose naturally rather than compete.

Microservices architecture is commonly, though not necessarily, aligned
one-to-one with Bounded Contexts, and when it is, the service dependency
graph and the Context Map tend to converge, but they are not the same
diagram, and treating a service dependency graph as automatically a valid
Context Map is a common source of confusion, since a service graph does not
by itself say which side is upstream, what kind of translation exists at
the boundary, or whether the relationship was a deliberate choice or an
accident.

Big Ball of Mud, as an architectural anti-pattern, Brian Foote and Joseph
Yoder, "Big Ball of Mud," in Pattern Languages of Program Design 4,
Addison-Wesley, 1999, is not incompatible with the Context Map, it is
explicitly nameable as a relationship or region label on the map, per
Vernon's usage, precisely so that a genuinely unstructured legacy region
can be bounded and contained rather than left to spread unacknowledged.
There is no named context relationship type in DDD literature that is
described as strictly incompatible with another, since any two contexts can,
in principle, be connected by any relationship kind, though certain
pairings are rarely sensible in practice, for example combining Shared
Kernel with a genuinely adversarial or low-trust team relationship tends to
fail for the organizational reasons described in section 11, not because
the pattern combination is technically disallowed.

## 14. Refactoring path in and out

Introducing a Context Map into a codebase that lacks one runs as follows.
First, identify the terms that carry ambiguous or conflicting meaning across
the codebase, the "Customer means two different things in billing and
support" signal from section 2, usually by walking through the domain
vocabulary with representatives from each affected team and noting every
place a shared term's meaning diverges. Second, draw a first-pass boundary
around each coherent model, naming each boundary a Bounded Context, usually
aligning loosely with existing team or module boundaries as a starting
hypothesis rather than a final answer. Third, for every pair of contexts
that currently exchange data or calls, ask which side currently has
authority over the shared concept and how translation, if any, currently
happens in code, usually revealing that an undeclared Conformist
relationship or an ad hoc, partial translation already exists informally.
Fourth, decide, with both teams present, whether the existing informal
relationship is the right one going forward or should be renegotiated, and
label the edge on the map with the agreed relationship kind. Fifth, where
the map reveals a relationship that does not match the code, for example
the map says Anticorruption Layer but the code has direct cross-context
imports, schedule the concrete refactoring, usually extracting an
explicit translation layer at the boundary, as its own piece of work, since
drawing the map does not by itself change the code.

Removing or simplifying a relationship when it stops earning its place runs
as follows. A Shared Kernel that has become a source of constant
coordination friction is usually refactored toward Open Host Service,
first by identifying which parts of the shared kernel each side actually
needs from the other, second by having the upstream side wrap that need in
a stable, published interface, third by having the downstream side switch
from direct references into the shared code to calls against the new
interface, and finally by shrinking or removing the shared kernel once
nothing depends on it directly. A Conformist relationship that has become
organizationally unnecessary, for instance because the downstream team has
gained the standing to negotiate changes with the upstream team, is
renegotiated into a Customer-Supplier relationship by establishing an
explicit process, a shared backlog, a regular planning sync, through which
downstream requirements reach the upstream team's future work, a purely
organizational change that may require no code change at all, only a
change in process and in the label drawn on the map.

## 15. Testing and verification

The Context Map itself is not directly unit-testable, since it is a design
artifact rather than executable code, but the relationships it documents
translate into concrete, testable obligations at each boundary. An
Anticorruption Layer is tested with contract-style unit tests asserting
that every field and edge case of the upstream model is correctly
translated into the downstream model, including null, missing, and
malformed upstream data, since the ACL is precisely the place a system must
degrade gracefully when the upstream side sends something unexpected. An
Open Host Service boundary is tested with consumer-driven contract tests,
the Pact framework, https://docs.pact.io/, verified 2026-08-02, is the most
widely used tool for this, in which each downstream consumer publishes the
exact shape of request and response it depends on, and the upstream
provider's test suite verifies, on every change, that it still satisfies
every published consumer contract before deploying, catching a breaking
change to the Published Language before it reaches production rather than
after a downstream consumer breaks. A Shared Kernel is tested by running
both teams' test suites against the same shared code in continuous
integration, so a change to the shared kernel that breaks either side's
assumptions is caught immediately in the pull request that introduces it,
rather than discovered later by the other team.

Verifying that the map itself remains accurate is a separate, harder
concern. Import-boundary or dependency-direction static analysis, for
example ArchUnit for Java, https://www.archunit.org/, verified 2026-08-02,
or equivalent module-boundary linters in other languages, can assert that
a context claimed to be protected by an Anticorruption Layer never imports
another context's internal types directly, converting the map's claim
about a relationship kind into an automatically enforced build-time check
rather than a diagram nobody actively verifies.

## 16. Observability signals

The map is not itself something a running system emits telemetry about, but
the health of the relationships it documents shows up in concrete,
monitorable signals. Consumer-driven contract test results, tracked per
downstream consumer against a given upstream Open Host Service, are a
leading indicator, a contract test starting to fail in CI is the earliest
possible signal that a relationship documented as stable is about to break
in production. Deploy coupling, measured as how often a change to context A's
release forces an unplanned, same-week change to context B, is a strong
signal that a relationship documented as loosely coupled, ACL or OHS, is
behaving, in practice, like a tightly coupled one, Shared Kernel or an
undeclared direct dependency, and a rising trend in this metric over time is
a sign the map no longer matches reality. Translation error rates at an
Anticorruption Layer, tracked as a metric on the ACL's translation function,
a count of upstream payloads that fail to map cleanly into the downstream
model, are a direct signal of upstream model drift, since an ACL's whole
purpose is absorbing upstream change, so a rising translation error rate
means the upstream side is changing faster or more unpredictably than the
ACL currently accommodates. Cross-context database or code access, detected
through the same static-analysis import-boundary tooling used for
verification in section 15, is the sharpest observability signal available
for detecting undocumented, informal coupling that the map does not, yet,
reflect, a rising count of such violations over time is a warning that the
map has fallen behind the code.

## 17. Security and privacy implications

The following analysis is engineering reasoning applied to the pattern, not
a sourced claim about a specific documented incident, and is labeled as
such per this repository's judgement-versus-sourced-claim convention. A
well-drawn Context Map, and specifically a rigorously applied
Anticorruption Layer, is a natural place to enforce a data-minimization
boundary, since the ACL already sits at every point where data crosses from
an upstream model into a downstream one, it is a convenient, already-existing
chokepoint at which to strip or mask fields the downstream context has no
legitimate need to hold, which matters for regulatory obligations such as
GDPR's data-minimization principle. By contrast, a Shared Kernel or a
Conformist relationship, precisely because they involve no translation
boundary, provide no natural chokepoint at which to apply such
minimization, so a system with sensitive data flowing through a Shared
Kernel or a Conformist relationship needs a separate, explicit
access-control or data-classification mechanism, since the relationship
pattern itself offers none.

A second implication concerns trust boundaries in the security sense. An
upstream Conformist relationship, by definition, means the downstream
context trusts the upstream context's model and data without independent
validation or translation, which is appropriate when the upstream side is a
trusted internal system but is a real security concern when the
upstream side is external or lower-trust, since a Conformist relationship
offers no natural place to apply input validation, sanitization, or
authorization checks the way an ACL's translation step does. Teams choosing
Conformist toward an external or lower-trust upstream context should
recognize that they are also, implicitly, choosing to trust that context's
data without an independent validation layer, and should weigh that trust
decision explicitly rather than as a side effect of choosing Conformist
purely for convenience.

## 18. References

- Evans, Eric. "Domain-Driven Design. Tackling Complexity in the Heart of
  Software." Addison-Wesley, 2003. Part IV, chapter 14, "Maintaining Model
  Integrity" (Bounded Context, Context Map, Continuous Integration, Shared
  Kernel, Customer-Supplier Development Teams, Conformist, Anticorruption
  Layer, Separate Ways, Open Host Service, Published Language). Chapter 2
  for Ubiquitous Language.
- Evans, Eric. "Domain-Driven Design Reference. Definitions and Pattern
  Summaries." domainlanguage.com, companion document to the 2003 book.
  https://www.domainlanguage.com/ddd/reference/, verified 2026-08-02.
- Vernon, Vaughn. "Implementing Domain-Driven Design." Addison-Wesley, 2013.
  Chapter 3, "Context Maps," including the worked Context Map example and
  the U and D relationship notation.
- Brandolini, Alberto. "Introducing EventStorming." Leanpub, 2021. Chapter
  on strategic design and context mapping via the EventStorming facilitation
  technique.
- Conway, Melvin E. "How Do Committees Invent." Datamation, April 1968.
  http://www.melconway.com/Home/Committees_Paper.html, verified 2026-08-02.
- Foote, Brian, and Yoder, Joseph. "Big Ball of Mud." In Pattern Languages
  of Program Design 4, Addison-Wesley, 1999.
  http://www.laputan.org/mud/, verified 2026-08-02.
- Cockburn, Alistair. "Hexagonal Architecture." alistair.cockburn.us, 2005.
  https://alistair.cockburn.us/hexagonal-architecture/, verified 2026-08-02.
- Context Mapper project documentation, "Context Map," contextmapper.org.
  https://contextmapper.org/docs/context-map/, verified 2026-08-02.
- Netflix Technology Blog. "Engineering Trade-Offs and The Netflix API
  Re-Architecture."
  https://netflixtechblog.com/engineering-trade-offs-and-the-netflix-api-re-architecture-a209f9e422c0,
  verified 2026-08-02.
- "A Conversation with Werner Vogels." ACM Queue, 2006.
  https://queue.acm.org/detail.cfm?id=1142065, verified 2026-08-02.
- Zalando. "Zalando RESTful API and Event Guidelines."
  https://opensource.zalando.com/restful-api-guidelines/, verified
  2026-08-02.
- Pact documentation, "What Is Pact." https://docs.pact.io/, verified
  2026-08-02.
- ArchUnit documentation. https://www.archunit.org/, verified 2026-08-02.

## Code examples

The Context Map pattern is a design and organizational artifact, not
executable logic, so the runnable code below demonstrates the concrete
mechanism a Context Map most directly produces in source form, an
Anticorruption Layer translating an upstream context's model into a
downstream context's model at a Bounded Context boundary, the piece of the
pattern that is genuinely code rather than a diagram.

### TypeScript

```typescript
// Upstream context's model, a third-party payment gateway's shape.
interface UpstreamPaymentRecord {
  txn_id: string;
  cents_amount: number;
  iso_currency: string;
  status_code: "OK" | "DECLINED" | "PENDING";
}

// Downstream context's own model, Billing's Ubiquitous Language.
interface BillingPayment {
  paymentId: string;
  amount: { value: number; currency: string };
  isSettled: boolean;
}

// Anticorruption Layer, the only place the upstream shape is known.
class PaymentGatewayAcl {
  translate(record: UpstreamPaymentRecord): BillingPayment {
    return {
      paymentId: record.txn_id,
      amount: { value: record.cents_amount / 100, currency: record.iso_currency },
      isSettled: record.status_code === "OK",
    };
  }
}

const acl = new PaymentGatewayAcl();
const upstream: UpstreamPaymentRecord = {
  txn_id: "tx_9001",
  cents_amount: 4599,
  iso_currency: "EUR",
  status_code: "OK",
};
console.log(acl.translate(upstream));
```

### Python

```python
from dataclasses import dataclass

# Upstream context's model.
@dataclass
class UpstreamPaymentRecord:
    txn_id: str
    cents_amount: int
    iso_currency: str
    status_code: str

# Downstream context's own model, Billing's Ubiquitous Language.
@dataclass
class BillingPayment:
    payment_id: str
    amount_value: float
    amount_currency: str
    is_settled: bool

class PaymentGatewayAcl:
    def translate(self, record: UpstreamPaymentRecord) -> BillingPayment:
        return BillingPayment(
            payment_id=record.txn_id,
            amount_value=record.cents_amount / 100,
            amount_currency=record.iso_currency,
            is_settled=record.status_code == "OK",
        )

acl = PaymentGatewayAcl()
upstream = UpstreamPaymentRecord("tx_9001", 4599, "EUR", "OK")
print(acl.translate(upstream))
```

### Go

```go
package main

import "fmt"

// Upstream context's model.
type UpstreamPaymentRecord struct {
	TxnID       string
	CentsAmount int
	IsoCurrency string
	StatusCode  string
}

// Downstream context's own model, Billing's Ubiquitous Language.
type BillingPayment struct {
	PaymentID      string
	AmountValue    float64
	AmountCurrency string
	IsSettled      bool
}

// Anticorruption Layer.
func Translate(r UpstreamPaymentRecord) BillingPayment {
	return BillingPayment{
		PaymentID:      r.TxnID,
		AmountValue:    float64(r.CentsAmount) / 100,
		AmountCurrency: r.IsoCurrency,
		IsSettled:      r.StatusCode == "OK",
	}
}

func main() {
	upstream := UpstreamPaymentRecord{"tx_9001", 4599, "EUR", "OK"}
	fmt.Printf("%+v\n", Translate(upstream))
}
```

The Java, Rust, and Swift variants are omitted from this entry, not because
the Anticorruption Layer mechanism does not translate to those languages,
it translates directly, a small struct-to-struct or class-to-class mapping
function in each, but because the mechanism carries no language-idiomatic
variation worth demonstrating a fourth, fifth, and sixth time. The shape is
identical, two data types and one pure translation function, and the three
languages above already establish that shape clearly.

I ran the TypeScript sample through `npx tsc --noEmit` against the file to
confirm it type-checks, ran the Python sample with `python3` to confirm it
executes and prints the translated record, and ran the Go sample with
`go run` to confirm it compiles and executes. All three produced the
expected translated output with no errors.
