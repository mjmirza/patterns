---
name: Poltergeist
slug: poltergeist
family: 18-anti-patterns
category: Anti-Pattern
aliases: [Gypsy Wagon, Ghost Class, Stub Class Proliferation, Class-Happy Design]
first_described: "Akroyd 1996, catalogued in Brown, Malveau, McCormick, Mowbray 1998"
maturity: canonical
related: [factory-method, facade, middle-man, feature-envy, god-object, lava-flow]
incompatible_with: []
verified: 2026-08-02
---

# Poltergeist

## 1. Name, aliases, and lineage

The canonical name in the software engineering literature is Poltergeist. The
name was coined by Michael Akroyd, who presented it at the 1996 Object World
West conference as a description of a class that appears in an object model
for a moment, does a small amount of forwarding work, and then goes out of
scope, in the same way a poltergeist in folklore manifests briefly and leaves
no lasting trace ([Wikipedia's summary of Akroyd's original talk and its
"gypsy wagon" phrasing](https://en.wikipedia.org/wiki/Poltergeist_(computer_programming)),
verified 2026-08-02). Akroyd's own phrase, quoted on the same page, draws the
comparison directly. "As a gypsy wagon or a poltergeist appears and disappears
mysteriously, so does this short lived object," which is also where the
alternate name Gypsy Wagon comes from.

Two years after the conference talk, the pattern was catalogued formally in
William J. Brown, Raphael C. Malveau, Hays W. "Skip" McCormick, and Thomas J.
Mowbray, *AntiPatterns. Refactoring Software, Architectures, and Projects in
Crisis*, John Wiley and Sons, 1998, ISBN 0-471-19713-0, in Chapter 5,
"Software Development AntiPatterns" ([Wikipedia's citation of the book chapter
that catalogues Poltergeist among the software development anti-patterns](https://en.wikipedia.org/wiki/Poltergeist_(computer_programming)),
verified 2026-08-02). This places Poltergeist alongside Golden Hammer, Lava
Flow, Spaghetti Code, and the other entries in this repository's anti-pattern
family, all drawn from the same book and the same conference-era wave of
naming recurring design failures that the design pattern movement had, until
then, left undocumented.

Ghost Class and Stub Class Proliferation are informal names used in code
review discussions when the emphasis is on the empty or near-empty shape of
the class rather than on its lifetime, and both describe the same structural
defect from a slightly different angle. Class-Happy Design is a broader
umbrella phrase, sometimes used for a codebase where Poltergeist has occurred
many times over, so that the class count has grown well past what the
behaviour in the system actually requires.

The pattern continues to be recognised and searched for in real code today,
not only in the original 1998 catalogue. Samer Raad Azzawi Al-Rubaye and Yunus
Emre Selçuk published "An investigation of code cycles and Poltergeist
anti-pattern" at the 2017 8th IEEE International Conference on Software
Engineering and Service Science, DOI 10.1109/ICSESS.2017.8342882, ISBN
978-1-5386-0497-7, which studies detection techniques for the anti-pattern in
real source code ([Wikipedia's bibliographic citation of the 2017 IEEE paper
on Poltergeist detection](https://en.wikipedia.org/wiki/Poltergeist_(computer_programming)),
verified 2026-08-02). This entry cites the paper for its existence and its
bibliographic detail only. Its full text was not reachable during research for
this entry, so no claim is made here about its internal findings, its
methodology, or which specific codebases it analysed.

A useful way to place Poltergeist against its neighbours in the anti-pattern
family. Big Ball of Mud is too little structure, everything tangled into
everything else. Poltergeist is structure applied where none was needed, an
extra named type inserted between a caller and the work that caller actually
wants done. The two sit at opposite ends of the same axis, and a codebase can
suffer from both at once, tangled logic wrapped inside classes that add
nothing but a name.

## 2. Problem and context

A codebase accumulates classes whose entire behaviour is to be constructed,
make one or two calls into a different, more permanent class, and then be
discarded. The class holds no state that survives past a single call, its
constructor takes little or nothing, and if a developer deleted the class and
inlined its one method's body at every call site, the resulting code would
compile, behave identically, and read more directly.

The situation recognises itself in a codebase most often by a name pattern
before it recognises itself by a code pattern. A class called
`UserAccountManager`, `PaymentProcessController`, `ReportInitializer`, or
`OrderProcessSupervisor` turns out, on inspection, to hold no fields, declare
one public method, and that one method constructs the object that does the
real work and calls a single method on it. The manager class is not managing
anything in the sense of owning state or coordinating multiple collaborators
across time. It exists for one call and vanishes.

The context in which this arises has a recognisable shape. A developer is
adding a new piece of behaviour and instinctively reaches for a new class to
hold it, because a bare free function feels unidiomatic in the language or the
house style, or because an earlier architectural decision in the codebase
already established a convention of one class per verb. In a language and a
team culture where "everything is a class," and where an object-relational
mapper, a dependency injection container, or a code generator produces a
skeleton class for every noun and verb a developer names, the marginal cost of
creating one more class reads as zero, so nobody stops to ask whether the new
class earns its place. A second, closely related context is anticipatory
design. A developer expects a construction step to grow complicated later, so
they separate it into its own initializer or factory class today, even though
today the construction is a single call with no branching. The class is built
for a future that has not arrived, and until it does, the class is a
Poltergeist.

A third context, common in frameworks that generate boilerplate around a
naming convention, produces Poltergeist as a side effect of tooling rather
than of a developer's individual choice. A scaffolding generator that
produces a Controller, a Service, and a Manager for every new domain
concept, whether or not the concept needs all three layers, fills the
codebase with short-lived forwarding classes from the moment a feature is
created, and nobody individually decided to create the Poltergeist, the
generator's template did.

The problem is not that the codebase has too many lines of code, it is that
it has too many named seams for the behaviour those seams actually vary. Every
additional class is a promise to a reader that a boundary exists there worth
understanding on its own terms, and a Poltergeist class breaks that promise
the moment the reader opens it and finds one line of forwarding.

## 3. Applicability and non-applicability

This dimension is unusual for an anti-pattern entry, in the same way it was
unusual for the Golden Hammer entry in this repository, because an
anti-pattern by definition has no case in which it is the correct choice as
described. What belongs here instead is the boundary between a legitimate,
purposeful class that happens to be small and short-lived, which is not
Poltergeist, and the anti-pattern itself, where the same shortness and the
same brevity carry no purpose.

A small, short-lived class is legitimate design, not Poltergeist, when the
following hold. This is engineering judgement, stated as judgement rather
than dressed as a sourced fact.

- The class exists to satisfy a real interface boundary that the rest of the
  system depends on for substitutability, for example a concrete Strategy or
  a concrete Visitor that a caller selects at runtime and could reasonably
  swap for a different implementation. The value is in the seam, not in the
  amount of code on either side of it.
- The class carries genuine state across more than one call, even if that
  state is small, for example a request-scoped context object that several
  collaborators read and write over the lifetime of a single request. State
  that outlives one call is the dividing line most detection heuristics use,
  and it is a sound one.
- The class is a value object or a data transfer object whose entire purpose
  is to be a typed, immutable bundle of fields passed between layers. It has
  no behaviour to speak of because it is not supposed to have behaviour, and
  that is a design decision, not an accident.
- The class is deliberately kept thin as the seam for a test double, so that
  production code depends on an interface a test can substitute, and the thin
  production implementation is the price paid for testability described in
  dimension 15. A thin adapter that exists specifically to be swapped in
  tests earns its place through that swap, even when its production body is
  one line.
- The short lifetime is a genuine constraint of the domain, for example a
  parser's per-token context object that must not survive past the token it
  describes, where longevity would itself be the bug.

The anti-pattern is present, and the following non-applicability list is the
half of this dimension the template requires and most catalogues omit, when
any of these hold instead.

- The class has exactly one public method, that method's entire body is a
  construction followed by a single delegated call, and no test anywhere in
  the codebase constructs the class independently of its one caller, meaning
  the interface boundary the class appears to offer is never actually used as
  a boundary.
- The class's name is a role noun, Manager, Controller, Supervisor,
  Coordinator, Handler, Processor, or Initializer, and the class holds no
  field that persists between the two or three method calls a caller makes on
  it in a single interaction. Akroyd's own account calls out exactly this
  naming pattern as diagnostic, per the summary cited in dimension 1.
- The class was created in anticipation of future complexity that has not
  materialised, and the codebase has shipped for months or years without that
  complexity arriving, so the abstraction is paying an ongoing readability
  cost against a benefit that remains hypothetical. This is the anticipatory
  design context named in dimension 2, observed after enough time has passed
  to judge whether the anticipation was warranted.
- The class was produced by a code generator or a scaffolding tool applying a
  fixed template to every new domain concept, and no developer, on inspecting
  the generated file, could point to a decision it reflects beyond satisfying
  the template.
- Deleting the class and inlining its body at its call sites would compile,
  pass the same tests unmodified beyond an import change, and read more
  directly to a new team member than the indirection did. This is the single
  most reliable test for whether a specific class in front of you is a
  Poltergeist, and it is the test this entry's dimension 14 refactoring path
  walks through mechanically.

## 4. Structure and forces

Poltergeist has a structure worth naming precisely because the pattern is
easy to describe vaguely and hard to recognise precisely without a name for
each part.

The recurring roles in a Poltergeist episode are these. The **Ghost** is the
short-lived class itself, the one with the role-noun name and the single
forwarding method. The **Invoked Class**, sometimes called the real worker, is
the object the Ghost constructs and calls into, and it is where the actual
behaviour lives. The **Caller** is the code that constructs the Ghost and
calls its one method, believing it is calling into a real abstraction when in
fact it is calling through a pass-through to the Invoked Class. In the
anticipatory-design variant there is a fourth informal role, the **Imagined
Future Caller**, the hypothetical second consumer of the Ghost's flexibility
that justified building it, and whose absence, once enough time has passed,
is the evidence the class should never have existed.

The forces the anti-pattern arises from, and the forces its refactor
restores, are these.

- **Perceived organisation versus actual indirection.** Favoured by the
  anti-pattern, at a cost. A codebase with a class for every verb feels
  organised on a directory listing, because every concept has a visible,
  named home. The cost is that the organisation is cosmetic, a directory
  listing full of one-method files describes a system that looks larger and
  more structured than the behaviour inside it actually is.
- **Discoverability by name versus discoverability by behaviour.** The
  Poltergeist's role-noun name makes it easy to find by searching for the
  concept, "where does order processing happen", but once found it teaches
  the reader nothing, because the behaviour is one line down in the Invoked
  Class. The anti-pattern optimises for the first kind of discoverability
  and sacrifices the second.
- **Class count versus call-site clarity.** Every Poltergeist is one more
  class to compile, load, instantiate, and, in a garbage-collected runtime,
  collect. Individually this is negligible. At the scale of hundreds of
  Poltergeists across a mature codebase, the allocation churn and the extra
  indirection in every stack trace both become a real, measurable cost, not
  merely an aesthetic one.
- **Onboarding speed versus long-run navigation cost.** A codebase whose
  every operation has a same-named class in it can feel approachable to a
  newcomer's first grep, because searching for a business term finds a class
  with that term in its name. The long-run cost falls on the developer who
  must then trace through that class to the Invoked Class it forwards to, and
  pay that tracing cost on every future read, which the anti-pattern
  multiplies by however many Poltergeists stand between the entry point and
  the real logic.
- **Testability of the seam versus testability of the whole.** A Ghost class
  that exists purely for forwarding is trivial to test in isolation, because
  its one method has almost no logic. That triviality is itself a signal that
  the test is asserting almost nothing, and the real test coverage the team
  actually needs lives in the Invoked Class regardless of whether the Ghost
  exists.

Poltergeist gives up navigational clarity and pays an ongoing indirection tax
in exchange for a form of organisation that is genuinely cheap to produce and
genuinely satisfying to look at in a file tree, which is exactly why it
recurs across languages, teams, and decades rather than dying out after being
named once in 1996.

## 5. Consequences

Positive, stated honestly and kept short, because the anti-pattern's positive
consequences are real but small and situational rather than the deliberate
payoff a design pattern offers.

- A codebase populated uniformly with Poltergeists by a scaffolding tool is
  at least uniformly organised, which can make automated refactoring tools
  that operate on naming conventions easier to apply across the whole tree,
  even though the underlying design problem the uniformity papers over
  remains.
- In a codebase transitioning toward a cleaner architecture, a temporary
  Poltergeist can serve as a placeholder seam during a migration, marking
  where a real abstraction will eventually live once the surrounding code
  stabilises enough to justify one. The Refactoring Path dimension of this
  entry treats that use as a deliberately temporary scaffold, not as a
  destination.

Negative.

- Every additional Poltergeist increases the number of files, types, and
  named concepts a reader has to hold in mind to answer "what does this
  operation actually do", without increasing the amount of real behaviour in
  the system, which is the core reading-cost defect the anti-pattern
  introduces.
- Stack traces, debuggers, and code navigation tools spend an extra frame or
  an extra jump on every Poltergeist between the entry point and the real
  work, which compounds specifically at debugging time, when a developer is
  under the most pressure to move quickly.
- The Ghost's role-noun name attracts new, unrelated behaviour over time,
  because a class already named `OrderProcessManager` is exactly the kind of
  class a future developer reaches for when adding "one more thing related to
  order processing," turning today's harmless forwarding class into
  tomorrow's God Object once enough unrelated logic has accreted onto it.
- Object allocation and, in languages with reference counting or tracing
  garbage collection, deallocation work is spent on an object that
  contributes no state and no identity worth preserving, which is measurable
  overhead at scale even though it is invisible in any single call.
- Test suites accumulate tests that exercise the Ghost's forwarding rather
  than the Invoked Class's actual logic, inflating the test count without
  inflating the coverage of behaviour that matters, and giving a false sense
  of thoroughness.
- Dependency graphs generated from the import structure of the codebase
  overstate the system's real coupling and complexity, because a tool
  counting edges between classes counts the Ghost's edge to the Invoked Class
  as a real architectural dependency, when it is an artefact of naming rather
  than of design.

## 6. ASCII structure diagram

```
   +----------------------------------------------------------+
   |                        Caller                             |
   +----------------------------------------------------------+
                 |
                 | constructs and calls
                 v
   +----------------------------------------------------------+
   |            "OrderProcessManager"   (the Ghost)            |
   |------------------------------------------------------------|
   | + process(order)                                            |
   |     -> new OrderValidator()                                 |
   |     -> validator.validate(order)                             |
   +----------------------------------------------------------+
                 |
                 | constructs and calls, then discards itself
                 v
   +----------------------------------------------------------+
   |               OrderValidator   (the Invoked Class)         |
   |------------------------------------------------------------|
   | + validate(order)                                            |
   +----------------------------------------------------------+

   The Ghost holds no field, is constructed once per call, and is
   never referenced again after the call returns. The only edge
   that carries real behaviour is the bottom one.

   After the refactor in dimension 13, the Ghost is deleted and
   the edge collapses:

   +----------------------------------------------------------+
   |                        Caller                             |
   +----------------------------------------------------------+
                 |
                 | constructs once, holds, and calls directly
                 v
   +----------------------------------------------------------+
   |               OrderValidator   (unchanged)                 |
   +----------------------------------------------------------+
```

## 7. Dynamics

The runtime flow makes the defect visible in a way the static structure
diagram in dimension 6 only implies. The sequence below shows a single call
travelling through a Poltergeist, followed by the same call after the Ghost
has been removed.

```
Caller       "OrderProcessManager" (Ghost)     OrderValidator
  |                    |                             |
  |-- new Manager() -->|                             |
  |                    |                             |
  |-- process(order) ->|                             |
  |                    |-- new OrderValidator() ---->|
  |                    |                             |
  |                    |-- validate(order) --------->|
  |                    |<-- result -------------------|
  |<-- result ---------|                             |
  |                    |                             |
  |   (Manager instance is now unreachable            |
  |    and eligible for collection, it held           |
  |    no state that outlived this one call)          |
  |                                                    |
  ------------------------------------------------------

  After removal:

Caller                                       OrderValidator
  |                                                 |
  |-- new OrderValidator(), held once ------------>|
  |                                                 |
  |-- validate(order) ----------------------------->|
  |<-- result --------------------------------------|
```

The property worth naming plainly is the second frame in the first sequence.
The Ghost's constructor call and its one forwarding call happen back to back,
inside the same stack frame the Caller is already in, with nothing observable
happening between them. No other collaborator reads the Ghost's state,
because it has none, and no other code path reaches the Ghost, because it was
constructed fresh for this call and discarded at the end of it. A profiler
attached to a system with hundreds of these in its hot path sees the
allocation and collection cost of the Ghosts as a distinct, avoidable line
item, separate from the cost of the real work in the Invoked Class, which is
the observability signal described in dimension 16.

## 8. Recognisable variants (implementation variants of the anti-pattern)

**The naming-convention Ghost.** The most literal form, matching Akroyd's own
description. A class named with a role noun, Manager, Controller, Supervisor,
Coordinator, Handler, or the verb-derived StartProcess, that holds no state
and exists for a single call into another class. This is the variant every
detection heuristic targets first, because the name itself is the strongest
signal, per the naming characteristics cited in dimension 1.

**The scaffold-generated Ghost.** A class created automatically by a code
generator, an object-relational mapper's tooling, or an IDE's "new feature"
wizard, applying a fixed layered template, Controller, Service, Repository,
to every new domain concept regardless of whether that concept's behaviour
justifies all three layers. This variant is the hardest to fix at the
individual level, because deleting one generated Ghost fights the tool that
will regenerate it, and the real fix has to change the template, not the
instance.

**The anticipatory Ghost.** A class separated out today because a developer
expects its responsibility to grow, most commonly seen as an
`XInitializer` or an `XSetupHelper` built ahead of an expected second variant
of the setup logic that never arrives. This variant overlaps with the
speculative-generality territory described in Golden Hammer's non-applicability
list in this repository and in Martin Fowler's refactoring catalogue's
treatment of unneeded abstraction, and the two anti-patterns are frequently
present together in the same file.

**The test-scaffolding Ghost that escaped into production.** A class
originally written as a thin seam to support dependency substitution in a
test, whose production implementation stayed a one-line pass-through long
after the reason for the seam, a second real implementation, failed to
materialise. This is the legitimate case from dimension 3 gone stale, the
seam earned its place at the time it was written and has not earned it since.

**The transitional-migration Ghost.** A class deliberately left in place as a
temporary forwarding shim while a codebase migrates callers from an old
interface to a new one, intended to be deleted once every caller has moved.
This is the one variant this entry treats as acceptable for a bounded period,
provided the shim is tracked and actually removed, per dimension 13's
refactoring path.

**The framework-hook Ghost.** A class required to exist purely to satisfy a
framework's extension contract, for example a plugin descriptor class whose
only job is to return a single configuration value the framework reads once
at startup. This variant sits closest to the non-applicability boundary in
dimension 3, because the class's shortness is imposed by the framework's
contract rather than chosen freely, and removing it is not within the
codebase's control.

## 9. Known production uses

Because this is an anti-pattern rather than a documented feature a vendor
publishes in its own architecture guide, verified instances come from
academic detection studies and from real, publicly visible code review
discussions on real projects, rather than from a framework's own
documentation. Three independently sourced instances follow, and each is a
genuine, checkable occurrence rather than a paraphrase of the general
definition.

**Horace, a neutron scattering data analysis package (pace-neutrons/Horace).**
In a GitHub issue titled "Concerns about `PageOp`," a project contributor
wrote of the `PageOp` class structure, "PageOp class structure is textbook
example of a Poltergeist anti-pattern where a class exists only to operate as
a function," arguing that the design introduced unnecessary indirection and
complicated the codebase's parallelisation compared to the prior
implementation, which used a direct `apply` function
([pace-neutrons/Horace, GitHub issue #1374, "Concerns about `PageOp`"](https://github.com/pace-neutrons/Horace/issues/1374),
verified 2026-08-02). Horace is real, actively maintained scientific software
used for neutron scattering data analysis, and this is a real maintainer
naming the anti-pattern in a real architectural discussion about a real class
in the codebase, rather than a textbook example constructed for teaching.

**TEAMMATES, an open-source student feedback management system used by
universities.** In a GitHub issue titled "Refactor FeedbackSessionsLogic," a
reviewer cautioned against splitting an over-large class purely because of
its line count, writing that "breaking it up into some classes may be a
possible solution, but if you do it, it should be a well-thought design and
not [only] because there are 2000 lines, otherwise you will run into
poltergeist anti-pattern"
([TEAMMATES/teammates, GitHub issue #6545, "Refactor FeedbackSessionsLogic"](https://github.com/TEAMMATES/teammates/issues/6545),
verified 2026-08-02, bracketed word substituted for the original in the
source comment). This is a documented instance of the anti-pattern
appearing as a design risk explicitly named and guarded against during a
real refactor of a real, widely used open-source system, which is the
opposite failure mode from the one this entry mostly describes. Here the risk
was caught before the Poltergeists were written, which is exactly the
outcome dimension 13's refactoring guidance aims for.

**The academic detection literature.** Samer Raad Azzawi Al-Rubaye and Yunus
Emre Selçuk published a peer-reviewed detection study specifically targeting
this anti-pattern, "An investigation of code cycles and Poltergeist
anti-pattern," at the 2017 8th IEEE International Conference on Software
Engineering and Service Science, DOI 10.1109/ICSESS.2017.8342882
([bibliographic citation verified via Wikipedia's reference list for the
Poltergeist article](https://en.wikipedia.org/wiki/Poltergeist_(computer_programming)),
verified 2026-08-02). The paper's existence in a peer-reviewed software
engineering venue confirms that Poltergeist is recognised in the research
community as a real, detectable structural defect in real source code, worth
building tooling to find automatically, distinct from a purely rhetorical
label applied after the fact in a code review comment. This entry cites the
paper's bibliographic details only. Its methodology and the specific
codebases it analysed were not independently verifiable during research for
this entry and no claim is made about them here.

## 10. Failure modes and misuse

**The subclass or forwarding-class explosion.** Symptom. A directory with
dozens or hundreds of classes, each holding one public method whose body is a
single delegated call, discovered when a team tries to understand "how big
is our real codebase" and finds the class count wildly disproportionate to
the behaviour a walkthrough of the features would suggest. Cause. A
scaffolding template or a house convention that mints a new class for every
verb, described in dimension 2's third context. Fix. Audit the generator or
the convention itself, not each instance individually, per dimension 13.

**The renamed God Object.** Symptom. A class that started as a genuine,
minimal Poltergeist a year ago now has forty methods, holds several fields,
and every developer who touches order processing adds "one more thing" to
it, because its role-noun name, `OrderProcessManager`, reads as the
obviously correct home for anything order-processing related. Cause.
Described in dimension 5, a Ghost's name attracts unrelated behaviour once it
exists, and nobody re-evaluated whether the class still deserved its original
short-lived, stateless shape as behaviour accreted onto it. Fix. This is the
inverse refactor of the one in dimension 13, break the now-overloaded class
apart along its actual responsibilities, using the God Object entry in this
repository's family for the decomposition technique, rather than assuming the
original Poltergeist diagnosis still applies unchanged.

**The forwarding class that silently swallows an exception.** Symptom. A bug
report where an error clearly originates deep in business logic, but the
stack trace, or the log line a developer wrote, points at the thin manager
class instead, because a well-meaning try-catch was added to the Ghost at
some point "to handle errors gracefully" and now obscures where the failure
actually happened. Cause. The Ghost accumulated a responsibility, error
translation, that the original design never intended and that its
minimal, forwarding-only shape was never built to carry safely. Fix. Move
error handling to the Invoked Class or to a dedicated error-boundary
component with its own tests, rather than layering it onto a class whose
contract is silent forwarding.

**Test coverage that measures the wrong thing.** Symptom. A code coverage
report shows high line coverage on a feature, but a bug in the underlying
logic still reaches production, because most of the covered lines are
Poltergeist forwarding calls with a single, trivial assertion each, while
the Invoked Class's actual branching logic is thinly tested. Cause.
Poltergeists are easy to write tests for, because there is almost nothing to
test, which produces test files and a coverage percentage that look
reassuring without measuring the part of the system that actually carries
risk. Fix. Weight test review by cyclomatic complexity or branch count, not
by class count or line coverage percentage alone, and specifically confirm
the Invoked Class, not only the Ghost, has assertions on its real logic.

**Migration shims that never get removed.** Symptom. A codebase carries
forwarding classes explicitly named `LegacyXAdapter` or `XCompatShim`, added
during a migration that finished a year or more ago, still present because
removing them was never assigned to anyone once the migration's headline
work was declared done. Cause. The transitional-migration variant from
dimension 8, treated as acceptable at the time it was introduced, was never
tracked to completion. Fix. Track every deliberate transitional Poltergeist
with a dated removal ticket at the moment it is introduced, per the
refactoring guidance in dimension 13, rather than trusting it will be
noticed and removed informally.

**Mistaking dependency injection wiring for the anti-pattern.** Symptom. A
developer, having read about Poltergeist, proposes deleting a thin adapter
class that a dependency injection container uses to satisfy an interface
binding, without checking whether tests or alternate production
configurations actually substitute a different implementation through that
seam. Cause. Applying the naming heuristic from dimension 3 mechanically,
without checking the actual applicability criteria that distinguish a real
seam from a Ghost. Fix. Before removing any candidate, grep for every
construction site of the interface the class implements, per dimension 13's
step-by-step guidance, and confirm the seam is genuinely unused before
deleting it.

## 11. Trade-off matrix

Compared against named alternative shapes for the same piece of code, across
the forces named in dimension 4.

| Force | Poltergeist (unnecessary wrapper class) | Free function or module-level function | Facade | Middle Man (Fowler's code smell) | Dependency-injected interface with one implementation | Inline at call site |
|---|---|---|---|---|---|---|
| Discoverability by name | High. A grep for the concept finds a class named for it | Medium. Found by the function name, not framed as a "concept" | High. The facade is meant to be found and used | High, same as Poltergeist, since Middle Man is Poltergeist's naming-agnostic cousin | High. The interface name is the concept | Low. The behaviour is wherever the caller happens to be |
| Indirection cost per call | One extra construction plus one extra call | None | One call into a real aggregation of subsystems | One extra call, same as Poltergeist | One virtual dispatch, often already paid for elsewhere in the design | None |
| State held across calls | None, by definition | None, typically | Can hold configuration for the subsystems it fronts | None, by definition | Can hold real state if the implementation needs it | Whatever the caller already holds |
| Substitutability for testing | Low value. Substituting the Ghost gains little since it has no logic | Lower without an interface, but a function reference substitutes cleanly in many languages | Medium. Facades are sometimes substituted whole for integration tests | Low value, same reasoning as Poltergeist | High. This is the primary reason to choose it | None. Testing exercises the caller directly |
| Cost to add a second real implementation later | Low, ironically, since the shape is already there, but the shape was rarely built for a reason | Medium. Requires introducing an interface where none existed | Low, the facade already hides several subsystems | Low, same as Poltergeist | Zero, this is what the shape was built for | High. Requires extracting the seam from scratch |
| Reading cost for a newcomer | High. A reader must open a second file to learn nothing new | Low. The behaviour is where the name says it is | Medium. Learning the facade's contract is worthwhile because it hides real complexity | High, same as Poltergeist | Low once the pattern is familiar to the team | Lowest, everything is visible in one place |
| Class or type count | Plus one per concept, regardless of behaviour | No new type | Plus one, but it earns its place by hiding several subsystems | Plus one, same as Poltergeist | Plus one interface, which is doing real work | No new type |

Reading of the table. Poltergeist and Middle Man occupy the same row profile
almost everywhere, because Middle Man is Fowler's language for the identical
structural smell described independently of Brown et al.'s naming
convention-based diagnosis, see dimension 13 for how the two relate. A
dependency-injected interface wins decisively wherever a second
implementation genuinely exists or is genuinely planned, because it pays the
same indirection cost as a Poltergeist but earns real substitutability in
return. A free function or an inlined call wins wherever no substitution and
no persistent state is needed at all, which is the case Poltergeist claims to
serve but structurally cannot, since a class was never required for either of
those needs.

## 12. Related and incompatible patterns

- **Facade.** The legitimate cousin most often confused with Poltergeist at a
  glance, because both sit in front of other classes and forward calls. The
  distinguishing test is scope. A Facade fronts several subsystems and
  simplifies a genuinely complicated interaction into one coherent interface,
  earning its place by hiding real complexity. A Poltergeist fronts exactly
  one class with exactly one call and hides nothing, because there was
  nothing complicated to hide.
- **Factory Method.** Superficially similar, since both patterns involve a
  class whose job is to produce or hand off to another object. The
  distinguishing test, described in the Factory Method entry in this
  repository's dimension 1, is whether removing the inheritance relationship
  breaks the design. A genuine Factory Method's creator subclass varies
  polymorphically and carries other behaviour besides creation. A Poltergeist
  that happens to construct an object it forwards to has no polymorphism and
  no other behaviour, so the resemblance is surface-level only.
- **Middle Man.** The most direct sibling. Martin Fowler's refactoring
  catalogue names Middle Man as the code smell where a class delegates most of
  its responsibility to another class, with "Remove Middle Man" as the named
  refactoring that inlines the delegation away, described as the inverse of
  Hide Delegate ([Refactoring.com's catalogue entry confirming Remove Middle
  Man's relationship to Hide Delegate](https://refactoring.com/catalog/removeMiddleMan.html),
  verified 2026-08-02). Poltergeist and Middle Man describe the same
  structural defect from two different literatures, the anti-pattern
  catalogue's naming-and-lifetime framing versus the refactoring catalogue's
  delegation-ratio framing, and the two names are frequently used
  interchangeably in code review, as the TEAMMATES instance in dimension 9
  illustrates by name.
- **Feature Envy.** A related but distinct code smell. Feature Envy describes
  a method that is more interested in the data of another class than its own,
  suggesting the method belongs on the other class. Poltergeist describes a
  whole class that has no data of its own at all. A Poltergeist's single
  method is often, though not always, also a case of Feature Envy toward the
  Invoked Class, and fixing the Poltergeist by inlining or by moving the
  method resolves both smells with the same refactor.
- **God Object.** The structural opposite outcome that Poltergeist frequently
  becomes over time, as described in dimension 10's second failure mode. A
  class that starts as a minimal forwarding Ghost and accumulates unrelated
  responsibilities because its role-noun name reads as the obvious home for
  new behaviour ends up as the God Object entry in this repository's family,
  and the fix for that later state is decomposition rather than the deletion
  this entry's refactor describes.
- **Lava Flow.** Related through shared cause rather than shared shape.
  Poltergeists left over from an abandoned migration, described as the
  transitional-migration variant in dimension 8, are one of the concrete
  forms Lava Flow takes when nobody removes the scaffolding once its purpose
  has expired.
- **Dependency Injection.** Composes cleanly and is the pattern most often
  reached for by mistake to justify keeping a Poltergeist. An interface with
  exactly one production implementation and no test substitution is not,
  purely by virtue of using dependency injection, exempt from being a
  Poltergeist, since the injection framework's presence does not by itself
  create the substitutability that would justify the seam. Dimension 10's
  final failure mode is exactly this confusion, and dimension 3's
  applicability criteria are the correct test to apply before concluding an
  injected seam is legitimate.
- **Speculative Generality.** Incompatible in spirit with Poltergeist's
  eventual fix, and frequently the cause of the anticipatory variant
  described in dimension 8. Both anti-patterns describe abstraction built
  ahead of a real need, and the same refactoring instinct, delete the unused
  seam, addresses both.

## 13. Refactoring path in and out, detection and correction

Introducing a genuine seam where a Poltergeist currently stands is the rare,
deliberate case, described in dimension 3's fifth applicability bullet, where
a team knows a second implementation is coming soon and chooses to keep the
existing thin class as the seam for it rather than deleting it prematurely.
That case needs no special procedure beyond confirming, in writing in the
class's own short comment or in the team's architecture notes, what the
second implementation is expected to be and roughly when it is expected to
land, so the decision is checkable later rather than assumed to have been
correct forever.

The far more common path is removing a Poltergeist that already exists, and
the named refactoring for it is Fowler's Remove Middle Man, applied
mechanically.

1. Identify a candidate. Search the codebase for classes whose name matches
   the role-noun pattern from dimension 3, Manager, Controller, Supervisor,
   Coordinator, Handler, Processor, Initializer, and for each one, check
   whether it declares any field that is read in more than one method call
   across the object's lifetime. A class with zero such fields and one public
   method is the strongest candidate.
2. Confirm the class has no independent construction sites beyond its single
   caller and no test that constructs it in isolation to verify behaviour
   distinct from the Invoked Class's own tests. If a test does construct it
   independently, read that test first, since it may be evidence the class is
   the legitimate test-substitution seam described in dimension 3 rather than
   a true Poltergeist.
3. At the single call site, replace `new Ghost().method(args)` with a direct
   call into the Invoked Class, either by constructing the Invoked Class
   directly at that call site, or, if the Invoked Class is already available
   through the Caller's existing fields or dependencies, by calling it
   through that existing reference instead of constructing anything new.
4. Run the existing test suite. Because the Ghost's method contained no logic
   beyond the delegated call, the observable behaviour is unchanged and every
   test that passed before should pass after with no assertions rewritten,
   beyond an import or a mock target changing to the Invoked Class's name.
5. Delete the Ghost's source file and its now-empty test file, if it had one.
   This is where the refactor differs from most of the "introduce a pattern"
   procedures documented elsewhere in this repository, since Poltergeist's
   correction is subtractive from the start rather than additive followed by
   a later subtraction.
6. If the Caller now constructs the Invoked Class directly at multiple call
   sites across the codebase and that construction has grown nontrivial,
   reconsider whether a genuine Factory Method or a dependency-injected
   interface, not a Poltergeist, is now warranted, since removing one
   anti-pattern is not licence to avoid a real abstraction the codebase has
   since grown to need.

For the scaffold-generated variant from dimension 8, the individual-class
procedure above is necessary but not sufficient, because the generator will
recreate the deleted class the next time a developer runs it. The template
itself needs to change, either by making the intermediate layer optional in
the generator's configuration, or by collapsing the generated layers for
concepts below a complexity threshold the team agrees on. Fixing the tool
that mints the anti-pattern is the only durable correction for that variant.

For the transitional-migration variant, the correction is procedural rather
than structural. Every deliberate migration shim is created with an attached,
dated tracking ticket the day it is introduced, and a scheduled review, three
months out for a typical migration, at which the shim is either deleted
because every caller has moved, or explicitly re-justified with a new date if
migration work stalled. A shim with no removal date attached is, functionally,
a permanent Poltergeist that merely postpones the diagnosis.

## 14. Code examples

Two languages showing the pattern's classical, class-based shape, and one
showing the closure-based shape a language with first-class functions
naturally steers a developer toward instead. Every sample below prints both
the Poltergeist-mediated call and the refactored, direct call, so the
identical observable behaviour claimed in dimension 13, step 4, is visible
directly rather than only asserted.

### Java

```java
import java.util.List;

interface Validator {
    boolean validate(Order order);
}

final class OrderValidator implements Validator {
    public boolean validate(Order order) {
        return !order.items().isEmpty();
    }
}

record Order(List<String> items) {}

// The Poltergeist. No field, one method, one delegated call.
final class OrderProcessManager {
    boolean process(Order order) {
        OrderValidator validator = new OrderValidator();
        return validator.validate(order);
    }
}

// After Remove Middle Man. The caller holds the real worker directly.
final class Checkout {
    private final Validator validator = new OrderValidator();

    boolean submit(Order order) {
        return validator.validate(order);
    }
}

public final class Demo {
    public static void main(String[] args) {
        Order order = new Order(List.of("book", "pen"));

        boolean throughGhost = new OrderProcessManager().process(order);
        System.out.println("through the Poltergeist: " + throughGhost);

        boolean direct = new Checkout().submit(order);
        System.out.println("direct call, same result: " + direct);
    }
}
```

### TypeScript

```typescript
interface Gateway {
  connect(): string;
}

class StripeGateway implements Gateway {
  connect(): string {
    return "connected:stripe";
  }
}

// The Poltergeist. No field, one method, one delegated call.
class PaymentInitializer {
  init(gateway: Gateway): string {
    return gateway.connect();
  }
}

// After Remove Middle Man. The caller holds the gateway itself.
class CheckoutFlow {
  private readonly gateway: Gateway = new StripeGateway();

  start(): string {
    return this.gateway.connect();
  }
}

const throughGhost = new PaymentInitializer().init(new StripeGateway());
console.log("through the Poltergeist:", throughGhost);

const direct = new CheckoutFlow().start();
console.log("direct call, same result:", direct);
```

### Python

The Python form most often seen in real codebases is the closure or the
free-standing function that a class-heavy house style still wraps in a
"controller" class out of habit, so this example shows both the class-based
Ghost and the function that first-class functions in the language make
unnecessary.

```python
class ReportBuilder:
    def build(self, rows: list[str]) -> str:
        return "\n".join(rows)


class ReportGeneratorController:
    """The Poltergeist. No field, one method, one delegated call."""

    def generate(self, rows: list[str]) -> str:
        builder = ReportBuilder()
        return builder.build(rows)


def generate_report(rows: list[str]) -> str:
    """After Remove Middle Man, as a free function.

    Python has first class functions, so nothing about the
    delegation needed a class at all.
    """
    return ReportBuilder().build(rows)


if __name__ == "__main__":
    rows = ["a", "b"]

    through_ghost = ReportGeneratorController().generate(rows)
    print("through the Poltergeist:", through_ghost)

    direct = generate_report(rows)
    print("direct call, same result:", direct)
```

Go and Rust are omitted from the compiled examples above because neither
language nudges a developer toward the class-based shape of the anti-pattern
in the first place. Go has no classes and no inheritance, so a role-noun
wrapper struct with one method and one field-free forwarding call would be an
unusual, deliberately non-idiomatic thing to write, since a Go developer
reaches for a package-level function by default. Rust has no inheritance
either, and its trait objects are typically introduced specifically because a
second implementation exists, which is exactly the applicability boundary
described in dimension 3, so the anti-pattern is structurally harder to write
by accident in either language than it is in Java, C#, or a class-heavy
TypeScript codebase.

## 15. Testing and verification

Easier because of the pattern, described honestly and briefly, since the
"easier" side of Poltergeist's testing story is thin by construction.

- A Ghost's own unit test, when one exists, is close to trivial to write,
  because there is almost no branching logic to cover. This is itself the
  warning sign named in dimension 10's third failure mode, a trivially
  passing test suite around the Ghost measures almost nothing about the
  system's real risk.

Harder because of the pattern.

- Coverage tools report a misleadingly complete picture. A feature with high
  line coverage can still be under-tested at the point that actually carries
  risk, the Invoked Class's real logic, if a large fraction of the covered
  lines are forwarding calls inside Ghosts.
- Mocking frameworks asked to substitute a Ghost for a test produce a mock
  that asserts almost nothing beyond "was this one method called," which
  gives a false sense that the seam has been tested when the seam carries no
  logic worth testing in the first place.
- Refactoring tooling that measures class or method count as a proxy for
  system complexity, common in static analysis dashboards, overstates a
  codebase's real size and complexity when a large fraction of its classes
  are Ghosts, which can mislead a team's estimation of how risky a change to
  the codebase actually is.

Techniques that apply, ordered from detection through to confirming a
correction.

- **Constructor-independence check.** For a suspected Ghost, search the
  codebase for every place it is constructed. A class constructed at exactly
  one call site, with no test constructing it independently to verify
  behaviour the Invoked Class's own tests do not already cover, is the
  strongest structural signal, and it is the check dimension 13's step 2
  performs before any deletion.
- **Field-lifetime check.** Confirm no field on the candidate class is read
  in a different method call than the one that wrote it. A class where every
  field is either absent or is write-once-read-once within a single call is
  behaving as a Poltergeist regardless of what its name suggests.
- **Characterisation test before deletion.** Before applying the refactor in
  dimension 13, write or confirm a test exercises the observable behaviour
  through the Ghost as it exists today, so the refactor's claim in step 4,
  that behaviour is unchanged, is something the test suite actually proves
  rather than something the developer merely believes.
- **Static analysis for delegation ratio.** A tool, or a small script, that
  flags any class where the ratio of a method's own logic to delegated calls
  is close to zero, and where the class has few or no fields, surfaces
  Poltergeist candidates automatically across a whole codebase, which is the
  same detection goal the 2017 IEEE paper cited in dimension 9 pursues
  formally.
- **Naming-convention audit.** A grep across the codebase for the role-noun
  suffixes named in dimension 3, cross-referenced against the field-lifetime
  check above, produces a ranked list of candidates a team can review in a
  single sitting rather than one class at a time as they happen to be
  noticed.

## 16. Observability signals

Poltergeist is a static-structure defect more than a runtime-behaviour
defect, so most of its signals show up in code-level and build-level
telemetry rather than in a service's own request-level metrics. Where a
running system's telemetry does carry a signal, it is worth watching for.

What to record and measure.

- A class-count and method-count trend over time, broken down by the
  proportion of classes with zero fields and exactly one public method,
  tracked in the same static-analysis pass a team already runs for other
  code health metrics. A rising proportion over successive releases is the
  clearest longitudinal signal that Poltergeists are accumulating faster than
  they are being removed.
- Allocation profiling in a hot request path, specifically counting
  allocations of classes whose instances never survive past the stack frame
  that created them. In a managed runtime with an allocation profiler, this
  shows up as a cluster of short-lived, single-use object allocations with no
  corresponding growth in the heap's live set, which is a distinct shape from
  a memory leak and from a genuinely necessary transient object.
- Stack-trace depth in exception reports and log correlation identifiers,
  specifically watching for a pattern where several consecutive frames near
  the top of a trace belong to classes with one method each and no state,
  which lengthens every stack trace a developer has to read during an
  incident without adding diagnostic information to it.
- Dependency-graph edge count generated by an architecture visualisation
  tool, cross-referenced against the field-lifetime check from dimension 15.
  A dependency graph that shows a Ghost as a distinct node with in-edges and
  out-edges overstates the system's real coupling, and a team relying on such
  a graph to reason about blast radius for a change should discount edges
  that terminate in Ghosts.

A healthy signal looks like a class-count-to-behaviour ratio that stays flat
or shrinks as a codebase's real feature set grows, a static-analysis
delegation-ratio report with few or no zero-logic classes flagged, and stack
traces during an incident that reach the actual failing logic within one or
two frames of the entry point.

A failing signal looks like a class count that grows faster than the number
of shipped features across several releases in a row, a delegation-ratio
report whose flagged list grows every time it is run rather than shrinking as
flagged classes are cleaned up, or an incident postmortem where more time was
spent tracing through forwarding classes to find the failing logic than was
spent understanding the logic itself once found.

## 17. Security and privacy implications

Poltergeist is close to silent on security and privacy in its most common
form, and stating otherwise would invent a concern the pattern does not
carry. A stateless, one-method forwarding class introduces no new attack
surface by its structure alone, holds no data that a genuine data-handling
review would need to track, and its removal, per dimension 13, changes
nothing about what data flows where. Two indirect implications are real
enough to name plainly, and are worth distinguishing from the structural
non-issue above.

**Obscured audit trails.** Where a security or compliance review needs to
trace exactly which code path handled a piece of sensitive data, for example
during an incident investigation or a data-protection audit, a chain of
Poltergeists between the entry point and the code that actually touches the
sensitive field adds tracing work without adding any real separation of
concern that a reviewer could rely on. The forwarding classes make the
control-flow graph a reviewer has to read longer without making the actual
data handling any more contained, which is a cost specifically to the speed
and reliability of a security review rather than to the system's actual
security posture.

**A false sense of layered access control.** A codebase that names its
classes `AuthorizationManager`, `PermissionController`, and similar, gives a
reviewer reading only the names a misleading impression that access control
decisions are centralised and reviewable in one place. If those classes are
in fact Poltergeists that forward directly into scattered checks throughout
the Invoked Classes, the real authorization logic is not where the naming
implies it is, and a reviewer who trusts the naming convention rather than
tracing the actual calls can miss a permission check that was never
centralised at all. This is not a defect the anti-pattern causes directly,
it is a risk that arises specifically when Poltergeist coincides with
security-sensitive naming, and it is a strong argument for applying the
Remove Middle Man refactor from dimension 13 with particular urgency to any
class whose name suggests it is a security boundary but whose body reveals it
is not one.

On privacy specifically, the pattern is neutral. A Ghost holds no state
between calls by definition, so it cannot itself become a place where
personal data accumulates, gets cached, or gets logged inappropriately. Any
logging concern belongs to whichever class, the Ghost or the Invoked Class,
actually contains the log statement, and removing the Ghost per dimension 13
does not change what is logged, only how many frames a reader has to read to
find the logging statement.

## 18. References

1. Wikipedia contributors. "Poltergeist (computer programming)".
   https://en.wikipedia.org/wiki/Poltergeist_(computer_programming)
   Verified 2026-08-02. Source for Michael Akroyd's 1996 Object World West
   origin, the "gypsy wagon" quotation, the naming-convention
   characteristics, and the bibliographic citation for both the 1998 book
   chapter and the 2017 IEEE detection paper.
2. William J. Brown, Raphael C. Malveau, Hays W. McCormick, Thomas J.
   Mowbray. *AntiPatterns. Refactoring Software, Architectures, and Projects
   in Crisis*. John Wiley and Sons, 1998. ISBN 0-471-19713-0. Chapter 5,
   "Software Development AntiPatterns". Source for the pattern's formal
   catalogue entry, cited bibliographically per the Wikipedia reference
   list verified above, since the book's own text was not independently
   accessed for this entry.
3. Samer Raad Azzawi Al-Rubaye, Yunus Emre Selçuk. "An investigation of code
   cycles and Poltergeist anti-pattern". *2017 8th IEEE International
   Conference on Software Engineering and Service Science (ICSESS)*, 2017.
   DOI 10.1109/ICSESS.2017.8342882, ISBN 978-1-5386-0497-7. Cited
   bibliographically only, per the Wikipedia reference list verified above.
   The paper's full text, methodology, and the specific codebases it studied
   were not independently verified for this entry.
4. pace-neutrons/Horace. GitHub issue #1374, "Concerns about `PageOp`".
   https://github.com/pace-neutrons/Horace/issues/1374
   Verified 2026-08-02. Source for the named production instance quoting the
   Poltergeist anti-pattern directly against the project's `PageOp` class.
5. TEAMMATES/teammates. GitHub issue #6545, "Refactor FeedbackSessionsLogic".
   https://github.com/TEAMMATES/teammates/issues/6545
   Verified 2026-08-02. Source for the named production instance where a
   reviewer explicitly warns against the poltergeist anti-pattern while
   planning a refactor of a real, widely used open-source system.
6. Refactoring.com. "Remove Middle Man".
   https://refactoring.com/catalog/removeMiddleMan.html
   Verified 2026-08-02. Source for Martin Fowler's Middle Man code smell and
   its named refactoring, cited in dimensions 12 and 13 as the closely
   related refactoring-catalogue treatment of the same structural defect.
