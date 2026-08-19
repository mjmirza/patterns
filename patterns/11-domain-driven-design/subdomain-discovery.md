---
name: Subdomain Discovery
slug: subdomain-discovery
family: 11-domain-driven-design
category: Strategic Design
aliases: [Domain Decomposition, Subdomain Identification, Domain Analysis]
first_described: "Eric Evans 2003"
maturity: established
related: [core-domain, supporting-subdomain, generic-subdomain, bounded-context, event-storming, domain-storytelling, context-map, ubiquitous-language]
incompatible_with: []
verified: 2026-08-02
---

# Subdomain Discovery

## 1. Name, aliases, and lineage

The activity described here is Subdomain Discovery, sometimes called Domain
Decomposition or Subdomain Identification. It is not a structural pattern in
the Gang of Four sense. It is a strategic design practice, the process by
which a team splits an organization's problem space into subdomains before
any bounded context, service, or module boundary is drawn.

Eric Evans introduced the raw material for this practice in *Domain-Driven
Design. Tackling Complexity in the Heart of Software*, Addison-Wesley, 2003,
in the part of the book concerned with strategic design. Evans defined Core
Domain as the subdomain that is the reason the software exists and that
delivers competitive advantage, and Generic Subdomain as a subdomain that
solves a problem the industry has already solved, cited by the summary at
[dddcommunity.org's page on the book](https://www.dddcommunity.org/book/evans_2003/),
verified 2026-08-02. The book describes the classification. it does not lay
out a repeatable, facilitated method for finding the subdomains in the first
place. That gap is what later practitioners filled, and Subdomain Discovery
as a named, structured activity is the sum of their work rather than a single
author's coinage.

Vaughn Vernon closed part of the gap in *Implementing Domain-Driven Design*,
Addison-Wesley, 2013. The book opens its strategic design material by warning
that teams which skip straight to tactical patterns without first
understanding the Subdomain, the Bounded Context, and a concise Ubiquitous
Language end up building a technically competent system that solves the wrong
problem, illustrated with a case study of a team that made exactly that
mistake on their first DDD project
([Goodreads summary of *Implementing Domain-Driven Design*](https://www.goodreads.com/book/show/15756865-implementing-domain-driven-design),
verified 2026-08-02).

Alberto Brandolini supplied the most widely adopted facilitation technique,
Big Picture EventStorming, described on his own reference site
[eventstorming.com](https://www.eventstorming.com/), verified 2026-08-02, as
a workshop format with no upfront scope limitation, run in isolation from
software design activities, whose output is a map of the group's shared
understanding of the business at the time of the session rather than a final
architecture. Big Picture EventStorming is the discovery step. drawing service
or bounded context boundaries is a later, separate step in Brandolini's own
sequencing.

Nick Tune contributed the Core Domain Chart, a visualization that plots
candidate subdomains by their classification and their current versus desired
investment, used as a facilitation artifact for the same discovery
conversation, described across his Medium publication
[Nick Tune's Tech Strategy Blog](https://medium.com/nick-tune-tech-strategy-blog/domain-discovery-facilitation-make-scale-explicit-1bf5b53afa7b),
verified 2026-08-02. Vlad Khononov's *Learning Domain-Driven Design*, O'Reilly,
2021, treats subdomain discovery as its own chapter, separate from the chapter
on classifying subdomains and separate again from the chapter on bounded
contexts, which is the structuring this entry follows.

The Azure Architecture Center names the activity Domain Analysis and places it
as the first of four steps in a microservices design flow, analyze the
domain, define bounded contexts, apply tactical patterns, identify
microservices ([Microsoft Learn, "Use Domain Analysis to Model Microservices"](https://learn.microsoft.com/en-us/azure/architecture/microservices/model/domain-analysis),
verified 2026-08-02). That framing, subdomain identification as a distinct,
earlier step than bounded context definition, is the one used throughout this
entry.

`maturity: established` because the underlying classification vocabulary from
Evans is canonical and thirty years old, but the facilitated discovery
technique itself is a community practice assembled from several authors
rather than a single formally specified method, and workshops in the field
still diverge on exact steps.

## 2. Problem and context

A team about to build or re-architect a nontrivial system faces a boundary
problem before it faces a single line of code. Where does one part of the
system's responsibility end and another begin. Get this wrong early and every
subsequent decision inherits the mistake. a bounded context drawn around the
wrong subdomain, a microservice that owns two unrelated concerns, a team
staffed to the org chart instead of the business, a shared database because
nobody could say where the seam was.

The problem shows up in a specific, recognizable way. A team sits down to
design microservices, or draw bounded contexts, or split a monolith, and
starts by listing nouns. Order, Customer, Product, Invoice. Nouns are not
subdomains. Two teams can use the word Customer and mean entirely different
things, a shipping team's Customer is a delivery address and a set of
service-level constraints, a billing team's Customer is a payment method and
a credit limit. Jumping to nouns produces boundaries that follow the words
in the room rather than the actual shape of the business's areas of
responsibility, and the words in the room are usually inherited from a
database schema or an existing UI, not from the domain itself.

Subdomain Discovery exists to interpose a deliberate step between "we have a
complex business" and "here are our bounded contexts." It answers the
question of what the distinct, coherent areas of business capability inside
this problem are, and which of them actually earns the business money or
differentiates it from a competitor. The output is not code and not even an
architecture. it is a map of the problem space, subdomains, and a rough
classification of which of them deserves the most design and staffing
investment.

The context in which this matters is any system whose domain has grown past
the point where one person can hold the whole model in their head, per
Evans's own framing of why strategic design exists at all, cited above. A
five-screen CRUD app for a single small team does not need this activity. A
system spanning shipping, billing, inventory, customer support, and
regulatory reporting, built by multiple teams over multiple years, does, and
skipping it is the single most common root cause of a bounded context or
microservice boundary that has to be redrawn later at significant cost.

## 3. Forces

**Business differentiation versus uniform effort.** Not every part of a
system deserves the same investment. Pouring the best engineers and the
tightest domain modeling into a Generic Subdomain, a login system, a
tax-rate lookup, wastes the scarce resource that should go to the Core
Domain. Subdomain Discovery exists specifically to surface this asymmetry
before staffing decisions are made, and that means the discovery activity
must produce a classification, not just a boundary list.

**Discovery cost versus the cost of a wrong boundary later.** A proper
discovery workshop consumes days of a domain expert's time, sometimes a full
week for a large domain, and pulls senior people away from delivery. Skipping
it costs nothing today and can cost months later, when a service boundary
drawn around the wrong concept has to be split or merged after production
data and production coupling have accumulated around it. The pattern favors
paying the cost early, and the entry's own failure modes section names the
alternative cost precisely because the trade is easy to underweight under
delivery pressure.

**Shared vocabulary versus speed.** A workshop that brings domain experts,
developers, and stakeholders into the same room to build a Ubiquitous
Language is slower than one architect drawing boxes alone, but the boxes one
architect draws alone tend to encode that architect's private mental model
rather than the business's actual structure. Discovery favors the slower,
collective route because the boundary only holds if the people who will live
inside it agree it is real.

**Boundary stability versus business evolution.** A subdomain is a property
of the business, not of the software, and businesses evolve. Discovery
produces a snapshot, and the pattern has to reconcile that snapshot's
usefulness with the certainty that the business will change under it. The
practice favors treating the discovery output as a living map to be revisited
rather than a one-time deliverable, which is exactly what Brandolini's own
description of a Big Picture session output states, cited above.

**Conway's law versus intentional team design.** Team communication
structures tend to be mirrored in the systems those teams build, an
observation usually attributed to Melvin Conway and cited directly by
Microsoft's own domain analysis guidance in the context of DDD
([Microsoft Learn, "Use Domain Analysis to Model Microservices"](https://learn.microsoft.com/en-us/azure/architecture/microservices/model/domain-analysis),
verified 2026-08-02). If subdomain discovery happens after teams already
exist, the discovered boundaries drift toward whatever the org chart already
looks like rather than the business's real shape. The pattern favors running
discovery early enough, or independently enough, that team structure can be
adjusted to the discovered boundaries instead of the other way round, though
in practice this force is the hardest one to fully honor because
reorganizing teams is a political cost most engineering-led discovery
sessions cannot pay alone.

**Facilitation depth versus participant fatigue.** A Big Picture EventStorming
session that tries to model an entire enterprise in one sitting produces
either an exhausted room or a shallow map. The forces trade off against each
other inside the workshop format itself, and most practitioners resolve it by
running the discovery in a dedicated timeboxed session, cited above, rather
than trying to fold it into an existing standing meeting.

## 4. Applicability and non-applicability

**Reach for Subdomain Discovery when:**

- A system's domain is large enough that no single person, including the
  most senior engineer on the team, can accurately describe every business
  rule in it from memory. Evans's own strategic design material exists for
  exactly this scale, cited above.
- A greenfield system is about to be decomposed into bounded contexts or
  microservices, before that decomposition happens, so the boundaries follow
  business capability rather than a guessed technical seam.
- A monolith is being split, either into modules or into services, and the
  team needs a principled way to decide what goes where instead of splitting
  along the existing folder structure, which usually encodes accidents of
  history rather than domain structure.
- Several previously separate systems, or several acquired companies' systems,
  are being consolidated, and the team needs to know where the real domain
  overlaps are before merging code.
- Investment decisions are being made, hiring, staffing the strongest domain
  modelers, budget allocation, and the organization needs a defensible answer
  to which part of the system is actually its competitive advantage.
- A new bounded context or aggregate is being proposed and its scope is
  unclear, because the surrounding subdomain map has never been made explicit.

**Do NOT reach for Subdomain Discovery when:**

- The system is small enough, in scope and lifetime, that one team fully
  understands it end to end and boundary mistakes are cheap to fix in an
  afternoon. Running a multi-day discovery workshop for a five-endpoint
  internal tool spends more calendar time than the tool will ever save.
- The domain is genuinely still being discovered through user experimentation,
  as in an early-stage product still searching for product-market fit. A
  formal discovery workshop presumes there is a stable business to map, and
  running one against a business model that changes weekly produces a map
  that is stale before the ink dries. Iterate the code first, formalize the
  subdomains once the shape of the business has settled.
- A candidate subdomain is already known, with certainty, to be a Generic
  Subdomain that an off-the-shelf product fully covers, for example
  authentication via a managed identity provider or payroll via a payroll
  vendor. Discovery adds nothing there beyond confirming what is already
  obvious, and the effort belongs instead in evaluating vendors, per the
  buy-versus-build force this entry's related entry `generic-subdomain`
  covers directly.
- The organization has no ability, political or structural, to act on the
  discovered boundaries by reshaping teams or service ownership. A subdomain
  map that cannot change staffing, funding, or team structure still has
  value for shared vocabulary, but running the heavyweight version of the
  workshop under that constraint over-invests relative to what the outcome
  can change.
- The team is inside a single, already well-understood bounded context and is
  deciding on tactical patterns, aggregate boundaries, entities, value
  objects. Subdomain Discovery operates one level above that decision and
  answering it does not help choose an aggregate root.

## 5. Structure

Subdomain Discovery has participants rather than classes, because it is a
facilitated activity that produces an artifact, not a runtime structure.

- **Facilitator.** Runs the discovery session, keeps the group inside the
  problem space and out of solution talk, and is responsible for the pacing
  described under dynamics below. Often the same person across Big Picture
  EventStorming and Core Domain Chart sessions, per Brandolini's own material
  cited above.
- **Domain expert or experts.** The people who actually run the business area
  under discussion, sales, operations, compliance, logistics. Their presence
  is what separates discovery from an engineer's guess, because a domain
  expert can say that two things drawn as one box are actually handled by
  completely different departments with different rules, which is precisely
  the signal a subdomain boundary is drawn from.
- **Development team representatives.** Present to ask the questions that
  surface hidden complexity, and to carry the discovered map back into
  architecture decisions afterward.
- **Sponsor or business stakeholder.** Provides the authority to say which
  areas of the business the organization considers strategically
  differentiating, which feeds directly into the Core versus Supporting
  versus Generic classification.
- **The discovery artifact.** A physical or virtual map, sticky notes on a
  wall or an equivalent digital board, that starts as an unordered timeline
  of domain events and business activities and is progressively clustered
  into candidate subdomains.
- **Candidate subdomain.** A cluster of closely related business capabilities
  that the group agrees behaves as one coherent unit of concern. This is the
  primary output of discovery and the primary input to the classification
  step covered by this repository's `core-domain`, `supporting-subdomain`,
  and `generic-subdomain` entries.
- **Pivotal event.** A domain event, in Brandolini's EventStorming vocabulary,
  that the group agrees marks a handoff from one area of responsibility to
  another, and therefore a candidate boundary between two subdomains. A
  pivotal event is the mechanical, repeatable signal this entry's code
  examples operationalize below.
- **Context map, a downstream artifact, not part of discovery itself.** Once
  subdomains are classified and bounded contexts are drawn around them, the
  relationships between those contexts are recorded separately, covered by
  this repository's `context-map` entry.

## 6. ASCII structure diagram

```
  Business activity, told as a story by domain experts
              |
              v
  +---------------------------------------------------+
  |            Discovery workshop artifact             |
  |  (event timeline, sticky notes, or digital board)   |
  |                                                     |
  |  E1 -> E2 -> E3 -> [PIVOT] -> E4 -> E5 -> [PIVOT]   |
  |         \_________/            \____/               |
  |          candidate               candidate           |
  |          subdomain A             subdomain B         |
  +---------------------------------------------------+
              |
              v
  +----------------------+   +----------------------+
  |  Candidate subdomain |   |  Candidate subdomain |
  |          A           |   |          B           |
  |  events. E1, E2, E3   |   |  events. E4, E5       |
  +----------------------+   +----------------------+
              |                          |
              v                          v
      Core / Supporting /        Core / Supporting /
      Generic classification     Generic classification
              |                          |
              v                          v
      +---------------+          +---------------+
      | Bounded        |          | Bounded        |
      | Context (1 to  |          | Context (1 to  |
      | 1 or a later   |          | 1 or a later   |
      | merge)         |          | merge)         |
      +---------------+          +---------------+

  Legend
  Ex        a domain event placed on the timeline by a participant
  [PIVOT]   a pivotal event, agreed by the group to mark a boundary
  candidate a contiguous run of events between two pivotal events
```

## 7. Dynamics

```
  Facilitator          Domain experts /       Discovery
  (drives pacing)       stakeholders           artifact
       |                      |                    |
       |-- 1. chaotic         |                    |
       |   exploration ------>|                    |
       |                      |-- write events ---->|
       |                      |   (any order,       |
       |                      |    any actor)        |
       |                      |                    |
       |-- 2. enforce the ----|                    |
       |   timeline ---------->|                    |
       |                      |-- reorder events -->|
       |                      |                    |
       |-- 3. surface --------|                    |
       |   pivotal events ---->|                    |
       |                      |-- mark handoffs --->|
       |                      |   between areas      |
       |                      |                    |
       |-- 4. cluster --------|                    |
       |   into candidates --->|                    |
       |                      |-- group events ---->|
       |                      |   between pivots     |
       |                      |                    |
       |-- 5. name and -------|                    |
       |   classify ---------->|                    |
       |                      |-- Core / Supporting /|
       |                      |   Generic verdict --->|
       |                      |                    |
       |-- 6. hand off -------|                    |
       |   to bounded         |                    |
       |   context design     |                    |
       v                      v                    v
```

The sequence above follows Brandolini's own three-flavor structuring of
EventStorming, Big Picture first, Process Modelling second, Software Design
third, with subdomain discovery living entirely inside the first flavor and
handing its output to the second and third, cited above via
[eventstorming.com](https://www.eventstorming.com/), verified 2026-08-02.
Step 2, enforcing a single shared timeline out of an initially chaotic set of
sticky notes, is the step most facilitators report as doing the real work.
Disagreements about ordering are disagreements about the model, surfaced in a
form domain experts can argue about without needing to know any software
vocabulary.

Step 3, surfacing pivotal events, is where the boundary decision actually
happens, and it is a judgement call made by the room, not a mechanical
computation. A pivotal event is agreed to exist when the group notices that
responsibility for what happens next has moved to a different department, a
different system of record, or a different set of business rules. "Order
Placed" is rarely pivotal on its own. "Order Handed to Fulfillment" often is,
because everything before it belongs to a sales-and-catalog concern and
everything after it belongs to a logistics concern with entirely different
rules, actors, and failure modes.

## 8. Implementation variants

**Big Picture EventStorming (Brandolini).** A physical or virtual unlimited
timeline covered with orange sticky notes for domain events, run with no
predetermined scope, explicitly separated from software design activities.
This is the most widely cited variant and the one this entry's dynamics
section follows directly, cited above.

**Domain Storytelling (Hofer and Schwentner).** A pictographic technique where
a domain expert tells a story using actors, work objects, and activities
rendered as icons, narrated sentence by sentence and captured live by a
listener. It surfaces subdomains as the set of distinct actor and workobject
groupings that recur across stories, and it is gentler on domain experts who
find an unbounded sticky-note wall intimidating. See this repository's
`domain-storytelling` entry for the full technique.

**Core Domain Charts (Nick Tune).** A two-axis visualization, business
differentiation on one axis and current model quality or investment on the
other, plotted per candidate subdomain, used less to discover the boundaries
in the first place and more to force an explicit, defensible classification
conversation once candidates already exist, described across Tune's own
Medium series cited above.

**Top-down decomposition from a domain vision statement.** Start from Evans's
own suggested artifact, a short written statement of the system's core
purpose, cited above, and decompose it by asking what has to be true for
this vision to hold until the answers stop being further decomposable. This
variant suits organizations with an existing, mature business strategy
document and a domain expert population too dispersed to gather for a
multi-day workshop, at the cost of losing the tacit knowledge that only
surfaces when a domain expert corrects a peer in real time.

**Structured interviews.** When a full workshop with all stakeholders in one
room is infeasible, sequential one-on-one interviews with domain experts,
each asked to describe their area's inputs, outputs, and rules, followed by
a synthesis pass by the facilitator. Slower and more prone to missing the
cross-department friction points a shared-room workshop surfaces
automatically, but the only realistic option for globally distributed
domain experts who cannot be gathered for several consecutive days.

**Legacy code and coupling mining.** In a brownfield system with no available
domain experts, or where the experts' mental model has drifted from what the
code actually does, subdomains can be inferred bottom up by measuring which
modules, tables, or classes change together in the version control history
and which are queried together at runtime. This produces a coupling-based
approximation of subdomain boundaries rather than a business-meaning-based
one, and the approximation must always be validated against a domain expert
afterward, because code coupling reflects implementation history as often as
it reflects domain structure.

**Value chain and business capability mapping.** Some organizations enter
discovery with an existing value chain map, a Wardley Map, or a business
capability model already produced by a strategy or enterprise architecture
function. In that case discovery becomes a validation and refinement pass
over an existing artifact rather than a from-scratch exercise, checking each
mapped capability against the event-level detail a workshop would otherwise
surface.

## 9. Known production uses

Microsoft's own Azure Architecture Center documents domain analysis, its name
for subdomain discovery, as the first of a four-step process it recommends
for designing microservices, and walks through a full worked example, a
fictional drone delivery company named Fabrikam, that produces candidate
subdomains, Shipping, Drone Management, ETA Analysis, User Accounts,
Invoicing, Call Center, and classifies them into Core, Supporting, and
Generic before any bounded context or service boundary is drawn
([Microsoft Learn, "Use Domain Analysis to Model Microservices"](https://learn.microsoft.com/en-us/azure/architecture/microservices/model/domain-analysis),
verified 2026-08-02). The article is explicit that the classification step is
what determines where the organization invests its heaviest design and
staffing effort, matching Evans's original distinction cited in dimension 1.

Capital One's engineering organization has published that it uses Event
Storming, the discovery technique this entry treats as the primary variant,
repeatedly as a starting point for microservices modernization initiatives,
bringing domain experts from across the company together to decompose a
domain into pieces that are subsequently reassembled into a target
microservices architecture
([Capital One Tech, "Event Storming. Kick-Start Your Microservices Architecture"](https://www.capitalone.com/tech/software-engineering/event-storming-for-microservice-architecture/),
verified 2026-08-02).

IBM's client engineering practice documents pairing a design thinking
workshop with Event Storming to run an end-to-end business process discovery
exercise ahead of building event-driven solutions, explicitly positioning the
discovery step before any technical solution design begins
([IBM Cloud Architecture reference material, "Domain Driven Design"](https://ibm-cloud-architecture.github.io/refarch-eda/methodology/domain-driven-design/),
verified 2026-08-02).

## 10. Consequences

**Positive.**

- Boundaries drawn after discovery reflect the business's own structure
  instead of an engineer's private mental model or an inherited database
  schema, which directly reduces the odds of a bounded context that spans
  two unrelated business concerns.
- A completed classification, Core, Supporting, Generic, gives the
  organization a defensible, explicit basis for staffing and investment
  decisions instead of an implicit, unexamined one, matching the purpose
  Evans assigned Core Domain in the first place, cited above.
- The shared vocabulary a discovery workshop produces becomes the seed of a
  Ubiquitous Language for each downstream bounded context, reducing the odds
  that two teams silently mean different things by the same word.
- The workshop format surfaces organizational friction, two departments who
  each believe they own a piece of the process, before that friction becomes
  a production incident caused by two services independently trying to be
  the system of record for the same concept.
- The candidate boundaries produced are reusable across a monolith split, a
  microservice decomposition, and a team topology redesign, because the
  subdomain map is independent of any single implementation choice.

**Negative.**

- The activity consumes real, and sometimes significant, calendar time from
  the people least available to give it, senior domain experts and
  stakeholders. A multi-day Big Picture session for a large enterprise
  domain is a genuine organizational cost, not a free planning exercise.
- A discovery map is a snapshot. It goes stale as the business evolves, and
  an organization that treats the original workshop's output as permanent
  rather than revisiting it periodically ends up with boundaries that were
  correct once and are quietly wrong now.
- The output is inherently a judgement call, not a computed answer. Two
  different facilitators running the same discovery with the same domain
  experts can produce differently shaped candidate subdomains, and the
  method offers no way to prove one shape is objectively correct.
- Discovery can surface organizational problems, ownership disputes, unclear
  authority, that the engineering team convening the workshop has no power
  to resolve, leaving a technically sound map that cannot be acted on
  without a political decision above the team's pay grade.
- Running the workshop without a facilitator experienced in keeping the room
  in problem space, rather than jumping to solution talk, class diagrams,
  API shapes, reliably degrades the output into premature technical design
  wearing sticky notes.

## 11. Failure modes and misuse

**Symptom.** The discovered subdomain map looks suspiciously identical to the
existing org chart.
**Cause.** The workshop was run with the current team structure already fixed
and unquestioned in participants' minds, so Conway's law, cited under
dimension 3, operated backward, the org chart shaped the discovered domain
instead of the domain shaping the org chart.
**Fix.** Explicitly ask the room, for each candidate boundary, whether that
boundary would exist if the current teams did not, and treat any boundary
that survives that question only because of existing team ownership as
suspect.

**Symptom.** Every candidate subdomain ends up classified as Core.
**Cause.** The classification step was run without a business sponsor present
to say no, or was run by engineers alone, who tend to rate whatever they find
technically interesting as strategically important.
**Fix.** Require a business stakeholder with budget authority to sign off on
the Core classification specifically, since a Core Domain classification is a
resourcing commitment, and reserve it for subdomains that genuinely provide
competitive differentiation rather than technical difficulty.

**Symptom.** The workshop produces dozens of tiny candidate subdomains, each
one or two events wide.
**Cause.** Pivotal events were marked too liberally, often because
participants defaulted to marking every event as pivotal when uncertain,
rather than reserving the marker for genuine handoffs of responsibility.
**Fix.** Require the facilitator to challenge each proposed pivotal event by
asking what specifically changes there, actor, system of record, or rule
set, and merge any two adjacent candidates where the answer is vague.

**Symptom.** Six months after the workshop, nobody can find the map, or the
map exists but nobody trusts it anymore.
**Cause.** The output was treated as a one-time deliverable, filed away, and
never revisited as the business changed, contradicting the living-artifact
framing Brandolini gives the technique, cited above.
**Fix.** Schedule a periodic, lightweight review of the subdomain map, tied
to a recurring business event such as a quarterly planning cycle, rather than
treating discovery as a single, closed project phase.

**Symptom.** A subdomain classified as Generic during discovery is still
being custom-built in house two years later with a large internal team.
**Cause.** The classification was made correctly but never acted on, because
no decision-maker owned the follow-through of evaluating and adopting a
vendor solution for it.
**Fix.** Attach an explicit owner and a decision deadline to every Generic
classification at the moment it is made, not just a label.

**Symptom.** The discovery workshop devolves into an argument about class
names, database schemas, or API endpoints.
**Cause.** The facilitator failed to hold the room in problem space, and
participants, especially engineers present in the room, drifted into
solution space because it feels more concrete and more comfortable than
describing business rules in plain language.
**Fix.** A facilitator explicitly enforces a no-technology-talk rule during
the discovery phase and defers all such discussion to the downstream bounded
context design step, where it belongs.

## 12. Trade-off matrix

| Force | Subdomain Discovery (workshop-led) | Guessed boundaries from an existing schema | Purely top-down business capability model |
|---|---|---|---|
| Reflects real business structure | High, because domain experts validate every boundary in real time | Low, boundaries reflect implementation history, not business meaning | Medium, reflects strategy documents, which can be stale relative to day-to-day operations |
| Speed to a first boundary | Slow, days of scheduling and workshop time | Fast, hours, since the schema already exists | Medium, depends on whether the capability model already exists |
| Surfaces organizational friction | High, cross-department disagreements appear live in the room | None, a schema cannot disagree with itself | Low, a document rarely captures unresolved team-level disputes |
| Requires scarce expert time | High, needs multiple domain experts for multiple days | None | Low to medium, may already be sunk cost from a prior strategy exercise |
| Produces a defensible investment classification | High, this is a stated goal of the technique | None, a schema carries no notion of strategic value | Medium, a capability model often ranks capabilities but rarely at subdomain granularity |
| Risk of encoding accidental history as domain structure | Low | High, this is the primary risk of the alternative | Low to medium, risk shifts to encoding org politics as strategy |
| Suitability for a small, well-understood system | Poor fit, overkill | Reasonable, the schema is usually still small enough to reason about directly | Poor fit, overkill |

## 13. Related and incompatible patterns

**core-domain, supporting-subdomain, generic-subdomain.** Subdomain Discovery
produces the candidate boundaries. These three entries cover what happens to
each candidate once it is classified, including the specific engineering and
staffing consequences of each classification. Discovery is the input step,
classification is the output this entry hands off to those three.

**bounded-context.** A bounded context is a solution-space construct, a
boundary within which a single model and a single Ubiquitous Language apply.
Subdomain Discovery operates strictly in the problem space and produces the
map that bounded context design then uses as its starting point. The two are
not the same thing and the most common conceptual error in the field is
treating them as synonyms. A subdomain and its corresponding bounded context
frequently end up drawn at different boundaries on purpose, for instance one
Core Domain subdomain modeled by two separate bounded contexts because two
different teams need different views of it.

**event-storming.** The primary facilitation technique this entry's dynamics
section is built around. Event Storming is the mechanism, Subdomain Discovery
is the goal one flavor of Event Storming, Big Picture, is used to reach.

**domain-storytelling.** An alternative facilitation technique to Event
Storming, better suited to domain experts uncomfortable narrating an
unbounded sticky-note wall, and generally run with a smaller group.

**context-map.** Once subdomains are discovered and classified, and bounded
contexts are drawn, the relationships between those contexts, customer or
supplier, conformist, anticorruption layer, are recorded by a context map.
Context mapping is downstream of and depends on discovery having happened
first.

**ubiquitous-language.** Each discovered subdomain typically develops its own
vocabulary during the workshop, and that vocabulary becomes the seed of the
Ubiquitous Language for the bounded context eventually drawn around it.

**Incompatible with nothing structurally**, because Subdomain Discovery is a
process activity rather than a code structure and does not compete for the
same runtime resource any structural pattern would. It is, however,
practically undermined by any process that skips straight from a raw
requirements document to a service boundary, since that shortcut is precisely
the failure mode this entry exists to prevent.

## 14. Refactoring path in and out

**Introducing discovery into an existing system with no prior domain map.**
Start by cataloging the bounded contexts, services, or modules that already
exist, whatever their current shape, and for each one write down, without
judgement, what business capability it currently claims to own. Run a
retrospective Big Picture EventStorming session using the system's actual
recorded domain events, pulled from logs, audit tables, or message topics
where available, rather than an imagined ideal event list, since a retrofit
discovery is more honest when it is grounded in what the system actually
does today. Compare the workshop's freshly discovered candidate subdomains
against the existing boundary catalog. Where they match, the existing
boundary is validated. Where they diverge, that divergence is now an explicit
finding, and it becomes an input to a deliberate, prioritized boundary
correction rather than a boundary that quietly stays wrong because nobody
ever named the mismatch.

**Introducing discovery for a genuinely new system.** Run the workshop before
any bounded context or service is proposed, following the dynamics sequence
in dimension 7. Resist the pressure, which is considerable under delivery
timelines, to let engineers start drafting an architecture diagram during the
workshop itself, capture the map, close the session, and let the
architecture design begin as a separate, subsequent activity that consumes
the map as an input.

**Retiring or revising an outdated subdomain map.** A map does not need
removing the way a code pattern does, but it does go stale, per dimension
11's staleness failure mode. The refactor here is procedural. Schedule a
lightweight re-validation pass, typically a half-day rather than the original
multi-day session, where the same or a refreshed group of domain experts
reviews the existing candidate subdomains against what has changed in the
business since the original workshop, and either reaffirms or revises the
classification of each. A subdomain previously classified Supporting can
become Core if the business's strategy shifts toward it, and the reverse
happens just as often when a formerly differentiating capability becomes
commoditized across the industry.

## 15. Testing and verification

Subdomain Discovery itself is not code and is not unit tested in the ordinary
sense, but its output is verifiable, and skipping verification is a common
misuse.

**Verify against domain experts, not against engineers alone.** The
candidate subdomain map, once drawn, should be walked back through with the
domain experts who participated, and separately with at least one domain
expert who did not participate, asking them to independently confirm each
boundary makes sense against their own understanding of the business. A
boundary only the facilitator and the engineers in the room believe in has
not actually been verified.

**Verify the classification with a concrete counterfactual.** For a proposed
Core Domain classification, ask whether a competitor building an identical
version of this subdomain tomorrow would cost the business its advantage. A
yes supports the classification. An uncertain or no answer is a signal the
subdomain may actually be Supporting, and the classification should be
revisited before it drives a staffing decision.

**Verify pivotal events against operational data where it exists.** Where a
system already runs in production, pivotal event boundaries proposed on a
sticky-note wall can be cross-checked against real telemetry, message topic
boundaries, or database transaction boundaries, since a genuine handoff of
responsibility in the business usually correlates with a genuine handoff of
data or control in the running system. A mismatch between the workshop's
pivotal event and the code's actual behavior at that point is worth
investigating before trusting either one blindly.

**Verify by testing the map's decision-making power, not its shape alone.**
A useful discovery output should be able to answer a concrete question, such
as which subdomain two newly hired senior engineers should join next
quarter, without further debate. If the map cannot answer that kind of
question, it has not actually done its job regardless of how tidy the sticky
notes look.

## 16. Observability signals

This dimension is engineering judgement, informed by practice rather than a
single cited source, since discovery itself produces no runtime telemetry.

A healthy subdomain map shows up indirectly in the codebase and the
organization's behaviour, not in a dashboard. Signals that the discovered
boundaries are holding include a low rate of cross-team pull requests that
touch two different bounded contexts' persistence models in the same change,
a low rate of ownership questions raised during incident postmortems, and a
staffing distribution that visibly weights toward subdomains classified Core
rather than being spread evenly regardless of classification.

Signals that a discovered map has gone stale or was wrong include a rising
rate of anticorruption layers being added at a boundary that was originally
supposed to be a clean bounded context split, a subdomain's Ubiquitous
Language visibly diverging from what its own domain experts currently use in
conversation, and repeated ad hoc reorganizations of the same service
boundary, which usually indicates the original boundary never matched the
domain and each reorg is an attempt to correct it without naming the root
cause.

## 17. Security and privacy implications

Subdomain Discovery itself opens no attack surface, since it produces a
map and a classification, not running software. Its security-relevant
consequence is indirect but material. Classifying a subdomain as Generic and
routing it to a third-party vendor, for example an identity provider or a
payment processor, is exactly the moment personal data, credentials, or
payment details cross an organizational trust boundary, and the discovery
and classification step is the earliest point at which that data flow should
be flagged for a data protection review. A discovery workshop that
classifies a subdomain as Generic without also flagging what data would leave
the organization's control as a result has skipped a step that later becomes
a compliance finding rather than an architecture decision.

Separately, because a discovery workshop necessarily exposes business rules,
volumes, margins, and competitive strategy to everyone in the room, including
any external consultants or vendor representatives present, the participant
list itself carries a confidentiality consideration that has nothing to do
with the software being designed and everything to do with who is trusted
with the organization's Core Domain reasoning.

## 18. References

1. Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*, Addison-Wesley, 2003. Strategic design part, Core Domain and
   Generic Subdomain. Summarized at
   [dddcommunity.org, "Domain-Driven Design by Eric Evans"](https://www.dddcommunity.org/book/evans_2003/),
   verified 2026-08-02.
2. Vaughn Vernon, *Implementing Domain-Driven Design*, Addison-Wesley, 2013.
   Strategic design opening chapters, Subdomain, Bounded Context, and
   Ubiquitous Language sequencing. Summarized at
   [Goodreads, "Implementing Domain-Driven Design"](https://www.goodreads.com/book/show/15756865-implementing-domain-driven-design),
   verified 2026-08-02.
3. Alberto Brandolini, EventStorming reference site, Big Picture, Process
   Modelling, and Software Design workshop flavors.
   [eventstorming.com](https://www.eventstorming.com/), verified 2026-08-02.
4. Nick Tune, "Domain Discovery Facilitation. Make Scale Explicit," Nick
   Tune's Tech Strategy Blog.
   [medium.com/nick-tune-tech-strategy-blog/domain-discovery-facilitation-make-scale-explicit-1bf5b53afa7b](https://medium.com/nick-tune-tech-strategy-blog/domain-discovery-facilitation-make-scale-explicit-1bf5b53afa7b),
   verified 2026-08-02.
5. Vlad Khononov, *Learning Domain-Driven Design*, O'Reilly, 2021. Chapters
   on discovering and on classifying subdomains, treated as separate
   chapters from bounded context design.
6. Microsoft Learn, "Use Domain Analysis to Model Microservices," Azure
   Architecture Center, drone delivery worked example.
   [learn.microsoft.com/en-us/azure/architecture/microservices/model/domain-analysis](https://learn.microsoft.com/en-us/azure/architecture/microservices/model/domain-analysis),
   verified 2026-08-02.
7. Capital One Tech, "Event Storming. Kick-Start Your Microservices
   Architecture."
   [capitalone.com/tech/software-engineering/event-storming-for-microservice-architecture/](https://www.capitalone.com/tech/software-engineering/event-storming-for-microservice-architecture/),
   verified 2026-08-02.
8. IBM Cloud Architecture reference material, "Domain Driven Design."
   [ibm-cloud-architecture.github.io/refarch-eda/methodology/domain-driven-design/](https://ibm-cloud-architecture.github.io/refarch-eda/methodology/domain-driven-design/),
   verified 2026-08-02.
9. Wikipedia contributors, "Conway's law," background on team communication
   structure shaping system structure, cited by the Microsoft Learn domain
   analysis article above as the basis for its own Conway's law framing.
   [en.wikipedia.org/wiki/Conway%27s_law](https://en.wikipedia.org/wiki/Conway%27s_law),
   verified 2026-08-02.

## Code examples

Subdomain Discovery is a facilitated process, not a runtime structure, so the
code below models the one part of the process that is genuinely mechanical
and testable, deriving candidate subdomain boundaries from an ordered event
timeline by splitting at agreed pivotal events, per dimension 6's diagram and
dimension 7's dynamics, then computing a cross-candidate coupling count as the
signal for the over-fragmentation failure mode from dimension 11. The
classification step that follows discovery, Core, Supporting, or Generic, is
covered by this repository's `core-domain` entry's code example and is not
repeated here to avoid duplicating that entry's contract.

### TypeScript

```typescript
interface DomainEvent {
  name: string;
  actor: string;
  isPivotal: boolean;
  refersTo: string[];
}

interface CandidateSubdomain {
  id: number;
  events: DomainEvent[];
}

function discoverCandidates(timeline: DomainEvent[]): CandidateSubdomain[] {
  if (timeline.length === 0) {
    throw new Error("cannot discover subdomains from an empty timeline");
  }

  const candidates: CandidateSubdomain[] = [];
  let current: DomainEvent[] = [];
  let nextId = 1;

  for (const event of timeline) {
    current.push(event);
    if (event.isPivotal) {
      candidates.push({ id: nextId, events: current });
      nextId += 1;
      current = [];
    }
  }
  if (current.length > 0) {
    candidates.push({ id: nextId, events: current });
  }
  return candidates;
}

function candidateNames(candidate: CandidateSubdomain): string[] {
  return candidate.events.map((e) => e.name);
}

function crossCandidateCouplingCount(candidates: CandidateSubdomain[]): number {
  const membership = new Map<string, number>();
  for (const candidate of candidates) {
    for (const event of candidate.events) {
      membership.set(event.name, candidate.id);
    }
  }

  let coupling = 0;
  for (const candidate of candidates) {
    for (const event of candidate.events) {
      for (const ref of event.refersTo) {
        const refCandidate = membership.get(ref);
        if (refCandidate !== undefined && refCandidate !== candidate.id) {
          coupling += 1;
        }
      }
    }
  }
  return coupling;
}

function isLikelyOverFragmented(candidates: CandidateSubdomain[], maxAvgEvents: number): boolean {
  const total = candidates.reduce((sum, c) => sum + c.events.length, 0);
  return total / candidates.length < maxAvgEvents;
}

function main(): void {
  const timeline: DomainEvent[] = [
    { name: "ItemAddedToCart", actor: "shopper", isPivotal: false, refersTo: [] },
    { name: "CheckoutStarted", actor: "shopper", isPivotal: false, refersTo: ["ItemAddedToCart"] },
    { name: "OrderHandedToFulfillment", actor: "sales", isPivotal: true, refersTo: ["CheckoutStarted"] },
    { name: "DroneAssigned", actor: "dispatcher", isPivotal: false, refersTo: [] },
    { name: "PackagePickedUp", actor: "drone", isPivotal: false, refersTo: ["DroneAssigned"] },
    { name: "PackageDelivered", actor: "drone", isPivotal: true, refersTo: ["OrderHandedToFulfillment"] },
    { name: "InvoiceIssued", actor: "billing", isPivotal: true, refersTo: ["PackageDelivered"] },
  ];

  const candidates = discoverCandidates(timeline);
  for (const candidate of candidates) {
    console.log(`candidate ${candidate.id}`, candidateNames(candidate).join(", "));
  }

  console.log("cross-candidate coupling count", crossCandidateCouplingCount(candidates));
  console.log("looks over-fragmented at threshold 2.5", isLikelyOverFragmented(candidates, 2.5));
}

main();
```

Compiled and run with `tsc --strict --target es2020 --module commonjs
subdomain-discovery.ts` followed by `node subdomain-discovery.js`, using the
locally installed TypeScript compiler.

### Python

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class DomainEvent:
    name: str
    actor: str
    is_pivotal: bool
    refers_to: tuple[str, ...] = field(default_factory=tuple)


@dataclass
class CandidateSubdomain:
    id: int
    events: list[DomainEvent]

    def names(self) -> list[str]:
        return [e.name for e in self.events]


def discover_candidates(timeline: list[DomainEvent]) -> list[CandidateSubdomain]:
    if not timeline:
        raise ValueError("cannot discover subdomains from an empty timeline")

    candidates: list[CandidateSubdomain] = []
    current: list[DomainEvent] = []
    next_id = 1

    for event in timeline:
        current.append(event)
        if event.is_pivotal:
            candidates.append(CandidateSubdomain(id=next_id, events=current))
            next_id += 1
            current = []

    if current:
        candidates.append(CandidateSubdomain(id=next_id, events=current))

    return candidates


def cross_candidate_coupling_count(candidates: list[CandidateSubdomain]) -> int:
    membership: dict[str, int] = {}
    for candidate in candidates:
        for event in candidate.events:
            membership[event.name] = candidate.id

    coupling = 0
    for candidate in candidates:
        for event in candidate.events:
            for ref in event.refers_to:
                ref_candidate = membership.get(ref)
                if ref_candidate is not None and ref_candidate != candidate.id:
                    coupling += 1
    return coupling


def is_likely_over_fragmented(candidates: list[CandidateSubdomain], max_avg_events: float) -> bool:
    total = sum(len(c.events) for c in candidates)
    return (total / len(candidates)) < max_avg_events


def main() -> None:
    timeline = [
        DomainEvent("ItemAddedToCart", "shopper", False, ()),
        DomainEvent("CheckoutStarted", "shopper", False, ("ItemAddedToCart",)),
        DomainEvent("OrderHandedToFulfillment", "sales", True, ("CheckoutStarted",)),
        DomainEvent("DroneAssigned", "dispatcher", False, ()),
        DomainEvent("PackagePickedUp", "drone", False, ("DroneAssigned",)),
        DomainEvent("PackageDelivered", "drone", True, ("OrderHandedToFulfillment",)),
        DomainEvent("InvoiceIssued", "billing", True, ("PackageDelivered",)),
    ]

    candidates = discover_candidates(timeline)
    for candidate in candidates:
        print(f"candidate {candidate.id}", ", ".join(candidate.names()))

    print("cross-candidate coupling count", cross_candidate_coupling_count(candidates))
    print("looks over-fragmented at threshold 2.5", is_likely_over_fragmented(candidates, 2.5))


if __name__ == "__main__":
    main()
```

Run with `python3 subdomain-discovery.py`, using the locally installed Python
interpreter.

### Go

```go
package main

import "fmt"

type DomainEvent struct {
	Name      string
	Actor     string
	IsPivotal bool
	RefersTo  []string
}

type CandidateSubdomain struct {
	ID     int
	Events []DomainEvent
}

func (c CandidateSubdomain) Names() []string {
	names := make([]string, 0, len(c.Events))
	for _, e := range c.Events {
		names = append(names, e.Name)
	}
	return names
}

func discoverCandidates(timeline []DomainEvent) ([]CandidateSubdomain, error) {
	if len(timeline) == 0 {
		return nil, fmt.Errorf("cannot discover subdomains from an empty timeline")
	}

	var candidates []CandidateSubdomain
	var current []DomainEvent
	nextID := 1

	for _, event := range timeline {
		current = append(current, event)
		if event.IsPivotal {
			candidates = append(candidates, CandidateSubdomain{ID: nextID, Events: current})
			nextID++
			current = nil
		}
	}
	if len(current) > 0 {
		candidates = append(candidates, CandidateSubdomain{ID: nextID, Events: current})
	}
	return candidates, nil
}

func crossCandidateCouplingCount(candidates []CandidateSubdomain) int {
	membership := make(map[string]int)
	for _, candidate := range candidates {
		for _, event := range candidate.Events {
			membership[event.Name] = candidate.ID
		}
	}

	coupling := 0
	for _, candidate := range candidates {
		for _, event := range candidate.Events {
			for _, ref := range event.RefersTo {
				if refCandidate, ok := membership[ref]; ok && refCandidate != candidate.ID {
					coupling++
				}
			}
		}
	}
	return coupling
}

func isLikelyOverFragmented(candidates []CandidateSubdomain, maxAvgEvents float64) bool {
	total := 0
	for _, c := range candidates {
		total += len(c.Events)
	}
	return float64(total)/float64(len(candidates)) < maxAvgEvents
}

func main() {
	timeline := []DomainEvent{
		{"ItemAddedToCart", "shopper", false, nil},
		{"CheckoutStarted", "shopper", false, []string{"ItemAddedToCart"}},
		{"OrderHandedToFulfillment", "sales", true, []string{"CheckoutStarted"}},
		{"DroneAssigned", "dispatcher", false, nil},
		{"PackagePickedUp", "drone", false, []string{"DroneAssigned"}},
		{"PackageDelivered", "drone", true, []string{"OrderHandedToFulfillment"}},
		{"InvoiceIssued", "billing", true, []string{"PackageDelivered"}},
	}

	candidates, err := discoverCandidates(timeline)
	if err != nil {
		panic(err)
	}

	for _, candidate := range candidates {
		fmt.Printf("candidate %d %v\n", candidate.ID, candidate.Names())
	}

	fmt.Println("cross-candidate coupling count", crossCandidateCouplingCount(candidates))
	fmt.Println("looks over-fragmented at threshold 2.5", isLikelyOverFragmented(candidates, 2.5))
}
```

Run with `go run subdomain-discovery.go`, using the locally installed Go
toolchain.

Java, Rust, Swift, C#, and Kotlin are omitted here not because the pattern
does not translate, the discovery-and-clustering logic is language neutral,
but because the three languages above already demonstrate the mechanical
core across a static nominally-typed language, a dynamically typed scripting
language, and a compiled systems language, and a fourth or fifth
implementation of the identical linear scan would add length without adding
a genuinely new idiom, unlike cases in this repository's tactical DDD entries
where a language's type system materially changes the shape of the solution.
