---
name: Big Ball of Mud
slug: big-ball-of-mud
family: 11-ddd
category: Anti-pattern
aliases: [Spaghetti Architecture, Mud Ball]
first_described: "Foote, Yoder 1997"
maturity: canonical
related: [bounded-context, anticorruption-layer, context-map, core-domain, supporting-subdomain]
incompatible_with: []
verified: 2026-08-02
---

# Big Ball of Mud

## 1. Name, aliases, and lineage

The canonical name is Big Ball of Mud. It was first described by Brian Foote and
Joseph Yoder in a paper of the same title, presented at the Fourth Conference on
Pattern Languages of Programs (PLoP '97 / EuroPLoP '97) in Monticello, Illinois,
in September 1997, and issued as Technical Report WUCS-97-34 by the Department
of Computer Science at Washington University in St. Louis. The paper was later
collected as Chapter 29 of Neil Harrison, Brian Foote, and Hans Rohnert, editors,
*Pattern Languages of Program Design 4*, Addison-Wesley, 2000
([conference PDF, hillside.net](https://hillside.net/plop/plop97/Proceedings/foote.pdf),
verified 2026-08-02; also mirrored at
[laputan.org/mud/mud.html](http://www.laputan.org/mud/mud.html), verified
2026-08-02).

The paper describes itself, without irony, as documenting "the de facto standard
software architecture," meaning the shape most systems actually have rather than
the shape architecture books recommend. Foote and Yoder frame the whole entry as
a small pattern language rather than a single pattern. The top-level pattern,
Big Ball of Mud, is accompanied by six subordinate patterns that describe how
systems arrive at and persist in that state. Throwaway Code, Piecemeal Growth,
Keep It Working, Shearing Layers, Sweeping It Under the Rug, and Reconstruction
(searchable confirmation of these six names across the paper's own table of
contents and secondary summaries,
[laputan.org/mud/mud.html](http://www.laputan.org/mud/mud.html) and
[hillside.net/plop/plop97/Proceedings/foote.pdf](https://hillside.net/plop/plop97/Proceedings/foote.pdf),
verified 2026-08-02).

Foote and Yoder extend the term with an analogy to a shantytown, an
unplanned settlement built from cheap materials by unspecialised labour, where
each dwelling is maintained by its own inhabitant and nobody owns the roads
between them. The shantytown analogy is not offered as an alternate name for
the pattern. It is a device the authors use to explain why the pattern
persists even though almost everybody who works inside one agrees it is a bad
outcome. No second, competing name for the pattern itself was proposed by
Foote and Yoder. Later writers on the web occasionally call the same
condition Spaghetti Architecture or a Mud Ball, both informal, both used to
mean the identical thing, an architecture with no discernible modular
structure at the system level (secondary usage, for example
[DevIQ, "Big Ball of Mud"](https://deviq.com/antipatterns/big-ball-of-mud/)
and
[GeeksforGeeks, "Big Ball of Mud Anti-Pattern"](https://www.geeksforgeeks.org/system-design/big-ball-of-mud-anti-pattern/),
verified 2026-08-02).

It is worth being precise about a distinction several secondary sources draw
and that this entry preserves. Spaghetti code describes a property of a single
function, method, or file, tangled control flow, deep nesting, unclear branch
logic. Big Ball of Mud describes a property of an entire system, the absence
of any boundary between modules at all, so that any file can reach any other
file's internals. A codebase can contain spaghetti code in one function and
still have clean module boundaries around it. A codebase can also have every
individual function reading cleanly while the system as a whole is a Big Ball
of Mud, because nothing stops module A from importing module Z's private
state directly. The two conditions correlate in practice, spaghetti code is
often a symptom found inside a mud ball, but they are not the same claim, and
conflating them is one of the more common misreadings of the term in blog
coverage (this distinction is engineering judgement drawn from reading the
primary source and the secondary commentary together, not a claim either
source states in exactly this form).

## 2. Problem and context

A system starts small. One person, or a small team under real time pressure,
writes code that solves the problem in front of them using whatever shortcut
gets a working result fastest. A shared database table gets read directly from
three unrelated parts of the codebase because building a proper interface
would take an afternoon nobody has. A global variable holds a piece of state
that three subsystems mutate because passing it through explicit parameters
would touch too many call sites. A quick script, written to migrate data once,
never gets deleted and quietly becomes a dependency of the nightly job. None of
these individual decisions is unreasonable in isolation, and the system that
results genuinely works, ships, and earns revenue.

The system then succeeds, which is the part that makes the story different
from ordinary neglect. Success brings more features, more deadlines, and more
people, and each new person extends the system the way the system already
teaches them to, by finding the nearest existing structure that does something
similar and copying it, coupling to it, and extending it in place. There is
rarely a moment where anyone decides "we will now build without architecture."
Instead every individual change is locally reasonable and every change is made
under the same pressure that produced the last one, and the aggregate of many
locally reasonable, deadline-driven changes is a system with no system-level
structure at all. This is the context the pattern names. Not a single bad
decision, but the accumulated residue of thousands of individually defensible
ones, made under conditions where nobody was ever paid to stop and draw a
boundary.

The context in which this arises has three recurring features. First, the
market or the organisation rewards shipping speed far more visibly and far
sooner than it rewards internal structure, so structure loses every local
trade-off even when it would win the aggregate one. Second, the team changes
over time, so the tacit knowledge of why a shortcut was taken, and where it
was meant to be temporary, is lost well before the shortcut is removed. Third,
there is no natural forcing function, no compiler error, no failed build, no
angry customer, that fires when a boundary is crossed silently, because the
language and the deployment unit both allow any file to call any other file.
A Big Ball of Mud is what you get, by default, from a system built entirely
out of locally optimal decisions with no global constraint enforcing
modularity.

## 3. Forces

The forces below are not a list this entry invented. They correspond directly
to the six subordinate patterns Foote and Yoder describe, restated here as
competing pressures rather than as named sub-patterns, so the trade-off each
one represents is visible.

- **Delivery speed against future comprehensibility.** Favours speed, almost
  always. A shortcut that saves an afternoon today is invisible on next
  quarter's roadmap, while the cost of that shortcut, paid by whoever reads the
  code next, is invisible on this quarter's roadmap. The two costs are never
  compared by the same person at the same time, so speed wins by default.
- **Local correctness against global structure.** Favours local correctness.
  Each individual change is judged by whether it makes the feature work, almost
  never by whether it respects a module boundary that may not even be
  documented as existing. A change can be entirely correct in its behaviour and
  entirely destructive to the system's structure at once.
- **Stability against redesign.** Favours stability once a system is in
  production and earning money. This is the force behind the sub-pattern Keep
  It Working, the working system, however ugly, is a known quantity that
  generates revenue, and a redesign is an unknown quantity that risks it. Teams
  under this force will accept an architecture they openly dislike over a
  rewrite whose failure mode is existential.
- **Individual ownership against shared infrastructure.** Favours individual
  ownership under time pressure. Building shared infrastructure, an internal
  library, a proper interface, an event bus, requires coordination across
  people and teams, and coordination is slow. A developer under deadline
  pressure will write a direct dependency into the nearest working thing before
  they will propose a cross-team interface and wait for it to be agreed.
- **Comprehension cost against removal cost.** As the system grows, this force
  inverts and becomes the trap the pattern is named for. Early on, understanding
  a small system well enough to restructure it is cheap and removing a bad
  decision is cheap. Once the system is large, understanding it well enough to
  safely change its structure becomes expensive precisely because the structure
  is unclear, which is the sub-pattern Sweeping It Under the Rug, isolating a
  bad area behind a thin wrapper rather than paying the now much higher cost of
  actually fixing it.
- **Piecemeal adaptation against a master plan.** Favours piecemeal adaptation.
  A grand architecture drawn up before requirements are known tends to be wrong
  about at least part of what the system will need, and a system that must obey
  a plan that turned out to be wrong pays a continuous tax fighting its own
  blueprint. Piecemeal Growth, extending the system in whatever direction the
  next requirement points, produces a working system faster than waiting for a
  master plan to be revised, at the cost of never having one.

No force here is favoured for free. The pattern exists because every one of
these trade-offs is a real trade-off with a real cost on both sides, and the
side that loses, structure, comprehensibility, and long-term change cost, does
not announce its bill until much later.

## 4. Applicability and non-applicability

Because this is an anti-pattern, applicability here means something specific.
It does not mean "when should I deliberately build one." It means "when is
tolerating the mud a rational engineering decision rather than a failure of
discipline," against the second list, when tolerating it is the failure.

Tolerating a Big Ball of Mud is a defensible, rational choice when the
following hold.

- The system is small, short-lived, or explicitly disposable, a prototype meant
  to validate a hypothesis and be discarded within a fixed, honoured deadline.
  Foote and Yoder's own Throwaway Code sub-pattern names exactly this case, and
  the failure is not writing throwaway code, it is failing to throw it away.
- Exactly one person will ever read or change the code, for the entire life of
  the code, and that fact is verifiable rather than hoped for.
- The domain itself is genuinely unstable and poorly understood, so that any
  structure imposed today would almost certainly be the wrong structure next
  month, and the cost of guessing wrong exceeds the cost of staying flexible a
  while longer.
- The system sits behind a hard deadline with an existential consequence for
  missing it, a regulatory filing date, a one-time demo that decides funding,
  and the alternative to accepting mud is not shipping at all.
- The mud is deliberately, visibly contained. It lives in a script, a batch job,
  or a spike branch that nothing else in production depends on, and that
  boundary is enforced rather than assumed.

Tolerating it stops being defensible, and becomes the failure this entry warns
against, when any of the following hold.

- More than one team, or more than a small handful of people, must change the
  code regularly. Coordination cost grows faster than team size in an
  unstructured codebase, because there is no boundary to divide the work along.
- The system is expected to be long-lived, and "long-lived" in practice means
  anything past the tenure of the people who wrote it. Tacit knowledge about
  where the mud is safe to touch does not survive a team turnover.
- The system handles money, safety, health, or regulated personal data, where
  an unreviewable, untestable change path is itself a compliance and safety
  risk, independent of whether a bug has occurred yet.
- A specific area of the mud is on the critical path for every new feature, so
  that the coordination and comprehension tax is paid on every single change
  rather than occasionally.
- The team already knows the structure is wrong and is choosing not to fix it
  purely because nobody has been given the time, which is a resourcing failure
  wearing the costume of an engineering trade-off. Foote and Yoder's own
  observation, that architecture is treated as a luxury the schedule cannot
  afford, describes this case directly, and it is the case the whole pattern
  language exists to help a team recognise and escape.
- Testing a single piece of behaviour requires standing up the entire system,
  because no seam exists at which a smaller piece can be isolated. This is the
  most reliable operational symptom that the second list, not the first,
  applies, see dimension 11.

## 5. Structure

A Big Ball of Mud does not have participants in the sense a design pattern
does, because the entire point of the condition is the absence of assigned
roles. It is still useful to name the structural properties that are present
in every instance of it, because naming them is what lets a reader recognise
the pattern in an unfamiliar codebase.

- **Undifferentiated modules.** Files, classes, or services exist, but their
  boundaries do not correspond to any single responsibility. A file named for
  one concern routinely contains logic for several unrelated ones, because it
  was the easiest place to add the next thing.
- **Promiscuous shared state.** Data that should be private to one part of the
  system, a database table, a global variable, an in-memory cache, is read and
  written directly by many unrelated parts, with no owner and no interface
  mediating access.
- **Implicit, undocumented invariants.** Rules that must hold for the system to
  behave correctly exist only as tribal knowledge, "never call this function
  before that one," enforced by nothing but the discipline of whoever
  remembers.
- **No layering.** There is no consistent direction of dependency. Code that
  should sit at a low level, formatting a date, calls back up into code that
  should sit at a high level, sending a notification, because at the moment
  that call was written the two were adjacent in the same file.
- **Duplicated, drifted logic.** The same business rule is implemented more
  than once, in more than one place, because nobody could find the first
  implementation, or found it and judged it too entangled to reuse safely, and
  each copy has since drifted slightly out of agreement with the others.
- **A thin, load-bearing crust.** Under sustained pressure, teams stop trying
  to fix the interior and instead wrap the worst parts in a facade, an
  adapter, a "do not touch" comment, so that new code can be added without
  entering the mud directly. This crust is real structure, but it grows around
  the mud rather than replacing it, and it is itself the Sweeping It Under the
  Rug sub-pattern in physical form.

There is no product being created here in the sense the Gang of Four use the
term. The "structure" of a Big Ball of Mud is the absence of enforced
structure, everywhere data or control can flow, it eventually does.

## 6. ASCII structure diagram

```
   A healthy layered system                A big ball of mud

   +-----------------+                     +-----+   +-----+
   |   Presentation   |                     | Ord |---| Bil |
   +--------+---------+                     | ers |\ /| ling|
            | calls                         +-----+ X +-----+
   +--------v---------+                       |   / \    |
   |     Domain       |                       |  /   \   |
   +--------+---------+                     +-v-v-+ +-v--v+
            | calls                         | Ship| | Notif|
   +--------v---------+                     +-----+ +-----+
   |  Infrastructure   |                       ^  \    ^  /
   +--------+---------+                        |   \   | /
            | calls                          +-+----v--v-+
   +--------v---------+                       |global cfg |
   |     Database      |                       | & shared  |
   +-------------------+                       | mutable   |
                                                | state     |
   One direction. Each layer                   +-----------+
   depends only on the one below it.
                                              Every box can read
                                              and write every other
                                              box, and all of them
                                              share one mutable
                                              state blob. There is
                                              no direction left to
                                              draw an arrow in.
```

## 7. Dynamics

A layered or bounded system has a runtime call graph that mirrors its
compile-time module graph, a request enters at one edge and flows through a
small, predictable sequence of layers. A Big Ball of Mud has no such
correspondence. The runtime call graph of a single request can pass through
the same module several times, at different points in the sequence, because
no rule prevents a low-level helper from calling back into a high-level
service that itself later calls the same helper again.

```
Client       Orders module     Billing module     Shipping module   Global state
  |               |                   |                   |               |
  |-- place() --->|                   |                   |               |
  |               |-- write row ------------------------------------------>|
  |               |-- charge() ------>|                   |               |
  |               |                   |-- read cfg --------------------->|
  |               |                   |-- write ledger -----------------> |
  |               |                   |-- notifyShipping() ------------->|
  |               |                   |                   |<-- read -----|
  |               |                   |                   |-- ship() --->|
  |               |                   |<-- callback ------|               |
  |               |<-- ack -----------|                   |               |
  |               |-- read status  <--------------------------------------|
  |<-- response --|                   |                   |               |
  |               |                   |                   |               |

  Every module can both call and be called by every other module, and every
  module reads and writes the same shared state directly. There is no single
  direction a new reader can trust the flow to move in.
```

The observable runtime signature of this shape is that a single request's
call stack, if captured with a profiler, shows the same module names
appearing more than once, non-adjacently, and shows writes to shared state
interleaved between calls to modules that logically have nothing to do with
each other. A stack trace from a crash inside a Big Ball of Mud is
frequently the only accurate map of the system's true dependencies that
exists anywhere, because no diagram was ever kept current enough to match it.

## 8. Implementation variants

There is no correct implementation of an anti-pattern, so this dimension
instead names the recognisable shapes the mud tends to take, which differ by
what the shared coupling mechanism is.

**Shared database mud.** Multiple services or modules read and write the same
tables directly, with no service boundary around the schema. This is the most
common variant in systems that started as a single application and were later
split into deployable services without splitting the data layer, and it means
the services are not actually independent no matter how they are packaged,
because a schema change in one breaks the others silently.

**Shared mutable global state mud.** A single process holds module-level or
static state that many unrelated parts of the code read and write, common in
long-running server processes and in front-end applications before a
disciplined state-management layer was introduced.

**God-object mud.** A single class or module accretes methods for every
concern in the system because it was the first class created and every new
feature found it convenient to attach a method there rather than create a new
home. This variant concentrates the mud in one file rather than spreading it,
which paradoxically can look tidier in a directory listing while being just
as coupled.

**Copy-paste mud.** The same logic is duplicated across many call sites
because extracting a shared function would require agreeing on an interface
across teams that do not talk to each other, and copying three lines is
faster than that conversation. This variant is easy to mistake for the
opposite of tight coupling, since the copies are literally independent code,
but it is coupling by content rather than by reference, a change to the rule
must now be made in every copy correctly or the system silently disagrees
with itself.

**Configuration mud.** Behaviour is controlled by a sprawling, undocumented
set of feature flags and environment variables read directly wherever they
are needed, rather than through a typed configuration boundary, so the actual
behaviour of the system in any given environment can only be determined by
grepping for every read site.

**Framework-scaffolding mud.** A framework's generated directory structure,
models, views, controllers, is treated as if it were architecture. Every
new concern gets dropped into whichever folder its type most resembles, and
because the folders are organised by technical role rather than by business
capability, unrelated business concerns end up adjacent to each other inside
the same folder while related ones are scattered across it. This is the
variant Domain-Driven Design's bounded contexts and the modular monolith are
most directly aimed at correcting, see dimension 13.

## 9. Known production uses

Three independently sourced, named examples.

**ANTLR, JavaMail, the MongoDB Java Driver, and Undertow, studied empirically
for Big Ball of Mud structure.** David Baum, Jens Dietrich, Craig Anslow, and
Richard Muller, "Visualizing Design Erosion. How Big Balls of Mud are Made,"
presented at the IEEE Working Conference on Software Visualization (VISSOFT)
2018. The authors analysed the class-level dependency graphs of these four
real, widely used open-source Java projects, ranging from roughly 300 classes
in JavaMail to roughly 1,500 classes in Undertow, across multiple released
versions of each, and found circular, cross-cutting dependency clusters
involving several dozen classes in every one of the four systems, with the
clusters growing across successive releases rather than shrinking
(arXiv 1807.06136, verified 2026-08-02). This is a rare case of the pattern
being measured directly rather than only described anecdotally, and it
establishes that the mud is present, and worsens over time, even in mature,
actively maintained, widely depended-upon open-source libraries, not only in
obscure internal enterprise systems.

**Shopify's core Ruby on Rails monolith.** Shopify's own engineering team
published a public account of restructuring their main commerce platform,
describing it explicitly in terms of extracting components "from a big ball
of mud" and acknowledging that, after three years of the effort, "we still
have a considerable sized ball of mud within the app that has no structure
whatsoever." At the time of writing the monolith held on the order of 2.8
million lines of Ruby and half a million commits, and the team's response was
not a rewrite but a Domain-Driven-Design-guided extraction of 37 named
components with assigned ownership, carried out while the system stayed in
continuous production use handling the company's Black Friday and Cyber
Monday peak traffic. Philip Muller, "Under Deconstruction. The State of
Shopify's Monolith," Shopify Engineering blog, published 2020-09-16
(shopify.engineering/shopify-monolith, verified 2026-08-02).

**The general observation that monoliths default to this shape.** Martin
Fowler's article on the trade-offs between monolithic and microservice
architectures states, discussing why teams reach for microservices at all,
that although a well-modularised monolith is theoretically possible, in his
observed experience it is rare enough that "the Big Ball of Mud is most
common architectural pattern" among monolithic systems he has encountered.
Martin Fowler, "Microservice Trade-Offs" (martinfowler.com, verified
2026-08-02). This is offered here as a named, credentialed practitioner's
stated observation across many systems, not as a controlled study, and it is
labelled as such rather than as a measured fact.

## 10. Consequences

Positive, stated honestly as they are genuinely present in the short term
rather than invented for symmetry.

- Delivery speed is high in the near term, because no time is spent agreeing
  interfaces, drawing boundaries, or coordinating across teams before writing
  the next feature.
- The system can adapt to a requirement nobody anticipated without first
  needing to revise an architecture document or negotiate a boundary change,
  because there was no boundary constraining where the new code could go.
- Onboarding a single new contributor to make one small, local change can be
  fast, since there is often a nearby example of similar code to copy, even
  though onboarding that same person to make a large or structural change is
  the opposite.
- Nothing is over-engineered for a future that may never arrive, since no
  abstraction was built ahead of a proven need.

Negative.

- Change cost rises over time and eventually rises faster than feature value,
  because every new feature must be threaded through an increasing number of
  undocumented, implicit dependencies rather than through a small, stable
  interface.
- The system cannot be safely divided among more people or teams, because
  there is no boundary along which the work divides without every side
  needing to understand the other side's internals.
- Testing degrades from unit-level to system-level by necessity, because no
  seam exists at which a piece of behaviour can be isolated, which slows
  feedback loops and discourages writing tests at all, see dimension 11.
- Onboarding a new contributor to make anything beyond a trivial local change
  takes materially longer, because there is no map of the system that matches
  reality, only the code itself, read in full.
- Confidence in any given change degrades, because the blast radius of an
  edit cannot be determined from the code's structure, it can only be
  discovered empirically, which pushes teams toward the fear-driven
  conservatism of Keep It Working, further entrenching the mud.
- The empirical evidence in dimension 9 indicates the condition does not
  self-correct. Left alone, the coupling documented by Baum, Dietrich, Anslow,
  and Muller grew across releases rather than shrinking, in every one of the
  four systems they studied.

## 11. Failure modes and misuse

**The change-amplification failure.** Symptom. A request that should touch
one file requires editing code in six unrelated modules because the same
business rule was duplicated six times, and the team discovers only in
production that one copy was missed. Cause. Copy-paste mud, dimension 8, no
single owner for the rule. Fix. Locate every copy with a text search across
the whole repository, consolidate to one implementation behind a named
function, and replace every call site, verifying with a characterisation
test written before the consolidation begins, see dimension 14.

**The untestable core.** Symptom. Writing a unit test for one function
requires constructing half the application's runtime, a database connection,
several unrelated services, and specific rows of seed data, before the
function under test can even be called. Cause. No seam exists between the
function and its collaborators, because the collaborators are reached
through direct references or global state rather than through an injected or
mockable interface. Fix. Introduce a seam at the smallest possible point
using the Sprout Method or Sprout Class technique from Michael Feathers,
"Working Effectively with Legacy Code," Prentice Hall, 2004, chapter 2, "The
Legacy Code Change Algorithm," rather than attempting to make the whole
surrounding module testable at once.

**The fear-driven freeze.** Symptom. A known bug is left unfixed for months
because everyone who has looked at the surrounding code is afraid that
fixing it will silently break something else that depends on the current,
buggy behaviour. Cause. Keep It Working under a system with no test coverage
and no clear dependency boundaries means the team cannot distinguish a safe
change from an unsafe one, so they treat every change as unsafe. Fix. Add
characterisation tests that pin the current, even if wrong, behaviour before
touching anything, per Feathers' definition of legacy code as code without
tests, then change the behaviour deliberately with the new test asserting
the corrected output.

**The false modularity of folders.** Symptom. The codebase has a tidy
directory structure, services, models, controllers, and the team believes
this constitutes modularity, while any two files in services can still call
into each other's private state freely and frequently do. Cause.
Framework-scaffolding mud, dimension 8, folder structure mistaken for
architectural boundary. Fix. Distinguish physical file layout from an
enforced dependency boundary. A folder is not a module unless something,
a compiler, a linter rule, a build target, actually rejects a disallowed
import across it.

**The crust that outlives its purpose.** Symptom. A facade or adapter that
was originally introduced to isolate one bad area of the mud has itself
accumulated new, unrelated logic over several years, and is now as tangled
as the interior it was meant to protect the rest of the system from. Cause.
Sweeping It Under the Rug treated as a permanent fix rather than as a
temporary containment measure with an intended follow-up that never
happened. Fix. Treat every containment facade as carrying an explicit,
tracked debt item with an owner, not as closed work, and periodically audit
whether the facade itself has grown a second, smaller ball of mud inside it.

**Rewrite as the reflex answer.** Symptom. The team proposes a full rewrite
as the response to any of the above, on the theory that a fresh codebase
cannot inherit the old mud. Cause. Underestimating that the same
organisational and time pressures that produced the first mud ball are still
present and will act on the new codebase the same way, absent a structural
change to how work is prioritised, not merely a change to which files hold
the logic. Fix. Foote and Yoder's own sixth sub-pattern, Reconstruction, is
offered as a last resort specifically because a rewrite under unchanged
pressure tends to reproduce the same shape on a delay, see dimension 14 for
the incremental alternative that is preferred first.

## 12. Trade-off matrix

Compared against named alternatives that address the same underlying
problem, insufficient modular structure, each from a different angle.

| Force | Big Ball of Mud (tolerated) | Modular Monolith | Bounded Context decomposition (DDD) | Layered Architecture | Microservices | Hexagonal / Ports and Adapters |
|---|---|---|---|---|---|---|
| Delivery speed, early stage | Highest, no coordination overhead | High, some upfront boundary design | Medium, requires domain analysis first | Medium, requires layer discipline | Lowest early, highest coordination cost | Medium, requires defining ports up front |
| Change cost as system grows | Rises fastest, often superlinearly | Rises slowly, bounded by module contracts | Rises slowly, bounded by context contracts | Rises moderately, bounded by layer direction | Stays flatter per-service, rises at integration points | Rises slowly inside the core, isolated at adapters |
| Testability | Poor, no seams, tests need the whole system | Good, module boundaries are natural seams | Good, context boundary is the seam | Good, each layer testable with the one below mocked | Good per service, hard for cross-service flows | Very good, the core is testable with fake adapters |
| Team scalability | Poor past a handful of people | Good, one team per module | Good, one team per bounded context | Fair, layers do not map cleanly to teams | Good, one team per service, at operational cost | Fair, teams organise around the core, not adapters |
| Operational complexity | Low, one deployable | Low, one deployable | Low to medium, may still be one deployable | Low, one deployable | High, many deployables, network calls, observability tax | Low, one deployable |
| Refactorability | Very poor, structure resists safe change | Good | Good | Fair | Good within a service, poor across service boundaries once contracts calcify | Good |
| Risk of over-engineering | None | Low | Medium, requires real domain complexity to earn its cost | Low | High, if applied before the domain or scale requires it | Medium, ceremony can exceed the payoff for a simple domain |
| Suitability for a genuinely small, short-lived system | Good fit, if honestly disposable | Overkill | Overkill | Mild overkill | Severe overkill | Mild to moderate overkill |

Reading of the table. A tolerated Big Ball of Mud is the correct row only for
a system that is genuinely small or genuinely disposable, matching dimension
4. For everything else the table is an argument for paying some structural
cost earlier, and the honest reading of the empirical evidence in dimension
9 is that the cost of not paying it does not stay flat, it compounds.

## 13. Related and incompatible patterns

- **Bounded Context.** The primary Domain-Driven Design remedy. Where a Big
  Ball of Mud has no boundary at all, a Bounded Context draws an explicit one
  around a coherent piece of the domain and its own model, so that logic and
  terminology inside the boundary need not agree with logic and terminology
  outside it. Extracting bounded contexts from an existing mud ball, as the
  Shopify case in dimension 9 illustrates, is one of the most common
  practical uses of this pattern in industry.
- **Anticorruption Layer.** Directly composes with the escape path. When a new
  bounded context must talk to the remaining, unreconstructed mud, an
  anticorruption layer sits at that boundary and translates the mud's
  ambiguous, drifted concepts into the new context's clean model, so that the
  mud's mess does not leak across the newly drawn line.
- **Context Map.** A useful diagnostic tool applied to a mud ball before any
  extraction begins. Because a Big Ball of Mud has no honoured boundaries,
  drawing a context map of what boundaries actually, informally, exist in
  practice, even messy or overlapping ones, is often the first concrete step
  toward choosing where a real boundary should be drawn.
- **Core Domain and Supporting Subdomain.** Once a team decides to extract
  structure from a mud ball, these two patterns supply the prioritisation
  question, which of the tangled pieces is where the organisation's real
  competitive differentiation lives and deserves the first, most careful
  extraction, versus which pieces are supporting machinery that can be
  extracted more mechanically or even bought rather than built.
- **Strangler Fig.** The standard incremental technique for performing the
  extraction itself without a stop-the-world rewrite, new functionality is
  routed to a new, clean module while old functionality keeps running inside
  the mud until it is individually, gradually replaced. This is the practical
  mechanism behind dimension 14's preferred path out.
- **Spaghetti Code.** A closely related but distinct condition, see dimension
  1. Spaghetti code is a property of individual functions or files. It
  frequently co-occurs with a Big Ball of Mud and is one of its symptoms, but
  a system can have one without the other.
- **Layered Architecture and Hexagonal Architecture.** Directly incompatible
  in the sense that a system cannot simultaneously have a genuinely enforced
  layering or ports-and-adapters boundary and also be a true Big Ball of Mud.
  The presence of either pattern, actually enforced rather than merely
  aspired to, is definitionally the absence of this one. A codebase can,
  however, have a layered architecture on paper and a Big Ball of Mud in
  practice, when the layering is a convention nothing enforces, which is the
  false-modularity failure mode in dimension 11.

## 14. Refactoring path in and out

Because this is an anti-pattern rather than a design choice, "introducing" it
is not something to instruct. The more useful path in is recognising how a
system drifts into this state, since recognising the drift early is the
cheapest point at which to stop it.

Signals that a system is drifting toward a Big Ball of Mud, roughly in the
order they tend to appear.

1. A "just this once" direct database read or write from a module that does
   not own that data, justified by a deadline.
2. A second occurrence of the same shortcut, in a different module, justified
   by "that's how it's already done elsewhere in the codebase."
3. A shared mutable object, a config singleton, a session object, a cache,
   that more than two unrelated modules now depend on directly.
4. The team can no longer state, without opening the code, which module owns
   a given piece of business logic, because more than one module contains an
   implementation of it.
5. A new hire's first non-trivial change touches files in more than three
   unrelated top-level directories, because there was no single place the
   change could be made.

Each of these signals is cheap to reverse the day it appears and expensive to
reverse a year later, which is the whole argument of the pattern.

The refactoring path out, once a system is already a recognised Big Ball of
Mud, is deliberately incremental. A full rewrite is named explicitly in
dimension 11 as a common, understandable, and usually mistaken reflex.

1. Stop the growth first. Before extracting anything, adopt a rule that new
   code is not added directly into the mud, new features are built as, or
   routed through, a new module with an explicit boundary, even if that
   module currently has to call back into the mud to get anything done. This
   is the Strangler Fig technique applied at the level of new development.
2. Choose the first extraction target using Core Domain versus Supporting
   Subdomain reasoning, dimension 13, not by picking the piece that merely
   looks easiest. The easiest piece to extract is rarely the piece paying the
   most in ongoing change cost.
3. Before touching the chosen area's internals, write characterisation tests
   around its current, observable, external behaviour, per Michael Feathers,
   "Working Effectively with Legacy Code," Prentice Hall, 2004, chapter 13,
   "I Need to Make a Change, but I Don't Know What Tests to Write." These
   tests pin what the system actually does today, bugs included, so the
   extraction can be verified not to have silently changed behaviour.
4. Introduce a seam at the boundary of the chosen area using the smallest
   safe technique that applies, Sprout Method, Sprout Class, or Wrap Method,
   from the same source, chapter 8. The goal of this step is only to make the
   area callable through one, narrow, explicit interface, not yet to clean up
   its interior.
5. Route every caller of the old, direct access path through the new
   interface, one caller at a time, running the characterisation tests after
   each one. This step is the part most teams underestimate the size of,
   because the number of undocumented callers is exactly what the mud hid.
6. Once every caller goes through the interface, the area behind it can be
   restructured freely, since its only observable contract is now the
   interface, not its internals. This is the point at which an
   Anticorruption Layer, a proper Bounded Context, or an internal module
   boundary can be formalised with confidence that nothing outside the
   boundary depends on what is inside it.
7. Repeat from step two for the next highest-value area. There is no single
   endpoint at which the system stops being a Big Ball of Mud all at once,
   the goal is a monotonically shrinking mud with a monotonically growing set
   of properly bounded areas around it, which matches what Shopify's own
   account in dimension 9 describes as an ongoing, multi-year effort rather
   than a finished project.

## 15. Testing and verification

Testing code that lives inside a Big Ball of Mud is, structurally, the
hardest testing situation this repository's pattern families describe,
because the defining property of the mud, no isolated seams, is also the
defining precondition for cheap unit testing.

What is hard because of the pattern.

- A true unit test, exercising one function or class in isolation, is often
  not possible without first refactoring toward a seam, because the function
  under test reaches directly into shared state or calls sideways into
  unrelated modules that themselves reach into more shared state.
- Test setup cost dominates test-writing time. Building the fixtures needed to
  even reach the code under test, a populated database, a running dependent
  service, specific global state, frequently takes longer than writing the
  assertion that follows.
- Tests written against a mud ball tend to be brittle in the specific sense
  that an unrelated change elsewhere in the system, one that should have no
  effect on the behaviour under test, breaks the test anyway, because the two
  were coupled through shared state the test did not know to isolate.
- Flaky tests are common, because shared mutable state that different tests
  read and write concurrently or in an undetermined order produces
  order-dependent results.

Techniques that work despite the pattern.

- **Characterisation testing**, per Feathers, is the correct starting
  technique specifically because it does not require understanding the
  code's intended behaviour, only its actual current behaviour, which is the
  one thing that is always observable even in the most tangled system.
- **Golden master testing**, capturing a large, representative output from
  the current system and diffing future runs against it, is a coarse-grained
  variant of characterisation testing that suits areas too entangled to pin
  down function by function.
- **The Sprout Method and Sprout Class techniques**, introducing new, tested
  code at the edge of an untested area rather than trying to retrofit tests
  onto the untested area itself, let a team add coverage incrementally
  without a large, risky, up-front testing effort.
- **Approval or snapshot testing at a system boundary**, such as the HTTP
  response of an endpoint, is often more reliable than an internal unit test
  in a mud ball, precisely because it does not need the internal seams the
  system lacks, it only needs the outer boundary, which is usually more
  stable than the interior.
- **Contract tests at the point of a new extraction**, per dimension 14 step
  4, are the tests that eventually replace the coarse-grained approval tests,
  once a real interface exists to test against.

## 16. Observability signals

The absence of structure is itself something that can be measured and
tracked over time, which turns "is our system a Big Ball of Mud, and is it
getting worse" from an opinion into a number a team can watch.

What to record.

- **A dependency cycle count**, the number of modules or packages involved in
  circular import or call relationships, computed from static analysis of the
  dependency graph. This is exactly the metric Baum, Dietrich, Anslow, and
  Muller used to detect and visualise the pattern empirically in dimension 9,
  and it is the single most direct structural signal available.
- **A cross-module coupling count**, the number of distinct external modules
  each module directly imports from or is imported by, tracked as a
  distribution rather than an average, since the pattern's danger is
  concentrated in the handful of modules with unusually high counts, a
  handful an average would hide.
- **Change coupling**, computed from version control history, the frequency
  with which two files are modified together in the same commit despite
  having no declared dependency on each other. High, unexplained change
  coupling between unrelated-looking files is strong evidence of a hidden,
  undocumented dependency, the exact shape the pattern produces.
- **Test setup cost**, tracked as wall-clock time from test start to the
  first assertion, averaged per test file. A rising trend indicates growing
  fixture complexity, which correlates directly with growing entanglement.
- **A touch count per file per feature**, how many files, on average, a
  single feature ticket requires editing. A rising trend over successive
  quarters is the change-amplification failure from dimension 11 becoming
  visible in project management data rather than only in code review.

A healthy trend on a dashboard. Dependency cycle count and cross-module
coupling distribution are flat or shrinking over successive releases, average
touch-count per feature is flat or shrinking, and test setup time is flat.

A failing trend. Any of the above metrics climbing steadily, release over
release, with no corresponding metric showing extraction or boundary work in
progress to offset it. The empirical study in dimension 9 recorded exactly
this failing trend, cycle counts that grew across the released versions of
every system studied, in codebases nobody was deliberately trying to
untangle at the time.

## 17. Security and privacy implications

Unlike a design pattern chosen deliberately, the security implications of a
Big Ball of Mud are consistently negative, because the properties that make
it hard to maintain also make it hard to secure, and the two are the same
underlying property, no enforced boundary.

**Unbounded blast radius of a single defect.** Because any module can read
and write any other module's state, a vulnerability found in one part of the
system, an injection point, an insufficiently validated input, has no
structural containment. In a properly bounded system, a compromise of one
module is limited by the interface that module exposes to the rest of the
system. In a mud ball, the effective interface is "everything," because
nothing was ever restricted, which means an attacker who compromises any one
entry point inherits the same unbounded reach the code itself has.

**Undiscoverable access to sensitive data.** Because sensitive data, personal
information, payment details, credentials, is read directly wherever it is
convenient rather than through a single, auditable access path, answering the
basic compliance question "which code paths touch this field" cannot be
answered by inspection of an interface, it requires a full-text search of the
entire codebase and trust that the search caught every access, including
dynamic or reflective access the search tool cannot see. This directly
undermines data-protection obligations that require demonstrating where
regulated data flows, since the honest answer in a true mud ball is often
that nobody currently knows.

**Inconsistent enforcement of authorisation.** When the same business rule is
implemented in more than one place, dimension 8's copy-paste mud, an
authorisation check is frequently one of the rules that drifts between
copies. One code path correctly checks that a user is permitted to perform an
action, a second, newer code path added under time pressure by someone
unaware the first path existed, does not. This is not a hypothetical, it is
the direct, structural consequence of the change-amplification failure mode
in dimension 11 applied specifically to a security-relevant rule.

**Slower, riskier patching.** Because the system's blast radius and its
dependency graph are both unknown at any given time, per the fear-driven
freeze in dimension 11, a security patch that changes shared, widely
depended-upon code is exactly the kind of change teams are most reluctant to
make quickly, which lengthens the window between a vulnerability being known
and being fixed in the exact class of code, shared, foundational, unowned,
most likely to be affected by a serious one.

On privacy specifically, beyond the data-flow discoverability point above,
the pattern has no additional implications this entry can source, and
inventing further ones would be exactly the fabrication the sourcing
standard for this repository forbids.

## Code examples

The code below shows the pathology honestly, in three languages, rather than
showing a pattern to imitate. Each example builds a small order-processing
system the way a Big Ball of Mud actually accretes, a shared mutable state
object that three unrelated concerns, orders, billing, and shipping, all read
and write directly, with no interface between them. Each example is then
followed by the smallest possible seam, Sprout Method from dimension 14 and
15, extracted at one call site to show the first, minimal step of the escape
path without pretending to solve the whole system in one pass.

Java was considered and omitted. No Java toolchain, javac, was available in
this environment, and the shape of the pathology, shared mutable static
state reached directly by unrelated classes, would be a close copy of the
Python and TypeScript examples below rather than showing anything the other
two languages do not already demonstrate. Rust was considered and omitted for
a different reason, the borrow checker actively resists exactly the kind of
unsynchronised, promiscuous shared mutable access this pattern depends on,
so an honest Rust example would either need unsafe blocks to defeat the
compiler's own protection or would stop being a faithful illustration of the
pattern at all.

### Python

```python
STATE = {"orders": {}, "ledger": [], "shipments": {}}


def place_order(order_id, amount):
    STATE["orders"][order_id] = {"amount": amount, "paid": False}
    charge(order_id)


def charge(order_id):
    order = STATE["orders"][order_id]
    STATE["ledger"].append(order["amount"])
    order["paid"] = True
    if order["paid"]:
        ship(order_id)


def ship(order_id):
    STATE["shipments"][order_id] = "dispatched"
    STATE["orders"][order_id]["amount"] *= 1.0


if __name__ == "__main__":
    place_order("A1", 42.50)
    print(STATE["orders"], STATE["ledger"], STATE["shipments"])
```

The seam, extracting one collaborator behind a narrow function so it can be
tested and later replaced without touching the other two.

```python
def compute_ledger_entry(amount):
    return round(amount, 2)


def charge_v2(order_id, state):
    order = state["orders"][order_id]
    state["ledger"].append(compute_ledger_entry(order["amount"]))
    order["paid"] = True
```

### TypeScript

```typescript
type OrderState = {
  orders: Record<string, { amount: number; paid: boolean }>;
  ledger: number[];
  shipments: Record<string, string>;
};

const STATE: OrderState = { orders: {}, ledger: [], shipments: {} };

function placeOrder(orderId: string, amount: number): void {
  STATE.orders[orderId] = { amount, paid: false };
  charge(orderId);
}

function charge(orderId: string): void {
  const order = STATE.orders[orderId];
  STATE.ledger.push(order.amount);
  order.paid = true;
  if (order.paid) ship(orderId);
}

function ship(orderId: string): void {
  STATE.shipments[orderId] = "dispatched";
  STATE.orders[orderId].amount *= 1.0;
}

placeOrder("A1", 42.5);
console.log(STATE.orders, STATE.ledger, STATE.shipments);
```

The seam.

```typescript
function computeLedgerEntry(amount: number): number {
  return Math.round(amount * 100) / 100;
}

function chargeV2(orderId: string, state: OrderState): void {
  const order = state.orders[orderId];
  state.ledger.push(computeLedgerEntry(order.amount));
  order.paid = true;
}
```

### Go

```go
package main

import "fmt"

type State struct {
	orders    map[string]*Order
	ledger    []float64
	shipments map[string]string
}

type Order struct {
	amount float64
	paid   bool
}

func placeOrder(s *State, id string, amount float64) {
	s.orders[id] = &Order{amount: amount}
	charge(s, id)
}

func charge(s *State, id string) {
	order := s.orders[id]
	s.ledger = append(s.ledger, order.amount)
	order.paid = true
	if order.paid {
		ship(s, id)
	}
}

func ship(s *State, id string) {
	s.shipments[id] = "dispatched"
	s.orders[id].amount *= 1.0
}

func main() {
	state := &State{
		orders:    map[string]*Order{},
		ledger:    []float64{},
		shipments: map[string]string{},
	}
	placeOrder(state, "A1", 42.50)
	fmt.Println(state.orders, state.ledger, state.shipments)
}
```

The seam.

```go
func computeLedgerEntry(amount float64) float64 {
	return float64(int(amount*100+0.5)) / 100
}

func chargeV2(s *State, id string) {
	order := s.orders[id]
	s.ledger = append(s.ledger, computeLedgerEntry(order.amount))
	order.paid = true
}
```

## 18. References

1. Brian Foote and Joseph Yoder. "Big Ball of Mud." Technical Report
   WUCS-97-34, Department of Computer Science, Washington University in
   St. Louis. Presented at the Fourth Conference on Pattern Languages of
   Programs (PLoP '97 / EuroPLoP '97), Monticello, Illinois, September 1997.
   Later published as Chapter 29 in Neil Harrison, Brian Foote, and Hans
   Rohnert, editors, Pattern Languages of Program Design 4, Addison-Wesley,
   2000. https://hillside.net/plop/plop97/Proceedings/foote.pdf
   Verified 2026-08-02. Source of the pattern's origin, its publication
   venue, the six named sub-patterns, and the shantytown metaphor.
2. Brian Foote and Joseph Yoder. "Big Ball of Mud," mirrored full text.
   http://www.laputan.org/mud/mud.html
   Verified 2026-08-02. Cross-referenced against source 1 for the pattern's
   structure and sub-pattern names.
3. David Baum, Jens Dietrich, Craig Anslow, and Richard Muller. "Visualizing
   Design Erosion. How Big Balls of Mud are Made." IEEE Working Conference
   on Software Visualization (VISSOFT), 2018.
   https://arxiv.org/abs/1807.06136
   Verified 2026-08-02. Source of the empirical production-use finding for
   ANTLR, JavaMail, MongoDB Java Driver, and Undertow in dimension 9, and the
   dependency-cycle observability metric in dimension 16.
4. Philip Muller. "Under Deconstruction. The State of Shopify's Monolith."
   Shopify Engineering blog. Published 2020-09-16.
   https://shopify.engineering/shopify-monolith
   Verified 2026-08-02. Source of the Shopify production use in dimension 9.
5. Martin Fowler. "Microservice Trade-Offs."
   https://martinfowler.com/articles/microservice-trade-offs.html
   Verified 2026-08-02. Source of the practitioner observation quoted in
   dimension 9.
6. Michael Feathers. Working Effectively with Legacy Code. Prentice Hall,
   2004. ISBN 0-13-117705-2. Chapter 2, "The Legacy Code Change Algorithm,"
   Chapter 8, "How Do I Add a Feature," Chapter 13, "I Need to Make a Change,
   but I Don't Know What Tests to Write." Source of Sprout Method, Sprout
   Class, Wrap Method, and characterisation testing, applied throughout
   dimensions 11, 14, and 15.
7. DevIQ. "Big Ball of Mud."
   https://deviq.com/antipatterns/big-ball-of-mud/
   Verified 2026-08-02. Source, alongside item 8, for the informal
   secondary-usage aliases noted in dimension 1.
8. GeeksforGeeks. "Big Ball of Mud Anti-Pattern."
   https://www.geeksforgeeks.org/system-design/big-ball-of-mud-anti-pattern/
   Verified 2026-08-02. Source for the spaghetti-code-versus-architecture
   distinction discussed in dimension 1.
