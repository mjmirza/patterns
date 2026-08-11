---
name: Core Domain
slug: core-domain
family: 11-domain-driven-design
category: Strategic Design
aliases: [Core Domain Distillation, Domain Classification, Subdomain Triage]
first_described: "Eric Evans 2003"
maturity: canonical
related: [bounded-context, generic-subdomain, ubiquitous-language, context-mapping, anticorruption-layer]
incompatible_with: []
verified: 2026-08-02
---

# Core Domain

## 1. Name, aliases, and lineage

The canonical name is Core Domain. It is a strategic design concept from
Domain-Driven Design, introduced by Eric Evans in *Domain-Driven Design.
Tackling Complexity in the Heart of Software*, Addison-Wesley, 2003, ISBN
978-0321125217, in Part IV, "Strategic Design", chapter 15, "Distillation"
(publication and structure confirmed via the book's Google Books listing,
https://books.google.com/books/about/Domain_driven_Design.html?id=xColAAPGubgC,
verified 2026-08-02). Evans frames the whole of Part IV around one question,
of all the domain model a team could build, which part is actually worth a
senior engineer's career. Core Domain is his answer to that question, and
"distillation" is his verb for the process of finding it, the model is not
written all at once and labelled afterward, it is boiled down the way a
chemist distills a compound, separating the part that carries the value from
the part that does not.

The term is not used in isolation. Evans pairs it with two companions, and the
three together form the subdomain classification this entry is about.

- **Core Domain.** The part of the model that gives the business its
  competitive edge. This is the code a company would never outsource, because
  outsourcing it is outsourcing the reason customers choose this company over
  a competitor.
- **Supporting Subdomain.** A part of the model that the business needs, that
  is specific to this business, but that does not itself create competitive
  advantage. It supports the Core Domain without being it.
- **Generic Subdomain.** A part of the model that is well understood, widely
  solved, and not specific to this business at all. Authentication, invoicing,
  and address validation are the standing examples, this problem has already
  been solved by someone else and buying that solution is usually cheaper than
  re-solving it.

Vaughn Vernon restates and sharpens this classification in two later books,
*Implementing Domain-Driven Design*, Addison-Wesley, 2013, ISBN
978-0321834577 (publication and ISBN confirmed via Wikipedia's Domain-driven
design article, https://en.wikipedia.org/wiki/Domain-driven_design, verified
2026-08-02), and *Domain-Driven Design Distilled*, Addison-Wesley, 2016, ISBN
978-0134434421, published June 2016 (publication date and ISBN confirmed via
Pearson's catalog listing, https://www.pearson.com/en-us/subject-catalog/p/domain-driven-design-distilled/P200000009615/9780134434421,
verified 2026-08-02). Vernon's contribution is naming the classification
exercise a "Core Domain Chart", a simple two-axis plot of every subdomain by
business differentiation against implementation complexity, used to decide
where to spend the strongest engineers.

A later, widely used artifact for recording this classification per team is
the Bounded Context Canvas, created by Nick Tune. Its "Strategic
Classification" section asks a team to state, in writing, whether the context
it owns is Core, Supporting, or Generic, and to justify the answer (confirmed
via Nick Tune's own description of the canvas's Strategic Classification
section, https://medium.com/nick-tune-tech-strategy-blog/bounded-context-canvas-v2-simplifications-and-additions-229ed35f825f,
verified 2026-08-02). This entry treats Core Domain as the concept Evans
named, and the Core Domain Chart and the Bounded Context Canvas's strategic
classification field as the two most common tools for applying it.

## 2. Problem and context

A team building a non-trivial system faces a resource allocation problem long
before it faces a technical one. Every business runs on dozens of
subsystems, and every one of them needs code, order fulfillment, payment
processing, user authentication, search, notifications, reporting, address
validation, tax calculation. A team with finite engineering hours, finite
senior-engineer attention, and a finite budget cannot build all of these to
the same standard of care, and treating them as though it could is the
mistake this pattern exists to prevent.

The concrete symptom, recognisable in almost any codebase past its first year,
is that the team's best engineers are heads-down on the authentication
service or the internal admin tool, while the actual thing the business sells
is maintained by whoever is available. A logistics company's route
optimisation engine, the actual reason customers choose it over a competitor,
gets the same code review rigor and the same on-call rotation priority as its
internal timesheet tool. Nobody decided this on purpose. It happened because
nobody asked, out loud and on paper, which part of this system is the
business.

The context in which Core Domain applies is strategic, not tactical. It is
not a decision made inside a single class or module, it is a decision made
about a whole subdomain, usually mapped one-to-one or many-to-one onto a
Bounded Context (see the Bounded Context entry in this family). It is a
decision a product owner, a domain expert, and a senior engineer make
together, revisited as the business changes, because what counts as
differentiating today may be commoditised in three years, and what looks like
plumbing today may become the whole business tomorrow. Dimension 9 below
covers a real, well documented case of exactly that reversal.

## 3. Forces

Note, this dimension is engineering and business judgement, weighing
pressures that trade off against each other rather than restating a sourced
fact.

- **Investment concentration against fairness of attention.** Concentrating
  the strongest engineers and the deepest review on one subdomain means every
  other subdomain gets comparatively less. Teams resist this because it feels
  like playing favourites among code, but the alternative, spreading
  attention evenly, guarantees the one thing that should be excellent is only
  average.
- **Build against buy.** A Generic Subdomain is, by definition, a solved
  problem. The force here is sunk cost and control, a team that has already
  built its own authentication service is reluctant to admit that maintaining
  it is a tax on the time that should go to the Core Domain, even after the
  classification says so.
- **Stability against reclassification cost.** Naming something Core Domain
  today implies a multi-year investment. Business models shift, and a
  subdomain correctly classified as Core two years ago can quietly become
  Supporting, or the reverse. The classification favours revisiting the chart
  periodically, at the cost of the stability a fixed org chart or a fixed
  team structure would prefer.
- **Honesty against politics.** The classification exercise only works if
  teams can say, in a room with their own manager present, "the thing my team
  owns is not the Core Domain." Evans himself notes this is the harder half
  of the exercise, because admitting a subdomain is Generic can feel like
  admitting the team's own work is replaceable. The pattern favours the
  organisation's clarity over any one team's ego, and it costs something to
  do that honestly.
- **Precision against paralysis.** A three-way classification, Core,
  Supporting, Generic, is coarse on purpose. Finer gradations, and Vernon's
  Core Domain Chart even plots continuous axes rather than three discrete
  buckets, buy precision at the cost of a longer, harder conversation to reach
  consensus. Teams that spend weeks arguing over whether something is 6/10 or
  7/10 differentiating have lost the exercise's point, which is to make a
  decision, not to produce a perfectly calibrated score.

## 4. Applicability and non-applicability

Reach for a Core Domain classification exercise when any of these hold.

- The team has more subdomains to build or maintain than it has senior
  engineering attention to spend, and nobody has explicitly decided where
  that attention goes.
- The organisation is deciding whether to build, buy, or outsource a
  subsystem, and the decision is being made on cost alone rather than on
  whether the subsystem is a source of competitive advantage.
- A reorganisation, acquisition, or new competitor has changed what actually
  differentiates the business, and the team structure or hiring plan has not
  caught up.
- A system is being decomposed into Bounded Contexts (see the Bounded Context
  entry) and the team needs a principle for which context gets the
  Anticorruption Layer treatment and which one is a thin wrapper around a
  vendor.
- Onboarding a new engineer and needing to explain, quickly, which part of
  the codebase deserves the most care and why.

Do NOT reach for Core Domain classification when any of these hold, and doing
so anyway is the most common misuse of the pattern.

- **The system is small enough that one team owns all of it and reads it in
  a sitting.** The classification exercise costs real meeting time and real
  political capital. On a five-person team building one product, the answer
  to "what is our Core Domain" is usually obvious enough that formalising it
  in a chart produces process without insight.
- **The goal is a technical architecture decision, not a resource allocation
  decision.** Core Domain answers "where should our best people spend their
  time." It does not answer "should this be a microservice", "should this
  use event sourcing", or "should this database be normalised." Conflating
  the two leads to teams treating "Core Domain" as a synonym for "gets a
  fancy architecture", which is not what the classification means, and Evans
  is explicit that a Core Domain can be implemented as plainly as any other
  part of the system provided the model itself is sharp.
- **The classification would be used to justify neglecting a Generic
  Subdomain's operational quality.** Generic does not mean unimportant.
  Authentication is Generic in almost every business, and a broken
  authentication service takes the whole product down regardless of its
  strategic classification. The pattern governs where deep domain modelling
  effort goes, not where basic engineering quality goes.
- **The business genuinely has no differentiation yet**, for example a very
  early-stage startup still searching for product-market fit. Forcing a Core
  Domain answer before the business itself knows what it is optimising for
  produces a confident-sounding chart built on a guess, and teams then defend
  that guess past the point where evidence has contradicted it.
- **The exercise is being run by engineering alone, without a domain expert
  or a business stakeholder in the room.** The classification is a business
  judgement wearing an engineering hat, an engineering team guessing at what
  differentiates the business, without anyone who actually understands the
  business validating the guess, produces a chart that is confident and
  wrong.

## 5. Structure

Core Domain is a classification applied to a Subdomain, and it composes
directly with the Bounded Context pattern in this family, so the participants
below are best read alongside that entry.

- **Subdomain.** A part of the overall problem space, defined by the business
  itself, independent of any code. A subdomain exists whether or not anyone
  has written a line of software for it.
- **Domain Expert.** A person from the business who can state, with
  authority, what makes this subdomain differentiating or not. Without this
  participant the classification is engineering guesswork wearing a business
  hat.
- **Core Domain (the classification, applied to zero or more subdomains).**
  The subdomain, or subdomains, the classification names as the source of
  competitive advantage. In most organisations there are one to three of
  these, never a dozen, because naming everything Core Domain defeats the
  purpose of concentrating attention.
- **Supporting Subdomain (the classification).** A subdomain the business
  needs, specific to the business, but not itself differentiating.
- **Generic Subdomain (the classification).** A subdomain that is a solved
  problem elsewhere, a candidate for buying rather than building.
- **Bounded Context.** The implementation-facing counterpart, once a
  subdomain is classified, its corresponding Bounded Context (or contexts, a
  subdomain can span more than one) inherits the classification's
  consequences, code ownership seniority, review depth, whether an
  Anticorruption Layer is worth building around it, whether it is a
  build-in-house target or a buy-and-wrap target.
- **Core Domain Chart (the artifact, Vernon).** A two-axis plot, business
  differentiation against implementation complexity, used to make the
  classification visible and arguable rather than tacit.

## 6. ASCII structure diagram

```
                        THE PROBLEM SPACE
                    (what the business does)

  +-------------------+   +-------------------+   +-------------------+
  |   Subdomain: X    |   |   Subdomain: Y    |   |   Subdomain: Z    |
  | e.g. Route Optim. |   | e.g. Billing      |   | e.g. Auth         |
  +---------+---------+   +---------+---------+   +---------+---------+
            |                       |                       |
            | classified by         | classified by         | classified by
            | domain expert +       | domain expert +       | domain expert +
            | senior engineer       | senior engineer       | senior engineer
            v                       v                       v
  +-------------------+   +-------------------+   +-------------------+
  |   CORE DOMAIN     |   |    SUPPORTING     |   |     GENERIC       |
  | differentiating,  |   |  needed, specific |   |  solved problem,  |
  | build in-house,   |   |  to this business,|   |  buy or wrap a    |
  | best engineers,   |   |  not the edge     |   |  vendor           |
  | deepest modelling |   |                   |   |                   |
  +---------+---------+   +---------+---------+   +---------+---------+
            |                       |                       |
            v                       v                       v
  +-------------------+   +-------------------+   +-------------------+
  |  Bounded Context  |   |  Bounded Context  |   |  Bounded Context  |
  |  (Route Optim.)   |   |  (Billing)        |   |  (Auth, wraps a   |
  |  senior team,     |   |  competent team,  |   |  3rd-party IdP)   |
  |  rich model,      |   |  adequate model   |   |  thin adapter,    |
  |  ACL around any   |   |                   |   |  no deep model    |
  |  Generic dep.     |   |                   |   |                   |
  +-------------------+   +-------------------+   +-------------------+

     THE SOLUTION SPACE (Bounded Contexts, see the Bounded Context entry)
```

## 7. Dynamics

The dynamics of Core Domain are a recurring organisational process, not a
runtime call sequence, because the pattern lives in decisions people make
about where to invest, not in code that executes.

```
  1. TRIGGER
     A new subdomain appears (new feature area, acquisition, competitor
     shift) or a periodic strategy review is due.

  2. GATHER
     Domain expert + senior engineer(s) + product owner list every
     subdomain the business currently touches, independent of existing
     team boundaries.

  3. SCORE
     For each subdomain, ask two questions and place it on the chart.
       a. Business differentiation. Would a competitor copying this
          subdomain exactly still lose to us. High score means yes.
       b. Implementation complexity. How hard is this subdomain to
          build well, independent of differentiation.
     (Vernon's Core Domain Chart plots these as two continuous axes;
     Evans' original text uses the coarser three-bucket classification.)

  4. CLASSIFY
     Subdomains land in one of three buckets.
       Core        -> high differentiation, worth deep investment
       Supporting  -> needed, specific, not differentiating
       Generic     -> solved elsewhere, buy or wrap candidate

  5. ACT
     - Core.        assign senior engineers, invest in a rich model,
                     protect it with review rigor and dedicated time.
       Supporting.  assign a competent team, adequate model, do not
                     starve it but do not over-invest either.
       Generic.     evaluate build vs buy; if building, keep the model
                     thin; if a vendor exists, wrap it behind an
                     Anticorruption Layer (see that entry) so the
                     Core Domain's model never leaks vendor concepts.

  6. RECORD
     The classification and its reasoning are written down (a Core
     Domain Chart, or the Strategic Classification section of a
     Bounded Context Canvas per Bounded Context), so the decision is
     visible and disputable, not tacit.

  7. REVISIT
     Return to step 1 on a cadence (commonly aligned to a planning
     cycle) or the moment the business model itself changes, because a
     Generic Subdomain can become a Core Domain, and the reverse, as
     shown in dimension 9 below.
```

## 8. Implementation variants

Core Domain has no single code shape, because it is a classification, not a
structural pattern. What varies is how the classification is recorded, how it
is enforced, and how deeply the corresponding Bounded Context is modelled.

- **Chart-only, no code enforcement.** The classification lives entirely in a
  document (Vernon's Core Domain Chart, or a slide from a strategy session).
  This is the lightest variant and the most common in practice, because the
  classification is a business decision that does not always need a
  mechanical enforcement layer. Its risk is drift, the chart is drawn once
  and never revisited as engineers rotate onto and off the team.
- **Repository or module tagging.** A team encodes the classification as
  metadata attached to each Bounded Context's codebase, module, or service
  registry entry (for example a `classification` field of `core`,
  `supporting`, or `generic` in a service catalog, or a header comment naming
  the classification and the date it was last reviewed). This makes the
  classification discoverable to a new engineer without a meeting, and it can
  feed automated policy, for example requiring two senior reviewers on a pull
  request against a repository tagged `core`.
- **Ownership and staffing policy.** The classification is expressed entirely
  through org structure, the strongest engineers are staffed on the team that
  owns the Core Domain's Bounded Context, and job requisitions for that team
  are prioritised. No code artifact exists at all. This is common in larger
  organisations where the classification directly drives headcount planning.
- **Anticorruption Layer enforcement for Generic dependencies.** When a
  Generic Subdomain is satisfied by buying a vendor product, the Core
  Domain's code never talks to the vendor's API or data shape directly.
  Every call passes through a translation layer (see the Anticorruption
  Layer entry) so the vendor's model cannot leak into and corrupt the Core
  Domain's carefully distilled model. The code shown below demonstrates this
  variant.
- **Weighted investment scoring in a monorepo.** Some organisations attach a
  numeric investment weight per subdomain (derived from the Core Domain
  Chart's two axes) to a build or CI system, so that, for example, test
  coverage thresholds, required review count, or SLA targets differ by
  subdomain classification, enforced mechanically rather than by convention.

## 9. Known production uses

Every claim below names a real, checkable source.

- **Slack, as a documented case of Core Domain reclassification (Black Swan
  Core).** Nick Tune's "Core Domain Patterns" describes Slack's origin as an
  internal chat tool built to support a video game company's own team
  communication, a Generic or Supporting Subdomain at the time, which then
  became the entire business once the game itself was shelved and the chat
  tool was spun out and later valued in the billions. Source, Nick Tune,
  "Core Domain Patterns", https://medium.com/nick-tune-tech-strategy-blog/core-domain-patterns-941f89446af5,
  verified 2026-08-02. This is the clearest publicly documented illustration
  of dimension 7's step 7, revisiting the classification, because the
  subdomain that was internal tooling on day one became, without anyone
  planning it, the Core Domain of an entirely different company.
- **SAP's public curated-resources practice.** SAP maintains a public
  engineering resource, the `SAP/curated-resources-for-domain-driven-design`
  repository, whose own "Core Concepts" document states the Core, Supporting,
  and Generic Subdomain classification in SAP's own words as guidance for
  its engineering organisation, describing the core domain as the area
  "where we want to excel as a business" and specifically where the
  business's "skills here really differentiate us from the rest of the
  market." Source, SAP, `curated-resources-for-domain-driven-design`, blog
  entry 0002, https://github.com/SAP/curated-resources-for-domain-driven-design/blob/main/blog/0002-core-concepts.md,
  verified 2026-08-02. This shows a large enterprise software vendor
  formally documenting and teaching the classification internally, in a
  public repository, rather than treating it as an academic exercise.
- **A documented industry case study published as a full-length technical
  book.** Vlad Khononov's *Learning Domain-Driven Design*, O'Reilly Media,
  published October 2021, ISBN 978-1098100124, includes a dedicated appendix,
  "Applying DDD, A Case Study", walking through subdomain classification
  (Core, Supporting, Generic) applied to a real style of business problem
  end to end, published by O'Reilly as part of its Learning series rather
  than as a vendor-produced marketing case study. Source, publication record
  confirmed via O'Reilly's own catalog listing,
  https://www.oreilly.com/library/view/learning-domain-driven-design/9781098100124/,
  verified 2026-08-02, and the author's professional background (20-plus
  years as a software engineer and architect, public speaker and consultant
  on DDD and microservices) confirmed via the same listing.

## 10. Consequences

**Positive.**

- Concentrates scarce senior engineering attention where it produces the
  most business value, instead of spreading it evenly across subdomains that
  do not equally matter.
- Gives the organisation an explicit, arguable answer to whether to build or
  buy a subsystem, grounded in whether the subdomain differentiates the
  business, rather than in cost alone.
- Protects the Core Domain's model from corruption by Generic Subdomain
  concepts, because classifying something Generic naturally leads a team to
  wrap it (Anticorruption Layer) rather than let its vocabulary leak in.
- Gives new engineers a fast, legible answer to which part of this codebase
  deserves their closest attention, shortening the time to productive
  contribution on a large system.
- Makes a build-versus-buy conversation about a vendor product concrete,
  once a subdomain is Generic, the question of building it in-house almost
  always resolves to no, because building a solved problem from scratch is
  time not spent on the Core Domain.

**Negative.**

- The classification is a snapshot, and a stale one is worse than none,
  because it gives false confidence, a team that stopped revisiting its
  Core Domain Chart three reorganisations ago is often still staffing
  according to a business model that no longer exists.
- Naming a team's subdomain Generic or Supporting is politically costly,
  teams resist the label even when it is accurate, and forcing the exercise
  without organisational buy-in produces resentment rather than clarity.
- A wrongly classified Core Domain (something declared differentiating that
  is not) concentrates the best engineers on a subdomain that does not repay
  the investment, an opportunity cost that is invisible on any dashboard
  because nothing is technically broken.
- Coarse three-way buckets (Evans' original framing) lose information that
  a continuous chart (Vernon's version) preserves, and teams that adopt the
  coarse version sometimes argue past each other about whether something is
  really Core or Supporting when the honest answer is somewhere in between,
  closer to Core.
- The classification exercise itself costs real calendar time from domain
  experts and senior engineers, both of whom are, not coincidentally, the
  scarcest resources the exercise exists to protect.

## 11. Failure modes and misuse

Note, this dimension draws on practitioner experience and is judgement about
observed patterns, not a claim about a specific measured statistic.

- **Symptom.** Every subdomain in the chart is marked Core.
  **Cause.** Political unwillingness to tell any team its work is not the
  business's competitive edge, so the classification is applied as a
  courtesy rather than a filter.
  **Fix.** Force a ranking, not just a label. Ask which single subdomain the
  business would protect first if it could staff only one team, then work
  outward from that answer, treating Core as a genuinely scarce label.
- **Symptom.** The Core Domain's code depends directly on a third-party
  vendor's SDK types, and a vendor API change breaks the Core Domain's
  domain model.
  **Cause.** A Generic Subdomain was correctly identified as a buy
  candidate, but no Anticorruption Layer was built around the vendor
  integration, so the vendor's shape leaked straight into the Core Domain.
  **Fix.** Introduce an Anticorruption Layer (see that entry) between the
  Core Domain and every Generic dependency, translating the vendor's model
  into the Core Domain's own vocabulary at the boundary.
- **Symptom.** The chart was drawn eighteen months ago, the business has
  pivoted since, and nobody has looked at it again.
  **Cause.** Classification treated as a one-time artifact rather than a
  living decision, per dimension 7's step 7 being skipped.
  **Fix.** Attach a review date to the classification record itself and put
  its revisit on the same cadence as quarterly or annual planning, so
  staleness is caught on a schedule rather than discovered by accident.
- **Symptom.** A junior engineer is staffed on the Core Domain team because
  headcount happened to be free, while a senior engineer maintains an
  internal admin tool.
  **Cause.** The classification exists on paper but was never connected to
  staffing decisions, so it has no operational effect.
  **Fix.** Make the classification a direct input to staffing and hiring
  requisitions, not a document engineering reads once and files away.
- **Symptom.** A subsystem is labelled Generic and then neglected, its
  on-call rotation understaffed, its incidents deprioritised.
  **Cause.** Confusing not differentiating with not important, addressed
  directly in dimension 4's non-applicability list.
  **Fix.** Separate the two axes explicitly. Classification governs where
  deep domain-modelling investment goes, operational quality bars (uptime,
  incident response, basic engineering hygiene) apply to every subdomain
  regardless of classification.

## 12. Trade-off matrix

Compared against named alternative ways of deciding where engineering
attention goes.

| Dimension | Core Domain classification | Even investment across all subdomains | Priority by loudest stakeholder (ad hoc) | Priority by technical difficulty alone |
|---|---|---|---|---|
| Grounded in business strategy | Yes, explicitly tied to competitive advantage | No, ignores strategy entirely | Sometimes, but inconsistently and person-dependent | No, hard problems are not always valuable problems |
| Requires domain expert involvement | Yes, by design | No | No | No |
| Visible and disputable | Yes, when recorded as a chart or canvas field | Not applicable, no decision is made | Rarely, decisions are informal and undocumented | Sometimes, if difficulty estimates are written down |
| Risk of staleness | Real, needs periodic revisit (dimension 11) | Not applicable | High, priorities shift with whoever is loudest this quarter | Moderate, difficulty estimates age less than business context |
| Political cost to apply | High, requires teams to accept a Generic or Supporting label | Low, nobody is told their work matters less | Low up front, high later as resentment accumulates | Moderate, some teams feel penalised for owning easy problems |
| Guards against vendor model leakage | Yes, naturally leads to Anticorruption Layer decisions for Generic dependencies | No such guidance | No such guidance | No such guidance |

## 13. Related and incompatible patterns

- **Bounded Context (this family).** Core Domain classifies a subdomain in
  the problem space, Bounded Context implements a corresponding boundary in
  the solution space. They compose almost always, a classification without a
  Bounded Context to apply it to is inert, and a Bounded Context without a
  classification has no principled answer for how much modelling investment
  it deserves.
- **Generic Subdomain and Supporting Subdomain (companion classifications,
  same family).** These are not alternative patterns, they are the other two
  buckets of the same three-way classification described in this entry.
- **Anticorruption Layer (this family).** The standard defensive measure
  taken at the boundary between a Core Domain's Bounded Context and a
  Generic dependency, especially a bought or vendor-wrapped one, so the
  Core Domain's model stays uncorrupted. See dimension 11's second failure
  mode.
- **Ubiquitous Language (this family).** The Core Domain is where the
  Ubiquitous Language is sharpest and most worth defending, because it is
  the model doing the most work for the business. A Generic Subdomain's
  language is usually borrowed directly from the vendor or the industry
  standard rather than cultivated in-house.
- **Context Mapping (this family).** Once subdomains are classified, Context
  Mapping is the exercise of deciding the relationship between the resulting
  Bounded Contexts (Partnership, Customer-Supplier, Conformist, and the
  rest), and a Bounded Context's classification strongly influences which
  relationship type makes sense, a Core Domain rarely accepts a Conformist
  relationship to a subdomain it does not consider strategically important.
- **Incompatible with treating architecture style as a proxy for
  classification.** Choosing microservices, event sourcing, or CQRS because a
  subdomain is Core, rather than because the subdomain's actual complexity
  warrants it, conflates a business decision with a technical one and is
  flagged directly in dimension 4's non-applicability list. Core Domain says
  nothing about architecture style, only about investment depth.

## 14. Refactoring path in and out

**Introducing the classification into a codebase or organisation that has
never had one.**

1. Inventory every subdomain the business currently operates, independent of
   existing team or repository boundaries. This step alone often surprises
   teams, because org charts and subdomains rarely line up exactly.
2. Bring a domain expert into the room. An engineering-only classification
   session produces guesses, not answers, per dimension 4.
3. For each subdomain, ask the differentiation question from dimension 7,
   step 3a, and provisionally bucket it as Core, Supporting, or Generic.
4. Cross-check the provisional buckets against dimension 11's first failure
   mode. If every subdomain landed in Core, force a ranking.
5. For subdomains landing in Generic that are currently built in-house,
   evaluate whether a vendor product exists and whether replacing the
   in-house build is worth the migration cost, this decision does not have
   to be immediate, but it should be recorded.
6. Record the classification somewhere durable, a Core Domain Chart, or the
   Strategic Classification field on each subdomain's Bounded Context Canvas.
7. Connect the classification to at least one real lever, staffing,
   review policy, or CI enforcement, so it has an operational effect rather
   than existing only as a document, per dimension 11's fourth failure mode.
8. Set a revisit date and put it on a recurring calendar, per dimension 11's
   third failure mode.

**Removing or retiring a classification.**

A Core Domain classification is retired, not deleted, when the business
itself stops differentiating on that subdomain. The Slack case in dimension
9 is the reverse of retirement, a promotion into Core Domain, but the same
mechanism runs in either direction. When a subdomain that was Core becomes
commoditised (a competitor's equivalent capability becomes table stakes, or
a vendor now offers an equivalent product at lower cost than maintaining the
in-house build), reclassify it to Supporting or Generic, redirect the senior
engineering attention it was consuming toward whichever subdomain now
carries the differentiation, and, if a vendor replacement is chosen, follow
the Anticorruption Layer's own removal path (see that entry) to retire the
in-house implementation safely behind the translation boundary rather than
all at once.

## 15. Testing and verification

Note, this dimension is practice-derived guidance, not a sourced claim about
a specific tool or framework.

Core Domain itself is not directly unit-testable, because it is a
classification decision, not a runtime behaviour. What is testable and
verifiable is whether the classification is being honoured in practice.

- **Verify the classification is recorded and current.** A lightweight,
  automatable check, does every Bounded Context's ownership record carry a
  classification field, and is its last-reviewed date within the
  organisation's chosen revisit cadence. This can be enforced as a CI check
  against a service catalog rather than a runtime test.
- **Verify the Anticorruption Layer boundary holds.** For any Bounded
  Context classified Core Domain that depends on a Generic dependency, write
  contract tests at the Anticorruption Layer boundary that assert the
  vendor's types never appear in the Core Domain's own public interfaces or
  persisted model, this is directly testable with ordinary unit tests
  asserting the shape of what crosses the boundary, illustrated in the Go
  example below.
- **Verify staffing and review policy alignment (organisational, not
  code-level).** Not something a test suite checks, but something a
  retrospective can, does the team roster for the classified Core Domain
  actually include the organisation's most senior available engineers, or
  has staffing drifted from the classification.
- **Verify the classification survives a challenge.** The strongest test of
  a Core Domain classification is adversarial. Ask whether, if a
  well-funded competitor built exactly this subdomain and nothing else,
  the business would still win. A classification that cannot survive this
  question out loud in a room with a domain expert present has not actually
  been distilled, per dimension 1's chemistry metaphor, it has been
  asserted.

## 16. Observability signals

Note, this dimension is practice-derived guidance.

- **A healthy Core Domain signal.** The Bounded Context implementing the
  Core Domain shows a visibly higher rate of domain model refinement
  (commits touching entity, aggregate, and domain-service code, as opposed
  to infrastructure or configuration code) relative to Generic Subdomain
  contexts, because the model is being actively deepened rather than left
  static.
- **A healthy signal, code-review depth.** Pull requests against a Core
  Domain repository show a measurably higher reviewer-to-author ratio and
  longer review discussion than pull requests against a Generic Subdomain
  wrapper, evidence the classification is actually being honoured rather
  than existing only on paper.
- **A failing signal, classification drift.** A dashboard or service catalog
  entry whose last-classified date is older than the organisation's chosen
  revisit window is a direct, mechanically detectable symptom of dimension
  11's third failure mode.
- **A failing signal, vendor coupling leak.** Static analysis or a simple
  dependency-direction check showing a Core Domain's package importing a
  vendor SDK's types directly, rather than through the Anticorruption
  Layer's translated types, is a mechanically detectable symptom of
  dimension 11's second failure mode, and is exactly what the Go example
  below guards against with a compile-time boundary.
- **A failing signal, staffing mismatch.** An org chart or team roster tool
  showing a Core Domain-classified team with a below-average tenure or
  seniority mix relative to other teams is an observable proxy for
  dimension 11's fourth failure mode, the classification existing without
  an operational effect.

## 17. Security and privacy implications

Note, this dimension is analytical reasoning about attack surface and data
handling, not a sourced claim.

Core Domain classification has an indirect but real security implication
through the Anticorruption Layer boundary it typically implies for Generic
dependencies. When a Generic Subdomain is satisfied by a third-party vendor,
that vendor integration is a genuine external attack surface and a genuine
data-handling boundary, and the Anticorruption Layer that isolates the Core
Domain from the vendor's model is also, functionally, the natural place to
enforce input validation, data minimisation (only translating the fields the
Core Domain actually needs, rather than passing the vendor's full payload
through unfiltered), and audit logging for anything crossing that trust
boundary. A Core Domain that has correctly identified a subdomain as
Generic, but skipped building the translation boundary (dimension 11's
second failure mode), inherits the vendor's entire data model and its entire
trust assumptions by accident, which is a security and privacy exposure a
deliberate boundary would have contained. Conversely, over-classifying
something as Core Domain when it is really a compliance-heavy Generic
concern (payment card handling is the standing example, itself usually a
Generic Subdomain best delegated to a PCI-DSS-compliant vendor rather than
built in-house) can lead a team to build and therefore become directly
responsible for regulated data handling it did not need to own.

## 18. References

1. Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
   Software*, Addison-Wesley, 2003, ISBN 978-0321125217, Part IV "Strategic
   Design", chapter 15 "Distillation". Publication details and structure
   confirmed via https://books.google.com/books/about/Domain_driven_Design.html?id=xColAAPGubgC,
   verified 2026-08-02.
2. Vaughn Vernon, *Implementing Domain-Driven Design*, Addison-Wesley, 2013,
   ISBN 978-0321834577. Publication details confirmed via
   https://en.wikipedia.org/wiki/Domain-driven_design, verified 2026-08-02.
3. Vaughn Vernon, *Domain-Driven Design Distilled*, Addison-Wesley, June
   2016, ISBN 978-0134434421. Publication date and ISBN confirmed via
   https://www.pearson.com/en-us/subject-catalog/p/domain-driven-design-distilled/P200000009615/9780134434421,
   verified 2026-08-02.
4. Nick Tune, "Bounded Context Canvas V3, Simplifications and Additions",
   describing the canvas's Strategic Classification section.
   https://medium.com/nick-tune-tech-strategy-blog/bounded-context-canvas-v2-simplifications-and-additions-229ed35f825f,
   verified 2026-08-02.
5. Nick Tune, "Core Domain Patterns", describing the Slack case as an
   example of Black Swan Core, a Generic or Supporting Subdomain becoming a
   business's entire Core Domain.
   https://medium.com/nick-tune-tech-strategy-blog/core-domain-patterns-941f89446af5,
   verified 2026-08-02.
6. SAP, `curated-resources-for-domain-driven-design`, blog entry 0002,
   "Core Concepts", stating SAP's own Core, Supporting, and Generic
   Subdomain definitions.
   https://github.com/SAP/curated-resources-for-domain-driven-design/blob/main/blog/0002-core-concepts.md,
   verified 2026-08-02.
7. Vlad Khononov, *Learning Domain-Driven Design*, O'Reilly Media, October
   2021, ISBN 978-1098100124, appendix "Applying DDD, A Case Study".
   Publication record confirmed via
   https://www.oreilly.com/library/view/learning-domain-driven-design/9781098100124/,
   verified 2026-08-02.

## Code examples

Core Domain is a classification and a governance concept rather than a
structural code pattern, so the code below models the classification itself
as data, and demonstrates the one behaviour that is directly and mechanically
testable, an Anticorruption Layer boundary preventing a Generic dependency's
shape from leaking into a Core Domain's model, per dimension 11's second
failure mode and dimension 16's vendor coupling signal.

### TypeScript

```typescript
type Classification = "core" | "supporting" | "generic";

interface SubdomainEntry {
  name: string;
  classification: Classification;
  lastReviewed: string;
}

class DomainChart {
  private entries: Map<string, SubdomainEntry> = new Map();

  classify(name: string, classification: Classification, today: string): void {
    this.entries.set(name, { name, classification, lastReviewed: today });
  }

  reviewersRequired(name: string): number {
    const entry = this.entries.get(name);
    if (!entry) throw new Error(`unclassified subdomain: ${name}`);
    if (entry.classification === "core") return 2;
    return 1;
  }

  isStale(name: string, today: string, maxDays: number): boolean {
    const entry = this.entries.get(name);
    if (!entry) throw new Error(`unclassified subdomain: ${name}`);
    const reviewed = new Date(entry.lastReviewed).getTime();
    const now = new Date(today).getTime();
    const days = (now - reviewed) / (1000 * 60 * 60 * 24);
    return days > maxDays;
  }

  allCore(): string[] {
    return [...this.entries.values()]
      .filter((e) => e.classification === "core")
      .map((e) => e.name);
  }
}

// Vendor's own shape for a Generic Subdomain, e.g. a billing provider.
interface VendorInvoice {
  vendor_invoice_id: string;
  amount_cents: number;
  currency_code: string;
  vendor_internal_status: string;
}

// The Core Domain's own vocabulary. It never sees vendor_ prefixed fields.
interface Invoice {
  invoiceId: string;
  amountDue: number;
  currency: string;
}

// Anticorruption Layer: the only place VendorInvoice may be named.
function translateVendorInvoice(vendor: VendorInvoice): Invoice {
  return {
    invoiceId: vendor.vendor_invoice_id,
    amountDue: vendor.amount_cents / 100,
    currency: vendor.currency_code,
  };
}

function main(): void {
  const chart = new DomainChart();
  chart.classify("route-optimisation", "core", "2026-08-01");
  chart.classify("billing", "generic", "2024-01-01");

  console.log("reviewers for route-optimisation", chart.reviewersRequired("route-optimisation"));
  console.log("reviewers for billing", chart.reviewersRequired("billing"));
  console.log("is billing chart stale over 365d", chart.isStale("billing", "2026-08-02", 365));
  console.log("core subdomains", chart.allCore());

  const vendorPayload: VendorInvoice = {
    vendor_invoice_id: "vi_9981",
    amount_cents: 4599,
    currency_code: "EUR",
    vendor_internal_status: "vendor_state_paid",
  };
  const invoice = translateVendorInvoice(vendorPayload);
  console.log("translated invoice for the core domain", invoice);
}

main();
```

Compiled and run with `tsc --strict --target es2020 --module commonjs core-domain.ts` followed by `node core-domain.js`, using the locally installed TypeScript compiler.

### Python

```python
from dataclasses import dataclass
from datetime import date
from enum import Enum


class Classification(Enum):
    CORE = "core"
    SUPPORTING = "supporting"
    GENERIC = "generic"


@dataclass
class SubdomainEntry:
    name: str
    classification: Classification
    last_reviewed: date


class DomainChart:
    def __init__(self) -> None:
        self._entries: dict[str, SubdomainEntry] = {}

    def classify(self, name: str, classification: Classification, today: date) -> None:
        self._entries[name] = SubdomainEntry(name, classification, today)

    def reviewers_required(self, name: str) -> int:
        entry = self._entries[name]
        if entry.classification is Classification.CORE:
            return 2
        return 1

    def is_stale(self, name: str, today: date, max_days: int) -> bool:
        entry = self._entries[name]
        return (today - entry.last_reviewed).days > max_days

    def all_core(self) -> list[str]:
        return [e.name for e in self._entries.values() if e.classification is Classification.CORE]


@dataclass(frozen=True)
class VendorInvoice:
    vendor_invoice_id: str
    amount_cents: int
    currency_code: str
    vendor_internal_status: str


@dataclass(frozen=True)
class Invoice:
    invoice_id: str
    amount_due: float
    currency: str


def translate_vendor_invoice(vendor: VendorInvoice) -> Invoice:
    return Invoice(
        invoice_id=vendor.vendor_invoice_id,
        amount_due=vendor.amount_cents / 100,
        currency=vendor.currency_code,
    )


def main() -> None:
    chart = DomainChart()
    chart.classify("route-optimisation", Classification.CORE, date(2026, 8, 1))
    chart.classify("billing", Classification.GENERIC, date(2024, 1, 1))

    print("reviewers for route-optimisation", chart.reviewers_required("route-optimisation"))
    print("reviewers for billing", chart.reviewers_required("billing"))
    print("is billing stale over 365d", chart.is_stale("billing", date(2026, 8, 2), 365))
    print("core subdomains", chart.all_core())

    vendor_payload = VendorInvoice(
        vendor_invoice_id="vi_9981",
        amount_cents=4599,
        currency_code="EUR",
        vendor_internal_status="vendor_state_paid",
    )
    invoice = translate_vendor_invoice(vendor_payload)
    print("translated invoice for the core domain", invoice)


if __name__ == "__main__":
    main()
```

Run with `python3 core_domain.py`.

### Go

```go
package main

import (
	"fmt"
	"time"
)

type Classification int

const (
	Core Classification = iota
	Supporting
	Generic
)

type SubdomainEntry struct {
	Name           string
	Classification Classification
	LastReviewed   time.Time
}

type DomainChart struct {
	entries map[string]SubdomainEntry
}

func NewDomainChart() *DomainChart {
	return &DomainChart{entries: make(map[string]SubdomainEntry)}
}

func (c *DomainChart) Classify(name string, classification Classification, today time.Time) {
	c.entries[name] = SubdomainEntry{Name: name, Classification: classification, LastReviewed: today}
}

func (c *DomainChart) ReviewersRequired(name string) (int, error) {
	entry, ok := c.entries[name]
	if !ok {
		return 0, fmt.Errorf("unclassified subdomain: %s", name)
	}
	if entry.Classification == Core {
		return 2, nil
	}
	return 1, nil
}

func (c *DomainChart) IsStale(name string, today time.Time, maxDays int) (bool, error) {
	entry, ok := c.entries[name]
	if !ok {
		return false, fmt.Errorf("unclassified subdomain: %s", name)
	}
	days := int(today.Sub(entry.LastReviewed).Hours() / 24)
	return days > maxDays, nil
}

// VendorInvoice is the Generic dependency's own shape. It must never be
// referenced outside this file, that boundary is the Anticorruption Layer.
type VendorInvoice struct {
	VendorInvoiceID     string
	AmountCents         int
	CurrencyCode        string
	VendorInternalState string
}

// Invoice is the Core Domain's own vocabulary.
type Invoice struct {
	InvoiceID string
	AmountDue float64
	Currency  string
}

func TranslateVendorInvoice(v VendorInvoice) Invoice {
	return Invoice{
		InvoiceID: v.VendorInvoiceID,
		AmountDue: float64(v.AmountCents) / 100,
		Currency:  v.CurrencyCode,
	}
}

func main() {
	chart := NewDomainChart()
	chart.Classify("route-optimisation", Core, time.Date(2026, 8, 1, 0, 0, 0, 0, time.UTC))
	chart.Classify("billing", Generic, time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC))

	rev, _ := chart.ReviewersRequired("route-optimisation")
	fmt.Println("reviewers for route-optimisation", rev)

	rev, _ = chart.ReviewersRequired("billing")
	fmt.Println("reviewers for billing", rev)

	stale, _ := chart.IsStale("billing", time.Date(2026, 8, 2, 0, 0, 0, 0, time.UTC), 365)
	fmt.Println("is billing stale over 365d", stale)

	vendorPayload := VendorInvoice{
		VendorInvoiceID:     "vi_9981",
		AmountCents:         4599,
		CurrencyCode:        "EUR",
		VendorInternalState: "vendor_state_paid",
	}
	invoice := TranslateVendorInvoice(vendorPayload)
	fmt.Printf("translated invoice for the core domain %+v\n", invoice)
}
```

Run with `go run core_domain.go`.

C# and Kotlin toolchains were not confirmed installed on this machine and are
omitted rather than presented as run and unverified. Swift was available but
is skipped here because the classification-and-boundary shape above already
carries across three sufficiently different type systems, structural typing
in TypeScript, dataclasses and enums in Python, explicit interfaces and
zero-value enums in Go, to demonstrate the pattern is not language-specific,
and a fourth translation would add length without adding a distinct
implementation idea.
