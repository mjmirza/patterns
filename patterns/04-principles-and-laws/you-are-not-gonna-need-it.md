---
name: You Aren't Gonna Need It
slug: you-are-not-gonna-need-it
family: 04-principles-and-laws
category: Principle
aliases: [YAGNI, You Ain't Gonna Need It, "You're Not Gonna Need It"]
first_described: "Kent Beck and Chet Hendrickson, C3 project, 1996; Ron Jeffries, xprog.com, 1998; Jeffries, Anderson, Hendrickson, Extreme Programming Installed, 2001"
maturity: canonical
related: [keep-it-simple, do-not-repeat-yourself, single-responsibility-principle, open-closed-principle]
incompatible_with: []
verified: 2026-08-02
---

# You Aren't Gonna Need It

## 1. Name, aliases, and lineage

The canonical name is You Aren't Gonna Need It, almost always written as the
acronym YAGNI. Two spoken variants circulate in the wild with identical
meaning, "You Ain't Gonna Need It" and "You're Not Gonna Need It", and both
resolve to the same four-letter acronym, so the alias list treats them as the
same principle rather than as competing phrasings.

The origin sits inside Extreme Programming, on Chrysler's payroll system
project, universally known by its short name, C3, the project on which Kent
Beck, Ward Cunningham, and Ron Jeffries first assembled the practices that
became XP. Martin Fowler's own account of the origin, in his bliki entry on
the term, places the coinage inside a specific exchange between Beck and a
colleague. "The origin of the phrase is an early conversation between Kent
Beck and Chet Hendrickson on the C3 project. Chet came up to Kent with a
series of capabilities that the system would soon need, to each one Kent
replied you aren't going to need it" (Martin Fowler, "Yagni", bliki entry,
verified 2026-08-02, https://martinfowler.com/bliki/Yagni.html). Fowler
frames YAGNI as one expression of XP's Simple Design practice, and notes it
pushed hard against the late 1990s consensus that a design should be fully
planned before code is written.

Ron Jeffries put the same idea into print earliest as a dated article on his
own site, "You're NOT gonna need it!", dated 4 April 1998
(https://ronjeffries.com/xprog/articles/practices/pracnotneed/, verified
2026-08-02). The article's own argument for the principle names three costs
of building a capability before it is needed. it distracts attention from the
actual task, it spends time writing, reading, and maintaining code nobody
uses yet, and the anticipated need frequently never materializes at all,
which means the entire investment was wasted regardless of how well it was
built. The article states its practical form plainly. build only the getter
you need today, not the setter or the second getter you expect to need
later.

The principle reached a wider audience in book form through *Extreme
Programming Installed*, by Ronald E. Jeffries, Ann Anderson, and Chet
Hendrickson, Addison-Wesley, 2001, which the Wikipedia entry on the term
cites at page 190 as calling YAGNI one of XP's most quoted slogans
(https://en.wikipedia.org/wiki/You_aren%27t_gonna_need_it, verified
2026-08-02). Kent Beck himself used the alternate spelling "you aren't going
to need it" a few years earlier in *Refactoring. Improving the Design of
Existing Code*, co-written with Martin Fowler, Addison-Wesley, 1999, page
68, in a passage about removing speculative flexibility discovered during
refactoring, and the same Wikipedia entry cites that page as an early print
appearance of the phrase under its alternate wording.

One naming confusion worth resolving up front. YAGNI is not a synonym for
"write less code" or for the general instinct toward simplicity. It is a
narrower and more specific claim, aimed at a particular decision point, add a
capability the code does not use today because you expect to need it later,
or do not add it. Keep It Simple is the broader sibling principle about the
shape of a solution once you have decided to build it, see dimension 13 for
how the two divide the work.

## 2. Problem and context

A developer sits inside a piece of work that is genuinely needed today, and
partway through, notices a plausible future requirement. The database schema
will probably need a `tenant_id` column once the product goes multi-tenant.
The API will probably need pagination once traffic grows. The configuration
loader will probably need a plugin mechanism once a second data source
shows up. Each observation is often correct as a prediction, and that is
exactly what makes the temptation dangerous, because a correct prediction
about the future still does not tell you the cost of building for it now is
lower than the cost of building for it when it actually arrives.

The situation that gives rise to the pull toward speculative work has three
recognisable ingredients. First, the developer currently holds the richest
mental model of the domain they will ever have at this moment, so adding the
flexible version feels cheap right now, cheaper than it will feel to a
different developer picking the code up in eight months. Second, the cost of
building the speculative capability is visible and immediate, a few extra
hours today, while the cost of NOT building it is invisible and deferred, a
possible future rewrite that may or may not ever happen. Humans systematically
discount deferred, uncertain costs against immediate, certain ones, which
biases the decision toward building early. Third, "good engineering" is
culturally associated with anticipation, foresight, and building things that
last, so declining to build the general version can feel, wrongly, like
cutting a corner rather than like making a deliberate trade.

YAGNI names the discipline of resisting this pull. it is a decision rule
applied at the exact moment a developer is tempted to generalize, abstract,
or extend beyond the concrete requirement in front of them, and it says.
build the thing the current, real requirement needs, and no more, deferring
every other capability until a real requirement for it exists.

The context in which the rule holds is load-bearing and is the subject of
dimension 4. YAGNI is a statement about SPECULATIVE work under conditions
where change is cheap to make later, not a blanket instruction to build the
smallest possible thing regardless of what changing it later will cost.

## 3. Forces

- **Cost of change over time.** Central to the whole principle. YAGNI is
  favoured wherever the cost of adding a capability later, when it is
  actually needed, is roughly comparable to or cheaper than the cost of
  adding it now on a guess. It becomes the wrong call wherever the cost of
  change rises sharply after a decision point, for example a public API
  contract, a wire format, or a stored data schema consumed by other teams,
  because at that point retrofitting a capability after the fact costs far
  more than including it at the one moment it was cheap. Kent Beck's own
  later writing on this exact trade-off is discussed in dimension 4.
- **Cognitive load, favoured.** Every branch, parameter, hook, or abstraction
  layer that exists to serve a future need that has not arrived yet is a
  thing every future reader must understand, maintain, and reason about,
  whether or not the future need ever materializes. YAGNI trades away
  hypothetical future convenience for present-day readability.
- **Certainty of the requirement, decisive.** The forecast that a capability
  will be needed is, by construction, less certain than the requirement in
  front of you today. A prediction with high confidence and low cost of being
  wrong tilts toward building now. A prediction with low confidence, or a
  high cost if the guess turns out wrong in shape, tilts hard toward YAGNI.
- **Delivery speed, favoured.** Every hour spent on a capability nobody is
  asking for today is an hour not spent delivering the thing somebody IS
  asking for today. In a context of genuine uncertainty about what the
  product needs next, shipping the real thing sooner and learning from real
  usage outperforms guessing further ahead on a longer feedback loop.
- **Robustness against a wrong guess, favoured.** A speculative abstraction is
  built against an imagined future requirement, and imagined requirements are
  frequently wrong in shape even when they are right in existence. Code
  written for the actual, arrived requirement is shaped correctly by
  definition, because the requirement is real and known rather than guessed.
- **Optionality and irreversible investment, sacrificed.** This is the honest
  cost YAGNI pays. In domains where the cost curve for retrofitting a
  capability is genuinely steep, foundational architecture decisions, data
  model choices with long-lived stored data, cryptographic algorithm agility,
  regulatory or accessibility requirements known to be coming, deferring
  the capability can be materially more expensive than including it early,
  and YAGNI applied blindly there produces expensive rework instead of saving
  effort. This is precisely why dimension 4 exists as a genuine, load-bearing
  non-applicability list rather than a formality.
- **Team trust and morale, situational.** A team disciplined about YAGNI
  spends its energy on what customers currently need, which tends to build
  trust with product leadership that engineering time maps to visible
  value. The same discipline, applied without judgement to a load-bearing
  architectural seam, produces a rewrite six months later that erodes exactly
  that trust when the people watching see the team redoing the same work.

YAGNI is not free. It trades long-run optionality for short-run focus and
low waste, and it wins that trade specifically in the conditions named in
dimension 4, not universally.

## 4. Applicability and non-applicability

Apply YAGNI when the following hold.

- The capability under consideration is not required by any current, real
  requirement, ticket, contract, or test. It exists only because someone can
  imagine wanting it.
- The cost of adding the capability later, once a real requirement for it
  exists, is comparable to or lower than the cost of adding it now. Internal
  application code behind a stable interface, most business logic, most UI
  behaviour, and most internal service implementation detail fits this
  description.
- The team has the ability to change the relevant code again later without
  friction, meaning automated tests exist, deployment is not a rare or risky
  event, and the code is not consumed by external, uncoordinated parties who
  would break if its shape changed.
- The anticipated future requirement is a guess about business direction, not
  a stated, scheduled, contracted requirement with a known delivery date.
- The developer is choosing between a narrow, concrete implementation and a
  generalized one built to also cover an imagined second case, where only
  one case currently exists.

Do NOT apply YAGNI, or apply it with real caution, in these cases, and the
reason for each carve-out matters more than the rule itself.

- **Public API and wire-format contracts.** Once a shape ships and another
  team, another company, or another process consumes it, changing that shape
  later is no longer cheap, it is a breaking change with a migration, a
  deprecation window, and a coordination cost across parties who do not
  report to you. Sam Newman makes exactly this point about service
  boundaries in *Building Microservices*, 2nd edition, O'Reilly, 2021,
  arguing that the cost asymmetry between changing an internal
  implementation and changing a published interface contract is the central
  fact that should govern how much upfront thought a public boundary
  deserves, precisely because a boundary crossed by other teams cannot be
  refactored the way private code can (verified against the publisher's own
  description of the book's boundary-design chapters, O'Reilly Media,
  https://www.oreilly.com/library/view/building-microservices-2nd/9781492034018/,
  verified 2026-08-02, description-level claim only, not a page-cited quote).
- **Stored data schemas with existing production data.** A missing column can
  be added to code in minutes. A missing column in a table with a billion
  rows of existing data, or a data model that at bottom cannot represent
  a requirement that has now genuinely arrived, is a migration project. Where
  a data model change is known to be steep-cost, YAGNI on the current
  requirement is still correct, but the schema's EXTENSIBILITY, not its
  speculative extra columns, deserves early attention.
- **Regulatory, accessibility, security, and compliance requirements that are
  known to be coming, not merely imagined.** A requirement stated in a
  signed contract, an approved compliance plan with a fixed date, or a
  passed law with a known effective date is not speculative. it is a real,
  scheduled requirement, and YAGNI does not apply to it merely because its
  effective date is in the future. The rule targets capabilities nobody has
  actually asked for, not capabilities whose delivery has simply been
  scheduled.
- **The one-time cost of an interface seam is genuinely cheap relative to its
  option value.** Defining a narrow interface around a third-party
  dependency, even before a second implementation exists, is frequently
  argued as an exception because the interface itself costs almost nothing
  and materially lowers the cost of the future change it is hedging against.
  This is the case Martin Fowler discusses when he distinguishes a cheap,
  narrow seam from an actual second, unneeded implementation behind it, in
  the same bliki entry cited in dimension 1. building the interface is close
  to free, building a second, currently unused implementation behind it is
  the actual YAGNI violation.
- **Kent Beck's own later qualification, on tests specifically.** Beck has
  written, discussing test-driven development, that he applies YAGNI far
  more loosely to test code than to production code, because a test that
  covers a case not yet exercised by production code can still catch a real
  regression cheaply, whereas production code built for an unused case
  cannot be exercised or validated by anything (this is Beck's own stated
  practice as summarised in discussion of TDD and YAGNI on the C2 wiki, a
  community-maintained record of XP practitioner discussion,
  http://wiki.c2.com/?YouArentGonnaNeedIt, verified 2026-08-02, cited here as
  a record of practitioner discussion, not as a primary authored source).
- **Cross-cutting concerns with a known, near-certain near-term arrival, such
  as internationalization on a product already committed to a second
  market.** The line between "imagined" and "near-certain and scheduled" is
  the entire judgement call YAGNI asks a team to make honestly, and teams
  that resolve every ambiguous case toward "build it now, to be safe" have
  simply opted out of the principle while claiming to follow it.

## 5. Structure

YAGNI is a decision principle, not a structural design pattern, so it has no
class diagram of participants in the sense a Gang of Four pattern does. Its
structure is procedural. it names a decision point, the criterion applied at
that point, and the two paths that follow.

- **The decision point.** The moment, during design or implementation, when a
  developer notices that a broader, more flexible, or more general version of
  the current piece of code is possible, and that version would also cover a
  case not currently required.
- **The current, real requirement.** The concrete, present need that
  motivated the work in the first place, verifiable against a ticket, a
  test, a stated user story, or an existing caller.
- **The imagined future requirement.** The capability under consideration
  that no current requirement, test, or caller actually needs.
- **The criterion.** Is the imagined future requirement backed by a real,
  scheduled need, or is it a guess. Is the future cost of adding it, once
  real, comparable to or cheaper than building it now.
- **The two resulting paths.** Build only what the current requirement needs,
  deferring the rest, versus build the broader version now.

## 6. ASCII structure diagram

```
                +-------------------------------+
                |     Current, real requirement  |
                |  (ticket, test, actual caller)  |
                +---------------+-----------------+
                                |
                                v
                +-------------------------------+
                |        Decision point           |
                |  "should this also handle X,    |
                |   which nothing needs yet?"     |
                +---------------+-----------------+
                                |
                 no real, near-term need for X
                                |
              +-----------------+------------------+
              |                                     |
              v                                     v
   +---------------------+              +--------------------------+
   |   Apply YAGNI        |              |  Exception applies       |
   |   Build only what    |              |  (dim. 4): public API,   |
   |   the real need      |              |  stored schema, known    |
   |   requires. Defer X. |              |  scheduled requirement   |
   +----------+-----------+              +-------------+------------+
              |                                        |
              v                                        v
   +---------------------+              +--------------------------+
   |  X arrives later     |              |  Build for X now,        |
   |  as a REAL           |              |  cost-justified by the   |
   |  requirement.        |              |  steep future cost of    |
   |  Build it then,      |              |  retrofitting.           |
   |  shaped by real       |             +--------------------------+
   |  usage, not guesses. |
   +---------------------+
```

## 7. Dynamics

YAGNI has no runtime behaviour, because it governs what code is written, not
how written code executes. What it does have is a repeatable decision
sequence a developer or a code reviewer runs at design time, and a longer
feedback loop across a project's lifetime that either validates or
invalidates each past YAGNI call.

```
Design-time sequence, run at each decision point:

  Developer          Code / ticket           Reviewer (later, in review)
     |                     |                          |
     |-- notices possible  |                          |
     |   generalization -->|                          |
     |                     |                          |
     |-- checks: does a    |                          |
     |   real requirement  |                          |
     |   need this NOW? -->|                          |
     |                     |                          |
     |   [no real need]    |                          |
     |-- checks: is this   |                          |
     |   one of the        |                          |
     |   dim. 4 exceptions?|                          |
     |                     |                          |
     |   [not an exception]|                          |
     |-- writes the narrow,|                          |
     |   concrete version  |                          |
     |   only ------------>|                          |
     |                     |-- diff reviewed -------->|
     |                     |                          |-- checks for
     |                     |                          |   unused params,
     |                     |                          |   unreachable
     |                     |                          |   branches, dead
     |                     |                          |   config knobs
     |                     |                          |
     |<----------------------------------------------- feedback:
     |                                                  "this branch
     |                                                   has no caller,
     |                                                   defer it"


Project-lifetime feedback loop, across many decision points over time:

   T0: real requirement A ships. Speculative capability B declined (YAGNI).
   T1: real requirement C ships. Speculative capability D declined (YAGNI).
   T2: requirement B finally becomes real.
       -> built now, shaped by the ACTUAL shape B turned out to need,
          which frequently differs from what was imagined at T0.
   T3: requirement D never arrives.
       -> the YAGNI call at T1 saved the entire cost of D, permanently.

   The loop only closes correctly if refactoring, at T2, is genuinely cheap.
   That precondition is the subject of dimension 11.
```

## 8. Implementation variants

**The literal form, refusing an added parameter or branch.** The narrowest
and most common instance. a function is written to handle the one case a
caller needs, with no extra parameter, flag, or branch added to also cover a
second, currently nonexistent caller. This is the shape of the code examples
in this entry.

**YAGNI applied to abstraction, refusing an interface with one
implementation.** A team declines to introduce an interface, a plugin
registry, or a strategy hierarchy when exactly one concrete implementation
exists and no second is currently required, deferring the abstraction until
a genuine second implementation shows up and the correct shape of the
abstraction is visible from two real cases rather than guessed from one.
This is the variant most closely paired with Rule of Three thinking, see
dimension 13.

**YAGNI applied to configuration, refusing a config knob nobody has asked
to turn.** Rather than exposing a setting because it might one day need to
be tunable, the value is hardcoded or set as a private constant until an
actual, real need to vary it in a specific way appears, at which point the
knob is added with the shape that real need actually requires.

**YAGNI applied to schema, refusing a speculative column or field.** A
database table or a serialized message is not given fields for data the
system does not yet capture or use, because an unused, always-null column is
a maintenance and data-quality burden with no offsetting benefit, and adding
a real column later, before that column has any production data in it, is
cheap.

**YAGNI applied to test coverage, the qualified variant.** As discussed in
dimension 4, several XP practitioners, including Beck, apply the principle
more loosely here, treating a test for an edge case not yet exercised in
production as a cheap insurance policy rather than as a YAGNI violation,
because an unexercised test still costs little and still catches a real
regression the day the edge case does arrive.

**YAGNI as a code review heuristic rather than an authoring rule.** In many
teams the principle shows up not as something the original author applies
silently, but as a specific reviewer question asked of a diff. "is any of
this exercised by a current caller or test, or is it here for something we
expect to need." This variant treats YAGNI as a shared team norm enforced
socially at review time rather than as an individual discipline, and it is
the shape most compatible with the observability signals in dimension 16.

**The narrow-seam exception as a deliberate, named variant.** Rather than
treating every abstraction as a violation, some teams explicitly permit one
class of exception, a narrow interface around an external dependency, added
even with a single implementation, on the argument that the interface itself
costs almost nothing and buys real optionality against a dependency the team
does not control. This is the exact seam Fowler distinguishes in his bliki
entry, discussed in dimension 4, and it is a deliberate, bounded relaxation
of the rule rather than an abandonment of it.

## 9. Known production uses

**Segment's move from microservices back to a monolith, 2018.** In "Goodbye
Microservices", Segment engineer Alexandra Noonan describes how Segment
built out more than 140 separate microservices, one per source-destination
integration pair, anticipating a scaling need for independent deployability
and isolation that the actual failure modes in production did not match, and
consolidated the system back into a single monolithic service once the
maintenance and on-call cost of the anticipatory architecture outweighed the
benefit it was built to provide (Segment Engineering Blog, "Goodbye
Microservices. From 100s of problem children to 1 superstar", 10 July 2018,
https://segment.com/blog/goodbye-microservices/, verified 2026-08-02). The
case is widely cited in software architecture discussion as a named,
concrete instance of a team paying for anticipated scale before the scale
existed, and later reverting once the real requirements were known.

**Basecamp's Majestic Monolith architecture stance.** David Heinemeier
Hansson, creator of Ruby on Rails and a founder of Basecamp, has argued
publicly and repeatedly that Basecamp keeps its application as a single Ruby
on Rails codebase rather than splitting it into services in anticipation of
scale or team growth the company does not currently have, explicitly framing
the decision as declining complexity the product does not yet need
(David Heinemeier Hansson, "The Majestic Monolith", Signal v. Noise, Basecamp
engineering blog, 29 February 2016,
https://signalvnoise.com/svn3/the-majestic-monolith/, verified 2026-08-02).
Ruby on Rails is one of the most widely deployed web application frameworks
in production use, so this is a named, first-party architectural stance from
the team building both the framework and a large commercial product on top
of it.

**Google's internal engineering guidance on speculative generality.** The
publicly released *Google Engineering Practices Documentation*, in its code
review guidance on design, instructs reviewers to look for code that does
more than the change actually requires, stating that a reviewer should be
"suspicious of design docs" or diffs that solve a more general problem than
the one at hand, and directing that speculative flexibility not currently
exercised by real functionality should generally be flagged in review
(Google, "Google Engineering Practices Documentation, How to do a code
review, What to look for in a code review", verified 2026-08-02,
https://google.github.io/eng-practices/review/reviewer/looking-for.html).
This is a first-party, named engineering organisation's own published review
standard, applied at the scale of one of the largest software codebases in
production use.

**Extreme Programming, as practiced on Chrysler's C3 payroll project,
1996 to 1999.** YAGNI's own origin project is
itself a named production use, since it was not a hypothetical example but a
real payroll processing system for a real employer, built under the XP
practices, including YAGNI, that were being actively developed on that
engagement (Kent Beck, *Extreme Programming Explained. Embrace Change*, 1st
edition, Addison-Wesley, 1999, described throughout as drawn from the C3
project experience; corroborated by Fowler's account cited in dimension 1).

## 10. Consequences

Positive.

- Less code exists overall, which means less code to read, less code to
  test, less code to keep correct across future changes, and less surface
  area for a bug to hide in, since unused, speculative code paths are a
  documented source of bugs that are exercised for the first time in
  production rather than in development.
- Delivery of the currently needed capability is faster, because no time is
  spent building, documenting, or testing a capability nobody is currently
  asking for.
- When the deferred capability finally does become a real requirement, it is
  built against the ACTUAL shape of that requirement rather than against an
  earlier guess, which frequently produces a better-fitting design than the
  speculative version would have been, because real usage reveals shape that
  imagination does not.
- Reduces the cognitive load on every future reader of the code, since there
  are no unused branches, unexercised configuration knobs, or dead
  abstraction layers to reason about while trying to understand what the
  system actually does.
- Redirects engineering attention toward the requirements a team can verify
  are real, which tends to align engineering effort more closely with
  delivered, observable value.

Negative.

- When applied to a genuinely load-bearing seam, a public contract, a stored
  schema, or a known-but-not-yet-scheduled regulatory requirement, deferring
  the capability produces a materially more expensive retrofit later, and the
  savings from not building it early are smaller than the cost paid when it
  finally arrives.
- A team that treats YAGNI as a blanket rule rather than a judgement applied
  at a decision point tends to underinvest in cheap, narrow seams, such as an
  interface around an external dependency, that would have bought real
  optionality at near-zero cost.
- Relying on YAGNI without genuinely cheap change later, meaning without
  automated tests, without frequent, low-risk deployment, and without a
  codebase that is actually easy to modify, converts deferred work into
  accumulated technical debt rather than into saved effort, because the
  precondition the principle depends on, cheap future change, was never true.
- Can be used as a rhetorical shield for under-engineering rather than as a
  genuine judgement call, where "we don't need that yet" is deployed to avoid
  a hard design conversation rather than because the requirement is actually
  speculative.
- Discourages exploratory or platform-style investment that pays off only
  over a longer timeframe than any single sprint or quarter can justify on its
  own, which can be a genuine cost in an organisation whose planning window
  is itself too short.

## 11. Failure modes and misuse

**YAGNI without safety nets, the precondition failure.** Symptom. deferred
work accumulates as a rewrite project rather than as an easy later addition,
each new "add it right now" change takes far longer than the original
estimate suggested, and the team dreads touching the module the deferred
capability eventually landed in. Cause. YAGNI's entire justification assumes
future change is cheap, and the team applying it has no automated test
suite, deploys rarely and riskily, or has let the codebase's structure decay,
so the future change the principle deferred is not actually cheap when it
arrives. Fix. treat automated testing and frequent, low-risk deployment as
prerequisites for applying YAGNI aggressively, not as optional extras, and
where those prerequisites are missing, build them before leaning harder on
deferral.

**YAGNI misapplied to a load-bearing seam.** Symptom. a public API version
bump, a painful data migration on a large production table, or a breaking
change communicated to external integrators, all traced back to a deferred
decision that "we'll add that when we need it" made on something that, once
shipped, other parties depended on. Cause. failing to recognise that the
decision point sat on one of the dimension 4 exceptions, a boundary where
retrofitting is expensive because other parties, not only the original team,
now depend on the shape. Fix. explicitly classify a decision as
internal-and-cheap-to-change versus external-or-stored-and-expensive-to-change
before applying YAGNI, and treat the second category with real design
attention up front regardless of current, narrow requirements.

**YAGNI as an excuse to avoid a hard design conversation.** Symptom. a
recurring pattern in code review where "we don't need that yet" is invoked
to shut down a legitimate discussion about a near-certain, scheduled future
requirement, such as an already-signed contract for a second market, rather
than about a genuinely speculative one. Cause. the principle is being applied
as a rhetorical stop rather than as an honest judgement of whether the future
requirement is real and scheduled or merely imagined. Fix. require the
person invoking YAGNI to name specifically what evidence tells them the
future requirement is not real, rather than accepting the invocation on its
own authority, and separate "not currently required" from "not currently
scheduled or known".

**Speculative generality shipped anyway, under a different name.** Symptom.
a configuration file with dozens of settings that have never been changed
from their default value in any deployment, or a plugin interface with
exactly one plugin that has ever existed. Cause. the team accepted the
narrow-seam exception discussed in dimension 4 far more broadly than its
justification supports, building not only a cheap interface but a full
generalized mechanism behind it, on the same "to be safe" reasoning YAGNI
exists to prevent. Fix. periodically audit configuration surfaces and
extension points for ones that have never been exercised by more than a
single value or a single implementation, and collapse them back to the
concrete case, per the refactoring path in dimension 14.

**Confusing YAGNI with refusing necessary design work.** Symptom. a codebase
where every module is tightly coupled to every other, with no seams anywhere,
justified by "we don't build abstractions we don't need yet", and a change to
one small thing now requires touching a dozen files. Cause. mistaking YAGNI,
a rule about not building UNUSED capabilities, for a rule against basic
structural design, such as separating concerns or naming a clear interface
boundary for code that genuinely has more than one caller today. Fix.
recognise that YAGNI governs capabilities nobody currently uses, not the
ordinary discipline of a well-factored design for capabilities that ARE
currently in use, and apply Keep It Simple and Single Responsibility, see
dimension 13, to that second concern separately.

**Under-resourced refactoring makes the deferred work permanent.** Symptom.
the deferred capability's "we'll build it properly when we actually need it"
moment arrives, and the team, under delivery pressure, instead bolts the new
requirement onto the existing narrow implementation with a special case
rather than generalizing it correctly, producing exactly the accreted
complexity YAGNI was meant to avoid, only arrived later and under worse
conditions. Cause. treating YAGNI as a one-time decision rather than as
paired with an obligation to actually do the generalizing work honestly once
the second real case arrives. Fix. when a second real requirement does
arrive, budget the time to properly generalize from the first concrete
implementation rather than patching around it, which is the Rule of Three
discipline discussed in dimension 13.

## 12. Trade-off matrix

Compared against named alternative stances a team could take at the same
decision point.

| Force | YAGNI (defer until real need) | Anticipatory design (build for the guessed future now) | Rule of Three (wait for a third real case before generalizing) | Design by Contract upfront (specify the full interface before any implementation) |
|---|---|---|---|---|
| Cost paid when the guess is wrong | Low. nothing was built for it | High. the speculative work is wasted | Low, same as YAGNI, deferred one case further | High, the contract itself may need renegotiation |
| Cost paid when the guess is right | Higher later, must build it then | Lower, already exists | Slightly higher than YAGNI, waits for a third case first | Lower for the specified capability, if the guess matched |
| Design quality of the eventual capability | High, shaped by real, arrived usage | Variable, shaped by imagination | High, shaped by two or more real cases, often better than YAGNI's single-case redo | Variable, depends entirely on the quality of the upfront guess |
| Cognitive load in the meantime | Low, nothing unused to read | Higher, unused code and knobs exist | Low, same as YAGNI until the second real case | Higher, a contract exists that nothing fully exercises yet |
| Suitability for public, external contracts | Poor fit, per dimension 4 | Reasonable fit, if the guess about the contract shape is well-researched | Poor fit, waiting for a third caller is not possible for a contract other teams depend on immediately | Strong fit, this is the case Design by Contract upfront suits best |
| Suitability for internal, easily-changed code | Strong fit, the default case | Poor fit, pays cost for no offsetting benefit | Strong fit, a common refinement of YAGNI for the abstraction-timing question specifically | Poor fit, overkill for code that changes freely |
| Team discipline required to execute well | Requires honest classification of real versus imagined need | Requires accurate prediction of the future, a harder skill | Requires patience to wait for the third case rather than generalizing after the second | Requires strong upfront domain knowledge and sponsor access |

Reading of the table. YAGNI and Rule of Three sit close together and are
often applied together, YAGNI deciding whether to build a capability at all,
Rule of Three deciding when an already-necessary capability should be
generalized rather than duplicated. Anticipatory design and upfront Design by
Contract both trade YAGNI's low cost-of-being-wrong for a shot at a lower
cost-of-being-right, and that trade is exactly the one dimension 4 says is
worth making at a genuinely load-bearing, expensive-to-change seam, and not
worth making anywhere else.

## 13. Related and incompatible patterns

- **Keep It Simple.** The closest sibling and frequently conflated with
  YAGNI, but the two answer different questions. Keep It Simple governs the
  shape of a solution to a problem you have already decided to solve. YAGNI
  governs whether you should be solving a given problem at all, right now.
  Applying Keep It Simple to a piece of speculative work still leaves the
  work speculative, YAGNI is the prior question of whether it should exist.
- **Do Not Repeat Yourself.** In active, healthy tension with YAGNI rather
  than simply complementary. DRY pushes toward extracting a shared
  abstraction as soon as duplication appears, while YAGNI pushes toward
  waiting until a real, current need for that abstraction exists. The Rule of
  Three heuristic, generally attributed to the same XP-era practitioner
  community and popularised in discussion of *The Pragmatic Programmer* by
  Andrew Hunt and David Thomas, Addison-Wesley, 1999, is the common
  resolution. tolerate the second duplicate instance, and only extract a
  shared abstraction once a genuine third real case confirms the
  abstraction's correct shape, which satisfies both principles by deferring
  the abstraction, YAGNI, until it is validated by real, repeated need,
  DRY.
- **Single Responsibility Principle and Open Closed Principle.** These
  govern how a module should be shaped once it exists and has more than one
  reason to exist. YAGNI is upstream of both. it decides whether a
  capability that would need a responsibility or an extension point should
  be built at all. A module correctly following Single Responsibility for
  capabilities it actually has is not in tension with YAGNI, a module given
  an extension point for a variation nobody has asked for, in the name of
  Open Closed Principle, usually is the exact violation YAGNI targets, since
  Open Closed applies to code that changes for known reasons, not code kept
  open for imagined ones.
- **Speculative generality, the code smell.** The direct negative expression
  of a YAGNI violation once it has been built. Martin Fowler and Kent Beck's
  own catalog of code smells in *Refactoring. Improving the Design of
  Existing Code*, Addison-Wesley, 1999, names unnecessary delegation, unused
  parameters, and abstract classes with a single concrete subclass as
  symptoms of exactly this smell, and its corrective refactorings, discussed
  in dimension 14, are the standard path back out of a YAGNI violation once
  one has been shipped.
- **Test-Driven Development.** Composes closely and is a common pairing.
  Writing the test first before writing the implementation naturally
  produces the narrowest implementation that satisfies a real, currently
  specified requirement, which is close to a mechanical enforcement of
  YAGNI at the level of individual functions, since code with no failing
  test demanding it has, by construction, no justification for existing yet.
- **Big Design Up Front, incompatible in its strong form.** The traditional
  waterfall-era practice of fully specifying a system's architecture before
  writing code is the direct historical opposite of YAGNI's stance, and the
  tension between the two is part of what made YAGNI a notable, deliberately
  provocative claim when XP introduced it in the late 1990s, per Fowler's
  account in dimension 1. The two are not simply incompatible in every case,
  see dimension 4's contract and schema exceptions, where a bounded amount of
  upfront design genuinely earns its cost.

## 14. Refactoring path in and out

Introducing the discipline into a team or a codebase that does not currently
practice it.

1. Pick one active pull request or diff currently in review and ask, of each
   parameter, branch, or configuration option it adds, whether a current,
   real caller, test, or ticket actually exercises it today.
2. For anything found that has no current exerciser, remove it from the diff
   and note, in the review comment, what the concrete signal would be that
   would justify adding it back, so the deferral is a documented decision
   rather than a silent one.
3. Extend the same question to existing code opportunistically, when it is
   already being touched for another reason, rather than as a standalone
   sweep. an unused configuration knob or an interface with a single
   implementation, discovered while working nearby, is collapsed at that
   point using the refactorings below.
4. Make the review question durable by writing it into the team's code
   review checklist, so it applies to every future diff rather than only to
   the one that prompted adoption.
5. Pair the practice with the prerequisite named in dimension 11, automated
   tests and low-risk, frequent deployment, since without those the later
   half of the discipline, cheaply adding the deferred capability when it
   becomes real, will not actually be cheap.

The corrective refactorings, when a speculative capability has already been
shipped and is confirmed to have no real exerciser, are named directly in
Fowler and Beck's *Refactoring* catalog. **Collapse Hierarchy**, for an
abstract class with exactly one concrete subclass and no plan for a second.
**Inline Class**, for an interface or wrapper introduced for a flexibility
nothing uses. **Remove Parameter**, for a function parameter no caller ever
varies. **Remove Dead Code**, for a branch, feature flag, or configuration
path with zero live callers. Each of these, run in the direction away from
the speculative generality and back toward the concrete case actually in
use, is the mechanical undo of a YAGNI violation once one is caught. See the
refactoring family entries for the step-by-step mechanics of each.

Removing the discipline, or rather, recognising when to relax it at a
specific decision point, per dimension 4.

1. Identify whether the decision point sits on a boundary crossed by another
   team, another company, or stored production data, rather than on purely
   internal, easily-changed code.
2. Confirm the future requirement is scheduled, contracted, or otherwise
   confirmed rather than merely plausible, using the test from dimension 11,
   "what specific evidence says this is real."
3. If both hold, treat the decision as one of the genuine exceptions, invest
   the design time up front, and document why, so a future reviewer applying
   the general YAGNI heuristic does not mistakenly flag or unwind a
   deliberate, justified exception.

## 15. Testing and verification

YAGNI itself is a design-time decision rather than a runtime behaviour, so it
is not directly unit-testable the way a class's behaviour is. What can be
verified is whether the discipline is actually being followed, and testing
plays two distinct roles here.

Testing as the enabling precondition. As covered in dimension 11, YAGNI's
entire justification rests on future change being cheap, and a codebase with
strong automated test coverage is what makes a later change cheap and safe.
A team without adequate test coverage that is also applying YAGNI
aggressively is not actually practicing the principle correctly, it is
accumulating risk while believing it is saving effort, because the safety
net the principle assumes does not exist.

Testing as a verification mechanism for the principle's own application.

- **Dead code and unreachable branch coverage.** Running a code coverage
  tool and treating a persistently zero-hit branch, function, or
  configuration path as a signal, not that the test suite is incomplete, but
  that the code itself may be a YAGNI violation nothing exercises. Coverage
  tooling here is repurposed as a speculative-generality detector rather than
  as a measure of test thoroughness.
- **Static analysis for unused code.** Linters and static analysers that flag
  unused parameters, unused private methods, unreachable code, and unused
  exports serve the same purpose mechanically, catching the concrete
  artifacts of a YAGNI violation, an unused parameter added for an imagined
  future caller, an unused method exposed for an imagined future consumer.
- **Test-Driven Development as a forcing function.** Writing a failing test
  first, then writing only the code that makes it pass, structurally prevents
  code with no current, verified need from being written in the first place,
  since code with nothing demanding it cannot be written under a strict
  red-green-refactor discipline.
- **Reviewing configuration surfaces for exercised values.** For a
  configuration knob or feature flag, checking, across the team's actual
  deployed environments, whether the value has ever been set to anything
  other than its default is a practical, low-cost audit that surfaces
  speculative generality shipped as configuration rather than as code.

What becomes harder because of the principle, honestly stated. a test
suite built strictly under YAGNI covers only currently real requirements,
which means it provides no safety net against a future requirement that has
not yet been anticipated by anyone, code or test. This is not a flaw
specific to YAGNI so much as an honest acknowledgement that no test suite
can cover a requirement nobody has thought of yet, and it is one more reason
the boundary and schema exceptions in dimension 4 receive real design and
test attention up front rather than being deferred along with everything
else.

## 16. Observability signals

YAGNI is a design-time principle, so its observability signals are mostly
static, drawn from the codebase itself, its review history, and its
configuration, rather than from a running system's telemetry. This dimension
is largely engineering judgement about what to look for, not a sourced fact.

What to look for as evidence the discipline is being followed.

- A low or falling ratio of unused-to-total code paths, measured by coverage
  tooling over time, as a proxy for how much speculative capability the team
  is carrying.
- Configuration and feature-flag surfaces where the great majority of values
  in production match the shipped default, indicating the flexibility exists
  because it was actually needed to vary, not because it was added
  speculatively.
- Pull request review comments that explicitly invoke a "do we need this
  yet" question and result in a smaller diff, which is a direct, observable
  trace of the principle being applied in practice rather than only claimed.
- A short average lifespan between a capability being added and its first
  real exercise by a caller or a user, which suggests capabilities are being
  built close to the point of actual need rather than well ahead of it.

What a codebase carrying an unmanaged YAGNI failure looks like.

- A steadily growing count of configuration options, interfaces with a
  single implementation, or abstract base classes with a single concrete
  subclass, none of which correspond to any change ever actually made in
  that dimension.
- A widening gap between code coverage percentage and the fraction of the
  codebase actually reachable from a real, current entry point, which points
  at dead or speculative branches accumulating faster than they are pruned.
- An increasing share of pull requests whose diff is mostly changes to code
  that has no test exercising it, and no caller reachable from a real
  user-facing entry point.
- Incident postmortems that repeatedly cite "we had to migrate this in an
  emergency" for a boundary that was, in fact, one of the dimension 4
  exceptions, public contract or stored schema, that was mistakenly treated
  as ordinary internal code and deferred anyway. this is the pattern that
  most directly indicates the exception list is being misapplied rather than
  the general rule.

## 17. Security and privacy implications

YAGNI's implications for security are real, and they run in both directions,
so neither should be overstated. This dimension is analytical judgement, not
a sourced claim about a specific incident.

The favourable direction. unbuilt code cannot be exploited. A capability,
endpoint, configuration option, or administrative code path that does not
exist because it was correctly deferred under YAGNI is, by definition, not
part of the attack surface. This is a genuine, mechanical security benefit
of the principle applied to code specifically. speculative generality
frequently manifests as an extra, rarely-used code path, and rarely-used
code paths are documented in security literature as disproportionately
likely to carry vulnerabilities, precisely because they receive less
scrutiny, less testing, and less real-world exercise than the paths a system
actually uses every day. A YAGNI-disciplined codebase has fewer of these
low-scrutiny paths to begin with.

The unfavourable direction, and the sharper one. security and privacy
requirements are a recurring example of a category that gets mistakenly
treated as speculative when it is not. A team that defers input validation,
authentication checks, rate limiting, or data-retention controls on the
reasoning that "we don't have that threat yet" is very often misapplying
YAGNI to a requirement that is not actually optional or future, it is a
present, structural requirement of handling untrusted input or personal data
at all, simply one that has not yet been exercised by an actual attacker or
an actual audit. This is precisely the misapplication named in dimension 4,
treating a real, known-but-not-yet-triggered requirement as a merely
speculative one, and it is one of the most consequential places that
misapplication can occur, because the cost of being wrong is not a rewrite,
it is a breach or a compliance failure.

The practical resolution most security-conscious teams reach is to treat a
class of security and privacy controls, input validation and output
encoding at trust boundaries, authentication and authorization checks,
encryption of data classified as sensitive, and logging of access to
regulated data, as a baseline that is never subject to YAGNI-style deferral,
because the "current, real requirement" for these controls exists the moment
untrusted input or personal data enters the system, not the moment an
attacker or an auditor first exercises the gap. YAGNI's deferral logic
correctly applies to the SPECULATIVE extras layered on top of that baseline,
an elaborate, unused permission model with roles nobody has been assigned,
for example, and correctly does not apply to the baseline itself.

## Code examples

Three languages chosen to show YAGNI's effect at different points along the
speculative-generality range. Python shows the smallest, most literal
form, refusing an unneeded parameter. TypeScript shows the interface-level
form, refusing a plugin abstraction with a single real implementation. Go
shows the same interface-level question in a language with no classical
inheritance, where the temptation is a wide, general-purpose struct rather
than a class hierarchy. Java and Swift are omitted here specifically because
the pattern's clearest expression is the ABSENCE of structure rather than the
presence of a particular language mechanism, and the three shown already
demonstrate the idea in a class-based, a structurally-typed, and a
non-inheritance language.

### Python

The literal form. Before, a function generalized for a caching mode nobody
has asked for. After, the function that matches the one real, current
requirement.

```python
# Before: a YAGNI violation. `cache_mode` has exactly zero callers
# that pass anything other than the default. It was added "in case"
# a caller someday wants in-memory caching instead of the current,
# only real backend.

def fetch_user_profile(user_id: str, cache_mode: str = "redis") -> dict:
    if cache_mode == "redis":
        return _fetch_from_redis(user_id)
    elif cache_mode == "memory":
        return _fetch_from_memory_cache(user_id)
    else:
        raise ValueError(f"unknown cache_mode: {cache_mode}")


# After: applying YAGNI. Only the one real backend that is actually
# in production use remains. The unused branch, and the parameter
# that exists only to select it, are both gone.

def fetch_user_profile(user_id: str) -> dict:
    return _fetch_from_redis(user_id)


def _fetch_from_redis(user_id: str) -> dict:
    return {"id": user_id, "source": "redis"}


if __name__ == "__main__":
    print(fetch_user_profile("u_42"))
```

### TypeScript

The interface-level form. Before, a plugin-style abstraction built for a
second export format nobody has requested. After, the concrete function that
matches the one real requirement, with a note on when the abstraction would
earn its place back, per the Rule of Three discussed in dimension 13.

```typescript
// Before: a YAGNI violation. An ExportStrategy interface and a
// registry exist to support "future export formats", but exactly
// one format, CSV, has ever been requested or implemented.

interface ExportStrategy {
  export(rows: string[][]): string;
}

class CsvExportStrategy implements ExportStrategy {
  export(rows: string[][]): string {
    return rows.map((r) => r.join(",")).join("\n");
  }
}

class ExportRegistry {
  private strategies = new Map<string, ExportStrategy>();
  register(name: string, strategy: ExportStrategy): void {
    this.strategies.set(name, strategy);
  }
  export(name: string, rows: string[][]): string {
    const strategy = this.strategies.get(name);
    if (!strategy) throw new Error(`unknown export format: ${name}`);
    return strategy.export(rows);
  }
}

// After: applying YAGNI. The registry and the interface are gone.
// A second real export format, if one is ever actually requested,
// is the trigger to reintroduce an abstraction, shaped by the two
// real cases that then exist rather than by a guess made with one.

function exportCsv(rows: string[][]): string {
  return rows.map((r) => r.join(",")).join("\n");
}

console.log(exportCsv([["a", "1"], ["b", "2"]]));
```

### Go

The same interface-level question, in a language with no inheritance, where
the speculative-generality temptation usually appears as an overly wide
struct or an interface with a single implementer rather than as a class
hierarchy.

```go
package main

import "fmt"

// Before: a YAGNI violation. NotificationSender is an interface with
// exactly one real implementer, EmailSender, introduced because a
// second channel, SMS, was imagined as a likely future need.
//
// type NotificationSender interface {
//     Send(to, body string) error
// }
//
// type EmailSender struct{}
// func (e EmailSender) Send(to, body string) error {
//     fmt.Printf("email to %s: %s\n", to, body)
//     return nil
// }

// After: applying YAGNI. A concrete function, no interface, no
// second implementer to satisfy, no abstraction to maintain until
// a real second channel is actually requested.

func sendEmail(to string, body string) error {
	fmt.Printf("email to %s: %s\n", to, body)
	return nil
}

func main() {
	if err := sendEmail("user@example.com", "your report is ready"); err != nil {
		panic(err)
	}
}
```

## 18. References

1. Martin Fowler. "Yagni." Bliki entry. https://martinfowler.com/bliki/Yagni.html
   Verified 2026-08-02. Source for the C3-project origin account, the Kent
   Beck and Chet Hendrickson exchange, the "Simple Design" framing, and the
   Jeremy Miller extensibility-point quote used in dimension 11's misuse
   discussion.
2. Ron Jeffries. "You're NOT gonna need it!" 4 April 1998.
   https://ronjeffries.com/xprog/articles/practices/pracnotneed/
   Verified 2026-08-02. Earliest dated print appearance of the argument for
   the principle by name, source for the three-cost argument in dimension 2
   and the getter and setter example in dimension 1.
3. Ronald E. Jeffries, Ann Anderson, Chet Hendrickson. *Extreme Programming
   Installed*. Addison-Wesley, 2001. ISBN 0-201-70842-6. Page 190, per the
   Wikipedia citation verified against
   https://en.wikipedia.org/wiki/You_aren%27t_gonna_need_it, verified
   2026-08-02. Book-form source for YAGNI as one of XP's most quoted
   slogans.
4. Martin Fowler and Kent Beck. *Refactoring. Improving the Design of
   Existing Code*. Addison-Wesley, 1999. ISBN 0-201-48567-2. Page 68, per
   the Wikipedia citation verified against the same URL as reference 3,
   verified 2026-08-02, for the alternate wording "you aren't going to need
   it," and the book's own code smell catalog, cited generally for
   Speculative Generality and the Collapse Hierarchy, Inline Class, Remove
   Parameter, and Remove Dead Code refactorings referenced in dimension 14.
5. Kent Beck. *Extreme Programming Explained. Embrace Change*. 1st edition,
   Addison-Wesley, 1999. ISBN 0-201-61641-6. Source for the C3 project
   context in which YAGNI and the rest of XP's practices were developed,
   cited generally, referenced in dimension 9.
6. Wikipedia contributors. "You aren't gonna need it."
   https://en.wikipedia.org/wiki/You_aren%27t_gonna_need_it
   Verified 2026-08-02. Used to cross-check the page citations for
   references 3 and 4 and the general attribution timeline, not as a source
   of original explanation.
7. Segment Engineering. Alexandra Noonan. "Goodbye Microservices. From 100s
   of problem children to 1 superstar." 10 July 2018.
   https://segment.com/blog/goodbye-microservices/
   Verified 2026-08-02. Source for the production use in dimension 9.
8. David Heinemeier Hansson. "The Majestic Monolith." Signal v. Noise,
   Basecamp engineering blog. 29 February 2016.
   https://signalvnoise.com/svn3/the-majestic-monolith/
   Verified 2026-08-02. Source for the Basecamp production use in dimension
   9.
9. Google. "Google Engineering Practices Documentation. How to do a code
   review. What to look for in a code review."
   https://google.github.io/eng-practices/review/reviewer/looking-for.html
   Verified 2026-08-02. Source for the Google code review guidance on
   speculative, overly general designs cited in dimension 9.
10. Sam Newman. *Building Microservices*. 2nd edition, O'Reilly, 2021. ISBN
    978-1-4920-3402-5. Cited at the publisher description level, not a
    page-specific quote, for the cost asymmetry between internal and
    published interface changes discussed in dimension 4.
11. Andrew Hunt and David Thomas. *The Pragmatic Programmer*.
    Addison-Wesley, 1999. ISBN 0-201-61622-X. Cited generally for the Rule
    of Three heuristic discussed as YAGNI's resolution with Do Not Repeat
    Yourself in dimension 13.
12. C2 Wiki contributors. "YouArentGonnaNeedIt." Community-maintained wiki
    record of Extreme Programming practitioner discussion.
    http://wiki.c2.com/?YouArentGonnaNeedIt
    Verified 2026-08-02. Cited only as a record of practitioner discussion
    of Kent Beck's looser application of YAGNI to test code, referenced in
    dimension 4, not as a primary authored source.
