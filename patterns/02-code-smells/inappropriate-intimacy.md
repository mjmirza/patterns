---
name: Inappropriate Intimacy
slug: inappropriate-intimacy
family: 02-code-smells
category: Coupling
aliases: []
first_described: "Fowler and Beck 1999"
maturity: canonical
related: [feature-envy, data-class, message-chains, move-method, extract-class, hide-delegate]
incompatible_with: []
verified: 2026-08-02
---

# Inappropriate Intimacy

## 1. Name, aliases, and lineage

The canonical name is Inappropriate Intimacy. It is one of the original smells
catalogued in Martin Fowler, *Refactoring. Improving the Design of Existing
Code*, 1st edition, Addison-Wesley, 1999, in the chapter "Bad Smells in Code."
That chapter's smell catalog carries a co-author who is not the book's named
author. Fowler states plainly on his own site that "the term was first coined
by Kent Beck while helping me with my Refactoring book"
(https://martinfowler.com/bliki/CodeSmell.html, verified 2026-08-02), and this
entry follows the sibling entry for Feature Envy in this family in crediting
Beck alongside Fowler for the smell catalog itself, not only the umbrella term
"code smell." The 2nd edition (Addison-Wesley, 2018, confirmed against the
Internet Archive catalog record for ISBN 9780134757599,
https://archive.org/details/refactoringimpro0000fowl, verified 2026-08-02)
restructures the book around the refactoring catalog rather than a standalone
smells chapter, but Move Method, Move Field, Extract Class, and Hide Delegate,
the refactorings this entry names throughout, all survive into the current
catalog under those or closely related names
(https://refactoring.com/catalog/, verified 2026-08-02).

This repository found no rival name for the smell in serious use. What exists
instead is a set of narrower, differently scoped ideas that people sometimes
reach for when they do not know the Fowler and Beck name, and confusing any
of them with this entry produces a misdiagnosis.

- A design-smell catalog can flag the shape from one direction only, as an
  over-exposed class rather than a mutual entanglement. DesigniteJava, a
  maintained open source design-smell detector for Java and C#, detects
  "Deficient Encapsulation" among its seventeen design smells
  (https://github.com/tushartushar/DesigniteJava, verified 2026-08-02). That
  smell names a class that hands out more access to its own internals than it
  should. It is a real and useful signal, and a class suffering from it is
  often one half of an Inappropriate Intimacy pair, but the two names are not
  interchangeable. Deficient Encapsulation can be true of a class that nobody
  else has ever actually reached into yet. Inappropriate Intimacy requires
  that the reaching has already happened, usually from a specific named
  neighbor, usually in both directions.
- A static analysis tool can operationalize the underlying pressure as a
  count rather than a named smell. PMD ships a `CouplingBetweenObjects` rule
  and a `LawOfDemeter` rule in its Java design rule set
  (https://docs.pmd-code.org/latest/pmd_rules_java_design.html, verified
  2026-08-02), covered in full in dimension 9. Neither rule is titled
  Inappropriate Intimacy. Both are proxies for it, catching a symptom a
  threshold can count rather than the judgment a human makes about whether
  two specific classes have grown too familiar with each other's insides.
- Feature Envy, this family's closest sibling, is frequently mistaken for
  this smell and frequently precedes it. The distinction is scale and
  direction, and it is worth stating here rather than only in dimension 13.
  Feature Envy is a single method on one class reaching for the data of one
  other class. Inappropriate Intimacy is what that same reaching becomes once
  it happens from several methods, on both sides, against private state
  rather than public accessors. A single instance of Feature Envy is not yet
  this smell. A codebase that has accumulated many instances of Feature Envy
  between the same two classes, in both directions, usually has.

## 2. Problem and context

Two classes end up knowing far more about each other's insides than either
one's public contract admits to. One reaches into the other's private fields
directly, or calls a method on it that was written to be called by exactly
one caller and exposes an implementation detail rather than offering a real
capability. The other side does the same thing back. Neither class can be
read, tested, or changed on its own anymore, because "on its own" stopped
being a true description of either one somewhere along the way.

The situation almost never starts this way. It accretes. A method on class A
needs one piece of data class B happens to hold. The clean move is to add a
method to B that hands over exactly what A needs, computed or fetched by B,
on B's own terms. The cheap move, available because the language lets a
field's visibility be loosened by one keyword, is to widen the field and
read it directly from A. Six months later, a second, unrelated feature on a
third file reaches for that same widened field, and now nobody remembers
whether the field is genuinely part of B's contract or an accident that
happened to compile. Later still, B needs something back from A to finish
its own job, under the exact same time pressure, and the shortcut runs in
reverse. What began as one convenient shortcut in one direction becomes a
pair of classes that cannot be separated without a coordinated, careful
rewrite of both files at once.

The context in which a reader should recognize this is concrete and
observable, not aesthetic. Changing a field's type, a collection's shape, or
a private helper's internal logic in class B forces a matching, same-commit
edit in class A, and this has happened more than once. A code reviewer
regularly finds themselves reading two files side by side to understand a
change that was supposed to touch one responsibility. A new engineer is told,
informally, "you can't really touch `Order` without also touching
`Customer`," and everyone nods, because it has stopped being surprising.
Encapsulation exists specifically to make that sentence false. a well drawn
class boundary is supposed to let its internal representation change without
rippling to a named neighbor. When it does ripple, on a specific, recurring,
two-file basis, the smell has a name, and the name is this one.

## 3. Forces

- **Coupling versus the convenience of the next line.** A direct field read
  is one keyword and zero new methods. A proper accessor is a few more lines
  today in exchange for the ability to change the internal representation
  later without touching the caller. The smell is what accumulates when the
  cheaper option wins repeatedly, on both sides of a relationship, without
  anyone deciding that on purpose.
- **Change amplification.** A single conceptual change to the domain, for
  example letting a reservation span more than one room, should touch the
  class that owns that concept and stop. Intimacy turns a one-file change
  into a two-file change every time, because neither file has a seam that
  absorbs the other's internal shift.
- **Testability.** A class whose invariant can be bypassed by a neighbor
  writing directly to its field is not actually enforcing that invariant. It
  only looks enforced in the narrow paths the neighbor's tests happen to
  exercise. Isolating either class for a genuine unit test, one that does not
  also construct and wire up the other, becomes difficult or impossible.
- **Team topology and review cost.** Two classes this intimate are one unit
  of change wearing two file names. If two different engineers, or two
  different teams, own the files nominally, every edit to either one needs
  the other engineer's attention regardless of what the ownership chart
  claims, which is a coordination tax nobody budgeted for.
- **A weak, frequently overstated counter-force.** Direct field access can be
  marginally cheaper at runtime than a method call in a language or a hot
  path where the call resists inlining. In the overwhelming majority of
  application code this saving is immeasurable next to allocation, I/O, and
  serialization costs, and using it to justify skipping an accessor is a
  false economy this entry explicitly rejects as a serious force.

The pattern this entry describes exists because the cheap force usually wins
locally, one shortcut at a time, while the expensive force only shows up
later, spread across many files and many commits, where it is much harder to
trace back to its origin.

## 4. Applicability and non-applicability

The label applies when the reaching is real, has already happened, and runs
in more than one place.

- Two classes read from, and write to, each other's private fields or
  collections directly, from outside any method the owning class defines for
  that purpose, and this happens from both sides.
- A change to one class's internal representation has repeatedly forced a
  same-commit edit to a specific named collaborator, not a generic ripple
  across the whole codebase.
- A bidirectional association exists where each side both reads and mutates
  the other's internal collection directly, rather than holding the
  reference purely for identity or navigation.
- One class exposes a method or a field at wider visibility than its actual
  contract needs, solely so that one specific other class can reach it, an
  informal, undocumented friend relationship with none of the explicitness a
  real friend declaration would carry.
- A subclass depends on a superclass's private implementation detail beyond
  what the protected contract promises, for example the exact iteration
  order of a private collection the superclass never documented, so that
  intimacy crosses an inheritance boundary rather than sitting between two
  independent peers.

Do NOT reach for this diagnosis in the following cases, and the reason
matters as much as the rule, because a mistaken diagnosis here sends a
refactor after code that was never broken.

- **A bidirectional association maintained entirely through paired accessor
  methods.** A tree node's `addChild` and `setParent`, called together by
  one method so the two sides can never disagree, is a correctly
  encapsulated two-way relationship, not this smell. The smell is about
  reaching past the accessor into the field, never about the mere existence
  of a reference pointing back.
- **The Memento pattern's deliberate privileged access.** The GoF Memento
  gives the originator that created a memento privileged access to its
  internal state while hiding that state from every other caller (Erich
  Gamma, Richard Helm, Ralph Johnson, John Vlissides, *Design Patterns.
  Elements of Reusable Object-Oriented Software*, Addison-Wesley, 1994,
  chapter 5, Behavioral Patterns, Memento). This looks like intimacy from a
  distance. It is a narrow, single-purpose, documented exception that the
  pattern itself exists to bound, the opposite of the accidental,
  undocumented accretion this entry describes.
- **A value object deliberately split across two small, immutable
  companions.** A `Money` type and a `Currency` type that never independently
  vary and never mutate each other are coupled by domain necessity, with no
  reach past a documented boundary and no mutation crossing it. Knowledge of
  another type's shape is not the smell. Mutation across the boundary, or
  reach past what the public contract promises, is.
- **Frequent collaboration through well-defined public methods, however
  chatty it looks.** Two classes calling each other's real, documented
  capabilities often, even many times per request, is ordinary coupling. It
  becomes a different smell, closer to Message Chains, when the calls form a
  long walk through several objects' accessors, but it never becomes
  Inappropriate Intimacy unless something on the far end is being reached
  into rather than asked of.
- **A deliberately scoped construction helper.** A `Builder` nested inside
  the class it builds, given access to that class's private constructor for
  exactly that purpose, is a bounded, single-direction, well-understood
  visibility decision. It is not this smell, because the access is narrow,
  documented by the nesting itself, and never reciprocated.
- **Test code reaching into production internals to assert on state.** A
  test using reflection, a package-private accessor, or a framework's
  visible-for-testing annotation to check a private field is a testing-scope
  trade-off, weighed against test fragility in dimension 15. It is a
  different engineering decision than a production collaborator reaching
  into the same field to compute a result, and treating the two the same
  misdiagnoses working test infrastructure as a design defect.

## 5. Structure

This is a code smell, not a construct someone deliberately builds, so this
dimension describes the shape a reader recognizes rather than participants
chosen at design time. Two classes, called Host and Guest here purely to
have names for the description, since the relationship is frequently
symmetric rather than one-directional.

- **Host.** Holds a reference to Guest, either as a field or received
  repeatedly as a parameter across several of its own methods. At least one
  of those methods reads or writes Guest's private state directly rather
  than calling a method Guest defines for that purpose.
- **Guest.** Symmetrically, in the fully developed form of the smell, holds a
  reference back to Host and does the same thing in reverse from at least
  one of its own methods.
- **The missing seam.** What should exist and does not is a small set of
  named, intention-revealing methods that would let Host and Guest
  collaborate without either one knowing the other's representation. Its
  absence is the structural fact this entry is about. every other symptom
  described in this entry follows from that one missing seam.

The recognizable structural signature, useful when scanning an unfamiliar
codebase, is this. Renaming or changing the type of a field on Guest breaks
compilation, or breaks a test, at more than one call site inside Host's file,
spread across more than one of Host's methods, and the reverse is also true
for a field on Host reached into from Guest's file. A single broken call site
is more often Feature Envy or an ordinary accessor use. Several broken call
sites on both sides is this smell.

## 6. ASCII structure diagram

```
  +-----------------------------+        +-----------------------------+
  |            Order            |        |           Customer          |
  |------------------------------------  |------------------------------
  | - items: List<Item>         |        | - orders: List<Order>       |
  | + redeem(customer, n)       |------->| - loyalty: LoyaltyAccount   |
  |     customer.loyalty.points |  reads |     (points: int)           |
  |     -= n   (direct write,   |  and   +-----------------------------+
  |      bypasses Customer)     |  writes            ^
  +-----------------------------+  fields             |
              ^                    directly            |
              |                                        |
              +---- customer.totalSpend() walks -------+
                    order.items directly too, in
                    the other direction, instead of
                    calling a method Order exposes.

  Neither class calls a capability the other publishes for this
  purpose. Both classes reach straight past the boundary into
  state the other one is supposed to own alone.
```

## 7. Dynamics

The runtime signature is a mutation, or a computation, that crosses a class
boundary through a field reference rather than a method call, so the class
whose invariant is at stake never gets the chance to check it. The sequence
below is drawn from the code examples at the end of this entry.

```
  Client          Order               Customer          LoyaltyAccount
    |               |                    |                    |
    |-- redeem(c,999) ->|                |                    |
    |               |--- c.loyalty.points -= 999 ------------>|
    |               |    (direct field write, no check,       |
    |               |     LoyaltyAccount never consulted)      |
    |               |                    |                    |
    |               |           points is now -989, an
    |               |           invariant nobody enforced
    |               |           has been silently broken

  After the fix, the same request is refused at a single choke
  point that exists specifically because it is now the only path.

  Client          Order               Customer          LoyaltyAccount
    |               |                    |                    |
    |-- redeemLoyalty(c,999) ->|         |                    |
    |               |--- c.redeemPoints(999) ---------------->|
    |               |                    |-- loyalty.redeem(999) ->|
    |               |                    |                    |-- 999 > 10,
    |               |                    |                    |   refuses
    |               |                    |<-- exception -------|
    |               |<---- exception propagates, points stay 10 -|
```

The property worth naming plainly. before the fix, the invariant lives
nowhere, because two different call sites can each independently mutate the
same state, and no single one of them is positioned to see the whole
picture. After the fix, the invariant lives in exactly one method, and every
path that wants to change that state must pass through it.

## 8. Implementation variants

The variants here describe the concrete shapes the smell takes in real code,
not implementation choices someone selects, since nobody chooses to write
this smell on purpose.

- **Bidirectional field reaching, the fully developed form.** Both classes
  hold a reference to the other and both mutate the other's fields directly.
  This is the shape the code examples in this entry demonstrate, and it is
  the most damaging variant because there is no single owner for either
  piece of state anymore.
- **Deep unidirectional reaching, a step short of the full smell.** One class
  reaches into another's internals from several of its own methods, while
  the other side never reaches back. This sits between a single instance of
  Feature Envy and full Inappropriate Intimacy. When several methods on one
  class each independently envy the same neighbor's data, the correct
  response shifts from several individual Move Method operations to a
  redesign of the boundary itself, most often Extract Class, because the
  repetition is evidence that a whole responsibility, not just one
  computation, belongs somewhere else.
- **Intimacy across an inheritance boundary.** A subclass depends on a
  superclass's private helper's exact behavior, or on the iteration order of
  a private collection the superclass never promised, discovered because the
  subclass breaks whenever the superclass's author refactors something they
  believed was purely internal. The base class has no visibility into the
  dependency at all, which makes this variant the hardest to detect by
  reading either file in isolation.
- **Informal friend access with no declared friendship.** A method or field
  is given wider visibility than its contract needs, purely so one specific
  other class can call it, sometimes marked with a comment asking other
  callers not to use it. Languages with an explicit friend mechanism at
  least make this decision visible in the source; languages without one hide
  it in a visibility keyword that looks, to every other reader, like an
  ordinary public member.
- **Bidirectional persistence associations.** A parent entity holding a
  collection of children and a child entity holding a back-reference to its
  parent is a genuinely common domain shape in object-relational mapping. The
  smell appears specifically when application code on either side mutates
  the collection or the back-reference directly, from outside a single
  paired method that keeps both sides consistent, rather than when the
  two-way reference exists at all. This entry treats the mapping technology
  itself as neutral. the same two-way reference is fine when only one method
  pair ever writes to it, and is this smell the moment two or more call
  sites write to either side independently.

## 9. Known production uses

**PMD, `CouplingBetweenObjects` and `LawOfDemeter` design rules.** PMD, a
widely deployed open source static analysis tool for Java, ships both rules
in its design rule set. `CouplingBetweenObjects` counts the unique attribute
types, local variable types, and return types referenced by a class and
flags it once that count passes a configurable threshold, default twenty.
`LawOfDemeter` flags an expression that reaches past a configurable trust
radius, default one hop, into an object it was not handed directly. Neither
rule names Inappropriate Intimacy, and both are proxies rather than a direct
detector of it, but both operationalize the same underlying pressure this
entry describes and are run in real continuous integration pipelines across
Java projects everywhere. PMD documentation, "Design rules",
https://docs.pmd-code.org/latest/pmd_rules_java_design.html, verified
2026-08-02.

**JetBrains IntelliJ IDEA, the Extract Delegate refactoring.** IntelliJ IDEA,
a commercial IDE used widely across JVM projects, ships an automated Extract
Delegate refactoring that extracts selected fields and methods of an
overgrown class into a newly created class, with the original class holding
a reference to the new one and delegating to it. JetBrains documents the
motivation as a class that "has grown too large and 'does too many things.'"
Applying it to one half of an intimate pair is a mechanical way to draw the
missing seam described in dimension 5, letting the tool perform the
extraction the dimension 14 refactoring path describes by hand. JetBrains
IntelliJ IDEA Help, "Extract Delegate",
https://www.jetbrains.com/help/idea/extract-delegate.html, verified
2026-08-02.

**The Chidamber and Kemerer coupling metrics, as an industry standard.**
Shyam Chidamber and Chris Kemerer's Coupling Between Object classes metric,
one of six metrics in their widely cited suite, gave the field a countable
definition of exactly the pressure this smell describes, a class's coupling
to the concrete types it references. S.R. Chidamber and C.F. Kemerer, "A
Metrics Suite for Object Oriented Design," IEEE Transactions on Software
Engineering, vol. 20, no. 6, June 1994, pp. 476 to 493. This entry does not
claim that PMD's rule of the same name was built directly from that paper,
only that both name and count the same underlying quantity, and that the
metric itself is the standard against which coupling thresholds in
commercial and open source tooling are commonly set.

## 10. Consequences

Positive, once the smell is recognized and fixed.

- Encapsulation's actual promise, that internal representation can change
  without rippling to a named neighbor, becomes true again for both classes.
- Each class becomes testable against a narrow contract rather than against
  the other class's full concrete shape, discussed further in dimension 15.
- A single conceptual change touches one file, or one newly extracted file,
  instead of two files that were never meant to move together.
- Ownership becomes real. two engineers or two teams can each own one file
  without needing the other's sign-off for every change.

Negative, while the smell stands.

- An invariant that lives in one class's method can be silently bypassed by
  a neighbor writing to the field directly, producing a bug with no single
  location responsible for causing it, the exact failure demonstrated in
  dimension 7.
- Review and merge cost rises, because a reviewer must read two files to
  understand one change, and two engineers editing either file concurrently
  are effectively editing the same unit of change.
- Onboarding cost rises. a new engineer who is told, correctly, that they
  cannot safely touch one class without also touching a named other one has
  been handed an informal rule that only lives in institutional memory.

The remedy itself is not free, and naming its own cost belongs here as
honestly as the smell's cost does. Extract Class adds a type to the
codebase. Hide Delegate adds one layer of indirection at each call site it
touches. Applied to a pair of classes that is small, stable, and genuinely
has stopped changing, the ceremony of a full remedy can cost more than the
mild coupling it removes, a case this entry returns to in dimension 11 as
its own failure mode, over-application.

## 11. Failure modes and misuse

**Invariant bypass through direct mutation.** Symptom. A value that one
class's own method is supposed to guard, for example a balance that must
never go negative, is observed to have gone negative in production or in a
test, even though the guarding method itself was never called with an
invalid argument. Cause. A collaborator wrote to the field directly instead
of calling the guarding method, so the guard was never in the mutation's
path at all. Fix. Move the mutation into a single method on the owning
class, per dimension 14, and make every remaining call site call that method
instead of touching the field.

**Shotgun-style cross file edits.** Symptom. Code review repeatedly asks why
a pull request for one feature touches two specific, seemingly unrelated
files, and the answer is always the same pair of files. Cause. The two files
share a responsibility that was never given its own name or its own class.
Fix. Extract Class, pulling the shared responsibility into a third,
honestly named class both original classes depend on unidirectionally.

**Slow, brittle tests that wire up more than they claim to test.** Symptom.
A test labeled as a unit test for class A constructs class B, sets several
of B's fields through a test-only setter or reflection, and only then
exercises A. The test breaks whenever B's constructor or internal shape
changes, for reasons that have nothing to do with A's actual behavior.
Cause. A's real behavior depends on B's internal representation, not on B's
public contract, so no smaller test double can stand in for B. Fix.
Introduce a narrow interface A genuinely depends on, per dimension 15, and
test A against a hand-written fake that implements only that interface.

**Import cycles in languages that enforce an acyclic module graph.** Symptom.
Adding one new method to class B fails to compile or link because B must now
import A while A already imports B, and no such cycle existed before the two
classes needed to reach into each other. Cause. Direct field access forced
both sides to depend on each other's concrete type rather than an
abstraction either one could depend on alone. Fix. Introduce an interface on
one side and depend on the abstraction, or apply Extract Class so both
original classes depend on the new class instead of on each other.

**A naive merge instead of a real fix.** Symptom. Someone "fixes" the
intimacy by folding both classes into one, and the resulting single class is
larger and violates single responsibility more severely than either original
class did, even though the reaching-into-fields symptom is technically gone
because everything is now one file. Cause. Merging was treated as the only
available remedy, and Extract Class into a properly bounded third class was
skipped. Fix. Split the merged class back out, this time drawing the
boundary around the shared concept that actually justified the original two
classes existing, rather than around the accident of which fields happened
to be reached into.

**Reflection based intimacy that escapes from tests into production.**
Symptom. A helper that reflectively sets a private field, first written for
test setup, is copy-pasted into production code to work around a missing
public method, and ships. Cause. The private field genuinely needed a
narrow, validated public mutator that nobody added, so the path of least
resistance reused a testing hack instead of raising the missing API as a
real gap. Fix. Add the narrow, validated public method the code actually
needed, then delete the reflection call from production entirely.

**Over-application to a stable, genuinely small pair.** Symptom. A codebase
carries several extra classes and delegate layers introduced to fix
Inappropriate Intimacy between two classes that, in hindsight, never
actually changed independently and never will, and the extraction has made
both harder to read for no measurable benefit. Cause. The refactoring path
in dimension 14 was applied mechanically to every flagged instance rather
than weighed against dimension 3's forces for that specific pair. Fix.
Recognize that a small, stable pair of tightly related classes with no
history of independent change is closer to the value-object non-applicability
case in dimension 4 than to the smell this entry targets, and leave it
alone.

## 12. Trade-off matrix

Compared across the remedies most often reached for, against the forces from
dimension 3, alongside the two responses this entry names as failures rather
than remedies.

| Force | Move Method | Extract Class | Hide Delegate | Unidirectional association | Merge into one class | Leave it, add more tests |
|---|---|---|---|---|---|---|
| Reduces two-way field reaching | Yes, for the reaching that motivated the move | Yes, both sides depend on the new class instead of each other | Partially, shortens the chain but does not by itself remove field access | Yes, if the direction removed was the unneeded one | Technically, but by deleting the boundary entirely | No, the reaching persists |
| New types introduced | None | One | None | None | Negative, one type removed | None |
| Restores single owner for the invariant | Yes, if the moved method was the mutator | Yes, the extracted class becomes the owner | No, by itself | Yes, for the side removed | Yes, trivially, everything is one owner | No |
| Risk during migration | Low, one method at a time | Medium, several call sites move at once | Low | Medium, must confirm the removed direction was truly unused | High, single-responsibility regresses, see dimension 11 | None, but the underlying bug stays live |
| Improves testability in isolation | Partially | Strongly | Mildly | Strongly, for the side made unidirectional | Worsens, the merged class is now harder to isolate | No improvement, and tests grow more brittle over time |
| Best suited to | A method that clearly belongs elsewhere | A shared concept both classes lean on | A long reach through one extra hop | A reference that was only ever needed one way | Never, named here as the misuse in dimension 11 | Never, named here as denial rather than a remedy |

Reading of the table. Move Method and Hide Delegate are surgical, appropriate
when the reaching is narrow. Extract Class is the right tool once the
reaching is broad enough that a whole concept, not one computation, is
missing a home. Demoting a bidirectional association to unidirectional is
free when the removed direction was genuinely never load bearing, and
dangerous to attempt without first confirming that. Merging and adding tests
around the symptom are included specifically because they are the two
responses this entry has seen stand in for a real fix, and both make the
underlying coupling worse or leave it untouched while looking like progress.

## 13. Related and incompatible patterns

**Feature Envy**, this family's closest sibling entry, is the smell this
entry most often grows out of. A single method reaching into one other
object's data, unidirectionally, is Feature Envy, fixable with one Move
Method. Several methods doing so, on both sides, against private state, is
this entry. The two share a remedy in Move Method for their narrower
instances and diverge once Extract Class becomes the correct scale of fix,
covered from that entry's side in its own dimension 13.

**Data Class** is a frequent victim on one side of a one-directional version
of this smell, since a class with public fields and no behavior of its own
gives collaborators nowhere else to reach except straight into its data. It
becomes the full smell described here specifically when the Data Class
starts reaching back into its collaborator's state too, rather than staying
a passive holder.

**Divergent Change**, already catalogued in this family, shares a root cause
with this entry, the absence of a clean boundary, but the observable symptom
runs in the opposite direction. Divergent Change is one class changing for
many unrelated reasons. This entry is two specific classes each changing
because of the other, a relationship rather than an internal accumulation.

**Message Chains**, referenced from the Feature Envy entry in this family,
often co-occurs with this smell but calls for a different mechanical fix.
Walking through several objects' accessors to reach a value at the end of
the chain is fixed with Hide Delegate along the chain. Reaching directly into
a private field one hop away, in both directions, is fixed with the remedies
in dimension 14 of this entry. A codebase can have either smell without the
other.

**The Law of Demeter**, a design guideline rather than a pattern, described
by Ian Holland in 1987 at Northeastern University's Demeter project and
formally published as Karl Lieberherr and Ian Holland, "Assuring Good Style
for Object-Oriented Programs," IEEE Software, vol. 6, no. 5, September 1989,
pp. 38 to 48, is closely related in spirit but not identical in shape. The
guideline concerns how far a method reaches through strangers, one dot at a
time, through a chain of public accessor calls. This entry concerns reaching
into an immediate neighbor's private state directly, with no chain at all.
Code can violate the Law of Demeter while never touching a private field,
and code can carry this smell while never chaining past one dot.

**The Memento pattern**, GoF, is the clearest example of a deliberate,
bounded exception that this entry explicitly excludes in dimension 4. The
distinction that matters. Memento's privileged access is narrow, single
purpose, and documented by the pattern's own structure. this entry's target
is broad, accidental, and undocumented.

**Friend declarations**, in languages that offer them, are the same idea
Memento uses, generalized into a language feature. A narrow, explicit,
compiler-checked grant of access, used for a specific, justified reason such
as an iterator needing its container's internal representation, is not this
smell. The smell is the informal, undeclared version of the same idea,
covered as its own implementation variant in dimension 8, where the wider
visibility looks to every other reader exactly like an ordinary public
member.

## 14. Refactoring path in and out

The path in is almost always the same three steps, told here because
recognizing the accretion pattern helps a reader catch it earlier next time.

1. One method on class A needs a single piece of data class B holds.
   Instead of adding a method to B that hands it over, a field on B is
   widened past private, and A reads it directly.
2. A second, unrelated feature elsewhere reaches for the same widened field
   from a third call site, cementing its accidental public status.
3. Class B, needing something back from A to finish its own job, repeats the
   same shortcut in reverse, closing the loop into a two-way relationship.

The path out follows the inventory-then-remedy sequence below, matched
against the concrete refactorings this entry has referenced throughout,
each one drawn from Fowler's catalog (https://refactoring.com/catalog/,
verified 2026-08-02, listing Move Method under its current name Move
Function, Move Field, Extract Class, and Hide Delegate).

1. Inventory every place either class reaches into the other's fields or
   calls a method that exposes an implementation detail. An IDE's find
   usages on each suspect field, run from both files, surfaces this
   quickly.
2. For a reach that amounts to "class A needs to compute something from
   class B's data," apply Move Method to relocate the computation onto B,
   the class that owns the data, mirroring the remedy this family's Feature
   Envy entry describes in full for the single-method case.
3. For a reach where both classes genuinely lean on one shared concept,
   apply Extract Class, giving that concept an honest name and its own
   file, with both original classes depending on it rather than on each
   other. The code examples at the end of this entry extract exactly this
   kind of class, `LoyaltyAccount`, out from between `Order` and `Customer`.
4. For a reach that exists only to save one hop through a chain, apply Hide
   Delegate so the caller talks to a single method on its immediate
   neighbor instead of walking further in.
5. Where a two-way relationship is genuinely required by the domain, for
   example a tree node needing to know its parent, keep the reference but
   route every mutation of it through one paired method on both sides at
   once, so the two sides can never independently disagree.
6. Where the relationship was never truly two-way in the domain, and one
   side only ever held the reference for convenience, demote it to
   unidirectional and delete the unused back-reference entirely.
7. Re-measure. run a coupling check such as PMD's `CouplingBetweenObjects`,
   covered in dimension 9, against both classes afterward, to confirm the
   count actually dropped rather than simply relocating to whatever class
   absorbed the extraction, which is the over-application failure mode
   named in dimension 11.

## 15. Testing and verification

Before a fix, a unit test for either class in an intimate pair is rarely a
true unit test. Testing class A's behavior in isolation requires
constructing class B and, frequently, reaching into B's internals through a
test-only setter or reflection to reach the exact state A's method depends
on, because A depends on B's internal representation rather than on a
contract. The resulting test is slow, coupled to B's constructor signature,
and breaks for reasons unrelated to A's own logic whenever B's internals
shift. This test-authoring pain is itself a reliable, cheap detector.
whenever writing a focused test for one class keeps requiring detailed setup
of a named neighbor's internals, that friction is worth treating as the
smell surfacing, not as an annoyance to route around with another test
helper.

After Move Method or Extract Class, each class can be tested against a
narrow fake or stub that implements only the interface it actually depends
on, rather than the full concrete neighbor. A hand-written stub with two or
three hard-coded return values is usually enough, and is preferable to a
mocking framework's dynamic mock here specifically because a dynamic mock
can be configured to expose the same internal shape the real class does,
quietly reintroducing the coupling the refactor was meant to remove.

Before attempting the refactor on a pair that already has behavior worth
preserving, characterization tests written at the pair's combined,
integration-level boundary give a safety net that survives the internal
boundary moving underneath them, since they assert on externally observable
behavior rather than on either class's internal shape.

A mutation-testing observation worth stating as engineering judgment rather
than as a sourced fact. an intimate pair frequently shows a poor mutation
kill rate on whichever side's field is reached into from outside, because
that class's own test suite never had a reason to exercise the mutation, the
reaching neighbor's tests happen to cover it by accident. A low kill rate
localized to one class's mutated fields, paired with a healthy overall
suite, is a signal worth investigating as this smell rather than as a gap in
that one class's tests alone.

## 16. Observability signals

A per-class coupling count, tracked release over release in continuous
integration using a metric such as PMD's `CouplingBetweenObjects`, described
in dimension 9, gives a cheap, mechanical trend line. a class whose count
climbs steadily without a corresponding, deliberate architectural decision
is worth a look before the climb becomes entrenched.

A file co-change count, mined from version control history as the number of
commits that touch two specific files together, is a practice-level signal
this entry names as engineering judgment rather than as a sourced claim
about any specific published detector. two files with an unusually high
co-change rate relative to the rest of the codebase are frequently exactly
the pair an Inappropriate Intimacy diagnosis fits, and the signal is cheap
to compute from ordinary git history with no additional tooling.

Once a fix routes every mutation of a piece of state through a single
method, that method becomes a genuine place to add a log line or a metric
counter for invalid attempts, something dimension 11's invariant-bypass
failure mode has nowhere to attach before the fix, because no single
location in the code is positioned to see every attempted mutation.

A human, review-level signal worth automating where the volume of pull
requests justifies it. a lightweight bot or dashboard that flags any file
pair crossing a co-change threshold across recent pull requests gives
reviewers the same lagging indicator described above without anyone having
to remember to look for it.

## 17. Security and privacy implications

For the ordinary case, this smell carries no security implication beyond the
general maintainability risk already covered in dimensions 10 and 11, and it
is worth saying so plainly rather than inventing a concern that is not
there.

Where the state being reached into is sensitive, the implication becomes
real. When an authentication or session object's internal token field is
reached into directly by an unrelated presentation-layer class instead of
through a narrow, purpose-built method, there is no single choke point at
which an authorization check, a redaction rule, or an audit log entry can be
attached, because the field's mutation and its reads are scattered across
however many call sites reach in. Widening a field's visibility from private
specifically to make one such reach convenient is, functionally, an
expansion of the trust boundary around that data that nobody explicitly
reviewed as a security decision, since the change reads, in a diff, like an
ordinary visibility keyword rather than a policy change.

The same pattern applies to personal data subject to retention or deletion
rules. a customer object holding data that must be redacted on account
deletion, reached into directly by several unrelated collaborators instead
of exposed through the customer's own methods, means the deletion logic
cannot be centralized in one place and verified once. Each direct reach-in
site becomes a separate location a data-protection review must find
independently, and a residual copy of data that should have been erased is
exactly the kind of gap that review style misses.

## 18. References

1. Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
   edition, Addison-Wesley, 1999, chapter 3, "Bad Smells in Code,"
   Inappropriate Intimacy.
2. Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
   edition, Addison-Wesley, 2018. Edition, publisher, and ISBN 9780134757599
   confirmed against the Internet Archive catalog record,
   https://archive.org/details/refactoringimpro0000fowl, verified
   2026-08-02.
3. Martin Fowler, "CodeSmell," https://martinfowler.com/bliki/CodeSmell.html,
   verified 2026-08-02. Source for the attribution of the term "code smell"
   to Kent Beck, and for treating Beck as a co-author of the smell catalog.
4. Refactoring catalog, https://refactoring.com/catalog/, verified
   2026-08-02. Source for Move Method (recorded as Move Function), Move
   Field, Extract Class, and Hide Delegate as named, current refactorings.
5. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides, *Design
   Patterns. Elements of Reusable Object-Oriented Software*, Addison-Wesley,
   1994, chapter 5, Behavioral Patterns, Memento. Source for the deliberate,
   bounded privileged-access exception described in dimension 4.
6. S.R. Chidamber and C.F. Kemerer, "A Metrics Suite for Object Oriented
   Design," IEEE Transactions on Software Engineering, vol. 20, no. 6, June
   1994, pp. 476 to 493. Citation confirmed against Wikipedia,
   "Programming complexity," https://en.wikipedia.org/wiki/Programming_complexity,
   verified 2026-08-02. Source for the Coupling Between Object classes
   metric described in dimension 9.
7. Karl Lieberherr and Ian Holland, "Assuring Good Style for Object-Oriented
   Programs," IEEE Software, vol. 6, no. 5, September 1989, pp. 38 to 48.
   Origin and citation confirmed against Wikipedia, "Law of Demeter,"
   https://en.wikipedia.org/wiki/Law_of_Demeter, verified 2026-08-02.
   Source for the Law of Demeter guideline described in dimension 13.
8. PMD documentation, "Design rules,"
   https://docs.pmd-code.org/latest/pmd_rules_java_design.html, verified
   2026-08-02. Source for the `CouplingBetweenObjects` and `LawOfDemeter`
   rules described in dimensions 1 and 9.
9. JetBrains IntelliJ IDEA Help, "Extract Delegate,"
   https://www.jetbrains.com/help/idea/extract-delegate.html, verified
   2026-08-02. Source for the automated Extract Delegate refactoring
   described in dimension 9.
10. DesigniteJava project repository,
    https://github.com/tushartushar/DesigniteJava, verified 2026-08-02.
    Source for the seventeen design smells the tool detects, including
    Deficient Encapsulation, used in dimension 1 to distinguish that smell
    from this one.
11. Wikipedia, "Code smell," https://en.wikipedia.org/wiki/Code_smell,
    verified 2026-08-02. Consulted while confirming this entry made no
    unsupported claim about the smell's history or about other automated
    detection tools; this entry does not rely on it for any claim not
    independently confirmed against a primary source above.

## Code examples

Three languages, Python, TypeScript, and Java, are shown against one shared
domain so the same before-and-after reads identically across all three. an
`Order` and a `Customer` reach directly into each other's private state,
`Order` writing straight into a `LoyaltyAccount` field it does not own, and
`Customer` walking through `Order`'s item list rather than asking `Order`
for its own total. The fix extracts `LoyaltyAccount` as its own honest
class, per dimension 14, and routes every mutation of loyalty points through
one method, closing the invariant-bypass failure mode from dimension 11. Go,
Rust, and Swift are omitted here because the same three-language coverage
already used by this family's Feature Envy entry is sufficient to show the
refactoring is language-independent, and the domain example benefits more
from staying identical across languages than from a fourth translation.

### Python

```python
class LoyaltyAccountBefore:
    def __init__(self, points):
        self.points = points


class CustomerBefore:
    def __init__(self, name, points):
        self.name = name
        self.loyalty = LoyaltyAccountBefore(points)
        self.orders = []


# Before. Order reaches straight into Customer's loyalty field and
# writes it directly, bypassing whatever rule should stop the
# balance going negative. This is the smell, in one direction.
class OrderBefore:
    def __init__(self, items):
        self.items = items

    def redeem(self, customer, n):
        customer.loyalty.points -= n


# Before, the other direction. Customer walks Order's own item
# list directly instead of asking Order for its own total.
def total_spend_before(customer):
    total = 0
    for order in customer.orders:
        for item in order.items:
            total += item["price"] * item["qty"]
    return total


# After. LoyaltyAccount is extracted, owns its own invariant, and
# is the only thing allowed to change its own points.
class LoyaltyAccount:
    def __init__(self, points):
        self._points = points

    def redeem(self, n):
        if n > self._points:
            raise ValueError("insufficient points")
        self._points -= n

    @property
    def points(self):
        return self._points


# After. Order computes its own total, so nobody outside it
# needs to walk its item list directly.
class Order:
    def __init__(self, items):
        self._items = items

    def total(self):
        return sum(i["price"] * i["qty"] for i in self._items)

    def redeem_loyalty(self, customer, n):
        customer.redeem_points(n)


class Customer:
    def __init__(self, name, points):
        self.name = name
        self._loyalty = LoyaltyAccount(points)
        self._orders = []

    def place_order(self, order):
        self._orders.append(order)

    def redeem_points(self, n):
        self._loyalty.redeem(n)

    def total_spend(self):
        return sum(o.total() for o in self._orders)

    @property
    def loyalty_points(self):
        return self._loyalty.points


if __name__ == "__main__":
    cb = CustomerBefore("Before", 10)
    ob = OrderBefore([{"price": 20.0, "qty": 2}])
    cb.orders.append(ob)
    ob.redeem(cb, 999)
    assert cb.loyalty.points == 10 - 999
    assert total_spend_before(cb) == 40.0

    c = Customer("After", 10)
    o = Order([{"price": 20.0, "qty": 2}])
    c.place_order(o)
    assert c.total_spend() == 40.0
    raised = False
    try:
        o.redeem_loyalty(c, 999)
    except ValueError:
        raised = True
    assert raised
    assert c.loyalty_points == 10

    print("before_negative=", cb.loyalty.points, "after_points=", c.loyalty_points)
```

Run with `python3 inappropriate_intimacy.py`. Verified to print
`before_negative= -989 after_points= 10` on CPython 3, no dependencies
required.

### TypeScript

```typescript
class LoyaltyAccountBefore {
  constructor(public points: number) {}
}

class CustomerBefore {
  loyalty: LoyaltyAccountBefore;
  orders: OrderBefore[] = [];
  constructor(public name: string, points: number) {
    this.loyalty = new LoyaltyAccountBefore(points);
  }
}

// Before. Order writes straight into Customer's loyalty field,
// bypassing any rule that should stop the balance going negative.
class OrderBefore {
  constructor(public items: { price: number; qty: number }[]) {}

  redeem(customer: CustomerBefore, n: number): void {
    customer.loyalty.points -= n;
  }
}

// Before, the other direction. this walks Order's own item list
// directly instead of asking Order for its own total.
function totalSpendBefore(customer: CustomerBefore): number {
  let total = 0;
  for (const order of customer.orders) {
    for (const item of order.items) {
      total += item.price * item.qty;
    }
  }
  return total;
}

// After. LoyaltyAccount owns its own invariant and is the only
// thing allowed to change its own points.
class LoyaltyAccount {
  private points: number;
  constructor(points: number) {
    this.points = points;
  }

  redeem(n: number): void {
    if (n > this.points) {
      throw new Error("insufficient points");
    }
    this.points -= n;
  }

  balance(): number {
    return this.points;
  }
}

// After. Order computes its own total, so nobody outside it needs
// to walk its item list directly.
class Order {
  private items: { price: number; qty: number }[];
  constructor(items: { price: number; qty: number }[]) {
    this.items = items;
  }

  total(): number {
    return this.items.reduce((sum, i) => sum + i.price * i.qty, 0);
  }

  redeemLoyalty(customer: Customer, n: number): void {
    customer.redeemPoints(n);
  }
}

class Customer {
  private loyalty: LoyaltyAccount;
  private orders: Order[] = [];
  constructor(public name: string, points: number) {
    this.loyalty = new LoyaltyAccount(points);
  }

  placeOrder(order: Order): void {
    this.orders.push(order);
  }

  redeemPoints(n: number): void {
    this.loyalty.redeem(n);
  }

  totalSpend(): number {
    return this.orders.reduce((sum, o) => sum + o.total(), 0);
  }

  loyaltyPoints(): number {
    return this.loyalty.balance();
  }
}

const cb = new CustomerBefore("Before", 10);
const ob = new OrderBefore([{ price: 20, qty: 2 }]);
cb.orders.push(ob);
ob.redeem(cb, 999);
if (cb.loyalty.points !== 10 - 999) throw new Error("mismatch");
if (totalSpendBefore(cb) !== 40) throw new Error("mismatch");

const c = new Customer("After", 10);
const o = new Order([{ price: 20, qty: 2 }]);
c.placeOrder(o);
if (c.totalSpend() !== 40) throw new Error("mismatch");
let raised = false;
try {
  o.redeemLoyalty(c, 999);
} catch {
  raised = true;
}
if (!raised) throw new Error("expected redemption to be refused");
if (c.loyaltyPoints() !== 10) throw new Error("mismatch");

console.log("before_negative=", cb.loyalty.points, "after_points=", c.loyaltyPoints());
```

Compiled with `tsc --strict --target es2020` (TypeScript 7.0.2) and run with
`node`. Verified to print `before_negative= -989 after_points= 10` with zero
compiler errors under strict mode.

### Java

```java
import java.util.ArrayList;
import java.util.List;

class LoyaltyAccountBefore {
    int points;
    LoyaltyAccountBefore(int points) { this.points = points; }
}

class CustomerBefore {
    String name;
    LoyaltyAccountBefore loyalty;
    List<OrderBefore> orders = new ArrayList<>();
    CustomerBefore(String name, int points) {
        this.name = name;
        this.loyalty = new LoyaltyAccountBefore(points);
    }
}

// Before. redeem writes straight into Customer's loyalty field,
// bypassing any rule that should stop the balance going negative.
class OrderBefore {
    List<double[]> items;
    OrderBefore(List<double[]> items) { this.items = items; }

    void redeem(CustomerBefore customer, int n) {
        customer.loyalty.points -= n;
    }
}

class BeforeDemo {
    // Before, the other direction. this walks Order's own item
    // list directly instead of asking Order for its own total.
    static double totalSpend(CustomerBefore customer) {
        double total = 0;
        for (OrderBefore order : customer.orders) {
            for (double[] item : order.items) {
                total += item[0] * item[1];
            }
        }
        return total;
    }

    public static void main(String[] args) {
        CustomerBefore cb = new CustomerBefore("Before", 10);
        List<double[]> items = new ArrayList<>();
        items.add(new double[]{20.0, 2.0});
        OrderBefore ob = new OrderBefore(items);
        cb.orders.add(ob);
        ob.redeem(cb, 999);
        if (cb.loyalty.points != 10 - 999) throw new AssertionError("mismatch");
        if (totalSpend(cb) != 40.0) throw new AssertionError("mismatch");
        System.out.println("before_negative=" + cb.loyalty.points);
    }
}
```

```java
import java.util.ArrayList;
import java.util.List;

// After. LoyaltyAccount owns its own invariant and is the only
// thing allowed to change its own points.
class LoyaltyAccount {
    private int points;
    LoyaltyAccount(int points) { this.points = points; }

    void redeem(int n) {
        if (n > points) throw new IllegalStateException("insufficient points");
        points -= n;
    }

    int balance() { return points; }
}

// After. Order computes its own total, so nobody outside it needs
// to walk its item list directly.
class Order {
    private List<double[]> items;
    Order(List<double[]> items) { this.items = items; }

    double total() {
        double sum = 0;
        for (double[] item : items) sum += item[0] * item[1];
        return sum;
    }

    void redeemLoyalty(Customer customer, int n) {
        customer.redeemPoints(n);
    }
}

class Customer {
    private String name;
    private LoyaltyAccount loyalty;
    private List<Order> orders = new ArrayList<>();
    Customer(String name, int points) {
        this.name = name;
        this.loyalty = new LoyaltyAccount(points);
    }

    void placeOrder(Order order) { orders.add(order); }
    void redeemPoints(int n) { loyalty.redeem(n); }

    double totalSpend() {
        double sum = 0;
        for (Order o : orders) sum += o.total();
        return sum;
    }

    int loyaltyPoints() { return loyalty.balance(); }
}

class AfterDemo {
    public static void main(String[] args) {
        Customer c = new Customer("After", 10);
        List<double[]> items = new ArrayList<>();
        items.add(new double[]{20.0, 2.0});
        Order o = new Order(items);
        c.placeOrder(o);
        if (c.totalSpend() != 40.0) throw new AssertionError("mismatch");
        boolean raised = false;
        try {
            o.redeemLoyalty(c, 999);
        } catch (IllegalStateException e) {
            raised = true;
        }
        if (!raised) throw new AssertionError("expected refusal");
        if (c.loyaltyPoints() != 10) throw new AssertionError("mismatch");
        System.out.println("after_points=" + c.loyaltyPoints());
    }
}
```

Each block compiles standalone with `javac` and runs with `java BeforeDemo`
and `java AfterDemo` respectively. Verified to print
`before_negative=-989` and `after_points=10` on OpenJDK 26, no external
dependencies required.
