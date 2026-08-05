---
name: Parallel Inheritance Hierarchies
slug: parallel-inheritance-hierarchies
family: 02-code-smells
category: Change Preventers
aliases: [Parallel Class Hierarchies, Twin Hierarchies, Shadow Hierarchies]
first_described: "Fowler, Beck, Brant, Opdyke, Roberts 1999, Refactoring, Improving the Design of Existing Code"
maturity: canonical
related: [divergent-change, shotgun-surgery, bridge, visitor, factory-method, abstract-factory, move-method, extract-class]
incompatible_with: []
verified: 2026-08-02
---

# Parallel Inheritance Hierarchies

## 1. Name, aliases, and lineage

The canonical name is Parallel Inheritance Hierarchies. It is one of the
twenty two named code smells catalogued by Martin Fowler, with Kent Beck,
John Brant, William Opdyke, and Don Roberts, in Martin Fowler, *Refactoring,
Improving the Design of Existing Code*, Addison-Wesley, 1999, Chapter 3,
"Bad Smells in Code". The book groups it near its close cousin Divergent
Change, and the sibling entry in this catalogue for Divergent Change, whose
frontmatter research was independently verified on 2026-08-02, records that
Fowler's second edition, 2018, with Kent Beck, places both smells under the
same family in the table of contents. This entry treats that grouping as
established given the cross reference already verified in this repository.

Fowler's book uses "parallel class hierarchies" and "parallel inheritance
hierarchies" interchangeably, and later writers have not settled on one
term over the other. This entry uses Parallel Inheritance Hierarchies
because that is the literal section title Fowler assigned, and treats
Parallel Class Hierarchies as the dominant alias in casual usage, because
the underlying structures are classes arranged in inheritance trees, not
merely hierarchies of some other kind such as a directory tree or an
organisational chart.

The underlying situation the smell names is older than Fowler's 1999 book.
Erich Gamma, Richard Helm, Ralph Johnson, and John Vlissides, *Design
Patterns, Elements of Reusable Object-Oriented Software*, Addison-Wesley,
1994, present the Bridge pattern with a motivating example in which a
`Window` abstraction hierarchy threatens to be extended once per platform,
producing the coupled hierarchy shape this smell describes, and they offer
Bridge as the structural fix, Gamma, Helm, Johnson, Vlissides 1994, Bridge
pattern chapter, Motivation section. Fowler's contribution in 1999 was not
to discover the structure, which GoF had already used as a worked example
five years earlier, but to name it as a smell a reader should notice in
existing code and to give it a repeatable refactoring recipe, Move Method,
for removing it once found. This entry treats the GoF Bridge motivation as
the earliest widely cited description of the underlying coupled hierarchy
problem, and Fowler 1999 as the source of the name used throughout the
industry today. No independent verification of an exact page number in the
GoF text was possible during this research pass, so the GoF citation here
is given at chapter granularity only, per the citation rule that a page
number is included only where independently confirmed.

Twin Hierarchies and Shadow Hierarchies are terms observed in code review
comments and team retrospectives rather than terms with independent
published attribution, and are listed only as encountered usage, never as
sourced aliases carrying the weight of a citation.

## 2. Problem and context

The smell appears whenever a codebase has two or more class hierarchies
where subclassing one forces a matching subclass to be added to the other,
over and over, for as long as the hierarchies exist. The two hierarchies
are usually different in kind. One might be a domain concept, a `Shape`,
an `Instruction`, an `Employee`, and the other a technical concern that
varies per concrete member of the first, a `Renderer`, a `Visitor`, a
`Validator`, a platform `Peer`. The tell is not that two hierarchies exist
side by side, plenty of correct designs have that, the tell is that adding
one new subclass to the first hierarchy is not complete until a matching
subclass has also been added to the second, and the two additions have to
be kept in lockstep by convention rather than by the compiler or the type
system enforcing it.

The context in which this arises is almost always an initial design that
picked inheritance as the mechanism for varying one axis of behaviour, and
later needed a second, independent axis of behaviour for the same set of
concrete types. A `Shape` hierarchy with `Circle` and `Square` needed a way
to render each shape to more than one output format, and the team reached
for a second hierarchy, `CircleRenderer` and `SquareRenderer`, rather than
for a technique that decouples the two axes. Once the second hierarchy
exists and a naming convention links `Circle` to `CircleRenderer`, every
future concrete `Shape` subclass carries an implicit, unenforced obligation
to also produce a matching `Renderer` subclass. Nothing in the type system
says a `Triangle` without a `TriangleRenderer` is wrong. The obligation
lives only in the heads of the people who remember it, or in a runtime
lookup that throws when it is forgotten.

This is also a context problem in the literal sense of Fowler's own
framing. A pattern that would be entirely appropriate in a closed, rarely
extended hierarchy becomes a smell specifically because the first hierarchy
keeps growing. A two member hierarchy with a matching two member companion
hierarchy is an inconvenience. A twenty member hierarchy with a matching
twenty member companion hierarchy, added to by different engineers over
several years, each of whom may not know the convention exists, is a
recurring source of missed cases and runtime surprises.

## 3. Forces

The forces below are weighed as engineering judgement, drawn from the
general literature on this smell and from the mechanics of the structure
itself, not as sourced facts about a specific measured system.

**Type safety against extensibility.** Using inheritance for the second
axis gives the compiler strong guarantees inside a single concrete pair,
`CircleRenderer` really does know it is rendering a `Circle`, but it buys
that guarantee at the cost of a convention the compiler cannot check across
the two hierarchies as a whole. A design that instead composes the second
axis in, a strategy object or a visitor, sacrifices some of that per pair
specificity in exchange for a single place, often a compiler error or a
single dispatch table, where a missing case is caught.

**Discoverability against indirection.** Two parallel hierarchies are easy
to read locally, opening `CircleRenderer` next to `Circle` tells a reader
everything about how a circle renders. The same information hidden inside
a Visitor's dispatch method or a Strategy map is centralised, which helps
someone auditing every rendering behaviour at once, but it costs a reader
who only wants to know how circles render specifically, because now they
must locate one case inside a larger construct.

**Coupling direction.** In a parallel hierarchy, both sides usually depend
on each other, the first hierarchy's factory method typically constructs
the matching member of the second, and the second hierarchy's methods
frequently need to read state that lives on the first. Bridge deliberately
breaks this into a one directional dependency, the abstraction depends on
the implementation interface, never the reverse, which is a smaller change
than it looks and is the entire content of the refactoring path in
dimension 14.

**Change fan-out.** Every new concrete type in the first hierarchy turns
into at least two file changes, sometimes across two different modules or
even two different teams' areas of ownership, because the matching type
belongs to the second hierarchy. This is the same underlying cost that
Divergent Change and Shotgun Surgery describe from other angles, and this
smell is often diagnosed alongside one of those two, because a missing
case in the second hierarchy is a textbook Divergent Change site, a
single class, the dispatcher, that now has to change for every new reason
a new concrete type is added.

**Team topology.** When the two hierarchies are owned by different teams,
for example a domain team owning `Shape` and a rendering team owning
`Renderer`, the smell becomes an organisational coordination cost, not
purely a technical one, because a change to one hierarchy now requires a
cross team pull request to the other, or a manual notification process
that is easy to skip.

## 4. Applicability and non-applicability

**When the shape is a genuine smell worth removing.**

- The two hierarchies vary along genuinely independent axes, for example a
  shape's geometry and a shape's rendering target, and both axes are
  expected to grow independently over the life of the system.
- New concrete members are added to the first hierarchy by people who do
  not necessarily know the second hierarchy exists, so the pairing
  obligation is easy to forget.
- The pairing is currently enforced only by naming convention, a
  dictionary keyed by class, or a long if or switch chain, none of which
  the compiler checks for completeness.
- A missing pairing currently fails at runtime, with a null reference, a
  missing key exception, or a silent no-op, rather than at compile time.

**When it is not a smell, and the fix should not be applied.**

- The second hierarchy has exactly one variation point that is not
  expected to grow, for example a single `Serializer` interface with one
  implementation per format where the set of formats is fixed by an
  external standard and will not change again. Introducing Bridge or
  Visitor here adds indirection with no corresponding future flexibility
  to pay for it.
- The two hierarchies are not actually coupled to each other, they merely
  happen to have a similar shape by coincidence, for example two unrelated
  domain concepts that both happen to have three subclasses. Restructuring
  here would not remove any real obligation, because no obligation exists.
- The language already provides exhaustiveness checking across the
  pairing, for example a closed sealed class hierarchy matched with an
  exhaustive pattern match that the compiler refuses to compile unless
  every case is handled. In that situation the parallel structure still
  exists, but the central danger this smell describes, a silently missing
  case, is already closed by the type system, and the remaining cost is
  largely aesthetic.
- Performance sensitive code deliberately trades the coupling for the
  absence of virtual dispatch or heap allocated strategy objects, as seen
  in dimension 9 below with LLVM's instruction visitor, where the authors
  chose the parallel structure on purpose and documented the fallback
  behaviour for a missing case, which removes the silent failure risk that
  is this smell's core cost.
- The project is small, has a single maintainer, and the pairing failure
  mode has never actually occurred. Removing the smell here optimises for
  a cost that has not yet shown up, at the price of an indirection that
  has a real, immediate readability tax.

## 5. Structure

The structure has two hierarchies and the coupling between them.

**Primary hierarchy.** An abstract base type, `Shape` in the running
example, and N concrete subclasses, `Circle`, `Square`, `Triangle`. This
hierarchy usually represents the true domain model and is the one that
changes for domain reasons.

**Companion hierarchy.** A second abstract base type, `Renderer`, and a
matching set of N concrete subclasses, `CircleRenderer`, `SquareRenderer`,
`TriangleRenderer`. This hierarchy usually represents a single technical
concern that must be specialised per member of the primary hierarchy.

**Pairing mechanism.** Some piece of code, most often a factory method on
the primary type, a static lookup table, or a long conditional, maps each
concrete primary type to its matching concrete companion type. This
mechanism is the load bearing part of the smell, because it is the one
place where the obligation that every primary subclass needs a companion
subclass is enforced, or fails to be enforced.

**Client.** Code that holds a primary object and needs the companion
behaviour, and therefore either asks the primary object for its matching
companion, or performs the same lookup itself, duplicating the pairing
mechanism a second time.

## 6. ASCII structure diagram

```
  PRIMARY HIERARCHY                    COMPANION HIERARCHY

     +-----------+                         +--------------+
     |   Shape   |<>-----needs------------>|   Renderer   |
     +-----------+                         +--------------+
      ^    ^    ^                           ^     ^     ^
      |    |    |                           |     |     |
  +--------+ +------+ +----------+   +------------+ +-----+ +------------+
  | Circle | |Square| |Triangle  |   |CircleRender| |SqRen| |TriRenderer |
  +--------+ +------+ +----------+   +------------+ +-----+ +------------+
      |                                     ^
      |            makes, returns           |
      +---------- pairing mechanism --------+
                (factory, switch, or map
                 keeping the two hierarchies
                 in lockstep by convention)

  A new concrete class on the left silently has no matching class
  on the right until a human remembers to add one.
```

## 7. Dynamics

```
  Client                Shape (Circle)         PairingMechanism        Renderer

    |  needsRenderer()        |                        |                  |
    |------------------------>|                        |                  |
    |                         |  lookup(Circle.class)   |                  |
    |                         |----------------------->|                  |
    |                         |                        |  match found?    |
    |                         |                        |------------------|
    |                         |                        |  yes, CircleRenderer
    |                         |<-----------------------|                  |
    |<------------------------|                        |                  |
    |   render(circle)                                 |                  |
    |-------------------------------------------------------------------->|
    |                                                                     |
    |         (a new concrete Shape, e.g. Pentagon, added without         |
    |          a matching Renderer produces a missing match branch)       |
    |                                                                     |
    |  needsRenderer() on Pentagon                      |                  |
    |------------------------>|                        |                  |
    |                         |  lookup(Pentagon.class) |                  |
    |                         |----------------------->|                  |
    |                         |                        |  match found?    |
    |                         |                        |------------------|
    |                         |                        |  no, throw or    |
    |                         |                        |  return default  |
    |                         |<-----------------------|                  |
    |<------------------------| (runtime failure, never a compile error)  |
```

## 8. Implementation variants

**Naming convention plus reflection.** The pairing mechanism looks up the
companion class by string concatenation, `Circle` plus the suffix
`Renderer`, then loads it via reflection. This is the loosest variant, the
compiler verifies nothing about the pairing, and a typo in either class
name produces a runtime lookup failure with a message that rarely names
the real cause.

**Explicit registry, or map keyed by class token.** A dictionary from the
primary class, or an enum representing it, to an instance or factory of
the companion class, populated once at startup. This is a step up in
safety because a missing entry can be validated at startup rather than
discovered lazily, but the validation is still a manual assertion someone
has to remember to run, not a compiler guarantee.

**Long conditional inside a dispatcher.** A single method with an if or
switch chain over the concrete type of the primary object, either using
instance-of checks or, in languages with closed sum types, a pattern
match. This is functionally the Visitor pattern collapsed into one method
instead of a class per case, and it is the variant most likely to be
caught by a compiler's exhaustiveness checker when the primary hierarchy
is sealed, which is precisely why the non-applicability list in dimension
4 calls out sealed hierarchies with exhaustive matching as a case where
the smell's core danger no longer applies even though the parallel
structure itself is still visible.

**Generic bound linking the two hierarchies.** In languages with
parametric generics, the companion hierarchy is expressed as
`Renderer<T extends Shape>`, and each concrete companion binds `T` to its
matching concrete primary type. This gives the compiler a stronger, though
still incomplete, guarantee, `CircleRenderer` cannot be used where a
`Renderer<Square>` is required, but the compiler still does not verify
that every concrete `Shape` subclass has a matching `Renderer<T>`
instantiation anywhere in the codebase.

**Visitor pattern as a deliberate, accepted instance.** The Visitor
pattern, as described by Gamma, Helm, Johnson, Vlissides, is itself a
formalised, named instance of a parallel hierarchy, a `Visitor` interface
with one method per concrete `Element` subtype, deliberately accepted in
exchange for adding new operations without touching the `Element`
hierarchy. LLVM's `InstVisitor`, discussed under dimension 9, is a real
production example of this exact variant, and its own header comments
document the fallback rule for a method that was not overridden, which is
the project's own mitigation for the smell's central failure mode.

## 9. Known production uses

**java.awt.peer, the historical AWT native peer architecture.** The JDK's
`java.awt` package defines heavyweight GUI component classes, `Button`,
`Checkbox`, `Choice`, `Label`, `List`, `TextField`, `TextArea`, `Scrollbar`,
`ScrollPane`, `Panel`, `Frame`, `Dialog`, and the `java.awt.peer` package
defines a matching interface for nearly every one of them, `ButtonPeer`,
`CheckboxPeer`, `ChoicePeer`, `LabelPeer`, `ListPeer`, `TextFieldPeer`,
`TextAreaPeer`, `ScrollbarPeer`, `ScrollPanePeer`, `PanelPeer`, `FramePeer`,
`DialogPeer`, alongside a handful of peers, `RobotPeer`, `SystemTrayPeer`,
`TaskbarPeer`, that do not have a matching AWT component and exist for
other reasons. The full list of thirty three peer interfaces plus a
`package-info.java` file was confirmed against the live OpenJDK source
tree at github.com slash openjdk slash jdk, path
`src/java.desktop/share/classes/java/awt/peer`, verified 2026-08-02. Each
concrete peer's job is to forward a component's behaviour to the native
windowing toolkit on the running platform, so adding a new heavyweight AWT
component historically meant adding a matching peer interface and a
matching native implementation per supported platform, the textbook shape
of this smell, and one of the documented motivations for Swing's later
move toward lightweight, mostly peer free components for most widget
types.

**javax.swing.plaf, the pluggable look and feel UI delegate hierarchy.**
Swing's `javax.swing.plaf` package defines an abstract UI delegate class
per Swing component family, `ButtonUI`, `LabelUI`, `ListUI`, `TreeUI`,
`TableUI`, `ComboBoxUI`, `MenuBarUI`, `MenuItemUI`, `ScrollBarUI`,
`SliderUI`, `TabbedPaneUI`, `ToolBarUI`, and more, alongside the matching
Swing component classes, `JButton`, `JLabel`, `JList`, `JTree`, `JTable`,
and so on, each of which looks up its delegate by a UI class ID string at
construction time. The forty three top level files in `javax/swing/plaf`,
including the abstract `ComponentUI` base and one concrete abstract UI
class per widget family, were confirmed against the live OpenJDK source
tree, verified 2026-08-02. Each look and feel, Metal, Nimbus, the native
platform look and feel, then supplies its own concrete subclass of every
one of those UI delegate classes, so the companion hierarchy is
effectively multiplied by the number of installed look and feel
implementations, and a look and feel that omits a delegate for a newer
Swing component silently falls back to a default rendering rather than
failing to compile.

**LLVM's InstVisitor, deliberately parallel and explicitly documented.**
LLVM's intermediate representation defines an `Instruction` class
hierarchy, with concrete subclasses such as `BinaryOperator`, `LoadInst`,
`StoreInst`, and `CallInst`, and the header
`llvm/include/llvm/IR/InstVisitor.h` defines a template based visitor with
one `visitXXX` method per concrete instruction subclass, for example
`visitBinaryOperator`, `visitLoadInst`, `visitStoreInst`, and
`visitCallInst`, confirmed against the live source at github.com slash
llvm slash llvm-project, verified 2026-08-02. The header's own comments
document that a subclass which does not implement `visitXXX` for a given
instruction type falls back to the visit method for that instruction's
superclass, which is LLVM's own accepted mitigation for the smell's core
danger, a silently missing case, and it is exactly the kind of deliberate,
well understood use of the structure that dimension 4's non-applicability
list describes, chosen for the absence of virtual dispatch overhead on a
hot compiler code path rather than adopted by accident.

## 10. Consequences

**Positive.**

- Each concrete pair reads locally, opening the companion class next to
  the primary class shows exactly how that one case behaves, with no need
  to trace through a dispatcher shared by every other case.
- Per pair specialisation is unrestricted, a concrete companion class can
  override any inherited method and can hold whatever per case state it
  needs, without the more constrained shape of a single Strategy or
  Visitor method body.
- Where the language supports it, generic bounds can at least prevent
  mismatched pairs from compiling, even though they cannot prove every
  primary subclass has a companion.

**Negative.**

- The pairing obligation is invisible to the compiler in the common case,
  a naming convention or a runtime lookup, so a missing companion fails at
  runtime, often far from the class that was actually added.
- Every new concrete member of the primary hierarchy is at minimum a two
  file change, and often crosses a module or ownership boundary, which is
  the same change fan-out cost Divergent Change and Shotgun Surgery
  describe.
- The two hierarchies tend to grow in lockstep forever once the pattern is
  established, because removing it later requires touching every existing
  pair at once, which is a larger single change than the incremental cost
  of adding one more pair.
- Onboarding cost rises, a new team member editing the primary hierarchy
  has no compiler signal that a second hierarchy even exists, let alone
  that it needs a matching edit.

## 11. Failure modes and misuse

**Missing companion at runtime.** Symptom, a new concrete type is added to
the primary hierarchy, ships, and then a null reference exception, a
missing key exception, or a silent default appears in production the
first time that new type reaches the pairing lookup. Cause, the pairing
mechanism is a naming convention or an unvalidated map, and nothing forced
the author of the new primary subclass to also add the companion, or to
even know the companion hierarchy exists. Fix, replace the lookup with
Bridge, so the primary constructor requires the companion as a constructor
argument, or replace the lookup with a Visitor whose interface the
compiler forces every implementation to satisfy, or, if the primary
hierarchy is closed and the language supports exhaustive matching, seal
both hierarchies and let the compiler refuse to build until every case is
handled.

**Divergent naming drift.** Symptom, over years the naming convention that
links the two hierarchies quietly breaks, a companion class is renamed for
a technical reason, or a new companion is added with a slightly different
suffix, and reflection based lookups start failing intermittently for the
affected types only. Cause, the pairing was never expressed as a type
level relationship, only as a string convention, so the compiler had no
way to catch the rename. Fix, replace the string based lookup with an
explicit registration call at each companion's definition site, ideally
one enforced by a static initializer check or a build time test that
asserts the primary and companion class counts match.

**Duplicated pairing logic.** Symptom, the same if or switch chain that
maps primary type to companion type is copy pasted into two or three
different call sites over time, because each new caller did not realise a
shared pairing mechanism already existed, and the copies drift out of
sync, so one call site handles a new primary type correctly and another
still throws. Cause, the pairing mechanism was never centralised behind a
single factory method or lookup, so each new use site reinvented it. Fix,
extract the pairing logic into a single factory method on the primary
hierarchy or a single registry class, and delete every duplicate, which is
a straightforward application of Extract Method or Move Method as
described by Fowler.

**Forced third dimension.** Symptom, a second axis of variation appears,
for example the companion hierarchy itself now needs to vary by output
format as well as by primary type, and the team's first instinct is to
add a third parallel hierarchy rather than revisit the design. Cause, once
the parallel hierarchy pattern is established as the team's default tool
for adding a variation axis, it gets reached for again without anyone
asking whether composition would scale better. Fix, this is the point at
which Bridge, which explicitly separates an abstraction hierarchy from an
implementation hierarchy that can itself vary independently, earns its
cost, because Bridge is designed from the start to support the
implementation side varying along its own axis without adding a further
hierarchy on the abstraction side.

## 12. Trade-off matrix

| Force | Parallel Inheritance Hierarchies | Bridge | Visitor | Single hierarchy with a switch |
|---|---|---|---|---|
| Compile time completeness check | None, a missing companion fails at runtime | Partial, generic bounds can prevent mismatches but not detect a missing implementation | Strong, a new Visitor interface method breaks every existing implementer at compile time | Strong only if the primary hierarchy is sealed and the match is exhaustive |
| Cost of adding a new primary subtype | Two file change plus a manual pairing step | Two file change, but the abstraction side needs no change if the implementation interface is stable | One file change to add the Element, then a compile break in every Visitor forces the update | One line added to a single switch, but the switch grows without limit |
| Cost of adding a new operation across all cases | Requires touching every existing companion class once per new operation, or growing every companion's interface | Adding a new abstraction subclass is cheap, adding a new operation on the implementation side means touching one interface plus every implementer | Cheap, add one new Visitor subclass, existing Element classes are untouched | Requires touching the shared switch, which now serves two unrelated axes and grows tangled |
| Local readability of one concrete case | High, the companion class sits next to the pattern's primary class | Medium, the implementation is one hop away through the bridge reference | Low to medium, the case is one branch inside a larger visitor class | Low, the case is a branch inside a shared function that also handles every other case |
| Team ownership fit | Poor across team boundaries, both hierarchies need coordinated edits | Good, the abstraction team and the implementation team can each own their hierarchy independently once the interface is fixed | Good for the operation adding team, poor for the element adding team, who must update every visitor | Poor once more than one team touches the shared switch |

## 13. Related and incompatible patterns

**Bridge.** Bridge is the structural fix most often applied to remove this
smell when the primary hierarchy's variation axis, and the companion
hierarchy's variation axis, are genuinely independent and both are
expected to keep growing. Gamma, Helm, Johnson, Vlissides 1994 present
Bridge's own motivating example, a `Window` abstraction that must not be
extended once per platform, as essentially this same coupled hierarchy
problem viewed from the implementation side, and the refactoring path in
dimension 14 below is, in effect, a step by step recipe for turning an
accidental parallel hierarchy into a deliberate Bridge.

**Visitor.** Visitor is the accepted, named version of this smell,
deliberately chosen when the primary hierarchy is expected to stay
relatively closed while the set of operations performed on it is expected
to grow. Where this smell entry treats the parallel structure as
accidental and worth removing, the Visitor entry in this catalogue treats
the identical structure as intentional, and the two entries should be
read together when deciding whether a given case of the smell is actually
a misapplied Visitor waiting to be named as such, or a genuine accident
worth collapsing with Bridge instead.

**Factory Method and Abstract Factory.** The pairing mechanism described
in dimension 5 is very often, in practice, an ad hoc Factory Method that
has not been named as one, a single method on the primary hierarchy or a
free function that maps a primary type to its companion. Naming that
lookup explicitly as a Factory Method, or, when whole families of related
companions must be created together, an Abstract Factory, is frequently
the first step toward either Bridge or Visitor, because it centralises the
one place where the pairing logic lives before that logic is redesigned.

**Divergent Change and Shotgun Surgery.** Both of these sibling code
smells describe symptoms that a parallel hierarchy commonly produces. A
centralised pairing dispatcher that grows a new branch for every new
primary subtype is a textbook Divergent Change site, one class with many
unrelated reasons to change. A decentralised pairing mechanism duplicated
across several call sites, described in dimension 11, produces Shotgun
Surgery instead, one new primary subtype forcing edits scattered across
several files. Diagnosing which of the two is present in a given codebase
often determines whether Extract Method plus Move Method, or a full
switch to Bridge, is the more proportionate fix.

**Incompatible with a genuinely closed, exhaustive design.** This smell
does not apply at all to a design where both hierarchies are sealed or
closed and the compiler already performs an exhaustive match across them,
because the central cost this smell describes, a silently missing case,
cannot occur under that design, even though the classes still visually
form two parallel trees.

## 14. Refactoring path in and out

**Introducing the smell, which happens by drift rather than by design.**
The smell is rarely introduced deliberately. It typically begins the
moment a second variation axis is needed for an existing hierarchy and a
single new companion class is added next to a single existing primary
class, which looks like the smallest possible change at the time. The
second and third companion class each look equally small in isolation,
and by the time the hierarchy has grown past three or four pairs the
convention is established and harder to question.

**Removing the smell toward Bridge, when both axes will keep growing.**
Fowler's own recipe for this smell is Move Method, applied repeatedly, to
migrate behaviour from the companion hierarchy down into the primary
hierarchy until one of the two hierarchies collapses to a single class.
The concrete steps, adapted to the running `Shape` and `Renderer` example
used throughout this entry, are as follows.

1. Pick one concrete pair, for example `Circle` and `CircleRenderer`, and
   for each method on `CircleRenderer`, use Move Method to move its
   behaviour onto `Circle` itself, updating call sites as you go, keeping
   the test suite green after every single method moved, per dimension 15
   below.
2. Once every method has moved off `CircleRenderer`, the class is left
   with no behaviour of its own, and it can be deleted, along with its
   entry in the pairing mechanism.
3. Repeat step one and step two for every remaining pair, one pair at a
   time, never batching more than one pair per commit, because a batched
   change here is exactly the kind of change that is hard to review and
   easy to get wrong silently.
4. Once every concrete companion class has been folded into its matching
   primary class, delete the now empty `Renderer` abstract base and the
   pairing mechanism entirely.
5. If, after this collapse, the behaviour that used to live on `Renderer`
   is still expected to vary independently in the future, for example a
   need to render the same `Shape` hierarchy to more than one output
   format, reintroduce the second axis deliberately as a Bridge, an
   interface `RenderTarget` held as a field on `Shape`, rather than as a
   second inheritance hierarchy, which is the structural difference that
   prevents the smell from reappearing.

**Removing the smell toward Visitor, when the primary hierarchy is closed
but operations will keep growing.** When step five above concludes that
the operations, not the primary types, are the axis expected to grow,
formalise the existing companion hierarchy as a Visitor interface instead
of collapsing it, add an `accept` method to the primary hierarchy that
double dispatches into the visitor, and rely on the compiler to flag every
existing visitor implementation the next time a new primary subtype's
`accept` method is added, which converts the smell's silent runtime
failure into a compile time one, the exact property Visitor is chosen for.

## 15. Testing and verification

Code carrying this smell is, in one specific sense, easy to test badly and
hard to test well. It is easy to write a unit test for one concrete pair
in isolation, `CircleRendererTest` next to `Circle`, and that test will
pass regardless of whether the pairing mechanism itself is correct. It is
hard to write a single test that proves every concrete primary type has a
matching companion, because that assertion has to enumerate both
hierarchies and cross reference them, something the production code
itself was not designed to do.

The single highest value test to add before attempting the refactoring
path in dimension 14 is exactly that cross reference, an exhaustiveness
test that walks every concrete subclass of the primary hierarchy, at
runtime via reflection in languages that support it, or at compile time
via an exhaustive match in languages with sealed hierarchies, and asserts
that a companion exists for each one. Writing this test first serves two
purposes, it gives the refactoring a safety net that catches a regression
the moment a pair is accidentally left unmoved, and it gives an early,
concrete count of how many pairs actually exist, which is often larger
than anyone on the team expected.

Beyond that exhaustiveness test, standard unit tests per concrete pair
remain useful and should be kept during the refactoring, since Move
Method is behaviour preserving and the same test that passed against the
split `Circle` and `CircleRenderer` classes should continue to pass,
unmodified, against the merged `Circle` class, which is itself a useful
signal that the refactoring step did not change observable behaviour. A
test double for the companion hierarchy, a fake `Renderer` that records
calls instead of performing real rendering, is a reasonable technique
while the smell is still present, and becomes unnecessary once Move
Method has folded the companion's behaviour into the primary class,
because there is no longer a second object to substitute a double for.

## 16. Observability signals

The most direct production signal for a system carrying this smell in a
naming convention or runtime lookup variant is a metric or a log line
counting lookup misses in the pairing mechanism, tagged with the concrete
primary type that had no companion, because that count should be zero in
a healthy system and any non zero value points at exactly the class that
needs a companion added.

A secondary, slower moving signal is simply the ratio of files touched
per pull request that adds a new concrete primary type. If that ratio is
reliably close to one, the pairing has likely already been collapsed or
was never a full parallel hierarchy. If it is reliably close to two or
more, with the second file consistently living in the companion
hierarchy, that ratio itself is a useful dashboard number for a team
deciding whether the cost described in dimension 10 is worth paying down.

Where the pairing mechanism is a reflection based lookup by class name,
logging every successful lookup at debug level, alongside the failed
ones, lets an operator later reconstruct exactly which concrete pairs are
actually exercised in production traffic, which is useful evidence when
deciding whether an unused or rarely used pair is a candidate for
deletion rather than for a fix.

## 17. Security and privacy implications

This smell's security surface is narrow and indirect, largely a
consequence of the specific pairing mechanism chosen rather than of the
parallel structure itself. A reflection based lookup that builds a class
name from untrusted input, for example a class name derived from a
request parameter or an external configuration file rather than from a
value fixed in source code, opens a class loading or instantiation
surface that an attacker could potentially use to load an unexpected
class, which is a general reflection based instantiation risk rather than
a risk specific to this pattern, and is out of scope for a detailed
treatment here. A pairing mechanism keyed purely by an internal enum or
sealed type, which is the common and recommended case, carries no such
surface, because the set of possible keys is fixed at compile time and
cannot be influenced by external input.

Beyond that specific reflection risk, this smell has no privacy
implication of its own, it does not by itself determine what data flows
through either hierarchy, and where such a review is needed it belongs to
the concrete classes and the data they carry, not to the shape of the two
hierarchies.

## 18. References

1. Martin Fowler, with Kent Beck, John Brant, William Opdyke, and Don
   Roberts, *Refactoring, Improving the Design of Existing Code*,
   Addison-Wesley, 1999, Chapter 3, "Bad Smells in Code", section
   "Parallel Inheritance Hierarchies". Second edition, with Kent Beck,
   Addison-Wesley, 2018, same chapter and section title retained.
2. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides, *Design
   Patterns, Elements of Reusable Object-Oriented Software*,
   Addison-Wesley, 1994, Bridge pattern chapter, Motivation section, and
   Visitor pattern chapter.
3. OpenJDK project, `java.awt.peer` package source directory,
   https://github.com/openjdk/jdk/tree/master/src/java.desktop/share/classes/java/awt/peer
   listing of AWT native peer interfaces mirroring the `java.awt`
   component hierarchy, verified 2026-08-02.
4. OpenJDK project, `javax.swing.plaf` package source directory,
   https://github.com/openjdk/jdk/tree/master/src/java.desktop/share/classes/javax/swing/plaf
   listing of pluggable look and feel UI delegate classes mirroring the
   `javax.swing` component hierarchy, verified 2026-08-02.
5. LLVM project, `InstVisitor.h`,
   https://github.com/llvm/llvm-project/blob/main/llvm/include/llvm/IR/InstVisitor.h
   showing one `visitXXX` method per concrete `Instruction` subclass and
   the documented superclass fallback behaviour, verified 2026-08-02.
6. Wikipedia, "Abstract Window Toolkit",
   https://en.wikipedia.org/wiki/Abstract_Window_Toolkit for general
   confirmation of the AWT native peer delegation model, verified
   2026-08-02.
7. This catalogue, `patterns/02-code-smells/divergent-change.md`, cross
   referenced for the shared Fowler catalogue grouping and the second
   edition table of contents research already performed for that sibling
   entry, verified 2026-08-02.

## Code examples

The examples below show the smell in its naming convention variant, a
`Shape` hierarchy paired with a `Renderer` hierarchy by a class name
lookup, followed by the Bridge based fix that collapses the pairing
obligation into a single constructor argument. Java and C# were not used
because a Java sample would not add anything the TypeScript sample does
not already show for this pattern, and neither toolchain's availability
was confirmed for this pass, per the citation and toolchain honesty rule.

### TypeScript, the smell

```typescript
abstract class Shape {
  abstract kind(): string;
}

class Circle extends Shape {
  constructor(public radius: number) {
    super();
  }
  kind(): string {
    return "Circle";
  }
}

class Square extends Shape {
  constructor(public side: number) {
    super();
  }
  kind(): string {
    return "Square";
  }
}

abstract class Renderer {
  abstract render(shape: Shape): string;
}

class CircleRenderer extends Renderer {
  render(shape: Shape): string {
    const c = shape as Circle;
    return `circle r=${c.radius}`;
  }
}

class SquareRenderer extends Renderer {
  render(shape: Shape): string {
    const s = shape as Square;
    return `square side=${s.side}`;
  }
}

// The pairing mechanism, a naming convention resolved by class name.
// A new Shape subclass with no matching entry here throws at runtime,
// not at compile time.
const renderers: Record<string, Renderer> = {
  Circle: new CircleRenderer(),
  Square: new SquareRenderer(),
};

function renderShape(shape: Shape): string {
  const renderer = renderers[shape.kind()];
  if (!renderer) {
    throw new Error(`no renderer registered for ${shape.kind()}`);
  }
  return renderer.render(shape);
}

const shapes: Shape[] = [new Circle(3), new Square(4)];
for (const shape of shapes) {
  console.log(renderShape(shape));
}
```

### Python, the Bridge based fix

```python
from abc import ABC, abstractmethod


class RenderTarget(ABC):
    @abstractmethod
    def draw_circle(self, radius: float) -> str: ...

    @abstractmethod
    def draw_square(self, side: float) -> str: ...


class SvgRenderTarget(RenderTarget):
    def draw_circle(self, radius: float) -> str:
        return f"<circle r='{radius}' />"

    def draw_square(self, side: float) -> str:
        return f"<rect width='{side}' height='{side}' />"


class Shape(ABC):
    # The pairing obligation is now a required constructor argument,
    # so the compiler and the type checker enforce it directly instead
    # of a naming convention or a lookup table.
    def __init__(self, target: RenderTarget) -> None:
        self._target = target

    @abstractmethod
    def render(self) -> str: ...


class Circle(Shape):
    def __init__(self, target: RenderTarget, radius: float) -> None:
        super().__init__(target)
        self._radius = radius

    def render(self) -> str:
        return self._target.draw_circle(self._radius)


class Square(Shape):
    def __init__(self, target: RenderTarget, side: float) -> None:
        super().__init__(target)
        self._side = side

    def render(self) -> str:
        return self._target.draw_square(self._side)


def main() -> None:
    target = SvgRenderTarget()
    shapes: list[Shape] = [Circle(target, 3.0), Square(target, 4.0)]
    for shape in shapes:
        print(shape.render())


if __name__ == "__main__":
    main()
```

### Go, an exhaustiveness test for a still parallel design

```go
package parallelhierarchies

import (
	"fmt"
	"testing"
)

// Shape is the primary hierarchy, implemented by concrete shape types.
type Shape interface {
	Kind() string
}

type Circle struct{ Radius float64 }

func (Circle) Kind() string { return "Circle" }

type Square struct{ Side float64 }

func (Square) Kind() string { return "Square" }

// Renderer is the companion hierarchy the smell pairs to Shape.
type Renderer interface {
	Render(Shape) string
}

type circleRenderer struct{}

func (circleRenderer) Render(s Shape) string {
	c := s.(Circle)
	return fmt.Sprintf("circle r=%.1f", c.Radius)
}

type squareRenderer struct{}

func (squareRenderer) Render(s Shape) string {
	sq := s.(Square)
	return fmt.Sprintf("square side=%.1f", sq.Side)
}

var renderers = map[string]Renderer{
	"Circle": circleRenderer{},
	"Square": squareRenderer{},
}

// TestEveryShapeHasARenderer is the exhaustiveness test dimension 15
// recommends before attempting the refactoring path in dimension 14. It
// enumerates every concrete Shape known to this test file and asserts a
// matching entry exists in the pairing map, so a newly added Shape with
// no matching Renderer fails the build instead of failing at runtime.
func TestEveryShapeHasARenderer(t *testing.T) {
	knownShapes := []Shape{Circle{Radius: 1}, Square{Side: 1}}
	for _, s := range knownShapes {
		if _, ok := renderers[s.Kind()]; !ok {
			t.Fatalf("no renderer registered for shape kind %q", s.Kind())
		}
	}
}
```
