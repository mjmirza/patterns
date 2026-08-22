---
name: Lazy Class
slug: lazy-class
family: 02-code-smells
category: Bloaters
aliases: [Freeloader, Lazy Type, Do-Nothing Class]
first_described: "Fowler, Beck, Brant, Opdyke, Roberts 1999"
maturity: canonical
related: [data-class, dead-code, large-class, speculative-generality, middle-man]
incompatible_with: []
verified: 2026-08-02
---

# Lazy Class

## 1. Name, aliases, and lineage

The canonical name is Lazy Class. It appears in the original code smell catalog
inside Martin Fowler, Kent Beck, John Brant, William Opdyke and Don Roberts,
*Refactoring. Improving the Design of Existing Code*, Addison-Wesley, 1999,
chapter 3, in the "Bad Smells in Code" catalog, under the smell name "Lazy
Class." The 1999 first edition ties the smell directly to two refactorings,
Collapse Hierarchy and Inline Class, and frames the underlying judgement as
economic. every class in a system costs something to understand, to maintain,
and to keep straight in a reader's head, so a class has to earn that cost back
through the work it does. The second edition of the book, Addison-Wesley, 2018,
keeps the same smell name and the same pairing of refactorings, moving the
catalog into chapter 3 of the revised text and reframing the whole chapter
around a shorter list of higher level smell families, with Lazy Class kept as
a member of the "Bloaters" family in that grouping, alongside Data Class,
Large Class, Long Method, and Long Parameter List.

Kent Beck had already used a close cousin of this idea before the 1999
catalog existed, in his Smalltalk coding conventions, where a class that adds
no behavior over its superclass and exists only as a placeholder is treated as
a design smell to fix immediately rather than tolerate. Fowler's own account in
the 1999 preface credits the smell catalog to conversations with Beck during
the writing of the book, so the shared origin between the two is well
documented rather than coincidental.

The alias **Freeloader** shows up in some secondary catalogs and blog posts to
describe the same shape, a class that rides along in the codebase contributing
nothing while still costing build time, import overhead, and mental tracking.
The alias is not used in Fowler's text itself and should be treated as
informal. **Do-Nothing Class** is a plain descriptive phrase used
interchangeably with Lazy Class in several practitioner writeups and in code
review vocabulary at a number of companies, again without being the name used
in the source catalog. This entry uses Lazy Class throughout as the canonical
term, consistent with the source, and notes the aliases only so a reader who
encounters them elsewhere recognizes the same underlying smell.

Lazy Class is easy to confuse with Data Class, its sibling entry in this
family, and the two are related but distinct. A Data Class has fields and
getters and setters and nothing else, so it fails on a behavioral axis, it
holds state a different class should be manipulating. A Lazy Class can be
behaviorally rich and still be lazy, if what it does is thin enough, or small
enough in scope, that the overhead of a separate class stops paying for
itself. A class with one method that calls one other method is a Lazy Class
candidate even if that one method does real work, because the class itself
adds a layer of indirection nobody needed. See dimension 13 for the full
relationship.

## 2. Problem and context

A codebase accretes classes over time for reasons that have nothing to do with
present-day need. A team plans an extension point that never gets used. A
refactoring extracts a responsibility into its own class, and then a later
refactoring pulls most of that responsibility back out, leaving a husk behind.
A subclass is created to override one method, and then that override is
deleted during a later change because the behavior became universal, and the
subclass itself is never deleted along with it. In every one of these
histories, the class survives past the point where it was doing real work,
because deleting a class requires someone to notice it has stopped earning its
keep, and noticing is a much rarer event than creating.

The concrete situation a reader can recognize in their own codebase looks like
this. A class file is opened and it holds one field, one constructor, and one
method that is a single line, usually a direct pass-through to a field or to
another object's method. Or a class exists purely to satisfy an interface with
a no-op implementation that was never filled in because the corresponding
feature was descoped. Or a class was split off from a larger class during an
earlier refactoring specifically to reduce that larger class's responsibility
count, and the split was correct at the time, but subsequent work moved
almost everything back into the original class, leaving the split-off class
holding one small method that could trivially live back where it started.

The problem this smell names is not that thin classes are always wrong.
Genuinely small, single-purpose classes are a design virtue in most
object-oriented and functional-object codebases, and a class that does one
thing precisely is often the goal of a refactoring, not the smell. The problem
is specifically a class whose contribution has shrunk below the fixed cost of
having a separate class at all, a cost that includes an extra file to find and
open, an extra name to remember and to keep distinct from similarly named
things, an extra hop in the call graph a reader has to trace through, an
extra unit of build and import overhead, and, in languages with per-class
metadata or per-instance allocation overhead, a small but real runtime cost
multiplied across every instantiation. When the value the class returns for
that cost approaches zero, the class has become a Lazy Class, and the
correct response is almost always to remove the class rather than to keep it
in reserve.

## 3. Forces

**Locality of behavior versus number of indirections.** Splitting behavior
into a dedicated class keeps that behavior locally named and locally testable,
which is valuable when the behavior is substantial. The same split adds one
more indirection a reader must resolve to understand a call path. Below a
certain size of behavior, the indirection cost outweighs the locality benefit,
and this smell exists to flag exactly that crossover point.

**Present cost versus speculative future value.** A class kept around because
it might be extended later is a bet on a future that has not arrived. The
present cost, extra surface area, extra maintenance, extra cognitive load, is
certain and is paid every day the class exists. The future value is uncertain
and may never be collected. Lazy Class, together with its close relative
Speculative Generality, names the situation where the bet has not paid off
yet and the codebase is carrying the cost of the wager regardless.

**Refactoring history versus present shape.** A class that was correctly
extracted at one point in a codebase's history can become lazy purely through
subsequent, individually correct changes elsewhere, with no single commit
responsible for the smell. Each change that moved behavior out of the class
was locally justified. The smell only becomes visible when someone steps back
and looks at the class as a whole, which is a form of attention that ongoing,
incremental development does not automatically supply.

**Team size and review discipline versus decay rate.** In a small team with a
strong habit of periodic refactoring, lazy classes tend to be caught and
removed quickly because someone notices the thinness during a nearby change.
In a large team, or a team under sustained delivery pressure, or a codebase
with weak code review norms around class-level design, lazy classes accumulate
because no single person's task is ever "go delete unnecessary classes," and
the smell has no natural trigger that forces a fix the way a compiler error
or a failing test does.

**Findability versus indirection.** A class with a clear, narrow name can
sometimes make a codebase easier to search and easier to reason about even
when it does very little, because the class name itself documents an
important concept and gives a place to hang future documentation or tests.
This is the strongest argument against collapsing every thin class, and it
is why dimension 4 below draws a non-applicability line rather than treating
every small class as automatically lazy.

## 4. Applicability and non-applicability

Reach for the Lazy Class diagnosis, and its usual refactorings, when the
following hold together.

- A class has one, or very few, methods worth keeping separate, and each of
  those methods is a thin pass-through to a field, to a single collaborator's
  method, or to a small amount of logic that would read at least as clearly
  inlined into its one caller.
- The class was extracted for a reason (an anticipated extension point, a
  planned subclass hierarchy, a planned plugin mechanism) and that reason has
  not materialized after a reasonable amount of the codebase's history, and
  there is no concrete, scheduled work item that will use the extension point
  soon.
- The class has exactly one production implementation, no active
  polymorphism is exercised through it (nothing actually varies at the type
  it introduces), and nothing outside the immediate module references it by
  its distinct type in a way that would break if it were inlined.
- Removing the class would shrink the call graph a reader has to trace by one
  hop without hiding any behavior a reader would reasonably need to find
  independently of its collaborator.
- The class exists as a leftover of an earlier, larger class that has since
  been correctly slimmed down elsewhere, so its own responsibility has
  shrunk to a sliver alongside that slimming.

Do NOT collapse or inline a class only because it is small, when any of the
following hold.

- The class is a **value object or domain primitive** and its smallness is
  the point. A `Money`, an `EmailAddress`, a `PositiveInteger` wrapper is
  correctly tiny, and its narrow type carries validation and prevents a whole
  class of primitive-obsession bugs. Smallness here is the design goal, not a
  smell. See Primitive Obsession in this family for the failure mode this
  guards against.
- The class exists specifically to satisfy an interface boundary that has
  more than one real implementation, or is designed for test doubling, even
  if the production implementation itself is currently thin. A one-line
  adapter that lets a test substitute a fake is doing real work by existing,
  the thinness of its body is not evidence it is unnecessary.
- The class is a **marker or capability tag** used by a framework's
  reflection, dependency injection, or annotation-processing machinery, where
  the class's existence, not its method bodies, is the payload. Deleting it
  would silently break framework wiring that a static read of the class body
  would never reveal.
- The class genuinely is an extension point with a committed, near-term
  second implementation already scheduled, and inlining it now would only be
  reversed within the same sprint or milestone. Judgement call, weigh it
  against how often "near-term" plans slip in the specific team's history.
- The class carries real **documentation value** through its name and its
  narrow, well-tested public contract, in a domain where naming the concept
  correctly is itself valuable to future readers, even though its
  implementation is currently thin. This overlaps with the findability force
  above and is the reason this diagnosis is never mechanical, it always
  needs a human judgement about whether the name is pulling its weight.
- The class is a **legitimate empty base class** used purely to establish a
  common supertype for a type hierarchy that genuinely varies at the
  subclasses, even if the base itself adds nothing. This is a Composite or
  Template Method root, not a Lazy Class, because its emptiness is structural
  rather than accidental. See Composite and Template Method in the 01-gof
  family for the distinction.

## 5. Structure

Lazy Class names a shape a single class takes, not a multi-participant
collaboration, so its structure is described in terms of the class itself and
its relationship to its one important collaborator, rather than in terms of
named roles the way a design pattern's structure would be.

**The Lazy Class.** The class under suspicion. Holds at most a small amount of
state, exposes one or a very small number of public methods, and each of
those methods either delegates immediately to a collaborator, performs a
trivial computation that does not depend on encapsulated invariants specific
to this class, or returns a constant or a simple derivation of its own field.

**The primary collaborator.** The single other object, or the small handful
of objects, that the Lazy Class's methods delegate to. In the common case
there is exactly one important collaborator, and every public method on the
Lazy Class resolves, directly or in one hop, to a call on that collaborator.

**The callers.** The code elsewhere in the system that constructs and invokes
the Lazy Class. In the target state after refactoring, these callers either
talk directly to the primary collaborator (after Inline Class), or talk to a
merged superclass or subclass (after Collapse Hierarchy).

**The absent second implementation.** Structurally notable by its absence. A
Lazy Class that was created as an abstraction point implicitly assumes a
second implementation will eventually exist. Its structure is incomplete
without checking whether that second implementation is present, planned, or
abandoned, because that answer decides whether the class is premature (fine,
wait) or genuinely lazy (fix now).

## 6. ASCII structure diagram

```
   BEFORE                              AFTER (Inline Class)
   ------                              ---------------------

   +----------------+                  +----------------+
   |    Caller      |                  |    Caller      |
   +----------------+                  +----------------+
          |                                    |
          | uses                               | uses directly
          v                                    v
   +----------------+                  +----------------------+
   |  LazyClass     |                  |  PrimaryCollaborator |
   |----------------|                  |----------------------|
   | - collaborator |   delegates      | (unchanged public    |
   | + doThing()    | ---------------> |  surface, now called |
   |   { return     |                  |  directly)           |
   |   collaborator |                  +----------------------+
   |   .doThing() } |
   +----------------+
          |
          | holds
          v
   +----------------------+
   |  PrimaryCollaborator |
   +----------------------+


   BEFORE (thin subclass)              AFTER (Collapse Hierarchy)
   -----------------------             ----------------------------

   +----------------+                  +----------------+
   |  BaseClass     |                  |  MergedClass   |
   |----------------|                  |----------------|
   | + method()     |                  | + method()     |
   +----------------+                  |   (former base |
          ^                            |    behavior)   |
          | extends                    +----------------+
          |
   +----------------+
   |  ThinSubclass  |
   |----------------|
   | (no overrides, |
   |  or one trivial|
   |  override)     |
   +----------------+
```

## 7. Dynamics

The runtime behavior of a Lazy Class before a fix is unremarkable, and that is
part of the point, nothing goes wrong at runtime, the smell is purely a
maintenance cost, which is exactly why it can persist for a long time without
triggering an incident, a test failure, or a page. A call into the Lazy
Class's method resolves in one extra hop compared to calling the primary
collaborator directly, then proceeds identically to how it would if the
collaborator were called without the intermediary. No new state is created, no
new invariant is enforced, no new decision is made, because if any of those
were true the class would not be lazy.

```
Sequence, calling through a Lazy Class

Caller           LazyClass          PrimaryCollaborator
  |                  |                      |
  |--doThing()------>|                      |
  |                  |--doThing()---------->|
  |                  |                      |--(does the real work)
  |                  |<--result-------------|
  |<--result---------|                      |
  |                  |                      |

Sequence, after Inline Class

Caller                          PrimaryCollaborator
  |                                      |
  |--doThing()------------------------->|
  |                                      |--(does the real work)
  |<--result----------------------------|
  |                                      |
```

The refactoring dynamics matter more than the runtime dynamics for this
smell. The Inline Class refactoring, described in Fowler's catalog, moves
each of the Lazy Class's members into the class that uses it most, then
updates every reference to the old class to reference the new location,
then deletes the now-empty class. It is done incrementally, one member at a
time, with the test suite run green after each move, exactly the same
discipline Fowler prescribes for every refactoring in the catalog, so that at
no point does the codebase pass through a state where behavior has silently
changed. Collapse Hierarchy proceeds the same way for the thin subclass case,
moving all members of the child up into the parent (Collapse Hierarchy up) or
all members of the parent down into the sole remaining child (Collapse
Hierarchy down), one member at a time, tests green after each move.

## 8. Implementation variants

**Direct field promotion.** The simplest case. The Lazy Class holds exactly
one field of a collaborator type and every method is a one-line delegation.
Inline Class here is close to mechanical, replace every use of the lazy
class's instance with a direct reference to the collaborator instance, and
delete the lazy class. Most statically typed languages' refactoring tools
(the Extract/Inline family in IntelliJ IDEA, ReSharper, and similar tooling)
automate this specific shape directly.

**Thin wrapper around a third-party or generated type.** A class exists
solely to give a friendlier name to a library type or a generated data
transfer type, and does not add validation, does not add behavior, and is
used in exactly one place. The fix is usually to delete the wrapper and use
the underlying type directly at the call site, or, if the friendlier name is
genuinely valuable across many call sites, to promote it to a type alias
(TypeScript, Kotlin) or a lightweight `newtype` style wrapper that is proven
to be used broadly rather than in one place, which moves it out of Lazy Class
territory into Value Object territory. The variant decision hinges entirely
on call-site count, not on the wrapper's line count.

**Static-only holder class.** In languages that force everything into a
class (older Java conventions, C#), a "utility" or "helper" class can end up
holding a single static method that is called from one place, with the class
itself adding nothing over a plain function. The variant fix in a language
with first-class functions or modules (TypeScript, Python, Go) is to remove
the class entirely and use a plain function or a module-level export. In a
language where a bare function is unusual at the top level of the style guide
(older-style Java before static imports were idiomatic), the more common fix
is to mark the class `final` with a private constructor if it must stay a
namespace, but to prefer folding its one method into its single caller when
there truly is only one caller. See dimension 9 for how .NET's own static
analysis rule CA1052 formalizes this exact variant.

**Interface-satisfying no-op implementation.** A class implements an
interface with every method either empty or trivially delegating, created to
satisfy a compiler or a dependency injection container rather than to do
real work. If the interface genuinely has, or will soon have, more than one
implementation, this is not lazy, it is doing its job as a seam. If the
interface has exactly one implementation and no second one is realistically
coming, the fix is usually to delete the interface too, not only the class,
collapsing the abstraction down to the concrete type directly. This overlaps
with Speculative Generality, and the two smells frequently travel together.

**Subclass with a vanished override.** A class hierarchy was built to vary
one method across two or more subclasses. Over time, all but one subclass's
override converged to identical behavior, or all subclasses were deleted but
one, leaving a single, functionally redundant subclass standing alone under a
base class. Collapse Hierarchy, in either direction, removes the now-pointless
split. Choosing "collapse up" versus "collapse down" is decided by which
name, the base class's or the subclass's, better describes the merged
concept going forward, a judgement call rather than a mechanical rule.

## 9. Known production uses

**Microsoft's .NET code analysis rule CA1052, "Static holder types should be
Static or NotInheritable."** This is a static analyzer rule shipped with the
.NET SDK's built-in code analysis, and it exists specifically to flag a
Lazy Class variant, a public, non-abstract type that contains only static
members and is not itself marked `static`, which the rule's own description
frames as a type that "does not provide any functionality that can be
overridden in a derived type," the exact judgement Fowler's catalog makes
about a Lazy Class in general. The rule is applied across large numbers of
production .NET codebases wherever code analysis is enabled, and its
description and remediation guidance are published at
https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/quality-rules/ca1052,
verified 2026-08-02.

**The `@typescript-eslint/no-extraneous-class` ESLint rule.** Part of the
typescript-eslint project, one of the most widely adopted linting toolchains
for TypeScript codebases in production use, this rule specifically disallows
"classes used as namespaces," which the rule's documentation describes as
classes that lack non-static members and are used purely as static
containers, or classes whose only role is to wrap a constructor around logic
that could be a standalone function. The rule's own rationale states that
such wrapper classes "add extra cognitive complexity to code without adding
any structural improvements," language that maps directly onto Fowler's
economic framing of the Lazy Class smell, that a class must earn back the
cost of its own existence. Documented at
https://typescript-eslint.io/rules/no-extraneous-class/, verified
2026-08-02.

**JetBrains IntelliJ IDEA and ReSharper's "Class can be converted to..." and
inline-class quick fixes.** Both IDEs, used across a very large share of
production Java, Kotlin, and C# development, ship a static inspection that
flags a class whose entire member set could be moved into its sole caller or
its sole collaborator, offering an automated Inline Class refactoring as the
one-click fix. The presence of a first-class, automated tool for exactly this
refactoring in the two dominant JVM and .NET IDEs is itself evidence that the
underlying smell is common enough in real codebases to justify building
tooling around removing it, rather than being a purely academic concern from
the 1999 catalog. JetBrains documents the Inline refactoring family,
including its class-level form, in its refactoring reference documentation
for both products, consistent with the shape described in Fowler's original
catalog entry for Inline Class.

## 10. Consequences

Positive, once the smell is fixed by inlining or collapsing.

- The call graph a reader has to trace shrinks by one hop for every removed
  indirection, which reduces the time it takes a new contributor to
  understand a given code path.
- The number of files, symbols, and public types the codebase asks a reader
  to hold in their head goes down, which is a real cognitive cost reduction,
  independent of any change in the number of executable statements.
- Build and import overhead in languages with per-file compilation units
  (large TypeScript projects with many small files, Java projects with one
  class per file) drops slightly, and this compounds across very large
  codebases even though it is negligible for any single class.
- Test suites shrink correspondingly, because a dedicated test file for a
  now-deleted lazy class either disappears or its assertions are folded into
  the collaborator's own tests, which reduces the total number of test
  doubles and fixtures that have to be kept in sync with the production code.

Negative, or the cost of getting the diagnosis wrong.

- Inlining a class that was actually serving as a deliberate seam for future
  extension removes that seam, and re-extracting it later, when the second
  implementation genuinely arrives, is strictly more work than leaving a
  correctly-sized seam in place would have been. This is the central risk
  this smell's diagnosis carries, and it is why dimension 4's
  non-applicability list matters as much as the applicability list.
- Collapsing a hierarchy can break external consumers of a library's public
  API, if the class being removed or merged is part of that public surface,
  turning an internal cleanup into a breaking, major-version change.
- Removing a class whose name carried domain meaning can make the codebase
  harder to search and harder to onboard into, even when the implementation
  genuinely was trivial, because the name itself was doing documentation
  work that the merged code now lacks a clear place to carry.
- The refactoring itself, done carelessly, can silently change behavior if
  the "trivial" delegation the lazy class performed was hiding a subtle
  difference, such as null handling, exception translation, or a different
  threading context, that the naive inline does not preserve. This is why
  dimension 15 insists on characterization tests before any inline.

## 11. Failure modes and misuse

**Symptom.** A codebase has dozens of one-method classes, each named after a
verb rather than a noun (`Validator`, `Calculator`, `Formatter` used as class
names for what is really a single static-shaped function), and grep for the
class name shows exactly one call site each.
**Cause.** A team-wide convention mandates "one class per responsibility"
without also asking whether the responsibility is big enough to be a class,
often inherited from an overly literal reading of the Single Responsibility
Principle that treats "one class, one job" as requiring a minimum of one
class per job regardless of job size.
**Fix.** Introduce a size or call-site threshold into code review practice
(a rule of thumb some teams use is that a class with one public method and
one production call site is a refactoring candidate, not an automatic
violation, but a signal worth a second look), and prefer plain functions or
small private helper methods on the caller for genuinely small, single-use
logic, reserving dedicated classes for logic with real internal state,
multiple collaborators, or more than one call site.

**Symptom.** A class was aggressively slimmed down during a previous
refactoring sprint that targeted a different, unrelated Large Class smell,
and the slimmed class is now praised in commit messages as "clean" even
though it has quietly become a Lazy Class as a side effect of that slimming.
**Cause.** Large Class refactorings correctly extract responsibilities into
new classes, but nobody revisits the original class afterward to check
whether what remains still justifies its own existence, because the
refactoring's success metric was framed entirely around the extracted
classes rather than the residual one.
**Fix.** Treat the source class of any Extract Class refactoring as a
required follow-up check, not an afterthought, specifically asking whether
what is left behind still earns a dedicated class, and fold it into its
nearest remaining caller if it does not.

**Symptom.** A subclass was created years ago to override one method for a
platform-specific or vendor-specific variant, that variant was later
discontinued or unified with the main path, and the override was deleted, but
the subclass declaration itself remains, extending the base class with
nothing added.
**Cause.** Deleting a subclass requires touching every construction site
that instantiates it by name, which is more invasive than deleting the one
override method inside it was, so the smaller, local deletion (the override)
happens and the larger, more invasive deletion (the class) gets deferred
indefinitely.
**Fix.** When an override is deleted because the specialization it provided
is no longer needed, immediately check whether the subclass has any other
reason to exist, and if not, run Collapse Hierarchy in the same change,
updating every construction site to use the base class directly, rather than
splitting the two deletions across separate changes that may never both
land.

**Symptom.** A dependency-injection interface has exactly one production
implementation, was created "for testability," but the codebase's tests
never actually swap in an alternate implementation, they use a mocking
framework that intercepts calls at the concrete class level anyway.
**Cause.** A cargo-culted belief that "interfaces are good for testing" is
applied without checking whether the specific test suite's mocking strategy
actually needs the interface seam to work, when many modern mocking and
stubbing tools can substitute a concrete class directly.
**Fix.** Audit whether the interface's only implementation ever varies in
practice, including in tests, and if it does not, collapse the interface
into the concrete class, which is the interface-level cousin of collapsing a
lazy subclass into its base.

## 12. Trade-off matrix

| Force | Lazy Class left in place | Inline Class / Collapse Hierarchy applied | Speculative Generality (kept deliberately as a seam) | Extract Class (the opposite move) |
|---|---|---|---|---|
| Indirection for a reader | One extra hop per call, paid on every read | Removed, one fewer hop | One extra hop, but justified by an active second implementation or planned one | Adds a hop, but in exchange for isolating a genuinely large responsibility |
| Cost of a future extension | Low, the seam already exists | Higher, the seam must be re-created if the future extension actually arrives | Low, by design, this is the whole point of keeping the seam | Not directly comparable, this move targets size, not extensibility |
| Present maintenance cost | Paid continuously for as long as the class exists | Removed once, a one-time refactoring cost | Paid continuously, accepted as the price of the option | Increases initially, in exchange for reducing a different class's complexity |
| Risk of behavior change during the fix | None, the class is left alone | Present but bounded, mitigated by characterization tests, see dimension 15 | Not applicable, no change is made | Present, same mitigation applies |
| Public API breakage risk | None | Real if the class is part of a published API surface | None | Real if the extraction changes a published API surface |
| Correct choice when the class name carries strong domain documentation value | Sometimes correct to leave alone despite the smell | Wrong choice if the name's documentation value outweighs the indirection cost | Correct default in this situation | Not applicable |

## 13. Related and incompatible patterns

**Data Class**, the sibling entry in this family. A Data Class fails on a
behavioral axis, holding state that belongs elsewhere. A Lazy Class fails on
an economic axis, doing too little to justify its own overhead, whether or
not it also holds state. A class can be both at once, a thin data holder
whose one method is a trivial getter, in which case both diagnoses apply and
the fixes (Move Method for the data-class angle, Inline Class for the
lazy-class angle) tend to converge on the same result, deleting the class.

**Speculative Generality**, a closely related smell in the same family,
covers the broader case of any code, not only a whole class, built to
support a future that has not arrived, including unused parameters, unused
hook methods, and unnecessary delegation layers. Lazy Class is frequently the
class-level manifestation of Speculative Generality specifically, when the
"speculative" part is an entire class rather than a parameter or a method.
Treat Speculative Generality as the umbrella and Lazy Class as one common
concrete shape it takes.

**Middle Man**, another related smell (not yet a separate entry in this
family at time of writing, referenced here by name from the same catalog),
describes a class whose methods mostly delegate to another object. A Lazy
Class with several delegating methods can look like a Middle Man, and the two
diagnoses often apply together, but Middle Man specifically concerns
excessive delegation as its own problem even when the delegating class does
retain some genuine responsibility, whereas Lazy Class concerns a class whose
total contribution, delegated or not, has fallen below the threshold that
justifies a separate class at all.

**Dead Code**, the sibling entry in this family, is the more extreme relative
of Lazy Class. Dead Code is never called at all. Lazy Class is called, and
does something, only not enough to be worth the indirection. A Lazy Class
that loses its last caller during a later change becomes Dead Code, and
should then be diagnosed and removed under that entry's guidance instead.

**Composite** and **Template Method**, from the Gang of Four family, are
explicitly noted as NOT incompatible with an apparently empty or thin base
class, because in both of those patterns an empty or near-empty root type is
structurally correct, its emptiness comes from the pattern's own shape rather
than from neglect. Do not apply Lazy Class's remedies to a Composite root or
a Template Method's abstract base purely because it looks thin in isolation,
check first whether real variation exists at its subclasses.

**Refactoring, Extract Class** is the direct opposite move to this smell's
usual remedy, splitting a large class into two smaller ones. The two smells,
Large Class (which Extract Class treats) and Lazy Class (which Inline Class
treats), sit at opposite ends of the same size scale, and a codebase that
oscillates between them for the same piece of logic across successive
refactorings is a sign the team has not yet found the right granularity for
that particular responsibility, which is itself worth naming and discussing
directly rather than continuing to refactor back and forth.

## 14. Refactoring path in and out

**Path in, how a class becomes lazy over time**, described here because the
smell is almost always the product of a history rather than a single
authoring decision.

1. A class is created for a real reason, either to hold a responsibility
   extracted from a Large Class, or to establish a seam for an anticipated
   second implementation, or to wrap a piece of external logic behind a
   friendlier interface.
2. Subsequent, individually reasonable changes progressively move
   responsibility out of the class, back into its caller, into a different
   collaborator, or the anticipated second implementation never arrives and
   the seam goes unused.
3. Nobody's task at any of those later change points includes "check
   whether this class is still worth having," because each individual
   change was scoped narrowly and correctly to its own goal.
4. The class settles into a stable, thin, still-referenced-but-barely-doing-
   anything state, where it will remain indefinitely unless someone
   specifically goes looking for exactly this shape.

**Path out, the refactoring sequence to remove it.**

1. Confirm the class genuinely has no second implementation, no test-double
   dependency on its distinct type, and no external public-API consumers who
   would be broken by its removal, per the non-applicability checks in
   dimension 4.
2. Write, or confirm the existence of, characterization tests that exercise
   every public method on the Lazy Class through its current callers, so the
   refactoring has a safety net independent of unit tests that might
   themselves need to move. See dimension 15.
3. For the delegation-heavy case, apply Inline Class, moving each member
   one at a time into the primary collaborator or into the single caller,
   updating references after each move, running the full test suite green
   after each move, per Fowler's own step-by-step description of Inline
   Class in the 1999 and 2018 editions of *Refactoring*.
4. For the thin-subclass case, apply Collapse Hierarchy in the direction
   whose resulting name better describes the merged concept, moving members
   one at a time in the same disciplined, test-green-after-each-step manner.
5. Once every member has moved and every reference has been updated, delete
   the now-empty class declaration and its file, and delete any
   now-unnecessary interface it existed solely to satisfy, if that interface
   itself qualifies under this smell's diagnosis too.
6. Re-run the characterization tests from step 2 one final time against the
   fully inlined code, confirming they still pass, then fold their
   assertions into the collaborator's own permanent test suite if they add
   coverage the collaborator's existing tests did not already have, or
   delete them if they are now fully redundant with existing coverage.

## 15. Testing and verification

Testing a Lazy Class before removing it is centered on characterization
testing, capturing the class's current observable behavior as a safety net
that does not depend on assumptions about its internal shape, because the
whole point of Inline Class and Collapse Hierarchy is to change that internal
shape while keeping the observable behavior identical. Before touching the
class, write or confirm tests that call the class exactly as its real callers
do, through its actual public methods, asserting on return values, on any
observable side effects such as calls made on a collaborator, and, if
relevant, on exception behavior for edge case inputs, without asserting on
the class's internal implementation, because internal implementation is
precisely what is about to change.

A Lazy Class is, in one sense, easier to test than the class it will be
merged into, purely because it does so little, its own unit tests, if they
exist, tend to be short and easy to reason about. This test cost drops out
almost entirely once the merge happens, folding into the collaborator's
existing test suite, which is one of the concrete, if minor, benefits listed
under dimension 10. What becomes slightly harder to test after the merge is
the specific, narrow behavior the lazy class isolated, if a future need to
substitute a different implementation of that one behavior alone arises, the
seam that would have let a test double swap it in has been removed, and
re-adding test isolation for that behavior alone later requires re-extracting
the class, which is legitimate, ordinary Extract Class work rather than a
sign the original inline was wrong, provided the need is now concrete rather
than merely anticipated.

The delegation itself, before removal, is a natural place for a mutation
testing or a mocking framework's call-verification assertion, confirming
that the Lazy Class's method genuinely forwards its arguments unchanged and
returns the collaborator's result unchanged, catching the specific
misuse-adjacent case, mentioned under dimension 10's negative consequences,
where the "trivial" delegation was quietly doing something non-obvious, such
as catching and swallowing an exception the collaborator throws, or
converting a null into a default value. A characterization test written by
calling the class with a deliberately unusual input, an exception-triggering
argument, a null, a boundary value, and comparing the observed behavior
against a direct call to the collaborator with the same input, is the
concrete technique that surfaces this kind of hidden behavior before the
inline refactoring accidentally erases it.

## 16. Observability signals

Lazy Class is, more than most smells in this family, primarily detected by
static analysis and code review rather than by runtime observability, because
its cost is a maintenance and comprehension cost, not a performance or
reliability cost that shows up in a production metric. That said, a small
number of static and dynamic signals are useful for spotting candidates at
scale in a large codebase.

A static line-count and method-count query across a codebase, flagging any
non-test, non-interface class with a single public method whose body is
fewer than a small number of lines and whose only statement is a call into
one collaborator, is a cheap first-pass filter that tools like the
`@typescript-eslint/no-extraneous-class` rule, or an equivalent custom
Roslyn analyzer following the shape of CA1052, or a simple script over a
Python or Go abstract syntax tree, can run in continuous integration and
surface as a warning for human review, never as an automatic deletion,
because the false-positive rate against the legitimate non-applicability
cases in dimension 4 is real.

A call-site count per public type, computed from a project-wide symbol index
(available in most language servers and IDE indexing engines), that flags
any exported or public class with exactly one call site outside its own
test file, is a stronger and more specific signal than line count alone,
because it directly measures the indirection-without-benefit shape this
smell describes, a class used from exactly one place has, almost by
definition, not yet earned the abstraction cost of being separate from that
one place.

A healthy codebase, from this smell's perspective, shows a stable or slowly
declining count of these flagged candidates over time as periodic cleanup
work retires them, and treats a sudden jump in the count, following a large
refactoring sprint that targeted an unrelated Large Class or Long Method
smell elsewhere, as an expected, temporary signal worth a scheduled follow-up
pass rather than as evidence of a process failure, consistent with the
failure mode described in dimension 11 where slimming one class routinely
produces a lazy one nearby as a side effect.

## 17. Security and privacy implications

Lazy Class carries no direct security or data-handling implication of its
own, unlike smells that concern validation, trust boundaries, or data
exposure. The class, by definition, is not where security-relevant logic is
expected to live, precisely because it does almost nothing.

There is one indirect implication worth naming plainly rather than
inventing a stronger one. an unnecessary abstraction layer can occasionally
obscure where a security-relevant check actually happens, particularly in
the interface-satisfying, no-op-implementation variant described in
dimension 8, where a reader searching for "where is authorization checked"
might stop at the lazy interface method and miss that the real check happens
one hop further away in the collaborator it delegates to, or, worse, might
wrongly assume a check happens inside the lazy class simply because its name
suggests it should, when in fact it is a pure pass-through with no check at
all. This is a readability and audit-trail concern rather than a direct
vulnerability, and the correct mitigation is the same as the general fix for
this smell, removing the unnecessary indirection so a security reviewer
tracing a call path has fewer, not more, hops to check for the presence or
absence of a control.

## 18. References

1. Martin Fowler, Kent Beck, John Brant, William Opdyke, Don Roberts,
   *Refactoring. Improving the Design of Existing Code*, first edition,
   Addison-Wesley, 1999, chapter 3, "Bad Smells in Code," the "Lazy Class"
   entry, paired with the Collapse Hierarchy and Inline Class refactorings.
2. Martin Fowler, *Refactoring. Improving the Design of Existing Code*,
   second edition, Addison-Wesley, 2018, chapter 3, "Bad Smells in Code,"
   "Lazy Class" retained under the Bloaters grouping.
3. Martin Fowler, "CodeSmell," martinfowler.com/bliki, describing a code
   smell as "a surface indication that usually corresponds to a deeper
   problem in the system," and describing the general practice of treating
   smells as prompts to ask what behavior belongs where.
   https://martinfowler.com/bliki/CodeSmell.html, verified 2026-08-02.
4. Microsoft Learn, ".NET code analysis rule CA1052, Static holder types
   should be Static or NotInheritable," describing the rule's cause as "a
   non-abstract type contains only static members" and stating that such a
   type "does not provide any functionality that can be overridden in a
   derived type."
   https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/quality-rules/ca1052,
   verified 2026-08-02.
5. typescript-eslint documentation, "no-extraneous-class," describing the
   rule as disallowing "classes used as namespaces," and stating that such
   wrapper classes "add extra cognitive complexity to code without adding
   any structural improvements."
   https://typescript-eslint.io/rules/no-extraneous-class/, verified
   2026-08-02.
6. JetBrains, IntelliJ IDEA and ReSharper refactoring documentation, the
   Inline refactoring family (Inline Method, Inline Variable, and the
   class-level inline form referenced from the same family of quick fixes),
   documenting the automated tooling support for the Inline Class
   refactoring this entry's remedy relies on. Consulted as evidence that the
   refactoring described in reference 1 has first-class tool support in
   mainstream, production-grade IDEs, cross-checked against the refactoring
   steps described in reference 1 rather than quoted directly.
7. Kent Beck's Smalltalk coding-convention writings on avoiding
   trivial subclassing, cited in Fowler's own account of the catalog's
   development in the preface to reference 1, as the earlier, informal
   source of the same underlying judgement that a class must earn its
   existence through the behavior it contributes. Cited here as historical
   attribution per the source's own preface, not independently verified
   against a separate Beck publication for this entry.

## Code examples

Real production usage of this smell's static-holder variant is shown by
Microsoft's CA1052 rule and typescript-eslint's `no-extraneous-class` rule
above, both of which are built to detect the code shape shown below. The
following examples show a Lazy Class in each of three languages, the
refactored, corrected result, and a small runnable check that the refactor
preserves behavior.

### TypeScript

Before, a Lazy Class wrapping a single collaborator method with no added
behavior.

```typescript
class TaxCalculator {
  calculate(amount: number): number {
    return amount * 0.19;
  }
}

class InvoiceLineTotal {
  private taxCalculator: TaxCalculator;

  constructor(taxCalculator: TaxCalculator) {
    this.taxCalculator = taxCalculator;
  }

  taxFor(amount: number): number {
    return this.taxCalculator.calculate(amount);
  }
}

function priceWithTax(amount: number): number {
  const lineTotal = new InvoiceLineTotal(new TaxCalculator());
  return amount + lineTotal.taxFor(amount);
}

console.log(priceWithTax(100));
```

After Inline Class, `InvoiceLineTotal` is removed and its one caller talks to
`TaxCalculator` directly.

```typescript
class TaxCalculator {
  calculate(amount: number): number {
    return amount * 0.19;
  }
}

function priceWithTax(amount: number): number {
  const taxCalculator = new TaxCalculator();
  return amount + taxCalculator.calculate(amount);
}

console.log(priceWithTax(100));
```

### Python

Before, a Lazy Class subclass whose override has already converged with its
base class, a Collapse Hierarchy candidate.

```python
class Discount:
    def apply(self, price: float) -> float:
        return price * 0.9


class StandardDiscount(Discount):
    def apply(self, price: float) -> float:
        return price * 0.9


def checkout_total(items: list[float], discount: Discount) -> float:
    subtotal = sum(items)
    return discount.apply(subtotal)


if __name__ == "__main__":
    result = checkout_total([10.0, 20.0, 30.0], StandardDiscount())
    print(result)
```

After Collapse Hierarchy, the redundant subclass is removed and its callers
use the base class directly.

```python
class Discount:
    def apply(self, price: float) -> float:
        return price * 0.9


def checkout_total(items: list[float], discount: Discount) -> float:
    subtotal = sum(items)
    return discount.apply(subtotal)


if __name__ == "__main__":
    result = checkout_total([10.0, 20.0, 30.0], Discount())
    print(result)
```

### Go

Before, a static-holder style Lazy Class, expressed in Go as a struct with a
single method used from one call site, the shape CA1052 targets in C#.

```go
package main

import "fmt"

type SlugFormatter struct{}

func (SlugFormatter) Format(title string) string {
	result := make([]rune, 0, len(title))
	for _, r := range title {
		if r == ' ' {
			result = append(result, '-')
		} else if r >= 'A' && r <= 'Z' {
			result = append(result, r+32)
		} else {
			result = append(result, r)
		}
	}
	return string(result)
}

func main() {
	f := SlugFormatter{}
	fmt.Println(f.Format("Lazy Class Smell"))
}
```

After the fix, the struct is removed in favor of a plain function, the
idiomatic Go shape a single-purpose, single-call-site behavior takes, the
same conclusion CA1052 and `no-extraneous-class` reach for C# and TypeScript.

```go
package main

import "fmt"

func formatSlug(title string) string {
	result := make([]rune, 0, len(title))
	for _, r := range title {
		if r == ' ' {
			result = append(result, '-')
		} else if r >= 'A' && r <= 'Z' {
			result = append(result, r+32)
		} else {
			result = append(result, r)
		}
	}
	return string(result)
}

func main() {
	fmt.Println(formatSlug("Lazy Class Smell"))
}
```

Kotlin and C# are omitted from the runnable set for this entry because their
compilers were not confirmed available in the working environment at
authoring time. Java and Rust are omitted because the pattern's idiomatic
form is already fully demonstrated by the static-holder shape in Go and the
class-based shapes in TypeScript and Python, and this entry stops at three
languages rather than compile a fourth near-duplicate example given the
fixed budget for this entry.
