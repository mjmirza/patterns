---
name: High Cohesion
slug: high-cohesion
family: 04-principles-and-laws
category: Principle
aliases: [Functional Cohesion, Module Cohesion, Cohesion Principle]
first_described: "Larry Constantine and Edward Yourdon, Structured Design, 1979; formalized as a GRASP pattern by Craig Larman in Applying UML and Patterns, 1997"
maturity: canonical
related: [single-responsibility-principle, low-coupling, information-expert, separation-of-concerns, facade]
incompatible_with: []
verified: 2026-08-02
---

# High Cohesion

## 1. Name, aliases, and lineage

The canonical name is High Cohesion. The idea originates in structured design,
not object orientation. Larry Constantine coined cohesion as a property of a
module in the early 1970s while developing structured design at IBM, and the
concept reached print in Larry L. Constantine and Edward Yourdon, *Structured
Design. Fundamentals of a Discipline of Computer Program and Systems Design*,
Yourdon Press, 1979, a full scan of which is preserved on the Internet
Archive ([archive.org, Structured Design Edward Yourdon Larry
Constantine](https://archive.org/details/Structured_Design_Edward_Yourdon_Larry_Constantine),
verified 2026-08-09; the primary source, Yourdon's own retrospective essay on
strucdesign.com, has since gone dead. checked against the live host directly
(404 GET after a 405 HEAD), the domain root (403), and the Wayback Machine
(no snapshot exists for this path), so the book scan is cited in its place.
Constantine's authorship of cohesion and coupling as a pair of measures is
also treated as a matched pair in Wikipedia's article on Constantine,
https://en.wikipedia.org/wiki/Larry_Constantine, verified 2026-08-02).
Constantine and Yourdon defined a graded scale of cohesion types, from
coincidental at the weak end to functional at the strong end, and argued
that a module's internal focus should be judged against that scale rather
than treated as a single yes or no property.

The name resurfaces as a named object-oriented design pattern twenty years
later. Craig Larman folded High Cohesion into GRASP, General Responsibility
Assignment Software Patterns, a set of nine responsibility-assignment
patterns, in Craig Larman, *Applying UML and Patterns. An Introduction to
Object-Oriented Analysis and Design and Iterative Development*, 3rd edition,
Prentice Hall, 2004, chapter 17, "GRASP. Designing Objects with
Responsibilities." Larman pairs High Cohesion with Low Coupling as the two
patterns that most directly answer how to assign a responsibility so the
design stays maintainable. Robert C. Martin later folded functional cohesion
into the Single Responsibility Principle as part of the SOLID acronym, first
named as a set in Robert C. Martin, "Design Principles and Design Patterns,"
objectmentor.com, 2000, and restated in Robert C. Martin, *Clean Architecture*,
Prentice Hall, 2017, chapter 7. The aliases in circulation, Functional
Cohesion and Module Cohesion, both point back to the original Constantine and
Yourdon scale, where functional cohesion is the strongest and most desirable
grade.

High Cohesion is not itself a class or an interface you instantiate. It is a
property you evaluate about an already-drawn module boundary, which is why it
belongs in this repository's principles and laws family rather than among the
Gang of Four patterns. It is measured, not implemented.

## 2. Problem and context

A team splits a system into modules, classes, packages, or services, and
almost every split is defensible on some axis. The axis that predicts whether
the split will still make sense in eighteen months is whether the members
inside each unit are there because they work together toward one purpose, or
because they happened to land in the same file, the same service, or the same
team's backlog.

The concrete symptom that low cohesion produces is a class, module, or service
whose name stops describing what is inside it. A `Utils` class accretes a
date formatter, a currency rounder, a Slack notifier, and a retry helper,
because each addition was individually small and the class was already there.
A `UserService` grows a password reset flow, a billing webhook handler, and a
CSV export, because "user" is broad enough to justify almost anything. Nobody
decided to build a kitchen-drawer module. It happened one convenient addition
at a time, and every individual addition looked like the path of least
resistance.

The context in which cohesion becomes a live design question is any moment a
developer chooses where a new piece of behavior goes. Does the new method
belong on this class, a sibling class, or a new one, does the new endpoint
belong in this service or a different one, and cohesion is the criterion for
that decision. Constantine and Yourdon frame it explicitly as a property of
the degree to which the elements of a module belong together (Constantine and
Yourdon 1979, restated in Wayne P. Stevens, Glenford J. Myers, and Larry L.
Constantine, "Structured Design," IBM Systems Journal, vol. 13, no. 2, 1974,
which is the original journal paper that predates the 1979 book and where the
cohesion scale first appeared in print, https://ieeexplore.ieee.org/document/5388086,
verified 2026-08-02).

## 3. Forces

High Cohesion is a decision made under competing pressures, and naming them
honestly is the point of this section rather than presenting the principle as
a free win.

Understandability versus locality of change. A highly cohesive module is easy
to understand in isolation, because everything inside it serves one purpose,
but that same focus can mean a single business change now touches several
small, cohesive modules instead of one large, unfocused one. Cohesion trades
a cheaper read for a more distributed write.

Reuse versus indirection. Splitting a kitchen-drawer class into focused
pieces makes each piece independently reusable, but a caller that previously
made one call into `UserService` now makes calls into three collaborators,
and someone has to coordinate them. The coordination has to live somewhere,
and that somewhere is new code that did not exist before the split.

Cohesion versus coupling, in tension with each other despite usually being
described together. Splitting a low-cohesion module into several
high-cohesion ones typically increases the number of dependencies between
those pieces, because the work that used to happen inside one unit now
happens across a boundary. Larman pairs High Cohesion with Low Coupling
precisely because pushing cohesion too far, past the point where the pieces
still share a genuine reason to change together, buys local clarity at the
cost of global coupling (Larman 2004, chapter 17, section on
contraindications and over-fragmentation).

Deployment and operational cost versus focus, at the service level. In a
microservice architecture, functional cohesion argues for narrowly scoped
services, but each additional service is an additional deployment pipeline,
an additional on-call surface, and an additional network hop. Sam Newman
discusses this trade-off directly under the heading of service boundaries in
Sam Newman, *Building Microservices*, 2nd edition, O'Reilly, 2021, chapter 2,
where he argues that the boundary should track business capability
cohesion, not database table or class cohesion, precisely because the
operational cost of a service boundary is much higher than the cost of a
class boundary.

Team topology versus code topology. Conway's Law means that a module
boundary chosen for cohesion inside the code can cut across the boundary of a
single team, or bundle two teams' concerns into one module, and either
mismatch produces friction that has nothing to do with the code's internal
quality. Matthew Skelton and Manuel Pais, *Team Topologies*, IT Revolution
Press, 2019, chapter 3, argue that cohesive software boundaries and cohesive
team boundaries should be designed together, not independently.

## 4. Applicability and non-applicability

Apply High Cohesion when a module, class, function, or service is being
carved out or reviewed and the question is whether its members share one
clear reason to exist together. It is the right lens for naming a class and
checking whether every public method is something that name would predict,
for a package or namespace boundary in a monolith, for the decision of where
a new service should own a piece of data versus calling out to another
service for it, and for any refactor motivated by not knowing where a method
should go.

Do not apply High Cohesion in the following situations, because doing so
produces worse designs, not better ones.

- Do not force unrelated small operations into one module purely to avoid a
  `Utils` class. A module whose real, honest job is a small set of
  independent pure functions with no shared state and no shared reason to
  change together is not low cohesion in the harmful sense as long as each
  function is itself internally focused. The failure mode is a module that
  claims one purpose and delivers several. A module that honestly claims to
  be a grab bag of small pure helpers, clearly named as such, is a
  defensible organizational unit, not a cohesion violation, as Steve
  McConnell notes when discussing utility routines in Steve McConnell,
  *Code Complete*, 2nd edition, Microsoft Press, 2004, chapter 5, section
  5.3.
- Do not split a class or service based on cohesion alone when the split
  crosses a strong transactional boundary. If two pieces of data must be
  updated together inside one ACID transaction to preserve an invariant,
  splitting them into two cohesive-looking services because they feel
  separate introduces a distributed transaction or a saga where a simple
  local transaction used to suffice. Vaughn Vernon discusses this directly
  when defining aggregate boundaries in Domain-Driven Design, arguing the
  transactional consistency boundary should dominate the cohesion argument
  when the two conflict, in Vaughn Vernon, *Implementing Domain-Driven
  Design*, Addison-Wesley, 2013, chapter 10, "Aggregates."
- Do not apply cohesion analysis to a throwaway script or a one-off data
  migration. The principle earns its cost through the second, third, and
  tenth change to a module. A script that runs once and is deleted never
  incurs that cost, so spending design effort on its internal cohesion is
  waste.
- Do not use cohesion as the sole justification for microservice
  decomposition when the team lacks the operational maturity to run many
  services. Newman is explicit that decomposing for cohesion before a team
  can operate the resulting services safely produces a distributed monolith,
  which is worse than the coupled monolith it replaced (Newman 2021, chapter
  1, "The Trade-Offs").
- Do not chase the highest theoretical grade of cohesion, functional, when a
  lower grade, sequential or communicational, already matches the real
  shape of the problem and the cost of further splitting exceeds the
  benefit. The Constantine and Yourdon scale is a diagnostic tool for
  spotting the genuinely bad grades, coincidental and logical, not a
  mandate to reach the top grade in every module.

## 5. Structure

High Cohesion is not object-structural in the Gang of Four sense, there are
no fixed participant roles like Subject and Observer. Instead the pattern
describes a property that any of the following units can have or lack, at
whichever scope is being evaluated.

- The unit under evaluation. A function, a class, a package, a bounded
  context, or a service. The evaluation asks whether the unit's members are
  present because they contribute to one clearly nameable purpose.
- The unit's members. Methods on a class, functions in a module, endpoints
  on a service, files in a package. Each member is checked against the
  unit's stated purpose.
- The reason for change. The organizing question, following Robert Martin's
  later restatement of cohesion through the Single Responsibility
  Principle, is which actor or business capability would ask for this
  member to change. Members sharing one reason to change belong together,
  members with different reasons to change do not (Martin, *Clean
  Architecture*, 2017, chapter 7, "SRP. The Single Responsibility
  Principle").
- The Constantine and Yourdon cohesion scale, used as the diagnostic
  vocabulary for describing how strong or weak the cohesion of a given unit
  is, from weakest to strongest, coincidental, logical, temporal,
  procedural, communicational, sequential, and functional (Constantine and
  Yourdon 1979, chapter 6, "Module Coupling and Cohesion," the same
  seven-way scale is reproduced and explained with worked examples in
  Steve McConnell, *Code Complete*, 2nd edition, 2004, chapter 5.3, table
  5.1).

| Grade | What binds the members | Typical symptom |
|---|---|---|
| Functional | Every element contributes to exactly one well-defined task | The strongest grade, the target |
| Sequential | Output of one element is the input of the next | A pipeline stage grouping, generally acceptable |
| Communicational | Elements operate on the same data | Acceptable, common in data-access classes |
| Procedural | Elements are grouped because they run in a fixed sequence, without a data relationship | Weak, often a sign the sequence itself is the real abstraction missing a name |
| Temporal | Elements are grouped because they happen at the same time, such as an initialize or cleanup bucket | Weak, a common source of Utils-class drift |
| Logical | Elements are grouped by category but selected through a flag or type code | Weak, usually reveals a missing polymorphic split |
| Coincidental | No discernible relationship at all | The worst grade, the kitchen-drawer class |

## 6. ASCII structure diagram

```
LOW COHESION (before)                    HIGH COHESION (after)

+------------------------+                 +------------------+
|     UserService        |                 |   UserProfile    |
|-------------------------|                 |------------------|
| updateName()            |                 | updateName()     |
| updatePassword()        |                 | updateEmail()    |
| chargeCard()            |                 +------------------+
| refundCard()            |
| exportUsersToCsv()      |                 +------------------+
| sendWelcomeSlack()      |    split into  |  BillingService  |
| resetPassword()         |    ----------->  |------------------|
+--------------------------+                 | chargeCard()     |
                                             | refundCard()     |
    every member has a                      +------------------+
    different reason to change
                                             +------------------+
                                             |  UserExporter    |
                                             |------------------|
                                             | exportUsersToCsv()|
                                             +------------------+

                                             +--------------------+
                                             | OnboardingNotifier |
                                             |---------------------|
                                             | sendWelcomeSlack() |
                                             +---------------------+

                                             each unit answers to
                                             exactly one reason to change
```

## 7. Dynamics

Cohesion has no runtime message flow of its own, because it is a static
design property rather than a collaboration pattern, so this section instead
traces the sequence a team follows when discovering and correcting a
cohesion problem, which is where the principle actually plays out over time.

```
Time  Event
----  --------------------------------------------------------------
t0    A new requirement arrives, send a Slack alert when a new
      user signs up. The fastest path is a new method on the
      existing UserService, because UserService already has a
      handle to the user object.

t1    UserService.sendWelcomeSlack() is added. The class now mixes
      identity management, billing, and notification. No single
      test broke, no build failed, the addition looked free.

t2    A second requirement arrives, retry the Slack call three
      times with backoff. The engineer implementing it must now
      also understand chargeCard() and resetPassword() to safely
      change the file, because they live in the same class and
      share its test fixtures and its lock in a monorepo build
      graph.

t3    Cohesion review, prompted by a slow, unfocused pull request
      that touches unrelated tests. The class is graded, sequential
      cohesion for chargeCard and refundCard, temporal cohesion for
      the new Slack method, since it exists because it happens on
      signup, not because it shares data with the rest of the class.

t4    Extraction. OnboardingNotifier is created, taking the Slack
      logic and its own retry policy. UserService keeps only
      identity fields and identity-changing methods.

t5    The caller that used to say userService.signUp(u) now says
      userService.signUp(u) followed by notifier.notifyWelcome(u),
      or, if the two must not be split at the call site, an
      application service coordinates both, keeping each
      collaborator itself cohesive.

t6    Regression check, BillingService tests, previously coupled to
      UserService test fixtures by file locality, now run
      independently and faster, because the split reduced blast
      radius, which is the coupling benefit that a cohesion fix
      produces as a side effect.
```

## 8. Implementation variants

Extract Class, the standard mechanical move. Identify a subset of a class's
fields and methods that share one reason to change, move them to a new
class, and replace direct field access with delegation or composition.
Martin Fowler names and describes this refactoring explicitly as the
corrective move for low cohesion in Martin Fowler, *Refactoring. Improving
the Design of Existing Code*, 2nd edition, Addison-Wesley, 2018, chapter 7,
"Moving Features Between Objects," Extract Class.

Bounded Context decomposition, the domain-driven design variant. At the
scale of a whole subsystem or service, cohesion is evaluated against a
ubiquitous language rather than a class's fields. A bounded context is
functionally cohesive when every term inside it means one thing and every
capability inside it belongs to one business responsibility, and the split
between contexts is drawn where the language itself starts to mean
something different. Eric Evans, *Domain-Driven Design. Tackling Complexity
in the Heart of Software*, Addison-Wesley, 2003, part 4, "Strategic
Design," chapter 14, "Maintaining Model Integrity."

Single Responsibility Principle as the OO restatement. Robert Martin
reframes functional cohesion for object-oriented code as gathering
together the things that change for the same reasons and separating those
things that change for different reasons, which turns the abstract
Constantine and Yourdon scale into an actionable per-class test, name the
actors who could request a change to this class, and if there is more than
one actor, the class has mixed reasons to change and low cohesion (Martin,
*Clean Architecture*, 2017, chapter 7).

Package-level and module-level cohesion, the Java and Go idiom. In
languages with an explicit package or module boundary, cohesion is
expressed by keeping a package's exported surface small and centered on one
concept, often paired with the Common Closure Principle, which states that
classes that change together should live in the same package. Robert C.
Martin, "Granularity," originally in *Engineering Notebook*, C++ Report,
1996, collected in Robert C. Martin, *Agile Software Development,
Principles, Patterns, and Practices*, Prentice Hall, 2002, chapter 28.

Facade as a cohesion-preserving seam. When splitting a low-cohesion class
into several focused ones would break too many existing callers at once, a
Facade can sit in front of the new, more numerous, more cohesive
collaborators and present the old call shape while the split proceeds
incrementally. This repository's own entry on Facade documents that seam in
detail, at patterns/01-design-patterns-gof/facade.md; this entry treats the trade-off from
the cohesion side only.

Cyclomatic and LCOM-style metrics as a machine-checkable proxy. Lack of
Cohesion in Methods, first defined by Shyam R. Chidamber and Chris F.
Kemerer, "A Metrics Suite for Object Oriented Design," IEEE Transactions on
Software Engineering, vol. 20, no. 6, 1994, pages 476 to 493, gives a
countable approximation of cohesion, it measures how many of a class's
method pairs share no instance field access, and a high count is a
machine-detectable signal that correlates with, but does not prove, low
functional cohesion (https://ieeexplore.ieee.org/document/295895, verified
2026-08-02).

## 9. Known production uses

The Unix philosophy and the coreutils toolset. Doug McIlroy's stated design
rule, make each program do one thing well, predates the Constantine and
Yourdon terminology but is the same functional cohesion criterion applied
at the process-and-tool granularity rather than the class granularity. The
GNU coreutils package ships dozens of single-purpose executables, `cat`,
`grep`, `sort`, `wc`, rather than one configurable unixutil binary, and the
project's own documentation states this decomposition explicitly as a
design goal (GNU Coreutils manual, "Introduction,"
https://www.gnu.org/software/coreutils/manual/html_node/index.html,
verified 2026-08-02; McIlroy's rule is quoted in Eric S. Raymond, *The Art
of Unix Programming*, Addison-Wesley, 2003, chapter 1, "The Rule of
Modularity").

The Java Collections Framework's interface segregation as a cohesion
outcome. `java.util.List`, `java.util.Set`, and `java.util.Map` are
deliberately separate interfaces rather than one general Collection type
with optional operations, and the Java Collections Framework overview
explicitly frames the split around distinct, cohesive contracts for
ordered sequences, unique-element sets, and key-value mappings (Oracle,
"The Java Collections Framework, Interfaces,"
https://docs.oracle.com/javase/8/docs/technotes/guides/collections/reference.html,
verified 2026-08-02).

Kubernetes controller design, the single-controller-single-resource-kind
convention. The Kubernetes API machinery documentation states that a
controller should track one resource kind and drive it toward a desired
state, rather than one controller managing many unrelated resource kinds,
and names this explicitly as a design guideline for writing custom
controllers (Kubernetes documentation, "Controllers,"
https://kubernetes.io/docs/concepts/architecture/controller/, verified
2026-08-02). The kubebuilder scaffolding tool, maintained by the Kubernetes
SIG API Machinery working group, generates exactly one reconciler per
custom resource definition as its default project layout, encoding the
same cohesion boundary into tooling (Kubebuilder Book, "Controller,"
https://book.kubebuilder.io/cronjob-tutorial/controller-overview.html,
verified 2026-08-02).

Stripe's API resource design. Stripe's REST API is organized around
narrowly scoped resources, Charge, Customer, Refund, PaymentIntent, each
exposing operations that act only on that resource's own data, rather than
one general Payments endpoint accepting a discriminator field for the
operation type. Stripe's own API reference documents each resource
separately with its own endpoint namespace, and Stripe's public API design
guide names resource-oriented, single-purpose endpoints as an explicit
principle (Stripe API Reference, https://docs.stripe.com/api, verified
2026-08-02).

## 10. Consequences

Positive.

- A cohesive unit is understandable on its own, because a reader does not
  need to hold unrelated concerns in mind to reason about any one method,
  which reduces the cognitive load Larman names directly as the motivation
  for GRASP High Cohesion (Larman 2004, chapter 17).
- Cohesive units are independently testable, because their collaborators
  and their state are narrow enough to construct or stub without dragging
  in unrelated fixtures.
- Cohesive units are independently reusable, because a caller that wants
  only the billing behavior no longer has to depend on identity or
  notification code that happened to share a class with it.
- Cohesive units localize the blast radius of a change. A bug fix or a
  behavior change to one responsibility does not force a rebuild, retest,
  or redeploy of unrelated responsibilities that merely lived in the same
  file or the same service.
- Cohesive naming becomes accurate and stays accurate, because a class
  whose members all serve one purpose can be named for that purpose and
  the name will still be true after the next ten changes, whereas a
  low-cohesion class's name decays into a lie almost immediately.

Negative.

- Splitting for cohesion increases the number of types, files, or services
  in the system, which increases the surface a newcomer must map before
  they can navigate it, even though each individual piece is simpler.
- Coordinating a workflow that used to happen inside one unit now requires
  an explicit coordinating layer, application service, or orchestrator,
  which is new code that did not exist before and which itself must be
  kept cohesive or it becomes the next kitchen-drawer.
- At the service level, pursuing functional cohesion aggressively
  multiplies deployment units, and each one carries a fixed operational
  cost, a health check, an on-call runbook, a CI pipeline, that does not
  shrink just because the service's internal logic did (Newman 2021,
  chapter 1).
- Over-splitting past the point where two pieces genuinely share a reason
  to change produces shotgun surgery, where one conceptual change now
  requires edits across several small files, which is itself a code smell
  named by Fowler as the mirror-image failure of low cohesion (Fowler
  2018, chapter 3, "Bad Smells in Code," "Shotgun Surgery").
- Measuring cohesion is not fully mechanical. LCOM-style metrics give a
  proxy, not a proof, and a class can score well on LCOM while still
  mixing two genuinely different responsibilities that happen to touch the
  same fields, so cohesion review still requires human judgement about the
  actors and reasons for change, not just a metric threshold.

## 11. Failure modes and misuse

| Symptom | Cause | Fix |
|---|---|---|
| A class named Utils, Helpers, Manager, or Common keeps growing and every pull request that touches it edits an unrelated method than the one under discussion. | Temporal or coincidental cohesion, methods are grouped because they needed a home rather than by shared purpose. | Extract Class per member group that shares a reason to change, name each new class for that reason, not for a generic bucket word. |
| Two engineers working on unrelated features both need to modify the same file in the same sprint and produce a merge conflict on unrelated lines. | Low cohesion increased the blast radius of the file, so unrelated work landed in the same physical location. | Split along the seam the merge conflict revealed, the conflicting hunks are evidence of the two different reasons to change. |
| A class passes an LCOM or cyclomatic-complexity linter threshold but a new team member still cannot describe what the class is for in one sentence. | The metric caught structural symptoms, shared field access patterns, but missed a semantic mixing of two responsibilities that happen to touch the same data, which communicational cohesion can mask. | Ask the who asks for this to change question from Martin's SRP framing for every public method, independent of the metric score. |
| A microservice decomposition produces ten services, each individually cohesive, but a single user-facing feature now requires four synchronous calls across four of them, with cascading latency and failure modes. | Cohesion was optimized at the service granularity without weighing the coupling and operational cost it introduced between services, the trade Newman warns against directly. | Reconsider the service boundary against the business capability boundary, per Newman's guidance, and consider whether some of the ten services should be merged back or reorganized around a coarser capability. |
| A God object is split into many small classes, but one orchestrator class is then reintroduced that calls all of them in sequence and re-accumulates every dependency the split removed. | The coordination logic that genuinely needs to know about several collaborators was treated as a design failure to be hidden, rather than acknowledged as its own cohesive responsibility, application coordination, and given its own well-scoped home. | Give the orchestrator a narrow, honestly named responsibility, coordinating one specific workflow, rather than treating it as a dumping ground for anything that touches more than one collaborator. |
| A cohesion-driven refactor is done purely defensively, moving code around with no behavior change and no test added, and a regression ships in the reshuffle. | Cohesion refactors are treated as risk-free because nothing changed, when in fact moving state and logic across a class boundary changes initialization order, visibility, and sometimes threading assumptions. | Treat every Extract Class or bounded-context split as a refactor requiring the same test coverage and review discipline as a behavior change, per Fowler's own precondition that refactoring requires a passing test suite before and after (Fowler 2018, chapter 2). |

## 12. Trade-off matrix

Compared against three named alternative organizing strategies for the same
decision, where to put a new piece of behavior.

| Force | High Cohesion (Larman GRASP, this entry) | Convenience Placement (add to whatever class is already open) | Feature-Folder Organization (group by feature, not by responsibility) | Microservice-per-Team (Conway's Law driven, no cohesion analysis) |
|---|---|---|---|---|
| Understandability of a single unit | High, each unit answers to one purpose | Low, purpose drifts with every addition | Medium, a feature folder can itself mix responsibilities internally | Depends entirely on the team's internal discipline, not guaranteed by the pattern |
| Speed of the next small addition | Slower initially, may require a new class | Fastest, always has somewhere convenient to land | Fast for changes local to one feature | Fast within a service, slow across services |
| Blast radius of a change | Small, isolated to the cohesive unit | Large, unrelated code shares the same file and build unit | Small within a feature, can leak if features share code | Small within a service, coordination cost across services |
| Testability | High, narrow collaborators to fake or stub | Low, tests drag in unrelated fixtures | Medium to high | High within a service, integration testing across services is expensive |
| Long-term maintainability | High, names stay accurate | Degrades continuously, this is the documented failure mode | Degrades if feature boundaries do not track the actual domain model | Depends on whether team boundaries track cohesive business capabilities |
| Coordination overhead when work spans units | Present, but explicit and named | Absent short term, hidden inside the shared class | Present when a change crosses feature folders | Highest, network calls and versioning replace in-process calls |
| Best used when | The team can afford to name and evolve boundaries deliberately | Never, as a deliberate strategy, it is the default that happens by not deciding | The domain naturally decomposes into user-facing features with little cross-cutting logic | Team topology and operational maturity both support many independently deployable services |

## 13. Related and incompatible patterns

Low Coupling. Larman presents High Cohesion and Low Coupling as a pair
precisely because they interact, increasing cohesion by splitting a module
usually increases the number of dependencies between the resulting pieces,
which is a coupling cost. The two patterns must be evaluated together, not
independently, and a design that maximizes one at the total expense of the
other is a worse design than one that balances both (Larman 2004, chapter
17, "Low Coupling" and "High Cohesion" presented as sequential sections
with explicit cross-references).

Single Responsibility Principle. SRP is the object-oriented,
actor-and-reason-to-change restatement of functional cohesion. Where the
Constantine and Yourdon scale is defined in terms of data and control flow
inside a procedural module, SRP is defined in terms of who requests a
change, but the two are describing the same underlying property from
different eras and different paradigms (Martin 2017, chapter 7).

Information Expert. Another GRASP pattern, Information Expert says to
assign a responsibility to the class that has the information needed to
fulfill it. Following Information Expert consistently tends to produce
high-cohesion classes as a side effect, because grouping behavior with the
data it needs is one of the strongest forms of cohesion, communicational
cohesion, on the Constantine and Yourdon scale (Larman 2004, chapter 17,
"Information Expert," discussion of the relationship to cohesion).

Separation of Concerns. David Parnas's broader principle of dividing a
system so that each part addresses a separable concern is the intellectual
ancestor that both cohesion and coupling operationalize at the module
level. David L. Parnas, "On the Criteria to Be Used in Decomposing Systems
into Modules," Communications of the ACM, vol. 15, no. 12, December 1972,
pages 1053 to 1058 (https://dl.acm.org/doi/10.1145/361598.361623, verified
2026-08-02), argues for decomposing around information hiding and design
decisions likely to change, which is functionally the same criterion
Larman later names cohesion.

Facade. When an existing caller cannot absorb a cohesion-driven split all
at once, a Facade can preserve the old call shape while the underlying
collaborators are separated for cohesion, letting the two changes,
internal restructuring and external interface stability, proceed on
different schedules. See this repository's Facade entry, at
patterns/01-design-patterns-gof/facade.md, for the pattern's own dimensions, this entry
only notes the seam.

God Object anti-pattern, the direct incompatibility. A God Object is the
named failure state of ignoring High Cohesion entirely, one class or
module accumulates responsibility for most of a system's behavior. Arthur
J. Riel names the anti-pattern's shape, though not always under that exact
label, in his heuristics against classes with too many responsibilities,
in Arthur J. Riel, *Object-Oriented Design Heuristics*, Addison-Wesley,
1996, heuristic 5.3. High Cohesion and the God Object anti-pattern are
directly opposed, and a design cannot exhibit both at once for the same
unit.

## 14. Refactoring path in and out

Introducing High Cohesion into an existing low-cohesion class.

1. List every public method on the class and, for each one, write down
   which actor or business event would ask for it to change. This is the
   diagnostic step from Martin's SRP framing, applied concretely (Martin
   2017, chapter 7).
2. Group the methods by that answer. Each distinct group is a candidate
   for its own class.
3. For each group with more than one member, apply Fowler's Extract Class,
   create the new class, move the relevant fields and methods to it, and
   replace the original class's direct access with either composition,
   the original class holds a reference to the new one, or delegation
   (Fowler 2018, chapter 7, "Extract Class").
4. Update every caller. If the number of call sites makes an atomic update
   risky, introduce a temporary Facade on the original class that
   forwards to the new collaborators, ship that, then migrate callers to
   the new collaborators directly over subsequent changes, then remove
   the Facade.
5. Re-run the actor-and-reason-to-change test on each resulting class. If
   a new class still answers to more than one actor, repeat the process
   on it.
6. Verify with the full test suite before and after each extraction, per
   Fowler's precondition that refactoring is only refactoring when
   behavior is provably unchanged (Fowler 2018, chapter 2, "Principles in
   Refactoring").

Removing an over-split, when cohesion has been pushed past its usefulness.

1. Identify the symptom named in section 11 as shotgun surgery, a single
   conceptual change routinely requires edits across several small
   classes that were split from one original.
2. Confirm the split pieces genuinely share a reason to change now, even
   if they did not when originally split, by checking recent commit
   history for co-changed files, which is the mechanical version of the
   Common Closure Principle (Martin 2002, chapter 28).
3. Apply Fowler's Inline Class, the direct inverse of Extract Class,
   merging the small classes back into one, and delete the coordinating
   class that only existed to call them in sequence, since it is no
   longer doing meaningful coordination work once the pieces are reunited
   (Fowler 2018, chapter 7, "Inline Class").
4. Re-run the full test suite and confirm the merge did not reintroduce
   the original mixed-responsibility problem that motivated the original
   split, the goal is a class with one clearer, larger responsibility,
   not a regression to a kitchen drawer.

## 15. Testing and verification

A cohesive unit is, definitionally, easier to test than an incohesive one,
because its constructor requires fewer collaborators and its test
fixtures need to represent less unrelated state. The testing implication
runs in both directions and is itself diagnostic.

Symptom-driven test smell. If unit-testing a single method on a class
requires constructing mocks or fakes for collaborators that have nothing
to do with that method's stated purpose, for example mocking a payment
gateway to test a password-reset method because both live on the same
`UserService`, that test friction is direct evidence of low cohesion, not
merely an inconvenience to route around with more mocking. Gerard
Meszaros names this test smell Obscure Test and traces several of its
causes back to production code that mixes unrelated concerns, in Gerard
Meszaros, *xUnit Test Patterns. Refactoring Test Code*, Addison-Wesley,
2007, chapter 16.

Testing an extraction is a regression test, not a new-feature test.
Because Extract Class is a refactoring, the correct test strategy is
characterization tests that lock in current behavior before the move,
followed by the same tests run unmodified after the move except for
their setup code, which should shrink as fixtures narrow.

Contract tests at service boundaries. When cohesion analysis produces a
service split rather than a class split, the collaborating services need
a contract test, not only unit tests inside each service, to catch cases
where each service is individually well-tested but the interface between
them has drifted. Pact and similar consumer-driven contract testing tools
exist specifically to test the seam a cohesion-motivated service split
creates (documented at https://docs.pact.io/, verified 2026-08-02).

What becomes harder. Testing a workflow that spans several newly
cohesive units, previously exercised with one integration test against
one class, now requires either an integration test that wires the
collaborators together or a set of individually-mocked unit tests plus
one end-to-end test for the coordinating layer, which is strictly more
test code than the single-class version, and is the direct testing-side
cost of the coordination overhead named in section 10.

## 16. Observability signals

Cohesion itself does not emit a runtime signal, because it is a static
property, but its violation and its correction both leave measurable
traces that a team can monitor.

Change-coupling metrics from version control history. If two files are
modified together in the same commit far more often than their declared
dependency graph would predict, that co-change frequency is a proxy for
hidden low cohesion or a missed abstraction, an approach described as
mining commit history for co-changed files to reveal hidden coupling in
Adam Tornhill, *Your Code as a Crime Scene*, 2nd edition, Pragmatic
Bookshelf, 2018, chapter 4, "The Principles of Code Age."

LCOM and related static-analysis metrics tracked over time. A rising Lack
of Cohesion in Methods score on a class, tracked release over release by
a static analysis tool, is a leading indicator that the class is
accreting unrelated responsibilities before it becomes a maintenance
emergency (Chidamber and Kemerer 1994).

Deployment and incident correlation, at the service level. If a
service's deploys or incidents cluster around unrelated feature areas
rather than around one business capability, that clustering is evidence
the service boundary does not track a cohesive capability, and the fix
is the same section 14 refactoring applied at the service granularity
rather than the class granularity.

Pull request diff shape. A pull request whose diff touches files with no
logical relationship to the PR's stated intent, for example a fix for a
Slack notification retry that also edits chargeCard, is a direct
runtime-adjacent signal, observable in code review tooling, that the
underlying class the PR touched has low cohesion.

## 17. Security and privacy implications

Cohesion has a real, if indirect, security implication through blast
radius and the principle of least privilege, rather than through any
cryptographic or authentication mechanism of its own.

A low-cohesion class or service that mixes, for example, payment
processing with unrelated user-preference storage typically ends up with
one credential, one database connection, and one set of access
permissions covering both concerns, because the code was never split
along a boundary that access control could follow. This means a
vulnerability or a bug in the lower-sensitivity concern, user
preferences, can be exploited to reach the higher-sensitivity concern,
payment data, because the two share a runtime identity and a data store.
The Payment Card Industry Data Security Standard requires network and
system segmentation to reduce the scope of systems that handle
cardholder data, and its own guidance explicitly favors architectures
where payment processing is isolated into its own boundary rather than
mixed into a general-purpose service (PCI Security Standards Council,
"PCI DSS v4.0," requirement 1, network security controls, and the
accompanying scoping guidance,
https://www.pcisecuritystandards.org/document_library/, verified
2026-08-02). A functionally cohesive billing service, kept separate from
unrelated concerns, is a direct architectural precondition for that kind
of scope reduction, because a security boundary cannot be scoped around a
concern that is not itself a separate deployable or a separate
credentialed principal.

Beyond payment data, the same reasoning applies to any regulated
category, personal data under GDPR's data minimization principle, health
data, or authentication secrets, a highly cohesive module dedicated to
that category is easier to audit, easier to encrypt at rest as a unit,
and easier to grant narrow database or IAM permissions to, than a
mixed-purpose module that happens to also touch that data as a side
effect of an unrelated responsibility. This is analytical judgement
rather than a sourced claim about a specific system, and it follows
directly from the blast-radius consequence already named in section 10.

## 18. References

1. Larry L. Constantine and Edward Yourdon, *Structured Design.
   Fundamentals of a Discipline of Computer Program and Systems Design*,
   Yourdon Press, 1979, chapter 6, "Module Coupling and Cohesion." The
   originating text for the cohesion scale.
2. W. P. Stevens, G. J. Myers, and L. L. Constantine, "Structured
   Design," IBM Systems Journal, vol. 13, no. 2, 1974, pages 115 to 139,
   https://ieeexplore.ieee.org/document/5388086, verified 2026-08-02. The
   original journal publication of coupling and cohesion, predating the
   1979 book.
3. Craig Larman, *Applying UML and Patterns. An Introduction to
   Object-Oriented Analysis and Design and Iterative Development*, 3rd
   edition, Prentice Hall, 2004, chapter 17, "GRASP. Designing Objects
   with Responsibilities." Source for High Cohesion as a named GRASP
   pattern.
4. Robert C. Martin, *Clean Architecture. A Craftsman's Guide to
   Software Structure and Design*, Prentice Hall, 2017, chapter 7, "SRP.
   The Single Responsibility Principle." Source for the reason-to-change
   reformulation of functional cohesion.
5. Martin Fowler, *Refactoring. Improving the Design of Existing Code*,
   2nd edition, Addison-Wesley, 2018, chapter 7, "Extract Class" and
   "Inline Class," chapter 3, "Shotgun Surgery," chapter 2, "Principles
   in Refactoring." Source for the mechanical refactorings and the
   over-split failure mode.
6. Sam Newman, *Building Microservices. Designing Fine-Grained Systems*,
   2nd edition, O'Reilly Media, 2021, chapter 1, "Microservices," and
   chapter 2, "How to Model Microservices." Source for the operational
   cost of service-level cohesion decisions and the distributed-monolith
   warning.
7. Vaughn Vernon, *Implementing Domain-Driven Design*, Addison-Wesley,
   2013, chapter 10, "Aggregates." Source for the transactional-boundary
   non-applicability case.
8. Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart
   of Software*, Addison-Wesley, 2003, chapter 14, "Maintaining Model
   Integrity." Source for bounded context as cohesion at the subsystem
   scale.
9. Shyam R. Chidamber and Chris F. Kemerer, "A Metrics Suite for Object
   Oriented Design," IEEE Transactions on Software Engineering, vol. 20,
   no. 6, June 1994, pages 476 to 493,
   https://ieeexplore.ieee.org/document/295895, verified 2026-08-02.
   Source for the LCOM metric.
10. David L. Parnas, "On the Criteria to Be Used in Decomposing Systems
    into Modules," Communications of the ACM, vol. 15, no. 12, December
    1972, pages 1053 to 1058,
    https://dl.acm.org/doi/10.1145/361598.361623, verified 2026-08-02.
    Source for the separation-of-concerns lineage.
11. Steve McConnell, *Code Complete. A Practical Handbook of Software
    Construction*, 2nd edition, Microsoft Press, 2004, chapter 5,
    "Design in Construction," section 5.3. Source for the reproduced
    cohesion-type table and the utility-routine non-applicability case.
12. Matthew Skelton and Manuel Pais, *Team Topologies. Organizing
    Business and Technology Teams for Fast Flow*, IT Revolution Press,
    2019, chapter 3, "Team-First Thinking." Source for the team-topology
    force.
13. Gerard Meszaros, *xUnit Test Patterns. Refactoring Test Code*,
    Addison-Wesley, 2007, chapter 16, "Test Smells," "Obscure Test."
    Source for the testing symptom of low cohesion.
14. Adam Tornhill, *Your Code as a Crime Scene. Use Forensic Techniques
    to Arrest Defects, Bottlenecks, and Bad Design in Your Programs*, 2nd
    edition, Pragmatic Bookshelf, 2018, chapter 4, "The Principles of
    Code Age." Source for change-coupling as an observability signal.
15. Arthur J. Riel, *Object-Oriented Design Heuristics*, Addison-Wesley,
    1996, heuristic 5.3. Source for the God Object anti-pattern's
    opposition to high cohesion.
16. Robert C. Martin, *Agile Software Development, Principles,
    Patterns, and Practices*, Prentice Hall, 2002, chapter 28,
    "Package-Design Principles." Source for package-level cohesion and
    the Common Closure Principle.
17. Eric S. Raymond, *The Art of Unix Programming*, Addison-Wesley,
    2003, chapter 1, "Philosophy," "The Rule of Modularity." Source for
    McIlroy's do one thing well rule as a production-scale expression of
    functional cohesion.
18. GNU Coreutils Manual, "Introduction,"
    https://www.gnu.org/software/coreutils/manual/html_node/index.html,
    verified 2026-08-02. Source for the coreutils single-purpose-
    executable production example.
19. Kubernetes documentation, "Controllers,"
    https://kubernetes.io/docs/concepts/architecture/controller/,
    verified 2026-08-02. Source for the single-controller-single-
    resource-kind convention.
20. Kubebuilder Book, "Controller Overview,"
    https://book.kubebuilder.io/cronjob-tutorial/controller-overview.html,
    verified 2026-08-02. Source for the tooling-level reification of
    that convention.
21. Stripe API Reference, https://docs.stripe.com/api, verified
    2026-08-02. Source for resource-oriented API design as a cohesion
    example.
22. Oracle, "The Java Collections Framework, Interfaces,"
    https://docs.oracle.com/javase/8/docs/technotes/guides/collections/reference.html,
    verified 2026-08-02. Source for the List, Set, Map interface split.
23. PCI Security Standards Council, "PCI DSS v4.0," requirement 1 and
    accompanying scoping guidance,
    https://www.pcisecuritystandards.org/document_library/, verified
    2026-08-02. Source for the security-scoping implication of cohesive
    service boundaries.
24. Pact documentation, "What Is Pact," https://docs.pact.io/, verified
    2026-08-02. Source for consumer-driven contract testing at
    cohesion-motivated service boundaries.
25. Joshua Bloch, *Effective Java*, 3rd edition, Addison-Wesley, 2018,
    Item 1, "Consider Static Factory Methods Instead of Constructors."
    Source for distinguishing GRASP-style cohesion analysis from the
    unrelated Static Factory Method naming collision, referenced for
    terminological clarity.

## Code examples

Three languages are used, TypeScript, Python, and Go. Each shows the same
before-and-after, a low-cohesion class or module handling identity,
billing, and notification concerns together, refactored into three
functionally cohesive units connected through explicit, narrow
interfaces. Swift and Java are omitted here only because TypeScript,
Python, and Go already show the pattern across a class-based, a
duck-typed, and a struct-and-interface style, which covers the idiomatic
range the pattern needs, the underlying move, Extract Class grouped by
reason to change, is identical in every mainstream object-oriented or
interface-based language.

### TypeScript

```typescript
// BEFORE. one class, three unrelated reasons to change.
class UserServiceLowCohesion {
  constructor(private db: Map<string, { name: string; email: string; balance: number }>) {}

  updateName(id: string, name: string): void {
    const u = this.db.get(id);
    if (u) u.name = name;
  }

  chargeCard(id: string, amountCents: number): string {
    const u = this.db.get(id);
    if (!u) throw new Error("no such user");
    if (u.balance < amountCents) throw new Error("insufficient funds");
    u.balance -= amountCents;
    return `charge-${id}-${amountCents}`;
  }

  exportUsersToCsv(): string {
    const rows = [...this.db.entries()].map(([id, u]) => `${id},${u.name},${u.email}`);
    return ["id,name,email", ...rows].join("\n");
  }
}

// AFTER. each unit answers to exactly one reason to change.
interface UserRecord {
  name: string;
  email: string;
  balance: number;
}

class UserProfile {
  constructor(private db: Map<string, UserRecord>) {}

  updateName(id: string, name: string): void {
    const u = this.db.get(id);
    if (u) u.name = name;
  }

  updateEmail(id: string, email: string): void {
    const u = this.db.get(id);
    if (u) u.email = email;
  }
}

class BillingService {
  constructor(private db: Map<string, UserRecord>) {}

  chargeCard(id: string, amountCents: number): string {
    const u = this.db.get(id);
    if (!u) throw new Error("no such user");
    if (u.balance < amountCents) throw new Error("insufficient funds");
    u.balance -= amountCents;
    return `charge-${id}-${amountCents}`;
  }
}

class UserExporter {
  constructor(private db: Map<string, UserRecord>) {}

  toCsv(): string {
    const rows = [...this.db.entries()].map(([id, u]) => `${id},${u.name},${u.email}`);
    return ["id,name,email", ...rows].join("\n");
  }
}

function demo(): void {
  const db = new Map<string, UserRecord>([["u1", { name: "Ana", email: "a@x.io", balance: 5000 }]]);
  const profile = new UserProfile(db);
  const billing = new BillingService(db);
  const exporter = new UserExporter(db);

  profile.updateEmail("u1", "ana@x.io");
  const receipt = billing.chargeCard("u1", 1200);
  console.log(receipt);
  console.log(exporter.toCsv());
}

demo();
```

### Python

```python
"""Extract Class applied to a low-cohesion order handler."""
from dataclasses import dataclass, field


@dataclass
class Order:
    order_id: str
    items: list[tuple[str, int]] = field(default_factory=list)
    paid: bool = False


# BEFORE. pricing, persistence, and email notification in one class.
class OrderServiceLowCohesion:
    def __init__(self):
        self._orders: dict[str, Order] = {}

    def add_item(self, order_id: str, sku: str, cents: int) -> None:
        o = self._orders.setdefault(order_id, Order(order_id))
        o.items.append((sku, cents))

    def total_cents(self, order_id: str) -> int:
        return sum(c for _, c in self._orders[order_id].items)

    def save(self, order_id: str) -> None:
        pass  # imagine a database write here

    def send_confirmation_email(self, order_id: str, address: str) -> str:
        return f"Sent confirmation for {order_id} to {address}"


# AFTER. three cohesive collaborators, each with one reason to change.
class OrderRepository:
    def __init__(self):
        self._orders: dict[str, Order] = {}

    def get_or_create(self, order_id: str) -> Order:
        return self._orders.setdefault(order_id, Order(order_id))

    def save(self, order: Order) -> None:
        self._orders[order.order_id] = order


class PricingCalculator:
    @staticmethod
    def total_cents(order: Order) -> int:
        return sum(c for _, c in order.items)


class OrderNotifier:
    @staticmethod
    def send_confirmation(order: Order, address: str) -> str:
        return f"Sent confirmation for {order.order_id} to {address}"


def demo() -> None:
    repo = OrderRepository()
    order = repo.get_or_create("o1")
    order.items.append(("sku-42", 1999))
    order.items.append(("sku-7", 599))
    repo.save(order)

    total = PricingCalculator.total_cents(order)
    assert total == 2598

    message = OrderNotifier.send_confirmation(order, "buyer@example.com")
    print(f"total_cents={total} message={message!r}")


if __name__ == "__main__":
    demo()
```

### Go

```go
package main

import "fmt"

// User is the shared data both cohesive units act on.
type User struct {
	ID      string
	Name    string
	Email   string
	Balance int // cents
}

// UserStore is a communicationally cohesive collaborator, every
// method operates on the same underlying map.
type UserStore struct {
	users map[string]*User
}

func NewUserStore() *UserStore {
	return &UserStore{users: make(map[string]*User)}
}

func (s *UserStore) Put(u *User) {
	s.users[u.ID] = u
}

func (s *UserStore) Get(id string) (*User, bool) {
	u, ok := s.users[id]
	return u, ok
}

// BillingService owns exactly one reason to change, how a charge
// is validated and applied. It depends on UserStore through a
// narrow interface rather than the concrete type, keeping the two
// units loosely coupled while each stays cohesive.
type balanceReader interface {
	Get(id string) (*User, bool)
}

type BillingService struct {
	store balanceReader
}

func NewBillingService(store balanceReader) *BillingService {
	return &BillingService{store: store}
}

func (b *BillingService) ChargeCard(id string, amountCents int) (string, error) {
	u, ok := b.store.Get(id)
	if !ok {
		return "", fmt.Errorf("no such user: %s", id)
	}
	if u.Balance < amountCents {
		return "", fmt.Errorf("insufficient funds for %s", id)
	}
	u.Balance -= amountCents
	return fmt.Sprintf("charge-%s-%d", id, amountCents), nil
}

// ProfileService owns a different reason to change, how identity
// fields are edited. It shares the store but has zero knowledge
// of billing rules, which is the point of the split.
type ProfileService struct {
	store *UserStore
}

func NewProfileService(store *UserStore) *ProfileService {
	return &ProfileService{store: store}
}

func (p *ProfileService) UpdateEmail(id, email string) error {
	u, ok := p.store.Get(id)
	if !ok {
		return fmt.Errorf("no such user: %s", id)
	}
	u.Email = email
	return nil
}

func main() {
	store := NewUserStore()
	store.Put(&User{ID: "u1", Name: "Ana", Email: "a@x.io", Balance: 5000})

	profiles := NewProfileService(store)
	billing := NewBillingService(store)

	if err := profiles.UpdateEmail("u1", "ana@x.io"); err != nil {
		panic(err)
	}

	receipt, err := billing.ChargeCard("u1", 1200)
	if err != nil {
		panic(err)
	}

	fmt.Println(receipt)
}
```
