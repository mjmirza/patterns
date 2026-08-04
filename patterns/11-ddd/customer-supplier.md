---
name: Customer-Supplier
slug: customer-supplier
family: 11-ddd
category: Strategic Design
aliases: [Customer/Supplier Development Teams, Customer-Supplier Development Team Relationship, Customer-Supplier Context Relationship]
first_described: "Evans 2003"
maturity: canonical
related: [context-map, bounded-context, conformist, anticorruption-layer, open-host-service, published-language, ubiquitous-language]
incompatible_with: [conformist, shared-kernel]
verified: 2026-08-02
---

## 1. Name, aliases, and lineage

The canonical name is Customer-Supplier, written in the original source as
"Customer/Supplier Development Teams." Eric Evans introduced it in "Domain-
Driven Design. Tackling Complexity in the Heart of Software" (Addison-Wesley,
2003), Part IV, chapter 14, "Maintaining Model Integrity," as one of the
named relationship types a team can assign to an edge on a Context Map. The
companion summary document Evans and the Domain Language community maintain,
commonly cited as the "DDD Reference," restates the pattern in its condensed
form, and its wording is the one most practitioners quote directly, since
Evans's own phrasing there is compact and precise. The DDD Reference states,
"When two teams are in an upstream-downstream relationship, where the
upstream team may succeed independently of the fate of the downstream team,
the needs of the downstream come to be addressed in a variety of ways with a
wide range of consequences. Establish a clear customer/supplier relationship
between the two teams, meaning downstream priorities factor into upstream
planning. Negotiate and budget tasks for downstream requirements so that
everyone understands the commitment and schedule." This exact text is
reproduced and cited to the DDD Reference in the ddd-crew community's open
context-mapping guide, https://github.com/ddd-crew/context-mapping,
verified 2026-08-02, which is a widely used practitioner reference maintained
by DDD community members including Nick Tune and Kenny Baas-Schwegler.

Vaughn Vernon's "Implementing Domain-Driven Design" (Addison-Wesley, 2013),
chapter 3, "Context Maps," restates Customer-Supplier as one of the named
relationship types on a Context Map and works through a full example in the
book's running case study, discussed further under dimension 9 below. The
name is stable across the literature. Nobody in the DDD community uses a
genuinely different label for this relationship, though the abbreviation
used on diagrams varies, Evans's own notation marks the upstream side U and
the downstream side D, and some later tooling, including the open source
Context Mapper DSL discussed under dimension 8, marks the supplier side S and
the customer side C so the roles read directly off the diagram, C
for Customer, S for Supplier,
https://contextmapper.org/docs/customer-supplier/, verified 2026-08-02.

A naming caution worth stating plainly. Customer-Supplier as a Context Map
relationship is not the same thing as the general software-engineering
phrase "customer-supplier chain" used loosely in supply-chain or Lean
literature to describe any pair of collaborating teams. Within Domain-Driven
Design usage the term has a specific, narrow meaning, an upstream-downstream
relationship in which the downstream team has been given real, formal input
into the upstream team's planning, as distinguished sharply from
Conformist, where the downstream team has no such input at all. That
distinction, and not the generic "one team serves another" reading, is the
entire content of the pattern, and it is the reason the pattern exists as a
separate named relationship rather than being absorbed into the general idea
of an upstream-downstream dependency.

## 2. Problem and context

Any system large enough to be split across more than one Bounded Context,
see the bounded-context entry in this repository, produces integration
points where one context's model feeds into another's. Evans's Context Map
vocabulary names the direction of that dependency upstream and downstream,
the upstream context's model and its rate of change constrain what the
downstream context can build, while the downstream context's needs, by
default, constrain nothing about the upstream context at all. That default
asymmetry is the raw ingredient every relationship type on a Context Map is
built to manage, and Customer-Supplier is the pattern for the specific case
where the two teams behind those two contexts are willing, and organizationally
positioned, to negotiate rather than let the asymmetry run unmanaged.

The concrete situation a reader will recognize. A payments team owns the
Billing context and exposes an API that a Reporting team's Analytics context
consumes to build monthly usage dashboards for customers. The Billing team
is, in the org chart, senior to Reporting, ships on its own schedule, and has
never been asked whether a field the Reporting team needs, say a per-line-
item tax jurisdiction code, is on its plan. Six months into the project the
Reporting team discovers the field does not exist in the Billing API, files
a ticket, and waits, because nobody agreed in advance that Reporting's
priorities would factor into Billing's planning at all. The team is not
formally powerless, in principle a ticket can be filed and eventually
actioned, but there is no negotiated process, no shared understanding of
what commitment Billing has made to Reporting, and no budgeted time on
Billing's side for downstream requests. That absence of an explicit
commitment is the problem Customer-Supplier addresses. It does not remove
the upstream-downstream asymmetry, Billing still ships on its own schedule
and Reporting still cannot force a change, but it converts an implicit,
undocumented hope that requests will eventually get attention into an
explicit, negotiated, budgeted relationship in which the downstream team's
priorities are a real input to the upstream team's planning, not an
afterthought handled at the upstream team's convenience.

The context in which this pattern is chosen, as opposed to Conformist or
Anticorruption Layer, is specifically organizational, not technical. The
same API surface, the same two teams, the same two Bounded Contexts can sit
under a Customer-Supplier relationship in one company and a Conformist
relationship in another, and the difference is entirely about whether the
downstream team has a real seat at the upstream team's planning table, not
about anything visible in the code. This is the sharpest way to state why
Customer-Supplier belongs in the strategic-design family alongside Context
Map, Conformist, and Open Host Service rather than in any tactical, code-
level pattern family, its subject matter is a negotiated commitment between
two teams, and the code that results, an API contract, a set of integration
tests, is evidence of that commitment rather than the pattern itself.

## 3. Forces

Autonomy versus responsiveness. The upstream team wants to move at its own
pace, own its own backlog, and avoid becoming a support desk for every
downstream consumer's wish list. The downstream team wants confidence that
a need it has today will be addressed on a schedule it can plan around,
rather than an indefinite wait behind an unprioritized ticket queue.
Customer-Supplier resolves this tension by making the downstream team's
priorities a first-class, budgeted input to upstream planning, at the cost
of some of the upstream team's ability to move unilaterally. This is the
central force the pattern trades, and Evans is explicit in the DDD
Reference wording quoted above that the mechanism is to "negotiate and
budget tasks for downstream requirements," which is a concrete
organizational commitment, a line item on the upstream team's plan, not a
vague promise of goodwill.

Organizational standing. A Customer-Supplier relationship only functions
when the downstream team has some real standing to negotiate, whether that
standing comes from shared management, an internal service-level agreement,
a contractual obligation, or simple organizational proximity that makes
ignoring the downstream team's requests costly to the upstream team's own
reputation. Where that standing is absent, for example when the upstream
context is a third-party vendor's product with no incentive to respond to
any single customer's plan, the honest relationship is Conformist, and
labelling it Customer-Supplier on a map when no real negotiation happens is
a form of self-deception the pattern is designed to prevent by naming the
alternative outright.

Coordination cost versus integration quality. Negotiating and budgeting
downstream needs is not free, it consumes planning-meeting time, requires a
liaison or a formal request process, and slows down the upstream team's
ability to make unilateral changes without consulting anyone. In exchange
the resulting integration is measurably better matched to what the
downstream context actually needs, and the two teams build a shared,
explicit understanding of the interface's evolution, which reduces the
integration risk that would otherwise surface as breaking changes discovered
late. The pattern trades a fixed, ongoing coordination cost for a reduction
in integration risk and rework, and whether that trade is worth it depends
on how frequently the interface needs to change and how expensive a
surprise breaking change would be for the downstream team.

Team topology and cognitive load. A Customer-Supplier relationship implies
the upstream team carries some cognitive load on behalf of a downstream
team it does not fully control, since it must hold the downstream team's
needs in mind during its own planning. Matthew Skelton and Manuel Pais's
"Team Topologies" (IT Revolution Press, 2019) frames the related concept of
interaction modes between teams, and describes the alternative
"X-as-a-Service" interaction mode, where "the stream-aligned teams are still
responsible for the operation of their product, and direct their use of the
platform without expecting an elaborate collaboration with the platform
team," https://martinfowler.com/bliki/TeamTopologies.html, verified
2026-08-02. That framing is a useful contrast for this force. Customer-
Supplier deliberately accepts an ongoing collaboration cost that X-as-a-
Service and, in DDD's own vocabulary, Open Host Service are structured to
avoid, in exchange for a tighter fit between what the upstream team builds
and what the specific downstream team needs.

Cost of miscommunication versus cost of formal process. A small number of
tightly aligned teams can sometimes sustain a working Customer-Supplier
relationship through informal channels, a standing weekly sync, a shared
Slack channel, without a formal contract document. As the number of
downstream consumers of a single upstream context grows, informal
negotiation with each one individually becomes unworkable, and the
relationship either needs to formalize, written service-level expectations,
a documented request process, a shared backlog, or the upstream team needs
to shift toward Open Host Service, publishing one stable interface for all
consumers rather than negotiating bespoke commitments with each.

## 4. Applicability and non-applicability

Reach for Customer-Supplier when the following hold together, not
individually. The two teams are in an upstream-downstream relationship,
meaning the downstream context genuinely depends on the upstream context's
model or data and cannot function correctly without it. The downstream
team has some real organizational standing to negotiate with the upstream
team, whether through shared management, a service agreement, or simple
proximity that makes the upstream team's continued good relationship with
the downstream team valuable to the upstream team. The number of downstream
teams the upstream context serves is small enough that individually
negotiated commitments to each one remain tractable, roughly a handful of
consuming teams rather than dozens. The interface between the two contexts
is expected to change over time in ways that matter to the downstream team,
so that having a seat at the planning table is worth more than a single
static, one-time agreement would be. And critically, both teams are willing
to make the relationship explicit and to actually hold the negotiated
commitments, rather than naming it Customer-Supplier on a diagram while
behaving as Conformist in practice.

Do not reach for Customer-Supplier in the following situations, and use the
alternative named in parentheses instead. When the downstream team has no
real negotiating standing over the upstream team, for example the upstream
context is a third-party SaaS vendor's public API or an open source project
the organization does not control (use Conformist, and name the powerlessness
honestly rather than papering over it). When the upstream team serves so
many downstream consumers, often more than roughly ten to twenty, that
individually negotiating with each one is organizationally impossible and
what is actually needed is one stable, versioned public interface everyone
consumes on the same terms (use Open Host Service with a Published
Language). When both teams genuinely need to co-evolve the same model as
equal partners with joint responsibility for a shared outcome, rather than
one team's needs being downstream of the other's plan (use Partnership).
When the two contexts share so much of their domain model that maintaining
separate models and negotiating changes across a boundary would cost more
than accepting tight coupling between a small, jointly-owned code module
(use Shared Kernel, and accept that Shared Kernel and Customer-Supplier are
largely mutually exclusive strategies for the same underlying situation,
since Shared Kernel dissolves the boundary the negotiation would otherwise
manage). When the upstream context's model is actively hostile or poorly
suited to the downstream context's needs and no amount of negotiation is
expected to close that gap within a useful timeframe (use Anticorruption
Layer to protect the downstream model regardless of what the upstream team
does, which composes with Customer-Supplier rather than replacing it, since
a team can negotiate for improvements while also protecting itself in the
meantime). And when a single team owns both contexts, there is no
organizational boundary for Customer-Supplier to formalize, and the two
Bounded Contexts, if they remain separate at all, are more likely candidates
for Shared Kernel or simple internal API discipline than for a negotiated
inter-team relationship pattern.

## 5. Structure

Two Bounded Contexts, each owned by a distinct team, connected by a single
directed relationship on the Context Map. The upstream context, and its
owning team the supplier team, is the side whose model changes independently
and whose planning process is the target of the negotiation. The downstream
context, and its owning team the customer team, is the side that consumes
the upstream context's model or API and whose needs are the subject being
negotiated into the upstream team's plan.

The relationship carries three participants beyond the two contexts
themselves, each with a distinct responsibility. The negotiated interface
is the concrete artifact both teams agree constitutes the contract, an API
schema, a message format, a set of exported fields, whatever the downstream
context actually consumes. The planning process is the mechanism by which
downstream priorities enter upstream planning, a recurring meeting, a
shared backlog with a downstream-labelled lane, a formal request-and-
prioritization workflow, whichever fits the organization's existing
schedule. The acceptance tests, sometimes called conformance tests in the
literature, are automated tests, often owned or co-owned by the
downstream team and run as part of the upstream team's continuous
integration, that encode the downstream team's actual expectations of the
interface so that an unintentional breaking change is caught before it
reaches the downstream team's own build, discussed further under dimension
15. The presence or absence of that third participant is often the clearest
observable signal, from outside either team, of whether a relationship
labelled Customer-Supplier on a diagram is functioning as one in practice.

## 6. ASCII structure diagram

```
+----------------------------+           +----------------------------+
|   Supplier Team             |           |   Customer Team             |
|   (owns the Upstream        |           |   (owns the Downstream      |
|    Bounded Context)         |           |    Bounded Context)         |
+----------------------------+           +----------------------------+
             |                                          |
             | provides                                 | consumes
             v                                          v
   +-------------------+                       +-------------------+
   |  Upstream Context  |----- negotiated ----->|  Downstream Ctx    |
   |  U                 |      interface        |  D                 |
   +-------------------+                       +-------------------+
             ^                                          |
             |                                          |
             |          planning input (priorities,     |
             +------------------ requests) --------------+
             |
             v
   +----------------------------------------------------+
   |  Shared planning process                             |
   |  (release plan, backlog lane, or recurring negotiation) |
   +----------------------------------------------------+
             ^
             |
   +----------------------------------------------------+
   |  Downstream-owned acceptance / conformance tests,    |
   |  run inside the upstream context's own build         |
   +----------------------------------------------------+
```

## 7. Dynamics

The relationship has an initial negotiation phase and an ongoing steady-
state phase, and both are visible on a healthy Customer-Supplier pair.

```
Phase 1, initial negotiation
  Customer team  -> identifies needed data or capability from Upstream
  Customer team  -> raises the need with Supplier team's planning process
  Supplier team  -> evaluates against its own plan and other commitments
  Supplier team  -> budgets time, communicates an expected delivery window
  Both teams     -> agree on the shape of the interface (fields, semantics)
  Customer team  -> writes acceptance tests encoding that agreed shape
  Supplier team  -> integrates those tests into its own CI pipeline

Phase 2, steady state, repeated on every relevant upstream change
  Supplier team  -> proposes or begins a change to the upstream model
  CI pipeline    -> runs the customer-owned acceptance tests automatically
  IF tests pass  -> Supplier team ships the change, Customer team unaffected
  IF tests fail  -> Supplier team is alerted before shipping, not after
  Supplier team  -> either adjusts the change or reopens negotiation with
                    Customer team before proceeding
  Customer team  -> is never surprised by a breaking change in production,
                    because the failure surfaces upstream, in CI, first
```

The critical dynamic to observe is where a breaking-change failure surfaces.
In an unmanaged upstream-downstream relationship with no Customer-Supplier
agreement, a breaking change surfaces downstream, in the customer team's
production system, often discovered by an end user rather than by either
engineering team. In a working Customer-Supplier relationship, the same
class of breaking change surfaces upstream, inside the supplier team's own
build, before it ships, because the acceptance tests the customer team wrote
run as part of the supplier team's own pipeline. That relocation of where
the failure is detected, from downstream production to upstream CI, is the
single most concrete, observable proof that a Customer-Supplier relationship
is functioning as designed rather than existing only as a label on a
diagram.

## 8. Implementation variants

The negotiation and planning half of this pattern is organizational and has
no single code shape, but the acceptance-test half is a concrete, well-
established engineering technique with several common variants.

Consumer-driven contract testing is the dominant modern implementation of
the acceptance-tests participant. The downstream, customer team writes a
contract, in a tool such as Pact, https://docs.pact.io, expressing the exact
interactions it depends on, request shapes, expected response shapes, status
codes, and this contract is published to a broker the upstream, supplier
team's CI pipeline reads and verifies against on every build. This is a
direct, machine-checked implementation of Evans's instruction to "negotiate
and budget tasks for downstream requirements," made continuously enforced
rather than a one-time conversation.

Shared, versioned schema files, an OpenAPI document, a Protobuf or Avro
schema, or a GraphQL schema, checked into a repository both teams can see
and, in the more disciplined variant, both teams can propose changes to via
pull request, function as a lighter-weight negotiated interface where full
consumer-driven contract tooling is more process than the relationship
warrants. The schema itself becomes the artifact of negotiation, and schema-
diff tooling that flags breaking changes in CI serves the same role
consumer-driven contracts serve in the heavier variant.

Domain event contracts, in systems that integrate primarily through
asynchronous messaging rather than synchronous APIs, extend the same idea to
event schemas, the downstream team negotiates and pins the shape of the
events it consumes from an upstream event stream, and schema-registry
tooling, common in Kafka-based architectures, such as Confluent Schema
Registry's compatibility checking, enforces that the upstream team cannot
publish an incompatible event schema without the change being caught before
deployment, https://docs.confluent.io/platform/current/schema-registry/
fundamentals/schema-evolution.html, verified 2026-08-02.

DSL-based context mapping tooling exists specifically to make the
relationship type itself an explicit, checkable artifact rather than tribal
knowledge. The open source Context Mapper project provides a textual domain-
specific language in which a team writes, for example,
`CustomerSelfServiceContext [D,C]<-[U,S] CustomerManagementContext`, marking
one context as downstream-customer and the other as upstream-supplier
directly in a file that can be reviewed, versioned, and used to generate
diagrams, https://contextmapper.org/docs/customer-supplier/, verified
2026-08-02. Context Mapper's own tooling additionally enforces the pattern's
incompatibility rule discussed under dimension 13, refusing to let a context
be simultaneously marked Conformist and Customer-Supplier toward the same
upstream partner, which is a rare case of a strategic DDD pattern's
constraints being mechanically checkable rather than purely a matter of
team discipline.

Organizational, non-tooled variants remain common and legitimate, a
recurring cross-team planning meeting with a standing agenda item for
downstream requests, a shared product backlog tool with a labelled lane for
requests from a specific downstream team, or a lightweight internal service-
level agreement document restating the commitment in writing. None of these
require special software, and a Customer-Supplier relationship implemented
purely through disciplined process, with no automated contract tests at
all, is a legitimate, if riskier, instance of the pattern, riskier because
the commitment then depends entirely on human follow-through rather than
being caught mechanically when it lapses.

## 9. Known production uses

Vaughn Vernon's "Implementing Domain-Driven Design" (Addison-Wesley, 2013),
chapter 3, works through a full Context Map for the book's running example,
a fictional SaaS product-management platform named SaaSOvation, and
explicitly labels the relationship between the Agile Project Management
context, downstream, and the Identity and Access Management context,
upstream, as Customer-Supplier, describing the negotiation the Agile Project
Management team undertakes to have its authentication and permission needs
addressed by the Identity and Access team's planning. This worked example is
the most widely cited concrete illustration of the Customer-Supplier
relationship specifically, as distinct from Context Map in general, in the
DDD practitioner literature, and it is reused for that reason across
numerous derivative training resources and conference talks in the DDD
community.

Pact, the consumer-driven contract testing tool discussed under dimension
8, documents its own adoption by named organizations including Atlassian
and DIUS in its public case studies, and describes its core mechanism, a
consumer team publishing an executable contract that a provider team's CI
pipeline verifies against automatically, as a direct technical
implementation of exactly the negotiated, continuously enforced interface
Evans describes for Customer-Supplier, https://docs.pact.io/faq, verified
2026-08-02, which states the tool's purpose is "that a consumer and a
provider can communicate," confirmed by tests each side can run
independently against a shared, agreed contract.

The Context Mapper open source project, maintained by Stefan Kapferer and
the Software Engineering research group at the University of Applied
Sciences of the Grisons in Chur, Switzerland, implements Customer-Supplier
as one of eight formally defined relationship types in its published
context-mapping DSL, with its own compiler-level validation rules,
including the rule that a relationship cannot be simultaneously typed
Conformist and Customer-Supplier, documented at
https://contextmapper.org/docs/customer-supplier/, verified 2026-08-02, and
the project's academic grounding is published in Kapferer and Zimmermann,
"Domain-specific Language and Tools for Strategic Domain Driven Design,
Context Mapping and Bounded Context Modelling," Proceedings of the 15th
International Conference on Software Technologies, 2020, which formalizes
the Context Map relationship vocabulary, including Customer-Supplier,
as a checkable modelling language rather than only a diagramming
convention.

Matthew Skelton and Manuel Pais's "Team Topologies" (IT Revolution Press,
2019) documents the general organizational pattern of one team's plan
being shaped by another team's downstream needs as a recurring, named team
interaction mode, and directly contrasts the collaborative negotiation
this requires against the lighter-weight X-as-a-Service mode the same book
recommends once a platform serves enough downstream teams that individual
negotiation no longer scales, https://martinfowler.com/bliki/
TeamTopologies.html, verified 2026-08-02, which is independent
corroboration, from the organizational-design literature rather than the
DDD literature, of the same forces Evans identifies, that a negotiated,
one-to-few relationship like Customer-Supplier is a deliberate choice
suited to a small number of consumers, and stops fitting once the number
of consumers grows large enough that a self-service interface, DDD's Open
Host Service, becomes the better trade.

## 10. Consequences

Positive. The downstream team gains a real, structural voice in the
upstream team's planning, converting an implicit hope that its needs will
eventually be addressed into an explicit, budgeted commitment, which
reduces the coordination risk and schedule uncertainty the downstream team
otherwise carries silently. Where the relationship is backed by automated
acceptance or contract tests, a breaking change is caught inside the
upstream team's own CI pipeline before it ships, relocating the point of
failure detection from the downstream team's production system, where it is
expensive and often customer-visible, to the upstream team's build, where
it is cheap and private. The relationship also produces a documented,
shared understanding of what the interface actually promises, which reduces
the ambiguity that otherwise surrounds an informally integrated API and
gives both teams a concrete artifact, the negotiated contract, to point to
during a disagreement rather than relying on memory or a chat-history
search.

Negative. The upstream, supplier team accepts a genuine, ongoing constraint
on its ability to act alone, its planning process must now make room for a
specific downstream team's priorities, which is a real cost against
unilateral speed, and Evans's own instruction is explicit that this cost is
to be budgeted, not absorbed for free. The relationship does not scale
linearly, each additional downstream team the upstream context serves under
a Customer-Supplier arrangement multiplies the negotiation and testing
overhead, and beyond a small number of consumers the pattern's own
scalability limit is reached, at which point the honest move is to
transition toward Open Host Service rather than continuing to add bespoke
Customer-Supplier relationships one at a time, discussed further under
dimension 14. The pattern also depends entirely on organizational will,
labelling a relationship Customer-Supplier on a diagram costs nothing and
guarantees nothing, and a relationship that is named Customer-Supplier but
never actually negotiated or tested is worse than one honestly labelled
Conformist, because the false label hides the real power dynamic from
anyone reading the map who would otherwise plan around it correctly.

## 11. Failure modes and misuse

Symptom, the downstream team's requests sit in the upstream team's backlog
indefinitely with no committed date and no visibility into prioritization.
Cause, the relationship was drawn as Customer-Supplier on a diagram during
an initial architecture exercise, but no actual planning process was ever
established to carry it into the teams' day-to-day work, so the label
exists only on paper. Fix, either establish a real, recurring mechanism,
a standing agenda item in the upstream team's planning meeting, a
downstream-labelled lane in the shared backlog with a service-level target,
or relabel the relationship honestly as Conformist so the downstream team
stops planning around a commitment that does not exist and instead builds
its own defensive layer.

Symptom, the upstream team ships a change that breaks the downstream
team's integration, and the downstream team discovers this in its own
production environment rather than being warned in advance. Cause, no
automated acceptance or contract tests exist, so the negotiated interface
lives only in conversation and documentation, which the upstream team can
drift away from without any mechanical signal. Fix, introduce consumer-
driven contract tests or, at minimum, a versioned, checked schema that the
upstream team's CI validates against on every change, per dimension 8,
so the failure surfaces upstream before release rather than downstream
after it.

Symptom, the upstream team's velocity visibly degrades and its own plan
items are repeatedly displaced by an accumulating queue of individual
requests from several different downstream teams, each negotiated
separately. Cause, the number of Customer-Supplier relationships the
upstream context is party to has grown past what one-to-one negotiation can
sustain, often somewhere beyond ten to twenty active downstream consumers,
and the pattern is being asked to do the job Open Host Service is designed
for. Fix, consolidate the individually negotiated interfaces into one
stable, versioned, self-service Published Language, communicate a
deprecation path for the bespoke arrangements, and reserve remaining
Customer-Supplier relationships for the small number of downstream
consumers whose needs genuinely cannot be served by the shared, generic
interface.

Symptom, the downstream team treats the negotiated interface as though it
were a Shared Kernel, directly depending on internal implementation details
of the upstream context rather than only the agreed contract surface, so
that even changes the upstream team considers purely internal break the
downstream team. Cause, the boundary between "the negotiated contract" and
"the upstream context's internal model" was never made explicit, so the
downstream team, often for expediency, reaches past the intended interface.
Fix, make the contract surface a distinct, deliberately narrow artifact,
a published schema, a versioned API, an explicit event contract, and treat
anything the downstream team consumes outside that surface as a bug in the
boundary discipline, not as an acceptable extension of the relationship.

Symptom, the two teams disagree, sometimes publicly and unproductively,
about whether a given change was a breaking change or not, with each side
citing a different, undocumented understanding of what was promised.
Cause, the negotiation happened verbally or in an ephemeral chat thread,
with no durable, agreed artifact either side can point back to. Fix, every
negotiation that changes the contract's shape produces a durable artifact,
an updated schema file, an updated contract test, a merged pull request to
a shared specification, so that "what was promised" is a checkable fact
rather than a matter of competing recollections.

## 12. Trade-off matrix

| Force | Customer-Supplier | Conformist | Open Host Service | Shared Kernel |
|---|---|---|---|---|
| Downstream influence on upstream plan | Real, negotiated, budgeted | None, downstream absorbs upstream's model as-is | Indirect, via a public release plan or RFC process, not individual negotiation | Full, both teams jointly own the shared model |
| Coordination cost | Moderate, ongoing, per downstream team | Low for the upstream team, all cost falls on downstream | Low per additional consumer once published, higher one-time cost to design | High, continuous joint change coordination |
| Scales to many consumers | Poorly, cost multiplies per relationship | Well for upstream, poorly for each downstream team | Well, one interface serves all consumers | Poorly, coupling multiplies with team count |
| Protects downstream from upstream churn | Partially, via negotiated stability and tests | Not at all, downstream absorbs every upstream change | Well, if the published interface is versioned and stable | Not applicable, there is no boundary to protect across |
| Requires organizational standing | Yes, downstream needs real negotiating power | No, exactly the pattern for when that power is absent | No, the interface is offered to anyone | Yes, requires shared management or a trusted peer relationship |
| Typical automation | Consumer-driven contract tests, versioned schemas | Downstream-owned adapter or translation code | Public API versioning and deprecation policy | Shared codebase, shared CI, shared release process |

## 13. Related and incompatible patterns

Context Map is the parent artifact. Customer-Supplier is one of the several
named edge types a Context Map can carry between two Bounded Contexts, and
this entry deliberately does not restate the full Context Map vocabulary,
Partnership, Shared Kernel, Conformist, Anticorruption Layer, Open Host
Service, Published Language, Separate Ways, which is covered in the
context-map entry in this repository.

Conformist is Customer-Supplier's direct opposite along the single
dimension both patterns share, downstream influence over upstream planning.
The two are mutually exclusive for the same pair of contexts at the same
time, a relationship either has negotiated downstream input, Customer-
Supplier, or it does not, Conformist, and naming both simultaneously is a
category error the Context Mapper tooling discussed under dimension 8
enforces mechanically by refusing to compile such a model. In practice a
relationship can transition from Conformist to Customer-Supplier, and back,
as organizational circumstances change, discussed under dimension 14.

Open Host Service, often paired with Published Language, is the pattern
Customer-Supplier tends to evolve into once the upstream context serves
enough downstream consumers that individually negotiated relationships stop
scaling, per dimension 11. The two patterns are not incompatible, an
upstream context can offer a general Open Host Service to most consumers
while maintaining a small number of individually negotiated Customer-
Supplier relationships with a handful of especially important or unusual
downstream teams, but they solve the same underlying force, downstream
influence over an upstream interface, at different points on the scale-of-
consumers axis.

Anticorruption Layer composes with, rather than substitutes for,
Customer-Supplier. A downstream team can simultaneously negotiate for
improvements to an upstream interface, the Customer-Supplier relationship,
while also maintaining a translation layer that protects its own model
from whatever the upstream context currently looks like, the
Anticorruption Layer pattern, as insurance against negotiation failing or
taking longer than expected. The two patterns address different
questions, Customer-Supplier asks whether the downstream team has
influence over what the upstream context becomes, Anticorruption Layer
asks how the downstream team protects itself regardless of the answer to
that question.

Shared Kernel is a largely incompatible alternative strategy for the same
underlying situation, two teams whose domains overlap enough that keeping
them fully separate carries real translation cost. Where Customer-Supplier
keeps the two models formally separate and manages the seam through
negotiation, Shared Kernel dissolves part of the seam by having both teams
jointly own a shared piece of the model. A pair of teams generally choose
one strategy or the other for a given overlapping concern, not both at
once, though it is possible for two teams to run a Shared Kernel for one
part of their domain and a Customer-Supplier relationship for an adjacent,
more clearly separable part.

Ubiquitous Language interacts with Customer-Supplier at the level of the
negotiated interface itself. Because the two Bounded Contexts retain
separate models under Customer-Supplier, the negotiated contract often
requires an explicit translation between the upstream context's Ubiquitous
Language and the downstream context's Ubiquitous Language, which is part of
what the negotiation in dimension 7 is actually establishing, agreement on
what a given field or concept in the contract means in each side's own
vocabulary, not merely its wire format.

## 14. Refactoring path in and out

Introducing Customer-Supplier into an existing, unmanaged upstream-
downstream dependency proceeds in stages, each of which can be verified
independently before moving to the next. First, both teams name the
relationship explicitly, on a Context Map, in a shared document, or in a
Context Mapper DSL file, stating plainly which side is upstream and which
is downstream, which surfaces any disagreement about the direction of the
dependency before any further work happens. Second, the downstream team
enumerates its actual, current dependencies on the upstream context's
model, which fields, which endpoints, which events, producing a concrete
list rather than a vague sense of "we use their API." Third, that list
becomes the starting point of a negotiated contract, a schema file, a set of consumer-
driven contract test cases, or at minimum a written document both teams
sign off on, and this is the step where the relationship becomes checkable
rather than only agreed in principle. Fourth, the upstream team integrates
the downstream team's acceptance or contract tests into its own CI
pipeline, so that a future change to the upstream model automatically
surfaces any conflict with the negotiated contract before the change ships,
completing the loop described under dimension 7. Fifth, the two teams
establish the ongoing planning mechanism, whether a recurring meeting or a
backlog lane, that carries the relationship forward as a living practice
rather than a one-time setup exercise.

Removing or downgrading a Customer-Supplier relationship happens for one of
two honest reasons, and the correct target pattern differs by reason. If
the relationship has stopped being real, the negotiated commitments are
consistently not honored and the downstream team in practice has no
influence despite the label, the correct move is to relabel the
relationship Conformist, remove any contract tests the upstream team is
not actually respecting, since maintaining tests nobody acts on is worse
than removing them and being honest about the power dynamic, and have the
downstream team build its own Anticorruption Layer to protect itself going
forward. If instead the relationship has succeeded so well that it no
longer scales, the upstream context has accumulated enough Customer-
Supplier partners that individual negotiation is consuming an
unsustainable share of the upstream team's planning capacity, the correct
move is the upgrade path described under dimension 11, consolidate the
individually negotiated contracts into a single, versioned, self-service
Open Host Service with a Published Language, communicate a deprecation
timeline for the bespoke, individually negotiated arrangements, and reserve
any remaining one-to-one Customer-Supplier relationships for the small
number of downstream teams whose needs the shared interface genuinely
cannot serve. Both paths are refactorings of an organizational relationship
as much as a technical one, and both should be reflected on the Context
Map itself so the map stays an accurate record of the current reality
rather than a historical artifact of an earlier arrangement.

## 15. Testing and verification

Consumer-driven contract testing is the primary verification technique this
pattern relies on, and it is worth stating precisely what it tests and what
it does not. A contract test, written from the downstream, customer side,
encodes the specific requests and expected responses the downstream context
actually depends on, and is run in two places, against a mock of the
upstream service on the downstream team's own build, to catch a regression
in how the downstream code consumes the contract, and against the real
upstream implementation on the upstream team's build, to catch a regression
in how the upstream service fulfils the contract. Neither run alone is
sufficient, the downstream-side run without the upstream-side run leaves
the upstream team free to break the contract silently, and the upstream-
side run without the downstream-side run leaves the downstream team unable
to catch its own misuse of the contract. Pact's broker-based workflow,
where the downstream team publishes its contract and the upstream team's
CI verifies against the latest published version automatically, is the
most widely adopted implementation of running both sides continuously,
https://docs.pact.io, verified 2026-08-02.

What becomes easier to test as a direct consequence of a working Customer-
Supplier relationship is integration correctness without requiring a full,
live, cross-team integration environment. Because the contract is an
explicit, checkable artifact, each team can verify its own side against
that contract in isolation, the downstream team against a mock built from
the contract, the upstream team against the contract's assertions run in
its own pipeline, without either team needing to stand up the other team's
full system to catch most integration defects.

What becomes harder, or at least what remains genuinely hard even with a
working contract, is catching defects the contract does not encode,
semantic drift where both sides technically satisfy the schema but
disagree about what a field means in practice, timing and ordering issues
in asynchronous event-based integrations that a request-response contract
test does not naturally capture, and any defect that only manifests under
production load or data volume neither team's test environment
approximates. A Customer-Supplier relationship's testing strategy reduces
integration risk, it does not eliminate the need for some periodic, real
full, real-run verification, particularly for asynchronous or high-volume
integrations, and teams that treat contract tests as a full substitute for
any full request-response check are trading one blind spot for a smaller but real
remaining one.

## 16. Observability signals

A healthy Customer-Supplier relationship is visible in engineering process
metrics more than in runtime telemetry, since the pattern's subject is a
team relationship rather than a running system, though several concrete,
observable signals do apply. The contract-verification pipeline itself is
the clearest technical signal, an upstream team's CI dashboard showing
consumer contract verification as a regular, passing step is direct
evidence the negotiated relationship is mechanically enforced, and a
verification step that has been silently skipped, disabled, or is failing
and being ignored is a direct, checkable sign the relationship has decayed
into an unmanaged one regardless of what the Context Map still says.

Lead time from a downstream request to a scheduled, committed delivery is
the primary organizational metric. A working relationship shows a
reasonably short, predictable interval between a downstream team raising a
need and that need appearing with a committed date on the upstream team's
plan, and a relationship in name only shows requests accumulating in an
unprioritized backlog with no visible commitment at all, which is directly
observable in whatever planning tool the teams share.

Breaking-change detection point is the second key signal, and it was
introduced under dimension 7 as the pattern's central dynamic. Tracking
where breaking changes are actually caught, in the upstream team's CI
before release, versus in the downstream team's production environment
after release, and trending that ratio over time gives a direct, measurable
proxy for whether the contract-testing half of the relationship is
functioning. An organization moving toward more upstream-caught and fewer
downstream-caught breaking changes over successive quarters is observing
the pattern working as intended.

The number of active Customer-Supplier relationships a single upstream
context carries, tracked over time on the Context Map itself if the team
maintains one as a living document, is the signal that surfaces the scaling
failure mode described under dimension 11 before it becomes acute, a
steadily growing count is the leading indicator that the pattern is
approaching the point where transitioning some or all of those
relationships to Open Host Service should be planned rather than reacted
to under pressure.

## 17. Security and privacy implications

Judgement. This dimension is mostly analytical inference from the pattern's
structure rather than sourced from a specific security incident report, and
is stated as such.

The pattern's primary security-relevant surface is the negotiated
interface itself, and specifically what data crosses it. Because a
Customer-Supplier relationship formalizes and often widens what the
downstream team is entitled to request from the upstream context, the
negotiation process is a natural point at which the field or event scope
exposed across the boundary should be reviewed for data minimization,
whether a newly requested field genuinely needs to cross the boundary or
whether the downstream team's actual need can be met with a narrower,
derived value that avoids exposing raw upstream data the downstream context
does not need to hold. This is not a concern unique to Customer-Supplier,
any cross-context data exchange raises the same question, but the explicit,
negotiated nature of this pattern makes it a natural, low-friction point to
apply that review deliberately, since a request is already being discussed
and documented rather than happening ad hoc through direct, unreviewed
access.

Contract test fixtures are a secondary, concrete risk worth naming plainly.
Because consumer-driven contract tests, per dimension 15, are often written
against realistic example data to make the contract's shape concrete, teams
sometimes populate those fixtures with data copied or lightly modified from
a real production record, which can leak personal or sensitive data into a
test suite, a broker service, or a version-controlled schema repository
that has weaker access controls or a longer, less audited retention policy
than the production system the data originated in. The correct discipline
is synthetic fixture data generated to satisfy the contract's shape without
resembling any real record, and this is a general software-testing
discipline rather than something specific to Customer-Supplier, but the
pattern's reliance on shared, often externally hosted contract-broker
tooling makes it worth naming explicitly here.

The negotiation and planning process itself carries a milder governance
implication, a documented, negotiated commitment between two teams is, in
effect, an internal data-sharing agreement, and in organizations subject to
data-protection regulation covering internal data flows between systems
handling personal data, that negotiation is a reasonable point to also
confirm the data-sharing has the appropriate internal authorization,
though the pattern itself provides no mechanism for that authorization and
simply creates a natural checkpoint at which the question can, and
arguably should, be asked.

## 18. References

1. Eric Evans, "Domain-Driven Design. Tackling Complexity in the Heart of
   Software," Addison-Wesley, 2003, Part IV, chapter 14, "Maintaining Model
   Integrity."
2. Vaughn Vernon, "Implementing Domain-Driven Design," Addison-Wesley, 2013,
   chapter 3, "Context Maps."
3. ddd-crew, "Context Mapping," GitHub, quoting the DDD Reference definition
   of Customer/Supplier Development Teams word for word,
   https://github.com/ddd-crew/context-mapping/blob/master/README.md,
   verified 2026-08-02.
4. Context Mapper project, "Customer/Supplier," documentation,
   https://contextmapper.org/docs/customer-supplier/, verified 2026-08-02.
5. Context Mapper project, "Conformist," documentation,
   https://contextmapper.org/docs/conformist/, verified 2026-08-02.
6. Stefan Kapferer and Olaf Zimmermann, "Domain-specific Language and Tools
   for Strategic Domain Driven Design, Context Mapping and Bounded Context
   Modelling," Proceedings of the 15th International Conference on Software
   Technologies, 2020.
7. Matthew Skelton and Manuel Pais, "Team Topologies. Organizing Business
   and Technology Teams for Fast Flow," IT Revolution Press, 2019.
8. Martin Fowler, "Team Topologies," bliki,
   https://martinfowler.com/bliki/TeamTopologies.html, verified 2026-08-02.
9. Martin Fowler, "BoundedContext," bliki, 15 January 2014,
   https://martinfowler.com/bliki/BoundedContext.html, verified 2026-08-02.
10. Pact documentation, "Frequently Asked Questions,"
    https://docs.pact.io/faq, verified 2026-08-02.
11. Confluent, "Schema Evolution and Compatibility," Confluent Platform
    documentation,
    https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html,
    verified 2026-08-02.

## Code examples

The examples below implement the acceptance-test half of a Customer-
Supplier relationship, a minimal consumer-driven contract check, since the
negotiation-and-planning half of the pattern is organizational and has no
genuine code form. Each example models a downstream Reporting context
consuming an upstream Billing context's invoice summary, and asserts the
upstream side satisfies the exact contract shape the downstream side
depends on. All six were compiled successfully.

### TypeScript

```typescript
interface InvoiceSummaryContract {
  invoiceId: string;
  totalCents: number;
  taxJurisdiction: string;
}

function upstreamBillingContext(invoiceId: string): InvoiceSummaryContract {
  return { invoiceId, totalCents: 12599, taxJurisdiction: "DE-BY" };
}

function verifyCustomerSupplierContract(
  produce: (id: string) => InvoiceSummaryContract
): void {
  const result = produce("inv-001");
  const requiredFields: (keyof InvoiceSummaryContract)[] = [
    "invoiceId",
    "totalCents",
    "taxJurisdiction",
  ];
  for (const field of requiredFields) {
    if (result[field] === undefined) {
      throw new Error(
        "negotiated contract violated, missing field: " + field
      );
    }
  }
  if (typeof result.totalCents !== "number" || result.totalCents < 0) {
    throw new Error("negotiated contract violated, totalCents must be a non-negative number");
  }
  console.log("contract satisfied:", JSON.stringify(result));
}

verifyCustomerSupplierContract(upstreamBillingContext);
```

Run with `npx tsc --strict customer-supplier.ts && node customer-supplier.js`.

### Python

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class InvoiceSummaryContract:
    invoice_id: str
    total_cents: int
    tax_jurisdiction: str


def upstream_billing_context(invoice_id: str) -> InvoiceSummaryContract:
    return InvoiceSummaryContract(
        invoice_id=invoice_id, total_cents=12599, tax_jurisdiction="DE-BY"
    )


def verify_customer_supplier_contract(produce) -> None:
    result = produce("inv-001")
    if not isinstance(result.total_cents, int) or result.total_cents < 0:
        raise AssertionError(
            "negotiated contract violated, total_cents must be a non-negative int"
        )
    if not result.tax_jurisdiction:
        raise AssertionError(
            "negotiated contract violated, tax_jurisdiction must be present"
        )
    print(f"contract satisfied: {result}")


if __name__ == "__main__":
    verify_customer_supplier_contract(upstream_billing_context)
```

Run with `python3 customer_supplier.py`.

### Go

```go
package main

import (
	"errors"
	"fmt"
)

type InvoiceSummaryContract struct {
	InvoiceID       string
	TotalCents      int
	TaxJurisdiction string
}

func upstreamBillingContext(invoiceID string) InvoiceSummaryContract {
	return InvoiceSummaryContract{
		InvoiceID:       invoiceID,
		TotalCents:      12599,
		TaxJurisdiction: "DE-BY",
	}
}

func verifyCustomerSupplierContract(
	produce func(string) InvoiceSummaryContract,
) error {
	result := produce("inv-001")
	if result.TotalCents < 0 {
		return errors.New("negotiated contract violated, TotalCents must be non-negative")
	}
	if result.TaxJurisdiction == "" {
		return errors.New("negotiated contract violated, TaxJurisdiction must be present")
	}
	fmt.Printf("contract satisfied: %+v\n", result)
	return nil
}

func main() {
	if err := verifyCustomerSupplierContract(upstreamBillingContext); err != nil {
		panic(err)
	}
}
```

Run with `go run customer_supplier.go`.

### Swift

```swift
struct InvoiceSummaryContract {
    let invoiceId: String
    let totalCents: Int
    let taxJurisdiction: String
}

func upstreamBillingContext(invoiceId: String) -> InvoiceSummaryContract {
    InvoiceSummaryContract(invoiceId: invoiceId, totalCents: 12599, taxJurisdiction: "DE-BY")
}

enum ContractError: Error {
    case violated(String)
}

func verifyCustomerSupplierContract(
    produce: (String) -> InvoiceSummaryContract
) throws {
    let result = produce("inv-001")
    if result.totalCents < 0 {
        throw ContractError.violated("totalCents must be non-negative")
    }
    if result.taxJurisdiction.isEmpty {
        throw ContractError.violated("taxJurisdiction must be present")
    }
    print("contract satisfied: \(result)")
}

try verifyCustomerSupplierContract(produce: upstreamBillingContext)
```

Run with `swiftc customer_supplier.swift -o customer_supplier && ./customer_supplier`.

### Java

```java
public final class CustomerSupplier {
    record InvoiceSummaryContract(String invoiceId, long totalCents, String taxJurisdiction) {}

    static InvoiceSummaryContract upstreamBillingContext(String invoiceId) {
        return new InvoiceSummaryContract(invoiceId, 12599L, "DE-BY");
    }

    static void verifyCustomerSupplierContract(
            java.util.function.Function<String, InvoiceSummaryContract> produce) {
        InvoiceSummaryContract result = produce.apply("inv-001");
        if (result.totalCents() < 0) {
            throw new IllegalStateException("negotiated contract violated, totalCents must be non-negative");
        }
        if (result.taxJurisdiction() == null || result.taxJurisdiction().isEmpty()) {
            throw new IllegalStateException("negotiated contract violated, taxJurisdiction must be present");
        }
        System.out.println("contract satisfied: " + result);
    }

    public static void main(String[] args) {
        verifyCustomerSupplierContract(CustomerSupplier::upstreamBillingContext);
    }
}
```

### Rust

```rust
#[derive(Debug)]
struct InvoiceSummaryContract {
    invoice_id: String,
    total_cents: i64,
    tax_jurisdiction: String,
}

fn upstream_billing_context(invoice_id: &str) -> InvoiceSummaryContract {
    InvoiceSummaryContract {
        invoice_id: invoice_id.to_string(),
        total_cents: 12599,
        tax_jurisdiction: "DE-BY".to_string(),
    }
}

fn verify_customer_supplier_contract<F>(produce: F) -> Result<(), String>
where
    F: Fn(&str) -> InvoiceSummaryContract,
{
    let result = produce("inv-001");
    if result.total_cents < 0 {
        return Err("negotiated contract violated, total_cents must be non-negative".to_string());
    }
    if result.tax_jurisdiction.is_empty() {
        return Err("negotiated contract violated, tax_jurisdiction must be present".to_string());
    }
    println!("contract satisfied: {:?}", result);
    Ok(())
}

fn main() {
    verify_customer_supplier_contract(upstream_billing_context).unwrap();
}
```

C# and Kotlin toolchains were not installed in this environment and are
omitted rather than hand-typed and left unconfirmed, per the repository's
toolchain-availability note.
