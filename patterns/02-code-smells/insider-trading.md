---
name: Insider Trading
slug: insider-trading
family: 02-code-smells
category: Coupling
aliases: [Inappropriate Intimacy (1999 name), Excessive Module Coupling]
first_described: "Fowler 2018 (renaming Fowler and Beck 1999)"
maturity: canonical
related: [inappropriate-intimacy, feature-envy, shotgun-surgery, divergent-change, message-chains, middle-man, hide-delegate, move-method, extract-class]
incompatible_with: []
verified: 2026-08-02
---

# Insider Trading

## 1. Name, aliases, and lineage

The canonical name used here is Insider Trading, the heading Martin Fowler gives
this smell in the second edition of the book that introduced the whole idea of a
code smell as a named, catalogued thing worth refactoring away. Martin Fowler,
*Refactoring. Improving the Design of Existing Code*, 2nd edition,
Addison-Wesley, 2018, ISBN 978-0134757599, Chapter 3, "Insider Trading". The
first edition of the same book, co-credited on the smells chapter to Kent Beck,
listed a smell under a different name in 1999 for essentially the same
underlying pressure, Inappropriate Intimacy, described as two classes that are
too interested in each other's private parts. Martin Fowler and Kent Beck,
*Refactoring. Improving the Design of Existing Code*, 1st edition,
Addison-Wesley, 1999, ISBN 0-201-48567-2, Chapter 3.

The rename is a documented, deliberate change, not an accident of two different
authors independently coining similar terms. A community-maintained catalogue
that cross-references both editions of the book records the 1999 name as
retired and the 2018 name as its replacement, and notes that the scope moved up
one level of granularity from a pair of classes to a pair of modules in the
process. luzkan.github.io, "Insider Trading",
https://luzkan.github.io/smells/insider-trading, verified 2026-08-02. This
repository keeps Inappropriate Intimacy as its own separate entry, because a
working reader still encounters that 1999 name constantly in older articles,
static analysis tool output, and code review vocabulary that has not caught up
with a 2018 rename, and because the two names, in practice, get applied at two
different scales. Dimension 13 below spells out exactly how this entry and that
one divide the same territory.

The word choice is the pattern's own best mnemonic. In securities law, insider
trading means someone with privileged, non-public information about a company
uses that information to their advantage in a transaction that should have been
conducted at arm's length. In code, the smell is the same shape at the module
level. Two modules that should interact only through their published,
public-facing surface have instead worked out a private back channel, each
knowing details about the other's internals that a third module, playing by the
public rules, is not allowed to know. Fowler's own reason for the rename,
according to the same corroborating catalogue, was to make it clear the concern
had generalised from a pair of classes reaching into each other's fields to a
pair of packages, modules, or services reaching into each other's
implementation, which the older name's wording did not signal.

## 2. Problem and context

Two modules were designed to talk to each other through a small, deliberate
interface, and over time they grew a second, informal interface nobody
designed. The second interface is made of direct field access across a package
boundary, a `friend` declaration reached for once and then reused everywhere,
a shared mutable object both sides read and write without either one owning
it, or a pair of classes that were split apart for a good reason but that keep
reaching back across the split to finish each other's sentences.

The context in which this actually happens is almost always the same story told
twice. A feature starts life as one class, gets too large, and a second class is
extracted from it under time pressure, the code-review equivalent of a hasty
divorce. The two halves used to be one, so they still know each other's private
state intimately, and the extraction did not bother to hide it, because hiding
it looked like extra work with no visible payoff that sprint. Or, the story
runs the other way. Two modules were designed as siblings from the start, each
owned by a different developer or a different team, and each one, needing one
piece of data the other holds privately, reached in through whatever access
modifier happened to be lax enough to let it, rather than asking the owning
module to publish that data properly.

Either way, the resulting code has one recognisable shape. Change one of the
two modules, and you cannot predict, from reading only that module, whether the
other one still compiles or still behaves correctly, because the contract
between them is not written down anywhere. It lives only in the accident of
which fields happened to be public, which package happened to be on the friend
list, and which developer happened to remember the informal agreement. This is
the same underlying failure that dimension 3 names as excess coupling, but the
distinguishing feature of Insider Trading specifically, as opposed to a merely
tangled dependency graph, is that the coupling runs through PRIVATE state.
Two modules calling each other's public methods a great deal is Feature Envy or
a plain design question about where behaviour belongs. Two modules reaching
past each other's public surface into fields, internal collections, or
package-private helpers that were never meant for outside consumption, that is
Insider Trading, and the fix is different because the leak is different.

## 3. Forces

- **Coupling.** Sacrificed, and this is the smell's entire subject matter.
  Insider Trading is what happens when the coupling between two modules is not
  merely present but is routed through the one channel that was supposed to
  stay private, so a change to internal representation on either side can
  silently break the other.
- **Encapsulation.** Sacrificed directly. Encapsulation exists to let a module's
  author change its internal representation without warning anyone. Insider
  Trading is the exact condition under which that promise becomes false,
  because someone outside the module is depending on the representation, not
  the interface.
- **Development velocity, short term.** Favoured, which is why the smell
  survives so long in real codebases. Reaching directly into a neighbour's
  field is almost always the fastest way to get a feature working today, and it
  produces a diff that looks smaller than the alternative of extending a public
  interface, writing a getter, or asking another team to expose something new.
- **Development velocity, long term.** Sacrificed, and the cost compounds. Each
  additional private back channel between two modules adds one more thing a
  future refactor of either side has to discover and preserve, and back
  channels are, by construction, undocumented and untested against directly,
  because nobody wrote a public contract for them.
- **Team topology.** Sacrificed when the two modules are owned by different
  teams. A private back channel is a dependency that the owning team's public
  API surface, its versioning discipline, and its deprecation process all fail
  to see, so the consuming team can be broken by a change the owning team
  believed was purely internal and safe.
- **Change locality.** Sacrificed. A well-encapsulated module can be rewritten
  internally with zero effect on its callers. A module entangled in Insider
  Trading cannot be rewritten internally at all without first finding and
  fixing every private channel a neighbour has opened into it, which is exactly
  the Shotgun Surgery smell viewed from the victim's side.
- **Runtime cost.** Roughly neutral on its own. Direct field access, a friend
  relationship, or a package-private call each usually cost no more at
  runtime than the equivalent call through a proper interface would, in most
  managed and compiled languages. The cost this smell imposes is a design and
  organisational cost, not a CPU cycle count.

## 4. Applicability and non-applicability

Insider Trading is a smell, never a technique to reach for on purpose in the
general case, so this dimension is framed differently from a design pattern
entry. The first list below is when the SYMPTOM described in dimension 2
genuinely indicates a problem worth fixing. The second list is when what looks
like the symptom is not the smell at all, and refactoring it away would remove
something that is doing real, intentional work.

Treat it as the real smell, worth fixing, when:

- Two modules owned by different people, or different teams, read or write
  each other's private fields, internal collections, or package-private
  methods, and no documented contract describes what is being shared or why.
- A change made entirely inside one module's stated responsibility regularly
  breaks tests or behaviour in a second module that was never told about the
  change, and tracing why takes longer than the change itself took to write.
- The private channel between the two modules has grown organically, one field
  access at a time, rather than being a single, reviewed, deliberate decision
  to expose a specific piece of shared state.
- A `friend` declaration, an `internal` visibility grant, or a qualified module
  export exists in the code but nobody involved in the current team could say,
  without reading the code, what it is for or whether it is still needed.
- The two modules were one module recently, were split for a legitimate reason
  such as size or team ownership, and the split never finished, so half the
  seams that should have become public interface calls are still direct field
  reads left over from when it was all one class.

Do NOT reach for a fix, or do not treat what you are looking at as this smell,
when:

- **The two types are a genuine, tightly bound pair by design, and both live in
  the same module under one owner.** A private linked-list node class that only
  its owning list ever touches is not Insider Trading, it is ordinary
  encapsulation working exactly as intended, with the privacy scoped correctly
  to the pair rather than to either type alone. The Composite pattern's
  internal child-parent back-references are the same case.
- **The privileged access is granted through an explicit, reviewed, narrow
  language mechanism rather than through accidental laxity.** A C++ `friend`
  class, a Java qualified module export naming exactly one consumer, or a C#
  `InternalsVisibleTo` attribute naming exactly one test assembly is a
  deliberate, auditable declaration of intimacy, not an accident. Dimension 9
  covers these mechanisms as the industry's answer to doing this safely when it
  is genuinely needed. The smell is the UNDECLARED, UNBOUNDED version of the
  same idea, not the declared and bounded one.
- **The shared state is exposed through a real, versioned, public API, even if
  that API happens to be very small.** A getter and a matching setter, both
  documented and both part of the module's contract, are not a back channel
  merely because they are narrow. The test in dimension 2 is whether the
  contract is written down and stable, not how many members it has.
- **The two modules are a test suite and the production code it tests.** A test
  frequently, and correctly, reaches into implementation detail that a normal
  caller never should, in order to assert on internal state directly rather
  than through slow or indirect black-box behaviour. This is intimacy by
  design, scoped to test code, and mechanisms like Python's convention of a
  leading `_` marking a member as private, Go's same-package test files, or a language's dedicated
  test-visibility attribute exist precisely to make this sanctioned case
  distinct from production-to-production Insider Trading.
- **The relationship is a one-time migration shim with a known removal date.**
  A temporary bridge that lets two modules share internal state while a
  boundary is being redrawn is a deliberate, tracked debt, not an accidental
  smell, provided it is actually tracked and actually removed on schedule. If
  the shim outlives its migration and nobody remembers why it exists, it has
  quietly become the real smell.

## 5. Structure

Two participants and one accidental channel, described by role rather than by
generic class name.

- **HostModule.** The module whose private state, internal collection, or
  package-private behaviour is being read or mutated from the outside. It has a
  public surface it intends callers to use, and a private surface it does not.
- **IntrudingModule.** The module that reaches past HostModule's public surface
  and touches the private one directly, usually because that was the fastest
  or only way, at the time it was written, to get a needed piece of information
  or trigger a needed side effect.
- **The BackChannel.** Not a class, a relationship. It is whichever mechanism
  the language allowed to be abused for this, a public field on a type that
  should have been private, a `friend` declaration granted broadly and never
  revisited, a package-private method called from outside its intended package
  through reflection or a same-package escape hatch, or a shared mutable
  object both sides hold a reference to and both sides write.
- **PublicContract, absent.** The signature of this smell is precisely that no
  participant of this name exists. A healthy pair of modules has a
  PublicContract, an interface, a published function, an event, standing
  between HostModule and any caller. Insider Trading is what remains when that
  participant is missing and the BackChannel has taken its place.

## 6. ASCII structure diagram

```
   THE SMELL, AS FOUND

   +-------------------+                    +-------------------+
   |    HostModule      |                    |  IntrudingModule   |
   |---------------------|                   |---------------------|
   | + publicMethod()    |                    | + doWork()         |
   | - privateField      |<== direct read ===| (reaches straight   |
   | - internalHelper()  |<== direct call ===|  past the public    |
   |                      |                    |  surface)           |
   +-------------------+                    +-------------------+
             ^                                          |
             |            no PublicContract exists       |
             +---------------- gap -----------------------+
             (nothing documents or versions this channel)


   THE FIX, AFTER HIDE DELEGATE OR EXTRACT CLASS

   +-------------------+     PublicContract    +-------------------+
   |    HostModule      |<---------------------|  IntrudingModule   |
   |---------------------|   (interface,       |---------------------|
   | + publicMethod()    |    published call,  | + doWork()         |
   | - privateField      |    or event)         | (calls only the    |
   | - internalHelper()  |--------------------->|  public surface)   |
   +-------------------+                       +-------------------+

   The BackChannel is deleted. Everything that crossed the boundary
   now crosses through one named, tested, versioned seam.
```

## 7. Dynamics

The runtime behaviour of the smell has no special sequence of its own, because
the whole point is that there is no designed protocol, only ad hoc reads and
writes whenever IntrudingModule happens to need something. What is worth
tracing is the FAILURE sequence this produces, because that sequence is what a
team actually experiences and what makes the smell expensive.

```
Developer A          HostModule internals        IntrudingModule (owned by B)
     |                        |                              |
     |-- refactors internal  |                                |
     |   representation ---->|                                |
     |   (renames a field,   |                                |
     |    changes a type,    |                                |
     |    all tests in A's   |                                |
     |    own module pass)   |                                |
     |                        |                                |
     |-- merges, ships ------>|                                |
     |                        |                                |
     |                        |<== B's build breaks or, worse,|
     |                        |    silently misbehaves, ------|
     |                        |    because IntrudingModule was |
     |                        |    reading the field A had recently|
     |                        |    renamed or reinterpreted    |
     |                        |                                |
Developer B          runs a bisect, or a debugger, and only THEN
     |                discovers a private channel that nothing
     |                in HostModule's public API, tests, or
     |                changelog ever mentioned existed.
```

The second timing note is about ordering under concurrency, which is a
second, sharper danger this smell introduces once the shared state is
mutable and both sides can write it. Because there is no PublicContract
mediating access, there is also no single place to put a lock, a version
check, or an invariant assertion. Each side independently assumes it is
the only writer, and a race between HostModule's internal update and
IntrudingModule's direct mutation corrupts state that neither side's own
tests, run in isolation, will ever exercise together.

## 8. Implementation variants

**Field-level intrusion.** The plainest form. A public or protected field on
HostModule that IntrudingModule reads or writes directly, with no accessor
method in between. Cheapest to introduce, cheapest to fix, because the field
can usually be made private and replaced by a narrow accessor without touching
call sites elsewhere.

**Package-private or `internal` escape.** A member marked with a
same-package or same-assembly visibility, intended for HostModule's own
sibling types, that IntrudingModule reaches by being placed in the same
package or assembly purely to gain that access, rather than because it
belongs there logically. This is the smell wearing the language's own
visibility system as camouflage, and it is common in large monorepos where
adding a file to an existing package is one line of an import path rather than
a design decision.

**Declared friendship, abused.** C++ `friend`, a Java module's qualified
`exports ... to`, and C#'s `InternalsVisibleTo` are all legitimate,
intentional mechanisms, see dimension 9. They become this smell's variant, not
its cure, the moment the friend list grows past the one or two consumers that
originally justified it, or the moment nobody can explain why a given entry is
still on the list. A friend declaration is meant to be a small, reviewed,
occasionally revisited exception. Left unreviewed for years, it becomes an
unbounded back door with a respectable-looking name.

**Shared mutable object, jointly owned.** Neither HostModule nor
IntrudingModule privately holds the state, both hold a reference to the same
object and both mutate it. This variant is the hardest to see in a code review
of either module alone, because neither diff, viewed in isolation, looks
suspicious. It only becomes visible when both modules are read together, or
when the shared object's invariants start silently breaking under
concurrent writes from two directions.

**Reflection or dynamic escape.** In a language that supports it, code that
uses reflection, a dynamic attribute lookup, or an unsafe pointer cast to
reach a private member that the type system would otherwise refuse to expose.
This is the most severe variant, because it defeats the compiler's own
enforcement of the boundary rather than merely exploiting a visibility
modifier that was set too loosely, and it usually shows up in serialization
libraries, test frameworks, and dependency-injection containers, where it is a
deliberate, contained trade-off rather than the accidental smell, provided its
blast radius is genuinely limited to that one library's own internals.

**Test-only intimacy.** Covered as an explicit non-applicability case in
dimension 4, but worth naming again here as an implementation variant of the
same underlying mechanism, used for a sanctioned purpose. A test module
reaching into production internals through the identical channels listed
above is the same shape of code, and the distinguishing fact is the
consumer's role, not the mechanism.

## 9. Known production uses

**The Java Platform Module System, qualified `exports ... to`.** Since Java 9,
a module descriptor can export a package to every other module without
restriction, or restrict that export to a named list of consumer modules with
the `to` clause. The Java Language Specification states plainly that for a
qualified export, the public and protected types in the package "are
accessible solely to code in the modules specified in the `to` clause," and
that those named modules "are referred to as friends of the current module."
This is the platform's own recognition that the general case of unrestricted
public access is not always right, and that a bounded, explicit,
compiler-enforced friend list is the correct way to grant privileged access
without opening the door to everyone. Oracle, *The Java Language Specification,
Java SE 21 Edition*, section 7.7, "Module Directives",
https://docs.oracle.com/javase/specs/jls/se21/html/jls-7.html#jls-7.7, verified
2026-08-02.

**The .NET Common Language Runtime, `InternalsVisibleToAttribute`.** An
assembly can mark itself as visible to one or more named friend assemblies
using this attribute, granting them access to types and members that carry
`internal`, `protected internal`, or `private protected` accessibility, while
leaving genuinely `private` members untouched. Microsoft's own documentation
describes the attribute as making types "ordinarily visible only within the
current assembly" visible "to a specified assembly, which is known as a friend
assembly," and the pattern's overwhelmingly common real use is granting a
unit-test assembly access to a production assembly's internals, which is the
sanctioned test-intimacy case from dimension 4 given first-class platform
support. Microsoft, ".NET API documentation,
`System.Runtime.CompilerServices.InternalsVisibleToAttribute`",
https://learn.microsoft.com/en-us/dotnet/api/system.runtime.compilerservices.internalsvisibletoattribute,
verified 2026-08-02.

**C++, the `friend` declaration.** A C++ class can name another class or
function as a friend, granting it access to the declaring class's private and
protected members. The mechanism exists precisely to let a small number of
tightly related types, most commonly a container and its own iterator, or an
operator-overload function that needs both operands' internals, cooperate
without widening the class's public interface for everyone else. Wikipedia's
summary states that a friend class "can access the private and protected
members of the class in which it is declared as a friend," used to let a data
structure's own component classes reach its internals "while preserving
encapsulation" from the perspective of external users, https://en.wikipedia.org/wiki/Friend_class,
verified 2026-08-02, used only to confirm the mechanism's wording, not as a
source of the pattern's analysis. C++ programmers who reach for `friend` on
every unrelated class that finds it convenient, rather than on the one or two
genuinely coupled collaborators the language feature was built for, reproduce
this smell inside the very mechanism meant to prevent it.

**ArchUnit, architecture rules that detect exactly this shape.** ArchUnit is a
Java library that lets a team assert architectural rules as executable tests,
and two of its core rule families exist specifically to catch the structure
this entry describes at build time rather than discovering it during an
incident. `slices().matching(...).should().beFreeOfCycles()` fails a build
when two packages depend on each other in both directions, which is the
bidirectional shape a private back channel produces, and
`classes().that().resideInAPackage(...).should().onlyBeAccessed().byAnyPackage(...)`
lets a team declare, and continuously enforce, exactly which packages are
allowed to reach into a given package's internals, turning an undeclared
back channel into either a compiler-adjacent failure or a deliberate, named,
reviewed exception. ArchUnit User Guide, sections on slice rules and package
access rules, https://www.archunit.org/userguide/html/000_Index.html, verified
2026-08-02.

## 10. Consequences

Positive, when the intimacy is the sanctioned, bounded kind from dimension 4.

- A small, well-audited exception to normal encapsulation can be faster to
  write and easier to understand locally than routing a genuinely tight
  collaboration through a full public interface that exists for exactly one
  consumer.
- Test code gains fast, precise access to internal state for assertions,
  without forcing production code to expose that state to every other caller
  purely to make it testable.
- A deliberate friend declaration is at least visible in the source and, in
  languages that support it, checked by the compiler, which is strictly better
  than the same coupling existing informally with no enforcement at all.

Negative, which is the overwhelming majority of real occurrences.

- Encapsulation stops meaning anything for the affected module, because its
  internal representation is now part of its effective, if undocumented,
  contract, and cannot be changed without a manual audit of every intruding
  caller.
- Changes ripple unpredictably. A refactor that should be entirely local to
  one module now has an invisible blast radius extending into whichever
  modules quietly depend on its internals, which is Shotgun Surgery experienced
  by the module that never asked to be depended on this way.
- Testing the two modules independently becomes unreliable, because their real
  behaviour depends on a shared, undocumented channel that a unit test written
  against either module's public interface alone will not exercise.
- Team ownership boundaries erode. Two teams that believe they own separate
  modules with a clean API between them discover, usually during an incident,
  that they actually share a mutable dependency neither team's process
  accounts for.
- The fix, once the intimacy has accumulated over years rather than being
  caught early, is expensive precisely because nothing documents the full
  extent of the back channel, so removing it safely requires first
  rediscovering everything it was quietly doing.

## 11. Failure modes and misuse

**The renamed-field incident.** Symptom. A production module renames or
reshapes an internal field as part of an unrelated refactor, its own test
suite is green, and a completely different, seemingly unrelated feature breaks
in production hours later. Cause. A second module was reading that field
directly, through a public accessor that was never meant to be load-bearing, or
through reflection. Fix. Grep the codebase for every external reference to the
field before beginning the refactor, not after, and if any exist, replace them
with a call through a proper accessor first, as a separate, tested step.

**The friend list nobody can explain.** Symptom. A `friend` class, a
qualified module export, or an `InternalsVisibleTo` attribute names a
consumer that, when someone asks in a team channel, nobody currently on the
team recognises or can justify. Cause. The declaration was added for a
now-obsolete reason, an experiment that never shipped, a consumer that was
since deleted, or a migration that finished years ago and never had its
scaffolding removed. Fix. Treat every friend declaration as a piece of debt
with an owner and a reason, recorded in a comment or a linked ticket at the
point of declaration, and review the list on a schedule the same way a
dependency audit reviews package versions.

**Two modules that cannot be deployed independently.** Symptom. A team
attempts to ship module A's change without also shipping module B's matching
change, and the system misbehaves in production even though both modules
individually pass their own test suites and their published API contract did
not change. Cause. The two modules share mutable state or private
representation that only happens to stay consistent when both are deployed
from the same commit, which is an unstated coupling invariant nobody wrote
down. Fix. Make the shared state's ownership explicit, assign it to exactly
one of the two modules, and have the other module access it only through that
owner's public interface, so the two can genuinely be versioned and deployed
apart.

**The test suite that only passes in one specific order.** Symptom. A test for
module B fails only when it runs after a particular test for module A, and
passes in isolation or under a different run order. Cause. The two tests, or
the code paths they exercise, share mutable internal state through a back
channel, so one test's side effect leaks into the other's assumed starting
condition. Fix. Treat this the same as any shared-mutable-state bug, isolate
or reset the shared state between tests, and, in the production code the tests
are exercising, remove the underlying back channel so the leak cannot recur
outside the test suite either.

**Reflection used to route around a `private` keyword the author left in
place on purpose.** Symptom. A member is genuinely, deliberately private, and a
separate, unrelated module reaches it anyway through reflection, a dynamic
proxy, or an unsafe cast, usually to work around a missing feature rather than
to solve a genuine architectural need. Cause. It was faster, in the moment, to
defeat the type system than to ask for or build the public extension point
that was actually needed. Fix. Treat the reflective access as a signal that a
real feature request is missing from the target module's public interface,
and add that feature properly, then delete the reflective workaround.

## 12. Trade-off matrix

Compared against the named refactorings and mechanisms that address the same
underlying pressure, across the forces from dimension 3.

| Force | Insider Trading, left as is | Hide Delegate | Move Method / Move Field | Extract Class (redraw the boundary) | Declared friendship (friend, InternalsVisibleTo, qualified exports) |
|---|---|---|---|---|---|
| Encapsulation | Broken, undocumented | Restored on the delegating side | Restored, ownership reassigned to the correct owner | Restored, with a newly explicit seam | Bounded and explicit, not restored to zero |
| Effort to apply | None, that is the problem | Low, a wrapper method per exposed call | Medium, needs every call site updated | High, a new type plus every reference moved | Low, one declaration, but needs ongoing review |
| Fits the case where | Never, by definition | The intruder chains through a middleman to reach the real target | A member's behaviour clearly belongs on the other side already | Neither current module is the right owner of the shared concern | The intimacy is genuinely small, permanent, and justified, most often for tests |
| Risk if applied wrong | N/A, it is the baseline risk | Can produce Middle Man if overused, see that entry | Breaks callers if the field or method is still genuinely needed at the old location | Can produce Feature Envy in reverse if the new class does not own enough behaviour to justify existing | Friend list grows unaudited and becomes this smell again in a different disguise |
| Compile-time enforcement | None | None beyond normal visibility rules | None beyond normal visibility rules | None beyond normal visibility rules | Strong, in languages with module or assembly-level friend systems |
| Best documented by | Nothing, that is the failure | The new delegating method's own signature | The moved member's new location and its call sites | The new class's name and responsibility | The declaration itself, plus a comment stating why |

## 13. Related and incompatible patterns

- **Inappropriate Intimacy.** The direct historical predecessor and, in the
  literature written before 2018, frequently the same concept under a
  different name, see dimension 1. This repository keeps the two as separate
  entries because the vocabulary in real use has not converged, and because a
  useful distinction can be drawn in practice. Inappropriate Intimacy, as most
  writers who still use that 1999 name apply it, tends to describe two
  CLASSES, often a subclass reaching into a superclass's implementation
  details or two sibling classes that grew too familiar. Insider Trading, as
  used here following the 2018 wording, generalises the same failure up to two
  MODULES, packages, services, or teams, where the stakes of an undocumented
  private channel are higher because the two sides are less likely to be
  edited by the same person on the same day. A codebase can have both. A pair
  of classes inside one module can be inappropriately intimate with each other
  entirely locally, while that same module is simultaneously engaged in
  insider trading with a sibling module across a package boundary.
- **Feature Envy.** A near neighbour, distinguished by what is being reached
  for. Feature Envy is a method that calls another module's PUBLIC methods so
  much that it seems to belong there instead. Insider Trading is reaching past
  the public methods into what was meant to stay private. A method with severe
  Feature Envy is a candidate for Move Method. A method engaged in Insider
  Trading needs the back channel closed first, and only then does it make
  sense to ask whether it also has Feature Envy through the newly proper
  public interface.
- **Shotgun Surgery.** Usually the downstream symptom, not the smell itself.
  Because a private back channel is undocumented, a single conceptual change
  to the shared state often has to be made in several places that nothing
  connects on paper, which is precisely Shotgun Surgery's definition.
  Refactoring away Insider Trading, by consolidating the shared state's
  ownership into one place, is frequently the direct fix for a Shotgun Surgery
  problem discovered at the boundary between two modules.
- **Divergent Change.** The opposite failure mode of the same underlying
  design problem. Where Shotgun Surgery is one change scattered across many
  places, Divergent Change is many unrelated reasons to change concentrated
  into one place. A HostModule riddled with back channels from several
  unrelated IntrudingModules often exhibits Divergent Change too, because it
  has become the de facto shared kernel for concerns that do not belong
  together.
- **Message Chains and Middle Man.** Genuinely opposite pressures on the same
  axis. Message Chains happens when code reaches too FAR through a series of
  public accessors to get what it needs, tunnelling through several objects'
  public interfaces. Insider Trading happens when code reaches too DEEP,
  skipping the public interface entirely for one object. Hide Delegate, the
  standard fix for a Message Chain, if applied carelessly by adding a
  pass-through method for every field a caller currently reaches directly, can
  turn Insider Trading into Middle Man instead of into a genuinely better
  design, because a thin delegating wrapper around a leaked field is not the
  same as a properly owned public operation that does real work.
- **Composite, Iterator, and other patterns that use a legitimate, narrow
  friendship by design.** These GoF structural patterns routinely rely on a
  parent-child or container-iterator pair that knows more about each other
  than the outside world is allowed to know, and languages provide `friend`,
  package-private, or nested-class mechanisms precisely to support this
  without opening the relationship to everyone. This is the sanctioned case
  from dimension 4, and it is incompatible with treating every instance of
  privileged cross-type access as automatically this smell.
- **Shared Kernel, from Domain-Driven Design's context-mapping vocabulary.**
  A deliberate, bounded, jointly governed piece of shared model between two
  teams' bounded contexts is the large-scale, intentional version of exactly
  the relationship this smell describes accidentally. The distinguishing
  feature is governance. A Shared Kernel has an agreed change process both
  teams honour. Insider Trading has no such process, only an accident of
  access that happened to compile.

## 14. Refactoring path in and out

Removing an existing case of Insider Trading, ordered from cheapest and safest
to most involved, matching the escalating implementation variants in
dimension 8.

1. Inventory the channel before touching anything. Find every field, method,
   or shared object that crosses the boundary between the two modules outside
   their stated public interface, using the compiler's own visibility errors
   as a forcing function where possible, by temporarily tightening access and
   seeing what fails to build.
2. For a simple field-level intrusion, apply Encapsulate Field to make the
   field private and add a narrow, purposeful accessor. This alone often
   surfaces the real shape of what was actually needed, which is frequently
   much smaller than the full field it replaces.
3. For a call chasing through a middleman object to reach a target's internal
   state, apply Hide Delegate, but stop and ask whether the newly hidden
   method represents a real operation on HostModule that does genuine work, or
   whether it is a naked pass-through that will read as a Middle Man to the
   next reviewer. If it is a naked pass-through, prefer step 4 instead.
4. Where a real behaviour, not only data, is what the intruding side actually
   needed, apply Move Method or Move Field to relocate the responsibility to
   whichever side legitimately owns it, guided by the question of which
   module's reason to change should govern this piece of state.
5. Where neither existing module is the right owner, and the shared concern
   is real and durable rather than an accident, apply Extract Class to draw a
   third, explicit boundary around the shared concern, with its own tests and
   its own public interface, turning an accidental Shared Kernel into a
   deliberate one.
6. Only after the interface is clean, if a genuinely small, permanent,
   justified exception remains, most commonly for a test assembly needing
   direct access to internals, replace the ad hoc back channel with the
   language's own declared-friendship mechanism from dimension 9, scoped as
   narrowly as the mechanism allows, and record why in a comment next to the
   declaration.
7. Add the boundary test from dimension 15 so a future reintroduction of a
   private channel fails a build rather than waiting to be discovered in
   production.

Introducing a deliberate, sanctioned intimacy is the rarer but legitimate
direction, and the path in is short precisely because it should stay small.

1. Confirm the case matches one of the non-applicability entries in dimension
   4, most commonly a test needing internal access, or a genuinely tight pair
   such as a container and its iterator.
2. Reach for the narrowest mechanism the language offers, a single named
   friend, a qualified export naming exactly one module, or an attribute
   naming exactly one assembly, never a blanket relaxation of visibility for
   an entire package.
3. Record the reason next to the declaration, in a comment or a linked
   ticket, so a future reviewer running the audit in step 6 above does not
   have to reverse-engineer the intent.
4. Add it to whatever periodic review process the team already runs for
   dependencies or access grants, so it does not silently outlive its reason.

## 15. Testing and verification

Made harder by the smell's presence.

- Unit tests written against either module's public interface alone pass
  while the real, integrated system fails, because the actual behaviour
  depends on the undocumented back channel that the tests never exercise
  together.
- Mocking or stubbing one side of the relationship for a test of the other
  side is unreliable, because a mock built against the public interface will
  not reproduce whatever the real object's private state was doing, and the
  test can pass against the mock while the production pairing is broken.
- Determining the full blast radius of a proposed change requires reading
  both modules together rather than reasoning about either one from its own
  interface and its own tests, which defeats the entire point of having
  separate, independently testable modules.

Techniques that apply, once the smell is identified.

- **A boundary test, expressed as an architecture rule.** Tools built for
  exactly this, such as ArchUnit for the JVM, NetArchTest for .NET, or a
  hand-written static check walking import graphs in any language, let a
  team assert "package A may only be accessed by packages B and C" and fail
  the build the moment a new, undeclared access appears, turning the smell
  from something discovered in production into something caught in code
  review before merge, see the dimension 9 citation.
- **Integration tests scoped exactly to the suspected boundary.** Rather than
  a broad, whole-system test, write a small test that exercises both HostModule
  and IntrudingModule together, deliberately, so the private channel's
  behaviour is asserted on directly instead of accidentally, while the
  refactor in dimension 14 is in progress.
- **A characterisation test taken before refactoring begins.** Capture the
  current, possibly accidental, combined behaviour of the two modules working
  together as a golden-master test before starting to remove the back
  channel, so an unintended behaviour change during the refactor is caught
  immediately rather than discovered later as a regression.
- **Mutation testing scoped to the shared state.** Deliberately corrupting the
  value the back channel carries and confirming that at least one test fails
  is a strong signal that the dependency is real and load-bearing, which
  matters when deciding whether a suspected channel from step 1 of dimension
  14 is safe to simply delete or needs to be preserved through a proper
  interface.

## 16. Observability signals

This smell is structural and is usually invisible at runtime until it fails,
so the useful signals are mostly static and organisational rather than
metrics collected from a running system, with one exception around shared
mutable state under concurrency.

What to record or watch for.

- A dependency-direction check run in CI, reporting the count of
  cross-boundary references that touch non-public members, trending over
  time. A healthy trend is flat or falling. A rising count is the smell
  actively accumulating.
- The size of any declared friend list, `InternalsVisibleTo` list, or
  qualified export's `to` clause, tracked the same way a team tracks its
  dependency count, since an unbounded, growing friend list is this smell
  wearing a legitimate-looking disguise.
- For genuinely shared mutable state accessed from more than one module, a
  counter or trace span recording which module last wrote a given piece of
  shared state, which turns an otherwise invisible race between two writers
  into something a dashboard can surface before it produces a customer-facing
  bug.
- Code review comment patterns. A repeated reviewer question of "why does
  this module need to reach into that one's internals" across several
  unrelated pull requests is a strong human signal that a static check from
  dimension 15 should be added to catch the pattern automatically instead of
  relying on a reviewer noticing it by hand every time.

A healthy state on a dashboard. The cross-boundary private-access count is
zero or a small, explained, stable number matching the declared friend list.
Deploys of either module can happen independently without a corresponding
deploy of the other. Code review rarely asks the "why does this reach into
that" question, because the architecture rule from dimension 15 already
prevents the case from reaching review.

A failing state. The private-access count climbs after a module split or a
team reorganisation. A friend list grows without a corresponding removal
elsewhere. Incidents trace back to "module A changed something internal and
module B broke," repeated across more than one postmortem, which is the
clearest signal that this specific smell, rather than a one-off bug, is the
recurring root cause worth fixing at the structural level rather than patching each time
it resurfaces.

## 17. Security and privacy implications

This smell has a real and direct security dimension, because it is, by
definition, a channel that bypasses the boundary a module's author put in
place on purpose, and that boundary is often the same boundary a security
review relies on when reasoning about what data a given piece of code can
reach.

**Privilege boundary erosion.** A module's public interface is frequently the
place where input validation, authorisation checks, or data redaction
actually live. A back channel that reaches past that interface into raw
internal state can also reach past whatever checks were attached to the
public methods, which means Insider Trading between a security-sensitive
module and a less trusted one can silently become a privilege-escalation
path, not merely a maintainability problem. This is engineering judgement
drawn from the general principle that access control is only as strong as its
narrowest enforced boundary, applied to this specific structural smell.

**Sensitive data exposure through an undeclared friend.** Where the shared
private state includes personal data, credentials, or any other sensitive
field, an undocumented back channel means that data now flows to a second
module that a data-flow audit, a privacy impact assessment, or a compliance
review is unlikely to discover, because such reviews usually trace declared
interfaces and declared dependencies, not accidental field access. The
architecture-rule tooling described in dimension 15, run continuously, is a
practical mitigation, because it turns an invisible channel into a visible,
auditable one, which is a genuine and common use of that tooling in regulated
codebases.

**Reflection-based intrusion as an actual attack surface, not only a code
smell.** When the mechanism in play is reflection or a dynamic escape hatch
rather than a mere visibility-modifier laxity, the same technique that lets
one internal module reach another's private state is, in a language runtime
that allows it broadly, also available to genuinely untrusted code loaded
into the same process, such as a plugin or a dependency pulled from a public
package registry. A codebase that has normalised reaching past `private`
with reflection for its own internal convenience has, as a side effect, made
it harder to argue that a sandboxing or plugin-isolation boundary elsewhere
in the same system is actually enforced, since the runtime demonstrably
permits exactly that kind of boundary-crossing already.

On plain data privacy in the narrower sense, the pattern is silent beyond the
sensitive-data-exposure point above. It does not itself introduce a specific
compliance obligation, and this entry does not claim one.

## Code examples

Three languages chosen for three genuinely idiomatic angles. TypeScript shows
the smell in its plainest field-level form and the Hide Delegate style fix.
Python shows the same failure using its convention-based privacy, plus the
encapsulation fix that convention alone cannot enforce. Go is included
specifically because its package-level `internal/` directory convention is a
language-level, compiler-enforced answer to exactly this smell, shown as the
production-grade fix rather than as a smell demonstration. Java is omitted
from the code samples because its production-use citation in dimension 9
(module `exports ... to`) already demonstrates the same declared-friendship
idea shown for Go, and repeating the identical mechanism in a second language
would add length without adding a new angle.

### TypeScript, the smell and the fix

```typescript
// The smell. Order reaches straight into Warehouse's private bookkeeping.
class Warehouse {
  stockByItem: Map<string, number> = new Map();

  constructor() {
    this.stockByItem.set("widget", 10);
  }
}

class OrderTheSmelly {
  constructor(private warehouse: Warehouse) {}

  fulfil(item: string, qty: number): boolean {
    const have = this.warehouse.stockByItem.get(item) ?? 0;
    if (have < qty) return false;
    this.warehouse.stockByItem.set(item, have - qty);
    return true;
  }
}

// The fix. Warehouse owns its own invariant, Order calls one public method.
class WarehouseFixed {
  private stockByItem: Map<string, number> = new Map();

  constructor() {
    this.stockByItem.set("widget", 10);
  }

  reserve(item: string, qty: number): boolean {
    const have = this.stockByItem.get(item) ?? 0;
    if (have < qty) return false;
    this.stockByItem.set(item, have - qty);
    return true;
  }
}

class OrderFixed {
  constructor(private warehouse: WarehouseFixed) {}

  fulfil(item: string, qty: number): boolean {
    return this.warehouse.reserve(item, qty);
  }
}

const smelly = new OrderTheSmelly(new Warehouse());
console.log("smelly fulfil:", smelly.fulfil("widget", 3));

const fixed = new OrderFixed(new WarehouseFixed());
console.log("fixed fulfil:", fixed.fulfil("widget", 3));
```

### Python, convention-based privacy defeated, then actually enforced

```python
class Account:
    def __init__(self, balance):
        self._balance = balance  # convention only, not enforced by Python


class Ledger:
    """Reaches past the underscore convention. This is Insider Trading."""

    def transfer(self, source: Account, target: Account, amount: int) -> bool:
        if source._balance < amount:
            return False
        source._balance -= amount
        target._balance += amount
        return True


class AccountFixed:
    def __init__(self, balance):
        self.__balance = balance  # name-mangled, harder to reach by accident

    def withdraw(self, amount: int) -> bool:
        if self.__balance < amount:
            return False
        self.__balance -= amount
        return True

    def deposit(self, amount: int) -> None:
        self.__balance += amount

    @property
    def balance(self) -> int:
        return self.__balance


class LedgerFixed:
    """Calls only the public contract. No back channel remains."""

    def transfer(self, source: AccountFixed, target: AccountFixed, amount: int) -> bool:
        if not source.withdraw(amount):
            return False
        target.deposit(amount)
        return True


if __name__ == "__main__":
    a, b = Account(100), Account(0)
    print("smelly transfer:", Ledger().transfer(a, b, 40), a._balance, b._balance)

    x, y = AccountFixed(100), AccountFixed(0)
    print("fixed transfer:", LedgerFixed().transfer(x, y, 40), x.balance, y.balance)
```

### Go, the language-enforced fix using `internal/`

Go has no smell demonstration here on purpose. Its `internal/` package
convention is a closer-to-a-language-feature answer to this exact problem, so
the sample shows only the fix, structured as one package a caller must go
through and one internal package the compiler itself refuses to let a
different module import.

```go
package main

import "fmt"

// stock is unexported. Outside this file's package, nothing can read or
// write it directly, which is the compiler enforcing dimension 14's fix
// even for code within the same repository that lives in another package.
type warehouse struct {
	stock map[string]int
}

func newWarehouse() *warehouse {
	return &warehouse{stock: map[string]int{"widget": 10}}
}

// Reserve is the one public seam. Everything crosses through here.
func (w *warehouse) Reserve(item string, qty int) bool {
	have := w.stock[item]
	if have < qty {
		return false
	}
	w.stock[item] = have - qty
	return true
}

type order struct {
	wh *warehouse
}

func (o *order) Fulfil(item string, qty int) bool {
	return o.wh.Reserve(item, qty)
}

func main() {
	o := &order{wh: newWarehouse()}
	fmt.Println("fixed fulfil:", o.Fulfil("widget", 3))
}
```

A second Go package placed under a path such as
`myrepo/internal/warehouse/` goes one step further than an unexported field,
because the Go compiler refuses to let ANY package outside `myrepo` import it
at all, not merely outside the same package, which is the closest thing a
mainstream language offers to a compiler-enforced module boundary that makes
this smell impossible to introduce by accident across a repository, rather
than merely inconvenient.

## 18. References

1. Martin Fowler. *Refactoring. Improving the Design of Existing Code*, 2nd
   edition. Addison-Wesley, 2018. ISBN 978-0134757599. Chapter 3, "Insider
   Trading". Source of the current canonical name and the 2018 generalisation
   from classes to modules.
2. Martin Fowler and Kent Beck. *Refactoring. Improving the Design of Existing
   Code*, 1st edition. Addison-Wesley, 1999. ISBN 0-201-48567-2. Chapter 3.
   Source of the original 1999 name, Inappropriate Intimacy, for the same
   underlying pressure at the class level.
3. luzkan.github.io. "Insider Trading". https://luzkan.github.io/smells/insider-trading
   Verified 2026-08-02. Used only to corroborate the historical relationship
   between the 1999 and 2018 names and the class-to-module generalisation
   described in dimension 1, not as a source of this entry's analysis.
4. Oracle. *The Java Language Specification, Java SE 21 Edition*, section 7.7,
   "Module Directives". https://docs.oracle.com/javase/specs/jls/se21/html/jls-7.html#jls-7.7
   Verified 2026-08-02. Source for the qualified module export production use
   in dimension 9.
5. Microsoft. *.NET API documentation*,
   `System.Runtime.CompilerServices.InternalsVisibleToAttribute`.
   https://learn.microsoft.com/en-us/dotnet/api/system.runtime.compilerservices.internalsvisibletoattribute
   Verified 2026-08-02. Source for the .NET friend-assembly production use in
   dimension 9.
6. Wikipedia contributors. "Friend class". https://en.wikipedia.org/wiki/Friend_class
   Verified 2026-08-02. Used only to confirm the wording of the C++ `friend`
   mechanism's definition and purpose, not as a source of this entry's
   analysis.
7. ArchUnit. *ArchUnit User Guide*, sections on slice rules and package access
   rules. https://www.archunit.org/userguide/html/000_Index.html
   Verified 2026-08-02. Source for the architecture-testing production use in
   dimension 9 and the boundary-test technique in dimension 15.
