---
name: Big Ball of Mud
slug: big-ball-of-mud
family: 18-anti-patterns
category: Anti-pattern
aliases: [Shantytown, Kitchen Sink Architecture, Distributed Big Ball of Mud]
first_described: "Foote, Yoder 1997"
maturity: canonical
related: [strangler-fig-application, bounded-context, god-object, spaghetti-code, lava-flow, layered-architecture, modular-monolith, technical-debt]
incompatible_with: [layered-architecture, hexagonal-architecture, bounded-context]
verified: 2026-08-02
---

# Big Ball of Mud

## 1. Name, aliases, and lineage

The canonical name is Big Ball of Mud, capitalized as a proper pattern name in
the tradition of the pattern-language community that coined it. Brian Foote
and Joseph Yoder, then at the Department of Computer Science, University of
Illinois at Urbana-Champaign, first presented it at the Fourth Conference on
Pattern Languages of Programs, PLoP '97 and its European sibling EuroPLoP '97,
in Monticello, Illinois, September 1997, and issued it as Washington
University technical report WUCS-97-34. It was later collected as chapter 29
of *Pattern Languages of Program Design 4*, edited by Neil Harrison, Brian
Foote, and Hans Rohnert, Addison-Wesley, 2000
([Foote and Yoder, "Big Ball of Mud"](http://www.laputan.org/mud/mud.html),
verified 2026-08-02). The paper opens by naming the target directly, "A BIG
BALL OF MUD is a casually, even haphazardly, structured system," and it goes
on to argue this is, in its own words, "this most frequently deployed of
software architectures" (same source, verified 2026-08-02).

Foote and Yoder use Shantytown as an alias inside the same paper, framing an
undisciplined system as a slum that grew one shack at a time rather than a
city that was planned. They also list Spaghetti Code as an alias for the
system-level shape they describe. That naming choice collides with a separate,
more narrowly scoped anti-pattern of the same name. William Brown, Raphael
Malveau, Hays "Skip" McCormick, and Thomas Mowbray, in *AntiPatterns,
Refactoring Software, Architectures, and Projects in Crisis*, Wiley, 1998,
chapter 5, "Software Development AntiPatterns," define Spaghetti Code as a
code-level anti-pattern about control flow specifically, procedural code whose
jumps and branches tangle into a shape with no discernible structure, most
associated in memory with unstructured GOTO-driven Basic and Fortran, and with
early object-oriented code that never bothered to use polymorphism where a
switch statement would do. The same chapter of the same book separately
defines Lava Flow, dead or frozen code from an earlier prototyping phase that
nobody dares delete because nobody remembers why it exists or what depends on
it, and The Blob, a single class or module that accretes so much
responsibility that the rest of the system becomes an inert collection of data
holders orbiting it. This entry treats Big Ball of Mud as the systemic,
architecture-level anti-pattern, the absence of any perceivable
decomposition across an entire codebase, and treats Spaghetti Code, Lava Flow,
and The Blob as related but narrower anti-patterns that frequently co-occur
inside a Big Ball of Mud without being identical to it. A single tangled
function is Spaghetti Code. A single overloaded class is The Blob, a term
that itself echoes Arthur Riel's earlier God Class, described in *Object-
Oriented Design Heuristics*, Addison-Wesley, 1996, heuristic 3.2, which says
plainly, "Do not create god classes/objects in your system. Be very suspicious
of an abstraction whose name contains Driver, Manager, System, or Subsystem"
([Riel's heuristics, plain-text mirror](https://www2.ccs.neu.edu/research/demeter/related-work/riel/heuristics2.txt),
verified 2026-08-02). A whole application with no seams anywhere in it, built
from many such classes and functions with no layering, no module boundaries,
and no owner able to describe its shape, is a Big Ball of Mud.

A later alias, Distributed Big Ball of Mud, was coined for the failure mode
that appears when a team decomposes a monolith into services but carries the
same absence of boundaries across the network. Ben Morris uses the phrase
directly, "instead of autonomous services collaborating to deliver business
processes you have a haphazard set of components locked together in a
distributed monolith"
([Morris, "Microservices, REST and the Distributed Big Ball of Mud," 2015](https://www.ben-morris.com/microservices-rest-and-the-distributed-big-ball-of-mud/),
verified 2026-08-02). Dimension 8 covers this variant in full. Foote and
Yoder's original title never claimed the anti-pattern was new when they named
it. Their contribution was to name a shape everyone already recognized, and to
argue, controversially at the time, that the shape is a rational outcome of
real forces rather than a simple failure of competence.

## 2. Problem and context

A reader can recognize this problem without ever hearing the pattern's name.
Open a file in the codebase and it does five unrelated things. A function that
is supposed to validate an order also charges a credit card, writes to three
tables, and formats an email. A class named `Manager` or `Helper` or
`Utils` has grown to thousands of lines because every new feature found it
convenient to add one more method there rather than create a new type. Global
mutable state, a static map, a module-level dictionary, a singleton with a
public field, is read and written from a dozen unrelated call sites, so no
one can predict what a given change will affect without running the whole
system and watching what breaks. Database tables are read directly by three
different subsystems that were never told about each other, so the schema is
the de facto integration layer and nobody can change a column name without a
company-wide search. New engineers spend their first weeks not learning the
domain but learning which functions are safe to call and which ones are land
mines, because the compiler and the file layout give no hints about either.

The context in which this problem arises is not a context of incompetence, and
treating it that way is the single most common mistake made about this
anti-pattern. Foote and Yoder are explicit that they are "in favor of good
architecture" while also refusing to blame the practitioners who build muddy
systems, because the pressures that produce mud are the ordinary pressures of
building working software under a deadline
([Foote and Yoder](http://www.laputan.org/mud/mud.html), verified
2026-08-02). A system becomes a Big Ball of Mud the same way a path becomes a
worn dirt track across a lawn. Nobody decided to build it there. Enough people
took the shortest route enough times that the shortcut became the structure.
Concretely, the context has a repeatable shape. The team started small, with
one or two people who could hold the whole system in their heads, so an
explicit architecture felt like overhead against the actual, immediate cost of
shipping. Requirements arrived incrementally and unpredictably, so any upfront
module boundary drawn on day one turned out to be wrong by day ninety, and
each wrong boundary that had to be worked around taught the team, correctly in
the moment, that boundaries cost more than they returned. The system succeeded,
which is the twist that makes this pattern painful rather than merely sloppy.
A system that fails gets rewritten or discarded before its mud matters. A
system that succeeds keeps growing, keeps accumulating engineers who never saw
the original small system, and keeps outliving every engineer's ability to
hold its whole shape in memory, which is exactly the property that mattered
least on day one and matters most on day one thousand.

## 3. Forces

The pattern balances the following competing pressures, several of them
identified directly by Foote and Yoder as the forces that produce mud in
practice.

- **Time pressure against upfront design.** Favors mud. A deadline rewards the
  code that ships this sprint over the code that will be easy to change next
  year, and next year's cost is, from inside this sprint, both uncertain and
  somebody else's problem.
- **Cost of architecture against the size of the immediate problem.** Favors
  mud early, and reverses later. A five hundred line prototype does not need a
  layered architecture, and building one anyway is itself a form of waste, the
  mirror-image mistake of speculative generality. The same investment on a
  five hundred thousand line system that will run for a decade is not
  optional.
- **Inexperience with the problem domain.** Favors mud. A team drawing module
  boundaries before it understands the domain is drawing them from a guess,
  and Foote and Yoder note plainly that architectural clarity usually arrives
  only after the domain is understood, by which time a great deal of code has
  already been written against the earlier, wrong understanding.
- **Coupling and consistency at small scale versus large scale.** A tightly
  coupled system with everything reachable from everything else is, for a
  three-person team working in one shared mental model, arguably the fastest
  system to change, because there is no boundary to negotiate and no
  interface to keep stable. The same coupling becomes the dominant cost the
  moment a second team, or a fifth developer, needs to change the system
  without first phoning everyone else who might be affected.
- **Cognitive load, deferred.** Sacrificed, but not immediately. This is a
  judgment about degree, not a sourced fact, the entropy a Big Ball of Mud
  accumulates does not bill the team that incurs it, it bills whichever team
  is still maintaining the system months or years later, which is the same
  asymmetry Ward Cunningham described when he introduced the debt metaphor for
  imperfect code, writing that "every minute spent on not-quite-right code
  counts as interest on that debt"
  ([Cunningham, "The WyCash Portfolio Management System," OOPSLA '92
  experience report](http://c2.com/doc/oopsla92.html), verified 2026-08-02).
- **Entropy under continuing change.** An academic force, not merely a
  practitioner's complaint. Manny Lehman's empirical study of large systems,
  grounded in IBM's OS/360, produced the Law of Continuing Change, that a
  program in active use must keep changing or become progressively less
  useful, and the Law of Increasing Complexity, that as a program evolves its
  complexity increases unless work is explicitly done to reduce it (M.M.
  Lehman, "Programs, Life Cycles, and Laws of Software Evolution,"
  *Proceedings of the IEEE*, Vol. 68, No. 9, September 1980, pp.
  1060-1076). Lehman's laws describe the default trajectory of any evolving
  system absent counter-pressure, and a Big Ball of Mud is what that default
  trajectory looks like when the counter-pressure, deliberate architectural
  maintenance, never arrives.
- **Team topology and communication cost.** Sacrificed as the system and team
  grow. A shared, undifferentiated codebase demands that every change be
  understood in the context of the whole, which does not scale past the
  number of relationships one team can hold informally.

No pattern gives up nothing, and this one gives up long-run changeability and
predictability in exchange for something real, the lowest possible short-run
cost of the very next feature, paid for by whichever engineer has to touch the
system next.

## 4. Applicability and non-applicability

There is a narrow, honest case for tolerating this shape on purpose, and a far
larger case against it. Both lists matter, because treating every instance of
this pattern as an unqualified mistake is itself a mistake that leads teams to
over-invest in architecture for code that will never need it.

Tolerating a Big Ball of Mud is defensible when the following hold.

- The system is a genuine, time-boxed spike or prototype meant to answer a
  question, not to run in production, and the team has a real plan and a real
  date for discarding or rewriting it. Foote and Yoder's own Throwaway Code
  pattern names this case directly, warning in the same breath that "the real
  problem with throwaway code comes when it isn't thrown away"
  ([Foote and Yoder](http://www.laputan.org/mud/mud.html), verified
  2026-08-02).
- The system's entire lifetime is measured in weeks, a one-off migration
  script, a conference demo, a load-testing rig that nobody will touch
  again after the numbers are collected.
- Exactly one person will ever read or change the code, that person already
  holds the whole shape in their head, and no plan exists to hand it to
  anyone else.
- The domain is still being discovered and every module boundary drawn today
  would be a guess. In this narrow case, deliberately writing undifferentiated
  code while treating the exploration itself as the deliverable, then
  refactoring hard once the domain is understood, can beat drawing confident
  boundaries around a misunderstanding.

Do NOT tolerate this pattern, and the reason matters more than the rule.

- **The system is expected to outlive the person who understands it.** The
  entire value of an architecture is that it lets someone who was not present
  for the accretion still reason about the system. A Big Ball of Mud fails
  that test by definition, and a system anyone expects to run for years, to
  be handed to a new hire, or to survive its original author leaving, cannot
  afford it.
- **More than a handful of engineers must change the system concurrently.**
  Coupling that costs nothing to a lone developer costs real, measurable
  coordination time to five, and grows worse than linearly as the team grows,
  because the number of undocumented relationships between parts grows with
  the number of people who might touch any of them.
- **The domain is regulated, safety-critical, or handles money or personal
  data at scale.** An undifferentiated system has no natural place to enforce
  an invariant, audit an access, or contain a failure, which is precisely the
  property a regulator, an auditor, or an attacker will test first. See
  dimension 17.
- **The team plans to decompose into services later.** Extracting a service
  from a system that has no internal boundaries does not create a boundary,
  it moves the same tangle onto the network and adds latency, partial
  failure, and versioning to it, producing the Distributed Big Ball of Mud
  variant covered in dimension 8. Boundaries must exist inside the monolith
  before they can be cut along a network edge.
- **The team has already noticed the symptoms in dimension 11 and is choosing
  to do nothing.** Recognizing the pattern and continuing to add features
  without any counter-investment is the one case Foote and Yoder do not
  defend, distinct from consciously choosing it for a bounded, honest reason.
- **A rewrite is being proposed as the fix with no containment plan.**
  Reconstruction is a real option in the source pattern language, but Joel
  Spolsky's account of Netscape choosing a full rewrite of its browser, and
  the three-year gap it opened for competitors, is the standard citable
  warning against reaching for it reflexively
  ([Spolsky, "Things You Should Never Do, Part I," Joel on Software, 6
  April 2000](https://www.joelonsoftware.com/2000/04/06/things-you-should-never-do-part-i/),
  verified 2026-08-02). See dimension 9 and dimension 14.

## 5. Structure

A Big Ball of Mud is defined by the absence of structure rather than by a
positive shape, which makes it unusual among the patterns in this catalogue,
but the absence itself has a recognizable anatomy, three participants, named
by the role each plays in the mess rather than by any class the codebase
actually declares.

- **Undifferentiated modules.** Files, classes, or services that were named
  for a feature or a screen rather than for a domain concept, and that each
  accumulate whatever logic happened to be convenient to add there. No module
  boundary maps to a boundary in the domain, so a change to one business rule
  can require edits scattered across files that share no obvious relationship
  except that someone once found it easiest to put the code there.
- **Pervasive, ambiently shared state.** A database schema, a set of global
  variables, a session object, or a widely imported "context" type that every
  module reads and writes directly, with no accessor, no validation boundary,
  and no owner. This is the connective tissue of the mud, it is what lets a
  change in one undifferentiated module silently break another one that never
  imported it.
- **An untraceable call graph.** Functions and methods that call each other
  across the whole system with no layering, so that tracing what a single
  user action actually does requires reading the running system rather than
  reading the architecture, because there is no architecture to read. Any
  attempt to draw a dependency diagram of a genuine Big Ball of Mud produces,
  reliably, a graph with far more edges than a reader can follow, which is
  itself diagnostic. See dimension 6.

The relationships between these three participants are the pathology.
Undifferentiated modules read and write ambiently shared state without going
through any of the others, so two modules that have never heard of each other
still depend on each other through the state they both touch. The call graph
crosses whatever notional layers exist, so a routine meant to sit at the
bottom of a stack, a database access function, say, ends up calling upward
into business logic or even presentation formatting, because at some point
that was the fastest way to get a feature out. There is no fourth
participant, a Coordinator or a Facade, because the defining property of this
anti-pattern is precisely that no participant was ever assigned the job of
keeping the others honest.

## 6. ASCII structure diagram

```
   Big Ball of Mud, the shape a dependency graph actually draws

   +------------+      +------------+      +------------+
   |  Screen A  |<---->|  Screen B  |<---->|  Screen C  |
   |  handler   |      |  handler   |      |  handler   |
   +-----+------+      +-----+------+      +-----+------+
         |  \                | \                  |  \
         |   \               |  \                 |   \
         v    v               v   v                v    v
   +------------------------------------------------------+
   |         Shared Mutable State  (globals, session,      |
   |         a "Manager"/"Utils" class, a giant table)     |
   +------------------------------------------------------+
         ^    ^               ^   ^                ^    ^
         |   /                |  /                 |   /
         |  /                 | /                  |  /
   +-----+------+      +-----+------+      +-----+------+
   |  Data       |<---->|  Email      |<---->|  Reporting |
   |  access fn  |      |  sender fn  |      |  job       |
   +------------+      +------------+      +------------+

   No layer is one-directional. Every box can reach every other
   box, directly or through the shared state box. There is no
   box whose job is to keep the others from doing that.

   For contrast, a layered system with the same six responsibilities.

   Presentation  -->  Application  -->  Domain  -->  Data access
        (calls flow one direction only; nothing calls upward)
```

## 7. Dynamics

The runtime behavior of a Big Ball of Mud is not the interesting dynamic, a
tangled system still executes correctly most of the time, that is exactly why
it survives. The interesting dynamic is how it accretes across calendar time,
one feature at a time, which is the pattern Foote and Yoder name Piecemeal
Growth. Their own instruction for it is blunt, "incrementally address forces
that encourage change and growth"
([Foote and Yoder](http://www.laputan.org/mud/mud.html), verified
2026-08-02), which describes both the healthy version of iterative
development and the unhealthy version this entry is about, the two are
distinguished only by whether anything is done to consolidate the structure
as it grows.

```
Sequence, repeated many times over the life of a codebase.

Product     Engineer                     Existing code
  |             |                              |
  |-- feature -->|                              |
  |             |-- find the nearest place ---->|
  |             |   that can be edited to       |
  |             |   produce the behavior         |
  |             |<-- shortest path found -------|
  |             |-- add a branch, a new field,   |
  |             |   a new call into shared state |
  |             |------------------------------->|
  |             |-- ship, deadline met -->|      |
  |             |                              |
  |         (structure of "existing code" is now
  |          one tangle wider than before; no
  |          step in this sequence revisits it)
  |             |                              |
  ~~~~ repeat for the next feature request ~~~~
```

Two properties of this loop matter. First, each individual step is locally
rational, the nearest edit point genuinely is the fastest way to ship the
next feature, which is why blaming any single commit misses the point.
Second, nothing in the loop is self-correcting, unlike a stack that overflows
or a queue that backs up, an accreting tangle produces no error, no alert, and
no test failure by default, because the code keeps working. Foote and Yoder's
companion pattern Keep It Working captures the reason nobody stops to fix it
even once it is noticed, "maintenance needs have accumulated, but an overhaul
is unwise, since you might break the system" (same source, verified
2026-08-02). The system's own continued success is what protects its
structure from ever being challenged, until the cost of the next feature
stops being locally rational too, which is the moment teams start reaching
for the Sweeping It Under the Rug and Reconstruction strategies covered in
dimension 14.

## 8. Implementation variants

**Procedural spaghetti.** No classes worth the name, a script or a set of
top-level functions that read and write shared globals directly, with control
flow that jumps between concerns, validation embedded inside a persistence
function, a side effect embedded inside a formatter. This is the variant
closest to Brown, Malveau, McCormick, and Mowbray's narrower Spaghetti Code
anti-pattern, and it is the easiest variant to spot because a reader can see
the tangle in a single file. See the Python example below.

**The god object, or Blob, variant.** One class, frequently named Manager,
Service, Engine, or System, accretes so much unrelated responsibility that
the rest of the codebase becomes thin data holders orbiting it. Riel's advice
to be "very suspicious of an abstraction whose name contains Driver, Manager,
System, or Subsystem" is aimed directly at this shape
([Riel's heuristics](https://www2.ccs.neu.edu/research/demeter/related-work/riel/heuristics2.txt),
verified 2026-08-02). See the TypeScript example below, where a single
`StoreApp` class owns pricing, inventory, notification, and auditing at once.

**Erosion inside a layered architecture.** The team drew layers, presentation,
application, domain, data access, on a whiteboard, and the first few modules
respected them. Under deadline pressure a controller starts calling the
database directly to avoid a round trip through the domain layer, once, for
one urgent fix, and the shortcut is never revisited. Repeated a hundred
times, the layer diagram survives in a design document that no longer
describes the actual dependency graph. This variant is the most dangerous of
the four, because the presence of layer names in the code gives false
confidence that the layering is real.

**The database as the integration layer.** Several notionally separate
subsystems, sometimes even owned by different teams, are integrated only
through direct reads and writes against a shared set of tables, with no
service boundary and no contract other than the schema. Any of those
subsystems can be broken by a column rename made by a team that has never
heard of the others. This variant is common in older enterprise systems
where the database predates the applications that grew up around it.

**Copy-paste proliferation.** Instead of one god object, dozens of near-
identical modules, each copied from the last time a similar feature was
needed and then patched independently. There is no single tangled center to
point at, the mud is spread thin across the whole codebase in the form of
duplicated, independently drifting logic that must now be fixed in every copy
whenever a shared bug is found.

**Distributed Big Ball of Mud.** The variant that appears after a monolith is
decomposed into services without first drawing real boundaries inside it.
Services call each other synchronously and circularly, share a database
across service ownership lines, and carry no clear contract for who owns
which piece of business logic, so the operational cost of a monolith, an
unpredictable blast radius from any single change, returns with the added
costs of network latency, partial failure, and independent deployment
schedules that must now stay compatible with each other. Ben Morris's
description of a "haphazard set of components locked together in a
distributed monolith" names exactly this outcome
([Morris](https://www.ben-morris.com/microservices-rest-and-the-distributed-big-ball-of-mud/),
verified 2026-08-02). See the Go example below, where a single handler
function inlines request parsing, pricing, inventory mutation, and
notification, the shape a service takes on its way toward this variant if
the same discipline that produced a monolithic Big Ball of Mud is applied one
service at a time.

## 9. Known production uses

Because this is an anti-pattern rather than a design choice a team announces
in its documentation, production uses are documented mostly through the
retrospective accounts of the teams that lived inside them and the empirical
studies that measured them from the outside, rather than through a vendor's
own architecture guide. Four independently sourced accounts follow.

**Netscape Navigator, mid-to-late 1990s.** Joel Spolsky's widely read account
of Netscape's decision to rewrite its browser from scratch, rather than
continue evolving the existing C++ codebase, describes exactly the trap this
entry warns against in dimension 4, code that looks messy from the outside
usually embeds years of accumulated, hard-won knowledge about real-world edge
cases, and discarding it in a full rewrite throws that knowledge away along
with the mess. Spolsky documents that the resulting rewrite opened a gap of
roughly three years between shippable releases, a gap competitors used to
take the market Netscape had led
([Spolsky, "Things You Should Never Do, Part I," 6 April 2000](https://www.joelonsoftware.com/2000/04/06/things-you-should-never-do-part-i/),
verified 2026-08-02). This is a production account of the Reconstruction
strategy from dimension 14 applied without the containment discipline the
strategy needs to succeed.

**Mozilla, the open-sourced successor codebase, studied empirically.** Alan
MacCormack, John Rusnak, and Carliss Baldwin used design structure matrices to
compare the dependency structure of the Linux kernel against Mozilla across
Mozilla's own history, including the purposeful redesign the Mozilla project
undertook specifically to become more modular. Their published result found
"significant differences in structure" between the two systems, with Linux
exhibiting a markedly more modular architecture, and traced how Mozilla's own
deliberate redesign effort moved its measured coupling in the direction of
Linux's
([MacCormack, Rusnak, and Baldwin, "Exploring the Structure of Complex
Software Designs, An Empirical Study of Open Source and Proprietary Code,"
*Management Science*, Vol. 52, No. 7, 2006, pp. 1015-1030, working paper
PDF](https://www.hbs.edu/ris/Publication%20Files/05-016.pdf), verified
2026-08-02). This is the rare case of a Big Ball of Mud being measured, not
just described, and of a team's deliberate decoupling effort being measured
against it.

**Amazon's Obidos application, pre-2001.** In an interview published in ACM
Queue, Amazon's then chief technology officer Werner Vogels described the
company's original web application, named Obidos, as an architecture that
"evolved to hold all the business logic, all the display logic, and all the
functionality" behind a single web-facing application talking to a database
([Jim Gray, "A Conversation with Werner Vogels," *ACM Queue*, Vol. 4, No. 4,
May 2006](https://queue.acm.org/detail.cfm?id=1142065), verified
2026-08-02). Amazon's well documented response, mandating that every internal
capability be exposed only as a service with a published interface, and
retiring Obidos entirely by 2006, is one of the clearest publicly described
examples of the Reconstruction and re-layering strategies in dimension 14
being applied deliberately, at scale, over years rather than as an emergency
rewrite.

**Shopify's core Ruby on Rails monolith, documented 2019.** Kirsten Westeinde,
writing on the Shopify Engineering blog, described the state of the
company's central monolith after roughly a decade and more than a thousand
contributing developers, "all of these distinct functionalities were built
into the same codebase with no boundaries between them," with
"functionally distinguishable aspects" left "interwoven, rather than
containing architecturally separate components," to the point that "making a
seemingly innocuous change could trigger a cascade of unrelated test
failures"
([Westeinde, "Deconstructing the Monolith, Designing Software that
Maximizes Developer Productivity," Shopify Engineering, 21 February
2019](https://shopify.engineering/deconstructing-monolith-designing-software-maximizes-developer-productivity),
verified 2026-08-02). Shopify's chosen fix, imposing component boundaries
inside the same deployable rather than splitting into services, is the
modular monolith strategy referenced in dimension 13, and stands as a
production counterpoint to the assumption that the only exit from this
pattern is a rewrite or a service split.

## 10. Consequences

Positive, stated honestly and without exaggeration.

- The cheapest possible unit cost for the very next small feature, for as
  long as the codebase and team stay small enough for one person to hold the
  whole shape in mind.
- Zero upfront design cost, which is a genuine advantage for a true
  throwaway prototype whose entire value is answering a question quickly.
- No premature boundary to be wrong about, a system with no structure cannot
  suffer from having drawn its module lines in the wrong place, because it
  never drew any.

Negative.

- Every change carries an unbounded, unpredictable blast radius, so the cost
  of a "small" feature grows without limit as the system ages, exactly the
  opposite of what piecemeal, deadline-driven development was trying to
  achieve.
- New engineers cannot safely change the system without first acquiring
  tribal knowledge that exists nowhere in the code, which makes onboarding
  slow and error-prone and concentrates risk in whichever few people already
  hold that knowledge.
- Testing is expensive and incomplete by construction, because there are no
  seams at which a unit test can isolate one part of the system from the
  rest. See dimension 15.
- The system resists almost every later architectural intervention, layering,
  service extraction, ownership division along team lines, because all of
  them assume boundaries the codebase does not have, so the fix generally
  costs more, later, than the original architecture would have cost up
  front, which is the debt-with-interest framing Cunningham introduced.
- The pattern is self-reinforcing, the harder the system is to change safely,
  the more attractive the next shortcut becomes relative to the alternative
  of understanding the existing tangle first, which accelerates rather than
  slows the accretion described in dimension 7.

## 11. Failure modes and misuse

**The onboarding cliff.** Symptom. A new engineer's first non-trivial change
takes weeks rather than days, and produces a regression in a part of the
system the change never mentioned. Cause. There is no module boundary that
limits the blast radius of a change, so correctness depends on knowledge the
new engineer has not yet acquired. Fix. Introduce seams incrementally around
the area being touched, per dimension 14, rather than attempting to document
the whole tangle, which goes stale immediately.

**The shotgun-surgery bug fix.** Symptom. A single logical fix requires
touching a dozen unrelated files, and the pull request is rejected twice
because the reviewer keeps finding one more place the same logic was
duplicated. Cause. Copy-paste proliferation or ambiently shared state means
the same rule is encoded in more than one place, with no single owner. Fix.
Consolidate the duplicated rule behind one function or module before making
the actual change, which is Extract Function followed by Introduce
Parameter Object in the refactoring vocabulary, then make the change once.

**The regression nobody can explain.** Symptom. A change to an apparently
unrelated screen breaks a report or an email that no test covers, and the
root cause turns out to be a shared global variable or table column that both
features happened to touch. Cause. Pervasive shared mutable state with no
access boundary. Fix. Wrap the shared state behind an explicit interface with
its own tests, even before attempting to split it apart, so the next change
through that interface is at least visible in a diff.

**The rewrite that recreates the mud.** Symptom. A team declares a full
rewrite, ships a cleaner version eighteen months later, and within a year the
new system exhibits the same symptoms as the old one. Cause. The rewrite
replaced the code but not the organizational forces from dimension 3, the
same deadline pressure, the same absence of an owner for architecture, that
produced the original tangle produces a second one on a fresh, initially
clean canvas. Fix. Pair any rewrite with an explicit, named owner for the
architecture and an explicit definition of what a boundary violation looks
like, enforced the same way tests are enforced, not merely written down once.

**Sweeping without ever coming back.** Symptom. A quarantine layer, an
adapter class wrapped around the worst part of the mud so the rest of the
system does not have to touch it directly, is added with a comment that says
it is temporary, and is still there, load-bearing, five years later, with the
comment unchanged. Cause. Foote and Yoder's own Sweeping It Under the Rug
pattern is a legitimate, honest stopgap, "if you can't easily make a mess go
away, at least cordon it off"
([Foote and Yoder](http://www.laputan.org/mud/mud.html), verified
2026-08-02), but a stopgap with no scheduled follow-up is functionally a
permanent decision made without anyone deciding it. Fix. Track the
quarantine as an explicit, dated item, not a comment, and revisit it on a
cadence, the same discipline dimension 16 recommends for measuring the mud
directly rather than trusting anyone's memory of intending to fix it.

**The distributed mud that looked like a fix.** Symptom. A monolith is split
into a dozen services, and the team's velocity gets worse, not better,
because a single feature now requires coordinated deploys across six of
them, with circular calls between services that both, incorrectly, believe
they own the same piece of business logic. Cause. Service boundaries were
drawn along team or deployment convenience rather than along real domain
seams, reproducing the Big Ball of Mud's absence of structure across process
and network boundaries instead of removing it, exactly the Distributed Big
Ball of Mud variant from dimension 8. Fix. Treat the service boundaries as a
hypothesis to test against the domain, using the Bounded Context exercise
from Domain-Driven Design before cutting a network boundary, not after.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3. The
alternatives are the shapes a team could choose instead of an undisciplined
monolith, not strawmen.

| Force | Big Ball of Mud | Layered Architecture | Modular Monolith | Microservices (well-bounded) | Strangler Fig (in transition) |
|---|---|---|---|---|---|
| Short-run feature cost, small team | Lowest, no boundary to negotiate | Higher, must respect layer direction | Higher, must respect module boundary | Highest, must design a service contract | Highest during transition, two systems live at once |
| Long-run feature cost as system grows | Grows without bound | Grows slowly if layers are respected | Grows slowly, bounded by module | Bounded per service, coordination cost across services | Falls over time as the legacy shrinks |
| Onboarding a new engineer | Slow, requires tribal knowledge | Faster, layer names orient the reader | Faster, module names map to domain | Fastest per service, hardest to see the whole | Mixed, depends on which side is touched |
| Blast radius of a typical change | Unbounded | Limited to the touched layer, mostly | Limited to the touched module | Limited to the touched service | Shrinking, contained to the strangled slice |
| Testability | Poor, no seams | Good at layer boundaries | Good at module boundaries | Good per service, weak across services | Improves as characterization tests accumulate |
| Operational cost | Low, one deployable | Low, one deployable | Low, one deployable | High, many deployables, network calls | Temporarily higher, two systems to run |
| Risk of introducing this pattern by mistake | Not applicable, it is the thing itself | Real, if layers erode under pressure | Lower, module boundaries are enforced in code | Real, at the network level, see dimension 8 | Real, if the new code repeats the old habits |
| Suits a genuine throwaway prototype | Yes, cheapest honest choice | Overkill | Overkill | Overkill | Not applicable, nothing to strangle yet |

Reading of the table. A Big Ball of Mud wins on exactly one axis, the cost of
the very next change on a small system, and loses on every axis that matters
once the system or the team grows. A layered architecture and a modular
monolith both trade a small amount of that short-run speed for a large amount
of long-run predictability, at no operational cost increase over the mud
itself, which is why dimension 14 recommends both as the default destination
rather than microservices. Microservices buy stronger isolation at a real
operational cost and only pay off when the team has already learned to draw
real boundaries, since drawing them wrong at the network layer produces the
worse variant in dimension 8. The Strangler Fig column describes a transition
state, not a resting state, included because it is the honest middle ground
between living with the mud and a wholesale rewrite.

## 13. Related and incompatible patterns

- **Layered Architecture.** The most common intended destination when a team
  decides to stop adding to the mud. Layering gives the untraceable call
  graph from dimension 5 a direction, so a dependency diagram becomes
  readable again. See the layered-architecture family entry for how layers
  are defined and how their direction is enforced.
- **Modular Monolith.** A close cousin of layering, drawn along domain
  boundaries rather than technical ones, and Shopify's account in dimension 9
  is a direct production example of choosing this over a rewrite or a
  service split.
- **Bounded Context, from Domain-Driven Design.** The tool for deciding where
  a boundary actually belongs rather than where it is technically convenient
  to draw one. Eric Evans devotes chapter 14, "Maintaining Model Integrity,"
  of *Domain-Driven Design, Tackling Complexity in the Heart of Software*,
  Addison-Wesley, 2003, to exactly this problem, arguing that a single,
  unified model across a whole large system is itself a common cause of the
  tangle this entry describes, and that splitting the model along explicit
  Bounded Contexts, each with its own vocabulary and its own boundary, is the
  antidote. Reach for Bounded Context analysis before drawing any service
  boundary, per the failure mode in dimension 11.
- **Strangler Fig Application.** The refactoring path of choice out of an
  existing Big Ball of Mud rather than into a fresh one. Martin Fowler's
  description of the pattern, named for a vine that "germinates in a nook of
  a tree" and gradually replaces its host, captures exactly the incremental
  replacement strategy dimension 14 recommends over a wholesale rewrite
  ([Fowler, "StranglerFigApplication," martinfowler.com, updated 22 August
  2024](https://martinfowler.com/bliki/StranglerFigApplication.html),
  verified 2026-08-02).
- **Spaghetti Code, The Blob, and Lava Flow.** Narrower, code-level relatives
  rather than substitutes, defined in Brown, Malveau, McCormick, and Mowbray,
  chapter 5. A Big Ball of Mud is very often built from many small instances
  of these three, and cleaning up an instance of any one of them, extracting
  a Blob's responsibilities, deleting a piece of Lava Flow once its
  dependents are confirmed gone, is a legitimate, bounded first step toward
  reducing the larger mud without requiring the whole-system rewrite that
  feels, wrongly, like the only real fix.
- **Service Locator and Singleton, applied to shared mutable state.** Actively
  contribute to this anti-pattern rather than composing with it cleanly. Both
  give every part of a system ambient, undeclared access to shared state,
  which is precisely the structural participant named in dimension 5, so
  reaching for either while trying to fix a Big Ball of Mud usually makes the
  problem worse rather than better.
- **Microservices, when adopted before internal boundaries exist.**
  Incompatible in practice, not in principle. Cutting a network boundary
  through a system that has no internal boundary does not create isolation,
  it relocates the tangle, producing the Distributed Big Ball of Mud variant
  in dimension 8. Microservices compose well with this anti-pattern's remedy
  only after a Modular Monolith or Bounded Context exercise has already
  identified where the real seams are.

## 14. Refactoring path in and out

**How the pattern is introduced.** In the overwhelming majority of real
systems, nobody introduces this pattern deliberately, dimension 7 already
describes how it accretes through many individually reasonable decisions with
no single point where a reviewer could have said no. The one deliberate,
defensible path in is the honest throwaway prototype from dimension 4,
adopted consciously, for a bounded reason, with a real plan to either discard
the code or refactor it hard once its purpose is served, and revisited if
that plan changes, per the Sweeping It Under the Rug failure mode in
dimension 11.

**Removing it, general approach.** The named refactoring path out draws on
Foote and Yoder's own Shearing Layers and Sweeping It Under the Rug patterns,
on Fowler's Strangler Fig, and on Feathers' seam-finding technique, applied
in this order.

1. Stop first, before touching structure, put characterization tests around
   whatever slice of behavior will be touched, using Michael Feathers'
   technique from *Working Effectively with Legacy Code*, Prentice Hall,
   2004, chapter 13, of pinning the system's actual current behavior, bugs
   included, so that a refactor can be verified not to change what the
   system does, only how it is built. See dimension 15.
2. Identify one shearing layer to extract. Foote and Yoder borrow the term
   Shearing Layers from architecture to describe the observation that
   different parts of a system change at different rates, and recommend
   pulling the slowest-changing part, often data access or a small set of
   stable domain rules, into its own seam first, because it is the least
   likely piece to require further disruptive change once separated.
3. Introduce an explicit interface at that seam, without moving the
   implementation yet, so every call site now goes through one named point
   rather than reaching directly into shared state. This alone, done with no
   other change, converts an invisible dependency from dimension 5 into a
   visible one a reviewer can see in a diff.
4. Move the implementation behind the interface, one call site at a time,
   running the characterization tests from step 1 after each move, which is
   the Strangler Fig pattern applied at the scale of a single seam rather
   than a whole application.
5. Repeat steps 2 through 4 for the next shearing layer, letting the seams
   accumulate into a real module boundary, then a real Bounded Context, per
   dimension 13, rather than attempting to design the target architecture
   in one pass before any code moves.
6. Only after several seams exist and the team has real evidence about where
   the domain's actual boundaries lie should a network boundary, a service
   extraction, be considered, and even then, cut along an existing seam
   rather than a new guess, to avoid recreating dimension 8's distributed
   variant.
7. Where a piece of the mud genuinely cannot be safely touched, quarantine it
   explicitly behind an adapter, Foote and Yoder's Sweeping It Under the Rug,
   and track the quarantine as a dated, revisited item rather than a comment,
   closing the failure mode named in dimension 11.

**When Reconstruction, a full rewrite, is the honest answer instead.** Foote
and Yoder name this as a legitimate last resort, not a first move, reserved
for systems whose underlying domain assumptions have changed so completely
that incremental extraction would cost more than starting over. Even then,
Spolsky's Netscape account and Amazon's multi-year Obidos retirement both
point the same direction, a rewrite that is not paired with an explicit
containment plan, keeping the old system serving traffic while the new one
is built incrementally alongside it via the same Strangler Fig discipline,
tends to reproduce the pattern on a second, initially clean codebase, as
described in dimension 11.

## 15. Testing and verification

Harder because of the pattern, and this is close to the whole story.

- There are no seams at which a unit test can isolate one piece of behavior
  from the rest, because dimension 5's ambiently shared state means almost
  any test setup pulls in most of the system to get a realistic starting
  state.
- A test that does manage to isolate one function often breaks the moment an
  unrelated change touches the shared state that function silently depended
  on, producing exactly the flaky, unpredictable test suite that
  demoralizes teams and eventually gets partially disabled, deepening the
  original problem.
- Coverage numbers, even when high, are frequently misleading here, because
  a line can be executed by a test without any assertion meaningfully
  constraining its behavior, a gap a coverage percentage alone cannot reveal.

Techniques that apply, in the order a team facing this pattern for the first
time should reach for them.

- **Characterization testing, or golden-master testing.** Michael Feathers'
  term for writing tests against a legacy system's actual current output,
  correct or not, before changing anything, precisely because the system has
  no specification and no seams to test against a specification with. Run
  the system with a range of real or realistic inputs, capture its actual
  output, and assert that output stays the same across a refactor. This is
  the technique step 1 of dimension 14 depends on.
- **Seam-finding.** Feathers defines a seam as any place in the code where
  behavior can be changed without editing the code at that exact spot, an
  interface boundary that already exists, or one that can be introduced with
  a minimal edit. Finding, or introducing, one seam at a time is the
  mechanism by which dimension 14's shearing-layer extraction becomes
  testable in isolation for the first time.
- **Contract tests at any boundary that is deliberately quarantined.** Once
  an adapter has been placed around a piece of mud per the Sweeping It Under
  the Rug strategy, a contract test at that adapter's boundary is cheap
  insurance that the quarantine is not silently violated by a future change
  on either side.
- **Approval testing on the whole system's output, at the edges.** Where no
  internal seam exists yet, an end-to-end test that captures a full request
  or response, an entire rendered page, an entire API payload, and diffs it
  against a stored approved version gives some regression protection while
  internal seams are still being introduced, at the cost of being slow and
  coarse-grained.
- **Mutation testing, deployed carefully.** Because coverage percentages
  mislead in a codebase this tangled, mutating the production code and
  checking whether any test fails is a more honest measure of whether the
  characterization tests from step 1 are actually pinning behavior or merely
  executing it. This is expensive to run broadly, so scope it to the slice of
  code currently being extracted, not the whole system at once.

## 16. Observability signals

The pattern hides in the structure of the code, not in its runtime logs, so
what to measure is mostly about the codebase and the team's own change
history rather than about production telemetry, though production signals
matter too.

What to record and track over time.

- **Change coupling, sometimes called logical coupling.** How often two
  files are modified in the same commit, aggregated across the whole commit
  history. A pair of files with no explicit dependency between them that are
  nonetheless almost always changed together is direct, measurable evidence
  of the ambiently shared state named in dimension 5, and is one of the few
  signals that can be computed automatically from version control alone with
  no runtime instrumentation.
- **The size distribution of the largest files and classes**, tracked over
  time rather than as a single snapshot, since a file that is merely large
  today but stable in size is a different risk from one whose line count is
  growing every release, the trajectory a Blob or a god object follows on
  its way into existence.
- **Cyclomatic complexity and its trend**, per function and aggregated per
  module, watched for modules whose complexity keeps climbing release over
  release with no corresponding drop anywhere else, the numeric shadow of
  the untraceable call graph in dimension 5.
- **Lead time and blast radius per change**, how long a typical pull request
  takes from open to merge, and how many files it touches. A rising trend in
  either, especially blast radius, is the most direct organizational symptom
  of the growing coordination cost described in dimension 10.
- **Onboarding time to first meaningful, safely merged change** for new
  engineers, tracked as a simple metric rather than left as folklore. A
  rising trend here is often the first signal a manager notices before any
  code-level metric is even collected.
- **A count of quarantine adapters and their age**, so the Sweeping It Under
  the Rug strategy from dimension 14 stays visible and dated rather than
  invisible and permanent, closing the failure mode named in dimension 11.

A healthy trajectory shows change coupling concentrated inside module
boundaries rather than spread across the whole codebase, complexity flat or
falling in the modules under active refactoring, and blast radius per change
shrinking as seams accumulate. An unhealthy one shows a small number of files
that appear in nearly every commit's diff regardless of what feature is being
built, complexity climbing across the board with no module bucking the
trend, and a growing gap between the size of a requested change and the size
of the diff it actually takes to deliver it.

## 17. Security and privacy implications

Unlike a pattern whose security implications are a secondary concern, this
one is close to a security anti-pattern in its own right, because the
structural properties in dimension 5 are precisely the properties a security
review depends on a system not having.

- **No natural boundary for the principle of least privilege.** Least
  privilege depends on being able to say which component needs access to
  which data, and a system where every module can reach ambiently shared
  state has already answered that question with everything, everywhere,
  which is the answer least privilege exists to prevent.
- **Untraceable data flow makes privacy impact assessment close to
  impossible.** Determining where a piece of personal data can end up, which
  is what a data protection impact assessment or a breach notification
  process both require, depends on being able to trace data flow through
  the system. The untraceable call graph in dimension 5 makes that tracing a
  manual, error-prone, whole-system exercise rather than a bounded one.
- **Attack surface is effectively the whole system from any single entry
  point.** A vulnerability in one undifferentiated module, an injection flaw
  in a data access function reached from a dozen unrelated call sites, is
  not contained to the feature where it was found, because nothing in the
  architecture stops it from being reachable everywhere that shared state or
  that function is reachable, which dimension 5 shows is nearly everywhere.
- **Penetration testing and code review cannot be meaningfully scoped.** A
  reviewer or a pen tester working against a well-bounded module can
  reasonably claim to have covered that module's attack surface. Against a
  Big Ball of Mud, that same claim requires reviewing the whole system,
  because any part might reach any other part, which in practice means
  security review coverage silently degrades to whatever slice a limited
  budget can afford, with no principled way to say which slice matters most.
- **Auditing is weakened for the same structural reason.** A compliance
  requirement to log every access to a category of sensitive data assumes
  there is a small, identifiable set of code paths that touch that data. In
  this pattern, that set is, at best, unknown, and at worst, unknowable
  without the same whole-system tracing exercise the privacy point above
  describes.

The remedy is the same remedy as the rest of this entry, introducing real
seams, because a seam is simultaneously a testing boundary, a change
boundary, and a security boundary. There is no security-specific fix
available that bypasses the underlying structural work in dimension 14.

## 18. References

- Foote, B., Yoder, J., "Big Ball of Mud," originally presented at PLoP '97 /
  EuroPLoP '97, Monticello, Illinois, September 1997, issued as Washington
  University technical report WUCS-97-34, later published as chapter 29 of
  *Pattern Languages of Program Design 4*, edited by Neil Harrison, Brian
  Foote, and Hans Rohnert, Addison-Wesley, 2000.
  http://www.laputan.org/mud/mud.html, verified 2026-08-02.
- Brown, W.J., Malveau, R.C., McCormick, H.W. "Skip", Mowbray, T.J.,
  *AntiPatterns, Refactoring Software, Architectures, and Projects in
  Crisis*, John Wiley and Sons, 1998, ISBN 978-0-471-19713-3, chapter 5,
  "Software Development AntiPatterns" (Spaghetti Code, The Blob, Lava Flow,
  Poltergeists, Golden Hammer, Cut-and-Paste Programming). Table of contents
  cross-checked against
  https://epdf.pub/antipatterns-refactoring-software-archtectures-and-projects-in-crisis.html,
  verified 2026-08-02.
- Riel, A.J., *Object-Oriented Design Heuristics*, Addison-Wesley, 1996,
  Heuristic 3.2. Plain-text mirror of the heuristic list,
  https://www2.ccs.neu.edu/research/demeter/related-work/riel/heuristics2.txt,
  verified 2026-08-02.
- Cunningham, W., "The WyCash Portfolio Management System," OOPSLA '92
  Experience Report. http://c2.com/doc/oopsla92.html, verified 2026-08-02.
- Lehman, M.M., "Programs, Life Cycles, and Laws of Software Evolution,"
  *Proceedings of the IEEE*, Vol. 68, No. 9, September 1980, pp. 1060-1076.
- Evans, E., *Domain-Driven Design, Tackling Complexity in the Heart of
  Software*, Addison-Wesley, 2003, chapter 14, "Maintaining Model
  Integrity."
- Feathers, M., *Working Effectively with Legacy Code*, Prentice Hall, 2004,
  chapter 13 (characterization testing) and the seam definition in chapter 4.
- Fowler, M., "StranglerFigApplication," martinfowler.com bliki, last
  updated 22 August 2024.
  https://martinfowler.com/bliki/StranglerFigApplication.html, verified
  2026-08-02.
- Spolsky, J., "Things You Should Never Do, Part I," Joel on Software, 6
  April 2000.
  https://www.joelonsoftware.com/2000/04/06/things-you-should-never-do-part-i/,
  verified 2026-08-02.
- MacCormack, A., Rusnak, J., Baldwin, C.Y., "Exploring the Structure of
  Complex Software Designs, An Empirical Study of Open Source and
  Proprietary Code," *Management Science*, Vol. 52, No. 7, 2006, pp.
  1015-1030, DOI 10.1287/mnsc.1060.0552. Working paper PDF,
  https://www.hbs.edu/ris/Publication%20Files/05-016.pdf, verified
  2026-08-02.
- Gray, J. (interviewer), "A Conversation with Werner Vogels," ACM Queue,
  Vol. 4, No. 4, May 2006. https://queue.acm.org/detail.cfm?id=1142065,
  verified 2026-08-02.
- Westeinde, K., "Deconstructing the Monolith, Designing Software that
  Maximizes Developer Productivity," Shopify Engineering, 21 February 2019.
  https://shopify.engineering/deconstructing-monolith-designing-software-maximizes-developer-productivity,
  verified 2026-08-02.
- Morris, B., "Microservices, REST and the Distributed Big Ball of Mud," 20
  April 2015.
  https://www.ben-morris.com/microservices-rest-and-the-distributed-big-ball-of-mud/,
  verified 2026-08-02.

## Code examples

Three languages illustrate three of the implementation variants from
dimension 8. Each block is deliberately written the way this anti-pattern
actually looks in a real codebase, tangled and working, rather than as a
demonstration of good practice, since the value of the example is
recognition, not imitation. All three were compiled or run directly, not
merely inspected. C#, Kotlin, and Java were skipped for this entry, three
languages already cover the god-object, procedural, and distributed variants
without repeating the same shape a fourth time.

TypeScript, the god-object variant from dimension 8. One class owns pricing,
inventory, notification, and audit logging at once, with all state held in
static fields any other part of the program could also reach.

```typescript
class StoreApp {
  static db: Map<string, number> = new Map([["widget", 12], ["gadget", 30]]);
  static orders: string[] = [];
  static taxRate = 0.08;

  handleCheckout(sku: string, qty: number, email: string): void {
    if (qty <= 0) {
      console.log("bad qty for " + sku);
      return;
    }
    const price = StoreApp.db.get(sku);
    if (price === undefined) {
      console.log("unknown sku " + sku);
      return;
    }
    const total = price * qty * (1 + StoreApp.taxRate);
    StoreApp.db.set(sku, (StoreApp.db.get(sku) ?? 0) - qty);
    StoreApp.orders.push(sku + ":" + qty + ":" + total.toFixed(2));
    if (email.indexOf("@") === -1) {
      console.log("skipping email, bad address");
    } else {
      console.log("emailing " + email + " total " + total.toFixed(2));
    }
    console.log("AUDIT checkout " + sku + " qty=" + qty);
  }
}

function main(): void {
  const app = new StoreApp();
  app.handleCheckout("widget", 2, "buyer@example.com");
  console.log(StoreApp.orders);
}

main();
```

Python, the procedural spaghetti variant from dimension 8. No classes at
all, module-level dictionaries stand in for a database, and one function
mixes lookup, validation, pricing, persistence, and notification.

```python
_customers = {"alice": {"email": "alice@example.com", "credit": 50}}
_inventory = {"widget": 12, "gadget": 30}
_orders = []


def checkout(customer, sku, qty):
    if customer not in _customers:
        print("unknown customer", customer)
        return
    if sku not in _inventory or _inventory[sku] < qty:
        print("cannot fulfil", sku)
        return
    price = 5 if sku == "widget" else 9
    total = price * qty
    if _customers[customer]["credit"] < total:
        print("over credit limit")
        return
    _inventory[sku] -= qty
    _customers[customer]["credit"] -= total
    _orders.append((customer, sku, qty, total))
    email = _customers[customer]["email"]
    if "@" in email:
        print("emailing", email, "total", total)
    print("AUDIT", customer, sku, qty)


def main():
    checkout("alice", "widget", 3)
    print(_orders)


if __name__ == "__main__":
    main()
```

Go, one step on the way to the distributed variant from dimension 8. A
single handler inlines request parsing, pricing, inventory mutation, and
notification, the shape that turns into a Distributed Big Ball of Mud the
moment several services each contain a handler built this way and start
calling one another.

```go
package main

import "fmt"

var db = map[string]int{"widget": 12, "gadget": 30}
var ledger []string

type orderRequest struct {
	SKU   string
	Qty   int
	Email string
}

func handleOrder(req orderRequest) string {
	if req.Qty <= 0 {
		return "rejected: bad qty"
	}
	stock, ok := db[req.SKU]
	if !ok || stock < req.Qty {
		return "rejected: out of stock"
	}
	price := 5
	if req.SKU == "gadget" {
		price = 9
	}
	total := price * req.Qty
	db[req.SKU] = stock - req.Qty
	ledger = append(ledger, fmt.Sprintf("%s:%d:%d", req.SKU, req.Qty, total))
	if len(req.Email) > 3 {
		fmt.Println("emailing", req.Email, "total", total)
	}
	fmt.Println("AUDIT order", req.SKU, req.Qty)
	return "ok"
}

func main() {
	result := handleOrder(orderRequest{SKU: "widget", Qty: 2, Email: "a@b.com"})
	fmt.Println(result, ledger)
}
```
