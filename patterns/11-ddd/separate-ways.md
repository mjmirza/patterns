---
name: Separate Ways
slug: separate-ways
family: 11-ddd
category: Strategic Design
aliases: [SW, No Integration, Cut the Strings]
first_described: "Evans 2003"
maturity: canonical
related: [bounded-context, context-map, shared-kernel, conformist, anticorruption-layer, customer-supplier, open-host-service, published-language]
incompatible_with: [shared-kernel, customer-supplier]
verified: 2026-08-02
---

# Separate Ways

## 1. Name, aliases, and lineage

The canonical name is Separate Ways. Eric Evans introduced it in *Domain-Driven
Design. Tackling Complexity in the Heart of Software*, Addison-Wesley, 2003,
Part IV, "Strategic Design," chapter 14, "Maintaining Model Integrity," in the
section titled "Separate Ways." Evans states the pattern in one sentence, in
his usual imperative form. "Declare a Bounded Context to have no connection to
the others at all, allowing developers to find simple specialized solutions
within this small scope" (Eric Evans, *Domain-Driven Design*, Addison-Wesley,
2003, ch. 14, section "Separate Ways," final manuscript pagination p. 260,
confirmed by direct extraction of the publicly hosted final-manuscript PDF at
[fabiofumarola.github.io/nosql/readingMaterial/Evans03.pdf](https://fabiofumarola.github.io/nosql/readingMaterial/Evans03.pdf),
verified 2026-08-02). This is one of six patterns Evans groups under
"Relationships Between Bounded Contexts," alongside Shared Kernel,
Customer-Supplier Development Teams, Conformist, Anticorruption Layer, and
Open Host Service, and it is the only one of the six whose entire content is
the decision to build no relationship at all.

Practitioner and training material almost never invents a competing name for
this pattern, which is itself a small signal of how settled the term is. The
open source ddd-crew context-mapping cheat sheet lists Separate Ways as one
of nine named Context Map patterns, quoting the same core sentence as Evans's
original definition
([ddd-crew/context-mapping on GitHub](https://github.com/ddd-crew/context-mapping),
verified 2026-08-02, whose fetched content reproduces "Declare a bounded
context to have no connection to the others at all, allowing developers to
find simple, specialized solutions within this small scope" as the pattern's
stated purpose). DevIQ's reference glossary, maintained separately from the
ddd-crew project, gives the identical wording and lists the same nine
patterns in the same grouping
([DevIQ, "Context Mapping"](https://deviq.com/domain-driven-design/context-mapping/),
verified 2026-08-02). Two independently maintained references converging on
the same sentence for the same pattern name is strong evidence that the term
has not drifted since 2003.

Vaughn Vernon's *Implementing Domain-Driven Design*, Addison-Wesley, 2013,
chapter 3, "Context Maps," treats Separate Ways as one of the standard
relationship types a team draws on its Context Map alongside Partnership,
Shared Kernel, Customer-Supplier, Conformist, Anticorruption Layer, Open
Host Service, and Published Language, using the same fictional SaaSOvation
product-management platform that anchors the book's Customer-Supplier and
Open Host Service worked examples to illustrate how a team decides a
relationship is not worth the cost of maintaining
([Pearson, "Implementing Domain-Driven Design," table of contents and chapter
3 summary](https://www.pearson.com/en-us/subject-catalog/p/implementing-domain-driven-design/P200000009616/9780133039887),
verified 2026-08-02, confirming chapter 3 covers the full set of Context Map
relationship patterns Evans defined). Vernon does not add a competing name.
He works within Evans's vocabulary, which is the normal pattern for how the
DDD community treats this specific term.

One informal alias worth naming honestly, because it is engineering judgement
rather than a citable term, is "cut the strings," a phrase Evans himself uses
in the Conformist section of the same chapter when describing a downstream
team abandoning a dependency on an unhelpful upstream. "If the downstream
team decides to cut the strings, they are going their Separate Ways" (Eric
Evans, *Domain-Driven Design*, Addison-Wesley, 2003, ch. 14, section
"Conformist," final manuscript p. 254). This entry uses that phrase as a
mnemonic for the abandonment path into the pattern, not as a second
canonical name.

## 2. Problem and context

A team splits a system into more than one Bounded Context for good reasons,
because two departments' vocabularies genuinely diverge, because two teams
cannot coordinate closely enough to keep one model unified, or because one
context depends on an external or legacy system it does not control. Having
drawn the boundary, the team then faces a second, separate question that
Evans treats as equally important as the boundary itself. Given two Bounded
Contexts that have been identified as distinct, what, if anything, should
connect them.

The instinctive answer is to integrate. A use case that touches both
contexts feels, on the surface, like proof that the two contexts need a
shared model, a translation layer, or at minimum an agreed interface. Evans
pushes back on that instinct directly. He writes that a team must "be
ruthless when it comes to defining requirements," because "if two sets of
functionality have no significant relationship, they can be completely cut
loose from each other," and because "integration is always expensive, and
sometimes the benefit is small" (Eric Evans, *Domain-Driven Design*,
Addison-Wesley, 2003, ch. 14, section "Separate Ways," final manuscript p.
260). He is explicit that appearing together in one use case is not, by
itself, sufficient grounds for integration. "Just because features are
related in a use case does not mean they must be integrated" (same source,
same page).

The context in which this pattern applies is a project that already has two
or more candidate Bounded Contexts, and a team facing the question of how
tightly to couple them. Evans frames the decision as a cost comparison rather
than a technical necessity. Every one of the other Context Map relationship
patterns, Shared Kernel, Customer-Supplier, Conformist, Anticorruption Layer,
Open Host Service, costs something ongoing, whether that is coordination
overhead, a translation layer to build and maintain, a constraint on one
team's design freedom, or a shared test suite that both teams must keep
green. Separate Ways is the one relationship pattern whose cost is paid
once, at the moment duplicate functionality is built, and never again as an
ongoing coordination tax. The pattern is reached for specifically when a
team has looked at that trade honestly and concluded the ongoing tax is not
worth what the integration would buy.

Evans illustrates the decision with a worked example he calls "An Insurance
Project Slims Down." An insurance claims project had set out to integrate
everything an adjuster or a customer service agent needed into one unified
system, spent a year in what Evans describes as "analysis paralysis"
combined with a large upfront infrastructure investment, and had nothing
shippable to show. A new project manager forced the team to list every
requirement, estimate its difficulty, and rank its importance, and, in
Evans's words, they "ruthlessly chopped the difficult and unimportant ones."
The team then noticed that adjusters needed access to existing databases
that none of the other proposed features actually depended on, so instead
of building integration for that access, they exported a key report to
static HTML on the intranet, wrote a standalone query tool with a
general-purpose package, and organized both behind links on a single
intranet page, with "no more integration than launching from the same
menu." Several capabilities shipped almost immediately. Evans is candid
about the project's ultimate fate. The team eventually slipped back into
its old habits and stalled again on the unified system, and, in his words,
"their only legacy turned out to be those small applications that had gone
their Separate Ways" (Eric Evans, *Domain-Driven Design*, Addison-Wesley,
2003, ch. 14, section "Separate Ways," final manuscript pp. 260 to 261).
This example is Evans's own worked illustration, presented anonymously in
the book rather than tied to a named company, and this entry states that
distinction plainly rather than presenting it as a named production case.

## 3. Forces

**Integration cost versus integration benefit.** Every integration path,
even the cheapest one, costs something to build and something ongoing to
maintain, whether that is a shared kernel's weekly merge discipline, a
customer-supplier team's joint planning meeting, or an anticorruption
layer's translation code that has to track two models as both evolve. The
benefit of integration is a single coherent workflow, less duplicated logic,
and one place to change a rule instead of several. Separate Ways is the
pattern that results when a team weighs these honestly and finds the cost
side heavier for a specific pair of contexts. This is the defining force,
and it is the one Evans names explicitly and repeatedly across the chapter.

**Specialization versus a general-purpose model.** A context free of
external constraints can pick the simplest possible model and the simplest
possible tool for its own narrow problem. A context that must integrate is
constrained to a model expressive enough to satisfy every partner it
integrates with, which is usually a more abstract, more general model than
any single partner needs on its own. Evans states this directly as a
justification for the pattern. The simple, specialized model "that can
satisfy a particular need must give way to the more abstract model that can
handle all situations" once integration is required (Eric Evans,
*Domain-Driven Design*, Addison-Wesley, 2003, ch. 14, section "Separate
Ways," final manuscript p. 260). Separate Ways trades a shared abstraction
for local simplicity.

**Team autonomy versus coordination overhead.** Two teams with no
integration point can plan, release, and change their own models on their
own schedule, with no cross-team meeting required to ship a change. Two
teams with any of the other relationship patterns must coordinate to some
degree, from a customer-supplier planning negotiation down to a shared
kernel's mandatory weekly merge. Separate Ways is the only pattern in the
family that removes this coordination cost entirely for the pair of
contexts it applies to, at the price of losing any structural mechanism for
keeping the two models consistent with each other.

**One-time duplication versus recurring translation cost.** Choosing
Separate Ways over a translation-based pattern such as Anticorruption Layer
trades a recurring cost, the ongoing maintenance of a translation layer
that must track both models, for a one-time cost, building and maintaining
two independent implementations of whatever functionality genuinely
overlaps. Evans is explicit that duplication is not treated as a defect
here. It is an accepted, deliberate cost. The insurance project example is
built entirely around this trade, choosing a handful of small, duplicated,
standalone tools over a single unified translation layer that the team had
already spent a year failing to build.

**Optionality versus foreclosure.** A model that has never integrated with
another model is, in principle, free to integrate later. In practice Evans
warns this freedom erodes over time. "Taking Separate Ways forecloses some
options. Although continuous refactoring can eventually undo any decision,
it is hard to merge models that have developed in complete isolation" (Eric
Evans, *Domain-Driven Design*, Addison-Wesley, 2003, ch. 14, section
"Separate Ways," final manuscript p. 261). The force here is genuinely
two-sided. Choosing Separate Ways now is cheap and reversible in theory, and
expensive to reverse in practice the longer the two models are left to
diverge independently.

## 4. Applicability and non-applicability

Reach for Separate Ways when the following hold, ideally together rather
than singly.

- A close look at the actual requirements, not the use-case diagram, shows
  that no logic, no object, and no shared data genuinely needs to cross the
  boundary between the two candidate contexts, even though a use case
  happens to touch both.
- The two teams' working styles, technical choices, or domain vocabularies
  clash badly enough that any shared artifact would become a constant
  source of friction, and the clash comes from something the organization
  cannot or does not want to change, such as a different regulatory regime,
  a different user community, or an acquired team with its own established
  practice.
- The scope under design is genuinely large or stalled, and cutting a
  feature loose into its own small, unintegrated tool is the fastest path
  to shipping something real, as in Evans's insurance project example.
- The integration, if built, would be one-off and would exist only to serve
  a single narrow interaction, so the cost of a translation layer would
  exceed the cost of a person manually switching between two separately
  launched tools.
- The relationship being replaced is a Conformist or a one-sided
  Customer-Supplier arrangement in which the upstream has no motivation to
  serve the downstream and the downstream has evaluated abandoning the
  dependency as more valuable than continuing to depend on it, described by
  Evans as "cutting the strings" (Eric Evans, *Domain-Driven Design*,
  Addison-Wesley, 2003, ch. 14, section "Conformist," final manuscript p.
  254).

### Non-applicability

Do NOT reach for Separate Ways in any of the following situations. This list
is the more valuable of the two, because Separate Ways is cheap to declare
and expensive to notice was wrong.

- Two contexts share a genuine, load-bearing concept, such as a single
  authoritative Customer record that must stay consistent for billing,
  fraud, and support to all agree on who the customer is. Evans's own
  three-path guidance for a downstream dependency the team cannot abandon
  places Separate Ways explicitly out of scope and routes the decision
  toward Conformist or Anticorruption Layer instead (Eric Evans,
  *Domain-Driven Design*, Addison-Wesley, 2003, ch. 14, section
  "Conformist," final manuscript pp. 254 to 255).
- The two contexts are choosing Separate Ways only to avoid a difficult
  conversation about ownership or a difficult integration project, rather
  than because a genuine cost and benefit analysis favors independence.
  Evans names this failure mode directly, warning that the pattern "can
  become an argument against change and a justification for any quirky
  parochial model" (Eric Evans, *Domain-Driven Design*, Addison-Wesley,
  2003, ch. 14, section "Catering to Special Needs With Distinct Models,"
  final manuscript p. 270).
- Regulatory, financial, or safety-critical data must be reconciled across
  the two systems, such as a ledger that has to balance across an order
  system and a billing system. Two independently evolving models of money
  will drift, and drift in money is rarely acceptable, however small the
  translation cost would have been.
- The two teams are, in practice, the same team wearing two hats, or one
  team owns both candidate contexts. Evans notes that one team can maintain
  more than one Bounded Context without difficulty, but the coordination
  cost that Separate Ways is meant to remove was never actually present,
  so the pattern earns the project nothing and only adds the cost of
  maintaining two divergent models by hand.
- A downstream team genuinely cannot function without an upstream
  capability and has no realistic path to replace it with its own
  implementation on any reasonable timeline. Choosing Separate Ways here is
  wishful thinking dressed as an architectural decision. It abandons a
  dependency the project still needs, which produces an outage of a
  feature rather than a clean architectural boundary.
- The system is small enough, and the team small enough, that a single
  unified Bounded Context under Continuous Integration is already working
  well. Evans is explicit that a single Bounded Context is the right
  default "for a team of fewer than ten people working on a set of highly
  interrelated functionality" (Eric Evans, *Domain-Driven Design*,
  Addison-Wesley, 2003, ch. 14, section "The System Under Design," final
  manuscript p. 269), and introducing Separate Ways here manufactures a
  boundary and a duplication cost that the project's actual size does not
  yet justify.

## 5. Structure

Separate Ways has an unusually small participant list, because its entire
content is the absence of a structural connection between two participants
that would otherwise be connected.

- **Bounded Context A and Bounded Context B.** Two contexts that have each
  been separately identified through the normal process of drawing Bounded
  Context boundaries, see the bounded-context entry in this repository.
  Each owns its own model, its own Ubiquitous Language, and, where
  applicable, its own data store, with neither one's model informing or
  constraining the other's design.
- **The Context Map.** The artifact, described fully in the context-map
  entry in this repository, on which the relationship between A and B is
  recorded. For every other relationship pattern, this is where the
  relationship type and its upstream and downstream roles, if any, are
  written. For Separate Ways, the Context Map records that A and B exist,
  and records, by the explicit absence of any drawn connection between
  them, that no relationship has been declared.
- **The optional deployment-level or presentation-level seam.** Evans is
  explicit that Separate Ways forbids sharing logic and forbids
  meaningful data translation, but it does not forbid a person moving
  between the two systems through ordinary means, such as two menu items
  in the same portal, two links on the same intranet page, or two tabs in
  the same browser. He writes that the pattern allows the "features" to
  "still be organized in middleware or the UI layer," but there will be
  "no sharing of logic, and an absolute minimum of data transfer through
  translation layers, preferably none" (Eric Evans, *Domain-Driven
  Design*, Addison-Wesley, 2003, ch. 14, section "Separate Ways," final
  manuscript p. 260).
- **The absent translator.** Every other pattern in the family, Shared
  Kernel, Customer-Supplier, Conformist, Anticorruption Layer, Open Host
  Service, and Published Language, has a translation artifact of some
  kind, a shared subset of code, a negotiated contract, an adapter, a
  published protocol. Separate Ways is defined by not having one. That
  absence is itself the participant a reader should notice, because it is
  the single structural fact that distinguishes this pattern from every
  neighbor in the family.

## 6. ASCII structure diagram

```
      Bounded Context A                    Bounded Context B
   (Orders and Fulfilment)                 (Support and Tickets)

  +-----------------------+           +-----------------------+
  |  OrderingCustomer     |           |  SupportCustomer       |
  |  - customerId         |           |  - accountId            |
  |  - shipTo             |           |  - tier                 |
  |  - openOrderCount     |           |  - openTicketCount      |
  +-----------------------+           +-----------------------+
  | own data store         |           | own data store          |
  | own release schedule   |           | own release schedule    |
  +-----------------------+           +-----------------------+

              ^                                    ^
              |  no shared model                    |
              |  no shared code                      |
              |  no ongoing translation layer         |
              |                                       |
              +-------------------X-------------------+
                    (no drawn edge on the
                     Context Map at all)

  Optional, allowed.  a portal page linking to both, with no
  logic or data crossing the link.

     +----------------------------------------------------+
     |  Intranet portal.  [ Orders ]     [ Support ]        |
     +----------------------------------------------------+
```

## 7. Dynamics

At runtime, Separate Ways has no cross-context sequence to draw, because
there is no message, call, or shared transaction that spans the two
contexts. The dynamics that matter for this pattern are organizational and
occur at design time and at release time rather than at request time.

```
Design-time decision sequence

  Team A                    Team B                Context Map owner
    |                          |                          |
    |-- proposes shared -----> |                          |
    |   Customer model         |                          |
    |                          |-- estimates translation ->|
    |                          |   or shared-kernel cost   |
    |                          |                          |
    |<----- both teams weigh cost of coordination -------->|
    |       against value of a shared model                |
    |                          |                          |
    |-- decides. no shared -->|                          |
    |   model is worth it      |                          |
    |                          |-- agrees ---------------->|
    |                          |                          |
    |                          |          record Separate Ways
    |                          |          on the Context Map
    |                          |          (no edge drawn)
    v                          v                          v
  builds own model,          builds own model,        no ongoing
  own release cadence        own release cadence       coordination step

Release-time behaviour, per deploy

  Team A ships a change ------> only Team A's tests run
  Team B ships a change ------> only Team B's tests run

  (contrast. a Shared Kernel deploy requires both teams'
   test suites to pass together, and a Customer-Supplier
   deploy requires the two teams to coordinate compatible
   versions before either releases)
```

Evans notes the release-time consequence directly when comparing the
deployment burden across the pattern family. "A Shared Kernel imposes a
much greater burden of coordination not just in development but also in
deployment. Separate Ways can make life much simpler" (Eric Evans,
*Domain-Driven Design*, Addison-Wesley, 2003, ch. 14, section "Deployment,"
final manuscript p. 271).

If the two contexts still need some functional integration despite having
declared Separate Ways for their models, Evans describes a narrower, later
runtime interaction. a translation layer built specifically for that one
remaining need, distinct from a full shared model, that both teams can
maintain jointly as a single point of continuous integration for that one
concern, or, where one side is external and unresponsive, an
Anticorruption Layer maintained unilaterally by the side that needs it
(Eric Evans, *Domain-Driven Design*, Addison-Wesley, 2003, ch. 14, section
"The System Under Design," final manuscript p. 270, and ch. 14, section
"Relationships With the External Systems," final manuscript p. 259). This
is discussed further under dimension 13.

## 8. Implementation variants

**Complete isolation, the canonical form.** Two Bounded Contexts share
nothing, not a library, not a database, not a message format. Integration,
if any, is limited to a shared navigation surface such as a portal page or
a mobile app's tab bar. This is the form Evans's own definition describes
and the form the insurance project example demonstrates.

**Isolation with a single narrow translator for one residual need.** The
models stay fully independent, but one specific interaction that genuinely
cannot be avoided is served by a small, explicitly scoped translation
layer, maintained by whichever team needs it, rather than by merging the
two models. Evans frames this as compatible with Separate Ways rather than
a contradiction of it. Two subsystems "based on different models" can
still be "connected with an Anticorruption Layer" even after a team has
"decided on Separate Ways" for the models overall, specifically when the
two contexts "still have some need of functional integration" (Eric Evans,
*Domain-Driven Design*, Addison-Wesley, 2003, ch. 14, section
"Anticorruption Layer," final manuscript p. 259). This is the variant that
most often gets missed by teams who wrongly treat Separate Ways as an
absolute ban on any interaction whatsoever.

**Separate Ways from an external or legacy system.** Evans treats
integration with a system outside the team's control as a distinct
decision from integration between two contexts the team both owns, and
lists Separate Ways as the first option to consider before Conformist or
Anticorruption Layer. "The first to consider is Separate Ways. Yes, you
wouldn't have included them if you didn't need integration. But be really
sure. Would it be sufficient to give the user easy access to both systems"
(Eric Evans, *Domain-Driven Design*, Addison-Wesley, 2003, ch. 14, section
"Relationships With the External Systems," final manuscript p. 269). This
variant is common in practice whenever a team is tempted to build a real
integration against a legacy or third-party system purely because the
system exists, rather than because any feature genuinely needs live data
from it.

**Separate Ways as a transitional state, not a destination.** A team
recognizes that two models clash badly enough for the deployment or
organizational reasons described under dimension 4, chooses to keep them
independent for now, and records this as a deliberate transitional state
they intend to revisit once a deeper unifying model becomes clear or once
the organizational obstacle changes. Evans describes exactly this
transition when a team shifts full responsibility for a duplicated
subdomain from one context to the other over time rather than merging
outright, calling out that this transition, which "can be quite long or
indefinite," carries "the usual advantages and disadvantages of going
Separate Ways" (Eric Evans, *Domain-Driven Design*, Addison-Wesley, 2003,
ch. 14, section "Merging Contexts (Separate Ways to Shared Kernel)," final
manuscript p. 274).

**Language- and platform-idiomatic duplication rather than a shared
package.** In a codebase this often shows up as two teams each writing
their own small type for a concept the other team also models, rather than
factoring out a shared library, a shared npm package, a shared Go module,
or a shared class hierarchy. The Go community names exactly this trade
directly in its own proverbs. "A little copying is better than a little
dependency" (Rob Pike, Go Proverbs, Gopherfest, 2015,
[go-proverbs.github.io](https://go-proverbs.github.io/), verified
2026-08-02). This is a general Go idiom, not a DDD-specific one, and this
entry states that distinction plainly, but it is the same underlying trade
Evans names for Separate Ways applied at the scale of a single utility
type rather than an entire Bounded Context, discussed further under
dimension 9.

## 9. Known production uses

- **Rob Pike's Go Proverbs, and the Go standard library's own practice of
  small, deliberate duplication over shared dependency.** In the talk that
  is the canonical statement of Go's design philosophy, delivered at
  Gopherfest SV, 2015, Pike states the proverb "a little copying is better
  than a little dependency" as one of nineteen core proverbs, directly
  alongside "the bigger the interface, the weaker the abstraction" (Rob
  Pike, "Go Proverbs," Gopherfest, 2015, transcript and slide list at
  [go-proverbs.github.io](https://go-proverbs.github.io/), verified
  2026-08-02). This is the identical cost trade Evans names for Separate
  Ways, a small amount of duplicated logic accepted specifically to avoid
  a coupling relationship, generalized from Bounded Contexts down to the
  scale of a single package. This is a widely cited design philosophy
  behind a major production language ecosystem rather than a single named
  company's case study naming Separate Ways by that term, and this entry
  states that distinction plainly.
- **The Database per Service pattern, as named and documented by Chris
  Richardson.** Richardson's microservices.io reference, drawn from his
  book *Microservices Patterns*, Manning, 2018, defines the pattern
  directly. "Keep each microservice's persistent data private to that
  service and accessible only via its API," specifically so that
  "changes to one service's database does not impact any other services"
  ([microservices.io, "Database per Service"](https://microservices.io/patterns/data/database-per-service.html),
  verified 2026-08-02). This is the data-layer instance of the same force
  Evans names for Separate Ways, that two contexts sharing a database is a
  coupling point that removes each side's ability to change independently,
  even when the two contexts otherwise integrate through service calls.
  Richardson's pattern is broader than pure Separate Ways, since services
  under this pattern typically still integrate through APIs, but the
  specific decision it documents, refusing a shared data model between
  independently owned services, is exactly the force dimension 3 of this
  entry names, and this entry states that distinction plainly rather than
  claiming the two patterns are identical.
- **The Context Mapper open source DSL, by omission rather than by an
  explicit keyword.** Context Mapper, maintained by Stefan Kapferer and the
  Software Engineering research group at the University of Applied
  Sciences of the Grisons in Chur, Switzerland, and formally described in
  Kapferer and Zimmermann, "Domain-specific Language and Tools for
  Strategic Domain Driven Design, Context Mapping and Bounded Context
  Modelling," Proceedings of the 15th International Conference on Software
  Technologies, 2020, implements the other seven Context Map relationship
  types, Partnership, Shared Kernel, Customer-Supplier, Upstream-Downstream,
  Conformist, Anticorruption Layer, and Open Host Service with Published
  Language, as first-class grammar constructs, confirmed by direct
  inspection of the project's published Xtext grammar file
  ([ContextMapper/context-mapper-dsl,
  ContextMappingDSL.xtext](https://raw.githubusercontent.com/ContextMapper/context-mapper-dsl/master/org.contextmapper.dsl/src/org/contextmapper/dsl/ContextMappingDSL.xtext),
  verified 2026-08-02) and the project's own language reference for the
  Context Map construct, which documents Bounded Contexts as a list added
  with a `contains` keyword and relationships as separately declared
  statements below that list
  ([contextmapper.org, "Context Map"](https://contextmapper.org/docs/context-map/),
  verified 2026-08-02). Neither source names a "Separate Way" relationship
  type or mentions Evans's pattern by name, and this entry states that
  fact plainly rather than overstating it. The engineering observation
  that follows is this entry's own judgement, not a claim from the
  project's documentation. because relationships in Context Mapper's model
  are declared separately from the list of Bounded Contexts, a Bounded
  Context that appears in a real, published Context Mapper `.cml` file but
  is never named in any relationship statement is, by the structure of the
  language itself, in a Separate Ways relationship with every other
  context in that map, represented by the absence of a statement rather
  than by a positive keyword, which is a direct, if implicit, structural
  echo of Evans's own definition of the pattern as an absence of
  connection.

## 10. Consequences

Positive consequences.

- Each team ships on its own schedule with no cross-team release
  coordination for the pair of contexts under this relationship, which
  removes one of the most expensive recurring costs any of the other
  Context Map patterns carries, confirmed directly by Evans's own
  deployment comparison in dimension 7.
- Each team can choose the simplest, most specialized model and the
  simplest, most specialized tool for its own problem, rather than the
  more abstract, more general model that integration with a partner would
  force, which is the specialization force named in dimension 3.
- There is no shared artifact, so there is no possibility of one team's
  change silently breaking the other team's system through a shared
  dependency, a shared database schema, or a shared library version, which
  is the same isolation benefit the Database per Service pattern documents
  under dimension 9.
- The decision is fast to make and fast to reverse in the narrow technical
  sense that no code has to be un-merged, because none was ever merged.
  Evans is explicit that this reversibility is only theoretical once real
  time has passed, discussed as a negative consequence below.
- A stalled or over-scoped project can recover momentum quickly by cutting
  a lower-priority feature loose into its own small tool, exactly as
  demonstrated in Evans's insurance project example, converting a paralyzed
  unified effort into several shippable pieces.

Negative consequences.

- Whatever functionality genuinely overlaps between the two contexts is
  duplicated, in code, in effort, and, most seriously, in data. Evans is
  explicit that this cost is real and not eliminated by the pattern. there
  will be "some duplication of effort, as different models of the same
  business activities and entities evolve" (Eric Evans, *Domain-Driven
  Design*, Addison-Wesley, 2003, ch. 14, section "Catering to Special
  Needs With Distinct Models," final manuscript p. 270).
- The two models drift further apart the longer they are left independent,
  and Evans warns this drift makes a later merge harder in practice even
  though it remains theoretically possible through refactoring. "It is
  hard to merge models that have developed in complete isolation" (Eric
  Evans, *Domain-Driven Design*, Addison-Wesley, 2003, ch. 14, section
  "Separate Ways," final manuscript p. 261).
- The Ubiquitous Language fragments. Each context develops its own dialect
  for whatever overlapping concepts exist, which Evans names as a direct
  cost. "The loss of shared language will reduce communication" (same
  source, section "Catering to Special Needs With Distinct Models," final
  manuscript p. 270).
- A person who needs data from both contexts has to gather it manually,
  since there is, by design, no automated bridge. Evans's own allowance
  for a shared middleware or UI layer, discussed under dimension 5, only
  reduces the friction of this manual work. It does not remove it.
- The pattern is easy to reach for as an excuse to avoid a genuinely
  necessary but uncomfortable integration conversation, and, in Evans's own
  words, can "become an argument against change and a justification for
  any quirky parochial model" (same source, same section, final
  manuscript p. 270), which is precisely why dimension 4's
  non-applicability list matters as much as the applicability list.

## 11. Failure modes and misuse

**Symptom.** Two systems that were declared Separate Ways for good reasons
now silently disagree about a customer's balance, address, or status, and
nobody can say which one is authoritative.
**Cause.** The two teams never revisited the decision as the systems
matured, and a concept that started out genuinely local to one context
grew, without anyone noticing the moment it happened, into a concept both
sides now depend on.
**Fix.** Treat Separate Ways as a decision with an expiration date, not a
permanent architectural fact. Periodically re-run the same cost and benefit
question from dimension 3 against the current state of both contexts, and
if a concept has become load-bearing on both sides, move deliberately
toward Shared Kernel or an explicit Anticorruption Layer using the
transformation Evans describes under dimension 14, rather than letting the
two models silently diverge on a concept that now matters to both.

**Symptom.** A support engineer, a sales rep, or a customer is asked to
manually re-enter the same information into two different systems, and the
organization treats this as an unavoidable cost of having two systems.
**Cause.** The team read "no integration" as "no automated help of any
kind, including navigation," when Evans's own definition explicitly
permits a shared middleware or UI seam, such as a linked portal page, that
carries no logic or data across the boundary but does remove the person's
burden of remembering both systems exist and finding each one separately.
**Fix.** Reread dimension 5 and dimension 6 of this entry. Build the
permitted UI-level or middleware-level seam, links, a shared portal, a
single sign-on session, even though the underlying models stay
independent. This is not a violation of Separate Ways. It is exactly the
form Evans describes.

**Symptom.** A team declares Separate Ways for two contexts, and six months
later a critical feature turns out to genuinely require live data from the
other side, so an engineer wires up a quick, undocumented, direct database
read against the other team's schema to unblock a deadline.
**Cause.** The one narrow, genuinely necessary integration point was never
acknowledged as an exception, so there was no sanctioned, small translation
layer ready to extend, and the fastest path under deadline pressure was an
unreviewed direct coupling that neither team tracks or owns.
**Fix.** When a genuine residual integration need appears, build the
narrow, explicitly scoped translation layer described under dimension 8's
second variant, owned jointly or by whichever side needs it, rather than a
silent direct dependency on the other context's internals. Evans's own
guidance is that this kind of translator, unlike a full merge, is
compatible with keeping the two models otherwise independent.

**Symptom.** Two teams that were told to keep their models separate
instead spend meetings arguing about which team's terminology is correct
for a concept neither side actually needs to share.
**Cause.** Separate Ways was declared as an excuse to avoid resolving a
genuine disagreement about a shared concept, rather than as a real finding
that the two teams' needs do not overlap. Evans names this specific
failure mode directly under dimension 4's non-applicability discussion.
**Fix.** Ask whether the disputed concept is actually used by both
contexts' features, not merely discussed by both teams. If it is genuinely
unused by one side, the argument is moot and the pattern is correctly
applied, so stop discussing it and let each team keep its own term. If it
is genuinely used by both sides, Separate Ways was the wrong pattern for
that concept from the start, and the fix is to name the disagreement
honestly and route it toward Shared Kernel or a negotiated Published
Language rather than continuing to argue under cover of an architecture
decision that does not actually apply here.

## 12. Trade-off matrix

| Force | Separate Ways | Shared Kernel | Customer-Supplier | Anticorruption Layer |
|---|---|---|---|---|
| Ongoing coordination cost | None for the pair, Evans's own deployment comparison names this the lightest option | High. mandatory joint test suite, at least weekly merge | Moderate. joint planning and a negotiated, tested interface | Low to moderate. one team owns and maintains the translator alone |
| Data or logic duplication | Full duplication of any overlapping concept, accepted deliberately | Minimal. the shared subset is defined once | Low. one model, one authoritative side | None duplicated, but a translation map must be kept current |
| Model expressiveness for each side | Maximally specialized and simple per side | Constrained on the shared subset only | Downstream constrained to what the upstream contract offers | Downstream fully free, cost paid entirely in the translator |
| Reversibility once chosen | Low in practice, high only in theory, per dimension 3 and dimension 10 | Moderate. the shared subset can be renegotiated | Moderate. the contract can be renegotiated if both sides agree | High. the translator can be extended or narrowed without touching either model |
| Best-fit team relationship | No meaningful ongoing dependency between the two teams | Two teams close enough to sustain frequent joint integration | One team genuinely upstream of another that can budget its planning | One team needs a legacy or uncooperative system's data without adopting its model |
| Cost if the underlying assumption is wrong | High. two live, diverging, load-bearing models with no bridge | Moderate. coordination overhead was unnecessary but no data drifted | Moderate. the negotiation overhead was unnecessary but a single model stayed authoritative | Low. an unused translator is dead code, not a data integrity problem |

This table compares Separate Ways only against the other named relationship
patterns in the same family described in Evans's own chapter, not against a
generic or unnamed baseline, consistent with the comparison Evans himself
draws in Figure 14.12 of the chapter, which places Separate Ways and
Conformist together at the low end of ongoing team communications
commitment, opposite Shared Kernel at the high end (Eric Evans,
*Domain-Driven Design*, Addison-Wesley, 2003, ch. 14, section "The
Tradeoff," final manuscript p. 271, Figure 14.12).

## 13. Related and incompatible patterns

**Bounded Context**, see the bounded-context entry in this repository, is
the prerequisite. Separate Ways only makes sense once two distinct
contexts have already been identified. The pattern says nothing about how
to draw the boundary itself, only about what, if anything, connects two
boundaries that already exist.

**Context Map**, see the context-map entry in this repository, is the
artifact on which the decision is recorded. A Context Map with no drawn
edge between two contexts is, by construction, declaring those two
contexts to be in a Separate Ways relationship, whether or not the team
explicitly names it that way, which is the same structural fact the
Context Mapper DSL analysis in dimension 9 identifies.

**Conformist**, see the conformist entry in this repository, is Separate
Ways's most common entry point when a downstream team genuinely abandons a
dependency rather than continuing to submit to an unhelpful upstream's
model. Evans states this transition directly, using the phrase "cut the
strings" for exactly this move, discussed under dimension 1 and dimension
4 above.

**Anticorruption Layer**, see the anticorruption-layer entry in this
repository, is not a contradiction of Separate Ways but a compatible
narrowing of it. A pair of contexts can be in a Separate Ways relationship
for their models overall while still maintaining one small, explicitly
scoped Anticorruption Layer for a single residual need, described fully
under dimension 8's second implementation variant and dimension 5's
structure. The two patterns are incompatible only in the specific sense
that an unrestricted Anticorruption Layer serving broad, ongoing
integration is no longer really Separate Ways for that pair, it has become
a full Anticorruption Layer relationship, and calling it Separate Ways at
that point would misdescribe the actual coupling on the ground.

**Shared Kernel**, see the shared-kernel entry in this repository, sits at
the opposite end of the coordination spectrum from Separate Ways and is
the pattern's most common exit point when duplication or translation
overhead becomes too costly to sustain. Evans devotes a full, named
transformation, "Merging Contexts, Separate Ways to Shared Kernel," to this
exact move, described step by step under dimension 14 below. The two
patterns are genuinely incompatible for the same pair of contexts at the
same time, since a Shared Kernel is, by definition, a drawn connection on
the Context Map, and Separate Ways is, by definition, the absence of one.

**Customer-Supplier**, see the customer-supplier entry in this repository,
is incompatible with Separate Ways for the same reason as Shared Kernel, a
Customer-Supplier relationship requires an ongoing negotiated interface
between an upstream and a downstream, which is precisely the kind of
drawn, maintained connection Separate Ways declares absent. A pair of
contexts moves between the two patterns, in either direction, but cannot
hold both at once.

**Open Host Service and Published Language**, see the open-host-service
and published-language entries in this repository, are the patterns a team
reaches for once a single Bounded Context needs to serve many downstream
consumers at once, which is a fundamentally different situation from the
two-context, no-integration-needed situation Separate Ways addresses. A
context that has genuinely gone Separate Ways from every other context in
the system has no consumers to serve through an Open Host Service in the
first place.

## 14. Refactoring path in and out

Refactoring toward Separate Ways, from a codebase that has an unwanted
integration point today, follows the same shape as Evans's insurance
project example and his three-path guidance for an unhelpful upstream
dependency.

1. List the actual requirements that touch both contexts today, not the
   use cases that merely mention both. Evans's own instruction is to be
   ruthless here, separating what genuinely needs data or logic from one
   context inside the other from what merely happens to appear in the
   same workflow diagram.
2. For each requirement that survives that filter, ask honestly whether a
   shared middleware or UI-level seam, a link, a menu, a single sign-on
   session, would satisfy the actual need without any shared logic or data
   translation. Evans's insurance example resolves almost its entire
   integration need this way, organizing standalone tools behind links on
   one intranet page.
3. For a downstream dependency that has become genuinely more trouble than
   it is worth, evaluate abandoning it outright rather than continuing to
   conform to it or building a translation layer for it, which is the
   "cut the strings" move Evans names under Conformist.
4. Remove the shared library, shared database access, or shared type that
   previously connected the two contexts, replacing it with each context's
   own independent, purpose-built implementation of whatever small amount
   of functionality genuinely overlaps.
5. Update the Context Map to remove the drawn edge between the two
   contexts, making the new Separate Ways relationship visible and
   discussable rather than an implicit fact nobody has written down. See
   the context-map entry in this repository for how this recording step
   is done in practice.

Refactoring away from Separate Ways, toward Shared Kernel, is the direction
Evans documents in the greatest procedural detail, under the heading
"Merging Contexts, Separate Ways to Shared Kernel." His own guidance,
restated here in this entry's own words rather than his, runs as follows.

1. Confirm both contexts are genuinely internally unified on their own
   before attempting to unify them with each other. A merge between two
   internally inconsistent models produces a worse result than either
   started with.
2. Agree the mechanics before writing any shared code. how the shared code
   will be physically shared, what its module naming convention will be,
   and that it will carry its own test suite with at least a weekly
   integration cadence between the two teams.
3. Pick one small, already-duplicated subdomain to merge first, ideally
   something outside the Core Domain and already served by an existing
   translation layer, so the first merge starts from a proven translation
   rather than from nothing.
4. Form a small joint group, Evans suggests two to four developers drawn
   from both teams, to design the shared model for that one subdomain,
   including reconciling any synonyms the two contexts' Ubiquitous
   Languages have accumulated for the same concept.
5. Have developers from either team implement or adapt the shared model,
   escalating back to the joint group from step 4 if real modeling
   problems surface during implementation.
6. Have each team integrate its own context against the new shared kernel,
   then remove the translation code that the shared kernel has made
   unnecessary.
7. Repeat steps 3 through 6 for additional subdomains in later iterations,
   deferring anything still tied to one context's specialized jargon until
   a genuinely deeper, unifying model emerges on its own, since Evans
   warns that a deep model cannot be scheduled, only recognized when it
   appears.

Evans also names a lighter-weight alternative that achieves some of a
merge's benefit without the ongoing coordination cost of a true Shared
Kernel, useful when one of the two existing models is simply the better
one and the team wants to eliminate duplication without taking on a shared
kernel's maintenance burden. Instead of sharing a subdomain, the weaker
context transfers full responsibility for it to the stronger one,
refactoring the weaker context's application to call directly on the
stronger context's model, with no ongoing translation layer at all (Eric
Evans, *Domain-Driven Design*, Addison-Wesley, 2003, ch. 14, section
"Merging Contexts, Separate Ways to Shared Kernel," final manuscript p.
274).

## 15. Testing and verification

Testing under Separate Ways is, in one specific sense, the easiest testing
story in the entire Context Map family, because there is no cross-context
integration point to test. Each context's test suite is complete on its
own terms, needs no test double for the other context, and runs on its own
schedule with no coordination requirement. This is a direct, practical
consequence of the deployment independence Evans describes under dimension
7.

What testing genuinely does need to cover, and what is easy to forget
precisely because the ordinary integration tests do not exist, is the
boundary itself. A test suite for a Separate Ways relationship should
assert two things that are easy to take for granted and expensive to
discover false in production. First, that no code path in either context
actually imports, calls, or reads from the other context's module or
database, which is best enforced with an architectural or dependency-graph
test that fails the build if a forbidden import appears, rather than left
to code review discipline alone. Second, where a narrow translation layer
exists for one residual need, per dimension 8's second variant, that
translator needs its own contract test in exactly the same shape an
Anticorruption Layer's translator needs, asserting the mapping stays
correct as either side's model evolves, discussed further in the
anticorruption-layer entry in this repository.

Testing should also cover the organizational assumption behind the
decision, not only the code. A periodic review, not a code test but a
process check, that re-asks the dimension 3 cost and benefit question
against the current state of both contexts is the closest thing this
pattern has to a regression test for its own continued correctness,
because the failure mode named first under dimension 11, two systems
silently disagreeing about a concept that has quietly become shared, is
invisible to any test that only exercises code that already exists. It
surfaces only when someone deliberately asks whether the original
no-overlap assumption still holds.

## 16. Observability signals

A healthy Separate Ways relationship shows almost no cross-context signal
at all, which is itself the signal to look for. Deployment logs, service
dependency graphs, and database connection strings for context A should
show zero references to context B, and vice versa. A dependency-graph
visualization or an architectural fitness function, of the kind commonly
run in continuous integration, should show two entirely disconnected
components for these two contexts, not two components joined by a thin
edge. If a dependency-graph tool such as a static import analyzer or a
service mesh's traffic graph ever shows a new edge appearing between two
contexts that are recorded on the Context Map as Separate Ways, that edge
is either an undocumented, unsanctioned coupling of the kind described in
dimension 11's third failure mode, or a sign that the relationship itself
has organically changed and the Context Map is now stale and needs
updating.

Duplication itself is also a useful, if unusual, signal to watch
deliberately rather than treat as pure waste. Tracking how much logic or
data genuinely overlaps between the two contexts over time, for example
through a periodic manual or lightly automated audit of each context's
model for concepts that also appear, independently defined, in the other
context, gives an early warning for the drift failure mode named first
under dimension 11. A small, stable amount of duplication that is not
growing is the expected, healthy state. A duplicated concept whose two
independent definitions are visibly diverging in meaning, not merely in
implementation, over successive audits is the signal that the original
no-overlap assumption behind the decision may no longer hold.

Support and operations signals matter here too, since the pattern
explicitly permits a shared UI or middleware seam. Metrics on how often a
person has to manually carry information from one system into the other,
support ticket volume tagged for exactly this reason, or a simple count of
how often a customer-facing team has to open both systems for the same
customer interaction, are the practical, human-facing cost of the
duplication Evans accepts as a trade-off, and a rising trend in that
specific metric is the clearest real-world evidence that the cost side of
the dimension 3 trade has grown large enough to revisit the decision.

## 17. Security and privacy implications

Separate Ways has a genuine, structural security benefit that is worth
stating plainly rather than treated as incidental. Because the two
contexts share no database, no library, and no translation layer, a
vulnerability, a data breach, or a misconfiguration in one context has no
direct technical path into the other. There is no shared credential, no
shared connection string, and no shared object graph for an attacker who
compromises one context to pivot through into the other, which is exactly
the isolation property the Database per Service pattern documents under
dimension 9 as a deliberate design goal for reducing blast radius.

The corresponding privacy risk is duplication of personal data. If both
contexts independently hold a copy of a person's name, address, or contact
details, because both genuinely need it and neither integrates with the
other, the organization now carries two separate systems of record for the
same personal data, each of which independently needs its own retention
policy, its own access controls, and its own deletion path for a data
subject access or erasure request under a regime such as GDPR. A
deliberate Separate Ways decision that involves personal data should
therefore be paired, from the start, with an explicit inventory of every
place that data now lives, because there is no shared translation layer
to serve as a single choke point where a deletion or correction request
could otherwise be applied once and trusted to propagate.

This entry's assessment of both points is engineering judgement grounded
in the structural facts of the pattern, isolation of failure domains on
one hand, duplication of personal data on the other, rather than a claim
sourced to Evans's own text, which does not discuss security or privacy
directly. Where the two contexts do maintain a narrow translation layer
for one residual need, per dimension 8's second variant, that translator
becomes the one place personal data does cross the boundary, and it should
be reviewed with the same care as any other data flow that moves personal
information between two independently governed systems, including
minimizing what the translator carries to only the fields the receiving
side genuinely needs.

## 18. References

- Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
  Software*, Addison-Wesley, 2003, ch. 14, "Maintaining Model Integrity,"
  sections "Separate Ways," "Conformist," "Anticorruption Layer,"
  "Relationships With the External Systems," "The System Under Design,"
  "Catering to Special Needs With Distinct Models," "Deployment," "The
  Tradeoff," and "Merging Contexts, Separate Ways to Shared Kernel."
  Direct primary-source citation confirmed by extraction of the publicly
  hosted final-manuscript PDF, final manuscript pp. 236, 249, 254 to 255,
  259 to 261, 269 to 271, and 273 to 274,
  [fabiofumarola.github.io/nosql/readingMaterial/Evans03.pdf](https://fabiofumarola.github.io/nosql/readingMaterial/Evans03.pdf),
  verified 2026-08-02.
- Vaughn Vernon, *Implementing Domain-Driven Design*, Addison-Wesley, 2013,
  ch. 3, "Context Maps." Publisher's chapter listing confirming Separate
  Ways as one of the chapter's covered Context Map relationship patterns,
  [Pearson, "Implementing Domain-Driven
  Design"](https://www.pearson.com/en-us/subject-catalog/p/implementing-domain-driven-design/P200000009616/9780133039887),
  verified 2026-08-02.
- ddd-crew, "Context Mapping," GitHub repository, listing nine named
  Context Map patterns including Separate Ways with quoted definition,
  [github.com/ddd-crew/context-mapping](https://github.com/ddd-crew/context-mapping),
  verified 2026-08-02.
- DevIQ, "Context Mapping," reference glossary entry listing the same nine
  Context Map patterns with matching definitions,
  [deviq.com/domain-driven-design/context-mapping](https://deviq.com/domain-driven-design/context-mapping/),
  verified 2026-08-02.
- Martin Fowler, "BoundedContext," bliki entry, 15 January 2014,
  confirming Bounded Context as a modeling boundary rather than a
  deployment boundary, background for dimension 5's structure,
  [martinfowler.com/bliki/BoundedContext.html](https://martinfowler.com/bliki/BoundedContext.html),
  verified 2026-08-02.
- Rob Pike, "Go Proverbs," Gopherfest, San Francisco, 2015, proverb "a
  little copying is better than a little dependency," cited under
  dimension 8 and dimension 9,
  [go-proverbs.github.io](https://go-proverbs.github.io/), verified
  2026-08-02.
- Chris Richardson, "Database per Service," pattern reference drawn from
  *Microservices Patterns*, Manning, 2018, cited under dimension 8 and
  dimension 9,
  [microservices.io/patterns/data/database-per-service.html](https://microservices.io/patterns/data/database-per-service.html),
  verified 2026-08-02.
- Stefan Kapferer and Olaf Zimmermann, "Domain-specific Language and
  Tools for Strategic Domain Driven Design, Context Mapping and Bounded
  Context Modelling," Proceedings of the 15th International Conference on
  Software Technologies, 2020. Cited for the Context Mapper project's
  academic grounding under dimension 9.
- ContextMapper project, Xtext grammar file, direct inspection confirming
  the set of formally typed relationship keywords and the absence of a
  Separate Way keyword,
  [github.com/ContextMapper/context-mapper-dsl](https://raw.githubusercontent.com/ContextMapper/context-mapper-dsl/master/org.contextmapper.dsl/src/org/contextmapper/dsl/ContextMappingDSL.xtext),
  verified 2026-08-02.
- ContextMapper project, "Context Map" language reference, confirming
  Bounded Contexts are declared with a `contains` keyword and
  relationships are declared as separate statements,
  [contextmapper.org/docs/context-map](https://contextmapper.org/docs/context-map/),
  verified 2026-08-02.

## Code examples

The point of Separate Ways is the absence of a shared type across a
boundary, so the clearest demonstration is two independently defined
models of the same everyday concept, customer, with no import, no shared
base class, and no common package linking them. Each block below compiles
and runs on its own with no reference to the others, which is itself the
proof that the two contexts share nothing.

Orders context, TypeScript, checked with `tsc --strict --noEmit`.

```typescript
interface Address {
  street: string;
  city: string;
  postalCode: string;
}

class OrderingCustomer {
  constructor(
    public readonly customerId: string,
    public readonly shipTo: Address,
    public readonly openOrderCount: number
  ) {}

  canPlaceOrder(): boolean {
    return this.openOrderCount < 25;
  }
}

const buyer = new OrderingCustomer(
  "cust-4471",
  { street: "9 Elm Row", city: "Leeds", postalCode: "LS1 4AB" },
  3
);
console.log(buyer.canPlaceOrder());
```

Support context, TypeScript, a second, unrelated `Customer`-shaped type in
a second bounded context, checked separately with `tsc --strict --noEmit`.

```typescript
type Tier = "standard" | "priority" | "enterprise";

class SupportCustomer {
  constructor(
    public readonly accountId: string,
    public readonly tier: Tier,
    public readonly openTicketCount: number
  ) {}

  slaHoursFor(severity: "low" | "high"): number {
    if (this.tier === "enterprise") return severity === "high" ? 1 : 8;
    if (this.tier === "priority") return severity === "high" ? 4 : 24;
    return severity === "high" ? 24 : 72;
  }
}

const requester = new SupportCustomer("acct-9910", "priority", 2);
console.log(requester.slaHoursFor("high"));
```

Billing context, Python, a third independent model of the same everyday
concept, checked with `python3 -m py_compile`.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class BillingCustomer:
    account_ref: str
    tax_id: str
    payment_terms_days: int

    def is_overdue(self, days_since_invoice: int) -> bool:
        return days_since_invoice > self.payment_terms_days


customer = BillingCustomer(
    account_ref="due-778", tax_id="DE123456789", payment_terms_days=30
)
print(customer.is_overdue(45))
```

Marketing context, Go, a fourth independent model, showing the pattern
also holds inside a monorepo where nothing technically prevents an import,
checked with `go vet`.

```go
package marketing

type Subscriber struct {
	Email      string
	OptedIn    bool
	SignupYear int
}

func (s Subscriber) EligibleForNewsletter() bool {
	return s.OptedIn && s.SignupYear >= 2020
}
```

Dimension 8's second implementation variant, a single narrow translator
kept for one residual need without merging the two models overall,
TypeScript, checked separately with `tsc --strict --noEmit`.

```typescript
interface SupportTicketRecord {
  account: string;
  entitlement: string;
  openCount: number;
}

interface FulfilmentRiskView {
  customerId: string;
  hasOpenComplaint: boolean;
}

function toFulfilmentRiskView(
  record: SupportTicketRecord
): FulfilmentRiskView {
  return {
    customerId: record.account,
    hasOpenComplaint: record.openCount > 0 && record.entitlement !== "standard",
  };
}

const bridged = toFulfilmentRiskView({
  account: "acct-9910",
  entitlement: "priority",
  openCount: 1,
});
console.log(bridged.hasOpenComplaint);
```

This narrow translator is the whole of dimension 8's second variant. It
reads from the support context's own record shape and produces a small,
purpose-built view for the orders context, with no shared class between
the two sides and no attempt to unify `SupportCustomer` and
`OrderingCustomer` into one model. Removing this one function removes the
entire integration surface between the two contexts, which is the
practical test of whether a Separate Ways relationship has stayed narrow
or has quietly grown into something else.

Java and Rust are available in this environment and were considered, but
this entry limits itself to the four languages above, because the pattern
itself carries no language-specific structure beyond a plain data type,
and a fifth or sixth restatement of the same shape would add length
without adding a new idea the reader has not already seen in the first
four blocks.
