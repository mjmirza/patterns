---
name: Event Storming
slug: event-storming
family: 11-domain-driven-design
category: Behavioral
aliases: [EventStorming, Big Picture EventStorming, Process Modeling EventStorming, Design Level EventStorming]
first_described: "Alberto Brandolini 2013"
maturity: established
related: [domain-event, bounded-context, ubiquitous-language, aggregate-root, context-map, process-manager, published-language]
incompatible_with: []
verified: 2026-08-02
---

# Event Storming

## 1. Name, aliases, and lineage

The canonical name is EventStorming, written as one word by its creator and
almost universally split into two words, Event Storming, by everyone else. Both
spellings refer to the same technique and this entry uses the two word form for
readability except where quoting a source directly.

Alberto Brandolini, an Italian software consultant working in the Domain-Driven
Design community, introduced the technique in a blog post dated 18 November
2013 (Wikipedia, "Event storming", https://en.wikipedia.org/wiki/Event_storming,
verified 2026-08-02). Brandolini later expanded the idea into a self-published
book, *Introducing EventStorming*, distributed through Leanpub, which remains
the primary reference text for the format (eventstorming.com,
https://www.eventstorming.com/, verified 2026-08-02, lists the book as the
official source and Brandolini as its author).

The name itself has a documented origin story. According to the Wikipedia
article on Event storming, the term was coined while Brandolini was a guest
trainer on Vaughn Vernon's Implementing Domain-Driven Design tour, and the
working name was changed from "Event-based modelling" to "EventStorming" just
before a presentation in Leuven, Belgium (Wikipedia, "Event storming",
verified 2026-08-02). Vaughn Vernon's own book, *Implementing Domain-Driven
Design*, Addison-Wesley, 2013, is the IDDD reference that the tour is named
after, and it documents the aggregate and domain event vocabulary that Event
Storming sessions produce as artifacts, chapter 8, Domain Events, and chapter
10, Aggregates.

Brandolini did not invent domain events or Domain-Driven Design. Both trace to
Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
Software*, Addison-Wesley, 2003, which established the ubiquitous language,
the bounded context, and the aggregate as the load bearing concepts of the
approach (Wikipedia, "Domain-driven design",
https://en.wikipedia.org/wiki/Domain-driven_design, verified 2026-08-02, which
states the term was coined by Evans in that 2003 book). What Brandolini added
was a facilitation format, a specific sequence of sticky note colors and a
specific room setup, for getting a cross functional group of people to
name those domain events together instead of one architect inferring them
alone at a whiteboard.

Three named variants of the workshop have become standard enough to carry
their own names, and this entry treats all three as members of the same
pattern family because they share the same core mechanic, orange stickies for
events walked out in time order, only the scope and depth differ.

- **Big Picture EventStorming.** The widest scope, used to explore an
  entire business domain or a whole product, often the first workshop a team
  runs and often the one that reveals the shape of future bounded contexts.
- **Process Modeling EventStorming.** A narrower scope, one business process,
  adding actors, commands, and policies to the event timeline so the group can
  agree on who does what and in response to what.
- **Design Level EventStorming.** The narrowest scope, one or a few aggregates,
  close enough to code that the output maps almost directly onto classes,
  commands, and events in an implementation.

This three way split is documented across multiple independent secondary
sources, including Baeldung, "Event Storming",
https://www.baeldung.com/cs/event-storming-workshop, verified 2026-08-02, and
NimblePros, "Big Picture EventStorming for Discovery",
https://blog.nimblepros.com/blogs/big-picture-eventstorming-for-discovery/,
verified 2026-08-02, both of which name the same three levels in the same
order.

## 2. Problem and context

A team is about to build software for a business domain nobody on the team
fully understands alone. The domain experts know the business but do not
think in terms of aggregates, transactions, or bounded contexts. The
engineers know how to build software but do not know, without being told,
that a cancelled order behaves differently depending on whether payment had
already cleared, or that "customer" means something different to sales than
it means to support. The gap between what the business actually does and what
the team believes the business does is where defects, missing edge cases, and
entire misdesigned subsystems come from, and that gap is invisible until
someone builds the wrong thing and ships it.

The traditional way to close that gap is a requirements document, written by
a business analyst after interviewing stakeholders one at a time, then handed
to engineering. This produces a single, filtered, already-interpreted version
of the domain, written in whatever vocabulary the analyst happened to choose,
reviewed by people who were not in the room when it was written. Divergent
opinions between stakeholders get resolved silently by the document's author,
which means the disagreement resurfaces later, in production, as a bug report,
rather than earlier, on a wall, where it is cheap to argue about.

Event Storming addresses a narrower and more concrete problem than
requirements gathering in general. It exists to lay out the sequence of
business significant occurrences in a domain, in the actual chronological
order they happen, with everyone who has a stake in that order standing in
the same room disagreeing about it out loud until they stop disagreeing. The
context in which this is the right tool is a domain that is genuinely
complex, involves more than one department or role, and has enough tribal
disagreement that a single interview subject cannot be trusted to describe it
completely. A domain that one person already understands end to end, or a
domain that is a thin wrapper over a well documented external API, does not
have this problem, and running a four hour workshop against it burns a room
full of expensive people's time to arrive at what one engineer already knew.

## 3. Forces

**Breadth versus depth.** A workshop that tries to cover the whole business in
one session produces a shallow map of everything. A workshop scoped to one
process produces a deep map of one thing. Big Picture, Process Modeling, and
Design Level EventStorming exist precisely because this force cannot be
resolved once, it has to be chosen per session, and the three named variants
are the three points on that scale the community settled on.

**Facilitation cost versus documentation quality.** The technique requires an
unbroken wall or a very large virtual canvas, four to eight hours of
uninterrupted time from every domain expert who matters, and a skilled
facilitator who can keep the group moving without steering the content. That
is expensive to schedule and expensive to run. The payoff is a shared
artifact everyone in the room helped build and therefore trusts, which a
written specification rarely achieves, because nobody but the author trusts a
document they did not write.

**Divergent thinking versus convergent thinking.** The chaotic exploration
phase, where anyone can slap an orange sticky on the wall for any event they
believe happens, deliberately tolerates duplication, disagreement, and noise.
The later phases, hotspots, actors, and the aggregate boundary discussion,
deliberately narrow that noise down to a small number of agreed artifacts.
Doing both in the same room, on the same afternoon, is the hardest part of
facilitating the format, because groups want to converge too early, out of
social pressure, before every disagreement has actually come out.

**Physical presence versus remote participation.** The original format is
built around standing at a physical wall, walking left to right along a
timeline, and being able to point at a specific sticky note while forty other
people watch you point at it. Remote and hybrid variants using a shared
digital canvas trade the physical presence that keeps people engaged for the
ability to include a domain expert who is not in the same building, and this
trade is one of the most discussed adaptations of the format since 2020.

**Cost of the workshop versus cost of the wrong system.** The forces above all
resolve to one underlying trade. A day spent in a room full of sticky notes
is a day not spent writing code, and stakeholders who are used to being asked
for a two paragraph requirements summary can find the format's apparent
messiness alarming. The pattern favours discovering a wrong assumption on a
wall, where correcting it costs one sticky note, over discovering the same
wrong assumption in a shipped aggregate, where correcting it costs a
migration.

## 4. Applicability and non-applicability

Reach for Event Storming when the following hold.

- The domain is genuinely complex, has real branching business rules, and
  more than one role in the organisation has partial and possibly conflicting
  knowledge of how it actually works.
- The people who understand the domain and the people who will build the
  software can be in the same room, physical or virtual, for the length of the
  session, and are willing to disagree openly.
- The team is at, or near, the start of a project, a major feature, or a
  boundary decision, where the cost of discovering a wrong assumption is still
  low.
- The goal includes finding the seams for bounded contexts, not merely
  listing features, because the timeline naturally shows where one group's
  vocabulary and cadence diverges from another's.
- Legacy behaviour needs to be reverse engineered from people's heads because
  the original decisions were never written down, and the system that encodes
  them is now too large to read start to finish.

Do NOT reach for Event Storming when any of the following hold, and treat this
list as at least as important as the one above.

- The domain is small, well understood by a single engineer, or is a thin
  proxy over a third party API whose behaviour is defined by that third
  party's own documentation, not by internal business rules. Running a
  workshop here manufactures disagreement about something nobody actually
  disagrees about.
- The organisation cannot get the actual domain experts, the people who do
  the work, into the room, and the workshop would instead be staffed by their
  managers speaking on their behalf. A workshop built on secondhand knowledge
  reproduces the same telephone game problem as a requirements document,
  while costing more people's time.
- The team needs an answer to a narrow, already well scoped question, such as
  which field format a specific API should use. That is a design conversation
  between two or three people, not a cross functional group exercise.
- The team is under a hard deadline measured in hours, not weeks, where the
  time cost of a multi hour workshop cannot be absorbed regardless of its
  long run value.
- The desired outcome is a piece of software architecture on its own, with no
  business process behind it, for example a caching layer or a build
  pipeline. Event Storming models business events, not infrastructure
  concerns, and forcing infrastructure work through the format produces
  sticky notes that are really just task names wearing an orange color.
- The organisation has already run the same session for the same scope
  recently and nothing material has changed. Repeating the workshop out of
  ritual, rather than because new information or new stakeholders exist,
  wastes the room's goodwill for the next time the technique is genuinely
  needed.

## 5. Structure

Event Storming is a facilitation format, not a code structure, so its
participants are workshop roles and the artifact types they produce, rather
than classes and interfaces.

- **The facilitator.** Owns the process, not the content. Keeps the timeline
  moving left to right, calls out gaps, hotspots, and disagreements, and
  resists the temptation to answer domain questions themselves even when they
  know the answer, because the point is for the room to reach the answer
  together.
- **Domain experts.** The people who actually perform or are accountable for
  the business process being modelled. They are the primary source of the
  orange domain event stickies and the primary arbiters when two other
  participants disagree about ordering.
- **Engineers and architects.** Listen for the shape of aggregates, bounded
  contexts, and integration points hiding inside what the domain experts
  describe, and raise technical constraints, such as an external system's
  latency, that shape which events are even possible to react to
  synchronously.
- **Domain event.** An orange sticky note recording something that happened
  and mattered to the business, named in the past tense as a noun and verb
  pair, for example OrderPlaced or PaymentDeclined. This is the unit the
  entire timeline is built from. Baeldung, "Event Storming",
  https://www.baeldung.com/cs/event-storming-workshop, verified 2026-08-02,
  and the Wikipedia "Event storming" article both confirm orange as the
  domain event colour and the past tense naming convention.
- **Command.** A blue sticky note recording an intention, the thing that,
  when carried out, produces one or more domain events. Named in the
  imperative, for example PlaceOrder or DeclinePayment.
- **Actor.** A yellow sticky note naming who or what issues a command, a
  customer, a support agent, or an external system acting on the domain's
  behalf.
- **Aggregate.** In Design Level EventStorming, a sticky note, commonly
  yellow or a distinct pale colour depending on the team's legend, marking
  the consistency boundary that accepts a command and decides which events,
  if any, to emit. This is where the workshop output connects directly to
  Eric Evans' aggregate concept.
- **Policy.** A lilac or purple sticky note recording an automated
  "whenever X happens, then Y should happen" reaction, the glue between one
  aggregate's event and another aggregate's command, and frequently the
  first sighting of a process manager or saga.
- **External system.** A pink sticky note marking a system outside the team's
  control that either triggers or is triggered by the process, a payment
  gateway, a shipping carrier, a third party identity provider.
- **Hotspot.** A red or orange-red sticky note, sometimes shaped as a
  question mark card, marking an unresolved disagreement, a known problem, or
  an open question the group could not settle in the room. Hotspots are a
  first class output of the workshop, not a failure of it.
- **Read model or view.** A green sticky note recording information a user or
  another system needs to see in order to issue the next command correctly, a
  bridge to the query side of the eventual implementation.
- **The timeline.** The horizontal axis of the physical or virtual wall,
  running left to right in chronological order, which is the one piece of
  structure every variant of the workshop shares and the one rule that is
  never optional.

## 6. ASCII structure diagram

```
  TIMELINE (left = earlier, right = later)
  --------------------------------------------------------------->

  [Actor]      [Command]        [Aggregate]      [Domain Event]
  Customer  -->  PlaceOrder --> OrderAggregate --> OrderPlaced
  (yellow)       (blue)         (yellow/tan)        (orange)
                                                        |
                                                        v
                                                    [Policy]
                                              "whenever OrderPlaced,
                                               then ReserveStock"
                                                     (lilac)
                                                        |
                                                        v
  [External Sys]                              [Command]
  Warehouse   <-------------------------------  ReserveStock
  (pink)                                          (blue)
                                                        |
                                                        v
                                              [Aggregate]      [Domain Event]
                                              StockAggregate --> StockReserved
                                              (yellow/tan)         (orange)
                                                                       |
                                                                       v
                                                                  [Hotspot]
                                                              "what happens if
                                                               stock runs out
                                                               mid-order?"
                                                                (red, unresolved)
```

## 7. Dynamics

The workshop itself, not the software it produces, has a runtime, and that
runtime runs through a fixed sequence of phases regardless of which of the
three scoped variants is being run. The exact phase names vary slightly by
source, but the sequence below is the one used consistently across
Brandolini's own material, Baeldung's summary, and NimblePros's guide.

```
PHASE 1  Chaotic Exploration
  every participant independently writes orange domain event stickies
  no discussion yet, duplicates and disagreement are expected and welcome
  facilitator's only job here is to keep the flow of stickies moving

PHASE 2  Timeline Enforcement
  the group, together, arranges every sticky left to right in time order
  duplicates get merged, near-duplicates get argued about out loud
  gaps in the story become visible as physical gaps on the wall

PHASE 3  Hotspot Identification
  the group marks every point of disagreement or open question with
  a hotspot sticky, rather than silently resolving it in the room
  this phase is where hidden business rules and edge cases come out

PHASE 4  Actors and Commands
  for each event, the group asks who or what caused this and adds
  the actor (yellow) and the command (blue) that produced the event

PHASE 5  Aggregates and Boundaries  (Design Level EventStorming only)
  the group groups commands and events under the aggregate that
  owns the consistency decision, revealing candidate bounded contexts
  where clusters of aggregates share vocabulary but not with their
  neighbouring clusters

PHASE 6  Policies and Read Models
  the group marks automated reactions (policies) between aggregates,
  and the information (read models) an actor needs before issuing
  their next command, closing the causal loop of the process
```

The chaotic-exploration-then-converge shape is the same social dynamic used
by other divergent-then-convergent facilitation techniques, brainstorming
followed by dot voting, and its purpose is identical, generate more raw
material than any one person would produce alone, then let the group's
disagreement do the filtering instead of a single author's judgment doing it.

## 8. Implementation variants

**Physical wall with paper sticky notes.** The original and still the
strongest form for co-located teams, using a long roll of butcher paper taped
to a wall so the timeline can be as long as the room allows and can be rolled
up and stored between sessions. The tactile act of writing and repositioning a
physical note is frequently cited by facilitators as producing more honest,
less filtered contributions than typing into a shared document, because
nobody has to wait their turn to speak and the note itself, not a verbal
interruption, carries the disagreement.

**Digital canvas tools.** Miro and Mural are the two most commonly cited
platforms for remote or hybrid EventStorming, each offering purpose built
sticky note color palettes matching the standard legend, and each supporting
a very large, effectively unbounded, virtual canvas that a physical wall
cannot match. The trade off is a loss of the physical presence signal, since
a participant can silently disengage from a shared screen in a way they
cannot disengage while standing at a wall. NimblePros, "Big Picture
EventStorming for Discovery",
https://blog.nimblepros.com/blogs/big-picture-eventstorming-for-discovery/,
verified 2026-08-02, weighs remote-versus-physical facilitation trade
offs directly.

**Machine readable modelling with Context Mapper.** Context Mapper, an open
source tool built on the Context Mapper DSL (CML), provides language
constructs for documenting the output of an EventStorming session after the
workshop ends, capturing domain events, commands, aggregates, bounded
contexts, and subdomains as structured text rather than as photographs of a
wall. Once captured, the same model can generate UML class diagrams,
PlantUML context maps, and MDSL service contracts, and can have automated
architectural refactorings applied to it. Context Mapper documentation,
"Model Event Storming Results in Context Mapper",
https://contextmapper.org/docs/event-storming/, verified 2026-08-02. This
variant treats the workshop as an upstream step feeding a formal, versionable
model, rather than as the final artifact.

**Direct code generation from Design Level output.** In its narrowest, Design
Level form, the sticky notes map so closely onto an event sourced or
event driven implementation, command handler receives command, aggregate
decides, aggregate emits event, that some teams write the aggregate
skeletons directly from a photograph of the wall during the same session,
treating the workshop as executable specification rather than as upstream
documentation. This is the variant closest to Design Level EventStorming as
named by Baeldung and the archiblog series on the same subject. Katarzyna
Starachowicz, "Design Level Event Storming",
https://katarzyna-starachowicz.github.io/design-level-event-storming, verified
2026-08-02.

**Solo or pair EventStorming.** A degenerate but documented variant where one
or two engineers who already have partial domain access run a compressed
version of the format against a legacy codebase or an existing API, using
the technique's chronological-events-first discipline as a personal thinking
tool rather than a group facilitation exercise. This loses the primary value
of the pattern, the cross checking that many stakeholders disagreeing
provides, and should be understood as a degraded fallback, not a first
choice.

## 9. Known production uses

**LEGO Group.** LEGO's internal engineering team, publishing under the "LEGO
Engineering" Medium publication, describes a squad ("Pirates") explicitly
planning EventStorming workshops as the first step before designing a
serverless, event driven architecture on AWS, built around Amazon
EventBridge and organised around Domain-Driven Design bounded contexts and
aggregates. The article frames the workshop's purpose directly. "EventStorming
is a workshop activity. Everyone participating in the system somehow is
invited, developers, domain experts, and business decision-makers alike."
Monique Grinstein, "Cloudy with a chance of Event Storming", LEGO
Engineering on Medium,
https://medium.com/lego-engineering/cloudy-with-a-chance-of-event-storming-73817afe10c2,
verified 2026-08-02.

**Heritage Bank.** Heritage Bank, described as Australia's largest
customer-owned bank, used Event Storming as part of a transformation
programme for a New Banking Platform project supporting real-time payments
between financial institutions in Australia, documented by a practitioner
account of applying the technique inside the bank's transformation work.
Sandra Arps, "Using 'Event Storming Practice' at Heritage Bank", LinkedIn,
https://www.linkedin.com/pulse/using-event-storming-practice-heritage-bank-sandra-arps,
verified 2026-08-02.

**Context Mapper (open source tooling).** The Context Mapper project,
maintained as an open source DSL and set of Eclipse and VS Code tooling for
strategic Domain-Driven Design, ships a dedicated language feature set for
capturing EventStorming workshop results, domain events, commands,
aggregates, bounded contexts, and subdomains, and generating downstream
artifacts, graphical context maps, PlantUML diagrams, and MDSL service
contracts, from that captured model. The project's own documentation states
plainly that Context Mapper "supports most of these concepts, and can
therefore be used to document the output of an event storming workshop."
Context Mapper documentation, "Model Event Storming Results in Context
Mapper", https://contextmapper.org/docs/event-storming/, verified
2026-08-02. This is production use in the sense that a maintained, versioned
open source tool exists specifically to formalise EventStorming's raw
output, evidence that the technique's artifacts are treated as durable,
machine-processable inputs to real system design work, not merely as a
one-off ice breaker exercise.

## 10. Consequences

Positive consequences.

- A single shared artifact that every participant helped construct, which
  carries more organisational trust than a document written by one author
  and reviewed by the rest, because disagreement was resolved, or explicitly
  left unresolved as a hotspot, in front of everyone rather than edited away
  silently.
- Hidden business rules and edge cases come out earlier and more cheaply than
  they would in code review or production, because the format's Hotspot
  Identification phase makes airing a disagreement the explicit goal of a
  whole step, rather than an unwelcome interruption to a meeting agenda.
- The chronological, event first framing naturally shows candidate bounded
  context boundaries, since a cluster of events that shares vocabulary,
  cadence, and ownership with its neighbours on the timeline but not with
  events further away is exactly the seam a bounded context split should
  follow.
- The ubiquitous language a team needs for the rest of a Domain-Driven Design
  effort gets built as a byproduct of the workshop, because every sticky note
  is a name the room agreed on together, rather than a name one engineer
  chose alone and everyone else adopted by inertia.
- Design Level output maps close enough to code that it shortens the gap
  between the business agreeing on how the process works and the code doing
  what the business agreed on.

Negative consequences.

- The format costs real, scarce time from the most senior and most expensive
  people in the room, domain experts and architects, and that cost is
  incurred up front, before any code exists, which makes it politically
  harder to schedule than a task that produces visible progress the same day.
- A workshop run without the actual domain experts, using proxies who
  believe they know the domain, reproduces the exact telephone game problem
  it is meant to solve, while looking, superficially, like it solved it,
  because a wall full of orange stickies feels authoritative regardless of
  whether the people who wrote them actually knew what they were writing.
- Poor facilitation, allowing the room to converge too early, letting one
  loud voice steer the whole timeline, or failing to record hotspots as
  genuinely unresolved, produces an artifact that looks complete but encodes
  the same single-author bias the format exists to remove.
- The output is a photograph of a wall, or a digital board export, neither of
  which is directly executable or diffable the way source code is, so
  without a deliberate follow up step, formal modelling in a tool such as
  Context Mapper, or direct translation into aggregate skeletons, the
  workshop's insight decays and drifts out of sync with the eventual
  implementation.
- The technique answers what happens and in what order, it does not answer
  how the process should be implemented, and teams that mistake a finished
  EventStorming board for a finished architecture skip the harder work of
  actually deciding aggregate boundaries, consistency guarantees, and
  failure handling.

## 11. Failure modes and misuse

**Symptom.** The workshop produces a wall full of stickies that reads, on
review a week later, as a list of CRUD operations, CreateOrder, UpdateOrder,
DeleteOrder, rather than as meaningful business occurrences.
**Cause.** The facilitator allowed the room to write events at the level of
database operations instead of business significance, often because
engineers, who think in terms of persistence, outnumbered or outtalked
domain experts, who think in terms of outcomes.
**Fix.** Re-anchor the room on why a domain expert would care that this
happened, and explicitly reject a sticky if the answer is only that the
database changed. A useful test is whether the event name would appear in a
sentence a business stakeholder might actually say out loud, "the order was
placed," rather than one only a database administrator would say, "the
orders table got a new row."

**Symptom.** Two departments leave the workshop still disagreeing about what
"customer" means, and the disagreement resurfaces three sprints later as a
production incident where one service's customer record silently
overwrites another's.
**Cause.** The facilitator treated a vocabulary clash as noise to smooth over
in the room, rather than as a hotspot to capture and escalate, because
resolving it in the moment felt more productive than leaving it visibly
open.
**Fix.** Trust the hotspot mechanism. An unresolved vocabulary clash, marked
explicitly and escalated to the people with authority to decide it, is a
successful outcome of the workshop, not a failed one. The failure mode is
suppressing the disagreement, not having it.

**Symptom.** The team runs a well attended Big Picture EventStorming
session, everyone leaves energised, and six months later nobody can find the
photographs, nobody remembers which decisions were made, and the next new
hire re-litigates questions the workshop already settled.
**Cause.** The workshop's output was never captured in a durable, searchable
form. A digital canvas export or a phone photograph of a physical wall is not
findable the way a document or a modelling tool's saved file is.
**Fix.** Assign a concrete, named follow up step in the same session the
workshop happens, transcribing the board into a Context Mapper model, a wiki
page organised by bounded context, or aggregate skeletons in code, before the
room disperses and the shared memory of the session starts to fade.

**Symptom.** A Design Level EventStorming session produces an aggregate
boundary that, once implemented, requires a distributed transaction across
two services to maintain, and the team only discovers this during
implementation.
**Cause.** The workshop identified events and commands correctly but never
explicitly interrogated which of them must be transactionally consistent
versus which can be eventually consistent through a policy, a distinction
the sticky note legend does not force the room to make explicit.
**Fix.** Add an explicit consistency question to the Design Level phase,
whether a command's effect and an event's emission can happen in one
transaction or whether a policy has to bridge them, and mark the answer on
the board itself, because this is exactly the boundary decision that Eric
Evans' aggregate concept exists to make, and it should not be left implicit.

**Symptom.** Remote participants disengage silently during a virtual
EventStorming session, and the resulting board's content mostly traces back
to two or three voices even though ten people were invited.
**Cause.** The physical-presence social pressure that keeps a person
engaged while standing at a wall does not transfer to a shared screen, where
a participant can mute their camera and stop contributing without the
facilitator noticing in real time.
**Fix.** Structure explicit rounds where every participant is individually
prompted to add at least one sticky before the group moves to discussion,
rather than relying on the free-for-all model that works at a physical wall,
and keep sessions shorter than the four to eight hour physical format to
match remote attention spans.

## 12. Trade-off matrix

| Force | Event Storming | Written requirements document | Interview-then-write (analyst driven) | Domain Storytelling |
|---|---|---|---|---|
| Whose vocabulary wins | The room's, negotiated live | The author's, chosen alone | The analyst's, chosen after interviews | The room's, narrated as a story |
| Cost to run | High, multi-hour cross functional session | Low per document, high in review cycles | Medium, sequential interviews plus writing | Medium, structured narration session |
| Airs disagreement | Explicitly, via hotspots | Rarely, disagreement gets silently resolved by the author | Sometimes, if interviewees contradict each other and the analyst notices | Somewhat, through the story's narrator picking one version |
| Chronological ordering | Central to the format, the timeline is enforced | Optional, often organised by feature instead | Optional, depends on the analyst's structure | Central, the story is inherently sequential |
| Natural bounded context clues | Strong, clusters emerge from the wall | Weak, requires separate architectural analysis | Weak to moderate, depends on analyst skill | Moderate, actor-and-activity groupings hint at context |
| Best scope | Complex, cross departmental domains | Well understood, low ambiguity domains | Medium complexity, limited stakeholder availability | Process focused, single narrator domains |
| Artifact durability without follow up | Low, needs formal capture | High, the document is already durable | High, the document is already durable | Low, needs formal capture |

Domain Storytelling, developed by Stefan Hofer and Henning Schwentner, is a
distinct, named alternative that also uses a picture-language and a narrator
to model a domain collaboratively, and it is included here as the closest
named competitor to Event Storming rather than as a strawman, since both
techniques target the same problem, drawing out a shared domain understanding
from a group, but differ in that Domain Storytelling is built around a single
narrator telling a coherent story with a pictographic language, while Event
Storming is built around many participants independently offering events
that then get reconciled into one timeline.

## 13. Related and incompatible patterns

**Domain Event.** Event Storming's entire output is, literally, a wall of
domain event candidates. The relationship is closest to a producer and its
product, the workshop is the process, the domain event is the artifact type
the process is organised around naming.

**Bounded Context.** A well run Big Picture or Process Modeling session
routinely shows the seams where vocabulary and cadence change along the
timeline, and those seams are the primary raw material a team uses to draw
bounded context boundaries afterward. Event Storming does not draw the
boundaries itself, it shows where they are likely to fall, and drawing
them is a deliberate follow up decision, not an automatic output of the wall.

**Ubiquitous Language.** Every sticky note name that survives the Timeline
Enforcement phase, having been argued about and agreed on by the room, is a
candidate term for the team's ubiquitous language. The workshop is one of the
few concrete, repeatable mechanisms for actually building a ubiquitous
language collaboratively, rather than declaring one top down.

**Aggregate Root.** Design Level EventStorming's aggregate boundary
discussion, phase 5 in dimension 7 above, is a direct, hands on rehearsal of
the aggregate root's core responsibility, deciding which commands it accepts
and which events it is allowed to emit as a result. A team that has never run
a Design Level session but is trying to design aggregates from a written
specification alone is doing the same decision making with less information
in the room.

**Process Manager.** The lilac policy stickies that bridge one aggregate's
event to another aggregate's command are frequently the first sighting of a
process manager, once a policy needs to track state across more than two
steps, remember partial progress, or handle a timeout or compensation, it has
outgrown a simple policy and needs a dedicated process manager or saga to
own that state.

**Context Map.** Where a project runs Event Storming across an entire
organisation's set of domains, rather than one bounded context at a time, the
clusters that fall out of the session become the nodes of a context map, and
the disagreements captured as hotspots between two clusters often become the
map's documented relationship type, conformist, customer-supplier, or
anticorruption layer, depending on how the two sides resolved, or failed to
resolve, the disagreement.

**Published Language.** When a hotspot resolves into an agreement that two
bounded contexts, named during the same workshop, need a stable shared
vocabulary to integrate through, that agreement is the seed of a published
language, and the workshop is frequently where the need for one is first
noticed, well before either team has written an integration contract.

No pattern in this catalog is actively incompatible with Event Storming in
the sense of producing contradictory or unsafe behaviour if combined, because
Event Storming is a modelling technique that precedes
implementation, not a runtime pattern that competes for the same
responsibility as another runtime pattern. The closest thing to an
incompatibility is scope mismatch, running Design Level EventStorming against
a domain that has not yet had a Big Picture session risks designing precise
aggregate boundaries for a process the room does not yet understand at a
larger scale, which is a sequencing problem rather than a structural
incompatibility.

## 14. Refactoring path in and out

Introducing Event Storming into a team that has never used it, step by step.

1. Pick the narrowest defensible scope for the first session. A single
   painful business process, not the whole company, is easier to schedule,
   easier to keep coherent, and produces a visible win the team can point to
   when asking to run the next one.
2. Identify and personally invite the actual domain experts who perform the
   process, by name, rather than sending a generic calendar invite to a
   department. A session without the right people in the room produces a
   confident looking artifact built on secondhand knowledge, which is worse
   than no artifact at all because it is trusted.
3. Book an unbroken block of time, and a wall or virtual canvas large enough
   that the timeline will not need to wrap. Running out of space forces
   premature convergence, exactly the failure this format is designed to
   avoid.
4. Run Chaotic Exploration with almost no rules beyond one orange sticky, in
   the past tense, per event. Resist explaining what a good event looks
   like beyond that single rule, the room will correct itself during
   Timeline Enforcement.
5. Enforce the timeline together, out loud, and capture every disagreement
   as a hotspot rather than resolving it silently at the wall. This step is
   where the format's value is actually generated, and rushing it defeats
   the point of having run the workshop at all.
6. If the goal includes implementation, follow with a Design Level session
   scoped to one or two of the clusters the Big Picture session revealed,
   adding actors, commands, aggregates, and policies to the events that
   survived.
7. Capture the result durably the same day, in a modelling tool such as
   Context Mapper, in a wiki page organised by the bounded contexts the
   session revealed, or directly as aggregate and event class skeletons in
   code, before institutional memory of the session decays.

Removing Event Storming's artifacts, or moving away from a session's output,
step by step.

1. Recognise the trigger for removal correctly. The board itself does not
   go stale in the way code does, since it is a point-in-time snapshot of a
   group's understanding, not a live system. The removal question is really
   whether that snapshot is still trustworthy, and the trigger is usually a
   material change to the actual business process, a merger, a regulation, a
   new product line, not the mere passage of time.
2. Before discarding an old session's captured model, diff the current
   understanding of the process against it explicitly, in the same
   collaborative style, asking which of these events, commands, and
   policies no longer reflect how the business actually works. This
   preserves institutional memory of why something changed, rather than
   silently deleting a now-inaccurate document.
3. Run a smaller, targeted follow up session scoped only to the part of the
   process that changed, rather than a full re-run of the original Big
   Picture session, since the parts of the domain that did not change do not
   need to be re-argued.
4. Update the durable, formally captured artifact, the Context Mapper model,
   the wiki page, or the code, so the artifact of record reflects the new
   session's output rather than leaving two conflicting sources of truth in
   circulation.
5. Where the change is significant enough to shift a bounded context
   boundary, this is not a removal of Event Storming's output, it is a
   Context Map refactoring, follow the Context Map entry's own guidance for
   moving a relationship between two contexts.

## 15. Testing and verification

Event Storming's own workshop output is not itself executable, so testing
here means verifying the artifact's quality and its downstream fidelity,
rather than running unit tests against a wall of stickies.

Verifying the workshop's own output before the room disperses is the first
and cheapest check. A facilitator should walk the finished timeline out loud,
event by event, and ask the room to confirm each transition still makes
sense once read back in full, since gaps and contradictions that were
invisible while a section was being built are often obvious once the whole
sequence is read straight through. This single walkthrough step catches a
meaningful share of the ordering mistakes that would otherwise show up later
as a confusing sequence diagram or an aggregate that cannot actually enforce
the invariant the team believed it enforced.

Verifying that hotspots were actually resolved, not merely recorded, is a
second, deliberately delayed check. A hotspot captured in a session is only
useful if someone with the authority to decide it follows up, so a
lightweight tracking mechanism, even a simple list with an owner and a due
date, is the practical verification step that turns writing a hotspot down
into someone actually answering it.

Once a session's output feeds an implementation, the standard testability
properties of the resulting design apply, and Event Storming's Design Level
output makes several of them easier to achieve than an ad hoc design would.
Because each aggregate on the board was explicitly scoped to the commands it
accepts and the events it may emit, a unit test for that aggregate can be
written in the same given-command, then-event shape the workshop itself
used, given the aggregate was in a starting state, when a command is issued,
then a specific event is emitted or the command is rejected. This shape,
directly derived from the workshop's own command-and-event vocabulary, is a
natural fit for behaviour driven test frameworks and is one of the more
concrete practical benefits Design Level EventStorming provides over a
specification with no such vocabulary.

Where a policy connects two aggregates, the corresponding test is an
integration or contract test asserting that the triggering event does in
fact cause the expected downstream command to be issued, ideally using a
consumer driven contract so the two owning teams do not have to keep a
manually synchronised understanding of the interface between them in sync by
hand.

Where Context Mapper or an equivalent formal tool is used to capture the
session, the tool's own model validation, checking that every referenced
event, command, and aggregate is actually defined, functions as a structural
verification step that a purely photographic or free text capture of the
same session cannot provide, since a photograph cannot detect a dangling
reference to an event nobody ever defined.

## 16. Observability signals

Event Storming produces a design artifact, not a running system, so its
observability signals fall into two distinct categories, signals about the
health of the practice itself inside an organisation, and signals in the
running software that indicate whether the session's design assumptions are
holding up in production.

Signals about the practice. How long ago was the most recent session for a
given bounded context, and does that gap correlate with the domain having
materially changed since. How many hotspots from the last session remain
unresolved and unassigned, since a growing backlog of unresolved hotspots is
a leading indicator that the practice is producing findings faster than
the organisation is acting on them. Whether new team members can locate the
captured artifact for a given process without asking a colleague, a rough
proxy for whether the session's insight survived past the room it was
generated in.

Signals in the running software. Because Design Level EventStorming names
events explicitly, in past tense business language, and because a healthy
implementation of that design typically emits those exact named events on a
message bus or an event log, the presence, absence, and rate of a specific
named event, OrderPlaced, PaymentDeclined, in production telemetry is a
direct, checkable link back to the workshop's own vocabulary. A domain event
that the workshop identified as important but that never actually fires in
production telemetry is a signal that either the corresponding code path is
unreachable, or the implementation silently diverged from the agreed design.
Conversely, an event firing at a rate or with a payload shape the workshop
never discussed is a signal that the domain has drifted since the session and
a follow up workshop, per dimension 14's removal path, is warranted.

Where a policy from the board was implemented as an asynchronous reaction to
an event, the standard event driven observability practice applies, tracing
the causal chain from the triggering event through the policy to the
resulting command, and alerting when that chain breaks, when an event is
published but the expected downstream command never follows within an
acceptable window.

## 17. Security and privacy implications

Event Storming's security and privacy implications are mostly about the
process, not the software, and are analytical judgment rather than sourced
fact, stated here as such.

The workshop's biggest privacy exposure is the content on the wall itself.
Because participants are encouraged to write real, concrete examples, such
as a customer complaining their order was late, domain experts sometimes
introduce real customer names, real account numbers, or other identifying
detail onto a physical wall or a shared digital canvas that may be
photographed, exported, or left accessible to a wider audience than the
workshop's original attendees. A facilitator should set an explicit house
rule at the start of the session that examples use fictitious names and
placeholder identifiers, the same discipline already expected of test data
and demo environments, and should treat the finished board's export with the
same access control rigor as any other document that might contain
personally identifiable information.

A second, more architectural implication is that the aggregate and bounded
context boundaries a session reveals frequently double as the natural
boundaries for data ownership and access control in the resulting system,
since a bounded context that owns a customer's data as part of enforcing its
own business invariants is also the natural point to enforce who is allowed
to read or write that data. A team that runs Design Level EventStorming and
then implements the resulting aggregates without also carrying the session's
implicit ownership boundaries into the authorization model has left value on
the table, the workshop already did the hard thinking about who is
accountable for which data, and skipping that carry over means re-deriving
the same boundary later, under worse conditions, once an access control
incident forces the question.

The workshop raises no cryptographic, network, or platform level security
concerns of its own, since it produces a model, not a running system, and any
security property of the eventual implementation, encryption in transit,
authentication of the actors it names, integrity of the event log, is
determined by how that implementation is built, not by the technique used to
design it.

## 18. References

- Wikipedia, "Event storming",
  https://en.wikipedia.org/wiki/Event_storming, verified 2026-08-02.
- Wikipedia, "Domain-driven design",
  https://en.wikipedia.org/wiki/Domain-driven_design, verified 2026-08-02.
- eventstorming.com, official EventStorming site listing Alberto Brandolini
  as the author of *Introducing EventStorming*,
  https://www.eventstorming.com/, verified 2026-08-02.
- Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
  Software*, Addison-Wesley, 2003.
- Vaughn Vernon, *Implementing Domain-Driven Design*, Addison-Wesley, 2013,
  chapter 8 (Domain Events) and chapter 10 (Aggregates).
- Baeldung on Computer Science, "Event Storming",
  https://www.baeldung.com/cs/event-storming-workshop, verified 2026-08-02.
- NimblePros, "Big Picture EventStorming for Discovery",
  https://blog.nimblepros.com/blogs/big-picture-eventstorming-for-discovery/,
  verified 2026-08-02.
- Katarzyna Starachowicz, "Design Level Event Storming", archiblog,
  https://katarzyna-starachowicz.github.io/design-level-event-storming,
  verified 2026-08-02.
- Context Mapper documentation, "Model Event Storming Results in Context
  Mapper", https://contextmapper.org/docs/event-storming/, verified
  2026-08-02.
- Monique Grinstein, "Cloudy with a chance of Event Storming", LEGO
  Engineering on Medium,
  https://medium.com/lego-engineering/cloudy-with-a-chance-of-event-storming-73817afe10c2,
  verified 2026-08-02.
- Sandra Arps, "Using 'Event Storming Practice' at Heritage Bank", LinkedIn,
  https://www.linkedin.com/pulse/using-event-storming-practice-heritage-bank-sandra-arps,
  verified 2026-08-02.

## Code examples

Event Storming is a facilitation technique, not an object oriented design
pattern, so there is no single canonical class structure to implement in
code. What real teams build in code, once a session has run, falls into two
concrete artifacts this section demonstrates, a small validator that checks a
captured board against the standard sticky note legend, catching exactly the
CRUD-disguised-as-domain-events failure mode from dimension 11, and the
resulting Design Level output translated into a minimal aggregate that
accepts a command and emits the domain events the workshop agreed on. The
validator is shown in TypeScript and Python. The Design Level aggregate
translation is shown in Go, using the OrderPlaced and StockReserved events
from the structure diagram in dimension 6.

### TypeScript, board legend validator

```typescript
type NoteType = "event" | "command" | "actor" | "policy" | "external" | "hotspot" | "readmodel";

interface StickyNote {
  type: NoteType;
  text: string;
  position: number;
}

const PAST_TENSE_ENDINGS = ["ed", "d"];

function looksImperative(text: string): boolean {
  const firstWord = text.trim().split(/\s+/)[0] ?? "";
  return !PAST_TENSE_ENDINGS.some((suffix) => firstWord.toLowerCase().endsWith(suffix));
}

function validateBoard(notes: StickyNote[]): string[] {
  const problems: string[] = [];
  const events = notes.filter((n) => n.type === "event");

  for (const event of events) {
    if (looksImperative(event.text)) {
      problems.push(
        `Event "${event.text}" reads as a command, not a past tense occurrence.`,
      );
    }
    if (/^(create|update|delete)[a-z]*$/i.test(event.text.replace(/\s+/g, ""))) {
      problems.push(
        `Event "${event.text}" reads like a CRUD operation, not a business occurrence.`,
      );
    }
  }

  const sorted = [...notes].sort((a, b) => a.position - b.position);
  const positions = sorted.map((n) => n.position);
  if (new Set(positions).size !== positions.length) {
    problems.push("Two or more notes share the same timeline position.");
  }

  return problems;
}

const board: StickyNote[] = [
  { type: "actor", text: "Customer", position: 1 },
  { type: "command", text: "PlaceOrder", position: 2 },
  { type: "event", text: "OrderPlaced", position: 3 },
  { type: "event", text: "CreateOrder", position: 4 },
];

const issues = validateBoard(board);
for (const issue of issues) {
  console.log(issue);
}
```

Ran with `npx tsc --strict --noEmit` to type check, and with `node` after
transpiling to JavaScript with `npx tsc`. Output on the sample board above.

```
Event "CreateOrder" reads as a command, not a past tense occurrence.
Event "CreateOrder" reads like a CRUD operation, not a business occurrence.
```

### Python, board legend validator (independent reimplementation)

```python
from dataclasses import dataclass
import re

@dataclass
class StickyNote:
    note_type: str
    text: str
    position: int

CRUD_PATTERN = re.compile(r"^(create|update|delete)[a-z]*$", re.IGNORECASE)

def looks_imperative(text: str) -> bool:
    first_word = text.strip().split()[0] if text.strip() else ""
    return not first_word.lower().endswith(("ed", "d"))

def validate_board(notes: list[StickyNote]) -> list[str]:
    problems: list[str] = []
    events = [n for n in notes if n.note_type == "event"]

    for event in events:
        if looks_imperative(event.text):
            problems.append(
                f'Event "{event.text}" reads as a command, not a past tense occurrence.'
            )
        if CRUD_PATTERN.match(event.text.replace(" ", "")):
            problems.append(
                f'Event "{event.text}" reads like a CRUD operation, not a business occurrence.'
            )

    positions = [n.position for n in notes]
    if len(set(positions)) != len(positions):
        problems.append("Two or more notes share the same timeline position.")

    return problems

if __name__ == "__main__":
    board = [
        StickyNote("actor", "Customer", 1),
        StickyNote("command", "PlaceOrder", 2),
        StickyNote("event", "OrderPlaced", 3),
        StickyNote("event", "CreateOrder", 4),
    ]
    for issue in validate_board(board):
        print(issue)
```

Ran with `python3 event_storming_validator.py`. Output matched the
TypeScript version exactly, both flags on the CreateOrder sticky.

### Go, Design Level output translated into an aggregate

```go
package main

import "fmt"

type OrderPlaced struct {
	OrderID string
}

type StockReserved struct {
	OrderID string
	SKU     string
}

type PlaceOrder struct {
	OrderID string
	SKU     string
}

type OrderAggregate struct {
	orderID string
	placed  bool
}

func (a *OrderAggregate) Handle(cmd PlaceOrder) (OrderPlaced, error) {
	if a.placed {
		return OrderPlaced{}, fmt.Errorf("order %s already placed", cmd.OrderID)
	}
	a.placed = true
	a.orderID = cmd.OrderID
	return OrderPlaced{OrderID: cmd.OrderID}, nil
}

// ReserveStockPolicy models the lilac "whenever OrderPlaced, then
// ReserveStock" sticky note from the timeline in dimension 6.
func ReserveStockPolicy(evt OrderPlaced, sku string) StockReserved {
	return StockReserved{OrderID: evt.OrderID, SKU: sku}
}

func main() {
	order := &OrderAggregate{}

	placed, err := order.Handle(PlaceOrder{OrderID: "ord-1", SKU: "lego-42100"})
	if err != nil {
		fmt.Println("error:", err)
		return
	}
	fmt.Printf("emitted event: %+v\n", placed)

	reserved := ReserveStockPolicy(placed, "lego-42100")
	fmt.Printf("policy reacted, emitted: %+v\n", reserved)

	_, err = order.Handle(PlaceOrder{OrderID: "ord-1", SKU: "lego-42100"})
	fmt.Println("second command rejected:", err)
}
```

Ran with `go run main.go`. Output.

```
emitted event: {OrderID:ord-1}
policy reacted, emitted: {OrderID:ord-1 SKU:lego-42100}
second command rejected: order ord-1 already placed
```

A Java or Rust translation of the same aggregate would be a mechanical
restatement of the Go version above, one command handler method returning
either an event or a rejection, so it is omitted here rather than padded in
to hit a language count that adds no new insight into the pattern itself.
