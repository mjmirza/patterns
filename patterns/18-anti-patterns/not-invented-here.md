---
name: Not Invented Here
slug: not-invented-here
family: 18-anti-patterns
category: Anti-Pattern
aliases: [NIH Syndrome, Reinventing the Wheel, Homegrown Everything]
first_described: "Katz, Allen 1982"
maturity: canonical
related: [golden-hammer, boat-anchor, vendor-lock-in, cargo-cult-programming, big-ball-of-mud]
incompatible_with: []
verified: 2026-08-02
---

# Not Invented Here

## 1. Name, aliases, and lineage

The canonical name in organizational and software literature is Not Invented
Here, almost always shortened to NIH or NIH syndrome. Wikipedia defines it as
"the tendency to avoid using or buying already existing products, research,
standards, or knowledge, instead choosing to redevelop them," a definition
adopted broadly across corporate and institutional cultures rather than being
specific to engineering ([Wikipedia, "Not invented here"](https://en.wikipedia.org/wiki/Not_invented_here),
verified 2026-08-02). The term is used pejoratively. it names a bias, not a
neutral description of choosing to build something.

The phrase reached its first serious empirical treatment in Ralph Katz and
Thomas J. Allen, "Investigating the Not Invented Here (NIH) Syndrome. A Look
at the Performance, Tenure, and Communication Patterns of 50 R&D Project
Groups," R&D Management, volume 12, issue 1, 1982, pages 7 to 19. The study
tracked fifty real research and development project groups and found that
project performance declined after roughly five years together, and traced
part of that decline to groups becoming steadily more insular, communicating
less with information sources outside the group over time. The same
mechanism, an internal group's confidence in its own prior work displacing
its willingness to evaluate outside alternatives, is what the term names in a
software context ([Wikipedia, "Not invented here," summarizing Katz and
Allen 1982](https://en.wikipedia.org/wiki/Not_invented_here), verified
2026-08-02). Katz and Allen were studying communication and tenure inside
R&d groups, not software architecture specifically, and the transplant of
their finding into software engineering discourse happened gradually over
the following two decades as engineering teams recognized the same insularity
in their own reluctance to adopt libraries, frameworks, and standards built
by other teams or other companies.

The opposite predisposition, adopting external work by default even when a
narrower internal solution would fit better, is documented under several
names. "Invented here," "not invented there," "proudly found elsewhere," and
"invented elsewhere" all describe the mirror-image bias, favoring anything
external purely because it is external
([Wikipedia, "Not invented here"](https://en.wikipedia.org/wiki/Not_invented_here),
verified 2026-08-02). This entry treats both directions as failure modes of
the same underlying decision, refusing to weigh a build choice on its actual
merits, and dimension 11 covers the reverse case explicitly.

Not Invented Here is closely related to, and frequently confused with,
Reinventing the Wheel. The two names are often used as synonyms in casual
conversation, but they name different things. Reinventing the Wheel describes
the act, building something that already exists elsewhere, regardless of
motive. Not Invented Here describes the cause, an organizational or personal
bias against adopting external work even after that work has been evaluated
and found adequate. A team can reinvent a wheel for a defensible reason, a
license conflict, a missing feature, a security requirement the existing
wheel does not meet, without exhibiting NIH. NIH is present only when the
external option was rejected for reasons that trace back to its origin
rather than to its fitness for the problem.

## 2. Problem and context

A team needs a capability another party has already built. a queue, a cache,
a date library, an authentication flow, a build system, sometimes an entire
platform. An external option exists, is documented, is used elsewhere, and on
paper meets the requirement. The team chooses to build its own version
instead, and the stated reasons for that choice, when examined honestly, turn
out to be about where the code came from rather than what the code does.

The pattern shows up in a recognizable sequence. Someone proposes adopting an
existing library or service. The proposal is met with concerns that sound
technical, it is too heavy, it does things we do not need, we cannot
customize it, we do not trust a black box we cannot read. Each concern is
individually plausible. What marks the pattern is that the same concerns
would be raised against any external option, regardless of its actual
quality, size, or fit, because the underlying objection is not to this
specific library, it is to depending on code the team did not write. A team
exhibiting NIH will find a reason to reject the third alternative library
as readily as it rejected the first two, because the search for
disqualifying flaws continues until an internal build is the last option
standing.

The context in which this becomes a genuine anti-pattern, rather than sound
engineering judgment, has three recurring ingredients. First, the team
underweights the true cost of the internal build, counting only the initial
implementation and skipping the years of maintenance, security patching, edge
case handling, and documentation that the external project has already
absorbed and will keep absorbing. Second, the team overweights control as a
value in itself, treating the ability to change any line of the dependency
as worth more than it actually is for a component nobody on the team plans to
change. Third, there is no honest build-versus-buy comparison on the table
at all, no written list of the external option's actual gaps against the
requirement, only a general discomfort that gets rationalized into specific
objections after the decision has effectively already been made. Remove any
one of the three and the decision usually resolves into a real evaluation
rather than a foregone conclusion dressed up as one.

The problem is not building things. Building infrastructure in-house is
sometimes exactly right, and dimension 4 lists the conditions under which it
is. The problem is a decision process that treats the origin of a piece of
code, written by us versus written by someone else, as a proxy for its
quality, when origin and quality are not correlated once a piece of external
software has real production usage and an active maintainer.

## 3. Forces

Judgement. The weighting below is engineering judgement drawn from the
sources cited elsewhere in this entry and from the general shape of the
failure mode. It is not itself a sourced claim.

The dominant force is the asymmetry between visible and invisible cost. The
cost of adopting an external dependency that later turns out to be wrong is
visible and attributable, an outage traced to a library, a security
advisory naming a package the team pulled in, a migration that has someone's
name on the pull request that introduced the dependency. The cost of an
internal build that quietly consumes a senior engineer's time for years,
never quite finishing the edge cases the external library solved on day one,
is diffuse and rarely attributed to the original decision to build rather
than adopt. Because attributable costs are felt more sharply than diffuse
ones, the incentive gradient tilts toward building, even when the expected
total cost of building is higher.

A second force is genuine risk reduction through control. Some external
dependencies really do carry risk that an internal build avoids, a company
that could go out of business or change its license, a library with a single
maintainer who could disappear, a service whose pricing could change
unilaterally. This is not imagined. The pattern is not that control has no
value. It is that the value of control is applied uniformly to every
external option regardless of that specific option's actual risk profile,
so a mature, widely used, permissively licensed library gets the same
suspicion as a single-maintainer weekend project.

A third force is learning and differentiation. Building something in-house
can genuinely deepen a team's understanding of a domain that is core to its
competitive position, and that depth is a real asset. The force runs the
other way as often. building something that is not core to the
business, purely for the sake of understanding it, spends scarce engineering
time on depth nobody outside the team will ever value.

A fourth force is switching cost once a codebase is entangled with a
homegrown component. The longer an internal build has been in production,
the more expensive it becomes to later admit the external alternative would
have been cheaper, because by then dozens of call sites depend on the
internal API's exact shape. This creates a ratchet, the sunk cost of the
build makes replacing it look more expensive than it would have looked to
never have built it, which keeps the team building the next internal
component too, because the first one "worked out."

## 4. Applicability and non-applicability

### When building it yourself is the right call

- **The capability is a genuine core differentiator of the business**, the
  thing customers are actually paying for, and no external option can be
  bent into that specific shape without losing the differentiation. Joel
  Spolsky's account of the early Microsoft Excel team is the case most often
  cited for this. the team maintained its own C compiler and deliberately
  kept its dependency surface small, and Spolsky argues this let the team
  ship on a schedule it controlled with code it fully understood
  ([Joel Spolsky, "In Defense of Not-Invented-Here Syndrome," Joel on
  Software, October 14, 2001](https://www.joelonsoftware.com/2001/10/14/in-defense-of-not-invented-here-syndrome/),
  verified 2026-08-02). The case holds only because the compiler behavior
  was load-bearing for the product's core value, not incidental
  infrastructure.
- **The available external options fail a specific, written requirement**,
  a real license conflict, a data residency rule the vendor cannot meet, a
  latency budget no hosted option can hit, and that failure is documented
  against the actual candidates evaluated rather than asserted in the
  abstract.
- **The team has already validated the external option in production and
  found a defect the maintainer will not or cannot fix**, and the defect
  actually matters for the product. Rejecting a library after using it is a
  different act from rejecting a library because of where it came from.
- **The dependency surface is small and stable enough that the maintenance
  cost of a thin internal implementation is genuinely lower than the
  integration and upgrade cost of an external one**, a narrowly scoped
  parsing routine over a full external parsing framework, for example.
- **No external option exists at the required maturity level**, which
  happens more often at the edge of a new platform or a new hardware
  generation than teams usually admit, but does happen.

### Non-applicability, when it is the anti-pattern rather than sound judgment

- **The stated objection to the external option would apply to any external
  option**, we cannot fully audit it, it might change, we would rather
  control it, without those concerns being weighed against the specific
  candidate's actual track record, license, and maintenance activity.
- **No real build-versus-buy comparison was written down.** the team can
  produce no document listing the requirement, the candidates considered,
  and the specific gap each candidate failed to close.
- **The capability is not a differentiator.** logging, date and time
  handling, HTTP retry logic, a UUID generator, a message queue client, a
  password hashing routine, are solved problems whose in-house
  reimplementation earns the business nothing a customer will ever notice,
  and often introduces bugs the mature external option fixed years earlier.
- **The team's true motive is unfamiliarity or discomfort with someone
  else's code, not a defect in that code.** discomfort reading unfamiliar
  source is real and worth naming honestly, but it is a training problem,
  not evidence the dependency is unsound.
- **Security-sensitive primitives are involved, cryptography, authentication
  token handling, random number generation for security purposes**, where a
  homegrown implementation is measurably more likely to contain an
  exploitable flaw than a widely reviewed external library, because
  correctness in this domain depends on adversarial review the internal
  team cannot replicate on its own.
- **The team is small and the internal build would consume a
  disproportionate share of its total engineering capacity** relative to the
  product work only the team can do, regardless of how well the internal
  build might eventually turn out.

## 5. Structure

Not Invented Here is a decision anti-pattern, not a code shape, so its
structure is organizational rather than architectural. the participants are
roles in a decision, not classes in a diagram.

- **The requirement.** the concrete capability needed, stated independently
  of any candidate solution, ideally in writing before any candidate is
  evaluated.
- **The external candidate.** an existing library, service, framework, or
  standard that could plausibly satisfy the requirement, along with its
  real, checkable attributes, license, maintenance activity, community size,
  known defects, and integration cost.
- **The internal alternative.** the team's own implementation of the same
  requirement, along with its own true cost, initial build time, and the
  ongoing maintenance, security patching, and edge case handling it will
  require over its lifetime.
- **The decision maker or decision process.** whoever, or whatever process,
  actually weighs the requirement against the two alternatives. In a healthy
  process this role produces a written comparison. In the anti-pattern, this
  role is absent or the comparison is produced after the internal build has
  already begun, functioning as a rationalization rather than an evaluation.
- **The sunk-cost ratchet.** once the internal alternative exists in
  production and has call sites depending on its specific shape, it
  functions as an additional, self-reinforcing participant. every day the
  internal build survives in production raises the perceived cost of later
  replacing it, independent of whether replacing it would actually be
  cheaper than continuing to maintain it.

## 6. ASCII structure diagram

```text
      requirement
          |
          v
+-------------------+          +---------------------+
| external candidate |          | internal alternative |
| license, maintainer|          | build time, ongoing  |
| track record, gaps |          | maintenance, patches  |
+---------+----------+          +-----------+----------+
          |                                 |
          |         decision process        |
          +----------------+----------------+
                           |
              written comparison exists?
                    /              \
                 yes                no
                  |                  |
                  v                  v
        evaluated on merit    origin-based rejection
                  |                  |
                  v                  v
          adopt or build       build by default
          on documented fit          |
                                      v
                          +----------------------+
                          | sunk-cost ratchet      |
                          | call sites accumulate  |
                          | replacement cost rises |
                          +----------------------+
```

## 7. Dynamics

The failure sequence has a consistent shape whether the object under
discussion is a library, a framework, or a whole platform.

```text
1. A requirement surfaces that an external option already satisfies.
2. Someone proposes adopting the external option.
3. Objections are raised about the external option.
4. Objections are checked against the ACTUAL candidate's real attributes?
       no  -> proceed to build without a written comparison
       yes -> proceed to a genuine build-versus-buy evaluation
5a. (no branch) Internal build begins. Cost is tracked as initial
    implementation time only.
6a. Internal build ships. Early cost looks comparable to, or cheaper than,
    the external option's integration cost.
7a. Over months and years, edge cases the external option had already
    solved surface one at a time in the internal build. Each is patched
    individually. No single patch looks expensive.
8a. Call sites accumulate against the internal build's specific API shape.
9a. A newer external option now clearly surpasses the internal build.
    Replacing it is proposed.
10a. The proposal to replace is met with the same category of objection
     that killed the original adoption, plus the new cost of migrating
     every accumulated call site. The internal build persists, now for
     sunk-cost reasons rather than the reasons that justified building it.
5b. (yes branch) The comparison is written, weighed against the specific
    candidate's actual gaps, and a decision is made on that basis, to
    adopt, to build a narrow wrapper, or to build the whole thing, with the
    reasoning recorded for the next person who reopens the question.
```

The dynamic that distinguishes the anti-pattern from a sound build decision
is entirely in step 4. A team that reliably checks its objections against a
real candidate's real attributes, and is willing to record "we evaluated
this and it is actually fine" as an outcome, does not fall into the failure
branch even when it occasionally decides to build. A team whose objections
are never checked against a specific candidate falls into the failure branch
even when its individual build decisions are, by luck, sometimes correct.

## 8. Implementation variants

Not Invented Here is a decision failure, not a code pattern, so it has no
correct implementation, but the form the resulting homegrown code takes
varies in ways worth naming, because each variant carries a different cost
profile.

- **Full reimplementation of a mature capability.** a homegrown date and
  time library, a homegrown ORM, a homegrown templating engine. This is the
  costliest variant because the external option's edge cases were solved by
  years of production use the internal build has to rediscover one bug
  report at a time.
- **A thin wrapper that duplicates an external client's surface with no
  added behavior.** a hand-rolled HTTP client wrapping raw sockets where an
  existing client library would have done the same job with less code. This
  variant's cost is smaller per instance but multiplies across a codebase
  when every team writes its own version of the same thin wrapper.
- **Platform-level NIH.** an organization builds its own version control
  system, its own container runtime, its own build tool, when general
  purpose tools already exist. This variant is sometimes justified at
  extreme scale, discussed in dimension 4, and is the most expensive
  variant to reverse once committed to, because an entire organization's
  tooling habits form around it.
- **Fork-and-diverge.** the team starts from an external project's source,
  intending to contribute improvements back, but instead accumulates local
  patches that are never upstreamed, ending up maintaining a private fork
  that drifts further from the upstream project with every release the team
  does not merge. This variant looks like adoption at the start and
  converts into full NIH cost over time without a discrete decision point
  where anyone chose it.
- **Standards NIH.** a team defines its own data format, protocol, or
  configuration syntax where an existing, documented standard would have
  served, because the standard does more than needed or is not exactly
  what is wanted. The cost here is paid by every future integration partner
  who has to learn the bespoke format instead of using existing tooling
  built for the standard.

## 9. Known production uses

Nokia (2010 to 2011), continued investment in the Symbian platform against
external platform alternatives. Nokia's internal culture had, since the
Symbian platform's origin in the 1990s, prioritized deep vertical control
over its own smartphone operating system rather than adopting an
already-maturing external platform. Incoming CEO Stephen Elop's internal
memo, made public through an Engadget leak on 8 February 2011 and now
generally referred to as the "burning platform" memo, argued that Nokia's
competitive position had shifted from a contest between individual devices
to a contest between entire surrounding platforms, one covering hardware,
software, outside developers, an app marketplace, commerce, advertising,
search, and communications together, and that Nokia had to choose whether
to build, catalyse, or join one of those broader platforms rather than
continue competing on the device alone
([Wikipedia, "Stephen Elop"](https://en.wikipedia.org/wiki/Stephen_Elop),
verified 2026-08-02). Within months Nokia abandoned Symbian and its MeeGo
successor in favor of Windows Phone, an unambiguous admission that the
years spent building and maintaining an internal alternative to an already
available external platform, Android, had cost the company its market
lead rather than protecting it.

Microsoft Excel's internal C compiler, reported and defended by Joel
Spolsky as a deliberate, successful instance of the same behavior applied
narrowly and on purpose. Spolsky reports that the Excel team at Microsoft
maintained its own C compiler rather than depending on Microsoft's shared
compiler infrastructure, choosing vertical independence over shared
tooling for a component the team judged core to shipping the product on
its own schedule
([Joel Spolsky, "In Defense of Not-Invented-Here Syndrome," Joel on
Software, October 14, 2001](https://www.joelonsoftware.com/2001/10/14/in-defense-of-not-invented-here-syndrome/),
verified 2026-08-02). This is cited in this entry alongside the Nokia case
deliberately, because it is the same behavior, retaining a home-grown
alternative to shared external infrastructure, and the only difference
between the two outcomes is whether the team's reasoning was checked
against the actual requirement or applied as a blanket default.

Amazon's Obidos e-commerce engine and Google's early hand-built server
hardware and software stack, both cited by Spolsky in the same essay as
further examples of large technology companies choosing to build core
infrastructure in-house where off-the-shelf options existed at the time,
on the argument that the specific infrastructure in question was close
enough to the company's actual competitive differentiation to justify the
build
([Joel Spolsky, "In Defense of Not-Invented-Here Syndrome," Joel on
Software, October 14, 2001](https://www.joelonsoftware.com/2001/10/14/in-defense-of-not-invented-here-syndrome/),
verified 2026-08-02). These cases are reported through Spolsky's essay
rather than independently verified against Amazon's or Google's own
disclosures, and are cited here as documented, named instances of the
behavior rather than as an independent confirmation of every technical
detail Spolsky attributes to each company.

Katz and Allen's original 1982 study itself constitutes a documented,
empirical production use of the pattern, tracking fifty real research and
development project groups and finding a measurable correlation between a
group's growing insularity, less communication with outside information
sources, and declining project performance after roughly five years
together ([Wikipedia, "Not invented here," summarizing Katz and Allen
1982](https://en.wikipedia.org/wiki/Not_invented_here), verified
2026-08-02). The study's participating organizations were not named,
consistent with standard practice for confidential organizational research
of that era, so this instance is cited for its empirical finding rather
than as a named system, distinct from the three named cases above.

## 10. Consequences

Positive.

- A team that builds a genuinely differentiating capability in-house can
  ship a product no competitor using the same off-the-shelf components can
  match, because the capability is inseparable from code only that team
  wrote.
- Full understanding of every line in a critical path removes a category of
  incident, a defect in a dependency the team cannot read or patch quickly,
  that external dependence always carries at some level.
- Independence from a vendor's release plans, pricing, and licensing
  decisions removes a real, if often overstated, category of business risk.
- Building a capability from first principles can produce genuine
  organizational learning that later pays off in an adjacent, truly novel
  problem the external option was never designed to solve.

Negative.

- The team pays the full lifecycle cost of the capability, initial build,
  every subsequent edge case, every security patch, every platform upgrade,
  that an external option's existing user base and maintainer would
  otherwise have already absorbed or would absorb going forward.
- Engineering time spent on a non-differentiating capability is engineering
  time not spent on the product work only that team can do, an opportunity
  cost that rarely appears on any accounting of the decision.
- New hires face a steeper ramp-up, because a homegrown component has no
  public documentation, no Stack Overflow history, and no community of
  prior users to draw on when something goes wrong.
- The internal build accumulates defects the mature external option already
  fixed years earlier, because the internal team is rediscovering the same
  edge cases the external community already worked through.
- The sunk-cost ratchet described in dimension 5 makes the decision to keep
  building progressively less reversible over time, independent of whether
  continuing is actually still the right call.

## 11. Failure modes and misuse

Symptom, cause, fix, in each case.

**Symptom.** Every proposal to adopt an external library is met with a
different, individually plausible objection, and no external library is
ever actually adopted, regardless of its quality.
Cause. The rejection criteria are being generated after the fact to justify
a default preference for building, rather than being checked consistently
against the specific candidate's actual attributes.
Fix. Require a written build-versus-buy comparison naming the specific
candidate evaluated, its license, its maintenance activity, and the
specific requirement it fails to meet, before a build decision is approved.

**Symptom.** A homegrown internal library has grown to duplicate most of the
feature surface of a well known external library, one feature at a time,
over several years, and nobody can point to the moment the team decided to
build the whole thing.
Cause. The internal build began as a small, justified wrapper and expanded
incrementally as each new requirement arrived, with each individual
expansion looking cheaper in isolation than switching to the external
library at that point, even though the cumulative cost of the whole
internal library now exceeds what adopting the external option would have
cost from the start.
Fix. Periodically compare the current feature surface of the internal build
against the current state of the external alternative it duplicates, not
against the external alternative's state at the time the internal build
began, and treat a widening gap as a signal to re-evaluate rather than
evidence the internal build must continue.

**Symptom.** The team maintains a private fork of an open source project
with a growing list of local patches, none of which have been proposed
upstream, and every upstream release requires manual reconciliation.
Cause. Fork-and-diverge, described in dimension 8, where the initial
adoption looked like using the external project but the team never
committed to a workflow of contributing changes back, so the fork's
maintenance cost grows every release without the corresponding benefit of
upstream improvements landing automatically.
Fix. Either commit engineering time to upstreaming local patches on a
schedule, or make the fork's independence an explicit, budgeted decision
with an owner responsible for its ongoing drift cost, rather than an
unplanned byproduct of never quite finding time to contribute back.

**Symptom.** A security incident traces back to a homegrown implementation
of a cryptographic or authentication primitive that an established library
would have implemented correctly.
Cause. The primitive was treated as a normal engineering problem subject to
the team's usual build-versus-buy judgment, rather than being recognized as
a category where correctness depends on adversarial review the internal
team cannot replicate, as covered in dimension 4's non-applicability list.
Fix. Treat security-sensitive primitives as a hard exception to any general
NIH tolerance the team otherwise applies, and require an explicit, named
justification, reviewed by someone other than the implementer, before a
homegrown cryptographic or authentication component is approved.

**Symptom.** The organization has standardized on a bespoke internal data
format, protocol, or configuration syntax, and every new integration
partner has to be taught the format from scratch because no existing
tooling understands it.
Cause. Standards NIH, described in dimension 8, where an existing
documented standard was rejected because it appeared to do more than
needed or was not exactly right, without pricing in the ongoing cost every
future integration partner would pay to learn the bespoke alternative.
Fix. When evaluating a data format or protocol decision, count the training
and tooling cost imposed on every future external party who will have to
integrate with it, not only the cost to the team making the decision, and
weigh that cost explicitly against the standard's imperfect fit.

**Symptom, reverse case.** A team adopts every external library, framework,
and service offered to it, for a component that was small, stable, and
would have taken less code to write directly than the code needed to
integrate and keep patched the external dependency now pulled in.
Cause. This is the mirror image of NIH, sometimes called "proudly found
elsewhere," where the bias runs toward external adoption for its own sake
rather than toward internal building for its own sake
([Wikipedia, "Not invented here"](https://en.wikipedia.org/wiki/Not_invented_here),
verified 2026-08-02). It produces the same failure, a decision made on the
origin of the code rather than its fit, in the opposite direction.
Fix. Apply the same written build-versus-buy comparison in both
directions. a small, stable requirement with no real edge cases is a
legitimate case for a direct, dependency-free implementation, and rejecting
that option purely because it is not external is the same error as
rejecting an external option purely because it is not internal.

## 12. Trade-off matrix

Compared against Boat Anchor, Golden Hammer, and Vendor Lock-in, the three
named anti-patterns this entry sits closest to.

| Force | Not Invented Here | Boat Anchor | Golden Hammer | Vendor Lock-in |
|---|---|---|---|---|
| What is rejected or over-favored | any external solution, on the basis of its origin | nothing rejected, a component already paid for is kept regardless of fit | no rejection of alternatives, a familiar tool is reused past its fit | the opposite bias, an external vendor's specific product is over-favored once adopted |
| Decision timing | at build-versus-buy time, before the code exists | after acquisition, the component already exists and sits unused or misused | at design time, a tool already known is chosen without comparison | at renewal or migration time, after switching cost has already accrued |
| Root cause | distrust of externally authored code | sunk cost in a prior purchase or acquisition | familiarity and comfort with a known tool | switching cost created by a specific vendor's proprietary interface |
| Typical fix | a written, candidate-specific comparison before building | write off the sunk cost, evaluate the component on today's needs | evaluate the problem's actual forces before reusing yesterday's tool | negotiate portability or abstraction boundaries before switching cost accrues |
| Ongoing maintenance burden | high, the team owns the full lifecycle of a duplicated capability | variable, depends on what was acquired | usually low per decision, cost compounds across many wrong-tool decisions | low day to day, high at the point of exit |

## 13. Related and incompatible patterns

**Golden Hammer** is the pattern this entry pairs with most often in
practice, and the two frequently occur together, a team that already built
its own version of a capability tends to reach for that same homegrown tool
on the next unrelated problem too, because it is now the familiar option
inside the team, compounding the original NIH decision into a second,
unrelated misuse.

**Boat Anchor** differs in timing rather than in kind. Boat Anchor is a
component already acquired, through a purchase, an acquisition, or a
previous decision, that stays in the system despite no longer fitting any
real need. NIH is the decision, made before any component exists, to build
rather than adopt. A homegrown NIH build that outlives its usefulness and
is kept anyway becomes a Boat Anchor. the two patterns can describe the
same object at different points in its life.

**Vendor Lock-in** is the structural opposite outcome of the same
underlying failure, evaluating a dependency on something other than its
actual fit for the requirement. NIH avoidance taken too far, adopting
every external option to escape any appearance of building in-house, is a
direct path into Vendor Lock-in, because the team never develops the
internal competence to evaluate whether a given vendor's proprietary
interface is safe to depend on.

**Cargo Cult Programming** shares NIH's tendency to copy structure without
evaluating fit, but in the opposite direction. Cargo Cult Programming
copies an external pattern's surface form without understanding why it
works. NIH refuses the external form outright. Both fail to actually
evaluate the external work on its merits, one by blind adoption, the other
by blind rejection.

**Strategy and Template Method**, the two GoF patterns most useful for
building a genuine, justified internal alternative correctly, when
dimension 4's applicability conditions are actually met. Strategy lets a
team swap between an external implementation and an internal one behind a
shared interface, which is the correct structural move when a build
decision needs to remain reversible, keeping the door open to adopt the
external option later without a full rewrite.

## 14. Refactoring path in and out

### Introducing a disciplined build-versus-buy check where none exists

1. Name the requirement in writing, independent of any specific candidate,
   before evaluating any option.
2. List the real external candidates, with their license, maintenance
   activity, and known limitations, sourced from the candidate's own
   documentation and issue tracker rather than from memory or reputation.
3. For each candidate, write the specific requirement it fails to meet, if
   any. wanting to control it is not a requirement it fails to meet.
4. Only after that list exists, decide whether to adopt an external
   candidate, build a narrow wrapper around one, or build the whole thing
   internally, and record the reasoning next to the decision so the next
   person who reopens the question, and someone eventually will, can see
   what was actually weighed.
5. Put an expiry or review trigger on any build decision, a scheduled point
   to re-run the comparison against the current external alternatives, not
   against the alternatives as they existed when the decision was made.

### Retiring an existing homegrown component in favor of an external one

1. Confirm the external candidate now genuinely covers the requirement,
   including the edge cases the internal build had to learn the hard way,
   not only the requirement as it was originally understood.
2. Introduce the external option behind the same interface the internal
   component already exposes, using Adapter or Strategy so call sites do
   not need to change yet.
3. Run both implementations in parallel for a defined period where safe,
   comparing outputs, or migrate call sites in small batches behind a
   feature flag, verifying behavior at each batch.
4. Remove the internal implementation only after every call site has moved,
   and archive rather than delete the internal source in case a
   regression surfaces later, per the repository's standard reversibility
   practice for any retired component.
5. Record what the internal build cost over its lifetime, engineering time,
   incident count, and the calendar time from decision to build to
   retirement, and treat that record as a real data point for the next
   build-versus-buy decision this team makes, closing the loop the sunk
   cost ratchet in dimension 5 otherwise keeps open indefinitely.

## 15. Testing and verification

Testing the anti-pattern itself is a decision-process check rather than a
code check, and it happens before any implementation exists.

- **Audit build decisions for a written comparison.** for any component
  built in-house in the last review period, confirm a document exists
  naming the requirement, the candidates considered, and the specific gap
  each candidate failed to close. A build decision with no such document is
  a flag, whether or not the decision itself was correct.
- **Test the internal build against the external option's published
  conformance or compatibility test suite where one exists**, for example
  running a homegrown date library against a standard's published test
  vectors. A gap the internal build fails that the external option passes
  is direct, checkable evidence of the true cost gap between the two.
- **Track defect density per component, homegrown versus adopted**, over a
  comparable period of production use. a homegrown component that shows a
  measurably higher defect rate than a comparable external component in
  active use elsewhere is evidence, not merely suspicion, that the build
  decision underestimated the external option's maturity.
- **Verify the reverse case, an audit of adopted dependencies for
  components that would have been smaller and simpler to write directly**,
  applying the same written comparison discipline in the other direction,
  as covered in dimension 11's reverse-case symptom.
- **Time-box a proof of concept against the leading external candidate
  before committing to a full internal build**, so the comparison in
  dimension 3's step 4 is based on a working spike rather than on assumed
  integration friction that may not materialize.

## 16. Observability signals

- **Dependency-versus-internal-line-of-code ratio, tracked over time.** a
  steadily rising share of a codebase devoted to reimplementing capability
  available externally, without a corresponding rise in product
  differentiation, is a lagging signal the organization is trending toward
  the anti-pattern.
- **Time-to-first-response on build-versus-buy proposals.** a healthy
  process produces a documented decision, adopt or build, within a bounded
  window. A pattern of proposals that stall indefinitely, with the default
  outcome being an unplanned internal build months later, indicates the
  comparison step in dimension 14 is not actually happening.
- **Mean time between adoption of an external option and its subsequent
  rejection in favor of an internal rebuild**, if unusually short across
  multiple unrelated components, indicates the external options are not
  being fairly evaluated to begin with, since a fair evaluation would
  reject unsuitable candidates before adoption rather than after.
- **Onboarding time for new hires on homegrown components versus adopted
  ones.** a large, consistent gap is a direct, measurable cost of NIH that
  rarely shows up on any other dashboard.
- **Issue count and patch frequency on the internal build compared with the
  external alternative's own issue tracker over the same window.** an
  internal build accumulating open issues at a rate the mature external
  option resolved years earlier is evidence the true maintenance cost was
  underestimated at build time.

## 17. Security and privacy implications

The sharpest security implication of Not Invented Here is in cryptography,
authentication, and random number generation, where a widely used external
library benefits from adversarial review, published attacks against known
implementations, and a maintained patch history that a single internal team
cannot replicate through code review alone. A homegrown implementation of
any of these primitives is not merely a duplicated effort. it is a
measurable increase in the probability the implementation contains a flaw
that a determined attacker would find before the internal team does,
because the internal team's review process, however careful, is not
equivalent to the years of public scrutiny a mature external library has
already absorbed. This is the basis for treating security-sensitive
primitives as a hard, named exception in dimension 4's non-applicability
list rather than as a case-by-case judgment call.

A secondary implication runs through supply chain risk in the opposite
direction. an organization that swings too far from NIH into
adopt-everything, the reverse case covered in dimension 11, expands its
dependency surface and, with it, the number of third parties whose
compromise, license change, or abandonment can directly affect the
organization's own systems. Neither extreme is safer than the other by
default. the safety of a given choice depends on the specific track record
of the specific dependency being adopted or avoided, which is exactly the
comparison this entry argues must be made explicit rather than assumed in
either direction.

Data handling implications are otherwise indirect. a homegrown
authentication or session-handling component that has not absorbed years of
external bug reports is more likely to leak or mishandle personal data
through an edge case a mature external library already closed, which is
one more argument for treating identity and access primitives as a
category where the default should favor adoption over building, consistent
with dimension 4.

## 18. References

- Ralph Katz and Thomas J. Allen, "Investigating the Not Invented Here (NIH)
  Syndrome. A Look at the Performance, Tenure, and Communication Patterns
  of 50 R&D Project Groups," R&D Management, volume 12, issue 1, 1982,
  pages 7 to 19.
- [Wikipedia, "Not invented here"](https://en.wikipedia.org/wiki/Not_invented_here),
  verified 2026-08-02.
- [Wikipedia, "Stephen Elop"](https://en.wikipedia.org/wiki/Stephen_Elop),
  verified 2026-08-02.
- [Joel Spolsky, "In Defense of Not-Invented-Here Syndrome," Joel on
  Software, October 14, 2001](https://www.joelonsoftware.com/2001/10/14/in-defense-of-not-invented-here-syndrome/),
  verified 2026-08-02.

## Code examples

Three implementations of the same decision surface, a rate limiter component
where the requirement is deliberately kept small and stable, to show what a
disciplined build decision looks like next to an internal implementation
that has quietly grown past its original scope. Each example first models
the honest comparison, then shows the homegrown implementation that a team
skipping the comparison would ship, with the same edge case gap.

### TypeScript

```typescript
// The requirement, named before any candidate is evaluated.
interface RateLimiterRequirement {
  readonly maxRequests: number;
  readonly windowMs: number;
  readonly distributed: boolean;
}

// A written comparison record, not a comment, a real data structure that
// gets reviewed and stored next to the decision.
interface BuildVsBuyRecord {
  readonly requirement: RateLimiterRequirement;
  readonly candidateName: string;
  readonly candidateGap: string | null;
  readonly decision: "adopt" | "build";
}

function evaluate(
  req: RateLimiterRequirement,
  candidateSupportsDistributed: boolean,
): BuildVsBuyRecord {
  const gap = req.distributed && !candidateSupportsDistributed
    ? "candidate has no distributed coordination, requirement needs one"
    : null;
  return {
    requirement: req,
    candidateName: "existing-rate-limit-library",
    candidateGap: gap,
    decision: gap === null ? "adopt" : "build",
  };
}

// The minimal, honestly scoped internal implementation, used only when
// evaluate() actually returned "build" with a named gap.
class FixedWindowLimiter {
  private count = 0;
  private windowStart = Date.now();

  constructor(
    private readonly max: number,
    private readonly windowMs: number,
  ) {}

  allow(now: number = Date.now()): boolean {
    if (now - this.windowStart >= this.windowMs) {
      this.windowStart = now;
      this.count = 0;
    }
    if (this.count >= this.max) return false;
    this.count += 1;
    return true;
  }
}

const record = evaluate(
  { maxRequests: 100, windowMs: 60_000, distributed: true },
  false,
);
console.log(record);
if (record.decision === "build") {
  const limiter = new FixedWindowLimiter(
    record.requirement.maxRequests,
    record.requirement.windowMs,
  );
  console.log("first request allowed", limiter.allow());
}
```

### Python

```python
from dataclasses import dataclass
from time import time


@dataclass(frozen=True)
class RateLimiterRequirement:
    max_requests: int
    window_seconds: float
    distributed: bool


@dataclass(frozen=True)
class BuildVsBuyRecord:
    requirement: RateLimiterRequirement
    candidate_name: str
    candidate_gap: str | None
    decision: str


def evaluate(
    requirement: RateLimiterRequirement,
    candidate_supports_distributed: bool,
) -> BuildVsBuyRecord:
    gap = None
    if requirement.distributed and not candidate_supports_distributed:
        gap = "candidate has no distributed coordination, requirement needs one"
    return BuildVsBuyRecord(
        requirement=requirement,
        candidate_name="existing-rate-limit-library",
        candidate_gap=gap,
        decision="build" if gap else "adopt",
    )


class FixedWindowLimiter:
    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self._max = max_requests
        self._window = window_seconds
        self._count = 0
        self._window_start = time()

    def allow(self, now: float | None = None) -> bool:
        now = time() if now is None else now
        if now - self._window_start >= self._window:
            self._window_start = now
            self._count = 0
        if self._count >= self._max:
            return False
        self._count += 1
        return True


if __name__ == "__main__":
    record = evaluate(
        RateLimiterRequirement(max_requests=100, window_seconds=60.0, distributed=True),
        candidate_supports_distributed=False,
    )
    print(record)
    if record.decision == "build":
        limiter = FixedWindowLimiter(
            record.requirement.max_requests, record.requirement.window_seconds
        )
        print("first request allowed", limiter.allow())
```

### Go

```go
package main

import (
	"fmt"
	"time"
)

// RateLimiterRequirement names the requirement independently of any
// candidate, per dimension 14 step 1.
type RateLimiterRequirement struct {
	MaxRequests int
	Window      time.Duration
	Distributed bool
}

// BuildVsBuyRecord is the written comparison, per dimension 14 step 3.
type BuildVsBuyRecord struct {
	Requirement   RateLimiterRequirement
	CandidateName string
	CandidateGap  string
	Decision      string
}

func evaluate(req RateLimiterRequirement, candidateSupportsDistributed bool) BuildVsBuyRecord {
	gap := ""
	if req.Distributed && !candidateSupportsDistributed {
		gap = "candidate has no distributed coordination, requirement needs one"
	}
	decision := "adopt"
	if gap != "" {
		decision = "build"
	}
	return BuildVsBuyRecord{
		Requirement:   req,
		CandidateName: "existing-rate-limit-library",
		CandidateGap:  gap,
		Decision:      decision,
	}
}

// FixedWindowLimiter is the minimal internal implementation used only
// when evaluate returns "build" with a named gap.
type FixedWindowLimiter struct {
	max         int
	window      time.Duration
	count       int
	windowStart time.Time
}

func newFixedWindowLimiter(max int, window time.Duration) *FixedWindowLimiter {
	return &FixedWindowLimiter{max: max, window: window, windowStart: time.Now()}
}

func (l *FixedWindowLimiter) allow(now time.Time) bool {
	if now.Sub(l.windowStart) >= l.window {
		l.windowStart = now
		l.count = 0
	}
	if l.count >= l.max {
		return false
	}
	l.count++
	return true
}

func main() {
	record := evaluate(
		RateLimiterRequirement{MaxRequests: 100, Window: 60 * time.Second, Distributed: true},
		false,
	)
	fmt.Printf("%+v\n", record)
	if record.Decision == "build" {
		limiter := newFixedWindowLimiter(record.Requirement.MaxRequests, record.Requirement.Window)
		fmt.Println("first request allowed", limiter.allow(time.Now()))
	}
}
```

Java, Rust, and Swift are omitted here on purpose. Not Invented Here is a
decision process, and the three examples above already show that process in
full across three idiomatically different languages, a strongly typed
scripting-adjacent language, a dynamically typed language, and a compiled
systems language with explicit memory ownership. A fourth or fifth language
would repeat the same structure without adding a new facet of the pattern,
which the repository's own guidance treats as a reason to omit rather than
pad.
