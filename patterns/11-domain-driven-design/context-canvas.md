---
name: Context Canvas
slug: context-canvas
family: 11-domain-driven-design
category: Strategic Design
aliases: [Bounded Context Canvas, BC Canvas, Bounded Context Design Canvas]
first_described: "Tune 2019"
maturity: established
related: [bounded-context, context-map, ubiquitous-language, event-storming, core-domain, generic-subdomain, supporting-subdomain, customer-supplier, conformist]
incompatible_with: []
verified: 2026-08-02
---

# Context Canvas

## 1. Name, aliases, and lineage

The community name is the Bounded Context Canvas, most often shortened in
conversation to Context Canvas or BC Canvas. It was created by Nick Tune, a
strategic domain-driven design consultant, as a structured worksheet for
answering the design questions a team must settle before a bounded context is
built. One of the earliest public descriptions of it appears in Nick Tune,
"Modelling Bounded Contexts with the Bounded Context Design Canvas. A Workshop
Recipe", Nick Tune's weird ideas, Medium, published 22 July 2019
(https://medium.com/nick-tune-tech-strategy-blog/modelling-bounded-contexts-with-the-bounded-context-design-canvas-a-workshop-recipe-1f123e592ab
verified 2026-08-02), where Tune writes that he designed the canvas from the
typical flow of the strategic domain-driven design workshops he ran publicly
and privately. That article calls it the Bounded Context Design Canvas, a
naming that later contracted to Bounded Context Canvas as the tool spread.

The tool did not stay fixed. Tune published a revised structure in Nick Tune,
"Bounded Context Canvas V3. Simplifications and Additions", Nick Tune's weird
ideas, Medium, published 12 January 2020
(https://medium.com/nick-tune-tech-strategy-blog/bounded-context-canvas-v2-simplifications-and-additions-229ed35f825f
verified 2026-08-02), which states plainly that the canvas itself is based on
a questionnaire Tune used before it existed as a single-page worksheet, and
which invites readers to change the canvas or design an entirely new one for
their own context. Maintenance of the canvas subsequently moved to a
community repository, ddd-crew/bounded-context-canvas on GitHub, whose README
lists Kenny Baas, Kim Lindhard, Michael Plöd, and Maxime Sanglan-Charlier as
contributors and states the work is licensed under a Creative Commons
Attribution 4.0 International License
(https://github.com/ddd-crew/bounded-context-canvas
verified 2026-08-02). The repository has iterated through published versions
up to a fifth revision, each removing a field readers found confusing or
adding one a facilitator kept drawing by hand.

This entry treats Context Canvas as a strategic design pattern in the
practice sense used throughout this catalog, a named, repeatable technique
with participants and a documented set of failure modes, even though its
first description was a blog post and a downloadable worksheet rather than a
class diagram. Event Storming in this same family carries the identical
shape, a facilitation technique with a lineage, a structure, and known
misuse, and the two tools are frequently run back to back, Event Storming to
discover the boundaries and the Context Canvas to document each one once
found.

## 2. Problem and context

A team has decided, usually from an Event Storming session or from a Context
Map already in hand, that a particular slice of the domain deserves its own
bounded context. The decision to draw the boundary is the easy part. What
happens next is where teams disagree without realising they disagree.

One engineer assumes the new context owns customer email validation because
it already validates addresses. Another assumes it should because the
project board has a ticket labelled "email service" sitting nearest to this
team's swimlane. A third has not thought about ownership at all and starts
writing a repository interface. Three weeks later the context has accreted a
grab bag of responsibilities nobody chose on purpose, its public interface
mixes commands its own team invented with events the upstream team actually
publishes, and nobody can say from memory which two or three neighbouring
contexts it depends on, in which direction, or under what kind of
relationship.

The concrete symptom that motivates reaching for a structured worksheet is
that the boundary was named in a meeting, on a whiteboard photo or in a
single sentence of a Context Map, and that sentence is the entire
specification the implementing team receives. A bounded context, as
described in the Bounded Context entry in this family, is a boundary within
which a model and its ubiquitous language stay consistent, but a boundary
alone says nothing about what the context is for, what business decisions it
owns, what messages cross the boundary in each direction, or what kind of
relationship exists with each neighbour from the taxonomy in the Context Map
entry, upstream, downstream, conformist, customer-supplier and the rest. The
Context Canvas exists to force those questions onto one page, before the
first class is written, so the disagreement happens in a workshop room with
a marker rather than in a pull request review three sprints later.

The context in which this problem shows up is specifically the design phase
of a new bounded context, or the retrofit of documentation onto an existing
one whose boundary already exists in code but was never written down.

## 3. Forces

- **Shared understanding versus speed.** Favours shared understanding. Filling
  the worksheet as a group, rather than one architect writing a design
  document alone, is slower per context but produces a boundary the whole
  team can defend later, because every field was argued over in the room
  rather than handed down.
- **Completeness versus workshop fatigue.** A tension the tool has visibly
  reworked across its own version history. The original 2019 version and the
  2020 V3 revision both trimmed fields readers found redundant, which is
  Tune's own admission in the V3 article that an earlier structure asked for
  more than a room could productively fill in the time available.
- **Documentation currency versus documentation existence.** A filled canvas
  is a snapshot. It favours having a boundary described at all over having a
  boundary described perfectly forever, because the fields it captures, the
  business decisions, the ubiquitous language terms, the collaborators, are
  exactly the ones most likely to drift as the context evolves, and nothing
  in the technique itself enforces that a stale copy gets updated.
- **Precision versus portability.** The worksheet favours a lightweight,
  facilitator-led format over a formal specification language. It sacrifices
  the machine checkability an interface definition language or a formal
  contract would give, in exchange for something a cross-functional room of
  engineers, product owners and domain experts can fill together in an hour
  without training.
- **Local decision versus global consistency.** Each worksheet is filled by
  the team that owns the context, which favours contexts each getting a
  boundary shaped by the people closest to the domain, at the cost that two
  worksheets produced independently can disagree about a shared vocabulary
  term, exactly the gap the Ubiquitous Language and Context Map entries in
  this family exist to reconcile.
- **Cost of adoption.** Low. Favoured deliberately. The tool is a single
  page, free to download under a Creative Commons license, and requires no
  tooling investment, which is why it is cited more often in engineering
  blog posts than in academic literature, a point taken up in dimension 9.

## 4. Applicability and non-applicability

Reach for the Context Canvas when the following hold.

- A team is about to design a new bounded context and needs to force a shared
  answer to what it owns, what it is not responsible for, and what crosses
  its boundary, before code is written.
- An existing bounded context has drifted into an unclear set of
  responsibilities and the team needs a structured artefact to hold the
  retrospective conversation about what belongs and what should be split out.
- Strategic design decisions, whether this context is a Core Domain, a
  Supporting Subdomain or a Generic Subdomain in the sense of the Core
  Domain, Supporting Subdomain and Generic Subdomain entries in this family,
  need to be made explicit and revisited, rather than assumed.
- Onboarding a new engineer or a new team to an existing service, where a
  filled worksheet is a faster and more honest artefact to hand over than a
  stale architecture diagram or an out of date wiki page.
- Following an Event Storming session, to convert the sticky notes clustered
  around a candidate boundary into a documented, reviewable design before
  implementation starts.

Do NOT reach for the Context Canvas in the following cases, and the reason
matters more than the rule.

- **The team is designing inside a single bounded context, not across
  boundaries.** The worksheet documents strategic decisions about a
  context's edges and its relationships to neighbours. Tactical design
  decisions inside the boundary, which aggregate owns which invariant, how a
  value object is shaped, belong to the Aggregate, Entity and Value Object
  entries in this family, not to this technique.
- **There is no organisational appetite to run a workshop.** The technique is
  a facilitation artefact. Filling it alone at a desk from memory produces a
  document that looks authoritative but was never actually agreed, which
  reintroduces the exact single-point-of-assumption problem from dimension 2
  under a different format.
- **The system genuinely has one undivided model and splitting it would be
  premature.** Filling a worksheet for a boundary that should not exist yet
  manufactures the appearance of strategic design work without the
  substance, and risks calcifying a boundary the team has not actually
  earned through evidence of divergent language or divergent rate of change.
  See the Big Ball of Mud entry in this family for the failure mode of
  drawing boundaries the team cannot defend.
- **The output needs to be machine readable and enforced by a build step.**
  The worksheet is prose and short structured lists, not a schema. A team
  that wants an automatically validated service contract needs an interface
  definition language, an event schema registry, or a contract testing
  tool, none of which this technique replaces, though dimension 8 shows how
  a team can encode the fields as data and validate them once it has
  outgrown a whiteboard.
- **The context boundary is still unknown.** The technique assumes a
  candidate boundary already exists to document. Discovering where a
  boundary should sit in the first place is Event Storming's job, or a
  Context Map built from an existing system, not this worksheet's.
- **A single fact needs recording, not a whole context.** Recording one
  business rule or one term does not need a full worksheet. A line in a
  decision log or in the Ubiquitous Language glossary is proportionate. The
  technique earns its cost when a whole boundary needs describing at once.

## 5. Structure

The technique has no runtime participants in the sense a code pattern does.
Its participants are the people and the fields of the worksheet itself. This
entry names both, because the failure modes in dimension 11 come from
confusing one for the other.

**Facilitator.** Runs the session, keeps the group moving field by field, and
resists the temptation to fill a field alone when the room disagrees, because
disagreement surfaced during the session is the artefact working correctly.

**Domain expert.** Supplies the vocabulary and the business rules that
populate the Ubiquitous Language and Business Decisions fields, and is the
person best placed to say whether a proposed responsibility genuinely belongs
inside this context or genuinely belongs to a neighbour.

**Implementing team.** The engineers who will build against the boundary, and
who supply the technical detail in the communication fields, which messages
this context consumes and produces, and in what shape.

**The fields**, based on the current community version maintained at
ddd-crew/bounded-context-canvas
(https://github.com/ddd-crew/bounded-context-canvas verified 2026-08-02):

- **Name.** The name of the bounded context, which should already read as a
  ubiquitous language term in its own right.
- **Purpose.** A short, business-oriented statement of why the context
  exists, written so someone outside engineering understands it.
- **Strategic Classification.** Three sub-judgements. The domain role, core,
  supporting or generic, in the sense of the Core Domain, Supporting
  Subdomain and Generic Subdomain entries in this family. The business model
  role, whether the context is a revenue generator, an engagement driver or
  a compliance requirement. The evolution stage, using Wardley Map
  terminology, genesis, custom built, product, or commodity, describing how
  mature and how differentiated the capability is expected to remain.
- **Domain Roles.** A characterisation of the context's behavioural shape,
  drawing on Alberto Brandolini's bounded context archetypes and Rebecca
  Wirfs-Brock's object role stereotypes, used to avoid accidentally coupling
  two responsibilities that behave differently, for example a context that
  is mostly an execution engine absorbing a reporting responsibility that
  behaves like an information holder.
- **Business Decisions.** The key business rules and policies this context
  is the authority for, written as decisions, not as implementation detail.
- **Ubiquitous Language.** The domain terms that exist inside this context's
  boundary, each with the meaning that is specific to this context, which is
  the same field the Ubiquitous Language entry in this family exists to
  deepen.
- **Inbound Communication.** The collaborations initiated by other
  collaborators against this context, listing each collaborator and the
  commands, queries or events they send in.
- **Outbound Communication.** The collaborations this context initiates
  against other collaborators, in the same shape as Inbound Communication
  but reversed.
- **Assumptions.** Design decisions the team is making without confirmed
  evidence, written down explicitly rather than left implicit, so a later
  reader can see which parts of the worksheet rest on a guess.
- **Verification Metrics.** The signals, drawn from delivery pipelines, issue
  trackers or the running system, that would tell the team whether the
  boundary they drew is actually holding, for example a change failure rate
  isolated to this service or a count of cross-boundary schema breaks.
- **Open Questions.** Questions raised during the workshop that nobody in the
  room could answer, captured so they are not lost and so the team's
  remaining uncertainty is visible rather than papered over.

Quotations of the field intents above are drawn from the ddd-crew README's
own description of each field
(https://github.com/ddd-crew/bounded-context-canvas verified 2026-08-02).

## 6. ASCII structure diagram

```
+------------------------------------------------------------------+
|                        CONTEXT CANVAS                            |
|  Name: <bounded context name>                                    |
|  Purpose: <one sentence, business framed>                        |
+-----------------------------+------------------------------------+
| Strategic Classification    |  Domain Roles                      |
|  domain role: core/support/ |   archetype, behavioural shape,    |
|  generic                    |   avoids coupling mismatched roles |
|  business model role        |                                    |
|  evolution stage            |                                    |
+-----------------------------+------------------------------------+
| Ubiquitous Language          |  Business Decisions               |
|  term -> meaning, in THIS    |   rules and policies this context |
|  context only                |   is the authority for            |
+-----------------------------+------------------------------------+
|                     Inbound Communication                        |
|  Collaborator A  --(command/query/event)-->  THIS CONTEXT        |
|  Collaborator B  --(command/query/event)-->  THIS CONTEXT        |
+--------------------------------------------------------------------+
|                     Outbound Communication                       |
|  THIS CONTEXT  --(command/query/event)-->  Collaborator C        |
|  THIS CONTEXT  --(command/query/event)-->  Collaborator D        |
+------------------------------------------------------------------+
| Assumptions       | Verification Metrics  | Open Questions       |
|  unproven design   |  signal that proves   |  unresolved during   |
|  decisions          |  the boundary holds   |  the workshop        |
+------------------------------------------------------------------+

  One worksheet describes one bounded context. Every arrow crossing the
  boundary must be named in Inbound or Outbound Communication.
```

## 7. Dynamics

The technique has no runtime dynamics, because it is not executed, it is
filled. What this section describes instead is the workshop sequence Tune
recommends and the order in which the fields are typically populated, because
the order matters, filling Inbound and Outbound Communication before
Strategic Classification tends to anchor the group on implementation detail
before the business framing is settled.

```
Facilitator      Domain Expert        Implementing Team      Worksheet (shared)
    |                  |                      |                    |
    |-- propose Name --------------------------------------------->|
    |                  |-- confirm Purpose ---------------------->|
    |                  |                      |                    |
    |-- prompt Strategic Classification ------------------------->|
    |                  |-- states domain role, evolution -------->|
    |                  |                      |                    |
    |-- prompt Ubiquitous Language --------------------------------|
    |                  |-- supplies terms and meanings ---------->|
    |                  |                      |                    |
    |-- prompt Business Decisions -----------------------------|
    |                  |-- states rules this context owns ------->|
    |                  |                      |                    |
    |-- prompt Inbound / Outbound Communication -------------------|
    |                  |                      |-- lists collaborators
    |                  |                      |   and message shapes ->|
    |                  |                      |                    |
    |-- prompt Assumptions, Metrics, Open Questions ----------------|
    |                  |                      |-- captures gaps ------>|
    |                                                               |
    |-- worksheet is reviewed against the vocabulary and the      |
    |   dependency graph, disagreements surfaced live, not later --|
```

A worksheet that fills every field in isolation, one person at a time,
without the cross-check step at the end, has skipped the part of the
technique that actually catches inconsistency, which is why dimension 11
treats a solo-filled worksheet as a misuse rather than a shortcut.

## 8. Implementation variants

**Whiteboard or paper worksheet.** The original form. A printed A3 sheet or
a whiteboard grid, filled with sticky notes or markers during a synchronous
workshop. Fastest to start, and the version Tune's 2019 article describes,
but the output lives as a photograph and rots the moment nobody re-opens it.

**Digital collaborative board.** Miro and similar tools host a template
version of the tool for distributed teams, referenced from the ddd-crew
repository's resources directory
(https://github.com/ddd-crew/bounded-context-canvas verified 2026-08-02).
Keeps the synchronous, room-filled character of the original while allowing
a remote team to participate, at the cost of losing the tactile pressure of
a shared physical sheet that keeps a workshop moving.

**Markdown or text template committed to the repository.** A blank worksheet
saved as a markdown file next to the service's source, filled by the team
and reviewed the way any other document change is reviewed, through a pull
request. This is the variant that treats the artefact as living rather than
a one-time workshop output, and it is the variant this entry's code examples
build on.

**Typed data with a linter.** Once a team has more than a handful of
contexts, the fields are modelled as a small data structure and checked by a
script for exactly the kind of drift a human reviewer misses on a busy day,
message names that no longer match the glossary, or a listed collaborator
with no documented message at all. Dimension 11's most common failure mode,
the worksheet that quietly drifts from the code, is precisely what this
variant is built to catch early. Shown in TypeScript, Python and Go in the
Code examples section.

**Extended with example mapping or BDD scenarios.** A documented extension
adds a fourth row per message, a Given, When, Then scenario, so the
communication contract is not only named but demonstrated with an example,
described in Erik Weijers, "Extending the Bounded Context Canvas with BDD
Examples", Xebia, published 9 March 2020
(https://xebia.com/blog/extending-the-bounded-context-canvas-with-bdd-examples/
verified 2026-08-02). This variant trades a larger worksheet for a
communication contract a reader can verify by eye against the running
system.

## 9. Known production uses

**ddd-crew community reference implementation.** The Bounded Context Canvas
is maintained as an open community artefact at
ddd-crew/bounded-context-canvas on GitHub, with contributions from Kenny
Baas, Kim Lindhard, Michael Plöd, and Maxime Sanglan-Charlier documented in
the repository's own README, and is offered under a Creative Commons
Attribution 4.0 International License for direct reuse
(https://github.com/ddd-crew/bounded-context-canvas verified 2026-08-02).
Wide reuse of a single freely licensed template is itself the evidence this
tool is applied outside its author's own consultancy, since a competing team
would otherwise author its own worksheet rather than adopt this one.

**IASA's Business Technology Architecture Body of Knowledge.** The
international architecture association IASA Global lists the Bounded
Context Canvas as one of its named structured techniques in its own body of
knowledge documentation, cataloguing it alongside other architecture design
tools as a recognised way to describe a bounded context
(https://iasa-global.github.io/btabok/bounded_context_canvas.html
verified 2026-08-02). Adoption by an independent professional body, rather
than only by the original author's own writing, is the signal this entry
treats as evidence of use beyond a single consultancy's client base.

**Grzegorz Smith's markdown implementation for repository documentation.**
An independent open source implementation renders the ddd-crew fields as a
markdown document intended to live alongside a service's source code rather
than as a workshop photograph, published as grjsmith/bounded_context_canvas_md
on GitHub (https://github.com/grjsmith/bounded_context_canvas_md
verified 2026-08-02). A second party building tooling around a technique,
rather than only writing about it, is evidence the technique is used
repeatedly enough to be worth automating.

**Xebia's practitioner extension with BDD examples.** Erik Weijers at Xebia
documents extending the worksheet with Given, When, Then scenarios for
practitioner teams doing strategic domain-driven design consulting work, a
direct account of the technique being applied with a real client engagement
in mind rather than as an academic exercise
(https://xebia.com/blog/extending-the-bounded-context-canvas-with-bdd-examples/
verified 2026-08-02).

## 10. Consequences

Positive.

- Forces a cross-functional group, not one architect, to agree on a bounded
  context's purpose, ownership and dependencies before implementation
  starts, which surfaces disagreement while it is cheap to resolve.
- Produces a single, scannable artefact that replaces a scattered mix of
  meeting notes, whiteboard photographs and tribal memory as the record of
  why a boundary exists where it does.
- Makes strategic classification, whether a context is core, supporting or
  generic, an explicit, revisitable decision rather than an assumption
  nobody wrote down, which directly informs how much investment the context
  deserves relative to its neighbours.
- Gives a new team member or a new engineer a fast, honest way to understand
  a context's edges without reading every line of its source.
- Surfaces vocabulary and dependency mismatches at design time, which is
  cheaper than discovering them as a runtime contract break.

Negative.

- The document is a snapshot. Nothing in the technique itself keeps it
  synchronised with the code as the context evolves, so an unmaintained copy
  becomes actively misleading, worse than no documentation at all, because a
  stale but confident document is trusted more readily than an admitted
  absence of documentation.
- Filling it well needs a skilled facilitator and a room with the right
  people in it. A poorly facilitated session produces a document that looks
  complete but was never actually argued over, which is the single-assumption
  problem from dimension 2 wearing a template.
- The strategic classification fields, core, supporting or generic, and the
  evolution stage borrowed from Wardley Mapping, ask for judgement calls that
  a team without prior exposure to those models can fill in badly with
  confidence, producing a document that looks rigorous while resting on a
  vocabulary the room does not actually share.
- It has no enforcement mechanism of its own. A worksheet that says a
  context only accepts three named commands does nothing to stop a fourth,
  unnamed one being added to the code six months later.
- The version churn documented in dimension 1, from the original 2019
  structure through a fifth published revision, means two teams referencing
  "the Bounded Context Canvas" may be filling structurally different
  templates, and a reader comparing two documents needs to check which
  version each one used.

## 11. Failure modes and misuse

**The stale document.** Symptom. A worksheet checked into the repository, or
pinned to a team wiki, that describes three inbound events when the running
service actually accepts five, discovered when an engineer greps the code
for a message name the document never mentions. Cause. The worksheet was
filled once at design time and never revisited as the context grew. Fix.
Treat it as a living document reviewed on the same cadence as an
architecture decision record, or generate it from a typed model the way
dimension 8's typed-data variant demonstrates, so drift is caught by a
script rather than discovered by accident.

**The solo-filled worksheet.** Symptom. A document that reads as unusually
tidy and confident, filled entirely by one architect, with no Open
Questions section populated and no Assumptions listed, despite the context
clearly touching several other teams' areas. Cause. The facilitation step
from dimension 7 was skipped, and the artefact was produced as a document
rather than as the output of a disagreement surfaced live. Fix. Re-run the
workshop with the actual implementing team and at least one domain expert
in the room, and treat an empty Open Questions section on a first pass as a
warning sign, not a good sign.

**Vocabulary drift between the document and the code.** Symptom. A message
name appears in Inbound or Outbound Communication that does not correspond
to any term in the Ubiquitous Language section, or the reverse, a glossary
term that no message or business decision ever references. Cause. The two
fields were filled by different people, at different times, without cross
checking, or the code evolved a new message shape after the document was
signed off. Fix. Run a consistency check, by eye in a small team or with
tooling in a large one, exactly the check dimension 8's linter automates.

**Boundary theatre.** Symptom. A beautifully filled worksheet for a context
that should not exist, drawn around a boundary the team wanted rather than
one evidence supports, discovered when the Business Decisions and
Ubiquitous Language sections turn out to be nearly identical to a
neighbouring context's document. Cause. Skipping the non-applicability guard
in dimension 4 about boundaries the team has not earned, and using the
technique to justify a split that was decided for organisational or
political reasons rather than domain reasons. Fix. Compare the two
documents' Ubiquitous Language sections directly. Near-duplicate vocabulary
between two "different" contexts is evidence the split is premature, per
the guidance in the Bounded Context and Context Map entries in this family.

**Confusing the worksheet for the contract.** Symptom. A downstream team
builds an integration against messages named on a context's document, then
the integration breaks in production because the actual running service
uses a slightly different message shape. Cause. Treating a facilitation
worksheet as an enforced interface definition, which dimension 4 explicitly
warns against. Fix. Use the worksheet to design the contract, then encode
the agreed contract in a schema registry, an interface definition language,
or contract tests, the tools actually built to enforce it.

## 12. Trade-off matrix

Compared against named alternative strategic design artefacts across the
forces from dimension 3.

| Force | Context Canvas | Context Map (this family) | Free-form design document | UML component diagram |
|---|---|---|---|---|
| Shared understanding | High, built for group facilitation | High, but focused on inter-context relationships, not one context's internals | Low to medium, usually one author | Low, usually one author, read by many |
| Speed to produce | Fast, roughly one hour per context in a workshop | Slower, needs every context already understood | Variable, depends on author's diligence | Slow, needs modelling tool proficiency |
| Documents a single context's internals | Yes, purpose built for this | No, documents relationships between contexts, not one context's internal decisions | Sometimes, inconsistently structured | Partially, structure only, no business framing |
| Documents relationships between contexts | Partially, via Inbound/Outbound Communication | Yes, purpose built for this, with named relationship patterns | Sometimes, inconsistently | Partially, as connectors, without relationship semantics |
| Enforced by tooling | No, by default. Can be encoded as data and linted, dimension 8 | No, by default, same caveat applies | No | No, diagrams drift from code just as easily |
| Captures business framing, not just technical shape | Yes, Purpose and Business Decisions fields exist specifically for this | Partially | Rarely, depends entirely on the author | No |
| Learning curve | Low, one page, free template | Medium, needs the relationship vocabulary from Evans and later DDD writing | Low to use, but inconsistent across authors | Medium, needs UML familiarity |

The Context Canvas and the Context Map are complementary rather than
competing. A Context Map shows the constellation of contexts and how they
relate. A Context Canvas is filled once per node in that constellation, to
describe what is inside it.

## 13. Related and incompatible patterns

**Bounded Context.** The Context Canvas exists to document a single instance
of a Bounded Context. Every field describes a decision about where this
boundary sits and what stays consistent inside it. Reading the Bounded
Context entry first makes the Purpose and Ubiquitous Language fields make
sense as an application of that boundary, not a separate idea.

**Context Map.** Composes directly. A Context Map shows several bounded
contexts and the relationship pattern between each pair, customer-supplier,
conformist, shared kernel and the rest. A Context Canvas is filled per
context named on that map, and its Inbound and Outbound Communication
fields are where the specific relationship type from the map gets made
concrete in terms of actual messages.

**Ubiquitous Language.** The Ubiquitous Language field is a scoped,
per-context instance of the practice described in the Ubiquitous Language
entry. A term defined on one context's document is not assumed to mean the
same thing on another context's document, which is the entire point of
scoping language to a boundary in the first place.

**Event Storming.** Frequently sequenced immediately before this technique.
Event Storming, described in the Event Storming entry in this family,
discovers candidate boundaries by clustering events, commands and actors on
a timeline. The Context Canvas then documents each discovered boundary in
full, once the group has agreed roughly where the lines fall.

**Core Domain, Supporting Subdomain, Generic Subdomain.** The Strategic
Classification field asks the team to place the context into one of these
three categories, described in their own entries in this family. Filling
the worksheet is one of the concrete moments a team is forced to make that
classification explicit rather than assumed.

**Customer-Supplier, Conformist, and the other Context Map relationship
patterns.** Each collaborator named in Inbound or Outbound Communication
should, in a mature document, carry one of these named relationship types
rather than an unlabelled arrow, connecting the technique back to the
vocabulary the Context Map and Customer-Supplier entries in this family
define.

**Incompatible with nothing structurally**, because this is a documentation
practice rather than a code structure that could conflict with another code
structure. The closest thing to an incompatibility is practice-level. a
team that has already committed to enforcing bounded context contracts
purely through machine-checked schemas and treats any human-facilitated
worksheet as overhead will find the technique redundant with tooling they
already trust, though the two are not mutually exclusive, since the
worksheet can still inform the design that the schema later encodes.

## 14. Refactoring path in and out

**Introducing the technique for an existing, undocumented context.** Gather
the implementing team and one domain expert. Start with Name and Purpose,
which are usually the easiest fields to agree on because the context
already exists and the group can describe what it does today rather than
design something new. Move to Ubiquitous Language, mining it from existing
code identifiers, ticket titles and conversation, flagging any term the
group cannot agree a single meaning for as a candidate Open Question rather
than forcing a false consensus. Fill Inbound and Outbound Communication
last, by reading the actual code's public interface and message handlers
rather than by memory, since memory is exactly what produced the drift this
exercise is meant to correct. Finish with Strategic Classification, since
that judgement is easier to make once the rest of the worksheet has made
the context's real shape and importance visible.

**Retiring or replacing a stale document.** When Verification Metrics or a
direct code review shows the document materially disagrees with the running
system, per dimension 11's stale document failure mode, the retirement path
is not to delete it silently. Re-run the workshop, produce a new version,
and keep the old one in version control history as a record of how the
design decision changed, which is the same discipline the Refactoring
family entry on Extract Class recommends for any structural change, leave a
trail rather than erase the prior state.

**Escalating from a whiteboard photograph to typed data.** When a team finds
itself checking three or more documents for consistency by eye, and missing
drift the way dimension 11 describes, migrate the markdown template variant
from dimension 8 into the typed data variant with an automated consistency
check, shown fully worked in the Code examples section. This does not
change what the technique asks the team to decide, only how the answers are
stored and cross-checked once there are enough contexts that human review
alone misses things.

## 15. Testing and verification

The technique itself is not code, so it is not unit tested in the
conventional sense, but its claims are checkable in three concrete ways.

- **Vocabulary consistency checking.** Verify every message name appearing in
  Inbound or Outbound Communication corresponds to a term defined in
  Ubiquitous Language, and flag any glossary term that no message or
  business decision ever references. This is exactly what the linter in
  dimension 8 and the Code examples section automates, and it is the single
  highest value automated check because it catches the drift failure mode
  from dimension 11 before a human notices it by accident.
- **Contract verification against the running system.** Once Inbound and
  Outbound Communication name specific messages, those names can be checked
  against a schema registry, an OpenAPI specification, or an event catalog
  the running service actually emits, turning the document's claims into an
  assertion a build pipeline can fail on. The technique itself does not do
  this, but it produces the list of claims worth testing.
- **Cross-document glossary reconciliation.** Where two contexts' documents
  define the same term differently, that is expected and healthy, per the
  Ubiquitous Language entry, a term scoped to one boundary need not agree
  with the same word used elsewhere. Where two documents define the same
  term identically and use it to describe near-identical responsibilities,
  that is the boundary-theatre smell from dimension 11 and worth a manual
  review, not an automated one, since judging whether two responsibilities
  are "the same" needs a domain expert, not a string comparison.

What the technique makes easier to test, once filled, is the running
system's adherence to a stated boundary, because it gives a reviewer a
checklist to compare the code against. What it does not make easier is
testing the code's internal correctness, which remains the job of ordinary
unit and integration tests scoped to the context's own logic.

## 16. Observability signals

A filled document is itself an observability artefact for a human reader,
but the fields most worth turning into a monitored signal are these.

- **Verification Metrics, made real.** The technique explicitly names a
  field for this. In practice, useful signals include a change failure rate
  isolated to deployments of this one context, a count of schema
  incompatibilities detected against declared Outbound messages, and the
  frequency with which a downstream team files an issue asking this
  context's team what a message means, which is a proxy for the Ubiquitous
  Language section being incomplete or wrong.
- **Document staleness as a metric in its own right.** The age of the last
  commit to a committed worksheet file, compared against the age of the
  last meaningful change to the context's public interface, is a cheap,
  automatable signal for the stale document failure mode from dimension 11.
  A document untouched for a year while the service's message catalog grew
  by six new event types is a documentation debt item worth surfacing the
  same way a dependency audit surfaces an outdated package.
- **Vocabulary check failures, tracked over time.** If a team runs the
  linter from dimension 8 as part of continuous integration on the
  markdown-as-data variant, the count of flagged inconsistencies per commit
  is itself a healthy signal to watch, a rising trend means the document and
  the code are diverging faster than the team is reconciling them.

A healthy document, observed from outside, is one whose Verification
Metrics section names real, currently monitored numbers rather than
aspirational ones, and whose last edit date tracks reasonably closely with
the last meaningful change to the context's public interface. A failing one
has an empty or stale Verification Metrics field and an edit history that
stopped the day the workshop ended.

## 17. Security and privacy implications

This is largely engineering judgement rather than a sourced claim, since
neither Tune's articles nor the ddd-crew documentation frame the technique
as a security tool. The technique has no runtime attack surface of its own,
since it produces no executable artefact, but two implications are worth
stating plainly rather than left implicit.

- **The document is a map of trust boundaries.** Inbound and Outbound
  Communication, once filled honestly, document exactly which external
  collaborators are trusted to send which commands and which data crosses
  the boundary in each direction. A filled worksheet is therefore a natural
  input to a threat-modelling exercise, since it already lists the attack
  surface's edges in the language a security reviewer needs, who calls in,
  with what, and who this context calls out to.
- **A worksheet circulated for a workshop, especially a remote one filled on
  a shared digital board, can leak information about internal system
  design, including named third-party dependencies, business rules that
  reveal pricing or eligibility logic, and the existence of contexts a
  company has not publicly disclosed.** Treat a filled worksheet with the
  same access controls as any other internal architecture document, and be
  deliberate about which collaborators from Inbound and Outbound
  Communication are safe to name in a document that might be shared outside
  the immediate team, for example with an external vendor during an
  integration discussion.

Beyond those two points, the technique is silent on security, stated here
plainly per the template's guidance rather than an invented concern,
because it is a design and communication tool, not a security control.

## 18. References

1. Nick Tune, "Modelling Bounded Contexts with the Bounded Context Design
   Canvas. A Workshop Recipe", Nick Tune's weird ideas, Medium, published 22
   July 2019.
   https://medium.com/nick-tune-tech-strategy-blog/modelling-bounded-contexts-with-the-bounded-context-design-canvas-a-workshop-recipe-1f123e592ab
   Verified 2026-08-02.
2. Nick Tune, "Bounded Context Canvas V3. Simplifications and Additions",
   Nick Tune's weird ideas, Medium, published 12 January 2020.
   https://medium.com/nick-tune-tech-strategy-blog/bounded-context-canvas-v2-simplifications-and-additions-229ed35f825f
   Verified 2026-08-02.
3. Nick Tune, "Bounded Context Canvas Recipe. Use Case Swimlanes", Nick
   Tune's weird ideas, Medium.
   https://medium.com/nick-tune-tech-strategy-blog/bounded-context-canvas-recipe-use-case-swimlanes-11ca647175d3
   Verified 2026-08-02.
4. ddd-crew, "bounded-context-canvas" repository, GitHub, README and
   resources directory, contributors Kenny Baas, Kim Lindhard, Michael Plöd,
   and Maxime Sanglan-Charlier, Creative Commons Attribution 4.0
   International License.
   https://github.com/ddd-crew/bounded-context-canvas
   Verified 2026-08-02.
5. IASA Global, "Bounded Context Canvas", Business Technology Architecture
   Body of Knowledge.
   https://iasa-global.github.io/btabok/bounded_context_canvas.html
   Verified 2026-08-02.
6. Grzegorz Smith, "bounded_context_canvas_md", a markdown implementation of
   the ddd-crew Bounded Context Canvas, GitHub.
   https://github.com/grjsmith/bounded_context_canvas_md
   Verified 2026-08-02.
7. Erik Weijers, "Extending the Bounded Context Canvas with BDD Examples",
   Xebia, published 9 March 2020.
   https://xebia.com/blog/extending-the-bounded-context-canvas-with-bdd-examples/
   Verified 2026-08-02.
8. Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*, Addison-Wesley, 2003, part IV, the source of the Bounded
   Context, Ubiquitous Language, and strategic design vocabulary the
   technique builds on. See the Bounded Context and Ubiquitous Language
   entries in this family for page-level citation of Evans's own text.

## Code examples

The Context Canvas is a facilitation worksheet, not an executable structure,
so there is no class hierarchy to instantiate the way a Gang of Four pattern
has one. What real teams build once a filled worksheet has moved past a
whiteboard photograph, described as the typed-data variant in dimension 8,
is a small typed model of the fields plus a linter that catches the two
most common drift failures from dimension 11, a message name that does not
correspond to any term in the Ubiquitous Language section, and a
collaborator listed with no message ever documented against it. The
validator is shown independently in TypeScript and Python. The Go example
takes the same typed model and renders it to a markdown document, the
repository-committed artefact the markdown template variant from dimension
8 describes, which is the shape teams use to keep the worksheet next to the
code it documents rather than trapped in a workshop tool nobody revisits.

### TypeScript, worksheet model and vocabulary linter

```typescript
type MessageType = "command" | "event" | "query";

interface Message {
  name: string;
  type: MessageType;
}

interface Collaboration {
  collaborator: string;
  messages: Message[];
}

interface GlossaryTerm {
  term: string;
  meaning: string;
}

interface BoundedContextWorksheet {
  name: string;
  purpose: string;
  domainRole: "core" | "supporting" | "generic";
  ubiquitousLanguage: GlossaryTerm[];
  inbound: Collaboration[];
  outbound: Collaboration[];
  verificationMetrics: string[];
}

const GENERIC_VERBS = new Set([
  "get", "create", "update", "delete", "request", "fetch", "list", "sync",
]);

function significantTokens(messageName: string): string[] {
  const words = messageName
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .split(/\s+/)
    .filter((w) => w.length > 0);
  return words.filter((w) => !GENERIC_VERBS.has(w.toLowerCase()));
}

function definedInGlossary(word: string, glossary: GlossaryTerm[]): boolean {
  return glossary.some((g) => g.term.toLowerCase().includes(word.toLowerCase()));
}

function checkVocabularyConsistency(sheet: BoundedContextWorksheet): string[] {
  const problems: string[] = [];
  const allMessages = [...sheet.inbound, ...sheet.outbound].flatMap((c) => c.messages);

  for (const msg of allMessages) {
    const tokens = significantTokens(msg.name);
    const known = tokens.some((t) => definedInGlossary(t, sheet.ubiquitousLanguage));
    if (!known) {
      problems.push(
        `Message "${msg.name}" uses a noun that is not defined in the Ubiquitous Language section.`,
      );
    }
  }
  return problems;
}

function checkOrphanCollaborators(sheet: BoundedContextWorksheet): string[] {
  const problems: string[] = [];
  for (const c of [...sheet.inbound, ...sheet.outbound]) {
    if (c.messages.length === 0) {
      problems.push(
        `Collaborator "${c.collaborator}" is listed with no message documented.`,
      );
    }
  }
  return problems;
}

function validateWorksheet(sheet: BoundedContextWorksheet): string[] {
  return [...checkVocabularyConsistency(sheet), ...checkOrphanCollaborators(sheet)];
}

const shippingSheet: BoundedContextWorksheet = {
  name: "Shipping",
  purpose: "Coordinate carrier handoff for a placed order",
  domainRole: "supporting",
  ubiquitousLanguage: [
    { term: "Shipment", meaning: "A single carrier handoff for one order" },
    { term: "Carrier", meaning: "A third party that transports a shipment" },
    { term: "Order", meaning: "A confirmed purchase awaiting fulfillment" },
    { term: "Invoice", meaning: "A billing record raised for a shipment" },
  ],
  inbound: [
    { collaborator: "Order Management", messages: [{ name: "OrderPlaced", type: "event" }] },
    { collaborator: "Billing", messages: [] },
  ],
  outbound: [
    {
      collaborator: "Carrier Gateway",
      messages: [
        { name: "RequestPickup", type: "command" },
        { name: "InvoiceGenerated", type: "event" },
      ],
    },
  ],
  verificationMetrics: [],
};

for (const issue of validateWorksheet(shippingSheet)) {
  console.log(issue);
}
```

Ran with `npx tsc --strict --noEmit` to type check, and with `node` after
transpiling to JavaScript with `npx tsc`. Output on the sample data above,
which deliberately includes one collaborator with no documented message and
one command whose noun was never added to the glossary.

```
Message "RequestPickup" uses a noun that is not defined in the Ubiquitous Language section.
Collaborator "Billing" is listed with no message documented.
```

### Python, worksheet model and vocabulary linter (independent reimplementation)

```python
from dataclasses import dataclass, field
import re

GENERIC_VERBS = {"get", "create", "update", "delete", "request", "fetch", "list", "sync"}


@dataclass
class Message:
    name: str
    kind: str


@dataclass
class Collaboration:
    collaborator: str
    messages: list[Message]


@dataclass
class GlossaryTerm:
    term: str
    meaning: str


@dataclass
class BoundedContextWorksheet:
    name: str
    purpose: str
    domain_role: str
    ubiquitous_language: list[GlossaryTerm]
    inbound: list[Collaboration]
    outbound: list[Collaboration]
    verification_metrics: list[str] = field(default_factory=list)


def significant_tokens(message_name: str) -> list[str]:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", message_name)
    words = [w for w in spaced.split() if w]
    return [w for w in words if w.lower() not in GENERIC_VERBS]


def defined_in_glossary(word: str, glossary: list[GlossaryTerm]) -> bool:
    return any(word.lower() in g.term.lower() for g in glossary)


def check_vocabulary_consistency(sheet: BoundedContextWorksheet) -> list[str]:
    problems: list[str] = []
    all_messages = [m for c in (sheet.inbound + sheet.outbound) for m in c.messages]
    for msg in all_messages:
        tokens = significant_tokens(msg.name)
        known = any(defined_in_glossary(t, sheet.ubiquitous_language) for t in tokens)
        if not known:
            problems.append(
                f'Message "{msg.name}" uses a noun that is not defined in the Ubiquitous Language section.'
            )
    return problems


def check_orphan_collaborators(sheet: BoundedContextWorksheet) -> list[str]:
    problems: list[str] = []
    for c in sheet.inbound + sheet.outbound:
        if not c.messages:
            problems.append(f'Collaborator "{c.collaborator}" is listed with no message documented.')
    return problems


def validate_worksheet(sheet: BoundedContextWorksheet) -> list[str]:
    return check_vocabulary_consistency(sheet) + check_orphan_collaborators(sheet)


if __name__ == "__main__":
    shipping_sheet = BoundedContextWorksheet(
        name="Shipping",
        purpose="Coordinate carrier handoff for a placed order",
        domain_role="supporting",
        ubiquitous_language=[
            GlossaryTerm("Shipment", "A single carrier handoff for one order"),
            GlossaryTerm("Carrier", "A third party that transports a shipment"),
            GlossaryTerm("Order", "A confirmed purchase awaiting fulfillment"),
            GlossaryTerm("Invoice", "A billing record raised for a shipment"),
        ],
        inbound=[
            Collaboration("Order Management", [Message("OrderPlaced", "event")]),
            Collaboration("Billing", []),
        ],
        outbound=[
            Collaboration(
                "Carrier Gateway",
                [Message("RequestPickup", "command"), Message("InvoiceGenerated", "event")],
            )
        ],
    )
    for issue in validate_worksheet(shipping_sheet):
        print(issue)
```

Ran with `python3 context_canvas.py`. Output matched the TypeScript version
exactly, both flags on RequestPickup and on the empty Billing collaboration.

```
Message "RequestPickup" uses a noun that is not defined in the Ubiquitous Language section.
Collaborator "Billing" is listed with no message documented.
```

### Go, rendering the worksheet model to a committed markdown document

```go
package main

import (
	"fmt"
	"strings"
)

type GlossaryTerm struct {
	Term    string
	Meaning string
}

type Message struct {
	Name string
	Kind string
}

type Collaboration struct {
	Collaborator string
	Messages     []Message
}

type Worksheet struct {
	Name               string
	Purpose            string
	DomainRole         string
	UbiquitousLanguage []GlossaryTerm
	Inbound            []Collaboration
	Outbound           []Collaboration
}

func renderCollaborations(title string, cols []Collaboration) string {
	var b strings.Builder
	fmt.Fprintf(&b, "### %s\n\n", title)
	if len(cols) == 0 {
		b.WriteString("None documented.\n\n")
		return b.String()
	}
	for _, c := range cols {
		fmt.Fprintf(&b, "- **%s**\n", c.Collaborator)
		for _, m := range c.Messages {
			fmt.Fprintf(&b, "  - %s (%s)\n", m.Name, m.Kind)
		}
		if len(c.Messages) == 0 {
			b.WriteString("  - no message documented\n")
		}
	}
	b.WriteString("\n")
	return b.String()
}

func RenderMarkdown(w Worksheet) string {
	var b strings.Builder
	fmt.Fprintf(&b, "# %s\n\n", w.Name)
	fmt.Fprintf(&b, "**Purpose.** %s\n\n", w.Purpose)
	fmt.Fprintf(&b, "**Domain role.** %s\n\n", w.DomainRole)

	b.WriteString("## Ubiquitous language\n\n")
	for _, t := range w.UbiquitousLanguage {
		fmt.Fprintf(&b, "- **%s.** %s\n", t.Term, t.Meaning)
	}
	b.WriteString("\n")

	b.WriteString(renderCollaborations("Inbound communication", w.Inbound))
	b.WriteString(renderCollaborations("Outbound communication", w.Outbound))
	return b.String()
}

func main() {
	shipping := Worksheet{
		Name:       "Shipping",
		Purpose:    "Coordinate carrier handoff for a placed order",
		DomainRole: "supporting",
		UbiquitousLanguage: []GlossaryTerm{
			{"Shipment", "A single carrier handoff for one order"},
			{"Carrier", "A third party that transports a shipment"},
		},
		Inbound: []Collaboration{
			{"Order Management", []Message{{"OrderPlaced", "event"}}},
		},
		Outbound: []Collaboration{
			{"Carrier Gateway", []Message{{"RequestPickup", "command"}}},
		},
	}
	fmt.Print(RenderMarkdown(shipping))
}
```

Ran with `go run main.go`. Output.

```
# Shipping

**Purpose.** Coordinate carrier handoff for a placed order

**Domain role.** supporting

## Ubiquitous language

- **Shipment.** A single carrier handoff for one order
- **Carrier.** A third party that transports a shipment

### Inbound communication

- **Order Management**
  - OrderPlaced (event)

### Outbound communication

- **Carrier Gateway**
  - RequestPickup (command)
```

This markdown output is exactly the artefact the repository-committed
variant from dimension 8 stores next to the service's source, reviewed
through the same pull request process as any other change, and regenerated
whenever the typed model is updated rather than hand-edited out of sync
with it.

Java, Rust, and Swift are omitted for this entry. The pattern is a
documentation and facilitation technique with no idiomatic language-specific
shape beyond ordinary structs and string formatting, and the three languages
shown already demonstrate the object-oriented, dataclass-based, and
struct-based renderings a reader would need to translate the idea into any
other language on the availability list.
