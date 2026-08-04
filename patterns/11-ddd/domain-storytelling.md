---
name: Domain Storytelling
slug: domain-storytelling
family: 11-ddd
category: Strategic
aliases: [Domain Story Modeling, Pictographic Domain Modeling]
first_described: "Hofer and Schwentner 2021"
maturity: established
related: [ubiquitous-language, bounded-context, domain-event, context-map]
incompatible_with: []
verified: 2026-08-02
---

# Domain Storytelling

## 1. Name, aliases, and lineage

The canonical name is Domain Storytelling, written as two capitalized words in
the literature. The method was developed and named by Stefan Hofer and Henning
Schwentner, both consultants at WPS - Workplace Solutions GmbH in Hamburg,
Germany, and published in full in their book "Domain Storytelling. A
Collaborative, Visual, and Agile Way to Build Domain-Driven Software"
(Addison-Wesley Professional, Addison-Wesley Signature Series edited by Vaughn
Vernon, first edition, September 17, 2021, ISBN 978-0-13-745891-2). The book's
inclusion in Vernon's Signature Series is itself a lineage marker, because that
series exists specifically to carry forward material the series editor judges
consistent with and useful to the Domain-Driven Design body of work that Eric
Evans began in 2003.

Hofer and Schwentner did not invent Domain Storytelling from nothing in 2021.
The technique and its supporting tool were developed inside WPS over roughly a
decade of client consulting work before the book formalized it, and the
open source modeling tool that carries out the pictographic notation, named
Egon, was already in active development on GitHub under the organization
account WPS starting in 2018, confirmed by inspection of the WPS/egon.io
repository at https://github.com/WPS/egon.io, verified 2026-08-02. The book is
the canonical written reference, and the companion website at
https://domainstorytelling.org, maintained by the same authors and verified
2026-08-02, is the canonical living reference for the notation itself, since
the notation has had small additions since the book's print run that the
website tracks and the fixed text of the book cannot.

The pattern has no rival name in general circulation, but it is frequently
discussed alongside a sibling collaborative-modeling technique, Event Storming,
which Alberto Brandolini introduced independently and earlier, documented at
https://www.eventstorming.com, verified 2026-08-02, and in his own writing
collected at that site. The two are sometimes loosely conflated by newcomers
because both are workshop-based, both produce a visual domain model on a wall
or a screen, and both feed the strategic design phase of Domain-Driven Design,
but they are distinct techniques with a distinct notation, a distinct
facilitation shape, and, as covered under dimension 13 below, a genuinely
different sweet spot. Domain Storytelling is not itself one of Evans' original
1994 or 2003-era DDD patterns. It is a later strategic-modeling technique that
sits upstream of and feeds those patterns, in the same family as Event
Storming and Context Mapping workshops, rather than a structural or tactical
pattern like Aggregate or Repository.

## 2. Problem and context

A team building software for a business domain needs an accurate, shared
picture of how work actually happens before it can decide what the software
should do. The obstacle is that this picture lives almost entirely in the
heads of the people who do the work, the domain experts, and it does not
transfer cleanly into a form developers can use. Two familiar failure shapes
recur constantly in real projects. The first is the interview transcript
problem, in which a business analyst interviews a domain expert, writes prose
minutes, and hands the prose to developers, who each read a slightly different
meaning into the same paragraph because natural-language prose is ambiguous
about sequence, about who does what, and about which details are essential
versus incidental. The second is the premature-artifact problem, in which a
team jumps straight to a UML activity diagram, a BPMN process model, or a set
of user stories before anyone has actually walked through the real workflow
with the person who lives it, so the artifact encodes the team's guess at the
domain rather than the domain itself, and the domain expert, confronted with a
diagram full of unfamiliar notation, cannot meaningfully critique it.

Domain Storytelling exists to close this gap directly. It sits a domain expert
and the people who need to understand the domain, developers, testers,
product people, in the same room or the same video call, and asks the domain
expert to narrate a concrete example of how the work happens, in their own
words, using their own vocabulary. A trained moderator listens and, in real
time, converts each sentence of the spoken story into a simple pictogram on a
shared board, using a small fixed vocabulary of icons, a numbered arrow, and
plain text, described fully under dimension 5. The domain expert watches the
picture form as they talk and immediately corrects anything that is wrong,
because recognizing an error in a picture of your own workflow is far easier
than recognizing an error buried in someone else's written summary of it.

The context in which this pattern earns its cost is the beginning of a
Domain-Driven Design effort, specifically the strategic phase, where a team is
still building the shared vocabulary described under Ubiquitous Language and
is still deciding where the seams of the eventual Bounded Contexts should
fall. It is not a technique for refining an already-well-understood workflow
down to implementation detail, and it is not useful in a domain so simple that
a single sentence would already describe it completely. It earns its keep
specifically when the domain has real workflow complexity, multiple actors
handing work to one another, and enough ambiguity in the existing written
material that different stakeholders would describe "how this actually works"
differently if asked separately.

## 3. Forces

Fidelity against speed is the dominant tension. Producing an accurate story
takes real workshop time, typically thirty minutes to two hours per story, per
Hofer and Schwentner's guidance in the book's chapters on running a workshop,
and a team under delivery pressure is tempted to skip the workshop and infer
the workflow from existing documentation or from a single developer's
assumption. The pattern's entire value proposition rests on paying the
workshop cost up front, on the argument, stated by the authors and echoed
across the secondary literature on collaborative modeling, that a wrong
assumption discovered after code is written costs far more than the workshop
that would have caught it.

Accessibility against expressive power is the second force. The pictographic
notation is deliberately minimal, three shapes and an arrow, precisely so a
domain expert with zero technical background can read and correct the diagram
without training. This same minimalism means the notation cannot express
every nuance a richer notation like BPMN could, and Domain Storytelling
explicitly accepts that trade, favoring a diagram every stakeholder in the
room can actually validate over a diagram only the diagram's author can fully
interpret.

Concreteness against generality is the third force. A domain story is always
told as one specific, concrete example, a named customer buying a named
product on a named date, rather than as an abstract flowchart with branches
and conditions. Concreteness is what lets a domain expert catch an error,
because people recognize the wrongness of a specific false statement far more
reliably than the wrongness of an abstract general rule. The cost is that a
single story captures one path through the domain, not the whole space of
possible paths, so covering a workflow's real variation requires multiple
stories, told for the happy path and for each variant and exception worth
capturing, rather than one master diagram that tries to hold everything.

Facilitation skill against democratized participation is the fourth force. A
skilled moderator can keep a story moving, ask the right clarifying question,
and avoid freezing the room into silence, but that skill takes practice to
build, and a poorly moderated session can produce a story that looks complete
while quietly missing the actual decision points that matter. The pattern
favors letting anyone learn to moderate over requiring a certified specialist,
which the authors argue explicitly in the book's early chapters, but this
democratization means quality varies with the moderator's experience.

The pattern favors shared understanding, domain-expert legibility, and early
error discovery. It sacrifices workshop time, full workflow coverage from any
single artifact, and notation richness, and it depends on facilitation skill
that a team has to build deliberately rather than assume.

## 4. Applicability and non-applicability

Reach for Domain Storytelling when a team is starting or restarting a
Domain-Driven Design effort and does not yet have a reliable, agreed picture
of how the core workflow actually happens. Reach for it when the people who
would write the requirements and the people who would implement them have
never sat in the same room with the actual domain expert and walked through a
real example together. Reach for it when a written specification already
exists but stakeholders disagree, in a low-key way that has not yet surfaced
as an open conflict, about what it means, because the pictographic session
tends to surface exactly that kind of disagreement fast, since two domain
experts telling the same story will visibly disagree on the diagram in a way
prose does not make visible. Reach for it when identifying the seams for
Bounded Contexts is the immediate goal, because a set of domain stories, each
scoped to a coherent slice of work, is one of the most direct inputs into
where a context boundary should sit, a use Hofer and Schwentner describe
explicitly in the book's strategic-design chapters. Reach for it when
onboarding a new team member into an existing domain, because a small set of
existing domain stories is a far faster onboarding artifact than a
requirements wiki nobody has kept current.

Do not reach for it when the domain is genuinely simple and a single clear
sentence already describes the whole workflow, because the workshop
overhead buys nothing a five-minute conversation would not already give you.
Do not reach for it as a substitute for detailed technical design, since the
pictographic notation is deliberately too coarse to specify an algorithm, a
data schema, or a concurrency strategy, and forcing it to carry that weight
produces either an unreadably dense diagram or a diagram that silently omits
the technical detail that actually matters. Do not reach for it when no
domain expert is available to tell the story, because the technique's
integrity depends on the narrator being the person who actually does the
work, not a proxy who has read documentation about the work. a developer
narrating their own guess at the workflow produces a developer's story, not a
domain story, and defeats the purpose. Do not reach for it as a
one-time, one-off exercise disconnected from the rest of the modeling effort,
because a single isolated story rarely covers enough of the domain's real
variation to be worth the setup cost. the pattern pays off across a small
portfolio of stories built up over the course of a discovery effort. Do not
reach for it when the goal is process automation modeling for a workflow
engine, where BPMN's richer notation for gateways, timers, and compensating
transactions is a better fit for the audience that will actually consume the
diagram, namely a process-automation tool rather than a domain expert.

## 5. Structure

Domain Storytelling has no runtime participants in the sense a code pattern
does, because it is a modeling and facilitation technique, not a software
structure. Its structure is the fixed pictographic vocabulary the notation is
built from, plus the human roles that operate it in a workshop.

The Actor is the pictogram for whoever initiates or receives an activity. An
actor can be a single named person, a role such as "the underwriter," a group
of people, or a software system, and Hofer and Schwentner are explicit in the
notation that a software system may be drawn as an actor when the story's
purpose is to include the software's part in the workflow, and omitted
entirely when the story is meant to describe the domain in software-free
terms, a scope choice covered under dimension 8.

The Work Object is the pictogram for anything an actor creates, reads,
modifies, or hands to another actor, a physical thing, a document, a digital
record, or an abstract item the domain treats as a unit, such as an order or
a claim. The same work object can recur through a story wearing a different
icon if its medium changes, for example a paper form that later becomes a
scanned digital file, a distinction the notation preserves deliberately
because the medium change is itself often the exact seam where an integration
or an anti-corruption boundary belongs.

The Activity is a numbered, labeled arrow drawn from an actor to a work
object or to another actor, using a verb drawn from the domain's own
vocabulary rather than a generic technical verb, so that "the underwriter
reviews the application" is drawn and numbered rather than "the system
processes the record." Each activity's number establishes its position in
the story's chronological sequence, and the accumulated set of numbered
activities is what makes the diagram readable as a story rather than as a
static map.

The Sentence is the smallest complete unit of meaning the notation produces,
formed by reading one numbered activity aloud as who does what with what and,
where relevant, with whom, following ordinary subject-verb-object grammar.
Hofer and Schwentner's quick-start material, published on
https://domainstorytelling.org/quick-start-guide and verified 2026-08-02,
states this sentence structure explicitly as the grammatical backbone of
every activity in the notation.

The Group is an outlined boundary drawn around a cluster of actors, work
objects, or activities, used to mark a repeated block, an optional branch, a
location, an organizational division, or a subdomain, without requiring a
separate diagram for each case.

The Annotation is free text attached to any element, used to record domain
terminology, an assumption the moderator made explicit and asked the expert
to confirm, a noted variation, or an exceptional case, without breaking the
flow of the main narrative into a separate diagram.

The human roles are the Domain Expert, who narrates a concrete example from
lived experience and is the sole authority on whether the resulting diagram
is correct, the Moderator, who listens, draws or directs the drawing of each
sentence in real time, and asks clarifying questions when a sentence is
ambiguous or when a work object appears without having been introduced, and
the Listeners, typically the developers, testers, and product people in the
room, who absorb the story, ask their own clarifying questions through the
moderator, and later carry the resulting shared understanding into design and
implementation work.

## 6. ASCII structure diagram

```text
+-----------------------------------------------------------+
|                 Domain Storytelling Notation               |
+-----------------------------------------------------------+

   Actor              Activity (numbered, verb-labeled)
   +---+     1. submits      +-----------+
   | @ |------------------->|  document  |  Work Object
   +---+                     +-----------+
   Applicant

           2. reviews
   +---+  <-----------------  +-----------+
   | @ |                      |  document  |
   +---+                      +-----------+
   Underwriter

   +--------------------------------------------------+
   | Group. "Credit check subprocess"                  |
   |                                                    |
   |  +---+   3. requests    +-----------+              |
   |  | @ |----------------->|   report   |              |
   |  +---+                   +-----------+              |
   |  Underwriter              Credit Bureau (actor,     |
   |                            drawn as a system icon)  |
   +--------------------------------------------------+

   Annotation. "In 2 of 10 cases the report is delayed
                more than 24 hours (told as a variation)"

   Sentence reading of activity 1.
     Actor(Applicant) --verb(submits)--> WorkObject(document)
```

## 7. Dynamics

A Domain Storytelling session runs as a live, synchronous conversation, not
as an asynchronous document review, and its dynamics are the dynamics of
facilitated conversation rather than the dynamics of a running program.

The session opens with the moderator setting the scope, deciding which
concrete scenario is about to be told, at what granularity, and whether
software systems will appear as actors in this telling or be left out to keep
the focus on the human domain, the domain-purity choice covered under
dimension 8. The domain expert then begins narrating a single concrete
example, using a real or realistic instance rather than a generalized rule,
for example "a customer named Jonas orders three chairs" rather than
"customers order products."

As the expert speaks, the moderator converts each clause into the next
numbered pictogram on the board in real time, choosing an existing actor or
work object icon when one already fits or introducing a new one when the
sentence names something not yet on the board. The moderator reads each new
sentence back to the expert immediately after drawing it, which is the
technique's core error-catching mechanism, because the expert hears their own
words reflected back through the picture and reliably notices when the
picture says something subtly different from what they meant, a dynamic Hofer
and Schwentner call out repeatedly across the book as the primary source of
the method's value. misunderstandings surface during the thirty-minute
session rather than during a code review three months later.

When the expert's narration reaches a branch, an exception, or a variation
worth capturing, the moderator has three live options available in the
moment. note it as an annotation and keep the main story moving, draw it as a
Group boundary marking an alternative path, or, when the variation is
substantial enough to deserve its own full telling, park it and schedule it
as a separate story rather than overloading the current diagram. This
decision, made in the moment by the moderator in consultation with the room,
is a recurring point of facilitation skill referenced under dimension 3.

The session closes when the expert reaches a natural end point in the
concrete example, at which point the moderator reads the complete numbered
sequence back to the room as a final check, and the resulting artifact, the
finished pictogram with its numbered activities, becomes an input to whatever
downstream design activity the team runs next, whether that is drafting
Ubiquitous Language glossary entries, identifying candidate Bounded Context
seams, or writing acceptance criteria grounded in the concrete example just
told.

```text
Expert          Moderator                    Board / Listeners
  |                 |                              |
  |--speaks s1------>|                              |
  |                 |--draws pictogram 1----------->|
  |<--reads back s1--|                              |
  |--confirms/fixes->|                              |
  |                 |--adjusts if needed----------->|
  |--speaks s2------>|                              |
  |                 |--draws pictogram 2----------->|
  |                 |--asks clarifying question----->|
  |--answers-------->|                              |
  |          (repeat for each sentence)              |
  |--reaches end----->|                              |
  |                 |--reads full sequence back----->|
  |<--confirms whole story is accurate---------------|
```

## 8. Implementation variants

Whiteboard and sticky-note variant. The oldest and lowest-tech form of the
technique, run with a physical whiteboard, printed or hand-drawn actor and
work-object icons, and a marker for the numbered arrows. Hofer and
Schwentner's book presents this as the default starting form because it
requires no tooling and no setup cost, and a co-located room can begin a
session within minutes of deciding to run one.

Digital tool variant, Egon. WPS built and open-sourced a purpose-made
modeling tool, Egon, distributed at https://egon.io and on GitHub at
https://github.com/WPS/egon.io under the GPLv3 license with two MIT-licensed
dependencies, diagram-js and ngx-color-picker, confirmed by inspection of the
repository's own README, verified 2026-08-02. Egon runs entirely in the
browser, requires no account, and, per the same README, does not track users
or transmit or store their diagram data, which matters directly for domain
experts in regulated industries who are wary of an unfamiliar SaaS tool
capturing internal process detail. This is the variant most cited in current
teaching material and workshops because it produces a shareable, exportable
diagram without requiring a physical room.

Remote and hybrid variant. When the domain expert and the listening team are
not co-located, the moderator drives a shared digital board, typically Egon
or a general-purpose whiteboard tool repurposed with the pictogram set, while
the expert narrates over a video call. This variant preserves the live
read-back dynamic that is central to the technique's error-catching value,
but loses some of the room-energy that helps a moderator sense when a
listener is confused and has not spoken up, a limitation acknowledged in
practitioner writeups of remote sessions cited under dimension 11.

Scope variants, chosen deliberately per story rather than fixed for a whole
project. Hofer and Schwentner describe three independent scope dimensions a
moderator sets before a session begins. granularity, which ranges from a
coarse whole-organization overview story down to a fine-grained single-task
story. temporality, whether the story captures the as-is workflow as it
happens today or a to-be workflow describing a desired future state. and
domain purity, whether software systems appear on the board as actors at
all, or are deliberately excluded so the story describes only the human
domain, independent of any current or future implementation. Choosing these
three settings correctly for the question at hand is itself a skill the book
devotes a full chapter to, because a story drawn at the wrong granularity for
its purpose, for example a fine-grained single-task story used to try to
identify Bounded Context seams across an entire organization, produces a
diagram too large to be legible or too narrow to answer the question it was
meant to answer.

## 9. Known production uses

WPS - Workplace Solutions GmbH, the Hamburg-based software consultancy where
Hofer and Schwentner work, developed and has used Domain Storytelling on real
client engagements for roughly a decade before publishing it, and continues
to run and publish domain storytelling client work on the company's own
site, https://www.wps.de/en/wps/computing-time/domain-storytelling, verified
2026-08-02, which the company maintains as an ongoing reference for the
technique's use in its consulting practice.

The Egon modeling tool, hosted at https://github.com/WPS/egon.io, is
open source software with a public issue tracker, release history, and a
companion example repository at https://github.com/WPS/egon.io-examples
containing worked, non-fictional example stories, including one modeled live
with a real domain expert during a public meetup with a recorded session,
both confirmed by inspection of the WPS GitHub organization, verified
2026-08-02, which together constitute a real, publicly inspectable body of
production usage of the notation rather than only the book's illustrative
examples.

DDD Europe, the largest recurring international Domain-Driven Design
conference, includes Domain Storytelling as a standing session topic in its
program, confirmed for the 2026 program at
https://2026.dddeurope.com/program/domain-storytelling/, verified 2026-08-02,
which is direct evidence that practitioners are still bringing real
engagement experience with the technique to a peer conference years after the
book's publication rather than the technique having faded to purely academic
interest.

The Open Practice Library, a community-maintained, Red Hat-affiliated
compendium of practices used in real enterprise consulting engagements,
lists Domain Storytelling as a documented practice at
https://openpracticelibrary.com/practice/domain-storytelling/, verified
2026-08-02, indicating adoption in enterprise consulting contexts beyond WPS's
own practice.

## 10. Consequences

Positive. A domain story produced in a well-run session is directly
legible to the domain expert who told it, because the notation was chosen
specifically to require no technical training to read, which means the
validation of correctness happens in the room, live, rather than in a later
review cycle where the domain expert has to first learn to read a technical
artifact before they can even judge whether it is right. The concrete,
scenario-based framing surfaces disagreement between stakeholders quickly,
because two people's differing mental models of "how this works" become
visibly different diagrams the moment each is asked to walk through a
specific real example, a disagreement that stays hidden far longer when each
side is only asked to review the same abstract written specification.
Because activities are drawn using the domain's own verbs rather than generic
technical verbs, the resulting artifact feeds directly into building the
Ubiquitous Language vocabulary a Domain-Driven Design effort needs, and the
work objects and actor boundaries that emerge across a small portfolio of
stories are a concrete, evidence-based input into deciding where a Bounded
Context should be drawn, rather than a boundary chosen from an org chart or a
guess.

Negative. A single story is a single concrete path through the domain and
does not, by itself, describe the domain's full space of variation, so
achieving useful coverage of a real workflow requires running multiple
sessions for the happy path and for each significant variant, which is a real
time cost that a team pressed for schedule will be tempted to shortcut. The
notation's deliberate minimalism means it cannot carry detailed technical
design information, conditional logic, timing constraints, or data-schema
detail, so a team that mistakes a domain story for a finished specification
and skips further design work will ship a system that satisfies the narrated
scenario and nothing else. The technique's value is bottlenecked on the
availability of a genuine domain expert and on facilitation skill. a session
run with a proxy narrator who does not actually do the work, or run by a
moderator inexperienced enough to let ambiguous sentences pass unclarified,
produces a diagram that looks the same as a good one but carries none of the
accuracy guarantee. And because the artifact is, in its native form, a
picture rather than a structured, machine-readable specification, it does not
by itself version, diff, or integrate into an automated pipeline the way a
formal specification language would, so a team that wants traceability from
domain story to code has to build that traceability deliberately, typically
by hand-linking a story's activities to the acceptance tests or user stories
it informed.

## 11. Failure modes and misuse

**The silent, uncorrected diagram.** Symptom. The diagram from a session
looks impressively detailed but the domain expert never once corrected
anything the moderator drew. Cause. The moderator is narrating their own
assumption of the workflow and drawing it without genuinely listening for and
inviting correction, effectively producing a developer's guess dressed up in
the notation, which defeats the technique's entire error-catching purpose.
Fix. The moderator must deliberately slow down, read every sentence back as a
question rather than a statement, and treat silence from the expert as a
prompt to ask directly whether the drawn sentence is accurate rather than as
tacit agreement.

**The single story treated as complete coverage.** Symptom. A team runs
exactly one domain story early in a project and then treats that single
artifact as a complete specification for the rest of the build, later
discovering in implementation that an entire branch of the workflow, the one
where the payment fails or the shipment is returned, was never captured.
Cause. Conflating running one session with having covered the domain, when a
single concrete scenario by definition only covers the one path it narrated.
Fix. Deliberately build a small portfolio of stories, explicitly including
the significant exception and variation paths, and treat the portfolio, not
any single story, as the coverage unit.

**The unreadably large diagram.** Symptom. The pictographic diagram grows so
large and so dense that even the domain expert who told it struggles to
follow the numbering, and new listeners cannot orient themselves in it at
all. Cause. The moderator set the wrong granularity for the story's purpose,
typically trying to capture an entire end-to-end organizational process in
one fine-grained story instead of first telling a coarse overview story and
then a set of finer stories for each subprocess. Fix. Explicitly decide the
granularity, per dimension 8, before the session starts, and split an
over-large story into a coarse parent story plus several child stories the
moment the diagram becomes hard to read.

**The technical drift that loses the expert.** Symptom. A domain story that
includes software systems as actors turns into a de facto technical
architecture diagram, and the domain expert stops participating actively
because the conversation has drifted into system names and integration
detail they cannot evaluate. Cause. The domain-purity scope setting was left
implicit rather than chosen deliberately, and the moderator let the
software-actor inclusion pull the session toward a technical audience rather
than the domain-expert audience the technique depends on. Fix. For any story
whose primary purpose is building shared domain understanding rather than
documenting an existing integration, run it software-free, deliberately
excluding system actors, and reserve software-actor stories for a separate,
explicitly technical audience.

**The disengaged remote session.** Symptom. A remote session over video call
runs noticeably worse than an equivalent co-located session, with the expert
disengaging and fewer corrections surfacing. Cause. The moderator loses the
room-level social signal, a listener's confused expression or hesitation,
that prompts a clarifying question in a co-located session, and nobody
compensates for that loss deliberately. Fix. In remote sessions, the
moderator should explicitly solicit questions from listeners at regular
checkpoints rather than relying on visible body language, and should read
sentences back more slowly and more often than a co-located session would
require.

## 12. Trade-off matrix

| Force | Domain Storytelling | Event Storming | Written requirements interview |
|---|---|---|---|
| Domain-expert legibility of the artifact | High, three icons and an arrow, no training needed | Medium, sticky-note conventions need brief onboarding | High to read, but ambiguous to validate against reality |
| Error and disagreement detection | High, live and immediate during the session | Medium, disagreement surfaces but sequence and actor detail is looser | Low, disagreement often stays hidden until implementation |
| Coverage per session | Narrow, one concrete scenario per story | Broad, a full timeline of events across a process in one session | Broad, but coverage depends entirely on interviewer thoroughness |
| Facilitation skill required | Medium to high, moderator must draw and clarify in real time | Medium, less strict moderation, more emergent participation | Low technique skill, but high interviewing and writing skill |
| Fit for low-technical-background participants | High, explicitly designed for this audience | Lower, works best with a mixed technical and business room | High for the participant, low for downstream traceability |
| Traceability into structured artifacts | Low natively, picture-to-spec linking is manual | Low to medium, sticky notes photographed and transcribed | Medium, prose can be directly quoted into requirements docs |

## 13. Related and incompatible patterns

Domain Storytelling composes directly with Ubiquitous Language, because the
domain vocabulary a story surfaces, particularly the verbs used for
activities and the nouns used for work objects, is precisely the raw material
a team distills into its glossary. Hofer and Schwentner treat this as one of
the technique's primary purposes rather than an incidental side effect. It
composes with Bounded Context and Context Mapping, because a portfolio of
stories, each naturally clustering around a coherent set of actors and work
objects, is direct evidence for where a context boundary belongs, and the
handoffs visible between stories, where a work object crosses from one
actor's group to another's, often point straight at the integration
relationships a Context Map needs to describe. It composes with Domain Event
identification, because each numbered activity in a story is a candidate
domain event once the team moves from strategic discovery into tactical
design, though the two notations describe the same underlying reality from
different angles, actor-centric process narrative in Domain Storytelling
versus event-centric timeline in Event Storming.

Event Storming is the closest sibling technique rather than a strict
alternative, and the two are frequently used together on the same project
at different points, a complementary relationship documented directly by
INNOQ's practitioner comparison at
https://www.innoq.com/de/blog/vergleich-event-storming-und-domain-storytelling/,
verified 2026-08-02, and echoed by Axxes' comparison at
https://www.axxes.com/en/insights/event-storming-domain-storytelling, verified
2026-08-02. The practical distinction both sources converge on is audience
and shape. Event Storming's orange-sticky-note timeline format brings a
larger, more technically mixed group into an unmoderated or lightly
moderated brainstorm well suited to surfacing a broad process quickly, while
Domain Storytelling's stricter, moderator-driven, pictographic sentence
format is better suited to a smaller room where a specific domain expert
needs to narrate a precise, concrete example and have every sentence checked
for accuracy as it is drawn, which is why teams with a low-technical-fluency
domain expert, or a need for very high fidelity on a specific workflow,
reach for Domain Storytelling, while teams needing a fast, broad first pass
across an unfamiliar large process reach for Event Storming.

No pattern in this catalog actively conflicts with Domain Storytelling, since
it operates entirely upstream of implementation and produces no structural or
runtime artifact that a code-level pattern could contradict. The nearest thing
to an incompatibility is scope misuse, attempting to use a domain story in
place of a Specification pattern's precise business-rule expression, or in
place of a BPMN process definition destined for a workflow engine, both of
which require a formality and completeness the pictographic notation was
deliberately not designed to provide.

## 14. Refactoring path in and out

Introducing Domain Storytelling into a team that has no existing modeling
practice begins with identifying one concrete, narrow scenario worth telling,
not the whole domain, and finding the one domain expert who actually performs
that scenario, since a proxy narrator undermines the technique from the
first sentence. The moderator, who does not need deep prior facilitation
experience but does benefit from having read the book's workshop chapters or
run a practice session on a familiar toy domain first, sets the story's scope
along the three dimensions from dimension 8, granularity, temporality, and
domain purity, explicitly and out loud before the expert begins narrating.
The first session should be treated as a calibration run. expect it to run
long, expect the moderator to need practice reading sentences back fluently,
and capture what worked and what did not before scheduling the next story.
From there, a team builds up a small, deliberately curated portfolio of
stories covering the domain's happy paths and its significant variants, using
each story's actors, work objects, and handoffs as direct input into
Ubiquitous Language glossary entries and into early hypotheses about Bounded
Context boundaries, rather than trying to capture the entire domain in one
oversized session.

Removing Domain Storytelling from active use, once a team's strategic
understanding of a domain has stabilized, is simply a matter of no longer
scheduling new sessions. the technique leaves behind a durable artifact, the
finished diagrams, that continues to serve as onboarding material and
historical record without requiring any ongoing process, tooling, or
maintenance once a portfolio of stories has answered the strategic questions
it was run to answer. Because the technique produces no code and no runtime
structure, there is no equivalent of a code-level strangle-and-remove step.
retiring it is purely a facilitation-practice decision, typically made when a
domain has stabilized enough that new features can be scoped confidently from
the existing Ubiquitous Language and Bounded Context map without a fresh
storytelling session, and revisited only when the team enters a genuinely new
or significantly changed part of the domain.

## 15. Testing and verification

This is engineering judgement, since Domain Storytelling produces a
discovery artifact rather than executable code, and verification here means
verifying the artifact's fidelity to the real domain rather than running an
automated test suite. The primary verification mechanism is built directly
into the technique itself. the moderator's live read-back of every sentence
to the domain expert is a continuous, in-session correctness check, and a
session where the expert never once corrected anything drawn should itself be
treated as a signal worth investigating, per the first failure mode under
dimension 11, rather than as evidence of a perfectly accurate first draft.
Beyond the session itself, the most reliable downstream verification
technique reported in practitioner material is triangulation. telling the
same or a closely related scenario with a second domain expert who performs
the same role, and comparing the two resulting stories, since a real
divergence between two experts describing the same workflow is exactly the
kind of hidden disagreement the technique is meant to surface, and a
convergence between them is meaningful confirmation that the story reflects
the actual domain rather than one person's idiosyncratic account of it. A
completed story should also be walked back through with a listener who was
not in the original session, asking them to read the diagram aloud as a set
of sentences without help. if they cannot reconstruct the sequence and
meaning from the diagram alone, the diagram has failed its own core design
goal of legibility and needs revision before it is trusted as an input to
downstream design.

## 16. Observability signals

This is engineering judgement, since there is no running system to
instrument. The useful signals here are practice-health signals a team can
watch across a Domain-Driven Design discovery effort. A healthy signal is a
growing, curated portfolio of stories where new stories increasingly reuse
actors and work objects already established by earlier stories rather than
introducing entirely new vocabulary each time, which indicates the team's
Ubiquitous Language is converging rather than still fragmenting. A healthy
signal is domain experts actively correcting diagrams during sessions,
since active correction is direct evidence the technique is doing its job.
a run of several consecutive sessions with zero corrections is the unhealthy
counterpart signal, worth investigating per dimension 11's first failure
mode. A healthy signal is downstream artifacts, glossary entries, Bounded
Context boundary proposals, acceptance criteria, visibly tracing back to a
specific story and a specific numbered activity within it, which indicates
the stories are actually being used rather than filed away after the
workshop ends. An unhealthy signal is a growing gap between the number of
stories told and the number of stories anyone can locate or reference weeks
later, which indicates the artifacts are not being captured or shared
durably enough to keep earning their workshop cost.

## 17. Security and privacy implications

Domain Storytelling sessions frequently surface real business process detail,
real customer or case examples, and sometimes real personal data used as the
concrete scenario a domain expert chooses to narrate, for example a session
about loan underwriting might use a real applicant's situation as the
walked-through example even when the name is fictionalized. Teams running
sessions in regulated domains, healthcare, finance, insurance, should treat
the choice of example scenario deliberately, using anonymized or clearly
fictional details rather than a live customer's actual data, and should
apply the same data-handling discipline to the resulting diagrams and any
exported files as they would to other internal process documentation,
particularly when a session is recorded on video, since a recorded narration
can capture more incidental detail than the final diagram alone. The
Egon tool's stated design choice, not tracking users and not processing or
storing diagram data server-side, per the WPS/egon.io README verified
2026-08-02, is directly relevant here because it means a team's diagrams and
any sensitive example data embedded in them stay local to the machine running
the browser tool rather than being retained by a third-party SaaS vendor, an
explicit design decision the maintainers made for exactly this reason. Beyond
data handling in the diagrams themselves, the technique carries no attack
surface implication, since it produces no runtime system and executes no
code. its security relevance is entirely about the information-handling
discipline of the workshop and its artifacts, not about a vulnerability class
in a running program.

## 18. References

1. Stefan Hofer and Henning Schwentner, "Domain Storytelling. A
   Collaborative, Visual, and Agile Way to Build Domain-Driven Software,"
   Addison-Wesley Signature Series (Vernon), Addison-Wesley Professional,
   first edition, September 17, 2021, ISBN 978-0-13-745891-2. Verified via
   publisher and retailer listing at
   https://www.amazon.com/Domain-Storytelling-Collaborative-Domain-Driven-Addison-Wesley/dp/0137458916,
   2026-08-02.
2. Domain Storytelling official companion site, maintained by Stefan Hofer
   and Henning Schwentner, https://domainstorytelling.org, verified
   2026-08-02.
3. Domain Storytelling Quick-Start Guide,
   https://domainstorytelling.org/quick-start-guide, verified 2026-08-02.
   Source for the pictographic element definitions in dimension 5 and the
   three scope dimensions in dimension 8.
4. Egon.io, official tool site, https://egon.io, verified 2026-08-02.
5. WPS/egon.io, GitHub repository, https://github.com/WPS/egon.io,
   verified 2026-08-02. Source for license, dependency licensing, and
   maintainer identity used in dimensions 8, 9, and 17.
6. WPS/egon.io-examples, GitHub repository,
   https://github.com/WPS/egon.io-examples, verified 2026-08-02. Source for
   real, non-fictional worked example stories cited in dimension 9.
7. WPS - Workplace Solutions GmbH, "Domain Storytelling" practice page,
   https://www.wps.de/en/wps/computing-time/domain-storytelling, verified
   2026-08-02.
8. DDD Europe 2026 conference program, "Domain Storytelling" session listing,
   https://2026.dddeurope.com/program/domain-storytelling/, verified
   2026-08-02.
9. Open Practice Library, "Domain Storytelling" practice entry,
   https://openpracticelibrary.com/practice/domain-storytelling/, verified
   2026-08-02.
10. Alberto Brandolini, Event Storming, official resource site,
    https://www.eventstorming.com, verified 2026-08-02. Source for the
    sibling-technique comparison in dimension 13.
11. INNOQ, "Event Storming und Domain Story Telling. Ein Vergleich,"
    https://www.innoq.com/de/blog/vergleich-event-storming-und-domain-storytelling/,
    verified 2026-08-02. Source for the audience and shape comparison in
    dimension 13.
12. Axxes, "Event Storming & Domain Storytelling,"
    https://www.axxes.com/en/insights/event-storming-domain-storytelling,
    verified 2026-08-02.
13. Eric Evans, "Domain-Driven Design. Tackling Complexity in the Heart of
    Software," Addison-Wesley, 2003. Referenced for the strategic-design
    context Domain Storytelling feeds into, per dimension 2 and dimension 13.

## Code examples

Domain Storytelling has no runtime object structure to implement, since it is
a facilitation technique that produces a diagram rather than a program. The
code below models the technique's own data shape instead, a small library
that lets a team build a domain story programmatically, render it as its
canonical numbered-sentence form, and validate it against the notation's own
integrity rules, specifically that sequence numbers are contiguous starting
at one and that every activity references an actor and a work object already
introduced to the story. This validation logic mirrors, in code, exactly the
kind of ambiguity check a moderator performs by hand during a live session,
which makes the example a faithful, idiomatic representation of the pattern
rather than an arbitrary data model. Three languages are shown, Python and
TypeScript, because tooling for lightweight collaborative-modeling artifacts
in real teams is overwhelmingly written in one of these two for internal
tooling and browser-based diagram tools such as Egon itself, and Go, because
the same validation logic translates cleanly into a small, dependency-free
command-line tool a team could run in a documentation-build pipeline to lint
exported story files. C#, Kotlin, and Swift are omitted because the pattern
has no idiomatic variation across those languages beyond a mechanical
translation of the same three languages' logic, and Rust is omitted for the
same reason, to avoid padding the entry with four near-identical restatements
of one small data model.

### Python

```python
from dataclasses import dataclass, field


@dataclass
class Actor:
    id: str
    name: str
    kind: str = "person"


@dataclass
class WorkObject:
    id: str
    name: str


@dataclass
class Activity:
    number: int
    actor_id: str
    verb: str
    object_id: str
    receiver_id: str | None = None


class DomainStoryError(ValueError):
    pass


@dataclass
class DomainStory:
    title: str
    actors: dict[str, Actor] = field(default_factory=dict)
    work_objects: dict[str, WorkObject] = field(default_factory=dict)
    activities: list[Activity] = field(default_factory=list)

    def add_actor(self, actor: Actor) -> None:
        self.actors[actor.id] = actor

    def add_work_object(self, work_object: WorkObject) -> None:
        self.work_objects[work_object.id] = work_object

    def add_activity(self, activity: Activity) -> None:
        self.activities.append(activity)

    def validate(self) -> None:
        expected = list(range(1, len(self.activities) + 1))
        actual = sorted(activity.number for activity in self.activities)
        if actual != expected:
            raise DomainStoryError(
                f"sequence numbers must be contiguous from 1, got {actual}"
            )
        for activity in self.activities:
            if activity.actor_id not in self.actors:
                raise DomainStoryError(
                    f"activity {activity.number} references unknown actor "
                    f"'{activity.actor_id}'"
                )
            if activity.object_id not in self.work_objects:
                raise DomainStoryError(
                    f"activity {activity.number} references unknown work "
                    f"object '{activity.object_id}'"
                )
            if activity.receiver_id and activity.receiver_id not in self.actors:
                raise DomainStoryError(
                    f"activity {activity.number} references unknown "
                    f"receiver '{activity.receiver_id}'"
                )

    def render(self) -> str:
        self.validate()
        lines = [self.title, "=" * len(self.title)]
        ordered = sorted(self.activities, key=lambda a: a.number)
        for activity in ordered:
            actor = self.actors[activity.actor_id].name
            obj = self.work_objects[activity.object_id].name
            sentence = f"{activity.number}. {actor} {activity.verb} {obj}"
            if activity.receiver_id:
                receiver = self.actors[activity.receiver_id].name
                sentence += f" with {receiver}"
            lines.append(sentence)
        return "\n".join(lines)


def build_loan_application_story() -> DomainStory:
    story = DomainStory(title="Loan application intake")
    story.add_actor(Actor(id="applicant", name="the applicant"))
    story.add_actor(Actor(id="underwriter", name="the underwriter"))
    story.add_work_object(WorkObject(id="application", name="an application"))
    story.add_work_object(WorkObject(id="credit_report", name="a credit report"))
    story.add_activity(
        Activity(number=1, actor_id="applicant", verb="submits", object_id="application")
    )
    story.add_activity(
        Activity(
            number=2,
            actor_id="underwriter",
            verb="reviews",
            object_id="application",
            receiver_id="applicant",
        )
    )
    story.add_activity(
        Activity(number=3, actor_id="underwriter", verb="requests", object_id="credit_report")
    )
    return story


if __name__ == "__main__":
    story = build_loan_application_story()
    print(story.render())

    broken = build_loan_application_story()
    broken.activities.append(
        Activity(number=5, actor_id="applicant", verb="cancels", object_id="application")
    )
    try:
        broken.validate()
    except DomainStoryError as error:
        print(f"\nvalidation caught a gap: {error}")
```

Run and verified output.

```text
$ python3 domain_storytelling.py
Loan application intake
=======================
1. the applicant submits an application
2. the underwriter reviews an application with the applicant
3. the underwriter requests a credit report

validation caught a gap: sequence numbers must be contiguous from 1, got [1, 2, 3, 5]
```

### TypeScript

```typescript
type ActorKind = "person" | "group" | "system";

interface Actor {
  id: string;
  name: string;
  kind: ActorKind;
}

interface WorkObject {
  id: string;
  name: string;
}

interface Activity {
  number: number;
  actorId: string;
  verb: string;
  objectId: string;
  receiverId?: string;
}

class DomainStoryError extends Error {}

class DomainStory {
  title: string;
  actors = new Map<string, Actor>();
  workObjects = new Map<string, WorkObject>();
  activities: Activity[] = [];

  constructor(title: string) {
    this.title = title;
  }

  addActor(actor: Actor): void {
    this.actors.set(actor.id, actor);
  }

  addWorkObject(workObject: WorkObject): void {
    this.workObjects.set(workObject.id, workObject);
  }

  addActivity(activity: Activity): void {
    this.activities.push(activity);
  }

  validate(): void {
    const expected = this.activities.map((_, index) => index + 1);
    const actual = [...this.activities]
      .map((activity) => activity.number)
      .sort((a, b) => a - b);
    if (JSON.stringify(actual) !== JSON.stringify(expected)) {
      throw new DomainStoryError(
        `sequence numbers must be contiguous from 1, got ${actual.join(", ")}`
      );
    }
    for (const activity of this.activities) {
      if (!this.actors.has(activity.actorId)) {
        throw new DomainStoryError(
          `activity ${activity.number} references unknown actor '${activity.actorId}'`
        );
      }
      if (!this.workObjects.has(activity.objectId)) {
        throw new DomainStoryError(
          `activity ${activity.number} references unknown work object '${activity.objectId}'`
        );
      }
      if (activity.receiverId && !this.actors.has(activity.receiverId)) {
        throw new DomainStoryError(
          `activity ${activity.number} references unknown receiver '${activity.receiverId}'`
        );
      }
    }
  }

  render(): string {
    this.validate();
    const lines = [this.title, "=".repeat(this.title.length)];
    const ordered = [...this.activities].sort((a, b) => a.number - b.number);
    for (const activity of ordered) {
      const actor = this.actors.get(activity.actorId)!.name;
      const obj = this.workObjects.get(activity.objectId)!.name;
      let sentence = `${activity.number}. ${actor} ${activity.verb} ${obj}`;
      if (activity.receiverId) {
        const receiver = this.actors.get(activity.receiverId)!.name;
        sentence += ` with ${receiver}`;
      }
      lines.push(sentence);
    }
    return lines.join("\n");
  }
}

function buildLoanApplicationStory(): DomainStory {
  const story = new DomainStory("Loan application intake");
  story.addActor({ id: "applicant", name: "the applicant", kind: "person" });
  story.addActor({ id: "underwriter", name: "the underwriter", kind: "person" });
  story.addWorkObject({ id: "application", name: "an application" });
  story.addWorkObject({ id: "credit_report", name: "a credit report" });
  story.addActivity({ number: 1, actorId: "applicant", verb: "submits", objectId: "application" });
  story.addActivity({
    number: 2,
    actorId: "underwriter",
    verb: "reviews",
    objectId: "application",
    receiverId: "applicant",
  });
  story.addActivity({ number: 3, actorId: "underwriter", verb: "requests", objectId: "credit_report" });
  return story;
}

const story = buildLoanApplicationStory();
console.log(story.render());

const broken = buildLoanApplicationStory();
broken.activities.push({ number: 5, actorId: "applicant", verb: "cancels", objectId: "application" });
try {
  broken.validate();
} catch (error) {
  if (error instanceof DomainStoryError) {
    console.log(`\nvalidation caught a gap: ${error.message}`);
  }
}
```

Run and verified output.

```text
$ npx tsc domain_storytelling.ts --target es2020 --module commonjs --strict
$ node domain_storytelling.js
Loan application intake
=======================
1. the applicant submits an application
2. the underwriter reviews an application with the applicant
3. the underwriter requests a credit report

validation caught a gap: sequence numbers must be contiguous from 1, got 1, 2, 3, 5
```

### Go

```go
package main

import (
	"fmt"
	"sort"
	"strings"
)

type Actor struct {
	ID   string
	Name string
}

type WorkObject struct {
	ID   string
	Name string
}

type Activity struct {
	Number     int
	ActorID    string
	Verb       string
	ObjectID   string
	ReceiverID string
}

type DomainStory struct {
	Title       string
	Actors      map[string]Actor
	WorkObjects map[string]WorkObject
	Activities  []Activity
}

func NewDomainStory(title string) *DomainStory {
	return &DomainStory{
		Title:       title,
		Actors:      map[string]Actor{},
		WorkObjects: map[string]WorkObject{},
	}
}

func (s *DomainStory) AddActor(a Actor)           { s.Actors[a.ID] = a }
func (s *DomainStory) AddWorkObject(w WorkObject) { s.WorkObjects[w.ID] = w }
func (s *DomainStory) AddActivity(a Activity)     { s.Activities = append(s.Activities, a) }

func (s *DomainStory) Validate() error {
	actual := make([]int, len(s.Activities))
	for i, a := range s.Activities {
		actual[i] = a.Number
	}
	sort.Ints(actual)
	for i, n := range actual {
		if n != i+1 {
			return fmt.Errorf("sequence numbers must be contiguous from 1, got %v", actual)
		}
	}
	for _, a := range s.Activities {
		if _, ok := s.Actors[a.ActorID]; !ok {
			return fmt.Errorf("activity %d references unknown actor '%s'", a.Number, a.ActorID)
		}
		if _, ok := s.WorkObjects[a.ObjectID]; !ok {
			return fmt.Errorf("activity %d references unknown work object '%s'", a.Number, a.ObjectID)
		}
		if a.ReceiverID != "" {
			if _, ok := s.Actors[a.ReceiverID]; !ok {
				return fmt.Errorf("activity %d references unknown receiver '%s'", a.Number, a.ReceiverID)
			}
		}
	}
	return nil
}

func (s *DomainStory) Render() (string, error) {
	if err := s.Validate(); err != nil {
		return "", err
	}
	ordered := make([]Activity, len(s.Activities))
	copy(ordered, s.Activities)
	sort.Slice(ordered, func(i, j int) bool { return ordered[i].Number < ordered[j].Number })

	var b strings.Builder
	b.WriteString(s.Title + "\n")
	b.WriteString(strings.Repeat("=", len(s.Title)) + "\n")
	for _, a := range ordered {
		actor := s.Actors[a.ActorID].Name
		obj := s.WorkObjects[a.ObjectID].Name
		sentence := fmt.Sprintf("%d. %s %s %s", a.Number, actor, a.Verb, obj)
		if a.ReceiverID != "" {
			sentence += " with " + s.Actors[a.ReceiverID].Name
		}
		b.WriteString(sentence + "\n")
	}
	return strings.TrimRight(b.String(), "\n"), nil
}

func buildLoanApplicationStory() *DomainStory {
	story := NewDomainStory("Loan application intake")
	story.AddActor(Actor{ID: "applicant", Name: "the applicant"})
	story.AddActor(Actor{ID: "underwriter", Name: "the underwriter"})
	story.AddWorkObject(WorkObject{ID: "application", Name: "an application"})
	story.AddWorkObject(WorkObject{ID: "credit_report", Name: "a credit report"})
	story.AddActivity(Activity{Number: 1, ActorID: "applicant", Verb: "submits", ObjectID: "application"})
	story.AddActivity(Activity{
		Number: 2, ActorID: "underwriter", Verb: "reviews",
		ObjectID: "application", ReceiverID: "applicant",
	})
	story.AddActivity(Activity{Number: 3, ActorID: "underwriter", Verb: "requests", ObjectID: "credit_report"})
	return story
}

func main() {
	story := buildLoanApplicationStory()
	rendered, err := story.Render()
	if err != nil {
		fmt.Println("unexpected error.", err)
		return
	}
	fmt.Println(rendered)

	broken := buildLoanApplicationStory()
	broken.AddActivity(Activity{Number: 5, ActorID: "applicant", Verb: "cancels", ObjectID: "application"})
	if err := broken.Validate(); err != nil {
		fmt.Printf("\nvalidation caught a gap. %s\n", err)
	}
}
```

Run and verified output.

```text
$ go run domain_storytelling.go
Loan application intake
=======================
1. the applicant submits an application
2. the underwriter reviews an application with the applicant
3. the underwriter requests a credit report

validation caught a gap. sequence numbers must be contiguous from 1, got [1 2 3 5]
```
